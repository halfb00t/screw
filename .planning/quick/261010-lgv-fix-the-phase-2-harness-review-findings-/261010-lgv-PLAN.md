---
phase: quick-261010-lgv
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - bench/thread_spike/__main__.py
  - bench/thread_spike/verdict.py
  - bench/thread_spike/maths.py
  - tests/test_bench.py
  - .planning/phases/02-thread-spike/02-SPIKE.md
  - .planning/phases/02-thread-spike/02-REVIEW-DISPOSITION.md
  - docs/tech_debt/INDEX.md
  - docs/tech_debt/active/2026-10-09-thread-spike-harness-review-findings.md
  - docs/tech_debt/resolved/2026-10-09-thread-spike-harness-review-findings.md
  - docs/tech_debt/active/2026-10-10-spike-protocol-amendments-before-next-campaign.md
autonomous: false
requirements: [WR-01, WR-02, WR-03, WR-04, WR-05, IN-01, IN-02, IN-03, IN-04, IN-05, IN-06, IN-07]

estimate:
  tokens: 150000
  raw_tokens: 150000
  tasks: 3
  confidence: low

must_haves:
  truths:
    - "WR-01: `verdict --campaign c1` reads exactly `c1-<block>.jsonl` for each block in CAMPAIGN_BLOCKS. A campaign under `c1-x` is never read or adopted. A `c1-<block>.jsonl` whose header names another block is refused with exit 2 and the file named (unless Task 1 deferred WR-01, in which case its ledger row reads deferred)"
    - "WR-02: `run <block> --k-from X` refuses (exit 2, nothing written) a K sweep that `block_gaps` finds incomplete, header-only included. `run rss --frontier-from Y` refuses a frontier walk that is incomplete, holds a foreign row or was recorded at a K other than the locked one, before any header is written"
    - "WR-04: a mixed-hand pair cell whose nut body misses pi d^2 m - A(c) m by more than T_PASS reads inconclusive and does not satisfy `mixed_hand_violated` (unless Task 1 deferred WR-04, in which case its ledger row reads deferred)"
    - "WR-05: the protocol guard refuses while `git status --porcelain` reports any change under bench (bench/results excepted), src, pyproject.toml or the protocol file, and names the paths. Campaign output written under bench/results never refuses the next block"
    - "IN-01: a run's Markdown HEAD line is the HEAD the guard read at the start of that run, and no git call in the CLI runs without cwd=_REPO_ROOT"
    - "IN-06: an integer too large for a float in a spike record is refused with ValueError (verdict exit 2), never an OverflowError traceback"
    - "Re-reading recorded campaign 2026-10-08-a after the fixes prints output byte-identical to lines 13-1086 of bench/results/thread-spike/2026-10-08-a-campaign.md"
    - "Every WR-xx and IN-xx row in 02-REVIEW-DISPOSITION.md reads fixed, skipped or deferred, with a one-line reason; open is 0. The debt item is in docs/tech_debt/resolved with Status: resolved. Every deferred finding lives in one new active debt item"
  artifacts:
    - path: "bench/thread_spike/__main__.py"
      provides: "exact-name `_read_runs`; completeness-checked `_locked_k` and `_frontier_rows`; `read_guard` reading git status; `_environment_lines(head)`"
    - path: "bench/thread_spike/verdict.py"
      provides: "`cell_verdict` with the nut-body check ahead of the mixed-hand branch; overflow-safe `_num`; `protocol_guard(..., uncommitted=...)`"
    - path: "tests/test_bench.py"
      provides: "a regression test per fixed finding, named after the property"
    - path: "docs/tech_debt/resolved/2026-10-09-thread-spike-harness-review-findings.md"
      provides: "resolved debt item with a Resolution section, one line per finding"
    - path: "docs/tech_debt/active/2026-10-10-spike-protocol-amendments-before-next-campaign.md"
      provides: "the deferred findings (WR-03 per Task 1, IN-02), trigger: before the next campaign"
    - path: ".planning/phases/02-thread-spike/02-REVIEW-DISPOSITION.md"
      provides: "twelve rows, none open"
  key_links:
    - from: "bench/thread_spike/__main__.py read_guard"
      to: "bench/thread_spike/verdict.py protocol_guard"
      via: "keyword `uncommitted=` carrying the porcelain lines"
      pattern: "uncommitted="
    - from: "bench/thread_spike/__main__.py _locked_k"
      to: "bench/thread_spike/verdict.py block_gaps"
      via: "completeness check before select_k"
      pattern: "block_gaps\\(\"ksweep\""
    - from: "bench/thread_spike/__main__.py run_block"
      to: "_frontier_rows"
      via: "the locked K passed in"
      pattern: "_frontier_rows\\(frontier_from, results_dir, "
    - from: "bench/thread_spike/__main__.py run_block"
      to: "_environment_lines"
      via: "the guard's start-of-run head"
      pattern: "_environment_lines\\(facts.head\\)"
---

<objective>
Close the Phase 2 harness review debt item (`docs/tech_debt/active/2026-10-09-thread-spike-harness-review-findings.md`, Severity must). Fix WR-01, WR-02, WR-04 and WR-05 with their tests. Put WR-03 to the owner, as CONTEXT 03 D-13 (owner, 2026-10-10) requires. Triage IN-01 to IN-07. Bring the ledger `.planning/phases/02-thread-spike/02-REVIEW-DISPOSITION.md` to zero open rows, and resolve the debt item per CLAUDE.md.

Purpose: per ROADMAP Phase 3 and CONTEXT 03 D-13, this PR must land on main before Phase 3 copies code out of `bench/thread_spike/`. Plan 03-01 Task 1 asserts that no WR-01, WR-02, WR-04 or WR-05 row reads `open`. The fixes protect any future campaign from reading the wrong record, judging a mixed pair on a garbage nut, or recording a run under a HEAD the tree does not match.

Output: four warnings fixed, or deferred by owner ruling. IN-01, IN-05 and IN-06 fixed. IN-02 deferred. IN-03, IN-04 and IN-07 skipped with reasons. The ledger is closed, the debt item resolved, and one new debt item carries what is deferred.

Planning-time findings the executor must know (each was measured, not assumed):
- Two fixes contradict pre-registered protocol text above `## Results` in `.planning/phases/02-thread-spike/02-SPIKE.md`. WR-04 contradicts line 237 (the pair-cell rule order, "Exactly as written, in this order") and line 238 (`mixed_hand_violated`). WR-01 contradicts line 110 ("reads one run per block under one prefix and refuses two"). Line 273 forbids rule changes after campaign data, except as a new PR that post-dates the protocol (D-19). Earlier amendments were owner-gated (Results, "option A"). So Task 1 is a blocking owner checkpoint (CLAUDE.md "Stop and ask first": evidence conflicts).
- WR-05's literal command, `git status --porcelain -- bench pyproject.toml <protocol>`, cannot be built as written. It would refuse every campaign block, because `run_campaign` opens `<prefix>-campaign.md` under `bench/results/thread-spike/` before the first block asks the guard. The plan excludes `bench/results` and adds `src`, which the worker imports via `bench/build_time.py:29` and `bench/export_cost.py:42`. Task 1 surfaces this.
- Re-reading campaign 2026-10-08-a today is byte-identical to its recorded verdict: lines 13-1086 of `bench/results/thread-spike/2026-10-08-a-campaign.md`, 26 s. With the WR-04 check moved ahead of the mixed-hand branch (a probe at planning), it is still byte-identical: 0 built pair cells are off their nut body. This identity is the regression gate for every verdict-side change.
- Any new public ALL_CAPS constant in quiet, maths, verdict, helical, measure, `__main__` or runner fails `test_the_protocol_pre_registers_every_constant_the_harness_uses`. Passing it would need a protocol row, which is another amendment. New module-level names here are private (leading underscore).
- Tracer-first does not apply. These are independent surgical fixes inside one layer, the harness, with no end-to-end path to prove.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@CLAUDE.md
@docs/CODING_VALUES.md
@.planning/STATE.md
@docs/tech_debt/active/2026-10-09-thread-spike-harness-review-findings.md
@.planning/phases/02-thread-spike/02-REVIEW.md
@.planning/phases/02-thread-spike/02-REVIEW-DISPOSITION.md
@docs/tech_debt/INDEX.md
@docs/tech_debt/resolved/2026-10-06-test-pool-dying-worker-flake.md
</context>

<tasks>

<task type="checkpoint:decision" gate="blocking-human">
  <name>Task 1: Owner rulings on the protocol text the fixes touch, and on WR-03</name>
  <decision>(1) May this PR amend the pre-registered protocol text that the WR-01 and WR-04 fixes would otherwise contradict? (2) What is WR-03's disposition?</decision>
  <context>
Evidence:
- WR-04 asks for the nut-body check before the mixed-hand branch. That contradicts `.planning/phases/02-thread-spike/02-SPIKE.md` line 237, the Rules pair-cell bullet: "Exactly as written, in this order: ... a mixed-hand cell ... is violated when every matched pose reads non-empty". It also contradicts line 238: `mixed_hand_violated` holds when "it finished, it was read at exactly MATCHED_POSES and every matched reading is non-empty". Both lines are above `## Results`, so they are pre-registered. Line 273 says no rule above changes after campaign data exists, and that a later change is a new PR post-dating the protocol (D-19). The owner listed WR-04 as "fixed with tests" (CONTEXT 03 D-13, 2026-10-10). No ruling covers the text amendment that fix needs. Owner ruling R1 ("D-14 is not amended") concerns the proven rule, which this fix does not touch.
- WR-01 asks the verdict to read exactly `<prefix>-<block>.jsonl`. That makes line 110 stale: "`verdict --campaign` reads one run per block under one prefix and refuses two". A second file such as `<prefix>-grid-2.jsonl` is simply not read any more, so nothing is refused.
- Measured at planning: re-reading campaign 2026-10-08-a under the WR-04 rule gives a verdict byte-identical to the recorded one, because 0 built pair cells are off their nut body. The exact names match all nine recorded JSONL files. No fix changes the rows any block records. So no recorded outcome changes, and line 110's "the affected block re-runs" fires for no block.
- WR-03 is the owner's call in this PR (CONTEXT 03 D-13, and the debt item calls it a D-17 protocol amendment). Implementing it means load readings between rows, recorded in the JSONL, plus a pre-registered downgrade rule. That is beyond this quick task.

Also for the owner (informational; object in the reply if needed):
- WR-05 cannot use the review's literal command. `git status --porcelain -- bench pyproject.toml <protocol>` would refuse every campaign block: `run_campaign` opens `<prefix>-campaign.md` under `bench/results/thread-spike/` before the first block asks the guard, and each block's JSONL lands there before the next block starts. The plan's path set is `bench` minus `bench/results`, plus `src` (the worker imports `screw` through `bench/build_time.py:29` and `bench/export_cost.py:42`), `pyproject.toml` and the protocol file. Untracked files count.
- IN triage: IN-01, IN-05 and IN-06 fixed. IN-02 deferred into the new debt item: the 600 s value is pre-registered, so changing it is an amendment for the next campaign. IN-03, IN-04 and IN-07 skipped, with reasons in Task 3.
  </context>
  <options>
    <option id="amend-defer">
      <name>Amend lines 110, 237 and 238 with dated notes; defer WR-03 to a new must debt item (with IN-02), trigger "before the next campaign"</name>
      <pros>Code and protocol agree, and D-13's list is met. Both amendments only tighten what the verdict accepts, so neither tunes toward a pass. The recorded verdict is unchanged (measured). Recommended.</pros>
      <cons>Pre-registered text changes after the data exists, visibly on main.</cons>
    </option>
    <option id="amend-skip">
      <name>Amend as above; skip WR-03 (D-17's start-of-block gate stands as registered)</name>
      <pros>Closes WR-03 for good, with the owner's reason on record.</pros>
      <cons>In a future campaign, a block that turns noisy part-way still carries decisive: true.</cons>
    </option>
    <option id="wr01-only">
      <name>Amend only line 110 (reading mechanics, no rule change); defer WR-04 with WR-03</name>
      <pros>No change to the Rules section.</pros>
      <cons>Departs from D-13 (WR-04 fixed). The mixed-hand verdict stays unguarded until the deferral is picked up.</cons>
    </option>
    <option id="no-amend">
      <name>No protocol edits; defer WR-01 and WR-04 with WR-03</name>
      <pros>The protocol is untouched.</pros>
      <cons>Departs from D-13 for two warnings. This PR then fixes only WR-02, WR-05, IN-01, IN-05 and IN-06.</cons>
    </option>
  </options>
  <resume-signal>Reply with one option id: amend-defer, amend-skip, wr01-only or no-amend. Optionally add "WR-03 now": it is then filed with trigger "now" for a dedicated task after this one, and this plan proceeds with the chosen option for the rest. You may also object to the WR-05 path set or to the IN triage. Record the reply verbatim. Tasks 2 and 3 cite it as "owner ruling 2026-10-10 (Task 1)".</resume-signal>
</task>

<task type="auto" tdd="true">
  <name>Task 2: The harness reads only the record the protocol means (WR-01, WR-02, WR-04, IN-06, IN-05)</name>
  <files>bench/thread_spike/__main__.py, bench/thread_spike/verdict.py, bench/thread_spike/maths.py, tests/test_bench.py, .planning/phases/02-thread-spike/02-SPIKE.md</files>
  <precondition>The working branch was cut from origin/main and carries no Phase 3 commit. `git merge-base --is-ancestor origin/main HEAD` exits 0, `git rev-parse --abbrev-ref HEAD` is not `gsd/phase-03-real-helical-thread`, and `git log --oneline origin/main..HEAD` lists no `docs(03)` commit. Reason: CONTEXT 03 D-13 and the ROADMAP Phase 3 precondition make this a separate PR that lands on main before Phase 3. Read-only check: do not create, rebase or switch branches yourself. Halt and report if unmet.</precondition>
  <reversibility rating="costly">Under amend-defer or amend-skip, this edits pre-registered protocol text on main. A revert is another visible amendment.</reversibility>
  <read_first>
    - bench/thread_spike/__main__.py lines 1-38 (module docstring), 537-582 (`_frontier_terminals`, `_block_rss`), 1118-1126 (`_frontier_rows`), 1142-1260 (`_locked_k`, `run_block`), 1359-1395 (`_read_runs`), 1580-1612 (`verdict_campaign` head), 1700-1715 (CAMPAIGN_BLOCKS, `_NEEDS`)
    - bench/thread_spike/verdict.py lines 160-215 (`_refuse`, `_num`), 1185-1200 (`mislabelled_rows`), 1293-1318 (`block_gaps`), 1525-1625 (`_nut_body` to `cell_verdict`)
    - bench/thread_spike/maths.py lines 1-12 (docstring)
    - tests/test_bench.py lines 455-459 (the existing `thread_depth` pin), 753-760 (`_HEADER`), 856-868 (finite-number test), 1334-1351 (`_ksweep`, `_m6_ksweep`), 1518-1525 (`_full_walk`), 1737-1767 (`_guard_says`, `_write_run`, `_held`), 1774-1843 (run tests that feed `--k-from`), 2053-2095 (`_full_campaign`, `_verdict`), 2783-2806 (prefix tests), 3476-3500 (frontier-from tests), 3668-3700 (`_pair`, `_mixed`), 4440-4485 (`_BlockLog`, `_campaign_goes`), and the `run_block(...)` calls at 3063, 3461 and 4277
    - .planning/phases/02-thread-spike/02-SPIKE.md lines 110, 237, 238, 273 (only under amend-defer, amend-skip or wr01-only)
    - the Task 1 reply
  </read_first>
  <behavior>
    - WR-01 `test_the_verdict_never_reads_a_campaign_whose_prefix_extends_its_own`. Clean `c1` plus a full `c1-x` campaign with a failing grid row: `_verdict("c1")` returns 0 and the output has no `c1-x-`. Clean `c1` written without its pair run, plus a lone `c1-x-pair.jsonl`: the verdict lists pair as missing (exit 1) and never names `c1-x-pair`. The old glob refuses the first case with exit 2 and adopts the pair in the second.
    - WR-01 `test_a_run_file_whose_header_names_another_block_is_refused`. A `c1-grid.jsonl` holding a ksweep header gives exit 2, with stderr naming `c1-grid.jsonl` and "holds a ksweep run".
    - WR-01 `test_a_file_that_is_not_a_campaign_run_name_is_never_read` replaces `test_two_runs_of_one_block_under_a_prefix_are_ambiguous_and_refused`. A clean `c1` plus `c1-grid-again.jsonl` holding a failing grid row: exit 0, and `c1-grid-again` appears nowhere in the output.
    - WR-02 `test_a_k_from_sweep_that_is_incomplete_is_refused_before_anything_is_written`, parametrized header-only and one-row-short. `run_block("grid", ...)` returns 2, stderr has "incomplete", and the target JSONL does not exist.
    - WR-02 `test_a_frontier_from_walk_that_is_incomplete_foreign_or_at_another_k_is_refused`, parametrized: a walk cut short without a stop; a row whose size is outside SIZES; a complete walk recorded at K = 5 against a sweep that locks K = 3. `run_block("rss", ...)` returns 2, nothing is written, the K case names both K values, and nothing raises (the old `SIZES.index` crash is gone).
    - WR-04 `test_a_mixed_hand_cell_on_a_nut_whose_body_misses_the_closed_form_is_not_a_violation`. A mixed cell with every matched pose non-empty and nut_volume = body x 1.001 reads inconclusive, with a reason mentioning the nut, and `mixed_hand_violated([cell])` is False. The existing mixed-hand tests still pass, because `_pair`'s default nut is believable.
    - IN-06 `test_an_integer_too_large_for_a_float_is_refused_at_the_boundary`. A record with precise_volume 10**400 raises ValueError matching "precise_volume". A header whose readings hold 10**400 raises ValueError. A clean `c1` campaign whose grid header readings are rewritten to hold 10**400 makes `_verdict("c1")` return 2 with no traceback.
  </behavior>
  <action>
Write each behavior's test first. Run it and confirm it fails for the stated reason, then implement. Never commit a failing test: the pre-commit hook runs make verify. Make one commit per finding, in the order below, with Conventional Commit subjects. A finding that Task 1 deferred is not touched here.

WR-01, under amend-defer, amend-skip or wr01-only. Finding: `verdict --campaign PREFIX` globs `PREFIX-*.jsonl`, so it reads campaigns whose prefix extends PREFIX, and `_read_runs` trusts the header's block over the file name. Change `_read_runs` in bench/thread_spike/__main__.py to loop over CAMPAIGN_BLOCKS and read only `results_dir / f"{prefix}-{block}.jsonl"` when it exists. After `parse_header`, raise ValueError naming the file and both blocks when the header's block differs from the name's block; `verdict_campaign` already turns that into exit 2. Delete the two-runs ambiguity branch: under exact names it cannot be reached, and CLAUDE.md forbids unreachable branches. Update the `_read_runs` docstring, and the module docstring's "then the verdict over PREFIX-*", to say exactly `<prefix>-<block>.jsonl`.

Amend line 110 in .planning/phases/02-thread-spike/02-SPIKE.md. Replace "reads one run per block under one prefix and refuses two" with a statement that it reads exactly `<prefix>-<block>.jsonl` per block, reads no other file, and refuses a file whose header names another block. Append one dated sentence: amended 2026-10-10 by harness review fix WR-01, owner ruling 2026-10-10 (Task 1). Keep the rest of the paragraph.

Rewrite the obsolete two-runs test as the third WR-01 behavior. Commit as fix(bench): read only the exact run names a campaign writes.

WR-02. Finding: the standalone `run <block> --k-from` and `--frontier-from` accept incomplete records, so K can come from half a sweep and a mid-walk row can become a "frontier terminal". Also, `SIZES.index` in `_frontier_terminals` crashes the rss block after its header is written.
- In `_locked_k`, keep the header and rows. Before `select_k`, call `block_gaps("ksweep", header, rows, sizes=SIZES, sample_sizes=SAMPLE_SIZES)`; on any gap, raise ValueError with the K-sweep run id, "is incomplete:" and the joined gaps.
- Give `_frontier_rows` a third parameter, the locked K. Raise ValueError when the header's k differs, naming both values. Then run `block_gaps("frontier", ...)` the same way. A walk that passes holds only rows of sizes in SIZES, so `SIZES.index` can no longer fail.
- In `run_block`, pass the locked K. k is an int there because every block but the sweep requires `--k-from`; narrow it the way the existing `DEFAULT_K if k is None else k` does, to keep mypy --strict clean. The `refused: {exc}` path already gives exit 2 before the quiet gate and before the header.
- Existing tests feed `_locked_k` a right-hand-only M6 sweep, so they would now be refused. Repair them without weakening any assertion: add a private test helper that monkeypatches `spike_cli.SIZES` and `spike_cli.SAMPLE_SIZES` to `("M6",)`, as `_verdict` does, and write `_m6_ksweep()` (or `_m6_ksweep(cls="silent_wrong")` in the K-is-5 test). This covers the run tests near lines 1781 and 1828, the controls, container and pair runs at 3063, 3461 and 4277, both frontier-from tests at 3476-3500, and `_BlockLog` / `_campaign_goes`.
- In `test_a_frontier_from_run_that_is_missing_or_not_a_frontier_run_is_refused`, make the sweep complete, so the refusal it checks is the frontier's: assert that stderr names the frontier.

Commit as fix(bench): refuse an incomplete K sweep or frontier walk as a run input.

WR-04, under amend-defer or amend-skip. Finding: the mixed-hand branch of `cell_verdict` returns before the nut-body check that guards same-hand cells, so a nut whose void cut failed can satisfy `mixed_hand_violated`. In bench/thread_spike/verdict.py, move the existing nut-body block of `cell_verdict` (its ValueError for a missing nut_volume and its T_PASS comparison against `_nut_body`, both unchanged) to directly after the not-built return, ahead of the `_is_mixed` branch, so it covers both hands as the finding's fix says. Update the `cell_verdict` docstring order, and any docstring that restates the mixed-hand rule.

Amend .planning/phases/02-thread-spike/02-SPIKE.md line 237, so the listed order puts the nut-body clause second and applies it to every built cell. Amend line 238, adding "its nut body matches its closed form within `T_PASS`" to what a violated mixed cell needs. Append to line 237 one dated sentence: amended 2026-10-10 by harness review fix WR-04, owner ruling 2026-10-10 (Task 1); re-reading campaign 2026-10-08-a under the amended rule gives a byte-identical verdict (0 built cells off their nut body).

Commit as fix(bench): believe a mixed-hand pair cell only on a nut body that matches its closed form.

IN-06. Finding: `_num` calls `math.isfinite` on an int, so 10**400 raises OverflowError instead of the documented refusal (T-02-09). Make `_num` refuse a number that cannot become a finite float through `_refuse`, by catching OverflowError or converting first. Keep the existing message shape, which names the key. Commit as fix(bench): refuse an integer too large for a float at the record boundary.

IN-05. Finding: the maths docstring claims the oracle shares no code path with the builder, but the builder imports `thread_depth` from it. Reword lines 3-5 of bench/thread_spike/maths.py to say that the closed form imports no kernel code (the import-linter contract), that it shares the pinned profile parameters with the builder, and that `test_the_basic_profile_has_the_coefficients_the_owner_confirmed` pins `thread_depth(1.0)` to the independently written ISO value 0.541265877. That pin already exists (tests/test_bench.py:459), so no new test is needed. Commit as docs(bench): say the spike oracle shares the pinned profile parameters with the builder.

Style throughout: ponytail, follow the surrounding code's shape, no Any (L04), no new public ALL_CAPS constant, and comments only where they carry a why.
  </action>
  <verify>
    <automated>make test PYTEST_ARGS="tests/test_bench.py -q --no-cov" && sed -n '13,1086p' bench/results/thread-spike/2026-10-08-a-campaign.md | cmp - <(.venv/bin/python -m bench.thread_spike verdict --campaign 2026-10-08-a) && echo VERDICT_IDENTICAL</automated>
  </verify>
  <done>
- Every behavior test exists and passes, and tests/test_bench.py passes as a whole.
- The cmp prints VERDICT_IDENTICAL. If it does not, stop and surface the diff: a verdict-side fix changed a recorded outcome.
- `grep -n 'glob(f"{prefix}-' bench/thread_spike/__main__.py` prints nothing (unless WR-01 was deferred).
- One commit per fixed finding.
- 02-SPIKE.md changes only on the lines Task 1 allowed.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: A run records the tree it ran (WR-05, IN-01); close the ledger and the debt item</name>
  <files>bench/thread_spike/__main__.py, bench/thread_spike/verdict.py, tests/test_bench.py, .planning/phases/02-thread-spike/02-REVIEW-DISPOSITION.md, docs/tech_debt/INDEX.md, docs/tech_debt/active/2026-10-09-thread-spike-harness-review-findings.md (moved to docs/tech_debt/resolved/), docs/tech_debt/active/2026-10-10-spike-protocol-amendments-before-next-campaign.md</files>
  <read_first>
    - bench/thread_spike/__main__.py lines 160-232 (`_git`, `GuardFacts`, `read_guard`, `check_protocol`, `_head`), 280-292 (`smoke`), 1129-1133 (`_environment_lines`), 1263-1282 (`smoke_block`), 1312-1322 (`smoke_pair`)
    - bench/thread_spike/verdict.py lines 594-631 (`GuardResult`, `protocol_guard`)
    - tests/test_bench.py lines 1010-1100 (pure guard tests and the `_guard` helper), 1101-1185 (real-git guard tests and `_repo_with_protocol`), 1774-1808 (the run test that checks the header head)
    - docs/tech_debt/TEMPLATE.md and docs/tech_debt/resolved/2026-10-06-test-pool-dying-worker-flake.md (shape of a resolved item, and the "name the sha in a follow-up" precedent: ef37f23 then b537528)
  </read_first>
  <behavior>
    - WR-05 `test_the_guard_refuses_while_the_harness_has_uncommitted_changes_naming_them`. `protocol_guard` with uncommitted set to one porcelain line for bench/thread_spike/verdict.py is not held, and a reason contains "uncommitted changes to the harness" plus that path. With uncommitted empty, the existing pure-guard results are unchanged.
    - WR-05 `test_the_guard_reads_real_git_and_refuses_an_uncommitted_harness_change_but_not_campaign_output`, in `_repo_with_protocol(landed=True)` with bench/thread_spike/verdict.py committed:
      - an untracked bench/results/thread-spike/c1-campaign.md leaves check_protocol at 0
      - an edit to the committed verdict.py gives 2, naming the path
      - after reverting it, an untracked src/screw/x.py gives 2
    - WR-05: update `test_the_guard_refuses_an_edit_before_results_and_allows_one_after_it`, keeping its purpose. An uncommitted after-Results edit now refuses with the uncommitted reason. Once committed, it holds (exit 0), still differing from origin/main after `## Results`.
    - IN-01: in `test_a_run_writes_its_header_first_then_one_row_per_line_and_never_overwrites_itself`, the printed report contains the line "- HEAD: `" + "a" * 40 + "`". That is the guard's start-of-run head, not a fresh git read: the old helper would print the real repository's short sha.
  </behavior>
  <action>
Write each behavior's test first, see it fail, then implement. The pre-commit hook runs make verify on every commit.

WR-05. Finding: the guard checks the protocol against origin/main and ancestry, but never that the working tree matches the HEAD the header records. An uncommitted edit to T_PASS, PAIR_BAND or helical.py therefore runs under a clean-looking sha. The review's literal command cannot be used as written (Task 1 context: it refuses every campaign block).
- In bench/thread_spike/__main__.py, add a private module-level tuple of pathspecs: bench, `:(exclude)bench/results`, src, pyproject.toml and PROTOCOL_PATH, with the Task 1 reply's changes if the owner objected. Its comment carries the two constraints. First, `run_campaign` writes `<prefix>-campaign.md`, and every block writes its JSONL, under bench/results before the next block asks the guard. Second, the worker imports `screw` via bench/build_time.py and bench/export_cost.py. Planning verified with git 2.56 that the exclude pathspec hides an untracked bench/results file and still reports an untracked file elsewhere under bench. Keep the tuple private: a public constant needs a protocol row (see objective).
- In `read_guard`, run `_git("status", "--porcelain", "--", *paths)`. That is a list argv with no shell (T-02-06), and untracked files count. Pass the output lines to `protocol_guard` through a new keyword-only parameter, uncommitted, typed `tuple[str, ...]` and without a default, matching the existing keyword-only flags. If git status itself fails, pass one line saying so, so the guard refuses.
- In bench/thread_spike/verdict.py, `protocol_guard` appends a reason containing "uncommitted changes to the harness" and the first few lines (use the module's existing list-shortening helper if it fits). Extend its docstring with why: HEAD is the recorded provenance, so the tree must be HEAD.
- Update the `_guard` test helper with an uncommitted parameter defaulting to an empty tuple. Update `check_protocol`'s module-docstring sentence.

IN-01. Finding: `_head()` runs git without cwd=_REPO_ROOT and is evaluated when the report is built, after the run, not at start. Delete the `_head` helper. `_environment_lines` takes the head as a parameter. `run_block` passes `facts.head`, read by the guard before any row. Each smoke path passes the head of a `read_guard(fetch=False)` read. `smoke` already reads one: read it once, before the environment lines, and keep the printed guard line where it is. Keep any refusal that already precedes the environment lines ahead of the guard read.

Docs, staged in the same commit as the WR-05 and IN-01 code (CLAUDE.md: resolve debt in the same commit as the fix).

(a) In .planning/phases/02-thread-spike/02-REVIEW-DISPOSITION.md, set each finding's disposition in both the frontmatter list and the table, put a one-line reason in the Source cell with no pipe character, and set open to 0. Touch nothing else in the file. Dispositions:
- WR-01, WR-02, WR-04: fixed with their Task 2 commit shas, or deferred per Task 1.
- WR-03: per Task 1. Deferred names the new item. Skipped carries the owner's reason.
- WR-05: fixed, with this commit's subject until (c) names the sha. Add "bench/results excluded so campaign output never refuses the next block; src added because the worker imports screw".
- IN-01: fixed, same placeholder.
- IN-02: deferred. The 600 s is pre-registered (Protocol inputs, owner "they stand"); 2026-10-08-a-pair recorded no timeout cell; changing it is an amendment for the owner before the next campaign; name the new item.
- IN-03: skipped. Unreachable: the parent builds every request line. If reached, worker_died fails the pass bar loudly.
- IN-04: skipped. Both failure modes are caught downstream: a shell reads solids=0 and so silent_wrong; the nut-body check; a non-converged volume misses the closed form by more than T_PASS. A status check would only relabel a failing row.
- IN-05 and IN-06: fixed with their shas.
- IN-07: skipped. The ruled rows are evidence only, never a verdict input, and the reference package was installed --no-deps (STATE.md, Phase 02), so the scratch directory carries no kernel to shadow.

(b) Run git mv on the debt item into docs/tech_debt/resolved/. Set Status: resolved and add a Resolved in line holding this commit's subject, the precedent's placeholder. Add a dated Resolution section with one line per finding (disposition, commit, test name), the WR-05 deviation and its reason, the Task 1 ruling verbatim, and the measured VERDICT_IDENTICAL re-read of 2026-10-08-a. Create docs/tech_debt/active/2026-10-10-spike-protocol-amendments-before-next-campaign.md from TEMPLATE.md:
- Severity must
- Source: this quick task plus the Task 1 owner ruling (the owner's sign-off)
- Related files: bench/quiet.py:52 and bench/thread_spike/__main__.py near the gate read for WR-03; bench/thread_spike/verdict.py near PAIR_TIMEOUT_S for IN-02; plus any finding Task 1 deferred
- Next step: before the next thread-spike campaign runs (a re-run after the Phase 5 roadmap revision, or Phase 7's re-measure), the owner rules each amendment
- If Task 1 said "WR-03 now", the trigger is "now: a dedicated task right after this one"

In docs/tech_debt/INDEX.md, move the old row to Resolved and add the new row under Active, in the same commit. Commit as fix(bench): refuse a run while the harness has uncommitted changes and report the HEAD it started at.

(c) Following the ef37f23 then b537528 precedent, add a second commit: docs(tech-debt): name the fix commits in the resolved harness review item. It replaces the placeholders with the real shas in the resolved item, its INDEX row and the WR-05 and IN-01 ledger cells.
  </action>
  <verify>
    <automated>make verify && sed -n '13,1086p' bench/results/thread-spike/2026-10-08-a-campaign.md | cmp - <(.venv/bin/python -m bench.thread_spike verdict --campaign 2026-10-08-a) && echo VERDICT_IDENTICAL && ! grep -nE '^\| (WR|IN)-0[0-9] \| [a-z]+ \| open \|' .planning/phases/02-thread-spike/02-REVIEW-DISPOSITION.md && ! grep -n 'disposition: open' .planning/phases/02-thread-spike/02-REVIEW-DISPOSITION.md && grep -n '^open: 0$' .planning/phases/02-thread-spike/02-REVIEW-DISPOSITION.md && test -f docs/tech_debt/resolved/2026-10-09-thread-spike-harness-review-findings.md && ! test -e docs/tech_debt/active/2026-10-09-thread-spike-harness-review-findings.md && grep -n '^Status: resolved$' docs/tech_debt/resolved/2026-10-09-thread-spike-harness-review-findings.md && test -f docs/tech_debt/active/2026-10-10-spike-protocol-amendments-before-next-campaign.md</automated>
  </verify>
  <done>
- `make verify` passes; quote its pytest result line.
- VERDICT_IDENTICAL prints.
- No ledger row or frontmatter entry reads open, and open is 0.
- The debt item is in resolved with Status: resolved and real shas after the follow-up commit.
- The new active item and both INDEX rows exist.
- `grep -n "def _head" bench/thread_spike/__main__.py` prints nothing.
- Every git call in `__main__.py` goes through `_git`.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| JSONL records on disk to the verdict and run_block parsers | a recorded file may be partial, hand-edited, foreign or from a neighbouring campaign |
| git working tree to the run header | the header's head sha is the run's provenance; the tree may not match it |
| protocol text to the run guard | pre-registered text gates whether any run may start |

## STRIDE Threat Register

Quick-task scoped IDs (T-lgv-NN): no phase register to continue.

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-lgv-01 | Tampering | `_read_runs` (WR-01) | medium | mitigate | read only `<prefix>-<block>.jsonl`; refuse a header naming another block (Task 2) |
| T-lgv-02 | Tampering | `_locked_k`, `_frontier_rows` (WR-02) | medium | mitigate | `block_gaps` on both inputs and a header-K check, all before the header is written (Task 2) |
| T-lgv-03 | Spoofing | `read_guard` / `protocol_guard` (WR-05) | high | mitigate | git status over bench (bench/results excepted), src, pyproject.toml and the protocol, list argv through `_git`, no shell; a refusal names the paths (Task 3) |
| T-lgv-04 | Tampering | `cell_verdict` (WR-04) | medium | mitigate | nut-body check ahead of the mixed-hand branch (Task 2, per Task 1) |
| T-lgv-05 | Denial of service | `_num` (IN-06) | low | mitigate | an integer too large for a float is refused as ValueError, so exit 2, not a traceback (Task 2) |
| T-lgv-06 | Repudiation | run report HEAD line (IN-01) | low | mitigate | the report prints the guard's start-of-run head (Task 3) |
| T-lgv-07 | Tampering | quiet gate `decisive` (WR-03) | medium | accept | owner ruling in Task 1; if deferred, the new must debt item's trigger is before the next campaign, and no campaign runs in this task |
| T-lgv-SC | Tampering | npm/pip/cargo installs | low | accept | this plan installs no package |
</threat_model>

<verification>
- `make verify` passes (ruff, mypy --strict, import contracts, unfinished-work scan, pytest). The executor states the command and its result line.
- The recorded campaign 2026-10-08-a re-reads byte-identical (VERDICT_IDENTICAL) after Task 2 and after Task 3.
- `git log --oneline origin/main..HEAD` shows one commit per fixed finding, plus the sha-naming follow-up, and no Phase 3 commit.
</verification>

<success_criteria>
- WR-01, WR-02, WR-04 and WR-05 are fixed with regression tests, or WR-01/WR-04 are deferred by the recorded Task 1 owner ruling.
- WR-03 and IN-01 to IN-07 each read fixed, skipped or deferred with a one-line reason. None reads open.
- Debt item resolved per CLAUDE.md: Status, Resolved in sha, git mv, and the INDEX row move, in the fix commit.
- Deferred work survives in one new active debt item with a named trigger.
- No recorded outcome of campaign 2026-10-08-a changes.
</success_criteria>

<output>
Create `.planning/quick/261010-lgv-fix-the-phase-2-harness-review-findings-/261010-lgv-SUMMARY.md` when done. Include the Task 1 ruling verbatim, the commit shas per finding, the make verify result line, and the path of every debt item filed or resolved.
</output>

<task1_ruling>
Owner ruling 2026-10-10 (Task 1), recorded verbatim from the orchestrator's AskUserQuestion:

- Protocol question: "amend-defer (Recommended)" — Amend lines 110, 237, 238 with dated notes. Fix WR-01/02/04/05. Defer WR-03 and IN-02 into a new must debt item, trigger: before next campaign.
- Branch question: "New branch from origin/main (Recommended)" — `git checkout -b fix/phase-2-harness-review origin/main --no-track`.
- No objection raised to the WR-05 path set (bench minus bench/results, plus src, pyproject.toml, protocol file) or to the IN triage.

Task 1 is resolved. Tasks 2 and 3 cite this block as "owner ruling 2026-10-10 (Task 1)".
</task1_ruling>
