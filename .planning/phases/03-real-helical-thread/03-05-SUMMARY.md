---
phase: 03-real-helical-thread
plan: 05
subsystem: ui
tags: [checkbox, boolean-field, shareable-hash, link-refusal, per-mesh-warnings, ui-spec-amendment, source-assertions]

requires:
  - phase: 03-real-helical-thread
    provides: left_hand as a boolean schema property on every kind, group Thread (plan 03-04); the repeated-key 422 (03-04); the threaded-rod warning, Turns, Thread depth and Minor diameter rows (03-01 to 03-03)
provides:
  - "The page builds a Left-hand thread checkbox from /api/schema alone (prop.type === 'boolean'); read() and write() are the only way a control's value is touched; the hash carries left_hand=true only while checked"
  - "refuseLink(): a key given twice, a key the kind does not define and a value its control cannot hold are refused like an unknown kind, naming the key; nothing builds (parity with the API's 422 and the CLI's exit 2)"
  - "pendingWarnings / meshWarnings: the warnings of the mesh on screen stay visible below every error and change only when a new mesh replaces it"
  - "01-UI-SPEC.md amended in place (D-19): rules 1, 2, 6, 9, 10, 15, 16, 19, 21, 24, 29, Copywriting, UI Considerations, OI-2, OI-3, OI-7"
affects: [03-06, 03-07, phase-04, phase-05, phase-06]

actuals:
  tokens: 15000
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "a control is read and written only through read()/write(), keyed on input.type, because a checkbox's .value is the constant on"
    - "one refuseLink(message) helper serves every link the page cannot honour; the checks run repeat, kind, foreign, unreadable"
    - "warnings are per mesh: a fetched info document waits in pendingWarnings and becomes the mesh's warnings only where showModel replaces the mesh"
    - "a page behaviour with no browser in the gate is pinned as source text in tests/test_parity.py, with the order of two statements asserted where order is the point"

key-files:
  created: []
  modified:
    - src/screw/static/app.js
    - src/screw/static/style.css
    - tests/test_parity.py
    - .planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md
    - docs/tech_debt/INDEX.md
    - docs/tech_debt/resolved/2026-10-06-ui-drops-foreign-hash-keys.md
    - docs/tech_debt/resolved/2026-10-06-ui-hides-warnings-on-failed-update.md

key-decisions:
  - "Unknown fields are reported with a singular and a plural sentence (Unknown field \"m\" / Unknown fields \"m\", \"x\"), and the known-field names come from fields before refuseLink clears it"
  - "An empty hash value (#d=) is not refused: only a non-empty value that its control reads back as '' is unreadable, as the plan specified; an empty checkbox value (#left_hand=) is refused because it is neither true nor false"
  - "The 'Showing the last valid part' status is still cleared by a refused link (setStatus('') in refuseLink, unchanged from the unknown-kind branch); the plan asked for the warnings to stay, not the status"
  - "The startup failure keeps showing no warnings: it is the one showMessages call with an error and no meshWarnings, and the pinned test says so"

patterns-established:
  - "Pinned statements live in PINNED_STATEMENTS with a comment naming the plan that changed them; a behaviour that is an order or a count (repeat check before the kind lookup, three error paths showing meshWarnings) is a dedicated source test"

requirements-completed: [THRD-02]

coverage:
  - id: D1
    description: "The form shows Left-hand thread as an unchecked checkbox in a Thread fieldset after Size, built from /api/schema alone; app.js reads no field name or row key"
    requirement: THRD-02
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_the_ui_round_trips_every_field_through_generic_code"
        status: pass
      - kind: unit
        ref: "tests/test_parity.py#test_the_form_has_a_size_fieldset_then_a_thread_one"
        status: pass
      - kind: unit
        ref: "tests/test_parity.py#test_the_ui_reads_no_field_by_name"
        status: pass
    human_judgment: true
    rationale: "Source assertions prove the statements are present, not that a browser renders a checkbox at its natural width in both themes, fires the input event on toggle, or shows the preview's thread changing hand"
  - id: D2
    description: "left_hand=true is written to the hash and the query only while checked; #left_hand=true opens checked; Reset unchecks; every control goes through read()/write()"
    requirement: THRD-02
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_the_ui_round_trips_every_field_through_generic_code"
        status: pass
    human_judgment: true
    rationale: "The round trip is pinned as source text only; the hash, the reload and Copy link in a real tab are not observable without a browser (L01)"
  - id: D3
    description: "A link with a repeated, foreign or unreadable key is refused like an unknown kind, naming the key, and builds nothing"
    requirement: THRD-02
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_the_ui_refuses_a_link_it_cannot_honour"
        status: pass
    human_judgment: true
    rationale: "#d=abc relies on HTML number-input sanitisation turning abc into an empty string, which only a browser shows (the debt item's ASSUMPTION, never run)"
  - id: D4
    description: "After a failed update or a refused link the warnings of the mesh on screen stay visible below the errors and change only when a new mesh replaces it"
    requirement: THRD-02
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_the_ui_keeps_the_warnings_of_the_mesh_on_screen"
        status: pass
    human_judgment: true
    rationale: "The interleaving of the info and STL fetches (a gate build_error on the STL after its info rendered) is only observable in a running page"
  - id: D5
    description: "01-UI-SPEC.md describes the page as built (rules 1, 2, 6, 9, 10, 15, 16, 19, 21, 24, 29, Copywriting, E2, E3, E5, E9, E10; OI-2, OI-3, OI-7 resolved), each changed rule pinned by a source assertion in the same commit"
    requirement: THRD-02
    verification:
      - kind: command
        ref: "make verify (836 passed, coverage 97.02%)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Both UI debt items are resolved in their fixing commits and moved to docs/tech_debt/resolved/ with their INDEX rows"
    verification:
      - kind: command
        ref: "test -f resolved/... && ! test -e active/... && grep -q 'Status: resolved' && grep -q 'resolved/...' INDEX.md, for both items"
        status: pass
    human_judgment: false

duration: 8min
completed: 2026-10-10
status: complete
commits: 3
plan_head_before: 33deaef684220b310669a39a5139c745bb01d0a7
plan_head_after: 909dec37bc1bb52cf179cc829395fece14e18cf4
---

# Phase 3 Plan 05: The page's left-hand checkbox, link refusals and per-mesh warnings Summary

**The page builds a `Left-hand thread` checkbox from the schema and round-trips `left_hand=true` through the link, refuses a repeated, foreign or unreadable hash key like an unknown kind (naming it, building nothing), and keeps the warnings of the mesh on screen under every error; `01-UI-SPEC.md` is amended to match and both UI debt items are retired.**

## Performance

- **Duration:** 8 min (SUMMARY write follows)
- **Started:** 2026-10-10T14:35:14Z
- **Completed:** 2026-10-10T14:43Z
- **Tasks:** 3
- **Files modified:** 7 (`app.js`, `style.css`, `tests/test_parity.py`, `01-UI-SPEC.md`, `docs/tech_debt/INDEX.md`, the two debt items moved to `resolved/`)

## Accomplishments

- `buildForm` takes a third branch: `prop.type === 'boolean'` makes `input.type = 'checkbox'` with none of the number attributes. `read(input)` and `write(input, v)` sit beside `fmt`; a checkbox reads as `String(input.checked)` and is written as `String(v) === 'true'`. `navigate()`, `partQuery()` and the Reset handler use them, so `left_hand=true` is written only while checked and `false` never is; an omitted key opens unchecked. No field name appears anywhere in `app.js`.
- `.field input[type=checkbox] { width: auto; }` keeps the box at its natural width (specificity 0,2,1 beats the shared `.field input` rule); no new token.
- `refuseLink(message)` is the one clearing for an unknown kind and three new cases, checked in order: a key given twice (before the kind lookup, so `#kind=bolt&kind=x` is refused too), a key other than `kind` that `fields` does not define (singular and plural sentences, known fields listed), and a value the control cannot hold (a checkbox not `true`/`false`, or a non-empty value a number or select reads back as `''`). Read as logic against `URLSearchParams` in node: `d=8&m=5` finds foreign `m`, `d=1&d=2` and `kind=bolt&kind=bolt` find the repeat.
- `pendingWarnings` and `meshWarnings`: `renderInfo` still shows the new document's warnings while its STL is in flight (rule 16) but stores them as pending; `showModel` copies them to `meshWarnings` where it replaces the mesh. `fail`, `refuseLink` and `reportLoadError` show `mesh ? meshWarnings : []` below the error paragraphs; the startup failure is the one `showMessages` call with no warnings.
- `PINNED_STATEMENTS` now holds the helper forms in place of the three `.value` spellings plus four boolean/checkbox statements, with a comment naming plan 03-05. New source tests: `test_the_form_has_a_size_fieldset_then_a_thread_one`, `test_the_ui_refuses_a_link_it_cannot_honour` (statements, the repeat check's position before the kind lookup, the helper's clearing), `test_the_ui_keeps_the_warnings_of_the_mesh_on_screen` (one `meshWarnings = pendingWarnings`, inside `showModel`; at least three `mesh ? meshWarnings : []`; the only bare `showMessages` is the startup failure).
- `01-UI-SPEC.md` amended in place with a dated note under the title: the rules above, the Copywriting table (new group, field, help texts, info rows, the new standing warning, the row-not-computable and fine-STL warnings, the several-fields 422s, `duplicate`, the gate's `build_error`, the three link refusals), UI Considerations (E2 error, E3 error and two populated rows, E5, E9, E10), OI-2, OI-3 and OI-7 marked resolved. Row counts updated to 43 applicable, 30 resolved.

## Task Commits

1. **Task 1: The page builds the left-hand checkbox from the schema and round-trips it through the link** - `9570adb` (feat)
2. **Task 2: A link with a foreign, repeated or unreadable key is refused naming it** - `05fb4ed` (fix)
3. **Task 3: The warnings of the mesh on screen survive a failed update** - `909dec3` (fix)

**Plan metadata:** the SUMMARY commit and the STATE/ROADMAP commit follow (docs).

## Files Created/Modified

- `src/screw/static/app.js` - the boolean branch, `read`/`write`, `refuseLink`, the three link checks, `pendingWarnings`/`meshWarnings`
- `src/screw/static/style.css` - the checkbox keeps its natural width
- `tests/test_parity.py` - amended `PINNED_STATEMENTS` and three new source tests
- `.planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md` - Phase 3 amendments (D-19)
- `docs/tech_debt/resolved/2026-10-06-ui-drops-foreign-hash-keys.md`, `docs/tech_debt/resolved/2026-10-06-ui-hides-warnings-on-failed-update.md` (moved from active/), `docs/tech_debt/INDEX.md` - items resolved, rows moved, in the fixing commits

## Decisions Made

- An empty hash value (`#d=`) is not refused, only a non-empty value that its control reads back as `''`, as the plan specified. `#left_hand=` is refused (neither `true` nor `false`).
- `refuseLink` still sets the status to `''`, unchanged from the unknown-kind branch, so a refused link over an on-screen mesh shows the warnings but not `Showing the last valid part`. The plan asked for the warnings to stay; changing the status wording was not asked. Noted for the verifier to look at, no item filed (see Debt).
- The `Resolved in:` lines of both debt items say "this commit; plan 03-07 names its sha", as plans 03-01 and 03-04 did.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] ruff `E501` in the new parity test (first `make verify` of Task 2)**
- **Found during:** Task 2
- **Fix:** split the long pinned statement and the `source.index(...)` comparison over lines.
- **Files modified:** tests/test_parity.py
- **Committed in:** 05fb4ed

**2. [Rule 1 - Bug] Task 2 commit first landed without its files**
- **Found during:** Task 2
- **Issue:** `git add` was passed the old `active/` path of the moved debt item, which no longer exists, so git aborted the whole add and the commit held only the staged rename.
- **Fix:** staged the files and amended my own, unpushed commit; the final `05fb4ed` holds the whole task (5 files). No other commit was amended.
- **Committed in:** 05fb4ed

---

**Total deviations:** 2 auto-fixed (1 lint, 1 commit mistake caught and corrected before moving on). **Impact on plan:** none on behaviour or contracts.

## Issues Encountered

- The dispatch's `Co-Authored-By` trailer is the harness one (`Claude Sonnet 5.5`), as in plan 03-04.
- Nothing in this plan could be run in a browser (L01); every browser-visible claim below is a human check, not verified.

## TDD Gate Compliance

All three tasks are `tdd="true"`. The pre-commit hook runs `make verify`, so a RED-only commit cannot land; RED was shown by running the new test against the pre-change `app.js`, and test plus implementation are one commit per task.

- **Task 1 RED:** `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"` after amending `PINNED_STATEMENTS`, before any `app.js` edit: `1 failed, 14 passed`; `test_the_ui_round_trips_every_field_through_generic_code` failed with `AssertionError: for (const [name, { input }] of fields) write(input, h.get(name) ?? defaults[name]);` not found in the source. `test_the_form_has_a_size_fieldset_then_a_thread_one` passed before the change (the server side already shipped in plan 03-04), so it is a regression pin, not RED evidence. After: `15 passed`.
- **Task 2 RED:** `test_the_ui_refuses_a_link_it_cannot_honour` failed against the unchanged `navigate()`: `1 failed, 15 passed`. After: `16 passed`.
- **Task 3 RED:** `test_the_ui_keeps_the_warnings_of_the_mesh_on_screen` failed (no `pendingWarnings`): `1 failed, 16 passed`. After: `17 passed`.
- Semantic assessment: each test failed on the planned assertion for the intended reason. `gsd_run check tdd-red-evidence` was not run (no persisted record, as in plans 03-01 to 03-04).

## Verification

- `make verify` (last run, Task 3 state; the hook re-ran it for each commit and passed): ruff clean, mypy clean, import-linter passed, pytest `============================= 836 passed in 31.23s =============================`, coverage `97.02%` against the 94 floor. After Task 1: `834 passed`; Task 2: `835 passed`.
- `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"`: `17 passed in 1.41s`.
- `node --input-type=module --check < src/screw/static/app.js`: syntax OK after each task.
- Acceptance greps: `prop.type === 'boolean'` at app.js:74; `input[type=checkbox]` in style.css; `Left-hand thread` in 01-UI-SPEC.md; `k !== 'kind' && !fields.has(k)` at app.js:156; the three message templates found; `grep -c 'mesh ? meshWarnings : \[\]'` prints 3; `meshWarnings = pendingWarnings` on one line (app.js:410); both debt items `Status: resolved`, active copies gone, INDEX rows under `## Resolved` only.

## Human checks for the end-of-phase verifier

None were run (`workflow.human_verify_mode: end-of-phase`). Harvest all of these:

1. **Task 1** - `make serve`, open http://127.0.0.1:8000/ in light, then dark. Expected: the preview shows a helical thread, not a cylinder; a `Thread` fieldset after `Size` holds an unchecked `Left-hand thread` checkbox at its natural width; checking it rebuilds after the 350 ms debounce, the hash reads `#left_hand=true` and the thread visibly winds the other way; unchecking drops the key; reloading `#left_hand=true` opens it checked; Reset unchecks; Copy link reproduces the state in a new tab. Why human: rendering, the checkbox's input event and the hand of a mesh are not visible to a source assertion.
2. **Task 2** - open one at a time `/#d=8&m=5`, `/#d=1&d=2`, `/#kind=bolt&kind=bolt`, `/#left_hand=banana`, `/#d=abc`, then `/#d=8`. Expected: each of the first five shows its refusal sentence naming the key (and the value for the unreadable ones), an empty form and panel, disabled downloads, builds nothing, and the URL is not rewritten; `/#d=8` then opens the M8-diameter part. Why human: `#d=abc` relies on HTML number-input sanitisation (the debt item's ASSUMPTION), which only a browser shows.
3. **Task 3** - open the default part, then set `pitch` = 6 (a root-radius 422), then `d` = 0.001, `pitch` = 0.0001, `length` = 0.01 (a gate `build_error` on the STL after the info rendered), then stop the server and edit a field (network error). Expected: in each case the last valid mesh stays, the status reads `Showing the last valid part`, the error paragraph shows (for the 422 Diameter and Pitch are marked invalid), and below it the warnings of the mesh on screen starting with `threaded rod: no head, plain-cut thread ends; not a product build`.
4. **Extra, from the Decisions above:** a refused link while a mesh is still on screen shows that mesh's warnings but an empty status; a human should say whether the status should read `Showing the last valid part` there too (the form is cleared, so the mesh is not editable).

## Debt

- Resolved: `docs/tech_debt/resolved/2026-10-06-ui-drops-foreign-hash-keys.md` (must) in `05fb4ed`, `docs/tech_debt/resolved/2026-10-06-ui-hides-warnings-on-failed-update.md` (must) in `909dec3`; INDEX rows moved in the same commits; both `Resolved in:` lines say plan 03-07 names the final sha.
- Filed: none. The status-after-refusal question is human check 4, not a defect; if the verifier calls it one, it becomes a `nice` item.
- Not claimed: `#d=abc` rejection and the fetch interleaving are unverified assumptions carried to the human checks, not facts.

## Threat Flags

None. No new endpoint or file access. T-3-12 is mitigated as planned: every new message goes through `showMessages` (`textContent`), and `test_the_ui_builds_nodes_from_text_only` still passes with `innerHTML`, `outerHTML` and `insertAdjacentHTML` absent. T-3-13 is mitigated: foreign, repeated and unreadable keys are refused before any build. No package installed; the vendored three.js bundle is untouched.

## Next Phase Readiness

Ready for 03-06. All three front ends now offer `left_hand`, refuse a key they cannot honour, and keep honest warnings. Plan 03-07 names the final shas for both debt items.

## Self-Check: PASSED

Modified files exist (`app.js`, `style.css`, `tests/test_parity.py`, `01-UI-SPEC.md`, both resolved debt items); commits `9570adb`, `05fb4ed` and `909dec3` are ancestors of HEAD; both active debt copies are gone; the plan commit ledger measures 3 commits from `33deaef`.

---
*Phase: 03-real-helical-thread*
*Completed: 2026-10-10*
