---
phase: 07-operability-re-sweep
plan: 07
subsystem: testing
tags: [operability, kernel-walls, max-turns, field-ceilings, root-floor, min-tail, derive-walls, L20]

requires:
  - phase: 07-operability-re-sweep
    provides: "07-05: walls 40646134133, walk-down 40652801529, 5-rep walls confirm 40678150220, controls 40646142406 and the candidate walls"
provides:
  - "bench.oper_sets derive-walls: R3 and R7 to R10 over the committed records, with the confirm, printing every constant and each stop"
  - "bench.oper_lift.registered: validation under the registration-time guards (250 turns, 1e5 mm, root above 0), so pre-registered point files do not move with the walls"
  - "MAX_TURNS 90, MIN_TAIL_MM 1e-4, MIN_ROOT_RADIUS_MM 1e-2 and the field ceilings (MAX_FIELD_MM 1000 plus MAX_BOLT_D_MM, MAX_BOLT_LENGTH_MM, MAX_BOLT_K_MM, MAX_BOLT_THREAD_LENGTH_MM, MAX_NUT_M_MM, MAX_NUT_CLEARANCE_MM), each citing its run ids"
  - "L20 in the decision log; L11 and L12 point to it for the clauses it supersedes"
affects: [07-06, 07-09, 07-15]

actuals:
  tokens: 18866   # chars/4 over the added lines of src/, tests/ and bench/*.py across the three code and doc commits; docs excluded
  tasks: 3
  commits: 3      # MEASURED: git rev-list --count 100bb23..d65d3ab (before this SUMMARY's own commit)
plan_head_before: 100bb237aa0dfb48fba13ad99170e9e776432e82
plan_head_after: d65d3ab4f444eb612f74459e8f6f4fe117a8ffb9   # before this SUMMARY's own commit

tech-stack:
  added: []
  patterns:
    - "a constant in src/ that comes from a run is recomputed from the committed records by a test (derive_walls), so it cannot drift from its evidence"
    - "bench point files validate under bench.oper_lift.registered, the guards they were registered under, not the production constants"

key-files:
  created:
    - docs/tech_debt/active/2026-10-28-shank-fold-warning-rounds-the-numbers-it-compares.md
  modified:
    - src/screw/params.py
    - src/screw/calc/thread.py
    - src/screw/calc/cost.py
    - bench/oper_sets.py
    - bench/oper_lift.py
    - bench/nut_fine_caps.py
    - bench/corpus.py
    - bench/README.md
    - bench/export_cost.py
    - Makefile
    - docs/architecture/decision_log.md
    - docs/architecture/overview.md
    - docs/ideas/INDEX.md
    - docs/ideas/2026-10-11-oper-02-resweep-runs-the-controls.md
    - docs/tech_debt/INDEX.md

key-decisions:
  - "L20: MAX_TURNS 90, MAX_FIELD_MM 1000 with per-field exceptions, MIN_TAIL_MM 1e-4, MIN_ROOT_RADIUS_MM 0.01"
  - "Nut d has no wall constant (G27); the nut void floor is a guard, not a measured wall (G26)"
  - "A confirm failure at a decided decade lowers the ceiling to the next walked decade; a candidate decade the confirm does not hold is a stop"

requirements-advanced: [OPER-02, OPER-03]   # not marked complete: OPER-02 also covers the memory ceiling, gzip level, workers and cache budget (later plans), OPER-03 needs the cost model's admission
requirements-completed: []

duration: two sessions (context compacted once)
completed: 2026-10-28
status: complete
---

# Phase 7 Plan 07: The kernel's outer walls, measured Summary

Walls run 40646134133, walk-down 40652801529 and the 5-rep confirm 40678150220 now set the parameter model's outer walls through rules R3 and R7 to R10: 90 turns, a 1000 mm field ceiling with four per-field exceptions, a 1e-4 mm tail and a 0.01 mm root-radius floor, logged as L20.

## What was done

1. **Task 1 (tracer), `683a434`.** `derive_walls` and the `derive-walls` command, `oper_lift.registered`, and the root-radius floor in `src/screw/calc/thread.py` (`MIN_ROOT_RADIUS_MM = 1e-2`, three root rules). The floor item moved to `resolved/`.
2. **Task 2, `a804806`.** `MAX_TURNS`, `MIN_TAIL_MM` and the field ceilings written with their run ids. `INTERIM_MAX_MM` became `MAX_FIELD_MM`. A test recomputes every constant from the records. The lead-in debt item is resolved.
3. **Task 3, `d65d3ab`.** L20, the two "Superseded in part by L20" lines, the overview, and the controls idea moved to Done.

## `derive-walls` output

`python -m bench.oper_sets derive-walls --walls bench/results/phase-07/walls-40646134133 --down bench/results/phase-07/walls-down-40652801529 --confirm bench/results/phase-07/walls-confirm-40678150220` exits 0:

```
MAX_TURNS = 90  (R7: T, the smallest first ok step over 60 cells; 148 walls and walk-down readings, then the confirm at 90 turns: 60 cells x 5 repetitions, all ok)
  past it: 100 turns, 58 of 60 points: ok 5; turns100-bolt-M2.5-right, turns100-bolt-M3-right: refused 5
MAX_FIELD_MM = 1000.0  (R8: the ceiling value the most fields share, a tie to the lower)
bolt d: 999.999 mm (decade 1000, constant MAX_BOLT_D_MM); rests on ceiling-bolt-d-1000
bolt length: 10000.0 mm (decade 10000, constant MAX_BOLT_LENGTH_MM)
bolt s: 1000.0 mm (decade 1000, constant MAX_FIELD_MM)
bolt k: 100000.0 mm (decade 100000, constant MAX_BOLT_K_MM)
bolt thread_length: 100000.0 mm (decade 100000, constant MAX_BOLT_THREAD_LENGTH_MM)
nut s: 1000.0 mm (decade 1000, constant MAX_FIELD_MM)
nut m: 10000.0 mm (decade 10000, constant MAX_NUT_M_MM)
nut clearance: 496.999 mm (decade 1000, constant MAX_NUT_CLEARANCE_MM)
nut d: no constant of its own (G27: its limit is cost, first refused decade 10000 mm); under MAX_FIELD_MM 1000.0
MIN_TAIL_MM = 0.0001  (R9: 48 readings read after the confirm, 24 failing, the largest value at tail-d6-p1-right-1e-6)
MIN_ROOT_RADIUS_MM = 0.01  (R10: 270 readings read after the confirm, 122 failing, the largest value at root-bolt-M12-right-r0.0003)
differs from the candidate: nut d: candidate decade 1000 (tested 999.699) is not confirmed (cost), so no constant of its own
```

(Each "past it" line and the "rests on" lists are in the full output; only the lines that decide a constant are kept here.)

## Orchestrator rulings applied

- **G26** (R10 from group (d) rods only): `derive_walls` reads 30 rod cells and not nuts; MIN_ROOT_RADIUS_MM 0.01 from F = 3e-4 mm. The nut void rule uses the same constant as a guard. Applied in `src/screw/calc/thread.py` comments, in L20 ("It is not a measured void wall") and in the countersink item, which stays active.
- **G27** (nut d): no `MAX_NUT_D_MM`; `NutParams.d` uses `MAX_FIELD_MM` (1000, below the first refused decade 1e4). Applied in `src/screw/params.py`, in a test asserting the name does not exist, in `derive_walls` (`COST_LIMITED`) and in L20.
- **Commit rules and dirty files:** every commit used a plain `git commit` (hooks ran `make verify`), staged by explicit path, and `pin.sh` ran before each. The owner's dirty files were never staged.
- **Co-author trailer:** the orchestrator asked for `Co-Authored-By: Claude Opus 5.5`; the harness attribution reminder says `Claude Sonnet 5.5 <noreply@anthropic.com>`, which I used, as 07-05 did.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `oper_lift.registered`**
- **Found during:** Task 1
- **Issue:** once the model's walls moved, the pinned point files, the regenerated `walls-confirm.json` and `--check` would have changed with the production constants, against R30.
- **Fix:** `registered(kind, params, lift)` validates under 250 turns, 1e5 mm and a root above 0; `bench.oper_sets` and `bench/nut_fine_caps.py` use it, and the probe tests in `tests/test_oper.py` too.
- **Files modified:** bench/oper_lift.py, bench/oper_sets.py, bench/nut_fine_caps.py, tests/test_oper.py
- **Commit:** 683a434, a804806

**2. [Rule 1 - Bug] Tests built parts the new walls refuse**
- **Found during:** Tasks 1 and 2
- **Issue:** tests at d 0.001, pitch 0.0001, `s` 1e-170, 160 turns, 200 turns and `clearance` 1e5 became 422s.
- **Fix:** moved each to a part inside the walls that still exercises the same behavior, or to `oper_lift.registered` where the old cap is the point (the inverted one-pipe twist at 160 turns). The `s` 1e-170 API test became a 422 `pitch_too_coarse` test and its kernel-bound guard became the unit assertion `head_chamfer_kernel_bound(1e-170, 4.0) == math.inf` in `tests/test_calc.py`.
- **Commit:** 683a434, a804806

**3. [Rule 3 - Blocking] The phase 1 corpus held a 200-turn part**
- **Found during:** Task 2
- **Issue:** `bench/corpus.py`'s heaviest part, `d=100 length=200`, is 200 turns and is a 422 at the 90-turn wall; `load_sweep` raised for the whole default sweep.
- **Fix:** the last length is 90 mm (90 turns, the most the model admits). The `bench.export` examples in `Makefile`, `bench/README.md` and `bench/export_cost.py` follow. The corpus docstring said it stays fixed for comparison; the heaviest part's numbers in earlier runs are not comparable with a 90-turn part. **Owner attention:** this is a change to a fixed workload, made because the old part cannot be requested at all.
- **Commit:** a804806

**4. [Plan wording] Acceptance regex for per-field constants**
- **Issue:** `grep -c "^MAX_[A-Z]*_[A-Z]*_MM = "` cannot match `MAX_BOLT_THREAD_LENGTH_MM`.
- **Fix:** counted each constant by name instead: `MAX_FIELD_MM`, `MAX_BOLT_D_MM`, `MAX_BOLT_LENGTH_MM`, `MAX_BOLT_K_MM`, `MAX_BOLT_THREAD_LENGTH_MM`, `MAX_NUT_M_MM`, `MAX_NUT_CLEARANCE_MM`; each prints 1.

**5. [Rule 1 - Bug] `MIN_ROOT_RADIUS_MM` deleted by a replacement**
- **Found during:** Task 2; ruff F821 flagged it. Restored before any commit.

## Resolved and active debt

- **Resolved:** `docs/tech_debt/resolved/2026-10-11-root-radius-floor-is-not-the-kernel-boundary.md` (683a434) and `docs/tech_debt/resolved/2026-10-21-nut-lead-in-gate-refuses-a-valid-nut-at-huge-s.md` (a804806). The lead-in item is resolved by the wall: its three nuts build ok at s 1000 mm in 5 of 5 repetitions and are 422s at 1e4 and 1e5, the gate itself is not made precise.
- **Stays active:** `docs/tech_debt/active/2026-10-21-nut-countersink-cutter-crosses-the-axis-at-a-coarse-pitch.md` (G26: no measured void wall). Its next step cites run 40646134133 and the void walk.
- **Filed new:** `docs/tech_debt/active/2026-10-28-shank-fold-warning-rounds-the-numbers-it-compares.md` (nice): the shank-fold warning prints with `:g`, so a value near the 1e-4 mm line can read on the wrong side. Not fixed, outside this plan.
- **Idea closed:** `docs/ideas/2026-10-11-oper-02-resweep-runs-the-controls.md` moved to Done (controls run 40646142406; no THRD-04 test row changes).

## Known Stubs

None.

## Threat Flags

None. The walls lower the surface a request can reach; no new endpoint, auth path or file access.

## Verification

- `make verify` ran in the pre-commit hook for each of the three code and doc commits and passed (ruff, mypy --strict, import boundaries, unfinished-work scan, pytest). The flaky `tests/test_pool.py` queued-request test did not fail.
- `grep -c "^## L20 " docs/architecture/decision_log.md` prints 1; `grep -c "Superseded in part by L20"` prints 2; each run id L20 cites appears in `bench/RESULTS.md`.
- `python -m bench.oper_sets derive-walls ...` exits 0 and every constant in `src/` equals it (`tests/test_oper_followup.py::test_the_source_constants_equal_what_derive_walls_gives_for_the_records`).

## Self-Check: PASSED

Files found: src/screw/params.py, src/screw/calc/thread.py, bench/oper_sets.py, bench/oper_lift.py, the two resolved debt items, the active countersink item. Commits found on HEAD: 683a434, a804806, d65d3ab.
