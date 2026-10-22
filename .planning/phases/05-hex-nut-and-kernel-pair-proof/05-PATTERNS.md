# Phase 5: Hex Nut and Kernel Pair Proof - Pattern Map

**Mapped:** 2026-10-14
**Files analyzed:** 30 (new and modified)
**Analogs found:** 28 / 30 (two have no code analog: the numeric end-cut oracle and the ISO 965-2 limits rows have only partial ones)

All analog paths below were checked as git-tracked (`git ls-files`). Line numbers are from the tree at `b5d5577`. RESEARCH.md "Codebase Map" (l.385-428) already lists the break points in existing tests; this file does not repeat them, it gives the code to copy.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/screw/params.py` (+`NutParams`, required-field helper, `KINDS`) | model | request-response | `src/screw/params.py` `BoltParams` | exact |
| `src/screw/calc/thread.py` (+`nut_closed_volume`, `nut_too_thin_refusal`, clearance-aware root radius, end-cut oracles) | utility (pure maths) | transform | `src/screw/calc/thread.py` `bolt_closed_volume`, `head_too_small_refusal`, `root_radius_refusal`; `bench/thread_spike/maths.py` `interference_area` | exact / partial (oracle) |
| `src/screw/calc/__init__.py` (+`_nut`, `counterpart`, groups, `derive` / `download_refusal` / `_EXPLICIT_CONFLICTS` branches, new `STANDING_WARNING`) | service | transform | `src/screw/calc/__init__.py` `_bolt` | exact |
| `src/screw/calc/pair.py` (kernel-free verdict rule) | utility | transform | `bench/thread_spike/verdict.py` `cell_verdict`, `closed_control`, `PAIR_BAND`, `EMPTY_MM3` | exact (move) |
| `src/screw/calc/presets.py` (per-kind dispatch, nut axes) | service | transform | itself (`catalogue_document`, `expand`, `match`) | exact |
| `src/screw/tables/iso4032.py` | model (cited data) | batch | `src/screw/tables/iso4017.py` | exact |
| `src/screw/tables/iso724.py` | model (cited data) | batch | `src/screw/tables/iso4017.py` / `iso262.py` | role-match |
| `src/screw/tables/iso965_2.py` | model (cited data) | batch | `src/screw/tables/iso4014.py` (per-size record with relation tests) | role-match |
| `src/screw/tables/rows.py` (+`HexNut`, ISO 724 row, ISO 965-2 row) | model | batch | `HexHead`, `ThreadBand` in same file | exact |
| `src/screw/tables/presets.py` (nut catalogue/expand) | service | transform | itself (`catalogue`, `_row`, `expand`) | exact |
| `src/screw/solid/nut.py` | service (kernel builder) | transform | `src/screw/solid/bolt.py` `assemble` + `bench/thread_spike/pair.py` `nut` | exact |
| `src/screw/solid/bolt.py` (tip cone, fillet ring) | service | transform | itself (`thread`, `assemble`, `_solid`) | exact |
| `src/screw/solid/__init__.py` (`_build` dispatch, `TESSELLATION`, `BuildError` wording, file name) | service | transform | itself (`_build`, `check_solid`) | exact |
| `src/screw/solid/pair.py` | service (kernel) | request-response | `bench/thread_spike/pair.py` | exact (move) |
| `src/screw/app.py` (`NutModelQuery`, `nut_info`, `nut_model`, `_serve` file name) | route | request-response | `app.py` `bolt_info` / `bolt_model` | exact |
| `src/screw/cli.py` (`pair` subcommand, required-field help, `os._exit`) | controller | request-response | `cli.py` `cmd_export`, `_add_args`, `main` loops | exact |
| `src/screw/static/app.js`, `index.html` (counterpart link) | component | request-response | `app.js` `renderInfo` / `navigate` (generic readers) | role-match |
| `pyproject.toml` (contract 9, `addopts`, marker) | config | n/a | existing `[[tool.importlinter.contracts]]` blocks, l.145-255 | exact |
| `Makefile` (`pair` target) | config | batch | `Makefile` `grid` target l.111-113 | exact |
| `.github/workflows/pair.yml` | config | batch | `.github/workflows/grid.yml` | exact |
| `tests/test_pair.py` | test | batch | `tests/test_grid.py` | exact |
| `tests/test_import_boundaries.py` (contract 9 probe) | test | request-response | same file | exact |
| `tests/test_tables.py`, `tests/test_tables_second_entry.py`, `tests/data/owner/{iso4032,iso724,iso965_2}.tsv` | test / data | batch | same files, Phase 4 rows | exact |
| `tests/test_parity.py`, `test_api.py`, `test_calc.py`, `test_presets.py`, `test_cli.py`, `test_params.py`, `test_solid.py` | test | request-response | themselves (break list at RESEARCH l.411-428) | exact |
| `tests/data/pair_expected.tsv` + deriving script | test data | batch | `bench/results/thread-spike/2026-10-08-a-pair.jsonl` + `verdict.parse_pair_result_row` | partial |
| `bench/thread_spike/pair.py`, `verdict.py`, `maths.py` (import moved code back) | utility | transform | `bench/thread_spike/helical.py` (re-export of `screw.solid.helical`) | exact |
| `bench/RESULTS.md`, `bench/<probe>.py` (end-cut probe, M18 probe) | utility | batch | `bench/head_fuse.py` (D-03 probe pattern) | role-match |
| `.planning/phases/05-*/05-OWNER-READS.md` | doc | n/a | `.planning/phases/04-iso-hex-bolts-and-screws/04-OWNER-READS.md` | exact |
| `.planning/phases/05-*/05-M18-DIAGNOSIS.md` | doc | n/a | `.planning/phases/02-thread-spike/02-SPIKE.md` shape | role-match |
| `docs/architecture/decision_log.md` (L14), `overview.md` | doc | n/a | L11/L13 entries | exact |
| numeric end-cut oracle in `calc/thread.py` | utility | transform | none in `src/` (spike recipe only) | no analog in src |

## Pattern Assignments

### `src/screw/params.py` : `NutParams` (model, request-response)

**Analog:** `src/screw/params.py` `BoltParams` (l.~85-150).

**Field helper to copy and where it must differ.** `_f` (l.38-47) requires `gt` and a default. The required `clearance` needs a sibling with no default, no `gt`, same `allow_inf_nan=False`:
```python
def _f[T](default: T, *, gt: float, le: float | None = None, title: str, group: str,
          unit: str = "", step: float | None = None, help: str = "") -> T:
    extra: JsonDict = {"group": group, "unit": unit}
    if step is not None:
        extra["step"] = step
    return Field(default, gt=gt, le=le, allow_inf_nan=False, title=title, description=help,
                 json_schema_extra=extra)
```
RESEARCH E1/F6 verified `Field(..., le=INTERIM_MAX_MM, allow_inf_nan=False, title=, description=, json_schema_extra={"group": "Pair", "unit": "mm"})` gives `422 missing`, no `default` key in the schema, `required: ["clearance"]`.

**Per-kind field declaration** (copy shape from `BoltParams.s`, l.~100): `s` is re-declared on `NutParams` with title `Across flats`, group `Nut`, its own frozen default (ISO 4032 M6 row), and a comment citing the row test like the bolt's D-07 comment:
```python
s: float = _f(10.0, gt=0, le=INTERIM_MAX_MM, title="Across flats", group="Head", unit="mm",
              step=0.1, help="Width across flats of the hexagon head (ISO symbol s).")
```

**Validator pattern (lazy import of calc, `PydanticCustomError` naming fields)**, overriding by the same method name `_root_radius` (RESEARCH F6: replaces the inherited rule); copy from l.77-85 and l.130-137:
```python
@model_validator(mode="after")
def _head_too_small(self) -> Self:
    from screw.calc.thread import head_too_small_refusal
    if (msg := head_too_small_refusal(self.s, self.d)) is not None:
        raise PydanticCustomError("head_too_small", msg, {"fields": ["s", "d"]})
    return self
```
`_nut_too_thin` (`s <= d + 2c`, ctx fields `["s","d","clearance"]`) and `_turn_cap` on the void length `m + 2*pitch` (copy `BoltParams._turn_cap`, l.~118-128) follow this exactly. Registry: `KINDS: dict[str, type[FastenerParams]] = {BoltParams.kind: BoltParams}` becomes two entries; `DEFAULT_KIND = "bolt"` unchanged (frozen).

---

### `src/screw/calc/thread.py` (utility, transform)

**Analog:** same file. Pure functions returning `str | None` refusal texts, naming fields, no braces (`root_radius_refusal` l.227-242; `head_too_small_refusal` l.127; `volume_check` l.166-180).

**Gate (keep as is, D-13):**
```python
def volume_check(measured: float, closed: float) -> str | None:
    if not (math.isfinite(closed) and closed > 0):
        return f"the closed form {closed:.6g} mm3 is not a finite positive number"
    rel = measured / closed - 1.0
    if not abs(rel) <= T_GATE:   # negated <=, NaN-safe
        return (...)
```
**Root radius with clearance:** copy `root_radius_refusal(d, pitch)` (l.227) body, `root = d / 2 - thread_depth(pitch) + clearance`, text names `d`, `pitch` and `clearance`; `_largest_accepted_pitch` may not apply with c (state `None` or recompute with c).

**Closed form to build `nut_closed_volume` on:** `closed_volume(d, pitch, length, clearance)` (l.87) and `hex_prism_volume(s, k)` (l.92, `sqrt(3)/2 * s * s * k`); `bolt_closed_volume` (l.115) is the shape for the sum: `hex_prism_volume(s, m) - closed_volume(d, pitch, m, c)` minus the stated end-cut volumes.

**End-cut oracle (no `src/` analog):** formulas and measured agreement are in RESEARCH F4 / E2; the recipe to copy is `bench/thread_spike/maths.py` `interference_area(d, pitch, clearance, phase)` (l.188) with its `INTEGRATION_POINTS`. Keep it kernel-free and logger-free (contracts 2 and 4). RESEARCH F4 trap: `arc_inside = rho * (2*pi - 12*acos(a/rho))`; test the oracle against the kernel.

---

### `src/screw/calc/__init__.py` : `_nut`, `counterpart` (service, transform)

**Analog:** `_bolt` (l.~125-250) and `derive` / `download_refusal` / `_EXPLICIT_CONFLICTS`.

**Lazy table import (contract 6) at the top of the builder:**
```python
def _bolt(p: BoltParams) -> PartInfo:
    from screw.calc.presets import designation_for, match, notes, row_values
```
**Rows as a `computed` list with formula strings, finite-guard loop, warnings for non-finite** (l.157-198) is the pattern for the `Nut` and `Pair` groups: each row a tuple `(key, group, label, unit, formula, lambda)`; `OverflowError`/`ValueError` become `math.nan` and a `... not reported` warning. Pair rows (D-19) come from `section_radius` (RESEARCH F7: `0.5c`, `2c/sqrt(3)`).

**Download state is required in every kind's info builder:**
```python
downloads = _downloads(p)
for reason in dict.fromkeys(e.refusal for e in downloads if e.refusal is not None):
    warnings.append(reason)
```
**Dispatch, copy then add a branch (raise `TypeError` otherwise):**
```python
if isinstance(p, BoltParams):
    return _bolt(p)
raise TypeError(f"no info document for kind {p.kind!r}")
```
**`_EXPLICIT_CONFLICTS`** needs `NutParams.kind: None` (a kind without an entry raises). **`PartInfo`** gains `counterpart` following the existing `Field(description=...)` style (frozen `BaseModel`, l.~99-118); RESEARCH E8 / F6: `fields: dict[str, float | bool]` round-trips `left_hand`. The pinned warnings (D-03, D-04) are f-strings in `derive` like `_thread_length_warning`.

---

### `src/screw/calc/presets.py`, `src/screw/tables/presets.py` (service, transform)

**Analog:** themselves. Hard-wired to bolt by `if KINDS.get(kind) is not BoltParams: raise TypeError(f"no preset catalogue for kind {kind!r}")` in `catalogue_document` (l.134) and `expand` (l.148); replace with a per-kind dict, keep the `TypeError` for an unknown kind.

**Row factory** (`tables/presets.py` `_row`, l.48-82): id `f"{standard.replace(' ', '').lower()}:{size.label}x{len}"` -> nut id `iso4032:M6`; bracket second-choice sizes in `display` and `picker`, never in `designation` (decimal comma):
```python
shown = f"({size.label})" if size.choice == 2 else size.label
designation=f"{noun} {standard} - {size.label.replace('.', ',')} x {shown_length}"
```
`AXES` (l.106) becomes `["Standard", "Size"]` for the nut; `PresetEntry.fields: dict[str, float]` is fine for the nut (`d, pitch, s, m`). `FIELD_NAMES` test (each key is a model field) must cover the nut tuple.

**Row values with citation labels (reuse verbatim for 6g/6H rows):** `_row_value(key, sense, value, source, group)` (l.54) labels `"{sense} ({standard}:{edition} {table})"`.

---

### `src/screw/tables/iso4032.py`, `iso724.py`, `iso965_2.py`, `rows.py` (cited data, batch)

**Analog:** `src/screw/tables/iso4017.py`.

```python
def _source(table: str, column: str) -> Source:
    return Source(standard="ISO 4017", edition="2022", table=table, column=column, status="verified")

HEADS: tuple[HexHead, ...] = (
    HexHead(size="M6", grade="A", pitch=1.0, s=10.0, ..., source=_source("Table 1", "M6")),
    HexHead(size="M3.5", ..., source=_source("Table 1", "(M3,5)")),   # printed header incl. brackets, decimal comma
```
Row dataclasses (`rows.py` l.~30-100): `@dataclass(frozen=True, slots=True, kw_only=True)`, no defaults, `source: Source` required; add `HexNut` (`size, pitch, s, s_min, e_min, m, m_min, mw_min, dw_min, informative: bool, source`), an ISO 724 row, an ISO 965-2 (size, class) row. Tables stay a leaf: import only `screw.tables.*` (contract 7). Annex A rows (M2-M4) get an explicit `informative` flag. `iso262.SIZES` is reused unchanged. `tables/__init__.py` stays empty-ish.

---

### `src/screw/solid/nut.py` (kernel builder, transform)

**Analog:** `src/screw/solid/bolt.py` for structure, `bench/thread_spike/pair.py` `nut()` for the void cut.

**Docstring/imports/`_solid` guard (copy):**
```python
import cadquery as cq
from screw.build_errors import BuildError
from screw.solid import helical

def _solid(made: object, what: str) -> cq.Solid:
    if not isinstance(made, cq.Solid):
        raise BuildError(f"Geometry kernel produced {type(made).__name__} for the {what}, expected a solid.")
    return made
```
Raise `BuildError`, never `assert` (04-REVIEW IN-01). Import `_solid` rather than re-defining if it moves; otherwise duplicate it (three similar lines beat an abstraction).

**Prism convention (across-flats):** `cq.Workplane("XY").polygon(6, p.s, circumscribed=True).extrude(p.m).val()` (bolt.py l.46-47; without `circumscribed` the prism is 0.75 of its closed form).

**Void (overshooting by one pitch each side, RESEARCH F3 / P11):**
```python
void = helical.thread(d, pitch, _span(pitch, m), clearance=clearance, left_hand=left_hand, k=k
                      ).translate(cq.Vector(0, 0, -pitch))
solids = cq.Solid.makeCylinder(d, m).cut(void).Solids()
if len(solids) != 1: raise ValueError(...)
```
Cutters (countersinks, corner chamfers) must cross, never graze, the root surface (RESEARCH F8 / E3 / P7): a cone ending exactly on `rr` leaves open STL edges that neither `isValid()` nor the volume gate sees.

---

### `src/screw/solid/bolt.py` (tip cone, fillet ring)

**Analog:** itself. `assemble` fuses the shank with a planar fuse starting on the face the thread ends in, then the head, no `clean()`:
```python
body: cq.Shape = bare_thread.fuse(shank)
...
return body.fuse(head)
```
The fillet ring is a revolved quarter-circle region fused the same way, only `if p.length - t >= r` (plain shank exists). Tip cone cut on the bare thread: `rod.intersect(revolved envelope)` (recipe in `2026-10-08-a-trim`, RESEARCH F4). Update the module docstring that now says "both thread ends are plain planar cuts".

---

### `src/screw/solid/__init__.py` (gate dispatch)

**Analog:** itself, `_build` (l.~118-130) and `check_solid` (l.~95-115).

```python
def _build(p: FastenerParams) -> cq.Solid:
    if not isinstance(p, BoltParams):
        raise TypeError(f"no solid builder for kind {p.kind!r}")
    t = built_thread_length(p.thread_length, p.length)
    bare_thread = bolt.thread(p)
    check_solid(bare_thread, closed_volume(p.d, p.pitch, t), part="thread")
    fused = bolt.assemble(p, bare_thread)
    check_solid(fused, bolt_closed_volume(...))
    return fused.Solids()[0]
```
Add a nut branch (`isinstance(p, NutParams)`) and keep the bare-thread-then-whole-part order. `_build_checked` re-raises `(BuildError, TypeError)` untouched and wraps other exceptions in a bolt-worded message ("check d, pitch, length, thread_length, s and k.") that must become kind-neutral. `TESSELLATION` (l.53) is one tuple, comment cites spur today; D-21 re-cites the ladder run id. `_write_export` already meshes `shape.copy()` with `relative=False`; keep.

---

### `src/screw/solid/pair.py` (kernel, moves from bench)

**Analog:** `bench/thread_spike/pair.py` (whole file, 103 lines). Move `_KEEP`, `_span`, `rod_piece`, `nut` (the plain-blank body: `cq.Solid.makeCylinder(d, m)` less the void), `place`, `check_cover`, `common` verbatim; bench then imports back.
```python
_KEEP: list[object] = []   # freeing the boolean segfaulted at teardown (exit 139)

def common(a, b) -> tuple[float, int, bool, bool, float]:
    op = BRepAlgoAPI_Common()
    first, second = TopTools_ListOfShape(), TopTools_ListOfShape()
    first.Append(a.wrapped); second.Append(b.wrapped)
    op.SetArguments(first); op.SetTools(second); op.Build()
    filler = op.DSFiller()
    _KEEP.append((op, filler))
```
Replace `from bench.thread_spike import helical, measure` with `from screw.solid import helical` and `precise_volume` from `screw.solid`. `prove(p: NutParams) -> PairReport` returns a frozen pydantic document; no `cq` type escapes. Add a rod-hand parameter (RESEARCH P3: `prove(NutParams)` cannot express the mixed-hand cell, which the grid builds from the bodies directly).

**Back-import pattern in bench** (`bench/thread_spike/helical.py` is the existing precedent): `from screw.solid.helical import thread as thread`.

---

### `src/screw/calc/pair.py` (kernel-free verdict rule)

**Analog:** `bench/thread_spike/verdict.py` `cell_verdict` (l.1585), `closed_control` (l.1535), `PAIR_BAND = 1e-3` (l.1340), `EMPTY_MM3 = 1e-6` (l.1343); `bench/thread_spike/maths.py` `MATCHED_POSES` (l.179), `interference_area` (l.188). Move the rule unchanged (owner ruling R1); bench imports it back. Contract "spike's oracle, verdict and parent process stay free of the CAD kernel" (pyproject l.216) must still hold after the move: `calc.pair` has no kernel import so the verdict module may import it.

---

### `src/screw/app.py` (route, request-response)

**Analog:** `bolt_info` / `bolt_model` (l.436-450) and `BoltModelQuery` / `strip` (l.276-290).
```python
class BoltModelQuery(BoltParams, _Quality): ...

@app.get("/api/bolt/info", dependencies=[Depends(refuse_explicit_conflict(BoltParams.kind))])
def bolt_info(q: Annotated[BoltParams, Query()]) -> PartInfo:
    return derive(q)

@app.get("/api/bolt/model.{fmt}", response_class=Response,
         responses={200: {"content": {t: {} for t in MEDIA_TYPES.values()}}},
         dependencies=[Depends(refuse_explicit_conflict(BoltParams.kind))])
async def bolt_model(fmt, q: Annotated[BoltModelQuery, Query()], request, backend: Annotated[BuildBackend, Depends(build_backend)]) -> Response:
    return await _serve(strip(q, BoltParams), fmt, q.quality, request, backend)
```
Copy for nut with `NutParams`; `strip` rebuilds the plain class (cache key). `app.py` must not import `screw.solid.pair` (contract 9). File name rule (D-22) edits l.568: `filename="{params.slug()}.{fmt}"` becomes `<slug>_preview.stl` for `quality == "preview"` and `fmt == "stl"`; put the rule in one shared function used by `cmd_export` too (the CLI export names the file the user gave, so the parity test pins the shared name function, not the `-o` path).

---

### `src/screw/cli.py` (controller, request-response)

**Analog:** `cmd_export` (l.~140-170), `_add_args` (l.~55-80), `main` subparser loop (l.~190-225).

**Flag generation** (`help_text = f"{field.description} [{field.default}]"`) prints `PydanticUndefined` for a required field: branch on `field.is_required()` (RESEARCH F6) and print `required` instead.

**Subparser family** (copy the `ik`/`ek` loop for a `pair` family over kinds that carry `clearance`):
```python
e = sub.add_parser("export", ...)
ek = e.add_subparsers(dest="kind", required=True)
e.set_defaults(func=cmd_export)
for kind, model in KINDS.items():
    kp = ek.add_parser(kind, allow_abbrev=False)
    ...
    _add_args(kp, kind, model)
```
`allow_abbrev=False` on every parser; `_params(kind, ns)` builds the model and exits 2 with `error: field: msg` on `ValidationError`. **Lazy kernel import after refusals** (`from .solid import ...` inside the command). `cmd_pair` ends `sys.stdout.flush(); sys.stderr.flush(); os._exit(code)` (RESEARCH P1/E4: normal exit after `common()` is 139). Never call `cli.main(["pair", ...])` in the pytest process.

---

### `.github/workflows/pair.yml`, `Makefile`, `pyproject.toml`

**Analog:** `.github/workflows/grid.yml` (whole file), `Makefile` l.111-113:
```make
grid: $(STAMP)  ## ...
	$(PY) -m pytest -m grid -n $(PYTEST_WORKERS) --no-cov $(if $(SIZE),-k '$(SIZE)-',) $(PYTEST_ARGS)
```
`pair.yml`: `on: workflow_dispatch` + `schedule` only, `permissions:\n  contents: read`, matrix `size: [M2, ... M20]`, `run: make pair PYTHON=python SIZE=${{ matrix.size }}`, kernel-pair print step, no `secrets.`. Add `pair` to `.PHONY` (Makefile l.32) and `-m 'not grid and not pair'` to `addopts` (update `tests/test_grid.py` l.90 literal).

**Contract 9** copy shape of the "serving process never imports the CAD kernel" block (pyproject l.187-197): `type = "forbidden"`, `source_modules = ["screw.app", "screw.pool"]`, `forbidden_modules = ["screw.solid.pair"]`, `allow_indirect_imports = false`. Note pool reaches the kernel by runtime `importlib.import_module("screw.solid")`, so add the `sys.modules` probe.

---

### `tests/test_pair.py` (test, batch)

**Analog:** `tests/test_grid.py`. Pattern: unmarked tests run in `make verify` and read no kernel; `@pytest.mark.pair` + `parametrize(..., ids=IDS)` for the grid; ids `f"{size}-{hand}-..."` so `-k 'M3-'` selects one size (and `test_a_size_selects_exactly_its_cells_by_id` guards it); workflow-shape tests:
```python
assert not re.search(r"^\s*(pull_request|pull_request_target|push)\s*:", text, re.MULTILINE)
assert re.search(r"^permissions:\n  contents: read$", text, re.MULTILINE)
assert "secrets." not in text
```
`assert "grid" not in ci` also must hold for `pair` (keep `ci.yml` free of the word). The verify cell runs in a child process (`subprocess.run([sys.executable, ...])`); do not assert a spawn child's `exitcode == 0` (RESEARCH F5). Expected table: derive with the unmodified `cell_verdict` over `2026-10-08-a-pair.jsonl` (RESEARCH P15) and re-derive in a verify test.

### `tests/test_import_boundaries.py`

**Analog:** same file, the fresh-interpreter probe:
```python
subprocess.run([sys.executable, "-I", "-c", f"import sys; {code}; print('screw.tables' in sys.modules)"], capture_output=True, text=True, check=True)
```
Add a sibling `_loads(module, code)` for `'screw.solid.pair' in sys.modules` after `import screw.app` / `import screw.pool` (False), with a positive control importing `screw.solid.pair` (True), as `test_the_probe_sees_the_tables_once_they_are_imported` does.

### `tests/test_tables.py`, `tests/test_tables_second_entry.py`, owner TSVs

**Analog:** same files. Add `_SHAPE` entries (`"iso4032.tsv": (("size",), (...numbers...))`, ...), extend `shipped()` and the non-vacuous row counts; one relation test per row in the style of `test_row_relations` (`head.s_min < head.s`, `head.dw_min < head.s_min`, pitch equals ISO 262's `PITCH[row.size]`); a frozen-default row test for `NutParams()` `s`/`m` (pattern: `test_the_frozen_defaults_are_the_iso_4017_m6_row_the_owner_confirmed`). The TSV generator lives outside the repo (RESEARCH l.474).

### `tests/test_parity.py`

**Analog:** itself (738 lines). Break points listed at RESEARCH l.414. Learn the required field by a positive rule (a field with `is_required()` must be omitted from default loops and must make the no-flag call exit 2), not by loosening checks; `HAND_WRITTEN` (l.47) and `PINNED_STATEMENTS` (l.394) take the new pinned strings; the `info.(\w+)` source assertion (l.615) gains `counterpart`.

### `.planning/phases/05-*/05-OWNER-READS.md`

**Analog:** `.planning/phases/04-iso-hex-bolts-and-screws/04-OWNER-READS.md` (record shape, `permanent: accepted` marks).

---

## Shared Patterns

### Cross-field refusal naming fields
**Source:** `src/screw/params.py` l.77-85, 130-137. **Apply to:** `NutParams` validators.
`raise PydanticCustomError(<type>, msg, {"fields": [...]})` with the refusal text produced by a pure function in `calc/thread.py` and imported lazily inside the validator (circular import, contract 6).

### Kernel-free calc, tables lazily imported
**Source:** `src/screw/calc/__init__.py` `_bolt` (import inside function), `tests/test_import_boundaries.py`. **Apply to:** `_nut`, `counterpart`, `calc/pair.py`. `params` and `calc.thread` never reach `screw.tables`; `calc/` imports no `cadquery`, `OCP`, `logging`, `records`.

### Build errors, not asserts
**Source:** `src/screw/solid/bolt.py` `_solid`, `src/screw/solid/__init__.py` `check_solid`. **Apply to:** `solid/nut.py`, fillet ring, `solid/pair.py`. Raise `BuildError`; `python -O` strips asserts.

### Gate shape
**Source:** `src/screw/solid/__init__.py` `check_solid(shape, closed, part=...)`, called inside the function `lru_cache` wraps. **Apply to:** nut build, chamfered bare thread, fillet.

### Every measured constant cites its run id; every INTERIM names Phase 7
**Source:** comments at `params.py` l.19-33, `solid/__init__.py` TESSELLATION, `calc/thread.py` fine-STL caps. **Apply to:** `TESSELLATION["fine"]`, `PAIR_BAND`, deflection test.

### Tracked-source rule
The only `.gsd/capabilities` style mirrors are not involved in this repo; all analogs above were verified with `git ls-files`.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| numeric end-cut oracle (tip cone, countersink, hex-corner chamfer) in `calc/thread.py` | utility | transform | `src/` has only closed forms; the integral recipe exists only in `bench/thread_spike/maths.py` `interference_area` and RESEARCH F4/E2 |
| `tests/data/pair_expected.tsv` deriving script | script | batch | no script in the repo derives expectations from a `.jsonl`; use `verdict.parse_pair_result_row` + `cell_verdict` (RESEARCH P15) |

## Metadata

**Analog search scope:** `src/screw/**`, `tests/`, `bench/thread_spike/`, `.github/workflows/`, `Makefile`, `pyproject.toml`, `.planning/phases/04-*`.
**Files scanned:** about 25 read in full or by range.
**Pattern extraction date:** 2026-10-14
