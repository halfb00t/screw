# Phase 6: Printed Pair Acceptance - Pattern Map

**Mapped:** 2026-10-22
**Files analyzed:** 17 (6 new, 11 modified)
**Analogs found:** 15 / 17 (all analog paths checked with `git ls-files`: tracked)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `bench/print_rules.py` (new) | utility (kernel-free rule module) | batch / transform (TSV record to constant) | `bench/pair_expected.py` | exact |
| `bench/print_matrix.py` (new) | utility (matrix as data, manifest) | batch | `bench/pair_expected.py` (`main`/`render`, ROOT-anchored paths) | role-match |
| `bench/results/phase-06/print-run-1.tsv`, `print-run-2.tsv`, `manifest.tsv` (new) | data record | file-I/O | `tests/data/pair_expected.tsv` (TSV, header = `COLUMNS`) | role-match |
| `.planning/phases/06-printed-pair-acceptance/06-PRINT-PROTOCOL.md` (new) | doc (pre-registration) | n/a | `.planning/phases/02-thread-spike/02-SPIKE.md` | exact |
| `src/screw/calc/printability.py` (new) | utility (constants + warning builders, kernel-free) | transform | `src/screw/calc/pair.py` (kernel-free constants with comment citing why) | role-match |
| `src/screw/calc/__init__.py` (mod: `_nut`, `_bolt`) | service | request-response | itself, `_nut` lines 377-410, `_bolt` 300-305 | exact |
| `src/screw/params.py` (mod: `NutParams.clearance`) | model | request-response | itself, `_f` / `_req` lines 34-58, field at 186-190 | exact |
| `tests/test_print_rules.py` (new) | test | batch | `tests/test_pair.py` (re-derivation) + `tests/test_thread_maths.py:486` (recompute from committed record) | exact |
| `tests/test_params.py`, `test_nut.py`, `test_api.py`, `test_cli.py`, `test_parity.py`, `conftest.py` (mod) | test | request-response | themselves (blast-radius table in RESEARCH) | exact |
| `tests/test_calc.py` (mod: warning tests) | test | request-response | `tests/test_calc.py` counterpart tests (`warnings[-1]` lines 1160-1173) | exact |
| `pyproject.toml` (mod: import contracts) | config | n/a | contract at lines 236-253 (`bench.pair_expected`) | exact |
| `docs/architecture/decision_log.md` (mod: L17/L18) | doc | n/a | L16 entry (line 1186) | exact |
| `bench/RESULTS.md` (mod) | doc | n/a | `## Product pair cells (Phase 5, D-07)` (line 6767) | role-match |
| `.planning/REQUIREMENTS.md`, three `docs/tech_debt/active/*.md` (mod) | doc | n/a | self; text edits only | n/a |
| `docs/architecture/overview.md:28` (mod) | doc | n/a | self | n/a |

## Pattern Assignments

### `bench/print_rules.py` (utility, batch/transform)

**Analog:** `bench/pair_expected.py` (read in full, 78 lines)

**Module docstring + imports** (lines 1-30): docstring states the rule is derived, never typed, committed before the run, re-derived by a `make verify` test, and that the module imports no kernel and no product code.
```python
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "bench" / "results" / "thread-spike" / "2026-10-08-a-pair.jsonl"
# The digest `bench/RESULTS.md` `### 2026-10-08-a-pair` records for the JSONL.
RECORD_SHA256 = "1644650e..."
COLUMNS = ("size", "d", "pitch", "m", "clearance", "rod_left_hand", "nut_left_hand", "verdict")
```
Do not import `screw.*` here (the ladder/sizes live in this module as literals; a test pins them to the protocol text). Copy `ROOT`-anchored fixed paths (05-01 deviation 2).

**Core pattern: sha pin refusal** (lines 36-47):
```python
data = path.read_bytes()
digest = hashlib.sha256(data).hexdigest()
if digest != RECORD_SHA256:
    raise ValueError(f"{path} is not the record L11 cites: sha256 {digest}, "
                     f"expected {RECORD_SHA256}")
```
Adapt: `RECORD_SHA256` per run file. For the synthetic-record tests, `default_from`/`thresholds_from` must take parsed rows (not a path), and a thin `load(path)` does the sha check, so tests do not need the pin.

**Render/main** (lines 67-78): `render(rows) -> str` with `"\t".join`, trailing newline; `main()` writes the table; `if __name__ == "__main__": main()`.

**Validation (no analog, RESEARCH Pitfall 5):** raise `ValueError` naming the row for blank cell, `result` not in {pass, bind}, bind without `turns`, a 4th sample, duplicate or missing sample id. Use stdlib `csv` with `delimiter="\t"`. Rule-function shape is in RESEARCH Pattern 1 (`default_from` returns `float | None`; `None` = D-08 escape; non-monotone also `None`). Strict `<` for D-11 (Pitfall 7).

---

### `bench/print_matrix.py` (utility, batch)

**Analog:** `bench/pair_expected.py` for structure (`COLUMNS`, `render`, `main`). One data module the manifest, blank template and tests all read (RESEARCH "Don't Hand-Roll"). Counts to pin: 60 nuts + 12 bolts (+12 bought-nut bolts per Open Question 2) + 9 + 9. Per-size ISO 4017 short lengths from `screw presets bolt`: M6 12, M8 16, M10 20, M12 25 (M3 6, M4 8, M5 10). STL names follow `screw export` (e.g. `nut_d8_pitch1.25_left_hand0_s13_m6.8_clearance0.1.stl`). If it shells `screw export`, keep that in `main()` only so the importable part stays kernel-free.

---

### `bench/results/phase-06/*.tsv` (data record, file-I/O)

**Analog:** `tests/data/pair_expected.tsv` (tab-separated, header line first, trailing newline, hand-diffable). The blank template lists every expected sample id so a missing row is detectable. Columns suggested: `run, size, clearance, sample, plate, order, result, turns, note`. Sha256 goes in `bench/RESULTS.md` and in the `print_rules` pin, committed with the derived constant.

---

### `.planning/phases/06-printed-pair-acceptance/06-PRINT-PROTOCOL.md` (doc)

**Analog:** `.planning/phases/02-thread-spike/02-SPIKE.md`

**Header sentence** (line 3): "This file is pre-registered: everything above the `## Results` heading lands on `main` in PR 1 before run 1 ..."
**Section order** (grep of headings): `## Question`, `## Owner rulings`, `## Environment`, `## Method`, `## Protocol inputs`, `## Rules`, `## Predictions`, `## Escape clause`, `## Results`, `## Verdict`.
**Predictions style** (line 245): each prediction is the outcome expected before any run with the prior evidence; "A prediction is not a target." Put the owner's 0.1 mm here as a prediction (D-01). Add the owner-typed D-06 profile (printer, nozzle, material, layer height, slicer, orientation, bought-nut brand/plating) and the pre-registered order and plate rules (Pitfalls 3, 4; 0.25 to 0.05 per bolt).
**Escape clause style** (line 262): bullets of "X is not planned/shipped until ... when ...", then the closing paragraph "Nothing is tuned toward a pass ... a change after landing is a new PR that visibly post-dates this protocol." Map to D-08 (no step passes, or not monotone: no default ships, `clearance` stays required) and D-14 (any size binds in 2 or more of 3 promotes PAIR-07).
Land via the Phase 5 05-01 pattern: worktree from `origin/main`, own `make venv`, other-CLI review, `make pr.land`, before print 1. Owner inputs are a `checkpoint:human-action` as in `05-02-PLAN.md:181`.

---

### `src/screw/calc/printability.py` (utility, transform)

**Analog:** `src/screw/calc/pair.py` (constants-with-why style, kernel-free, `from __future__ import annotations`, imports only `math`/`typing`). Constants carry a comment citing the run id, record sha256 and the owner profile:
```python
# Radial clearance of the nut's void in mm, the proof bracket (D-11) ...
PAIR_CLEARANCES: tuple[float, ...] = (0.05, 0.10, 0.15, 0.20)
```
Holds `D_MIN`, `P_MIN`, `MEASURED_RANGE` (d 6.0 to 12.0 per recommendation), run ids, and two warning builders returning `str | None`. Imports nothing from `screw.tables`, `logging`, `cadquery` (contracts in pyproject lines 160-190 already cover `screw.calc`; the tables contract is the runtime test in `tests/test_import_boundaries.py`). Constants may not be typed by hand: `tests/test_print_rules.py` recomputes them from the committed record.

---

### `src/screw/calc/__init__.py` (service, request-response)

**Analog:** itself.

**Nut insertion point** (lines 405-410): add D-09 and D-13 warnings after the download refusals and BEFORE `counterpart_for`, because tests assert `warnings[-1]` is `off_row` (`tests/test_calc.py:1160,1167,1173`, `tests/test_api.py:1289`):
```python
    downloads = _downloads(p)
    for reason in dict.fromkeys(e.refusal for e in downloads if e.refusal is not None):
        warnings.append(reason)
    # <-- new: measured-range (nut only, D-09) and printability (D-13) here
    m18 = [M18_NOTE] if (p.d, p.pitch) == M18_KEY else []
    counterpart, off_row = counterpart_for(p)
    if off_row is not None:
        warnings.append(off_row)
```
**Bolt insertion point** (lines 298-305): same spot, after the `for reason in dict.fromkeys(...)` loop and before `counterpart, off_row = counterpart_for(p)`. D-13 only (bolt has no clearance).
**Warning style** (line 382): `warnings.append(f"clearance {p.clearance:g} is not positive: " "the pair cannot be proven (PAIR-03)")`. Plain f-string, names the field, cites a requirement/decision id. New texts name the edge crossed (`d` and/or `pitch`), the run and the `Lxx`.
**Keep `STANDING_WARNING` first** (lines 55-57); keep the "not a product build" clause (D-15). Fix the stale comment at lines 53-54 ("Phase 6 removes the last clause"). `Counterpart` docstring (139-146) mentions required clearance: update.
Imports go at top beside `from screw.calc.thread import (...)` (line 18); add `from screw.calc.printability import ...`.

---

### `src/screw/params.py` (model, request-response)

**Analog:** itself.

**Current seam** (lines 184-190): replace the comment and `_req(...)` call:
```python
    # D-01, PAIR-01: no default, no lower bound ... until Phase 6 records the printed test.
    clearance: float = _req(
        le=INTERIM_MAX_MM, title="Clearance (radial)", group="Pair", unit="mm", step=0.01,
        help="Radial clearance c in mm: ...")
```
**New helper:** a default-carrying sibling of `_req` with no `gt` (a nominal or interference fit is legal, D-04). Copy `_req` (lines 45-58) body but `Field(default, le=le, allow_inf_nan=False, title=..., description=help, json_schema_extra=extra)`. Do NOT use `_f` (it demands `gt=`, which adds `exclusiveMinimum` and a form `min`; RESEARCH verified app.js:112-115). Default literal comment follows the frozen-default style at params.py 175-178 ("Frozen: every shareable link that omits s or m means these values forever"): cite run id, sha256, profile, `Lxx`. Leave `_req` in place (surgical-edit, Open Question 5). Refusals `void_root_radius_refusal`, `nut_too_thin_refusal` unchanged.

---

### `tests/test_print_rules.py` (test, batch)

**Analogs:** `tests/test_pair.py:84-87` and `tests/test_thread_maths.py:486-520`.

**Re-derivation** (test_pair.py:85-87):
```python
def test_the_expected_verdicts_are_re_derived_from_the_recorded_pair_campaign() -> None:
    derived = pair_expected.render(pair_expected.derive())
    assert derived == pair_expected.TABLE.read_text(encoding="utf-8")
```
**Recompute shipped constant from committed record** (test_thread_maths.py:486-520): parametrized over run ids in a `{run_id: path}` dict, read records, recompute by rule, assert equal to the typed table. For Phase 6: assert `NutParams.model_fields["clearance"].default == print_rules.default_from(load(RUN1))`, and `printability.D_MIN/P_MIN == thresholds_from(load(RUN2))`.
**New (no analog):** synthetic-record controls: smallest all-3/3-and-all-above step; `None` when no step passes; `None` when non-monotone; refusal on incomplete/duplicate/4-sample rows; D-14 boundary (2 of 3 promotes, 1 of 3 does not); protocol counts (60/12/12/9/9) match matrix and template. Imports: `from bench import print_rules, print_matrix` (as `tests/test_pair.py:28`).

---

### Blast-radius test edits (`tests/conftest.py`, `test_parity.py`, `test_params.py`, `test_nut.py`, `test_api.py`, `test_cli.py`)

**Analog:** the existing tests themselves.
- `tests/conftest.py:27`: `REQUIRED_VALUES: dict[str, dict[str, float]] = {"nut": {"clearance": 0.1}}` becomes `{}`; update comment lines 24-26. `part_of` fixture (29-31) already tolerates `{}` via `.get(kind, {})`.
- `tests/test_params.py:69-77` `test_the_clearance_has_no_default_and_a_missing_one_is_refused_naming_it` (asserts `field.is_required()`, `PydanticUndefined`, `"missing"` error): replace with default-literal test; model the neighbour `test_the_frozen_nut_defaults_are_the_iso_4032_m6_row` (lines ~60-67) for the "default read back from the cited source" shape.
- `tests/test_parity.py:184-203, 342-354, 385-388, 970`: keep the planted-required-field test so the generic rule stays honest; remove only the `clearance` special case. `test_the_limits_heading_...` (line ~380-392) passes `--clearance 0.1` / `params={"clearance": 0.1}`; it still works but may drop the extra.
- `tests/test_nut.py:218-251, 322-329`, `test_api.py:145-148`, `test_cli.py:195-212`: rewrite per the table in RESEARCH "Test blast radius".
- New warnings can break exact-list asserts in `tests/test_calc.py` (lines listed in RESEARCH); let `make verify` find them.

---

### `pyproject.toml` (config)

**Analog:** contract "The spike's oracle, verdict and parent process stay free of the CAD kernel" (lines 236-253). Add `"bench.print_rules"` (and `"bench.print_matrix"` if its import part is kernel-free) to `source_modules`:
```toml
source_modules = [
    "bench.thread_spike.maths",
    ...
    "bench.quiet",
    "bench.pair_expected",
]
forbidden_modules = ["cadquery", "OCP"]
```
`screw.calc.printability` is already covered by the `screw.calc` contracts (kernel, logger).

---

### `docs/architecture/decision_log.md` (L17, optional L18)

**Analog:** L16 (line 1186): heading `## L16 — <the decision as a sentence naming the run>`, then `Date:` / decided-by line citing the owner record, a "Why" paragraph, "The rule, fixed before any row ran" citing the module docstring commit, then run narrative. L17: default, M6-M12 range, profile, one-way note (D-07), sizes reading `inconclusive` at the shipped default (Pitfall 2), the stale `PAIR_CLEARANCES` comment (Pitfall 9). L18: `d_min`, `P_min`, run 2.

---

### `bench/RESULTS.md` (doc)

**Analog:** `## Product pair cells (Phase 5, D-07)` (line 6767) and `## Mesh deviation (Phase 5, D-21)`. New `## Printed pair matrix (Phase 6, ...)` section: run id, HEAD sha, profile, record sha256, table of derived result, plus the fresh `screw pair nut --d 8 --pitch 1.25 --s 13 --m 6.8` JSON for D-16 (RESEARCH Pitfall 1).

## Shared Patterns

### Derive, never type
**Source:** `bench/pair_expected.py` + `tests/test_pair.py:85` + `tests/test_thread_maths.py:486`
**Apply to:** the clearance default, `D_MIN`, `P_MIN`, the PAIR-07 verdict. A constant enters the product only through a rule module reading a sha256-pinned record, and a `make verify` test recomputes it.

### Warnings are strings in `PartInfo.warnings`
**Source:** `src/screw/calc/__init__.py` (`derive()`, `_bolt`, `_nut`)
**Apply to:** D-09 and D-13. One producer for UI, API and CLI; no text in JS (`tests/test_parity.py:559,739` pin that `info.warnings` is read once; page uses `textContent`, app.js:404-411). `STANDING_WARNING` first, `off_row` last.

### Kernel-free import boundary lands with the module
**Source:** `pyproject.toml:160-190, 236-253`
**Apply to:** `bench/print_rules.py`, `bench/print_matrix.py`, `src/screw/calc/printability.py`. Same commit as the module (CLAUDE.md).

### Pre-registration order via PRs on `main`
**Source:** 02-SPIKE.md header + Phase 5 `05-01-PLAN.md`/`05-03-SUMMARY.md`
**Apply to:** the protocol, rule module with synthetic tests, blank templates: one PR cut from `origin/main` and landed (`make pr.land`) before print 1. Delete all `GIT_*` env vars in any test that runs git under the hook (05-03 incident).

### Frozen-default comment
**Source:** `src/screw/params.py:175-178`
**Apply to:** the new `clearance` default literal.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| strict hand-filled TSV validator inside `bench/print_rules.py` | utility | file-I/O | existing records are machine JSONL; no hand-typed record parser exists. Use RESEARCH Pitfall 5 and stdlib `csv`. |
| owner-filled run record workflow | process | manual | no earlier physical measurement. Use `05-02-PLAN.md:181` `checkpoint:human-action` and `05-OWNER-READS.md` format for owner-typed inputs. |
| synthetic positive/negative-control tests for a rule over human data | test | batch | closest idea is the spike's controls; write fresh from RESEARCH Validation map. |

## Metadata

**Analog search scope:** `bench/`, `src/screw/{calc,params.py}`, `tests/`, `pyproject.toml`, `docs/architecture/decision_log.md`, Phase 2 and Phase 5 planning docs
**Files scanned:** about 15 read or grepped
**Pattern extraction date:** 2026-10-22
