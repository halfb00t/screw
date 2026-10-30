---
phase: 07-operability-re-sweep
plan: 17
subsystem: infra
tags: [operability, runtime, docker, compose, mem_limit, tmpfs, healthcheck, decision-log, timeouts, bench, debt, R16, R24, R25, R26, D-02, D-03, D-09, D-10, D-11, D-14, D-16]
status: complete

requires:
  - phase: 07-operability-re-sweep
    provides: "07-16 bench/results/phase-07/runtime.json and calc.cost.BUILD_TIMEOUT_S; 07-21 the serving and worker knobs and tests/test_runtime_bounds.py; 07-14 the debounce relabelled a UI choice"
provides:
  - "compose.yaml: SCREW_BUILD_WORKERS 1, mem_limit 2304m (2415919104 B), tmpfs /tmp 256m, SCREW_WORKERS 1, each citing rule, runs and inputs"
  - "Dockerfile: HEALTHCHECK --timeout 2s and --start-period 10s (R25), interval 30s and retries 3 cited as Docker's defaults; ENV SCREW_WORKERS=1 (R24)"
  - "decision log L23 (the measured runtime) and L24 (the per-artifact timeouts, the queue-aware deadline, the miss record, Retry-After, no override); L09 notes it is superseded in part"
  - "tests/test_runtime_bounds.py: container values equal runtime.json; every shipped value equal to its L23/L24 row as the code writes it; every cited run id has its RESULTS.md section; no INTERIM or Phase 7 re-sweep shipped; no SCREW_BUILD_TIMEOUT in src/, bench/, the Makefile or bench/README.md"
  - "bench.build_time: each artifact's cold wall judged against BUILD_TIMEOUT_S for that artifact, cost-model-refused artifacts shown and not judged, no --timeout"
affects: [07-18, 07-19, 07-20]

estimate:
  tokens: 110000
  tasks: 3
actuals:
  tokens: 11258      # chars/4 over the added lines of the plan's diff, 00b0259..530adbe (45032 chars)
  tasks: 3
  commits: 3         # MEASURED: git rev-list --count 00b0259..530adbe (this SUMMARY's commit not counted)
plan_head_before: 00b025946a5e5c7817e469cb5d07b4217bada7a1
plan_head_after: 530adbef3f989af31d16e23a0f7083334de42a5f

tech-stack:
  added: []
  patterns:
    - "container files are read as text with a regex and held to runtime.json; no YAML parser is added"
    - "a decision log entry's knob table is machine-checked: column 3 is the value as the code writes it"
    - "a run id is any 11-digit number from 3e10 to 5e10 in the scanned text; each must have its own '### <set>, run <id>' section in bench/RESULTS.md"

key-files:
  created:
    - .planning/phases/07-operability-re-sweep/07-17-SUMMARY.md
  modified:
    - compose.yaml
    - Dockerfile
    - docs/architecture/decision_log.md
    - docs/architecture/overview.md
    - tests/test_runtime_bounds.py
    - bench/build_time.py
    - bench/README.md
    - bench/corpus.py
    - bench/thread_spike/verdict.py
    - Makefile
    - tests/test_bench.py
    - docs/tech_debt/INDEX.md
    - docs/tech_debt/resolved/2026-10-05-interim-runtime-bounds.md
    - docs/tech_debt/resolved/2026-10-06-bench-memory-sampling-is-too-coarse-for-short-corpora.md
    - docs/tech_debt/resolved/2026-10-11-default-pitch-d100-length200-exceeds-both-interim-backstops.md

key-decisions:
  - "The plan's L22 and L23 are L23 and L24: L22 was already taken by 07-15 for the G30 widening and the turns refusal (orchestrator note 1)"
  - "compose mem_limit is 2304m, which docker compose config resolves to 2415919104, runtime.json's mem_limit_bytes; the tmpfs stays 256m, now cited to R26"
  - "bench.build_time shows an artifact the cost model refuses and does not judge it against a timeout or count it in the exit code: the service answers it with a 422 before any build (L21)"
  - "The interim-bounds item's 350 ms debounce row is withdrawn as stale: a UI choice that bounds no build, relabelled by 07-14 (717f333)"

requirements-completed: []   # OPER-01 waits on the full grid (07-18, 07-19); 07-20 proves OPER-02 on the runner

metrics:
  duration: "09:33Z to 10:05Z on 2026-10-30, about 32 min"
  completed: 2026-10-30
---

# Phase 7 Plan 17: the container's measured values, L23 and L24, and the last interim labels gone Summary

**compose and the Dockerfile now ship runtime.json's values, each citing its rule and run: 1 build
worker, mem_limit 2304m (2415919104 B), a 256m tmpfs, 1 server process, and a healthcheck with a
2 s timeout and a 10 s start period. L23 logs the measured runtime and L24 the per-artifact
timeouts, the queue-aware deadline, the miss record and Retry-After. A test ties every shipped value
to its log row and every cited run to its RESULTS.md section. `SCREW_BUILD_TIMEOUT` is gone from the
bench, and the three debt items that waited on this are resolved.**

## Commits

| # | sha | subject |
| --- | --- | --- |
| 1 | 83976da | feat(docker): measured mem_limit, tmpfs, workers and healthcheck timings (07 D-02, D-03) |
| 2 | 85b400d | docs(07): log the measured runtime as L23 and the timeouts as L24 |
| 3 | 530adbe | chore(07): remove the last interim runtime labels and close the debt they tracked (07 D-16) |

Each subject is the plan's, except that Task 2's says L23 and L24 (deviation 1).

## Task 1: the container values

| value | was | now | runtime.json key |
| --- | --- | --- | --- |
| compose `SCREW_BUILD_WORKERS` | "2" (INTERIM) | "1" | `picked_workers` |
| compose `mem_limit` | 4g (INTERIM) | 2304m = 2415919104 B | `mem_limit_bytes`, `shipped_mem_limit.bytes` |
| compose tmpfs `/tmp` | 256m (INTERIM) | 256m = 268435456 B | `tmpfs_bytes` |
| compose `SCREW_WORKERS` | "1" (INTERIM) | "1" | `screw_workers.workers` |
| Dockerfile `ENV SCREW_WORKERS` | 1 (INTERIM) | 1 | `screw_workers.workers` |
| HEALTHCHECK `--timeout` | 2s (INTERIM) | 2s | `healthcheck.timeout_s` |
| HEALTHCHECK `--start-period` | 30s (INTERIM) | 10s | `healthcheck.start_period_s` |
| HEALTHCHECK `--interval`, `--retries` | 30s, 3 | 30s, 3, cited as Docker's documented defaults | `healthcheck.interval_s`, `retries` |

- **mem_limit comment.** It carries R16 and G20's formula and every input from runtime.json: W
  1758363648 B (drift-60 run 41022812680), B 65208320 B, the load peak 1657307136 B (load run
  40909724292), the export cache 251658240 B, the tmpfs 268435456 B and W(4) 1652121600 B (run
  41016510597).
- **The two ceilings.** mem_limit is under 16 x 10^9 B and under the smallest runner MemTotal,
  16758394880 B. The test asserts both.
- **No hand-typed figure.** Every figure in the comments is a runtime.json value. `2304m` and
  `256m` are those byte values in MiB, and the test converts them back.
- **Checks run.**
  - `docker compose config` prints `mem_limit: "2415919104"`.
  - `make image smoke` passed; the log is in the scratchpad as `image-0717.log`.
  - `docker inspect screw:latest` shows Interval 30 s, Timeout 2 s, StartPeriod 10 s, Retries 3
    and `SCREW_WORKERS=1`.

## Task 2: L23 and L24

**L23, the measured runtime.** It records:
- the host facts: 254 headers, nproc 4, the smallest MemTotal, the kernel, cadquery and the six
  CPU models seen in Runs II;
- the 5-repetition rule;
- the D-19 margin (0.5382691940004687, spread run 40646125666) and every set's shard count;
- the per-N load table, with the pick N = 1;
- the W, B and G20 derivation of mem_limit;
- a 16-row knob table, R15 to R26, each row with its rule, evidence and runs. Column 3 is the value
  as the code writes it.

It supersedes L09's interim paragraph and the values carried from spur L17 and L19.

**L24, the timeouts.** It records:
- the per-artifact table: `BUILD_TIMEOUT_S` 26.0, 71.0 and 26.0 s, each artifact's bound point,
  max cold wall and reading, and `MEDIAN_BUILD_S`;
- D-09's x2 factor;
- the D-14 formula, `deadline = BUILD_TIMEOUT_S[artifact] + ` the timeouts queued ahead on the
  slot, named the second divergence from spur's pool.py after L09's guard;
- the `cost_model.miss` record (D-10);
- `Retry-After = max(1, ceil(median x live depth))` (D-11);
- no override, with `SCREW_BUILD_TIMEOUT` removed (D-16).

**Other edits.**
- L09 gains a "Superseded in part by L23 and L24" line, following the L11 and L12 convention.
- overview.md: the `pool` row says "a per-artifact timeout with a queue-aware deadline (L24)". The
  `app` row names the measured Retry-After and the `cost_model.miss` record.

**Generated, not typed.** The figures in both entries were formatted from runtime.json by a
scratchpad script, so none is hand-typed. The tests hold them:
- `test_every_shipped_runtime_value_is_in_l23_as_the_code_writes_it`;
- `test_every_timeout_and_retry_after_median_is_in_l24_as_the_code_writes_it`;
- `test_every_run_id_the_code_and_l20_to_l24_cite_has_its_section_in_results`. It covers 17 run
  ids, each with its own `### <set>, run <id>` heading.

## Task 3: bench, the scans, the debt

**`bench.build_time`.**
- It times the preview STL as well as the fine STL and STEP after one cold build.
- `Timing.cold_wall(artifact)` is the build plus that artifact's export, R2's cold wall.
- `over_timeout()` lists the admitted artifacts past `BUILD_TIMEOUT_S[artifact]`. A wall exactly
  at the timeout counts as inside.
- The report prints the three timeouts, a verdict cell per artifact and the heaviest part per
  artifact.
- `--timeout` and the `int_env("SCREW_BUILD_TIMEOUT", 30)` default are gone. A real run on two
  parts printed and exited as designed.

**Docs.** The Makefile help, bench/README.md and the corpus docstring now cite L24 and say three
things:
- The corpus holds no entry the parameter model refuses.
- Its last length has been 90 mm since a804806, so heaviest-part runs from before that commit are
  not comparable (owner ruling 2026-10-28).
- The cost model refuses some entries at some artifacts, and those artifacts are marked, not
  judged.

verdict.py's comment says `(history: removed by L24)`.

**The static scans.**
- No `INTERIM` and no `Phase 7 re-sweep` in any .py, .js, .html or .css under src/, in the
  Dockerfile or in compose.yaml. app.js is asserted to be in the scan.
- No `SCREW_BUILD_TIMEOUT` in src/ or bench/ .py files, bench/README.md or the Makefile. The one
  exception is verdict.py's history line. bench/RESULTS.md and bench/results/ are run records and
  are not scanned.

**Debt resolved in 530adbe.** For each item: Status flipped, `Resolved in:` added, `git mv`, INDEX
row moved.
- `docs/tech_debt/resolved/2026-10-05-interim-runtime-bounds.md`. Every table row now names L20,
  L21, L23 or L24, with its run. The debounce row is withdrawn as stale (orchestrator note 4). The
  Phase 3 in-cap cost examples are now 422s at validation (250 turns, d 1e5), checked against
  `BoltParams`.
- `docs/tech_debt/resolved/2026-10-11-default-pitch-d100-length200-exceeds-both-interim-backstops.md`
  (WR-05). The request is a `turn_cap` 422: 200 turns against `MAX_TURNS` 90 (L20), checked
  against `BoltParams`. Neither L21's cost model nor L24's timeout is reached. The corpus's
  heaviest part is d=100 length=90 since a804806 (owner ruling 2026-10-28). The kill-point
  measurement is withdrawn.
- `docs/tech_debt/resolved/2026-10-06-bench-memory-sampling-is-too-coarse-for-short-corpora.md`.
  mem_limit comes from cgroup `memory.peak` read by `bench.oper_child.read_peak`: in part,
  contention and drift readings (`bench.oper_bound`) and in the load run (`bench.oper_load`). See
  L23. `bench.memory` stays the sampled harness and sets no bound.

## Deviations from Plan

### Auto-fixed issues

**1. [Orchestrator note 1] Decision log numbering.** L22 was already taken by 07-15, so the plan's
L22 and L23 are L23 and L24 everywhere: the tests, the comments, the debt resolutions, verdict.py's
"(history: removed by L24)", Task 2's commit subject and this SUMMARY. L21 and L22 are untouched.

**2. [Rule 2 - Missing critical functionality] bench.build_time does not judge refused artifacts.**
- **Found during:** Task 3.
- **Issue:** at HEAD, `cost.fits` refuses 11 of the 12 corpus entries at one artifact or more, for
  example d=6 length=20 s=12 k=3 at all three. A timeout verdict there would describe a request
  the service answers with a 422 and never builds (L21), and an overrun would fail the run for a
  timeout that cannot occur.
- **Fix:** `Timing.refused` holds the refused artifacts, which the report prints as
  `refused (L21)`. They are left out of `over_timeout()` and the exit code.
- **Tests:** `test_an_artifact_the_cost_model_refuses_is_never_held_to_a_timeout` and
  `test_main_fails_only_on_an_admitted_export_past_its_timeout`.
- **Commit:** 530adbe.

**3. [Rule 3 - Blocking] ruff PT018 in the new run-id test.** The first try of commit 2 failed the
gate. The assertion was split and the commit landed green. The tree was never committed red.

### Interpretation

**4. Run ids for the run-id test.** A run id is matched as an 11-digit number starting with 3 or 4.
No byte figure in the scanned text reaches 3e10, and the one 11-digit byte figure, MemTotal
16758394880, starts with 1. Each id must have a `### ..., run <id>` heading, which is stricter than
appearing anywhere in RESULTS.md.

**5. The INTERIM scan's RED came from Task 1.** Task 1's commit removed the last labels, so Task 3's
INTERIM scan passed as soon as it was written. Its SCREW_BUILD_TIMEOUT scan and the bench tests
were red (8 failed) before the bench change.

**6. "No entry the model refuses".** The bench docs say no entry the *parameter* model refuses.
The cost model refuses most entries at some artifact, and the docs say so without a count, so the
text does not drift when the envelope moves.

**7. Old references left as written.** L09, L12, L13, RESULTS.md and three resolved items still
name `active/2026-10-05-interim-runtime-bounds.md`. That follows the precedent: L21 still names
the head-ratio item under active/.

## Verification

- `make test PYTEST_ARGS="tests/test_runtime_bounds.py -q -n0 --no-cov"`:
  - 24 passed after Task 1 (3 failed at RED);
  - 27 passed after Task 2 (3 failed at RED).
- `make test PYTEST_ARGS="tests/test_runtime_bounds.py tests/test_bench.py -q -n0 --no-cov"`: 505
  passed after Task 3 (8 failed at RED).
- `make image smoke`: exit 0. The last line is "smoke: kernel, exports, ASGI stack and validation
  all live".
- The debt-move loop exits 0.
- `git grep -n INTERIM -- src Dockerfile compose.yaml` prints nothing.
  - The plan's literal `grep -rn INTERIM src Dockerfile compose.yaml` also hits two gitignored
    `src/screw/__pycache__/*.cpython-314.pyc` files dated 2026-10-06, stale bytecode from a
    Python 3.14 interpreter. They are not in the repo; I left them in place.
- `grep -c INTERIM Dockerfile compose.yaml`: 0 and 0. `grep -c "mem_limit: 4g" compose.yaml`: 0.
- `make verify` at 530adbe: `4571 passed in 187.24s (0:03:07)`, coverage 97.70 %, 10 contracts
  kept, mypy clean.

## For the owner

**The corpus.** `cost.fits` refuses 11 of the 12 bench corpus entries at one artifact or more,
because `s = 2 d` and `k = d / 2` are harness inputs. An M6 at s 12, k 3 and a 20 mm thread is
refused at all three artifacts. That is L21/L22's rule acting as ruled (k/d 0.5 is below the band).
The harness now says so instead of judging those walls. Nothing was changed in the model.

## Known Stubs

None.

## Threat Flags

None. T-07-42 is mitigated: mem_limit and the tmpfs equal runtime.json, and mem_limit is under
16 x 10^9 B and MemTotal, all tested. T-07-43 is mitigated by the L23/L24 consistency tests, the
run-id test and the INTERIM scan. T-07-SC holds: no package was added.

## Debt

- Filed: none.
- Resolved: the three items above, with their resolved/ paths.

## Self-Check: PASSED

- All 15 modified files and this SUMMARY exist. The three items are in resolved/ and absent from
  active/.
- 83976da, 85b400d and 530adbe are ancestors of HEAD.
