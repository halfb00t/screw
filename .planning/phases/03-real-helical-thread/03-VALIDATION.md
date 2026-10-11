---
phase: "3"
slug: "real-helical-thread"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-10"
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (>=8) + pytest-xdist 3.8.0 + pytest-cov 7.1.0; `filterwarnings = ["error"]`, `xfail_strict`, `--strict-markers`, `--strict-config` |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (plan 03-06 adds the `grid` marker and `-m 'not grid'`); coverage floor `[tool.coverage.report] fail_under` (94, re-measured in plan 03-07) |
| **Quick run command** | `make test PYTEST_ARGS="<the task's test files> -q -n0 --no-cov"` (each task's `<verify>` names its files) |
| **Full suite command** | `make verify` (ruff, mypy --strict, import contracts, unfinished-work scan, pytest under the coverage floor); the pre-commit hook runs it on every commit |
| **Slow tier** | `make grid` (all 15 sizes) or `make grid SIZE=M3.5` (one size); CI: `.github/workflows/grid.yml`, dispatch + weekly, never a required job (D-14) |
| **Estimated runtime** | ~40 s for `make verify` on the baseline (695 passed in 37.96 s, 95.56 %); expect more once every default build is a thread (M6 x 20 builds in 0.09 s, the gate adds about 0.13 s); a grid shard takes minutes, the full grid hours of compute (RESEARCH A2) |

---

## Sampling Rate

- **After every task commit:** the task's quick command, then `make lint-imports` when `pyproject.toml` or a module edge moved; the commit itself runs `make verify` (pre-commit hook), so no commit lands red
- **After every plan wave:** `make verify`
- **Before `/gsd-verify-work`:** `make verify` green, and the slow tier recorded at least as the two local shards of plan 03-06 (M3.5, M4) in bench/RESULTS.md; `grid.yml` can only be dispatched once it is on the default branch, so its first CI run is recorded after merge (it records, it never gates `main`)
- **Max feedback latency:** ~60 s for a task's quick command; ~90 s for `make verify`; nothing in `make verify` asserts a timing (02 D-15)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 1 | THRD-01, THRD-04 | T-3-01, T-3-02 | default bolt is the gated L11 thread; a tiny length refuses at the doorway, never SIGSEGVs | integration (real kernel) + e2e CLI | `make test PYTEST_ARGS="tests/test_solid.py tests/test_api.py tests/test_cli.py tests/test_pool.py -q -n0 --no-cov"` | ✅ (extended) | ✅ green |
| 3-01-02 | 01 | 1 | THRD-04, THRD-01 | T-3-02 | naive and inverted controls refused; refusal never cached; rod, void, sub-turn, drift sample | unit (kernel-free) + integration | `make test PYTEST_ARGS="tests/test_thread_maths.py tests/test_solid.py -q -n0 --no-cov"` | ❌ creates tests/test_thread_maths.py in-task | ✅ green |
| 3-01-03 | 01 | 1 | THRD-04 | T-3-03 | broken STL/STEP export is a BuildError, never a 200 or 500; blocker reproductions answer 422 / exit 1 | integration | `make test PYTEST_ARGS="tests/test_solid.py tests/test_api.py tests/test_cli.py -q -n0 --no-cov"` | ✅ | ✅ green |
| 3-02-01 | 02 | 2 | THRD-01 | T-3-04, T-3-05 | >250 turns and a non-positive root radius are 422s naming both fields before any build | unit + API + CLI | `make test PYTEST_ARGS="tests/test_thread_maths.py tests/test_params.py tests/test_api.py tests/test_cli.py -q -n0 --no-cov"` | ✅ | ✅ green |
| 3-02-02 | 02 | 2 | THRD-01 | T-3-06 | info rows from the pinned profile only; standing warning first on API and CLI | unit + parity | `make test PYTEST_ARGS="tests/test_calc.py tests/test_api.py tests/test_cli.py tests/test_parity.py -q -n0 --no-cov"` | ✅ | ✅ green |
| 3-03-01 | 03 | 3 | THRD-01 | T-3-07 | over-budget fine STL on an L11 row refused before cache, slot and pool | unit + API | `make test PYTEST_ARGS="tests/test_thread_maths.py tests/test_api.py -q -n0 --no-cov"` | ✅ | ✅ green |
| 3-03-02 | 03 | 3 | THRD-01 | T-3-07 | the CLI refuses the same artefact (exit 2, no file); the info document warns | CLI + unit | `make test PYTEST_ARGS="tests/test_cli.py tests/test_calc.py -q -n0 --no-cov"` | ✅ | ✅ green |
| 3-04-01 | 04 | 4 | THRD-02 | T-3-09, T-3-10 | left_hand builds the hand asked for (isInside probe); a repeated or contradictory flag exits 2 | integration + parity | `make test PYTEST_ARGS="tests/test_params.py tests/test_solid.py tests/test_parity.py tests/test_api.py tests/test_cli.py -q -n0 --no-cov"` | ✅ | ✅ green |
| 3-04-02 | 04 | 4 | THRD-02 | T-3-09 | a repeated query key is a 422 duplicate before validation on every route | parity + API | `make test PYTEST_ARGS="tests/test_parity.py tests/test_api.py -q -n0 --no-cov"` | ✅ | ✅ green |
| 3-05-01 | 05 | 5 | THRD-02 | T-3-12 | checkbox from the schema; link round trip pinned as source text | source-text + human-check | `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"` | ✅ | ✅ green |
| 3-05-02 | 05 | 5 | THRD-02 | T-3-12, T-3-13 | foreign, repeated or unreadable hash key refused naming it, via textContent | source-text + human-check | `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"` | ✅ | ✅ green |
| 3-05-03 | 05 | 5 | THRD-02 | — | warnings of the mesh on screen survive a failed update | source-text + human-check | `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"` | ✅ | ✅ green |
| 3-06-01 | 06 | 6 | THRD-01, THRD-04 | — | the spike measures the shipped builder; the protocol guard holds | integration + bench smoke | `make test PYTEST_ARGS="tests/test_bench.py -q -n0 --no-cov"` and `.venv/bin/python -m bench.thread_spike smoke` | ✅ | ⚠️ flaky (tests green: 449 passed; the serial process exits 139 at teardown, docs/tech_debt/active/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md) |
| 3-06-02 | 06 | 6 | THRD-04 | T-3-14, T-3-15 | full 7160-row grid through the gate in a non-required workflow with read-only permissions | slow tier + governance | `make test PYTEST_ARGS="tests/test_grid.py tests/test_pr_land.py -q -n0 --no-cov"` and `make grid SIZE=M3.5` | ❌ creates tests/test_grid.py in-task | ✅ green |
| 3-07-01 | 07 | 7 | THRD-01, THRD-02, THRD-04 | T-3-16 | L12 cites run ids; docs describe the threaded rod | docs grep + gate | `make verify` | ✅ | ✅ green |
| 3-07-02 | 07 | 7 | THRD-04 | T-3-16 | INTERIM register carries the new knobs and D-18 costs; retired items name their shas | docs grep | `make verify` | ✅ | ✅ green |
| 3-07-03 | 07 | 7 | THRD-04 | — | coverage floor re-measured by L34's rule | measurement + gate | `make verify` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements: pytest, xdist, coverage and the import-linter
contracts are in place, and no task leaves a `MISSING` verify. The pre-commit hook runs `make verify` on
every commit, so a test cannot land red ahead of its code; each new test file is created in the task
whose behaviour it proves:

- [x] `tests/test_thread_maths.py` — created by plan 03-01 Task 2 (kernel-free maths, `volume_check`), extended by 03-02 Task 1 and 03-03 Task 1 (rules, L11 row table)
- [x] `tests/test_grid.py` — created by plan 03-06 Task 2 (the `grid`-marked corpus test plus unmarked governance tests)
- [x] `grid` marker registration and `-m 'not grid'` — plan 03-06 Task 2, same commit as the first marked test
- [x] Contract 8 edit (`screw.solid -> OCP`, `screw.solid.** -> OCP`) — plan 03-01 Task 1, same commit as the first OCP import in `screw.solid`
- [x] Coverage floor re-measured by spur L34's rule — plan 03-07 Task 3

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| The preview shows a helical thread; the `Left-hand thread` checkbox sits at its natural width, toggles a rebuild and the hand visibly reverses; the link round-trips `left_hand=true` | THRD-02 | No browser in the gate (L01); rendering and the checkbox's input event are invisible to source assertions | plan 03-05 Task 1 `<human-check>` |
| `#d=8&m=5`, `#d=1&d=2`, `#left_hand=banana`, `#d=abc` are each refused naming the key and build nothing | THRD-02 | `#d=abc` depends on HTML number-input sanitisation (the debt item's ASSUMPTION) | plan 03-05 Task 2 `<human-check>` |
| After a 422, a gate `build_error` or a network error, the last mesh, `Showing the last valid part` and that mesh's warnings are on screen together | THRD-02, THRD-04 | The interleaving of the info and STL fetches only shows in a running page | plan 03-05 Task 3 `<human-check>` |
| First CI run of `grid.yml` (15 jobs) after merge, wall time recorded in bench/RESULTS.md | THRD-04 | `workflow_dispatch` needs the workflow on the default branch | dispatch once the Phase 3 PR has landed; record it like the local shards |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify (17 of 17), each followed by its `<fails_when>`
- [x] Sampling continuity: every task commit runs `make verify` through the pre-commit hook
- [x] Wave 0 covers all MISSING references (none: no task carries a `MISSING` sentinel)
- [x] No watch-mode flags
- [x] Feedback latency < 90 s for the gate (the slow tier is outside it by design)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-10-10 by `/gsd-validate-phase 3` after execution: 17 of 17 tasks green under `make verify` (843 passed, coverage 97.02 % against the re-measured 96 floor); `tests/test_thread_maths.py` and `tests/test_grid.py` exist as planned; 3-06-01 flagged flaky for the serial exit-139 debt item; the four manual-only rows stay for the end-of-phase UAT.

## Validation Audit 2026-10-10

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
