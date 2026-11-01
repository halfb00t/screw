---
phase: quick-261029-mik
plan: 01
status: complete
subsystem: calc / cost model
tags: [G28, R11, cost-model, head-ratio]
branch: gsd/phase-07-operability-re-sweep
plan_head_before: d869b87
plan_head_after: 09daea1
commits: 5
---

# Quick 261029-mik: G28, out-of-band head ratios are judged against their fitted band

The fit saw each head ratio only in a narrow band. Below that band a part is now predicted no lower
than at the band's low edge, and above it no lower than anywhere in the band. The bands are generated
from the committed records into `cost.BANDS`. The budget table and fit.json are byte-identical, and
both bypass cases are refused at every artifact.

## Commits

| sha | Subject |
| --- | --- |
| 070ff13 | docs(07): record the owner's ruling G28 and bound the head ratios the cost model was not fitted on |
| 5f4cdb7 | docs(07): take only the low band edge for a head ratio below its band (07 G28, ruling 5) |
| bc7b2ab | feat(calc): predict an out-of-band head ratio no lower than anywhere in its band (07 G28) |
| f6729f2 | docs(07): name the at-the-walls part among G28's 22 gate failures |
| 09daea1 | docs(07): carry G28 into 07-12 and 07-15 and update the head-ratio item |

This SUMMARY and the STATE row land in their own docs commit after these.

## The rule as shipped (rulings 1, 2, 4, 5)

The bands come from `python -m bench.oper_fit emit-constants --fit ... --rulings ... --explore ...
--spread ...`. Each is the [min, max] over the R11 fitted points, with omitted fields at their
defaults:

| ratio | band |
| --- | --- |
| bolt k/d | (0.6, 0.7) |
| bolt s/d | (1.5, 2.0) |
| nut s/d | (1.5, 4.0) |
| nut m/d | (0.7999999999999999, 3.0) |

A part with any ratio outside its band is predicted, target by target, as the largest of the raw
prediction and the predictions at every combination of edges of its out-of-band ratios:
- above its band, both edges;
- below its band, the low edge only.

Inside every band the prediction is the raw fit, bit for bit. `cost.predict` and
`bench.oper_fit.predict` agree exactly (`==` in `tests/test_cost.py`).

## Evidence

- The regenerated `07-BUDGET-TABLE.md` and fit.json `cmp` byte-identical with the committed copies
  at bc7b2ab.
- Every catalogue row (294 bolt, 14 nut) and both default parts lie inside every band.
- Outcomes (preview / fine STL / STEP):

| part | d869b87 | bc7b2ab |
| --- | --- | --- |
| bolt d100 p1 L30 t30 s200 k1000 | admitted / admitted / admitted | refused / refused / refused |
| nut d30 p0.35 m24 c0.15 s999 | admitted / refused / admitted | refused / refused / refused |
| bolt d-only M8 | admitted / admitted / admitted | admitted / admitted / admitted |
| bolt d-only M5 | admitted / admitted / admitted | refused / admitted / admitted (OK'd by ruling 5) |

## Stops and the owner's rulings

1. Under the nearest-edge rule, bolt k 1000 stayed admitted at STEP and nut s 999 at the preview.
   Ruling 4: "B: max over the band (Recommended)".
2. Under rule B, the pre-commit gate gave `22 failed, 4409 passed`, each `assert 422 == 200`. 21 of
   them are d-only bolt previews; the 22nd is the at-the-walls part. Ruling 5: "2: one-sided B
   (Recommended)".

## Deviations

- **Extra commits (on the coordinator's instruction).** 5f4cdb7 is a follow-up to 070ff13, not an
  amend. f6729f2 corrects G28's account of the 22 failures: I had first reported all 22 as d-only.
- **[Rule 1] `tests/test_api.py::test_a_part_at_the_walls_...` re-pinned in bc7b2ab.** The part is
  d 999.999, s 1000, k 1e5, length 1e4, so k/d is 100. The model route served it only because that
  k/d made its raw prediction cheap, which is the bypass itself. The test, now
  `..._is_taken_and_judged_by_the_cost_model_and_one_past_is_not`, asserts:
  - the walls take the part and `/api/bolt/info` answers 200;
  - the preview answers as `download_refusal` rules, an `over_budget` 422;
  - one past the length wall is still the `length` 422.
  No decision pins "served". The test came from 07-07 (a804806), before the cost model existed.
- **`emit-constants` now requires `--explore` and `--spread`,** because the bands come from the
  records, not from fit.json. 07-15's command was updated to match.
- **07-15's out-of-band point choice is mine, written into the plan.** For each ratio, side and
  artifact, the point is the first catalogue row in file order whose field, one 0.1 mm form step past
  the edge, the rule admits. A far point at 10x the high edge is added where admitted; it exists for
  bolt k and nut s only. Each point is charged as an explore-like part (R6, G4). The owner may want
  to review this choice.

## Verification

- The `make verify` pre-commit hook passed on every commit listed.
- `tests/test_cost.py` and `tests/test_oper_fit.py`: 72 passed at bc7b2ab.

## Debt

Updated, still active: `docs/tech_debt/active/2026-10-29-cost-model-admits-out-of-fit-head-heights.md`.
It corrects the band to 0.6 to 0.7, adds the nut s evidence and records the guard at bc7b2ab. The
trigger is 07-15's out-of-band readings. No new item was filed.
