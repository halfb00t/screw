---
phase: 04-iso-hex-bolts-and-screws
verified: 2026-10-12T13:55:00Z
status: human_needed
score: 6/8 must-haves verified
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
  - "tests/test_import_boundaries.py"
  - "tests/test_parity.py"
  - "tests/test_presets.py"
  - "tests/test_tables.py"
  - "tests/test_tables_second_entry.py"
covered_digest: "v3:sha256:cabf64f8850bce6259d7334c96dae986b3091973ce4ce4ad6c335efc99b050ef"
behavior_unverified: 2
overrides_applied: 0
behavior_unverified_items:
  - truth: "The UI picker resolves a change in any of the three selects to one complete row, writes the six mm fields through the form and rebuilds at once, and the selects follow the fields afterwards (SC1, UI half)"
    test: "make serve; open an empty hash; pick ISO 4014, then M10, then 80; change Standard back to ISO 4017; choose a bracketed size such as (M3.5)"
    expected: "Selects read ISO 4017 / M6 / 20 on an empty hash; the ISO 4014 pick fills d 10, pitch 1.5, length 80, s 16, k 6.4, thread_length 26 and leaves Left-hand thread as it was; the hash carries mm fields only; a bracketed size shows its brackets in the select and the badge"
    why_human: "The page's cascade and the hash are exercised only by source-string assertions in tests/test_parity.py; no committed test runs the page. The verifier ran the real pick/showPicks/showMatch functions of app.js under node against the live 294-row catalogue and the transitions held, but that run is not in the repository and is not a browser"
  - truth: "The badge reads 'matches <display>' while the fields equal a row and 'custom, based on <display>' once a field is edited (SC3, page half)"
    test: "In the browser: empty hash (badge matches ISO 4017 M6 x 20); edit Pitch to 0.75; Reset; pick ISO 4014 M10 x 80, edit Length to 75, then to 90, then Reset; reload a link with an edited field"
    expected: "Pitch edit reads 'custom, based on ISO 4017 M6 × 20' (NOT plain 'custom': the basis is the last exact match, rule 33); Length 75 reads 'custom, based on ISO 4014 M10 × 80'; Length 90 reads 'matches ISO 4014 M10 × 90'; Reset reads 'matches ISO 4017 M6 × 20'; a reloaded edited link reads plain 'custom'"
    why_human: "A state transition in page-session state (presetBasis) that no committed test executes; the backend status that feeds it (exact/custom) is tested. Note: step 4 of 04-13-SUMMARY.md's browser list says Pitch 0.75 reads 'custom'; with the shipped basis rule it reads 'custom, based on ISO 4017 M6 × 20' when the session began on the default part, so the SUMMARY's expectation is stale against its own Deviation 1"
human_verification:
  - test: "Run the six browser steps of 04-13-SUMMARY.md (picker cascade, badge transitions, panel groups and notes in light and dark, error-with-warnings, label wrap at 820px)"
    expected: "As in the two behavior_unverified_items above, plus: heading is the designation, groups Shank and thread / Head / Part, grade note after the standing warning in its own style, long labels wrap"
    why_human: "Layout, theme contrast and interactive select behaviour are visual; the orchestrator is running this in parallel with this verification"
  - test: "Open the page on a long ISO 4017 preset (for example ISO 4017 M20 x 200, or M8 x 70) and click Download STL"
    expected: "Decide whether the current behaviour is acceptable: the info panel warns that the fine STL is refused, the link then returns a 422 JSON body; the preview STL and the STEP of the same part are served"
    why_human: "62 of the 186 ISO 4017 presets (33% of them, 21% of the 294-row catalogue) cannot be downloaded as a fine STL because the INTERIM 64 MiB export budget caps the thread (D-21, L13; 04-REVIEW IN-02). The owner accepted the caps, not necessarily this page behaviour for the picker's own rows"
  - test: "Rule on the open code-review findings WR-01, WR-02, IN-01, IN-02, IN-03, IN-04 (04-REVIEW-DISPOSITION.md)"
    expected: "Each is fixed, filed as docs/tech_debt with sign-off, or skipped by the owner"
    why_human: "CLAUDE.md: a deferred item needs the owner's sign-off; none is a must-have failure, CR-01 (the one blocker) is fixed in 41c21ae"
---

# Phase 4: ISO Hex Bolts and Screws Verification Report

**Phase Goal:** A user picks "M6 x 20, ISO 4017" (or an ISO 4014 size and length) and gets a hex head bolt or screw whose explicit millimetre fields were filled from a cited, tested table row, with an info panel whose every number traces to a field or a row.
**Verified:** 2026-10-12T13:55:00Z
**Status:** human_needed
**Re-verification:** No, initial verification (no previous VERIFICATION.md in the phase directory).

## Verdict

The goal is achieved in the code. No must-have FAILED and no BLOCKER was found. Two page-side truths (the picker cascade and the badge transitions) are present, wired and source-asserted but no committed test executes them, so they are held at PRESENT_BEHAVIOR_UNVERIFIED and routed to the browser check the orchestrator is running. Those two items, the long-preset STL download decision and the open review findings are the only reasons the status is `human_needed` and not `passed`.

Evidence I produced myself, not read from SUMMARYs:

- `make verify` run once from `/Users/halfb00t/git/halfb00t/screw` at HEAD afb9d04: ruff, mypy --strict, import-linter (9 contracts kept, 0 broken), unfinished-work scan, pytest `2620 passed in 59.61s`, coverage 97.57% (floor 96), exit 0.
- Live API through `TestClient`: `/api/presets?kind=bolt` returns 294 rows, axes Standard/Size/Length, both standards, all 15 ISO 262 sizes (second-choice bracketed), longest ISO 4017 length 200; `/api/bolt/info` for the empty query returns designation `Hexagon head screw ISO 4017 - M6 x 20`, preset exact `iso4017:M6x20`; the ISO 4014 M10 x 80 fields return designation `Hexagon head bolt ISO 4014 - M10 x 80`, `b` 26, `lg,max` 54, `ls,min` 46.5, and the wrench note `16 mm (ISO 4014:2022); the withdrawn DIN 931 used 17 mm`; a length of 81 returns `custom`, no designation, the no-row warning and no cited rows; `length=10&thread_length=30` is a 422 `thread_length_conflict` on the plain path, under `root_path="/screw"` (the CR-01 fix) and on `model.stl`; `s=5` is `head_too_small`; `preset=` is `extra_forbidden`.
- Real builds through the CLI (`screw export bolt --preset ... --quality preview`): `iso4017:M6x20`, `iso4014:M10x80`, `iso4017:M2x4`, `iso4014:M20x200` each built in about 3 s past the THRD-04 gate; a STEP of `iso4014:M10x80` wrote 942 KiB.
- Independent third read of the shipped numbers against the purchased-edition preview pages in `/Users/halfb00t/Documents/standards` (not the owner copy and not the agent's second entry): ISO 262 Table 1 (all 15 sizes, coarse pitch and choice column), ISO 4017 Tables 1, 2 and 3 (`dw,min`, `e,min`, `k` min/max/nom, `s` min/nom, pitch for M2 to M20, both grades) all equal the shipped `HEADS`; ISO 4014 Table 2 rendered and read by eye (M5 to M12 length cells and `ls,min`/`lg,max`, `b` 16/18/20/22/26/30), Table 3 `b` row and Table 4 grade B cells (M16 160: 106/116; M18 160 and 180: 99.5/112 and 119.5/132; M20 160, 180, 200: 95.5/108, 115.5/128, 135.5/148; `c` 44/48/52) all equal `CELLS` and `BANDS`. No disagreement found.
- A node harness (scratchpad, not in the repo) extracted `buildPicker`, `pick`, `showPicks`, `showMatch` from the shipped `app.js` and drove them with the real catalogue: the cascade, the six written fields, the bracketed size, the blank-change resync and the badge strings behaved as the SUMMARY claims. Evidence for the human check, not a substitute for it.

## Goal Achievement

### Observable Truths

| # | Truth (source) | Status | Evidence |
|---|----------------|--------|----------|
| 1 | A user can pick standard + size + length across M2 to M20 per ISO 262 (second-choice sizes bracketed, coarse only) on the API and the CLI and get an ISO 4014 bolt or ISO 4017 screw up to 200 mm; parity is green (SC1; TYPE-01, TYPE-02, TABL-01, TABL-05) | ✓ VERIFIED | 294 catalogue rows (186 ISO 4017, 108 ISO 4014), 15 sizes; `GET /api/presets` and `screw presets bolt` print the same document (`tests/test_parity.py::test_the_cli_and_the_api_print_the_same_preset_catalogue`); `--preset` on `info` and `export` (`cli.py::_params`); every row round-trips to its own exact match (`tests/test_presets.py::test_every_catalogue_row_round_trips`, 294 cases); builds of four extreme rows passed the gate; parity test green inside `make verify`. Plain planar ends are the amended SC1 wording (D-02, below) |
| 2 | The UI offers the same pick and writes the row's mm fields (SC1, UI half) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | `index.html` has `#picker` and `#badge`; `app.js` `loadPresets`, `buildPicker`, `pick` write `Object.entries(entry.fields)` through `write()` then `update()`; `tests/test_parity.py::test_the_ui_builds_its_picker_from_the_catalogue_and_writes_fields_only` asserts the source. No committed test runs the cascade. Node harness run by the verifier held. Browser check pending (orchestrator) |
| 3 | The preset fills explicit mm fields only: link carries mm fields, preset id is metadata, opening the URL rebuilds the part without consulting a table; `thread_length` is filled by the preset (full length 4017, `b` 4014) and stays editable (SC2; TABL-01, THRD-03) | ✓ VERIFIED | `BoltParams` has `d, pitch, length, s, k, thread_length` and `extra="forbid"` (a `preset` key is a 422, checked live); catalogue `thread_length` is `length` for ISO 4017 and `_b_of(size, length)` for ISO 4014 (`test_row_relations`, `test_an_iso_4014_row_fills_thread_length_with_b_of_its_band...`); contract "The parameters never consult a table" KEPT plus `tests/test_import_boundaries.py` runtime probes (fresh `-I` interpreter: `BoltParams()` and `screw.solid` leave `screw.tables` out of `sys.modules`, with positive controls); the page's only fetches and the `partQuery`/`writeHash` bodies are asserted free of `presetBasis` and ids; the field is editable and a bad edit is a 422 or a warning (checked live) |
| 4 | The designation line shows the ISO designation without a property class (SC3, second clause; TABL-07) | ✓ VERIFIED | `Hexagon head screw ISO 4017 - M6 x 20`, `Hexagon head bolt ISO 4014 - M10 x 80` live; second-choice sizes carry no brackets in the designation and a comma decimal (`M3,5`); withheld for left-hand (`designation_for`, Clause 7 gives no left-hand form, 04-OWNER-READS.md); `tests/test_tables.py` asserts no `8.8`-shaped token |
| 5 | The badge reads "matches ISO 4017 M6 x 20" while the fields equal the row and "custom, based on ISO 4017 M6 x 20" once any field is edited (SC3, first clause; TABL-06) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Backend half verified: `preset.status` is `exact`/`custom` with id and display, exact float equality, live-checked. Page half: `showMatch` composes the three strings (`app.js` lines 163-175), asserted by source only. Node harness: default match then edit gives `custom, based on ISO 4017 M6 × 20`; pick M10 x 80 then edit gives `custom, based on ISO 4014 M10 × 80`. Judgment on the widened basis in "Judgments" below. Browser check pending |
| 6 | Every table row carries a typed `Source`, so a row without one fails mypy; exactly one pure-data verification test per row generated from the table; an UNVERIFIED row is refused by the gate (SC4; TABL-02, TABL-03, TABL-04) | ✓ VERIFIED | `rows.py` dataclasses are `kw_only` with no defaults and a required `source: Source`; `test_a_row_without_source_fails_mypy_strict_naming_source...` runs mypy over a bad and a good file; `test_row_relations` is parametrized over the 294 catalogue rows, `test_head_relations` over the 36 heads, a per-cell relation test over the 108 shank cells; the diff test `tests/test_tables_second_entry.py` reads six owner files cell by cell and is non-vacuous (15/18/186/18/15/108 rows asserted); `test_no_module_marks_a_row_unverified` text-scans `src/screw/tables`, `test_no_row_in_the_tree_is_unverified` walks every row, each with a control that sees a planted unverified row. The gate runs in every `make verify`, which is stricter than "a release build". Minor: ISO 262 `Size` rows and `ThreadBand` rows have no 1:1 parametrized test; their invariants are tested through the aggregate test and through every head and cell that cross-checks pitch and `b` |
| 7 | The info panel numbers (head, shank, thread) come from kernel-free maths, each traceable to an mm field or a cited, tested row; an uncomputable value is a warning and no number; any volume is the closed form; where ISO wrench size differs from the withdrawn DIN the panel adds a one-line note (SC5; INFO-03, INFO-05) | ✓ VERIFIED | `calc/__init__.py::_bolt`: every row is an exact reading of a field or `thread_depth`/`closed form`; volume is `bolt_closed_volume`, never `Volume()`; non-finite or sub-`MIN_TAIL_MM` rows are dropped with a named warning (IN-01 retired); cited rows (`s_min`, `e_min`, `k_max`, `k_min`, `dw_min`, `b`, `lg_max`, `ls_min`) appear only on an exact match, each labelled with its own table; no-row part gets `NO_ROW_WARNING` and no row values (checked live); `calc` never imports the kernel or the logger (contracts KEPT); wrench note only for M10, M12, M14 (`WITHDRAWN_DIN_WRENCH_MM`, `test_calc.py` pins all six texts and that no other size gets one). The DIN figures are web-sourced (two pages, MEDIUM confidence, D-20), not a purchased row; they are a note, not a panel number |
| 8 | The bolt/screw the preset names builds as one valid solid with plain planar ends, gated by the THRD-04 postcondition including the bare-thread gate (TYPE-01, TYPE-02 geometry) | ✓ VERIFIED | `solid/bolt.py` hex prism with `circumscribed=True`, plain shank fused at a planar face; `_build` gates the bare thread then the whole part against `bolt_closed_volume`; four CLI builds and one STEP passed; positive controls in `tests/test_solid.py` (inside the green 2620) |

**Score:** 6/8 truths verified (2 present, behavior-unverified).

### Judgments the orchestrator asked for

1. **REQUIREMENTS.md final state.** Today's file marks TABL-02, TABL-03, TABL-04, TABL-05 and TYPE-02 `[x]`/Complete and leaves THRD-03, TYPE-01, TABL-01, TABL-06, TABL-07, INFO-03, INFO-05 `[ ]`/Pending (traceability agrees). The five early ticks by plan 04-09 were premature at that moment (ISO 4014 rows did not exist until 04-10) but are correct now: every ISO 4014 and ISO 4017 row has a Source, a per-row test and the gate; all 15 sizes are held; ISO 4017 reaches 200. One caveat on TABL-04: its text also names ISO 4032, 724 and 965-2 and the Phase 5 precondition says the 4032 and 965-2 rows ship there, so the tick is the gate and the Phase 4 standards, not the whole v1 list; acceptable because the roadmap maps TABL-04 to Phase 4. Remaining ticks: THRD-03, TYPE-01, TABL-07, INFO-03, INFO-05 are proven in code and can be ticked on this verification; TABL-01 and TABL-06 each have a page half and should be ticked after the browser check passes. The Phase 4 ROADMAP checkbox, STATE and the "Last updated" line are the orchestrator's to move.
2. **Badge basis (rule 33) vs SC3.** SC3 is met as written. The shipped basis is "the last row the part matched exactly" (a pick, Reset, or an edit landing on another row); the plan and D-12 said "the picked row". The two differ only when a part passes through a second exact row before the next edit, where the plan's reading would show a stale row, which L02 forbids; plan 04-13's own expected sequence already had Reset reading `matches ISO 4017 M6 x 20`. It also makes the default-part case read exactly the TABL-06 example (edit the default and see `custom, based on ISO 4017 M6 × 20`). The deviation is recorded (04-13 Deviation 1, 01-UI-SPEC rule 33, L13) and pinned by a source test. Not a gap. Real defect found while checking: the 04-13 SUMMARY browser step 4 and the plan's wording expect plain `custom` after a Pitch edit from an empty hash; the shipped rule gives `custom, based on ISO 4017 M6 × 20`. The expectation is stale, not the code.
3. **Preset id case (D-11 "lowercase").** D-11 contradicts itself: it says lowercase and in the same sentence gives `iso4017:M6x20` and `iso4014:M10x80`. The shipped ids keep the capital M, are case-sensitive, and that is recorded in L13 and pinned (`expand('iso4017:m6x20')` is None in `tests/test_tables.py`, `tests/test_presets.py` and the CLI test that exits 2). The ids are metadata and never enter a link, so this changes no URL. Accepted; info only.
4. **Owner ruling B (generated owner copy).** Recorded in 04-OWNER-READS.md and L13, with the cost stated in L13 itself (the two copies share the same PDFs and differ in reading method; the diff cannot catch a printed error). The three hand-typed M6 files are byte-identical to the generator's output per the record. Because the independence is weaker than D-14 intended, I read the shipped numbers off the preview pages a third time (see evidence above) and found no disagreement. The one standing residue is that the second entry and the checks read the on-disk preview pages under the owner's ruling `A - 3.`, not the full purchased documents; that is the owner's recorded call and stays so. Accepted.
5. **Plan 04-13 browser checks.** No executor ran them. They are human_verification items 1 and 2 above and the two behavior_unverified_items. The node run is supporting evidence only.
6. **TDD without a RED commit.** The pre-commit hook rejects a failing suite, so no repo can hold a RED commit. Each TDD plan's SUMMARY records the RED run with source at HEAD and the assertion-level failures (plan 04-05 gives the failing counts and notes an import fault was not counted as RED). Judged against acceptance, not commit shape: met. One loose end from 04-05 is flagged for the verifier: the plan's must-have about "re-pinning a probe row" found nothing to re-pin; the behaviour it would pin is covered by the new tests.

### Amendments made inside the phase (read as the contract)

Commit `e376024` amended TYPE-01 and ROADMAP SC1 to drop "chamfered point, under-head fillet" (moved to THRD-05, Phase 5 with ISO 4753), INFO-05 to M10, M12, M14 only, and SC2 to name `screw.params` and `screw.calc.thread`. These were pre-announced in 04-CONTEXT D-02 and D-20 (owner discuss-phase rulings of 2026-10-11) and THRD-05 stays Pending, so no requirement is lost. I verified against the amended text. The unamended SC1 would fail on the chamfer and fillet; the owner chose that scope.

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|--------------|----------|
| 1 | Tip chamfer and under-head fillet | Phase 5 | ROADMAP Phase 5 requirement THRD-05 and its ISO 4753 precondition |
| 2 | Printability warning for small sizes | Phase 6 | INFO-04 maps to Phase 6 |
| 3 | Measured per-size build caps and a re-swept export budget (the cause of the 62 refused fine STLs) | Phase 7 | OPER-01 to OPER-03 and the INTERIM markers in `calc/thread.py` |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/screw/tables/rows.py` | typed row dataclasses with a required `Source` | ✓ VERIFIED | kw_only, no defaults; mypy test with control |
| `src/screw/tables/iso262.py` | 15 sizes, coarse | ✓ VERIFIED | equals the owner copy and the printed ISO 262 Table 1 (pitches and the first/second-choice column of all 15 sizes read from the preview page text) |
| `src/screw/tables/iso4017.py` | 18 heads, 186 lengths | ✓ VERIFIED | heads checked against Tables 1 to 3 of the preview pages |
| `src/screw/tables/iso4014.py` | 18 heads, 15 bands, 108 cells | ✓ VERIFIED | Tables 2 and 4 and the `b` rows checked against the preview pages |
| `src/screw/tables/presets.py` | catalogue and `expand` | ✓ VERIFIED | 294 rows, closed dict lookup, case-sensitive ids |
| `src/screw/calc/presets.py` | match, designation, cited rows, notes, catalogue document | ✓ VERIFIED | 100% coverage, wired from `_bolt` and `app.py`/`cli.py` |
| `src/screw/params.py` | `s`, `k`, `thread_length` with frozen defaults equal to the M6 x 20 row | ✓ VERIFIED | defaults `s 10, k 4, thread_length 20` equal the row and the owner's confirmation; test pins them |
| `src/screw/app.py` | `/api/presets`, conflict dependency on the matched route | ✓ VERIFIED | CR-01 fix confirmed live under `root_path` |
| `src/screw/cli.py` | `presets`, `--preset`, conflict rule | ✓ VERIFIED | unknown id exits 2; flags win; repeat refused |
| `src/screw/solid/bolt.py`, `solid/__init__.py` | hex head, plain shank, bare-thread gate | ✓ VERIFIED | builds past the gate |
| `src/screw/static/app.js`, `index.html` | picker, badge, grouped panel, unrounded numbers | ⚠️ present and wired, behavior routed to human | see truths 2 and 5 |
| `tests/data/owner/*.tsv` | six owner files | ✓ VERIFIED | non-vacuity counts asserted |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `app.py` presets route | `calc.presets.catalogue_document` | direct call | WIRED | live 294 rows |
| `calc.__init__._bolt` | `calc.presets.match/row_values/notes` | function-local import | WIRED | local import keeps tables behind `derive` only; runtime probe proves it |
| `cli._params` | `calc.presets.expand` then `thread_length_conflict` | merge then rule | WIRED | exit 2 on conflict |
| `app.refuse_thread_length_conflict` | matched `APIRoute` | `request.scope["route"]` | WIRED | 422 under `root_path` confirmed live |
| `app.js` pick | form inputs and `update()` | `write(fields.get(name).input, value)` | WIRED (source) | behavior in human items |
| `app.js` `showMatch` | `info.preset.status/display/id` | `renderInfo` | WIRED (source) | behavior in human items |
| `tables.presets` | `iso262`, `iso4014`, `iso4017` | imports | WIRED | contract "Tables are a leaf" KEPT |
| `params` / `calc.thread` | `tables` | none allowed | NOT IMPORTED (as required) | contract KEPT, runtime probe |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| Info panel cited rows | `row_values(row)` | stored `HexHead`/`ThreadBand`/`ShankCell` records, each with own `Source` | yes (values equal the PDF pages for the sampled cells) | ✓ FLOWING |
| Info panel computed rows | `p.*`, `thread_depth`, `bolt_closed_volume` | the user's own fields and the pinned profile | yes | ✓ FLOWING |
| Picker | `catalogue.rows` | `/api/presets` from `calc.presets.catalogue_document` | yes (294 rows) | ✓ FLOWING |
| Badge | `preset.display` | `PresetMatch` from `match(p)` | yes | ✓ FLOWING (page behavior unverified) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| The gate | `make verify` | 2620 passed, 9 contracts kept, coverage 97.57%, exit 0 | ✓ PASS |
| Catalogue document | `TestClient.get('/api/presets?kind=bolt')` | 294 rows, 15 sizes, max length 200 | ✓ PASS |
| Exact and custom match, designation, notes | `TestClient.get('/api/bolt/info?...')` | as listed in Verdict | ✓ PASS |
| Conflict 422 on plain path, `root_path`, model route | `TestClient` | 422 on all three | ✓ PASS |
| Build of four extreme presets | `python -m screw export bolt --preset ID --quality preview` | each built about 3 s | ✓ PASS |
| Table data against the standard | `pdftotext` and a rendered page of the preview PDFs | no disagreement in the sampled cells | ✓ PASS |
| Picker/badge functions of `app.js` | node harness on the real functions | transitions as claimed | ✓ PASS (not a browser) |

### Probe Execution

Step 7c: SKIPPED. No PLAN or SUMMARY of this phase declares a probe script and `scripts/*/tests/probe-*.sh` does not exist.

### Requirements Coverage

Every ID in the 14 PLAN frontmatters is accounted for and equals the ROADMAP's list of twelve. No ID is orphaned: REQUIREMENTS.md maps no further ID to Phase 4.

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| THRD-03 | 04-04, 04-05, 04-06, 04-10, 04-12 | `thread_length` explicit mm; 4017 fills full length, 4014 fills `b`; editable | ✓ SATISFIED | truth 3; code complete, REQUIREMENTS.md still `[ ]` |
| TYPE-01 | 04-03, 04-04, 04-08, 04-10, 04-11, 04-14 | ISO 4014 hex bolt: `s, e, k, dw, b, ls/lg`, grade (amended, D-02) | ✓ SATISFIED | truths 1, 7, 8; `e` and `dw` and `ls,min`/`lg,max` shown on exact match, grade as a note |
| TYPE-02 | 04-03, 04-09 | ISO 4017 hex screw to 200 mm | ✓ SATISFIED | 186 rows, M20 x 200 builds; already `[x]` and correct |
| TABL-01 | 04-12, 04-13 | pick standard + size + length; mm fields only | ✓ SATISFIED (UI half pending human) | truths 1 to 3 |
| TABL-02 | 04-07, 04-09, 04-10 | typed `Source` on every row | ✓ SATISFIED | truth 6 |
| TABL-03 | 04-07, 04-09, 04-10 | one pure-data test per row | ✓ SATISFIED | truth 6, minor note on Size and Band rows |
| TABL-04 | 04-01, 04-07, 04-09, 04-10, 04-14 | purchased-copy rule, UNVERIFIED gate | ✓ SATISFIED for the Phase 4 standards | caveat on 4032, 724 and 965-2 (Phase 5) in Judgments |
| TABL-05 | 04-09, 04-12, 04-13 | M2 to M20 per ISO 262, brackets, coarse | ✓ SATISFIED | 15 sizes, 4 bracketed |
| TABL-06 | 04-08, 04-13 | match badge | ⚠️ backend satisfied, page behavior routed to human | truth 5 |
| TABL-07 | 04-07, 04-08, 04-13 | designation without a property class | ✓ SATISFIED | truth 4 |
| INFO-03 | 04-02, 04-03, 04-04, 04-05, 04-11, 04-13 | every number traces; no number rather than a plausible one; closed-form volume | ✓ SATISFIED | truth 7 |
| INFO-05 | 04-11, 04-13 | ISO wrench value and one-line DIN note for M10, M12, M14 | ✓ SATISFIED | truth 7 |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/` and the phase's test and bench files | | `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` scan | none found | `make verify`'s unfinished-work scan agrees |
| `bench/head_fuse.py` | 74, 85 | fuses `thread.fuse(shank.fuse(head))`; the product fuses `thread.fuse(shank).fuse(head)` (04-REVIEW WR-01, open) | ⚠️ Warning | the D-03 probe is cited in L13 as measuring "what ships"; the `_build` gate protects users either way; owner ruling pending |
| `src/screw/calc/thread.py` | `FINE_STL_ROWS` | INTERIM caps refuse the fine STL for 62 of 186 ISO 4017 presets | ⚠️ Warning | owner-accepted bound (D-21, L13), logged as INTERIM, surfaced as a panel warning and a 422; see human item 2 |
| `src/screw/app.py`, `cli.py` | | kind-specific conflict rule hard-coded in generic paths (WR-02, open) | ⚠️ Warning | Phase 5's nut is the named trigger |
| `src/screw/params.py` and solid | | edit gives 422 or warning depending on whether `thread_length` equals 20 (IN-03) | ℹ️ Info | as designed under D-25 |

No debt marker, no stub, no hollow prop and no static-return data source found. The ISO 4014 and ISO 4017 head values being equal per size and grade is the owner's confirmed answer A3 and is pinned by a test, not a copy-paste stub.

### Human Verification Required

#### 1. Browser run of plan 04-13's checks (in progress by the orchestrator)

**Test:** `make serve`, empty hash; pick ISO 4014 / M10 / 80; edit Length to 75 then 90; Reset; edit Pitch to 0.75; reload an edited link; pick a bracketed size; force a request error; check long labels at 820 px in light and dark.
**Expected:** as in the two `behavior_unverified_items`. Pitch 0.75 from an empty hash reads `custom, based on ISO 4017 M6 × 20`, not plain `custom` (the 04-13 SUMMARY step 4 is stale on this point).
**Why human:** interactive selects, the hash, theme contrast and layout; no committed test runs the page.

#### 2. Fine-STL refusal on the picker's own long presets

**Test:** click Download STL on `ISO 4017 M20 x 200` or `ISO 4017 M8 x 70`.
**Expected:** owner decision on whether a 422 JSON body behind a link the page itself offers is acceptable until Phase 7, or whether the link should be disabled or switched to the preview quality for refused parts (04-REVIEW IN-02).
**Why human:** a product decision; the part is delivered through the preview STL and the STEP and the panel names the refusal.

#### 3. Open code-review findings

**Test:** rule on WR-01, WR-02, IN-01, IN-02, IN-03, IN-04.
**Expected:** each fixed, filed under `docs/tech_debt/` with sign-off, or skipped.
**Why human:** CLAUDE.md requires the owner's sign-off for deferral. No debt item was filed by this verification.

### Gaps Summary

No gaps. Nothing in the codebase contradicts a must-have, and the data was independently re-read from the standard's own pages. What remains is the page-behavior confirmation in a real browser (two truths held at PRESENT_BEHAVIOR_UNVERIFIED), one product decision about the long-preset STL download, and the owner's rulings on the open review findings. When the browser run reports the expected strings, the phase can be marked passed and REQUIREMENTS.md can tick THRD-03, TYPE-01, TABL-01, TABL-06, TABL-07, INFO-03 and INFO-05.

---

_Verified: 2026-10-12T13:55:00Z_
_Verifier: Claude (gsd-verifier)_
