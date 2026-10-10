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

import ast
import importlib
import itertools
import json
import math
import os
import re
import struct
import subprocess
import sys
from collections.abc import Iterable, Sequence
from fractions import Fraction
from pathlib import Path
from typing import Literal

import cadquery as cq
import httpx2 as httpx
import pytest
from pydantic import ValidationError

from bench import quiet as quiet_module
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
from bench.thread_spike import helical, maths, measure, pair, worker
from bench.thread_spike import verdict as verdict_module
from bench.thread_spike.__main__ import _table_row
from bench.thread_spike.runner import (
    CONTAINER_IMAGE,
    Worker,
    container_argv,
    docker_kill,
    run_once,
)
from bench.thread_spike.verdict import (
    BUDGET_BYTES,
    BUDGET_S,
    EMPTY_MM3,
    ESTIMATOR_TIE,
    FINE_CHECK_CEILING,
    GATE_FACTOR,
    PAIR_BAND,
    PROTOCOL_PATH,
    ROW_TIMEOUT_S,
    T_PASS,
    GuardResult,
    HeaderRecord,
    MeshRecord,
    PairReading,
    PairRecord,
    PairRequest,
    RowRecord,
    RowRequest,
    before_results,
    cell_verdict,
    classify_record,
    classify_row,
    closed_control,
    escape_rows,
    excluded_clearances,
    failed_pair_record,
    failed_record,
    frontier_stop,
    gate_tolerance,
    k_scores,
    known_bad_inputs,
    mixed_hand_violated,
    over_budget,
    parse_header,
    parse_pair_record,
    parse_pair_request,
    parse_pair_result_row,
    parse_record,
    parse_request,
    parse_result_row,
    pass_bar,
    protocol_guard,
    relative_error,
    request_seconds,
    select_estimator,
    select_k,
    sensitivity_ok,
    size_falsifiable,
    skipped_checks,
    turn_caps,
    variant_rules,
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
    "step": False, "gzip_on": [], "check_ceiling": FINE_CHECK_CEILING, "want_gzip_table": False,
}


def _built(precise: float, *, solids: int = 1, valid: bool = True,
           meshes: list[MeshRecord] | None = None) -> RowRecord:
    return {
        **_REQUEST, "outcome": "built", "error": None, "solids": solids, "is_valid": valid,
        "precise_volume": precise, "default_volume": precise, "build_s": 0.1, "volume_s": 0.1,
        "meshes": [] if meshes is None else meshes, "step_bytes": None, "step_s": None,
        "trim_s": None, "peak_rss_bytes": None, "gzip_table": None, "gzip_selected": None,
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
        "check_ceiling": FINE_CHECK_CEILING, "want_gzip_table": False,
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
        "trim_s": None, "peak_rss_bytes": None, "gzip_table": None, "gzip_selected": None,
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
            err: float = 0.0, far: _RowCls = "ok", left: bool = False) -> list[RowRecord]:
    """One K's sweep rows for M6 and one hand: the standard max (60 turns) rod and void, and the
    250-turn rod (preview only) and void."""
    return [
        _synth(k=k, left=left, cls=cls, err=err, fine=(triangles, 1000, 1.0, 500),
               step=(step_bytes, 1.0)),
        _synth(kind="void", k=k, left=left),
        _synth(k=k, left=left, turns=250.0, cls=far, fine=None, step=None),
        _synth(kind="void", k=k, left=left, turns=250.0),
    ]


def _m6_ksweep(*, cls: _RowCls = "ok") -> list[RowRecord]:
    """The whole M6 sweep: every K, both hands. K has 1000 + K fine triangles, so the rule
    selects K = 3 unless `cls` spoils every row."""
    return [row for k in (3, 5, 10) for left in (False, True)
            for row in _ksweep(k, left=left, triangles=1000 + k, cls=cls)]


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


def _winner(precise: float, stl: float, *, precise_s: float = 0.1, stl_s: float = 0.1,
            decisive: bool = True) -> str:
    return select_estimator(_estimator_rows(precise, stl, precise_s=precise_s, stl_s=stl_s),
                            decisive)[0]


def test_the_estimator_with_the_smaller_max_error_wins_when_they_are_not_within_2x() -> None:
    name, err, gate = select_estimator(_estimator_rows(1e-6, 1e-3), True)
    assert name == "precise"
    assert err == pytest.approx(1e-6)
    assert gate == gate_tolerance(err) == pytest.approx(1e-5)
    assert _winner(8e-5, 1e-5, precise_s=0.01, stl_s=9.0) == "stl"  # accuracy beats cost


def test_estimators_within_2x_tie_and_the_cheaper_by_median_seconds_wins() -> None:
    assert _winner(1.99e-5, 1e-5, precise_s=2.0, stl_s=0.5) == "stl"
    assert _winner(1.99e-5, 1e-5, precise_s=0.5, stl_s=2.0) == "precise"
    # past 2x it is no tie: the smaller error wins however much it costs
    assert _winner(2.01e-5, 1e-5, precise_s=0.5, stl_s=2.0) == "stl"
    assert _winner(1e-5, 2.01e-5, precise_s=2.0, stl_s=0.5) == "precise"


def test_a_tied_estimator_pair_with_equal_cost_goes_to_the_smaller_error() -> None:
    assert _winner(1.5e-5, 1e-5) == "stl"
    assert _winner(1e-5, 1.5e-5) == "precise"


def test_a_tie_on_a_non_decisive_gate_is_not_established_whatever_the_seconds_say() -> None:
    """The tie-break is a timing claim, and a loaded host's timings prove nothing (R4): changing
    only the non-decisive seconds can neither pick an estimator nor change the outcome."""
    for precise_s, stl_s in ((2.0, 0.5), (0.5, 2.0), (0.1, 0.1)):
        with pytest.raises(ValueError, match="tie"):
            _winner(1.5e-5, 1e-5, precise_s=precise_s, stl_s=stl_s, decisive=False)
    assert _winner(1.5e-5, 1e-5, precise_s=0.5, stl_s=2.0, decisive=True) == "precise"


def test_without_a_tie_the_gate_does_not_matter_because_no_seconds_are_read() -> None:
    assert _winner(1e-6, 1e-3, precise_s=9.0, stl_s=0.01, decisive=False) == "precise"
    assert _winner(1e-5, 2.01e-5, precise_s=9.0, stl_s=0.01, decisive=False) == "precise"


def test_the_estimator_reads_only_ok_rod_rows_and_refuses_an_empty_set() -> None:
    rows = [*_estimator_rows(1e-6, 1e-3), _synth(cls="silent_wrong", err=0.5, stl_err=1e-9)]
    assert select_estimator(rows, True)[0] == "precise"  # the wrong row's tiny stl is not read
    with pytest.raises(ValueError, match="no"):
        select_estimator([_synth(kind="void"), _synth(cls="failure")], True)


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
          end: int = 250, k: int = 5) -> list[RowRecord]:
    """Frontier rows of `size` and one hand: rod and void at every step from the first
    frontier turn to `end`, the walk ending at `stop_at` with the rod in class `rod_cls`."""
    d, pitch = maths.PITCH[size]
    rows: list[RowRecord] = []
    for turns in maths.frontier_turns(d, pitch):
        if turns > end:
            break
        stopped = turns == stop_at
        rows.append(_synth(size, left=left, turns=float(turns), k=k,
                           cls=rod_cls if stopped else "ok"))
        rows.append(_synth(size, "void", left=left, turns=float(turns), k=k))
        if stopped:
            break
    return rows


def _full_walk(size: str = "M6", stop_at: int | None = None, *, k: int = 5,
               **kwargs: object) -> list[RowRecord]:
    return (_walk(size, False, stop_at, k=k, **kwargs)  # type: ignore[arg-type]
            + _walk(size, True, None, k=k))


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


def test_a_timed_out_void_caps_the_size_like_a_timed_out_rod_on_a_decisive_gate() -> None:
    """The pass bar holds over a decisive void timeout because it is a cap; the cap must exist."""
    grid = [_synth(turns=10.0), _synth(kind="void", turns=10.0), _synth(turns=20.0),
            _synth(kind="void", turns=20.0, cls="timeout"), _synth(turns=30.0)]
    assert pass_bar(grid, True) == ("held", ())
    cap = turn_caps(grid, [], True)["M6"]
    assert (cap.seconds_cap_length, cap.seconds_established) == (10.0, True)
    loose = turn_caps(grid, [], False)["M6"]
    assert (loose.seconds_cap_length, loose.seconds_established) == (None, False)


def test_a_void_never_makes_a_bytes_cap_because_it_has_no_fine_mesh() -> None:
    grid = [_synth(turns=10.0), _synth(kind="void", turns=10.0), _heavy(30.0),
            _synth(kind="void", turns=30.0)]
    cap = turn_caps(grid, [], True)["M6"]
    assert (cap.bytes_cap_length, cap.seconds_cap_length) == (10.0, None)


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
        "trim_s": 0.01 if request["kind"] == "trim" else None,
        "peak_rss_bytes": None, "gzip_table": None, "gzip_selected": None,
    }


class _FakeWorker(Worker):
    """Answers every request in-process without a kernel; a rod of `fail_size`, `fail_left` at
    `fail_turns` turns fails. Records every request it was given."""

    def __init__(self, fail: tuple[str, bool, float] | None = None, **_: object) -> None:
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


def _write_run(path: Path, block: str, rows: list[RowRecord], *, decisive: bool = True,
               k: int | None = None) -> None:
    """A recorded run as a campaign writes it: the header (which names the run's K, none for the
    K sweep), then one row per line carrying the run's own verdict keys, `class` always `ok`:
    `verdict` must not believe it."""
    header: HeaderRecord = {**_HEADER, "block": block, "k": k, "run_id": path.stem,
                            "decisive": decisive}
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


def _m6_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """The run inputs (a K sweep, a frontier walk) are held to the pre-registered row set of the
    sizes the harness covers; `_m6_ksweep` and `_full_walk` are complete for M6 alone."""
    for name in ("SIZES", "SAMPLE_SIZES"):
        monkeypatch.setattr(spike_cli, name, ("M6",))


def _one_row_block(c: spike_cli.Campaign, k: int, smoke: bool) -> None:
    assert not smoke
    c.measure({**_REQUEST, "k": k, "turns": 3.0, "length": 3.0})


def test_a_run_writes_its_header_first_then_one_row_per_line_and_never_overwrites_itself(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _held(monkeypatch)
    monkeypatch.setitem(spike_cli._BLOCKS, "grid", _one_row_block)
    _m6_only(monkeypatch)
    ksweep = _m6_ksweep()
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
    monkeypatch.setitem(spike_cli._BLOCKS, "ksweep", _one_row_block)
    assert spike_cli.run_block("ksweep", "loose", None, results_dir=tmp_path) == 0
    header = parse_header((tmp_path / "loose.jsonl").read_text().splitlines()[0])
    assert header["decisive"] is False
    assert header["k"] is None
    assert "non-decisive after 900 s (2 readings)" in capsys.readouterr().out


def test_k_is_5_and_says_why_when_no_k_qualified_under_the_rule(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _held(monkeypatch)
    monkeypatch.setitem(spike_cli._BLOCKS, "frontier", _one_row_block)
    _m6_only(monkeypatch)
    _write_run(tmp_path / "sweep.jsonl", "ksweep", _m6_ksweep(cls="silent_wrong"))
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
    spike_cli._BLOCKS["grid"](c, 5, False)
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
    spike_cli._BLOCKS["grid"](c, 5, False)
    m2 = [r for r in fake.requests if r["size"] == "M2" and r["kind"] == "rod"
          and not r["left_hand"]]
    by_length = {r["length"]: r["turns"] for r in m2}
    assert by_length[1.2] == 3.0  # 1.2 mm = 3 turns of 0.4 mm: not 3.0000000000000004


def test_the_ksweep_block_runs_the_sample_sizes_at_every_k_and_both_hands() -> None:
    c, fake = _campaign()
    spike_cli._BLOCKS["ksweep"](c, 99, False)  # the sweep ignores the K it is handed
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
    spike_cli._BLOCKS["frontier"](c, 5, False)
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
    spike_cli._BLOCKS["frontier"](c, 5, False)
    assert "M6 right: stop: rod failure at 100 turns; last measured 100 turns" in c.stops
    assert "M6 left: no stop up to 250 turns; last measured 250 turns" in c.stops
    m6_right = [r["turns"] for r in fake.requests if r["size"] == "M6" and r["kind"] == "rod"
                and not r["left_hand"]]
    assert m6_right[-1] == 100.0  # nothing was built beyond the stop


def test_the_ladder_block_meshes_every_preset_of_the_right_hand_rod_with_gzip_on_each() -> None:
    c, fake = _campaign()
    spike_cli._BLOCKS["ladder"](c, 5, False)
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
    spike_cli._BLOCKS[block](c, 5, True)
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


# --- The verdict subcommand over recorded runs ---

def test_k_scores_lists_every_k_with_its_counts_and_scores_only_the_ones_that_qualify() -> None:
    rows = _ksweep(3, triangles=900, step_bytes=30) + _ksweep(5, cls="silent_wrong") + [
        _synth(k=10, cls="timeout", turns=250.0, fine=None, step=None)]
    scores = k_scores(rows)
    assert [score.k for score in scores] == [3, 5, 10]
    three, five, ten = scores
    assert (three.k, three.rows, three.non_ok, three.triangles, three.step_bytes) == (
        3, 4, 0, 900, 30)
    assert (five.k, five.rows, five.non_ok, five.triangles, five.step_bytes) == (
        5, 4, 1, None, None)
    assert (ten.k, ten.rows, ten.non_ok, ten.triangles, ten.step_bytes) == (10, 1, 1, None, None)


def test_k_scores_leaves_out_a_k_with_no_rows() -> None:
    assert [score.k for score in k_scores(_ksweep(3) + _ksweep(10))] == [3, 10]


def test_the_escape_rows_are_the_failures_inside_the_standard_range_of_either_hand() -> None:
    rows = [
        _synth(cls="silent_wrong"), _synth(left=True, cls="failure"),
        _synth(kind="void", cls="worker_died"), _synth(cls="timeout"),  # a cap, not an escape
        _synth(turns=65.0, cls="silent_wrong"),  # frontier: beyond the standard max of 60
        _synth(turns=10.0),
    ]
    reasons = escape_rows(rows)
    assert len(reasons) == 3
    assert any("right" in r and "silent_wrong" in r for r in reasons)
    assert any("left" in r and "failure" in r for r in reasons)
    assert any("void" in r and "worker_died" in r for r in reasons)


_LOCKED_K = 3  # `_m6_ksweep` makes K = 3 the K with the fewest fine triangles


def _m6_ladder(k: int) -> list[RowRecord]:
    """The M6 ladder at `k`: the rod at 10 turns and at the standard max (60 mm), each with the
    ladder's own request (every INTERIM and depth preset, gzip on each, no STEP)."""
    return [_ok_record(verdict_module.ladder_request("M6", Fraction(length), k))
            for length in (10, 60)]


def _m6_lengths(extra: list[RowRecord], *, container: bool, err: float,
                stl_err: float | None, k: int = _LOCKED_K) -> list[RowRecord]:
    """The M6 grid at the locked K: P = 1 mm, so the D-03 lengths are every integer 1 to 60, a
    rod and a void at each, both hands. A row of `extra` takes the place of the row it names
    (kind, hand, length) and is recorded at the locked K."""
    rows: dict[tuple[str, bool, float], RowRecord] = {}
    for left in (False, True):
        for turns in (float(x) for x in range(1, 61)):
            rod = (_synth(left=left, turns=turns, k=k, preview=False, fine=None, step=None)
                   if container else
                   _synth(left=left, turns=turns, k=k, err=err, stl_err=stl_err))
            rows[("rod", left, turns)] = rod
            rows[("void", left, turns)] = _synth(kind="void", left=left, turns=turns, k=k)
    for row in extra:
        rows[(row["kind"], row["left_hand"], row["turns"])] = {**row, "k": k}
    return list(rows.values())


def _full_campaign(tmp_path: Path, *, prefix: str = "c1", grid_extra: list[RowRecord] | None = None,
                   grid_decisive: bool = True, skip: tuple[str, ...] = (),
                   container_extra: list[RowRecord] | None = None,
                   pair_cells: list[PairRecord] | None = None, err: float = 1.5e-6,
                   stl_err: float | None = 1e-3, k: int = _LOCKED_K) -> None:
    """A clean campaign for M6 alone, complete against the pre-registered row sets of the sizes
    it covers (read it with `_verdict`): the K sweep, the grid, the frontier walk, the ladder, the
    pair cells and the container grid, written the way a run writes them. `err` and `stl_err` are
    the grid rod rows' precise and preview-mesh errors, which the estimator rule reads (no
    `stl_err`: no checked preview). `grid_extra` and `container_extra` rows replace the row at the
    same kind, hand and length; `pair_cells` replace the cell of the same pair, hands, c and K.
    Every block after the sweep is recorded at `k`, which the sweep selects unless it is spoiled
    (then the harness records at its default, 5)."""
    blocks: dict[str, list[RowRecord]] = {
        "ksweep": _m6_ksweep(),
        "grid": _m6_lengths(grid_extra or [], container=False, err=err, stl_err=stl_err, k=k),
        "frontier": _full_walk("M6", None, k=k),
        "ladder": _m6_ladder(k),
        "container": _m6_lengths(container_extra or [], container=True, err=err, stl_err=None,
                                 k=k),
    }
    for block, rows in blocks.items():
        if block not in skip:
            # Emulated timings: a container run is written non-decisive, as a run writes it.
            _write_run(tmp_path / f"{prefix}-{block}.jsonl", block, rows,
                       decisive=grid_decisive if block == "grid" else block != "container",
                       k=None if block == "ksweep" else k)
    if "pair" not in skip:
        cells = {_pair_identity(c): c for c in _clean_pair_cells(k)}
        cells.update({_pair_identity(c): c for c in pair_cells or []})
        _write_pair_run(tmp_path / f"{prefix}-pair.jsonl", list(cells.values()), k=k)


def _verdict(prefix: str, results_dir: Path) -> int:
    """`verdict_campaign` over a campaign recorded for M6 alone: the pre-registered row sets are
    the Method table's for the sizes covered, so it is told M6 is the only size. The full sets are
    pinned by `test_the_pre_registered_row_sets_are_what_the_blocks_request`."""
    with pytest.MonkeyPatch.context() as patch:
        for name in ("SIZES", "SAMPLE_SIZES", "PAIR_REFERENCE_SIZES"):
            patch.setattr(spike_cli, name, ("M6",))
        return spike_cli.verdict_campaign(prefix, results_dir=results_dir)


def _pair_identity(cell: PairRecord) -> tuple[str, bool, bool, float, int]:
    return (cell["size"], cell["rod_left_hand"], cell["nut_left_hand"], cell["clearance"],
            cell["k"])


def _clean_pair_cells(k: int = _LOCKED_K) -> list[PairRecord]:
    """Every cell the Method pre-registers for M6 at the locked K `k`: both same-hand pairs at
    the two diagnostic and four proof clearances, the mixed pair violated at the four proof
    ones, and the two other K values right hand at the proof clearances as reference rows. M6 is
    proven on both hands at c = 0.10."""
    cells = [_pair(c, rod_left=left, nut_left=left, k=k)
             for left in (False, True) for c in (*maths.DIAGNOSTIC_CLEARANCES,
                                                 *maths.PAIR_CLEARANCES)]
    cells += [_mixed(c, (6.5, 6.9, 6.7), k=k) for c in maths.PAIR_CLEARANCES]
    cells += [_pair(c, k=other) for other in maths.K_CANDIDATES if other != k
              for c in maths.PAIR_CLEARANCES]
    return cells


def _write_pair_run(path: Path, cells: list[PairRecord], *, k: int | None = _LOCKED_K) -> None:
    """A pair run as the block writes it, every cell stored with a verdict of `proven`: the
    verdict must not believe it."""
    header: HeaderRecord = {**_HEADER, "block": "pair", "k": k, "run_id": path.stem}
    lines = [json.dumps(header)]
    lines += [json.dumps({**cell, "verdict": "proven", "reasons": [], "closed_control": 1.0})
              for cell in cells]
    path.write_text("\n".join(lines) + "\n")


def test_a_clean_campaign_passes_with_the_k_the_estimator_and_the_turn_caps_printed(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path)
    assert _verdict("c1", tmp_path) == 0
    out = capsys.readouterr().out
    assert "selected K: 3" in out
    assert "estimator: precise" in out
    assert "T_gate" in out
    assert "pass bar: held" in out
    assert "escape clause: not fired" in out
    assert "M6" in out.split("### Turn caps")[1]
    assert "no stop up to 250 turns" in out
    assert "Blocks read: ksweep" in out
    assert "missing" not in out.split("### K")[0]


def test_a_silent_wrong_grid_row_fails_the_verdict_and_fires_the_escape_clause_naming_it(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The row is stored with class `ok`: the verdict recomputes every class from the raw
    record, so a hand-edited class cannot pass a wrong row (T-02-09)."""
    _full_campaign(tmp_path, grid_extra=[_synth(turns=30.0, cls="silent_wrong", left=True)])
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "pass bar: failed" in out
    assert "escape clause: FIRED" in out
    assert out.count("- M6 left L=30 rod: silent_wrong") == 2  # under the bar and the clause


def test_a_campaign_without_all_four_blocks_lists_the_missing_ones_and_never_passes(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path, skip=("frontier", "ladder"))
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "Blocks missing: frontier, ladder" in out
    assert "no frontier record" in out


def test_a_sweep_in_which_no_k_qualified_fires_the_escape_clause_and_never_passes(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Every other block is clean: the grid at K = 5 would read held, and without this rule
    the campaign would exit 0 with "no K was selected" printed above a pass."""
    _full_campaign(tmp_path, k=5)  # every later block ran at the harness's default K
    _write_run(tmp_path / "c1-ksweep.jsonl", "ksweep", _m6_ksweep(cls="silent_wrong"))
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "pass bar: held" in out
    assert "escape clause: FIRED" in out
    assert "- K: no K qualified under the rule" in out


def test_skipped_checks_count_unchecked_meshes_of_rods_and_voids_and_nothing_else() -> None:
    half = _synth(stl_err=1e-3)  # checked preview, unchecked fine
    neither = _synth(turns=20.0)  # both unchecked
    rows = [half, neither, _synth(kind="void"), _naive(0.3)]
    assert skipped_checks(rows) == (3, 4)  # a void has no mesh, and the naive control is no input
    assert skipped_checks([]) == (0, 0)


def test_a_held_pass_bar_prints_how_many_mesh_checks_were_skipped_and_still_exits_0(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Skipped checks never change a row's class (the Rules), but a held bar must not read as a
    claim about meshes nobody checked: the count sits beside it, named unchecked."""
    _full_campaign(tmp_path, grid_extra=[_synth(turns=30.0, left=True)])  # preview unchecked too
    assert _verdict("c1", tmp_path) == 0
    bar = capsys.readouterr().out.split("### Pass bar")[1].split("### Escape clause")[0]
    assert "pass bar: held" in bar
    # 120 rods of two meshes each (the fine one never checked), one of them with neither checked
    assert "mesh checks skipped: 121 of 240 meshes unchecked" in bar


# --- A block is read only when its record is the pre-registered row set (plan 02-06 review) ---

_M6 = {"sizes": ("M6",), "sample_sizes": ("M6",)}


def _m6_header(block: str, *, k: int | None = _LOCKED_K, decisive: bool = True) -> HeaderRecord:
    return {**_HEADER, "block": block, "k": k, "decisive": decisive}


def _m6_grid() -> list[RowRecord]:
    return _m6_lengths([], container=False, err=0.0, stl_err=None)


@pytest.mark.parametrize("block", ["ksweep", "grid", "ladder", "container"])
def test_the_pre_registered_row_sets_are_what_the_blocks_request(block: str) -> None:
    """The completeness check holds a record against `expected_rows`; this holds `expected_rows`
    against the whole requests each block really makes (presets, STEP and gzip included), over
    all 15 sizes, so the two cannot drift."""
    fake = _FakeWorker()
    c = spike_cli.Campaign(fake, False, None, container=fake if block == "container" else None)
    spike_cli._BLOCKS[block](c, 5, False)
    wanted = verdict_module.expected_rows(block, 5, sizes=maths.SIZES,
                                          sample_sizes=maths.SAMPLE_SIZES)
    assert sorted(fake.requests, key=repr) == sorted(wanted, key=repr)


def test_the_pre_registered_row_sets_have_the_counts_the_method_table_states() -> None:
    counts = {block: len(verdict_module.expected_rows(block, 5, sizes=maths.SIZES,
                                                      sample_sizes=maths.SAMPLE_SIZES))
              for block in ("ksweep", "grid", "ladder", "container")}
    assert counts == {"ksweep": 192, "grid": 7160, "ladder": 16, "container": 7160}
    cells = verdict_module.expected_cells(5, sizes=maths.SIZES,
                                          reference_sizes=maths.PAIR_REFERENCE_SIZES)
    assert len(cells) == 272
    longest = sum(4 * len(maths.frontier_turns(*maths.PITCH[size])) for size in maths.SIZES)
    assert longest == 2236  # "at most": a walk that stops early is shorter


def test_the_pre_registered_pair_cells_are_what_the_pair_block_requests() -> None:
    requests = _run_pair_block(5)
    asked = sorted((r["size"], r["rod_left_hand"], r["nut_left_hand"], r["clearance"], r["k"])
                   for r in requests)
    wanted = verdict_module.expected_cells(5, sizes=maths.SIZES,
                                           reference_sizes=maths.PAIR_REFERENCE_SIZES)
    assert asked == sorted(wanted)


def test_a_frontier_walk_that_nothing_stops_is_complete_for_every_size_and_hand() -> None:
    fake = _FakeWorker()
    c = spike_cli.Campaign(fake, True, None)
    spike_cli._BLOCKS["frontier"](c, 5, False)
    rows = [m.record for m in c.rows]
    assert verdict_module.frontier_gaps(rows, 5, True, sizes=maths.SIZES) == []


@pytest.mark.parametrize("block", ["ksweep", "grid", "ladder", "container"])
def test_a_record_with_every_pre_registered_row_once_has_no_gaps(block: str) -> None:
    rows = {"ksweep": _m6_ksweep(), "grid": _m6_grid(),
            "ladder": _m6_ladder(_LOCKED_K),
            "container": _m6_lengths([], container=True, err=0.0, stl_err=None)}[block]
    header = _m6_header(block, k=None if block == "ksweep" else _LOCKED_K)
    assert verdict_module.block_gaps(block, header, rows, **_M6) == []


def test_a_grid_that_is_header_only_or_short_a_row_names_what_is_missing() -> None:
    header, rows = _m6_header("grid"), _m6_grid()
    (empty,) = verdict_module.block_gaps("grid", header, [], **_M6)
    assert "240 of 240 pre-registered rows missing" in empty
    short = [r for r in rows if not (r["kind"] == "void" and r["left_hand"]
                                     and r["length"] == 30.0)]
    (gap,) = verdict_module.block_gaps("grid", header, short, **_M6)
    assert gap == "1 of 240 pre-registered rows missing: M6 left L=30 void K=3"


def test_a_grid_row_recorded_twice_or_outside_the_set_is_reported() -> None:
    header, rows = _m6_header("grid"), _m6_grid()
    gaps = verdict_module.block_gaps("grid", header, [*rows, rows[0], _synth(turns=61.0, k=3)],
                                     **_M6)
    assert any("not in the pre-registered set: M6 right L=61 rod K=3" in g for g in gaps)
    assert any("recorded more than once: M6 right L=1 rod K=3" in g for g in gaps)


def test_a_grid_recorded_at_another_k_than_its_header_names_is_incomplete() -> None:
    other: list[RowRecord] = [{**r, "k": 5} for r in _m6_grid()]
    gaps = verdict_module.block_gaps("grid", _m6_header("grid"), other, **_M6)
    assert any("240 of 240 pre-registered rows missing" in g for g in gaps)
    assert any("240 rows not in the pre-registered set" in g for g in gaps)


def test_completeness_holds_a_record_to_the_exact_values_the_harness_wrote_not_their_print(
) -> None:
    """c = 0.10000001 prints as 0.1 to six digits and a length one float step past 30 mm prints
    as 30, yet neither is the pre-registered value: each is a stray, and the cell or row it
    resembles stays missing."""
    cells = [_pair(0.10000001, k=_LOCKED_K)
             if (c["clearance"], c["rod_left_hand"], c["nut_left_hand"], c["k"])
             == (0.10, False, False, _LOCKED_K) else c for c in _clean_pair_cells()]
    assert verdict_module.pair_gaps(_m6_header("pair"), cells, sizes=("M6",),
                                    reference_sizes=("M6",)) == [
        "1 of 24 pre-registered cells missing: M6 right c=0.1 K=3",
        "1 cells not in the pre-registered set: M6 right c=0.10000001 K=3"]
    near = math.nextafter(30.0, math.inf)
    rows: list[RowRecord] = [
        {**r, "length": near} if (r["kind"], r["left_hand"], r["length"]) == ("void", True, 30.0)
        else r for r in _m6_grid()]
    assert verdict_module.block_gaps("grid", _m6_header("grid"), rows, **_M6) == [
        "1 of 240 pre-registered rows missing: M6 left L=30 void K=3",
        "1 rows not in the pre-registered set: M6 left L=30.000000000000004 void K=3"]


@pytest.mark.parametrize(("clearance", "shown"), [(0.21, "0.21"), (0.20000001, "0.20000001")])
def test_a_grid_or_frontier_void_is_complete_only_at_the_pre_registered_clearance(
        clearance: float, shown: str) -> None:
    """A void at another clearance is another cutter, even one that prints as 0.2 to six digits:
    it is a stray row, reported, and the void it resembles stays missing."""
    rows: list[RowRecord] = [
        {**r, "clearance": clearance}
        if (r["kind"], r["left_hand"], r["length"]) == ("void", True, 30.0) else r
        for r in _m6_grid()]
    assert verdict_module.block_gaps("grid", _m6_header("grid"), rows, **_M6) == [
        "1 of 240 pre-registered rows missing: M6 left L=30 void K=3",
        f"1 rows not in the pre-registered set: M6 left L=30 void K=3 c={shown}"]
    walk: list[RowRecord] = [
        {**r, "clearance": clearance}
        if (r["turns"], r["kind"], r["left_hand"]) == (80.0, "void", False) else r
        for r in _full_walk("M6", None, k=_LOCKED_K)]
    assert _walk_gaps(walk) == [
        f"M6 right: step 80 has a void row that is not the pre-registered request: "
        f"clearance {shown}, not 0.2",
        "M6 right: step 80 has 0 void rows, not 1"]


def test_a_grid_rod_without_the_registered_request_is_stray_and_the_grid_is_never_read(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A grid row counts only with the request the Method registers for it. 119 of the 120 rods
    are recorded bare (no presets, no STEP, no gzip: the container's request), so they measured
    no mesh: each is a stray naming what differs, the full rod it resembles stays missing, the
    grid is not read, and no bytes or seconds claim is drawn from rows that meshed nothing."""
    _full_campaign(tmp_path)
    full = _m6_grid()
    bare = _m6_lengths([], container=True, err=0.0, stl_err=None)
    assert (full[0]["kind"], full[0]["left_hand"], full[0]["length"]) == ("rod", False, 1.0)
    (tmp_path / "c1-grid.jsonl").unlink()
    _write_run(tmp_path / "c1-grid.jsonl", "grid", [full[0], *bare[1:]], k=_LOCKED_K)
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "- Blocks not read: grid" in out
    assert "  - grid: 119 of 240 pre-registered rows missing: M6 left L=1 rod K=3;" in out
    assert ("  - grid: 119 rows not in the pre-registered set: M6 left L=1 rod K=3 (presets [], "
            "not [('preview', 0.08, 0.5), ('fine', 0.01, 0.1)]; step False, not True; gzip_on "
            "[], not ['fine'])") in out
    assert "no row over budget" not in out
    assert "pass bar: not established" in out


def _m2_labelled_m6() -> RowRecord:
    """An M2 rod (d = 2, P = 0.4) at 75 turns, 30 mm, labelled M6 at the locked K: against the
    closed form of the d and P it records it reads ok, at a length the M6 grid registers."""
    forged: RowRecord = {**_synth("M2", turns=75.0, left=True, k=_LOCKED_K), "size": "M6"}
    assert forged["length"] == 30.0
    assert verdict_module.row_class(forged) == "ok"
    return forged


def test_a_row_whose_d_or_pitch_is_not_its_sizes_is_a_stray_and_its_block_is_never_read(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The M6 left 30 mm rod of the grid is replaced by an M2 rod labelled M6. Its d and P are
    not M6's, so it is a stray naming both, the M6 rod it resembles stays missing, the grid is
    not read and the campaign never passes; nothing judges it as the M6 part it is labelled."""
    forged = _m2_labelled_m6()
    rows = [forged if (r["kind"], r["left_hand"], r["length"]) == ("rod", True, 30.0) else r
            for r in _m6_grid()]
    assert verdict_module.block_gaps("grid", _m6_header("grid"), rows, **_M6) == [
        "1 of 240 pre-registered rows missing: M6 left L=30 rod K=3",
        "1 rows not in the pre-registered set: M6 left L=30 rod K=3 (d 2.0, not 6.0; pitch "
        "0.4, not 1.0; turns 75.0, not 30.0)"]
    _full_campaign(tmp_path)
    (tmp_path / "c1-grid.jsonl").unlink()
    _write_run(tmp_path / "c1-grid.jsonl", "grid", rows, k=_LOCKED_K)
    assert _verdict("c1", tmp_path) == 1
    assert "- Blocks not read: grid" in capsys.readouterr().out


def test_an_evidence_row_or_a_pair_cell_whose_d_or_pitch_is_not_its_sizes_is_never_judged(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The evidence runs are held to no row set, yet a row whose d or P is not its size's would
    be printed as evidence about a part it is not: its run is not read. A pair cell likewise is
    a stray, and the cell it resembles stays missing."""
    _full_campaign(tmp_path)
    _write_run(tmp_path / "c1-rss.jsonl", "rss", [_m2_labelled_m6()], k=_LOCKED_K)
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "- Blocks not read: rss" in out
    assert ("  - rss: run `c1-rss` holds 1 rows whose d or P is not their size's, never judged: "
            "M6 left L=30 rod K=3 (d 2.0, not 6.0; pitch 0.4, not 1.0)") in out
    cells: list[PairRecord] = [
        {**c, "d": 2.0, "pitch": 0.4}
        if (c["clearance"], c["rod_left_hand"], c["nut_left_hand"], c["k"])
        == (0.10, False, False, _LOCKED_K) else c for c in _clean_pair_cells()]
    assert verdict_module.pair_gaps(_m6_header("pair"), cells, sizes=("M6",),
                                    reference_sizes=("M6",)) == [
        "1 of 24 pre-registered cells missing: M6 right c=0.1 K=3",
        "1 cells not in the pre-registered set, their d or P not their size's: M6 right c=0.1 "
        "K=3 (d 2.0, not 6.0; pitch 0.4, not 1.0)"]


def test_a_block_whose_header_names_no_k_cannot_be_held_against_its_rows() -> None:
    (gap,) = verdict_module.block_gaps("grid", _m6_header("grid", k=None), _m6_grid(), **_M6)
    assert "no K" in gap


def test_a_ksweep_missing_a_k_or_a_hand_is_incomplete() -> None:
    rows = [r for r in _m6_ksweep() if not (r["k"] == 10 and r["left_hand"])]
    (gap,) = verdict_module.block_gaps("ksweep", _m6_header("ksweep", k=None), rows, **_M6)
    assert gap.startswith("4 of 24 pre-registered rows missing")
    assert "M6 left L=60 rod K=10" in gap


def _walk_gaps(rows: list[RowRecord], *, decisive: bool = True) -> list[str]:
    return verdict_module.frontier_gaps(rows, _LOCKED_K, decisive, sizes=("M6",))


def test_a_complete_frontier_walk_ends_at_250_turns_or_at_a_stop() -> None:
    assert _walk_gaps(_full_walk("M6", None, k=_LOCKED_K)) == []
    stopped = _walk("M6", False, 100, k=_LOCKED_K) + _walk("M6", True, None, k=_LOCKED_K)
    assert _walk_gaps(stopped) == []


def test_a_frontier_with_no_walk_for_a_hand_is_incomplete() -> None:
    assert _walk_gaps(_walk("M6", False, None, k=_LOCKED_K)) == ["M6 left: no walk recorded"]
    assert _walk_gaps([]) == ["M6 right: no walk recorded", "M6 left: no walk recorded"]


def test_a_frontier_walk_that_ends_without_a_stop_before_250_turns_is_not_terminated() -> None:
    cut = _walk("M6", False, None, end=100, k=_LOCKED_K) + _walk("M6", True, None, k=_LOCKED_K)
    assert _walk_gaps(cut) == ["M6 right: the walk ends at 100 turns without a stop or "
                               "reaching 250"]


def test_a_frontier_step_missing_its_void_or_its_rod_is_incomplete() -> None:
    rows = _full_walk("M6", None, k=_LOCKED_K)
    no_void = [r for r in rows if not (r["kind"] == "void" and r["turns"] == 80.0
                                       and not r["left_hand"])]
    assert _walk_gaps(no_void) == ["M6 right: step 80 has 0 void rows, not 1"]
    twice = [*rows, rows[0]]
    assert _walk_gaps(twice) == ["M6 right: step 65 has 2 rod rows, not 1"]


def test_a_frontier_step_is_complete_only_at_its_own_length_and_with_no_other_kind() -> None:
    """A step is named by its turns and measured at turns x P: a rod labelled 250 turns that is
    1 mm long measured another part, and a row of another kind is no part of a walk."""
    rows = _full_walk("M6", None, k=_LOCKED_K)
    short: list[RowRecord] = [
        {**r, "length": 1.0} if (r["turns"], r["kind"], r["left_hand"]) == (250.0, "rod", False)
        else r for r in rows]
    assert _walk_gaps(short) == [
        "M6 right: step 250 has a rod row that is not the pre-registered request: length 1.0, "
        "not 250.0",
        "M6 right: step 250 has 0 rod rows, not 1",
        "M6 right: the walk ends at 245 turns without a stop or reaching 250"]
    stray: RowRecord = {**_synth(turns=65.0, k=_LOCKED_K), "kind": "trim"}
    assert _walk_gaps([*rows, stray]) == ["1 rows not in the pre-registered set: M6 right L=65 "
                                          "trim K=3"]


def test_a_frontier_row_of_a_size_no_walk_covers_is_a_stray_and_the_block_is_incomplete(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The frontier walks are per size and hand of the table, and nothing else: a row of a size
    outside it is reported as not in the pre-registered set, as a fixed block's stray row is,
    never dropped unreported, and the block is not read."""
    rows = _full_walk("M6", None, k=_LOCKED_K)
    stray: RowRecord = {**_synth(turns=65.0, k=_LOCKED_K), "size": "M99"}
    assert _walk_gaps([*rows, stray]) == ["1 rows not in the pre-registered set: M99 right L=65 "
                                          "rod K=3"]
    _full_campaign(tmp_path)
    (tmp_path / "c1-frontier.jsonl").unlink()
    _write_run(tmp_path / "c1-frontier.jsonl", "frontier", [*rows, stray], k=_LOCKED_K)
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "- Blocks not read: frontier" in out
    assert "  - frontier: 1 rows not in the pre-registered set: M99 right L=65 rod K=3" in out


def test_a_frontier_row_whose_length_is_not_its_turns_times_the_pitch_feeds_no_cap() -> None:
    near = math.nextafter(250.0, 0.0)  # one float below 250 turns x 1 mm
    rows: list[RowRecord] = [
        {**r, "length": near} if (r["turns"], r["kind"], r["left_hand"]) == (250.0, "void", True)
        else r for r in _full_walk("M6", None, k=_LOCKED_K)]
    cap = turn_caps([], rows, True)["M6"]
    assert cap.construction_turns is None
    assert "left: the void row of step 250 is at L=249.99999999999997 mm" in cap.stop_reason
    assert "no cap is drawn from it" in cap.stop_reason


def test_a_frontier_step_after_a_stop_is_reported_and_a_skipped_step_breaks_the_walk() -> None:
    stopped = _walk("M6", False, 100, k=_LOCKED_K)
    beyond = [r for r in _walk("M6", False, None, k=_LOCKED_K) if r["turns"] > 100.0]
    after = [*stopped, *beyond, *_walk("M6", True, None, k=_LOCKED_K)]
    assert "M6 right: a step follows the stop at 100 turns" in _walk_gaps(after)
    skipped = [r for r in _full_walk("M6", None, k=_LOCKED_K)
               if not (r["turns"] == 70.0 and not r["left_hand"])]
    assert any("not consecutive" in g for g in _walk_gaps(skipped))


def test_a_frontier_stop_that_only_a_decisive_clock_would_make_is_not_a_stop_otherwise() -> None:
    slow = _full_walk("M6", None, k=_LOCKED_K)
    slow[0] = _synth(turns=65.0, k=_LOCKED_K, build_s=40.0)  # over 30 s, right hand, 65 turns
    cut = [r for r in slow if not (r["turns"] > 65.0 and not r["left_hand"])]
    assert _walk_gaps(cut, decisive=True) == []  # the clock stopped the walk at 65
    assert any("without a stop" in g for g in _walk_gaps(cut, decisive=False))


def test_the_pair_cells_of_the_method_table_are_complete_and_a_missing_one_is_named() -> None:
    header = _m6_header("pair")
    cells = _clean_pair_cells()
    kwargs = {"sizes": ("M6",), "reference_sizes": ("M6",)}
    assert verdict_module.pair_gaps(header, cells, **kwargs) == []
    short = [c for c in cells if not (c["nut_left_hand"] and not c["rod_left_hand"]
                                      and c["clearance"] == 0.15)]
    (gap,) = verdict_module.pair_gaps(header, short, **kwargs)
    assert gap == "1 of 24 pre-registered cells missing: M6 right rod, left nut c=0.15 K=3"
    assert "no K" in verdict_module.pair_gaps(_m6_header("pair", k=None), cells, **kwargs)[0]


def test_a_pair_cell_that_did_not_finish_is_a_recorded_outcome_not_a_gap() -> None:
    cells = _clean_pair_cells()
    cells[0] = _pair(maths.DIAGNOSTIC_CLEARANCES[0], outcome="timeout", k=_LOCKED_K)
    assert verdict_module.pair_gaps(_m6_header("pair"), cells, sizes=("M6",),
                                    reference_sizes=("M6",)) == []


def test_a_header_only_grid_with_header_only_frontier_ladder_and_container_never_passes(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The review's scenario: every block present, none of them holding its rows. The bar over no
    rows must not read as held."""
    _full_campaign(tmp_path)
    for block in ("grid", "frontier", "ladder", "container"):
        _write_run(tmp_path / f"c1-{block}.jsonl", block, [], k=_LOCKED_K,
                   decisive=block != "container")
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "Blocks not read: grid, frontier, ladder, container" in out
    assert "  - grid: 240 of 240 pre-registered rows missing" in out
    assert "  - frontier: M6 right: no walk recorded" in out
    assert "pass bar: not established" in out
    assert "grid run not read" in out


def test_the_partial_record_of_a_run_that_crashed_is_reported_and_not_judged(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A crashed block keeps its partial JSONL. Its rows are not read: a silent_wrong row among
    them is not fed to the pass bar, and the campaign says the block is incomplete."""
    _full_campaign(tmp_path)
    partial = [*_m6_grid()[:40], _synth(turns=45.0, cls="silent_wrong", k=_LOCKED_K)]
    _write_run(tmp_path / "c1-grid.jsonl", "grid", partial, k=_LOCKED_K)
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "Blocks not read: grid" in out
    assert "pass bar: not established" in out
    assert "silent_wrong" not in out.split("### Pass bar")[1].split("### Escape clause")[0]


def test_a_failure_recorded_in_an_unread_block_is_named_and_never_read_as_not_fired(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A crashed grid keeps a silent_wrong row, and a cut-short pair run a cell that timed out.
    Neither block is judged, but each recorded outcome is named under the blocks not read, and
    the escape clause does not read "not fired" over rows nobody judged."""
    _full_campaign(tmp_path, skip=("pair",))
    partial = [*_m6_grid()[:40], _synth(turns=45.0, cls="silent_wrong", k=_LOCKED_K)]
    _write_run(tmp_path / "c1-grid.jsonl", "grid", partial, k=_LOCKED_K)
    cells = _clean_pair_cells()[:5]
    cells[0] = _pair(maths.DIAGNOSTIC_CLEARANCES[0], outcome="timeout", k=_LOCKED_K)
    _write_pair_run(tmp_path / "c1-pair.jsonl", cells)
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    head = out.split("### K")[0]
    assert "  - grid: recorded, not judged: M6 right L=45 rod: silent_wrong" in head
    assert "  - pair: recorded, not judged: M6 right rod, right nut c=0 K=3: timeout" in head
    assert "escape clause: not established (blocks not read: grid, pair)" in out
    assert "not fired" not in out


def test_a_fired_escape_clause_stays_fired_and_still_names_the_sources_nobody_judged(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A silent_wrong grid row fires the clause; the container run is cut short and the pair run
    is missing. More rows cannot un-fire it, so it reads FIRED, never "not established", and the
    two sources it could not judge are named on the same line."""
    _full_campaign(tmp_path, skip=("pair",),
                   grid_extra=[_synth(turns=30.0, cls="silent_wrong", left=True)])
    (tmp_path / "c1-container.jsonl").unlink()
    _write_run(tmp_path / "c1-container.jsonl", "container",
               _m6_lengths([], container=True, err=0.0, stl_err=None)[:-1], decisive=False,
               k=_LOCKED_K)
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert ("escape clause: FIRED (sources not read: container; sources missing: pair)\n"
            "- M6 left L=30 rod: silent_wrong") in out
    assert "escape clause: not established" not in out


def test_the_escape_clause_is_not_established_while_a_block_it_draws_on_is_missing(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """No container run: the clause cannot say the container's rows fired nothing."""
    _full_campaign(tmp_path, skip=("container",))
    assert _verdict("c1", tmp_path) == 1
    assert "escape clause: not established (blocks missing: container)" in capsys.readouterr().out


def test_an_incomplete_pair_block_is_reported_and_the_campaign_is_not_clean(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path, skip=("pair",))
    _write_pair_run(tmp_path / "c1-pair.jsonl", _clean_pair_cells()[:5])
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "Blocks not read: pair" in out
    assert "pair: not read" in out


# --- K is the sweep's, never a header's (plan 02-06 review) ---


@pytest.mark.parametrize("block", ["grid", "frontier", "ladder", "container", "pair", "rss"])
def test_a_run_recorded_at_another_k_than_the_sweep_selected_is_not_read_and_never_passes(
        block: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The sweep selects K = 3 from its own rows. Every later run must name that K; one that
    names 5, whatever its rows say, is reported with both Ks and not read."""
    _full_campaign(tmp_path)
    if block == "pair":
        _write_pair_run(tmp_path / "c1-pair.jsonl", _clean_pair_cells(5), k=5)
    elif block == "rss":
        _write_run(tmp_path / "c1-rss.jsonl", "rss", [_synth(k=5)], k=5)
    else:
        rows = {"grid": _m6_grid(), "frontier": _full_walk("M6", None, k=5),
                "ladder": [_synth(turns=10.0, k=5), _synth(turns=60.0, k=5)],
                "container": _m6_lengths([], container=True, err=0.0, stl_err=None, k=5)}[block]
        _write_run(tmp_path / f"c1-{block}.jsonl", block, rows, k=5)
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert f"Blocks not read: {block}" in out
    assert (f"  - {block}: run `c1-{block}` was recorded at K = 5, but the sweep's locked K is 3 "
            "(selected by select_k from run `c1-ksweep`)") in out


@pytest.mark.parametrize("block", ["controls", "trim", "rss"])
def test_an_evidence_run_with_a_row_at_another_k_than_the_locked_one_is_not_read(
        block: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The header names the K the sweep selected, but one row was built at K = 5: a header
    vouches for nothing it did not build, so the run is not read and the campaign never passes."""
    _full_campaign(tmp_path)
    rows = {"controls": _controls_rows(), "trim": [_trim()],
            "rss": [_synth(k=_LOCKED_K)]}[block]
    rows[-1] = {**rows[-1], "k": 5}
    _write_run(tmp_path / f"c1-{block}.jsonl", block, rows, k=_LOCKED_K)
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert f"Blocks not read: {block}" in out
    assert (f"  - {block}: run `c1-{block}` holds 1 rows recorded at K = 5, but the sweep's "
            "locked K is 3 (selected by select_k from run `c1-ksweep`)") in out


def test_the_pair_run_is_read_at_the_k_the_sweep_selected_not_at_the_one_its_header_names(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The pair evidence, its header and its cells all at K = 5 while the sweep selects 3: the
    review's case. Nothing about the pair is judged, and the pair escape does not fire on cells
    nobody read."""
    _full_campaign(tmp_path, skip=("pair",))
    _write_pair_run(tmp_path / "c1-pair.jsonl", _clean_pair_cells(5), k=5)
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "pair: not read" in out.split("### Pair check (D-11 to D-14)")[1]
    assert "pair: not falsifiable" not in out


def test_a_header_that_names_no_k_cannot_stand_in_for_the_locked_one(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path)
    _write_run(tmp_path / "c1-ladder.jsonl", "ladder",
               [_synth(turns=10.0, k=3), _synth(turns=60.0, k=3)], k=None)
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "Blocks not read: ladder" in out
    assert "recorded at K = None" in out


def test_with_no_k_selected_the_harness_default_is_the_locked_k(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """No K qualifies, so the blocks ran at 5 and say so; a run at 3 is not the locked one."""
    _full_campaign(tmp_path, k=5)
    _write_run(tmp_path / "c1-ksweep.jsonl", "ksweep", _m6_ksweep(cls="silent_wrong"))
    _write_run(tmp_path / "c1-ladder.jsonl", "ladder",
               [_synth(turns=10.0, k=3), _synth(turns=60.0, k=3)], k=3)
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "  - ladder: run `c1-ladder` was recorded at K = 3, but the sweep's locked K is 5 " \
           "(no K qualified, so the harness's 5)" in out
    assert "Blocks not read: ladder" in out


def test_a_decisive_void_timeout_holds_the_bar_and_the_turn_caps_name_it(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path, grid_extra=[_synth(kind="void", turns=30.0, cls="timeout")])
    assert _verdict("c1", tmp_path) == 0
    caps = capsys.readouterr().out.split("### Turn caps")[1]
    assert "| no row over budget | no row over budget | 29 |" in caps  # the cap: below L = 30
    assert "- M6: first row over the seconds budget: M6 right L=30 void" in caps


@pytest.mark.parametrize("grid", ["missing", "not read"])
def test_with_no_grid_read_every_grid_cap_says_no_grid_record_never_no_row_over_budget(
        grid: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The bytes and seconds caps are grid claims: with no grid rows read, "no row over budget"
    would be drawn from zero rows."""
    _full_campaign(tmp_path, skip=("grid",) if grid == "missing" else ())
    if grid == "not read":
        _write_run(tmp_path / "c1-grid.jsonl", "grid", _m6_grid()[:40], k=_LOCKED_K)
    assert _verdict("c1", tmp_path) == 1
    caps = capsys.readouterr().out.split("### Turn caps")[1].split("### Controls")[0]
    assert "| no grid record | no grid record | no grid record |" in caps
    assert "no row over budget" not in caps


def test_a_non_decisive_grid_does_not_name_the_first_row_over_the_seconds_budget(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A row is over the clock only on a quiet host: the report must not point at one when the
    grid ran loaded, even though the timeout row is right there in the record."""
    _full_campaign(tmp_path, grid_extra=[_synth(turns=30.0, build_s=45.0)], grid_decisive=False)
    _verdict("c1", tmp_path)
    caps = capsys.readouterr().out.split("### Turn caps")[1].split("### Controls")[0]
    assert f"- M6: first row over the seconds budget: {_NOT_ESTABLISHED}" in caps
    assert "L=30 rod" not in caps


def test_a_decisive_grid_names_the_first_row_over_the_seconds_budget(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path, grid_extra=[_synth(turns=30.0, build_s=45.0)])
    _verdict("c1", tmp_path)
    caps = capsys.readouterr().out.split("### Turn caps")[1].split("### Controls")[0]
    assert "- M6: first row over the seconds budget: M6 right L=30 rod" in caps


def test_a_campaign_whose_volume_estimator_is_not_established_never_passes(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """No grid rod row has a checked preview mesh, so the two estimators cannot be compared:
    everything else is clean, and the campaign still must not read as a pass."""
    _full_campaign(tmp_path, stl_err=None)
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "pass bar: held" in out
    assert "escape clause: not fired" in out
    assert "estimator and T_gate: not established" in out
    assert "not a pass" in out


def test_a_tied_estimator_pair_on_a_non_decisive_grid_never_passes(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Precise and mesh errors within 2x of each other: only the cost could pick one, and the
    grid ran on a loaded host. The same rows on a decisive grid pick the cheaper one."""
    _full_campaign(tmp_path, err=1e-5, stl_err=1.5e-5, grid_decisive=False)
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "estimator and T_gate: not established (the estimators tie within 2x" in out
    assert "pass bar: held" in out
    _full_campaign(tmp_path, prefix="c2", err=1e-5, stl_err=1.5e-5, grid_decisive=True)
    assert _verdict("c2", tmp_path) == 0


def test_a_campaign_whose_gate_tolerance_cannot_be_derived_never_passes(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Both estimators agree with the closed form exactly, so there is no error to scale into a
    gate: T_gate is not established and the campaign is not a clean pass."""
    _full_campaign(tmp_path, err=0.0, stl_err=0.0)
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "no gate can be derived" in out
    assert "estimator and T_gate: not established" in out


def test_a_timeout_on_a_non_decisive_grid_makes_the_bar_not_established_and_exit_1(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path, grid_extra=[_synth(turns=30.0, cls="timeout")],
                   grid_decisive=False)
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "pass bar: not established" in out
    assert "escape clause: not fired" in out
    assert "not established (non-decisive gate)" in out.split("### Turn caps")[1]


def test_the_verdict_only_reads_runs_under_its_own_prefix(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path, prefix="c1")
    _full_campaign(tmp_path, prefix="c2", grid_extra=[_synth(turns=30.0, cls="failure")])
    assert _verdict("c1", tmp_path) == 0
    assert "c2-" not in capsys.readouterr().out


@pytest.mark.parametrize(("prefix", "wanted"), [("../c1", "prefix"), ("nothing", "no runs")])
def test_a_bad_prefix_or_an_empty_one_is_refused_not_passed(
        prefix: str, wanted: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path)
    assert _verdict(prefix, tmp_path) in (1, 2)
    captured = capsys.readouterr()
    assert wanted in captured.out + captured.err


def test_the_verdict_never_reads_a_campaign_whose_prefix_extends_its_own(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path)
    _full_campaign(tmp_path, prefix="c1-x", grid_extra=[_synth(turns=30.0, cls="failure")])
    assert _verdict("c1", tmp_path) == 0
    assert "c1-x-" not in capsys.readouterr().out
    alone = tmp_path / "alone"
    alone.mkdir()
    _full_campaign(alone, skip=("pair",))
    _write_pair_run(alone / "c1-x-pair.jsonl", _clean_pair_cells())
    assert _verdict("c1", alone) == 1
    captured = capsys.readouterr()
    assert "pair: not recorded" in captured.out
    assert "c1-x-pair" not in captured.out + captured.err


def test_a_run_file_whose_header_names_another_block_is_refused(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path)
    _write_run(tmp_path / "c1-grid.jsonl", "ksweep", [])
    assert _verdict("c1", tmp_path) == 2
    err = capsys.readouterr().err
    assert "c1-grid.jsonl" in err
    assert "holds a ksweep run" in err


def test_a_file_that_is_not_a_campaign_run_name_is_never_read(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path)
    _write_run(tmp_path / "c1-grid-again.jsonl", "grid", [_synth(turns=30.0, cls="failure")])
    _write_pair_run(tmp_path / "c1-pair-again.jsonl", _clean_pair_cells())
    assert _verdict("c1", tmp_path) == 0
    captured = capsys.readouterr()
    assert "again" not in captured.out + captured.err


# --- The comparison rows and the tip trim (Phase 2, plan 02-04) ---

_M6_CLOSED_10 = maths.closed_volume(6.0, 1.0, 10.0)


def _comparison(kind: str, *, left_hand: bool = False) -> RowRequest:
    """An M6 request of `kind` at 10 turns (10 mm), no mesh and no STEP."""
    return {**_REQUEST, "kind": kind, "turns": 10.0, "length": 10.0, "presets": [],
            "left_hand": left_hand}


def test_the_negative_control_is_never_classified_ok_by_the_real_kernel() -> None:
    """The class, not the ratio: the boolean may land differently on linux/amd64 (STACK)."""
    record = worker.run_row(_comparison("naive"))
    assert parse_record(json.dumps(record)) == record
    assert classify_record(record)[0] != "ok"


def test_the_one_pipe_twist_of_ten_turns_is_classified_ok_by_the_real_kernel() -> None:
    record = worker.run_row(_comparison("one_pipe"))
    assert classify_record(record) == ("ok", ())
    assert record["trim_s"] is None


def test_the_default_worker_cannot_see_the_ruled_surface_package() -> None:
    """T-02-11: the reference package is on the reference worker's path only, so a ruled row
    in the default environment is one recorded failure and not a built row."""
    record = worker.run_row(_comparison("ruled"))
    assert record["outcome"] == "failure"
    assert record["error"] is not None
    assert maths.RULED_MODULE.split(".")[0] in record["error"]


@pytest.mark.parametrize("kind", ["naive", "ruled"])
def test_the_negative_control_and_the_reference_are_right_hand_only(kind: str) -> None:
    record = worker.run_row(_comparison(kind, left_hand=True))
    assert record["outcome"] == "failure"
    assert record["error"] is not None
    assert "right hand only" in record["error"]


def _naive(ratio: float, *, solids: int = 1, valid: bool = True, kind: str = "naive") -> RowRecord:
    return {**_built(_M6_CLOSED_10 * ratio, solids=solids, valid=valid), "kind": kind,
            "turns": 10.0, "length": 10.0, "presets": []}


def test_the_known_bad_inputs_are_the_naive_rows_with_one_valid_solid_below_half_the_volume(
) -> None:
    keep = _naive(0.238)
    rows = [keep, _naive(0.5), _naive(1.011), _naive(0.2, solids=2), _naive(0.2, valid=False),
            _naive(0.2, kind="rod"), failed_record(_comparison("naive"), "failure", "Null"),
            _naive(0.4999)]
    assert known_bad_inputs(rows) == [keep, _naive(0.4999)]
    assert known_bad_inputs([]) == []


def _trim(*, precise: float = 1.0, solids: int = 1, valid: bool = True, watertight: bool = True,
          volume: float = 100.0, checked: bool = True) -> RowRecord:
    mesh = _mesh(watertight=watertight, volume=volume, checked=checked)
    return {**_built(precise, solids=solids, valid=valid, meshes=[mesh]), "kind": "trim",
            "trim_s": 0.5, "k": _LOCKED_K}


def test_a_trim_row_is_judged_on_solids_validity_and_the_preview_check_never_on_a_closed_form(
) -> None:
    far_off = _trim(precise=0.3 * maths.closed_volume(6.0, 1.0, 5.0), volume=7.0)
    assert classify_record(far_off) == ("ok", ())  # a closed form would call this wrong
    assert classify_record(_trim(checked=False)) == ("ok", ())
    assert classify_record(_trim(solids=2))[0] == "silent_wrong"
    assert classify_record(_trim(valid=False))[0] == "silent_wrong"
    assert classify_record(_trim(watertight=False))[0] == "silent_wrong"
    assert classify_record(_trim(volume=-1.0))[0] == "silent_wrong"
    died = failed_record(far_off, "timeout", "late")
    assert classify_record(died) == ("timeout", ("late",))


def test_no_comparison_or_trim_row_can_fail_the_pass_bar_or_fire_the_escape_clause() -> None:
    rows = [_synth(), _naive(0.238), _naive(0.2, kind="one_pipe"), _trim(solids=2),
            _naive(0.1, kind="ruled")]
    assert pass_bar(rows, True) == ("held", ())
    assert escape_rows(rows) == ()


def test_a_trim_request_costs_build_plus_trim_plus_the_slower_export() -> None:
    row: RowRecord = {**_synth(build_s=1.0, fine=(10, 10, 2.0, 5), step=(5, 3.0)),
                      "kind": "trim", "trim_s": 0.5}
    assert request_seconds(row) == 1.0 + 0.5 + 3.0
    assert request_seconds({**row, "trim_s": None}) is None  # never a partial sum


def test_a_real_trim_row_records_the_trim_seconds_and_is_judged_without_a_closed_form() -> None:
    request: RowRequest = {**_REQUEST, "kind": "trim", "turns": 20.0, "length": 20.0}
    record = worker.run_row(request)
    assert parse_record(json.dumps(record)) == record
    assert record["trim_s"] is not None
    assert record["trim_s"] > 0
    assert classify_record(record) == ("ok", ())


def test_trim_seconds_are_set_exactly_on_a_built_trim_row() -> None:
    row = _trim()
    assert parse_record(json.dumps(row)) == row
    with pytest.raises(ValueError, match="trim_s"):
        parse_record(json.dumps({**_built(1.0), "trim_s": 0.1}))  # a rod row cannot carry one
    with pytest.raises(ValueError, match="trim_s"):
        parse_record(json.dumps({**row, "trim_s": None}))  # a trim row must
    liar = {**failed_record(_REQUEST, "failure", "boom"), "trim_s": 0.1}
    with pytest.raises(ValueError, match="trim_s"):
        parse_record(json.dumps(liar))


def test_the_tip_chamfer_angle_is_30_degrees_and_says_it_is_unverified() -> None:
    source = (Path(spike_cli.__file__).parent / "maths.py").read_text()
    line = next(line for line in source.splitlines() if line.startswith("TIP_CHAMFER_DEG"))
    assert line == "TIP_CHAMFER_DEG = 30.0"
    assert maths.TIP_CHAMFER_DEG == 30.0
    comment: list[str] = []
    for above in reversed(source.split(line)[0].splitlines()):
        if not above.startswith("#"):
            break
        comment.append(above)
    assert "UNVERIFIED" in " ".join(comment)


def test_the_controls_block_runs_ruled_in_the_reference_worker_and_the_rest_right_hand() -> None:
    default, reference = _FakeWorker(), _FakeWorker()
    c = spike_cli.Campaign(default, True, None, reference=reference)
    spike_cli._BLOCKS["controls"](c, 5, False)
    assert {r["kind"] for r in default.requests} == {"naive", "one_pipe"}
    assert {r["kind"] for r in reference.requests} == {"ruled"}
    assert {r["left_hand"] for r in default.requests + reference.requests} == {False}
    assert all(not r["presets"] and not r["step"] for r in default.requests)
    assert {r["size"] for r in default.requests} == set(maths.SAMPLE_SIZES)
    m6 = [r for r in default.requests if r["size"] == "M6"]
    assert [r["length"] for r in m6 if r["kind"] == "naive"] == [10.0, 20.0, 60.0]
    assert [r["turns"] for r in m6 if r["kind"] == "one_pipe"] == [60.0, 100.0, 160.0, 200.0,
                                                                   250.0]
    assert [r["length"] for r in reference.requests if r["size"] == "M6"] == [10.0, 60.0]


def test_the_controls_smoke_scope_says_so_when_the_package_is_missing_and_refuses_nothing() -> None:
    default = _FakeWorker()
    c = spike_cli.Campaign(default, True, None)
    spike_cli._BLOCKS["controls"](c, 5, True)
    assert [r["kind"] for r in default.requests] == ["naive", "one_pipe"]
    assert c.notes == [spike_cli.PACKAGE_NOT_IMPORTABLE]
    assert spike_cli.PACKAGE_NOT_IMPORTABLE == "ruled: skipped, package not importable"
    reference = _FakeWorker()
    c2 = spike_cli.Campaign(default, True, None, reference=reference)
    spike_cli._BLOCKS["controls"](c2, 5, True)
    assert [(r["kind"], r["turns"]) for r in reference.requests] == [("ruled", 10.0)]
    assert c2.notes == []


def test_the_trim_block_is_one_full_rod_row_per_size_and_hand_at_the_standard_max() -> None:
    c, fake = _campaign()
    spike_cli._BLOCKS["trim"](c, 5, False)
    assert len(fake.requests) == 2 * 15
    first = fake.requests[0]
    assert (first["kind"], first["size"], first["left_hand"], first["length"]) == (
        "trim", "M2", False, 20.0)
    assert (first["step"], first["gzip_on"], first["clearance"]) == (True, ["fine"], 0.0)
    assert [name for name, _, _ in first["presets"]] == ["preview", "fine"]
    assert {r["length"] for r in fake.requests if r["size"] == "M20"} == {200.0}
    smoke_c, smoke_fake = _campaign()
    spike_cli._BLOCKS["trim"](smoke_c, 5, True)
    assert [(r["size"], r["length"], r["left_hand"]) for r in smoke_fake.requests] == [
        ("M6", 20.0, False)]


def _controls_rows() -> list[RowRecord]:
    """The comparison rows as a controls run at the locked K records them."""
    rows = [_naive(0.238), _naive(1.0, kind="one_pipe"), _naive(0.985, kind="ruled")]
    return [{**r, "k": _LOCKED_K} for r in rows]


def test_the_controls_section_lists_the_rows_the_known_bad_inputs_and_the_profile_caveat() -> None:
    text = "\n".join(spike_cli.controls_section(_controls_rows()))
    assert "| naive sweep + fuse (negative control) | M6 | 10 | 10 | silent_wrong | 1 | yes " \
           "| 0.238000 |" in text
    assert "- naive_sweep_fuse(d=6.0, pitch=1.0, length=10.0): precise ratio 0.238000" in text
    assert "ratio to this closed form is not an accuracy claim" in text
    assert "NEGATIVE CONTROL READ OK" not in text
    assert spike_cli.controls_section([]) == ["controls: not recorded"]


def test_a_negative_control_that_reads_ok_is_said_so_loudly() -> None:
    text = "\n".join(spike_cli.controls_section([_naive(1.0)]))
    assert "NEGATIVE CONTROL READ OK: M6 right L=10 naive" in text
    assert "- none recorded" in text


def test_the_trim_section_labels_the_cone_angle_unverified_and_no_pass_bar_input() -> None:
    text = "\n".join(spike_cli.trim_section([_trim()]))
    assert "| M6 | right | 5 | ok | 0.50 |" in text
    assert "30 degrees" in text
    assert "UNVERIFIED" in text
    assert "never enter the pass bar" in text
    assert spike_cli.trim_section([]) == ["trim: not recorded"]


def test_a_trim_row_prints_no_error_against_a_closed_form_it_does_not_have() -> None:
    cells = _table_row(_trim(precise=0.3), "ok", 1.0).split("|")
    assert [c.strip() for c in cells[9:11]] == ["n/a", "n/a"]  # precise and default rel err


def test_the_controls_block_refuses_without_the_scratch_directory_before_anything_runs(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _forbid_everything_after_the_id_checks(monkeypatch)
    assert spike_cli.run_block("controls", "a-run", "a-sweep", results_dir=tmp_path, env={}) == 2
    assert spike_cli.CQW_ENV in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_the_controls_block_refuses_a_scratch_directory_the_package_does_not_import_from(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _forbid_everything_after_the_id_checks(monkeypatch)
    empty = tmp_path / "empty"
    empty.mkdir()
    results = tmp_path / "results"
    results.mkdir()
    env = {spike_cli.CQW_ENV: str(empty)}
    assert spike_cli.run_block("controls", "a-run", "a-sweep", results_dir=results, env=env) == 2
    assert "not importable" in capsys.readouterr().err
    assert list(results.iterdir()) == []


def _stub_package(root: Path) -> Path:
    package = root / "scratch" / "cq_warehouse"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("")
    (package / "thread.py").write_text("")
    return package.parent


def test_the_reference_worker_environment_puts_the_scratch_directory_first_on_pythonpath(
        tmp_path: Path) -> None:
    scratch = _stub_package(tmp_path)
    env, why = spike_cli._reference_env({spike_cli.CQW_ENV: str(scratch), "PYTHONPATH": "/else"})
    assert why == ""
    assert env is not None
    assert env["PYTHONPATH"] == f"{scratch}{os.pathsep}/else"
    assert env[spike_cli.CQW_ENV] == str(scratch)


def test_a_controls_run_streams_the_comparison_rows_and_prints_their_section(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _held(monkeypatch)
    scratch = _stub_package(tmp_path)
    _m6_only(monkeypatch)
    ksweep = _m6_ksweep()
    _write_run(tmp_path / "sweep.jsonl", "ksweep", ksweep)
    env = {spike_cli.CQW_ENV: str(scratch)}
    assert spike_cli.run_block("controls", "ctl", "sweep", results_dir=tmp_path, env=env) == 0
    lines = (tmp_path / "ctl.jsonl").read_text().splitlines()
    assert parse_header(lines[0])["block"] == "controls"
    kinds = {parse_result_row(line)["kind"] for line in lines[1:]}
    assert kinds == {"naive", "one_pipe", "ruled"}
    assert "### Controls (D-06)" in capsys.readouterr().out


def test_smoke_controls_prints_the_naive_class_and_it_never_reads_ok(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """The protocol expects only "never ok" of the naive row: the class it does read is the
    kernel's, `silent_wrong` on arm64 macOS and `failure` (Null TopoDS_Shape) on linux/amd64 in
    `screw:latest`, so pinning one class failed CI on the other platform."""
    monkeypatch.delenv(spike_cli.CQW_ENV, raising=False)
    assert spike_cli.smoke_block("controls") == 0
    out = capsys.readouterr().out
    assert "not a campaign run" in out
    naive = re.findall(r"^\| M6 \| right \| 10 \| 5 \| naive \| (\w+) \|", out, re.MULTILINE)
    assert len(naive) == 1
    assert naive[0] in ("silent_wrong", "failure", "worker_died", "timeout")
    assert "| M6 | right | 10 | 5 | one_pipe | ok |" in out
    assert "ruled: skipped, package not importable" in out


def test_smoke_trim_runs_the_real_trim_and_prints_the_trim_seconds(
        capsys: pytest.CaptureFixture[str]) -> None:
    assert spike_cli.smoke_block("trim") == 0
    out = capsys.readouterr().out
    assert "not a campaign run" in out
    assert "| M6 | right | 20 | 5 | trim | ok |" in out
    assert "Trim s" in out


def test_the_verdict_prints_the_controls_and_trim_evidence_beside_a_clean_pass(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A naive row that is silent_wrong on purpose and a trim row judged without a closed form
    sit beside the verdict and cannot change it."""
    _full_campaign(tmp_path)
    _write_run(tmp_path / "c1-controls.jsonl", "controls", _controls_rows(), k=_LOCKED_K)
    _write_run(tmp_path / "c1-trim.jsonl", "trim", [_trim()], k=_LOCKED_K)
    assert _verdict("c1", tmp_path) == 0
    out = capsys.readouterr().out
    controls = out.split("### Controls (D-06)")[1].split("### Tip trim cost")[0]
    assert "naive_sweep_fuse(d=6.0, pitch=1.0, length=10.0)" in controls
    assert "pass bar: held" in out
    assert "| M6 | right | 5 | ok | 0.50 |" in out.split("### Tip trim cost (D-08)")[1]


def test_a_verdict_without_the_controls_or_trim_runs_says_they_are_not_recorded(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path)
    assert _verdict("c1", tmp_path) == 0
    out = capsys.readouterr().out
    assert "controls: not recorded" in out
    assert "trim: not recorded" in out


# --- Fresh-child RSS, the L19 gzip table and the container block (Phase 2, plan 02-04) ---

_TABLE: list[tuple[int, int, float, float]] = [(1, 100, 1.0, 2.0), (6, 90, 2.0, 3.0),
                                               (9, 89, 3.0, 4.0)]


def _once_request(*, table: bool = False, presets: int = 1) -> RowRequest:
    names = [("preview", 0.08, 0.5), ("fine", 0.01, 0.1)][:presets]
    return {**_REQUEST, "turns": 3.0, "length": 3.0, "presets": names, "gzip_on": ["fine"],
            "want_gzip_table": table}


def _fresh(request: RowRequest, *, rss: int | None = 800 * 1024 * 1024) -> RowRecord:
    """What a healthy fresh `--once` child would answer for a rod request."""
    record = _ok_record(request)
    table = _TABLE if request["want_gzip_table"] else None
    return {**record, "peak_rss_bytes": rss, "gzip_table": table,
            "gzip_selected": 1 if table else None}


def test_the_container_argv_is_a_list_that_mounts_bench_read_only_under_linux_amd64() -> None:
    argv = container_argv("probe-1", Path("/repo"))
    assert isinstance(argv, list)
    assert all(isinstance(part, str) for part in argv)
    assert argv[:3] == ["docker", "run", "-i"]
    assert "--rm" in argv
    assert argv[argv.index("--platform") + 1] == "linux/amd64"
    assert argv[argv.index("--name") + 1] == "probe-1"
    assert argv[argv.index("-v") + 1] == "/repo/bench:/probe/bench:ro"
    assert argv[argv.index("-e") + 1] == "PYTHONPATH=/probe"
    assert argv[argv.index("--entrypoint") + 1] == "python"
    assert argv[-3:] == [CONTAINER_IMAGE, "-m", "bench.thread_spike.worker"]
    assert CONTAINER_IMAGE == "screw:latest"


def test_docker_kill_stops_the_container_the_argv_named_and_ignores_an_argv_without_one(
        monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_run(argv: list[str], **kwargs: object) -> None:
        calls.append(argv)

    monkeypatch.setattr(subprocess, "run", fake_run)
    docker_kill(container_argv("probe-7", Path("/repo")))
    docker_kill([sys.executable, "-c", "pass"])
    assert calls == [["docker", "kill", "probe-7"]]


def test_a_timeout_runs_the_on_timeout_hook_and_the_respawn_asks_for_a_new_argv() -> None:
    spawned: list[list[str]] = []
    killed: list[list[str]] = []

    def argv() -> list[str]:
        spawned.append([sys.executable, "-c", f"import time; time.sleep(60)  # {len(spawned)}"])
        return spawned[-1]

    worker = Worker(argv=argv, on_timeout=killed.append)
    try:
        first = worker.run(_REQUEST, 0.5)
        second = worker.run(_REQUEST, 0.5)
    finally:
        worker.close()
    assert (first["outcome"], second["outcome"]) == ("timeout", "timeout")
    assert len(spawned) == 2
    assert spawned[0] != spawned[1]
    assert killed == spawned


def test_a_worker_that_dies_does_not_run_the_on_timeout_hook() -> None:
    killed: list[list[str]] = []
    worker = Worker(argv=[sys.executable, "-c", "import os; os._exit(3)"],
                    on_timeout=killed.append)
    try:
        assert worker.run(_REQUEST, 30.0)["outcome"] == "worker_died"
    finally:
        worker.close()
    assert killed == []


def test_a_fresh_once_child_records_its_peak_rss_and_a_persistent_worker_never_does() -> None:
    fresh = run_once(_once_request(), ROW_TIMEOUT_S)
    assert fresh["outcome"] == "built"
    assert fresh["peak_rss_bytes"] is not None
    assert fresh["peak_rss_bytes"] > 50 * 1024 * 1024  # a kernel process, not a stray byte count
    assert fresh["gzip_table"] is None
    assert parse_record(json.dumps(fresh)) == fresh
    persistent = worker.run_row(_once_request())
    assert persistent["outcome"] == "built"
    assert persistent["peak_rss_bytes"] is None  # a high-water mark of the whole process


def test_the_once_child_runs_l19s_table_on_the_rows_own_stl_after_the_rss_reading() -> None:
    record = run_once({**_once_request(table=True), "presets": [("fine", 0.01, 0.1)]},
                      ROW_TIMEOUT_S)
    assert record["peak_rss_bytes"] is not None
    table = record["gzip_table"]
    assert table is not None
    assert [level for level, *_ in table] == [1, 6, 9]
    assert all(out_bytes > 0 and single > 0 and concurrent > 0
               for _, out_bytes, single, concurrent in table)
    assert record["gzip_selected"] in (1, 6, 9)
    assert parse_record(json.dumps(record)) == record


@pytest.mark.parametrize(("request_", "why"), [
    (_once_request(presets=2), "exactly one preset"),
    ({**_once_request(), "presets": []}, "exactly one preset"),
])
def test_a_once_rod_row_with_other_than_one_preset_is_refused_not_given_a_misleading_peak(
        request_: RowRequest, why: str) -> None:
    record = worker.run_row(request_, once=True)
    assert record["outcome"] == "failure"
    assert record["error"] is not None
    assert why in record["error"]
    assert record["peak_rss_bytes"] is None


def test_a_persistent_worker_refuses_a_gzip_table_request_and_a_void_cannot_ask_for_one() -> None:
    record = worker.run_row(_once_request(table=True))
    assert record["outcome"] == "failure"
    assert record["error"] is not None
    assert "--once" in record["error"]
    void = worker.run_row({**_REQUEST, "kind": "void", "presets": [], "want_gzip_table": True},
                          once=True)
    assert void["outcome"] == "failure"
    assert void["error"] is not None
    assert "rod" in void["error"]


def test_a_record_carries_a_gzip_table_exactly_when_its_request_asked_for_one() -> None:
    asked: RowRequest = {**_once_request(table=True), "kind": "rod"}
    record = _fresh(asked)
    assert parse_record(json.dumps(record)) == record
    for broken in ({**record, "gzip_table": None, "gzip_selected": None},  # asked, not given
                   {**record, "want_gzip_table": False},  # given, not asked
                   {**record, "gzip_selected": None},  # a table with no selection
                   {**record, "gzip_table": []}):  # an empty table is no table
        with pytest.raises(ValueError, match="gzip"):
            parse_record(json.dumps(broken))
    with pytest.raises(ValueError, match="gzip_table"):
        parse_record(json.dumps({**record, "gzip_table": [[1, 2, 3]]}))


def test_only_a_built_rod_row_carries_a_peak_rss_or_a_gzip_table() -> None:
    rod = _fresh(_once_request())
    assert parse_record(json.dumps(rod)) == rod
    with pytest.raises(ValueError, match="peak_rss_bytes"):
        parse_record(json.dumps({**rod, "kind": "void", "presets": []}))
    died = {**failed_record(_REQUEST, "timeout", "late"), "peak_rss_bytes": 5}
    with pytest.raises(ValueError, match="memory or gzip"):
        parse_record(json.dumps(died))
    liar = {**failed_record(_REQUEST, "failure", "boom"), "gzip_table": [[1, 2, 3.0, 4.0]],
            "gzip_selected": 1}
    with pytest.raises(ValueError, match="memory or gzip"):
        parse_record(json.dumps(liar))


def test_an_rss_row_prints_its_figure_labelled_a_fresh_child_and_a_persistent_row_prints_none(
) -> None:
    fresh = _fresh({**_once_request(), "kind": "rod"})
    persistent: RowRecord = {**_ok_record(_once_request()), "size": "M8"}
    text = "\n".join(spike_cli.rss_section([fresh, persistent]))
    assert "| M6 | right | preview | 3 | 3 | below standard max | 800.0 MiB (fresh child, this "\
           "row only) | ok |" in text
    assert "| M8 | right | preview | 3 | 3 | below standard max | n/a | ok |" in text
    assert text.count("fresh child, this row only") == 1
    assert spike_cli.rss_section([]) == ["rss: not recorded"]


def test_the_l19_table_and_the_selected_level_print_only_for_rows_that_asked_for_one() -> None:
    plain = _fresh(_once_request())
    assert "L19" not in "\n".join(spike_cli.rss_section([plain]))
    asked = _fresh({**_once_request(table=True), "kind": "rod"})
    text = "\n".join(spike_cli.rss_section([plain, asked]))
    assert "| M6 | 6 | 90 | 2.0 | 3.0 |" in text
    assert "- M6: selected gzip level 1" in text
    assert text.count("selected gzip level") == 1


def test_the_standard_max_and_the_frontier_terminal_rows_are_told_apart_in_the_rss_table() -> None:
    standard = _fresh({**_once_request(), "turns": 60.0, "length": 60.0})
    terminal = _fresh({**_once_request(), "turns": 100.0, "length": 100.0})
    text = "\n".join(spike_cli.rss_section([standard, terminal]))
    assert "| 60 | 60 | standard max |" in text
    assert "| 100 | 100 | frontier terminal |" in text


def test_the_frontier_terminals_are_the_last_measured_turn_count_per_size_and_hand() -> None:
    rows = _walk("M6", False, 100) + _walk("M6", True, None) + _walk("M2", False, 55)
    assert spike_cli._frontier_terminals(rows) == [
        ("M2", False, 55), ("M6", False, 100), ("M6", True, 250)]


class _FreshLog:
    def __init__(self) -> None:
        self.requests: list[RowRequest] = []
        self.timeouts: list[float] = []

    def __call__(self, request: RowRequest, timeout_s: float) -> RowRecord:
        self.requests.append(request)
        self.timeouts.append(timeout_s)
        return _fresh(request)


def test_the_rss_block_is_one_fresh_child_per_size_hand_and_preset_plus_the_terminal_rows(
) -> None:
    log = _FreshLog()
    default = _FakeWorker()
    frontier = _walk("M6", False, 100) + _walk("M6", True, None)
    c = spike_cli.Campaign(default, True, None, fresh=log, frontier_rows=frontier)
    spike_cli._BLOCKS["rss"](c, 5, False)
    assert default.requests == []  # no persistent worker: nothing else may print an RSS
    assert len(log.requests) == 15 * 2 * 2 + 2
    standard, terminals = log.requests[:60], log.requests[60:]
    assert all(len(r["presets"]) == 1 and r["gzip_on"] == [r["presets"][0][0]]
               for r in standard)
    assert {name for r in standard for name, _, _ in r["presets"]} == {"preview", "fine"}
    tabled = [r for r in standard if r["want_gzip_table"]]
    assert len(tabled) == 15  # one per size: the right-hand fine standard-max child
    assert all(r["presets"][0][0] == "fine" and not r["left_hand"] for r in tabled)
    assert tabled[0]["length"] == 20.0
    assert tabled[-1]["length"] == 200.0
    assert [(r["size"], r["left_hand"], r["turns"]) for r in terminals] == [
        ("M6", False, 100.0), ("M6", True, 250.0)]
    assert all(r["presets"][0][0] == "fine" and not r["want_gzip_table"] for r in terminals)
    assert {r["k"] for r in log.requests} == {5}
    assert log.timeouts.count(verdict_module.GZIP_TABLE_TIMEOUT_S) == 15
    assert log.timeouts.count(ROW_TIMEOUT_S) == 47


def test_the_rss_block_without_frontier_rows_is_refused_and_its_smoke_is_one_child() -> None:
    c = spike_cli.Campaign(_FakeWorker(), True, None, fresh=_FreshLog())
    with pytest.raises(ValueError, match="frontier"):
        spike_cli._BLOCKS["rss"](c, 5, False)
    log = _FreshLog()
    smoke = spike_cli.Campaign(_FakeWorker(), True, None, fresh=log)
    spike_cli._BLOCKS["rss"](smoke, 5, True)
    assert [(r["size"], r["turns"], r["presets"][0][0], r["want_gzip_table"])
            for r in log.requests] == [("M6", 10.0, "fine", True)]


def test_the_container_block_is_the_full_grid_in_the_image_with_no_presets_and_no_step() -> None:
    default, container = _FakeWorker(), _FakeWorker()
    c = spike_cli.Campaign(default, False, None, container=container)
    spike_cli._BLOCKS["container"](c, 5, False)
    assert default.requests == []
    assert len(container.requests) == 2 * 2 * 1790
    rod, void = container.requests[:2]
    assert (rod["kind"], rod["presets"], rod["step"], rod["gzip_on"], rod["clearance"]) == (
        "rod", [], False, [], 0.0)
    assert (void["kind"], void["clearance"]) == ("void", maths.VOID_CLEARANCE)
    assert {r["left_hand"] for r in container.requests} == {False, True}
    assert {r["k"] for r in container.requests} == {5}
    smoke_container = _FakeWorker()
    smoke = spike_cli.Campaign(default, False, None, container=smoke_container)
    spike_cli._BLOCKS["container"](smoke, 5, True)
    assert [(r["kind"], r["size"], r["turns"]) for r in smoke_container.requests] == [
        ("rod", "M6", 5.0), ("void", "M6", 5.0)]


def test_a_container_row_that_is_silent_wrong_fails_the_pass_bar_naming_the_row() -> None:
    assert pass_bar([_synth(), _synth(kind="void")], False) == ("held", ())
    status, named = pass_bar([_synth(), _synth(turns=30.0, cls="silent_wrong")], False)
    assert status == "failed"
    assert named == ("M6 right L=30 rod: silent_wrong",)


def test_the_container_rows_count_toward_the_pass_bar_and_the_escape_clause_in_the_verdict(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path, container_extra=[_synth(turns=30.0, cls="silent_wrong", left=True,
                                                     preview=False, fine=None, step=None)])
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "pass bar: failed" in out
    assert "escape clause: FIRED" in out
    assert out.count("- container M6 left L=30 rod: silent_wrong") == 2
    assert "container (run `c1-container`, non-decisive)" in out


def test_a_campaign_without_the_container_run_is_never_a_pass(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path, skip=("container",))
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "Blocks missing: container" in out
    assert "pass bar: not established" in out
    assert "no container run" in out


def test_a_container_timeout_is_never_a_cap_because_emulated_timings_are_never_decisive(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path, container_extra=[_synth(turns=30.0, cls="timeout", preview=False,
                                                     fine=None, step=None)])
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "pass bar: not established" in out
    assert "- container M6 right L=30 rod: timeout" in out


def test_the_verdict_prints_the_rss_table_and_the_l19_table_from_a_recorded_run(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path)
    asked: RowRequest = {**_once_request(table=True), "turns": 60.0, "length": 60.0,
                         "k": _LOCKED_K}
    _write_run(tmp_path / "c1-rss.jsonl", "rss", [_fresh(asked)], k=_LOCKED_K)
    assert _verdict("c1", tmp_path) == 0
    out = capsys.readouterr().out.split("### Peak RSS and the L19 gzip table")[1]
    assert "800.0 MiB (fresh child, this row only)" in out
    assert "| M6 | 9 | 89 | 3.0 | 4.0 |" in out
    assert "- M6: selected gzip level 1" in out


def _image_says(monkeypatch: pytest.MonkeyPatch, image: str | None) -> None:
    monkeypatch.setattr(spike_cli, "_image_facts",
                        lambda: (image, "" if image else "image screw:latest is not available"))


def test_the_container_block_refuses_before_the_guard_when_docker_or_the_image_is_absent(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _forbid_everything_after_the_id_checks(monkeypatch)
    _image_says(monkeypatch, None)
    assert spike_cli.run_block("container", "a-run", "a-sweep", results_dir=tmp_path) == 2
    assert "is not available" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []
    assert spike_cli.smoke_block("container") == 2


def test_a_container_run_is_never_decisive_and_says_which_image_and_that_timings_are_emulated(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _held(monkeypatch, decisive=True)  # the host gate was quiet
    _image_says(monkeypatch, "sha256:abc 2026-10-06T08:00:00Z")
    monkeypatch.setattr("platform.machine", lambda: "arm64")

    def one_container_row(c: spike_cli.Campaign, k: int, smoke: bool) -> None:
        c.measure({**_REQUEST, "k": k, "presets": []}, via="container")

    monkeypatch.setitem(spike_cli._BLOCKS, "container", one_container_row)
    _m6_only(monkeypatch)
    ksweep = _m6_ksweep()
    _write_run(tmp_path / "sweep.jsonl", "ksweep", ksweep)
    assert spike_cli.run_block("container", "box", "sweep", results_dir=tmp_path) == 0
    header = parse_header((tmp_path / "box.jsonl").read_text().splitlines()[0])
    assert header["decisive"] is False  # emulated timings prove nothing about the host
    out = capsys.readouterr().out
    assert "- Image: `screw:latest` sha256:abc 2026-10-06T08:00:00Z" in out
    assert "platform linux/amd64 under emulation on arm64: timings feed no bound" in out
    assert "non-decisive by construction" in out
    assert "### Container validity (D-05)" in out


@pytest.mark.parametrize(("block", "frontier_from", "wanted"), [
    ("rss", None, "requires --frontier-from"),
    ("grid", "front", "only the rss block takes --frontier-from"),
    ("rss", "../x", "not a run id"),
])
def test_only_the_rss_block_takes_frontier_from_and_it_requires_one(
        block: str, frontier_from: str | None, wanted: str, tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _forbid_everything_after_the_id_checks(monkeypatch)
    assert spike_cli.run_block(block, "a-run", "a-sweep", results_dir=tmp_path,
                               frontier_from=frontier_from) == 2
    assert wanted in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("which", ["missing", "wrong block"])
def test_a_frontier_from_run_that_is_missing_or_not_a_frontier_run_is_refused(
        which: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _held(monkeypatch)
    _m6_only(monkeypatch)
    ksweep = _m6_ksweep()
    _write_run(tmp_path / "sweep.jsonl", "ksweep", ksweep)
    if which == "wrong block":
        _write_run(tmp_path / "front.jsonl", "grid", [_synth()])
    assert spike_cli.run_block("rss", "a-rss", "sweep", results_dir=tmp_path,
                               frontier_from="front") == 2
    err = capsys.readouterr().err
    assert "refused" in err
    assert "frontier" in err
    assert not (tmp_path / "a-rss.jsonl").exists()


@pytest.mark.parametrize("cut", ["header only", "one row short"])
def test_a_k_from_sweep_that_is_incomplete_is_refused_before_anything_is_written(
        cut: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _held(monkeypatch)
    _m6_only(monkeypatch)
    monkeypatch.setitem(spike_cli._BLOCKS, "grid", _one_row_block)
    _write_run(tmp_path / "sweep.jsonl", "ksweep", [] if cut == "header only"
               else _m6_ksweep()[:-1])
    assert spike_cli.run_block("grid", "a-grid", "sweep", results_dir=tmp_path) == 2
    assert "incomplete" in capsys.readouterr().err
    assert not (tmp_path / "a-grid.jsonl").exists()


@pytest.mark.parametrize("fault", ["cut short", "foreign size", "another K"])
def test_a_frontier_from_walk_that_is_incomplete_foreign_or_at_another_k_is_refused(
        fault: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _held(monkeypatch)
    _m6_only(monkeypatch)
    monkeypatch.setitem(spike_cli._BLOCKS, "rss", _one_row_block)
    _write_run(tmp_path / "sweep.jsonl", "ksweep", _m6_ksweep())
    walk = _full_walk("M6", None, k=_LOCKED_K)
    walk_k = _LOCKED_K
    if fault == "cut short":
        walk = _walk("M6", False, None, end=100, k=_LOCKED_K) + _walk("M6", True, None,
                                                                     k=_LOCKED_K)
    elif fault == "foreign size":
        walk = [*walk, _synth("M8", turns=60.0, k=_LOCKED_K)]
    else:
        walk_k = 5
        walk = _full_walk("M6", None, k=walk_k)
    _write_run(tmp_path / "front.jsonl", "frontier", walk, k=walk_k)
    assert spike_cli.run_block("rss", "a-rss", "sweep", results_dir=tmp_path,
                               frontier_from="front") == 2
    err = capsys.readouterr().err
    assert ("K 5" in err and "K 3" in err) if fault == "another K" else "incomplete" in err
    assert not (tmp_path / "a-rss.jsonl").exists()


def test_smoke_rss_runs_one_real_fresh_child_and_prints_its_peak_and_the_table(
        capsys: pytest.CaptureFixture[str]) -> None:
    assert spike_cli.smoke_block("rss") == 0
    out = capsys.readouterr().out
    assert "not a campaign run" in out
    assert "(fresh child, this row only)" in out
    assert "L19 gzip table" in out
    assert "selected gzip level" in out


# --- The pair check's closed form and pre-registered rules (Phase 2, plan 02-05) ---

_M6_PAIR_M = 5.2  # the closed-form pins below are for m = 5.2 whatever NUT_HEIGHT says


@pytest.mark.parametrize(("clearance", "phase", "volume"), [
    (0.10, math.pi, 12.213),    # the half-pitch control at the middle proof clearance
    (0.05, math.pi, 14.1335),
    (0.0, math.pi, 16.1427),
    (-0.05, math.pi, 18.2374),
    (-0.05, 0.0, 4.3627),       # the sensitivity reading: a matched pose with interference
])
def test_interference_area_reads_the_research_pins_for_m6_within_a_part_in_a_thousand(
        clearance: float, phase: float, volume: float) -> None:
    got = _M6_PAIR_M * maths.interference_area(6.0, 1.0, clearance, phase)
    assert got == pytest.approx(volume, rel=1e-3)


@pytest.mark.parametrize("clearance", maths.PAIR_CLEARANCES)
def test_interference_area_of_a_matched_pose_is_exactly_zero_at_every_proof_clearance(
        clearance: float) -> None:
    assert maths.interference_area(6.0, 1.0, clearance, 0.0) == 0.0


def test_the_control_closed_form_falls_as_the_clearance_grows_and_depends_on_the_size() -> None:
    values = [maths.interference_area(6.0, 1.0, c, math.pi) for c in (-0.05, 0.0, 0.05, 0.10)]
    assert values == sorted(values, reverse=True)
    assert all(v > 0 for v in values)
    assert maths.interference_area(20.0, 2.5, 0.10, math.pi) != maths.interference_area(
        6.0, 1.0, 0.10, math.pi)


def test_the_pair_constants_are_the_pre_registered_ones() -> None:
    assert maths.INTEGRATION_POINTS == 400_000
    assert maths.PAIR_CLEARANCES == (0.05, 0.10, 0.15, 0.20)
    assert maths.DIAGNOSTIC_CLEARANCES == (0.0, -0.05)
    assert (-2 * math.pi / 3, 0.0, 2 * math.pi / 3) == maths.MATCHED_POSES
    assert maths.CONTROL_OFFSET_PITCHES == 0.5
    assert maths.PAIR_REFERENCE_SIZES == ("M2", "M6", "M10", "M20")
    assert verdict_module.PAIR_BAND == 1e-3
    assert verdict_module.EMPTY_MM3 == 1e-6
    assert verdict_module.PAIR_TIMEOUT_S == 600.0


def test_every_matched_pose_and_control_slide_stays_inside_the_rod_pad_of_one_pitch() -> None:
    """Pitfall 2: a slide past the pad shrinks the engaged length and the control volume falls
    below the closed form, silently."""
    for theta in maths.MATCHED_POSES:
        matched = abs(theta) / (2 * math.pi)
        assert matched + maths.CONTROL_OFFSET_PITCHES < 1.0
        assert matched == pytest.approx(1 / 3) or theta == 0.0


def test_the_nut_heights_are_the_r5_values_for_every_size_each_with_a_source_label() -> None:
    assert maths.NUT_HEIGHT == {
        "M2": 1.60, "M2.5": 2.00, "M3": 2.40, "M3.5": 2.80, "M4": 3.20, "M5": 4.70, "M6": 5.20,
        "M7": 5.60, "M8": 6.80, "M10": 8.40, "M12": 10.80, "M14": 12.80, "M16": 14.80,
        "M18": 15.80, "M20": 18.00}
    assert set(maths.NUT_HEIGHT) == set(maths.SIZES)
    assert maths.NUT_HEIGHT["M7"] == pytest.approx(0.8 * 7)  # 0.8 d as a stated input (R5)
    block = Path(maths.__file__).read_text().split("NUT_HEIGHT: dict[str, float] = {")[1]
    entries = block.split("}")[0].strip().splitlines()
    assert len(entries) == len(maths.NUT_HEIGHT)
    # Nothing was read from the standard by the owner, so every label says UNVERIFIED.
    assert all("# " in line and "UNVERIFIED" in line for line in entries)


_POSES = maths.MATCHED_POSES


def _reading(theta: float, offset: float, volume: float) -> PairReading:
    return {"theta": theta, "offset_pitches": offset, "outcome": "built",
            "solids": 0 if volume == 0.0 else 1, "volume": volume, "diag_errors": False,
            "diag_warnings": False, "seconds": 1.5}


def _pair(clearance: float = 0.10, *, size: str = "M6", matched: tuple[float, ...] | None = None,
          controls: tuple[float, ...] = (1.0, 1.0, 1.0), rod_left: bool = False,
          nut_left: bool = False, k: int = 5, nut_factor: float = 1.0,
          with_controls: bool = True, outcome: verdict_module.Outcome = "built") -> PairRecord:
    """A synthetic cell. `controls` are factors of the half-pitch closed form; `matched`
    defaults to the closed form of a matched pose, which is exactly 0 for every c > 0."""
    d, pitch = (float(x) for x in maths.PITCH[size])
    m = maths.NUT_HEIGHT[size]
    expected = m * maths.interference_area(d, pitch, clearance, math.pi)
    at_matched = m * maths.interference_area(d, pitch, clearance, 0.0)
    shown = (at_matched,) * 3 if matched is None else matched
    readings = [_reading(theta, 0.0, v) for theta, v in zip(_POSES, shown, strict=True)]
    if with_controls:
        readings += [_reading(theta, maths.CONTROL_OFFSET_PITCHES, expected * f)
                     for theta, f in zip(_POSES, controls, strict=True)]
    body = (math.pi * d * d - maths.section_area(d, pitch, clearance)) * m
    return {"size": size, "d": d, "pitch": pitch, "m": m, "clearance": clearance,
            "rod_left_hand": rod_left, "nut_left_hand": nut_left, "k": k, "outcome": outcome,
            "error": None if outcome == "built" else f"{outcome} for the test",
            "nut_volume": body * nut_factor if outcome == "built" else None,
            "readings": readings if outcome == "built" else []}


def test_cell_verdict_proves_a_cell_with_empty_matched_poses_and_controls_in_band() -> None:
    assert cell_verdict(_pair()) == ("proven", ())


def test_cell_verdict_proves_controls_within_the_band_on_either_side_of_the_closed_form() -> None:
    assert cell_verdict(_pair(controls=(1.0009, 0.9991, 1.0)))[0] == "proven"


def test_cell_verdict_calls_a_control_just_outside_the_band_inconclusive_naming_it() -> None:
    verdict, reasons = cell_verdict(_pair(controls=(1.0, 1.0011, 1.0)))
    assert verdict == "inconclusive"
    assert any("control" in r and "band" in r for r in reasons)


def test_cell_verdict_calls_a_cell_with_one_empty_control_inconclusive_never_proven() -> None:
    verdict, reasons = cell_verdict(_pair(controls=(1.0, 0.0, 1.0)))
    assert verdict == "inconclusive"
    assert any("control" in r and "empty" in r for r in reasons)


def test_cell_verdict_calls_one_non_empty_matched_pose_violated() -> None:
    verdict, reasons = cell_verdict(_pair(matched=(0.0, 0.5, 0.0)))
    assert verdict == "violated"
    assert any("matched" in r for r in reasons)


def test_cell_verdict_lets_a_non_empty_matched_pose_outrank_a_control_that_did_not_fire() -> None:
    assert cell_verdict(_pair(matched=(0.0, 0.5, 0.0), controls=(0.0, 0.0, 0.0)))[0] == "violated"


@pytest.mark.parametrize("clearance", [0.0, -0.05])
def test_cell_verdict_is_inconclusive_by_definition_at_the_diagnostic_clearances(
        clearance: float) -> None:
    """Even a cell that reads like a perfect proof: at c <= 0 the boolean's answer is what is
    being recorded, not trusted (D-11)."""
    verdict, reasons = cell_verdict(_pair(clearance, matched=(0.0, 0.0, 0.0)))
    assert verdict == "inconclusive"
    assert any("by definition" in r for r in reasons)


@pytest.mark.parametrize("outcome", ["failure", "timeout", "worker_died"])
def test_cell_verdict_calls_a_cell_that_did_not_finish_inconclusive_with_its_outcome_named(
        outcome: verdict_module.Outcome) -> None:
    verdict, reasons = cell_verdict(_pair(outcome=outcome))
    assert verdict == "inconclusive"
    assert any(outcome in r for r in reasons)


def test_cell_verdict_reports_a_control_that_cannot_fire_by_geometry_and_is_inconclusive() -> None:
    """A clearance so large that the closed form is 0: the control could never have fired, so
    reading it as empty proves nothing."""
    cell = _pair(1.0)
    assert closed_control(cell) <= EMPTY_MM3
    verdict, reasons = cell_verdict(cell)
    assert verdict == "inconclusive"
    assert any("control cannot fire by geometry" in r for r in reasons)


def test_cell_verdict_distrusts_a_nut_whose_body_volume_misses_the_closed_form() -> None:
    assert cell_verdict(_pair(nut_factor=1 + 0.5 * verdict_module.T_PASS))[0] == "proven"
    verdict, reasons = cell_verdict(_pair(nut_factor=1.001, matched=(0.5, 0.5, 0.5)))
    assert verdict == "inconclusive"  # even a violation is not believed from a bad nut
    assert any("nut" in r for r in reasons)


def test_cell_verdict_refuses_to_prove_poses_other_than_the_pre_registered_ones() -> None:
    cell = _pair()
    cell["readings"] = [{**r, "theta": r["theta"] + 0.01} for r in cell["readings"]]
    verdict, reasons = cell_verdict(cell)
    assert verdict == "inconclusive"
    assert any("pre-registered" in r for r in reasons)


def _mixed(clearance: float, matched: tuple[float, ...], *,
           outcome: verdict_module.Outcome = "built", k: int = 5) -> PairRecord:
    """A right-hand rod against a left-hand nut: matched poses only, no controls."""
    return _pair(clearance, matched=matched, rod_left=False, nut_left=True, with_controls=False,
                 outcome=outcome, k=k)


def test_cell_verdict_calls_a_mixed_hand_cell_violated_only_if_every_matched_pose_reads() -> None:
    assert cell_verdict(_mixed(0.10, (6.5, 6.9, 6.7)))[0] == "violated"
    verdict, _ = cell_verdict(_mixed(0.10, (6.5, 0.0, 6.7)))
    assert verdict == "inconclusive"  # an empty read at a mixed pair proves nothing either way


def _mixed_at(thetas: tuple[float, ...], volume: float = 6.5) -> PairRecord:
    """A mixed-hand cell with a non-empty reading at each of `thetas` and no other reading."""
    cell = _mixed(0.10, (volume,) * 3)
    cell["readings"] = [_reading(theta, 0.0, volume) for theta in thetas]
    return cell


@pytest.mark.parametrize("thetas", [
    (0.3,),  # one non-empty reading at an arbitrary pose
    _POSES[:2],  # a pre-registered pose missing
    (*_POSES, 0.3),  # a pose chosen after the fact beside the three
    (_POSES[0], _POSES[1], 2.0),  # one of the three replaced
], ids=["arbitrary", "missing", "stray", "replaced"])
def test_a_mixed_hand_cell_read_at_other_poses_than_the_matched_ones_is_inconclusive(
        thetas: tuple[float, ...]) -> None:
    cell = _mixed_at(thetas)
    verdict, reasons = cell_verdict(cell)
    assert verdict == "inconclusive"
    assert any("pre-registered" in r for r in reasons)
    assert not mixed_hand_violated([cell])


def test_a_mixed_hand_cell_read_with_controls_is_inconclusive_not_violated() -> None:
    cell = _mixed_at(_POSES)
    cell["readings"] += [_reading(t, maths.CONTROL_OFFSET_PITCHES, 6.5) for t in _POSES]
    assert cell_verdict(cell)[0] == "inconclusive"


def test_one_mixed_cell_at_the_wrong_poses_stops_a_size_from_reading_violated() -> None:
    good = [_mixed(0.05, (6.5, 6.9, 6.7)), _mixed(0.10, (6.5, 6.9, 6.7))]
    assert mixed_hand_violated(good)
    assert not mixed_hand_violated([*good, _mixed_at((0.3,))])


def test_size_falsifiable_needs_one_proven_cell_at_a_proof_clearance() -> None:
    proven, off = _pair(0.10), _pair(0.15, controls=(1.0, 1.0, 0.0))
    assert size_falsifiable([off, proven])
    assert not size_falsifiable([off, _pair(0.05, controls=(0.0, 0.0, 0.0))])
    assert not size_falsifiable([])
    # c = 0 and c = -0.05 can never be proven, so they never make a size falsifiable.
    diagnostic = [_pair(0.0), _pair(-0.05, matched=(4.0, 4.0, 4.0))]
    assert not size_falsifiable(diagnostic)
    assert size_falsifiable([*diagnostic, proven])


def test_excluded_clearances_are_the_proof_clearances_that_did_not_prove() -> None:
    cells = [_pair(0.05), _pair(0.10, controls=(0.0, 1.0, 1.0)), _pair(0.15),
             _pair(0.20, outcome="timeout"), _pair(0.0), _pair(-0.05)]
    assert excluded_clearances(cells) == (0.10, 0.20)
    assert excluded_clearances([_pair(0.05)]) == ()


def test_mixed_hand_violated_is_true_only_if_every_matched_reading_of_every_cell_is_non_empty(
        ) -> None:
    two = [_mixed(0.05, (6.5, 6.9, 6.7)), _mixed(0.10, (6.5, 6.9, 6.7))]
    assert mixed_hand_violated(two)
    assert not mixed_hand_violated([*two, _mixed(0.15, (6.5, 0.0, 6.7))])
    assert not mixed_hand_violated([*two, _mixed(0.15, (0.0, 0.0, 0.0), outcome="timeout")])
    assert not mixed_hand_violated([])  # no mixed cell is no proof of anything


def test_sensitivity_ok_needs_every_matched_reading_at_minus_005_inside_the_band() -> None:
    near = maths.NUT_HEIGHT["M6"] * maths.interference_area(6.0, 1.0, -0.05, 0.0)
    assert near == pytest.approx(4.3627, rel=1e-3)
    assert sensitivity_ok(_pair(-0.05, with_controls=False))
    assert not sensitivity_ok(_pair(-0.05, matched=(near, near * 1.002, near), with_controls=False))
    assert not sensitivity_ok(_pair(-0.05, matched=(near, 0.0, near), with_controls=False))
    assert not sensitivity_ok(_pair(0.05, with_controls=False))  # not the sensitivity cell
    assert not sensitivity_ok(_pair(-0.05, outcome="timeout"))


def test_variant_rules_accept_two_of_three_controls_while_the_verdict_stays_inconclusive() -> None:
    cell = _pair(controls=(1.0, 0.0, 1.0))
    assert cell_verdict(cell)[0] == "inconclusive"
    rules = variant_rules([cell])
    assert rules["two of three controls fire in band"] == {"M6 right c=0.1 K=5": True}


def test_variant_rules_refuse_a_fired_control_that_is_out_of_band() -> None:
    rules = variant_rules([_pair(controls=(1.0, 1.01, 0.0))])
    assert rules["two of three controls fire in band"] == {"M6 right c=0.1 K=5": False}


def test_variant_rules_can_drop_the_seam_pose_without_touching_the_verdict() -> None:
    """The control at theta = 0 is the false-empty cluster of the research; excluding it is a
    variant, reported, never the verdict (owner ruling R1)."""
    cell = _pair(controls=(1.0, 0.0, 1.0))
    assert variant_rules([cell])["seam pose excluded"] == {"M6 right c=0.1 K=5": True}
    off = _pair(controls=(0.0, 1.0, 1.0))
    assert variant_rules([off])["seam pose excluded"] == {"M6 right c=0.1 K=5": False}
    assert cell_verdict(cell)[0] == "inconclusive"


def test_variant_rules_can_use_the_same_pose_reading_at_minus_005_as_the_control() -> None:
    sensitivity = _pair(-0.05, with_controls=False)
    cell = _pair(0.10, controls=(0.0, 0.0, 0.0))
    rules = variant_rules([cell, sensitivity])
    assert rules["same-pose c=-0.05 reading as the control"] == {"M6 right c=0.1 K=5": True}
    assert cell_verdict(cell)[0] == "inconclusive"
    assert variant_rules([cell])["same-pose c=-0.05 reading as the control"] == {
        "M6 right c=0.1 K=5": False}  # no sensitivity cell, no such control


def test_variant_rules_cover_every_same_hand_proof_cell_and_nothing_else() -> None:
    cells = [_pair(0.05), _pair(0.10, nut_left=True, rod_left=True), _pair(0.0), _pair(-0.05),
             _mixed(0.15, (6.5, 6.9, 6.7))]
    keys = {key for table in variant_rules(cells).values() for key in table}
    assert keys == {"M6 right c=0.05 K=5", "M6 left c=0.1 K=5"}


def _wire(cell: PairRecord) -> str:
    return json.dumps(cell)


def test_a_pair_record_parses_back_to_itself() -> None:
    cell = _pair()
    assert parse_pair_record(_wire(cell)) == cell


def test_a_pair_request_parses_back_to_itself_and_refuses_an_unknown_key() -> None:
    request: PairRequest = {
        "size": "M6", "d": 6.0, "pitch": 1.0, "m": 5.2, "clearance": 0.1, "rod_left_hand": False,
        "nut_left_hand": False, "k": 5, "poses": [(0.0, 0.0), (0.0, 0.5)]}
    assert parse_pair_request(json.dumps(request)) == request
    with pytest.raises(ValueError, match="unknown key 'extra'"):
        parse_pair_request(json.dumps({**request, "extra": 1}))


def test_a_pair_record_with_an_unknown_or_missing_key_is_refused_naming_it() -> None:
    cell = dict(_pair())
    with pytest.raises(ValueError, match="unknown key 'verdict'"):
        parse_pair_record(json.dumps({**cell, "verdict": "proven"}))
    del cell["nut_volume"]
    with pytest.raises(ValueError, match="missing the key 'nut_volume'"):
        parse_pair_record(json.dumps(cell))


def test_a_built_pair_record_needs_its_nut_volume_and_a_finished_cell_needs_no_error() -> None:
    cell = _pair()
    with pytest.raises(ValueError, match="nut_volume"):
        parse_pair_record(json.dumps({**cell, "nut_volume": None}))
    with pytest.raises(ValueError, match="error"):
        parse_pair_record(json.dumps({**cell, "error": "boom"}))


def test_a_cell_that_did_not_finish_carries_an_error_and_a_killed_one_no_readings() -> None:
    cell = _pair(outcome="timeout")
    assert parse_pair_record(_wire(cell)) == cell
    with pytest.raises(ValueError, match="error"):
        parse_pair_record(json.dumps({**cell, "error": None}))
    with pytest.raises(ValueError, match="readings"):
        parse_pair_record(json.dumps({**cell, "readings": _pair()["readings"]}))


def test_a_pair_reading_that_failed_carries_no_measurement_and_a_built_one_all_of_them() -> None:
    cell = _pair()
    bad = {**cell["readings"][0], "volume": None}
    with pytest.raises(ValueError, match="volume"):
        parse_pair_record(json.dumps({**cell, "readings": [bad]}))
    failed = {**cell["readings"][0], "outcome": "failure"}
    with pytest.raises(ValueError, match="failure"):
        parse_pair_record(json.dumps({**cell, "readings": [failed]}))


def test_a_pair_reading_at_an_offset_that_is_neither_matched_nor_control_is_refused() -> None:
    cell = _pair()
    odd = {**cell["readings"][0], "offset_pitches": 0.25}
    with pytest.raises(ValueError, match="offset"):
        parse_pair_record(json.dumps({**cell, "readings": [odd]}))


def test_a_pair_result_row_drops_the_runs_own_verdict_and_keeps_the_record() -> None:
    cell = _pair()
    row = {**cell, "verdict": "proven", "reasons": [], "closed_control": 1.0}
    assert parse_pair_result_row(json.dumps(row)) == cell
    with pytest.raises(ValueError, match="missing the key 'verdict'"):
        parse_pair_result_row(_wire(cell))


def test_a_failed_pair_record_echoes_the_request_and_has_no_number_in_it() -> None:
    request: PairRequest = {
        "size": "M6", "d": 6.0, "pitch": 1.0, "m": 5.2, "clearance": 0.1, "rod_left_hand": False,
        "nut_left_hand": True, "k": 5, "poses": [(0.0, 0.0)]}
    record = failed_pair_record(request, "timeout", "no record within 600 s")
    assert record["outcome"] == "timeout"
    assert record["error"] == "no record within 600 s"
    assert record["nut_volume"] is None
    assert record["readings"] == []
    assert (record["size"], record["nut_left_hand"], record["k"]) == ("M6", True, 5)


# --- The pair builder, the pair block and smoke --pair (Phase 2, plan 02-05) ---


def test_the_turn_count_of_the_rod_piece_is_exact_where_a_float_division_drifts() -> None:
    """M2: (1.6 + 2 * 0.4) / 0.4 is 6 turns, and the float quotient is 6.000000000000001."""
    assert (1.6 + 2 * 0.4) / 0.4 != 6.0
    assert pair._turns(0.4, 1.6) == 6.0
    assert pair._turns(1.0, 5.2) == pytest.approx(7.2)


@pytest.mark.parametrize("size", ["M2", "M20"])
def test_place_keeps_a_right_hand_nut_at_the_widest_pose_with_a_control_inside_the_rod_piece(
        size: str) -> None:
    d, pitch = (float(x) for x in maths.PITCH[size])
    m = maths.NUT_HEIGHT[size]
    rod = pair.rod_piece(d, pitch, m, False, 5)
    placed = pair.place(cq.Solid.makeCylinder(d, m), 2 * math.pi / 3, 0.5, pitch, False)
    box, rod_box = placed.BoundingBox(), rod.BoundingBox()
    assert box.zmin == pytest.approx(5 * pitch / 6)  # P/3 of screw motion plus P/2 of control
    assert box.zmax == pytest.approx(m + 5 * pitch / 6)
    assert (rod_box.zmin, rod_box.zmax) == pytest.approx((-pitch, m + pitch), abs=1e-6)
    pair.check_cover(rod, placed)


def test_place_slides_a_left_hand_nut_the_other_way_and_turns_it_by_theta() -> None:
    blank = cq.Solid.makeCylinder(6.0, 5.2)
    right = pair.place(blank, 2 * math.pi / 3, 0.0, 1.0, False).BoundingBox()
    left = pair.place(blank, 2 * math.pi / 3, 0.0, 1.0, True).BoundingBox()
    assert right.zmin == pytest.approx(1 / 3)
    assert left.zmin == pytest.approx(-1 / 3)
    assert pair.place(blank, 0.0, 0.0, 1.0, False).BoundingBox().zmin == pytest.approx(0.0)


def test_a_placed_nut_the_rod_does_not_cover_is_a_raised_defect_not_a_reading() -> None:
    rod = pair.rod_piece(6.0, 1.0, 5.2, False, 5)
    pair.check_cover(rod, pair.place(cq.Solid.makeCylinder(6.0, 5.2), 0.0, 0.0, 1.0, False))
    for offset in (1.2, -1.2):
        with pytest.raises(ValueError, match="slides past the pad"):
            pair.check_cover(rod, pair.place(cq.Solid.makeCylinder(6.0, 5.2), 0.0, offset, 1.0,
                                             False))


def test_the_nut_is_a_plain_blank_less_the_void_and_its_volume_is_the_closed_form() -> None:
    d, pitch = (float(x) for x in maths.PITCH["M2"])
    m = maths.NUT_HEIGHT["M2"]
    blank = pair.nut(d, pitch, m, 0.10, False, 5)
    body = (math.pi * d * d - maths.section_area(d, pitch, 0.10)) * m
    assert measure.precise_volume(blank) == pytest.approx(body, rel=T_PASS)
    box = blank.BoundingBox()
    assert (box.zmin, box.zmax) == pytest.approx((0.0, m), abs=1e-6)
    assert box.xmax == pytest.approx(d, abs=1e-6)  # radius d: the hex adds nothing (D-13)


def test_common_reads_the_volume_of_an_overlap_and_zero_solids_for_a_disjoint_pair() -> None:
    one = cq.Solid.makeBox(2, 2, 2)
    volume, solids, errors, warnings, seconds = pair.common(
        one, cq.Solid.makeBox(2, 2, 2).translate(cq.Vector(1, 1, 1)))
    assert volume == pytest.approx(1.0)
    assert (solids, errors, warnings) == (1, False, False)
    assert seconds > 0
    apart = pair.common(one, cq.Solid.makeBox(1, 1, 1).translate(cq.Vector(5, 5, 5)))
    assert apart[:2] == (0.0, 0)


def test_a_child_that_read_a_pose_comes_back_with_exit_0_the_way_the_worker_ends() -> None:
    """The boolean and its filler must outlive `common`: freed with it, the process dies with a
    segfault (RESEARCH Pitfall 4), which the worker meets after answering and before its
    `os._exit(0)`. Read as the worker reads, in a fresh process, and the exit code is the
    behaviour: with the hold dropped this child dies on signal 11 (checked when it was written)."""
    code = "\n".join([
        "import gc, os", "import cadquery as cq", "from bench.thread_spike import pair",
        "box = cq.Solid.makeBox(2, 2, 2)",
        "print(pair.common(box, cq.Solid.makeBox(2, 2, 2).translate(cq.Vector(1, 1, 1)))[:2],"
        " flush=True)",
        "print(pair.common(box, cq.Solid.makeBox(1, 1, 1).translate(cq.Vector(5, 5, 5)))[:2],"
        " flush=True)",
        "gc.collect()", "os._exit(0)"])
    done = subprocess.run([sys.executable, "-c", code], cwd=Path(__file__).resolve().parents[1],
                          capture_output=True, text=True, timeout=120, check=False)
    assert done.returncode == 0, done.stderr
    overlap, apart = done.stdout.splitlines()
    assert overlap.startswith("(1.0")
    assert overlap.endswith(", 1)")
    assert apart == "(0.0, 0)"


def _m2_request(poses: list[tuple[float, float]], *, clearance: float = 0.10) -> PairRequest:
    d, pitch = (float(x) for x in maths.PITCH["M2"])
    return {"size": "M2", "d": d, "pitch": pitch, "m": maths.NUT_HEIGHT["M2"],
            "clearance": clearance, "rod_left_hand": False, "nut_left_hand": False, "k": 5,
            "poses": poses}


def test_a_worker_reads_the_requested_pose_of_a_real_cell_and_judges_nothing() -> None:
    """M2, c = 0.10, one control a half pitch off the widest matched pose (not theta = pi: its
    control slides the nut a whole pitch, the pad's edge), through a real child: the record
    carries the nut's volume and a built reading at the closed form. The matched poses cost
    about 12 s each, so `smoke --pair` is where those are read for real."""
    cell = Worker()
    try:
        record = cell.run_pair(_m2_request([(2 * math.pi / 3, 0.5)]),
                               verdict_module.PAIR_TIMEOUT_S)
    finally:
        cell.close()
    assert record["outcome"] == "built"
    assert record["nut_volume"] == pytest.approx(
        (math.pi * 4.0 - maths.section_area(2.0, 0.4, 0.10)) * 1.6, rel=T_PASS)
    (control,) = record["readings"]
    assert (control["theta"], control["offset_pitches"]) == (2 * math.pi / 3, 0.5)
    assert control["solids"] == 1
    assert control["volume"] is not None
    assert control["volume"] == pytest.approx(closed_control(record), rel=PAIR_BAND)
    assert (control["diag_errors"], control["diag_warnings"]) == (False, False)


def test_an_exception_at_a_pose_ends_the_cell_as_a_failure_that_keeps_the_readings_so_far(
        monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    def common(a: cq.Shape, b: cq.Shape) -> tuple[float, int, bool, bool, float]:
        calls.append(1)
        if len(calls) == 2:
            raise RuntimeError("the boolean raised")
        return 0.0, 0, False, False, 0.5

    monkeypatch.setattr(pair, "common", common)
    record = worker.run_pair(_m2_request([(0.0, 0.0), (0.0, 0.5), (math.pi, 0.5)]))
    assert record["outcome"] == "failure"
    assert record["error"] == "RuntimeError: the boolean raised"
    assert record["nut_volume"] is not None  # the nut was built before the boolean raised
    assert [r["outcome"] for r in record["readings"]] == ["built", "failure"]
    assert record["readings"][1]["volume"] is None
    assert len(calls) == 2  # the third pose was never read


def test_a_pose_the_rod_does_not_cover_is_a_failure_naming_the_pad_never_a_reading() -> None:
    record = worker.run_pair(_m2_request([(0.0, 1.5)]))
    assert record["outcome"] == "failure"
    assert record["error"] is not None
    assert "slides past the pad" in record["error"]
    assert [r["outcome"] for r in record["readings"]] == ["failure"]


def test_a_cell_whose_build_raises_has_no_readings_and_no_nut_volume() -> None:
    bad = _m2_request([(0.0, 0.0)])
    record = worker.run_pair({**bad, "d": 1e-9, "clearance": 5.0})
    assert record["outcome"] == "failure"
    assert record["readings"] == []
    assert record["nut_volume"] is None


def test_a_pair_request_is_told_from_a_row_request_by_its_poses() -> None:
    assert worker._is_pair(json.dumps(_m2_request([(0.0, 0.0)])))
    assert not worker._is_pair(json.dumps(_REQUEST))


def test_a_worker_that_dies_or_stalls_on_a_pair_cell_is_one_cell_with_no_reading_in_it() -> None:
    request = _m2_request([(0.0, 0.0)])
    dying = Worker(argv=[sys.executable, "-c", "import os; os._exit(3)"])
    stalled = Worker(argv=[sys.executable, "-c", "import time; time.sleep(60)"])
    babbling = Worker(argv=[sys.executable, "-c",
                            "import sys; sys.stdin.readline(); print('not json')"])
    try:
        died = dying.run_pair(request, 30.0)
        late = stalled.run_pair(request, 0.5)
        garbled = babbling.run_pair(request, 30.0)
    finally:
        for w in (dying, stalled, babbling):
            w.close()
    assert died["outcome"] == "worker_died"
    assert died["error"] is not None
    assert "return code 3" in died["error"]
    assert (late["outcome"], late["error"]) == ("timeout", "no record within 0.5 s")
    assert garbled["outcome"] == "failure"
    assert garbled["error"] is not None
    assert "unreadable worker output" in garbled["error"]
    for record in (died, late, garbled):
        assert (record["nut_volume"], record["readings"]) == (None, [])
        assert (record["size"], record["clearance"], record["k"]) == ("M2", 0.10, 5)


class _FakePairWorker(_FakeWorker):
    """Answers every pair request in-process: a cell as the closed form would have it, with the
    seam control empty (the research's false-empty) when `seam_false_empty`."""

    def __init__(self, seam_false_empty: bool = False, **_: object) -> None:
        super().__init__()
        self.cells: list[PairRequest] = []
        self.seam_false_empty = seam_false_empty

    def run_pair(self, request: PairRequest, timeout_s: float) -> PairRecord:
        del timeout_s
        self.cells.append(request)
        controls = (1.0, 0.0, 1.0) if self.seam_false_empty else (1.0, 1.0, 1.0)
        return _pair(request["clearance"], size=request["size"], k=request["k"],
                     rod_left=request["rod_left_hand"], nut_left=request["nut_left_hand"],
                     controls=controls, with_controls=len(request["poses"]) == 6)


class _RecordingPairWorker(_FakePairWorker):
    """Records the cells it is asked for and answers each as a failed one: structure tests need
    no closed form, which costs about 0.35 s per (size, clearance)."""

    def run_pair(self, request: PairRequest, timeout_s: float) -> PairRecord:
        del timeout_s
        self.cells.append(request)
        return failed_pair_record(request, "failure", "recorded only")


def _run_pair_block(k: int, smoke: bool = False) -> list[PairRequest]:
    fake = _RecordingPairWorker()
    spike_cli._BLOCKS["pair"](spike_cli.Campaign(fake, True, None), k, smoke)
    return fake.cells


def test_the_pair_block_is_per_size_two_hands_six_clearances_and_four_mixed_cells() -> None:
    cells = [c for c in _run_pair_block(5) if c["k"] == 5]
    assert len(cells) == 15 * (2 * 6 + 4)
    m6 = [c for c in cells if c["size"] == "M6"]
    same = [c for c in m6 if c["rod_left_hand"] == c["nut_left_hand"]]
    assert sorted((c["rod_left_hand"], c["clearance"]) for c in same) == sorted(
        (left, c) for left in (False, True) for c in (0.0, -0.05, 0.05, 0.10, 0.15, 0.20))
    assert all(len(c["poses"]) == 6 for c in same)
    assert [p[0] for p in same[0]["poses"]] == list(maths.MATCHED_POSES) * 2
    assert [p[1] for p in same[0]["poses"]] == [0.0] * 3 + [0.5] * 3
    mixed = [c for c in m6 if c["rod_left_hand"] != c["nut_left_hand"]]
    assert sorted(c["clearance"] for c in mixed) == [0.05, 0.10, 0.15, 0.20]
    assert all((c["rod_left_hand"], c["nut_left_hand"]) == (False, True) for c in mixed)
    assert all(len(c["poses"]) == 3 and {p[1] for p in c["poses"]} == {0.0} for c in mixed)
    assert {c["m"] for c in m6} == {5.2}
    assert {(c["d"], c["pitch"]) for c in m6} == {(6.0, 1.0)}


def test_the_pair_block_reads_the_two_other_k_values_on_the_reference_sizes_right_hand() -> None:
    reference = [c for c in _run_pair_block(5) if c["k"] != 5]
    assert len(reference) == 4 * 2 * 4
    assert {c["size"] for c in reference} == set(maths.PAIR_REFERENCE_SIZES)
    assert {c["k"] for c in reference} == {3, 10}
    assert all(not c["rod_left_hand"] and not c["nut_left_hand"] for c in reference)
    assert {c["clearance"] for c in reference} == set(maths.PAIR_CLEARANCES)
    # K is the locked one wherever it was locked: with 3 locked, the references are 5 and 10.
    assert {c["k"] for c in _run_pair_block(3) if c["k"] != 3} == {5, 10}


def test_the_pair_smoke_block_is_one_m6_right_hand_cell_at_c_010() -> None:
    (cell,) = _run_pair_block(5, smoke=True)
    assert (cell["size"], cell["clearance"], cell["k"], cell["rod_left_hand"]) == (
        "M6", 0.10, 5, False)
    assert len(cell["poses"]) == 6


def test_a_pair_cell_is_streamed_with_the_verdict_this_run_drew_and_parses_back(
        tmp_path: Path) -> None:
    with (tmp_path / "pair.jsonl").open("w") as sink:
        c = spike_cli.Campaign(_FakePairWorker(), True, sink)
        c.measure_pair(_m2_request([(0.0, 0.0)]))
    (line,) = (tmp_path / "pair.jsonl").read_text().splitlines()
    row = json.loads(line)
    assert row["verdict"] == "inconclusive"
    assert row["closed_control"] == pytest.approx(closed_control(c.pairs[0]))
    assert parse_pair_result_row(line) == c.pairs[0]


def test_smoke_pair_prints_six_readings_the_closed_form_and_the_cell_verdict(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(spike_cli, "Worker", lambda: _FakePairWorker(seam_false_empty=True))
    assert spike_cli.smoke_pair() == 0  # a false-empty control is a measured outcome, not a defect
    out = capsys.readouterr().out
    assert "not a campaign run" in out
    assert out.count("| matched |") == 3
    assert out.count("| control |") == 3
    assert "- control closed form: 12.213" in out
    assert "- cell verdict: inconclusive" in out
    assert "control at theta +0.0000 reads empty" in out


@pytest.mark.parametrize("outcome", ["failure", "timeout", "worker_died"])
def test_smoke_pair_exits_1_when_the_cell_did_not_finish(
        outcome: verdict_module.Outcome, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    class Failing(_FakePairWorker):
        def run_pair(self, request: PairRequest, timeout_s: float) -> PairRecord:
            del timeout_s
            return failed_pair_record(request, outcome, "it did not finish")

    monkeypatch.setattr(spike_cli, "Worker", Failing)
    assert spike_cli.smoke_pair() == 1
    assert f"cell {outcome}: it did not finish" in capsys.readouterr().out
    assert spike_cli.main(["smoke", "--pair"]) == 1


def test_smoke_pair_is_reachable_from_the_command_line_and_not_beside_a_block(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(spike_cli, "Worker", _FakePairWorker)
    assert spike_cli.main(["smoke", "--pair"]) == 0
    assert spike_cli.main(["smoke", "--block", "pair"]) == 0
    assert capsys.readouterr().out.count("- cell verdict: proven") == 2
    with pytest.raises(SystemExit):
        spike_cli.main(["smoke", "--pair", "--block", "grid"])


def _pair_cells() -> list[PairRecord]:
    """M6 right and left: c = 0.10 proven, c = 0.05 with the seam control empty, the sensitivity
    cell, and the mixed pair violated at c = 0.10; K = 3 reference rows beside them."""
    return [
        _pair(0.10), _pair(0.05, controls=(1.0, 0.0, 1.0)), _pair(-0.05, with_controls=False),
        _pair(0.10, rod_left=True, nut_left=True),
        _mixed(0.10, (6.5, 6.9, 6.7)),
        _pair(0.10, k=3, controls=(0.0, 1.0, 1.0)),
    ]


def test_the_pair_section_renders_rows_falsifiability_mixed_sensitivity_and_the_variants() -> None:
    text = "\n".join(spike_cli.pair_section(_pair_cells(), 5))
    assert "#### M6 right hand (m = 5.2 mm, UNVERIFIED)" in text
    assert "#### M6 left hand" in text
    # every volume read, the control's closed form, the solids, the diagnostics, the verdict
    assert ("| 0.1 | 0/0/0 | 12.213/12.213/12.213 | 12.213 | 0/0/0 ; 1/1/1 | "
            "errors 0 of 6, warnings 0 of 6 | proven |") in text
    assert ("| 0.05 | 0/0/0 | 14.1335/0/14.1335 | 14.1335 | 0/0/0 ; 1/0/1 | "
            "errors 0 of 6, warnings 0 of 6 | inconclusive |") in text
    assert "| -0.05 | 4.36267/4.36267/4.36267 | n/a |" in text
    assert "- M6 right c=0.05: inconclusive: control at theta +0.0000 reads empty" in text
    assert "- M6: falsifiable on both hands" in text
    assert "- M6 right: excluded clearances 0.05" in text
    assert "- M6 left: excluded clearances none" in text
    assert "- M6: mixed-hand pair read violated at every matched pose: yes (1 mixed cells)" in text
    assert "- M6 right: sensitivity (c = -0.05) ok" in text
    assert "| M6 | 3 | n/a | inconclusive | n/a | n/a |" in text  # the K = 3 reference row


def test_the_variant_table_sits_beside_the_verdict_and_says_it_never_changes_it() -> None:
    text = "\n".join(spike_cli.pair_section(_pair_cells(), 5))
    heading, table = text.split("#### Variant rules (reported, never the verdict)")
    assert "never feed it" in table
    assert "| Cell | D-14 verdict | two of three controls fire in band | seam pose excluded | " \
           "same-pose c=-0.05 reading as the control |" in table
    assert "| M6 right c=0.05 K=5 | inconclusive | yes | yes | yes |" in table
    assert "| M6 right c=0.1 K=5 | proven | yes | yes | yes |" in table
    assert "| M6 left c=0.1 K=5 | proven | yes | yes | NO |" in table  # no c = -0.05 cell
    assert "K=3" not in table  # a reference row is not a variant row
    assert heading.count("#### ") >= 3


def test_a_size_without_a_proven_cell_on_both_hands_fires_the_escape_naming_the_hand() -> None:
    cells = [_pair(0.10), _pair(0.10, rod_left=True, nut_left=True, controls=(0.0, 0.0, 0.0)),
             _mixed(0.10, (6.5, 6.9, 6.7))]
    assert spike_cli.pair_escapes(cells, 5, ["M6"]) == (
        "pair: not falsifiable for size M6 (left hand)",)
    text = "\n".join(spike_cli.pair_section(cells, 5))
    assert "- not falsifiable for size M6 (left hand): the escape clause fires" in text


def test_a_size_whose_mixed_pair_did_not_read_violated_or_was_never_read_fires_escape() -> None:
    both = [_pair(0.10), _pair(0.10, rod_left=True, nut_left=True)]
    reasons = spike_cli.pair_escapes([*both, _mixed(0.10, (6.5, 0.0, 6.7))], 5, ["M6"])
    assert reasons == ("pair: size M6: the mixed-hand pair did not read violated at every "
                       "matched pose",)
    assert spike_cli.pair_escapes(both, 5, ["M6"]) == reasons
    assert len(spike_cli.pair_escapes([], 5, ["M6", "M8"])) == 4  # a size never read is both


def test_a_reference_k_cell_never_makes_a_size_falsifiable() -> None:
    cells = [_pair(0.10, k=3), _pair(0.10, k=3, rod_left=True, nut_left=True),
             _mixed(0.10, (6.5, 6.9, 6.7))]
    assert len(spike_cli.pair_escapes(cells, 5, ["M6"])) == 1  # the K = 5 cells: only the mixed one


def test_the_pair_report_is_the_header_the_section_and_the_end_reading_and_refuses_an_empty_run(
        ) -> None:
    end = Reading("2026-10-08T10:00:00+00:00", 2.5)
    text = spike_cli.pair_report(["## Thread spike run x"], _pair_cells(), 5, end)
    assert text.startswith("## Thread spike run x")
    assert text.endswith("load1 2.50 read 2026-10-08T10:00:00+00:00 (includes this run's own load)")
    with pytest.raises(ValueError, match="no cells"):
        spike_cli.pair_report([], [], 5, end)


def test_a_pair_run_streams_its_header_then_one_cell_per_line_and_reports_the_section(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _held(monkeypatch)
    monkeypatch.setattr(spike_cli, "Worker", _FakePairWorker)
    _m6_only(monkeypatch)
    ksweep = _m6_ksweep()
    _write_run(tmp_path / "sweep.jsonl", "ksweep", ksweep)

    def one_cell(c: spike_cli.Campaign, k: int, smoke: bool) -> None:
        c.measure_pair(_pair_request_for_test(k))

    monkeypatch.setitem(spike_cli._BLOCKS, "pair", one_cell)
    assert spike_cli.run_block("pair", "box-pair", "sweep", results_dir=tmp_path) == 0
    lines = (tmp_path / "box-pair.jsonl").read_text().splitlines()
    assert len(lines) == 2
    header = parse_header(lines[0])
    assert (header["block"], header["k"]) == ("pair", 3)
    assert parse_pair_result_row(lines[1])["k"] == 3
    assert "#### M6 right hand" in capsys.readouterr().out
    assert "#### M6 right hand" in (tmp_path / "box-pair.md").read_text()


def _pair_request_for_test(k: int) -> PairRequest:
    return {"size": "M6", "d": 6.0, "pitch": 1.0, "m": 5.2, "clearance": 0.10,
            "rod_left_hand": False, "nut_left_hand": False, "k": k,
            "poses": [(t, 0.0) for t in maths.MATCHED_POSES]
            + [(t, 0.5) for t in maths.MATCHED_POSES]}


# --- The pair run in the verdict and the campaign driver ---


def test_a_clean_campaign_reads_the_pair_run_and_prints_its_section_beside_the_verdict(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path)
    assert _verdict("c1", tmp_path) == 0
    out = capsys.readouterr().out
    assert "pair (run `c1-pair`, decisive)" in out
    assert "escape clause: not fired" in out
    section = out.split("### Pair check (D-11 to D-14)")[1]
    assert "Locked K = 3" in section
    assert "- M6: falsifiable on both hands" in section
    assert "#### Variant rules (reported, never the verdict)" in section


def test_a_pair_cell_stored_as_proven_is_judged_again_from_its_readings(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path, pair_cells=[  # a control reads empty at every right-hand proof c
        _pair(c, controls=(0.0, 1.0, 1.0), k=_LOCKED_K) for c in maths.PAIR_CLEARANCES])
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "escape clause: FIRED" in out
    assert "- pair: not falsifiable for size M6 (right hand)" in out


def test_a_mixed_hand_pair_that_did_not_read_violated_fires_the_escape_clause(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path, pair_cells=[_mixed(0.10, (6.5, 0.0, 6.7), k=_LOCKED_K)])
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "- pair: size M6: the mixed-hand pair did not read violated" in out
    assert "mixed-hand pair read violated at every matched pose: NO" in out


def test_a_campaign_without_the_pair_run_is_never_a_pass(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path, skip=("pair",))
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "Blocks missing: pair" in out
    assert "pair: not recorded" in out


def test_a_reference_k_cell_is_printed_beside_the_verdict_and_never_changes_it(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path, pair_cells=[_pair(0.15, k=5, controls=(0.0, 0.0, 0.0))])
    assert _verdict("c1", tmp_path) == 0
    out = capsys.readouterr().out
    assert "| M6 | 5 | proven | proven | inconclusive | proven |" in out
    assert "| M6 | 10 | proven | proven | proven | proven |" in out


def test_a_pair_run_whose_header_has_no_k_is_reported_not_read_and_never_passes(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Like any block whose header names no K: listed under the blocks not read with the rest of
    the verdict printed, and exit 1, never a refusal before the report."""
    _full_campaign(tmp_path)
    _write_pair_run(tmp_path / "c1-pair.jsonl", _clean_pair_cells(), k=None)
    assert _verdict("c1", tmp_path) == 1
    out = capsys.readouterr().out
    assert "Blocks not read: pair" in out
    assert "  - pair: its header carries no K, so the cells it should hold cannot be named" in out
    assert "pair: not read" in out.split("### Pair check (D-11 to D-14)")[1]
    assert "**Verdict:** not a pass" in out


def test_a_pair_run_cell_with_an_unknown_key_is_refused_not_read(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _full_campaign(tmp_path)
    path = tmp_path / "c1-pair.jsonl"
    path.write_text(path.read_text() + json.dumps(
        {**_pair(), "verdict": "proven", "reasons": [], "closed_control": 1.0,
         "hand_edited": True}) + "\n")
    assert _verdict("c1", tmp_path) == 2
    assert "unknown key 'hand_edited'" in capsys.readouterr().err


# --- The whole campaign as one guarded command (Phase 2, plan 02-05) ---


def test_the_campaign_runs_the_blocks_in_protocol_order_and_every_block_is_runnable() -> None:
    assert spike_cli.CAMPAIGN_BLOCKS == (
        "ksweep", "grid", "frontier", "ladder", "trim", "controls", "rss", "pair", "container")
    assert set(spike_cli.CAMPAIGN_BLOCKS) == set(spike_cli._BLOCKS)


def _forbid_the_guard_and_every_block(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*args: object, **kwargs: object) -> None:
        raise AssertionError("a refused campaign reached the guard or a block")

    monkeypatch.setattr(spike_cli, "read_guard", boom)
    monkeypatch.setattr(spike_cli, "run_block", boom)


@pytest.mark.parametrize("prefix", ["a" * 51, "../x", "A", ""])
def test_a_prefix_that_is_not_a_run_id_or_is_over_50_characters_is_refused_before_anything(
        prefix: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _forbid_the_guard_and_every_block(monkeypatch)
    assert spike_cli.run_campaign(prefix, results_dir=tmp_path) == 2
    assert "at most 50 characters" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_a_50_character_prefix_still_makes_a_run_id_of_every_block() -> None:
    prefix = "a" * spike_cli.MAX_PREFIX
    assert all(spike_cli.RUN_ID.fullmatch(f"{prefix}-{b}") for b in spike_cli.CAMPAIGN_BLOCKS)


@pytest.mark.parametrize("taken", ["c1-grid.jsonl", "c1-container.jsonl", "c1-campaign.md"])
def test_one_recorded_block_refuses_the_whole_campaign_before_anything_runs_and_is_left_intact(
        taken: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _forbid_the_guard_and_every_block(monkeypatch)
    (tmp_path / taken).write_text("what the first run measured\n")
    assert spike_cli.run_campaign("c1", results_dir=tmp_path) == 2
    err = capsys.readouterr().err
    assert taken in err
    assert "already recorded" in err
    assert (tmp_path / taken).read_text() == "what the first run measured\n"
    assert [p.name for p in tmp_path.iterdir()] == [taken]


def _forbid_a_block(*args: object, **kwargs: object) -> int:
    pytest.fail("a block ran")


def test_a_refused_protocol_guard_refuses_the_campaign_with_nothing_written(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    refused = spike_cli.GuardFacts(GuardResult(False, ("it has not landed",)), "none", "none", "h")
    _guard_says(monkeypatch, refused)
    monkeypatch.setattr(spike_cli, "run_block", _forbid_a_block)
    target = tmp_path / "results"
    assert spike_cli.run_campaign("c1", results_dir=target) == 2
    assert "protocol guard: refused -- it has not landed" in capsys.readouterr().err
    assert not target.exists()


class _BlockLog:
    """A stand-in for `run_block`: records each call, writes the K-sweep record the others must
    read their K from, and resolves K the way the real one does, through `_locked_k`."""

    def __init__(self, results_dir: Path, *, refuse: dict[str, str] | None = None,
                 crash: tuple[str, ...] = ()) -> None:
        self.dir = results_dir
        self.refuse = refuse or {}
        self.crash = crash
        self.calls: list[tuple[str, str, str | None, str | None]] = []
        self.k: dict[str, int] = {}

    def __call__(self, block: str, run_id: str, k_from: str | None, *,
                 results_dir: Path = Path("unused"), env: object = None,
                 frontier_from: str | None = None) -> int:
        del env
        assert results_dir == self.dir
        self.calls.append((block, run_id, k_from, frontier_from))
        if block in self.refuse:
            print(f"refused: {self.refuse[block]}", file=sys.stderr)
            return 2
        if block == "ksweep":
            _write_run(self.dir / f"{run_id}.jsonl", "ksweep", _m6_ksweep())
        else:
            assert k_from is not None
            self.k[block] = spike_cli._locked_k(k_from, self.dir)[0]
            (self.dir / f"{run_id}.jsonl").write_text("partial\n")
        if block in self.crash:
            raise RuntimeError("the kernel fell over")
        print(f"## block {block}")
        return 0


def _campaign_goes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, verdict_code: int = 0, *,
                   refuse: dict[str, str] | None = None, crash: tuple[str, ...] = ()) -> _BlockLog:
    facts = spike_cli.GuardFacts(GuardResult(True, ()), "b" * 40, "c" * 40, "a" * 40)
    _guard_says(monkeypatch, facts)
    _m6_only(monkeypatch)
    log = _BlockLog(tmp_path, refuse=refuse, crash=crash)
    monkeypatch.setattr(spike_cli, "run_block", log)

    def verdict(prefix: str, *, results_dir: Path) -> int:
        print(f"## verdict over {prefix} in {results_dir.name}")
        return verdict_code

    monkeypatch.setattr(spike_cli, "verdict_campaign", verdict)
    return log


def test_every_block_runs_as_prefix_dash_block_with_k_from_the_ksweep_record_never_a_flag(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log = _campaign_goes(monkeypatch, tmp_path)
    assert spike_cli.run_campaign("c1", results_dir=tmp_path) == 0
    assert [c[0] for c in log.calls] == list(spike_cli.CAMPAIGN_BLOCKS)
    assert [c[1] for c in log.calls] == [f"c1-{b}" for b in spike_cli.CAMPAIGN_BLOCKS]
    # No block after the sweep is handed a K: each is handed the sweep's run id and reads the K
    # the rule selects from that record (3: the fewest triangles in the synthetic sweep).
    assert [c[2] for c in log.calls] == [None] + ["c1-ksweep"] * 8
    assert set(log.k) == set(spike_cli.CAMPAIGN_BLOCKS) - {"ksweep"}
    assert set(log.k.values()) == {3}
    assert [c[3] for c in log.calls if c[3] is not None] == ["c1-frontier"]
    assert [c[0] for c in log.calls if c[3] is not None] == ["rss"]


def test_the_campaign_log_names_every_block_then_the_verdict_and_ends_with_campaign_finished(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _campaign_goes(monkeypatch, tmp_path)
    assert spike_cli.run_campaign("c1", results_dir=tmp_path) == 0
    text = (tmp_path / "c1-campaign.md").read_text()
    assert text.splitlines()[0] == "## Thread spike campaign c1"
    assert "- ksweep: ran as `c1-ksweep`" in text
    assert "- container: ran as `c1-container`" in text
    assert "## verdict over c1 in " in text
    assert text.endswith("\ncampaign finished\n")
    assert text.index("- container: ran") < text.index("## verdict over")
    out = capsys.readouterr().out
    assert "## verdict over c1" in out  # the verdict is printed as well as appended
    assert out.rstrip().endswith("campaign finished")


@pytest.mark.parametrize("code", [0, 1, 2])
def test_the_campaign_exits_with_the_verdicts_code(
        code: int, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _campaign_goes(monkeypatch, tmp_path, verdict_code=code)
    assert spike_cli.run_campaign("c1", results_dir=tmp_path) == code
    assert (tmp_path / "c1-campaign.md").read_text().endswith("campaign finished\n")


def test_a_block_that_refuses_to_start_is_logged_with_its_reason_and_the_rest_still_run(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log = _campaign_goes(monkeypatch, tmp_path, refuse={
        "controls": "SCREW_SPIKE_CQW is not set", "container": "docker is not installed"})
    assert spike_cli.run_campaign("c1", results_dir=tmp_path) == 0
    assert [c[0] for c in log.calls] == list(spike_cli.CAMPAIGN_BLOCKS)
    text = (tmp_path / "c1-campaign.md").read_text()
    assert "- controls: refused to start (exit 2): refused: SCREW_SPIKE_CQW is not set" in text
    assert "- container: refused to start (exit 2): refused: docker is not installed" in text
    assert "- pair: ran as `c1-pair`" in text


def test_a_block_that_crashes_keeps_its_partial_record_and_is_logged_as_interrupted(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _campaign_goes(monkeypatch, tmp_path, crash=("grid",))
    assert spike_cli.run_campaign("c1", results_dir=tmp_path) == 0
    text = (tmp_path / "c1-campaign.md").read_text()
    assert ("- grid: interrupted (RuntimeError: the kernel fell over); its partial record "
            "`c1-grid.jsonl` is kept and is never re-run") in text
    assert (tmp_path / "c1-grid.jsonl").read_text() == "partial\n"
    assert "- frontier: ran as `c1-frontier`" in text  # the rest of the campaign went on


def test_a_sweep_that_did_not_finish_stops_every_block_that_needs_its_k(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log = _campaign_goes(monkeypatch, tmp_path, refuse={"ksweep": "the host is busy"})
    assert spike_cli.run_campaign("c1", results_dir=tmp_path) == 0
    assert [c[0] for c in log.calls] == ["ksweep"]  # a K from half a sweep is not the sweep's K
    text = (tmp_path / "c1-campaign.md").read_text()
    assert "- grid: skipped, needs c1-ksweep, which did not complete" in text
    assert "- container: skipped, needs c1-ksweep, which did not complete" in text


def test_a_frontier_that_did_not_finish_skips_the_rss_block_that_measures_its_terminal_rows(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log = _campaign_goes(monkeypatch, tmp_path, crash=("frontier",))
    assert spike_cli.run_campaign("c1", results_dir=tmp_path) == 0
    assert "rss" not in [c[0] for c in log.calls]
    assert "- rss: skipped, needs c1-frontier, which did not complete" in (
        tmp_path / "c1-campaign.md").read_text()


def test_the_campaign_subcommand_takes_a_run_id_prefix_and_returns_the_campaigns_code(
        monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []

    def run_campaign(prefix: str) -> int:
        seen.append(prefix)
        return 1

    monkeypatch.setattr(spike_cli, "run_campaign", run_campaign)
    assert spike_cli.main(["campaign", "--run-id", "plan-check"]) == 1
    assert seen == ["plan-check"]
    with pytest.raises(SystemExit):
        spike_cli.main(["campaign"])


# The protocol's inputs are pre-registered in 02-SPIKE.md (D-16, D-19). These two tests bind the
# text to the code, so after PR 1 lands no constant can move, and none can be added, without the
# protocol changing in the same PR: a visible diff that post-dates the landed one.
_PROTOCOL_TEXT_MODULES = {
    "quiet": quiet_module, "maths": maths, "verdict": verdict_module, "helical": helical,
    "measure": measure, "cli": spike_cli,
    "runner": importlib.import_module("bench.thread_spike.runner"),
}
# The modules whose every public constant the protocol must list: all seven, the driver and the
# container runner included, so a policy constant of the driver cannot sit outside the table
# unnoticed. A driver constant that is no protocol input (a dispatch table, the smoke subset) is
# private, with its reason beside it, not exempted here.
_PROTOCOL_COMPLETE_MODULES = ("quiet", "maths", "verdict", "helical", "measure", "cli", "runner")
_PROTOCOL_HEADINGS = ("Environment", "Method", "Protocol inputs", "Rules", "Predictions",
                      "Escape clause")
_INPUT_ROW = re.compile(
    r"^\| `(?P<module>[a-z]+)\.(?P<name>[A-Z][A-Z0-9_]*)` \| `(?P<value>.+?)` \| ")
_PITCH_ROW = re.compile(r"^\| (?P<size>M[0-9.]+) \| (?P<d>[0-9/]+) \| (?P<pitch>[0-9/]+) \|$")
_NUT_ROW = re.compile(r"^\| (?P<size>M[0-9.]+) \| (?P<m>[0-9.]+) \| .+ \|$")


def _protocol_head() -> str:
    text = (Path(__file__).resolve().parents[1] / verdict_module.PROTOCOL_PATH).read_text()
    head = verdict_module.before_results(text)
    assert head is not None, f"{verdict_module.PROTOCOL_PATH} has no results heading"
    return head


def _defined_constants(module: object) -> set[str]:
    """Public ALL_CAPS names a module assigns at its top level, read from its source, so a name it
    merely imports (verdict re-uses maths.PITCH; quiet imports datetime's UTC) is not its own."""
    path = getattr(module, "__file__", None)
    assert isinstance(path, str)
    names: set[str] = set()
    for node in ast.parse(Path(path).read_text()).body:
        targets = (node.targets if isinstance(node, ast.Assign)
                   else [node.target] if isinstance(node, ast.AnnAssign) else [])
        names.update(t.id for t in targets
                     if isinstance(t, ast.Name) and t.id.isupper() and not t.id.startswith("_"))
    return names


def test_the_protocol_pre_registers_every_constant_the_harness_uses() -> None:
    """Every public ALL_CAPS constant of the seven modules has a row, and every row's value is the
    code's. A compiled pattern is registered by its text and a directory by its path in the
    repository: the values a reader can check without running the code."""
    head = _protocol_head()
    rows = [m for m in map(_INPUT_ROW.match, head.split("\n")) if m]
    listed = [f"{m['module']}.{m['name']}" for m in rows]
    assert len(listed) == len(set(listed)), "a constant is listed twice in the protocol"
    assert rows, "no constant rows were parsed: the table's shape changed"

    wrong: list[str] = []
    for m in rows:
        module = _PROTOCOL_TEXT_MODULES.get(m["module"])
        if module is None or not hasattr(module, m["name"]):
            wrong.append(f"{m['module']}.{m['name']} names no constant of the harness")
            continue
        registered = ast.literal_eval(m["value"])
        actual = getattr(module, m["name"])
        if isinstance(actual, re.Pattern):
            actual = actual.pattern
        elif isinstance(actual, Path):
            actual = actual.relative_to(Path(__file__).resolve().parents[1]).as_posix()
        if registered != actual:
            wrong.append(f"{m['module']}.{m['name']}: protocol {registered!r}, code {actual!r}")

    pitch_part, _, nut_part = head.partition("### NUT_HEIGHT")
    pitch_part = pitch_part.partition("### PITCH")[2]
    pitch = {m["size"]: (Fraction(m["d"]), Fraction(m["pitch"]))
             for m in map(_PITCH_ROW.match, pitch_part.split("\n")) if m}
    nut = {m["size"]: float(m["m"]) for m in map(_NUT_ROW.match, nut_part.split("\n")) if m}
    if pitch != maths.PITCH:
        wrong.append(f"maths.PITCH: protocol {pitch!r}, code {maths.PITCH!r}")
    if nut != maths.NUT_HEIGHT:
        wrong.append(f"maths.NUT_HEIGHT: protocol {nut!r}, code {maths.NUT_HEIGHT!r}")

    registered_names = {*listed, "maths.PITCH", "maths.NUT_HEIGHT"}  # the two tables above
    for name in _PROTOCOL_COMPLETE_MODULES:
        for constant in sorted(_defined_constants(_PROTOCOL_TEXT_MODULES[name])):
            if f"{name}.{constant}" not in registered_names:
                wrong.append(f"{name}.{constant} is not in the protocol")
    assert not wrong, "the protocol and the code disagree:\n" + "\n".join(wrong)


def test_the_protocol_text_above_results_carries_every_pre_registered_section() -> None:
    headings = [line for line in _protocol_head().split("\n") if line.startswith("## ")]
    names = [h.removeprefix("## ") for h in headings]
    assert [n for n in names if n in _PROTOCOL_HEADINGS] == list(_PROTOCOL_HEADINGS)
