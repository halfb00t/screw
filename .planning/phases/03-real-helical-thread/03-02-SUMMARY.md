---
phase: 03-real-helical-thread
plan: 02
subsystem: params
tags: [pydantic, model-validator, iso-68-1, fractions, info-document, 422]

requires:
  - phase: 03-real-helical-thread
    provides: calc.thread (thread_depth, closed_volume, T_GATE) and the gated sewn-thread builder (plan 03-01)
provides:
  - "calc.thread: MAX_TURNS = 250, turns_of, root_radius_refusal, turn_cap_refusal (kernel-free, exact-decimal reading)"
  - "params: pitch_too_coarse and turn_cap 422s with ctx.fields, so the page highlights both fields and the CLI message names them"
  - "calc: STANDING_WARNING and the D-05 info rows d, pitch, length, turns, volume, thread_depth, minor_diameter"
affects: [03-03, 03-04, 03-05, 03-06, 03-07, phase-04, phase-07]

actuals:
  tokens: 5500
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "model-level refusals are after-validators raising PydanticCustomError with ctx.fields; the rule text lives kernel-free in calc.thread and is imported lazily inside the validator (calc/__init__ imports params)"
    - "a user-typed number is read as Fraction(repr(x)) for any comparison that is a measured boundary"
    - "a computed info row is appended only when finite; otherwise a warning names the row and its formula"

key-files:
  created: []
  modified:
    - src/screw/calc/thread.py
    - src/screw/params.py
    - src/screw/calc/__init__.py
    - tests/test_thread_maths.py
    - tests/test_params.py
    - tests/test_calc.py
    - tests/test_api.py
    - tests/test_cli.py
    - tests/test_parity.py

key-decisions:
  - "Both refusals are 422s naming both fields and never a trim: the 250-turn cap (L11's measured frontier) and the root-radius bound (D-04) are explicit-choice conflicts under L02"
  - "The cap compares exact decimals, so all 15 measured 250-turn rows are accepted (M4 175 mm at 0.7 included) and 250 turns plus one ulp of length is refused"
  - "STANDING_WARNING replaces the skeleton warning; it stays first on every document and is asserted on the API, the CLI and the parity test"

patterns-established:
  - "Refusal text carries the field names first ('d and pitch: ...'), because the CLI prints no loc for a model-level error"

requirements-completed: [THRD-01]

coverage:
  - id: D1
    description: "A pitch with no root radius (including pitch=1e300) is a 422 pitch_too_coarse with ctx.fields [d, pitch] on both bolt routes and an exit-2 error naming d and pitch on the CLI, before any build"
    requirement: THRD-01
    verification:
      - kind: unit
        ref: "tests/test_params.py#test_a_pitch_with_no_root_radius_is_refused_naming_d_and_pitch"
        status: pass
      - kind: integration
        ref: "tests/test_api.py#test_a_thread_that_cannot_be_made_or_was_never_measured_is_a_422_naming_both_fields"
        status: pass
      - kind: integration
        ref: "tests/test_cli.py#test_a_thread_that_cannot_be_made_exits_2_naming_both_fields"
        status: pass
      - kind: unit
        ref: "tests/test_thread_maths.py#test_a_pitch_one_part_in_a_billion_inside_the_root_bound_is_accepted_and_outside_refused"
        status: pass
    human_judgment: false
  - id: D2
    description: "A length past 250 turns, read as exact decimals, is a 422 turn_cap naming length and pitch, 250 and 2026-10-08-a-frontier; exactly 250 turns and all 15 measured rows are accepted"
    requirement: THRD-01
    verification:
      - kind: unit
        ref: "tests/test_thread_maths.py#test_every_measured_250_turn_row_is_accepted"
        status: pass
      - kind: unit
        ref: "tests/test_thread_maths.py#test_one_ulp_past_250_turns_is_refused_naming_both_fields_and_the_run"
        status: pass
      - kind: unit
        ref: "tests/test_params.py#test_a_length_past_250_turns_is_refused_naming_length_and_pitch"
        status: pass
      - kind: integration
        ref: ".venv/bin/screw info bolt --length 300 exits 2 with 'error: length and pitch:' and the run id; --d 4 --pitch 0.7 --length 175 exits 0"
        status: pass
    human_judgment: false
  - id: D3
    description: "The info document lists d, pitch, length, turns, volume, thread_depth, minor_diameter in that order with the closed-form volume, exact turns and the profile-labelled depth and minor diameter, and carries the threaded-rod warning first on the API and the CLI"
    requirement: THRD-01
    verification:
      - kind: unit
        ref: "tests/test_calc.py (rows, order, units, turns 9.0, labels, standing warning)"
        status: pass
      - kind: integration
        ref: "tests/test_parity.py#test_the_cli_and_the_api_print_the_same_document"
        status: pass
      - kind: integration
        ref: "tests/test_api.py#test_the_default_info_document"
        status: pass
    human_judgment: false
  - id: D4
    description: "A computed row that is not a finite number is left out and explained in warnings, and the standing warning stays first"
    requirement: THRD-01
    verification:
      - kind: unit
        ref: "tests/test_calc.py#test_an_infinite_diameter_leaves_out_every_row_it_would_make_infinite"
        status: pass
      - kind: unit
        ref: "tests/test_calc.py#test_a_volume_that_overflows_is_absent_and_explained_not_a_500"
        status: pass
    human_judgment: false

duration: 6min
completed: 2026-10-10
status: complete
commits: 2
plan_head_before: e8074017729edafa14a76699247911c23a9fdbd5
plan_head_after: fd6792fb165b49c0242cd38a8de66763bc23cf9c
---

# Phase 3 Plan 02: Refusals and the thread's info document Summary

**A pitch with no root radius and a length past 250 turns (read as the exact decimals typed) are 422s naming both fields before any build, and the info document now reports turns, closed-form volume, ISO 68-1:2023 depth and minor diameter under the threaded-rod warning.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-10-10T14:03:54Z
- **Completed:** 2026-10-10T14:09:48Z
- **Tasks:** 2
- **Files modified:** 9 (0 created, 9 modified)

## Accomplishments

- `calc/thread.py` gained `MAX_TURNS = 250`, `_exact` (`Fraction(repr(x))`), `turns_of`, `root_radius_refusal` and `turn_cap_refusal`, all kernel-free. Refusal texts start with the field names, carry the numbers (`:g`) and contain no braces.
- `params.py`: `FastenerParams._root_radius` raises `pitch_too_coarse` (`ctx.fields` `["d", "pitch"]`); `BoltParams._turn_cap` raises `turn_cap` (`["length", "pitch"]`). Both import `screw.calc.thread` inside the validator. Stale skeleton help text and the `INTERIM_MAX_MM` comment were rewritten (the bound itself did not change).
- `calc/__init__.py`: `STANDING_WARNING` replaces `SKELETON_WARNING`; `_bolt` appends `turns`, `volume`, `thread_depth`, `minor_diameter` only when finite, otherwise a warning naming the row and its formula.
- Real-process checks: `screw info bolt --length 300` exits 2 with `error: length and pitch: 300 turns is past the 250-turn cap, ... (run 2026-10-08-a-frontier); ...`; `--pitch 6` exits 2 with `error: d and pitch: ... the largest pitch for this d is 5.54256`; `--d 4 --pitch 0.7 --length 175` exits 0.

## Task Commits

1. **Task 1: refuse a pitch with no root radius and a length past 250 turns** - `e6ccfc3` (feat)
2. **Task 2: describe the thread on the info document and pin the threaded-rod warning** - `fd6792f` (feat)

**Plan metadata:** committed with this SUMMARY (docs: complete plan)

## Files Created/Modified

- `src/screw/calc/thread.py` - cap constant, exact-decimal reading, the two refusal rules
- `src/screw/params.py` - the two after-validators, thread-era help text, rewritten `INTERIM_MAX_MM` comment
- `src/screw/calc/__init__.py` - `STANDING_WARNING`, the D-05 rows with the finite-or-warn loop
- `tests/test_thread_maths.py`, `tests/test_params.py`, `tests/test_calc.py`, `tests/test_api.py`, `tests/test_cli.py`, `tests/test_parity.py` - tests for all of the above

## Decisions Made

- Followed the plan's formulas and wording. Text choices not fixed by the plan: the root-radius text reads `d and pitch: the root radius d/2 - 5H/8 of the ISO 68-1:2023 basic profile is <r> mm at d <d> and pitch <p>, and must be above 0; the largest pitch for this d is <P>`; the cap text is `length and pitch: <turns> turns is past the 250-turn cap, the most measured (run 2026-10-08-a-frontier); shorten length or raise pitch`.
- The interim-bound tests moved the `length` case to `{"pitch": 400.0, "d": 1000.0}` as the plan specified (250 turns at the bound, root radius above 0).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The plan's behaviour line for `d=1e200` expects `minor_diameter` absent; it is a finite number**
- **Found during:** Task 2 (first `make verify`: `tests/test_calc.py` asserted it absent)
- **Issue:** `1e200 - 2 * 0.541...` is a finite float (1e200). Leaving a finite, correctly computed row out would be the code lying in the other direction; only `d=inf` makes it non-finite. `volume` does overflow at 1e200 (`ro**2` raises `OverflowError`) and is absent as planned.
- **Fix:** the test split in two: `d=1e200` asserts `volume` absent and explained, `minor_diameter` present; `d=inf` asserts both absent and explained and every remaining computed row finite. The implementation follows the plan's rule ("appended only when finite") unchanged.
- **Files modified:** tests/test_calc.py
- **Committed in:** fd6792f

**2. [Rule 3 - Blocking] Two ruff E501 lines in the new code and tests (limit 100)**
- **Found during:** Task 1 (`make verify`)
- **Fix:** reflowed a docstring, the cap message and two comments; no behaviour change.
- **Committed in:** e6ccfc3

---

**Total deviations:** 2 auto-fixed (1 bug in the plan's test expectation, 1 blocking lint). **Impact on plan:** none on behaviour or the contracts.

## TDD Gate Compliance

Both tasks are `tdd="true"`. The pre-commit hook runs `make verify`, so a RED-only commit cannot land; RED was shown by running the new tests against the pre-change code, and test plus implementation are one commit per task.

- **Task 1 RED** (before any `src/` edit): `make test PYTEST_ARGS="tests/test_params.py tests/test_api.py tests/test_cli.py -q -n0 --no-cov"` gave `11 failed, 129 passed` on the planned assertions: `test_a_pitch_with_no_root_radius_is_refused_naming_d_and_pitch` (pitch 5.6 accepted), `test_a_length_past_250_turns_is_refused_naming_length_and_pitch`, six cases of `test_a_thread_that_cannot_be_made_or_was_never_measured_is_a_422_naming_both_fields` (two routes by three queries), and three of `test_a_thread_that_cannot_be_made_exits_2_naming_both_fields` (e.g. `pitch 1e300` ended `error: Geometry kernel failed (OverflowError)` instead of exit 2). `tests/test_thread_maths.py` could not be collected (`ImportError: cannot import name 'MAX_TURNS'`), so it counts only as a load failure, not as RED evidence. Semantic assessment: the target tests ran and failed on the planned assertions for the intended reason (the boundary accepted what D-01 and D-04 refuse).
- **Task 2 RED:** `tests/test_calc.py`, `tests/test_api.py` and `tests/test_parity.py` failed to import (`cannot import name 'STANDING_WARNING'`); `tests/test_cli.py` ran and `test_export_writes_stl_and_step_and_warns_on_stderr` failed on the new warning line (`1 failed, 31 passed`). The import failures are load failures, not RED evidence.
- `gsd_run check tdd-red-evidence` was not run (no persisted record, as in plan 03-01).

## Issues Encountered

- A macOS `sed -i` without a backup suffix failed once while reverting an import in `tests/test_api.py` (it read the script as the suffix); redone with a Python edit. No effect on the tree.

## Verification

- `make verify` after Task 1 (in the hook): ruff passed, mypy `Success: no issues found in 46 source files`, `Contracts: 7 kept, 0 broken`, pytest `791 passed in 67.63s`, coverage 96.73 % against the 94 floor.
- `make verify` after Task 2, last run before the final commit (the hook re-ran it and passed): `794 passed in 29.93s`, coverage `96.76%` against the 94 floor, ruff `All checks passed!`, mypy `Success: no issues found in 46 source files`, `Contracts: 7 kept, 0 broken`.
- Acceptance greps: `grep -n '^from screw.calc' src/screw/params.py` and `grep -n 'walking skeleton' src/screw/params.py` print nothing; `git grep -n SKELETON_WARNING -- src tests` and `git grep -n 'walking skeleton' -- src/screw/calc` print nothing; both `PydanticCustomError("pitch_too_coarse"` and `PydanticCustomError("turn_cap"` are present.
- Task 2's piped CLI check (`--d 3.5 --pitch 0.6 --length 5.4`): rows in the planned order, `turns == 9.0`, first warning the standing warning.

## Debt

- Resolved: none. Filed: none.
- Noted, not filed: the `src/screw/__init__.py` module docstring still describes the walking skeleton (a plain unthreaded cylinder); the plan scoped only `calc` and `params`. Plan 03-07 or the first docs sweep should reword it.

## Known Stubs

None.

## Threat Flags

None. The surfaces touched are the plan's T-3-04 (250-turn cap before the pool, mitigated), T-3-05 (root-radius refusal before `helical.section`, mitigated) and T-3-06 (finite-or-warn rows, exact turns, closed-form volume, mitigated), each tested.

## Next Phase Readiness

Ready for 03-03. The model boundary now refuses a root radius at or below 0 and more than 250 turns, so the kernel only sees parameters inside the measured construction cap. `d < ~0.02` mm with a tiny `length` (the 1e-5 mm crash band from 03-CONTEXT) is still guarded only by the D-17 doorway guard in `helical.thread`, as decided.

## Self-Check: PASSED

Modified files exist on disk; commits `e6ccfc3` and `fd6792f` are ancestors of HEAD; `git rev-list --count e807401..HEAD` read 2 before this SUMMARY.

---
*Phase: 03-real-helical-thread*
*Completed: 2026-10-10*
