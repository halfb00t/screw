---
phase: 04-iso-hex-bolts-and-screws
plan: 05
subsystem: api
tags: [thread-length, request-boundary, conflict-422, cli-parity, short-thread-warning, d-25, in-01]

requires:
  - phase: 04-iso-hex-bolts-and-screws
    provides: "04-04: thread_length, built_thread_length, MIN_TAIL_MM in calc/thread.py, the builder's BuildError below MIN_TAIL_MM"
provides:
  - "calc/thread.py: thread_length_conflict(length, thread_length), the one rule the API and the CLI share (D-25)"
  - "app.py: refuse_thread_length_conflict, an app-level dependency after refuse_repeated_keys; 422 type thread_length_conflict, ctx.fields [thread_length, length]"
  - "cli._params: the same rule on the explicit flags before the model; exit 2, `error: <same text>`"
  - "info document: below MIN_TAIL_MM of built thread, a warning naming thread_length and length and no turns or volume row"
  - "IN-01 debt item resolved and moved to docs/tech_debt/resolved in the fixing commit"
affects: [04-06, 04-07, 04-12 (--preset expands before the CLI check), 04-14 (L13 records the D-25 model-level acceptance)]

actuals:
  tokens: 6500
  tasks: 2
  commits: 2
plan_head_before: 81d3c8a93260b36c3ab8c95d799ddf394b883dcc
plan_head_after: 436a54757200f898cfdc178e01d1f2d05f83d44e

tech-stack:
  added: []
  patterns:
    - "Provenance (explicit vs default) is read only at the request boundary: the raw query on the API, the non-None flags on the CLI. The model never decides it (FastAPI 0.142.2 marks every field set)"
    - "One pure kernel-free rule, two callers, one parity test asserting the same words"

key-files:
  created:
    - docs/tech_debt/resolved/2026-10-11-info-document-prints-numbers-for-a-length-the-builder-refuses.md
  modified:
    - src/screw/calc/thread.py
    - src/screw/calc/__init__.py
    - src/screw/app.py
    - src/screw/cli.py
    - tests/test_thread_maths.py
    - tests/test_calc.py
    - tests/test_api.py
    - tests/test_cli.py
    - tests/test_parity.py
    - docs/tech_debt/INDEX.md

key-decisions:
  - "The conflict text prints the two numbers with repr minus a trailing .0, not :g: :g keeps 6 significant figures and would print 10.00001 as 10, giving 'thread_length 10 mm is longer than length 10 mm' (L02)"
  - "The dependency acts only on /api/bolt/ paths, so /api/schema with both keys stays a 200; the rule is keyed on bolt field names"
  - "A non-finite or non-positive value on either side gives no conflict, so the model's own 422 keeps naming the bad field"

patterns-established:
  - "A request-boundary refusal for two explicit values: one pure function in calc/thread.py, an app dependency reading request.query_params, a CLI check in _params, a parity test"

requirements-completed: [THRD-03, INFO-03]

duration: 35min
completed: 2026-10-11
status: complete
---

# Phase 4 Plan 05: thread_length conflict and short-thread warning Summary

**An explicit `thread_length` above an explicit `length` is a 422 `thread_length_conflict` on the API and exit 2 on the CLI with identical text, decided on the raw query rather than the model; a thread below 0.001 mm gets a warning and no turns or volume, which retires IN-01.**

## Performance

- **Duration:** about 35 min
- **Started:** 2026-10-11T16:10:00Z
- **Completed:** 2026-10-11T16:46:00Z
- **Tasks:** 2
- **Files modified:** 11 (10 modified, 1 moved)

## Accomplishments
- `thread_length_conflict(length, thread_length)` in `calc/thread.py`: None unless both are finite, above 0 and `thread_length > length`; the text begins `thread_length and length: ` and has no braces.
- `refuse_thread_length_conflict` runs after the duplicate-key check, reads `request.query_params`, parses with `float()` and leaves unreadable values to the query model. `?length=10&thread_length=10.0` is a 200, `10.00001` a 422, `?length=10` alone a 200 with the D-08 default warning, `?length=10&length=11&thread_length=30` the duplicate 422.
- `cli._params` applies the same rule to the explicit flags; `screw info bolt --length 10 --thread-length 30` and the export both exit 2, and the export writes no file.
- A parity test asserts the API `msg` equals the CLI `error:` text for three value pairs.
- `derive` leaves out `turns` and `volume` and warns when the built thread is below `MIN_TAIL_MM`; the boundary (exactly 0.001 mm) keeps both rows. The model route for the same part stays a 422 `build_error` naming `thread_length and length`.
- IN-01 resolved: item moved to `docs/tech_debt/resolved/`, INDEX row moved, all in the fixing commit.

## Task Commits

1. **Task 1: two explicit values in conflict are a 422 naming both** - `871eb6c` (feat)
2. **Task 2: a thread too short to build gets a warning and no numbers; IN-01 resolved** - `436a547` (fix)

**Plan metadata:** the docs commit that follows this file (docs: complete plan)

## TDD Gate Compliance

The pre-commit gate (`make verify`) rejects a failing suite, so no separate RED commit was possible (as plans 04-02 to 04-04). RED was run with `src/` returned to HEAD (per-file `git checkout --` of the three files I had edited, then the saved patch re-applied), and the failing targets recorded here. GREEN is the one commit per task. No REFACTOR commit.

**Task 1 RED** (`make test` on `tests/test_api.py tests/test_cli.py tests/test_parity.py`, src at HEAD): 6 failed on the planned assertions, all "a 200 / exit 0 where a 422 / exit 2 was expected":
- `tests/test_api.py::test_an_explicit_thread_length_above_an_explicit_length_is_a_422_naming_both[/api/bolt/info]` and `[/api/bolt/model.stl]`
- `tests/test_api.py::test_the_conflict_compares_parsed_floats` (10.00001 returned 200)
- `tests/test_cli.py::test_an_explicit_thread_length_above_an_explicit_length_exits_2_naming_both`
- `tests/test_cli.py::test_the_same_conflict_stops_an_export_before_it_writes_a_file`
- `tests/test_parity.py::test_a_thread_length_conflict_is_the_same_words_on_the_api_and_the_cli`

`tests/test_thread_maths.py` failed at collection (`ImportError: cannot import name 'thread_length_conflict'`); that is an import fault, not assertion evidence, and was not counted as RED for it. Its two new tests are covered by the same rule exercised through the API and CLI RED above. The guard tests (default 200, bad value stays a field 422, repeated key stays the duplicate 422, schema route, equal values) passed already, as intended: they pin behaviour the new dependency must not change.

**Task 2 RED** (`tests/test_calc.py tests/test_api.py`, src at HEAD): 3 failed, all on the missing short-thread warning and the `turns`/`volume` rows still present:
- `tests/test_calc.py::test_a_thread_too_short_to_build_gets_a_warning_and_no_turns_or_volume[params0-0.0005]` and `[params1-0.0005]`
- `tests/test_api.py::test_a_length_below_the_floor_is_a_warned_info_document_and_a_422_build_error`

The boundary test (exactly 0.001 mm keeps both rows) passed before and after, as a guard.

Semantic assessment: each target executed and failed on the planned behaviour (a refusal or a warning that did not exist), not on an import, fixture or syntax fault. `gsd_run check tdd-red-evidence` was not run; the plan is `type: execute` with `tdd="true"` tasks and pytest's console format is not one of the classifier's supported report formats.

**GREEN:** `871eb6c` (Task 1), `436a547` (Task 2); `make verify` green for each (1010 and 1014 passed, coverage 97.18% and 97.21%).

## Files Created/Modified
- `src/screw/calc/thread.py` - `thread_length_conflict` and the `_plain` formatter
- `src/screw/app.py` - `refuse_thread_length_conflict`, registered after `refuse_repeated_keys`; module docstring line
- `src/screw/cli.py` - the conflict check in `_params`
- `src/screw/calc/__init__.py` - `buildable` flag, short-thread warning, `turns` and `volume` skipped below `MIN_TAIL_MM`
- `tests/test_thread_maths.py`, `tests/test_api.py`, `tests/test_cli.py`, `tests/test_parity.py`, `tests/test_calc.py` - the behaviour list of both tasks
- `docs/tech_debt/resolved/2026-10-11-info-document-prints-numbers-for-a-length-the-builder-refuses.md` - IN-01, `Status: resolved`, with a Resolution section
- `docs/tech_debt/INDEX.md` - the row moved from Active to Resolved

## Decisions Made
- Values in the conflict text use `repr` with a trailing `.0` removed instead of the plan's `:g` (see Deviations).
- The dependency is limited to `/api/bolt/` paths so it cannot refuse an unrelated route such as `/api/schema`.
- `params.py` is untouched: `tests/test_params.py::test_a_thread_length_above_the_length_is_accepted_by_the_model` already asserts `BoltParams(length=10, thread_length=30)` validates (D-25).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The plan's `:g` formatting contradicts its own pinned text**
- **Found during:** Task 1 (writing the text)
- **Issue:** the plan asks for `<tl:g>` yet pins `thread_length 10.00001 mm is longer than length 10 mm`; `:g` prints 10.00001 as `10`, so the message would read "10 mm is longer than 10 mm", a misleading number (L02).
- **Fix:** `_plain(x)` = `repr(x).removesuffix(".0")`: 30.0 reads `30`, 10.00001 reads `10.00001`. Satisfies the pinned examples for both values.
- **Files modified:** `src/screw/calc/thread.py`
- **Verification:** `test_a_thread_length_above_the_length_is_a_conflict_with_the_pinned_text` and `test_the_conflict_compares_parsed_floats`
- **Committed in:** `871eb6c`

**2. [Rule 1 - Bug] An existing bound test collided with the new rule**
- **Found during:** Task 1 (full run of the four test files)
- **Issue:** `test_the_interim_bound_is_inclusive_and_the_next_value_is_refused` sent an explicit `length` at the bound with a `thread_length` one float above it and expected a field 422 on `thread_length`. With both explicit, that request is also the D-25 conflict, which is checked first, so the type and `loc` changed.
- **Fix:** the over-bound request no longer sends `length` (the default 20 mm applies), so it still tests the `thread_length` bound; the at-bound request, with `length` equal to `thread_length`, is unchanged.
- **Files modified:** `tests/test_api.py`
- **Verification:** the test passes; the at-bound 200 still proves a 250-turn 1e5 mm thread is served
- **Committed in:** `871eb6c`

**3. [Rule 2 - Missing critical] Restrict the dependency to the bolt routes**
- **Found during:** Task 1 (design)
- **Issue:** an app-level dependency also runs on `/api/schema` and `/api/kinds`; a stray `length`/`thread_length` pair there would be refused with a bolt-specific message.
- **Fix:** return unless the path starts with `/api/bolt/`; a test pins `/api/schema?kind=bolt&length=10&thread_length=30` as a 200.
- **Files modified:** `src/screw/app.py`, `tests/test_api.py`
- **Committed in:** `871eb6c`

---

**Total deviations:** 3 auto-fixed (2 bug, 1 missing critical)
**Impact on plan:** none on scope or on any pinned text; all three keep a printed number honest or an existing test truthful.

## Issues Encountered
- The plan's must-have mentions "a re-pin of the probe row plan 04-04 resolves and tags, once the conflict dependency exists". No probe row or marker referring to it exists in `tests/` or `src/` at HEAD, so there was nothing to re-pin; the behaviour it would pin (an explicit conflict is a 422, a default is built and warned) is covered by the new tests. Flagged for the verifier.
- `ruff` PT018 rejected a compound assertion in the first test draft; split into two assertions.

## Known Stubs

None.

## Threat Flags

None. The new dependency reads only the query keys `length` and `thread_length` and returns before any build; no new endpoint, file access or schema.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Ready for 04-06 (bench corpus, `bench/README.md`) and 04-07 (tables).
- Plan 04-12 expands `--preset` before `_params` reaches the conflict check, so the rule runs on merged values as the plan said.
- Plan 04-14 records the D-25 model-level acceptance in L13.
- No tech debt item filed; one item (IN-01) resolved at `docs/tech_debt/resolved/2026-10-11-info-document-prints-numbers-for-a-length-the-builder-refuses.md`.

## Self-Check: PASSED

- FOUND: src/screw/calc/thread.py (`def thread_length_conflict(`), src/screw/app.py (`def refuse_thread_length_conflict(`), src/screw/cli.py (`thread_length_conflict(`)
- FOUND: docs/tech_debt/resolved/2026-10-11-info-document-prints-numbers-for-a-length-the-builder-refuses.md with `Status: resolved`; absent from docs/tech_debt/active/
- FOUND commits: 871eb6c, 436a547 (ancestors of HEAD); commit 436a547 lists the fix, the resolved item and INDEX.md
- `make verify`: 1014 passed, coverage 97.21%

---
*Phase: 04-iso-hex-bolts-and-screws*
*Completed: 2026-10-11*
