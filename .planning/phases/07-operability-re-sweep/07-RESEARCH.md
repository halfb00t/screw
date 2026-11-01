# Phase 7: Operability Re-sweep - Research

**Researched:** 2026-10-26
**Domain:** runtime-bound measurement on linux/amd64 (GitHub Actions runner), a kernel-free cost model that refuses before the pool, per-artifact build timeouts, CI tiers and a `pr.land` gate change
**Confidence:** HIGH for what is in the repo (every inventory row below was read this session); MEDIUM for runner mechanics (GitHub docs plus one local container probe); no timing or memory figure is claimed for linux/amd64, because none exists yet (that is the phase's work).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Measurement host and container size**
- **D-01:** Every runtime figure is measured natively on a GitHub Actions `ubuntu-latest` runner (linux/amd64), started by `workflow_dispatch` so anyone can re-run it. Each run records the runner's `nproc`, RAM and CPU model (`/proc/cpuinfo` model name), because GitHub mixes CPU generations. CI enforces the bounds on the same host class. macOS arm64 figures are context and never a bound.
- **D-02:** The target container is runner-sized, 4 vCPU and 16 GB. `mem_limit` = the measured peak per worker × the chosen worker count + headroom, and it must stay under 16 GB. Peak memory is read from the cgroup (`memory.peak`, or `memory.max_usage_in_bytes` on cgroup v1), not from coarse RSS sampling (`docs/tech_debt/active/2026-10-06-bench-memory-sampling-is-too-coarse-for-short-corpora.md`). Reversibility: reversible - a constant in `compose.yaml` and an Lxx; a smaller deploy box later means a new sweep and a superseding entry.
- **D-03:** `SCREW_BUILD_WORKERS` is chosen by a load sweep at 1, 2 and 3 workers. The pick is the count with the best p95 latency whose peak memory fits D-02, and one core stays for uvicorn and gzip. The pick and its run go into a new Lxx. Carrying 2 over unmeasured is not allowed (OPER-02).
- **D-04:** Every measurement point takes 5 repetitions and records the median and the max. Bounds are set from the max.

**Bounding the allowed space**
- **D-05:** The allowed space is bounded by a measured, kernel-free cost model in `calc`. It predicts each artifact's cost (triangles, or bytes, plus build seconds and peak memory as the sweep shows they track) from d, pitch, length, hand, the head and nut fields, and the tessellation preset. It is fitted to the sweep and validated against it. A request whose admitted cost exceeds the measured budget is refused before the cache, the admission slot and the pool, like today's fine-STL 422. The model obeys the calc import boundary (no `cadquery`). Reversibility: costly - the model decides refusals on every front end, and the pinned refused-preset counts and the page's offered artifacts move with it.
- **D-06:** Refusal is per artifact. The info document always works. The preview STL, the fine STL and STEP are each judged against their own measured budget and refused with a `422` naming the fields. The page offers whatever fits, as with today's `Download STL (preview)`. A defaulted value that pushes a part over is capped and warned. An explicit request over budget is a `422`, never a quiet trim (L02).
- **D-07:** The model is a conservative envelope. A part is admitted only if its prediction × (1 + the worst under-prediction observed on the sweep) fits the budget. The factor and the run it came from are cited in the Lxx. Some legal parts are refused, and no over-budget part is admitted. An under-prediction found by CI fails the job, and the envelope narrows in a superseding entry.
- **D-08:** The cost model replaces `FINE_STL_ROWS`, which is retired. `MAX_TURNS` and the `INTERIM_MAX_MM` (1e5 mm) field ceiling stay only as re-measured outer walls: the kernel's own limits, like `MIN_TAIL_MM`'s SIGSEGV boundary, each cited on linux/amd64. They are never the budget. `MIN_TAIL_MM` is re-measured the same way. The pinned refused-preset count in `tests/test_presets.py` moves to the new figure.

**Timeout policy**
- **D-09:** There is one timeout per artifact: preview STL, fine STL and STEP. Each equals that artifact's worst measured build among admitted parts × 2, measured with every worker busy on admitted parts at the D-03 worker count. The ×2 factor is written in the Lxx. `SCREW_BUILD_TIMEOUT` (30 s, INTERIM) is replaced.
- **D-10:** An admitted part that still hits its timeout gets today's `503` with `Retry-After`. The worker slot is recycled, nothing is cached, and no partial file is served. The server logs the part's parameters as a cost-model miss. The timeout is the backstop behind the D-05 model, not the bound.
- **D-11:** `Retry-After` is derived from the sweep: the artifact's median build × queue depth, rounded up to whole seconds. It replaces spur's 5 s.

**Full-grid CI cadence**
- **D-12:** There are two tiers.
  - **Required:** a job in `ci.yml` (so in `required-jobs.txt` under L08) builds a small boundary set: the admitted points nearest each artifact's budget edge, plus a fixed-seed random sample of admitted points, inside the D-09 timeouts. Target about 10 minutes.
  - **Full, recording:** a separate workflow, modelled on `.github/workflows/grid.yml`, builds every catalogue row and standard length (including integer `L/P` lengths), the nut grid and a dense boundary sweep. It runs weekly and on dispatch, and it records to `bench/RESULTS.md`. A miss in either tier fails the tier.
- **D-13:** The full tier also runs on a PR whose diff touches the cost model, the budgets, the timeouts, the tessellation constants or `src/screw/solid/`, through a paths filter. `make pr.land` (`scripts/pr_land.py`, today it reads `ci.yml` only) refuses that PR while the full tier is red or missing for its head. This changes how L08 gates merges, so the planner records it as a new Lxx. Reversibility: reversible - one rule in `scripts/pr_land.py` and one workflow trigger.
  - **Constraint to resolve in research:** `grid.yml` has no `pull_request` trigger on purpose (T-3-14: no untrusted code runs with the token). A same-repo PR trigger with `permissions: contents: read` has to keep that guarantee, and the planner shows that it does.

### Claude's Discretion
Each item below is measured on the D-01 runner, cited in an Lxx, and stripped of its `INTERIM` label:
- The gzip level and `minimum_size`, and the bytes-cache budget (`SCREW_EXPORT_CACHE_MB`).
- `SCREW_SOLID_CACHE`, `SCREW_MAX_QUEUED_BUILDS`, `SCREW_WORKERS`, and the HEALTHCHECK timings.
- tmpfs `/tmp` size, and the `_release_arenas` effect on amd64.
- Tessellation presets: keep them unless the sweep shows a reason. They feed the cost model, so a change is made before fitting.
- The UI debounce (350 ms) stays a UI choice. It is relabelled as not a runtime bound rather than measured.
- The cost model's functional form and features, and the exact boundary-set size and seed.

### Deferred Ideas (OUT OF SCOPE)
- Sizing for a smaller deploy box (for example 2 vCPU / 4 GB) - a later sweep and a superseding entry once a real deploy target exists.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| OPER-01 | CAD builds run in worker processes off the event loop with a per-build timeout measured over the whole allowed grid (every size, every standard length, including integer `L/P`), recorded as a constant with its measurement cited. | "Current bound inventory" (where the timeout lives, `pool.py` shape); "The allowed grid" (294 bolt rows, 201 with integer L/P, 14 nut rows, the 1790-length L11 corpus); Pitfall 1 (the timer also counts same-slot queue wait); per-artifact timeout pattern. |
| OPER-02 | Memory ceiling, gzip level, worker count and bytes-cache budget re-swept for threaded parts on linux/amd64; none of spur's figures carried. | "Measurement mechanics" (image on a native runner, per-point container, `memory.peak`); Pitfall 2 (the existing memory driver is sequential); Pitfall 3 (tmpfs counts against the cgroup); gzip / cache / worker methods. |
| OPER-03 | Every allowed configuration builds inside the timeout; one that cannot is capped and warned or refused with a `422`, never silently shortened. | Cost-model refusal path (`download_refusal`, one rule for API, CLI, info document and page); required and full CI tiers; `pr.land` rule; Pitfall 5 (page fails when the preview itself is refused). |
</phase_requirements>

## Summary

Phase 7 replaces 16 spur-derived or interim knobs and the nut's interim ceilings with figures measured on a GitHub-hosted `ubuntu-latest` runner, then uses those measurements to bound what a user may ask for. All of the inventory is in five source files plus `Dockerfile`, `compose.yaml` and `app.js` (table below, with file:line and the verbatim values). The refusal machinery to reuse already exists and is shared by every front end: `calc.download_refusal(p, fmt, quality)` is called by `_serve` (API 422, type `fine_stl_cap`), by `cmd_export` (exit 2) and by `_downloads` (the info document's per-artifact `Download.refusal`). The cost model plugs into exactly that function, which gives D-06's per-artifact refusal and API/CLI/page parity with no new plumbing.

The work is mostly measurement and sequencing, not new mechanism. Three things in the code and in CONTEXT.md are not obvious and change the plan: (1) CONTEXT never says what the budget is. D-05 admits a part whose cost fits "the measured budget", D-09 sets the timeout from the worst admitted build, and D-03 picks workers from admitted parts, so the budget has to be fixed first and it is a product choice the sweep cannot make (Open Question 1). (2) `pool.py` starts its timeout clock when the build is submitted, so a request queued behind another build on the same worker slot spends its timeout waiting; D-09's "worst build × 2 with every worker busy" is not what the clock measures (Open Question 2, Pitfall 1). (3) The page always fetches the preview STL before it offers any download, so D-06's "the page offers whatever fits" needs an `app.js` change when the preview itself is refused (Pitfall 5).

For the catalogue the binding constraint is bytes, not seconds. A context run on this macOS arm64 host (load 6, so not quiet, not a bound) built ISO 4017 M20 x 200 in 2.28 s with a 3.94 s fine STL of 144,602,684 bytes, against a 64 MiB cache budget and a 256 MiB tmpfs. Timings on the GitHub runner will be several times slower (the pair verify cell took 167.5 s there against 42.55 s here, `2026-10-20-ci-test-job-tripled-by-two-pair-tests.md`), which is why D-01 forbids using this host.

**Primary recommendation:** Plan the phase as a measure-first sequence with two owner checkpoints: (a) a dispatchable, image-based runner harness that records one point end to end (cgroup `memory.peak`, CPU model, 5 reps) before anything else; (b) an exploration sweep that fits the cost model and produces a table of what each candidate budget keeps and refuses, then an owner ruling on the budgets (Open Question 1); then workers, timeouts, caches, CI tiers and `pr.land`. Pre-register each knob's selection rule before its run, as this repo did for the thread spike.

## Project Constraints (from CLAUDE.md)

Extracted from `/Users/half/git/halfb00t/screw/CLAUDE.md` (symlink of AGENTS.md); same authority as locked decisions.

- **The gate is `make verify`** (ruff, mypy `--strict`, import-linter, unfinished-work scan, pytest under a 96 % coverage floor). State the command and the result line; predicting is not running. `make check` = `verify smoke vendor-check` (needs Docker).
- **L02 standing rules:** a number the tool prints is one someone will cut metal to; a parameter the user did not set must never silently change the part; defaults are absolute mm and frozen; trim only when it contradicts nothing the user set, and warn; a direct conflict is a `422` naming the fields.
- **Stop and ask** when: an architectural claim is not in the decision log; a locked decision looks wrong; an acceptance criterion cannot be met as written; a library behaviour is unverified after a real check; evidence conflicts; a destructive operation; a choice trades stability for speed. Ask format: trigger, 2-3 options, recommendation, wait.
- **Decisions:** new non-trivial choice = 2-3 options + recommendation, then a new `Lxx` (next free id is **L20**, the log ends at L19). Do not re-litigate logged decisions; supersede them.
- **Measure before you claim** (CODING_VALUES): performance, memory and size statements ship with the number and the workload; comments carry the measurement that forced the constant.
- **Pure maths stays out of the kernel's way:** `calc` never imports `cadquery`, `logging` or `screw.records`; `params` and `calc.thread` never import `screw.tables`; `cadquery` objects do not escape `screw.solid`; `screw.app` never imports the kernel by any path (import-linter contracts in `pyproject.toml`).
- **`Any` is not written** (L04); a parameter is validated once at the model boundary.
- **No `TODO`/`FIXME`/`XXX`/`HACK`/`NotImplementedError`, no `type: ignore` in `src/screw/`** (`make no-fake-done`).
- **New behaviour ships with its tests in the same change;** claims about performance or memory are measured and recorded.
- **Debt:** on fixing, flip `Status: resolved`, add the commit sha, `git mv` to `resolved/`, move the INDEX row, same commit. State at the end whether any item was filed.
- **A new dependency is a decision, ask first.** This phase needs none.
- **Tools:** reuse `make` targets; start file-changing work through a gsd entry point. Commit messages: Conventional Commits. Cross-CLI review: whoever wrote the diff does not review it.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Cost model (predict triangles / bytes / seconds / memory) | `screw.calc` (pure maths, kernel-free) | `screw.params` (field bounds that remain as outer walls) | Runs on every keystroke via the info document; must obey the calc import contracts (D-05). |
| Per-artifact refusal (422 / exit 2 / `downloads[].refusal`) | `screw.calc.download_refusal` | `app._serve`, `cli.cmd_export`, `static/app.js` | One rule already shared by API, CLI and info document; refusal precedes cache, slot and pool. |
| Build timeout enforcement, worker recycle | `screw.pool.BuildPool` (parent process) | `screw.app` (maps `BuildTimeout` to 503) | The pool owns the executor and terminates the OS process; `app` owns HTTP semantics. |
| Cost-model-miss log record | `screw.records` / `screw.app` | - | `calc` must not import `logging` or `records`, so the miss is logged where the 503 is produced. |
| `Retry-After` value | `screw.app` (503 sites) | constant derived from the sweep | Three 503 sites carry the literal `"5"` today. |
| Bytes cache, gzip, admission queue | `screw.app` (serving process, kernel-free) | `GZipMiddleware` for JSON bodies | `_serve` compresses inside the admission slot; the middleware also gzips the info/schema JSON. |
| Solid cache, tessellation, `malloc_trim` | `screw.solid` (worker process) | - | Per-worker; only `solid` may touch the kernel. |
| Container memory, tmpfs, HEALTHCHECK, worker env | `compose.yaml`, `Dockerfile` | `screw.cli serve` default | Deployment-tier settings; a cgroup limit counts tmpfs. |
| Measurement harness (runner-side sweeps, fits, records) | `bench/` + a dispatch workflow | `bench/RESULTS.md`, `bench/results/` | Outside `make verify` by design (timing assertions flap). |
| CI enforcement (required boundary set; full recording tier) | `.github/workflows/ci.yml` (required) and a new workflow (recording) | `scripts/pr_land.py`, `required-jobs.txt` | L08 requires every `ci.yml` job to be green on a head; the full tier is a separate workflow plus a `pr.land` rule. |
| Artifact offering when one is refused | Browser (`static/app.js`) | - | The update loop fetches the preview STL before `setDownloads` runs. |

## Standard Stack

No new package is needed. Everything below is already in `pyproject.toml` / `requirements.txt` or the OS image. Versions verified this session in the project venv.

### Core
| Library / tool | Version | Purpose | Why standard here |
|----------------|---------|---------|-------------------|
| cadquery / cadquery-ocp | 2.8.0 / 7.9.3.1.1 | the kernel being measured | pinned in `requirements.txt` (L06/L08); the sweep must run the pinned pair [VERIFIED: `.venv` import, `bench.build_time` header] |
| FastAPI / Pydantic v2 / uvicorn | as pinned | the serving layer whose limits are re-swept | L01 |
| `concurrent.futures.ProcessPoolExecutor` (spawn) | CPython 3.12 stdlib | the worker model (one single-worker executor per slot, hash affinity) | already in `pool.py` |
| pytest + xdist + cov | 9.x / 3.8.0 / 7.1.0 | tests, marker-deselected slow tiers | L10 pins; `addopts = "--strict-markers --strict-config -m 'not grid and not pair'"` [VERIFIED: pyproject.toml:118] |
| httpx2 | 2.13.1 | HTTP client for the load driver | already a dev dependency, used by `bench/latency.py` and `bench/memory.py` [VERIFIED: `.venv` import] |
| Docker + `docker/build-push-action` | runner-provided | run the production image on the runner | `ci.yml` `image` job already builds it in about 1m18s [VERIFIED: `gh run view 40294590409` steps] |

### Supporting
| Tool | Purpose | When to use |
|------|---------|-------------|
| `bench/build_time.py`, `export_cost.py`, `memory.py`, `latency.py`, `corpus.py`, `nut_fine_caps.py`, `quiet.py` | the existing harness (L07: ported as harness, not numbers) | extend, do not rewrite; each needs the changes listed under Pitfalls |
| `bench/thread_spike/` (`worker.py`, `measure.py`, `verdict.py`, `runner.py`) | per-row child-process runner, JSONL records, `controls` block | reuse for the native `controls` run (`docs/ideas/2026-10-11-oper-02-resweep-runs-the-controls.md`) |
| `gh` CLI | read runs, jobs and PR files in `pr_land.py` | already authenticated on the dev host [VERIFIED: `gh auth status`] |

### Alternatives Considered
| Instead of | Could use | Tradeoff |
|------------|-----------|----------|
| GitHub runner (D-01, locked) | own linux/amd64 box | quieter, but not re-runnable by others; rejected in the discussion |
| macOS Docker, linux/amd64 under emulation | - | forbidden for bounds by D-01; this host has `DOCKER_DEFAULT_PLATFORM=linux/amd64` set, so `make check` and `make bench.memory` here are emulation figures [VERIFIED: `echo $DOCKER_DEFAULT_PLATFORM`] |
| `docker stats` sampling (`bench/memory.py` today) | cgroup `memory.peak` read once at the end | exact vs sampled; D-02 mandates the cgroup |

**Installation:** none. **Version verification:** the kernel pair was read from the venv (`cadquery 2.8.0`, `cadquery-ocp 7.9.3.1.1`); no registry lookup applies because nothing is installed.

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| (none) | - | - | - | - | - | This phase installs no external package; `gsd_run query package-legitimacy check` was not run because there is nothing to check. |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## The Current Bound Inventory

Every value below was read this session (Read tool, or `sed`/`grep -n` on the file) and is quoted verbatim. "Origin" says whether it is a spur figure, an interim guess or a screw measurement on macOS arm64. None is a linux/amd64 measurement.

| Knob | Where (file:line) | Verbatim value | Origin | Phase 7 action |
|------|-------------------|----------------|--------|----------------|
| Build timeout | `src/screw/app.py:165` | `int_env("SCREW_BUILD_TIMEOUT", 30),` | spur (worst 7.39 s × ~4) | replace with per-artifact timeouts (D-09) |
| Build workers | `src/screw/app.py:155` | `int_env("SCREW_BUILD_WORKERS", 2),` | spur L17 | load sweep 1, 2, 3 (D-03) |
| Queue depth | `src/screw/app.py:114` | `return int_env("SCREW_MAX_QUEUED_BUILDS", 2 * int_env("SCREW_BUILD_WORKERS", 2))` | spur | measure, feeds `Retry-After` |
| Bytes cache | `src/screw/app.py:100` | `_EXPORTS = _BlobCache(int_env("SCREW_EXPORT_CACHE_MB", 64) * 1024 * 1024)` | spur (sized on ~9 MB gear STLs) | re-sweep against threaded artifact sizes |
| gzip level | `src/screw/app.py:256` | `_GZIP_LEVEL = 1` | spur L19 (gear STL) | re-run `bench.export_cost` on threaded parts |
| gzip `minimum_size` | `src/screw/app.py:260` | `app.add_middleware(GZipMiddleware, minimum_size=1024, compresslevel=_GZIP_LEVEL)` | spur | measure; applies to JSON bodies, not the STL (the STL is gzipped by `_gzip`) |
| `Retry-After` | `src/screw/app.py:337`, `:552`, `:570` | `headers={"Retry-After": "5"},` (337 and 570) and `headers={"Retry-After": "5"}) from exc` (552) | spur | derive per artifact (D-11) |
| Solid cache | `src/screw/solid/__init__.py:278` | `_build_cached = lru_cache(maxsize=int_env("SCREW_SOLID_CACHE", 4))(_build_checked)` | spur | measure; per worker |
| Tessellation | `src/screw/solid/__init__.py:76` | `TESSELLATION: dict[str, tuple[float, float]] = {"preview": (0.08, 0.5), "fine": (0.01, 0.1)}` | fine preset set by the Phase 5 D-21 rule (mesh deviation); preview is spur's | keep unless the sweep shows a reason; any change before fitting |
| `_release_arenas` | `src/screw/solid/__init__.py:93-105` | `_MALLOC_TRIM(0)` after every `export()` (line 336) | spur (1578 → 360 MiB on gears) | measure the effect on amd64 threaded parts |
| `MAX_TURNS` | `src/screw/calc/thread.py:29` | `MAX_TURNS = 250` | L11 frontier (macOS), nothing above measured | re-measure as an outer wall (D-08) |
| `MIN_TAIL_MM` | `src/screw/calc/thread.py:37` | `MIN_TAIL_MM = 1e-3` | research probe, macOS | re-measure natively (D-08); tails ≤1e-8 mm SIGSEGV |
| Rod fine-STL caps | `src/screw/calc/thread.py:384` | `FINE_STL_ROWS: dict[tuple[float, float, bool], float] = {` (13 keys) | L11 grid vs the INTERIM 64 MiB budget | retire (D-08) |
| Nut fine-STL caps | `src/screw/calc/thread.py:442-443` | `NUT_FINE_STL_CLEARANCE = 5.0` and `NUT_FINE_STL_ROWS: ... = {` (30 keys) | L16, macOS | retire with the model (see Open Question 5) |
| Field ceiling | `src/screw/params.py:31` | `INTERIM_MAX_MM = 1e5` | Phase 1 cylinder, macOS | re-measure as an outer wall; applies to `d`, `length`, `s`, `k`, `thread_length` (bolt) and `s`, `m`, `clearance` (nut) |
| `SCREW_WORKERS` | `src/screw/cli.py:227`, `Dockerfile:41`, `compose.yaml:14` | `default=int_env("SCREW_WORKERS", 1)` / `SCREW_WORKERS=1` / `SCREW_WORKERS: "1"` | spur L17 | measure 1 vs 2 server processes |
| `mem_limit` | `compose.yaml:20` | `mem_limit: 4g` | spur L17 | `peak × workers + headroom`, under 16 GB (D-02) |
| tmpfs | `compose.yaml:26` | `- /tmp:size=256m` | spur | size from the largest admitted STL (Pitfall 3) |
| HEALTHCHECK | `Dockerfile:51` | `HEALTHCHECK --interval=30s --timeout=2s --start-period=30s --retries=3 \` | spur | measure `/api/health` p95 under the chosen load |
| UI debounce | `src/screw/static/app.js:585` | `debounce = setTimeout(update, 350);` | spur | relabel as a UI choice, not measured (D-discretion) |

Also in scope but not on the interim list: `BuildPool.__init__(self, workers: int, timeout: int)` stores one `timeout` (`pool.py:73-75`); `max_tasks_per_child` is deliberately absent (`pool.py:78-86`, "Not measured for screw; Phase 7 re-sweeps").

### Debt items this phase closes (resolve in the same commits)
`2026-10-05-interim-runtime-bounds.md`, `2026-10-14-nut-interim-bounds.md`, `2026-10-11-default-pitch-d100-length200-exceeds-both-interim-backstops.md` (its trigger is Phase 7), `2026-10-06-bench-memory-sampling-is-too-coarse-for-short-corpora.md`. Related, decide in-scope or re-file: `2026-10-11-root-radius-floor-is-not-the-kernel-boundary.md` (the real pitch boundary is a kernel outer wall, same family as `MIN_TAIL_MM`), `2026-10-10-spike-protocol-amendments-before-next-campaign.md` (WR-03 per-row load readings, IN-02 a 600 s pair deadline; its trigger is "before the next campaign" and Phase 7 is one), `2026-10-21-nut-lead-in-gate-refuses-a-valid-nut-at-huge-s.md`, `2026-10-14-m18-probe-one-entry-has-no-deadline-during-a-run.md`. Idea to fold in: `docs/ideas/2026-10-11-oper-02-resweep-runs-the-controls.md`.

## The Allowed Grid

Counts computed this session from `screw.tables.presets.catalogue()` and `nut_catalogue()` with exact `Fraction(repr(x))` quotients (the same exactness rule as `calc.thread._exact`).

| Set | Size | Source |
|-----|------|--------|
| Bolt presets | **294** rows: 186 ISO 4017 + 108 ISO 4014 | `catalogue()` [VERIFIED: run this session] |
| Nut presets | **14** rows (ISO 4032, no M7) | `nut_catalogue()` [VERIFIED: run this session] |
| Catalogue rows with an integer `length / pitch` | **201 of 294** | computed with exact fractions [VERIFIED: run this session] |
| Distinct standard lengths | 29: 4, 5, 6, 8, 10, 12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 180, 200 | computed [VERIFIED: run this session] |
| Largest turn count of any preset's `thread_length / pitch` | 80 | computed [VERIFIED: run this session] |
| L11 thread corpus (the "measured grid") | 7160 rows = 15 sizes × 2 hands × rod/void × **1790** length points (every integer-mm and integer-turn length up to `min(10 d, 200 mm)`) | `tests/test_grid.py` `ROWS = 7160`, `bench.thread_spike.maths.lengths` |
| Fine-STL-refused presets today | 62 (all ISO 4017) | `tests/test_presets.py:172-189` (`assert len(refused) == 62`) |

"Standard length" in OPER-01 is the catalogue lengths above; "including lengths where `L/P` is an integer" is why the sewn-segment boundary matters (segments are K = 3 turns, L11), and 201 catalogue rows hit it. The free (non-catalogue) space is far larger: `d` and `length` up to 1e5 mm, `pitch` has `gt=0` and no upper bound except the root-radius rule, and up to 250 turns [VERIFIED: `params.py:97-99`, `:134`, `calc/thread.py:29`]. The cost model governs that region.

**Sizing the full tier.** 1790 length points × 2 hands × 3 artifacts × 5 repetitions (D-04) is 53,700 artifact builds before the catalogue, the nut grid and the dense boundary sweep. The only GitHub-runner timing on record is the thread-builder grid (no meshing, no export): 5-7 s per row at 4 xdist workers, 29:03 wall for the slowest of 15 shards [CITED: `bench/RESULTS.md` "GitHub runner: run 38240380994"]. A meshed export is slower than a bare build, so the full tier will need sharding across runners and a decision on where 5 repetitions apply (Open Question 6). Do not size it from the macOS figures.

## Measurement Mechanics

### Where a linux/amd64 number can come from
- **GitHub Actions `ubuntu-latest`, public repo:** 4 vCPU, 16 GB RAM, 14 GB disk, x64; `ubuntu-latest` points to Ubuntu 24.04. A private repo would get 2 vCPU / 8 GB [CITED: docs.github.com/en/actions/reference/runners/github-hosted-runners]. `halfb00t/screw` is public [VERIFIED: `gh repo view` → `"visibility":"PUBLIC"`], and the recorded grid run printed 4 xdist workers on each shard (`bench/RESULTS.md`), consistent with 4 vCPU. D-02's "runner-sized 4 vCPU / 16 GB" therefore matches the public-repo runner. If the repo were ever made private the figures would not transfer.
- **This host cannot produce a bound.** Apple M5 Max, 18 CPUs, 64 GiB, arm64; OrbStack Docker with `DOCKER_DEFAULT_PLATFORM=linux/amd64` [VERIFIED: sysctl, `docker info`, env]. Whether OrbStack uses Rosetta or QEMU, the timings are not native. The 2026-10-11 ad-hoc control re-run was exactly this and L11 labels it "an emulation figure".
- **The runner is much slower than this host.** The pair verify cell took 167.50 s on ubuntu-latest and 42.55 s alone locally; another test took 300 s against 13.6 s [CITED: `docs/tech_debt/active/2026-10-20-ci-test-job-tripled-by-two-pair-tests.md`; the 20x gap is unexplained there, so do not extrapolate]. Expect the catalogue to cost several times more seconds than the macOS context run.

### Measure inside the production image, not only in a venv (ASSUMPTION A1, recommended)
D-01 says "natively on a runner" but not whether the build runs from the repo venv (as `grid.yml` does) or from the image. The shipped artefact is the Docker image (`python:3.12-slim-bookworm`, Debian 12 glibc), while the runner is Ubuntu 24.04 with a different glibc. Memory behaviour (glibc arenas, the `malloc_trim` that `_release_arenas` calls through `libc.so.6`) and the container cgroup that `mem_limit` limits only exist in the image. Recommendation: every figure that feeds `mem_limit`, workers, caches or timeouts is measured in the image on the runner; the required CI tier can use the same image (the `image` job already builds it in about 80 s). Flag to the owner as a confirm-by-default choice.

### Reading the peak: cgroup `memory.peak`, one container per measurement point
- `memory.peak` exists in cgroup v2 from kernel 5.19 and is the v2 counterpart of v1's `memory.max_usage_in_bytes` [CITED: kernel patch thread via search, lore/yhbt "memory.peak ... requires Linux kernel 5.19 or newer"]. Reset-by-write semantics differ between kernels, so do not rely on resetting: start a fresh container per point.
- Verified locally that a container sees it and a Python process can read it with no shell: `docker run --rm python:3.12-slim-bookworm python -c "print(open('/sys/fs/cgroup/memory.peak').read())"` printed `5640192` on cgroupfs type `cgroup2fs`, kernel `7.0.14-orbstack-00380-ga7e0a2dc9535` [VERIFIED: run this session; OrbStack, not a GitHub runner]. That the hosted runner (Ubuntu 24.04) exposes cgroup v2 `memory.peak` to containers is [ASSUMED] until the first runner run prints it; make the harness fail loudly (no number) if the file is missing or the filesystem is not `cgroup2fs`, and fall back to `memory.max_usage_in_bytes` only if present (D-02 names both).
- `memory.peak` counts page cache and tmpfs pages, not only RSS, so it is the number a `mem_limit` is judged against. A per-process `ru_maxrss` (already used by `bench/export_cost.py` and the thread-spike worker) is exact but smaller; use it only as a cross-check.
- The image runs as a non-root `nologin` user with Python present, so `docker exec <c> python -c ...` works with no shell (the debt item asks to check this first).

### Why the existing memory driver cannot answer D-03 as written
`bench/memory.py::_drive_corpus` sends the corpus **one request at a time** with a single `httpx.Client`, fine STL only, and `_sweep_one` samples `docker stats --no-stream`, at N = 1, 2, 4. With one request in flight the pool never has more than one busy worker, so peak memory at N = 2 or 3 does not include "every worker busy". The load sweep needs concurrent clients (at least workers + queue depth) over a fixed mix of admitted parts and all three artifacts, with the peak read from the cgroup once at the end. Changing the sweep set to 1, 2, 3 is also required (`for n in (1, 2, 4)` at the `sweep()` call).

### Runner heterogeneity and noise
GitHub mixes CPU generations (D-01), so record `lscpu`/`/proc/cpuinfo` model name, `nproc` and RAM on every run, and run the enforcement tier on the same class. Bounds come from the max over 5 repetitions (D-04) taken on at least two distinct runner instances; a single runner's max is one draw from the fleet. Read the 1-minute load average before every timing-bearing row (the open WR-03 amendment): `bench/quiet.py` fixes `decisive` once at block start. Do not run xdist next to a timing sweep; `Makefile` `PYTEST_WORKERS` defaults to the online CPU count clamped to 8, so a timing run must pass `-n 0` or use the harness's own runner.

### OCCT meshing is multi-threaded by default
`cadquery.Shape.exportStl(..., parallel: bool = True)` runs `BRepMesh_IncrementalMesh(..., parallel)` [VERIFIED: `inspect.getsource(cadquery.Shape.exportStl)` in the project venv, cadquery 2.8.0]. `_write_export` does not pass `parallel`, so each STL export may use every core. That makes the worker count and per-build speed interact on a 4-vCPU box: one build alone can use all four cores, and N busy workers contend. The D-03 sweep must therefore be run with the shipped meshing setting; changing `parallel` is a behaviour change to measure separately, not a free knob.

## Existing Refusal Machinery (reuse, do not rebuild)

| Layer | Mechanism | Where |
|-------|-----------|-------|
| Model-level 422 | `PydanticCustomError(type, msg, {"fields": [...]})` in `@model_validator(mode="after")`, e.g. `turn_cap`, `pitch_too_coarse`, `head_too_small`, `nut_too_thin` | `params.py:107-116`, `:165-188`, `:223-252` |
| Request-boundary 422 for explicit-vs-default conflicts | `refuse_explicit_conflict(kind)` dependency → `HTTPException(422, detail=[{"loc": ["query"], "type": conflict.type, "msg": ..., "ctx": {"fields": [...]}}])`, backed by `calc.explicit_conflict` | `app.py:200-231`, `calc/__init__.py` `_bolt_explicit_conflict` |
| Per-download refusal before cache, slot and pool | `download_refusal(p, fmt, quality) -> str | None`, dispatched by `isinstance` on `BoltParams` / `NutParams`; `_serve` raises `HTTPException(422, detail=[{"loc": ["query"], "type": "fine_stl_cap", "msg": refusal}])` as its first statement | `calc/__init__.py` `download_refusal`; `app.py:489-492` |
| Same rule on the CLI | `cmd_export` prints `error: {refusal}` and exits 2 before the kernel is imported | `cli.py` `cmd_export` |
| Same rule in the info document | `_downloads(p)` builds `Download(format, quality, refusal)` for the four `(fmt, quality)` pairs `("stl","fine"), ("stl","preview"), ("step","fine"), ("step","preview")` | `calc/__init__.py` `_DOWNLOADS`, `_downloads` |
| Cap-and-warn for a defaulted value | `derive(p)` returns `PartInfo.warnings`; e.g. the `head_chamfer` cap at `k / 2` (L19) | `calc/__init__.py` |

`download_refusal` currently returns `None` for everything except the fine STL (the preview STL and the STEP are never refused: L12, L13). The cost model extends this one function to judge preview STL, fine STL and STEP separately, so `_serve`, `cmd_export`, `/api/*/info` and the page stay in agreement for free (`tests/test_parity.py`, `tests/test_calc.py::..._document_agrees_with_the_shared_download_rule`). The refusal text must begin with the field names, because the CLI prints no `loc` for a model-level error (existing convention in `fine_stl_refusal`: "thread_length and length: ...").

Note on D-06's "a defaulted value that pushes a part over is capped and warned": which defaulted field can raise cost? `head_too_small` already turns a default `s` that is not larger than `d` into a 422, `thread_length` is already folded to `length`, `head_chamfer` is already capped at `k / 2`. The planner should enumerate the defaulted fields against the cost features before writing any cap code; if none can be the cause, every over-budget request is an explicit choice and therefore a 422 (A6).

## Worker Process Model and How the Timeout Works Today

- `BuildPool(workers, timeout)` makes `workers` single-worker `ProcessPoolExecutor`s (spawn context, `_warm` imports `screw.solid`) and routes by `hash(p) % self.workers` (affinity, no work stealing) [VERIFIED: `pool.py:70-93`]. `app.lifespan` builds it eagerly; `build_backend()` hard-fails rather than building inline.
- `export()` → `_run_with_timeout`: `loop.run_in_executor(...)` then `asyncio.wait_for(future, timeout=self.timeout)`. On `TimeoutError` it terminates the executor's OS processes (`executor._processes.values()` → `proc.terminate()`), calls `recreate_for(p, executor, "timeout")`, and raises `BuildTimeout`; the D-16 same-slot guard returns the timeout without touching a slot already replaced [VERIFIED: `pool.py:148-222`]. `app._serve` maps `BuildTimeout` to 503 `type: "timeout"` with `Retry-After: 5`, and `BrokenProcessPool` to 503 `pool_broken`.
- `build_export(p, fmt, quality)` = `solid.export(p, fmt, quality)`: build (through the per-worker `lru_cache` of 4 solids), then one export, then `malloc_trim`. A **cold request** is build + one export; a warm request (same params, solid still cached, same slot) is export only.
- `int_env` returns a positive int (`max(1, int(...))`) [VERIFIED: `src/screw/__init__.py`]. Per-artifact timeouts that are not whole seconds, or a derived `Retry-After`, need float handling; `pool.timeout` is also assigned directly in `tests/test_pool.py` (`pool.timeout = 0.2`, lines 163-171, 391-397, 459-493), so keep an attribute or keyword that tests can still inject.

**Per-artifact seam.** The artifact is `(fmt, quality)` and the pool already receives both in `export(p, fmt, quality)`. A lookup `timeout_for(fmt, quality)` inside `export()` passing `timeout=` to `_run_with_timeout` (defaulting to `self.timeout`) changes the signature minimally and leaves the injected-timeout tests valid. STEP ignores `quality` (`_write_export`), so the STEP timeout is one value for both qualities.

## Architecture Patterns

### System Architecture Diagram

```
                        request (API / CLI / page)
                                   |
                                   v
                 params validated once (Pydantic) --- 422 on field/model rules
                                   |   (INTERIM_MAX_MM, MAX_TURNS stay only as outer walls)
                                   v
            calc.download_refusal(p, fmt, quality)   <- NEW: cost model, kernel-free
              features: d, pitch, built length, hand, head, nut fields, preset
              admit iff predicted_cost * (1 + worst_under_prediction) <= artifact budget
                |                                   |
        refused: 422 naming fields          admitted
        (API) / exit 2 (CLI) /                      |
        downloads[].refusal (info)                  v
                                   exports cache (bytes) hit? -> serve
                                                    |
                                                    v
                              admission slot (BUILD_QUEUE, depth measured)
                                busy -> 503 busy + Retry-After(derived)
                                                    |
                                                    v
                         BuildPool: hash(p) % workers -> single-worker executor (spawn)
                                   deadline = per-artifact timeout (D-09)
                                                    |
                  worker: build (lru 4) -> check_solid -> tessellate/export -> malloc_trim
                                                    |
              returns bytes | BuildError(422) | timeout -> terminate+replace -> 503 + miss log
                                                    |
                                       gzip in slot (level measured) -> cache -> response
```

Measurement and enforcement run beside this path, not in it:

```
workflow_dispatch / weekly / PR(paths filter)
  -> runner (ubuntu-latest, record nproc, RAM, CPU model)
     -> docker build image -> per point: docker run (fresh cgroup) python -> build/export x5
        -> read /sys/fs/cgroup/memory.peak -> JSONL record -> bench/RESULTS.md entry
  -> fit cost model (offline) -> constants + Lxx citing the run id
  -> required tier (ci.yml): boundary set + fixed-seed sample inside timeouts
  -> pr_land.py: PR diff touches model/budgets/solid/tessellation -> full-tier run for head must be green
```

### Recommended Project Structure (additions only)
```
src/screw/calc/cost.py            # the cost model + budgets + per-artifact refusal text (no cadquery/logging)
src/screw/calc/__init__.py        # download_refusal delegates to cost.py; FINE_STL_ROWS call sites removed
src/screw/pool.py                 # per-artifact timeout; (maybe) queue-aware deadline
src/screw/app.py                  # derived Retry-After; cost-model-miss log call; lifespan reads constants
bench/oper_*.py                   # runner harness: point runner (image), load driver, fit script
.github/workflows/operability.yml # full recording tier (dispatch, weekly, paths-filtered PR); name avoids the word "grid" only where tests demand
.github/workflows/ci.yml          # + one required job (boundary set); required-jobs.txt in the same commit
scripts/pr_land.py                # + full-tier rule (diff paths -> require run for head)
docs/architecture/decision_log.md # L20.. (see below)
```

### Pattern 1: Pre-register the rule, then run (the repo's own method)
**What:** commit each knob's selection rule and its inputs before the run that applies them, then record the run id the Lxx cites. L11 did this (`02-SPIKE.md`, "rules written before any run"), the Phase 5 mesh-deviation and nut-fine-caps runs did (`bench/mesh_deviation.py`, `bench/nut_fine_caps.py`: "the rule, fixed before any row ran"), and spur's gzip rule ("adopt a higher level only if it shrinks output by >=10% AND costs <=1.5x the 10-concurrent wall time of the level below it") is the template for gzip; screw's own thresholds must be stated, not inherited as numbers.
**When to use:** gzip level, cache budget, solid cache, queue depth, worker pick, headroom factor. Avoids "tuned toward a pass" (L11, L37 wording).

### Pattern 2: Per-artifact budgets through one function
**What:** keep `download_refusal` as the single judge; give `cost.py` one pure function `predict(p, fmt, quality) -> Cost` and one `refusal(p, fmt, quality) -> str | None`. Constants (budgets, envelope factor, fit coefficients) live as module constants each with a comment citing the run id and the measurement that forced it (AGENTS.md comment rule).
**Example (shape, from the existing convention):**
```python
# Source: src/screw/calc/__init__.py download_refusal / calc/thread.py fine_stl_refusal (existing shape)
def download_refusal(p: FastenerParams, fmt: str, quality: str) -> str | None:
    if isinstance(p, BoltParams):
        return cost.bolt_refusal(p, fmt, quality)   # text begins with the field names
    if isinstance(p, NutParams):
        return cost.nut_refusal(p, fmt, quality)
    raise TypeError(f"no download rule for kind {p.kind!r}")
```

### Pattern 3: One container per measurement point, cgroup read at the end
```python
# Source: verified locally on OrbStack (cgroup2fs); runner behaviour is ASSUMED until the first run.
# Inside the container, after the build/export finished:
peak = int(open("/sys/fs/cgroup/memory.peak").read())
# Record None, never a plausible number, if the file is missing or the container hit its --memory cap
# (bench/memory.py::_is_capped is the precedent).
```
A probe must run under `docker run --memory=<cap>` with a wall deadline so an over-budget or non-terminating corner (the recorded `d=1e5, pitch=1, length=1` preview "did not finish in 120 s"; `d=100, L=200` needs 9143 MiB on macOS) is recorded as capped or killed instead of taking the 16 GB runner down.

### Pattern 4: `pr.land` full-tier rule computed from the diff, not from the workflow
`scripts/pr_land.py` keeps `WORKFLOW = "ci.yml"` (a test pins it: `tests/test_grid.py::test_the_grid_tier_is_not_a_required_job` asserts `WORKFLOW == "ci.yml"`). Add a second constant for the full-tier workflow file and a function that (1) lists the PR's changed paths from `gh` (e.g. `gh api repos/{owner}/{repo}/pulls/N/files --paginate` or `gh pr view --json files`), (2) matches them against a path list defined **in `pr_land.py`**, (3) if any match, requires a completed `success` run of the full workflow whose `head_sha` equals the PR head. The workflow's own `paths:` filter exists only to avoid wasting runs; a PR author controls the workflow file in their own PR, so the filter cannot be the authority. A test must assert the `pr_land` path list and the workflow's `paths:` list are equal (as `required-jobs.txt` is held equal to `ci.yml`).

### Anti-Patterns to Avoid
- **Setting a bound from a macOS run, or from qemu/Rosetta timings** (D-01).
- **Deriving mem_limit by multiplying a single-part peak by N** instead of a concurrent sweep (spur L17's own warning).
- **A cost model whose features cannot separate the axes.** On the L11 grid `d` and `pitch` are 15 collinear pairs, so a regression on them cannot separate the two. A crude `log(triangles) ~ log turns + log d + log pitch` fit over 3506 rod rows gave exponents 0.99 / 0.08 / 0.91 and a worst-case actual/predicted ratio of 0.61 to 1.59 [VERIFIED: computed this session from `bench/results/thread-spike/2026-10-08-a-grid.jsonl`, macOS, a fit sanity check only, not a model]. The sweep needs off-row `(d, pitch)` points (small `d` with tiny pitch, large `d` with coarse pitch) or the envelope factor will be wrong in exactly the region users can reach.
- **Moving a frozen default to make a part fit** (L02). Budgets refuse or warn; they never change a default.

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---------|-------------|-------------|-----|
| Peak memory | sampling `docker stats` or `ps` | cgroup `memory.peak` (D-02) | exact high-water mark; includes tmpfs and page cache |
| p95 | `sorted(x)[int(0.95*n)]` | `statistics.quantiles(x, n=20)[-1]` as `bench/latency.py::_p95` does, with its `MIN_SAMPLES = 20` refusal | off-by-one plausible numbers |
| Per-row isolation, deadlines, JSONL records | a new runner | `bench/thread_spike/runner.py` + `worker.py` (child process per row, `ru_maxrss`, deadline) | already tested in `tests/test_bench.py` |
| A second refusal path | new exception types or 422 shapes | `download_refusal` + existing `HTTPException(422, ...)` shape | parity across API, CLI, info and page is already tested |
| Exact turns | `length / pitch` in floats | `calc.thread._exact` / `turns_of` | 168 of 3000 float `k*P` products fail `(k*P)/P == k` (Pitfall 1 in `maths.py`) |
| Process termination | `executor.shutdown(cancel_futures=True)` | the existing terminate-then-`recreate_for` path | `cancel_futures` does not stop a running OCCT call (`pool.py:194-209`) |
| Gzip | custom compression | `gzip.compress(level)` as `_gzip` | level choice is the only knob |
| CPU/RAM facts | ad-hoc strings | extend `bench.machine_facts()` with the `/proc/cpuinfo` model name | D-01 requires CPU model; today it prints CPU count, arch, RAM only |

**Key insight:** the only genuinely new code is the cost model, the per-artifact timeout lookup, the runner harness and the `pr_land` rule. Everything else is measurement and editing constants with citations.

## Common Pitfalls

### Pitfall 1: The timeout clock counts time spent queued behind a same-slot build
**What goes wrong:** `asyncio.wait_for(future, timeout=self.timeout)` starts at submission. With hash affinity, up to `MAX_QUEUED_BUILDS` (2 × workers = 4 today) admitted requests can land on one single-worker executor; the 2nd-4th spend their timeout waiting. When the first overruns, the worker is terminated and the queued ones surface as `BrokenProcessPool` (503 `pool_broken`). spur recorded the effect: four of ten admitted requests, all four exceeded the timeout (spur L37).
**Why it happens:** the pool measures wall time from enqueue, not from the start of execution.
**How to avoid:** decide explicitly (Open Question 2). Either the timeout is measured and set end-to-end for the worst same-slot queue, or the pool computes a queue-aware deadline (own timeout plus the timeouts of requests ahead on that slot, tracked in the single-threaded event loop with no lock), or the worker reports its start. Whatever is chosen, the D-09 measurement must drive concurrency with parts that hash to distinct slots **and** a run with all parts on one slot, because "every worker busy" is not what random parts guarantee.
**Warning signs:** `build.failed` records with `BuildTimeout` whose `duration_ms` is the timeout exactly (spur's `30004`/`30003`) on parts that build alone in a fraction of it.

### Pitfall 2: The memory driver never has more than one build in flight
See "Why the existing memory driver cannot answer D-03". Result if reused: peak memory looks flat across N, `mem_limit` is under-sized, and an OOM kill shows up as a user-visible 503 `pool_broken`.

### Pitfall 3: tmpfs counts against the container and caps the STL it can hold
`_write_export` writes each export into a `tempfile.TemporaryDirectory` (default `/tmp`, which compose mounts as `size=256m` tmpfs) and reads it back. tmpfs pages are charged to the container's cgroup, so a large STL costs memory twice (file in tmpfs, then `read_bytes()`), and an export larger than the tmpfs fails to write. Recorded sizes: M20 x 200 fine STL 144,945,384 bytes (`04-RESEARCH`/`RESULTS.md` head-fuse probe) and 144,602,684 bytes in this session's context run; `d=100, L=200` fine STL 1,303,132,684 bytes (WR-05 debt item). The cost model's fine-STL byte budget and the tmpfs size must be chosen together (tmpfs ≥ largest admitted raw STL, and both inside `mem_limit`). The exact failure text of an over-full tmpfs through `exportStl` was not run here (A5); the existing `exportStl() returned False` → `BuildError` path covers a missing file but not necessarily a truncated one, and `_check_stl` (header count vs byte length) is the existing guard.

### Pitfall 4: Bytes cross the process boundary as copies
A built artifact is returned from the worker through the executor's result pipe (pickled, then unpickled in the parent), then optionally gzipped in a thread, and `_serve` caches the raw blob and the gzip blob as separate entries in a budget shared by both (`_BlobCache`; the comment above `_EXPORTS` accepts this). So the parent transiently holds several copies of one large artifact. This is the mechanism by which the kernel-free parent still has a size that scales with the artifact; it is [ASSUMED] from CPython's `ProcessPoolExecutor` design and must be confirmed by the cgroup sweep rather than computed. It is why the bytes-cache budget and `mem_limit` are not independent knobs.

### Pitfall 5: The page needs the preview to offer anything
`static/app.js::update()` fetches `info`, then `GET .../model.stl?quality=preview`; only after that succeeds does it call `setDownloads(q, info.downloads)`. If the preview STL is refused (D-06 allows that), `fail(await problems(res))` runs and no download link is set, so "the page offers whatever fits" is false until the loop is changed: on a preview refusal it must still render the info panel and call `setDownloads`. `setDownloads` already handles per-format refusals (it links the first non-refused entry per format and labels a fallback quality), so the change is in `update()` and the status text. Add a browser-level or JS-contract test for it; today's JS is exercised via the static bundle and parity tests only.

### Pitfall 6: Test and workflow tripwires that will fail on the obvious edit
- `tests/test_grid.py::test_the_grid_tier_is_not_a_required_job`: `assert "grid" not in ci` over the **whole text of `ci.yml`**, comments included. A new required job and its comments must not contain the word "grid".
- `tests/test_grid.py::test_the_grid_marker_is_registered_and_deselected_by_default` pins `"-m 'not grid and not pair'" in options["addopts"]` exactly; adding a deselected marker means updating that test in the same commit. The existing markers are described in `pyproject.toml:119-122`.
- `tests/test_pr_land.py` derives the effective job names from `ci.yml` and fails if `required-jobs.txt` disagrees (L08): change both in one commit. Job names with a matrix are reported `name (value)`.
- `tests/test_grid.py::test_the_grid_workflow_has_no_pull_request_or_push_trigger_and_reads_only` pins `grid.yml`; the full tier is a **new** workflow file, so `grid.yml` and its pins stay untouched. The new file needs its own pin test (triggers, `permissions: contents: read`, no `secrets.`).
- `tests/test_presets.py:172-189` pins 62 refused presets (and `FINE_STL_ROWS` by name); `tests/test_thread_maths.py` has 17 references to the caps/constants; `tests/test_mesh.py` compares the fine preset to the caps header; `tests/test_calc.py`, `tests/test_solid.py` and `tests/test_bench.py` (3 refs) also touch retired names. Count these as the retirement's blast radius.
- Coverage floor `fail_under = 96`: new `calc` and `pool` code lands with tests in the same change.
- `scripts/pr_land.py` and its tests were ported byte for byte from spur (L08); changing them is the "first fix that has to land in both repos" trigger for L07's extraction note. Record that in the new Lxx rather than let it pass silently.

### Pitfall 7: A probe at a corner can take the runner down
Unbounded probes (`d` up to 1e5, 250 turns, fine tessellation) can exceed 16 GB or never finish. Every probe runs in a container with a memory cap and a hard wall deadline, records `capped` / `killed` with no number (the `bench.memory._is_capped` precedent), and the job sets `timeout-minutes` below the 6-hour hosted-job ceiling [A7: the 6 h figure is from memory, not fetched]. The recorded corners are macOS single runs: `d=100, pitch=5, L=1250` fine STL 152.6 s and 7875 MiB; `d=100, L=200` fine STL 53.3 s and 9143 MiB; `d=1e5, pitch=1, L=1` preview did not finish in 120 s (`2026-10-05-interim-runtime-bounds.md`, `2026-10-11-default-pitch-...md`). They show where to place deadlines, not what the limits are.

### Pitfall 8: Cold versus warm builds decide which timeout is honest
The solid cache (4 entries, per worker) means a second artifact of the same part can skip the build. A timeout set from warm exports is too short for the first request of a part, after a worker replacement, or after eviction. Set each artifact's timeout from the cold path (build + that export) and record build and export separately, as `bench/build_time.py::Timing` already does (`worst_request = build + max(stl, step)`, which for per-artifact timeouts should be `build + that artifact's export`).

### Pitfall 9: Decisive-looking records from a noisy block
`Campaign.decisive` is fixed at block start (WR-03). On a shared hosted runner a long block can go noisy mid-run. Read load between rows and downgrade `decisive`, as the open amendment proposes, or record the reading per row; and keep `PAIR_TIMEOUT_S` (IN-02) in mind if the pair tier is re-run.

## Code Examples

### The refusal returned to API, CLI and info document
```python
# Source: src/screw/app.py:489-492 (existing; the cost model changes what download_refusal returns, not this site)
refusal = download_refusal(params, fmt, quality)
if refusal is not None:
    raise HTTPException(422, detail=[{"loc": ["query"], "type": "fine_stl_cap",
                                      "msg": refusal}])
```
The `type` string `fine_stl_cap` is part of the published error shape (the page and tests read it); a cost-model type name is a deliberate change to list in the Lxx (pattern: L19 lists the 422 type and `ctx.fields` as costly to change).

### Where a 503 is produced (three sites, one literal)
```python
# Source: src/screw/app.py:337, 552, 570 (verbatim values)
headers={"Retry-After": "5"},
```
Derive one helper from the per-artifact constants (artifact median build × queue depth, rounded up to whole seconds, D-11) and use it at all three sites; a test should assert none of the three keeps the literal.

### Reading the container's peak (see Pattern 3)

## State of the Art

| Old approach | Current approach | Impact |
|--------------|------------------|--------|
| `docker stats` polling for peak memory | cgroup v2 `memory.peak` (kernel ≥ 5.19) | exact, not sampled |
| One global build timeout | per-artifact timeout, with queue wait made explicit | preview, fine STL and STEP differ by orders of magnitude (macOS context: STEP 0.09 s vs fine STL 3.94 s at M20 x 200) |
| Per-row measured fine-STL caps (13 + 30 keys, run keys not ISO rows) | a fitted, envelope-guarded cost model over `(d, pitch, length, hand, head, nut fields, preset)` | covers off-row parts; costs some legal parts being refused |

**Deprecated within this phase:** `FINE_STL_ROWS`, `NUT_FINE_STL_ROWS`, `NUT_FINE_STL_CLEARANCE`, `fine_stl_refusal`, `nut_fine_stl_refusal`, `SCREW_BUILD_TIMEOUT`, the literal `Retry-After: 5`. L12/L13/L16 text about those caps becomes history; the new Lxx supersedes them by id.

## Decision Log Entries the Phase Must Produce

The log ends at L19 [VERIFIED: `grep '^## L'`], so the next ids are L20 onward. CONTEXT already requires: a measurement-host / worker-pick / memory entry (D-01 to D-04), the cost-model and budget entry that supersedes the L12/L13/L16 cap lists (D-05 to D-08), the timeout and `Retry-After` entry with the ×2 factor and the run (D-09 to D-11), and the CI-tier plus `pr.land` entry (D-12, D-13, "changes how L08 gates merges"). Each cites run ids in `bench/RESULTS.md`, states reversibility, and keeps the house form (Date, who decided, Reason, Reversibility). One entry per decision keeps "supersedes Lxx" precise; the planner should decide whether the gzip / cache / solid-cache / healthcheck / tmpfs set is its own entry or part of the first.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Figures that feed `mem_limit`, workers, caches and timeouts should be measured in the production image on the runner, not in a venv. D-01 says "natively on a runner" but not which. | Measurement Mechanics | If the owner wants venv-only (as `grid.yml`), glibc/arena and cgroup effects are not measured and `mem_limit` is unsupported. |
| A2 | GitHub's `ubuntu-latest` runner exposes cgroup v2 `memory.peak` to containers (kernel ≥ 5.19, Ubuntu 24.04). Verified only on OrbStack, not on a runner. | Measurement Mechanics | The harness must fall back to `memory.max_usage_in_bytes` or refuse; the first runner run settles it. |
| A3 | The public-repo runner stays 4 vCPU / 16 GB and the fleet's CPU spread is bounded enough that 5 reps on ≥ 2 runner instances give a usable max. | Measurement Mechanics | Bounds could be too tight or too loose for a later, slower runner; CI would then fail (that is the D-07 narrowing path). |
| A4 | A partial export into a full tmpfs fails visibly (`exportStl` returns False or `_check_stl` rejects it) rather than serving a truncated file. | Pitfall 3 | If not, a truncated artifact could pass; the budget design must make the tmpfs always larger than any admitted raw STL. |
| A5 | The parent holds several copies of one large artifact (result pipe, gzip, two cache entries). | Pitfall 4 | If fewer, `mem_limit` headroom is looser; the cgroup sweep measures it either way. |
| A6 | No defaulted field can raise a part's cost over budget by itself, so every over-budget request is an explicit choice and a 422. | Existing Refusal Machinery | If one can, D-06 needs a cap-and-warn path for it. |
| A7 | A hosted-runner job is limited to 6 hours. | Pitfall 7 | A longer shard would be cancelled; size shards from the first measured run. |
| A8 | Path-filtered `pull_request` runs report the PR head sha as the run's `head_sha` in the runs API, as `ci.yml` PR runs already do for `pr.land`. | Pattern 4 | `pr_land` would not find the full-tier run; test against a recorded `gh api` fixture as `tests/test_pr_land.py` does. |
| A9 | Per-artifact budgets are a bytes/triangle budget for STL (client and cache limits) and a seconds/memory budget for STEP, with no single time ceiling that fits all three. | Open Question 1 | The owner may prefer one user-facing latency ceiling; the table in Open Question 1 supports either. |

## Open Questions

1. **What is the budget?** (blocks D-05, D-09, D-03; needs an owner ruling)
   - What we know: D-05 refuses a part whose cost exceeds "the measured budget"; D-09 sets each timeout from the worst admitted build; D-03 picks workers by memory that fits D-02. Memory has a ceiling by construction (under 16 GB, split across workers). Time, bytes and triangles have none: CONTEXT does not say how slow a cold build the product tolerates, nor how large a preview STL the page should load (the browser parses it with three.js; M20 x 200 preview is 22,320,784 bytes and the d=100, L=200 preview 256,952,984 bytes per the recorded probes), nor whether every catalogue row must keep its fine STL (62 ISO 4017 rows are refused today).
   - What is unclear: the circularity budget → admitted set → worst build → timeout → worker count (memory per worker depends on N, N is picked from admitted parts).
   - Recommendation: do an exploration sweep first, then put 2-3 candidate budgets to the owner as a table (rows kept / refused among the 294 + 14 catalogue rows and the free space, predicted worst build and bytes). Suggested default stance to offer: all catalogue rows admitted for preview and STEP; the fine-STL byte budget derived from `min(tmpfs, cache-feasible, mem_limit headroom)`; a per-worker memory allowance fixed up front at `(16 GB − headroom) / 3` so the worker pick can only move down. Then confirm with the workers sweep and iterate once if needed.

2. **How should the timeout treat same-slot queue wait?** (Pitfall 1; needs an owner ruling because it changes D-09's meaning)
   - Options: (a) keep the clock as is and measure/set each timeout for the worst same-slot queue (timeouts become roughly queue depth × worst build × 2, long and loose); (b) queue-aware deadline in `pool.py` (parent tracks requests ahead per slot; no worker change); (c) the worker reports its start so the clock runs from execution (new IPC, largest change).
   - Recommendation: (b), with the Lxx stating the formula; it keeps `BuildPool`'s public shape, needs no IPC, and makes "worst build × 2" true for the build itself. This is also a second divergence from spur's `pool.py` (after D-16).

3. **Required tier and full tier: image or venv?** (A1) Recommendation: image for both; the required job reuses the `image` job's build. Ask the owner to confirm by default.

4. **Do timeouts keep an environment override?** `SCREW_BUILD_TIMEOUT` is an `int_env` knob today and CODING_VALUES says "Limits live in code with an env var and a check". Per-artifact values suggest one multiplier env or none. Recommendation: no override for the three measured values (an override defeats "cites the run that set it"); keep none and let a deployer on slower hardware re-sweep. Needs a yes/no.

5. **Nut scope.** CONTEXT names `FINE_STL_ROWS`; the nut's `NUT_FINE_STL_ROWS` (30 keys, measured at `s` 1e5 and clearance 5.0, L16) and its refusal for clearance above 5.0 are the same kind of per-row cap and `2026-10-14-nut-interim-bounds.md` is in the phase's scope. Recommendation: the cost model covers the nut (features `s`, `m`, `clearance`, `d`, `pitch`, hand) and retires both cap tables and `NUT_FINE_STL_CLEARANCE`; L16 is superseded by id. Confirm.

6. **Size of the full tier and where D-04's 5 repetitions apply.** At 5 reps everywhere the 1790-point corpus alone is over 50,000 artifact builds (arithmetic above). Options: 5 reps on the boundary sweep and on the worst point per artifact (where a bound is set from the max), 1 pass on bulk catalogue rows with any row within a margin of its timeout re-run at 5. The planner should size from the exploration run's measured seconds per row and shard accordingly; this is a plan decision unless it weakens D-04, in which case it is the owner's.

7. **Kernel outer walls.** `MAX_TURNS` (250), `INTERIM_MAX_MM` (1e5) and `MIN_TAIL_MM` are to be "re-measured, cited" as kernel limits (D-08). The measurement is a walk to failure under a memory cap and a deadline, per size, both hands, rod and void. Is the pitch boundary (`root-radius-floor` debt, kernel fails near root radius 3e-5 mm) in or out? Recommendation: in, it is the same kind of wall and the debt item says Phase 7 is where it belongs; confirm.

8. **`SCREW_WORKERS` (server process count).** Each uvicorn process owns its own pool, queue and caches (`app.py` comments on the single-loop assumption). Recommendation: measure 1 vs 2 only with the total builder count held equal, and report `/api/health` p95 plus memory; keep 1 unless the load sweep shows the event loop or gzip is the bottleneck. This stays in discretion; flagged because the "one core stays for uvicorn and gzip" rule in D-03 presupposes 1.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 + project venv | all tests and harness | ✓ | 3.12.15, cadquery 2.8.0, cadquery-ocp 7.9.3.1.1 | - |
| Docker (OrbStack) | local `make check`, image build, container probes | ✓ | 29.8.2 | runner Docker for real figures |
| Docker default platform | - | linux/amd64 (emulated here) | `DOCKER_DEFAULT_PLATFORM=linux/amd64` | local runs are correctness only, never bounds |
| `gh` CLI, authenticated | `pr_land.py`, workflow dispatch and run reads | ✓ | logged in as halfb00t | - |
| Node | `make vendor-check` (success criterion 4) | ✓ | v26.11.0 (CI uses 22) | CI's `vendor-bundle` job |
| GitHub-hosted `ubuntu-latest` runner | every bound (D-01) | ✓ (public repo) | 4 vCPU / 16 GB, Ubuntu 24.04 [CITED] | none; macOS is context only |
| cgroup v2 `memory.peak` on the runner | D-02 | not yet confirmed | - | `memory.max_usage_in_bytes`; otherwise refuse to report |
| Native linux/amd64 host with the repo | the controls re-run | ✗ locally | - | the runner |

**Missing with no fallback:** none blocking planning. Execution depends on dispatching workflows on GitHub; nothing here can substitute for it.
**Missing with fallback:** local timing (use the runner); cgroup file on the runner (A2).

## Validation Architecture

`workflow.nyquist_validation` is `true` in `.planning/config.json` [VERIFIED: read this session], so this section applies.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.x with xdist and coverage (`pyproject.toml`), mypy `--strict`, ruff, import-linter |
| Config file | `pyproject.toml` (`addopts = "--strict-markers --strict-config -m 'not grid and not pair'"`, `fail_under = 96`) |
| Quick run command | `make test PYTEST_ARGS="tests/test_<file>.py -q -n0 --no-cov"` |
| Full suite command | `make verify` (and `make check` for success criterion 4; needs Docker) |
| Slow tiers | `make grid`, `make pair` (existing); the Phase 7 tiers are new markers outside `make verify`, run by workflow |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| OPER-01 | each artifact has a timeout constant whose comment/entry cites a run id; `export()` passes the per-artifact value; no `SCREW_BUILD_TIMEOUT` literal left | unit (`pool`, constants) | `pytest tests/test_pool.py -q -n0 --no-cov` | ✅ extend; new cases ❌ Wave 0 |
| OPER-01 | an overrunning build is terminated, slot replaced, nothing cached, no partial file, 503 + derived `Retry-After`, a cost-model-miss record | contract (`TestClient`, injected sleeper) | `pytest tests/test_pool.py tests/test_api.py -q -n0 --no-cov` | ✅ extend |
| OPER-01 | queue-aware deadline: a request behind a same-slot build keeps its own full timeout (if Open Question 2 = b) | unit (pool, injected timeouts as at `tests/test_pool.py:459-493`) | `pytest tests/test_pool.py -q -n0 --no-cov` | ❌ Wave 0 |
| OPER-01 | full-grid timings recorded on the runner: every catalogue row, integer `L/P` rows, nut rows | slow tier, runner | workflow dispatch (new); `make operability` or similar target | ❌ Wave 0 |
| OPER-02 | no `INTERIM` label or spur figure remains in `src/`, `Dockerfile`, `compose.yaml`, `app.js` (debounce relabelled) | static scan test | `pytest tests/test_<new>.py -q -n0 --no-cov` (grep-style, like `make no-fake-done`) | ❌ Wave 0 |
| OPER-02 | each constant (gzip level, cache MB, workers, solid cache, queue, `mem_limit`, tmpfs) equals the value in its decision entry / RESULTS record | consistency test (reads the log and constants) | same | ❌ Wave 0 |
| OPER-02 | cgroup peak reader: refuses a missing file / non-`cgroup2fs`, flags a capped row, harness predicates (p95 over too few samples, empty sweep) | unit on synthetic inputs (`tests/test_bench.py` style) | `pytest tests/test_bench.py -q -n0 --no-cov` | ✅ extend |
| OPER-02 | native amd64 sweep + load sweep 1/2/3 recorded with CPU model, nproc, RAM | runner tier | workflow dispatch | ❌ Wave 0 |
| OPER-03 | cost model: kernel-free (import contracts), monotone sanity, envelope factor applied, golden values at the measured points | unit (`calc`) | `pytest tests/test_cost.py -q -n0 --no-cov`; `make lint-imports` | ❌ Wave 0 |
| OPER-03 | per-artifact refusal parity: API 422 = CLI exit 2 = `downloads[].refusal`, same sentence, naming the fields | parity / contract | `pytest tests/test_parity.py tests/test_api.py tests/test_cli.py -q -n0 --no-cov` | ✅ extend |
| OPER-03 | the preset refused count moves to the new figure; every catalogue row's document agrees with the shared rule | unit | `pytest tests/test_presets.py -q -n0 --no-cov` | ✅ edit |
| OPER-03 | an explicit over-budget request is a 422, never a trim; a defaulted one is capped and warned (if any exists, A6) | unit + contract | as above | ❌ Wave 0 |
| OPER-03 | the page offers what fits when the preview is refused | JS contract / static test | whichever harness covers `app.js` (none exists for the update loop today) | ❌ Wave 0 |
| OPER-03 | required boundary tier builds inside the timeouts; a miss fails the job (CI) | CI job | `ci.yml` job (new); `required-jobs.txt` + `tests/test_pr_land.py` agreement | ❌ Wave 0 |
| OPER-03 | `pr_land` refuses a PR touching the model/budgets/solid/tessellation when the full-tier run for its head is red, missing or for another sha; allows when the diff misses those paths | unit with recorded `gh` fixtures | `pytest tests/test_pr_land.py -q -n0 --no-cov` | ✅ extend |
| OPER-03 | full-tier workflow keeps T-3-14: `permissions: contents: read`, no `secrets.`, no `pull_request_target`; its `paths:` list equals `pr_land`'s | text-pin test (pattern of `tests/test_grid.py`) | `pytest tests/test_<new>.py -q -n0 --no-cov` | ❌ Wave 0 |
| SC4 | builds still in worker processes off the loop; `make check` passes | existing tests + `make check` | `make verify`, `make check` | ✅ |

### Sampling Rate
- **Per task commit:** the targeted `make test PYTEST_ARGS="<files> -q -n0 --no-cov"` line for the files touched, plus `make lint typecheck lint-imports` for `calc`/`pool`/`app` edits.
- **Per wave merge:** `make verify`.
- **Phase gate:** `make verify` green, `make check` green, one successful dispatch of the full-tier workflow on the head, and the required-tier job green in `ci.yml`, before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `tests/test_cost.py` - the cost model, envelope, refusals, golden points (OPER-03)
- [ ] a runner-harness module and its synthetic-record tests in `tests/test_bench.py` style (cgroup reader, capped rows, p95 sample floor) (OPER-02)
- [ ] pin tests for the new workflow (triggers, permissions, `paths:` equals the `pr_land` list) (OPER-03)
- [ ] consistency test: constants vs decision-log entries vs `bench/RESULTS.md` run ids (OPER-01/02)
- [ ] `tests/test_pr_land.py` recorded `gh` fixtures for the full-tier rule, including a run whose `head_sha` is a different commit (OPER-03)
- [ ] a test for the page's refused-preview path (OPER-03)
- [ ] update the pinned strings noted in Pitfall 6 (`addopts`, the `"grid" not in ci` rule is a constraint on wording, not an edit)
- [ ] a Makefile target for the new tier(s), listed by `make` (the project rule: reuse `make`, not ad-hoc shell)

## Security Domain

`security_enforcement` is enabled (absent or true) and `security_asvs_level` is 1.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | the app has none by design (compose binds `127.0.0.1`) |
| V3 Session Management | no | no sessions |
| V4 Access Control | no | no accounts |
| V5 Input Validation | **yes** | Pydantic field bounds and model validators (single validation point), the cost-model 422 before any build; no free-form input reaches the kernel |
| V6 Cryptography | no | none used |
| V11/V13 Business logic / API resource consumption (denial of service) | **yes** | admission queue + 503, per-artifact timeout with worker termination, cost model refusing before the pool, `mem_limit`, tmpfs bound |
| CI / supply chain (workflow permissions) | **yes** | `permissions: contents: read`, no secrets in the recording workflow, no `pull_request_target`, `pull_request` only |

### Known Threat Patterns
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| One unauthenticated GET holds a worker for the full timeout and drives the container toward OOM (WR-05 debt: `d=100, L=200`, 53.3 s, 9143 MiB on macOS) | Denial of service | cost model refuses before cache/slot/pool; per-artifact timeout; `mem_limit` from a measured peak; this is the debt item's stated "paid-API drain" nearest blocker rubric |
| Same-slot request pile-up multiplying timeouts and killing neighbours | DoS | queue-aware deadline or explicit end-to-end timeout (Pitfall 1); small bounded queue |
| Cost-model under-prediction admits an over-budget part | DoS | conservative envelope (D-07), the 503 backstop plus a miss log, CI boundary set failing on a miss |
| Fork PR running the new `pull_request` workflow | Elevation of privilege / tampering | for a fork, "the `GITHUB_TOKEN` has read-only permissions in pull requests from forked repositories" and secrets are not passed; a maintainer may need to approve a first-time contributor's run [CITED: docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows]. `ci.yml` already runs `pull_request` with untrusted code and no `permissions:` block, so the new workflow with `permissions: contents: read` and no `secrets.` is no weaker. T-3-14's guarantee (no untrusted code with a privileged token) holds without a same-repo-only condition; do not use `pull_request_target`. State this reasoning and pin it with a test |
| A PR editing the workflow's `paths:` filter to skip the full tier | Tampering | the authority is `pr_land.py`'s own path list computed from the PR's changed files, held equal to the workflow list by a test (Pattern 4) |
| Resource-exhausting probe on the sweep runner | DoS (own CI) | container `--memory` cap, wall deadline, job `timeout-minutes` |
| Over-long path or unexpected characters in downloaded names | Tampering | unchanged: `slug()` yields only letters, digits and `_.+-` (T-01-06) |

## Sources

### Primary (HIGH confidence)
- Repository files read this session: `07-CONTEXT.md`, `07-DISCUSSION-LOG.md`, `REQUIREMENTS.md`, `STATE.md`, `docs/architecture/decision_log.md` (L01-L13 and L19 read in full; headers for L14-L18 listed), `docs/CODING_VALUES.md` (Code values, Testing, Tech debt, Dependencies, Project-specific), `src/screw/app.py`, `pool.py`, `params.py`, `solid/__init__.py`, `calc/thread.py` (caps, nut caps, refusals), `calc/__init__.py` (`download_refusal`, `_downloads`, `explicit_conflict`), `cli.py`, `build_errors.py`, `tables/presets.py`, `static/app.js` (update loop, `setDownloads`), `Dockerfile`, `compose.yaml`, `Makefile`, `.github/workflows/{ci,grid,pair}.yml`, `required-jobs.txt`, `scripts/pr_land.py`, `tests/test_grid.py`, `tests/test_presets.py:172-189`, `bench/{README.md,build_time.py,corpus.py,memory.py,latency.py,export_cost.py,quiet.py,__init__.py}`, `bench/RESULTS.md` (grid tier and the GitHub run), `bench/results/thread-spike/2026-10-08-a-grid.jsonl`, the debt items and the idea file listed under "Debt items", `pyproject.toml` (contracts, markers, addopts, coverage).
- Commands run this session: `make`-adjacent `bench.build_time` on three parts (macOS context), a catalogue/nut/integer-`L/P` count, `inspect.getsource(cadquery.Shape.exportStl)`, `docker run ... memory.peak`, `gh repo view`, `gh run view` job timings, `gh auth status`.
- spur (`../spur/docs/architecture/decision_log.md` L17, L37) for how spur measured memory and recorded a timeout under contention.

### Secondary (MEDIUM confidence)
- https://docs.github.com/en/actions/reference/runners/github-hosted-runners - public-repo `ubuntu-latest` is 4 vCPU / 16 GB / 14 GB, private 2 vCPU / 8 GB, points to Ubuntu 24.04.
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows - fork PR token and secrets behaviour; `paths` filter on `pull_request`.
- cgroup v2 `memory.peak` (kernel ≥ 5.19; v1 counterpart `memory.max_usage_in_bytes`; write-to-reset): kernel patch discussions found by web search (lore.kernel.org / yhbt.net mirror, "memory.peak ... requires Linux kernel 5.19 or newer").

### Tertiary (LOW confidence - flagged in the Assumptions Log)
- GitHub runner cgroup layout and kernel version (A2), the 6-hour job ceiling (A7), partial-write behaviour on a full tmpfs (A4), pipe-copy memory shape (A5).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - nothing new; versions read from the venv.
- Architecture (where each knob lives, refusal path, pool/timeout mechanics): HIGH - read in source this session.
- Measurement mechanics on the runner: MEDIUM - GitHub spec and cgroup semantics cited; the runner's cgroup exposure is unverified until the first run.
- Cost model form: LOW-MEDIUM by design - the existing data cannot separate `d` from `pitch`; the form is the sweep's output, not this document's.
- Pitfalls: HIGH for 1, 2, 5, 6 (read in code or tests); MEDIUM for 3, 4, 7 (mechanism reasoned, not run).

**Research date:** 2026-10-26
**Valid until:** 2026-11-25 (30 days; the runner image and the pinned kernel pair are the fast-moving parts - re-check `ubuntu-latest` mapping and the cadquery pin before the first dispatch)
