# The cost model admits a part it refuses once its head height leaves the fitted band

Severity: must
Status: active
Date: 2026-10-29
Source: plan 07-11 (the cost model wired into `download_refusal`). Found while moving the tests;
not ruled on yet.
Related files:
- src/screw/calc/cost.py (`predict`, `fits`, the emitted `COEFFICIENTS`)
- bench/results/phase-07/fit.json (the `ln_k` coefficients)
- bench/points/explore.json (the fitted points)
- src/screw/params.py (`MAX_BOLT_K_MM`, L20)

## Context
R11 fits the log of each target as a linear function of the log features. In the explore points
the bolt's `k` is always between 0.5 and about 0.69 of `d` (k 0.6 mm to 600 mm), so `ln_k` is
almost collinear with `ln_d`. fit.json (runs explore 40646117094, spread 40646125666) gives it
negative coefficients on every bolt artifact. At stl-fine they are bytes -3.675, seconds -3.366 and
peak -3.007. A taller head therefore predicts a cheaper part. The parameter model allows k up to
`MAX_BOLT_K_MM` (100000 mm, L20), far outside the fitted band.

The figures below come from `cost.fits` at commit ed55679. Take the explore point
`bolt-d100-p1-n30-right` (d 100, pitch 1, 30 mm of thread, s 160, k 60). It is refused at all
three artifacts. Change only k to 100000 and it is admitted at all three. The same thing happens
at d 30 and d 300. Real cost does not fall as the head grows, because the thread is unchanged and
the head adds geometry. So this part is admitted on a prediction the fit does not support.

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

## Next step
Put it to the owner before plan 07-14 draws the bound set. There are three options:
- (a) Clamp each feature to its fitted range before predicting. Out-of-band values would then be
  judged as the band's edge, which is conservative for negative coefficients. This is a rule
  change to R11.
- (b) Add a ratio wall (k/d, s/d) to L20 at the fitted band, so the model is never asked outside
  it.
- (c) Accept it and leave this direction to the timeouts, logged in L21.
