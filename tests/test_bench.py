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
import struct
import subprocess
import sys
from collections.abc import Iterable, Sequence
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
from bench.thread_spike import helical, maths, measure
from bench.thread_spike.__main__ import _table_row
from bench.thread_spike.runner import Worker
from bench.thread_spike.verdict import (
    PROTOCOL_PATH,
    ROW_TIMEOUT_S,
    T_PASS,
    MeshRecord,
    RowRecord,
    RowRequest,
    before_results,
    classify_row,
    failed_record,
    parse_record,
    parse_request,
    protocol_guard,
    relative_error,
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


_REQUEST: RowRequest = {
    "kind": "rod", "size": "M6", "d": 6.0, "pitch": 1.0, "turns": 5.0, "length": 5.0,
    "left_hand": False, "k": 5, "clearance": 0.0, "presets": [("preview", 0.08, 0.5)],
}


def _built(precise: float, *, solids: int = 1, valid: bool = True,
           meshes: list[MeshRecord] | None = None) -> RowRecord:
    return {
        **_REQUEST, "outcome": "built", "error": None, "solids": solids, "is_valid": valid,
        "precise_volume": precise, "default_volume": precise, "build_s": 0.1, "volume_s": 0.1,
        "meshes": [] if meshes is None else meshes,
    }


def _mesh(*, watertight: bool = True, volume: float = 1.0, area: float = 10.0,
          checked: bool = True) -> MeshRecord:
    return {
        "preset": "preview", "tolerance": 0.08, "angular": 0.5, "triangles": 100, "bytes": 5084,
        "mesh_s": 0.01, "checked": checked,
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
