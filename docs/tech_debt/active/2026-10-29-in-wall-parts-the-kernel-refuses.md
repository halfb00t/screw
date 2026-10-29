# Twenty parts inside the L20 walls pass validation and then fail in the kernel

Severity: must
Status: active
Date: 2026-10-29
Source: plan 07-09 (cost model fit). The owner chose "File must debt, continue" on 2026-10-28.
Related files:
- bench/results/phase-07/explore-40646117094/ (the readings)
- bench/oper_fit.py (`within_walls`, `load_set`)
- src/screw/calc/thread.py (the L20 walls and the root-radius floor)
- .planning/phases/07-operability-re-sweep/deferred-items.md (07-09's first note)
- docs/tech_debt/active/2026-10-21-nut-countersink-cutter-crosses-the-axis-at-a-coarse-pitch.md (a known nut refusal, maybe related)

## Context
Explore run 40646117094 (linux/amd64 runner) read 20 free-space parts that the parameter model
takes today (`within_walls` is true under L20). Every one of their readings is `refused` with
`BuildError`: 3 artifacts each, 60 readings. Listed from the committed records:

- bolts, d 3: `bolt-d3-p0.1-n3-right`, `bolt-d3-p0.1-n30-left`, `bolt-d3-p0.1-n30-right`
- bolts, d 100: `bolt-d100-p0.1-n3-right`, `bolt-d100-p0.1-n30-right`, `bolt-d100-p0.35-n3-right`,
  `bolt-d100-p0.35-n30-right`
- bolts, d 300: `bolt-d300-p0.1-n3-left`, `bolt-d300-p0.1-n3-right`, `bolt-d300-p0.1-n30-left`,
  `bolt-d300-p0.1-n30-right`, `bolt-d300-p0.35-n3-left`, `bolt-d300-p0.35-n3-right`,
  `bolt-d300-p0.35-n30-left`, `bolt-d300-p0.35-n30-right`, `bolt-d300-p1-n3-right`,
  `bolt-d300-p1-n30-right`
- nuts, d 30: `nut-d30-p0.35-m0.8d-s1.6d-c0.15-left`, `nut-d30-p0.35-m0.8d-s1.6d-c0.15-right`,
  `nut-d30-p0.35-m0.8d-s4d-c0.15-right`

The explore set reads each point once (R4), so none of these is confirmed in 5 repetitions. Under
the owner's budget C1 (07-OWNER-RULINGS.md B-01), the budget table counts admitted points with a
non-ok explore reading as 5 at `stl-preview`, 3 at `stl-fine` and 10 at `step`. No cause was
investigated. Hand matters: in the same run the left twins of `bolt-d300-p1-n3-right`,
`bolt-d3-p0.1-n3-right` and `bolt-d100-p0.1-n3-right` read `ok` at all three artifacts. The left
twin of `bolt-d300-p1-n30-right` reads `ok` at `stl-preview` and `step` and `capped` at `stl-fine`.
It is not right-hand only: 5 of the 17 refused bolts are left-hand. ASSUMPTION: a kernel failure
at fine pitch that depends on hand and size, not a fault of the bench.

## Why it matters
A request the model admits gets a build error instead of a part. L02 holds, because no wrong part
is printed. But the API returns a failure for an input it called valid, holds a worker for the
build, and gives the user no field to change. The cost model is fitted without these points, so
their cost is not predicted from any reading.

## Next step
Run `/gsd-debug` on one bolt pair that differs only in hand (`bolt-d300-p1-n3-right` refused, its
left twin `ok`) and on one nut. Decide whether this needs a measured guard (an R-rule
ruling and a sweep) or a kernel fix. Revisit before phase 7 closes, or before the first release.

## Seen again in Runs II (07-15, 2026-10-29)
Two of the twenty, `nut-d30-p0.35-m0.8d-s4d-c0.15-right` and `nut-d30-p0.35-m0.8d-s1.6d-c0.15-left`,
are admitted at stl-preview and among its five slowest enveloped predictions, so R14 put them in the
stl-preview bound set; the first is also the slot-0 partner of four other bound points at N = 3. R14
asks for an ok explore reading only for its two measured choices, not for the five slowest or the
partners. Every reading that built either nut was `refused` with `BuildError` (the lead-in
countersink): 50 of 300 in bound run 40907549180 and 10 of 70 in gzip run 40909739628. Under R3
those points have no max, which 07-16 meets when it takes the bound point, W and the gzip level
from these records.
