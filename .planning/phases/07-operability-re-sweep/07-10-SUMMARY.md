---
phase: 07-operability-re-sweep
plan: 10
subsystem: planning
tags: [owner-rulings, budget, B-01, B-02, B-03, R13, G10, D-06]

requires:
  - phase: 07-operability-re-sweep
    provides: "07-09: 07-BUDGET-TABLE.md (blob 5ddf7b8) and fit.json"
provides:
  - ".planning/phases/07-operability-re-sweep/07-OWNER-RULINGS.md: B-01 C1, B-02 over_budget, B-03 part-wide"
affects: [07-11, 07-12, 07-13, 07-14, 07-15]

actuals:
  tasks: 4
  commits: 2      # 8079a6a (rulings), ca0c727 (debt item the owner ruled on)
---

# 07-10: the owner's budget, refusal shape and default cap

The orchestrator ran this plan inline: all three tasks are `blocking-human` checkpoints, and no
executor agent was spawned. The owner answered by selecting one option per checkpoint, each the
orchestrator's recommended one.

## Rulings (07-OWNER-RULINGS.md, 8079a6a)

- **B-01: C1, catalogue-complete.** Raw bytes, cold build seconds and cgroup peak bytes per artifact:
  - stl-preview (55704726.47566052, 34.127968722622484, 1049185338.9620932)
  - stl-fine (239508059.14804876, 94.42979276577135, 2930457561.336711)
  - step (9748694.773917168, 15.000925691551677, 422239338.63724077)
  - All 294 bolt and 14 nut catalogue rows keep all three artifacts.
- **B-02: over-budget.** One 422 `type`, `over_budget`, with `ctx.fields` and `ctx.artifact`.
  `fine_stl_cap` is retired, and L21 lists the new type.
- **B-03: part-wide.** A defaulted bolt `thread_length` then `length`, or nut `m`, is capped to
  the largest form-step value at which every artifact fits, with one warning. `d`, pitch, `s`,
  `k`, clearance, head chamfer and hand never move.

## Also ruled

07-09's finding: 20 explore parts inside the L20 walls read `refused` with `BuildError` at every
artifact. The owner chose "File must debt, continue". Filed as
`docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md` (ca0c727). Checked from
the records, hand matters: the left twins of three refused right-hand bolts read `ok`. It is not
right-hand only, because 5 of the 17 refused bolts are left-hand.

## Verification

- `grep -cE "^## B-0[123]" 07-OWNER-RULINGS.md` prints 3.
- `git log -1 --format=%s` on 8079a6a is the plan's subject.
- The pre-commit `make verify` passed on both commits.

## Deviations

- The plan says "quote the owner's reply verbatim". Each reply was an option selection, so the
  recorded reply is the selected label, for example `c1 (Recommended)`. The file says
  "(Recommended)" is the orchestrator's label, not part of the ruling.
- The orchestrator wrote this plan's records itself, not an executor.

No requirement is ticked: OPER-02 and OPER-03 are not wholly done.
