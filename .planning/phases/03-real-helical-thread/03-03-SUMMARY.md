---
phase: 03-real-helical-thread
plan: 03
subsystem: api
tags: [fine-stl-cap, l11, bytes-cache, download-refusal, cli-parity, info-warning, 422]

requires:
  - phase: 03-real-helical-thread
    provides: calc.thread (turns_of, MAX_TURNS), the info document and STANDING_WARNING (plans 03-01, 03-02)
provides:
  - "calc.thread: FINE_STL_ROWS (L11's seven measured (d, pitch) rows -> bytes cap in mm) and fine_stl_refusal"
  - "calc.download_refusal(p, fmt, quality): the one kernel-free rule the API and the CLI share"
  - "API: GET /api/bolt/model.stl at fine quality over a measured cap is a 422 fine_stl_cap before the bytes cache, the admission slot and the pool"
  - "CLI: screw export refuses the same part with exit 2 and no file, before the kernel import"
  - "info document: the same refusal text as a warning after the standing warning at a capped part"
affects: [03-04, 03-05, 03-06, 03-07, phase-04, phase-07]

actuals:
  tokens: 4700
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "a measured-rows table with mm only; turns derived by turns_of, never stored"
    - "one kernel-free refusal rule in calc, called by app._serve and cli.cmd_export, dispatched by isinstance like derive() (a kind without an entry is a TypeError the registry test catches)"
    - "an off-row part gets no cap: a cap from an unmeasured mapping to the nearest row is the plausible number L02 forbids"

key-files:
  created: []
  modified:
    - src/screw/calc/thread.py
    - src/screw/calc/__init__.py
    - src/screw/app.py
    - src/screw/cli.py
    - tests/test_thread_maths.py
    - tests/test_calc.py
    - tests/test_api.py
    - tests/test_cli.py

key-decisions:
  - "download_refusal raises TypeError for a kind with no entry whatever fmt and quality say, so a missing entry is caught by the registry test and not only on a fine STL request"
  - "The CLI refusal prints 'error: <text>' and exits 2 (a parameter choice refused), keeping exit 1 for BuildError; the text starts 'length: ' because the CLI prints no loc"
  - "The refusal is applied unconditionally, even when a deployer changes SCREW_EXPORT_CACHE_MB: the caps were measured against the 64 MiB budget only"

patterns-established:
  - "Refusals that depend only on parameters sit in calc and are called first in every serving path, before any cache or slot"

requirements-completed: [THRD-01]

coverage:
  - id: D1
    description: "The API refuses the fine STL at each of L11's seven measured rows above its bytes cap with a 422 fine_stl_cap naming length, the cap in mm and turns and the run id, and the backend is never called"
    requirement: THRD-01
    verification:
      - kind: integration
        ref: "tests/test_api.py#test_a_fine_stl_l11_measured_over_budget_is_a_422_and_never_reaches_the_backend"
        status: pass
      - kind: unit
        ref: "tests/test_thread_maths.py#test_each_cap_is_accepted_and_the_next_float_above_is_refused"
        status: pass
      - kind: unit
        ref: "tests/test_thread_maths.py#test_the_fine_stl_table_is_exactly_the_seven_rows_l11_measured"
        status: pass
    human_judgment: false
  - id: D2
    description: "The preview STL, the STEP and the info route of a capped part are served; the cap itself and an off-row part reach the backend as asked"
    requirement: THRD-01
    verification:
      - kind: integration
        ref: "tests/test_api.py#test_the_same_part_is_served_on_the_preview_stl_the_step_and_the_info_route"
        status: pass
      - kind: integration
        ref: "tests/test_api.py#test_the_cap_itself_and_an_off_row_part_reach_the_backend_as_asked"
        status: pass
      - kind: unit
        ref: "tests/test_calc.py#test_only_the_fine_stl_of_a_capped_part_is_refused"
        status: pass
    human_judgment: false
  - id: D3
    description: "screw export refuses the same fine STL with exit 2, 'error: length:' and the run id, writes no file, and exports the same part as STEP or preview STL"
    requirement: THRD-01
    verification:
      - kind: unit
        ref: "tests/test_cli.py#test_a_fine_stl_l11_measured_over_budget_exits_2_and_writes_nothing"
        status: pass
      - kind: integration
        ref: "tests/test_cli.py#test_the_over_budget_fine_stl_exits_2_from_the_real_process"
        status: pass
      - kind: integration
        ref: ".venv/bin/screw export bolt --d 8 --pitch 1.25 --length 67.6 -o x.stl (exit 2, no x.stl)"
        status: pass
    human_judgment: false
  - id: D4
    description: "The info document of a capped part carries the refusal text as a warning after the standing warning; at the cap or off the measured rows the warnings stay the standing one only"
    requirement: THRD-01
    verification:
      - kind: unit
        ref: "tests/test_calc.py#test_a_capped_part_warns_about_its_fine_stl_after_the_standing_warning"
        status: pass
      - kind: unit
        ref: "tests/test_calc.py#test_no_fine_stl_warning_at_the_cap_or_off_the_measured_rows"
        status: pass
    human_judgment: false

duration: 7min
completed: 2026-10-10
status: complete
commits: 2
plan_head_before: 1d9c44a2286477754b8e80689b9a2b0febdbf670
plan_head_after: 2fc210c23305c38dfb3524ee7db419c6f80fcfc1
---

# Phase 3 Plan 03: The fine-STL cap on the measured rows Summary

**L11's seven measured fine-STL bytes caps are one kernel-free refusal: a 422 `fine_stl_cap` on the API before the cache, the slot and the pool, exit 2 on the CLI before the kernel import, and a warning on the info document, with off-row parts untouched.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-10-10T14:11Z (HEAD `1d9c44a` commit time; the start was not recorded separately)
- **Completed:** 2026-10-10T14:18Z
- **Tasks:** 2
- **Files modified:** 8 (0 created, 8 modified)

## Accomplishments

- `calc/thread.py`: `FINE_STL_ROWS` holds exactly the seven L11 rows (8, 1.25) 67.5, (10, 1.5) 56, (12, 1.75) 60, (14, 2) 58, (16, 2) 52, (18, 2.5) 65, (20, 2.5) 64 mm, with the D-03 comment block (measured rows, not ISO rows; run keys UNVERIFIED as table truth; 64 MiB budget only; off-row gets no cap) and one comment per row naming its first row over budget. `fine_stl_refusal` begins `length: `, gives the rod, the cap in mm and turns, the run id and the asked length, and says the preview STL and the STEP are not capped. Turns read 54, 37.3333, 34.2857, 29, 26, 26, 25.6.
- `calc/__init__.py`: `download_refusal(p, fmt, quality)`; `_bolt` appends the same text to the warnings after the standing warning.
- `app._serve` calls `download_refusal` first and raises `422 [{"loc": ["query"], "type": "fine_stl_cap", "msg": ...}]`; it reads no field by name. The `_EXPORTS` budget comment and the 30 s timeout comment were restated for threads (values and knobs unchanged); `grep -n 'skeleton cylinder' src/screw/app.py` prints nothing.
- `cli.cmd_export` builds the params, asks `download_refusal`, prints `error: <text>` and exits 2 before `from .solid import`. Real process: `screw export bolt --d 8 --pitch 1.25 --length 67.6 -o x.stl` exits 2, prints `error: length: ...2026-10-08-a-grid...`, writes no file.

## Task Commits

1. **Task 1: the API refuses the fine STL L11 measured over budget** - `35a590a` (feat)
2. **Task 2: the CLI refuses the same fine STL, the info document warns about it** - `2fc210c` (feat)

**Plan metadata:** committed with this SUMMARY (docs: complete plan)

## Files Created/Modified

- `src/screw/calc/thread.py` - `FINE_STL_ROWS`, `fine_stl_refusal`
- `src/screw/calc/__init__.py` - `download_refusal`; the fine-STL warning in `_bolt`
- `src/screw/app.py` - the `fine_stl_cap` 422 in `_serve`; two INTERIM comments restated
- `src/screw/cli.py` - the exit-2 refusal in `cmd_export`, kernel import after it
- `tests/test_thread_maths.py`, `tests/test_calc.py`, `tests/test_api.py`, `tests/test_cli.py` - the table (typed from L11, not read back from the code), the cap and the next float above for each row, the orphan-kind TypeError, the registry test, the routes with a counting backend (zero calls) and a stub backend, the CLI in process and in a real process

## Decisions Made

- Refusal text wording (not fixed by the plan): `length: the fine STL of the rod with d <d> and pitch <p> is refused above <cap> mm (<turns> turns), where L11 measured it over the export budget (run 2026-10-08-a-grid); this length is <length> mm. Shorten length, or ask for the preview STL or the STEP, which are not capped`.
- `download_refusal` dispatches on the kind before it looks at `fmt` and `quality`, so an unregistered kind is a `TypeError` on every call and `test_every_registered_kind_has_a_download_rule` catches it.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] mypy: `FastenerParams` has no attribute `length` in the new stub-backend test**
- **Found during:** Task 1 (first commit attempt, hook)
- **Issue:** the stub records `FastenerParams`; reading `.length` failed `mypy --strict`.
- **Fix:** the test narrows with `isinstance(p, BoltParams)` and asserts nothing was dropped by the narrowing.
- **Files modified:** tests/test_api.py
- **Committed in:** 35a590a

**2. [Rule 3 - Blocking] ruff E501: a 102-column test name**
- **Found during:** Task 2 (first commit attempt, hook)
- **Fix:** renamed to `test_a_capped_part_warns_about_its_fine_stl_after_the_standing_warning`.
- **Files modified:** tests/test_calc.py
- **Committed in:** 2fc210c

---

**Total deviations:** 2 auto-fixed (both blocking lint/type). **Impact on plan:** none on behaviour or contracts. Each failing hook meant no commit was made; the fixed commit is the only one.

## TDD Gate Compliance

Both tasks are `tdd="true"`. The pre-commit hook runs `make verify`, so a RED-only commit cannot land; RED was shown by running the new tests against the pre-change source (a `git archive` of the parent commit on `PYTHONPATH`, in the scratchpad) and test plus implementation are one commit per task.

- **Task 1 RED:** `tests/test_api.py -k "fine_stl or same_part_is_served or cap_itself"` gave `1 failed, 2 passed`: `test_a_fine_stl_l11_measured_over_budget_is_a_422_and_never_reaches_the_backend` failed on `assert 200 == 422` (the capped fine STL was served). The two passing tests are the "everything else is unchanged" cases and are expected green before the change. `tests/test_thread_maths.py` and `tests/test_calc.py` failed to collect (`cannot import name 'download_refusal'` / `fine_stl_refusal`); those are load failures, not RED evidence.
- **Task 2 RED:** `tests/test_cli.py -k "fine_stl or over_budget or same_part"` gave `2 failed, 1 passed`: `test_a_fine_stl_l11_measured_over_budget_exits_2_and_writes_nothing` failed with `DID NOT RAISE SystemExit` (it wrote the fine STL, 44299 KiB) and `test_the_over_budget_fine_stl_exits_2_from_the_real_process` failed on `assert 0 == 2`; `tests/test_calc.py -k "warns_about or no_fine_stl"` gave `1 failed, 1 passed` (the capped warnings were `[STANDING_WARNING]` only). Semantic assessment: the target tests ran and failed on the planned assertions for the intended reason.
- `gsd_run check tdd-red-evidence` was not run (no persisted record, as in plans 03-01 and 03-02).

## Issues Encountered

- A `rm -rf "$SCR/.."` in a scratch step was refused by the shell (it ends in `..`); the scratch copy was simply re-extracted over the previous one from `HEAD` (which by then included Task 1, the right baseline for Task 2's RED). Nothing in the repo was touched.

## Verification

- `make verify` (last run, after the final code commit): ruff `All checks passed!`; mypy `Success: no issues found in 46 source files`; import-linter `Contracts: 7 kept, 0 broken`; pytest `815 passed in 35.34s`, coverage `96.89%` against the 94 floor.
- `make test PYTEST_ARGS="tests/test_thread_maths.py tests/test_api.py tests/test_calc.py -q -n0 --no-cov"`: `143 passed`; `tests/test_cli.py tests/test_calc.py`: `50 passed`.
- Task 2's piped real-entry-point check: `.venv/bin/screw export bolt --d 8 --pitch 1.25 --length 67.6 -o $d/x.stl` exit 2, `error: length:` on stderr, no `x.stl`.
- Acceptance greps: `FINE_STL_ROWS`, `2026-10-08-a-grid`, `not ISO rows`, `def fine_stl_refusal(` present in `calc/thread.py`; `def download_refusal(` in `calc/__init__.py`; `"fine_stl_cap"` in `app.py`; no `skeleton cylinder` in `app.py`; `download_refusal(` (cli.py line 86) precedes `from .solid import` (line 93); `fine_stl_refusal(` is referenced in `_bolt`.

## Debt

- Resolved: none. Filed: none. T-3-08 (in-cap off-row parts that need minutes) is accepted by the plan and recorded by plan 03-07 in `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md`; the timeout comment in `app.py` now points at the figures and the cap.

## Known Stubs

None.

## Threat Flags

None. The surface touched is the plan's T-3-07 (denial of service by a fine STL the bytes cache refuses to keep), mitigated by `download_refusal` before the cache, the slot and the pool, with a counting backend showing zero builds, and the same rule on the CLI.

## Next Phase Readiness

Ready for 03-04. The seven L11 rows are the only bytes caps; no other row was measured and none was invented. The refusal is also visible on the info document, so the UI built in later plans shows it with no extra work.

## Self-Check: PASSED

Modified files exist on disk; commits `35a590a` and `2fc210c` are ancestors of HEAD; `git rev-list --count 1d9c44a..HEAD` read 2 before this SUMMARY.

---
*Phase: 03-real-helical-thread*
*Completed: 2026-10-10*
