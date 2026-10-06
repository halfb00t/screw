---
phase: 02-thread-spike
plan: 03
subsystem: testing
tags: [thread-spike, d03-grid, frontier, k-sweep, pre-registered-verdict, jsonl-records, quiet-gate, worker-subprocess]

requires:
  - phase: 02-thread-spike
    provides: bench/thread_spike tracer (maths, verdict wire shapes, Worker, protocol_guard, quiet gate) and the owner-pinned basic profile (plan 02-02)
provides:
  - maths - the exact D-03 grid (1790 lengths per hand), the D-04 frontier, SAMPLE_SIZES, K_CANDIDATES, VOID_CLEARANCE, the h/4..h/32 depth presets
  - worker kinds rod (preview and fine meshes, gzip-1, STL check under a 1 000 000 triangle ceiling, STEP) and void (postcondition only)
  - run <block> --run-id with blocks ksweep, grid, frontier, ladder - guarded, JSONL streamed header first, per-size Markdown report, K only from a K-sweep record
  - smoke --block NAME on a small subset for every block
  - verdict rules written before any data - over_budget, frontier_stop, k_scores/select_k, select_estimator, gate_tolerance, pass_bar, escape_rows, turn_caps
  - verdict --campaign PREFIX - recomputes every class, prints K, estimator and T_gate, pass bar, escape clause and turn caps, exit 0 only on a clean pass
affects: [02-04 constructions and controls, 02-05 pair check, 02-06 protocol write-up, 02-07 campaign, 02-08 verdict, Phase 3 builder promotion]

actuals:
  tokens: 28900
  tasks: 3
  commits: 8
plan_head_before: b2d176e544f6407a922eca31816e04a3407a680c
plan_head_after: ed00ddaf1b5d20a60e7cf80865cd0ca74d07ed3c

tech-stack:
  added: []
  patterns:
    - "Every verdict rule is a pure function over RowRecord lists, tested on synthetic records with no kernel and no clock"
    - "Timing-derived claims take a decisive flag and read 'not established (non-decisive gate)' without it; byte claims are integer comparisons that hold on any run"
    - "A campaign block is a function over a Campaign (worker, gate verdict, JSONL sink), so the real worker, a fake one and the smoke subset run the same block code"
    - "A record the child did not produce carries None in every measurement field, and each optional measurement is set exactly when it was asked for or taken"

key-files:
  created: []
  modified:
    - bench/thread_spike/maths.py
    - bench/thread_spike/measure.py
    - bench/thread_spike/worker.py
    - bench/thread_spike/verdict.py
    - bench/thread_spike/__main__.py
    - tests/test_bench.py

key-decisions:
  - "The verdict recomputes every row's class from its raw record and never reads the stored class, so a hand-edited JSONL cannot pass a wrong row (T-02-09)"
  - "K reaches grid, frontier and ladder only through --k-from <ksweep run id> and select_k; there is no flag that takes a K"
  - "A run id is checked, then an existing id refused, then the guard, then the quiet gate: nothing is written before the guard holds, and the JSONL is opened exclusively so an id is never overwritten"
  - "gate_tolerance rounds on the decimal text of the error, so exactly 1e-5 gives 1e-4; a real error that is 1e-6 plus float noise rounds to 2e-5, which is the rule working as written"
  - "check_ceiling is one number per request: a mesh over it is recorded as not checked, never as watertight"

patterns-established:
  - "RED commits that cannot land through the hook use behaviourless stubs plus strict xfail markers, with the evidence taken under --runxfail and classified RED_EVIDENCE_OK"
  - "Report cells print the signed value of greatest magnitude for relative errors, so a -2 from an inverted solid is not hidden behind a +1e-6"

requirements-completed: [INFR-03]

coverage:
  - id: D1
    description: "The D-03 grid is exact: 1790 lengths per hand with the pinned per-size counts (M2 60 ... M20 240), both ends included, coincident integer-turn and integer-mm lengths listed once, 1781 under the alternative lower bound with rows lost only at M8-M20; integer turns decided on Fractions where the float product drifts"
    requirement: INFR-03
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_the_grid_has_the_pinned_length_count_per_size_and_1790_in_all"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_the_grid_under_the_alternative_lower_bound_loses_rows_only_at_m8_and_above"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_integer_turns_are_decided_on_fractions_where_the_float_product_drifts"
        status: pass
    human_judgment: false
  - id: D2
    description: "The D-04 frontier starts at the first multiple of 5 turns strictly above the standard max (M2 55, M2.5 60, M6 65, M20 85), steps by 5 and ends at 250"
    requirement: INFR-03
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_the_frontier_starts_above_the_standard_max_and_steps_by_five_to_250"
        status: pass
    human_judgment: false
  - id: D3
    description: "A rod row records preview and fine meshes, gzip-1 on the named presets, the STL check under a triangle ceiling (a skipped check recorded as not checked) and STEP; a void row records the postcondition only and refuses a mesh or STEP request; each optional field is set exactly when asked for"
    requirement: INFR-03
    verification:
      - kind: integration
        ref: "tests/test_bench.py#test_a_rod_row_meshes_gzips_checks_and_exports_step_as_the_request_asks"
        status: pass
      - kind: integration
        ref: "tests/test_bench.py#test_a_mesh_over_the_check_ceiling_is_recorded_as_not_checked_never_as_a_pass"
        status: pass
      - kind: integration
        ref: "tests/test_bench.py#test_a_void_row_records_the_postcondition_only_against_the_closed_form_with_clearance"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_a_built_record_carries_step_exactly_when_its_request_asked_for_it"
        status: pass
    human_judgment: false
  - id: D4
    description: "Budget and stop rules pinned at their thresholds: 64 MiB raw plus gzip-1 inside and one byte more over; exactly 30.0 s inside and the next float over; a non-decisive gate reads 'seconds not established', never over; frontier stops name the first non-ok row and use the clock only when decisive"
    requirement: INFR-03
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_a_row_of_exactly_64_mib_raw_plus_gzip_is_inside_the_budget_and_one_byte_more_is_over"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_a_row_of_exactly_30_seconds_is_inside_the_budget_and_the_next_float_is_over"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_a_slow_row_on_a_non_decisive_gate_is_seconds_not_established_never_over_budget"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_build_plus_fine_mesh_over_30_seconds_is_a_frontier_stop_only_on_a_decisive_gate"
        status: pass
    human_judgment: false
  - id: D5
    description: "K, estimator and gate rules: select_k takes the fewest fine triangles then STEP bytes then the smaller K and excludes any K with a non-ok row; select_estimator applies the 2x tie rule; gate_tolerance rounds 10x the error up to one significant figure (7.6e-6 to 8e-5, 1e-5 to 1e-4, 2.7e-5 to 3e-4)"
    requirement: INFR-03
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_select_k_takes_the_fewest_fine_triangles_at_the_standard_max"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_estimators_within_2x_tie_and_the_cheaper_by_median_seconds_wins"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_gate_tolerance_is_ten_times_the_error_rounded_up_to_one_significant_figure"
        status: pass
    human_judgment: false
  - id: D6
    description: "Pass bar, escape clause and turn caps: any silent_wrong, failure or worker_died row of either hand fails the bar naming the row; a timeout is an over-budget cap when decisive and makes the bar not established otherwise; per-size construction, bytes and seconds caps with their reasons, seconds only from a decisive run"
    requirement: INFR-03
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_the_pass_bar_fails_naming_the_row_on_one_bad_row_of_either_hand"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_a_timeout_makes_the_pass_bar_not_established_on_a_non_decisive_gate"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_the_seconds_turn_cap_exists_only_from_a_decisive_grid_run"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_the_escape_rows_are_the_failures_inside_the_standard_range_of_either_hand"
        status: pass
    human_judgment: false
  - id: D7
    description: "run <block> is guarded and never overwrites: a bad or already-recorded run id and a --k-from error exit 2 before the guard, a refused guard writes nothing, the header is the first JSONL line, K comes from the K-sweep record, an empty block raises; the unlanded branch refuses the real command"
    requirement: INFR-03
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_a_run_writes_its_header_first_then_one_row_per_line_and_never_overwrites_itself"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_a_run_id_already_recorded_is_refused_with_exit_2_before_any_build_and_left_intact"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_a_block_with_no_rows_raises_instead_of_printing_an_empty_table"
        status: pass
      - kind: other
        ref: ".venv/bin/python -m bench.thread_spike run grid --run-id plan-check --k-from none (exit 2, 'protocol guard: refused', no file written)"
        status: pass
    human_judgment: false
  - id: D8
    description: "Blocks take their rows from maths and run on smoke subsets: grid 4 x 1790 rows from lengths(), ksweep 192, frontier walks to 250 or the first stop, ladder 16 with every preset; every block's smoke subset exits 0 end to end against the real kernel"
    requirement: INFR-03
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_the_grid_block_is_the_d03_grid_from_maths_for_both_hands_with_a_rod_and_a_void"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_the_frontier_block_stops_a_walk_at_the_first_failing_step_and_says_why"
        status: pass
      - kind: integration
        ref: "tests/test_bench.py#test_smoke_block_runs_the_real_frontier_code_on_a_subset_and_says_it_is_not_a_run"
        status: pass
      - kind: other
        ref: ".venv/bin/python -m bench.thread_spike smoke --block ksweep|grid|frontier|ladder (each exit 0, every Class cell ok, 'not a campaign run')"
        status: pass
    human_judgment: false
  - id: D9
    description: "verdict --campaign recomputes every class from the raw record (a stored class of ok on a two-solid row still fails), lists missing blocks and never passes on them, and exits 0 only on a clean pass"
    requirement: INFR-03
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_a_silent_wrong_grid_row_fails_the_verdict_and_fires_the_escape_clause_naming_it"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_a_clean_campaign_passes_with_the_k_the_estimator_and_the_turn_caps_printed"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_a_campaign_without_all_four_blocks_lists_the_missing_ones_and_never_passes"
        status: pass
    human_judgment: false
  - id: D10
    description: "The pre-registered thresholds and rules (30 s, 64 MiB, the K rule's order, the 2x estimator tie, the factor of 10 for T_gate, a timeout not being an escape) express the owner's intent for D-07, D-09, D-10 and D-20"
    requirement: INFR-03
    verification: []
    human_judgment: true
    rationale: "The numbers and orderings are the plan's and the research's, coded and tested for consistency with the plan text; whether they are the right pre-registration is the owner's call and is what the other-CLI review of PR 1 (D-19) is for. No test can say a pre-registered rule is wise."

duration: 27min
completed: 2026-10-06
status: complete
---

# Phase 2 Plan 03: Rod campaign grid, blocks and pre-registered verdict Summary

**The exact D-03 grid (1790 lengths per hand) and D-04 frontier, four guarded run blocks streaming JSONL, and a `verdict --campaign` that recomputes every class from raw records through kernel-free rules written before any data.**

## Performance

- **Duration:** 27 min
- **Started:** 2026-10-06T12:13:36Z
- **Completed:** 2026-10-06T12:40:45Z
- **Tasks:** 3 (Tasks 1 and 3 TDD)
- **Files modified:** 6 (all existing; no file created)

## Accomplishments

- `maths.lengths` reproduces the research's per-size counts exactly (M2 60, M2.5 78, M3 60, M3.5 82, M4 92, M5 100, M6 60, M7 70, M8 128, M10 133, M12 171, M14 140, M16 160, M18 216, M20 240, 1790 in all) in exact `Fraction`s, and a test pins them. The alternative reading (start at L = P) gives 1781 with rows lost only at M8 to M20. `frontier_turns` starts at 55, 60, 65 and 85 for M2, M2.5, M6 and M20 and every list ends at 250.
- A rod row now carries preview and fine meshes, gzip-1 on the named presets, the STL check under a 1 000 000 triangle ceiling (a skipped check is `checked: False` with every check field `None`) and STEP bytes and seconds; a void row records the postcondition only. Every optional field is set exactly when asked for or taken, and the parser refuses the rest.
- `run <block> --run-id ID [--k-from KSWEEP_ID]` runs ksweep, grid, frontier or ladder behind the protocol guard and the quiet gate, writes the header as the first JSONL line, streams and flushes one row per line, and prints and writes the per-size Markdown report. A run id that is not `[a-z0-9][a-z0-9-]{0,63}` or is already recorded exits 2; the file is opened exclusively. On this unlanded branch the real command exits 2 with `protocol guard: refused` and writes nothing.
- The pre-registered rules are tested kernel-free on synthetic records at every threshold: exactly 30.0 s and exactly 64 MiB are inside, the next float and the next byte are over; a non-decisive gate reads "seconds not established" and never "over"; a timeout is an over-budget cap when decisive and makes the bar "not established" otherwise.
- `verdict --campaign PREFIX` prints K with the rule's per-K table, the estimator with its largest error and T_gate, the pass bar and escape clause with every offending row, and the turn cap per size with its reason and source run. Exit 0 only on a clean pass; a missing block exits 1.
- Smoke on this host: `smoke --block ksweep`, `grid`, `frontier` and `ladder` each exit 0 with every Class cell `ok` (precise rel err +1.4e-06 to +3.6e-06, default rel err about +1.5e-05 to +2.7e-05, watertight at preview), 6 to 7 s wall each at host load 4 to 5. These are not campaign runs and carry no bound.

## Task Commits

1. **Task 1 RED: failing grid and frontier tests** - `079257f` (test)
2. **Task 1 GREEN: the exact D-03 grid and the D-04 frontier** - `e3b12c5` (feat)
3. **Task 2 part 1: the full rod and void row record** - `6112853` (feat)
4. **Task 3 RED: failing rod verdict rule tests** - `4dba7f5` (test)
5. **Task 3 GREEN: pre-registered verdict rules** - `b652a61` (feat)
6. **Task 2 part 2: guarded blocks, JSONL records, per-size reports** - `4964115` (feat)
7. **Task 3 RED: failing verdict subcommand tests** - `3dcea41` (test)
8. **Task 3 GREEN: verdict subcommand over recorded runs** - `ed00dda` (feat)

**Plan metadata:** recorded in the commit that follows this file (docs: complete plan)

## TDD Gate Compliance

- **RED (Task 1, `079257f`):** 11 tests fail on their assertions against behaviourless stubs (`lengths` returns a one-element list, `frontier_turns` returns `[int(d / pitch)]`, ...). Evidence under `--runxfail` with JUnit XML, classifier `RED_EVIDENCE_OK` (target `test_the_grid_has_the_pinned_length_count_per_size_and_1790_in_all`). Semantic assessment: the target ran and failed on the planned assertion; the stubs exist only so the module imports; the constants landed in the same commit and their one test passes by design.
- **GREEN (Task 1, `e3b12c5`):** 13 of 13 pass, markers removed.
- **RED (Task 3 rules, `4dba7f5`):** 53 tests fail on their assertions (plain assertions, or `DID NOT RAISE` where a refusal is expected) against stubs returning sentinels (`("stub",)`, `-1`, `("not established", ("stub", "stub"))`). Classifier `RED_EVIDENCE_OK`, target `test_select_k_takes_the_fewest_fine_triangles_at_the_standard_max`. Semantic assessment as above. Two stub-related failure shapes were fixed before the commit: `KeyError` on an empty `turn_caps` result (the stub now returns a `TurnCap` so tests fail on values) and a stub that made one test pass.
- **GREEN (Task 3 rules, `b652a61`):** 56 of 56 pass.
- **RED (Task 3 verdict subcommand, `3dcea41`):** 11 tests, 11 failures on assertions against `verdict_campaign` returning 99 and stub `k_scores` / `escape_rows`; classifier `RED_EVIDENCE_OK`, target `test_a_silent_wrong_grid_row_fails_the_verdict_and_fires_the_escape_clause_naming_it`.
- **GREEN (Task 3 verdict subcommand, `ed00dda`):** 11 of 11 pass.
- **REFACTOR:** none; no commit.
- The plan expected one RED and one GREEN for Task 3; it has two pairs (see Deviations 2).

## Files Created/Modified

- `bench/thread_spike/maths.py` - grid, frontier, sample sizes, K candidates, void clearance, depth presets
- `bench/thread_spike/measure.py` - `gzip1`, `step_export`
- `bench/thread_spike/worker.py` - rod and void kinds, per-preset gzip and check under the ceiling, STEP
- `bench/thread_spike/verdict.py` - wire shape fields, `HeaderRecord`, `parse_result_row`, every verdict rule, `TurnCap`, `KScore`
- `bench/thread_spike/__main__.py` - `RUN_ID`, `RESULTS_DIR`, `Campaign`, four blocks, `run_block`, `smoke_block`, `aggregate_table`, `report`, `verdict_campaign`
- `tests/test_bench.py` - 131 new tests (199 in the file, 459 in the suite)

## Decisions Made

- The verdict ignores every stored verdict key in a JSONL row and recomputes the class, so editing a row by hand cannot change an outcome (T-02-09).
- K is read from a K-sweep record only; `run` refuses `--k-from` on the sweep itself and requires it on every other block.
- A smoke run and the `verdict` subcommand both use the same rules and report code as a campaign run, so what is smoke-tested is what will run.
- `gate_tolerance` works on the decimal text of the error. At an error of exactly 1e-5 it gives 1e-4, but a measured 1e-6 carrying float noise rounds up to 2e-5; that is the rule as written and real data are never on the boundary. The tests avoid the boundary for that reason.
- The estimator tie rule is tested at ratios 1.99 and 2.01, not at exactly 2.0: the errors come from volumes, so they carry about 1e-16 absolute noise, which is 1e-11 relative at 1e-5. The exact-boundary pins (30.0 s, 64 MiB, T_PASS) are on values the code compares directly.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] RED commits made of strict-xfail tests over stubs**
- **Found during:** Tasks 1 and 3 (RED)
- **Issue:** the pre-commit hook runs `make verify` including pytest and `--no-verify` is forbidden, so a commit of genuinely failing tests cannot land; tests importing symbols that do not exist fail collection for the whole file, which is `INVALID_RED`.
- **Fix:** behaviourless stubs (sentinel returns, `# noqa: ARG001`) and `xfail(strict=True)` markers; evidence from a `--runxfail` JUnit run through `gsd-tools check tdd-red-evidence`; the GREEN commit removes the stubs and markers, so a strict xfail that starts passing could not be left behind.
- **Files modified:** `bench/thread_spike/maths.py`, `bench/thread_spike/verdict.py`, `bench/thread_spike/__main__.py`, `tests/test_bench.py`
- **Verification:** classifier `RED_EVIDENCE_OK` three times; `make verify` green on every commit that landed.
- **Committed in:** `079257f`, `4dba7f5`, `3dcea41`, and their GREEN commits.

**2. [Rule 3 - Blocking] Task 2 needs Task 3's rules, so the tasks ran out of order**
- **Found during:** Task 2 planning
- **Issue:** Task 2's blocks call `over_budget`, `frontier_stop` and `select_k` (and the report needs the budget helpers), and its verify needs `smoke --block frontier` to print a stop line; the plan defines those functions, with their TDD tests, only in Task 3. Implementing them in Task 2 would have left Task 3 with nothing to be RED about.
- **Fix:** Task 2 was split. Its wire shapes, worker and measure changes landed first (`6112853`), then Task 3's pure rules as a RED/GREEN pair (`4dba7f5`, `b652a61`), then Task 2's blocks, run flow, report and smoke (`4964115`), then Task 3's `verdict` subcommand as a second RED/GREEN pair (`3dcea41`, `ed00dda`). Plan commit messages are kept for the two commits the plan names (`feat(02-03): guarded rod campaign blocks ...`, `feat(02-03): pre-registered verdict rules ...`).
- **Files modified:** none beyond the plan's list
- **Verification:** every acceptance criterion of all three tasks re-run at the end (below).
- **Committed in:** the eight commits above.

**3. [Rule 2 - Missing critical] `k_scores` and `escape_rows` added to verdict**
- **Found during:** Task 3 (`verdict` subcommand)
- **Issue:** the plan asks `verdict` to print "K selected and the rule's table" and "the escape clause (fired or not, with rows)", but `select_k` returned only the winner and nothing named the escape rows. Re-deriving them in `__main__` would have copied the rule in a second place.
- **Fix:** `k_scores` (per-K counts, totals only for qualifying Ks) with `select_k` now reading it, and `escape_rows` (failure, worker_died, silent_wrong inside the standard range, rod or void, either hand). Both are pure and tested. Not in the plan's interface list.
- **Files modified:** `bench/thread_spike/verdict.py`, `bench/thread_spike/__main__.py`, `tests/test_bench.py`
- **Committed in:** `3dcea41`, `ed00dda`

**4. [Rule 2 - Missing critical] A missing rod block makes `verdict` exit 1**
- **Found during:** Task 3 (`verdict`)
- **Issue:** the plan says exit 0 only when the pass bar held and no escape fired. A campaign with a held grid but no frontier or ladder run satisfies that wording while saying nothing about the frontier or the mesh ladder, and the plan also says missing blocks are never treated as passing.
- **Fix:** exit 0 additionally requires all four of ksweep, grid, frontier, ladder to have been read; missing ones are listed. Tested.
- **Files modified:** `bench/thread_spike/__main__.py`, `tests/test_bench.py`
- **Committed in:** `ed00dda`

### Interpretations

- **One check ceiling per request.** The plan says the STL check runs at preview on every row and at fine only at or under 1 000 000 triangles, but its interface gives one `check_ceiling: int` per request. The ceiling applies to every mesh in a request. The preview mesh stays far below it at every grid length (a 0.05 mm mesh of M20 L200 is 605 450 triangles, so 0.08 mm is smaller), but the largest frontier rows (M20 at 250 turns, 625 mm) may exceed it at preview too; those checks are skipped, recorded as not checked, and counted in the "Checks skipped" column. Nothing reads a skip as a pass.
- **The ladder runs on `SAMPLE_SIZES`.** The plan's block list says SIZES for the ladder; its Task 1 comment (from RESEARCH Open Question 7) says SAMPLE_SIZES serve the K sweep, the reference rows and the ladder. The comment was followed: 8 sizes at 10 turns and the standard max, 6 presets each, 16 rows. Switching to all 15 sizes is a one-word change if the owner wants it.
- **Smoke exit code.** `smoke --block` exits 0 only when every row classifies `ok`, which is stricter than "every row was measured": the plan's own `fails_when` reads any failure, silent_wrong, timeout or worker_died Class cell as a failure.
- **Over-budget lines on a non-decisive run.** Every row slower than 30 s on a non-decisive run prints its "seconds not established" line in the report, so a loaded run could list many rows. Left as is: each is a row where a timing claim was withheld, and the owner runs the timing campaign detached.

---

**Total deviations:** 4 auto-fixed (2 blocking, 2 missing critical) and 4 interpretations
**Impact on plan:** the ordering change and the two added helpers were needed to build the plan's own behaviour without duplicating a rule or leaving Task 3 untestable; no scope creep. The interpretations are the places where the plan contradicts itself or leaves a number open, each stated here so the owner can overrule it.

## Issues Encountered

- One pre-commit run rejected a commit: ruff ARG001 on `frontier_stop`'s unused `void` argument. My manual lint check before that commit had already printed the failure and I committed anyway; the hook caught it. Fixed by naming the void row's own turn count in its stop message, which uses the argument for real; the retried commit passed. Later commits were preceded by a clean lint and typecheck.
- `tests/test_pool.py::test_a_dying_worker_surfaces_as_broken_pool_and_is_replaced` (the flake logged in `deferred-items.md` by plan 02-02) did not fail in any of the eight commit hooks or the standalone `make verify` here (459 passed); host load was 4 to 5. No recurrence, so the trigger in `deferred-items.md` is unchanged.
- The estimator tie and the gate rounding are float-noise sensitive at exact boundaries (Decisions). Tests sit off the boundary on purpose.

## Known Stubs

None. The behaviourless stubs existed only inside the three RED commits and are real in their GREEN commits; `make verify`'s unfinished-work scan passes.

## Threat Flags

None. The new surface is what the plan's threat model names: the run id and the verdict prefix reach file paths only through the `RUN_ID` fullmatch and a fixed `RESULTS_DIR` (T-02-08), the JSONL is opened exclusively and the verdict recomputes classes (T-02-09), and rows run under the 120 s kill with a per-mesh temporary directory and a triangle ceiling on the Python check (T-02-10). No file under `bench/results/` was created; the directory appears at the first campaign run.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plans 02-04 and 02-05 can add constructions, controls and the pair check on the same `Worker`, `Campaign` and report code, and extend `verdict --campaign` with their sections.
- No campaign run has happened and none can: `run` exits 2 until PR 1 lands on origin/main. All numbers above are smoke output, not records.
- All ISO pitch values and the 200 mm length cap stay UNVERIFIED until Phase 4's row tests.
- No tech-debt or idea item filed by this plan.

## Self-Check: PASSED

- FOUND: `bench/thread_spike/{maths,measure,worker,verdict,__main__}.py` and `tests/test_bench.py` (modified; this plan creates no file)
- FOUND: commits `079257f`, `e3b12c5`, `6112853`, `4dba7f5`, `b652a61`, `4964115`, `3dcea41`, `ed00dda` (eight commits between `plan_head_before` and `plan_head_after`, measured with `git rev-list --count`)
- `make verify` exit 0 (459 passed, coverage 95.03 % over the 94 % floor, `Contracts: 7 kept, 0 broken.`)
- `smoke --block ksweep|grid|frontier|ladder` each exit 0, "not a campaign run" printed once, no Class cell outside `ok`
- `run grid --run-id plan-check --k-from none` exit 2 with `protocol guard: refused`, `bench/results/thread-spike/plan-check.jsonl` not written
- greps: `FRONTIER_MAX_TURNS = 250`, `VOID_CLEARANCE = 0.20`, `FINE_CHECK_CEILING = 1_000_000`, `BUDGET_BYTES = 64 * 1024 * 1024`, `GATE_FACTOR = 10` match; `grep -c -- '--k '` on `__main__.py` prints 0; `UNVERIFIED` matches on the length-cap comment

---
*Phase: 02-thread-spike*
*Completed: 2026-10-06*
