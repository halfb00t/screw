---
phase: quick-261011-fzb
plan: 01
subsystem: bench-tests
tags: [pytest, segfault, ocp, tech-debt]
requirements: [INFR-03]
key-files:
  modified:
    - tests/test_bench.py
    - bench/thread_spike/pair.py
    - docs/tech_debt/INDEX.md
  moved:
    - docs/tech_debt/resolved/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md
metrics:
  completed: 2026-10-11
status: complete
actuals:
  tasks: 2
  commits: 2
plan_head_before: 66d9393e97a87d8dfa43ac655eed9bf0b9ed06b6
plan_head_after: 5be6a1569f4ddf43ed25520f2e472d3b3e4ea6de
---

# Quick 261011-fzb: Stop the pytest worker segfault at exit

The last in-process `pair.common` test is gone and its checks run in the existing child-process test, so the pytest process no longer frees `pair._KEEP` at interpreter exit (the SIGSEGV in `~BRepAlgoAPI_BuilderAlgo`).

## Commits

- `cfe00a4` test(bench): read pair.common only in a child so the pytest worker exits clean
- `5be6a15` docs(tech-debt): name the fix commit in the resolved pair-test segfault item

## Readings

Pair block: `.venv/bin/python -X faulthandler -m pytest tests/test_bench.py -k "common or pair or place or nut or rod_piece" -q -n0 --no-cov -p no:cacheprovider`

- RED (Step 0, before the change): `52 passed, 397 deselected in 13.39s`, then `Fatal Python error: Segmentation fault`, `rc=139`.
- GREEN (after the change): `51 passed, 397 deselected in 12.36s`, `rc=0`, no `Fatal Python error` line.

Whole file (the debt item's own reproduction): `.venv/bin/python -X faulthandler -m pytest tests/test_bench.py -q -n0 --no-cov -p no:cacheprovider`

- After the change: `448 passed in 68.79s (0:01:08)`, `rc=0`, no fatal line (449 tests before; one deleted).

Child test alone: `1 passed, 447 deselected in 4.07s`.

Final gate, `make verify` run explicitly after both commits:

```
TOTAL                           720     17    144     10  96.88%
Required test coverage of 96.0% reached. Total coverage: 96.88%
============================= 859 passed in 56.82s =============================
```

The pre-commit `make verify` also passed on both commits.

## What changed

- tests/test_bench.py: deleted `test_common_reads_the_volume_of_an_overlap_and_zero_solids_for_a_disjoint_pair`. `test_a_child_that_read_a_pose_comes_back_with_exit_0_the_way_the_worker_ends` now prints the full `common` tuple from the child, and the parent parses it with `ast.literal_eval` and asserts volume approx 1.0, solids == 1, errors is False, warnings is False and seconds > 0. It keeps the exit code 0 check and the disjoint `(0.0, 0)`. The docstring carries the crash frame and date.
- bench/thread_spike/pair.py: one comment line next to `_KEEP`. `common` and bench/thread_spike/worker.py are byte-identical to 66d9393.
- Debt item moved to resolved/ with `Status: resolved`, the captured frame chain in place of the guess, a `Resolution (2026-10-11)` section with the measured numbers above, and `Resolved in: cfe00a4 — <subject>`. INDEX row moved from Active to Resolved.

## Squash-merge note

PRs here are squash-merged, so `cfe00a4` is a branch commit, as ef37f23 was. Whoever ships may append "(PR #N)" to the INDEX row and the `Resolved in:` line. This plan did not.

## Deviations from Plan

None, apart from the trailer. The orchestrator corrected the commit trailer to `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`, used on both commits.

## Known Stubs

None.

## Debt

Resolved docs/tech_debt/resolved/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md; filed nothing new.

## Self-Check: PASSED

- cfe00a4 and 5be6a15 are ancestors of HEAD (`git log --oneline -3`).
- Resolved item exists in resolved/ and is absent from active/. Task 2's verify block printed `TASK2_VERIFY_OK`.
- `.planning/ui-reviews/` and `web/.DS_Store` were never staged.
