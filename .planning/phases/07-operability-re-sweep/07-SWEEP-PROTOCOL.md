# Phase 7 Sweep Protocol (pre-registered)

Written before any runner reading of the phase exists. Every selection rule, threshold, seed, set
and rounding that Phase 7 applies to a measurement is fixed here, so a bound is credible because
its rule was fixed before its data (the L11 method; `07-RESEARCH.md` Pattern 1). Plans 07-03 to
07-21 apply these rules; none of them may change one (R30).

- **Branch:** `gsd/phase-07-preregistration` (PR A: the harness, the point files and this file).
- **Point files:** written by `bench/oper_sets.py`; `python -m bench.oper_sets --check` and
  `tests/test_oper.py` fail when a committed file is not what it writes or when a sha below is not the
  git blob sha of the committed file. Git blob shas: `explore.json` `c2b5f05e23e46c09b0b73a424a85b9c178e703e3`,
  `spread.json` `52ef3a8506251a8254b05fb31cbf0ed4b6adaa06`, `walls.json`
  `6f14e72c8b98e46b429f9332672d5f2377125baf`, `controls.json`
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

Exploration takes 1 repetition per point (`explore`, `walls`, `controls`, the R7 walk-down set and the void walk of R4 (d)). 5 repetitions are taken
on `spread` and on every set that sets a bound: the Runs II bound set, the contention and load sets
and the walls confirm set. The 5 repetitions of a point are 5 matrix jobs (`rep` 1 to 5), so 5
runner instances. Per point the median and the max over its ok repetitions are recorded; a point
with any repetition that is not ok has no median and no max (`bench.oper.summarize`). The
repetitions must also be the ones asked for: `rep` 1 to the set's reps, each exactly once. A point
with four of five, or with five copies of one (a lost job artifact, a file downloaded twice), is
`incomplete` and has no median and no max, so it supplies no bound and no fit figure. Bounds use
the max.

The walls confirm set is, for each of R7 to R10, the readings at the value the rule decides and at
the next step past it, re-run at 5 repetitions. For R7 the value is the candidate T, read for every
size, hand and kind (R7). A point decides only when its 5 repetitions agree in
status; a disagreement keeps the stricter outcome, that is the lower wall.

The *next step past* a decided value is: for R7, 10 turns more (260 where 250 stands); for R8, the next
decade (1e6 where 1e5 stands); for R9 and R10, the next smaller walked value, which `walls` groups (c)
and (d) already hold; for R10 the confirm reads the rods of group (d) only, as the nut voids bear on
no bound (R10). Where R9 or R10 decides "above 0", no walked value lies below the decided one, so
the confirm set for that rule is the smallest walked value (tail 1e-9 mm, root radius 1e-6 mm) for every
cell of the rule, at 5 repetitions, and nothing past it. Any reading there that is not `ok` awards no
floor, and the phase stops and asks the owner, as R7 does. A step that lies past a validator's own cap would be refused before the kernel, so
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
| walls | 1 | 20 | 600 | 756 | 0 | the kernel outer walls (R7 to R10) |
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
and the field's own bound of X cannot be reached); nut `d`: a nut with `s` = X, the default `clearance`
(0.15) and `d` the largest number of 6 significant figures under X - 2 x 0.15 (999.699, 9999.69, 99999.6;
the same rule leaves no larger `d` at that `s`, so the field's own bound of X cannot be reached). (c) Tails: the `tail` probe at (d, pitch) in
{(6, 1), (2, 0.4), (20, 2.5)}, both hands, 3 whole turns plus a tail in {1e-2, 1e-3, ... 1e-9} mm,
with the builder's guard (`MIN_TAIL_MM`) lowered inside the probe only and restored after it.
(d) Root radius: for each of the 15 sizes, both hands, and `r` in {1e-2, 3e-3, 1e-3, 3e-4, 1e-4,
3e-5, 1e-5, 3e-6, 1e-6} mm, a bolt whose pitch solves `d / 2 - thread_depth(pitch) = r` and a nut
whose pitch solves `d / 2 - thread_depth(pitch) + 0.15 = r`, 3 turns (nut `m` = 3 pitch). The pitch
is solved to full float precision and not rounded to 6 figures: a 6-figure pitch moves the root
radius by up to about 5e-6 mm, which is more than the 1e-6 mm end of the walk, so the radius named
in the label would not be the radius walked. Above 1e-2 mm the nut voids are walked in a set of their
own, the void walk (`walls-voids`), added after the first runner reading by the owner's ruling that
R30 asks for: for each of the 15 sizes and both hands, the nut of this group, built and labelled the
same way, at `r` in {3e-2, 1e-1, 3e-1, 1} mm, 120 points at 1 repetition and R2's deadline. Every
pitch it solves is positive. No rod is walked above 1e-2 mm, and the void walk is not extended past
1 mm. (e) The nuts the two open nut debt items name, so their
fate is decided by records: the lead-in item's M2 (m 12), M8 (m 38) and M14 (m 46) at `clearance`
0.1 and `s` in {1e3, 1e4, 1e5}, and the countersink item's `d` 2, `s` 4, `m` 3 nuts at `clearance`
0.05 with pitch 1.5 and 1.8 and at `clearance` 0.01 with pitch 1.5. (f) Past the caps, the
confirmation probes of R3, each with the one guard it needs lifted (`lift`): the rod and the void of (a)
at 260 turns (`max_turns` 260; `m = 258 x pitch`), and the nine corners of (b) at X = 1e6 mm
(`max_mm` 1e6), same constructions, labelled `beyond-`.

**controls.** `naive_sweep_fuse` at {10 pitch, 10, 20, standard max} mm and `one_pipe` at the
standard max and at 100, 160, 200 and 250 turns, on the sample sizes (M2, M2.5, M3, M6, M8, M10,
M16, M20), right hand, at the positions of `thread_spike._block_controls`. No gate is applied; each
reading records the solid count, `isValid()` and the signed precise-volume ratio, or the kernel's
error text. The ruled-surface rows need a reference package and are out of this set.

## R5 - The margin (D-19)

The margin `m` is the largest `max / median - 1` of the cold wall (`build_s + export_s`) over the
`spread` points, from their 5 repetitions. If any `spread` point has no median (a repetition that is
not `ok`, or repetitions that are incomplete, R3), `m` has no number and the phase stops and asks the
owner. A bulk row of the full tier (R28), read once, is re-run at
5 repetitions when its single cold wall x (1 + `m`) reaches its artifact's timeout.

## R6 - Shard size (D-19)

For a set with a new run, a shard is a run of consecutive points of the set in the order of its
file, and each point is charged a number of seconds. A shard is the longest such prefix of the points
not yet placed whose summed charge stays under half the measure job's `timeout-minutes`; the shard
count is the number of shards that places every point. Half leaves the other half for a slower runner
instance and for the image build. A point of an explore-like set whose own charge is not under that half
stops the phase and asks the owner; a reading of the contention, load, drift, gzip and arena sets is
ruled below.

For a set of explore-like parts (`walls`, the walls confirm set, the R7 walk-down set and the void walk of R4 (d)), each point is
charged the largest `wall_s` of any `explore` reading in its (kind, artifact) group, whatever the
status of that reading (`wall_s` is kept for every status, R2), so a part is charged the slowest cold
wall measured for its kind of part at its artifact. A (kind, artifact) group with no `explore` reading
is charged its `deadline_s`, as no figure is invented for it.

For the contention, load and drift sets, no `explore` reading is a bound on a point, so each reading is
charged the deadline its own rule sets: 600 s where R2's deadline applies, and K x
the artifact's timeout for a drift reading, that is 20 x that timeout (R23), which is not 600 s. The
shards are cut by the same rule, so a reading whose deadline alone fills a shard runs in a job of its
own. A reading whose deadline is not under half the job's `timeout-minutes` stops the phase and asks
the owner: the job timeout also counts the runner setup, the image build and the upload of the
records, and the other half is kept for them.

The R19 gzip set and the R23 arena set are charged the same way: each of their readings is charged
R2's 600 s, and their shards are cut, and a reading that does not fit stops the phase, by the rule
above. Their parts have `explore` readings, but those walls are not taken as a bound: a gzip reading
also compresses its output at levels 6 and 9, which no `explore` wall includes, and the arena readings
are charged alike, so the charge of neither set rests on a measured wall.

## R7 - MAX_TURNS (D-08)

A *cell* is a size, a hand and a kind (bolt rod or nut void): 15 x 2 x 2. A cell's *first ok step* is
250 if its 250-turn reading (`walls`, group (a)) is `ok`. A cell whose 250-turn reading is `refused`
or `crashed` is in the *walk-down set*: the set reads every such cell at every step of 10 turns from
240 down to 10, at 1 repetition, in one dispatch. The cell's first ok step is the highest of those
steps whose reading is `ok`. A cell's readings below its first ok step are recorded and used for
nothing: they are not boundary evidence (below) and no rule reads them; the 5-repetition confirm at T
decides. A cell with no `ok` step has no first ok step, so no turn bound is awarded and the phase
stops and asks the owner.

The *candidate* T is the smallest first ok step over the cells. It is a provisional common value: the
cells need not end their walks at the same step. `MAX_TURNS` is T only if the confirmation readings
(R3: the readings at T and at the next step past it, 5 repetitions) at T are `ok`, in all 5
repetitions, for every cell. The confirmation set reads every cell at T, at 5 repetitions taken fresh,
whether or not that cell already has a 1-repetition reading at T (its own first ok step, or a step
below it that the complete walk-down read): such a reading is not one of the 5 and stands in for none
of them. A confirmation reading at T that is not `ok`, or is missing, awards no turn bound, 250
included, and the phase stops and asks the owner; no other value is tried.

The boundary evidence is every reading this walk asks for: the 250-turn readings, each walk-down
reading down to a cell's first ok step, and the confirmation readings at T. The bound stands only on
`ok` readings. A `killed`, `capped` or `no_cgroup` reading in that evidence, or a reading it asks for
that is missing, is cost, an unreadable peak or a gap, not a kernel wall: it starts no walk-down and
moves no wall, and it cannot support a bound either. No turn bound is then awarded, 250 included, and
the phase stops and asks the owner.

## R8 - The field ceilings (D-08)

The readings that bear on a field (`walls`, group (b) and (e)): bolt `d` the `ceiling-bolt-d` reading;
bolt `length` the `ceiling-bolt-length` and `ceiling-bolt-thread` readings; bolt `s` the
`ceiling-bolt-s` and `ceiling-bolt-d` readings; bolt `k` the `ceiling-bolt-k` reading; bolt
`thread_length` the `ceiling-bolt-thread` reading; nut `s` the `ceiling-nut-s` reading and the
`nutlead` readings; nut `d` the `ceiling-nut-d` reading; nut `m` the `ceiling-nut-m` reading; nut
`clearance` the `ceiling-nut-clearance` reading. A field's ceiling is the largest decade in {1e3, 1e4, 1e5} mm at which
every reading that bears on it is `ok`, and its value is the field's *tested value* at that decade: X,
except for the bolt `d`, whose tested value is the largest number of 6 significant figures under X
(99999.9 at 1e5), the nut `clearance`, whose tested value is the largest under (X - 6) / 2
(49996.9 at 1e5), and the nut `d`, whose tested value is the largest under X - 2 x 0.15 (99999.6 at
1e5): the readings never hold any of the three at X, and the head and nut rules admit nothing between
the tested value and X. A ceiling is never written above a value a reading tested. A `refused` or `crashed` reading counts against its decade;
a `killed` or `capped` reading is cost and does not move a wall, but cannot raise one either (that
decade is not confirmed). `MAX_FIELD_MM` is the ceiling value the most fields share, a tie going to the
lower value, and each field whose ceiling differs gets its own named constant
(`MAX_<KIND>_<FIELD>_MM`). If a field has no `ok` decade, the phase stops and asks the owner: there
is no number.

The nut `d` gets no constant of its own. Its reading at 1e3 was `ok` once and `capped` in all 5 confirm
repetitions, and its reading at 1e4 is `refused`, so it has no confirmed decade. A `capped` reading is
cost, so the cost model's admission (R12) and the timeouts bound a large nut, not a wall. The nut `d`
stays under the shared `MAX_FIELD_MM` only while that value lies below the nut `d`'s first refused
decade (1e4). A shared value at or above that decade stops the phase and asks the owner. This
sentence was added after the first runner reading by the owner's ruling that R30 asks for.

## R9 - MIN_TAIL_MM (D-08)

Let F be the largest `tail` in `walls` group (c) whose reading is `refused` or `crashed` at any size or
hand (F = 0 when none fails). `MIN_TAIL_MM` is the smallest power of ten at or above 100 F. If no reading
fails down to 1e-9 mm, the floor stays "above 0" and the entry says the walk reached 1e-9 mm, but only if
the confirm set of R3 at 1e-9 mm, for every size and hand, is `ok` in all 5 repetitions. 100 is
two decades, a margin fixed here before any reading; it is a margin, not a measured figure.

The value V this names stands only on `ok` readings. V must be a tail the walk holds (at most 1e-2),
and every reading of group (c) at a tail of V or more, at every size and hand, must be `ok`; for
"above 0", every reading of group (c) must be `ok`. A
`killed` or `capped` reading sets no F, being cost and not a wall, but it cannot support a bound
either (R8). Otherwise there is no number: the phase stops and asks the owner.

## R10 - MIN_ROOT_RADIUS_MM (D-18)

Let F be the largest root radius `r` of a rod in `walls` group (d) whose reading is `refused` or
`crashed`, at any size or hand (F = 0 when none fails). `MIN_ROOT_RADIUS_MM` is the smallest power of
ten at or above 10 F. If no rod reading fails down to 1e-6 mm, the floor stays "above 0" and the entry
says the walk reached 1e-6 mm, but only if the confirm set of R3 at 1e-6 mm, for every size and hand,
rods only, is `ok` in all 5 repetitions. 10 is one decade, the coarsest margin that is still tighter
than the tail rule's 100; the walk's own steps are half-decades, so 10 F sits at least two steps clear
of F.

The value V this names stands only on `ok` readings. V must be a radius the rods of group (d) hold, a
power of ten from 1e-2 mm down to 1e-6 mm, and every rod reading of group (d) at a radius of V or
more, at every size and hand, must be `ok`; for "above 0", every rod reading of group (d) must be
`ok`. A `killed` or `capped` reading sets no F, being cost and not a wall, but it cannot support a
bound either (R8). Otherwise there is no number: the phase stops and asks the owner.

The nut voids bear on no bound: the nut readings of group (d) and the readings of the void walk of R4
(d) are recorded, set no F, need not be `ok` for V and are not in the R3 confirm. The owner ruled this
after the first runner reading, once the void walk had been read, as R30 asks: in one reading each,
the voids failed up to a root radius that grows with `d`, so no single floor in millimetres holds
them. That is an observation and not a bound; a void the kernel refuses is refused by no guard before
the build, and stays open as debt.

## R11 - The cost model's form (D-05, D-17)

One model per (kind, artifact, target), with the targets raw bytes, build seconds (the cold build
plus that artifact's export) and cgroup peak bytes. Ordinary least squares of the natural log of the
target on: for the bolt, ln d, ln pitch, ln turns (built thread length divided by pitch,
`calc.thread.built_thread_length`), ln length, ln s, ln k and `left_hand` (0 or 1); for the nut, ln
d, ln pitch, ln s, ln m, `clearance` and `left_hand`. It is fitted on the per-point max of every
`explore` and `spread` point whose every repetition is `ok`; a point with any repetition that is not
`ok` has no max (R3) and is not fitted, however many of its other repetitions were `ok`. The
tessellation presets are kept (R23). The model is kernel-free (`calc` import boundary) and adds no
dependency.

A part whose head ratio lies above the band the fit saw is predicted no lower than anywhere in that
band, and one whose ratio lies below it no lower than at the band's low edge. The head ratios are the
bolt's k / d and s / d and the nut's s / d and m / d. Each ratio's band is its smallest and largest
value over the fitted points of its kind, each point's fields read through the parameter model so
that an omitted field takes its default; the bands are computed from the records by code and shipped
with the coefficients, never typed. For a part with any ratio outside its band, each target is
predicted raw and at every combination of edges of its out-of-band ratios, a ratio above its band
taking both edges (the smallest and the largest) and a ratio below it the smallest only, each such
field (k, s or m) set to the edge times d and every other field held; the prediction is the largest
of these, target by target, and R12 applies the envelope to it. Below the band this assumes, without
a measurement, that a smaller head never costs more than one at the low edge. Inside every band the
prediction is the fit's own, unchanged. The second campaign
reads, at 5 repetitions, per kind, artifact and ratio, at least one part above the band and one below
it, each a part this rule admits; a reading above its enveloped prediction stops the phase for the
owner and does not widen `e`. This sentence was added after the first runner reading by the owner's
ruling that R30 asks for.

## R12 - The envelope (D-07)

For each (kind, artifact, target) the envelope `e` is `max(0, largest actual / predicted - 1)` over
the fitted readings. A part is admitted if and only if `prediction x (1 + e)` is at most the budget
for every target. A later reading (Runs II, either tier) above its envelope widens `e` and is
recorded with its run id, but only a cold isolated reading widens it: a reading of a part in a fresh
container with no other build running, which is a part reading of either tier, a gzip reading of R19,
an arena reading of R23, a contention reading at N = 1 and build 1 of a drift repetition. A contended wall (a contention reading at N = 2 or 3), a load
request wall and a drift build 2 to K never widen `e`.

D(A) (R27 steps 1 to 4), the bound set (R14) and the load mix (R15) are each fixed once, from the
enveloped prediction they were first computed from, and are never redrawn when `e` widens. A widening
changes admission and the final numbers only.

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
  peak divided by the raw bytes of the `stl-fine` point with the largest raw bytes among the `explore`
  and `spread` points whose every repetition is `ok` (the per-point max, R11): C2's peak share written
  as fine STL bytes at the peak per output byte of the largest measured fine STL. The preview and STEP
  artifacts are bounded only by the walls (R7 to R10).

The owner rules (B-01), and the ruling is one of C1, C2 and C3: no other triple is offered or taken.
No candidate is a figure until then, and nothing downstream of the budget
(R14 to R29) runs before that ruling.

## R14 - The bound set, contention and the timeouts (D-09)

The bound set of an artifact is the 5 admitted points with the largest enveloped build-seconds
prediction, plus the worst measured admitted point (the largest cold wall in `explore`), plus the two
memory extrema: the admitted point with the largest enveloped peak-bytes prediction and the admitted
point with the largest measured peak (the largest `memory_peak_bytes` in `explore`). The candidates are
the admitted `explore` points at that artifact (for the two measured choices, those whose reading is
`ok`), a tie going to the label that sorts first; a point that is in two of these groups counts once, so the set holds 5 to 8 points. The set is drawn once and is not redrawn when `e` widens (R12). The
memory extrema are in it because W (R16) is read from the bound set's containers, and the heaviest
point in memory need not be among the slowest. Contention runs, for every point P of the bound set and every N in {1, 2, 3}:
P on one slot and, on each of the other N - 1 slots, one admitted point of the same artifact, all cold
and submitted together. A slot is a worker of the pool, which routes a part to worker `hash(p) % N`
with `p = KINDS[kind].model_validate(params)` (`BuildPool.executor_for`); the hash is of the field
values and is the same in every process, so every slot is computed when the set is built, before any
server runs. P has its own slot. The partner of each other slot is the admitted point other than P
whose slot at this N is that one and whose enveloped build-seconds prediction is the largest, a tie
going to the label that sorts first. The N points are therefore on N distinct workers and none waits
behind another. A slot that holds no admitted point leaves that (P, N) unrunnable, and the phase stops
and asks the owner: no rule here puts two points on one worker, which would leave a worker idle and
measure less than N-way contention. The partners are chosen for each (P, N), since the slots depend
on N. Every (P, N) takes 5 repetitions (R3), so no
reading waits for a worker count that R16 has not yet picked. The *bound point* of an artifact is the P
whose max cold wall over its 5 repetitions at the picked N (R16) is the largest. The timeout of the
artifact is `ceil(2 x` that max `)` seconds. The 2 is D-09's factor.

## R15 - The load run (D-03)

The load run starts the server in the image with `SCREW_BUILD_WORKERS = N`, a queue depth of 2N
(`SCREW_MAX_QUEUED_BUILDS`) and 2N concurrent clients.

*The mix.* The load run measures the cold worst case: no request repeats a part anywhere in a run,
so neither cache can hit. A run has 20 parts for each artifact. 20 is the floor of samples per
reported p95, so each artifact reports its own p95 over its own 20. The artifacts take their parts in
the order `stl-fine`, `step`, `stl-preview`, fixed here before any reading: the fine STL, whose output
is the largest, takes first pick and `stl-preview`, the coarser mesh of the same solid, the last. Each
artifact takes its parts on its own, in two steps:

1. its 3 edge parts: the first 3 parts of its own edge ranking (R27 step 3: every candidate by edge
   ratio, largest first, a tie going to the label that sorts first) that are unused and whose
   `explore` reading is `ok`;
2. its 17 draw parts: the first 17 parts of its draw order (R27 step 4) that are unused and whose
   `explore` reading is `ok` (a part that failed there is a tier failure, R29, and not a load sample).

A part is used once any artifact has taken it, so no part appears twice in a run, the three artifacts
of one part included. An artifact whose edge parts an earlier artifact took takes its next-ranked ones
by its own edge ranking, so every artifact keeps 3 edge points; the walk goes on past R27's 10
minutes. If a list cannot supply the parts an artifact needs, the phase stops and asks the owner: no
part is repeated to fill a gap. The mix of a run is its 60 requests (part, artifact), listed in the
order the artifacts took them and shuffled once by a new `random.Random(20261026).shuffle`; the order
is the same in every repetition and at every N. A client takes the next request as soon as its
previous response is complete, and the first 2N start together. The `/api/health` probes of R24 and
R25 are not part of the mix. The mix is drawn once and is not redrawn when `e` widens (R12).

*The measures.* The p95 (`statistics.quantiles(n=20)`, the 19th cut point) and the medians are over
the run: 20 samples per artifact and 60 over all requests. The container's cgroup peak is read once,
at the end of the run; it is a high-water mark, so that read covers the whole run. The run measures
latency and the peak under load; growth across repeated builds is the drift run of R23.

*The caches and the encoding.* Every repetition is a new container, so both caches start empty, and no
part repeats, so neither can hit. `SCREW_EXPORT_CACHE_MB` is 1, the smallest value the server accepts
(`int_env` floors it at 1): that cache can still store an output under 1 MiB, but with no repeated part
it serves none, so the load measures builds. `SCREW_SOLID_CACHE` is 4 unless R22 is measuring a K. Every
request carries `Accept-Encoding: identity`, so no response is compressed and the load measures
builds and serving, not gzip (R19 owns the level). 5 repetitions (R3).

## R16 - The worker count and mem_limit (D-02, D-03)

`W` is the max `memory_peak_bytes` over the N = 1 contention containers of every point of
every bound set (R14), the memory extrema of each included. `B` is the max idle-server peak
before load. `mem_limit(N)` is the larger of `W x N + B +` the export cache budget `+` the tmpfs
size, and the max load peak at N (read at the end of the load run, R15), rounded up to 256 MiB. N
qualifies when `mem_limit(N)` is under both 16 x 10^9 bytes and the smallest `MemTotal` any runner header recorded, and N is at most
`nproc - 1`, and only if all 5 of its load repetitions are `ok`. If no N qualifies, the phase stops
and asks the owner. The pick is the qualifying N with the lowest load p95 over all requests (the max over
its 5 repetitions of each repetition's p95, D-04), ties to the smaller N. 256 MiB is a rounding
step fixed before the data: small against the 16 GB ceiling (about 1.7 %), large enough to be a visible
margin and not an arithmetic residue. The `mem_limit` that ships is the larger of `mem_limit(N)` at
the picked N built from this W and the one built from `W(K)` at the K R22 keeps.

## R17 - The queue depth

`SCREW_MAX_QUEUED_BUILDS` stays 2N if the load run at the picked N shows no timeout and a peak at
most `mem_limit`; otherwise it is N. "No timeout" is checked on the existing load records of the
picked N, after R14 has derived the timeouts: no request's wall, its queue wait plus its build, may
exceed the timeout of its artifact under the queue-aware deadline (plan 07-02). The check needs no
further runner time.

## R18 - Retry-After (D-11)

`Retry-After` per artifact is `ceil(` the median built-request wall of that artifact in the load runs
at the picked N, pooled over the 5 repetitions, `x` the live queue depth `)`, at least 1 s. The
median is the shipped constant and the product is taken at run time, so a deployer's queue depth
moves it.

## R19 - The gzip level

Levels 1, 6 and 9 on the bound set's STL artifacts. A level's seconds and bytes are each the max over
5 repetitions (R3), and the comparison below uses those maxima. Level 1 is the start; level 6 is tried
first, then level 9. A higher level is adopted only if it shrinks the bytes by at least 10 % and costs
at most 1.5x the seconds of the adopted level, and it must pass at every point of the STL bound set on
its own: the points of the `stl-preview` and `stl-fine` bound sets (R14) together, 10 to 16 points.
Level 9 is compared with the adopted level, not with level 6: with level 1 when level 6 was not
adopted. If a max the gzip comparison needs is missing (R3: a point with any repetition that is not
`ok` has no max), the phase stops and asks the owner.
The rule's shape is spur's; the thresholds are stated here for screw and are not carried figures.
10 % is the least saving worth a higher level and 1.5x the most extra time accepted for it; both
are round numbers chosen before any gzip reading, and neither is derived from a measurement.

## R20 - minimum_size

`minimum_size` is the smallest measured JSON body length from which every measured body shrinks at
the chosen level. The bodies are `/api/health`, every catalogue row's info document and
`/api/presets`.

## R21 - The export cache

`SCREW_EXPORT_CACHE_MB` holds both encodings (raw and gzip) of all three artifacts of the candidate
part with the largest such sum, rounded up to a whole MiB. The candidates are the `explore` parts that
are admitted at all 3 artifacts and whose `explore` readings are `ok` at all 3. A candidate's sum is
the raw `bytes` and the `gzip1_bytes` of those three readings: the gzip level-1 bytes are the upper
bound of the gzip encoding at any level R19 adopts. If any R19 reading shows the bytes at level 6 or 9
above the bytes at level 1, that bound does not hold and the phase stops and asks the owner.

## R22 - The solid cache

`SCREW_SOLID_CACHE` stays 4 if `mem_limit` computed with `W(4)` at the picked N still qualifies
(R16), else it is the largest K in {3, 2, 1} that does. `W(K)` is the peak with K solids cached per
worker. `W(K)` for every K from 1 to 4 is measured after R16's pick, by running the load mix of R15 at
N = 1 with `SCREW_SOLID_CACHE` = K, 5 repetitions for each K measured, so that every `W(K)` this rule
compares comes from the same instrument; `W(4)` is not taken from R16's W. K = 4 is measured first,
then 3, 2 and 1, each only if the K above it did not qualify. `W(K)` is the max over the repetitions of
the container's peak. With one worker, the container peak is that worker's peak. The `mem_limit` that
ships is the larger of the one built from R16's W and the one built from `W(K)` at the K this rule
keeps, both computed as R16 computes `mem_limit(N)` at the picked N.

## R23 - Tessellation, arenas and recycling

The tessellation presets are kept. `_release_arenas` (the trim) is kept only if the retained memory
after an export is lower with it than without, at every artifact. For each artifact A the *arena
readings* are readings (R2) of Z(A), the drift run's part (below), at A: 5 repetitions (R3) with the
trim on and 5 with it off. The measure is the cgroup's `memory.current`, read after the export. The
maxima over the 5 repetitions are compared, and the trim is kept only if the max with the trim on is
lower than the max with it off at every artifact. If a max the arena comparison needs is missing (R3:
a point with any repetition that is not `ok` has no max), the phase stops and asks the owner.
`max_tasks_per_child` stays unset unless the drift run shows growth above its allowance for any
artifact; if it does, the phase stops and asks the owner, because no rule here sets a recycling value.

*The drift run.* It is separate from the load run, because a load run builds different parts and a
larger transient build later in it would read as growth. For each artifact it builds one fixed part
K = 20 times in a row, and compares the cgroup peak after build 1 with the peak after build K.

- *The part.* Z(A) is the point of A's bound set (R14) with the largest `memory_peak_bytes` in its
  `explore` reading, among those whose reading is `ok`, a tie going to the label that sorts first:
  R14's measured memory extremum.
- *K.* 20, the number of parts a load run takes for each artifact (R15).
- *The reading.* One fresh container of the image under the R2 cap, one per artifact and repetition,
  5 repetitions (R3). One process does what a pool worker does and nothing else: it builds and exports
  Z(A) at A, K times, one after another. Before each build it empties the solid cache
  (`screw.solid.clear_cache`), so every build is cold: the cache keeps at least one solid
  (`int_env` floors `SCREW_SOLID_CACHE` at 1), so a repeat of one part would otherwise be a hit and
  not a build. It runs below the HTTP layer, so the export cache and the response encoding play no part.
  The peak is read as R2 says, after the build, its export and a level-1 gzip of the output, after every
  build; the rule reads builds 1 and K. The deadline is K x the artifact's timeout (R14).
- *The drift.* The drift of a repetition is the peak after build K minus the peak after build 1; the
  drift of the artifact is the max over its 5 repetitions. Any repetition that is not `ok`, or whose
  readings after build 1 or build K are missing, leaves the artifact with no drift and the phase stops
  and asks the owner.
- *The allowance.* The drift of an artifact is above its allowance when it exceeds 0.10 x the
  smallest peak after build 1 among its 5 repetitions. The owner fixed the fraction before any
  reading: it scales with the part, and 10 % sits above the run-to-run spread expected between cold
  builds of one part. It is a pre-registered allowance, not a measured figure.
- *Memory limit.* Drift adds nothing to R16's `mem_limit(N)`: drift above the allowance stops the
  phase, so a drift term in the limit would count the same growth twice.

## R24 - SCREW_WORKERS

`SCREW_WORKERS` stays 1 if the `/api/health` p95 under load at the picked N is at most the probe's
1 s inner timeout (the `urlopen(..., timeout=1)` of the `HEALTHCHECK`); otherwise the phase stops and
asks the owner.

## R25 - The HEALTHCHECK

`--timeout` is `ceil(2 x` the max health wall under load `)` seconds. The health wall is the wall of
the `HEALTHCHECK` command, and the max is taken over the 5 load readings of the picked N (R16), the 5
repetitions of its load run (R15). `--start-period` is 2 x the max
time to the first healthy response, rounded up to 10 s. `--interval` 30 s and `--retries` 3 are
Docker's documented defaults and are cited as such.

## R26 - tmpfs

The `/tmp` tmpfs is at least the `stl-fine` byte budget x N or, where the budget (R13) leaves that
unbounded, the largest enveloped `stl-fine` bytes prediction over the admitted explore points x N,
rounded up to the 256 MiB step of R16 and inside `mem_limit`.

## R27 - The required tier (D-12)

Per artifact A, the tier is taken from an ordered list D(A) of admitted points, fixed by these steps so
that two implementations write the same list.

1. *Candidates.* The admitted `explore` points at A, in the order of the `explore` file, deduplicated by
   part: two points are one part when their kind and params are equal as JSON objects, and the first in
   file order is kept.
2. *The budget edge.* The edge ratio of a point is the largest, over the targets (bytes, seconds, peak)
   whose component of the chosen budget (R13) is finite for A, of its enveloped prediction (R12) divided
   by that component. C1 has a finite component for every target; C2 only for the peak (4 x 10^9 bytes,
   every artifact); C3 only for the raw bytes of `stl-fine` (Q). Where no component is finite for A,
   which under C3 is `stl-preview` and `step` (bounded only by the walls, R7 to R10, which a prediction
   is not divided by), the edge ratio is the point's enveloped build-seconds prediction, by this rule
   and not as a stand-in for an infinite component: the edge of an artifact the budget leaves
   unbounded is the slowest part the model admits, ranked by seconds and not by bytes.
3. *The edge points.* The *edge ranking* is every candidate ordered by edge ratio, largest first, a tie
   going to the label that sorts first (plain string comparison). The edge points are its first 3.
   The load run (R15) walks the same ranking further when another artifact has taken an edge point.
4. *The draw.* The other candidates, in file order, shuffled by `random.Random(20261026).shuffle`
   (CPython 3.12, a new generator for each artifact). The seed is the date of the owner's rulings,
   2026-10-26, written as an integer; any fixed integer would do, and this one is fixed here.
5. *The tier.* D(A) is the 3 edge points and then the draw. The tier takes the 3 edge points always,
   then draw points in order, each only if the summed charges of the points taken, itself included,
   stay under 10 minutes (600 s, D-12's target); it stops at the first draw point that does not fit
   and skips none. The charge of a point is the cold wall (`build_s + export_s`) of its `explore`
   reading when that reading is `ok`, and otherwise the artifact's full timeout (R14): a point that
   was killed, capped, refused or crashed at `explore` has no wall, and may take its whole deadline
   again. It is in the tier all the same, and if it fails again it fails the tier (R29).

   Steps 1 to 4 need no timeout, so D(A) is fixed before the load run (R15), and it is not redrawn when
   `e` widens (R12). Step 5 needs the
   timeouts, which R14 fixes after R16 has picked N, so the tier is built only then and never before.
   A point's charge is its `explore` reading and the timeout, each fixed before the tier is built.

## R28 - The full tier (D-12)

Every catalogue row x 3 artifacts, the nut factorial, and the dense boundary. The dense boundary is
bolt only: per artifact, for each of the 15 L11 sizes and both hands, the bolt at the size's coarse
pitch P with `s = 1.6 d`, `k = 0.6 d` and `thread_length = length = n x P` (R4), where n is the
largest whole number of turns at which that bolt is admitted at that artifact. One pass; R5 re-runs
apply. A pair the cost model refuses is
still read in the full tier and must return its expected refusal (422 or info status); it is not
judged against the cost model.

## R29 - When a tier fails (D-07, D-12)

A tier fails on any non-`ok` reading of an admitted point, a cold wall above its artifact's timeout,
or `actual / predicted - 1` above its envelope for any target. A pair the cost model refuses (R28) fails
the tier only if it does not return its expected refusal; it has no cost to judge.

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
