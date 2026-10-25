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
| PAIR-06 | deferred to v2 by owner ruling R9 (2026-10-22): no bought-nut rule, record or test | - | - | - | deferred |
| INFO-04 | below threshold both kinds warn naming edge, run and Lxx; at/above no warning; no 422 | unit | `make test PYTEST_ARGS="tests/test_calc.py -k printab -q -n0 --no-cov"` | ❌ W0 | ⬜ pending |
| INFO-04 | `d_min`, `P_min` equal `thresholds_from(record2)` | unit | `make test PYTEST_ARGS="tests/test_print_rules.py -k threshold -q -n0 --no-cov"` | ❌ W0 | ⬜ pending |
| INFO-04 | CLI and API emit identical printability warnings | parity | `make test PYTEST_ARGS="tests/test_parity.py -k printab -q -n0 --no-cov"` | partly ✅ | ⬜ pending |
| protocol | template, manifest and tests agree on sample counts and file names | unit | `make test PYTEST_ARGS="tests/test_print_rules.py -k protocol -q -n0 --no-cov"` | ❌ W0 | ⬜ pending |
| contract | `bench.print_rules` kernel-free; printability module import limits | import-linter | `make lint-imports` | contract edit | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### Per task (filled by the planner, 2026-10-22)

| Plan · Task | Requirement | Automated check (from the main checkout) | Kind |
|-------------|-------------|------------------------------------------|------|
| 06-01 · 1 (tracer) | PAIR-02, INFO-04 | branch commit subject on `gsd/phase-06-preregistration` (hook ran `make verify` in the worktree); `git show` of `bench/print_rules.py` holds the seven functions and the ladder literal; contract lists `bench.print_rules` | git + hook |
| 06-01 · 2 | PAIR-02, INFO-04 | commit subject; branch file set is exactly seven files; the three blank records hold 61, 13, 10 lines | git + hook |
| 06-02 · 1 | — | checkpoint:decision (owner) | manual |
| 06-02 · 2 | — | `06-OWNER-RULINGS.md` has R1-R8 lines with option ids and a `Ruled:` date | grep |
| 06-03 · 1 (tracer) | all four | commit subject; protocol headings are the nine in order | git + hook |
| 06-03 · 2 | PAIR-02 | checkpoint:human-action (owner types profile and predictions) | manual |
| 06-03 · 3 | all four | no owner slot in the committed protocol; PR A file set is eight files; `gh pr view` reads `OPEN main` | git + gh |
| 06-04 · 1 | — | checkpoint:human-action (Codex review) | manual |
| 06-04 · 2 | PAIR-02, INFO-04 | PR A `MERGED`; phase branch contains origin/main and the landed files; `make verify` | gh + gate |
| 06-05 · 1 (tracer) | PAIR-02 | manifest-run-1 header and 4 + 20 rows; each digest matches its file; commit subject | file + python |
| 06-05 · 2 | PAIR-02 | checkpoint:human-action (print run 1); reader passes read-only | manual |
| 06-05 · 3 | PAIR-02 | `make test PYTEST_ARGS="tests/test_print_rules.py -q -n0 --no-cov"`; one digest pinned; RESULTS heading | pytest + grep |
| 06-06 · 1 | PAIR-02 | checkpoint:decision (`permanent: accepted`, one-way) | manual |
| 06-06 · 2 (tracer) | PAIR-02 | `screw info nut` with no clearance reads the record's value; the six-file pytest run; `make verify` | CLI + pytest + gate |
| 06-06 · 3 | PAIR-02 | `## L17` present; PAIR-02 ticked; debt triggers moved | grep |
| 06-07 · 1 (tracer) | PAIR-02 | `make test ... -k measured`; CLI warning for d 5 cites L17 and the run; `make verify` | pytest + CLI + gate |
| 06-07 · 2 | PAIR-02 | no "required" clearance text in the API docstring or overview; `make verify` | grep + gate |
| 06-08 · 1 (tracer) | INFO-04 | manifest-run-2 header and 3 + 3 rows; digests match; nut names carry the shipped default | file + python |
| 06-08 · 2 | INFO-04 | checkpoint:human-action (print run 2); reader passes read-only | manual |
| 06-08 · 3 | INFO-04 | `make test ... -k run_2`; digest pinned; RESULTS heading | pytest + grep |
| 06-09 · 1 (tracer) | INFO-04 | `make test ... -k printab`; CLI warning on the M2 bolt cites run 2, d before pitch; `make verify` | pytest + CLI + gate |
| 06-09 · 2 | INFO-04 | entry cites `06-print-run-2`; INFO-04 ticked; `<human-check>` page glance for end-of-phase UAT | grep + manual |
| 06-10 · 1 (tracer) | PAIR-05 | the acceptance entry holds a proven verdict; manifest lists one M8 bolt and nut; dev server answers | file + curl |
| 06-10 · 2 | PAIR-05 | checkpoint:human-action (page path, print, hand test) | manual |
| 06-10 · 3 | PAIR-05 | the entry's owner result line is pass or bind; `make verify` | grep + gate |

No three consecutive tasks lack an automated check: every manual checkpoint sits between automated tasks.

---

## Wave 0 Requirements

- [ ] `bench/print_rules.py`, `tests/test_print_rules.py` — PAIR-02, INFO-04 rules with synthetic positive/negative controls
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
| Printed bolts into bought steel nuts, 3 per size | PAIR-06 | deferred to v2 by owner ruling R9 (2026-10-22) | not run in Phase 6 |
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
