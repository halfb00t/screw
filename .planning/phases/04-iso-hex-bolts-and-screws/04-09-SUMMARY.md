---
phase: 04-iso-hex-bolts-and-screws
plan: 09
subsystem: tables
tags: [tables, iso262, iso4017, double-entry, owner-copy, series-rules, catalogue]

requires:
  - phase: 04-iso-hex-bolts-and-screws
    provides: "04-07: row types, the M6 rows, the double-entry diff and the relation tests; 04-08: match() so every new row is recognised on the info document without a calc change"
provides:
  - "iso262.SIZES: the 15 sizes of TABL-05 (coarse pitch, choice 2 for M3.5, M7, M14, M18)"
  - "iso4017.HEADS: 18 heads (grade A for all 15 sizes, grade B for M16, M18, M20), each citing its table and size column as printed"
  - "iso4017.SERIES: 186 lengths, M2 to M20, grade A up to 150 mm (Tables 1 and 2), grade B above (Table 3), up to the 200 mm cap"
  - "tests/data/owner/iso262.tsv, iso4017_heads.tsv, iso4017_lengths.tsv in full, diffed cell by cell against the shipped rows"
  - "tests/test_tables.py::STANDARD_LENGTHS (the owner-confirmed list, A1) with the series, grade, bracket and round-trip tests"
  - "04-OWNER-READS.md `## Full copy`: A1, A3, no relation dropped, the owner ruling on how the owner copy was produced"
affects: [04-10 (ISO 4014 reuses the sizes, the A3 answer and the owner's iso4014 files), 04-13 (the picker reads the bracketed pickers), 04-14]

actuals:
  tokens: 5359
  tasks: 3
  commits: 2
plan_head_before: 9b1a73e71e7b2bacb81d78e33bafe4d1aea77d3f
plan_head_after: 9102fe14d0255c7ffc8d75593ba7ad268a593457

tech-stack:
  added: []
  patterns:
    - "iso4017.SERIES is built from one run per size and grade, (size, grade, table, column, lengths), so a length's grade and its citation come from the same place as its head"
    - "A test that parametrises over rows also asserts the set is not empty, so no loop can pass for nothing"

key-files:
  created: []
  modified:
    - src/screw/tables/iso262.py
    - src/screw/tables/iso4017.py
    - tests/test_tables.py
    - tests/test_tables_second_entry.py
    - tests/test_calc.py
    - tests/data/owner/iso262.tsv
    - tests/data/owner/iso4017_heads.tsv
    - tests/data/owner/iso4017_lengths.tsv
    - .planning/phases/04-iso-hex-bolts-and-screws/04-OWNER-READS.md

key-decisions:
  - "The ISO 4017 catalogue is pinned at 186 rows, counted after the diff was empty; the pin counts ISO 4017 rows only so plan 04-10's ISO 4014 rows do not move it"
  - "The series test is stronger than the plan's three rules: a size's series must equal every listed length between the first and last bound, so a missing length fails it, not only a wrong bound"
  - "STANDARD_LENGTHS is the owner's A1 confirmation of the research guess, cited to 04-OWNER-READS.md, not a formula"

patterns-established:
  - "Second-entry order inside one plan: write the transcription, then `cp` only the owner files that task covers, then run the diff; the lengths file stays unopened until Task 3's rows are written"

requirements-completed: [TABL-02, TABL-03, TABL-04, TABL-05, TYPE-02]

duration: about 1 h (Tasks 2 and 3; Task 1 was the owner's)
completed: 2026-10-12
status: complete
---

# Phase 4 Plan 09: Every ISO 262 size and every ISO 4017 row for M2 to M20 Summary

**All 15 ISO 262:2023 sizes, 18 ISO 4017:2022 heads and 186 ISO 4017 lengths up to 200 mm ship as cited rows, each diffed cell by cell against the owner copy with an empty result on the first run, and every one of the 186 rows is recognised as an exact match on the info document.**

## Performance

- **Duration:** about 1 h for Tasks 2 and 3 (Task 1 was the owner's checkpoint)
- **Completed:** 2026-10-12
- **Tasks:** 3 (Task 1 the owner checkpoint, Tasks 2 and 3 auto)
- **Files modified:** 9 (the three owner TSVs extended, not created)

## Accomplishments

- Sizes: `iso262.SIZES` holds M2, M2.5, M3, M3.5, M4, M5, M6, M7, M8, M10, M12, M14, M16, M18, M20 with the coarse pitch read from Table 1 (pages 1 and 2 of the standard); choice 2 for exactly M3.5, M7, M14 and M18.
- Heads: grade A for every size (Table 1 for M2 to M7, Table 2 for M8 to M20), grade B for M16, M18 and M20 (Table 3). `Source.column` keeps the size heading as printed, so `(M3,5)`, `(M7)`, `(M14)` and `(M18)` carry their brackets and a test reads them from there (Pitfall 8).
- Lengths: the stepped bold lines of the three length blocks gave 74 grade A lengths in Table 1, 106 in Table 2 and 6 grade B lengths in Table 3 (M16: 160; M18: 160, 180; M20: 160, 180, 200). Every size's series equals the listed lengths from the one nearest 2 d (ties to the longer: M3.5 starts at 8, M7 at 16) to the longest not above min(10 d, 200).
- The cell-by-cell diff was empty at the first run for both batches (sizes and heads; lengths): no re-read, no disagreement, no checkpoint to the owner.
- The tests: 15 sizes and the choice set, a relation test per head (18), the series rules per size, 150 mm grade A and 160 mm grade B, a head for every (size, grade) of the series, the 186-row pin, a `derive` round trip for every row, the bracket, id, display, picker and designation cases for M7 x 20, M3.5 x 20, M14 x 50 and M18 x 50, and `expand("iso4017:M20x200")` present and `M20x220` absent.
- Catalogue row count, pinned: **186 ISO 4017 rows** (`tests/test_tables.py::test_the_iso_4017_catalogue_has_the_row_count_the_agreed_transcription_yields`).

## Task Commits

1. **Task 1: owner completes the owner copy, answers A1 and A3** - no commit (checkpoint; the owner's reply is recorded in 04-OWNER-READS.md by Task 2)
2. **Task 2: all 15 ISO 262 sizes and every ISO 4017 head** - `6c313cb` (feat)
3. **Task 3: every ISO 4017 length up to 200 mm** - `9102fe1` (feat)

**Plan metadata:** the docs commit following this summary.

Note: commit `6c313cb` was amended once after creation to correct the `Co-Authored-By` trailer to the model that wrote it; the tree is unchanged by the amendment and the pre-commit gate ran again and passed.

## Files Created/Modified

- `src/screw/tables/iso262.py` - the 15 sizes, one shared `Source` for Table 1, column Coarse.
- `src/screw/tables/iso4017.py` - `_source()` helper, 18 `HexHead` rows, `_RUNS` and the `SERIES` built from it.
- `tests/data/owner/iso262.tsv`, `iso4017_heads.tsv`, `iso4017_lengths.tsv` - the owner's files, copied with `cp`.
- `tests/test_tables.py` - the tests above, `STANDARD_LENGTHS`.
- `tests/test_tables_second_entry.py` - `test_the_owner_copy_is_not_vacuous` (15, 18 and 186 rows in the three files).
- `tests/test_calc.py` - one case moved off a part that became a row (see Deviations).
- `04-OWNER-READS.md` - `## Full copy (owner, 2026-10-12)`.

## Owner's answers (recorded in 04-OWNER-READS.md)

- A1: confirmed, the 31-length list of the research guess, unchanged.
- A3: yes, ISO 4014 and ISO 4017 head values are equal per size and grade (plan 04-10 can reuse the heads).
- Relations dropped: none (item 7 was unanswered and is treated as none; no printed row broke a relation, so nothing had to be reported).
- Ruling `B` of 2026-10-12: the owner copy was generated from the purchased PDFs' text layer by `make_owner_copy.py` (outside the repository), the stepped lines read by pixel sampling, the ISO 4014 pixel read cross-checked against the printed ls,min / lg,max pairs. This supersedes D-14's "the owner types one copy" for this phase.

## Decisions Made

- The row count is pinned for ISO 4017 only (186), so 04-10 adds ISO 4014 rows without touching this pin.
- Series rules are tested as an equality against the standard list between two bounds, which also catches a dropped length.
- `_RUNS` keeps one tuple per size and grade rather than one `SeriesLength(...)` per length; the Source and the grade are stated once for the run, and the head test pins that they match the head's.

## TDD Gate Compliance

The pre-commit gate (`make verify`) rejects a failing suite, so no separate RED commit was possible (as in every earlier TDD plan of this phase). RED was run on the working tree with the tests and the owner copy in place and the old implementation restored from HEAD for the specific files (`git checkout -- <file>`, my own edit, no blanket reset).

- **Task 2 RED:** `pytest tests/test_tables.py tests/test_tables_second_entry.py -n0 --no-cov` with the M6-only `iso262.py` and `iso4017.py`: 4 failed, 42 passed. Failures: the 15-size test, the grade A head for every size test, the cell-by-cell diff (owner file full, shipped rows M6 only) and the one-changed-cell test (the diff reported far more than one line). The head-relation, bracket and table-citation tests passed vacuously over the single M6 head, which is why `test_the_owner_copy_is_not_vacuous` and the 15-size and 18-head assertions exist.
- **Task 3 RED:** same command with the Task 2 `iso4017.py` (SERIES M6 only) and the 186-row owner file: 25 failed, 74 passed. Failures: the per-size series tests for every size but M6, the 150 mm grade test, the head-for-every-grade test, the 186-row pin, the round trip and bracket cases for the sizes with no row, the M20 cap test, the cell-by-cell diff and the row-on-one-side test.
- **Semantic assessment:** each counted failure executed and failed on the planned behaviour (a missing size, a length not in the shipped rows, a row count of 11 not 186), not on a syntax, import or fixture fault. `gsd_run check tdd-red-evidence` was not run: pytest's console output is not a supported classifier report format and the plan is `type: execute` with `tdd="true"` tasks (as in 04-05, 04-07 and 04-08).
- **GREEN:** `6c313cb` (Task 2) and `9102fe1` (Task 3); `make verify` green on each, and again in the pre-commit hook. Last result: 1657 passed, coverage 97.26% (floor 96.0%). No REFACTOR commit.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `test_a_part_matching_no_row_is_custom_with_no_designation` assumed M8 x 20 was not a row**
- **Found during:** Task 3 (`make verify`, 1 failed of 1657)
- **Issue:** the test built `BoltParams(d=8.0, pitch=1.25, s=13.0, k=5.3)`, which is the M8 x 20 row once ISO 4017 M8 ships (the default length and thread_length are 20). It read `exact`, not `custom`; the test's premise had only been true while the catalogue held M6 alone.
- **Fix:** the case keeps its intent (an M8 part with every M8 head value but no row) by setting `length=22.0, thread_length=22.0`, which is not in the M8 series; a comment says why.
- **Files modified:** tests/test_calc.py (not in the plan's `files_modified`; it is in Task 3's verify command)
- **Verification:** `make test PYTEST_ARGS="tests/test_calc.py ..."` 40 passed; `make verify` green.
- **Commit:** `9102fe1`

### Plan-level deviations

- **D-14 supersession (owner ruling `B`, 2026-10-12):** the owner copy is machine-generated from the PDFs' text layer and pixel-sampled for the stepped lines, not typed by hand. The independence of the second entry now rests on my own reading of the rendered page images, which was done and written before any owner file for that task was copied. It is recorded in 04-OWNER-READS.md. The verifier should note that the two copies share the same PDFs but not the same reading method: the owner copy is text layer plus pixels, mine is the rendered image read by eye, one length block zoomed to 200 dpi.
- **The series bounds** (the first and last length of each size) were produced by the generator and reported to the owner, not separately typed by the owner. My independent reading of the stepped bold lines agreed with them for all 15 sizes.
- **Owner reply item 7** (relations a printed row legitimately breaks) was unanswered; treated as none, as instructed. No relation broke.

**Total deviations:** 1 auto-fixed (Rule 1), 3 plan-level notes above. **Impact:** no change to scope; the one test edit keeps its intent.

## Authentication Gates

None. Task 1 was an owner checkpoint (human-action), handled before this resume.

## Known Stubs

None. No placeholder, empty value flowing to a UI, or TODO was left in the files of this plan.

## Threat Flags

None. No new network endpoint, auth path, file access pattern or schema change; the tables are static data read by the existing catalogue.

## Issues Encountered

- `gsd_run` was not defined in the executor's shell, so the state updates below call `gsd-tools.cjs` through `node`.
- The pages carry the iTeh preview watermark; the owner's ruling of 2026-10-11 (`A - 3.`) makes them the source for the tables they contain. Nothing in the rows came from anywhere else.

## Next Phase Readiness

Plan 04-10 can reuse `iso262.SIZES`, the ISO 4017 heads (A3: equal per size and grade) and the owner's `iso4014_*.tsv` files, which sit in the owner copy directory and which this plan did not open or transcribe.

## Self-Check: PASSED

- FOUND: src/screw/tables/iso262.py, src/screw/tables/iso4017.py, tests/data/owner/iso262.tsv (16 lines), iso4017_heads.tsv (19 lines), iso4017_lengths.tsv (187 lines)
- FOUND: commits `6c313cb` and `9102fe1` on `gsd/phase-04-iso-hex-bolts-and-screws`
- `label="M3.5"` and `choice=2` present in iso262.py; `## Full copy` with `A1:` and `A3:` present in 04-OWNER-READS.md
- `make verify` exit 0 on the final tree: 1657 passed, coverage 97.26%
