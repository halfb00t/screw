---
phase: 06-printed-pair-acceptance
plan: 02
subsystem: planning
tags: [owner-rulings, printed-test, protocol, decision-record]

requires:
  - phase: 06-printed-pair-acceptance
    provides: 06-RESEARCH.md open questions 1-5 and pitfalls 3, 4, 6
provides:
  - 06-OWNER-RULINGS.md, the owner's rulings R1-R8, dated 2026-10-22, taken before any Phase 6 record row exists
affects: [06-03 protocol (R1-R5), 06-06 (R7, R8), 06-07 (R6), 06-09 (R7)]

actuals:
  tokens: 1500
  tasks: 2
  commits: 1

key-files:
  created:
    - .planning/phases/06-printed-pair-acceptance/06-OWNER-RULINGS.md

key-decisions:
  - "R1 a: run 2 is pre-registered in PR A with run 1; its clearance is the value the run-1 rule returns"
  - "R2 a: 12 more bolts from the same matrix STLs, used only in the bought nuts"
  - "R3 a: one bolt meets its five nuts loosest to tightest, order recorded per sample"
  - "R4 a: sample k of every cell on plate set k, plate recorded per part"
  - "R5 b: a part that fails to print is reprinted alone before any fit test of its cell; narrows D-08's no-reprint wording by owner ruling"
  - "R6 a: the D-09 nut warning fires when d < 6.0 or d > 12.0"
  - "R7 a: L17 for the default after run 1, L18 for the threshold after run 2"
  - "R8 b: _req becomes the default-carrying helper _free; the generic required-field rule stays in the CLI, the page and the parity tests"

requirements-completed: [PAIR-02, PAIR-06, INFO-04]

coverage:
  - id: D1
    description: "Eight owner rulings recorded with the offered option name, date and applying plan, before any record row exists"
    requirement: "PAIR-02"
    verification:
      - kind: other
        ref: "plan Task 2 automated checks: every ruling line R1-R8 carries an option id; exactly one dated Ruled line"
        status: pass
    human_judgment: false

duration: 6min
completed: 2026-10-22
status: complete
plan_head_before: 7bad66b7ec76fbc4e63eeadb9b7d75861f8d6273
plan_head_after: 629f0d66face269a4ad7cedbd344c6f2ecdfa1ef
---

# Phase 6 Plan 02: Owner rulings for the printed test Summary

**The owner's eight rulings (R1-R8) on the printed test, recorded in one dated file before any record row exists.**

## Accomplishments

- `06-OWNER-RULINGS.md` holds R1-R8, each with the offered option name and the plan that applies it. The owner's reply was `r1-a r2-a r3-a r4-a r5-b r6-a r7-a r8-b` with no extra words, so no ruling carries a quotation.
- R5 b is recorded as narrowing D-08's no-reprint wording by owner ruling.
- R1 was not b: no plan is inserted before 06-08. R8 was not c: no `docs/ideas/` file and no `INDEX.md` row.

## Task Commits

1. **Task 1: Owner rulings R1-R8** - checkpoint decision; nothing committed (answered by the owner)
2. **Task 2: Record the rulings** - `629f0d6` (docs)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. The commit hook ran `make verify` and passed. `git show --stat HEAD` lists only `06-OWNER-RULINGS.md`.

## Known Stubs

None.

## Threat Flags

None.

## Ideas and debt

No `docs/ideas/` or `docs/tech_debt/` item filed.

## Self-Check: PASSED

- FOUND: .planning/phases/06-printed-pair-acceptance/06-OWNER-RULINGS.md
- FOUND: 629f0d6 (ancestor of HEAD)
