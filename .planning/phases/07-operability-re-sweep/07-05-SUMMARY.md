---
phase: 07-operability-re-sweep
plan: 05
subsystem: testing
tags: [operability, github-runner, sweep-protocol, margin, walk-down, owner-stop]

requires:
  - phase: 07-operability-re-sweep
    provides: "07-04: the sweep protocol R1 to R30, amended through G1 to G24 (PRs A2, A3, A4), on the phase branch at a142c27"
provides:
  - "first runner readings of the phase: tracer, explore, spread, walls, controls and the R7 walk-down, committed as downloaded"
  - "bench.oper_sets: ProtocolStop, margin, charge_table/charges/shard_sizes, walk_down_points, decide_walls, confirm_points and their commands, tested on every stop"
  - "D-19 margin m = 0.5382691940004687 and the R6 charge table, derived from committed records"
  - "bench/points/walls-down.json (9 cells, 216 points, 9 R6 shards), read in one dispatch"
affects: [07-06, 07-07, 07-09, 07-15]

actuals:
  tokens: 15169   # chars/4 over the added lines of the four code and test files; generated point file and records excluded
  tasks: 2        # Task 1 and Task 2 complete; Task 3 stopped at step 3 (R10)
  commits: 6      # MEASURED: git rev-list --count a142c27..d4233bc
plan_head_before: a142c278f8bba48df8a2405ec7e092d42b725421
plan_head_after: d4233bccca1434704df85adbdd0f1958383c9b06   # before this SUMMARY's own commit

tech-stack:
  added: []
  patterns:
    - "a rule's owner stop is a ProtocolStop that the command line turns into exit 3; no value is chosen past it"
    - "sets generated from runner records carry `sources` and `shard_sizes`; --check writes them again from the records"

key-files:
  created:
    - tests/test_oper_followup.py
    - bench/points/walls-down.json
    - bench/results/phase-07/tracer-40645463872/
    - bench/results/phase-07/explore-40646117094/
    - bench/results/phase-07/spread-40646125666/
    - bench/results/phase-07/walls-40646134133/
    - bench/results/phase-07/controls-40646142406/
    - bench/results/phase-07/walls-down-40652801529/
  modified:
    - bench/oper.py
    - bench/oper_sets.py
    - tests/test_oper.py
    - bench/RESULTS.md

key-decisions:
  - "Plan stopped at R10 in Task 3 step 3: every nut-void root reading is refused at every radius, so V = 1e-1 lies outside the walk; the owner rules before candidate walls or the confirm set exist"
  - "confirm_points takes the decision only: cells below 250 turns are built by the shared turn constructor, cells at 250 and 260 are copied from the walls points"

requirements-completed: []

duration: 1h 40m (the runner sets took 10 to 45 minutes each)
completed: 2026-10-28
status: checkpoint
---

# Phase 7 Plan 05: Runs I Summary

**First runner figures of the phase are committed (tracer, explore, spread, walls, controls, the R7 walk-down), the margin is m = 0.538, and the plan halts at an R10 owner stop: all 270 nut-void root readings are refused at every radius, so no root-radius floor and no walls confirm set can be derived.**

Status is `checkpoint`: Tasks 1 and 2 are done, Task 3 is done through step 2 and stopped at step 3.

## Performance

- Tasks: 1 and 2 complete, 3 of 3 started, halted at an owner stop
- Files: 4 code and test files, 1 generated point file, 6 record directories, RESULTS

## Accomplishments

- **Task 1, tracer (D-01, D-02).** The precondition held: `grep -cE '^\| G(1[5-9]|2[01]) \|' 07-GAP-RULINGS.md` printed 7, and G15 to G24 are on main (PRs #23, #24, #25), which the phase branch carries at the merge a142c27. Run 40645463872 at a142c27: five reps, all `ok`, integer `memory_peak_bytes` (cgroup), nproc 4, MemTotal 16759443456, AMD EPYC 7763 (4 jobs) and 9V74 (1 job). The instrument works; no `no_cgroup`.
- **Task 2, four sets.** All dispatched at 7e7d7e6: explore 40646117094 (1692 readings: ok 1517, refused 142, capped 27, killed 6), spread 40646125666 (60 readings, all ok), walls 40646134133 (756: ok 300, refused 443, crashed 10, capped 2, killed 1), controls 40646142406 (69: ok 53, refused 16). Six CPU models were seen across explore (AMD EPYC 7763, 9V45, 9V74; Intel Xeon Platinum 8573C, 6973P-C, 8370C).
- **Controls against L11.** The four THRD-04 test rows reproduce on the runner as one valid wrong-volume solid: naive (2.0, 0.4, 4.0) ratio 0.290229, (8.0, 1.25, 10.0) 0.231722, (20.0, 2.5, 10.0) 0.219346, one-pipe (6.0, 1.0, 160 turns) ratio -0.999995 (inverted). No test row needs to change. Several other controls differ from the macOS rows in RESULTS (for example naive-M2-L10 is refused on the runner and built on macOS), as L11's platform note says.
- **Margin (R5, G3).** m = 0.5382691940004687, set by `iso4014:M20x200` at `stl-fine` (cold wall median 5.960 s, max 9.168 s). All 12 spread points were complete and ok, so no G3 stop. The next largest is 0.262 (`iso4032:M20` `stl-fine`).
- **R6 charges (G4).** Largest explore `wall_s` per group, every status: bolt preview 600.73 s (a `killed` reading), bolt fine 571.83, bolt step 29.94, nut preview 74.69, nut fine 576.09, nut step 37.97. Half the job timeout is 10500 s.
- **Code.** `bench/oper_sets.py` gained `ProtocolStop`, `margin`, `charge_table`, `charges`, `shard_sizes`, `walk_down_points`, `decide_walls`, `confirm_points`, and the commands `margin`, `charges`, `walk-down`, `decide-walls`, `confirm`; `--check` writes the derived sets again from their `sources`. `bench/oper.py` accepts optional `shard_sizes` and `sources`. The five protocol-pinned point files did not move (blob-sha tests pass).
- **Walk-down (R7, G2).** Nine cells were refused at 250 turns (bolt M2, M2.5, M3 by hand; nut M2 by hand and nut M3 right). `walls-down.json` holds 216 points in 9 R6 shards; run 40652801529 at 4dd60e1 read it in one dispatch (131 ok, 85 refused). First ok steps: bolt M2 right 100, nut M2 right 100, bolt M2 left 210, nut M2 left 200, bolt M2.5 right 90, bolt M2.5 left 180, bolt M3 right 90, nut M3 right 240, bolt M3 left 160. The candidate T from R7 is 90 turns.

## The owner stop (R10, Task 3 step 3)

`python -m bench.oper_sets decide-walls --walls bench/results/phase-07/walls-40646134133 --down bench/results/phase-07/walls-down-40652801529` exits 3:

```
oper_sets: stop (R10): the largest failing value is 0.01, so V is 0.1, which lies outside the walk (it holds at most 0.01)
```

**Rule.** R10: F is the largest root radius in `walls` group (d) with a refused or crashed reading, at any size, hand, rod or void; V is the smallest power of ten at or above 10 F; V must be a radius the walk holds (1e-2 to 1e-6); "Otherwise there is no number: the phase stops and asks the owner."

**Evidence** (all in `bench/results/phase-07/walls-40646134133/`, labels `root-{bolt|nut}-{size}-{hand}-r{r}`, tabulated in RESULTS under "D-08 stop at R10"):

- bolt rods: ok at every size and hand at 1e-2, 3e-3 and 1e-3; one refusal each at 3e-4 (`root-bolt-M12-right-r0.0003`) and 1e-4 (`root-bolt-M6-right-r0.0001`); all 30 refused at 3e-5, 1e-5, 3e-6, 1e-6.
- nut voids: **all 30 refused at every one of the nine radii, 1e-2 included** (270 of 270), always `Geometry kernel failed (StdFail_NotDone)`. The largest failing radius is therefore 1e-2 and V = 1e-1.
- The nut points are built with the pitch that solves `d/2 - thread_depth(pitch) + 0.15 = r`. For `root-nut-M8-right-r0.01` that is pitch 7.6487363662241625 mm and m 22.946 mm (`bench/points/walls.json`), against the M8 coarse pitch 1.25 mm. ASSUMPTION, not shown by a reading: the nut refusals come from this very coarse pitch and not from the root radius, so the nut walk carries no information about a radius wall.

R7 (T = 90), R8 and R9 resolved before the stop (computed by the same functions, not written as decisions anywhere in RESULTS): R8 decades bolt d 1e3 (999.999), bolt length 1e4, bolt s 1e3, bolt k 1e5, bolt thread_length 1e5, nut s 1e3, nut d 1e3 (999.699), nut m 1e4, nut clearance 1e3 (496.999); R9 V = 1e-4 (failing from 1e-6 down). These are provisional until the whole decision exists; nothing here is final, and the confirm set cannot be generated before R10 is ruled.

**Options for the owner** (a rule change after the first reading needs the owner's ruling, R30):

1. **Treat the nut-void walk as a harness/construction flaw and amend** (a new gap ruling, then a PR like A2 to A4): change group (d) so the nut void keeps a real pitch and the radius moves another way, regenerate `walls.json`, re-read group (d) in a new walls run, then apply R10. Costs a protocol amendment and one more walls dispatch; gives a nut radius figure that means something.
2. **Apply R10 to the rods only and record the voids as "refused at every radius, no wall inferred"** (amend R10's "rod or void"). With rods alone F = 3e-4, V = 1e-2, which the walk holds and every reading at or above it is ok. Cheapest; leaves nuts with no radius floor.
3. **Award no root floor**: R10 stays "no number", `MIN_ROOT_RADIUS_MM` is not added, and 07-07 proceeds without it (the debt item stays open). No amendment, no re-run.

**Recommendation:** option 1 if the owner wants nuts covered; option 2 if the phase should move on, because the rod readings are clean and the nut walk, as built, cannot answer the question R10 asks. I would not take option 3 silently: it leaves the root-radius floor debt unresolved.

Task 3 steps 3 to 5 (candidate walls, the confirm set at 5 reps, its run) are not done and no file for them exists.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `gh run download <id>` fails on the runner artifacts**
- **Found during:** Task 1
- **Issue:** `docker/build-push-action` also uploads `*.dockerbuild` build-record artifacts that are not valid zips, so `gh run download <id> -D DIR` exits 1 ("not a valid zip file") before writing the oper artifacts.
- **Fix:** `gh run download <id> -p 'oper-*' -D DIR`, which downloads the same oper artifacts; documented in RESULTS. No harness code changed, so nothing goes in the protocol's "Harness fixes" list.
- **Commit:** 7e7d7e6

**2. [Rule 1 - Design] `confirm_points` takes the decision only**
- **Found during:** Task 2
- **Issue:** the plan names `confirm_points(decisions, walls_spec, down_spec)`, but cells that were ok at 250 turns have no point in the walk-down file, so a walk-down spec cannot supply the 60 cells at T.
- **Fix:** below 250 turns the cells are built by the constructor that `walls` and the walk-down share; at 250 and 260 the walls points are copied verbatim with their `lift`. `walls-down.json` is not read for points.
- **Files modified:** bench/oper_sets.py, tests/test_oper_followup.py
- **Commit:** beb2437

**3. TDD cadence.** Tests and code are one commit (`beb2437`): the repo's commit hook runs `make verify`, so a failing RED commit cannot land. The tests were written first and the code was written until they passed.

**4. Extra commits.** The margin and charges got their own docs commit (7ce2080) so that the later `walls-down.json` commit follows the RESULTS record of the margin, as Task 3 orders them; the walk-down run and the R10 stop are in d4233bc.

**Total deviations:** 2 auto-fixed (1 blocking, 1 design), 2 process notes. **Impact:** none on any figure.

## Authentication Gates

None.

## Known Stubs

None.

## Threat Flags

None. The two new commands read committed records and write point files; `sources` paths are resolved inside the repo (`relative_to`).

## Issues Encountered

- Hook runs: every commit ran `make verify` and passed. The pre-commit framework stashed and restored the owner's unstaged files around each hook; nothing of theirs was staged, committed or lost.
- `.planning/STATE.md` carried an uncommitted orchestrator edit; this plan's state update is in the same commit as this SUMMARY.

## Next Phase Readiness

Blocked on the owner's ruling for R10. After it: if option 1, a protocol amendment, regenerated `walls.json` and a new walls run before step 3; if option 2 or 3, rerun `decide-walls` after the amendment (option 2) or record "no root floor" and continue to `confirm`. Then Task 3 steps 3 to 5 remain: candidate walls in RESULTS, `walls-confirm.json` (T = 90 would give 120 R7 points at turns90 and turns100), its dispatch, the 5-rep record, and the final docs commit. Plans 07-06 onward need the confirm run.

## Self-Check: PASSED

Files and record directories listed under key-files exist; commits 7e7d7e6, beb2437, 5ef2b1d, 7ce2080, 4dd60e1 and d4233bc are ancestors of HEAD; `python -m bench.oper_sets --check` exits 0; RESULTS has six `### <set>, run` subsections. Task 3's acceptance criteria are not all met (no candidate-walls subsection, no `walls-confirm.json`, no final docs commit); that is the stop above, not a failed check.
