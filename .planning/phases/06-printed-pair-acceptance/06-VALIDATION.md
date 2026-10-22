---
phase: "06"
slug: "printed-pair-acceptance"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-22"
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 + pytest-xdist 3.8.0 + pytest-cov 7.1.0 (coverage floor 96) |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`, markers `grid`, `pair` deselected by `addopts`; import-linter contracts) |
| **Quick run command** | `make test PYTEST_ARGS="tests/test_print_rules.py tests/test_params.py tests/test_calc.py -q -n0 --no-cov"` |
| **Full suite command** | `make verify` |
| **Estimated runtime** | quick ~60 seconds warm; full several minutes (pre-commit hook runs it; use 600 s Bash timeout) |

---

## Sampling Rate

- **After every task commit:** Run the quick command for the touched modules
- **After every plan wave:** Run `make verify`
- **Before `/gsd-verify-work`:** `make verify` green, record sha256 pinned, PAIR-05 acceptance recorded by the owner
- **Max feedback latency:** 600 seconds

---

## Per-Task Verification Map

Filled by the planner per task; requirement-level map from RESEARCH.md:

| Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|----------|-----------|-------------------|-------------|--------|
| PAIR-02 | rule module derives the default from synthetic records; `None` on no pass / non-monotone; refuses malformed rows | unit | `make test PYTEST_ARGS="tests/test_print_rules.py -k default -q -n0 --no-cov"` | ❌ W0 | ⬜ pending |
| PAIR-02 | committed record sha256 equals pin; shipped `NutParams` clearance default equals `default_from(record)` | unit | `make test PYTEST_ARGS="tests/test_print_rules.py -k committed -q -n0 --no-cov"` | ❌ W0 | ⬜ pending |
| PAIR-02 | default is one absolute-mm literal; omitted clearance rebuilds that value on API/CLI/link | unit | `make test PYTEST_ARGS="tests/test_params.py tests/test_nut.py tests/test_api.py tests/test_cli.py -q -n0 --no-cov"` | ✅ rewrite | ⬜ pending |
| PAIR-02 | registry has no required field; parity rules still bite | unit | `make test PYTEST_ARGS="tests/test_parity.py -k required -q -n0 --no-cov"` | ✅ adjust | ⬜ pending |
| PAIR-02 | nut outside measured range carries the D-09 warning on API and CLI identically | unit/parity | `make test PYTEST_ARGS="tests/test_calc.py tests/test_parity.py -k measured -q -n0 --no-cov"` | ❌ W0 | ⬜ pending |
| PAIR-05 | M8 counterpart carries no clearance; nut uses the default | unit | `make test PYTEST_ARGS="tests/test_calc.py -k counterpart -q -n0 --no-cov"` | ✅ | ⬜ pending |
| PAIR-06 | D-14 rule: ≥2/3 binds promotes PAIR-07; 1/3 does not; refusal on incomplete data | unit | `make test PYTEST_ARGS="tests/test_print_rules.py -k bought -q -n0 --no-cov"` | ❌ W0 | ⬜ pending |
| INFO-04 | below threshold both kinds warn naming edge, run and Lxx; at/above no warning; no 422 | unit | `make test PYTEST_ARGS="tests/test_calc.py -k printab -q -n0 --no-cov"` | ❌ W0 | ⬜ pending |
| INFO-04 | `d_min`, `P_min` equal `thresholds_from(record2)` | unit | `make test PYTEST_ARGS="tests/test_print_rules.py -k threshold -q -n0 --no-cov"` | ❌ W0 | ⬜ pending |
| INFO-04 | CLI and API emit identical printability warnings | parity | `make test PYTEST_ARGS="tests/test_parity.py -k printab -q -n0 --no-cov"` | partly ✅ | ⬜ pending |
| protocol | template, manifest and tests agree on sample counts and file names | unit | `make test PYTEST_ARGS="tests/test_print_rules.py -k protocol -q -n0 --no-cov"` | ❌ W0 | ⬜ pending |
| contract | `bench.print_rules` kernel-free; printability module import limits | import-linter | `make lint-imports` | contract edit | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `bench/print_rules.py`, `tests/test_print_rules.py` — PAIR-02, PAIR-06, INFO-04 rules with synthetic positive/negative controls
- [ ] `bench/print_matrix.py` (matrix as data, manifest writer) and blank `bench/results/phase-06/print-run-*.tsv`
- [ ] `06-PRINT-PROTOCOL.md`
- [ ] `pyproject.toml`: kernel-free contract covers `bench.print_rules` (and matrix module if kernel-free)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Print profile and predictions typed into protocol before PR A lands | PAIR-02, INFO-04 | owner's printer and judgement | owner edits protocol on the pre-registration branch |
| PR A reviewed by the other CLI and landed | PAIR-02 | cross-CLI review rule | Codex review, merge |
| Print run 1 (60 nuts + 12 bolts), fit-test every sample in pre-registered order | PAIR-02 | physical print | owner fills `print-run-1.tsv`; sha256 recorded |
| Printed bolts into bought steel nuts, 3 per size | PAIR-06 | physical | owner, same record |
| Print run 2 (M3–M5) and fit-test | INFO-04 | physical | owner fills `print-run-2.tsv` |
| Fresh M8 pair at the shipped default threads by hand | PAIR-05 | physical acceptance | owner records in SUMMARY/UAT with exported file sha256 |
| Below-threshold part shows the warning on the page | INFO-04 | no browser test in gate | owner at UAT |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 600s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
