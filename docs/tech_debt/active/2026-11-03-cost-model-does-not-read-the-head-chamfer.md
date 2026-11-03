# The cost model does not read the head chamfer

Severity: must
Status: active
Date: 2026-11-03
Source: v1.0 milestone audit (INT-05); 08-CONTEXT.md Deferred Ideas
Related files:
- src/screw/calc/cost.py:73-76

## Context
The cost model was fitted at the default 30 degree head chamfer, and `cost.FEATURES` has no
`head_chamfer`. A bolt with another angle is priced as a 30 degree one. Phase 6.1 measured about
0.03 s for the cut, but no runner reading prices it.

## Why it matters
The numbers the gate prints for a bolt with another head chamfer rest on a fit that never saw that
angle (L02: a number someone will cut metal to).

## Next step
A runner reading of the chamfer at its range ends against its prediction. Revisit at the next
cost-model re-fit, or on a `cost_model.miss` logged for a bolt whose head_chamfer is not 30. Not
fixed in Phase 8.
