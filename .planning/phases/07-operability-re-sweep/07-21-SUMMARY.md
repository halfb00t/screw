---
phase: 07-operability-re-sweep
plan: 21
subsystem: api
tags: [operability, runtime, retry-after, workers, queue, gzip, export-cache, solid-cache, arenas, recycling, R16, R17, R18, R19, R20, R21, R22, R23, R24, G17, G32]
status: complete

requires:
  - phase: 07-operability-re-sweep
    provides: "07-16 bench/results/phase-07/runtime.json (complete at 84dfbec), tests/test_runtime_bounds.py, calc.cost.BUILD_TIMEOUT_S"
provides:
  - "screw.app.MEDIAN_BUILD_S and retry_after(artifact): R18's median x the live MAX_QUEUED_BUILDS, ceil, at least 1 s, at all three 503 sites"
  - "screw.app.DEFAULT_BUILD_WORKERS (1, R16), _build_workers(), queue depth 2N (R17), EXPORT_CACHE_MB (240, R21), gzip level 1 (R19), minimum_size 4012 (R20)"
  - "pool.py: max_tasks_per_child stays unset with R23's 60-build plateau (run 41022812680) as the reason"
  - "solid: SCREW_SOLID_CACHE 4 (R22), _release_arenas kept (R23, G17), TESSELLATION kept (R23); cli: --workers 1 (R24)"
  - "tests/test_runtime_bounds.py: every serving and worker knob read from runtime.json and held equal; INTERIM and 'Phase 7' scan over six runtime modules"
affects: [07-17, 07-18, 07-19]

estimate:
  tokens: 80000
  tasks: 2
actuals:
  tokens: 3690       # chars/4 over the added lines of the 8 changed files (14759 chars)
  tasks: 2
  commits: 2         # MEASURED: git rev-list --count 7665eae..744d6e4 (this SUMMARY's commit not counted)
plan_head_before: 7665eae659199faa0d5dffb2a31f20e4d3541ae6
plan_head_after: 744d6e40966c568e636ba0324ff6aff1848e0d0f

tech-stack:
  added: []
  patterns:
    - "a shipped knob's default is a named constant whose comment cites rule, run and deciding reading; a test reads the same key from runtime.json"
    - "Retry-After is computed per request from a shipped median and the live queue depth, so an env override of the depth moves it"

key-files:
  created: []
  modified:
    - src/screw/app.py
    - src/screw/pool.py
    - src/screw/solid/__init__.py
    - src/screw/calc/__init__.py
    - src/screw/cli.py
    - tests/test_api.py
    - tests/test_pool.py
    - tests/test_runtime_bounds.py

key-decisions:
  - "SCREW_BUILD_WORKERS default 1 and queue depth 2 (R16, R17, load run 40909724292); Retry-After per artifact from R18's medians 5.21 / 9.53 / 6.33 s x the live depth"
  - "SCREW_EXPORT_CACHE_MB 240 (R21), gzip level 1 (R19), minimum_size 4012 B (R20); every env override kept, a deployer who moves one re-sweeps (D-16)"
  - "SCREW_SOLID_CACHE 4 (R22), _release_arenas kept (R23/G17), TESSELLATION kept (R23), max_tasks_per_child unset (R23/G32), SCREW_WORKERS 1 (R24)"
  - "No decision log entry written: every value is a rule outcome already recorded in runtime.json and the protocol"

requirements-completed: []   # OPER-01 and OPER-02 advance; 07-17 ships the container values and resolves the interim-runtime-bounds debt

metrics:
  duration: "09:08Z to 09:28Z on 2026-10-30, about 20 min"
  completed: 2026-10-30
---

# Phase 7 Plan 21: the serving and worker knobs from runtime.json Summary

**The serving process and its workers now run on runtime.json's values. That means 1 build
worker, a queue of 2, a per-artifact `Retry-After` of ceil(R18 median x live queue depth), a
240 MiB export cache, gzip level 1 with a 4012 B threshold, 4 cached solids, the arena trim kept
and no recycling. Each comment cites its rule and run, and `tests/test_runtime_bounds.py` holds
every value equal to runtime.json.**

## Commits

| # | sha | subject |
| --- | --- | --- |
| 1 | 070e999 | feat(app): measured workers, queue depth, Retry-After, gzip and export cache (07 D-03, D-11) |
| 2 | 744d6e4 | feat(solid): measured solid cache and arena release, and the CLI server count (07 D-02) |

## The knobs and their evidence

| knob | was | now | runtime.json key | evidence in the comment |
| --- | --- | --- | --- | --- |
| `SCREW_BUILD_WORKERS` default | 2 | 1 | `picked_workers` | R16: p95 35.09 / 51.88 / 69.78 s at N 1 / 2 / 3, load run 40909724292 |
| `SCREW_MAX_QUEUED_BUILDS` default | 2 x 2 | 2 x 1 = 2 | `queue_depth.depth` | R17: largest wall / deadline 0.362, end peak 1657307136 B under 2415919104 B |
| `Retry-After` | "5" | `retry_after(artifact)` | `retry_after.*.median_s` | R18: medians over 100 built requests per artifact, load run 40909724292 |
| `SCREW_EXPORT_CACHE_MB` default | 64 | 240 | `export_cache.mib` | R21: iso4017:M20x200, 250654910 B, 394 candidates, explore run 40646117094 |
| `_GZIP_LEVEL` | 1 | 1 | `gzip.level` | R19: levels 6 and 9 fail at all 14 points (gzip runs 40909739628, 40999657702) |
| `minimum_size` | 1024 | 4012 | `minimum_size.bytes` | R20: 1555 bodies, /api/health 95 B -> 98 B the largest not shrinking |
| `max_tasks_per_child` | unset | unset | `recycling.max_tasks_per_child` | R23/G32: plateau 6467584 / 11583488 / 5222400 B within allowance, run 41022812680; W 1758363648 B |
| `SCREW_SOLID_CACHE` default | 4 | 4 | `solid_cache_k` | R22: W(4) 1652121600 B, run 41016510597 |
| `_release_arenas` | kept | kept | `arenas_kept` | R23/G17: trim on lower at every artifact, arenas run 40909754190 |
| `TESSELLATION` | kept | kept | `tessellation_kept` | R23; the arena and drift runs exported at it; L21's fit |
| `serve --workers` default | 1 | 1 | `screw_workers.workers` | R24: health p95 0.0094 s, load run 40909724292 |

The figures are all runtime.json values, some rounded for display.
`retry_after` takes the product at run time. At the shipped depth it gives 11 / 20 / 13 s, but
no comment or test types those numbers: the tests compute them from runtime.json.

## How the tests tie them

`tests/test_runtime_bounds.py` gains 11 tests (16 test ids with the parametrization):

- **The lifespan.** It starts `BuildPool(picked_workers, BUILD_TIMEOUT_S)` with no env set. A
  fake pool records the arguments, so no worker is spawned.
- **The queue.** `_max_queued_builds()` and `MAX_QUEUED_BUILDS` equal `queue_depth.depth`.
- **Retry-After.**
  - `MEDIAN_BUILD_S` equals the medians in runtime.json.
  - `retry_after` equals ceil(median x depth) for every artifact.
  - Patching the depth to 10 moves the value.
  - A median of 0 gives "1".
- **The carried 5 s.** A static scan finds no `"Retry-After": "5"` in app.py.
- **The export cache.** `EXPORT_CACHE_MB` equals `export_cache.mib`.
- **gzip.** The `GZipMiddleware` entry in `app.user_middleware` has `minimum_size` and
  `compresslevel` from runtime.json.
- **Recycling.** pool.py passes no `max_tasks_per_child=` while runtime.json says null.
- **The solid cache.** `_build_cached.cache_parameters()["maxsize"]` equals `solid_cache_k`.
- **The trim.** With `arenas_kept` true, a real `export()` ends in `malloc_trim(0)`. The trim
  function is replaced by a recorder.
- **The CLI.** `screw serve` hands uvicorn `workers` equal to `screw_workers.workers`.
- **INTERIM.** No `INTERIM` and no `Phase 7` in app.py, pool.py, cli.py, solid/__init__.py,
  calc/__init__.py or calc/cost.py.

End to end:

- `tests/test_api.py`: the busy 503 is parametrized over all three artifacts and expects
  `retry_after(artifact)`. The timeout test expects it per artifact, and the build-failure and
  compress-only busy tests expect it at stl-preview.
- `tests/test_pool.py`: the failure-mode mapping expects `retry_after("stl-preview")`.

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 1 - Bug] Stale "admits 4 builds" comments.**
- **Found during:** Task 1.
- **Issue:** `pool.py`'s same-slot race comment and its `tests/test_pool.py` twin said
  `MAX_QUEUED_BUILDS` admits 4 builds. That stopped being the default once workers became 1.
- **Fix:** Both now say a 4th same-slot request is reachable once the queue admits 4 builds
  (2 build workers or more). The measured default admits 2.
- **Commit:** 070e999.

**2. [Rule 3 - Blocking] Two "Phase 7" forward references in the scanned modules.**
- **Found during:** Task 2. The plan's behaviour scans these modules for `Phase 7`.
- **Fix 1:** `solid/__init__.py`'s head chamfer timing said "Phase 7 re-measures". It now says
  the linux/amd64 walls under the cost model and the timeouts (explore run 40646117094, bound
  run 40907549180) build every bolt at the default 30 degrees. Checked:
  - no point set sets `head_chamfer`;
  - both runs' `GITHUB_SHA` descend from the head chamfer commit cc6bccf.
- **Fix 2:** `calc/__init__.py`'s standing warning said "the first release, after Phase 7". It
  now says "once the runtime bounds are measured", with 06 D-15 cited as before.
- **Commit:** 744d6e4.

**3. [Rule 3 - Blocking] Lint and type fixes in the new tests.** The pre-commit gate refused
the first two attempts at commit 1:
- ruff: SIM300 and PT018;
- mypy: an `object` index, middleware identity, and a redundant `cast` in test_api once
  `want_artifact` became `Artifact`.

All were fixed before the commit landed. The tree was never committed red.

### Interpretation

**4. New named defaults.** The plan named the knobs but not their shape.
- `DEFAULT_BUILD_WORKERS` and `_build_workers()` replace two literal `2`s, so the lifespan and
  the queue derivation read one default.
- `EXPORT_CACHE_MB` names the cache budget, so a test reads it without the private
  `_BlobCache._budget`.

**5. RED for Task 2 was the static scan only.** The solid cache (4), the trim (kept) and the CLI
default (1) already held their runtime.json values. Their new tests passed at once and now pin
them. The INTERIM/Phase 7 scan failed on three modules, as expected.

**6. No decision log entry.** Every value is a rule outcome already recorded in runtime.json and
the protocol, so no L number was taken. The next free one is still the one after L22.

## Not changed here (07-17's scope)

- `compose.yaml` still sets `SCREW_BUILD_WORKERS: "2"`, so `make up` runs 2 build workers until
  07-17.
- The Dockerfile `SCREW_WORKERS` ENV and its HEALTHCHECK keep their INTERIM labels.
- The tech debt item `2026-10-05-interim-runtime-bounds.md` stays active.

07-17's plan covers all three.

## Verification

- Task 1's `<verify>`: `make test PYTEST_ARGS="tests/test_api.py tests/test_pool.py
  tests/test_runtime_bounds.py -q -n0 --no-cov"`: 234 passed. It was re-run as the tracer gate,
  with the same result.
- Task 2's `<verify>`: `make test PYTEST_ARGS="tests/test_runtime_bounds.py tests/test_cost.py
  tests/test_solid.py -q -n0 --no-cov"`: 236 passed.
- `make verify` at 744d6e4: `4557 passed in 168.92s`, coverage 97.70 %, 10 contracts kept, mypy
  clean.
- Acceptance:
  - `grep -c '"Retry-After": "5"' src/screw/app.py` prints 0.
  - `INTERIM` counts 0 in app.py, pool.py, solid/__init__.py, cli.py, calc/__init__.py and
    calc/cost.py.
  - Both commit subjects are the plan's.

## Known Stubs

None.

## Threat Flags

None. T-07-67 is mitigated by `tests/test_runtime_bounds.py` and the INTERIM scan. T-07-68
stands as accepted: each env override is kept, and each comment says a deployer who moves it
re-sweeps.

## Debt

- Filed: none.
- Resolved: none. `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` stays active for
  07-17, which resolves it in the commit that removes the last INTERIM label.

## Self-Check: PASSED

- The 8 modified files exist, and the SUMMARY is at
  `.planning/phases/07-operability-re-sweep/07-21-SUMMARY.md`.
- 070e999 and 744d6e4 are ancestors of HEAD.
