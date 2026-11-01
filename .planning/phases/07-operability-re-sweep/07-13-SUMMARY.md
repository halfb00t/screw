---
phase: 07-operability-re-sweep
plan: 13
subsystem: calc
tags: [cost-model, OPER-03, D-08, D-17, L21, retirement]
status: complete

requires:
  - phase: 07-operability-re-sweep
    provides: "07-11: download_refusal on the cost model alone; test_presets.py off the old rule"
  - phase: 07-operability-re-sweep
    provides: "07-12: L21, which records the retirement this plan carries out"
provides:
  - "src/screw/calc/thread.py without FINE_STL_ROWS, fine_stl_refusal, NUT_FINE_STL_RUN, NUT_FINE_STL_CLEARANCE, NUT_FINE_STL_ROWS, nut_fine_stl_refusal"
  - "src/screw/solid/__init__.py: the TESSELLATION comment cites the cost model's fit (L21, R23)"
  - "bench/end_cuts.py: RECORDED_FINE_STL_CAPS, the three caps its nut-cap probe ran with"
  - "tests/test_thread_maths.py: a static test that no retired name is left in src/"
affects: [07-14, 07-15, 07-16, 07-21]

tech-stack:
  added: []
  patterns:
    - "A bench script keeps a local copy of the shipped values its run read, naming the run, once the shipped table is retired"
    - "A test that meshes a solid build() returns meshes a copy, as _write_export does"

key-files:
  created:
    - .planning/phases/07-operability-re-sweep/07-13-SUMMARY.md
  modified:
    - src/screw/calc/thread.py
    - src/screw/solid/__init__.py
    - tests/test_thread_maths.py
    - tests/test_mesh.py
    - tests/test_solid.py
    - bench/end_cuts.py
    - docs/tech_debt/INDEX.md
    - docs/tech_debt/resolved/2026-10-14-nut-interim-bounds.md
    - docs/tech_debt/active/2026-10-21-nut-countersink-cutter-crosses-the-axis-at-a-coarse-pitch.md

key-decisions:
  - "The six retired cap names are deleted from src/; download_refusal already read the cost model alone, so no admitted or refused outcome moves"
  - "The watertight sweep picks ISO 4014 rows by download_refusal(p, \"stl\", \"fine\") is None at test time; it picks the same row as the old rule at every size and hand"

metrics:
  duration: "about 25 minutes"
  completed: 2026-10-29

estimate:
  tokens: 70000
  tasks: 2
actuals:
  tokens: 9855
  tasks: 2
  commits: 2
plan_head_before: 08a879b881bcdf7d549869eb8a679fc8fc621951
plan_head_after: 6c7f71493ac0a3637f8daefc2698ae890f6ef4f2
---

# Phase 7 Plan 13: Retire the per-row fine-STL caps Summary

The rods' `FINE_STL_ROWS` and the nut's `NUT_FINE_STL_ROWS` are gone, along with their refusals,
their clearance ceiling and their tests. The L21 cost model is now the only download rule in the
code. A static test keeps the six names out of `src/`. The nut's interim-bounds debt item is
resolved in the same commit.

## Commits

| # | Hash | Subject |
|---|------|---------|
| 1 | ee88194 | test(mesh): mesh a copy of the cached default bolt, as the export does |
| 2 | 6c7f714 | refactor(calc): retire the per-row fine-STL caps the cost model replaced (07 D-08, D-17) |

## What was done

- **`calc/thread.py`.** The six names and their comments are deleted. Two comments that listed
  "the caps" among the callers of `built_thread_length` and `MIN_TAIL_MM` now name the cost model,
  which calls `built_thread_length` in `cost._features`.
- **No outcome moved.**
  - Since 07-11, `download_refusal` reads only `cost.refusal`. Before editing, the only hits for the
    six names in `src/` were the definitions and the `TESSELLATION` comment.
  - `tests/test_calc.py` and `tests/test_presets.py` had no reader left.
- **`tests/test_thread_maths.py`.**
  - Deleted: the rod cap tests (L11 rows, grid recompute, cap boundary, hand, off-row) and the nut
    cap tests (typed table, record recompute, cap boundary, clearance ceiling, off-key).
  - Kept: the `MAX_TURNS` and root-rule tests.
  - Added `test_no_retired_cap_name_is_left_in_the_source`, which scans every `*.py` under `src/`.
  - Added `test_a_nut_above_the_retired_clearance_ceiling_is_judged_by_the_cost_model_alone`.
- **`tests/test_solid.py::_sweep_row`.**
  - It now takes the longest ISO 4014 row for which `download_refusal(p, "stl", "fine") is None`.
    The row is chosen at test time, and no literal pins it.
  - A size with no admitted row fails on an assert that names it.
  - A one-off check picked the same row length as the old `fine_stl_refusal` filter at all 15 sizes
    and both hands.
- **`tests/test_mesh.py`.** The test is renamed
  `test_the_fine_preset_is_the_one_the_cost_model_was_fitted_at`. Its docstring cites R23, L21 and
  the fit runs.
  - Those runs export through `screw.solid.export` (`bench/oper_child.py`), which reads
    `TESSELLATION`.
- **`solid/__init__.py`.** The `TESSELLATION` sentence now says the value is the one
  `2026-10-08-a-ladder` was measured at and the cost model was fitted at (L21, R23), so changing it
  needs a re-fit. The comment keeps its 12 lines, and the dict is unchanged.
- **`bench/end_cuts.py`.**
  - `RECORDED_FINE_STL_CAPS` holds the three keys `CAP_NUTS` reads: M10 right 56.0, M20 right 64.0
    and M20 left 91.0, copied from the deleted table.
  - Its comment names run `2026-10-08-a-grid` (L11) and says that L21 retired the shipped table.
  - `import bench.end_cuts` exits 0.
- **Debt.**
  - `2026-10-14-nut-interim-bounds.md` is resolved and moved to `resolved/`, and its INDEX row moved
    with it.
  - Its Resolution names L20 for the nut's `s`, `m`, `clearance` walls, the G27 `d` and
    `MAX_TURNS` 90, and L21 for the nut's cost model, the retired caps and the clearance refusal.

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 1 - Bug] The plan's own verify command failed at HEAD on a test-isolation bug**
- **Found during:** Task 1 verify (`-n0`, the four test files in that order).
- **Issue:** `tests/test_solid.py:74` failed with `assert box.zmin == pytest.approx(0.0, abs=TOL)`.
  It obtained -0.023742145378211617.
  - The test passed alone and failed in the same way at HEAD 08a879b, in a scratch worktree with
    this plan's changes absent (1 failed, 550 passed).
  - Cause: `tests/test_mesh.py::test_the_fine_mesh_keeps_the_kernels_control_surface_deflection_on_and_absolute`
    ran `BRepMesh_IncrementalMesh` on the solid `build()` caches. The triangulation stayed on that
    solid, so the next `BoundingBox()` read the mesh. That pair of tests alone fails.
  - `_write_export` already copies before `exportStl` for exactly this reason (spur L24).
- **Fix:** the test meshes `build(BoltParams()).copy().wrapped`. Because it is a separate concern,
  it was committed on its own, ahead of the retirement.
- **Files:** tests/test_mesh.py. **Commit:** ee88194.

**2. [Rule 1 - Spec] The plan's `NutParams(clearance=6.0)` does not validate**
- **Issue:** at the default `s` of 10 the model raises `nut_too_thin`: `s` must exceed
  d + 2 * clearance = 18.
- **Fix:** the test uses `NutParams(clearance=6.0, s=20.0)`. It is M6 x 1 right, one of the 30
  retired keys, and s/d 3.33 is inside the nut's s band.
  - The retired `nut_fine_stl_refusal` refused this nut for its clearance. The cost model admits it
    at every artifact (one-off check).
  - The test asserts only the plan's equality, `download_refusal(...) == cost.refusal(...)`, so an
    R12 widening cannot make it stale.
- **Commit:** 6c7f714.

**3. [Rule 1 - Pointer] A link in an active debt item that the move broke**
- **Issue:** after the `git mv`, the Related files line of
  `docs/tech_debt/active/2026-10-21-nut-countersink-cutter-crosses-the-axis-at-a-coarse-pitch.md`
  pointed at the old `active/` path.
- **Fix:** repointed to `resolved/`, with no other change. It is neither of the two items the
  orchestrator froze.
- The decision log line 1129 ("Open, filed." in an older entry) is history and stays as written.
- **Commit:** 6c7f714.

**4. [Scope note] The debt item's Next step asked for nut rows in `2026-10-05-interim-runtime-bounds.md`**
- Not added. The Resolution says why: what is left there (the build timeout, the workers, the
  memory limit) applies to every kind, and it stays open until 07-15 and 07-16. The plan's Task 2
  asks only for the resolution and the move.

### TDD evidence

- **RED:** `test_no_retired_cap_name_is_left_in_the_source` failed with 7 hits; the first was
  `screw/calc/thread.py: FINE_STL_ROWS`.
- The nut test passed at RED, because 07-11 had already moved `download_refusal` onto the cost
  model. It pins the outcome the retirement must keep, not new behavior.
- **GREEN:** the plan's verify command, `make test PYTEST_ARGS="tests/test_thread_maths.py
  tests/test_calc.py tests/test_mesh.py tests/test_solid.py -q -n0 --no-cov"`, gave
  `500 passed in 164.84s`.
- The grep for the six names over `src/` is empty, and both commits passed the pre-commit
  `make verify`.

## Requirements

OPER-03 is not ticked: the timeouts and the runner verification (07-15, 07-16) are still open.

## Known Stubs

None.

## Threat Flags

None. T-07-34 is mitigated: the names are deleted from `src/`, and a static test pins that they
are absent.

## Self-Check: PASSED

Commits ee88194 and 6c7f714 are ancestors of HEAD; the resolved debt item, `bench/end_cuts.py` and
this SUMMARY exist; the six names are absent from `src/`.
