# The required CI test job tripled: two pair tests run 20x slower on the runner than locally

Severity: must
Status: active
Date: 2026-10-20
Source: plan 05-15 (draft PR #18 CI runs); owner ruling option c, 2026-10-20
Related files:
- tests/test_pair.py (the M6 right-hand c = 0.10 verify cell)
- tests/test_bench.py (`test_the_expected_verdicts_are_re_derived_from_the_recorded_pair_campaign`)
- .github/workflows/ci.yml (`test (3.12)`)

## Context
The required `test (3.12)` job went from 3 to 7.5 min (runs before plan 05-15) to 12m26s
(run 39428789949, `3334 passed in 681.73s`) and 16m28s (run 39431329111, `3334 passed in
922.00s`). The `--durations=10` list of the second run names the two tests:

| Test | ubuntu-latest (4 vCPU) | local (M5 Max) |
| --- | --- | --- |
| `test_the_expected_verdicts_are_re_derived_from_the_recorded_pair_campaign` | 300 s | 13.6 s |
| the pair verify cell (M6 right, c = 0.10) | 167.50 s | 42.55 s alone |

The 20x gap on the first test is unexplained; CPU contention under xdist on 4 vCPU is a guess,
not a measurement. R14 ruled on the local `make verify` time only, not on CI time.

## Why it matters
Every push to a PR now waits about 16 min for the required job, and the job is one slow test
away from the runner's limits. The pair cell must stay required (it is what catches a change
that breaks the verdict on the PR), so moving it out is not the first fix.

## Next step
Revisit after phase 5 closes: measure both tests on the runner alone (`-n0`, one job) versus
under xdist to find where the 300 s goes, then choose between fixing the slow path, pinning the
two tests to one worker, or moving the campaign re-derivation (not the verify cell) to the
`pair` tier. Trigger: phase 5 close, or the job passing 20 min.
