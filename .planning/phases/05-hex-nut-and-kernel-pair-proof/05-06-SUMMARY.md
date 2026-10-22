---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 06
subsystem: tables
tags: [tables, iso4032, gost, hex-nut, double-entry, citation, relations]
requires:
  - phase: 05-04
    provides: "NutParams with the frozen s 10.0 and m 5.2 defaults"
  - phase: 05-05
    provides: "the nut's validators"
provides:
  - "tables/iso4032.py NUTS: 14 cited GOST ISO 4032-2014 rows, M2 to M20, Table 1 and Table 2, no M7"
  - "rows.py HexNut, Source.document(), ADOPTED_ISO"
  - "tests/data/owner/iso4032.tsv and its cell-by-cell diff in make verify (empty)"
  - "one relation test per nut row, and the frozen nut defaults pinned to the M6 row"
affects: [05-07, 05-08, 05-09, 05-11, 05-13]
actuals:
  tokens: 5200
  tasks: 2
  commits: 2
plan_head_before: 5f67579bc8a84ed72de69b42757ded5a538fd760
plan_head_after: f4eb57d8c55ac25e7eaba49ea9a26c9d3425a10d
tech-stack:
  added: []
  patterns:
    - "a GOST text is cited as its own designation plus the ISO edition it adopts, from a closed map"
    - "a relation helper returns the broken relations by name, with a planted-row positive control"
key-files:
  created:
    - src/screw/tables/iso4032.py
    - tests/data/owner/iso4032.tsv
  modified:
    - src/screw/tables/rows.py
    - src/screw/tables/__init__.py
    - src/screw/params.py
    - tests/test_tables.py
    - tests/test_tables_second_entry.py
    - tests/test_params.py
key-decisions:
  - "Every nut row is normative and its Source names Table 1 or Table 2 (owner ruling 2026-10-20); there is no informative flag"
  - "Source.document() raises ValueError for any standard that is neither ISO nor a mapped GOST designation, so a citation is never guessed"
  - "The existing literal test test_the_nut_defaults_are_the_iso_4032_m6_values_the_owner_accepted stays (05-04 SUMMARY refs it); the two new tests sit beside it"
requirements-completed: []
requirements-partial:
  - id: TYPE-03
    note: "the nut rows ship cited and double-entered; the catalogue, the panel and the chamfer rows are 05-07 to 05-13, so it is not marked complete"
  - id: INFO-01
    note: "the rows the panel will read ship; the panel itself is 05-09"
status: complete
---

# Phase 5 Plan 06: GOST ISO 4032-2014 hex nut rows Summary

14 cited GOST ISO 4032-2014 (ISO 4032:2012) hex nut rows, transcribed from page images and diffed cell by cell against the owner's text-layer copy with an empty diff, each guarded by relation tests, with the frozen nut defaults pinned to the M6 row.

## What was done

**Preconditions.** All three held: the PDF's sha256 printed `1f4183cafec1eadbe13bfc5bb2df29fbe4fae6c9dcbd04de49524dbd1afa84e1` (matched); `pdftoppm` rendered PDF pages 5 to 8 to the session scratch directory; the owner copy directory held `iso4032.tsv` and its header line matched the recorded one (`head -1` only).

**Independent transcription first (D-14, T-05-14).** Pages 7 and 8 (Table 1 continued across both, Table 2 on page 8) were read from the rendered images and written into `iso4032.py` before any data row of the owner copy was opened. No text extraction was run on the PDF. M1,6 and sizes above M20 were left out as out of scope. The rendered scope clause (page 6) prints grade A for D up to M16 and grade B for D above M16, which is the rule the text layer had given, so `grade` follows it (M2 to M16 A, M18 and M20 B).

**Then the owner copy.** `iso4032.tsv` was copied byte for byte (`cmp` exit 0) into `tests/data/owner/`. The diff in `make verify` reports no disagreement on any of the 14 rows or on any table or column label, so no stop to the owner was needed and neither copy was edited.

**Code.** `HexNut` (frozen, slots, kw_only, no defaults; the interface's fields), `Source.document()` and `ADOPTED_ISO` in `rows.py`; `cite()` now uses `document()`. Every Phase 4 string is unchanged, asserted by a test that walks every ISO 262, 4014 and 4017 row. A standard that is not `ISO ` or a mapped `GOST ` designation raises `ValueError` naming it.

**Tests.** The `_SHAPE` entry and `shipped()` rows for `iso4032.tsv` and the non-vacuous count (14); `iso4032.NUTS` in the unverified walk; the row set, field list, citation strings and a mypy `--strict` check that a `HexNut` without `source=` errors naming `source`; relation tests per row (s_min < s, e_min > s, m_min < m_max, mw_min < m_min, dw_min < s_min, c_min < c_max, da_min < da_max, pitch equals the ISO 262 pitch, grade rule) with a planted-row control; `test_the_frozen_nut_defaults_are_the_iso_4032_m6_row_the_owner_confirmed` (literals) and `test_the_frozen_nut_defaults_are_the_iso_4032_m6_row` (the row's `s` and `m_max`). One comment sentence in `params.py` records the 2026-10-20 cross-check.

## Task commits

| Task | Commit | Message |
| ---- | ------ | ------- |
| 1 | 66bf25b | feat(tables): ship the GOST ISO 4032-2014 hex nut rows, double-entered |
| 2 | f4eb57d | test(tables): guard every GOST ISO 4032-2014 row and pin the nut defaults to the M6 row |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The first commit attempts failed the pre-commit `make verify`**
- **Found during:** Task 1 commit
- **Issue:** two E501 line-length errors, a PT018 combined assertion and a mypy `attr-defined` on a heterogeneous row list in the new tests.
- **Fix:** wrapped the docstring, split the assertion into a tuple compare, built the source list from per-table generators.
- **Files modified:** `src/screw/tables/__init__.py`, `tests/test_tables.py`
- **Commit:** 66bf25b (the failed attempts left nothing committed)

**2. [Judgement, not a rule] One relation test per row, not per relation.** The plan's truth says one relation test per row; Task 2's behavior says one parametrised test per relation. I wrote one parametrised test per row (one id per shipped size) whose helper names each broken relation, and a planted-row control. Every relation is still checked on every row and a failure names the size and the relation.

## Known Stubs

None.

## Threat Flags

None. No new endpoint, auth path or file access; the row data is read only by tests and, in 05-07, by the catalogue.

## Issues Encountered

None beyond the deviation above. No filed tech-debt item.

## Verification

- `make test PYTEST_ARGS="tests/test_tables.py tests/test_tables_second_entry.py -q -n0 --no-cov"`: 1252 passed.
- `make lint-imports`: 9 kept, 0 broken.
- `make verify`: `2795 passed in 93.35s`, coverage 97.52% (required 96.0%).
- `git status --porcelain`: no PNG, PDF or text render staged; renders stayed in the session scratch directory.

## Self-Check: PASSED

- `src/screw/tables/iso4032.py`, `tests/data/owner/iso4032.tsv`, this file: present.
- Commits 66bf25b and f4eb57d are ancestors of HEAD.
