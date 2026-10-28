---
phase: quick-261028-mt2
plan: 01
status: complete
subsystem: bench / phase-07 sweep protocol
tags: [G26, R3, R10, decide-walls, confirm, root-floor]
requirements: [OPER-01, OPER-02, OPER-03]
branch: gsd/phase-07-operability-re-sweep
plan_head_before: 9fa1d72
plan_head_after: b95d034
commits: 4
---

# Quick 261028-mt2: G26, the R10 root floor from the rods of group (d) only

R10 now decides `MIN_ROOT_RADIUS_MM` from the rods of group (d) only. `decide-walls` run once on the
real records exits 0 with candidate V = 0.01 mm. The nut voids are recorded as an observation and set
no number. Stopped before 07-05's confirm set: `bench/points/walls-confirm.json` does not exist.

## Commits (pushed with a plain `git push`, e80cdeb..b95d034)

| Task | sha | Subject | Files |
| --- | --- | --- | --- |
| 1 | e82d18a | docs(07): record the owner's ruling G26 and take the R10 root floor from the rods of group (d) only | 07-GAP-RULINGS.md, 07-SWEEP-PROTOCOL.md, tests/test_oper.py |
| 2 | b6e7d1f | feat(bench): decide the R10 root floor from the rods of group (d) only (07 D-18, G26) | bench/oper_sets.py, tests/test_oper_followup.py |
| 3a | 17bab4c | docs(bench): record the void observation and the candidate walls after the rods-only R10 (07 D-08, D-18, G26) | bench/RESULTS.md |
| 3b | b95d034 | docs(debt): add the void walk evidence to the countersink item and the rod floor to the root-radius item (07 G26) | the two debt items, docs/tech_debt/INDEX.md |

All four passed the `make verify` pre-commit hook (the hook line reads "make verify (ruff, mypy,
import boundaries, unfinished-work scan, pytest)...Passed"). Gates run by hand: `make test
PYTEST_ARGS="tests/test_oper.py tests/test_oper_followup.py -q -n0 --no-cov"` gave `399 passed`;
`.venv/bin/python -m bench.oper_sets --check` exit 0; `git diff --quiet 93afc81 --
bench/points/walls-voids.json bench/points/walls.json` exit 0 (both byte-identical).

## Evidence commands (Task 1 step 0), output as printed

Matched the plan's expected output exactly.

```
readings 120, ok 20, not ok 100 (['refused'])
r/d: ok min 0.1250, not ok max 0.1200
pitch/d: ok max 0.7852, not ok min 0.7667
```

```
nut void readings 390: ok 20, not ok 370 (['refused']); no countersink 0
countersink inner radius mm: ok min 0.0450, not ok max -0.0300; on the other side of 0: 0
```

## decide-walls on the real records: exit 0

Command: `.venv/bin/python -m bench.oper_sets decide-walls --walls bench/results/phase-07/walls-40646134133 --down bench/results/phase-07/walls-down-40652801529`

Stdout, verbatim (the failing lists are long; the lines up to MAX_FIELD_MM are complete, and the R9
and R10 lines are pasted in full in `bench/RESULTS.md`, `### candidate walls (before the confirm)`):

```
T = 90 turns (smallest first ok step over 60 cells)
  cell bolt-M2-right: first ok step 100
  cell nut-M2-right: first ok step 100
  cell bolt-M2-left: first ok step 210
  cell nut-M2-left: first ok step 200
  cell bolt-M2.5-right: first ok step 90
  cell bolt-M2.5-left: first ok step 180
  cell bolt-M3-right: first ok step 90
  cell nut-M3-right: first ok step 240
  cell bolt-M3-left: first ok step 160
readings T rests on: 148
bolt d: decade 1000, tested value 999.999, rests on ceiling-bolt-d-1000
bolt length: decade 10000, tested value 10000.0, rests on ceiling-bolt-length-10000, ceiling-bolt-thread-10000
bolt s: decade 1000, tested value 1000.0, rests on ceiling-bolt-s-1000, ceiling-bolt-d-1000
bolt k: decade 100000, tested value 100000.0, rests on ceiling-bolt-k-100000
bolt thread_length: decade 100000, tested value 100000.0, rests on ceiling-bolt-thread-100000
nut s: decade 1000, tested value 1000.0, rests on ceiling-nut-s-1000, nutlead-M2-s1000, nutlead-M8-s1000, nutlead-M14-s1000
nut d: decade 1000, tested value 999.699, rests on ceiling-nut-d-1000
nut m: decade 10000, tested value 10000.0, rests on ceiling-nut-m-10000
nut clearance: decade 1000, tested value 496.999, rests on ceiling-nut-clearance-1000
MAX_FIELD_MM candidate: 1000
tail (R9): V = 0.0001 mm; 48 readings read, failing: tail-d6-p1-right-1e-6, ... (24 labels, 1e-6 to 1e-9)
root (R10): V = 0.01 mm; 270 readings read, failing: root-bolt-M12-right-r0.0003, root-bolt-M6-right-r0.0001, root-bolt-M2-right-r3e-05, ... (all `root-bolt-`, 122 labels, down to r1e-06)
```

Candidates: T 90, MAX_FIELD_MM 1000, MIN_TAIL_MM (R9) V 0.0001, MIN_ROOT_RADIUS_MM (R10) V 0.01 mm
with largest failing rod `root-bolt-M12-right-r0.0003` (F = 3e-4). These match the planner's dry run.
The R3 confirm (07-05) decides them.

## The temporary confirm run (outside the repo)

Same command line as `confirm`, `--out` in a scratchpad directory: exit 0, `217 points in shards of
[30, 30, 30, 30, 29, 17, 17, 17, 17]`. Of its points, 60 start `root-`, all `root-bolt-`, at radii
0.01 and 0.003 only. `bench/points/walls-confirm.json` does not exist in the repo.

## Resume command for 07-05 Task 3 step 4 (no `--voids`; it replaces the command in the 261028-l2l SUMMARY, which no longer parses)

```
.venv/bin/python -m bench.oper_sets confirm --walls bench/results/phase-07/walls-40646134133 --down bench/results/phase-07/walls-down-40652801529 --explore bench/results/phase-07/explore-40646117094 --out bench/points/walls-confirm.json
```

07-05 Task 3 steps 4 and 5 (the confirm set, its run, the final docs commit) belong to the 07-05
executor. Step 3's heading `### candidate walls (before the confirm)` is in RESULTS.

## Debt touched (no new file filed)

- `docs/tech_debt/active/2026-10-21-nut-countersink-cutter-crosses-the-axis-at-a-coarse-pitch.md`:
  void walk evidence, the computed countersink-radius correlation (cause marked ASSUMPTION), the owner's
  trigger. INDEX row trigger now names the void root ratio r/d near or below 0.12. Severity must,
  still active.
- `docs/tech_debt/active/2026-10-11-root-radius-floor-is-not-the-kernel-boundary.md`: rod result
  (F = 3e-4, V = 1e-2). Left in `active/`; plan 07-07 resolves it with the floor.

## Flags for the orchestrator on 07-07-PLAN.md (not edited here)

- Its R10 "every cell" / "60 cells" now means the 30 rod cells (60 confirm points: 30 rods at each of
  two radii).
- Its planned `void_root_radius_refusal` floor would be the rod floor (1e-2 mm), which does not hold the
  void wall: every void reading at r <= 1e-2 mm was refused, and the wall scales with `d`. That is the
  countersink item's "before a void guard is relied on" trigger.

## Deviations from plan

1. **[Attribution] Commit trailer.** The run constraints named `Co-Authored-By: Claude Opus 5.5`; the
   harness attribution instruction for this session says `Claude Sonnet 5.5`, which is the model that
   wrote the commits. All four commits carry the Sonnet 5.5 trailer. Amend the trailers only if the
   orchestrator wants the Opus line; no history was rewritten.
2. **[Hook flake] First commit attempt of Task 1 failed.** The pre-commit `make verify` run failed
   `tests/test_pool.py::test_a_request_queued_behind_a_build_keeps_its_own_full_timeout` (1 failed, 4150
   passed) under the parallel load of the full suite. That test passed twice on its own, and the file is
   untouched by this work. The same commit message was retried and passed the hook. No `--no-verify`.
3. Minor in tests: the G26 ruling test needed a wrapped `def` (name plus signature exceeds 100 columns);
   one helper line (`gone = [label ...]`) was simplified after ruff C416.

No R-rule deviations; no auth gates; no stubs; no threat flags beyond the plan's register.

## Self-Check: PASSED

- Commits e82d18a, b6e7d1f, 17bab4c, b95d034: all ancestors of HEAD (`git rev-list --count
  9fa1d72..HEAD` = 4); pushed.
- Owner's dirty paths untouched: `git status` still shows only `.planning/state.json` (M), HANDOFF.json,
  `05-*/.continue-here.md`, `06.1-*/.gitkeep`, `ui-reviews/` and this quick directory as before.
- `bench/points/walls-confirm.json` absent; `walls-voids.json` and `walls.json` identical to 93afc81.
- SUMMARY, PLAN and STATE.md not committed; ROADMAP.md not touched.
