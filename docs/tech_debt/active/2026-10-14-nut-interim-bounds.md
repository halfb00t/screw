# The nut's size ceilings are interim, and its fine-STL cap is a separate open item

Severity: must
Status: active
Date: 2026-10-14
Source: plans 05-04 and 05-05 (Phase 5); filed by plan 05-18 as the phase closed
Related files:
- src/screw/params.py (`NutParams`: `s`, `m`, `clearance` share `INTERIM_MAX_MM`)
- src/screw/calc/thread.py (`nut_turn_cap_refusal`, `MAX_TURNS`)
- src/screw/calc/__init__.py (`download_refusal`, the nut branch)
- docs/tech_debt/active/2026-10-14-nut-fine-stl-caps-unmeasured.md
- docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md (the bolt's and the runtime's rows)

## Context
The nut's three size fields `s`, `m` and `clearance` are each bounded only by `INTERIM_MAX_MM`
(1e5 mm), the figure Phase 1 measured on a plain cylinder and not on a nut (D-14, F1). The nut's
other bounds are rules, not measurements: the root radius with the clearance, `s > d + 2c`
(`nut_too_thin`) and the 250-turn cap on `m + 2 pitch` (`MAX_TURNS`, measured on rods and voids in
L11's `2026-10-08-a-frontier`, nothing above it). None of them is a bound on build time or memory
for a nut. What was measured is small: every ISO 4032 row builds in 1.0 to 1.5 s at clearances 0, 0.1
and 0.2 on macOS arm64 under a shared host (plan 05-13), not on linux/amd64 and not at the corners.

The nut has no fine-STL cap. The plan text assumed the nut would reuse the rod caps (`FINE_STL_ROWS`)
under R12. R12's own condition was not met by the probe on any size it measured (05-OWNER-READS.md,
R12; plan 05-05 stopped there), so no cap was shipped and `download_refusal` serves every nut
download. That is the existing item
`2026-10-14-nut-fine-stl-caps-unmeasured.md`; this item does not duplicate it and does not resolve it.

## Why it matters
A user can ask for a nut up to 1e5 mm across, or one tall enough to take 250 turns of void, and
nothing measured says the build finishes inside `SCREW_BUILD_TIMEOUT` or the container's memory. The
bolt has the same open question (`2026-10-05-interim-runtime-bounds.md`); the nut adds three more
fields to it and a download with no byte cap at all.

## Next step
Revisit with Phase 7's operability re-sweep (OPER-02, OPER-03): measure the nut on the full grid on
linux/amd64, replace the `s`, `m` and `clearance` ceilings and the turn cap with measured values,
and measure the nut's fine STL plus its gzip copy to give the nut its own caps (the existing item's
next step). Add the nut's rows to the table in `2026-10-05-interim-runtime-bounds.md` in that change.
