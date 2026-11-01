# Root radii down to about 3e-5 mm pass validation and then fail in the kernel with a generic message

Severity: must
Status: resolved
Date: 2026-10-11
Resolved in: 683a434, `feat(calc): refuse a root radius below the measured kernel floor (07 D-18)`
Source: Phase 3 code review (03-REVIEW.md WR-04), deferred by the owner on 2026-10-10; needs a measurement and an INTERIM bound
Related files:
- src/screw/calc/thread.py (`root_radius_refusal`)
- src/screw/solid/__init__.py (`_build_checked`, the `Standard_Failure` rewrite)
- docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md (where the floor belongs once measured)
- docs/architecture/decision_log.md (L12: "a root radius at or below zero is a 422 naming d and pitch")

## Context
`root_radius_refusal` accepts any root radius above 0. Single-run probe at `d=6`: pitch 5.54 (root 1.4e-3 mm), 5.541 and 5.542 (root 3.0e-4 mm) build; pitch 5.5425 (root 3.4e-5 mm) and above fail inside OpenCascade with `Standard_Failure`, rewritten as "Geometry kernel failed (Standard_Failure); check d, pitch and length." (422 `build_error`). The gate holds, so nothing wrong is served, but the model says the pair is fine and the build refuses without naming the cause. Where it flips between 5.542 and 5.5425 is unmeasured.

Runner result (2026-10-28, R10 as ruled by G26):
- In walls run 40646134133 group (d), rods only, the largest failing root radius F is 3e-4 mm; the
  failing label at that radius is `root-bolt-M12-right-r0.0003`.
- So the candidate `MIN_ROOT_RADIUS_MM` is V = 1e-2 mm (`bench/RESULTS.md`, `### candidate walls
  (before the confirm)`).
- The R3 confirm (plan 07-05) decides, and plan 07-07 sets the floor and resolves this item.
- The nut voids bear on no R10 bound. Their wall is in
  `docs/tech_debt/active/2026-10-21-nut-countersink-cutter-crosses-the-axis-at-a-coarse-pitch.md`.

## Resolution
Plan 07-07 set the floor from the runner records, by the pre-registered rule R10 as ruled by G26
(`bench/RESULTS.md`, `### candidate walls (before the confirm)` and `#### R3 outcome of the confirm
run by candidate wall`):
- Walls run 40646134133, group (d), the 30 rods (15 sizes, both hands): every rod built at 1e-2, 3e-3
  and 1e-3 mm, the largest failing root radius is 3e-4 mm (`root-bolt-M12-right-r0.0003`, 1 of 30
  refused), and every rod from 3e-5 mm down was refused. The floor is the smallest power of ten at or
  above 10 x 3e-4, `MIN_ROOT_RADIUS_MM = 1e-2` mm.
- Confirm run 40678150220 read all 30 rods at 1e-2 and at 3e-3 mm in 5 repetitions: ok, 30 of 30
  points each.
- `root_radius_refusal`, `void_root_radius_refusal` and `_largest_accepted_pitch` in
  `src/screw/calc/thread.py` accept a root radius that is at least the floor and say so in the 422:
  "must be at least 0.01 mm, the smallest root radius the kernel built on linux/amd64 (runs
  40646134133 and 40678150220)". A root exactly at the floor is accepted, the next float pitch past it
  is refused (`tests/test_thread_maths.py`, `tests/test_api.py`).
- The nut void's root radius is held to the same number as a guard and nothing more: no void was
  measured against it. The kernel refuses voids far above it, and that stays open in
  `docs/tech_debt/active/2026-10-21-nut-countersink-cutter-crosses-the-axis-at-a-coarse-pitch.md`.
- L12's clause "a root radius at or below zero is a 422 naming d and pitch" is superseded in part by
  L20.

## Why it matters
The user-visible contract (L12) names a boundary that is not the real one; the generic kernel text hides the cause the model could have named.

## Original next step
Measure the smallest root radius that builds (as a fraction of `d` or `pitch`, a few sizes), set it as an INTERIM minimum in `root_radius_refusal` with the same message shape, list it in the interim-bounds item and amend L12. Short of that, make the `Standard_Failure` text say "d and pitch leave almost no root".
