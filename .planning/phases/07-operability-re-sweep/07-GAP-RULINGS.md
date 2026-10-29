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
