---
phase: 07-operability-re-sweep
plan: 01
subsystem: testing
tags: [cgroup, memory.peak, docker, github-actions, workflow_dispatch, jsonl, bench]

requires:
  - phase: 06.1-bolt-head-chamfer
    provides: origin/main at cc6bccf, the base the preregistration branch is cut from
provides:
  - "bench.oper: kernel-free parent that takes one reading per fresh container of the production image and classifies it ok, capped, killed, crashed, refused or no_cgroup"
  - "bench.oper_child: in-image child, one cold build and export, cgroup v2 memory.peak or v1 max_usage_in_bytes, CgroupUnavailable otherwise"
  - "bench.cpu_model and bench.host_facts: the D-01 host facts; machine_facts names the CPU model"
  - "bench/points/tracer.json and the point-file schema (set, rule, reps, shards, deadline_s, points)"
  - ".github/workflows/operability.yml: dispatch-only runner workflow (plan job builds the matrix, measure job runs readings)"
  - "make bench.oper"
affects: [07-02, 07-03, 07-04, 07-05, operability, ci]

actuals:
  tokens: 18900
  tasks: 2
  commits: 2
plan_head_before: cc6bccfe82eb56e6122efb8e669dc30227533b9d
plan_head_after: 3c589d8e215e8372e57f394c021928696a2cfaee

tech-stack:
  added: []
  patterns:
    - "one fresh container per reading, no --rm, docker inspect OOMKilled then docker rm"
    - "a reading that is not ok carries a status and no figure (L02)"
    - "workflow input reaches scripts only through env, pinned by text tests"

key-files:
  created:
    - bench/oper.py
    - bench/oper_child.py
    - bench/points/tracer.json
    - tests/test_oper.py
    - .github/workflows/operability.yml
  modified:
    - bench/__init__.py
    - pyproject.toml
    - Makefile

key-decisions:
  - "Code lives on gsd/phase-07-preregistration (worktree .claude/worktrees/phase-07-preregistration, cut from origin/main), never on the phase branch, so the workflow can reach main before any runner figure exists"
  - "CAP_BYTES = 12 GiB per reading container on the 16 GB runner; DEADLINE_S = 600 per reading"
  - "The summary status of a point with unequal failures is mixed; a point with any non-ok repetition has no median and no max"

patterns-established:
  - "Parent/child split: stdlib-only parent on the runner's bare interpreter, kernel child inside the image"
  - "Point files validated against an exact key set; set name held to [a-z0-9-]+ and an existing file"

requirements-completed: [OPER-01, OPER-02]

coverage:
  - id: D1
    description: "A reading that is capped, killed, crashed, refused or cgroup-blind carries a status and no build seconds, export seconds, bytes or peak"
    requirement: OPER-02
    verification:
      - kind: unit
        ref: "tests/test_oper.py#test_a_reading_that_is_not_ok_carries_no_number"
        status: pass
      - kind: unit
        ref: "tests/test_oper.py#test_a_peak_one_byte_below_99_percent_of_the_cap_is_not_capped"
        status: pass
    human_judgment: false
  - id: D2
    description: "read_peak, parse_child_line, summarize, load_set, matrix and run behave as specified on synthetic input; bench.oper imports no screw module"
    requirement: OPER-01
    verification:
      - kind: unit
        ref: "tests/test_oper.py (115 tests)"
        status: pass
      - kind: other
        ref: "make verify: 3843 passed, 10 import contracts kept"
        status: pass
    human_judgment: false
  - id: D3
    description: "The tracer reading (default bolt, preview STL) ends ok with an integer memory_peak_bytes in an emulated linux/amd64 screw:latest on macOS arm64"
    requirement: OPER-02
    verification:
      - kind: other
        ref: "python -m bench.oper point --kind bolt --params '' --artifact stl-preview --image screw:latest --reps 1 --out -"
        status: pass
    human_judgment: true
    rationale: "Path check on an emulated host (D-01): proves the code path, not that the GitHub runner exposes cgroup v2 memory.peak to containers (RESEARCH A2). Only the first dispatched run on the runner settles that."
  - id: D4
    description: "operability.yml is dispatch-only, read-only, names no secret, and hands the set input to scripts only through env"
    requirement: OPER-01
    verification:
      - kind: unit
        ref: "tests/test_oper.py#test_the_set_input_reaches_a_script_only_through_an_env_variable"
        status: pass
    human_judgment: true
    rationale: "GitHub starts a workflow_dispatch run only for a file on the default branch, so the workflow has never run; the text pins pass, the first real dispatch (after PR A lands) is the proof."

duration: 28min
completed: 2026-10-26
status: complete
---

# Phase 7 Plan 01: Runner Harness Tracer Summary

**One measurement point travels the whole path: point file, fresh container of the production image under a 12 GiB cap, cold build and export, cgroup memory.peak, JSONL record with host facts, median and max, and a dispatch-only GitHub workflow that runs it.**

## Performance

- **Duration:** 28 min
- **Started:** 2026-10-26T20:00:19Z
- **Completed:** 2026-10-26T20:28:07Z
- **Tasks:** 2
- **Files modified:** 8 (5 created, 3 modified) on `gsd/phase-07-preregistration`

## Accomplishments

- `bench.oper` (stdlib only, kernel-free) takes a reading per fresh container: `--memory` and `--memory-swap` at `CAP_BYTES`, no `--rm`, `docker inspect` for `OOMKilled`, then `docker rm -f`. It classifies `ok`, `capped` (OOMKilled, peak at or above 99 % of the cap, or a cgroup `oom_kill`), `killed` (past `DEADLINE_S`), `crashed` (any non-zero exit or no valid line, with exit code and stderr tail), `refused` (BuildError class) and `no_cgroup`. Only a clean `ok` keeps build seconds, export seconds, bytes and peak.
- `bench.oper_child` runs inside the image: one cold build, one export, then cgroup v2 `memory.peak` (when `/sys/fs/cgroup` is a `cgroup2` mount) or v1 `memory.max_usage_in_bytes`; anything unreadable raises `CgroupUnavailable` and the reading has no peak.
- Host facts (nproc, MemTotal bytes, CPU model, kernel, image id, image kernel pair, run id, job, sha when set) and `load1` per reading, so a runner figure names the machine behind it.
- `matrix`, `run` and `summarize` (plain and `--markdown`) over point files; the set name is held to `[a-z0-9-]+` and an existing file, the file to its exact schema.
- `operability.yml` (plan job, measure job) pinned by 115 tests in `tests/test_oper.py`; `make bench.oper`; `bench.oper` joins the kernel-free import contract.

### Tracer reading: emulated linux/amd64 on macOS arm64, path check, not a figure (D-01)

Taken with `python -m bench.oper point --kind bolt --params "" --artifact stl-preview --image screw:latest --reps 1 --out -` (OrbStack, `DOCKER_DEFAULT_PLATFORM=linux/amd64`, load1 4.7). Nothing here is committed as a figure or sets a bound.

```
{"type": "header", "image": "screw:latest", "image_id": "sha256:fcbda84531b197e8649578f69765b5f2597ef929b47f75b0723014276873fc90", "versions": {"cadquery": "2.8.0", "cadquery_ocp": "7.9.3.1.1"}, "nproc": 18, "mem_total_bytes": null, "cpu_model": null, "kernel": "27.0.0", "machine": "arm64"}
{"type": "reading", "label": "default-bolt", "kind": "bolt", "params": {}, "artifact": "stl-preview", "rep": 1, "load1": 4.671875, "container": "screw-oper-28522-1", "status": "ok", "build_s": 1.8495003200368956, "export_s": 0.2701045669382438, "bytes": 1587384, "triangles": 31746, "gzip1_bytes": 701631, "maxrss_bytes": 884162560, "memory_peak_bytes": 579043328, "oom_kills": 0, "cadquery": "2.8.0", "cadquery_ocp": "7.9.3.1.1", "wall_s": 6.583163416013122}
```

A second reading of the same point through `bench.oper run --set tracer --shard 1 --rep 3` ended `ok` with `memory_peak_bytes` 1430880256, 2.5 times the first. Under emulation one reading is not a measurement of the part; that is the reason D-04 takes 5 repetitions and bounds from the max.

The header describes the macOS Docker client (arm64, kernel 27.0.0, no `/proc`, so `mem_total_bytes` and `cpu_model` are `null`), not the emulated container. On the runner the container shares the host kernel and CPU, so the facts coincide there. `null` is deliberate: an absent fact is unknown, not guessed (L02).

## Task Commits

All on `gsd/phase-07-preregistration` (worktree `.claude/worktrees/phase-07-preregistration`), cut from `origin/main` cc6bccf. Nothing is pushed.

1. **Task 1: Tracer, the default bolt's preview STL measured in one container of the production image** - `8be1b6d` (feat)
2. **Task 2: The dispatchable workflow, the tracer point file, the make target and the workflow pins** - `3c589d8` (feat)

**Plan metadata:** recorded in the docs commit on `gsd/phase-07-operability-re-sweep` that adds this file.

## Files Created/Modified

- `bench/oper.py` - the parent: `CAP_BYTES`, `DEADLINE_S`, `is_capped`, `parse_child_line`, `classify`, `reading_argv`, `run_reading`, `load_set`, `shard_points`, `summarize`, `markdown_report`, and the `point`, `run`, `matrix`, `summarize` CLI
- `bench/oper_child.py` - the in-image child: `CgroupUnavailable`, `read_peak`, `oom_kills`, `main`
- `bench/__init__.py` - `cpu_model`, `host_facts`; `machine_facts` names the CPU model
- `bench/points/tracer.json` - the one-point tracer set, 5 repetitions, 1 shard, rule `07-SWEEP-PROTOCOL.md R2`
- `.github/workflows/operability.yml` - dispatch-only workflow
- `tests/test_oper.py` - 115 synthetic tests (one real-kernel child build)
- `pyproject.toml` - `bench.oper` in the kernel-free import contract
- `Makefile` - `bench.oper` target

## Decisions Made

- `CAP_BYTES = 12 * 1024**3`: leaves 4 GiB of the 16 GB runner for the OS, dockerd and the parent. Undersized is visible, because a capped reading has no number.
- The peak is read right after the export and before the child's gzip, because the production gzip runs in the serving process, not in the worker.
- The versions of the kernel pair come from the child when it can report them and from the header's one probe container otherwise, so a killed or crashed reading still names them.
- A non-zero exit, even after a valid line, is `crashed`: no figure from a process that died.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] A cgroup-counted OOM kill makes an ok line `capped`**
- **Found during:** Task 1 (classify)
- **Issue:** the plan classifies capped by Docker's `OOMKilled` or the 99 % peak. A child that survived while a process in its cgroup was OOM-killed would still print a plausible peak.
- **Fix:** `classify` also treats `oom_kills > 0` from `memory.events` as `capped`.
- **Files modified:** `bench/oper.py`
- **Verification:** `tests/test_oper.py::test_a_reading_that_is_not_ok_carries_no_number` and the `oom_kills` reader tests
- **Committed in:** 8be1b6d

**2. [Rule 2 - Missing Critical] `summarize` of a missing file is a message and exit 1**
- **Found during:** Task 2 (workflow summary step runs `if: always()` on a red run whose JSONL may not exist)
- **Fix:** `_cmd_summarize` catches `OSError` and prints `oper: cannot read <file>`; the workflow's summary step is `continue-on-error: true` because an empty shard has no readings and `summarize` exits 1 on that by design.
- **Files modified:** `bench/oper.py`, `.github/workflows/operability.yml`
- **Committed in:** 3c589d8

**3. [Rule 3 - Blocking] ruff TRY004 on type checks that must raise `ValueError`**
- **Found during:** Task 1 (`make verify`)
- **Fix:** one `_refuse(message) -> NoReturn` helper raises every `ValueError` of the child-line and point-file parsers; behavior unchanged.
- **Files modified:** `bench/oper.py`
- **Committed in:** 8be1b6d

**4. [Rule 2 - Missing Critical] `--label` on the `point` command**
- **Found during:** Task 1 (summarize groups by label)
- **Fix:** `point` takes `--label` (default `point`) so an ad-hoc point groups in `summarize`.
- **Committed in:** 8be1b6d

### Process note: no separate RED commit

`make verify` runs in the pre-commit hook, so a commit of failing tests cannot land. RED was run and observed but not committed: Task 1's `tests/test_oper.py` failed at collection on the missing modules (`ImportError: cannot import name 'oper' from 'bench'`), and Task 2's additions failed 48 of 115 (`AttributeError`/`FileNotFoundError` on the missing `load_set`, `matrix`, workflow and make target). The plan prescribes one `feat(bench): ...` commit per task, so there is no `test(07-01)` commit.

---

**Total deviations:** 4 auto-fixed (3 missing critical, 1 blocking), 1 process note
**Impact on plan:** All four are inside the harness and strengthen "no number it did not measure". No scope creep.

## TDD Gate Compliance

Task 2 carries `tdd="true"`. RED was observed (48 failing of 115, semantic: the named behaviors did not exist) and GREEN passed, but the RED state was never committed because the hook blocks a failing commit. `git log --grep='^test(7-1)'` finds nothing; this section is the flag the gate asks for. The RED evidence was not run through `gsd_run check tdd-red-evidence` (no supported report format was captured).

## Issues Encountered

- The first import of cadquery in the fresh worktree venv took about 100 s inside the one real-kernel test (cold bytecode and disk cache); the second run took 2 s. Later runs are not slow.
- Under emulation the same point's peak differed 2.5 times between two readings (579 MB, 1.43 GB), and `ru_maxrss` (884 MB) exceeded the cgroup peak on the first. Both are emulation artefacts to be re-read on the runner; neither is a figure.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Branch `gsd/phase-07-preregistration` is at `3c589d8`, unpushed. Plan 07-03 adds `07-SWEEP-PROTOCOL.md` (named by `tracer.json`'s `rule`) and opens PR A. The workflow cannot be dispatched until that lands on `main`.
- RESEARCH A2 (the hosted runner exposes cgroup v2 `memory.peak` to containers) stays unverified until the first dispatched run; the harness fails loudly with no number if it does not.
- The `.claude/worktrees/phase-07-preregistration` worktree and its own `.venv` stay in place for the next plans.

## Self-Check: PASSED

- FOUND: `bench/oper.py`, `bench/oper_child.py`, `bench/points/tracer.json`, `tests/test_oper.py`, `.github/workflows/operability.yml` (in the worktree)
- FOUND commits `8be1b6d`, `3c589d8` on `gsd/phase-07-preregistration`; `git rev-list --count cc6bccf..HEAD` is 2
- Task acceptance criteria re-run: all pass. Plan verification: `make verify` in the worktree, 3843 passed, 10 import contracts kept, coverage 97.66 %

---
*Phase: 07-operability-re-sweep*
*Completed: 2026-10-26*
