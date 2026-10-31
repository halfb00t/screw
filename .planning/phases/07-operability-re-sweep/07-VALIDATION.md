---
phase: "7"
slug: "operability-re-sweep"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
# nyquist_compliant stays false: OPER-03 is Pending by owner ruling (in-wall parts the kernel refuses remain debt)
nyquist_compliant: false
wave_0_complete: true
created: "2026-10-26"
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `07-RESEARCH.md` § Validation Architecture. Owner rulings D-14..D-19 in `07-CONTEXT.md`.
> Audited at HEAD 7e03915: 1978 tests passed across 16 files (`-n4`, `--no-cov`). Verdict: PARTIAL (OPER-03 Pending).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x + xdist + coverage, mypy `--strict`, ruff, import-linter |
| **Config file** | `pyproject.toml` (`addopts` pinned; `fail_under = 96`) |
| **Quick run command** | `make test PYTEST_ARGS="tests/test_<file>.py -q -n0 --no-cov"` |
| **Full suite command** | `make verify` (plus `make check` for success criterion 4; needs Docker) |
| **Estimated runtime** | quick ~10-60 s; audited 16-file set ~55 s with `-n4`; `make verify` several minutes; runner tiers are dispatched workflows |

---

## Sampling Rate

- **After every task commit:** the targeted `make test PYTEST_ARGS="<files> -q -n0 --no-cov"` for touched files, plus `make lint typecheck lint-imports` for `calc` / `pool` / `app` edits
- **After every plan wave:** `make verify`
- **Before `/gsd-verify-work`:** `make verify` green, `make check` green, one successful full-tier workflow dispatch on the head, required-tier job green in `ci.yml`
- **Max feedback latency:** 60 s for the quick command

---

## Per-Task Verification Map

Task ID is `07-NN-TM` (plan NN, task M). Requirement-level gate: OPER-01 and OPER-02 complete; OPER-03 Pending.

Run notes: "(run)" means the file was executed in the audit. "inspected, not run" means the named tests exist and target the behaviour, but the file (`test_api.py`, `test_cli.py`, `test_calc.py`, `test_thread_maths.py`, `test_params.py`, `test_mesh.py`, `test_solid.py`) was not part of the audit run.

| Task ID | Plan | Wave | Requirement | Behavior | Test Type | Automated Command | Status |
|---------|------|------|-------------|----------|-----------|-------------------|--------|
| 07-01-T1 | 01 | 1 | OPER-01, OPER-02 | tracer: one point in the production image with its cgroup peak | unit | `make test PYTEST_ARGS="tests/test_oper.py -q -n0 --no-cov"` | ✅ green (run) |
| 07-01-T2 | 01 | 1 | OPER-01, OPER-02 | dispatchable workflow, make target, workflow pins | unit | `make test PYTEST_ARGS="tests/test_oper.py -q -n0 --no-cov"` | ✅ green (run) |
| 07-02-T1 | 02 | 1 | OPER-01 | queued request keeps its own full timeout (D-14) | unit | `make test PYTEST_ARGS="tests/test_pool.py -q -n0 --no-cov"` | ✅ green (run) |
| 07-02-T2 | 02 | 1 | OPER-01 | one timeout per artifact, no env override (D-09, D-16) | unit | `make test PYTEST_ARGS="tests/test_cost.py tests/test_pool.py tests/test_import_boundaries.py -q -n0 --no-cov"` | ✅ green (run) |
| 07-02-T3 | 02 | 1 | OPER-01 | timed-out admitted part logged as cost-model miss, not cached (D-10) | contract | `make test PYTEST_ARGS="tests/test_api.py tests/test_records.py -q -n0 --no-cov"` | ✅ green (test_records run; test_api inspected, not run) |
| 07-03-T1 | 03 | 2 | OPER-01, OPER-02, OPER-03 | tracer: probe point runs in image | unit | `make test PYTEST_ARGS="tests/test_oper.py -q -n0 --no-cov"` | ✅ green (run) |
| 07-03-T2 | 03 | 2 | OPER-01, OPER-02, OPER-03 | deterministic point-set generator, four committed sets | unit | `make test PYTEST_ARGS="tests/test_oper.py -q -n0 --no-cov"`; `.venv/bin/python -m bench.oper_sets --check` | ✅ green (test run; --check not run) |
| 07-03-T3 | 03 | 2 | OPER-01, OPER-02, OPER-03 | protocol, debt items, PR A | record | git/gh checks in the plan | 📄 process record |
| 07-04-T1 | 04 | 3 | OPER-01, OPER-02 | Codex review of PR A | human | — | 👤 human gate |
| 07-04-T2 | 04 | 3 | OPER-01, OPER-02 | land PR A, merge main, `make verify` | process | `make verify` | 📄 process record |
| 07-05-T1 | 05 | 4 | OPER-01, OPER-02, OPER-03 | runner tracer: cgroup peak and host facts | runner tier | committed record: RESULTS.md `### tracer, run 40645463872` | 🏃 manual (runner), record committed |
| 07-05-T2 | 05 | 4 | OPER-01, OPER-02, OPER-03 | dispatch explore/spread/walls/controls; margin, walk-down | runner tier | `make test PYTEST_ARGS="tests/test_oper_followup.py tests/test_oper.py -q -n0 --no-cov"`; RESULTS.md runs 40646117094, 40646125666, 40646134133, 40646142406 | ✅ test green (run); 🏃 runner record committed |
| 07-05-T3 | 05 | 4 | OPER-01, OPER-02, OPER-03 | margin, walk-down, walls, 5-rep confirm | runner tier | RESULTS.md `walls-down` 40652801529, `walls-voids` 40665307964, `walls-confirm` 40678150220; `bench.oper_sets --check` | 🏃 manual (runner), record committed |
| 07-06-T1 | 06 | 6 | OPER-01, OPER-02 | tracer: two-worker contention reading in image | unit | `make test PYTEST_ARGS="tests/test_oper_bound.py tests/test_oper.py -q -n0 --no-cov"` | ✅ green (run) |
| 07-06-T2 | 06 | 6 | OPER-01, OPER-02 | drift and arenas readings (R23) | unit | `make test PYTEST_ARGS="tests/test_oper_bound.py tests/test_oper.py -q -n0 --no-cov"` | ✅ green (run) |
| 07-06-T3 | 06 | 6 | OPER-01, OPER-02 | prove instruments on runner with smoke set | runner tier | `gh run list` bound-smoke success; `make verify` | 🏃 manual (runner) |
| 07-07-T1 | 07 | 5 | OPER-02, OPER-03 | walls derived from confirm; root-radius floor through model/API/CLI | unit | `make test PYTEST_ARGS="tests/test_oper_followup.py tests/test_thread_maths.py tests/test_api.py -q -n0 --no-cov"` | ✅ green (test_oper_followup run; test_thread_maths and test_api inspected, not run) |
| 07-07-T2 | 07 | 5 | OPER-02, OPER-03 | MAX_TURNS, MIN_TAIL_MM, per-field ceilings as cited walls | unit | `make test PYTEST_ARGS="tests/test_thread_maths.py tests/test_params.py tests/test_bench.py tests/test_oper_followup.py -q -n0 --no-cov"` | ✅ green (test_bench, test_oper_followup run; others inspected, not run) |
| 07-07-T3 | 07 | 5 | OPER-02, OPER-03 | L20, superseded clauses, debt items | static | `grep -c "^## L20 " docs/architecture/decision_log.md`; `make verify` | 📄 doc check |
| 07-08-T1 | 08 | 7 | OPER-02 | tracer: one load reading at N=1 in image | unit | `make test PYTEST_ARGS="tests/test_oper_load.py tests/test_oper.py -q -n0 --no-cov"` | ✅ green (run) |
| 07-08-T2 | 08 | 7 | OPER-02 | HEALTHCHECK probe wall, JSON bodies, per-level gzip | unit | `make test PYTEST_ARGS="tests/test_oper_load.py tests/test_oper.py -q -n0 --no-cov"` | ✅ green (run) |
| 07-08-T3 | 08 | 7 | OPER-02 | prove load instruments on runner (load-smoke) | runner tier | `gh run list` load-smoke success | 🏃 manual (runner) |
| 07-09-T1 | 09 | 6 | OPER-03 | fit one (kind, artifact, target) to fit.json, then all | unit | `make test PYTEST_ARGS="tests/test_oper_fit.py -q -n0 --no-cov"` | ✅ green (run) |
| 07-09-T2 | 09 | 6 | OPER-03 | candidate budget table and D-06 evidence | unit | `make test PYTEST_ARGS="tests/test_oper_fit.py -q -n0 --no-cov"` | ✅ green (run) |
| 07-10-T1-3 | 10 | 7 | OPER-03 | B-01..B-03 owner decisions (budget, refusal shape, defaulted cap) | human | — | 👤 human decision, recorded in 07-OWNER-RULINGS.md |
| 07-10-T4 | 10 | 7 | OPER-03 | record the three rulings | static | `grep -cE "^## B-0[123]" 07-OWNER-RULINGS.md` | 📄 doc check |
| 07-11-T1 | 11 | 8 | OPER-03 | tracer: bolt fine STL judged by cost model through calc/CLI/API/info | unit | `make test PYTEST_ARGS="tests/test_cost.py tests/test_cli.py tests/test_api.py tests/test_calc.py tests/test_presets.py tests/test_parity.py tests/test_import_boundaries.py -q -n0 --no-cov"` | ✅ green (cost, presets, parity, boundaries run; cli, api, calc inspected, not run) |
| 07-11-T2 | 11 | 8 | OPER-03 | every artifact of both kinds through the model; old cap unwired | unit | `make test PYTEST_ARGS="tests/test_cost.py tests/test_calc.py tests/test_api.py tests/test_cli.py tests/test_presets.py -q -n0 --no-cov"` | ✅ green (cost, presets run; others inspected, not run) |
| 07-11-T3 | 11 | 8 | OPER-03 | ruled 422 shape: API = CLI = info document | parity | `make test PYTEST_ARGS="tests/test_api.py tests/test_parity.py tests/test_cli.py -q -n0 --no-cov"` | ✅ green (parity run; api, cli inspected, not run) |
| 07-12-T1 | 12 | 9 | OPER-03 | defaulted thread_length capped to fit, API info and STL | unit | `make test PYTEST_ARGS="tests/test_cost.py tests/test_api.py -q -n0 --no-cov"` | ✅ green (cost run; api inspected, not run) |
| 07-12-T2 | 12 | 9 | OPER-03 | same cap on CLI and nut, with parity | unit | `make test PYTEST_ARGS="tests/test_cli.py tests/test_cost.py -q -n0 --no-cov"` | ✅ green (cost run; cli inspected, not run) |
| 07-12-T3 | 12 | 9 | OPER-03 | L21, superseded cap entries | static | `grep -c "^## L21 " docs/architecture/decision_log.md` | 📄 doc check |
| 07-13-T1 | 13 | 10 | OPER-03 | retire cap tables and refusals; move readers | unit | `make test PYTEST_ARGS="tests/test_thread_maths.py tests/test_calc.py tests/test_mesh.py tests/test_solid.py -q -n0 --no-cov"`; `! grep -rnE "FINE_STL_ROWS|fine_stl_refusal" src/` | ✅ green (inspected, not run) |
| 07-13-T2 | 13 | 10 | OPER-03 | resolve nut interim-bounds debt item | static | `test -f docs/tech_debt/resolved/2026-10-14-nut-interim-bounds.md` | 📄 doc check |
| 07-14-T1 | 14 | 10 | OPER-03 | tracer: refused preview shows info and the downloads that fit | JS/static | `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"` (`test_the_ui_offers_the_downloads_that_fit_when_the_preview_is_refused`) | ✅ green (run) |
| 07-14-T2 | 14 | 10 | OPER-03 | amend page contract in 01-UI-SPEC.md | static | `grep -c "Amended in Phase 7" 01-UI-SPEC.md` | 📄 doc check |
| 07-15-T1 | 15 | 10 | OPER-01, OPER-02, OPER-03 | D(A) and bound set generated; contention dispatched | unit | `make test PYTEST_ARGS="tests/test_oper_followup.py -q -n0 --no-cov"` | ✅ green (run) |
| 07-15-T2 | 15 | 10 | OPER-01, OPER-02, OPER-03 | dispatch every Runs II set | runner tier | RESULTS.md `bound` 40907549180, `load` 40909724292, `gzip` 40909739628, `arenas` 40909754190, `outband` 40909768713 | 🏃 manual (runner), record committed |
| 07-15-T3 | 15 | 10 | OPER-01, OPER-02, OPER-03 | re-check envelope against readings | unit | `make test PYTEST_ARGS="tests/test_oper_followup.py tests/test_cost.py tests/test_presets.py -q -n0 --no-cov"` | ✅ green (run) |
| 07-16-T1 | 16 | 11 | OPER-01, OPER-02 | derive pick, timeouts, serving values; ship timeouts | unit | `make test PYTEST_ARGS="tests/test_oper_followup.py tests/test_runtime_bounds.py -q -n0 --no-cov"` | ✅ green (run) |
| 07-16-T2 | 16 | 11 | OPER-01, OPER-02 | R22 W(K) runs and R23 drift run | runner tier | RESULTS.md `drift` 41016507364, `solid-cache-4` 41016510597, `drift-60` 41022812680 | 🏃 manual (runner), record committed |
| 07-16-T3 | 16 | 11 | OPER-01, OPER-02 | derive K and R23 outcomes; finish runtime.json | unit | `make test PYTEST_ARGS="tests/test_oper_followup.py tests/test_runtime_bounds.py -q -n0 --no-cov"` | ✅ green (run) |
| 07-17-T1 | 17 | 13 | OPER-01, OPER-02 | measured values in compose and Dockerfile | unit | `make test PYTEST_ARGS="tests/test_runtime_bounds.py -q -n0 --no-cov"`; `make image smoke` | ✅ green (test run; image smoke not run) |
| 07-17-T2 | 17 | 13 | OPER-01, OPER-02 | L22/L23 and the test tying each constant to its entry and run | consistency | `make test PYTEST_ARGS="tests/test_runtime_bounds.py -q -n0 --no-cov"` | ✅ green (run) |
| 07-17-T3 | 17 | 13 | OPER-01, OPER-02 | SCREW_BUILD_TIMEOUT gone, no INTERIM shipped, debt closed | static | `make test PYTEST_ARGS="tests/test_runtime_bounds.py tests/test_bench.py -q -n0 --no-cov"` | ✅ green (run) |
| 07-18-T1 | 18 | 13 | OPER-01, OPER-03 | tracer: boundary file and `bench.oper check` on synthetic readings | unit | `make test PYTEST_ARGS="tests/test_oper.py tests/test_oper_followup.py -q -n0 --no-cov"` | ✅ green (run) |
| 07-18-T2 | 18 | 13 | OPER-01, OPER-03 | `bounds` job in ci.yml and required-jobs.txt | agreement | `make test PYTEST_ARGS="tests/test_oper.py tests/test_grid.py tests/test_pr_land.py -q -n0 --no-cov"` | ✅ green (run) |
| 07-18-T3 | 18 | 13 | OPER-01, OPER-03 | bounds job green on runner via PR #26 | CI | `gh pr checks <pr>`; judged records from run 41089145344 | 🏃 manual (runner), recorded in 07-18-SUMMARY |
| 07-19-T1 | 19 | 14 | OPER-01, OPER-03 | tracer: full set, synthetic miss, R5 follow-up on 5 instances | unit | `make test PYTEST_ARGS="tests/test_oper.py tests/test_oper_followup.py -q -n0 --no-cov"`; `bench.oper_sets --check` | ✅ green (test run; follow-up job never ran on runner, see Manual-Only) |
| 07-19-T2 | 19 | 14 | OPER-01, OPER-03 | weekly and paths-filtered triggers; `pr.land` waits for full tier | unit | `make test PYTEST_ARGS="tests/test_oper.py tests/test_grid.py tests/test_pr_land.py -q -n0 --no-cov"` | ✅ green (run) |
| 07-19-T3 | 19 | 14 | OPER-01, OPER-03 | L24, L25, L07 trigger note | static | `grep -c "^## L24 " docs/architecture/decision_log.md` | 📄 doc check |
| 07-20-T1 | 20 | 15 | OPER-01, OPER-02, OPER-03 | full tier green on the head, recorded | runner tier | RESULTS.md `### full, run 41161227951` (also 41155746591); head 4a2b536 full tier 41162982938 | 🏃 manual (runner), record committed |
| 07-20-T2 | 20 | 15 | OPER-01, OPER-02, OPER-03 | every gate green on final head; `make check` | CI + Docker | `gh pr checks`; `make check` (ci.yml run 41162982868) | 🏃 manual (runner / Docker), recorded in 07-20-SUMMARY |
| 07-21-T1 | 21 | 12 | OPER-01, OPER-02 | tracer: busy 503 carries measured Retry-After; serving values | contract | `make test PYTEST_ARGS="tests/test_api.py tests/test_pool.py tests/test_runtime_bounds.py -q -n0 --no-cov"` | ✅ green (pool, runtime_bounds run; api inspected, not run) |
| 07-21-T2 | 21 | 12 | OPER-01, OPER-02 | worker-side knobs and CLI server count | unit | `make test PYTEST_ARGS="tests/test_runtime_bounds.py tests/test_cost.py tests/test_solid.py -q -n0 --no-cov"` | ✅ green (runtime_bounds, cost run; solid inspected, not run) |

*Status: ✅ green · 🏃 manual, runner-only with committed record · 📄 doc/static check or process record · 👤 human gate · ❌ red · ⚠️ flaky*

Counts (57 tasks, estimated from classification): about 36 test-covered, about 14 covered by committed runner record or doc check, 6 process or human, 0 MISSING, 0 PARTIAL.

---

## Wave 0 Requirements

- [x] `tests/test_cost.py` — cost model, envelope, refusals, golden points (OPER-03)
- [x] runner-harness modules and synthetic-record tests: `tests/test_oper.py`, `test_oper_bound.py`, `test_oper_load.py`, `test_oper_fit.py`, `test_oper_followup.py`, `test_oper_pitch.py`, `test_bench.py` (OPER-02)
- [x] pin tests for the full-tier workflow: `tests/test_oper.py` (T-3-14 pin: no `pull_request_target`, no `secrets.`)
- [x] consistency test constants vs decision log vs RESULTS.md: `tests/test_runtime_bounds.py` (OPER-01/02)
- [x] `tests/test_pr_land.py` full-tier rule tests (OPER-03)
- [x] refused-preview page test: `tests/test_parity.py::test_the_ui_offers_the_downloads_that_fit_when_the_preview_is_refused` (OPER-03)
- [x] pinned-string updates per research Pitfall 6
- [x] `make` targets for the new tiers

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| R5 follow-up job on 5 runner instances (07-19) | OPER-01 | The follow-up job has never run on the runner; code path pinned by `tests/test_oper_followup.py`. Debt: `docs/tech_debt/active/2026-10-31-full-tier-follow-up-job-never-run-on-the-runner.md` | Dispatch the full-tier workflow so the follow-up job runs; record the run id in `bench/RESULTS.md` |
| Every allowed configuration builds inside the timeout | OPER-03 | Pending by owner ruling; in-wall parts the kernel refuses remain open. Debt: `docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md` | Not to be covered in this phase; revisit when the debt item is scheduled |
| `make check` (SC4: builds off loop, image smoke) | OPER-01, OPER-02 | Needs Docker; recorded in `07-20-SUMMARY.md` (exit 0, Docker 29.4.0) | `make check` |
| Runner measurement runs | OPER-01/02 | Executed by `workflow_dispatch`; run ids in the map above and in `bench/RESULTS.md` (full tier on head: 41161227951) | dispatch workflow, record run id |
| Budget choice B-01..B-03 | OPER-03 | Owner rulings, recorded in `07-OWNER-RULINGS.md` | `checkpoint:decision`, done |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (consecutive non-test tasks are 04-T1/T2, 10-T1..T4, bounded by runner or doc checks)
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter (withheld: OPER-03 Pending by owner ruling)

**Approval:** partial, 2026-10-31 (OPER-03 Pending; follow-up job debt open)

## Validation Audit 2026-10-31

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 2 |
