---
phase: "4"
slug: "iso-hex-bolts-and-screws"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
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
| (filled from `04-*-PLAN.md` task `<verify>` blocks by validate-phase) | | | | | | | | | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

From RESEARCH § Validation Architecture → Wave 0 Gaps:

- [ ] `tests/test_tables.py` — per-row relations, UNVERIFIED scan with positive control, `Source` typing via `mypy.api`, series rules, cross-standard checks (TABL-02..05)
- [ ] `tests/test_tables_second_entry.py` and `tests/data/` — the double-entry diff (TABL-04); blocked on the owner's purchased copies
- [ ] `tests/test_presets.py` — catalogue round trip, 4017-before-4014 tie, API/CLI catalogue identity, fine-STL-refused count (TABL-01)
- [ ] `tests/test_import_boundaries.py` — the subprocess `sys.modules` control for contract 6 (RESEARCH Alert 3)
- [ ] No framework install is needed; existing `tests/test_params.py`, `test_solid.py`, `test_calc.py`, `test_api.py`, `test_cli.py`, `test_parity.py` are extended

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| A table row is marked verified only against the owner's purchased copy of its standard | TABL-04 | The purchased PDFs are not in the repo; the double-entry transcription is the owner checkpoint | Owner confirms the M6 × 20 row and the ISO 262 M6 pitch at the opening checkpoint before any row is committed as verified; rows entered from previews stay UNVERIFIED |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
