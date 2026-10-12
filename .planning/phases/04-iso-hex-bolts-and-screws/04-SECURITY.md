---
phase: "4"
slug: "iso-hex-bolts-and-screws"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-12"
---

# Phase 4 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

Register origin: every one of the 14 plans carries a `<threat_model>` block (authored at plan time), so this audit verifies the declared mitigations and scans for nothing new. ASVS level 1 and `threats_open: 0` after the grep-level classification below, so no auditor agent was spawned (secure-phase short-circuit rule). Evidence is a file, a line or a test name in this repository at the audited commit; the SUMMARY `## Threat Flags` sections of all 14 plans were read and none flags a new surface.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| purchased PDF → repository | licensed text and layout never cross into git (D-16); the repository holds per-size numeric records and an identifier-only `Source` | `*.pdf`, `/.standards/` ignored; no PDF or PNG tracked; `tests/data/owner/*.tsv` are the owner's per-size numeric copies, not layout |
| purchased standard → owner copy → shipped rows | a value ships only when two transcriptions agree (TABL-04); the owner's half is generated from the purchased PDF text layer under ruling B (2026-10-12), the agent's half read from page images | ISO 262, 4017 and 4014 values, diffed cell by cell in `tests/test_tables_second_entry.py` |
| HTTP query / CLI argv → `params` | `s`, `k`, `thread_length`, a preset id and `kind` are user text; validated once at the model boundary (L02), except the explicit-conflict rule that reads the raw `length` / `thread_length` pair before the model (D-25) | untrusted strings → `BoltParams`; a conflict is a 422 / exit 2 naming both fields |
| `params` → `solid` (kernel) | the bare-thread gate and the whole-part gate run inside the cached build; a sliver below 1e-3 mm is folded or refused before the kernel | trusted floats; a refused build never reaches `lru_cache` or an export |
| tables → rebuild path | a link rebuilds the same part without consulting a table: contracts 6 and 7 plus the `sys.modules` runtime control | `screw.params` and `screw.calc.thread` never import `screw.tables`; `screw.tables` imports nothing of ours |
| tables → info document → DOM | a row's cited values reach the panel only through an exact match; the page writes text only; the hash carries millimetres only | `PresetRow` fields, designation, notes, labels → `textContent` / `new Option` |
| bench records → code | a typed fine-STL cap must be one the committed grid records hold; the corpus pins `s`, `k`, `thread_length` | JSONL records → `FINE_STL_ROWS`; `bench/corpus.py` |
| decisions → later phases | Phase 5 reads L13 for the document shape, the tables and the fields | `docs/architecture/decision_log.md` |
| host → system tools | poppler installed through Homebrew on the owner's machine only, outside the project closure (L06) | nothing enters the repository or its dependency files |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-04-01 | Information disclosure | `.gitignore`, page renders | medium | mitigate | `.gitignore` has `*.pdf` and `/.standards/`; `git ls-files '*.pdf' '*.png'` is empty; the six tracked `tests/data/owner/*.tsv` files are per-size numeric records (D-16), the double-entry's owner half | closed |
| T-04-02 | Tampering | owner copy, D-07 defaults | high | mitigate | Plans 04-01 and 04-09 carry `blocking-human` checkpoints the owner answered (`04-OWNER-READS.md`: ruling `A - 3.`, `permanent: accepted`, A1, A3, ruling B); values come from the purchased copies via the PDF text layer and page images, never a preview or a web table | closed |
| T-04-SC | Tampering | npm / pip / cargo installs | low | accept | No package was added in Phase 4: `git diff main...HEAD -- pyproject.toml` adds only import-linter contracts 6 and 7; `requirements*.txt` and `web/package.json` are unchanged; poppler is a Homebrew install on the owner's machine (04-01) | closed — accepted |
| T-04-03 | Denial of service | `FINE_STL_ROWS` left-hand caps | medium | mitigate | `tests/test_thread_maths.py::test_every_cap_is_the_longest_measured_length_that_fits_in_the_grid_records` recomputes each cap from the JSONL records; a typed first-over value fails it | closed |
| T-04-04 | Denial of service | `s`, `k` up to 1e5 mm | low | accept | Bounds `gt=0`, `le=INTERIM_MAX_MM`, finite at the model; the head is one prism (D-03 probe, tens of kB fine); the interim bounds are the debt row `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` for Phase 7 (OPER-02) | closed — accepted |
| T-04-05 | Tampering | `_build` fused part vs the gate | high | mitigate | `tests/test_solid.py:179 test_a_thread_wrong_by_a_part_in_ten_thousand_is_refused_on_the_thread_not_the_whole` (positive control) and `:201 test_the_good_thread_of_the_same_screw_passes_both_gates`; both gates sit inside the cached build in `src/screw/solid/bolt.py` | closed |
| T-04-06 | Denial of service | long cheap shank (`length` up to 1e5 mm with a short thread) | medium | accept | By design (D-22): the caps bound the thread, the shank is one cylinder; `INTERIM_MAX_MM` and the 30 s timeout are the backstops; recorded for Phase 7 in the interim-bounds debt row by plan 04-14 | closed — accepted |
| T-04-07 | Tampering | conflict rule split between API and CLI | medium | mitigate | One `thread_length_conflict` in `src/screw/calc/thread.py`, called from `src/screw/app.py` and `src/screw/cli.py`; `tests/test_parity.py` pins the same text on both; `tests/test_api.py` and `tests/test_cli.py` exercise it | closed |
| T-04-08 | Denial of service | shank sliver below 1e-3 mm crashing the kernel | high | mitigate | `built_thread_length` in `src/screw/calc/thread.py` is the one fold for every consumer (`solid/bolt.py`, `calc/__init__.py`, `params.py`); 0.0005 mm and 0.001 mm cases in `tests/test_solid.py`, `tests/test_calc.py`, `tests/test_api.py`; `tests/test_solid.py:126` refuses a thread below the floor before the kernel | closed |
| T-04-09 | Tampering | an UNVERIFIED row reaching `main` | high | mitigate | `tests/test_tables.py:472` text scan (`_UNVERIFIED` over every tables module) and runtime walk of every row, each with a positive control; runs in `make verify` (pre-commit, CI, `make pr.land`) | closed |
| T-04-10 | Tampering | the agent copy biased by the owner copy | medium | mitigate | 04-07: transcription from page images preceded opening the owner copy (04-07-SUMMARY); 04-09/04-10: the owner half is generated mechanically from the PDF text layer (ruling B), the agent half read from page images, diffed by `tests/test_tables_second_entry.py` (5 tests); disagreements go to the owner | closed |
| T-04-11 | Elevation of privilege | `params` / `calc.thread` reaching `tables` through the `calc/__init__` edge | medium | mitigate | `pyproject.toml` contract "The parameters never consult a table" (indirect imports checked); `tests/test_import_boundaries.py` subprocess `sys.modules` probe with its control | closed |
| T-04-12 | Information disclosure | licensed layout in the repository | medium | mitigate | Per-size records only, identifier-only `Source` (`src/screw/tables/rows.py`); no PDF or PNG tracked; renders stay in the session scratch directory | closed |
| T-04-13 | Tampering | transcription error in a shipped ISO 4017 / ISO 262 row | high | mitigate | `tests/test_tables.py` (47 tests: per-row relations, series rules, cross-table checks) and `tests/test_tables_second_entry.py` (owner diff), all in `make verify` | closed |
| T-04-14 | Information disclosure | licensed layout (ISO 4017 lengths) | medium | mitigate | Same controls as T-04-12: per-size records, no tolerance columns, renders outside git | closed |
| T-04-15 | Tampering | a mis-typed `ls,min` / `lg,max` or `b` | high | mitigate | `tests/test_tables.py:203 test_a_printed_shank_cell_satisfies_lg_max_and_ls_min_from_its_bands_b` (`lg,max = l − b`, `ls,min = lg,max − 5P` on the stored cells) plus the owner diff | closed |
| T-04-16 | Tampering | a row value shown for a part that is not that row | high | mitigate | `src/screw/calc/presets.py:32 match` is exact float equality over every field the row defines, no nearest-row inference; `tests/test_calc.py:308`, `:456`, `:465` (custom, non-coarse, edited) | closed |
| T-04-17 | Repudiation | DIN wrench values without a purchased source | low | accept | `src/screw/calc/presets.py:26 WITHDRAWN_DIN_WRENCH_MM` limited to M10, M12, M14 with its two cited sources and MEDIUM confidence in the comment (D-20); L13 records it | closed — accepted |
| T-04-18 | Tampering | `--preset` id | medium | mitigate | `src/screw/tables/presets.py:138` dict `.get`, never a path or `eval`; `src/screw/cli.py:36 _Once` refuses a repeat; `tests/test_presets.py:106` unknown id exits 2 naming it, `:116` repeat exits 2 | closed |
| T-04-19 | Information disclosure | `kind` echoed in the 404 | low | accept | Same `!r` echo as `/api/schema`, JSON body only; the page writes text only (`tests/test_parity.py:479`) | closed — accepted |
| T-04-20 | Denial of service | `/api/presets` cost | low | mitigate | `src/screw/tables/presets.py:84` and `:128` `@cache`; the route (`src/screw/app.py:424`) reads in-memory rows and never touches the kernel | closed |
| T-04-21 | Tampering (XSS) | catalogue and document strings in the DOM | medium | mitigate | `tests/test_parity.py:479 test_the_ui_builds_nodes_from_text_only` forbids the HTML sinks; new nodes use `createElement`, `textContent`, `new Option` | closed |
| T-04-22 | Tampering | a stale preset basis riding in links | medium | mitigate | `src/screw/static/app.js:23 presetBasis` is session state, reset at `:258` in `navigate()`; `tests/test_parity.py` asserts it is absent from `partQuery` / `writeHash` and lists the only four fetch URLs | closed |
| T-04-23 | Repudiation | an undocumented locked choice | low | mitigate | `docs/architecture/decision_log.md:539 ## L13` records every Phase 4 D-xx with its source; `docs/architecture/overview.md` lists contracts 6 and 7 | closed |
| T-04-24 | Repudiation | a bench workload whose meaning drifts under recorded figures | low | mitigate | `bench/corpus.py:31` pins `s`, `k`, `thread_length` per entry; `tests/test_bench.py` spells each entry out | closed |
| T-04-25 | Elevation of privilege | `calc/__init__.py` importing `screw.calc.presets` at module top | medium | mitigate | No module-top import (`grep -E '^from screw\.calc\.presets' src/screw/calc/__init__.py` prints nothing); the import sits inside `_bolt` at `src/screw/calc/__init__.py:111`; the `derive` converse in `tests/test_import_boundaries.py` | closed |
| T-04-26 | Repudiation | info numbers for a part the builder refuses | medium | mitigate | `MIN_TAIL_MM` in `src/screw/calc/thread.py`; `tests/test_calc.py:258 test_a_thread_too_short_to_build_gets_a_warning_and_no_turns_or_volume`; API case in `tests/test_api.py` | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-04-01 | T-04-SC | No package added; the only host install (poppler) is the owner's choice outside the project closure (L06) | owner, via the approved plan registers 04-01 … 04-14 | 2026-10-11 |
| AR-04-02 | T-04-04 | `s`, `k` bounded by `INTERIM_MAX_MM`; the head is one prism; Phase 7 re-sweeps (OPER-02) | owner, via plan 04-03's register; debt row 2026-10-05-interim-runtime-bounds | 2026-10-11 |
| AR-04-03 | T-04-06 | D-22: a long plain shank is one cheap cylinder; `INTERIM_MAX_MM` and the 30 s timeout backstop it; recorded for Phase 7 | owner, via plan 04-04's register and D-22 | 2026-10-11 |
| AR-04-04 | T-04-17 | DIN wrench sizes are a note on three sizes only, with two cited sources and MEDIUM confidence (D-20) | owner, via plan 04-11's register and D-20 | 2026-10-11 |
| AR-04-05 | T-04-19 | `kind` echo in a JSON 404 matches `/api/schema`; no HTML sink | owner, via plan 04-12's register | 2026-10-11 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-12 | 27 | 27 | 0 | execute-phase orchestrator (verify:post secure-phase, grep-level ASVS L1; no auditor agent) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-12
