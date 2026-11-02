# Phase 8: Pre-release Gap Closure - Pattern Map

**Mapped:** 2026-11-02
**Files analyzed:** 24 new/modified
**Analogs found:** 22 / 24 (all analog paths verified git-tracked with `git ls-files`)

Owner rulings D-15 to D-18 are applied: band-specific fine predicate for bolts (D-15), nut threshold strict `> 6` (D-16), `solid/pair.py` untouched (D-17), turns guard names `d, pitch, thread_length, length` (D-18).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|
| `src/screw/calc/thread.py` (+thresholds, `uses_fine_sweep`, `turn_guard_refusal`) | utility (pure maths) | transform | same file: `pitch_too_fine_refusal`, `MAX_*_D_PER_PITCH`, `_exact` | exact |
| `src/screw/params.py` (+turn-guard validator, last in order) | model validator | request-response | same file: `_pitch_too_fine`, `BoltParams._turn_cap` | exact |
| `src/screw/solid/helical.py` (`fine` arg, samples, tolerance) | service (kernel) | transform | same file: `section`, `twist`, `thread` | exact |
| `src/screw/solid/bolt.py` (pass `fine=`) | service | transform | same file `thread()` | exact |
| `src/screw/solid/nut.py` (pass `fine=`) | service | transform | same file `void()` | exact |
| `src/screw/solid/pair.py` | service | transform | NO CHANGE (D-17) | n/a |
| `src/screw/calc/cost.py` (+`FINE_ENVELOPE`, `fits`/`predict` select) | service (cost model) | transform | same file `fits`, emit-constants block | exact |
| `bench/oper_fit.py` (fine envelope, `emit_constants`) | utility | batch | same file `envelope`, `emit_constants` | exact |
| `bench/oper_sets.py` (proof-grid walk set, fine re-sweep set, judge subcommand) | utility | batch | same file `pitch-walls` set (`PITCH_*`, `build_*`, `_regenerate_runs2`) | exact |
| `bench/oper_lift.py` (`_no_pitch_wall` also lifts new guard) | utility | transform | same file `_no_pitch_wall` | exact |
| `bench/points/<new>.json` | config (data) | batch | `bench/points/explore.json`, `dense-band.json` | role-match |
| `bench/results/phase-08/**`, `bench/RESULTS.md` section | records | batch | `bench/results/phase-07/walls-pitch-41074314305/`, `### walls-pitch, run 41074314305` | exact |
| `tests/test_turn_guard.py` (new) | test | request-response | `tests/test_fine_pitch.py` | exact |
| `tests/test_oper_fine.py` (new, records-driven proof grid) | test | batch | `tests/test_oper_pitch.py` | exact |
| `tests/test_fine_pitch.py` (extend: nut max ratio assertion, island/debt cells) | test | request-response | itself | exact |
| `tests/test_solid.py` / `tests/test_nut.py` (island, 25 mm debt example kernel cells) | test | transform | existing kernel tests in same files (not re-read; planner copies local style) | role-match |
| `tests/test_cost.py`, `tests/test_oper_fit.py` (fine envelope pinned to records) | test | batch | `test_the_shipped_constants_are_the_block_emit_constants_writes_from_the_evidence` | exact |
| `tests/test_parity.py` (PINNED_STATEMENTS edit, INT-03 part) | test | request-response | itself, lines ~590-612 | exact |
| `tests/test_cli.py` (help text line) | test | request-response | itself | role-match |
| `src/screw/static/app.js` (touched-field tracking) | component | event-driven | same file `partQuery`, `pick`, `navigate`, `lastTyped` | exact |
| `src/screw/cli.py` (help text only), `README.md` (one line) | config/doc | n/a | `cmd_export`; README Use block lines 25-30 | exact |
| `docs/architecture/decision_log.md` (L34+) | doc | n/a | L25 (line 2051), L32 (line 2470) | exact |
| `docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md` -> `resolved/` + `INDEX.md` | doc | n/a | CLAUDE.md debt-resolve flow | exact |
| `.planning/REQUIREMENTS.md`, `04-11-SUMMARY.md` | doc | n/a | existing text (TABL-06 line 42; SUMMARY frontmatter line 46) | exact |

## Pattern Assignments

### `src/screw/calc/thread.py` (utility, transform)

**Analog:** itself. Constants block at lines 70-83, `_exact` at 301, `pitch_too_fine_refusal` at 390.

**Constants pattern** (lines 76-83): ruled constants carry the ruling in a comment; data-derived ones live between BEGIN/END markers written by the judge.
```python
# BEGIN pitch-walls: written by `python -m bench.oper_sets pitch-walls --from
# bench/results/phase-07/walls-pitch-41074314305`; not edited by hand.
MAX_BOLT_D_PER_PITCH = Fraction("20")
# END pitch-walls
# Nut: 8 by the owner's ruling G36, not by the margin rule. ...
MAX_NUT_D_PER_PITCH = Fraction(8)
```
Add beside them: nut fine threshold `Fraction(6)` (strict `>`, D-16, ruling comment: island is at 6.999993636, so `>= 7` misses it); bolt D-15 band predicate (d bands about 0.5-0.85 and 1.6-3.3 mm, with d / pitch > 6; edges judge-written between BEGIN/END markers from runner records); the turn-guard ceilings as a judge-written block.

**Exact compare pattern** (lines 301-305, 395-405):
```python
def _exact(x: float) -> Fraction:
    """The decimal the user typed: `repr` is the shortest string that round-trips the float. ..."""
ratio = _exact(d) / _exact(pitch)
if ratio <= wall:
    return None
```
`uses_fine_sweep(kind, d, pitch)` follows this: `Fraction` compare, strict `>`, no float division, kernel-free (never import `cadquery`).

**Refusal-text pattern** (lines 407-415): message begins with the field names because the CLI prints no `loc`; no braces (pydantic formats the message).
```python
text = (f"d and pitch: d / pitch is {ratio:.6g} at d {_plain(d)} and pitch {_plain(pitch)}, "
        f"above {wall}, {why}")
```
`turn_guard_refusal(d, pitch, t)` starts `d, pitch, thread_length and length: `. Takes `t = built_thread_length(thread_length, length)` (line 203). Sibling for tone: `turn_cap_refusal` (begins `thread_length, length and pitch: `).

---

### `src/screw/params.py` (model validator, request-response)

**Analog:** `_pitch_too_fine` (158-166) and `BoltParams._turn_cap` (208-220), `_fine_pitch` last validator (233-236, 303-306).

**Validator-to-PydanticCustomError pattern** (lines 158-166, 208-220):
```python
def _pitch_too_fine(p: FastenerParams) -> None:
    from screw.calc.thread import pitch_too_fine_refusal
    if (msg := pitch_too_fine_refusal(p.kind, p.d, p.pitch)) is not None:
        raise PydanticCustomError("pitch_too_fine", msg, {"fields": ["d", "pitch"]})

@model_validator(mode="after")
def _turn_cap(self) -> Self:
    from screw.calc.thread import built_thread_length, turn_cap_refusal
    t = built_thread_length(self.thread_length, self.length)
    if (msg := turn_cap_refusal(t, self.pitch)) is not None:
        raise PydanticCustomError("turn_cap", msg, {"fields": ["thread_length", "length", "pitch"]})
    return self
```
New `_turn_guard` on `BoltParams` (bolt only has `thread_length`): lazy import inside body, `ctx.fields = ["d", "pitch", "thread_length", "length"]` (D-18), declared AFTER `_fine_pitch` so a part another rule refuses keeps its older error (L25). Nut: add only if the runner leaves a nut refusal (D-06 "no refusal, no ceiling").

---

### `src/screw/solid/helical.py` (service, transform)

**Analog:** itself. `SECTION_SAMPLES = 14` (line 26, comment documents 0.1 um vs 4 -> 7 um); `section` (38-62) reads it at line 46; `twist` (65-77); `thread` (80+).

**Core pattern to modify** (lines 46, 65-77):
```python
nf = SECTION_SAMPLES                      # -> nf = 56 if fine else SECTION_SAMPLES
...
pipe = BRepOffsetAPI_MakePipeShell(spine.wrapped)
pipe.SetMaxSegments(MAX_SEGMENTS)
pipe.SetMode(aux.wrapped, False)
# fine only: pipe.SetTolerance(1e-6, 1e-6, 1e-4)   # after SetMode, before Add, as the debug E12/E14 variant
pipe.Add(section(d, pitch, clearance).wrapped)
```
Thread `fine: bool = False` through `section(..., fine)`, `twist(..., fine)`, `thread(..., *, fine=False)` as an argument, NOT a flipped module global (RESEARCH anti-pattern). Default False keeps `pair.py` and all shipped callers bit-identical (D-17). Comments carry the measurement, per house style (cite the runner run id; each cited id needs a `### <set>, run <id>` heading in `bench/RESULTS.md`, Pitfall 6).

### `src/screw/solid/bolt.py` and `nut.py`

**Analog:** the two call sites.
```python
# bolt.py:38
return helical.thread(p.d, p.pitch, t, left_hand=p.left_hand)
# nut.py:45
return helical.thread(p.d, p.pitch, p.m + 2 * p.pitch, clearance=p.clearance,
                      left_hand=p.left_hand).translate(cq.Vector(0, 0, -p.pitch))
```
Add `fine=uses_fine_sweep(p.kind, p.d, p.pitch)` (import from `screw.calc.thread`, already a `solid` dependency). `pair.py:68,78` stays untouched (D-17).

---

### `src/screw/calc/cost.py` (cost model, transform)

**Analog:** `fits` (334-341) and the `# BEGIN emit-constants` block (line 92, `ENVELOPE` at 147).
```python
def fits(p: FastenerParams, artifact: Artifact) -> bool:
    if below_fitted_turns(p):
        return False
    kind = p.kind
    return all(admitted(pred, ENVELOPE[kind, artifact, target], component)
               for pred, target, component in zip(predict(p, artifact), TARGETS,
                                                  budget(kind, artifact), strict=True))
```
Select `FINE_ENVELOPE` when `uses_fine_sweep(...)` else `ENVELOPE`. `FINE_ENVELOPE` goes INSIDE the emit-constants block, written by `bench.oper_fit.emit_constants`, never typed (`make verify` pins it). `cap_defaults`/`fits_every_artifact` need no change beyond `fits`. After editing re-run R21 export-cache count (`tests/test_runtime_bounds.py`).

### `bench/oper_fit.py`

**Analog:** `envelope(model, points)` (line 272, raises factor by single ulps so `pred x (1+e) >= every actual`) and `emit_constants` (line 701). Reuse `envelope` over the fine re-sweep readings only; extend `emit_constants` with the `FINE_ENVELOPE` lines. Do not touch `fit.json` (`widened_by`).

### `bench/oper_sets.py` and `bench/oper_lift.py`

**Analog (sets):** the `pitch-walls` set: `PITCH_BOLT_FORMS`, `PITCH_BOLT_D`, `PITCH_BOLT_Q`, `PITCH_NUT_*`, a `build_*` function, a `_regenerate_runs2` entry and a CLI subcommand that prints a `# BEGIN pitch-walls` block. Add sets for (a) the shipped-sweep walk in the d 0.5-0.85 / 1.6-3.3 bands at d / pitch 6-8 and turns 50-90, with d steps near 0.45-0.9 and 1.5-3.4, (b) the proof grid, (c) the fine re-sweep, each with a subcommand that prints the constants. Pre-register rules before data (A6). Point cell pitch is `ceil6(d / q)` (exact ratio at most q).

**Analog (lift)** `bench/oper_lift.py:91-100`:
```python
@contextmanager
def _no_pitch_wall() -> Iterator[None]:
    module = vars(thread)
    saved = {name: module[name] for name in ("MAX_BOLT_D_PER_PITCH", "MAX_NUT_D_PER_PITCH")}
    module.update(dict.fromkeys(saved, UNWALLED))
    try:
        yield
    finally:
        module.update(saved)
```
Extend the tuple (or add a sibling context manager used by `drawn`/`registered`) with the new guard constants, in the same commit as the guard, or `python -m bench.oper_sets --check` and `test_the_walk_file_is_what_the_generator_writes_under_its_recorded_envelope` go red (Pitfall 1). Dispatch order: fine sweep without guard first, then add guard.

**Dispatch commands** (Pattern 3, RESEARCH): push branch with `-u`, `gh workflow run operability.yml --ref gsd/phase-08-pre-release-gap-closure -f set=<name>`, `gh run download <id> -p 'oper-*' -D bench/results/phase-08/<name>-<id>`.

---

### `tests/test_turn_guard.py` (new) and `tests/test_fine_pitch.py` (extend)

**Analog:** `tests/test_fine_pitch.py` lines 1-140.

**Imports + helpers** (lines 10-47): `TestClient(app)`, `build_backend` override fixture `no_build` that records parts so a refused part never reaches the kernel, `_argv(params)` flag builder, `_explore()` reading `bench/points/explore.json`.

**API assertion shape** (lines 85-92):
```python
r = client.get(route, params=params)
assert r.status_code == 422, (label, route)
[detail] = r.json()["detail"]
assert {k: v for k, v in detail.items() if k != "input"} == {
    "loc": ["query"], "type": "pitch_too_fine", "msg": expected,
    "ctx": {"fields": ["d", "pitch"]}}
assert no_build == []
```
**CLI assertion shape** (lines 99-105): `pytest.raises(SystemExit)`, `code == 2`, `capsys.readouterr().err == f"error: {expected}\n"`, output file not written.

**Catalogue-untouched test** (lines 108-125): iterate `catalogue()` / `nut_catalogue()` with `expand`/`expand_nut` and `model_validate` every row. Copy into the turn-guard test (294 bolt rows, 14 nut rows all admitted, iso4017:M3x30 at 60.0 turns is the binding row). Edit in `test_fine_pitch.py`: the `max(ratios) == MAX_NUT_D_PER_PITCH` assertion stays true (8); the 20 `IN_WALL` parts stay `pitch_too_fine` (already pinned, do not alter).

### `tests/test_oper_fine.py` (new, records-driven)

**Analog:** `tests/test_oper_pitch.py` (lines 60-80 shown): counts points from the committed set file, checks labels unique, artifact set, and re-derives cell pitches with `Decimal` as a second method. Mirror it: proof grid from committed runner records is `ok` or refused by the model; shipped thresholds equal the judge's output. Kernel-free; do NOT mark `grid`/`pair` (deselected by default).

### `tests/test_cost.py` / `tests/test_oper_fit.py`

**Analog:** `test_the_shipped_constants_are_the_block_emit_constants_writes_from_the_evidence` in `tests/test_cost.py` (asserts the emit block verbatim against `bench.oper_fit.emit_constants(...)`). Extend with the fine envelope record under `bench/results/phase-08/`.

### `src/screw/static/app.js` and `tests/test_parity.py` (event-driven, web)

**Analog:** `partQuery()` (lines 384-397), `pick()` (226-240), `navigate()` (296+), `lastTyped` (line 36).
```js
function partQuery() {
  const q = new URLSearchParams();
  for (const [name, { input }] of fields) {
    const value = read(input);
    if (value === '') continue;
    const changed = input.type === 'number'
      ? Number(value) !== Number(defaults[name])
      : value !== String(defaults[name]);
    if (changed) q.set(name, value);
  }
  return q;
}
```
Change to `if (changed || touched.has(name)) q.set(name, value);`. `touched` is a page `Set`: add on `input` event with non-empty value; delete when cleared; `pick()` replaces it with `Object.keys(entry.fields)` (D-12); `navigate()` resets it to the hash's keys; cleared by Reset and kind switch. `partQuery`/`writeHash` must not name `presetBasis`, `rowOfFields`, `quality`, `download`, `lastTyped` (parity test enforces).

**Test pin edit** (`tests/test_parity.py` ~lines 590-612): `PINNED_STATEMENTS` pins `"Number(value) !== Number(defaults[name])"` and `"for (const [name, { input }] of fields) write(input, h.get(name) ?? defaults[name]);"`. Edit pins in the same commit; keep `test_the_literal_check_has_teeth`. D-13 test: no browser harness exists, so execute API and CLI on `BoltParams d=30 pitch=2 s=48 k=18` with typed `thread_length=20` (422 `over_budget` / exit 2) versus omitted (capped, warned), and assert by source text that `touched` is set by `input`, `pick()` and `navigate()`.

---

### Docs: decision log, debt, requirements

**Decision log analog:** L25 (`docs/architecture/decision_log.md:2051`) and L32 (`:2470`). Heading format `## L34 — <title>` (parsed by `^## (L\d\d) ` in `tests/test_runtime_bounds.py`), `Date:`, rulings cited, bold-lead paragraphs (**The rule.**, **What it refuses.**, **What moves.**, **What it leaves open.**), `Reason:`, `Reversibility:`. Contents: sweep + thresholds + D-15 band predicate + guard (supersedes L25 in part), 8 moved nut rows named (M5, M8, M10, M12, M14, M16, M18, M20), pair-on-shipped-sweep note (D-17), grid-unproven residual (E32), typed-default rule (supersedes L19/L21 sentences, UI-SPEC rules 6, 9, 19, 35), CLI no-deadline (D-09). Splitting L34/L35/L36 is cleaner.

**Debt resolve flow** (CLAUDE.md): in the fix commit, flip `Status: resolved`, add sha, `git mv docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md docs/tech_debt/resolved/`, move the `docs/tech_debt/INDEX.md` row, correct the "names no field" wording (INT-06).

**REQUIREMENTS.md:** TABL-06 (line 42) text amend citing L19 and 2026-11-01 ruling; OPER-03 complete only when SC1 holds. **04-11-SUMMARY.md:46:** `requirements-completed: [INFO-05]`.

**README/CLI:** one line near README lines 25-30 and in `cli.py` `export` subparser help (`help="write an STL or STEP file"`, ~line 245). No flag, no child process.

## Shared Patterns

### Kernel-free refusal at the model boundary
**Source:** `src/screw/params.py:158-166`, `src/screw/calc/thread.py:390-415`
**Apply to:** the turns guard, and the `uses_fine_sweep` predicate (exact `Fraction`, text begins with field names, `PydanticCustomError(type, msg, {"fields": [...]})`).

### Constants written by judge code, held by a test
**Source:** `calc/thread.py` BEGIN/END `pitch-walls`; `calc/cost.py` BEGIN emit-constants; `bench/oper_sets.py pitch-walls` subcommand; `tests/test_oper_pitch.py`, `tests/test_cost.py`
**Apply to:** guard ceilings, band edges for D-15, `FINE_ENVELOPE`. Rulings (nut 6, bolt 8) are typed with the ruling in a comment.

### Import boundaries
`calc` never imports `cadquery`; vendor types stop at `screw.solid`; `Any` is not written (L04). Run `make lint typecheck lint-imports` after `calc`/`params`/`bench` edits.

### Runner evidence
Every cited run id needs a `### <set>, run <id>` section in `bench/RESULTS.md` (`tests/test_runtime_bounds.py` scans `src/**/*.py|js`, `Dockerfile`, `compose.yaml`, L20-L25 text). Freeze `helical.py`, thresholds, `bolt.py`, `nut.py` before the cost dispatch (Pitfall 10).

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| Band-specific fine predicate (D-15) in `calc/thread.py` | utility | transform | No existing d-band predicate; build from the E30 band edges (0.45 out, 0.5 in, 0.85 in, 0.9 out, 1.55 out, 1.6 in, 3.3 in, 3.35 out) re-read on the runner at d / pitch 6-8, in the `_exact` style. Follow `RESEARCH.md` Pitfall 3. |
| Web touched-field test | test | event-driven | No browser harness exists (L01); use source-text assertions like `tests/test_parity.py`. |

## Metadata

**Analog search scope:** `src/screw/{calc,solid,static}`, `src/screw/params.py`, `src/screw/cli.py`, `bench/`, `tests/`, `docs/architecture/decision_log.md`, `docs/tech_debt/`
**Files scanned:** about 25 (ranged reads of large files)
**Pattern extraction date:** 2026-11-02
**Not re-read (lines taken from RESEARCH.md, verified tracked):** `tests/test_solid.py` / `tests/test_nut.py` local style, `tests/test_cli.py`, `bench/oper_fit.py` internals.
