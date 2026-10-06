# Phase 1: Runtime Port and Walking Skeleton - Pattern Map

**Mapped:** 2026-10-06
**Files analyzed:** 47 (new or modified)
**Analogs found:** 43 / 47 (4 screw-native design pieces have only pattern-level analogs)

Conventions: `S:` = `/Users/halfb00t/git/halfb00t/spur/` (the house-style reference, read-only, all cited paths are git-tracked there). `R:` = `/Users/halfb00t/git/halfb00t/screw/` (all cited paths git-tracked). Line numbers are spur HEAD (ported surface unchanged since `ec195fb`, RESEARCH.md). Per L07, `S:src/spur/{calc,model,params}.py` are never copied; they appear below as pattern-only.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|
| `src/screw/__init__.py` (mod) | config/utility | n/a | `S:src/spur/__init__.py` | exact |
| `src/screw/__main__.py` | entrypoint | n/a | `S:src/spur/__main__.py` | exact |
| `src/screw/build_errors.py` | model (exceptions) | n/a | `S:src/spur/build_errors.py` | exact |
| `src/screw/params.py` | model + registry | CRUD/validation | `S:src/spur/params.py` (`_f`, frozen model pattern only) | pattern-only |
| `src/screw/calc/__init__.py` | service (pure maths) | transform | `S:src/spur/calc.py` `derive()` (pattern only) | pattern-only |
| `src/screw/solid/__init__.py`, `solid/bolt.py` | service (kernel doorway) | file-I/O + transform | `S:src/spur/model.py` (cache, lock, mesh-on-copy; pattern only) | pattern-only |
| `src/screw/pool.py` | service | request-response (process pool) | `S:src/spur/pool.py` | exact (+1 guard) |
| `src/screw/records.py` | utility (logging) | event-driven | `S:src/spur/records.py` | exact |
| `src/screw/app.py` | controller | request-response | `S:src/spur/app.py` | role-match (route layer rewritten) |
| `src/screw/cli.py` | controller | request-response | `S:src/spur/cli.py` | role-match (arg layer rewritten) |
| `src/screw/static/{index.html,app.js,style.css}` | component | request-response | `S:src/spur/static/*` | role-match |
| `src/screw/static/vendor/*`, `web/*` | vendored asset | batch | `S:src/spur/static/vendor/*`, `S:web/*` | exact (copy) |
| `scripts/{__init__,pr_land,skip_tokens}.py` | utility | batch | `S:scripts/*` | exact (copy) |
| `docker/smoke.py`, `docker/refresh-requirements.sh` | utility | request-response | `S:docker/*` | exact (retype) |
| `Dockerfile`, `compose.yaml`, `.dockerignore` | config | n/a | `S:Dockerfile`, `S:compose.yaml` | exact (retype) |
| `Makefile` (mod) | config | n/a | `R:Makefile` extended from `S:Makefile` | exact |
| `pyproject.toml` (mod) | config | n/a | `R:pyproject.toml` + `S:pyproject.toml` | exact |
| `.pre-commit-config.yaml` (mod) | config | n/a | `R:.pre-commit-config.yaml` + `S:.pre-commit-config.yaml` | exact |
| `.github/workflows/ci.yml` (mod), `required-jobs.txt` | config | n/a | `R:.github/workflows/ci.yml` + `S:.github/workflows/*` | exact |
| `bench/*` | utility | batch | `S:bench/*` | exact (harness), corpus rewritten |
| `tests/conftest.py`, `test_pool.py`, `test_records.py`, `test_api.py`, `test_cli.py`, `test_pr_land.py`, `test_skip_tokens.py`, `test_bench.py` | test | n/a | same names in `S:tests/` | exact (retype) |
| `tests/test_params.py`, `test_parity.py`, `test_solid.py` | test | n/a | `S:tests/test_api.py` UI source assertions; `S:tests/test_model.py` (pattern) | partial |
| `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` + INDEX row | doc | n/a | `R:docs/tech_debt/TEMPLATE.md` | exact |
| `docs/architecture/decision_log.md` (L08, L09), `docs/HOW_TO_DEVELOP.md`, `docs/ideas/*` | doc | n/a | `R:docs/architecture/decision_log.md` L01-L07 | exact |

## Pattern Assignments

### `src/screw/__init__.py` (modify) and `__main__.py`

**Analog:** `S:src/spur/__init__.py` lines 1-13, `__main__.py` lines 1-3. Keep screw's single literal `__version__ = "0.0.0"` line (hatch reads it, R:`src/screw/__init__.py:8`). Add `int_env`:

```python
import os

def int_env(name: str, default: int) -> int:
    """A positive integer setting from the environment, falling back on nonsense."""
    try:
        return max(1, int(os.environ.get(name) or default))
    except ValueError:
        return default
```
`__main__.py` is `from .cli import main` / `main()`. Add `[project.scripts] screw = "screw.cli:main"` to `pyproject.toml`.

---

### `src/screw/build_errors.py` (model, kernel-free)

**Analog:** `S:src/spur/build_errors.py` lines 17-25 (copy; keep docstring rationale lines 1-15, drop "D-02" gear refs).
```python
from __future__ import annotations

class BuildError(RuntimeError):
    """The CAD kernel could not produce a valid solid for these parameters."""

class BuildTimeout(Exception):  # noqa: N818 -- named after asyncio.TimeoutError on purpose
    """A build did not finish within its allotted time; the worker was terminated."""
```

---

### `src/screw/params.py` (model + registry, pattern-only from spur)

**Analog:** `S:src/spur/params.py` lines 8-23 for the `_f` wrapper and `ConfigDict(frozen=True)` (line 31). Do not copy fields (L07). Screw rewrite per RESEARCH Pattern 1: `gt=` not `ge/le`, `allow_inf_nan=False`, `extra="forbid"`, `ClassVar` kind, `KINDS`, `DEFAULT_KIND = "bolt"`, plus the D-14 INTERIM upper bound (`le=`) on `d` and `length` with D-01 label.

```python
# spur pattern (params.py:17-23) -- the shape of _f; change ge/le to gt, add allow_inf_nan=False
def _f[T](default: T, ge: float, le: float, *, title: str, group: str,
          unit: str = "", step: float | None = None, help: str = "") -> T:
    extra: JsonDict = {"group": group, "unit": unit}
    if step is not None:
        extra["step"] = step
    return Field(default, ge=ge, le=le, title=title, description=help,
                 json_schema_extra=extra)
```
Header docstring convention (lines 1-6): "All lengths are millimetres... Field metadata (group, unit, step) is exported through the JSON schema and drives the web form".

---

### `src/screw/calc/__init__.py` and `src/screw/solid/{__init__,bolt}.py`

**Analog (pattern only):** `S:src/spur/calc.py` (`derive()`), `S:src/spur/model.py`. New designs (match + `assert_never`, `PartInfo`/`InfoRow`, F2 overflow guard) have no spur analog: use RESEARCH Pattern 3 and D-15.

Copy these kernel-doorway patterns from `S:src/spur/model.py`:

Lock + checked build + lru cache (lines 63, 551-566):
```python
def _build_checked(p: GearParams) -> cq.Solid:
    try:
        return _build(p)
    except BuildError:
        raise
    except Exception as exc:  # OCCT raises assorted Standard_Failure subclasses
        raise BuildError(f"Geometry kernel failed ({type(exc).__name__}); ...") from exc

_build_cached = lru_cache(maxsize=int_env("SPUR_SOLID_CACHE", 4))(_build_checked)  # label INTERIM (F9)

def build(p): 
    with _LOCK:
        return _build_cached(p)
```
Validity check (lines 545-547): `if len(solids) != 1 or not solids[0].isValid(): raise BuildError(...)`.

Mesh-on-copy, STEP without copy (lines 570-590, L24): `shape.copy().exportStl(str(path), tolerance=tol, angularTolerance=ang, ascii=False, relative=False)` and `shape.exportStep(str(path))`; `TESSELLATION = {"preview": (0.08, 0.5), "fine": (0.01, 0.1)}` (line 53, label INTERIM, F9). `export()` (lines 593-597): `with _LOCK: data = _write_export(...); _release_arenas(); return data`. Expose `build`, `export`, `TESSELLATION` and a cache-clear hook publicly so `bench/` does not import privates. Skeleton cylinder: `cq.Workplane("XY").circle(d/2).extrude(length)` (A8).

Import-boundary: `solid` is the only module with `import cadquery`; `calc` must not import `cadquery`, `logging` or `screw.records` (contracts 2, 4).

---

### `src/screw/pool.py` (service, request-response)

**Analog:** `S:src/spur/pool.py` (copy; retype `GearParams` to `FastenerParams`, `spur.model` to `screw.solid`).

**Imports + spawn context** (lines 20-35):
```python
from .build_errors import BuildTimeout
from .params import GearParams          # -> FastenerParams
from .records import worker_replaced

_SPAWN = mp.get_context("spawn")
P = ParamSpec("P")
```
**Worker import through importlib, never static** (lines 41-50, 53-67; contracts 5/8):
```python
def _warm() -> None:
    importlib.import_module("spur.model")        # -> "screw.solid"

def build_export(p, fmt, quality) -> bytes:
    model = importlib.import_module("spur.model")   # -> "screw.solid"
    return cast(bytes, model.export(p, fmt, quality))
```
**Affinity + identity-guarded replacement** (lines 97-104, 124-155): `self._executors[hash(p) % self.workers]`; `recreate_for` returns early when `self._executors[i] is not executor`; no `cancel_futures=True` (keep the long comment).

**Timeout path with the D-16 guard** (original lines 184-210). Insert the guard before the `_processes` loop, and reword the message ("Try a coarser quality." not "fewer teeth"):
```python
except TimeoutError:
    # NEW (D-16): same-slot race fix, divergence recorded in L09
    if self._executors[hash(p) % self.workers] is not executor:
        raise BuildTimeout(f"Build exceeded the {self.timeout}s per-build timeout. "
                           "Try a coarser quality.") from None
    for proc in executor._processes.values():
        proc.terminate()
    self.recreate_for(p, executor, "timeout")
    raise BuildTimeout(...) from None
except BrokenProcessPool:
    self.recreate_for(p, executor, "broken_pool")
    raise
```
`BuildPool.__init__(workers, timeout)`; `export()` = `await self._run_with_timeout(p, build_export, p, fmt, quality)`.

---

### `src/screw/records.py` (utility, event-driven)

**Analog:** `S:src/spur/records.py` (copy). Changes: `SPUR_LOG_LEVEL` to `SCREW_LOG_LEVEL` (line 168), `_gear_fields` (line 171) to `_part_fields`:
```python
def _part_fields(p: FastenerParams) -> dict[str, object]:
    return {"kind": p.kind, "slug": ..., "params": p.model_dump(exclude_defaults=True)}
```
Keep imports (lines 28-39), `_STANDARD_LOGRECORD_ATTRS` (50-55), `_JsonFormatter` (58+), `configure()` idempotent at two call sites. Per-event helpers `export_served`, `build_failed`, `queue_refused`, `worker_replaced` keep signatures.

---

### `src/screw/app.py` (controller, request-response)

**Analog:** `S:src/spur/app.py`. Keep machinery verbatim, rewrite the route layer (lines 227-246, 368-390).

**Keep (retype env prefix, add INTERIM labels per D-01):** `_BlobCache` (46), `_EXPORTS = _BlobCache(int_env("SPUR_EXPORT_CACHE_MB", 64) * 1024 * 1024)` (88), `_max_queued_builds` (91-98: `int_env("..._MAX_QUEUED_BUILDS", 2 * int_env("..._BUILD_WORKERS", 2))`), `lifespan` (121-150, `int_env("..._BUILD_WORKERS", 2)`, `int_env("..._BUILD_TIMEOUT", 30)`), `GZipMiddleware` line 207 (`minimum_size=1024, compresslevel=_GZIP_LEVEL`), `StaticFiles` mount (208), `PoolState`/`HealthReport`/`/api/health` (297-325), `_gzip` (247-255), `_build_slot` (258-289).

**Admission control to copy** (lines 273-283), change "gears" to "parts":
```python
if not BUILD_QUEUE.acquire(blocking=False):
    queue_refused(request_id, p, fmt, quality, in_flight=_in_flight_builds, max_queued=MAX_QUEUED_BUILDS)
    raise HTTPException(503,
        detail=[{"loc": ["query"], "type": "busy",
                 "msg": f"Busy: {MAX_QUEUED_BUILDS} parts are already being built or compressed. Try again in a moment."}],
        headers={"Retry-After": "5"})
```
**Error mapping to copy** (lines 440-499): `BuildTimeout` -> 503 `type: "timeout"` + `Retry-After`; `BrokenProcessPool` -> 503 `pool_broken`; `except HTTPException: raise` before catch-all; `except Exception` logs `build_failed` then re-raises; `BuildError` -> 422. Response tail: `Content-Disposition` from slug, `Vary: Accept-Encoding`, `Content-Encoding: gzip` when `wants_gzip`.

**Replace (D-08) with this shape**, lifted from spur lines 227-246, 368-390:
```python
class ModelQuery(GearParams):      # -> BoltModelQuery(BoltParams, _Quality)
    quality: Literal["preview", "fine"] = Field("fine", description=...)

def _gear(q):                      # -> generic strip(q, cls)
    return GearParams(**q.model_dump(include=set(GearParams.model_fields)))
    # RESEARCH Pattern 2: def strip[T: FastenerParams](q, cls: type[T]) -> T

@app.get("/api/info")
def info(q: Annotated[InfoQuery, Query()]) -> DerivedDimensions: ...
@app.get("/api/model.{fmt}", response_class=Response, responses={...})
async def model(fmt: Literal["stl","step"], q: Annotated[ModelQuery, Query()], request: Request,
                backend: Annotated[BuildBackend, Depends(build_backend)]) -> Response: ...
```
Screw: `GET /api/{kind}/info` (plain `BoltParams`, so `quality` is a 422), `/api/bolt/model.{stl,step}` (two five-line routes delegating to `_serve()`, the body of spur's `model()`), `GET /api/schema?kind=` (404 via `HTTPException` for unknown kind, 422 when missing), `GET /api/kinds` returning `{"default": DEFAULT_KIND, "kinds": [...]}`. The info response is `PartInfo` (D-15). Contract 5: `app` must not import `screw.solid`/`cadquery` by any path.

---

### `src/screw/cli.py` (controller, request-response)

**Analog:** `S:src/spur/cli.py`. Keep: imports (6-18), `cmd_serve` (71-87, `configure()`, `uvicorn.run("screw.app:app", ..., log_config=None)`, `proxy_headers=True`), `cmd_export` (99-116), `main()` subcommand skeleton (119-149), `--host/--port/--workers/--root-path` env-default pattern (126-130, `SCREW_*`).

**Flag generation to adapt** (lines 42-56): loop per kind, add `allow_abbrev=False` on every parser (Pitfall 4), `Literal` -> `choices`:
```python
for name, field in GearParams.model_fields.items():
    flag = "--" + name.replace("_", "-")
    help_text = f"{field.description} [{field.default}]".replace("%", "%%")
    ...
    g.add_argument(flag, dest=name, default=None, help=help_text, metavar="V", type=field.annotation)
```
**Param assembly + error exit** (lines 59-68), becomes `_params(kind, ns)`:
```python
values = {k: v for k in Model.model_fields if (v := getattr(ns, k)) is not None}
try:
    return Model(**values)
except ValidationError as exc:
    for err in exc.errors():
        where = ".".join(str(x) for x in err["loc"])
        print(f"error: {where + ': ' if where else ''}{err['msg'].removeprefix('Value error, ')}", file=sys.stderr)
    raise SystemExit(2) from None
```
Drop `--mate-teeth`/`_mate_teeth` (lines 20-39). Lazy imports inside commands (`from .calc import derive`, `from .solid import export`, lines 91, 100-102) keep contract 2/3 intact. `cmd_info` prints `derive(p).model_dump_json(indent=2)` (same document as API, D-06/D-15).

---

### `src/screw/static/{app.js,index.html,style.css}` and vendor

**Analog:** `S:src/spur/static/app.js`. Generic parts to copy: `buildForm` loop over `schema.properties` with `prop.group` fieldsets (lines 45-60), `readHash` (94-99), query builder omitting defaults (101-109), `seq` stale-response counter + `AbortController` (171-195), `showMessages`/`problems`, `renderInfo` (136), `setDownloads`, viewer functions (251-330, `textContent` only, never `innerHTML`).

Rewrite (no spur analog): remove `DIMS` table (lines 13-38; D-09/D-10 forbid per-kind labels), render `rows` generically; fetch `api/kinds` and `api/schema?kind=<k>`; `replaceChildren()` and clear `fields`/`defaults` on kind switch (Pitfall 6); write `kind=` only when not `DEFAULT_KIND` (Pitfall 7); `exclusiveMinimum` is not `minimum` (Pitfall 5).

**Vendor copy:** `S:src/spur/static/vendor/{three.bundle.min.js,three.LICENSE}`, `S:web/{entry.js,package-lock.json}`; `S:web/package.json` with the build output path edited (Pitfall 9):
```json
"build": "esbuild entry.js --bundle --format=esm --minify --legal-comments=eof --outfile=../src/screw/static/vendor/three.bundle.min.js && cp node_modules/three/LICENSE ../src/screw/static/vendor/three.LICENSE"
```

---

### `scripts/{__init__,pr_land,skip_tokens}.py`

**Analog:** `S:scripts/*` byte-for-byte copy; `WORKFLOW = "ci.yml"`; no project strings to retype (RESEARCH).

---

### `docker/smoke.py`, `docker/refresh-requirements.sh`, `Dockerfile`, `compose.yaml`

**Analog:** `S:docker/smoke.py`, `S:Dockerfile`, `S:compose.yaml`. Retype `spur` to `screw`, `SPUR_*` to `SCREW_*`.

`smoke.py` core (lines 11-50): `from starlette.types import Message`; raw ASGI `get(path, query)` helper with `receive`/`send` closures; no HTTP client in the image. Paths become `/api/kinds`, `/api/schema?kind=bolt`, `/api/bolt/info`, `/api/bolt/model.stl`, `.step`, and a 422 for a foreign field. The lifespan note at the end of the visible section applies (run under a lifespan-aware driver).

`Dockerfile`: lines 3-56 retype; keep `pip install --no-deps -r requirements.txt` then `pip install --no-deps . && python docker/smoke.py` (23-31), `useradd --system --uid 10001` (33), `HEALTHCHECK --interval=30s --timeout=2s --start-period=30s --retries=3` (53), `CMD ["screw", "serve"]` (56). Label the healthcheck numbers as choices (F9).

`compose.yaml` (lines 1-35): `127.0.0.1:8000:8000`, `SCREW_WORKERS: "1"`, `SCREW_BUILD_WORKERS: "2"`, `mem_limit: 4g`, `read_only: true`, `tmpfs: /tmp:size=256m`, `cap_drop: [ALL]`, `no-new-privileges`. Replace spur's measurement comment (lines 17-25) with the D-01/D-03 text: `INTERIM: from spur L17 (4g, measured on 160-199 tooth gears); Phase 7 re-sweeps (OPER-02)`.

---

### `Makefile` (modify)

**Analog:** `R:Makefile` (existing targets, `$(STAMP)` pattern, `CONSTRAINT`, `-w` scan comment) extended with targets from `S:Makefile`: `serve` (99), `check` (102), `image` (106), `smoke` (117), `up` (120), `down` (130), `logs` (133), `bench.*` (140-156), `lock` (161, becomes `docker/refresh-requirements.sh`), `vendor` (164), `vendor-check` (167), `pr.land` (213), `clean-docker` (225). Skip `test-image` (D-18) and `fixture.regen`. Extend `typecheck` to `mypy src tests docker bench scripts`; `test` to `pytest -n $(PYTEST_WORKERS) --cov --cov-report=term` with spur's clamp (`S:Makefile:94-96`); `no-fake-done` also excludes `src/screw/static/vendor` (Pitfall 8). Every target keeps the `## description` suffix `help` greps.

---

### `pyproject.toml` (modify)

**Analog:** `R:pyproject.toml` lines 110-123 (existing `[tool.importlinter]`, contract 1) and `S:pyproject.toml` lines 130-213.

Contracts 2, 3, 4, 5 copy from `S:pyproject.toml` 166-213 with `spur` renamed `screw`, sources `screw.calc`, `screw.params`, `screw.cli`; contract 5:
```toml
[[tool.importlinter.contracts]]
name = "The serving process never imports the CAD kernel"
type = "forbidden"
source_modules = ["screw.app"]
forbidden_modules = ["cadquery", "OCP"]
allow_indirect_imports = false
```
Contract 8 from RESEARCH Code Examples (`source_modules = ["screw"]`, `ignore_imports = ["screw.solid -> cadquery"]`). Coverage block (`S:pyproject.toml` 130-154): `source = ["src/screw"]`, `concurrency = ["multiprocessing", "thread"]`, `parallel = true`, `sigterm = true`, `precision = 2`; `fail_under` is measured on the finished suite per L34, never copied (spur's 96 is a gear number). Dev extras: `httpx2`, `pytest-xdist`, `pytest-cov` (one human-verify checkpoint, RESEARCH legitimacy audit).

---

### `.pre-commit-config.yaml` (modify)

**Analog:** `R:.pre-commit-config.yaml` (verify hook) plus `S:.pre-commit-config.yaml` lines 15-45:
```yaml
default_install_hook_types: [pre-commit, commit-msg]
repos:
  - repo: local
    hooks:
      - id: verify
        ...
        stages: [pre-commit]          # pinned, else it runs twice (S comment lines 29-32)
      - id: no-skip-token
        name: reject GitHub Actions skip tokens in the commit message
        entry: .venv/bin/python -m scripts.skip_tokens
        language: system
        stages: [commit-msg]
```
After merge each clone re-runs `.venv/bin/pre-commit install` (Pitfall 11).

---

### `.github/workflows/ci.yml` (modify) and `required-jobs.txt`

**Analog:** `R:.github/workflows/ci.yml` (test job, lines 9-27) extended from `S:.github/workflows/ci.yml`.

Add the matrix so the reported name is `test (3.12)` (F6):
```yaml
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python: ["3.12"]
    ...
      - uses: actions/setup-python@v5
        with: { python-version: "${{ matrix.python }}", cache: pip }
      - run: make verify PYTHON=python
        env: { PIP_CONSTRAINT: requirements.txt }
```
Add `vendor-bundle` (setup-node 22, `npm ci`, `npm run build` in `web`, `git diff --exit-code -- src/screw/static/vendor`) and `image` jobs (S lines ~63-90; curl `localhost:8000/api/health`, `/api/bolt/model.stl?quality=preview`, `/api/bolt/model.step`; tag `screw:ci`). `required-jobs.txt` is exactly three lines: `test (3.12)`, `vendor-bundle`, `image`; `tests/test_pr_land.py` fails when they drift from `ci.yml`.

---

### `bench/*` and `tests/*`

**Analog:** `S:bench/{__init__,latency,memory,build_time,export_cost,README}.py|md` (method kept, `import httpx2 as httpx`, `os.getloadavg()` read before the first row); rewrite `corpus.py` to a `d x length` grid. Drop `honeycomb_spike.py`, `tip_chamfer_spike.py`, `sweeps/*`. Use `solid`'s public surface, not privates.

**Tests that port (retype only):** `S:tests/conftest.py` (autouse `_reset_root_logger`, lines 1-25), `test_pool.py` (add the D-16 regression: ten same-slot requests end as `BuildTimeout`, never `AttributeError`), `test_records.py`, `test_pr_land.py`, `test_skip_tokens.py`, `test_bench.py`, generic parts of `test_api.py` and `test_cli.py`. Not ported: `composition.py`, `regression/*`, `test_calc.py`, `test_model.py`, `test_bench` gear scenarios.

**`tests/test_parity.py` (new; one test over `KINDS`)** analog patterns in `S:tests/test_api.py`:
- UI source assertions, lines 120-139 (`test_every_key_the_ui_reads...`): read `STATIC / "app.js"`, extract with `re.findall`, assert `len(...) >= N` so a regex that stops matching fails.
- Round-trip, lines 142-160: collapse whitespace `re.sub(r"\s+", " ", source)` then assert the generic loop tokens exist (`for ... of Object.entries(schema.properties)`).
- F3: restrict the property-access regex to parameter-carrying receivers (`info`, `prop`, `values`, `h`), keep the quoted-literal check, add a positive control (fixture JS containing `info.length` must be caught). Assert `len(KINDS) >= 1`, `DEFAULT_KIND in KINDS`.

**`tests/test_solid.py`, `test_params.py` (new):** pattern from `S:tests/test_model.py` (not read in full): one valid solid, bbox equals `d`/`length`, STEP starts `ISO-10303-21;`, cached solid stays mesh-free after STL export (L24). `test_params.py`: frozen, `extra=forbid`, class-aware eq/hash, `DEFAULT_KIND == "bolt"` literal.

TestClient typing (Pitfall 1): build query params as `dict[str, str | int | float | bool | None]`.

---

### Docs: tech-debt item, decision log, ideas, HOW_TO_DEVELOP

**Analog:** `R:docs/tech_debt/TEMPLATE.md` and the existing `R:docs/tech_debt/active/2026-10-05-shared-infra-extraction.md` (one file per item, INDEX row in `R:docs/tech_debt/INDEX.md` in the same commit). `R:docs/architecture/decision_log.md` L01-L07 for entry shape; new `L08` (wall, cites spur L22/L25, records D-17's L06 narrowing) and `L09` (registry, URL shape, hash `kind=`, interim bounds, pool divergence). `R:docs/ideas/2026-10-05-wall-main-like-spur.md` closed with INDEX row. `R:docs/HOW_TO_DEVELOP.md` §0 and §9 to `make pr.land`; spur's §8 `gh api` calls (`S:docs/HOW_TO_DEVELOP.md`) feed the owner checkpoint (POST + PATCH + read-back, RESEARCH Code Examples).

## Shared Patterns

### INTERIM labelling (D-01, D-14)
**Apply to:** `app.py` (cache 64 MB, queue 2x workers, timeout 30, workers 2, `Retry-After: 5`, gzip `minimum_size`/level), `solid` (`TESSELLATION`, solid cache 4), `compose.yaml`, `Dockerfile` HEALTHCHECK, `app.js` debounce 350 ms, `params.py` upper bound. Each gets a comment reading `INTERIM` + the spur entry (L17/L19/L34) + "Phase 7 re-sweeps (OPER-02)", and a row in the D-02 debt item. Spur's comments (`S:compose.yaml:17-25`) are the standard for carrying the measurement; screw states it is not measured.

### Kernel isolation (contracts 2, 3, 4, 5, 8)
**Source:** `S:pyproject.toml:160-213`. Use `importlib.import_module("screw.solid")` inside workers only (`S:src/spur/pool.py:50,63`), lazy imports inside CLI commands (`S:src/spur/cli.py:91,100-102`), and `build_errors.py`/`records.py` kernel-free so `app` and `cli` can import them.

### Validation once at the model boundary, 422 naming the field
**Source:** `S:src/spur/params.py:17-23` (`_f`) with screw's `gt=` + `allow_inf_nan=False` + `extra="forbid"`. CLI mirrors via `S:src/spur/cli.py:59-68` (exit 2, `error: <loc>: <msg>`).

### Structured logging
**Source:** `S:src/spur/records.py:28-80`. One JSON line per event; `configure()` at `cmd_serve` and `lifespan`; no `extra=` dicts assembled at call sites.

### Error mapping to HTTP
**Source:** `S:src/spur/app.py:440-499`. `BuildError` 422, `BuildTimeout` 503 `timeout`, `BrokenProcessPool` 503 `pool_broken`, busy 503 `busy`, all with `Retry-After: 5` for 503s; `except HTTPException: raise` before the catch-all.

### Standing warning and L02
`walking skeleton: plain unthreaded cylinder, not a product build` verbatim in `warnings` on API and CLI; volume absent from `rows` and explained in `warnings` when non-finite (F2, test `d=1e200`); no `L/P` turns number (CONTEXT specifics).

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `src/screw/calc/__init__.py` (`PartInfo`/`InfoRow`, `derive`) | service | transform | spur's `DerivedDimensions` is a flat gear model (L07 forbids copying calc.py); self-describing rows are new (D-15) |
| `src/screw/params.py` registry (`KINDS`, `DEFAULT_KIND`, per-kind subclasses) | model | CRUD | spur has one `GearParams`; use RESEARCH Pattern 1/2 |
| `src/screw/solid/bolt.py` cylinder, `match` + `assert_never` dispatch | service | transform | spur has one gear builder; RESEARCH Pattern 3 (A1 assumed) |
| `tests/test_parity.py` registry iteration | test | n/a | spur's UI source-assertion tests (`S:tests/test_api.py:120-160`) are the only partial analog |

## Metadata

**Analog search scope:** `S:src`, `S:tests`, `S:scripts`, `S:docker`, `S:bench`, `S:web`, `S:Makefile`, `S:pyproject.toml`, `S:Dockerfile`, `S:compose.yaml`, `S:.github`, `S:.pre-commit-config.yaml`; `R:` config and docs.
**Not re-read in full (counts from RESEARCH.md, which ran them):** `S:scripts/pr_land.py`, `S:scripts/skip_tokens.py`, `S:tests/test_pr_land.py`, `S:bench/*`, `S:src/spur/static/index.html`, `style.css`.
**Tracked-source gate:** every `S:` path above appears in `git ls-files` for spur; every `R:` path appears in `git ls-files` for screw. No `.gsd/capabilities` mirror paths used.
**Pattern extraction date:** 2026-10-06
