# Phase 3: Real Helical Thread - Pattern Map

**Mapped:** 2026-10-10
**Files analyzed:** 22 (5 new, 17 modified; docs and debt items grouped)
**Analogs found:** 22 / 22 (all analogs are git-tracked source under `src/`, `bench/`, `tests/`, `.github/`)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|
| `src/screw/calc/thread.py` (new) | utility (kernel-free maths + cap rules) | transform | `bench/thread_spike/maths.py` (moves from it) | exact (move) |
| `src/screw/solid/helical.py` (new) | service (kernel builder) | transform | `bench/thread_spike/helical.py` `section`/`twist`/`thread` | exact (move) |
| `src/screw/solid/bolt.py` (mod) | service (kind assembly) | transform | itself (`cylinder`) | exact |
| `src/screw/solid/__init__.py` (mod) | service (gate, cache, export) | request-response | itself (`_build`/`_build_checked`/`_write_export`) | exact |
| `src/screw/params.py` (mod) | model | CRUD/validation | itself (`_f`, `FastenerParams`) | exact |
| `src/screw/calc/__init__.py` (mod) | service (info document) | transform | itself (`_bolt`) | exact |
| `src/screw/app.py` (mod) | controller | request-response | itself (`_serve`, `_BlobCache`) | exact |
| `src/screw/cli.py` (mod) | controller | request-response | itself (`_add_args`, `cmd_export`) | exact |
| `src/screw/static/app.js` (mod) | component | event-driven | itself (`buildForm`, `navigate`, `partQuery`, `showMessages`) | exact |
| `bench/thread_spike/{helical,maths,measure}.py` (mod) | utility (re-export) | transform | `bench/thread_spike/measure.py` volume call | exact |
| `tests/test_thread_maths.py` (new) | test | transform | `tests/test_calc.py` | role-match |
| `tests/test_grid.py` (new) | test | batch | `tests/test_solid.py` + `bench/thread_spike/measure.py` | role-match |
| `tests/test_{parity,solid,api,cli,params,bench}.py` (mod) | test | request-response | themselves | exact |
| `.github/workflows/grid.yml` (new) | config | batch | `.github/workflows/ci.yml` | role-match |
| `pyproject.toml` (mod) | config | n/a | itself (markers, importlinter) | exact |
| `Makefile` (mod, optional) | config | n/a | `bench.thread` target (line 166) | exact |
| `docs/architecture/{decision_log,overview}.md`, `docs/tech_debt/**` (mod) | doc | n/a | existing L11 entry / existing items | exact |

## Pattern Assignments

### `src/screw/calc/thread.py` (utility, transform)

**Analog:** `bench/thread_spike/maths.py` lines 79-129. Move `fundamental_height`, `thread_depth`, `_radii`, `section_radius`, `section_area`, `closed_volume` verbatim. Grid, frontier and preset helpers (`standard_max`, `lengths`, `frontier_turns`, `depth_presets`, `interference_area`, `VOID_CLEARANCE`, `RULED_MODULE`) stay in bench. `bench/thread_spike/maths.py` then does `from screw.calc.thread import ...` (02 D-18).

**Core excerpt** (maths.py 79-129):
```python
def fundamental_height(pitch: float) -> float:
    return math.sqrt(3) / 2 * pitch

def thread_depth(pitch: float) -> float:
    return 5 / 8 * fundamental_height(pitch)

def _radii(d, pitch, clearance) -> tuple[float, float]:
    return d / 2 + clearance, d / 2 - thread_depth(pitch) + clearance

def section_area(d, pitch, clearance=0.0) -> float:
    ro, rr = _radii(d, pitch, clearance)
    return (math.pi / 8 * ro**2 + math.pi / 4 * rr**2
            + 5 * math.pi / 24 * (ro**2 + ro * rr + rr**2))

def closed_volume(d, pitch, length, clearance=0.0) -> float:
    return section_area(d, pitch, clearance) * length
```
Keep the docstrings (they carry the derivation). Imports: only `math` (plus `Fraction` is NOT needed here). Contract 2 and 4 forbid `cadquery`, `OCP`, `logging`, `screw.records` under `screw.calc`.

**New kernel-free rules to add here** (no analog; write in the same style as existing INTERIM comments, see `params.py` 17-33 for comment form):
- `MAX_TURNS = 250` with comment citing `2026-10-08-a-frontier` (L11 style, run id in comment).
- root-radius bound `d/2 - thread_depth(pitch) <= 0` (D-04), reusing `thread_depth`.
- L11 measured rows table (7 rows, one run id per row, labelled "L11 measured rows (`2026-10-08-a-grid`), not ISO rows") plus one function `fine_stl_cap(d, pitch)` returning the cap or None, shared by `app._serve` and `cli export`.

---

### `src/screw/solid/helical.py` (service, transform)

**Analog:** `bench/thread_spike/helical.py` lines 1-115. Move `section`, `twist`, `thread`, and the constants `SECTION_SAMPLES=14`, `MAX_SEGMENTS=500`, `SEWING_TOLERANCE=1e-4` with their "(STACK, measured)" comments. `naive_sweep_fuse`, `one_pipe`, `trim_tip`, `ruled_reference` stay in bench.

**Imports** (helical.py 12-23), change the last line to the calc module:
```python
from __future__ import annotations
import math
import cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakePipeShell
from OCP.TopoDS import TopoDS
from screw.calc.thread import thread_depth
```
Contract 8 already allows `screw.solid.** -> cadquery`. Absolute `screw.` imports are the convention in `solid/` (see `solid/bolt.py` line 7).

**Core pattern** (helical.py 63-114): `twist` = `BRepOffsetAPI_MakePipeShell` with auxiliary helix, `SetMaxSegments(MAX_SEGMENTS)`, `SetMode(aux, False)`; `thread` = K-turn base twist translated per segment, remainder segment, `BRepBuilderAPI_Sewing(SEWING_TOLERANCE)`, skip interior PLANE seam caps where `abs(z - z0) < 1e-7`, then `cq.Solid.makeSolid(cq.Shell(TopoDS.Shell_s(sew.SewedShape())))`.

**Changes the spike version does not have:**
- Default `k=3` (L11), spike's is `k=5`.
- Takes `length` (not `turns`), places the remainder segment to end at `z = length` exactly (CONTEXT Discretion; Pitfall 1). Current `end = turns * pitch` is the drift to avoid.
- D-17: `if not length >= MIN_TAIL_MM: raise BuildError(...)` (1e-3 mm, INTERIM, cite the 2026-10-10 probe); fold a sub-`MIN_TAIL_MM` remainder into the previous segment. `BuildError` from `screw.build_errors` (24-line module).
- Spike's `if turns <= 0: raise ValueError` is replaced by the D-17 check.

---

### `src/screw/solid/bolt.py` (service, transform)

**Analog:** itself. Current whole body (lines 1-17): `def cylinder(p: BoltParams) -> cq.Solid: return cq.Solid.makeCylinder(p.d / 2, p.length)`. Replace the body with a call to `helical.thread(p.d, p.pitch, p.length, left_hand=p.left_hand)`; keep the typed-`Solid` return and the module docstring style. File keeps its name.

---

### `src/screw/solid/__init__.py` (service, request-response: gate and export)

**Analog:** itself. The gate goes inside the function `lru_cache` wraps so a raise is never cached.

**Current funnel to extend** (lines 73-99):
```python
def _build(p):
    ...
    if len(solid.Solids()) != 1 or not solid.isValid():
        raise BuildError("Geometry kernel produced an invalid solid for these parameters.")
    return solid

def _build_checked(p):
    try:
        return _build(p)
    except (BuildError, TypeError):
        raise
    except Exception as exc:  # OCCT raises assorted Standard_Failure subclasses
        raise BuildError(f"Geometry kernel failed ({type(exc).__name__}); "
                         "check d and length.") from exc

_build_cached = lru_cache(maxsize=int_env("SCREW_SOLID_CACHE", 4))(_build_checked)
```
Add to `_build`, after the existing validity/one-solid check: precise volume via
`BRepGProp.VolumeProperties_s(shape.wrapped, props, 1e-6, False, False)` (copy from `bench/thread_spike/measure.py` 38-42, `PRECISE_EPS = 1e-6`), compare `(v - closed_volume(...)) / closed_volume(...)` against `T_gate = 9e-05`, put the signed error in the `BuildError` message. Imports (`from OCP.BRepGProp import BRepGProp`, `from OCP.GProp import GProp_GProps`) are allowed here (contract 8). The `check d and length.` message should also name `pitch`.

**Export status checks** (D-08), extend `_write_export` (lines 114-133): check the `bool` from `shape.copy().exportStl(...)`, check the STEP status for `IFSelect_RetDone`, and compare the STL header count (`struct.unpack("<I", stl[80:84])`) with `84 + 50 * count == len(data)`; the unpack is already in `tests/test_solid.py` 17-21 as `_triangles`. Keep the `copy()` and its L24 comment untouched.

---

### `src/screw/params.py` (model, validation)

**Analog:** itself.

**Field helper** (lines 36-45), `_f` requires `gt`, so add a sibling for bool with the same `json_schema_extra` shape:
```python
def _f[T](default: T, *, gt: float, le: float | None = None, title: str, group: str,
          unit: str = "", step: float | None = None, help: str = "") -> T:
    extra: JsonDict = {"group": group, "unit": unit}
    ...
    return Field(default, gt=gt, le=le, allow_inf_nan=False, title=title, description=help,
                 json_schema_extra=extra)
```
**Field placement** (lines 63-67): `left_hand: bool = ...` on `FastenerParams`, default `False` with the frozen-default comment in the style of lines 59-62. The `pitch` help text ("The walking skeleton builds no thread") and `BoltParams.length` help text ("Length of the cylinder") and docstring must be rewritten.

**Cross-field rules:** no `model_validator` exists yet; add `@model_validator(mode="after")` on `BoltParams`/base that raises `ValueError` naming both fields (CLI strips `"Value error, "` at `cli.py` 46, `app.js` `problems()` strips it too, and reads `ctx.fields` for highlighting, so check how `ctx.fields` is produced by `app.py` before choosing the error shape). Import `screw.calc.thread` lazily inside the validator (spur pattern, CONTEXT code_context), because `calc/__init__.py` imports `screw.params` (circular otherwise).

`slug()` (69-76) iterates `model_fields` with `%g`; a bool renders `Falseg`-unsafe? `f"{True:g}"` gives `1`, so fine, but add a test.

---

### `src/screw/calc/__init__.py` (service, transform)

**Analog:** itself, `_bolt` (lines 43-63). Remove `SKELETON_WARNING` (line 19) and replace with the pinned text `threaded rod: no head, plain-cut thread ends; not a product build`. Rows follow the `InfoRow(key=..., label=..., value=..., unit=...)` shape; add `turns`, `thread depth`, `minor diameter` (labels carry "ISO 68-1:2023 basic profile"); `volume` becomes `section_area(d, pitch) * length` from `screw.calc.thread` (use `closed_volume`). Keep the `OverflowError` guard structure (lines 54-62) around the new volume. `left_hand` is not a row (D-07).

---

### `src/screw/app.py` (controller, request-response)

**Analog:** itself. `_serve` (line 376+) is where the D-02 fine-STL cap runs before any build is requested; the existing refusal shape to copy is lines 427 and 453:
```python
raise HTTPException(422, detail=[{"loc": ["query"], "msg": str(exc), ...}])
```
Duplicate-key refusal (D-12): the unknown-kind refusal at line ~357 is the model for a hand-built detail: `{"loc": ["query", "kind"], "type": "unknown_kind", ...}`; use `{"loc": ["query", name], "type": "duplicate"}`. `app.py` must not import `screw.solid` (contract 5), but `screw.calc.thread` is fine (kernel-free). `_BlobCache.put` (lines 62-71) silently drops over-budget blobs: that is the behaviour D-02 reasons from; no change needed there.

---

### `src/screw/cli.py` (controller, request-response)

**Analog:** itself. `_add_args` (lines 21-35) branches on `get_origin(field.annotation) is Literal`; add a `bool` branch before the generic one:
```python
g.add_argument(flag, dest=name, default=None, help=help_text,
               action=argparse.BooleanOptionalAction)
```
`field.annotation is bool` is the test. For D-12, wrap argument registration with a custom `argparse.Action` subclass that exits 2 naming the flag when `getattr(ns, dest)` is already set (defaults are `None`, so "already set" is detectable). `_params` (38-48) and the `error:` / exit 2 printing are reused unchanged. `cmd_export` (75-94) gets the D-02 fine-cap check after `_params` and before `export(...)`; failure form is `raise SystemExit(f"error: {exc}")` as at line 90 (exit 1 path for BuildError; for the cap decide exit status per D-02 "error exit"). Lazy imports stay inside the command (lines 80-84); `screw.calc.thread` is kernel-free so it may sit with `derive`.

---

### `src/screw/static/app.js` (component, event-driven)

**Analog:** itself.
- Checkbox branch in `buildForm` (lines 63-76): add `else if (prop.type === 'boolean')` creating `input.type = 'checkbox'` ahead of the number branch. `defaults[name] = prop.default` (line 47) will be `false`.
- Hash read in `navigate` (line 125): `input.value = h.get(name) ?? defaults[name]` must set `input.checked` for checkboxes.
- `partQuery` (134-145) already has the changed-vs-default branch on `input.type === 'number'`; add a checkbox branch writing `true` only when checked (D-09).
- Foreign key refusal (D-10): copy the unknown-kind block in `navigate` (lines 110-120): `showMessages([...]); return;` naming the keys, after comparing `h.keys()` with the schema field names (do after `buildForm`, before `update()`).
- Warnings on failure (D-11): `showMessages(errors, warnings)` (154-160) already takes both; `renderInfo` (180-190) calls it with `[]` errors; `fail()` must pass the last warnings. Keep `tests/test_parity.py` 206-230 true: no field-name literals in the source.

---

### `bench/thread_spike/{helical,maths,measure}.py` (utility, transform)

**Analog:** `measure.py` lines 38-42 (`precise_volume`) is the call the gate copies; bench modules re-import the moved names (`from screw.calc.thread import ...`, `from screw.solid.helical import section, twist, thread`). Contract at `pyproject.toml` 207-225 keeps `bench.thread_spike.maths` kernel-free without `allow_indirect_imports`, so `screw.calc.thread` must have no kernel path (it does not). `helical.py` imports `RULED_MODULE, thread_depth` from `maths` (line 23); keep that working through the re-export. The precondition harness-review PR must have landed first (CONTEXT D-13); do not fold its fixes in.

---

### `tests/test_thread_maths.py` (new, test, transform)

**Analog:** `tests/test_calc.py` (kernel-free) for structure; assertions of `closed_volume` against `bench/thread_spike/maths` values and the root-radius bound at `pitch ≈ 0.9238 d`. No kernel imports (it must run under contract 2's spirit).

### `tests/test_grid.py` (new, test, batch)

**Analog:** `tests/test_solid.py` header (lines 1-21: `from screw.solid import build, clear_cache, export`, `TOL`, `pytest.approx`). Gate sample in `make verify`: default M6x20 RH, one LH, one void at `maths.VOID_CLEARANCE = 0.20`, sub-turn, non-integer turn, plus an integer-turn float-drift length, plus the positive control feeding `bench.thread_spike.helical.naive_sweep_fuse` into the gate (expects `BuildError`). The full-corpus test carries a new pytest marker; register it in `pyproject.toml` (`addopts = "--strict-markers"` at line 112 makes an unregistered marker an error) and deselect it from the default run. The corpus generator is `bench.thread_spike.maths.lengths()`/`standard_max()`; import it, do not re-pick. Void rows call `helical.thread(..., clearance=0.20)` directly (the gate's closed form takes `clearance`).

### `tests/test_{parity,solid,api,cli,params,bench}.py` (mod)

- `test_parity.py`: registry-driven via `@pytest.mark.parametrize("kind", list(KINDS))` (lines 108-206); the boolean branch is covered by the field existing; add the duplicate-key parametrised test for API and CLI (D-12) in the same style, and the foreign-hash-key source assertion modelled on lines 206-242.
- `test_solid.py`: bounding-box test (lines 26-36) becomes `d x d x length`; `_triangles` helper reused for the header-count check.
- `test_bench.py`: line referencing `INTERIM_PRESETS == TESSELLATION` stays; add re-export identity checks.
- `test_api.py` / `test_cli.py` / `test_params.py`: the 422 naming-fields tests and the D-06 warning assertions follow their existing SKELETON_WARNING assertions (grep `SKELETON_WARNING` / the warning text to update each site).

---

### `.github/workflows/grid.yml` (new, config, batch)

**Analog:** `.github/workflows/ci.yml` (lines 1-35): same `actions/checkout@v4`, `actions/setup-python@v5` with `python-version: "3.12"` and `cache: pip`, and `make` entry points. Triggers: `workflow_dispatch` plus `schedule: cron`. Add a job matrix to shard the corpus. Do not add the job name to `.github/workflows/required-jobs.txt`; verify `tests/test_pr_land.py` reads `ci.yml` only before relying on that (D-14).

### `pyproject.toml` / `Makefile`

`pyproject.toml`: add the marker under `[tool.pytest.ini_options]` (line 110-115), and consider whether import-linter contract 7's `source_modules` (lines 216-222) needs no change (it does not: `maths` stays listed and now reaches calc). `Makefile`: an optional grid target follows `bench.thread` (line 166, `## ... ARGS=...` doc comment style that `help` parses).

### Docs

`docs/architecture/decision_log.md`: new `L12` after `L11`, same entry shape as L11 (read L11 before writing; cites run ids). `docs/tech_debt/`: resolve four items by `Status: resolved`, sha, `git mv` to `resolved/`, INDEX row moved in the fixing commit; add the D-18 figures to `2026-10-05-interim-runtime-bounds.md`.

## Shared Patterns

### Error model
**Source:** `src/screw/build_errors.py` (`BuildError`), `src/screw/solid/__init__.py` 84-93.
**Apply to:** `helical.py` (D-17), the gate (D-08), export checks. Kernel exceptions become `BuildError`; `BuildError` and `TypeError` pass through; `lru_cache` never stores a raise. API maps `BuildError` to `422` (`app.py` ~427), CLI to `SystemExit("error: ...")` (`cli.py` 89-90).

### Boundary validation
**Source:** `src/screw/params.py` `_f` and `FastenerParams`.
**Apply to:** `left_hand`, turn cap, root-radius bound. Validate once, `422` naming the fields (L02), never clamp.

### INTERIM and measured-constant comments
**Source:** `params.py` 17-33, `solid/__init__.py` 37-41, `helical.py` 25-33.
**Apply to:** every new constant (`MAX_TURNS`, `MIN_TAIL_MM`, `T_gate`, the row table). Form: `INTERIM`, source, run id, "Phase 7 re-sweeps".

### Import boundaries
**Source:** `pyproject.toml` 141-225.
**Apply to:** `calc/thread.py` (no `cadquery`/`OCP`/`logging`), `app.py` (no static path to `screw.solid`), `cli.py` (no `screw.app`, lazy kernel imports), `solid/helical.py` (kernel allowed). Run `make lint-imports`; the bench contract has no `allow_indirect_imports`.

### Registry-driven front ends
**Source:** `cli._add_args`, `app.js` `buildForm`, `tests/test_parity.py`.
**Apply to:** `left_hand` and any later field: no per-field code in the form, flag generator or UI.

### Vendor types stop at their boundary
**Source:** `solid/__init__.py` docstring (lines 1-13).
**Apply to:** `helical.py` returns `cq.Solid` only to `solid/`; bytes or `BuildError` leave the package. Gate volume is a float.

## No Analog Found

| File / Piece | Role | Data Flow | Reason |
|---|---|---|---|
| Boolean field helper in `params.py` | model | validation | no non-numeric non-Literal field exists; extend `_f` style by hand |
| `argparse.Action` duplicate-flag refusal and `BooleanOptionalAction` | controller | request-response | no custom Action in `cli.py` today |
| Duplicate-query-key pre-validation in `app.py` | controller | request-response | no pre-validation hook; unknown-kind detail at ~357 is the nearest shape |
| `after` model validator for cross-field rules | model | validation | `params.py` has no validator yet; use RESEARCH Pattern 1 and a lazy `calc.thread` import |
| Checkbox branch and hash round-trip in `app.js` | component | event-driven | form builds number and select only; follow the `enum` branch as shape |
| Workflow shard matrix in `grid.yml` | config | batch | `ci.yml` has a one-entry matrix only |

## Metadata

**Analog search scope:** `src/screw/**`, `bench/thread_spike/**`, `tests/`, `.github/workflows/`, `pyproject.toml`, `Makefile`
**Files read:** CONTEXT.md, `solid/__init__.py`, `solid/bolt.py`, `params.py`, `calc/__init__.py`, `cli.py`, `build_errors.py`, `bench/thread_spike/{helical,maths,measure}.py` (targeted), `app.py` (ranges), `static/app.js` (40-200), `ci.yml` (head), pyproject import-linter block
**Tracked-source gate:** all named analogs are under tracked trees (`git ls-files` listing of `src`, `bench`, `tests`, `.github`); no `.gsd/capabilities` mirror paths used
**RESEARCH.md was not re-read** by this mapper; line numbers for `app.py` beyond 30-130 are from grep hits and should be confirmed by the planner
**Pattern extraction date:** 2026-10-10
