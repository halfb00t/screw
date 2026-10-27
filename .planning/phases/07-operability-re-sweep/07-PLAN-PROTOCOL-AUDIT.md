# Phase 7: Plans 07-05 to 07-20 against the frozen protocol

Read-only audit, 2026-10-27, branch `gsd/phase-07-operability-re-sweep` at `02b6151`.

**What was compared.** The protocol as it landed is `07-SWEEP-PROTOCOL.md`, frozen by R30 at squash `9dea01e`. All protocol line numbers below refer to that file. It was diffed against the plan-07-03 text, read with `git show 40f667d:...` in `.claude/worktrees/phase-07-preregistration`. The landed code read was `bench/oper.py`, `bench/oper_child.py`, `bench/oper_sets.py`, `bench/oper_lift.py`, `bench/points/*.json` and `.github/workflows/operability.yml`. Also read: the Codex reviews, rounds 1 to 4, and `07-03-SUMMARY.md` / `07-04-SUMMARY.md`.

**Plan line numbers** are `cat -n` lines of each `07-NN-PLAN.md`.

**Kinds of conflict:**
- *contradicts*: the plan says something the protocol rules out.
- *omits*: required work is missing.
- *redundant*: the plan's work is now unneeded.
- *stale*: a number or path is out of date.
- *dependency*: steps are in the wrong order.

**Severities:**
- *blocker*: the plan would spend runner time on, or produce a bound from, something the protocol forbids.
- *must*: has to be fixed before the plan runs, but is not a blocker.
- *nice*: worth fixing; does not change any number.

Facts checked against the files (not inferred):
- `walls.json` has 756 points:
  - 60 turn walls
  - 27 ceilings (9 per decade, including `ceiling-nut-clearance-*` and `ceiling-nut-d-*`)
  - 48 tails
  - 540 root points
  - 12 nut-debt points
  - 69 `beyond-*` points, each with a `lift`
- Set reps:
  - `walls`, `explore` and `controls`: 1
  - `spread` and `tracer`: 5
- `summarize` behaves as follows (`bench/oper.py:300-342`):
  - It groups by `(label, artifact, lift)`.
  - A point gets a median and a max only when every repetition is `ok` and the repetitions are exactly the expected ones. Otherwise it is `incomplete`.
  - A lifted point never gets a median or a max.
  - `--reps` defaults to `1,2,3,4,5` (`bench/oper.py:741-743`).
- The child reads the peak once, after the level-1 gzip (`bench/oper_child.py:299-307`). It writes `maxrss_bytes` and `oom_kills` (`:311-313`).
- `wall_s` is kept for every status (`bench/oper.py:263-264, 291`).
- The pool routes a part by `hash(p) % workers` (`src/screw/pool.py:97-98`).
- `d` is a field of the shared base `FastenerParams` with `le=INTERIM_MAX_MM` (`src/screw/params.py:82, 97`).
- `operability.yml` has one job type only: `bench.oper run` over a point file. It has no load, drift or contention mode.

---

## 07-05 (Runs I: tracer, the four sets, walls confirm, margin, shards)

1. **Interfaces describe the summary as it was before the change.**
   - Plan (L103-104): "`python -m bench.oper summarize FILE... [--markdown]` (07-01): per (label, artifact) median and max of ok reps".
   - Code: `bench/oper.py:300-342` groups per `(label, artifact, lift)`. A point with any non-ok repetition, or with the wrong set of repetitions, has no median and no max. A lifted point never has one. This is R3, lines 60-64.
   - Kind: stale. Severity: must.
   - Fix: replace the bullet with the current behaviour and the `--reps` flag.

2. **Interfaces give record key names that do not exist.**
   - Plan (L107-108): "`ru_maxrss_bytes`, `oom_kill`".
   - Code: `bench/oper_child.py:311-313` writes `maxrss_bytes` and `oom_kills`. Records also carry `lift` (`bench/oper.py:292-293`).
   - Kind: stale. Severity: nice.
   - Fix: correct the key names and add `lift`.

3. **The RESULTS summaries would mark every 1-rep point `incomplete`.**
   - Plan, Task 2 step 3 (L172-173): "the pasted `summarize --markdown` output". No `--reps` is given.
   - Code and rule: `bench/oper.py:741-743` defaults to `1,2,3,4,5`. R3 (L61-64) makes a point with the wrong repetitions `incomplete`. So every `explore`, `walls` and `controls` point (reps 1) would print `incomplete` with no figures.
   - Kind: omits. Severity: must.
   - Fix: pass `--reps 1` for explore, walls, controls and walk-down. Pass `--reps 1,2,3,4,5` (the default) for spread, tracer and walls-confirm.

4. **The walk-down is not R7's per-cell walk.**
   - Plan, Task 3 behaviour (L206): "`walk_down_points(walls_records)` ... the 240, 230, ... points (step 10) for each failing size and hand, down to the first step every one of them reaches".
   - R7 (L169-178): "A *cell* is a size, a hand and a kind (bolt rod or nut void) ... goes on to the cell's first `ok` step ... The *candidate* T is the smallest first ok step over the cells ... a cell is read at T only if T is its own first ok step or the confirmation set below asks for it."
   - The plan's version drops `kind` from the cell and walks to a common step. R7 walks each cell to its own first ok step and then takes the minimum.
   - Kind: contradicts. Severity: blocker (the walk-down set would read points R7 does not ask for, and skip ones it does).
   - Fix: `walk_down_points` returns, for each cell whose 250-turn reading is `refused` or `crashed`, its next 10-turn step down. It stops per cell at that cell's first ok step. `derive` computes T as the minimum first ok step.

5. **The walk-down trigger is undefined, and its stop is missing.**
   - Plan (L206): "for each failing size and hand".
   - R7 (L170-171): only "A `refused` or `crashed` reading starts a walk-down set". R7 (L183-188): a "`killed`, `capped` or `no_cgroup` reading in that evidence, or a reading it asks for that is missing ... No turn bound is then awarded, 250 included, and the phase stops and asks the owner."
   - Kind: omits. Severity: blocker (a capped 250-turn reading could start a walk-down and lead to a bound).
   - Fix: trigger the walk-down only on `refused` or `crashed`. Make any `killed`, `capped`, `no_cgroup` or missing reading in the R7 evidence raise and stop for the owner.

6. **The confirm set is generated before T exists.**
   - Plan, Task 3 step 3 (L216-218): "Generate `bench/points/walls-confirm.json` (and `walls-down.json` only if `walk_down_points` is non-empty), commit, push, dispatch each".
   - R3 (L67-69): "For R7 the value is the candidate T, read for every size, hand and kind". R7 (L174-179): T is the smallest first ok step over the cells, so it exists only after the walk-down readings are in.
   - Kind: dependency. Severity: blocker (a confirm set built before the walk-down would read the wrong T).
   - Fix, in order:
     - Dispatch the walk-down (repeat it while any cell has not reached its first ok step).
     - Derive T.
     - Generate `walls-confirm.json`. For R7 it holds T for all 60 cells and T+10.
     - Dispatch it.

7. **The confirm generator leaves out two required cases.**
   - Plan behaviour (L205): "`confirm_points(walls_records)` returns, for each of R7-R10, the points at the decided value and at the next step past it".
   - The protocol says:
     - R3 (L72-78): the next step past 250 turns or 1e5 mm is a `walls` group (f) point with its `lift`. "A reading past a cap awards nothing".
     - R9 (L213-219) and R10 (L227-233): when no reading fails, the result is "above 0", which is not a walked value.
   - The plan does not say:
     - that the confirm points must carry the `lift` (`max_turns` 260, `max_mm` 1e6);
     - what to confirm when R9 or R10 comes out "above 0" (see gap G1).
   - Kind: omits. Severity: must.
   - Fix: copy `lift` from the walls point. Stop and ask the owner on an "above 0" outcome until G1 is ruled.

8. **The margin is not defined on the cold wall, and it silently drops points.**
   - Plan behaviour (L207): "`margin(spread_records)` is the largest (max / median - 1) over spread points with 5 ok reps".
   - R5 (L156-157): "the largest `max / median - 1` of the cold wall (`build_s + export_s`) over the `spread` points".
   - The plan names no metric. `summarize` gives a max and a median per metric, and the max of a sum is not the sum of the maxes. The plan also quietly leaves out a spread point that has no median, which R5 does not allow (see G3).
   - Kind: omits. Severity: must.
   - Fix: compute `build_s + export_s` for each reading, then take the max and the median per point. If any spread point has no median, stop and ask the owner.

9. **Shard sizing uses only ok readings.**
   - Plan behaviour (L208): "`shard_size(explore_records, timeout_minutes=350)` ... None when there are no ok records".
   - R6 (L162-163): "summed measured `wall_s` (from the explore records, per artifact and kind)". `wall_s` exists for every status (`bench/oper.py:263-264`). A killed reading costs about 600 s.
   - Kind: contradicts. Severity: must (shards would be undersized, and runner jobs would time out).
   - Fix: sum `wall_s` over every explore record, whatever its status.

## 07-06 (contention and memory instruments)

1. **Fillers are resubmitted in a cycle.**
   - Plan truth (L24): "filler points on slots 1..N-1 ... each filler slot is resubmitted the moment it finishes, so every worker stays busy until the bound point ends". Same in behaviour (L119): "at least 5 filler completions on slot 1 (resubmitted while the bound point runs)".
   - R14 (L286-287): "P on one slot and, on each of the other N - 1 slots, one admitted point of the same artifact, all cold and submitted together." A resubmitted part on the same worker is a solid-cache hit (`SCREW_SOLID_CACHE` is at least 1, R23 L409-410), so it is not cold.
   - Kind: contradicts. Severity: blocker (every contention reading would measure something other than R14's experiment).
   - Fix: submit exactly N-1 partners, each once, and wait for all N.

2. **Slots are addressed directly, with the bound point on slot 0.**
   - Plan truth (L26): "Slots are addressed directly (`pool._executors[i]`), not by `hash(p) % N`, because str hashing is salted per process". Acceptance (L151): "`grep -c "hash(" bench/oper_bound.py` prints 0". Action (L132): "submit the bound point to `_executors[0]`".
   - R14 (L288-293): "routes a part to worker `hash(p) % N` with `p = KINDS[kind].model_validate(params)` (`BuildPool.executor_for`); the hash is of the field values and is the same in every process ... P has its own slot. The partner of each other slot is the admitted point other than P whose slot at this N is that one". Codex round 3 confirmed that the hashes match across processes.
   - Kind: contradicts. Severity: blocker.
   - Fix: route every point through `executor_for` (or `_executors[hash(p) % N]`) so that each point lands on the slot the set file computed. Drop the `hash(` acceptance criterion.

3. **The bound wall is measured from submit to result.**
   - Plan truth (L25) and action (L134): "the bound point's wall from submit to result ... Every wall is `time.perf_counter` from submit to result".
   - Protocol: the Terms (L19) define "The *cold wall* of a reading is `build_s + export_s`". R14 (L298-300) picks the bound point and sets the timeout from the "max cold wall".
   - Kind: contradicts. Severity: must (07-16's timeouts would rest on a different quantity).
   - Fix: have each pool task time its own build and export, and return `build_s` and `export_s` with the bytes. Keep submit-to-result as an extra field if it is wanted.

4. **The plan invents a `failed` status.**
   - Plan behaviour (L121): "a fake that raises for the bound point gives status `failed`".
   - R2 (L47-50): the statuses are exactly `ok`, `capped`, `killed`, `crashed`, `refused`, `no_cgroup`. A kernel raise is `refused`.
   - Kind: contradicts. Severity: must.
   - Fix: use `refused`, with the exception class and text.

5. **The drift probe is the two-pass design that was removed.**
   - Plan truth (L29): "mode `drift` exports the given list twice in one process and records the largest `memory.current` sampled after each export of pass 1 and of pass 2". Behaviour (L166): "`pass1_max_current_bytes` and `pass2_max_current_bytes`". Action (L174-175): "`clear_cache()` at the start only".
   - R23 (L398-413): one fixed part Z(A), built K = 20 times. "Before each build it empties the solid cache". "The peak is read as R2 says, after the build and its export, after every build". The deadline is K x the artifact's timeout. The protocol diff shows pass 2 was removed.
   - Kind: contradicts. Severity: blocker (07-15 would dispatch a drift set R23 does not define).
   - Fix: mode `drift` takes `{part, artifact, k: 20}`. It calls `clear_cache()` before each build, reads `memory.peak` (R2, after gzip; see G14) after every build, and reports peaks 1 to K. It takes a deadline argument.

6. **The solid-cache probe measures W(K) outside the load run.**
   - Plan truth (L27): "mode `solid-cache` sets `SCREW_SOLID_CACHE=K` ... exports the given parts in order in one process ... for K in 1..4 (R22)".
   - R22 (L389): "`W(K)` is the peak with K solids cached per worker, measured in the load run." R15 (L338): "`SCREW_SOLID_CACHE` is 4 unless R22 is measuring a K."
   - Kind: contradicts / redundant. Severity: must here (the instrument itself); it is a blocker in 07-15, which would dispatch it.
   - Fix: drop mode `solid-cache`. W(K) is a load reading with a `SCREW_SOLID_CACHE` env, which belongs in 07-08.

7. **A smoke point file is written by hand in `bench/points/`.**
   - Plan, Task 3 (L201): "Write `bench/points/bound-smoke.json` by hand".
   - R30 (L494): "The point files change only through `bench/oper_sets.py`".
   - Kind: contradicts. Severity: nice (the smoke sets no figure).
   - Fix: either have `bench.oper_sets` write it, or record that R30's sentence covers only measured sets (owner).

## 07-07 (walls into code, L20)

1. **A killed 250-turn reading keeps 250.**
   - Plan behaviour (L150): "a `killed` 250-turn reading leaves 250".
   - R7 (L185-188): "A `killed`, `capped` or `no_cgroup` reading in that evidence ... cannot support a bound either. No turn bound is then awarded, 250 included, and the phase stops and asks the owner."
   - Kind: contradicts. Severity: blocker (it writes a bound the protocol forbids).
   - Fix: the case must raise naming R7.

2. **A walk-down result becomes a bound without the confirm.**
   - Plan behaviour (L150): "one `refused` 250-turn reading with ok walk-down at 240 gives 240".
   - R7 (L176-181): "`MAX_TURNS` is T only if the confirmation readings ... at T are `ok`, in all 5 repetitions, for every cell ... A confirmation reading at T that is not `ok`, or is missing, awards no turn bound".
   - Kind: omits. Severity: blocker.
   - Fix: the derived value must require 5 ok confirm repetitions at T for all 60 cells. Add a test with one missing or non-ok confirm reading that raises.

3. **The tail case uses the old rule.**
   - Plan behaviour (L150): "largest failing tail 1e-8 gives MIN_TAIL_MM 1e-3".
   - R9 (L213): "`MIN_TAIL_MM` is the smallest power of ten at or above 100 F". F = 1e-8 gives 1e-6. The plan's 1e-3 is the removed rule ("stays 1e-3 if F is at most 1e-5", plan-07-03 text).
   - Kind: contradicts / stale. Severity: blocker.
   - Fix: change the expected value to 1e-6. Add cases for "above 0" and for V above 1e-2, which has no number.

4. **The "above 0" floors and the ok-only rule for tails and roots are missing.**
   - Plan Task 2 action (L215): "set `MAX_TURNS` and `MIN_TAIL_MM` to the derived values". It has no "above 0" path for tails. The behaviour (L150) has no killed or capped case for R9 or R10.
   - R9 (L214, L217-221) and R10 (L231-235): "If no reading fails down to 1e-9 mm, the floor stays "above 0"". "V ... stands only on `ok` readings ... every reading of group (c) at a tail of V or more ... must be `ok` ... Otherwise there is no number: the phase stops".
   - Kind: omits. Severity: must.
   - Fix:
     - Add the "above 0" path for `MIN_TAIL_MM`. What the builder's guard becomes is decided by the owner, since the guard is also a crash guard.
     - Add tests: a killed reading at or above V raises; a capped reading in an otherwise clean walk raises rather than giving "above 0".

5. **The field ceilings assume every field is tested at X, and the shared `d` field is missing.**
   - Plan:
     - Truth (L39): "a field whose measured ceiling differs from it gets its own named constant".
     - Interfaces (L121): "used as `le=` on bolt d, length, s, k, thread_length and nut s, m, clearance". Nut `d` is missing.
     - Behaviour (L208): "(not `d`: `head_too_small` needs s above d, so d cannot reach the ceiling with a valid s)".
   - Protocol and code:
     - R8 (L196-205) awards bolt `d` 99999.9, nut `d` 99999.6 and nut `clearance` 49996.9 at 1e5, so those three always differ from the X that the other six fields share.
     - `d` is one field on `FastenerParams` (`params.py:97`), so `MAX_BOLT_D_MM` and `MAX_NUT_D_MM` need per-subclass overrides.
     - "A ceiling is never written above a value a reading tested."
   - Kind: stale / omits. Severity: must.
   - Fix:
     - Expect three per-field constants whenever their decade is confirmed.
     - Add nut `d` to the interfaces.
     - Plan the per-kind override of the base `d` field.
     - Boundary tests at each tested value.

6. **Lifted readings must award nothing.**
   - Plan: the `derive_walls` behaviour (L150) has no case for an ok `beyond-*` reading.
   - R3 (L77-78): "A reading past a cap awards nothing: R7 and R8 never raise a cap above its present value."
   - Kind: omits. Severity: must (`walls.json` holds 69 lifted points, so an ok reading at 260 or 1e6 will exist).
   - Fix: add a test that an ok 260-turn or 1e6 reading leaves 250 and 1e5.

7. **The stop conditions are incomplete.**
   - Plan truth (L42): "If R8 finds a field with no ok decade, or R7 a size with no ok walk-down step, the plan stops".
   - The protocol also stops on:
     - R7 (L180-181, L186-188): a confirm reading at T that is not ok or is missing, or killed/capped/no_cgroup/missing boundary evidence.
     - R9 and R10 (L221, L234-235): "Otherwise there is no number".
   - Kind: omits. Severity: must.
   - Fix: list every stop by rule.

8. **The derive command leaves out the walk-down records.**
   - Plan acceptance (L185): "`derive-walls --from bench/results/phase-07/walls-* bench/results/phase-07/walls-confirm-*`".
   - R7 (L183-184): "The boundary evidence is every reading this walk asks for: the 250-turn readings, each walk-down reading ... and the confirmation readings at T."
   - Kind: omits. Severity: must.
   - Fix: add `bench/results/phase-07/walls-down-*`.

## 07-08 (load, bodies, gzip instruments)

1. **Load requests ask for gzip.**
   - Plan action (L147): "each request a GET with `Accept-Encoding: gzip`".
   - R15 (L339-340): "Every request carries `Accept-Encoding: identity`, so no response is compressed".
   - Kind: contradicts. Severity: blocker (every load reading would include gzip work).
   - Fix: use `identity`.

2. **The load container misses two required environment variables.**
   - Plan truth (L26) and action (L142-143) set only `SCREW_BUILD_WORKERS` and `SCREW_MAX_QUEUED_BUILDS` ("the two env flags").
   - The protocol also requires:
     - R15 (L336-338): "`SCREW_EXPORT_CACHE_MB` is 1 ... `SCREW_SOLID_CACHE` is 4 unless R22 is measuring a K". The default today is 64 MiB (`src/screw/app.py:108`).
     - R22 (L389): W(K) is measured in the load run, so the load point needs `SCREW_SOLID_CACHE`.
   - Kind: omits. Severity: blocker.
   - Fix: the load point carries `SCREW_EXPORT_CACHE_MB=1` and `SCREW_SOLID_CACHE` (4 by default; K for R22), passed as `-e` argv elements.

3. **Requests are dealt to clients in advance.**
   - Plan behaviour (L128): "`split_mix(mix, clients)` deals the requests round-robin in mix order".
   - R15 (L326-327): "A client takes the next request as soon as its previous response is complete, and the first 2N start together."
   - Kind: contradicts. Severity: blocker (pre-dealt lists leave clients idle, so less than 2N-way concurrency is measured).
   - Fix: replace `split_mix` with one shared queue in mix order that each client pulls from.

4. **A smoke point file is written by hand in `bench/points/`.**
   - Plan (L211): "Write `bench/points/load-smoke.json` by hand".
   - R30 (L494). Same as 07-06 #7.
   - Kind: contradicts. Severity: nice.

## 07-09 (fit and budget table)

1. **The fit does not handle incomplete repetitions.**
   - Plan truth (L24): "from the per-point max of every ok reading of the committed explore and spread records". Truth (L27) excludes a point "with any non-ok repetition", but nothing covers a point with missing or duplicate repetitions.
   - R3 (L61-64): "A point with four of five, or with five copies of one ... is `incomplete` and has no median and no max, so it supplies no bound and no fit figure." R11 (L243-246): "fitted on the per-point max of every `explore` and `spread` point whose every repetition is `ok`".
   - Kind: omits / stale wording. Severity: must.
   - Fix: build the fit input from `summarize(readings, expected_reps)`, with (1,) for explore and (1..5) for spread. Exclude `incomplete` points and list them. Reword truth L24.

2. **C3 is not specified.**
   - Plan behaviour (L163): "`candidates(fit, records)` returns C1, C2 and C3 per artifact". No formula is given.
   - R13 (L268-272): "Q = 4 x 10^9 / rho, where rho is the cgroup peak divided by the raw bytes of the `stl-fine` point with the largest raw bytes among the `explore` and `spread` points whose every repetition is `ok`". Preview and STEP are unbounded under C3.
   - Kind: omits. Severity: must (the 64 MiB basis in RESEARCH L65 and L159 is the obvious wrong fallback).
   - Fix: state the Q formula and rho's selection. Add a test with an all-ok selection and a mixed point that is skipped.

3. **The note compares against the old fine-STL rule.**
   - Plan action (L176-178): "a one-line note ... if a candidate keeps fewer catalogue rows than the 232 the current fine-STL rule keeps".
   - That 232 is the old C3 basis, which the protocol diff removed.
   - Kind: stale. Severity: nice.
   - Fix: drop the note, or word it as "the rule being retired" and not as a candidate basis.

## 07-10 (owner rulings B-01..B-03)

1. **Option c3 describes the old C3.**
   - Plan (L103-107): "C3, today's fine-STL basis ... Keeps the 64 MiB fine-STL budget the L12, L13 and L16 caps were set against".
   - R13 (L268-272): "C3, bytes-bound. ... Q = 4 x 10^9 / rho". The protocol diff removed the 64 MiB C3.
   - Kind: contradicts / stale. Severity: must (the owner would rule on a description of a candidate that no longer exists).
   - Fix: reword option c3 as "bytes-bound, Q = 4e9 / rho from the largest all-ok fine STL; preview and STEP bounded only by the walls".

2. **A custom triple is offered.**
   - Plan (L108-112): "Another triple per artifact, stated by the owner".
   - R13 (L258-275) defines three candidates and "The owner rules (B-01)". It does not say whether a ruling outside C1-C3 is within the rule, and R30 forbids adding a threshold after the first reading (see G10).
   - Kind: relies on an unstated rule. Severity: nice.
   - Fix: keep the option, but mark that choosing it needs the owner to rule G10 first.

## 07-11 (cost model in calc)

Consistent.
- R12's admission `pred * (1 + e) <= budget` is in truth L30 and action L168.
- A None component is unbounded (L168), which matches R13's unbounded components.
- The model is fitted per (kind, artifact, target) from fit.json.
- R12 widening is carried through `widened_by` (L163).

## 07-12 (default cap, L21)

Consistent. It is product code and decision logging only. L21 cites R11-R13 (L208), and no protocol rule governs B-03.

## 07-13 (retire cap tables)

Consistent. "The tessellation presets are kept" (R23 L393, R11 L246) is what the renamed mesh test asserts (L139-140). Nothing else touches a rule.

## 07-14 (page handles a refused preview)

Consistent. It is UI only and cites no rule.

## 07-15 (Runs II sets and envelope check)

1. **The bound set leaves out the memory extrema.**
   - Plan truth (L34): "per artifact the 5 admitted points with the largest enveloped build-seconds prediction plus the worst measured admitted point". Behaviour (L129): "5 + 1 bound points".
   - R14 (L280-284): "plus the two memory extrema: the admitted point with the largest enveloped peak-bytes prediction and the admitted point with the largest measured peak ... so the set holds 5 to 8 points". R16 (L344-345) reads W from these points.
   - Kind: omits. Severity: blocker.
   - Fix: add both extrema. Ties go to the first label in sort order. Restrict the measured choices to explore readings that are `ok`. De-duplicate.

2. **The contention partners are the "next-heaviest" points.**
   - Plan truth (L34): "with the next-heaviest admitted points as fillers". Behaviour (L129): "fillers the next-heaviest admitted points".
   - R14 (L291-297): "The partner of each other slot is the admitted point other than P whose slot at this N is that one and whose enveloped build-seconds prediction is the largest ... A slot that holds no admitted point leaves that (P, N) unrunnable, and the phase stops and asks the owner".
   - Kind: contradicts. Severity: blocker.
   - Fix: for each (P, N), compute `hash(KINDS[kind].model_validate(params)) % N` for every admitted point at that artifact. Pick one partner per slot that P does not occupy. Raise naming R14 on an empty slot.

3. **The load mix is not R15's mix.**
   - Plan truth (L34): "the mix of the first 10 admitted parts in `random.Random(20261026)` order at all three artifacts". Behaviour (L130): "takes the first 10 admitted parts ... all three artifacts each".
   - R15 (L308-327):
     - 20 parts per artifact.
     - The artifacts pick in the order `stl-fine`, `step`, `stl-preview`.
     - Each artifact takes 3 edge parts from its R27 step-3 edge ranking, then 17 draw parts from its R27 step-4 draw order, all unused and with an `ok` explore reading.
     - "no part appears twice in a run, the three artifacts of one part included".
     - The 60 requests are shuffled once by a new `random.Random(20261026).shuffle`.
     - If a list runs out, stop.
   - Kind: contradicts. Severity: blocker.
   - Fix: replace `load_points` with R15's allocation over R27 D(A) steps 1-4.

4. **The load points omit the encoding and cache settings.**
   - Plan truth (L34): the load set is "N 1, 2, 3 with Q = 2N, C = 2N". Inherited from 07-08 #1 and #2.
   - R15 (L336-340).
   - Kind: omits. Severity: blocker.
   - Fix: the load points carry `SCREW_EXPORT_CACHE_MB=1` and `SCREW_SOLID_CACHE=4`, and the driver sends `identity`.

5. **The memory set measures W(K) with a separate probe.**
   - Plan truth (L34): "`memory` (solid-cache K 1 to 4 ...)". Behaviour (L131): "solid-cache at K 1..4 over the 4 heaviest admitted parts".
   - R22 (L389): "`W(K)` ... measured in the load run".
   - Kind: contradicts. Severity: blocker (it spends runner time on an instrument R22 does not use).
   - Fix: drop it. W(K) for K below 4 comes from load runs at the picked N, which happen after 07-16's R16 pick (see 07-16 #5 and G9).

6. **The drift set is the wrong design and runs too early.**
   - Plan truth (L34): "drift". Behaviour (L131): "drift over the load mix". Task 2 (L165) dispatches `memory` alongside `load`.
   - R23 (L402-413):
     - Z(A) is the bound set's measured memory extremum, not the load mix.
     - K = 20, with `clear_cache` before each build, below HTTP, 5 repetitions.
     - "The deadline is K x the artifact's timeout (R14)". Those timeouts exist only after R16 picks N from the load run (R27 L473-474, R14 L298-300).
   - Kind: contradicts / dependency. Severity: blocker.
   - Fix: remove drift from 07-15. Generate and dispatch it after 07-16 has derived the R14 timeouts (see 07-16 #2).

7. **D(A) is not fixed before the load run.**
   - Plan: no task generates or commits the R27 candidates, edge ranking or draw order. `boundary_points` comes only in 07-18 (L129).
   - R27 (L473): "Steps 1 to 4 need no timeout, so D(A) is fixed before the load run (R15)". R15 (L314-318) takes its parts from them.
   - Kind: dependency / omits. Severity: must.
   - Fix: implement R27 steps 1-4 in 07-15 Task 1. Commit D(A) with the Runs II sets. 07-18 then reuses it.

8. **Contention readings are used to widen the envelope.**
   - Plan, Task 3 step 2 (L206-207): "contention bound walls and peaks count as the bound points' build seconds and peak".
   - R12 (L253-254) widens on "A later reading (Runs II, either tier)". R11's targets (L239-240) are the isolated cold build plus export and the container peak. The protocol does not say whether a reading at N of 2 or 3 (a shared container peak, a wall under contention) is a reading of P against those targets (see G5).
   - Kind: relies on an unstated rule. Severity: must.
   - Fix: count only N = 1 contention readings and ordinary part readings, or stop for the owner's ruling on G5.

9. **A capped N is taken as not qualifying.**
   - Plan truth (L41): "A load set at an N whose readings are capped or OOM-killed records that N as not measured (no figure), which under R16 means it does not qualify".
   - R16 (L346-350) needs every one of the 5 repetitions' p95 and the max load peak. It does not say what a non-ok repetition does (see G7).
   - Kind: relies on an unstated rule. Severity: nice.
   - Fix: cite G7, or stop for the owner when it happens.

## 07-16 (derive runtime values)

1. **The tmpfs rounding step is 64 MiB.**
   - Plan behaviour (L130): "mem_limit rounds up to 256 MiB, tmpfs to 64 MiB".
   - R26 (L441): "rounded up to the 256 MiB step of R16". The 64 MiB step was removed.
   - Kind: stale. Severity: blocker (it ships a value against the rule).
   - Fix: change the tmpfs step to 256 MiB and add a test.

2. **The drift run cannot exist when this plan runs.**
   - Plan: truth (L31) has derive-runtime produce "recycling". Behaviour (L131): "recycling triggered raises naming R23". Action (L136): it runs over "every committed Runs I and Runs II directory".
   - R23 (L412-413): "The deadline is K x the artifact's timeout (R14)". The timeouts are this plan's own output.
   - Kind: dependency. Severity: blocker.
   - Fix: split the plan, or add a step:
     - Derive R14 to R16 first.
     - Generate the R23 drift set with `deadline_s` = 20 x timeout(A) and dispatch it at 5 repetitions.
     - Then derive R23 and the rest.
     - Insert this as a plan step between Task 1 and Task 2.

3. **The drift run's own stop is missing.**
   - Plan truth (L32) lists the owner stops; the drift stop is not among them.
   - R23 (L415-417): "Any repetition that is not `ok`, or whose readings after build 1 or build K are missing, leaves the artifact with no drift and the phase stops and asks the owner."
   - Kind: omits. Severity: must.
   - Fix: add it to `derive_runtime`'s raises and to truth L32.

4. **"Rule order" computes R16 before its inputs.**
   - Plan action (L136): "implementing R14-R26 in rule order".
   - R16 (L346-347): `mem_limit(N)` uses "the export cache budget `+` the tmpfs size". Those are R21 and R26, which come later in rule order.
   - Kind: dependency. Severity: must.
   - Fix: compute in this order: R14 sets (N-independent), R21, R26 per N, R16, R14 timeouts at the picked N, R17, R18, R19, R20, R22, R24, R25, R23.

5. **R22's load runs at K below 4 are not planned.**
   - Plan behaviour (L130-133) and truth (L35) take "R22's K" as if it were already measured.
   - R22 (L387-389) needs `W(K)` from "the load run" at the picked N. R15 (L338) runs at 4 "unless R22 is measuring a K". No plan dispatches a load at K = 3, 2 or 1 after the pick.
   - Kind: omits. Severity: must.
   - Fix: if W(4) fails at the picked N, dispatch load runs at that N with K = 3, then 2, then 1, and derive R22 from them. G9 must be ruled first.

6. **The timeout wording describes the old contention design.**
   - Plan truth (L33): "the bound point's wall with every worker busy at the picked N".
   - R14 (L298-300): the "max cold wall over its 5 repetitions at the picked N", with one partner per other slot.
   - Kind: stale wording. Severity: nice.
   - Fix: say "the max cold wall (`build_s + export_s`)".

7. **Two R16 checks are not tested.**
   - Plan: the behaviour (L129) has no `nproc - 1` check, and no W from the N = 1 containers that include the memory extrema.
   - R16 (L344-349).
   - Kind: omits. Severity: nice.
   - Fix: add both cases.

## 07-17 (Dockerfile, compose, L22, L23)

1. **The prohibition allows mem_limit equal to MemTotal.**
   - Plan prohibition (L42): "MUST NOT set mem_limit at or above 16 x 10^9 bytes or above the runner's recorded MemTotal".
   - R16 (L348): "under both 16 x 10^9 bytes and the smallest `MemTotal`". Equal to MemTotal does not qualify.
   - Kind: contradicts (wording). Severity: nice (behaviour L133 already says "below").
   - Fix: "at or above ... the smallest recorded MemTotal".

## 07-18 (required bounds tier)

1. **The tier is not built the way R27 says.**
   - Plan truth (L34): "per artifact the 3 admitted points nearest the budget edge, then admitted explore points in `random.Random(20261026)` order while the summed recorded walls stay under 10 minutes". Behaviour (L129): "while the summed `wall_s` stays under 600 s".
   - R27 (L448-471):
     - Candidates are de-duplicated by part.
     - The edge ratio is taken over finite budget components. Preview and STEP under C3 use build seconds.
     - Ties go to the label that sorts first.
     - The draw is the remaining candidates in file order, shuffled by a new `Random(20261026).shuffle` per artifact.
     - The tier "stops at the first draw point that does not fit and skips none".
     - The charge is "the cold wall (`build_s + export_s`) of its `explore` reading when that reading is `ok`, and otherwise the artifact's full timeout".
     - `wall_s` is the whole `docker run` wall, not the cold wall.
   - Kind: contradicts. Severity: blocker (every PR's required job would run a tier R27 does not define).
   - Fix: `boundary_points` takes D(A) from 07-15's R27 steps 1-4 and applies step 5 exactly. Add tests for de-duplication, ties, the stop at the first point that does not fit, and the non-ok charge.

2. **R27 is implemented too late.**
   - Plan: `boundary_points` first appears here (L137). The plan depends only on 07-16.
   - R27 (L473) and R15 (L314-318) need steps 1-4 before the load run (07-15).
   - Kind: dependency. Severity: must.
   - Fix: move steps 1-4 to 07-15 (07-15 #7). 07-18 adds only step 5.

## 07-19 (full tier, D-13 gate, L24, L25)

1. **The R5 re-run happens inside the same job.**
   - Plan truth (L30): "a point whose single cold wall x (1 + m) reaches its timeout is re-measured to 5 reps in the same job and judged on their max". Behaviour (L169): "a reading within margin of its timeout triggers 4 more reps".
   - Protocol: R5 (L157-158): "re-run at 5 repetitions". R3 (L59-63): "The 5 repetitions of a point are 5 matrix jobs (rep 1 to 5), so 5 runner instances ... `rep` 1 to the set's reps, each exactly once".
   - Kind: contradicts. Severity: must (the re-runs would come from one runner instance, which R1 L30-31 and R3 rule out).
   - Fix: the full run records the within-margin points. A follow-up set generated from them is dispatched at reps 5 (5 matrix jobs) and judged on its max with `summarize --reps 1,2,3,4,5`.

2. **Refused catalogue pairs are dropped from the full set.**
   - Plan truth (L29): "every catalogue row of both kinds at each artifact the model admits (refused pairs listed in `dropped`...)".
   - R28 (L479): "Every catalogue row x 3 artifacts". R29 (L484) judges only admitted points (see G12).
   - Kind: relies on an unstated rule. Severity: nice.
   - Fix: cite G12 in the plan.

## 07-20 (full tier green, final gates)

Consistent. It runs R28 and R29 through 07-19's machinery, stops on an overrun or a non-ok reading (R29 L484-485), and widens by R12. Two dependencies:
- It inherits 07-19 #1: "re-runs within margin" (L100) must be the 5-job follow-up.
- Regenerating `tests/data/oper_boundary.json` after a widening (L111-112) depends on G6.

---

## Summary

### Plans that need replanning (structural change, not a text edit)

- **07-05**: Task 3 must become a sequence: walk-down dispatch, repeated until every failing cell reaches its first ok step; derive T; generate the confirm set; dispatch it. It must also carry R7's per-cell/T logic and its stops, lifted next steps, the cold-wall margin, and `wall_s` over all statuses.
- **07-06**: the contention driver changes:
  - hash-routed slots;
  - exactly one partner per other slot, submitted once;
  - cold wall measured inside the worker;
  - R2 statuses only.
  
  The drift mode is redesigned to R23. The solid-cache mode is removed.
- **07-15**:
  - bound set of 5 to 8 points;
  - per-slot partners with the unrunnable stop;
  - R15 load mix built on R27 steps 1-4, committed before the load run;
  - load env and encoding;
  - drop solid-cache and drift from this plan.
- **07-16**: split around the drift run. Derive R14 to R16, dispatch R23's drift at a 20 x timeout deadline, then derive R23. Also fix the computation order, plan R22's K below 4 load runs, and use the 256 MiB tmpfs step.
- **07-19**: Task 1's R5 re-run mechanism (a 5-matrix-job follow-up set in place of in-job repetitions).

### Plans that need only a text fix

- **07-07**: the `derive_walls` behaviour cases and stop list (#1-#4, #6-#7); the per-field `d` constants on the shared base field (#5); `--from walls-down-*` (#8).
- **07-08**: `identity` encoding, the two env vars, a shared request queue in place of `split_mix`.
- **07-09**: summarize-based fit input with expected reps; the C3 Q/rho formula; drop the 232-row note.
- **07-10**: rewrite option c3; tag `custom` against G10.
- **07-17**: the MemTotal wording.
- **07-18**: rewrite `boundary_points` to R27 step 5 over 07-15's D(A).

### Consistent

07-11, 07-12, 07-13, 07-14, 07-20 (07-20 is conditional on the 07-19 fix and G6).

### Protocol gaps the plans expose (owner ruling needed; R30 forbids rule text, so none is proposed)

- **G1 (R3, R9, R10).** R3 (L67-68, L73-74) confirms "the value the rule decides" and the next smaller walked value. When R9 or R10 decides "above 0" (L214, L228), there is no walked value, so the confirm set for that rule is undefined.
- **G2 (R3, R7).** The repetitions of the walk-down set are not stated. R3 (L57-59) lists `walls` at 1 and the confirm set at 5, but not the walk-down. R7 (L170-172) also does not say whether the steps are read one dispatch at a time or all at once (the readings below a cell's first ok step would then be outside "the readings this walk asks for", L183-184).
- **G3 (R5).** When a spread point has no median (any non-ok or incomplete repetition, R3 L61-64), R5 (L156-157) does not say whether m is taken over the rest or has no number.
- **G4 (R6).** "The largest point count whose summed measured `wall_s`" (L162-163) names no point order. It is also undefined for sets with no explore `wall_s` analogue: contention, load, drift, confirm, walk-down and full re-runs.
- **G5 (R12).** Which Runs II readings can widen e for R11's targets (L239-240, L253-254) is not stated:
  - contention at N of 2 or 3 (a shared peak, a wall under contention);
  - load request walls;
  - drift builds 2 to K.
- **G6 (R12, R14, R15, R27).** After an R12 widening, R27 says D(A) "is fixed before the load run" (L473), but its steps use the enveloped prediction (L452). The protocol does not say whether D(A), the R14 bound set and the R15 mix are recomputed, or stay as measured. 07-15, 07-18 and 07-20 each regenerate after a widening.
- **G7 (R15, R16).** A load repetition that is not `ok` (capped, killed, no_cgroup): R16 (L349-350) takes "the max over its 5 repetitions of each repetition's p95" and the "max load peak". It does not say whether that N does not qualify, or whether the phase stops.
- **G8 (R17).** "Shows no timeout" (L356): during the load run the server runs under the instrument deadline (07-08), and the R14 timeouts are derived only after R16's pick. Which timeout R17 tests against is not stated.
- **G9 (R22).** "`W(K)` is the peak with K solids cached per worker, measured in the load run" (L389). Not stated:
  - when the K below 4 load runs happen (after the pick, by implication of R15 L338);
  - at which N and how many repetitions;
  - how a per-worker W(K) is read from a single container peak.
- **G10 (R13).** Whether B-01 may be a triple outside C1 to C3 (L258-275). 07-10 offers `custom`. R30 (L489) forbids adding a threshold after the first reading.
- **G11 (R19).** "Costs at most 1.5x the seconds of the level below it" (L369): the statistic over 5 repetitions (median or max) is not stated.
- **G12 (R28).** "Every catalogue row x 3 artifacts" (L479) against R29 judging only admitted points (L484): whether refused pairs are read (unjudged) or dropped.
- **G13 (header).** Lines 5-6 say "Plans 07-03 to 07-17 apply these rules". Plans 07-18 to 07-20 apply R27 to R29 and are not named.
- **G14 (R23).** "The peak is read as R2 says" (L412). R2 reads the peak after a level-1 gzip (L39-41). Whether the drift child gzips each of the K outputs is not stated.
