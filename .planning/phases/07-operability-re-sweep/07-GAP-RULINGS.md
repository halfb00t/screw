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
