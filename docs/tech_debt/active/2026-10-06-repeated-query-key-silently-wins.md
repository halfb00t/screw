# A repeated query key or CLI flag silently drops one of two explicit values

Severity: must
Status: active
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
