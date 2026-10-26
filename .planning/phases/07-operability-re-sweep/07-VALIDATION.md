---
phase: "7"
slug: "operability-re-sweep"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-26"
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `07-RESEARCH.md` § Validation Architecture. Owner rulings D-14..D-19 in `07-CONTEXT.md`.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x + xdist + coverage, mypy `--strict`, ruff, import-linter |
| **Config file** | `pyproject.toml` (`addopts` pinned; `fail_under = 96`) |
| **Quick run command** | `make test PYTEST_ARGS="tests/test_<file>.py -q -n0 --no-cov"` |
| **Full suite command** | `make verify` (plus `make check` for success criterion 4; needs Docker) |
| **Estimated runtime** | quick ~10-60 s; `make verify` several minutes; runner tiers are dispatched workflows |

---

## Sampling Rate

- **After every task commit:** the targeted `make test PYTEST_ARGS="<files> -q -n0 --no-cov"` for touched files, plus `make lint typecheck lint-imports` for `calc` / `pool` / `app` edits
- **After every plan wave:** `make verify`
- **Before `/gsd-verify-work`:** `make verify` green, `make check` green, one successful full-tier workflow dispatch on the head, required-tier job green in `ci.yml`
- **Max feedback latency:** 60 s for the quick command

---

## Per-Task Verification Map

Task IDs are filled by the planner; requirement-level map below.

| Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|----------|-----------|-------------------|-------------|--------|
| OPER-01 | per-artifact timeout constants cite a run id; `SCREW_BUILD_TIMEOUT` gone (D-16) | unit | `make test PYTEST_ARGS="tests/test_pool.py -q -n0 --no-cov"` | ✅ extend / ❌ W0 cases | ⬜ pending |
| OPER-01 | overrun: terminate, slot replaced, nothing cached, 503 + derived `Retry-After`, cost-model-miss log | contract | `make test PYTEST_ARGS="tests/test_pool.py tests/test_api.py -q -n0 --no-cov"` | ✅ extend | ⬜ pending |
| OPER-01 | queue-aware deadline (D-14): request behind same-slot build keeps its own full timeout | unit | `make test PYTEST_ARGS="tests/test_pool.py -q -n0 --no-cov"` | ❌ W0 | ⬜ pending |
| OPER-01 | full-grid timings on runner (catalogue, integer `L/P`, nut) | runner tier | workflow dispatch + new `make` target | ❌ W0 | ⬜ pending |
| OPER-02 | no `INTERIM` label / spur figure left in `src/`, `Dockerfile`, `compose.yaml`, `app.js` | static scan | new test file | ❌ W0 | ⬜ pending |
| OPER-02 | constants equal decision-log / `bench/RESULTS.md` values | consistency | new test file | ❌ W0 | ⬜ pending |
| OPER-02 | cgroup `memory.peak` reader + harness predicates | unit (synthetic) | `make test PYTEST_ARGS="tests/test_bench.py -q -n0 --no-cov"` | ✅ extend | ⬜ pending |
| OPER-02 | native amd64 load sweep 1/2/3 workers, in image (D-15) | runner tier | workflow dispatch | ❌ W0 | ⬜ pending |
| OPER-03 | cost model kernel-free, envelope applied, golden points; covers nut (D-17) | unit + import contract | `make test PYTEST_ARGS="tests/test_cost.py -q -n0 --no-cov"`; `make lint-imports` | ❌ W0 | ⬜ pending |
| OPER-03 | per-artifact refusal parity API 422 = CLI exit 2 = `downloads[].refusal` | parity | `make test PYTEST_ARGS="tests/test_parity.py tests/test_api.py tests/test_cli.py -q -n0 --no-cov"` | ✅ extend | ⬜ pending |
| OPER-03 | preset refused count moves to new figure | unit | `make test PYTEST_ARGS="tests/test_presets.py -q -n0 --no-cov"` | ✅ edit | ⬜ pending |
| OPER-03 | page offers what fits when preview refused | JS/static | new test | ❌ W0 | ⬜ pending |
| OPER-03 | required boundary tier in `ci.yml` / `required-jobs.txt` | CI job + agreement test | `make test PYTEST_ARGS="tests/test_pr_land.py -q -n0 --no-cov"` | ✅ extend | ⬜ pending |
| OPER-03 | `pr_land` full-tier rule from diff; T-3-14 kept (`contents: read`, no `secrets.`, no `pull_request_target`) | unit w/ `gh` fixtures + text pin | `make test PYTEST_ARGS="tests/test_pr_land.py -q -n0 --no-cov"` | ✅ extend / ❌ W0 pin | ⬜ pending |
| SC4 | builds in worker processes off loop; `make check` passes | existing | `make verify`; `make check` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_cost.py` — cost model, envelope, refusals, golden points (OPER-03)
- [ ] runner-harness module + synthetic-record tests in `tests/test_bench.py` style (OPER-02)
- [ ] pin tests for the new full-tier workflow (OPER-03)
- [ ] consistency test: constants vs decision log vs `bench/RESULTS.md` (OPER-01/02)
- [ ] `tests/test_pr_land.py` recorded `gh` fixtures for the full-tier rule (OPER-03)
- [ ] test for the page's refused-preview path (OPER-03)
- [ ] pinned-string updates per research Pitfall 6
- [ ] `make` target(s) for the new tier(s)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Budget choice (research Q1) | OPER-03 | owner ruling on measured candidate table | `checkpoint:decision` after exploration sweep |
| Runner measurement runs | OPER-01/02 | executed by `workflow_dispatch` on GitHub; results committed to `bench/RESULTS.md` | dispatch workflow, record run id |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
