---
phase: 07-operability-re-sweep
plan: 03
subsystem: testing
tags: [pre-registration, protocol, point-sets, probes, cgroup, docker, github-actions, pr]

requires:
  - phase: 07-operability-re-sweep
    provides: "07-01: bench.oper parent, bench.oper_child, operability.yml, tracer.json (branch gsd/phase-07-preregistration at 3c589d8)"
provides:
  - "07-SWEEP-PROTOCOL.md: the rules R1 to R30 of the whole phase 7 campaign, fixed before any runner reading"
  - "bench.oper_sets: deterministic generator and --check for explore, spread, walls and controls (1692, 12, 681 and 69 points)"
  - "bench.oper_child.run_probe: tail, naive and one_pipe probes that run in the production image through the same parent as a part"
  - "PR A (#22) open: gsd/phase-07-preregistration against main, head 40f667d843d9c83a0111890f95b0bfbdf4d0f2b3"
affects: [07-04, 07-05, 07-06, operability, ci]

actuals:
  tokens: 185535   # chars/4 over the added lines of 3c589d8..40f667d; 22668 hand-written, 162867 generated point files
  tasks: 3
  commits: 5
plan_head_before: 3c589d8e215e8372e57f394c021928696a2cfaee
plan_head_after: 40f667d843d9c83a0111890f95b0bfbdf4d0f2b3

tech-stack:
  added: []
  patterns:
    - "a point file is generated and byte-checked: the same code writes the same bytes and --check runs in make verify"
    - "a combination the parameter model refuses is listed in dropped with its pydantic error type, never measured and never silent"
    - "a probe is a Point whose kind is probe, whose artifact is the probe name and whose params are its arguments"
    - "an ok line is held to the fields of what was asked for: a part line is not a probe line"

key-files:
  created:
    - bench/oper_sets.py
    - bench/points/explore.json
    - bench/points/spread.json
    - bench/points/walls.json
    - bench/points/controls.json
    - .planning/phases/07-operability-re-sweep/07-SWEEP-PROTOCOL.md (on gsd/phase-07-preregistration)
  modified:
    - bench/oper.py
    - bench/oper_child.py
    - tests/test_oper.py
    - pyproject.toml
    - docs/tech_debt/active/2026-10-10-spike-protocol-amendments-before-next-campaign.md
    - docs/tech_debt/active/2026-10-14-m18-probe-one-entry-has-no-deadline-during-a-run.md

key-decisions:
  - "The tail probe runs the production THRD-04 gate (check_solid) with MIN_TAIL_MM lowered for the call and restored in a finally, so a failing tail is exactly a tail the shipped builder would refuse; naive and one_pipe apply no gate (controls are expected to be wrong)"
  - "A probe ok line carries solids, valid and a signed volume_ratio and no export; volume_ratio is the only number allowed below 0, because one_pipe at 160 turns builds an inverted solid (measured -0.99999) that still reports valid"
  - "A point label may be listed once per artifact (not once per file), so a part keeps one label across its three artifacts and the fit joins on it"
  - "The root-radius walk solves the pitch to full float precision: a 6-figure pitch moves the root radius by up to about 5e-6 mm, more than the 1e-6 mm end of the walk"
  - "The fourth recorded corner (d 1e5) cannot be requested (s must exceed d and is bounded by 1e5), so it is in dropped, not measured; walls walks the largest d the ceiling allows"
  - "The protocol defines the cold wall as build_s + export_s and takes the R5 margin over it"

patterns-established:
  - "Pre-registration order: probes, then point files, then the protocol, then PR A; the protocol quotes the generator and a test pins the quote"

requirements-completed: [OPER-01, OPER-02, OPER-03]

coverage:
  - id: D1
    description: "The tail, naive and one_pipe probes run in the image through the same parent as a part: a kernel exception is a refused record with class and text, a SIGSEGV is crashed with no number, and the tail probe restores MIN_TAIL_MM after the call, success or failure"
    requirement: OPER-02
    verification:
      - kind: unit
        ref: "tests/test_oper.py#test_the_tail_probe_lowers_the_builder_guard_for_the_call_and_restores_it"
        status: pass
      - kind: unit
        ref: "tests/test_oper.py#test_the_tail_probe_restores_the_guard_when_the_build_fails"
        status: pass
      - kind: unit
        ref: "tests/test_oper.py#test_a_probe_that_crashes_the_container_is_crashed_with_no_number"
        status: pass
      - kind: unit
        ref: "tests/test_oper.py#test_a_kernel_exception_in_a_control_is_a_refused_record_with_its_class_and_text"
        status: pass
    human_judgment: false
  - id: D2
    description: "The point files are deterministic and cannot drift from their generator; explore holds all 294 bolt and 14 nut rows at three artifacts (924 preset points); 201 of 294 rows have an integer L/P by exact decimals"
    requirement: OPER-01
    verification:
      - kind: unit
        ref: "tests/test_oper.py#test_the_committed_point_files_are_what_the_generator_writes"
        status: pass
      - kind: unit
        ref: "tests/test_oper.py#test_writing_twice_gives_byte_identical_files"
        status: pass
      - kind: unit
        ref: "tests/test_oper.py#test_201_of_the_294_catalogue_rows_have_an_integer_turn_count_by_exact_decimals"
        status: pass
      - kind: unit
        ref: "tests/test_oper.py#test_explore_holds_every_catalogue_row_at_each_of_the_three_artifacts"
        status: pass
      - kind: other
        ref: "python -m bench.oper_sets --check (prints integer L/P: 201 of 294, exit 0)"
        status: pass
    human_judgment: false
  - id: D3
    description: "A combination the parameter model refuses is listed in dropped with the model's error type and is never a point"
    requirement: OPER-01
    verification:
      - kind: unit
        ref: "tests/test_oper.py#test_every_dropped_combination_is_refused_by_the_model_with_the_error_it_names"
        status: pass
      - kind: unit
        ref: "tests/test_oper.py#test_a_corner_the_model_refuses_is_dropped_with_its_error_and_never_measured"
        status: pass
    human_judgment: false
  - id: D4
    description: "The walls set covers the 250-turn walls, the 1e3/1e4/1e5 field ceilings, the tails 1e-2 to 1e-9 mm and the root radii 1e-2 to 1e-6 mm per size and hand, and the controls set the thread spike's positions"
    requirement: OPER-02
    verification:
      - kind: unit
        ref: "tests/test_oper.py#test_the_turn_walls_are_250_turns_at_the_15_sizes_both_hands_rod_and_void"
        status: pass
      - kind: unit
        ref: "tests/test_oper.py#test_the_root_radius_walk_reaches_the_radius_it_names_at_every_size_and_hand"
        status: pass
      - kind: unit
        ref: "tests/test_oper.py#test_the_controls_run_the_thread_spikes_positions_on_the_sample_sizes_right_hand"
        status: pass
    human_judgment: false
  - id: D5
    description: "07-SWEEP-PROTOCOL.md states R1 to R30, names the seed, margins, roundings and thresholds with their reasons, and is committed before any runner reading"
    requirement: OPER-02
    verification:
      - kind: unit
        ref: "tests/test_oper.py#test_the_protocol_states_thirty_rules_once_each_in_order"
        status: pass
      - kind: unit
        ref: "tests/test_oper.py#test_the_protocol_table_gives_each_set_the_shape_and_counts_its_file_has"
        status: pass
    human_judgment: true
    rationale: "The tests pin that the rules exist and agree with the files. Whether each threshold and margin is the right rule is the owner's and Codex's judgment on PR A, and R30 freezes it after landing."
  - id: D6
    description: "The two older debt items the campaign leaves open each carry a dated disposition line and stay active; PR A (#22) is open"
    requirement: OPER-03
    verification:
      - kind: other
        ref: "git show HEAD:docs/tech_debt/active/<item>.md | grep '(plan 07-03)' for both items"
        status: pass
      - kind: other
        ref: "gh pr list --head gsd/phase-07-preregistration --state open --json number --jq length (1)"
        status: pass
    human_judgment: true
    rationale: "Review and landing of PR A is plan 07-04, a human checkpoint; the disposition wording is an owner-visible statement about older debt."
  - id: D7
    description: "A SIGSEGV below about 1e-8 mm is absorbed by the container and read as crashed on the GitHub runner"
    requirement: OPER-02
    verification:
      - kind: other
        ref: "python -m bench.oper point --kind probe --probe tail ... tail=1e-9 (emulated linux/amd64 on macOS arm64: crashed, exit 139, no number)"
        status: pass
    human_judgment: true
    rationale: "A path check on an emulated host (D-01); it proves the code path, not the hosted runner's behavior. Only the first dispatched walls run settles it."

duration: 39min
completed: 2026-10-27
status: complete
---

# Phase 7 Plan 03: Pre-registered sweep protocol, point sets and in-image probes Summary

**The whole phase 7 campaign is fixed before any runner reading: 30 rules in `07-SWEEP-PROTOCOL.md`, four deterministic point files (1692, 12, 681 and 69 points) that `make verify` byte-checks against their generator, `tail`, `naive` and `one_pipe` probes that run in the production image, and PR A (#22) open.**

## Performance

- **Duration:** 39 min
- **Started:** 2026-10-27T02:36:33Z
- **Completed:** 2026-10-27T03:15Z
- **Tasks:** 3
- **Files modified:** 12 on `gsd/phase-07-preregistration` (5 created including the protocol, 7 modified)

## Accomplishments

- **Probes in the image (Task 1, tracer).** `run_probe` builds the `tail` probe through the production gate with `MIN_TAIL_MM` lowered for the call and restored in a `finally`; `naive` and `one_pipe` apply no gate and report the solid count, `isValid()` and the signed precise-volume ratio. Any kernel exception, of any class, is a `refused` record with the class and the text. Path check in the emulated `screw:latest` (not a figure): tail 0.01 mm ended `ok` (ratio 1.0000002), tail 1e-9 mm ended `crashed` (exit 139, no number), `naive` (8, 1.25, 10) ended `ok` with ratio 0.2317 (macOS arm64 gives about a quarter of the closed form; linux/amd64 may raise, L11).
- **Point sets (Task 2).** `bench/oper_sets.py` writes `explore` (1692 points, 76 parts dropped), `spread` (12), `walls` (681) and `controls` (69), 617 KB together. The same code writes the same bytes, in the order it lists the points; `--check` names the first differing file. Every part point validates with `KINDS[kind].model_validate`; refused combinations are in `dropped` with `pitch_too_coarse` (42), `nut_too_thin` (18), `turn_cap` (15) and `less_than_equal` (1). 201 of the 294 catalogue rows have an integer `L / P` by exact decimals.
- **Protocol (Task 3).** R1 to R30 with the decision each applies, the explicit numbers (seed 20261026, the 10 % and 1.5x gzip thresholds, the 256 MiB and 64 MiB roundings, the 4 x 10^9-byte C2 allowance) each with its reason, and the disposition of the two older debt items.
- **PR A.** https://github.com/halfb00t/screw/pull/22, base `main`, head `40f667d843d9c83a0111890f95b0bfbdf4d0f2b3`. `git log origin/main..HEAD` is exactly the five 07-01 and 07-03 commits plus 07-01's two. Not landed (plan 07-04).

## Task Commits

All on `gsd/phase-07-preregistration` (worktree `.claude/worktrees/phase-07-preregistration`):

1. **Task 1: Tracer, tail and control probes in the production image** - `b529485` (feat)
2. **Task 2: Deterministic point-set generator and the four committed sets** - `1841593` (feat)
3. **Task 3: Protocol** - `b081610` (docs); **debt dispositions** - `02c18bc` (docs); **R19 reason** - `40f667d` (docs)

**Plan metadata:** the docs commit on `gsd/phase-07-operability-re-sweep` that adds this file.

## Tracer gate

Interactive, `end-of-phase`, the tracer's `<verify>` is `<automated>` only: re-ran `make test PYTEST_ARGS="tests/test_oper.py -q -n0 --no-cov"` after Task 1, 161 passed; expanded.

## TDD

Both `tdd="true"` tasks observed RED before GREEN and landed as one `feat` commit each, because the pre-commit hook runs the full `make verify` and cannot take a failing suite (same constraint as 07-01 and 07-02).

- **RED 1:** 42 tests failed on the planned behaviours (a probe point refused by the schema, `run_probe` missing, `parse_child_line` taking no `probe`).
- **RED 2:** against a skeleton `bench/oper_sets.py` returning no sets, 42 of 207 failed on the planned assertions (empty `generate()`, no `--check` text, no walls); `gsd_run check tdd-red-evidence` was not run (pytest console output is not a supported report format and no `tdd_mode` gate is configured).

## Files Created/Modified

- `bench/oper_child.py` - `run_probe`, `_probe_tail`, `_probe_naive`, `_probe_one_pipe`, probe `main` path
- `bench/oper.py` - probe points, `PROBE_ARGS`, probe-aware `parse_child_line`/`classify`/`summarize`, `point --kind probe --probe`, optional `dropped`/`notes`/`preset`, label unique per artifact
- `bench/oper_sets.py` - the generator and `--check`
- `bench/points/{explore,spread,walls,controls}.json` - the generated sets
- `tests/test_oper.py` - 51 new tests (212 in the file)
- `pyproject.toml` - `bench.oper_sets` in the kernel-free contract
- `.planning/phases/07-operability-re-sweep/07-SWEEP-PROTOCOL.md` - R1 to R30 (committed on the preregistration branch)
- two debt items - dated `(plan 07-03)` disposition lines

## Decisions Made

See `key-decisions`. The protocol additionally fixes, where the plan left it open: the cold wall is `build_s + export_s`; R5's margin is taken over it; `s` and `k` multiples of `d` are decimals rounded to 6 figures; the nut `m = X` ceiling pitch is rounded up so the void stays at or under 250 turns; R8 names the readings that bear on each field; R14 defines the bound point.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] The parent could not classify or summarize a probe**
- **Found during:** Task 1
- **Issue:** the plan says "nothing else changes in the parent". A probe has no export, so its ok line cannot carry `export_s` and `bytes`; inventing them would be a made-up number (L02), and `summarize`, `format_rows` and the markdown table would have raised `KeyError` on it. A negative `volume_ratio` (an inverted solid) would have been refused by the non-negative check.
- **Fix:** `parse_child_line(line, probe=...)` and `classify(..., probe=...)` hold an ok line to the fields of what was asked for; `volume_ratio` alone may be negative; `summarize` takes the median and max of `build_s` and `memory_peak_bytes` for a probe and the report prints a dash for what a probe does not have; `point` takes `--kind probe --probe NAME`.
- **Files modified:** `bench/oper.py`, `tests/test_oper.py`
- **Committed in:** `b529485`

**2. [Rule 1 - Bug in the plan's recipe] The root-radius pitch is not rounded to 6 figures**
- **Found during:** Task 2
- **Issue:** the plan solves the pitch for `d/2 - thread_depth(pitch) = r` and rounds it down to 6 significant figures "so the model accepts it". That moves the root radius by up to about 5e-6 mm at pitch 3.7, more than the 1e-6 mm end of the walk, so the radius in the label would not be the radius walked and R10's "the walk reached 1e-6" would be false.
- **Fix:** the pitch is solved to full float precision; the model accepts it (the realized root is the target to better than 1e-9 relative) and a test asserts every point's realized radius is within 1e-3 of its label.
- **Files modified:** `bench/oper_sets.py`
- **Committed in:** `1841593`

**3. [Rule 3 - Blocking] The loader refused the generator's own files**
- **Found during:** Task 2
- **Issue:** `load_set` required the exact key sets and unique labels. The generator adds `dropped`, `notes` and a per-point `preset`, and one part has three artifacts, so its label repeats.
- **Fix:** `dropped`, `notes` and `preset` are optional and type-checked; a label may be listed once per artifact. `tracer.json` still loads unchanged.
- **Files modified:** `bench/oper.py`, `tests/test_oper.py`
- **Committed in:** `1841593`

### Plan inconsistency, handled by the plan's own mechanism

The `<interfaces>` block gives the fourth recorded corner as `d=1e5, pitch=1, length=1` with `s=160000`, `k=60000`. `s` is bounded by `INTERIM_MAX_MM` (1e5) and must exceed `d`, so no `d` = 1e5 bolt exists (the interim-bounds debt item already says so). The point is generated as written and the model refuses it (`less_than_equal`), so it is in `explore.json`'s `dropped`, explained in its `notes`, and `walls` group (b) walks the largest legal `d` per decade (62500 at 1e5). Explore therefore holds three corners as points and one as a visible refusal. No acceptance criterion fails (the plan requires every dropped combination to be listed), but the owner may want to know the recorded corner is unreachable.

### Process notes

- No separate RED commit (see TDD). Not run: `gsd_run check tdd-red-evidence`.
- Task 1 step 4 (`make image`) was not run: `screw:latest` (id `fcbda84531b1...`, the one 07-01 used) already exists, the probes need nothing newer than the builder it contains, and `bench/` is mounted read-only into the container. The path check ran against it.
- The plan's `<automated>` commands use `make -C .claude/worktrees/phase-07-preregistration`, written for the main checkout; they were run from inside the worktree without `-C` (same checkout, same result).
- Commit trailer is `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`, as 07-01 and the session's attribution say; the dispatch note named a different model string.
- `commits: 5` is measured (`git rev-list --count 3c589d8..HEAD`); no `gsd-plan-head-before` ledger file was written in the worktree, so the base is 07-01's recorded `plan_head_after`.

---

**Total deviations:** 3 auto-fixed (1 missing critical, 1 bug in the plan's recipe, 1 blocking), 1 plan inconsistency surfaced, 5 process notes
**Impact on plan:** all inside the harness and generator; each keeps a number the run did not measure out of a record (L02). No scope creep.

## Issues Encountered

- Under emulation the tail 1e-9 mm probe ended `crashed` in 4.0 s and the tail 0.01 mm probe `ok` in 5.1 s; these are path checks, not figures, and no rule takes them.
- `naive` (8, 1.25, 10) built one valid solid at 0.2317 of the closed form on macOS arm64; the `test_the_naive_control_*` test accepts `ok` or `refused` because the same row may raise on linux/amd64 (L11 platform note).

## Verification

- `make verify` in the worktree before the last code-bearing commit (`02c18bc`): ruff, mypy `--strict`, import-linter (10 contracts kept), unfinished-work scan, pytest: `3940 passed in 174.98s (0:02:54)`, coverage 97.66 %. The same command passed in the pre-commit hook of all five commits.
- `python -m bench.oper_sets --check` prints `integer L/P: 201 of 294`, exit 0.
- Protocol headings: `git show HEAD:...07-SWEEP-PROTOCOL.md | grep -cE "^#+ R(1|...|30)\b"` prints 30.
- `gh pr list --head gsd/phase-07-preregistration --state open --json number --jq length` prints 1 (#22).

## Known Stubs

None.

## Threat Flags

None beyond the plan's register. T-07-07 (the `tail` probe crossing the SIGSEGV wall) is mitigated as planned: capped and deadlined container, `crashed` with no number, guard restored in a `finally` (tested). T-07-08 (rules tuned after data) is addressed by R30 and the order of the commits; T-07-09 (point files drifting) by the `--check` test in `make verify`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 07-04 lands PR A (#22), a human checkpoint: Codex review of the protocol first (R7 to R10 and R12 to R14 decide which numbers become bounds). The workflow cannot be dispatched until it is on `main`.
- Filed no debt or idea item; the unreachable fourth corner is already recorded in `2026-10-05-interim-runtime-bounds.md` and in `explore.json`'s notes.
- RESEARCH A2 (the hosted runner exposes cgroup v2 `memory.peak` to containers) is still unverified until the first dispatched run.

## Self-Check: PASSED

- FOUND: `bench/oper.py`, `bench/oper_child.py`, `bench/oper_sets.py`, the four point files, `tests/test_oper.py`, `pyproject.toml`, the protocol and both debt items (in the worktree)
- FOUND commits `b529485`, `1841593`, `b081610`, `02c18bc`, `40f667d` on `gsd/phase-07-preregistration`; `git rev-list --count 3c589d8..HEAD` is 5
- Task acceptance criteria re-run: all pass. Plan verification: `make verify` green, `--check` exit 0, 30 rule headings, PR #22 open

---
*Phase: 07-operability-re-sweep*
*Completed: 2026-10-27*
