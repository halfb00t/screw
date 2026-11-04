# Phase 8 Sweep Protocol (pre-registered)

Written before any Phase 8 runner reading exists. Every selection rule, threshold, grid, ceiling and
rounding that Phase 8 applies to a measurement is fixed here, so a bound is credible because its rule
was fixed before its data (the L11 method; 07-SWEEP-PROTOCOL.md R30 is the precedent). Plans 08-02 to
08-13 apply these rules; none of them may change one (F14).

- **Branch:** `gsd/phase-08-pre-release-gap-closure`.
- **Point file:** written by `bench/oper_sets.py`; `python -m bench.oper_sets --check` and
  `tests/test_oper_fine.py` fail when a committed file is not what it writes. Git blob sha of the band
  walk `bench/points/fine-bands.json`: `7602c6998298796f331a4af8d1da42aa21a6d869`.
- **Decisions applied:** `08-CONTEXT.md` D-01 to D-20 and D-22, and the standing rules L02 (a number the
  tool prints is a number someone will cut metal to), L25 (the d / pitch walls) and L33 (CI measures
  nothing; sweeps are dispatched by hand).
- **Terms.** A *reading*, a *point*, a *wall* and *admitted* are as in 07-SWEEP-PROTOCOL.md (R2, R12).
  The *shipped sweep* is `helical.thread` as `origin/main` holds it. The *fine sweep* is F2. A
  *band* is a range of d that F5 reads from the band walk. The mm values that research and the debug
  session quote from macOS arm64 runs are context and appear in no rule as a value.

## F1 - Evidence (D-04, L33)

Only readings taken on a GitHub-hosted `ubuntu-latest` runner (linux/amd64) through
`operability.yml`'s `workflow_dispatch`, started by hand, bound anything. A local run, a macOS figure
or a run started by anything but the owner is context. A reading is 07 R2's: one cold build and one
export of one artifact of one part in one fresh container of the image built from the dispatched
commit. Shards are cut by 07 R6 from the charges of explore run 40646117094. Records are committed as
downloaded (`gh run download <id> -p 'oper-*' -D bench/results/phase-08/<set>-<id>`) and each run gets
`### <set>, run <id>` under `## Phase 8` in `bench/RESULTS.md` with the dispatched sha, CPU models,
status counts and the `summarize --markdown` output.

## F2 - The fine sweep (D-01, D-22)

`helical.thread(..., fine=True)` samples each flank spline at 56 points and calls
`BRepOffsetAPI_MakePipeShell.SetTolerance(1e-6, 1e-6, 1e-4)` after `SetMode` and before `Add` (the
debug session's E12/E14 variant). `fine=False` is the shipped sweep unchanged. The bench tools'
direct `helical.thread` calls keep the shipped sweep.

`solid/pair.py` is unchanged (D-22, amending D-17). Its verdict rods and blanks call
`helical.thread` directly (`pair.py:68`, `:78`) and keep the shipped sweep, while its shipped
evidence row (`_shipped`, `pair.py:269`) builds the served nut through `build(p)`, which F3 puts on
the fine sweep for M5 to M20, so that row reads the part users download.
`tests/data/pair_expected.tsv` holds verdicts judged on the shipped-sweep rods and is not
re-measured.

## F3 - Who gets it (D-02, D-03, D-15, D-16, D-19)

Exact d / pitch = `Fraction(repr(d)) / Fraction(repr(pitch))`, compared strictly.

- **A nut is fine above 6** (ruled, D-16: the island's exact ratio is 1100000/157143 =
  6.999993636369421, so 7 would miss it). This moves the nut catalogue rows M5, M8, M10, M12, M14,
  M16, M18 and M20 and keeps M2, M2.5, M3, M3.5, M4, M6 and the default nut on the shipped sweep.
- **A bolt is fine only when its exact d lies strictly inside a band F5 reads and its exact d / pitch
  is above 6** (D-15). There is no d / pitch-only bolt clause (D-19): D-03 reads the bolt threshold
  from the refusals, and the committed Phase 6 and 7 runner records hold 973 `ok` bolt readings and
  no refusal outside the bands at 8 < d / pitch <= 20 (the 6 refusals there are inside them: d 3,
  d / pitch 8.57, 84 mm of thread, explore run 40646117094). So a bolt outside every band keeps the
  shipped sweep up to the wall of 20.
- **What that rests on.** That the shipped sweep builds such a bolt is read at sampled ratios only:
  those 973 readings at their own ratios, and F4's check cells at q 9, 12.5, 16 and 20 on this
  phase's runner. A bolt outside the bands at a ratio between the samples ((8, 9), (9, 12.5),
  (12.5, 16) or (16, 20)), or at a d or thread no sample holds, carries no reading and is F13's
  residual. No rule claims a reading the walk does not take.
- No bolt catalogue row moves (F5 stops if one would).

Every part F3 does not put on the fine sweep keeps the shipped sweep and its timeouts, budgets,
envelope and records (D-02).

## F4 - The band walk `fine-bands` (D-15, D-19)

The set `bench/points/fine-bands.json`, written by `python -m bench.oper_sets band-walk --explore
bench/results/phase-07/explore-40646117094 --out bench/points/fine-bands.json`. Bolts only, 1
repetition per cell, 4956 cells in two groups. A cell is `kind bolt`, with pitch = d / q rounded up
to 6 significant figures (so the exact d / pitch is at most q), s = 1.6 d at most 1000 mm, k = 0.6 d,
both hands, right before left.

- **Edge group** (2844 cells, labels `band-d{d}-q{q}-n{n}-{right|left}`): full thread, thread_length =
  length = n x pitch as an exact decimal, at n 50, 70 and 90; q in {5, 6, 6.5, 7, 7.5, 8}; d from
  0.3 to 1.2 and from 1.3 to 3.8 mm in 0.05 mm steps plus 4, 4.5, 5, 6, 8, 10, 12, 16 and 20 mm
  (79 sizes).
- **Check group** (D-19; 2112 cells, labels `check-d{d}-q{q}-n{n}-{hand}` and
  `check-{form}-d{d}-q{q}-{hand}`): the same 79 sizes plus 24, 30, 42, 60 and 100 mm (84 sizes), full
  thread at n 3, 30 and 90 (2016 cells), and d 150, 200, 300, 450, 600 and 999.999 mm in 07 R31's
  `n3` and `n3s` bolt forms (96 cells), all at q in {9, 12.5, 16, 20}. Every check cell's exact
  d / pitch lies in (8, 20].
- **Artifact.** Each cell is read at `step` when the shipped model admits it there, else at the first
  of `stl-preview` and `stl-fine` it admits (a build is the same at every artifact, so a cell served
  only as an STL is still read). A cell the parameter model refuses (pitch walls lifted, as R31's
  walk) is in `dropped` with its type, and a cell admitted at no artifact under the shipped envelope
  is in `dropped` as `over_budget`.
- **Provenance.** The walk is read from a commit whose `src/screw/solid/` equals origin/main's, so
  every reading is the shipped sweep's (D-02). The file holds 4803 points in 151 shards and 153
  dropped cells (all `over_budget`, at d 8 mm and above).

## F5 - Band edges and the check cells (D-15, D-19)

Every point of the walk has exactly one reading, `ok`, `refused` or `crashed`; any other status or a
missing reading is a stop (S1).

- **Edges come from the edge group only** (q at most 8).
- An edge-group refused or crashed reading at d / pitch at most 6 is a stop (S2): it would stay on
  the shipped sweep (D-15, D-16).
- Of the edge-group refusals above 6 (all are at most 8 by construction), one at d 4 mm or more is a
  stop (S3): it lies outside both D-15 bands.
- In each walked range, 0.3 to 1.2 mm and 1.3 to 3.8 mm: no refusal gives no band; otherwise the
  band's edges are the largest walked d of the range below its smallest refused d and the smallest
  walked d above its largest refused d, both excluded (the "out" values, as E30 named them). A
  refused d at a range's end is a stop (S3): there is no out value.
- A band edge that puts any bolt catalogue row with d / pitch above 6 strictly inside a band is a
  stop (S4): D-15, no catalogue bolt moves.
- **Then the check group (D-19).** A refused or crashed check cell whose d lies strictly inside a
  band is listed and is not a stop (F3 puts it on the fine sweep, and F6 reads it there). A refused
  or crashed check cell whose d lies outside every band is a stop (S5).
- The judge prints the bands, the in-band check refusals and the count of out-of-band check readings
  that are `ok`. `python -m bench.oper_sets fine-bands --from DIR` prints the block that 08-12 pastes
  into `calc/thread.py`; it is never typed.

## F6 - The proof walk `fine-proof` (D-07)

Read once, by F4's artifact rule, from the commit that adds the fine sweep and the F5 bands and has
no turns guard. Grids:

- **(a) In-band bolts.** For each F5 band, every d of the 0.05 mm grid strictly between its excluded
  edges (low < d < high; F5's edges are walked d outside the band, so no edge is drawn and F3 puts
  every grid (a) cell on the fine sweep), D-07's named 0.5 to 0.85 and 1.6 to 3.3 mm at 0.05 among
  them wherever they lie inside a band, q {6.5, 7, 8, 10, 14, 20}, n {3, 30, 60, 90}, full thread,
  s 1.6 d, k 0.6 d, both hands. A D-07-named d outside every band keeps the shipped sweep (F3) and is
  not drawn here: its proof is the band walk's own cells at that d, every one read `ok`, because F5
  puts every refused or crashed edge-group d inside a band or stops (S2, S3) and stops on an
  out-of-band check refusal (S5). The grid (a) q and n the band walk does not hold at that d are
  F13's residual.
- **(b) The examples and the refusals.** The debt's examples d 3, pitch 0.35, length = thread_length
  = 25, s 4.8, k 1.8 and d 2.5, pitch 0.35, length = thread_length = 30, s 4, k 1.5, both hands; and
  every explore.json bolt that F3 puts on the fine sweep and whose reading in explore run
  40646117094 is `refused` or `crashed`, as drawn (the 6 at d 3, d / pitch 8.57, 84 mm of thread);
  and every band-walk cell, edge or check group, that F3 puts on the fine sweep and whose
  `fine-bands` reading is `refused` or `crashed`, as drawn (so every in-band refusal F5 lists is read
  again on the fine sweep).
- **(c) The denser nut grid.** R31's four nut forms (base, s4, c0, m1), d = R31's 44 nut sizes plus
  2.1 and 2.3, q {5.5, 6, 6.25, 6.5, 6.75, 7, 7.25, 7.5, 7.75, 8}, both hands (the island is base,
  s4 and m1 at d 2.2, q 7).
- **(d) The moved catalogue rows.** The nut catalogue rows F3 moves, both hands.

Pitch = d / q rounded up to 6 figures; drop rules as F4. Bolts outside the bands are not in the
proof walk: they keep the shipped sweep (D-19), and F4's check group reads them at its sampled ratios
only (F3, F13).

## F7 - Proof-walk judgement (D-06, D-18)

Every point exactly one reading, `ok`, `refused` or `crashed`, else stop (S1).

- A refused or crashed part F3 keeps on the shipped sweep is a stop (S6): the nut grid's q 5.5 and 6
  cells.
- A refused or crashed nut on the fine sweep is a stop (S7): the guard of D-06 and D-18 is a bolt
  rule.
- Refused or crashed fine-sweep bolts feed F8.

## F8 - Turn ceilings (D-06, D-18)

Regions are the F5 bands in ascending d, named `band-1` and `band-2` in that order; there is no
region outside the bands, because every fine-sweep bolt lies inside one (F3, D-19).

- Per region F is the smallest exact built turns (`built_thread_length(thread_length, length) /
  pitch`) of a refused or crashed fine-sweep bolt, and its ceiling N the largest whole number at or
  below F / 1.25 (R31's margin). A region with no such reading has no ceiling. N below 3 is a stop
  (S8): it would refuse every fine bolt there; B-03's fitted minimum is 3 turns.
- **The guard.** A bolt F3 puts on the fine sweep, in a band with a ceiling, whose exact built turns
  exceed N, is a 422 `turn_guard` with `ctx.fields` d, pitch, thread_length and length, checked after
  `pitch_too_fine`.
- `python -m bench.oper_sets fine-ceilings --from DIR` prints the block that 08-09 pastes into
  `calc/thread.py`; it is never typed.

## F9 - The cost re-sweep (D-05)

- **`fine-cost`, reps 1:** every explore.json part and every nut catalogue row F3 puts on the fine
  sweep; in-band bolts d {0.5, 0.8, 1.6, 2.5, 3, 3.3} (each kept only if strictly inside an F5 band)
  at q {7, 8, 12.5, 20} and n {3, 30, 90}, full thread, s 1.6 d, k 0.6 d, right hand; and nuts
  d {0.8, 2.2, 5, 10, 20} at q {6.25, 7, 8} in forms base and s4, right hand. Each part at every
  artifact the shipped model admits under the shipped envelope and B-01, the others in `dropped` as
  `over_budget`.
- **`fine-spread`, reps 5:** the nut catalogue rows F3 moves, at every artifact.
- No bolt outside the bands is in either set (D-05, D-19): they keep the shipped sweep and its fit.
- Both are read from the fine-proof commit.

## F10 - The fine envelope (D-05)

For each (kind, artifact, target), `FINE_ENVELOPE` is the smallest e at or above the shipped
`ENVELOPE` value such that `cost.predict` x (1 + e) is at least the actual of every cold isolated
`ok` reading of a fine-sweep part the F8 guard admits, in fine-proof, fine-cost and fine-spread (the
factor raised by single ulps, `bench.oper_fit.envelope`'s method; a part the F8 guard refuses is
never served, so its readings are listed and fit nothing). `cost.fits` judges a part F3 puts on the
fine sweep under `FINE_ENVELOPE` and every other part under `ENVELOPE`.

Stops (S9): a fine-cost or fine-spread point of a part the F8 guard admits with any non-`ok` reading,
or with a missing repetition; an `ok` reading of a part `FINE_ENVELOPE` admits at that artifact whose
cold wall exceeds `BUILD_TIMEOUT_S` (L24, frozen by L33); a catalogue row or default part refused at
any artifact under `FINE_ENVELOPE` (B-01); a fine-spread catalogue reading above its B-01 component;
any Phase 8 reading of a shipped-sweep part above its shipped enveloped prediction (D-05 forbids
widening `ENVELOPE`).

## F11 - Freeze (research Pitfall 10)

From the fine-proof dispatch commit on, `src/screw/solid/helical.py`, `bolt.py`, `nut.py` and the F3
and F5 constants do not change in this phase. A change voids F7 to F10 and stops the phase (S10).

## F12 - Sets drawn before Phase 8 (G6, G36)

They are checked under the model they were drawn under and never drawn again. `oper_lift.drawn` and
`registered` lift the turns guard as they lift the pitch walls. A pre-Phase-8 point file whose
regeneration `FINE_ENVELOPE` moves is regenerated under `ENVELOPE` alone. `runtime.json` is
re-derived, and a move of any value other than R21's export-cache candidate count is a stop (S11;
L32's precedent).

## F13 - What stays unproven (D-07, D-20, E32)

A cell off the F4 and F6 grids is not proven. Among them:

- every bolt outside the bands at a d / pitch between the check group's samples (F3);
- a D-07-named d outside every band at a grid (a) q or n the band walk does not hold (F6);
- an F4 cell that F3 moves to the fine sweep and F6 does not read (its shipped-sweep reading says
  nothing of the fine sweep).

Isolated failures at a seam cannot be bounded by a grid. No rule turns a post-build `BuildError`
into a field 422. OPER-03's and ROADMAP SC1's amended text names this residual (D-20, 08-10), and
08-09 files it as debt.

## F14 - Immutability

As 07 R30, for F1 to F13 and the stops section, from the first Phase 8 runner reading on. A harness
fix that changes no rule is listed under "Harness fixes" with its sha and nothing else in this file
is edited; a rule change stops the phase for the owner's ruling.

A set drawn before the turns guard (`fine-bands`, `fine-proof`, `fine-cost`, `fine-spread`) is read
only from a commit without the guard: from the guard's commit on, `bench/oper_child.py` validates
each point through `oper_lift.validate`, which lifts only the point's own named `lift` and never the
walls or the guard, so a point the guard refuses reads `bad point` (exit 2). Such a re-dispatch is
not a Phase 8 reading.

## F15 - The small-d bolt wall (owner ruling at S5, 2026-11-03; amends F3, F5 and F6)

Added after the first Phase 8 runner reading, by the owner's ruling that F14 asks for. F1 to F14 and
the stops stand as written; this section only adds to them, and the data it cites exists: the band
walk, run 41635270998 (`bench/results/phase-08/fine-bands-41635270998`, sha b69aae5, 152 of 152 jobs,
4803 points, 4273 `ok`, 530 refused). Phase 7's R30 did the same for its R31.

**The stop.** `oper_sets: stop (F5): S5: check-d0.5-q12.5-n90-right was refused at d 1/2, outside
every band, and no bolt outside the bands goes on the fine sweep (D-19)`. The edge group gave one
band, d 1.55 to 3.35 mm, and nothing at d 0.5 to 0.85. The check group had 355 refusals: 315 inside
that band and 40 outside every band, all at d 0.5 to 0.85 in 0.05 steps, all with 90 turns: q 12.5
right hand only (8), q 16 both hands (16), q 20 both hands (16). The smallest refused exact d / pitch
is 12.5; every q 9 cell in that range and every cell with 0.45 < d < 0.9 at 3 and 30 turns read `ok`.

**The ruling.** Owner's reply, verbatim: `c`. That is S5's option (c) (lower the bolt wall below the
refused ratio for that d range, superseding L25 there), put to them as: a bolt with exact d strictly
between 0.45 and 0.9 mm has a d / pitch wall of 9 and no other d changes. The protocol's own rule
recommended (b); the owner chose (c). It is logged as L37 (`docs/architecture/decision_log.md`), not
L36, which plan 08-10 writes.

**The amendment.**

- **F5, the check group.** A refused or crashed check cell outside every band is *walled*, and is not
  a stop, exactly when its exact d lies strictly between 0.45 and 0.9 and its exact d / pitch is above
  9: the parameter model refuses such a bolt before the kernel (L37), so the cell is not a bolt the
  shipped sweep is asked to build. The judge lists the walled cells and prints their count. Every other
  refused or crashed check cell outside every band stays S5: one at d 0.45 or 0.9, one at d / pitch of
  9 or less, one at any other d. The rule hides no other refusal, and it is not read from the data: the
  two edges and the 9 are the ruling's.
- **F3.** A bolt in that interval at d / pitch above 9 is refused by the wall and never reaches a
  sweep. At 9 or less it is outside every band and keeps the shipped sweep, as F3 says.
- **F6.** A D-07-named d (0.5 to 0.85 mm) outside every band is proven by the band walk's own cells at
  that d: each read `ok` or is above the wall of 9, where the model refuses it before the kernel.
  That is the grid bar's "refused before the kernel with a 422 naming its fields". The grid (a) q and
  n the band walk does not hold at that d stay F13's residual.
- **Where the wall's code lands.** Plan 08-12, in `calc/thread.py` beside `MAX_BOLT_D_PER_PITCH`
  (`pitch_too_fine_refusal` is the only function that reads the walls and `params.py` calls it), with
  `bench/oper_lift.py` lifting the new constant as it lifts the two walls, and the API and CLI 422 tests
  in `tests/test_fine_pitch.py`. Plan 08-03 changes no file under `src/`.

## F16 - The F10 stops (owner ruling at S9, 2026-11-04; amends F10 and S9's use)

Added after the first fine-envelope fit, by the owner's ruling that F14 asks for. F1 to F15 and the
stops stand as written; this section only adds to them, and the data it cites exists: fine-proof
(run 41684315321, 5790 readings), fine-cost (41684331518, 278) and fine-spread (41684347573, 120),
under `bench/results/phase-08/`, all `ok`, `FINE_TURN_CEILINGS` empty. 07 R30 and F15 did the same.

**The stops.** S9 fired three times, on one candidate fine envelope (F10 as written):

1. 37 `ok` cold isolated readings of shipped-sweep parts (nuts at `step` in grid (c), q 5.5 and 6)
   were above their enveloped prediction: 41 model-readings, 37 on seconds (worst
   `proof-nut-base-d300-q5.5-left`, 1.552) and 4 on bytes (worst 1.0184).
2. Judging every catalogue row and default part under that one candidate refused 84.
3. `proof-walk-check-d1.65-q20-n90-left` and `-right` (`stl-preview`, 26.971 s and 26.816 s) are over
   `BUILD_TIMEOUT_S` and the candidate admits them.

**The ruling.** Owner's reply, verbatim: `recommended`. It is S9 (c) for stop 1, an amendment of F10
for stop 2, and S9 (b) for stop 3 and what stop 2 leaves. Logged as L38.

**The amendment.**

- **(i) Stop 1, the host check of 07 R2.** Run as R2 writes it (a reading is `ok`, not `capped`, with a
  readable cgroup peak, `oom_kills` 0 and inside the deadline) it passes on 37 of 37 readings: the host
  is not degraded and the stop is not S1. R2 sets no threshold on the recorded load or CPU model, and
  none is added. Consequence: `ENVELOPE` is widened for the nut `step` seconds and nut `step` bytes
  models by the Phase 7 method (07 R12 and `bench.oper_sets.envelope_check`, whole ulps of the factor),
  over every cold isolated `ok` reading of a shipped-sweep part in the three directories, superseding
  D-05 and L33 there; no other shipped-sweep model widens. F10's "shipped `ENVELOPE` value" and the
  last stop of F10 (a shipped-sweep reading above its enveloped prediction) then read the widened
  value, and the stop stands for any other reading. The widened `ENVELOPE` alone must refuse no
  catalogue row and no default part at any artifact (the 07 R12 check, `oper_sets._admits_all`).
- **(ii) Stop 2, F10's B-01 stop.** "A catalogue row or default part refused at any artifact under
  `FINE_ENVELOPE`" is judged for each part under the envelope that applies to it, as `cost.fits` will
  judge it: `FINE_ENVELOPE` when F3 puts the part on the fine sweep, the (widened) `ENVELOPE` for every
  other part. The reading of the stop as one envelope over all parts is withdrawn. `FINE_ENVELOPE` is
  still floored at `ENVELOPE` and fitted only on guard-admitted fine-sweep readings.
- **(iii) Stop 3 and what (ii) leaves, S9 (b).** A fine-sweep feature in `calc/cost.py`'s prediction,
  fitted on the same readings (the three directories; no new run), so that the cost gate predicts
  fine-swept parts honestly. F10's rule is otherwise unchanged, with `cost.predict` meaning the
  prediction including the feature for a fine-swept part, and `FINE_ENVELOPE` is then the smallest
  e at or above `ENVELOPE` over the feature's own residuals. The feature's form is not fixed here; the
  revised 08-08 and 08-13 choose it within D-05. It may not move a shipped-sweep prediction, `BUDGET`,
  `BUILD_TIMEOUT_S` or `COEFFICIENTS`. F10's stops stand and are judged after the feature: if a
  catalogue row or default part is refused (ii), a guard-admitted `ok` reading over `BUILD_TIMEOUT_S`
  is admitted, or a fine-spread reading is above its B-01 component, S9 fires again; the two
  `check-d1.65-q20-n90` bolts must be refused by the cost gate, not admitted.

**The residue the feature must clear** (a scratch recompute of (ii) at the ruling, to be recomputed by
the committed judge): nut `step` seconds refuses the 8 fine-swept nut rows iso4032 M5, M8, M10, M12,
M14, M16, M18 and M20 at `step` (enveloped 29.6 to 37.1 s against 15.0 s; their fine-spread actuals are
3.90 to 4.92 s); bolt `stl-preview` seconds admits the 2 over-deadline bolts. Every bolt row, every
shipped-sweep nut row and both default parts are admitted, and there is no fine-spread B-01 overrun.

## Stops and owner paths

A stop means the executor commits nothing more for that run, reports the stop line, the readings it
names and this bullet to the owner, and waits (CLAUDE.md: stop and ask).

- **S1 (F5, F7, F10: a missing, doubled or foreign reading, a status other than `ok`, `refused` or
  `crashed`, a run whose conclusion is not `success`, or a head sha other than the dispatched
  one).** Options: (a) a harness defect: fix it in its own commit, list it under Harness fixes, and
  dispatch the same set again in full (a new run id; the faulty run's records are committed as
  downloaded and marked void in RESULTS); (b) a runner fault (a cancelled or lost job): dispatch the
  same set again unchanged, records as in (a). Recommendation: (a) for a harness defect, (b) for a
  runner fault.
- **S2 (F5: an edge-group refusal at d / pitch at most 6).** Options: (a) lower that band's
  d / pitch floor below the refused cell's ratio (an F3 amendment), if no bolt catalogue row then
  lies inside the band above the new floor, so F6 reads the cell on the fine sweep; (b) keep the
  floor and give that band's shipped-sweep bolts a turns ceiling by F8's rule read from the band
  walk (a D-06 amendment). Recommendation: (a) when no catalogue row moves, else (b).
- **S3 (F5: an edge-group refusal at d 4 mm or more, or a refused d at a walked range's end).**
  Options: (a) extend the walk past that end in a new pre-registered set (an F4 amendment) and read
  the band again; (b) close the band at the walk's end and give the cells past it a turns ceiling by
  F8's rule read from the band walk. Recommendation: (a).
- **S4 (F5: a bolt catalogue row with d / pitch above 6 strictly inside a band).** Options: (a) raise
  that band's floor above the row's d / pitch, if every edge-group refusal of the band stays above
  it; (b) accept that row on the fine sweep (a D-03 and D-15 amendment: F9 then reads it at every
  artifact under B-01). Recommendation: (a) if it holds, else (b).
- **S5 (F5, D-19: a check cell outside every band refused or crashed, 8 < d / pitch <= 20).**
  Options: (a) widen the nearest band, or add one, to hold that d (an F3 and F5 amendment), so F6
  reads it on the fine sweep; (b) a d / pitch-only bolt clause at the refused cell's ratio (D-03's
  first form), if no bolt catalogue row moves; (c) lower the bolt wall below the refused ratio for
  that d range (supersede L25 there). Recommendation: (a) when the refused d is next to a band, else
  (b).
- **S6 (F7: a refused or crashed proof-walk part that F3 keeps on the shipped sweep).** Options:
  (a) lower that kind's fine threshold below the refused ratio (a D-15 or D-16 amendment) and read
  the moved cells on the fine sweep in a new proof set, if no further catalogue row moves; (b) give
  the part's region a turns ceiling by F8's rule (a D-06 amendment). Recommendation: (a) when no
  catalogue row or default part moves, else (b).
- **S7 (F7: a refused or crashed nut on the fine sweep).** Options: (a) a nut turns guard in the
  bolt guard's form, its ceilings read by F8's rule over the nut refusals and its `ctx.fields` d,
  pitch and m (a D-06 and D-18 amendment), if no catalogue nut row and not the default nut is
  refused by it; (b) lower the nut wall below the refused ratio for the refused d range (supersede
  L25 there), if no catalogue row is refused; (c) a finer nut sweep (voids F11; a new proof walk).
  Recommendation: (a).
- **S8 (F8: a ceiling N below 3).** Options: (a) refuse every fine bolt of that band by a band wall
  at d / pitch 6 there (supersede L25 there; F5 has already shown no catalogue row is inside the
  band above 6); (b) a finer sweep for that band (voids F11; a new proof walk). Recommendation: (a).
- **S9 (F10: a guard-admitted fine-cost or fine-spread part read `refused` or `crashed`; an `ok`
  reading over `BUILD_TIMEOUT_S`; a catalogue row or default part refused under `FINE_ENVELOPE`; a
  fine-spread reading above its B-01 component; a shipped-sweep reading above its shipped enveloped
  prediction).** Options: (a) for a refused or crashed part, re-judge F8 with that reading included
  (an F8 amendment) so the guard refuses it; (b) for a timeout, a refused row or a B-01 overrun, a
  fine-sweep feature in the cost model, fitted on the same readings (D-05 "or add a feature");
  (c) for a shipped-sweep reading, check it against 07 R2's host checks and treat a degraded host as
  S1, else widen `ENVELOPE` for that model by the Phase 7 method (supersede D-05 and L33 there).
  Recommendation: (a) for a refusal, (b) for a cost miss, (c)'s host check first for a shipped-sweep
  reading.
- **S10 (F11: a frozen file changed after the fine-proof dispatch commit).** Options: (a) restore the
  frozen text in a new commit; (b) keep the change and dispatch fine-proof, fine-cost and fine-spread
  again from the new commit (F7 to F10 re-read). Recommendation: (a), unless the change fixes a
  defect the readings expose, then (b).
- **S11 (F12: `runtime.json` moves in any value other than R21's export-cache candidate count).**
  Options: (a) the owner rules the moved value and the new L-entry records it (L32's precedent);
  (b) narrow `FINE_ENVELOPE` admission so the value does not move. Recommendation: (a).

## Harness fixes

None yet. Append `<date> <sha> <one line>` below.
