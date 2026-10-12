---
phase: 04-iso-hex-bolts-and-screws
plan: 11
subsystem: calc
tags: [calc, info-panel, traceability, notes, wrench-size, iso4014, iso4017]

requires:
  - phase: 04-iso-hex-bolts-and-screws
    provides: "04-08: calc.presets.match and designation_for; 04-09/04-10: the full ISO 4017 and ISO 4014 heads, bands and shank cells"
provides:
  - "InfoRow.group (Shank and thread, Head, Part) on every info row"
  - "calc.presets.row_values: the matched row's s_min, e_min, k_max, k_min, dw_min and, on ISO 4014, b, lg_max, ls_min, each labelled with sense and source"
  - "PartInfo.notes: the product grade, then at M10, M12, M14 the ISO versus withdrawn DIN wrench size"
  - "calc.presets.WITHDRAWN_DIN_WRENCH_MM and WITHDRAWN_DIN; calc.SHANK, HEAD, PART, NO_ROW_WARNING"
affects: [04-12 (the API serves the new fields), 04-13 (the page renders groups and notes), 04-14]

actuals:
  tokens: 8366
  tasks: 2
  commits: 2
plan_head_before: 494ed7d5931def5476af48c187c49430952bdd3c
plan_head_after: 6a74924611941013315601e6bbdc1c0f52cf34b3

tech-stack:
  added: []
  patterns:
    - "_bolt matches the catalogue first, then splices the matched row's cited rows in after the row each sits beside (minor_diameter, k), so server order is fixed in one place"
    - "an ISO 4014 row's b is read from the row's thread_length field (the catalogue sets it to the band's b; a test pins that for all 108 rows), so the 125 mm band rule exists once"

key-files:
  created: []
  modified:
    - src/screw/calc/__init__.py
    - src/screw/calc/presets.py
    - tests/test_calc.py
    - tests/test_api.py
    - tests/test_parity.py

key-decisions:
  - "Group names and the no-row warning are module constants in screw.calc (SHANK, HEAD, PART, NO_ROW_WARNING); calc.presets imports HEAD and SHANK from there, so the names exist once and the lazy table import from calc is unchanged (contracts 6 and 7)"
  - "The label cites the table of the stored record each value came from: head.source for the head values, band.source for b, cell.source for lg,max and ls,min"

patterns-established:
  - "Existing tests that use a custom part now expect the no-row warning after the thread warnings; tests/test_calc.py defines NO_ROW and ROW_KEYS once for that"

requirements-completed: []

duration: about 35 min
completed: 2026-10-12
status: complete
---

# Phase 4 Plan 11: The traceable info panel Summary

**The info document now groups its rows (Shank and thread, Head, Part), reports the matched row's five head values and, on ISO 4014, b, lg,max and ls,min with sense and source in each label, says in one warning when no row matches, and adds the product grade and the ISO-versus-DIN wrench size as notes.**

## Performance

- **Duration:** about 35 min
- **Completed:** 2026-10-12
- **Tasks:** 2 (both auto, tdd)
- **Files modified:** 5 (no files created)

## Accomplishments

- Every `InfoRow` has a required `group`; row order is `d, pitch, length, thread_length, shank_length, turns, thread_depth, minor_diameter, [b, lg_max, ls_min], s, across_corners, k, [s_min, e_min, k_max, k_min, dw_min], volume`.
- Labels read `<sense> (<standard>:<edition> <table>)`, e.g. `Across flats, min (ISO 4017:2022 Table 1)` for the default M6 x 20 and `... Table 2` for M10. A test runs every one of the 294 catalogue rows through `derive` and checks each value and label suffix against the stored record.
- A part that matches no row (non-coarse pitch, any edited field, an ISO 4014 shape with `thread_length` off b) has none of the eight keys, empty `notes`, and the warning `no ISO 4014:2022 or ISO 4017:2022 row matches these fields; row values not reported` after the thread, fold and short-thread warnings and before the fine-STL one. An ISO 4017 match has no b, lg_max or ls_min.
- Notes: `product grade A (ISO 4017:2022: l ≤ 150 mm and l ≤ 10 d)` or `product grade B (ISO 4017:2022: l > 150 mm)` with the matched standard substituted; at M10, M12, M14 only, `wrench size 16 mm (ISO 4017:2022); the withdrawn DIN 933 used 17 mm` (DIN 931 for ISO 4014), the ISO figure read from the row's `s`, the DIN figure from `WITHDRAWN_DIN_WRENCH_MM` with its two sources in the comment. A test over the whole catalogue shows exactly the M10, M12 and M14 rows carry the second note, and another that the shipped `s` differs from the DIN figure there.
- Verified: `make verify` exits 0, **2301 passed**, coverage 97.45% (floor 96.0%). `screw info bolt --pitch 0.75` and `screw info bolt` satisfy the plan's two CLI assertions.

## Task Commits

1. **Task 1: Rows in groups, cited row values, one honest warning** - `aad7c2e` (feat)
2. **Task 2: Product grade and ISO-versus-DIN wrench size as notes** - `6a74924` (feat)

**Plan metadata:** the docs commit following this summary.

## Files Created/Modified

- `src/screw/calc/__init__.py` - `InfoRow.group`, `PartInfo.notes`, `SHANK/HEAD/PART/NO_ROW_WARNING`, `_bolt` matches first and splices the cited rows and the no-row warning.
- `src/screw/calc/presets.py` - `row_values`, `notes`, `WITHDRAWN_DIN_WRENCH_MM`, `WITHDRAWN_DIN`.
- `tests/test_calc.py`, `tests/test_api.py`, `tests/test_parity.py` - existing document pins updated for the grouped rows and the no-row warning; new tests as above, the OpenAPI schemas (`InfoRow` requires `group`, `PartInfo` requires `notes`), an API round trip for an ISO 4014 match and a non-row part, and the UI row-key check over an ISO 4014 match.

## Decisions Made

- `_bolt` calls `match` before the rows are built so the cited rows can be spliced in at their place; the lazy `screw.calc.presets` import stays inside the function.
- An ISO 4014 row's `b` is the row's `thread_length` field, not a second copy of the 125 mm band rule; the all-rows test compares it with `band.b_short` or `band.b_long`.

## TDD Gate Compliance

The pre-commit gate (`make verify`) rejects a failing suite, so no separate RED commit was possible (as in every earlier TDD plan of this phase). Honest account of RED:

- **Task 1 RED:** the implementation was written before the tests. With it in place, the existing suite showed `pytest tests/test_calc.py tests/test_api.py tests/test_parity.py tests/test_cli.py -n0 --no-cov`: 11 failed, 252 passed (the old document pins: row keys, warning lists, the OpenAPI `InfoRow` keys). Those failures are the behaviour change, not a fault; they were then rewritten and the new tests added. This is a weaker RED than a test-first one for the new behaviours.
- **Task 2 RED:** tests first. `pytest tests/test_calc.py` failed at collection with `ImportError: cannot import name 'WITHDRAWN_DIN_WRENCH_MM'` before any Task 2 code existed; after a first fix of the import, two of the parametrised cases failed on a wrong test id (`(M14)x40`, the brackets are in the display, not the id), a test fault corrected before GREEN.
- **GREEN:** `aad7c2e` and `6a74924`, `make verify` green in the pre-commit hook on each and again after. No REFACTOR commit. `gsd_run check tdd-red-evidence` not run (pytest console output is not a supported classifier format; same as 04-05 to 04-10).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Existing document pins assumed no group, no row rows and no no-row warning**
- **Found during:** Task 1 (11 failing tests)
- **Issue:** `KEYS` and the default-document row order in `test_calc.py` and `test_api.py`, nine warning-list equalities for custom parts, and the OpenAPI key sets were written for the 04-08 document.
- **Fix:** updated to the new document; custom parts expect `NO_ROW` after the thread warnings; the parts that are catalogue rows (M6 x 30 full thread, left-hand M10 x 60) keep `[STANDING_WARNING]` and `[STANDING_WARNING, refusal]`.
- **Files modified:** tests/test_calc.py, tests/test_api.py
- **Commit:** `aad7c2e`

### Plan wording versus data (no code change)

- The plan's example label `Across flats, min (ISO 4017:2022 Table 2)` is given as "for example". The shipped, double-entered data cites the default M6 head to `Table 1`, so the default part reads `Table 1`; M10 reads `Table 2`. Labels follow the stored `Source`, as D-18 requires. Tests pin both.
- The grade note's wording is the plan's pinned text with the matched standard substituted, including for ISO 4014 (`l ≤ 150 mm and l ≤ 10 d`). I did not check that clause against the ISO 4014 text; the catalogue holds ISO 4014 grade A up to 150 mm and grade B above, which agrees with it.

## Issues Encountered

None beyond the above. The first full `pytest tests` run exceeded the tool's 120 s foreground limit; the focused files and the hook's `make verify` (about 56 s) were used instead.

## Known Stubs

None.

## Threat Flags

None. No new endpoint, auth path or file access; the new fields travel on the existing info route.

T-04-16 (mitigate): a row value is printed only from the exact `match` result; tests cover custom, non-coarse, edited-field and edited-ISO-4014 parts.
T-04-17 (accept): the DIN figures are a constant with both sources in its comment, MEDIUM confidence, three sizes only.

## Next Phase Readiness

04-12 can serve the new fields without a route change (the API returns `PartInfo`); 04-13 renders `group` headings in server order and `notes` after the warnings, reading no row key by name (the parity test over an ISO 4014 match is in place).

Filed: no docs/ideas or docs/tech_debt item.

## Self-Check: PASSED

- `src/screw/calc/__init__.py` and `src/screw/calc/presets.py` present; commits `aad7c2e` and `6a74924` are ancestors of HEAD.
