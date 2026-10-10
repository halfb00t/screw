# A repeated query key or CLI flag silently drops one of two explicit values

Severity: must
Status: resolved
Resolved in: eaaac85 (API) and d849557 (CLI) — fix(app): refuse a repeated query key before validation, feat(params): add left_hand to every kind and build left-hand threads from the API and CLI (plan 03-04)
Date: 2026-10-06
Source: Phase 1 code review (01-REVIEW.md WR-01). Owner sign-off 2026-10-06: fix in the
`/gsd-quick` PR that follows the Phase 1 close PR, together with CR-01.
Related files:
- src/screw/app.py:363, :370, :349 (query parsing takes the last value of a repeated key)
- src/screw/cli.py:34 (argparse takes the last `--d`)

## Context
`/api/bolt/info?d=0&d=5` returns 200 with d=5; `?d=5&d=100000` returns 200 with d=100000;
`?d=5&d=0` returns 422 judging only the 0; `/api/schema?kind=bolt&kind=x` returns 404. The
CLI behaves the same for a repeated `--d`. Reproduced 2026-10-06.

## Why it matters
L02: a direct conflict between two things the user asked for is a 422 naming the fields,
never a guess. A shared link with a duplicated key builds a part the author did not see.
The parity criterion (a foreign field is refused on every front end) is silent on duplicates,
so no test catches it.

## Next step
In the app, refuse a repeated key before validation (compare
`len(request.query_params.multi_items())` with `len(request.query_params)` and raise a 422
`{"loc": ["query", name], "type": "duplicate"}`); in the CLI, an `argparse.Action` that exits
2 when its dest was already set. One parametrised test over the registry on both front ends.

## Resolution
Closed by Phase 3 plan 03-04 (D-12), in two commits, one per front end.

- API: `refuse_repeated_keys` is an app-level dependency (`FastAPI(dependencies=[...])`), so it
  runs before each route's query model and covers every route, `/api/schema` included. A key
  given twice is a 422 `{"loc": ["query", key], "type": "duplicate"}` listing every repeated key
  in first-seen order; neither value is judged. The check this item suggested (comparing the
  lengths of `multi_items()` and `query_params`) was replaced by counting per key, which names
  the key.
- CLI: `_Once` and `_OnceBool` (`--x` / `--no-x`, once between them) exit 2 naming the flag when
  the parameter is already set; export's `-o`, `--format` and `--quality` use the same action
  (`--quality` now defaults to `None` and `cmd_export` reads `ns.quality or "fine"`).
- One parametrised test over the registry, `test_a_repeated_parameter_is_refused_naming_it` in
  `tests/test_parity.py`, covers both front ends; the four reproductions in this item are tests
  in `tests/test_api.py`.
