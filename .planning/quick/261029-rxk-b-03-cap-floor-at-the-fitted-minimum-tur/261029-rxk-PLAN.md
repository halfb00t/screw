---
phase: quick-261029-rxk
plan: 01
type: quick
branch: gsd/phase-07-operability-re-sweep
base: 97600d7
---

# Quick 261029-rxk: the B-03 cap never goes below the fitted minimum turns

Written by the orchestrator from the owner's ruling of 2026-10-29. No planner agent.

## The owner's ruling (quote it verbatim)

Question: the B-03 cap can cut a defaulted thread to almost nothing. An M6 with only s=15 named
gets thread_length 20 -> 0.5 mm, which is 0.5 turns. The fitted bolt points start at 3 turns.

Reply: "Floor at fitted min turns (Recommended)".

## Evidence (orchestrator, `cost.cap_defaults` at 97600d7)

| request | cap result |
| --- | --- |
| `BoltParams(s=15)`, explicit {s} | thread_length 0.5, length 20, 0.5 turns, capped for stl-preview |
| `BoltParams(d=5)`, explicit {d} | thread_length 16.5, 16.5 turns |
| `BoltParams(d=30, s=48, k=18)`, explicit {d, s, k} | thread_length 6.5, 6.5 turns |

The debt item is `docs/tech_debt/active/2026-10-29-default-cap-lands-below-the-fitted-turns.md`
(6cb928b).

## The rule

- The floor is the smallest built-thread turn count over the fitted bolt points:
  `calc.thread.built_thread_length(thread_length, length) / pitch`, with each point's fields read
  through the parameter model so that defaults are filled.
- The fitted points are those of R11, from explore 40646117094 and spread 40646125666.
- `bench.oper_fit` computes the floor, and `emit-constants` emits it into `calc/cost.py`. It is
  never typed (L02).
- The bolt cap (`thread_length` first, then `length`, with the 07-12 guard that `length` is never
  capped below a named `thread_length`) only takes values whose built turns are at or above the
  floor.
- If no such value fits every artifact, the answer is B-02's `over_budget` 422, as for any part no
  cap can save.
- The nut `m` cap is unchanged: the nut has no turns feature, and G28 holds m/d at its low edge.

## Tasks

1. **Ruling and code, one commit:** `feat(calc): the default cap stops at the fewest turns the cost
   model was fitted on (07 B-03)`.
   - **Ruling record:** add a second B-03 clarification to
     `.planning/phases/07-operability-re-sweep/07-OWNER-RULINGS.md`, dated 2026-10-29, with the reply
     verbatim and the evidence above.
   - **Code:** emit the floor and apply it in `cap_defaults`.
   - **Tests:**
     - The emitted floor equals the one recomputed from the committed records.
     - `BoltParams(s=15)` with explicit {s} is not capped below the floor. Assert against the
       rule: either it is capped at or above the floor, or `cap_defaults` leaves it uncapped and
       the download gets the over_budget 422. Report which.
     - `BoltParams(d=5)` still caps to 16.5, and the d30 s48 k18 case to 6.5, if both are at or
       above the floor. If not, STOP and report.
   - **L21:** update its text in `docs/architecture/decision_log.md` to state the floor.
   - **Debt:** resolve the debt item in the same commit, then `git mv` it to `resolved/` and move
     its INDEX row.
   - **Regeneration:** regenerate `07-BUDGET-TABLE.md` and fit.json and cmp them with the committed
     copies. Any byte difference: STOP and do not commit.
2. **Quick records, docs commit:** `261029-rxk-SUMMARY.md` and a STATE "Quick Tasks Completed" row.

Done when: both commits are pushed, `make verify` has passed after the last one, and the table and
fit.json are byte-identical.
