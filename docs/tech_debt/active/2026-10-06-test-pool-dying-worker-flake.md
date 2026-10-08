# The pool's dying-worker test failed once under host load

Severity: must
Status: active
Date: 2026-10-06
Source: Phase 2, plan 02-02 executor (deferred-items.md), carried to the owner by the 02-06 orchestrator; owner sign-off 2026-10-06
Related files:
- tests/test_pool.py (`test_a_dying_worker_surfaces_as_broken_pool_and_is_replaced`)
- .planning/phases/02-thread-spike/deferred-items.md (the original log entry)
- tests/test_bench.py (the CPU-heavy bench tests added in plan 02-02)

## Context
`tests/test_pool.py::test_a_dying_worker_surfaces_as_broken_pool_and_is_replaced` failed
once, in wave 2 of phase 02: the pre-commit `make verify` of the attempt that became commit
`f611dd0`, with host load between 4 and 23 from other projects and `-n 8`. The test passed
alone (`-n0`, 17 of 17 in the file) and on the retried commit. It has not recurred in the
pre-commit hook runs of plans 02-03, 02-04 and 02-05.

First suspect: the CPU-heavy tests that plan 02-02 added to `tests/test_bench.py`
(400 000-point midpoint integrals, kernel builds in worker children) compete for cores and
starve the pool test's injected timeouts. The Makefile already notes that those timeouts
are what a starved runner trips. This is a suspicion, not a measurement.

## Second occurrence (2026-10-08) -- the trigger has fired
The same test failed again in the pre-commit `make verify` of the commit that became
`e77d7af` (plan 02-06, Task 3, the H5 fix): `1 failed, 694 passed in 49.41s`, and this time
with a traceback: multiprocessing's resource tracker was called reentrantly during semaphore
cleanup. The retry passed. Earlier the same day a `make verify` after commit `c54919d` ended
`1 failed, 689 passed` with the failing test's name lost; whether that was this test is not
known. Per the trigger below, the investigation is due before PR 2 lands Phase 2
(`gsd/phase-02-thread-spike-runs`); PR 1 (the protocol, #5) lands first because the
protocol must precede every campaign run (D-19) and this test is not part of the harness.

## Why it matters
`make verify` is the gate, the pre-commit hook and CI. A test that fails under load but
passes on retry teaches everyone to retry a red gate, which is how a real failure gets
waved through. It also costs a full hook cycle each time it fires.

## Next step
Trigger: a second occurrence. Then investigate and fix before the next phase lands: measure
the failure rate with and without `tests/test_bench.py`, and decide between lowering the
bench tests' CPU cost and widening or restructuring the pool test's timeouts. Owner
sign-off to file as `must`: the owner's reply "defaults" to the orchestrator's "file it"
recommendation on 2026-10-06.
