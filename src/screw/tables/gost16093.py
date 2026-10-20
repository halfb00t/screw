"""GOST 16093-2004 deviations and tolerances, and the 6g and 6H limits derived from them (L14).

GOST 16093-2004 is based on ISO 965-1:1998 and ISO 965-3:1998 and is not a copy of ISO 965-2. It
prints the fundamental deviations (Table 7) and the tolerances (Tables 3 to 6), not the limits, so
each limit is derived: the GOST 24705-2004 basic value (`iso724`) plus the printed terms, printed
values only. No tolerance formula is used and a term the tables do not print gives no row. The PDF
is a download-site copy whose faithfulness to the published GOST is UNVERIFIED.

Each limit is the exact decimal sum of its addends, converted to float once: no float arithmetic
touches a limit, so no representation error is added to what the part is cut to.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from screw.tables.iso724 import BASIC
from screw.tables.rows import BasicDiameters, BoltLimits, NutLimits, Source, Tolerance

_TO_MM = {"um": Decimal("0.001")}


def _source(table: str, column: str) -> Source:
    """The page cell a value was read from: the table and the column head as printed."""
    return Source(
        standard="GOST 16093", edition="2004", table=table, column=column, status="verified"
    )


def _tolerance(
    quantity: str, grade: str, pitch: float, value: int, table: str,
    d_over: float | None = None, d_upto: float | None = None,
) -> Tolerance:
    return Tolerance(
        quantity=quantity, grade=grade, pitch=pitch, d_over=d_over, d_upto=d_upto, value=value,
        unit="um", source=_source(table, grade),
    )


# Read from the rendered page images (PDF pages 13 to 18) on 2026-10-20, before the owner copy
# was opened. The 12 coarse pitches of M2 to M20, micrometres. Tables 3, 4 and 7 are keyed by
# pitch alone; Tables 5 and 6 by the size's diameter range ("over X up to Y") and pitch. Columns:
# pitch, es of g, Td(6), TD1(6), range over, range up to, Td2(6), TD2(6).
_PRINTED = (
    (0.4, -19, 95, 112, 1.4, 2.8, 67, 90),
    (0.45, -20, 100, 125, 1.4, 2.8, 71, 95),
    (0.5, -20, 106, 140, 2.8, 5.6, 75, 100),
    (0.6, -21, 125, 160, 2.8, 5.6, 85, 112),
    (0.7, -22, 140, 180, 2.8, 5.6, 90, 118),
    (0.8, -24, 150, 200, 2.8, 5.6, 95, 125),
    (1.0, -26, 180, 236, 5.6, 11.2, 112, 150),
    (1.25, -28, 212, 265, 5.6, 11.2, 118, 160),
    (1.5, -32, 236, 300, 5.6, 11.2, 132, 180),
    (1.75, -34, 265, 335, 11.2, 22.4, 150, 200),
    (2.0, -38, 280, 375, 11.2, 22.4, 160, 212),
    (2.5, -42, 335, 450, 11.2, 22.4, 170, 224),
)

TOLERANCES: tuple[Tolerance, ...] = (
    *(_tolerance("es", "g", row[0], row[1], "Table 7") for row in _PRINTED),
    # H is 0 at every pitch (Table 7, internal thread, EI).
    *(_tolerance("EI", "H", row[0], 0, "Table 7") for row in _PRINTED),
    *(_tolerance("Td", "6", row[0], row[2], "Table 3") for row in _PRINTED),
    *(_tolerance("TD1", "6", row[0], row[3], "Table 4") for row in _PRINTED),
    *(_tolerance("Td2", "6", row[0], row[6], "Table 5", row[4], row[5]) for row in _PRINTED),
    *(_tolerance("TD2", "6", row[0], row[7], "Table 6", row[4], row[5]) for row in _PRINTED),
)


def _term(
    tolerances: Iterable[Tolerance], quantity: str, grade: str, row: BasicDiameters
) -> Tolerance | None:
    """The printed term of a size: exact pitch and, for a range table, d in "over X up to Y"."""
    for tolerance in tolerances:
        if (
            tolerance.quantity == quantity
            and tolerance.grade == grade
            and tolerance.pitch == row.pitch
            and (tolerance.d_over is None or tolerance.d_over < row.d)
            and (tolerance.d_upto is None or row.d <= tolerance.d_upto)
        ):
            return tolerance
    return None


def _mm(term: Tolerance) -> Decimal:
    return Decimal(repr(term.value)) * _TO_MM[term.unit]


def derive_limits(
    basic: Iterable[BasicDiameters], tolerances: Iterable[Tolerance]
) -> tuple[tuple[BoltLimits, ...], tuple[NutLimits, ...]]:
    """The 6g and 6H limits of every size that has a basic row and every printed term it needs.

    6g: d_max = d + es, d_min = d_max - Td(6), d2_max = d2 + es, d2_min = d2_max - Td2(6).
    6H: D1_min = D1 + EI, D1_max = D1_min + TD1(6), D2_min = D2 + EI, D2_max = D2_min + TD2(6).
    """
    terms = tuple(tolerances)
    bolts: list[BoltLimits] = []
    nuts: list[NutLimits] = []
    for row in basic:
        d, d2, d1 = Decimal(repr(row.d)), Decimal(repr(row.d2)), Decimal(repr(row.d1))
        es, td, td2 = _term(terms, "es", "g", row), _term(terms, "Td", "6", row), _term(
            terms, "Td2", "6", row
        )
        if es and td and td2:
            d_max = d + _mm(es)
            d2_max = d2 + _mm(es)
            bolts.append(BoltLimits(
                size=row.size, pitch=row.pitch,
                d_max=float(d_max), d_min=float(d_max - _mm(td)),
                d2_max=float(d2_max), d2_min=float(d2_max - _mm(td2)),
                sources=(row.source, es.source, td.source, td2.source),
            ))
        ei, big_td1, big_td2 = (
            _term(terms, "EI", "H", row), _term(terms, "TD1", "6", row),
            _term(terms, "TD2", "6", row),
        )
        if ei and big_td1 and big_td2:
            d1_min = d1 + _mm(ei)
            d2_min = d2 + _mm(ei)
            nuts.append(NutLimits(
                size=row.size, pitch=row.pitch,
                D1_min=float(d1_min), D1_max=float(d1_min + _mm(big_td1)),
                D2_min=float(d2_min), D2_max=float(d2_min + _mm(big_td2)),
                sources=(row.source, ei.source, big_td1.source, big_td2.source),
            ))
    return tuple(bolts), tuple(nuts)


BOLT_LIMITS, NUT_LIMITS = derive_limits(BASIC, TOLERANCES)
