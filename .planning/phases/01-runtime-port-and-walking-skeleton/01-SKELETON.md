# Walking Skeleton — screw

**Phase:** 1
**Generated:** 2026-10-06

## Capability Proven End-to-End

A user generates the registered `bolt` kind (a plain unthreaded cylinder of diameter `d` and length
`length`; `pitch` validated and echoed) from the web UI, the HTTP API and the CLI — preview, info
document, STL and STEP — all from one frozen parameter model, built in a spawned worker process,
with one registry-driven parity test proving the three front ends expose the same fields.

The tracer (plan 01-01, Task 1) is the first proof: `GET /api/bolt/model.stl` through the app,
the worker pool and the kernel doorway, checked end to end by `docker/smoke.py`. Plans 01-02..01-05
expand it into the API contract, the CLI, the UI and the parity proof; 01-06..01-09 port the
delivery and gate infrastructure L07 lists; 01-10 is the owner's post-merge ruleset.

This is an internal milestone, never released (version 0.0.x, no tag). Every info document says so:
`walking skeleton: plain unthreaded cylinder, not a product build`.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Framework | FastAPI + Pydantic v2 + uvicorn; argparse CLI; vanilla JS + vendored three.js 0.186.0 | L01; spur's proven stack (L07 port) |
| Parameter model | One frozen, `extra="forbid"` Pydantic model per kind over `FastenerParams`; `KINDS` registry; `DEFAULT_KIND = "bolt"` frozen forever | D-05, D-09, L09; a discriminated union breaks all three front ends (ARCHITECTURE Q1) |
| Defaults | `d=6.0`, `pitch=1.0`, `length=20.0` absolute mm | D-05 (one-way): every link omits defaults (L02) |
| Validation | Once, at the model: `gt=0`, finite, `le=1e5` INTERIM on `d` and `length`; foreign field is a `422` naming it | D-07 amended by D-14; L02 |
| Info document | `PartInfo(kind, rows[InfoRow(key, label, value, unit)], warnings)`; volume from the closed form, absent plus a warning when not honest | D-06, D-15; INFO-03's shape from day one |
| API shape | `GET /api/{kind}/info`, `GET /api/{kind}/model.{stl,step}` explicit per kind over one `_serve()`; `GET /api/schema?kind=` (required); `GET /api/kinds`; `GET /api/health` global | D-08 (costly), L09 |
| Shareable link | URL hash with non-default fields only; `kind=` written only when not the default; omitted means `bolt` | D-09 (one-way), L09 |
| Data layer | None. Nothing is persisted; the URL is the store. The "real read/write" of this skeleton is build -> STL/STEP export and the info document | PROJECT.md; CODING_VALUES "State" |
| Kernel isolation | Only `screw.solid` imports cadquery; workers reach it by `importlib`; `app` reaches it by no path | contracts 5 and 8 (INFR-02) |
| Concurrency | N single-worker spawn executors, hash affinity, per-build timeout with kill-and-replace, the D-16 same-slot guard; admission control (503 + Retry-After) in the web layer only | spur L04/L17 port; D-16, L09 |
| Runtime bounds | spur's figures carried as INTERIM with their source; D-14's bound measured at the corner; all listed in the D-02 debt item; Phase 7 re-sweeps | D-01, D-02, D-14 |
| Auth | None; compose binds 127.0.0.1 only | spur's no-authentication debt carried by reference |
| Deployment target | Local: `make serve` (host) and `make up` (compose, non-root, read-only); `make check` = verify + in-image smoke + vendored-bundle byte check | SC3; L07 |
| Dependency closure | `requirements.txt` = linux/amd64 runtime closure from `docker/refresh-requirements.sh`, used as the pip constraint; dev tools float | L07, D-17, L08 |
| Gate | `make verify` (ruff, mypy strict, import-linter, unfinished-work scan, pytest -n with a measured coverage floor); commit-msg hook against CI-skip tokens; `make pr.land`; owner-applied ruleset | L03, L08, D-11 |
| Directory layout | `src/screw/{params.py, calc/, solid/, pool.py, records.py, build_errors.py, app.py, cli.py, static/}`, `docker/`, `bench/`, `scripts/`, `web/`, `tests/` | RESEARCH Recommended Project Structure; `tables/` absent until Phase 4 |

## Stack Touched in Phase 1

- [x] Project scaffold — existed (L01-L07); this phase adds the package, entry point, contracts, coverage
- [x] Routing — `/api/kinds`, `/api/schema?kind=`, `/api/bolt/info`, `/api/bolt/model.{stl,step}`, `/api/health`, `/`
- [x] Data — no database by design; the build -> export path and the info document are the real read/write
- [x] UI — kind selector, schema-generated form, live preview, info panel, downloads, copy-link, all wired to the API
- [x] Deployment — `make serve`, `make up` (compose), `make check`; CI `test (3.12)`, `vendor-bundle`, `image`

## Out of Scope (Deferred to Later Slices)

- Any thread geometry; `pitch` builds nothing (Phase 3 after the Phase 2 spike)
- Heads, chamfers, bolt ends, ISO tables and presets (Phase 4; ISO 4753 ends in Phase 5)
- The nut kind, clearance, matching-part derivation, the kernel pair proof and `screw pair` (Phase 5)
- Boolean form controls and `argparse.BooleanOptionalAction` (Phase 3, with `left_hand`)
- Import-linter contracts 6 and 7 (Phase 4) and 9 (Phase 5)
- Measured runtime bounds on linux/amd64 for threaded parts (Phase 7, OPER-01/02/03)
- An in-image test target (D-18), a release, a tag
- A shared infrastructure package with spur (L07 trigger fired by D-16; owner decides)

## Subsequent Slice Plan

Each later phase adds one vertical slice on this skeleton without changing its decisions:

- Phase 2: a pre-registered thread spike picks the construction, volume estimator and turn cap
- Phase 3: the bolt kind's solid becomes a real ISO 68-1 helical thread (right or left hand) behind a postcondition gate
- Phase 4: ISO 4014/4017 presets from cited, tested table rows fill the bolt's mm fields; a traceable info panel
- Phase 5: the ISO 4032 nut joins `KINDS` (one registry entry, two routes, no JS edits) with the kernel pair proof
- Phase 6: the owner's printed test sets the clearance default and printability threshold
- Phase 7: every INTERIM bound in the D-02 item is re-swept on linux/amd64 and replaced
