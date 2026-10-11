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

from screw.tables.iso262 import SIZES
from screw.tables.iso4017 import HEADS, SERIES
from screw.tables.rows import HexHead, Source

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
    sources: tuple[Source, ...]

    def citation(self) -> str:
        """The distinct `Source.cite()` strings of the row, in order, joined with `; `."""
        return "; ".join(dict.fromkeys(source.cite() for source in self.sources))


@cache
def catalogue() -> tuple[PresetRow, ...]:
    """ISO 4017 rows first, then ISO 4014; by diameter, then length, ascending."""
    sizes = {size.label: size for size in SIZES}
    heads = {(head.size, head.grade): head for head in HEADS}
    rows: list[PresetRow] = []
    for entry in sorted(SERIES, key=lambda e: (sizes[e.size].d, e.length)):
        size = sizes[entry.size]
        head = heads[entry.size, entry.grade]
        length = f"{entry.length:g}"
        # Second-choice sizes carry their brackets in the display and the picker (D-28); the
        # designation never does, and prints the decimal sign the standard prints (a comma).
        shown = f"({size.label})" if size.choice == 2 else size.label
        rows.append(
            PresetRow(
                id=f"iso4017:{size.label}x{length}",
                standard="ISO 4017",
                edition="2022",
                size=size.label,
                choice=size.choice,
                length=entry.length,
                grade=entry.grade,
                display=f"ISO 4017 {shown} \u00d7 {length}",
                designation=(
                    f"Hexagon head screw ISO 4017 - {size.label.replace('.', ',')} x {length}"
                ),
                picker=("ISO 4017", shown, length),
                # thread_length = length: the thread runs the full length (D-07).
                fields=(
                    ("d", size.d),
                    ("pitch", size.pitch),
                    ("length", entry.length),
                    ("s", head.s),
                    ("k", head.k),
                    ("thread_length", entry.length),
                ),
                head=head,
                sources=(size.source, head.source, entry.source),
            )
        )
    return tuple(rows)


@cache
def _by_id() -> dict[str, PresetRow]:
    return {row.id: row for row in catalogue()}


def expand(preset_id: str) -> dict[str, float] | None:
    """The millimetre fields of one row, or None for an id that is not in the catalogue.

    Ids are case-sensitive: `iso4017:M6x20` is a row, `iso4017:m6x20` is not.
    """
    row = _by_id().get(preset_id)
    return None if row is None else dict(row.fields)
