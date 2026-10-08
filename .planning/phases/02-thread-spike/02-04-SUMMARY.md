---
phase: 02-thread-spike
plan: 04
subsystem: testing
tags: [thread-spike, negative-control, one-pipe, ruled-surface-reference, tip-trim, fresh-child-rss, l19-gzip-table, container-linux-amd64, worker-once]

requires:
  - phase: 02-thread-spike
    provides: the rod campaign grid, blocks, JSONL records and verdict rules (plan 02-03); the maths, worker protocol and guard (plan 02-02)
provides:
  - helical - naive_sweep_fuse (the research negative control, reproduced to three digits), one_pipe, trim_tip, ruled_reference (importlib, object-typed, narrowed against cadquery types)
  - worker kinds naive, one_pipe, ruled, trim and the --once child (peak RSS after the one mesh and gzip-1, before any STL check; L19 gzip table after that reading)
  - runner - CONTAINER_IMAGE, container_argv (read-only bench mount, list argv), docker_kill on timeout, a Worker argv factory and on_timeout hook, run_once
  - blocks controls, trim, rss (--frontier-from) and container behind the same guard and quiet gate, each with a smoke subset
  - verdict - classify_record / classify_trim (no closed form for a trimmed tip), known_bad_inputs, container rows counted in the pass bar and escape clause, controls / trim / RSS / gzip / container sections
  - owner approval of the ruled-surface reference package, recorded below
affects: [02-05 pair check, 02-06 protocol write-up, 02-07 campaign, 02-08 verdict, Phase 3 builder promotion and THRD-04 positive control]

actuals:
  tokens: 29700
  tasks: 3
  commits: 2
plan_head_before: 135efa6b997c9809db603661a8dd3a1eefe1cc0c
plan_head_after: 1ed384909999a6bd00a78c474c8b5d4a1a63b814

tech-stack:
  added: []
  patterns:
    - "A fresh --once child is the only source of a per-row peak RSS; a persistent worker records None and a rod --once request must name exactly one preset so the reading is taken after that mesh and before any check"
    - "Evidence rows (controls, trim, rss) are printed beside the verdict and filtered out of pass_bar and escape_rows by kind, so a control that is wrong on purpose cannot fail a bar"
    - "A block's report sections are one SECTIONS table of (title, builder over RowRecord lists), shared by the run report and the verdict over the recorded JSONL"
    - "The reference package is probed in a throw-away child and imported only in a separate worker whose PYTHONPATH adds SCREW_SPIKE_CQW; the parent never imports it or the kernel"

key-files:
  created: []
  modified:
    - bench/thread_spike/maths.py
    - bench/thread_spike/helical.py
    - bench/thread_spike/worker.py
    - bench/thread_spike/verdict.py
    - bench/thread_spike/runner.py
    - bench/thread_spike/__main__.py
    - tests/test_bench.py

key-decisions:
  - "The request flag that asks for the gzip table is want_gzip_table, because a RowRecord inherits the request's keys and its own gzip_table field (a list or None) cannot also be the request's bool"
  - "A row that asks for the gzip table gets GZIP_TABLE_TIMEOUT_S = 900 s instead of the 120 s row deadline: the table compresses one STL 35 times at each of three levels and the largest fine STL is 164 MB"
  - "A container run is never decisive and its header says decisive false whatever the host gate read: emulated timings prove nothing about the production host"
  - "A campaign without a container run is never a pass (PASS_BLOCKS adds container to the four rod blocks): the container rows are verdict inputs, so a missing run is unestablished, not held"
  - "naive_sweep_fuse reads the research recipe as helix radius d/2, core cylinder at the root radius, tooth root embedded 0.05 P below it, flank half-width P/16 + (d/2 - embedded root) * tan 30: the only one of 12 readings that reproduces all three research ratios"

patterns-established:
  - "RULED_MODULE lives in maths (a name, not an import) so the kernel-free parent can probe the scratch directory"
  - "Smoke exit codes are per block: controls expects the naive row not ok, one-pipe ok and the reference built; every other block expects every row ok"

requirements-completed: [INFR-03]

coverage:
  - id: D1
    description: "The negative control naive_sweep_fuse is reproduced from the research recipe and never classifies ok: M6 L10 gives 1 solid, valid, precise ratio 0.238384 (research 0.238), M2 L6 0.274107 (0.274), M6 L20 and L40 raise Null TopoDS_Shape; the known-bad inputs (naive, 1 solid, valid, ratio below 0.5) are listed with exact parameters for Phase 3's THRD-04 test and the recipe stays importable"
    requirement: INFR-03
    verification:
      - kind: integration
        ref: "tests/test_bench.py#test_the_negative_control_is_never_classified_ok_by_the_real_kernel"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_the_known_bad_inputs_are_the_naive_rows_with_one_valid_solid_below_half_the_volume"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_the_controls_section_lists_the_rows_the_known_bad_inputs_and_the_profile_caveat"
        status: pass
    human_judgment: false
  - id: D2
    description: "One-pipe twist and the ruled-surface reference run on the sample sizes, right hand, judged by the same classify_row; the ruled rows run only in a second worker whose PYTHONPATH carries SCREW_SPIKE_CQW, the default worker cannot see the package, and the controls block refuses (exit 2, nothing written, before the guard) when the variable is unset or the package is not importable there"
    requirement: INFR-03
    verification:
      - kind: integration
        ref: "tests/test_bench.py#test_the_one_pipe_twist_of_ten_turns_is_classified_ok_by_the_real_kernel"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_the_default_worker_cannot_see_the_ruled_surface_package"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_the_controls_block_runs_ruled_in_the_reference_worker_and_the_rest_right_hand"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_the_controls_block_refuses_without_the_scratch_directory_before_anything_runs"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_the_controls_block_refuses_a_scratch_directory_the_package_does_not_import_from"
        status: pass
      - kind: e2e
        ref: "SCREW_SPIKE_CQW=$HOME/.cache/screw-spike/cq_warehouse-daa4650 .venv/bin/python -m bench.thread_spike smoke --block controls"
        status: pass
    human_judgment: false
  - id: D3
    description: "The tip-chamfer-trim row, one per size and hand at the standard max, records trim seconds and the request cost build + trim + slower export; it is judged on solids, isValid and the preview check only, never against a closed form, never enters the pass bar, and labels the 30 degree cone UNVERIFIED (ISO 4753 unread)"
    requirement: INFR-03
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_a_trim_row_is_judged_on_solids_validity_and_the_preview_check_never_on_a_closed_form"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_no_comparison_or_trim_row_can_fail_the_pass_bar_or_fire_the_escape_clause"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_a_trim_request_costs_build_plus_trim_plus_the_slower_export"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_the_tip_chamfer_angle_is_30_degrees_and_says_it_is_unverified"
        status: pass
      - kind: e2e
        ref: ".venv/bin/python -m bench.thread_spike smoke --block trim"
        status: pass
    human_judgment: false
  - id: D4
    description: "Peak RSS exists only from a fresh --once child, read after the one mesh and gzip-1 and before any STL check; a persistent worker records none and refuses a gzip-table request; every printed figure is labelled 'fresh child, this row only'; the L19 gzip table and the selected level print only for rows that asked for one"
    requirement: INFR-03
    verification:
      - kind: integration
        ref: "tests/test_bench.py#test_a_fresh_once_child_records_its_peak_rss_and_a_persistent_worker_never_does"
        status: pass
      - kind: integration
        ref: "tests/test_bench.py#test_the_once_child_runs_l19s_table_on_the_rows_own_stl_after_the_rss_reading"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_an_rss_row_prints_its_figure_labelled_a_fresh_child_and_a_persistent_row_prints_none"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_the_l19_table_and_the_selected_level_print_only_for_rows_that_asked_for_one"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_the_rss_block_is_one_fresh_child_per_size_hand_and_preset_plus_the_terminal_rows"
        status: pass
      - kind: e2e
        ref: ".venv/bin/python -m bench.thread_spike smoke --block rss"
        status: pass
    human_judgment: false
  - id: D5
    description: "The container block runs the locked construction over the full D-03 grid, rod and void, both hands, through the same JSON-lines worker in screw:latest under linux/amd64 with bench/ mounted read-only (list argv, --rm, docker kill and a new name on timeout), validity, solid count and volume only; a failure or silent_wrong container row counts toward the pass bar and the escape clause; the run is never decisive and refuses (exit 2) when docker or the image is absent"
    requirement: INFR-03
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_the_container_argv_is_a_list_that_mounts_bench_read_only_under_linux_amd64"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_a_timeout_runs_the_on_timeout_hook_and_the_respawn_asks_for_a_new_argv"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_the_container_rows_count_toward_the_pass_bar_and_the_escape_clause_in_the_verdict"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_a_container_run_is_never_decisive_and_says_which_image_and_that_timings_are_emulated"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_the_container_block_refuses_before_the_guard_when_docker_or_the_image_is_absent"
        status: pass
      - kind: e2e
        ref: ".venv/bin/python -m bench.thread_spike smoke --block container"
        status: pass
    human_judgment: false
  - id: D6
    description: "The owner vetted and approved the ruled-surface reference package at a blocking legitimacy checkpoint before anything installed it; it was installed only from the pinned commit, --no-deps, into a scratch directory outside the repository, and never entered pyproject.toml or requirements.txt"
    requirement: INFR-03
    verification:
      - kind: other
        ref: "git diff --quiet origin/main...HEAD -- requirements.txt; git grep -n 'warehouse' -- pyproject.toml requirements.txt (exit 1)"
        status: pass
    human_judgment: true
    rationale: "The legitimacy decision is the owner's and is recorded as a quoted reply; no automated check can stand in for it"

duration: 27min (this continuation only; Task 1 was the previous executor's checkpoint)
completed: 2026-10-06
status: complete
---

# Phase 2 Plan 04: Comparison, Cost and Container Slices Summary

**The negative control (reproduced to three digits), one-pipe twist and ruled-surface reference rows, the tip-trim cost row, fresh-child RSS rows with the L19 gzip table, and the linux/amd64 container block all run end to end under smoke, behind the owner-approved, scratch-installed reference package.**

## Performance

- **Duration:** 27 min for this continuation (12:59Z to 13:26Z); Task 1 was a checkpoint returned by the previous executor
- **Started:** 2026-10-06T12:59:28Z
- **Completed:** 2026-10-06T13:26:27Z
- **Tasks:** 3 (Task 1 checkpoint, Tasks 2 and 3 auto)
- **Files modified:** 7

## Owner approval (Task 1)

The owner approved the ruled-surface reference package at the blocking legitimacy checkpoint on **2026-10-06**. The reply, verbatim:

> approved

Evidence presented at the checkpoint (both `gh api` calls exit 0): pinned commit `daa46507ecc429c0e2dce11d9d5ffd09b12a42af` exists, authored 2023-09-24T13:18:35Z; licence Apache-2.0; owner `gumyr`. The plan's "November 11th 2021" is the `thread.py` file-header date from research, which the commit date neither confirms nor contradicts: it stays an unverified research claim. Installed exactly as approved (`PIP_CONSTRAINT=requirements.txt .venv/bin/python -m pip install --no-deps --target "$HOME/.cache/screw-spike/cq_warehouse-daa4650" "git+https://github.com/gumyr/cq_warehouse.git@daa46507..."`): cq_warehouse 0.8.0 built from the pinned commit, `import cq_warehouse.thread` exits 0 with `PYTHONPATH` set to the scratch directory, `.venv` site-packages untouched (`pip list` shows no such package), `pyproject.toml` and `requirements.txt` untouched, no code copied.

## Accomplishments

- **Negative control reproduced.** Four readings of the research recipe were tried; one reproduces all three measured ratios: M6 L10 gives 1 solid, valid, precise ratio 0.238384 (research 0.238); M2 L6 0.274107 (0.274); M6 L20 and L40 raise `Null TopoDS_Shape`. It is never classified ok, listed by the verdict as a THRD-04 known-bad input with exact parameters, and importable from `bench/thread_spike/helical.py`.
- **Comparison rows.** One-pipe twist classifies ok at 10 turns (ratio 1.000002, and 0.999993 at 250 turns in a probe on M6, which does not reproduce STACK's inversion at 160-171 turns on that size; the campaign, not this plan, is where that gets measured). The ruled-surface reference built at 10 turns (ratio 0.985012) and 60 turns (0.997312) in the reference worker; the report states its profile differs from the pinned one so the ratio is not an accuracy claim.
- **Tip-trim cost.** `trim_tip` over the rod, M6 at 20 mm: valid, 1 solid, trim 0.31 s, request cost 1.03 s (build + trim + slower export), cone angle labelled UNVERIFIED; trim rows never enter the pass bar.
- **Fresh-child RSS and L19.** `--once` child: smoke M6 10 turns fine read 777.0 MiB peak (one measurement on a 12-CPU arm64 host, not a bound); the L19 table on that STL selected level 1 (2 645 122 B at level 1 against 2 518 410 B at 6, under L19's 10 % bar).
- **Container pass.** M6 rod and void at 5 turns in `screw:latest` (amd64, Docker 29.4.0 on arm64, emulated): both ok. A forced 2 s timeout killed the container (`docker kill`), the respawn took a new name, `docker ps -a` showed none left.
- **Verdict extended.** Container rows count toward the pass bar and the escape clause beside the host grid; controls, trim, RSS and container sections print from recorded JSONL; a campaign without a container run is never a pass.

## Task Commits

1. **Task 1: Owner vets the ruled-surface reference package** - no commit (verification only; approval recorded above)
2. **Task 2: Negative control, one-pipe, ruled-surface reference and tip-trim row** - `9ff13b9` (feat)
3. **Task 3: Fresh-child RSS and gzip rows and the container block** - `1ed3849` (feat)

**Plan metadata:** the SUMMARY commit, then the STATE/ROADMAP commit (docs).

## Files Created/Modified

- `bench/thread_spike/maths.py` - `RULED_MODULE` name and `TIP_CHAMFER_DEG = 30.0` (UNVERIFIED, ISO 4753 unread)
- `bench/thread_spike/helical.py` - `naive_sweep_fuse`, `one_pipe`, `trim_tip`, `ruled_reference`
- `bench/thread_spike/worker.py` - kinds naive, one_pipe, ruled, trim; `--once`; `_OnceProbe` (RSS, then gzip table); `_refusal` guards
- `bench/thread_spike/verdict.py` - wire fields `trim_s`, `peak_rss_bytes`, `gzip_table`, `gzip_selected`, request `want_gzip_table`; `classify_trim`, `classify_record`, `known_bad_inputs`; `GZIP_TABLE_TIMEOUT_S`; kind filter in `pass_bar` and `escape_rows`
- `bench/thread_spike/runner.py` - `CONTAINER_IMAGE`, `container_argv`, `docker_kill`, Worker argv factory and `on_timeout`, `run_once`
- `bench/thread_spike/__main__.py` - blocks controls, trim, rss, container; `--frontier-from`; `SCREW_SPIKE_CQW` probe; sections and per-block smoke expectations; container precheck; verdict container and evidence sections
- `tests/test_bench.py` - 31 new tests (257 in the file, 517 in `make verify`)

## Decisions Made

See `key-decisions`. In brief: the gzip request flag is `want_gzip_table`; gzip-table rows get a 900 s deadline; container runs are never decisive; a campaign without a container run is never a pass; the naive recipe is the one reading that reproduces the research numbers.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] A verdict with no container run could read as a pass**
- **Found during:** Task 3 (verdict extension)
- **Issue:** The plan counts container rows in the pass bar and the escape clause but not what a campaign with no container run says; with nothing recorded the bar would read held, a plausible pass over an unmeasured production image (L02).
- **Fix:** `PASS_BLOCKS` adds `container` to the four rod blocks; a missing run lists as a missing block, the bar reads "not established" ("no container run") and the exit is 1. The plan 02-03 test campaigns gained a container run.
- **Files modified:** bench/thread_spike/__main__.py, tests/test_bench.py
- **Verification:** `test_a_campaign_without_the_container_run_is_never_a_pass`
- **Committed in:** 1ed3849

**2. [Rule 2 - Missing Critical] The 120 s row deadline cannot carry the gzip table**
- **Found during:** Task 3 (rss block)
- **Issue:** `gzip_rows` compresses the STL 5 times single-threaded and 30 times concurrently at each of three levels; on the 164 MB fine STL of M20 L200 that is minutes. At `ROW_TIMEOUT_S` the L19 table the plan requires at every size would be a recorded timeout at the large sizes.
- **Fix:** `GZIP_TABLE_TIMEOUT_S = 900.0` applies to rows with `want_gzip_table`. It is a protocol input that plan 02-06 must register in `02-SPIKE.md` beside the 120 s one.
- **Files modified:** bench/thread_spike/verdict.py, bench/thread_spike/__main__.py
- **Verification:** `test_the_rss_block_is_one_fresh_child_per_size_hand_and_preset_plus_the_terminal_rows` (15 rows at 900 s, 47 at 120 s)
- **Committed in:** 1ed3849

**3. [Rule 3 - Blocking] `RULED_MODULE` could not live in helical**
- **Found during:** Task 2
- **Issue:** The parent needs the module name to probe the scratch directory, and `__main__` may not import `helical` (the import-linter contract forbids reaching the kernel, even indirectly).
- **Fix:** the name is a constant in the kernel-free `maths`, and `helical` imports it.
- **Files modified:** bench/thread_spike/maths.py, bench/thread_spike/helical.py
- **Committed in:** 9ff13b9

### Plan Interpretations (not deviations from an acceptance criterion)

- The request flag is named `want_gzip_table` (the plan says only "when the request asks for the gzip table").
- A `--once` rod request must name exactly one preset: with two, the RSS reading would follow the first mesh's check or miss the second mesh. Anything else is a recorded failure.
- The rss smoke row (M6, 10 turns, fine) also asks for the gzip table, so the table path runs end to end in smoke. The table prints only for such rows.
- The naive recipe's wording ("r", "root embedded") admits several readings; the one used is documented in `naive_sweep_fuse` and in `key-decisions`.

---

**Total deviations:** 3 auto-fixed (2 missing critical, 1 blocking)
**Impact on plan:** All three are additions needed for honesty or to compile under the import contracts; no scope creep. Plan 02-06 must register `GZIP_TABLE_TIMEOUT_S`.

## Issues Encountered

- `tests/test_pool.py::test_a_dying_worker_surfaces_as_broken_pool_and_is_replaced` did not flake in any of the five `make verify` runs here (two explicit, two commit hooks, one test-file run); no recurrence to note.
- The container pass under emulation: the 120 s `ROW_TIMEOUT_S` may be too short for the largest void rows at M20 L200. A timeout there makes the container bar "not established" rather than held (container runs are never decisive). That is the protocol's call, not this plan's; flagged for 02-06 and 02-07.
- The research date for `thread.py` (November 2021) was not confirmed by the pinned commit's date (2023-09-24); recorded above as unverified.

## Known Stubs

None. Stub scan of the diff found no TODO, FIXME, placeholder text or empty-default data flowing to a report.

## Threat Flags

None beyond the plan's register. T-02-SC, T-02-11, T-02-12 and T-02-13 are mitigated as written: pinned install with a blocking checkpoint, reference package importable only in a separate worker, read-only mount with list argv and `docker kill` on timeout (checked against real Docker), fresh children one at a time under a deadline.

## User Setup Required

None. The reference package is installed at `$HOME/.cache/screw-spike/cq_warehouse-daa4650`, outside the repository; the controls block reads it through `SCREW_SPIKE_CQW`.

## Next Phase Readiness

- Ready for plan 02-05 (pair check). The verdict now needs the container run, so plan 02-08's campaign must include one.
- Plan 02-06 (protocol) must pre-register: `GZIP_TABLE_TIMEOUT_S = 900`, the container block being never decisive, the controls expectation (naive never ok, one-pipe ok, reference built), the 30 degree trim cone as an UNVERIFIED input, and that container rows count toward the pass bar.
- Nothing here is a campaign record: every number above is a smoke reading on one host.

## Self-Check: PASSED

- `bench/thread_spike/{maths,helical,worker,verdict,runner,__main__}.py` and `tests/test_bench.py` exist; commits `9ff13b9` and `1ed3849` are ancestors of HEAD.
- `make verify` exit 0, 517 passed, coverage 95.56 % (floor 94 %), lint-imports clean.
- `smoke --block controls` (with `SCREW_SPIKE_CQW`), `trim`, `rss` and `container` each exit 0 and print "not a campaign run".
- `git diff --quiet origin/main...HEAD -- requirements.txt` exit 0; `git grep -n 'warehouse' -- pyproject.toml requirements.txt` exit 1.
- `grep -n 'TIP_CHAMFER_DEG = 30.0' bench/thread_spike/maths.py` matches with UNVERIFIED in its comment; `def container_argv(` and `:ro` match in `runner.py`.

---
*Phase: 02-thread-spike*
*Completed: 2026-10-06*
