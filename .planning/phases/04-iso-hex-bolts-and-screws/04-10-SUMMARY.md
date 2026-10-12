---
phase: 04-iso-hex-bolts-and-screws
plan: 10
subsystem: tables
tags: [tables, iso4014, double-entry, owner-copy, shank-cells, thread-band, catalogue]

requires:
  - phase: 04-iso-hex-bolts-and-screws
    provides: "04-09: iso262.SIZES, the ISO 4017 heads and series, the A3 answer, the diff harness; 04-08: match() so every new row is recognised without a calc change"
provides:
  - "rows.ThreadBand and rows.ShankCell"
  - "iso4014.HEADS: 18 heads (grade A for all 15 sizes, grade B for M16, M18, M20), each citing its table and size column as printed"
  - "iso4014.BANDS: 15 sizes, b for l <= 125 and, where the grade A table prints it, c for 125 < l <= 200"
  - "iso4014.CELLS: 108 printed ls,min / lg,max cells, M2 to M20, grade A up to 150 mm (Tables 1 to 3), grade B above (Table 4)"
  - "tests/data/owner/iso4014_heads.tsv, iso4014_bands.tsv, iso4014_lengths.tsv, diffed cell by cell against the shipped rows"
  - "108 ISO 4014 catalogue rows (iso4014:<size>x<length>) filling thread_length = b of the length's band; catalogue is 294 rows, ISO 4017 first"
affects: [04-11, 04-12 (THRD-03 consumers see thread_length < length on the 4014 rows), 04-13 (the picker lists the ISO 4014 standard), 04-14]

actuals:
  tokens: 10846
  tasks: 2
  commits: 2
plan_head_before: e5451caa88743e924cbc5fa4fe924d5c0f6195e7
plan_head_after: 03e75c80395c09fb70bb14eabdd76066c5f8f560

tech-stack:
  added: []
  patterns:
    - "iso4014._RUNS is one tuple per size and grade, (size, grade, table, column, ((length, ls,min, lg,max), ...)): the printed pair of every cell is entered, never derived from b"
    - "presets._row builds a PresetRow for either standard; the standard and the designation noun are arguments, so the id, display and picker grammar exist once"

key-files:
  created:
    - src/screw/tables/iso4014.py
    - tests/data/owner/iso4014_heads.tsv
    - tests/data/owner/iso4014_bands.tsv
    - tests/data/owner/iso4014_lengths.tsv
  modified:
    - src/screw/tables/rows.py
    - src/screw/tables/presets.py
    - tests/test_tables.py
    - tests/test_tables_second_entry.py
    - tests/test_calc.py

key-decisions:
  - "The catalogue order is the tie rule: all 186 ISO 4017 rows precede the 108 ISO 4014 rows, so match reports ISO 4017 if a part ever equalled both (CONTEXT discretion); the tie is latent today because an ISO 4017 screw is threaded to the head and an ISO 4014 bolt only b of it"
  - "A band is cited to its size's grade A table and column, the same cell as the grade A head; a test pins it"
  - "The rows.py docstring said the printed ls,min cell is never stored; it now names the ISO 4014 shank cell as the one stored exception (Pitfall 5)"

patterns-established:
  - "The diff harness' Cells type admits None, the owner's `-` in a number column, so an absent second b is compared as None and not as a string"

requirements-completed: []

duration: about 1 h
completed: 2026-10-12
status: complete
---

# Phase 4 Plan 10: Every ISO 4014 head, band and shank cell, and every ISO 4014 bolt as a preset Summary

**ISO 4014:2022 for M2 to M20 ships as 18 heads, 15 thread-length bands and 108 printed shank cells, each diffed cell by cell against the owner copy with an empty result on the first run, and every one of the 108 bolts is a catalogue row whose thread_length is the b of its length band and which the info document recognises as the exact match.**

## Performance

- **Duration:** about 1 h
- **Completed:** 2026-10-12
- **Tasks:** 2 (both auto, tdd)
- **Files modified:** 9 (4 created: `iso4014.py` and the three owner TSVs)

## Accomplishments

- Heads: grade A for every size (Table 1 for M2 to M4, Table 2 for M5 to M12, Table 3 for M14 to M20), grade B for M16, M18 and M20 (Table 4). `Source.column` keeps the size heading as printed, brackets and comma included.
- Bands: the `b` row of each size's grade A table, plus the `c` row for M14 to M20 (34/40, 38/44, 42/48, 46/52); M2 to M12 have no second row and `b_long` is `None`. Table 4's dashes are not entered.
- Cells: 16 in Table 1, 48 in Table 2, 38 grade A in Table 3 and 6 grade B in Table 4 (M16: 160; M18: 160, 180; M20: 160, 180, 200), each with its printed `ls,min` and `lg,max`. M1,6 and the sizes above M20 are not entered (outside TABL-05).
- Catalogue rows pinned: **108 ISO 4014 rows, 294 in all** (`test_the_iso_4014_catalogue_has_one_row_per_shank_cell`, `test_the_iso_4014_row_counts_the_agreed_transcription_yields`). The ISO 4017 pin of 186 is untouched.
- The cell-by-cell diff over the three owner files was empty at the first run: no re-read, no disagreement, no checkpoint to the owner.
- Tests: per cell `lg,max = l - b` and `ls,min = lg,max - 5 P` (108); the 125 mm band boundary; `b_long` present exactly when a length exceeds 125; per size strictly increasing standard lengths, longest the greatest listed length not above 10 d; the footnote d shortest length from M5 up; grade A to 150 mm and grade B above; table and bracketed column per head and band; A3 (numeric equality with the ISO 4017 head of the same size and grade, separate rows, separate Sources); the order and latent-tie tests; the M10 x 80 row (citation, expansion to `thread_length` 26, designation `Hexagon head bolt ISO 4014 - M10 x 80`); a `derive` round trip for every one of the 294 rows and a pointed one in `test_calc.py`.

## Task Commits

1. **Task 1: ISO 4014 heads, b bands and shank cells, double-entered** - `3aec449` (feat)
2. **Task 2: every ISO 4014 bolt as a preset filling b by length band** - `03e75c8` (feat)

**Plan metadata:** the docs commit following this summary.

## Files Created/Modified

- `src/screw/tables/iso4014.py` - `_source()` helper, 18 `HexHead`, 15 `ThreadBand`, `_RUNS` and the `CELLS` built from it.
- `src/screw/tables/rows.py` - `ThreadBand`, `ShankCell`; docstring names the shank cell as the stored exception.
- `src/screw/tables/presets.py` - `PresetRow.band` and `.cell`, the shared `_row` builder, the ISO 4014 loop after every ISO 4017 row.
- `tests/data/owner/iso4014_*.tsv` - the owner's files, copied with `cp` after `iso4014.py` was written; `cmp` identical to the owner directory.
- `tests/test_tables.py`, `tests/test_tables_second_entry.py`, `tests/test_calc.py` - the tests above.

## Decisions Made

- Order is the tie rule, pinned by a test on the catalogue order and a second one that no ISO 4014 row shares its fields with an ISO 4017 row (so the tie is shown latent, not exercised).
- `test_row_relations` now expects `thread_length == length` for ISO 4017 and `== b of the band` for ISO 4014, with b read from the band records and not from the row under test.
- The source-count pin became 3 per ISO 4017 row and 4 per ISO 4014 row (size, head, band, cell).

## TDD Gate Compliance

The pre-commit gate (`make verify`) rejects a failing suite, so no separate RED commit was possible (as in every earlier TDD plan of this phase). RED was run on the working tree with the tests and the owner copy in place and the implementation emptied or restored from HEAD (my own file edits, no blanket reset).

- **Task 1 RED:** `pytest tests/test_tables.py tests/test_tables_second_entry.py -n0 --no-cov` with `iso4014.py` holding three empty tuples: 32 failed, 626 passed, 2 skipped. Failures: the cell-by-cell diff and the band diff, the 18/15/108 non-vacuity pin, the row-count pins and the per-size, per-head and A3 checks that need at least one row (the per-row parametrised tests collected no case and skipped, which is why the non-empty assertions exist).
- **Task 2 RED:** `pytest tests/test_tables.py tests/test_calc.py -n0 --no-cov` with `presets.py` restored from HEAD: 9 failed, 838 passed, 1 skipped. Failures: the 108-row count, `PresetRow` has no `band` or `cell` (the ISO 4017 no-band test), the order test (no ISO 4014 row), the four `iso4014:` id, display, picker and designation cases, the M10 x 80 citation and expansion, and the pointed `derive` test. The latent-tie test and the parametrised ISO 4014 row tests passed or skipped vacuously over zero ISO 4014 rows, which is why the 108-row count test exists.
- **Semantic assessment:** each counted failure executed and failed on the planned behaviour (a missing row or an empty table), not on a syntax, import or fixture fault. `gsd_run check tdd-red-evidence` was not run: pytest's console output is not a supported classifier report format and the plan is `type: execute` with `tdd="true"` tasks (as in 04-05, 04-07, 04-08 and 04-09).
- **GREEN:** `3aec449` (Task 1) and `03e75c8` (Task 2); `make verify` green on each, and again in the pre-commit hook. Last result: 2277 passed, coverage 97.35% (floor 96.0%). No REFACTOR commit.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Two existing relation tests assumed every row is ISO 4017**
- **Found during:** Task 2 (109 failures once the 108 rows existed)
- **Issue:** `test_row_relations` asserted `thread_length == length` for every catalogue row, and `test_no_row_in_the_tree_is_unverified` asserted `3 * len(ROWS)` sources. Both were true only while the catalogue held ISO 4017.
- **Fix:** the first now expects `length` for ISO 4017 and b of the band for ISO 4014 (b from `iso4014.BANDS`, not from the row); the second counts 3 or 4 sources per row by standard.
- **Files modified:** tests/test_tables.py
- **Commit:** `03e75c8`

**2. [Rule 1 - Bug] My own first draft of the pointed `derive` test claimed the wrong "custom" case**
- **Found during:** Task 2 (1 failed of 1280)
- **Issue:** M10 x 80 threaded to the head is the ISO 4017 M10 x 80 row, not custom.
- **Fix:** the test asserts that part is the exact ISO 4017 row, and uses `thread_length` 30 for the custom case.
- **Commit:** `03e75c8` (never committed in the wrong form)

### Plan-level notes

- **Commit trailer:** the dispatch note named the trailer `Claude Fable 5.1`; the system attribution for this session names `Claude Sonnet 5.5`, which is the model that wrote the code, so both commits carry that one (04-09 amended its trailer the same way).
- **D-14 as superseded by the owner's ruling `B` (2026-10-12):** the owner copy is machine-generated, not typed. The independence of the second entry rests on my own reading of the rendered 150 dpi page images (PDF pages 6 to 10), written into `iso4014.py` before the three owner files were copied. The scratch directory of an earlier plan held pdftotext extracts of the same pages (`tsv-4014-*.tsv`); I did not open them.
- **Stepped lines:** the white cells were identified by the printed `ls,min` / `lg,max` pair in each cell (grey cells print nothing), rather than by pixel sampling. The 108 cells agree with the owner file, which was pixel-sampled.
- **Latent tie:** nothing is exercised by the ISO 4017-before-ISO 4014 order today; it is a guard for a later table.

**Total deviations:** 2 auto-fixed (Rule 1, both in tests), 4 plan-level notes. **Impact:** no change to scope.

## Authentication Gates

None.

## Known Stubs

None. No placeholder, empty value flowing to a UI, or TODO was left in the files of this plan.

## Threat Flags

None. No new network endpoint, auth path, file access pattern or schema change; the tables are static data read by the existing catalogue. T-04-15 (mistyped cell) is mitigated by the owner diff plus the two stored-cell relations.

## Issues Encountered

- `gsd_run` was not defined in the executor's shell, so the state updates below call `gsd-tools.cjs` through `node`.
- The pages carry the iTeh preview watermark; the owner's ruling of 2026-10-11 (`A - 3.`) makes them the source for the tables they contain. Nothing in the rows came from anywhere else.
- ISO 4014 Table 1 also prints M1,6 (lengths 12 and 16) and Table 4 prints M22 to M27 and lengths above 200; none is entered, being outside M2 to M20 and the 200 mm cap.

## Next Phase Readiness

The catalogue now holds both standards for M2 to M20 (294 rows). A part built from an ISO 4014 row has `thread_length` < `length`, so plans 04-11 and 04-12 see a real shank and a thread that starts at the tip; the picker of plan 04-13 gets a second standard in `picker[0]`. Requirement traceability (TABL-02/03/04, TYPE-01, THRD-03) is left to `phase.complete`: later plans of the phase declare the same ids.

## Self-Check: PASSED

- FOUND: src/screw/tables/iso4014.py, tests/data/owner/iso4014_heads.tsv (19 lines), iso4014_bands.tsv (16 lines), iso4014_lengths.tsv (109 lines)
- FOUND: commits `3aec449` and `03e75c8` on `gsd/phase-04-iso-hex-bolts-and-screws`
- `CELLS`, `HEADS`, `BANDS` and `standard="ISO 4014"` present in iso4014.py; `iso4014:` and `b_short` present in presets.py; `lg_max` and `ls_min` with `5 * ` pitch present in tests/test_tables.py
- `make verify` exit 0 on the final tree: 2277 passed, coverage 97.35%
