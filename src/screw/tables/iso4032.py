"""GOST ISO 4032-2014 hex nuts (ISO 4032:2012, adopted identically): the nut rows M2 to M20.

L14 reads ISO 4032 in this free GOST text in place of a purchased ISO copy; the file keeps the ISO
number because it names the same document. The PDF is a download-site copy whose faithfulness to
the published GOST is UNVERIFIED. The 2012 edition has no Annex A, so every row is normative and
its table is in its Source: Table 1 holds the preferred sizes, Table 2 the additional ones of
limited use (owner ruling 2026-10-20).
"""

from __future__ import annotations

from typing import Literal

from screw.tables.rows import HexNut, Source


def _source(table: str, column: str) -> Source:
    """The page cell a row was read from: the table and the size column as printed, with the
    decimal comma."""
    return Source(
        standard="GOST ISO 4032", edition="2014", table=table, column=column, status="verified"
    )


def _grade(d: float) -> Literal["A", "B"]:
    # Not printed in the table: the scope clause gives grade A up to M16 and B above it.
    return "A" if d <= 16 else "B"


# Read from the rendered page images (PDF pages 7 and 8) on 2026-10-20, before the owner copy was
# opened. `s` is the column printed as nominal = max.
NUTS: tuple[HexNut, ...] = (
    HexNut(size="M2", grade=_grade(2), pitch=0.4, s=4.0, s_min=3.82, e_min=4.32, m_max=1.6,
           m_min=1.35, mw_min=1.1, dw_min=3.1, c_max=0.2, c_min=0.1, da_max=2.3, da_min=2.0,
           source=_source("Table 1", "M2")),
    HexNut(size="M2.5", grade=_grade(2.5), pitch=0.45, s=5.0, s_min=4.82, e_min=5.45, m_max=2.0,
           m_min=1.75, mw_min=1.4, dw_min=4.1, c_max=0.3, c_min=0.1, da_max=2.9, da_min=2.5,
           source=_source("Table 1", "M2,5")),
    HexNut(size="M3", grade=_grade(3), pitch=0.5, s=5.5, s_min=5.32, e_min=6.01, m_max=2.4,
           m_min=2.15, mw_min=1.7, dw_min=4.6, c_max=0.4, c_min=0.15, da_max=3.45, da_min=3.0,
           source=_source("Table 1", "M3")),
    HexNut(size="M3.5", grade=_grade(3.5), pitch=0.6, s=6.0, s_min=5.82, e_min=6.58, m_max=2.8,
           m_min=2.55, mw_min=2.0, dw_min=5.0, c_max=0.4, c_min=0.15, da_max=4.0, da_min=3.5,
           source=_source("Table 2", "M3,5")),
    HexNut(size="M4", grade=_grade(4), pitch=0.7, s=7.0, s_min=6.78, e_min=7.66, m_max=3.2,
           m_min=2.9, mw_min=2.3, dw_min=5.9, c_max=0.4, c_min=0.15, da_max=4.6, da_min=4.0,
           source=_source("Table 1", "M4")),
    HexNut(size="M5", grade=_grade(5), pitch=0.8, s=8.0, s_min=7.78, e_min=8.79, m_max=4.7,
           m_min=4.4, mw_min=3.5, dw_min=6.9, c_max=0.5, c_min=0.15, da_max=5.75, da_min=5.0,
           source=_source("Table 1", "M5")),
    HexNut(size="M6", grade=_grade(6), pitch=1.0, s=10.0, s_min=9.78, e_min=11.05, m_max=5.2,
           m_min=4.9, mw_min=3.9, dw_min=8.9, c_max=0.5, c_min=0.15, da_max=6.75, da_min=6.0,
           source=_source("Table 1", "M6")),
    HexNut(size="M8", grade=_grade(8), pitch=1.25, s=13.0, s_min=12.73, e_min=14.38, m_max=6.8,
           m_min=6.44, mw_min=5.2, dw_min=11.6, c_max=0.6, c_min=0.15, da_max=8.75, da_min=8.0,
           source=_source("Table 1", "M8")),
    HexNut(size="M10", grade=_grade(10), pitch=1.5, s=16.0, s_min=15.73, e_min=17.77, m_max=8.4,
           m_min=8.04, mw_min=6.4, dw_min=14.6, c_max=0.6, c_min=0.15, da_max=10.8, da_min=10.0,
           source=_source("Table 1", "M10")),
    HexNut(size="M12", grade=_grade(12), pitch=1.75, s=18.0, s_min=17.73, e_min=20.03, m_max=10.8,
           m_min=10.37, mw_min=8.3, dw_min=16.6, c_max=0.6, c_min=0.15, da_max=13.0, da_min=12.0,
           source=_source("Table 1", "M12")),
    HexNut(size="M14", grade=_grade(14), pitch=2.0, s=21.0, s_min=20.67, e_min=23.36, m_max=12.8,
           m_min=12.1, mw_min=9.7, dw_min=19.6, c_max=0.6, c_min=0.15, da_max=15.1, da_min=14.0,
           source=_source("Table 2", "M14")),
    HexNut(size="M16", grade=_grade(16), pitch=2.0, s=24.0, s_min=23.67, e_min=26.75, m_max=14.8,
           m_min=14.1, mw_min=11.3, dw_min=22.5, c_max=0.8, c_min=0.2, da_max=17.3, da_min=16.0,
           source=_source("Table 1", "M16")),
    HexNut(size="M18", grade=_grade(18), pitch=2.5, s=27.0, s_min=26.16, e_min=29.56, m_max=15.8,
           m_min=15.1, mw_min=12.1, dw_min=24.9, c_max=0.8, c_min=0.2, da_max=19.5, da_min=18.0,
           source=_source("Table 2", "M18")),
    HexNut(size="M20", grade=_grade(20), pitch=2.5, s=30.0, s_min=29.16, e_min=32.95, m_max=18.0,
           m_min=16.9, mw_min=13.5, dw_min=27.7, c_max=0.8, c_min=0.2, da_max=21.6, da_min=20.0,
           source=_source("Table 1", "M20")),
)
