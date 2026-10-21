---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 24
subsystem: ui
tags: [javascript, page-state, kind-switch, preset-picker, gap-closure, wr-09]

requires:
  - phase: 05-hex-nut-and-kernel-pair-proof
    provides: plan 05-23's update guard (formKind !== currentKind), navigate's rebuild condition (kind !== formKind) and the rowOfFields IN-06 guard
provides:
  - navigate's rebuild block clears the old kind's form and picker directly after dropMesh, before the new schema is fetched
  - the WR-09 source pin test_a_kind_change_clears_the_old_form_and_picker_before_it_fetches_the_new_ones
  - UI-SPEC rules 30, 32 and 36, a dated note, a Verification status bullet and Extension rule 3 describing the built behaviour
  - WR-09 recorded fixed in 05-REVIEW-DISPOSITION.md
affects: [phase 5 verification (05-VERIFICATION gap WR-09), UAT tests 1 and 3 re-run]

plan_head_before: cc8c923599722d61b397ef0daaade8e0612e16d5
plan_head_after: 5cbc40f3e9345a4a5aa62369021ac8e7188bf668

actuals:
  tokens: 7300   # chars/4 over git diff cc8c923..5cbc40f (29195 chars)
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "A kind switch looks like a first load: nothing of the old kind (control, select, catalogue, badge, mesh) is on screen until the new kind's pieces are built"
    - "formKind is null for the whole switch, so update() returns and an overtaking navigation rebuilds the kind it names whole"

key-files:
  created: []
  modified:
    - src/screw/static/app.js
    - tests/test_parity.py
    - .planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md
    - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-REVIEW-DISPOSITION.md

key-decisions:
  - "Candidate C: clearForm(); clearPicker(); directly after dropMesh(), before buildForm. The review's picker-only patch (A) left the bolt with no picker or badge after Back during the schema fetch; a clear after buildForm (B) left the schema half of the window open (a pick rebuilt the bolt after dropMesh and the nut opened over it as the last valid part). Both measured by the planner and re-confirmed by this run's probe at BASE"
  - "No guard or try/catch in pick: the stale picker is taken away, not muted. The rowOfFields IN-06 guard stays as a second line, only its comment changed"
  - "L15 not edited: its invariant (no wrong hash, request or download link) held before and holds after"

requirements-completed: [TYPE-04]

coverage:
  - id: D1
    description: "WR-09: from the start of a kind switch until the new picker is built, no picker select, catalogue row or badge of the old kind is on screen, so a pick throws nothing and writes nothing into the new controls"
    requirement: TYPE-04
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_a_kind_change_clears_the_old_form_and_picker_before_it_fetches_the_new_ones"
        status: pass
      - kind: e2e
        ref: "scratch probe_05_24.py window steps (headless Chromium via spur's Playwright, not in the repo)"
        status: pass
    human_judgment: true
    rationale: "No browser runs in the gate (L01); the owner re-runs the throttled kind switch and UAT tests 1 and 3 in a real browser"
  - id: D2
    description: "Schema half of the window: no control of the old kind is on screen while the new schema loads, nothing of it is requested or built, and the nut opens with no last valid part (rule 36, R10)"
    requirement: TYPE-04
    verification:
      - kind: e2e
        ref: "scratch probe_05_24.py schema-window steps"
        status: pass
    human_judgment: true
    rationale: "Observed only in a headless browser; the owner confirms in a real throttled browser"
  - id: D3
    description: "Back while the nut's schema loads reopens the bolt whole (seven controls, picker ISO 4017 / M6 / 20, badge, one bolt/model.stl 200)"
    requirement: TYPE-04
    verification:
      - kind: e2e
        ref: "scratch probe_05_24.py back-schema step"
        status: pass
    human_judgment: true
    rationale: "Observed only in a headless browser"
  - id: D4
    description: "05-23 behaviour unchanged: probe_05_23.py passes 17/17 before and after"
    requirement: TYPE-04
    verification:
      - kind: e2e
        ref: "scratch probe_05_23.py"
        status: pass
    human_judgment: false
  - id: D5
    description: "UI-SPEC rules 30, 32, 36, dated note, Verification status and Extension rule 3 describe the built behaviour; WR-09 recorded fixed"
    requirement: TYPE-04
    verification:
      - kind: other
        ref: "UI-SPEC grep check and the disposition ancestor check from the plan (UISPEC_OK, DISPO_OK)"
        status: pass
    human_judgment: false

duration: ~45min
completed: 2026-10-21
status: complete
---

# Phase 5 Plan 24: Kind switch clears the old form and picker Summary

**A kind switch now takes the old kind's form and preset picker off screen with the mesh, before the new schema is fetched, so a Size pick in the stale picker can no longer throw or write one kind's catalogue row into another kind's controls (WR-09) and no old control can rebuild the old part under the new kind.**

## Performance

- **Duration:** about 45 min (start time not recorded at the top of the run; estimated)
- **Completed:** 2026-10-21T17:42Z (code at 63835c8, disposition at 5cbc40f)
- **Tasks:** 2
- **Files modified:** 4 (`git diff --name-only cc8c923 HEAD`)

## Accomplishments

- Two statements in navigate's rebuild block, `clearForm(); clearPicker();` directly after `dropMesh();` and before `if (!(await buildForm(kind))) return;`, plus the why comment citing review WR-09 and plan 05-24. The `rowOfFields` comment is rewritten (statements untouched).
- The WR-09 pin: `test_a_kind_change_clears_the_old_form_and_picker_before_it_fetches_the_new_ones`.
- UI-SPEC rules 30, 32 and 36, a dated note (eleventh), a Verification status bullet and the Extension rule 3 clause.
- WR-09 flipped to `fixed` with `63835c8` in 05-REVIEW-DISPOSITION.md.

## Task Commits

1. **Task 1 (tracer, TDD): clear the old kind's form and picker before a kind switch fetches the new ones** - `63835c8` (fix). RED (failing pin and probe) is recorded below and not committed: every commit is green (plan commit protocol).
2. **Task 2: record WR-09 as fixed and run the final gate** - `5cbc40f` (docs)

**Plan metadata:** the SUMMARY commit that follows this file, then the STATE/ROADMAP commit.

## RED evidence (BASE = `cc8c923`, tree identical to `3eb2920` under src, tests, docs)

Server: `.venv/bin/screw serve --port 8024`. Probe md5s matched the plan: `probe_05_24.py` afb4467e5a32bf7989d649cc736463d9, `probe_05_23.py` 4e913d256925e9df77838564c0cb5fcc, `same_check_05_24.py` 6aceb6f126d5686eaa8f2d409616563a.

`probe_05_24.py` at BASE: exit 1, exactly the five predicted FAIL steps.

```
PASS premise: the bolt page shows its own picker and badge {"selects": ["ISO 4017", "M6", "20"], "picker": {"hidden": false, "selects": 3, "badge": "matches ISO 4017 M6 × 20"}}
FAIL window: no picker, catalogue row or badge of the old kind is on screen while the new form is (WR-09) {"hidden": false, "selects": 3, "badge": "matches ISO 4017 M6 × 20"}
FAIL window: a pick in the window throws nothing (WR-09) ["Cannot read properties of undefined (reading 'input')"]
FAIL window: the nut's controls hold nothing the old catalogue wrote (WR-09) {"d": "2.5", "pitch": "0.45", "left_hand": "on", "s": "", "m": "", "clearance": ""}
PASS window: only the schema request is sent and the hash stays #kind=nut (05-23 guard) {"requests": ["schema?kind=nut"], "held": 1, "hash": "#kind=nut"}
PASS after load: the nut's own picker holds ISO 4032 / M6 over the nut's defaults, nothing builds {...selects ["ISO 4032","M6"], picker {"hidden": false, "selects": 2, "badge": ""}, values {"d": "6", "pitch": "1", "left_hand": "on", "s": "10", "m": "5.2", "clearance": ""}, errors ["Clearance (radial): Field required"], nut_stl [], hash "#kind=nut"}
FAIL schema-window: no control or picker of the old kind is on screen while the new kind's schema loads {"inputs": 7, "hidden": false, "selects": 3, "badge": "matches ISO 4017 M6 × 20"}
FAIL schema-window: nothing of the old kind is requested or built, and the nut opens with no last valid part {"requests": ["bolt/info?d=8&pitch=1.25&s=13&k=5.3", "bolt/model.stl?d=8&pitch=1.25&s=13&k=5.3&quality=preview"], "hash": "#d=8&pitch=1.25&s=13&k=5.3", "status": "Showing the last valid part", "errors": ["Clearance (radial): Field required"], "all": ["bolt/info", "bolt/model.stl", "schema", "presets", "nut/info"], "pageerrors": []}
PASS back-schema: ... {"names": [7 bolt fields], "kind": "bolt", "selects": ["ISO 4017","M6","20"], "picker": {"hidden": false, "selects": 3, "badge": "matches ISO 4017 M6 × 20"}, "bolt_stl": [200], "held": 1, "pageerrors": []}
PASS switch: the nut at 0.1 shows its own picker and badge
PASS switch: back on the bolt, its own picker and badge, no page error
RESULT FAIL [the 3 (WR-09) window steps, the 2 schema-window steps]
```

`probe_05_23.py` at BASE: exit 0, 17 PASS lines, `RESULT PASS []`.

RED test, before the fix, with the pin added:

```
make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"
FAILED tests/test_parity.py::test_a_kind_change_clears_the_old_form_and_picker_before_it_fetches_the_new_ones
1 failed, 71 passed in 5.35s
```

It failed at the first assertion (`dropMesh(); clearForm(); clearPicker(); if (!(await buildForm(kind))) return; try {` not in navigate's squashed body). Semantic assessment: the target test ran and failed on the planned assertion, for the intended reason (the clears are absent). No `tdd-red-evidence` classifier run: the plan has `type: execute`, not `type: tdd`, and no `workflow.tdd_mode` gate applies.

## GREEN evidence (HEAD `63835c8` code, working tree = committed)

- `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"`: `72 passed in 5.17s`.
- `same_check_05_24.py src/screw/static/app.js`: `unchanged except navigate's two calls and comments`.
- `probe_05_24.py`: exit 0, `RESULT PASS []`, 11 PASS lines. The decisive ones:

```
PASS window: no picker, catalogue row or badge of the old kind is on screen while the new form is (WR-09) {"hidden": true, "selects": 0, "badge": ""}
PASS window: a pick in the window throws nothing (WR-09) []
PASS window: the nut's controls hold nothing the old catalogue wrote (WR-09) {"d": "", "pitch": "", "left_hand": "on", "s": "", "m": "", "clearance": ""}
PASS window: only the schema request is sent and the hash stays #kind=nut (05-23 guard) {"requests": ["schema?kind=nut"], "held": 1, "hash": "#kind=nut"}
PASS schema-window: no control or picker of the old kind is on screen while the new kind's schema loads {"inputs": 0, "hidden": true, "selects": 0, "badge": ""}
PASS schema-window: nothing of the old kind is requested or built, and the nut opens with no last valid part {"requests": [], "hash": "#kind=nut", "status": "", "errors": ["Clearance (radial): Field required"], "all": ["schema", "presets", "nut/info"], "pageerrors": []}
PASS back-schema: ... "kind": "bolt", "selects": ["ISO 4017", "M6", "20"], "picker": {"hidden": false, "selects": 3, "badge": "matches ISO 4017 M6 × 20"}, "bolt_stl": [200], "held": 1, "pageerrors": []
PASS switch: the nut at 0.1 shows its own picker and badge {... "badge": "matches ISO 4032 M6"}
PASS switch: back on the bolt, its own picker and badge, no page error
RESULT PASS []
```

- `probe_05_23.py` after the fix: exit 0, 17 PASS lines, `RESULT PASS []`. So the two clears break no truth of 05-21, 05-22 or 05-23.
- UI-SPEC grep check: `UISPEC_OK`. Disposition ancestor check: `DISPO_OK`.
- Final tree, `make verify`: exit 0, `3466 passed in 170.27s (0:02:50)` (3465 at 3eb2920 plus the new test). The pre-commit hook ran `make verify` and passed on both commits.
- `git diff --name-only cc8c923 HEAD`: exactly the four files_modified paths. `git diff --quiet 3eb2920 HEAD -- src/screw/calc src/screw/app.py src/screw/cli.py src/screw/static/index.html src/screw/static/style.css docs/architecture/decision_log.md`: exit 0.

## Files Created/Modified

- `src/screw/static/app.js` - navigate: `clearForm(); clearPicker();` after `dropMesh();` and a why comment; `rowOfFields` comment rewritten.
- `tests/test_parity.py` - the WR-09 source pin, directly after `test_a_kind_change_drops_the_old_mesh_and_what_described_it`.
- `.planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md` - rules 30, 32, 36, the plan 05-24 dated note, Verification status bullet, Extension rule 3.
- `.planning/phases/05-hex-nut-and-kernel-pair-proof/05-REVIEW-DISPOSITION.md` - WR-09 `fixed` with `63835c8`.

## Decisions Made

Followed the plan's candidate C (see key-decisions). This widens the review's patch by one statement (`clearForm()`), flagged by the plan for the owner: candidate B is a two-line revert plus the pin string and the two `schema-window:` probe steps.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. The pre-commit hook stashes and restores the orchestrator's unstaged STATE.md and state.json around each hook run; both came back intact. Port 8024 was free. Task 1's tracer gate: auto mode is off and HUMAN_VERIFY_MODE is end-of-phase with an automated-only `<verify>`, so the verify was re-run end to end (pin test 72 passed, both probes passed) and the run expanded to Task 2 without a checkpoint. The plan's human-check (throttled kind switch in a real browser) is the owner's end-of-phase item.

## Known Stubs

None.

## Tech debt

No tech-debt item or idea filed. The schema-window case was fixed in Task 1, not deferred. The old kind's info panel and `Matching <kind>` link staying on screen until the new kind's first info answer arrives is pre-existing, unchanged behaviour the plan flags for the owner (not filed: the plan makes it a separate owner decision).

## Threat Flags

None - page state only; no new endpoint, auth path, file access or schema change.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

WR-09, the one gap of the re-verification after 05-23, is closed in code and contract. Ready for re-verification of phase 5 and the owner's browser steps (throttled Kind switch to nut, Matching nut then Back, UAT tests 1 and 3).

## Self-Check: PASSED

Verified: `src/screw/static/app.js`, `tests/test_parity.py`, 01-UI-SPEC.md and 05-REVIEW-DISPOSITION.md exist and are modified in `cc8c923..HEAD`; commits `63835c8` and `5cbc40f` are ancestors of HEAD; commit 1 lists exactly app.js, test_parity.py and 01-UI-SPEC.md, commit 2 only the disposition file.

---
*Phase: 05-hex-nut-and-kernel-pair-proof*
*Completed: 2026-10-21*
