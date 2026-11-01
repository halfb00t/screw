# Phase 7 deferred items

Out-of-scope discoveries logged by the executor, not fixed. Each needs the owner or a later plan.

## From 07-09 (cost model fit and budget table)

- **In-wall parts the shipped build refuses.** Explore run 40646117094 has 20 free-space parts that
  pass the L20 parameter model and whose readings are `refused` with `BuildError` at all three
  artifacts (60 readings): 17 bolts at d 3, 100 and 300 with pitch 0.1, 0.35 or 1
  (12 right hand, 5 left) and three d 30 pitch 0.35 nuts. Listed by label with
  `bench.oper_fit.within_walls` over the explore records. The budget table counts them in the
  "admitted with a non-ok explore reading" column wherever a candidate admits them. Not a wrong part (the
  build refuses, L02 holds), but a request the model admits that cannot be built. No cause was
  investigated. Belongs to the owner's budget ruling (07-10) or a debt item.
- **C3 admits capped parts.** Under C3 at `stl-fine`, 5 admitted free-space bolts (d 300, pitch 1,
  3 and 10, 30 turns) read `capped` at the 12 GiB cap in explore run 40646117094, and C3's
  enveloped predicted worst peak is 1.81628e10 B. This is what R13's C3 gives as written (seconds
  and peak unbounded); it is in the table for the owner's ruling.
