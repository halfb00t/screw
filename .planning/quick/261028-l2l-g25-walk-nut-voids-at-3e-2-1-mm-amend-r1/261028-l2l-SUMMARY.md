---
phase: quick-261028-l2l
plan: 01
subsystem: bench / phase 7 sweep protocol
tags: [phase-07, R10, G25, void-walk, owner-stop]
status: checkpoint
requirements: [OPER-01, OPER-02, OPER-03]
commits: 4
plan_head_before: daeafeb18e5f5c818e3d6f0e6c51d95b279f9d68
plan_head_after: e80cdeb0ececd2359dc0647cf960236e9bf55e34
actuals:
  tasks: 3
  commits: 4
---

# Quick 261028-l2l: G25 void walk, amended R10 (R10 owner stop after the walk)

G25 is recorded, R3, R4 (d), R6 and R10 are amended, the 120-point void walk was generated, read once
on the runner and committed, and the amended R10 then **stops again (exit 3)**: nut voids still fail
at 1 mm for M10 to M20. Per G25 the walk is not extended. The phase is at an owner decision.

## Commits (branch `gsd/phase-07-operability-re-sweep`, pushed, no force)

| # | sha | subject |
|---|-----|---------|
| 1 | `59017dc60fba435b3121acdc333e94641936d0c8` | docs(07): record the owner's ruling G25 and walk the nut voids up to 1 mm in R3, R4, R6 and R10 |
| 2 | `93afc8129dd6a28ca6fcdd84f8cc7a35d962e0ed` | feat(bench): the R10 void walk set and the amended root-radius decision (07 D-18, G25) |
| 3 | `e6cab31af06077372a47e7dd6d52b504eb8ee631` | docs(bench): record the R10 void walk run 40665307964 (07 D-18, G25) |
| 4 | `e80cdeb0ececd2359dc0647cf960236e9bf55e34` | docs(bench): record the R10 stop after the void walk (07 D-18, G25) |

Every commit passed the `make verify` pre-commit hook. The first attempt of commit 1 and the first
attempt of commit 2 failed the hook (ruff E501 on a comment line; mypy `object` indexing in a new
test) and were fixed before the commit landed, so there is no failed or amended commit.

## Task A: the rule and the set

- `07-GAP-RULINGS.md`: section `## Gap G25 (owner ruling after the first runner reading, 2026-10-28)`
  names walls run 40646134133, says it is an owner ruling after R30's freeze and not a harness fix.
  "Harness fixes" still reads "None yet."
- `07-SWEEP-PROTOCOL.md`: R3 (two places), R4 (d), R6, R10 (two paragraphs) amended in the protocol's
  own voice. No gap label and no run id; 30 rules once each; the header sha list, the R4 table and
  R30 are untouched.
- `bench/oper_sets.py`: `VOID_RADII`, shared `_void_cell` (walls group (d) and the void walk use one
  nut constructor, so `walls.json` is byte-identical), `_void_walk_set`, `void_walk_points`,
  `build_void_walk`, the void walk prepended to `_root_walk`, `decide_walls(..., voids_readings)`
  with one R10 index (a label read in both record sets is a stop), `_confirm_set` copying void-walk
  points verbatim, `build_confirm(..., voids_dir, ...)`, `GENERATED` and `_regenerate` for
  `walls-voids`, the `void-walk` subcommand, `--voids` required on `decide-walls` and `confirm`.
- `bench/points/walls-voids.json`: written only by `python -m bench.oper_sets void-walk --explore
  bench/results/phase-07/explore-40646117094 --out bench/points/walls-voids.json`. 120 points, 0
  dropped, 1 R6 shard `[120]`, pitches 0.2771281292110204 to 18.69691111743684 mm. `--check` exits 0.
- Tests: 3 protocol key-phrase tests and 4 void-walk shape/commit tests in `tests/test_oper.py`; in
  `tests/test_oper_followup.py` the old "outside the walk" test became Case 6, plus Cases 1 to 5, the
  missing/killed/read-twice stops, the confirm at V inside the void walk, and the `void-walk`,
  `--voids`, decide-walls and `--check` command tests. `tests/test_oper.py` plus
  `tests/test_oper_followup.py`: 400 passed. The blob-sha, thirty-rules and protocol-table tests pass.

## Task B: the run

- Run id: **40665307964**, https://github.com/halfb00t/screw/actions/runs/40665307964
- Dispatched sha: `93afc8129dd6a28ca6fcdd84f8cc7a35d962e0ed` (the commit that added `walls-voids.json`;
  the record header `GITHUB_SHA` equals it). 1 shard, 1 artifact, 120 readings, 1 job on AMD EPYC
  7763.
- Records: `bench/results/phase-07/walls-voids-40665307964/`, committed as downloaded.
- Counts by status: **refused: 100, ok: 20**.

| r mm | readings by status |
|---|---|
| 1 | ok: 18, refused: 12 (M10, M12, M14, M16, M18, M20, both hands) |
| 0.3 | ok: 2 (M2 both hands), refused: 28 |
| 0.1 | refused: 30 |
| 0.03 | refused: 30 |

All 100 refusals: `Geometry kernel failed (StdFail_NotDone); check d, pitch, le`.

## Task C: `decide-walls` over walls + walls-down + walls-voids

Command:

```
.venv/bin/python -m bench.oper_sets decide-walls --walls bench/results/phase-07/walls-40646134133 --down bench/results/phase-07/walls-down-40652801529 --voids bench/results/phase-07/walls-voids-40665307964
```

Exit code: **3** (R10 stop). Stdout: empty. Stderr verbatim:

```
oper_sets: stop (R10): the largest failing value is 1, so V is 10, which lies outside the walk (it holds at most 1)
```

Recorded in `bench/RESULTS.md` under `### D-08 stop at R10 after the void walk (owner decision
pending)` with the status table by kind and radius. No candidate walls were recorded, and
`bench/points/walls-confirm.json` was not written. No further walk is proposed (G25 forbids extending
it) and no value was chosen.

## Resume command for 07-05 step 4

There is none yet: the exit was 3, not 0. 07-05 Task 3 steps 4 and 5 must not resume until the owner
rules on this second R10 stop. If the owner's ruling later yields an R10 number, the step-4 command
takes `--voids`:

```
.venv/bin/python -m bench.oper_sets confirm --walls bench/results/phase-07/walls-40646134133 --down bench/results/phase-07/walls-down-40652801529 --voids bench/results/phase-07/walls-voids-40665307964 --explore bench/results/phase-07/explore-40646117094 --out bench/points/walls-confirm.json
```

## Deviations from Plan

None. The plan executed as written. Note: the plain `git push` before the dispatch also pushed the two
earlier local commits `d4233bc` and `daeafeb` (the remote was at `4dd60e1`); a normal push, no force.

## Known Stubs

None.

## Threat Flags

None.

## Debt and ideas filed

No `docs/tech_debt/` or `docs/ideas/` item was filed.

## Owner paths

`.planning/state.json`, `.planning/HANDOFF.json`, `.planning/ui-reviews/`,
`.planning/phases/05-*/.continue-here.md` and `.planning/phases/06.1-*/.gitkeep` are untouched and in
no commit. `.planning/STATE.md`, this SUMMARY and the PLAN are not committed (left to the orchestrator).

## Self-Check: PASSED

- `bench/points/walls-voids.json`, `bench/results/phase-07/walls-voids-40665307964/`: found.
- Commits `59017dc`, `93afc81`, `e6cab31`, `e80cdeb`: ancestors of HEAD.
- `bench/points/walls-confirm.json`: absent, as required.
