---
phase: 04-iso-hex-bolts-and-screws
verified: 2026-10-12T20:30:00Z
status: passed
score: 11/12 must-haves verified
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
covered_digest: "v3:sha256:90c203672e3ec084be5ae2a068f0870680fcadb4dca49debb4813417c1b0bedc"
behavior_unverified: 1
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 9/10
  gaps_closed:
    - "G-04-5: a full-precision info-panel value no longer runs into the next cell and its label no longer collapses to one word a line (UAT test 5, plan 04-17): code and gate half closed here, browser half held for the owner"
    - "Truth 10 (download links, G-04-3 page half): human-confirmed by UAT test 4 (result: pass); app.js is byte-unchanged since the previous report"
  gaps_remaining: []
  regressions: []
behavior_unverified_items:
  - truth: "In a real browser, light and dark, at 720 px and 1920 px, ISO 4017 M8 x 70's 0.6765823467065926 mm, 6.646835306586815 mm, 15.011106998930268 mm and 3670.874961137891 mm³ each sit whole on a line of their own under their label at the right edge of their cell, nothing reaches Head height or another neighbour; labels wrap as phrases (at most 4 lines), short values stay beside their labels; every value reads as the API sent it, the 25-character 0.00010825317547305484 mm breaks only before mm (G-04-5, plan 04-17 truths 2 to 4, verification: backstop)"
    test: "make serve (SCREW_PORT=8001 if 8000 is taken), empty hash, pick ISO 4017 / M8 / 70. Light theme at 720 px then 1920 px; repeat in the dark theme. At 720 px run document.querySelectorAll('#dims dd')[9].textContent = '0.00010825317547305484 mm' in the console"
    expected: "At both widths and in both themes each of the four long values sits whole under its label at the right of its cell, above the dashed line, touching no neighbour; labels wrap as phrases, at most 4 lines; 8 mm, 1.25 mm, 13 mm, 12.73 mm, 5.3 mm and 56 stay on their label's first line at the right; no value rounded, cut or ellipsized; the injected value reads 0.00010825317547305484 with mm on the line under it"
    why_human: "Line breaks, overlap and contrast are visible only on a rendered page; no browser runs in the gate (L01); tests/test_parity.py reads style.css as text. The verifier's headless Chrome probe of the committed sheet (Behavioral Spot-Checks) is evidence for the human check and not a substitute for it. This is UAT test 5, still recorded as an issue in 04-UAT.md until the owner re-runs it"
human_verification:
  - test: "Re-run UAT test 5 (plan 04-17 Task 1 human-check), listed in behavior_unverified_items above, and mark 04-UAT.md test 5 and gap G-04-5 resolved"
    expected: "As in the item above"
    why_human: "Rendered layout and contrast in both themes; the gate cannot run a browser"
  - test: "Rule on the eight open findings in 04-REVIEW-DISPOSITION.md: WR-03, IN-05, IN-06, IN-07, IN-08 (G-04-3 review) and WR-04, IN-09, IN-10 (G-04-5 review)"
    expected: "Each is fixed, filed under docs/tech_debt/ with sign-off, or skipped by the owner, and the disposition rows say so"
    why_human: "CLAUDE.md: a deferred item needs the owner's sign-off. UAT test 6 is recorded as pass without a per-finding ruling, so every row is still open (open: 8 of 15). None is a must-have failure. WR-04 (the style.css pin matches selectors exactly, so a more specific selector walks past it) is the one that touches this re-verification: it weakens the regression guard of truth 11, not the shipped CSS"
  - test: "Plan 04-13 and 04-16 browser checks (UAT tests 1 and 4), light theme and 820px part"
    expected: "Picker, badge, grouped panel, notes and the downloads row (Download STL (preview), 22 characters) keep contrast and wrap cleanly in the light theme and under 820px"
    why_human: "UAT 1 and 4 are recorded pass, but UAT 1 was an orchestrator pre-run in the dark theme only; the light-theme and narrow pass is folded into UAT test 5's re-run (same page, both themes). Listed so it is not lost"
---

# Phase 4: ISO Hex Bolts and Screws Verification Report

**Phase Goal:** A user picks "M6 x 20, ISO 4017" (or an ISO 4014 size and length) and gets a hex head bolt or screw whose explicit millimetre fields were filled from a cited, tested table row, with an info panel whose every number traces to a field or a row.
**Verified:** 2026-10-12T20:30:00Z, at HEAD `f39b2c2`
**Status:** human_needed
**Re-verification:** Yes, after gap closure G-04-5 (plan 04-17, wave 13). Previous report: `human_needed`, 9/10 (verified 2026-10-12T17:35:00Z, stale: `style.css`, `tests/test_parity.py` and the plan files changed).

## Verdict

The goal is achieved in the code. No must-have FAILED and no BLOCKER was found. The status stays `human_needed` for one must-have reason: the browser half of gap G-04-5 (a full-precision value sits whole under its label, inside its cell, in both themes at 720 and 1920 px) is tagged `verification: backstop` by its own plan, no committed test renders a page, and the owner's browser re-run (UAT test 5) has not happened. Two softer human items do not touch the goal (the owner's rulings on eight open review findings; the light-theme and narrow pass folded into the same re-run).

What changed against the previous report:

- Plan 04-17 changed exactly three source-side files: `src/screw/static/style.css` (the `#dims` info row wraps), `tests/test_parity.py` (a `style.css` source pin and its teeth) and `01-UI-SPEC.md` (diff `e9a7f8d..HEAD` shows `src/` and `tests/` touched only in those two files; no `app.js`, `index.html`, calc, tables or solid change). The data half, the API and the CLI are therefore unchanged since the previous report and were re-proved by the full gate, not re-read.
- Truth 10 (download links) moves from PRESENT_BEHAVIOR_UNVERIFIED to VERIFIED: `04-UAT.md` test 4 ("The browser steps of plan 04-16 Task 1") is `result: pass`, and `app.js` and `index.html` are unchanged since the report that held it. Provenance: UAT test 4 carries no pre-run note; I accept the recorded `pass` as the owner's result.
- A new truth pair covers G-04-5: truth 11 (CSS rules and pin) VERIFIED; truth 12 (browser behavior) PRESENT_BEHAVIOR_UNVERIFIED.
- The previous report's human item 3 (rulings on WR-03, IN-05 to IN-08) is still open: UAT test 6 is `pass` without a disposition per finding and the five rows read `open`; the G-04-5 review added WR-04, IN-09 and IN-10, also `open`.

Evidence I produced myself, not read from SUMMARYs:

- `make verify` run once at HEAD from the repo root: ruff, mypy `--strict`, import-linter, unfinished-work scan, pytest `2637 passed in 84.95s`, coverage 97.33% (floor 96), exit 0 (the last lines read `Required test coverage of 96.0% reached. Total coverage: 97.33%` and `2637 passed`).
- `.venv/bin/python -m pytest tests/test_parity.py -k info_row -n0 --no-cov`: `2 passed` (`test_an_info_row_drops_a_long_value_whole_under_its_label_instead_of_into_the_next_cell`, `test_the_info_row_check_has_teeth`).
- `style.css` read at lines 169 to 195 and `tests/test_parity.py` lines 120 to 178: the committed rules are `#dims div { display: flex; flex-wrap: wrap; justify-content: space-between; gap: .75rem; padding: .15rem 0; border-bottom: ... }`, `#dims dt { color: var(--muted); flex: 1 1 50%; }`, `#dims dd { margin: 0 0 0 auto; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }`; no `white-space`, `overflow` or `text-overflow` anywhere under `#dims`; `#dims dl` unchanged. `INFO_ROW_RULES` pins exactly these, iterating the pinned selectors (a deleted rule is reported).
- A headless Chrome probe of the committed `style.css` (details under Behavioral Spot-Checks): 0 px of any value outside its cell at 720 and 1920 px, light and dark.
- Fingerprint recomputed through the CLI, `covered_files` and `covered_digest` copied verbatim from its output.

## Goal Achievement

### Observable Truths

| # | Truth (source) | Status | Evidence |
|---|----------------|--------|----------|
| 1 | A user can pick standard + size + length across M2 to M20 per ISO 262 (second-choice bracketed, coarse only) on the API and the CLI and get an ISO 4014 bolt or ISO 4017 screw up to 200 mm; parity is green (SC1; TYPE-01, TYPE-02, TABL-01, TABL-05) | ✓ VERIFIED | Unchanged since the previous report (no calc/tables/api/cli diff in `e9a7f8d..HEAD`); `tests/test_presets.py` round-trips all 294 rows, parity tests inside the green 2637 |
| 2 | The UI offers the same pick and writes the row's mm fields (SC1, UI half) | ✓ VERIFIED | `app.js`/`index.html` unchanged; source tests green; UAT test 1 `pass` |
| 3 | The preset fills explicit mm fields only: the link carries mm fields, the preset id is metadata, opening the URL rebuilds the part without consulting a table; `thread_length` is filled by the preset and stays editable (SC2; TABL-01, THRD-03) | ✓ VERIFIED | `BoltParams` `extra="forbid"`; contract "The parameters never consult a table" KEPT (9 contracts) plus the `-I` runtime probes in `tests/test_import_boundaries.py` |
| 4 | The designation line shows the ISO designation without a property class (SC3, second clause; TABL-07) | ✓ VERIFIED | `tests/test_tables.py`/`test_calc.py`; unchanged |
| 5 | The badge reads "matches ISO 4017 M6 x 20" while the fields equal the row and "custom, based on ISO 4017 M6 x 20" once any field is edited (SC3, first clause; TABL-06) | ✓ VERIFIED | backend `preset.status`; `showMatch` unchanged; UAT test 1 `pass` |
| 6 | Every table row carries a typed `Source`; one pure-data test per row generated from the table; an UNVERIFIED row is refused by the gate (SC4; TABL-02, TABL-03, TABL-04) | ✓ VERIFIED | `rows.py` kw_only dataclasses with required `source`; per-row, per-head and per-cell tests and `test_no_row_in_the_tree_is_unverified` with a planted-row control, all inside the green 2637. Minor, as before: ISO 262 `Size`/`ThreadBand` rows have no 1:1 parametrized test |
| 7 | The info panel numbers come from kernel-free maths, each traceable to an mm field or a cited, tested row; an uncomputable value is a warning and no number; any volume is the closed form; the ISO wrench size note where it differs from the DIN (SC5; INFO-03, INFO-05) | ✓ VERIFIED | `calc/__init__.py::_bolt` unchanged; `calc` imports neither the kernel nor the logger (contracts KEPT). Live row list for M8 x 70 read this run: every row is a field, a closed form or a cited `ISO 4017:2022 Table 2` row, `Volume (closed form)` 3670.874961137891 mm³ |
| 8 | The bolt the preset names builds as one valid solid with plain planar ends, gated by the THRD-04 postcondition (TYPE-01, TYPE-02 geometry) | ✓ VERIFIED | `solid/*` unchanged since the previous report; solid tests with positive controls inside the 2637 |
| 9 | The info document carries a required `downloads` member from the one `download_refusal` rule; `/api/bolt/info`, `screw info bolt`, the model route and `screw export` agree; the fine-STL warning stays; the pinned 62 is unchanged (G-04-3, plan 04-15) | ✓ VERIFIED | Unchanged code; `test_every_download_the_document_lists_is_answered_by_the_route_as_it_says`, the catalogue-wide agreement tests and `test_the_fine_stl_refused_presets_are_counted` are inside the green 2637; live M8 x 70 document served again this run (200, 17 rows) |
| 10 | The page builds both download links from `info.downloads`, offers `Download STL (preview)` with the refusal sentence as its title where the fine STL is refused, keeps `Download STEP`, names no quality, writes nothing to the hash; in a real browser M8 / 70 saves an STL (G-04-3, plan 04-16) | ✓ VERIFIED | Source pins pass (`app.js` unchanged since the previous report); node harness held the four cases in the previous report; the browser half is now human-confirmed: `04-UAT.md` test 4 `result: pass`. Light theme and 820px part folded into truth 12's re-run |
| 11 | `style.css` lays out each `#dims div` as a wrapping flex row, `#dims dt` as `flex: 1 1 50%`, `#dims dd` as `margin: 0 0 0 auto` with `overflow-wrap: anywhere` and no `white-space`; no `#dims` rule keeps text on one line, clips or ellipsizes; a source pin fails the gate if the rules change and a second test shows the check flags the plan 01-04 rules and the single-line `overflow-wrap` variant (G-04-5, plan 04-17 truth 1) | ✓ VERIFIED | The rules read verbatim from `style.css` (see Evidence); `INFO_ROW_RULES`, `_css_rules`, `_css_declarations`, `_info_row_problems` read; both tests pass in isolation and inside `make verify`; the teeth test runs four sheets (plan 01-04 rules, the V4 variant, an ellipsis rule appended, `#dims dt` deleted) plus a comment-only control. Known limit: the pin matches selectors exactly (WR-04, open) |
| 12 | In a real browser, light and dark, 720 and 1920 px, ISO 4017 M8 x 70's four long values sit whole under their label inside their own cell, labels wrap as phrases (at most 4 lines), short values stay beside their labels, nothing is rounded or cut, the 25-character value breaks only before `mm` (G-04-5, plan 04-17 truths 2 to 4, `verification: backstop`) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Present and wired (truth 11; the `dd` text keeps `${String(row.value)} ${row.unit}` with a plain space before the unit, asserted by the pin test). No committed test renders a page. The verifier's headless Chrome probe held (Behavioral Spot-Checks) and is evidence only. Browser steps pending: UAT test 5 re-run (human item 1). The plan tags these three truths `backstop` |

**Score:** 11/12 truths verified (1 present, behavior-unverified).

### Judgments

1. **L02 on the new layout.** "A number the tool prints is a number someone will cut metal to": the layout moves the value and never the number. `style.css` has no `text-overflow`, `overflow`, `white-space: nowrap` or `max-width` under `#dims`; the probe read every value back whole (all 17 `dd` texts equal the API's `value unit`). The one rule that can split text, `overflow-wrap: anywhere` on `dd`, fires only for a value wider than a whole track, and the space before the unit is the first break it takes (plan 04-17 prohibition 1, `verification: test`, resolved by the pin and its teeth for the clip/nowrap half; the "never splits digits" half is part of truth 12, held for the human).
2. **UI-SPEC extension rule 4 (no off-scale length).** The label basis is `50%`, a proportion like the sheet's `1fr` and `100%`; `.75rem` gap is the existing `md` step. The exception table and the `Applicable:` count are unchanged in the `01-UI-SPEC.md` diff (checked). Prohibition 2 holds.
3. **Regression guard strength (WR-04).** The pin proves the shipped sheet; it does not prove a future sheet, because a more specific selector (`#dims dl dd { white-space: pre; }`) returns `[]` from `_info_row_problems` according to the incremental review. I did not re-run that probe. It lowers the value of truth 11 as a future guard, not the correctness of the shipped CSS, and it is an owner ruling (human item 2).
4. **REQUIREMENTS.md final state.** The file marks TYPE-02, TABL-01 to TABL-05 and INFO-03 `[x]`/Complete and leaves THRD-03, TYPE-01, TABL-06, TABL-07 and INFO-05 `[ ]`/Pending. Code proves all five. No requirement is blocked. TABL-06's page half now has UAT 1 `pass`. They can be ticked once the owner accepts the status; ticking is the orchestrator's. Caveat unchanged: TABL-04's text also names ISO 4032, 724 and 965-2 (Phase 5); the tick is the gate and the Phase 4 standards.
5. **Plan 04-17 requirement.** INFO-03 only; already `[x]` Complete. The plan's wrapping row serves the INFO-03 half "every number on the panel" reaching the eye intact.

### Amendments made inside the phase (read as the contract)

As in the previous report (`e376024`: TYPE-01, SC1, INFO-05, SC2; G-04-3: `01-UI-SPEC.md`, L13). Plan 04-17 added a fourth dated note and amended the Page Anatomy `#dims` bullet, the Spacing `md` usage, E10 overflow and long-text and Verification status in `01-UI-SPEC.md`; the commit `2899c0d` diff was read: the exception table, the `Applicable:` count and the three earlier notes are unchanged, each amended row names its pinning test, and the measured widths are cited as the planner's 2026-10-12 measurement in `04-17-PLAN.md`.

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|--------------|----------|
| 1 | Tip chamfer and under-head fillet | Phase 5 | ROADMAP Phase 5, THRD-05 and its ISO 4753 precondition |
| 2 | Printability warning for small sizes | Phase 6 | INFO-04 maps to Phase 6 |
| 3 | Measured per-size build caps and a re-swept export budget (the cause of the 62 refused fine STLs, now reached through the preview link) | Phase 7 | OPER-01 to OPER-03 and the INTERIM markers in `calc/thread.py` |
| 4 | Preview quality named in the saved file name | Phase 5 (with FRNT-06) | `docs/ideas/2026-10-12-preview-stl-download-names-its-quality.md`; an owner decision and a new Lxx |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/screw/static/style.css` | wrapping info row, `flex: 1 1 50%` | ✓ VERIFIED (source) / ⚠️ behavior routed to human | contains `flex-wrap: wrap`, `flex: 1 1 50%`, `overflow-wrap: anywhere`; `#dims dl` unchanged; probe held |
| `tests/test_parity.py` | `STATIC / "style.css"` source pin and its teeth | ✓ VERIFIED | `STYLE_CSS = (STATIC / "style.css").read_text()` at line 40; both tests pass |
| `01-UI-SPEC.md` | wrapping row in the UI contract, plan 04-17 | ✓ VERIFIED | diff read; contains `plan 04-17` in the note, Page Anatomy, E10 and Verification status |
| `src/screw/calc/__init__.py`, `app.py`, `cli.py`, `app.js`, `index.html` | as in the previous report | ✓ VERIFIED | unchanged (diff empty) |
| `src/screw/tables/*`, `calc/presets.py`, `params.py`, `solid/*` | as in the previous report | ✓ VERIFIED | unchanged (diff empty) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/test_parity.py` | `src/screw/static/style.css` | `STYLE_CSS` read from `STATIC`, `#dims` declarations compared after comments are stripped | WIRED | line 40; a comment cannot satisfy or fail the pin (asserted by the comment-only control) |
| `style.css` | `app.js renderInfo` | the plain space between number and unit in the `dd` text is the first break `overflow-wrap` takes | WIRED | `renderInfo` line 374 builds `` `${String(row.value)} ${row.unit}`.trim() ``; the pin test asserts the template |
| `calc._bolt` | `download_refusal` | `_downloads(p)` | WIRED | unchanged since the previous report |
| `app.js update()` | `setDownloads` | `setDownloads(q, info.downloads)` | WIRED | unchanged; UAT 4 pass |
| `params` / `calc.thread` | `tables` | none allowed | NOT IMPORTED (as required) | contracts 9 kept |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| Info panel `dd` | `row.value`, `row.unit` | `/api/bolt/info` rows from the user's fields and cited rows | yes (17 rows read live for M8 x 70) | ✓ FLOWING |
| Download links | `info.downloads` | `download_refusal(p, fmt, quality)` | yes (62 of 294 rows refuse stl fine) | ✓ FLOWING |
| Picker, badge | `/api/presets`, `PresetMatch` | stored `Source`-carrying rows | yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| The gate | `make verify` | 2637 passed, coverage 97.33%, exit 0 | ✓ PASS |
| The info-row pin and its teeth | `pytest tests/test_parity.py -k info_row -n0 --no-cov` | 2 passed | ✓ PASS |
| Real `style.css` + real `index.html` + the `renderInfo` row-building code on the live M8 x 70 document (`/api/bolt/info?d=8&pitch=1.25&length=70&s=13&k=5.3&thread_length=70`), headless Chrome, `--force-prefers-color-scheme` light and dark, windows 720 and 1920 px, measured with `getBoundingClientRect` (scratch files in `/tmp`, not in the repo) | per row: `dd.right - cell.right` and `cell.left - dd.left`, `dd.top - cell.top`, `dt` height | max overflow 0 px in all four runs; at 720 and 1920 px `Thread depth (ISO 68-1...)` 0.6765823467065926 mm, `Minor diameter` 6.646835306586815 mm and `Across corners, geometric` 15.011106998930268 mm sit 54 px below their cell's top (under a 2-line label of 39 px) and `Volume (closed form)` 3670.874961137891 mm³ sits 34 px below under a 1-line label of 20 px; short values (`13 mm`, `5.3 mm`, `56`, `12.73 mm` and the rest) sit 2 px below the top (on the label line); label heights 20 to 78 px, at most 4 lines (14 px body at 17-20 px line height) | ✓ PASS (not the owner's browser run; the injected 25-character value and the dark-theme contrast were not checked) |

### Probe Execution

Step 7c: SKIPPED. No PLAN or SUMMARY of this phase declares a probe script and `scripts/*/tests/probe-*.sh` does not exist.

### Requirements Coverage

Every ID in the 17 PLAN frontmatters is accounted for and equals the ROADMAP's list of twelve (plan 04-17 declares INFO-03). No ID is orphaned: REQUIREMENTS.md maps exactly these twelve to Phase 4 and no further ID.

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| THRD-03 | 04-04, 04-05, 04-06, 04-10, 04-12 | `thread_length` explicit mm; 4017 fills full length, 4014 fills `b`; editable | ✓ SATISFIED | truth 3; REQUIREMENTS.md still `[ ]` |
| TYPE-01 | 04-03, 04-04, 04-08, 04-10, 04-11, 04-14 | ISO 4014 hex bolt (amended, D-02) | ✓ SATISFIED | truths 1, 7, 8; REQUIREMENTS.md still `[ ]` |
| TYPE-02 | 04-03, 04-09, 04-15, 04-16 | ISO 4017 hex screw to 200 mm | ✓ SATISFIED | truths 1, 8, 9, 10 |
| TABL-01 | 04-12, 04-13, 04-15, 04-16 | pick standard + size + length; mm fields only | ✓ SATISFIED | truths 1 to 3, 9, 10 |
| TABL-02 | 04-07, 04-09, 04-10 | typed `Source` on every row | ✓ SATISFIED | truth 6 |
| TABL-03 | 04-07, 04-09, 04-10 | one pure-data test per row | ✓ SATISFIED | truth 6 |
| TABL-04 | 04-01, 04-07, 04-09, 04-10, 04-14 | purchased-copy rule, UNVERIFIED gate | ✓ SATISFIED for the Phase 4 standards | Judgments 4 |
| TABL-05 | 04-09, 04-12, 04-13 | M2 to M20 per ISO 262, brackets, coarse | ✓ SATISFIED | truth 1 |
| TABL-06 | 04-08, 04-13 | match badge | ✓ SATISFIED | truth 5 (backend tested, page human-confirmed by UAT 1); REQUIREMENTS.md still `[ ]` |
| TABL-07 | 04-07, 04-08, 04-13 | designation without a property class | ✓ SATISFIED | truth 4; REQUIREMENTS.md still `[ ]` |
| INFO-03 | 04-02, 04-03, 04-04, 04-05, 04-11, 04-13, 04-17 | every number traces; no number rather than a plausible one; closed-form volume | ✓ SATISFIED (truth 12 browser half pending human) | truths 7, 11, 12 |
| INFO-05 | 04-11, 04-13 | ISO wrench value and one-line DIN note for M10, M12, M14 | ✓ SATISFIED | truth 7; REQUIREMENTS.md still `[ ]` |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/`, `tests/`, `bench/` | | `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` scan | none found | `make verify`'s unfinished-work scan agrees |
| `tests/test_parity.py` | 157-178 | the `#dims` pin matches selectors exactly (04-REVIEW WR-04, open) | ⚠️ Warning | a more specific selector or a bare `dd` rule walks past the pin; guard strength only, shipped CSS is correct |
| `tests/test_parity.py` | `_links_by_rule_17` | rule 17 test applies a Python copy of the page's algorithm (WR-03, open) | ⚠️ Warning | superseded in practice by UAT 4 `pass` for the shipped page |
| `src/screw/static/style.css` | `#dims div` | `gap: .75rem` is also the row gap, so a wrapped value sits 10.5 px under its label (IN-09, open) | ℹ️ Info | visual spacing; probe shows 54 px for a 39 px label (the 15 px offset is the gap plus padding) |
| `tests/test_parity.py` | `_info_row_problems` docstring | garbled docstring, pin also freezes `#dims dl` (IN-10, open) | ℹ️ Info | wording |
| `src/screw/calc/__init__.py`, `app.js`, `tests/test_calc.py`, `tests/test_api.py` | | IN-05, IN-06, IN-07, IN-08 (open) | ℹ️ Info | as in the previous report |
| `src/screw/calc/thread.py` | `FINE_STL_ROWS` | INTERIM caps refuse the fine STL for 62 of 186 ISO 4017 presets | ℹ️ Info | owner-accepted bound (D-21, L13), handled by the preview link; Phase 7 re-sweeps |

No stub, hollow prop or static-return data source found. No debt item was filed by this verification.

### Human Verification Required

#### 1. UAT test 5 re-run: the wrapping info row (plan 04-17 Task 1 human-check)

**Test:** `make serve` (or `SCREW_PORT=8001 make serve`), empty hash, pick ISO 4017 / M8 / 70. In the light theme make the window 720 px wide, then 1920 px; repeat both in the dark theme. At 720 px run `document.querySelectorAll('#dims dd')[9].textContent = '0.00010825317547305484 mm'` in the console.
**Expected:** At both widths and in both themes `0.6765823467065926 mm`, `6.646835306586815 mm`, `15.011106998930268 mm` and `3670.874961137891 mm³` each sit whole on a line of their own under their label, at the right edge of their cell and above its dashed line; nothing touches `Head height` or any neighbouring cell. Labels wrap as phrases, at most 4 lines (for example `Thread depth (ISO 68-1:2023` then `basic profile)`), never one word a line. `8 mm`, `1.25 mm`, `13 mm`, `12.73 mm`, `5.3 mm` and `56` stay on their label's first line at the right. Nothing rounded, cut or ellipsized. The injected value reads `0.00010825317547305484` with `mm` on the line under it, its digits never split. The picker, badge, notes and downloads row wrap cleanly and stay readable in both themes, as in UAT tests 1 and 4.
**Why human:** line breaks, overlap and contrast are visible only on a rendered page; no browser in the gate (L01).

#### 2. Owner's ruling on the eight open review findings

**Test:** rule on WR-03, IN-05, IN-06, IN-07, IN-08, WR-04, IN-09 and IN-10 in `04-REVIEW-DISPOSITION.md` (UAT test 6 recorded `pass` without naming a disposition).
**Expected:** each fixed, filed under `docs/tech_debt/` with sign-off, or skipped, and the rows updated.
**Why human:** CLAUDE.md requires the owner's sign-off for any deferral.

#### 3. Light theme and narrow layout of plans 04-13 and 04-16

**Test:** covered by item 1 (same page, both themes); also look under 820 px.
**Expected:** picker, badge, grouped panel, notes and the downloads row wrap cleanly with readable contrast.
**Why human:** UAT 1 was an orchestrator pre-run in dark theme only; layout and contrast are visual.

### Gaps Summary

No gaps. Gap G-04-5 is closed in the code and in the gate: the `#dims` row wraps, the label claims half of it, the value keeps full precision and drops whole under its label, `make verify` pins the three rules and shows its check flags the old ones, and a headless Chrome measurement of the committed sheet found 0 px of overflow at 720 and 1920 px in both themes. What remains is the owner's browser re-run of UAT test 5 (the one behavior-unverified truth, deferred by the plan to end-of-phase UAT) and the owner's rulings on eight open review findings. `04-UAT.md` still records test 5 as `issue` and gap G-04-5 as `status: failed`; those two lines are stale against the code and are the owner's to flip when the re-run reports the expected layout. When it does, the phase can be marked passed and REQUIREMENTS.md can tick THRD-03, TYPE-01, TABL-06, TABL-07 and INFO-05.

---

_Verified: 2026-10-12T20:30:00Z_
_Verifier: Claude (gsd-verifier)_
