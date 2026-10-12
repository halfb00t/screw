---
phase: 04-iso-hex-bolts-and-screws
verified: 2026-10-12T17:35:00Z
status: human_needed
score: 9/10 must-haves verified
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
covered_digest: "v3:sha256:f035ea37af25bdbbc459e4d8de42aebd777e613576eb447f100ccfd4cb6b4292"
behavior_unverified: 1
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 6/8
  gaps_closed:
    - "G-04-3: the Download STL link never points at a download the server refuses (UAT test 3, review IN-02; plans 04-15 and 04-16)"
    - "Truth 2 (UI picker cascade) and truth 5 (badge transitions): the page half was human-confirmed by UAT test 1 (pass); that code is unchanged since"
  gaps_remaining: []
  regressions: []
behavior_unverified_items:
  - truth: "The page builds both download links from info.downloads: Download STL (preview) with the refusal sentence as its tooltip where the fine STL is refused, Download STEP unchanged, both disabled under their static labels after a failed update (G-04-3, plan 04-16 truth 5, verification: backstop)"
    test: "make serve; empty hash; pick ISO 4017 / M8 / 70, hover the STL button, click it, click Download STEP; tick Left-hand thread; untick and pick M8 / 65; set Length 10 and Thread length 30; repeat in the other theme and under 820px"
    expected: "Empty hash: Download STL and Download STEP, no tooltip. M8 / 70: the STL button reads Download STL (preview), the tooltip begins 'thread_length and length: the fine STL of a right-hand thread with d 8 and pitch 1.25 is refused above 67.5 mm of thread (54 turns)', the click saves an .stl file (not a JSON body), Download STEP saves the .step, the same sentence shows as a warning, the hash carries mm fields only. Left-hand ticked: Download STL again. M8 / 65: Download STL, no tooltip. Length 10 with Thread length 30: the error shows and both buttons are disabled under their static labels"
    why_human: "The anchor download, the tooltip and the on-screen label are visible only in a browser. No committed test executes app.js (L01): tests/test_parity.py asserts the source of setDownloads and applies rule 17 to the document with a Python copy of the algorithm (04-REVIEW WR-03). The verifier ran the real setDownloads from app.js under node with a stub DOM and the four cases held (see Behavioral Spot-Checks), which is evidence for the human check and not a substitute for it. The executor deferred this check to end-of-phase UAT (04-VALIDATION.md, Manual-Only)"
human_verification:
  - test: "Run the browser steps of plan 04-16 Task 1 (listed in behavior_unverified_items above)"
    expected: "As in the item above"
    why_human: "Deferred by the plan to end-of-phase UAT; the download, the tooltip and the layout need a real page"
  - test: "Look at the page in the light theme and in a window narrower than 820px (plans 04-13 and 04-16)"
    expected: "Picker, badge, grouped panel, notes and the downloads row (the longest label Download STL (preview) is 22 characters) wrap cleanly and keep contrast in both themes"
    why_human: "UAT test 1 was pre-run in the dark theme only; light theme, contrast and the 820px wrap were not looked at (04-UAT.md note). Layout and contrast are visual"
  - test: "Rule on the open findings of the incremental review of the gap closure: WR-03, IN-05, IN-06, IN-07, IN-08 (04-REVIEW-DISPOSITION.md, open: 5)"
    expected: "Each is fixed, filed under docs/tech_debt/ with sign-off, or skipped by the owner"
    why_human: "CLAUDE.md: a deferred item needs the owner's sign-off. None is a must-have failure. WR-03 is the one warning: the rule 17 test checks a Python copy of the algorithm, not app.js, which is exactly why the page behavior above is held for a human"
---

# Phase 4: ISO Hex Bolts and Screws Verification Report

**Phase Goal:** A user picks "M6 x 20, ISO 4017" (or an ISO 4014 size and length) and gets a hex head bolt or screw whose explicit millimetre fields were filled from a cited, tested table row, with an info panel whose every number traces to a field or a row.
**Verified:** 2026-10-12T17:35:00Z, at HEAD `e9a7f8d0f8f10d3df5511a3d7e7b1c9e89403bc3`
**Status:** human_needed
**Re-verification:** Yes, after gap closure G-04-3 (plans 04-15 and 04-16). Previous report: `human_needed`, 6/8, with two page truths held at PRESENT_BEHAVIOR_UNVERIFIED.

## Verdict

The goal is achieved in the code and gap G-04-3 is closed on the server side and in the page source. No must-have FAILED and no BLOCKER was found. The status is `human_needed` for one reason that is a must-have: the page half of G-04-3 (the `Download STL (preview)` link, its tooltip and the saved file) is tagged `verification: backstop` by its own plan, no committed test runs the page, and the executor deferred the browser steps to end-of-phase UAT as the orchestrator said. Two further human items (light theme and the 820px wrap; the owner's ruling on five open review findings) do not touch the goal.

What changed against the first report:

- The two page truths held at PRESENT_BEHAVIOR_UNVERIFIED (picker cascade, badge transitions) are now VERIFIED: `04-UAT.md` test 1 is `result: pass` (committed in 935cccc), and `git diff afb9d04..HEAD -- src/screw/static/app.js` shows only `setDownloads`, the `downloadLinks` map and one line of `update()` changed, so the code that run observed (`buildPicker`, `pick`, `showPicks`, `showMatch`) is unchanged. Provenance note: the UAT note says the run was an orchestrator pre-run in dark theme only; I accept the recorded `pass` as the human result the first report asked for and carry the unlooked light-theme and 820px part as a human item.
- The first report's human item 2 (long-preset STL download) is resolved by G-04-3: the owner ruled option a, and the page no longer links a refused download.
- The first report's open review findings were ruled on 2026-10-12: WR-01, WR-02, IN-01, IN-04 fixed, IN-02 fixed by G-04-3, IN-03 skipped by the owner (as designed, D-25). The incremental review of the gap closure opened five new items (WR-03, IN-05 to IN-08, none critical).

Evidence I produced myself, not read from SUMMARYs:

- `make verify` run once at HEAD from the repo root: ruff "All checks passed", mypy --strict "Success: no issues found in 59 source files", import-linter "Contracts: 9 kept, 0 broken", unfinished-work scan clean, pytest `2635 passed in 69.61s`, coverage 97.33% (floor 96), exit 0.
- Live API through `TestClient` with the app lifespan running: the empty query answers designation `Hexagon head screw ISO 4017 - M6 x 20`, preset exact `iso4017:M6x20` and four `downloads` entries in the order stl fine, stl preview, step fine, step preview, none refused. For the row `iso4017:M8x70` (d 8, pitch 1.25, length 70, s 13, k 5.3, thread_length 70) only the stl fine entry carries a refusal. The model route then answered the entries as the document says: stl fine `422 fine_stl_cap`, stl preview `200 model/stl` (4,813,884 bytes), step fine and step preview `200 model/step` (3,367,238 bytes).
- Across all 294 catalogue rows through `/api/bolt/info`: exactly 62 rows carry a refusal (the pinned count of `test_the_fine_stl_refused_presets_are_counted`, unchanged), none of them refuses its first STL entry without the document saying so, and no row leaves a format without a served entry.
- CLI: `python -m screw info bolt --preset iso4017:M8x70` prints the same downloads (stl fine refused only). `screw export bolt --preset iso4017:M8x70 -o x.stl` exits 2 with `error: thread_length and length: the fine STL of a right-hand thread with d 8 and pitch 1.25 is refused above 67.5 mm of thread (54 turns) ...` and writes no file; with `--quality preview` it exits 0 and writes the 4,813,884-byte STL, the same size the route served.
- The fine-STL warning is still on the document, after the standing warning, with the same text as the refusal sentence (printed live above and by `screw export --quality preview`), so L02's "never a silent downgrade" holds: the preview link is labelled, carries the reason as its title and the warning stays.
- A node harness (scratchpad, not in the repo) extracted the real `downloadLinks`/`setDownloads` text from `app.js` and ran it on a stub DOM; see Behavioral Spot-Checks.
- The data half (ISO 262, 4017 and 4014 tables against the purchased-edition preview pages, three-way read) was done in the first verification and `src/screw/tables/*` is byte-unchanged since except the `assert` to `raise ValueError` edit in `presets.py` (IN-01); the 294 per-row tests and the two diff tests run green inside the 2635.

## Goal Achievement

### Observable Truths

| # | Truth (source) | Status | Evidence |
|---|----------------|--------|----------|
| 1 | A user can pick standard + size + length across M2 to M20 per ISO 262 (second-choice bracketed, coarse only) on the API and the CLI and get an ISO 4014 bolt or ISO 4017 screw up to 200 mm; parity is green (SC1; TYPE-01, TYPE-02, TABL-01, TABL-05) | ✓ VERIFIED | `/api/presets?kind=bolt` returns 294 rows, ids and fields read live; `screw info bolt --preset` and `screw export bolt --preset` accept the same ids; `tests/test_presets.py` round-trips every row to its own exact match; the parity tests are inside the green 2635. Plain planar ends are the amended SC1 wording (D-02) |
| 2 | The UI offers the same pick and writes the row's mm fields (SC1, UI half) | ✓ VERIFIED | `index.html` `#picker`/`#badge`; `app.js` `loadPresets`, `buildPicker`, `pick` write `entry.fields` through `write()` then `update()`; source test pins it. Human: `04-UAT.md` test 1 `result: pass`; the functions are unchanged since (`git diff afb9d04..HEAD`). Light theme and 820px not looked at (human item 2) |
| 3 | The preset fills explicit mm fields only: the link carries mm fields, the preset id is metadata, opening the URL rebuilds the part without consulting a table; `thread_length` is filled by the preset and stays editable (SC2; TABL-01, THRD-03) | ✓ VERIFIED | `BoltParams` is `extra="forbid"`; catalogue `thread_length` is `length` for 4017 and `b` for 4014; contract "The parameters never consult a table" KEPT plus the `-I` runtime probes in `tests/test_import_boundaries.py`; the new `downloads` member does not enter `partQuery` or `writeHash` (asserted in `test_the_ui_builds_both_download_links_from_the_info_document_and_names_no_quality`; the function bodies hold no `quality` or `download`) |
| 4 | The designation line shows the ISO designation without a property class (SC3, second clause; TABL-07) | ✓ VERIFIED | live: `Hexagon head screw ISO 4017 - M6 x 20`; the ISO 4014 form and the left-hand withholding are unchanged and tested in `tests/test_tables.py`/`test_calc.py` |
| 5 | The badge reads "matches ISO 4017 M6 x 20" while the fields equal the row and "custom, based on ISO 4017 M6 x 20" once any field is edited (SC3, first clause; TABL-06) | ✓ VERIFIED | backend `preset.status` exact/custom with id and display, live: exact for the empty query; `showMatch` composes the strings (`app.js`, unchanged since the first report); human: UAT test 1 `pass` (Pitch edit, Length 82 off-row edit, Reset, pick, reload as listed in the first report) |
| 6 | Every table row carries a typed `Source`, so a row without one fails mypy; exactly one pure-data verification test per row generated from the table; an UNVERIFIED row is refused by the gate (SC4; TABL-02, TABL-03, TABL-04) | ✓ VERIFIED | `rows.py` kw_only dataclasses with required `source`; mypy control test; `test_row_relations` over 294 catalogue rows, `test_head_relations` over 36 heads, per-cell relation test over 108 cells; `test_no_row_in_the_tree_is_unverified` with a planted-row control; all green in `make verify`. Minor, as before: ISO 262 `Size` and `ThreadBand` rows have no 1:1 parametrized test, their invariants are checked through the aggregate and through every head and cell |
| 7 | The info panel numbers come from kernel-free maths, each traceable to an mm field or a cited, tested row; an uncomputable value is a warning and no number; any volume is the closed form; where ISO wrench size differs from the withdrawn DIN the panel adds a one-line note (SC5; INFO-03, INFO-05) | ✓ VERIFIED | `calc/__init__.py::_bolt`: rows are exact readings of fields, `thread_depth` or the closed form; cited rows only on an exact match; no-row part gets the no-row warning and no row values; `calc` never imports the kernel or the logger (contracts KEPT); the only edit since the first report is that the fine-STL warning is now appended from `_downloads(p)` refusals (same text, same position after the no-row warning: `test_the_fine_stl_warning_is_the_refused_downloads_reasons_once_in_entry_order` pins `[STANDING_WARNING, NO_ROW, *reasons]`) |
| 8 | The bolt the preset names builds as one valid solid with plain planar ends, gated by the THRD-04 postcondition including the bare-thread gate (TYPE-01, TYPE-02 geometry) | ✓ VERIFIED | `solid/bolt.py` and `solid/__init__.py` re-read: the gap-closure-adjacent edits are a rename (`bare_thread`) and `assert` to `BuildError` (IN-01, IN-04), no geometry change; live builds of `iso4017:M8x70` (stl preview, step) passed the `_build` gates; solid tests with positive controls are inside the 2635 |
| 9 | The info document carries a required `downloads` member, one entry per format and quality the model route serves in the page's order, each `refusal` equal to `download_refusal(p, fmt, quality)`; `/api/bolt/info` serves it and `screw info bolt` prints it identically; the route and `screw export` refuse exactly what it refuses; the fine-STL warning stays; the pinned 62 is unchanged (G-04-3, plan 04-15 truths) | ✓ VERIFIED | `calc/__init__.py` `Download`, `PartInfo.downloads` (required field), `_DOWNLOADS`, `_downloads(p)` over `download_refusal`; live M8 x 70 route/CLI/export agreement as listed in the Verdict; 62 rows refused across the catalogue, derived live; `tests/test_presets.py::test_every_catalogue_rows_document_agrees_with_the_shared_download_rule` and `..._rows_whose_stl_falls_back_to_the_preview_are_the_fine_stl_refused_rows` (both lists derived, nothing typed); `tests/test_api.py::test_every_download_the_document_lists_is_answered_by_the_route_as_it_says`; the 62 in `test_the_fine_stl_refused_presets_are_counted` is untouched in the diff |
| 10 | The page builds both download links from `info.downloads`, offers `Download STL (preview)` with the refusal sentence as its title where the fine STL is refused, keeps `Download STEP`, matches no warning text and holds no format name or quality preference (D-10), writes nothing to the hash (D-09); in a real browser M8 / 70 saves an STL not a JSON body (G-04-3, plan 04-16) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Present and wired: `app.js` `downloadLinks`, `setDownloads(q, downloads)`, called as `setDownloads(q, info.downloads)` from `update()` after `showModel`; `setDownloads(null)` on every failure path; `index.html` keeps the two static anchors. Source test `test_the_ui_builds_both_download_links_from_the_info_document_and_names_no_quality` (pins the only `info.*` and `download.*` members, no `'fine'`/`'stl'`/`'step'` literals, no warning text, `partQuery`/`writeHash` free of quality) and the label test pass. Not behaviorally proven by a committed test (WR-03). Node harness held; browser steps pending (human item 1). The plan itself tags this truth `verification: backstop` |

**Score:** 9/10 truths verified (1 present, behavior-unverified).

### Judgments

1. **L02, the owner's standing rule, on the new link.** A coarser mesh could pass for the fine one the user was refused. It does not: the label names the quality (`Download STL (preview)`), the title is the server's refusal sentence, the warning stays after the no-row warning, and `Download STEP` is not capped. The one place the quality does not travel is the saved file name (`Content-Disposition` carries no quality). The owner's ruling named the label and the link, not the header; the item is filed as `docs/ideas/2026-10-12-preview-stl-download-names-its-quality.md` with an INDEX row. Not a gap. Info.
2. **"A parameter the user did not set must never silently change the part."** The download state is not a parameter and never enters the link or the form. The explicit-conflict rule (IN-02/WR-02 refactor) still returns a 422 naming both fields; `explicit_conflict` is dispatched by kind and raises for an unregistered kind, so a new kind cannot inherit the bolt's rule.
3. **"Uncomputable value is a warning and no number."** The `Download` entry says `refusal` is null when the shared rule does not refuse on parameters alone, and it states that this is not a promise the build succeeds (a builder refusal is still a 422 `build_error`). Honest; no number is invented.
4. **REQUIREMENTS.md final state.** The file marks TYPE-02 and TABL-01 to TABL-05 `[x]`/Complete and leaves THRD-03, TYPE-01, TABL-06, TABL-07, INFO-03, INFO-05 `[ ]`/Pending. All six are proven in code at HEAD and TABL-06's page half now has the UAT pass; they can be ticked on this verification once the owner accepts the status. Ticking REQUIREMENTS.md, ROADMAP, STATE and "Last updated" is the orchestrator's. Caveat unchanged: TABL-04's text also names ISO 4032, 724 and 965-2 (Phase 5), the tick is the gate and the Phase 4 standards.
5. **Preset id case (D-11), badge basis (rule 33), owner ruling B, TDD without a RED commit.** Unchanged from the first report; code at HEAD agrees with that analysis. The first report's note that the 04-13 SUMMARY browser step 4 expected plain `custom` after a Pitch edit from an empty hash was stale against the shipped basis rule; UAT test 1 recorded the shipped behavior as the expected one.

### Amendments made inside the phase (read as the contract)

Commit `e376024` amended TYPE-01 and ROADMAP SC1 (tip chamfer and under-head fillet go to THRD-05, Phase 5), INFO-05 (M10, M12, M14 only) and SC2 (names `screw.params` and `screw.calc.thread`); pre-announced in 04-CONTEXT D-02 and D-20, and THRD-05 stays Pending. Verified against the amended text. The G-04-3 closure amended `01-UI-SPEC.md` (Hard constraints, Page Anatomy, Color, Copywriting, Interaction rules 13, 15, 17, 22, 29, E8, verification status; each names the pinning test) and L13 (a paragraph on `downloads`) with no existing L13 line changed, as plan 04-16 promised.

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
| `src/screw/calc/__init__.py` | `Download`, `PartInfo.downloads`, `_downloads` over `download_refusal`; kind-owned `explicit_conflict` | ✓ VERIFIED | 100% coverage; `downloads` is a required field (no default), so a kind's info builder cannot omit it |
| `src/screw/static/app.js` | `setDownloads(q, info.downloads)` building both links | ✓ VERIFIED (source) / ⚠️ behavior routed to human | see truth 10 |
| `src/screw/static/index.html` | two static anchors `#dl-stl`, `#dl-step` | ✓ VERIFIED | labels `Download STL`, `Download STEP`, pinned by the label test against the OpenAPI `fmt` enum |
| `src/screw/app.py`, `cli.py` | route-attached `refuse_explicit_conflict(kind)`; CLI calls the same `explicit_conflict` | ✓ VERIFIED | the global dependency is gone; the dependency is on `/api/bolt/info` and `/api/bolt/model.{fmt}`; `root_path` regression test from CR-01 still green |
| `tests/test_calc.py`, `test_api.py`, `test_parity.py`, `test_presets.py` | agreement of document, route, CLI and every catalogue row | ✓ VERIFIED | new tests listed in truth 9 and 10, all green |
| `docs/architecture/decision_log.md` (L13), `01-UI-SPEC.md`, `04-REVIEW-DISPOSITION.md`, `docs/ideas/*` | amendments in the same plan | ✓ VERIFIED | read; IN-02 `fixed` with the two commits named |
| `src/screw/tables/*`, `calc/presets.py`, `params.py`, `solid/*` | as in the first report | ✓ VERIFIED | unchanged but for IN-01/IN-04 edits, read |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `calc._bolt` | `download_refusal` | `_downloads(p)` once, warnings appended from the same list | WIRED | the document, the warning, the route and `screw export` read one rule |
| `app._serve` / `cmd_export` | `download_refusal` | direct call | WIRED | live: route 422 `fine_stl_cap`, export exit 2, same sentence |
| `app.py` model route | `Download` order and enums | OpenAPI | WIRED | `test_api.py` pins the set and the first quality to the route's `fmt` and `quality` parameters |
| `app.js update()` | `setDownloads` | `setDownloads(q, info.downloads)` after the preview mesh is shown | WIRED (source) | a failed info or mesh fetch leaves the links disabled (`setDownloads(null)` at the start of each update and on `fail`) |
| `app.js setDownloads` | `index.html` anchors | `downloadLinks` map of static labels, `#dl-<format>` lookup | WIRED | IN-06: the map selects every `.downloads a` while the lookup uses `#dl-<format>`; harmless today with two anchors |
| `cli info` | the same document | prints `PartInfo` as served | WIRED | live: equal downloads; `test_the_downloads_of_iso_4017_m8_x_70_...` asserts CLI == API, and that the refused sentence is the route's `msg` and export's error line |
| `params` / `calc.thread` | `tables` | none allowed | NOT IMPORTED (as required) | contracts 9 kept |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| Download links | `info.downloads` | `download_refusal(p, fmt, quality)` over the user's own fields | yes (62 of 294 rows refuse stl fine, live) | ✓ FLOWING |
| `title` of the preview link | `download.refusal` | the same sentence the route 422s with | yes | ✓ FLOWING |
| Info panel, picker, badge | as in the first report | stored `Source`-carrying rows, `/api/presets`, `PresetMatch` | yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| The gate | `make verify` | 2635 passed, 9 contracts kept, coverage 97.33%, exit 0 | ✓ PASS |
| Document, route and export agree for M8 x 70 | `TestClient` with lifespan: `/api/bolt/info` then each `model.{stl,step}?quality=` | stl fine 422 `fine_stl_cap`; stl preview 200; step fine/preview 200 | ✓ PASS |
| Refused count over the catalogue | `/api/bolt/info` for all 294 `fields` | 62 rows with a refusal; none without a served entry per format | ✓ PASS |
| CLI parity and refusal | `screw info bolt --preset iso4017:M8x70`; `screw export ... -o x.stl`; same with `--quality preview` | same downloads; exit 2, no file; exit 0, 4,813,884 bytes | ✓ PASS |
| Real `setDownloads` from `app.js` on a stub DOM (node) | all-served document; stl-fine-refused document; `q = null`; stl all refused | `Download STL` -> `...model.stl?d=8&length=70&quality=fine`; refused -> `Download STL (preview)`, `...quality=preview`, title = the sentence, `Download STEP` unchanged at `quality=fine`; `q=null` -> both disabled under static labels; stl all refused -> `Download STL` disabled, STEP linked | ✓ PASS (not a browser) |

### Probe Execution

Step 7c: SKIPPED. No PLAN or SUMMARY of this phase declares a probe script and `scripts/*/tests/probe-*.sh` does not exist.

### Requirements Coverage

Every ID in the 16 PLAN frontmatters is accounted for and equals the ROADMAP's list of twelve (the two gap-closure plans declare TABL-01 and TYPE-02). No ID is orphaned: REQUIREMENTS.md maps exactly these twelve to Phase 4 and no further ID.

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| THRD-03 | 04-04, 04-05, 04-06, 04-10, 04-12 | `thread_length` explicit mm; 4017 fills full length, 4014 fills `b`; editable | ✓ SATISFIED | truth 3; REQUIREMENTS.md still `[ ]` |
| TYPE-01 | 04-03, 04-04, 04-08, 04-10, 04-11, 04-14 | ISO 4014 hex bolt (amended, D-02) | ✓ SATISFIED | truths 1, 7, 8; REQUIREMENTS.md still `[ ]` |
| TYPE-02 | 04-03, 04-09, 04-15, 04-16 | ISO 4017 hex screw to 200 mm | ✓ SATISFIED | truths 1, 8, 9; every one of the 186 ISO 4017 rows has a served format, including the 62 whose fine STL is capped |
| TABL-01 | 04-12, 04-13, 04-15, 04-16 | pick standard + size + length; mm fields only | ✓ SATISFIED (G-04-3 link behavior pending human) | truths 1 to 3, 9; the picker's own primary action no longer ends in a 422 once truth 10's human check passes |
| TABL-02 | 04-07, 04-09, 04-10 | typed `Source` on every row | ✓ SATISFIED | truth 6 |
| TABL-03 | 04-07, 04-09, 04-10 | one pure-data test per row | ✓ SATISFIED | truth 6 |
| TABL-04 | 04-01, 04-07, 04-09, 04-10, 04-14 | purchased-copy rule, UNVERIFIED gate | ✓ SATISFIED for the Phase 4 standards | caveat in Judgments 4 |
| TABL-05 | 04-09, 04-12, 04-13 | M2 to M20 per ISO 262, brackets, coarse | ✓ SATISFIED | truth 1 |
| TABL-06 | 04-08, 04-13 | match badge | ✓ SATISFIED | truth 5 (backend tested, page human-confirmed by UAT 1) |
| TABL-07 | 04-07, 04-08, 04-13 | designation without a property class | ✓ SATISFIED | truth 4 |
| INFO-03 | 04-02, 04-03, 04-04, 04-05, 04-11, 04-13 | every number traces; no number rather than a plausible one; closed-form volume | ✓ SATISFIED | truth 7 |
| INFO-05 | 04-11, 04-13 | ISO wrench value and one-line DIN note for M10, M12, M14 | ✓ SATISFIED | truth 7 |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/`, `tests/`, `bench/` | | `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` scan | none found | `make verify`'s unfinished-work scan agrees |
| `tests/test_parity.py` | `_links_by_rule_17` | the rule 17 test applies a Python copy of the page's algorithm (04-REVIEW WR-03, open) | ⚠️ Warning | the page's link choice is source-asserted only; this is the reason truth 10 is held for a human. No product defect found: the real function behaved identically under node |
| `src/screw/calc/__init__.py` | above `_thread_length_warning` | comment now false after the fine-STL block moved (IN-05, open) | ℹ️ Info | wording only |
| `src/screw/static/app.js` | `downloadLinks` | selects every `.downloads a`, lookup by `#dl-<format>` (IN-06, open) | ℹ️ Info | fine with two anchors |
| `tests/test_calc.py` | | two tests compare `_downloads` to the call it is built from (IN-07, open) | ℹ️ Info | tautological but cheap; the independent route/CLI/catalogue tests carry the load |
| `tests/test_api.py` | | stub bytes for M8 x 70 enter the session-wide export cache (IN-08, open) | ℹ️ Info | test isolation |
| `src/screw/calc/thread.py` | `FINE_STL_ROWS` | INTERIM caps refuse the fine STL for 62 of 186 ISO 4017 presets | ℹ️ Info | owner-accepted bound (D-21, L13), now handled by the preview link; Phase 7 re-sweeps |

No stub, hollow prop or static-return data source found. `IN-03` (edit gives a 422 or a warning depending on whether `thread_length` equals 20) is skipped by the owner as designed (D-25, D-09).

### Human Verification Required

#### 1. Browser run of plan 04-16 Task 1 (the deferred `<human-check>`)

**Test:** `make serve` (or `SCREW_PORT=8001 make serve`), empty hash; pick ISO 4017 / M8 / 70, hover the STL button, click it, click Download STEP; tick Left-hand thread; untick it and pick ISO 4017 / M8 / 65; set Length 10 and Thread length 30.
**Expected:** Empty hash: `Download STL` and `Download STEP`, no tooltip. M8 / 70: the STL button reads `Download STL (preview)`, its tooltip begins `thread_length and length: the fine STL of a right-hand thread with d 8 and pitch 1.25 is refused above 67.5 mm of thread (54 turns)`, the click saves `bolt_d8_pitch1.25_left_hand0_length70_s13_k5.3_thread_length70.stl` (an STL, not a JSON body); `Download STEP` saves the `.step`; the same sentence shows as a warning under the buttons; the hash carries mm fields only. Left-hand ticked: `Download STL` again (the left-hand M8 has no cap, D-21). M8 / 65: `Download STL`, no tooltip. Length 10 with Thread length 30: the error shows and both buttons are disabled under `Download STL` and `Download STEP`.
**Why human:** the anchor download, the tooltip and the label on screen are visible only in a browser; no committed test runs `app.js`.

#### 2. Light theme and narrow layout

**Test:** repeat the page in the light theme and in a window narrower than 820px (the downloads row with `Download STL (preview)`, the picker, the badge, the grouped panel and notes).
**Expected:** clean wrap, readable contrast, no clipped label.
**Why human:** UAT test 1 was run in dark theme only; layout and contrast are visual.

#### 3. Owner's ruling on the open review findings

**Test:** rule on WR-03, IN-05, IN-06, IN-07, IN-08 in `04-REVIEW-DISPOSITION.md`.
**Expected:** each fixed, filed under `docs/tech_debt/` with sign-off, or skipped.
**Why human:** CLAUDE.md requires the owner's sign-off for deferral. No debt item was filed by this verification.

### Gaps Summary

No gaps. Gap G-04-3 is closed: the info document carries `downloads` from the single `download_refusal` rule, the model route, `screw export`, the CLI and all 294 catalogue rows agree with it, the fine-STL warning is preserved, and the page source builds its links from the document and labels the preview link. What remains is the owner's browser confirmation of that link (the one behavior-unverified truth, deferred by the plan to end-of-phase UAT), the visual pass in the light theme and under 820px, and the owner's rulings on five open review findings. When the browser run reports the expected strings, the phase can be marked passed and REQUIREMENTS.md can tick THRD-03, TYPE-01, TABL-06, TABL-07, INFO-03 and INFO-05.

---

_Verified: 2026-10-12T17:35:00Z_
_Verifier: Claude (gsd-verifier)_
