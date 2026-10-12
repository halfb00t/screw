"""Which catalogue row a part is and what to call it: the one calc module reading the tables.

Reached only from `_bolt`, and only inside the function: `screw.params` loads
`screw.calc.thread`, which runs `screw/calc/__init__.py`, so a table import at the top of that
file would put every rebuilt link behind a table (contract 6, tests/test_import_boundaries.py).
"""

from __future__ import annotations

from screw.calc import HEAD, SHANK, InfoRow
from screw.params import BoltParams
from screw.tables.presets import PresetRow, catalogue
from screw.tables.rows import Source


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
    label = f"{sense} ({source.standard}:{source.edition} {source.table})"
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
