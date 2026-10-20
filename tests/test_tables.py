"""The cited rows: relations per row, the UNVERIFIED gate, the type-level citation, the catalogue.

One pure-data relation test per catalogue row (D-14, TABL-03); none builds a solid (C11).
"""

from __future__ import annotations

import dataclasses
import math
import re
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path

import pytest
from mypy import api as mypy_api

from screw.calc import derive
from screw.calc.thread import FILLET_R, basic_minor_diameter, fillet_radius, pitch_diameter
from screw.params import BoltParams
from screw.tables import gost16093, iso724, iso4014, iso4032
from screw.tables.iso262 import SIZES
from screw.tables.iso4017 import HEADS, SERIES
from screw.tables.presets import FIELD_NAMES, PresetRow, catalogue, expand
from screw.tables.rows import (
    BasicDiameters,
    BoltLimits,
    HexHead,
    HexNut,
    NutLimits,
    ShankCell,
    Size,
    Source,
    Tolerance,
)

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
    # ISO 4017 is threaded to the head (D-07); an ISO 4014 bolt is threaded b of its band (THRD-03).
    expected_thread = row.length if row.standard == "ISO 4017" else _b_of(row.size, row.length)
    assert dict(row.fields)["thread_length"] == expected_thread


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
    for head in (*HEADS, *iso4014.HEADS):
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


@pytest.mark.parametrize(
    "head", [*HEADS, *iso4014.HEADS], ids=lambda h: f"{h.source.standard}-{h.size}-{h.grade}"
)
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


# ISO 4014:2022 (TYPE-01): heads, the thread length b by band, and the printed shank cells.
BAND = {band.size: band for band in iso4014.BANDS}
HEAD_4014 = {(head.size, head.grade): head for head in iso4014.HEADS}


def _cell_id(cell: ShankCell) -> str:
    return f"{cell.size}x{cell.length:g}"


def _b_of(size: str, length: float) -> float:
    """b of the band the length falls in: b for l <= 125, c for 125 < l <= 200."""
    band = BAND[size]
    if length <= 125:
        return band.b_short
    assert band.b_long is not None, (size, length)
    return band.b_long


@pytest.mark.parametrize("cell", iso4014.CELLS, ids=_cell_id)
def test_a_printed_shank_cell_satisfies_lg_max_and_ls_min_from_its_bands_b(
    cell: ShankCell,
) -> None:
    # Pitfall 5: the stored printed cells are tested against the relations, never recomputed from
    # them, so a mistyped digit in either column fails here as well as in the owner diff.
    b = _b_of(cell.size, cell.length)
    assert abs(cell.lg_max - (cell.length - b)) <= 1e-9, cell
    assert abs(cell.ls_min - (cell.lg_max - 5 * PITCH[cell.size])) <= 1e-9, cell


def test_the_iso_4014_pitch_of_each_head_and_band_is_the_iso_262_pitch() -> None:
    assert all(head.pitch == PITCH[head.size] for head in iso4014.HEADS)
    assert {band.size for band in iso4014.BANDS} == set(PITCH)


def test_a_band_has_a_second_b_exactly_when_a_length_of_the_size_exceeds_125() -> None:
    for size, band in BAND.items():
        longest = max(c.length for c in iso4014.CELLS if c.size == size)
        assert (band.b_long is not None) == (longest > 125), size
        # b grows with l: the longer band never has the shorter thread.
        assert band.b_long is None or band.b_long > band.b_short, size


def test_every_length_uses_the_band_its_length_falls_in_at_the_125_mm_boundary() -> None:
    # The cell at 120 or 125 mm and the next listed one (130) sit either side of the boundary
    # for M14 to M20: 120 takes b, 130 takes c (Table 3, footnotes b and c).
    for size in ("M14", "M16", "M18", "M20"):
        by_length = {c.length: c for c in iso4014.CELLS if c.size == size}
        assert by_length[120.0].length - by_length[120.0].lg_max == BAND[size].b_short, size
        assert by_length[130.0].length - by_length[130.0].lg_max == BAND[size].b_long, size


@pytest.mark.parametrize("label", sorted(PITCH), ids=str)
def test_an_iso_4014_size_lists_increasing_standard_lengths_up_to_ten_diameters(
    label: str,
) -> None:
    d = DIAMETER[label]
    lengths = [c.length for c in iso4014.CELLS if c.size == label]
    assert lengths, label  # a size with no cell would pass every check below for nothing
    assert lengths == sorted(set(lengths)), label
    assert set(lengths) <= set(STANDARD_LENGTHS), label
    assert lengths[-1] <= 10 * d, label
    # Footnote e: the greatest listed length not above 10 d, and none missing between the ends.
    assert lengths[-1] == max(n for n in STANDARD_LENGTHS if n <= min(10 * d, 200)), label
    assert lengths == [n for n in STANDARD_LENGTHS if lengths[0] <= n <= lengths[-1]], label


@pytest.mark.parametrize("label", [s for s in sorted(PITCH) if DIAMETER[s] >= 5], ids=str)
def test_the_shortest_iso_4014_length_follows_the_footnote_from_m5_up(label: str) -> None:
    # Footnote d: 5 d for M5 to M8, 4,5 d for M10, 4 d for M12 to M22, to the nearest listed
    # length. M2 to M4 print no such rule; the owner copy alone holds those cells.
    d = DIAMETER[label]
    factor = 5 if d <= 8 else 4.5 if d == 10 else 4
    shortest = min(c.length for c in iso4014.CELLS if c.size == label)
    assert shortest == min(STANDARD_LENGTHS, key=lambda n: (abs(n - factor * d), -n)), label


def test_150_mm_is_the_last_grade_a_iso_4014_length_and_the_next_one_is_grade_b() -> None:
    for cell in iso4014.CELLS:
        assert cell.grade == ("A" if cell.length <= min(10 * DIAMETER[cell.size], 150) else "B")
    assert {c.size for c in iso4014.CELLS if c.grade == "B"} == {"M16", "M18", "M20"}
    assert all(c.length > 150 for c in iso4014.CELLS if c.grade == "B")


def test_every_iso_4014_cell_has_its_grade_head_and_cites_the_same_table_and_column() -> None:
    assert {(c.size, c.grade) for c in iso4014.CELLS} == set(HEAD_4014)
    for cell in iso4014.CELLS:
        assert cell.source == HEAD_4014[cell.size, cell.grade].source, cell


def test_iso_4014_heads_and_bands_cite_the_table_and_bracketed_column_of_their_size() -> None:
    for head in iso4014.HEADS:
        table = "Table 4" if head.grade == "B" else (
            "Table 1" if DIAMETER[head.size] <= 4 else
            "Table 2" if DIAMETER[head.size] <= 12 else "Table 3"
        )
        assert head.source.table == table, head
    sourced: list[tuple[str, Source]] = [
        *((head.size, head.source) for head in iso4014.HEADS),
        *((band.size, band.source) for band in iso4014.BANDS),
    ]
    for size, source in sourced:
        assert (source.standard, source.edition) == ("ISO 4014", "2022"), size
        assert source.column.startswith("(") == (CHOICE[size] == 2), size
        assert source.column.strip("()") == size.replace(".", ","), size
    # A band is read from its size's grade A table, the same cell as the grade A head.
    for band in iso4014.BANDS:
        assert band.source == HEAD_4014[band.size, "A"].source, band


def test_every_size_has_a_grade_a_iso_4014_head_and_grade_b_only_for_m16_m18_m20() -> None:
    keys = list(HEAD_4014)
    assert len(keys) == len(iso4014.HEADS) == 18
    assert {size for size, grade in keys if grade == "A"} == set(PITCH)
    assert {size for size, grade in keys if grade == "B"} == {"M16", "M18", "M20"}
    assert keys == sorted(keys, key=lambda k: (DIAMETER[k[0]], k[1]))


def test_the_iso_4014_row_counts_the_agreed_transcription_yields() -> None:
    # Counted after the owner copy and the transcription agreed cell by cell: 2 + 3 + 3 + 4 + 4
    # cells in Table 1, 6 + 7 + 8 + 8 + 9 + 10 in Table 2, 11 + 10 + 9 + 8 grade A cells in
    # Table 3 and 1 + 2 + 3 grade B cells in Table 4.
    assert len(iso4014.CELLS) == 108
    assert len(iso4014.BANDS) == 15


@pytest.mark.parametrize("head", iso4014.HEADS, ids=lambda h: f"{h.size}-{h.grade}")
def test_an_iso_4014_head_equals_the_iso_4017_head_of_the_same_size_and_grade(
    head: HexHead,
) -> None:
    # A3 = yes (04-OWNER-READS.md, 2026-10-12): the values are equal as numbers, though the
    # printed digits differ (ISO 4017 M6 k reads `4`, ISO 4014 M6 k reads `4,0`). Equal does not
    # mean one row: each standard keeps its own head row and its own citation (TABL-02).
    other = next(h for h in HEADS if (h.size, h.grade) == (head.size, head.grade))
    for column in ("pitch", "s", "s_min", "e_min", "k", "k_min", "k_max", "dw_min"):
        assert getattr(head, column) == getattr(other, column), column
    assert head is not other
    assert head.source.standard == "ISO 4014"
    assert other.source.standard == "ISO 4017"


ROWS_4014 = [row for row in ROWS if row.standard == "ISO 4014"]


def test_the_iso_4014_catalogue_has_one_row_per_shank_cell() -> None:
    assert len(ROWS_4014) == len(iso4014.CELLS) == 108
    assert len(ROWS) == 186 + 108


@pytest.mark.parametrize("row", ROWS_4014, ids=lambda r: r.id)
def test_an_iso_4014_row_fills_thread_length_with_b_of_its_band_and_is_shorter_than_the_bolt(
    row: PresetRow,
) -> None:
    fields = dict(row.fields)
    assert fields["thread_length"] == _b_of(row.size, row.length)
    assert fields["thread_length"] < fields["length"]
    assert row.band is BAND[row.size]
    assert row.cell is not None
    assert (row.cell.size, row.cell.length) == (row.size, row.length)
    assert row.id == f"iso4014:{row.size}x{row.length:g}"


def test_an_iso_4017_row_carries_no_band_and_no_cell() -> None:
    assert all(
        row.band is None and row.cell is None for row in ROWS if row.standard == "ISO 4017"
    )


def test_the_catalogue_order_lists_every_iso_4017_row_before_iso_4014_so_a_tie_reads_4017() -> None:
    # `match` returns the first equal row, so the catalogue order is the tie rule (CONTEXT
    # discretion): a part equal to rows of both standards would be reported as ISO 4017.
    standards = [row.standard for row in ROWS]
    last_4017 = max(i for i, name in enumerate(standards) if name == "ISO 4017")
    first_4014 = standards.index("ISO 4014")
    assert last_4017 < first_4014


def test_no_iso_4014_row_has_the_fields_of_an_iso_4017_row_so_the_tie_is_latent() -> None:
    # An ISO 4017 screw is threaded to the head, an ISO 4014 bolt only b of it, so the two
    # standards never share a part today. If a later table makes them equal, the order above
    # decides and this test is the one to revisit.
    fields_4017 = {row.fields for row in ROWS if row.standard == "ISO 4017"}
    assert [row.id for row in ROWS_4014 if row.fields in fields_4017] == []


@pytest.mark.parametrize(
    ("label", "shown", "preset_id"),
    [("M10", "M10", "iso4014:M10x80"), ("M3.5", "(M3.5)", "iso4014:M3.5x20"),
     ("M14", "(M14)", "iso4014:M14x60"), ("M18", "(M18)", "iso4014:M18x100")],
)
def test_an_iso_4014_row_has_the_owners_designation_and_brackets_a_second_choice_size(
    label: str, shown: str, preset_id: str,
) -> None:
    row = next(r for r in ROWS if r.id == preset_id)
    length = f"{row.length:g}"
    assert row.display == f"ISO 4014 {shown} \u00d7 {length}"
    assert row.picker == ("ISO 4014", shown, length)
    assert row.designation == (
        f"Hexagon head bolt ISO 4014 - {label.replace('.', ',')} x {length}"
    )
    assert "(" not in row.id


def test_the_m10_by_80_row_cites_its_standard_and_expands_to_b_as_the_thread_length() -> None:
    row = next(r for r in ROWS if r.id == "iso4014:M10x80")
    assert row.citation() == (
        "ISO 262:2023 Table 1, column Coarse; ISO 4014:2022 Table 2, column M10"
    )
    assert expand("iso4014:M10x80") == {
        "d": 10.0, "pitch": 1.5, "length": 80.0, "s": 16.0, "k": 6.4, "thread_length": 26.0,
    }
    # The row's own printed cell: lg,max = 80 - 26, ls,min = lg,max - 5 * 1.5.
    assert row.cell is not None
    assert (row.cell.ls_min, row.cell.lg_max) == (46.5, 54.0)


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
    assert unverified([*SIZES, *HEADS, *SERIES, *iso4014.HEADS, *iso4014.CELLS]) == []
    assert unverified(iso4014.BANDS) == []
    assert unverified(iso4014.FILLETS) == []
    assert unverified(iso4032.NUTS) == []
    assert unverified(iso724.BASIC) == []
    assert unverified(gost16093.TOLERANCES) == []
    assert [s for s in sources if s.status != "verified"] == []
    # Size, head and length for ISO 4017; size, head, band and cell for ISO 4014.
    assert len(sources) == sum(3 if row.standard == "ISO 4017" else 4 for row in ROWS)


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



# Source.document() and the nut rows (L14): a GOST text is cited with the ISO edition it adopts.
def test_the_nut_rows_are_the_14_gost_iso_4032_rows_with_their_table_and_no_m7() -> None:
    sizes = [nut.size for nut in iso4032.NUTS]
    assert sizes == [
        "M2", "M2.5", "M3", "M3.5", "M4", "M5", "M6", "M8", "M10", "M12", "M14", "M16", "M18",
        "M20",
    ]
    assert {nut.size for nut in iso4032.NUTS if nut.source.table == "Table 2"} == {
        "M3.5", "M14", "M18",
    }
    assert {nut.source.table for nut in iso4032.NUTS} == {"Table 1", "Table 2"}
    assert all(
        nut.source.standard == "GOST ISO 4032"
        and nut.source.edition == "2014"
        and nut.source.status == "verified"
        for nut in iso4032.NUTS
    )


def test_the_nut_row_has_exactly_the_printed_columns_the_size_the_grade_and_the_source() -> None:
    assert [f.name for f in dataclasses.fields(HexNut)] == [
        "size", "grade", "pitch", "s", "s_min", "e_min", "m_max", "m_min", "mw_min", "dw_min",
        "c_max", "c_min", "da_max", "da_min", "source",
    ]


def test_a_nut_row_cites_the_gost_text_with_the_iso_edition_it_adopts() -> None:
    assert {nut.source.document() for nut in iso4032.NUTS} == {"GOST ISO 4032-2014 (ISO 4032:2012)"}
    m6 = next(nut for nut in iso4032.NUTS if nut.size == "M6")
    assert m6.source.cite() == "GOST ISO 4032-2014 (ISO 4032:2012) Table 1, column M6"
    assert (m6.source.table, m6.source.column) == ("Table 1", "M6")


def test_every_phase_4_row_cites_exactly_as_before() -> None:
    sources = [
        *(row.source for row in SIZES),
        *(row.source for row in HEADS),
        *(row.source for row in SERIES),
        *(row.source for row in iso4014.HEADS),
        *(row.source for row in iso4014.BANDS),
        *(row.source for row in iso4014.CELLS),
    ]
    assert sources
    for source in sources:
        assert source.document() == f"{source.standard}:{source.edition}"
        assert source.cite() == (
            f"{source.standard}:{source.edition} {source.table}, column {source.column}"
        )
    head = next(row for row in HEADS if row.size == "M6")
    assert head.source.document() == "ISO 4017:2022"
    assert head.source.cite() == "ISO 4017:2022 Table 1, column M6"


@pytest.mark.parametrize("standard", ["GOST 99999", "GOST ISO 9999", "DIN 934", ""])
def test_a_standard_with_no_citation_form_is_refused_by_name(standard: str) -> None:
    source = Source(standard=standard, edition="2014", table="Table 1", column="M6",
                    status="verified")
    with pytest.raises(ValueError, match="no citation form"):
        source.document()


_NUT_BAD_AND_GOOD = '''\
from screw.tables.rows import HexNut, Source

SOURCE = Source(
    standard="GOST ISO 4032", edition="2014", table="Table 1", column="M6", status="verified"
)
{call}(
    size="M6", grade="A", pitch=1.0, s=10.0, s_min=9.78, e_min=11.05, m_max=5.2, m_min=4.9,
    mw_min=3.9, dw_min=8.9, c_max=0.5, c_min=0.15, da_max=6.75, da_min=6.0{source}
)
'''


def test_a_nut_row_without_source_fails_mypy_strict_naming_source(tmp_path: Path) -> None:
    bad = tmp_path / "bad_nut.py"
    bad_text = _NUT_BAD_AND_GOOD.format(call="BAD = HexNut", source="")
    bad.write_text(bad_text, encoding="utf-8")
    good = tmp_path / "good_nut.py"
    good.write_text(
        _NUT_BAD_AND_GOOD.format(call="GOOD = HexNut", source=",\n    source=SOURCE"),
        encoding="utf-8",
    )
    stdout, _, status = mypy_api.run([
        "--config-file", str(ROOT / "pyproject.toml"), "--strict",
        "--cache-dir", str(tmp_path / "mypy-cache"), str(bad), str(good),
    ])
    bad_line = 1 + bad_text[: bad_text.index("BAD = HexNut")].count("\n")
    assert status == 1, stdout
    assert any(
        line.startswith(f"{bad}:{bad_line}:") and '"source"' in line
        for line in stdout.splitlines()
    ), stdout
    assert not any(str(good) in line for line in stdout.splitlines()), stdout


def broken_nut_relations(nut: HexNut) -> list[str]:
    """The relations a printed nut row breaks, each named; empty for a sound row."""
    checks = {
        "s_min < s": nut.s_min < nut.s,
        "e_min > s": nut.e_min > nut.s,
        "m_min < m_max": nut.m_min < nut.m_max,
        "mw_min < m_min": nut.mw_min < nut.m_min,
        "dw_min < s_min": nut.dw_min < nut.s_min,
        "c_min < c_max": nut.c_min < nut.c_max,
        "da_min < da_max": nut.da_min < nut.da_max,
        "pitch is the ISO 262 coarse pitch": nut.pitch == PITCH[nut.size],
        # The scope clause: grade A for D up to M16, B above (read on the rendered page).
        "grade A up to d = 16, B above": nut.grade == ("A" if DIAMETER[nut.size] <= 16 else "B"),
    }
    return [f"{nut.size}: {name}" for name, holds in checks.items() if not holds]


@pytest.mark.parametrize("nut", iso4032.NUTS, ids=lambda n: n.size)
def test_nut_relations(nut: HexNut) -> None:
    assert broken_nut_relations(nut) == []


def test_a_planted_nut_row_that_breaks_a_relation_is_reported_by_size_and_relation() -> None:
    m6 = next(nut for nut in iso4032.NUTS if nut.size == "M6")
    planted = dataclasses.replace(m6, m_min=m6.m_max + 0.1)
    assert broken_nut_relations(planted) == ["M6: m_min < m_max"]
    assert broken_nut_relations(dataclasses.replace(m6, grade="B")) == [
        "M6: grade A up to d = 16, B above"
    ]


# GOST 24705-2004 Table 1 (ISO 724:1993, MOD): the basic diameters the 6g and 6H limits add to.
def test_the_basic_rows_are_the_15_coarse_iso_262_sizes_with_iso_262s_d_and_pitch() -> None:
    assert [row.size for row in iso724.BASIC] == [size.label for size in SIZES]
    assert all(row.d == DIAMETER[row.size] and row.pitch == PITCH[row.size] for row in iso724.BASIC)


def test_a_basic_row_cites_gost_24705_table_1_at_its_printed_nominal_diameter() -> None:
    assert {row.source.document() for row in iso724.BASIC} == {
        "GOST 24705-2004 (ISO 724:1993, MOD)"
    }
    assert {row.source.table for row in iso724.BASIC} == {"Table 1"}
    assert all(row.source.status == "verified" for row in iso724.BASIC)
    m25 = next(row for row in iso724.BASIC if row.size == "M2.5")
    assert m25.source.cite() == "GOST 24705-2004 (ISO 724:1993, MOD) Table 1, column 2,5"


@pytest.mark.parametrize("row", iso724.BASIC, ids=lambda r: r.size)
def test_a_printed_d2_and_d1_equal_the_basic_profile_formula_rounded_to_the_printed_decimals(
    row: object,
) -> None:
    # R13: the agreement test only; no panel number comes from the table.
    assert isinstance(row, BasicDiameters)
    assert round(pitch_diameter(row.d, row.pitch), 3) == row.d2
    assert round(basic_minor_diameter(row.d, row.pitch), 3) == row.d1


@pytest.mark.parametrize("row", iso724.BASIC, ids=lambda r: r.size)
def test_basic_relations(row: object) -> None:
    assert isinstance(row, BasicDiameters)
    assert row.d1 < row.d2 < row.d


# GOST 16093-2004 deviations and tolerances, and the 6g and 6H limits derived from them (L14).
_G16093 = "GOST 16093-2004 (based on ISO 965-1:1998 and ISO 965-3:1998)"
_G24705 = "GOST 24705-2004 (ISO 724:1993, MOD)"
_BASIC = {row.size: row for row in iso724.BASIC}
_UM = Decimal("0.001")


def test_every_printed_term_is_verified_gost_16093_and_there_are_72_unique_ones() -> None:
    terms = gost16093.TOLERANCES
    assert len(terms) == 72
    assert {t.source.document() for t in terms} == {_G16093}
    assert {t.source.edition for t in terms} == {"2004"}
    assert {t.unit for t in terms} == {"um"}
    keys = [(t.quantity, t.grade, t.pitch, t.d_over, t.d_upto) for t in terms]
    assert len(set(keys)) == len(keys)
    # Tables 5 and 6 are keyed by range; the others by pitch alone.
    assert {t.quantity for t in terms if t.d_over is not None} == {"Td2", "TD2"}
    assert all(t.pitch in {b.pitch for b in iso724.BASIC} for t in terms)


def test_the_limits_are_one_row_per_size_with_iso_262s_pitch() -> None:
    labels = [size.label for size in SIZES]
    assert [b.size for b in gost16093.BOLT_LIMITS] == labels
    assert [n.size for n in gost16093.NUT_LIMITS] == labels
    assert all(b.pitch == PITCH[b.size] for b in gost16093.BOLT_LIMITS)
    assert all(n.pitch == PITCH[n.size] for n in gost16093.NUT_LIMITS)


def _printed(quantity: str, grade: str, row: BasicDiameters) -> Decimal:
    """The printed term of a size in mm, found by a different walk than the module's."""
    (term,) = (
        t for t in gost16093.TOLERANCES
        if (t.quantity, t.grade, t.pitch) == (quantity, grade, row.pitch)
        and (t.d_over is None or t.d_over < row.d <= (t.d_upto or 0))
    )
    return Decimal(repr(term.value)) * _UM


def _decimal(value: float) -> Decimal:
    return Decimal(repr(value))


def test_each_limit_is_the_exact_decimal_sum_of_its_printed_addends() -> None:
    for bolt in gost16093.BOLT_LIMITS:
        row = _BASIC[bolt.size]
        es = _printed("es", "g", row)
        want = {
            "d_max": _decimal(row.d) + es,
            "d_min": _decimal(row.d) + es - _printed("Td", "6", row),
            "d2_max": _decimal(row.d2) + es,
            "d2_min": _decimal(row.d2) + es - _printed("Td2", "6", row),
        }
        for name, total in want.items():
            # repr round-trips through Decimal to the exact sum: no float error is in the limit.
            assert _decimal(getattr(bolt, name)) == total, (bolt.size, name)
    for nut in gost16093.NUT_LIMITS:
        row = _BASIC[nut.size]
        ei = _printed("EI", "H", row)
        want = {
            "D1_min": _decimal(row.d1) + ei,
            "D1_max": _decimal(row.d1) + ei + _printed("TD1", "6", row),
            "D2_min": _decimal(row.d2) + ei,
            "D2_max": _decimal(row.d2) + ei + _printed("TD2", "6", row),
        }
        for name, total in want.items():
            assert _decimal(getattr(nut, name)) == total, (nut.size, name)


def test_a_limit_row_cites_derived_and_names_both_gost_texts_once_per_addend() -> None:
    m6 = next(b for b in gost16093.BOLT_LIMITS if b.size == "M6")
    assert m6.sources == (
        _BASIC["M6"].source,
        *(
            t.source for t in gost16093.TOLERANCES
            if (t.quantity, t.pitch) in {("es", 1.0), ("Td", 1.0), ("Td2", 1.0)} and t.grade != "H"
        ),
    )
    assert m6.citation().startswith("derived: ")
    assert _G24705 in m6.citation()
    assert _G16093 in m6.citation()
    assert m6.citation().split(" + ") == [
        f"derived: {_G24705} Table 1, column 6",
        f"{_G16093} Table 7, column g",
        f"{_G16093} Table 3, column 6",
        f"{_G16093} Table 5, column 6",
    ]
    for nut in gost16093.NUT_LIMITS:
        assert nut.citation().startswith("derived: ")
        assert _G24705 in nut.citation()
        assert _G16093 in nut.citation()
        assert len(nut.sources) == 4


def broken_limit_relations(
    basic: BasicDiameters, bolt: BoltLimits, nut: NutLimits
) -> list[str]:
    """The relations a derived limit row breaks, each named; empty for a sound row."""
    checks = {
        "d_min < d_max": bolt.d_min < bolt.d_max,
        "d_max < d": bolt.d_max < basic.d,
        "d2_min < d2_max": bolt.d2_min < bolt.d2_max,
        "d2_max < d2": bolt.d2_max < basic.d2,
        "D1 <= D1_min": basic.d1 <= nut.D1_min,
        "D1_min < D1_max": nut.D1_min < nut.D1_max,
        "D2 <= D2_min": basic.d2 <= nut.D2_min,
        "D2_min < D2_max": nut.D2_min < nut.D2_max,
    }
    return [f"{basic.size}: {name}" for name, holds in checks.items() if not holds]


@pytest.mark.parametrize("size", [size.label for size in SIZES])
def test_limit_relations(size: str) -> None:
    bolt = next(b for b in gost16093.BOLT_LIMITS if b.size == size)
    nut = next(n for n in gost16093.NUT_LIMITS if n.size == size)
    assert broken_limit_relations(_BASIC[size], bolt, nut) == []


def test_a_planted_limit_row_that_breaks_a_relation_is_reported_by_size_and_relation() -> None:
    bolt = next(b for b in gost16093.BOLT_LIMITS if b.size == "M6")
    nut = next(n for n in gost16093.NUT_LIMITS if n.size == "M6")
    assert broken_limit_relations(
        _BASIC["M6"], dataclasses.replace(bolt, d_max=6.0), nut
    ) == ["M6: d_max < d"]
    assert broken_limit_relations(
        _BASIC["M6"], bolt, dataclasses.replace(nut, D2_min=_BASIC["M6"].d2 - 0.001)
    ) == ["M6: D2 <= D2_min"]


def _limits_of(terms: Iterable[Tolerance]) -> dict[str, tuple[float, ...]]:
    bolts, nuts = gost16093.derive_limits(iso724.BASIC, terms)
    return {
        **{f"bolt {b.size}": (b.d_max, b.d_min, b.d2_max, b.d2_min) for b in bolts},
        **{f"nut {n.size}": (n.D1_min, n.D1_max, n.D2_min, n.D2_max) for n in nuts},
    }


def test_a_planted_term_moves_exactly_the_limits_that_add_it() -> None:
    before = _limits_of(gost16093.TOLERANCES)
    planted = tuple(
        dataclasses.replace(t, value=t.value + 1)
        if (t.quantity, t.pitch) == ("Td2", 1.0) else t
        for t in gost16093.TOLERANCES
    )
    after = _limits_of(planted)
    # Td2 at pitch 1 is read by the 6g d2_min of M6 and M7 and nothing else.
    assert {k for k in before if before[k] != after[k]} == {"bolt M6", "bolt M7"}
    for size in ("M6", "M7"):
        assert after[f"bolt {size}"][3] == round(before[f"bolt {size}"][3] - 0.001, 3)
        assert after[f"bolt {size}"][:3] == before[f"bolt {size}"][:3]


def test_a_size_missing_a_needed_term_gets_no_row_and_the_other_side_keeps_its_row() -> None:
    no_es = tuple(t for t in gost16093.TOLERANCES if (t.quantity, t.pitch) != ("es", 1.75))
    bolts, nuts = gost16093.derive_limits(iso724.BASIC, no_es)
    assert "M12" not in {b.size for b in bolts}
    assert "M12" in {n.size for n in nuts}
    assert (len(bolts), len(nuts)) == (14, 15)
    no_range = tuple(t for t in gost16093.TOLERANCES if (t.quantity, t.pitch) != ("TD2", 2.5))
    assert {n.size for n in gost16093.derive_limits(iso724.BASIC, no_range)[1]} == {
        n.size for n in gost16093.NUT_LIMITS
    } - {"M18", "M20"}


def test_the_range_bounds_are_over_x_up_to_y() -> None:
    # No shipped size lies on a bound (read 5), so the convention is pinned on a planted size:
    # 2.8 belongs to "over 1.4 up to 2.8" (pitch 0.4 has a term there), 1.4 does not.
    def bolts_of(d: float) -> tuple[BoltLimits, ...]:
        row = dataclasses.replace(_BASIC["M2"], d=d, size="planted")
        return gost16093.derive_limits([row], gost16093.TOLERANCES)[0]

    assert len(bolts_of(2.8)) == 1
    assert bolts_of(1.4) == ()
    assert bolts_of(2.8001) == ()


# The ISO 4014 under-head fillet radii (R1, L14 amendment): cited, and copied kernel-free.
def test_the_fillet_rows_are_the_14_gost_r_iso_4014_rows_and_have_no_m7() -> None:
    assert [row.size for row in iso4014.FILLETS] == [
        "M2", "M2.5", "M3", "M3.5", "M4", "M5", "M6", "M8", "M10", "M12", "M14", "M16", "M18",
        "M20",
    ]
    assert {row.size for row in iso4014.FILLETS if row.source.table == "Table 2"} == {
        "M3.5", "M14", "M18",
    }
    assert all(row.source.status == "verified" for row in iso4014.FILLETS)
    assert all(row.pitch == PITCH[row.size] for row in iso4014.FILLETS)


def test_a_fillet_row_cites_the_national_text_with_the_iso_edition_it_adopts() -> None:
    assert {row.source.document() for row in iso4014.FILLETS} == {
        "GOST R ISO 4014-2013 (ISO 4014:2011)"
    }
    m6 = next(row for row in iso4014.FILLETS if row.size == "M6")
    assert m6.source.cite() == "GOST R ISO 4014-2013 (ISO 4014:2011) Table 1, column M6"
    assert m6.r_min == 0.25


def test_phase_4_iso_4014_rows_keep_their_2022_citation() -> None:
    sources = [
        *(row.source for row in iso4014.HEADS),
        *(row.source for row in iso4014.BANDS),
        *(row.source for row in iso4014.CELLS),
    ]
    assert {source.document() for source in sources} == {"ISO 4014:2022"}


def _fillet_copy() -> dict[tuple[float, float], float]:
    diameters = {size.label: size.d for size in SIZES}
    return {(diameters[row.size], row.pitch): row.r_min for row in iso4014.FILLETS}


def test_the_kernel_free_fillet_copy_equals_the_cited_rows() -> None:
    assert _fillet_copy() == FILLET_R


def test_a_planted_fillet_mismatch_names_the_key() -> None:
    planted = dict(FILLET_R)
    planted[6.0, 1.0] = 0.3
    differing = [key for key in planted.keys() | _fillet_copy().keys()
                 if planted.get(key) != _fillet_copy().get(key)]
    assert differing == [(6.0, 1.0)]


def test_a_bolt_gets_the_cited_fillet_only_on_a_row_with_a_long_enough_shank() -> None:
    assert fillet_radius(6.0, 1.0, 60.0, 40.0) == 0.25
    assert fillet_radius(6.0, 1.0, 60.0, 59.75) == 0.25  # shank exactly r long
    assert fillet_radius(6.0, 1.0, 60.0, 59.76) is None  # shank shorter than r
    assert fillet_radius(6.0, 1.0, 60.0, 60.0) is None  # thread to the head
    assert fillet_radius(6.0, 0.75, 60.0, 40.0) is None  # (d, pitch) off a row
    assert fillet_radius(7.0, 1.0, 60.0, 40.0) is None  # M7 has no row
