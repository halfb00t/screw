# Phase 7: Operability Re-sweep - Context

**Gathered:** 2026-10-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace every INTERIM runtime bound (the 16 knobs in
`docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md`, and the nut's in
`2026-10-14-nut-interim-bounds.md`) with a value measured on threaded parts on linux/amd64 and
cited in a decision entry. Bound the request space so that every configuration a user may ask for
builds inside its measured timeout; anything outside it is capped and warned, or refused with a
`422` naming the fields (L02), never silently shortened. A CI job proves it. Builds stay in worker
processes off the event loop, and `make check` passes (OPER-01, OPER-02, OPER-03).

The sweep measures the final part: the chamfered head (L19), the 0.15 mm nut clearance (L17) and
the printability warnings (L18). It adds no new part features.

</domain>

<decisions>
## Implementation Decisions

### Measurement host and container size
- **D-01:** Every runtime figure is measured natively on a GitHub Actions `ubuntu-latest` runner
  (linux/amd64), started by `workflow_dispatch` so anyone can re-run it. Each run records the
  runner's `nproc`, RAM and CPU model (`/proc/cpuinfo` model name), because GitHub mixes CPU
  generations. CI enforces the bounds on the same host class. macOS arm64 figures are context and
  never a bound.
- **D-02:** The target container is runner-sized, 4 vCPU and 16 GB. `mem_limit` = the measured
  peak per worker × the chosen worker count + headroom, and it must stay under 16 GB. Peak memory
  is read from the cgroup (`memory.peak`, or `memory.max_usage_in_bytes` on cgroup v1), not from
  coarse RSS sampling (`docs/tech_debt/active/2026-10-06-bench-memory-sampling-is-too-coarse-for-short-corpora.md`).
  — **Reversibility:** reversible — a constant in `compose.yaml` and an Lxx; a smaller deploy box
  later means a new sweep and a superseding entry.
- **D-03:** `SCREW_BUILD_WORKERS` is chosen by a load sweep at 1, 2 and 3 workers. The pick is the
  count with the best p95 latency whose peak memory fits D-02, and one core stays for uvicorn and
  gzip. The pick and its run go into a new Lxx. Carrying 2 over unmeasured is not allowed (OPER-02).
- **D-04:** Every measurement point takes 5 repetitions and records the median and the max. Bounds
  are set from the max.

### Bounding the allowed space
- **D-05:** The allowed space is bounded by a measured, kernel-free cost model in `calc`. It
  predicts each artifact's cost (triangles, or bytes, plus build seconds and peak memory as the
  sweep shows they track) from d, pitch, length, hand, the head and nut fields, and the
  tessellation preset. It is fitted to the sweep and validated against it. A request whose
  admitted cost exceeds the measured budget is refused before the cache, the admission slot and
  the pool, like today's fine-STL 422. The model obeys the calc import boundary (no `cadquery`).
  — **Reversibility:** costly — the model decides refusals on every front end, and the pinned
  refused-preset counts and the page's offered artifacts move with it.
- **D-06:** Refusal is per artifact. The info document always works. The preview STL, the fine STL
  and STEP are each judged against their own measured budget and refused with a `422` naming the
  fields. The page offers whatever fits, as with today's `Download STL (preview)`. A defaulted
  value that pushes a part over is capped and warned. An explicit request over budget is a `422`,
  never a quiet trim (L02).
- **D-07:** The model is a conservative envelope. A part is admitted only if its prediction ×
  (1 + the worst under-prediction observed on the sweep) fits the budget. The factor and the run it
  came from are cited in the Lxx. Some legal parts are refused, and no over-budget part is
  admitted. An under-prediction found by CI fails the job, and the envelope narrows in a
  superseding entry.
- **D-08:** The cost model replaces `FINE_STL_ROWS`, which is retired. `MAX_TURNS` and the
  `INTERIM_MAX_MM` (1e5 mm) field ceiling stay only as re-measured outer walls: the kernel's own
  limits, like `MIN_TAIL_MM`'s SIGSEGV boundary, each cited on linux/amd64. They are never the
  budget. `MIN_TAIL_MM` is re-measured the same way. The pinned refused-preset count in
  `tests/test_presets.py` moves to the new figure.

### Timeout policy
- **D-09:** There is one timeout per artifact: preview STL, fine STL and STEP. Each equals that
  artifact's worst measured build among admitted parts × 2, measured with every worker busy on
  admitted parts at the D-03 worker count. The ×2 factor is written in the Lxx.
  `SCREW_BUILD_TIMEOUT` (30 s, INTERIM) is replaced.
- **D-10:** An admitted part that still hits its timeout gets today's `503` with `Retry-After`. The
  worker slot is recycled, nothing is cached, and no partial file is served. The server logs the
  part's parameters as a cost-model miss. The timeout is the backstop behind the D-05 model, not the
  bound.
- **D-11:** `Retry-After` is derived from the sweep: the artifact's median build × queue depth,
  rounded up to whole seconds. It replaces spur's 5 s.

### Full-grid CI cadence
- **D-12:** There are two tiers.
  - **Required:** a job in `ci.yml` (so in `required-jobs.txt` under L08) builds a small boundary
    set: the admitted points nearest each artifact's budget edge, plus a fixed-seed random sample of
    admitted points, inside the D-09 timeouts. Target about 10 minutes.
  - **Full, recording:** a separate workflow, modelled on `.github/workflows/grid.yml`, builds every
    catalogue row and standard length (including integer `L/P` lengths), the nut grid and a dense
    boundary sweep. It runs weekly and on dispatch, and it records to `bench/RESULTS.md`. A miss in
    either tier fails the tier.
- **D-13:** The full tier also runs on a PR whose diff touches the cost model, the budgets, the
  timeouts, the tessellation constants or `src/screw/solid/`, through a paths filter.
  `make pr.land` (`scripts/pr_land.py`, today it reads `ci.yml` only) refuses that PR while the full
  tier is red or missing for its head. This changes how L08 gates merges, so the planner records it
  as a new Lxx.
  — **Reversibility:** reversible — one rule in `scripts/pr_land.py` and one workflow trigger.
  - **Constraint to resolve in research:** `grid.yml` has no `pull_request` trigger on purpose
    (T-3-14: no untrusted code runs with the token). A same-repo PR trigger with
    `permissions: contents: read` has to keep that guarantee, and the planner shows that it does.

### Rulings after research (2026-10-26, owner, at plan-phase)
Answers to the open questions in `07-RESEARCH.md`.
- **D-14 (research Q2):** The timeout clock becomes a queue-aware deadline in `pool.py`. The parent
  tracks the requests ahead on each slot in the event loop, with no lock. A request's deadline is
  its own timeout plus the timeouts of the requests ahead of it on that slot. There is no new IPC,
  and `BuildPool`'s public shape stays the same. This makes D-09's "worst build × 2" true for the
  build itself. It is a second divergence from spur's `pool.py`, and the timeout Lxx states the
  formula.
- **D-15 (research Q3, A1):** Both tiers measure and enforce inside the production Docker image on
  the runner, one container per measurement point, and read the peak from cgroup `memory.peak`. The
  required job reuses the `image` job's build. Venv-only measurement is not a bound.
- **D-16 (research Q4):** The three measured per-artifact timeouts are code constants that cite the
  run, with no environment override. `SCREW_BUILD_TIMEOUT` is removed. A deployer on slower
  hardware re-sweeps, and the new figures go into a superseding entry.
- **D-17 (research Q5):** The cost model also covers the nut, with features `s`, `m`, `clearance`,
  `d`, `pitch` and hand. It retires `NUT_FINE_STL_ROWS` and the clearance > 5.0 refusal
  (`NUT_FINE_STL_CLEARANCE`). L16 is superseded by id. Resolve
  `docs/tech_debt/active/2026-10-14-nut-interim-bounds.md`.
- **D-18 (research Q7):** The pitch boundary is one of the D-08 kernel outer walls. It is the
  root-radius-floor debt, where the kernel fails near root radius 3e-5 mm. It is re-measured by
  walk-to-failure per size, both hands, rod and void, and cited in an Lxx. Resolve the matching
  debt item.
- **D-19 (research Q6, applies D-04):** Five repetitions, with the median and the max recorded, are
  run where a bound is set: the boundary sweep, and each artifact's worst point. Bulk catalogue rows
  in the full tier get one pass. Any row within a margin of its timeout is re-run at 5. The margin
  and the shard sizes come from the measured exploration run and are recorded in the Lxx.
- **Budget (research Q1) stays open on purpose.** It needs data. Run an exploration sweep first,
  then a `checkpoint:decision` puts 2-3 candidate budgets to the owner as a table. The table shows
  the rows kept and refused among the 294 bolt and 14 nut catalogue rows and the free space, plus
  the predicted worst build and bytes. Fitting the final model, setting the timeouts and picking
  the workers all wait for that ruling.

### Claude's Discretion
Each item below is measured on the D-01 runner, cited in an Lxx, and stripped of its `INTERIM` label:
- The gzip level and `minimum_size`, and the bytes-cache budget (`SCREW_EXPORT_CACHE_MB`).
- `SCREW_SOLID_CACHE`, `SCREW_MAX_QUEUED_BUILDS`, `SCREW_WORKERS`, and the HEALTHCHECK timings.
- tmpfs `/tmp` size, and the `_release_arenas` effect on amd64.
- Tessellation presets: keep them unless the sweep shows a reason. They feed the cost model, so a
  change is made before fitting.
- The UI debounce (350 ms) stays a UI choice. It is relabelled as not a runtime bound rather than
  measured.
- The cost model's functional form and features, and the exact boundary-set size and seed.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and rules
- `.planning/ROADMAP.md` § Phase 7 — the goal and the four success criteria.
- `.planning/REQUIREMENTS.md` — OPER-01, OPER-02, OPER-03.
- `AGENTS.md` — L02 standing rules, the gate, and debt filing.
- `docs/architecture/decision_log.md`:
  - L02 (cap/warn/422), L08 (walled main, required jobs, `pr.land`), L09 (interim bounds, the pool divergence D-16).
  - L11 (thread grid, known-bad rows and the platform note), L12/L13/L16 (fine-STL caps, preview row, nut caps).
  - L17/L18/L19 (the final part the sweep measures).

### What is being replaced
- `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` — the full knob table with file:line, the in-cap costs and the resolve instructions.
- `docs/tech_debt/active/2026-10-14-nut-interim-bounds.md` — the nut's interim bounds.
- `docs/tech_debt/active/2026-10-11-default-pitch-d100-length200-exceeds-both-interim-backstops.md` — WR-05 (53.3 s, 9143 MiB). Phase 7 is its trigger.
- `docs/tech_debt/active/2026-10-06-bench-memory-sampling-is-too-coarse-for-short-corpora.md` — read cgroup peak memory.
- `docs/tech_debt/active/2026-10-10-spike-protocol-amendments-before-next-campaign.md` — protocol amendments before the next campaign.
- `docs/tech_debt/active/2026-10-14-m18-probe-one-entry-has-no-deadline-during-a-run.md` — a probe deadline.
- `docs/ideas/2026-10-11-oper-02-resweep-runs-the-controls.md` — run the known-bad controls natively on amd64 and re-check the THRD-04 rows and the L11 list.

### Harness and CI
- `bench/README.md`, `bench/RESULTS.md` — the method, and where runs are recorded.
- `bench/build_time.py`, `bench/memory.py`, `bench/latency.py`, `bench/export_cost.py`, `bench/corpus.py`, `bench/nut_fine_caps.py`.
- `.github/workflows/grid.yml` — the template for a recording tier: dispatch/schedule, `contents: read`, the T-3-14 rationale.
- `.github/workflows/ci.yml`, `.github/workflows/required-jobs.txt`, `scripts/pr_land.py` (`WORKFLOW = "ci.yml"`).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `bench/` harness (ported from spur as harness, not numbers):
  - `make bench.build`: build, fine STL and STEP time per corpus part against the timeout.
  - `make bench.memory`: container sweep at 1, 2 and 4 workers.
  - `make bench.latency`, and `make bench.export` (gzip table).
- `make grid` / `tests/test_grid.py`: the sharded per-size grid runner with the THRD-04 gate (7160 rows).
- `src/screw/calc/thread.py`:
  - `FINE_STL_ROWS`, `MAX_TURNS`, `MIN_TAIL_MM` and the cap readers. The cost model takes their place and their call sites.
  - The kernel-free closed forms (volume, turns) are possible cost features.
- `src/screw/pool.py`: worker processes, the per-build timeout and the D-16 same-slot race guard.
  Per-artifact timeouts plug in here (`tests/test_pool.py`).

### Established Patterns
- A refusal happens before the cache, the admission slot and the pool (the fine-STL 422 today, `app.py`). The CLI exits 2 with the same sentence. API, CLI and page parity is tested (`tests/test_parity.py`).
- Every constant carries its run citation in a comment, with the measurement that forced it (AGENTS.md comment rule).
- Debt is resolved in the same commit as the fix: `git mv` into `resolved/` and an INDEX row move.

### Integration Points
- `src/screw/app.py`: the lifespan knobs, `_GZIP_LEVEL`, the `Retry-After` 503s and the export cache.
- `src/screw/solid/__init__.py`: `TESSELLATION`, `SCREW_SOLID_CACHE`, `_release_arenas`.
- `src/screw/params.py`: `INTERIM_MAX_MM`.
- `src/screw/cli.py`: the `serve` default.
- `Dockerfile` and `compose.yaml`: `mem_limit`, the workers, tmpfs and HEALTHCHECK.
- `src/screw/static/app.js`: the artifacts offered when one is refused.

</code_context>

<specifics>
## Specific Ideas

- Known data points the sweep must cover and explain, all from macOS arm64 single runs:
  - d100 × 200 at the default pitch: 53.3 s, 9143 MiB.
  - d=100, pitch=5, L=1250 fine STL: 152.6 s, 7875 MiB.
  - d=6, pitch=0.1, L=25 fine STL: 101 MiB.
  - d=1e5, pitch=1, L=1: preview did not finish in 120 s.
- On linux/amd64, five L11 rows behave differently from macOS (`Null TopoDS_Shape`, or two solids), so the controls run natively.

</specifics>

<deferred>
## Deferred Ideas

- Sizing for a smaller deploy box (for example 2 vCPU / 4 GB) — a later sweep and a superseding entry once a real deploy target exists.

</deferred>

---

*Phase: 07-operability-re-sweep*
*Context gathered: 2026-10-26*
