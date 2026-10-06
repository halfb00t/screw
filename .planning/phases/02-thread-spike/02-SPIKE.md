# Phase 2: Thread spike — protocol

This file is pre-registered: everything above the `## Results` heading lands on `main` in PR 1 before run 1 (D-16, D-19), and the run guard refuses any run while that text differs from `origin/main`'s.

## Question

**Construction.** Which helical construction do we build? The sewn twist-section is the research favourite; one-pipe twist and the `cq_warehouse` ruled surface are reference rows, and the naive `sweep` + `fuse` is the negative control. The answer includes the failure frontier: for each size, the turn count and length at which each construction first fails or goes silently wrong (D-04, D-06, D-09).

**Mesh budget.** What does a fine mesh of a threaded rod and a threaded void cost? Triangles, build and mesh seconds, peak RSS, STL bytes and the gzip ratio, per size, against the INTERIM 30 s and 64 MB budgets (D-10, D-20).

**Pair-check falsifiability.** Can a kernel pair check be made falsifiable? A nut void against a rod at the screw-motion matched poses must read empty, and the half-pitch-offset controls must read non-empty within a band of the closed-form estimate. A check that cannot fail proves nothing (D-11, D-12, D-14).

**Volume estimator.** Which volume estimator agrees with the closed form across the grid: `BRepGProp.VolumeProperties_s` or the STL's signed tetrahedron volume? The default `Volume()` is already known to be 15 to 21 % off on some constructions (D-20).

## Owner rulings (D-01 checkpoint, 2026-10-06)

- **Profile pin: `basic`.** ISO 68-1:2023 basic profile, flat crest and flat root. Every measured row builds this section. Read by the owner on **2026-10-06**. One-way door: a later profile change re-runs the whole campaign (D-01). The design (rounded-root) profile stays a deferred option.
- **Coefficients, owner-confirmed.** The owner read the standard and offered no correction; the values below stand as presented at the checkpoint. No clause text is copied here.
  - H = (sqrt(3)/2) * P
  - crest flat P/8, at radius d/2
  - root flat P/4, at radius d/2 - 5H/8
  - flanks at 60 degrees
  - Downstream: plan 02-02 codes `section_radius` and `section_area` from these values.
- **R0: not applicable.** Basic is pinned, so rod and void share one section and one builder (the nut-void section question only exists for the design profile).
- **R1: planner default.** The pair verdict stays exactly D-12/D-14: all 3 matched poses empty AND all 3 half-pitch controls non-empty within the band. Variant rules (2 of 3 controls; the same-pose c = -0.05 reading as the control; seam pose excluded) are computed from the same readings and reported beside the verdict, never changing it. D-14 is not amended. Downstream: plan 02-05 pair rules.
- **R2: planner default.** D-03's lower length bound is min(P, 1 mm), keeping sub-turn rows such as M8 L = 1 mm = 0.8 turn: 1790 lengths per hand. Downstream: plan 02-03 grid counts.
- **R3: planner default.** `bench/RESULTS.md` carries each run's header, host state, time-labelled load readings, per-size aggregates and every non-ok or over-budget row verbatim. The raw per-row JSONL and the run's Markdown are committed under `bench/results/thread-spike/`, with the JSONL sha256 in `bench/RESULTS.md`. This narrows D-16's "verbatim". Downstream: plans 02-03 and 02-07 record layout.
- **R4: planner default.** A non-decisive run's validity, solid-count, volume and pair outcomes count. Its timing-derived claims (the 30 s frontier stop, a seconds-based cap) are reported as not established and never re-run toward a pass (D-17). The owner runs the timing-critical campaign detached, with every agent session closed. Downstream: plans 02-03, 02-07 and 02-08.
- **R5: planner default.** Nut heights m in mm, each with its source label kept verbatim from the checkpoint. Downstream: plan 02-05 `NUT_HEIGHT`. m only scales the engaged length and the closed-form expectation together; it is a label, not a verdict input.
  - M5 4.70, M6 5.20, M8 6.80, M10 8.40, M12 10.80, M16 14.80, M20 18.00: m max as read from the ISO 4032:2023 preview by the research. UNVERIFIED (the owner did not re-read them from the standard).
  - M14 12.80 and M18 15.80: memory of the same table, not re-read. UNVERIFIED.
  - M7 5.60: ISO 4032:2023 added M7 but no value was read by anyone and the owner supplied none, so this is 0.8 * d as a stated input. UNVERIFIED.
  - M2 1.60, M2.5 2.00, M3 2.40, M4 3.20: Annex A not read; memory of the withdrawn ISO 4032:2012. UNVERIFIED.
  - M3.5 2.80: 0.8 * d, no ISO 4032 row. UNVERIFIED.
- **Pre-registered values: no objection raised, they stand.** Planner-set under D-07, D-20 and CONTEXT "Claude's Discretion", not owner-supplied: T_PASS 1e-4 relative; pair band 1e-3 relative; empty threshold 1e-6 mm3; row timeout 120 s, pair cell 600 s; matched poses theta = -2pi/3, 0, 2pi/3 (the seam pose included, because excluding it would be a pose picked after seeing probe data); grid void clearance 0.20 mm; tip-chamfer cone 30 degrees from the end face from the minor radius (ISO 4753 unread, UNVERIFIED); sewing tolerance 1e-4; K rule: fewest fine triangles, then STEP bytes, then smaller K.

Transparency note (T-02-01): before the owner ruled, the orchestrator recommended `basic, defaults`, with these reasons: the four spike questions do not depend on root shape; basic is the only profile with evidence (closed form within 7.6e-6 on 576 of 576 research rows); design adds an unmeasured root radius, a numeric integral and R0 before any row exists; amending D-14 before run 1 would tune the verdict toward a pass; m is a label, not a verdict input. The owner then ruled in two messages, quoted verbatim:

> basic, defaults
>
> today

The second message answered the question "the date you read ISO 68-1:2023 (today is 2026-10-06) — reply `today` or a date".

## Results

No run yet.
