---
phase: 04-iso-hex-bolts-and-screws
reviewed: 2026-10-12T00:00:00Z
depth: standard
files_reviewed: 33
files_reviewed_list:
  - src/screw/app.py
  - src/screw/calc/__init__.py
  - src/screw/calc/presets.py
  - src/screw/calc/thread.py
  - src/screw/cli.py
  - src/screw/params.py
  - src/screw/solid/__init__.py
  - src/screw/solid/bolt.py
  - src/screw/solid/helical.py
  - src/screw/static/app.js
  - src/screw/static/index.html
  - src/screw/static/style.css
  - src/screw/tables/__init__.py
  - src/screw/tables/iso262.py
  - src/screw/tables/iso4014.py
  - src/screw/tables/iso4017.py
  - src/screw/tables/presets.py
  - src/screw/tables/rows.py
  - bench/corpus.py
  - bench/head_fuse.py
  - pyproject.toml
  - tests/test_api.py
  - tests/test_bench.py
  - tests/test_calc.py
  - tests/test_cli.py
  - tests/test_import_boundaries.py
  - tests/test_params.py
  - tests/test_parity.py
  - tests/test_presets.py
  - tests/test_solid.py
  - tests/test_tables.py
  - tests/test_tables_second_entry.py
  - tests/test_thread_maths.py
findings:
  critical: 1
  warning: 2
  info: 4
  total: 7
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-10-12
**Depth:** standard
**Files Reviewed:** 33
**Status:** issues_found

## Summary

All source files in scope were read in full. The test files were read only where they
bear on a claim (`test_tables_second_entry.py`, `test_import_boundaries.py`,
`test_presets.py`); the gate is green at HEAD and the full suite was not re-run.

Checked and found sound:

- The ISO row data. The ISO 4014 `lg,max = l - b` and `ls,min = lg,max - 5P` relation holds for
  all 108 cells. Every cell was recomputed by hand and uses the right `b` band (`b_short` for
  l <= 125, `b_long` above). Head values and the DIN wrench-size note constants agree with the
  figures I know for ISO 4017/4014 and DIN 931/933. I could not check them against the purchased
  text.
- The import boundaries. `screw.params` and `screw.solid` load no table, and `calc.presets`
  reaches the tables only through `_bolt`'s inner import.
- The decimal-exact turn arithmetic and the largest-accepted-pitch truncation.
- `/api/bolt/info` under 2400 hostile parameter combinations (subnormals, 1e-300, 1e5, sub-`MIN_TAIL_MM`
  lengths and threads). The result was 422 or 200 every time, never a 500, and never a non-finite
  number in a row.
- Kernel builds of small and degenerate inputs (`k` down to 1e-100, thread lengths from 0.0011
  mm, a left-hand M20 x 200 row, `s = d + 1e-4`). All built or raised `BuildError`; none crashed.
- The web page's DOM writes. Every one goes through `textContent`, and `currentKind` is checked
  against the registry before it is used in a URL.

One defect breaks an explicit project contract. Two are quality defects in how that contract and
its evidence are built. The Info items are small.

## Critical Issues

### CR-01: The `thread_length`/`length` 422 is silently skipped under `screw serve --root-path`

**File:** `src/screw/app.py:210-212`
**Issue:** `refuse_thread_length_conflict` decides whether a request is a bolt route with
`request.url.path.startswith("/api/bolt/")`. uvicorn prepends the configured root path to
`scope["path"]` (`uvicorn/protocols/http/h11_impl.py:206-216`, uvicorn 0.54.0). `request.url.path`
is built from that value, so behind a prefix-stripping reverse proxy the path reads
`/screw/api/bolt/info` and the check is false. `screw serve --root-path` and `SCREW_ROOT_PATH`
are shipped, documented flags (`cli.py:192`).

I reproduced it against the app with the ASGI scope uvicorn would build:

```
TestClient(app, root_path="/screw").get("/screw/api/bolt/info?length=10&thread_length=30")
-> 200   (a 10 mm thread; the same query without a root path is a 422 thread_length_conflict)
```

An explicit conflict between two values the user asked for (L02, D-25, the module docstring's
promise) is answered with a built part that differs from the request. A warning is added, but
the contract is a 422 naming the fields. `/api/bolt/model.stl` and `model.step` are affected the
same way. No test sets a root path (`grep root_path tests/` finds only the `serve` argument
check in `test_cli.py:270`).

**Fix:** Test the route, not the raw URL path. Either strip the root path:

```python
path = request.url.path.removeprefix(request.scope.get("root_path", ""))
if not path.startswith("/api/bolt/") or not ("length" in query and "thread_length" in query):
    return
```

or, better, read the matched route (`request.scope["route"].path`) so no prefix arithmetic is
involved. Add a regression test that sends `/screw/api/bolt/info?...` with `root_path="/screw"`
and asserts 422.

## Warnings

### WR-01: `bench/head_fuse.py` does not fuse in the order the shipped builder does, yet claims to measure what ships

**File:** `bench/head_fuse.py:65-85` (against `src/screw/solid/bolt.py:39-49`)
**Issue:** The shipped assembly is `thread.fuse(shank).fuse(head)`. The probe builds
`thread.fuse(shank.fuse(head))` (`_head_and_shank` fuses shank and head first, `assemble` then
fuses that onto the thread). The module docstring says "The thread is the shipped builder's ...
so what is measured is what ships", and `bench/RESULTS.md` ("Head fuse probe") is the D-03
evidence for building the head this way. Only the thread is shared. The solid count, validity,
volume error and mesh closedness recorded there describe a different boolean sequence from the
one `_build` runs. The gate in `_build` still protects users; the defect is that the recorded
evidence does not cover the code it is cited for. The probe also keeps a second copy of the
head and shank construction that can drift from `bolt.assemble`.

**Fix:** Have the probe call the shipped `assemble`. Build a `BoltParams` per case (the cases
already satisfy the validators) and use the shipped `thread` and `assemble`. If the probe must
stay free of `screw.params`, copy the shipped order exactly and say so. Re-run the probe and
update the RESULTS table if the numbers move.

### WR-02: Kind-specific rules are hard-coded into the generic request and CLI paths

**File:** `src/screw/app.py:198-220`, `src/screw/cli.py:98-104`
**Issue:** `params.py` promises that adding a kind is "one class and one registry entry, never
an edit to the form or the flag generator". Two code paths now break that promise:

- `refuse_thread_length_conflict` is an app-level dependency, so it runs on every route. It
  hard-codes the prefix `"/api/bolt/"` and the field names `length` and `thread_length`.
- `cli._params` is the generic, registry-driven parameter builder. It reads `values.get("length")`
  and `values.get("thread_length")` for every kind and applies the bolt's rule.

A second kind (a nut, a threaded rod) that has its own `length` or `thread_length` either escapes
the rule silently (a different route prefix) or is judged by the bolt's rule (the CLI). There is
no registry hook that says which kinds own the rule. This is also how CR-01 got in: the path
test is the weak part of a coupling that should not be needed.

**Fix:** Make the rule a property of the kind, as `derive` and `download_refusal` already are.
For example, add an `explicit_conflict(values: Mapping[str, float]) -> str | None` function in
`screw.calc`, dispatched with `isinstance` like `download_refusal`. The dependency would resolve
the kind from the matched route (as CR-01's fix does), and `_params` would call the same function.

## Info

### IN-01: Production `assert` statements guard data and kernel invariants

**File:** `src/screw/tables/presets.py:117`, `src/screw/solid/bolt.py:37,43`
**Issue:** `assert b is not None, cell` is the only guard that a cell above 125 mm has a
`b_long`. `python -O` removes it, and a missing second band would then become a `None` thread
length and a pydantic error far from the table. The two `isinstance` asserts in `bolt.py` have
the same property, but those are pre-existing kernel-typing narrowing. A test pins the data
invariant today, so this is a hardening point only.
**Fix:** `if b is None: raise ValueError(f"no second thread band for {cell}")` in
`tables/presets.py`.

### IN-02: The page's Download STL link fetches the fine STL, which is refused for 62 of the picker's presets

**File:** `src/screw/static/app.js:385-396` (with `src/screw/calc/__init__.py:170-183`)
**Issue:** `setDownloads(q)` builds `api/bolt/model.stl?<q>` with no `quality`, so the server's
default `fine` applies. `tests/test_presets.py:142-157` pins 62 ISO 4017 catalogue rows whose
fine STL is refused with a 422 (D-02). Picking one of them and clicking Download STL navigates to
a JSON error; only the info warning explains it. The warning is present and this is the owner's
D-02 trade-off, so it is not a correctness defect. Roughly a fifth of the picker is a dead-end
click on the primary action.
**Fix:** When the newest info document carries the cap warning, either point the STL link at
`quality=preview` or disable it with a title that names the cap. The page should not parse warning
text to do this. A structured field on `PartInfo` (for example `fine_stl_refused: bool`) would be
a cleaner signal.

### IN-03: The same edit gives a 422 or a warning depending on whether `thread_length` equals the default 20

**File:** `src/screw/static/app.js:308-321` (with `src/screw/calc/__init__.py:87-104`)
**Issue:** `partQuery()` omits any field equal to its default. A user who types `thread_length`
20 into the form and then lowers `length` to 12 sends `length=12` only. The API sees no explicit
`thread_length`, so it builds a 12 mm thread and warns `thread_length 20 (default) exceeds length
12`. With `thread_length` 21 the query carries both keys and the answer is a 422. This follows
from D-25 and the link-stability rule, and the docstring of `_thread_length_warning` describes
the API and CLI half. It is not recorded as a known UI divergence, so a user cannot predict which
answer they get.
**Fix:** Record the divergence next to D-25 in the decision log and the UI-SPEC. If it is not
acceptable, send `thread_length` whenever the control holds a user-typed value, which needs a
dirty flag per field.

### IN-04: The `thread` parameter of `assemble` shadows the module-level `thread` function

**File:** `src/screw/solid/bolt.py:30` (also the local `thread` in `src/screw/solid/__init__.py:126`)
**Issue:** `def assemble(p, thread: cq.Solid)` hides `bolt.thread` inside the function. It is
harmless today, but any later call to the builder from inside `assemble` would hit the solid.
**Fix:** Rename the parameter to `rod` or `threaded`.

---

_Reviewed: 2026-10-12_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
