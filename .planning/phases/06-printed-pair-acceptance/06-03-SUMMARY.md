---
phase: 06-printed-pair-acceptance
plan: 03
subsystem: testing
tags: [pre-registration, protocol, owner-profile, scope-cut, pull-request]

requires:
  - phase: 06-printed-pair-acceptance
    provides: plan 06-01's rule and matrix modules and blank records; plan 06-02's owner rulings R1-R8
provides:
  - 06-PRINT-PROTOCOL.md on gsd/phase-06-preregistration, nine sections in order, owner profile and predictions typed in, no bought-nut test
  - tests binding the protocol text to the rule module, and a guard that fails while an owner slot is left
  - PR A, https://github.com/halfb00t/screw/pull/19 (gsd/phase-06-preregistration -> main), open
  - ruling R9 applied across REQUIREMENTS, ROADMAP, CONTEXT, OWNER-RULINGS, plans 06-04 to 06-06 and the validation map
affects: [06-04 review and landing of PR A, 06-05 run 1, 06-06 L17 and requirement evidence]

actuals:
  tokens: 60000
  tasks: 3
  commits: 3

key-files:
  created:
    - .planning/phases/06-printed-pair-acceptance/06-PRINT-PROTOCOL.md (on the pre-registration branch)
  modified:
    - bench/print_rules.py
    - bench/print_matrix.py
    - tests/test_print_rules.py
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/phases/06-printed-pair-acceptance/06-CONTEXT.md
    - .planning/phases/06-printed-pair-acceptance/06-OWNER-RULINGS.md
    - .planning/phases/06-printed-pair-acceptance/06-04-PLAN.md
    - .planning/phases/06-printed-pair-acceptance/06-05-PLAN.md
    - .planning/phases/06-printed-pair-acceptance/06-06-PLAN.md
    - .planning/phases/06-printed-pair-acceptance/06-VALIDATION.md
  deleted:
    - bench/results/phase-06/bought-nut.tsv (on the pre-registration branch)

key-decisions:
  - "R9 (owner, 2026-10-22, Defer + strip, 'drop PAIR-06'): PAIR-06 and PAIR-07 move to v2; the bought-nut test is removed from Phase 6 before any print. No Lxx entry: it is a scope cut, not architecture."
  - "The run-2 prediction is renumbered P3 after P3 (PAIR-07) was removed; nothing else referenced P2-P4."
  - "The owner has no prediction for P2 and P3; both are recorded as 'owner: no prediction (\"have no idea\", 2026-10-22)', not filled in on the owner's behalf."
  - "PAIR-06 stays in the traceability table as 'v2 (deferred)' so the requirement is not silently deleted; v1 coverage reads 38."

requirements-completed: []

coverage:
  - id: D1
    description: "The protocol states every number, size, preset, record path, column and rule the modules read, and its nine sections are in order"
    requirement: "PAIR-02"
    verification:
      - kind: unit
        ref: "tests/test_print_rules.py#test_the_protocol_states_the_numbers_the_rules_read"
        status: pass
      - kind: unit
        ref: "tests/test_print_rules.py#test_the_protocol_has_the_pre_registered_sections_in_order"
        status: pass
    human_judgment: false
  - id: D2
    description: "No owner slot is left and the printer, material, layer height and slicer lines are filled; the owner's text unchanged by Claude"
    requirement: "PAIR-02"
    verification:
      - kind: unit
        ref: "tests/test_print_rules.py#test_the_protocol_has_no_owner_slot_left"
        status: pass
    human_judgment: true
  - id: D3
    description: "PR A is open against main with the pre-registration only: seven files, no STL, no filled record"
    requirement: "INFO-04"
    verification:
      - kind: other
        ref: "gh pr view 19: OPEN main; git diff --name-only origin/main...gsd/phase-06-preregistration lists the seven files"
        status: pass
    human_judgment: false

duration: 70min
completed: 2026-10-22
status: complete
plan_head_before: aeda2586d112efbea08b77da9d7069b966818149
plan_head_after: d8d990c6cd72b78363b7784840abeb5e647ac269
---

# Phase 6 Plan 03: The protocol, the owner's profile and PR A Summary

**The printed pair test's protocol is pre-registered with the owner's Prusa MK4 / Prusa PETG / 0.2 mm profile and predictions, bound to the rule module by tests, and open as PR A (#19); the bought-nut test was cut by owner ruling R9 before any print.**

## Accomplishments

- `06-PRINT-PROTOCOL.md` has the nine sections in order. Everything above `## Results` is written before any print. Two tests fail if the protocol and `bench/print_rules.py` or `bench/print_matrix.py` ever name different numbers, and a third fails while any `OWNER-SLOT` or an empty profile line remains.
- The owner's print profile, from the owner's chat answers on 2026-10-22: printer `Prusa MK4`, material `Prusa PETG`, layer height `0.2`, slicer `PrusaSlicer, Prusa PETG system profile, stock (no settings changed)`; the slicer version was not recorded by the owner. The protocol quotes the owner's words ("prusa mk4", "prusa petg", "0.2 mm", "prusa slicer, profile - prusa petg", "stock profile").
- Predictions: P1 is the owner's 0.10 mm, never an input (`default_from` reads the record). For P2 and P3 the owner said "have no idea"; the protocol records that and no prediction was written for them.
- PR A: https://github.com/halfb00t/screw/pull/19, open, base `main`, title "Pre-register the Phase 6 printed pair test: protocol, rules and records". Its body carries the PR attribution line and no skip token.
- The main checkout is on `gsd/phase-06-printed-pair-acceptance`; the worktree `.claude/worktrees/phase-06-preregistration` stays in place for plan 06-04.

## Task Commits

1. **Task 1 (tracer): protocol and number-pinning tests** - `569fda5` (docs), on `gsd/phase-06-preregistration`
2. **Task 2: the owner's profile and predictions** - checkpoint, typed by the owner in chat (no commit of its own)
3. **Scope cut R9, pre-registration side** - `3a838b4` (refactor): removed `read_bought`, `promotes_undersize`, the bought-nut constants, `bought-nut.tsv`, the bought-nut protocol text and tests
4. **Task 3: the owner's text and the slot guard** - `d8d990c` (docs), then push and PR A

On the phase branch (planning documents, R9): `e637eb6` (REQUIREMENTS, ROADMAP, CONTEXT, OWNER-RULINGS) and `a0bad1a` (plans 06-04 to 06-06 and the validation map).

## Deviations from Plan

### Owner-approved scope change

**1. [Rule 4 - owner ruling R9] PAIR-06 and PAIR-07 deferred, the bought-nut test stripped**
- **Found during:** Task 2 (the owner was asked for the bought nuts and answered "drop PAIR-06"; Claude Code then asked the scope question and the owner picked "Defer + strip")
- **Change:** PAIR-06 and PAIR-07 moved to v2 in REQUIREMENTS (reason "deferred by owner ruling 2026-10-22 (06 R9): bought-nut test dropped from Phase 6"); ROADMAP requirements line drops PAIR-06 and success criterion 4 is struck through and marked deferred; D-14 stays in CONTEXT with a dated "Superseded 2026-10-22 by owner ruling R9" note; R2 marked "moot after R9"; plans 06-04, 06-05, 06-06 and the validation map lose their bought-nut, `BOUGHT`, PAIR-06 and PAIR-07 steps (minimally; 06-03-PLAN.md itself is left as written, this summary records the difference).
- **Plan differences this causes:** PR A's file set is seven files, not the eight the plan's Task 3 verify lists (`bought-nut.tsv` is gone); the protocol has no bought-nut line in `## Print profile`; `test_the_protocol_has_no_owner_slot_left` checks printer, material, layer height and slicer only; the run-2 prediction is P3.
- **Files modified:** listed under key-files. **Commits:** `3a838b4`, `e637eb6`, `a0bad1a`.

### Auto-fixed Issues

**2. [Rule 1 - Bug] Docstring line over the 100-column limit**
- **Found during:** the first commit of the strip (the hook's ruff E501 on `bench/print_rules.py` line 5)
- **Fix:** re-wrapped the paragraph I had shortened; the commit then passed the hook.

Task 2 was a checkpoint answered by the owner in chat rather than by editing the file; Claude wrote the owner's answers into the slots verbatim in the forms the owner's reply fixed.

## Issues Encountered

None beyond the lint wrap. `make verify` on the pre-registration branch: `3507 passed in 154.46s (0:02:34)`. The commit hook also ran it on the phase branch for both planning commits and passed.

## Authentication Gates

None.

## Known Stubs

None. The `OWNER-SLOT` marker appears only inside the guard test.

## Threat Flags

None. No new network, auth, file-access or schema surface.

## Ideas and debt

No `docs/ideas/` or `docs/tech_debt/` item filed. PAIR-06 and PAIR-07 are recorded in REQUIREMENTS v2, not as debt.

## Requirements

None is ticked by this plan: it pre-registers the test. PAIR-02 and INFO-04 complete with the default (06-06) and the threshold (06-09); PAIR-05 with the acceptance print.

## Next Phase Readiness

Plan 06-04: the other CLI reviews PR A (#19) and it lands on `main`; the phase branch then merges origin/main. Plan 06-04's check of the landed file set must expect seven files. Plan 06-05 exports and prints run 1 only; there is no bought-nut record to fill.

## Self-Check: PASSED

- FOUND: `.planning/phases/06-printed-pair-acceptance/06-PRINT-PROTOCOL.md` on `gsd/phase-06-preregistration` with `grep -c OWNER-SLOT` = 0
- FOUND: `569fda5`, `3a838b4`, `d8d990c` (ancestors of the branch head); `e637eb6`, `a0bad1a` (ancestors of the phase branch)
- FOUND: `bench/results/phase-06/bought-nut.tsv` absent; no `read_bought`, `promotes_undersize`, `BOUGHT` in `bench/` or `tests/`
- FOUND: PR 19 OPEN main
