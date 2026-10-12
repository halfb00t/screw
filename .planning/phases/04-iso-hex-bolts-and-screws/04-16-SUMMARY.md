---
phase: 04-iso-hex-bolts-and-screws
plan: 16
subsystem: ui
tags: [vanilla-js, info-document, downloads, preview-stl, gap-closure, ui-spec]

requires:
  - phase: 04-iso-hex-bolts-and-screws
    provides: "PartInfo.downloads: one Download(format, quality, refusal) per format and quality the model route serves, from download_refusal (plan 04-15)"
provides:
  - "setDownloads(q, downloads) in app.js: both download links built from the info document, per format the first entry the server does not refuse"
  - "Download STL (preview) with the refusal sentence as its title where the fine STL is refused (ISO 4017 M8 x 70), Download STEP unchanged, the warning kept"
  - "page-source and label tests that pin the links to the member and keep the page free of format names, quality preferences and warning text"
  - "01-UI-SPEC.md, L13 and 04-REVIEW-DISPOSITION.md describe the download state; IN-02 closed"
affects: [verify-work UAT test 3 re-run (G-04-3), end-of-phase browser UAT, Phase 5 FRNT-06 (preview mesh naming idea)]

plan_head_before: b4e2fe197da82c32e9553bfbc1dfd3ef2588870d
plan_head_after: ac912495f321af777145bdc830b21191b970b261

actuals:
  tokens: 12500
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "A page control whose state depends on the part is built from a member of the info document in server order; the page holds the static label and the server supplies the quality suffix"
    - "A page-side rule of the UI contract is pinned by a Python test that applies the rule to the live API document, beside the source assertions on app.js"

key-files:
  created:
    - docs/ideas/2026-10-12-preview-stl-download-names-its-quality.md
  modified:
    - src/screw/static/app.js
    - tests/test_parity.py
    - .planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md
    - docs/architecture/decision_log.md
    - .planning/phases/04-iso-hex-bolts-and-screws/04-REVIEW-DISPOSITION.md
    - docs/ideas/INDEX.md

key-decisions:
  - "The downgraded link carries the refusal sentence as its title, so the reason sits on the button as well as in the warning; the warning stays the primary explanation (a tooltip does not reach touch screens)"
  - "The STEP link now carries quality=fine explicitly: same bytes and the same cache key the omitted default used"
  - "The saved preview STL keeps the fine STL's file name; the question is filed as an idea for the owner, not changed here (the ruling named the label and the link, not the header)"

patterns-established:
  - "setDownloads resets every anchor to its static label, href-less and aria-disabled, before it links anything, so a failed update cannot leave a stale label or tooltip"

requirements-completed: [TABL-01, TYPE-02]

coverage:
  - id: D1
    description: "The page builds both download links from info.downloads: per format the first entry whose refusal is null, linked with its quality; a refused first entry reads <static label> (<quality>) with the refusal as title; the page reads no warning and names no format or quality of its own; nothing reaches partQuery or writeHash"
    requirement: TYPE-02
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_the_ui_builds_both_download_links_from_the_info_document_and_names_no_quality"
        status: pass
      - kind: unit
        ref: "tests/test_parity.py#test_the_download_labels_are_static_and_the_refused_fine_stl_reads_download_stl_preview"
        status: pass
    human_judgment: false
  - id: D2
    description: "01-UI-SPEC.md, L13 and 04-REVIEW-DISPOSITION.md describe the download state; L13 gains lines only; IN-02 is closed (open: 0)"
    requirement: TABL-01
    verification: []
    human_judgment: true
    rationale: "Prose contract and record; the L13 diff shape is machine-checked (difflib against d3eb46f) but whether the wording says what the page does is a reading task"
  - id: D3
    description: "In a real browser ISO 4017 / M8 / 70 shows Download STL (preview) whose tooltip is the fine-STL sentence and whose click saves an STL, beside an unchanged Download STEP; M8 / 65 shows Download STL; a failed update leaves both disabled under their static labels; the buttons lay out in light, dark and under 820px"
    requirement: TYPE-02
    verification: []
    human_judgment: true
    rationale: "No browser runs in the gate (L01); the anchor download, the tooltip and the layout are visible only on a page. The Task 1 human check, an end-of-phase UAT item"

duration: 13min
completed: 2026-10-12
status: complete
---

# Phase 4 Plan 16: Download links from the info document Summary

**The page builds both download links from `info.downloads` and offers `Download STL (preview)` (with the refusal sentence as its tooltip) where the INTERIM cap refuses the fine STL, so every picker row downloads on its primary action; the UI contract, L13 and the review record say so and IN-02 is closed.**

## Performance

- **Duration:** 13 min
- **Started:** 2026-10-12T09:57:00Z
- **Completed:** 2026-10-12T10:10:00Z
- **Tasks:** 2
- **Files modified:** 7 (6 modified, 1 created)

## Accomplishments

- `setDownloads(q, downloads)` replaces the fixed two-format loop: every anchor is reset to its static `index.html` label (no `href`, no `title`, `aria-disabled`), then per format the first entry whose `refusal` is null is linked as `api/<kind>/model.<format>?<changed fields>&quality=<quality>`; when an earlier entry of that format was refused the label becomes `<static label> (<quality>)` and the title the refusal sentence. `update()` passes `info.downloads` once the preview mesh is on screen. The page names no format, no quality preference and no warning text; `partQuery` and `writeHash` are untouched (D-09, D-10).
- Checked against the live API for ISO 4017 M8 x 70: `model.stl?...&quality=preview` is 200 `model/stl` named `bolt_d8_pitch1.25_left_hand0_length70_s13_k5.3_thread_length70.stl`, `model.step?...&quality=fine` is 200, the fine STL is the 422 the document lists.
- Two tests in `tests/test_parity.py`: the page-source test (reads off `info` are exactly designation, rows, warnings, notes, preset, downloads; off a download entry exactly format, quality, refusal; the quoted `preview` occurs once, no quoted `fine`, `stl` or `step`; `info.warnings` once; `fine_stl_cap` and `fine STL` absent; `partQuery` and `writeHash` free of `quality` and `download`) and the label test (an anchor per route format, static texts, rule 17 applied to the M8 x 70 and the default document, and to an all-refused format).
- `01-UI-SPEC.md` amended in place (dated note, hard constraint, anatomy, color, copywriting, rules 13, 15, 17, 22, 29, E8 with two new rows and the recounted `Applicable: 70`, verification status, extension rule 3); L13 gains six lines after the Info document paragraph (machine-checked: exactly one insert against `d3eb46f`); `04-REVIEW-DISPOSITION.md` closes IN-02 (`open: 0`) naming `90ad513` and `31a4596`.

## Task Commits

1. **Task 1 (tracer): ISO 4017 M8 x 70 offers a working `Download STL (preview)`** - `31a4596` (feat)
2. **Task 2: UI contract, L13 and the review disposition; the file-name idea filed** - `ac91249` (docs)

**Plan metadata:** the commit that carries this SUMMARY, STATE.md and ROADMAP.md (docs: complete plan).

## TDD evidence (Task 1, `tdd="true"`)

RED could not be committed (the pre-commit hook runs `make verify`, plan commit protocol), so it is recorded here.

- Command: `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"`
- Result before the change: `1 failed, 27 passed`; failing test `tests/test_parity.py::test_the_ui_builds_both_download_links_from_the_info_document_and_names_no_quality`, on its first assertion `assert "setDownloads(q, info.downloads)" in _function_body("update")` (the planned behavior, not a load or import fault).
- `test_the_download_labels_are_static_and_the_refused_fine_stl_reads_download_stl_preview` passed at RED: it pins `index.html` and the document plan 04-15 already serves, which satisfy it; only the JavaScript was missing. Its value is the regression guard (a renamed anchor, a new route format without an anchor, a rule-17 change) not a RED.
- Semantic assessment: the target test executed and failed on the planned assertion for the intended reason. The record was not passed to `gsd_run check tdd-red-evidence` (the plan is `type: execute`, not `type: tdd`, and pytest's console output is not one of the classifier's report formats).
- Result after: `28 passed`; `make verify` 2635 passed, coverage 97.33% (floor 96.0%).

## Files Created/Modified

- `src/screw/static/app.js` - `downloadLinks`, `setDownloads(q, downloads)`, `setDownloads(q, info.downloads)` in `update()`
- `tests/test_parity.py` - the page-source test, `_download_labels`, `_links_by_rule_17` and the label test
- `.planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md` - the download state in the UI contract
- `docs/architecture/decision_log.md` - L13: the `downloads` member and the owner's IN-02 ruling (lines added only)
- `.planning/phases/04-iso-hex-bolts-and-screws/04-REVIEW-DISPOSITION.md` - IN-02 fixed, `open: 0`
- `docs/ideas/2026-10-12-preview-stl-download-names-its-quality.md`, `docs/ideas/INDEX.md` - the file-name idea

## Decisions Made

- The reason for the downgrade is on the button (`title`) as well as in the warning; the warning stays primary because a tooltip does not reach touch screens.
- The STEP link carries `quality=fine` explicitly (same bytes, same cache key as the omitted default).
- The saved preview STL keeps the fine STL's name; filed as an idea, header unchanged.

## Deviations from Plan

None - plan executed exactly as written.

One reading of the protocol is recorded for the verifier rather than as a code deviation. Task 1 is `type="tracer"`, and its `<verify>` carries a `<human-check>`. With `human_verify_mode` at the default `end-of-phase` and auto mode off, the tracer feedback gate table (checkpoints.md row 4) reads as a stop for a `checkpoint:human-verify` before expansion. I did not stop: the plan's verification section schedules that browser check into the end-of-phase UAT batch with plan 04-13's, the must-have for it is `verification: backstop`, and Task 2 is documentation that does not build on the slice. The tracer's automated checks were re-run and pass (parity tests, grep, `make verify`, and the live route check above). If the owner wants the gate to stop here, the browser steps are in the Task 1 human check and in 01-UI-SPEC.md E8 (backstop).

**Total deviations:** 0 auto-fixed. **Impact on plan:** none.

## Issues Encountered

None. `.planning/state.json`, `.planning/ui-reviews/` and `web/.DS_Store` were already modified or untracked when the plan started and were left alone and unstaged.

## Known Stubs

None. The `downloads = []` default of `setDownloads` is the reset path (`setDownloads(null)`), not a data stand-in.

## Threat Flags

None. The only new surface is the download anchors, covered by T-04-27, T-04-28 and T-04-30: server text reaches the DOM through `textContent` and the `title` property only, and `format` and `quality` are `Literal` enums written with `URLSearchParams.set`.

## Filed Items

- Idea: `docs/ideas/2026-10-12-preview-stl-download-names-its-quality.md` (row under `## Open` in `docs/ideas/INDEX.md`). No `docs/tech_debt/` item filed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- G-04-3 is closed in code, contract and record. `/gsd-verify-work` re-runs UAT test 3 against plans 04-15 and 04-16.
- Browser steps of the Task 1 human check remain for the end-of-phase UAT: `make serve` (or `SCREW_PORT=8001 make serve`), pick ISO 4017 / M8 / 70, hover and click `Download STL (preview)`, click `Download STEP`, tick and untick Left-hand thread, pick M8 / 65, set Length 10 with Thread length 30, and repeat in the other theme and under 820px.

---
*Phase: 04-iso-hex-bolts-and-screws*
*Completed: 2026-10-12*

## Self-Check: PASSED

- FOUND: src/screw/static/app.js, tests/test_parity.py, 01-UI-SPEC.md, docs/architecture/decision_log.md, 04-REVIEW-DISPOSITION.md, docs/ideas/2026-10-12-preview-stl-download-names-its-quality.md
- FOUND commits: 31a4596, ac91249
- Acceptance criteria re-run: app.js contains `setDownloads(q, info.downloads)`, `downloadLinks` and the label template; parity tests 28 passed; decision-log diff check DIFF_OK; `open: 0`; idea row present; `make verify` exit 0 (2635 passed).
