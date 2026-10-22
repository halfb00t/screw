---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 25
subsystem: ui
tags: [javascript, page-state, kind-switch, error-path, gap-closure, wr-10, in-08]

requires:
  - phase: 05-hex-nut-and-kernel-pair-proof
    provides: plan 05-24's clearForm/clearPicker before the schema fetch, plan 05-23's formKind guard and refuseLink as the page's one refusal exit
provides:
  - navigate clears the info panel, matching-part link, downloads and status with the form and picker, before the first await
  - one try around buildForm and loadPresets whose catch returns when a newer navigation overtook this one, else refuses whole through refuseLink (selector deselected, any pick retries)
  - the WR-09 pin re-bodied (seven clears before the first await), the WR-10 pin, and a _rebuild_block helper that drops comment lines and counts nothing file-wide (IN-08)
  - UI-SPEC Copywriting rows, rules 14, 30, 34 and 36, E2, E3, E10, E11, E15 and E17, a dated note, a Verification status bullet and Extension rule 3
  - WR-10 and IN-08 recorded fixed in 05-REVIEW-DISPOSITION.md
affects: [phase 5 re-verification (05-VERIFICATION warning WR-10), the owner's browser steps and UAT tests 1 and 3]

plan_head_before: c9c1bc7cb4011d9c1cba4d36431e8118b94d3554
plan_head_after: d85a02422f3761e6bb046e273783a47d05a7a26a

actuals:
  tokens: 15750   # chars/4 over git diff c9c1bc7..d85a024 (63001 chars)
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "navigate keeps the formSeq it set as mine, so its catch can tell a newer navigation took over (the name buildForm, loadPresets and update already use)"
    - "A failed schema or catalogue fetch is refused whole through refuseLink, never a half page; the deselected selector is the retry"

key-files:
  created: []
  modified:
    - src/screw/static/app.js
    - tests/test_parity.py
    - .planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md
    - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-REVIEW-DISPOSITION.md

key-decisions:
  - "Candidate D: the three panel clears, both fetches in one try, the overtaken guard and setStatus('') (the plan's measured table: the review's patch A leaves 5 probe steps failing, B 3, C 1, D none)"
  - "A failed first schema fetch at startup is refused like any kind switch (Could not load the part: ..., selector deselected); the startup string now covers a failed /api/kinds only"
  - "IN-08 recorded fixed on the mutant evidence; the behaviour half stays with docs/ideas/2026-10-21-browser-test-of-the-page-in-the-gate.md (a one-row revert if the owner wants it open)"
  - "L15 not edited and no retry button, timer or new message string added"

requirements-completed: [TYPE-04]

coverage:
  - id: D1
    description: "WR-10: with api/schema?kind=nut answering 500 on a Kind switch, nothing of the bolt stays on screen, one error shows, the Kind select is deselected and the hash is kept; picking nut again loads the nut"
    requirement: TYPE-04
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_a_kind_change_whose_fetch_fails_is_refused_whole_unless_overtaken"
        status: pass
      - kind: e2e
        ref: "scratch probe_05_25.py steps fail, retry, fail-link, startup (headless Chromium via spur's Playwright, not in the repo)"
        status: pass
    human_judgment: true
    rationale: "No browser runs in the gate (L01); a real browser's network error text and the real select's change behaviour are the owner's to see"
  - id: D2
    description: "Owner decision: from the start of a kind switch until the new kind's first info document, the old part's panel, Matching link and downloads are off screen, in the schema and the catalogue window; the new kind writes them again"
    requirement: TYPE-04
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_a_kind_change_clears_the_old_form_and_picker_before_it_fetches_the_new_ones"
        status: pass
      - kind: e2e
        ref: "scratch probe_05_25.py steps window-schema, window-catalogue, switch"
        status: pass
    human_judgment: true
    rationale: "Observed in a headless browser only; the owner confirms the throttled switch in a real one"
  - id: D3
    description: "The failure of an overtaken switch refuses nothing: the bolt the user went back to stays whole when the nut's schema or catalogue fails late"
    requirement: TYPE-04
    verification:
      - kind: e2e
        ref: "scratch probe_05_25.py steps overtaken-schema, overtaken-catalogue"
        status: pass
      - kind: unit
        ref: "tests/test_parity.py#test_a_kind_change_whose_fetch_fails_is_refused_whole_unless_overtaken (guard before refusal)"
        status: pass
    human_judgment: false
  - id: D4
    description: "A failed bolt's 'Showing the last valid part' status does not stay over the empty canvas of a switch (E17)"
    requirement: TYPE-04
    verification:
      - kind: e2e
        ref: "scratch probe_05_25.py step status"
        status: pass
    human_judgment: false
  - id: D5
    description: "05-23 and 05-24 behaviour unchanged: probe_05_23.py 17 of 17 and probe_05_24.py 11 of 11 pass before and after"
    requirement: TYPE-04
    verification:
      - kind: e2e
        ref: "scratch probe_05_23.py and probe_05_24.py"
        status: pass
    human_judgment: false
  - id: D6
    description: "IN-08: the pins pass benign changes (another clearForm caller, a split await, a comment between the clears) and fail the defects; the old pin failed all three benign mutants"
    requirement: TYPE-04
    verification:
      - kind: other
        ref: "scratch mutants_05_25.py: MUTANTS PASS [] (eleven ok lines)"
        status: pass
    human_judgment: false
  - id: D7
    description: "UI-SPEC rows, rules and notes describe the built behaviour; WR-10 and IN-08 recorded fixed against b857016"
    requirement: TYPE-04
    verification:
      - kind: other
        ref: "UI-SPEC md5 and grep check (UISPEC_GREP_OK) and the disposition ancestor check (DISP_OK) from the plan"
        status: pass
    human_judgment: false

duration: ~30min
completed: 2026-10-22
status: complete
---

# Phase 5 Plan 25: A kind switch leaves nothing of the old part, and a failed one is refused whole Summary

**A kind switch now takes the old part's info panel, `Matching <kind>` link, downloads and status off screen with its form and picker before the new schema is fetched, and a failed schema or catalogue fetch is refused whole through `refuseLink` (one error, Kind select deselected, so any pick retries) unless a newer navigation overtook it (WR-10, IN-08).**

## Performance

- **Duration:** about 30 min (start time not captured at run start; estimated from commit times)
- **Completed:** 2026-10-22T05:49Z (code at b857016, disposition at d85a024)
- **Tasks:** 2
- **Files modified:** 4 (`git diff --name-only c9c1bc7 HEAD`)

## Accomplishments

- app.js (patch md5 `b77c651eb38e5b669eff786c609fed70`): `const mine = ++formSeq;`, four clears after `clearPicker();`, `buildForm` moved into the existing `try`, `if (mine !== formSeq) return;` before the unchanged `refuseLink` line, two why comments.
- tests/test_parity.py (md5 `71ee546af9b093c113163a0ee21a1313`): `_rebuild_block()`, the re-bodied `test_a_kind_change_clears_the_old_form_and_picker_before_it_fetches_the_new_ones` and the new `test_a_kind_change_whose_fetch_fails_is_refused_whole_unless_overtaken`.
- 01-UI-SPEC.md (md5 `fd5268ae28966468dfa376ba8c500283`): the plan 05-25 dated note, three Copywriting rows, rules 14, 30, 34 and 36, six UI Considerations rows, a Verification status bullet and the Extension rule 3 clause. `Applicable: 82` unchanged.
- WR-10 and IN-08 flipped to `fixed` with `b857016` in 05-REVIEW-DISPOSITION.md.

## Task Commits

1. **Task 1 (tracer, TDD): take the old part off screen on a kind switch and refuse a failed one whole** - `b857016` (fix). RED is recorded below and not committed: every commit is green (plan commit protocol).
2. **Task 2: record WR-10 and IN-08 as fixed and run the final gate** - `d85a024` (docs)

**Plan metadata:** the SUMMARY commit that follows this file, then the STATE/ROADMAP update.

## RED evidence (BASE = `c9c1bc7`; `git diff --quiet 9f68e69 HEAD -- src tests docs 01-UI-SPEC.md 05-REVIEW-DISPOSITION.md` exit 0)

Server: `.venv/bin/screw serve --port 8025`. All seven extracted grounded blocks matched the plan's md5s (`test_05_25.diff` ab73535d..., `app_05_25.diff` cd71c00c..., `uispec_05_25.py` a5537908..., `mutants_05_25.py` 9a4fe2e7..., `probe_05_25.py` 7ec2ff12..., `probe_05_23.py` 4e913d25..., `probe_05_24.py` afb4467e...). `SCREW_PROBE_APP_JS` unset.

`probe_05_25.py` at BASE: exit 1, 5 PASS lines and exactly the eleven predicted FAIL steps (`fail:` x2, `retry:`, `fail-link:` refusal, `window-schema:`, `window-catalogue:`, `overtaken-schema:`, `overtaken-catalogue:`, `status:`, `startup:` x2). The decisive readings:

```
FAIL fail: a failed schema fetch leaves nothing of the old part on screen (WR-10) {"inputs": 0, "dims": 9, "link": "#kind=nut&d=6&pitch=1&left_hand=false&s=10&m=5.2", "downloads": ["api/bolt/model.stl?quality=fine", "api/bolt/model.step?quality=fine"], ...}
FAIL fail: the switch is refused whole ... {"errors": ["Could not load the part: 500 Internal Server Error"], "kind": "nut", "kindIndex": 1, "hash": "#kind=nut", "status": "", "pageerrors": []}
FAIL retry: ... {"kindIndex_before": 1, ...}
FAIL window-schema / window-catalogue: {"dims": 9, "link": "#kind=nut&...", "downloads": ["api/bolt/model.stl?quality=fine", ...], "held": 1}
FAIL overtaken-schema: bolt whole but "errors": ["Could not load the part: 500 Internal Server Error"]
FAIL overtaken-catalogue: {"names": [], "kind": "", ..., "dims": 0, "link": null, "downloads": [null, null], "errors": ["Could not load the part: 500 Internal Server Error"]}
FAIL status: {"before": "Showing the last valid part", "during": "Showing the last valid part", "after": ""}
FAIL startup: {... "errors": ["Could not load the part kinds and schema: 500 Internal Server Error"], "kind": "bolt", "kindIndex": 0, ...}
RESULT FAIL [eleven steps]
```

`probe_05_23.py` at BASE: exit 0, 17 PASS, `RESULT PASS []`. `probe_05_24.py` at BASE: exit 0, 11 PASS, `RESULT PASS []`.

RED test run, after `git apply` of the test patch (tests/test_parity.py md5 `71ee546a...` as grounded):

```
make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"
FAILED tests/test_parity.py::test_a_kind_change_clears_the_old_form_and_picker_before_it_fetches_the_new_ones
FAILED tests/test_parity.py::test_a_kind_change_whose_fetch_fails_is_refused_whole_unless_overtaken
2 failed, 71 passed in 5.79s
```

The first failed in its clear loop on `$('#dims').replaceChildren();`; the second at `assert "await" not in head` (the old `if (!(await buildForm(kind))) return;` sits before the `try`). Semantic assessment: each target test ran and failed on the planned assertion for the intended reason (the new clears and the single `try` are absent). No `tdd-red-evidence` classifier run: the plan is `type: execute`, and pytest output is not one of the classifier's report formats.

## GREEN evidence (code at `b857016`, working tree = committed)

- `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"`: `73 passed in 6.30s`.
- md5s: app.js `b77c651eb38e5b669eff786c609fed70`, tests/test_parity.py `71ee546af9b093c113163a0ee21a1313`, 01-UI-SPEC.md `fd5268ae28966468dfa376ba8c500283`.
- Mutant check, `.venv/bin/python -I mutants_05_25.py src/screw/static/app.js tests/test_parity.py` (IN-08's evidence):

```
ok   fix | 73 passed in 5.19s | []
ok   benign: another clearForm call | 73 passed in 5.10s | []
ok   benign: the schema await split | 73 passed in 5.32s | []
ok   benign: a comment between clears | 73 passed in 5.65s | []
ok   defect: no overtaken guard | 1 failed, 72 passed in 6.79s | ['test_a_kind_change_whose_fetch_fails_is_refused_whole_unless_overtaken']
ok   defect: panel cleared after the schema | 1 failed, 72 passed in 6.56s | ['test_a_kind_change_clears_the_old_form_and_picker_before_it_fetches_the_new_ones']
ok   defect: BASE app.js | 2 failed, 71 passed in 5.92s | [both pins]
ok   old pin, BASE | 72 passed in 6.91s | []
ok   old pin, another clearForm call | 1 failed, 71 passed in 7.09s | [the 05-24 pin]
ok   old pin, the schema await split | 1 failed, 71 passed in 6.32s | [the 05-24 pin]
ok   old pin, a comment before the fetch | 1 failed, 71 passed in 5.77s | [the 05-24 pin]
MUTANTS PASS []
```

- `probe_05_25.py` on the patched app.js: exit 0, 16 PASS lines, `RESULT PASS []`. Decisive readings:

```
PASS fail: ... {"inputs": 0, "dims": 0, "link": null, "downloads": [null, null], "picker": {"hidden": true, "selects": [], "badge": ""}}
PASS fail: the switch is refused whole ... {"errors": ["Could not load the part: 500 Internal Server Error"], "kind": "", "kindIndex": -1, "hash": "#kind=nut", "status": "", ...}
PASS retry: ... {"kindIndex_before": -1, "names": ["d","pitch","left_hand","s","m","clearance"], "picker": {"selects": ["ISO 4032","M6"], ...}, "errors": ["Clearance (radial): Field required"]}
PASS window-schema / window-catalogue: {"dims": 0, "link": null, "downloads": [null, null], "held": 1}
PASS overtaken-schema / overtaken-catalogue: the bolt whole, errors []
PASS status: {"before": "Showing the last valid part", "during": "", "after": ""}
PASS startup: selector deselected; picking bolt then loads and builds it
PASS switch: the nut at 0.1 (dims 11, link #kind=bolt&d=6&pitch=1&left_hand=false&s=10&k=4, nut downloads with clearance=0.1) and back on the bolt (dims 9, link carrying 0.1)
RESULT PASS []
```

- `probe_05_23.py` after the fix: exit 0, 17 PASS, `RESULT PASS []`. `probe_05_24.py` after the fix: exit 0, 11 PASS, `RESULT PASS []`. Nothing of 05-21 to 05-24 regressed.
- UI-SPEC grep check from Task 1's verify: `UISPEC_GREP_OK`. Disposition check from Task 2's verify: `DISP_OK`.
- `make verify` on the final tree (HEAD `d85a024`): exit 0, `3467 passed in 158.79s (0:02:38)` (3466 at 9f68e69 plus the new test; the re-bodied test keeps its slot). The pre-commit hook ran `make verify` and passed on both commits.
- `git diff --name-only c9c1bc7 HEAD | sort`: exactly the four files_modified paths. `git diff --quiet 9f68e69 HEAD -- src/screw/calc src/screw/app.py src/screw/cli.py src/screw/static/index.html src/screw/static/style.css docs/architecture/decision_log.md`: exit 0.

## Files Created/Modified

- `src/screw/static/app.js` - navigate only: `mine`, four clears, one `try`, the guard, two why comments.
- `tests/test_parity.py` - `_rebuild_block()`, the re-bodied WR-09 pin, the WR-10 pin.
- `.planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md` - the contract rows, rules and notes above.
- `.planning/phases/05-hex-nut-and-kernel-pair-proof/05-REVIEW-DISPOSITION.md` - WR-10 and IN-08 `fixed` with `b857016`.

## Decisions Made

Followed the plan's candidate D. It widens the review's patch by the overtaken guard, the one shared `try` and `setStatus('')`, each measured by the planner and each flagged in the plan for the owner; the revert of any of them is listed in the plan's Decisions. IN-08 is recorded `fixed` on the mutant evidence; if the owner wants it open until a browser test lands it is a one-row revert in `d85a024`. UI-SPEC E12 (`loading`, the badge across a kind switch) is stale since 05-24 and is left unedited, as the plan flagged.

## Deviations from Plan

None - plan executed exactly as written. Process notes, not deviations:

- The first commit was made with the `Co-Authored-By: Claude Opus 5.5` line given in the dispatch constraints, then amended before anything else used its sha (`d81f47b` became `b857016`; message only, the hook re-ran green) so the line matches the session's attribution (`Claude Sonnet 5.5`), which is also what 5cbc40f uses. The sha in the disposition and in this SUMMARY is the amended one.
- The execute-phase `gsd-tools query commit` helper was not used (30 s timeout vs a ~160 s hook, per the phase constraints); plain `git commit` with a 600 s timeout was.

## Issues Encountered

None. Port 8025 was free. Task 1's tracer gate: auto mode is off and `HUMAN_VERIFY_MODE` is `end-of-phase` with an automated-only `<verify>`, so the verify was re-run end to end (73 passed, three probes passed, mutants passed) and the run expanded to Task 2 without a checkpoint. The plan's human-check (the failure and the throttled switch in a real browser, Matching nut then Back, UAT tests 1 and 3) is the owner's end-of-phase item.

## Known Stubs

None.

## Tech debt

No tech-debt item or idea filed. The two planner measurements (the overtaken failure and the status claim) were fixed in Task 1, not deferred. The E12 `loading` row is the owner's call, flagged in the plan and above; it is not filed.

## Threat Flags

None - page state only; no new endpoint, auth path, file access or schema change. T-05-82 to T-05-86 are mitigated as the plan's register states (clears before the first await, one refusing `try`, the overtaken guard, `setStatus('')`, contract and disposition checked by command).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

WR-10 and IN-08 are closed in code, pins and contract; only IN-07 (`tests/test_nut.py`, out of scope by the plan) stays open in the disposition. Ready for re-verification of phase 5 and the owner's browser steps.

## Self-Check: PASSED

Verified: `src/screw/static/app.js`, `tests/test_parity.py`, 01-UI-SPEC.md and 05-REVIEW-DISPOSITION.md exist and differ in `c9c1bc7..HEAD`; commits `b857016` and `d85a024` are ancestors of HEAD; commit 1 lists exactly app.js, test_parity.py and 01-UI-SPEC.md, commit 2 only the disposition file; `git rev-list --count c9c1bc7..HEAD` was 2 before this SUMMARY.

---
*Phase: 05-hex-nut-and-kernel-pair-proof*
*Completed: 2026-10-22*
