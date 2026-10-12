"""ISO 262:2023 sizes: nominal diameter, coarse pitch, first or second choice."""

from __future__ import annotations

from screw.tables.rows import Size, Source

# Table 1 of the purchased copy (pages 1 and 2 of the standard), coarse pitch column, read from
# the rendered page images on 2026-10-12. `choice` is the column the diameter stands in: 1 for
# the first-choice column, 2 for the second-choice column (M3.5, M7, M14, M18).
_COARSE = Source(
    standard="ISO 262", edition="2023", table="Table 1", column="Coarse", status="verified"
)

SIZES: tuple[Size, ...] = (
    Size(label="M2", d=2.0, pitch=0.4, choice=1, source=_COARSE),
    Size(label="M2.5", d=2.5, pitch=0.45, choice=1, source=_COARSE),
    Size(label="M3", d=3.0, pitch=0.5, choice=1, source=_COARSE),
    Size(label="M3.5", d=3.5, pitch=0.6, choice=2, source=_COARSE),
    Size(label="M4", d=4.0, pitch=0.7, choice=1, source=_COARSE),
    Size(label="M5", d=5.0, pitch=0.8, choice=1, source=_COARSE),
    Size(label="M6", d=6.0, pitch=1.0, choice=1, source=_COARSE),
    Size(label="M7", d=7.0, pitch=1.0, choice=2, source=_COARSE),
    Size(label="M8", d=8.0, pitch=1.25, choice=1, source=_COARSE),
    Size(label="M10", d=10.0, pitch=1.5, choice=1, source=_COARSE),
    Size(label="M12", d=12.0, pitch=1.75, choice=1, source=_COARSE),
    Size(label="M14", d=14.0, pitch=2.0, choice=2, source=_COARSE),
    Size(label="M16", d=16.0, pitch=2.0, choice=1, source=_COARSE),
    Size(label="M18", d=18.0, pitch=2.5, choice=2, source=_COARSE),
    Size(label="M20", d=20.0, pitch=2.5, choice=1, source=_COARSE),
)
