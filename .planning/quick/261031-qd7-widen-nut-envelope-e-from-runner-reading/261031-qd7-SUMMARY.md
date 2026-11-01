---
phase: quick-261031-qd7
plan: 01
status: complete
subsystem: cost model / runner records
tags: [cost-model, G39, G40, G41, L30, L31, L32, envelope, memory]
branch: gsd/phase-07-operability-re-sweep
plan_head_before: 3b3b8f0a833c9a57fd04d2f385abe42c65fa591c
plan_head_after: 4282ef622d0b35d85cc943663f5b125fffa87f4b
commits: 5
actuals:
  tokens: 51506
  tasks: 3
  commits: 5
---

# Quick 261031-qd7: the tall nut the clearance band left open (G39, G40, G41)

The tall-nut debt rested on a wrong 2.93 x. The real defect was the edge rule, so a fix is in. The
runner read tall nuts and d-only M2 and M3. It widened two nut seconds e and caught an admitted nut
whose fine-STL peak would pass `mem_limit`. The nut's fine-STL peak budget is now capped at the
worker's headroom.

## Commits

| sha | Subject |
| --- | --- |
| e65ff6c | fix(cost): price a nut's clearance edges with its other fields real (G39, L30) |
| ab72cf8 | feat(bench): write the tall-nut and d-only bolt out-of-band set (G39) |
| 912e1ca | fix(test): hold the G39 pins to what holds on the linux runner |
| b5cc6f9 | feat(calc): widen the nut preview and STEP seconds e from outband-tall run 41206999278 (L31, G41) |
| 4282ef6 | fix(cost): cap the nut's fine-STL peak budget at the worker's memory headroom (G40, L32) |

## Owner rulings (recorded verbatim in 07-GAP-RULINGS.md and 07-OWNER-RULINGS.md)

- **G39, in order.**
  1. "Runner readings, widen e (Recommended)", given on the wrong 2.93 x premise: it divided the
     clearance-0.15 nut's bytes by the clearance -21.12 nut's envelope.
  2. "C: fix rule, then runner (Recommended)", superseded: it would refuse d-only bolt links M2 to
     M4 and undo part of G28 ruling 5.
  3. "F: clearance only (Recommended)", final.
- **G40, in order.**
  1. "1: budget peak to headroom (Recommended)", stopped by its own catalogue check: on every
     artifact it refuses the fine STL of 110 bolt rows and 33 d-only bolt links.
  2. "1: nut stl-fine only (Recommended)", final.
  3. "Keep cap, file must debt (Recommended)".
- **G41.** "1: regenerate the files (Recommended)".

## What changed

- **G39 rule (L30).** `cost._edges` and `oper_fit.edges` also price each clearance edge with every
  other field at its real value, when another field is out of band too. All three reviewer nuts are
  refused at stl-fine: m 967.04 at 0.15, and m 967.04 and m 2764.2 at -21.12. The last wrote
  364,438,484 B on macOS, past tmpfs. Nothing else moved: no catalogue row, default part,
  single-out-of-band part or d-only link (160), and no set.
- **Runner set (G39).** `bench/points/outband-tall.json` (`python -m bench.oper_sets
  outband-tall`): 27 points at 5 repetitions. Run 41206999278 gave 135 readings, all ok. The largest
  cold wall is 36.568 s of 71 s, and the largest fine STL 142,657,184 B, under tmpfs. d-only M2/M3
  read at most 0.5992 of their envelope.
- **Widening (L31, G41).** Both e are set by `tall-nut-x1-m5d` rep 1:

  | e | before | after |
  | --- | --- | --- |
  | nut stl-preview seconds | 1.061383246630594 | 1.0971665633647603 |
  | nut step seconds | 0.8785228687431521 | 1.0534097750071423 |

  `full.json`, `oper_boundary.json` and `dense-band.json` were drawn again by their own commands:
  80 limits loosened by at most 9.31 %. No admission moved.
- **Cap (L32, G40).** `cost.budget` caps the nut's stl-fine peak at `WORKER_HEADROOM_BYTES` =
  1,830,617,088 B. That is runtime.json's `mem_limit` less B, the export cache and the tmpfs, emitted
  by `emit-constants --runtime`. The tall nut m 461.4 read up to 2,040,320,000 B; with the rest that
  is 2,625,622,016 B, past the 2,415,919,104 B limit. It is now refused at stl-fine. No row, default
  or d-only link moved. `runtime.json` moves only R21's candidate count (394 to 390).

## Deviations from Plan

- **[Rule 4, stopped four times]** The 2.93 x premise, rule C's d-only refusals, the memory reading
  and the gate-file drift each went back to the owner, and each answer is recorded.
- **[Rule 1] CI 41207004836, test (3.12) red.**
  - My budget-table pin compared committed bytes, which the linux fit does not reproduce (G33). It
    now compares G39's table with G38's on the same host.
  - The cap parity test collided with `tests/test_api.py` in the shared byte cache. It now uses its
    own cache.
  - Fixed in 912e1ca.
- **[Correction] G40 ruling 3's premise.** The d 30 clearance-5 grid nuts the question named (the
  71 s timeout's bound point and W's drift part) are past the nut's d / pitch wall of 8. No request
  reaches them. The one production nut the cap refuses although it was read under the headroom is
  `tall-nut-x0.5-m10.5d`: 0.8102 read, 1.0116 enveloped. The must debt carries it, and L32 and G40
  say so.

## Debt

- **Resolved (blocker):** `docs/tech_debt/resolved/2026-10-31-tall-nut-misses-its-envelope-inside-the-clearance-band.md`.
- **Filed (must):**
  - `docs/tech_debt/active/2026-10-31-head-ratio-edges-never-meet-a-real-out-of-band-ratio.md`
    (1.0024 x; M2/M3 runner readings show no miss).
  - `docs/tech_debt/active/2026-10-31-bolt-fine-peak-budget-above-the-worker-headroom.md`
    (runs 41155746591 and 41161227951, 0.4941 of the headroom).
  - `docs/tech_debt/active/2026-10-31-nut-peak-envelope-refuses-parts-read-under-the-headroom.md`.

## Verify

- `make verify`: the pre-commit hook passed on every commit (at 912e1ca: 5150 passed).
- `python -m bench.oper_sets --check` exits 0, and `prediction-drift` is 0 in every file.
- On 4282ef6, CI 41216519008 and the operability full tier 41216519010 both passed.

## Self-Check: PASSED

All five commits are on HEAD's history. PLAN.md, the set file, the records folder and the four debt
items exist.
