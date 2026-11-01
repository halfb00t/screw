# The pool's two dying-worker tests time out at 5 s under host load

Severity: must
Status: resolved
Date: 2026-10-30
Resolved in: this commit — `test(pool): start the worker before the clock in the dying-worker and queued-timeout tests` (quick 261030-g01)
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

## Second occurrence (2026-10-30) -- the trigger has fired
About 20 minutes later, the pre-commit `make verify` of the commit that became `3bcbdb3` ended
`2 failed, 4460 passed in 238.03s`, with a 1-minute load average of 22.63 read a minute after it.
Two other sessions' Python processes each held a core at 100 %. Failed:

- `test_two_same_slot_deaths_from_one_incident_replace_the_worker_once`, the same `BuildTimeout`
  at 5 s as above.
- `test_a_request_queued_behind_a_build_keeps_its_own_full_timeout`, new here:
  `BuildTimeout('Build exceeded its 2s per-build timeout. Try a coarser quality.') != b''`.
  The same test is the subject of the resolved item
  `docs/tech_debt/resolved/2026-10-28-queued-request-timeout-test-flakes-under-full-suite-load.md`.

The retried commit passed, at a load average of 18.18. So the next step below is due. Plan 07-15
did not take it, because it is outside that plan's scope; it is due before phase 7 lands.

## Why it matters
`make verify` is the gate, the pre-commit hook and CI. A test that fails under load and
passes on retry teaches everyone to retry a red gate. That is how a real failure gets
waved through. Each occurrence also costs a full hook cycle, about 4 minutes.

## Next step
Trigger: a second occurrence (fired 2026-10-30, above), or the next edit to
`tests/test_pool.py` or `screw.pool`. Due before phase 7 lands.
Measure the time from a test's worker spawn to its first task under `make verify` load.
Then choose between two fixes:
- Give the two tests a timeout above the measured worst spawn.
- Start the test's worker before the clock does, for example with a warm-up call.

## Measurement (quick 261030-g01, 2026-10-30)
A scratch script timed a fresh `BuildPool(1, ...)` on this 18-CPU macOS arm64 host, with
`tests/` on `sys.path` the way pytest puts it there, so the worker unpickled `test_pool._die`
exactly as the tests make it. Samples were taken alone, then while `pytest -n auto
--ignore=tests/test_pool.py` ran the other test files: three rounds with one or two such
runs at once, then three more. 1-minute load averages: 4.5 to 5.0 alone, 5.4 to 74.8 under
load.

| Reading | Alone (n=5), median / max | Under load (n=81), median / max |
| --- | --- | --- |
| `_die` sent to a cold worker, to `BrokenProcessPool` | 1.56 / 1.58 s | 1.94 / 9.25 s |
| Spawn + `_warm` + `os.getpid` | 1.43 / 1.45 s | 1.75 / 11.40 s |
| First `test_pool` function after an `os.getpid` warm-up (the worker imports `test_pool`, so `screw.app` and fastapi) | 0.10 / 0.10 s | 0.12 / 0.62 s |
| Queued test's first request, 1.2 s build after an `os.getpid` warm-up (deadline 2.0 s) | 1.30 / 1.31 s | 1.33 / 1.997 s |
| Same, second request (deadline 4.0 s) | 2.51 / 2.51 s | 2.53 / 3.20 s |
| `_die` on a worker that has already imported `test_pool` | 0.007 / 0.009 s | 0.011 / 0.027 s |
| Queued first / second after that warm-up (n=33 under load) | -- | 1.206 / 1.220 s; 2.411 / 2.425 s |

The ASSUMPTION held for the dying-worker tests: 13 of 81 cold `_die` samples overran 5 s.
The queued test's cause was a different one, not load on the build itself: its `os.getpid`
warm-up loaded the kernel but not `test_pool`, so the worker imported `test_pool` inside
the first request's 2.0 s clock. That import alone took up to 0.62 s of the 0.8 s slack, and
one sample ended 3 ms short of the deadline. No product bug: in production the initializer
`screw.pool._warm` imports `screw.pool` and `screw.solid` before the first `build_export`.

## Resolution
`tests/test_pool.py::_start_worker` submits `_sleep_past_timeout(0.0)` to the test's worker
and waits for it before the timed part, so the spawn, `_warm` and the `test_pool` import all
happen before the clock starts. The three tests call it. The timeouts are unchanged: 5 s
against a measured 0.027 s worst case for `_die`; 0.8 s and 1.6 s of slack against measured
overheads of 0.020 s and 0.025 s for the queued pair.

- Under load, two `pytest -n auto` runs of the other files at once, 1-minute load 12.7 to
  82.8: the three tests passed 14 runs of 14.
- Mutant `deadline = timeout`: the queued test fails, index 1 is
  `BuildTimeout('Build exceeded its 2s ...')`.
- Mutant without `recreate_for` in the `BrokenProcessPool` branch: both dying-worker tests
  fail, `assert 0 == (0 + 1)` on `pool.replaced`.
- Mutant without `recreate_for`'s identity guard: the two-deaths test fails,
  `assert 2 == (0 + 1)`.
