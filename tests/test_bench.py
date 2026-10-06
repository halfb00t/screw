"""The bench harness's own predicates, pinned without a service, a daemon or a stopwatch.

Ported from spur's `tests/test_bench.py` (L07): the capped-row rule, the STL size check, the
L19 gzip selection rule, the `ru_maxrss` units, the 503 reasons, the refusal of an empty sweep
and of a p95 over too few samples. spur's gear-sweep and composed-scenario tests are not
carried over -- there is no gear corpus here. The skeleton corpus is pinned instead, so it
cannot drift under a number that someone compares with an earlier run.

The thread spike's (Phase 2) predicates are pinned here too, with the same rule: no timing
assertion. The quiet gate runs on an injected host, the closed form against a numeric
integral, the row verdict on synthetic records, the STL check on hand-built meshes. Two tests
build a real rod in the kernel, because a verdict nobody ran against a real solid is a claim,
not a check.

Run as `.venv/bin/python -m pytest tests/test_bench.py -q` from the repo root: the `-m` form
puts the root on `sys.path`, which is what makes `import bench` resolve. `bench` is not an
installed package (`pyproject.toml` ships `src/screw` only) and `tests/conftest.py` puts
`tests/` on the path, not the root.
"""

from __future__ import annotations

import itertools
import json
import math
import os
import struct
import subprocess
import sys
from collections.abc import Iterable, Sequence
from fractions import Fraction
from pathlib import Path
from typing import Literal

import httpx2 as httpx
import pytest
from pydantic import ValidationError

from bench.build_time import Timing, load_sweep, report, stl_size
from bench.corpus import corpus
from bench.export_cost import GzipRow, find_set, maxrss_bytes, select_gzip_level
from bench.latency import (
    DEFAULT_SCENARIOS,
    MIN_SAMPLES,
    SCENARIOS,
    RequestOutcome,
    ScenarioResult,
    _p95_or_warn,
    fetch,
    report_markdown,
)
from bench.memory import (
    _CAP_TOLERANCE_FRACTION,
    _SWEEP_MEM_LIMIT_BYTES,
    _is_capped,
    _parse_mem,
    _publish,
)
from bench.quiet import QuietResult, Reading, wait_quiet
from bench.thread_spike import __main__ as spike_cli
from bench.thread_spike import helical, maths, measure, worker
from bench.thread_spike.__main__ import _table_row
from bench.thread_spike.runner import Worker
from bench.thread_spike.verdict import (
    BUDGET_BYTES,
    BUDGET_S,
    ESTIMATOR_TIE,
    FINE_CHECK_CEILING,
    GATE_FACTOR,
    PROTOCOL_PATH,
    ROW_TIMEOUT_S,
    T_PASS,
    GuardResult,
    HeaderRecord,
    MeshRecord,
    RowRecord,
    RowRequest,
    before_results,
    classify_row,
    failed_record,
    frontier_stop,
    gate_tolerance,
    over_budget,
    parse_header,
    parse_record,
    parse_request,
    parse_result_row,
    pass_bar,
    protocol_guard,
    relative_error,
    request_seconds,
    select_estimator,
    select_k,
    turn_caps,
)
from screw.params import BoltParams
from screw.solid import TESSELLATION


def test_the_skeleton_corpus_is_the_d_by_length_grid() -> None:
    """12 parts, d outermost: the grid is pinned so a later edit cannot quietly change the
    workload under figures that someone compares with an earlier run. It exercises the
    harness and sets no bound (L07); Phase 7 replaces it with the threaded grid."""
    assert corpus() == [
        {"d": d, "length": length}
        for d in (2.0, 6.0, 20.0, 100.0)
        for length in (5.0, 20.0, 200.0)
    ]


def test_every_corpus_entry_is_a_valid_bolt() -> None:
    entries = corpus()
    assert len(entries) == 12  # an empty corpus would pass the loop below vacuously
    for entry in entries:
        BoltParams.model_validate(entry)


def test_the_default_sweep_is_the_corpus_labelled_by_its_two_numbers() -> None:
    sets = load_sweep()
    assert [label for label, _ in sets][:2] == ["d=2 length=5", "d=2 length=20"]
    assert sets[-1] == ("d=100 length=200", BoltParams(d=100.0, length=200.0))
    assert len(sets) == 12


def test_a_sweep_file_set_that_is_not_a_bolt_is_refused_naming_it(tmp_path: Path) -> None:
    """A set that cannot be built must not be silently skipped: the sweep is refused before
    any timing starts, and the message names the file, the position and the set."""
    path = tmp_path / "sweep.json"
    path.write_text(json.dumps([{"d": 6.0}, {"d": -1.0, "length": 5.0}]))
    with pytest.raises(ValueError, match=r"set 1 \(d=-1 length=5\)") as raised:
        load_sweep(path)
    assert str(path) in str(raised.value)
    assert isinstance(raised.value.__cause__, ValidationError)


def test_a_set_is_found_by_the_label_the_sweep_prints() -> None:
    assert find_set(None, "d=100 length=200") == BoltParams(d=100.0, length=200.0)


def test_an_unknown_set_label_exits_2_and_lists_the_labels(
        capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        find_set(None, "d=7 length=7")
    assert raised.value.code == 2
    assert "d=2 length=5" in capsys.readouterr().err


def test_a_binary_stl_is_sized_by_its_length_and_the_triangle_count_its_header_names() -> None:
    """The count is read from the header's own little-endian uint32 at bytes 80-84, not by
    walking the facets: a synthetic 84 + 50 * 2 byte STL whose header says 2 triangles."""
    data = bytes(80) + (2).to_bytes(4, "little") + bytes(50 * 2)
    assert stl_size(data) == (184, 2)


def test_an_stl_whose_length_disagrees_with_its_header_is_refused() -> None:
    """A truncated file, or an ASCII STL that happens to carry 80 header-like bytes, must
    never yield a plausible but wrong triangle count: the header says 2 triangles and the
    file is one short."""
    data = bytes(80) + (2).to_bytes(4, "little") + bytes(50)
    with pytest.raises(ValueError, match="184"):
        stl_size(data)


def test_the_report_names_the_largest_fine_stl_and_breaks_a_tie_by_file_order() -> None:
    """Two rows tied for the largest fine STL and for the heaviest worst request: both lines
    name the first in the list, which is `max()`'s documented behaviour pinned rather than
    assumed. Also pins the two size columns."""
    timings = [
        Timing("a", 1.0, 1.0, 1.0, 1000, 10),
        Timing("b", 1.0, 1.0, 1.0, 1000, 10),  # ties "a" on both worst_request and stl_bytes
        Timing("c", 0.5, 0.5, 0.5, 500, 5),
    ]
    text = report(Path("x.json"), timings, 30, (1.23, 4.56, 7.89))
    assert "| Fine STL (bytes) | Triangles |" in text
    assert "| a | 1.00 | 1.00 | 1.00 | 2.00 | yes | 1000 | 10 |" in text
    assert "**Heaviest:** a -- 2.00 s of 30 s." in text
    assert "**Largest fine STL:** a -- 1000 bytes, 10 triangles." in text


def test_an_empty_sweep_is_refused_rather_than_reported() -> None:
    """An empty table reads as a pass; refuse it loudly instead."""
    with pytest.raises(ValueError, match="empty"):
        report(Path("empty.json"), [], 30, (0.0, 0.0, 0.0))


def test_the_report_prints_the_load_it_was_given_rather_than_reading_one_itself() -> None:
    """The reading is taken before the first row builds, so a sweep's "at start" line is not
    an end-of-run figure. A made-up load no real host would report (99.99) proves the
    printed figures are the caller's: a live `os.getloadavg()` inside `report()` could
    coincidentally print the same numbers as the host's, and this test would not notice."""
    text = report(Path("x.json"), [Timing("a", 1.0, 1.0, 1.0, 100, 1)], 30,
                  (99.99, 88.88, 77.77))
    assert "- Load averages at start: 99.99, 88.88, 77.77" in text


def test_l19s_rule_applied_to_its_own_table_keeps_level_1() -> None:
    """spur L19's recorded table (a 9 MB gear STL): neither level 6 nor level 9 reaches the
    10% shrink bar over level 1 (8.7% and 8.66%), so the rule keeps level 1, which is the
    reading L19 itself recorded by hand."""
    rows = [
        GzipRow(level=1, single_ms=51.5, out_bytes=2_632_467, concurrent_ms=74.4),
        GzipRow(level=6, single_ms=147.9, out_bytes=2_403_312, concurrent_ms=198.9),
        GzipRow(level=9, single_ms=788.0, out_bytes=2_404_371, concurrent_ms=925.5),
    ]
    assert select_gzip_level(rows) == 1


def test_a_higher_gzip_level_is_adopted_exactly_on_both_of_l19s_bars() -> None:
    """A level 6 row exactly 10% smaller than level 1 with a 10-concurrent wall exactly 1.5x
    level 1's is adopted; one byte less shrink, or a wall 1.5x plus a millisecond, holds
    level 1. Level 9 equals level 1 in every row so it can never itself be adopted."""
    level1 = GzipRow(level=1, single_ms=50.0, out_bytes=1_000_000, concurrent_ms=100.0)
    inert_level9 = GzipRow(level=9, single_ms=500.0, out_bytes=1_000_000, concurrent_ms=100.0)

    at_both_bars = GzipRow(level=6, single_ms=100.0, out_bytes=900_000, concurrent_ms=150.0)
    assert select_gzip_level([level1, at_both_bars, inert_level9]) == 6

    one_byte_short = GzipRow(level=6, single_ms=100.0, out_bytes=900_001, concurrent_ms=150.0)
    assert select_gzip_level([level1, one_byte_short, inert_level9]) == 1

    one_ms_over = GzipRow(level=6, single_ms=100.0, out_bytes=900_000, concurrent_ms=150.001)
    assert select_gzip_level([level1, one_ms_over, inert_level9]) == 1


def test_level_9_is_compared_against_the_level_currently_adopted() -> None:
    """With 6 held, 9 is compared against 1; with 6 adopted, 9 is compared against 6, not
    always against 1. The second case would wrongly adopt 9 if the comparison stayed
    pinned to level 1."""
    level1 = GzipRow(level=1, single_ms=50.0, out_bytes=1_000_000, concurrent_ms=100.0)

    # Level 6 is only 5% smaller (held); level 9 is 20% smaller at 1.4x the wall: adopted.
    level6_held = GzipRow(level=6, single_ms=100.0, out_bytes=950_000, concurrent_ms=110.0)
    level9_beats_1 = GzipRow(level=9, single_ms=200.0, out_bytes=800_000, concurrent_ms=140.0)
    assert select_gzip_level([level1, level6_held, level9_beats_1]) == 9

    # Level 6 adopted at both bars. Level 9 is 15% smaller than level 1 but only 5.6% smaller
    # than level 6, so against the level actually adopted it misses the shrink bar. The wall
    # is 100 ms, inside both bases' bars, so only the shrink clause can decide this row.
    level6_adopted = GzipRow(level=6, single_ms=100.0, out_bytes=900_000, concurrent_ms=150.0)
    level9_beats_1_not_6 = GzipRow(level=9, single_ms=200.0, out_bytes=850_000,
                                   concurrent_ms=100.0)
    assert select_gzip_level([level1, level6_adopted, level9_beats_1_not_6]) == 6


def test_peak_rss_reads_bytes_on_macos_and_kibibytes_on_linux() -> None:
    """`ru_maxrss` is bytes on Darwin and kibibytes everywhere else this project runs
    (Linux, in the image); a mesh-copy reading needs the unit split to be believed at all."""
    assert maxrss_bytes(1000, "Darwin") == 1000
    assert maxrss_bytes(1000, "Linux") == 1024000


def test_a_peak_equal_to_the_ceiling_is_capped() -> None:
    """A sampled peak that reads the ceiling exactly -- what spur's two capped rows read -- is
    the sweep's own limit showing up as a measurement, so it is capped."""
    assert _is_capped(_SWEEP_MEM_LIMIT_BYTES, _SWEEP_MEM_LIMIT_BYTES)


def test_a_peak_well_below_the_ceiling_is_not_capped() -> None:
    """spur's honest N=1 and N=2 peaks (2052.1 and 2878.5 MiB) against the 8 GiB ceiling are
    the uncapped cases this predicate must never call capped."""
    assert not _is_capped(round(2052.1 * 1024**2), _SWEEP_MEM_LIMIT_BYTES)
    assert not _is_capped(round(2878.5 * 1024**2), _SWEEP_MEM_LIMIT_BYTES)


def test_the_tolerance_boundary_is_pinned_from_both_sides() -> None:
    """The smallest integer peak inside the tolerance is capped; one byte less is not."""
    just_inside = math.ceil(_SWEEP_MEM_LIMIT_BYTES * (1 - _CAP_TOLERANCE_FRACTION))
    assert _is_capped(just_inside, _SWEEP_MEM_LIMIT_BYTES)
    assert not _is_capped(just_inside - 1, _SWEEP_MEM_LIMIT_BYTES)


def test_docker_stats_sizes_parse_by_their_longest_suffix() -> None:
    """MiB itself ends in "B", so a check for "B" first would misparse every non-byte value."""
    assert _parse_mem("612.5MiB") == 642252800
    assert _parse_mem("1GiB") == 1024**3
    assert _parse_mem("2KiB") == 2048
    assert _parse_mem("17B") == 17
    with pytest.raises(ValueError, match="unrecognised"):
        _parse_mem("12")


def test_the_container_is_published_on_the_host_port_the_base_url_names() -> None:
    """A host whose 8000 belongs to another project points the sweep at a free port; the
    image always listens on 8000, and the publish stays on localhost like compose.yaml's."""
    assert _publish("http://127.0.0.1:8000") == "127.0.0.1:8000:8000"
    assert _publish("http://127.0.0.1:8001") == "127.0.0.1:8001:8000"
    with pytest.raises(ValueError, match="names no port"):
        _publish("http://127.0.0.1")


def test_the_no_argument_latency_run_is_still_concurrent_then_single() -> None:
    """A scenario added to `SCENARIOS` must not slip into `make bench.latency`:
    `DEFAULT_SCENARIOS` pins the run, and `sorted(SCENARIOS)` would reorder it."""
    assert DEFAULT_SCENARIOS == ("concurrent", "single")
    assert set(SCENARIOS) == {"concurrent", "single"}


def test_the_concurrent_scenario_never_builds_the_single_scenarios_part() -> None:
    """The default run is concurrent then single; a part built first would make the second a
    cache hit that puts no load on the server."""
    heaviest = corpus()[-1]
    assert heaviest == {"d": 100.0, "length": 200.0}
    assert heaviest not in corpus()[:10]


def test_a_503_is_recorded_by_the_reason_the_server_gave() -> None:
    """`fetch` turns a 200 into `"200"` and a 503 into `"503 " + detail[0]["type"]` read from
    the body -- `busy`, `timeout` and `pool_broken` are `src/screw/app.py`'s own three. Any
    other status still raises. No network: `httpx.MockTransport` stands in for the server."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["quality"] == "fine"
        case = request.url.params["case"]
        if case == "200":
            return httpx.Response(200, content=b"stl-bytes")
        if case in ("busy", "timeout", "pool_broken"):
            return httpx.Response(
                503, json={"detail": [{"loc": ["query"], "type": case, "msg": case}]})
        if case == "no-type":
            return httpx.Response(503, content=b"gateway says no")
        return httpx.Response(500, content=b"boom")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        outcome = fetch("http://test", client, {"case": "200"})
        assert outcome.status == "200"
        assert outcome.params == "case=200"
        assert outcome.wall_s >= 0

        for case in ("busy", "timeout", "pool_broken"):
            assert fetch("http://test", client, {"case": case}).status == f"503 {case}"

        with pytest.raises(ValueError, match="gateway says no"):
            fetch("http://test", client, {"case": "no-type"})
        with pytest.raises(httpx.HTTPStatusError):
            fetch("http://test", client, {"case": "500"})


def test_a_p95_over_too_few_samples_is_refused_with_a_warning(
        capsys: pytest.CaptureFixture[str]) -> None:
    """`statistics.quantiles(n=20)` over fewer samples than buckets would print a plausible
    number about data that was never collected: refuse it (L02), at the boundary exactly."""
    assert _p95_or_warn([0.001] * (MIN_SAMPLES - 1), "x/idle") is None
    assert "only 19 /api/health samples" in capsys.readouterr().err
    assert _p95_or_warn([0.001] * MIN_SAMPLES, "x/idle") == (0.001, MIN_SAMPLES)
    assert capsys.readouterr().err == ""


def test_the_latency_report_counts_what_the_server_answered_and_sets_no_bar() -> None:
    result = ScenarioResult("concurrent", [], [], (
        RequestOutcome("d=2 length=5", "200", 0.25),
        RequestOutcome("d=2 length=20", "200", 0.5),
        RequestOutcome("d=6 length=5", "503 busy", 0.01),
    ))
    text = report_markdown(result, (0.002, 40), (0.004, 25), (9.87, 6.54, 3.21))
    assert "- Load averages at start: 9.87, 6.54, 3.21" in text
    assert "- Idle p95: 2.0 ms (n=40)" in text
    assert "- Under-load p95: 4.0 ms (n=25)" in text
    assert "- Ratio (under-load / idle): 2.00x -- no bar is set for screw yet" in text
    assert "- Slowest successful build: 0.50 s" in text
    assert "3 attempted -- 200: 2, 503 busy: 1" in text


# --- the thread spike (Phase 2) ----------------------------------------------------------


def _quiet(loads: Iterable[float], cap: float = 900.0) -> QuietResult:
    """`wait_quiet` on a made-up host: each read pops the next load, `sleep` advances a fake
    clock, and `now` stamps the fake time, so no test waits and none reads the real load."""
    clock = [0.0]
    feed = iter(loads)

    def sleep(seconds: float) -> None:
        clock[0] += seconds

    return wait_quiet(read=lambda: next(feed), sleep=sleep,
                      now=lambda: f"t={clock[0]:g}", clock=lambda: clock[0], cap=cap)


def test_three_readings_under_the_bar_release_the_gate_decisively_after_three() -> None:
    result = _quiet([1.4, 1.4, 1.4])
    assert result.decisive
    assert [r.load1 for r in result.readings] == [1.4, 1.4, 1.4]


def test_a_reading_of_exactly_the_bar_resets_the_run_of_quiet_readings() -> None:
    """The bar is strict: 1.5 is not under 1.5. 1.4, 1.5, 1.4, 1.4, 1.4 releases only at the
    fifth reading, because the third and fourth still have the 1.5 inside their window."""
    result = _quiet([1.4, 1.5, 1.4, 1.4, 1.4])
    assert result.decisive
    assert len(result.readings) == 5


def test_the_largest_float_below_the_bar_counts_as_quiet() -> None:
    just_under = math.nextafter(1.5, 0.0)
    result = _quiet([just_under] * 3)
    assert result.decisive
    assert len(result.readings) == 3


def test_a_host_that_never_quiets_is_non_decisive_after_the_cap_with_31_readings() -> None:
    """Cap 900 at interval 30: readings at t = 0, 30, ... 900, and the last one is the one
    that finds the deadline reached."""
    result = _quiet(itertools.repeat(2.0))
    assert not result.decisive
    assert len(result.readings) == 31
    assert result.readings[-1].utc == "t=900"


def test_a_zero_cap_reads_once_and_is_non_decisive_by_construction() -> None:
    result = _quiet(itertools.repeat(0.1), cap=0.0)
    assert not result.decisive
    assert len(result.readings) == 1


def test_every_reading_carries_the_time_it_was_read() -> None:
    """The injected `now` stamps the fake clock at the moment of each read: 0, 30, 60."""
    result = _quiet([1.9, 1.9, 1.4, 1.4, 1.4])
    assert [r.utc for r in result.readings] == ["t=0", "t=30", "t=60", "t=90", "t=120"]
    assert Reading("t=0", 1.9) == result.readings[0]


def test_the_basic_profile_has_the_coefficients_the_owner_confirmed() -> None:
    """H = (sqrt(3)/2) P and the depth 5H/8, against the digits the research read for M6 P=1:
    H = 0.866 025 404 P, H1 = 0.541 265 877 P."""
    assert maths.fundamental_height(1.0) == pytest.approx(0.866025404, abs=1e-9)
    assert maths.thread_depth(1.0) == pytest.approx(0.541265877, abs=1e-9)


def test_the_section_is_a_crest_flat_a_root_flat_and_two_linear_flanks() -> None:
    d, pitch = 6.0, 1.0
    ro, rr = d / 2, d / 2 - maths.thread_depth(pitch)
    radius = maths.section_radius
    assert radius(d, pitch, 0.0, 0.0) == ro
    assert radius(d, pitch, 0.0, math.pi / 8) == pytest.approx(ro)
    assert radius(d, pitch, 0.0, math.pi) == rr
    assert radius(d, pitch, 0.0, 3 * math.pi / 4) == pytest.approx(rr)
    mid_flank = radius(d, pitch, 0.0, (math.pi / 8 + 3 * math.pi / 4) / 2)
    assert mid_flank == pytest.approx((ro + rr) / 2)
    assert radius(d, pitch, 0.0, 2 * math.pi) == ro  # taken modulo 2 pi
    assert radius(d, pitch, 0.2, 0.0) == pytest.approx(ro + 0.2)


@pytest.mark.parametrize("clearance", [0.0, 0.2])
@pytest.mark.parametrize("size", ["M2", "M6", "M20"])
def test_the_closed_form_section_area_is_half_the_integral_of_the_radius_squared(
        size: str, clearance: float) -> None:
    """A 400 000-point midpoint rule over one turn: the radius is piecewise linear in angle
    with its breaks on multiples of pi/8, which 400 000 points divide exactly, so the rule's
    only error is the second-order one on each quadratic piece."""
    d, pitch = (float(x) for x in maths.PITCH[size])
    points = 400_000
    step = 2 * math.pi / points
    integral = sum(maths.section_radius(d, pitch, clearance, (i + 0.5) * step) ** 2
                   for i in range(points)) * step / 2
    assert maths.section_area(d, pitch, clearance) == pytest.approx(integral, rel=1e-9)


def test_closed_volume_is_the_section_area_times_the_length() -> None:
    assert maths.closed_volume(6.0, 1.0, 5.0) == maths.section_area(6.0, 1.0) * 5.0


def test_the_spike_covers_the_15_sizes_in_numeric_order() -> None:
    assert len(maths.SIZES) == 15
    assert maths.SIZES[0] == "M2"
    assert maths.SIZES[-1] == "M20"
    diameters = [maths.PITCH[size][0] for size in maths.SIZES]
    assert diameters == sorted(diameters)


def test_the_interim_presets_equal_the_ones_the_service_ships() -> None:
    """The kernel-free spike module copies the INTERIM presets so it need not import the
    kernel to read them; this pins that the copy cannot drift from `screw.solid`."""
    assert maths.INTERIM_PRESETS == TESSELLATION


# The D-03 grid per size under the owner's R2 reading (lower bound min(P, 1 mm)); RESEARCH
# Pattern 1 counts, re-derived by `maths.lengths` and pinned so Phase 7's reuse cannot drift.
_GRID_COUNTS = {
    "M2": 60, "M2.5": 78, "M3": 60, "M3.5": 82, "M4": 92, "M5": 100, "M6": 60, "M7": 70,
    "M8": 128, "M10": 133, "M12": 171, "M14": 140, "M16": 160, "M18": 216, "M20": 240,
}


def _grid(size: str, lower: Fraction | None = None) -> list[Fraction]:
    d, pitch = maths.PITCH[size]
    return maths.lengths(d, pitch, lower)


def test_the_grid_and_frontier_constants_are_the_ones_the_protocol_names() -> None:
    assert maths.FRONTIER_MAX_TURNS == 250
    assert maths.FRONTIER_STEP_TURNS == 5
    assert maths.K_CANDIDATES == (3, 5, 10)
    assert maths.VOID_CLEARANCE == 0.20
    assert maths.DEPTH_FRACTIONS == (4, 8, 16, 32)
    assert maths.SAMPLE_SIZES == ("M2", "M2.5", "M3", "M6", "M8", "M10", "M16", "M20")
    assert set(maths.SAMPLE_SIZES) <= set(maths.SIZES)


def test_the_grid_has_the_pinned_length_count_per_size_and_1790_in_all() -> None:
    assert {size: len(_grid(size)) for size in maths.SIZES} == _GRID_COUNTS
    assert sum(_GRID_COUNTS.values()) == 1790


def test_the_grid_under_the_alternative_lower_bound_loses_rows_only_at_m8_and_above() -> None:
    """Starting at L = P instead of min(P, 1 mm) drops the integer-mm lengths below P: the
    sizes with P > 1 mm, which is exactly M8 (1.25) to M20 (2.5). 1790 - 1781 = 9 rows."""
    lost = {size: _GRID_COUNTS[size] - len(_grid(size, maths.PITCH[size][1]))
            for size in maths.SIZES}
    assert {size for size, n in lost.items() if n} == {"M8", "M10", "M12", "M14", "M16", "M18",
                                                       "M20"}
    assert sum(lost.values()) == 9


def test_the_grid_includes_both_ends_and_lists_each_length_once() -> None:
    for size in maths.SIZES:
        d, pitch = maths.PITCH[size]
        grid = _grid(size)
        assert grid[0] == min(pitch, Fraction(1))
        assert grid[-1] == maths.standard_max(d)
        assert grid == sorted(set(grid))


def test_a_length_that_is_both_an_integer_turn_and_an_integer_mm_appears_once() -> None:
    """M2.5 (P = 9/20): 9 mm and 18 mm are 20 and 40 turns."""
    grid = _grid("M2.5")
    assert grid.count(Fraction(9)) == 1
    assert grid.count(Fraction(18)) == 1


def test_the_grid_stops_at_ten_diameters_capped_at_200_mm() -> None:
    assert maths.standard_max(Fraction(6)) == 60
    assert maths.standard_max(Fraction(20)) == 200
    assert maths.standard_max(Fraction(25)) == 200


def test_integer_turns_are_decided_on_fractions_where_the_float_product_drifts() -> None:
    assert 0.4 * 3 != 1.2  # the drift this guards against: 1.2000000000000002
    assert maths.is_integer_turn(Fraction(6, 5), Fraction(2, 5))
    assert not maths.is_integer_turn(Fraction(1), Fraction(2, 5))
    assert maths.turns_of(Fraction(6, 5), Fraction(2, 5)) == 3


@pytest.mark.parametrize(("size", "first", "count"), [
    ("M2", 55, 40),    # standard max 50 turns: the next multiple of 5 above it
    ("M2.5", 60, 39),  # 55.56 turns
    ("M6", 65, 38),    # exactly 60 turns is not strictly above: starts at the next one
    ("M20", 85, 34),   # 80 turns
])
def test_the_frontier_starts_above_the_standard_max_and_steps_by_five_to_250(
        size: str, first: int, count: int) -> None:
    d, pitch = maths.PITCH[size]
    turns = maths.frontier_turns(d, pitch)
    assert turns[0] == first
    assert turns[-1] == 250
    assert len(turns) == count
    assert all(b - a == 5 for a, b in itertools.pairwise(turns))
    assert turns[0] > maths.turns_of(maths.standard_max(d), pitch)


def test_the_depth_presets_are_fractions_of_five_eighths_of_the_fundamental_height() -> None:
    h = 5 / 8 * math.sqrt(3) / 2
    presets = maths.depth_presets(1.0)
    assert [name for name, _, _ in presets] == ["h/4", "h/8", "h/16", "h/32"]
    assert [tolerance for _, tolerance, _ in presets] == pytest.approx(
        [h / 4, h / 8, h / 16, h / 32])
    assert {angular for _, _, angular in presets} == {0.5}


_REQUEST: RowRequest = {
    "kind": "rod", "size": "M6", "d": 6.0, "pitch": 1.0, "turns": 5.0, "length": 5.0,
    "left_hand": False, "k": 5, "clearance": 0.0, "presets": [("preview", 0.08, 0.5)],
    "step": False, "gzip_on": [], "check_ceiling": FINE_CHECK_CEILING,
}


def _built(precise: float, *, solids: int = 1, valid: bool = True,
           meshes: list[MeshRecord] | None = None) -> RowRecord:
    return {
        **_REQUEST, "outcome": "built", "error": None, "solids": solids, "is_valid": valid,
        "precise_volume": precise, "default_volume": precise, "build_s": 0.1, "volume_s": 0.1,
        "meshes": [] if meshes is None else meshes, "step_bytes": None, "step_s": None,
    }


def _mesh(*, watertight: bool = True, volume: float = 1.0, area: float = 10.0,
          checked: bool = True) -> MeshRecord:
    return {
        "preset": "preview", "tolerance": 0.08, "angular": 0.5, "triangles": 100, "bytes": 5084,
        "mesh_s": 0.01, "gzip1_bytes": None, "gzip1_s": None, "checked": checked,
        "check_s": 0.01 if checked else None,
        "watertight": watertight if checked else None,
        "open_edges": (0 if watertight else 3) if checked else None,
        "stl_volume": volume if checked else None, "surface_area": area if checked else None,
    }


def test_a_row_inside_the_tolerance_is_ok_and_the_next_volume_above_it_is_not() -> None:
    """1.0001 against a closed form of 1.0 sits at T_PASS (1e-4); 1.00010001 is just outside."""
    assert classify_row(_built(1.0001), 1.0) == ("ok", ())
    row_class, reasons = classify_row(_built(1.00010001), 1.0)
    assert row_class == "silent_wrong"
    assert reasons == ("precise rel err +1.000e-04 outside +/-1e-4",)


def test_the_tolerance_boundary_is_exact_to_the_next_representable_volume() -> None:
    """Walk to the largest volume whose relative error is still <= T_PASS: that one is ok and
    the very next float is silent_wrong."""
    volume = 1.0 + T_PASS
    while relative_error(volume, 1.0) > T_PASS:
        volume = math.nextafter(volume, 0.0)
    while relative_error(math.nextafter(volume, 2.0), 1.0) <= T_PASS:
        volume = math.nextafter(volume, 2.0)
    assert classify_row(_built(volume), 1.0)[0] == "ok"
    assert classify_row(_built(math.nextafter(volume, 2.0)), 1.0)[0] == "silent_wrong"


def test_the_naive_row_with_its_core_missing_is_silent_wrong_although_one_valid_solid() -> None:
    """The recorded known-bad shape (RESEARCH Pitfall 9): one solid, isValid() True, volume
    0.238 of the closed form. isValid() and the solid count both pass it; only the volume
    against the closed form catches it."""
    row_class, reasons = classify_row(_built(0.238), 1.0)
    assert row_class == "silent_wrong"
    assert reasons == ("precise rel err -7.620e-01 outside +/-1e-4",)


def test_an_inverted_solid_is_silent_wrong_by_its_sign() -> None:
    """An inside-out solid reports isValid() True and one solid; its volume is minus the
    closed form, a relative error of -2, and the sign is what keeps it from reading as ok."""
    row_class, reasons = classify_row(_built(-1.0), 1.0)
    assert row_class == "silent_wrong"
    assert reasons == ("precise rel err -2.000e+00 outside +/-1e-4",)


def test_a_row_with_two_solids_or_an_invalid_solid_names_each_reason() -> None:
    assert classify_row(_built(1.0, solids=2), 1.0) == ("silent_wrong", ("solids=2",))
    assert classify_row(_built(1.0, valid=False), 1.0) == ("silent_wrong", ("isValid False",))


@pytest.mark.parametrize("outcome", ["failure", "timeout", "worker_died"])
def test_a_row_that_was_not_built_keeps_its_class_and_carries_no_measurement(
        outcome: Literal["failure", "timeout", "worker_died"]) -> None:
    """A failed row is never a zero or a guessed number: every measurement is None (L02)."""
    record = failed_record(_REQUEST, outcome, "it broke")
    assert classify_row(record, 1.0) == (outcome, ("it broke",))
    measurements = (record["solids"], record["is_valid"], record["precise_volume"],
                    record["default_volume"], record["build_s"], record["volume_s"],
                    record["meshes"])
    assert measurements == (None,) * 7


def test_a_checked_mesh_that_is_open_inside_out_or_off_the_closed_form_is_silent_wrong() -> None:
    closed = 100.0
    ok_mesh = _mesh(volume=99.0, area=200.0)  # |99 - 100| <= 0.08 * 200
    assert classify_row(_built(closed, meshes=[ok_mesh]), closed) == ("ok", ())
    open_mesh = _mesh(watertight=False, volume=99.0, area=200.0)
    assert classify_row(_built(closed, meshes=[open_mesh]), closed) == (
        "silent_wrong", ("preview: STL not watertight (3 open edges)",))
    inside_out = _mesh(volume=-99.0, area=200.0)
    reasons = classify_row(_built(closed, meshes=[inside_out]), closed)[1]
    assert reasons == ("preview: STL signed volume -9.900e+01 <= 0",)
    far = _mesh(volume=50.0, area=200.0)  # |50 - 100| = 50 > 0.08 * 200 = 16
    far_reasons = classify_row(_built(closed, meshes=[far]), closed)[1]
    assert len(far_reasons) == 1
    assert "misses the closed form" in far_reasons[0]


def test_a_mesh_that_was_not_checked_is_neither_a_pass_nor_a_failure_and_prints_so() -> None:
    skipped = _built(1.0, meshes=[_mesh(checked=False)])
    assert classify_row(skipped, 1.0) == ("ok", ())
    assert "| not checked |" in _table_row(skipped, "ok", 1.0)


def test_a_row_with_no_measurement_prints_n_a_never_a_zero() -> None:
    cells = _table_row(failed_record(_REQUEST, "timeout", "late"), "timeout", 1.0).split("|")
    assert [c.strip() for c in cells[7:14]] == ["n/a"] * 7  # solids .. watertight, build s incl.


def test_a_record_survives_the_wire_unchanged() -> None:
    assert parse_request(json.dumps(_REQUEST)) == _REQUEST
    built = _built(1.5, meshes=[_mesh()])
    assert parse_record(json.dumps(built)) == built
    died = failed_record(_REQUEST, "worker_died", "exit 139")
    assert parse_record(json.dumps(died)) == died


def test_a_record_with_a_step_export_and_a_gzipped_mesh_survives_the_wire() -> None:
    request: RowRequest = {**_REQUEST, "step": True, "gzip_on": ["preview"]}
    mesh: MeshRecord = {**_mesh(), "gzip1_bytes": 2400, "gzip1_s": 0.002}
    record: RowRecord = {**_built(1.0, meshes=[mesh]), **request,
                         "step_bytes": 3_570_000, "step_s": 0.31}
    assert parse_record(json.dumps(record)) == record
    assert parse_request(json.dumps(request)) == request


def test_a_built_record_carries_step_exactly_when_its_request_asked_for_it() -> None:
    asked: RowRecord = {**_built(1.0), "step": True}  # asked, nothing measured
    with pytest.raises(ValueError, match="step_bytes"):
        parse_record(json.dumps(asked))
    unasked: RowRecord = {**_built(1.0), "step_bytes": 10, "step_s": 0.1}  # measured, not asked
    with pytest.raises(ValueError, match="step_bytes"):
        parse_record(json.dumps(unasked))
    half: RowRecord = {**_built(1.0), "step": True, "step_bytes": 10}
    with pytest.raises(ValueError, match="step_bytes"):
        parse_record(json.dumps(half))
    liar = {**failed_record(_REQUEST, "failure", "boom"), "step_bytes": 10, "step_s": 0.1}
    with pytest.raises(ValueError, match="STEP"):
        parse_record(json.dumps(liar))


def test_a_mesh_names_its_gzip_pair_together_and_its_check_time_with_its_check() -> None:
    lopsided: MeshRecord = {**_mesh(), "gzip1_bytes": 5}
    with pytest.raises(ValueError, match="gzip1"):
        parse_record(json.dumps(_built(1.0, meshes=[lopsided])))
    untimed: MeshRecord = {**_mesh(), "check_s": None}
    with pytest.raises(ValueError, match="check fields"):
        parse_record(json.dumps(_built(1.0, meshes=[untimed])))


_HEADER: HeaderRecord = {
    "run_id": "2026-10-08-a-grid", "block": "grid", "head": "a" * 40,
    "protocol_blob": "b" * 40, "protocol_commit": "c" * 40, "decisive": True,
    "readings": [("2026-10-08T09:00:00+00:00", 1.2), ("2026-10-08T09:00:30+00:00", 1.1)],
    "k": 5, "k_source": "selected by select_k from run 2026-10-08-a-ksweep",
}


def test_a_header_survives_the_wire_and_refuses_an_unknown_or_malformed_key() -> None:
    assert parse_header(json.dumps(_HEADER)) == _HEADER
    ksweep: HeaderRecord = {**_HEADER, "block": "ksweep", "k": None}
    assert parse_header(json.dumps(ksweep)) == ksweep
    with pytest.raises(ValueError, match="kay"):
        parse_header(json.dumps({**_HEADER, "kay": 5}))
    with pytest.raises(ValueError, match="readings"):
        parse_header(json.dumps({**_HEADER, "readings": [["only-a-time"]]}))
    with pytest.raises(ValueError, match="decisive"):
        parse_header(json.dumps({**_HEADER, "decisive": "yes"}))


def test_a_result_row_gives_back_its_record_and_needs_the_runs_own_verdict_keys() -> None:
    record = _built(1.0, meshes=[_mesh()])
    row = {**record, "closed_volume": 1.0, "rel_err": 0.0, "class": "ok", "reasons": [],
           "over_budget": []}
    assert parse_result_row(json.dumps(row)) == record
    del row["class"]
    with pytest.raises(ValueError, match="class"):
        parse_result_row(json.dumps(row))


_ROD_REQUEST: RowRequest = {
    **_REQUEST, "turns": 3.0, "length": 3.0, "presets": [("preview", 0.08, 0.5),
                                                         ("fine", 0.01, 0.1)],
    "step": True, "gzip_on": ["fine"],
}


def test_a_rod_row_meshes_gzips_checks_and_exports_step_as_the_request_asks() -> None:
    record = worker.run_row(_ROD_REQUEST)
    assert parse_record(json.dumps(record)) == record  # what the child writes parses back
    meshes = {m["preset"]: m for m in record["meshes"] or []}
    assert set(meshes) == {"preview", "fine"}
    assert meshes["preview"]["gzip1_bytes"] is None
    gzipped = meshes["fine"]["gzip1_bytes"]
    assert gzipped is not None
    assert 0 < gzipped < meshes["fine"]["bytes"]
    assert meshes["fine"]["triangles"] > meshes["preview"]["triangles"]
    assert all(m["checked"] and m["watertight"] for m in meshes.values())
    assert record["step_bytes"] is not None
    assert record["step_bytes"] > 0
    closed = maths.closed_volume(6.0, 1.0, 3.0)
    assert classify_row(record, closed) == ("ok", ())


def test_a_mesh_over_the_check_ceiling_is_recorded_as_not_checked_never_as_a_pass() -> None:
    record = worker.run_row({**_ROD_REQUEST, "step": False, "check_ceiling": 10})
    meshes = record["meshes"] or []
    assert len(meshes) == 2
    for mesh in meshes:
        assert not mesh["checked"]
        assert (mesh["watertight"], mesh["check_s"], mesh["stl_volume"]) == (None, None, None)
        assert mesh["triangles"] > 10
    assert record["step_bytes"] is None
    assert classify_row(record, maths.closed_volume(6.0, 1.0, 3.0))[0] == "ok"


def test_a_void_row_records_the_postcondition_only_against_the_closed_form_with_clearance() -> None:
    request: RowRequest = {**_REQUEST, "kind": "void", "turns": 3.0, "length": 3.0,
                           "clearance": 0.2, "presets": []}
    record = worker.run_row(request)
    assert (record["outcome"], record["solids"], record["is_valid"]) == ("built", 1, True)
    assert record["meshes"] == []
    assert record["step_bytes"] is None
    closed = maths.closed_volume(6.0, 1.0, 3.0, 0.2)
    assert classify_row(record, closed) == ("ok", ())
    assert closed > maths.closed_volume(6.0, 1.0, 3.0)  # the void really is the larger section


@pytest.mark.parametrize("extra", [{"presets": [("preview", 0.08, 0.5)]}, {"step": True}])
def test_a_void_row_that_asks_for_a_mesh_or_a_step_is_refused(extra: dict[str, object]) -> None:
    request: RowRequest = {**_REQUEST, "kind": "void", "presets": [], **extra}  # type: ignore[typeddict-item]
    record = worker.run_row(request)
    assert record["outcome"] == "failure"
    assert "void" in (record["error"] or "")


def test_a_record_with_an_unknown_key_is_refused_naming_it() -> None:
    wire = {**_built(1.0), "volumne": 1.0}
    with pytest.raises(ValueError, match="volumne"):
        parse_record(json.dumps(wire))


def test_a_record_with_a_missing_key_is_refused_naming_it() -> None:
    wire = dict(_built(1.0))
    del wire["precise_volume"]
    with pytest.raises(ValueError, match="precise_volume"):
        parse_record(json.dumps(wire))
    request = dict(_REQUEST)
    del request["pitch"]
    with pytest.raises(ValueError, match="pitch"):
        parse_request(json.dumps(request))


def test_a_number_that_is_not_finite_or_not_a_number_is_refused_at_the_boundary() -> None:
    """json.loads accepts NaN, and a NaN volume would compare as not-outside-the-tolerance."""
    with pytest.raises(ValueError, match="precise_volume"):
        parse_record(json.dumps(_built(float("nan"))))
    wire = dict(_built(1.0))
    wire["solids"] = "one"
    with pytest.raises(ValueError, match="solids"):
        parse_record(json.dumps(wire))
    with pytest.raises(ValueError, match="not JSON"):
        parse_record("not json")
    with pytest.raises(ValueError, match="not a JSON object"):
        parse_request("[1, 2]")


def test_a_built_record_missing_a_measurement_or_a_failed_one_carrying_one_is_refused() -> None:
    wire = dict(_built(1.0))
    wire["build_s"] = None
    with pytest.raises(ValueError, match="build_s"):
        parse_record(json.dumps(wire))
    liar = dict(failed_record(_REQUEST, "failure", "boom"))
    liar["precise_volume"] = 0.0
    with pytest.raises(ValueError, match="precise_volume"):
        parse_record(json.dumps(liar))
    nameless = dict(failed_record(_REQUEST, "failure", "boom"))
    nameless["error"] = None
    with pytest.raises(ValueError, match="error"):
        parse_record(json.dumps(nameless))


_Vertex = tuple[float, float, float]
_Facet = tuple[_Vertex, _Vertex, _Vertex]


def _stl(facets: Sequence[_Facet]) -> bytes:
    body = b"".join(struct.pack("<12fH", 0, 0, 0, *v0, *v1, *v2, 0) for v0, v1, v2 in facets)
    return bytes(80) + struct.pack("<I", len(facets)) + body


_TETRAHEDRON: list[_Facet] = [
    ((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)),
    ((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)),
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
]


def test_a_closed_tetrahedron_is_watertight_with_a_signed_volume_of_a_sixth() -> None:
    check = measure.stl_check(_stl(_TETRAHEDRON))
    assert check.watertight
    assert check.open_edges == 0
    assert check.triangles == 4
    assert check.signed_volume == pytest.approx(1 / 6)
    assert check.surface_area == pytest.approx(1.5 + math.sqrt(3) / 2)


def test_a_tetrahedron_missing_a_facet_is_not_watertight_and_counts_its_open_edges() -> None:
    check = measure.stl_check(_stl(_TETRAHEDRON[:3]))
    assert not check.watertight
    assert check.open_edges == 3


def test_a_tetrahedron_with_every_facet_reversed_has_a_negative_volume() -> None:
    reversed_facets = [(v0, v2, v1) for v0, v1, v2 in _TETRAHEDRON]
    check = measure.stl_check(_stl(reversed_facets))
    assert check.signed_volume == pytest.approx(-1 / 6)
    assert check.watertight  # inside out is still closed: sign is what tells them apart


def test_an_empty_stl_is_not_a_watertight_one() -> None:
    assert not measure.stl_check(_stl([])).watertight


def test_a_real_m6_right_hand_five_turn_rod_passes_the_row_verdict() -> None:
    """Built in this process, judged by the kernel-free closed form: one solid, valid, and a
    precise volume within T_PASS. The precise volume is what this verdict reads; the default
    Volume() is only a reference column."""
    d, pitch, turns = 6.0, 1.0, 5.0
    shape = helical.thread(d, pitch, turns, k=5)
    precise = measure.precise_volume(shape)
    record = _built(precise)
    record["solids"] = len(shape.Solids())
    record["is_valid"] = bool(shape.isValid())
    closed = maths.closed_volume(d, pitch, turns * pitch)
    assert record["solids"] == 1
    assert classify_row(record, closed) == ("ok", ())
    assert abs(relative_error(precise, closed)) < T_PASS
    data, _ = measure.mesh_stl(shape, *maths.INTERIM_PRESETS["preview"])
    assert measure.stl_check(data).watertight


def test_a_worker_round_trip_returns_one_record_per_request_and_survives_a_bad_rod() -> None:
    """A rod the kernel cannot build (d = 1e-9) is a recorded failure or a silent-wrong row,
    never a crash of the parent, and the same child still serves the next request."""
    worker = Worker()
    try:
        first = worker.run(_REQUEST, ROW_TIMEOUT_S)
        bad_request: RowRequest = {**_REQUEST, "size": "bad", "d": 1e-9}
        bad = worker.run(bad_request, ROW_TIMEOUT_S)
        third = worker.run(_REQUEST, ROW_TIMEOUT_S)
    finally:
        worker.close()
    closed = maths.closed_volume(6.0, 1.0, 5.0)
    assert classify_row(first, closed) == ("ok", ())
    bad_closed = maths.closed_volume(1e-9, 1.0, 5.0)
    assert classify_row(bad, bad_closed)[0] in ("failure", "silent_wrong")
    assert classify_row(third, closed) == ("ok", ())
    assert third["size"] == "M6"


def test_a_worker_that_dies_is_one_worker_died_row_with_its_return_code() -> None:
    worker = Worker(argv=[sys.executable, "-c", "import os; os._exit(3)"])
    try:
        record = worker.run(_REQUEST, 30.0)
    finally:
        worker.close()
    assert record["outcome"] == "worker_died"
    assert record["error"] is not None
    assert "return code 3" in record["error"]
    assert record["precise_volume"] is None


def test_a_worker_killed_by_a_signal_reports_the_negative_return_code() -> None:
    script = "import os, signal; os.kill(os.getpid(), signal.SIGSEGV)"
    worker = Worker(argv=[sys.executable, "-c", script])
    try:
        record = worker.run(_REQUEST, 30.0)
    finally:
        worker.close()
    assert record["outcome"] == "worker_died"
    assert record["error"] is not None
    assert "return code -11" in record["error"]


def test_a_worker_that_does_not_answer_in_time_is_killed_and_recorded_as_a_timeout() -> None:
    worker = Worker(argv=[sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        record = worker.run(_REQUEST, 0.5)
    finally:
        worker.close()
    assert record["outcome"] == "timeout"
    assert record["solids"] is None


def test_a_worker_that_speaks_garbage_is_one_failure_row_and_not_reused() -> None:
    worker = Worker(argv=[sys.executable, "-c", "print('garbage')"])
    try:
        record = worker.run(_REQUEST, 30.0)
    finally:
        worker.close()
    assert record["outcome"] == "failure"
    assert record["error"] is not None
    assert "unreadable worker output" in record["error"]


# --- the pre-registration guard ------------------------------------------------------------

_PROTOCOL = "# Phase 2\n\n## Question\nWhich construction?\n\n## Results\n\nNo run yet.\n"


def _guard(local: str | None = _PROTOCOL, main: str | None = _PROTOCOL, *,
           fetched: bool = True, ancestor: bool = True) -> tuple[bool, tuple[str, ...]]:
    result = protocol_guard(local, main, fetched=fetched, landed_is_ancestor=ancestor)
    return result.held, result.reasons


def test_the_guard_holds_when_the_protocol_is_on_main_unchanged_and_an_ancestor() -> None:
    assert _guard() == (True, ())


def test_the_guard_refuses_when_origin_main_was_not_fetched() -> None:
    held, reasons = _guard(fetched=False)
    assert not held
    assert len(reasons) == 1
    assert "not fetched" in reasons[0]


def test_the_guard_refuses_when_the_protocol_is_missing_from_the_working_tree() -> None:
    held, reasons = _guard(local=None)
    assert not held
    assert len(reasons) == 1
    assert "working tree" in reasons[0]


def test_the_guard_refuses_when_the_protocol_is_missing_from_origin_main() -> None:
    held, reasons = _guard(main=None)
    assert not held
    assert len(reasons) == 1
    assert "origin/main has no protocol" in reasons[0]


def test_the_guard_refuses_when_either_text_has_no_results_line() -> None:
    headless = "# Phase 2\n\n## Question\nWhich construction?\n"
    held, reasons = _guard(local=headless)
    assert not held
    assert len(reasons) == 1
    assert "working tree" in reasons[0]
    assert "## Results" in reasons[0]
    held, reasons = _guard(main=headless)
    assert not held
    assert len(reasons) == 1
    assert "origin/main" in reasons[0]
    assert "## Results" in reasons[0]


def test_the_guard_refuses_a_single_changed_character_before_the_results_line() -> None:
    edited = _PROTOCOL.replace("Which", "Whish")
    held, reasons = _guard(local=edited)
    assert not held
    assert len(reasons) == 1
    assert "differs" in reasons[0]


def test_the_guard_refuses_when_the_protocol_commit_is_not_an_ancestor_of_head() -> None:
    """A branch cut from the pre-squash PR 1 branch: the same text, but the commit that put it
    on origin/main is not in this branch's history (RESEARCH Pitfall 10)."""
    held, reasons = _guard(ancestor=False)
    assert not held
    assert len(reasons) == 1
    assert "ancestor" in reasons[0]


def test_the_guard_names_every_reason_not_only_the_first() -> None:
    held, reasons = _guard(local=None, main=None, fetched=False, ancestor=False)
    assert not held
    assert len(reasons) == 4


def test_the_text_after_the_results_line_may_differ_freely() -> None:
    """PR 2 writes the Results and the Verdict, and that must not trip the guard."""
    written = _PROTOCOL.replace("No run yet.", "Run 1: see bench/RESULTS.md.\n\n## Verdict\nx")
    assert _guard(local=written) == (True, ())


def test_the_results_boundary_is_the_first_line_that_is_exactly_the_heading() -> None:
    assert before_results(_PROTOCOL) == "# Phase 2\n\n## Question\nWhich construction?\n\n"
    twice = _PROTOCOL + "\n## Results\nagain\n"
    assert before_results(twice) == before_results(_PROTOCOL)


def test_a_heading_that_only_starts_with_the_results_words_is_no_boundary() -> None:
    assert before_results("# A\n\n## Results and more\n") is None
    assert before_results("# A\n\n### Results\n") is None
    assert before_results("# A\n") is None


def _git(cwd: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-c", "user.name=spike", "-c", "user.email=spike@example.com",
         "-c", "commit.gpgsign=false", *args],
        cwd=cwd, capture_output=True, text=True, check=True)
    return done.stdout.strip()


def _repo_with_protocol(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *,
                        landed: bool) -> tuple[Path, str]:
    """A throwaway clone of a throwaway origin whose `main` carries the protocol commit when
    `landed`, and a local-only protocol commit when not. Returns the clone and that commit.
    The guard's git wiring runs against it for real: no mock stands in for git."""
    # A commit hook hands its children GIT_DIR / GIT_INDEX_FILE for the outer repo; left in
    # place, every git call below (and the guard's own) would act on that repo, not the
    # throwaway one -- found when this suite first ran inside `git commit`'s pre-commit hook.
    for name in [n for n in os.environ if n.startswith("GIT_")]:
        monkeypatch.delenv(name)
    origin = tmp_path / "origin.git"
    work = tmp_path / "work"
    _git(tmp_path, "init", "--bare", "-b", "main", str(origin))
    _git(tmp_path, "init", "-b", "main", str(work))
    _git(work, "remote", "add", "origin", str(origin))
    (work / "README").write_text("start\n")
    _git(work, "add", "README")
    _git(work, "commit", "-m", "start")
    _git(work, "push", "origin", "main")
    protocol = work / PROTOCOL_PATH
    protocol.parent.mkdir(parents=True)
    protocol.write_text(_PROTOCOL)
    _git(work, "add", PROTOCOL_PATH)
    _git(work, "commit", "-m", "protocol")
    commit = _git(work, "rev-parse", "HEAD")
    if landed:
        _git(work, "push", "origin", "main")
    monkeypatch.setattr(spike_cli, "_REPO_ROOT", work)
    return work, commit


def test_the_guard_reads_real_git_and_refuses_while_the_protocol_is_not_on_origin_main(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _repo_with_protocol(tmp_path, monkeypatch, landed=False)
    assert spike_cli.check_protocol() == 2
    err = capsys.readouterr().err
    assert err.startswith("protocol guard: refused -- ")
    assert "origin/main has no protocol file" in err


def test_the_guard_reads_real_git_and_holds_once_the_protocol_has_landed(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _, commit = _repo_with_protocol(tmp_path, monkeypatch, landed=True)
    assert spike_cli.check_protocol() == 0
    out = capsys.readouterr().out
    assert out.startswith("protocol guard: held")
    assert commit in out


def test_the_guard_refuses_a_branch_cut_before_the_protocol_landed(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    """The same protocol text in the working tree, but the commit that put it on origin/main is
    not in this branch's history: only the ancestor check can tell."""
    work, _ = _repo_with_protocol(tmp_path, monkeypatch, landed=True)
    _git(work, "checkout", "-b", "old", "HEAD~1")
    (work / PROTOCOL_PATH).parent.mkdir(parents=True)
    (work / PROTOCOL_PATH).write_text(_PROTOCOL)
    assert spike_cli.check_protocol() == 2
    err = capsys.readouterr().err
    assert "ancestor" in err
    assert "differs" not in err


def test_the_guard_refuses_an_edit_before_results_and_allows_one_after_it(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    work, _ = _repo_with_protocol(tmp_path, monkeypatch, landed=True)
    path = work / PROTOCOL_PATH
    path.write_text(_PROTOCOL.replace("Which", "Whish"))
    assert spike_cli.check_protocol() == 2
    assert "differs" in capsys.readouterr().err
    path.write_text(_PROTOCOL.replace("No run yet.", "Run 1: see bench/RESULTS.md."))
    assert spike_cli.check_protocol() == 0


# --- Pre-registered rod verdict rules (Phase 2, plan 02-03): synthetic records, no kernel ---

_Fine = tuple[int, int, float, int | None]  # triangles, bytes, mesh seconds, gzip-1 bytes
_RowCls = Literal["ok", "silent_wrong", "failure", "timeout", "worker_died"]


def _synth(size: str = "M6", kind: str = "rod", *, left: bool = False, turns: float = 60.0,
           k: int = 5, cls: _RowCls = "ok", err: float = 0.0, build_s: float = 1.0,
           fine: _Fine | None = (1000, 1000, 1.0, 500), preview: bool = True,
           step: tuple[int, float] | None = (100, 1.0), volume_s: float = 0.1,
           stl_err: float | None = None, preview_s: float = 0.01) -> RowRecord:
    """A rod or void row of `size` at `turns`, with the measurements the rules read. An `ok`
    row sits `err` off its closed form; `silent_wrong` is two solids; the other classes carry
    nothing, as the runner records them. The preview mesh is checked, with a signed volume
    `stl_err` off the closed form, only when `stl_err` is given."""
    d_exact, pitch_exact = maths.PITCH[size]
    d, pitch = float(d_exact), float(pitch_exact)
    length = turns * pitch
    clearance = maths.VOID_CLEARANCE if kind == "void" else 0.0
    rod = kind == "rod"
    presets = ([("preview", 0.08, 0.5)] if preview else []) + ([("fine", 0.01, 0.1)] if fine
                                                               else [])
    request: RowRequest = {
        "kind": kind, "size": size, "d": d, "pitch": pitch, "turns": turns, "length": length,
        "left_hand": left, "k": k, "clearance": clearance, "presets": presets if rod else [],
        "step": rod and step is not None, "gzip_on": ["fine"] if rod and fine else [],
        "check_ceiling": FINE_CHECK_CEILING,
    }
    if cls in ("failure", "timeout", "worker_died"):
        return failed_record(request, cls, "it broke")
    closed = maths.closed_volume(d, pitch, length, clearance)
    meshes: list[MeshRecord] = []
    if rod and preview:
        checked = stl_err is not None
        meshes.append({
            "preset": "preview", "tolerance": 0.08, "angular": 0.5, "triangles": 100,
            "bytes": 5084, "mesh_s": preview_s, "gzip1_bytes": None, "gzip1_s": None,
            "checked": checked, "check_s": 0.0 if checked else None,
            "watertight": True if checked else None, "open_edges": 0 if checked else None,
            "stl_volume": closed * (1 + (stl_err or 0.0)) if checked else None,
            "surface_area": 1e12 if checked else None,  # a band wide enough to never trip
        })
    if rod and fine:
        triangles, nbytes, mesh_s, gzip_bytes = fine
        meshes.append({
            "preset": "fine", "tolerance": 0.01, "angular": 0.1, "triangles": triangles,
            "bytes": nbytes, "mesh_s": mesh_s, "gzip1_bytes": gzip_bytes,
            "gzip1_s": None if gzip_bytes is None else 0.1, "checked": False, "check_s": None,
            "watertight": None, "open_edges": None, "stl_volume": None, "surface_area": None,
        })
    return {
        **request, "outcome": "built", "error": None, "solids": 2 if cls == "silent_wrong" else 1,
        "is_valid": True, "precise_volume": closed * (1 + err), "default_volume": closed,
        "build_s": build_s, "volume_s": volume_s, "meshes": meshes,
        "step_bytes": step[0] if rod and step else None,
        "step_s": step[1] if rod and step else None,
    }


_BUDGET_BYTES = 64 * 1024 * 1024
_NOT_ESTABLISHED = "seconds not established (non-decisive gate)"


def test_the_budgets_are_the_interim_30_seconds_and_64_mebibytes() -> None:
    assert BUDGET_S == 30.0
    assert BUDGET_BYTES == _BUDGET_BYTES
    assert (GATE_FACTOR, ESTIMATOR_TIE) == (10, 2.0)


def test_a_budget_request_costs_build_plus_the_slower_of_the_fine_stl_and_the_step_export() -> None:
    row = _synth(build_s=2.0, fine=(1, 1, 3.0, 1), step=(1, 5.0))
    assert request_seconds(row) == 7.0
    assert request_seconds(_synth(build_s=2.0, fine=(1, 1, 9.0, 1), step=(1, 5.0))) == 11.0


def test_a_request_with_a_part_missing_has_no_seconds_rather_than_a_partial_sum_budget() -> None:
    assert request_seconds(_synth(step=None)) is None
    assert request_seconds(_synth(fine=None)) is None
    assert request_seconds(_synth(kind="void")) is None
    assert request_seconds(_synth(cls="timeout")) is None


def test_a_row_of_exactly_64_mib_raw_plus_gzip_is_inside_the_budget_and_one_byte_more_is_over(
) -> None:
    inside = _synth(fine=(1, _BUDGET_BYTES - 500, 1.0, 500))
    over = _synth(fine=(1, _BUDGET_BYTES - 499, 1.0, 500))
    for decisive in (True, False):  # bytes are integers and need no quiet host
        assert over_budget(inside, decisive) == ()
        reasons = over_budget(over, decisive)
        assert len(reasons) == 1
        assert reasons[0].startswith("over budget")
        assert str(_BUDGET_BYTES + 1) in reasons[0]


def test_a_row_of_exactly_30_seconds_is_inside_the_budget_and_the_next_float_is_over() -> None:
    inside = _synth(build_s=0.5, fine=(1, 1, 29.5, None), step=(1, 0.0))
    over = _synth(build_s=math.nextafter(30.0, math.inf), fine=(1, 1, 0.0, None), step=(1, 0.0))
    assert request_seconds(inside) == 30.0
    assert over_budget(inside, True) == ()
    reasons = over_budget(over, True)
    assert len(reasons) == 1
    assert reasons[0].startswith("over budget")


def test_a_slow_row_on_a_non_decisive_gate_is_seconds_not_established_never_over_budget() -> None:
    slow = _synth(build_s=40.0)
    assert over_budget(slow, False) == (_NOT_ESTABLISHED,)
    assert over_budget(_synth(build_s=1.0), False) == ()


def test_a_timeout_is_an_over_budget_cap_on_a_decisive_gate_and_not_established_otherwise() -> None:
    timed_out = _synth(cls="timeout")
    decisive = over_budget(timed_out, True)
    assert len(decisive) == 1
    assert decisive[0].startswith("over budget")
    assert "timeout" in decisive[0]
    assert over_budget(timed_out, False) == (_NOT_ESTABLISHED,)


def test_the_frontier_stop_is_none_while_both_rows_are_ok_and_fast() -> None:
    assert frontier_stop(_synth(), _synth(kind="void"), "ok", "ok", True) is None


@pytest.mark.parametrize(("rod_class", "void_class", "named"), [
    ("silent_wrong", "ok", "rod silent_wrong"),
    ("ok", "failure", "void failure"),
    ("worker_died", "timeout", "rod worker_died"),
])
def test_a_frontier_stop_names_the_first_row_that_is_not_ok(
        rod_class: _RowCls, void_class: _RowCls, named: str) -> None:
    reason = frontier_stop(_synth(), _synth(kind="void"), rod_class, void_class, False)
    assert reason is not None
    assert named in reason


def test_build_plus_fine_mesh_over_30_seconds_is_a_frontier_stop_only_on_a_decisive_gate() -> None:
    inside = _synth(build_s=0.5, fine=(1, 1, 29.5, None))
    over = _synth(build_s=0.5, fine=(1, 1, math.nextafter(29.5, math.inf), None))
    void = _synth(kind="void")
    assert frontier_stop(inside, void, "ok", "ok", True) is None
    reason = frontier_stop(over, void, "ok", "ok", True)
    assert reason is not None
    assert "30" in reason
    assert frontier_stop(over, void, "ok", "ok", False) is None  # not established, so no stop


def _ksweep(k: int, *, triangles: int = 1000, step_bytes: int = 100, cls: _RowCls = "ok",
            err: float = 0.0, far: _RowCls = "ok") -> list[RowRecord]:
    """One K's sweep rows for M6: the standard max (60 turns) rod and void, and the 250-turn rod
    (preview only) and void."""
    return [
        _synth(k=k, cls=cls, err=err, fine=(triangles, 1000, 1.0, 500), step=(step_bytes, 1.0)),
        _synth(kind="void", k=k),
        _synth(k=k, turns=250.0, cls=far, fine=None, step=None),
        _synth(kind="void", k=k, turns=250.0),
    ]


def test_select_k_takes_the_fewest_fine_triangles_at_the_standard_max() -> None:
    rows = _ksweep(3, triangles=900) + _ksweep(5, triangles=1000) + _ksweep(10, triangles=1100)
    assert select_k(rows) == 3


def test_select_k_breaks_a_triangle_tie_by_step_bytes_then_by_the_smaller_k() -> None:
    by_step = _ksweep(3, step_bytes=300) + _ksweep(5, step_bytes=100) + _ksweep(10, step_bytes=200)
    assert select_k(by_step) == 5
    by_k = _ksweep(10) + _ksweep(5) + _ksweep(3)
    assert select_k(by_k) == 3


def test_select_k_ignores_the_250_turn_rows_when_it_counts_triangles() -> None:
    rows = _ksweep(3, triangles=900) + _ksweep(5, triangles=1000)
    rows[2]["meshes"] = [{**_mesh(checked=False), "triangles": 10**9}]  # K = 3's 250-turn mesh
    assert select_k(rows) == 3


@pytest.mark.parametrize(("bad", "why"), [
    ({"cls": "silent_wrong"}, "a silent_wrong row"),
    ({"err": 2 * T_PASS}, "a precise error outside T_PASS"),
    ({"far": "failure"}, "a non-ok 250-turn row"),
    ({"far": "timeout"}, "a timed-out 250-turn row"),
])
def test_select_k_excludes_a_k_with_any_non_ok_sweep_row(bad: dict[str, object],
                                                         why: str) -> None:
    rows = _ksweep(3, triangles=1, **bad) + _ksweep(5, triangles=1000)  # type: ignore[arg-type]
    assert select_k(rows) == 5, why


def test_select_k_is_none_when_every_k_is_excluded() -> None:
    rows = [r for k in (3, 5, 10) for r in _ksweep(k, cls="silent_wrong")]
    assert select_k(rows) is None


def test_select_k_refuses_a_standard_max_rod_it_cannot_score() -> None:
    rows = _ksweep(3)
    rows[0]["meshes"] = []  # the standard-max rod carries no fine mesh
    with pytest.raises(ValueError, match="fine"):
        select_k(rows)


def _estimator_rows(precise: float, stl: float, *, precise_s: float = 0.1,
                    stl_s: float = 0.1) -> list[RowRecord]:
    return [_synth(turns=turns, err=precise, stl_err=stl, volume_s=precise_s, preview_s=stl_s)
            for turns in (5.0, 10.0, 20.0)]


def test_the_estimator_with_the_smaller_max_error_wins_when_they_are_not_within_2x() -> None:
    name, err, gate = select_estimator(_estimator_rows(1e-6, 1e-3))
    assert name == "precise"
    assert err == pytest.approx(1e-6)
    assert gate == gate_tolerance(err) == pytest.approx(1e-5)
    name, err, _ = select_estimator(_estimator_rows(8e-5, 1e-5, precise_s=0.01, stl_s=9.0))
    assert name == "stl"  # accuracy beats cost outside the tie
    assert err == pytest.approx(1e-5)


def test_estimators_within_2x_tie_and_the_cheaper_by_median_seconds_wins() -> None:
    assert select_estimator(_estimator_rows(1.99e-5, 1e-5, precise_s=2.0, stl_s=0.5))[0] == "stl"
    assert select_estimator(_estimator_rows(1.99e-5, 1e-5, precise_s=0.5, stl_s=2.0))[0] == (
        "precise")
    # past 2x it is no tie: the smaller error wins however much it costs
    assert select_estimator(_estimator_rows(2.01e-5, 1e-5, precise_s=0.5, stl_s=2.0))[0] == "stl"
    assert select_estimator(_estimator_rows(1e-5, 2.01e-5, precise_s=2.0, stl_s=0.5))[0] == (
        "precise")


def test_a_tied_estimator_pair_with_equal_cost_goes_to_the_smaller_error() -> None:
    assert select_estimator(_estimator_rows(1.5e-5, 1e-5))[0] == "stl"
    assert select_estimator(_estimator_rows(1e-5, 1.5e-5))[0] == "precise"


def test_the_estimator_reads_only_ok_rod_rows_and_refuses_an_empty_set() -> None:
    rows = [*_estimator_rows(1e-6, 1e-3), _synth(cls="silent_wrong", err=0.5, stl_err=1e-9)]
    assert select_estimator(rows)[0] == "precise"  # the wrong row's tiny stl error is not read
    with pytest.raises(ValueError, match="no"):
        select_estimator([_synth(kind="void"), _synth(cls="failure")])


@pytest.mark.parametrize(("err", "gate"), [(7.6e-6, 8e-5), (1e-5, 1e-4), (2.7e-5, 3e-4),
                                           (1.0001e-5, 2e-4)])
def test_gate_tolerance_is_ten_times_the_error_rounded_up_to_one_significant_figure(
        err: float, gate: float) -> None:
    assert gate_tolerance(err) == gate


@pytest.mark.parametrize("err", [0.0, -1e-5, math.nan, math.inf])
def test_gate_tolerance_refuses_an_error_it_cannot_honestly_scale(err: float) -> None:
    with pytest.raises(ValueError, match="gate"):
        gate_tolerance(err)


def test_the_pass_bar_holds_over_ok_rows_of_both_hands() -> None:
    rows = [_synth(left=False), _synth(left=True), _synth(kind="void", left=True)]
    assert pass_bar(rows, True) == ("held", ())
    assert pass_bar(rows, False) == ("held", ())


@pytest.mark.parametrize("cls", ["silent_wrong", "failure", "worker_died"])
@pytest.mark.parametrize("left", [False, True])
def test_the_pass_bar_fails_naming_the_row_on_one_bad_row_of_either_hand(
        cls: _RowCls, left: bool) -> None:
    rows = [_synth(), _synth(left=left, turns=30.0, cls=cls, size="M3")]
    verdict, reasons = pass_bar(rows, True)
    assert verdict == "failed"
    assert len(reasons) == 1
    assert "M3" in reasons[0]
    assert cls in reasons[0]
    assert ("left" if left else "right") in reasons[0]


def test_a_timeout_makes_the_pass_bar_not_established_on_a_non_decisive_gate() -> None:
    rows = [_synth(), _synth(cls="timeout", size="M20")]
    verdict, reasons = pass_bar(rows, False)
    assert verdict == "not established"
    assert "M20" in reasons[0]


def test_a_timeout_is_an_over_budget_cap_and_not_a_failure_of_the_pass_bar_when_decisive() -> None:
    assert pass_bar([_synth(), _synth(cls="timeout")], True) == ("held", ())


def test_a_failure_outranks_a_timeout_in_the_pass_bar_on_a_non_decisive_gate() -> None:
    rows = [_synth(cls="timeout"), _synth(cls="silent_wrong", size="M3")]
    verdict, reasons = pass_bar(rows, False)
    assert verdict == "failed"
    assert len(reasons) == 1


def _walk(size: str, left: bool, stop_at: int | None, *, rod_cls: _RowCls = "silent_wrong",
          end: int = 250) -> list[RowRecord]:
    """Frontier rows of `size` and one hand: rod and void at every step from the first
    frontier turn to `end`, the walk ending at `stop_at` with the rod in class `rod_cls`."""
    d, pitch = maths.PITCH[size]
    rows: list[RowRecord] = []
    for turns in maths.frontier_turns(d, pitch):
        if turns > end:
            break
        stopped = turns == stop_at
        rows.append(_synth(size, left=left, turns=float(turns),
                           cls=rod_cls if stopped else "ok"))
        rows.append(_synth(size, "void", left=left, turns=float(turns)))
        if stopped:
            break
    return rows


def _full_walk(size: str = "M6", stop_at: int | None = None, **kwargs: object) -> list[RowRecord]:
    return (_walk(size, False, stop_at, **kwargs)  # type: ignore[arg-type]
            + _walk(size, True, None))


def test_the_construction_turn_cap_is_the_last_ok_frontier_turn_before_the_stop() -> None:
    caps = turn_caps([], _full_walk(stop_at=80), True)
    cap = caps["M6"]
    assert cap.construction_turns == 75
    assert "rod silent_wrong" in cap.stop_reason
    assert "80" in cap.stop_reason
    assert "right" in cap.stop_reason


def test_the_turn_cap_is_250_when_no_hand_stopped() -> None:
    cap = turn_caps([], _full_walk(stop_at=None), True)["M6"]
    assert cap.construction_turns == 250
    assert "250" in cap.stop_reason


def test_a_stop_at_the_first_frontier_step_gives_a_turn_cap_of_the_standard_max() -> None:
    cap = turn_caps([], _full_walk(stop_at=65), True)["M6"]
    assert cap.construction_turns == 60  # M6's standard max is 60 turns, already in the grid


def test_the_smaller_construction_turn_cap_of_the_two_hands_is_the_size_cap() -> None:
    rows = _walk("M6", False, 100) + _walk("M6", True, 80)
    cap = turn_caps([], rows, True)["M6"]
    assert cap.construction_turns == 75
    assert "left" in cap.stop_reason


def test_a_frontier_walk_that_ends_early_gives_no_turn_cap_as_incomplete() -> None:
    cap = turn_caps([], _walk("M6", False, None, end=100) + _walk("M6", True, None), True)["M6"]
    assert cap.construction_turns is None
    assert "incomplete" in cap.stop_reason


def test_a_size_with_no_frontier_rows_has_no_turn_cap() -> None:
    cap = turn_caps([_synth()], [], True)["M6"]
    assert cap.construction_turns is None
    assert "no frontier record" in cap.stop_reason


def test_a_frontier_timeout_turn_cap_stops_when_decisive_and_is_not_established_otherwise() -> None:
    rows = _full_walk(stop_at=80, rod_cls="timeout")
    assert turn_caps([], rows, True)["M6"].construction_turns == 75
    cap = turn_caps([], rows, False)["M6"]
    assert cap.construction_turns is None
    assert "not established" in cap.stop_reason


def _heavy(turns: float, *, left: bool = False) -> RowRecord:
    """A rod row whose fine STL plus gzip-1 is one byte over the 64 MiB budget."""
    return _synth(left=left, turns=turns, fine=(1, _BUDGET_BYTES, 1.0, 1))


def test_the_bytes_cap_is_the_largest_grid_length_below_the_first_over_budget_row() -> None:
    grid = [_synth(turns=10.0), _synth(turns=20.0), _heavy(30.0), _synth(turns=40.0),
            _synth(turns=10.0, left=True), _heavy(20.0, left=True)]
    cap = turn_caps(grid, [], False)["M6"]
    assert (cap.bytes_cap_length, cap.bytes_cap_turns) == (10.0, 10.0)  # the left hand's 20 wins


def test_there_is_no_bytes_turn_cap_when_no_row_is_over_and_zero_when_the_shortest_is() -> None:
    assert turn_caps([_synth(turns=10.0)], [], False)["M6"].bytes_cap_length is None
    cap = turn_caps([_heavy(10.0), _synth(turns=20.0)], [], False)["M6"]
    assert (cap.bytes_cap_length, cap.bytes_cap_turns) == (0.0, 0.0)


def test_the_seconds_turn_cap_exists_only_from_a_decisive_grid_run() -> None:
    slow = _synth(turns=30.0, build_s=40.0)
    grid = [_synth(turns=10.0), _synth(turns=20.0), slow]
    decisive = turn_caps(grid, [], True)["M6"]
    assert (decisive.seconds_cap_length, decisive.seconds_established) == (20.0, True)
    loose = turn_caps(grid, [], False)["M6"]
    assert (loose.seconds_cap_length, loose.seconds_established) == (None, False)
    quick = turn_caps([_synth(turns=10.0)], [], True)["M6"]
    assert (quick.seconds_cap_length, quick.seconds_established) == (None, True)


def test_a_timed_out_grid_row_sets_the_seconds_turn_cap_on_a_decisive_gate() -> None:
    grid = [_synth(turns=10.0), _synth(turns=20.0, cls="timeout")]
    assert turn_caps(grid, [], True)["M6"].seconds_cap_length == 10.0


# --- The guarded campaign blocks (Phase 2, plan 02-03) ---


def _ok_record(request: RowRequest) -> RowRecord:
    """What a healthy child would answer for `request`: exactly the closed form, one valid solid,
    unchecked meshes (the check is the kernel's business, not this plumbing's)."""
    closed = maths.closed_volume(request["d"], request["pitch"], request["length"],
                                 request["clearance"])
    meshes: list[MeshRecord] = [{
        "preset": name, "tolerance": tol, "angular": ang, "triangles": 10, "bytes": 100,
        "mesh_s": 0.001, "gzip1_bytes": 50 if name in request["gzip_on"] else None,
        "gzip1_s": 0.001 if name in request["gzip_on"] else None, "checked": False,
        "check_s": None, "watertight": None, "open_edges": None, "stl_volume": None,
        "surface_area": None,
    } for name, tol, ang in request["presets"]]
    return {
        **request, "outcome": "built", "error": None, "solids": 1, "is_valid": True,
        "precise_volume": closed, "default_volume": closed, "build_s": 0.1, "volume_s": 0.1,
        "meshes": meshes, "step_bytes": 1000 if request["step"] else None,
        "step_s": 0.01 if request["step"] else None,
    }


class _FakeWorker(Worker):
    """Answers every request in-process without a kernel; a rod of `fail_size`, `fail_left` at
    `fail_turns` turns fails. Records every request it was given."""

    def __init__(self, fail: tuple[str, bool, float] | None = None) -> None:
        super().__init__()
        self.fail = fail
        self.requests: list[RowRequest] = []

    def run(self, request: RowRequest, timeout_s: float) -> RowRecord:
        del timeout_s
        self.requests.append(request)
        if self.fail == (request["size"], request["left_hand"], request["turns"]) and (
                request["kind"] == "rod"):
            return failed_record(request, "failure", "boom")
        return _ok_record(request)

    def close(self) -> None:
        return None


def _campaign(fail: tuple[str, bool, float] | None = None) -> tuple[spike_cli.Campaign,
                                                                     _FakeWorker]:
    fake = _FakeWorker(fail)
    return spike_cli.Campaign(fake, True, None), fake


def test_a_run_id_is_lower_case_letters_digits_and_hyphens_up_to_64_characters() -> None:
    for good in ("2026-10-08-a-grid", "a", "0", "a" * 64):
        assert spike_cli.RUN_ID.fullmatch(good), good
    for bad in ("../x", "A", "", "a" * 65, "-a", "a/b", "a.b", "a b", "a\n", "é"):
        assert not spike_cli.RUN_ID.fullmatch(bad), bad


def _forbid_everything_after_the_id_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*args: object, **kwargs: object) -> None:
        raise AssertionError("a refused run id reached the guard, the gate or a build")

    monkeypatch.setattr(spike_cli, "read_guard", boom)
    monkeypatch.setattr(spike_cli, "wait_quiet", boom)
    monkeypatch.setattr(spike_cli, "Worker", boom)


@pytest.mark.parametrize("run_id", ["../x", "A", "", "a" * 65])
def test_a_run_id_that_is_not_a_run_id_is_refused_with_exit_2_before_anything_runs(
        run_id: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _forbid_everything_after_the_id_checks(monkeypatch)
    assert spike_cli.run_block("ksweep", run_id, None, results_dir=tmp_path) == 2
    assert "fullmatch" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_a_run_id_already_recorded_is_refused_with_exit_2_before_any_build_and_left_intact(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _forbid_everything_after_the_id_checks(monkeypatch)
    (tmp_path / "taken.jsonl").write_text("what the first run measured\n")
    assert spike_cli.run_block("ksweep", "taken", None, results_dir=tmp_path) == 2
    assert "already recorded" in capsys.readouterr().err
    assert (tmp_path / "taken.jsonl").read_text() == "what the first run measured\n"


@pytest.mark.parametrize(("block", "k_from", "wanted"), [
    ("ksweep", "some-run", "takes no --k-from"),
    ("grid", None, "requires --k-from"),
    ("frontier", "../x", "not a run id"),
])
def test_k_comes_only_from_a_ksweep_run_so_the_other_blocks_demand_one(
        block: str, k_from: str | None, wanted: str, tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _forbid_everything_after_the_id_checks(monkeypatch)
    assert spike_cli.run_block(block, "a-run", k_from, results_dir=tmp_path) == 2
    assert wanted in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_a_refused_protocol_guard_writes_nothing_and_exits_2(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    refused = spike_cli.GuardFacts(GuardResult(False, ("it has not landed",)), "none", "none", "h")
    _guard_says(monkeypatch, refused)
    monkeypatch.setattr(spike_cli, "wait_quiet", lambda: pytest.fail("waited for a quiet host"))
    target = tmp_path / "results"
    assert spike_cli.run_block("ksweep", "a-run", None, results_dir=target) == 2
    assert "protocol guard: refused -- it has not landed" in capsys.readouterr().err
    assert not target.exists()


def _guard_says(monkeypatch: pytest.MonkeyPatch, facts: spike_cli.GuardFacts) -> None:
    def read_guard(*, fetch: bool) -> spike_cli.GuardFacts:
        assert fetch  # a campaign run fetches: only then is "on origin/main" a fact
        return facts

    monkeypatch.setattr(spike_cli, "read_guard", read_guard)


def _write_run(path: Path, block: str, rows: list[RowRecord]) -> None:
    """A recorded run as a campaign writes it: the header, then one row per line carrying the
    run's own verdict keys."""
    header: HeaderRecord = {**_HEADER, "block": block, "k": None, "run_id": path.stem}
    lines = [json.dumps(header)]
    for row in rows:
        closed = maths.closed_volume(row["d"], row["pitch"], row["length"], row["clearance"])
        lines.append(json.dumps({**row, "closed_volume": closed, "rel_err": None,
                                 "class": "ok", "reasons": [], "over_budget": []}))
    path.write_text("\n".join(lines) + "\n")


def _held(monkeypatch: pytest.MonkeyPatch, *, decisive: bool = True) -> None:
    held = spike_cli.GuardFacts(GuardResult(True, ()), "b" * 40, "c" * 40, "a" * 40)
    _guard_says(monkeypatch, held)
    readings = (Reading("2026-10-08T09:00:00+00:00", 1.2), Reading("2026-10-08T09:00:30+00:00",
                                                                    1.1))
    monkeypatch.setattr(spike_cli, "wait_quiet", lambda: QuietResult(decisive, readings))
    monkeypatch.setattr(spike_cli, "Worker", _FakeWorker)


def _one_row_block(c: spike_cli.Campaign, k: int, smoke: bool) -> None:
    assert not smoke
    c.measure({**_REQUEST, "k": k, "turns": 3.0, "length": 3.0})


def test_a_run_writes_its_header_first_then_one_row_per_line_and_never_overwrites_itself(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _held(monkeypatch)
    monkeypatch.setitem(spike_cli.BLOCKS, "grid", _one_row_block)
    ksweep = [r for k in (3, 5, 10) for r in _ksweep(k, triangles=1000 + k)]
    _write_run(tmp_path / "2026-10-08-a-ksweep.jsonl", "ksweep", ksweep)
    assert spike_cli.run_block("grid", "2026-10-08-a-grid", "2026-10-08-a-ksweep",
                               results_dir=tmp_path) == 0
    lines = (tmp_path / "2026-10-08-a-grid.jsonl").read_text().splitlines()
    assert len(lines) == 2
    header = parse_header(lines[0])
    assert header["run_id"] == "2026-10-08-a-grid"
    assert header["block"] == "grid"
    assert header["decisive"] is True
    assert header["k"] == 3
    assert "select_k" in header["k_source"]
    assert "2026-10-08-a-ksweep" in header["k_source"]
    assert [load for _, load in header["readings"]] == [1.2, 1.1]
    assert (header["head"], header["protocol_blob"], header["protocol_commit"]) == (
        "a" * 40, "b" * 40, "c" * 40)
    row = json.loads(lines[1])
    assert row["class"] == "ok"
    assert row["k"] == 3  # the locked K reached the block, not a typed one
    assert parse_result_row(lines[1])["kind"] == "rod"
    text = capsys.readouterr().out
    assert text == (tmp_path / "2026-10-08-a-grid.md").read_text()
    assert "release: decisive at 2026-10-08T09:00:30+00:00" in text
    assert "load1 1.20 read 2026-10-08T09:00:00+00:00" in text
    assert "includes this run's own load" in text
    before = (tmp_path / "2026-10-08-a-grid.jsonl").read_text()
    assert spike_cli.run_block("grid", "2026-10-08-a-grid", "2026-10-08-a-ksweep",
                               results_dir=tmp_path) == 2
    assert (tmp_path / "2026-10-08-a-grid.jsonl").read_text() == before


def test_a_non_decisive_run_says_so_in_its_header_and_its_release_line(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _held(monkeypatch, decisive=False)
    monkeypatch.setitem(spike_cli.BLOCKS, "ksweep", _one_row_block)
    assert spike_cli.run_block("ksweep", "loose", None, results_dir=tmp_path) == 0
    header = parse_header((tmp_path / "loose.jsonl").read_text().splitlines()[0])
    assert header["decisive"] is False
    assert header["k"] is None
    assert "non-decisive after 900 s (2 readings)" in capsys.readouterr().out


def test_k_is_5_and_says_why_when_no_k_qualified_under_the_rule(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _held(monkeypatch)
    monkeypatch.setitem(spike_cli.BLOCKS, "frontier", _one_row_block)
    _write_run(tmp_path / "sweep.jsonl", "ksweep",
               [r for k in (3, 5, 10) for r in _ksweep(k, cls="silent_wrong")])
    assert spike_cli.run_block("frontier", "front", "sweep", results_dir=tmp_path) == 0
    header = parse_header((tmp_path / "front.jsonl").read_text().splitlines()[0])
    assert header["k"] == 5
    assert header["k_source"] == spike_cli.NO_K_SOURCE


@pytest.mark.parametrize("which", ["missing", "wrong block"])
def test_a_k_from_run_that_is_missing_or_not_a_ksweep_is_refused(
        which: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _held(monkeypatch)
    if which == "wrong block":
        _write_run(tmp_path / "sweep.jsonl", "grid", [_synth()])
    assert spike_cli.run_block("grid", "a-grid", "sweep", results_dir=tmp_path) == 2
    assert "refused" in capsys.readouterr().err
    assert not (tmp_path / "a-grid.jsonl").exists()


def test_a_block_with_no_rows_raises_instead_of_printing_an_empty_table() -> None:
    with pytest.raises(ValueError, match="no rows"):
        spike_cli.aggregate_table([])
    with pytest.raises(ValueError, match="no rows"):
        spike_cli.report([], [], [], Reading("2026-10-08T09:00:00+00:00", 1.0))


def _measured(record: RowRecord) -> spike_cli.Measured:
    closed = maths.closed_volume(record["d"], record["pitch"], record["length"],
                                 record["clearance"])
    cls, reasons = classify_row(record, closed)
    return spike_cli.Measured(record, cls, reasons, over_budget(record, True), closed)


def test_the_aggregate_prints_signed_errors_counts_classes_and_counts_skipped_checks() -> None:
    rows = [_measured(_synth(turns=10.0, err=2e-6)), _measured(_synth(turns=20.0, err=-3e-5)),
            _measured(_synth(turns=30.0, cls="silent_wrong", err=-0.5)),
            _measured(_synth(turns=40.0, cls="timeout")),
            _measured(_synth("M2", turns=10.0))]
    lines = spike_cli.aggregate_table(rows)
    cells = {line.split("|")[1].strip(): [c.strip() for c in line.split("|")[2:-1]]
             for line in lines[2:]}
    assert set(cells) == {"M2", "M6"}
    m6 = cells["M6"]
    assert m6[:6] == ["4", "2", "1", "0", "1", "0"]  # rows, ok, wrong, failure, timeout, died
    assert m6[6] == "-5.000e-01"  # the signed extreme of greatest magnitude, sign kept
    assert m6[8] == "1000"  # the largest fine triangle count
    assert m6[10] == "1500"  # the largest raw + gzip-1 bytes
    assert m6[-1] == "6"  # three built rod rows, each with a preview and a fine mesh unchecked
    assert cells["M2"][-1] == "2"


def test_the_report_lists_every_non_ok_and_over_budget_row_with_its_reasons() -> None:
    rows = [_measured(_synth(turns=10.0)), _measured(_synth(turns=20.0, cls="timeout")),
            _measured(_synth(turns=30.0, fine=(1, _BUDGET_BYTES, 1.0, 1)))]
    text = spike_cli.report(["header line"], rows, ["M6 right: no stop up to 250 turns"],
                            Reading("2026-10-08T09:30:00+00:00", 3.5))
    assert text.startswith("header line\n")
    assert "- M6 right L=20 rod: timeout: it broke" in text
    assert "- M6 right L=20 rod: over budget: timeout" in text
    assert f"- M6 right L=30 rod: over budget: fine raw + gzip-1 {_BUDGET_BYTES + 1} bytes" in text
    assert "- frontier M6 right: no stop up to 250 turns" in text
    assert text.endswith("- load1 3.50 read 2026-10-08T09:30:00+00:00 (includes this run's "
                         "own load)")


def test_the_grid_block_is_the_d03_grid_from_maths_for_both_hands_with_a_rod_and_a_void() -> None:
    c, fake = _campaign()
    spike_cli.BLOCKS["grid"](c, 5, False)
    assert len(fake.requests) == 2 * 2 * 1790
    expected = [(kind, size, left, float(length), float(length / maths.PITCH[size][1]))
                for size in maths.SIZES
                for length in _grid(size) for left in (False, True) for kind in ("rod", "void")]
    assert [(r["kind"], r["size"], r["left_hand"], r["length"], r["turns"])
            for r in fake.requests] == expected
    rod, void = fake.requests[0], fake.requests[1]
    assert (rod["k"], rod["clearance"], rod["step"], rod["gzip_on"]) == (5, 0.0, True, ["fine"])
    assert [name for name, _, _ in rod["presets"]] == ["preview", "fine"]
    assert (void["k"], void["clearance"], void["step"], void["presets"]) == (
        5, maths.VOID_CLEARANCE, False, [])
    assert rod["check_ceiling"] == FINE_CHECK_CEILING


def test_the_grid_block_builds_an_integer_turn_row_with_its_exact_integer_turns() -> None:
    c, fake = _campaign()
    spike_cli.BLOCKS["grid"](c, 5, False)
    m2 = [r for r in fake.requests if r["size"] == "M2" and r["kind"] == "rod"
          and not r["left_hand"]]
    by_length = {r["length"]: r["turns"] for r in m2}
    assert by_length[1.2] == 3.0  # 1.2 mm = 3 turns of 0.4 mm: not 3.0000000000000004


def test_the_ksweep_block_runs_the_sample_sizes_at_every_k_and_both_hands() -> None:
    c, fake = _campaign()
    spike_cli.BLOCKS["ksweep"](c, 99, False)  # the sweep ignores the K it is handed
    assert len(fake.requests) == 8 * 3 * 2 * 4
    assert {r["size"] for r in fake.requests} == set(maths.SAMPLE_SIZES)
    assert {r["k"] for r in fake.requests} == {3, 5, 10}
    first = fake.requests[:4]
    assert [(r["kind"], r["turns"]) for r in first] == [("rod", 50.0), ("void", 50.0),
                                                        ("rod", 250.0), ("void", 250.0)]
    assert [name for name, _, _ in first[0]["presets"]] == ["preview", "fine"]
    assert [name for name, _, _ in first[2]["presets"]] == ["preview"]  # the far rod: preview only
    assert (first[2]["step"], first[2]["gzip_on"]) == (False, [])


def test_the_frontier_block_walks_each_size_and_hand_to_250_turns_when_nothing_stops_it() -> None:
    c, fake = _campaign()
    spike_cli.BLOCKS["frontier"](c, 5, False)
    steps = sum(len(maths.frontier_turns(*maths.PITCH[size])) for size in maths.SIZES)
    assert len(fake.requests) == 2 * 2 * steps
    assert len(c.stops) == 30
    assert all("no stop up to 250 turns; last measured 250 turns" in stop for stop in c.stops)
    assert c.stops[0] == "M2 right: no stop up to 250 turns; last measured 250 turns"
    m2_right = [r["turns"] for r in fake.requests if r["size"] == "M2" and r["kind"] == "rod"
                and not r["left_hand"]]
    assert m2_right[0] == 55.0
    assert m2_right[-1] == 250.0


def test_the_frontier_block_stops_a_walk_at_the_first_failing_step_and_says_why() -> None:
    c, fake = _campaign(fail=("M6", False, 100.0))
    spike_cli.BLOCKS["frontier"](c, 5, False)
    assert "M6 right: stop: rod failure at 100 turns; last measured 100 turns" in c.stops
    assert "M6 left: no stop up to 250 turns; last measured 250 turns" in c.stops
    m6_right = [r["turns"] for r in fake.requests if r["size"] == "M6" and r["kind"] == "rod"
                and not r["left_hand"]]
    assert m6_right[-1] == 100.0  # nothing was built beyond the stop


def test_the_ladder_block_meshes_every_preset_of_the_right_hand_rod_with_gzip_on_each() -> None:
    c, fake = _campaign()
    spike_cli.BLOCKS["ladder"](c, 5, False)
    assert len(fake.requests) == 8 * 2
    assert {r["left_hand"] for r in fake.requests} == {False}
    assert {r["kind"] for r in fake.requests} == {"rod"}
    first, second = fake.requests[:2]
    assert (first["turns"], second["length"]) == (10.0, 20.0)
    names = [name for name, _, _ in first["presets"]]
    assert names == ["preview", "fine", "h/4", "h/8", "h/16", "h/32"]
    assert first["gzip_on"] == names
    assert first["step"] is False


@pytest.mark.parametrize(("block", "rows"), [("ksweep", 6), ("grid", 4), ("frontier", 2),
                                             ("ladder", 4)])
def test_a_smoke_scope_is_a_handful_of_rows_on_m2_and_m6_of_at_most_20_turns(
        block: str, rows: int) -> None:
    c, fake = _campaign()
    spike_cli.BLOCKS[block](c, 5, True)
    assert len(fake.requests) == rows <= 6
    assert {r["size"] for r in fake.requests} <= {"M2", "M6"}
    assert {r["left_hand"] for r in fake.requests} == {False}
    if block != "frontier":
        assert max(r["turns"] for r in fake.requests) <= 20.0


def test_smoke_block_runs_the_real_frontier_code_on_a_subset_and_says_it_is_not_a_run(
        capsys: pytest.CaptureFixture[str]) -> None:
    assert spike_cli.smoke_block("frontier") == 0
    out = capsys.readouterr().out
    assert "not a campaign run" in out
    assert "frontier M2 right: no stop up to 55 turns; last measured 55 turns" in out
    assert "| M2 | right | 55 | 5 | rod | ok |" in out
