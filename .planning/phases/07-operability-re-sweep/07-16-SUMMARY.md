---
phase: 07-operability-re-sweep
plan: 16
subsystem: testing
tags: [operability, runtime, timeouts, mem_limit, drift, solid-cache, arenas, R14, R16, R17, R18, R19, R20, R21, R22, R23, R24, R25, R26, G7, G8, G9, G11, G15, G16, G17, G18, G20, G31]
status: stopped-for-owner   # Task 3 halted at R23's drift stop; not complete

requires:
  - phase: 07-operability-re-sweep
    provides: "07-15 Runs II records and point files (bound, load, gzip, arenas, bound-rerun, gzip-rerun), the shipped envelope with the G30 widening (54965a0), L22"
provides:
  - "bench.oper_sets: read_runs, matched, Read, gzip_level, export_cache, tmpfs_base, tmpfs_inside, per_workers, Workers, timeouts, queue_depth, retry_after, minimum_size, screw_workers, healthcheck, derivation, runtime, derive_runtime, runtime_text; CLI derive-runtime"
  - "bench.oper_sets: drift_points, solid_cache_points, build_drift, build_solid_cache, --check of both; CLI drift, solid-cache"
  - "bench.oper_sets: solid_cache (R22, G20), arenas (G17), drift and recycling (R23); CLI check-r22-r23"
  - "bench/results/phase-07/runtime.json: R14 to R21 and R24 to R26 (stage one), tied by tests/test_runtime_bounds.py"
  - "calc.cost.BUILD_TIMEOUT_S: 26, 71 and 26 s, measured (bound run 40907549180)"
  - "bench/points/drift.json and bench/points/solid-cache-4.json, and their records (runs 41016507364, 41016510597)"
affects: [07-17, 07-18, 07-21]

estimate:
  tokens: 140000
  tasks: 3
actuals:
  tokens: 23470      # chars/4 over the added lines of oper_sets.py, the two test files, cost.py and RESULTS.md (93879 chars); records and point files excluded
  tasks: 2           # Tasks 1 and 2 done; Task 3 step 1 and the code of step 2 done, runtime.json not finished: R23 stops
  commits: 6         # MEASURED: git rev-list --count 8a258d9..72e0b2d (this SUMMARY's commit not counted)
plan_head_before: 8a258d9854f220e30e9367e29dda118b8401efd2
plan_head_after: 72e0b2d250d73ae216297900b85b59893c6e8870

tech-stack:
  added: []
  patterns:
    - "runtime.json is a test-pinned output: tests/test_runtime_bounds.py compares it byte for byte with derive-runtime over every committed directory, and the shipped timeouts with it"
    - "the derivation is a generator of the values in order, so a read-only command can print what is derived before a stop fires, while derive-runtime writes only a whole result"
    - "readings are matched to committed points by every identity field the point carries (members included), each point from exactly one run"

key-files:
  created:
    - bench/results/phase-07/runtime.json
    - tests/test_runtime_bounds.py
    - bench/points/drift.json
    - bench/points/solid-cache-4.json
    - bench/results/phase-07/drift-41016507364/
    - bench/results/phase-07/solid-cache-4-41016510597/
  modified:
    - bench/oper_sets.py
    - tests/test_oper_followup.py
    - src/screw/calc/cost.py
    - bench/RESULTS.md

key-decisions:
  - "R16 picks N = 1: its max-over-reps p95 over all requests is 35.09 s against 51.88 s at N = 2 and 69.78 s at N = 3 (load run 40909724292); all three qualify"
  - "R14 at N = 1: timeouts 26 s (stl-preview), 71 s (stl-fine), 26 s (step), from bound run 40907549180; shipped in calc.cost.BUILD_TIMEOUT_S"
  - "R19 keeps gzip level 1 (level 6 keeps 95 to 96 % of level 1's bytes at every point); R21 export cache 240 MiB; R26 tmpfs 256 MiB; R16 mem_limit 2 GiB from W; R17 queue depth 2; R20 minimum_size 4012; R24 SCREW_WORKERS 1; R25 --timeout 2 s, --start-period 10 s"
  - "R22 keeps K = 4 (W(4) 1652121600 B, run 41016510597); G20's mem_limit is 2415919104 B; G17 keeps the trim (lower memory.current at every artifact, run 40909754190)"
  - "R23 stops the phase: drift run 41016507364 is above its allowance at all three artifacts; no recycling value and no R22 or R23 value is written"

requirements-completed: []   # OPER-01 and OPER-02 advance; R23 stops before runtime.json is complete

metrics:
  duration: "06:22Z to 07:31Z on 2026-10-30, about 69 min, the runner time inside it"
  completed: 2026-10-30
---

# Phase 7 Plan 16: the runtime values, the measured timeouts, and the stop at R23's drift Summary

**`derive-runtime` derives every stage-one runtime value from committed runner records by the
pre-registered rules. N = 1 is picked. The measured per-artifact timeouts (26 / 71 / 26 s) are
shipped and held to their records by a test. The R22 and R23 runs were generated from those
timeouts and read on the runner. R22 keeps K = 4 and G17 keeps the trim. But R23's drift is above
its allowance at every artifact, which stops the phase for the owner before runtime.json is
finished.**

## Commits

| # | sha | subject |
| --- | --- | --- |
| 1 | 5c7e231 | feat(bench): derive the runtime values from the runner records by R14 to R26 (07 D-02, D-03, D-09, D-11) |
| 2 | c2fd5fa | feat(app): per-artifact build timeouts measured on the runner (07 D-09, D-16) |
| 3 | d48130a | feat(bench): generate R23's drift and R22's W(K) sets from the derived timeouts (07 D-02) |
| 4 | 2dac3a8 | docs(bench): add the R22 W(4) and R23 drift records (runs 41016510597, 41016507364) |
| 5 | 378d58c | feat(bench): derive R22's solid cache, the arena release and R23's drift from the records (07 D-02) |
| 6 | 72e0b2d | docs(bench): record R22's W(K) and R23's drift runs (07 D-02) |

This SUMMARY lands in its own docs commit after these. Pushed to `origin/gsd/phase-07-operability-re-sweep`.

## Run ids per set

Stage one (runtime.json) reads the existing records. Matching is by members (G31), each point from
exactly one run:

| set | run(s) | used for |
| --- | --- | --- |
| bound + bound-rerun | 40907549180, 40999654995 | W (R16), the timeouts (R14); every bound point has 5 ok repetitions from exactly one run |
| gzip + gzip-rerun | 40909739628, 40999657702 | R19's level, R21's G16 check |
| load | 40909724292 | B, mem_limit(N), qualification, the pick (R16); R17, R18, R20, R24, R25 |
| explore | 40646117094 | R21's candidates |
| every directory | (all 17 now) | nproc 4 and the smallest MemTotal, 16758394880 B (R16) |

Read by this plan, both dispatched at d48130a, each job succeeded first time:

| set | run | jobs | readings | statuses |
| --- | --- | --- | --- | --- |
| solid-cache-4 (R22, G9) | 41016510597 | 5 | 5 | ok 5 |
| drift (R23) | 41016507364 | 5 | 15 | ok 15 |

The R22/R23 outcome also uses arenas run 40909754190 (07-15).

## What was built

1. **`derive-runtime` (Task 1).** It applies the rules in the order their inputs exist (audit #4):
   - R19 (G11, G15): each level's max bytes and seconds over 5 repetitions. Each point passes on
     its own, and level 9 is compared with the level adopted by then.
   - R21 (G16): candidates are explore parts that `cost.fits` admits and that read ok at all 3
     artifacts. Raw plus level-1 gzip bytes, in whole MiB. A level 6 or 9 reading above level 1
     is a stop.
   - R26: B-01's stl-fine bytes budget x N, rounded up to 256 MiB, and inside mem_limit.
   - R16 (G7): W, B, mem_limit(N), qualification and the pick. nproc must agree across every
     header.
   - R14: at the picked N.
   - R17 (G8): on the picked N's pool log, under the derived timeouts.
   - R18, R20, R24 and R25 (G18).

   Every stop is a `ProtocolStop`, exit 3, and nothing is written. Outputs:
   `bench/results/phase-07/runtime.json`, and `tests/test_runtime_bounds.py`, which compares that
   file with `derive-runtime` over every committed directory and compares `BUILD_TIMEOUT_S` with
   it.
2. **The timeouts.** `calc.cost.BUILD_TIMEOUT_S` is now `{"stl-preview": 26.0, "stl-fine": 71.0,
   "step": 26.0}`. Its comment names R14, D-09's x2, the bound run, the picked N, D-14 and D-16.
   The INTERIM note is gone.
3. **The R22 and R23 sets (Task 2).**
   - `drift` writes Z(A) per artifact: the committed bound set's point with the largest ok
     explore peak, K = 20, `deadline_s` 20 x the timeout. A deadline at or above 10500 s is an R6
     stop.
   - `solid-cache --k K` writes the committed R15 mix at N = 1 with `solid_cache` K.
   - `--check` writes both again from their sources.
   - The drift parts are the arena set's parts: the d 100 nut at 520 s, the d 30 nut at 1420 s
     and `iso4017:M16x160` at 520 s.
4. **Stage two (Task 3 code).**
   - `solid_cache`: R22 and G20.
   - `arenas`: G17.
   - `drift` and `recycling`: R23.
   - The tessellation is recorded as kept.

   All of these run inside `derivation(..., stage_two=True)`. `check-r22-r23` prints the values as
   they are derived. `derive-runtime` stays on stage one, so runtime.json holds no R22 or R23
   value until the owner rules.

## The stage-one values (runtime.json)

| value | figure | evidence |
| --- | --- | --- |
| picked N | 1 | p95 max over reps: 35.09 s (N 1), 51.88 s (N 2), 69.78 s (N 3) |
| timeouts | 26 / 71 / 26 s | `nut-d10-p0.35-m3d-s4d-c0.15-right` 12.72 s, `nut-d30-p1-m0.8d-s1.6d-c5-right` 35.26 s, `nut-d100-p3.5-m3d-s4d-c5-right` 12.81 s |
| W | 1533550592 B | 40907549180:nut-d30-p1-m0.8d-s1.6d-c5-right-n1 rep 1 |
| B | 65208320 B | 40909724292:load-n1 rep 1 |
| export cache | 240 MiB | `iso4017:M20x200`, 250654910 B raw + gzip1 |
| tmpfs | 256 MiB | the stl-fine bytes budget x 1 |
| mem_limit (from W) | 2147483648 B | at N = 1; N 2 and 3: 4026531840 and 5905580032 B |
| gzip level | 1 | level 6 and level 9 fail at all 14 points (bytes ratio 0.951 to 0.960) |
| queue depth | 2 (2N) | largest wall / D-14 deadline 0.362 |
| Retry-After medians | 5.21 / 9.53 / 6.33 s | 100 walls each (preview / fine / step) |
| minimum_size | 4012 B | `/api/health` (95 B to 98 B) is the largest body that does not shrink |
| SCREW_WORKERS | 1 | health p95 0.0094 s |
| HEALTHCHECK | --timeout 2 s, --start-period 10 s | max wall 0.736 s, time to healthy 0.958 s; interval 30 s and retries 3 are Docker's defaults |

07-21 and 07-17 put these into the code and the container. 07-16 ships only the timeouts.

## Needs the owner: the R23 drift stop

Drift run 41016507364 has all 5 repetitions `ok` at every artifact, with all 20 peaks. Here is
`check-r22-r23` on the committed records (exit 3). The drift is the max over repetitions of the
peak after build 20 minus the peak after build 1. The allowance is 0.10 x the smallest build-1
peak:

| artifact | drift | allowance | worst reading |
| --- | --- | --- | --- |
| stl-preview | 53616640 B | 44301516.8 B | 41016507364:drift-nut-d100-p3.5-m0.8d-s4d-c5-right rep 2 |
| stl-fine | 323194880 B | 137344204.8 B | 41016507364:drift-nut-d30-p1-m0.8d-s4d-c5-right rep 2 |
| step | 31100928 B | 28473344.0 B | 41016507364:drift-iso4017:M16x160 rep 3 |

R23 says that drift above its allowance "stops the phase and asks the owner, because no rule here
sets a recycling value". What the records show (per-repetition table in `bench/RESULTS.md`,
`### R22 and R23 (07-16)`):

- Most of each repetition's growth is the step from build 1 to build 2. At stl-fine rep 2 the
  peak goes 1373442048 B, then 1589825536 B after build 2, then 1696636928 B after build 20.
  After build 2 the peaks rise in small steps.
- Some peaks are still rising at the end. Stl-fine rep 1 rose at builds 18, 19 and 20, so growth
  past 20 builds is not excluded.
- The largest peak after build 20, 1716760576 B (stl-fine rep 1), is above both W (1533550592 B)
  and W(4) (1652121600 B). Those are the inputs of the two mem_limits G20 compares.

Options:

1. **Count the drift in the memory limit and keep recycling unset (recommended).** W also takes
   the largest peak after build K of the drift run (R16). The limit is then sized for a warm
   worker, and that replaces R23's allowance as the drift's test.
   - Rule change to R16 and R23. R23 now says drift "adds nothing to mem_limit".
   - Pro: it covers the growth that was measured, with no respawn cost, and it keeps the warm
     solid cache that affinity exists for.
   - Con: it assumes growth levels off. The records show a step and then a plateau within 20
     builds, but not beyond.
   - Under this ruling, `derive-runtime` re-derives mem_limit by committed code. It stops again
     if the pick or a timeout moves.
2. **Measure the allowance from build 2, the warm worker.** Keep 0.10, but compare build 20 with
   build 2.
   - Rule change to R23.
   - Pro: it separates the one-off first-build step from growth.
   - Con: the baseline would be chosen after the records show where the step is, which R30
     guards against. mem_limit stays below the drift run's peaks.
3. **Recycle workers.** Set `max_tasks_per_child`.
   - Needs a new rule for the value, and new runner readings of the respawn cost: the cold
     kernel import and the lost solid cache.
   - Pro: it bounds any growth.
   - Con: it is the largest change, and it goes against the pool's documented reason for leaving
     recycling unset.

Recommendation: 1. It favours stability: the limit is sized from measured warm-worker peaks, and
no new mechanism is added.

## Also for the owner (not a stop of this plan)

- **N = 1 is picked.** R16 ranks only the max-over-reps p95 over all requests, so one worker with
  a queue of 2 wins on latency (35.09 s against 51.88 s and 69.78 s). Throughput is not part of
  the rule. This is the rule as written, not a stop.
- **The timeouts are single-build walls.** At N = 1 the bound points ran with no partner, so
  "built beside one cold partner per worker" has no partner to name. The cost.py comment says
  so.
- **No drift build 1 widens e.** The envelope check over the drift and W(4) records is within
  every envelope, so orchestrator note 3's widening path was not needed. fit.json, L21 and L22
  are untouched.

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 3 - Blocking] The pre-commit gate saw an untracked test against the old constant.**
- **Found during:** Task 1, the first commit.
- **Issue:** pre-commit stashed the unstaged `cost.py` change but not the untracked
  `tests/test_runtime_bounds.py`, so the gate read `1 failed, 4513 passed`
  (`test_the_shipped_build_timeouts_are_the_derived_ones`).
- **Fix:** I moved the file to the scratchpad for commit 1 and restored it for commit 2, which
  ships it with the timeouts. The tree was never committed red.

### Interpretation and sequencing

**2. Task 1 is two commits.** The derivation and runtime.json come first (5c7e231). The timeouts
and their test follow (c2fd5fa), with the plan's subject, so `git log -1` matched it at the end of
Task 1. One concern per commit.

**3. runtime.json was re-derived in the records commit (2dac3a8).** The new directories add 10
runner headers. Stage one reads every header for nproc and the smallest MemTotal, so
`test_runtime_bounds` needed runtime.json re-derived in the same commit. Only `sources` and
`runner.headers` (239 to 249) moved. The records were committed before any R22 or R23 figure was
taken from them.

**4. Task 3 was stopped as R23 requires.**
- Committed: the stage-two code and its behaviour tests, and a read-only command,
  `check-r22-r23` (not in the plan). Every figure above therefore comes from committed code over
  committed records (orchestrator note 5).
- Not done: `derive-runtime` is not wired to stage two, runtime.json is not finished, and the
  plan's final subject, `feat(bench): derive the solid cache, the drift and the arena release
  from the runner (07 D-02)`, is not used. Wiring stage two would make `derive-runtime` exit 3 on
  the committed records, and `test_runtime_bounds` would fail.
- After the ruling, the wiring is one argument (`stage_two=True` in `derive_runtime`), plus the
  rule change itself.

**5. Choices the plan left to me.**
- The W(K) point is the committed N = 1 mix with `bodies` false. The JSON bodies are R20's, and
  `run_load` measures them after the end peak, so the peak is the same instrument.
- R25's `--start-period` reads the same 5 picked-N readings as its `--timeout` (G18). Over all 15
  load readings it is 10 s as well.
- R21 admits with `cost.fits`, which is the shipped rule and includes G30's turns refusal.
- R20 reads the bodies of every ok load reading. Only N = 1 measures them.
- G20's W(K) mem_limit goes through `per_workers`, with R16's own formula and qualification at the
  picked N.
- Orchestrator note 1: every bound point (all N) must have 5 ok repetitions from exactly one run,
  checked after the timeouts as an R14 stop. W and the timeouts check their own points first, with
  their own rule names.

### TDD evidence

Each task's tests were run against the previous commit's sources, then the sources were restored
(`cmp` checked):

| commit | tests | result at the earlier sources |
| --- | --- | --- |
| 5c7e231 / c2fd5fa | Task 1 behaviour and CLI (`test_oper_followup.py`) | 39 failed, 129 passed; `test_runtime_bounds.py` errors at collection (no `RUNTIME`) |
| d48130a | drift and W(K) sets, their `--check` | 5 failed, 169 passed |
| 378d58c | R22, R23 drift, arenas, stage two, the records test | 9 failed, 174 passed |

GREEN was every commit's pre-commit `make verify`. Each Task 1 tracer `<verify>` was re-run before
expanding: 170 passed.

## Verification

- `make verify` at 72e0b2d: `4529 passed in 203.87s`; ruff "All checks passed!"; mypy "Success:
  no issues found in 95 source files"; "Contracts: 10 kept, 0 broken."
- `.venv/bin/python -m bench.oper_sets --check`: exit 0.
- Task 1's acceptance:
  - `picked_workers` is 1.
  - `tmpfs_bytes` and every `mem_limit_bytes` mod 268435456 are 0.
  - `grep -n "30.0" src/screw/calc/cost.py | grep -c BUILD_TIMEOUT` prints 0.
  - Task 1's last commit has the plan's subject.
- Task 2's acceptance:
  - Each drift `deadline_s` is 20 x its timeout and under 10500.
  - The commit adding `drift.json` (d48130a) comes after c2fd5fa.
  - No `solid-cache-<k>.json` exists for k below 4.
  - `docs(bench): record R22's W(K) and R23's drift runs (07 D-02)` is 72e0b2d.
- Task 3's acceptance: not met, because of the R23 stop above.

## Known Stubs

None. runtime.json lacks R22 and R23 by design until the ruling. No consumer reads them yet: 07-21
does, and 07-21 depends on this plan.

## Threat Flags

None beyond the plan's register:
- T-07-40: runtime.json and the timeouts are pinned to the records by `test_runtime_bounds.py`.
- T-07-65: every max comes from complete, all-ok points, or the run stops.
- T-07-66: drift deadlines are 20 x the timeout and under 10500 s, checked as R6.

## Debt

- Filed: none.
- Still active: `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md`. Its timeout row is
  now measured; its workers, queue, caches, mem_limit, tmpfs, gzip and HEALTHCHECK rows are
  consumed by 07-21 and 07-17. It moves to resolved when those plans land.

## Self-Check: PASSED

- Found: runtime.json, test_runtime_bounds.py, drift.json, solid-cache-4.json, and both record
  directories.
- All six commits are ancestors of HEAD (72e0b2d) and are pushed.
- `check-r22-r23` on the committed records exits 3 with the R23 stop above.
  `test_the_committed_records_keep_4_solids_and_the_trim_and_stop_at_r23s_drift` pins it.
