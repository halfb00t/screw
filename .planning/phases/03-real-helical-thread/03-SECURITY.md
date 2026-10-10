---
phase: "3"
slug: "real-helical-thread"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-10"
---

# Phase 3 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| HTTP query / CLI argv → `params` | user-supplied `d`, `pitch`, `length`, `left_hand`, `quality`, repeated keys | untrusted strings validated once at the model boundary (L02) |
| `params` → `solid` / pool worker | validated `BoltParams` to the kernel builder; the THRD-04 gate inside `_build` | trusted floats; a refused build never reaches `lru_cache` or `_EXPORTS` |
| `solid` → export bytes / page | STL/STEP bytes, info rows, warnings | a 200 only carries an export the gate accepted |
| shareable link hash → page | `#kind=…&d=…&left_hand=…` from any origin | refused before any fetch when foreign, repeated or unreadable; rendered via `textContent` only |
| CI → repository | `.github/workflows/grid.yml` token | `contents: read`, `workflow_dispatch` + `schedule` only, no secrets, never a required job |

---

## Threat Register

Register authored at plan time (every PLAN carries a `<threat_model>`); every SUMMARY's `## Threat Flags` reads "None" and names its planned threats as mitigated. Verified 2026-10-10 at ASVS L1 (grep-level presence of each mitigation in the shipped code on `gsd/phase-03-real-helical-thread` at `f2ae623`).

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-3-01 | Denial of service | `helical.thread` on a float length | high | mitigate | `MIN_TAIL_MM` doorway guard and tail fold in `src/screw/solid/helical.py` (lines 41, 97, 102); 03-01 `510b7b1` | closed |
| T-3-02 | Tampering | `_build` / `lru_cache` / `_EXPORTS` | high | mitigate | `check_solid` runs inside the `lru_cache`-wrapped builder in `src/screw/solid/__init__.py`, a raise is never stored; positive-control and never-cached tests in `tests/test_solid.py`, `tests/test_api.py`; 03-01 `510b7b1`, `f569238` | closed |
| T-3-03 | Tampering | `_write_export` | high | mitigate | `exportStl` False, non-`RetDone` STEP status and a bad STL header raise `BuildError` in `src/screw/solid/__init__.py`; 03-01 `de9304e` | closed |
| T-3-04 | Denial of service | `BoltParams` → pool | high | mitigate | `turn_cap` validator in `src/screw/params.py` on `MAX_TURNS` from `src/screw/calc/thread.py`, exact decimals, before the pool; 03-02 `e6ccfc3` | closed |
| T-3-05 | Denial of service | `FastenerParams` → `helical.section` | high | mitigate | `pitch_too_coarse` validator in `src/screw/params.py`; 03-02 `e6ccfc3` | closed |
| T-3-06 | Information disclosure | `derive` rows | medium | mitigate | non-finite computed rows withheld with a warning in `src/screw/calc/__init__.py`; 03-02 `fd6792f` | closed |
| T-3-07 | Denial of service | `app._serve` fine STL on L11 rows | medium | mitigate | `download_refusal` over `FINE_STL_ROWS` before the cache, the slot and the pool in `src/screw/app.py` and in `src/screw/cli.py`; counting-backend test; 03-03 `35a590a`, `2fc210c` | closed |
| T-3-08 | Denial of service | in-cap off-row parts | medium | accept | D-18: the INTERIM 30 s timeout, the bounded queue and the container limit are the backstop; figures in `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` (03-07 `1144bca`) | closed — accepted |
| T-3-09 | Tampering | `app` query parsing, `cli` argparse | medium | mitigate | `refuse_repeated_keys` before validation in `src/screw/app.py`; `_Once` / `_OnceBool` actions in `src/screw/cli.py`; 03-04 `eaaac85`, `d849557` | closed |
| T-3-10 | Tampering | `left_hand` parsing | medium | mitigate | pydantic bool field in `src/screw/params.py` (422 on `banana`); `BooleanOptionalAction` in `src/screw/cli.py` takes no value; 03-04 `d849557` | closed |
| T-3-11 | Repudiation | `records._part_fields` logging `left_hand` | low | accept | `model_dump(exclude_defaults=True)` in `src/screw/records.py:154` writes a validated bool into structured JSON | closed — accepted |
| T-3-12 | Tampering | refusal messages echoing hash keys and values | high | mitigate | every message goes through `showMessages` with `textContent`; `src/screw/static/app.js` contains no `innerHTML`, `outerHTML` or `insertAdjacentHTML`; `test_the_ui_builds_nodes_from_text_only` in `tests/test_parity.py`; 03-05 `05fb4ed` | closed |
| T-3-13 | Tampering | `navigate()` reading the hash | medium | mitigate | foreign, repeated and unreadable keys refused before any fetch in `src/screw/static/app.js`; 03-05 `05fb4ed` | closed |
| T-3-14 | Elevation of privilege | `.github/workflows/grid.yml` | medium | mitigate | `permissions: contents: read`; triggers `workflow_dispatch` and `schedule` only; no `pull_request`/`push`; no `secrets.`; pinned by `test_the_grid_workflow_has_no_pull_request_or_push_trigger_and_reads_only`; 03-06 `2b08ff0` | closed |
| T-3-15 | Spoofing | `scripts/pr_land.py` reading CI state | low | mitigate | `WORKFLOW = "ci.yml"` in `scripts/pr_land.py`; `grid` absent from `.github/workflows/required-jobs.txt`; 03-06 `2b08ff0` | closed |
| T-3-16 | Repudiation | `docs/architecture/decision_log.md` L12, the debt register | low | mitigate | L12 (decision_log.md:412) cites the L11 run ids (21 references to `2026-10-08-a`); the four retired items name real fix shas (`de9304e`, `eaaac85`+`d849557`, `05fb4ed`, `909dec3`); 03-07 `8fd6a4e`, `1144bca` | closed |
| T-3-SC | Tampering | npm/pip/cargo installs; GitHub actions | low | accept | no dependency added in the phase (`pyproject.toml` diff since `8d38167` touches only pytest/coverage/import-linter config); `grid.yml` uses only the two actions `ci.yml` already pins by major; the vendored three.js bundle is untouched (`make vendor-check`) | closed — accepted |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-3-01 | T-3-08 | Off-row in-cap parts are built as decided (D-18); the INTERIM runtime bounds are the backstop until the Phase 7 re-sweep | owner (03-CONTEXT D-18) | 2026-10-10 |
| R-3-02 | T-3-11 | The log carries a validated bool from `model_dump`, never request text | plan 03-04 threat model | 2026-10-10 |
| R-3-03 | T-3-SC | No package installed or added in Phase 3; actions pinned by major as in `ci.yml` | plan threat models 03-01..03-07 | 2026-10-10 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-10 | 17 | 17 | 0 | /gsd-secure-phase 03 (orchestrator, ASVS L1 grep verification; short-circuit, no auditor spawned) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-10
