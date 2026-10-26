# Phase 7: Operability Re-sweep - Pattern Map

**Mapped:** 2026-10-26
**Files analyzed:** 17 new or modified
**Analogs found:** 16 / 17 (all analog paths are git-tracked, checked with `git ls-files`)

Note: no spur file is cited as an analog. `../spur` is a sibling checkout, not part of this repo. The screw files below are themselves ports of spur's harness, so they are the tracked analogs. spur's `bench/` and `.github/workflows/ci.yml` exist for house-style reading only.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|
| `src/screw/calc/cost.py` (new) | service (pure maths) | transform | `src/screw/calc/thread.py` (`fine_stl_refusal`, `nut_fine_stl_refusal`) | role-match |
| `src/screw/calc/__init__.py` (edit `download_refusal`, `_downloads`) | service | request-response | itself, lines 523-542 | exact |
| `src/screw/calc/thread.py` (retire `FINE_STL_ROWS`, `NUT_FINE_STL_*`; re-measure `MAX_TURNS`, `MIN_TAIL_MM`) | config / constants | transform | itself, lines 29, 37, 384-443 | exact |
| `src/screw/params.py` (`INTERIM_MAX_MM` outer wall) | model | request-response | itself, line 31 | exact |
| `src/screw/pool.py` (per-artifact and queue-aware timeout) | service | event-driven | itself, lines 70-229 | exact |
| `src/screw/app.py` (derived `Retry-After`, miss log, lifespan constants) | controller | request-response | itself, `_serve` lines 480-575 | exact |
| `src/screw/cli.py` (`SCREW_WORKERS` default) | controller | request-response | itself, line 227 | exact |
| `src/screw/solid/__init__.py` (cache and tessellation citations) | service | transform | itself, lines 76, 93-105, 278 | exact |
| `src/screw/static/app.js` (`update()` when preview refused; debounce relabel) | component | request-response | itself (`update`, `setDownloads`) | exact |
| `bench/oper_*.py` (runner point harness, cgroup reader, load driver, fit script) | utility / harness | batch | `bench/memory.py` + `bench/thread_spike/runner.py` | role-match |
| `bench/__init__.py` (`machine_facts` adds CPU model) | utility | transform | itself, lines 21-31 | exact |
| `bench/export_cost.py`, `bench/build_time.py`, `bench/latency.py` (re-run on threaded parts) | utility | batch | themselves | exact |
| `.github/workflows/operability.yml` (new, full recording tier) | config (CI) | batch | `.github/workflows/grid.yml` | exact |
| `.github/workflows/ci.yml` (+ required boundary-set job) and `required-jobs.txt` | config (CI) | batch | `ci.yml` `image` job | exact |
| `scripts/pr_land.py` (full-tier rule) | utility | request-response | itself, `head_refusals` lines 260-300 | exact |
| `Dockerfile`, `compose.yaml` (`mem_limit`, workers, tmpfs, HEALTHCHECK) | config | n/a | themselves | exact |
| `tests/test_cost.py`, pin tests for the new workflow, `tests/test_pr_land.py` / `test_pool.py` / `test_presets.py` / `test_bench.py` extensions | test | n/a | `tests/test_grid.py`, `tests/test_pr_land.py`, `tests/test_pool.py` | exact |
| `docs/architecture/decision_log.md` (L20..) | doc | n/a | L09, L11-L19 entries | exact |

## Pattern Assignments

### `src/screw/calc/cost.py` (service, transform)

**Analog:** `src/screw/calc/thread.py` `fine_stl_refusal` (lines 402-419), reached through `download_refusal`.

**Refusal text convention.** Text starts with the field names, because the CLI prints no `loc`. It has no braces, because pydantic formats custom errors from context. It cites the run and says what is still allowed:
```python
return (f"thread_length and length: the fine STL of a {hand} thread with d {d:g} and pitch "
        f"{pitch:g} is refused above {cap:g} mm of thread ({turns_of(cap, pitch):g} turns), "
        f"the longest L11 measured whose fine STL plus its gzip copy fit the 64 MiB export "
        f"budget (run 2026-10-08-a-grid); the thread built here is {t:g} mm. Shorten "
        f"thread_length or length, or ask for the preview STL or the STEP, which are not "
        f"capped")
```
**Constants-with-citation convention** (`thread.py` 422-430): every constant carries a comment with the run id, the rule fixed before the run, and the measurement that forced it.

**Exact arithmetic.** Use `calc.thread._exact` and `turns_of` for turns. Never use float `length / pitch`.

**Import boundary.** `calc` never imports `cadquery`, `logging` or `screw.records`, so the cost-model miss log lives in `app.py`. A contract in `pyproject.toml` lands in the same commit as the module. Check that `cost.py` falls under the existing `calc` contract, and add it if not.

**Shape (RESEARCH Pattern 2):** `predict(p, fmt, quality) -> Cost` and `bolt_refusal` / `nut_refusal`. Admit only when `prediction * (1 + worst_under_prediction) <= budget` (D-07).

---

### `src/screw/calc/__init__.py` `download_refusal` (service, request-response)

**Analog:** itself, lines 523-542. Keep the `isinstance` dispatch and the `TypeError` for an unknown kind. Replace the body of each branch with `cost.bolt_refusal` or `cost.nut_refusal` (fmt and quality, all three artifacts).
```python
if isinstance(p, BoltParams):
    if fmt == "stl" and quality == "fine":
        return fine_stl_refusal(
            p.d, p.pitch, built_thread_length(p.thread_length, p.length), p.left_hand)
    return None
...
raise TypeError(f"no download rule for kind {p.kind!r}")
```
The docstring says "Only the fine STL is ever refused (D-02)". Update it, since D-06 now refuses per artifact. `_downloads(p)` and `_DOWNLOADS` (the four `(fmt, quality)` pairs) already feed `Download.refusal`, so parity needs no new plumbing.

---

### `src/screw/pool.py` (service, event-driven)

**Analog:** itself. Edit in place.

**Constructor to change** (lines 73-77). The signature `BuildPool(workers, timeout)` stays usable. `tests/test_pool.py` assigns `pool.timeout = 0.2` (lines 163-171, 391-397, 459-493), so keep the attribute as a fallback or override:
```python
def __init__(self, workers: int, timeout: int) -> None:
    self.workers = workers
    self.timeout = timeout
    self.replaced = 0
```
**Seam for the per-artifact timeout.** `export()` (line 224) already receives `fmt` and `quality`. Look up the timeout there and pass it to `_run_with_timeout`:
```python
async def export(self, p, fmt, quality) -> bytes:
    return await self._run_with_timeout(p, build_export, p, fmt, quality)
```
**Clock to change (D-14).** Line 172 is `await asyncio.wait_for(future, timeout=self.timeout)`. Replace it with a deadline of its own timeout plus the timeouts of the requests ahead on that slot. Track the slot's pending timeouts in the event loop with no lock. Increment on submit and decrement in a `finally`.

**Keep unchanged:**
- The same-slot guard `if self._executors[hash(p) % self.workers] is not executor: raise BuildTimeout(...)` (line 189).
- The terminate loop over `executor._processes.values()`.
- `recreate_for(p, executor, cause)` and its identity check.
- The `BrokenProcessPool` branch.

Update both `BuildTimeout` messages (lines 190-193 and 211-214), which interpolate `self.timeout`, to the artifact's timeout. Update the "Not measured for screw; Phase 7 re-sweeps" comment (lines 78-86) with the `max_tasks_per_child` measurement.

**Test analog:** `tests/test_pool.py::test_two_same_slot_timeouts_in_one_incident_end_as_build_timeout_not_attribute_error` (line 536) and the injected-timeout tests at 459-493. Copy them for a queue-aware-deadline case: a request behind a same-slot build keeps its own full timeout.

---

### `src/screw/app.py` (controller, request-response)

**Analog:** itself.

**Refusal site, unchanged in shape** (lines 489-492). The 422 `type` string `fine_stl_cap` is part of the published error shape, so a rename must be listed in the Lxx:
```python
refusal = download_refusal(params, fmt, quality)
if refusal is not None:
    raise HTTPException(422, detail=[{"loc": ["query"], "type": "fine_stl_cap",
                                      "msg": refusal}])
```
**503 sites with the literal `"5"`:** lines 337, 552 and 570. The `BuildTimeout` site is lines 541-553:
```python
build_failed(request_id, params, fmt, quality, exc=exc, duration_s=time.monotonic() - start)
raise HTTPException(503, detail=[{"loc": ["query"], "msg": str(exc), "type": "timeout"}],
                    headers={"Retry-After": "5"}) from exc
```
Replace all three with one helper: the artifact's median build × queue depth, rounded up to whole seconds (D-11). Add a test that none keeps the literal. Log the cost-model miss at the `BuildTimeout` branch, through `screw.records` next to `build_failed`.

**Knob lines to edit:**
- 155: `int_env("SCREW_BUILD_WORKERS", 2)`.
- 165: `int_env("SCREW_BUILD_TIMEOUT", 30)`. Remove it (D-16).
- 114: `SCREW_MAX_QUEUED_BUILDS`.
- 100: `_EXPORTS = _BlobCache(int_env("SCREW_EXPORT_CACHE_MB", 64) ...)`.
- 256 and 260: `_GZIP_LEVEL = 1` and `minimum_size=1024`.

`int_env` returns a positive int. Per-artifact timeouts become code constants, as floats or ints, with no env override (D-16).

---

### `src/screw/static/app.js` (component, request-response)

**Analog:** itself. Grep `async function update` and `setDownloads`. The update loop fetches `info`, then `GET .../model.stl?quality=preview`, and only then calls `setDownloads(q, info.downloads)`. On a preview refusal, still render the info panel and call `setDownloads`. `setDownloads` already links the first non-refused entry per format. Debounce at line 585 (`setTimeout(update, 350)`) gets a "UI choice, not a runtime bound" comment.

---

### `bench/oper_*.py` (harness, batch)

**Analogs:** `bench/memory.py` for the container driver, and `bench/thread_spike/runner.py` (`Worker`, `run_once`, deadline) for per-row child isolation.

**Capped row, no number** (`memory.py` 61-72). Reuse for a `docker run --memory` cap:
```python
_SWEEP_MEM_LIMIT_BYTES = 8 * 1024**3
_CAP_TOLERANCE_FRACTION = 0.01
def _is_capped(peak_bytes: int, ceiling_bytes: int) -> bool:
    return peak_bytes >= ceiling_bytes * (1 - _CAP_TOLERANCE_FRACTION)
```
**Fixed worker constant, not `os.cpu_count()`** (`memory.py` 41-45). Pass the cap as an integer with a `b` suffix, so the number Compose applies and the number `_is_capped` compares are the same constant. `memory.py` line 188 has the per-N container naming `screw-bench-n{n}` and the `_teardown` pattern.

**Must change versus `memory.py`:**
- It drives the corpus one request at a time with one `httpx.Client`. The load sweep needs concurrent clients, at least workers plus queue depth.
- `for n in (1, 2, 4)` becomes 1, 2, 3.
- Replace `docker stats` polling with a read of `/sys/fs/cgroup/memory.peak` at the end. Fail loudly with no number if the file is missing or the filesystem is not `cgroup2fs`; fall back to `memory.max_usage_in_bytes` only if present.

**Pre-registered rule style** (`bench/nut_fine_caps.py` module docstring, lines 1-30): state "THE RULE ... fixed before any row ran", the STOP CONDITIONS and the constants in the module docstring, committed before the run. Do the same for the budget, worker pick, timeout, headroom and gzip level.

**Gzip rule analog:** `bench/export_cost.py` `_decisions` / `select_gzip_level` (lines 117-148). Integer arithmetic for the shrink clause, direct float compare for the wall clause:
```python
shrunk = 10 * (current.out_bytes - candidate.out_bytes) >= current.out_bytes
wall_ok = candidate.concurrent_ms <= 1.5 * current.concurrent_ms
```
Screw's thresholds must be stated, not inherited as numbers.

**Noise:** `bench/quiet.py` (`QUIET_BAR`, `Reading`, `_read_load1`) records load per block. WR-03 asks for a reading per row.

**`machine_facts`** (`bench/__init__.py` 21-31) prints CPU count, arch and RAM. Add the `/proc/cpuinfo` model name (D-01). Use `statistics.quantiles(x, n=20)[-1]` for p95, as `bench/latency.py::_p95` does.

---

### `.github/workflows/operability.yml` (CI, batch)

**Analog:** `.github/workflows/grid.yml` (47 lines). Copy this structure:
```yaml
on:
  workflow_dispatch:
  schedule:
    - cron: "23 3 * * 1"
permissions:
  contents: read
jobs:
  grid:
    runs-on: ubuntu-latest
    timeout-minutes: 120
    strategy:
      fail-fast: false
      matrix: ...
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12", cache: pip}
      - run: make grid PYTHON=python SIZE=${{ matrix.size }}
      - name: kernel pair this run resolved
        if: always()
```
**Differences:**
- Add `pull_request:` with a `paths:` filter (D-13), still `permissions: contents: read`, no `secrets.`, never `pull_request_target`.
- Build the image as in the `ci.yml` `image` job (`docker/setup-buildx-action@v3`, `docker/build-push-action@v6` with `load: true`).
- Run one container per point and record `nproc`, RAM and the CPU model.
- Name the workflow and its comments so they avoid the word "grid" only where tests demand. The `"grid" not in ci` test covers `ci.yml` only.
- Add a Makefile target listed by `make` (help lines use `## text`).

**Pin test analog:** `tests/test_grid.py::test_the_grid_workflow_has_no_pull_request_or_push_trigger_and_reads_only` (lines 94-102). Invert the `pull_request` assertion to `pull_request` present and `pull_request_target` absent. Keep these assertions:
```python
assert re.search(r"^permissions:\n  contents: read$", text, re.MULTILINE)
assert "secrets." not in text
```
Add a test that the workflow's `paths:` list equals `pr_land`'s list.

---

### `.github/workflows/ci.yml` + `required-jobs.txt` (CI, batch)

**Analog:** the `image` job (lines 58-77 of `ci.yml`): buildx, `build-push-action@v6` with `tags: screw:ci`, then `docker run -d`, a health `curl` loop and `docker rm -f`. Add the boundary-set job after it, running inside `screw:ci` (D-15). Do not make a second image build; use the same job or an `needs:` plus rebuild from cache.

`required-jobs.txt` today lists `test (3.12)`, `vendor-bundle` and `image`. Add the new job name in the same commit. `tests/test_pr_land.py::test_required_jobs_file_matches_ci_yml_job_names` (line 269) fails otherwise.

**Tripwire:** `tests/test_grid.py::test_the_grid_tier_is_not_a_required_job` asserts `"grid" not in ci` over the whole text of `ci.yml`, comments included.

---

### `scripts/pr_land.py` (utility, request-response)

**Analog:** itself. `WORKFLOW = "ci.yml"` (line 56) stays, and a test pins it. Add a second constant for the full-tier workflow and a pure function in the style of `head_refusals` (lines 260-300):
- Take the PR's changed paths and the newest full-tier run for the head as parameters.
- Return a `list[str]` of refusals in the `pr.land: ...` message style, where an empty list means go.
- Keep it read-only and fixture-testable with recorded `gh` JSON, using the `parse_*` helpers at lines 134-208 (`_as_object`, `_as_array`, `_as_str`).

The path list lives in `pr_land.py`, which is the authority. The workflow's `paths:` filter only saves runs. Refuse when the full-tier run is missing, red or in progress for the head sha (A8: check `head_sha` equality). Record the change as a new Lxx. Its text must say that changing `pr_land.py` is the "first fix that has to land in both repos" trigger for L07.

**Test analog:** `tests/test_pr_land.py::test_head_refusals_*` (lines 340-386). One test per outcome: no run, in progress, red, success on another sha, and the diff misses the paths.

---

### `Dockerfile` / `compose.yaml` (config)

**Analog:** themselves.
- `mem_limit: 4g` (`compose.yaml:20`) becomes `peak × workers + headroom` and must be under 16 GB (D-02).
- `SCREW_WORKERS` (`compose.yaml:14`, `Dockerfile:41`).
- `/tmp:size=256m` (`compose.yaml:26`) is sized from the largest admitted raw STL, together with the bytes budget (Pitfall 3).
- `HEALTHCHECK --interval=30s --timeout=2s --start-period=30s --retries=3` (`Dockerfile:51`).

Each edit carries a comment citing the run. A consistency test reads these values against the decision log (Wave 0 gap).

---

### Tests

- `tests/test_cost.py` (new): follow the kernel-free unit style of `tests/test_thread_maths.py`. Cover golden values at measured points, monotonicity and the envelope factor.
- Update `tests/test_presets.py:172-189`. It asserts `len(refused) == 62` and references `FINE_STL_ROWS`. The new figure comes from the owner-ruled budget.
- Retirement blast radius: `tests/test_thread_maths.py` (17 refs), `tests/test_mesh.py` (compares the fine preset to the caps header), `tests/test_calc.py`, `tests/test_solid.py`, `tests/test_bench.py` (3 refs).
- `tests/test_bench.py`: add synthetic-input tests for the cgroup reader, capped rows and the p95 sample floor.
- `tests/test_parity.py`: extend for per-artifact refusal parity across API 422, CLI exit 2 and `downloads[].refusal`.

---

## Shared Patterns

### One refusal judge
**Source:** `src/screw/calc/__init__.py` `download_refusal` (523-542), `app._serve` (489-492), `cli.cmd_export`, `_downloads`.
**Apply to:** the cost model and every front end. No second refusal path and no new 422 shape.

### Constants carry the run that forced them
**Source:** the comments on `FINE_STL_ROWS` and `NUT_FINE_STL_ROWS` in `src/screw/calc/thread.py` (422-430), and the `bench/memory.py` constants.
**Apply to:** every constant in the phase. The comment names the run id in `bench/RESULTS.md`, the rule and the host. Strip `INTERIM` labels.

### Pre-register the rule, then run
**Source:** `bench/nut_fine_caps.py` docstring, `bench/export_cost.py::select_gzip_level`.
**Apply to:** gzip, cache, workers, solid cache, queue depth and headroom.

### Capped or killed means no number (L02)
**Source:** `bench/memory.py::_is_capped`. **Apply to:** every probe, which also runs with a `--memory` cap and a wall deadline.

### Debt flip in the fixing commit
`git mv` the debt item into `docs/tech_debt/resolved/`, add the sha and move the INDEX row. This covers the interim-runtime-bounds, nut-interim-bounds, WR-05, bench-memory-sampling and root-radius-floor items.

### Import boundaries
`calc` stays kernel-free. `cadquery` stays inside `screw.solid`. `screw.app` never imports the kernel. Use `make lint-imports`.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| The `memory.peak` cgroup reader and concurrent load driver | harness | batch | `bench/memory.py` is sequential and uses `docker stats`. Reuse its scaffolding (`_is_capped`, teardown, naming), but the reader and the concurrent client driver are new. Use RESEARCH Pattern 3. |

## Metadata

**Analog search scope:** `src/screw/`, `bench/`, `scripts/`, `.github/workflows/`, `tests/`, `Makefile`; `../spur/bench` and `../spur/.github` listed only.
**Files read:** about 14 (full or targeted ranges).
**Pattern extraction date:** 2026-10-26
