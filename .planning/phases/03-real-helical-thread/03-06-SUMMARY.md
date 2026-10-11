---
phase: 03-real-helical-thread
plan: 06
subsystem: testing
tags: [thread-spike, import-back, pytest-marker, github-actions, grid, import-linter]

requires:
  - phase: 03-real-helical-thread
    provides: "plan 03-01's screw.calc.thread oracle, screw.solid.helical builder, screw.solid.check_solid and precise_volume"
provides:
  - "bench/thread_spike imports the shipped maths, builder and estimator back from src/ (one copy of each)"
  - "tests/test_grid.py: the 02 D-03 corpus (7160 rows, 60 cells) through helical.thread and check_solid, marked grid"
  - "make grid [SIZE=...] and .github/workflows/grid.yml: the slow tier, dispatch + weekly schedule, never required"
  - "bench/RESULTS.md: the M3.5 and M4 local shards, every row ok"
affects: [03-07, phase-04, phase-05, phase-07]

actuals:
  tokens: 8500
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "re-export with `from x import name as name` (mypy no_implicit_reexport) so bench modules keep the registered constants reachable"
    - "slow tier = pytest marker deselected by addopts `-m 'not grid'`, selected by a later `-m grid`; governance tests read the workflow YAML as text"
    - "a size shard is `-k 'M6-'`, safe because the cell ids are `<size>-<hand>-<kind>` (pinned by a test)"

key-files:
  created:
    - tests/test_grid.py
    - .github/workflows/grid.yml
    - docs/tech_debt/active/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md
  modified:
    - bench/thread_spike/maths.py
    - bench/thread_spike/helical.py
    - bench/thread_spike/measure.py
    - bench/thread_spike/worker.py
    - bench/thread_spike/pair.py
    - tests/test_bench.py
    - pyproject.toml
    - Makefile
    - scripts/pr_land.py
    - bench/RESULTS.md
    - docs/tech_debt/INDEX.md

key-decisions:
  - "worker._build passes request['length'] (the exact float(Fraction) the grid computed) to the shipped builder, not request['turns']"
  - "pair._span(pitch, m) returns the m + 2P span in mm from exact decimals and replaces _turns; the rod piece and the nut void are built over that length"
  - "The grid test counts a row as built when helical.thread returns, then runs check_solid and the end-face check; every exception is that row's finding, listed with the rest, never skipped"

patterns-established:
  - "Workflow governance is tested by reading the YAML as text (no new dependency): triggers, permissions, matrix == maths.SIZES, absence from ci.yml and required-jobs.txt"

requirements-completed: [THRD-01, THRD-04]

coverage:
  - id: D1
    description: "The spike imports the moved maths, builder and estimator back from src/; the pre-registered protocol still matches the code and check-protocol holds"
    requirement: THRD-04
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_the_spike_imports_the_shipped_builder_oracle_and_estimator_back"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_the_protocol_pre_registers_every_constant_the_harness_uses"
        status: pass
      - kind: integration
        ref: ".venv/bin/python -m bench.thread_spike check-protocol (protocol guard: held, run on the committed tree)"
        status: pass
      - kind: integration
        ref: ".venv/bin/python -m bench.thread_spike smoke; smoke --pair (exit 0)"
        status: pass
    human_judgment: false
  - id: D2
    description: "The full measured grid runs through helical.thread and check_solid in a slow tier: 60 cells collected by -m grid, deselected by make verify, selected per size by make grid SIZE="
    requirement: THRD-04
    verification:
      - kind: unit
        ref: "tests/test_grid.py#test_a_size_selects_exactly_its_four_cells_by_id"
        status: pass
      - kind: unit
        ref: "tests/test_grid.py#test_the_grid_is_the_measured_7160_row_corpus"
        status: pass
      - kind: integration
        ref: "make grid SIZE=M3.5 (4 passed, 131.89 s); make grid SIZE=M4 (4 passed, 148.15 s)"
        status: pass
    human_judgment: false
  - id: D3
    description: "grid.yml is dispatch + schedule only, contents: read, one job per size, and neither ci.yml nor required-jobs.txt nor pr_land.py knows it"
    requirement: THRD-04
    verification:
      - kind: unit
        ref: "tests/test_grid.py#test_the_grid_workflow_has_no_pull_request_or_push_trigger_and_reads_only"
        status: pass
      - kind: unit
        ref: "tests/test_grid.py#test_the_grid_workflow_matrix_is_exactly_the_measured_sizes_in_order"
        status: pass
      - kind: unit
        ref: "tests/test_grid.py#test_the_grid_tier_is_not_a_required_job"
        status: pass
    human_judgment: false
  - id: D4
    description: "The first grid run on a GitHub runner (wall time, whether the shards fit the 120 min timeout) is not yet known"
    verification: []
    human_judgment: true
    rationale: "Runner sizing is UNVERIFIED (A2, A3): it is measured by the first workflow_dispatch after merge, which only the owner can trigger, and is recorded in bench/RESULTS.md then"

duration: 21min
completed: 2026-10-10
status: complete
commits: 3
plan_head_before: 85b08ee65446f0e2699d6d9ccd2e7db78da7a295
plan_head_after: 3bb80d3117d543a3c787bcfc72cda9be9cd1acb9
---

# Phase 3 Plan 06: Import-back and the slow grid tier Summary

**The thread spike now measures the builder, oracle and estimator that ship (imported back from src/), and the full 7160-row measured grid runs through the THRD-04 gate in its own `grid.yml` workflow and `make grid`, outside `make verify` and the required jobs; the M3.5 and M4 shards passed every row locally.**

## Performance

- **Duration:** about 21 min (start not recorded at execution; estimated from the first command)
- **Started:** about 2026-10-10T16:15Z
- **Completed:** 2026-10-10T16:37Z
- **Tasks:** 2
- **Files modified:** 14 (3 created, 11 modified)

## Accomplishments

- `bench.thread_spike.helical.thread is screw.solid.helical.thread`, `maths.closed_volume is screw.calc.thread.closed_volume`, `measure.precise_volume is screw.solid.precise_volume`, `measure.PRECISE_EPS == 1e-6` (one test pins all four). `naive_sweep_fuse`, `one_pipe`, `trim_tip` and `ruled_reference` stay in bench. About 190 lines of duplicate code left the spike.
- The pre-registered protocol is untouched: `git diff origin/main -- 02-SPIKE.md` is empty, `test_the_protocol_pre_registers_every_constant_the_harness_uses` passes, and `check-protocol` reads `protocol guard: held` on the committed tree. Import-linter stays `7 kept, 0 broken` (the oracle module reaches no kernel by any path).
- `pytest -m grid --collect-only` collects 60 cells (`60/66 tests collected (6 deselected)`); `-k 'M3-'`, `-k 'M2-'` select exactly four cells each (no `M3.5-`/`M12-` aliasing). The 7160-row count is asserted in `make verify`.
- `make grid SIZE=M3.5`: 4 passed, 328 rows, 131.89 s. `make grid SIZE=M4`: 4 passed, 368 rows, 148.15 s. Both recorded in `bench/RESULTS.md` (host, load before and after, command, rows, wall) as a harness check of the slow tier, not a bound; macOS arm64, not linux/amd64.

## Task Commits

1. **Task 1: The spike imports the shipped maths, builder and estimator back from src/** - `08776d3` (refactor)
2. **Task 2: The full measured grid runs through the gate in a slow tier** - `2b08ff0` (test)
3. **Debt: the serial-run segfault of the in-process pair tests** - `3bb80d3` (docs)

**Plan metadata:** committed with this SUMMARY (docs: complete plan)

## Files Created/Modified

- `bench/thread_spike/maths.py`, `helical.py`, `measure.py` - the moved names re-exported with `as` aliases; docstrings say where the code moved
- `bench/thread_spike/worker.py` - the rod/void/trim branch passes `request["length"]`
- `bench/thread_spike/pair.py` - `_span(pitch, m)` replaces `_turns`
- `tests/test_bench.py` - the real-rod test passes `turns * pitch`; `_span` pinned; the identity test
- `tests/test_grid.py` - the grid-marked corpus test and the unmarked id, count, marker and workflow governance tests
- `pyproject.toml` - `grid` marker and `-m 'not grid'` in `addopts`
- `Makefile` - `SIZE ?=`, `grid` in `.PHONY`, `make grid`
- `.github/workflows/grid.yml` - `workflow_dispatch` + weekly cron, `contents: read`, matrix over the 15 sizes, `timeout-minutes: 120`, `fail-fast: false`
- `scripts/pr_land.py` - the comment above `WORKFLOW = "ci.yml"` (the constant is unchanged)
- `bench/RESULTS.md` - `## Thread grid tier (Phase 3)`

## Decisions Made

- The grid test is one test per cell (60), each looping over that cell's lengths, so a failing row is listed with size, hand, kind, length and the error, and a shard is four tests over four workers.
- `grid.yml` writes the matrix as a one-line flow list so the governance test can compare it with `maths.SIZES` by regex, with no YAML dependency.
- The tracer-style RED for Task 2 could not be committed alone (the hook runs the suite); see TDD below.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Verify command 1 of Task 1 exits non-zero on a green run; filed, not fixed**
- **Found during:** Task 1
- **Issue:** `make test PYTEST_ARGS="tests/test_bench.py -q -n0 --no-cov"` prints `449 passed` and then the process dies with exit 139. The same happens on a `git archive` copy of `85b08ee` (before this plan), and `-k "common or pair or place or nut or rod_piece"` reproduces it alone, so it is the in-process pair-boolean teardown segfault that `pair.py` already documents (RESEARCH Pitfall 4), not the import-back. `make verify` (`-n 8`) exits 0.
- **Fix:** none to the code (out of scope: not caused by this task). The 449 passed lines and the clean `make verify` are the evidence; the item is `docs/tech_debt/active/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md` (must), INDEX row added in `3bb80d3`.
- **Files modified:** docs/tech_debt/active/..., docs/tech_debt/INDEX.md
- **Committed in:** 3bb80d3

**2. [Rule 1 - Bug] Two lint failures in the first draft of tests/test_grid.py**
- **Found during:** Task 2 (first `make verify`)
- **Issue:** ruff I001 (import order) and PT018 (two compound asserts).
- **Fix:** sorted the imports, split the asserts; the `grid` text check in ci.yml became one `"grid" not in ci`.
- **Committed in:** 2b08ff0

---

**Total deviations:** 2 auto-fixed (1 blocking-but-out-of-scope and filed, 1 bug). **Impact on plan:** none on behaviour or scope.

## TDD Gate Compliance

Task 2 is `tdd="true"`. RED could not be committed alone because the pre-commit hook runs the whole suite. It was shown instead by copying the new `tests/test_grid.py` into a `git archive` copy of `HEAD` before the change and running it there: `ERROR collecting tests/test_grid.py - Failed: 'grid' not found in markers configuration option` (`1 error in 1.32s`), i.e. none of the tests can run without the marker, the workflow and the Makefile target. GREEN: the six unmarked tests pass in `make verify` (`843 passed`, 837 before) and the 60 grid cells passed for M3.5 and M4. REFACTOR: none. `gsd_run check tdd-red-evidence` was not run.

## Issues Encountered

- `smoke --pair` exits 0 with no traceback but its cell verdict is `inconclusive` (`control at theta +0.0000 reads empty`), the false-empty boolean reading Phase 2 recorded for many cells in `bench/RESULTS.md` (Pitfall 3/4). The plan's check is the exit status and the absence of a traceback; I did not compare it with a pre-change run.
- `check-protocol` and `smoke` refuse or note an uncommitted harness tree, so `check-protocol` was run after the Task 1 commit (`protocol guard: held`), not before it. It was not bypassed.
- `pyproject.toml` changed, so `make` re-created `.venv` (the stamp rule); no dependency changed.

## Verification

- `make verify` (before the Task 2 commit, and again in its hook): ruff `All checks passed!`; mypy `Success: no issues found in 47 source files`; import-linter `Contracts: 7 kept, 0 broken`; pytest `============================= 843 passed in 36.51s =============================`, coverage `97.02%` against the 94 floor. No grid cell ran in it.
- `make test PYTEST_ARGS="tests/test_grid.py tests/test_pr_land.py -q -n0 --no-cov"`: `64 passed, 60 deselected`.
- `.venv/bin/python -m pytest -m grid --collect-only -q -p no:cacheprovider tests/test_grid.py | tail -1`: `60/66 tests collected (6 deselected)`.
- `make grid SIZE=M3.5`: `4 passed in 131.89s`; `make grid SIZE=M4`: `4 passed in 148.15s`.
- Acceptance greps: no `pull_request`/`push` key in grid.yml; `required-jobs.txt` identical to `origin/main`'s; no `grid` in ci.yml; `-m 'not grid'` in pyproject.toml; `02-SPIKE.md` identical to `origin/main`'s.

## Debt

- Filed: `docs/tech_debt/active/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md` (must; INDEX row added).
- Resolved: none.

## Known Stubs

None.

## Threat Flags

None. The new surface is `grid.yml`, the plan's T-3-14 (read-only token, no PR trigger, no secrets; pinned by `test_the_grid_workflow_has_no_pull_request_or_push_trigger_and_reads_only`) and T-3-15 (`WORKFLOW = "ci.yml"` unchanged, required-jobs.txt unchanged).

## Next Phase Readiness

- Plan 03-07 (records) can cite `make grid`, `grid.yml` and the RESULTS.md section; the coverage floor re-measure it lists still stands (total reads 97.02 % here).
- Open for the owner: the first `workflow_dispatch` of `grid.yml` after merge measures the GitHub-runner wall time per size (UNVERIFIED A2/A3; the 120 min timeout and the 15 shards are the plan's guess) and its result goes into `bench/RESULTS.md`. The weekly schedule may be disabled after 60 days without activity (A4, assumption).

## Self-Check: PASSED

Created files exist (`tests/test_grid.py`, `.github/workflows/grid.yml`, the debt item); commits `08776d3`, `2b08ff0` and `3bb80d3` are ancestors of HEAD.

---
*Phase: 03-real-helical-thread*
*Completed: 2026-10-10*
