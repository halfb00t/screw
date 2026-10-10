# The thread spike harness carries five open review warnings that PR 2 may not fix

Severity: must
Status: resolved
Date: 2026-10-09
Resolved in: fix(bench): refuse a run while the harness has uncommitted changes and report the HEAD it started at
Source: execute-phase code-review hook on Phase 2 (`.planning/phases/02-thread-spike/02-REVIEW.md`, ledger `02-REVIEW-DISPOSITION.md`); all twelve findings open
Related files:
- bench/thread_spike/__main__.py:1375 (WR-01: `verdict --campaign PREFIX` globs `PREFIX-*.jsonl`, so a prefix that extends another is read too, and the header's `block` is trusted over the file name)
- bench/thread_spike/__main__.py:1142 and :1118 (WR-02: `run <block> --k-from` and `--frontier-from` accept incomplete records; the campaign path is guarded, the standalone path is not)
- bench/quiet.py:52 and bench/thread_spike/__main__.py:1218 (WR-03: `decisive` is fixed at block start; nothing re-reads the load during a multi-hour block)
- bench/thread_spike/verdict.py:1589 (WR-04: the mixed-hand branch of `cell_verdict` returns before the nut-body check that guards same-hand cells)
- bench/thread_spike/__main__.py:183 (WR-05: the guard does not check that the working tree matches the HEAD it records)
- bench/thread_spike/worker.py:246, helical.py:74, measure.py:40, maths.py:3, verdict.py:196, verdict.py:1329, __main__.py:226 and :1056 (IN-01 to IN-07)

## Context
The Phase 2 harness landed on main as PR 5 (`fd40abc`) after a second CLI reviewed it, and
decision D-19 freezes it for PR 2: the runs branch records data and the decision entry and
changes no harness file. The end-of-phase code review (standard depth, 13 source files) then
found 0 critical, 5 warning and 7 info items. None changed the recorded campaign
`2026-10-08-a`: the reviewer checked that the classification, the closed form and the STL
check hold, that the pair report has no timeout, failure or worker_died cell, and that every
record name matches `{prefix}-{block}`. The warnings are places where the harness could read a
record other than the one the protocol means, or could accept a dirty working tree, on a
future run.

WR-03 touches a pre-registered rule (D-17: the gate is read once per block and the end reading
is labelled "includes this run's own load" and never used), so changing it is a protocol
amendment in a PR that post-dates the protocol, not a bug fix.

## Why it matters
A later campaign (a re-run after a Phase 5 revision, or Phase 7's re-measure) could record a
block under a clean-looking HEAD from an edited tree (WR-05), adopt a neighbouring campaign's
run under a nested prefix (WR-01), or carry `decisive: true` through a block that went noisy
half-way (WR-03). The verdict rules would then be applied to the wrong evidence while every
record looked well-formed.

## Next step
Revisit when the next harness PR is opened (the first PR after PR 2 lands that touches
`bench/thread_spike/` or `bench/quiet.py`), and in any case before the next campaign is run:
fix WR-01, WR-02, WR-04 and WR-05 with their tests in that PR; put WR-03 to the owner as a
protocol amendment; triage IN-01 to IN-07 there. Update the ledger rows in
`02-REVIEW-DISPOSITION.md` as each one closes.

## Resolution (2026-10-10)

Quick task 261010-lgv, branch `fix/phase-2-harness-review`, cut from origin/main (a0c7923).
One commit per finding; every code fix has the test that would have caught it.

- WR-01 fixed, be82c06. `_read_runs` reads exactly `<prefix>-<block>.jsonl` for each campaign
  block and refuses a file whose header names another block; the two-runs branch is gone.
  Tests: `test_the_verdict_never_reads_a_campaign_whose_prefix_extends_its_own`,
  `test_a_run_file_whose_header_names_another_block_is_refused`,
  `test_a_file_that_is_not_a_campaign_run_name_is_never_read`. 02-SPIKE.md Method (the harness
  is frozen at landing) carries a dated amendment note.
- WR-02 fixed, 9a5a5c5. `_locked_k` and `_frontier_rows` run `block_gaps`, and the walk must
  be at the locked K, all before the header is written. Tests:
  `test_a_k_from_sweep_that_is_incomplete_is_refused_before_anything_is_written`,
  `test_a_frontier_from_walk_that_is_incomplete_foreign_or_at_another_k_is_refused`.
- WR-03 deferred, owner ruling 2026-10-10 (Task 1): a D-17 protocol amendment, moved into
  `docs/tech_debt/active/2026-10-10-spike-protocol-amendments-before-next-campaign.md`,
  trigger "before the next campaign".
- WR-04 fixed, cc05a38. The nut-body check runs right after the not-built return and covers
  both hand pairings. Test:
  `test_a_mixed_hand_cell_on_a_nut_whose_body_misses_the_closed_form_is_not_a_violation`.
  02-SPIKE.md Rules (the pair cell, falsifiability) carry dated amendment notes.
- WR-05 fixed, fix(bench): refuse a run while the harness has uncommitted changes and report the HEAD it started at. `read_guard` runs `git status --porcelain` over the harness and
  `protocol_guard(..., uncommitted=...)` refuses, naming the paths. Tests:
  `test_the_guard_refuses_while_the_harness_has_uncommitted_changes_naming_them`,
  `test_the_guard_reads_real_git_and_refuses_an_uncommitted_harness_change_but_not_campaign_output`,
  and `test_the_guard_refuses_an_edit_before_results_and_allows_one_after_it` (updated: an
  after-Results edit now refuses until committed). Deviation from the review's literal command
  (`git status --porcelain -- bench pyproject.toml <protocol>`): `bench/results` is excluded
  and `src` is added. `run_campaign` writes `<prefix>-campaign.md`, and each block its JSONL,
  under `bench/results/thread-spike/` before the next block asks the guard, so the literal
  command would refuse every block after the first; the worker imports `screw` through
  `bench/build_time.py` and `bench/export_cost.py`, so a change under `src` changes the run.
- IN-01 fixed, fix(bench): refuse a run while the harness has uncommitted changes and report the HEAD it started at. `_head()` is gone; the report prints the HEAD the guard read at the
  start of the run, and every git call goes through `_git` with `cwd=_REPO_ROOT`. Test: the
  HEAD line in `test_a_run_writes_its_header_first_then_one_row_per_line_and_never_overwrites_itself`.
- IN-02 deferred, owner ruling 2026-10-10 (Task 1), same new item as WR-03.
- IN-03 skipped: unreachable, the parent builds every request line.
- IN-04 skipped: both failure modes are caught downstream (solids=0, the nut-body check, a
  non-converged volume missing the closed form by more than T_PASS).
- IN-05 fixed, 2bf9a90 (docstring; the `thread_depth(1.0)` pin already existed).
- IN-06 fixed, a8bc769. Test: `test_an_integer_too_large_for_a_float_is_refused_at_the_boundary`.
- IN-07 skipped: the ruled rows are evidence only and the reference package is installed
  `--no-deps`, so the scratch directory carries no kernel to shadow.

Owner ruling 2026-10-10 (Task 1), recorded verbatim from the orchestrator's AskUserQuestion:
- Protocol question: "amend-defer (Recommended)" -- Amend lines 110, 237, 238 with dated notes.
  Fix WR-01/02/04/05. Defer WR-03 and IN-02 into a new must debt item, trigger: before next
  campaign.
- Branch question: "New branch from origin/main (Recommended)" -- `git checkout -b
  fix/phase-2-harness-review origin/main --no-track`.
- No objection raised to the WR-05 path set (bench minus bench/results, plus src,
  pyproject.toml, protocol file) or to the IN triage.

Measured: re-reading campaign 2026-10-08-a after the fixes prints output byte-identical to
lines 13-1086 of `bench/results/thread-spike/2026-10-08-a-campaign.md` (VERDICT_IDENTICAL), after
each verdict-side commit (WR-01, WR-04, IN-06) and after the last. No recorded outcome changed.
