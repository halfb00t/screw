# A bolt's under-head fillet ring can overhang the head's flats with no warning

Severity: must
Status: active
Date: 2026-10-21
Source: 05-REVIEW.md IN-02, filed by plan 05-20 (owner's choice 2026-10-21)
Related files:
- src/screw/solid/bolt.py:69 (`fillet_ring` at ad09d46)
- src/screw/calc/thread.py:699 (`fillet_radius` at ad09d46) and :681 (`FILLET_R`)
- src/screw/params.py (`head_too_small` requires only s > d)

## Context
`fillet_radius` is keyed on (d, pitch) alone, and `head_too_small` only requires s > d. The ring's
outer radius at the head's underside is d/2 + r, so for s - d < 2r it reaches past the head's
inscribed radius s/2 and nothing says so.

The arithmetic is from the code: `FILLET_R[(6.0, 1.0)]` is 0.25, so the ring reaches 3.25 mm against
an s/2 of 3.1 mm for the reviewer's `BoltParams(d=6, pitch=1, s=6.2, k=4, length=20,
thread_length=10)`. That this bolt builds as one valid solid inside the gate, with the info document
silent, is the reviewer's run in 05-REVIEW.md, not a record.

## Why it matters
A downloaded part has a fillet wider than the head it sits under, and the tool is silent where L02's
cap-and-warn rule would have it warn. The solid is self-consistent, so no gate catches it.

## Next step
Revisit before the first release (after Phase 7), or when the fillet or the head next changes. Leave the ring out
with a warning naming `s` when d/2 + r > s/2, as `end_depths` does for the nut's countersink, or add
the case to the standing "ends modelled" warnings.
