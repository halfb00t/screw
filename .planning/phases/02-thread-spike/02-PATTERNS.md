# Phase 2: Thread Spike - Pattern Map

**Mapped:** 2026-10-06
**Files analyzed:** 16 new or modified
**Analogs found:** 14 / 16 (all analog paths verified git-tracked; `../spur/...` paths are a sibling repo, read-only house-style reference per CLAUDE.md)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `bench/quiet.py` | utility (host gate) | request-response (pure fn, injected effects) | `bench/__init__.py` (kernel-free, typed, docstring-why) + spur `session.py:296-319` (semantics, in RESEARCH Ex. 2) | role-match |
| `bench/thread_spike/__init__.py` | config (package docstring) | n/a | `bench/__init__.py` | exact |
| `bench/thread_spike/maths.py` | utility (kernel-free oracle) | transform | `bench/corpus.py` (deterministic written-out grid, kernel-free) + `src/screw/calc/__init__.py` (pure maths, `from __future__`) | role-match |
| `bench/thread_spike/verdict.py` | utility (pure predicates) | transform | `bench/export_cost.py` `_decisions`/`select_gzip_level` (rule as pure function on rows) + `bench/build_time.py` `Timing.inside` | exact |
| `bench/thread_spike/helical.py` | service (kernel builder) | transform | `src/screw/solid/__init__.py` `_build` + postcondition | role-match |
| `bench/thread_spike/measure.py` | utility (kernel measure, STL, STEP) | file-I/O | `bench/export_cost.py` `_run_child` + `bench/build_time.py` `stl_size` | exact |
| `bench/thread_spike/pair.py` | service (kernel boolean) | request-response | none in repo (RESEARCH Ex. 5) | no analog |
| `bench/thread_spike/worker.py` | service (JSON-lines child) | event-driven / request-response | `bench/export_cost.py` `--child` + `_ChildPayload` | role-match |
| `bench/thread_spike/__main__.py` | controller (CLI report, exit 1 on verdict) | batch | spur `bench/tip_chamfer_spike.py` `main` + `bench/build_time.py` `report`/`main` | exact |
| `bench/RESULTS.md` (new `## Thread spike (Phase 2)`) | docs | n/a | `bench/RESULTS.md` Phase 1 entries (lines 16-60) | exact |
| `tests/test_bench.py` (new cases) | test | transform | the same file, lines 48-142 | exact |
| `pyproject.toml` (import-linter) | config | n/a | `pyproject.toml` `[tool.importlinter]` contract 2 | exact |
| `Makefile` (`bench.thread`) | config | n/a | `Makefile` `bench.build` / `bench.export` | exact |
| `.planning/phases/02-thread-spike/02-SPIKE.md` | docs (protocol) | n/a | spur `13-LATENCY-INVESTIGATION.md` (Question, Environment, Method, Predictions, Results) | exact |
| `docs/architecture/decision_log.md` (L11) | docs | n/a | existing `L10` entry (last, line ~264) | exact |
| container pass entry (`--container-pass`) | utility | batch | none (RESEARCH Ex. 7 is the shape) | no analog |

## Pattern Assignments

### `bench/thread_spike/__init__.py`, `bench/quiet.py` (module shape)

**Analog:** `bench/__init__.py` (lines 1-44) and `bench/corpus.py` (1-36)

Every bench module opens with a docstring stating what it is and what it is NOT (not a bound, not in `make verify`), then `from __future__ import annotations`, stdlib imports, full type hints, `-> None`/`-> float` everywhere, no `Any`.

```python
"""Measurement harness, ported from spur's `bench/` (L07: "as a harness, not as numbers").
...None of them is part of `make verify`: they need minutes ... a timing assertion on shared
hardware would flap until someone stopped believing it.
"""

from __future__ import annotations

import os
import platform
```

Kernel-free modules must not import `bench.build_time` (it pulls `screw.solid` and cadquery). `bench/corpus.py:30-34` states this rule and why. Copy the docstring habit: the why carries the measurement or constraint.

`wait_quiet` body: copy RESEARCH.md Code Example 2 verbatim (frozen dataclasses `Reading(utc, load1)`, `QuietResult(decisive, readings)`, injected `read/sleep/now/clock`). Production wiring: `read=lambda: os.getloadavg()[0]`.

---

### `bench/thread_spike/verdict.py` (utility, pure rule predicates)

**Analog:** `bench/export_cost.py`

**Rule-as-pure-function pattern** (lines 111-138): integer arithmetic decides a bar, floats only for printing, comment states why.

```python
        shrunk = 10 * (current.out_bytes - candidate.out_bytes) >= current.out_bytes
        wall_ok = candidate.concurrent_ms <= 1.5 * current.concurrent_ms
        adopted = shrunk and wall_ok
```

**Frozen row dataclass with no defaults** (`bench/build_time.py:33-55`): a default 0 would be a plausible fake number (L02).

```python
@dataclass(frozen=True)
class Timing:
    label: str
    build: float
    ...
    # No defaults on the two fields above: a default 0 would be a plausible-looking fake STL
    # size for a row nobody actually measured (L02).

    @property
    def worst_request(self) -> float:
        return self.build + max(self.stl, self.step)

    def inside(self, timeout: float) -> bool:
        return self.worst_request <= timeout
```

Apply to: row record (`ok / silent_wrong / failure / timeout / worker_died`), over-budget vs failure separation, escape-clause, K rule, estimator rule, pair rule, protocol guard (git output injected, as `report()` takes `load` as an argument: `bench/build_time.py:117-131`, test at `tests/test_bench.py:134-142`).

---

### `bench/thread_spike/maths.py` (utility, kernel-free oracle)

**Analog:** `bench/corpus.py` (written-out deterministic grid + `label()`), `src/screw/calc/__init__.py` (pure-maths module docstring and `math` use).

```python
"""The numbers the tool prints about a part: pure maths, free of the CAD kernel and the logger.
...A value that cannot be computed honestly is left out ... never a plausible number (L02, D-15).
"""
from __future__ import annotations
import math
```

Core content: copy RESEARCH.md Code Examples 1 (exact `Fraction` grid) and 3 (`area`, `interference_area`). Use `corpus.label()` for label text rather than re-writing it. Pin counts (1790 lengths per hand, per-size counts in RESEARCH Pattern 1) in a test, the way `tests/test_bench.py:48-56` pins the skeleton corpus.

---

### `bench/thread_spike/helical.py` (service, kernel builder)

**Analog:** `src/screw/solid/__init__.py` lines 62-74 (`_build` postcondition) and `src/screw/solid/bolt.py` (builder shape; not read, same package)

```python
def _build(p: FastenerParams) -> cq.Solid:
    ...
    # An invariant a type cannot express is asserted positively: exactly one valid solid.
    if len(solid.Solids()) != 1 or not solid.isValid():
        raise BuildError("Geometry kernel produced an invalid solid for these parameters.")
    return solid
```

This gate is exactly the C1 hole (CONTEXT code_context). The spike's row record must NOT copy it as a verdict; it records solids, `isValid()`, precise volume, signed rel err (RESEARCH Pattern 2, Example 4) and classifies. Vendor types stop at the row record: return plain floats/ints, wrap OCP returns in `float()` (RESEARCH Ex. 4, A7). Builder body: STACK.md § Reference implementation (not in the repo source; per CONTEXT specifics), parameterised by K. Naive sweep+fuse recipe: RESEARCH Pitfall 9, kept in this package for Phase 3's gate test. Keep the words TODO/FIXME/XXX/HACK/NotImplementedError out (`make no-fake-done`).

---

### `bench/thread_spike/measure.py` (utility, file-I/O)

**Analog:** `bench/export_cost.py` `_run_child` (lines 163-190) and `src/screw/solid/__init__.py` `_write_export` (lines 118-140)

**Mesh a copy, temp dir, shipped parameters:**
```python
shape = solid.build(params)
tol, ang = solid.TESSELLATION["fine"]
with tempfile.TemporaryDirectory(prefix="screw-export-cost-") as d:
    path = Path(d) / f"{params.slug()}.stl"
    t0 = time.perf_counter()
    shape.copy().exportStl(str(path), tolerance=tol, angularTolerance=ang,
                           ascii=False, relative=False)
    export_ms = (time.perf_counter() - t0) * 1000
    data = path.read_bytes()
n_bytes, n_triangles = stl_size(data)
peak = maxrss_bytes(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, platform.system())
```
Spike differences: build the solid directly (no `screw.solid.build`), read RSS right after mesh+gzip and BEFORE the STL check (RESEARCH Pitfall 5), STEP via `shape.exportStep(str(path))` (`solid/__init__.py:139`). Import `stl_size` from `bench.build_time` and `TESSELLATION` from `screw.solid` only in kernel modules (never maths/verdict). Reuse `gzip_rows`, `select_gzip_level`, `maxrss_bytes` from `bench.export_cost` (`export_cost.py:76,82,140`); level 9 per size-max rows only.

---

### `bench/thread_spike/worker.py` (service, JSON-lines child)

**Analog:** `bench/export_cost.py` `_ChildPayload` (lines 24-32) and parent spawn (lines 258-275)

```python
class _ChildPayload(TypedDict):
    """The one JSON line `--child` prints: the wire shape ... typed so the parent reads it
    without an `Any` (L04)."""
    export_ms: float
    peak_rss_bytes: int
    bytes: int
    triangles: int
```
```python
child = subprocess.run(
    [sys.executable, "-m", "bench.export_cost", *sweep_args, "--set", args.label, "--child", mode],
    capture_output=True, text=True, check=False)
if child.returncode != 0 or not child.stdout.strip():
    sys.stderr.write(child.stderr)
    raise SystemExit(f"error: --child {mode} run {run} exited {child.returncode} without a payload ...")
child_payload: _ChildPayload = json.loads(child.stdout.strip().splitlines()[-1])
```
Differences: the spike worker is persistent (request line in, record line out, hard timeout, kill and respawn; `Popen`, list argv, no shell, JSON only, `TypedDict` schema, unknown keys refused). One failure there is `failure`, nonzero/negative return is `worker_died`, timeout is `timeout`. Use fresh children (this analog as-is) only for per-row RSS rows.

---

### `bench/thread_spike/__main__.py` (controller, Markdown report, exit 1 on failed verdict)

**Analog:** `bench/build_time.py` `report`/`main` (117-195) plus spur `bench/tip_chamfer_spike.py:304-386`

**Header block** (build_time.py:123-141): kernel versions, `git rev-parse --short HEAD`, `machine_facts()`, load read by the CALLER before row 1 and passed in.
```python
versions = ", ".join(f"{dist} {metadata.version(dist)}" for dist in ("cadquery", "cadquery-ocp"))
head = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                      capture_output=True, text=True, check=True).stdout.strip()
...
f"- Machine: {machine_facts()}", f"- Kernel: {versions}", f"- HEAD: `{head}`",
f"- Load averages at start: {load1:.2f}, {load5:.2f}, {load15:.2f}",
```
Spike difference: replace the single reading with `wait_quiet` readings, each labelled with its `utc`, printed at start AND at end (end labelled "includes this run's own load").

**Empty-sweep refusal** (build_time.py:119-122): raise rather than print an empty table.

**Compute everything, then verdict** (spur tip_chamfer_spike.py:326-330, 366-384):
```python
# Time and print everything before deciding: every row ... is computed here, before the
# verdict below reads any of them.
...
print("### Verdict")
if not reasons:
    print(f"**Verdict:** held -- ...")
    return 0
print(f"**Verdict:** FAILED -- {'; '.join(reasons)}.")
return 1

if __name__ == "__main__":
    sys.exit(main())
```
CLI shape: `argparse.ArgumentParser(prog="bench.thread_spike", ...)` (build_time.py:161-174), `main(argv: list[str] | None = None) -> int`. Validate run ids with a regex and resolve output paths under `bench/` (RESEARCH security table). Protocol guard exit code 2 mirrors `find_set` (`export_cost.py:150-159`: stderr message, `raise SystemExit(2)`).

---

### `tests/test_bench.py` (new cases: quiet, grid, verdict, rules, closed form, protocol guard, smoke)

**Analog:** same file, lines 1-60, 96-142

- Module docstring says how to run (`.venv/bin/python -m pytest tests/test_bench.py -q`; `bench` not installed, root on `sys.path`). Add the spike's imports to the existing `from bench...` import block (lines 25-47); keep the file's isort order.
- Test names are full sentences stating the rule; docstrings give the why and use a made-up value that proves the injected path (lines 134-142: `99.99` load).
- Pin grid like lines 48-56 (`corpus() == [...]` written out).
- Negative/positive-control style, `pytest.raises(ValueError, match="184")` (lines 103-109).
- Predicates only; no timing assertion (D-15). One real-kernel smoke row (M6, 5 turns).
- Use synthetic rows with injected readings for `wait_quiet`: `[1.4,1.4,1.4]` decisive, exact `1.5` resets, never-quiet cap gives 31 readings (RESEARCH Ex. 2).

---

### `pyproject.toml` (import-linter contract)

**Analog:** `pyproject.toml` lines 142-160 (contract 2, the kernel-free contract)

```toml
[tool.importlinter]
root_package = "screw"
include_external_packages = true
...
[[tool.importlinter.contracts]]
name = "The thread maths stays free of the CAD kernel"
type = "forbidden"
source_modules = ["screw.calc", "screw.params", "screw.cli"]
forbidden_modules = ["cadquery", "OCP"]
allow_indirect_imports = true
```
Edit: change `root_package = "screw"` to `root_packages = ["screw", "bench"]` (RESEARCH Pattern 8) and add a contract with `source_modules = ["bench.thread_spike.maths", "bench.thread_spike.verdict", "bench.quiet"]`, same forbidden list. Decide `allow_indirect_imports`: `bench.corpus` was KEPT and `bench.build_time` BROKEN by a transitive chain in the scratch run, so omit `allow_indirect_imports = true` for the new contract (indirect reach is the failure). Re-run `make lint-imports` in the same commit (CLAUDE.md). Contract 8 (lines 200-205, `source_modules = ["screw"]`) is unaffected: bench is outside it, as `bench/build_time.py` already is.

---

### `Makefile` (`bench.thread`)

**Analog:** `Makefile` lines 30, 155-161

```make
	    bench bench.build bench.export bench.latency bench.memory      # .PHONY (line 30): add bench.thread
# Needs no service: it times screw.solid in-process, the code a worker runs.
bench.build: $(STAMP)  ## build, fine STL and STEP time per corpus part vs SCREW_BUILD_TIMEOUT; SWEEP=<json> optional
	$(PY) -m bench.build_time $(SWEEP)
```
Add `bench.thread: $(STAMP)  ## <one-line help>` with a preceding comment saying why it is outside the gate; `$(PY) -m bench.thread_spike $(ARGS)`. `typecheck` (line 60) already covers `bench`.

---

### `bench/RESULTS.md` (`## Thread spike (Phase 2)`)

**Analog:** `bench/RESULTS.md` lines 16-60 (Phase 1 entries) and spur RESULTS.md "Tooth-tip chamfer spike (Phase 10, D-05)"

Shape: section banner "not a bound (L07)", one host line (machine, OS, date), per-run paragraph "Run <UTC>, native arm64, in-process, load averages ... at start (other projects were running; not an idle machine). Output verbatim:" then a fenced block of the header and table. Add run id, decisive/non-decisive release table with timestamps (spur "Phase 13 investigation sessions"). Per RESEARCH Open Question 5 (needs owner nod): per-size aggregates plus every non-ok row verbatim, JSONL path and sha256 for the rest.

---

### `02-SPIKE.md` and decision entry `L11`

**Analogs:** spur `.planning/milestones/v0.3-phases/13-latency-bar/13-LATENCY-INVESTIGATION.md` headings (`## Question`, `## Environment`, `## Method`, `## Predictions`, `## Results`); `docs/architecture/decision_log.md` L10 entry for format. Protocol must end with a stub `## Results` heading (the guard's boundary, RESEARCH Pattern 6). Inputs to pre-register: RESEARCH "Protocol Inputs the Planner Must Pre-register" table. Read the L10 entry for the exact field layout before writing L11.

---

## Shared Patterns

### INTERIM and UNVERIFIED labelling, no plausible numbers
**Source:** `src/screw/solid/__init__.py:35-39`, `bench/export_cost.py:102-107`
```python
# INTERIM (D-01): (linear deflection mm, angular deflection rad) for STL tessellation.
# Carried from spur model.py:53 ... not measured for screw. Phase 5 re-chooses it ...
```
**Apply to:** every ISO preview value (pitches, ISO 4017 cap, nut heights, chamfer angle): label UNVERIFIED in code comments, report and RESULTS. Print sign explicitly (`{delta:+.1f}`, export_cost.py:293-296).

### Header + load before first row, measurement not a bound
**Source:** `bench/build_time.py:117-141`, `bench/export_cost.py:216-232`
**Apply to:** `__main__.py`, container pass, RESULTS entries.

### Typed wire shapes, no `Any`
**Source:** `bench/export_cost.py:24-32` (`TypedDict`), `float(...)` wrapping OCP returns.
**Apply to:** worker/parent protocol, measure.py.

### Subprocess hygiene
**Source:** `bench/build_time.py:125-128`: list argv, `capture_output=True, text=True, check=True`.
**Apply to:** git calls in the protocol guard, worker spawn, `docker run`.

### Fail loud on an unmeasured value
**Source:** `bench/build_time.py:87-94` (`stl_size` refuses a length/header mismatch), `:119-122` (empty sweep).
**Apply to:** skipped STL checks counted visibly, never reported as pass.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `bench/thread_spike/pair.py` | service | request-response | No boolean pair check exists in `src/` or `bench/`; use RESEARCH Pattern 5 and Code Example 5 (keep `op`/filler refs alive, `os._exit(0)` in worker) |
| container `--container-pass` | utility | batch | No existing container-run bench path for kernel code; `bench/memory.py` manages containers via `docker compose` (read it for subprocess style) but not `docker run --entrypoint python -v bench:ro`; use RESEARCH Example 7 |

## Metadata

**Analog search scope:** `bench/`, `tests/test_bench.py`, `src/screw/solid/`, `src/screw/calc/`, `Makefile`, `pyproject.toml`, `../spur/bench/tip_chamfer_spike.py`, spur `13-LATENCY-INVESTIGATION.md` headings
**Files scanned:** about 14 read in full or by range
**Not read in full:** `bench/memory.py`, `bench/latency.py`, `src/screw/solid/bolt.py`, spur `session.py` (semantics taken from RESEARCH.md citation)
**Tracked-source gate:** all in-repo analog paths confirmed in `git ls-files`; no mirror paths
**Pattern extraction date:** 2026-10-06
