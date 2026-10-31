# The nut's countersink cutter ends at a negative radius at a coarse pitch and the kernel refuses a valid nut

Severity: must
Status: active
Date: 2026-10-21
Source: the plan 05-20 planner's scratch probe at ad09d46 (not in 05-REVIEW.md), filed by plan 05-20 (owner's choice 2026-10-21)
Related files:
- src/screw/solid/nut.py (`countersink_inner_radius`, `CROSS_FRACTION`)
- docs/tech_debt/active/2026-10-11-root-radius-floor-is-not-the-kernel-boundary.md
- docs/tech_debt/resolved/2026-10-14-nut-interim-bounds.md
- bench/results/phase-07/walls-voids-40665307964/
- bench/RESULTS.md (`### R10 void readings, an observation (no number is taken from it)`)
- .planning/phases/07-operability-re-sweep/07-GAP-RULINGS.md (G26)

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

Runner evidence (2026-10-28, owner ruling G26):
- Void walk run 40665307964 and walls run 40646134133 group (d) together hold 390 nut-void readings.
  All are built as `bench/oper_sets.py` `_void_cell` builds them: `s` 1.6 d, `m` 3 pitch, clearance
  0.15.
- 20 are ok and 370 refused, all `StdFail_NotDone`.
- Every ok void walk reading has r/d >= 0.1250 and every refused one <= 0.1200. pitch/d does not
  separate them.
- Computed from the code and not read (`countersink_inner_radius` over the committed params of all
  390 readings, run from the repo root with the venv), the output being:

  ```
  nut void readings 390: ok 20, not ok 370 (['refused']); no countersink 0
  countersink inner radius mm: ok min 0.0450, not ok max -0.0300; on the other side of 0: 0
  ```

  So this item's countersink inner radius is >= 0.0450 mm on every ok reading and <= -0.0300 mm on
  every refused one, with 0 of 390 on the other side of 0.
- ASSUMPTION: the negative cutter radius is the cause of the refusal. No reading built one of these
  nuts with the radius capped, so the correlation is not shown to be the cause.
- A nut whose void root ratio r/d is near or below about 0.12 is refused by the kernel
  (`StdFail_NotDone`) and not by a guard.

## Why it matters
An accepted nut is refused with an unactionable "check d, pitch, ..." error, the same class as the
face-chamfer defect plan 05-20 fixed (WR-01). No ISO 262 coarse size meets it (computed from the code: at clearance 0 the smallest
`d/2 - 1.3 * thread_depth` of the 15 sizes is 0.7185 mm, at M2); it needs a coarse pitch at a small
diameter.

R10 (G26) takes no floor from the voids, so nothing refuses such a nut before the build. A void guard
at the rod floor (candidate 1e-2 mm) would not hold it: every void reading at r <= 1e-2 mm was
refused.

## Next step
Plan 07-07 (L20) set the rod floor (`MIN_ROOT_RADIUS_MM`, 1e-2 mm) and applied it to the void's root
radius as a guard only; it does not hold this item. The three nuts of walls set (e) that the 05-20
probe named (d 2, s 4, m 3: clearance 0.05 at pitch 1.5 and 1.8, clearance 0.01 at pitch 1.5) were
read on the runner in walls run 40646134133 (labels `nutcsk-d2-s4-m3-c0.05-p1.5`,
`nutcsk-d2-s4-m3-c0.05-p1.8`, `nutcsk-d2-s4-m3-c0.01-p1.5`): all three `refused` by the kernel
(`Geometry kernel failed (StdFail_NotDone)`), and the model still accepts all three (void root radii
0.238, 0.076 and 0.198 mm, over the floor), so the item stays active.

Revisit before the nut's pitch or clearance range is relied on, or together with the root-radius floor
item, or on a request for a nut whose void root ratio r/d is near or below 0.12, or before a void
guard is relied on. Cap the inner radius, measure the smallest void root radius that builds, and refuse below it
naming d, pitch and clearance.
