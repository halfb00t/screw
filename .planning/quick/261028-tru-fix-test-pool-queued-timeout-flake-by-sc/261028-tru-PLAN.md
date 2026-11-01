---
phase: quick-261028-tru
plan: 01
type: quick
branch: gsd/phase-07-operability-re-sweep
---

# Quick 261028-tru: stop the queued-request timeout test flaking under full-suite load

Written by the orchestrator. No planner agent was spawned for this one-file test edit.

## Task 1: scale the build and the timeout together

`tests/test_pool.py::test_a_request_queued_behind_a_build_keeps_its_own_full_timeout` builds
0.6 s twice under a 1.0 s timeout. It failed four times on 2026-10-28, each time on the first
request's own build (the assertion was captured in the debt item).

- Change the builds to 1.2 s and the timeout to 2.0 s, and the wall assertion to `wall > 2.0`.
  This keeps `timeout / 2 < build < timeout` and doubles the slack to 0.8 s.
- Mutation check: with `deadline = timeout` in `_run_with_timeout`, the test must fail.
- Resolve `docs/tech_debt/active/2026-10-28-queued-request-timeout-test-flakes-under-full-suite-load.md`
  in the same commit and move its INDEX row.

Done when: the test passes alone, the mutant fails it, and `make verify` passes.

The owner chose a separate PR off `main`. The test exists only on the phase branch (D-14,
`f1c1fb3`), so the fix lands there instead.
