# Phase 7 — owner rulings on protocol gaps G1–G14

Date: 2026-10-27. Source: `07-PLAN-PROTOCOL-AUDIT.md` (commit eac98ab), "Protocol gaps the plans
expose". No runner reading of phase 7 exists yet, so R30's freeze ("after the first runner reading")
has not started. These rulings amend `07-SWEEP-PROTOCOL.md` through PR A2, which lands before plan
07-05 takes the first reading.

| Gap | Rule(s) | Owner ruling |
|---|---|---|
| G1 | R3, R9, R10 | When R9 or R10 decides "above 0", the confirm set is the smallest walked value (tail 1e-9 mm, root 1e-6 mm) for every cell at 5 repetitions. Any reading there that is not `ok` awards no floor and stops the phase for the owner, as R7 does. |
| G2 | R3, R7 | The R7 walk-down reads every step for every cell at 1 repetition in one dispatch, in steps of 10 turns from 240 down to 10. A cell's readings below its first `ok` step are recorded and used for nothing. The 5-repetition confirm at T decides. A cell with no `ok` step stops the phase for the owner. |
| G3 | R5 | If any spread point has no median (a repetition not `ok`, or incomplete), m has no number and the phase stops for the owner. |
| G4 | R6 | Hybrid. Sets of explore-like parts (walls, confirm, walk-down) charge each point the max explore `wall_s` of its (kind, artifact) group, and a shard is the longest prefix in file order that fits under half the job timeout. Contention, load and drift charge each reading the deadline its own rule sets (600 s where R2 applies, 20 x the artifact timeout for a drift reading); a reading whose deadline is not under half the job's `timeout-minutes` stops the phase for the owner, because the job timeout also counts setup, the image build and the upload (owner ruling after the PR #23 round-2 review; the earlier one-job-per-repetition fallback is withdrawn). A walls, confirm or walk-down point whose (kind, artifact) group has no explore reading is charged its `deadline_s`. (Owner rulings after the PR #23 review, findings 1 and 3.) |
| G5 | R12 | Only cold isolated readings widen e: contention readings at N = 1 and drift build 1. Contended walls (N = 2, 3), load walls and drift builds 2..K do not widen e. |
| G6 | R12, R14, R15, R27 | D(A), the R14 bound set and the R15 load mix are each fixed once, from the prediction they were first computed from, and never redrawn after a widening. A widening changes admission and the final numbers only. |
| G7 | R15, R16 | An N qualifies only if all 5 of its load repetitions are `ok`. If no N qualifies, the phase stops for the owner. |
| G8 | R17 | R17 is checked on the existing load records after R14 derives the timeouts. No request's queue plus build wall may exceed its artifact's timeout under the queue-aware deadline (07-02). No extra runner time. |
| G9 | R22 | W(K) for K < 4 is measured after R16's pick, running the load mix at N = 1 with `SCREW_SOLID_CACHE` = K, 5 repetitions each. W(4) is also measured there, at N = 1, so every W(K) that R22 compares comes from the same instrument. With one worker, the container peak is that worker's peak. |
| G10 | R13 | B-01 is one of C1, C2, C3. `custom` is removed from 07-10. |
| G11 | R19 | R19 compares the max over 5 repetitions. |
| G12 | R28, R29 | Refused pairs are read in the full tier and must still return their expected refusal (422 or info status). They are not judged against the cost model. |
| G13 | header | Text fix: the header names plans 07-03 to 07-20. |
| G14 | R23 | Each drift build is built, exported and level-1 gzipped before its peak is read, as R2 says. |

## Gaps G15–G21 (plan revision, 2026-10-27)

Source: the planner's revision of plans 07-05 to 07-21 against the protocol as amended by PR A2
(squash 8aa143f). Those plans gate the dependent steps on these rulings. The rulings amend
`07-SWEEP-PROTOCOL.md` through PR A3. PR A3 has to land before plan 07-05 takes the first reading.
The owner took the recommended option for every gap.

| Gap | Rule(s) | Owner ruling |
|---|---|---|
| G15 | R19 | Every point of the STL bound set (10 to 16 points) must pass on its own. Level 9 is compared with the adopted level, not with level 6. |
| G16 | R21 | The candidates are the explore parts that are admitted and `ok` at all 3 artifacts. Their gzip level-1 bytes are the upper bound. If any R19 reading shows level k bigger than level 1, the phase stops for the owner. |
| G17 | R23 (arenas) | Z(A) per artifact, trim on and trim off, 5 repetitions each. The measure is cgroup `memory.current`, read after the export. The maxima are compared. The trim is kept only if it is lower at every artifact. |
| G18 | R25 | The health wall is the wall of the HEALTHCHECK command. It is taken over the 5 load readings of the picked N. |
| G19 | R28 | The dense boundary is bolt only, over the 15 sizes. Coarse pitch, s = 1.6d, k = 0.6d. t = L = n·P, where n is the largest admitted. |
| G20 | R16, R22 | The `mem_limit` that ships is the larger of the one built from R16's W and the one built from W(K). |
| G21 | R12 | The R19 gzip readings and the R23 arena readings are cold isolated part readings. They widen e. |

## Gaps G22–G23 (owner answers on the PR A3 plan, 2026-10-27)

Source: the owner's answers to the open questions of the PR A3 plan
(`.planning/quick/261027-va3-amend-07-sweep-protocol-md-with-g15-g21-/261027-va3-PLAN.md`). The
rulings amend `07-SWEEP-PROTOCOL.md` through PR A3, together with G15–G21. The owner also confirmed
the reading of G16: "level k bigger than level 1" compares bytes; the candidates are admitted and `ok`
at all 3 artifacts; a candidate's sum is the raw bytes plus the level-1 gzip bytes of its three
explore readings.

| Gap | Rule(s) | Owner ruling |
|---|---|---|
| G22 | R19, R23 (arenas) | When a max that R19 (G15) or R23's arena comparison (G17) compares is missing (R3: a point with any repetition that is not `ok` has no max), the phase stops for the owner. |
| G23 | header | Text fix: the header names plans 07-03 to 07-21. |

## Gap G24 (owner answer before plan 07-05, 2026-10-28)

Source: question Q5 of the PR A3 plan, left open there. R6 named no charge for the R19 gzip set or the
R23 arena set, and R30 freezes R6 at the first runner reading. The ruling amends `07-SWEEP-PROTOCOL.md`
through PR A4, which has to land before plan 07-05 takes the first reading. The owner took the
recommended option.

| Gap | Rule(s) | Owner ruling |
|---|---|---|
| G24 | R6 | Each reading of the R19 gzip set and the R23 arena set is charged its deadline (R2's 600 s), as contention and load readings are, not its explore group's largest `wall_s`. A reading whose deadline is not under half the job's `timeout-minutes` stops the phase for the owner, as G4 rules. |

Earlier rulings in the same review cycle (PR A, rounds 1–3) are recorded in `07-04-SUMMARY.md`.

## Gap G25 (owner ruling after the first runner reading, 2026-10-28)

Source: plan 07-05 halted at its R10 stop (`bench/RESULTS.md`, "D-08 stop at R10"). In walls run
40646134133, group (d), the rods are `ok` at 1e-2, 3e-3 and 1e-3 mm in all 30 cells, so the rods alone
give F = 3e-4 mm. The nut voids are `refused` (`StdFail_NotDone`) in all 270 readings, at every radius
from 1e-2 down to 1e-6 mm. The void construction is valid geometry: D-04, `void_root_radius_refusal`
accepts a root `d/2 - 5H/8 + c` above 0. So the refusals are a real void wall above 1e-2 mm. The
ruling comes after the first runner reading of the phase, so R30's freeze had started. It is a rule
change the owner ruled, as R30 requires ("A rule change stops the phase for the owner's ruling"). It
is not a harness fix, and it is not listed under the protocol's "Harness fixes". It amends
`07-SWEEP-PROTOCOL.md` R3, R4 (d), R6 and R10 on the phase branch `gsd/phase-07-operability-re-sweep`.

| Gap | Rule(s) | Owner ruling |
|---|---|---|
| G25 | R3, R4 (d), R6, R10 | Walk the nut voids upward. For each of the 15 sizes and both hands, take the group (d) nut (pitch solving `d/2 - thread_depth(pitch) + 0.15 = r`, 3 turns, `m` = 3 pitch) at `r` in {3e-2, 1e-1, 3e-1, 1} mm. That is 120 readings at 1 repetition, with R2's deadline and the R6 explore-like charge (the largest explore `wall_s` of the (nut, stl-preview) group, or `deadline_s` if none). Every pitch is positive; the smallest is M2 at `r` = 1 mm, 0.277 mm. R10 then decides on group (d) and this walk together: F is the largest failing `r` over rods and voids at all radii; V is the smallest power of ten at or above 10 F, and may be any power of ten the walks hold from 1 mm down to 1e-6 mm; every reading of rods and voids at `r` >= V must be `ok`, otherwise there is no number and the phase stops again. If the voids still fail at 1 mm, that is an R10 stop and the walk is not extended. The R3 confirm set for R10 follows the existing rule (V and the next smaller walked value), using the void walk's radii where V lies in it. |

## Gap G26 (owner ruling after the void walk, 2026-10-28)

Source: the R10 stop after the void walk (`bench/RESULTS.md`, "D-08 stop at R10 after the void walk").
Void walk run 40665307964 read the 120 nuts once: 20 `ok` and 100 `refused` (`StdFail_NotDone`). Over
the committed records, every `ok` reading has a void root ratio r/d of 0.1250 or more, and every
refused one 0.1200 or less. pitch/d does not separate them (`ok` max 0.7852, refused min 0.7667). So
the void wall scales with `d`, and no absolute floor in millimetres can hold it. The group (d) voids
(r <= 1e-2 mm) of walls run 40646134133 are all refused (270 of 270). That is one repetition in one
run: an observation, not a confirmed bound. The rods of group (d) give F = 3e-4 mm. As before G25, the
rods are walked from 1e-2 mm down, so V must be a radius that walk holds, and a rod failing above
1e-3 mm puts V above it and stops the phase. This is the second rule change after the first runner
reading, so R30's freeze had started. It is a rule change the owner ruled, as R30 requires. It is not
a harness fix, and it is not listed under the protocol's "Harness fixes". It supersedes the part of
G25 that has R10 decide on the voids; G25's void walk stands as recorded. It amends
`07-SWEEP-PROTOCOL.md` R3 and R10 on the phase branch `gsd/phase-07-operability-re-sweep`. R4 (d) and
R6 describe and charge the void walk, contradict nothing here, and stand.

| Gap | Rule(s) | Owner ruling |
|---|---|---|
| G26 | R3, R10 | R10 decides `MIN_ROOT_RADIUS_MM` from the rods of group (d) only: F is the largest failing rod `r` (3e-4 mm on the record); V is the smallest power of ten at or above 10 F (1e-2 mm); every rod reading at `r` >= V must be `ok`. The R3 confirm for R10 is rods only: V and the next smaller walked value, every size and hand, 5 repetitions. The nut readings of group (d) and the void walk are recorded, set no F and bear on no bound; `bench/RESULTS.md` states the r/d observation and takes no number from it. Debt (must): a nut whose void root ratio r/d is near or below about 0.12 is refused by the kernel (`StdFail_NotDone`), not by a guard; the trigger is a request for such a nut, or the point before a void guard is relied on. That debt is added to `docs/tech_debt/active/2026-10-21-nut-countersink-cutter-crosses-the-axis-at-a-coarse-pitch.md` instead of being filed twice: computed from the code over every void reading, that item's countersink inner radius is positive on each `ok` reading and negative on each refused one, and the cause is an assumption, not a reading. The root-radius-floor item takes the rod result, and plan 07-07 resolves it with the floor. |

## Gap G27 (owner ruling after the walls confirm, 2026-10-28)

Source: the walls confirm run 40678150220 (`bench/RESULTS.md`, "R3 outcome of the confirm run by
candidate wall"). `ceiling-nut-d-1000` read `ok` once in walls run 40646134133 (peak 12663300096 B,
92752773 B under the capped threshold of 12756052869 B) and `capped` in all 5 confirm repetitions;
`ceiling-nut-d-10000` is `refused` 5 of 5. Under R3 (a point decides on its 5 repetitions) and R8 (a
`capped` reading cannot raise a wall), nut `d` has no confirmed decade, which is R8's "no number" stop.
This is a ruled change after R30's freeze, not a harness fix. The owner took the recommended option.

| Gap | Rule(s) | Owner ruling |
|---|---|---|
| G27 | R8 | R8 writes no `MAX_NUT_D_MM`. The nut `d` limit is cost, not a wall: the cost model's admission (R12) and the timeouts bound a large nut. The nut `d` stays under the shared `MAX_FIELD_MM` (1000 on the candidate decision), which holds only while that value lies below the nut `d`'s first refused decade (1e4); otherwise the phase stops for the owner. Plan 07-07 writes no `MAX_NUT_D_MM`. |

## Gap G28 (owner ruling on the head ratios the cost model was not fitted on, 2026-10-29)

Source: `docs/tech_debt/active/2026-10-29-cost-model-admits-out-of-fit-head-heights.md`, filed by
plan 07-11, and the orchestrator's read-only check at commit d869b87 (figures from `cost.fits` and
`cost.predict`, on the models of fit.json, runs explore 40646117094 and spread 40646125666). R11
fits the log of each target on the log of each field, and the fitted points hold every head ratio
in a narrow band, so a coefficient can say a larger head is cheaper.

- Bolt `k`. At d 100, pitch 1, length 30, thread_length 30, s 200, k 60 is refused at all three
  artifacts; its fine STL is predicted at 82 s and 4.2e9 B peak before the envelope. k 1000, inside
  `MAX_BOLT_K_MM` (1e5), is admitted at all three; its fine STL is predicted at 0.0063 s and 8.9e3 B.
  `ln_k` is negative on 9 of 9 bolt models (stl-fine bytes -3.675).
- Bolt `s`. `ln_s` is positive: the fine STL's predicted seconds rise with s (82 s at s 200, 390 s at
  s 400, 3060 s at s 999). So moving a ratio only to its nearest band edge can under-predict.
- Nut `s`. At d 30, pitch 0.35, m 24, clearance 0.15: s 48 is refused at all three artifacts; at
  s 120 the preview is admitted; at s 300 the preview and the fine STL; at s 999 the preview and the
  STEP. `ln_s` is negative on 6 of 9 nut models (down to -0.241).
- The bands, over the fitted points (R11) with omitted fields at their defaults: bolt k/d 0.6 to 0.7
  (1247 points, 4 with no `k`, which take the default 4) and s/d 1.5 to 2.0; nut s/d 1.5 to 4.0 and
  m/d 0.8 to 3.0 (282 points). The bolt catalogue's k/d is 0.625 to 0.7; every catalogue row and both
  default parts lie inside every band.
- Under the first rule (each out-of-band ratio moved to its nearest edge) the executor found bolt
  k 1000 still admitted at STEP (the edge k 70 is predicted under the STEP budget, k 60 is not) and
  nut s 999 still admitted at the preview (the edge s 120 admits it, s 45 does not). Ruling 4 answers
  that.
- Under ruling 4 (the largest prediction anywhere in the band, on both sides) the pre-commit
  `make verify` gave `22 failed, 4409 passed`, 21 in `tests/test_api.py` and 1 in
  `tests/test_records.py`, each `assert 422 == 200`. 21 are a bolt preview with only `d` set (7.2,
  7.3, 7.4, 8 or 8.6), s 10 and k 4 at their defaults; the 22nd is the API's at-the-walls part
  (d 999.999, s 1000, k 1e5), admitted at d869b87 only because k/d 100 made its raw prediction
  cheap, which is the bypass itself, so its test is re-pinned to the rule. A d-only M8 has s/d 1.25, below the band, and the
  wide-head edge s 16 (s/d 2.0) predicts a preview peak of 1.32e9 to 1.46e9 B, over the 1.05e9 B
  budget. Over d-only bolts, ruling 4 refused the preview at d 5 and 7 to 9.5 and the fine STL at
  d 9 and 9.5, all admitted at d869b87. With the low edge only below the band, d 5.5 to 9.5 keep
  every artifact, both bypass cases stay refused at all three, and the table is byte-identical.
  d 5 (k/d 0.8, above the band) still loses its preview. Ruling 5 answers that.

The owner's replies, verbatim (the label "(Recommended)" is the orchestrator's, not part of the
ruling):

1. Asked how to fix the head-height bypass: "Clamp k/d, verify on runner (Recommended)".
2. Asked whether to widen the rule past k/d: "All head ratios, max-of (Recommended)".
3. Asked about the preview refused while the fine STL is admitted:
   "Accept, note it in L21 (Recommended)".
4. Asked again after the executor's stop under the nearest-edge rule:
   "B: max over the band (Recommended)". This supersedes the nearest-edge rule.
5. Asked after the second stop, where ruling 4 refused d-only bolt links:
   "2: one-sided B (Recommended)". The option picked stated, in its own text, that a d-only M5
   loses its preview (k/d 0.8, above the band); that answer is the owner's OK for that refusal. It
   supersedes ruling 4 below the band.

This is a ruled change after R30's freeze, not a harness fix. It amends `07-SWEEP-PROTOCOL.md` R11
on the phase branch `gsd/phase-07-operability-re-sweep`. Under it the regenerated
`07-BUDGET-TABLE.md` and fit.json are byte-identical, so B-01's evidence does not move.

| Gap | Rule(s) | Owner ruling |
|---|---|---|
| G28 | R11 | A part whose head ratio (bolt k/d and s/d, nut s/d and m/d) lies outside its band, the [min, max] over the fitted points of its kind with omitted fields at their defaults, is predicted, target by target, as the largest of the raw prediction and the predictions with each out-of-band ratio set to an edge (each such field set to edge x d, every other field held, every combination): a ratio above its band takes both edges, a ratio below it its low edge only. Above the band that is, for this log-linear model, the largest prediction anywhere in the band; below it, max(raw, low edge). ASSUMPTION, unmeasured: a smaller head never costs more than one at the low edge; the 07-15 points below the band test it. R12 applies the envelope to it. Inside every band the prediction is unchanged. The bands are generated from the records by code and emitted into `calc/cost.py`. Plan 07-15 reads, at 5 repetitions, per kind, artifact and ratio, a part above the band and one below it, each admitted under this rule; a reading above its enveloped prediction stops the phase for the owner and does not widen `e`. L21 records that per-artifact budgets can refuse a preview while they admit the fine STL (ISO 4017 M20 x 60 at pitch 1). |

### Follow-up rulings, 2026-10-29 (after the G28 code landed at bc7b2ab)

- **07-15's out-of-band points.** The executor's first pick took the first admitted catalogue row
  in file order, which is the M2 rows in every case: the cheapest parts, the furthest from any
  budget. Reply, verbatim: "Nearest the budget (Recommended)". Each (kind, artifact, ratio, side)
  now also reads the admitted row with the largest enveloped edge ratio, as R27 ranks. R11's "at
  least one part above the band and one below it" still holds, so the protocol text is unchanged.
- **The at-the-walls gate test.** A bolt at every wall (d 999.999, s 1000, k 1e5) was served only
  because k/d 100 made its raw prediction cheap, which is the bypass itself. The executor re-pinned
  the test: info 200, preview `over_budget` 422. Reply, verbatim: "Accept the re-pin
  (Recommended)".

## Gap G29 (owner ruling on named threads below the fitted turns, 2026-10-29)

Quick task 261029-rxk (52dcf95) stopped the B-03 cap at `cost.MIN_FITTED_TURNS`, the fewest built
turns among the 1247 fitted bolt points (3 turns, set by the n3 points at pitch 0.1; explore
40646117094, spread 40646125666). A `thread_length` the user names below that count is still
predicted outside the fit. `ln_turns` is positive, so fewer turns predict a cheaper part: plausible,
but unmeasured. The only request for a runner check sat in the resolved item
`docs/tech_debt/resolved/2026-10-29-default-cap-lands-below-the-fitted-turns.md`, and plan 07-15
did not include it.

Reply, verbatim: "Add to 07-15 (Recommended)".

| Gap | Rule(s) | Owner ruling |
|---|---|---|
| G29 | R11 | A bolt whose built thread has fewer turns than the fewest among the fitted bolt points is predicted by the fit as it stands. Plan 07-15 reads, at 5 repetitions, per artifact, two admitted bolts below that count: the one nearest the budget (largest enveloped edge ratio, as R27 ranks) and the first in catalogue order. A reading above its enveloped prediction stops the phase for the owner and does not widen `e`. |

## Gap G30 (owner ruling after the out-of-band check, 2026-10-30)

Source: plan 07-15 stopped at its G28/G29 out-of-band check (`bench/RESULTS.md`, "out-of-band
check"; `07-15-SUMMARY.md`, "Needs the owner"). Outband run 40909768713 read 7 (point, target)
pairs above their enveloped prediction, all M2 rows at the fine STL:

| point | target | actual / enveloped prediction |
| --- | --- | --- |
| `outband-nut-s-below-iso4032:M2` | seconds | 1.3200 |
| `turns-below-iso4017:M2x4` (G29) | bytes | 1.3116 |
| `outband-nut-m-below-iso4032:M2` | seconds | 1.2217 |
| `outband-nut-s-far-iso4032:M2` | seconds | 1.1255 |
| `outband-nut-s-above-iso4032:M2` | seconds | 1.0696 |
| `outband-nut-s-below-iso4032:M2` | peak | 1.0260 |
| `outband-nut-m-below-iso4032:M2` | peak | 1.0004 |

The executor computed what a widening would do with committed code at 196ef2e (`envelope_check`
over the outband readings, then `_admits_all`), and wrote none of it: nut stl-fine seconds e
1.1069417227945801 to 1.7812452161769916 and peak e 0.5571452809681212 to 0.5976833077470993 refuse
nothing B-01 keeps; bolt stl-fine bytes e 0.5633622849303941 to 1.0504847478595214 refuses 6
catalogue rows at the fine STL, because C1 sets each budget component at the largest catalogue
prediction. The orchestrator checked that 0 of the 294 bolt catalogue rows have fewer built turns
than `cost.MIN_FITTED_TURNS`.

The owner's reply, verbatim, to the SUMMARY's three options (the label "(Recommended)" is the
orchestrator's, not part of the ruling): "1: widen nuts, guard G29 (Recommended)".

This is a ruled change after R30's freeze, not a harness fix. It amends `07-SWEEP-PROTOCOL.md` R11
on the phase branch `gsd/phase-07-operability-re-sweep`. It supersedes G28's "does not widen `e`"
for the nut readings and G29's "predicted by the fit as it stands".

| Gap | Rule(s) | Owner ruling |
|---|---|---|
| G30 | R11 | A nut reading of R11's out-of-band points above its enveloped prediction widens `e` as a cold isolated reading does (R12): the nut stl-fine seconds and peak e are re-derived by committed code from the outband readings and emitted with `emit-constants`, never typed. A bolt reading of those points widens no `e`, so the bolt stl-fine bytes e is not widened. A bolt whose built thread has fewer turns than `cost.MIN_FITTED_TURNS` is refused before any build at every artifact with B-02's `over_budget` 422, naming the fields that set its turns (pitch, length and thread_length); no reading supports its prediction. No catalogue row is below the floor, so B-01 holds; a test pins that. B-03's cap floor stays as it is. If the widening refuses any part B-01 keeps, or changes any set's `--check`, the phase stops for the owner again. |

## Gap G31 (owner ruling on the kernel-refused nuts in the bound set, 2026-10-30)

Source: `07-15-SUMMARY.md`, "Also for the owner". `nut-d30-p0.35-m0.8d-s4d-c0.15-right` and
`nut-d30-p0.35-m0.8d-s1.6d-c0.15-left` are admitted by the cost rule, and R14 asked for an `ok`
explore reading only for its two measured choices. They entered the stl-preview bound set as P
(among the 5 slowest) and as the N = 3 partner of four other P. Every reading that built them was
refused (`BuildError`, the lead-in countersink): 50 readings of bound run 40907549180 and 10 of gzip
run 40909739628. Under R3 those (P, N) and gzip points have no max, which R16, R19 and G22 need.
Recorded in `docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md`.

The owner's reply, verbatim (the label "(Recommended)" is the orchestrator's, not part of the
ruling): "Exclude, rerun preview (Recommended)".

This is a ruled change after R30's freeze, not a harness fix. It amends `07-SWEEP-PROTOCOL.md` R14
on the phase branch `gsd/phase-07-operability-re-sweep`. R19 takes the bound set's points and is not
edited.

| Gap | Rule(s) | Owner ruling |
|---|---|---|
| G31 | R14, R19 | Every candidate of a bound set (the 5 slowest, the two prediction extrema, the two measured extrema and every contention partner) is an admitted explore point whose explore reading is `ok` at every artifact, not only the two measured choices. `bound.json` and `gzip.json` are regenerated under their recorded envelope. Only the stl-preview contention and gzip points this changes are read again, at 5 repetitions; the records are committed before they are used and the earlier readings of the points they replace decide nothing. D(A), the load mix, the stl-fine and STEP bound sets and the arena set do not change. |

## Gap G32 (owner ruling on the drift stop, 2026-10-30)

Source: plan 07-16 stopped at R23 (`07-16-SUMMARY.md`, "Needs the owner: the R23 drift stop";
`bench/RESULTS.md`, "R22 and R23 (07-16)"). Drift run 41016507364 read Z(A) 20 times per repetition,
5 repetitions, all `ok`. Its drift, the peak after build 20 minus the peak after build 1 at the worst
repetition, was above the allowance (0.10 x the smallest build-1 peak) at every artifact:
stl-preview 53616640 B against 44301516.8 B, stl-fine 323194880 B against 137344204.8 B, and step
31100928 B against 28473344.0 B. Most of each repetition's growth falls between build 1 and build 2.
The largest peak after build 20, 1716760576 B (stl-fine, rep 1), is above both W (1533550592 B,
contention run 40907549180) and W(4) (1652121600 B, run 41016510597). The figures are
`check-r22-r23` output at 378d58c.

The owner's reply, verbatim (the label "(Recommended)" is the orchestrator's, not part of the
ruling): "1 + longer drift run (Recommended)".

This is a ruled change after R30's freeze, not a harness fix. It amends `07-SWEEP-PROTOCOL.md` R16
and R23 on the phase branch `gsd/phase-07-operability-re-sweep`, and the plateau criterion was
committed before the 60-build reading was dispatched. The plan executor took R23's allowance for the
plateau to be 0.10 x the smallest build-1 peak among the repetitions of both drift readings of an
artifact. That is never more than the 20-build reading's own allowance.

| Gap | Rule(s) | Owner ruling |
|---|---|---|
| G32 | R16, R23 | A drift reading of 60 builds per repetition is read: 5 repetitions, the same three artifacts, the same points in the same order as the 20-build set, each deadline 60 x the artifact's timeout. The plateau: per artifact and repetition, the max peak over builds 41 to 60 minus the max peak over builds 21 to 40 must be at most R23's allowance at the worst repetition of every artifact. Otherwise the phase stops for the owner again, and the next step is recycling. If the plateau holds, W (R16) also takes the largest peak after any build of the drift readings, so the 60-build set's peak replaces 1716760576 B as the input when it is larger. The values are re-derived by committed code. If the pick N, any timeout or any set's `--check` moves, the phase stops. R23 no longer stops on the build-1 to build-20 drift alone, because the drift is absorbed into W, and `max_tasks_per_child` stays unset while the plateau holds. |

## Gap G33 (owner ruling on the regeneration checks across platforms, 2026-10-30)

Source: plan 07-18's checkpoint. The first CI run of the phase branch, run 41042483745 at 155fabb,
failed `test (3.12)` on two regeneration checks: `tier-order.json`'s `--check` and the tier file's
regeneration test. Both files hold floats from `cost.predict`, which is `math.exp` of a sum of
`math.log` terms, and the platform libm sets their last bit. For example, a limit of the tier file
is 6801399.663168809 on macOS and 6801399.66316881 on the Linux runner, one ulp apart. Membership
and order did not move, and the bounds job judges the limits the committed file holds.

The owner's reply, verbatim (the label "(Recommended)" is the orchestrator's, not part of the
ruling): "A: tolerance on limits (Recommended)".

The measurement, by committed code (`python -m bench.oper_sets prediction-drift`, ef45c0c), in
the `test (3.12)` job of run 41048346068 on the runner: every file `--check` and the tier test
write again was compared with the committed one. Only `tier-order.json` (1254 edge ratios) and
the tier file (1305 limits) hold predicted floats. One float in each differs, by a relative
3.239877599502309e-16 (1.459 x 2^-52, an edge ratio) and 1.369310172520534e-16 (0.617 x 2^-52, a
limit), and no other value of any file differs. The tolerance is 2^-51, the smallest whole
multiple of 2^-52 at or above the larger.

This is a ruled change after R30's freeze, not a harness fix. It amends `07-SWEEP-PROTOCOL.md` R27
on the phase branch `gsd/phase-07-operability-re-sweep`.

| Gap | Rule(s) | Owner ruling |
|---|---|---|
| G33 | R27 | When `tier-order.json` or the tier file is written again to check it, only a float computed from the prediction (an edge ratio, a limit) may differ from the committed one, by a relative difference of at most 2^-51 (2 x 2^-52); every other value, the order and the membership stay exact. The tolerance is the measured cross-platform difference (largest 1.459 x 2^-52, run 41048346068) rounded up to a whole multiple of 2^-52. |

## Gap G34 (owner ruling on the required tier's wall time, 2026-10-30)

Source: plan 07-18's checkpoint. The bounds job of run 41042483745 read the 435 points of R27 step
5 in one job: 35.5 min, from 10:43:07 to 11:18:38, with the readings' container walls summing to
2092.9 s. D-12 targets about 10 minutes. R27 step 5 gives each artifact 600 s of charges, so the
tier holds about 30 minutes of cold walls, and every reading also starts and stops a container.

The owner's reply, verbatim (the label "(Recommended)" is the orchestrator's, not part of the
ruling): "Shard into parallel jobs (Recommended)".

This is a ruled change after R30's freeze, not a harness fix. It amends `07-SWEEP-PROTOCOL.md` R27
on the phase branch `gsd/phase-07-operability-re-sweep`. Step 5's membership and its 600 s per
artifact do not change.

| Gap | Rule(s) | Owner ruling |
|---|---|---|
| G34 | R27, D-12 | The required tier is read in parallel shard jobs on the one image, cut deterministically in the tier file's order: each shard is the longest run of consecutive points whose summed estimate stays under 600 s (a point's estimate is its explore `wall_s` when ok, else the larger of that and its timeout), so every point is judged exactly once. Each shard job's `timeout-minutes` is at least twice its estimate. The shard jobs replace `bounds` in `required-jobs.txt`, and a test holds the shards to a partition of the tier. D-12's 10 minutes is the target of one shard. |

## Gap G35 (owner ruling on the in-wall parts the kernel refuses, 2026-10-30)

Source: the debug session `.planning/debug/in-wall-kernel-builderror.md` (commit 10d8c49), opened
after G33's ruling 1 on the 11 tier points the kernel refused in runs 41042483745 and 41052312369.
The 20 in-wall parts of `docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md` are
refused by one cause: the OCCT booleans that cut the tip cone (bolt), the lead-in countersink and
the prism minus void (nut) return a wrong solid while reporting success once the swept thread's
representation error is not small against the thread depth, and the gates refuse it (L02 holds).
Nothing bounds pitch against `d` before the kernel. No wall on `d / pitch` alone holds the whole
failure region and keeps B-01: the bolt's tip error also grows with the number of turns at a fixed
`d / pitch` in two bands of `d` (0.5 to 0.85 and 1.6 to 3.3 mm), and nuts fail at isolated cells.

F, as the session's scripts computed it over its grid records (shipped code; macOS arm64 and the
production image emulated as linux/amd64, which R1 counts as context, not a bound), per kind the
smallest exact `d / pitch` (`Fraction(repr(d)) / Fraction(repr(pitch))`) of a refused build:

- bolt, over the 3-turn forms only (`thread_length = length = 3 pitch`, and the same thread with a
  shank of length `d`): 26.999784001727985 (d 3, pitch 0.111112, right hand) on macOS arm64 and
  26.999990550003307 (d 2, pitch 0.0740741, right hand) on linux/amd64. The forms with 30, 60, 80
  and 90 turns are refused lower (14.999875001041659, 9.999954545661156, 8.0 and
  6.99998250004375 on macOS arm64) and are the residual region, not F.
- nut, over the four forms (`m` 0.8 d, `s` 1.6 d, `clearance` 0.15; `s` 4 d; `clearance` 0;
  `m` = d): 10.999993714289307 (`m` = d, d 3.5, pitch 0.318182, right hand) on both.

The margin rule (the largest ISO 3 R10 number at or below F / 1.25) gives a bolt W of 20 and a nut
W of 8. Measured by the session at those walls: they refuse all 20 in-wall parts, 0 of the 294
bolt and 0 of the 14 nut catalogue rows (the catalogue's largest `d / pitch` is 8 for both kinds),
117 of the 475 in-wall explore labels (the 20, and 97 that build today, 77 of them admitted at an
artifact) and 80 of the 435 points of `tests/data/oper_boundary.json` (the 11 tier failures, 26
other bolt and 43 other nut points). Under the bolt wall the grids still hold refused bolts with
more than 3 turns: 83 of 2789 built cells on macOS arm64 (0 of 782 at 3 turns, 0 of 726 with a
shank, 36 of 687 at 30 turns, 12 of 307 at 60, 3 of 6 at 80, 32 of 281 at 90) and 13 of 178 on
linux/amd64. Under the nut wall no nut cell read is refused (0 of 568 on macOS arm64, 0 of 44 on
linux/amd64). A grid is a sample: isolated nut failures tied to a sewn seam near a face cannot be
bounded by one.

The owner's replies, verbatim (the label "(Recommended)" is the orchestrator's, not part of the
ruling):

1. On the guard: "Guard d/p wall + debt (Recommended)". A part whose exact `d / pitch` is above
   its kind's W is a `422` of type `pitch_too_fine` naming `["d", "pitch"]`; the value W itself is
   admitted. It is validated once, at the parameter-model boundary, as a direct conflict between
   two fields (L02). The kernel is not changed.
2. On the nut's wall: "Nut d/p ≤ 8 (Recommended)". The bolt's W (20) and the nut's W (8) come from
   one margin rule: the largest ISO 3 R10 number at or below F / 1.25, F the smallest refused
   `d / pitch` of the kind.
3. On where W is measured: "Walk W on runner (Recommended)". W is not final until a walk on the
   runner confirms it: the walk set is generated by committed code and committed, with this
   ruling and the rule, before it is dispatched; its records are committed before they are used;
   F and W are recomputed from them by committed code. A W other than 20 (bolt) or 8 (nut) stops
   the phase for the owner.
4. On what the wall leaves: "Must debt, don't block (Recommended)". The residual stays as debt of
   severity must: bolts with longer threads in the two bands of `d`, and isolated nut cells, that
   the wall admits and the kernel refuses.

This is a ruled change after R30's freeze, not a harness fix. It adds R31 to
`07-SWEEP-PROTOCOL.md` on the phase branch `gsd/phase-07-operability-re-sweep`; no other rule is
edited.

| Gap | Rule(s) | Owner ruling |
|---|---|---|
| G35 | R31 (new), D-08 | A fine-pitch wall per kind: a part whose exact `d / pitch` is above W is a `422` `pitch_too_fine` naming `d` and `pitch`, at the parameter-model boundary; W is admitted. W is the largest ISO 3 R10 number at or below F / 1.25, F the smallest exact `d / pitch` of a `refused` or `crashed` reading of the kind in the walk: bolts with 3 turns of thread (with and without a shank), nuts in four forms, a grid of `d` and `d / pitch` around the wall, both hands, one reading each at `step`, written by `bench/oper_sets.py` as `walls-pitch`. A `killed`, `capped`, `no_cgroup` or missing reading, or a kind with no refusal, leaves W with no number and stops the phase; so does a W other than the ruled 20 (bolt) and 8 (nut). W ships written from the records by code. The longer-thread bolts and the isolated nut cells below W stay as must debt. |

## Gap G36 (owner ruling after the fine-pitch walk, 2026-10-30)

Source: plan 07-18 stopped at R31's check. Walk run 41074314305 (`walls-pitch` at 7ecaebb, records
committed at cfdf5f2) read all 5656 points once: 5579 `ok` and 77 `refused`.
`python -m bench.oper_sets pitch-walls` over the records gives:

- bolt: F = 26.999784001727985 at `pitch-bolt-n3-d3-q27-right` (d 3, pitch 0.111112), F / 1.25 =
  21.59982720138239, W = 20, as G35 ruled. All 60 bolt refusals are right-hand.
- nut: F = 6.999993636369421 at `pitch-nut-base-d2.2-q7-left`, F / 1.25 = 5.599994909095537, W = 5,
  not the 8 G35 ruled. Six cells are refused at `d` 2.2, `d / pitch` 7 (forms base, s4 and m1, both
  hands); the c0 form there, `d` 2.0, 2.4 and 2.5 at `d / pitch` 7, and `d` 2.2 at 6 and 8 are all
  `ok`. No nut is refused at `d / pitch` 5 or below (0 of 344); the other 11 nut refusals are at
  `d / pitch` 11. A nut W of 5 refuses 13 of the 14 nut catalogue rows, the default M6 nut
  (`d / pitch` 6) among them, so no nut W keeps B-01 and holds the island.

The executor also found that the guard, applied by the production model, would draw `bound.json`,
`gzip.json`, `arenas.json` and `bound-rerun.json` again (they hold parts it refuses) and, with D(A)
drawn again, `load.json`, so the committed runtime records would no longer match their sets. With
the committed D(A) kept, R27 step 5 less the 80 points the guard refuses leaves 355 points
(stl-preview 151, stl-fine 51, step 153), each in the committed tier and `ok` at `explore`; every
artifact's third edge point is refused by the guard, so each keeps 2.

The owner's replies, verbatim (the label "(Recommended)" is the orchestrator's, not part of the
ruling):

1. "Rule nut W = 8, island to debt (Recommended)"
2. "(i)(b) old sets, drop refused (Recommended)"

This is a ruled change after R30's freeze, not a harness fix. It amends R31 of
`07-SWEEP-PROTOCOL.md` on the phase branch `gsd/phase-07-operability-re-sweep`. It supersedes
G35's ruling 2 for the nut (its W is not taken from the margin rule); G35 stands otherwise.

| Gap | Rule(s) | Owner ruling |
|---|---|---|
| G36 | R31, R27 | The nut's W is 8 by ruling, not by the margin rule; the bolt's W stays the margin rule's, written by code from the walk's records (20). The 6 island cells (`d` 2.2, `d / pitch` 7) and any nut cell the walk refused at or below 8 join the residual must debt; the nut's constant is a ruled value whose comment cites this ruling and the island. The committed point files and the sets drawn from runner records are checked under the model they were drawn under, without the fine-pitch wall (as `bench.oper_lift.registered` does for the walls), so `runtime.json` and L22 to L24 do not move. The required tier is R27 step 5 over the committed D(A) with the points the fine-pitch wall refuses dropped and nothing drawn in their place: 355 points, each artifact keeping 2 edge points. |

## Gap G37 (owner ruling on the full tier's residual points, 2026-10-31)

Source: plan 07-19's checkpoint, raised before anything was dispatched. The full grid of R28 was
drawn under the shipped model (the parameter model with L25's walls, admission by `cost.fits`) and
checked against the explore records (run 40646117094) and the fine-pitch walk (run 41074314305):
1056 points. These are 924 catalogue points, all admitted; 42 nut-factorial points (14 parts), all
admitted, with 201 refused by the parameter model (171 `pitch_too_fine`, 30 `turn_cap`); and 90
dense-boundary points, admitted by construction. No pair is refused by the cost model. 114
admitted points lie in the residual region of
`docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md` (a bolt with d in 0.5 to
0.85 or 1.6 to 3.3 mm, exact d / pitch at most 20 and more than 3 turns). No point is at the nut
island (d 2.2, d / pitch 7). 96 of the 114 are catalogue points, each `ok` at explore. The other
18 are dense-boundary points with no runner reading: M2, M2.5 and M3 at their coarse pitch, both
hands, 90 turns at stl-preview and stl-fine and 57 to 61 turns at step. Their only evidence is
the debug session's text (E27, E29: d 2 and 3 at d / pitch 5 and 6 built at 90 turns, both
hands, on macOS arm64 and the emulated linux/amd64 image; M3-right at 90 turns read a tip piece
of +0.0291 against T_PIECE 0.03), which R1 counts as context.

The owner's replies, verbatim (the label "(Recommended)" is the orchestrator's, not part of the
ruling):

1. "2: read the 18 first (Recommended)"
2. "R4 'dropped' list (Recommended)"

Neither changes a rule, so `07-SWEEP-PROTOCOL.md` is not amended. Ruling 1 adds one reading of
the 18 points before the full tier's trigger and gate are built. It sets no figure, and R28 and
R29 judge the full tier as written. Ruling 2 is R4 as written.

| Gap | Rule(s) | Owner ruling |
|---|---|---|
| G37 | R28, R29, R4 | (1) Before the full tier's trigger and merge gate are built, the 18 dense-boundary points inside the residual region are read once on the runner, as a set written by committed code and committed before it is dispatched, with its records committed before they are used. Each point is judged as the full tier judges it (R29: `ok`, a cold wall within its timeout, every target within prediction x (1 + e)); the tip piece of each distinct part is read alongside and reported against T_PIECE. If all 18 pass, the full tier judges every point as R28 and R29 write it, with no exclusion. If any is refused, or reads over its envelope or past its timeout, the phase stops for the owner before the trigger and the gate are built. (2) A full-tier combination the parameter model refuses (201 nut-factorial points: 171 `pitch_too_fine`, 30 `turn_cap`) is listed in the file's `dropped` array with its error type and is not judged (R4). |

## Gap G38 (owner ruling on the nut clearance the cost model was not fitted on, 2026-10-31)

Source: `07-REVIEW.md`, CR-01. R11 fits a nut's `clearance` as a plain linear feature, and the
fitted points (explore 40646117094, spread 40646125666) hold it at two values only: computed by
`bench.oper_fit.head_bands` over the 1529 fitted points with omitted fields at their defaults, its
[min, max] is [0.15, 5.0] mm. The parameter model allows a clearance from about
`-(d/2 - 5H/8 - 0.01)` up to 496.999 mm, and G28's band guard covered the head ratios only. The
stl-fine nut coefficients of `clearance` are positive (bytes 0.112, seconds 0.065, peak 0.055 per
mm), so below 0.15 the model predicted a cheaper nut than any reading. The reviewer's reproducer,
`NutParams(d=163.65, pitch=21.743, s=387.26, m=1589.12, clearance=-30.32)`, was admitted at the fine
STL on a raw prediction of 24,513,233 bytes; `solid.export(p, "stl", "fine")` wrote 591,529,584
bytes in 26.95 s on macOS arm64 (mesh bytes are geometry; R1 counts the host as context, not a
bound). That does not fit the 256 MiB tmpfs the export is written to.

The owner's reply, verbatim (the label "(Recommended)" is the orchestrator's, not part of the
ruling): "Band clearance like G28 (Recommended)".

Measured by committed code at the implementing commit: the reproducer is refused at all three
artifacts; 0 of the 294 bolt and 0 of the 14 nut catalogue rows change prediction at any artifact
(every catalogue nut is at the default 0.15); both default parts are admitted at every artifact; a
nut with clearance inside [0.15, 5.0] is predicted bit for bit as under G28 alone; every file
`--check` and `prediction-drift` write again is unchanged, and `runtime.json` is unchanged. G28's
out-of-band points are head-ratio points only, so `outband.json` draws none for the clearance.

The reviewer's second case, `d=92.28 pitch=31.418 s=130.54 m=967.04 clearance=-21.12`, stays
admitted at the fine STL under this rule, judged at the low edge 0.15: enveloped prediction
76,540,259 bytes. Read by the executor with `solid.export` on macOS arm64: 121,632,684
bytes at -21.12 and 223,951,384 bytes at 0.15. So this nut is cheaper below the band, as the rule
assumes, but it misses its enveloped prediction by 2.93 x inside the clearance band (its m/d, 10.5,
is above the m band; the cause is not measured). Both readings are under the 239,508,059-byte
budget. That miss is not a clearance defect and this ruling does not answer it; it is filed as
`docs/tech_debt/active/2026-10-31-tall-nut-misses-its-envelope-inside-the-clearance-band.md` and
put to the owner.

This is a ruled change after R30's freeze, not a harness fix. It amends `07-SWEEP-PROTOCOL.md` R11
on the phase branch `gsd/phase-07-operability-re-sweep`. `python -m bench.oper_fit table` writes the
same bytes with the clearance band as without it, and fit.json and B-01's budget do not move.

| Gap | Rule(s) | Owner ruling |
|---|---|---|
| G38 | R11 | The nut's `clearance` is a banded feature as G28's head ratios are, in mm rather than over d: its band is the [min, max] over the fitted nut points with omitted fields at their defaults, computed from the records by code and emitted into `calc/cost.py` with the head-ratio bands, never typed. A clearance above its band is predicted, target by target, as the largest of the raw prediction and the predictions at both edges; one below it as max(raw, low edge), with every combination of the part's other out-of-band edges, as G28 rules. ASSUMPTION, unmeasured on the runner: a smaller clearance never costs more than one at the low edge. Inside the band the prediction is unchanged. |
