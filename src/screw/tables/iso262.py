"""ISO 262:2023 sizes: nominal diameter, coarse pitch, first or second choice."""

from __future__ import annotations

from screw.tables.rows import Size, Source

# Read from the page image of the purchased copy (Table 1, continued page), 2026-10-11.
SIZES: tuple[Size, ...] = (
    Size(
        label="M6",
        d=6.0,
        pitch=1.0,
        choice=1,
        source=Source(
            standard="ISO 262", edition="2023", table="Table 1", column="Coarse", status="verified"
        ),
    ),
)
