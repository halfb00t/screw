"""The bench harness's own predicates, pinned without a service, a daemon or a stopwatch.

Ported from spur's `tests/test_bench.py` (L07): the capped-row rule, the STL size check, the
L19 gzip selection rule, the `ru_maxrss` units, the 503 reasons and the refusal of an empty
sweep. spur's gear-sweep and composed-scenario tests are not carried over -- there is no gear
corpus here. The skeleton corpus is pinned instead, so it cannot drift under a number that
someone compares with an earlier run.

Run as `.venv/bin/python -m pytest tests/test_bench.py -q` from the repo root: the `-m` form
puts the root on `sys.path`, which is what makes `import bench` resolve. `bench` is not an
installed package (`pyproject.toml` ships `src/screw` only) and `tests/conftest.py` puts
`tests/` on the path, not the root.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from bench.build_time import Timing, load_sweep, report, stl_size
from bench.corpus import corpus
from bench.export_cost import GzipRow, find_set, maxrss_bytes, select_gzip_level
from screw.params import BoltParams


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
