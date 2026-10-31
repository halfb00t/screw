# A tall nut below the clearance band was admitted on a prediction that never priced its height

Severity: blocker
Status: resolved
Resolved in: this commit — `fix(cost): price a nut's clearance edges with its other fields real (G39, L30)` (`git log --grep` finds the sha)
Date: 2026-10-31
Source: quick task 261031-o7u (the CR-01 fix of the phase 7 code review, G38), checking the
review's second case; re-measured and corrected by quick task 261031-qd7, ruled as G39. The file
keeps its first name; the title it was filed under ("misses its envelope inside the clearance
band") was wrong.
Related files:
- src/screw/calc/cost.py (`_edges`, `predict`)
- bench/oper_fit.py (`edges`, `predict`)

## Context
Filed as must, on a 2.93 x miss "inside the clearance band". That figure divided the bytes of one
part by the envelope of another. The corrected figures, from `cost.predict` and `cost.fits` at
3b3b8f0 and `solid.export(p, "stl", "fine")` on macOS arm64 (mesh bytes are geometry; R1 counts the
host as context, not a bound), for the nut d 92.28, pitch 31.418, s 130.54:

| m, clearance | stl-fine at 3b3b8f0 | enveloped bytes | bytes written | written / enveloped |
| --- | --- | --- | --- | --- |
| 967.04, 0.15 | refused | 304,650,496 | 223,951,384 | 0.7351 |
| 967.04, -21.12 | admitted | 76,540,259 | 121,632,684 | 1.5891 |
| 2764.2, -21.12 | admitted | 89,999,215 | 364,438,484 | 4.0494 |

Inside the band the nut was covered and refused. Below it, G38's rule priced the real m (10.5 d,
then 30 d) only with the clearance at its own value, which the positive stl-fine clearance
coefficients (bytes 0.112 per mm) made cheap, or with m at its band edges. The real m never met
the clearance edge 0.15.

## Why it matters
Raised to blocker: an admitted part, the third row, writes a fine STL past the 256 MiB export tmpfs
(268,435,456 B) and the 239,508,059 B budget, so it would fail as a `build_error` where L21 promises
a clean `over_budget` refusal (L02). A wider `e` could not cover it: the gap grows with m / d, and
covering the third row alone needs the nut stl-fine bytes e at about 5.07.

## Next step
Resolved by G39 (L30): each clearance edge is also priced with every other field at its real value
when another field is out of band too, so all three rows are refused at the fine STL (the third at
973,648,375 B enveloped). No catalogue row, default part, d-only link or set moves. The runner
reads tall nuts of this shape at 5 repetitions (`bench/points/outband-tall.json`). The head-ratio
gap that remains is
`docs/tech_debt/active/2026-10-31-head-ratio-edges-never-meet-a-real-out-of-band-ratio.md`.
