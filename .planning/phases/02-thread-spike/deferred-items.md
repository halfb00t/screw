# Phase 2 deferred items

Out-of-scope discoveries logged by executors; not fixed in the plan that found them.

## 02-02: possible load-sensitive flake in tests/test_pool.py

- **Test:** `tests/test_pool.py::test_a_dying_worker_surfaces_as_broken_pool_and_is_replaced`
- **Seen:** once, in the pre-commit `make verify` of a `tests/test_bench.py`-only change
  (2026-10-06, host load 4 to 23 from other projects, `-n 8`). The retried commit passed; the
  file passes alone (17 of 17, `-n0`).
- **Not known:** whether the new CPU-heavy tests from plan 02-02 (400 000-point midpoint
  integrals, kernel builds in worker children) contributed by starving the pool test's
  injected timeouts. The Makefile already notes that those timeouts are what a starved runner
  trips.
- **Trigger to act:** a second occurrence. Then measure the failure rate with and without
  `tests/test_bench.py` and decide between lowering the new tests' CPU cost and a debt item for
  the pool test's timeouts.
- **Status:** resolved
- **Resolved:** The trigger fired. The item was filed as must-severity debt at the first
  occurrence, on the owner's sign-off (9502c66, 2026-10-06). The second occurrence was recorded
  on 2026-10-08 (3964e3f) and a third happened on 2026-10-09. It was fixed on 2026-10-10 in
  69436fb (PR #7). The cause was neither host load nor the 02-02 bench tests:
  `test_a_wedged_build_is_terminated_and_its_worker_replaced` left five semaphores as cyclic
  garbage, CPython's resource tracker re-entered on their finalisers (gh-109629), and
  `filterwarnings = ["error"]` charged the failure to the next test. The fix is a `del manager`
  in that test; no product code changed. The full record is
  `docs/tech_debt/resolved/2026-10-06-test-pool-dying-worker-flake.md`.
