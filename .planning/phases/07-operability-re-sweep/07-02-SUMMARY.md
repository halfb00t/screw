---
phase: 07-operability-re-sweep
plan: 02
subsystem: infra
tags: [pool, timeout, asyncio, process-pool, logging, cost-model]

requires:
  - phase: 01-walking-skeleton
    provides: BuildPool with parameter-hash affinity, the same-slot guard, records.py vocabulary
provides:
  - "queue-aware per-build deadline on BuildPool (D-14)"
  - "screw.calc.cost: Artifact, ARTIFACTS, artifact_of, BUILD_TIMEOUT_S (D-09, D-16)"
  - "records.cost_model_miss and the cost_model.miss event (D-10)"
affects: [07-08, 07-11, 07-16, 07-17]

actuals:
  tokens: 7100
  tasks: 3
  commits: 3

plan_head_before: 9acbae9ae15855691813fa978d46b20176bace4e
plan_head_after: d77c07c08b8896e354142e853cfb0253acfdc597

tech-stack:
  added: []
  patterns:
    - "per-slot pending list of timeouts on the event loop, no lock; entry freed in a finally"
    - "timeouts as a read-only code constant keyed by artifact; no environment override"

key-files:
  created:
    - src/screw/calc/cost.py
    - tests/test_cost.py
  modified:
    - src/screw/pool.py
    - src/screw/app.py
    - src/screw/records.py
    - tests/test_pool.py
    - tests/test_api.py
    - tests/test_records.py

key-decisions:
  - "The deadline is the request's own timeout plus the timeouts of the requests already submitted and not yet finished on its slot, taken at submit; deadlines on a slot are strictly increasing, so a later request never fires before the one it queues behind (D-14)"
  - "BUILD_TIMEOUT_S is a MappingProxyType in calc/cost.py, imported by app.py and passed to BuildPool by the module-level name, so an instrument can replace screw.app.BUILD_TIMEOUT_S before startup; the three values stay at the carried 30 s and stay INTERIM until 07-16"
  - "artifact_of refuses an unknown quality for STEP too, so STEP ignoring quality is a statement about the two real qualities, not a hole that accepts any string"

patterns-established:
  - "A test that needs a per-pool invariant after the lifespan has deleted app.state.pool records the pools as they are built (autouse fixture patching screw.app.BuildPool)"

requirements-completed: [OPER-01]

coverage:
  - id: D1
    description: "A request queued behind a build on the same slot keeps its own full timeout; with nothing ahead the deadline is its own timeout"
    requirement: OPER-01
    verification:
      - kind: integration
        ref: "tests/test_pool.py#test_a_request_queued_behind_a_build_keeps_its_own_full_timeout"
        status: pass
      - kind: integration
        ref: "tests/test_pool.py#test_a_request_with_nothing_ahead_times_out_at_its_own_timeout"
        status: pass
    human_judgment: false
  - id: D2
    description: "Every pending entry is freed on success, timeout and broken pool; the same-slot guard still holds under queue-aware deadlines"
    requirement: OPER-01
    verification:
      - kind: integration
        ref: "tests/test_pool.py#_no_pending_entry_outlives_a_test (autouse, every test in the file)"
        status: pass
      - kind: integration
        ref: "tests/test_pool.py#test_a_timeout_on_an_already_replaced_slot_ends_as_build_timeout"
        status: pass
      - kind: integration
        ref: "tests/test_pool.py#test_four_same_slot_requests_all_refuse_without_cancellation"
        status: pass
    human_judgment: false
  - id: D3
    description: "One timeout per artifact (stl-preview, stl-fine, step) from code constants, with no environment override"
    requirement: OPER-01
    verification:
      - kind: unit
        ref: "tests/test_cost.py"
        status: pass
      - kind: integration
        ref: "tests/test_pool.py#test_export_looks_its_timeout_up_by_artifact"
        status: pass
      - kind: unit
        ref: "tests/test_pool.py#test_no_build_timeout_is_read_from_the_environment"
        status: pass
    human_judgment: false
  - id: D4
    description: "A timed-out admitted part reaches the client as today's 503 timeout and leaves one cost_model.miss ERROR record; nothing is cached"
    requirement: OPER-01
    verification:
      - kind: integration
        ref: "tests/test_api.py#test_a_timed_out_admitted_part_is_logged_as_a_cost_model_miss_and_never_cached"
        status: pass
      - kind: integration
        ref: "tests/test_api.py#test_a_failure_other_than_a_timeout_is_not_a_cost_model_miss"
        status: pass
      - kind: unit
        ref: "tests/test_records.py#test_cost_model_miss_round_trips_through_json_loads_with_no_traceback"
        status: pass
    human_judgment: false

duration: 19min
completed: 2026-10-26
status: complete
---

# Phase 7 Plan 02: Queue-aware per-artifact build timeout Summary

**BuildPool deadline that adds the timeouts ahead of it on the slot, a per-artifact timeout table in `calc/cost.py` with no environment override, and a `cost_model.miss` ERROR record when an admitted part still times out.**

## Performance

- **Duration:** 19 min
- **Started:** 2026-10-26T15:56:20Z
- **Completed:** 2026-10-26T16:15:18Z
- **Tasks:** 3
- **Files modified:** 8 (2 created, 6 modified)

## Accomplishments

- The per-build clock no longer counts queue wait (D-14). Two same-slot requests that each build 0.6 s under a 1.0 s timeout both return (second wall about 1.2 s); with nothing ahead, a 5 s build under 0.2 s still raises `BuildTimeout` in under 1 s. RED was measured on the old code before the change: the second request raised `BuildTimeout` at 1.0 s wall, 0.4 s into its own build.
- One timeout per artifact (D-09): `artifact_of(fmt, quality)` maps to `stl-preview`, `stl-fine` or `step`; `BuildPool(workers, timeout)` keeps its two parameters, `timeout` is now the table, `export` looks the seconds up. `SCREW_BUILD_TIMEOUT` is gone from `src/` (D-16); the three values stay at the carried 30 s with the INTERIM label naming spur as the origin. This plan sets no figure.
- A `BuildTimeout` still maps to 503 `timeout` with `Retry-After: 5`, and now also emits one `cost_model.miss` record at ERROR (part fields, fmt, quality, artifact, `timeout_s`, no traceback) right after `build.failed` (D-10).

## Task Commits

1. **Task 1: Tracer, queued request keeps its own full timeout (D-14)** - `f1c1fb3` (feat)
2. **Task 2: One timeout per artifact, code constants, no env override (D-09, D-16)** - `918efa2` (feat)
3. **Task 3: Timed-out admitted part logged as a cost-model miss (D-10)** - `d77c07c` (feat)

**Plan metadata:** the docs commit that carries this file.

## Tracer gate

Interactive, `end-of-phase`, the tracer's `<verify>` is `<automated>` only: re-ran `make test PYTEST_ARGS="tests/test_pool.py -q -n0 --no-cov"` after Task 1, 20 passed; expanded.

## TDD

Each task ran RED against the pre-change code and landed as one `feat` commit. The pre-commit hook runs the full `make verify`, which cannot take a failing suite, so no separate `test(...)` commit exists (same constraint as Phase 2, which committed RED as strict-xfail; here the plan specifies one commit per task and each commit carries both the test and the change).

- **RED 1 (semantic):** a throwaway script drove two same-slot requests at 0.6 s each with a 1.0 s timeout on the old code: results `[b'', BuildTimeout('Build exceeded the 1.0s per-build timeout...')]` at 1.0 s wall. That is the planned assertion failing for the planned reason. The mutation check that the same-slot guard test has teeth: with the guard disabled the new `test_a_timeout_on_an_already_replaced_slot_ends_as_build_timeout` fails; restored afterwards.
- **RED 2:** against a stub `calc/cost.py` (empty `ARTIFACTS`, `artifact_of` returning `"step"`): 9 failed on the planned assertions (`artifact_of` mapping, `ARTIFACTS` value, the export lookup, the source scan finding `SCREW_BUILD_TIMEOUT` in `app.py`).
- **RED 3:** 3 `test_api` cases failed on `len(misses) == 1` (0 records) and the records round trip failed with `AttributeError` (the helper did not exist yet). The records case is a missing-name failure rather than an assertion on output; the three API cases carry the behaviour.
- `gsd_run check tdd-red-evidence` was not run: the evidence is pytest console output, not one of its supported report formats, and no `tdd_mode` gate is configured for this phase.

## Files Created/Modified

- `src/screw/calc/cost.py` - `Artifact`, `ARTIFACTS`, `artifact_of`, `BUILD_TIMEOUT_S` (kernel-free, logger-free)
- `src/screw/pool.py` - `_pending` per-slot lists, `_run_with_timeout(p, timeout, func, ...)`, per-artifact lookup in `export`
- `src/screw/app.py` - lifespan passes `BUILD_TIMEOUT_S`; `_serve` calls `cost_model_miss` in the BuildTimeout branch
- `src/screw/records.py` - `cost_model_miss`
- `tests/test_cost.py` - `artifact_of`, `ARTIFACTS`, `BUILD_TIMEOUT_S` coverage
- `tests/test_pool.py` - explicit `timeout` argument everywhere (no `pool.timeout =` left), autouse empty-pending check, adjacency, empty and already-replaced-slot tests, export lookup, no-env source scan
- `tests/test_api.py`, `tests/test_records.py` - miss record cases

## Decisions Made

See `key-decisions`. One note on the incident test: under D-14 the ten one-tick requests at 0.2 s get deadlines 0.2, 0.4 ... 2.0 s, so the first timeout replaces the slot and the other nine surface as `BrokenProcessPool`. Measured: `Counter({'BrokenProcessPool': 9, 'BuildTimeout': 1})`, pending lists empty. The test's three assertions are unchanged; its docstring says so.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] mypy no-implicit-reexport on `app.BUILD_TIMEOUT_S`**
- **Found during:** Task 2
- **Issue:** the plan's test reads `app.BUILD_TIMEOUT_S is cost.BUILD_TIMEOUT_S`; app.py imports the name rather than defining it, so mypy `--strict` refuses the attribute read.
- **Fix:** the test reads `vars(app_module)["BUILD_TIMEOUT_S"]`; the Task 3 test imports the constant from `screw.calc.cost` (the same object). No `as`-alias re-export added to app.py.
- **Files modified:** tests/test_pool.py, tests/test_api.py
- **Committed in:** 918efa2, d77c07c

**2. [Rule 1 - Bug in own test] orphaned parametrize decorator**
- **Found during:** Task 3
- **Issue:** inserting the new tests put them between an existing `@pytest.mark.parametrize` and its function; collection failed.
- **Fix:** the decorator moved back onto its function before anything was committed.
- **Committed in:** d77c07c

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 own-test slip). **Impact on plan:** none on scope or behaviour.

## Issues Encountered

- Commit `d77c07c` body says "emits cost.model.miss"; the event is `cost_model.miss` (the code and subject are right). Not amended: the hook is a 3-4 minute full `make verify` and the subject line is the acceptance string.
- `bench/build_time.py` still reads `int_env("SCREW_BUILD_TIMEOUT", 30)`, and the Makefile `bench.build` help and `bench/README.md` still name it. Out of this plan's files; plan 07-17 Task 3 owns removing it ("`SCREW_BUILD_TIMEOUT` is gone from bench/, the Makefile help and bench/README.md"). Until then the bench default of 30 equals the new constant, so nothing diverges. No debt item filed (07-17 names it).
- Two docs name the variable as a runtime knob (`docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md`, `docs/tech_debt/active/2026-10-14-nut-interim-bounds.md`); 07-17 closes "the three debt items", so they were left alone.

## Known Stubs

None.

## Threat Flags

None. `cost_model.miss` is the T-07-06 surface the plan's threat model already covers (no traceback field, tested); `_pending` is T-07-05 (freed in a `finally`, asserted empty after every test in the file).

## User Setup Required

None - no external service configuration required.

## Verification

- `make verify` after Task 3 (`d77c07c`): ruff, mypy `--strict`, import-linter (10 contracts kept), unfinished-work scan, pytest: `3749 passed in 204.71s (0:03:24)`. The same command passed in the pre-commit hook of each of the three commits.
- `grep -rn SCREW_BUILD_TIMEOUT src/` prints nothing.

## Next Phase Readiness

- 07-16 can replace the three `30.0` values in `calc/cost.py` with measured ones and cite the run; 07-08 can replace `screw.app.BUILD_TIMEOUT_S` before startup; 07-11 adds the cost model beside the timeouts in `calc/cost.py`; 07-17 records the divergence from spur (second after the same-slot guard) and removes the last `SCREW_BUILD_TIMEOUT` readers from `bench/`.
- Nothing blocks the next plan.

## Self-Check: PASSED

---
*Phase: 07-operability-re-sweep*
*Completed: 2026-10-26*
