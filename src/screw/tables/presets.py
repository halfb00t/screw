"""The preset catalogue: a way to fill the millimetre fields from a cited row.

A preset never travels: the part is always rebuilt from the fields alone (TABL-01), so a link
carries `d`, `pitch`, `length`, `s`, `k` and `thread_length` and no preset id. `expand` is a dict
lookup on a closed set of ids, never a path or an expression. Plain frozen dataclasses only;
`screw.calc.presets` turns them into documents (RESEARCH Pattern 3).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from typing import Literal

from screw.tables import iso4014
from screw.tables.iso262 import SIZES
from screw.tables.iso4017 import HEADS, SERIES
from screw.tables.iso4032 import NUTS
from screw.tables.rows import HexHead, HexNut, ShankCell, Size, Source, ThreadBand

# Every key `expand` returns; a test asserts each is a `BoltParams` field so a rename cannot
# drift silently.
FIELD_NAMES = ("d", "pitch", "length", "s", "k", "thread_length")


@dataclass(frozen=True, slots=True, kw_only=True)
class PresetRow:
    id: str
    standard: str
    edition: str
    size: str
    choice: Literal[1, 2]
    length: float
    grade: Literal["A", "B"]
    display: str
    designation: str
    picker: tuple[str, str, str]
    fields: tuple[tuple[str, float], ...]
    head: HexHead
    band: ThreadBand | None  # ISO 4014 rows only: the b of the row's length band
    cell: ShankCell | None  # ISO 4014 rows only: the printed ls,min and lg,max
    sources: tuple[Source, ...]

    def citation(self) -> str:
        """The distinct `Source.cite()` strings of the row, in order, joined with `; `."""
        return "; ".join(dict.fromkeys(source.cite() for source in self.sources))


def _row(
    *, standard: str, noun: str, size: Size, head: HexHead, length: float, thread_length: float,
    band: ThreadBand | None, cell: ShankCell | None, sources: tuple[Source, ...],
) -> PresetRow:
    shown_length = f"{length:g}"
    # Second-choice sizes carry their brackets in the display and the picker (D-28); the
    # designation never does, and prints the decimal sign the standard prints (a comma).
    shown = f"({size.label})" if size.choice == 2 else size.label
    return PresetRow(
        id=f"{standard.replace(' ', '').lower()}:{size.label}x{shown_length}",
        standard=standard,
        edition="2022",
        size=size.label,
        choice=size.choice,
        length=length,
        grade=head.grade,
        display=f"{standard} {shown} \u00d7 {shown_length}",
        designation=(
            f"{noun} {standard} - {size.label.replace('.', ',')} x {shown_length}"
        ),
        picker=(standard, shown, shown_length),
        fields=(
            ("d", size.d),
            ("pitch", size.pitch),
            ("length", length),
            ("s", head.s),
            ("k", head.k),
            ("thread_length", thread_length),
        ),
        head=head,
        band=band,
        cell=cell,
        sources=sources,
    )


@cache
def catalogue() -> tuple[PresetRow, ...]:
    """Every ISO 4017 row, then every ISO 4014 row; by diameter, then length, ascending.

    The order is the tie rule: `calc.presets.match` reports the first equal row, so a part that
    ever equalled a row of each standard would read as ISO 4017, the standard's own "ISO 4017
    recommended" note (CONTEXT discretion). The tie is latent today: an ISO 4017 screw is
    threaded to the head and an ISO 4014 bolt is not, so no two rows share every field.
    """
    sizes = {size.label: size for size in SIZES}
    heads = {(head.size, head.grade): head for head in HEADS}
    rows: list[PresetRow] = []
    for entry in sorted(SERIES, key=lambda e: (sizes[e.size].d, e.length)):
        size = sizes[entry.size]
        head = heads[entry.size, entry.grade]
        rows.append(
            _row(
                standard="ISO 4017", noun="Hexagon head screw", size=size, head=head,
                length=entry.length,
                # thread_length = length: the thread runs the full length (D-07).
                thread_length=entry.length, band=None, cell=None,
                sources=(size.source, head.source, entry.source),
            )
        )
    heads_4014 = {(head.size, head.grade): head for head in iso4014.HEADS}
    bands = {band.size: band for band in iso4014.BANDS}
    for cell in sorted(iso4014.CELLS, key=lambda c: (sizes[c.size].d, c.length)):
        size = sizes[cell.size]
        head = heads_4014[cell.size, cell.grade]
        band = bands[cell.size]
        # b for l <= 125, the second b for 125 < l <= 200; a size with no second b has no
        # length above 125, which a test pins.
        b = band.b_short if cell.length <= 125 else band.b_long
        if b is None:
            # tests/test_tables.py pins that no such cell exists; a table edit that breaks the
            # pin is refused here too, never asserted (`python -O` strips asserts, 04-REVIEW IN-01).
            raise ValueError(f"ISO 4014 {cell.size} x {cell.length:g}: no second b for a length "
                             "above 125 mm")
        rows.append(
            _row(
                standard="ISO 4014", noun="Hexagon head bolt", size=size, head=head,
                length=cell.length, thread_length=b, band=band, cell=cell,
                sources=(size.source, head.source, band.source, cell.source),
            )
        )
    return tuple(rows)


@cache
def _by_id() -> dict[str, PresetRow]:
    return {row.id: row for row in catalogue()}


def expand(preset_id: str) -> dict[str, float] | None:
    """The millimetre fields of one bolt row, or None for an id that is not in the catalogue.

    Ids are case-sensitive: `iso4017:M6x20` is a row, `iso4017:m6x20` is not.
    """
    row = _by_id().get(preset_id)
    return None if row is None else dict(row.fields)


@dataclass(frozen=True, slots=True, kw_only=True)
class NutPresetRow:
    """One GOST ISO 4032-2014 nut size as the picker, the match and the panel read it."""

    id: str
    size: str
    choice: Literal[1, 2]
    display: str
    designation: str
    picker: tuple[str, str]
    fields: tuple[tuple[str, float], ...]
    nut: HexNut
    sources: tuple[Source, ...]

    def citation(self) -> str:
        """The distinct `Source.cite()` strings of the row, in order, joined with `; `."""
        return "; ".join(dict.fromkeys(source.cite() for source in self.sources))


def _nut_row(size: Size, nut: HexNut) -> NutPresetRow:
    # Every nut row is normative (owner ruling 2026-10-20: the 2012 text has no Annex A), so the
    # display carries brackets for an ISO 262 second-choice size and no suffix of any kind.
    shown = f"({size.label})" if size.choice == 2 else size.label
    return NutPresetRow(
        id=f"iso4032:{size.label}",
        size=size.label,
        choice=size.choice,
        display=f"ISO 4032 {shown}",
        # The owner's form (05-OWNER-READS.md, Designation): the noun is the owner's ASCII choice,
        # the decimal sign is the comma the tables print, the property class is left out.
        designation=f"Hexagon regular nut GOST ISO 4032 - {size.label.replace('.', ',')}",
        picker=("ISO 4032", shown),
        fields=(
            ("d", size.d),
            ("pitch", size.pitch),
            ("s", nut.s),
            # m max, the column the owner chose for the height (read 1, option a).
            ("m", nut.m_max),
        ),
        nut=nut,
        sources=(size.source, nut.source),
    )


@cache
def nut_catalogue() -> tuple[NutPresetRow, ...]:
    """Every GOST ISO 4032-2014 row (14: the text prints no M7), by diameter ascending."""
    sizes = {size.label: size for size in SIZES}
    return tuple(_nut_row(sizes[nut.size], nut)
                 for nut in sorted(NUTS, key=lambda n: sizes[n.size].d))


@cache
def _nut_by_id() -> dict[str, NutPresetRow]:
    return {row.id: row for row in nut_catalogue()}


def expand_nut(preset_id: str) -> dict[str, float] | None:
    """The millimetre fields of one nut row, or None for an id that is not in its catalogue.

    Ids are case-sensitive, and a bolt's id is not a nut's: `iso4017:M6x20` is None here.
    """
    row = _nut_by_id().get(preset_id)
    return None if row is None else dict(row.fields)
