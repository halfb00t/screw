---
phase: 01-runtime-port-and-walking-skeleton
plan: 08
subsystem: testing
tags: [bench, harness, latency, memory, docker-stats, gzip, stl, httpx2]

requires:
  - phase: 01-runtime-port-and-walking-skeleton
    provides: "screw.solid's public build/export/clear_cache/TESSELLATION, the pooled service with /api/health and /api/bolt/model.stl (01-01..01-05), compose.yaml and the image (01-06)"
provides:
  - "bench/ package (corpus, build_time, export_cost, latency, memory) ported from spur with its method, typed under mypy --strict and covered by make typecheck"
  - "make bench, bench.build, bench.export, bench.latency, bench.memory; SWEEP and SET variables"
  - "bench/RESULTS.md: one labelled run of each of the four harness halves on the walking skeleton, each as a harness check and not a bound (L07)"
  - "tests/test_bench.py: 25 predicate tests, part of the gate"
  - "a tech-debt item for bench.memory's sampling limit, triggered by the Phase 7 memory sweep"
affects: [phase-02 (re-uses the harness on threaded parts), phase-07 (OPER-01..03 re-sweep on linux/amd64 replaces the corpus and sets the bounds)]

actuals:
  tokens: 24000
  tasks: 2
  commits: 7
plan_head_before: 3fbb241656f424b3d5e75f51e504249afaa6e375
plan_head_after: 469c8ed0a33f3348103e15d55e98ae89a81b4c6f

tech-stack:
  added: []
  patterns:
    - "the harness is ported with its method and its predicates tested; the numbers it prints are never carried over or promoted to bounds"
    - "a measuring client (bench.latency) imports no kernel: label() lives in bench.corpus, not in the module that imports screw.solid"
    - "a figure refused rather than invented: a p95 over fewer than 20 samples, an empty sweep, a capped memory row and an STL whose length disagrees with its header all print a warning and no number"

key-files:
  created:
    - bench/__init__.py
    - bench/corpus.py
    - bench/build_time.py
    - bench/export_cost.py
    - bench/latency.py
    - bench/memory.py
    - bench/README.md
    - bench/RESULTS.md
    - tests/test_bench.py
    - docs/tech_debt/active/2026-10-06-bench-memory-sampling-is-too-coarse-for-short-corpora.md
  modified:
    - Makefile
    - docs/tech_debt/INDEX.md

key-decisions:
  - "No bar is set for the latency ratio: spur's 2.00x pass bar and its recorded gear baseline are dropped, because screw has no baseline and L07 ports the harness, not the numbers"
  - "bench.memory publishes the container with docker compose run -p on the host port of --base-url instead of --service-ports, so a host whose 8000 belongs to another project can still run it"
  - "label() lives in bench.corpus so bench.latency stays free of screw.solid and so of the CAD kernel"
  - "the skeleton corpus is d in {2, 6, 20, 100} x length in {5, 20, 200}; the concurrent latency scenario takes the first ten parts so it never builds the single scenario's part (a cache hit would make the second scenario measure nothing)"

patterns-established:
  - "Every recorded run carries machine, load, date, HEAD and what it was run against, plus a paragraph of what it does not show"
  - "A run from a harness build that did not print the load is repeated rather than annotated by hand"

requirements-completed: [INFR-01]

coverage:
  - id: D1
    description: "bench.build and bench.export run in-process on the skeleton corpus through screw.solid's public surface only, and their predicates (STL sizing, the L19 selection rule at both bars, ru_maxrss units, empty-sweep refusal, the load the report was given) are tested"
    requirement: INFR-01
    verification:
      - kind: unit
        ref: "tests/test_bench.py (25 passed in make verify: 285 passed)"
        status: pass
      - kind: other
        ref: "make bench.build (exit 0, 12 rows, load line before the first row); make bench.export SET=\"d=100 length=200\" (exit 0)"
        status: pass
      - kind: other
        ref: "! grep -rnE 'solid\\._[a-z]' bench (no match)"
        status: pass
    human_judgment: false
  - id: D2
    description: "bench.latency reports idle and under-load /api/health p95 for the single and concurrent scenarios against a fresh skeleton server, and records 503s by the reason the server gave"
    requirement: INFR-01
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_a_503_is_recorded_by_the_reason_the_server_gave, #test_a_p95_over_too_few_samples_is_refused_with_a_warning, #test_the_latency_report_counts_what_the_server_answered_and_sets_no_bar"
        status: pass
      - kind: other
        ref: ".venv/bin/python -m bench.latency --base-url http://127.0.0.1:8001 (exit 0, both scenarios, recorded in bench/RESULTS.md)"
        status: pass
    human_judgment: false
  - id: D3
    description: "bench.memory sweeps SCREW_BUILD_WORKERS 1, 2, 4 over the corpus under its own ceiling, reports a capped row with no peak number, and leaves no container behind"
    requirement: INFR-01
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_a_peak_equal_to_the_ceiling_is_capped, #test_the_tolerance_boundary_is_pinned_from_both_sides, #test_the_container_is_published_on_the_host_port_the_base_url_names"
        status: pass
      - kind: other
        ref: ".venv/bin/python -m bench.memory sweep --base-url http://127.0.0.1:8001 (exit 0, 3 rows, 0 failures; docker ps and docker network ls show no screw container or network afterwards)"
        status: pass
    human_judgment: false
  - id: D4
    description: "every figure in bench/RESULTS.md is labelled a harness check, not a bound, with machine, load, date and the emulation caveat for container figures; the memory figures are not a footprint"
    requirement: INFR-01
    verification: []
    human_judgment: true
    rationale: "whether the wording of each entry keeps a harness check from being read as a bound is a judgment no test asserts"

duration: 17min
completed: 2026-10-06
status: complete
---

# Phase 1 Plan 8: Bench Harness Summary

**spur's bench harness ported to screw and run once against the walking skeleton: build/STL/STEP time and the L19 gzip and L24 mesh-copy table in-process, `/api/health` latency on the host, and the N=1,2,4 container memory sweep, every figure recorded as a harness check and none as a bound**

## Performance

- **Duration:** 17 min
- **Started:** 2026-10-06T05:41:00Z (approximate; the start time was not captured at launch)
- **Completed:** 2026-10-06T05:58:00Z
- **Tasks:** 2
- **Files modified:** 12 (10 created, 2 modified; `.planning/` bookkeeping not counted)

## Accomplishments

- `bench/` ported with the method intact: a `d x length` corpus of 12 plain cylinders, `bench.build_time`, `bench.export_cost`, `bench.latency`, `bench.memory`, a README and `RESULTS.md`; `bench/` imports no private name of `screw.solid` and `make typecheck` covers it.
- All four halves ran on this host and are recorded verbatim in `bench/RESULTS.md`, each with machine, load, date, HEAD and a paragraph saying what the run does not show. Nothing was carried over from spur and nothing is presented as a bound.
- `tests/test_bench.py` (25 tests, in the gate) pins the corpus, sweep loading that names a bad set, STL sizing, the empty-sweep and too-few-samples refusals, the L19 rule at both bars, the `ru_maxrss` unit split, 503 reasons, the capped-row predicate and its boundary, and the container publish port.
- Host left clean: no screw container, network or server process remained; the other project's container on 8000 was never touched.

## Task Commits

1. **Task 1 (TDD): in-process harness** - RED `a931298` (test; 15 tests, strict xfail), GREEN `8bb2398` (feat), results `7388183` (docs)
2. **Task 2: service harness** - `26bf992` (feat), results `b1f4cb3` (docs)
3. **Tech debt item and results labelling** - `2a2a0cd` (docs), `469c8ed` (docs)

**Plan metadata:** the docs commit that carries this SUMMARY, STATE.md, ROADMAP.md and REQUIREMENTS.md follows.

## What ran, and what the figures are

All on one host: Apple M2 Max, 12 CPUs, 32 GiB RAM, macOS, 2026-10-06, load averages 2.3 to 2.8 (other projects were running; this was not an idle machine). Full output and caveats are in `bench/RESULTS.md`.

| Half | Where it ran | Figure that matters | What it does not show |
|---|---|---|---|
| `bench.build` | native arm64, in-process | 12 parts, every build+export 0.01 s at two decimals; fine STL 25,084 B / 500 triangles up to d=20, 44,484 B / 888 at d=100 | anything about a threaded part; the "Heaviest" row is not a ranking |
| `bench.export` (`d=100 length=200`) | native arm64 | L19 selects level 1 (level 6: 16.06 % smaller but 1.81x wall, bar 1.5x); copy costs +0.1 ms, +0.9 MiB over in place | the wall bar is decided at sub-2 ms walls over a 44 KB mesh |
| `bench.latency` | native arm64 host, `screw serve --port 8001`, 2 workers, fresh server | idle p95 0.6 ms; under load 0.8 ms (1.26x, concurrent: 4 of 10 built, 6 `503 busy`) and 0.6 ms (0.99x, single) | a bound; no bar is set; the 2.1 s slowest build is not the cost of building a part and its cause was not isolated |
| `bench.memory sweep` | **linux/amd64 image under emulation** on OrbStack (Docker 29.4.0, aarch64 daemon), port 8001, 8 GiB sweep ceiling | N=1 1323.0 MiB, N=2 980.8 MiB, N=4 1881.1 MiB, 0 failures, no capped row | a footprint: each peak is the max of 4 to 12 `docker stats` readings and falls in the second half; N=1 above N=2 is not a result |

## Files Created/Modified

- `bench/__init__.py` - `machine_facts()`, spur's, docstring retyped
- `bench/corpus.py` - the 12-part grid and `label()`; says it sets no bound
- `bench/build_time.py` - build/STL/STEP time per part vs `SCREW_BUILD_TIMEOUT`, `load_sweep`, `stl_size`, `report`
- `bench/export_cost.py` - L19 gzip table and its selection rule, L24 mesh-copy cost, `find_set`
- `bench/latency.py` - `single` and `concurrent` scenarios, `fetch` (503 by reason), p95 refusal, report with load
- `bench/memory.py` - sweep and confirm over `docker compose run`, `_is_capped`, teardown in a `finally`
- `bench/README.md`, `bench/RESULTS.md` - method, where each half must run, the recorded runs
- `tests/test_bench.py` - 25 tests
- `Makefile` - `bench`, `bench.build`, `bench.export`, `bench.latency`, `bench.memory`, `SWEEP`, `SET`; `typecheck` covers `bench`
- `docs/tech_debt/INDEX.md` and `docs/tech_debt/active/2026-10-06-bench-memory-sampling-is-too-coarse-for-short-corpora.md` - the sampling limit, trigger Phase 7

## Decisions Made

- No latency bar and no recorded baseline: spur's 2.00x bar and gear baseline are its own numbers, and L07 ports the method only.
- The memory sweep publishes with `-p 127.0.0.1:<port>:8000` from `--base-url`; default behaviour on a free 8000 is identical to spur's `--service-ports`.
- `label()` in `bench.corpus` (kernel-free) rather than `bench.build_time`.
- The concurrent latency scenario takes `corpus()[:10]`, excluding the heaviest part, because the default run is concurrent then single and a part built first is a cache hit for the second.

## TDD Gate Compliance

RED `a931298` (`test(01-08)`), GREEN `8bb2398` (`feat(01-08)`); no REFACTOR commit.

- **RED evidence:** against the placeholders, `pytest tests/test_bench.py --runxfail` reported `15 failed` and the plain run `15 xfailed`, each failing on its planned assertion (placeholders return `[]`, a wrong size, an empty report, level 9, the raw `ru_maxrss`). The RED record was not run through `gsd_run check tdd-red-evidence`: pytest's text report is not one of that classifier's supported formats (TAP, JUnit XML, swift-testing, unittest). The semantic assessment was by inspection of the `--runxfail` output. `semanticAssessment`: every target test executed and failed on the intended assertion, none on an import, collection or fixture fault.
- One test, `test_every_corpus_entry_is_a_valid_bolt`, passed vacuously against the empty placeholder corpus (XPASS under strict xfail). It was strengthened with `len(entries) == 12` before the RED commit, so the RED commit has no unexpected pass.
- Task 2 is `type="auto"` without `tdd`: its predicate tests were written alongside the code and land in `26bf992`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] bench.memory could not publish on 8000**
- **Found during:** Task 2 (planning the container run)
- **Issue:** spur's `docker compose run --service-ports` publishes `compose.yaml`'s `127.0.0.1:8000:8000`, and 8000 is held by another project's container (`spur-spur-1`) on this host, which must not be stopped. Compose merges `ports` lists, so a one-line override cannot replace the mapping.
- **Fix:** `_publish(base_url)` turns the port of `--base-url` into `-p 127.0.0.1:<port>:8000`; the default `http://127.0.0.1:8000` reproduces `compose.yaml`'s mapping. Tested (`test_the_container_is_published_on_the_host_port_the_base_url_names`).
- **Files modified:** bench/memory.py, tests/test_bench.py
- **Committed in:** 26bf992

**2. [Rule 2 - Missing critical] the latency and memory reports printed no load reading**
- **Found during:** Task 2
- **Issue:** the plan requires each recorded entry to carry a load reading, and spur's latency and memory reports print only machine facts. Taking the load by hand beside a run would be a figure the harness cannot reproduce.
- **Fix:** both reports print `os.getloadavg()` read before the scenario (latency) or before the first container (memory). A first latency run made before this change was discarded and the scenarios re-run on the committed harness; its ratios (1.27x, 1.08x) are mentioned in `RESULTS.md` only as a repeat.
- **Files modified:** bench/latency.py, bench/memory.py, tests/test_bench.py
- **Committed in:** 26bf992

**3. [Scope] spur's recorded baseline and 2.00x bar are dropped**
- **Found during:** Task 2
- **Issue:** the plan says to keep "the p95 helpers, the 503-reason recording and the markdown report". spur's report prints a "pass bar is <= 2.00x" and a gear baseline from its debt file; screw has neither, and a bar printed beside a screw number would read as a bound (L07, T-01-29).
- **Fix:** the report prints the ratio and "no bar is set for screw yet". `RECORDED_BASELINE` is not ported.
- **Committed in:** 26bf992

**4. [Scope] `label()` moved to bench.corpus, and the tests grew**
- **Found during:** Task 2
- **Issue:** `bench.latency` needs the same label as `load_sweep` but `bench.build_time` imports `screw.solid`, which would pull the CAD kernel into a measuring client.
- **Fix:** `label()` lives in `bench.corpus`; `bench.build_time` imports it. The test file also carries tests beyond the plan's list for code that is new here (`load_sweep`, `find_set`, `_publish`, `_parse_mem`, the p95 refusal, the report).
- **Committed in:** 26bf992

---

**Total deviations:** 4 (1 blocking, 1 missing-critical, 2 scope). **Impact on plan:** none changes what the plan promised; 1 and 2 are needed to run it on this host and to carry the load reading it requires.

## Issues Encountered

- **Make targets cannot take a port.** With 8000 taken, `make bench.latency` and `make bench.memory` cannot be pointed at 8001. The plan lists only `SWEEP` and `SET`, so no variable was added; the runs used the direct form `.venv/bin/python -m bench.latency --base-url http://127.0.0.1:8001` (and `bench.memory sweep --base-url ...`), which is what the targets run plus the port. `bench/README.md` documents both forms. A `BASE_URL` variable would be a small follow-up if the owner wants one.
- **The memory figures are not usable as a footprint.** 4 to 12 readings per row; N=1 reads above N=2. Recorded as it is in `RESULTS.md` and filed as a tech-debt item (below), not smoothed or re-run until it looked monotonic.
- **Container timings are emulation figures.** `DOCKER_DEFAULT_PLATFORM=linux/amd64` on an aarch64 daemon; labelled in `RESULTS.md`. No native linux/amd64 figure exists yet; that is Phase 7's.
- **Start time not captured.** `PLAN_START_TIME` was not recorded at launch; the start above is reconstructed from the first command's `uptime`.

## Filed

- `docs/tech_debt/active/2026-10-06-bench-memory-sampling-is-too-coarse-for-short-corpora.md` (severity must, trigger: before the Phase 7 memory sweep) with its row in `docs/tech_debt/INDEX.md`.

## Known Stubs

None. The only placeholders in the history are the RED-commit placeholders in `a931298`, replaced in `8bb2398`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plans 01-09 and 01-10 are not blocked by this plan. `make verify` passes: 285 passed, `Contracts: 6 kept, 0 broken`.
- Phase 2 and Phase 7 re-use the harness: Phase 7 replaces `bench/corpus.py` with the threaded grid and keeps it fixed, fixes the memory sampling (debt item above), and runs the memory half on native linux/amd64 before any figure becomes a limit.
- The interim bounds in `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` are neither confirmed nor changed by anything here.

## Self-Check: PASSED

- All ten created files exist on disk; commits `a931298`, `8bb2398`, `7388183`, `26bf992`, `b1f4cb3`, `2a2a0cd`, `469c8ed` are ancestors of HEAD.
- Acceptance criteria re-run: no private `solid._` name in `bench`; `def corpus(` and `SCREW_BUILD_TIMEOUT` present; `bench.build`/`bench.export` (2 lines), `bench`/`bench.latency`/`bench.memory` (3 lines) and `mypy src tests docker bench scripts` in the Makefile; `import httpx2 as httpx` in `latency.py` and `memory.py`; `sets no bound` in `bench/README.md`; `not a bound` and `p95` and `SCREW_BUILD_WORKERS` in `RESULTS.md`.
- `make verify` after the last code commit: `285 passed`, `Contracts: 6 kept, 0 broken`, ruff and mypy clean.
- Host: `docker ps` shows only `spur-spur-1`; no `screw_default` network; no `screw serve` process.

---
*Phase: 01-runtime-port-and-walking-skeleton*
*Completed: 2026-10-06*
