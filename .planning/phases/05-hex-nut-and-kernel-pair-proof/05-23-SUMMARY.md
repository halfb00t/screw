---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 23
subsystem: ui
tags: [javascript, page-state, typed-value-memory, kind-switch, gap-closure, wr-07, wr-08, in-06]

requires:
  - phase: 05-hex-nut-and-kernel-pair-proof
    provides: plan 05-22's page memory of the typed clearance (lastTyped, rememberTyped, the L15 amendment of 2026-10-21)
provides:
  - the typed-value memory keyed by formKind, the kind of the controls on screen
  - update() that does nothing while a kind switch is still loading
  - navigate() that rebuilds a form that is not the link's kind
  - rowOfFields that never throws on a catalogue row naming a field the form lacks
  - forgetUntyped on Reset and on a link that writes another value
  - the L15 amendment of plan 05-23 and the UI contract (rules 14, 19, 32, 35, 36, 37) as built
affects: [phase 5 verification, UAT tests 1 and 3 re-run]

plan_head_before: 4f0f06fdfe6f8a2c99d59beb832a4077599bfcfc
plan_head_after: 58bbc9ff5459aec8f5a36823ee502d24ad91273c

actuals:
  tokens: 12900   # chars/4 over git diff 4f0f06f..HEAD (51678 chars)
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "A page memory is keyed by the state of the controls it describes (formKind), never by a variable that lags them (currentKind)"
    - "A guard on the first line of update() makes the update loop wait for a navigation that is still loading"
    - "forgetUntyped only deletes; typing stays the one writer of the memory"

key-files:
  created: []
  modified:
    - src/screw/static/app.js
    - tests/test_parity.py
    - docs/architecture/decision_log.md
    - .planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md

key-decisions:
  - "WR-07: lastTyped is keyed by formKind, set in buildForm directly after clearForm with no await before defaults, cleared in clearForm"
  - "Owner choice (a): update() returns while formKind !== currentKind, so in a kind switch's window only the schema request is sent and the hash stays #kind=nut"
  - "Owner choice 'fix in navigate': navigate rebuilds when kind !== currentKind || kind !== formKind, so Back before the catalogue loads reopens the bolt with its own controls"
  - "WR-08, owner ruling 'forget on Reset and on a link': forgetUntyped(input) deletes an entry the field no longer holds, after navigate's write loop and in the Reset handler"

patterns-established:
  - "The update guard's why comment sits above the function, so the guard stays the first statement of the body (pinned by a startswith assertion)"

requirements-completed: [TYPE-04]

coverage:
  - id: D1
    description: "WR-07: a clearance typed while a kind switch loads is remembered under the form on screen; the nut's Matching bolt link carries no clearance and opens the bolt, which builds"
    requirement: TYPE-04
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_the_typed_memory_is_keyed_by_the_kind_of_the_form_on_screen"
        status: pass
      - kind: e2e
        ref: "scratch probe_05_23.py: window steps (headless Chromium via spur's Playwright, not in the repo)"
        status: pass
    human_judgment: true
    rationale: "No browser runs in the gate (L01); the owner re-runs UAT test 3 and the optional throttled step 5 in a real browser"
  - id: D2
    description: "In the kind-switch window update() sends only the schema request and the hash stays #kind=nut"
    requirement: TYPE-04
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_the_typed_memory_is_keyed_by_the_kind_of_the_form_on_screen"
        status: pass
      - kind: e2e
        ref: "scratch probe_05_23.py: the two WR-07 guard window steps"
        status: pass
    human_judgment: false
  - id: D3
    description: "Back before a kind switch's catalogue loads reopens the bolt with its own seven controls and builds it"
    requirement: TYPE-04
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_a_kind_change_drops_the_old_mesh_and_what_described_it"
        status: pass
      - kind: e2e
        ref: "scratch probe_05_23.py: back step"
        status: pass
    human_judgment: true
    rationale: "No browser runs in the gate (L01); the owner's optional step 6 re-runs it in a real browser"
  - id: D4
    description: "IN-06: rowOfFields treats a catalogue row naming a field the form lacks as not held and never throws"
    requirement: TYPE-04
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_after_a_failed_update_the_selects_show_the_row_the_fields_hold_exactly"
        status: pass
    human_judgment: false
  - id: D5
    description: "WR-08: Reset, and a link that writes another clearance, forget the remembered value; the round trip still carries a value a link wrote back unchanged"
    requirement: TYPE-04
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_reset_and_a_navigation_forget_a_typed_value_the_field_no_longer_holds"
        status: pass
      - kind: e2e
        ref: "scratch probe_05_23.py: reset, link, round trip and cleared steps"
        status: pass
    human_judgment: true
    rationale: "No browser runs in the gate (L01); the owner re-runs UAT tests 1 and 3 and the two review cases in a real browser"
  - id: D6
    description: "The L15 amendment of plan 05-23 and UI-SPEC rules 14, 19, 32, 35, 36 and 37, E16, Verification status and Extension rule 3 describe the built behaviour"
    requirement: TYPE-04
    verification:
      - kind: other
        ref: "difflib check of docs/architecture/decision_log.md against f0c73e8 (one inserted block before L16) and the UI-SPEC grep check"
        status: pass
    human_judgment: false

duration: 16 min
completed: 2026-10-21
status: complete
---

# Phase 5 Plan 23: Typed-clearance memory follows the form on screen Summary

**The typed-clearance memory is keyed by `formKind`, `update()` waits for a kind switch to load, `navigate()` rebuilds a form that is not the link's kind, and Reset or a link that writes another value forgets the remembered clearance (WR-07, WR-08, IN-06).**

## Performance

- **Duration:** 16 min
- **Started:** 2026-10-21T13:52:42Z
- **Completed:** 2026-10-21T14:08:15Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- WR-07 closed. A clearance typed while a kind switch loads stays the nut's. The nut's Matching bolt link reads `#kind=bolt&d=6&pitch=1&left_hand=false&s=10&k=4`, following it builds the bolt with no error, and the bolt's Matching nut link carries the clearance typed after the load.
- The kind-switch window is closed by the owner's choice (a): `update()` returns while `formKind !== currentKind`, so only `schema?kind=nut` is requested and the hash stays `#kind=nut`.
- Back before a kind switch's catalogue loads reopens the bolt with its own seven controls and builds it (owner choice "fix in navigate").
- IN-06: no page error in the window; `rowOfFields` treats a missing control as not held.
- WR-08 closed by the owner's ruling: Reset and a link that writes another value forget the entry through `forgetUntyped`; the round trip of UAT test 3 still carries 0.1.
- The L15 amendment and the UI contract describe the built behaviour in the WR-08 code's commit.

## Task Commits

1. **Task 1: formKind key, update guard, navigate rebuild, rowOfFields guard, IN-05 pins** - `53cd338` (fix)
2. **Task 2: forgetUntyped on Reset and on a link, L15 amendment, UI-SPEC rules** - `58bbc9f` (fix)

**Plan metadata:** the commit that carries this SUMMARY, STATE.md, ROADMAP.md and REQUIREMENTS.md (docs).

## Evidence (RED and GREEN)

BASE is `4f0f06f` (`git diff --quiet f0c73e8 HEAD -- src tests docs` exited 0, so the plan's predictions held). The probe is `probe_05_23.py` from the plan, unchanged, run against `.venv/bin/screw serve --port 8023` with spur's Playwright (`PLAYWRIGHT_BROWSERS_PATH=/Users/half/git/halfb00t/spur/.venv/ms-playwright`). It is in the session scratch directory and not in the repo (L01).

### Probe at BASE (`4f0f06f`): exit 1, exactly the nine predicted FAIL steps

```
FAIL window: only the schema request is sent, no bolt/info?clearance= (WR-07 guard) {"requests": ["schema?kind=nut", "bolt/info?clearance=0.1"], "held": 1}
FAIL window: the hash stays #kind=nut (WR-07 guard) "#clearance=0.1"
FAIL window: no page error while the kind switch loads (IN-06) ["Cannot read properties of undefined (reading 'input')"]
PASS premise: the finished navigation writes the link's empty clearance over the window's typing {"clearance": "", "selects": ["ISO 4032", "M6"]}
FAIL window: the nut's Matching bolt link carries no clearance (WR-07) "#kind=bolt&clearance=0.1&d=6&pitch=1&left_hand=false&s=10&k=4"
FAIL window: Matching bolt opens the bolt and it builds (WR-07) {"bolt_stl": [], "errors": ["Unknown field \"clearance\" for kind \"bolt\". Known fields: d, pitch, left_hand, length, s, k, thread_length."], "hash": "#kind=bolt&clearance=0.1&d=6&pitch=1&left_hand=false&s=10&k=4"}
FAIL window: the bolt's Matching nut carries the clearance typed after load (0.2) ""
FAIL back: Back before the nut's catalogue loads rebuilds the bolt's form and builds the bolt {"names": ["d", "pitch", "left_hand", "s", "m", "clearance"], "kind": "bolt", "bolt_stl": [200], "pageerrors": []}
FAIL reset: the bolt's Matching nut carries no clearance after Reset emptied it (WR-08) "#kind=nut&clearance=0.1&d=6&pitch=1&left_hand=false&s=10&m=5.2"
PASS premise: the link wrote 0.3 into the field "0.3"
FAIL link: the bolt's Matching nut carries no clearance after a link wrote another (WR-08) "#kind=nut&clearance=0.1&d=6&pitch=1&left_hand=false&s=10&m=5.2"
PASS round trip: the bolt's Matching nut carries 0.1 "#kind=nut&clearance=0.1&d=6&pitch=1&left_hand=false&s=10&m=5.2"
PASS round trip: the nut opens with 0.1 and builds {"clearance": "0.1", "nut_stl": [200]}
PASS round trip: a link that wrote the same 0.1 keeps it "#kind=nut&clearance=0.1&d=6&pitch=1&left_hand=false&s=10&m=5.2"
PASS cleared: a clearance typed empty is forgotten "#kind=nut&d=6&pitch=1&left_hand=false&s=10&m=5.2"
PASS pick: ISO 4032 then M6 holds with an empty clearance and nothing builds {"selects": ["ISO 4032", "M6"], "nut_stl": [], "pageerrors": []}
PASS fresh page: no clearance typed, none carried "#kind=nut&d=6&pitch=1&left_hand=false&s=10&m=5.2"
RESULT FAIL [the nine FAIL steps above]
```

### RED source tests, Task 1 (`make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"`): 4 failed, 66 passed

- `test_after_a_failed_update_the_selects_show_the_row_the_fields_hold_exactly`: `assert 'const control = fields.get(name);' in ...` (the old lookup `read(fields.get(name).input)`).
- `test_the_matching_link_carries_only_a_value_typed_in_this_page_into_a_field_with_no_default`: `assert 'formKind === null' in ...` (the old `lastTyped.get(currentKind)` body).
- `test_the_typed_memory_is_keyed_by_the_kind_of_the_form_on_screen`: `assert 'let formKind = null;' in APP_JS`.
- `test_a_kind_change_drops_the_old_mesh_and_what_described_it`: `ValueError: substring not found` on `if (kind !== currentKind || kind !== formKind) {`.

### Probe after Task 1 (`53cd338`): exit 1, exactly the two WR-08 FAIL steps

Both window checks pass (`{"requests": ["schema?kind=nut"], "held": 1}` and `"#kind=nut"`), as does IN-06 (`[]`). `back:` passes: `{"names": ["d", "pitch", "length", "left_hand", "thread_length", "s", "k"], "kind": "bolt", "bolt_stl": [200], "pageerrors": []}`. The window's Matching bolt link is `#kind=bolt&d=6&pitch=1&left_hand=false&s=10&k=4`, Matching bolt builds with `"errors": []`, and the bolt's Matching nut link is `#kind=nut&clearance=0.2&d=6&pitch=1&left_hand=false&s=10&m=5.2`.

```
FAIL reset: the bolt's Matching nut carries no clearance after Reset emptied it (WR-08) "#kind=nut&clearance=0.1&d=6&pitch=1&left_hand=false&s=10&m=5.2"
FAIL link: the bolt's Matching nut carries no clearance after a link wrote another (WR-08) "#kind=nut&clearance=0.1&d=6&pitch=1&left_hand=false&s=10&m=5.2"
RESULT FAIL ["reset: ... (WR-08)", "link: ... (WR-08)"]
```

GREEN for Task 1: 70 passed.

### RED source test, Task 2: 1 failed, 70 passed

`test_reset_and_a_navigation_forget_a_typed_value_the_field_no_longer_holds` failed at the `forgetUntyped` lookup (`AssertionError: forgetUntyped`, `assert None is not None`). GREEN: 71 passed.

### Probe after Task 2 (`58bbc9f` tree, run before the commit): exit 0

All 18 steps PASS, ending `RESULT PASS []`. The two WR-08 steps now read `#kind=nut&d=6&pitch=1&left_hand=false&s=10&m=5.2` (no clearance); the round trip steps still carry `clearance=0.1`.

### Final gate

Command: `make verify`. Result line: `3465 passed in 200.16s (0:03:20)`, exit 0, on the final tree (the pre-commit hook ran the same command and passed on both task commits).

The decision-log difflib check passed (one inserted block after the G-05-3 amendment, before `## L16`, no existing line changed). The UI-SPEC grep check passed. `git diff --stat 4f0f06f..HEAD` touches only the four files_modified paths. `git diff --quiet f0c73e8 HEAD -- src/screw/calc src/screw/app.py src/screw/cli.py src/screw/static/index.html` exits 0.

## Files Created/Modified

- `src/screw/static/app.js` - `formKind` (set in `buildForm`, cleared in `clearForm`), the `update()` guard, navigate's rebuild condition, the `rowOfFields` guard, `rememberTyped` re-keyed, `forgetUntyped` and its two call sites, corrected comments
- `tests/test_parity.py` - the WR-07 and WR-08 source tests, the updated IN-05 and IN-06 pins and the navigate rebuild pin
- `docs/architecture/decision_log.md` - the L15 amendment of plan 05-23 (one new paragraph)
- `.planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md` - the dated note, rules 14, 19, 32, 35, 36 and 37, E16, Verification status, Extension rule 3

## Decisions Made

None beyond the owner's choices already folded into the plan: formKind key, update guard (choice (a)), navigate rebuild ("fix in navigate"), forget on Reset and on a link. Followed the plan as specified.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The update guard's why comment moved above the function**
- **Found during:** Task 1 (GREEN)
- **Issue:** The plan asks for the why comment "above" the guard line, inside `update()`, and also for `_function_body("update").strip().startswith("if (currentKind === null || formKind !== currentKind) return;")`. With the comment inside the body the pin failed (1 failed, 69 passed).
- **Fix:** The comment sits directly above `async function update()`, so the guard is still update's first statement. Text and content are as planned, plus one closing sentence saying the guard is first.
- **Files modified:** src/screw/static/app.js
- **Verification:** 70 passed; the plan's grep `^  if (currentKind === null || formKind !== currentKind) return;$` matches.
- **Committed in:** `53cd338`

**2. [Rule 3 - Blocking] Two test lines wrapped for ruff E501**
- **Found during:** Task 1 commit (the hook's `make verify` failed at lint), and Task 2 (caught by `ruff check` before the commit)
- **Issue:** Three lines in the new test text were 101 to 105 columns against the 100 limit. The first commit attempt was rejected by the hook with nothing committed.
- **Fix:** Wrapped them; no assertion changed.
- **Files modified:** tests/test_parity.py
- **Verification:** `ruff check tests/test_parity.py` clean; 70, then 71 passed.
- **Committed in:** `53cd338`, `58bbc9f`

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both are layout only; no assertion, behaviour or contract text changed. No scope creep.

## Issues Encountered

None beyond the two layout fixes above. Every probe stage matched the planner's prediction exactly (nine, two, zero FAIL steps).

## Known Stubs

None.

## Threat Flags

None. The change adds no endpoint, auth path, file access or schema; it narrows page state (T-05-69 to T-05-75 mitigated as planned).

## Tech debt

No item filed. The planner's WR-07 tech-debt item was dropped by the owner's choice (a). The pick-from-the-old-picker-during-the-window case (plan "Flagged assumptions") is unchanged, fails closed, and is recorded in the plan.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The owner's end-of-phase item: re-run UAT tests 1 and 3 and the cases in Task 2's `<human-check>` (steps 1 to 6) in a real browser.
- Re-verification of 05-VERIFICATION.md gaps WR-07 and WR-08 can run against this tree.

## Self-Check: PASSED

- FOUND: src/screw/static/app.js, tests/test_parity.py, docs/architecture/decision_log.md, 01-UI-SPEC.md
- FOUND commits: 53cd338, 58bbc9f (ancestors of HEAD)
- `make verify`: 3465 passed, exit 0

---
*Phase: 05-hex-nut-and-kernel-pair-proof*
*Completed: 2026-10-21*
