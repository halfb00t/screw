---
phase: 01-runtime-port-and-walking-skeleton
plan: 02
subsystem: api
tags: [fastapi, pytest, testclient, httpx2, logging, decision-log, tech-debt]

requires:
  - phase: 01-runtime-port-and-walking-skeleton
    provides: "plan 01-01 routes, BuildPool with the D-16 guard, records.py vocabulary, PartInfo, dev extras"
provides:
  - "tests/test_api.py: the D-08 API contract per kind (validation, foreign fields, bound adjacency, admission control, byte cache, gzip, per-request logging)"
  - "tests/test_records.py: formatter edges, SCREW_LOG_LEVEL knob, idempotent configure, calc-package log-free scan"
  - "L09 in the decision log: registry, URL shape, hash default, PartInfo, interim-bounds policy, pool.py divergence"
  - "Interim-runtime-bounds debt item (Severity: must) enumerating 11 INTERIM knobs for the Phase 7 re-sweep"
  - "L07 extraction trigger recorded as fired by the pool.py guard"
affects: [01-03 cli, 01-04 ui, 01-05 parity test, 01-06 docker and wall, phase-7 operability re-sweep]

actuals:
  tokens: 13000
  tasks: 2
  commits: 2
plan_head_before: 5e93b59af9f71e4fb179200cefbc6486cd40ede1
plan_head_after: a47e85f722ac6b73d7cf0394ad6fa75b05d15cd5

tech-stack:
  added: []
  patterns:
    - "API tests build every query as dict[str, str | int | float | bool | None] (starlette 1.7.0 typing)"
    - "tests that assert a fresh build, a build count or a failing backend take a diameter no other test downloads, because the byte cache is shared across the pytest session"
    - "backend swap and slot saturation are small context managers (_backend, _saturated), not repeated try/finally blocks"

key-files:
  created:
    - tests/test_api.py
    - tests/test_records.py
    - docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md
  modified:
    - docs/architecture/decision_log.md
    - docs/tech_debt/active/2026-10-05-shared-infra-extraction.md
    - docs/tech_debt/INDEX.md

key-decisions:
  - "L09 logged with the owner's Phase 1 decisions D-01..D-19: registry with frozen default kind, per-kind URLs, omitted kind= hash rule, PartInfo, interim-bounds policy, pool.py divergence"
  - "L07's extraction trigger is recorded as fired; this plan does not extract, the owner decides extract-now vs fix-spur-by-hand"
  - "The gzip 'compressed' log test uses a 20 ms stand-in compressor: a skeleton cylinder gzips in under 0.5 ms, which rounds to 0 ms and looks like a cache hit"

patterns-established:
  - "Contract tests pin a status AND the body's type, not just a status range (timeout is 503 timeout, pool_broken is 503 pool_broken, build_error is 422)"
  - "Debt item rows carry the measurement and the spur source, so Phase 7 can replace each one rather than rediscover it"

requirements-completed: [FRNT-01, FRNT-03, INFR-01]

coverage:
  - id: D1
    description: "Each of d, pitch and length refuses 0, -1, inf, nan and text with a 422 whose loc is [query, field] on the info and model routes; a foreign field (m, and quality on info) is a 422 extra_forbidden naming it"
    requirement: FRNT-01
    verification:
      - kind: unit
        ref: "tests/test_api.py#test_each_field_refuses_zero_negative_infinite_nan_and_text"
        status: pass
      - kind: unit
        ref: "tests/test_api.py#test_a_foreign_field_is_a_422_naming_it"
        status: pass
    human_judgment: false
  - id: D2
    description: "The INTERIM bound is inclusive at 100000 (info and preview STL), the next float and 1e200 are 422s naming the field, and d=1e-9 is a 422 build_error rather than a served file"
    requirement: FRNT-01
    verification:
      - kind: unit
        ref: "tests/test_api.py#test_the_interim_bound_is_inclusive_and_the_next_value_is_refused"
        status: pass
      - kind: unit
        ref: "tests/test_api.py#test_a_diameter_the_kernel_cannot_build_is_a_422_build_error"
        status: pass
    human_judgment: false
  - id: D3
    description: "Kinds, schema?kind= and unknown-kind routes: /api/kinds is the frozen default plus the list, schema without kind is a 422, kind=nut is a 404, /api/nut/* is a 404"
    requirement: FRNT-03
    verification:
      - kind: unit
        ref: "tests/test_api.py#test_kinds_names_the_frozen_default"
        status: pass
      - kind: unit
        ref: "tests/test_api.py#test_schema_requires_a_kind_and_knows_only_registered_kinds"
        status: pass
      - kind: unit
        ref: "tests/test_api.py#test_an_unknown_kind_has_no_routes"
        status: pass
    human_judgment: false
  - id: D4
    description: "Admission control and failure mapping: a saturated service is a 503 busy with Retry-After 5, timeout and pool_broken are 503 with their own type, BuildError is a 422, an unclassified exception is logged and re-raised"
    requirement: FRNT-03
    verification:
      - kind: unit
        ref: "tests/test_api.py#test_a_saturated_service_refuses_instead_of_queueing"
        status: pass
      - kind: unit
        ref: "tests/test_api.py#test_a_failed_build_emits_build_failed_naming_the_class_and_the_level"
        status: pass
      - kind: unit
        ref: "tests/test_api.py#test_an_unclassified_exception_still_emits_build_failed_and_is_not_swallowed"
        status: pass
    human_judgment: false
  - id: D5
    description: "Byte cache idempotency and gzip: two identical downloads return identical bytes, the second from cache with zero duration; identity and gzip clients never get each other's bytes"
    requirement: FRNT-03
    verification:
      - kind: unit
        ref: "tests/test_api.py#test_a_second_identical_download_is_served_from_the_byte_cache"
        status: pass
      - kind: unit
        ref: "tests/test_api.py#test_a_repeat_download_is_served_from_cache_with_zero_duration_and_no_build_started"
        status: pass
    human_judgment: false
  - id: D6
    description: "Every per-request log record carries kind, slug and the non-default params; SCREW_LOG_LEVEL moves the threshold; the calc package stays log-free"
    requirement: INFR-01
    verification:
      - kind: unit
        ref: "tests/test_records.py#test_screw_log_level_moves_the_threshold"
        status: pass
      - kind: unit
        ref: "tests/test_records.py#test_calc_module_stays_log_free"
        status: pass
      - kind: unit
        ref: "tests/test_api.py#test_a_fresh_build_emits_build_started_then_export_served_with_source_built"
        status: pass
    human_judgment: false
  - id: D7
    description: "L09 and the interim-bounds debt item record the decisions and every INTERIM knob accurately, and agree with the code's INTERIM labels"
    requirement: INFR-01
    verification: []
    human_judgment: true
    rationale: "Whether the prose faithfully records the owner's decisions and the knob table is complete and correctly sourced is a judgment; the acceptance greps only prove the named strings are present"

duration: 8 min
completed: 2026-10-06
status: complete
---

# Phase 1 Plan 02: API contract tests, log vocabulary and L09 Summary

**Every D-08 route's error states and edges are pinned by 77 tests (64 API, 13 log): a 422 naming the field for each bad input and foreign field, 503 with `Retry-After` under load or on timeout, never a 500, plus L09, the Phase 7 interim-bounds debt item (11 knobs) and the recorded L07 extraction trigger.**

## Performance

- **Duration:** about 8 min of agent time (start not recorded at launch; derived from the previous plan's final commit at 04:10Z)
- **Started:** 2026-10-06T04:10:00Z (approximate)
- **Completed:** 2026-10-06T04:19:00Z
- **Tasks:** 2
- **Files modified:** 6 (3 created, 3 modified; excludes `.planning/`)

## Accomplishments

- `tests/test_api.py` (64 tests with parametrisation) pins the D-08 contract: the nine binding new tests, plus spur's admission-control, byte-cache, gzip and logging tests ported and retyped to the bolt routes. Dropped every gear-feature test and the static-file tests (plan 01-04 owns `STATIC`).
- Failure mapping is pinned by status, `type` and `Retry-After`, not a status range: `BuildError` is 422 `build_error` (WARNING), `BuildTimeout` is 503 `timeout` and `BrokenProcessPool` is 503 `pool_broken` (both ERROR, `Retry-After: 5`).
- D-14 adjacency measured through the real stack in-process: `d=100000` and `length=100000` serve 200 on info and a preview STL; `math.nextafter(100000, inf)` and `1e200` are 422s naming the field.
- `tests/test_records.py` (13 tests): formatter round trip, traceback rendering, one-line-per-record, key order, `_ms` rounding, `SCREW_LOG_LEVEL` threshold and default, idempotent `configure()`, and a calc-package scan that now covers a package and the `from screw import records` form.
- L09 appended to the decision log; the D-02 debt item lists every INTERIM knob with value, location and spur source and has its INDEX row; the shared-infra item records that the L07 trigger fired.

## Task Commits

1. **Task 1: The API contract per kind** - `4996118` (test)
2. **Task 2: Log-vocabulary tests, L09, interim-bounds debt item, L07 trigger** - `a47e85f` (docs; also carries `tests/test_records.py`)

**Plan metadata:** committed with STATE and ROADMAP after this SUMMARY (docs: complete plan).

## Files Created/Modified

- `tests/test_api.py` - API contract per kind (64 tests)
- `tests/test_records.py` - log vocabulary, formatter edges, level knob (13 tests)
- `docs/architecture/decision_log.md` - L09
- `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` - the Phase 7 knob register (Severity: must)
- `docs/tech_debt/active/2026-10-05-shared-infra-extraction.md` - L07 trigger fired, owner decides
- `docs/tech_debt/INDEX.md` - the new `must` row; the extraction row's trigger cell now reads "fired"

## Decisions Made

- L09 is logged (D-01..D-19). Its text notes that L08 (the wall of `main`) lands later in the same phase, so the gap from L07 to L09 does not read as an error.
- The extraction trigger is recorded, not acted on. Severity stays `nice`; the choice between extracting now and fixing spur by hand is the owner's (see Next Phase Readiness).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug in ported test] `duration_ms > 0` cannot hold for a skeleton-sized part**
- **Found during:** Task 1
- **Issue:** spur's `test_a_gzip_request_after_an_identity_download_emits_source_compressed` asserts `duration_ms > 0`. spur's gear meshes were megabytes; the skeleton cylinder's STL gzips in well under 0.5 ms, which `_ms` rounds to 0, indistinguishable from a cache hit. The ported test failed on its first run.
- **Fix:** monkeypatch `_gzip` with a 20 ms sleeping wrapper and assert `duration_ms >= 20`, which keeps the test's real claim (a compressed response reports measured time, not the cache's constant zero). The reason is in the docstring.
- **Files modified:** tests/test_api.py
- **Verification:** `tests/test_api.py` 64 passed; `make verify` green.
- **Committed in:** `4996118`

### Additions beyond the plan text (tests and docs only, no production change)

- `test_quality_is_a_foreign_field_on_the_info_route` is split out of `test_a_foreign_field_is_a_422_naming_it` (m on both routes there; quality on info here); the binding names are all present.
- The ported build-failed test is stronger than spur's `status in (422, 503)`: it asserts the exact status, the body `type` and `Retry-After` per exception class, which is what the "BuildTimeout maps to 503 timeout, BrokenProcessPool to 503 pool_broken" truth needs.
- `tests/test_records.py` scans every `.py` under `calc/` (the plan's wording) and its regex also catches `from screw import records` and `from . import records`; checked on eight sample lines, none a false positive.
- The debt table has an eleventh row, `_release_arenas` (`malloc_trim`): the code carries an `INTERIM` label there (spur 1578 MiB without it, 360 MiB with), so omitting it would leave an INTERIM knob unregistered. The plan's acceptance list names ten.
- `_backend` and `_saturated` context managers replace spur's repeated try/finally blocks.

---

**Total deviations:** 1 auto-fixed (Rule 1), 5 additive notes
**Impact on plan:** None changes behaviour or scope; no production file was touched, and all acceptance criteria are met as written.

## Issues Encountered

- The pre-commit hook printed "Unstaged files detected" and stashed and restored the orchestrator's `.planning/config.json`, `milestone.lock` and `state.json` around each commit; after each commit they were back untouched (`git status` shows the same three entries). This is the hook's own handling, not a `git stash` run by this plan.

## Known Stubs

None. Nothing here renders empty or placeholder data; `pitch` having no geometric effect is 01-01's recorded stub and is covered by the standing `SKELETON_WARNING`, which `test_the_default_info_document` asserts verbatim.

## Threat Flags

None. No new network endpoint, auth path or file access was added; this plan adds tests and records only.

## Self-Check: PASSED

- Files exist: `tests/test_api.py`, `tests/test_records.py`, `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md`.
- Commits are ancestors of HEAD: `4996118`, `a47e85f`; `git rev-list --count 5e93b59..HEAD` = 2, matching `actuals.commits`; `check evaluation-scope --commits-only` lists both.
- Task 1 acceptance: the nine binding test names counted 9; `dependency_overrides[build_backend]` matches; `tests/test_api.py` 64 passed.
- Task 2 acceptance: `^## L09` matches and its body contains `DEFAULT_KIND`, `/api/schema?kind=`, `kind=`, `PartInfo`, `INTERIM`, `pool.py`; `Severity: must` present; the ten-knob loop printed nothing; the INDEX row and the `L09` mention in the shared-infra item match; `SCREW_LOG_LEVEL` in `tests/test_records.py`.
- `make verify`: ruff, mypy `--strict`, `Contracts: 5 kept, 0 broken`, no-fake-done clean, `136 passed in 30.23s` (59 from 01-01, 77 here). The pre-commit hook ran the same command and passed on both task commits.
- Plan verification: `pytest tests/test_api.py tests/test_records.py` gave `77 passed`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 01-03 (CLI) can reuse the API tests' `PartInfo` shape for the parity check; 01-05's parity test cites the nine binding test names, all present.
- **Owner decision wanted:** L07's trigger fired (the `pool.py` same-slot guard must also reach spur, which still carries the race as an open `must` debt). Options: extract the shared package now, or fix spur by hand with the same guard and keep the fork. Recommendation: fix spur by hand now (one guard, one test) and defer extraction, since the guard is the only divergence so far. Filed in `docs/tech_debt/active/2026-10-05-shared-infra-extraction.md`; nothing was changed in spur.
- Plans 01-04 and 01-06 append their rows (debounce, `SCREW_WORKERS`, `mem_limit`, HEALTHCHECK, tmpfs) to `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md`.
- Items filed by this plan: `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` (new, `must`); the shared-infra item was updated, not newly filed. No blockers.

---
*Phase: 01-runtime-port-and-walking-skeleton*
*Completed: 2026-10-06*
