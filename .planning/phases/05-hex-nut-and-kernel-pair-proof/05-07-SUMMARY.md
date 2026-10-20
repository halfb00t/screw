---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 07
subsystem: presets
tags: [presets, iso4032, gost, hex-nut, catalogue, exact-match, citation]
requires:
  - phase: 05-06
    provides: "tables/iso4032.py NUTS (14 cited GOST ISO 4032-2014 rows) and Source.document()"
  - phase: 05-04
    provides: "NutParams with the frozen s 10.0 and m 5.2 defaults"
provides:
  - "tables/presets.py NutPresetRow, nut_catalogue(), expand_nut(id): 14 ids iso4032:<size>, no M7"
  - "calc/presets.py NUT_AXES, match_nut, nut_designation_for, nut_row_values, nut_notes; nut branches of catalogue_document and expand"
  - "the nut info document reads preset exact, designation, six cited values and the grade note for a nut that is a row"
  - "NUT_NO_ROW_WARNING reworded to name GOST ISO 4032-2014 (ISO 4032:2012), raised only when no row matches"
affects: [05-09, 05-10]
actuals:
  tokens: 3900
  tasks: 2
  commits: 3
plan_head_before: 05df5a1a566b27fe3fa7887a0b36cfed13d1f209
plan_head_after: 6c2187d4c97fa810e7fef3c3c9a28f37dbb295b9
tech-stack:
  added: []
  patterns:
    - "per-kind catalogue rows in tables/presets.py, joined to ISO 262 sizes by label, served through one document type"
    - "a cited label is built from Source.document(), so a GOST row and an ISO row each name the text actually read"
key-files:
  created: []
  modified:
    - src/screw/tables/presets.py
    - src/screw/calc/presets.py
    - src/screw/calc/__init__.py
    - tests/test_presets.py
    - tests/test_parity.py
    - tests/test_calc.py
    - docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md
key-decisions:
  - "The nut designation is the owner's ruled form: `Hexagon regular nut GOST ISO 4032 - M6`, decimal comma, no left-hand form, ASCII hyphen, property class left out"
  - "The cited rows sit after across_corners in the Nut group, as the plan words it, so the m row follows the six cited values"
requirements-completed: []
requirements-partial:
  - id: TYPE-03
    note: "the nut catalogue and picker ship; the nut panel's pair rows and the chamfer rows are 05-09 to 05-13, so it is not marked complete"
  - id: INFO-01
    note: "a nut that is a row reports its cited values and designation; the pair numbers on the panel are 05-09, so it is not marked complete"
status: complete
---

# Phase 5 Plan 07: The ISO 4032 nut catalogue and exact match Summary

A user can pick any of the 14 GOST ISO 4032-2014 sizes (`ISO 4032 M6`, second-choice sizes bracketed) on the API, the CLI and the page, and a nut that equals a row exactly reads its id, designation, six cited values labelled with the table they came from, and the product-grade note.

## What was done

**Precondition.** `05-OWNER-READS.md` `## Designation` records the owner's ruling (2026-10-20, option a): `Hexagon regular nut GOST ISO 4032 - M6`, decimal comma, left-hand form `none`, ASCII hyphen, property class left out. Nothing was PENDING, so no checkpoint.

**Task 1, catalogue (9142e40).** `NutPresetRow`, `_nut_row`, `nut_catalogue()` and `expand_nut()` in `tables/presets.py`; the 14 `NUTS` rows joined to ISO 262 sizes by label and sorted by diameter. Ids are `iso4032:<size>`, displays exactly `ISO 4032 <size>` or `ISO 4032 (<size>)` (M3.5, M14, M18), pickers `[ISO 4032, <size>]`, fields d, pitch, s and `m` = the row's `m_max` (read 1, option a). `calc/presets.py` serves the nut document from these (`NUT_AXES = ["Standard", "Size"]`), replacing the 05-04 empty one. The picker code in `app.js` is generic over `axes` and `picker`, so two axes need no JS change. The parity test now asserts non-empty rows for every kind.

**Task 2, exact match (b0a1d35).** `match_nut` compares d, pitch, s and m with exact float equality (never clearance, never left_hand). `nut_row_values` gives `s_min`, `e_min`, `m_max`, `m_min`, `mw_min`, `dw_min` in group Nut, labelled `<sense> (GOST ISO 4032-2014 (ISO 4032:2012) Table N)`; `c` and `da` are stored but not reported (D-15). `nut_notes` gives the single grade note (A to M16, B above). `_row_value` now builds its label from `source.document()`; every Phase 4 label is byte-identical (the existing bolt label tests pass unchanged). `_nut` splices the cited rows after `across_corners` and keeps `NUT_NO_ROW_WARNING` only when there is no match; the warning is reworded to name the GOST document and is pinned as a literal in a test.

**Tests.** Catalogue: axes, 14 ids with no M7, per-row display/picker/designation/citation (Table 2 for the bracketed sizes), `expand` (case-sensitive, M7 None, a bolt id None), fields are `NutParams` fields and exclude clearance and left_hand, CLI document. Info: the default M6 nut is exact with the literal labels; clearance 0.25 and left_hand True still match (left-hand designation None); `nextafter(5.2, inf)` reads custom with the pinned warning and no cited rows; an M7 nut reads custom; all 14 rows read back as their own row with the right table and grade note; the M16/M18 grade boundary.

## Task commits

| Task | Commit | Message |
| ---- | ------ | ------- |
| 1 | 9142e40 | feat(presets): add the ISO 4032 nut catalogue read from GOST ISO 4032-2014 |
| 2 | b0a1d35 | feat(nut): report the GOST ISO 4032-2014 row a nut matches exactly |
| - | 6c2187d | docs(tech_debt): note the nut no-row warning now names GOST ISO 4032-2014 |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] mypy rejected `NutParams(**fields)` in the new tests**
- **Found during:** Task 2 verification
- **Issue:** `dict[str, float]` unpacked into a model whose last keyword is `bool`.
- **Fix:** built the models with `NutParams.model_validate({**fields, "clearance": 0.1})`, as the existing preset tests do.
- **Files modified:** `tests/test_calc.py`
- **Commit:** b0a1d35 (the failed run left nothing committed)

**2. [Rule 1 - Stale reference] The tech-debt item named the old warning**
- **Found during:** Task 2 close-out
- **Issue:** `docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md` listed `NUT_NO_ROW_WARNING` as naming ISO 4032:2023, false after this plan.
- **Fix:** one line updated.
- **Commit:** 6c2187d

**3. [Judgement] The `NUT_NO_ROW_WARNING` literal is split over two source lines.** The acceptance criterion greps one line `NUT_NO_ROW_WARNING = "no GOST ... not reported"`; that line is 108 characters, over ruff's 100 (E501). The string is identical (implicit concatenation) and a test pins it as a literal, so the intent holds; the grep as written does not.

**4. [Judgement] Tests written with the implementation, not first.** The plan marks both tasks `tdd="true"` but fixes one commit per task; I wrote the tests beside the code in each commit and ran them, without a separate RED commit or a recorded failing run.

**Total deviations:** 2 auto-fixed, 2 judgement calls. **Impact:** none on behaviour.

## Known Stubs

None.

## Threat Flags

None. No new endpoint, auth path or file access; the id is looked up in a closed, case-sensitive dict (T-05-16) and the match is exact equality only with a one-ulp test (T-05-17).

## Issues Encountered

- `.venv/bin/mypy` has a stale shebang path (`/Users/halfb00t/...`); `make` calls `python -m mypy`, so the gate is unaffected. Not fixed (outside scope).
- The plan puts the six cited rows before the `m` row in group Nut (after `across_corners`). I followed it literally; plan 05-09 may want them after `m`.
- No tech-debt item filed.

## Verification

- `make test PYTEST_ARGS="tests/test_presets.py tests/test_parity.py -q -n0 --no-cov"`: 369 passed.
- `make test PYTEST_ARGS="tests/test_calc.py -q -n0 --no-cov -k nut"`: 26 passed.
- `.venv/bin/screw presets nut`: axes `[Standard, Size]`, 14 rows, all displays match the plan's regex; `iso4032:M6` present.
- `.venv/bin/screw info nut --clearance 0.1`: `"status": "exact"`, `"id": "iso4032:M6"`.
- `make verify`: `2833 passed in 92.96s`, coverage 97.62% (required 96.0%); the pre-commit hook ran it again on every commit and passed.

## Self-Check: PASSED

- `src/screw/tables/presets.py`, `src/screw/calc/presets.py`, `src/screw/calc/__init__.py`, `tests/test_presets.py`, `tests/test_parity.py`, `tests/test_calc.py`: present and modified.
- Commits 9142e40, b0a1d35 and 6c2187d are ancestors of HEAD.
