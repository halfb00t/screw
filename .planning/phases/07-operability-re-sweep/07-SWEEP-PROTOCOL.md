# Phase 7 Sweep Protocol (pre-registered)

Written before any runner reading of the phase exists. Every selection rule, threshold, seed, set
and rounding that Phase 7 applies to a measurement is fixed here, so a bound is credible because
its rule was fixed before its data (the L11 method; `07-RESEARCH.md` Pattern 1). Plans 07-03 to
07-17 apply these rules; none of them may change one (R30).

- **Branch:** `gsd/phase-07-preregistration` (PR A: the harness, the point files and this file).
- **Point files:** written by `bench/oper_sets.py`; `python -m bench.oper_sets --check` and
  `tests/test_oper.py` fail when a committed file is not what it writes or when a sha below is not the
  git blob sha of the committed file. Git blob shas: `explore.json` `c2b5f05e23e46c09b0b73a424a85b9c178e703e3`,
  `spread.json` `52ef3a8506251a8254b05fb31cbf0ed4b6adaa06`, `walls.json`
  `b0b997307bdc0fb1c3e2e47b428730159616622c`, `controls.json`
  `0e95d12b50b155a57be1e32ec3dffe859d0b7174`, and the tracer `tracer.json`
  `16d1928fb1ab30f6fbac5179dfa34d74d7e276c1`.
- **Decisions applied:** `07-CONTEXT.md` D-01 to D-19, and the standing rules L02 (a number the tool
  prints is a number someone will cut metal to) and L11 (the thread grid and its method).
- **Terms.** A *reading* is one cold build and one export of one artifact of one part in one fresh
  container (R2). The *cold wall* of a reading is `build_s + export_s`. A *point* is a part and an
  artifact, or a probe. A *wall* is a limit of the kernel (it refuses or crashes), as against a
  *cost* (it is too slow or too large to serve), which the cost model and the timeouts own.
  *Admitted* means the cost model admits a part (R12). The mm values quoted from the macOS
  arm64 runs of `07-CONTEXT.md` are context and appear in no rule as a value.

## R1 - Where a bound comes from (D-01, D-15)

Every bound comes from a run of `.github/workflows/operability.yml` on an `ubuntu-latest` runner
(linux/amd64), with the image built from the dispatched commit, one fresh container of that image
per reading. The runner's `nproc`, `MemTotal`, CPU model, kernel, image id and kernel pair are
recorded in the header of every JSONL file; GitHub mixes CPU generations, so a bound that depends on
speed is taken over readings from at least two runner instances (R3). A figure from macOS, from an
emulated image or from spur is context; no rule below takes one as a value, and no threshold is
carried from spur or from a laptop run: every number a rule applies comes from a runner record.

## R2 - What a reading is and records (D-02, D-04, L02)

A reading is: a new container of the production image, `--memory` and `--memory-swap` both 12 GiB
(`bench.oper.CAP_BYTES`), a deadline of 600 s (`bench.oper.DEADLINE_S`), the solid cache cleared,
one build, one export of one artifact (`stl-preview`, `stl-fine` or `step`), a level-1 gzip of the
output, then the container's peak, read once and after the gzip so that it covers the build, the export
and the compression, and so that the cap test below sees the memory the gzip used. It records `build_s`, `export_s`, `bytes`, `triangles` (STL), `gzip1_bytes`, `maxrss_bytes`,
`memory_peak_bytes`, `oom_kills`, the kernel pair, the 1-minute load average before the reading and
the wall of the whole `docker run`. A *probe* (`tail`, `naive`, `one_pipe`) records `build_s`,
`solids`, `valid` (`isValid()`), the signed precise-volume ratio to the closed form and the same
peak fields, and no export.

The status of a reading is `ok`, `capped` (Docker `OOMKilled`, a cgroup `oom_kill`, or a peak at or
above 99 % of the cap), `killed` (past 600 s), `crashed` (a non-zero exit, a signal, or no valid
line; a SIGSEGV of the kernel is this), `refused` (the kernel or the production gate raised; the
class and text are kept) or `no_cgroup` (no readable peak). Only `ok` carries numbers; any other
status carries none (L02). The peak is the cgroup's: v2 `memory.peak` when `/sys/fs/cgroup` is a
`cgroup2` mount, else v1 `memory.max_usage_in_bytes`; neither readable is `no_cgroup`, never a
substituted figure.

## R3 - Repetitions (D-04, D-19)

Exploration takes 1 repetition per point (`explore`, `walls`, `controls`). 5 repetitions are taken
on `spread` and on every set that sets a bound: the Runs II bound set, the contention and load sets
and the walls confirm set. The 5 repetitions of a point are 5 matrix jobs (`rep` 1 to 5), so 5
runner instances. Per point the median and the max over its ok repetitions are recorded; a point
with any repetition that is not ok has no median and no max (`bench.oper.summarize`). Bounds use
the max.

The walls confirm set is, for each of R7 to R10, the readings at the value the rule decides and at
the next step past it, re-run at 5 repetitions. A point decides only when its 5 repetitions agree in
status; a disagreement keeps the stricter outcome, that is the lower wall.

The *next step past* a decided value is: for R7, 10 turns more (260 where 250 stands); for R8, the next
decade (1e6 where 1e5 stands); for R9 and R10, the next smaller walked value, which `walls` groups (c)
and (d) already hold. A step that lies past a validator's own cap would be refused before the kernel, so
`walls` group (f) holds it with a `lift`: one named guard replaced by one stated limit, `max_turns` for
`MAX_TURNS` and `max_mm` for the `le` bound of every length field. Every other validator still runs,
and the reading records the lift (`bench/oper_lift.py`). A reading past a cap awards nothing: R7 and R8
never raise a cap above its present value.

## R4 - The four first sets (D-04, D-05, D-08, D-17, D-18)

`bench/oper_sets.py` is the only definition; `python -m bench.oper_sets --check` fails when a
committed file is not what it writes, and `tests/test_oper.py` runs that in `make verify`. Floats
are written with `repr`; the same code writes the same bytes, in the order it lists the points. A
combination the parameter model refuses (`KINDS[kind].model_validate`) is not measured: it is listed
in the file's `dropped` array with the pydantic error type. `s` and `k` written as multiples of `d`
(1.6 d, 0.6 d, and the like) are formed as decimals and rounded to 6 significant figures.

| set | reps | shards | deadline_s | points | dropped parts | purpose |
| --- | --- | --- | --- | --- | --- | --- |
| explore | 1 | 40 | 600 | 1692 | 76 | fit data for the cost model (R11) |
| spread | 5 | 12 | 600 | 12 | 0 | the margin of repeated cold readings (R5) |
| walls | 1 | 20 | 600 | 752 | 0 | the kernel outer walls (R7 to R10) |
| controls | 1 | 4 | 600 | 69 | 0 | the known-bad constructions, natively (L11 platform note) |

Every set runs at 600 s per reading; the shard counts are chosen before any timing exists and R6
re-sizes them from the explore readings.

**explore.** (a) Every `catalogue()` bolt row (294) at `stl-preview`, `stl-fine` and `step`, with the
row's expanded fields and its id as `preset`; (b) every `nut_catalogue()` row (14), the same three
artifacts. (c) The bolt factorial: `d` in {1, 3, 10, 30, 100, 300, 1000}, `pitch` in {0.1, 0.35, 1,
3, 10}, turns in {3, 30, 240}, both hands, with `thread_length = length = turns x pitch` formed as
an exact decimal (so `length / pitch` is an integer by construction), `s = 1.6 d`, `k = 0.6 d`; it
breaks the collinearity of `d` and `pitch` that the catalogue has. (d) The nut factorial: `d` in {3,
10, 30, 100}, `pitch` in {0.35, 1, 3.5}, `m` in {0.8 d, 3 d}, `s` in {1.6 d, 4 d}, `clearance` in
{0.15, 5.0}, right hand, plus the left-hand copy of the `clearance` 0.15, `s` 1.6 d subset. (e) The
four recorded corners at the artifact each was recorded with: d 100 x 200 at the default pitch
(`stl-fine`), d 100, pitch 5, length 1250 (`stl-fine`), d 6, pitch 0.1, length 25 (`stl-fine`), and
d 1e5, pitch 1, length 1 (`stl-preview`). The integer `L / P` count over the catalogue is decided on
exact decimals (`calc.thread._exact`): 201 of the 294 rows, printed by the generator.
The fourth corner is not a request anyone can make: `d` = 1e5 needs `s` above `d` and `s` is bounded
by the same 1e5 (`head_too_small` with `less_than_equal`), so it is in `dropped` and is not measured;
`walls` walks the largest `d` that the ceiling allows. The 76 dropped explore parts are factorial
combinations the model refuses (`pitch_too_coarse`, `nut_too_thin`, `turn_cap`) and that one corner.

**spread.** The default bolt, the default nut, the last bolt row (`iso4014:M20x200`) and the last nut
row (`iso4032:M20`), at the three artifacts.

**walls** (`stl-preview` unless a probe). (a) Turns: for each of the 15 L11 sizes and both hands, a
bolt with `thread_length = length = 250 x pitch` and a nut with `m = 248 x pitch` (the void the
builder makes, `m + 2 pitch`, is 250 turns), exact decimals, `s = 1.6 d`, `k = 0.6 d`. (b) Field
ceilings, for X in {1e3, 1e4, 1e5} mm: a bolt with `s` = X and `d` the largest number of 6
significant figures under X (999.999, 9999.99, 99999.9; the head rule is `s > d`, so no larger `d` is
admitted at that `s`; pitch 1, `thread_length` 1, `k = 0.6 d`); bolt `length` = X; bolt `s` =
X; bolt `k` = X; bolt `thread_length = length = X` at `pitch = X / 250` and `d = 2 pitch` rounded up
to 6 figures; nut `s` = X; nut `m` = X at `pitch` = X / 248 rounded up to 6 figures (so the void
stays at or under 250 turns), `d = 2.5 pitch`, `s = 1.6 d`; nut `clearance`: the default nut (`d` 6)
with `s` = X and `clearance` the largest number of 6 significant figures under (X - 6) / 2 (496.999,
4996.99, 49996.9; `nut_too_thin` is `s > d + 2 clearance`, so no larger clearance is admitted at that `s`
and the field's own bound of X cannot be reached). (c) Tails: the `tail` probe at (d, pitch) in
{(6, 1), (2, 0.4), (20, 2.5)}, both hands, 3 whole turns plus a tail in {1e-2, 1e-3, ... 1e-9} mm,
with the builder's guard (`MIN_TAIL_MM`) lowered inside the probe only and restored after it.
(d) Root radius: for each of the 15 sizes, both hands, and `r` in {1e-2, 3e-3, 1e-3, 3e-4, 1e-4,
3e-5, 1e-5, 3e-6, 1e-6} mm, a bolt whose pitch solves `d / 2 - thread_depth(pitch) = r` and a nut
whose pitch solves `d / 2 - thread_depth(pitch) + 0.15 = r`, 3 turns (nut `m` = 3 pitch). The pitch
is solved to full float precision and not rounded to 6 figures: a 6-figure pitch moves the root
radius by up to about 5e-6 mm, which is more than the 1e-6 mm end of the walk, so the radius named
in the label would not be the radius walked. (e) The nuts the two open nut debt items name, so their
fate is decided by records: the lead-in item's M2 (m 12), M8 (m 38) and M14 (m 46) at `clearance`
0.1 and `s` in {1e3, 1e4, 1e5}, and the countersink item's `d` 2, `s` 4, `m` 3 nuts at `clearance`
0.05 with pitch 1.5 and 1.8 and at `clearance` 0.01 with pitch 1.5. (f) Past the caps, the
confirmation probes of R3, each with the one guard it needs lifted (`lift`): the rod and the void of (a)
at 260 turns (`max_turns` 260; `m = 258 x pitch`), and the eight corners of (b) at X = 1e6 mm
(`max_mm` 1e6), same constructions, labelled `beyond-`.

**controls.** `naive_sweep_fuse` at {10 pitch, 10, 20, standard max} mm and `one_pipe` at the
standard max and at 100, 160, 200 and 250 turns, on the sample sizes (M2, M2.5, M3, M6, M8, M10,
M16, M20), right hand, at the positions of `thread_spike._block_controls`. No gate is applied; each
reading records the solid count, `isValid()` and the signed precise-volume ratio, or the kernel's
error text. The ruled-surface rows need a reference package and are out of this set.

## R5 - The margin (D-19)

The margin `m` is the largest `max / median - 1` of the cold wall (`build_s + export_s`) over the
`spread` points, from their 5 repetitions. A bulk row of the full tier (R28), read once, is re-run at
5 repetitions when its single cold wall x (1 + `m`) reaches its artifact's timeout.

## R6 - Shard size (D-19)

For a set with a new run, the shard size is the largest point count whose summed measured `wall_s`
(from the explore records, per artifact and kind) stays under half the measure job's
`timeout-minutes`; the shard count is the point count divided by it, rounded up. Half leaves the
other half for a slower runner instance and for the image build.

## R7 - MAX_TURNS (D-08)

`MAX_TURNS` stays 250 if every 250-turn wall reading (`walls`, group (a): bolt rod and nut void, 15
sizes, both hands) is `ok`. A `refused` or `crashed` reading at a size starts a walk-down set at 240,
230, ... (step 10 turns) for that size and hand and kind; `MAX_TURNS` becomes the largest step that is
`ok` at every size, hand and kind. A `killed` or `capped` reading is cost, not a kernel wall: the cost
model owns it and it moves no wall.

## R8 - The field ceilings (D-08)

The readings that bear on a field (`walls`, group (b) and (e)): bolt `d` the `ceiling-bolt-d` reading;
bolt `length` the `ceiling-bolt-length` and `ceiling-bolt-thread` readings; bolt `s` the
`ceiling-bolt-s` and `ceiling-bolt-d` readings; bolt `k` the `ceiling-bolt-k` reading; bolt
`thread_length` the `ceiling-bolt-thread` reading; nut `s` the `ceiling-nut-s` reading and the
`nutlead` readings; nut `m` the `ceiling-nut-m` reading; nut `clearance` the `ceiling-nut-clearance` reading. A field's ceiling is the largest decade in {1e3, 1e4, 1e5} mm at which
every reading that bears on it is `ok`, and its value is the field's *tested value* at that decade: X,
except for the bolt `d`, whose tested value is the largest number of 6 significant figures under X
(99999.9 at 1e5), and the nut `clearance`, whose tested value is the largest under (X - 6) / 2
(49996.9 at 1e5): the readings never hold either at X, and the head and nut rules admit nothing between
the two. A ceiling is never written above a value a reading tested. A `refused` or `crashed` reading counts against its decade;
a `killed` or `capped` reading is cost and does not move a wall, but cannot raise one either (that
decade is not confirmed). `MAX_FIELD_MM` is the ceiling value the most fields share, a tie going to the
lower value, and each field whose ceiling differs gets its own named constant
(`MAX_<KIND>_<FIELD>_MM`). If a field has no `ok` decade, the phase stops and asks the owner: there
is no number.

## R9 - MIN_TAIL_MM (D-08)

Let F be the largest `tail` in `walls` group (c) whose reading is `refused` or `crashed` at any size or
hand (F = 0 when none fails). `MIN_TAIL_MM` is the smallest power of ten at or above 100 F. If no reading
fails down to 1e-9 mm, the floor stays "above 0" and the entry says the walk reached 1e-9 mm. 100 is
two decades, a margin fixed here before any reading; it is a margin, not a measured figure.

The value V this names stands only on `ok` readings. V must be a tail the walk holds (at most 1e-2),
and every reading of group (c) at a tail of V or more, at every size and hand, must be `ok`; for
"above 0", every reading of group (c) must be `ok`. A
`killed` or `capped` reading sets no F, being cost and not a wall, but it cannot support a bound
either (R8). Otherwise there is no number: the phase stops and asks the owner.

## R10 - MIN_ROOT_RADIUS_MM (D-18)

Let F be the largest root radius `r` in `walls` group (d) whose reading is `refused` or `crashed`, at
any size, hand, rod or void (F = 0 when none fails). `MIN_ROOT_RADIUS_MM` is the smallest power of ten
at or above 10 F. If no reading fails down to 1e-6 mm, the floor stays "above 0" and the entry says
the walk reached 1e-6 mm. 10 is one decade, the coarsest margin that is still tighter than the
tail rule's 100; the walk's own steps are half-decades, so 10 F sits at least two steps clear of F.

The value V this names stands only on `ok` readings. V must be a radius the walk holds (1e-2 to 1e-6
as a power of ten), and every reading of group (d) at a radius of V or more, at every size and hand,
rod and void, must be `ok`; for "above 0", every reading of group (d) must be `ok`. A `killed` or
`capped` reading sets no F but cannot support a bound either (R8). Otherwise there is no number: the
phase stops and asks the owner.

## R11 - The cost model's form (D-05, D-17)

One model per (kind, artifact, target), with the targets raw bytes, build seconds (the cold build
plus that artifact's export) and cgroup peak bytes. Ordinary least squares of the natural log of the
target on: for the bolt, ln d, ln pitch, ln turns (built thread length divided by pitch,
`calc.thread.built_thread_length`), ln length, ln s, ln k and `left_hand` (0 or 1); for the nut, ln
d, ln pitch, ln s, ln m, `clearance` and `left_hand`. It is fitted on the per-point max over the ok
readings of every `explore` and `spread` point; a point with no ok reading is not fitted. The
tessellation presets are kept (R23). The model is kernel-free (`calc` import boundary) and adds no
dependency.

## R12 - The envelope (D-07)

For each (kind, artifact, target) the envelope `e` is `max(0, largest actual / predicted - 1)` over
the fitted readings. A part is admitted if and only if `prediction x (1 + e)` is at most the budget
for every target. A later reading (Runs II, either tier) above its envelope widens `e` and is
recorded with its run id.

## R13 - The budget candidates (Q1, B-01)

For each artifact the budget is a (bytes, seconds, peak) triple. Three candidates are computed from
the explore fit and shown to the owner as a table, each with the rows kept and refused among the 294
bolt and 14 nut catalogue rows and among the explore free-space points, and the predicted worst
build and bytes:

- **C1, catalogue-complete.** Each component is the largest enveloped prediction over the catalogue
  rows of that artifact, so no catalogue row is refused.
- **C2, memory-bound.** The peak component is 4 x 10^9 bytes: the 16 x 10^9 bytes of D-02 in four
  equal shares, one per vCPU, of which three are builds (N is at most 3, D-03) and one is kept for
  uvicorn, gzip, the caches and tmpfs. The seconds and bytes components are unbounded.
- **C3, bytes-bound.** The fine STL raw bytes are at most Q = 4 x 10^9 / rho, where rho is the cgroup
  peak divided by the raw bytes of the `stl-fine` point with the largest raw bytes among the ok
  `explore` and `spread` points (the per-point max, R11): C2's peak share written as fine STL bytes at
  the peak per output byte of the largest measured fine STL. The preview and STEP artifacts are
  bounded only by the walls (R7 to R10).

The owner rules (B-01). No candidate is a figure until then, and nothing downstream of the budget
(R14 to R29) runs before that ruling.

## R14 - The bound set, contention and the timeouts (D-09)

The bound set of an artifact is the 5 admitted points with the largest enveloped build-seconds
prediction, plus the worst measured admitted point (the largest cold wall in `explore`), which is
one of the 5 or a sixth. Contention runs, for every point P of the bound set and every N in {1, 2, 3}:
P on one slot and, on the other N - 1 slots, the N - 1 admitted points other than P with the largest
enveloped build-seconds prediction, all cold and submitted together; the slots are distinct workers of
the pool (chosen by the pool's affinity hash). Every (P, N) takes 5 repetitions (R3), so no
reading waits for a worker count that R16 has not yet picked. The *bound point* of an artifact is the P
whose max cold wall over its 5 repetitions at the picked N (R16) is the largest. The timeout of the
artifact is `ceil(2 x` that max `)` seconds. The 2 is D-09's factor.

## R15 - The load run (D-03)

The load run starts the server in the image with `SCREW_BUILD_WORKERS = N`, a queue depth of 2N
(`SCREW_MAX_QUEUED_BUILDS`) and 2N concurrent clients.

*The mix.* Per artifact, 20 admitted parts: the artifact's 3 edge points of R27, then the admitted
`explore` points in R27's draw order until there are 20 (the draw goes on past R27's 10 minutes if it
must). 20 is the floor of samples per reported p95, so each artifact reports its own p95 over its own 20.
The mix is the 60 requests (part, artifact), listed artifact by artifact in that order and shuffled once
by `random.Random(20261026).shuffle`; that order is the same in every repetition and at every N. A
client takes the next request as soon as its previous response is complete, and the first 2N start
together.

*The passes.* A repetition runs the mix twice back to back on one server, pass 1 and pass 2, in the
same order. The p95 (`statistics.quantiles(n=20)`, the 19th cut point) and the medians are over pass 1:
20 samples per artifact and 60 over all requests. Pass 2 serves R23. The container's cgroup peak is read
at the end of each pass.

*The caches.* Every repetition is a new container, so both caches start empty. `SCREW_EXPORT_CACHE_MB`
is 1, the smallest value the server accepts (`int_env` floors it at 1), so the export cache keeps no
output over 1 MiB and the load measures builds; `SCREW_SOLID_CACHE` is 4 unless R22 is measuring a K.
5 repetitions (R3).

## R16 - The worker count and mem_limit (D-02, D-03)

`W` is the max `memory_peak_bytes` over the N = 1 contention containers of every point of
every bound set (R14). `B` is the max idle-server peak
before load. `mem_limit(N)` is the larger of `W x N + B +` the export cache budget `+` the tmpfs
size, and the max load peak at N (read at the end of pass 2), rounded up to 256 MiB. N qualifies when `mem_limit(N)` is under
both 16 x 10^9 bytes and the smallest `MemTotal` any runner header recorded, and N is at most
`nproc - 1`. The pick is the qualifying N with the lowest load p95 over all requests (the max over
its 5 repetitions of each repetition's p95, D-04), ties to the smaller N. 256 MiB is a rounding
step fixed before the data: small against the 16 GB ceiling (about 1.7 %), large enough to be a visible
margin and not an arithmetic residue.

## R17 - The queue depth

`SCREW_MAX_QUEUED_BUILDS` stays 2N if the load run at the picked N shows no timeout and a peak at
most `mem_limit`; otherwise it is N.

## R18 - Retry-After (D-11)

`Retry-After` per artifact is `ceil(` the median built-request wall of that artifact in the load runs
at the picked N, pooled over the 5 repetitions, `x` the live queue depth `)`, at least 1 s. The
median is the shipped constant and the product is taken at run time, so a deployer's queue depth
moves it.

## R19 - The gzip level

Levels 1, 6 and 9 on the bound set's STL artifacts. A higher level is adopted only if it shrinks the
bytes by at least 10 % and costs at most 1.5x the seconds of the level below it (1 is the start).
The rule's shape is spur's; the thresholds are stated here for screw and are not carried figures.
10 % is the least saving worth a higher level and 1.5x the most extra time accepted for it; both
are round numbers chosen before any gzip reading, and neither is derived from a measurement.

## R20 - minimum_size

`minimum_size` is the smallest measured JSON body length from which every measured body shrinks at
the chosen level. The bodies are `/api/health`, every catalogue row's info document and
`/api/presets`.

## R21 - The export cache

`SCREW_EXPORT_CACHE_MB` holds both encodings (raw and gzip) of all three artifacts of the admitted
part with the largest such sum, rounded up to a whole MiB.

## R22 - The solid cache

`SCREW_SOLID_CACHE` stays 4 if `mem_limit` computed with `W(4)` at the picked N still qualifies
(R16), else it is the largest K in {3, 2, 1} that does. `W(K)` is the peak with K solids cached per
worker, measured in the load run.

## R23 - Tessellation, arenas and recycling

The tessellation presets are kept. `_release_arenas` is kept if the retained memory after an export
is lower with it than without. `max_tasks_per_child` stays unset unless the peak read after pass 2 of
the load run (R15) is higher than the peak read after pass 1 by more than one cached solid
(`W(4) - W(3)`); if it is, the phase stops and asks the owner, because no rule here sets a recycling value.

## R24 - SCREW_WORKERS

`SCREW_WORKERS` stays 1 if the `/api/health` p95 under load at the picked N is at most the probe's
1 s inner timeout (the `urlopen(..., timeout=1)` of the `HEALTHCHECK`); otherwise the phase stops and
asks the owner.

## R25 - The HEALTHCHECK

`--timeout` is `ceil(2 x` the max health wall under load `)` seconds. `--start-period` is 2 x the max
time to the first healthy response, rounded up to 10 s. `--interval` 30 s and `--retries` 3 are
Docker's documented defaults and are cited as such.

## R26 - tmpfs

The `/tmp` tmpfs is at least the `stl-fine` byte budget x N or, where the budget (R13) leaves that
unbounded, the largest enveloped `stl-fine` bytes prediction over the admitted explore points x N,
rounded up to the 256 MiB step of R16 and inside `mem_limit`.

## R27 - The required tier (D-12)

Per artifact, the 3 admitted points nearest the budget edge (the largest enveloped prediction over the
budget), plus admitted `explore` points drawn in `random.Random(20261026)` order (the seed is the
date of the owner's rulings, 2026-10-26, written as an integer; any fixed integer would do, and this
one is fixed here) while the summed measured cold walls stay under 10 minutes (D-12's target).

## R28 - The full tier (D-12)

Every catalogue row x 3 artifacts, the nut factorial, and the dense boundary: per artifact, size and
hand, the largest admitted integer-turn length. One pass; R5 re-runs apply.

## R29 - When a tier fails (D-07, D-12)

A tier fails on any non-`ok` reading of an admitted point, a cold wall above its artifact's timeout,
or `actual / predicted - 1` above its envelope for any target.

## R30 - Immutability

No rule, threshold, seed, set or rounding in R1 to R29 is changed, added or dropped after the first
runner reading of the phase. This file is committed on `gsd/phase-07-preregistration` before any
reading exists and lands on `main` with PR A (plan 07-04). A harness fix that changes no rule (a bug
in the parent, the child or the workflow) is recorded under "Harness fixes" below with its commit
sha, and nothing else in this file is edited. A rule change stops the phase for the owner's ruling.
The point files change only through `bench/oper_sets.py`, so the same rule binds them.

## Debt this campaign leaves open

`docs/tech_debt/active/2026-10-10-spike-protocol-amendments-before-next-campaign.md` stays active.
Its WR-03 (`Campaign.decisive`) and IN-02 (`PAIR_TIMEOUT_S`) amend the thread-spike harness, which
this campaign does not run: the controls are `bench.oper` probes (R4), and `bench.oper` records the
1-minute load average before every reading (R2), which is the WR-03 idea in the new harness. The
amendments still need the owner's ruling the item names, for the next thread-spike campaign.

`docs/tech_debt/active/2026-10-14-m18-probe-one-entry-has-no-deadline-during-a-run.md` stays active.
`bench/m18_probe.py` is not reused, and every `bench.oper` reading is killed at the parent's
`DEADLINE_S` (R2). Neither item's trigger fires in this phase, so neither INDEX row moves.

## Harness fixes

None yet. Append `<date> <commit sha> <one line: what broke and why no rule changed>` below.
