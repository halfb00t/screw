---
phase: 07-operability-re-sweep
plan: 12
subsystem: calc
tags: [cost-model, OPER-03, D-06, B-03, L21, default-cap]
status: complete

requires:
  - phase: 07-operability-re-sweep
    provides: "07-11: calc/cost.py predict, fits, refusal, BUDGET; download_refusal on the cost model; the B-02 422"
  - phase: 07-operability-re-sweep
    provides: "quick 261029-mik (G28): cost.BANDS and the one-sided band rule in predict"
  - phase: 07-operability-re-sweep
    provides: "07-OWNER-RULINGS.md B-01 C1, B-02 over_budget, B-03 part-wide and its 2026-10-29 clarification"
provides:
  - "src/screw/calc/cost.py: CAP_STEPS, fits_every_artifact, cap_defaults(p, explicit)"
  - "src/screw/calc/__init__.py: derive_capped(p, explicit)"
  - "src/screw/app.py: explicit_fields(request, kind); info and model routes serve the capped part"
  - "src/screw/cli.py: _params returns (part, explicit); screw info and screw export serve the capped part"
  - "docs/architecture/decision_log.md: L21, and pointer lines under L12, L13, L16"
affects: [07-13, 07-14, 07-15, 07-16]

tech-stack:
  added: []
  patterns:
    - "Request-boundary cap: the explicit set is the raw query keys (API) or given flags plus preset fields (CLI); the model never guesses which fields were named"
    - "Cap tests assert the rule (largest admitted form-step value, nothing between it and the default admits), not a typed value, so an R12 widening cannot silently stale them"

key-files:
  created:
    - .planning/phases/07-operability-re-sweep/07-12-SUMMARY.md
    - docs/tech_debt/active/2026-10-29-default-cap-lands-below-the-fitted-turns.md
  modified:
    - .planning/phases/07-operability-re-sweep/07-OWNER-RULINGS.md
    - src/screw/calc/cost.py
    - src/screw/calc/__init__.py
    - src/screw/app.py
    - src/screw/cli.py
    - tests/test_cost.py
    - tests/test_api.py
    - tests/test_cli.py
    - tests/test_parity.py
    - docs/architecture/decision_log.md
    - docs/architecture/overview.md
    - docs/tech_debt/INDEX.md

key-decisions:
  - "B-03 clarification (owner, 2026-10-29): each unnamed field is capped on its own, thread_length then length (or the nut's m); length is never capped below a named thread_length"
  - "B-03 clarification (owner, 2026-10-29): a d-only M5 is served with its defaulted thread_length capped (16.5 mm), not refused at the preview"
  - "A field not at its frozen default counts as named on direct Python construction, so cap_defaults never moves a chosen value even without an explicit set"
  - "The cap warning comes before the standing ends-modelled entry in warnings (the plan's 'first'); the parity test was re-pinned to that order"

metrics:
  duration: "about 85 minutes"
  completed: 2026-10-29

estimate:
  tokens: 110000
  tasks: 3
actuals:
  tokens: 14954
  tasks: 3
  commits: 5
plan_head_before: bf7b173aae61938773b01ab64172e9d32ae17dde
plan_head_after: 6cb928bc50b1175953ceb40f33ef1b336742fa18
---

# Phase 7 Plan 12: The default cap (B-03) and L21 Summary

A link that leaves a bolt's thread_length or length, or a nut's m, at its default now gets that one
field cut to the largest form-step value at which every artifact fits, plus a warning. Before this
change such a link got a 422. A field the request named is never moved, and `length` is never cut
below a named `thread_length`. The API and the CLI serve the same capped part, warning and file
name. L21 records the cost model, the budget, the 422 and the cap.

## Commits

| # | Hash | Subject |
|---|------|---------|
| 0 | a500356 | docs(07): record the B-03 clarification on a named thread_length and the length cap |
| 1 | c850726 | feat(calc): cap a defaulted length that pushes a part over its budget, and warn (07 D-06, B-03) |
| 2 | dc4b7fd | feat(cli): the default cap on the CLI and for the nut, with API parity (07 D-06, B-03) |
| 3 | 94aa461 | docs(07): log the cost model, the budget and the default cap as L21 |
| - | 6cb928b | docs(07): file the default cap landing below the fitted turn counts as debt |

## What was built

- **`cost.cap_defaults(p, explicit)`** (B-03, part-wide):
  - Returns `(p, ())` when every artifact already fits.
  - Otherwise tries each field the request did not name, in the order `CAP_STEPS` gives: bolt
    `thread_length`, then `length` (0.5 mm steps), or nut `m` (0.1 mm step). It scans down from
    the frozen default, validates each candidate with the model, and takes the first value at which
    every artifact fits.
  - `length` stops at a named `thread_length` (clarification ruling 1).
  - It returns one warning that names the field, the default, the capped value, the step and L21,
    and no predicted figure (L02).
  - A part no cap admits keeps its per-artifact `over_budget` 422.
- **`calc.derive_capped`** caps the part, derives its info document and puts the cap warning first.
- **API:**
  - `explicit_fields(request, kind)` is the set of raw query keys that are model fields.
  - `/api/{kind}/info` calls `derive_capped`.
  - `/api/{kind}/model.{fmt}` caps the part before `_serve`, so the bytes and the
    Content-Disposition name come from the capped part.
- **CLI:**
  - `_params` returns the explicit set: the given flags plus a preset's fields.
  - `screw info` and `screw export` call `derive_capped`.
  - `screw pair` is never capped, because the proof has no budget.
- **L21** covers the fit and its run ids (explore 40646117094, spread 40646125666), G28's bands and
  their one-sided rule, the envelope table, the B-01, B-02 and B-03 replies quoted, the cap rule with
  its clarification, the refused-preset count of 0 and its test, the retired fine-STL and nut caps,
  how a CI under-prediction narrows the envelope, the ISO 4017 M20 x 60 pitch-1 preview and fine-STL
  case (G28 reply 3), and "Reversibility: costly". Pointer lines sit under L12, L13 and L16.

## Consequences the owner should know

1. **A d-only M5 is now served capped** (clarification ruling 2). `?d=5` used to lose its preview
   (G28 ruling 5). It is now served with thread_length 16.5 mm (from `cost.cap_defaults` at c850726)
   and a warning. Its prediction is unchanged.
2. **The nut `m` cap only works below about d 6.5 mm.**
   - Below the m/d band (0.8 d), G28 predicts a nut at the band's low edge. So once m is under
     0.8 d, a shorter m predicts no cheaper part.
   - With the default m of 5.2, only nuts under about d 6.5 can be helped. The test part is d 2,
     pitch 0.1, refused at step and capped to m 4.4.
   - Every larger nut over its budget keeps its 422.
3. **A wider head can cut the thread to almost nothing.**
   - An M6 with only `s` 15 named (s/d 2.5, above the band) is over its preview budget. The cap
     takes its thread from 20 mm to 0.5 mm, half a turn. That follows the rule as ruled.
   - The smallest fitted bolt point has 3 turns, so admitting this part rests on an extrapolation.
   - Filed as `docs/tech_debt/active/2026-10-29-default-cap-lands-below-the-fitted-turns.md`
     (must; trigger 07-15). The owner may want 07-15 to read a capped part below 3 turns.
4. **A preset is never capped.** Its fields count as given. On the API, though, a page link writes
   only the fields that differ from their defaults. So an ISO M6 x 20 with a typed `s` 15 is capped
   through the page but refused through `--preset iso4017:M6x20 --s 15`. That is truth 3 as written.

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 3 - Blocking] The `screw info` cap landed with Task 1**
- **Found during:** Task 1.
- **Issue:** the existing `tests/test_parity.py::test_the_cli_and_the_api_print_the_same_document[bolt]`
  (case `s` 15) failed once the API capped. The pre-commit `make verify` would not pass with the
  CLI uncapped.
- **Fix:** Task 1 also made `_params` return the explicit set and moved `cmd_info` to
  `derive_capped`. Task 2 added `cmd_export`, the nut, preset and pitch cases, and the parity
  test.
- **Files:** src/screw/cli.py. **Commit:** c850726.

**2. [Rule 1 - Spec] The cap warning comes first; the parity test was re-pinned**
- **Found during:** Task 1.
- **Issue:** the parity test asserted `warnings[0]` is the standing ends-modelled entry for every
  one-field-off part. The plan puts the cap warning first.
- **Fix:** for a capped part the test now asserts `[cap warning, STANDING_WARNING, ...]`. It keeps
  the literal check of the standing entry, which every document still carries.
- **Files:** tests/test_parity.py. **Commit:** c850726.

**3. [Rule 1 - Acceptance] The signature became `def cap_defaults(` as the plan names it**
- **Found during:** Task 2.
- **Issue:** Task 1 shipped a generic `def cap_defaults[T: FastenerParams](`. The criterion
  `grep -c "^def cap_defaults(" src/screw/calc/cost.py` then printed 0.
- **Fix:** Task 2 made `cap_defaults` and `derive_capped` take and return `FastenerParams`, and
  added `isinstance` narrowing in the tests. The count is 1 at HEAD.
- **Commit:** dc4b7fd.

**4. [Rule 2 - Correctness] A value off its default counts as named**
- **Issue:** `cap_defaults` can be called from Python with no explicit set.
- **Fix:** any field that is not at its frozen default is treated as named. This keeps the "never
  move a value the user chose" rule (T-07-31) without needing an explicit set.
- **Test:** `test_a_value_off_its_default_counts_as_named_on_direct_construction`.

**5. [Plan scope] Not built**
- **`per-artifact` and `part-wide-pitch` branches.** B-03 ruled `part-wide`, so the per-artifact
  `Download.warning` field was not added and the pitch is never moved. A test asserts that a part
  only a coarser pitch would admit keeps its refusal.

**6. [Added test] The ISO 4017 M20 x 60 claim in L21**
- **Fix:** `tests/test_cost.py::test_a_preview_can_be_refused_while_the_fine_stl_is_admitted`
  holds this claim, so the figure is computed by committed code (L02).

### TDD evidence

- **Task 1 RED:** the new cap tests were run against the HEAD versions of the four source files:
  12 failed, then the sources were restored.
- **Task 2 RED:** the CLI and parity tests were run against Task 1's `cli.py`: 4 failed.
- **GREEN:** every commit's pre-commit `make verify` passed.
- **Order:** the code for Task 1 was written before its tests, and RED was then shown by swapping
  the sources out.

## Requirements

OPER-03 is not ticked. The cap and refusal path is done, but the timeouts and the runner
verification (07-15, 07-16) are still open.

## Known Stubs

None.

## Threat Flags

None. The explicit set is read from the raw query keys and the given flags only (T-07-31). The scan
is at most 39 + 39 or 51 kernel-free candidates (T-07-32). Every cap emits its warning (T-07-33).

## Debt filed

- `docs/tech_debt/active/2026-10-29-default-cap-lands-below-the-fitted-turns.md` (must), with an
  INDEX row (commit 6cb928b).
- Not touched: `2026-10-29-in-wall-parts-the-kernel-refuses.md`.
- Not touched: `2026-10-29-cost-model-admits-out-of-fit-head-heights.md`, which stays active until
  07-15.

## Self-Check: PASSED

- All files listed in key-files exist.
- Commits a500356, c850726, dc4b7fd, 94aa461 and 6cb928b are ancestors of HEAD.
- `grep -c "^def cap_defaults(" src/screw/calc/cost.py` gives 1.
- `grep -c "cap_defaults\|derive_capped"` gives 6 in app.py and 4 in cli.py.
- `grep -c "^## L21 "` gives 1, with three "Superseded in part by L21" lines under L12, L13 and L16.
- Every run id named in L21 is in `bench/RESULTS.md`.
