---
phase: "08"
slug: "pre-release-gap-closure"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-11-02"
---

# Phase 08 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 + pytest-xdist 3.8.0 + pytest-cov 7.1.0 (coverage floor 96) |
| **Config file** | `pyproject.toml` (`addopts = "--strict-markers --strict-config -m 'not grid and not pair'"`) |
| **Quick run command** | `make test PYTEST_ARGS="tests/test_fine_pitch.py tests/test_cost.py -q -n0 --no-cov"` |
| **Full suite command** | `make verify` |
| **Estimated runtime** | quick ~30 s; full suite several minutes (kernel tests under xdist) |

---

## Sampling Rate

- **After every task commit:** the targeted `make test PYTEST_ARGS=...` command for the touched files, plus `make lint typecheck lint-imports` for `calc`, `params` and `bench` edits.
- **After every plan wave:** `make verify`.
- **Before `/gsd-verify-work`:** `make verify` green, `.venv/bin/python -m bench.oper_sets --check` clean, runner records committed.
- **Max feedback latency:** quick command under 60 s.

---

## Per-Task Verification Map

Filled by the planner per task; the requirement-to-test map below is the source.

| Req / SC | Behavior | Test Type | Automated Command | File Exists |
|----------|----------|-----------|-------------------|-------------|
| SC1 sweep | fine predicate exact and strict at thresholds (nut `> 6`, bolt `> 8`, bolt band predicate D-15); `helical.thread(fine=True)` uses 56 samples and the tolerance; default call unchanged | unit + kernel (2-3 cells) | `make test PYTEST_ARGS="tests/test_thread_maths.py tests/test_solid.py -q -n0 --no-cov"` | extend |
| SC1 island | 6 island nuts (d 2.2, d/pitch ~7, forms base/s4/m1, both hands) build | kernel | `make test PYTEST_ARGS="tests/test_nut.py -k island -q -n0 --no-cov"` | ❌ W0 |
| SC1 long thread | d 3, pitch 0.35, 25 mm right and d 2.5, pitch 0.35, 30 mm right build | kernel | `make test PYTEST_ARGS="tests/test_solid.py -k long_thread -q -n0 --no-cov"` | ❌ W0 |
| SC1 guard | turns guard is 422 with `ctx.fields` [d, pitch, thread_length, length] on API, exit 2 on CLI, same text; no catalogue row refused | kernel-free | `make test PYTEST_ARGS="tests/test_fine_pitch.py tests/test_turn_guard.py -q -n0 --no-cov"` | ❌ W0 |
| SC1 proof grid | every grid point `ok` in committed runner records or refused by the model | records-driven | `make test PYTEST_ARGS="tests/test_oper_fine.py -q -n0 --no-cov"` | ❌ W0 |
| SC1 constants | thresholds, bands, ceilings, `FINE_ENVELOPE` equal judge output from `bench/results/phase-08/` | records-driven | `make test PYTEST_ARGS="tests/test_cost.py tests/test_oper_fit.py tests/test_oper_pitch.py -q -n0 --no-cov"` | extend |
| SC1 debt | 20 in-wall parts handled; debt moved to `resolved/` with INDEX row | existing + grep | `make test PYTEST_ARGS="tests/test_fine_pitch.py -q -n0 --no-cov"` | exists |
| SC2 | `export` help or README carries the no-deadline line; Lxx exists | text assertion | `make test PYTEST_ARGS="tests/test_cli.py -q -n0 --no-cov"` | extend |
| SC3 | TABL-06 text agrees with L19 | grep | `grep -n "TABL-06" .planning/REQUIREMENTS.md` | n/a |
| SC4 | d=30 pitch=2 s=48 k=18 with typed `thread_length=20` is 422 `over_budget` / exit 2 on API and CLI; page source writes a touched field | API+CLI executed, web source assertions | `make test PYTEST_ARGS="tests/test_parity.py tests/test_cost.py -q -n0 --no-cov"` | extend |
| SC5 | Phase 4 SUMMARY lists INFO-05; 06/07 VALIDATION.md `status: validated`; audit `passed`/`tech_debt` | grep + workflows | `grep -n "requirements-completed" .planning/phases/04-*/04-1[13]-SUMMARY.md` | n/a |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_turn_guard.py` — API 422 shape, CLI exit 2, catalogue untouched
- [ ] `tests/test_oper_fine.py` — proof grid against committed records; constants against the judge
- [ ] kernel cells for the island and the long-thread examples in `tests/test_nut.py` / `tests/test_solid.py`
- [ ] `bench/oper_lift.py` lift for the guard before any set is regenerated
- [ ] Phase 8 sweep protocol (rules before data) and the walk and re-sweep point files

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Runner walk and re-sweep readings on linux/amd64 | OPER-03 (D-04, D-05) | L33: CI measures nothing; dispatches are by hand | `gh workflow run operability.yml --ref <branch> -f mode=measure -f set=<set>`; then `gh run download <id> -p 'oper-*'` |
| Web form typed-default behavior in a browser | FRNT-05 / INT-03 | No browser harness (L01) | Type a field equal to its default, check the link keeps it and the answer matches the API |
| `/gsd-validate-phase 6`, `/gsd-validate-phase 7`, `/gsd-audit-milestone` | SC5 | GSD workflows run by the human | Run each; check status fields |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
