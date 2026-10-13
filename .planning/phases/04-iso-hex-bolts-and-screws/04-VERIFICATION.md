---
phase: 04-iso-hex-bolts-and-screws
verified: 2026-10-13T09:00:00Z
status: passed
score: 12/12 must-haves verified
covered_files:
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-01-PLAN.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-01-SUMMARY.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-02-PLAN.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-02-SUMMARY.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-03-PLAN.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-03-SUMMARY.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-04-PLAN.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-04-SUMMARY.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-05-PLAN.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-05-SUMMARY.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-06-PLAN.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-06-SUMMARY.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-07-PLAN.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-07-SUMMARY.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-08-PLAN.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-08-SUMMARY.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-09-PLAN.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-09-SUMMARY.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-10-PLAN.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-10-SUMMARY.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-11-PLAN.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-11-SUMMARY.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-12-PLAN.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-12-SUMMARY.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-13-PLAN.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-13-SUMMARY.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-14-PLAN.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-14-SUMMARY.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-15-PLAN.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-15-SUMMARY.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-16-PLAN.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-16-SUMMARY.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-17-PLAN.md"
  - ".planning/phases/04-iso-hex-bolts-and-screws/04-17-SUMMARY.md"
  - "bench/head_fuse.py"
  - "docs/architecture/decision_log.md"
  - "pyproject.toml"
  - "src/screw/app.py"
  - "src/screw/calc/__init__.py"
  - "src/screw/calc/presets.py"
  - "src/screw/calc/thread.py"
  - "src/screw/cli.py"
  - "src/screw/params.py"
  - "src/screw/solid/__init__.py"
  - "src/screw/solid/bolt.py"
  - "src/screw/static/app.js"
  - "src/screw/static/index.html"
  - "src/screw/static/style.css"
  - "src/screw/tables/iso262.py"
  - "src/screw/tables/iso4014.py"
  - "src/screw/tables/iso4017.py"
  - "src/screw/tables/presets.py"
  - "src/screw/tables/rows.py"
  - "tests/test_api.py"
  - "tests/test_calc.py"
  - "tests/test_import_boundaries.py"
  - "tests/test_parity.py"
  - "tests/test_presets.py"
  - "tests/test_tables.py"
  - "tests/test_tables_second_entry.py"
covered_digest: "v3:sha256:50ffa18d09a6bdc2350f1846d8082f1808e25ef7d79a3404d5b36fea34b3530a"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 11/12
  previous_body_status: human_needed
  gaps_closed:
    - "Truth 12 (G-04-5 browser half, plan 04-17 truths 2 to 4, verification: backstop): was PRESENT_BEHAVIOR_UNVERIFIED; the owner's browser re-run is recorded in 04-UAT.md test 7 (result: pass), and test 9 (light theme, under 820px) is pass. Evidence is the owner's recorded UAT result, carried forward; src/screw/static/style.css and index.html/app.js are byte-identical to the merged phase"
    - "Previous human item 2 (rulings on eight open review findings): 04-UAT.md test 8 (result: pass) is the owner's ruling. The disposition rows were not rewritten (observation, not a gap)"
    - "Previous human item 3 (light theme and narrow layout of plans 04-13 and 04-16): 04-UAT.md test 9 (result: pass)"
  gaps_remaining: []
  regressions: []
  what_changed: "Nothing in src/, tests/ or web/ since the phase was squash-merged as e8df305 (git diff --stat e8df305..HEAD, .planning excluded, touches only bench/RESULTS.md and docs/architecture/decision_log.md). The previous report went stale because the 17 PLAN and 17 SUMMARY files were finished after that run. Re-run at 7634830 on main: the gate is green again and the three human items are closed by the owner in UAT tests 7, 8, 9"
---

# Phase 4: ISO Hex Bolts and Screws Verification Report

**Phase Goal:** A user picks "M6 x 20, ISO 4017" (or an ISO 4014 size and length) and gets a hex head bolt or screw whose explicit millimetre fields were filled from a cited, tested table row, with an info panel whose every number traces to a field or a row.
**Verified:** 2026-10-13T09:00:00Z, at `main` `7634830` (branch `docs/phase-04-verification-refresh`)
**Status:** passed
**Re-verification:** Yes. Previous report: verified 2026-10-12T20:30:00Z at `f39b2c2`, body `human_needed`, frontmatter `passed`, 11/12. It is stale because the 17 PLAN and 17 SUMMARY files changed after it. Phase merged as `e8df305` (PR #12).

## Verdict

The goal is achieved. No must-have failed, no blocker was found, and the one truth the previous report held back (truth 12, the browser half of gap G-04-5) now has the owner's recorded browser result. All 12 requirement IDs are accounted for.

What I checked myself, not read from SUMMARYs:

- `make verify` run once from the repo root at `7634830`: ruff `All checks passed!`; mypy `--strict` `Success: no issues found in 59 source files`; import-linter `Contracts: 9 kept, 0 broken.` (including "The parameters never consult a table KEPT", "Tables are a leaf KEPT", "The thread maths stays free of the CAD kernel KEPT", "Only the solid package imports the CAD kernel KEPT"); unfinished-work scan clean; pytest `2637 passed in 69.59s`; `Required test coverage of 96.0% reached. Total coverage: 97.33%`; exit 0. This agrees with the orchestrator's earlier `make test` (2637 passed, 97.33%).
- `git diff --stat e8df305..HEAD -- . ':(exclude).planning'` shows only `bench/RESULTS.md` (+59) and `docs/architecture/decision_log.md` (+19). `src/`, `tests/`, `web/` are byte-identical to the merged phase, so everything the previous report read in the code still holds.
- `src/screw/static/style.css` lines 169 to 195 read: `#dims dl` is the auto-fill grid; `#dims div { display: flex; flex-wrap: wrap; justify-content: space-between; gap: .75rem; padding: .15rem 0; border-bottom: 1px dashed var(--line); }`, `#dims dt { color: var(--muted); flex: 1 1 50%; }`, `#dims dd { margin: 0 0 0 auto; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }`. No `white-space`, `overflow` or `text-overflow` under `#dims`.
- `tests/test_parity.py`: `STYLE_CSS = (STATIC / "style.css").read_text()` (line 40), `INFO_ROW_RULES` (line 127), `_info_row_problems` (line 171), `test_an_info_row_drops_a_long_value_whole_under_its_label_instead_of_into_the_next_cell` (line 504), `test_the_info_row_check_has_teeth` (line 516, includes a comment-only control at line 539). Both are inside the green 2637.
- Live API (TestClient on the real app): `/api/presets?kind=bolt` returns 294 rows (`axes`, `rows`); row 0 is `iso4017:M2x4`, `fields` = `d 2.0, pitch 0.4, length 4.0, s 4.0, k 1.4, thread_length 4.0`, with `citation` "ISO 262:2023 Table 1, column Coarse; ISO 4017:2022 Table 1, column M2". `/api/bolt/info?d=6&pitch=1&length=20&s=10&k=4&thread_length=20` returns designation "Hexagon head screw ISO 4017 - M6 x 20" (no property class) and `preset` `{status: exact, id: iso4017:M6x20, display: ISO 4017 M6 × 20}`; the same document with `length=21&thread_length=21` returns `{status: custom, id: None}`.
- Tables: `src/screw/tables/rows.py` defines `Source` as `@dataclass(frozen=True, slots=True, kw_only=True)` with required `standard, edition, table, column, status`, and every row dataclass is kw_only with no defaults, so a row without `source=` is a `mypy --strict` error. Row modules call `source=_source("Table 1", "M2")` on each row. `tests/test_tables.py::test_no_row_in_the_tree_is_unverified` plus `test_the_text_scan_sees_an_unverified_row` and `test_the_runtime_check_sees_an_unverified_row` hold the gate against UNVERIFIED rows; `test_a_row_without_source_fails_mypy_strict_naming_source...` holds TABL-02.
- Fingerprint recomputed through the CLI over the same covered set the previous report used (the 17 PLAN and 17 SUMMARY files, which the CLI adds on its own, plus the 26 implementation and test files the previous report named). `covered_files` is identical to the previous list (60 entries); the digest changed because the plan and summary files and `decision_log.md` changed. Both fields copied verbatim from the CLI output.

## Goal Achievement

### Observable Truths

| # | Truth (source) | Status | Evidence |
|---|----------------|--------|----------|
| 1 | A user can pick standard + size + length across M2 to M20 per ISO 262 (second-choice bracketed, coarse only) on the API and the CLI and get an ISO 4014 bolt or ISO 4017 screw up to 200 mm; parity is green (SC1; TYPE-01, TYPE-02, TABL-01, TABL-05) | ✓ VERIFIED | 294-row catalogue served live this run; `tests/test_presets.py` round-trips every row; parity and CLI tests inside the green 2637; code byte-identical to the previous report |
| 2 | The UI offers the same pick and writes the row's mm fields (SC1, UI half) | ✓ VERIFIED | `app.js`/`index.html` byte-identical; source tests green; UAT test 1 `pass` |
| 3 | The preset fills explicit mm fields only: the link carries mm fields, the preset id is metadata, opening the URL rebuilds the part without consulting a table; `thread_length` is filled by the preset and stays editable (SC2; TABL-01, THRD-03) | ✓ VERIFIED | live `fields` object carries only mm values incl. `thread_length`; import contract "The parameters never consult a table" KEPT this run; `-I` runtime probes in `tests/test_import_boundaries.py` |
| 4 | The designation line shows the ISO designation without a property class (SC3, second clause; TABL-07) | ✓ VERIFIED | live: "Hexagon head screw ISO 4017 - M6 x 20"; `tests/test_tables.py::test_the_row_citation_lists_each_source_once_and_the_designation_has_no_class` |
| 5 | The badge reads "matches ISO 4017 M6 x 20" while the fields equal the row and "custom, based on ISO 4017 M6 x 20" once any field is edited (SC3, first clause; TABL-06) | ✓ VERIFIED | live: `exact` for the row, `custom` after editing length; page copy confirmed by UAT test 1 `pass` |
| 6 | Every table row carries a typed `Source`; one pure-data test per row generated from the table; an UNVERIFIED row is refused by the gate (SC4; TABL-02, TABL-03, TABL-04) | ✓ VERIFIED | `rows.py` kw_only dataclasses with required `source`; per-row (`test_row_relations`), per-head (`test_head_relations`), per-cell tests and the unverified gate with planted-row controls, all inside the green 2637. Minor, as before: ISO 262 `Size`/`ThreadBand` rows have no 1:1 parametrized test |
| 7 | The info panel numbers come from kernel-free maths, each traceable to an mm field or a cited, tested row; an uncomputable value is a warning and no number; any volume is the closed form; the ISO wrench size note where it differs from the DIN (SC5; INFO-03, INFO-05) | ✓ VERIFIED | `calc/__init__.py::_bolt` unchanged; import-linter "thread maths stays free of the CAD kernel" and "...of the logger" KEPT this run; `Volume (closed form)` row; calc tests inside the green 2637 |
| 8 | The bolt the preset names builds as one valid solid with plain planar ends, gated by the THRD-04 postcondition (TYPE-01, TYPE-02 geometry) | ✓ VERIFIED | `solid/*` byte-identical; solid tests with positive controls inside the 2637; "Only the solid package imports the CAD kernel" KEPT |
| 9 | The info document carries a required `downloads` member from the one `download_refusal` rule; `/api/bolt/info`, `screw info bolt`, the model route and `screw export` agree; the fine-STL warning stays; the pinned 62 is unchanged (G-04-3, plan 04-15) | ✓ VERIFIED | unchanged code; catalogue-wide agreement tests and `test_the_fine_stl_refused_presets_are_counted` inside the green 2637 |
| 10 | The page builds both download links from `info.downloads`, offers `Download STL (preview)` with the refusal sentence as its title where the fine STL is refused, keeps `Download STEP`, names no quality, writes nothing to the hash; in a real browser M8 / 70 saves an STL (G-04-3, plan 04-16) | ✓ VERIFIED | source pins pass; `app.js` byte-identical; browser half is the owner's UAT test 4 `pass`; light theme and narrow pass is UAT test 9 `pass` |
| 11 | `style.css` lays out each `#dims div` as a wrapping flex row, `#dims dt` as `flex: 1 1 50%`, `#dims dd` as `margin: 0 0 0 auto` with `overflow-wrap: anywhere` and no `white-space`; no `#dims` rule keeps text on one line, clips or ellipsizes; a source pin fails the gate if the rules change and a second test shows the check flags the old rules (G-04-5, plan 04-17 truth 1) | ✓ VERIFIED | rules read verbatim from `style.css` this run (see Verdict); both pin tests green inside `make verify`; known limit WR-04: the pin matches selectors exactly |
| 12 | In a real browser, light and dark, 720 and 1920 px, ISO 4017 M8 x 70's four long values sit whole under their label inside their own cell, labels wrap as phrases (at most 4 lines), short values stay beside their labels, nothing is rounded or cut, the 25-character value breaks only before `mm` (G-04-5, plan 04-17 truths 2 to 4, `verification: backstop`) | ✓ VERIFIED (owner UAT) | Present and wired (truth 11; the `dd` text keeps a plain space before the unit). The backstop evidence is the owner's browser re-run, `04-UAT.md` test 7 `result: pass`, with test 9 `pass` for the light theme and under 820px. `style.css` and `app.js` are byte-identical to what the previous report probed (headless Chrome, 0 px overflow at 720 and 1920 px, both themes). Provenance: UAT 7 carries a note that the verifier's probe was evidence for the owner; the recorded result is the owner's `pass`, and per the dispatch it is carried forward, not downgraded. Not re-run in a browser by this verification |

**Score:** 12/12 truths verified (0 present, behavior-unverified).

### Judgments

1. **L02 on the info-panel layout.** The layout moves the value and never the number: no `text-overflow`, `overflow`, `white-space: nowrap` or `max-width` under `#dims`. The one text-splitting rule, `overflow-wrap: anywhere` on `dd`, fires only for a value wider than a whole track and the space before the unit is the first break it takes. Prohibition holds.
2. **UI-SPEC extension rule 4 (no off-scale length).** `50%` is a proportion like the sheet's `1fr`/`100%`; `.75rem` is the existing `md` step. Holds, as in the previous report.
3. **Regression guard strength (WR-04).** The `style.css` pin proves the shipped sheet; a more specific future selector could walk past it. This lowers the value of truth 11 as a future guard, not the correctness of the shipped CSS. The owner's UAT test 8 ruled on it (`pass`); no disposition per finding was written (see Observations).
4. **REQUIREMENTS.md.** All 12 IDs are ticked `[x]` and the traceability table reads `Complete` for each (lines 122 to 146). Code proves all 12. The previous report's note that five IDs were still pending is superseded. Caveat unchanged: TABL-04's text also names ISO 4032, 724 and 965-2 (Phase 5); the tick is the gate plus the Phase 4 standards.
5. **Security.** `04-SECURITY.md`: `status: verified`, `threats_open: 0`.

### Observations (not must-have gaps)

- `04-REVIEW-DISPOSITION.md` still shows 8 findings with `disposition: open` (WR-03, IN-05, IN-06, IN-07, IN-08, WR-04, IN-09, IN-10) although `04-UAT.md` test 8 records `pass`. The owner typed `pass` without naming a disposition per finding, and the rows were not rewritten after the ruling. Under CLAUDE.md a deferral needs sign-off and a `docs/tech_debt/` item; none of the eight is a blocker (the report classes them warning or info), and none touches a must-have, but the disposition file and UAT disagree. The orchestrator should either rewrite the rows (fixed, tech debt, skipped) or accept that the `pass` covers them. No debt item was filed by this verification.
- `04-UAT.md` summary block reads `passed: 7, issues: 2`: tests 3 and 5 stay `issue` in the per-test records while their gaps G-04-3 and G-04-5 are `status: resolved` (plans 04-16 and 04-17, re-run by tests 4 and 7). This is the file's convention, not a failure.
- `src/screw/calc/thread.py` `FINE_STL_ROWS` INTERIM caps still refuse the fine STL for 62 of the 186 ISO 4017 presets; owner-accepted (D-21, L13), handled by the preview link, re-swept in Phase 7.

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|--------------|----------|
| 1 | Tip chamfer and under-head fillet | Phase 5 | ROADMAP Phase 5, THRD-05 and its ISO 4753 precondition |
| 2 | Printability warning for small sizes | Phase 6 | INFO-04 maps to Phase 6 |
| 3 | Measured per-size build caps and a re-swept export budget (cause of the 62 refused fine STLs) | Phase 7 | OPER-01 to OPER-03 and the INTERIM markers in `calc/thread.py` |
| 4 | Preview quality named in the saved file name | Phase 5 (with FRNT-06) | `docs/ideas/2026-10-12-preview-stl-download-names-its-quality.md` |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/screw/tables/rows.py` | typed `Source`, kw_only row types | ✓ VERIFIED | read this run; required `source`, `status: Literal["verified","unverified"]` |
| `src/screw/tables/iso4017.py`, `iso4014.py`, `iso262.py` | cited rows | ✓ VERIFIED | every row passes `source=_source(Table, column)`; 19, 34 and 15 `source=` sites |
| `src/screw/tables/presets.py`, `src/screw/calc/presets.py` | catalogue expansion, preset status | ✓ VERIFIED | 294 rows served live; exact/custom badge status live |
| `src/screw/calc/__init__.py` | info panel from fields and rows | ✓ VERIFIED | unchanged; contracts KEPT |
| `src/screw/params.py`, `solid/bolt.py` | `thread_length`, hex head builder | ✓ VERIFIED | unchanged; tests green |
| `src/screw/app.py`, `cli.py` | API and CLI parity | ✓ VERIFIED | unchanged; parity tests green |
| `src/screw/static/style.css` | wrapping info row, `flex: 1 1 50%` | ✓ VERIFIED | read this run |
| `src/screw/static/app.js`, `index.html` | picker, badge, downloads from `info.downloads` | ✓ VERIFIED | byte-identical; UAT 1, 4, 7, 9 `pass` |
| `tests/test_tables.py`, `test_presets.py`, `test_calc.py`, `test_api.py`, `test_parity.py`, `test_import_boundaries.py`, `test_tables_second_entry.py` | tests with teeth | ✓ VERIFIED | all inside the green 2637 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/test_parity.py` | `src/screw/static/style.css` | `STYLE_CSS` read from `STATIC`, `#dims` declarations compared after comments are stripped | WIRED | line 40; comment-only control at line 539 |
| `style.css` | `app.js renderInfo` | plain space between number and unit is the first break `overflow-wrap` takes | WIRED | unchanged since the previous report |
| `calc._bolt` | `download_refusal` | `_downloads(p)` | WIRED | unchanged |
| `app.js update()` | `setDownloads` | `setDownloads(q, info.downloads)` | WIRED | unchanged; UAT 4 pass |
| `params` / `calc.thread` | `tables` | none allowed | NOT IMPORTED (as required) | contracts: 9 kept, 0 broken |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| Info panel `dd` | `row.value`, `row.unit` | `/api/bolt/info` rows from the user's fields and cited rows | yes (document read live for M6 x 20) | ✓ FLOWING |
| Download links | `info.downloads` | `download_refusal(p, fmt, quality)` | yes (62 of 294 rows refuse fine STL) | ✓ FLOWING |
| Picker, badge | `/api/presets`, `PresetMatch` | stored `Source`-carrying rows | yes (294 rows; exact/custom live) | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| The gate | `make verify` | ruff clean, mypy 59 files clean, contracts 9 kept 0 broken, 2637 passed, coverage 97.33%, exit 0 | ✓ PASS |
| Catalogue served | TestClient `GET /api/presets?kind=bolt` | 294 rows, mm `fields`, citation | ✓ PASS |
| Designation and badge | TestClient `GET /api/bolt/info` for M6 x 20 and for length 21 | designation without class; `exact` then `custom` | ✓ PASS |
| Browser layout | not re-run here | rests on UAT tests 7 and 9, owner `pass`; code byte-identical to the probed commit | carried forward |

### Probe Execution

Step 7c: SKIPPED. No PLAN or SUMMARY of this phase declares a probe script and `scripts/*/tests/probe-*.sh` does not exist.

### Requirements Coverage

Every ID in the 17 PLAN frontmatters is accounted for and equals the ROADMAP's list of twelve. No ID is orphaned: REQUIREMENTS.md maps exactly these twelve to Phase 4 and no further ID. Plan-frontmatter `requirements:` lines were collected from all 17 plans (e.g. 04-17 declares INFO-03; 04-03 declares TYPE-01, TYPE-02, INFO-03).

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| THRD-03 | 04-04, 04-05, 04-06, 04-10, 04-12 | `thread_length` explicit mm; 4017 fills full length, 4014 fills `b`; editable | ✓ SATISFIED | truth 3; `[x]`/Complete |
| TYPE-01 | 04-03, 04-04, 04-08, 04-10, 04-11, 04-14 | ISO 4014 hex bolt (amended, D-02) | ✓ SATISFIED | truths 1, 7, 8; `[x]`/Complete |
| TYPE-02 | 04-03, 04-09, 04-15, 04-16 | ISO 4017 hex screw to 200 mm | ✓ SATISFIED | truths 1, 8, 9, 10; `[x]`/Complete |
| TABL-01 | 04-12, 04-13, 04-15, 04-16 | pick standard + size + length; mm fields only | ✓ SATISFIED | truths 1 to 3, 9, 10; `[x]`/Complete |
| TABL-02 | 04-07, 04-09, 04-10 | typed `Source` on every row | ✓ SATISFIED | truth 6; `rows.py` read |
| TABL-03 | 04-07, 04-09, 04-10 | one pure-data test per row | ✓ SATISFIED | truth 6 |
| TABL-04 | 04-01, 04-07, 04-09, 04-10, 04-14 | purchased-copy rule, UNVERIFIED gate | ✓ SATISFIED for the Phase 4 standards | truth 6; Judgment 4 |
| TABL-05 | 04-09, 04-12, 04-13 | M2 to M20 per ISO 262, brackets, coarse | ✓ SATISFIED | truth 1; `test_iso_262_holds_exactly_the_fifteen_sizes_of_tabl_05_in_diameter_order` |
| TABL-06 | 04-08, 04-13 | match badge | ✓ SATISFIED | truth 5 |
| TABL-07 | 04-07, 04-08, 04-13 | designation without a property class | ✓ SATISFIED | truth 4 |
| INFO-03 | 04-02, 04-03, 04-04, 04-05, 04-11, 04-13, 04-17 | every number traces; no number rather than a plausible one; closed-form volume | ✓ SATISFIED | truths 7, 11, 12 |
| INFO-05 | 04-11, 04-13 | ISO wrench value and one-line DIN note for M10, M12, M14 | ✓ SATISFIED | truth 7 |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/`, `tests/`, `bench/` | | `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` | none found | `make verify`'s unfinished-work scan agrees |
| `tests/test_parity.py` | 157-178 | `#dims` pin matches selectors exactly (WR-04, row `open`) | ⚠️ Warning | guard strength only; shipped CSS correct; owner UAT 8 `pass` |
| `tests/test_parity.py` | `_links_by_rule_17` | rule 17 test applies a Python copy of the page's algorithm (WR-03, row `open`) | ⚠️ Warning | superseded in practice by UAT 4 `pass` for the shipped page |
| `src/screw/static/style.css` | `#dims div` | `gap: .75rem` is also the row gap (IN-09, row `open`) | ℹ️ Info | visual spacing |
| `tests/test_parity.py` | `_info_row_problems` docstring | garbled docstring (IN-10, row `open`) | ℹ️ Info | wording |
| `src/screw/calc/__init__.py`, `app.js`, `tests/test_calc.py`, `tests/test_api.py` | | IN-05 to IN-08 (rows `open`) | ℹ️ Info | as in the previous report |

No stub, hollow prop or static-return data source found.

### Human Verification Required

None. The previous report's three human items are closed by the owner: item 1 (UAT test 5 re-run) by `04-UAT.md` test 7 `pass`; item 2 (rulings on eight findings) by test 8 `pass`; item 3 (light theme and narrow layout) by test 9 `pass`. See Observations for the one housekeeping mismatch (disposition rows).

### Gaps Summary

No gaps. Phase 4 delivers the goal: the picker, API and CLI turn a size and length (for example ISO 4017 M6 x 20) into a hex head screw or bolt whose explicit mm fields come from a cited, typed, gated table row; the badge, designation and wrench note behave as specified; the info panel traces every number to a field or a row; the layout keeps full-precision values whole. `make verify` is green at `7634830`. The only loose end is bookkeeping: the eight review-disposition rows still read `open` after the owner's ruling.

---

_Verified: 2026-10-13T09:00:00Z_
_Verifier: Claude (gsd-verifier)_
