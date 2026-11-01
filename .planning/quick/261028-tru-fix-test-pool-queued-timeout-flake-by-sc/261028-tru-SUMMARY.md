---
phase: quick-261028-tru
plan: 01
status: complete
subsystem: tests / build pool
tags: [D-14, flake, test_pool]
branch: gsd/phase-07-operability-re-sweep
plan_head_before: 006405e
plan_head_after: 61e06d4
commits: 1
---

# Quick 261028-tru: the queued-request timeout test gets twice the slack

## Commit

| sha | Subject | Files |
| --- | --- | --- |
| 61e06d4 | test(pool): give the queued-request timeout test twice the slack under load | tests/test_pool.py, docs/tech_debt/INDEX.md, the debt item (moved to resolved/) |

Built in the worktree `.claude/worktrees/phase-07-preregistration-a2` while the 07-09 executor held
the main tree. It was rebased onto 006405e, then fast-forwarded onto the phase branch.

## Verification

- The test alone: 3 of 3 passed.
- Mutant `deadline = timeout`: the test fails on `assert results == [b"", b""]`; the second request
  ends as `BuildTimeout`.
- `make verify` on the rebased commit: `4336 passed in 220.53s`, all checks passed.

## Deviations

- The fix landed on the phase branch, not as a PR off `main`, because the test does not exist on
  `main`.
- No planner or executor agents were spawned: the orchestrator made this one-file edit itself.

## Debt

Resolved: `docs/tech_debt/resolved/2026-10-28-queued-request-timeout-test-flakes-under-full-suite-load.md`.
