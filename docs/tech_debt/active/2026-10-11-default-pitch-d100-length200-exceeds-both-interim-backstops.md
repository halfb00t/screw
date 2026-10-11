# A valid in-cap request (d=100, length=200, default pitch) exceeds both interim backstops and is unrecorded

Severity: must
Status: active
Date: 2026-10-11
Source: Phase 3 code review (03-REVIEW.md WR-05), deferred by the owner on 2026-10-10; needs a measurement at the kill point and a severity ruling
Related files:
- src/screw/params.py (`INTERIM_MAX_MM` and its comment, "one valid request cannot outgrow mem_limit")
- docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md (worst case recorded there: d=100, pitch=5, length=1250)
- bench/corpus.py, bench/README.md ("The corpus")

## Context
`GET /api/bolt/model.stl?d=100&length=200` passes validation (200 turns, off the seven fine-STL rows). One in-process run of `screw.solid.export` on macOS arm64 at load 15: fine STL 53.3 s, 1,303,132,684 bytes, peak RSS 9143 MiB; preview STL 4.1 s, 256,952,984 bytes, 1588 MiB. The 30 s `SCREW_BUILD_TIMEOUT` and the 4g `mem_limit` are both exceeded, before gzip or the bytes cache. The interim-bounds item records a harder-to-reach worst case and says which backstop fires first was not measured. `bench/corpus.py` and `bench/README.md` do not say the corpus now drives entries that time out and exceed `mem_limit`.

## Why it matters
One unauthenticated GET holds a worker for the full timeout and drives the container toward OOM. The owner accepted the exposure in D-18, but the recorded example understates it, and the `params.py` comment's premise is now false. CLAUDE.md's "paid-API drain" rubric is the nearest blocker category.

## Next step
Owner ruling 2026-10-11 (UAT test 6): stays Severity must under D-18; trigger is the Phase 7 linux/amd64 re-sweep. Add the d=100/length=200 row with host and load to the interim-bounds item and the corpus docstring; measure RSS at the 30 s kill point so the item can say which backstop fires first; correct the `params.py` comment.
