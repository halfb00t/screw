# The pair tier has not run on ubuntu: pair.yml can be dispatched only once it is on main

Severity: must
Status: active
Date: 2026-10-14
Source: plan 05-15 (the workflow), plan 05-16 (the local grid); filed by plan 05-18 as the phase closed
Related files:
- .github/workflows/pair.yml
- bench/RESULTS.md ("Pair tier (Phase 5, D-07)": the macOS arm64 run)
- tests/test_pair.py (`test_pair_cell`, the `pair` marker)

## Context
`pair.yml` has `workflow_dispatch` and a weekly schedule (Mondays 04:23 UTC), copying `grid.yml`.
GitHub runs a `workflow_dispatch` workflow only from the default branch, so the workflow cannot be
dispatched while it exists only on the phase branch. Until it is on `main`, the full 240-cell grid
has run once, on macOS arm64 (240 of 240 equal their pre-registered verdicts, 1054.04 s on 8 workers
at a shared load). On ubuntu only the single verify cell ran, as part of `test (3.12)`: `proven`,
167.50 s (CI run 39431329111). So the grid's per-size wall time and its verdicts on linux/amd64 are
unrecorded, and so is whether the 600 s cell deadline holds on a runner about four times slower than
the dev host.

## Why it matters
The pair proof's verdicts depend on the kernel build. The recorded campaign and the local grid agree,
but L11 measured on macOS arm64 too; a platform difference would show first on the runner. A cell that
times out at 600 s on ubuntu would read as a failure of the weekly job, not of the product.

## Next step
Trigger: the Phase 5 PR's merge to `main`. Then dispatch `pair.yml` (`gh workflow run pair.yml`), wait
for all 15 size jobs, and record in `bench/RESULTS.md` a "Pair tier on ubuntu-latest" entry in the
shape `grid.yml`'s first run was recorded in: the run id, the per-size job times, every verdict
against the table, and the slowest cell against the 600 s deadline. A mismatch or a timeout is a
finding to surface, not a cell to reclassify. Resolve this item in the same commit.
