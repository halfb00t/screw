---
phase: 08-pre-release-gap-closure
plan: 04
subsystem: web
tags: [web, parity, touched, l35, int-03, decision-log, ui-spec, tech-debt]

requires:
  - phase: 08-pre-release-gap-closure
    provides: "08-02's L34, the decision-log tail L35 follows"
provides:
  - "The page's touched set: a typed, picked or linked field is written to the request and the link even at its default (D-11, D-12)"
  - "Executed API and CLI typed-default parity tests, one for the INT-03 part and one registry-driven over every kind's defaulted fields (D-13)"
  - "L35, with superseded-in-part notes in L19 and L21"
  - "UI-SPEC rule 38 and the amended rules 6, 9, 19 and two Copywriting rows"
  - "The web half of typed-default parity filed as must debt with triggers"
affects: [08-05]

actuals:
  tokens: 12200
  tasks: 2
  commits: 3

plan_head_before: 51b8d098f70eb191da3a2744a9d992630d21b7dd
plan_head_after: 2c69a577153303e545cd8b21393db759a03fca89

tech-stack:
  added: []
  patterns:
    - "A page rule with no browser harness is pinned as source text in PINNED_STATEMENTS plus one recorded owner browser check, and filed as debt with triggers"

key-files:
  created:
    - docs/tech_debt/active/2026-11-03-typed-default-web-half-is-source-pinned.md
  modified:
    - src/screw/static/app.js
    - tests/test_parity.py
    - docs/architecture/decision_log.md
    - .planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md
    - docs/tech_debt/INDEX.md

key-decisions:
  - "L35 (written from 08 D-11 to D-13, no new ruling): the page counts a field the user typed, picked or linked as explicit, as the API and the CLI do"

patterns-established:
  - "touched is read only by partQuery; no field name is written as a literal in app.js (rule 29)"

requirements-completed: [FRNT-05]

status: complete
---

# Phase 8 Plan 04: Typed defaults are explicit on the web Summary

The page keeps a `touched` set so a field typed, picked from a preset or named by the link reaches the request and the link even at its default; the API and the CLI are proven to answer such a part alike for every kind, and the rule is logged as L35.

## Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Tracer: a typed default from the input event through partQuery to the same API and CLI answer | dccefdf | src/screw/static/app.js, tests/test_parity.py |
| 2 | L35, the L19 and L21 notes, the UI-SPEC amendments | a43f187 | docs/architecture/decision_log.md, 01-UI-SPEC.md |
| 2 | The web half filed as debt | 2c69a57 | docs/tech_debt/active/2026-11-03-typed-default-web-half-is-source-pinned.md, docs/tech_debt/INDEX.md |

## Browser check

Run by the owner against `make serve` at head dccefdf: kind bolt, Diameter 30, Pitch 2, Across flats 48, Head height 18, then Thread length typed 20, then cleared. Expected: with 20 typed the link carries `thread_length=20`, no warning starts `thread_length: the default 20 mm`, both STL downloads show the refusal; cleared, `thread_length` leaves the link and the first warning starts `thread_length: the default 20 mm`.

Owner's reply, verbatim: "pass"

The owner gave a bare "pass", not a quoted reading of the page. The check is therefore recorded as a pass against the expected result above, not as text the owner read off the screen.

The API's answer for the same queries, fetched in-process with the test client at head 2c69a57 (not invented):

`GET /api/bolt/info?d=30&pitch=2&s=48&k=18&thread_length=20` is 200; no warning starts `thread_length: the default`; the downloads are:

- stl fine: `d, pitch, length, s, k and thread_length: the fine STL (stl-fine) of this bolt is predicted over its measured budget (L21), so it is refused before any build; the STEP (step) of this part fits. To get it, change one of these fields, or download an artifact that fits`
- stl preview: `d, pitch, length, s, k and thread_length: the preview STL (stl-preview) of this bolt is predicted over its measured budget (L21), so it is refused before any build; the STEP (step) of this part fits. To get it, change one of these fields, or download an artifact that fits`
- step fine and step preview: no refusal

`GET /api/bolt/model.stl` with the same query is 422 `over_budget`, `ctx.fields` `["d","pitch","length","s","k","thread_length"]`.

`GET /api/bolt/info?d=30&pitch=2&s=48&k=18` is 200 with first warning `thread_length: the default 20 mm puts the preview STL (stl-preview) and fine STL (stl-fine) of this bolt over its measured budget (L21), so thread_length is capped at 15.5 mm, the largest value on its 0.5 mm form step at which every artifact fits; give thread_length to choose it, and an artifact over the budget is then refused`, and no download is refused.

## Verification

`make verify`: ruff, mypy `--strict`, import boundaries, unfinished-work scan and pytest all pass; pytest result line `5125 passed in 191.72s (0:03:11)`. Each of the three commits also passed the pre-commit `make verify` hook.

## Deviations from Plan

None - plan executed exactly as written. The browser check matched `<expected>`, so Task 2 started.

## Issues Encountered

None.

## Known Stubs

None.

## Threat Flags

None. T-08-12 is mitigated by the executed parity tests and the pinned page writers; T-08-42 by the recorded browser check and the must debt with triggers.

## Debt filed

- `docs/tech_debt/active/2026-11-03-typed-default-web-half-is-source-pinned.md` (must, row in `docs/tech_debt/INDEX.md`)

## Self-Check: PASSED

Files, commits dccefdf, a43f187 and 2c69a57 exist and are ancestors of HEAD; L35 appears once; both superseded notes, rule 38 and the Phase 8 note are present.
