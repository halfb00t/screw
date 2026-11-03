---
phase: 08-pre-release-gap-closure
plan: 05
subsystem: solid
tags: [fine-sweep, helical, uses-fine-sweep, nut, island, oper-03, d-01, d-02, d-16, d-19]

requires:
  - phase: 08-pre-release-gap-closure
    provides: "08-03's band walk records (bands are not wired here; they land in 08-12)"
provides:
  - "calc.thread.FINE_NUT_ABOVE and uses_fine_sweep(kind, d, pitch): exact-decimal predicate, a nut is fine strictly above d / pitch 6, every bolt False until 08-12"
  - "helical.thread / twist / section take fine=; FINE_SECTION_SAMPLES = 56 and FINE_TOLERANCE = (1e-6, 1e-6, 1e-4) set after SetMode and before Add"
  - "nut.void and bolt.thread pass fine=uses_fine_sweep(...)"
  - "Tests: the six island nuts build through the served path; call-order and sampling spies; the catalogue pinned to the eight moved nut rows"
affects: [08-06, 08-08, 08-12]

actuals:
  tokens: 4660
  tasks: 2
  commits: 2

plan_head_before: d4764de6a9a991379ad0876e35f16660bd24ac7e
plan_head_after: da29a12790ec29c539c65a8062690d78d0018e12

tech-stack:
  added: []
  patterns:
    - "The sweep is an argument (fine=), never a module global, so one process serves both sweeps"
    - "A spy whose fine has no default fails a call site that omits it"

key-files:
  created: []
  modified:
    - src/screw/calc/thread.py
    - src/screw/solid/helical.py
    - src/screw/solid/nut.py
    - src/screw/solid/bolt.py
    - tests/test_nut.py
    - tests/test_thread_maths.py

key-decisions:
  - "No new decision. D-01, D-02, D-16, D-19 and F2/F3 applied as written; L36 and L37 untouched"

requirements-completed: [OPER-03]

status: complete
---

# Phase 8 Plan 05: The fine sweep, the nut threshold and the bolt's route through the predicate

**`helical.thread(fine=True)` with 56 flank samples and `SetTolerance(1e-6, 1e-6, 1e-4)`, chosen by an exact-decimal `uses_fine_sweep`: nuts above d / pitch 6 take it (8 catalogue rows), every bolt stays on the shipped sweep until 08-12 adds the bands.**

## Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 (tracer) | Island nut, from the predicate through the fine sweep to a built nut | 5d8c0b7 | calc/thread.py, solid/helical.py, solid/nut.py, tests/test_nut.py, tests/test_thread_maths.py |
| 2 | Bolt call site through the predicate, catalogue pinned to the eight nut rows | da29a12 | solid/bolt.py, tests/test_nut.py, tests/test_thread_maths.py |

## What was done

- `calc/thread.py`: comment block (why: F2 and D-01; who: D-02, D-03, D-15, D-16 with the island's exact ratio 1100000/157143 and the 8 moved rows; D-19: no d / pitch-only bolt clause, 973 `ok` bolt readings, shipped sweep up to the wall of 20, built-there read at sampled ratios only, F3 and F13), `FINE_NUT_ABOVE = Fraction(6)` and `uses_fine_sweep`. No new import; no `FINE_BOLT_ABOVE`.
- `helical.py`: `section`, `twist` and `thread` take `fine: bool = False`. `SECTION_SAMPLES = 14` keeps its name and value; `fine=False` is the shipped sweep call for call (the tolerance call is skipped, 14 samples).
- `nut.void` and `bolt.thread` pass `fine=uses_fine_sweep(...)`. `solid/pair.py` and `calc/cost.py` are untouched (`git diff origin/main` is empty for both). The M8 evidence row's nut reaches `helical.thread` with `fine=True` through `build`, which is what `pair._shipped` calls (D-22).
- Tests: predicate at exactly 6 (False), 6.25 and the island (True), and 4.2 / 0.7 (float quotient 6.000000000000001, exact 6, False); `SetMaxSegments, SetMode, SetTolerance, Add` order for both twists of a fine thread and no `SetTolerance` on the shipped one; 56 against 14 points per flank spline; the six island nuts (d 2.2, R31's pitch 0.314286 via `oper_sets._pitch_params`, forms base, s4, m1, both hands) build, are valid, one solid, inside `T_GATE` of `nut_end_closed_volume`; default nut, default bolt stay on `fine=False`; a planted predicate reaches `helical.thread` as `fine=True`; the nut catalogue ids that are fine are exactly M5, M8, M10, M12, M14, M16, M18 and M20, no bolt row is fine.

## Verification

- Pre-change `make verify`: 5159 passed, 197.5 s wall (`time -p`, clean tree at d4764de).
- Post-change: `make verify` ran as the pre-commit hook on both commits and passed (hook wall 4:15 and 4:27, which includes the hook's own steps and the new fine-swept nut builds; not a like-for-like timing against the 197.5 s run, so no cost claim is made from it). `make lint typecheck lint-imports`: ruff clean, mypy --strict clean, 10 contracts kept.
- Focused: `make test PYTEST_ARGS="tests/test_thread_maths.py tests/test_nut.py -q -n0 --no-cov"`: 286 passed (task 1), the task 2 subset 29 passed.
- Acceptance greps: `fine=uses_fine_sweep(` prints 1 for `nut.py` and 1 for `bolt.py`; `import cadquery` count in `calc/thread.py` is 0; `^SECTION_SAMPLES = 14$` present; no `FINE_BOLT_ABOVE` outside comments.

## Re-pinned test values

None. No existing test pinned a figure of a moved nut row, so no pin was re-measured, and no pin that cites a runner run or a cost-model admission moved.

## Deviations from Plan

None - plan executed exactly as written. Two lint/type adjustments in the new tests only (a `noqa: N803` on cadquery's `includeCurrent` keyword in a spline spy; the pipe spy's `__getattr__` returns `object` because mypy forbids explicit `Any`).

## Known Stubs

None.

## Threat Flags

None. T-08-14 stays open by design: the fine sweep is not released until 08-08 lands `FINE_ENVELOPE` and 08-06 measures it on the runner (D-04); the local figures here are development evidence only.

## Debt filed

None.

## Notes for later plans

- 08-12 adds the bands and their clause. `test_no_bolt_is_fine_until_a_band_exists` (cells d 3 / pitch 0.35 among them) names the state of this plan and must change with the bands; `test_the_fine_sweep_moves_exactly_the_eight_nut_rows` is the one to keep green.
- From the commit 08-06 dispatches, `helical.py`, `bolt.py`, `nut.py` and the F3/F5 constants are frozen (F11).

## Self-Check: PASSED

- Files: all six modified files exist; commits 5d8c0b7 and da29a12 are ancestors of HEAD.
