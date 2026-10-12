"""ISO 4017:2022 hexagon head screws: head values by grade and each size's standard lengths."""

from __future__ import annotations

from typing import Literal

from screw.tables.rows import HexHead, SeriesLength, Source


def _source(table: str, column: str) -> Source:
    """The page cell a row was read from: the table and the size column as printed, brackets
    and decimal comma included, since the brackets are what marks a second-choice size."""
    return Source(
        standard="ISO 4017", edition="2022", table=table, column=column, status="verified"
    )


# Read from the rendered page images of the purchased copy: Table 1 (product grade A, M1,6 to
# M7), Table 2 (grade A, M8 to M24) and Table 3 (grade B, M16 to M36), 2026-10-11 and 2026-10-12.
# `s` is the nominal width across flats, equal to its maximum; `k` is the nominal head height.
# Grade B is held only where a size has a length above 150 mm, which is M16, M18 and M20.
HEADS: tuple[HexHead, ...] = (
    HexHead(size="M2", grade="A", pitch=0.4, s=4.0, s_min=3.82, e_min=4.32, k=1.4, k_min=1.275,
            k_max=1.525, dw_min=3.34, source=_source("Table 1", "M2")),
    HexHead(size="M2.5", grade="A", pitch=0.45, s=5.0, s_min=4.82, e_min=5.45, k=1.7, k_min=1.575,
            k_max=1.825, dw_min=4.34, source=_source("Table 1", "M2,5")),
    HexHead(size="M3", grade="A", pitch=0.5, s=5.5, s_min=5.32, e_min=6.01, k=2.0, k_min=1.875,
            k_max=2.125, dw_min=4.84, source=_source("Table 1", "M3")),
    HexHead(size="M3.5", grade="A", pitch=0.6, s=6.0, s_min=5.82, e_min=6.58, k=2.4, k_min=2.275,
            k_max=2.525, dw_min=5.34, source=_source("Table 1", "(M3,5)")),
    HexHead(size="M4", grade="A", pitch=0.7, s=7.0, s_min=6.78, e_min=7.66, k=2.8, k_min=2.675,
            k_max=2.925, dw_min=6.2, source=_source("Table 1", "M4")),
    HexHead(size="M5", grade="A", pitch=0.8, s=8.0, s_min=7.78, e_min=8.79, k=3.5, k_min=3.35,
            k_max=3.65, dw_min=7.2, source=_source("Table 1", "M5")),
    HexHead(size="M6", grade="A", pitch=1.0, s=10.0, s_min=9.78, e_min=11.05, k=4.0, k_min=3.85,
            k_max=4.15, dw_min=8.88, source=_source("Table 1", "M6")),
    HexHead(size="M7", grade="A", pitch=1.0, s=11.0, s_min=10.73, e_min=12.12, k=4.8, k_min=4.65,
            k_max=4.95, dw_min=9.63, source=_source("Table 1", "(M7)")),
    HexHead(size="M8", grade="A", pitch=1.25, s=13.0, s_min=12.73, e_min=14.38, k=5.3, k_min=5.15,
            k_max=5.45, dw_min=11.63, source=_source("Table 2", "M8")),
    HexHead(size="M10", grade="A", pitch=1.5, s=16.0, s_min=15.73, e_min=17.77, k=6.4, k_min=6.22,
            k_max=6.58, dw_min=14.63, source=_source("Table 2", "M10")),
    HexHead(size="M12", grade="A", pitch=1.75, s=18.0, s_min=17.73, e_min=20.03, k=7.5, k_min=7.32,
            k_max=7.68, dw_min=16.63, source=_source("Table 2", "M12")),
    HexHead(size="M14", grade="A", pitch=2.0, s=21.0, s_min=20.67, e_min=23.36, k=8.8, k_min=8.62,
            k_max=8.98, dw_min=19.64, source=_source("Table 2", "(M14)")),
    HexHead(size="M16", grade="A", pitch=2.0, s=24.0, s_min=23.67, e_min=26.75, k=10.0, k_min=9.82,
            k_max=10.18, dw_min=22.49, source=_source("Table 2", "M16")),
    HexHead(size="M16", grade="B", pitch=2.0, s=24.0, s_min=23.16, e_min=26.17, k=10.0, k_min=9.71,
            k_max=10.29, dw_min=22.0, source=_source("Table 3", "M16")),
    HexHead(size="M18", grade="A", pitch=2.5, s=27.0, s_min=26.67, e_min=30.14, k=11.5,
            k_min=11.285, k_max=11.715, dw_min=25.34, source=_source("Table 2", "(M18)")),
    HexHead(size="M18", grade="B", pitch=2.5, s=27.0, s_min=26.16, e_min=29.56, k=11.5,
            k_min=11.15, k_max=11.85, dw_min=24.85, source=_source("Table 3", "(M18)")),
    HexHead(size="M20", grade="A", pitch=2.5, s=30.0, s_min=29.67, e_min=33.53, k=12.5,
            k_min=12.285, k_max=12.715, dw_min=28.19, source=_source("Table 2", "M20")),
    HexHead(size="M20", grade="B", pitch=2.5, s=30.0, s_min=29.16, e_min=32.95, k=12.5,
            k_min=12.15, k_max=12.85, dw_min=27.7, source=_source("Table 3", "M20")),
)

# Each size's range of standard lengths between the stepped bold lines of the length block, read
# from the same pages: (size, grade, table, column, lengths). A size whose lengths pass 150 mm has
# a second run, grade B, from Table 3 (the 150 mm row of Table 2 is the last grade A one).
_RUNS: tuple[tuple[str, Literal["A", "B"], str, str, tuple[float, ...]], ...] = (
    ("M2", "A", "Table 1", "M2", (4, 5, 6, 8, 10, 12, 16, 20)),
    ("M2.5", "A", "Table 1", "M2,5", (5, 6, 8, 10, 12, 16, 20, 25)),
    ("M3", "A", "Table 1", "M3", (6, 8, 10, 12, 16, 20, 25, 30)),
    ("M3.5", "A", "Table 1", "(M3,5)", (8, 10, 12, 16, 20, 25, 30, 35)),
    ("M4", "A", "Table 1", "M4", (8, 10, 12, 16, 20, 25, 30, 35, 40)),
    ("M5", "A", "Table 1", "M5", (10, 12, 16, 20, 25, 30, 35, 40, 45, 50)),
    ("M6", "A", "Table 1", "M6", (12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60)),
    ("M7", "A", "Table 1", "(M7)", (16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70)),
    ("M8", "A", "Table 2", "M8", (16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80)),
    ("M10", "A", "Table 2", "M10", (20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100)),
    ("M12", "A", "Table 2", "M12",
     (25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100, 110, 120)),
    ("M14", "A", "Table 2", "(M14)",
     (30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100, 110, 120, 130, 140)),
    ("M16", "A", "Table 2", "M16",
     (30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100, 110, 120, 130, 140, 150)),
    ("M16", "B", "Table 3", "M16", (160,)),
    ("M18", "A", "Table 2", "(M18)",
     (35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100, 110, 120, 130, 140, 150)),
    ("M18", "B", "Table 3", "(M18)", (160, 180)),
    ("M20", "A", "Table 2", "M20",
     (40, 45, 50, 55, 60, 65, 70, 80, 90, 100, 110, 120, 130, 140, 150)),
    ("M20", "B", "Table 3", "M20", (160, 180, 200)),
)

SERIES: tuple[SeriesLength, ...] = tuple(
    SeriesLength(size=size, length=float(length), grade=grade, source=_source(table, column))
    for size, grade, table, column, lengths in _RUNS
    for length in lengths
)
