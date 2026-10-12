# A saved preview STL should name its quality in the file name

Date: 2026-10-12
Source: plan 04-16 (gap G-04-3, the owner's ruling on review item IN-02)
Related files:
- src/screw/app.py (`_serve`, the `Content-Disposition` header)
- src/screw/params.py (`slug()`)
- src/screw/solid.py (`TESSELLATION`)
- docs/architecture/decision_log.md (L13, FRNT-06 in REQUIREMENTS.md)

## Context
The page now offers `Download STL (preview)` where the INTERIM 64 MiB cap refuses the fine STL
(a long ISO 4017 screw, for example M8 x 70). The server names both files `<slug>.stl` from
`params.slug()`, which holds no quality, so once saved a preview mesh (INTERIM 0.08 mm
deflection, 0.5 rad) cannot be told from a fine one (0.01 mm, 0.1 rad). The owner's ruling named
the label and the link, not the header, so this plan left the header alone.

## Why it matters
L02: a saved file is the one place the page's label no longer travels with the mesh. FRNT-06 says a
download's chord deviation must not consume the clearance (Phase 5), and a preview mesh is the
coarse one. A user who opens a month-old file has only its name to go by.

## Next step
The owner decides whether the server names a non-default quality in the file name, for example a
`_preview` suffix (a published header change, so a decision with a new `Lxx`). Revisit with
FRNT-06 in Phase 5.
