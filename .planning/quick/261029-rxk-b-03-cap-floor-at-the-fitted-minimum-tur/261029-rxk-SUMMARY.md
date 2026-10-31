---
phase: quick-261029-rxk
plan: 01
status: complete
subsystem: calc / cost model
tags: [B-03, D-06, R11, L21, default-cap]
branch: gsd/phase-07-operability-re-sweep
plan_head_before: 97600d79e0d814672a6f775d2cd5f88b8fa0b07f
plan_head_after: 52dcf95
commits: 1
key-files:
  modified:
    - bench/oper_fit.py
    - src/screw/calc/cost.py
    - tests/test_cost.py
    - tests/test_cli.py
    - tests/test_parity.py
    - docs/architecture/decision_log.md
    - docs/tech_debt/INDEX.md
    - .planning/phases/07-operability-re-sweep/07-OWNER-RULINGS.md
  moved:
    - docs/tech_debt/active/2026-10-29-default-cap-lands-below-the-fitted-turns.md -> docs/tech_debt/resolved/
decisions:
  - "B-03 second clarification: the bolt cap takes no value below cost.MIN_FITTED_TURNS built turns, emitted from the fitted points; a part with nothing left keeps its over_budget 422"
---

# Quick 261029-rxk: the B-03 cap never goes below the fitted minimum turns

The default cap no longer cuts a bolt's thread below the fewest turns the cost model was fitted on.
`bench.oper_fit.min_turns` computes the floor from the committed records, and `emit-constants`
ships it as `cost.MIN_FITTED_TURNS = 2.9999999999999996`. That is 3 turns as `0.3 / 0.1` comes out
in floats: the n3 points at pitch 0.1 set it. fit.json and `07-BUDGET-TABLE.md` regenerate byte for
byte.

## Commits

| sha | Subject |
| --- | --- |
| 52dcf95 | feat(calc): the default cap stops at the fewest turns the cost model was fitted on (07 B-03) |

This SUMMARY and the STATE row land in their own docs commit after it.

## Outcomes against the plan

| Check | Result |
| --- | --- |
| Floor emitted, never typed | `MIN_FITTED_TURNS` sits inside the emit-constants block. `test_the_shipped_constants_are_the_block_emit_constants_writes_from_the_evidence` holds the block. `test_the_turns_floor_is_the_fewest_built_turns_over_the_fitted_bolt_points` recomputes it from the 1247 fitted bolt points without calling `min_turns`. |
| M6, only s=15 named | **Not capped.** No thread_length or length value at or above the floor fits every artifact. The preview download is the `over_budget` 422; the fine STL and STEP are served. At 97600d7 it was capped to thread_length 0.5. |
| d 5, only d named | Capped to 16.5, unchanged (16.5 turns) |
| d 30, s 48, k 18 | Capped to 6.5, unchanged (6.5 turns) |
| Catalogue rows and default parts | No artifact lost. They fit already, so the cap never runs on them (`test_a_part_admitted_at_every_artifact_is_never_capped_whatever_was_named`, `tests/test_presets.py`). |
| fit.json, 07-BUDGET-TABLE.md | `cmp` reports them identical before the change and after the commit |
| Nut m cap | Unchanged |

`test_the_cap_never_goes_below_the_turns_floor` checks the rule on an M6 with only s named, for s
from 12 to 15 in 0.5 steps. Each part is either capped at the largest admitted value at or above the
floor, or left uncapped with every grid value either below the floor or not fitting, and then its
preview is the API's `over_budget` 422. s 12, 12.5 and 13 are capped. s 13.5 to 15 are refused.

## Deviations from Plan

1. **[Rule 1 - test premise] `tests/test_cli.py::test_a_presets_fields_count_as_given_so_a_preset_is_never_capped`**
   used `--s 15` and asserted that the same values, left unnamed, would be capped. That no longer
   holds under the ruling, so the test now uses `--s 13`, which is still over its preview budget and
   still caps (thread_length 4.5, above the floor). The test's intent is unchanged: a preset's fields
   count as named.
2. **[Rule 1 - stale comment] `tests/test_parity.py`** said the M6 with s 15 is a capped case. None
   of that test's cases is capped now. The comment says so and points to `PARITY_CAPS` in
   `tests/test_cost.py`, which still checks API/CLI parity on three capped parts.
3. **Reading "through the parameter model".** Some fitted points are past today's L20 walls (the
   n240 points against the 90-turn cap), so `BoltParams.model_validate` refuses them. `min_turns` therefore fills
   omitted fields from `BoltParams.model_fields` defaults (`oper_fit._full`), the same way
   `features` and `head_bands` read the points. It does not validate them.

## Owner attention

- An explicit thread_length under 3 turns is still predicted by extrapolation. The user chose that
  part, and the ruling covers only the cap. The resolved debt item names 07-15's readings below 3
  turns as the remaining check.

## Self-Check: PASSED

- 52dcf95 is on HEAD. `MIN_FITTED_TURNS` is present in `src/screw/calc/cost.py`. The debt item is
  under `docs/tech_debt/resolved/`.
- `make verify` before the commit: `4469 passed in 211.94s`. The pre-commit hook re-ran it, and it
  passed.
