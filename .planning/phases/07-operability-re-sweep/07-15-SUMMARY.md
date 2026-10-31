---
phase: 07-operability-re-sweep
plan: 15
subsystem: testing
tags: [operability, runs-ii, contention, load, gzip, arenas, outband, envelope, G28, G29, G30, G31, R11, R12, R14, R15, R19, R23, R27]
status: complete

requires:
  - phase: 07-operability-re-sweep
    provides: "07-06 bench.oper_bound and the Runs II point kinds; 07-08 bench.oper_load; 07-11 calc/cost.py and emit-constants; 07-12 the cap; quick 261029-mik (G28 bands) and 261029-rxk (MIN_FITTED_TURNS)"
provides:
  - "bench.oper_sets: tier_order, candidates, bound_candidates, bound_sets, bound_points, load_mix, load_points, gzip_points, arena_points, head_ratio_points, turns_points, unread, build_rerun, load_table, envelope_check, widens; CLI runs2, rerun, load-table, envelope-check"
  - "bench.oper: the optional `envelope` header of a point file"
  - "bench/results/phase-07/tier-order.json (D(A) steps 1 to 4) and bench/points/{bound,load,gzip,arenas,outband,bound-rerun,gzip-rerun}.json, each with its envelope and sources, checked by --check"
  - "runner records of all seven sets under bench/results/phase-07/ and `## Phase 7 Runs II` in bench/RESULTS.md, with the out-of-band check and the envelope check"
  - "calc.cost: below_fitted_turns, refused_fields, TURN_FIELDS; the nut stl-fine seconds and peak e widened by outband run 40909768713 (L22)"
affects: [07-16]

estimate:
  tokens: 140000
  tasks: 3
actuals:
  tokens: 45548      # chars/4 over the authored added lines (123802 chars to the stop, 58389 after it), generated point files and records excluded
  tasks: 3
  commits: 23        # MEASURED: git rev-list --count 97d33cc..54965a0 (this SUMMARY's commit not counted)
plan_head_before: 97d33cce511273dee04d4e81bc6bea96cc909ea3
plan_head_after: 54965a0916bd2f1ebeeefdeb4938dcbcfb3d72cf

tech-stack:
  added: []
  patterns:
    - "a Runs II file records the envelope it was drawn under; --check regenerates it under that envelope and refuses a recorded e above the shipped one, so a widening never redraws a set (G6)"
    - "set generators take the envelope and the budget as parameters and admit with the shipped cost.predict, so the tests steer them without a stub cost module"
    - "a rerun file is the points of a regenerated set that no reading of the earlier run is of, matched on every identity field the point carries (contention members included), and --check regenerates it from both sources"

key-files:
  created:
    - bench/results/phase-07/tier-order.json
    - bench/points/bound.json
    - bench/points/load.json
    - bench/points/gzip.json
    - bench/points/arenas.json
    - bench/points/outband.json
    - bench/points/bound-rerun.json
    - bench/points/gzip-rerun.json
    - bench/results/phase-07/bound-40907549180/
    - bench/results/phase-07/load-40909724292/
    - bench/results/phase-07/gzip-40909739628/
    - bench/results/phase-07/arenas-40909754190/
    - bench/results/phase-07/outband-40909768713/
    - bench/results/phase-07/bound-rerun-40999654995/
    - bench/results/phase-07/gzip-rerun-40999657702/
    - docs/tech_debt/active/2026-10-30-pool-dying-worker-tests-time-out-under-host-load.md
  modified:
    - bench/oper.py
    - bench/oper_sets.py
    - bench/results/phase-07/fit.json
    - bench/RESULTS.md
    - src/screw/calc/cost.py
    - src/screw/app.py
    - src/screw/cli.py
    - docs/architecture/decision_log.md
    - .planning/phases/07-operability-re-sweep/07-GAP-RULINGS.md
    - .planning/phases/07-operability-re-sweep/07-OWNER-RULINGS.md
    - .planning/phases/07-operability-re-sweep/07-SWEEP-PROTOCOL.md
    - tests/test_oper.py
    - tests/test_oper_followup.py
    - tests/test_oper_load.py
    - tests/test_oper_fit.py
    - tests/test_cost.py
    - tests/test_api.py
    - tests/test_cli.py
    - docs/tech_debt/INDEX.md
    - docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md
    - docs/tech_debt/resolved/2026-10-29-cost-model-admits-out-of-fit-head-heights.md

key-decisions:
  - "G30 (owner): a nut out-of-band reading widens e as a cold isolated reading does; a bolt's never does. The envelope check widens nut stl-fine seconds e 1.1069417227945801 to 1.7812452161769916 and peak e 0.5571452809681212 to 0.5976833077470993, both set by run 40909768713; no other Runs II reading exceeds its envelope (L22)"
  - "G30 (owner): a bolt below cost.MIN_FITTED_TURNS built turns is refused at every artifact with the over_budget 422 naming pitch, length and thread_length; the bolt stl-fine bytes e is not widened"
  - "G31 (owner): every bound candidate, partners included, has an ok explore reading at every artifact; only the 10 stl-preview contention and 2 gzip points that changed were read again (runs 40999654995, 40999657702)"
  - "The far point of G28 takes the first value on the form step at or above 10 x the high edge x d"
  - "tier-order.json names one source, the explore point file: R27 steps 1 to 4 read predictions and file order, no reading"

requirements-completed: []   # OPER-01, OPER-02 and OPER-03 advance; 07-16 derives the timeouts and the remaining bounds, so none is wholly done

metrics:
  duration: "commits 15:55Z to 17:02Z on 2026-10-29 and 03:14Z to 04:22Z on 2026-10-30, about 135 min, the owner's rulings in between; the runner time is inside it"
  completed: 2026-10-30
---

# Phase 7 Plan 15: Runs II, the out-of-band stop, the owner's G30 and G31, and the envelope check Summary

**All Runs II sets ran on the runner at 5 repetitions and are committed with RESULTS subsections. The
G28/G29 out-of-band check stopped the phase. The owner ruled G30 and G31. Under them, the stl-preview
bound and gzip points that held two kernel-refused nuts were read again, and a bolt below the fitted
turns is now refused. The envelope check over every Runs II directory then widened exactly two e,
nut stl-fine seconds and peak, both from outband run 40909768713, in one commit with fit.json,
`calc/cost.py`, RESULTS and L22.**

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
| 13 | 196ef2e | docs(07-15): record the Runs II campaign and its stop at the G28/G29 check |
| 14 | d5876d6 | fix(cli): type the numeric flags' converter for mypy 2.4 |
| 15 | 27ea042 | docs(debt): file the pool's dying-worker tests timing out under host load |
| 16 | 3bcbdb3 | docs(07): record the owner's rulings G30 and G31 and amend R11 and R14 |
| 17 | a09ce3e | docs(debt): record the pool tests' second timeout under host load |
| 18 | 6d68f20 | feat(bench): draw the bound set from points read ok at every artifact (07 G31) |
| 19 | bccb6f3 | feat(calc): refuse a bolt below the fitted turns at every artifact (07 G30) |
| 20 | 4c70138 | docs(bench): add the G31 stl-preview bound and gzip rerun records (runs 40999654995, 40999657702) |
| 21 | c07ed46 | feat(bench): let the out-of-band nut readings widen the envelope (07 G30) |
| 22 | 65867a8 | docs(bench): record the G31 stl-preview bound and gzip reruns in RESULTS (07 G31) |
| 23 | 54965a0 | feat(calc): widen the cost model's envelope to cover every cold isolated Runs II reading (07 D-07) |

This SUMMARY lands in its own docs commit after these.

## The runs

| set | run | sha | jobs | readings | statuses |
| --- | --- | --- | --- | --- | --- |
| bound | 40907549180 | 98c62ad | 20 (4 shards x 5) | 300 | ok 250, refused 50 |
| load | 40909724292 | f730ecb | 5 | 15 | ok 15 |
| gzip | 40909739628 | f730ecb | 5 | 70 | ok 60, refused 10 |
| arenas | 40909754190 | f730ecb | 5 | 30 | ok 30 |
| outband | 40909768713 | f730ecb | 10 (2 shards x 5) | 300 | ok 300 |
| bound-rerun (G31) | 40999654995 | 6d68f20 | 5 | 50 | ok 50 |
| gzip-rerun (G31) | 40999657702 | 6d68f20 | 5 | 10 | ok 10 |

Every job of every run succeeded on its first attempt, so no `gh run rerun` was needed. Every point
has repetitions 1 to 5 each once. With the reruns, each of the 60 bound points and 14 gzip points
has 5 ok repetitions in exactly one run, matched by its identity fields (members included). The 50
bound and 10 gzip readings G31 replaced, all `refused`, decide nothing. The CPU models per job are in
each RESULTS subsection.

## What was built

1. **D(A) first (R27, G6).** `tier_order` gives, per artifact, the candidates (admitted explore
   points in file order, deduplicated by kind and params as JSON), the edge ranking (largest edge
   ratio first, a tie to the label) and the draw (`random.Random(20261026).shuffle`, a new
   generator per artifact). `tier-order.json` was committed in c28c768, before `load.json`
   (98c62ad). It has 411, 404 and 439 candidates at stl-preview, stl-fine and step, which are
   B-01's admitted counts. G31 does not touch it.
2. **The sets.** Each file records `envelope` and `sources`, carries R6 `shard_sizes`, and is
   regenerated byte for byte by `--check`:
   - `bound.json` (R14, G31): 7, 7 and 6 bound points; 60 contention readings in shards of 17, 17,
     17 and 9. Its candidates are the admitted explore points read ok at every artifact
     (`bound_candidates`), partners included. The G31 regeneration moved only stl-preview points:
     `iso4017:M16x150` and `iso4017:M20x160` replace the two nuts, and four N = 3 points take a new
     partner.
   - `load.json` (R15): N 1, 2 and 3, Q = C = 2N, `solid_cache` 4, bodies at N = 1 only, one mix
     of 60 distinct cold requests.
   - `gzip.json` (R19): the 14 STL bound points at levels 1, 6 and 9.
   - `arenas.json` (R23, G17): Z(A) with the trim on and off; unchanged by G31.
   - `outband.json` (G28, G29): 60 points. Far points exist for bolt k and nut s only.
   - `bound-rerun.json` and `gzip-rerun.json` (G31): `python -m bench.oper_sets rerun`. These are the
     points of the regenerated set that no reading of the earlier run is of (10 and 2), with
     sources `explore` and `run`.
3. **`load-table`** prints the per-N figures of a load run. A non-ok reading, and every repetition
   of an incomplete point, prints no figure.
4. **`envelope-check`** applies R12 to the readings `widens` keeps. Load readings are never kept;
   outband readings are kept only of a nut (G30); every other set is kept and its cold isolated
   readings are used: part, gzip and arena readings, contention at N = 1, drift build 1. Where a
   reading exceeds its envelope, it raises the factor 1 + e by ulps and writes only the widened
   models' `envelope` and a `widened_by` list. It stops (exit 3) and writes nothing when the
   widened envelope would refuse a catalogue row or a default part.
5. **The turns refusal (G30).** `cost.fits` is False at every artifact for a bolt with
   `built_thread_length / pitch < MIN_FITTED_TURNS`. `cost.refusal` names pitch, length and
   thread_length and prints no figure; the API's `ctx.fields` reads `cost.refused_fields`. The
   bench's `admits` keeps the budget comparison alone, so every set drawn before G30 still
   regenerates.

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

**After G30:** the six nut pairs are covered by the widened nut stl-fine e (below). The G29 bolt is
refused by the shipped rule (bccb6f3). Every outband reading is within the shipped envelope, or is
of a part the shipped rule refuses.

## The owner's rulings (2026-10-30)

- **G30**, reply verbatim "1: widen nuts, guard G29 (Recommended)". A nut out-of-band reading widens
  e as a cold isolated reading does, and a bolt's does not. A bolt below the fitted turns is refused
  at every artifact. B-03's cap floor is unchanged. Recorded in `07-GAP-RULINGS.md` and
  `07-OWNER-RULINGS.md`. R11 is amended (3bcbdb3) with no gap label, no run id and the post-freeze
  sentence; the pins are in `tests/test_oper.py`.
- **G31**, reply verbatim "Exclude, rerun preview (Recommended)". Every bound candidate has an ok
  explore reading at every artifact; R14 is amended. Read literally ("at every artifact") or as "at
  its own artifact", the rule gives the same sets on the record (computed both ways before coding);
  the code takes the literal reading.

## Envelope check (Task 3, under G30)

Over all seven Runs II directories, 775 readings, 335 of them used (contention N = 1: 90 and 10;
gzip: 60 and 10; arenas: 30; nut outband: 135). Exactly the two models G30 names widen:

| model | e before | e now | set by |
| --- | --- | --- | --- |
| nut stl-fine seconds | 1.1069417227945801 | 1.7812452161769916 | 40909768713:outband-nut-s-below-iso4032:M2 rep 3 |
| nut stl-fine peak | 0.5571452809681212 | 0.5976833077470993 | 40909768713:outband-nut-s-below-iso4032:M2 rep 3 |

No other reading is above its enveloped prediction, the G31 reruns included. The widened envelope
refuses no catalogue row and neither default part. So B-01's budget, the refused-preset count and
every cap case stay put, and no cap test moved. The widening commit 54965a0 holds fit.json (only
the two `envelope` lines and `widened_by`), the re-emitted `calc/cost.py` block, RESULTS (the G30
outcome and `### envelope check`), decision_log (L22, and L21's "Superseded in part" line), the
resolved head-height item and two re-pinned fit tests. It lists no `bench/points` file and not
`tier-order.json`; `--check` exits 0.

Re-pinned tests:
- `tests/test_oper_fit.py::test_the_committed_fit_json_is_what_the_code_fits_from_the_committed_records`:
  a committed e may exceed the fresh fit's only when `widened_by` names a run.
- `tests/test_oper_followup.py::test_the_command_writes_only_the_widened_envelopes_and_the_widening_runs`:
  keeps the `widened_by` already present. Its out-of-band reading is now a bolt (c07ed46).
- G30's turns refusal (bccb6f3) moved six tests whose bolt (length 1e-8, 1e-9 or 5e-5 mm) is below
  the floor. Each is now the `over_budget` 422 or CLI exit 2, before the builder's doorway
  `build_error` or exit 1:
  - `tests/test_api.py`: the three cases of `test_a_length_too_short_to_model_is_a_422_not_a_served_file`
    and `test_a_length_below_the_floor_is_a_warned_info_document_and_a_422`.
  - `tests/test_cli.py`: `test_a_length_too_short_to_model_ends_with_an_error_naming_it_and_writes_nothing`
    and `test_a_length_too_short_to_model_exits_2_from_the_real_process`.
- Protocol pins (3bcbdb3): the G29 R11 pin and the R14 partner pin.

## For the owner

- **The turns refusal now answers before the builder's doorway (D-17).** Six request shapes changed:
  a bolt too short to model (length 1e-8 mm and the like) has fewer turns than the floor. So the API
  answers `over_budget` naming pitch, length and thread_length instead of `build_error`, and
  `screw export` exits 2 instead of 1. Both are still 422 refusals that name the length, and no file
  is written. This follows G30's text, "at every artifact", and nothing was approximated. If the
  doorway's message should win for such parts, that is a new ruling. Options: (1) keep as built
  (recommended: one rule, no exception); (2) let `download_refusal` pass a part the builder's
  doorway refuses, so its `build_error` is returned.
- **L21 vs the plan.** The plan asked to amend L21's envelope paragraph. L21 itself says a widened e is
  "a superseding entry that names the run, never an edit of this one". I followed the log's own
  convention: L22 supersedes the two rows, and L21 ends with a "Superseded in part by L22" line that
  names each widened e and its run.
- **`envelope_set_by` in fit.json** still names the explore point for the two widened models; the
  acceptance criterion allows only `envelope` and `widened_by` lines to change. `widened_by` and L22
  name the run that set them.
- **The pool tests' flake fired twice** (`docs/tech_debt/active/2026-10-30-pool-dying-worker-tests-time-out-under-host-load.md`,
  `must`, trigger fired). Each time the commit was retried openly at a lower host load and passed.
  Its next step is due before phase 7 lands.
- **For 07-16:** a contention point keeps its label when its partner changes. So the bound readings
  of `iso4017:M16x160-n3`, `iso4017:M20x180-n3`, `iso4017:M20x200-n3` and
  `nut-d100-p3.5-m0.8d-s4d-c5-right-n3` in run 40907549180 are of different points from those in
  bound.json. Match readings to points by their members (`bench.oper_sets.unread`'s identity), never
  by label.

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

**6. [Rule 3 - Blocking] The venv re-sync took mypy to 2.4.0, which failed `make verify`.**
- **Issue:** `src/screw/cli.py:74: error: Argument "type" to "add_argument" ... incompatible type
  "TypeForm[Any]"` on an unchanged tree, after the orchestrator's `uv run` re-synced the venv.
- **Fix:** the numeric fields' annotation is cast to the converter it is at run time; no behavior
  change. **Commit:** d5876d6.

**7. [Gate] Two pre-commit runs failed on `tests/test_pool.py` under host load (15.47, then 22.63).**
The assertions were `BuildTimeout(... 5s ...)` where `BrokenProcessPool` was expected, and once
`BuildTimeout(... 2s ...) != b''`. `test_pool.py` alone passed 22 of 22 three times. Each commit was
retried openly and passed. The debt item was filed (27ea042) and updated (a09ce3e); it is out of
scope here.

**8. [Rule 1 - Bug] A pin missed by the first rulings commit.** The R14 partner pin in
`tests/test_oper.py` held the old "one admitted point" text. It was re-pinned in the same commit
(3bcbdb3), after the hook reported `1 failed`.

**9. [Interpretation] The G31 reruns as their own sets.** `bound-rerun.json` and `gzip-rerun.json`
are written by code from two sources (`explore`, `run`) and checked by `--check`. `RUNS2_SETS` and
the default `runs2` command are unchanged.

### TDD evidence

Each task's tests were run against HEAD's sources swapped in, then restored:

| commit | tests | result at HEAD's sources |
| --- | --- | --- |
| c28c768 | the new Runs II tests | 23 failed, 3 errors |
| 6cf6f39 | `load_table` | 2 failed |
| 9e47eb1 | envelope check | 4 failed |
| 6d68f20 | G31 candidates, `unread`, `rerun` | 4 failed |
| bccb6f3 | the turns refusal (cost, API, CLI) | 4 failed |
| c07ed46 | `widens` | 1 failed |

GREEN was every commit's pre-commit `make verify`.

## Known Stubs

None.

## Threat Flags

None beyond the plan's register:
- **T-07-37:** each set, the reruns included, is generated by code and checked by regeneration.
- **T-07-63:** each set records its envelope, and `--check` refuses a recorded e above the shipped one.
- **T-07-64:** one partner per slot, and an empty slot is a stop.
- **T-07-38:** the widening ran with its B-01 guard: nothing B-01 keeps is refused.

## Debt

- Filed: `docs/tech_debt/active/2026-10-30-pool-dying-worker-tests-time-out-under-host-load.md`
  (must; the trigger fired on its second occurrence).
- Resolved: `docs/tech_debt/resolved/2026-10-29-cost-model-admits-out-of-fit-head-heights.md`
  (54965a0; INDEX row moved).
- Updated, still active: `docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md`
  (seen again in Runs II; G31 keeps such parts out of the bound set, but the kernel still refuses
  them).

## Self-Check: PASSED

- Found: `tier-order.json`, the seven Runs II point files under `bench/points/`, the seven record
  directories under `bench/results/phase-07/`, the resolved head-height item and the new pool item.
- All 23 commits of the table are ancestors of HEAD.
- `python -m bench.oper_sets --check` exits 0.
- The plan's verify command, `make test PYTEST_ARGS="tests/test_oper_followup.py tests/test_cost.py
  tests/test_presets.py -q -n0 --no-cov"`, gave `530 passed`. `grep -q "### envelope check"
  bench/RESULTS.md` succeeds.
- `git show --stat 54965a0` lists fit.json, `calc/cost.py`, RESULTS and decision_log, and no
  `bench/points` file and not `tier-order.json`. Its fit.json diff is two `envelope` lines and
  `widened_by`.
- The envelope check run again on the pre-widening fit.json writes the same file byte for byte
  (`cmp`).
