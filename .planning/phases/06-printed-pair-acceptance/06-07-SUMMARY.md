---
phase: 06-printed-pair-acceptance
plan: 07
subsystem: calc
tags: [measured-range-warning, d-09, r6, l17, pair-02, kernel-free]

requires:
  - phase: 06-printed-pair-acceptance
    provides: the shipped clearance default 0.15 mm (L17, 06-06) and the pinned run-1 record
provides:
  - screw.calc.printability, standard-library only: MEASURED_D_MIN_MM / MEASURED_D_MAX_MM (6.0 / 12.0, R6 r6-a), CLEARANCE_ENTRY "L17", CLEARANCE_RUN "06-print-run-1", measured_range_warning(d, pitch)
  - the D-09 warning in _nut, one producer for the UI, the API and the CLI
  - comments, docstrings and the overview no longer call the nut's clearance required
affects: [06-08 run 2, 06-09 threshold and L18, 06-10 acceptance print]

actuals:
  tokens: 4555
  tasks: 2
  commits: 2

key-files:
  created:
    - src/screw/calc/printability.py
  modified:
    - src/screw/calc/__init__.py
    - src/screw/calc/pair.py
    - src/screw/app.py
    - src/screw/static/app.js
    - tests/test_calc.py
    - tests/test_parity.py
    - tests/test_print_rules.py
    - docs/architecture/overview.md

key-decisions:
  - "R6 applied as r6-a: a nut warns when d < 6.0 or d > 12.0 (NaN d warns too); compared exactly on the stored float, no tolerance. The pitch is not read."
  - "The warning reads size alone, so a nut that took the default and one with a typed clearance carry it identically; the bolt never carries it."

requirements-completed: []

coverage:
  - id: D1
    description: "A nut outside M6 to M12 carries one warning naming d, M6 to M12, L17 and run 06-print-run-1, with or without a typed clearance"
    requirement: "PAIR-02"
    verification:
      - kind: unit
        ref: "tests/test_calc.py#test_a_nut_outside_the_measured_range_warns_with_or_without_a_typed_clearance"
        status: pass
    human_judgment: false
  - id: D2
    description: "The range edges: 5, 14 and one float outside 6 and 12 warn; 6, 8, 10, 12 and one float inside do not"
    requirement: "PAIR-02"
    verification:
      - kind: unit
        ref: "tests/test_calc.py#test_the_measured_range_edges_warn_on_the_outside_only"
        status: pass
    human_judgment: false
  - id: D3
    description: "The bolt never carries the measured-range warning"
    requirement: "PAIR-02"
    verification:
      - kind: unit
        ref: "tests/test_calc.py#test_a_bolt_never_carries_the_measured_range_warning"
        status: pass
    human_judgment: false
  - id: D4
    description: "The warning changes no row, sits after the download refusal and before the off-row warning, and the standing warning stays first"
    requirement: "PAIR-02"
    verification:
      - kind: unit
        ref: "tests/test_calc.py#test_the_measured_range_warning_changes_no_row_and_keeps_the_warning_order"
        status: pass
    human_judgment: false
  - id: D5
    description: "The CLI and the API print the same document, answer 200, and the sentence is in no JavaScript"
    requirement: "PAIR-02"
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_the_measured_range_warning_is_the_same_on_the_cli_and_the_api"
        status: pass
    human_judgment: false
  - id: D6
    description: "The range and the ids are pinned to the sizes and the run id of bench.print_rules"
    requirement: "PAIR-02"
    verification:
      - kind: unit
        ref: "tests/test_print_rules.py#test_the_measured_range_is_the_sizes_run_1_printed"
        status: pass
    human_judgment: false

duration: "about 25min of agent time, three full make verify runs included"
completed: 2026-10-23
status: complete
plan_head_before: 704bbfef3b67f19bfe1bb42ba27b4efb8700e9ff
plan_head_after: f6a50f4cf63f93befdc71e461c2fcd4a3a9ec459
---

# Phase 6 Plan 07: The measured-range warning Summary

**A nut whose d is outside 6.0 to 12.0 mm builds as asked and carries one more warning from `derive()` saying the clearance default was measured on M6 to M12 only (L17, run 06-print-run-1), identical on the CLI and the API and rendered by the page through `info.warnings` with no JavaScript change.**

## Accomplishments

- Task 1 (tracer, `95aa1f8`): new kernel-free `screw.calc.printability` with the R6 bounds and `measured_range_warning(d, pitch)`; `_nut` appends the result after the download-refusal loop and before the counterpart's off-row warning (so the off-row sentence is still last and the standing warning still first, `not a product build` clause intact). The `STANDING_WARNING` comment now says the first release after Phase 7 removes the last clause (06 D-15) and the `Counterpart` docstring says the clearance is the nut's own field with the L17 default. Sample sentence: `d 5 mm is outside M6 to M12, the sizes the clearance default was measured on (L17, run 06-print-run-1)`.
- Task 2 (`f6a50f4`): text-only corrections in `app.py` (module docstring, `nut_info`), `app.js` (typed-value memory, `write` comment), `pair.py` (the `PAIR_CLEARANCES` comment: proof bracket fixed in Phase 2, the printed ladder runs to 0.25 mm, outside it at its top step) and `docs/architecture/overview.md`. `PAIR_CLEARANCES` is unchanged.

## Task Commits

1. **Task 1: tracer, the warning** - `95aa1f8` feat(nut): warn where the clearance default was not measured (D-09)
2. **Task 2: comments and docs** - `f6a50f4` docs(06): stop calling the nut's clearance required in comments and the overview

`commits: 2` is measured from the ledger base `704bbfe`.

## Verification

- `make test PYTEST_ARGS="tests/test_calc.py tests/test_parity.py tests/test_print_rules.py -q -n0 --no-cov -k measured"`: `22 passed, 285 deselected` (the first run had 3 failures in my own new tests, fixed before any commit: a bolt of d 12 or 14 needs a wider s, and the ordering test needed an M5 x 0.8 nut for a download refusal and a d 5.5 nut for an off-row warning).
- `screw info nut --d 5 --pitch 0.8 --s 8 --m 4.7` carries a sentence with `L17`, `06-print-run-1` and `M6 to M12`: exit 0.
- Tracer gate (`human_verify_mode` end-of-phase, automated-only verify): the verify re-ran green before expansion.
- `make verify`: first run stopped at ruff (two SIM300 Yoda comparisons in my test, fixed); then `3534 passed in 205.68s (0:03:25)` before the Task 1 commit and `3534 passed in 204.75s (0:03:24)` before the Task 2 commit; both commit hooks passed (`make verify` Passed).
- Task 2 checks: `clearance` is required in `app.py` 0, `a required radial clearance` in the overview 0, `today the` in `app.js` 0, the `PAIR_CLEARANCES` literal still found; the Task 2 diff has only comment, docstring and Markdown lines.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `# noqa: ARG001` on `measured_range_warning`**
- **Found during:** Task 1.
- **Issue:** the plan fixes the signature `(d, pitch)` and the key link `measured_range_warning(p.d, p.pitch)`, but under R6 (r6-a) `pitch` is not read, and ruff selects `ARG`, which would fail the gate.
- **Fix:** kept the plan's signature and added a `# noqa: ARG001` with the reason in the docstring. Dropping the parameter was the alternative; it would have broken the plan's stated key link.
- **Files modified:** src/screw/calc/printability.py
- **Commit:** `95aa1f8`

**2. [Rule 2 - Consistency] One more stale comment fixed in `app.js` (`showCounterpart`)**
- **Found during:** Task 2.
- **Issue:** the comment above `showCounterpart` said that with nothing typed the nut "opens with its clearance empty and builds nothing", false since L17, and the plan's truth says no comment may still say so. It was not in the plan's list of lines.
- **Fix:** reworded to say the nut opens at its default clearance (L17); the rest of the comment is unchanged. Comment only.
- **Files modified:** src/screw/static/app.js
- **Commit:** `f6a50f4`

No existing test needed changing for the new sentence.

## Issues Encountered

None beyond the self-inflicted test and lint failures above.

## Authentication Gates

None.

## Known Stubs

None.

## Threat Flags

None. The sentence is built from a finite validated float and module constants and is written by the page with `textContent` (T-06-14); T-06-15 is mitigated by a test that the rows and every other warning are the same with the sentence switched off, and by the 200 on the API.

## Ideas and debt

None filed.

## Open for the next plans

- INFO-04 stays Pending (the threshold comes from run 2, 06-09); PAIR-05 stays Pending (the acceptance print, 06-10). `requirements-completed` is empty by design: the plan lists PAIR-02, which 06-06 already completed.
- `app.js` line 318 still says "a nut with no clearance typed" for a part that cannot build yet; a user can still clear the field, so it was left.
- The untracked `.planning/HANDOFF.json`, `.planning/phases/05-hex-nut-and-kernel-pair-proof/.continue-here.md` and `.planning/ui-reviews/` were never staged.

## Self-Check: PASSED

Checked after writing: `src/screw/calc/printability.py` exists and defines `measured_range_warning`; `95aa1f8` and `f6a50f4` are ancestors of HEAD.
