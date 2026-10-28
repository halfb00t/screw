---
phase: 07-operability-re-sweep
plan: 05
subsystem: testing
tags: [operability, github-runner, sweep-protocol, margin, walk-down, walls-confirm]

requires:
  - phase: 07-operability-re-sweep
    provides: "07-04: the sweep protocol R1 to R30, amended through G1 to G24 (PRs A2, A3, A4), on the phase branch at a142c27"
provides:
  - "runner readings of Runs I: tracer, explore, spread, walls, controls, the R7 walk-down, the R10 void walk (read by the owner-ruled G25 step, not by this executor) and the 5-rep walls confirm, committed as downloaded"
  - "bench.oper_sets: ProtocolStop, margin, charge_table/charges/shard_sizes, walk_down_points, decide_walls, confirm_points and their commands, tested on every stop"
  - "D-19 margin m = 0.5382691940004687 and the R6 charge table, derived from committed records"
  - "bench/points/walls-down.json (216 points) and bench/points/walls-confirm.json (217 points, 5 reps, 9 R6 shards)"
  - "the R3 confirm outcome per candidate wall, in RESULTS, for plan 07-07: T = 90, MIN_TAIL_MM 1e-4 and MIN_ROOT_RADIUS_MM 1e-2 confirmed ok; nut d at 1e3 mm not confirmed (capped)"
affects: [07-06, 07-07, 07-09, 07-15]

actuals:
  tokens: 15169   # chars/4 over the added lines of the four code and test files of beb2437; generated point files and records excluded
  tasks: 3
  commits: 20     # MEASURED: git rev-list --count a142c27..b23bbf6. Of them 9 are this plan's (7e7d7e6 beb2437 5ef2b1d 7ce2080 4dd60e1 d4233bc daeafeb 8992e1c b23bbf6); the other 11 are the owner-ruled G25 and G26 work on the same branch (59017dc to b9a0096)
plan_head_before: a142c278f8bba48df8a2405ec7e092d42b725421
plan_head_after: b23bbf6b5a0a0e6fd0aedfa6ef8b22b0e17cce6a   # before this SUMMARY's own commit

tech-stack:
  added: []
  patterns:
    - "a rule's owner stop is a ProtocolStop that the command line turns into exit 3; no value is chosen past it"
    - "sets generated from runner records carry `sources` and `shard_sizes`; --check writes them again from the records"

key-files:
  created:
    - tests/test_oper_followup.py
    - bench/points/walls-down.json
    - bench/points/walls-confirm.json
    - bench/results/phase-07/tracer-40645463872/
    - bench/results/phase-07/explore-40646117094/
    - bench/results/phase-07/spread-40646125666/
    - bench/results/phase-07/walls-40646134133/
    - bench/results/phase-07/controls-40646142406/
    - bench/results/phase-07/walls-down-40652801529/
    - bench/results/phase-07/walls-confirm-40678150220/
  modified:
    - bench/oper.py
    - bench/oper_sets.py
    - tests/test_oper.py
    - bench/RESULTS.md

key-decisions:
  - "The first halt (R10, nut voids refused at every radius) was ruled by the owner as G25 and G26: R10 decides MIN_ROOT_RADIUS_MM from the rods of group (d) only, and the confirm for R10 is rods only"
  - "confirm_points takes the decision only: cells below 250 turns are built by the shared turn constructor, cells at 250 and 260 are copied from the walls points"
  - "The confirm outcome is recorded as it read: nut d at 1e3 mm is capped in 5 of 5 and is not confirmed; no value is awarded and the question goes to the owner before 07-07"

requirements-completed: [OPER-01, OPER-02, OPER-03]

duration: 1h 40m of work over two sessions, plus the owner's rulings and the runner queue
completed: 2026-10-28
status: complete
---

# Phase 7 Plan 05: Runs I Summary

**Runs I are on the branch with their provenance: m = 0.538, the R6 charges, the walk-down (T = 90 turns), and a 5-rep confirm of 217 points in which T, the tail floor (1e-4 mm) and the rod root floor (1e-2 mm) read ok in 5 of 5, and the nut `d` ceiling does not (capped in 5 of 5).**

## Accomplishments

- **Task 1, tracer (D-01, D-02).** The precondition held: `grep -cE '^\| G(1[5-9]|2[01]) \|' 07-GAP-RULINGS.md` printed 7, and G15 to G24 are on main (PRs #23, #24, #25), carried by the phase branch at the merge a142c27. Run 40645463872 at a142c27: five reps, all `ok`, integer cgroup `memory_peak_bytes`, nproc 4, MemTotal 16759443456, AMD EPYC 7763 (4 jobs) and 9V74 (1 job). No `no_cgroup`.
- **Task 2, four sets.** All dispatched at 7e7d7e6: explore 40646117094 (1692 readings: ok 1517, refused 142, capped 27, killed 6), spread 40646125666 (60, all ok), walls 40646134133 (756: ok 300, refused 443, crashed 10, capped 2, killed 1), controls 40646142406 (69: ok 53, refused 16). Six CPU models appear across the runs.
- **Controls against L11.** The four THRD-04 test rows reproduce on the runner as one valid wrong-volume solid (ratios 0.290229, 0.231722, 0.219346, and -0.999995 inverted). No test row needs to change. Other control rows differ from L11's macOS rows (for example naive-M2-L10 is refused on the runner, built on macOS), as L11's platform note says; all are in RESULTS.
- **Margin (R5, G3).** m = 0.5382691940004687, set by `iso4014:M20x200` at `stl-fine` (cold wall median 5.960 s, max 9.168 s); all 12 spread points were complete and ok. **R6 charges (G4):** bolt preview 600.73 s (a `killed` reading), bolt fine 571.83, bolt step 29.94, nut preview 74.69, nut fine 576.09, nut step 37.97; half the job timeout is 10500 s.
- **Code.** `bench/oper_sets.py`: `ProtocolStop`, `margin`, `charge_table`, `charges`, `shard_sizes`, `walk_down_points`, `decide_walls`, `confirm_points` and the commands `margin`, `charges`, `walk-down`, `decide-walls`, `confirm`; `--check` writes the derived sets again from their `sources`. `bench/oper.py`: optional `shard_sizes` and `sources`. The pinned point files did not move.
- **Walk-down (R7, G2).** Nine cells were refused at 250 turns; `walls-down.json` (216 points, 9 shards) was read in one dispatch, run 40652801529 at 4dd60e1 (131 ok, 85 refused). The smallest first ok step is 90 turns (bolt M2.5 right and bolt M3 right).
- **The first R10 halt and its resolution.** At the first resume point `decide-walls` exited 3 at R10: every nut-void root reading was refused at every radius. The owner ruled it (G25, then G26): the voids were walked upward (run 40665307964) and bear on no bound; R10 takes `MIN_ROOT_RADIUS_MM` from the rods of group (d) only. That work (commits 59017dc to b9a0096) is not this plan's; the candidate walls in RESULTS (`### candidate walls (before the confirm)`) come from it and I did not duplicate them.
- **Task 3 steps 4 and 5, the confirm (R3, G1, G26).** `walls-confirm.json` generated by `bench.oper_sets confirm` (217 points at 5 reps, 9 R6 shards [30, 30, 30, 30, 29, 17, 17, 17, 17]): 60 cells at `turns90-` and 60 at `turns100-` (120 R7 points), the R8 fields at their decade and the next (two lifted `beyond-` points, both carrying their `lift`), the tail cells at 1e-4 and 1e-5 (12), the rod cells at 1e-2 and 3e-3 (60, all `root-bolt-`). Run 40678150220 at 8992e1c: 1085 readings, 217 points each with repetitions 1 to 5 once, none incomplete, none mixed (ok 1035, refused 35, capped 10, killed 5).

### The confirm outcome (full table in RESULTS, "R3 outcome of the confirm run by candidate wall")

| wall | at the decided value | one step past |
| --- | --- | --- |
| MAX_TURNS, T = 90 | ok, 60 of 60 cells, 5 of 5 | 100 turns: 58 ok, `bolt-M2.5-right` and `bolt-M3-right` refused 5 of 5 |
| MIN_TAIL_MM, V = 1e-4 | ok, 6 of 6 points | 1e-5: ok, 6 of 6 |
| MIN_ROOT_RADIUS_MM, V = 1e-2 (rods) | ok, 30 of 30 | 3e-3: ok, 30 of 30 |
| bolt d 999.999 (1e3) | ok | 1e4 refused |
| bolt length 1e4, bolt s 1e3, bolt k 1e5, bolt thread_length 1e5, nut s 1e3, nut m 1e4, nut clearance 496.999 (1e3) | ok | refused, ok, killed or capped as listed in RESULTS (none raises a wall) |
| **nut d 999.699 (1e3)** | **capped, 5 of 5** | 1e4 refused |

## Owner question for plan 07-07 (not a halt of this plan)

The nut `d` ceiling does not confirm. `ceiling-nut-d-1000` (d 999.699, s 1000) read `ok` in the first walls run with `memory_peak_bytes` 12663300096, which is 92752773 bytes under the 99 % capped threshold (12756052869 of the 12 GiB cap), and read `capped` in all 5 confirm repetitions. R8 calls `capped` cost: it moves no wall, and it cannot raise one, so the tested value 999.699 is not confirmed. The next decade (1e4) is refused, and no decade below 1e3 is in the grid, so under R8 the field has no confirmed ok decade; the rules do not say what the confirm does then (R7 and the above-0 floors have an explicit stop, R8 has none for the confirm). I did not pick a value. Options for the owner:

1. **Treat nut `d` as having no number** (R8: "there is no number"), as the stop the rule would give if it were run on the confirm; 07-07 writes no nut `d` ceiling, and the nut `d` field keeps its present bound.
2. **Rule that a memory-bound reading is a cost bound** and take the budget model to cap nut `d` (a cost question for R13 to R16), keeping the wall unrecorded.
3. **Walk the nut `d` decade grid down** (a new lower step, for example 5e2 mm, a rule change after the first reading) and confirm it at 5 reps.

Recommendation: option 1, because it applies R8 as written and costs no run; options 2 and 3 are rule changes. The other fields, T, R9 and R10 are unaffected.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `gh run download <id>` fails on the runner artifacts**
- **Found during:** Task 1
- **Issue:** `docker/build-push-action` uploads `*.dockerbuild` artifacts that are not valid zips, so `gh run download <id> -D DIR` exits 1 before writing the oper artifacts.
- **Fix:** `gh run download <id> -p 'oper-*' -D DIR` (the same oper artifacts); documented in RESULTS. No harness code changed, so nothing goes in the protocol's "Harness fixes" list.
- **Commit:** 7e7d7e6

**2. [Rule 1 - Design] `confirm_points` takes the decision only**
- **Issue:** the plan names `confirm_points(decisions, walls_spec, down_spec)`, but cells ok at 250 turns have no point in the walk-down file, so it cannot supply the 60 cells at T.
- **Fix:** below 250 turns the cells are built by the constructor that `walls` and the walk-down share; at 250 and 260 the walls points are copied verbatim with their `lift`.
- **Commit:** beb2437

**3. Process notes.** Tests and code are one commit (`beb2437`) because the hook runs `make verify` and a failing RED commit cannot land. The margin got its own docs commit (7ce2080) so the later `walls-down.json` commit follows its RESULTS record. The commit trailer is `Claude Sonnet 5.5`, as the session's attribution instruction says, not the `Claude Opus 5.5` named in the resume message. The pre-commit `make verify` run failed once on `tests/test_pool.py::test_a_request_queued_behind_a_build_keeps_its_own_full_timeout` (a timing test, filed as debt in 1af9160) and passed on retry, twice in this plan; no `--no-verify`.

**Total deviations:** 2 auto-fixed, 1 note. **Impact:** none on any figure.

## Authentication Gates

None.

## Known Stubs

None.

## Threat Flags

None.

## Issues Encountered

- The SDK commit helper's 30 s timeout killed `git commit` mid-hook once and the pre-commit framework restored the owner's stashed `.planning/state.json` when its run ended; no owner file was staged, committed or lost.
- The nut `d` confirm reading above; no other issue.

## Next Phase Readiness

Plan 07-06 can proceed. Plan 07-07 needs the owner's answer on nut `d` before it writes the field ceilings; T (90), `MIN_TAIL_MM` (1e-4), `MIN_ROOT_RADIUS_MM` (1e-2, rods) and the other field ceilings are confirmed and recorded.

## Self-Check: PASSED

Files and record directories listed under key-files exist; commits 7e7d7e6, beb2437, 5ef2b1d, 7ce2080, 4dd60e1, d4233bc, daeafeb, 8992e1c and b23bbf6 are ancestors of HEAD; `python -m bench.oper_sets --check` exits 0; RESULTS has the `### D-19 margin and R6 charges`, `### candidate walls (before the confirm)` and `### walls-confirm, run ` headings; `walls-confirm.json` has reps 5, `sum(shard_sizes) == len(points)` and sources; 120 R7 points (60 `turns90-`, 60 `turns100-`); both `beyond-` points carry a `lift`; the commit adding `walls-confirm.json` (8992e1c) comes after the commit recording the walk-down (d4233bc).
