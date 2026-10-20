---
phase: "5"
slug: "hex-nut-and-kernel-pair-proof"
status: draft
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 1
asvs_level: 1
created: "2026-10-20"
---

# Phase 5 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

Register origin: all 18 plans carry a `<threat_model>` block (authored at plan time); 44 unique threat IDs, none shared between plans. The gsd-security-auditor verified the declared mitigations at `9acbfbd` (read-only: `make lint-imports` 10 kept / 0 broken; targeted mitigation tests `123 passed`; `git status` unchanged). Every SUMMARY `## Threat Flags` entry is `None` or maps to an existing ID (05-14's `screw.solid.pair` → `screw.calc.presets` import maps to T-05-30; the `screw pair` CLI to T-05-33 and T-05-35). Evidence is a file, line, test or document in this repository at the audited commit.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| recorded campaign → expected table | a typed or tuned verdict makes the CI tier check the author's wishes (05-01) | pair verdicts |
| protocol → probe run | a method written after the data proves nothing (05-01) | M18 protocol |
| PR text → main's commit message | the squash commit takes the PR title and body (05-01) | commit text |
| purchased standard → repository | licensed text must not leak; values enter only by double entry (05-02) | standard text, renders |
| owner reply → frozen defaults | a one-way value needs the owner's permanence line (05-02) | default dimensions |
| phase branch → main | only `make pr.land` merges, on green required jobs (05-03) | git history |
| query string / CLI flags → NutParams | untrusted numbers are validated once (05-04, 05-05) | user numbers |
| NutParams → kernel | a validated nut reaches the pool and the solid package (05-04) | build requests |
| free GOST text (L14) → tables/ | double entry: owner copy from the text layer, agent copy from page images (05-06, 05-08) | table values |
| preset id (URL/CLI) → fields | the id is looked up in a closed set (05-07) | preset id |
| calc → page and API | every printed number may be cut to metal (05-09) | printed dimensions |
| info document → page link | server data becomes a URL fragment (05-10) | counterpart href |
| oracle → gate | a wrong oracle passes a wrong part or refuses a right one (05-11) | volumes |
| solid → download | an open or wrong mesh would reach a printer (05-12, 05-13) | STL/STEP |
| server process → kernel pair proof | a segfault-prone, minutes-long boolean must never run in a request (05-14) | none (import contract) |
| recorded rule → product rule | a moved rule that differs voids the CI tier (05-14) | verdict rule |
| CLI process → kernel boolean | a process that ran the boolean segfaults at teardown (05-15) | exit code |
| workflow → repository token | read-only token, no fork code (05-15) | GitHub token |
| run → record | results must not be chosen after seeing them (05-16) | jsonl records |
| solid → printed part | a mesh coarser than the clearance makes a pair that binds (05-17) | mesh deviation |
| user-supplied export path → filesystem | the CLI writes where the user points (05-18) | file path |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-05-01 | Tampering | tests/data/pair_expected.tsv | high | mitigate | bench/pair_expected.py:24,43-46 sha256 refusal; tests/test_pair.py:82 byte-for-byte re-derive, :44/:98 L11_EXCLUDED literal, :114 tampered record refused | closed |
| T-05-02 | Repudiation | 05-M18-DIAGNOSIS.md, bench/m18_probe.py | high | mitigate | m18_probe.py:114,129,250 byte check against origin/main; protocol 5d90f3e before run 22bcd50; test_pair.py protocol-on-main tests | closed |
| T-05-03 | EoP | PR title/body/commits | medium | mitigate | `.pre-commit-config.yaml` `no-skip-token`; scripts/pr_land.py:252; 0 skip tokens in 92 branch commits and squash 5d90f3e | closed |
| T-05-04 | Info disclosure | 05-OWNER-READS.md, bench/ | high | mitigate | .gitignore:37-38 `*.pdf`, `/.standards/`; no pdf/png/ppm/pgm ever in `git log --all`; 05-06-SUMMARY staged-file check | closed |
| T-05-05 | Tampering | bench/end_cuts.py inputs | medium | mitigate | end_cuts.py:10,65,404,413 UNVERIFIED; no `bench` import under src/ | closed |
| T-05-06 | Repudiation | owner rulings | medium | mitigate | 05-OWNER-READS.md R1–R15, each dated with the applying plan | closed |
| T-05-07 | Tampering | local main history | high | mitigate | `git reflog main`: no reset/rebase in phase 5; merge 3600368; 05-03-SUMMARY refused pull | closed |
| T-05-08 | Repudiation | PR A review | medium | mitigate | PR #17: 5 `fix(bench)` Codex-finding commits after the authored ones; 05-03-SUMMARY | closed |
| T-05-09 | Tampering | clearance input | medium | mitigate | params.py:186 `_req(le=INTERIM_MAX_MM)`, :55 `allow_inf_nan=False`, :75 `extra="forbid"`; app.py repeated-key check; test_nut.py:256-261 | closed |
| T-05-10 | DoS | nut builds through pool | medium | mitigate | admission slot and pool (app.py:310,520), turn cap (params.py:214); nut fine-STL cap absent (calc/__init__.py:449-457 returns None for every nut) | open — below high threshold (non-blocking); closed by the same gap plan as T-05-12 |
| T-05-11 | Info disclosure | BuildError text | low | accept | BuildError texts carry fields and the exception type only, no path or trace (solid/__init__.py:248) | closed (AR-05-03) |
| T-05-12 | DoS | huge `m` | high | mitigate | turn cap present (params.py:214-221, thread.py:348-360, test_nut.py:384); R12 nut fine-STL cap absent (calc/__init__.py:449-457; test_calc.py:360 pins the absence); M20 left at m=600 is served as fine STL while the probe measured m=91 over 64 MiB | **open** — owner chose option b (measure and cap) on 2026-10-20; gap-closure plan |
| T-05-13 | Tampering | clearance crossing axis | medium | mitigate | params.py:192-202 → thread.py:331-345; test_nut.py:360 | closed |
| T-05-14 | Tampering | tables/iso4032.py | high | mitigate | test_tables_second_entry.py:235,251; test_tables.py:697,701; page images transcribed first (05-06-SUMMARY) | closed |
| T-05-15 | Info disclosure | page renders | high | mitigate | .gitignore:37; no render in any ref | closed |
| T-05-16 | Tampering | preset id | low | mitigate | tables/presets.py:199-210 closed dict; test_presets.py:240 | closed |
| T-05-17 | Spoofing | near-row nut | medium | mitigate | calc/presets.py:105-114 exact `==`; test_calc.py:295-296 | closed |
| T-05-18 | Tampering | basic values, deviations, tolerances | high | mitigate | test_tables_second_entry.py:47-48,253-254; test_tables.py:737,853,859 (iso724 M7 owner copy made after the agent's transcription was known: owner ruling, 05-OWNER-READS.md:127-134) | closed |
| T-05-19 | Info disclosure | renders, clause text | high | mitigate | .gitignore:37-38; 05-08 staged checks | closed |
| T-05-20 | Spoofing | limits off a row | high | mitigate | calc/presets.py:158-167 exact `==`; test_calc.py:940-950 | closed |
| T-05-21 | Tampering | pair factors | medium | mitigate | test_thread_maths.py:403-433 central-difference slope pins | closed |
| T-05-22 | Tampering | counterpart href | low | mitigate | static/app.js:396-401 `URLSearchParams`, `textContent`; test_parity.py:687 | closed |
| T-05-23 | Spoofing | stale bolt mesh | medium | mitigate | app.js:281,588 `dropMesh()`; test_parity.py:864 | closed |
| T-05-24 | Tampering | oracle formulas | high | mitigate | thread.py:437-728 ValueError guards; test_end_oracles.py independent integrals, :317 probe reproduced | closed |
| T-05-25 | Repudiation | T_PIECE, end constants | medium | mitigate | thread.py:583-609,675-681 cite rulings; test_end_oracles.py:360,376 | closed |
| T-05-26 | Tampering | end cuts diluted | high | mitigate | solid/__init__.py:170-188, :196-231 `piece_refusal`; test_solid.py:558,586; test_nut.py:552,563 | closed |
| T-05-27 | DoS | extra precise volumes | low | mitigate | 05-12-SUMMARY measured +0.4 to +0.6 s; cache and pool unchanged | closed |
| T-05-28 | Tampering | grazing countersink | high | mitigate | solid/nut.py:27-32 `CROSS_FRACTION=0.3`; test_nut.py:587,595 | closed |
| T-05-29 | Tampering | overlapping cutters | medium | mitigate | thread.py:745-749 `min(full, m/2)` + warning naming m; test_end_oracles.py:453 | closed |
| T-05-30 | DoS | solid/pair.py from a route | high | mitigate | import-linter contract "…never import the pair proof" KEPT; test_import_boundaries.py:63,67,71 | closed |
| T-05-31 | Tampering | rule move | high | mitigate | bench/thread_spike/verdict.py:37-60 re-export; test_pair.py:333,338,82 | closed |
| T-05-32 | Repudiation | evidence row as verdict | medium | mitigate | test_pair.py:679 planted shipped reading leaves the verdict unchanged | closed |
| T-05-33 | Repudiation | exit code | high | mitigate | cli.py:205-208 flush then `os._exit`; test_cli_pair.py:35,58,68,75,81,99 | closed |
| T-05-34 | EoP | pair.yml | high | mitigate | pair.yml:15-23 dispatch+schedule only, `contents: read`, no secrets; test_pair.py:909-914 | closed |
| T-05-35 | DoS | verify-tier wall time | medium | mitigate | one cell in a child process; 42.55 s local / 167.50 s ubuntu; CI cost in debt `2026-10-20-ci-test-job-tripled-by-two-pair-tests.md` | closed |
| T-05-36 | Repudiation | M18 and product-cell results | high | mitigate | protocol 5d90f3e before 22bcd50/80aac99; sha256 of all phase-05 jsonl in bench/RESULTS.md | closed |
| T-05-37 | Tampering | quiet reclassification | high | mitigate | `git diff b19348a a58b702 -- src tests` empty; 240/240 match | closed |
| T-05-38 | Tampering | ControlSurfaceDeflection default | medium | mitigate | test_mesh.py:19, :46-57 with preview positive control | closed |
| T-05-39 | DoS | finer mesh, larger downloads | high | mitigate | preset kept (solid/__init__.py:74); test_mesh.py:33-37 pins (0.01, 0.1) | closed |
| T-05-40 | Tampering | Content-Disposition name | low | mitigate | app.py:591-592 quoted `download_name`; calc/__init__.py:461-472; test_api.py:568 | closed |
| T-05-41 | Tampering | `-o <directory>` | low | accept | cli.py:174-178 writes one `download_name` file | closed (AR-05-01) |
| T-05-42 | Repudiation | L15 claims | medium | mitigate | decision_log.md L15 cites a run, owner-read line, probe or summary per value | closed |
| T-05-43 | Tampering | GOST ISO 4032-2014 reproduction | medium | accept | L14; 05-OWNER-READS.md UNVERIFIED + sha256 | closed (AR-05-02) |
| T-05-44 | Tampering | derived limits | high | mitigate | tables/gost16093.py:16-21,87-103 `Decimal`; test_tables.py:784,810,878 | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-05-01 | T-05-41 | the CLI runs as the user who typed the path and writes one `download_name` file there; no request supplies a path | owner, R9 (05-OWNER-READS.md); R-01-01 in 01-SECURITY.md | 2026-10-20 |
| AR-05-02 | T-05-43 | both copies read the same GOST reproduction, so the diff cannot catch an error in it; faithfulness UNVERIFIED; buying the ISO texts is deferred | owner, L14; docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md | 2026-10-20 |
| AR-05-03 | T-05-11 | BuildError text names fields and the exception type only, never a path or kernel trace | owner, via plan 05-04's approved register | 2026-10-20 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-20 | 44 | 42 | 2 (1 blocking: T-05-12) | gsd-security-auditor at 9acbfbd |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [ ] `threats_open: 0` confirmed — blocked on T-05-12 (gap-closure plan: measure the nut fine-STL caps)
- [ ] `status: verified` set in frontmatter

**Approval:** pending
