# The nut's countersink cutter ends at a negative radius at a coarse pitch and the kernel refuses a valid nut

Severity: must
Status: active
Date: 2026-10-21
Source: the plan 05-20 planner's scratch probe at ad09d46 (not in 05-REVIEW.md), filed by plan 05-20 (owner's choice 2026-10-21)
Related files:
- src/screw/solid/nut.py (`countersink_inner_radius`, `CROSS_FRACTION`)
- docs/tech_debt/active/2026-10-11-root-radius-floor-is-not-the-kernel-boundary.md
- docs/tech_debt/active/2026-10-14-nut-interim-bounds.md

## Context
`countersink_inner_radius` returns `root - CROSS_FRACTION * thread_depth` once the cone reaches the
void's root, with `root = d/2 - thread_depth + clearance`. That is negative when the void's root
radius is below 0.3 thread depths.

The numbers are a scratch probe by the planner at HEAD ad09d46 on 2026-10-21 (macOS arm64), not a
record and not committed. At d 2, clearance 0.05, s 4, m 3:
- pitch 1.5 gives an inner radius of -0.0055 mm, and pitch 1.8 gives -0.2166 mm;
- the model accepts both nuts and the kernel refused both with `Standard_Failure`;
- capping the radius at max(root - 0.3 td, root / 2) built both inside T_GATE with passing preview
  STLs;
- at clearance 0.01 (void root 0.036 mm) the build still refused, with "invalid solid", which is the
  root-floor class of the item above.

## Why it matters
An accepted nut is refused with an unactionable "check d, pitch, ..." error, the same class as the
face-chamfer defect plan 05-20 fixed (WR-01). No ISO 262 coarse size meets it (computed from the code: at clearance 0 the smallest
`d/2 - 1.3 * thread_depth` of the 15 sizes is 0.7185 mm, at M2); it needs a coarse pitch at a small
diameter.

## Next step
Revisit before the nut's pitch or clearance range is relied on, or together with the root-radius floor
item. Cap the inner radius, measure the smallest void root radius that builds, and refuse below it
naming d, pitch and clearance.
