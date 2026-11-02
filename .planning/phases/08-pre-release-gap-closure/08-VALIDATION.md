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

Filled by the planner per task (2026-11-02, revised after the second plan check); rows run in execution
order, so 08-12 follows 08-05 and 08-13 follows 08-08 (waves: 08-01 W1; 08-02, 08-03 W2; 08-04, 08-05 W3;
08-12 W4; 08-06 W5; 08-07 W6; 08-08 W7; 08-13 W8; 08-09 W9; 08-10 W10; 08-11 W11). The requirement-to-test
map below it is the source.

| Task | Req / SC | Automated command | Status |
|------|----------|-------------------|--------|
| 08-01 T1 | OPER-03 / SC1 | `make test PYTEST_ARGS="tests/test_oper_fine.py tests/test_oper_pitch.py -q -n0 --no-cov"`; `.venv/bin/python -m bench.oper_sets --check` | ⬜ |
| 08-01 T2 | OPER-03 / SC1 | F1 to F14 heading check; blob sha grep | ⬜ |
| 08-01 T3 | OPER-03 / SC1 | checkpoint: owner dispatches `fine-bands`; `gh run view <id> --json headSha,event` | ⬜ |
| 08-02 T1 | OPER-03 / SC2 | `make test PYTEST_ARGS="tests/test_cli.py -q -n0 --no-cov"` | ⬜ |
| 08-02 T2 | TABL-06 / SC3 | `grep -q 'once a dimension the row prints is edited' .planning/REQUIREMENTS.md` | ⬜ |
| 08-02 T3 | INFO-05 / SC5 | `grep -q '^requirements-completed: \[INFO-05\]$' .planning/phases/04-iso-hex-bolts-and-screws/04-11-SUMMARY.md`; INT-04 and INT-05 debt files and INDEX rows | ⬜ |
| 08-03 T1 | OPER-03 / SC1 | `make test PYTEST_ARGS="tests/test_oper_fine.py -q -n0 --no-cov"` (edge and D-19 check-cell cases) | ⬜ |
| 08-03 T2 | OPER-03 / SC1 | `.venv/bin/python -m bench.oper_sets fine-bands --from bench/results/phase-08/fine-bands-<id>` | ⬜ |
| 08-04 T1 | FRNT-05 / SC4 | `make test PYTEST_ARGS="tests/test_parity.py tests/test_cost.py -q -n0 --no-cov"` (the INT-03 part and the registry-driven typed-default cases of every kind); human-check: browser at d 30, pitch 2, s 48, k 18, typed thread_length 20, recorded under `## Browser check` | ⬜ |
| 08-04 T2 | FRNT-05 / SC4 | L35 and note greps; `make test PYTEST_ARGS="tests/test_runtime_bounds.py tests/test_parity.py -q -n0 --no-cov"`; web-half debt file and INDEX row | ⬜ |
| 08-05 T1 | OPER-03 / SC1 | `make test PYTEST_ARGS="tests/test_thread_maths.py tests/test_nut.py -q -n0 --no-cov"` (island nuts, spies); `make lint typecheck lint-imports` | ⬜ |
| 08-05 T2 | OPER-03 / SC1 | `make test PYTEST_ARGS="tests/test_thread_maths.py tests/test_nut.py -q -n0 --no-cov"` (bolt route, catalogue); `make lint typecheck lint-imports` | ⬜ |
| 08-12 T1 | OPER-03 / SC1 | `make test PYTEST_ARGS="tests/test_oper_fine.py tests/test_solid.py -k 'shipped_bands or long_thread' -q -n0 --no-cov"`; `--check` | ⬜ |
| 08-12 T2 | OPER-03 / SC1 | `make test PYTEST_ARGS="tests/test_thread_maths.py tests/test_oper_fine.py tests/test_solid.py -q -n0 --no-cov"`; head pushed | ⬜ |
| 08-06 T1 | OPER-03 / SC1 | `make test PYTEST_ARGS="tests/test_oper_fine.py tests/test_oper_pitch.py -q -n0 --no-cov"` (grid (b) with the band walk's refused fine-sweep cells); `--check` | ⬜ |
| 08-06 T2 | OPER-03 / SC1 | `make test PYTEST_ARGS="tests/test_oper_fine.py -q -n0 --no-cov"`; `--check`; `bench.oper matrix` | ⬜ |
| 08-06 T3 | OPER-03 / SC1 | checkpoint: owner dispatches `fine-proof`, `fine-cost`, `fine-spread` | ⬜ |
| 08-07 T1 | OPER-03 / SC1 | `make test PYTEST_ARGS="tests/test_oper_fine.py -q -n0 --no-cov"` | ⬜ |
| 08-07 T2 | OPER-03 / SC1 | `.venv/bin/python -m bench.oper_sets fine-ceilings --from bench/results/phase-08/fine-proof-<id>` | ⬜ |
| 08-08 T1 | OPER-03 / SC1 | `make test PYTEST_ARGS="tests/test_oper_fit.py -q -n0 --no-cov"` (F10 judge, `fine-fit.json` regeneration); fit.json and cost.py unchanged | ⬜ |
| 08-08 T2 | OPER-03 / SC1 | `make test PYTEST_ARGS="tests/test_cost.py tests/test_oper_fit.py -q -n0 --no-cov"` (emit block); no point file or runtime.json moved | ⬜ |
| 08-13 T1 | OPER-03 / SC1 | `make test PYTEST_ARGS="tests/test_cost.py tests/test_runtime_bounds.py tests/test_oper_bound.py -q -n0 --no-cov"`; `--check`; pre-Phase-8 point files unchanged | ⬜ |
| 08-13 T2 | OPER-03 / SC1 | RESULTS `### The fine envelope (F10, 08 D-05)` once, saying sampled; `make test PYTEST_ARGS="tests/test_runtime_bounds.py tests/test_cost.py -q -n0 --no-cov"` | ⬜ |
| 08-09 T1 | OPER-03 / SC1 | `make test PYTEST_ARGS="tests/test_turn_guard.py tests/test_fine_pitch.py tests/test_oper_fine.py tests/test_params.py -q -n0 --no-cov"`; `--check`; no guard region beyond the bands | ⬜ |
| 08-09 T2 | OPER-03 / SC1 | F13, A3 and D-17 debt files with `Severity: must` and INDEX rows; every Active INDEX link resolves | ⬜ |
| 08-10 T1 | OPER-03 / SC1 | `make test PYTEST_ARGS="tests/test_oper_fine.py tests/test_fine_pitch.py tests/test_oper_pitch.py tests/test_runtime_bounds.py tests/test_oper.py -q -n0 --no-cov"`; debt move, OPER-03, L36 (D-20, sampled, the eight nut rows) and D-20 greps on OPER-03 and ROADMAP SC1 | ⬜ |
| 08-10 T2 | SC1 to SC5 | `make verify`; `--check`; L34 to L36, OPER-03 and SC1 with D-20, TABL-06, INFO-05 and six-debt greps; head pushed, no PR open | ⬜ |
| 08-11 T1 | SC1 to SC5 | checkpoint: Codex reviews `git diff origin/main...<sha>` (HOW_TO_DEVELOP section 8) | ⬜ |
| 08-11 T2 | SC1 to SC5 | `make verify`; `--check`; fixes pushed, no PR open | ⬜ |
| 08-11 T3 | SC5 | checkpoint: owner runs `/gsd-validate-phase 6`, `/gsd-validate-phase 7`, `/gsd-audit-milestone` | ⬜ |

The requirement-to-test map:

| Req / SC | Behavior | Test Type | Automated Command | File Exists |
|----------|----------|-----------|-------------------|-------------|
| SC1 sweep | fine predicate exact and strict at thresholds (nut `> 6`; bolt only inside a measured band above 6, D-15, D-19; no d / pitch-only bolt clause); `helical.thread(fine=True)` uses 56 samples and the tolerance; default call unchanged | unit + kernel (2-3 cells) | `make test PYTEST_ARGS="tests/test_thread_maths.py tests/test_solid.py -q -n0 --no-cov"` | extend |
| SC1 island | 6 island nuts (d 2.2, d/pitch ~7, forms base/s4/m1, both hands) build | kernel | `make test PYTEST_ARGS="tests/test_nut.py -k island -q -n0 --no-cov"` | ❌ W0 |
| SC1 long thread | d 3, pitch 0.35, 25 mm right and d 2.5, pitch 0.35, 30 mm right build (08-12) | kernel | `make test PYTEST_ARGS="tests/test_solid.py -k long_thread -q -n0 --no-cov"` | ❌ W0 |
| SC1 guard | turns guard is 422 with `ctx.fields` [d, pitch, thread_length, length] on API, exit 2 on CLI, same text; band regions only, no bolt outside the bands guarded (D-19); no catalogue row refused | kernel-free | `make test PYTEST_ARGS="tests/test_fine_pitch.py tests/test_turn_guard.py -q -n0 --no-cov"` | ❌ W0 |
| SC1 proof grid | every grid point `ok` in committed runner records or refused by the model | records-driven | `make test PYTEST_ARGS="tests/test_oper_fine.py -q -n0 --no-cov"` | ❌ W0 |
| SC1 constants | thresholds, bands, ceilings, `FINE_ENVELOPE` equal judge output from `bench/results/phase-08/` | records-driven | `make test PYTEST_ARGS="tests/test_cost.py tests/test_oper_fit.py tests/test_oper_pitch.py -q -n0 --no-cov"` | extend |
| SC1 debt | 20 in-wall parts handled; debt moved to `resolved/` with INDEX row; F13, A3 and D-17 residuals filed under `active/` | existing + grep | `make test PYTEST_ARGS="tests/test_fine_pitch.py -q -n0 --no-cov"` | exists |
| SC1 text (D-20) | OPER-03 and ROADMAP SC1 state D-07's grid bar and name the off-grid residual with the F13 debt path, in the `[x]` commit; no wider claim survives | grep | 08-10 T1's OPER-03 and SC1 grep loop | n/a |
| SC2 | `export` help or README carries the no-deadline line; Lxx exists | text assertion | `make test PYTEST_ARGS="tests/test_cli.py -q -n0 --no-cov"` | extend |
| SC3 | TABL-06 text agrees with L19 | grep | `grep -n "TABL-06" .planning/REQUIREMENTS.md` | n/a |
| SC4 | d=30 pitch=2 s=48 k=18 with typed `thread_length=20` is 422 `over_budget` / exit 2 on API and CLI; every kind's defaulted fields typed at their defaults answer alike on API and CLI and are never capped (registry-driven); page source writes a touched field; the un-executed page half is filed as debt | API+CLI executed, web source assertions, debt | `make test PYTEST_ARGS="tests/test_parity.py tests/test_cost.py -q -n0 --no-cov"` | extend |
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
| Runner walk and re-sweep readings on linux/amd64 | OPER-03 (D-04, D-05) | L33: CI measures nothing; dispatches are by hand | `gh workflow run operability.yml --ref <branch> -f set=<set>` (`set` is the workflow's only input, L33); then `gh run download <id> -p 'oper-*'` |
| Web form typed-default behavior in a browser | FRNT-05 / INT-03 | No browser harness (L01); filed as must debt `docs/tech_debt/active/<date>-typed-default-web-half-is-source-pinned.md` with its triggers | 08-04 T1 human-check: `make serve`, d 30, pitch 2, s 48, k 18, type thread_length 20; the link keeps it and the refusal matches the API; record in 08-04-SUMMARY `## Browser check` |
| Codex review of the phase branch | SC1 to SC5 | the author CLI may not review its own diff (HOW_TO_DEVELOP section 8) | 08-11 T1: Codex reviews `git diff origin/main...<sha>`; findings become commits in 08-11 T2 |
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
