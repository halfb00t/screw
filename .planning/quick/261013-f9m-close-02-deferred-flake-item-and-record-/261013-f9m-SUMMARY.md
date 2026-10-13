---
phase: quick-261013-f9m
plan: 01
subsystem: planning-hygiene
tags: [audit-uat, bench, grid, ci]
requires: []
provides:
  - "02-02 deferred entry marked resolved"
  - "GitHub-runner grid timings in bench/RESULTS.md"
  - "03-UAT test 5 closed"
affects: [.planning/phases/02-thread-spike/deferred-items.md, bench/RESULTS.md, .planning/phases/03-real-helical-thread/03-UAT.md]
key-files:
  modified:
    - .planning/phases/02-thread-spike/deferred-items.md
    - bench/RESULTS.md
    - .planning/phases/03-real-helical-thread/03-UAT.md
decisions: []
metrics:
  tasks: 2
  files: 3
status: complete
actuals:
  tasks: 2
  commits: 2
plan_head_before: e8df30541068df381f28d5a7f0d2afa8f4411afb
plan_head_after: 397b207
---

# Quick 261013-f9m: close the 02-02 deferred item and record the first GitHub-runner grid run

Two commits close the two items `audit-uat` counted as open: the stale 02-02 pool-flake deferred entry, and 03-UAT test 5 on grid run 38240380994 (a `schedule` run, not a `workflow_dispatch`), with its per-size timings recorded in `bench/RESULTS.md`.

## Commits

| Task | Commit | Files |
|---|---|---|
| 1. Mark the 02-02 entry resolved (Status bullet + Resolved bullet citing 9502c66, 3964e3f, 69436fb, resolved debt record) | 777c28e | .planning/phases/02-thread-spike/deferred-items.md |
| 2. Record run 38240380994 and close 03-UAT test 5 | 397b207 | bench/RESULTS.md, .planning/phases/03-real-helical-thread/03-UAT.md |

Base was e8df305. `git diff --name-only e8df305..HEAD` lists exactly the three plan files. `git diff e8df305..HEAD -- .github/workflows/grid.yml .planning/ROADMAP.md docs/tech_debt/` is empty.

## Tracer gate (Task 1)

Audit `summary.total_items` went 2 -> 1 after the deferred-items edit, with no result left for `deferred-items.md`; the commit passed the pre-commit `make verify`.

## Acceptance

`node ~/.claude/gsd-core/bin/gsd-tools.cjs query audit-uat --raw | jq '.summary.total_items, .summary.parse_gap_files'` printed:

```
0
0
```

`make verify` (run directly before the second commit): `2637 passed in 80.22s (0:01:20)`, `Required test coverage of 96.0% reached. Total coverage: 97.33%`. Both commits also passed it through the pre-commit hook.

## What was recorded

Re-derived from `gh` output, not copied from the plan: run `schedule` on `main` at 57d05c6c7844a2b0403107f647e5251acc2477eb, created 2026-10-12T11:05:07Z, updated 11:34:14Z (29 min 7 s), success, 15 of 15 jobs. Every shard `4 passed`, 4/4 xdist workers, Python 3.12.15, pytest 9.1.1, cadquery 2.8.0, cadquery-ocp 7.9.3.1.1, image ubuntu-24.04 (version 20261004.327.1), cache key `Linux-x64-24.04`. Rows from `bench.thread_spike.maths` sum to 7160. Slowest shard M20: 1686.74 s pytest wall, 29:03 job wall, against `timeout-minutes: 120`. s a row range 3.13 (M3.5) to 7.06 (M16). Pytest wall and job wall are separate columns; the job-minus-pytest gap measured 42.7 s (M3.5) to 59.6 s (M8). The `make grid` step time is not recorded. Load is stated as not recorded.

## Deviations from Plan

None. Every re-derived number matched the plan's evidence block. The grid.yml cron (`23 3 * * 1`, Monday 03:23 UTC) fired a run created at 11:05 UTC; the RESULTS entry states the cron and the created time and draws no conclusion from the gap.

## Owner-facing leftovers (not acted on)

- `.github/workflows/grid.yml`: the "Sizing is UNVERIFIED on GitHub runners" comment and `timeout-minutes: 120` now have one measured run against them (M20: 1743 s job wall of 7200 s). Whether to reword or resize is the owner's call.
- `docs/tech_debt/resolved/2026-10-06-test-pool-dying-worker-flake.md` cites `Resolved in: ef37f23`, which does not resolve on this checkout (pre-squash branch commit). The commit on main is 69436fb. The deferred entry cites 69436fb. The resolved record was left untouched (out of scope).
- Run 38240380994 speaks for 57d05c6 only (before the Phase 4 merge e8df305).
- Filed no `docs/ideas/` or `docs/tech_debt/` item.

## Known Stubs

None.

## Self-Check: PASSED

- 777c28e and 397b207 are ancestors of HEAD.
- The three plan files exist and are modified as described; untracked `.planning/ui-reviews/` and `web/.DS_Store` were not staged.
