# A tall nut with a coarse pitch misses its fine-STL bytes envelope inside the clearance band

Severity: must
Status: active
Date: 2026-10-31
Source: quick task 261031-o7u (the CR-01 fix of the phase 7 code review, G38), checking the
review's second case
Related files:
- src/screw/calc/cost.py (`predict`, `_edges`)
- bench/oper_fit.py (`predict`, `edges`)

## Context
`NutParams(d=92.28, pitch=31.418, s=130.54, m=967.04, clearance=0.15)` is admitted at the fine STL.
Its enveloped bytes prediction is 76,540,259 B. `solid.export(p, "stl", "fine")` wrote 223,951,384
bytes in 11.4 s on macOS arm64 (mesh bytes are geometry; R1 counts the host as context, not a
bound): 2.93 x the envelope. Its clearance is inside the G38 band. Its m/d is 10.5, above the
nut's m band (0.8 to 3.0), its s/d is 1.41, below the s band, and its pitch is coarse (pitch / d
0.34). The cause of the miss is not measured. ASSUMPTION: it lies in the fit's form outside the
fitted ranges (no turns feature for the nut; ln_pitch -0.993 on the nut stl-fine bytes model, so a
coarser pitch always predicts cheaper). The same nut at clearance -21.12 wrote 121,632,684 bytes,
so the clearance band itself behaves as G38 assumes.

## Why it matters
The envelope guarantee (`pred x (1 + e) >= actual`) does not hold for this admitted part. Both
readings are under B-01's 239,508,059-byte stl-fine budget, so no over-budget admission is shown.
But a larger nut of the same shape could be over the budget, the 256 MiB tmpfs or the memory
headroom, and get a `build_error` or an OOM instead of the clean `over_budget` refusal L21
promises (L02). Not filed as a blocker because no admitted part has been shown over a limit; the
owner may rule otherwise.

## Next step
Owner ruling. Options: add nuts above the m band (tall, coarse pitch) to the Runs II out-of-band set
so R12 widens `e` from runner readings; or refuse a nut m/d above its band until such a reading
exists. Revisit before the first release, or as soon as an admitted nut is measured over a limit.
