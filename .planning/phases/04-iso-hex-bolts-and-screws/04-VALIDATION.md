---
phase: "4"
slug: "iso-hex-bolts-and-screws"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-11"
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 + pytest-xdist 3.8.0 + pytest-cov 7.1.0; `filterwarnings = ["error"]`, `xfail_strict`, `--strict-markers`, `--strict-config`, `-m 'not grid'` (RESEARCH § Validation Architecture) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]`; coverage floor `[tool.coverage.report] fail_under = 96` |
| **Quick run command** | `make test PYTEST_ARGS="<the task's test files> -q -n0 --no-cov"` (each task's `<verify>` names its files) |
| **Full suite command** | `make verify` (ruff, mypy --strict, lint-imports, unfinished-work scan, pytest under the coverage floor); the pre-commit hook runs it on every commit |
| **Estimated runtime** | ~40–90 s for `make verify` on the Phase 3 baseline; the ~294 catalogue rows add one pure-data test each (no kernel build per row, TABL-03) |

---

## Sampling Rate

- **After every task commit:** the task's quick command, then `make lint-imports` when `pyproject.toml` or a module edge moved (contracts 6 and 7 land this phase); the commit itself runs `make verify` (pre-commit hook), so no commit lands red
- **After every plan wave:** `make verify`
- **Before `/gsd-verify-work`:** `make verify` green
- **Max feedback latency:** ~60 s for a task's quick command; ~90 s for `make verify`

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-T1 | 04-01 | 1 | TABL-04 | — | — | integration (bench) | `make test PYTEST_ARGS="tests/test_bench.py -q -n0 --no-cov -k head_fuse"`; `bench/RESULTS.md` head-fuse grep | ✅ | ✅ green |
| 04-01-T2 | 04-01 | 1 | TABL-04 | T-04-02 | owner reads the purchased copy; auto-mode never approves | manual (blocking-human checkpoint) | none — Manual-Only | n/a | ✅ done (04-OWNER-READS.md, 2026-10-11) |
| 04-01-T3 | 04-01 | 1 | TABL-04 | T-04-01 | licensed PDFs and renders never tracked | smoke (grep, git) | `.gitignore` / `04-OWNER-READS.md` grep chain; `git status --porcelain` has no pdf/png/tsv | ✅ | ✅ green |
| 04-02-T1 | 04-02 | 1 | INFO-03 | T-04-03 | a left-hand cap is the longest measured length | unit | `make test PYTEST_ARGS="tests/test_thread_maths.py tests/test_calc.py tests/test_api.py tests/test_cli.py -q -n0 --no-cov"`; WR-02 moved to resolved/ | ✅ | ✅ green |
| 04-03-T1 | 04-03 | 2 | TYPE-01, TYPE-02, INFO-03 | T-04-04 | `s`, `k` bounded at the model | tracer (unit, integration, smoke) | `make test PYTEST_ARGS="tests/test_params.py tests/test_calc.py tests/test_solid.py tests/test_api.py tests/test_cli.py tests/test_parity.py tests/test_pool.py -q -n0 --no-cov"`; `screw export bolt --quality preview` writes a non-empty STL | ✅ | ✅ green — the plan's row-key probe lists the wave-2 keys; the document has since gained `thread_length`, `shank_length` (04-04) and the matched row's cited values (04-11), so that one probe is stale, not red |
| 04-03-T2 | 04-03 | 2 | TYPE-01, INFO-03 | T-04-05 | a fused part is refused by both gates | unit, smoke | `make test PYTEST_ARGS="tests/test_thread_maths.py tests/test_solid.py tests/test_params.py tests/test_api.py tests/test_cli.py -q -n0 --no-cov"`; `screw info bolt --s 6` exits 2 naming `s and d` | ✅ | ✅ green |
| 04-04-T1 | 04-04 | 3 | THRD-03, TYPE-01, INFO-03 | T-04-06, T-04-08 | a sliver is folded before the kernel | unit, integration | `make test PYTEST_ARGS="tests/test_thread_maths.py tests/test_params.py tests/test_calc.py tests/test_solid.py tests/test_api.py tests/test_cli.py tests/test_parity.py tests/test_bench.py -q -n0 --no-cov"`; `screw info bolt --length 10` warning probe | ✅ | ✅ green |
| 04-05-T1 | 04-05 | 4 | THRD-03, INFO-03 | T-04-07 | one conflict rule on API and CLI | integration, smoke | `make test PYTEST_ARGS="tests/test_thread_maths.py tests/test_api.py tests/test_cli.py tests/test_parity.py -q -n0 --no-cov"`; `--length 10 --thread-length 30` exits 2 with the pinned text | ✅ | ✅ green |
| 04-05-T2 | 04-05 | 4 | THRD-03, INFO-03 | T-04-26 | no numbers for a refused part | unit, integration | `make test PYTEST_ARGS="tests/test_calc.py tests/test_api.py -q -n0 --no-cov"`; IN-01 moved to resolved/ | ✅ | ✅ green |
| 04-06-T1 | 04-06 | 4 | THRD-03 | T-04-24 | the corpus pins every key | unit | `make test PYTEST_ARGS="tests/test_bench.py -q -n0 --no-cov -k 'corpus or sweep or set'"`; corpus label probe | ✅ | ✅ green |
| 04-07-T1 | 04-07 | 4 | TABL-02, TABL-03, TABL-04, TABL-07 | T-04-09, T-04-10, T-04-11, T-04-12 | UNVERIFIED gate; contracts 6 and 7; `sys.modules` control | unit (pure data), lint | `make test PYTEST_ARGS="tests/test_tables.py tests/test_tables_second_entry.py tests/test_import_boundaries.py -q -n0 --no-cov"`; `make lint-imports` (≥9 KEPT, none BROKEN) | ✅ | ✅ green |
| 04-08-T1 | 04-08 | 5 | TABL-06, TABL-07, TYPE-01 | T-04-25 | `calc.presets` imported only inside `_bolt` | unit, integration | `make test PYTEST_ARGS="tests/test_calc.py tests/test_api.py tests/test_params.py tests/test_parity.py tests/test_import_boundaries.py -q -n0 --no-cov"`; `screw info bolt` preset-exact probe; `make lint-imports` | ✅ | ✅ green |
| 04-09-T1 | 04-09 | 6 | TABL-04 | T-04-02 | the owner copy comes from the purchased copies | manual (blocking-human checkpoint) | none — Manual-Only | n/a | ✅ done (ruling B, 04-OWNER-READS.md, 2026-10-12) |
| 04-09-T2 | 04-09 | 6 | TABL-02, TABL-03, TABL-04, TABL-05, TYPE-02 | T-04-13 | cell diff plus per-row relations | unit (pure data) | `make test PYTEST_ARGS="tests/test_tables.py tests/test_tables_second_entry.py -q -n0 --no-cov"` | ✅ | ✅ green |
| 04-09-T3 | 04-09 | 6 | TABL-02, TABL-03, TABL-04, TABL-05, TYPE-02 | T-04-13, T-04-14 | per-size records only | unit (pure data) | `make test PYTEST_ARGS="tests/test_tables.py tests/test_tables_second_entry.py tests/test_calc.py -q -n0 --no-cov"`; `expand('iso4017:M20x200')` / `M20x220` probe | ✅ | ✅ green |
| 04-10-T1 | 04-10 | 7 | TABL-02, TABL-03, TABL-04, TYPE-01, THRD-03 | T-04-15 | lg/ls relations on the stored cells | unit (pure data) | `make test PYTEST_ARGS="tests/test_tables.py tests/test_tables_second_entry.py -q -n0 --no-cov"` | ✅ | ✅ green |
| 04-10-T2 | 04-10 | 7 | TABL-02, TABL-03, TABL-04, TYPE-01, THRD-03 | — | 4017-before-4014 tie rule | unit | `make test PYTEST_ARGS="tests/test_tables.py tests/test_calc.py -q -n0 --no-cov"`; catalogue-order probe | ✅ | ✅ green |
| 04-11-T1 | 04-11 | 8 | INFO-03, INFO-05, TYPE-01 | T-04-16 | row values only on an exact match | unit, integration | `make test PYTEST_ARGS="tests/test_calc.py tests/test_api.py tests/test_parity.py -q -n0 --no-cov"`; `screw info bolt --pitch 0.75` no-row probe | ✅ | ✅ green |
| 04-11-T2 | 04-11 | 8 | INFO-03, INFO-05, TYPE-01 | T-04-17 | DIN note cites its sources | unit, integration | same command; `screw info bolt` notes probe | ✅ | ✅ green |
| 04-12-T1 | 04-12 | 9 | TABL-01, TABL-05, THRD-03 | T-04-19, T-04-20 | cached catalogue; `!r` echo only | integration, smoke | `make test PYTEST_ARGS="tests/test_parity.py tests/test_api.py tests/test_cli.py -q -n0 --no-cov"`; `screw presets bolt` probe; `make lint-imports` | ✅ | ✅ green |
| 04-12-T2 | 04-12 | 9 | TABL-01, TABL-05, THRD-03 | T-04-18 | dict lookup; `_Once` | smoke | `make test PYTEST_ARGS="tests/test_presets.py tests/test_parity.py tests/test_cli.py -q -n0 --no-cov"`; `--preset iso4014:M10x80 --length 20` exits 2 | ✅ | ✅ green |
| 04-13-T1 | 04-13 | 10 | TABL-01, TABL-05, TABL-06, TABL-07, INFO-03, INFO-05 | T-04-21 | text-only DOM | source pins (parity) | `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"`; `toFixed` count 0, `String(row.value)` present, debt item moved | ✅ | ✅ green; the browser check is Manual-Only |
| 04-13-T2 | 04-13 | 10 | TABL-01, TABL-05, TABL-06, TABL-07, INFO-03, INFO-05 | T-04-22 | the basis never enters the hash | source pins (parity) | same command; picker / badge / UI-SPEC greps | ✅ | ✅ green; the browser check is Manual-Only |
| 04-14-T1 | 04-14 | 10 | TYPE-01, TABL-04 | T-04-23 | L13 recorded with sources | smoke (grep) | L13 / L12 / overview grep chains | ✅ | ✅ green |
| 04-14-T2 | 04-14 | 10 | TYPE-01, TABL-04 | — | — | smoke | ROADMAP / REQUIREMENTS / debt / README greps; `make test PYTEST_ARGS="tests/test_cli.py -q -n0 --no-cov -k readme"` | ✅ | ✅ green |
| 04-15-T1 | 04-15 | 11 | TABL-01, TYPE-02 | T-04-29 | one rule: `_downloads` calls `download_refusal`, enums pinned to the route in OpenAPI | tracer (unit, integration) | `make test PYTEST_ARGS="tests/test_calc.py tests/test_api.py tests/test_parity.py -q -n0 --no-cov"`; `screw info bolt --preset iso4017:M8x70` downloads probe | ✅ | ✅ green |
| 04-15-T2 | 04-15 | 11 | TYPE-02 | T-04-29 | every catalogue row agrees with the rule; the pinned 62 is byte-identical to `d3eb46f` | unit | `make test PYTEST_ARGS="tests/test_presets.py -q -n0 --no-cov"`; `ast` diff of the counted test against `d3eb46f` | ✅ | ✅ green |
| 04-16-T1 | 04-16 | 12 | TABL-01, TYPE-02 | T-04-27, T-04-28, T-04-30 | text-only DOM; `quality` via `URLSearchParams.set`; the label names the quality it falls back to | tracer (source pins, parity) | `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"`; `setDownloads(q, info.downloads)` / `downloadLinks` greps | ✅ | ✅ green; the browser check is Manual-Only |
| 04-16-T2 | 04-16 | 12 | TABL-01 | — | L13 gains lines only, after the Info document paragraph | smoke (grep, difflib) | UI-SPEC / L13 / disposition / ideas grep chain; difflib one-insert check against `d3eb46f` | ✅ | ✅ green |

Every automated task also ends with `make verify`; it is green at the audited commit (`134dbae`: 2619 passed, coverage 97.57%, pre-commit run) and the per-task probes above were re-run on 2026-10-12 by the execute-phase orchestrator (25 of 26 pass; the one stale probe is noted on 04-03-T1). The G-04-3 gap closure (04-15, 04-16) was audited at `f3b5acd` (`make verify`: 2635 passed, coverage 97.33%); its four probes were re-run by the orchestrator on 2026-10-12 and pass.

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

From RESEARCH § Validation Architecture → Wave 0 Gaps:

- [x] `tests/test_tables.py` — per-row relations, UNVERIFIED scan with positive control, `Source` typing via `mypy.api`, series rules, cross-standard checks (TABL-02..05)
- [x] `tests/test_tables_second_entry.py` and `tests/data/` — the double-entry diff (TABL-04); blocked on the owner's purchased copies
- [x] `tests/test_presets.py` — catalogue round trip, 4017-before-4014 tie, API/CLI catalogue identity, fine-STL-refused count (TABL-01)
- [x] `tests/test_import_boundaries.py` — the subprocess `sys.modules` control for contract 6 (RESEARCH Alert 3)
- [x] No framework install is needed; existing `tests/test_params.py`, `test_solid.py`, `test_calc.py`, `test_api.py`, `test_cli.py`, `test_parity.py` are extended

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| The picker, badge, designation, groups, notes and unrounded numbers on the page | TABL-01, TABL-05, TABL-06, TABL-07, INFO-03, INFO-05 | No browser runs in the gate (L01); `tests/test_parity.py` pins the source, a throwaway node harness checked the list logic | The six-step checklist in `04-13-SUMMARY.md` (`make serve`, empty hash, pick ISO 4014 / M10 / 80, edit Length, Reset, reload an edited link, second-choice size) — the Phase 4 UAT item |
| A table row is marked verified only against the owner's purchased copy of its standard | TABL-04 | The purchased PDFs are not in the repo; the double-entry transcription is the owner checkpoint | Done: opening read 2026-10-11 (04-01 T2, ruling `A - 3.`) and the full copy 2026-10-12 (04-09 T1, ruling B: owner half generated from the purchased PDF text layer, agent half read from page images); recorded in `04-OWNER-READS.md`; no row shipped UNVERIFIED |
| `Download STL (preview)` with the refusal as its tooltip saves an STL for ISO 4017 / M8 / 70 beside an unchanged `Download STEP`; `Download STL` for M8 / 65; both disabled under their static labels after a failed update; the two buttons lay out in light, dark and under 820px | TABL-01, TYPE-02 | No browser runs in the gate (L01); `tests/test_parity.py` pins the source and applies rule 17 in Python to the live document | The Task 1 human check in `04-16-PLAN.md` (`make serve` or `SCREW_PORT=8001 make serve`, empty hash, pick ISO 4017 / M8 / 70, hover and click the STL button, click Download STEP, tick and untick Left-hand, pick M8 / 65, set Length 10 and Thread length 30, repeat in the other theme and under 820px) — the Phase 4 UAT item for G-04-3 |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 90s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-10-12 (execute-phase verify:post; 23 automated tasks green, 2 owner checkpoints and the 04-13 browser checks manual-only; no gaps, no auditor spawned); gap closure 04-15 and 04-16 validated 2026-10-12 (4 automated tasks green, the 04-16 browser check manual-only; no gaps, no auditor spawned)

## Validation Audit 2026-10-12

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
