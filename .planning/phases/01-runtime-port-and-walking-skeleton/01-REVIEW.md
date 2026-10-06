---
phase: 01-runtime-port-and-walking-skeleton
reviewed: 2026-10-06T00:00:00Z
depth: standard
files_reviewed: 47
files_reviewed_list:
  - .github/workflows/ci.yml
  - .github/workflows/required-jobs.txt
  - .pre-commit-config.yaml
  - bench/__init__.py
  - bench/build_time.py
  - bench/corpus.py
  - bench/export_cost.py
  - bench/latency.py
  - bench/memory.py
  - compose.yaml
  - docker/refresh-requirements.sh
  - docker/smoke.py
  - Dockerfile
  - Makefile
  - pyproject.toml
  - requirements.txt
  - scripts/__init__.py
  - scripts/pr_land.py
  - scripts/skip_tokens.py
  - src/screw/__init__.py
  - src/screw/__main__.py
  - src/screw/app.py
  - src/screw/build_errors.py
  - src/screw/calc/__init__.py
  - src/screw/cli.py
  - src/screw/params.py
  - src/screw/pool.py
  - src/screw/records.py
  - src/screw/solid/__init__.py
  - src/screw/solid/bolt.py
  - src/screw/static/app.js
  - src/screw/static/index.html
  - src/screw/static/style.css
  - tests/conftest.py
  - tests/test_api.py
  - tests/test_bench.py
  - tests/test_calc.py
  - tests/test_cli.py
  - tests/test_params.py
  - tests/test_parity.py
  - tests/test_pool.py
  - tests/test_pr_land.py
  - tests/test_records.py
  - tests/test_skip_tokens.py
  - tests/test_solid.py
  - web/entry.js
  - web/package.json
findings:
  critical: 1
  warning: 7
  info: 5
  total: 13
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-10-06
**Depth:** standard
**Files Reviewed:** 47
**Status:** issues_found

## Summary

Reviewed the walking skeleton: the parameter model, the info maths, the solid doorway, the
process pool, the HTTP app, the CLI, the web page, the bench harness, the delivery files and
the merge tooling. The runtime port is careful and mostly sound. The pool/timeout/admission
logic holds up under reading, and `scripts/pr_land.py` and `scripts/skip_tokens.py` raised no
defects.

The serious problem sits where the plan said the safety net is: the solid doorway's "one
valid solid" check does not catch a collapsed solid. Every finding below was reproduced by
running code in `.venv`, except where a finding says it comes from reading only.

Already filed and not repeated: `ui-rounds-displayed-numbers`, `ui-hides-warnings-on-failed-update`,
`ui-drops-foreign-hash-keys`, `bench-memory-sampling-is-too-coarse-for-short-corpora`,
`interim-runtime-bounds`. WR-05 below is a distinct case near the first of these, and is marked.

## Critical Issues

### CR-01: A collapsed thin solid passes the validity check and is served as a 200 with a wrong or missing mesh

**File:** `src/screw/solid/__init__.py:79` (check), `:128-133` (unchecked exporters); `src/screw/params.py:84` (no lower bound on `length`)
**Issue:** `_build` accepts a solid when `len(solid.Solids()) == 1 and solid.isValid()`. For a
tiny `length` the kernel returns a solid that is valid and has one solid but has collapsed to
one face and zero volume. Reproduced with the real kernel and the app (inline backend):

- `GET /api/bolt/model.stl?length=1e-8&quality=preview` returns **200** with a 134-byte STL
  holding **one triangle**, volume 0. The same part's info row still reports the closed-form
  volume (7.85e-05 mm³ at d=100), so the page shows a number for a part that was not built.
- `d=100000&length=1e-7` returns **200** with 14,050 triangles instead of 28,096: the STL is
  not watertight (edge-sharing check fails, signed volume ~1e-16 against a true 785 mm³).
- `GET /api/bolt/model.step?length=1e-8` returns **200**; re-importing the file gives one
  face, `Volume() == 0`.
- `length=1e-9` (any `d`): `exportStl` returns `False` and writes no file, so
  `path.read_bytes()` raises `FileNotFoundError`. It is not a `BuildError`, so `_serve` takes
  its catch-all, logs `build.failed`, and the client gets a **500**. `screw export bolt
  -o x.stl --length 1e-9` prints a raw traceback.

This breaks three standing rules. The solid module promises "one exception type leaves", the
doorway's own comment says the validity check turns degenerate input into a refusal, and L02
says a wrong output is worse than none. `params.py` gives `length` only `gt=0`, so
`length=1e-8` is valid input at the boundary.

**Fix:** Assert the invariant a type cannot express: reject a solid with no volume, and check
the exporters' own results. In `_build`:
```python
if len(solid.Solids()) != 1 or not solid.isValid() or not solid.Volume() > 0:
    raise BuildError("Geometry kernel produced an invalid solid for these parameters.")
```
Still volume-zero below some size, so also give `d` and `length` a physical lower bound in
`params.py` (a 422 naming the field, never a clamp, per L02). In `_write_export`, treat a
`False` from `exportStl` and a non-`IFSelect_RetDone` status from `exportStep` as
`BuildError`, and check that the STL's header count matches `(len - 84) / 50` and is at least
4 before returning it. Add a test with `length=1e-8`.

## Warnings

### WR-01: A repeated query key silently drops one of two explicit values

**File:** `src/screw/app.py:363` (and `:370`, `:349`); `src/screw/cli.py:34`
**Issue:** L02 says a direct conflict between two things the user asked for is a 422 naming
the field. Duplicated keys are such a conflict, and the last one wins silently. Reproduced:
`/api/bolt/info?d=0&d=5` returns **200** with d=5; `?d=5&d=100000` returns **200** with
d=100000; `?d=5&d=0` returns 422 (the 5 is ignored, the 0 is judged). `/api/schema?kind=bolt&kind=x`
returns 404. The CLI behaves the same: argparse takes the last `--d`. The parity success
criterion (a foreign field is refused on every front end) is silent on this.
**Fix:** In the app, refuse a repeated key before validation, for example a small dependency
that compares `len(request.query_params.multi_items())` with `len(request.query_params)` and
raises a 422 `{"loc": ["query", name], "type": "duplicate"}`. In the CLI, use a custom
`argparse.Action` that exits 2 when its dest was already set.

### WR-02: `int_env` clamps zero and negative values to 1 instead of falling back, against its own docstring

**File:** `src/screw/__init__.py:15-19`
**Issue:** The docstring says "falling back on nonsense", but only `ValueError` falls back.
`int("0")` and `int("-5")` succeed and `max(1, ...)` turns them into 1. Reproduced:
`SCREW_BUILD_TIMEOUT=0` or `-5` gives a **1 second** build timeout, which kills almost every
build, terminates the worker and answers 503 `timeout`. `SCREW_PORT=0` becomes port 1, a
privileged port. `SCREW_WORKERS=0` and `SCREW_BUILD_WORKERS=0` become 1 with no message. The
timeout case is the worst: a typo makes the service look broken on the hardware, with no
startup message pointing at the setting.
**Fix:** Return `default` when the parsed value is below 1 (`value = int(...); return value if value >= 1 else default`), and print one warning to stderr naming the variable. Add the zero and negative cases to the `int_env` tests.

### WR-03: The per-build timeout counts queue wait, so a build that never overran is reported as overrunning and kills its worker

**File:** `src/screw/pool.py:170-172`, `:208-214`
**Issue:** `asyncio.wait_for(future, timeout=self.timeout)` starts its clock when the work is
submitted, not when the worker starts it. Under hash affinity up to `MAX_QUEUED_BUILDS` (4)
builds can sit on one single-worker executor. Scenario: A takes 25 s on the slot; B (different
parameters, same slot) is submitted at t=1 and needs 10 s of its own. B starts at t=25 and
would finish at t=35 but its timer fires at t=31. B is answered with "Build exceeded the 30s
per-build timeout" for a 10 s build, the worker is terminated (losing the warm solid cache),
and any C queued behind B gets 503 `pool_broken`. The `build.failed` and `worker.replaced`
records name a timeout that is not the build's. The comments cover C's case, not B's own.
**Fix:** Either start the timer when the worker picks the job up (have the worker report
"started" through a `multiprocessing.Event`/`Queue`), or document the semantics as "timeout
includes queue wait" in the message and the log (`cause` and `queued_ms`). Today's cylinder
builds finish in tens of milliseconds, so this is latent until Phase 3 threaded builds make
builds slow. File a debt item with that trigger if it is deferred.

### WR-04: The STL tessellation is absolute millimetres, so a very small part is silently a coarse prism

**File:** `src/screw/solid/__init__.py:41`, `:128`
**Issue:** `TESSELLATION` uses a fixed linear deflection (`relative=False`) of 0.08 mm
(preview) and 0.01 mm (fine). The model has no lower bound on `d`, so `d=0.001` is valid.
Reproduced: `d=0.001` gives **12 triangles** in both preview and fine, with an STL volume of
63.7 % of the cylinder; `d=0.02` preview gives 28 triangles at 90.0 %. The info panel reports
the exact closed-form volume next to a download that is a square-ish prism. The known item
`interim-runtime-bounds` covers the tessellation numbers being carried from spur; it does not
record this consequence, and a dimension that tiny is reachable today.
**Fix:** Scale deflection to the part (`min(tol, 0.01 * p.d)`-style, chosen and measured), or
give `d` a lower bound so no admitted part is below the tessellation floor, or have the info
document warn when the STL deviates from the exact solid by more than a stated fraction. Raise
it with the owner; it is a tessellation decision.

### WR-05: The UI's number formatter prints a wrong magnitude for a large `pitch`, and `pitch` has no upper bound

**File:** `src/screw/static/app.js:18`; `src/screw/params.py:65`
**Issue:** Distinct from the filed rounding item, which is about three-decimal rounding. Here
`fmt` corrupts the *exponent*: `Number(v).toFixed(3)` returns `"1e+100"` for values at or above
1e21, and the trailing-zero regex then strips the exponent's zeros. Measured in node:
`fmt(1e100) === "1e+1"`, `fmt(1e200) === "1e+2"`, `fmt(2.5e30) === "2.5e+3"`. `pitch` is
`gt=0` with no `le`, and `tests/test_params.py::test_pitch_has_no_upper_bound` pins that, so
`#pitch=1e100` is accepted by the API and the page shows "Pitch 1e+1 mm", a plausible,
wrong, ten-orders-off number (L02).
**Fix:** Stop reformatting server numbers, as the filed item proposes (`String(row.value)`).
Independently, bound `pitch` at `INTERIM_MAX_MM` like `d` and `length`, and update the pinned
test.

### WR-06: `bench.memory sweep` returns success and prints a peak for a run where every request failed

**File:** `bench/memory.py:269` (and `_drive_corpus`, `:131-146`)
**Issue:** `sweep()` returns `all(row.peak_bytes is not None ...)`. A row's `failures` count
is ignored. If the container is healthy but every corpus request fails (a 500, a 503 storm,
`/tmp` not writable), the recorded "peak" is the idle interpreter floor, the table shows it
with `Failures: 12`, and the exit code is 0. That is a plausible wrong number being offered
as a memory measurement (L02), in the harness whose output Phase 7 sets `mem_limit` from.
`confirm()` does check `failures == 0`; `sweep()` does not.
**Fix:** Return `all(row.peak_bytes is not None and row.failures == 0 for row in rows)`, and
print the peak as `(none -- N of M requests failed)` for a row with failures, the same way a
capped row is refused.

### WR-07: `screw export` leaves a raw traceback for an unwritable output path, and validates parameters only after loading the kernel

**File:** `src/screw/cli.py:86-91`
**Issue:** `out.write_bytes(data)` is unguarded: `screw export bolt -o /nonexistent/x.stl`
prints a `FileNotFoundError` traceback instead of `error: ...` and exit 1, unlike every other
failure in this command (reproduced). Separately, `_params()` runs after `from .solid import
...`, so a bad value (`--d 0`) costs the roughly 2 s kernel import that the comment at line 80
says the extension check avoids.
**Fix:** Call `p = _params(ns.kind, ns)` before the lazy imports, and wrap the write:
```python
try:
    out.write_bytes(data)
except OSError as exc:
    raise SystemExit(f"error: cannot write {out}: {exc.strerror}") from None
```

## Info

### IN-01: `quality` is accepted on STEP, does nothing, and doubles the build

**File:** `src/screw/app.py:370-373`, `:392`
**Issue:** `model.step?quality=preview` is accepted. STEP bytes are identical for both values,
but `quality` is part of the cache key `(params, fmt, quality, encoding)`, so the same part is
built, held and gzipped twice. It is also a parameter the user set that silently has no effect
(L02).
**Fix:** Normalise `quality` to a fixed value for `fmt == "step"` in the key, or refuse it on
the STEP route with a 422.

### IN-02: `slug()` uses `%g`, so distinct parts get the same download name

**File:** `src/screw/params.py:75`
**Issue:** `%g` keeps 6 significant digits. `BoltParams(d=6.0000001)` and `BoltParams(d=6.0000002)`
are different parts (unequal, different cache keys) with the identical slug
`bolt_d6_pitch1_length20`, so two downloads overwrite each other or look the same.
**Fix:** Use `repr(float)` (still filename-safe: digits, `.`, `e`, `+`, `-`) or document the
collision.

### IN-03: The `Accept-Encoding` test ignores `q=0` and case

**File:** `src/screw/app.py:390`
**Issue:** `"gzip" in header` treats `gzip;q=0` ("not acceptable") and any header containing
the substring as a request for gzip, and misses `GZIP`. The code comment says it matches
Starlette's own test, so endpoint and middleware agree, but both disagree with RFC 9110 for a
client that sets `q=0`.
**Fix:** Parse the header once for a `gzip` coding with non-zero q, and have the endpoint own
the decision (it already sets `Content-Encoding`, which makes the middleware pass through).

### IN-04: A malformed `#d=abc` link and an emptied field build the default silently

**File:** `src/screw/static/app.js:150-158`
**Issue:** `partQuery()` skips an empty value. A cleared field, or one the browser sanitises to
`''` (for example a stray `1e`), builds the default part while the box stays blank, and
`writeHash` then rewrites the link without the key. The filed `ui-drops-foreign-hash-keys`
item covers foreign keys and the `#d=abc` hash case; the live-typing case (a blank field
building the default) is not named there.
**Fix:** When `input.value === ''` and `input.validity.badInput` or a required field is blank,
show "Diameter: enter a number" in `#messages` and skip the build, instead of sending the default.

### IN-05: CI and delivery nits

**File:** `.github/workflows/ci.yml:60-66`, `Makefile:worktree.land`, `Dockerfile:3`
**Issue:** (a) The `image` job never prints `docker logs screw` when the health loop times out
or a curl fails, so a red run has no server output. (b) `make worktree.land` expands `$(MSG)`
inside double quotes in a shell command, so a message containing `"`, `$(` or a backtick is
executed by the shell (local developer tool, self-inflicted). (c) The base image is a floating
tag (`python:3.12-slim-bookworm`) beside a fully pinned `requirements.txt`; L06's closure
pinning stops at pip.
**Fix:** (a) add a final `if: failure()` step running `docker logs screw`. (b) pass the message
through the environment (`MSG='$(MSG)' ...` quoted with `printf %q`, or write it to a temp file
and use `git commit -F`). (c) pin the base image by digest, or note the choice in the decision
log.

---

_Reviewed: 2026-10-06_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
