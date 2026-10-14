---
phase: 04-iso-hex-bolts-and-screws
verified: 2026-10-14T08:00:00Z
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
  - "bench/RESULTS.md"
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
covered_digest: "v3:sha256:83331143f6908b19302db3f0145655ee71431cb7674251635300af69bd01addc"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 11/12
  gaps_closed:
    - "Truth 12 (G-04-5 browser half): the owner's re-run is recorded in 04-UAT.md test 7 (result: pass) and test 9 (result: pass, light theme and under 820 px); gap G-04-5 is status: resolved there"
  gaps_remaining: []
  regressions: []
---

# Phase 4: ISO Hex Bolts and Screws Verification Report

**Phase Goal:** A user picks "M6 x 20, ISO 4017" (or an ISO 4014 size and length) and gets a hex head bolt or screw whose explicit millimetre fields were filled from a cited, tested table row, with an info panel whose every number traces to a field or a row.
**Verified:** 2026-10-14T08:00:00Z
**Status:** passed
**Re-verification:** Yes. The previous report (verified 2026-10-12T20:30:00Z, `human_needed`, 11/12) was routed back here because its covered-input digest went stale.

## Verdict

The goal is achieved in the codebase. No must-have failed, no blocker was found, and the one truth the previous report held for a human (truth 12, the rendered layout of the wrapping info row) is now covered by the owner's recorded UAT results.

Why the digest was stale, and what that does and does not mean:

- `git diff e8df305 HEAD -- src tests pyproject.toml Makefile` is empty. Phase 4 landed on `main` as `e8df305` (PR #12) and no file under `src/`, `tests/`, `pyproject.toml` or `Makefile` has changed since. The only non-`.planning/` changes after the previous report are `docs/architecture/decision_log.md` (+19 lines, the L11 escape-clause entry for Phase 5), `bench/RESULTS.md` (+59 lines, the first `grid.yml` run on a GitHub runner, Phase 3 material), and two files under `docs/ideas/`. The L11 entry concerns the Phase 5 pair check; nothing in Phase 4 cites it, and it contradicts no Phase 4 decision.
- `bench/RESULTS.md` still carries the `## Head fuse probe (Phase 4, D-03)` entry that plan 04-01 required (line 6384, from `e8df305`).
- The squash merge removed commit `f39b2c2` (the previous report's HEAD), so I could not diff against it. I re-read the shipped code instead of trusting that nothing moved, and it matches the previous report's description (style.css rules, `renderInfo` template, preset and info code).

Evidence I produced myself on this tree, not read from SUMMARYs:

- `make verify` was run by the orchestrator on this exact tree on 2026-10-14: exit 0, `2637 passed in 44.02s`, coverage 97.57% (floor 96%). I did not re-run it.
- Targeted run by me: `.venv/bin/python -m pytest tests/test_tables.py tests/test_tables_second_entry.py tests/test_presets.py tests/test_calc.py tests/test_import_boundaries.py tests/test_parity.py -p no:cacheprovider --no-cov -q -n0`: `1656 passed in 4.60s`. `pytest tests/test_solid.py -k bolt`: `3 passed`.
- `.venv/bin/lint-imports`: `Contracts: 9 kept, 0 broken` (including "The parameters never consult a table", "Tables are a leaf", "The thread maths stays free of the CAD kernel", "The serving process never imports the CAD kernel").
- A live probe through the FastAPI `TestClient` (lifespan on) and the CLI, described under Behavioral Spot-Checks.
- The unfinished-work scan (`TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER`) over `src/`, `tests/`, `bench/`: no match.

## Goal Achievement

### Observable Truths

| # | Truth (source) | Status | Evidence |
|---|----------------|--------|----------|
| 1 | A user can pick standard + size + length across M2 to M20 per ISO 262 (second-choice bracketed, coarse only) on the UI, API and CLI and get an ISO 4014 bolt or ISO 4017 screw up to the 200 mm cap; parity is green (ROADMAP SC1; TYPE-01, TYPE-02, TABL-01, TABL-05) | VERIFIED | `catalogue()` returns 294 rows: 186 ISO 4017 + 108 ISO 4014, 15 sizes M2 to M20 (M3.5, M7, M14, M18 are `choice == 2`), maximum length 200.0 in both standards. `GET /api/presets?kind=bolt` returns the same 294 rows with axes `['Standard','Size','Length']`; `screw presets bolt` prints the same document. `tests/test_presets.py::test_every_catalogue_row_round_trips` x 294 and the registry-wide parity tests in `tests/test_parity.py` pass. UAT test 1 `pass` for the page picker |
| 2 | The UI offers the same pick and writes the row's mm fields (SC1, UI half; TABL-01) | VERIFIED | `app.js` builds one select per catalogue axis from `/api/presets` (lines 137 to 230), with `showPicks` and the cascade; the entry's `fields` are written to the form and hash. Source-pin tests in `tests/test_parity.py` pass; UAT test 1 `pass`, UAT 9 `pass` for the light theme and narrow window |
| 3 | The preset fills explicit mm fields only: the link carries mm fields, the preset id is metadata, opening the URL rebuilds the part without consulting a table; `thread_length` is filled by the preset (full length for 4017, `b` for 4014) and stays editable (SC2; TABL-01, THRD-03) | VERIFIED | `FIELD_NAMES = ("d","pitch","length","s","k","thread_length")`; ISO 4017 row `thread_length = length`; ISO 4014 row `thread_length = b` of its band (live: `iso4014:M10x60` fills 26.0, `iso4014:M12x80` fills 30.0, matching ISO 4014 b for M10 and M12; band table M14/M16/M20 second b 40/44/52 above 125 mm). Import-linter contract "The parameters never consult a table" KEPT and the `-I` runtime probes in `tests/test_import_boundaries.py` pass. The CLI refuses `--length 10 --thread-length 30` with exit 2 and a named-field message; the API gives a 422 `thread_length_conflict` |
| 4 | The designation line shows the ISO designation without a property class (SC3, second clause; TABL-07) | VERIFIED | Live: `Hexagon head screw ISO 4017 - M6 x 20` and `Hexagon head bolt ISO 4014 - M10 x 60`; decimal sign printed as a comma for M3,5; left-hand parts get `None` (the standards give no left-hand form, `designation_for`). Tests in `tests/test_tables.py` and `tests/test_calc.py` pass |
| 5 | The badge reads "matches ISO 4017 M6 x 20" while the fields equal the row and "custom, based on ISO 4017 M6 x 20" once any field is edited (SC3, first clause; TABL-06) | VERIFIED | Backend `PresetMatch`: `status: exact` with `display: ISO 4017 M6 × 20` for the row's fields; editing `k` to 4.1 gives `status: custom`, `designation: None`, and the warning "no ISO 4014:2022 or ISO 4017:2022 row matches these fields; row values not reported". `app.js` lines 172 to 174 compose `matches ${preset.display}` / `custom, based on ${presetBasis.display}` from those keys. UAT test 1 `pass` |
| 6 | Every table row carries a typed `Source` (standard, edition, table, column); one pure-data verification test per row generated from the table; an UNVERIFIED row is refused by the gate (SC4; TABL-02, TABL-03, TABL-04) | VERIFIED | `rows.py`: every dataclass is `kw_only` with no defaults and a required `source`, so a row without it is a `mypy --strict` error. Collected tests: `test_row_relations` x 294, `test_head_relations` x 36, `test_a_printed_shank_cell_satisfies_lg_max_and_ls_min_from_its_bands_b` x 108, `test_an_iso_4014_row_fills_thread_length_with_b_of_its_band_...` x 108, plus per-size series tests x 15. `test_no_module_marks_a_row_unverified` and `test_no_row_in_the_tree_is_unverified` pass with planted-row controls (`test_the_text_scan_sees_an_unverified_row`, `test_the_runtime_check_sees_an_unverified_row`); my scan found no `status="unverified"` row in the tree. Minor, unchanged: ISO 262 `Size` and `ThreadBand` rows have no 1:1 parametrized test, they are covered through the catalogue-wide row tests |
| 7 | The info panel numbers come from the kernel-free maths, each traceable to an mm field or a cited, tested row; a value that cannot be computed honestly is a warning and no number; any volume is the closed form; the ISO wrench size with a one-line note where it differs from the DIN (SC5; INFO-03, INFO-05) | VERIFIED | Live panel for ISO 4017 M6 x 20 (17 rows): each row is an explicit field (`d`, `pitch`, `length`, `s`, `k`), a computed reading of fields (`across_corners` = s / cos 30° = 11.547005383792515; `thread_depth` 0.5412658773652741 = 5H/8 with H = (sqrt(3)/2) P; `minor_diameter`), a cited row value whose label carries its table (e.g. `Across flats, min (ISO 4017:2022 Table 1)` 9.78) or `Volume (closed form)` 805.5542424753626 mm³. `_bolt` leaves a non-finite value out and adds a `... not reported` warning; below `MIN_TAIL_MM` of built thread it omits turns and volume with a warning. `calc` imports neither the kernel nor the logger (contracts KEPT). Wrench note live: ISO 4014 M12 x 80 notes `wrench size 18 mm (ISO 4014:2022); the withdrawn DIN 931 used 19 mm`, M10 x 60 `16 mm ... DIN 931 used 17 mm`; the note exists only for M10, M12, M14 (`WITHDRAWN_DIN_WRENCH_MM`) |
| 8 | The bolt the preset names builds as one valid solid with plain planar ends, gated by the THRD-04 postcondition (TYPE-01, TYPE-02 geometry) | VERIFIED | Live through the API with the lifespan running: ISO 4017 M6 x 20 returns `model.stl?quality=preview` 200 (1,579,284 bytes) and `model.step` 200 (1,190,192 bytes). `tests/test_solid.py -k bolt` 3 passed; the full solid suite with positive controls sits inside the orchestrator's green 2637. The head-fuse probe entry exists in `bench/RESULTS.md` |
| 9 | The info document carries a required `downloads` member computed by the one `download_refusal` rule that the model route and `screw export` also call; the fine-STL warning stays; the pinned count of 62 refused is unchanged (G-04-3, plan 04-15) | VERIFIED | `PartInfo.downloads` is required; `_downloads(p)` calls `download_refusal` for each of `_DOWNLOADS`, the same function `app._serve` and `cmd_export` call; the refusal sentences are appended as warnings from the same call so the two cannot disagree. Agreement tests (`test_every_download_the_document_lists_is_answered_by_the_route_as_it_says`, the catalogue-wide ones, `test_the_fine_stl_refused_presets_are_counted`) are in `tests/test_api.py` and `tests/test_calc.py` and inside the green gate |
| 10 | The page builds both download links from `info.downloads`, offers `Download STL (preview)` with the refusal as its title where the fine STL is refused, keeps `Download STEP`, names no quality, writes nothing to the hash; in a real browser M8 / 70 saves an STL (G-04-3, plan 04-16) | VERIFIED | `setDownloads(q, info.downloads)` at `app.js` line 474, defined at line 397; no warning-text matching. Human half: `04-UAT.md` test 4 `result: pass`; light theme and narrow window in UAT test 9 `pass`. `app.js` and `index.html` are byte-identical to the Phase 4 PR (`e8df305`) |
| 11 | `style.css` lays out each `#dims div` as a wrapping flex row, `#dims dt` as `flex: 1 1 50%`, `#dims dd` as `margin: 0 0 0 auto` with `overflow-wrap: anywhere` and no `white-space`; no `#dims` rule keeps text on one line, clips or ellipsizes; a source pin fails the gate if the rules change and a second test shows the check flags the old rules (G-04-5, plan 04-17 truth 1) | VERIFIED | Rules read verbatim in `style.css` lines 169 to 195 this run: `#dims div { display: flex; flex-wrap: wrap; justify-content: space-between; gap: .75rem; padding: .15rem 0; border-bottom: 1px dashed var(--line); }`, `#dims dt { color: var(--muted); flex: 1 1 50%; }`, `#dims dd { margin: 0 0 0 auto; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }`; no `white-space`, `overflow` or `text-overflow` under `#dims`. `renderInfo` builds the `dd` text as `` `${String(row.value)} ${row.unit}`.trim() `` (line 374), so no number is rounded in the page. The pin test and its teeth test are inside my 1656-test run (`tests/test_parity.py`) and pass. Known limit, unchanged: the pin matches selectors exactly (04-REVIEW WR-04) |
| 12 | In a real browser, light and dark, 720 and 1920 px, ISO 4017 M8 x 70's four long values sit whole under their label inside their own cell, labels wrap as phrases (at most 4 lines), short values stay beside their labels, nothing is rounded or cut, the 25-character value breaks only before `mm` (G-04-5, plan 04-17 truths 2 to 4, `verification: backstop`) | VERIFIED | Directly observed behavior, recorded by the owner: `04-UAT.md` test 7 (the re-run of test 5 against plan 04-17) `result: pass`, and test 9 (light theme and under 820 px) `result: pass`; the file is `status: complete`, `gaps G-04-5 status: resolved`. Supporting, not substituting: the previous verifier's headless Chrome probe of the same committed sheet read 0 px of overflow in both themes at 720 and 1920 px, and the CSS and `app.js` it measured are unchanged (see Verdict). Provenance caveat: test 7's note does not say which browser or theme the owner used; I accept the recorded `pass` as the owner's result, as the previous report did for test 4. Test 5 still reads `issue` by design: it records the original report that plan 04-17 then fixed |

**Score:** 12/12 truths verified (0 present, behavior-unverified).

No truth is flagged `coincidental-reliance`: the preconditions the truths lean on (the closed-form row list, the catalogue order tie rule, `FIELD_NAMES` mapped to `BoltParams` fields) are established by the code and pinned by tests.

### Judgments

1. **L02, a printed number is a number someone cuts metal to.** Held. Defaults stay the absolute millimetres of `BoltParams`; `match()` is exact float equality with no nearest row; a part that is no row gets no row values and a warning; the CSS moves a value, never changes it; volume is the closed form. A direct conflict (`length` 10, `thread_length` 30) is a 422 / exit 2 naming both fields rather than a guess.
2. **Requirement bookkeeping.** `.planning/REQUIREMENTS.md` now marks all twelve IDs `[x]` and "Complete" (the previous report found five still `[ ]`; the orchestrator ticked them). Caveat unchanged: TABL-04's text also names ISO 4032, 724 and 965-2, which are Phase 5 purchases; the tick is the gate plus the Phase 4 standards.
3. **Open review findings.** `04-REVIEW-DISPOSITION.md` still lists eight rows `open` (WR-03, IN-05 to IN-08, WR-04, IN-09, IN-10). The owner was asked twice (UAT tests 6 and 8) and answered `pass` without a per-finding ruling. None is a must-have failure: WR-04 weakens a future regression guard, not the shipped CSS. I record them as warnings in the anti-pattern table and not as a human verification item, because the human decision was requested and given; writing the rulings into the disposition file is the owner's bookkeeping. STATE.md already records the same.

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|--------------|----------|
| 1 | Tip chamfer and under-head fillet | Phase 5 | ROADMAP Phase 5, THRD-05 and its ISO 4753 precondition |
| 2 | Printability warning for small sizes | Phase 6 | INFO-04 maps to Phase 6 |
| 3 | Measured per-size build caps and a re-swept export budget (the cause of the 62 refused fine STLs, now reached through the preview link) | Phase 7 | OPER-01 to OPER-03 and the INTERIM markers in `calc/thread.py` |
| 4 | Preview quality named in the saved file name | Phase 5 (with FRNT-06) | `docs/ideas/2026-10-12-preview-stl-download-names-its-quality.md` |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/screw/tables/rows.py` | typed, citation-required row types | VERIFIED | 102 lines, `kw_only` dataclasses, `source` required on every row type |
| `src/screw/tables/iso262.py`, `iso4017.py`, `iso4014.py` | cited rows, M2 to M20 | VERIFIED | 15 sizes; heads read from `Table 1/2/3` (4017) and `Table 1 to 4` (4014); `b` bands match ISO 4014 for M6/M8/M10/M12/M14/M16/M20 |
| `src/screw/tables/presets.py` | catalogue, `expand`, tie rule | VERIFIED | 294 rows, case-sensitive `expand`, 4014 row `thread_length = b` or ValueError (no assert) |
| `src/screw/calc/presets.py` | match, designation, row values, notes, catalogue document | VERIFIED | reached only from inside `_bolt` (contract 6) |
| `src/screw/calc/__init__.py` | `derive`, `download_refusal`, `explicit_conflict` | VERIFIED | kernel-free; registered-kind dispatch raises TypeError for an unregistered kind |
| `src/screw/params.py`, `calc/thread.py` | explicit-mm `BoltParams`, thread maths | VERIFIED | no `tables` import (contract "The parameters never consult a table" KEPT) |
| `src/screw/solid/bolt.py`, `solid/__init__.py` | hex head + threaded shank, gated build | VERIFIED | live STL and STEP builds returned 200 |
| `src/screw/app.py`, `cli.py` | `/api/presets`, `screw presets`, `--preset` | VERIFIED | live responses above; unknown preset id is a CLI exit 2 naming the id |
| `src/screw/static/app.js`, `index.html`, `style.css` | picker, badge, grouped panel, downloads, wrapping row | VERIFIED | source read; UAT tests 1, 4, 7, 9 `pass` |
| `tests/test_tables.py`, `test_presets.py`, `test_calc.py`, `test_api.py`, `test_parity.py`, `test_import_boundaries.py`, `test_tables_second_entry.py` | per-row, gate, parity and boundary tests | VERIFIED | 1656 tests in the six files I ran, all pass; `test_api.py` is inside the orchestrator's green gate |
| `bench/head_fuse.py`, `bench/RESULTS.md` | the D-03 head-fuse probe entry | VERIFIED | entry at `bench/RESULTS.md` line 6384 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `app.js` picker | `/api/presets` | `fetch('api/presets?kind=...')` line 220 | WIRED | live route returns 294 rows |
| `app.js update()` | `/api/<kind>/info` and badge | `info.preset.status` / `.display` | WIRED | live info document carries `preset` |
| `app.js update()` | `setDownloads` | `setDownloads(q, info.downloads)` line 474 | WIRED | UAT 4 `pass` |
| `calc._bolt` | `calc.presets` | local import inside the function | WIRED | contract 6 forbids a top-level import; live rows prove the call |
| `calc._bolt` | `download_refusal` | `_downloads(p)` | WIRED | same rule as `app._serve` and `cmd_export` |
| `app.py`, `cli.py` | `calc.explicit_conflict` | route-attached refusal; CLI calls the same | WIRED | API 422 `thread_length_conflict` and CLI exit 2 observed |
| `tests/test_parity.py` | `style.css` | `STYLE_CSS` read from `STATIC` | WIRED | pin and teeth tests pass |
| `params` / `calc.thread` | `tables` | none allowed | NOT IMPORTED (as required) | 9 contracts kept |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| Info panel `dd` | `row.value`, `row.unit` | `/api/bolt/info` rows from the user's fields and cited rows | yes (17 rows read live for ISO 4017 M6 x 20; 4014 rows add `b`, `lg_max`, `ls_min`) | FLOWING |
| Picker, badge | `catalogue.rows`, `info.preset` | `/api/presets`, `PresetMatch` from stored `Source`-carrying rows | yes | FLOWING |
| Download links | `info.downloads` | `download_refusal(p, fmt, quality)` | yes (62 of 294 rows refuse the fine STL, pinned by test) | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Catalogue size, sizes, caps, no UNVERIFIED row | `catalogue()` via `.venv/bin/python` | 294 rows (186 + 108), 15 sizes, max length 200.0, no unverified source | PASS |
| Pick M6 x 20, ISO 4017 | `GET /api/presets?kind=bolt` then `GET /api/bolt/info` with the row's `fields` | `exact` match, designation `Hexagon head screw ISO 4017 - M6 x 20`, 17 rows, only the standing warning | PASS |
| Edit one field | same with `k=4.1` | `status: custom`, no designation, no-row warning | PASS |
| ISO 4014 pick | `iso4014:M10x60` fields | `thread_length` 26.0, designation `Hexagon head bolt ISO 4014 - M10 x 60`, `b` 26.0, `lg,max` 34.0, `ls,min` 26.5 cited to `ISO 4014:2022 Table 2`, DIN 931 wrench note | PASS |
| Explicit conflict | API `length=10&thread_length=30`; `screw info bolt --length 10 --thread-length 30` | 422 `thread_length_conflict`; exit 2 with a message naming both fields | PASS |
| CLI parity | `screw info bolt --preset iso4014:M12x80`, `screw presets bolt`, `--preset nope` | exact match with the same notes; same 294-row document; exit 2 naming the id | PASS |
| Build | `model.stl?quality=preview` and `model.step` for M6 x 20 under the app lifespan | 200 and 200 (1,579,284 and 1,190,192 bytes) | PASS |
| Tables, presets, calc, boundaries, parity | `pytest` over six files, `-n0 --no-cov` | 1656 passed | PASS |
| Module graph | `.venv/bin/lint-imports` | 9 kept, 0 broken | PASS |
| The gate | `make verify` (orchestrator, this tree, 2026-10-14) | exit 0, 2637 passed, coverage 97.57% | PASS (not re-run by me) |

### Probe Execution

Step 7c: SKIPPED. No PLAN or SUMMARY of this phase declares a probe script and `scripts/*/tests/probe-*.sh` does not exist.

### Requirements Coverage

Every requirement ID declared in the 17 PLAN frontmatters (read this run: 04-01 TABL-04; 04-02 INFO-03; 04-03 TYPE-01, TYPE-02, INFO-03; 04-04 THRD-03, TYPE-01, INFO-03; 04-05 THRD-03, INFO-03; 04-06 THRD-03; 04-07 TABL-02, TABL-03, TABL-04, TABL-07; 04-08 TABL-06, TABL-07, TYPE-01; 04-09 TABL-02, TABL-03, TABL-04, TABL-05, TYPE-02; 04-10 TABL-02, TABL-03, TABL-04, TYPE-01, THRD-03; 04-11 INFO-03, INFO-05, TYPE-01; 04-12 TABL-01, TABL-05, THRD-03; 04-13 TABL-01, TABL-05, TABL-06, TABL-07, INFO-03, INFO-05; 04-14 TYPE-01, TABL-04; 04-15 TABL-01, TYPE-02; 04-16 TABL-01, TYPE-02; 04-17 INFO-03) is in the union of twelve IDs the task lists, and REQUIREMENTS.md's traceability table maps exactly these twelve to Phase 4 and no further ID. No ID is orphaned and none is missing from a plan.

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| THRD-03 | 04-04, 04-05, 04-06, 04-10, 04-12 | `thread_length` explicit mm; 4017 fills full length, 4014 fills `b`; editable | SATISFIED | truth 3; REQUIREMENTS.md `[x]` |
| TYPE-01 | 04-03, 04-04, 04-08, 04-10, 04-11, 04-14 | ISO 4014 hex bolt | SATISFIED | truths 1, 7, 8 |
| TYPE-02 | 04-03, 04-09, 04-15, 04-16 | ISO 4017 hex screw to 200 mm | SATISFIED | truths 1, 8, 9, 10 |
| TABL-01 | 04-12, 04-13, 04-15, 04-16 | pick standard + size + length; mm fields only | SATISFIED | truths 1 to 3, 9, 10 |
| TABL-02 | 04-07, 04-09, 04-10 | typed `Source` on every row | SATISFIED | truth 6 |
| TABL-03 | 04-07, 04-09, 04-10 | one pure-data test per row | SATISFIED | truth 6 |
| TABL-04 | 04-01, 04-07, 04-09, 04-10, 04-14 | purchased-copy rule, UNVERIFIED gate | SATISFIED for the Phase 4 standards | truth 6; judgment 2 |
| TABL-05 | 04-09, 04-12, 04-13 | M2 to M20 per ISO 262, brackets, coarse | SATISFIED | truth 1 |
| TABL-06 | 04-08, 04-13 | match badge | SATISFIED | truth 5 |
| TABL-07 | 04-07, 04-08, 04-13 | designation without a property class | SATISFIED | truth 4 |
| INFO-03 | 04-02, 04-03, 04-04, 04-05, 04-11, 04-13, 04-17 | every number traces; no number rather than a plausible one; closed-form volume | SATISFIED | truths 7, 11, 12 |
| INFO-05 | 04-11, 04-13 | ISO wrench value and one-line DIN note for M10, M12, M14 | SATISFIED | truth 7 |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/`, `tests/`, `bench/` | | `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` scan | none found | `make verify`'s unfinished-work scan agrees |
| `tests/test_parity.py` | `_info_row_problems` | the `#dims` pin matches selectors exactly (04-REVIEW WR-04, open) | Warning | a more specific selector walks past the pin; guard strength only, shipped CSS is correct |
| `tests/test_parity.py` | `_links_by_rule_17` | rule 17 test applies a Python copy of the page's algorithm (WR-03, open) | Warning | superseded in practice by UAT 4 `pass` for the shipped page |
| `src/screw/static/style.css` | `#dims div` | `gap: .75rem` is also the row gap, so a wrapped value sits 10.5 px under its label (IN-09, open) | Info | visual spacing only |
| `tests/test_parity.py` | `_info_row_problems` docstring | garbled docstring; the pin also freezes `#dims dl` (IN-10, open) | Info | wording |
| `src/screw/calc/__init__.py`, `app.js`, `tests/test_calc.py`, `tests/test_api.py` | | IN-05 to IN-08 (open) | Info | as in the previous report; the owner passed UAT tests 6 and 8 without a per-finding ruling, so the rows stay `open` in `04-REVIEW-DISPOSITION.md` |
| `src/screw/calc/thread.py` | `FINE_STL_ROWS` | INTERIM caps refuse the fine STL for 62 of 186 ISO 4017 presets | Info | owner-accepted bound (D-21, L13, UAT test 2 `pass`), handled by the preview link; Phase 7 re-sweeps |

No stub, hollow prop or static-return data source found. No debt item was filed by this verification.

### Human Verification Required

None. Every item the previous report held for a human is now recorded in `04-UAT.md` (`status: complete`, 9 tests): the info-row re-run (test 7), the light-theme and narrow-window pass (test 9), the download steps (test 4) and the two review-finding rulings (tests 6 and 8, `pass`). The eight open review rows are an owner bookkeeping step, not a verification item (Judgment 3).

### Gaps Summary

No gaps. All 12 must-haves hold against the code as it stands on `main`. The only things that changed since the previous report are documentation and a Phase 3 benchmark record; `src/`, `tests/`, `pyproject.toml` and `Makefile` are identical to the Phase 4 PR. What remains is housekeeping that blocks nothing: the eight `open` rows in `04-REVIEW-DISPOSITION.md` (WR-04 is the one worth a ruling, since it limits how well the `#dims` source pin guards a future stylesheet) and the stale `issue` line of UAT test 5, which documents the original report.

---

_Verified: 2026-10-14T08:00:00Z_
_Verifier: Claude (gsd-verifier)_
