# Root radii down to about 3e-5 mm pass validation and then fail in the kernel with a generic message

Severity: must
Status: active
Date: 2026-10-11
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

## Why it matters
The user-visible contract (L12) names a boundary that is not the real one; the generic kernel text hides the cause the model could have named.

## Next step
Measure the smallest root radius that builds (as a fraction of `d` or `pitch`, a few sizes), set it as an INTERIM minimum in `root_radius_refusal` with the same message shape, list it in the interim-bounds item and amend L12. Short of that, make the `Standard_Failure` text say "d and pitch leave almost no root".
