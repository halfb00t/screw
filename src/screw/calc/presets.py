"""Which catalogue row a part is and what to call it: the one calc module reading the tables.

Reached only from `_bolt`, and only inside the function: `screw.params` loads
`screw.calc.thread`, which runs `screw/calc/__init__.py`, so a table import at the top of that
file would put every rebuilt link behind a table (contract 6, tests/test_import_boundaries.py).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field

from screw.calc import HEAD, LIMITS, NUT, SHANK, Counterpart, InfoRow
from screw.params import KINDS, BoltParams, FastenerParams, NutParams
from screw.tables import gost16093, iso262, iso4017, iso4032
from screw.tables.presets import NutPresetRow, PresetRow, catalogue, expand_nut, nut_catalogue
from screw.tables.presets import expand as expand_row
from screw.tables.rows import Source

# The wrench size the withdrawn DIN 931 and DIN 933 gave the three sizes where it differs from the
# ISO one, in mm (D-20, INFO-05). Read from two independent web pages that agree, MEDIUM
# confidence, not from the purchased text: Eurolink FSS, "DIN 933 vs. ISO 4017 and DIN 931 vs.
# ISO 4014", and Wermac, "metric hex bolt dimensions" (04-RESEARCH.md Sources). The ISO side of the
# note is never typed here: it is the matched row's own `s`. This is the only DIN text in v1;
# DIN aliases are v2 (TABL-08).
WITHDRAWN_DIN_WRENCH_MM: dict[str, float] = {"M10": 17.0, "M12": 19.0, "M14": 22.0}

# The withdrawn DIN standard each ISO one replaced, for the wrench note.
WITHDRAWN_DIN: dict[str, str] = {"ISO 4017": "DIN 933", "ISO 4014": "DIN 931"}


def match(p: BoltParams) -> PresetRow | None:
    """The first catalogue row whose every field equals `p`'s, or None (D-09).

    Exact float equality, no tolerance and no nearest row: the table values and the values a URL
    carries are the same decimal literals, so a part either is the row or is not (L02).
    `left_hand` is not a row field, so a left-hand part matches its row too.
    """
    for row in catalogue():
        if all(getattr(p, name) == value for name, value in row.fields):
            return row
    return None


def designation_for(p: BoltParams, row: PresetRow) -> str | None:
    """The row's designation for a right-hand part; None for a left-hand one.

    Clause 7 of ISO 4014 and ISO 4017 gives no left-hand form (04-OWNER-READS.md), so the
    designation is withheld rather than invented (TABL-07, L02).
    """
    return None if p.left_hand else row.designation


def _row_value(key: str, sense: str, value: float, source: Source, group: str) -> InfoRow:
    """One cited row value; the label carries its sense and the page it was read from (D-18)."""
    label = f"{sense} ({source.document()} {source.table})"
    return InfoRow(key=key, label=label, value=value, unit="mm", group=group)


def row_values(row: PresetRow) -> list[InfoRow]:
    """The cited values of a matched row: the head's five, then ISO 4014's b, lg,max and ls,min.

    Each value is read from the stored record it came from and labelled with that record's own
    source, so a row's head, band and cell can cite different tables (D-18, INFO-03). The
    geometric across-corners stays a separate row beside the standard's `e,min` (PITFALLS C7).
    """
    head = row.head
    rows = [
        _row_value("s_min", "Across flats, min", head.s_min, head.source, HEAD),
        _row_value("e_min", "Across corners, min", head.e_min, head.source, HEAD),
        _row_value("k_max", "Head height, max", head.k_max, head.source, HEAD),
        _row_value("k_min", "Head height, min", head.k_min, head.source, HEAD),
        _row_value("dw_min", "Bearing face diameter, min", head.dw_min, head.source, HEAD),
    ]
    if row.band is not None and row.cell is not None:
        # The catalogue sets an ISO 4014 row's thread_length to its band's b (a test pins that
        # for every row), so reading the field avoids repeating the length-band rule here.
        b = dict(row.fields)["thread_length"]
        rows += [
            _row_value("b", "Thread length b, ref", b, row.band.source, SHANK),
            _row_value("lg_max", "Grip length lg, max", row.cell.lg_max, row.cell.source, SHANK),
            _row_value("ls_min", "Plain shank length ls, min", row.cell.ls_min, row.cell.source,
                       SHANK),
        ]
    return rows


def notes(row: PresetRow) -> list[str]:
    """The one-line notes of a matched row: its product grade, then the wrench-size remark.

    The grade rule is the standards' (A up to 150 mm and 10 d, else B), read off the row's own
    grade and standard. The wrench note exists only where the withdrawn DIN size differs, which
    is M10, M12 and M14; its ISO figure is the row's `s`, its DIN figure a cited constant (D-20).
    """
    cite = f"{row.standard}:{row.edition}"
    limit = "l \u2264 150 mm and l \u2264 10 d" if row.grade == "A" else "l > 150 mm"
    result = [f"product grade {row.grade} ({cite}: {limit})"]
    din = WITHDRAWN_DIN_WRENCH_MM.get(row.size)
    if din is not None:
        result.append(f"wrench size {row.head.s:g} mm ({cite}); "
                      f"the withdrawn {WITHDRAWN_DIN[row.standard]} used {din:g} mm")
    return result


def match_nut(p: NutParams) -> NutPresetRow | None:
    """The nut row whose d, pitch, s and m all equal `p`'s, or None (D-17, INFO-01).

    Exact float equality, no tolerance and no nearest row (L02). Never `clearance` and never
    `left_hand`: neither is a row field, so a nut at any clearance, of either hand, is its row.
    """
    for row in nut_catalogue():
        if all(getattr(p, name) == value for name, value in row.fields):
            return row
    return None


def nut_designation_for(p: NutParams, row: NutPresetRow) -> str | None:
    """The row's designation for a right-hand nut; None for a left-hand one.

    Clause 5 of GOST ISO 4032-2014 gives no left-hand form (05-OWNER-READS.md, Designation), so
    the designation is withheld rather than invented (L02).
    """
    return None if p.left_hand else row.designation


def nut_row_values(row: NutPresetRow) -> list[InfoRow]:
    """The six cited values of a matched nut row, each labelled with the table it was read from.

    `e`, `mw` and `dw` are reported (D-15); the `c` and `da` columns the table stores are not.
    """
    nut = row.nut
    return [
        _row_value("s_min", "Across flats, min", nut.s_min, nut.source, NUT),
        _row_value("e_min", "Across corners, min", nut.e_min, nut.source, NUT),
        _row_value("m_max", "Height, max", nut.m_max, nut.source, NUT),
        _row_value("m_min", "Height, min", nut.m_min, nut.source, NUT),
        _row_value("mw_min", "Wrench height, min", nut.mw_min, nut.source, NUT),
        _row_value("dw_min", "Bearing face diameter, min", nut.dw_min, nut.source, NUT),
    ]


def nut_notes(row: NutPresetRow) -> list[str]:
    """The one note of a matched nut row: its product grade, by the scope clause's rule.

    Grade A up to M16 and B above, confirmed on the rendered page of GOST ISO 4032-2014 (05-06).
    """
    limit = "D \u2264 16 mm" if row.nut.grade == "A" else "D > 16 mm"
    return [f"product grade {row.nut.grade} ({row.nut.source.document()}: {limit})"]


# L14: the 6g and 6H limits are derived, not read: the GOST 24705-2004 basic value plus the printed
# GOST 16093-2004 terms. The label names both designations and the ISO editions they rest on, and
# no label names ISO 724:2023 or ISO 965-2:2024, which nobody read (L14 Citations).
LIMITS_SOURCE = ("derived: GOST 24705-2004 (ISO 724:1993, MOD) + "
                 "GOST 16093-2004 (based on ISO 965-1:1998 and ISO 965-3:1998)")


def _size_label(d: float, pitch: float) -> str | None:
    """The ISO 262 label whose d and pitch both equal these exactly, or None (INFO-02, L02).

    Exact float equality, no tolerance and no nearest size: a limit printed for a part that is
    one float off the size would be a number someone cuts metal to (T-05-20).
    """
    for size in iso262.SIZES:
        if size.d == d and size.pitch == pitch:
            return size.label
    return None


def _limit_rows(values: list[tuple[str, str, float]]) -> list[InfoRow]:
    return [InfoRow(key=key, label=f"{sense} ({LIMITS_SOURCE})", value=value, unit="mm",
                    group=LIMITS) for key, sense, value in values]


def bolt_limits_for(d: float, pitch: float) -> list[InfoRow]:
    """The four 6g rows of the exact ISO 262 size (d, pitch), or [] off a size or a limits row."""
    label = _size_label(d, pitch)
    for limits in gost16093.BOLT_LIMITS:
        if limits.size == label:
            return _limit_rows([
                ("d_max", "Major diameter, max, 6g", limits.d_max),
                ("d_min", "Major diameter, min, 6g", limits.d_min),
                ("d2_max", "Pitch diameter, max, 6g", limits.d2_max),
                ("d2_min", "Pitch diameter, min, 6g", limits.d2_min)])
    return []


def nut_limits_for(d: float, pitch: float) -> list[InfoRow]:
    """The four 6H rows of the exact ISO 262 size (d, pitch), or [] off a size or a limits row."""
    label = _size_label(d, pitch)
    for limits in gost16093.NUT_LIMITS:
        if limits.size == label:
            return _limit_rows([
                ("D1_min", "Minor diameter, min, 6H", limits.D1_min),
                ("D1_max", "Minor diameter, max, 6H", limits.D1_max),
                ("D2_min", "Pitch diameter, min, 6H", limits.D2_min),
                ("D2_max", "Pitch diameter, max, 6H", limits.D2_max)])
    return []


def counterpart_for(p: FastenerParams) -> tuple[Counterpart, str | None]:
    """The part that mates with `p` and, off a catalogue size, the warning that says what is left.

    d, pitch and left_hand always carry over. When the exact (d, pitch) is a row of the other
    kind's standard, that row's across-flats and height carry too: the nut's `s` and `m` (the
    `m_max` the nut presets take, read 1) for a bolt, the bolt's `s` and `k` for a nut, which
    are the same in both ISO 4017 grades (04-OWNER-READS.md A3). Never `clearance`, `length` or
    `thread_length` (D-02, TYPE-04). Off a row there is no nearest row (L02): the fields the
    counterpart cannot carry stay the target kind's own defaults and the warning names them
    (D-03). The unit is mm; `:g` prints 6.5 and 1 as the page and the CLI print them.
    """
    shared: dict[str, float | bool] = {"d": p.d, "pitch": p.pitch, "left_hand": p.left_hand}
    label = _size_label(p.d, p.pitch)
    where = f"d {p.d:g} pitch {p.pitch:g}"
    if isinstance(p, BoltParams):
        nut = next((n for n in iso4032.NUTS if n.size == label), None)
        if nut is None:
            return (Counterpart(kind=NutParams.kind, fields=shared),
                    f"no GOST ISO 4032-2014 (ISO 4032:2012) row for {where}; "
                    "set s and m on the nut")
        return (Counterpart(kind=NutParams.kind, fields={**shared, "s": nut.s, "m": nut.m_max}),
                None)
    if isinstance(p, NutParams):
        head = next((h for h in iso4017.HEADS if h.size == label), None)
        if head is None:
            return (Counterpart(kind=BoltParams.kind, fields=shared),
                    f"no ISO 4017:2022 row for {where}; "
                    "set s, k, length and thread_length on the bolt")
        return (Counterpart(kind=BoltParams.kind, fields={**shared, "s": head.s, "k": head.k}),
                None)
    raise TypeError(f"no counterpart for kind {p.kind!r}")


# The picker's select labels, in the order a row's `picker` strings answer them (D-10, D-28).
AXES = ["Standard", "Size", "Length"]


class PresetEntry(BaseModel):
    """One catalogue row as the picker and the CLI read it."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(description="the row's stable, case-sensitive id, e.g. iso4017:M6x20")
    display: str = Field(description="the row's text for the badge and the info panel; "
                                     "second-choice sizes are bracketed")
    designation: str = Field(description="the standard's designation of the row, ASCII")
    picker: list[str] = Field(description="the row's display strings, one per axis")
    fields: dict[str, float] = Field(description="the millimetre values picking the row writes")
    citation: str = Field(description="the standards, tables and columns the row came from")


class PresetCatalogue(BaseModel):
    """The preset catalogue of one kind: one document for the page, the API and the CLI (D-10)."""

    model_config = ConfigDict(frozen=True)

    kind: str = Field(description="the kind the catalogue fills")
    axes: list[str] = Field(description="the picker's select labels, in order")
    rows: list[PresetEntry] = Field(description="every row, in catalogue order")


# The nut's picker labels: no length axis, a nut has no length (D-10).
NUT_AXES = ["Standard", "Size"]


@lru_cache
def catalogue_document(kind: str) -> PresetCatalogue:
    """The catalogue document of `kind`; TypeError for a kind without one, like `derive`.

    Built from in-memory rows and cached per kind, so the route costs nothing per request
    and starts no kernel (T-04-20). The frozen result is safe to share between callers.
    """
    model = KINDS.get(kind)
    if model is NutParams:
        return PresetCatalogue(kind=kind, axes=NUT_AXES, rows=[
            PresetEntry(id=row.id, display=row.display, designation=row.designation,
                        picker=list(row.picker), fields=dict(row.fields),
                        citation=row.citation())
            for row in nut_catalogue()])
    if model is not BoltParams:
        raise TypeError(f"no preset catalogue for kind {kind!r}")
    return PresetCatalogue(kind=kind, axes=AXES, rows=[
        PresetEntry(id=row.id, display=row.display, designation=row.designation,
                    picker=list(row.picker), fields=dict(row.fields), citation=row.citation())
        for row in catalogue()])


def expand(kind: str, preset_id: str) -> dict[str, float] | None:
    """The millimetre fields of one row of `kind`'s catalogue, or None for an unknown id.

    A bolt's id is unknown to the nut and the other way round: each kind looks in its own table.
    """
    model = KINDS.get(kind)
    if model is NutParams:
        return expand_nut(preset_id)
    if model is not BoltParams:
        raise TypeError(f"no preset catalogue for kind {kind!r}")
    return expand_row(preset_id)
