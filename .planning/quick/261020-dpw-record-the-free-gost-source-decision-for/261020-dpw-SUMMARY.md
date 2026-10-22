---
phase: quick-261020-dpw
plan: 01
subsystem: docs
tags: [standards, gost, decision-log, tech-debt, tabl-04]
requires: []
provides:
  - "L14: Phase 5 table values come from free GOST texts that adopt the ISO standards"
  - "docs/requirements/standards-sources.md: the source map"
  - "Must debt for the deferred ISO purchase"
affects: [phase-05 plans 05-06 to 05-18, TABL-04]
key-files:
  created:
    - docs/requirements/standards-sources.md
    - docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md
  modified:
    - docs/architecture/decision_log.md
    - docs/requirements/README.md
    - docs/tech_debt/INDEX.md
    - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-OWNER-READS.md
    - .planning/STATE.md
decisions:
  - "L14: GOST-only sources for Phase 5; the ISO purchase is deferred as must debt"
metrics:
  tasks: 3
  files: 7
completed: 2026-10-20
status: complete
commits: 1
plan_head_before: 895da33
plan_head_after: e738d17
actuals:
  tasks: 3
  commits: 1
---

# Quick 261020-dpw: Record the free GOST source decision for Phase 5 Summary

The owner's choice of 2026-10-20 (free GOST texts instead of purchased ISO copies) is locked as L14, mapped in `docs/requirements/standards-sources.md`, and the ISO purchase is filed as must debt.

## Result

- Commit: `e738d17` docs: source Phase 5 table values from free GOST equivalents (7 files, 245 insertions, 3 deletions).
- `make verify` result line: `2769 passed in 87.46s (0:01:27)` (coverage 97.45%, required 96.0%). It ran standalone and again in the pre-commit hook (hook: Passed).
- Debt item filed: `docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md` (Severity must), with its INDEX row.
- `git config core.bare` after the commit: `false`.

## Deviations from Plan

None. The plan executed as written. `decision_log.md` shows 71 added lines and 0 deleted; `05-OWNER-READS.md` shows 8 added and 0 deleted. No millimetre value from any standard is in the repo.

## Open items for the owner

1. ISO 4014:2022 conflict: the purchase list names it, while L13 records Phase 4's rows as read from a purchased copy. Nothing records why it is on the list. Asked at plan 05-12's precondition.
2. M6 s/m cross-check: the frozen nut defaults (s, m) must be compared with the GOST ISO 4032-2014 M6 row before plan 05-06. A mismatch is a stop-and-ask (D-15).
3. Amendments due before plan 05-06 executes: the pending plans' ISO preconditions (05-06, 05-08, 05-11, 05-12), ROADMAP's Phase 5 precondition and TABL-04's text in REQUIREMENTS.md. ROADMAP.md and REQUIREMENTS.md were not touched here, as planned.

## Known Stubs

None.

## Self-Check: PASSED

All seven files exist and are in commit e738d17; the 12 source URLs, the L14 terms and the debt item fields were grep-checked.
