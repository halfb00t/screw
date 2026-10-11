# `derive()` prints turns and volume for a length below MIN_TAIL_MM, which the builder refuses

Severity: nice
Status: resolved
Date: 2026-10-11
Resolved in: this commit, `fix(calc): report no turns or volume for a thread too short to build` (plan 04-05; `git log --grep` finds the sha)
Source: Phase 3 code review (03-REVIEW.md IN-01), deferred by the owner on 2026-10-10
Related files:
- src/screw/calc/__init__.py (`derive`, `_bolt`)
- src/screw/calc/thread.py (`MIN_TAIL_MM`)

## Context
`GET /api/bolt/info?length=1e-9` is a 200 with `turns` and `volume` rows while `model.stl` for the same part is a 422 (`MIN_TAIL_MM`, D-17); the CLI prints the same document. L12 accepts this, but `MIN_TAIL_MM` is kernel-free knowledge that could warn on the info document as `fine_stl_refusal` already does.

## Why it matters
A printed number for a part that cannot be built is a weaker form of the L02 rule.

## Next step
Move `MIN_TAIL_MM` to `calc/thread.py`, import it back in the builder, and add a warning (not a refusal) to `_bolt` below it. Revisit when the info document next changes.

## Resolution
- `MIN_TAIL_MM` lives in `calc/thread.py` (plan 04-04) and the builder imports it, so there is
  one definition for the builder, the closed forms, the caps and the info document.
- The builder's refusal names `thread_length and length` (plan 04-04).
- `_bolt` leaves the `turns` and `volume` rows out when the built thread is below `MIN_TAIL_MM`
  and adds a warning that says so: `thread_length and length: a thread of <t> mm is shorter than
  the 0.001 mm the builder can model, so this part is not built; turns and volume not reported`.
  The other rows are exact readings of the user's own fields and stay.
- `tests/test_calc.py` covers 0.0005 mm as the whole length and as a short thread on a long shank,
  and exactly 0.001 mm (rows present, no warning); `tests/test_api.py` pairs the warned info
  document with the 422 `build_error` for the same part.
