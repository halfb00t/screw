---
phase: 08-pre-release-gap-closure
plan: 06
subsystem: bench
tags: [fine-sweep, proof-walk, cost-resweep, dispatch, d-04, d-05, d-07, f6, f9, oper-03]

requires:
  - phase: 08-pre-release-gap-closure
    provides: "08-05's fine sweep and uses_fine_sweep; 08-12's bands and the small-d wall (L37); 08-03's band-walk records"
provides:
  - "bench/points/fine-proof.json: F6's proof walk (5790 points, 87 dropped, 91 shards)"
  - "bench/points/fine-cost.json and fine-spread.json: F9's cost re-sweep and spread sets of the fine-swept parts"
  - "The freeze commit 09af247 and three operability runs dispatched from it (fine-proof, fine-cost, fine-spread)"
affects: [08-07, 08-08]

actuals:
  tokens: 9579    # chars/4 over the +/- lines of bench/oper_sets.py and tests/test_oper_fine.py (38315 chars); the three generated point files (about 1.59M chars) are excluded, they are output of the generators
  tasks: 3
  commits: 2      # MEASURED: git rev-list --count 56f4629..09af247

plan_head_before: 56f4629e9ae7c76dc4d76b517c09ffe06656fe8b
plan_head_after: 09af247322141e81c8584092ab7f92cea66b7cfa

tech-stack:
  added: []
  patterns:
    - "A refusal source read from committed records (explore, band walk) feeds a later point set through one function, so a grid is re-derived rather than copied"
    - "The dispatch is the owner's act (D-04, L33); the executor pushes the freeze commit, the owner replies, the run ids are recorded against the freeze sha"

key-files:
  created:
    - bench/points/fine-proof.json
    - bench/points/fine-cost.json
    - bench/points/fine-spread.json
  modified:
    - bench/oper_sets.py
    - tests/test_oper_fine.py

key-decisions:
  - "Drops use _runner_refusal (walls-lifted model plus the production pitch wall) because bench/oper_child.py validates with oper_lift.validate; accepted by the owner"
  - "F6 (b)'s named explore evidence is dispatched as is although it never reaches the runner; accepted by the owner on the orchestrator's and executor's recommendation"

requirements-completed: []  # OPER-03 closes later (08-07, 08-08, 08-09)

coverage:
  - id: D1
    description: "F6's proof walk is a committed, regenerable, sharded set covering every D-07 grid and every in-band refusal of the explore and band-walk records"
    requirement: "OPER-03"
    verification:
      - kind: unit
        ref: "tests/test_oper_fine.py"
        status: pass
      - kind: other
        ref: ".venv/bin/python -m bench.oper_sets --check"
        status: pass
    human_judgment: false
  - id: D2
    description: "F9's cost and spread sets hold only fine-swept parts (D-05)"
    requirement: "OPER-03"
    verification:
      - kind: unit
        ref: "tests/test_oper_fine.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "The owner dispatched the three sets from one pushed freeze commit"
    requirement: "OPER-03"
    verification:
      - kind: other
        ref: "gh run view <id> --json headSha,event for 41684315321, 41684331518, 41684347573"
        status: pass
    human_judgment: false

duration: n/a
completed: 2026-11-03
status: complete
---

# Phase 8 Plan 06: Proof walk and fine cost sets Summary

**F6's proof walk (5790 points over 91 shards) and F9's cost and spread sets of the fine-swept parts, pre-registered on one pushed freeze commit and dispatched by hand on linux/amd64**

## Performance

- **Duration:** not tracked (two sessions with an owner checkpoint between)
- **Tasks:** 3 (two commits; the third is the owner's dispatch)
- **Files modified:** 5 (two sources, three generated point files)

## Accomplishments

- `python -m bench.oper_sets proof-walk` regenerates `bench/points/fine-proof.json` from F6's four grids and the refusals in the explore run and the band walk; `--check` exits 0.
- `python -m bench.oper_sets fine-cost-sets` regenerates `fine-cost.json` (reps 1) and `fine-spread.json` (reps 5) from the explore points; only parts `uses_fine_sweep` puts on the fine sweep are drawn (D-05, D-19).
- The three sets were dispatched from the freeze commit, no turns guard in the tree; from `09af247` on, `helical.py`, `bolt.py`, `nut.py` and the F3 and F5 constants are frozen (F11).

## Counts

| Set | Points | Dropped | Shards | Notes |
|---|---|---|---|---|
| fine-proof (reps 1) | 5790 | 87 | 91 | 4526 at `step`, 1264 at `stl-preview`; dropped: 40 nut_too_thin, 40 less_than_equal, 4 turn_cap, 3 pitch_too_fine |
| fine-cost (reps 1) | 278 | 91 | 10 | dropped: 61 pitch_too_fine, 14 turn_cap, 16 over_budget at `step` |
| fine-spread (reps 5) | 24 (8 rows x 3 artifacts) | 0 | 1 | the 8 nut rows of D-16, right hand |

## Dispatch (Task 3, D-04)

Freeze sha: `09af247322141e81c8584092ab7f92cea66b7cfa` (pushed; `HEAD == origin head`, clean tracked tree, `make verify` at it: 5246 passed in 187.57 s).

The owner replied, verbatim: `approved, run"` (that is, "approved, run"), and asked Claude to dispatch on their behalf, as in 08-01. Claude dispatched at the owner's instruction (D-04), via the orchestrator, which ran the three plan commands.

| Set | Run id | Created (UTC) | headSha | Event |
|---|---|---|---|---|
| fine-proof | 41684315321 | 2026-11-03T17:26:48Z | 09af247322141e81c8584092ab7f92cea66b7cfa | workflow_dispatch |
| fine-cost | 41684331518 | 2026-11-03T17:26:55Z | 09af247322141e81c8584092ab7f92cea66b7cfa | workflow_dispatch |
| fine-spread | 41684347573 | 2026-11-03T17:27:01Z | 09af247322141e81c8584092ab7f92cea66b7cfa | workflow_dispatch |

Each run was re-checked with `gh run view <id> --json headSha,event`: all three show the freeze sha and `workflow_dispatch`, all `queued` at the check. The runs were not waited on and nothing was downloaded; reading them is 08-07.

## Task Commits

1. **Task 1: proof walk from F6's grids (tracer)** - `d34b3a4` (feat)
2. **Task 2: cost re-sweep and spread sets (F9)** - `09af247` (feat), the freeze commit
3. **Task 3: owner dispatch** - no commit; run ids above

## Files Created/Modified

- `bench/oper_sets.py` - `PROOF_WALK`, `_refused_on_fine`, `proof_walk_set`, `build_proof_walk`, `FINE_COST`, `FINE_SPREAD`, `fine_cost_set`, `fine_spread_set`; subcommands `proof-walk` and `fine-cost-sets`; `--check` registration
- `bench/points/fine-proof.json`, `fine-cost.json`, `fine-spread.json` - the generated sets
- `tests/test_oper_fine.py` - per-grid count tests, `test_every_grid_a_cell_is_on_the_fine_sweep`, the D-05 test over both cost files

## Decisions Made

None beyond the two deviations below.

## Deviations from Plan

**1. [Rule 1 - Bug in the plan's drop rule] Drops use `_runner_refusal`, not the plain parameter-model refusal.** The plan says a dropped cell carries the parameter model's error type with the pitch walls lifted. `bench/oper_child.py` validates with `oper_lift.validate`, so a cell the walls-lifted model admits but the production pitch wall refuses would be dropped at the child, not read. `_runner_refusal` (walls-lifted model plus the production pitch wall) drops those cells in the set, where the count is visible, with their type (the 3 and 61 `pitch_too_fine` drops above). Reported to the owner before the dispatch and accepted.

**2. [Evidence gap, accepted by the owner] F6 (b)'s named explore evidence never reaches the runner.** The six d 3, d / pitch 8.57, 84 mm (240 turns) explore bolts and the d / pitch 30 cells are `turn_cap` or `pitch_too_fine` under the shipped model, so they are in `dropped` and are not read on the runner. The sets were dispatched as drawn on the orchestrator's and executor's recommendation; the owner approved. 08-07 must not claim those cells were read on the fine sweep.

**Total deviations:** 2 (1 rule 1, 1 owner-accepted evidence gap). No scope creep; no frozen file touched.

## Issues Encountered

An orphaned `make verify` was not left behind; commits used plain `git commit` and passed the hook (`gsd-tools query commit` times out inside it).

## Known Stubs

None.

## Threat Flags

None. Only point files and their generators changed.

## Next Phase Readiness

- 08-07 reads the three runs: `gh run view <id> --json headSha,event` shows the freeze sha above; it checks `git diff 09af247 HEAD` of `helical.py`, `bolt.py`, `nut.py` and the F3 and F5 constants is empty (T-08-17).
- A killed or timed-out shard is stop S1 (assumption: fine sweep under 2x the shipped build time, R6).

## Self-Check: PASSED

- `d34b3a4` and `09af247` are ancestors of HEAD; `git rev-list --count 56f4629..HEAD` was 2 at the check.
- `bench/points/fine-proof.json`, `fine-cost.json`, `fine-spread.json` exist; the three run ids show the freeze sha.
