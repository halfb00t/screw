"""ISO 4014:2022 hexagon head bolts: heads, the thread length b, and the printed shank cells."""

from __future__ import annotations

from typing import Literal

from screw.tables.rows import HexHead, ShankCell, Source, ThreadBand


def _source(table: str, column: str) -> Source:
    """The page cell a row was read from: the table and the size column as printed, brackets
    and decimal comma included, since the brackets are what marks a second-choice size."""
    return Source(
        standard="ISO 4014", edition="2022", table=table, column=column, status="verified"
    )


# Read from the rendered page images of the purchased copy: Table 1 (product grade A, M1,6 to
# M4), Table 2 (grade A, M5 to M12), Table 3 (grade A, M14 to M24) and Table 4 (grade B, M16 to
# M27), 2026-10-12. `s` is the nominal width across flats, equal to its maximum; `k` is the
# nominal head height. Grade B is held only where a size has a length above 150 mm, which is M16,
# M18 and M20. The head values equal ISO 4017's per size and grade (A3, 04-OWNER-READS.md), but
# they are a separate row with this standard's own citation.
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
            k_max=3.65, dw_min=7.2, source=_source("Table 2", "M5")),
    HexHead(size="M6", grade="A", pitch=1.0, s=10.0, s_min=9.78, e_min=11.05, k=4.0, k_min=3.85,
            k_max=4.15, dw_min=8.88, source=_source("Table 2", "M6")),
    HexHead(size="M7", grade="A", pitch=1.0, s=11.0, s_min=10.73, e_min=12.12, k=4.8, k_min=4.65,
            k_max=4.95, dw_min=9.63, source=_source("Table 2", "(M7)")),
    HexHead(size="M8", grade="A", pitch=1.25, s=13.0, s_min=12.73, e_min=14.38, k=5.3, k_min=5.15,
            k_max=5.45, dw_min=11.63, source=_source("Table 2", "M8")),
    HexHead(size="M10", grade="A", pitch=1.5, s=16.0, s_min=15.73, e_min=17.77, k=6.4, k_min=6.22,
            k_max=6.58, dw_min=14.63, source=_source("Table 2", "M10")),
    HexHead(size="M12", grade="A", pitch=1.75, s=18.0, s_min=17.73, e_min=20.03, k=7.5, k_min=7.32,
            k_max=7.68, dw_min=16.63, source=_source("Table 2", "M12")),
    HexHead(size="M14", grade="A", pitch=2.0, s=21.0, s_min=20.67, e_min=23.36, k=8.8, k_min=8.62,
            k_max=8.98, dw_min=19.64, source=_source("Table 3", "(M14)")),
    HexHead(size="M16", grade="A", pitch=2.0, s=24.0, s_min=23.67, e_min=26.75, k=10.0, k_min=9.82,
            k_max=10.18, dw_min=22.49, source=_source("Table 3", "M16")),
    HexHead(size="M16", grade="B", pitch=2.0, s=24.0, s_min=23.16, e_min=26.17, k=10.0, k_min=9.71,
            k_max=10.29, dw_min=22.0, source=_source("Table 4", "M16")),
    HexHead(size="M18", grade="A", pitch=2.5, s=27.0, s_min=26.67, e_min=30.14, k=11.5,
            k_min=11.285, k_max=11.715, dw_min=25.34, source=_source("Table 3", "(M18)")),
    HexHead(size="M18", grade="B", pitch=2.5, s=27.0, s_min=26.16, e_min=29.56, k=11.5,
            k_min=11.15, k_max=11.85, dw_min=24.85, source=_source("Table 4", "(M18)")),
    HexHead(size="M20", grade="A", pitch=2.5, s=30.0, s_min=29.67, e_min=33.53, k=12.5,
            k_min=12.285, k_max=12.715, dw_min=28.19, source=_source("Table 3", "M20")),
    HexHead(size="M20", grade="B", pitch=2.5, s=30.0, s_min=29.16, e_min=32.95, k=12.5,
            k_min=12.15, k_max=12.85, dw_min=27.7, source=_source("Table 4", "M20")),
)

# The b (ref.) row of each size's grade A table: b for l <= 125 and, where the table prints a
# second row, c for 125 < l <= 200. Tables 1 and 2 print only the first row. Table 4's dashes are
# not entered: its grade B values equal the grade A ones of the same size.
BANDS: tuple[ThreadBand, ...] = (
    ThreadBand(size="M2", b_short=10.0, b_long=None, source=_source("Table 1", "M2")),
    ThreadBand(size="M2.5", b_short=11.0, b_long=None, source=_source("Table 1", "M2,5")),
    ThreadBand(size="M3", b_short=12.0, b_long=None, source=_source("Table 1", "M3")),
    ThreadBand(size="M3.5", b_short=13.0, b_long=None, source=_source("Table 1", "(M3,5)")),
    ThreadBand(size="M4", b_short=14.0, b_long=None, source=_source("Table 1", "M4")),
    ThreadBand(size="M5", b_short=16.0, b_long=None, source=_source("Table 2", "M5")),
    ThreadBand(size="M6", b_short=18.0, b_long=None, source=_source("Table 2", "M6")),
    ThreadBand(size="M7", b_short=20.0, b_long=None, source=_source("Table 2", "(M7)")),
    ThreadBand(size="M8", b_short=22.0, b_long=None, source=_source("Table 2", "M8")),
    ThreadBand(size="M10", b_short=26.0, b_long=None, source=_source("Table 2", "M10")),
    ThreadBand(size="M12", b_short=30.0, b_long=None, source=_source("Table 2", "M12")),
    ThreadBand(size="M14", b_short=34.0, b_long=40.0, source=_source("Table 3", "(M14)")),
    ThreadBand(size="M16", b_short=38.0, b_long=44.0, source=_source("Table 3", "M16")),
    ThreadBand(size="M18", b_short=42.0, b_long=48.0, source=_source("Table 3", "(M18)")),
    ThreadBand(size="M20", b_short=46.0, b_long=52.0, source=_source("Table 3", "M20")),
)

# Each size's white cells between the stepped bold lines, as the page prints them:
# (size, grade, table, column, ((length, ls,min, lg,max), ...)). A size whose lengths pass 150 mm
# has a second run, grade B, from Table 4 (the 150 mm row of Table 3 is the last grade A one).
# The cells are stored, not computed from b (RESEARCH Pitfall 5): a test holds each to
# lg,max = l - b and ls,min = lg,max - 5 P, which would be circular if they were derived here.
_Run = tuple[str, Literal["A", "B"], str, str, tuple[tuple[float, float, float], ...]]
_RUNS: tuple[_Run, ...] = (
    ("M2", "A", "Table 1", "M2", ((16, 4.0, 6.0), (20, 8.0, 10.0))),
    ("M2.5", "A", "Table 1", "M2,5", ((16, 2.75, 5.0), (20, 6.75, 9.0), (25, 11.75, 14.0))),
    ("M3", "A", "Table 1", "M3", ((20, 5.5, 8.0), (25, 10.5, 13.0), (30, 15.5, 18.0))),
    ("M3.5", "A", "Table 1", "(M3,5)",
     ((20, 4.0, 7.0), (25, 9.0, 12.0), (30, 14.0, 17.0), (35, 19.0, 22.0))),
    ("M4", "A", "Table 1", "M4",
     ((25, 7.5, 11.0), (30, 12.5, 16.0), (35, 17.5, 21.0), (40, 22.5, 26.0))),
    ("M5", "A", "Table 2", "M5",
     ((25, 5.0, 9.0), (30, 10.0, 14.0), (35, 15.0, 19.0), (40, 20.0, 24.0), (45, 25.0, 29.0),
      (50, 30.0, 34.0))),
    ("M6", "A", "Table 2", "M6",
     ((30, 7.0, 12.0), (35, 12.0, 17.0), (40, 17.0, 22.0), (45, 22.0, 27.0), (50, 27.0, 32.0),
      (55, 32.0, 37.0), (60, 37.0, 42.0))),
    ("M7", "A", "Table 2", "(M7)",
     ((35, 10.0, 15.0), (40, 15.0, 20.0), (45, 20.0, 25.0), (50, 25.0, 30.0), (55, 30.0, 35.0),
      (60, 35.0, 40.0), (65, 40.0, 45.0), (70, 45.0, 50.0))),
    ("M8", "A", "Table 2", "M8",
     ((40, 11.75, 18.0), (45, 16.75, 23.0), (50, 21.75, 28.0), (55, 26.75, 33.0),
      (60, 31.75, 38.0), (65, 36.75, 43.0), (70, 41.75, 48.0), (80, 51.75, 58.0))),
    ("M10", "A", "Table 2", "M10",
     ((45, 11.5, 19.0), (50, 16.5, 24.0), (55, 21.5, 29.0), (60, 26.5, 34.0), (65, 31.5, 39.0),
      (70, 36.5, 44.0), (80, 46.5, 54.0), (90, 56.5, 64.0), (100, 66.5, 74.0))),
    ("M12", "A", "Table 2", "M12",
     ((50, 11.25, 20.0), (55, 16.25, 25.0), (60, 21.25, 30.0), (65, 26.25, 35.0),
      (70, 31.25, 40.0), (80, 41.25, 50.0), (90, 51.25, 60.0), (100, 61.25, 70.0),
      (110, 71.25, 80.0), (120, 81.25, 90.0))),
    ("M14", "A", "Table 3", "(M14)",
     ((55, 11.0, 21.0), (60, 16.0, 26.0), (65, 21.0, 31.0), (70, 26.0, 36.0), (80, 36.0, 46.0),
      (90, 46.0, 56.0), (100, 56.0, 66.0), (110, 66.0, 76.0), (120, 76.0, 86.0),
      (130, 80.0, 90.0), (140, 90.0, 100.0))),
    ("M16", "A", "Table 3", "M16",
     ((65, 17.0, 27.0), (70, 22.0, 32.0), (80, 32.0, 42.0), (90, 42.0, 52.0), (100, 52.0, 62.0),
      (110, 62.0, 72.0), (120, 72.0, 82.0), (130, 76.0, 86.0), (140, 86.0, 96.0),
      (150, 96.0, 106.0))),
    ("M16", "B", "Table 4", "M16", ((160, 106.0, 116.0),)),
    ("M18", "A", "Table 3", "(M18)",
     ((70, 15.5, 28.0), (80, 25.5, 38.0), (90, 35.5, 48.0), (100, 45.5, 58.0), (110, 55.5, 68.0),
      (120, 65.5, 78.0), (130, 69.5, 82.0), (140, 79.5, 92.0), (150, 89.5, 102.0))),
    ("M18", "B", "Table 4", "(M18)", ((160, 99.5, 112.0), (180, 119.5, 132.0))),
    ("M20", "A", "Table 3", "M20",
     ((80, 21.5, 34.0), (90, 31.5, 44.0), (100, 41.5, 54.0), (110, 51.5, 64.0), (120, 61.5, 74.0),
      (130, 65.5, 78.0), (140, 75.5, 88.0), (150, 85.5, 98.0))),
    ("M20", "B", "Table 4", "M20",
     ((160, 95.5, 108.0), (180, 115.5, 128.0), (200, 135.5, 148.0))),
)

CELLS: tuple[ShankCell, ...] = tuple(
    ShankCell(
        size=size, length=float(length), grade=grade, ls_min=ls_min, lg_max=lg_max,
        source=_source(table, column),
    )
    for size, grade, table, column, cells in _RUNS
    for length, ls_min, lg_max in cells
)
