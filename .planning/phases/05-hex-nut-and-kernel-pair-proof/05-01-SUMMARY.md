---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 01
subsystem: testing
tags: [pre-registration, pair-proof, m18, cadquery, expected-verdicts, import-linter]

requires:
  - phase: 02-thread-spike
    provides: the recorded pair campaign 2026-10-08-a-pair, the unmodified cell_verdict rule, bench.thread_spike.pair bodies
provides:
  - bench/pair_expected.py and tests/data/pair_expected.tsv, the 240 expected K = 3 pair verdicts derived from the record (88 proven, 92 inconclusive, 60 violated)
  - tests/test_pair.py with the re-derivation test, the L11 excluded-clearance pin and the M18 pins, all in make verify
  - 05-M18-DIAGNOSIS.md, the D-08 protocol (36 readings, 130 s deadline) written before any reading
  - bench/m18_probe.py, the probe that reads exactly that protocol and refuses to run until it is byte-identical on origin/main
  - PR A (number 17), open against main, branch gsd/phase-05-preregistration
affects: [05-03 lands PR A, 05-14 pair tier compares the kernel against the table, M18 diagnosis run, L14 decision entry]

actuals:
  tokens: 9473
  tasks: 3
  commits: 2
plan_head_before: 0ef52e8f38a711813b1982cabaf93332d9d5cde6
plan_head_after: b7cf17b05edfccf01d757a85b20e19ae7ff77bc6

tech-stack:
  added: []
  patterns:
    - "expected verdicts are derived by a script from the recorded campaign and re-derived by a test, never typed"
    - "a kernel probe keeps the kernel import inside the child-side function so the parent stays kernel-free"
    - "run guard compares the local protocol with origin/main byte for byte and fails closed"

key-files:
  created:
    - bench/pair_expected.py
    - tests/data/pair_expected.tsv
    - tests/test_pair.py
    - bench/m18_probe.py
    - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-M18-DIAGNOSIS.md
  modified:
    - pyproject.toml

key-decisions:
  - "PR A is number 17 (gsd/phase-05-preregistration, cut from origin/main 0ef52e8); plan 05-03 has the other CLI review it and lands it before any Phase 5 pair run or probe reading"
  - "The probe's deadline is 130 s per reading: 4 x 30.964 s (slowest recorded M18 boolean) rounded up to 10 s; IN-02's 600 s is a whole-cell figure and is not reused"
  - "The closed form the protocol states for the harness controls is 336.6316 mm3 (verdict.closed_control of the M18 c = 0.10 cell)"

patterns-established:
  - "Pre-registration PR: derivation script + frozen table + re-derivation test + independent literal pin, on a branch cut from origin/main in a separate worktree"

requirements-completed: [PAIR-03, PAIR-04]

coverage:
  - id: D1
    description: "Expected pair verdicts derived from 2026-10-08-a-pair by the unmodified cell_verdict, with a sha256-pinned record and a byte-for-byte re-derivation test"
    requirement: "PAIR-03"
    verification:
      - kind: unit
        ref: "tests/test_pair.py#test_the_expected_verdicts_are_re_derived_from_the_recorded_pair_campaign"
        status: pass
      - kind: unit
        ref: "tests/test_pair.py#test_the_expected_table_counts_the_recorded_k_3_cells"
        status: pass
      - kind: unit
        ref: "tests/test_pair.py#test_a_record_that_is_not_the_one_l11_cites_is_refused"
        status: pass
    human_judgment: false
  - id: D2
    description: "L11's excluded clearances per size and hand, and M18 inconclusive on both hands at every proof clearance, pinned independently of the derivation"
    requirement: "PAIR-03"
    verification:
      - kind: unit
        ref: "tests/test_pair.py#test_the_excluded_clearances_are_the_ones_l11_records"
        status: pass
      - kind: unit
        ref: "tests/test_pair.py#test_m18_is_inconclusive_on_both_hands_at_every_proof_clearance"
        status: pass
    human_judgment: false
  - id: D3
    description: "M18 diagnosis protocol (Question, Environment, Method, Predictions, Escape clause, Results) and a probe that reads exactly its 36 readings and refuses until the protocol is on origin/main"
    requirement: "PAIR-04"
    verification:
      - kind: unit
        ref: "tests/test_pair.py#test_the_m18_probe_reads_exactly_the_36_pre_registered_readings"
        status: pass
      - kind: unit
        ref: "tests/test_pair.py#test_the_m18_probe_refuses_to_run_until_its_protocol_is_on_main"
        status: pass
      - kind: unit
        ref: "tests/test_pair.py#test_the_protocol_states_the_numbers_the_probe_reads"
        status: pass
    human_judgment: false
  - id: D4
    description: "PR A is open against main with a Conventional title and no skip token; the pre-registration is not yet on main, so the order claim (SC3, SC6) is only complete once plan 05-03 lands it"
    requirement: "PAIR-03"
    verification:
      - kind: other
        ref: "gh pr view gsd/phase-05-preregistration --json state,baseRefName -> OPEN main"
        status: pass
    human_judgment: true
    rationale: "Whether the expectations and the diagnosis method predate the data on main is only checkable after PR A lands; the review by the other CLI (plan 05-03) is a human-gated step."

duration: 15min
completed: 2026-10-14
status: complete
---

# Phase 5 Plan 01: Pre-register the pair verdicts and the M18 diagnosis Summary

**The expected verdict of all 240 recorded K = 3 pair cells (88 proven, 92 inconclusive, 60 violated) is derived by script from `2026-10-08-a-pair` and pinned by a re-derivation test, and the 36-reading M18 control diagnosis is written down with its probe, both on open PR #17 before any Phase 5 kernel run exists.**

## Performance

- **Duration:** about 15 min wall (start time was not captured at launch; estimated from the first command)
- **Started:** 2026-10-14 (about 11:38 UTC)
- **Completed:** 2026-10-14T11:54Z
- **Tasks:** 3
- **Files:** 6 changed on the pre-registration branch (762 insertions), plus this SUMMARY on the phase branch

## Accomplishments

- `bench/pair_expected.py` derives every K = 3 cell of the record with the unmodified `cell_verdict`, refuses any file whose sha256 is not `1644650e...84d9f3`, and writes `tests/data/pair_expected.tsv` (241 lines). Counts: same-hand proof cells 88 proven and 32 inconclusive, diagnostic cells (c = 0 and -0.05) 60 inconclusive, mixed-hand cells 60 violated. The module joined the spike's kernel-free import contract (`make lint-imports`: 9 kept, 0 broken).
- `tests/test_pair.py` carries ten kernel-free tests: the byte-for-byte re-derivation, the counts, L11's excluded clearances per size and hand from an independent literal, M18 inconclusive on both hands at every proof clearance, the refused record, the product K, and four probe tests.
- `05-M18-DIAGNOSIS.md` fixes the Question, Environment, Method, Predictions and Escape clause before any reading: P1 five repeats per hand, P2 eight pose offsets per hand, P3 the c = -0.05 pose, P4a fuzzy 1e-4 mm, P4b swapped operands, H four harness controls (36 total), a 130 s deadline, and the sentence that no rule, pose, constant or body changes whatever the result.
- `bench/m18_probe.py` holds the reading list as a tuple built from named constants, runs each reading in a fresh child, ends the child with `os._exit(0)` (RESEARCH F5), and refuses with exit 2 when origin/main's protocol is missing or differs. It was exercised only on its refusal path (no reading ran, `bench/results/phase-05` does not exist).
- PR A: https://github.com/halfb00t/screw/pull/17, `OPEN main`, title "Pre-register the Phase 5 kernel runs: expected pair verdicts and the M18 diagnosis", no skip token (checked with `scripts.skip_tokens.find_skip_tokens`), nothing under `src/` changed.

## Task Commits

All on branch `gsd/phase-05-preregistration` in the worktree `.claude/worktrees/phase-05-preregistration`, cut from origin/main `0ef52e8` (the pre-commit hook ran `make verify` on each):

1. **Task 1: expected pair verdicts** - `a7a5b39` (test)
2. **Task 2: M18 protocol and probe** - `b7cf17b` (docs)
3. **Task 3: PR A** - no commit; branch pushed, PR #17 opened

**Plan metadata:** the commit that adds this SUMMARY, STATE.md and ROADMAP.md on `gsd/phase-05-hex-nut-and-kernel-pair-proof` in the main checkout.

`commits: 2` is measured on the pre-registration branch (`git rev-list --count 0ef52e8..gsd/phase-05-preregistration`), because the plan's two code commits live there by design (D-08). The per-plan ledger sits in the worktree's git dir, not the main checkout's.

## For plan 05-03

- **PR A number: 17.** Branch `gsd/phase-05-preregistration`, worktree `.claude/worktrees/phase-05-preregistration` (left in place, its own `.venv` built there).
- Verification evidence in the worktree: `make verify` exit 0 twice (2643 passed after Task 1, 2647 after Task 2, coverage 97.57 % against the 96 floor).
- The table's counts and file set are readable from the main checkout through `git show gsd/phase-05-preregistration:tests/data/pair_expected.tsv` and `git diff --name-only origin/main...gsd/phase-05-preregistration` (exactly the six files).
- Reviewer attention list is in the PR body: typed verdicts, inputs chosen to favour a pass, probe readings absent from the protocol, the guard's teeth.

## Decisions Made

- The deadline of 130 s is derived, not chosen: 4 x 30.964 s rounded up to a multiple of 10 s (`bench.m18_probe.deadline_from_record` recomputes it from the record and a test pins it equal to `DEADLINE_S`).
- The harness-control closed form is stated in the protocol as 336.6316 mm3 and a test recomputes it with `verdict.closed_control`.
- `pair._KEEP` is used exactly as `pair.common` does; `pair.py` itself is untouched (no body changes).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] The probe fetches origin/main and refuses to overwrite its output**
- **Found during:** Task 2
- **Issue:** `git show origin/main:<protocol>` against a stale local ref could pass or fail on old text, and a second run would overwrite the first run's JSONL, which the protocol forbids ("no reading is retried").
- **Fix:** `main()` runs `git fetch --quiet origin main` first and treats a failed fetch as "not on main" (fail closed); the output file is opened with mode `"x"` after an explicit existence refusal (exit 2).
- **Files modified:** `bench/m18_probe.py`
- **Commit:** `b7cf17b`

**2. [Rule 3 - Blocking/robustness] Paths anchored on the repository root, kernel import deferred**
- **Found during:** Tasks 1 and 2
- **Issue:** The plan wrote `RECORD`, `TABLE` and `PROTOCOL` as bare relative `Path`s, which break when the cwd is not the repo root; and importing `bench.thread_spike.pair` at module top would make every test that imports the probe load the kernel (about 4 s, plus the exit 139 hazard).
- **Fix:** `ROOT = Path(__file__).resolve().parents[1]` anchors the constants; `bench/m18_probe.py` imports `cadquery`, `OCP` and `bench.thread_spike.pair` inside `read_one`, which only the child processes call. `pair.rod_piece(`, `pair.nut(`, `pair.place(` and `pair._KEEP` are still the calls the key link names. The module stays outside the kernel-free contract as the plan said.
- **Files modified:** `bench/pair_expected.py`, `bench/m18_probe.py`
- **Commits:** `a7a5b39`, `b7cf17b`

**3. [Process note, not a code deviation] Pre-commit branch assertion**
- The executor protocol's worktree allow-list (`agent-*` branch names) was not applied to the commits on `gsd/phase-05-preregistration`: that branch and its worktree are the plan's explicit design (D-08), and the orchestrator's project-root pin says so. The protected-branch refusal (main, master, develop, trunk, release/*) and the cwd-drift sentinel were applied before each commit; the branch is not protected and the worktree toplevel matched the sentinel.

**Total deviations:** 2 auto-fixed (1 Rule 2, 1 Rule 3), 1 process note. **Impact:** none on any pre-registered value; both fixes tighten the guard or the paths.

## TDD note (Task 1)

The test file was written first and run before `bench/pair_expected.py` existed: collection failed with `ImportError: cannot import name 'pair_expected'` (one error, no test ran). That is not a valid RED by the gate's definition (an import error, not an assertion), and it was not committed; `workflow.tdd_mode` is false and the project's pre-commit gate cannot take a failing suite. The GREEN evidence is the six Task 1 tests passing against the table the module generated, and the table is pinned by the byte-for-byte re-derivation test. No `test(05-01)`/`feat(05-01)` gate commits exist; the plan's commit subjects are the ones its `<automated>` checks name.

## Issues Encountered

- The first `tests/test_pair.py` run on the fresh worktree venv took 117 s (6 tests); later runs took about 14 s. The cause is the cold start of a new venv, not the tests (no kernel is called); not investigated further.
- `make venv` in the worktree installed about 1.4 GB, as the plan said.

## Known Stubs

None.

## Threat Flags

None. T-05-01 (tampering with the expected table), T-05-02 (protocol written after data) and T-05-03 (skip token in PR text) are mitigated as the plan's register says: the table is script-written, sha256-pinned and re-derived by a test; the probe's guard fails closed; the PR text was checked with `find_skip_tokens`.

## Next Phase Readiness

PR A is open and awaits plan 05-03 (other-CLI review, then `make pr.land`). Nothing in Phase 5 may run a pair cell against the table or any probe reading before PR #17 is on main. The main checkout is on `gsd/phase-05-hex-nut-and-kernel-pair-proof` with a clean tree apart from this plan's metadata commit.

## Self-Check: PASSED

- Files present on `gsd/phase-05-preregistration` (checked with `git show`): `bench/pair_expected.py`, `tests/data/pair_expected.tsv`, `tests/test_pair.py`, `bench/m18_probe.py`, `05-M18-DIAGNOSIS.md`, `pyproject.toml` change.
- Commits `a7a5b39` and `b7cf17b` are ancestors of `gsd/phase-05-preregistration` and `origin/main` is an ancestor of both.
- All three tasks' `<automated>` checks exit 0 from the main checkout; the plan-level verification (six-file diff, 88 / 92 / 60 table, PR open against main, main checkout on the phase branch) holds.
