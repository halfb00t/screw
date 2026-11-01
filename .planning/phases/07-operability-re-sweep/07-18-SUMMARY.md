---
phase: 07-operability-re-sweep
plan: 18
subsystem: infra
tags: [operability, bounds, ci, required-tier, fine-pitch, guard, decision-log, debt, R27, R31, G33, G34, G35, G36, L25, D-07, D-12, D-15]
status: complete

requires:
  - phase: 07-operability-re-sweep
    provides: "07-15 tier-order.json (R27 steps 1 to 4) and fit.json; 07-16 runtime.json and BUILD_TIMEOUT_S; 07-21 the serving knobs"
provides:
  - "tests/data/oper_boundary.json: R27 step 5 over the committed D(A), less the 80 points the fine-pitch wall refuses: 355 points (stl-preview 151, stl-fine 51, step 153) in 4 shards"
  - "`python3 -m bench.oper check FILE --image IMAGE [--shard N] [--out PATH]`: every point once, cold, judged against its timeout and its limits"
  - "ci.yml `bounds` matrix job (4 shards, 20 min each, needs image, contents: read, no secret), each shard required in required-jobs.txt"
  - "the R31 fine-pitch walk (bench/points/walls-pitch.json, run 41074314305) and its judge `python -m bench.oper_sets pitch-walls --from`"
  - "L25: a 422 `pitch_too_fine` naming d and pitch above exact d / pitch 20 (bolt) or 8 (nut), validated once at the parameter-model boundary"
  - "bench.oper_lift.drawn: the production model less the fine-pitch wall, for every set drawn before R31"
affects: [07-19, 07-20]

estimate:
  tokens: 95000
  tasks: 3
actuals:
  tokens: 51827      # chars/4 over the added lines of the plan's diff outside the run records, point files and tier data (207307 chars); 1449356 with them
  tasks: 3
  commits: 15        # MEASURED: git rev-list --count 8100a3a..ffa53f1 (this SUMMARY's commit not counted)
plan_head_before: 8100a3a89f125ac011f7f12d44d6a31e2f1e5cf1
plan_head_after: ffa53f13670cc096f90487167be7acafb1593218

tech-stack:
  added: []
  patterns:
    - "a matrix CI job per shard of a pre-registered point set, shards cut by the explore walls so each stays under 600 s"
    - "a regenerated file may move a prediction-derived float by a relative 2^-51 and nothing else (G33)"
    - "a wall derived from runner records is a BEGIN/END block the judge prints, and a test holds the shipped block to the committed records"
    - "a guard added after sets were drawn is lifted when those sets are checked (oper_lift.drawn), so no earlier record or derived value moves"

key-files:
  created:
    - tests/test_fine_pitch.py
    - tests/test_oper_pitch.py
    - bench/points/walls-pitch.json
    - bench/results/phase-07/walls-pitch-41074314305/
    - .planning/phases/07-operability-re-sweep/07-18-SUMMARY.md
  modified:
    - src/screw/calc/thread.py
    - src/screw/params.py
    - bench/oper.py
    - bench/oper_sets.py
    - bench/oper_lift.py
    - bench/oper_fit.py
    - bench/build_time.py
    - bench/corpus.py
    - bench/RESULTS.md
    - bench/results/phase-07/runtime.json
    - tests/data/oper_boundary.json
    - .github/workflows/ci.yml
    - .github/workflows/required-jobs.txt
    - docs/architecture/decision_log.md
    - docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md
    - docs/tech_debt/INDEX.md
    - .planning/phases/07-operability-re-sweep/07-SWEEP-PROTOCOL.md
    - .planning/phases/07-operability-re-sweep/07-GAP-RULINGS.md
    - .planning/phases/07-operability-re-sweep/07-OWNER-RULINGS.md
    - .planning/debug/resolved/in-wall-kernel-builderror.md
    - .planning/debug/knowledge-base.md

key-decisions:
  - "G33: a regeneration may move a prediction-derived float (edge_ratio, limit) by a relative 2^-51; the runner moved 2 of 2559 by 1.459 x 2^-52"
  - "G34: the required tier runs in parallel shards cut in file order by the explore container walls, each under 600 s, every point once"
  - "G35: guard the in-wall parts with an exact d / pitch wall (422 pitch_too_fine), measured by a walk on the runner, residual as must debt"
  - "G36: the nut's wall is 8 by the owner's ruling (the margin rule gave 5 from an island at d 2.2, d / pitch 7); the sets drawn before R31 are checked without the wall and the tier drops the points it refuses, with no refill"
  - "L25 logged: bolt wall 20 from walk run 41074314305 (F 26.999784001727985), nut wall 8 ruled; supersedes nothing and extends the 422 types of L13, L15, L20, L21 and L22 without editing them"

requirements-completed: []  # OPER-01 and OPER-03 are also 07-19's and 07-20's, and the in-wall residual keeps OPER-03 open

duration: 6h03m
completed: 2026-10-30
---

# Phase 7 Plan 18: The required bounds tier, green on the runner behind the fine-pitch walls Summary

**A required `bounds` CI job builds the 355-point R27 boundary tier in the production image in 4 shards and judges each point against its timeout and limits. It went green on PR #26 once L25's d / pitch walls (bolt 20 from a runner walk, nut 8 by ruling) refused the 20 in-wall parts the kernel could not build.**

## Performance

- **Duration:** about 6 h (16:14 to 22:17 +0600, 2026-10-30), including five owner rulings and three runner readings
- **Tasks:** 3 of 3
- **Commits:** 15 (measured from the ledger)

## Accomplishments

- **Task 1 (9694cb6):** `tests/data/oper_boundary.json` is R27 step 5 over the committed D(A). `bench.oper check` reads each point once, cold, in its own container, and exits 1 naming any point that is not ok, past its timeout, or over a limit. `--out` writes the readings in `run`'s JSONL format.
- **Task 2 (155fabb, ed49dd1):** a `bounds` job in ci.yml. It needs `image`, loads the saved image, uses the runner's own Python 3.12, has `contents: read` and no secret, and uploads `bounds-records-<shard>`. It runs as a fail-fast-off matrix, and each shard is listed in required-jobs.txt.
- **Task 3:** the tier is green on draft PR #26, CI run 41089145344 at ffa53f1:

  | job | result | time |
  | --- | --- | --- |
  | test (3.12) | pass | 23m20s |
  | image | pass | 2m31s |
  | vendor-bundle | pass | 10s |
  | bounds (1) | pass | 12m27s |
  | bounds (2) | pass | 11m30s |
  | bounds (3) | pass | 8m0s |
  | bounds (4) | pass | 5m15s |

  Every shard is under its 20-minute timeout.

  The records were downloaded with `gh run download 41089145344 -p 'bounds-records*'` and judged with committed code:
  - `bench.oper.judge` over `load_boundary` for shards 1 to 4: 355 of 355 points, 0 failures. The largest cold wall is 0.402 of its point's timeout.
  - `python -m bench.oper_sets envelope-check` with a scratch copy of fit.json: "no reading exceeds its envelope". The scratch fit.json is byte-identical to the committed one. The largest ratio is 1.0, nut step bytes, at the point that set that envelope.

## The road to green (runner readings)

1. **CI run 41042483745** (155fabb), the tier in one job: 11 points were refused by the kernel. Separately, the regeneration tests failed on a one-ulp libm difference.
2. **CI run 41048346068** (ef45c0c) measured that drift. It led to G33, which tolerates a relative 2^-51 in prediction-derived floats (9b880db), and G34, which splits the tier into 5 shards (ed49dd1).
3. **CI run 41052312369** (9b880db): every shard was red on the same 11 kernel-refused points. The debug session (10d8c49) found the cause, the end-cut booleans on a swept thread at a fine pitch for its d.
4. **The rulings and the walk:**
   - G35 ruled a d / pitch wall measured on the runner (3662570, 7ecaebb).
   - Walk run 41074314305 (cfdf5f2): bolt F 26.999784001727985, W 20; nut F 6.999993636369421 (the island), W 5.
   - The nut W differed from the ruled 8, so the plan stopped.
   - G36 ruled the nut at 8 with the island kept as debt, kept the old sets, and dropped the refused points from the tier (74652ee).
   - CI runs 41074323357 and 41079543634 (7ecaebb, cfdf5f2) were red on the same 11 points, before the guard.
5. **The guard and the tier** (b49703b, 8ec96ba, 36c3601, ffa53f1), then CI run 41089145344: green.

## W per kind from the runner

| kind | F (smallest refused exact d / pitch) | reading | margin rule W | shipped W |
| --- | --- | --- | --- | --- |
| bolt | 26.999784001727985 | pitch-bolt-n3-d3-q27-right | 20 | 20 (from the records, by code) |
| nut | 6.999993636369421 | pitch-nut-base-d2.2-q7-left | 5 | 8 (owner's ruling G36) |

## Task Commits

1. `9694cb6` feat(bench): a boundary set and a check that fails on an overrun or under-prediction (07 D-07, D-12)
2. `155fabb` ci: a required bounds job builds the boundary set in the production image (07 D-12, D-15)
3. `ef45c0c` feat(bench): measure how far a regeneration's predicted floats drift from the committed files
4. `1543e7b` docs(07): record the owner's rulings G33 and G34 and amend R27
5. `ed49dd1` ci: read the required tier in five parallel shards (07 G34)
6. `9b880db` fix(bench): let a regeneration move a predicted float by the measured libm difference (07 G33)
7. `10d8c49` docs(debug): record the in-wall kernel BuildError diagnosis and guard measurements
8. `3662570` docs(07): record the owner's ruling G35 and add the fine-pitch walls rule R31
9. `7ecaebb` feat(bench): the R31 fine-pitch walk and its judge (07 G35)
10. `cfdf5f2` chore(bench): record the R31 fine-pitch walk, run 41074314305 (07 G35)
11. `74652ee` docs(07): record the owner's ruling G36 and amend R31
12. `b49703b` docs(bench): record the fine-pitch walk, run 41074314305, and R31's walls (07-18)
13. `8ec96ba` docs(decisions): log L25, the fine-pitch walls (07 R31, G35, G36)
14. `36c3601` feat(params): refuse a pitch too fine for its d, the fine-pitch walls of L25 (07 R31)
15. `ffa53f1` docs(debt): re-scope the in-wall debt to what L25 leaves and resolve its debug session

## Decisions Made

See `key-decisions` above. Every rule change after the freeze is an owner ruling (G33 to G36) recorded in 07-GAP-RULINGS.md and 07-OWNER-RULINGS.md. The protocol text is amended with no G labels or run ids, and it ends with the post-freeze closing sentence. L25 is logged.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Tests that used parts past the new wall were re-pinned to parts inside it**
- **Found during:** step C (the guard)
- **Issue:** about 36 tests and 18 collection errors used parts above d / pitch 20 (bolt) or 8 (nut). Examples: NUT_OVER at d 100 pitch 1, the field-wall corners at d 999.999 pitch 1, M18 x 2, the parity case at 1.5 x the default d, and the exact 90-turn row at d 4 pitch 0.03.
- **Fix:** each test keeps its subject with a part inside the wall:
  - pitch 50 at the bolt's d wall, 124.963 at the nut's d 999.699;
  - NUT_OVER d 50, pitch 6.25, m 500;
  - OVER at pitch 3 with 90 mm of thread;
  - parity at 1.25 x the default d;
  - M18 at pitch 3 for the off-key note.

  Where a test is about records drawn before the wall (the explore grid, the walk set), it validates through `oper_lift.drawn`. Each re-pin carries a comment naming R31.
- **Files modified:** the test_api, test_calc, test_cli, test_cost, test_nut, test_params, test_parity, test_bench, test_oper, test_oper_pitch and test_pr_land modules
- **Commit:** 36c3601

**2. [Rule 1 - Bug] The fine-pitch validator on the base class changed which 422 an older rule gives**
- **Found during:** step C
- **Issue:** pydantic runs a base class's after-validators first, so `head_too_small` and `turn_cap` cases started reporting `pitch_too_fine`.
- **Fix:** each kind calls the check from its own last validator, and a test pins the precedence.
- **Commit:** 36c3601

**3. [Rule 3 - Blocking] The local build-time corpus has three entries past the wall**
- **Found during:** step C
- **Issue:** `bench.corpus`'s d 100 rows (d / pitch 100 at the default pitch) no longer validate, and `load_sweep` raised.
- **Fix:** following G36's old-sets rule, the fixed corpus is validated without the wall. `bench.build_time` marks those rows `refused (L25)` at every artifact and does not judge them, as it already did for L21. A test pins the three labels.
- **Commit:** 36c3601

**4. [Rule 2 - Missing check] The walk judge for G36's semantics**
- **Found during:** step C
- **Issue:** after G36 the judge needed to stop only on a bolt W off 20. It also needed to list the refused cells the shipped walls still admit.
- **Fix:**
  - `pitch-walls` prints the shipped walls, the residual, and the block `calc.thread` must hold.
  - Tests hold the shipped block to the committed records.
  - A test pins the residual to the six island cells.
- **Commit:** 36c3601

**5. [Scope] The CI shard count went from 5 to 4**
- **Why:** G36 dropped 80 refused points, so the shard cut gives 4 shards: 117, 72, 115 and 51 points.
- **Fix:** ci.yml and required-jobs.txt moved together, and test_pr_land and test_oper follow.

## Debt Changes

- **Re-scoped (must, active):** `docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md`. Its new title is "Parts inside the fine-pitch walls that the kernel still refuses", with the trigger "before the first release".
  - It now covers the residual: the nut island at d 2.2, d / pitch 7, and the long-thread bolt bands below 20 (d 0.5 to 0.85 and 1.6 to 3.3 mm).
  - It keeps option 2's measured facts. The accuracy variant builds the 20, regresses 4 parts at d / pitch 250, and costs 1.33x to 1.54x the build time and 2.3x to 4.5x the STEP bytes.
  - The INDEX row is updated.
- **Debug session resolved:** `.planning/debug/resolved/in-wall-kernel-builderror.md`, with the fix (36c3601) and the verification filled in, plus a knowledge-base entry.
- **Filed:** no new item.

## Verification

- `make verify`: `4718 passed in 204.25s` (ruff, mypy --strict, import boundaries, the unfinished-work scan; green in the pre-commit hook on 36c3601 and ffa53f1)
- CI run 41089145344 at ffa53f1: all 7 jobs pass, and the bounds records are judged green by committed code (above)
- PR #26 stays a draft. It is not merged and not marked ready.

## Threat Flags

None. The guard narrows the inputs the API accepts and adds no endpoint, path or secret. The bounds job keeps `contents: read`, no secret and no `pull_request_target`.

## Self-Check: PASSED

- FOUND: tests/test_fine_pitch.py, tests/test_oper_pitch.py, bench/points/walls-pitch.json, bench/results/phase-07/walls-pitch-41074314305/, .planning/debug/resolved/in-wall-kernel-builderror.md
- FOUND: all 15 commits (9694cb6 to ffa53f1) are ancestors of HEAD
