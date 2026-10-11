"""Which catalogue row a part is and what to call it: the one calc module reading the tables.

Reached only from `_bolt`, and only inside the function: `screw.params` loads
`screw.calc.thread`, which runs `screw/calc/__init__.py`, so a table import at the top of that
file would put every rebuilt link behind a table (contract 6, tests/test_import_boundaries.py).
"""

from __future__ import annotations

from screw.params import BoltParams
from screw.tables.presets import PresetRow, catalogue


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
