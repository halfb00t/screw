# Interim runtime bounds are spur's figures, not screw's measurements

Severity: must
Status: active
Date: 2026-10-05
Source: Phase 1 D-01, D-02, D-14; 01-RESEARCH.md F1, F9; L09
Related files:
- src/screw/app.py:82-86 (`SCREW_EXPORT_CACHE_MB`)
- src/screw/app.py:89-103 (`SCREW_MAX_QUEUED_BUILDS`)
- src/screw/app.py:138-148 (`SCREW_BUILD_WORKERS`, `SCREW_BUILD_TIMEOUT`)
- src/screw/app.py:170-188 (`_GZIP_LEVEL`, `minimum_size`)
- src/screw/app.py:258-260 (`Retry-After`)
- src/screw/solid/__init__.py:37-41 (`TESSELLATION`)
- src/screw/solid/__init__.py:58-68 (`_release_arenas`)
- src/screw/solid/__init__.py:96-99 (`SCREW_SOLID_CACHE`)
- src/screw/params.py:17-33 (`INTERIM_MAX_MM`)

## Context
Phase 1 ports spur's runtime, and the pool, the queue and the caches need numbers to run.
spur measured its own on involute gears (160-199 teeth, a 200-tooth worst case); nothing
below was measured on a threaded part or on linux/amd64. Each is carried as an explicit
default, commented `INTERIM` in the code with its source, and none is presented as measured
for screw (D-01).

| Knob | Value | Where | Source |
|---|---|---|---|
| `SCREW_BUILD_TIMEOUT` | 30 s | app.py lifespan | spur's worst observed build was 7.39 s (a 200-tooth fine gear, ten concurrent requests), so 30 s is about 4x that; the skeleton cylinder builds in well under a second |
| `SCREW_BUILD_WORKERS` | 2 | app.py lifespan | spur L17: a fixed number, not `os.cpu_count()` |
| `SCREW_MAX_QUEUED_BUILDS` | 2 x workers | app.py `_max_queued_builds` | spur app.py admission control: a measured load run showed deeper queues only adding latency |
| `SCREW_EXPORT_CACHE_MB` | 64 | app.py `_EXPORTS` | spur's export-cache default (same knob, renamed), sized against ~9 MB gear STLs |
| `_GZIP_LEVEL` | 1 | app.py | spur L19: level 1 won on a 9 MB gear STL (29.0% of input in 51.5 ms; level 6 was only 8.7% smaller) |
| GZipMiddleware `minimum_size` | 1024 | app.py | spur app.py:207, F9 |
| `Retry-After` | 5 s | app.py `_build_slot`, `timeout` and `pool_broken` 503s | spur app.py:282, F9: a client hint, not a measurement |
| `SCREW_SOLID_CACHE` | 4 solids per worker | solid/__init__.py | spur model.py:561, F9 |
| `TESSELLATION` | preview (0.08, 0.5), fine (0.01, 0.1) | solid/__init__.py | spur model.py:53, F9: chosen for gears; Phase 5 re-chooses it against pair clearance (FRNT-06) |
| `_release_arenas` (`malloc_trim`) | on after every export | solid/__init__.py | spur model.py: 1578 MiB resident without it, 360 MiB with it, over 40 distinct 160-199 tooth gears |
| `INTERIM_MAX_MM` | 1e5 mm on `d` and `length` | params.py | D-14, F1: a cylinder at d=1e5 and length=1e5 measured 0.107 s / 550 MiB (preview STL) and 0.934 s / 1,052 MiB (fine STL) on macOS arm64; d=1e7 is 25 s and 6.0 GiB, past compose's interim `mem_limit: 4g` |
| UI debounce | 350 ms | src/screw/static/app.js `scheduleUpdate` | spur app.js:221 (F9): a UI choice, never measured for screw |

Plan 01-06 appends the `SCREW_WORKERS`, `mem_limit`, HEALTHCHECK and tmpfs rows when it
lands those knobs.

## Why it matters
These numbers decide what a user may ask for (`INTERIM_MAX_MM` is a hard 422) and when a
build is refused (queue depth, timeout). They were measured on a different part family, on
a different host, so a user can be refused or kept waiting on a figure that says nothing
about a threaded bolt. `INTERIM_MAX_MM` is also the one guard between a valid-looking
request and the container's memory limit.

## Next step
Revisit at the Phase 7 operability re-sweep (OPER-01, OPER-02, OPER-03): replace each row
with a value measured on threaded parts under linux/amd64, drop the `INTERIM` comment from
each knob, and resolve this item in that commit.

<!-- On resolve: set Status: resolved, add `Resolved in: <commit sha>`,
     git mv into resolved/, move the INDEX row to Resolved — same commit as the fix. -->
