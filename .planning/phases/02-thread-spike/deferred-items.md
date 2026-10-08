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
