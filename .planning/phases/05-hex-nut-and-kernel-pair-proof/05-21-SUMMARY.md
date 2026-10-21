---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 21
subsystem: ui
tags: [picker, showMatch, gap-closure, G-05-1, playwright-probe]
requires:
  - phase: 05-hex-nut-and-kernel-pair-proof
    provides: "plan 05-20 (the nut page and UAT that found G-05-1)"
provides:
  - "rowOfFields() in app.js: after a failed update the selects show the catalogue row the fields hold exactly, else blank"
  - "source pin test_after_a_failed_update_the_selects_show_the_row_the_fields_hold_exactly"
  - "01-UI-SPEC.md amended (rules 15 and 32, E11, E16, Verification status, extension rule 3)"
  - "docs/ideas entry putting the browser-test-in-the-gate decision to the owner"
affects: [05-22, phase-5-uat-rerun]
commits: 3
plan_head_before: 0d1895a4eca0b01283ad8a16fbc781660bef972a
plan_head_after: c65f6e5bc308f85c6696bbe9033abe2a72c618db
actuals:
  tokens: 3200
  tasks: 3
  commits: 3
tech-stack:
  added: []
  patterns:
    - "client-side exact catalogue match by the server's rule and order, generic over kind and fields"
key-files:
  created:
    - docs/ideas/2026-10-21-browser-test-of-the-page-in-the-gate.md
  modified:
    - src/screw/static/app.js
    - tests/test_parity.py
    - .planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md
    - docs/ideas/INDEX.md
key-decisions:
  - "Match the fields client-side on any failure rather than special-casing the nut's missing clearance"
  - "The badge stays empty after a failure and presetBasis is untouched; only the selects change"
  - "The reproduction is a scratch Playwright probe on spur's venv; a browser in the gate is filed for the owner, not taken"
requirements-completed: [TYPE-03]
coverage:
  - id: D1
    description: "With kind nut and the clearance empty, picking ISO 4032 then M6 keeps the selects on ISO 4032 / M6 with the M6 fields, and nothing builds"
    requirement: TYPE-03
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_after_a_failed_update_the_selects_show_the_row_the_fields_hold_exactly"
        status: pass
    human_judgment: true
    rationale: "No browser is in the gate (L01). The scratch probe drove a headless shell, not the owner's browser; the owner re-runs UAT test 1."
  - id: D2
    description: "01-UI-SPEC.md describes the selects following the fields after a failed update"
    verification: []
    human_judgment: true
    rationale: "Prose contract amendment; reviewed by reading."
  - id: D3
    description: "Browser test in the gate filed as an open owner decision"
    verification: []
    human_judgment: true
    rationale: "A decision for the owner, not a verifiable behaviour."
duration: ~40min (start time not recorded; estimate from commit and hook timing)
completed: 2026-10-21
status: complete
---

# Phase 5 Plan 21: Nut preset pick holds with an empty clearance Summary

**After any failed update the picker's selects show the first catalogue row the form holds exactly (the server's rule and order), else blank, so ISO 4032 then M6 stays picked on a nut with no clearance (G-05-1).**

## Performance

- **Duration:** ~40 min (start time not recorded; estimate)
- **Completed:** 2026-10-21T10:37Z
- **Tasks:** 3
- **Files modified:** 5 (one created)

## Accomplishments
- `rowOfFields()` added to `src/screw/static/app.js`; `showMatch` takes it when `preset === null`. Exact `Number(held) === value`, `held !== ''`, no `Math.`, no field or kind name. Badge branches, `presetBasis`, `pick`, `showPicks`, `update`, `fail`, `renderInfo`, `partQuery` and `writeHash` untouched.
- Source pin `test_after_a_failed_update_the_selects_show_the_row_the_fields_hold_exactly` in `tests/test_parity.py`.
- 01-UI-SPEC.md amended in place: dated note, rules 15 and 32, a new E11 row, E16, `Applicable:` recounted to 82 (resolved 65, explicit 48), Verification status, extension rule 3.
- Idea filed for the owner: a browser test in the gate (options a and b, neither taken).
- The default nut now opens with ISO 4032 / M6 in the selects (its fields are the M6 row); a bolt whose fields are a row keeps that row after a failed update.

## Task Commits

BASE (HEAD before Task 1): `0d1895a4eca0b01283ad8a16fbc781660bef972a`

1. **Task 1: keep a nut preset pick in the selects while the clearance is empty** - `a22734e` (fix; app.js, tests/test_parity.py)
2. **Task 2: UI contract says the selects follow the fields after a failed update** - `18d896a` (docs; 01-UI-SPEC.md)
3. **Task 3: file the browser-test-in-the-gate decision** - `c65f6e5` (docs; the idea file and INDEX.md)

**Plan metadata:** the docs(05-21) completion commit that follows this file.

`git diff --stat BASE..HEAD` before the metadata commit touches only the five files in `files_modified`.

## RED evidence

### Probe, RED, at HEAD `0d1895a` (tree untouched), server `.venv/bin/screw serve --port 8011`, `SCREW_PROBE_APP_JS` unset

Command: `PLAYWRIGHT_BROWSERS_PATH=/Users/half/git/halfb00t/spur/.venv/ms-playwright /Users/half/git/halfb00t/spur/.venv/bin/python probe_g05_1.py http://127.0.0.1:8011/` (script in the session scratch directory, not in the repo). Exactly the three predicted FAIL steps; `d 6.5` passed:

```
FAIL open nut: the selects follow the default fields {"selects": ["", ""], "sizes": [""], "fields": {"d": "6", "pitch": "1", "left_hand": "false", "s": "10", "m": "5.2", "clearance": ""}, "status": "", "dims": 0, "disabled": ["true", "true"], "errors": ["Clearance (radial): Field required"]}
PASS d 6.5: no row, blank selects {"selects": ["", ""], "sizes": [""], "fields": {"d": "6.5", "pitch": "1", "left_hand": "false", "s": "10", "m": "5.2", "clearance": ""}, "status": "", "dims": 0, "disabled": ["true", "true"], "errors": ["Clearance (radial): Field required"]}
FAIL pick ISO 4032: the selects keep ISO 4032 / M2 {"selects": ["", ""], "sizes": [""], "fields": {"d": "2", "pitch": "0.4", "left_hand": "false", "s": "4", "m": "1.6", "clearance": ""}, "status": "", "dims": 0, "disabled": ["true", "true"], "errors": ["Clearance (radial): Field required"]}
FAIL pick M6: M6 is not offered in Size ['']
RESULT FAIL ['open nut: the selects follow the default fields', 'pick ISO 4032: the selects keep ISO 4032 / M2', 'pick M6']
```

(The shell pipeline swallowed the exit code in the log; `RESULT FAIL` is the script's `sys.exit(1)` branch.)

### Source test, RED

`make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov -k fields_hold_exactly"`:

```
>       row_of_fields = _squash(_function_body("rowOfFields"))
E       AssertionError: rowOfFields
tests/test_parity.py:644: AssertionError
FAILED tests/test_parity.py::test_after_a_failed_update_the_selects_show_the_row_the_fields_hold_exactly
1 failed, 66 deselected in 1.55s
```

## GREEN evidence

### Probe, GREEN, same server and command, after the app.js edit (uncommitted tree, HEAD `0d1895a` + edit), exit 0

```
PASS open nut: the selects follow the default fields {"selects": ["ISO 4032", "M6"], "sizes": ["", "M2", "M2.5", "M3", "(M3.5)", "M4", "M5", "M6", "M8", "M10", "M12", "(M14)", "M16", "(M18)", "M20"], "fields": {"d": "6", "pitch": "1", "left_hand": "false", "s": "10", "m": "5.2", "clearance": ""}, "status": "", "dims": 0, "disabled": ["true", "true"], "errors": ["Clearance (radial): Field required"]}
PASS d 6.5: no row, blank selects {"selects": ["", ""], "sizes": [""], "fields": {"d": "6.5", "pitch": "1", "left_hand": "false", "s": "10", "m": "5.2", "clearance": ""}, "status": "", "dims": 0, "disabled": ["true", "true"], "errors": ["Clearance (radial): Field required"]}
PASS pick ISO 4032: the selects keep ISO 4032 / M2 {"selects": ["ISO 4032", "M2"], "sizes": ["", "M2", "M2.5", "M3", "(M3.5)", "M4", "M5", "M6", "M8", "M10", "M12", "(M14)", "M16", "(M18)", "M20"], "fields": {"d": "2", "pitch": "0.4", "left_hand": "false", "s": "4", "m": "1.6", "clearance": ""}, "status": "", "dims": 0, "disabled": ["true", "true"], "errors": ["Clearance (radial): Field required"]}
PASS pick M6: the selects keep ISO 4032 / M6 {"selects": ["ISO 4032", "M6"], "sizes": ["", "M2", "M2.5", "M3", "(M3.5)", "M4", "M5", "M6", "M8", "M10", "M12", "(M14)", "M16", "(M18)", "M20"], "fields": {"d": "6", "pitch": "1", "left_hand": "false", "s": "10", "m": "5.2", "clearance": ""}, "status": "", "dims": 0, "disabled": ["true", "true"], "errors": ["Clearance (radial): Field required"]}
RESULT PASS []
```

No nut `model.stl` request at any step, status empty, panel empty, both downloads disabled (the probe's `check` asserts these).

### Source tests, GREEN

`make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"`: `67 passed in 5.06s`.

### Gate

Command: `make verify` on the final tree (after commit 3). Result line: `======================= 3461 passed in 195.47s (0:03:15) =======================`, exit 0. The pre-commit hook ran the same `make verify` and passed on all three commits.

## Decisions Made
- Client-side match on any failure (the plan's second option): one generic rule that covers every kind and every failure with no field name, instead of parsing which fields a 422 names.
- Badge and `presetBasis` unchanged after a failure: the badge reads only an info document (rule 33, D-09).
- The probe stays in session scratch; a committed browser test is the owner's decision (idea file).

## Deviations from Plan

None - plan executed exactly as written. Two small notes, neither a deviation: the doc comment of `showMatch` paraphrases the diameter, pitch, width and height values in words, because `tests/test_parity.py` forbids quoted field names in app.js even in comments; and the plan's step 8 stop of the server was run before the commit rather than after the final `<verify>`, since the probe's `<verify>` had already run in step 5.

**Total deviations:** 0.
**Impact on plan:** none.

## Issues Encountered
- The Bash tool's `PIPESTATUS` was not usable in this shell, so the RED probe's exit code was not captured in the log; `RESULT FAIL` is printed only on the branch that exits 1. The GREEN run's exit code (0) was captured.
- The pre-commit hook stashes and restores unstaged files (STATE.md, state.json); they were restored intact each time and the orchestrator's untracked files were never staged.

## Known Stubs

None.

## Threat Flags

None. No new endpoint, auth path or file access; `rowOfFields` reads the catalogue the page already fetched. T-05-60, T-05-61 and T-05-62 mitigations are pinned by the new source test and the probe.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Plan 05-22 (G-05-3) can proceed; it edits the same three files and depends on this plan.
- Owner end-of-phase item: re-run 05-UAT.md test 1 in a real browser (steps in the plan's Task 1 human check). No browser is in the gate.
- Open owner decision filed: `docs/ideas/2026-10-21-browser-test-of-the-page-in-the-gate.md`. No tech debt filed.

## Self-Check: PASSED

Files found: `src/screw/static/app.js`, `tests/test_parity.py`, `.planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md`, `docs/ideas/2026-10-21-browser-test-of-the-page-in-the-gate.md`, `docs/ideas/INDEX.md`. Commits `a22734e`, `18d896a`, `c65f6e5` are ancestors of HEAD.

---
*Phase: 05-hex-nut-and-kernel-pair-proof*
*Completed: 2026-10-21*
