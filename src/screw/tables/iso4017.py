"""ISO 4017:2022 hexagon head screws: head values by grade and each size's standard lengths."""

from __future__ import annotations

from screw.tables.rows import HexHead, SeriesLength, Source

# Read from the page image of the purchased copy (Table 1, product grade A, M1,6 to M7),
# 2026-10-11. `s` is the nominal width across flats, equal to its maximum; `k` is the nominal
# head height.
_M6 = Source(standard="ISO 4017", edition="2022", table="Table 1", column="M6", status="verified")

HEADS: tuple[HexHead, ...] = (
    HexHead(
        size="M6",
        grade="A",
        pitch=1.0,
        s=10.0,
        s_min=9.78,
        e_min=11.05,
        k=4.0,
        k_min=3.85,
        k_max=4.15,
        dw_min=8.88,
        source=_M6,
    ),
)

# The M6 column's range between the stepped bold lines of the length block, grade A.
SERIES: tuple[SeriesLength, ...] = tuple(
    SeriesLength(size="M6", length=length, grade="A", source=_M6)
    for length in (12.0, 16.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0)
)
