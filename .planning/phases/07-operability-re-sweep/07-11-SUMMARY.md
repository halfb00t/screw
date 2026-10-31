---
phase: 07-operability-re-sweep
plan: 11
subsystem: calc
tags: [cost-model, OPER-03, D-05, D-06, D-07, D-08, D-17, B-01, B-02, L21]
status: complete

requires:
  - phase: 07-operability-re-sweep
    provides: "07-02: calc/cost.py Artifact, ARTIFACTS, artifact_of"
  - phase: 07-operability-re-sweep
    provides: "07-09: bench/oper_fit.py and bench/results/phase-07/fit.json (runs 40646117094, 40646125666)"
  - phase: 07-operability-re-sweep
    provides: "07-10: 07-OWNER-RULINGS.md B-01 C1, B-02 over_budget"
provides:
  - "src/screw/calc/cost.py: FEATURES, FIELDS, TARGETS, COEFFICIENTS, ENVELOPE, BUDGET, Cost, predict, admitted, fits, refusal"
  - "bench/oper_fit.py: emit-constants, ruled_budget, emit_constants"
  - "download_refusal delegates to cost.refusal for both kinds and every artifact"
  - "app._serve: the B-02 422 (type over_budget, ctx.fields, ctx.artifact)"
affects: [07-12, 07-13, 07-14, 07-15, 07-16]

tech-stack:
  added: []
  patterns:
    - "Constants generated from evidence: a BEGIN/END emit-constants block in cost.py, and a test that regenerates it from fit.json and the rulings and finds it verbatim"
    - "Widening-safe pins: refused parts are B-01-refused explore points; any other outcome is asserted as equality with cost.refusal"

key-files:
  created:
    - .planning/phases/07-operability-re-sweep/07-11-SUMMARY.md
    - docs/tech_debt/active/2026-10-29-cost-model-admits-out-of-fit-head-heights.md
  modified:
    - src/screw/calc/cost.py
    - src/screw/calc/__init__.py
    - src/screw/app.py
    - bench/oper_fit.py
    - tests/test_cost.py
    - tests/test_calc.py
    - tests/test_api.py
    - tests/test_cli.py
    - tests/test_presets.py
    - tests/test_parity.py
    - docs/tech_debt/INDEX.md

key-decisions:
  - "Owner ruling 2026-10-29 on the 07-11 checkpoint, verbatim: \"A: preset + overrides (Recommended)\". The preset export test is iso4017:M20x70 with --pitch 1, which cost.refusal refuses"
  - "The refusal text says the part is predicted over its measured budget and prints no figure (L02)"
  - "An unvalidated part whose prediction overflows exp predicts infinity and is refused, never an OverflowError"

requirements-completed: []   # OPER-03 advances; the default cap (07-12) and the tiers (07-15) remain

actuals:
  tokens: 23187       # chars/4 over `git diff 0e89eaf..9dab2d1` (92749 chars)
  tasks: 3
  commits: 4
plan_head_before: 0e89eafaa45d061ce397cbeb78b2eba7510ac43d
plan_head_after: 9dab2d17b7c02f18a5648920fffdcafa7c68db15

metrics:
  duration: "about 64 min (from 08:16 +0600 HEAD to 09:20 +0600, checkpoint round trip included)"
  completed: 2026-10-29
---

# Phase 7 Plan 11: the cost model judges every download Summary

**The fitted, enveloped, kernel-free predictor is now the only download rule.** It judges each
artifact of the bolt and the nut against B-01's C1 budgets through the shared `download_refusal`.
The 422 is B-02's single `over_budget` type, with `ctx.fields` and `ctx.artifact`.

## What shipped

- `calc/cost.py`:
  - `predict(p, artifact) -> Cost` is the fit's own sum, in the same order as
    `bench.oper_fit.predict`. It uses `math.log` and `math.exp` only.
  - `admitted(pred, e, budget)` implements R12. A part at the budget is admitted and one float
    above is refused. A None component means unbounded.
  - `fits` checks every target of one artifact.
  - `refusal(p, artifact)` builds the text. It starts with the kind's cost fields in model order:
    `d, pitch, length, s, k and thread_length: ` for the bolt, `d, pitch, s, m and clearance: `
    for the nut. It names the artifact and L21 and says which other artifacts fit. Its only
    digits are those of L21.
- `COEFFICIENTS`, `ENVELOPE` and `BUDGET` sit between the `emit-constants` markers. They are
  `python -m bench.oper_fit emit-constants --fit bench/results/phase-07/fit.json --rulings
  .planning/phases/07-operability-re-sweep/07-OWNER-RULINGS.md` verbatim. The block's comments
  name the runs and B-01 with its date. A later `widened_by` list in fit.json would print one
  "Widened by run" line per run (R12).
- `tests/test_cost.py` checks the evidence three ways. It finds the regenerated block verbatim in
  cost.py. It holds the constants equal to fit.json's models and to B-01's table. It recomputes C1
  from fit.json and the catalogue and gets B-01's three triples bit for bit.
- `download_refusal` raises TypeError for a kind with no model, and otherwise returns
  `cost.refusal(p, artifact_of(fmt, quality))`. `calc/__init__.py` no longer imports
  `fine_stl_refusal` or `nut_fine_stl_refusal`; plan 07-13 retires them from `calc.thread`.
- `_serve` answers a refused download with `{"loc": ["query"], "type": "over_budget", "msg":
  <refusal>, "ctx": {"fields": FIELDS[kind], "artifact": <artifact>}}`. `fine_stl_cap` no longer
  appears in `app.py`.

## Evidence for the plan's edges

- **Empty edge.** The all-default bolt and nut fit every artifact, and `download_refusal` returns
  None for all four download pairs.
- **Adjacency edge.** `admitted` is true at each B-01 component and false at the next float above
  it. With every shipped envelope, it is also false one float under the enveloped figure.
- **Ordering edge.** Over every in-wall explore point, each refusal appears once in `warnings`, in
  `_DOWNLOADS` order. The STEP pair gives a single sentence.
- **Parity.** `tests/test_parity.py::test_every_front_end_refuses_the_same_downloads_with_the_same_words`
  covers the info document (CLI and API), the model route and `screw export`. For two B-01-refused
  parts and two off-row parts, the four download pairs agree everywhere, the 422 body equals the
  B-02 shape exactly, and a refused request makes no backend call.
- **Refused presets.** Under C1 the shipped rule refuses 0 of the 294 bolt catalogue rows, at any
  download. That count is pinned with a comment citing L21 and B-01, and the old `== 62` is gone.

## Deviations from Plan

### Owner ruling

**1. The preset export test no longer refuses a catalogue row.**
- **Found during:** Task 1, before any edit.
- **Issue:** The plan said "the preset export test refuses a row the model refuses". Under B-01
  (C1) the model refuses no catalogue row: 294/0 and 14/0 at every artifact, which I recomputed
  from fit.json. The test could not be written as specified, so I stopped with a checkpoint.
- **Ruling (owner, 2026-10-29), reply verbatim:** "A: preset + overrides (Recommended)".
- **Fix:** `tests/test_presets.py::test_an_export_of_a_preset_the_model_refuses_exits_2_and_writes_nothing`
  exports `--preset iso4017:M20x70 --pitch 1`, which is 70 turns of a 20 mm thread. The test
  asserts that `cost.refusal` refuses this part at stl-fine. It then checks exit 2, stderr equal
  to `error: <that text>`, `L21` in the text, and that no file was written. I picked the override
  with committed code (`cost.refusal` on fit.json's constants). The catalogue's largest d is 20.
  At pitch 1, M20 x 60 is admitted at stl-fine and M20 x 70 is the first M20 length refused.
  At pitch 1, M20 x 100 has 100 turns and is refused by the 90-turn wall. `tests/test_parity.py`'s
  former M8 x 70 test uses the same part.
- **Commit:** 5ed154a

### Auto-fixed issues

**2. [Rule 1 - Bug] An unvalidated part overflowed `math.exp`.**
- **Found during:** Task 1.
- **Issue:** `derive` on `BoltParams.model_construct(d=1e200, ...)` raised OverflowError inside
  `predict`. The existing tests pin that `derive` returns a document for such a part.
- **Fix:** A log-sum at or past `ln(sys.float_info.max)` predicts `math.inf`, which is refused.
  No figure is printed either way. Tested.
- **Files modified:** src/screw/calc/cost.py, tests/test_cost.py
- **Commit:** 5ed154a

**3. [Rule 1 - Test] The kernel-gate API test was being answered by the model.**
- **Found during:** Task 2.
- **Issue:** `test_a_solid_the_kernel_gets_wrong_is_a_422_build_error` asks for the preview STL of
  d 0.03 mm with the default 10 mm head. That part is far outside the fit, and the model refuses
  its preview, so the test stopped reaching the volume gate.
- **Fix:** The test switches `app.download_refusal` off with monkeypatch, so the gate answers
  whatever the model says. This adds no pin on the model's outcome.
- **Commit:** 6cb9080

**4. More old-rule pins than the plan listed.**
- **Found during:** Task 1.
- **What moved:**
  - `tests/test_api.py`: the M8 x 70 document test, the at-cap and off-row test, and the left-hand
    test.
  - `tests/test_parity.py`: the download-label test. It now marks the all-default document's fine
    STL refused, so rule 17 is read without pinning another part's outcome.
  - `tests/test_presets.py`: the preview-fallback test.
  - `tests/test_calc.py`: the warning-order tests of parts the old rule refused, and the
    measured-range test, which now uses the refused d 100 nut.
- **How:** Each follows the widening rule. Refused parts are the B-01-refused explore points
  `bolt-d30-p1-n30-right` (and its left twin) and `nut-d100-p1-m0.8d-s1.6d-c5-right`. Every other
  outcome is asserted as equality with the shared rule. Tests that built a refused part's other
  artifacts with the kernel now use a stubbed builder: the rule is under test, and a d 30 build
  costs seconds.
- **Commits:** 5ed154a, 6cb9080

## Known Stubs

None.

## Threat Flags

None new. T-07-28 (an over-budget part reaching the pool) is mitigated as planned, with one gap
filed below.

## Needs the owner

**The cost model admits out-of-fit head heights.** Filed as must:
`docs/tech_debt/active/2026-10-29-cost-model-admits-out-of-fit-head-heights.md`.

- The bolt's `ln_k` coefficients are negative on every artifact in fit.json. The explore points
  fit k only between 0.5 and about 0.69 of d.
- So `bolt-d100-p1-n30-right` is refused at all three artifacts with k 60, but admitted at all
  three with k 100000 (`MAX_BOLT_K_MM`). These outcomes come from `cost.fits` at ed55679.
- This is no regression: the old rule refused nothing off its measured rows.
- The per-build timeout remains the only bound for this direction, and plan 07-15's tiers would
  not reach it, because its bound sets are drawn from explore points.
- Any fix changes R11 or L20, so it needs a ruling (R30). The options are: (a) clamp features to
  the fitted band, (b) add a k/d and s/d wall, (c) accept it and leave it to the timeouts.
- I recommend ruling before plan 07-14 draws the bound set.

A milder, consistent oddity: ISO 4017 M20 x 60 at pitch 1 is admitted at stl-fine and refused at
stl-preview. Each artifact has its own C1 budget and envelope.

## Self-Check: PASSED

- src/screw/calc/cost.py, tests/test_cost.py and the debt item exist.
- 5ed154a, 6cb9080, ed55679 and 9dab2d1 are ancestors of HEAD.
- Acceptance greps:
  - cost.py imports no cadquery, OCP, numpy, logging or records (0 matches).
  - The emit-constants block is found verbatim in cost.py.
  - `== 62` is gone from tests/test_presets.py (0 matches).
  - `fine_stl_refusal` and `nut_fine_stl_refusal` are gone from calc/__init__.py (0 matches).
  - `"fine_stl_cap"` is gone from app.py (0 matches).
- The three task commit subjects match the plan.
