---
phase: 04-iso-hex-bolts-and-screws
plan: 17
subsystem: ui
tags: [css, flexbox, info-panel, gap-closure, source-pin]

requires:
  - phase: 04-iso-hex-bolts-and-screws
    provides: plan 04-13 full-precision info rows (D-19) and plan 04-16 amended UI contract
provides:
  - wrapping info row in style.css (label claims half the row, a long value drops whole under it)
  - style.css source pin and its teeth in tests/test_parity.py
  - 01-UI-SPEC.md describing the wrapping row with the measured widths
affects: [verify-work UAT test 5 re-run, phase 04 verification]

actuals:
  tokens: 5200
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "CSS source pin: read style.css as text, compare pinned declarations per selector after stripping comments, with a teeth test (no browser in the gate, L01)"

key-files:
  created: []
  modified:
    - src/screw/static/style.css
    - tests/test_parity.py
    - .planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md

key-decisions:
  - "Label basis is the proportion 50%, not a length: no new value on the locked spacing scale (UI-SPEC extension rule 4)"
  - "overflow-wrap: anywhere stays on dd only inside the wrapping row, where it fires only for a value wider than a whole track"

patterns-established:
  - "Pinned-selector CSS check: iterate the pinned selectors, never the ones found in the sheet, so a deleted rule is reported"

requirements-completed: [INFO-03]

duration: 6 min
completed: 2026-10-12
status: complete
plan_head_before: f0193d9e423d7436a4435a0470bff28d21e27900
plan_head_after: 2899c0d8f0cb89f09e4f78482603d49fca9e1f86

coverage:
  - id: D1
    description: "Each #dims info row wraps: label flex 1 1 50%, value margin-left auto with overflow-wrap anywhere and no white-space, pinned in the gate"
    requirement: INFO-03
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_an_info_row_drops_a_long_value_whole_under_its_label_instead_of_into_the_next_cell"
        status: pass
      - kind: unit
        ref: "tests/test_parity.py#test_the_info_row_check_has_teeth"
        status: pass
    human_judgment: false
  - id: D2
    description: "In a real browser, light and dark, 720 and 1920 px, ISO 4017 M8 x 70's long values sit whole under their label inside their own cell; labels wrap as phrases; short values stay beside their labels; the 25-character value breaks only before mm"
    requirement: INFO-03
    verification: []
    human_judgment: true
    rationale: "No browser runs in the gate (L01); line breaks, overlap and contrast are visible only on a rendered page. The tracer human-check is the owner's re-run of UAT test 5 via /gsd-verify-work. A headless-Chrome probe of the committed sheet (8 widths, light theme) is recorded below as evidence, not as a gate."
  - id: D3
    description: "01-UI-SPEC.md describes the wrapping row (fourth note, Page Anatomy bullet, Spacing md, E10 overflow and long-text, Verification status) with spacing exceptions, Applicable count and three earlier notes unchanged"
    verification:
      - kind: other
        ref: "Task 2 structure check against 585d926 (python -I one-liner in the plan's second automated verify)"
        status: pass
    human_judgment: false
---

# Phase 4 Plan 17: Wrapping info row (G-04-5) Summary

**Info rows in `#dims` now wrap: the label claims half the row (`flex: 1 1 50%`) and a full-precision value that does not fit beside it drops whole under it at the right; a style.css source pin with teeth holds it in the gate, and 01-UI-SPEC.md says so.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-10-12T14:49:57Z
- **Completed:** 2026-10-12T14:55Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- `#dims div` gained `flex-wrap: wrap`; `#dims dt` is `flex: 1 1 50%`; `#dims dd` is `margin: 0 0 0 auto` with `overflow-wrap: anywhere` and no `white-space`. One comment above the rule carries the measurement (179.2 px value, 200 to 256 px tracks, 56.6 px overrun, 4-line label bound). `#dims dl` is untouched.
- `tests/test_parity.py`: `STYLE_CSS`, `_css_rules`, `_css_declarations`, `_info_row_problems` (four pinned selectors, `nowrap` and clip detection, comments stripped), the pin test and `test_the_info_row_check_has_teeth` (plan 01-04 rules, the debug V4 variant, an ellipsis clip, a deleted `#dims dt` rule, and a comment that must not fail the pin).
- `01-UI-SPEC.md`: fourth dated note, the `#dims` layout bullet (rule 4: a percentage or `fr` is a proportion outside the spacing scale), Spacing `md` usage, E10 overflow and long-text rows (each naming G-04-5 and citing `04-17-PLAN.md`), Verification status line. Exceptions table, `Applicable:` line and the three earlier notes are byte identical to 585d926.

## RED run (recorded, not committed: the pre-commit hook runs `make verify`)

Command: `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov -k 'info_row'"` on the as-built rules (tests written, style.css untouched).

Result: `2 failed, 28 deselected`:

- `tests/test_parity.py::test_an_info_row_drops_a_long_value_whole_under_its_label_instead_of_into_the_next_cell` failed on `_info_row_problems(STYLE_CSS) == []` (the as-built `#dims div`, `#dims dt`, `#dims dd` and `nowrap` were reported).
- `tests/test_parity.py::test_the_info_row_check_has_teeth` passed its four teeth sheets and failed on its last line, the comment check, which asserts the real sheet is clean.

Semantic assessment: both tests failed on the planned assertion for the intended reason (the as-built one-line row), not on import, collection or syntax. GREEN: after the CSS change the same file gave `30 passed`.

## Task Commits

1. **Task 1 (tracer): wrapping `#dims` row and its source pin** - `e366f5c` (fix)
2. **Task 2: UI contract describes the wrapping row** - `2899c0d` (docs)

**Plan metadata:** the docs commit that adds this SUMMARY (docs: complete plan).

Tracer feedback gate (interactive, `end-of-phase`, the tracer `<verify>` carries a `<human-check>`): the automated verifies were re-run green (parity file 30 passed, the grep check, `make verify` via the pre-commit hook) and the human check is left as end-of-phase UAT material (coverage D2), as the plan states.

## Files Created/Modified

- `src/screw/static/style.css` - the three `#dims` rules and their comment
- `tests/test_parity.py` - the CSS reader, the pin and its teeth
- `.planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md` - the wrapping row in the UI contract

## Optional probe (evidence, not a gate, L01)

Ran: `/tmp/gsd-g045-O3ci/sweep3.mjs` (headless Chrome, light theme) against `screw serve --port 8001` serving the working tree after the CSS change, no injected CSS, ISO 4017 M8 x 70, widths 375, 680, 720, 821, 1280, 1440, 1920, 2560.

| Width (px) | Largest value past its cell (px) | Most label lines |
|-----------|----------------------------------|------------------|
| 375 | 0 | 2 |
| 680 | 0 | 4 |
| 720 | 0 | 3 |
| 821 | 0 | 3 |
| 1280 | 0 | 3 |
| 1440 | 0 | 2 |
| 1920 | 0 | 4 |
| 2560 | 0 | 3 |

The committed sheet reproduces the planner's numbers: 0 px past the cell at every width, at most 4 lines. Nothing the probe writes is in the repo. Dark theme and the 25-character injected value were not run; they stay in the owner's human check.

## Planner measurement (copied from 04-17-PLAN.md; the UI contract cites it)

Source: the debug session's CDP probe (`sweep3.mjs`, headless Chrome) on the real page served by `screw serve --port 8001` from the working tree at HEAD 585d926: ISO 4017 M8 x 70, light theme, deviceScaleFactor 1, 15 viewports from 375 to 2560 px; each candidate injected after the page's stylesheet. "Past the cell" is the value text's right edge minus the cell's right edge. Planner's measurement of 2026-10-12.

| Variant | Past the cell | Labels | Values |
|---------|---------------|--------|--------|
| as built | at 11 of 15 widths, worst 56.6 px (680) and 54.9 px (1920) | up to 7 lines, one word a line | all on the label's line |
| row wraps, `dd` guard, `dt { flex: 1 1 50% }` (this plan) | 0 px at all 15 | at most 4 lines at the 200 to 202 px tracks (680, 1536, 1920), 3 at 213 to 240 px, 2 from 265 px; a label beside a value is at least 121.5 px wide | the four full-precision values drop whole under their label at every width; every short value stays beside its label at every width |
| same with `dt { flex: 1 1 7rem }` (debug V8) | 0 px at all 15 | at most 4 lines | as above, except that the long values stay beside a label of at least 151.8 px in the single 343 and 356 px tracks |
| same with `dt { flex: 1 1 8.5rem }` (the existing input-column exception) | 0 px | at most 3 lines | `12.73 mm`, `14.38 mm`, `11.63 mm` drop under their labels at 720 px, and with them `1.25 mm`, `5.45 mm`, `5.15 mm` at 680, 1536 and 1920 px |
| same with `dt { flex: 1 1 0 }` | 0 px | still 7 lines (46 px wide) beside the long values at 800, 821, 1280, 1366, 1440 px | long values stay beside crushed labels |

The longest-value guard under this plan's variant, with `0.00010825317547305484 mm` written into dd 9 and `1502197910971446.5 mm³` into dd 16: the 25-character value reads `0.00010825317547305484 ` then `mm` at 680, 720 and 1920 px and stays on one line at 375, 1024 and 1440 px; the 22-character one stays on one line everywhere; 0 px past the cell at all six widths.

## Decisions Made

- The label's basis is `50%`, a proportion, not V8's `7rem` (a length off the locked spacing scale, extension rule 4). Both give zero overflow in the planner's table.
- The `.75rem` gap also separates a wrapped value from its label; kept as measured, no new value.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Three ruff E501 line-length errors in the new tests**
- **Found during:** Task 1 (first commit attempt; the pre-commit `make verify` stopped at lint)
- **Issue:** the test function name from the plan is 101 characters on its `def` line, plus two long literal lines
- **Fix:** wrapped the `def` signature (name unchanged, as the plan and the UI contract cite it), split the CSS literal and named the ellipsis rule
- **Files modified:** tests/test_parity.py
- **Verification:** `ruff check` clean, the hook's `make verify` passed
- **Committed in:** e366f5c (the first attempt was rejected by the hook, so no commit of the unfixed file exists)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** None on behaviour; formatting only.

## Issues Encountered

- The step 0c plan-commit ledger was created after Task 1's commit, not before it; its base is the pre-Task-1 HEAD (f0193d9), read straight from the branch, so `commits: 2` is measured, not narrated.

## Known Stubs

None.

## Threat Flags

None. T-04-32 (a value split inside its digits or run into the neighbour's cell) is mitigated as planned: the row wraps, the guard sits on `dd` only, and the pin fails the gate on a revert, on the V4 variant and on any clip.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- G-04-5 closes when the owner re-runs UAT test 5 (`/gsd-verify-work`) against this plan: both themes, 720 and 1920 px, with the injected 25-character value (coverage D2).
- No tech-debt item or idea was filed: the fix leaves no deliberate corner cut.

## Self-Check: PASSED

- FOUND: src/screw/static/style.css, tests/test_parity.py, .planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md
- FOUND commits: e366f5c, 2899c0d (ancestors of HEAD)
- `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"`: 30 passed; `make verify` passed in both commits' pre-commit hook
- Task 2 structure check against 585d926: passed

---
*Phase: 04-iso-hex-bolts-and-screws*
*Completed: 2026-10-12*
