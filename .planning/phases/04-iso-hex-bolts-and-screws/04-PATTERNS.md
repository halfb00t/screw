# Phase 4: ISO Hex Bolts and Screws - Pattern Map

**Mapped:** 2026-10-11
**Files analyzed:** 27 (11 new, 16 modified; docs and debt grouped)
**Analogs found:** 27 / 27 for structure; 3 new subsystems have only a partial analog (see "No Analog Found")
**Tracked-source gate (#3645):** every analog below is git-tracked under `src/`, `tests/`, `bench/`, `.github/`, `pyproject.toml`. No `.gsd/capabilities` mirror path is named.

Line numbers are for the working tree at branch `gsd/phase-04-iso-hex-bolts-and-screws`. The planner must read 04-RESEARCH.md "Planner Alerts" 1 to 7 before fixing any of the mechanisms below. Where an alert changes the mechanism, the pattern here follows the RESEARCH recommendation and says so.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|
| `src/screw/params.py` (mod: `s`, `k`, `thread_length`, `head_too_small`, turn cap on `t`) | model | validation | itself (`_f`, `_root_radius`, `_turn_cap`) | exact |
| `src/screw/calc/thread.py` (mod: `built_thread_length`, hex/bolt closed form, `thread_length_conflict`, re-keyed `FINE_STL_ROWS`, `head_too_small_refusal`) | utility | transform | itself (`turn_cap_refusal`, `fine_stl_refusal`, `closed_volume`) | exact |
| `src/screw/calc/__init__.py` (mod: `InfoRow.group`, `PartInfo` keys, `_bolt` groups/designation/notes) | service | transform | itself (`_bolt`, `computed` loop) | exact |
| `src/screw/calc/presets.py` (new: catalogue document, `match`) | service | request-response | `src/screw/calc/__init__.py` (`PartInfo`/`InfoRow` frozen pydantic documents) + `app.py` `KindsReport` | role-match |
| `src/screw/tables/__init__.py` (new, docstring only) | config | n/a | `src/screw/calc/__init__.py` docstring (L1-7) | role-match |
| `src/screw/tables/source.py` (new: `Source`) | model | n/a | `src/screw/params.py` `FastenerParams` (frozen, typed, required fields) | partial |
| `src/screw/tables/iso262.py`, `iso4014.py`, `iso4017.py` (new: typed rows) | model (data) | n/a | `FINE_STL_ROWS` in `calc/thread.py` L170-190 (typed dict, cited, run-id comment) | partial |
| `src/screw/tables/presets.py` (new: `expand`, `catalogue`, `PresetRow`) | utility | transform | `calc.thread.fine_stl_refusal` ("one function, two callers") | role-match |
| `src/screw/solid/bolt.py` (mod: `rod` becomes bolt assembly) | service | transform | itself (`rod`) + `solid/helical.py` `thread` | exact |
| `src/screw/solid/__init__.py` (mod: `_build`, optional bare-thread gate) | service | request-response | itself (`_build`, `check_solid`) | exact |
| `src/screw/app.py` (mod: `/api/presets`, conflict dependency, comment reword) | controller | request-response | itself (`schema`, `refuse_repeated_keys`, `KindsReport`, `_serve`) | exact |
| `src/screw/cli.py` (mod: `--preset`, `presets` subcommand) | controller | request-response | itself (`_add_args`, `_Once`, `_params`, `cmd_info`) | exact |
| `src/screw/static/app.js` (mod: picker, badge, groups, notes, `String(row.value)`) | component | event-driven | itself (`buildForm`, `renderInfo`, `showMessages`, `partQuery`) | exact |
| `src/screw/static/index.html`, `style.css` (mod) | component | n/a | themselves (`aside`, `#dims`, `#messages`) | exact |
| `pyproject.toml` (mod: contracts 2, 6, 7) | config | n/a | itself `[tool.importlinter]` L145-230 | exact |
| `tests/test_tables.py` (new) | test | batch (parametrised) | `tests/test_thread_maths.py` L207-233 (`L11_ROWS` parametrised) | role-match |
| `tests/test_tables_second_entry.py` + `tests/data/` (new) | test | batch | `tests/test_thread_maths.py` (typed-from-source table vs code) | partial |
| `tests/test_presets.py` (new) | test | request-response | `tests/test_parity.py` (`cli.main` + TestClient on both fronts) | role-match |
| `tests/test_import_boundaries.py` (new, subprocess `sys.modules`) | test | n/a | none in repo; see No Analog | none |
| `tests/test_{params,calc,api,cli,solid,parity,thread_maths,bench}.py` (mod) | test | mixed | themselves | exact |
| `bench/corpus.py`, `bench/RESULTS.md` (mod: pin `s`,`k`,`thread_length`; probe entry) | config / doc | n/a | themselves | exact |
| `.gitignore` (mod: `*.pdf`, local standards dir) | config | n/a | itself | exact |
| `docs/architecture/{decision_log,overview}.md` (mod: L13, L12 Caps reword, `tables` row) | doc | n/a | L12 entry | exact |
| `docs/tech_debt/**` (resolve 2, amend 3) | doc | n/a | `docs/tech_debt/TEMPLATE.md`, `INDEX.md` | exact |
| `.planning/{REQUIREMENTS,ROADMAP,STATE}.md`, `01-UI-SPEC.md` (amend) | doc | n/a | themselves | exact |
| `README.md` (mod: status paragraph, optional presets example) | doc | n/a | itself; note `tests/test_cli.py` L236-251 runs every `.venv/bin/screw` line | exact |

## Pattern Assignments

### `src/screw/params.py` (model, validation)

**Analog:** itself.

**New field pattern** (copy `_f` call shape, `params.py` L104-105; helper at L34-43):
```python
length: float = _f(20.0, gt=0, le=INTERIM_MAX_MM, title="Length", group="Size", unit="mm",
                   step=0.5, help="Length of the threaded rod along its axis.")
```
`s`, `k`, `thread_length` are three more `_f(default, gt=0, le=INTERIM_MAX_MM, title="Across flats" | "Head height" | "Thread length", group=..., unit="mm", step=...)` on `BoltParams` (D-05, D-06, D-23). Defaults are committed only after the owner checkpoint (D-07). Group names decide the form fieldsets, so choose them with the info groups in mind (`Size`, `Head`, `Thread`).

**Cross-field rule pattern** (`params.py` L78-87 and L107-114): lazy import from `screw.calc.thread` inside an `after` validator, `PydanticCustomError(code, msg, {"fields": [...]})`, message starts with the field names because the CLI prints no `loc`.
```python
@model_validator(mode="after")
def _turn_cap(self) -> Self:
    from screw.calc.thread import turn_cap_refusal
    if (msg := turn_cap_refusal(self.length, self.pitch)) is not None:
        raise PydanticCustomError("turn_cap", msg, {"fields": ["length", "pitch"]})
    return self
```
Apply to: `head_too_small` (`{"fields": ["s", "d"]}`, rule in `calc/thread.py`), and `_turn_cap` re-pointed at `built_thread_length(self.thread_length, self.length)` with `{"fields": ["thread_length", "length", "pitch"]}` (D-22).

**Deviation from CONTEXT (Alert 1):** do NOT use `self.model_fields_set` in a validator. FastAPI 0.142.2 marks every field "set" on the query model and `strip()` (`app.py` L249-256) rebuilds with all fields. The explicit-conflict 422 lives in an API dependency and in CLI `_params`, both calling `thread_length_conflict`. The model only derives `t = min(...)`.

**Slug:** `slug()` (L89-96) iterates `model_fields` with `%g`; new fields enter it automatically, `tests/test_params.py` slug assertion changes.

**Frozen-default comment pattern** (L64-67): the `ASSUMPTION (D-05)` block is replaced by a comment citing the row test that asserts `(d, pitch, s, k, length, thread_length)` equals the ISO 4017 M6 x 20 row.

---

### `src/screw/calc/thread.py` (utility, transform)

**Analog:** itself. Kernel-free, imports only `math`, `Decimal`, `Fraction` (L14-16). Contracts 2 and 4 forbid `cadquery`, `OCP`, `logging`, `screw.records`. After contract 6 it must not import `screw.tables` either, even indirectly.

**Closed form to extend** (L79-81):
```python
def closed_volume(d: float, pitch: float, length: float, clearance: float = 0.0) -> float:
    return section_area(d, pitch, clearance) * length
```
Add `bolt_closed_volume(d, pitch, length, s, k, t)` = `section_area(d, pitch) * t + math.pi * (d / 2) ** 2 * (length - t) + math.sqrt(3) / 2 * s * s * k` (RESEARCH Code Example 2), and `built_thread_length(thread_length, length) = min(...)` (RESEARCH Pattern 2; Alert 6 fold rule below `MIN_TAIL_MM` is an open owner question).

**Refusal-function pattern** (L162-167 and L145-159): return `None` or a text that starts with the field names, contains no braces (pydantic formats custom errors from context), exact-decimal arithmetic through `_exact`.
```python
def turn_cap_refusal(length: float, pitch: float) -> str | None:
    if _exact(length) <= MAX_TURNS * _exact(pitch):
        return None
    return (f"length and pitch: {turns_of(length, pitch):g} turns is past the {MAX_TURNS}-turn "
            f"cap, the most measured (run 2026-10-08-a-frontier); shorten length or raise pitch")
```
Apply to: `thread_length_conflict(length, thread_length)` (RESEARCH Code Example 4), `head_too_small_refusal(s, d)` (text must say `s` must be above `d`, Alert 4), and `turn_cap_refusal` taking `t`.

**Re-keyed cap table** (L170-205). Keep the comment style (run id, "first row over budget", INTERIM, Phase 7 re-sweeps):
```python
FINE_STL_ROWS: dict[tuple[float, float], float] = {
    (8.0, 1.25): 67.5,    # first row over budget: M8 right L=68 rod
    ...
}
cap = FINE_STL_ROWS.get((d, pitch))
if cap is None or length <= cap:
    return None
```
Becomes `dict[tuple[float, float, bool], float]` with the RESEARCH Code Example 7 values. **Alert 2:** left-hand caps are 72, 77, 78, 75, 91, 91 (largest fitting length), not the debt item's 73/78/79/76/92/92 (first over). The refusal text is reworded to "the fine STL plus its gzip copy exceeded the 64 MiB export budget" and names `thread_length`. `tests/test_thread_maths.py` L207-233 (`L11_ROWS`, "each cap accepted, next float above refused") is the test pattern to widen to 13 rows, keeping the independently typed table.

---

### `src/screw/calc/__init__.py` (service, transform)

**Analog:** itself.

**Document model pattern** (L27-45): frozen pydantic models, `InfoRow(key, label, value: float, unit)`. Add `group: str` to `InfoRow`; add `designation: str | None`, `preset: PresetMatch | None`, `notes: list[str]` to `PartInfo` (D-17).

**Finite-or-warned loop** (L60-79) is the pattern for every new numeric row (shank length, geometric across-corners `s / cos 30 deg`, whole-bolt volume):
```python
computed: list[tuple[str, str, str, str, Callable[[], float]]] = [
    ("turns", "Turns", "", "length / pitch", lambda: turns_of(p.length, p.pitch)),
    ...
]
for key, label, unit, formula, compute in computed:
    try:
        value = compute()
    except (OverflowError, ValueError):
        value = math.nan
    if math.isfinite(value):
        rows.append(InfoRow(key=key, label=label, value=value, unit=unit))
    else:
        warnings.append(f"{key} not reported: {formula} is not a finite number for these parameters")
```
Extend the tuple with a group element (or build rows per group). `turns` uses `built_thread_length`.

**Warnings order:** `STANDING_WARNING` first (L24 constant, rewritten verbatim per D-04), then the `thread_length` default warning, the no-row warning, then `fine_stl_refusal` (L82-84, now with `left_hand` and `t`). `tests/test_calc.py` L124-136 pin this order; update, do not loosen.

**Lazy table import (Alert 3):** `calc/__init__.py` must NOT import `screw.calc.presets` or `screw.tables` at top level. Import inside `_bolt` so `BoltParams()` leaves `screw.tables` out of `sys.modules`. Also keep `derive`'s `isinstance` dispatch (L88-98) and `download_refusal` (L101-114) shape: one function, two callers (`app._serve`, `cli.cmd_export`).

---

### `src/screw/calc/presets.py` (service, request-response) — new

**Analog:** pydantic response-model style in `app.py` L361-367 and `calc/__init__.py` L27-45.
```python
class KindsReport(BaseModel):
    """..."""
    model_config = ConfigDict(frozen=True)
    default: str = Field(description="The kind a link that omits `kind` means (L02).")
    kinds: list[str] = Field(description="Every registered kind.")
```
Copy: frozen `ConfigDict`, `Field(description=...)` on every key (the OpenAPI contract is pinned by `tests/test_api.py::test_openapi_documents_the_typed_contracts`). Defines `PresetMatch` (`status: Literal["exact","custom"]`, `id`, `display`), the `PresetCatalogue` document (RESEARCH Pattern 5: `axes`, per-row `choice`, `fields`, `id`, `display`, `designation`, `citation`) and `match(fields)`. Imports `screw.tables` at top level; this module is only reached lazily from `derive` and directly from `app`/`cli`. Match is exact float equality over the fields a row defines, 4017 reported before 4014 (Pattern 4, pinned by a test).

---

### `src/screw/tables/*` (data, leaf) — new

**Contract 7 (leaf):** stdlib only; no `screw.params`, `screw.calc`, `screw.solid`, `screw.app`, `screw.cli`, `cadquery`, `OCP`, `fastapi`, `logging`. `tables/__init__.py` is a docstring only (carries the D-16 licence stance), no imports of its modules.

**Analog for typed, cited constants:** `FINE_STL_ROWS` and its comment (`calc/thread.py` L170-190): a typed dict, every entry carries its provenance, the comment states what the values are NOT ("not ISO rows"). Mirror this discipline with a required `Source(standard, edition, table, column, status)` frozen dataclass (no defaults, so a row without one fails mypy `--strict`, TABL-02). `from __future__ import annotations` and `@dataclass(frozen=True, slots=True)` follow the repo style (mypy strict, no `Any`, L04).

**Row identity:** `(standard, size, grade)` not size alone (RESEARCH Pitfall 6); store the printed `ls,min`/`lg,max` cells for 4014 (Pitfall 5); do not store tolerance columns (Pitfall 10); both entry copies are per-size records, not the printed layout (D-16).

**`tables/presets.py`:** plain frozen dataclass `PresetRow` (id, standard, size label, length, `fields: tuple[tuple[str, float], ...]`, citation); `expand(id)` and `catalogue(kind)`. Field-name keys are strings; a test asserts every key is a `BoltParams` field. Id grammar `iso4017:M6x20` (D-11). Unknown id: `KeyError`/`None`, never `eval`/path.

---

### `src/screw/solid/bolt.py` (service, transform)

**Analog:** itself plus `solid/helical.py`. Current (L15-18):
```python
def rod(p: BoltParams) -> cq.Solid:
    return helical.thread(p.d, p.pitch, p.length, left_hand=p.left_hand)
```
Imports (L7-12): `import cadquery as cq`, `from screw.params import BoltParams`, `from screw.solid import helical`. Replace `rod` with the assembly from RESEARCH Code Examples 1-2: thread over `t` from z=0, shank cylinder `t..length`, head `polygon(6, s, circumscribed=True).extrude(k)` at `length`, `Shape.fuse` (no `clean=`; Pitfall 2), `assert isinstance(solid, cq.Solid)` narrowing as `helical.section` does for `Wire`. Pitfall 1: `circumscribed=True` or the gate refuses every bolt at volume ratio 0.75. No `cadquery` object leaves `screw.solid` (contract 8).

### `src/screw/solid/__init__.py` (service, request-response)

**Analog:** itself, `_build` L115-122:
```python
def _build(p: FastenerParams) -> cq.Solid:
    if isinstance(p, BoltParams):
        solid = bolt.rod(p)
        closed = closed_volume(p.d, p.pitch, p.length)
    else:
        raise TypeError(f"no solid builder for kind {p.kind!r}")
    check_solid(solid, closed)
    return solid
```
Swap in `bolt.assemble(p)` and `bolt_closed_volume(...)`. Alert 5 recommends an extra `check_solid(thread, closed_volume(d, pitch, t))` on the bare thread before the fuse (owner/planner decision). `_build_checked` generic failure text (L132-134, `"check d, pitch and length."`) should name `thread_length`, `s`, `k` too. Keep `lru_cache` wrapping `_build_checked` so a gate refusal is never cached. Existing test imports `check_solid` for known-bad controls (`tests/test_solid.py`); keep the positive controls.

---

### `src/screw/app.py` (controller, request-response)

**`GET /api/presets?kind=` — analog `schema()` L375-386** (copy the 404 shape exactly):
```python
@app.get("/api/schema")
def schema(kind: str) -> JsonSchemaValue:
    model = KINDS.get(kind)
    if model is None:
        raise HTTPException(404, detail=[{
            "loc": ["query", "kind"], "type": "unknown_kind",
            "msg": f"Unknown kind {kind!r}. Known kinds: {', '.join(KINDS)}."}])
    return model.model_json_schema()
```
Return a typed response model like `KindsReport` (L361-371). The handler imports the catalogue from `screw.calc.presets`, never `solid`, so contract 5 (app never reaches the kernel, indirect disallowed) holds.

**Conflict dependency — analog `refuse_repeated_keys` L173-190**, registered at L194-199 in `dependencies=[Depends(...)]`:
```python
def refuse_repeated_keys(request: Request) -> None:
    ...
    raise HTTPException(422, detail=[
        {"loc": ["query", key], "type": "duplicate", "msg": f"..."} for key in repeated])
```
New `refuse_thread_length_conflict(request)` (RESEARCH Code Example 4) goes next to it; it must run after the repeat check, and its detail carries `"ctx": {"fields": ["thread_length", "length"]}` because `problems()` in `app.js` (L217-232) marks controls from `ctx.fields`.

**Refusal call site L403-414** (`download_refusal` before cache/slot/pool, `type: "fine_stl_cap"`) is unchanged except the comment about D-02 is reworded (D-21: "fine STL plus its gzip copy exceeded the 64 MiB export budget"). `strip()` L249-256 stays untouched (RESEARCH Example 6: do not add `exclude_unset`).

---

### `src/screw/cli.py` (controller, request-response)

**`--preset` — analog `_add_args` + `_Once` + `_params`** (L35-84).

Hand-added flag precedent (L175-181) uses `action=_Once`, `default=None`:
```python
kp.add_argument("--quality", choices=["preview", "fine"], default=None, action=_Once,
                help="STL tessellation [fine]")
```
Add `--preset` the same way to the `info` and `export` kind parsers. Expansion goes in `_params` before the dict is built (L74-84); explicit non-`None` flags override; the merged values go through `thread_length_conflict`, exit 2 like the ValidationError branch:
```python
values = {k: v for k in model.model_fields if (v := getattr(ns, k)) is not None}
try:
    return model(**values)
except ValidationError as exc:
    ...
    raise SystemExit(2) from None
```
Unknown preset id: `print("error: ...", file=sys.stderr)`, `raise SystemExit(2)`. `screw presets <kind>`: a new `sub.add_parser("presets", allow_abbrev=False)` with a kind sub-subparser, mirroring `info`/`export` (L162-168). Lazy-import `.calc.presets`/`tables` inside the command functions like `cmd_info` does for `derive` (L106). Contract 3 forbids `cli` importing `screw.app`; the catalogue builder therefore lives in `calc/presets.py`. Every parser keeps `allow_abbrev=False`.

---

### `src/screw/static/app.js` (component, event-driven)

**Rule:** reads no field, row or group name (`tests/test_parity.py::_field_literals` flags quoted literals and `info|prop|values|h|q|defaults|properties` property reads). Keys the new document introduces (`designation`, `preset`, `notes`, `group`) are document keys, not field names, but add them to the parity test's allow-list deliberately.

**Groups for the info panel — copy the form's fieldset grouping** (`buildForm` L68-79):
```js
const group = prop.group ?? 'Other';
if (!groups.has(group)) {
  const fs = document.createElement('fieldset');
  const legend = document.createElement('legend');
  legend.textContent = group;
  ...
  groups.set(group, fs);
}
```
Apply in `renderInfo` (L234-247) with a `Map` keyed by `row.group`, first-seen order.

**Unrounded numbers (D-19):** `fmt` (L26) `Number(v).toFixed(3)...` is replaced by `String(row.value)` in the one place `renderInfo` uses it (L240). Delete `fmt` if unused (a test may pin its absence); resolve `docs/tech_debt/active/2026-10-06-ui-rounds-displayed-numbers.md` in the same commit.

**Notes and badge:** extend `showMessages(errors, warnings)` (L209-215), which builds `<p class="error|warning">` via `Object.assign(document.createElement('p'), {className, textContent})`; add a third list with its own class. Text only via `textContent` (`tests/test_parity.py::test_the_ui_builds_nodes_from_text_only` L352). `renderInfo` stores `pendingWarnings` (L244) so mesh warnings survive; notes must follow the same rule-15 treatment.

**Picker:** three selects built from `/api/presets` using the generic `fetch(...)`, `new Option(text, value)`, `write(input, v)` helpers (L30-34, L39-44). A pick writes every `fields` entry through `write()` keyed by whatever names arrive. `partQuery()` (L187-200) omits default-valued fields, so a picked preset equal to the defaults leaves the hash empty. The preset id is session state only, never in `partQuery()` or `writeHash()` (D-09, `navigate`/`refuseLink` unchanged).

**Pinned statements:** `PINNED_STATEMENTS` (`tests/test_parity.py` L258-276) is a list of verbatim JS substrings. If `fmt(row.value)` or the `renderInfo` loop line changes, update the pinned string in the same commit and add the new statements (positive rule, do not delete a pin silently).

---

### `pyproject.toml` `[tool.importlinter]` (config)

**Analog:** contracts at L145-230. Contract 2 (L155-166) `source_modules = ["screw.calc", "screw.params", "screw.cli"]`; widen with `screw.tables`. Add contracts 6 and 7 in the same style (name, explanatory comment, `type = "forbidden"`):
```toml
[[tool.importlinter.contracts]]
name = "The parameters never consult a table"
type = "forbidden"
source_modules = ["screw.params", "screw.calc.thread"]
forbidden_modules = ["screw.tables"]       # leave allow_indirect_imports unset (checked indirectly)

[[tool.importlinter.contracts]]
name = "Tables are a leaf"
type = "forbidden"
source_modules = ["screw.tables"]
forbidden_modules = ["screw.params", "screw.calc", "screw.solid", "screw.app", "screw.cli",
                     "cadquery", "OCP", "fastapi", "logging"]
```
**Alert 3:** these pass vacuously if `calc/__init__.py` imports `tables` at import time (grimp does not model the package `__init__` edge). Note the existing contracts use `allow_indirect_imports = true` to allow reaching through; contract 6 deliberately does not. Contract 5 (`screw.app` to kernel, `allow_indirect_imports = false`, L187-197) is why `calc/presets.py` must not import `solid`. The runtime `sys.modules` subprocess test is the positive control.

---

### `tests/test_tables.py` (test, batch)

**Analog:** `tests/test_thread_maths.py` L207-233: a table typed independently from the code under test, then parametrised over its items with the failure cases asserted.
```python
@pytest.mark.parametrize(("key", "row"), list(L11_ROWS.items()))
def test_each_cap_is_accepted_and_the_next_float_above_is_refused(key, row) -> None:
    (d, pitch), (cap, turns) = key, row
    assert fine_stl_refusal(d, pitch, cap) is None
    refusal = fine_stl_refusal(d, pitch, math.nextafter(cap, math.inf))
    assert refusal is not None
```
Use `@pytest.mark.parametrize("row", ROWS, ids=lambda r: r.id)` with the relation list (RESEARCH Code Example 5 / D-14). Also: UNVERIFIED scan over `src/screw/tables/` plus a positive control feeding an UNVERIFIED row; a `mypy.api` test that a row without `Source` fails; cross-table checks (262 pitch equals 4014/4017 `P`; bracket iff choice 2). No kernel build per row (C11). `filterwarnings = ["error"]`, `xfail_strict` are on (pyproject), so no stray warnings.

### `tests/test_presets.py` (test, request-response)

**Analog:** `tests/test_parity.py`: `cli.main([...])` with `capsys`, TestClient on the app with an inline build backend (`_inline_build_backend`, L45), and `_expected_flags`/`_cli_flags` (L60-88). Round-trip every catalogue row through `BoltParams(**fields)` and `derive` and assert the exact match id (4017 when both match); assert `/api/presets` and `screw presets` identical; pin the count of fine-STL-refused rows (Alert 7).

### `tests/test_parity.py` and other modified tests

`_expected_flags` (L60-67) generates flags from fields; `--preset` is the one flag not from a field. Teach it by a positive rule: `_expected_flags(kind) + ["--preset"]` on `info`/`export` only, and a test that feeds a stray hand-written flag and sees the failure (the existing `test_the_literal_check_has_teeth` L232 is the control pattern). Ripple list: RESEARCH Pitfall 3 (params defaults/schema property list/slug, API OpenAPI field sets, calc `WARNING`/`KEYS`/units, parity groups assertion and `cases` loop, solid default bbox 6x6x20, thread-maths `L11_ROWS == FINE_STL_ROWS`, `bench/corpus.py` and `tests/test_bench.py` L147-151). `tests/test_calc.py` L14-19 pins `WARNING`/`KEYS` at module level; update those constants to the D-04 text and the new keys.

`tests/test_params.py` L87-95 is the pattern for the new 422 tests:
```python
with pytest.raises(ValidationError) as caught:
    BoltParams.model_validate({"length": 250.5})
[err] = caught.value.errors()
assert err["type"] == "turn_cap"
assert err["loc"] == ()
assert err["ctx"]["fields"] == ["length", "pitch"]
assert err["msg"].startswith("length and pitch: ")
```
Reuse for `head_too_small` and the new turn-cap fields.

---

## Shared Patterns

### One pure function, two callers (parity)
**Source:** `src/screw/calc/__init__.py` L101-114 (`download_refusal`), used by `app.py` L403-414 and `cli.py` L116-126.
**Apply to:** `thread_length_conflict`, preset `expand`, catalogue builder, `head_too_small_refusal`. The text begins with the field names because the CLI prints no `loc`.

### Cross-field 422 with named fields
**Source:** `src/screw/params.py` L78-87, L107-114; surfaced by `app.js` `problems()` L217-232 via `ctx.fields` and by `cli._params` L79-84.
**Apply to:** `head_too_small`, the turn cap on `t`, the `thread_length` conflict (API dependency version carries the same `ctx.fields`).

### Finite-or-warned (L02)
**Source:** `calc/__init__.py` L60-79. **Apply to:** every new numeric info row; absent row plus a warning, never a plausible number.

### INTERIM / run-id comments
**Source:** `calc/thread.py` L18-29, L170-181; `params.py` L18-31. **Apply to:** `FINE_STL_ROWS` re-key (cite `2026-10-08-a-grid`), the cap-input change (D-22), any new bound. Comments carry the measurement, "Phase 7 re-sweeps".

### Frozen pydantic documents
**Source:** `calc/__init__.py` L27-45, `app.py` L361-367. `ConfigDict(frozen=True)`, described fields.

### Debt retirement
**Source:** `docs/tech_debt/TEMPLATE.md`, `INDEX.md`. In the fixing commit: `Status: resolved`, commit sha, `git mv active/ resolved/`, INDEX row. Applies to `2026-10-06-ui-rounds-displayed-numbers.md` (D-19) and `2026-10-11-fine-stl-cap-applies-right-hand-rows-to-left-hand-parts.md` (D-21). Amend (not resolve) `2026-10-05-interim-runtime-bounds.md` (D-22 row), `2026-10-11-default-pitch-d100-length200-...` (repro now needs `thread_length=200`), `2026-10-11-info-document-prints-numbers-for-a-length-the-builder-refuses.md` (Alert 6).

### The gate per commit
`make verify` is the pre-commit hook (RESEARCH Pitfall 4): rows and their second copy land together; the UNVERIFIED scan lands with the first rows; a default-changing commit lands field, builder, `derive` and ripple tests as one change.

## No Analog Found

| File / concern | Role | Data Flow | Reason |
|---|---|---|---|
| `src/screw/tables/iso4014.py`, `iso4017.py`, `iso262.py` (the row data itself) | data | n/a | No tables exist in the repo; `FINE_STL_ROWS` is the only typed, cited constant table. Rows come from the owner's and agent's transcriptions of the purchased PDFs (D-14), not from any code or web source. `../spur` has no tables (checked 2026-10-11). |
| `tests/test_tables_second_entry.py` (cell-by-cell diff) | test | batch | No double-entry test exists. Closest in spirit: `test_thread_maths.py` `L11_ROWS` ("typed from the table, not read back from the code under test"). |
| `tests/test_import_boundaries.py` (`python -I -c` subprocess for `sys.modules`) | test | n/a | No subprocess test of import state exists. Use RESEARCH Code Example 3 and its converse (`derive` loads `screw.tables`) so it cannot pass vacuously. |
| Picker (three linked selects) and badge | component | event-driven | `app.js` has `kindSelect` (`loadKinds`, L39-44) as the only select built from an API list; the linked filtering and "blank option when no row matches" have no precedent. Write against the generic `write()`/`Option` helpers and the RESEARCH Pattern 5 catalogue shape. |
| Hex-head solid | service | transform | `helical.thread` is the only builder; the prism and cylinder recipe comes from RESEARCH Code Examples 1-2 (probe verified), not the repo. |

## Metadata

**Analog search scope:** `src/screw/` (all modules), `tests/`, `pyproject.toml`, `.github/`, `docs/tech_debt/`, `bench/corpus.py`.
**Files read:** 14 (params, calc/__init__, calc/thread, solid/__init__, solid/bolt, app, cli, app.js excerpts, test_parity/test_calc/test_params/test_thread_maths/test_cli excerpts, pyproject excerpt, 03-PATTERNS head).
**Pattern extraction date:** 2026-10-11
**Open items the planner must put to the owner before fixing mechanisms:** RESEARCH Alerts 1 (D-08 mechanism), 2 (left-hand cap values), 4 (D-23 keep 422), 6 (undefined `thread_length` cases and shank sliver), plus Open Questions 4, 5, 7.
