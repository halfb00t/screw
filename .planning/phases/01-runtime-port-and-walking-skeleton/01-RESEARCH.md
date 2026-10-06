# Phase 1: Runtime Port and Walking Skeleton - Research

**Researched:** 2026-10-05
**Domain:** porting a measured FastAPI + process-pool + CadQuery runtime (spur) onto a new multi-kind parameter registry; a skeleton `bolt` kind; repo-wall tooling; Docker/CI delivery
**Confidence:** HIGH on the port mechanics (spur's runtime tests were run green on screw's pinned stack, see below); MEDIUM on the new design pieces (registry-driven info panel, parity test shape), which are recommendations, not facts

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Interim runtime bounds (OPER-01/02/03 are Phase 7; the ported pool needs values to run)**
- **D-01:** spur's shipping figures are carried as explicitly labelled **interim** defaults:
  `SCREW_BUILD_TIMEOUT=30` s, `SCREW_BUILD_WORKERS=2`, `SCREW_MAX_QUEUED_BUILDS=2×workers`,
  `SCREW_EXPORT_CACHE_MB=64`, the gzip level spur L19 measured, `SCREW_WORKERS=1` (one
  server process), compose `mem_limit: 4g`. Every such constant carries a comment reading
  `INTERIM` + the spur entry it came from (L17/L19/L34) + "Phase 7 re-sweeps (OPER-02)".
  None is presented as measured for screw. Not measured on the skeleton; not waited for from
  the spike.
- **D-02:** One tech-debt item, `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md`
  (from `docs/tech_debt/TEMPLATE.md`, INDEX row in the same commit), `Severity: must`,
  trigger "Phase 7 operability re-sweep", enumerating every interim knob, its value and its
  spur source so Phase 7 cannot miss one. Resolved in Phase 7's commit per AGENTS.md.
- **D-03:** `compose.yaml` ships `mem_limit: 4g` as interim rather than uncapped: a labelled
  cap beats none, and the skeleton is lighter than the gear corpus 4g was measured on.

**Skeleton shape and frozen defaults**
- **D-04:** The `bolt` kind builds a plain cylinder of diameter `d` and length `length`.
  No head, no chamfer, no thread: head dimensions come from ISO 4014/4017 rows in Phase 4
  and bolt ends from ISO 4753 in Phase 5; inventing either now is the plausible number L02
  forbids. `pitch` is a validated model field with no geometric effect until Phase 3.
- **D-05:** Frozen defaults: `d=6.0`, `pitch=1.0`, `length=20.0` (absolute mm, L02).
  — **Reversibility:** one-way — every shareable link omits fields at default; moving a
  default silently rebuilds a different part from an old link. `ASSUMPTION:` 1.0 mm is the
  ISO 262 coarse pitch for M6; Phase 4's ISO 262 row test must assert the default
  `(d, pitch)` equals a row. Phase 5's `defaults mate` test guards the pair.
- **D-06:** Info panel for the skeleton: `d`, `pitch`, `length` echoed; `volume` as the
  closed form π·(d/2)²·length (INFO-03's shape from day one, never the kernel's
  `Volume()`); and a standing entry in `warnings`:
  `walking skeleton: plain unthreaded cylinder, not a product build`. Same document on
  `/api/bolt/info` and `screw info bolt` (parity). Version stays `0.0.x`; no release tag.
- **D-07:** Validation at the model boundary: `d > 0`, `pitch > 0`, `length > 0`, all
  finite. No size or length cap: a cap is an unmeasured number; the interim timeout is the
  backstop; Phase 7 sets caps from the sweep (OPER-03). `pitch >= d` is a Phase 3 question.

**API paths, kind selector, parity proof**
- **D-08:** Routes: `GET /api/{kind}/info` and `GET /api/{kind}/model.{stl,step}` written
  explicitly per kind (two five-line routes delegating to one `_serve()`; no route loop —
  mypy `disallow_any_explicit`, L04); `GET /api/schema?kind=` with `kind` required (no
  API-side default); `GET /api/kinds`; `GET /api/health` global. An unknown kind is a 404
  by construction. A field the kind does not define is a `422` naming it (`extra="forbid"`
  on a `Query()` model, research Q1). — **Reversibility:** costly — the URL shape is the
  API contract every consumer and the UI bind to.
- **D-09:** The UI renders a kind selector from `/api/kinds` now, with one entry; the form
  fetches `api/schema?kind=<kind>`; `kind=` omitted in the hash means `bolt`.
  — **Reversibility:** one-way — the hash is the shareable link; an omitted `kind` must
  mean `bolt` forever (L02). Phase 5 adds a nut by a registry entry, not by JS edits.
- **D-10:** The one parity test iterates `KINDS` and asserts, per kind: API schema
  `properties` == the model's fields; a foreign field on `/api/{kind}/info` is a `422`
  naming it; the CLI subparser's flags == the model's fields and a foreign flag exits 2
  naming it; `static/app.js` builds the form from `schema.properties` and contains no
  field-name literal (source assertion, spur's `test_every_key_the_ui_reads...` pattern);
  the hash round-trips every field through generic code. No browser in the gate (L01).
  The test stays in `make verify` for every later phase (SC2).

**Walling `main` and the landing flow**
- **D-11:** The wall's code lands in this phase on the phase branch: `scripts/pr_land.py`,
  `scripts/skip_tokens.py` and their tests, the `commit-msg` hook in
  `.pre-commit-config.yaml` (`default_install_hook_types: [pre-commit, commit-msg]`, verify
  pinned to `stages: [pre-commit]`), `.github/workflows/required-jobs.txt`, the `image` and
  `vendor-bundle` CI jobs, `make pr.land`. The GitHub ruleset itself is enabled by the owner
  **after** the Phase 1 PR merges (the `image`/`vendor-bundle` jobs it requires do not exist
  on `main` before that), as the phase's last manual checkpoint, with spur's
  `docs/HOW_TO_DEVELOP.md` §8 `gh api` calls. The planner writes this as a checkpoint task,
  not an automated one. Same commit: a new `Lxx` in `docs/architecture/decision_log.md`
  (walls `main`, cites spur L22/L25), `docs/ideas/2026-10-05-wall-main-like-spur.md` closed
  (INDEX row updated), `docs/HOW_TO_DEVELOP.md` §0 and §9 updated to `make pr.land`.
- **D-12:** Phase 1 lands as one PR from `gsd/phase-01-runtime-port-and-walking-skeleton`
  with plan-level commits on the branch; the reviewer reads per commit. Merged with
  `gh pr merge --squash --delete-branch` (pre-wall, HOW_TO_DEVELOP §9).
- **D-13:** `main` was pushed before the phase PR (this session), so the PR diff is phase
  work only.

### Claude's Discretion
- Env prefix `SPUR_*` → `SCREW_*`; the 503 text says "parts", not "gears".
- The `httpx` dev dependency starlette's `TestClient` needs (research: `starlette 1.7.0`
  refuses without it — verify the exact package name on the pinned stack, then `make lock`).
- Coverage floor: spur L34's rule (`floor(L - max(0.25, S))`, measured on the finished
  skeleton suite, serial baseline vs `-n 8` spread) — pinned in the phase's last plan, never
  a round number; the measurement recorded in `bench/RESULTS.md` or the decision entry.
- `records.py` log fields from `params.model_dump()` plus `kind`.
- `bench/` corpus for the skeleton: a grid over `d × length`; the harness runs, the numbers
  are not bounds (L07).
- Per-kind query subclasses (`BoltModelQuery(BoltParams, _Quality)`) plus one generic
  `strip()` helper, per research Q1; `quality: preview|fine` inherited.
- The checkbox branch for boolean fields lands with the first boolean field (Phase 3), not
  now. `argparse.BooleanOptionalAction` likewise.
- `screw pair` is Phase 5; `screw serve | info | export` here.
- Import-linter contracts landing here: 1 (present), 2, 3, 4, 5, 8 as written in research
  ARCHITECTURE.md § Import-linter contracts; 6 and 7 in Phase 4, 9 in Phase 5.
- Module layout per research § Recommended Project Structure (`calc/`, `solid/` as packages
  from the start; `tables/` absent until Phase 4).

### Deferred Ideas (OUT OF SCOPE)
- Boolean form control (checkbox) and `argparse.BooleanOptionalAction` — Phase 3, with
  `left_hand`.
- `screw pair` subcommand — Phase 5.
- Import-linter contracts 6, 7 — Phase 4; contract 9 — Phase 5.
- Runtime bounds measured for threaded parts on linux/amd64 — Phase 7 (D-02's trigger).

Roadmap wording corrected by CONTEXT (planner: build to this, not to the loose text): SC1 "schema and health under the `bolt` kind path" means D-08's shape (schema is `/api/schema?kind=`, health is global); SC3 "the `main` ruleset [is] in place" means the code lands here and the owner enables the GitHub ruleset after the Phase 1 PR merges (D-11).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INFR-01 | spur's runtime ported per L07 over screw's models, with a walking-skeleton kind | "Port Inventory" below maps every spur file to copy / retype / rewrite / skip. spur's `pool`, `records`, `app`, `cli` and their tests were run unmodified on screw's pinned stack: 212 tests passed, `src/`, `docker/`, `scripts/` type-check clean under screw's mypy 2.4.0 [VERIFIED: ran this session, see Summary] |
| INFR-02 | Module graph enforced by import-linter: inherited contracts plus kernel-doorway and "app never imports the kernel by any path" | Contracts 4, 5 and 8 run against a scratch package, kept and broken both observed [VERIFIED: ran this session]; contracts 2 and 3 are spur's verbatim (read, not re-run); config in "Code Examples" |
| FRNT-01 | One frozen Pydantic model per kind over a shared base, registered by `kind`; foreign field is a `422` naming it | `extra="forbid"` + `Query()` subclass returned `422 extra_forbidden loc ["query","m"]`; class-aware hash/eq confirmed [VERIFIED: ran this session] |
| FRNT-02 | UI generated from `/api/schema`: form, live preview, info panel, shareable URL with defaults omitted | spur `static/app.js` read in full; schema emits `exclusiveMinimum` (not `minimum`) for `gt=`, `kind` switch needs form rebuild; see Pitfalls 3, 6, 7 |
| FRNT-03 | API serves info, STL, STEP, schema, health per kind; admission control in the web layer only | spur `app.py` read in full; `_serve()` lift and 503/`Retry-After` mapping documented; contract 5 keeps it kernel-free |
| FRNT-04 | CLI `serve | info | export` with flags generated from the model; never imports the web layer | argparse generation per kind; `allow_abbrev=False` required or `--len` silently binds to `--length` [VERIFIED: ran this session]; contract 3 |
| FRNT-05 | Each kind ships on all three front ends with parity proven by one test over the registry | Parity test design with a positive control; spur's `\.field\b` JS regex false-positives on `length` (Pitfall 3) |
</phase_requirements>

## Summary

Phase 1 is a port plus one new design seam. The port is low risk: spur's runtime files (`pool.py`, `records.py`, `build_errors.py`, `app.py`, `cli.py`) and their generic tests were run against screw's pinned stack (fastapi 0.142.2, starlette 1.7.0, pydantic 2.13.5, uvicorn 0.54.0, mypy 2.4.0, ruff 0.16.10) with `httpx2` added: 212 tests passed (114 in `test_pool/test_records/test_pr_land/test_skip_tokens`, 98 in `test_api/test_cli`), ruff clean, and mypy reported no errors in `src`, `docker` or `scripts`. The only mypy failures (28) were in tests and bench and all trace to `httpx` (3 import-not-found, 23 `TestClient.get(params=<dict[str, object]>)` and 2 `**<dict[str, object]>` typing errors under starlette 1.7.0). The ported spur surface is unchanged since `ec195fb` (empty `git diff --stat ec195fb..HEAD` over `src scripts docker .github Makefile pyproject.toml bench tests Dockerfile compose.yaml .pre-commit-config.yaml web`; spur HEAD is now `f235e38`, docs commits only).

The real risk sits in what spur does not have: the kind registry, per-kind routes, a generic info panel, the parity test, and the repo wall for a repository that has no ruleset yet. Research found nine things that qualify or conflict with CONTEXT or that CONTEXT does not list, and the planner should surface the first eight to the owner before locking plans (section "Findings to Surface"): (1) with no size cap (D-07), a preview request at `d=1e7` mm took 25 s and 6.0 GiB RSS on this host, above the interim `mem_limit: 4g`, so the timeout is not a sufficient backstop; (2) `?d=1e200` passes validation and the closed-form volume raises `OverflowError`, a 500; (3) spur's "no field literal in `app.js`" regex flags `.length` in `Vector3.length()`, so the parity test fails on day one for a field called `length`; (4) spur's open `must` debt (same-slot timeout race gives a 500) travels with `pool.py`; (5) replacing L06's freeze with L07's image closure drops the pins on the gate's own tools; (6) screw's `ci.yml` has no `strategy.matrix`, which spur's drift test requires, and GitHub has no ruleset to PUT to, it must be created; (7) L01's stated reason for the 3.12 ceiling (no newer wheels) is false for the pinned kernel on PyPI today; (8) the info panel cannot be both "no field literals in JS" and "nut by registry entry" with spur's `DIMS` table, so the info document needs a self-describing shape; (9) D-01's interim-knob list misses several constants the port carries.

**Primary recommendation:** Port mechanically in this order (kernel-free foundation, app/cli/parity, UI + vendored bundle, wall tooling, image + compose, bench + coverage floor + docs, owner checkpoint last), keep every ported file's structure so a later shared-package extraction stays mechanical, apply the pool race guard and the `OverflowError` guard as the two deliberate divergences, and make the info document self-describing (`rows` of label/value/unit plus `warnings`) so the UI carries no per-kind literals.

## Project Constraints (from CLAUDE.md)

Extracted directives the planner must verify compliance with (same authority as locked decisions):

- **Gate:** nothing is done until `make verify` passes; state the command run and its result line. `make verify` = ruff + mypy `--strict` + import-linter + unfinished-work scan + pytest, no Docker.
- **Python 3.12 only** (L01); `Any` is not written (L04): untyped values are `object`, narrowed; library aliases (e.g. `Message`, `JsonSchemaValue`) are kept.
- **L02:** a value that cannot be computed honestly is a warning and no number; defaults are absolute mm and never silently change; trim-and-warn only when no explicit choice is contradicted, a direct conflict is a `422` naming the fields.
- **Pure maths never imports `cadquery`** (and its import-boundary contract lands in the same commit as the module); vendor types stop at their boundary (`cadquery` objects do not escape `solid`); a parameter is validated once at the model boundary and trusted afterwards.
- **Stop and ask first** on: claims not in the decision log, a locked decision that looks wrong, an acceptance criterion that cannot be met as written, evidence conflicts, destructive operations, stability-for-speed trades. Ask format: trigger, 2-3 options, recommendation.
- **Decisions:** new non-trivial choice gets 2-3 options and a recommendation, then a new `Lxx` (next free id is `L08`). Flag guesses as `ASSUMPTION:`.
- **Simplicity:** no speculative features; surgical edits; one concern per commit; consistency with existing naming/layout beats a locally better idea; comments carry the measurement or constraint.
- **Finishing:** new behaviour ships with its tests in the same change; performance/memory claims are measured and recorded; no `TODO`/`pass`/unreachable branches (`make verify` fails on the markers); deliberate corner cuts are `docs/tech_debt/` items with the owner's sign-off.
- **Capturing:** one file per item from `docs/<dir>/TEMPLATE.md` plus an INDEX row in the same commit; resolving debt = flip status, add sha, `git mv` to `resolved/`, move INDEX row, same commit; state before the final reply whether any item was filed.
- **Tools:** use `make` targets; start file-changing work through a gsd entry point; Conventional Commits in normal prose; English throughout; cross-CLI review (whoever wrote the diff does not review it).
- **Project skills:** `.claude/skills/` and `.ai_skills/` hold only a README (no skills defined) [VERIFIED: listed this session].

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Parameter model, registry, field metadata (group/unit/step) | Parameters (`params.py`, kernel-free) | none | One source of truth for the form, CLI flags, API query and schema; validated once at this boundary |
| Closed-form info (echo, volume, standing warning) | Thread/part maths (`calc/`, kernel-free) | none | Runs on every keystroke, must never import the kernel; INFO-03 forbids the kernel's `Volume()` |
| Build + STL/STEP export, solid cache, mesh-on-copy | CAD kernel (`solid/`, worker process only) | none | Only module allowed to import `cadquery`/`OCP`; runs inside spawned workers |
| Worker lifecycle, hash affinity, per-build timeout, kill-and-replace | Pool (`pool.py`) | none | Names the kernel only through `importlib` at runtime so `app` has no static path to it |
| Admission control, 503 + `Retry-After`, bytes cache, gzip | HTTP API (`app.py`, web layer only) | none | L04 (spur): a CLI export must never queue; keeps the parent kernel-free so memory is a statement about workers |
| Structured logging | `records.py` | `app.py`, `pool.py` call it | One vocabulary; configured at two idempotent call sites (spur L20) |
| Form, preview, info panel, share link | Browser (`static/app.js`, vendored three.js) | API serves schema/info/STL | Vanilla JS; the hash is the store (no accounts); WebGL cannot be tested in the gate |
| CLI (`serve/info/export`) | CLI (`cli.py`) | `solid` by lazy import inside a command | Never imports the web layer (contract 3); `export` builds in-process |
| Merge wall (skip-token hook, `pr_land`, ruleset) | Repository tooling (`scripts/`, `.github/`, GitHub setting) | owner (ruleset) | Ruleset is a repository setting outside git, applied by the owner after merge (D-11) |
| Image + closure pinning | Packaging (`Dockerfile`, `docker/`) | CI `image` job | `requirements.txt` is regenerated inside linux/amd64 and installed `--no-deps` |

## Standard Stack

### Core (runtime, already pinned in `requirements.txt`)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| cadquery | 2.8.0 | solid construction and STL/STEP export | L01; `cadquery 2.8.0` requires `cadquery-ocp<8.0,>=7.9.3.1` [VERIFIED: PyPI JSON `requires_dist`] |
| cadquery-ocp | 7.9.3.1.1 | OpenCascade binding | PyPI latest is 8.0.1.1.0 but cadquery 2.8.0 caps it below 8.0 [VERIFIED: pip index + PyPI JSON], so the pin stays |
| fastapi | 0.142.2 | HTTP API | latest on PyPI [VERIFIED: pip index versions] |
| starlette | 1.7.0 | ASGI; `TestClient` prefers `httpx2` | latest on PyPI; `testclient.py` imports `httpx2` first and warns on `httpx` [VERIFIED: file read] |
| pydantic | 2.13.5 | frozen models, JSON schema, query models | latest on PyPI [VERIFIED: pip index versions] |
| uvicorn | 0.54.0 | ASGI server | latest on PyPI [VERIFIED: pip index versions] |

### Supporting (dev extras to add to `pyproject.toml`)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx2 | 2.13.1 | `starlette.testclient` backend; also the bench HTTP client | add as a dev dependency; no `filterwarnings` carve-out needed (see Pitfall 1) |
| pytest-xdist | 3.8.0 | `-n 8` gate parallelism (spur L34) | in spur's dev extras [CITED: spur `pyproject.toml` dev list] |
| pytest-cov | 7.1.0 | coverage floor | in spur's dev extras [CITED: spur `pyproject.toml` dev list]; pytest-cov 7 dropped its subprocess hook, so `[tool.coverage.run] concurrency = ["multiprocessing", "thread"]` is what counts worker lines [CITED: spur `pyproject.toml:141` and L34] |
| import-linter | 2.15 | module boundaries | already pinned; `ignore_imports` and wildcard behaviour verified below |
| three.js (vendored) | 0.186.0 | viewer | pinned by spur's `web/package-lock.json`; rebuild is byte-identical (below); do not bump (latest on npm is 0.186.1) |
| esbuild (dev, Node only) | 0.25.12 | builds the bundle | pinned by the lockfile; npm latest is 0.28.2, do not bump |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `httpx2` | `httpx` plus spur's `ignore:Using \`httpx\`` filter | works but `starlette 1.7.0` emits `StarletteDeprecationWarning` which `filterwarnings = ["error"]` turns into a failure unless filtered [VERIFIED: ran `-W error`]; httpx2 is the path starlette now prefers |
| route loop for per-kind routes | explicit routes (D-08, locked) | loop needs a runtime-built annotation which `disallow_any_explicit` rejects |

**Installation (dev extras, then re-lock):**
```bash
# pyproject.toml [project.optional-dependencies].dev += "httpx2>=2.13", "pytest-xdist>=3.8", "pytest-cov>=7.1"
# dry-run under the existing constraint resolved cleanly: would install
# coverage-7.16.2 execnet-2.1.2 httpcore2-2.13.1 httpx2-2.13.1 pytest-cov-7.1.0 pytest-xdist-3.8.0 truststore-0.10.4
make lock   # becomes docker/refresh-requirements.sh (see Port Inventory); dev extras are NOT in the image closure
```

**Version verification:** every version above was read from `requirements.txt` and confirmed with `pip index versions <pkg>` on 2026-10-05 (fastapi 0.142.2, starlette 1.7.0, pydantic 2.13.5, uvicorn 0.54.0, cadquery 2.8.0, import-linter 2.15, pytest 9.1.1, pytest-xdist 3.8.0, pytest-cov 7.1.0, httpx2 2.13.1, ruff 0.16.10, mypy 2.4.0, pre-commit 4.6.2). `make lock` via the image may move runtime versions to whatever is current at refresh time; re-run the registry checks in "Code Examples" after it.

## Package Legitimacy Audit

Run: `gsd_run query package-legitimacy check --ecosystem pypi|npm ...` on 2026-10-05. The seam has no download telemetry for PyPI (`weeklyDownloads: null`), so every PyPI package reads `SUS` with reason `unknown-downloads`; that is a gap in the tool's data, not a finding about the packages.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| httpx2 | PyPI | repo created 2026-05-11, latest 2.13.1 published 2026-09-23 | n/a | github.com/pydantic/httpx2 (1518 stars, not archived, pushed 2026-10-01) | SUS (`too-new`, `unknown-downloads`) | Flagged. Named by starlette 1.7.0's own `testclient.py` as the required package [VERIFIED: file read]; pulls `httpcore2`, `truststore`. Planner adds one `checkpoint:human-verify` before the install |
| pytest-xdist | PyPI | 3.8.0 published 2025-07-01 | n/a | github.com/pytest-dev/pytest-xdist | SUS (`unknown-downloads`) | Flagged for the same checkpoint; spur has run it since Phase 15 [CITED: spur L34] |
| pytest-cov | PyPI | 7.1.0 published 2026-03-21 | n/a | none reported by the seam | SUS (`unknown-downloads`, `no-repository`) | Flagged for the same checkpoint; spur's dev dependency [CITED: spur `pyproject.toml`] |
| esbuild | npm | 0.25.12 pinned; latest published 2026-08-08 | 359M/wk | github.com/evanw/esbuild | OK | Approved. Has `scripts.postinstall: node install.js` (platform-binary check); installed under `npm ci` with the committed lockfile, as spur does |
| three | npm | 0.186.0 pinned; 0.186.1 latest published 2026-09-24 | 24M/wk | github.com/mrdoob/three.js | SUS (`too-new`, applies to the newest publish, not the pinned 0.186.0) | No new install decision: the bundle and lockfile are copied from spur unchanged. Do not run `npm update` |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** httpx2, pytest-xdist, pytest-cov (one combined human-verify checkpoint), three (no action, pinned and vendored)

Python package names here come from spur's `pyproject.toml` and starlette's own source, both read this session; the registry check confirms they exist on PyPI and nothing else.

## Port Inventory

Source is spur at `ec195fb` (HEAD `f235e38`, ported surface unchanged). "Retype" = same structure, names changed; "Rewrite" = new shape.

| spur file | Action | What changes, and traps |
|-----------|--------|-------------------------|
| `src/spur/__init__.py` | Retype | keep `int_env` (positive int env var, falls back on nonsense) and `__version__`; screw's version is a hatch-dynamic read of this file, so keep `__version__ = "0.0.0"` as a single literal line |
| `src/spur/__main__.py` | Copy | add `[project.scripts] screw = "screw.cli:main"` to `pyproject.toml` (screw's has none; the Dockerfile `CMD ["screw", "serve"]` needs it) |
| `build_errors.py` | Copy | kernel-free exception pair; the `BuildTimeout` message currently ends "Try a coarser quality or fewer teeth." (`pool.py`): reword for parts |
| `pool.py` | Retype + one guard | `GearParams` becomes `FastenerParams`; `importlib.import_module("spur.model")` becomes `"screw.solid"` in both `_warm` (line 50) and `build_export` (line 63); keep `_SPAWN = mp.get_context("spawn")` (line 35) and the private `executor._processes` access with its tripwire test. **Add the identity guard from spur's open `must` debt** (Finding 4) |
| `records.py` | Retype | `_gear_fields` becomes `_part_fields` returning `{"kind", "slug", "params": p.model_dump(exclude_defaults=True)}`; `SPUR_LOG_LEVEL` becomes `SCREW_LOG_LEVEL`; keep both `configure()` call sites (spur L20) |
| `app.py` | Rewrite the route layer, keep the machinery | keep `_BlobCache`, `_build_slot`, `HealthReport`/`PoolState`, the 503 mapping (`busy`/`timeout`/`pool_broken`), gzip-in-slot, `lifespan`. Replace `info`/`model`/`schema`/`_gear` with `_serve()` + per-kind routes + `strip()` + `/api/kinds`. 503 text "gears" becomes "parts". Rename the env reads |
| `cli.py` | Rewrite the argument layer | nested subparsers per `KINDS` entry; `allow_abbrev=False` on every parser; drop `--mate-teeth`; `_params(kind, ns)`; keep `cmd_serve` (`log_config=None`, `configure()`), `cmd_export` (`BuildError` to exit code, warnings to stderr) |
| `calc.py`, `model.py`, `params.py` | **Never copy** (L07) | read for pattern only. `params._f()` (Field wrapper that stores `group`/`unit`/`step` in `json_schema_extra`) is the pattern to re-write with `gt=` and `allow_inf_nan=False` |
| `static/app.js`, `index.html`, `style.css` | Retype + generic rewrite of two parts | remove `DIMS`, `mate-teeth`, gear title/favicon; add kind selector, per-kind schema fetch, form rebuild, `kind` in hash; generic info panel (Open Question 1) |
| `static/vendor/*`, `web/` | Copy | rename `web/package.json` `name` and **change the build script's output path** `../src/spur/static/vendor/...` to `../src/screw/static/vendor/...` (it is hard-coded; a rename without that edit silently writes into a non-existent `src/spur/`) |
| `scripts/__init__.py`, `pr_land.py`, `skip_tokens.py` | Copy | no project-specific strings in the code; `WORKFLOW = "ci.yml"`; module docstrings cite spur PR numbers (fine, they are history) |
| `docker/smoke.py`, `docker/refresh-requirements.sh`, `Dockerfile`, `compose.yaml`, `.dockerignore` | Retype | image tag `spur:resolve` to `screw:resolve`, `grep -v "^spur"` to `^screw`, user `spur` to `screw`, `SPUR_*` env, smoke paths become `/api/kinds`, `/api/schema?kind=bolt`, `/api/bolt/info`, `/api/bolt/model.stl`, `.step`, and a `422` for a foreign field |
| `Makefile` | Extend | add `serve check image smoke up down logs vendor vendor-check pr.land clean-docker bench.*`; `lock` becomes `docker/refresh-requirements.sh`; `typecheck` becomes `mypy src tests docker bench scripts`; `test` becomes `pytest -n $(PYTEST_WORKERS) --cov --cov-report=term` with spur's clamp (`Makefile:94`); `no-fake-done` must also exclude `src/screw/static/vendor` |
| `pyproject.toml` | Extend | dev extras, `[project.scripts]`, `[tool.coverage.run]`/`[tool.coverage.report]` (`source = ["src/screw"]`), contracts, and **`filterwarnings`** unchanged (no `httpx` carve-out needed with httpx2) |
| `.pre-commit-config.yaml` | Copy spur's | `default_install_hook_types: [pre-commit, commit-msg]`, `verify` pinned `stages: [pre-commit]`, `no-skip-token` hook `.venv/bin/python -m scripts.skip_tokens`; the clone must re-run `.venv/bin/pre-commit install` once, only `pre-commit` is installed in `.git/hooks` today [VERIFIED: listed] |
| `.github/workflows/ci.yml`, `required-jobs.txt` | Retype | see Finding 6: the `test` job needs a `strategy.matrix.python: ["3.12"]` so its reported name is `test (3.12)` and spur's drift test (which requires a `python:` matrix list) passes; `image` job curls `/api/bolt/model.stl?quality=preview` |
| `.gitignore`, `.gitattributes` | Extend | add `web/node_modules/`, `.coverage`, `.coverage.*` to `.gitignore`; spur's `.gitattributes` marks the bundle `linguist-vendored -diff` |
| `bench/` | Port the harness, rewrite the corpus | `__init__.py` (`machine_facts`), `latency.py`, `memory.py`, `build_time.py`, `export_cost.py` keep their method; `corpus.py` becomes a `d x length` grid; drop `honeycomb_spike.py`, `tip_chamfer_spike.py`, `sweeps/*.json`, the composed scenario and `RESULTS.md` content. `build_time.py` and `export_cost.py` reach into `model._build_cached.cache_clear()`, `model._build_checked` and `model.TESSELLATION`: give `solid` a small public surface instead (`build`, `export`, `TESSELLATION`, a cache-clear hook) rather than importing privates. `bench/latency.py` and `memory.py` do `import httpx`: use `import httpx2 as httpx` (httpx2 is typed, `py.typed` present, `Client`/`Timeout`/`HTTPError`/`Response` exist [VERIFIED: imported]). There is no quiet-host gate in spur code (grep found none); it is a human-run procedure, so the harness only prints `os.getloadavg()` read **before** the first row (spur's WR-07 fix is already in `build_time.py:188`) |
| `tests/` | Port the generic ones | see Validation Architecture for the keep/rewrite/skip list; `tests/composition.py`, `tests/regression/*`, `test_calc.py`, `test_model.py` are gear-only and are not ported |

## Architecture Patterns

### System Architecture Diagram

```
 Browser (static/app.js + vendored three.js)      CLI (screw serve|info|export)
  kind selector <- GET /api/kinds                   argparse subparser per KINDS entry
  form  <- GET /api/schema?kind=<k>                 flags <- Model.model_fields
  hash  = #[kind=..&]field=..  (defaults omitted)   foreign flag -> exit 2 naming it
        |                                                |              (lazy import)
        | GET /api/<k>/info?...   GET /api/<k>/model.{stl,step}?...&quality=   |
        v                                                v                     v
 +-----------------------------------------------+   +------------------+  +--------+
 | app.py  (web layer; NO static path to kernel) |   | calc/ (kernel-   |  | solid/ |
 |  per-kind routes -> strip(q, BoltParams)      |-->| free): derive()  |  | (ONLY  |
 |  -> _serve(): bytes cache (params,fmt,quality,|   | echo, volume,    |  | doorway|
 |     encoding) -> hit: return                  |   | standing warning |  | to     |
 |     miss: _build_slot (503+Retry-After if full)|  +------------------+  | cadquery|
 |       -> pool.export(p, fmt, quality)         |                          | /OCP)  |
 |       -> gzip inside the slot (L19)           |                          +---^----+
 +----------------------+------------------------+                              |
                        | async, hash(p) % N affinity, per-build timeout        |
                        v                                                        |
 +-----------------------------------------------+   spawn + importlib           |
 | pool.py: N single-worker ProcessPoolExecutors |------------------------------+
 |  timeout -> terminate -> replace slot         |   worker: solid.export(p,fmt,quality)
 |  BrokenProcessPool -> replace slot            |     build cylinder -> 1 solid + isValid
 +-----------------------------------------------+     STL: mesh a COPY (L24)  STEP: exportStep
 records.py: one JSON line per event on stderr (parent process only)
```

### Recommended Project Structure
```
src/screw/
├── __init__.py          # __version__, int_env
├── __main__.py          # from .cli import main; main()
├── params.py            # FastenerParams (d, pitch), BoltParams (+length), KINDS, DEFAULT_KIND
├── calc/__init__.py     # derive(p) -> PartInfo (kernel-free; match on type with assert_never)
├── solid/__init__.py    # the doorway: build(), export(), TESSELLATION, _LOCK, solid cache, malloc_trim
├── solid/bolt.py        # cylinder builder (Phase 3 grows helical.py beside it)
├── pool.py  records.py  build_errors.py  app.py  cli.py
├── static/{index.html,app.js,style.css,vendor/three.bundle.min.js,vendor/three.LICENSE}
scripts/{__init__,pr_land,skip_tokens}.py
docker/{smoke.py,refresh-requirements.sh}
bench/{__init__,corpus,latency,memory,build_time,export_cost}.py, README.md, RESULTS.md
web/{entry.js,package.json,package-lock.json}
tests/...            # see Validation Architecture
```
`calc/feasibility.py` is deliberately absent: the skeleton has no cross-field rule (D-07 defers `pitch >= d` to Phase 3), so a `_feasible` validator calling an empty check would be dead code. Add it with the first cross-field rule.

### Pattern 1: Registry with a frozen default kind
**What:** each model carries `kind: ClassVar[str]`; `KINDS` maps kind to class; `DEFAULT_KIND = "bolt"` is a module constant asserted by a test with the literal `"bolt"` (L02: an omitted `kind` must mean `bolt` forever). `/api/kinds` returns `{"default": DEFAULT_KIND, "kinds": [...]}` so the JS needs no literal and registry order can never move the default.
**When to use:** always; this is what lets Phase 5 add a nut by one registry entry.
**Example:**
```python
# Source: ran against screw's pinned stack this session (pydantic 2.13.5); ClassVar kept out of fields and schema
class FastenerParams(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    kind: ClassVar[str]
    d: float = _f(6.0, gt=0, title="Diameter", group="Size", unit="mm", step=0.1)
    pitch: float = _f(1.0, gt=0, title="Pitch", group="Size", unit="mm", step=0.05)

class BoltParams(FastenerParams):
    kind: ClassVar[str] = "bolt"
    length: float = _f(20.0, gt=0, title="Length", group="Size", unit="mm", step=0.5)
# observed: list(BoltParams.model_fields) == ['d','pitch','length'], schema props identical,
# B(d=8).model_dump(exclude_defaults=True) == {'d': 8.0}, hash equal but == False across subclasses
```
`_f` must pass `allow_inf_nan=False` (without it `d=inf` passes `gt=0`; with it the response was `422 finite_number` for `inf` and `nan` [VERIFIED: ran]).

### Pattern 2: Per-kind routes over one `_serve()`, `Query()` subclass plus `strip()`
**What:** `class BoltModelQuery(BoltParams, _Quality)` for the model route; the info route takes the plain `BoltParams` so `quality` is a foreign field there (a `422` naming it, which the parity test relies on); `strip(q, BoltParams)` rebuilds the plain class so the cache key (equality includes the class) is shared across STL, STEP and preview.
**Example:**
```python
# Source: ran this session (fastapi 0.142.2). Observed responses:
#   /api/bolt/info?m=5       -> 422 {"type":"extra_forbidden","loc":["query","m"], ...}
#   /api/schema?kind=nut     -> 404 (handler raises HTTPException; a runtime-built Literal cannot satisfy mypy strict)
#   /api/schema              -> 422 {"type":"missing","loc":["query","kind"], ...}
#   /api/nut/info            -> 404 (no route)
def strip[T: FastenerParams](q: FastenerParams, cls: type[T]) -> T:
    return cls(**q.model_dump(include=set(cls.model_fields)))
```

### Pattern 3: One doorway, dispatch with `match` and `assert_never`
`solid.build(p)` and `calc.derive(p)` dispatch on `type(p)` with a `match` statement ending in `assert_never`, so adding a kind is a compile-time-visible edit in each place (ARCHITECTURE.md's "adding a kind is a closed list") instead of a silently missing dict key. [ASSUMED: design recommendation, not run]

### Pattern 4: Admission control in the web layer only
Port `_build_slot` unchanged: a `threading.BoundedSemaphore` acquired non-blocking; refusal is `503` with detail `type: "busy"` and header `Retry-After: 5` (`app.py:277-283`). The CLI never queues; contract 3 forbids `screw.cli -> screw.app/fastapi/starlette`.

### Anti-Patterns to Avoid
- **Importing `solid` from `pool` or `app` statically:** use `importlib.import_module("screw.solid")` inside the worker (spur `pool.py:50,63`); a static edge breaks contract 5.
- **A discriminated union as the one model:** FastAPI rejects it as a `Query()` model and the schema has no `properties` (ARCHITECTURE.md Q1, verified there).
- **Reading private `solid` names from `bench/`:** expose `build`/`export`/`TESSELLATION`/a cache-clear hook publicly.
- **A `DIMS`-style per-kind label table in JS:** violates D-09 ("not by JS edits") and D-10 (no field literals).
- **Copying spur numbers without the `INTERIM` label** (D-01): every carried constant gets the comment.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Merge gating | a custom merge script | spur's `scripts/pr_land.py` + `skip_tokens.py` + their tests, copied | 982 lines of `test_pr_land.py` encode the incidents recorded in spur L22 and L25 |
| Worker timeout/replacement | a new pool | spur's `BuildPool` | the mechanics (terminate via `executor._processes`, identity-guarded replacement, `BrokenProcessPool`) were found by incident; do not re-derive |
| CLI flags per kind | hand-written flags | loop over `Model.model_fields` | parity by construction; a hand list drifts |
| Form per kind | per-field HTML | `schema.properties` plus `group/unit/step` metadata | parity by construction |
| JSON log lines | a logging library | spur's `records.py` (stdlib `logging` + one formatter) | spur L20 rejected structlog against the pinned closure |
| Import boundaries | grep tests | import-linter contracts | function-level (lazy) imports are seen as edges [VERIFIED: ran, a `params -> calc.feasibility -> solid -> cadquery` chain was reported] |
| Squash-merge text rules | manual care | the `commit-msg` hook + `pr_land` message checks | the token reached `main` twice (spur L22) |
| Closure pinning | hand-edited `requirements.txt` | `docker/refresh-requirements.sh` | with `--no-deps`, pip will not tell you a hand-bumped pin broke the closure (spur L12) |

**Key insight:** every piece of the runtime is a response to a recorded incident in spur's history; the value of the port is the incident record, so port structure, comments and tests together, and diverge only deliberately (two places, below).

## Findings to Surface (conflicts and qualifications; owner decision wanted before plans lock)

Per AGENTS.md "Stop and ask first", each is: trigger, options, recommendation.

**F1. D-07 (no size cap) versus D-03 (`mem_limit: 4g`) and measured memory.**
Measured this session (macOS arm64, Apple M2 Max, 12 CPU, 32 GiB, load averages 2.86 7.26 7.68 read after the runs, one run per row, not a controlled benchmark), cylinder `length=20`, `exportStl` on a copy, `tolerance=0.08 angularTolerance=0.5` (spur's `preview`):

| `d` (mm) | triangles | mesh time | max RSS |
|---|---|---|---|
| 6 | 100 | 0.004 s | 451 MiB |
| 1e4 | 3,140 | 0.014 s | 465 MiB |
| 1e5 | 9,932 | 0.10 s | 553 MiB |
| 1e6 | 31,412 | 1.2 s | 1,159 MiB |
| 1e7 | 99,344 | 25.1 s | 6,036 MiB |
| 1e8 | did not finish in 60 s | | 14.9 GiB at kill |

At `d=1e9` the build succeeds and the mesh did not finish in 20 s. Everything up to `d=1e5` is cheap. So an unbounded `d` makes one valid-looking request exceed the interim `mem_limit: 4g` before the 30 s timeout fires: the timeout is not a sufficient backstop, memory is, and an OOM-kill takes the whole container (all workers and the parent), not one slot. Compose binds `127.0.0.1` only, which bounds the exposure to local use. [VERIFIED: ran this session; macOS RSS, not linux/container]
- Option A: keep D-07 as locked, record this table in the D-02 debt item as a known interim exposure (`Severity: must`, trigger Phase 7). Cheapest, honest, leaves a one-request OOM path.
- Option B: add one explicitly `INTERIM`-labelled upper bound on `d` and `length` chosen from this table, with the same D-01 label and a D-02 row; Phase 7 replaces it from the sweep. Violates the letter of D-07 ("no cap") but its stated reason, "a cap is an unmeasured number", no longer holds for the skeleton.
- Option C: keep no cap, add a lower-cost guard in the worker only (refuse when a closed-form triangle estimate exceeds a budget). More code, more unmeasured numbers.
- **Recommendation: B** for any non-localhost use, otherwise A. The owner decides; the planner must not choose silently.

**F2. Closed-form volume overflows on finite input.** `?d=1e200` passes `gt=0` and `allow_inf_nan=False`, then `math.pi * (p.d / 2) ** 2 * p.length` raises `OverflowError: (34, 'Result too large')`, which is a raw 500 from `/info` [VERIFIED: ran]. The kernel side already fails differently per case: `d=1e-9` builds with `isValid() == False` (so the spur-style `isValid` check gives a `BuildError`), `length=1e-9` raises `Standard_Failure`, `d=1e300` raises `ValueError: Cannot build face(s): wires not planar`, `length=1e300` raises `Standard_Failure` (all wrapped to `BuildError` by spur's `_build_checked` `except Exception` pattern) [VERIFIED: ran]. Per L02 the derived volume must become `None` with a warning when it is not finite or overflows, never a 500 and never a plausible number. Recommendation: guard in `calc`, test with `d=1e200`.

**F3. spur's "no field literal in JS" regex fails on `length`.** spur's test rejects `re.search(r"\." + re.escape(name) + r"\b", rest)` for every model field. For `length` that matches `box.getSize(new Vector3()).length()` at `static/app.js:290` and `:316` [VERIFIED: grep]. Porting the pattern verbatim fails on day one, and any future field named like a JS built-in (`length`, `size`) recurs. Recommendation: keep the quoted-literal check (`['"]name['"]`), restrict the property-access check to the receivers that carry parameter data (`info`, `prop`, `values`, `h`), and add a **positive control** in the same test (a fixture JS string containing `info.length` must be caught) so the test cannot go vacuous.

**F4. spur's open `must` debt travels with `pool.py`.** `docs/tech_debt/active/2026-10-02-same-slot-timeout-cleanup-race-produces-undocumented-500.md`: two same-slot requests that time out in one incident make the second one read `executor._processes` after `shutdown`, giving `AttributeError` and a raw 500 outside the documented `busy|timeout|pool_broken` set. With `SCREW_BUILD_WORKERS=2` and hash affinity this is reachable. The fix is narrow: in `_run_with_timeout`'s `except TimeoutError`, compare `executor` with `self._executors[hash(p) % self.workers]` before touching `_processes` and skip to `raise BuildTimeout`. AGENTS.md says to fix, not file, anything blocking; this is `must`. Recommendation: port with the guard plus a regression test, and record the divergence from spur in the new `Lxx` (it is the first change that must land in both repos, which is exactly L07's extraction trigger; note it in `docs/tech_debt/active/2026-10-05-shared-infra-extraction.md`).

**F5. L06 versus L07 on pinning the gate's own tools.** L06 says `requirements.txt` pins "including the gate's own tools, so a ruff or mypy release cannot turn the gate red on its own". L07 replaces the host freeze with `docker/refresh-requirements.sh`, whose output is the runtime closure only (spur's has 36 lines, no ruff, mypy, pytest, import-linter). After the swap those tools float. spur accepted this (L34: "a developer's venv can still drift"). The coverage floor and the green gate then depend on unpinned tools. Options: (a) follow L07 and say so in the new `Lxx` (amends L06); (b) keep a second host-side file for dev tools. Recommendation: (a), because L07 is explicit and (b) is speculative infrastructure; the owner should know L06's promise narrows.

**F6. CI naming and the ruleset do not exist yet.** (i) spur's drift test `_effective_job_names` requires `python:\s*\[...\]` in `ci.yml` (`tests/test_pr_land.py:241-242`) and expands the test job to `test (3.12)`; screw's `ci.yml` has a single `test` job with no matrix, so its reported name is `test`. Adopt spur's matrix shape, or the ported test fails with "no python matrix found". (ii) `gh api repos/halfb00t/screw/rulesets` returns `[]`, and the repo's squash settings are `COMMIT_MESSAGES`/`COMMIT_OR_PR_TITLE` [VERIFIED: gh api]; spur's `HOW_TO_DEVELOP` §8 only documents a `PUT` to an existing ruleset id, so the screw checkpoint needs a `POST` plus the `PATCH` for the squash-message setting. A draft body is in Code Examples; its `POST` was **not** run (it would change the repository), so its acceptance is `[ASSUMED]` and the checkpoint must read the wall back.

**F7. L01's stated reason for the 3.12 ceiling is no longer true of the pinned kernel.** `cadquery-ocp 7.9.3.1.1` publishes cp313 and cp314 wheels for macOS, manylinux and Windows, and `cadquery 2.8.0` declares `requires_python >=3.11` [VERIFIED: PyPI JSON]. The decision stands on other grounds (mypy floor, spur L23, the pinned closure, the unchecked wheel set of vtk and the other transitive packages), and nothing in Phase 1 depends on it. Surface for the owner; do not act in this phase.

**F8. The info document needs a self-describing shape.** See Open Question 1.

**F9. D-01's knob list is incomplete.** The port also introduces these spur-measured or spur-chosen constants, which D-02's debt item should enumerate so Phase 7 cannot miss them: `SCREW_SOLID_CACHE` default 4 (`model.py:561`), `TESSELLATION = {"preview": (0.08, 0.5), "fine": (0.01, 0.1)}` (`model.py:53`; gear-chosen absolute deviation), `Retry-After: 5` (`app.py:282`), `GZipMiddleware(minimum_size=1024, ...)` (`app.py:207`), the UI debounce `350` ms (`app.js:221`), `HEALTHCHECK --interval=30s --timeout=2s --start-period=30s`, and compose `tmpfs /tmp:size=256m`. Only the first two are measurement-bound; the rest are labelled choices.

## Runtime State Inventory

Not a rename or migration phase: greenfield port into a repository with no product code, no deployed service and no stored data. The `SPUR_*` to `SCREW_*` env prefix change touches code and compose only. Nothing found in stored data, live service config, OS-registered state, secrets, or build artifacts (verified: `git ls-files` shows only the stub package, one smoke test, docs and config).

## Common Pitfalls

### Pitfall 1: `starlette 1.7.0` `TestClient` needs `httpx2`, and the warning is an error here
**What goes wrong:** `from fastapi.testclient import TestClient` raises `RuntimeError: The starlette.testclient module requires the httpx2 package to be installed.`; with plain `httpx` it imports but emits `StarletteDeprecationWarning`, and `filterwarnings = ["error"]` (screw's `pyproject.toml:108`) fails every API test. **How to avoid:** add `httpx2` to dev extras; with it `python -W error` ran clean through `TestClient` [VERIFIED: ran]. **Also:** 23 ported test call sites pass a mixed `dict[str, object]` as `params=` and 2 unpack one into a call, which mypy rejects under starlette 1.7.0's typing (spur's own mypy run is clean on its older starlette/httpx pair); build those params as `dict[str, str | int | float | bool | None]`. **Warning signs:** `make lint`/`typecheck` red on first test port.

### Pitfall 2: the parity test is vacuous if it iterates something empty or compares a thing to itself
**What goes wrong:** `for kind in KINDS` over an accidentally empty registry passes. **How to avoid:** assert `len(KINDS) >= 1` and `DEFAULT_KIND in KINDS`; compare the API schema to `model_fields` (two independent sources), the CLI flags to `model_fields`, and give the JS check a positive control (F3). Plant a foreign field and see all three fail once, manually, and record it.

### Pitfall 3: JS field-literal assertions collide with ordinary JS (F3)
See F3. Also `'#mate-teeth'`-style DOM ids contain field-like substrings in spur; in screw the form has no extra inputs, so the quoted-literal check has no false positives from ids, but a one-letter quoted token such as `'d'` can appear in unrelated strings later (a CSS selector, a unit): anchor the property-access check to the receivers that carry parameter data and keep the quoted-literal check, and rerun it whenever a field is added.

### Pitfall 4: `allow_abbrev` silently binds a foreign flag
**What goes wrong:** argparse's default prefix matching makes `screw info bolt --len 5` set `length=5`; with `allow_abbrev=False` on every parser it exits 2. `--m 5` and `--lenght 5` exit 2 naming the argument either way (`unrecognized arguments: --m 5`) [VERIFIED: ran]. **How to avoid:** `allow_abbrev=False` on the root, the `info`/`export` parsers and each kind parser; the parity test asserts a prefix of a real flag exits 2.

### Pitfall 5: `exclusiveMinimum` is not `minimum`
`Field(gt=0)` emits `"exclusiveMinimum": 0` [VERIFIED: schema printed]; spur's builder reads `prop.minimum`/`prop.maximum` and would drop the bound silently. HTML `min` is inclusive, so leave `min` unset for exclusive bounds and let the server `422` speak; keep `step` from `json_schema_extra`.

### Pitfall 6: kind switch races and stale form state
spur builds the form once (`buildForm` appends fieldsets, `fields` and `defaults` are module-level). With a kind selector the form must `replaceChildren()`, clear `fields`/`defaults`, refetch `api/schema?kind=`, and only then `readHash()`; `hashchange` and the selector must share one path, and an in-flight fetch for the old kind must be discarded (spur's `seq` counter pattern, `app.js:171-188`). A hash with a `kind` whose form is not yet built must not be read into the wrong form.

### Pitfall 7: `kind` in the hash must be omitted at the default
Write `kind=` only when it differs from `DEFAULT_KIND` (fetched from `/api/kinds`), so every link stays what it was (L02). Test: a bolt link carries no `kind=`; reading a hash without `kind` selects the default.

### Pitfall 8: unfinished-work scan and vendored bundle
`no-fake-done` scans `*.js`; spur excludes `':!src/spur/static/vendor'`. screw's `-w` scan found no hits in the bundle today [VERIFIED: grep], but add the exclusion so a three.js comment never fails the gate (spur L11).

### Pitfall 9: the vendored bundle path is hard-coded in `web/package.json`
Renaming `spur` to `screw` in the package name is not enough; the `build` script writes to `../src/spur/static/vendor/...`. Rebuilding with only the name changed wrote to `src/spur/` in a scratch copy; with the path fixed the output is byte-identical to spur's committed bundle and LICENSE (`cmp` clean, node v22.23.1) [VERIFIED: ran]. CI's `vendor-bundle` job uses Node 22.

### Pitfall 10: image closure is regenerated in linux/amd64 and may move versions
`docker/refresh-requirements.sh` resolves `pip install /src` fresh, then prunes `trame* wslink numba llvmlite matplotlib contourpy cycler kiwisolver pillow scipy aiohttp aiosignal frozenlist multidict yarl propcache attrs msgpack`, runs `docker/smoke.py`, and freezes. Versions can differ from today's host freeze (spur's closure has `fastapi==0.141.1`, screw's has `0.142.2`). Re-run the registry checks and the whole suite after `make lock`. Docker (OrbStack, server `linux/arm64`) is present; the `linux/amd64` resolve runs under emulation and its duration is unmeasured here.

### Pitfall 11: the commit-msg hook is not active until `pre-commit install` is re-run, and it refuses gsd's ship note
Only `.git/hooks/pre-commit` exists [VERIFIED: listed]. After the config change each clone re-runs `.venv/bin/pre-commit install`. Once active, `/gsd-ship`'s hard-coded `[ci skip]` ship-note commit is refused (spur L22 D-04); write the manual step into `HOW_TO_DEVELOP` the way spur's §6 does.

### Pitfall 12: gsd's 30 s commit timeout versus the pre-commit hook
`const COMMIT_TIMEOUT_MS = 30_000;` is hard-coded in the installed gsd (`~/.claude/gsd-core/bin/lib/commands.cjs:3794`) [VERIFIED: grep]. `make verify` is 0.7 s today (cached) and will exceed 30 s once the ported suite and `-n 8 --cov` run; spur measured 63.555 s warm. Use a plain `git commit` with a long timeout for commits that trigger the hook; carry spur's active debt `2026-09-25-gsd-commit-timeout-kills-cold-verify-hook` as a screw debt item only if it recurs.

### Pitfall 13: worker coverage is flaky in serial runs
spur's `nice` debt: serial full `--cov` runs lost `pool.py` lines (0.22 points) in 3 of 3 serial runs and 0 of 5 `-n 8` runs. Measure the floor per L34's rule and do not chase it. The floor must be measured on screw's finished skeleton suite (below), never copied (spur's `fail_under = 96` is a gear-suite number).

### Pitfall 14: the "defaults omitted" rule and the standing warning
`kind=bolt`, `d=6`, `pitch=1`, `length=20` are all defaults; `?` with nothing is a valid bolt. The standing warning string (`walking skeleton: plain unthreaded cylinder, not a product build`) must be identical on API and CLI and is asserted verbatim in the parity test; the info panel must not show an `L/P` turns number (CONTEXT specifics).

## Code Examples

### import-linter contracts for 1, 2, 3, 4, 5, 8
Contracts 4, 5 and 8 were run against a scratch `screw` package with import-linter 2.15 (2 and 3 are spur's text, read only): all three reported KEPT on a clean tree, and BROKEN when `cli.py` imported `cadquery` directly (contract 8) and when `calc.feasibility` imported `screw.solid` (the `app -> params -> calc.feasibility -> solid -> cadquery` chain was reported, which is contract 5 seeing a lazy import) [VERIFIED: ran this session]. Contract 8 uses `ignore_imports` so one contract covers every module except `solid`:
```toml
# Source: scratch package run this session; import-linter 2.15
[[tool.importlinter.contracts]]
name = "Only the solid package imports the CAD kernel"
type = "forbidden"
source_modules = ["screw"]
forbidden_modules = ["cadquery", "OCP"]
# solid's own edge to the kernel is the point; any other module's direct edge is the violation.
# An ignored import that matches nothing is itself an error by default (observed:
# "No matches for ignored import screw.solid.** -> cadquery"), and `screw.solid.**` does NOT
# match `screw.solid` itself: list `screw.solid -> cadquery` now, add `screw.solid.** -> cadquery`
# in the phase that adds the first solid submodule that imports it.
ignore_imports = ["screw.solid -> cadquery"]

[[tool.importlinter.contracts]]
name = "The serving process never imports the CAD kernel"   # contract 5, port as in spur
type = "forbidden"
source_modules = ["screw.app"]
forbidden_modules = ["cadquery", "OCP"]
allow_indirect_imports = false
```
Contracts 2 (`screw.calc`, `screw.params`, `screw.cli` -> kernel, indirect allowed), 3 (`screw.cli` -> `screw.app`, `fastapi`, `starlette`), 4 (`screw.calc` -> `screw.records`, `logging`) port from `../spur/pyproject.toml` with `spur` renamed. Contract 8 as written also makes contract 2 redundant for direct imports; keep 2 as spur's inherited, named contract (CONTEXT lists it).

### CLI generation per kind
```python
# Source: argparse behaviour verified this session (Python 3.12.13)
for kind, model in KINDS.items():
    kp = kinds.add_parser(kind, allow_abbrev=False)   # on EVERY parser, or --len binds --length
    for name, field in model.model_fields.items():
        kp.add_argument("--" + name.replace("_", "-"), dest=name, default=None,
                        metavar="V", type=float if field.annotation is float else ...)
```
Observed: `['info','bolt','--len','5']` binds `length=5.0` with `allow_abbrev=True`, exits 2 with it `False`; `--m 5` exits 2 either way.

### Draft owner checkpoint commands (the POST body is [ASSUMED], read back after applying)
```sh
# 1. squash text = PR title/body (L22 D-03); current value is COMMIT_MESSAGES / COMMIT_OR_PR_TITLE
gh api -X PATCH repos/halfb00t/screw -f squash_merge_commit_title=PR_TITLE -f squash_merge_commit_message=PR_BODY

# 2. create the wall (screw has no ruleset yet; spur's doc only PUTs an existing id).
# Shape copied from spur's live ruleset 23977515 read via `gh api` this session (rules: deletion,
# non_fast_forward, pull_request with 0 approvals, required_status_checks strict, bypass_actors []).
gh api -X POST repos/halfb00t/screw/rulesets --input - <<'JSON'
{"name":"default","target":"branch","enforcement":"active","bypass_actors":[],
 "conditions":{"ref_name":{"include":["refs/heads/main"],"exclude":[]}},
 "rules":[{"type":"deletion"},{"type":"non_fast_forward"},
  {"type":"pull_request","parameters":{"required_approving_review_count":0,"dismiss_stale_reviews_on_push":false,
   "required_reviewers":[],"require_code_owner_review":false,"require_last_push_approval":false,
   "required_review_thread_resolution":false,"require_extra_approval_for_unattributed_changes":true,
   "allowed_merge_methods":["merge","squash","rebase"]}},
  {"type":"required_status_checks","parameters":{"strict_required_status_checks_policy":true,"do_not_enforce_on_create":false,
   "required_status_checks":[{"context":"test (3.12)","integration_id":15368},{"context":"vendor-bundle","integration_id":15368},{"context":"image","integration_id":15368}]}}]}
JSON

gh api repos/halfb00t/screw/rules/branches/main   # read the wall back; the names must equal required-jobs.txt
```
`integration_id: 15368` is GitHub Actions: `gh api apps/github-actions` returned `{"id":15368,"name":"GitHub Actions","slug":"github-actions"}` [VERIFIED].

### Coverage floor (spur L34 rule, to be measured, not copied)
`floor(L - max(0.25, S))` where L is the lowest of the serial `--cov` baseline and three `-n 8 --cov` totals, S is the spread of the three `-n 8` totals; `fail_under` is an integer, `precision = 2` (without it a 45.93 % total passed a floor of 46; spur `pyproject.toml:151-154`). spur's reading was L=96.99, S=0.00, giving 96. For screw the number comes from the finished skeleton suite in the phase's last plan.

### Pool race guard (the one deliberate divergence in `pool.py`)
In `_run_with_timeout`'s `except TimeoutError`, before the `for proc in executor._processes.values()` loop: `if self._executors[hash(p) % self.workers] is not executor: raise BuildTimeout(...) from None`. Regression test: ten identical same-slot requests, all expected to end as `BuildTimeout`/`503 timeout`, none as `AttributeError`. [ASSUMED: guard shape taken from the debt file's "Next step", not run]

## State of the Art

| Old Approach (spur at `ec195fb`) | Current Approach (screw today) | Impact |
|----------------------------------|-------------------------------|--------|
| `httpx` as the `TestClient` backend, filtered deprecation | `httpx2`, no filter | one dev dependency and a typing fix in ported tests (Pitfall 1) |
| `starlette 1.6.0`, `fastapi 0.141.1` | `starlette 1.7.0`, `fastapi 0.142.2` | spur's runtime tests pass unmodified on the new pair (212 passed) |
| One `GearParams`, `/api/info`, `/api/model.{fmt}`, `/api/schema` | registry, `/api/{kind}/...`, `/api/schema?kind=`, `/api/kinds` | route layer, CLI argument layer and UI form builder are rewritten |
| Gear info panel keyed by a JS `DIMS` table | self-describing info document (recommended) | no per-kind JS (Open Question 1) |
| `make lock` host freeze (screw L06) | image-resolved runtime closure (L07) | dev tools float (F5) |

**Deprecated/outdated:** spur's `--mate-teeth`, `InfoQuery`, `_gear()`, gear favicon and title, `bench/sweeps/*`, `composition.py` fixtures.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `match` + `assert_never` dispatch in `solid.build` and `calc.derive` type-checks cleanly under mypy 2.4.0 strict with the pydantic plugin | Pattern 3 | low: fall back to an `isinstance` chain |
| A2 | A self-describing `rows` info document is acceptable to the owner and compatible with later INFO-01 panels | Open Question 1 | medium: changes the typed-response style spur L21 set |
| A3 | The ruleset `POST` body above is accepted as written by the GitHub API | Code Examples | low: it is a checkpoint with a read-back; fix and re-run |
| A4 | `make test-image` would not collect `scripts`/`bench` tests (they are not mounted into the container) | Port Inventory (Makefile) | low: recommendation is to skip porting that target; no SC names it |
| A5 | The pool race guard shape from spur's debt file removes the 500 without changing the documented 503 set | F4 | medium: needs the regression test to prove it |
| A6 | `docker/refresh-requirements.sh`'s PRUNE list is still valid for the same `cadquery 2.8.0` closure and `docker/smoke.py` would catch a gap | Pitfall 10 | medium: smoke is the proof, but it was not run here |
| A7 | The `linux/amd64` resolve under emulation completes in acceptable time on the owner's host | Pitfall 10 | low: only time |
| A8 | Cylinder axis along +Z from `z=0` (`Workplane("XY").circle(d/2).extrude(length)`) is what later phases want | Architecture | low: Phase 4 defines the head; PITFALLS C8 recommends axis along Z |
| A9 | The extreme-size memory figures (F1) are the same order on linux/amd64 in a container | F1 | medium: `malloc_trim` and the allocator differ; Phase 7 re-sweeps anyway |
| A10 | `/api/kinds` as `{"default": ..., "kinds": [...]}` rather than a bare list is acceptable to D-08's "`GET /api/kinds`" | Pattern 1 | low: D-08 does not fix the body shape |

## Open Questions

1. **What is the info document's shape?**
   - What we know: D-06 fixes the content (echo of `d`, `pitch`, `length`, closed-form `volume`, the standing warning) and the parity (same document on API and CLI); D-09/D-10 forbid per-kind JS edits and field-name literals in `app.js`; spur's panel is a hard-coded JS `DIMS` table of `[key, label]` pairs with a fixed `mm` suffix (`app.js:13-38,138-148`), which cannot show `mm³` or a nut's rows.
   - What's unclear: whether the owner wants a flat typed model per kind (spur L21 style, needs JS labels) or a self-describing list.
   - Recommendation (A2): `PartInfo(kind: str, rows: list[InfoRow], warnings: list[str])` with `InfoRow(key: str, label: str, value: float, unit: str)`; `volume` is simply absent from `rows` and explained in `warnings` when it cannot be computed honestly (F2). The UI renders rows generically; the parity test asserts the same document on API and CLI and that no row key is read by name in JS. Ask the owner; if flat is chosen, the label table must live server-side and be served, not in JS.

2. **Which of F1 A/B/C, F4, F5?** Owner decisions listed above; plans depend on F1 (D-02's content) and F4 (a test and a divergence note).

3. **Should `make test-image` be ported?** Not in any success criterion; recommended skip (A4). If kept, run it once to see which modules collect.

4. **Does the new `Lxx` cover only the wall?** CONTEXT requires one for the wall. D-05, D-08 and D-09 are marked one-way/costly, and AGENTS.md says non-trivial choices get logged: recommend a second entry (registry + URL shape + frozen default kind + interim-bounds policy) in the same phase. Next free ids are `L08`, `L09`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | everything (L01) | yes | 3.12.13 (`/opt/homebrew/bin/python3.12`) | none needed |
| `.venv` with dev extras | `make verify` | yes | mypy 2.4.0, ruff 0.16.10, pytest 9.1.1, import-linter 2.15, pre-commit 4.6.2 | `make venv` |
| GNU make | all targets | yes | 4.4.1 | none |
| git | hooks, `pr_land` | yes | 2.54.0 | none |
| gh (authenticated) | `pr_land`, ruleset checkpoint | yes | logged in as halfb00t | none |
| Docker + Compose | `image`, `smoke`, `lock`, `bench.memory`, `make check` | yes | 29.4.0 (server `linux/arm64`, OrbStack), Compose v5.1.2 | `linux/amd64` resolve runs under emulation |
| Node + npm | `vendor`, `vendor-check` | yes | node v22.23.1 (CI uses 22) | none (CI job covers it) |
| GitHub repo `halfb00t/screw` | CI, wall | yes | public, `main` default, 0 rulesets, squash allowed | none |
| spur checkout `../spur` | the port | yes | HEAD `f235e38`; ported surface unchanged since `ec195fb` | none |
| Browser with WebGL | UI acceptance | not exercised here | n/a | manual UAT at verify-work (no browser in the gate, L01) |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none. Image build and smoke were not run in this session (heavy); their first run is a Wave task, not a research claim.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 (+ pytest-xdist 3.8.0, pytest-cov 7.1.0 to add) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (`--strict-markers --strict-config`, `xfail_strict`, `filterwarnings = ["error"]`) |
| Quick run command | `.venv/bin/python -m pytest tests/<file>.py -q -n0 --no-cov` (run from repo root; `scripts` and `bench` resolve only via `python -m pytest`, spur `test_bench.py` docstring) |
| Full suite command | `make verify` (ruff, mypy `src tests docker bench scripts`, `lint-imports`, `no-fake-done`, `pytest -n 8 --cov`) |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FRNT-01 | registry invariants: every `KINDS` entry has a unique `kind`, frozen, `extra=forbid`, class-aware hash/eq; `DEFAULT_KIND == "bolt"` | unit | `pytest tests/test_params.py -q -n0 --no-cov` | no, Wave 0 |
| FRNT-01 | `d`/`pitch`/`length`: `0`, negative, `inf`, `nan`, non-number are `422` naming the field | API | `pytest tests/test_api.py -k validation` | no, Wave 0 |
| FRNT-01 | foreign field on `/api/bolt/info` is `422 extra_forbidden` naming it; `quality` on `/info` is foreign | API | same | no, Wave 0 |
| FRNT-02 | UI reads `/api/kinds` and `/api/schema?kind=`; source assertions (generic loops, no field literals, positive control); hash omits `kind` at default | static source | `pytest tests/test_parity.py -k ui` | no, Wave 0 |
| FRNT-02 | live preview, form, copy link work in a browser | manual-only (WebGL, no browser in the gate, L01) | `make serve` then walk the UAT list | n/a |
| FRNT-03 | info/STL/STEP/schema/kinds/health under the per-kind paths; STL is binary, STEP starts `ISO-10303-21;`; `/api/schema` without `kind` is 422, unknown kind 404 | API | `pytest tests/test_api.py` | no, Wave 0 (port) |
| FRNT-03 | saturated service answers `503` + `Retry-After: 5`, type `busy`; timeout and broken pool map to `503` types; cache and gzip behaviour; log records | API/pool | `pytest tests/test_api.py tests/test_pool.py tests/test_records.py` | no, Wave 0 (port) |
| FRNT-03 | worker really builds off the loop; same part reaches the same worker; wedged build terminated and replaced; same-slot race yields `BuildTimeout`, never `AttributeError` (new) | pool (spawns real workers) | `pytest tests/test_pool.py -n0 --no-cov` | no, Wave 0 (port + 1 new) |
| FRNT-04 | `info` and `export` run per kind; foreign flag and abbreviation exit 2; CLI and API print the same info document; CLI never imports app | CLI + contract | `pytest tests/test_cli.py`, `make lint-imports` | no, Wave 0 (port) |
| FRNT-05 | one parity test over `KINDS`: API schema properties == model fields; CLI flags == model fields; UI generic; hash round-trip; standing warning identical | parity | `pytest tests/test_parity.py` | no, Wave 0 |
| INFR-01 | `pr_land` decision logic and the skip-token hook; `required-jobs.txt` equals `ci.yml`'s effective job names | unit | `pytest tests/test_pr_land.py tests/test_skip_tokens.py` | no, Wave 0 (port) |
| INFR-01 | `make check`: in-image smoke and vendored-bundle byte check; `make vendor-check` leaves no diff | integration (Docker, Node) | `make check` | n/a, new target |
| INFR-01 | coverage floor enforced: `make test` fails below `fail_under` | gate | `make test` | n/a, config |
| INFR-01 | bench harness runs against the skeleton (not a bound) | smoke | `make bench.build` etc. | n/a |
| INFR-02 | contracts 1,2,3,4,5,8 kept; a planted violation breaks them | contract | `make lint-imports` (+ one recorded negative control) | partial: contract 1 exists |
| F2 | volume is `None` plus a warning (not a 500) for `d=1e200`; `d=1e-9` is a `422 build_error` | API | `pytest tests/test_api.py -k overflow` | no, Wave 0 |

### Sampling Rate
- **Per task commit:** the touched file's tests with `-n0 --no-cov`, then `make lint typecheck lint-imports`.
- **Per wave merge:** `make verify`.
- **Phase gate:** `make verify` green and `make check` green (Docker) before `/gsd-verify-work`; coverage floor measured per L34 in the last plan.

### Wave 0 Gaps
- [ ] `tests/conftest.py` (autouse root-logger reset, port from spur)
- [ ] `tests/test_params.py`, `tests/test_parity.py` (new: registry and the one parity test with positive controls)
- [ ] `tests/test_api.py`, `test_cli.py`, `test_pool.py`, `test_records.py`, `test_pr_land.py`, `test_skip_tokens.py`, `test_bench.py` (port, retype; gear-specific cases dropped)
- [ ] `tests/test_solid.py` (cylinder: one valid solid, bounding box equals `d`/`length` within kernel tolerance, STL/STEP bytes, mesh-on-copy keeps the cached solid mesh-free, L24)
- [ ] Framework additions: dev extras `httpx2`, `pytest-xdist`, `pytest-cov`, then the Docker-resolved `requirements.txt`
- [ ] Replace `tests/test_smoke.py` (the stub proof of the editable install) when the first real test lands

Which spur tests port, drop or rewrite (counts from reading the files): `test_pool.py` (14 tests) port almost whole, retype `GearParams`; `test_records.py` (13) port, drop `test_calc_module_stays_log_free` only if replaced by contract 4 (keep both, as spur does); `test_pr_land.py` (982 lines) and `test_skip_tokens.py` port unchanged except nothing; `test_api.py` keep health, index/static, schema, openapi-typed-contracts (rewrite fields), queue/cache/gzip/logging tests, drop every gear-feature test; `test_cli.py` keep info/export/unknown-extension/real-process exit-code tests, rewrite the parity and refusal tests; `test_bench.py` keep the `_is_capped`, `stl_size`, `select_gzip_level`, `maxrss_bytes` predicates, drop the gear sweep pins.

## Security Domain

`security_enforcement` is enabled (absent means on), ASVS level 1.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | none, by decision: spur's active debt `no-authentication`; compose binds `127.0.0.1` only and says to put authentication in front before exposing it |
| V3 Session Management | no | no sessions; the URL is the store |
| V4 Access Control | no | single public surface; the ruleset and `pr_land` guard the repository, not the app |
| V5 Input Validation | yes | Pydantic v2 at the model boundary: `gt=0`, `allow_inf_nan=False`, `extra="forbid"`, typed `Literal` for `fmt`/`quality`; the F2 overflow guard; no free-text input reaches the kernel |
| V6 Cryptography | no | none; nothing is hashed or signed (the `hash(p)` is pool affinity, not security) |
| V8/V14 Data and config protection, supply chain | yes | pinned closure, `npm ci` with lockfile, vendored bundle byte check in CI, image runs as non-root uid, `read_only`, `cap_drop: [ALL]`, `no-new-privileges` (spur `compose.yaml`) |
| V7 Error handling and logging | yes | no worker traceback leaves through spur's own log vocabulary (spur `records.py` docstring, T-03-05); uvicorn's own exception record does carry one |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Resource exhaustion by a huge or tiny parameter (F1: `d=1e7` took 25 s and 6.0 GiB RSS) | Denial of service | per-build timeout (kills the worker), bounded admission queue, `mem_limit`; **not sufficient alone** (F1), so an owner decision on an interim bound |
| Unhandled overflow in the serving process (F2) | DoS / information (500) | guard the closed form; the info route has no timeout, it runs on the event loop's threadpool |
| Reflected content in the UI (`warnings`, field titles, error text) | Tampering (XSS) | spur's `app.js` builds nodes with `textContent`, never `innerHTML`; keep that for the new rows and kind selector (a source assertion costs one line) |
| `Content-Disposition` header built from user numbers | Tampering | the slug is built from floats formatted with `:g` (no separators or quotes) in spur; keep a test that the header filename matches `^[A-Za-z0-9_.-]+$` for extreme values |
| Supply chain: new dev dependencies, the vendored bundle, GitHub Actions pinned by tag not SHA (`actions/checkout@v4` etc., as spur) | Tampering | the legitimacy checkpoint above; byte check in CI; note the tag-pinned actions as a known spur-inherited choice, not a Phase 1 change |
| A skip token in a commit or PR text silently disabling CI | Tampering | the `commit-msg` hook and `pr_land` message check (spur L22, L25) |
| Slow-loris / unauthenticated public exposure | DoS | out of scope here: localhost bind; spur debt `no-authentication` carried by reference |

## Sources

### Primary (HIGH confidence)
- spur at `ec195fb` (HEAD `f235e38`), read in full this session: `src/spur/{pool,records,app,cli,params,build_errors,__init__,__main__}.py`, `src/spur/model.py` (header, build/export), `static/{app.js,index.html}`, `style.css` (head), `web/*`, `scripts/*` (heads and structure), `docker/*`, `Dockerfile`, `compose.yaml`, `Makefile`, `pyproject.toml`, `.pre-commit-config.yaml`, `.github/workflows/*`, `bench/*` (structure and coupling), `tests/` (inventory and `test_api.py` head), `docs/architecture/decision_log.md` (L11, L12, L13, L17, L20, L22, L25, L34, L35), `docs/HOW_TO_DEVELOP.md` §6-§8, `docs/tech_debt/active/*` (race, coverage flush, no-cancellation, commit timeout)
- screw repo files: `AGENTS.md`/`CLAUDE.md`, `docs/architecture/decision_log.md` L01-L07, `.planning/{REQUIREMENTS,STATE,ROADMAP,PROJECT}.md`, `.planning/research/{ARCHITECTURE,SUMMARY}.md`, `.planning/research/PITFALLS.md` (grep), `pyproject.toml`, `Makefile`, `requirements.txt`, `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `docs/HOW_TO_DEVELOP.md`, `docs/ideas/*`, `docs/tech_debt/*`
- Installed library source: `starlette/testclient.py` (httpx2 requirement, lines 41-62 of the file as read)
- PyPI JSON for `cadquery-ocp 7.9.3.1.1`, `8.0.1.1.0` and `cadquery 2.8.0`; `pip index versions` for every package listed; `gh api` reads of `repos/halfb00t/screw`, `repos/halfb00t/screw/rulesets`, `repos/halfb00t/spur/rulesets/23977515`, `apps/github-actions`, `repos/pydantic/httpx2`
- gsd package-legitimacy seam (`pypi`: httpx2, httpx, pytest-xdist, pytest-cov; `npm`: three, esbuild)

### Experiments run this session (reproducible; scratch scripts under the session scratchpad, not committed)
- spur's `test_pool`, `test_records`, `test_pr_land`, `test_skip_tokens` (114 passed) and `test_api`, `test_cli` (98 passed) against screw's `.venv` with `httpx2` on `PYTHONPATH`; screw's mypy 2.4.0 over `../spur` (28 errors, all `httpx`-related, none in `src`, `docker`, `scripts`) and ruff 0.16.10 (clean)
- FastAPI query-model behaviour (extra forbidden, finite, `gt`, unknown kind, missing kind), class-aware hash/eq with `ClassVar` kind, `Field(gt=0)` schema shape
- import-linter contracts on a scratch package (kept and broken, lazy-import chain, `ignore_imports` semantics)
- argparse abbreviation behaviour; vendored-bundle rebuild (byte-identical); cylinder build/mesh cost and failure modes at extreme sizes; baseline `make verify` (green, 1 test)

### Secondary (MEDIUM confidence)
- GitHub REST docs for "Create a repository ruleset" (parameter names; says nothing about Actions `integration_id`, which was confirmed by `gh api` instead)

### Tertiary (LOW confidence)
- none relied on

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, versions read from the lock and confirmed on the registry; kernel cap read from PyPI metadata
- Port mechanics: HIGH, spur's runtime and tests ran on screw's pinned stack; image/CI jobs not executed here (A6, A7)
- Architecture (registry, routes, parity): MEDIUM-HIGH for the mechanics (run), MEDIUM for the info-document recommendation (A2)
- Pitfalls: HIGH where marked VERIFIED; F1 numbers are single-run, uncontrolled-load, macOS (A9)

**Research date:** 2026-10-05
**Valid until:** 2026-11-04 for versions (the stack moves weekly: httpx2 was published 12 days before this research); the spur-surface claims hold until spur's `src`, `scripts`, `docker` change (re-check with `git diff ec195fb..HEAD`)
