# The pool's dying-worker test failed once under host load

Severity: must
Status: resolved
Date: 2026-10-06
Resolved in: ef37f23 (PR #7) — test(pool): free the wedged test's dead-worker semaphores before it returns
Source: Phase 2, plan 02-02 executor (deferred-items.md), carried to the owner by the 02-06 orchestrator; owner sign-off 2026-10-06
Related files:
- tests/test_pool.py (`test_a_dying_worker_surfaces_as_broken_pool_and_is_replaced`, the
  test that failed; `test_a_wedged_build_is_terminated_and_its_worker_replaced`, the cause
  and the fix)
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

## Third occurrence (2026-10-09) -- on the PR 2 ship commit
The same test failed in the pre-commit `make verify` of the ship-note commit for PR 2
(branch `gsd/phase-02-thread-spike-runs` at `5ec5af4`, a `.planning/STATE.md`-only change):
`1 failed, 694 passed in 29.28s`. Same signature as 2026-10-08: pytest collected five
unraisable `ReentrantCallError` / "ResourceTracker called reentrantly for resource cleanup"
warnings during semaphore cleanup (`/mp-75xbwhju`, `/mp-l5v27z2u`, `/mp-pgw8ubgu`,
`/mp-3urv7fhw`, `/mp-8_ij1r7m`); the captured log shows `worker.replaced slot 0 cause
broken_pool`, so the pool did replace the worker and the failure is the unraisable-exception
check, not the assertion. `-n 8`; the host was running the agent session and other
applications (load not read at the moment of failure). The commit was not retried: the
gate stayed red and the ship note stayed uncommitted until the owner decided how to
proceed. The trigger named below is therefore due now, before `make pr.land` on PR 2 (#6).

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

## Resolution (2026-10-09)

- Not host load, and not the bench tests. Three conditions, all needed:
  1. `test_a_wedged_build_is_terminated_and_its_worker_replaced` kept `manager` -- the
     killed executor's `_ExecutorManagerThread`, which holds that executor's call and
     result queues, five named semaphores -- in a local, and `asyncio.run` raising
     `BuildTimeout` through `pytest.raises` leaves the test's frame reachable from a
     `BuildTimeout -> traceback -> run_until_complete frame -> Task -> BuildTimeout`
     reference cycle. Unless a young GC happened to run before the test returned, the five
     semaphores outlived the test as cyclic garbage -- the only such garbage in the suite.
  2. CPython 3.12.15, gh-109629 (`multiprocessing/resource_tracker.py` lines 65-71 and
     118-126, `_send` at 205-216; `synchronize.py` lines 80-89): when the next cyclic GC
     runs on a thread that is inside `ResourceTracker.ensure_running`'s lock -- the next
     test's semaphore `register`, or a worker spawn's `getfd()` -- the semaphores'
     finalizers re-enter the tracker, `ensure_running` raises `ReentrantCallError`, and
     `_send` turns it into a `UserWarning`.
  3. `filterwarnings = ["error"]` makes that warning an exception inside the finalizer, and
     pytest's unraisable-exception plugin reports the five against whichever test is
     running: the next test in the same process, `test_a_dying_worker_...` in file order.
     Its own assertions passed every time.
- Fix: `del manager` in the wedged test after its last use, with a comment carrying the
  mechanism and the numbers below. The semaphores now die by refcount at that line, on the
  main thread, outside any tracker lock. No product code changed.
- Production impact: none found. Every pool-path semaphore cleanup traced (`recreate_for`'s
  shutdown, the lifespan's `pool.shutdown()`, an exiting manager thread) is by refcount with
  the tracker lock free. Even if the reentrant path fired, production's default warning
  filters make it one `UserWarning` line per semaphore while `_send` still writes the
  UNREGISTER (scratch reproduction: 0 unraisable, 5 warnings, no tracker report at exit).
  Only the `error` filter aborts the UNREGISTER, after which the tracker reports "There
  appear to be 5 leaked semaphore objects to clean up at shutdown" and five
  `[Errno 2] No such file or directory` -- the semaphores had been unlinked already.
- Measured on the dev host (CPython 3.12.15, pytest 9.1.1, pytest-xdist 3.8.0, load1 4-12):
  - Natural, the gate's pytest invocation (`-n 8 --cov`): on the unmodified tree 2 of 20
    runs failed with the exact signature, all with `tests/test_bench.py`; 0 of 20 without
    it (260 tests) -- not a significant difference (Fisher p ~ 0.49), and the forced
    reproduction below needs no bench test. After the fix: 0 of 20 with `tests/test_bench.py`
    (not decisive alone against 2 of 20, Fisher p ~ 0.49; the forced numbers are the proof).
  - Forced: a throwaway plugin that runs one `gc.collect()` inside the first locked
    `ResourceTracker._check_alive` of every test (below). Before the fix: wedged + dying
    `-n0` failed 3 of 3, dying alone passed 3 of 3, the full suite `-n 8` gave
    `1 failed, 694 passed` 2 of 2 (the dying test only). After: wedged + dying passed 5 of
    5, `tests/test_pool.py` 2 of 2, the full suite `695 passed` 5 of 5. Revert check:
    without the `del` it failed 3 of 3 again; restored, it passed 3 of 3.
  - Origin tracing (which test created each semaphore the cyclic GC freed): 5 per full
    `-n 8` run before the fix, all created by the wedged test, 3 of 3 runs; 0 after, 3 of 3.
- Rejected: a `filterwarnings` marker on the dying test -- the GC frees the garbage during
  whichever later test it lands in (in 2 of 3 traced runs that was
  `test_each_build_failure_mode_maps_to_its_own_status_and_type`), so the marker would
  move the flake, and it would hide every finalizer error in that test; a suite-wide ignore
  of the CPython warning -- it hides the cause instead of removing it, and nothing is left
  to the GC once the cause is gone; any `pool.py` change -- no production impact; a `gc`
  disable/collect dance -- not needed.
- No regression test, deliberately. The reproduction is an ordering property between two
  tests plus a patch of CPython-private `ResourceTracker._check_alive`, and forcing the GC
  inside the test that creates the garbage collects the cycle early (a GC forced in every
  locked section: wedged + dying passed 3 of 3), so a self-contained test would have to
  rerun the 3 s wedged scenario and patch CPython internals to assert another test's frame
  hygiene. The procedure instead, rerun by hand with
  `PYTHONPATH=<dir> .venv/bin/python -m pytest -p pf_force_first tests/test_pool.py -n0 --no-cov`
  (before the fix: `1 failed, 16 passed`; after: `17 passed`):

  ```python
  # <dir>/pf_force_first.py
  import gc
  from multiprocessing import resource_tracker as rt

  ARMED = {"on": False}
  _orig = rt.ResourceTracker._check_alive
  def _check_alive_with_gc(self):  # called inside ensure_running's lock
      if ARMED["on"]:
          ARMED["on"] = False
          gc.collect()
      return _orig(self)
  rt.ResourceTracker._check_alive = _check_alive_with_gc

  def pytest_runtest_setup(item):
      ARMED["on"] = True
  ```
- Tests: 695 collected before and after.
