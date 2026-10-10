# A collapsed thin solid passes the validity check and is served as a 200

Severity: blocker
Status: resolved
Date: 2026-10-06
Resolved in: fix(solid): refuse a broken export and close the collapsed-solid blocker (this commit; plan 03-07 names its sha)
Source: Phase 1 code review (01-REVIEW.md CR-01). Owner sign-off 2026-10-06: file now, fix in the
`/gsd-quick` PR that follows the Phase 1 close PR — not deferred to a phase.
Related files:
- src/screw/solid/__init__.py:79 (`len(solid.Solids()) == 1 and solid.isValid()` accepts a zero-volume solid)
- src/screw/solid/__init__.py:128-133 (`exportStl` / `exportStep` results are not checked)
- src/screw/params.py:84 (`length` has `gt=0` and no physical lower bound; `d` likewise)

## Context
For a tiny `length` the kernel returns a solid that is "valid" and has one solid but has
collapsed to one face with zero volume. Reproduced with the real kernel on 2026-10-06:
`GET /api/bolt/model.stl?length=1e-8&quality=preview` is a 200 with a 134-byte STL of one
triangle while the info panel still shows the closed-form volume; `d=100000&length=1e-7` is a
200 with 14,050 triangles instead of 28,096 and is not watertight; `model.step?length=1e-8`
re-imports as one face, `Volume() == 0`; `length=1e-9` makes `exportStl` return `False` and
write no file, so `path.read_bytes()` raises `FileNotFoundError` — not a `BuildError` — and
the API answers 500 while `screw export bolt -o x.stl --length 1e-9` prints a raw traceback.

## Why it matters
Silent partial success: a 200 carrying a mesh that is not the part, beside an info document
that is. L02 says a wrong output is worse than none; the solid module promises that one
exception type leaves it and that the validity check turns degenerate input into a refusal.
The skeleton is internal (D-06), which is why this is filed rather than blocking the close,
but the API is live on every `make serve`.

## Next step
In `_build`, refuse a solid whose `Volume()` is not > 0 with `BuildError`; treat `False` from
`exportStl` and a non-`IFSelect_RetDone` status from `exportStep` as `BuildError`; check the
STL header triangle count against `(len - 84) / 50` and at least 4 before serving. Give `d`
and `length` a physical lower bound in `params.py` as a 422 naming the field (never a clamp,
L02), labelled INTERIM and listed in the D-02 item until the Phase 2 spike measures one. Tests
with `length=1e-8` and `1e-9` on the API and the CLI. Fix together with
`2026-10-06-repeated-query-key-silently-wins.md` in one `/gsd-quick` PR through the wall.

## Resolution
Closed by Phase 3 plan 03-01, in two parts.

- The precise-volume gate (L11, D-08) replaced the `Volume() > 0` check this item suggested:
  `check_solid` refuses a build that is not exactly one valid solid, or whose `BRepGProp` volume
  is outside `T_GATE` of the closed form, so a collapsed solid reads relative error -1 and is
  refused by its volume, inside the function `lru_cache` wraps. `_write_export` treats `False`
  from `exportStl` and a STEP status other than `IFSelect_RetDone` as `BuildError`, and checks
  the STL header count against the byte length and a floor of 4 facets before anything is served.
- The `params` lower bound this item suggested was not added. D-04 keeps the params boundary
  free of an unmeasured minimum, and D-17's doorway guard (`MIN_TAIL_MM`, INTERIM) refuses the
  lengths that crash the kernel: `length=1e-8` and `1e-9` are now a 422 `build_error` on the
  API and an `error:` exit 1 on the CLI, never a worker SIGSEGV. The reproductions are tests in
  `tests/test_api.py`, `tests/test_cli.py` and `tests/test_solid.py`.
