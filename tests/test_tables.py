"""The cited rows: relations per row, the UNVERIFIED gate, the type-level citation, the catalogue.

One pure-data relation test per catalogue row (D-14, TABL-03); none builds a solid (C11).
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable
from pathlib import Path

import pytest
from mypy import api as mypy_api

from screw.calc import derive
from screw.params import BoltParams
from screw.tables.iso262 import SIZES
from screw.tables.iso4017 import HEADS, SERIES
from screw.tables.presets import FIELD_NAMES, PresetRow, catalogue, expand
from screw.tables.rows import HexHead, Size, Source

ROOT = Path(__file__).resolve().parents[1]
TABLES_DIR = ROOT / "src" / "screw" / "tables"
ROWS = catalogue()
PITCH = {size.label: size.pitch for size in SIZES}
DIAMETER = {size.label: size.d for size in SIZES}
CHOICE = {size.label: size.choice for size in SIZES}

# The standard nominal lengths the ISO 4017 series are drawn from. The owner confirmed this exact
# list (assumption A1, 04-OWNER-READS.md, 2026-10-12); it is the standard's list, not a formula,
# and the series tests below hold every shipped length to it.
STANDARD_LENGTHS: tuple[float, ...] = (
    2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100, 110,
    120, 130, 140, 150, 160, 180, 200,
)


@pytest.mark.parametrize("row", ROWS, ids=lambda r: r.id)
def test_row_relations(row: PresetRow) -> None:
    head, d = row.head, DIAMETER[row.size]
    assert head.s_min < head.s
    assert head.dw_min < head.s_min
    assert head.s_min < head.e_min < head.s / math.cos(math.radians(30))
    assert head.k_min <= head.k <= head.k_max
    # The printed pitch of the head table is a second source for ISO 262's.
    assert head.pitch == PITCH[row.size]
    # Product grade is a function of diameter and length (the title of the standards).
    assert row.grade == ("A" if d <= 24 and row.length <= min(10 * d, 150) else "B")
    assert head.grade == row.grade
    assert dict(row.fields)["thread_length"] == row.length


@pytest.mark.parametrize("row", ROWS, ids=lambda r: r.id)
def test_a_second_choice_size_is_bracketed_and_a_first_choice_size_is_not(row: PresetRow) -> None:
    bracketed = row.picker[1].startswith("(")
    assert bracketed == (CHOICE[row.size] == 2)
    assert row.choice == CHOICE[row.size]
    assert ("(" in row.display) == bracketed
    assert "(" not in row.designation


def test_k_tolerance_is_symmetric_about_the_nominal() -> None:
    # Held for every column read so far. A confirmed row that breaks it means this invariant is
    # wrong; it then comes out only with the owner's ruling recorded in 04-OWNER-READS.md.
    for head in HEADS:
        assert math.isclose(head.k_max - head.k, head.k - head.k_min, abs_tol=1e-9), head


SECOND_CHOICE = {"M3.5", "M7", "M14", "M18"}
FIRST_CHOICE = {"M2", "M2.5", "M3", "M4", "M5", "M6", "M8", "M10", "M12", "M16", "M20"}


def test_iso_262_holds_exactly_the_fifteen_sizes_of_tabl_05_in_diameter_order() -> None:
    labels = [size.label for size in SIZES]
    assert len(SIZES) == 15
    assert set(labels) == FIRST_CHOICE | SECOND_CHOICE
    assert [size.d for size in SIZES] == sorted({size.d for size in SIZES})
    assert all(size.label == f"M{size.d:g}" for size in SIZES)
    assert {size.label for size in SIZES if size.choice == 2} == SECOND_CHOICE


@pytest.mark.parametrize("head", HEADS, ids=lambda h: f"{h.size}-{h.grade}")
def test_head_relations(head: HexHead) -> None:
    assert head.s_min < head.s
    assert head.dw_min < head.s_min
    assert head.s_min < head.e_min < head.s / math.cos(math.radians(30))
    assert head.k_min <= head.k <= head.k_max
    # The printed pitch of the head table is a second source for ISO 262's (Pitfall 7).
    assert head.pitch == PITCH[head.size]


def test_every_size_has_a_grade_a_head_and_no_head_is_listed_twice() -> None:
    keys = [(head.size, head.grade) for head in HEADS]
    assert len(set(keys)) == len(keys)
    assert {size for size, grade in keys if grade == "A"} == set(PITCH)
    # Grade B is held only for the sizes whose lengths pass 150 mm (D-13).
    assert {size for size, grade in keys if grade == "B"} == {"M16", "M18", "M20"}
    # By diameter ascending, then grade A before B.
    assert keys == sorted(keys, key=lambda k: (DIAMETER[k[0]], k[1]))


def test_a_head_column_is_bracketed_exactly_for_a_second_choice_size() -> None:
    # Pitfall 8: the brackets are printed in the 4017 size column, which `Source.column` keeps.
    for head in HEADS:
        assert head.source.column.startswith("(") == (CHOICE[head.size] == 2), head
        assert head.source.column.endswith(")") == (CHOICE[head.size] == 2), head
    # The column names its size, decimal comma as printed.
    for head in HEADS:
        assert head.source.column.strip("()") == head.size.replace(".", ","), head


def test_each_head_cites_the_table_that_holds_its_grade_and_size() -> None:
    for head in HEADS:
        if head.grade == "B":
            assert head.source.table == "Table 3", head
        else:
            assert head.source.table == ("Table 1" if DIAMETER[head.size] <= 7 else "Table 2"), head


def _series(label: str) -> list[float]:
    return [entry.length for entry in SERIES if entry.size == label]


def test_each_size_series_is_strictly_increasing() -> None:
    for label in {entry.size for entry in SERIES}:
        lengths = _series(label)
        assert lengths == sorted(set(lengths)), label


@pytest.mark.parametrize("label", sorted(PITCH), ids=str)
def test_a_size_series_is_the_listed_lengths_between_two_d_and_the_cap(label: str) -> None:
    # RESEARCH Code Example 5, from the footnotes of the length block: the series starts at the
    # listed length nearest 2 d (a tie goes to the longer) and ends at the longest listed length
    # not above min(10 d, 200), with no listed length missing in between (A1).
    d = DIAMETER[label]
    first = min(STANDARD_LENGTHS, key=lambda n: (abs(n - 2 * d), -n))
    last = max(n for n in STANDARD_LENGTHS if n <= min(10 * d, 200))
    lengths = _series(label)
    assert lengths, label  # a size with no length would pass every loop below for nothing
    assert set(lengths) <= set(STANDARD_LENGTHS)
    assert lengths == [n for n in STANDARD_LENGTHS if first <= n <= last]


def test_the_two_series_bounds_are_ties_to_the_longer_for_m3_5_and_m7() -> None:
    # 2 d = 7 sits midway between 6 and 8, 2 d = 14 midway between 12 and 16 (Pitfall 6).
    assert _series("M3.5")[0] == 8
    assert _series("M7")[0] == 16


def test_150_mm_is_grade_a_and_the_next_listed_length_is_grade_b() -> None:
    for label in ("M16", "M18", "M20"):
        grades = {entry.length: entry.grade for entry in SERIES if entry.size == label}
        assert grades[150.0] == "A", label
        assert grades[160.0] == "B", label
    assert all(entry.grade == "A" for entry in SERIES if entry.length <= 150)
    assert all(entry.grade == "B" for entry in SERIES if entry.length > 150)


def test_every_series_grade_has_a_head_and_grade_b_heads_exist_only_for_grade_b_lengths() -> None:
    heads = {(head.size, head.grade) for head in HEADS}
    assert {(entry.size, entry.grade) for entry in SERIES} == heads


def test_every_series_length_cites_the_table_that_holds_its_head() -> None:
    sources = {(head.size, head.grade): head.source for head in HEADS}
    for entry in SERIES:
        assert entry.source == sources[entry.size, entry.grade], entry


def test_the_iso_4017_catalogue_has_the_row_count_the_agreed_transcription_yields() -> None:
    # Counted after the owner copy and the transcription agreed cell by cell: 8 + 8 + 8 + 8 + 9
    # + 10 + 11 + 12 grade A lengths in Table 1, 13 + 14 + 15 + 16 + 17 + 16 + 15 in Table 2 and
    # 1 + 2 + 3 grade B lengths in Table 3.
    assert sum(1 for row in ROWS if row.standard == "ISO 4017") == 186
    assert len(SERIES) == 186


@pytest.mark.parametrize("row", ROWS, ids=lambda r: r.id)
def test_every_catalogue_row_is_recognised_as_its_own_row_on_the_info_document(
    row: PresetRow,
) -> None:
    info = derive(BoltParams.model_validate(dict(row.fields)))
    assert info.preset is not None
    assert (info.preset.status, info.preset.id) == ("exact", row.id)
    assert info.designation == row.designation


@pytest.mark.parametrize(
    ("label", "shown", "preset_id"),
    [("M7", "(M7)", "iso4017:M7x20"), ("M3.5", "(M3.5)", "iso4017:M3.5x20"),
     ("M14", "(M14)", "iso4017:M14x50"), ("M18", "(M18)", "iso4017:M18x50")],
)
def test_a_second_choice_row_is_bracketed_in_display_and_picker_but_not_in_id_or_designation(
    label: str, shown: str, preset_id: str,
) -> None:
    row = next(r for r in ROWS if r.id == preset_id)
    length = f"{row.length:g}"
    assert row.display == f"ISO 4017 {shown} \u00d7 {length}"
    assert row.picker == ("ISO 4017", shown, length)
    assert row.designation == (
        f"Hexagon head screw ISO 4017 - {label.replace('.', ',')} x {length}"
    )
    assert "(" not in row.id


def test_the_catalogue_lists_m20_up_to_the_200_mm_cap_and_no_longer() -> None:
    assert expand("iso4017:M20x200") is not None
    assert expand("iso4017:M20x220") is None
    assert max(row.length for row in ROWS) == 200


def test_catalogue_ids_are_unique_match_the_grammar_and_are_in_catalogue_order() -> None:
    ids = [row.id for row in ROWS]
    assert len(set(ids)) == len(ids)
    assert all(re.fullmatch(r"iso(4014|4017):M\d+(\.\d+)?x\d+", i) for i in ids)
    # ISO 4017 first, then by diameter and length ascending.
    order = [(row.standard, DIAMETER[row.size], row.length) for row in ROWS]
    assert order == sorted(order, key=lambda o: (o[0] != "ISO 4017", o[1], o[2]))


def test_the_m6_by_20_preset_expands_to_the_frozen_defaults_of_the_part() -> None:
    fields = expand("iso4017:M6x20")
    assert fields == {
        "d": 6.0, "pitch": 1.0, "length": 20.0, "s": 10.0, "k": 4.0, "thread_length": 20.0,
    }
    defaults = BoltParams()
    assert fields == {name: getattr(defaults, name) for name in FIELD_NAMES}


@pytest.mark.parametrize("preset_id", ["iso4017:m6x20", "iso4017:M6x21", "", "../etc/passwd"])
def test_an_id_not_in_the_catalogue_is_none(preset_id: str) -> None:
    assert expand(preset_id) is None


def test_the_row_citation_lists_each_source_once_and_the_designation_has_no_class() -> None:
    row = next(r for r in ROWS if r.id == "iso4017:M6x20")
    assert row.citation() == (
        "ISO 262:2023 Table 1, column Coarse; ISO 4017:2022 Table 1, column M6"
    )
    assert row.display == "ISO 4017 M6 \u00d7 20"
    assert row.picker == ("ISO 4017", "M6", "20")
    assert row.designation == "Hexagon head screw ISO 4017 - M6 x 20"
    assert not re.search(r"\b\d+\.\d\b", row.designation)  # no property class such as 8.8


def test_field_names_are_all_bolt_params_fields() -> None:
    assert set(FIELD_NAMES) <= set(BoltParams.model_fields)
    assert all(set(dict(row.fields)) == set(FIELD_NAMES) for row in ROWS)


# The UNVERIFIED gate (D-15): a text scan of every module and a runtime walk of every row.
_UNVERIFIED = re.compile(r"""\bstatus\s*=\s*["']unverified["']""")


def scan(directory: Path) -> list[str]:
    """`path:line` of every `status="unverified"` under `directory`."""
    return [
        f"{path}:{number}"
        for path in sorted(directory.rglob("*.py"))
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if _UNVERIFIED.search(line)
    ]


def unverified(rows: Iterable[object]) -> list[str]:
    """The `repr` of every row whose source is not verified."""
    return [
        repr(row)
        for row in rows
        if isinstance(source := getattr(row, "source", None), Source)
        and source.status != "verified"
    ]


def test_no_module_marks_a_row_unverified() -> None:
    assert scan(TABLES_DIR) == []


def test_no_row_in_the_tree_is_unverified() -> None:
    sources = [source for row in ROWS for source in row.sources]
    assert unverified([*SIZES, *HEADS, *SERIES]) == []
    assert [s for s in sources if s.status != "verified"] == []
    assert len(sources) == 3 * len(ROWS)


def test_the_text_scan_sees_an_unverified_row(tmp_path: Path) -> None:
    module = tmp_path / "rows.py"
    module.write_text(
        'ok = Source(standard="x", edition="1", table="t", column="c", status="verified")\n'
        'bad = Source(standard="x", edition="1", table="t", column="c", status="unverified")\n',
        encoding="utf-8",
    )
    assert scan(tmp_path) == [f"{module}:2"]


def test_the_runtime_check_sees_an_unverified_row() -> None:
    size = Size(
        label="M6", d=6.0, pitch=1.0, choice=1,
        source=Source(standard="ISO 262", edition="2023", table="Table 1", column="Coarse",
                      status="unverified"),
    )
    assert unverified([size]) == [repr(size)]


# TABL-02: a row without `source=` is a type error naming `source`; the same row with it passes.
_BAD_AND_GOOD = '''\
from screw.tables.rows import HexHead, Source

SOURCE = Source(
    standard="ISO 4017", edition="2022", table="Table 1", column="M6", status="verified"
)
{call}(
    size="M6", grade="A", pitch=1.0, s=10.0, s_min=9.78, e_min=11.05,
    k=4.0, k_min=3.85, k_max=4.15, dw_min=8.88{source}
)
'''


def test_a_row_without_source_fails_mypy_strict_naming_source_and_the_same_row_with_it_passes(
    tmp_path: Path,
) -> None:
    bad, good = tmp_path / "bad_row.py", tmp_path / "good_row.py"
    bad_text = _BAD_AND_GOOD.format(call="BAD = HexHead", source="")
    bad.write_text(bad_text, encoding="utf-8")
    bad_line = 1 + bad_text[: bad_text.index("BAD = HexHead")].count("\n")
    good.write_text(
        _BAD_AND_GOOD.format(call="GOOD = HexHead", source=",\n    source=SOURCE"),
        encoding="utf-8",
    )
    stdout, _, status = mypy_api.run([
        "--config-file", str(ROOT / "pyproject.toml"), "--strict",
        "--cache-dir", str(tmp_path / "mypy-cache"), str(bad), str(good),
    ])
    errors = stdout.splitlines()
    assert status == 1, stdout
    assert any(
        line.startswith(f"{bad}:{bad_line}:") and '"source"' in line for line in errors
    ), stdout
    assert not any(str(good) in line for line in errors), stdout

