"""GOST 24705-2004 (ISO 724:1993, MOD) basic diameters: d, d2 and d1 of every coarse size.

L14 reads ISO 724 in this free GOST text. Each 6g and 6H limit adds printed deviations to these
printed values (`gost16093`), so they are shipped as printed and double-entered. The panel does
not print them: it prints the ISO 68-1 basic-profile formulas, and a test asserts the two agree
(R13). The PDF is a download-site copy whose faithfulness to the published GOST is UNVERIFIED.
"""

from __future__ import annotations

from screw.tables.rows import BasicDiameters, Source


def _source(table: str, column: str) -> Source:
    """The page cell a row was read from: the table and the nominal diameter as printed, with
    the decimal comma."""
    return Source(
        standard="GOST 24705", edition="2004", table=table, column=column, status="verified"
    )


# Read from the rendered page images (PDF pages 6 to 8, Table 1) on 2026-10-20, before the owner
# copy was opened. A size's rows are grouped under one printed d, largest pitch first, so the
# coarse row is the first of its group.
BASIC: tuple[BasicDiameters, ...] = (
    BasicDiameters(size="M2", pitch=0.4, d=2.0, d2=1.740, d1=1.567,
                   source=_source("Table 1", "2")),
    BasicDiameters(size="M2.5", pitch=0.45, d=2.5, d2=2.208, d1=2.013,
                   source=_source("Table 1", "2,5")),
    BasicDiameters(size="M3", pitch=0.5, d=3.0, d2=2.675, d1=2.459,
                   source=_source("Table 1", "3")),
    BasicDiameters(size="M3.5", pitch=0.6, d=3.5, d2=3.110, d1=2.850,
                   source=_source("Table 1", "3,5")),
    BasicDiameters(size="M4", pitch=0.7, d=4.0, d2=3.545, d1=3.242,
                   source=_source("Table 1", "4")),
    BasicDiameters(size="M5", pitch=0.8, d=5.0, d2=4.480, d1=4.134,
                   source=_source("Table 1", "5")),
    BasicDiameters(size="M6", pitch=1.0, d=6.0, d2=5.350, d1=4.917,
                   source=_source("Table 1", "6")),
    BasicDiameters(size="M7", pitch=1.0, d=7.0, d2=6.350, d1=5.917,
                   source=_source("Table 1", "7")),
    BasicDiameters(size="M8", pitch=1.25, d=8.0, d2=7.188, d1=6.647,
                   source=_source("Table 1", "8")),
    BasicDiameters(size="M10", pitch=1.5, d=10.0, d2=9.026, d1=8.376,
                   source=_source("Table 1", "10")),
    BasicDiameters(size="M12", pitch=1.75, d=12.0, d2=10.863, d1=10.106,
                   source=_source("Table 1", "12")),
    BasicDiameters(size="M14", pitch=2.0, d=14.0, d2=12.701, d1=11.835,
                   source=_source("Table 1", "14")),
    BasicDiameters(size="M16", pitch=2.0, d=16.0, d2=14.701, d1=13.835,
                   source=_source("Table 1", "16")),
    BasicDiameters(size="M18", pitch=2.5, d=18.0, d2=16.376, d1=15.294,
                   source=_source("Table 1", "18")),
    BasicDiameters(size="M20", pitch=2.5, d=20.0, d2=18.376, d1=17.294,
                   source=_source("Table 1", "20")),
)
