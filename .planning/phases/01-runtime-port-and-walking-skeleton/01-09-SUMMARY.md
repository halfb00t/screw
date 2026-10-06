---
phase: 01-runtime-port-and-walking-skeleton
plan: 09
subsystem: infra
tags: [coverage, pytest-cov, pytest-xdist, import-linter, tech-debt, docs]

requires:
  - phase: 01-runtime-port-and-walking-skeleton
    provides: "the finished 285-test skeleton suite (01-01..01-08), pytest-cov 7.1.0 and pytest-xdist 3.8.0 (01-01), the D-02 interim-bounds item (01-01..01-06), bench/RESULTS.md (01-08)"
provides:
  - "[tool.coverage.run] and [tool.coverage.report] with fail_under = 94, measured by spur L34's rule on the skeleton suite"
  - "make test runs -n $(PYTEST_WORKERS) --cov --cov-report=term, so the floor gates make verify, the pre-commit hook, CI and make worktree.land"
  - "bench/RESULTS.md 'Coverage floor (Phase 1)': four totals, L, S, the floor, per-module cover, host and load"
  - "a D-02 item that lists every INTERIM-labelled knob in src/, Dockerfile and compose.yaml with value, file and source"
  - "overview.md as a real module map with the six import-linter contracts in force; AGENTS.md status line and HOW_TO_DEVELOP section 5 describe the skeleton"
affects: [phase-02, phase-04 (contracts 6 and 7), phase-05 (contract 9), phase-07 (OPER-01..03 re-sweep; re-measure the floor before moving it)]

actuals:
  tokens: 2600
  tasks: 2
  commits: 2
plan_head_before: c175f69968dc533a7bae94884d17285753938bcd
plan_head_after: d7541042d2a576d05c4a098a5aa7f85789012f23

tech-stack:
  added: []
  patterns:
    - "a coverage floor is a measured number: floor(L - max(0.25, S)) over one serial and three -n 8 totals, recorded with host and load, never a round number and never spur's 96"
    - "a verification command that greps the whole tree excludes the vendored bundle: it is a build artefact, not code we wrote"

key-files:
  created: []
  modified:
    - pyproject.toml
    - Makefile
    - .gitignore
    - bench/RESULTS.md
    - docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md
    - docs/architecture/overview.md
    - docs/HOW_TO_DEVELOP.md
    - AGENTS.md

key-decisions:
  - "fail_under = 94 = floor(95.03 - max(0.25, 0.00)): L is the serial total, S is zero because the three -n 8 totals are identical at 95.56"
  - "PYTEST_WORKERS stays 8, spur L34's knee, carried and labelled in the Makefile as not re-measured for screw's suite"

requirements-completed: [INFR-01, INFR-02]

coverage:
  - id: D1
    description: "make test enforces a coverage floor of 94 %, measured by spur L34's rule on the finished skeleton suite and recorded in bench/RESULTS.md"
    requirement: INFR-01
    verification:
      - kind: other
        ref: "make test (exit 0, 'Required test coverage of 94.0% reached. Total coverage: 95.56%')"
        status: pass
      - kind: other
        ref: "make test PYTEST_ARGS=--cov-fail-under=100 (exit 2, 'FAIL Required test coverage of 100% not reached. Total coverage: 95.56%')"
        status: pass
    human_judgment: false
  - id: D2
    description: "every INTERIM label in src/, Dockerfile, compose.yaml and app.js has a row in the D-02 debt item"
    requirement: INFR-01
    verification:
      - kind: other
        ref: "the plan's D-02 audit, run with the vendored bundle excluded: 'missing: none'"
        status: pass
    human_judgment: false
  - id: D3
    description: "overview.md maps the real modules and names the six contracts in force; AGENTS.md and HOW_TO_DEVELOP.md no longer describe an empty tree or an in-image test target"
    requirement: INFR-02
    verification:
      - kind: other
        ref: "make verify (Contracts: 6 kept, 0 broken); grep acceptance criteria in 01-09-PLAN.md Task 2"
        status: pass
    human_judgment: true
    rationale: "Whether the prose is an accurate and useful map is a reading judgment; the gate checks only that the named contracts are kept and the phrases exist."

duration: 8min
completed: 2026-10-06
status: complete
---

# Phase 1 Plan 09: Coverage floor and standing docs Summary

**A measured 94 % coverage floor (floor(95.03 - 0.25)) now gates `make test` under xdist, every INTERIM knob is inventoried for Phase 7, and the overview, AGENTS.md and HOW_TO_DEVELOP describe the walking skeleton.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-10-06T06:00:00Z (approximate; first command read `uptime` at 12:01 local)
- **Completed:** 2026-10-06T06:09:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Coverage config (`branch`, `source = ["src/screw"]`, `concurrency = ["multiprocessing", "thread"]`, `parallel`, `sigterm`, `precision = 2`) carried from spur with its reasons, and `fail_under = 94` set from a measurement on this phase's finished suite.
- `make test` is `pytest -n $(PYTEST_WORKERS) --cov --cov-report=term`; `PYTEST_WORKERS` is 8 clamped to the host's CPUs, labelled as spur's knee and not re-measured.
- The D-02 inventory is complete: the audit found no knob without a row; the item gained the missing related files (cli.py, Dockerfile, compose.yaml, app.js), refreshed line numbers, the probe's inner 1 s `urlopen` timeout and compose's `SCREW_BUILD_WORKERS`.
- Standing docs updated: module table and the six contracts (numbered as the code comments cite them: 1-5 and 8) in overview.md, the walking-skeleton status line in AGENTS.md, the dropped in-image test clause in HOW_TO_DEVELOP section 5.

## Coverage measurement (command, date, figures)

Measured 2026-10-06 on Apple M2 Max, 12 CPUs, 32 GiB, macOS Darwin 27.0.0, Python 3.12.13, pytest-cov 7.1.0, pytest-xdist 3.8.0, 285 tests, host not idle (`uptime` load averages 3.09/2.72/2.56 before the serial run, 2.59/2.63/2.53, 2.67/2.64/2.54 and 3.21/2.77/2.59 before the three `-n 8` runs).

| Run | Command | TOTAL | Wall |
|---|---|---|---|
| serial | `.venv/bin/python -m pytest -n0 --cov --cov-report=term --cov-fail-under=0` | 95.03 % | 34.28 s |
| -n 8 (1) | `.venv/bin/python -m pytest -n 8 --cov --cov-report=term --cov-fail-under=0` | 95.56 % | 16.90 s |
| -n 8 (2) | same | 95.56 % | 16.92 s |
| -n 8 (3) | same | 95.56 % | 16.97 s |

L = 95.03, S = 0.00, floor = floor(95.03 - max(0.25, 0.00)) = floor(94.78) = **94**.

Per-module (identical serial and `-n 8` except `pool.py`): `__init__` 71.43, `__main__` 0.00, `app` 96.83, `build_errors` 100.00, `calc/__init__` 100.00, `cli` 95.88, `params` 96.00, `pool` 95.31 serial / 100.00 at `-n 8`, `records` 94.03, `solid/__init__` 91.30, `solid/bolt` 100.00 (percent). The 0.53 serial gap is exactly `pool.py`'s 3 lines (spur's Pitfall 13); its cause was not isolated.

Negative control, `make test PYTEST_ARGS=--cov-fail-under=100`, exit 2:

```
FAIL Required test coverage of 100% not reached. Total coverage: 95.56%
```

Coverage and xdist interplay: pass/fail was unchanged (285 passed in all five runs), and the suite under `-n 8 --cov` takes about 17 s against 34 s serial. A fourth `-n 8` run was taken only to read the per-module column; it read the same 95.56 %.

## Task Commits

1. **Task 1: Coverage floor measured on the finished skeleton suite and enforced by make test** - `5fb4e3d` (build)
2. **Task 2: Interim-bounds inventory complete, standing docs describe the skeleton** - `d754104` (docs)

**Plan metadata:** the `docs(01-09)` commit that follows this file.

## Files Created/Modified

- `pyproject.toml` - `[tool.coverage.run]`, `[tool.coverage.report]` with `fail_under = 94` and the formula comment
- `Makefile` - `PYTEST_WORKERS` with the clamp, `test` with `-n` and `--cov`
- `.gitignore` - `.coverage`, `.coverage.*`
- `bench/RESULTS.md` - "Coverage floor (Phase 1)"
- `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` - complete related files, two rows completed
- `docs/architecture/overview.md` - module table, six contracts, dependency-closure line
- `docs/HOW_TO_DEVELOP.md` - section 5 trap, no in-image test target
- `AGENTS.md` - status line only

## Decisions Made

- The floor is 94, the plan's formula applied literally; the serial run sets L, so a clean xdist machine reads 1.56 above it.
- `PYTEST_WORKERS` 8 is carried from spur and not re-measured; it changes gate speed, not any printed number.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The plan's D-02 audit command matches the vendored bundle**
- **Found during:** Task 2 (audit of INTERIM knobs)
- **Issue:** `git grep -h -o -E ... -e '350' -- src ...` also hits the minified `src/screw/static/vendor/three.bundle.min.js`, whose "Binary file ... matches" output made the second audit command report `Binary`, a path and `matches` as missing knobs and exit non-zero, although nothing was missing.
- **Fix:** Ran the same audit with `':!src/screw/static/vendor'` added to the pathspec, the same exclusion `make no-fake-done` uses; it reports `missing: none`. The bundle is a build artefact, not a knob.
- **Files modified:** none (a verification-command change only)
- **Verification:** `missing: none`, exit 0; `make verify` and `make check` exit 0.

---

**Total deviations:** 1 auto-fixed (1 blocking, in the plan's own verify command)
**Impact on plan:** None on shipped files. If the audit is ever re-run from the plan text, add the vendor exclusion.

## Issues Encountered

- The pre-commit hook stashes and restores unstaged files around each commit; the orchestrator-owned `.planning/config.json`, `milestone.lock` and `state.json` were restored intact after both task commits.

## Known Stubs

None.

## Threat Flags

None. No new endpoint, auth path, file access or schema at a trust boundary.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 1's port is complete: `make verify` (285 passed, `Contracts: 6 kept, 0 broken`, coverage 95.56 % against a floor of 94) and `make check` (smoke line `smoke: kernel, exports, ASGI stack and validation all live`, no diff under `src/screw/static/vendor`) both exit 0.
- Re-measure the floor the same way whenever a phase adds a large untested module, before moving it. Modules with the most headroom to lose: `solid/__init__.py` (91.30 %), `records.py` (94.03 %).
- Filed this plan: no new debt item (the pool.py serial gap is spur's existing nice-severity item and was not chased, per the plan).

## Self-Check: PASSED

- `5fb4e3d` and `d754104` are ancestors of HEAD; `git rev-list --count c175f69..d754104` read 2.
- `pyproject.toml` has `fail_under = 94`, `precision = 2` and the concurrency line; `Makefile` has the `-n $(PYTEST_WORKERS) --cov --cov-report=term` line; `.gitignore` has `.coverage`; `bench/RESULTS.md` has "Coverage floor (Phase 1)" with four totals.

---
*Phase: 01-runtime-port-and-walking-skeleton*
*Completed: 2026-10-06*
