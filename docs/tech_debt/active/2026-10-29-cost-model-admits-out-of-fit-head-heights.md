# The cost model admits a part it refuses once its head height leaves the fitted band

Severity: must
Status: active
Date: 2026-10-29
Source: plan 07-11 (the cost model wired into `download_refusal`). Found while moving the tests.
Ruled on 2026-10-29 as G28 (`07-GAP-RULINGS.md`); guarded since commit bc7b2ab. Trigger: 07-15's
out-of-band readings.
Related files:
- src/screw/calc/cost.py (`predict`, `fits`, the emitted `COEFFICIENTS`)
- bench/results/phase-07/fit.json (the `ln_k` coefficients)
- bench/points/explore.json (the fitted points)
- src/screw/params.py (`MAX_BOLT_K_MM`, L20)

## Context
R11 fits the log of each target as a linear function of the log features. Over the fitted points
(1247 bolt points, omitted fields at their defaults) the bolt's k/d runs from 0.6 to 0.7, so `ln_k`
is almost collinear with `ln_d`. (This item first said 0.5 to about 0.69; that was wrong.) fit.json (runs explore 40646117094, spread 40646125666) gives it
negative coefficients on every bolt artifact. At stl-fine they are bytes -3.675, seconds -3.366 and
peak -3.007. A taller head therefore predicts a cheaper part. The parameter model allows k up to
`MAX_BOLT_K_MM` (100000 mm, L20), far outside the fitted band.

The figures below come from `cost.fits` at commit ed55679. Take the explore point
`bolt-d100-p1-n30-right` (d 100, pitch 1, 30 mm of thread, s 160, k 60). It is refused at all
three artifacts. Change only k to 100000 and it is admitted at all three. The same thing happens
at d 30 and d 300. Real cost does not fall as the head grows, because the thread is unchanged and
the head adds geometry. So this part is admitted on a prediction the fit does not support.

The nut's `s` does the same. `ln_s` is negative on 6 of the 9 nut models (down to -0.241), and the
fitted nut s/d runs from 1.5 to 4.0. At d 30, pitch 0.35, m 24, clearance 0.15 (figures from
`cost.fits` at commit d869b87): s 48 is refused at all three artifacts; at s 120 the preview is
admitted; at s 300 the preview and the fine STL; at s 999 the preview and the STEP.

This is no regression. The old rule (`FINE_STL_ROWS`) capped only the measured (d, pitch, hand)
rows and refused no off-row part at any artifact. The per-build timeout (`BUILD_TIMEOUT_S`,
interim 30 s until 07-16) still bounds each build. The phase goal of every allowed configuration
being bounded is still not met for this direction. Plan 07-15's tiers would not catch it either:
its bound sets are drawn from explore points (R14), and none has a tall head.

A milder relative of the same issue: a few in-fit parts are admitted at stl-fine and refused at
stl-preview, for example ISO 4017 M20 x 60 at pitch 1. Each artifact has its own C1 budget and
envelope, so this is consistent with R11 to R13. Still, nobody would expect the fine mesh to fit
when the coarse one does not.

## Why it matters
An unauthenticated request can push an expensive thread past the admission rule by naming a tall
head. Only the timeout then stops it from occupying a worker. Any fix changes R11 or the L20 walls,
and R30 says a rule change needs the owner's ruling.

## What is done
The owner ruled G28 on 2026-10-29 (rulings 1, 2, 4 and 5 of that section), amending R11. Each head
ratio (bolt k/d and s/d, nut s/d and m/d) has a band, its [min, max] over the fitted points, which
`bench.oper_fit emit-constants` ships as `cost.BANDS`. A part with a ratio above its band is
predicted as the largest prediction anywhere in the band. A part with a ratio below its band is
predicted as max(raw, low edge). Commit bc7b2ab ships the guard. Bolt k 1000 and nut s 999 are now
refused at all three artifacts, and the budget table and fit.json are byte-identical.

The below-band side rests on an ASSUMPTION that has not been measured: that a smaller head never
costs more than one at the low edge. The above-band side assumes that real cost does not fall as a
head grows past the band.

## Next step
Plan 07-15 reads `outband.json` at 5 repetitions: per kind, artifact and ratio, one part below the
band and one above it, plus a far point where the rule admits one. This item resolves only if every
one of those readings stays within its enveloped prediction. A reading above its envelope stops the
phase for the owner, and `e` is not widened. In that case the item stays active with the readings
added.

## The 07-15 readings (outband run 40909768713, 2026-10-29)
`bench/points/outband.json` (60 points: G28's head-ratio points and G29's bolts below the fitted
turns) read `ok` in all 300 readings (5 repetitions). 7 (point, target) pairs have readings above
their enveloped prediction, 20 readings in all, every one a first-in-file M2 row at stl-fine:

| point | target | largest actual / enveloped prediction | repetitions above |
| --- | --- | --- | --- |
| outband-nut-s-below-iso4032:M2 | seconds | 1.3200 | 1, 2, 3 |
| turns-below-iso4017:M2x4 (G29) | bytes | 1.3116 | 1 to 5 |
| outband-nut-m-below-iso4032:M2 | seconds | 1.2217 | 1, 2, 3 |
| outband-nut-s-far-iso4032:M2 | seconds | 1.1255 | 1, 2, 3 |
| outband-nut-s-above-iso4032:M2 | seconds | 1.0696 | 1, 3 |
| outband-nut-s-below-iso4032:M2 | peak | 1.0260 | 1, 2, 3 |
| outband-nut-m-below-iso4032:M2 | peak | 1.0004 | 3 |

No nearest-the-budget point, and no point at stl-preview or step, exceeds its envelope. The figures
and their context are in `bench/RESULTS.md`, `### out-of-band check` under `## Phase 7 Runs II`.
Under R11 and G28 this stops the phase for the owner and widens no e. The item stays active.
