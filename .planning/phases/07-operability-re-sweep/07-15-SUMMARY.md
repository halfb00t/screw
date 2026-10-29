---
phase: 07-operability-re-sweep
plan: 15
subsystem: testing
tags: [operability, runs-ii, contention, load, gzip, arenas, outband, envelope, G28, G29, R11, R12, R14, R15, R19, R23, R27]
status: stopped-for-owner   # Task 3 halted at its G28/G29 stop (R11); not complete

requires:
  - phase: 07-operability-re-sweep
    provides: "07-06 bench.oper_bound and the Runs II point kinds; 07-08 bench.oper_load; 07-11 calc/cost.py and emit-constants; 07-12 the cap; quick 261029-mik (G28 bands) and 261029-rxk (MIN_FITTED_TURNS)"
provides:
  - "bench.oper_sets: tier_order, candidates, bound_sets, bound_points, load_mix, load_points, gzip_points, arena_points, head_ratio_points, turns_points, load_table, envelope_check; CLI runs2, load-table, envelope-check"
  - "bench.oper: the optional `envelope` header of a point file"
  - "bench/results/phase-07/tier-order.json (D(A) steps 1 to 4) and bench/points/{bound,load,gzip,arenas,outband}.json, each with its envelope and sources, checked by --check"
  - "runner records of all five sets under bench/results/phase-07/ and `## Phase 7 Runs II` in bench/RESULTS.md"
affects: [07-16]

estimate:
  tokens: 140000
  tasks: 3
actuals:
  tokens: 30950      # chars/4 over the authored added lines (123802 chars), generated point files and records excluded
  tasks: 2           # Tasks 1 and 2 done; Task 3 step 1 done, step 2 stopped at G28/G29, step 3 not reached
  commits: 12        # MEASURED: git rev-list --count 97d33cc..01eecff (this SUMMARY's commit not counted)
plan_head_before: 97d33cce511273dee04d4e81bc6bea96cc909ea3
plan_head_after: 01eecffc786e5e6087fa55df913670cb82788bd9

tech-stack:
  added: []
  patterns:
    - "a Runs II file records the envelope it was drawn under; --check regenerates it under that envelope and refuses a recorded e above the shipped one, so a widening never redraws a set (G6)"
    - "set generators take the envelope and the budget as parameters and admit with the shipped cost.predict, so the tests steer them without a stub cost module"

key-files:
  created:
    - bench/results/phase-07/tier-order.json
    - bench/points/bound.json
    - bench/points/load.json
    - bench/points/gzip.json
    - bench/points/arenas.json
    - bench/points/outband.json
    - bench/results/phase-07/bound-40907549180/
    - bench/results/phase-07/load-40909724292/
    - bench/results/phase-07/gzip-40909739628/
    - bench/results/phase-07/arenas-40909754190/
    - bench/results/phase-07/outband-40909768713/
  modified:
    - bench/oper.py
    - bench/oper_sets.py
    - tests/test_oper.py
    - tests/test_oper_followup.py
    - tests/test_oper_load.py
    - bench/RESULTS.md
    - docs/tech_debt/active/2026-10-29-cost-model-admits-out-of-fit-head-heights.md
    - docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md

key-decisions:
  - "G28/G29 stop (R11): 7 (point, target) pairs of outband run 40909768713 read above their enveloped prediction; no e is widened and the envelope check over the Runs II readings is not run; the owner rules"
  - "The far point of G28 takes the first value on the form step at or above 10 x the high edge x d"
  - "tier-order.json names one source, the explore point file: R27 steps 1 to 4 read predictions and file order, no reading"

requirements-completed: []   # OPER-01, OPER-02 and OPER-03 advance; none is wholly done

metrics:
  duration: "commits from 15:55Z to 16:59Z on 2026-10-29 (about 1 h, the runner time inside it), after the reading and design work"
  completed: 2026-10-29
---

# Phase 7 Plan 15: Runs II, stopped at the G28/G29 out-of-band check Summary

**All five Runs II sets ran on the runner at 5 repetitions and are committed with a RESULTS
section: bound 40907549180, load 40909724292, gzip 40909739628, arenas 40909754190 and outband
40909768713. The G28/G29 out-of-band check then found 7 (point, target) pairs above their enveloped
prediction, all at the M2 rows at stl-fine. R11 and G28 stop the phase there for the owner: no e is
widened, the envelope check is not run, and fit.json and `calc/cost.py` are unchanged.**

## Commits

| # | sha | subject |
| --- | --- | --- |
| 1 | c28c768 | feat(bench): fix R27's ordered candidates before the Runs II sets (07 D-12) |
| 2 | 98c62ad | feat(bench): generate the Runs II bound, load and gzip sets from the admitted space (07 D-03, D-09) |
| 3 | 4584d12 | feat(bench): generate R23's arena readings (07 D-02) |
| 4 | f730ecb | feat(bench): generate G28's out-of-band head-ratio points (07 G28) |
| 5 | 6cf6f39 | feat(bench): a per-N table of the load readings (07 D-03) |
| 6 | 9e47eb1 | feat(bench): an envelope check over the readings R12 lets widen it (07 D-07) |
| 7 | 300e440 | test(bench): keep the fake load server's handler errors off stderr |
| 8 | f080236 | docs(bench): add the phase 7 Runs II bound and arena records (runs 40907549180, 40909754190) |
| 9 | 61e6077 | docs(bench): add the phase 7 Runs II load, gzip and out-of-band records (runs 40909724292, 40909739628, 40909768713) |
| 10 | fef28d1 | docs(bench): record the phase 7 Runs II bound, load, gzip and arena sets (07 D-02, D-03, D-09) |
| 11 | 14093ac | docs(bench): record the G28 and G29 out-of-band check, which stops the phase (07 G28, G29) |
| 12 | 01eecff | docs(bench): give the M2 nut's own readings in the out-of-band context |

This SUMMARY lands in its own docs commit after these.

## The runs

| set | run | sha | jobs | readings | statuses |
| --- | --- | --- | --- | --- | --- |
| bound | 40907549180 | 98c62ad | 20 (4 shards x 5) | 300 | ok 250, refused 50 |
| load | 40909724292 | f730ecb | 5 | 15 | ok 15 |
| gzip | 40909739628 | f730ecb | 5 | 70 | ok 60, refused 10 |
| arenas | 40909754190 | f730ecb | 5 | 30 | ok 30 |
| outband | 40909768713 | f730ecb | 10 (2 shards x 5) | 300 | ok 300 |

Every job of every run succeeded on its first attempt, so no `gh run rerun` was needed. Every point
has repetitions 1 to 5 each once. The CPU models per job are in each RESULTS subsection.

## What was built

1. **D(A) first (R27, G6).** `tier_order` gives, per artifact, the candidates (admitted explore
   points in file order, deduplicated by kind and params as JSON), the edge ranking (largest edge
   ratio first, a tie to the label) and the draw (`random.Random(20261026).shuffle`, a new
   generator per artifact). `tier-order.json` was committed in c28c768, before `load.json`
   (98c62ad). It has 411, 404 and 439 candidates at stl-preview, stl-fine and step, which are
   B-01's admitted counts.
2. **The sets.** Each file records `envelope` and `sources`, carries R6 `shard_sizes`, and is
   regenerated byte for byte by `--check`:
   - `bound.json` (R14): 7, 7 and 6 bound points; 60 contention readings in shards of 17, 17, 17
     and 9. The tracer gate passed on shard 4's first record: ok builds on the named slots and
     integer peaks.
   - `load.json` (R15): N 1, 2 and 3, Q = C = 2N, `solid_cache` 4, bodies at N = 1 only, one mix
     of 60 distinct cold requests.
   - `gzip.json` (R19): the 14 STL bound points at levels 1, 6 and 9.
   - `arenas.json` (R23, G17): Z(A) with the trim on and off.
   - `outband.json` (G28, G29): 60 points. Far points exist for bolt k and nut s only.
3. **`load-table`** prints the per-N figures of a load run. A non-ok reading, and every repetition
   of an incomplete point, prints no figure.
4. **`envelope-check`** applies R12 to the cold isolated readings only: part, gzip and arena
   readings, contention at N = 1, and drift build 1. Load, outband and N = 2 or 3 contention
   readings are skipped. Where a reading exceeds its envelope, it raises the factor 1 + e by ulps
   and writes only the widened models' `envelope` and a `widened_by` list. It stops (exit 3) and
   writes nothing when the widened envelope would refuse a catalogue row or a default part.
   **Built and tested, but not run over the Runs II records, because the G28 check stopped
   first.**

## G28/G29 outcome per point (outband run 40909768713)

Each point's largest actual / (`cost.predict` x (1 + e)) over its 5 repetitions and 3 targets:

| point | artifact | worst target | largest actual / enveloped | outcome |
| --- | --- | --- | --- | --- |
| outband-bolt-k-below-iso4017:M20x160 | stl-preview | bytes | 0.3957 | within |
| outband-bolt-k-below-iso4017:M2x4 | stl-preview | peak | 0.2945 | within |
| outband-bolt-k-above-iso4017:M18x180 | stl-preview | bytes | 0.3923 | within |
| outband-bolt-k-above-iso4017:M2x4 | stl-preview | peak | 0.3087 | within |
| outband-bolt-k-far-iso4017:M2x4 | stl-preview | peak | 0.3091 | within |
| outband-bolt-k-below-iso4017:M20x100 | stl-fine | bytes | 0.4989 | within |
| outband-bolt-k-below-iso4017:M2x4 | stl-fine | bytes | 0.3113 | within |
| outband-bolt-k-above-iso4017:M18x150 | stl-fine | bytes | 0.5488 | within |
| outband-bolt-k-above-iso4017:M2x4 | stl-fine | bytes | 0.4286 | within |
| outband-bolt-k-far-iso4017:M2x4 | stl-fine | bytes | 0.4286 | within |
| outband-bolt-k-below-iso4017:M20x150 | step | peak | 0.6461 | within |
| outband-bolt-k-below-iso4017:M2x4 | step | peak | 0.6015 | within |
| outband-bolt-k-above-iso4017:M16x130 | step | peak | 0.6656 | within |
| outband-bolt-k-above-iso4017:M2x4 | step | peak | 0.6508 | within |
| outband-bolt-k-far-iso4017:M2x4 | step | peak | 0.6495 | within |
| outband-bolt-s-below-iso4017:M20x200 | stl-preview | bytes | 0.4094 | within |
| outband-bolt-s-below-iso4017:M2x4 | stl-preview | peak | 0.7193 | within |
| outband-bolt-s-above-iso4017:M4x25 | stl-preview | bytes | 0.2327 | within |
| outband-bolt-s-above-iso4017:M2x4 | stl-preview | bytes | 0.3192 | within |
| outband-bolt-s-below-iso4017:M20x200 | stl-fine | bytes | 0.6040 | within |
| outband-bolt-s-below-iso4017:M2x4 | stl-fine | bytes | 0.8848 | within |
| outband-bolt-s-above-iso4017:M10x50 | stl-fine | bytes | 0.6421 | within |
| outband-bolt-s-above-iso4017:M2x4 | stl-fine | bytes | 0.7451 | within |
| outband-bolt-s-below-iso4017:M16x160 | step | peak | 0.7031 | within |
| outband-bolt-s-below-iso4017:M2x4 | step | peak | 0.8262 | within |
| outband-bolt-s-above-iso4017:M18x120 | step | peak | 0.6109 | within |
| outband-bolt-s-above-iso4017:M2x4 | step | peak | 0.7407 | within |
| outband-nut-s-below-iso4032:M20 | stl-preview | bytes | 0.7051 | within |
| outband-nut-s-below-iso4032:M2 | stl-preview | bytes | 0.9722 | within |
| outband-nut-s-above-iso4032:M20 | stl-preview | bytes | 0.6324 | within |
| outband-nut-s-above-iso4032:M2 | stl-preview | bytes | 0.8618 | within |
| outband-nut-s-far-iso4032:M2 | stl-preview | seconds | 0.7859 | within |
| outband-nut-s-below-iso4032:M20 | stl-fine | bytes | 0.6037 | within |
| outband-nut-s-below-iso4032:M2 | stl-fine | seconds | 1.3200 | **over** |
| outband-nut-s-above-iso4032:M20 | stl-fine | bytes | 0.5828 | within |
| outband-nut-s-above-iso4032:M2 | stl-fine | seconds | 1.0696 | **over** |
| outband-nut-s-far-iso4032:M2 | stl-fine | seconds | 1.1255 | **over** |
| outband-nut-s-below-iso4032:M16 | step | bytes | 0.7204 | within |
| outband-nut-s-below-iso4032:M2 | step | seconds | 0.8467 | within |
| outband-nut-s-above-iso4032:M16 | step | bytes | 0.7204 | within |
| outband-nut-s-above-iso4032:M2 | step | bytes | 0.8084 | within |
| outband-nut-s-far-iso4032:M2 | step | bytes | 0.7977 | within |
| outband-nut-m-below-iso4032:M20 | stl-preview | bytes | 0.6582 | within |
| outband-nut-m-below-iso4032:M2 | stl-preview | bytes | 0.9229 | within |
| outband-nut-m-above-iso4032:M20 | stl-preview | bytes | 0.8134 | within |
| outband-nut-m-above-iso4032:M2 | stl-preview | bytes | 0.8529 | within |
| outband-nut-m-below-iso4032:M20 | stl-fine | bytes | 0.6008 | within |
| outband-nut-m-below-iso4032:M2 | stl-fine | seconds | 1.2217 | **over** |
| outband-nut-m-above-iso4032:M20 | stl-fine | bytes | 0.6178 | within |
| outband-nut-m-above-iso4032:M2 | stl-fine | peak | 0.8507 | within |
| outband-nut-m-below-iso4032:M16 | step | bytes | 0.7740 | within |
| outband-nut-m-below-iso4032:M2 | step | seconds | 0.8353 | within |
| outband-nut-m-above-iso4032:M16 | step | bytes | 0.6812 | within |
| outband-nut-m-above-iso4032:M2 | step | seconds | 0.7221 | within |
| turns-below-iso4017:M20x40 | stl-preview | bytes | 0.4352 | within |
| turns-below-iso4017:M2x4 | stl-preview | bytes | 0.4913 | within |
| turns-below-iso4014:M20x200 | stl-fine | bytes | 0.5814 | within |
| turns-below-iso4017:M2x4 | stl-fine | bytes | 1.3116 | **over** |
| turns-below-iso4017:M20x40 | step | peak | 0.8464 | within |
| turns-below-iso4017:M2x4 | step | peak | 0.9045 | within |

**Over the envelope (7 pairs, 20 readings):**

| point | target | ratio |
| --- | --- | --- |
| nut s/d below, M2, stl-fine | seconds | 1.3200 |
| nut s/d below, M2, stl-fine | peak | 1.0260 |
| nut s/d above, M2, stl-fine | seconds | 1.0696 |
| nut s/d far, M2, stl-fine | seconds | 1.1255 |
| nut m/d below, M2, stl-fine | seconds | 1.2217 |
| nut m/d below, M2, stl-fine | peak | 1.0004 |
| G29 `turns-below-iso4017:M2x4`, stl-fine (thread_length 1.0, 2.5 built turns) | bytes | 1.3116, all 5 repetitions |

Every nearest-the-budget point, and every point at stl-preview and step, is within its envelope.
The largest actual, the enveloped prediction and the repetitions above it are in `bench/RESULTS.md`,
`### out-of-band check`.

## Needs the owner: the G28/G29 stop (R11)

**Trigger.** R11's G28 and G29 sentences say: "a reading above its enveloped prediction stops the
phase for the owner and does not widen `e`." 7 pairs did, so Task 3 stopped at step 2. Steps 2b
(the envelope check) and 3 did not run, and fit.json and `calc/cost.py` are unchanged.

**Evidence that bears on the choice.** All figures are computed by committed code from committed
records; none is written to a file.

- The nut overruns sit where the prediction is the in-band one. `outband-nut-m-below-iso4032:M2`
  is predicted one float below the in-band `iso4032:M2` row: m 1.5 is judged at the low edge,
  0.7999999999999999 x d. Its fine STL read a 1.5275 s cold wall in explore 40646117094, against
  an enveloped 2.2918 s. Its own five stl-fine readings are 2.682, 2.423, 2.800, 1.701 and 2.033 s,
  the first three above that prediction. This points at the spread of repeated cold readings at the
  cheap end of the fine STL, more than at the below-band assumption. ASSUMPTION: the in-band M2 nut would overrun the same way at 5
  repetitions; it was not read here.
- The G29 miss is an extrapolation miss. A 1 mm thread on the 4 mm M2 bolt keeps 3 mm of
  tessellated shank, and the model, fitted on 3 turns and up, does not see it.
- These are the cheapest parts: 3.15 s against the 94.43 s stl-fine budget, and 1446684 bytes
  against 239508059 bytes.
- What a widening would do (`envelope_check` over the outband readings, then `_admits_all`,
  computed and not written):

  | model | e now | e covering the outband readings | refuses |
  | --- | --- | --- | --- |
  | nut stl-fine seconds | 1.1069417227945801 | 1.7812452161769916 | nothing B-01 keeps |
  | nut stl-fine peak | 0.5571452809681212 | 0.5976833077470993 | nothing B-01 keeps |
  | bolt stl-fine bytes | 0.5633622849303941 | 1.0504847478595214 | 6 catalogue rows at stl-fine, among them iso4017:M16x150, M16x160, M18x180 and M20x160 (C1 sets the budget at the largest catalogue prediction, so any bolt stl-fine bytes widening refuses its top rows) |

**Options.**

1. **Widen the two nut models, and guard G29 (recommended).** Rule that these out-of-band nut
   readings widen e like cold isolated readings, which changes R11/G28's "does not widen". The
   nut stl-fine seconds and peak then cover them, and B-01's set does not move. For G29, rule that
   a bolt whose built thread is below `cost.MIN_FITTED_TURNS` is refused at the cost rule (a
   B-02 `over_budget` 422, or a wall in L20), since no reading supports its prediction. Then
   continue 07-15 Task 3 over the other Runs II readings.
2. **Accept and record.** Rule that these overruns, far below every budget, are recorded in L21 as
   the model's known error at the cheap end, widen nothing, and continue Task 3. Faster, but it
   leaves a measured under-prediction in the shipped rule.
3. **Widen all three models from these readings.** The bolt stl-fine bytes widening refuses 6
   catalogue rows, so B-01 (C1) has to be re-ruled or its budget recomputed before Task 3. That
   is the most change.

Recommendation: option 1. It keeps B-01 as ruled, and it leaves no admitted part whose cost no
reading covers. Waiting for the owner.

## Also for the owner (not a stop of this plan)

- **Two kernel-refused nuts sit in the stl-preview bound set.** `nut-d30-p0.35-m0.8d-s4d-c0.15-right`
  and `nut-d30-p0.35-m0.8d-s1.6d-c0.15-left` are admitted, and R14 asks for an ok explore reading
  only for its two measured choices. They entered as P (5 slowest) and as the N = 3 partner of four
  other P. Every reading that built them was refused (`BuildError`, the lead-in countersink): 50
  bound and 10 gzip readings. Under R3 those (P, N) have no max. 07-16 meets this when it takes the
  stl-preview bound point at the picked N (four of seven P have no N = 3 max), R16's W (two P have
  no N = 1 reading) and R19 (two stl-preview gzip points have no max, which G22 makes a stop).
  Recorded in `docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md`.

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 3 - Blocking] A cross-test stderr leak failed the gate on every records commit.**
- **Found during:** Task 2, the bound and arenas records commit.
- **Issue:** the pre-commit `make verify` failed twice in a row with
  `1 failed, 4459 passed`. The test was
  `tests/test_records.py::test_a_model_request_emits_one_export_served_line_that_json_loads_round_trips`,
  which raised `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)` on a
  stderr line of 40 dashes. That line is `socketserver`'s `handle_error` banner: the fake load
  server in `tests/test_oper_load.py` hit an error after its test ended, and the banner reached a
  later test's capture. `tests/test_oper_load.py tests/test_records.py -n0` fails the same way
  at 97d33cc, in a scratch worktree, so it was there before this plan.
- **Fix:** the fake server keeps the error instead of printing it.
- **Commit:** 300e440, in its own commit, as 07-13 did for its isolation bug.

**2. [Process] A mixed commit was split before it was pushed.** The first commit of that fix also
picked up the record directories, which were still staged from the failed attempts. I split it with
`git reset --soft HEAD~1` (unpushed; no working-tree change) and committed the fix and the records
separately.

**3. [Binding note] Records committed in their own commits before use.** The plan bundles records
with RESULTS. The orchestrator's note asks for each set's records to be committed before they are
used, so f080236 and 61e6077 precede the RESULTS commit fef28d1.

**4. [Plan wording] `envelope_check` uses `cost.predict`, not the fit's own predict.**
`bench.oper_fit` imports `bench.oper_sets`, so the reverse import would be circular. The two agree
bit for bit (07-11's test), and the e values come from fit.json.

**5. [Interpretation] Where the plan's choice was mine.**
- `tier-order.json`'s only source is the explore point file.
- The G28 far point takes the first value on the form step at or above 10 x the high edge x d.
- Outband points carry no `preset`: their fields are not the row's.

### TDD evidence

Each task's tests were run against HEAD's sources swapped in, then restored:

| commit | tests | result at HEAD's sources |
| --- | --- | --- |
| c28c768 | the new Runs II tests | 23 failed, 3 errors |
| 6cf6f39 | `load_table` | 2 failed |
| 9e47eb1 | envelope check | 4 failed |

GREEN was every commit's pre-commit `make verify`.

## Known Stubs

None.

## Threat Flags

None beyond the plan's register:
- **T-07-37:** each set is generated by code and checked by regeneration.
- **T-07-63:** each set records its envelope, and `--check` refuses a recorded e above the shipped one.
- **T-07-64:** one partner per slot, and an empty slot is a stop.
- **T-07-38:** the widening path is built, with its B-01 guard, and was not run.

## Debt

- Updated, still active:
  - `docs/tech_debt/active/2026-10-29-cost-model-admits-out-of-fit-head-heights.md` (the 07-15
    readings).
  - `docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md` (seen again in Runs II).
- None filed, none resolved. The head-height item resolves only when every outband reading is
  within its envelope.
- Not done: the plan's move of the head-height item to `resolved/`.

## Self-Check: PASSED

- Found: `bench/results/phase-07/tier-order.json`, the five point files under `bench/points/`, and
  the five record directories under `bench/results/phase-07/`.
- The 12 commits of the table are ancestors of HEAD.
- `.venv/bin/python -m bench.oper_sets --check` exits 0.
- D(A) came first: `tier-order.json`'s last commit, c28c768, is an ancestor of `load.json`'s, 98c62ad.
- `tests/test_oper_followup.py`: 123 passed (`-n0 --no-cov`).
- The Task 2 verify loop finds a records directory and a `### <set>, run ` subsection for all five
  sets.
- Three RESULTS figures were checked against the raw records:
  - load-n3 rep 2 p95 all: 69.784, from 69.78429913074984.
  - `iso4017:M20x200-n1` stl-preview median build: 4.792, from 4.791720593999997.
  - Arena stl-fine trim-on max peak: 1445138432.
