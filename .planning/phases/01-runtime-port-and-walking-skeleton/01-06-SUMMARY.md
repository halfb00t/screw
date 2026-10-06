---
phase: 01-runtime-port-and-walking-skeleton
plan: 06
subsystem: infra
tags: [docker, compose, requirements, github-actions, cadquery, linux-amd64]

requires:
  - phase: 01-runtime-port-and-walking-skeleton
    provides: "docker/smoke.py and make lock scaffold (01-01), the interim-bounds debt item (01-02), the serving runtime and bolt endpoints (01-02 to 01-04)"
provides:
  - "docker/refresh-requirements.sh: resolves pyproject.toml in a fresh linux/amd64 python:3.12-slim-bookworm container, prunes spur's list, proves it with docker/smoke.py, writes requirements.txt"
  - "requirements.txt: the 32-package runtime closure only (no ruff, mypy, pytest, import-linter, pre-commit); also the pip constraint for make venv and CI"
  - "Dockerfile: --no-deps closure install, smoke at build, uid 10001, INTERIM-labelled SCREW_WORKERS and HEALTHCHECK, CMD screw serve"
  - "compose.yaml: 127.0.0.1-only service, read_only, cap_drop ALL, no-new-privileges, INTERIM mem_limit 4g and tmpfs /tmp 256m"
  - "Makefile: lock (docker resolve), image, smoke, check, up, down, logs, clean-docker; no target runs pytest in the image (D-18)"
  - "CI image job: build with smoke, run, curl /api/health, the bolt STL (preview) and STEP"
  - "SCREW_WORKERS, mem_limit, HEALTHCHECK and tmpfs rows in the D-02 interim-bounds item"
affects: [01-07 L08 gate-tools-float, 01-08, phase-7 operability re-sweep (OPER-01/02/03)]

actuals:
  tokens: 4469
  tasks: 2
  commits: 2
plan_head_before: 6795e29e28f0c19d778341bd8006d804c75b7a1e
plan_head_after: d2af1b918be39dee5045630a4ae8683d0350386e

tech-stack:
  added: []
  patterns:
    - "the image installs a frozen runtime closure with --no-deps and fails its own build if docker/smoke.py fails"
    - "requirements.txt is regenerated in linux/amd64, never hand-edited, and doubles as the constraint file"
    - "every carried runtime limit is commented INTERIM with its spur source and has a row in the D-02 item"

key-files:
  created:
    - docker/refresh-requirements.sh
    - Dockerfile
    - .dockerignore
    - compose.yaml
  modified:
    - requirements.txt
    - Makefile
    - .github/workflows/ci.yml
    - docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md

key-decisions:
  - "The resolve ran under linux/amd64 emulation on the arm64 host and succeeded; no arm64 closure was substituted"
  - "No runtime version moved: cadquery 2.8.0, cadquery-ocp 7.9.3.1.1, fastapi 0.142.2, pydantic 2.13.5, uvicorn 0.54.0 are unchanged; only the dev tools and spur's pruned packages left the file"
  - "make up was verified through a COMPOSE_FILE override on 127.0.0.1:8001 because another project's container held 8000; compose.yaml itself keeps 127.0.0.1:8000:8000"

patterns-established:
  - "INTERIM comment form: INTERIM (D-01, D-03): <value> is spur <Lxx/F9>, measured on <spur workload>; not measured for screw; Phase 7 re-sweeps (OPER-02)"

requirements-completed: [INFR-01]

coverage:
  - id: D1
    description: "make lock resolves the runtime closure in linux/amd64, proves it with docker/smoke.py and writes a requirements.txt with no gate-tool line"
    requirement: INFR-01
    verification:
      - kind: integration
        ref: "make lock (exit 0, smoke line printed inside the amd64 resolve container); grep -cE gate-tool pins requirements.txt = 0"
        status: pass
    human_judgment: false
  - id: D2
    description: "make verify is green on a .venv constrained by the regenerated requirements.txt"
    requirement: INFR-01
    verification:
      - kind: integration
        ref: "make verify: Contracts 6 kept, 0 broken; 175 passed"
        status: pass
    human_judgment: false
  - id: D3
    description: "make smoke builds the linux/amd64 image and docker/smoke.py passes inside it"
    requirement: INFR-01
    verification:
      - kind: integration
        ref: "make smoke -> 'smoke: kernel, exports, ASGI stack and validation all live'; docker image inspect screw:latest = linux/amd64"
        status: pass
    human_judgment: false
  - id: D4
    description: "make up brings the compose service healthy, the bolt STL (preview), STEP and info answer 200 from the container, make down stops it; container is uid 10001, read-only, cap_drop ALL, no-new-privileges, mem 4g, bound to 127.0.0.1"
    requirement: INFR-01
    verification:
      - kind: integration
        ref: "make up under COMPOSE_FILE override on :8001, curl stl 200 (5084 bytes) / step 200 / info 200, docker inspect, make down"
        status: pass
    human_judgment: false
  - id: D5
    description: "make check (verify, smoke, vendor-check) passes on the dev host"
    requirement: INFR-01
    verification:
      - kind: integration
        ref: "make check exit 0"
        status: pass
    human_judgment: false
  - id: D6
    description: "CI image job builds with smoke and probes health, STL and STEP"
    requirement: INFR-01
    verification:
      - kind: other
        ref: ".github/workflows/ci.yml image job (YAML parses; not runnable on this host)"
        status: unknown
    human_judgment: true
    rationale: "A GitHub Actions job cannot be executed locally; its first real run is on the next push or PR"

duration: 10min
completed: 2026-10-06
status: complete
---

# Phase 1 Plan 06: Container delivery Summary

**A linux/amd64 runtime closure resolved and smoke-proved in a fresh container, a non-root read-only localhost-only image that tests itself at build, compose with INTERIM-labelled limits, `make check` as the local copy of CI, and a CI image job that builds and probes it**

## Performance

- **Duration:** about 10 min (the amd64 resolve under emulation took about 3 min)
- **Started:** 2026-10-06T05:22:00Z
- **Completed:** 2026-10-06T05:31:00Z
- **Tasks:** 2
- **Files modified:** 8 (4 created, 4 modified)

## Accomplishments

- `make lock` now runs `docker/refresh-requirements.sh`: fresh `pip install /src` in `python:3.12-slim-bookworm` under `--platform linux/amd64`, spur's prune list, `docker/smoke.py` as the proof, then a freeze. Result: 32 packages, header naming the script, `cadquery==2.8.0` and `cadquery-ocp==7.9.3.1.1`, no gate-tool line.
- The image installs that closure with `--no-deps`, runs `docker/smoke.py` during the build, runs as uid 10001 and ends in `CMD ["screw", "serve"]`. `docker image inspect` reports `linux/amd64`.
- `compose.yaml` publishes `127.0.0.1:8000:8000` only, with `read_only`, `cap_drop: [ALL]`, `no-new-privileges`, `mem_limit: 4g` and `tmpfs /tmp:size=256m`.
- `make check` = `verify smoke vendor-check`; `up`, `down`, `logs`, `clean-docker` added; the host-side lock venv and the `LOCK_VENV` variable are gone; nothing runs pytest inside the image (D-18).
- The D-02 interim-bounds item gained the `SCREW_WORKERS`, `mem_limit`, HEALTHCHECK and tmpfs rows and lost its "plan 01-06 appends" note.

## Task Commits

1. **Task 1: runtime closure resolved in linux/amd64, image that smoke-tests itself at build** - `ff4b22c` (feat)
2. **Task 2: compose on localhost, `make check` mirrors CI, CI builds and probes the image** - `d2af1b9` (feat)

**Plan metadata:** committed with this summary (docs: complete plan)

## Files Created/Modified

- `docker/refresh-requirements.sh` - the runtime-closure resolver (replaces the host-side freeze, L07); executable
- `Dockerfile` - pinned closure, smoke at build, non-root, healthcheck, INTERIM notes
- `.dockerignore` - spur's list plus `.planning`, `bench`, `scripts`
- `compose.yaml` - the local service with the INTERIM memory cap
- `requirements.txt` - regenerated: 32-package amd64 runtime closure
- `Makefile` - `lock`, `image`, `smoke`, `check`, `up`, `down`, `logs`, `clean-docker`, `IMAGE`, `PLATFORM`, `PLATFORM_ARG`
- `.github/workflows/ci.yml` - the `image` job
- `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` - four new rows

## Decisions Made

- Used `docker build`/`run --platform linux/amd64` emulation for the resolve; it worked, so no checkpoint was needed. The dev host also exports `DOCKER_DEFAULT_PLATFORM=linux/amd64`, so `make image`, `make smoke` and `make up` built and ran the amd64 image without `PLATFORM=`.
- Resolve moved no runtime version (Pitfall 10 did not fire). The old file differed only by the gate tools (ruff, mypy, pytest, import-linter, pre-commit and their dependencies) and spur's pruned packages (matplotlib, numba, scipy, trame, pillow and friends).
- Kept the comments' wording of the INTERIM label identical across Dockerfile, compose.yaml and the debt rows, so one grep for `INTERIM` finds every carried spur figure.

## Deviations from Plan

None - plan executed exactly as written.

The one departure in method, recorded so it is not hidden: `make up` as written failed on this host because a spur container (`spur-spur-1`, not this project's) already holds `127.0.0.1:8000`. I did not stop it. I ran `make up` itself with `COMPOSE_FILE=compose.yaml:<scratch override>` that remaps only the published port to 8001, then curled 8001. Everything else (image, limits, healthcheck, user) is the committed configuration. The unmodified `127.0.0.1:8000:8000` mapping is therefore untested on this host; it is a one-line, spur-identical mapping.

## Issues Encountered

- Port 8000 held by another project's running container (above).
- `useradd` prints `uid 10001 is greater than SYS_UID_MAX 999` during the build; it is a warning, the user is created, and spur's Dockerfile does the same.
- The plan-level commit ledger (`gsd-plan-head-before-01-06`) was written after the first commit rather than before it; the base recorded is the HEAD at plan start (`6795e29`), so the measured commit count is correct.

## Known Stubs

None.

## What ran here and what did not

- Ran here: `make lock` (amd64 emulation), `make verify` (175 passed, `Contracts: 6 kept, 0 broken`), `make smoke`, `make up`/`make down` (via the port override), `make check` (exit 0), all grep acceptance criteria.
- Did not run: the CI `image` job. It is written to spur's shape with the screw paths and `screw:ci`, and its YAML parses, but a GitHub Actions job cannot run on this host. First real exercise is the next push or PR. It builds natively on amd64 runners, which is also a free second proof of the closure.
- Not tested: the unmodified `127.0.0.1:8000:8000` publish (see Deviations).

## Threat Flags

None. T-01-20 to T-01-23 mitigations are in place as planned (uid 10001, read-only root, cap_drop ALL, no-new-privileges, tmpfs bounded at 256m, 127.0.0.1 bind, INTERIM mem_limit, resolve plus smoke at lock and at build); T-01-24 accepted unchanged.

## Next Phase Readiness

- 01-07 can record L08 (gate tools float, D-17); `requirements.txt` already says so in its header.
- Phase 7 owns the re-sweep of every INTERIM row (OPER-02); the D-02 item lists them all.

## Self-Check: PASSED

- Files: `docker/refresh-requirements.sh`, `Dockerfile`, `.dockerignore`, `compose.yaml`, `requirements.txt` present.
- Commits `ff4b22c` and `d2af1b9` are ancestors of HEAD.

---
*Phase: 01-runtime-port-and-walking-skeleton*
*Completed: 2026-10-06*
