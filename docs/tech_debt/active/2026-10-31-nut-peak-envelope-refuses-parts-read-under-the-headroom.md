# The nut's fine-STL peak envelope refuses a nut the runner built under the headroom

Severity: must
Status: active
Date: 2026-10-31
Source: quick task 261031-qd7, G40 ("Keep cap, file must debt (Recommended)"), L32
Related files:
- src/screw/calc/cost.py (`budget`, `HEADROOM_CAPPED`, the nut stl-fine peak `ENVELOPE` row)
- bench/results/phase-07/fit.json (the nut stl-fine peak model)

## Context
G40 caps the nut's fine-STL peak budget at 1,830,617,088 B. The nut stl-fine peak e is
0.5976833077470993 (widened by outband run 40909768713), so the cap refuses nuts whose readings are
well under the headroom:

| part | read at most | / headroom | enveloped / headroom | reading |
| --- | --- | --- | --- | --- |
| tall-nut-x0.5-m10.5d (d 46.14, pitch 15.709, s 65.27, m 484.5) | 1,483,145,216 B | 0.8102 | 1.0116 | 41206999278 rep 5 |

It is the one production-valid part so refused. The d 30 grid nuts at clearance 5 that the owner's
question named are refused by the cap too: `nut-d30-p1-m0.8d-s1.6d-c5-right` (0.8377 read, 1.2646
enveloped, bound run 40907549180, the 71 s stl-fine timeout's bound point), its s 4 d sibling
(0.8438 and 1.2721, gzip run 40909739628, the part whose drift build set W) and the pitch-3.5 pair
(0.7406 to 0.8027 read, 1.1368 to 1.1435 enveloped, explore run 40646117094). But their d / pitch
(30 and 8.57) is past the nut's wall of 8 (L25, G36), so no request reaches them. The timeout and W
stand as derived from them.

## Why it matters
A correct nut is refused at the fine STL on a prediction its own readings contradict, so the space a
user can download is smaller than the platform supports. It refuses, never admits, so it is not a
blocker.

## Next step
Re-fit the nut stl-fine peak model (R11 form, over the explore, spread and out-of-band readings) so
its envelope tracks the readings, and drop the tall nut at 0.5 scale from this list. Revisit at the
next re-fit, or before the first release.
