# `derive()` prints turns and volume for a length below MIN_TAIL_MM, which the builder refuses

Severity: nice
Status: active
Date: 2026-10-11
Source: Phase 3 code review (03-REVIEW.md IN-01), deferred by the owner on 2026-10-10
Related files:
- src/screw/calc/__init__.py (`derive`, `_bolt`)
- src/screw/solid/helical.py (`MIN_TAIL_MM`)

## Context
`GET /api/bolt/info?length=1e-9` is a 200 with `turns` and `volume` rows while `model.stl` for the same part is a 422 (`MIN_TAIL_MM`, D-17); the CLI prints the same document. L12 accepts this, but `MIN_TAIL_MM` is kernel-free knowledge that could warn on the info document as `fine_stl_refusal` already does.

## Why it matters
A printed number for a part that cannot be built is a weaker form of the L02 rule.

## Next step
Move `MIN_TAIL_MM` to `calc/thread.py`, import it back in the builder, and add a warning (not a refusal) to `_bolt` below it. Revisit when the info document next changes.
