---
phase: 04-iso-hex-bolts-and-screws
plan: 08
subsystem: calc
tags: [calc, presets, designation, info-document, openapi, import-contracts, sys-modules-control]

requires:
  - phase: 04-iso-hex-bolts-and-screws
    provides: "04-05: the info document's rows and the short-thread no-number rule; 04-07: screw.tables catalogue(), expand(), PresetRow.designation, contracts 6 and 7, the sys.modules probe"
provides:
  - "src/screw/calc/presets.py: match(p) (exact float equality over every row field, first in catalogue order) and designation_for(p, row) (the row's designation, None for a left-hand part)"
  - "screw.calc.PresetMatch (status exact|custom, id, display) and PartInfo.designation / PartInfo.preset, both required nullable keys, on /api/bolt/info and screw info bolt"
  - "tests/test_params.py::test_the_frozen_defaults_are_the_iso_4017_m6_x_20_row, closing 01 D-05's ASSUMPTION"
  - "tests/test_import_boundaries.py: the derive converse (derive(BoltParams()) loads screw.tables) and the screw.calc-alone case (does not)"
affects: [04-13 (the page composes its match badge from preset and designation), 04-09 (new rows are matched automatically; no calc change needed)]

actuals:
  tokens: 4072
  tasks: 1
  commits: 1
plan_head_before: cb0201080a3ef2c65ef5948f9e94d42da9b53b88
plan_head_after: 4ce2438bc3d71878b791fa9bcaed06bc5b83a858

tech-stack:
  added: []
  patterns:
    - "calc/presets.py is the only calc module that imports screw.tables, and _bolt imports it inside the function, so importing screw.calc.thread (which runs calc/__init__.py) never loads a table"
    - "A required nullable key in the published info document: null means 'no row' or 'no standard form', never an invented value"

key-files:
  created:
    - src/screw/calc/presets.py
  modified:
    - src/screw/calc/__init__.py
    - src/screw/params.py
    - tests/test_calc.py
    - tests/test_api.py
    - tests/test_params.py
    - tests/test_import_boundaries.py
    - docs/architecture/overview.md

key-decisions:
  - "A left-hand part still matches its row (left_hand is not a row field) but its designation is null: Clause 7 gives no left-hand form (04-OWNER-READS.md), so it is withheld, not invented"
  - "match() is exact float equality with no tolerance and no nearest row; a part one field off a row is custom (D-09, L02)"
  - "The converse import test also pins that import screw.calc alone loads no table, so a top-of-module import in calc/__init__.py fails a test, not only the grep criterion"

patterns-established:
  - "Import-boundary tests come in pairs: the part that must not load a table, and the call that must"

requirements-completed: [TABL-06, TABL-07, TYPE-01]

duration: about 15 min
completed: 2026-10-11
status: complete
---

# Phase 4 Plan 08: The info document reports the matching ISO row and its designation Summary

**The empty link's info document now says it matches ISO 4017 M6 x 20 with the designation `Hexagon head screw ISO 4017 - M6 x 20` (no property class), any part off a row reads custom with a null designation, and a link still rebuilds without loading a table.**

## Performance

- **Duration:** about 15 min
- **Completed:** 2026-10-11
- **Tasks:** 1
- **Files modified:** 8 (1 created, 7 modified)

## Accomplishments

- `derive(BoltParams()).preset == PresetMatch(status="exact", id="iso4017:M6x20", display="ISO 4017 M6 × 20")` with the designation in the owner's Clause 7 form; the API and the CLI print the same document (`screw info bolt` checked).
- `derive(BoltParams(d=8.0, pitch=1.25, s=13.0, k=5.3))` reads `custom`, id and display null, designation null; each of s, k, pitch, thread_length and length moved off the M6 x 20 row alone also reads custom (no nearest-row guess).
- The frozen defaults equal `expand("iso4017:M6x20")`, asserted by a named test that `params.py` now cites in place of the 01 D-05 assumption comment.
- Contract 6's runtime property holds and is proved both ways: `BoltParams()`, `import screw.solid` and `import screw.calc` leave `screw.tables` out of `sys.modules`; `derive(BoltParams())` puts it in.
- The OpenAPI `PartInfo` has required keys `{kind, rows, warnings, designation, preset}` and a `PresetMatch` component with `{status, id, display}`.

## Task Commits

1. **Task 1: The info document reports the exact match and the designation** - `4ce2438` (feat)

**Plan metadata:** the docs commit following this summary.

## Files Created/Modified

- `src/screw/calc/presets.py` - `match` and `designation_for`; the only calc module importing `screw.tables`.
- `src/screw/calc/__init__.py` - `PresetMatch`; `PartInfo.designation` / `.preset`; `_bolt` imports `screw.calc.presets` inside the function.
- `src/screw/params.py` - the D-05 assumption comment replaced by one citing the row test; the frozen rule (L02) kept.
- `tests/test_calc.py`, `tests/test_api.py`, `tests/test_params.py`, `tests/test_import_boundaries.py` - the behaviours above.
- `docs/architecture/overview.md` - the `calc` row names `calc/presets.py` and why `_bolt` imports it lazily.

## Decisions Made

- Left-hand designation is null (the owner's `none` ruling); the match itself is unaffected by hand.
- Exact equality only; the catalogue order decides which row wins if two rows ever share every field (none do today).
- `PartInfo.preset` is typed `PresetMatch | None` as the plan says, but `_bolt` always sets it; `None` is reserved for a future kind without a catalogue.

## TDD Gate Compliance

The pre-commit gate (`make verify`) rejects a failing suite, so no separate RED commit was possible (as plans 04-02 to 04-07). RED was run on the working tree with the tests written and no implementation: `pytest tests/test_api.py tests/test_params.py tests/test_import_boundaries.py -n0 --no-cov`: 4 failed, 201 passed. The 4 failures, all assertion or key failures on the planned behaviour:

- `tests/test_api.py::test_openapi_documents_the_typed_contracts` (`{'kind', 'rows', 'warnings'}` where `designation` and `preset` were expected)
- `tests/test_api.py::test_the_default_info_document` (`KeyError: 'preset'`)
- `tests/test_api.py::test_a_part_matching_no_row_is_custom_on_the_wire` (`KeyError: 'preset'`)
- `tests/test_import_boundaries.py::test_deriving_the_info_document_loads_the_tables_it_matches_against` (`derive` printed `False` for `'screw.tables' in sys.modules`)

`tests/test_calc.py` failed at collection (`ImportError: cannot import name 'PresetMatch'`): an import failure, not an assertion, so it is not counted as RED evidence for its own cases; those are covered by the same behaviour seen through the API tests above and passed once the implementation landed. `tests/test_params.py::test_the_frozen_defaults_are_the_iso_4017_m6_x_20_row` passed at RED by design: the M6 x 20 row already shipped in 04-07 and equals the defaults, so it is a guard that closes the assumption, not a driver of new code.

Semantic assessment: each counted failure executed and failed on the planned behaviour (a missing key, a table not loaded), not on a syntax or fixture fault. `gsd_run check tdd-red-evidence` was not run: the plan is `type: execute` with a `tdd="true"` task and pytest's console format is not a supported classifier report format (as in 04-05 and 04-07).

**GREEN:** `4ce2438`; `make verify` green (ruff, mypy --strict, 9 contracts kept, unfinished-work scan, 1073 passed, coverage 97.52%, floor 96.0%). The pre-commit hook ran the same gate on the commit. No REFACTOR commit.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] ruff and mypy fixes inside the new tests**
- **Found during:** Task 1 (first `make verify`)
- **Issue:** `assert a is not None and ...` tripped PT018; `BoltParams(**dict[str, float])` tripped mypy's `arg-type`; the module docstring line was 101 chars.
- **Fix:** split the assertions, built the part with `BoltParams.model_validate(...)`, shortened the docstring.
- **Files modified:** tests/test_calc.py, src/screw/calc/presets.py
- **Verification:** `make verify` green.
- **Committed in:** 4ce2438

### Additions beyond the plan's list

- `docs/architecture/overview.md` was edited (one sentence in the `calc` row) so the system map names the new module and the lazy import; the plan's `files_modified` did not list it. CLAUDE.md keeps that map as the reference for the module layout.
- An extra import-boundary case (`import screw.calc` alone loads no table) and a few extra `test_calc.py` cases (each field off the row, another catalogue length, every row matches itself) beyond the behaviour list.

---

**Total deviations:** 1 auto-fixed (1 blocking lint/type fix in new tests), 2 small additions.
**Impact on plan:** None on behaviour; no scope creep into `src/screw/tables/`.

## Issues Encountered

None beyond the lint and type fixes above.

## Known Stubs

None.

## Threat Flags

None. T-04-25 is mitigated: the only import of `screw.calc.presets` is inside `_bolt` (`grep -nE '^from screw\.calc\.presets' src/screw/calc/__init__.py` prints nothing), and the `derive` converse plus the `import screw.calc` case sit beside the `BoltParams()` case.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 04-09 can add the other sizes and the ISO 4014 rows; `match` reads whatever `catalogue()` returns, with no calc change.
- Plan 04-13 can render the badge and the designation from `preset` and `designation`.
- Filed no tech-debt or idea item.

## Self-Check: PASSED

- `src/screw/calc/presets.py` exists; `4ce2438` is an ancestor of HEAD.
- Acceptance criteria re-run: `class PresetMatch` present; no module-top `from screw.calc.presets`; `def test_the_frozen_defaults_are_the_iso_4017_m6_x_20_row(` present; the import-boundary test calls `derive(` in the subprocess; `grep -c 'ASSUMPTION (D-05)' src/screw/params.py` prints 0; `make verify` exits 0; `make lint-imports` reports 9 kept, 0 broken; `screw info bolt` prints the exact `iso4017:M6x20` match and a designation without `8.8`.

---
*Phase: 04-iso-hex-bolts-and-screws*
*Completed: 2026-10-11*
