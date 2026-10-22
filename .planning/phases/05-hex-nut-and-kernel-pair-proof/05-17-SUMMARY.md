---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 17
subsystem: solid-mesh
tags: [frnt-06, d-21, mesh-deviation, tessellation, control-surface-deflection, owner-r6]
requires:
  - phase: 05-16
    provides: "the pre-registered runs; the bench entries this one follows"
  - phase: 02
    provides: "2026-10-08-a-ladder, the fine-STL caps' run"
provides:
  - "bench/mesh_deviation.py: the D-21 rule, ladder, metric and harness check, committed before its run"
  - "bench/RESULTS.md: ## Mesh deviation (Phase 5, D-21), 50 rows, the rule selects 0.01 mm / 0.1 rad"
  - "tests/test_mesh.py: ControlSurfaceDeflection/Relative pin, the fine bound on the shipped M6 thread export (both hands) with the preview as positive control, the fine preset pin"
  - "TESSELLATION comment citing the rule, the R6 fraction and the run; FINE_STL_ROWS comment saying the preset was kept"
affects: [05-18]
requirements-completed: [FRNT-06]
estimate_ref: "120000 tokens, 3 tasks"
actuals:
  tokens: 9700
  tasks: 3
  commits: 5
plan_head_before: b8ddceeafdd08763ebaf9f249a6007c02881f4ed
plan_head_after: 9b2b4bed3f541ee032d79019dbaa92c8cacab406
tech-stack:
  added: []
  patterns:
    - "a rule is committed with its instrument before the run; an instrument fault found by the run is amended in its own commit, with the cause, before the re-run"
key-files:
  created:
    - bench/mesh_deviation.py
    - tests/test_mesh.py
  modified:
    - bench/RESULTS.md
    - bench/thread_spike/maths.py
    - src/screw/solid/__init__.py
    - src/screw/calc/thread.py
    - tests/test_bench.py
key-decisions:
  - "The D-21 rule selects the kept 0.01 mm / 0.1 rad: worst deviation 0.0161 mm (M20, both hands) against the owner's R6 bound of 0.5 x 0.05 = 0.025 mm; TESSELLATION is unchanged and no fine-STL cap was re-derived"
  - "The harness vertex check was amended from 1e-4 to 1e-3 mm after its first run aborted on a 1.912e-04 mm model-vs-solid gap at M20; rule, ladder, fraction and bound untouched"
status: complete
---

# Phase 5 Plan 17: the fine mesh against the clearance Summary

The D-21 rule (largest ladder step whose worst radial deviation over M2, M3, M6, M10, M20, both hands, is within the owner's 0.5 x 0.05 mm) was committed with its instrument, run once, and selects the already shipped **0.01 mm / 0.1 rad**: worst row **0.0161 mm** (M20), 64 % of the **0.025 mm** bound. `TESSELLATION["fine"]` is unchanged, so every fine-STL cap, the refused-preset count and the M20 x 200 figure stand; the value now cites the rule instead of spur, and `ControlSurfaceDeflection` is pinned on.

## Task commits

| Task | Commit | Message |
| ---- | ------ | ------- |
| 1 (instrument) | c87aadf | test(bench): state the D-21 mesh deviation rule and its instrument |
| 1 (amendment) | e9698cf | test(bench): amend the D-21 vertex check after its first run aborted |
| 1 (record) | ab9a605 | test(bench): record the D-21 mesh deviation ladder |
| 2 | 99fce63 | test(solid): pin the fine STL deflection to the D-21 rule |
| 3 | 9b2b4be | docs(thread): note the fine-STL caps stand at the kept preset |

`commits: 5` is measured from the plan-start ledger (`git rev-list --count b8ddcee..HEAD` before this summary). The instrument commit is older than the record commit (acceptance criterion).

## Findings

**1. The run (Task 1).** `.venv/bin/python -m bench.mesh_deviation` on HEAD `e9698cf`, 18 CPUs arm64 64 GiB, load1 7.01 before and 6.46 after (shared host, geometry not timing), **40.7 s** wall. 50 rows (5 sizes x 2 hands x 4 ladder steps + the preview control). Worst deviation per step over the grid: 0.01 mm **0.0161**, 0.0075 mm 0.0159, 0.005 mm 0.0097 (M3 left), 0.0025 mm 0.0036. Preview (0.08, 0.5): 0.0587 to 0.1299 mm, every row over the bound (the positive control works). The rule takes the largest step, 0.01 mm.

**2. Instrument fault caught by the run, amended before the record.** The first run (HEAD `c87aadf`) aborted at M20 right-hand: the pre-registered vertex check (1e-4 mm) found a vertex **1.912e-04 mm** off `section_radius`. The gap is the same (1.92e-04) at 0.0025 mm, so it is the shipped solid's own departure from the model (order of `helical.SEWING_TOLERANCE`), not the mesh. The threshold became 1e-3 mm (540 times below a wrong-hand miss of 0.54 mm, 4 % of the bound) in `e9698cf` before the re-run, and the largest vertex gap became a table column (5.7e-05 at M2 to 1.9e-04 at M20). The rule, ladder, fraction and bound were not touched; the abort and the 40 rows it printed (equal to the record's) are in the entry.

**3. 05-RESEARCH F2 is not fully reproduced.** Triangle counts match F2 exactly. F2's sampled maxima at 0.01 mm exceed this run's every-facet maxima for M2 (0.0094 vs 0.0069), M3 (0.0141 vs 0.0102) and M10 (0.0184 vs 0.0150); M6 and M20 agree. A sample cannot beat the all-facet maximum of the same metric, so F2's probe measured something slightly different; its script is not in the repo. Cross-check of this run's metric against the kernel on M3 (12 facets): `Shape.distance` to the boundary faces is 0.498 to 0.521 of the radial gap on flank facets and 1.000 to 1.002 on crest/root, i.e. the radial gap is a conservative upper bound. The decision does not turn on it: F2's own 0.0184 mm is also under 0.025 mm.

**4. Fine preset kept, so Task 3 took the plan's no-move branch.** No `bench/fine_caps.py`, no `## Fine-STL caps at the D-21 preset` entry, no cap, count or figure changed. The `FINE_STL_ROWS` comment now says the rule kept the preset and cites the entry; `tests/test_mesh.py` pins `TESSELLATION["fine"] == (0.01, 0.1)` so a later change cannot ship without a recorded caps run (T-05-39).

## Deviations from Plan

### Interpretation

**1. R9 (`download_name`) not applied here.** `05-OWNER-READS.md` lists R9 as "Applied by plan 05-17, as plan 05-02 lists it (plan 05-18 also reads it)", and the orchestrator brief repeated it. Plan 05-17 has no task, file (`app.py`, `cli.py`) or acceptance line for it; plan 05-18 (`depends_on: [05-17]`) carries it fully (`download_name(p, fmt, quality)`, `-o <directory>`, the `wrote` line, the parity test, the idea file). It is not implemented here; the ruling's content is in 05-18, so it is applied, one plan later than the ruling line says. Surfaced for the orchestrator and the owner.

**2. Commit types.** Task 2's plan message `feat(solid): set the fine STL deflection...` became `test(solid): pin the fine STL deflection to the D-21 rule`: the value did not change, only its comment and the tests. Task 1 is three commits, not two (the amendment above).

**3. Task 2 had no RED step.** `tdd="true"`, but the value did not move, so the new tests pass at once; the comment change is the only source edit. The positive control (the preview export breaks the bound) is what keeps the test able to fail.

### Auto-fixed Issues

**1. [Rule 1 - Bug] Harness index error in my own instrument.** `_z_window` read vertex z at facet tuple indices (6, 9, 12) instead of (5, 8, 11). Caught by the kernel-free tests before the first commit; fixed before any run.

**2. [Rule 1 - Bug] Test helper name clash.** A new `_stl` in `tests/test_bench.py` redefined an existing module-level `_stl` (late binding would have broken the older tests). Caught by mypy `no-redef`; the new tests use the existing helper.

**3. [Rule 3] Vertex-check threshold** (finding 2) is a harness fix, not a rule change.

No auth gates. No Rule 4 stop: the selected deviation (0.0161 mm) is within the 0.025 mm bound and no cap or downloadable size changed.

## Measured facts

- **`make verify`** after the last commit: `3346 passed in 128.39s (0:02:08)`, coverage **97.32 %** against the 96.0 % floor, exit 0. Host load1 7.50 before and 11.20 after (shared). All five commits also passed the pre-commit `make verify`.
- Estimate was 120000 tokens at low confidence; actuals are chars/4 over `git diff b8ddcee..HEAD` (38 714 chars), which is mostly the RESULTS table and tests.

## Known Stubs

None.

## Threat Flags

None new. T-05-38 mitigated (`ControlSurfaceDeflection` and `Relative` asserted on the same constructor `exportStl` calls; the behavioural bound test has a positive control). T-05-39 mitigated by not moving the preset, and by the fine-preset pin that fails if it moves without a caps run.

## Notes for later plans

- Plan 05-18 owns `download_name` and R9; nothing here touches `app.py` or `cli.py`.
- The deviation is stated on facet centroids of 8-pitch thread rods (five sizes, both hands), not on the finished bolt or the nut; the entry says so. The shipped solid departs from `section_radius` by up to 1.9e-04 mm at M20 (0.8 % of the bound); it is recorded per row, not added.
- Debt or ideas filed: none. The pre-existing `docs/tech_debt/active/2026-10-14-nut-fine-stl-caps-unmeasured.md` was not touched (the plan does not resolve it).

## Self-Check: PASSED

- FOUND: bench/mesh_deviation.py, tests/test_mesh.py, `## Mesh deviation (Phase 5, D-21)` in bench/RESULTS.md (count 1)
- FOUND commits: c87aadf, e9698cf, ab9a605, 99fce63, 9b2b4be (each an ancestor of HEAD)
