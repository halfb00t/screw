---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 22
subsystem: ui
tags: [matching-part-link, lastTyped, gap-closure, G-05-3, L15-amendment, playwright-probe]
requires:
  - phase: 05-hex-nut-and-kernel-pair-proof
    provides: "plan 05-21 (rowOfFields, the selects following the fields) and the UAT that found G-05-3"
provides:
  - "lastTyped and rememberTyped in app.js: per kind, the value last typed into each field with no default"
  - "the bolt's Matching nut link composed as kind, typed values, then the server's fields"
  - "L15 amendment of 2026-10-21 for the owner's ruling, in the code's commit"
  - "source pin test_the_matching_link_carries_only_a_value_typed_in_this_page_into_a_field_with_no_default and contract test test_a_bolts_matching_nut_link_with_a_typed_clearance_opens_a_nut_that_builds"
  - "01-UI-SPEC.md amended (Copywriting row, rules 34, 35, new 37, E15, E16, Verification status, extension rule 3)"
affects: [phase-5-uat-rerun]
commits: 2
plan_head_before: a6d10cf1ad08a293d4915babc2f3f3db81750576
plan_head_after: 98e7864a6f4fdd8db327cee5bb630035b8d8a411
actuals:
  tokens: 6500
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns:
    - "page memory (module-level Map) for a value the user typed, written only by an input event, read only by one link"
key-files:
  created: []
  modified:
    - src/screw/static/app.js
    - tests/test_parity.py
    - docs/architecture/decision_log.md
    - .planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md
key-decisions:
  - "Generic memory: per kind, each field whose default is undefined; app.js names no field or kind (D-10)"
  - "Typed means an input event; a link, Reset or a kind change never writes it; typing the field empty forgets it"
  - "Page memory only (a module-level Map), no storage, so a reload or a new tab forgets it"
  - "The server's fields are spread last, so no remembered value can override one the server names"
  - "PartInfo.counterpart is unchanged (D-02's published shape)"
requirements-completed: [TYPE-04]
coverage:
  - id: D1
    description: "Type 0.1 on a nut, follow Matching bolt, then Matching nut: the nut opens with clearance 0.1 and builds; the bolt's link reads #kind=nut&clearance=0.1&d=6&pitch=1&left_hand=false&s=10&m=5.2"
    requirement: TYPE-04
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_a_bolts_matching_nut_link_with_a_typed_clearance_opens_a_nut_that_builds"
        status: pass
      - kind: unit
        ref: "tests/test_parity.py#test_the_ui_reads_the_counterpart_by_kind_and_fields_only_and_names_no_kind"
        status: pass
    human_judgment: true
    rationale: "No browser is in the gate (L01). The scratch probe drove a headless shell, not the owner's browser; the owner re-runs UAT test 3."
  - id: D2
    description: "The memory is page-only: never in the bolt's hash, requests or downloads; nothing persisted; nothing typed means an unchanged link"
    requirement: TYPE-04
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_the_matching_link_carries_only_a_value_typed_in_this_page_into_a_field_with_no_default"
        status: pass
    human_judgment: false
  - id: D3
    description: "L15 carries the dated amendment, additive and inside L15, in the code's commit"
    verification:
      - kind: command
        ref: "difflib check of docs/architecture/decision_log.md against a64f9c7 (one insert block inside L15, before L16)"
        status: pass
    human_judgment: false
  - id: D4
    description: "01-UI-SPEC.md describes the matching-part link as built"
    verification: []
    human_judgment: true
    rationale: "Prose contract amendment; reviewed by reading."
duration: 12 min
completed: 2026-10-21
status: complete
---

# Phase 5 Plan 22: The Matching nut link carries the last typed clearance Summary

**The bolt's `Matching nut` link now carries the clearance last typed on a nut in this page (page memory, generic over any field with no default), so the nut it opens builds; with none typed the link and the nut are as before (G-05-3, owner ruling 2026-10-21, L15 amendment).**

## Performance

- **Duration:** 12 min (measured: start 2026-10-21T10:42:34Z, end 2026-10-21T10:54:34Z, the second `make verify` included)
- **Tasks:** 2
- **Files modified:** 4 (none created)

## Accomplishments
- `lastTyped` (a module-level `Map`) and `rememberTyped(input)` in `src/screw/static/app.js`. The only writer is the form's `input` listener; a field with a default returns early; an empty typed value deletes the entry. `showCounterpart` spreads `...lastTyped.get(counterpart.kind)` before `...counterpart.fields`, so the server's fields win. No field or kind is named, no storage or cookie is used, and `partQuery`, `writeHash`, `update`, `setDownloads`, `navigate`, `refuseLink`, `pick` and `renderInfo` do not read it.
- L15 amendment of 2026-10-21 in `docs/architecture/decision_log.md`, additive (one inserted block inside L15, before L16), in the same commit as the code.
- Two new tests and one updated pin in `tests/test_parity.py`.
- 01-UI-SPEC.md amended in place: dated note, Copywriting row, rules 34 and 35, new rule 37, E15 and E16, Verification status, extension rule 3. No row added, so `Applicable:` is unchanged.

## Task Commits

BASE (HEAD before Task 1): `a6d10cf1ad08a293d4915babc2f3f3db81750576`

1. **Task 1 (tracer, starts red): carry the clearance last typed on a nut on the bolt's Matching nut link** - `a2e1f07` (feat; app.js, tests/test_parity.py, decision_log.md)
2. **Task 2: the UI contract says the matching nut link carries the last typed clearance** - `98e7864` (docs; 01-UI-SPEC.md)

**Plan metadata:** the docs(05-22) completion commit that follows this file.

`git diff --stat BASE..HEAD` before the metadata commit touches only the four files in `files_modified`. The first attempt at commit 1 was stopped by the hook's ruff (E501, one over-long test line); it was reflowed and committed once green, so no `--no-verify`.

## RED evidence

### Probe, RED, at HEAD `a6d10cf` (plan 05-21 in place, tree untouched), server `.venv/bin/screw serve --port 8011`, `SCREW_PROBE_APP_JS` unset

Command: `PLAYWRIGHT_BROWSERS_PATH=/Users/half/git/halfb00t/spur/.venv/ms-playwright /Users/half/git/halfb00t/spur/.venv/bin/python probe_g05_3.py http://127.0.0.1:8011/` (script in the session scratch directory, not in the repo). Exit 1. Exactly the two predicted FAIL steps; the other three pass. The plan's prediction was grounded at `a64f9c7`; 05-21 changed nothing in these readings:

```
FAIL bolt: Matching nut carries the typed clearance "#kind=nut&d=6&pitch=1&left_hand=false&s=10&m=5.2"
PASS bolt: its hash and its requests carry no clearance {"hash": "", "bolt": ["bolt/info?", "bolt/model.stl?quality=preview"]}
FAIL nut again: opens with clearance 0.1 and builds {"clearance": "", "nut_stl": []}
PASS cleared: a clearance typed empty is forgotten "#kind=nut&d=6&pitch=1&left_hand=false&s=10&m=5.2"
PASS fresh page: no clearance typed, none carried "#kind=nut&d=6&pitch=1&left_hand=false&s=10&m=5.2"
RESULT FAIL ['bolt: Matching nut carries the typed clearance', 'nut again: opens with clearance 0.1 and builds']
```

### Source tests, RED

`make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov -k 'counterpart or typed_in_this_page or matching_nut_link'"` (tests written, app.js untouched):

```
FAILED tests/test_parity.py::test_the_ui_reads_the_counterpart_by_kind_and_fields_only_and_names_no_kind
FAILED tests/test_parity.py::test_the_matching_link_carries_only_a_value_typed_in_this_page_into_a_field_with_no_default
2 failed, 5 passed, 62 deselected in 2.80s
```

The updated pin failed at its `URLSearchParams` line. The new source test failed at its first assertion, `const lastTyped = new Map();`, because I ordered that assertion before the `rememberTyped` lookup; the plan expected the `rememberTyped` lookup, and both are the same absence (nothing written yet). `test_a_bolts_matching_nut_link_with_a_typed_clearance_opens_a_nut_that_builds` passed before the change, by design (the server half of UAT test 3; 1.15 s).

## GREEN evidence

### Probe, GREEN, same server and command, after the edit (HEAD `a6d10cf` + edit, uncommitted), exit 0

```
PASS bolt: Matching nut carries the typed clearance "#kind=nut&clearance=0.1&d=6&pitch=1&left_hand=false&s=10&m=5.2"
PASS bolt: its hash and its requests carry no clearance {"hash": "", "bolt": ["bolt/info?", "bolt/model.stl?quality=preview"]}
PASS nut again: opens with clearance 0.1 and builds {"clearance": "0.1", "nut_stl": [200]}
PASS cleared: a clearance typed empty is forgotten "#kind=nut&d=6&pitch=1&left_hand=false&s=10&m=5.2"
PASS fresh page: no clearance typed, none carried "#kind=nut&d=6&pitch=1&left_hand=false&s=10&m=5.2"
RESULT PASS []
```

### Source tests, GREEN

`make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"`: `69 passed in 5.32s`. The grep gate (memory, writer, composed line, no `localStorage`, `sessionStorage` or `document.cookie`) and the decision-log difflib check against `a64f9c7` both passed.

### Gate

Command: `make verify` on the final tree (after commit 2), exit 0. Result line: `======================= 3463 passed in 159.66s (0:02:39) =======================`. The pre-commit hook ran the same `make verify` and passed on both commits (the first commit's hook run was blocked once by ruff E501 and passed after the reflow).

## Decisions Made
- Generic memory (per kind, each field with no default) instead of naming the nut's clearance: app.js may not name a field or kind (D-10), and today the set is exactly the owner's ruling.
- "Typed" read literally as an `input` event. A nut opened from a shared link that already carries a clearance does not count as typed, so its bolt's link carries none until the user types one. If the owner wants "the clearance the nut last held", the writer moves from the input listener to `update()`; that is a different rule and was not taken (plan, flagged assumption).
- Page memory, not storage: a reload or a new tab forgets it (CODING_VALUES State).
- `PartInfo.counterpart`, `screw info` and the API are unchanged (D-02's shape).

## Deviations from Plan

None - plan executed exactly as written. Notes, none a deviation:
- The source test's first failing assertion differs from the plan's prediction (see RED evidence); both are the same missing code.
- The over-long test line was reflowed after the hook's ruff check failed the first commit attempt, before anything was committed.
- Step 9 (stop the server) ran after the final probe and before commit 2, since both probe runs had already completed.

**Total deviations:** 0.
**Impact on plan:** none.

## Issues Encountered
- The pre-commit hook's ruff E501 on a test line stopped the first commit attempt; fixed and recommitted. Nothing was committed in between.
- The background `screw serve` reported exit 144 when I stopped it with `pkill`; expected.

## Known Stubs

None.

## Threat Flags

None. No new endpoint, auth path or file access. T-05-63 to T-05-68 are mitigated as planned: the source test pins the reader and writer sets and the absence of storage; the probe asserts the bolt's hash and request URLs hold no clearance and that a cleared or fresh page carries none.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Owner end-of-phase item: re-run 05-UAT.md test 3 in a real browser (the Task 1 human check: type 0.1 and tick Left-hand on a nut, follow Matching bolt then Matching nut; clear the field and switch to bolt; reload). No browser is in the gate. Together with the 05-21 item for test 1.
- Open owner decision from 05-21 still stands: `docs/ideas/2026-10-21-browser-test-of-the-page-in-the-gate.md`.
- No idea or tech-debt item was filed by this plan.

## Self-Check: PASSED

Files found: `src/screw/static/app.js`, `tests/test_parity.py`, `docs/architecture/decision_log.md`, `.planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md`. Commits `a2e1f07` and `98e7864` are ancestors of HEAD. The untracked `.planning/HANDOFF.json` and `.continue-here.md` were never staged.

---
*Phase: 05-hex-nut-and-kernel-pair-proof*
*Completed: 2026-10-21*
