# Interim runtime bounds are spur's figures, not screw's measurements

Severity: must
Status: active
Date: 2026-10-05
Source: Phase 1 D-01, D-02, D-14; 01-RESEARCH.md F1, F9; L09. Phase 3 added `MIN_TAIL_MM`,
`MAX_TURNS` and `FINE_STL_ROWS` and the in-cap costs below (D-01 to D-03, D-17, D-18; L12; plan 03-07)
Related files (every `INTERIM` label under src/, Dockerfile and compose.yaml; the audit in
01-09 Task 2 compared `git grep` of the knob names against this item and found none missing):
- src/screw/app.py:87-93 (`SCREW_EXPORT_CACHE_MB`)
- src/screw/app.py:99-107 (`SCREW_MAX_QUEUED_BUILDS`)
- src/screw/app.py:146-158 (`SCREW_BUILD_WORKERS`, `SCREW_BUILD_TIMEOUT`)
- src/screw/app.py:213-219 (`_GZIP_LEVEL`, `minimum_size`)
- src/screw/app.py:290-292, 474, 492 (`Retry-After`; the label sits at 290, the other two 503s carry the same header)
- src/screw/solid/__init__.py:44-48 (`TESSELLATION`)
- src/screw/solid/__init__.py:65-77 (`_release_arenas`)
- src/screw/solid/__init__.py:137-140 (`SCREW_SOLID_CACHE`)
- src/screw/solid/helical.py:36-41 (`MIN_TAIL_MM`)
- src/screw/calc/thread.py:23-28 (`MAX_TURNS`)
- src/screw/calc/thread.py:138-158 (`FINE_STL_ROWS`)
- src/screw/params.py:18-31 (`INTERIM_MAX_MM`)
- src/screw/cli.py:155-157 (`SCREW_WORKERS`, the `serve` default)
- src/screw/static/app.js:318-321 (UI debounce)
- Dockerfile:36-41 (`SCREW_WORKERS` `ENV`), Dockerfile:44-52 (`HEALTHCHECK`)
- compose.yaml:10-15 (`SCREW_WORKERS`, `SCREW_BUILD_WORKERS`), compose.yaml:17-20 (`mem_limit`), compose.yaml:23-26 (`tmpfs`)

## Context
Phase 1 ports spur's runtime, and the pool, the queue and the caches need numbers to run.
spur measured its own on involute gears (160-199 teeth, a 200-tooth worst case); nothing
below that is spur's was measured on a threaded part or on linux/amd64. Each is carried as an explicit
default, commented `INTERIM` in the code with its source, and none is presented as measured
for screw (D-01).

| Knob | Value | Where | Source |
|---|---|---|---|
| `SCREW_BUILD_TIMEOUT` | 30 s | app.py lifespan | spur's worst observed build was 7.39 s (a 200-tooth fine gear, ten concurrent requests), so 30 s is about 4x that; M6 x 20 builds in 0.09 s (planner probe 2026-10-10), while an in-cap off-row part can need minutes (see the costs below); still a backstop, not a measurement for threads |
| `SCREW_BUILD_WORKERS` | 2 | app.py lifespan, compose.yaml `environment` | spur L17: a fixed number, not `os.cpu_count()` |
| `SCREW_MAX_QUEUED_BUILDS` | 2 x workers | app.py `_max_queued_builds` | spur app.py admission control: a measured load run showed deeper queues only adding latency |
| `SCREW_EXPORT_CACHE_MB` | 64 | app.py `_EXPORTS` | spur's export-cache default (same knob, renamed), sized against ~9 MB gear STLs |
| `_GZIP_LEVEL` | 1 | app.py | spur L19: level 1 won on a 9 MB gear STL (29.0% of input in 51.5 ms; level 6 was only 8.7% smaller) |
| GZipMiddleware `minimum_size` | 1024 | app.py | spur app.py:207, F9 |
| `Retry-After` | 5 s | app.py `_build_slot`, `timeout` and `pool_broken` 503s | spur app.py:282, F9: a client hint, not a measurement |
| `SCREW_SOLID_CACHE` | 4 solids per worker | solid/__init__.py | spur model.py:561, F9 |
| `TESSELLATION` | preview (0.08, 0.5), fine (0.01, 0.1) | solid/__init__.py | spur model.py:53, F9: chosen for gears; Phase 5 re-chooses it against pair clearance (FRNT-06) |
| `_release_arenas` (`malloc_trim`) | on after every export | solid/__init__.py | spur model.py: 1578 MiB resident without it, 360 MiB with it, over 40 distinct 160-199 tooth gears |
| `INTERIM_MAX_MM` | 1e5 mm on `d` and `length` | params.py | D-14, F1: those figures were measured on the Phase 1 cylinder (d=1e5 and length=1e5: 0.107 s / 550 MiB preview STL, 0.934 s / 1,052 MiB fine STL on macOS arm64; d=1e7 is 25 s and 6.0 GiB, past compose's interim `mem_limit: 4g`). The thread is unmeasured at that corner: planner probe 2026-10-10, d=1e5, pitch=1, length=1 builds in 0.01 s and its preview STL did not finish in 120 s |
| `MIN_TAIL_MM` | 1e-3 mm | solid/helical.py | D-17, research probe 2026-10-10 at d=6, pitch=1: a twist of length <= 1e-8 mm SIGSEGVs the process before any check can run, 3e-8 to 1e-6 mm raises, 1e-5 mm builds; as a sewn tail 1e-5 to 1e-2 mm built one valid solid at (6, 1), (2, 0.4) and (20, 2.5). 1e-3 sits 100x above the last failing tail. Not a campaign result; Phase 7 re-measures (OPER-03) |
| `MAX_TURNS` | 250 turns (`length / pitch`, exact decimals) | calc/thread.py | D-01, L11 `2026-10-08-a-frontier`: measured, no stop up to 250 turns at any size, both hands, rod and void. Nothing above it is measured, and the seconds cap is not established; Phase 7 replaces it with per-size caps (OPER-03) |
| `FINE_STL_ROWS` | seven `(d, pitch)` rows, 52 to 67.5 mm | calc/thread.py | D-02, D-03, L11 `2026-10-08-a-grid`: measured against the INTERIM 64 MiB export budget and the INTERIM fine preset (0.01 mm, 0.1 rad) with gzip level 1, so each cap moves if either moves. Run keys, not ISO rows; an off-row part has no cap. Phase 7 re-measures (OPER-02, OPER-03) |
| `SCREW_WORKERS` | 1 | cli.py `serve` default, Dockerfile `ENV`, compose.yaml | spur L17: one server process, with `SCREW_BUILD_WORKERS` carrying the parallelism; not measured for screw |
| `mem_limit` | 4g | compose.yaml | spur L17: 4g measured on two workers over spur's 160-199 tooth gear corpus; a labelled cap beats none; not measured for screw. The research probe below peaked at 7875 MiB for one in-cap fine STL |
| HEALTHCHECK | interval 30 s, timeout 2 s, start-period 30 s, retries 3, and the probe's inner `urlopen` timeout 1 s | Dockerfile | spur's healthcheck (F9): spur measured `/api/health` under-load p95 at 0.7-2.3 ms on its gear service and kept 2 s for interpreter startup in the probe; not measured for screw |
| tmpfs `/tmp` | 256m | compose.yaml | spur's choice (F9): exports are written there before being read back; not measured for screw |
| UI debounce | 350 ms | src/screw/static/app.js `scheduleUpdate` | spur app.js:221 (F9): a UI choice, never measured for screw |

### What the thread costs inside the caps (Phase 3, D-18)

D-01 and D-03 accept that a part inside the 250-turn cap and off the seven measured rows can
exceed the INTERIM backstops, and no unmeasured guard was added (L02). These are single runs on
macOS arm64 (the research probe 2026-10-10, load 4 to 26, not linux/amd64); they bound nothing:

- d=100, pitch=5, length=1250 (250 turns): build 0.6 s. Preview STL 6,452,418 triangles, 308 MiB,
  6.7 s, peak RSS 1534 MiB. Fine STL 36,906,760 triangles, 1760 MiB, 152.6 s, peak RSS 7875 MiB,
  against the 30 s `SCREW_BUILD_TIMEOUT` and compose's `mem_limit: 4g`.
- d=6, pitch=0.1, length=25, fine STL: 2,126,222 triangles, 101 MiB, peak RSS 1327 MiB. Over the
  64 MiB export budget, so it is served uncached and rebuilt on every repeat request.
- d=1e5, pitch=1, length=1 (planner probe 2026-10-10): builds in 0.01 s; its preview STL did not
  finish in 120 s.

Which backstop such a part reaches first, the 30 s timeout or the container limit, was not
measured. The phase added no guard for them.

## Why it matters
These numbers decide what a user may ask for (`INTERIM_MAX_MM`, `MAX_TURNS` and the fine-STL
rows are hard 422s) and when a build is refused (queue depth, timeout). They were measured on a different part family, on
a different host, so a user can be refused or kept waiting on a figure that says nothing
about a threaded bolt. `INTERIM_MAX_MM` and `MAX_TURNS` are also the guards between a valid-looking
request and the container's memory limit, and the costs above show a part inside both can still
need minutes and more than 4 GiB.

## Next step
Revisit at the Phase 7 operability re-sweep (OPER-01, OPER-02, OPER-03): replace each row
(`MIN_TAIL_MM`, `MAX_TURNS` and `FINE_STL_ROWS` included) with a value measured on threaded parts
under linux/amd64, drop the `INTERIM` comment from
each knob, and resolve this item in that commit.

<!-- On resolve: set Status: resolved, add `Resolved in: <commit sha>`,
     git mv into resolved/, move the INDEX row to Resolved — same commit as the fix. -->
