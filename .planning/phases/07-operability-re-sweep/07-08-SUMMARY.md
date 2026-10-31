---
phase: 07-operability-re-sweep
plan: 08
subsystem: testing
tags: [operability, load, uvicorn, healthcheck, gzip, runs-ii, buildpool]

requires:
  - phase: 07-operability-re-sweep
    provides: "07-06: bench.oper's Runs II kinds, reading_argv(module=), the bound-smoke generator pattern"
provides:
  - "bench.oper_load: p95, container_argv, model_path, drive (one shared queue), run_load, healthcheck_argv, catalogue_rows, measure_bodies, request_status"
  - "bench.oper_serve: the instrument server (--deadline, --pool-log) and record_calls, the per-pool-call log for R17 (G8)"
  - "bench.oper: point kind load (workers, queue, clients, mix, solid_cache, bodies); gzip_levels on part points"
  - "bench.oper_child: gzip_levels(data, levels) after the R2 peak read (R19)"
  - "bench.oper_sets.load_smoke(); bench/points/load-smoke.json, generated and covered by --check"
  - "a successful runner smoke of the load instruments (run 40804106015), a path check that sets nothing"
affects: [07-15, 07-16]

actuals:
  tokens: 17514   # chars/4 over the added lines of bench/, tests/ and pyproject.toml across the three commits
  tasks: 3
  commits: 3      # MEASURED: git rev-list --count 80d9cd0..c6b09d4
plan_head_before: 80d9cd0fa70d1624cb4348aaeedd352c6a4103b9
plan_head_after: c6b09d431a9cf03df27d969a4bba6366c37dd935   # before this SUMMARY's own commit

tech-stack:
  added: []
  patterns:
    - "the parent drives a long-lived container through the docker CLI (run -d, port, exec, inspect, rm), with the docker call injectable so the whole reading runs against a local fake server in tests"
    - "an instrument patches the app's module globals in its own process only (vars(screw.app), setattr on BuildPool), so src/ is untouched"

key-files:
  created:
    - bench/oper_load.py
    - bench/oper_serve.py
    - bench/points/load-smoke.json
    - tests/test_oper_load.py
  modified:
    - bench/oper.py
    - bench/oper_child.py
    - bench/oper_sets.py
    - tests/test_oper.py
    - pyproject.toml

key-decisions:
  - "A load reading's health poller and HEALTHCHECK poller cover the load window only (from the release of the clients to the last response), so every health sample is a sample under load (R24, R25)"
  - "A load reading's status takes the container first (capped, then killed, crashed, no_cgroup), then the requests (any 422 refused, any timeout 503 killed, any other non-200, unfinished or compressed response crashed); a socket timeout at the reading's deadline is killed, not crashed"
  - "Owner ruling 2026-10-29 on the Task 3 check: 19 health samples accepted as the path check (option 1), recorded as a deviation"

requirements-completed: []   # OPER-02 advances; it is not wholly done (the Runs II sets, the timeouts, mem_limit and the rest are later plans)

duration: about 35 min of work plus one runner job
completed: 2026-10-29
status: complete
---

# Phase 7 Plan 08: The load instruments Summary

**`bench.oper_load` runs R15's load reading: the server in the production image (`bench.oper_serve`, `screw serve` with the instrument deadline and a pool-call log), C clients pulling one shared queue in mix order with `Accept-Encoding: identity`, a 0.5 s health poller and the Dockerfile's own HEALTHCHECK every 5 s. With `bodies` it also measures R20's JSON bodies after the end peak. Part points take R19's `gzip_levels`. A generated smoke set read `ok` in both readings on the runner (run 40804106015).**

## What was done

1. **Task 1 (tracer), `a959fe4`.**
   - `bench/oper_serve.py` runs in the container. It calls `configure()` and replaces `screw.app.BUILD_TIMEOUT_S` with a `MappingProxyType` of `--deadline` for every artifact, before the lifespan builds the pool. It wraps `BuildPool._run_with_timeout` with `record_calls`, then calls `uvicorn.run("screw.app:app", host="0.0.0.0", port=8000, workers=1, proxy_headers=True, log_config=None)`. `record_calls` appends one line per pool call: slot, artifact, the artifacts pending on that slot at submit, `submit_s`, `end_s` and the outcome.
   - `bench/oper_load.py` uses the standard library and `bench` only. In order:
     1. `container_argv` is `docker run -d` with `--memory` and `--memory-swap` at the cap and `-p 127.0.0.1::8000`. It has four separate `-e` elements: `SCREW_BUILD_WORKERS`, `SCREW_MAX_QUEUED_BUILDS`, `SCREW_EXPORT_CACHE_MB=1` and `SCREW_SOLID_CACHE`. `bench/` is mounted read-only.
     2. It waits for the first 200 of `/api/health`. That wait is the time to healthy.
     3. It settles 2 s and reads the idle peak with `docker exec`, using `bench.oper_child.read_peak`.
     4. `drive` runs the clients: one `queue.Queue` filled in mix order, each client takes its first request before a barrier, and the health poller runs beside them.
     5. It then reads the end peak, the pool log and `OOMKilled`, and finishes with `docker rm -f` in a `finally`.
     6. `p95` is `statistics.quantiles(n=20)[18]` from 20 or more samples. Below that it is `None`, and the sample count is recorded.
     7. Only `ok` carries figures. Any other status keeps each request's index, label, kind, params, artifact, status code and error type.
   - `bench/oper.py`: the `load` kind with exactly the keys listed. Refused with exit 2: N outside 1..3, a queue below N, clients below 1, `solid_cache` outside 1..4, `bodies` not a bool, an empty or malformed mix. It is dispatched to `run_load` by a lazy import, because `oper_load` imports `is_capped` from `oper`. The mix is not repeated in the record. `summarize` takes `memory_peak_bytes` as a load reading's metric.
2. **Task 2, `c178a70`.**
   - `healthcheck_argv()` reads the exec-form `CMD` of the Dockerfile's `HEALTHCHECK`. A second poller runs it through `docker exec` every 5 s and records each wall and exit code.
   - `catalogue_rows` reads `/api/kinds` and each kind's `/api/presets`. `measure_bodies` records, for `/api/health`, each `/api/presets` and every row's info document, the identity length and `gzip.compress` lengths at 1, 6 and 9. A non-200 keeps its status and no length. Both run only after the end peak is read.
   - In `bench.oper_child`, `gzip_levels` gives `{level, bytes, seconds}` per level, after the R2 peak read.
   - The parent accepts `gzip_levels` on part points (distinct levels of 1, 6 and 9), passes them in the point JSON, records them, and checks the child's `gzip` entries.
3. **Task 3, `c6b09d4`.**
   - `load_smoke()`: `load-n1` (N 1, queue 2, clients 2, `solid_cache` 4, bodies, the default bolt and nut at all three artifacts), and the default bolt `stl-fine` with `gzip_levels` [1, 6, 9]. Rule "smoke, not a figure: 07-08 path check", reps 1, shards 1.
   - `generate()` and `--check` include it, and `bench/points/load-smoke.json` was written by the generator.

## Runner smoke, path check only

Run **40804106015** (`operability: load-smoke`, commit c6b09d4), conclusion `success`. One job, 2 readings, both **ok**. The artifacts were downloaded with `-p 'oper-*'` into the session scratch directory, not into the repository. Nothing is recorded under `bench/results/`, and no figure from the run is quoted here.

**`load-n1`**

| Check | Result |
| --- | --- |
| Requests | 6 of 6 returned 200, all `content_encoding` identity, so no response was compressed |
| Pool log | 6 lines, one per build request, all outcome `ok` |
| Readings present | time to healthy, idle peak, end peak |
| Health samples | **19**, all 200 |
| HEALTHCHECK runs | 2, both exit 0 |
| Bodies | 311 (health, 2 presets, 308 info documents), none non-200 |

**`default-bolt` `stl-fine`:** `gzip` entries at levels 1, 6 and 9.

## Verification

- `make test PYTEST_ARGS="tests/test_oper_load.py tests/test_oper.py -q -n0 --no-cov"`:
  - 426 passed after Task 1.
  - After Task 2 the same command passed. The last run also included `tests/test_oper_bound.py`: 486 passed.
  - 446 passed during Task 3.
- `make verify` passed in the pre-commit hook for each of the three commits. The first try of the Task 3 commit failed lint on a long line in `tests/test_oper.py`; the line was wrapped and committed again, with no skip.
- `make verify` run by hand after the last commit: `4390 passed in 160.35s (0:02:40)`.
- `gh run list ... select(success and "operability: load-smoke") | length` prints 1.
- `.venv/bin/python -m bench.oper_sets --check` exits 0.
- `ls bench/results/phase-07 | grep -c load-smoke` prints 0.
- Acceptance greps:
  - `bench/oper_load.py`: no `screw` import line; `identity` and `SCREW_EXPORT_CACHE_MB` present; `^def measure_bodies(` matches once.
  - `bench/oper_serve.py`: `BUILD_TIMEOUT_S` present.
  - `bench/oper_child.py`: `gzip_levels` present.
  - `git show --stat --format= a959fe4 -- src/` is empty.
  - Each commit subject matches the plan.

## Deviations from Plan

### Owner-ruled

**1. [Check not met as written] 19 health samples, not at least 20**
- **Found during:** Task 3, the runner smoke check.
- **What happened:** the plan's check asks for at least 20 health samples. Run 40804106015 has 19, all 200.
  - The six-request mix finishes before 20 polls at 0.5 s. The poller kept its schedule for the whole load window.
  - `health_latency` is `{samples: 19, p95_s: null}`: the p95 is withheld and the count stated, which is R24's branch for fewer than 20 samples.
- **Ruling (owner, 2026-10-29), verbatim:** "Accept 19, record deviation (Recommended)".
- **Effect:** none on any rule or figure. The real R15 mix (60 cold requests) runs much longer.

### Auto-fixed Issues

**2. [Rule 1 - Bug] A request cut by the reading's deadline was `crashed`**
- **Found during:** Task 1 (the deadline test).
- **Issue:** each request's socket timeout is the reading's deadline. A request that timed out there was recorded with an error and counted as a non-200, so the reading read `crashed`.
- **Fix:** an error at or after the deadline is recorded as `deadline`. A reading with such a request, or one never started, ends `killed`.
- **Commit:** a959fe4

**3. [Rule 2 - Correctness] A compressed response is not `ok`**
- `request_status` makes a reading with a non-identity `Content-Encoding` `crashed`, so a smoke or a run cannot pass with gzip measured in the latency.
- **Commit:** a959fe4

**4. [Rule 2 - Boundary] `bench.oper_load` joins the kernel-free import contract**
- `pyproject.toml` is not in the plan's file list.
- The fresh `-I` interpreter test proves no `screw` module loads, and the contract keeps the kernel out too.
- **Commit:** a959fe4

**5. [Rule 3 - Blocking] Generator tests list the new smoke**
- `tests/test_oper.py`'s two generator assertions now expect `(*SET_NAMES, "bound-smoke", "load-smoke")`, as 07-06 did for `bound-smoke`.
- **Commit:** c6b09d4

**6. [Shape] A load point's `artifact` is `"load"`**
- A load point has no single artifact. It takes its kind's name, as a probe takes its probe's name, so `summarize` and the label uniqueness check treat it like any point.

**7. [Plan wording] Local path check on the native image**
- **What the plan said:** run the step-5 path check under emulation.
- **What was done:** the laptop sets `DOCKER_DEFAULT_PLATFORM=linux/amd64`, so the check ran on the native arm64 image with that variable overridden to `linux/arm64`.
- **Result:**
  - The load point at N = 1, Q = 2, C = 2 over the default bolt and nut read `ok`.
  - With bodies on, it read `ok` with 311 bodies.
  - The gzip-levels point read `ok`.
- Context only; no figure from it is used.

**8. Process.** Tests and code share one commit per task, because the hook runs `make verify` and a RED commit cannot land (as in 07-05 and 07-06).

## Known Stubs

None.

## Threat Flags

None beyond the plan's register:

| Threat | How it is met |
| --- | --- |
| T-07-21 | The port is published on 127.0.0.1 only and the container is removed in a `finally`. |
| T-07-22 | The deadline and the recorder are replaced in the instrument process only; `src/` is untouched. |
| T-07-23 | The same cap and a 600 s deadline over the whole reading. |
| T-07-61 | Four `-e` elements built from validated integers, never a shell string. |

## Debt

None filed. None resolved. The smoke read only default parts, so no new in-wall part was refused by the kernel.

## Self-Check: PASSED

Files found:
- `bench/oper_load.py`
- `bench/oper_serve.py`
- `bench/points/load-smoke.json`
- `tests/test_oper_load.py`

Commits a959fe4, c178a70 and c6b09d4 are ancestors of HEAD.
