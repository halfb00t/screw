---
phase: quick-261010-lgv
plan: 01
subsystem: bench/thread_spike
tags: [harness, review-fixes, protocol-amendment, tech-debt]
requires: []
provides:
  - verdict reads only exact `<prefix>-<block>.jsonl` names
  - run inputs (`--k-from`, `--frontier-from`) held to the pre-registered row set
  - nut-body check ahead of the mixed-hand branch of `cell_verdict`
  - protocol guard that refuses on an uncommitted harness tree
affects: [Phase 3 (precondition: no WR-01, WR-02, WR-04, WR-05 row reads open)]
tech-stack:
  added: []
  patterns: ["private pathspec tuple `_HARNESS_PATHS` (a public ALL_CAPS constant would need a protocol row)"]
key-files:
  created:
    - docs/tech_debt/active/2026-10-10-spike-protocol-amendments-before-next-campaign.md
  modified:
    - bench/thread_spike/__main__.py
    - bench/thread_spike/verdict.py
    - bench/thread_spike/maths.py
    - tests/test_bench.py
    - .planning/phases/02-thread-spike/02-SPIKE.md
    - .planning/phases/02-thread-spike/02-REVIEW-DISPOSITION.md
    - docs/tech_debt/INDEX.md
    - docs/tech_debt/resolved/2026-10-09-thread-spike-harness-review-findings.md
decisions:
  - "owner ruling 2026-10-10 (Task 1): amend-defer"
metrics:
  duration: "about 1 h 15 min"
  completed: 2026-10-10
status: complete
commits: 7
plan_head_before: a0c792328606e15ea92673bad96149fd97a8a7ad
plan_head_after: e079ef243f08cf639a9194687c8e3f2229140cb5
actuals:
  tokens: 19400
  tasks: 3
  commits: 7
---

# Phase quick-261010-lgv Plan 01: Fix the Phase 2 harness review findings Summary

Four review warnings fixed with a regression test each (verdict reads only exact run names, run inputs must be whole records, mixed-hand cells need a believable nut body, a run refuses an uncommitted harness tree), three infos fixed, two deferred into one new must debt item, three skipped with reasons. The ledger has 0 open rows, the debt item is resolved, and the recorded campaign 2026-10-08-a re-reads byte-identical.

## Task 1 ruling (owner, 2026-10-10), verbatim

Recorded verbatim from the orchestrator's AskUserQuestion:

- Protocol question: "amend-defer (Recommended)" -- Amend lines 110, 237, 238 with dated notes. Fix WR-01/02/04/05. Defer WR-03 and IN-02 into a new must debt item, trigger: before next campaign.
- Branch question: "New branch from origin/main (Recommended)" -- `git checkout -b fix/phase-2-harness-review origin/main --no-track`.
- No objection raised to the WR-05 path set (bench minus bench/results, plus src, pyproject.toml, protocol file) or to the IN triage.

## Commits (branch `fix/phase-2-harness-review`, one per finding)

| Finding | Disposition | Commit | Test |
|---|---|---|---|
| WR-01 | fixed | be82c06 | `test_the_verdict_never_reads_a_campaign_whose_prefix_extends_its_own`, `test_a_run_file_whose_header_names_another_block_is_refused`, `test_a_file_that_is_not_a_campaign_run_name_is_never_read` |
| WR-02 | fixed | 9a5a5c5 | `test_a_k_from_sweep_that_is_incomplete_is_refused_before_anything_is_written`, `test_a_frontier_from_walk_that_is_incomplete_foreign_or_at_another_k_is_refused` |
| WR-04 | fixed | cc05a38 | `test_a_mixed_hand_cell_on_a_nut_whose_body_misses_the_closed_form_is_not_a_violation` |
| IN-06 | fixed | a8bc769 | `test_an_integer_too_large_for_a_float_is_refused_at_the_boundary` |
| IN-05 | fixed | 2bf9a90 | docstring only; the `thread_depth(1.0)` pin already existed |
| WR-05, IN-01 | fixed | 0e2f437 | `test_the_guard_refuses_while_the_harness_has_uncommitted_changes_naming_them`, `test_the_guard_reads_real_git_and_refuses_an_uncommitted_harness_change_but_not_campaign_output`, `test_the_guard_refuses_an_edit_before_results_and_allows_one_after_it` (updated), HEAD line in `test_a_run_writes_its_header_first_...` |
| (docs) | sha-naming follow-up | e079ef2 | n/a |
| WR-03, IN-02 | deferred | 0e2f437 (ledger + new item) | n/a |
| IN-03, IN-04, IN-07 | skipped | 0e2f437 (ledger, reasons) | n/a |

02-SPIKE.md changed only on the lines the ruling allows: the "harness is frozen at landing" paragraph (WR-01, be82c06), and the pair-cell and falsifiability bullets (WR-04, cc05a38), each with a dated amendment note citing the ruling.

## Verification

- `make verify` (ruff, mypy `--strict`, import contracts, unfinished-work scan, pytest) passed at the last commit. Result line: `705 passed in 30.35s` with `Required test coverage of 94.0% reached. Total coverage: 95.56%`. The pre-commit hook ran the same `make verify` and passed on all seven commits.
- VERDICT_IDENTICAL printed: `sed -n '13,1086p' bench/results/thread-spike/2026-10-08-a-campaign.md | cmp - <(.venv/bin/python -m bench.thread_spike verdict --campaign 2026-10-08-a)`, checked after WR-01, after WR-04, after IN-06, after WR-05/IN-01 and after the last commit. No recorded outcome changed.
- Ledger: no `open` row, `open: 0` in the frontmatter. `grep "def _head"` prints nothing; every git call in `__main__.py` goes through `_git`; `grep 'glob(f"{prefix}-'` prints nothing.
- Live check: `python -m bench.thread_spike check-protocol` on the working tree refused while two harness files were modified and uncommitted, naming both, as intended.

## Debt items

- Resolved: `docs/tech_debt/resolved/2026-10-09-thread-spike-harness-review-findings.md` (Status: resolved, Resolved in 0e2f437 with the earlier shas, INDEX row moved).
- Filed: `docs/tech_debt/active/2026-10-10-spike-protocol-amendments-before-next-campaign.md` (Severity: must, WR-03 and IN-02, trigger "before the next campaign", owner sign-off = the Task 1 ruling).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The second ambiguity test also became obsolete**
- **Found during:** Task 2 (WR-01)
- **Issue:** the plan names only `test_two_runs_of_one_block_under_a_prefix_are_ambiguous_and_refused`, but `test_two_pair_runs_under_a_prefix_are_ambiguous_and_refused` asserts the same unreachable "two runs" refusal for the pair block.
- **Fix:** both are gone; `test_a_file_that_is_not_a_campaign_run_name_is_never_read` covers a `c1-grid-again` and a `c1-pair-again` file together.
- **Files modified:** tests/test_bench.py
- **Commit:** be82c06

**2. [Rule 3 - Blocking] Lint line length in docstring and help text**
- **Found during:** Task 2 (WR-01), first commit attempt (pre-commit hook, E501 on three lines I had reworded)
- **Fix:** rewrapped before committing; no behaviour change.
- **Commit:** be82c06

**3. [Rule 1 - Bug] Two new tests would have started a real grid or rss build**
- **Found during:** Task 2 (WR-02), RED run of `test_a_k_from_sweep_that_is_incomplete_...`: the old code accepted the half sweep and ran the real grid block.
- **Fix:** both new run tests stub their block (`_one_row_block`), as the existing run tests do, so a failing RED cannot start a kernel build.
- **Commit:** 9a5a5c5

**4. [Rule 1 - Bug] My first debt-item rewrite emptied the resolved file**
- **Found during:** Task 3 docs: a scripting slip (a trailing `if False else ""` bound to the whole write expression) wrote an empty file over the `git mv`'d item.
- **Fix:** restored the content from `HEAD`, redid the edit; nothing was committed in the broken state.

Note on style: `_num` (IN-06) keeps two refusal sites of the same message rather than one merged condition, because mypy loses the `int | float` narrowing on a merged form.

## Known Stubs

None.

## Threat Flags

None. The new `git status` call uses list argv through `_git` with no shell (T-lgv-03); no new endpoint, auth path or schema.

## Self-Check: PASSED

Commits be82c06, 9a5a5c5, cc05a38, a8bc769, 2bf9a90, 0e2f437 and e079ef2 are ancestors of HEAD; the resolved item, the new active item and the ledger exist.
