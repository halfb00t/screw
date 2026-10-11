---
phase: 03-real-helical-thread
plan: 01
subsystem: solid
tags: [cadquery, opencascade, thread, iso-68-1, brepgprop, postcondition-gate, lru_cache, import-linter]

requires:
  - phase: 02-thread-spike
    provides: the measured sewn twist-section builder (K = 3), the closed form, T_gate, the known-bad controls (L11)
provides:
  - screw.calc.thread: the ISO 68-1:2023 basic-profile maths, T_GATE = 9e-05 and the NaN-safe volume_check
  - screw.solid.helical: the one helical builder (section, twist, thread) taking the length in mm, with the tail fold and the D-17 doorway guard
  - screw.solid.check_solid and precise_volume: the THRD-04 postcondition inside the function lru_cache wraps
  - export-status and STL-header checks in _write_export
  - the default bolt on the API, the CLI and the pool is a real thread
affects: [03-02, 03-03, 03-04, 03-05, 03-06, 03-07, phase-04, phase-05]

actuals:
  tokens: 11991
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "the gate sits inside the function lru_cache wraps, so a raise is never stored; the bytes cache only puts a returned export"
    - "NaN-safe comparison written as `not abs(rel) <= T_GATE`"
    - "positive control for every gate: a known-bad build fed through build() with bolt.rod monkeypatched, refused twice, cache size unchanged"

key-files:
  created:
    - src/screw/calc/thread.py
    - src/screw/solid/helical.py
    - tests/test_thread_maths.py
    - docs/tech_debt/resolved/2026-10-06-collapsed-thin-solid-served-as-200.md
  modified:
    - src/screw/solid/__init__.py
    - src/screw/solid/bolt.py
    - pyproject.toml
    - tests/test_solid.py
    - tests/test_api.py
    - tests/test_cli.py
    - docs/tech_debt/INDEX.md

key-decisions:
  - "The gate reads the signed relative error and refuses on `not abs(rel) <= T_GATE`; the text carries the precise volume, the closed form, the error as :+.3e and L11"
  - "helical.thread takes the length in mm and folds a tail below MIN_TAIL_MM (1e-3, INTERIM) into the previous segment; a length below it, or NaN, is a BuildError before any kernel call (D-17)"
  - "The params lower bound the blocker item suggested was not added; D-04 and D-17 cover it"

patterns-established:
  - "Kernel-free oracle in screw.calc.thread, kernel builder in screw.solid.helical, gate in screw.solid: the maths decides, the solid module acts"
  - "Tests that build a shape no parameter set makes call check_solid directly (positive controls, the void)"

requirements-completed: [THRD-01, THRD-04]

coverage:
  - id: D1
    description: "The default bolt is one valid solid whose precise volume is within T_GATE of the closed form and more than 1 % from the old cylinder, with z exact and x/y within 1e-4"
    requirement: THRD-01
    verification:
      - kind: unit
        ref: "tests/test_solid.py#test_the_default_bolt_is_one_valid_thread_six_by_six_by_twenty"
        status: pass
    human_judgment: false
  - id: D2
    description: "The default part is the same gated thread on the API STEP route, the CLI STL export and the worker pool"
    requirement: THRD-01
    verification:
      - kind: integration
        ref: "tests/test_api.py#test_the_default_part_served_is_the_gated_thread"
        status: pass
      - kind: integration
        ref: ".venv/bin/screw export bolt -o x.stl --quality preview (1,578,084 bytes)"
        status: pass
      - kind: integration
        ref: "tests/test_pool.py (real worker process)"
        status: pass
    human_judgment: false
  - id: D3
    description: "The gate refuses wrong builds by volume and sign, never caches them, and runs in the fixed order count, validity, volume; lengths off whole turns build and end at their length; tiny lengths refuse before the kernel"
    requirement: THRD-04
    verification:
      - kind: unit
        ref: "tests/test_solid.py#test_the_gate_refuses_the_naive_sweep_the_kernel_calls_valid"
        status: pass
      - kind: unit
        ref: "tests/test_solid.py#test_the_gate_refuses_the_inverted_one_pipe_twist_by_its_sign"
        status: pass
      - kind: unit
        ref: "tests/test_thread_maths.py (boundary pairs on both signs, NaN, inf, closed form not positive)"
        status: pass
      - kind: unit
        ref: "tests/test_solid.py#test_a_length_off_the_whole_turns_builds_through_the_gate_and_ends_at_its_length"
        status: pass
    human_judgment: false
  - id: D4
    description: "A broken export (exportStl False, STEP status not RetDone, bad STL header) is a BuildError and the collapsed-solid blocker is retired"
    requirement: THRD-04
    verification:
      - kind: unit
        ref: "tests/test_solid.py#test_an_stl_that_is_not_a_closed_solids_mesh_is_a_build_error"
        status: pass
      - kind: integration
        ref: "tests/test_api.py#test_a_failed_export_is_a_422_and_never_enters_the_bytes_cache"
        status: pass
      - kind: integration
        ref: "tests/test_cli.py#test_a_length_too_short_to_model_exits_1_from_the_real_process"
        status: pass
    human_judgment: false

duration: 11min
completed: 2026-10-10
status: complete
commits: 3
plan_head_before: 1fa9a41e1dcd3dccb7cd58378d1b13460c81c8c8
plan_head_after: de9304ede0c8c02e712b658b60d19a0762bf7db6
---

# Phase 3 Plan 01: The gated sewn-thread tracer Summary

**The default bolt is now the L11 sewn twist-section thread on the API, CLI and pool, built behind a signed precise-volume gate inside the lru_cache'd function, with the collapsed-solid blocker retired.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-10-10T13:43:33Z
- **Completed:** 2026-10-10T13:54:47Z
- **Tasks:** 3
- **Files modified:** 11 (4 created, 7 modified)

## Accomplishments

- `calc/thread.py` (kernel-free) carries the moved profile maths, `T_GATE = 9e-05` and `volume_check`; `solid/helical.py` carries the moved builder with the length-in-mm tail fold and the `MIN_TAIL_MM` doorway guard; `bolt.rod` replaces `cylinder`.
- `check_solid` runs inside `_build`, so a refused build is never stored by `lru_cache` and never exported. Positive controls (the naive sweep at three L11 rows, the inverted one-pipe twist) are refused by volume and sign, twice, with the cache size unchanged.
- `make verify` carries the sample: default rod, void at `VOID_CLEARANCE`, sub-turn, non-integer, and three float-drift lengths. M6 x 20 builds in 0.2 s at relative error +9.71e-10.
- Export checks: `exportStl` False, a STEP status other than `IFSelect_RetDone`, and an STL header disagreeing with its byte length or under 4 facets are each a `BuildError`; `length` 1e-8 and 1e-9 are a 422 `build_error` on the API and an `error:` exit 1 on the CLI.

## Task Commits

1. **Task 1: default bolt is the gated sewn thread (tracer)** - `510b7b1` (feat)
2. **Task 2: positive controls and the make verify sample** - `f569238` (test)
3. **Task 3: broken export is a BuildError, blocker retired** - `de9304e` (fix)

**Plan metadata:** committed with this SUMMARY (docs: complete plan)

## Files Created/Modified

- `src/screw/calc/thread.py` - profile maths, `T_GATE`, `volume_check`
- `src/screw/solid/helical.py` - `section`, `twist`, `thread`, builder constants with their L11 comments
- `src/screw/solid/bolt.py` - `rod(p)` over `helical.thread`
- `src/screw/solid/__init__.py` - `PRECISE_EPS`, `precise_volume`, `check_solid`, `_check_stl`, export status checks
- `pyproject.toml` - contract 8 ignores `screw.solid -> OCP` and `screw.solid.** -> OCP`
- `tests/test_thread_maths.py` (new), `tests/test_solid.py`, `tests/test_api.py`, `tests/test_cli.py` - tests for all of the above
- `docs/tech_debt/resolved/2026-10-06-collapsed-thin-solid-served-as-200.md`, `docs/tech_debt/INDEX.md` - blocker retired

## Decisions Made

- Gate text format and NaN-safe comparison as in key-decisions; no number was loosened and the default `Volume()` is not used anywhere in the gate.
- The tracer feedback gate: mode `end-of-phase`, the tracer `<verify>` is automated only, so it was re-run (targeted tests, `make lint-imports`, the shipped CLI export, `make verify` in the hook) and passed; expansion continued with no checkpoint.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Moved `tests/test_thread_maths.py` and the three `check_solid` unit tests from Task 2 into the Task 1 commit**
- **Found during:** Task 1 (first `make verify`)
- **Issue:** with only Task 1's planned tests, coverage read 92.51 % against the 94 floor (`calc/thread.py` 53 %), so the Task 1 commit could not pass its hook, and CLAUDE.md requires new behaviour to ship with its tests in the same change.
- **Fix:** `tests/test_thread_maths.py` (the whole planned content) and the count, validity and ordering tests of `check_solid` landed in Task 1. Task 2 then added the positive controls, the sample and the void to `tests/test_solid.py`. Total coverage after Task 1: 96.05 %; after Task 3: 96.56 %.
- **Files modified:** tests/test_thread_maths.py, tests/test_solid.py
- **Committed in:** 510b7b1

**2. [Rule 1 - Bug] Two assertions in the first draft of the maths tests were wrong**
- **Found during:** Task 1
- **Issue:** the back-flank probe at 15pi/8 + 0.01 lands on the crest (the flank ends at 15pi/8), and the refusal text said "closed-form" where the plan's tests look for "closed form".
- **Fix:** probe at 7pi/4 asserting four fifths of the way up; text reworded to "closed form".
- **Committed in:** 510b7b1

---

**Total deviations:** 2 auto-fixed (1 missing critical, 1 bug). **Impact on plan:** none on behaviour; only the split of tests between Tasks 1 and 2 moved.

## TDD Gate Compliance

Tasks 2 and 3 are `tdd="true"` but Task 1 (a tracer) had already built what Task 2 tests, so Task 2 has no failing RED to commit: its tests passed on first run. Evidence instead: mutation checks of `volume_check` after the tests passed (positive-form comparison failed the NaN case; `if False:` failed 13 tests including all four controls; dropping the sign failed the one-pipe control and the -1.0 case), and the source was restored. The plan's own text says the lengths 1e-8/1e-9 tests are answered by Task 1's doorway guard.

Task 3 had a real RED: with the old `_write_export` restored, 6 new tests failed for the planned reasons (a `FileNotFoundError` instead of `BuildError`, no STEP status check, no header check, a cached-key assertion). The RED was shown by running the tests against the old source and was not committed separately, because the pre-commit gate cannot take a failing suite; RED, GREEN and the debt move are one commit `de9304e`, as the plan specifies. The `gsd_run check tdd-red-evidence` classifier was not run.

## Issues Encountered

- The planner's probe reads `d=0.001, pitch=0.0001, length=0.01` at +9.590e-03; this run reads +9.858e-03 in three fresh processes (deterministic here). It is refused either way, and the tests assert only the sign and the 1e-03 exponent. The second fallback row (0.01, 0.0015, 0.3) reads -3.579e-04 as the research said. Not investigated further; the difference is probably the probe's builder (its tail handling) rather than the product's.
- `make test` re-created `.venv` after `pyproject.toml` changed (the stamp rule); no dependency changed.

## Verification

- `make verify`: ruff all checks passed; mypy `Success: no issues found in 46 source files`; import-linter `Contracts: 7 kept, 0 broken` (contract 8 `KEPT (5 ignored imports)`); pytest `758 passed in 55.16s`, coverage `96.56%` against the 94 floor.
- `.venv/bin/screw export bolt -o x.stl --quality preview` wrote a 1,578,084-byte STL.
- Acceptance greps for all three tasks pass; `git show --stat 510b7b1 -- bench/` is empty (no bench file edited).

## Debt

- Resolved: `docs/tech_debt/resolved/2026-10-06-collapsed-thin-solid-served-as-200.md` (blocker), INDEX row moved in `de9304e`; its `Resolved in:` line names the commit subject because the sha was not known when the file was written (plan 03-07 names it).
- Filed: none.

## Known Stubs

None.

## Threat Flags

None. The surfaces touched (query to kernel, CLI argv to kernel, the two caches) are the plan's T-3-01, T-3-02 and T-3-03, each mitigated and tested.

## Next Phase Readiness

Plans 03-02 onward build on `check_solid`, `helical.thread(..., clearance=, left_hand=)` and `calc.thread`. The `left_hand` field, the 250-turn and root-radius validators, and the pitch=1e300 / d=1e-9 inputs that now reach the kernel are still unguarded at the params boundary until plan 03-02. `bench/thread_spike/` still has its own copies of the moved code; plan 03-06 imports them back.

## Self-Check: PASSED

All created files exist on disk; commits `510b7b1`, `f569238` and `de9304e` are ancestors of HEAD.

---
*Phase: 03-real-helical-thread*
*Completed: 2026-10-10*
