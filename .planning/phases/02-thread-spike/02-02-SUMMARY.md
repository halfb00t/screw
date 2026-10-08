---
phase: 02-thread-spike
plan: 02
subsystem: testing
tags: [thread-spike, sewn-twist, closed-form-oracle, quiet-gate, worker-subprocess, import-linter, pre-registration-guard]

requires:
  - phase: 02-thread-spike
    provides: 02-SPIKE.md protocol with the owner's pinned basic profile and coefficients (plan 02-01)
provides:
  - bench/quiet.py wait_quiet gate with injected effects and UTC-labelled readings
  - bench/thread_spike package - kernel-free maths/verdict/runner/__main__, kernel-side helical/measure/worker
  - smoke subcommand - one M6 right-hand 5-turn sewn rod end to end, exit 0 only when the row is ok
  - check-protocol subcommand and protocol_guard predicate - exit 2 until the protocol is on origin/main
  - seventh import-linter contract keeping the oracle, verdict and parent process kernel-free
  - make bench.thread target
affects: [02-03 grid and records, 02-04 constructions, 02-05 pair check, 02-06 protocol write-up, 02-07 campaign, 02-08 verdict, Phase 3 builder promotion]

actuals:
  tokens: 19800
  tasks: 2
  commits: 4
plan_head_before: 2923d489ffba15c24bad5e2de29b5be6e2c14dc9
plan_head_after: f611dd05173be2544e6b2e90785298359ca21932

tech-stack:
  added: []
  patterns:
    - "Process split: kernel only in a persistent JSON-lines worker child; oracle, verdict and parent are kernel-free and held so by an import-linter contract"
    - "Pure predicate with git output injected (protocol_guard), wired to real git by a thin caller, tested both ways"
    - "Quiet gate as a pure function with injected read/sleep/now/clock"
    - "A row that was not built carries None in every measurement field, never a zero"

key-files:
  created:
    - bench/quiet.py
    - bench/thread_spike/__init__.py
    - bench/thread_spike/maths.py
    - bench/thread_spike/helical.py
    - bench/thread_spike/measure.py
    - bench/thread_spike/worker.py
    - bench/thread_spike/verdict.py
    - bench/thread_spike/runner.py
    - bench/thread_spike/__main__.py
  modified:
    - pyproject.toml
    - Makefile
    - tests/test_bench.py

key-decisions:
  - "Non-finite numbers (NaN, Infinity) are refused at the wire boundary: json.loads accepts them and a NaN volume would compare as not outside the tolerance and read as ok"
  - "A worker that speaks unparseable output is one failure row and is killed, not reused; a line cut short by the child dying is worker_died"
  - "An STL with zero triangles is not watertight: an empty mesh proves nothing"
  - "The smoke header's guard line is computed without fetching, so it always carries the 'not fetched' reason beside the real ones; it is informational and smoke never enforces it"

patterns-established:
  - "Refusals at the wire boundary are one exception type (ValueError naming the key), raised through one NoReturn helper rather than per-site suppressions"
  - "No-fake-done words stay out of code; stubs for a RED commit use their arguments and return a wrong-but-typed value"

requirements-completed: [INFR-03]

coverage:
  - id: D1
    description: "smoke builds one M6 right-hand 5-turn sewn rod (K=5) in a worker subprocess, checks it against the closed form, prints a report whose load readings carry their UTC time, says it is not a campaign run, exits 0 only when the row is ok"
    requirement: INFR-03
    verification:
      - kind: other
        ref: ".venv/bin/python -m bench.thread_spike smoke (exit 0, Class ok, precise rel err +1.694e-06, two readings with 'read 2026-10-06T...', 'not a campaign run')"
        status: pass
      - kind: integration
        ref: "tests/test_bench.py#test_a_worker_round_trip_returns_one_record_per_request_and_survives_a_bad_rod"
        status: pass
    human_judgment: false
  - id: D2
    description: "Row verdict: silent_wrong on solids != 1, invalid, |precise rel err| > T_PASS (sign kept, exact boundary), or a checked mesh that is open, inside out or off the closed form; failure/timeout/worker_died keep their class with null measurements"
    requirement: INFR-03
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_the_tolerance_boundary_is_exact_to_the_next_representable_volume"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_an_inverted_solid_is_silent_wrong_by_its_sign"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_a_row_that_was_not_built_keeps_its_class_and_carries_no_measurement"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_a_real_m6_right_hand_five_turn_rod_passes_the_row_verdict"
        status: pass
    human_judgment: false
  - id: D3
    description: "Worker isolation: a dead child (exit code, signal -11), a timeout and garbage output are each one recorded row and the parent survives"
    requirement: INFR-03
    verification:
      - kind: integration
        ref: "tests/test_bench.py#test_a_worker_that_dies_is_one_worker_died_row_with_its_return_code"
        status: pass
      - kind: integration
        ref: "tests/test_bench.py#test_a_worker_killed_by_a_signal_reports_the_negative_return_code"
        status: pass
      - kind: integration
        ref: "tests/test_bench.py#test_a_worker_that_does_not_answer_in_time_is_killed_and_recorded_as_a_timeout"
        status: pass
    human_judgment: false
  - id: D4
    description: "wait_quiet releases only after three consecutive readings strictly under 1.5; exact 1.5 resets, nextafter(1.5, 0) counts; a host that never quiets is non-decisive with 31 readings; every reading carries its UTC time"
    requirement: INFR-03
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_a_reading_of_exactly_the_bar_resets_the_run_of_quiet_readings"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_a_host_that_never_quiets_is_non_decisive_after_the_cap_with_31_readings"
        status: pass
    human_judgment: false
  - id: D5
    description: "The guard: check-protocol exits 2 printing 'protocol guard: refused' while origin/main has no protocol; protocol_guard holds only when fetched, texts equal before '## Results' and origin/main's protocol commit is an ancestor of HEAD, and names every failed check"
    requirement: INFR-03
    verification:
      - kind: other
        ref: ".venv/bin/python -m bench.thread_spike check-protocol (exit 2, 'protocol guard: refused -- origin/main has no protocol file ...')"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_the_guard_names_every_reason_not_only_the_first"
        status: pass
      - kind: integration
        ref: "tests/test_bench.py#test_the_guard_refuses_a_branch_cut_before_the_protocol_landed"
        status: pass
    human_judgment: false
  - id: D6
    description: "Import-linter contract: bench.thread_spike.maths, .verdict, .runner, .__main__ and bench.quiet reach cadquery/OCP by no path; the six older contracts stay KEPT with root_packages = [screw, bench]"
    requirement: INFR-03
    verification:
      - kind: other
        ref: "make lint-imports (Contracts: 7 kept, 0 broken.)"
        status: pass
    human_judgment: false
  - id: D7
    description: "Faithfulness of the kernel-side port and of the closed form to the owner-pinned basic profile (crest P/8, root P/4, depth 5H/8)"
    requirement: INFR-03
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_the_closed_form_section_area_is_half_the_integral_of_the_radius_squared"
        status: pass
    human_judgment: true
    rationale: "The coefficients are the owner's, read from ISO 68-1:2023 by the owner and not independently re-read by anyone here; the tests prove internal consistency (area equals the integral of the radius, kernel volume within 1.7e-6), not agreement with the standard"

duration: 17min
completed: 2026-10-06
status: complete
---

# Phase 2 Plan 02: Tracer rod row and the pre-registration guard Summary

**One M6 right-hand sewn-twist rod runs through quiet gate, worker subprocess, kernel-free closed form, classification and report (precise volume within 1.7e-6 of the closed form), and `check-protocol` refuses every campaign run until the protocol is on origin/main.**

## Performance

- **Duration:** 17 min
- **Started:** 2026-10-06T11:52:25Z
- **Completed:** 2026-10-06T12:09:38Z
- **Tasks:** 2 (Task 1 tracer, Task 2 TDD)
- **Files modified:** 12 (9 created, 3 modified)

## Accomplishments

- The process split is proven on a real row: the kernel lives only in the worker child, while the closed form, the verdict, the quiet gate and the report run in a parent that an import-linter contract keeps free of cadquery and OCP (7 contracts kept, 0 broken).
- `smoke` on this host: class `ok`, 1 solid, valid, precise rel err +1.694e-06 and default rel err +1.504e-05 against the closed form, 7866 preview triangles, watertight, build 0.02 s. Load readings printed with their UTC time at start and end; the end one is labelled as including the run's own load. Host load was 6.99 to 23.50 during runs, so these timings are indicative of nothing (not a bound, not a campaign run).
- Every failure mode of the child is one recorded row with null measurements: exit code (`worker_died`, including signal -11), no answer in time (`timeout`, child killed and respawned), unparseable output (`failure`). A kernel failure on d = 1e-9 reads `failure: Standard_Failure: BRepOffsetAPI_MakePipeShell::MakeSolid` and the same child serves the next request.
- The guard is a tested pure predicate wired to real git. On this unlanded branch `check-protocol` exits 2 with "origin/main has no protocol file: the protocol PR has not landed; origin/main's protocol commit is not an ancestor of HEAD". It will hold only after PR 1 lands.

## Task Commits

1. **Task 1: One rod row end to end (tracer)** - `90d2834` (feat)
2. **Task 2 RED: failing guard tests** - `7f3cc98` (test)
3. **Task 2 GREEN: the pre-registration guard** - `92a6662` (feat)
4. **Fix to Task 2's real-git tests (found at close-out)** - `f611dd0` (fix)

**Plan metadata:** recorded in the commit that follows this file (docs: complete plan)

Tracer feedback gate (end-of-phase mode, automated-only verify): `smoke` re-run after the Task 1 commit passed end to end (exit 0, Class ok); logged "Tracer verified end-to-end - expanding" and continued to Task 2.

## TDD Gate Compliance

- **RED:** `7f3cc98` adds 11 guard tests. They fail 11 of 11 on their assertions against behaviourless stubs (`protocol_guard` returns held=False with no reasons; `before_results` returns the whole text), e.g. `assert (False, ()) == (True, ())`. Evidence run with `--runxfail` and JUnit XML, classifier verdict `RED_EVIDENCE_OK` (reason `target_test_failed`, target `test_the_guard_holds_when_the_protocol_is_on_main_unchanged_and_an_ancestor`). Semantic assessment: the target executed and failed on the planned assertion, not on import or fixture; the stub exists only so the module imports.
- **GREEN:** `92a6662` implements `before_results` and `protocol_guard`, removes the xfail markers, adds `check-protocol`; 11 of 11 pass, plus 4 real-git tests.
- **REFACTOR:** none needed, no commit.

## Files Created/Modified

- `bench/quiet.py` - `wait_quiet`, `read_now`, `Reading`, `QuietResult`; spur D-05's constants with their source
- `bench/thread_spike/__init__.py` - package docstring with the kernel-free / kernel module map
- `bench/thread_spike/maths.py` - exact-fraction `PITCH` for 15 sizes (UNVERIFIED), `INTERIM_PRESETS`, `section_radius`, `section_area`, `closed_volume` for the pinned basic profile
- `bench/thread_spike/helical.py` - sewn K-turn twist builder ported from STACK, `turns` used exactly as given
- `bench/thread_spike/measure.py` - precise and default volume, `mesh_stl` on a copy, stdlib `stl_check` (weld, directed-edge pairing, signed volume, area)
- `bench/thread_spike/worker.py` - the JSON-lines kernel child, `os._exit(0)` at EOF
- `bench/thread_spike/verdict.py` - wire shapes, strict parsers, `classify_row`, `failed_record`, `before_results`, `protocol_guard`
- `bench/thread_spike/runner.py` - `Worker` with a hard deadline, kill and respawn
- `bench/thread_spike/__main__.py` - `smoke` and `check-protocol`, `read_guard`, `_git`
- `pyproject.toml` - `root_packages = ["screw", "bench"]` and the seventh contract
- `Makefile` - `ARGS`, `bench.thread`
- `tests/test_bench.py` - 40 new tests (68 in the file, 343 in the suite)

## Decisions Made

- Non-finite JSON numbers are refused at the wire boundary (see key-decisions); unparseable child output kills the child.
- Refusals at the wire boundary all go through one `NoReturn` helper that raises `ValueError` naming the key, so the plan's "ValueError naming the offending key" holds without scattering lint suppressions (ruff TRY004 would otherwise demand `TypeError` for wrong types).
- The unknown-row-kind check sits before the `try` in the worker so a bad kind is a `failure` record without raising inside the guarded block.
- The real-git guard tests monkeypatch `_REPO_ROOT` to a throwaway clone of a throwaway origin; git itself is not mocked.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] RED commit made of strict-xfail tests over stubs**
- **Found during:** Task 2 (RED)
- **Issue:** the pre-commit hook runs `make verify` including pytest, and `--no-verify` is forbidden, so a commit of genuinely failing tests cannot land. Tests that import symbols that do not exist would fail collection for the whole file, which is `INVALID_RED`, not RED.
- **Fix:** added `protocol_guard` / `before_results` as behaviourless stubs (they use their arguments to satisfy ruff ARG001 and return a wrong typed value) and marked the 11 target tests `xfail(strict=True)`. RED evidence came from a `--runxfail` run. The GREEN commit removed the markers; a strict xfail that starts passing fails the gate, so the markers could not be forgotten.
- **Files modified:** `bench/thread_spike/verdict.py`, `tests/test_bench.py`
- **Verification:** classifier `RED_EVIDENCE_OK`; `make verify` green on both commits.
- **Committed in:** `7f3cc98`, `92a6662`

**2. [Rule 2 - Missing critical] Non-finite numbers refused at the wire boundary**
- **Found during:** Task 1 (`verdict.parse_record`)
- **Issue:** `json.loads` accepts `NaN`; `abs(nan) > T_PASS` is False, so a NaN precise volume would classify `ok`, a plausible wrong verdict (L02).
- **Fix:** `_num` refuses non-finite values naming the key; tested.
- **Files modified:** `bench/thread_spike/verdict.py`, `tests/test_bench.py`
- **Committed in:** `90d2834`

**3. [Rule 2 - Missing critical] Empty STL is not watertight; mesh check fields tied to `checked`**
- **Found during:** Task 1 (`measure.stl_check`, `verdict._mesh`)
- **Issue:** a zero-triangle mesh has no open edges, so it would read watertight; and a mesh record could claim `checked` with null check fields or the reverse.
- **Fix:** `watertight` requires triangles > 0; `parse_record` refuses a mesh whose check fields are not set exactly when `checked` is true.
- **Files modified:** `bench/thread_spike/measure.py`, `bench/thread_spike/verdict.py`, `tests/test_bench.py`
- **Committed in:** `90d2834`

**4. [Rule 2 - Missing critical] Tests of the guard's git wiring**
- **Found during:** Task 2 (GREEN)
- **Issue:** the plan's tests cover the predicate on injected texts only; `read_guard` and `check_protocol` (fetch, show, log, merge-base, exit 2) had no test, and CLAUDE.md requires new behaviour to ship with its tests.
- **Fix:** four real-git tests against a throwaway origin: refused before landing, held after, refused for a branch cut before the landing (ancestor reason only), refused for an edit before `## Results` and allowed after it.
- **Files modified:** `tests/test_bench.py`
- **Committed in:** `92a6662`

---

**5. [Rule 1 - Bug] Real-git guard tests inherited the hook's GIT_* environment**
- **Found during:** close-out commit (the first attempt of the docs commit, run through `gsd-tools query commit`)
- **Issue:** inside a commit's hook environment `GIT_DIR` and `GIT_INDEX_FILE` point at the outer repository, so every git call in the four real-git tests, and the guard's own, acted on this repo instead of the throwaway one. They passed in a plain shell and in `92a6662`'s hook run, and failed under the other commit path.
- **Fix:** the fixture drops every `GIT_*` variable for the test (`monkeypatch.delenv`). Reproduced first with `GIT_DIR`/`GIT_INDEX_FILE` set by hand, then green with them set.
- **Files modified:** `tests/test_bench.py`
- **Verification:** the four tests pass with the variables set; `make verify` green in the hook.
- **Committed in:** `f611dd0`

---

**Total deviations:** 5 auto-fixed (1 bug, 1 blocking, 3 missing critical)
**Impact on plan:** all five are needed for correctness or to satisfy the gate; no scope creep. The additions are small: one helper `failed_record` in `verdict.py` (shared by the runner and the worker, not in the plan's interface list) and the guard wiring tests.

## Issues Encountered

- `.venv` kernel import and builds are fast here (smoke: 2.3 s wall); the slowest test is the worker round trip at 5.9 s, which includes one failing kernel build. No timing assertion exists anywhere in the new tests.
- The smoke guard line always carries the reason "origin/main was not fetched", because smoke does not fetch by design (the plan's wording); the other reasons on that line are real. Plan 02-03 onward calls the guard with `fetch=True` for campaign runs.

- One run of `make verify` in the first fix-commit attempt failed `tests/test_pool.py::test_a_dying_worker_surfaces_as_broken_pool_and_is_replaced`; the same test passes alone (17 of 17 in `tests/test_pool.py`) and the retried commit passed. Host load was 4 to 23 from other work. Not reproduced, not caused by a change in this plan that could be identified, and not fixed (out of scope). Logged in `deferred-items.md` in this phase directory: if it recurs, the new CPU-heavy tests in this plan (400 000-point integrals, kernel builds) are the first suspect, since the Makefile already notes that `tests/test_pool.py`'s injected timeouts are what a starved runner trips.

## Known Stubs

None. `protocol_guard` and `before_results` were stubs only inside the RED commit `7f3cc98` and are real in `92a6662`.

## Threat Flags

None. The new surface is the one the plan's threat model already covers: worker stdout parsed with `json.loads` only and exact keys (T-02-03), hard timeout with kill and respawn and stderr to a file (T-02-04), no flag skips the guard and smoke writes only to a temp directory (T-02-05), git called with list argv and a constant path (T-02-06), `TemporaryDirectory` per mesh (T-02-07).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02-03 can build the grid and record layout on `maths`, `verdict` and `Worker`, and call `read_guard(fetch=True)` before a campaign run.
- No campaign run has happened and none can: `check-protocol` exits 2 until PR 1 lands on origin/main.
- All ISO pitch values in `maths.PITCH` stay UNVERIFIED until Phase 4's row tests.
- No tech-debt or idea item filed by this plan.

## Self-Check: PASSED

- FOUND: all 9 created files under `bench/`
- FOUND: commits `90d2834`, `7f3cc98`, `92a6662`, `f611dd0` (four commits between plan_head_before and plan_head_after, measured with `git rev-list --count`; the fourth is `f611dd0`)
- `make verify` exit 0 (343 passed, coverage 95.56 % over the 94 % floor, `Contracts: 7 kept, 0 broken.`)
- `.venv/bin/python -m bench.thread_spike smoke` exit 0, Class ok; `check-protocol` exit 2 with `protocol guard: refused`

---
*Phase: 02-thread-spike*
*Completed: 2026-10-06*
