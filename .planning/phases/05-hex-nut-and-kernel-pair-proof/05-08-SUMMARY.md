---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 08
subsystem: tables
tags: [tables, gost24705, gost16093, iso724, iso965, double-entry, derived-limits, decimal, thread-maths]
requires:
  - phase: 05-06
    provides: "Source.document(), ADOPTED_ISO, the double-entry diff and the unverified scans"
  - phase: 05-02
    provides: "05-OWNER-READS.md reads 4 and 5 (GOST 24705-2004 and GOST 16093-2004, L14) and ruling R13"
provides:
  - "tables/iso724.py BASIC: d, d2, d1 of the 15 coarse ISO 262 sizes from GOST 24705-2004 Table 1"
  - "tables/gost16093.py TOLERANCES: the 72 printed es, EI, Td, TD1, Td2, TD2 values of the 12 coarse pitches"
  - "tables/gost16093.py derive_limits, BOLT_LIMITS (6g) and NUT_LIMITS (6H): 15 rows each, exact Decimal sums, each row carrying its addends' Sources and citation()"
  - "calc/thread.py pitch_diameter(d, pitch) and basic_minor_diameter(d, pitch): the ISO 68-1 basic-profile formulas (R13)"
  - "tests/data/owner/iso724.tsv (15 rows) and gost16093.tsv (72 rows), both diffed cell by cell in make verify"
affects: [05-09]
actuals:
  tokens: 23000
  tasks: 2
  commits: 3
plan_head_before: d32d5a298ac42139370fbba16715b6d81b4dac42
plan_head_after: 21c6135b8b12fc5ab8d856548540cb98ab304ee4
tech-stack:
  added: []
  patterns:
    - "a limit is the exact Decimal sum of printed addends (Decimal of each stored literal's repr, unit converted exactly, float once), never float arithmetic and never a tolerance formula"
    - "a derived row carries the Sources of its addends and cites `derived: ` plus their distinct citations, so both GOST texts are named"
    - "a size missing a basic value or a printed term gets no limits row, never a computed one"
key-files:
  created:
    - src/screw/tables/iso724.py
    - src/screw/tables/gost16093.py
    - tests/data/owner/iso724.tsv
    - tests/data/owner/gost16093.tsv
  modified:
    - src/screw/tables/rows.py
    - src/screw/calc/thread.py
    - tests/test_tables.py
    - tests/test_tables_second_entry.py
    - tests/test_thread_maths.py
key-decisions:
  - "Limits are derived per L14 from printed values only: 6g d_max = d + es(g), d_min = d_max - Td(6), d2_max = d2 + es(g), d2_min = d2_max - Td2(6); 6H D1_min = D1 + EI(H), D1_max = D1_min + TD1(6), D2_min = D2 + EI(H), D2_max = D2_min + TD2(6); read 5 confirmed these addends"
  - "Range tables read as over X up to Y; no shipped size lies on a bound, and a test pins the convention on a planted size"
  - "Tolerance.value is the printed integer in micrometres (unit stored as um); the 15 coarse sizes use 12 pitches, so Tables 5 and 6 carry one range per pitch"
requirements-completed: []
requirements-partial:
  - id: INFO-01
    note: "the basic-profile formulas and the cited basic diameters exist; the panel's thread rows are 05-09, so it is not marked complete"
  - id: INFO-02
    note: "the derived 6g and 6H limits ship cited and double-entered; the limits group on the panel is 05-09, so it is not marked complete"
status: complete
---

# Phase 5 Plan 08: GOST basic diameters, deviations and tolerances, and the derived 6g and 6H limits Summary

Every number the panel's thread rows and limits group will print now traces to a printed, cited, double-entered GOST value or to the ISO 68-1 basic profile: the 15 coarse basic diameters (GOST 24705-2004), 72 printed deviations and tolerances (GOST 16093-2004), and 15 6g plus 15 6H limit rows derived from them by exact decimal addition.

## What was done

**Precondition.** Read 4 and read 5 in `05-OWNER-READS.md` are answered (both tables print values; no needed value is formula-only), both PDFs match their recorded sha256, and both owner copies carry the recorded headers.

**Task 1, basic diameters (544290f).** `pitch_diameter` (d - 3H/4) and `basic_minor_diameter` (d - 5H/4) in `calc/thread.py`, kernel-free. `BasicDiameters` in `rows.py`; `tables/iso724.py` `BASIC` holds the 15 coarse ISO 262 sizes M2 to M20 (including M7), transcribed from the rendered pages of Table 1 before the owner copy was opened. The diff against `iso724.tsv` is empty. Tests: the two formulas exactly, `basic_minor_diameter` equal to the existing `d - 2 * thread_depth` to 1e-15, 15 rows with ISO 262's d and pitch, the citation, and the R13 agreement test (every printed d2 and d1 equals the formula rounded to three decimals).

**Task 2, deviations, tolerances and limits (21c6135).** `Tolerance`, `BoltLimits`, `NutLimits` (with `citation()`) in `rows.py`; `"GOST 16093-2004"` added to `ADOPTED_ISO`. `tables/gost16093.py` `TOLERANCES` was transcribed from the rendered pages 13 to 18 (Tables 3 to 7) before the owner copy was opened: es of g and EI of H (Table 7), Td(6) (Table 3), TD1(6) (Table 4), Td2(6) (Table 5), TD2(6) (Table 6), at the 12 coarse pitches, Tables 5 and 6 at each size's own diameter range. `derive_limits(basic, tolerances)` builds `BOLT_LIMITS` and `NUT_LIMITS` (15 rows each) by `Decimal` addition. The diff against `gost16093.tsv` (72 rows) is empty.

**Tests.** Diff: both files added to `_SHAPE` and `shipped()`, non-vacuous counts 15 and 72, a changed cell named by file, key, column and both values, and numeric key columns keyed by value not spelling. Tables: 72 unique verified terms; one limits row per size with ISO 262's pitch; every limit equals an independently walked Decimal sum (the repr of each limit round-trips to the exact sum); citation starts `derived: ` and names both documents, and its four addends are listed in order; relation tests per size (d_min < d_max < d, d2_min < d2_max < d2, D1 <= D1_min < D1_max, D2 <= D2_min < D2_max) with a planted row reported by size and relation; a planted Td2 term at pitch 1 moves exactly M6 and M7 bolt `d2_min`; a missing es at pitch 1.75 drops only M12's 6g row, a missing TD2 at pitch 2.5 drops only M18 and M20's 6H row; the over-X-up-to-Y bound convention. Both new modules are in the unverified scans.

## Task commits

| Task | Commit | Message |
| ---- | ------ | ------- |
| 1 | 544290f | feat(tables): ship the GOST 24705-2004 basic diameters, double-entered, and the basic-profile formulas |
| - | abd4723 | docs(05): record the iso724 owner copy regenerated with M7 after the 05-08 diff |
| 2 | 21c6135 | feat(tables): ship the GOST 16093-2004 deviations and tolerances and the derived 6g and 6H limits |

## Double-entry record

- **Task 1.** The first executor's cell diff found that the owner copy had no M7 row (the generator keyed only the 14 GOST ISO 4032 sizes) and stopped to the owner. The owner ruled: add `7` to the generator's key list and rerun by the same text-layer route, no number edited (recorded in `05-OWNER-READS.md`, abd4723). This continuation re-checked both PDF sha256 values, copied the regenerated `iso724.tsv` byte for byte (`cmp` exit 0), and the diff over all 15 rows is empty. **Independence caveat for M7 only:** the first executor's M7 values were reported to the orchestrating session before the rerun, so for that one row the owner copy was generated after the other copy was known (also recorded in `05-OWNER-READS.md`). The other 14 rows keep the independence the plan asks for. Also, the Task 1 transcription predates this continuation; the previous executor had read the old 14-row copy only in the diff step, after the transcription was written.
- **Task 2.** The transcription of all 72 terms was written to `gost16093.py` from the rendered page images before any data row of `gost16093.tsv` was read (`head -1` only before). The diff was empty on the first run; no disagreement, no owner stop.
- Both copies read the same download-site reproductions (PDF Title begins "Скачать"), so the diff cannot catch an error in them (L14, the L13 caveat). The sources stay UNVERIFIED.

## Deviations from Plan

None - plan executed exactly as written. (The M7 stop and resume above is the checkpoint route the plan prescribes, not a deviation.)

## Known Stubs

None.

## Threat Flags

None. The new surface is static tables and two pure functions; no endpoint, auth path or file access.

## Verification

`make verify`: ruff, mypy `--strict`, import-boundary contracts, unfinished-work scan, pytest; final result line `2895 passed in 94.76s`, coverage 97.76% (floor 96%). Both owner-copy diffs empty; `cmp` of each copy against the owner directory exits 0.

## Self-Check: PASSED

Files found: `src/screw/tables/iso724.py`, `src/screw/tables/gost16093.py`, `tests/data/owner/iso724.tsv`, `tests/data/owner/gost16093.tsv`. Commits found on HEAD: 544290f, abd4723, 21c6135.
