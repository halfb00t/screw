---
phase: quick-261031-o7u
plan: 01
status: complete
subsystem: cost model / merge gate / CI
tags: [code-review, cost-model, G38, L29, L28, L24, pr-land, ci]
branch: gsd/phase-07-operability-re-sweep
plan_head_before: 04d41384f2a590cc5372dcd220006ab874f53fa6
plan_head_after: 3febf4b840b96ade9775dd1cb21404d32cef3561
commits: 5
actuals:
  tasks: 5
  commits: 5
---

# Quick 261031-o7u: fix the phase 7 code review findings CR-01 and WR-01 to WR-04

The nut's `clearance` is now banded like G28's head ratios. Its band is (0.15, 5.0) mm, computed
from the fit records and emitted into `cost.BANDS`. The reviewer's 591 MB nut is refused at every
artifact, and nothing else moves. The merge gate now guards its own files. The drift record can no
longer fail `test (3.12)`. The budget-vs-limit gap is recorded and pinned. The `bench.export`
example now runs.

## Commits

| sha | Subject |
| --- | --- |
| f0c890e | fix(cost): band the nut clearance like the head ratios (G38, L29) |
| 7013c0d | fix(pr-land): guard the merge gate and the image pins (WR-02) |
| 7c4ac07 | fix(ci): keep the prediction-drift record from failing test (3.12) (WR-04) |
| 8ed48ee | docs(decisions): record that B-01's budgets are looser than their limits (WR-03) |
| 3febf4b | docs(bench): give the bench.export example the whole set label (WR-01) |

## CR-01 (blocker): fixed, no debt filed for it

- **Band.** `bench.oper_fit.head_bands` over the 1529 fitted points gives `("nut", "clearance"):
  (0.15, 5.0)`. It is emitted by `emit_constants` and is not typed. `oper_fit.MM_BANDS` and
  `cost.BANDED_IN_MM` mark it as banded in mm, not over d. A test holds the two equal.
- **Rule.** G28's one-sided rule: above the band, the max of raw and both edges; below it,
  max(raw, low edge). `cost._edges` and `oper_fit.edges` changed together, and the bit-for-bit
  parity tests still pass.
- **Reproducer.** `NutParams(d=163.65, pitch=21.743, s=387.26, m=1589.12, clearance=-30.32)` is
  refused at stl-preview, stl-fine and step. Under G28's bands alone it is admitted at stl-fine,
  and a test pins both facts.
- **Nothing moved** (each fact pinned in `tests/test_cost.py`):
  - 0 of the 294 bolt and 0 of the 14 nut catalogue rows change prediction at any artifact.
  - Both default parts are admitted everywhere.
  - In-band nuts predict as before, bit for bit.
  - `prediction-drift` shows 0 drift in every file.
  - `runtime.json` still equals `derive-runtime`.
  - `oper_fit table` writes the same bytes with and without the band.
- **Outband set.** `head_ratio_points` skips the clearance band, so `outband.json` does not move.
- **Records.** G38 is in `07-GAP-RULINGS.md` and `07-OWNER-RULINGS.md`. R11 of
  `07-SWEEP-PROTOCOL.md` is amended with no G label, no run id and the post-freeze sentence. The
  R11 sentence-count pin went from 3 to 4, and a new pin checks the text. L29 is logged, and L21
  carries a "Superseded in part by L29" note.

## WR-02, WR-04, WR-03, WR-01

- **WR-02.**
  - `GATE_PATHS` gains `Makefile`, `scripts/pr_land.py` and `tests/test_pr_land.py`.
  - `FULL_TIER_PATHS` and the operability.yml `paths:` gain `Dockerfile` and `requirements.txt`.
  - The derivation test and both paths pins are updated. L28 is updated in place, including PR
    #26: it touches `Dockerfile`, `Makefile` and `scripts/pr_land.py`.
- **WR-04.** The ci.yml `prediction-drift` step has `continue-on-error: true`, pinned by
  `tests/test_oper.py`.
- **WR-03.** A note on L24 gives the figures from code:
  - Seconds budgets 34.13 and 94.43 s against the 26 and 71 s timeouts.
  - Fine peak budget 2,930,457,561 B against a 1,830,617,088 B headroom (`mem_limit` less B,
    the export cache and the tmpfs).
  - The timeout is the backstop: a 503, `cost_model.miss`, nothing cached.
  - `tests/test_runtime_bounds.py` pins which budget is above which limit.
- **WR-01.** All four places use `SET="d=100 length=90 s=200 k=50 thread_length=90"`. A test
  resolves every documented label through `find_set`.

## Deviations from Plan

- **[Rule 2, owner question] The reviewer's second nut.**
  - The nut is `d=92.28 pitch=31.418 s=130.54 m=967.04 clearance=-21.12`. It stays admitted at
    stl-fine under the band rule.
  - Measured with `solid.export` on macOS arm64: 121,632,684 B at -21.12 and 223,951,384 B at
    0.15. At 0.15 that is 2.93 x its enveloped prediction of 76,540,259 B.
  - So the clearance assumption holds on this pair. The nut misses its envelope inside the band
    for another reason (m/d 10.5, coarse pitch; the cause is not measured).
  - Both readings are under the 239,508,059-byte budget.
  - Filed as must: `docs/tech_debt/active/2026-10-31-tall-nut-misses-its-envelope-inside-the-clearance-band.md`.
    It is recorded in G38 and put to the owner, who may raise it to blocker.
- **[Rule 3] Test pins.** These moved with the rule: the R11 post-freeze sentence count, the
  operability.yml `paths:` pin in `tests/test_oper.py`, and `test_oper_fit`'s band fixture.

## Verify

`make verify`: ruff and mypy clean, `Contracts: 10 kept, 0 broken.`, `4827 passed in 188.87s`.
`python -m bench.oper_sets prediction-drift`: 0 differing values in every file.

## Self-Check: PASSED

All five commits are on HEAD's history. The debt item, PLAN.md and this file exist.
