---
phase: 04-iso-hex-bolts-and-screws
plan: 07
subsystem: tables
tags: [tables, iso-262, iso-4017, double-entry, unverified-gate, import-contracts, sys-modules-control]

requires:
  - phase: 04-iso-hex-bolts-and-screws
    provides: "04-01: the rendering route and the owner copy; 04-03/04-04: the frozen defaults s 10.0, k 4.0, thread_length 20.0 the M6 x 20 row agrees with"
provides:
  - "src/screw/tables/: Source, Size, HexHead, SeriesLength (frozen, slotted, keyword-only, no defaults); SIZES (ISO 262:2023 M6); HEADS and SERIES (ISO 4017:2022 grade A, M6, lengths 12 to 60); presets.py with FIELD_NAMES, PresetRow, catalogue(), expand()"
  - "tests/data/owner/: the owner's M6 lines verbatim, the other side of the cell-by-cell diff"
  - "import-linter contracts 6 (The parameters never consult a table) and 7 (Tables are a leaf); contract 2 widened with screw.tables; 9 contracts KEPT"
  - "tests/test_import_boundaries.py: the subprocess sys.modules control for contract 6, with its positive control"
affects: [04-08 (presets.py in calc, the info document's preset and designation, adds the derive converse), 04-09 (the other 14 sizes and the ISO 4014 rows, same row types and gates)]

actuals:
  tokens: 7833
  tasks: 1
  commits: 1
plan_head_before: 78ca9229fa46ddf78e27a7ea45737643c232f2ae
plan_head_after: 6e952efe62cdab7b2c7daeab08155fa812b95de8

tech-stack:
  added: []
  patterns:
    - "A required typed Source on every row: a row without source= is a mypy --strict error (proved inside the suite by one mypy.api run over a bad and a good file)"
    - "Double entry: the agent's rows are transcribed from page images before the owner copy is opened; a header-driven TSV parser and diff() compare every cell, Source table and column included"
    - "A runtime sys.modules probe (python -I, fresh interpreter) covers the package __init__ edge that grimp cannot see"

key-files:
  created:
    - src/screw/tables/__init__.py
    - src/screw/tables/rows.py
    - src/screw/tables/iso262.py
    - src/screw/tables/iso4017.py
    - src/screw/tables/presets.py
    - tests/test_tables.py
    - tests/test_tables_second_entry.py
    - tests/test_import_boundaries.py
    - tests/data/owner/iso262.tsv
    - tests/data/owner/iso4017_heads.tsv
    - tests/data/owner/iso4017_lengths.tsv
  modified:
    - pyproject.toml
    - docs/architecture/overview.md

key-decisions:
  - "Source.table is the printed table title (`Table 1`) and Source.column the column heading as printed (`M6`; `Coarse` for ISO 262); the owner's copy uses the same spellings, so the diff needed no reconciliation"
  - "Preset ids keep the size label as printed with a capital M (`iso4017:M6x20`), as the plan's regex and expand case require; CONTEXT D-11 says lowercase, the plan is the later and more specific statement"
  - "The designation prints ASCII `-` and `x` and a decimal comma in the size (`M3,5`), never brackets and no property class, per 04-OWNER-READS.md"

patterns-established:
  - "Per-size records of numbers with an identifier-only Source; tolerance columns are not stored (Pitfall 10)"

requirements-completed: [TABL-02, TABL-03, TABL-04, TABL-07]

duration: about 10 min
completed: 2026-10-11
status: complete
---

# Phase 4 Plan 07: ISO 262 and ISO 4017 M6 rows, double-entered behind contracts 6 and 7 Summary

**The first cited rows ship in `screw.tables` (ISO 262:2023 M6, ISO 4017:2022 M6 grade A head and the eleven M6 lengths), transcribed from page images, diffed cell by cell against the owner's copy with no disagreement, gated against `unverified` rows, and fenced by import-linter contracts 6 and 7 plus a runtime `sys.modules` control.**

## Performance

- **Duration:** about 10 min
- **Started:** 2026-10-11T16:59:00Z
- **Completed:** 2026-10-11T17:08:00Z
- **Tasks:** 1
- **Files modified:** 13 (11 created, 2 modified)

## Accomplishments
- `rows.py`: `Status`, `Source` (with `cite()`), `Size`, `HexHead`, `SeriesLength`, all `@dataclass(frozen=True, slots=True, kw_only=True)` with no defaults.
- Rows entered: ISO 262:2023 M6 (d 6.0, pitch 1.0, choice 1, Table 1, `Coarse`); ISO 4017:2022 M6 grade A (pitch 1.0, s 10.0, s_min 9.78, e_min 11.05, k 4.0, k_min 3.85, k_max 4.15, dw_min 8.88, Table 1, `M6`); the series 12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60 (grade A, Table 1, `M6`).
- `presets.py`: `catalogue()` returns 11 rows (`iso4017:M6x12` to `iso4017:M6x60`); `expand("iso4017:M6x20")` is `{d: 6.0, pitch: 1.0, length: 20.0, s: 10.0, k: 4.0, thread_length: 20.0}`, which equals `BoltParams()` field for field (a test asserts it, closing the D-07 loop at the table side); `expand("iso4017:m6x20")` is `None`. Citation of the M6 x 20 row: `ISO 262:2023 Table 1, column Coarse; ISO 4017:2022 Table 1, column M6`. Designation: `Hexagon head screw ISO 4017 - M6 x 20`.
- Double-entry diff over the committed owner copy: empty. Positive control: one changed cell gives exactly one line naming file, key, column and both values; one-sided keys are reported either way.
- UNVERIFIED gate: a regex scan of every `src/screw/tables/*.py` and a runtime walk of `SIZES`, `HEADS`, `SERIES` and every catalogue row's three sources, each with a positive control.
- TABL-02 type proof: one `mypy.api.run` (`--strict`, project config) over a HexHead without `source=` and the same call with it; the error names `"source"` on the bad file's call line and the good file is clean.
- TABL-03: one relation test per catalogue row (id as test id): s_min < s, dw_min < s_min < e_min < s / cos 30 degrees, k_min <= k <= k_max, head pitch equals the ISO 262 pitch, grade from (d, length), thread_length = length; plus series strictly increasing, ids unique and in catalogue order, bracket iff choice 2, symmetric k tolerance (own test, with the comment that a confirmed row breaking it comes out only with the owner's ruling).
- Contracts: 6 and 7 added, contract 2 widened; `make lint-imports` reports `Contracts: 9 kept, 0 broken`. `tests/test_import_boundaries.py`: `BoltParams()` and `import screw.solid` leave `screw.tables` out of `sys.modules` (fresh `python -I` interpreter); `import screw.tables.presets` puts it in (the control).

## Pages read (second copy, D-14)

Rendered with `pdftoppm -r 150` (and one 300 dpi crop of the length block) into the session scratch directory; nothing rendered entered the repository. Read on 2026-10-11 under the owner's ruling of the same date (`04-OWNER-READS.md`, literal `A - 3.`): the on-disk preview pages are the purchased pages and serve as the agent's second copy for the tables they contain.

| Standard | PDF page | Printed page | Content read |
| -------- | -------- | ------------ | ------------ |
| ISO 4017:2022 | 7 | 3 | Table 1 (grade A, M1,6 to M7): the M6 column of the head block and the M6 range of the stepped length block (first row 12, last row 60) |
| ISO 262:2023 | 6 | 2 | Table 1 (continued): the M6 row, first choice, coarse pitch |
| ISO 262:2023 | 5 | 1 | Table 1 (first page): layout check only, M6 is not on it |

`pdftotext` was used only to find which page carries which table title; no value was read from extracted text. The rows were written to `src/screw/tables/` before the owner's TSVs were opened. The owner copy was then taken as the header plus M6 lines of each file (each file already held only those lines; `cmp` shows the three are byte-identical to the owner's) and the diff run: no disagreement on the first run, no cell re-read or edited.

## Task Commits

1. **Task 1: the ISO 262 and ISO 4017 M6 rows ship cited, double-entered and gated, behind contracts 6 and 7** - `6e952ef` (feat)

**Plan metadata:** the docs commit that follows this file (docs: complete plan)

## TDD Gate Compliance

The pre-commit gate (`make verify`) rejects a failing suite, so no separate RED commit was possible (as plans 04-02 to 04-05). RED was run with `src/screw/tables/iso262.py` and `iso4017.py` temporarily replaced by empty tuples (the package, `rows.py` and `presets.py` real), then the real files restored from a scratch copy. Command: `pytest tests/test_tables.py tests/test_tables_second_entry.py tests/test_import_boundaries.py -n0 --no-cov`: 5 failed, 16 passed, 2 skipped (the per-row parametrisation over an empty catalogue). The 5 failures, all assertion failures on the planned behaviour:
- `tests/test_tables.py::test_the_m6_by_20_preset_expands_to_the_frozen_defaults_of_the_part` (`expand` returned None, not the field dict)
- `tests/test_tables.py::test_the_row_citation_lists_each_source_once_and_the_designation_has_no_class` (no `iso4017:M6x20` row)
- `tests/test_tables_second_entry.py::test_the_owner_copy_and_the_shipped_rows_agree_cell_by_cell` (every owner key reported "only in the owner copy")
- `tests/test_tables_second_entry.py::test_one_changed_cell_is_one_disagreement_naming_file_key_column_and_both_values` and `::test_a_row_on_one_side_only_is_a_disagreement` (keys missing on the shipped side)

The tests that passed under the empty tables are guards that do not depend on a row: the mypy citation test, the text-scan and runtime-check positive controls, the `sys.modules` probes (the tables are not loaded until imported), and the id-grammar and unknown-id cases.

Semantic assessment: each failing target executed and failed on the planned behaviour (a row that should be present and was not), not on an import, fixture or syntax fault. `gsd_run check tdd-red-evidence` was not run; the plan is `type: execute` with a `tdd="true"` task and pytest's console format is not one of the classifier's supported report formats (as in 04-05).

**GREEN:** `6e952ef`; `make verify` green (ruff, mypy --strict, 9 contracts kept, unfinished-work scan, 1057 passed, coverage 97.45%, floor 96.0%). The pre-commit hook ran the same gate on the commit. No REFACTOR commit.

## Files Created/Modified
- `src/screw/tables/__init__.py` - docstring only: what the package is and the D-16 licence stance
- `src/screw/tables/rows.py`, `iso262.py`, `iso4017.py`, `presets.py` - row types, the rows, the catalogue and `expand`
- `tests/test_tables.py` - relations per row, the UNVERIFIED gate with controls, the mypy citation proof, catalogue and `expand` cases
- `tests/test_tables_second_entry.py` - the TSV parser, `diff()` and its controls
- `tests/test_import_boundaries.py` - the subprocess `sys.modules` control
- `tests/data/owner/*.tsv` - the owner's M6 lines
- `pyproject.toml` - contracts 6 and 7; contract 2's `source_modules` gains `screw.tables`
- `docs/architecture/overview.md` - see Deviations

## Decisions Made
- Source labels use the printed spellings (`Table 1`, `M6`, `Coarse`); the owner's copy agrees, so no normalisation exists anywhere.
- Length in ids, display and designation is `f"{length:g}"`, the plan's form; it prints integers exactly for every length in the standards (all at or below 500).
- Contract 7's forbidden list is the plan's (`screw.records`, `pydantic` included); `screw.records` is also the logger module, so the leaf is free of the project's own logging as well as `logging`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] `docs/architecture/overview.md` named contracts 6 and 7 as a planned gap**
- **Found during:** Task 1 (adding the contracts)
- **Issue:** the overview says "Seven are in force ... contracts 6 and 7 (the tables) land in Phase 4" and has no `tables` module row; after this commit both statements are false, and CLAUDE.md says a module's contract lands with the module (and the overview is the system map).
- **Fix:** a `tables` row in the module table, "Nine are in force", contracts 6 and 7 listed, the planned-gap sentence reduced to contract 9. Not in the plan's `files_modified`.
- **Files modified:** `docs/architecture/overview.md`
- **Verification:** read back; `make verify` green
- **Committed in:** `6e952ef`

**2. [Rule 1 - Bug] Lint failures in the first draft**
- **Found during:** Task 1 (`make verify`)
- **Issue:** ruff RUF001 on the literal multiplication sign and E501 on four long lines; the mypy test hard-coded the bad row's line number, which moved when the shared template was wrapped.
- **Fix:** `×` escapes (the display string is unchanged), wrapped lines, and the bad line computed from the template text.
- **Files modified:** `src/screw/tables/presets.py`, `tests/test_tables.py`
- **Verification:** `make verify`
- **Committed in:** `6e952ef`

**Total deviations:** 2 auto-fixed (1 missing doc truth, 1 lint). **Impact:** none on scope or behaviour.

## Authentication Gates
None.

## Issues Encountered
None. No double-entry disagreement; no `blocking-human` checkpoint was needed.

## Known Stubs
None. No filed debt item and no `.planning/WINDOWS.md` entry: nothing was left unfinished.

## Threat Flags
None beyond the plan's register. T-04-09 (UNVERIFIED reaching `main`): text scan and runtime walk in `make verify`, each with a positive control. T-04-10 (agent copy biased by the owner copy): transcription from page images preceded opening the owner copy. T-04-11: contract 6 plus the `sys.modules` probe and control. T-04-12: per-size records only; `git ls-files '*.pdf' '*.png'` is empty and `git status --porcelain` lists no PDF or PNG.

## Next Phase Readiness
- Plan 04-08 can add `screw.calc.presets` over `catalogue()`, the info document's `preset` and `designation`, and the `derive` converse to the `sys.modules` test once `_bolt` imports the catalogue lazily.
- Plan 04-09 extends `SIZES`, `HEADS` and `SERIES` to the other sizes and adds ISO 4014 under the same gates; the catalogue id regex and the order test already allow `iso4014`. The relation test's grade rule and the bracket rule apply to the larger set unchanged.

## Self-Check: PASSED

- Created files exist: `src/screw/tables/{__init__,rows,iso262,iso4017,presets}.py`, `tests/test_tables.py`, `tests/test_tables_second_entry.py`, `tests/test_import_boundaries.py`, `tests/data/owner/{iso262,iso4017_heads,iso4017_lengths}.tsv`.
- Commit `6e952ef` is an ancestor of HEAD; `git rev-list --count 78ca922..6e952ef` is 1.
- Acceptance: `rows.py` has `kw_only=True` and `class Source`; `tables/__init__.py` has no `import` text; `pyproject.toml` has both contract names and `screw.tables` in contract 2; `iso4017_heads.tsv` header matches; `git ls-files '*.pdf' '*.png'` empty; `make verify` exit 0; `make lint-imports` 9 kept.
