---
phase: 07-operability-re-sweep
plan: 16
subsystem: testing
tags: [operability, runtime, timeouts, mem_limit, drift, plateau, solid-cache, arenas, R14, R16, R17, R18, R19, R20, R21, R22, R23, R24, R25, R26, G7, G8, G9, G11, G15, G16, G17, G18, G20, G31, G32]
status: complete

requires:
  - phase: 07-operability-re-sweep
    provides: "07-15 Runs II records and point files (bound, load, gzip, arenas, bound-rerun, gzip-rerun), the shipped envelope with the G30 widening (54965a0), L22"
provides:
  - "bench.oper_sets: read_runs, matched, Read, gzip_level, export_cache, tmpfs_base, tmpfs_inside, per_workers, Workers, timeouts, queue_depth, retry_after, minimum_size, screw_workers, healthcheck, derivation, runtime, derive_runtime, runtime_text; CLI derive-runtime"
  - "bench.oper_sets: drift_points (K = 20 or 60), solid_cache_points, build_drift, build_solid_cache, --check of all three sets; CLI drift [--k 60], solid-cache"
  - "bench.oper_sets: solid_cache (R22, G20), arenas (G17), drift, plateau and drift_peak (R23, G32); CLI check-r22-r23"
  - "bench/results/phase-07/runtime.json: every value R14 to R26 decide, stage two included, tied by tests/test_runtime_bounds.py"
  - "calc.cost.BUILD_TIMEOUT_S: 26, 71 and 26 s, measured (bound run 40907549180)"
  - "bench/points/drift.json, drift-60.json, solid-cache-4.json and their records (runs 41016507364, 41022812680, 41016510597)"
  - "07-SWEEP-PROTOCOL.md R16 and R23 amended by the owner's ruling G32"
affects: [07-17, 07-18, 07-21]

estimate:
  tokens: 140000
  tasks: 3
actuals:
  tokens: 30689      # chars/4 over the added lines of oper_sets.py, the three test files, cost.py, RESULTS.md and the three protocol/ruling files (122754 chars); records, point files and runtime.json excluded
  tasks: 3
  commits: 12        # MEASURED: git rev-list --count 8a258d9..3aac686 (includes the stop SUMMARY 12f61f2; this SUMMARY's commit not counted)
plan_head_before: 8a258d9854f220e30e9367e29dda118b8401efd2
plan_head_after: 3aac68694ef6edb256be22a63c950bd96263d6ec

tech-stack:
  added: []
  patterns:
    - "runtime.json is a test-pinned output: tests/test_runtime_bounds.py compares it byte for byte with derive-runtime over every committed directory, and the shipped timeouts with it"
    - "the derivation is a generator of the values in order, so a read-only command can print what is derived before a stop fires, while derive-runtime writes only a whole result"
    - "readings are matched to committed points by every identity field the point carries (members included), each point from exactly one run"
    - "a ruled criterion is committed to the protocol and to code before the reading it judges is dispatched (R30)"

key-files:
  created:
    - bench/results/phase-07/runtime.json
    - tests/test_runtime_bounds.py
    - bench/points/drift.json
    - bench/points/drift-60.json
    - bench/points/solid-cache-4.json
    - bench/results/phase-07/drift-41016507364/
    - bench/results/phase-07/drift-60-41022812680/
    - bench/results/phase-07/solid-cache-4-41016510597/
  modified:
    - bench/oper_sets.py
    - tests/test_oper_followup.py
    - tests/test_oper.py
    - src/screw/calc/cost.py
    - bench/RESULTS.md
    - .planning/phases/07-operability-re-sweep/07-SWEEP-PROTOCOL.md
    - .planning/phases/07-operability-re-sweep/07-GAP-RULINGS.md
    - .planning/phases/07-operability-re-sweep/07-OWNER-RULINGS.md

key-decisions:
  - "R16 picks N = 1: its max-over-reps p95 over all requests is 35.09 s against 51.88 s at N = 2 and 69.78 s at N = 3 (load run 40909724292); all three qualify"
  - "R14 at N = 1: timeouts 26 s (stl-preview), 71 s (stl-fine), 26 s (step), from bound run 40907549180; shipped in calc.cost.BUILD_TIMEOUT_S"
  - "R19 keeps gzip level 1; R21 export cache 240 MiB; R26 tmpfs 256 MiB; R17 queue depth 2; R20 minimum_size 4012; R24 SCREW_WORKERS 1; R25 --timeout 2 s, --start-period 10 s"
  - "R22 keeps K = 4 (W(4) 1652121600 B, run 41016510597); G17 keeps the trim (run 40909754190)"
  - "G32 (owner): R23's 20-build drift no longer stops alone; the 60-build plateau holds at every artifact (run 41022812680), so W takes the drift readings' largest peak, 1758363648 B, and max_tasks_per_child stays unset"
  - "shipped mem_limit 2415919104 B (2.25 GiB): from W and from W(4) alike at N = 1"

requirements-completed: []   # OPER-01 and OPER-02 advance; 07-21 and 07-17 ship the remaining values into the code and the container

metrics:
  duration: "06:22Z to 08:56Z on 2026-10-30, about 154 min, the owner's ruling and three runner reads inside it"
  completed: 2026-10-30
---

# Phase 7 Plan 16: the runtime values by rule, the measured timeouts, and R22/R23 under the owner's G32 Summary

**`derive-runtime` derives every runtime value the phase ships from committed runner records by the
pre-registered rules, R22 and R23 included. N = 1 is picked, the measured timeouts 26 / 71 / 26 s
ship in `calc/cost.py`, and K = 4 and the arena trim are kept. R23's 20-build drift was above its
allowance and stopped the plan for the owner. Under the owner's ruling G32, a 60-build drift run
showed the growth levels off at every artifact, so W takes its largest peak, 1758363648 B,
`max_tasks_per_child` stays unset, and the shipped mem_limit is 2415919104 B.**

## Commits

| # | sha | subject |
| --- | --- | --- |
| 1 | 5c7e231 | feat(bench): derive the runtime values from the runner records by R14 to R26 (07 D-02, D-03, D-09, D-11) |
| 2 | c2fd5fa | feat(app): per-artifact build timeouts measured on the runner (07 D-09, D-16) |
| 3 | d48130a | feat(bench): generate R23's drift and R22's W(K) sets from the derived timeouts (07 D-02) |
| 4 | 2dac3a8 | docs(bench): add the R22 W(4) and R23 drift records (runs 41016510597, 41016507364) |
| 5 | 378d58c | feat(bench): derive R22's solid cache, the arena release and R23's drift from the records (07 D-02) |
| 6 | 72e0b2d | docs(bench): record R22's W(K) and R23's drift runs (07 D-02) |
| 7 | 12f61f2 | docs(07-16): record the runtime derivation and its stop at R23's drift |
| 8 | dec5f7d | docs(07): record the owner's ruling G32 and amend R16 and R23 before the 60-build drift reading |
| 9 | b47e52c | feat(bench): generate R23's 60-build drift set and derive the plateau and W from it (07 G32) |
| 10 | e50358e | docs(bench): add the R23 60-build drift records (run 41022812680) |
| 11 | 84dfbec | feat(bench): derive the solid cache, the drift and the arena release from the runner (07 D-02) |
| 12 | 3aac686 | docs(bench): record R23's 60-build drift run, its plateau and the W it sets (07 G32) |

Commit 11 carries the plan's Task 3 subject. This SUMMARY lands in its own docs commit after them.
Everything is pushed to `origin/gsd/phase-07-operability-re-sweep`.

## Run ids per set

Stage one reads the existing records, matched by members (G31), each point from exactly one run:

| set | run(s) | used for |
| --- | --- | --- |
| bound + bound-rerun | 40907549180, 40999654995 | the contention W (R16), the timeouts (R14); every bound point has 5 ok repetitions from exactly one run |
| gzip + gzip-rerun | 40909739628, 40999657702 | R19's level, R21's G16 check |
| load | 40909724292 | B, mem_limit(N), qualification, the pick (R16); R17, R18, R20, R24, R25 |
| explore | 40646117094 | R21's candidates |
| arenas | 40909754190 | G17's trim comparison |
| every directory | all 18 | nproc 4 and the smallest MemTotal, 16758394880 B (R16); 254 headers |

Read by this plan, every job succeeded on its first run:

| set | run | dispatched at | jobs | readings | statuses |
| --- | --- | --- | --- | --- | --- |
| solid-cache-4 (R22, G9) | 41016510597 | d48130a | 5 | 5 | ok 5 |
| drift (R23, K = 20) | 41016507364 | d48130a | 5 | 15 | ok 15 |
| drift-60 (R23, G32) | 41022812680 | b47e52c | 5 | 15 | ok 15 |

## What was built

1. **`derive-runtime` (Task 1).** It applies the rules in the order their inputs exist (audit #4):
   R19, R21, R26, R16, R14 at the picked N, R17, R18, R20, R24 and R25. Then, after this plan's own
   runs, it applies R22 and R23 (stage two). Every stop is a `ProtocolStop`: exit 3, and nothing is
   written. `tests/test_runtime_bounds.py` pins runtime.json to `derive-runtime` over every
   committed directory, and `BUILD_TIMEOUT_S` to runtime.json.
2. **The timeouts.** `calc.cost.BUILD_TIMEOUT_S` is now `{"stl-preview": 26.0, "stl-fine": 71.0,
   "step": 26.0}`. The comment names R14, D-09's x2, the bound run, the picked N, D-14 and D-16.
3. **The R22 and R23 sets (Task 2).**
   - `drift` writes Z(A) per artifact. Z(A) is the committed bound set's point with the largest
     ok explore peak: the d 100 nut, the d 30 nut and `iso4017:M16x160`.
   - K = 20 by default. `--k 60` writes the G32 plateau set: the same parts in the same order,
     deadline 60 x the timeout (1560, 4260 and 1560 s, one shard).
   - `solid-cache --k K` writes the committed N = 1 mix with `solid_cache` K.
   - `--check` writes all three sets again from their sources.
4. **Stage two (Task 3).** Each value comes from its own function:
   - `solid_cache`: R22 and G20.
   - `arenas`: G17.
   - `drift`: R23's 20-build drift, kept as evidence.
   - `plateau`: G32. The worst repetition's rise from builds 21-40 to builds 41-60 must stay
     within 0.10 x the smallest build-1 peak of both drift readings. A miss stops the phase and
     names recycling as the next step.
   - `drift_peak`: the drift readings' largest peak, which W takes once the plateau holds.

   `derive-runtime` now runs the whole derivation. `check-r22-r23` prints the stage-two values as
   they are derived.

## The values (runtime.json)

| value | figure | evidence |
| --- | --- | --- |
| picked N | 1 | p95 max over reps: 35.09 s (N 1), 51.88 s (N 2), 69.78 s (N 3) |
| timeouts | 26 / 71 / 26 s | bound walls 12.72 s, 35.26 s, 12.81 s (run 40907549180) |
| W | 1758363648 B | 41022812680:drift-nut-d30-p1-m0.8d-s4d-c5-right rep 2 build 15; contention W 1533550592 B (40907549180) |
| B | 65208320 B | 40909724292:load-n1 rep 1 |
| export cache | 240 MiB | `iso4017:M20x200`, raw + gzip1 |
| tmpfs | 256 MiB | the stl-fine bytes budget x 1 |
| mem_limit(N) | 2415919104 / 4563402752 / 6442450944 B | N = 1 / 2 / 3, all qualify |
| solid_cache_k | 4 | W(4) 1652121600 B, run 41016510597 |
| shipped mem_limit (G20) | 2415919104 B | equal from W and from W(4) |
| arenas_kept | true | trim on lower at every artifact, run 40909754190 |
| recycling | unset | the plateau holds at every artifact (run 41022812680) |
| tessellation_kept | true | R23 |
| gzip level | 1 | level 6 and 9 fail at all 14 points |
| queue depth | 2 (2N) | largest wall / D-14 deadline 0.362 |
| Retry-After medians | 5.21 / 9.53 / 6.33 s | preview / fine / step |
| minimum_size | 4012 B | `/api/health` is the largest body that does not shrink |
| SCREW_WORKERS | 1 | health p95 0.0094 s |
| HEALTHCHECK | --timeout 2 s, --start-period 10 s | interval 30 s and retries 3 are Docker's defaults |

07-21 and 07-17 put these into the code and the container. 07-16 ships only the timeouts.

## The R23 stop and the owner's ruling G32

**The stop.** In drift run 41016507364, the drift was above its allowance at every artifact. The
drift is the peak after build 20 minus the peak after build 1; the allowance is 0.10 x the
smallest build-1 peak.

| artifact | drift | allowance |
| --- | --- | --- |
| stl-preview | 53616640 B | 44301516.8 B |
| stl-fine | 323194880 B | 137344204.8 B |
| step | 31100928 B | 28473344.0 B |

The plan stopped there (12f61f2).

**The ruling.** The owner replied "1 + longer drift run (Recommended)". It is recorded as G32 in
`07-GAP-RULINGS.md` and as a section of `07-OWNER-RULINGS.md`.

**The amendments.** R16 and R23 were amended in dec5f7d, each closing with the post-freeze
sentence, with no gap labels and no run ids. `tests/test_oper.py` pins the new text. The plateau
criterion went into the protocol (dec5f7d) and into the code (b47e52c) before drift-60 was
dispatched.

**The plateau.** It holds at every artifact (run 41022812680, worst repetition):

| artifact | builds 41-60 max minus builds 21-40 max | allowance |
| --- | --- | --- |
| stl-preview | 6467584 B (rep 4) | 44044697.6 B |
| stl-fine | 11583488 B (rep 1) | 134713753.6 B |
| step | 5222400 B (rep 4) | 28473344.0 B |

**W.** It takes the largest peak after any build of both drift readings: 1758363648 B, above the
20-build peak (1716760576 B) and the contention W.

**What moved.** As the ruling requires, I re-derived with committed code and `stage_two=True`.

- Unchanged:
  - the pick, N = 1;
  - the timeouts, 26 / 71 / 26 s;
  - R17's queue depth;
  - `python -m bench.oper_sets --check`, exit 0.
- mem_limit(N) rose:
  - N = 1: 2147483648 to 2415919104 B;
  - N = 2 and 3: by 536870912 B each.
- The shipped mem_limit is unchanged at 2415919104 B.

**The envelope.** No drift build 1, in either run, exceeds its envelope. fit.json, `calc/cost.py`,
L21 and L22 are untouched.

## Also for the owner

- **N = 1 is picked.** R16 ranks latency only, so one worker with a queue of 2 wins. Throughput
  is not part of the rule.
- **The timeouts are single-build walls.** At N = 1 the bound points ran with no partner. The
  cost.py comment says so.
- **I filled in one detail of the plateau allowance.** It is 0.10 x the smallest build-1 peak
  among the repetitions of both drift readings, so it is never more than the 20-build reading's
  own allowance. The ruling said "R23's existing allowance". For stl-preview this is 44044697.6 B,
  set by the 60-build rep 4, which is a little below the 20-build figure. The protocol and
  07-GAP-RULINGS.md state this choice, and with either reading the plateau holds by a wide
  margin.

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 3 - Blocking] The pre-commit gate saw an untracked test against the old constant.**
- **Found during:** Task 1, the first commit.
- **Issue:** pre-commit stashed the unstaged `cost.py` change but not the untracked
  `tests/test_runtime_bounds.py`, so the gate read `1 failed`.
- **Fix:** I moved the file to the scratchpad for commit 1 and restored it for commit 2, which
  ships it with the timeouts. The tree was never committed red.

**2. [Rule 1 - Bug] A test fixture lacked the stage-two point files.**
- **Found during:** Task 3, after wiring `derive_runtime` to stage two.
- **Issue:** `test_derive_runtime_exits_3_on_a_stop_and_writes_nothing` wrote only bound, gzip and
  load files, so the run ended in `FileNotFoundError` instead of the R14 stop.
- **Fix:** The fixture writes empty arenas, drift and drift-60 files as well (84dfbec).

### Interpretation and sequencing

**3. Task 1 is two commits.** The derivation and runtime.json come first (5c7e231), then the
timeouts and their test (c2fd5fa) with the plan's subject.

**4. runtime.json is re-derived in each records commit (2dac3a8, e50358e).** Stage one reads every
runner header, so only `sources` and `runner.headers` moved: 239 to 249, then 254. The records were
committed before any figure was taken from them.

**5. The R23 stop and G32.** Task 3 stopped at R23 as written (12f61f2, a CHECKPOINT). The owner's
ruling added:
- the protocol amendment (dec5f7d);
- the 60-build set and its run (b47e52c, e50358e);
- the RESULTS record (3aac686).

These are five more commits than the plan foresaw. The 20-build drift test was replaced by
plateau tests. The committed-records test now expects exit 0, with the drift above its allowance
and the plateau holding.

**6. A read-only command, `check-r22-r23`,** prints the stage-two values without writing anything.
Every figure in the stop report came from committed code over committed records.

**7. Choices the plan left to me.**
- The W(K) point is the committed N = 1 mix with `bodies` false.
- R25's `--start-period` reads the 5 picked-N readings (G18).
- R21 admits with `cost.fits`.
- G20's W(K) mem_limit goes through `per_workers` at the picked N.
- Every bound point must have 5 ok repetitions from exactly one run.

### TDD evidence

I ran each change's tests against the previous commit's sources, then restored the sources (`cmp`
checked):

| commit | tests | result at the earlier sources |
| --- | --- | --- |
| 5c7e231 / c2fd5fa | Task 1 behaviour and CLI | 39 failed, 129 passed; `test_runtime_bounds.py` errors at collection |
| d48130a | the drift and W(K) sets, their `--check` | 5 failed, 169 passed |
| 378d58c | R22, the drift, the arenas, stage two | 9 failed, 174 passed |
| b47e52c | the plateau, drift_peak, the 60-build set, W from the drift | 9 failed, 181 passed |
| 84dfbec | runtime.json stage two, the committed-records test | 3 failed, 191 passed |

GREEN was every commit's pre-commit `make verify`.

## Verification

- `make verify` (pre-commit) passed at every commit, the last at 3aac686. The final run is quoted
  in the plan report.
- `.venv/bin/python -m bench.oper_sets --check`: exit 0.
- Task 3's `<verify>`:
  - `make test PYTEST_ARGS="tests/test_oper_followup.py tests/test_runtime_bounds.py -q -n0
    --no-cov"`: 194 passed.
  - The runtime.json key check: exit 0.
- Task 3's acceptance:
  - `solid_cache_k` is 4, and `solid_cache.runs` is `["41016510597"]`.
  - The last task commit, 84dfbec, has the plan's subject.

## Known Stubs

None.

## Threat Flags

None beyond the plan's register:
- T-07-40: runtime.json and the timeouts are pinned to the records.
- T-07-65: every max comes from complete, all-ok points, or the run stops.
- T-07-66: the drift deadlines are 20 x and 60 x the timeout, and under 10500 s, which R6
  checks.

## Debt

- Filed: none.
- Still active: `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md`. Its timeout row is
  measured now. The other rows are consumed by 07-21 and 07-17.

## Self-Check: PASSED

- Found: runtime.json, test_runtime_bounds.py, drift.json, drift-60.json, solid-cache-4.json, and
  the three record directories.
- All 12 commits are ancestors of HEAD (3aac686) and are pushed.
- `check-r22-r23` on the committed records exits 0, and
  `test_the_committed_records_keep_4_solids_and_the_trim_and_count_the_drift_in_w` pins it.
