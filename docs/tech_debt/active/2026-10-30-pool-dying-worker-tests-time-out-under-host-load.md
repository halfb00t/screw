# The pool's two dying-worker tests time out at 5 s under host load

Severity: must
Status: active
Date: 2026-10-30
Source: Phase 7, plan 07-15 executor: the pre-commit `make verify` of the commit that became `d5876d6`
Related files:
- tests/test_pool.py:252 (`test_a_dying_worker_surfaces_as_broken_pool_and_is_replaced`)
- tests/test_pool.py:534-535 (`test_two_same_slot_deaths_from_one_incident_replace_the_worker_once`)
- src/screw/pool.py:43 (`_warm`, the initializer that imports `screw.solid` in each new worker)
- docs/tech_debt/resolved/2026-10-06-test-pool-dying-worker-flake.md (an earlier flake with a different cause)

## Context
Both tests failed together in one pre-commit run: `2 failed, 4458 passed in 222.38s`, at
`-n` from the Makefile. The host's 5-minute load average read 15.47 just after the run, with
10 sessions logged in. The assertion:

```
E           AssertionError: assert False
E            +  where False = isinstance(BuildTimeout('Build exceeded its 5s per-build timeout. Try a coarser quality.'), BrokenProcessPool)
```

The captured log shows `worker.replaced ... "cause": "timeout"`, not `broken_pool`. So the
5 s per-build timeout ran out before `os._exit(1)` surfaced as a broken pool. This is not the
resolved 2026-10-06 item, which failed on unraisable `ReentrantCallError` warnings.

`test_pool.py` alone passed 22 of 22, three times in a row, at load 8.9 to 15. A
`make verify` of the same tree minutes earlier passed 4460 of 4460. The retried commit
passed.

ASSUMPTION, not measured: a worker spawned for the test runs `_warm` first, which imports
`screw.solid` and so cadquery and OCP. On a loaded host, that import plus the spawn takes
longer than the 5 s the tests allow, and `_die` never runs before the timeout fires.

## Why it matters
`make verify` is the gate, the pre-commit hook and CI. A test that fails under load and
passes on retry teaches everyone to retry a red gate. That is how a real failure gets
waved through. Each occurrence also costs a full hook cycle, about 4 minutes.

## Next step
Trigger: a second occurrence, or the next edit to `tests/test_pool.py` or `screw.pool`.
Measure the time from a test's worker spawn to its first task under `make verify` load.
Then choose between two fixes:
- Give the two tests a timeout above the measured worst spawn.
- Start the test's worker before the clock does, for example with a warm-up call.
