# An above-band head ratio is never priced against a below-band one at its edge

Severity: must
Status: active
Date: 2026-10-31
Source: quick task 261031-qd7, ruled as G39 ("F: clearance only (Recommended)"), which pairs only the
nut's clearance edges with the part's real fields
Related files:
- src/screw/calc/cost.py (`_edges`, `predict`)
- bench/oper_fit.py (`edges`, `predict`)

## Context
G28's rule (R11) predicts a part with head ratios outside their bands as the largest of the raw part
and every combination of the out-of-band ratios' edges. An above-band ratio at its real value meets
the other out-of-band ratios only at their real values too, never at their edges. G39 closed that
for the clearance and left the head ratios as they are. On the review's nut, d 92.28, pitch 31.418,
s 130.54 (s / d 1.41, below its band), m 967.04 (m / d 10.5, above it), clearance 0.15, pairing
every field's real value with the others' edges predicts 305,377,062 B enveloped at the fine STL
against the shipped 304,650,496 B: 1.0024 x (`cost` at the G39 commit). Both refuse that nut.

Pairing every field was measured before the ruling over every link that names only d, at d 0.1 to
999.9 mm. It refuses the bolt's fine STL at d 1.2 to 4.0 and 8.3 to 9.9, its STEP at 1.2 to 3.4 and
8.4 to 9.5 and its preview at 9.8 and 9.9, leaving d-only M2 and M3 with no download. Pairing only
the fields above their bands refuses the fine STL at d 1.2 to 4.0 and the STEP at 1.2 to 3.4. Both
price a head the user never asked for (a d-only M2 at its real s 10 with k at 0.6 d), so a refusal
there rests on no reading either.

## Why it matters
Where the gap is large, a part could be admitted on a prediction no reading covers (L02). The one
measured case is 1.0024 x, inside every envelope. `ln_k` is negative on every bolt model, so the
d-only small bolts are where a paired prediction moves most.

## Next step
Read the d-only M2 and M3 of `bench/points/outband-tall.json` on the runner (G39) and record here
whether any reading misses its enveloped prediction. Revisit before the first release, or as soon as
an admitted part with two head ratios out of band is measured over its envelope.
