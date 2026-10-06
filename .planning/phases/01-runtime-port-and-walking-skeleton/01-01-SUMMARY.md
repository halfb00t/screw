---
phase: 01-runtime-port-and-walking-skeleton
plan: 01
subsystem: api
tags: [fastapi, pydantic, cadquery, processpool, import-linter, pytest, httpx2]

requires:
  - phase: none
    provides: first phase of the milestone; spur's runtime is ported from ../spur (L07)
provides:
  - "Registered bolt model (BoltParams, KINDS, DEFAULT_KIND) with d=6.0 / pitch=1.0 / length=20.0 frozen defaults"
  - "Kernel-free info document (calc.derive, PartInfo, SKELETON_WARNING)"
  - "Kernel doorway (solid.build / export / clear_cache) building the unthreaded cylinder"
  - "BuildPool with timeout-terminate-replace and the D-16 same-slot guard"
  - "HTTP API: /api/health, /api/kinds, /api/schema?kind=, /api/bolt/info, /api/bolt/model.{stl,step}"
  - "docker/smoke.py raw-ASGI end-to-end driver; import-linter contracts 1, 2, 4, 5, 8"
affects: [01-02 api tests, 01-03 cli, 01-04 ui, 01-07 docker, phase-3 threads, phase-7 operational sweep]

actuals:
  tokens: 28500
  tasks: 3
  commits: 4
plan_head_before: e56d5a7d77353d6da458d1a64fcfeb62122380e5
plan_head_after: e1861ab5a8e07f4faed99a71e73cc58a3b7cf705

tech-stack:
  added: [httpx2 2.13.1, pytest-xdist 3.8.0, pytest-cov 7.1.0]
  patterns:
    - "per-kind Query model over one _serve(); strip() back to the plain parameter class so caches key on one type"
    - "kernel reached only inside spawned workers via importlib; contracts 5 and 8 enforce it"
    - "every ported spur runtime figure sits under an INTERIM comment naming its spur source"

key-files:
  created:
    - src/screw/params.py
    - src/screw/calc/__init__.py
    - src/screw/solid/__init__.py
    - src/screw/solid/bolt.py
    - src/screw/build_errors.py
    - src/screw/records.py
    - src/screw/pool.py
    - src/screw/app.py
    - docker/smoke.py
    - tests/test_params.py
    - tests/test_calc.py
    - tests/test_solid.py
    - tests/test_pool.py
    - tests/conftest.py
  modified:
    - src/screw/__init__.py
    - pyproject.toml
    - Makefile
    - requirements.txt
  deleted:
    - tests/test_smoke.py

key-decisions:
  - "Owner approved httpx2 2.13.1, pytest-xdist 3.8.0 and pytest-cov 7.1.0 on 2026-10-06 at the blocking legitimacy checkpoint; installed only after that"
  - "D-16 same-slot guard raises BuildTimeout (not a new type) when the slot was already replaced: the worker is already dead, so there is nothing left to terminate"
  - "derive() and solid._build dispatch with isinstance and raise TypeError for an unregistered kind, instead of match + assert_never; the registry test enforces the closed list"
  - "INTERIM_MAX_MM = 1e5 mm measured at its worst corner (d=1e5, length=1e5) before being pinned"

patterns-established:
  - "Task commit hook runs make verify; a RED commit is carried past it as a strict xfail that the GREEN commit must remove"
  - "Ported comments keep the incident and the measurement and drop spur's planning ids"

requirements-completed: [FRNT-01, FRNT-03, INFR-01, INFR-02]

coverage:
  - id: D1
    description: "The default skeleton bolt is served as STL, STEP and an info document by the real API through a spawned worker"
    requirement: FRNT-03
    verification:
      - kind: integration
        ref: ".venv/bin/python docker/smoke.py"
        status: pass
      - kind: integration
        ref: "tests/test_pool.py#test_a_real_worker_builds_and_downloads"
        status: pass
    human_judgment: false
  - id: D2
    description: "Parameter validation refuses 0, negative, inf, nan, values above the INTERIM bound and foreign fields, each naming the field; defaults frozen"
    requirement: FRNT-01
    verification:
      - kind: unit
        ref: "tests/test_params.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "Info document carries d, pitch, length and a closed-form volume, always with the walking-skeleton warning, never a non-finite number"
    requirement: FRNT-01
    verification:
      - kind: unit
        ref: "tests/test_calc.py"
        status: pass
    human_judgment: false
  - id: D4
    description: "Import-linter contracts 1, 2, 4, 5, 8 hold: calc and params are kernel-free, calc is logger-free, app reaches the kernel by no path, only solid imports cadquery"
    requirement: INFR-02
    verification:
      - kind: other
        ref: "make lint-imports (Contracts: 5 kept, 0 broken)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Pool port plus the D-16 same-slot guard: ten same-slot timeouts end as BuildTimeout or BrokenProcessPool, never AttributeError"
    requirement: INFR-01
    verification:
      - kind: unit
        ref: "tests/test_pool.py#test_two_same_slot_timeouts_in_one_incident_end_as_build_timeout_not_attribute_error"
        status: pass
    human_judgment: false
  - id: D6
    description: "Every carried spur runtime figure is labelled INTERIM with its spur source and 'Phase 7 re-sweeps (OPER-02)'"
    requirement: INFR-01
    verification: []
    human_judgment: true
    rationale: "Wording and honesty of a comment is a judgment; the grep in the acceptance criteria only proves the word INTERIM is present"
  - id: D7
    description: "Three dev packages vetted by the owner before install"
    verification: []
    human_judgment: true
    rationale: "Package legitimacy is a human decision by design (blocking-human gate); recorded here with the date, not machine-checkable"

duration: 17 min
completed: 2026-10-06
status: complete
---

# Phase 1 Plan 01: Walking-skeleton tracer Summary

**Walking-skeleton bolt served as STL, STEP and an info document by spur's ported runtime (registry, per-kind Query models, spawned worker pool), with the kernel confined to `screw.solid` by five KEPT import contracts and a same-slot timeout guard that spur still carries as open debt.**

## Performance

- **Duration:** 17 min of agent time (wall clock includes the owner's package-vetting wait)
- **Started:** 2026-10-06T03:51:14Z
- **Completed:** 2026-10-06T04:08:15Z
- **Tasks:** 3 (1 tracer, 1 human-verify checkpoint, 1 TDD)
- **Files modified:** 19 (14 created, 4 modified, 1 deleted; counts exclude `.planning/`)

## Accomplishments

- One real request path through every layer: `/api/bolt/model.stl` through `app` -> `BuildPool` -> a spawned worker -> `solid` -> `cq.Solid.makeCylinder`, proven end to end by `docker/smoke.py` driving the ASGI app through its lifespan.
- Validation at the model boundary only: `allow_inf_nan=False` plus `gt=0` refuses `inf`/`nan`/0/negative, `le=INTERIM_MAX_MM` refuses above 1e5 mm naming the field, `extra="forbid"` turns a foreign query field into a 422. Defaults are absolute millimetres (6.0 / 1.0 / 20.0) and `DEFAULT_KIND` is the literal `"bolt"`.
- `calc.derive` returns d, pitch, length and a closed-form volume with the standing "walking skeleton: plain unthreaded cylinder, not a product build" warning; volume is omitted with a warning rather than printed non-finite. No thread or turn count anywhere.
- Contracts 1, 2, 4, 5, 8 all KEPT (`Contracts: 5 kept, 0 broken`); the INFR-02 negative control proved they bite.
- Dev packages vetted and approved by the owner, then pinned; pool tests ported against `BoltParams`; the D-16 guard landed test-first.

## Task Commits

1. **Task 1: End-to-end skeleton bolt over the API (tracer)** - `3b6d220` (feat)
2. **Task 2: Owner vets httpx2, pytest-xdist and pytest-cov** - no commit (checkpoint, verification only). Owner replied `approved` on 2026-10-06 for all three: httpx2 2.13.1, pytest-xdist 3.8.0, pytest-cov 7.1.0.
3. **Task 3: Dev extras pinned, pool tests ported, D-16 guard** (TDD)
   - infrastructure: `73a0d13` (chore) - extras, `make lock`, `tests/conftest.py`, ported `tests/test_pool.py`
   - RED: `0de63f8` (test) - regression test, committed as strict xfail
   - GREEN: `e1861ab` (fix) - the guard, xfail marker removed

**Plan metadata:** committed with this SUMMARY (docs: complete plan).

## TDD Gate Compliance

The plan is `type: execute` with one `tdd="true"` task, so the plan-level gate is advisory; the sequence was followed anyway: `test(01-01)` `0de63f8` precedes `fix(01-01)` `e1861ab`.

- **RED:** `test_two_same_slot_timeouts_in_one_incident_end_as_build_timeout_not_attribute_error` run unmarked against the unguarded pool: failed 6 of 6 runs on the planned assertion (`not [r for r in results if isinstance(r, AttributeError)]`), with `AttributeError("'NoneType' object has no attribute 'values'")` in the result list alongside one `BuildTimeout`. Exactly the mechanism the plan named (CPython 3.12 sets `_processes = None` on shutdown). No import, fixture or collection fault.
  - `semanticAssessment`: the target test executed and failed on the planned assertion for the intended reason.
  - `gsd_run check tdd-red-evidence` was not run: pytest's plain output is not one of the classifier's supported report formats and the gate is advisory on an `execute` plan. The evidence above is from the real command output, not a fabricated record.
- **GREEN:** guard added as the first statement of `_run_with_timeout`'s `except TimeoutError:`; the test passes 5 of 5 runs and `tests/test_pool.py` passes 17/17.
- **REFACTOR:** none needed.

## Files Created/Modified

- `src/screw/params.py` - `FastenerParams`, `BoltParams`, `KINDS`, `DEFAULT_KIND`, `INTERIM_MAX_MM` (corner measured and recorded in its comment)
- `src/screw/calc/__init__.py` - kernel-free `derive`, `PartInfo`, `InfoRow`, `SKELETON_WARNING`
- `src/screw/solid/__init__.py`, `solid/bolt.py` - the kernel doorway and the cylinder
- `src/screw/build_errors.py`, `records.py` - failure types and the JSON-lines log vocabulary (`kind` in every per-request record)
- `src/screw/pool.py` - `BuildPool`; now carries the D-16 same-slot guard
- `src/screw/app.py` - routes, caches, admission queue, error mapping
- `docker/smoke.py` - end-to-end driver
- `tests/test_params.py`, `test_calc.py`, `test_solid.py`, `test_pool.py`, `conftest.py` - 59 tests
- `pyproject.toml`, `Makefile`, `requirements.txt` - contracts, typecheck scope, approved dev extras and the regenerated lock

## Decisions Made

- The owner approved the three flagged dev packages on 2026-10-06; nothing installed before that.
- The D-16 guard raises `BuildTimeout` with the same message rather than a new exception: the first request already killed the worker, and the client-facing outcome (503 `timeout`) is the truthful one.
- `derive` and `solid._build` dispatch by `isinstance` and raise `TypeError` for an unregistered kind (design deviation from RESEARCH Pattern 3, flagged in the plan); the registry test that builds and derives every `KINDS` entry enforces the closed list.
- D-14 corner measured on macOS arm64 (load 3.73 2.89 3.37, `/usr/bin/time -l`), cylinder d=1e5 length=1e5: preview STL 0.107 s / 550 MiB / 9,932 triangles; fine STL 0.934 s / 1,052 MiB / 28,096 triangles; STEP 0.017 s / 451 MiB. Well under the 30 s and 2 GiB stop lines. Recorded in the `INTERIM_MAX_MM` comment.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Absolute imports inside `calc/` and `solid/`**
- **Found during:** Task 1
- **Issue:** ruff TID252 forbids parent-relative imports, which the ported layout would have used.
- **Fix:** absolute `screw.*` imports in the two packages.
- **Verification:** `make verify`.
- **Committed in:** `3b6d220`

**2. [Rule 3 - Blocking] Contract 2 sources are `screw.calc` and `screw.params` only**
- **Found during:** Task 1
- **Issue:** `screw.cli` does not exist yet; a contract naming it is an import-linter error.
- **Fix:** left as the plan itself states (plan 01-03 adds `screw.cli`); noted in the contract comment.
- **Committed in:** `3b6d220`

**3. [Rule 3 - Blocking] Starlette TestClient check by source reading**
- **Found during:** Task 2 (pre-checkpoint)
- **Issue:** the planned check `import starlette.testclient` raises `RuntimeError: The starlette.testclient module requires the httpx2 package to be installed.` while httpx2 is deliberately not installed.
- **Fix:** read `starlette/testclient.py` source instead (`'httpx2' in source` is `True`), which is what the check was meant to prove.

**4. [Process] RED commit carried as a strict xfail; RED and GREEN are separate commits**
- **Found during:** Task 3
- **Issue:** the pre-commit hook runs the whole suite and `--no-verify` is not allowed, so a bare failing test cannot be committed. The plan's done-text also says "guard and its test landed in one commit", while the resume instructions require RED then GREEN.
- **Fix:** RED recorded from an unmarked run (6/6), committed with `@pytest.mark.xfail(raises=AssertionError)` (`xfail_strict` is on, so the marker cannot silently outlive the fix); GREEN removes it. RED/GREEN as two commits follows the TDD order the owner's dispatch required.
- **Committed in:** `0de63f8`, `e1861ab`

**5. [Rule 3 - Blocking] Dev-extras pin split into its own commit**
- **Found during:** Task 3
- **Issue:** the RED test needs `httpx2` (TestClient) and the ported pool tests, which are not RED material.
- **Fix:** `73a0d13` carries extras, lock, `conftest.py` and the ported tests (16 passing), so the RED commit is the regression test alone.

**6. [Observation] `make lock` also bumped two unrelated pins**
- `aiohttp` 3.14.3 -> 3.14.4 and `filelock` 4.0.11 -> 4.0.12: `make lock` resolves unconstrained by design (L06). The three approved packages resolved at exactly the approved versions (httpx2 2.13.1, pytest-xdist 3.8.0, pytest-cov 7.1.0); new transitive pins: `httpcore2` 2.13.1, `truststore` 0.10.4, `coverage` 7.16.2, `execnet` 2.1.2.

**7. [Observation] INFR-02 negative control broke three contracts, not two**
- Adding `import cadquery` to `src/screw/calc/__init__.py` made `make lint-imports` report contracts 2, 5 and 8 BROKEN (2 kept, 3 broken). The plan expected 2 and 8; contract 5 breaks too because `screw.app` imports `screw.calc` and contract 5 forbids indirect paths, which is correct behaviour. After the revert: `Contracts: 5 kept, 0 broken`.

**8. [Process] Ported comments drop spur's planning ids**
- spur's `D-xx`/`L-xx`/`CR-01` identifiers would collide with screw's own decision ids; incident descriptions, measurements and mechanisms were kept. Stale-identifier scan `! grep -rnE 'GearParams|SPUR_|spur\.model'` clean.

---

**Total deviations:** 5 auto-fixed or process (3 Rule 3, 2 process), 3 observations
**Impact on plan:** None changes behaviour or scope; all acceptance criteria met as written.

## Issues Encountered

- None blocking. The same-slot race reproduced on the first run, as spur's debt file predicted.

## Known Stubs

- `pitch` has no effect on the solid (the skeleton builds a plain cylinder, D-04). Intentional, stated in the field's help text and the standing warning; threads arrive in Phase 3 and later. Not a data-wiring gap.

## Self-Check: PASSED

- Files exist: all 14 created paths above found; `tests/test_smoke.py` absent.
- Commits are ancestors of HEAD: `3b6d220`, `73a0d13`, `0de63f8`, `e1861ab`; `git rev-list --count e56d5a7..HEAD` = 4, matching `actuals.commits`.
- `make verify`: 59 passed, `Contracts: 5 kept, 0 broken` (ruff, mypy `--strict` over `src tests docker`, no-fake-done all clean; the pre-commit hook ran the same command and passed on each of the four task commits).
- `.venv/bin/python docker/smoke.py` printed `smoke: kernel, exports, ASGI stack and validation all live`.
- Task 3 acceptance: 3 extras lines in `pyproject.toml`; 3 pinned lines in `requirements.txt`; regression test name present; `is not executor` appears at `pool.py` lines 120 (`recreate_for`) and 189 (D-16 guard).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 01-02 can pin the routes, error mapping and `strip` behaviour in API tests; `httpx2`, `pytest-xdist` and `pytest-cov` are installed, but `-n` and a coverage floor are not wired into `addopts` yet (not part of this plan).
- The D-02 interim-bounds debt item (`docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md`) is outside this plan's file list and belongs to a later plan. No debt or idea item was filed by this plan.
- No blockers.

---
*Phase: 01-runtime-port-and-walking-skeleton*
*Completed: 2026-10-06*
