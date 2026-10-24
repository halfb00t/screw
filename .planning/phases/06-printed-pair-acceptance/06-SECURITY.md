---
phase: "6"
slug: "printed-pair-acceptance"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-24"
---

# Phase 6 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

The phase adds no network, auth or file-access surface (every SUMMARY's Threat Flags: none). Its
threats are integrity threats on a measurement: a hand-filled record, a rule written before the
data, and a default frozen by L02. The register is the union of the ten PLAN `<threat_model>`
blocks, authored at plan time.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| owner's hand-filled record -> rule module | a person types the record; an ambiguous cell must not become a result | TSV records, integrity-critical |
| rule text -> printed data | a rule written or tuned after the data would set a one-way default by wish | `bench/print_rules.py`, protocol |
| owner reply -> rulings record | a ruling must be the owner's words | `06-OWNER-RULINGS.md` |
| PR text -> main's commit message | the squash commit takes the PR title and body | PR A (#19) |
| phase work -> main | only `make pr.land` merges, on green required jobs | git history |
| STL files -> printed parts | the printed parts must be the pinned exports | STL bytes, manifests with sha256 |
| pinned record -> parameter model | the one place a number becomes a frozen default | `NutParams.clearance`, `D_MIN_MM`, `P_MIN_MM` |
| user fields -> warning text -> page | warnings reach the page as text built from validated floats and constants | warning strings |
| page download -> printed acceptance pair | the owner's files must be the shipped default's | STL bytes, sha256 |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-06-01 | Tampering | `bench/print_rules.py` rules | high | mitigate | landed on main in PR A (16f7041, #19) before any record; rule tests `tests/test_print_rules.py:60-237`; digests the only later edits (`bench/print_rules.py:56`) | closed |
| T-06-02 | Tampering | record reader | high | mitigate | strict reader refusing naming the line: `test_an_incomplete_or_ambiguous_record_is_refused_naming_the_line` (`tests/test_print_rules.py:160`), `:171`, `:181`, `:214`, `:368` | closed |
| T-06-03 | Tampering | record and manifest paths | medium | mitigate | `ROOT`-anchored paths (`bench/print_rules.py:52`); no `eval`/`pickle` in `bench/*.py` (grep empty); export refuses non-empty dir and never overwrites (`tests/test_print_rules.py:375`, `:391`, `:403`) | closed |
| T-06-04 | Repudiation | `06-OWNER-RULINGS.md` | medium | mitigate | each ruling recorded with option, the owner's literal reply `r1-a r2-a r3-a r4-a r5-b r6-a r7-a r8-b` and the date (`06-OWNER-RULINGS.md:6-16`) | closed |
| T-06-05 | Repudiation | `06-PRINT-PROTOCOL.md` | high | mitigate | landed in PR A before any print; protocol-text tests `tests/test_print_rules.py:436`, `:443`, `:467` (no owner slot left) | closed |
| T-06-06 | Elevation of privilege | PR title, body, commits | medium | mitigate | commit-msg hook `.pre-commit-config.yaml:36` rejects skip tokens; `tests/test_skip_tokens.py` (L08) | closed |
| T-06-07 | Tampering | local main history | high | mitigate | 06-04 SUMMARY:127 reflog record: plan's entries are checkout, `pull --ff-only`, merge only; phase branch merges origin/main (1332178) | closed |
| T-06-08 | Repudiation | PR A review | medium | mitigate | Codex reviewed PR A; three findings applied as commits on `gsd/phase-06-preregistration` (06-04 SUMMARY:11, :94) | closed |
| T-06-09 | Tampering | `print-run-1.tsv` | high | mitigate | digest pinned; `test_the_run_1_record_is_the_one_pinned` (`tests/test_print_rules.py:288`), `load()` refuses any other sha256 (`bench/print_rules.py:86-97`) | closed |
| T-06-10 | Tampering | the run | high | mitigate | outcome read only by the landed rules and pinned: `test_run_1_reads_a_default_of_0_15_mm_by_d_07` (`:312`); R5 the only reprint rule, ruled before data | closed |
| T-06-11 | Tampering | STL files | medium | mitigate | manifests with bytes and sha256 committed before the print (`bench/results/phase-06/manifest-*.tsv`); `tests/test_print_rules.py:243`, `:403` | closed |
| T-06-12 | Tampering | `NutParams.clearance` default | high | mitigate | literal test `tests/test_params.py:68` (0.15); re-derivation `tests/test_print_rules.py:319` | closed |
| T-06-13 | Tampering | shared links (L02) | high | mitigate | frozen-default comment `src/screw/params.py:189`; omitted-equals-typed test `tests/test_print_rules.py:326` | closed |
| T-06-14 | Tampering | warning text on the page | low | accept | page writes warnings with `textContent` (`src/screw/static/app.js:406-413`), 0 `innerHTML` uses; strings from `allow_inf_nan=False` floats (`src/screw/params.py:42`) | closed |
| T-06-15 | Tampering | a nut outside the measured range | medium | mitigate | rows and other warnings identical with the sentence switched off (`tests/test_calc.py:1346-1366`). The "API answers 200" half has no test; probed 2026-10-24: `GET /api/nut/info?d=5&pitch=0.8&s=8&m=4.7` -> 200 with the sentence. See note below | closed |
| T-06-16 | Tampering | run-2 STLs | medium | mitigate | `exports("run-2")` carries no clearance: `test_the_matrix_prints_exactly_the_pre_registered_parts` (`tests/test_print_rules.py:243`); digests in `manifest-run-2` checked in 06-08 Task 1 | closed |
| T-06-17 | Tampering | `print-run-2.tsv` | high | mitigate | digest pinned `tests/test_print_rules.py:333`; size read only by `threshold_from` (`:343`) | closed |
| T-06-18 | Tampering | `D_MIN_MM`, `P_MIN_MM` | high | mitigate | `src/screw/calc/printability.py:56-57`; re-derived from the pinned record by `test_the_printability_threshold_is_the_one_run_2_reads` (`tests/test_print_rules.py:352`) | closed |
| T-06-19 | Denial of service | parts below the threshold | medium | mitigate | `test_a_part_below_the_printability_threshold_still_builds` (`tests/test_calc.py:1464`): 200 on info and on preview `model.stl` | closed |
| T-06-20 | Repudiation | acceptance pair provenance | medium | mitigate | page-download sha256 and bytes compared with `manifest-acceptance.tsv`, recorded in `bench/RESULTS.md` "Acceptance pair (Phase 6, D-16)" (06-10 commit 4632b61) | closed |
| T-06-21 | Tampering | the kernel precondition | high | mitigate | verdict `proven`, exit 0, JSON recorded verbatim in `bench/RESULTS.md` before the print; no rule, constant, clearance or table changed (06-10 SUMMARY:11, :36-40) | closed |
| T-06-SC | Tampering | packages | low | accept | no package added in any plan (RESEARCH Package Legitimacy Audit: none); `make venv` installs the pinned closure (L06, L10) | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

**T-06-15 note.** The mitigation plan names two controls: the row-identity test and "the API
answers 200". The first is in `make verify`. The second is true today (probe above) but no test
holds it, so a later change could turn an out-of-range nut into a 422 without failing the gate.
Medium, below `block_on: high`; closed on the probe, not on a test. Tracked as debt:
`docs/tech_debt/active/2026-10-24-measured-range-nut-api-200-untested.md`.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-06-01 | T-06-14 | the page writes every warning with `textContent`; the string is built from finite validated floats and module constants, so no markup reaches the DOM | owner, via the plan-time register (06-07-PLAN) | 2026-10-24 |
| AR-06-02 | T-06-SC | no package is added in this phase; the install is the pinned closure (L06, L10) | owner, via the plan-time registers (06-01..06-10) | 2026-10-24 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-24 | 22 | 22 | 0 | secure-phase orchestrator at cc955e6, ASVS L1 grep evidence; T-06-15 API half closed on a probe, test gap filed as debt |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-24
