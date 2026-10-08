# Phase 2: Thread spike — protocol

This file is pre-registered: everything above the `## Results` heading lands on `main` in PR 1 before run 1 (D-16, D-19), and the run guard refuses any run while that text differs from `origin/main`'s.

## Question

**Construction.** Which helical construction do we build? The sewn twist-section is the research favourite; one-pipe twist and the `cq_warehouse` ruled surface are reference rows, and the naive `sweep` + `fuse` is the negative control. The answer includes the failure frontier: for each size, the turn count and length at which each construction first fails or goes silently wrong (D-04, D-06, D-09).

**Mesh budget.** What does a fine mesh of a threaded rod and a threaded void cost? Triangles, build and mesh seconds, peak RSS, STL bytes and the gzip ratio, per size, against the INTERIM 30 s and 64 MB budgets (D-10, D-20).

**Pair-check falsifiability.** Can a kernel pair check be made falsifiable? A nut void against a rod at the screw-motion matched poses must read empty, and the half-pitch-offset controls must read non-empty within a band of the closed-form estimate. A check that cannot fail proves nothing (D-11, D-12, D-14).

**Volume estimator.** Which volume estimator agrees with the closed form across the grid: `BRepGProp.VolumeProperties_s` or the STL's signed tetrahedron volume? The default `Volume()` is already known to be 15 to 21 % off on some constructions (D-20).

## Owner rulings (D-01 checkpoint, 2026-10-06)

- **Profile pin: `basic`.** ISO 68-1:2023 basic profile, flat crest and flat root. Every measured row builds this section. Read by the owner on **2026-10-06**. One-way door: a later profile change re-runs the whole campaign (D-01). The design (rounded-root) profile stays a deferred option.
- **Coefficients, owner-confirmed.** The owner read the standard and offered no correction; the values below stand as presented at the checkpoint. No clause text is copied here.
  - H = (sqrt(3)/2) * P
  - crest flat P/8, at radius d/2
  - root flat P/4, at radius d/2 - 5H/8
  - flanks at 60 degrees
  - Downstream: plan 02-02 codes `section_radius` and `section_area` from these values.
- **R0: not applicable.** Basic is pinned, so rod and void share one section and one builder (the nut-void section question only exists for the design profile).
- **R1: planner default.** The pair verdict stays exactly D-12/D-14: all 3 matched poses empty AND all 3 half-pitch controls non-empty within the band. Variant rules (2 of 3 controls; the same-pose c = -0.05 reading as the control; seam pose excluded) are computed from the same readings and reported beside the verdict, never changing it. D-14 is not amended. Downstream: plan 02-05 pair rules.
- **R2: planner default.** D-03's lower length bound is min(P, 1 mm), keeping sub-turn rows such as M8 L = 1 mm = 0.8 turn: 1790 lengths per hand. Downstream: plan 02-03 grid counts.
- **R3: planner default.** `bench/RESULTS.md` carries each run's header, host state, time-labelled load readings, per-size aggregates and every non-ok or over-budget row verbatim. The raw per-row JSONL and the run's Markdown are committed under `bench/results/thread-spike/`, with the JSONL sha256 in `bench/RESULTS.md`. This narrows D-16's "verbatim". Downstream: plans 02-03 and 02-07 record layout.
- **R4: planner default.** A non-decisive run's validity, solid-count, volume and pair outcomes count. Its timing-derived claims (the 30 s frontier stop, a seconds-based cap) are reported as not established and never re-run toward a pass (D-17). The owner runs the timing-critical campaign detached, with every agent session closed. Downstream: plans 02-03, 02-07 and 02-08.
- **R5: planner default.** Nut heights m in mm, each with its source label kept verbatim from the checkpoint. Downstream: plan 02-05 `NUT_HEIGHT`. m only scales the engaged length and the closed-form expectation together; it is a label, not a verdict input.
  - M5 4.70, M6 5.20, M8 6.80, M10 8.40, M12 10.80, M16 14.80, M20 18.00: m max as read from the ISO 4032:2023 preview by the research. UNVERIFIED (the owner did not re-read them from the standard).
  - M14 12.80 and M18 15.80: memory of the same table, not re-read. UNVERIFIED.
  - M7 5.60: ISO 4032:2023 added M7 but no value was read by anyone and the owner supplied none, so this is 0.8 * d as a stated input. UNVERIFIED.
  - M2 1.60, M2.5 2.00, M3 2.40, M4 3.20: Annex A not read; memory of the withdrawn ISO 4032:2012. UNVERIFIED.
  - M3.5 2.80: 0.8 * d, no ISO 4032 row. UNVERIFIED.
- **Pre-registered values: no objection raised, they stand.** Planner-set under D-07, D-20 and CONTEXT "Claude's Discretion", not owner-supplied: T_PASS 1e-4 relative; pair band 1e-3 relative; empty threshold 1e-6 mm3; row timeout 120 s, pair cell 600 s; matched poses theta = -2pi/3, 0, 2pi/3 (the seam pose included, because excluding it would be a pose picked after seeing probe data); grid void clearance 0.20 mm; tip-chamfer cone 30 degrees from the end face from the minor radius (ISO 4753 unread, UNVERIFIED); sewing tolerance 1e-4; K rule: fewest fine triangles, then STEP bytes, then smaller K.

Transparency note (T-02-01): before the owner ruled, the orchestrator recommended `basic, defaults`, with these reasons: the four spike questions do not depend on root shape; basic is the only profile with evidence (closed form within 7.6e-6 on 576 of 576 research rows); design adds an unmeasured root radius, a numeric integral and R0 before any row exists; amending D-14 before run 1 would tune the verdict toward a pass; m is a label, not a verdict input. The owner then ruled in two messages, quoted verbatim:

> basic, defaults
>
> today

The second message answered the question "the date you read ISO 68-1:2023 (today is 2026-10-06) — reply `today` or a date".

### Owner rulings on the harness's protocol questions (2026-10-06)

Building the harness (plans 02-03 to 02-05) raised four protocol questions that the plans left open. The orchestrator put them to the owner with a recommendation for each. The owner replied, verbatim:

> defaults

"defaults" takes the orchestrator's recommendation on all four:

1. **Ladder block scope: `SAMPLE_SIZES`.** Plan 02-03's block list said the mesh ladder runs on every size, its Task 1 comment said the sample sizes; the harness builds `SAMPLE_SIZES` (M2, M2.5, M3, M6, M8, M10, M16, M20) and the owner confirms it. The ladder is evidence for the preset choice, not a verdict input, so it needs no size the K sweep and the reference rows do not already use.
2. **The flaky pool test is filed as debt.** `tests/test_pool.py::test_a_dying_worker_surfaces_as_broken_pool_and_is_replaced` failed once in wave 2 under host load 4 to 23 and passed on retry, with no recurrence in waves 3 to 5. It is filed as `docs/tech_debt/active/2026-10-06-test-pool-dying-worker-flake.md` (Severity: must) and stays logged in `.planning/phases/02-thread-spike/deferred-items.md`. It is not a protocol input and no campaign result depends on it.
3. **The 120 s row timeout stays.** `verdict.ROW_TIMEOUT_S` is not raised for any reason. A container void row that times out under amd64 emulation makes the container bar "not established", never "failed", and never a reason to raise the bound (D-17).
4. **The pair run is required.** The overall verdict requires the pair run: a size that is not falsifiable on both hands, or whose mixed-hand pair did not read violated, fires the escape clause, and a campaign without a pair run is never a pass. The owner confirms this as protocol.

Rules the harness executors introduced and flagged for this protocol. These are not new owner decisions: they are registered here, tied to their constants in the Protocol inputs tables where they have one, and are open to the review of PR 1:

- `GZIP_TABLE_TIMEOUT_S = 900`: a row that asks for L19's gzip table gets 900 s instead of 120 s, because the table compresses one STL 35 times at each of three levels and the largest fine STL is about 164 MB (plan 02-04).
- Container runs are never decisive, whatever the host gate read, but their rows count toward the pass bar and the escape clause, because production runs in that image (D-05). A campaign without a container run is never a pass (plan 02-04).
- The controls block's smoke expectation, a check of the harness and never a campaign result: the naive negative control never reads ok, the one-pipe row reads ok and the ruled-surface reference builds (plan 02-04).
- The 30 degree tip-chamfer cone is an UNVERIFIED input (ISO 4753 unread); the trim rows it feeds are Phase 4 cost evidence and never enter the pass bar (D-08, plan 02-04).
- `campaign` skips, and logs, a block whose K-sweep or frontier input did not complete, so K is never selected from half a sweep (plan 02-05).

## Environment

- **Host:** Apple M2 Max, 12 CPUs, arm64, 32 GiB RAM, macOS. Every run prints `machine_facts()` ("12 CPUs, arm64, 32.0 GiB RAM"), the git HEAD, the protocol blob and commit, and the load readings with the UTC time each was read.
- **Python:** 3.12 (3.12.13 at registration; L01).
- **Kernel pair:** cadquery 2.8.0 with cadquery-ocp 7.9.3.1.1, pinned in `requirements.txt` (L06). A kernel bump is a re-measure event: nothing measured on one pair is carried to another. Every run prints the installed versions.
- **Container:** the production image `screw:latest` (built by `make image`), linux/amd64 under emulation on this arm64 host. Emulated timings feed no bound.
- **Ruled-surface reference:** `cq_warehouse` at commit `daa46507ecc429c0e2dce11d9d5ffd09b12a42af`, installed with `--no-deps` into a scratch directory outside the repository, named by `SCREW_SPIKE_CQW`, approved by the owner on 2026-10-06 (plan 02-04), never in `pyproject.toml` or `requirements.txt` (D-06).
- **Quiet gate (D-17):** a run releases decisively once three consecutive 1-minute load readings, 30 s apart, are all strictly under 1.5; after 900 s without that it releases non-decisive. The constants are in the Protocol inputs table and no flag overrides them.
- **Who runs what (owner ruling R4):** the owner runs the campaign, detached, with every agent session closed, because a host with an open agent session idles near 2.0 and reads non-decisive.

## Method

**The command.** One command runs the whole spike, after PR 1 has landed (`make bench.thread ARGS="check-protocol"` exits 0 and prints "protocol guard: held"):

```
SCREW_SPIKE_CQW=<scratch dir> make bench.thread ARGS="campaign --run-id <prefix>"
```

The prefix is at most 50 characters and fully matches `[a-z0-9][a-z0-9-]{0,63}`; each block is recorded as run id `<prefix>-<block>`, and `<prefix>-campaign.md` logs the campaign. The container block needs `docker` and the image; the controls block needs the scratch directory. A block that refuses to start or crashes is logged and the rest still run. Every block asks the protocol guard and the quiet gate for itself.

**The blocks, in `CAMPAIGN_BLOCKS` order, with the rows exactly as the code builds them.** "Full rod row" is a rod with a preview mesh (0.08 mm, 0.5 rad) and a fine mesh (0.01 mm, 0.1 rad), the STL check under `FINE_CHECK_CEILING`, gzip-1 on the fine STL and a STEP export, measured for solid count, `isValid()`, the precise volume and the default `Volume()`. A void row is the cutter at clearance `VOID_CLEARANCE` (0.20 mm), measured for solid count, validity and precise volume only. Lengths are exact fractions; K means the segment length in turns.

| Block | Rows | Count |
|---|---|---|
| `ksweep` | `SAMPLE_SIZES` x K in {3, 5, 10} x both hands. At the standard max: the full rod row and the void. At 250 turns: the rod with the preview mesh only (no fine mesh, no STEP) and the void. K is what is being swept, not an input. | 192 |
| `grid` | all 15 sizes x every D-03 length (every integer-turn k * P and every integer mm from min(P, 1 mm) up to min(10 d, 200 mm), each length once) x both hands: the full rod row and the void, at the K the rule selected. | 7160 (1790 lengths per hand) |
| `frontier` | per size and hand, from the first multiple of 5 turns strictly above the standard max in steps of 5 up to 250 turns: the full rod row and the void at each step, stopping at the first step `frontier_stop` ends; one line per walk says why it ended. | at most 2236 |
| `ladder` | `SAMPLE_SIZES`, right hand, at 10 turns and at the standard max: the rod at the preview and fine presets and at depth presets h/4, h/8, h/16, h/32 (h = 5H/8, angular 0.5 rad), gzip-1 on every preset, no STEP, the STL check under the ceiling. | 16 |
| `trim` | all 15 sizes x both hands at the standard max: the full rod row with its tip trimmed (cone `TIP_CHAMFER_DEG` from the end face at the minor radius), so the request cost is build + trim + the slower export. Phase 4 cost evidence. | 30 |
| `controls` | `SAMPLE_SIZES`, right hand, built by the comparison constructions (no meshes, no STEP): the naive `sweep` + `fuse` negative control at 10 turns, 10 mm, 20 mm and the standard max; the one-pipe twist at the standard max and at 100, 160, 200 and 250 turns; the ruled-surface reference at 10 turns and the standard max, in a second worker that alone sees `SCREW_SPIKE_CQW`. A length that two of these coincide on is built once. | 85 (29 naive, 40 one-pipe, 16 ruled) |
| `rss` | one fresh `--once` child per row, the only place a peak RSS exists: per size and hand at the standard max, one child at the fine preset and one at the preview preset (gzip-1 on that preset), the right-hand fine child also running L19's gzip table (levels 1, 6, 9); then each frontier walk's terminal row at fine. Needs the frontier run's rows. | 90 (60 + 30 terminals, 15 gzip tables) |
| `pair` | per size, both same-hand pairs at c in {0, -0.05, 0.05, 0.10, 0.15, 0.20} mm, each read at the three matched screw-motion poses and the three half-pitch controls; the mixed pair (right-hand rod, left-hand nut) at the four proof clearances, matched poses only; then, on `PAIR_REFERENCE_SIZES`, the two K values other than the locked one, right hand, proof clearances, as reference rows. Nut height m from the NUT_HEIGHT table. | 272 cells (15 x (2 x 6 + 4) + 4 x 2 x 4) |
| `container` | the locked construction over the full grid, both hands, in `screw:latest` under linux/amd64: the rod without presets or STEP, and the void; validity, solid count and volume only. | 7160 |

At most 16 969 rows and 272 pair cells in all. A pair cell is one request with its own deadline; a row has `ROW_TIMEOUT_S`, a row that asks for the gzip table has `GZIP_TABLE_TIMEOUT_S`, a pair cell `PAIR_TIMEOUT_S`.

**What a row is judged against.** The closed form of the pinned profile's section times the length (Rules). The default `Volume()` is a reference column and never an input to any verdict.

**The record.** Each run writes `bench/results/thread-spike/<id>.jsonl`: a header record first (run id, block, git head, protocol blob and commit, decisive, the quiet readings, K and where K came from), then one row per line, flushed as written, so a run that dies keeps what it measured; and `<id>.md`, the Markdown report. The file is opened exclusively: a run id already recorded is refused and nothing is ever overwritten. Owner ruling R3 sets what `bench/RESULTS.md` carries for each run: the header, the host state, the time-labelled load readings, the per-size aggregates, every non-ok or over-budget row verbatim, and the JSONL's sha256; the raw JSONL and the Markdown are committed under `bench/results/thread-spike/`. `.stl` and `.step` files are never committed.

**Order of blocks and where K comes from.** K is read only from the K sweep's own record through `select_k`; there is no way to type one. When no K qualifies the harness still runs the remaining blocks at `DEFAULT_K` = 5 and labels it so, to keep the frontier and budget data for a roadmap revision. `campaign` skips and logs every block when the K sweep did not complete, and the `rss` block when the frontier did not.

**Smoke runs** (`smoke`, `smoke --block <block>`, `smoke --pair`) are harness checks: no run id, output in a temporary directory, the guard informational, the quiet cap 0. They are never recorded in `bench/RESULTS.md` and never cited as evidence. The controls block's smoke expects the naive row not ok, the one-pipe row ok and the reference built; every other block's smoke expects every row ok.

**The harness is frozen at landing.** A harness fix after run 1 is a new PR that visibly post-dates this one; the affected block re-runs under a new run id and both runs are recorded. An interrupted block keeps its partial JSONL, which is never resumed or overwritten; it is re-run once under a new run id, and both runs stay recorded. `verdict --campaign` reads one run per block under one prefix and refuses two, so the Results name, before the verdict is read, the one prefix that holds one run per block and how it was assembled; the choice is made by completeness (a partial record lacks rows by definition), never by which outcome is better.

**The verdict** is `make bench.thread ARGS="verdict --campaign <prefix>"`, also run by `campaign`: it recomputes every row's class from the raw record and trusts no stored class (a hand-edited JSONL cannot change an outcome), prints K and the rule's table, the estimator and the gate tolerance, the pass bar and the escape clause with every offending row, the turn cap per size with its source run, the controls, trim, RSS and container sections and the pair section. It exits 0 only when the pass bar held, the escape clause did not fire, all six verdict blocks (`ksweep`, `grid`, `frontier`, `ladder`, `pair`, `container`) were read, each complete against the table above (Rules, Completeness), and the volume estimator and its gate tolerance were established. The `controls`, `trim` and `rss` runs are evidence printed beside the verdict and never inputs to it.

## Protocol inputs

Every public module-level constant of `bench.quiet`, `bench.thread_spike.maths`, `verdict`, `helical` and `measure` is in the first table as `` `quiet.NAME` ``, `` `maths.NAME` ``, `` `verdict.NAME` ``, `` `helical.NAME` `` or `` `measure.NAME` ``, with its value as a Python literal; so is the protocol-level data of the driver (`cli.NAME` is `bench.thread_spike.__main__`) and of the container runner (`runner.NAME`). `maths.PITCH` and `maths.NUT_HEIGHT` are the two tables after it. `tests/test_bench.py::test_the_protocol_pre_registers_every_constant_the_harness_uses` parses these tables and fails when a constant is missing from them or its value differs from the code's, so after PR 1 lands no constant moves without a visible new PR (D-19). The Label says what stands behind a value: INTERIM (a Phase 1 figure Phase 7 re-measures), UNVERIFIED (a stated input, the standard unread), ASSUMED (planner-set; the owner raised no objection and the research gives its basis), MEASURED-PRIOR (set from a research probe, not from a campaign run), DECISION (a CONTEXT decision, named).

| Constant | Value | Label | Source |
|---|---|---|---|
| `quiet.QUIET_BAR` | `1.5` | DECISION (D-17) | load bar, strictly under; spur D-05's convention on the same 12-core host class |
| `quiet.QUIET_SAMPLES` | `3` | DECISION (D-17) | consecutive readings under the bar |
| `quiet.QUIET_INTERVAL_S` | `30.0` | DECISION (D-17) | seconds between readings |
| `quiet.QUIET_CAP_S` | `900.0` | DECISION (D-17) | give up after this and read non-decisive |
| `maths.SIZES` | `('M2', 'M2.5', 'M3', 'M3.5', 'M4', 'M5', 'M6', 'M7', 'M8', 'M10', 'M12', 'M14', 'M16', 'M18', 'M20')` | DECISION (D-02) | the 15 sizes, in table order |
| `maths.LENGTH_CAP_DIAMETERS` | `10` | UNVERIFIED | D-03: ISO 4017 greatest standard length at most 10 d, unverified until Phase 4 |
| `maths.LENGTH_CAP_MM` | `200` | UNVERIFIED | D-03: the 200 mm cap is a preview value |
| `maths.FRONTIER_STEP_TURNS` | `5` | DECISION (D-04) | frontier step in turns |
| `maths.FRONTIER_MAX_TURNS` | `250` | DECISION (D-04) | the research's measured ceiling for sewn twist (STACK section A, 0 of 166 failures) |
| `maths.SAMPLE_SIZES` | `('M2', 'M2.5', 'M3', 'M6', 'M8', 'M10', 'M16', 'M20')` | DECISION (D-06, D-07) | the K sweep, the reference rows and the ladder; RESEARCH Open Question 7; owner ruling 1 of 2026-10-06 |
| `maths.K_CANDIDATES` | `(3, 5, 10)` | DECISION (D-07) | segment lengths in turns swept |
| `maths.VOID_CLEARANCE` | `0.2` | ASSUMED | radial mm of every grid and frontier void: the upper end of D-11's bracket; planner-set |
| `maths.RULED_MODULE` | `"cq_warehouse.thread"` | DECISION (D-06) | the reference package's module, imported by the reference worker only |
| `maths.TIP_CHAMFER_DEG` | `30.0` | UNVERIFIED | cone from the end face meeting it at the minor radius; ISO 4753 unread; cost evidence only (D-08) |
| `maths.DEPTH_FRACTIONS` | `(4, 8, 16, 32)` | ASSUMED | ladder presets h/4 to h/32 of the thread depth h = 5H/8; CONTEXT discretion |
| `maths.LADDER_ANGULAR` | `0.5` | ASSUMED | angular deflection in rad of the depth presets, as the preview preset |
| `maths.INTERIM_PRESETS` | `{'preview': (0.08, 0.5), 'fine': (0.01, 0.1)}` | INTERIM | Phase 1 D-01, carried from spur; equals `screw.solid.TESSELLATION` (a test pins it) |
| `maths.INTEGRATION_POINTS` | `400000` | ASSUMED | midpoints over one turn of the pair closed form; it matched the kernel to 1e-5 where the kernel answered (R5, R7) |
| `maths.PAIR_CLEARANCES` | `(0.05, 0.1, 0.15, 0.2)` | DECISION (D-11) | proof clearances in mm |
| `maths.DIAGNOSTIC_CLEARANCES` | `(0.0, -0.05)` | DECISION (D-11) | c = 0 reads inconclusive by definition; c = -0.05 is the sensitivity check |
| `maths.MATCHED_POSES` | `(-2.0943951023931953, 0.0, 2.0943951023931953)` | ASSUMED (-2pi/3, 0, 2pi/3) | theta in radians, the seam pose included; planner-set under D-12 |
| `maths.CONTROL_OFFSET_PITCHES` | `0.5` | DECISION (D-12) | the control slides the nut half a pitch from the matched pose |
| `maths.PAIR_REFERENCE_SIZES` | `('M2', 'M6', 'M10', 'M20')` | ASSUMED | the research's four probe sizes, which also run at the two other K values (Pitfall 8) |
| `verdict.T_PASS` | `0.0001` | ASSUMED | relative tolerance of the precise volume against the closed form; research max 7.6e-6 over 576 sewn rows (R10), the naive defect is about 0.76 (R15); D-09 |
| `verdict.ROW_TIMEOUT_S` | `120.0` | ASSUMED | four times the 30 s budget, so over budget is measured, not killed; owner ruling 3 of 2026-10-06 |
| `verdict.GZIP_TABLE_TIMEOUT_S` | `900.0` | ASSUMED | a row that asks for L19's gzip table: minutes, not seconds (RESEARCH Pitfall 6); plan 02-04 |
| `verdict.FINE_CHECK_CEILING` | `1000000` | ASSUMED | triangles above which the pure-Python STL check is skipped and counted (RESEARCH Pitfalls 5, 6) |
| `verdict.BUDGET_S` | `30.0` | INTERIM | Phase 1 D-01 `SCREW_BUILD_TIMEOUT`; over budget caps a size, never an escape (D-10) |
| `verdict.BUDGET_BYTES` | `67108864` | INTERIM | Phase 1 D-01 `SCREW_EXPORT_CACHE_MB` 64: fine raw STL plus its gzip-1 |
| `verdict.GATE_FACTOR` | `10` | ASSUMED | the shipped gate is this times the estimator's largest error, rounded up to one significant figure (D-20) |
| `verdict.ESTIMATOR_TIE` | `2.0` | ASSUMED | the estimators tie when the larger error is within this times the smaller (D-20) |
| `verdict.PROTOCOL_PATH` | `".planning/phases/02-thread-spike/02-SPIKE.md"` | DECISION (D-16, D-19) | the file the guard compares with origin/main |
| `verdict.RESULTS_HEADING` | `"## Results"` | DECISION (D-19) | the line that ends the pre-registered text |
| `verdict.SECONDS_NOT_ESTABLISHED` | `"seconds not established (non-decisive gate)"` | DECISION (D-17) | what a seconds claim reads on a non-decisive gate (owner ruling R4) |
| `verdict.PAIR_BAND` | `0.001` | ASSUMED | relative band of a control reading around the closed form: 100 times the worst agreement of a non-empty reading (1e-5, R7); D-14 |
| `verdict.EMPTY_MM3` | `1e-06` | ASSUMED | a reading is empty at 0 solids or abs(volume) at most this; the c = 0 garbage read -0.0000 in one solid (R4) |
| `verdict.PAIR_TIMEOUT_S` | `600.0` | ASSUMED | one pair cell is six booleans, a full M20 boolean took 16 to 121 s (STACK section C) |
| `helical.SECTION_SAMPLES` | `14` | MEASURED-PRIOR | spline samples per flank: 0.1 um off the ideal spiral, 4 gives 7 um (STACK) |
| `helical.MAX_SEGMENTS` | `500` | MEASURED-PRIOR | the default pipe fails from about 80 turns, 500 builds 250 turns (STACK) |
| `helical.SEWING_TOLERANCE` | `0.0001` | MEASURED-PRIOR | mm; closes the seams without a boolean (STACK); a protocol input, not a tuning knob |
| `measure.PRECISE_EPS` | `1e-06` | MEASURED-PRIOR | `BRepGProp.VolumeProperties_s` relative bound; 1e-7 cost 2x for no gain (RESEARCH Code Example 4) |
| `measure.WELD_MM` | `1e-05` | ASSUMED | STL vertices are welded to this many mm before edges are paired |
| `measure.GZIP_LEVEL` | `1` | INTERIM | the app's gzip level (spur L19); levels 6 and 9 gave 4.9 % smaller at M6 L60 |
| `cli.CAMPAIGN_BLOCKS` | `('ksweep', 'grid', 'frontier', 'ladder', 'trim', 'controls', 'rss', 'pair', 'container')` | DECISION (D-07, D-15) | the blocks in protocol order: K first, `rss` after `frontier`, `container` last |
| `cli.PASS_BLOCKS` | `('ksweep', 'grid', 'frontier', 'ladder', 'pair', 'container')` | DECISION (D-05, D-14, D-15) | the blocks a clean verdict needs; a campaign without one is never a pass |
| `cli.ONE_PIPE_TURNS` | `(100, 160, 200, 250)` | ASSUMED | one-pipe comparison turn counts; inverted solids appeared at 160 to 171 turns in the research (STACK) |
| `cli.DEFAULT_K` | `5` | ASSUMED | the research reference K, used only when no K qualifies, and labelled |
| `runner.CONTAINER_IMAGE` | `"screw:latest"` | DECISION (D-05) | the production image the container block runs in |

### PITCH

ISO 262 coarse pitch, as exact fractions in mm (`maths.PITCH`). UNVERIFIED until Phase 4's row tests (D-02); the source is a secondary one (en.wikipedia.org "ISO metric screw thread", fetched 2026-10-06).

| Size | d | P |
|---|---|---|
| M2 | 2 | 2/5 |
| M2.5 | 5/2 | 9/20 |
| M3 | 3 | 1/2 |
| M3.5 | 7/2 | 3/5 |
| M4 | 4 | 7/10 |
| M5 | 5 | 4/5 |
| M6 | 6 | 1 |
| M7 | 7 | 1 |
| M8 | 8 | 5/4 |
| M10 | 10 | 3/2 |
| M12 | 12 | 7/4 |
| M14 | 14 | 2 |
| M16 | 16 | 2 |
| M18 | 18 | 5/2 |
| M20 | 20 | 5/2 |

### NUT_HEIGHT

Nut height m in mm (`maths.NUT_HEIGHT`, owner ruling R5). m only scales the engaged length and the closed-form expectation together: a label, never a verdict input. Every entry is UNVERIFIED; the Source cell is the label recorded at the checkpoint.

| Size | m | Source |
|---|---|---|
| M2 | 1.6 | Annex A not read; memory of the withdrawn ISO 4032:2012. UNVERIFIED |
| M2.5 | 2.0 | Annex A not read; memory of the withdrawn ISO 4032:2012. UNVERIFIED |
| M3 | 2.4 | Annex A not read; memory of the withdrawn ISO 4032:2012. UNVERIFIED |
| M3.5 | 2.8 | 0.8 * d, no ISO 4032 row. UNVERIFIED |
| M4 | 3.2 | Annex A not read; memory of the withdrawn ISO 4032:2012. UNVERIFIED |
| M5 | 4.7 | m max as read from the ISO 4032:2023 preview by the research. UNVERIFIED |
| M6 | 5.2 | m max as read from the ISO 4032:2023 preview by the research. UNVERIFIED |
| M7 | 5.6 | ISO 4032:2023 added M7, no value read: 0.8 * d, a stated input. UNVERIFIED |
| M8 | 6.8 | m max as read from the ISO 4032:2023 preview by the research. UNVERIFIED |
| M10 | 8.4 | m max as read from the ISO 4032:2023 preview by the research. UNVERIFIED |
| M12 | 10.8 | m max as read from the ISO 4032:2023 preview by the research. UNVERIFIED |
| M14 | 12.8 | memory of the same table, not re-read. UNVERIFIED |
| M16 | 14.8 | m max as read from the ISO 4032:2023 preview by the research. UNVERIFIED |
| M18 | 15.8 | memory of the same table, not re-read. UNVERIFIED |
| M20 | 18.0 | m max as read from the ISO 4032:2023 preview by the research. UNVERIFIED |

## Rules

Each rule was written before any data, names the function that implements it in `bench/thread_spike/verdict.py` (or in `__main__.py`, where it says so; the rules about whole campaigns live in its `verdict_campaign`), and is pinned by tests on synthetic records. Nobody tunes any of them toward a pass (D-17).

- **A row's class (`classify_row`, D-09).** A row that is not built keeps its outcome: `failure`, `timeout` or `worker_died`, with its error. A built row is `silent_wrong` when it has not exactly one solid, is not valid, has a precise volume that misses the closed form by more than `T_PASS` (sign included, so an inverted solid reading about -1 times the closed form is wrong), or has a checked mesh that is not watertight, whose signed volume is not positive, or that misses the closed form by more than its deflection times its surface area (an inscribed mesh is a deflection-limited estimate). Anything else is `ok`. A mesh above `FINE_CHECK_CEILING` is not checked, and every skipped check is counted in the report and never read as a pass: the row's class stays as above, and `verdict_campaign` prints the count of unchecked meshes over the host grid's and the container's rows beside the pass bar, naming them unchecked.
- **The closed form (`maths.closed_volume`).** The area of the transverse section of the pinned basic profile times the length; a void's section is grown by its clearance. `classify_record` judges a rod, a void and the comparison rows against their own closed form; `classify_trim` judges a trim row on solid count, validity and a watertight preview mesh with positive signed volume only, because no closed form exists for a trimmed tip (D-08).
- **Decisiveness (owner ruling R4).** A non-decisive run's validity, solid-count, volume and pair outcomes count. Its timing claims are reported "not established" and never re-run toward a pass: the 30 s frontier stop, a seconds cap, the seconds clause of `over_budget` and the estimator tie-break by seconds. A bytes claim needs no quiet host and counts on any run. Timing claims are taken only from a decisive release.
- **The pass bar (`pass_bar`, D-05, D-09).** Over the host grid's rod and void rows and, separately, the container rows (judged as non-decisive whatever a header says): any `silent_wrong`, `failure` or `worker_died` row fails it, naming the row. A `timeout` is an over-budget cap on a decisive gate and leaves the bar held; on a non-decisive gate the row's validity is unknown, so the bar reads "not established", which is not an escape either. A failure outranks a not-established, which outranks held, across the two. Only rod and void rows are inputs: the naive control, one-pipe, ruled and trim rows are evidence beside the verdict and cannot fail a bar.
- **The escape clause for the rod (`escape_rows`, D-10).** A `failure`, `worker_died` or `silent_wrong` row, rod or void, either hand, whose length is at most min(10 d, 200 mm) in the host grid or the container rows. Beyond that length a failure is a frontier stop, and a timeout is a cap under `pass_bar`, never an escape.
- **Over budget and the cap (`over_budget`, D-10).** A row is over budget when its fine raw STL plus its gzip-1 exceed `BUDGET_BYTES` (integers: exactly 64 MiB is inside, one byte more is over), or its request seconds (build plus the slower of the fine STL and the STEP export, plus the trim on a trim row) exceed `BUDGET_S` or the row timed out. The seconds clause is a timing claim: on a non-decisive gate it reads `SECONDS_NOT_ESTABLISHED`, never "over", and so does the verdict's "first row over the seconds budget" line for a non-decisive grid, which names no row. Over budget caps a size; it is never an escape.
- **The frontier stop (`frontier_stop`, D-04).** After each step the walk stops when the rod or the void is not ok, naming which and its class; or, on a decisive gate only, when build plus the fine mesh exceed `BUDGET_S`. A non-decisive run never stops on the clock.
- **The turn caps (`turn_caps`, D-04, D-10).** Per size, three caps each with its reason, never merged: the construction cap from the frontier walk (the smaller of the two hands, each the last ok step before the stop, or the standard max when the first step stops, or 250 turns when nothing stops; not established for a timeout stop on a non-decisive gate, for an incomplete walk and for a walk with a row whose length is not its turns x P); the bytes cap from the grid (the largest length below the first over-budget row; always established); and the seconds cap from the grid, only from a decisive run. Void rows count with rod rows in both grid caps, as they do in the pass bar: a decisive void timeout holds the bar as a cap and caps the size's length (a void has no fine mesh, so only its timeout can be over). The smallest is Phase 3's cap-and-warn input.
- **The K rule (`select_k`, D-07, Pitfall 8).** Among the K that qualify (every sweep row ok at that K: no failure, no silent_wrong, every precise error inside `T_PASS`, at the standard max and at 250 turns, both hands), the fewest fine triangles summed over the standard-max rod rows, then the fewer STEP bytes, then the smaller K. None qualifying is an escape for the construction, read by `verdict_campaign` (Escape clause).
- **K consistency (`verdict_campaign`, D-07).** The locked K is derived by the verdict, never taken from a header: `select_k` over the K sweep's own record, or `DEFAULT_K` when none qualifies, as the blocks themselves lock it. Every later run (`grid`, `frontier`, `ladder`, `pair`, `container`, and the `controls`, `trim` and `rss` evidence runs) is read only when its header names that K. A run whose header names another K, or none, is reported with both and not read, and the campaign is not a clean pass (exit 1). With no complete sweep there is no K to check against: that is a missing block, and the later runs are read at the K their own headers name.
- **The estimator rule (`select_estimator`, `gate_tolerance`, D-20).** Candidates are `precise` (`BRepGProp`, eps `PRECISE_EPS`) and `stl` (the preview mesh's signed volume), compared over the ok rod rows that have a checked preview mesh by the largest absolute error against the closed form. When the larger error is within `ESTIMATOR_TIE` times the smaller they tie, and on a decisive grid run the cheaper by median seconds wins (then the smaller error); on a non-decisive grid run the break is a timing claim and is not made (owner ruling R4): the tie is not established, so the estimator and `T_gate` are not, and the campaign is not a clean pass (Required blocks). Otherwise the smaller error wins, on any gate. The default `Volume()` is a reference column, not a candidate. The shipped gate is `GATE_FACTOR` times the winner's largest error, rounded up to one significant figure by decimal arithmetic on the printed value.
- **The pair cell (`cell_verdict`, D-12, D-14, owner ruling R1).** Exactly as written, in this order: a cell that did not finish is inconclusive; a mixed-hand cell whose poses are exactly `MATCHED_POSES` and no others is `violated` when every matched pose reads non-empty, else inconclusive, and any other pose set (a stray pose, a missing one, a control) leaves it inconclusive; c at or below 0 is inconclusive by definition (D-11); poses other than `MATCHED_POSES` and their half-pitch controls leave the cell inconclusive, because no verdict is drawn from poses chosen after the fact; a nut body whose precise volume misses pi d^2 m - A(c) m by more than `T_PASS` is not believed; any non-empty matched pose is `violated`; a control whose closed form is at or below `EMPTY_MM3` cannot fire by geometry and is inconclusive; otherwise `proven` only when all 3 matched poses are empty AND all 3 controls are non-empty within `PAIR_BAND` of `closed_control`. Empty means 0 solids or abs(volume) at most `EMPTY_MM3`. The diagnostic columns (errors and warnings of the boolean) are printed and never read.
- **Falsifiability (`size_falsifiable`, `excluded_clearances`, `mixed_hand_violated`, D-14).** A size is falsifiable on one hand when some same-hand cell at c of at least 0.05 is proven; a size is not falsifiable unless both hands are. `excluded_clearances` lists the proof clearances at which some cell did not prove: the flaky cells Phase 5 must leave out. `mixed_hand_violated` is true only when a size has at least one mixed-hand cell and `cell_verdict` reads every one `violated`: it finished, it was read at exactly `MATCHED_POSES` and every matched reading is non-empty; no cell, an unfinished cell, one empty reading or a pose chosen after the fact is not a violation. `pair_escapes` (in `__main__.py`) applies both over the sizes the grid covered (all sizes when there is no grid).
- **Reported only (`sensitivity_ok`, `variant_rules`, owner ruling R1).** `sensitivity_ok`: the c = -0.05 cell's matched readings are all non-empty and within `PAIR_BAND` of the closed form of a matched pose. `variant_rules`: per same-hand proof cell, whether two of three controls fire in band, whether the rule holds with the seam pose left out, and whether the same cell's c = -0.05 reading at each matched pose, as the control, fires in band. They are computed from the same recorded readings, printed beside the verdict and never change it; they are for Phase 5's revision.
- **Container runs.** They run the locked construction over the full grid in `screw:latest`; they are never decisive (their header says so whatever the host gate read), their rows count toward the pass bar and the escape clause, and a campaign without a container run is never a pass. A container row that times out under emulation makes the container bar "not established", never "failed", and is never a reason to raise `ROW_TIMEOUT_S` (owner ruling 3).
- **Completeness (`block_gaps`, `pair_gaps`).** `verdict_campaign` reads a verdict block only when its record is complete against the Method table's row set. For `ksweep`, `grid`, `ladder` and `container`: every pre-registered row (sizes x lengths x hands x kinds, at the block's K for all but the sweep) exactly once, and nothing else. For `frontier`: per size and hand a walk of consecutive steps from the first, a rod and a void at each exactly once, at the block's K and at the step's own length (turns x P, built in exact fractions and compared with the recorded float exactly, as the harness wrote it), and no row of any other kind, ending at 250 turns or at a step `frontier_stop` ends (judged on the header's decisive flag), with no step after a stop; each gap is reported by its step, and a row whose length is not its turns x P feeds no cap. For `pair`: every cell of the table exactly once, at the header's K for the locked cells. A header that names no K cannot be held to a row set and is incomplete. An incomplete record, such as the partial JSONL a crashed run keeps, is reported by block with what it lacks and is not judged: its rows feed no pass bar, escape, cap or K, and the campaign is not a clean pass (exit 1). A pair cell that did not finish is a recorded outcome, not a gap. The `controls`, `trim` and `rss` runs are evidence and are held to no row set.
- **Required blocks (`verdict_campaign`).** A campaign is a clean pass only when the pass bar held, no escape fired, `ksweep`, `grid`, `frontier`, `ladder`, `pair` and `container` were all read, each complete, and the volume estimator and its gate tolerance `T_gate` were established; a missing block is listed and exits 1. An estimator or a `T_gate` that cannot be established (no ok rod row with a checked preview mesh to compare on, or a largest error from which no gate can be derived) is printed as "not established" with its reason and the campaign exits 1. That is a withheld pass, not an escape: no roadmap revision follows from it, and it is never re-run toward a pass (D-17).
- **Evidence rows (D-06, D-08).** The naive control is wrong on purpose: a naive row that reads ok is reported loudly as "the control did not control"; its rows with one solid, `isValid()` true and a precise volume below half the closed form are listed with their exact parameters as `known_bad_inputs` for THRD-04's positive-control test in Phase 3. The one-pipe and ruled rows are comparison rows (the ruled profile is not the pinned one, so its ratio to this closed form is not an accuracy claim). Trim rows are Phase 4 cost evidence. The `rss` figures are labelled as a fresh child's, for that row only.

## Predictions

Each prediction is the outcome expected before any run, with the research probe that is its prior evidence. The probes R1 to R16 (RESEARCH, "Research probe record") are research, not campaign runs: they carry no run id and are cited here only as prior evidence. A prediction is not a target: no input, rule or constant above was chosen to make one come true, and a prediction that fails is a result.

- **Construction.** The sewn twist passes the whole grid, both hands, rod and void, with no failure and no silent_wrong row: 576 of 576 research rows were clean with a maximum precise error of 7.6e-6 (R10), against the 1e-4 `T_PASS`.
- **K.** K = 3 is selected, if it qualifies: at M6 L60 the fine triangle counts were 604 344, 678 624 and 792 016 for K = 3, 5 and 10 (R1, R14), at the price of more STEP bytes (3.57 MB against 2.93 MB at K = 5, R14).
- **Negative control.** The naive `sweep` + `fuse` produces silent-wrong rows (one solid, valid, a precise volume of about 0.24 to 0.27 of the closed form at M6 L10 and M2 L6) and `Null TopoDS_Shape` exceptions at longer lengths (M6 L20 and L40) (R15).
- **One-pipe.** The one-pipe twist produces inverted solids above about 160 turns on some sizes (STACK section A; R15 saw them at 160 to 171 turns). The onset is expected to depend on size and turn count and is not predicted more finely.
- **Ruled-surface reference.** Its default `Volume()` reads about +6 % over the closed form (R9: +6.3 % at M6 L20); its profile is not the pinned one, so this is a cost and behaviour reference only.
- **Frontier.** The sewn twist reaches 250 turns for every size unless the 30 s stop fires first on the largest sizes (R2 and R11: an M20 L200 fine mesh took 5.4 to 12.6 s, load-dependent, and a 250-turn M20 is about three times that length).
- **Budget.** Bytes, not construction, set the caps: the fine preset's raw STL plus gzip-1 passes 64 MiB near L = 53 mm at M20 (R11, extrapolated: 0.82 MB per mm raw and a gzip-1 of about 0.46 of the raw), and stays inside it at M6 L60 (49.7 MB, R11). So a bytes cap below the standard max is expected for the large sizes while the construction holds.
- **Estimator.** `precise` (GProp, eps 1e-6) wins the estimator rule: the mesh's signed volume is deflection-limited and always low (-7e-4 to -2.9e-2 against the closed form, R1, R2), while the precise volume read within 7.6e-6 (R10). The default `Volume()` is known to read 15 to 21 % off on some constructions (D-20) and is not a candidate.
- **Pair check.** The pair rule as written is likely to read "not falsifiable" for several sizes, which fires the escape clause for Phase 5: 21 of 72 half-pitch controls read false-empty at c = 0.10 (29 %), 10 of 12 (size, K) combinations had at least one, and no K, fuzzy value or serial setting cleaned it (R7, R8). Matched poses are expected to read empty at every c > 0 (no matched pose ever read non-empty in 42 readings, R4 to R8), so the rule's weak half is the controls. The mixed-hand pair is expected to read violated (R4: non-empty at all 6 poses at M6). c = 0 is expected to give inconclusive garbage and c = -0.05 to show interference near the closed form (R4, R5).
- **Container.** `screw:latest` under linux/amd64 reads the same validity and volume outcomes as the host (R16: the same volume errors for the reference builder). Timings under emulation are expected to be several times the host's, and the largest void rows may time out at `ROW_TIMEOUT_S`, which leaves the container bar "not established" (Rules).

Disclosure of what the predictor had seen: the harness smoke checks of plans 02-02 to 02-05 (not campaign runs, never cited as evidence) read, among other things, an M6 right-hand rod at 5 turns within 1.7e-6 of the closed form; one one-pipe row at 250 turns on M6 that did not invert (ratio 0.999993); a ruled-surface row at M6 10 turns at 0.985 of the closed form; and one pair cell (M6, K = 5, c = 0.10) whose matched poses read empty, whose two non-seam controls read the closed form and whose seam control read empty. The one-pipe prediction is left as the research stated it for that reason: the campaign decides.

## Escape clause

The spike says so, in its Verdict, and the roadmap is revised before the affected phase is planned, when any of these happens:

- **Phase 3 is not planned until the roadmap is revised** when any `failure`, `worker_died` or `silent_wrong` row occurs inside the standard range (length at most min(10 d, 200 mm)), rod or void, either hand, in the host grid or in the container run. A `timeout` there is not an escape: under a decisive gate it is a cap, and under a non-decisive gate it leaves the pass bar "not established", which is reported as that and nothing more.
- **Phase 3 is not planned until the roadmap is revised** when no K qualifies under the K rule: the construction has no segment length the rule can defend.
- **Phase 5 is not planned until the roadmap is revised** (SC5) when any size is "not falsifiable" (some hand has no proven proof-clearance cell at the locked K), or when the mixed-hand pair of any size does not read violated at every matched pose.
- **An over-budget row is not an escape.** It is a per-size cap below the standard max, reported in the decision entry as Phase 3's cap-and-warn input, and so is a frontier stop beyond the standard max.

Nothing is tuned toward a pass: no constant, rule, tolerance, pose, block or sample above changes after any campaign data exists, a non-decisive run is never re-run toward a pass (D-17), and a change after landing is a new PR that visibly post-dates this protocol, which the guard refuses to run under until it lands too (D-19).

## Results

No run yet.
