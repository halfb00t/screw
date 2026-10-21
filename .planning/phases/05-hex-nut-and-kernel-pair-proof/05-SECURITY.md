---
phase: "5"
slug: "hex-nut-and-kernel-pair-proof"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-20"
---

# Phase 5 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

Register origin: all 19 plans carry a `<threat_model>` block (authored at plan time); 51 unique threat IDs from the plans (05-19 adds T-05-45 to T-05-50 and T-05-SC), none shared between plans, plus T-05-51, which the re-audit at `d7234e8` raised and the owner accepted. The gsd-security-auditor verified the declared mitigations at `9acbfbd`, and re-verified them at `d7234e8` after gap plan 05-19 (read-only: `make lint-imports` 10 kept / 0 broken; targeted `-k "nut_fine_stl or nut_fine_caps or tall_nut"` `53 passed`; scratch probe of M20 at m=600 through calc, API and CLI) (read-only: `make lint-imports` 10 kept / 0 broken; targeted mitigation tests `123 passed`; `git status` unchanged). Every SUMMARY `## Threat Flags` entry is `None` or maps to an existing ID (05-14's `screw.solid.pair` → `screw.calc.presets` import maps to T-05-30; the `screw pair` CLI to T-05-33 and T-05-35). Evidence is a file, line, test or document in this repository at the audited commit.

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
| query string / CLI flags → nut fine-STL export | a tall or loose nut must not reach the pool past its measured budget (05-19) | m, clearance |
| bench run → typed caps | the caps must be what the committed records hold, under a rule fixed before any row (05-19) | jsonl records |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-05-01 | Tampering | tests/data/pair_expected.tsv | high | mitigate | bench/pair_expected.py:24,43-46 sha256 refusal; tests/test_pair.py:82 byte-for-byte re-derive, :44/:98 L11_EXCLUDED literal, :114 tampered record refused | closed |
| T-05-02 | Repudiation | 05-M18-DIAGNOSIS.md, bench/m18_probe.py | high | mitigate | m18_probe.py:114,129,250 byte check against origin/main; protocol 5d90f3e before run 22bcd50; test_pair.py protocol-on-main tests | closed |
| T-05-03 | EoP | PR title/body/commits | medium | mitigate | `.pre-commit-config.yaml` `no-skip-token`; scripts/pr_land.py:252; 0 skip tokens in 92 branch commits and squash 5d90f3e | closed |
| T-05-04 | Info disclosure | 05-OWNER-READS.md, bench/ | high | mitigate | .gitignore:37-38 `*.pdf`, `/.standards/`; no pdf/png/ppm/pgm ever in `git log --all`; 05-06-SUMMARY staged-file check | closed |
| T-05-05 | Tampering | bench/end_cuts.py inputs | medium | mitigate | end_cuts.py:10,65,404,413 UNVERIFIED; no `bench` import under src/ | closed |
| T-05-06 | Repudiation | owner rulings | medium | mitigate | 05-OWNER-READS.md R1–R17, each dated with the applying plan | closed |
| T-05-07 | Tampering | local main history | high | mitigate | `git reflog main`: no reset/rebase in phase 5; merge 3600368; 05-03-SUMMARY refused pull | closed |
| T-05-08 | Repudiation | PR A review | medium | mitigate | PR #17: 5 `fix(bench)` Codex-finding commits after the authored ones; 05-03-SUMMARY | closed |
| T-05-09 | Tampering | clearance input | medium | mitigate | params.py:186 `_req(le=INTERIM_MAX_MM)`, :55 `allow_inf_nan=False`, :75 `extra="forbid"`; app.py repeated-key check; test_nut.py:256-261 | closed |
| T-05-10 | DoS | nut builds through pool | medium | mitigate | admission slot and pool (app.py:310,514), turn cap (params.py:214); nut fine-STL refusal ahead of the pool (app.py:485, calc/__init__.py:452-453) | closed (05-19) |
| T-05-11 | Info disclosure | BuildError text | low | accept | BuildError texts carry fields and the exception type only, no path or trace (solid/__init__.py:248) | closed (AR-05-03) |
| T-05-12 | DoS | huge `m` | high | mitigate | turn cap (params.py:214-221, thread.py:348-360, test_nut.py:384); 30 measured caps `NUT_FINE_STL_ROWS` (thread.py:441-455), `nut_fine_stl_refusal` (thread.py:457-482) wired at calc/__init__.py:452-453; API 422 `fine_stl_cap` before cache/slot/backend (app.py:485; test_api.py:1065 `calls == 0`); CLI exit 2 before export (cli.py:161-164; test_cli.py:343); absence pin replaced (test_calc.py:361); M20 m=600 refused both hands (re-audit probe) | closed (05-19) |
| T-05-13 | Tampering | clearance crossing axis | medium | mitigate | params.py:192-202 → thread.py:331-345; test_nut.py:360 | closed |
| T-05-14 | Tampering | tables/iso4032.py | high | mitigate | test_tables_second_entry.py:235,251; test_tables.py:697,701; page images transcribed first (05-06-SUMMARY) | closed |
| T-05-15 | Info disclosure | page renders | high | mitigate | .gitignore:37; no render in any ref | closed |
| T-05-16 | Tampering | preset id | low | mitigate | tables/presets.py:199-210 closed dict; test_presets.py:240 | closed |
| T-05-17 | Spoofing | near-row nut | medium | mitigate | calc/presets.py:105-114 exact `==`; test_calc.py:296-297 | closed |
| T-05-18 | Tampering | basic values, deviations, tolerances | high | mitigate | test_tables_second_entry.py:47-48,253-254; test_tables.py:737,853,859 (iso724 M7 owner copy made after the agent's transcription was known: owner ruling, 05-OWNER-READS.md:127-134) | closed |
| T-05-19 | Info disclosure | renders, clause text | high | mitigate | .gitignore:37-38; 05-08 staged checks | closed |
| T-05-20 | Spoofing | limits off a row | high | mitigate | calc/presets.py:158-167 exact `==`; test_calc.py:963-973 | closed |
| T-05-21 | Tampering | pair factors | medium | mitigate | test_thread_maths.py:409-439 central-difference slope pins | closed |
| T-05-22 | Tampering | counterpart href | low | mitigate | static/app.js:396-401 `URLSearchParams`, `textContent`; test_parity.py:687 | closed |
| T-05-23 | Spoofing | stale bolt mesh | medium | mitigate | app.js:281,588 `dropMesh()`; test_parity.py:864 | closed |
| T-05-24 | Tampering | oracle formulas | high | mitigate | thread.py:501-792 ValueError guards; test_end_oracles.py independent integrals, :317 probe reproduced | closed |
| T-05-25 | Repudiation | T_PIECE, end constants | medium | mitigate | thread.py:647-673,739-745 cite rulings; test_end_oracles.py:360,376 | closed |
| T-05-26 | Tampering | end cuts diluted | high | mitigate | solid/__init__.py:170-188, :196-231 `piece_refusal`; test_solid.py:558,586; test_nut.py:552,563 | closed |
| T-05-27 | DoS | extra precise volumes | low | mitigate | 05-12-SUMMARY measured +0.4 to +0.6 s; cache and pool unchanged | closed |
| T-05-28 | Tampering | grazing countersink | high | mitigate | solid/nut.py:27-32 `CROSS_FRACTION=0.3`; test_nut.py:587,595 | closed |
| T-05-29 | Tampering | overlapping cutters | medium | mitigate | thread.py:809-813 `min(full, m/2)` + warning naming m; test_end_oracles.py:453 | closed |
| T-05-30 | DoS | solid/pair.py from a route | high | mitigate | import-linter contract "…never import the pair proof" KEPT; test_import_boundaries.py:63,67,71 | closed |
| T-05-31 | Tampering | rule move | high | mitigate | bench/thread_spike/verdict.py:37-60 re-export; test_pair.py:333,338,82 | closed |
| T-05-32 | Repudiation | evidence row as verdict | medium | mitigate | test_pair.py:679 planted shipped reading leaves the verdict unchanged | closed |
| T-05-33 | Repudiation | exit code | high | mitigate | cli.py:205-208 flush then `os._exit`; test_cli_pair.py:35,58,68,75,81,99 | closed |
| T-05-34 | EoP | pair.yml | high | mitigate | pair.yml:15-23 dispatch+schedule only, `contents: read`, no secrets; test_pair.py:909-914 | closed |
| T-05-35 | DoS | verify-tier wall time | medium | mitigate | one cell in a child process; 42.55 s local / 167.50 s ubuntu; CI cost in debt `2026-10-20-ci-test-job-tripled-by-two-pair-tests.md` | closed |
| T-05-36 | Repudiation | M18 and product-cell results | high | mitigate | protocol 5d90f3e before 22bcd50/80aac99; sha256 of all phase-05 jsonl in bench/RESULTS.md (incl. both 05-19 runs) | closed |
| T-05-37 | Tampering | quiet reclassification | high | mitigate | `git diff b19348a a58b702 -- src tests` empty; 240/240 match | closed |
| T-05-38 | Tampering | ControlSurfaceDeflection default | medium | mitigate | test_mesh.py:19, :46-57 with preview positive control | closed |
| T-05-39 | DoS | finer mesh, larger downloads | high | mitigate | preset kept (solid/__init__.py:74); test_mesh.py:33-37 pins (0.01, 0.1) | closed |
| T-05-40 | Tampering | Content-Disposition name | low | mitigate | app.py:591-592 quoted `download_name`; calc/__init__.py:458-469; test_api.py:568 | closed |
| T-05-41 | Tampering | `-o <directory>` | low | accept | cli.py:174-178 writes one `download_name` file | closed (AR-05-01) |
| T-05-42 | Repudiation | L15 claims | medium | mitigate | decision_log.md L15 cites a run, owner-read line, probe or summary per value; L15 superseded by L16 (decision_log.md:938,1119) | closed |
| T-05-43 | Tampering | GOST ISO 4032-2014 reproduction | medium | accept | L14; 05-OWNER-READS.md UNVERIFIED + sha256 | closed (AR-05-02) |
| T-05-44 | Tampering | derived limits | high | mitigate | tables/gost16093.py:16-21,87-103 `Decimal`; test_tables.py:784,810,878 | closed |
| T-05-45 | DoS | nut fine STL at its cap boundary | high | mitigate | every key pinned at cap, `nextafter(cap)`, cap+1 (test_thread_maths.py:530); refusal before cache, slot, pool (test_api.py:1065) | closed |
| T-05-46 | DoS | clearance above the measured ceiling | high | mitigate | R16 option-a (05-OWNER-READS.md:382); `clearance > NUT_FINE_STL_CLEARANCE` judged first (thread.py:470); test_thread_maths.py:548, test_calc.py:361 | closed |
| T-05-47 | Tampering | cap run rule chosen after the data | high | mitigate | instrument commits 0c349a7/9b4fbb7 precede records 837b0bc/f1488ea, instrument byte-identical across each pair; R17 amendment changes refused-check handling, run id and path only; sha256 8682c702…, 64ae355a… in RESULTS.md; caps re-derived from both jsonl without importing bench (test_thread_maths.py:486) | closed |
| T-05-48 | Tampering | caps applied beyond what was measured | high | mitigate | no cap and no nearest row off the 30 keys (test_thread_maths.py:569); header `s_mm == 1e5` (:497); 2.5 and slimmest-s checks built on all 30 keys (:486); catalogue nuts served (test_calc.py:387); 46 low-clearance checks refused by the lead-in gate recorded per R17, debt `2026-10-21-nut-lead-in-gate-refuses-a-valid-nut-at-huge-s.md` | closed |
| T-05-49 | DoS | bench run on the shared host | low | mitigate | dirty tree / existing records refuse to start (bench/nut_fine_caps.py:305-310); serial; `timeout 7000` and load in RESULTS.md amended entry | closed |
| T-05-50 | Repudiation | tessellation preset of the run | medium | mitigate | `header["preset"] == list(TESSELLATION["fine"])` both runs (test_thread_maths.py:501) | closed |
| T-05-SC | Tampering | supply chain | high | mitigate | `git diff 2a4c07a HEAD` touches no pyproject, lock, requirements, Dockerfile or `.github` file | closed |
| T-05-51 | DoS | nut off the 30 measured keys (fine pitch, off-row d) | medium | accept | no fine-STL cap by design (D-03, L02: no nearest row); test_thread_maths.py:571-574 pins M8x1 at m=248 served; over-budget size UNMEASURED (auditor ASSUMPTION); backstops: turn cap (params.py:214-221), admission slot and pool (app.py:310,514), INTERIM timeout (D-18) | closed (AR-05-04) |

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
| AR-05-04 | T-05-51 | a nut off the 30 measured keys is built as decided (D-03, the rod's T-3-08 / R-3-01 posture); turn cap, admission slot, pool and the INTERIM timeout are the backstop until the Phase 7 re-sweep | owner, secure-phase re-audit decision | 2026-10-21 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-20 | 44 | 42 | 2 (1 blocking: T-05-12) | gsd-security-auditor at 9acbfbd |
| 2026-10-21 | 52 | 52 | 0 | gsd-security-auditor at d7234e8 (after 05-19); T-05-51 accepted by owner |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed (re-audit at d7234e8)
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-21

## Security Audit 2026-10-21

| Metric | Count |
|---|---|
| Threats found | 52 |
| Closed | 52 |
| Open | 0 |
