---
phase: 02-thread-spike
plan: 05
subsystem: testing
tags: [thread-spike, pair-check, closed-form-interference, screw-motion-poses, half-pitch-control, d-14-falsifiability, campaign-driver, worker-pair]

requires:
  - phase: 02-thread-spike
    provides: the rod campaign blocks, JSONL records, verdict rules and container block (plans 02-02 to 02-04); the sewn-twist builder, worker protocol and run guard
provides:
  - maths - interference_area (400 000-point midpoint integral, cached), NUT_HEIGHT with every R5 source label, PAIR_CLEARANCES, DIAGNOSTIC_CLEARANCES, MATCHED_POSES, CONTROL_OFFSET_PITCHES, PAIR_REFERENCE_SIZES
  - verdict - PAIR_BAND, EMPTY_MM3, PAIR_TIMEOUT_S, the pair wire shapes and parsers, cell_verdict (D-12/D-14 as written), size_falsifiable, excluded_clearances, mixed_hand_violated, sensitivity_ok, variant_rules, closed_control
  - pair.py - rod_piece, nut, place, check_cover, common with the boolean and its filler kept alive in _KEEP
  - worker kind pair (run_pair) and runner.Worker.run_pair; block pair, smoke --pair, the pair section of run reports and of the verdict
  - campaign --run-id PREFIX (CAMPAIGN_BLOCKS, run_campaign, PREFIX-campaign.md)
affects: [02-06 protocol write-up, 02-07 campaign, 02-08 verdict, Phase 5 pair check]

actuals:
  tokens: 32200
  tasks: 3
  commits: 4
plan_head_before: 246ae838860698bb9a66855c424f117004be037e
plan_head_after: b927a68e9aa77868a8700da4a6283055e72564a4

tech-stack:
  added: []
  patterns:
    - "The pair verdict is a pure function of recorded readings and the kernel-free closed form; the worker records, the parent judges, and every stored verdict is recomputed by `verdict`"
    - "A pair cell is one request under its own 600 s deadline; a killed or dead child is one cell with no reading in it"
    - "Variant rules are a table beside the D-14 verdict column, computed from the same readings, never an input to cell_verdict"
    - "The campaign driver calls run_block per block, so every block keeps its own guard, quiet gate, header and end reading; a block whose K or frontier input did not complete is skipped, not fed half a record"

key-files:
  created:
    - bench/thread_spike/pair.py
  modified:
    - bench/thread_spike/maths.py
    - bench/thread_spike/verdict.py
    - bench/thread_spike/worker.py
    - bench/thread_spike/runner.py
    - bench/thread_spike/__main__.py
    - tests/test_bench.py

key-decisions:
  - "cell_verdict order: a cell that did not finish, a mixed-hand cell, c <= 0, poses other than the pre-registered ones, a nut body off pi d^2 m - A(c) m by more than T_PASS, any matched pose non-empty (violated), a control that cannot fire by geometry, then the controls against the band. A bad nut body outranks a violation: no reading from a nut that is not the closed form's is believed"
  - "A size is falsifiable only if BOTH hands have a proven cell at some c >= 0.05, and the escape clause also fires when a size's mixed-hand pair did not read violated at every matched pose or has no mixed cell"
  - "The pair run is a verdict input and a required block (PASS_BLOCKS adds pair): a campaign without it is never a pass; the sizes it must cover are the sizes the grid covered, or all of them when there is no grid"
  - "Mixed-hand cells place the nut by the nut's own hand (slide sign -1 for a left-hand nut), and cell_verdict calls one violated only if every matched pose reads non-empty"
  - "A pair reading's outcome is built or failure: a pose that raises is recorded as a failure reading with no measurement and ends the cell, so the record names the pose that raised"
  - "The campaign skips a block whose input did not complete (ksweep for every block, ksweep and frontier for rss) and logs it, because select_k over half a sweep is not the sweep's K"

patterns-established:
  - "RED commits that cannot land through the hook use behaviourless stubs plus strict xfail markers, evidence taken under --runxfail and classified RED_EVIDENCE_OK (as in plans 02-02 and 02-03)"
  - "A real-kernel test names the pose it reads and why: the unit suite reads a cheap control, `smoke --pair` reads the 12 s matched poses"

requirements-completed: [INFR-03]

coverage:
  - id: D1
    description: "interference_area is m-free and kernel-free: M6 with m = 5.2 reads 12.213, 14.1335 and 16.1427 for the half-pitch control at c = 0.10, 0.05 and 0 and 4.3627 for the matched pose at c = -0.05 (each within 1e-3), and exactly 0 for the matched pose at every proof clearance; the M20 control at c = 0.10 reads 429.631 as in research"
    requirement: INFR-03
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_interference_area_reads_the_research_pins_for_m6_within_a_part_in_a_thousand"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_interference_area_of_a_matched_pose_is_exactly_zero_at_every_proof_clearance"
        status: pass
      - kind: other
        ref: "make lint-imports (Contracts: 7 kept, 0 broken.)"
        status: pass
    human_judgment: false
  - id: D2
    description: "cell_verdict is D-12/D-14 exactly as written (owner ruling R1): proven only when all 3 matched poses are empty and all 3 controls fire within PAIR_BAND of the closed form; c <= 0, an unfinished cell, a nut body off its closed form, a control that cannot fire and an off-band or empty control are inconclusive with the reason; a non-empty matched pose is violated; the variant rules are reported and never feed it"
    requirement: INFR-03
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_cell_verdict_proves_a_cell_with_empty_matched_poses_and_controls_in_band"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_cell_verdict_calls_a_control_just_outside_the_band_inconclusive_naming_it"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_variant_rules_can_drop_the_seam_pose_without_touching_the_verdict"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_cell_verdict_distrusts_a_nut_whose_body_volume_misses_the_closed_form"
        status: pass
    human_judgment: false
  - id: D3
    description: "size_falsifiable, excluded_clearances, mixed_hand_violated and sensitivity_ok implement D-14's rules and D-11's sensitivity check; a size falsifiable on neither or one hand, or whose mixed pair did not read violated, fires the escape clause in the verdict naming the size"
    requirement: INFR-03
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_size_falsifiable_needs_one_proven_cell_at_a_proof_clearance"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_a_size_without_a_proven_cell_on_both_hands_fires_the_escape_naming_the_hand"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_a_mixed_hand_pair_that_did_not_read_violated_fires_the_escape_clause"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_a_pair_cell_stored_as_proven_is_judged_again_from_its_readings"
        status: pass
    human_judgment: false
  - id: D4
    description: "pair.py builds the rod piece and the nut once per cell, places the nut by screw motion plus the half-pitch control, raises when the rod does not cover the placed nut, and reads the boolean with its filler kept alive; a real child reads a real M2 control at the closed form, and a child that dies, stalls or babbles is one cell with no reading in it"
    requirement: INFR-03
    verification:
      - kind: integration
        ref: "tests/test_bench.py#test_a_worker_reads_the_requested_pose_of_a_real_cell_and_judges_nothing"
        status: pass
      - kind: integration
        ref: "tests/test_bench.py#test_place_keeps_a_right_hand_nut_at_the_widest_pose_with_a_control_inside_the_rod_piece"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_a_placed_nut_the_rod_does_not_cover_is_a_raised_defect_not_a_reading"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_a_worker_that_dies_or_stalls_on_a_pair_cell_is_one_cell_with_no_reading_in_it"
        status: pass
      - kind: e2e
        ref: ".venv/bin/python -m bench.thread_spike smoke --pair"
        status: pass
    human_judgment: false
  - id: D5
    description: "The pair block runs per size both hands at every diagnostic and proof clearance (six readings each), the mixed pair at the proof clearances (matched poses only), and two reference K values on four sizes; its report prints every volume, the control's closed form, solids, diagnostics and verdict, falsifiability, excluded clearances, the mixed-hand and sensitivity lines, the reference K rows and the variant table under 'Variant rules (reported, never the verdict)'"
    requirement: INFR-03
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_the_pair_block_is_per_size_two_hands_six_clearances_and_four_mixed_cells"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_the_pair_section_renders_rows_falsifiability_mixed_sensitivity_and_the_variants"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_the_variant_table_sits_beside_the_verdict_and_says_it_never_changes_it"
        status: pass
    human_judgment: false
  - id: D6
    description: "campaign --run-id PREFIX runs the nine blocks in protocol order as PREFIX-<block>, K from PREFIX-ksweep by the rule, logs refused and interrupted blocks in PREFIX-campaign.md and goes on, prints the verdict and 'campaign finished', exits with the verdict's code, and refuses (exit 2, nothing written) a long prefix, a recorded block, or a protocol that has not landed"
    requirement: INFR-03
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_every_block_runs_as_prefix_dash_block_with_k_from_the_ksweep_record_never_a_flag"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_one_recorded_block_refuses_the_whole_campaign_before_anything_runs_and_is_left_intact"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_a_block_that_crashes_keeps_its_partial_record_and_is_logged_as_interrupted"
        status: pass
      - kind: e2e
        ref: "out=$(.venv/bin/python -m bench.thread_spike campaign --run-id plan-check 2>&1) -> exit 2, 'protocol guard: refused', no plan-check-* file"
        status: pass
    human_judgment: false

duration: 24min
completed: 2026-10-06
status: complete
---

# Phase 2 Plan 05: The pair check and the campaign driver Summary

**A pre-registered, falsifiable kernel pair check (screw-motion matched poses against half-pitch controls, judged by D-12/D-14 against a 400 000-point closed form) and `campaign`, which runs all nine blocks in protocol order with K taken from the sweep by the rule.**

## Performance

- **Duration:** 24 min
- **Started:** 2026-10-06T13:35:58Z
- **Completed:** 2026-10-06T14:00:26Z
- **Tasks:** 3 (Task 1 is TDD: RED then GREEN)
- **Files modified:** 7 (1 created)

## Accomplishments

- Question 3's expectation and rules exist in kernel-free code with tests before any pair is built. `maths.interference_area` reproduces every research pin (M6 m = 5.2: 12.213, 14.1335, 16.1427, 4.3627, matched exactly 0; M20 control 429.631). `cell_verdict` is D-12/D-14 as written, and owner ruling R1 holds: the variant rules (two of three controls, seam pose excluded, same-pose c = -0.05 as the control) are computed from the same readings and printed in a table beside the verdict column, never feeding it.
- `pair.py` builds the rod piece (thread at c = 0 over m + 2P from z = -P, turn count from exact fractions) and the nut (plain blank of radius d less the void thread), places the nut by screw motion (sign -1 for a left-hand nut) plus the half-pitch control, raises when the rod does not cover the placed nut, and reads the boolean with `op` and the filler kept alive in `_KEEP`. The worker answers a pair request with one reading per pose; a pose that raises is a failure reading that ends the cell and names the pose.
- The block `pair` reads, per size, both hands at c in (0, -0.05, 0.05, 0.10, 0.15, 0.20) with six readings each, the mixed pair (right-hand rod, left-hand nut) at the four proof clearances with matched poses only, and two reference K values on M2, M6, M10, M20. `smoke --pair` reads one M6 right-hand cell at c = 0.10 and K = 5 and prints its six readings, the closed form and the cell verdict; it exited 0 here (53 s).
- `campaign --run-id PREFIX` is the whole spike as one guarded command. On this unlanded branch it exits 2 with `protocol guard: refused` and writes nothing, which is the plan's check.

## Task Commits

1. **Task 1: closed form and pair rules** (TDD)
   - RED: `016d3e8` (test)
   - GREEN: `a252081` (feat)
2. **Task 2: pair builder, pair block, smoke --pair** - `c3f183e` (feat)
3. **Task 3: the campaign** - `b927a68` (feat)

**Plan metadata:** recorded by the docs commit that follows this file.

## TDD Gate Compliance

- **RED (`016d3e8`):** 41 tests fail on their assertions under `--runxfail` against behaviourless stubs (`interference_area` returns -1.0, `cell_verdict` returns `("inconclusive", ())`, `size_falsifiable` False, the parsers raise `ValueError("stub")`, ...), e.g. `assert -5.2 == 12.213 ± 0.012213`. They are strict xfail in the commit because a genuinely failing test cannot land through the pre-commit hook. Classifier verdict `RED_EVIDENCE_OK` (reason `target_test_failed`, target `test_cell_verdict_proves_a_cell_with_empty_matched_poses_and_controls_in_band`). Semantic assessment: the target executed and failed on the planned assertion, not on import or fixture; the stubs exist only so the modules import. The constants and wire types landed in the same commit and their tests pass by design. One stub-related XPASS (a diagnostic-clearance test that the all-False stub satisfied) was fixed before the commit by folding it into a positive assertion.
- **GREEN (`a252081`):** the stubs and all `xfail` markers are gone; the 45 selected tests pass and `make verify` is green. No REFACTOR commit was needed.

## Files Created/Modified

- `bench/thread_spike/pair.py` - new: `rod_piece`, `nut`, `place`, `check_cover`, `common`, `_KEEP`
- `bench/thread_spike/maths.py` - `INTEGRATION_POINTS`, `NUT_HEIGHT` (every entry labelled UNVERIFIED), the pair constants, cached `interference_area`
- `bench/thread_spike/verdict.py` - pair constants, `PairReading`/`PairCell`/`PairRequest`/`PairRecord`, parsers that refuse unknown keys, `failed_pair_record`, `closed_control`, the D-12/D-14 predicates and the variant rules
- `bench/thread_spike/worker.py` - `run_pair`, dispatch on a request carrying `poses`
- `bench/thread_spike/runner.py` - `Worker.run_pair` over one shared `_exchange`
- `bench/thread_spike/__main__.py` - block `pair`, `smoke_pair` and `smoke --pair`, `pair_section`/`pair_report`/`pair_escapes`, the pair run in `verdict_campaign`, `CAMPAIGN_BLOCKS`, `run_campaign`, the `campaign` subcommand
- `tests/test_bench.py` - 84 new test functions (299 in the file, 621 collected in the suite)

## Decisions Made

See `key-decisions`. The two that change what the verdict can read: the pair run is a required block and its falsifiability fires the escape clause by itself, and a size is falsifiable only when both hands are. Neither alters D-14's per-cell rule or owner ruling R1.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] RED commit made of strict-xfail tests over stubs**
- **Found during:** Task 1 (RED)
- **Issue:** the pre-commit hook runs `make verify` including pytest and `--no-verify` is forbidden, so a commit of genuinely failing tests cannot land.
- **Fix:** behaviourless stubs and `xfail(strict=True)` markers; evidence from a `--runxfail` JUnit run through `check tdd-red-evidence`; the GREEN commit removes both.
- **Files modified:** `bench/thread_spike/maths.py`, `bench/thread_spike/verdict.py`, `tests/test_bench.py`
- **Verification:** classifier `RED_EVIDENCE_OK`; `make verify` green on both commits.
- **Committed in:** `016d3e8`, `a252081`

**2. [Rule 3 - Blocking] `runner.py` changed though the plan does not list it**
- **Found during:** Task 2
- **Issue:** `Worker.run` parsed every answer as a `RowRecord`, so a pair record read as "unreadable worker output".
- **Fix:** the request/answer/timeout/death handling moved into one `_exchange`; `run` and the new `run_pair` wrap it. `_died` no longer builds a record. The existing worker tests (death, signal, timeout, hook) pass unchanged.
- **Files modified:** `bench/thread_spike/runner.py`
- **Committed in:** `c3f183e`

**3. [Rule 2 - Missing critical functionality] Pair run required by the verdict**
- **Found during:** Task 2
- **Issue:** the plan adds a pair section to the verdict but not to `PASS_BLOCKS`, so a campaign with no pair run could still read as a pass, against D-15 ("a partial campaign never reads as a pass"); and a size that is not falsifiable must fire the escape clause (D-14).
- **Fix:** `PASS_BLOCKS` gains `pair`; `pair_escapes` feeds the escape list; the sizes judged are those the grid covered (all of them when there is no grid). The `_full_campaign` test helper now writes a pair run.
- **Files modified:** `bench/thread_spike/__main__.py`, `tests/test_bench.py`
- **Committed in:** `c3f183e`

**4. [Rule 1 - Bug] A test read a pose at the pad's edge**
- **Found during:** Task 2, the pre-commit-style `make verify`
- **Issue:** the first real-kernel worker test used a control at theta = pi, which slides the nut a whole pitch, the rod's pad; it passed twice and then failed on `check_cover` (nut z max 2.0000 against rod 2.0000 minus noise). The cover check was right; the pose was outside the pre-registered range.
- **Fix:** the test reads a control at 2 pi / 3 (slide 5P/6), and only that pose, because an M2 matched read costs about 12 s; `smoke --pair` reads the matched poses for real.
- **Files modified:** `tests/test_bench.py`
- **Committed in:** `c3f183e`

**5. [Rule 2 - Missing critical functionality] A block whose input did not complete is skipped**
- **Found during:** Task 3
- **Issue:** the plan logs a crashed block and continues, but a crashed K sweep leaves a partial `PREFIX-ksweep.jsonl` that every later block would read through `select_k`, locking K from half a sweep; the rss block would measure a partial frontier.
- **Fix:** `_NEEDS` skips (and logs) every block when the sweep did not complete and the rss block when the frontier did not.
- **Files modified:** `bench/thread_spike/__main__.py`, `tests/test_bench.py`
- **Committed in:** `b927a68`

**6. [Rule 3 - Blocking] A code-qualified `noqa: E501` on one line**
- **Found during:** Task 3
- **Issue:** the acceptance criterion greps `CAMPAIGN_BLOCKS = (...)` as one 107-character line.
- **Fix:** the single line carries `# noqa: E501` (by code, not bare).
- **Files modified:** `bench/thread_spike/__main__.py`
- **Committed in:** `b927a68`

**Also, without a rule:** `smoke --block pair` is an alias of `smoke --pair`, and a campaign refuses (exit 2) when `PREFIX-campaign.md` already exists, not only a block's JSONL.

**Total deviations:** 6 (3 blocking, 2 missing critical, 1 bug). **Impact:** none changes a pre-registered value or D-14's per-cell rule; deviations 3 and 5 tighten when a campaign may read as a pass.

## Issues Encountered

- `tests/test_pool.py::test_a_dying_worker_surfaces_as_broken_pool_and_is_replaced` did not fail in any hook run or `make verify` run of this plan (no recurrence of the wave 2 flake).
- `smoke --pair` is not a campaign run, so nothing from it is evidence. As a check of the harness it behaves as the research said it would: at M6, K = 5, c = 0.10 the three matched poses read empty and two controls read 12.2131 mm3 against a closed form of 12.213, while the seam control at theta = 0 read empty, which `cell_verdict` calls inconclusive and names. That is exactly the false-empty cluster of RESEARCH Pitfall 3, and what the campaign will measure at scale.

## User Setup Required

None.

## Known Stubs

None. Every function that was a stub in the RED commit is implemented.

## Threat Flags

None. The campaign driver writes only under `bench/results/thread-spike/` (T-02-16: an existing record refuses it), the pair worker exits through `os._exit(0)` with the boolean kept alive (T-02-15), and a reading is trusted only through the controls (T-02-14).

## Next Phase Readiness

The harness is complete. `campaign --run-id PREFIX` refuses on this branch until the protocol lands on `origin/main` (PR 1), and no campaign was run. Plan 02-06 describes the protocol exactly; it can cite `CAMPAIGN_BLOCKS`, `PAIR_BAND`, `EMPTY_MM3`, `PAIR_TIMEOUT_S`, `MATCHED_POSES`, the pair block's cell counts (15 sizes x (2 hands x 6 clearances + 4 mixed) = 240, plus 32 reference cells at the locked K's two neighbours) and the rule that the pair run is a required verdict input.

## Self-Check: PASSED

- Files: `bench/thread_spike/pair.py` exists; `maths.py`, `verdict.py`, `worker.py`, `runner.py`, `__main__.py` and `tests/test_bench.py` carry the changes (`git diff --stat 246ae83..HEAD`: 7 files, 2198 insertions, 39 deletions).
- Commits: `016d3e8`, `a252081`, `c3f183e` and `b927a68` are ancestors of HEAD; `git rev-list --count 246ae83..HEAD` is 4.
- Acceptance greps: `PAIR_BAND = 1e-3`, `EMPTY_MM3 = 1e-6`, `INTEGRATION_POINTS = 400_000`, `_KEEP: list[object]`, `Variant rules (reported, never the verdict)`, `CAMPAIGN_BLOCKS = (...)` and `campaign finished` all match.
- Commands run: `make verify` -> `621 passed in 32.65s`, ruff, mypy `--strict` and `Contracts: 7 kept, 0 broken.` clean; `.venv/bin/python -m bench.thread_spike smoke --pair` -> exit 0, six reading lines, `- cell verdict: inconclusive`, `not a campaign run`; `campaign --run-id plan-check` -> exit 2, `protocol guard: refused`, no `plan-check-*` file.
