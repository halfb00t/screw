---
phase: 07-operability-re-sweep
plan: 19
subsystem: infra
tags: [operability, full-tier, ci, merge-gate, pr-land, R5, R28, R29, G37, L26, L27, D-12, D-13, D-19]
status: complete

requires:
  - phase: 07-operability-re-sweep
    provides: "07-18 the required bounds tier (355 points, 4 shards) and L25's pitch walls; 07-05 the D-19 margin and R6 charges; 07-16 the timeouts"
provides:
  - "bench/points/full.json: R28's 1056 points under the shipped model, margin in the header, R6 charges and 40 shards, 106 parameter-model refusals in dropped (G37)"
  - "bench/points/dense-band.json and run 41153581470: G37's pre-read of the 18 residual-band dense points and their tip pieces"
  - "bench.oper: run judges points carrying timeout_s and limit (R29), expect: refused (G12), followup-matrix, run --followup-from, verdict; the tip_piece probe"
  - "operability.yml: weekly schedule, a pull_request trigger on calc/cost.py, calc/thread.py, params.py and solid/**, SET default full, followup-plan, followup and verdict jobs"
  - "scripts/pr_land.py: FULL_TIER_WORKFLOW, FULL_TIER_PATHS, parse_changed_files, full_tier_refusals, check_full_tier; land refuses a listed-path PR without a green full run"
  - "L26 (the two tiers) and L27 (the merge gate) in the decision log"
affects: [07-20]

estimate:
  tokens: 155000
  tasks: 3
actuals:
  tokens: 24442      # chars/4 over the added lines of the plan's diff outside the run records and point files (97767 chars)
  tasks: 3
  commits: 12        # MEASURED: git rev-list --count 023a3f9..8f9a1fc (this SUMMARY's commit not counted)
plan_head_before: 023a3f90da7ff905653fc52c63826346e8b9106b
plan_head_after: 8f9a1fc2c9dcb5cb6f65bf62e54346fcf205de2a

tech-stack:
  added: []
  patterns:
    - "a judged point carries its timeout and limits in the point file, and `run` fails its job after writing every record"
    - "R5's follow-up is a filter over the committed set and the run's own records, never a new point file"
    - "a merge gate decides from the PR's diff and its own list, held by tests to the workflow filter and to the cost model's ast import closure"

key-files:
  created:
    - bench/points/full.json
    - bench/points/dense-band.json
    - bench/results/phase-07/dense-band-41153581470/
    - bench/results/phase-07/full-41155746591/
    - docs/tech_debt/active/2026-10-31-full-tier-follow-up-job-never-run-on-the-runner.md
    - .planning/WINDOWS.md
  modified:
    - bench/oper.py
    - bench/oper_child.py
    - bench/oper_sets.py
    - bench/RESULTS.md
    - bench/results/phase-07/runtime.json
    - .github/workflows/operability.yml
    - scripts/pr_land.py
    - tests/test_oper.py
    - tests/test_oper_followup.py
    - tests/test_pr_land.py
    - docs/architecture/decision_log.md
    - docs/tech_debt/active/2026-10-05-shared-infra-extraction.md
    - docs/tech_debt/INDEX.md
    - .planning/phases/07-operability-re-sweep/07-GAP-RULINGS.md
    - .planning/phases/07-operability-re-sweep/07-OWNER-RULINGS.md

key-decisions:
  - "G37 ruling 1: the 18 dense-boundary bolts in the in-wall residual band were read on the runner before the trigger and gate (run 41153581470): all ok; M3-right n90 tip piece 0.9687 of T_PIECE"
  - "G37 ruling 2: full-tier combinations the parameter model refuses go in dropped with their type (R4), not judged"
  - "L26 logged (plan's L24, renumbered): the required bounds tier and the full recording tier, D-19 follow-up, T-3-14 for the PR trigger"
  - "L27 logged (plan's L25, renumbered): pr.land requires a green full operability run on the head of a PR that touches FULL_TIER_PATHS; only runs named operability: full count"

requirements-completed: []  # OPER-01 and OPER-03 are also 07-20's, and the in-wall residual keeps OPER-03 open

duration: about 2h10m of execution over two sessions
completed: 2026-10-31
---

# Phase 7 Plan 19: The full recording tier and its merge gate Summary

**The full grid (1056 points) is now a judged operability set. It runs weekly and on any PR that touches `calc/cost.py`, `calc/thread.py`, `params.py` or `solid/`. `make pr.land` refuses such a PR until a full run is green on its head. The first dispatch (41155746591) and the first PR run (41158301476) both came back green.**

## Performance

- **Duration:** about 2 h 10 min of execution.
  - 2026-10-30 16:55 UTC: the residual stop before any dispatch.
  - 2026-10-31 00:45 to 02:55 UTC: everything after the owner's G37 ruling.
- **Tasks:** 3 of 3
- **Commits:** 12, measured from the ledger. The SUMMARY commit is not counted.

## The residual stop and G37

The plan first stopped before any dispatch, as orchestrator note 3 asked. I drew the full grid by code and compared it with the explore and walk records. 114 admitted points lie in the in-wall debt's residual band (d 0.5 to 0.85 or 1.6 to 3.3 mm, more than 3 turns):

- **96 catalogue points:** each one read `ok` at explore.
- **18 dense-boundary bolts:** no runner had read them.

The owner ruled G37: read the 18 first, and put the parameter-model refusals in R4's `dropped` list. Both rulings are in `07-GAP-RULINGS.md` and `07-OWNER-RULINGS.md` (f89d962). No rule changed, so the protocol text was not edited.

**Pre-read, run 41153581470 at 5e5c07d:** 18 points and 12 `tip_piece` probes, all `ok`. `bench.oper verdict` gives `dense-band: 30 points, 0 failures`. No point reached its timeout after the margin, and no reading exceeded its envelope.

| part (both hands read) | n (preview, fine / step) | tip piece / T_PIECE, right | left |
| --- | --- | --- | --- |
| M2, pitch 0.4 | 90 / 60 right, 61 left | 0.784 (n90), 0.521 (n60) | 0.411 (n90), 0.317 (n61) |
| M2.5, pitch 0.45 | 90 / 58 right, 59 left | 0.923 (n90), 0.620 (n58) | 0.511 (n90), 0.350 (n59) |
| M3, pitch 0.5 | 90 / 58 right, 57 left | **0.9687** (n90), 0.653 (n58) | 0.526 (n90), 0.381 (n57) |

M3-right at 90 turns has a tip piece of +0.029060678245931948 against T_PIECE 0.03, which is 0.9687 of the gate. The debug session read +0.0291 on macOS for the same part. The exact figures are in `bench/RESULTS.md`, `### dense-band, run 41153581470`.

## Accomplishments

- **Task 1 (5e5c07d, 3480e19):** the full tier as a judged set.
  - `bench/points/full.json` holds 924 catalogue points, 42 nut-factorial points and 90 dense-boundary points.
  - 106 combinations the parameter model refuses are in `dropped`: 57 `pitch_too_fine`, 25 `turn_cap`, 18 `nut_too_thin` and 6 `pitch_too_coarse`.
  - The header carries the margin m 0.5382691940004687, the R6 charges and 40 shards.
  - `run` judges every point that carries `timeout_s` and `limit`.
  - The child reads an `expect: refused` point's refusal from the info document and builds nothing.
  - `followup-matrix`, `run --followup-from` and `verdict` implement R5.
  - The workflow gains `followup-plan`, `followup` and `verdict`.
- **Tracer gate:** the verify commands pass (699 tests and `--check`). I then dispatched the full set once, run 41155746591 at b0186b9:
  - 1056 of 1056 `ok`, and the verdict passed;
  - the largest cold wall was 0.397 of its timeout (iso4017:M20x200, stl-fine);
  - `followup` was skipped because nothing was selected;
  - envelope-check: "no reading exceeds its envelope", and fit.json is unchanged.
- **Task 2 (dc88f12, f9868bf):** D-13 end to end.
  - The workflow keeps dispatch, now with an optional `set`. It gains a weekly `41 4 * * 1` cron and a `pull_request` trigger filtered to the four paths.
  - It keeps `contents: read`, names no secret, and never uses the base-context PR event. 07-01's dispatch-only pin is replaced.
  - `pr_land.py` adds `check_full_tier` after `check_head`.
  - The two recorded fixtures are PR A's files and the operability full runs for the 07-05 tracer's head (`[]`). Both were read with the real `gh` on 2026-10-31.
- **Task 3 (caa39ce, e11d4e6):**
  - L26 and L27 are logged, and L08 is marked "Extended by L26" and "Extended by L27".
  - The extraction item records the second trigger and stays active.
  - L21 is not amended: neither 07-18 nor this plan widened an envelope.
- **On PR #26's head e11d4e6:**
  - the `pull_request` trigger fired: operability run 41158301476 succeeded, with its verdict passing and `followup` skipped;
  - CI run 41158301475 succeeded on all 7 jobs, `bounds (1)` to `(4)` included.

  PR #26 stays a draft and was not merged.

## Task Commits

1. `f89d962` docs(07): record the owner's ruling G37 on the full tier's residual points
2. `5e5c07d` feat(bench): read the full tier's 18 residual-band points and their tip pieces first (07 G37)
3. `f645ac0` chore(bench): record the dense-band pre-read, run 41153581470 (07 G37)
4. `3480e19` feat(bench): the full recording tier's point set, judged, with R5's re-runs on five runner instances (07 D-12, D-19)
5. `b0186b9` docs(bench): record the dense-band pre-read, run 41153581470, and its tip pieces (07 G37)
6. `dc88f12` ci: run the full operability tier weekly and on PRs that touch the cost model's files or the solid package (07 D-12, D-13)
7. `f9868bf` feat(scripts): pr.land refuses a PR that touches the cost model's files or the solid package until the full tier is green for its head (07 D-13)
8. `3ba9784` chore(bench): record the first full-tier run, 41155746591 (07 D-12, R28)
9. `d264b69` docs(bench): record the first full-tier run, 41155746591, and the bounds runs (07-19)
10. `caa39ce` docs(07): log the two operability tiers as L26
11. `e11d4e6` docs(07): log the full-tier merge gate as L27 and note the L07 trigger
12. `8f9a1fc` docs(debt): the full tier's follow-up job has never run on the runner

## Runs

| run | what | head | result |
| --- | --- | --- | --- |
| 41094108547 | CI, still running at launch | 023a3f9 | success, 7 of 7 jobs |
| 41153581470 | operability `dense-band` (G37) | 5e5c07d | success, 30 of 30 ok |
| 41155746591 | operability `full`, dispatch | b0186b9 | success, 1056 of 1056 ok, follow-up skipped |
| 41155751598 | CI | b0186b9 | success |
| 41158301476 | operability `full`, `pull_request` | e11d4e6 | success, verdict 1056 points 0 failures, follow-up skipped |
| 41158301475 | CI | e11d4e6 | success, 7 of 7 jobs |

## Deviations from Plan

### Auto-fixed Issues

**1. [Orchestrator note 1] Renumbered L24/L25 to L26/L27**
- The plan's L24 is logged as L26 and its L25 as L27, in the code comments, the tests, the docstring and this SUMMARY. The marker under L08 reads "Extended by L27", plus "Extended by L26" for the bounds jobs that L26 adds to L08's required list.

**2. [Rule 2 - Missing check] Only `operability: full` runs count for the gate**
- **Found during:** Task 2
- **Issue:** the plan takes the newest `operability.yml` run for the head. A later dispatch of another set on the same head (such as `dense-band` or `tracer`) would then pass the gate.
- **Fix:** the runs read keeps only runs named `operability: full`, with a jq `select` in `pr_land.py`. `FULL_TIER_RUN_NAME` is held to the workflow's `run-name` by a test, and the recorded tracer head pins the case.
- **Commit:** f9868bf

**3. [Scope] Task 1 split across three commits**
- `run`'s judging, the full-set generator and the `tip_piece` probe landed in 5e5c07d, because G37's pre-read needed them before the rest of Task 1.
- The rest of Task 1 carries the plan's commit subject (3480e19).

**4. [Rule 3 - Blocking] runtime.json lists every record folder**
- `tests/test_runtime_bounds.py` derives runtime.json from every folder under `bench/results/phase-07/`. Each records commit therefore regenerates it.
- Only `sources` and the header count moved (275, then 315). No derived value moved.

**5. [Scope] A full run was dispatched as the tracer's end-to-end check**
- The plan's tracer verify is local. A dispatch of the full set traced the new jobs on the runner before the trigger and the gate were committed.

### Not met on the runner

- **Follow-up on 5 instances:** the tracer's "R5's follow-up jobs judging a within-margin point on 5 runner instances" was not reached on the runner. No full-grid point reaches its timeout after the margin, so `followup` was skipped in both full runs.
  - Its logic is tested offline: the selection, the shard cut, the matrix, the reads, the four-reps, over-timeout and unread failures, and the workflow pins.
  - A synthetic point to force it would be a point file outside `bench.oper_sets` (R30), so none was made.
  - Filed as debt (below) and in `.planning/WINDOWS.md` (#1, unrun-verify).
- **No expected refusals:** the full set holds no `expect: refused` point today. C1 keeps every catalogue row, and the dense boundary is admitted by construction. The G12 path is tested offline only.

## Debt Changes

- **Filed (nice):** `docs/tech_debt/active/2026-10-31-full-tier-follow-up-job-never-run-on-the-runner.md`, with its INDEX row. It is revisited on the first full run that selects a follow-up point.
- **Updated (nice, still active):** `docs/tech_debt/active/2026-10-05-shared-infra-extraction.md`. Its Context gains the 2026-10-31 line: `pr_land.py` diverged from spur's copy in 07-19 (L27). The INDEX trigger column names it too.
- **Unchanged (must):** `docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md`. The 18 residual-band dense points built on the runner, M3-right at 0.97 of T_PIECE, and the residual stays open.

## Verification

- `make verify`: `4790 passed in 195.22s` (ruff, mypy --strict on 97 files, 10 import contracts kept, the unfinished-work scan). Green in the pre-commit hook on every commit.
- `.venv/bin/python -m bench.oper_sets --check`: exit 0.
- `python3 -c` over full.json: `full True True`. Its 294 x 3 bolt and 14 x 3 nut catalogue points are all present.
- The acceptance greps:
  - `pull_request_target` 0 and `secrets\.` 0 in operability.yml;
  - `WORKFLOW = "ci.yml"` 1 and `FULL_TIER_WORKFLOW = "operability.yml"` 1 in pr_land.py;
  - `## L26 ` 1, `## L27 ` 1 and `Extended by L27` 1 in the decision log;
  - `07-19` in the extraction item;
  - the bounds run 41089145344 and the margin's spread run 40646125666 both appear in `bench/RESULTS.md`.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: ci-trigger | .github/workflows/operability.yml | A new `pull_request` trigger runs a PR's code on the runner, as planned under T-07-47. It has `contents: read`, no secret and is never the base-context event. A PR author can still edit this workflow in their PR, so the `verdict` is the author's code, the same as ci.yml's `test`. L27 relies on GitHub's ruleset and `make pr.land` being the merge path, not on the workflow's integrity. |

## Self-Check: PASSED

- FOUND: bench/points/full.json, bench/points/dense-band.json, bench/results/phase-07/dense-band-41153581470/, bench/results/phase-07/full-41155746591/, docs/tech_debt/active/2026-10-31-full-tier-follow-up-job-never-run-on-the-runner.md
- FOUND: all 12 commits (f89d962 to 8f9a1fc) are ancestors of HEAD
