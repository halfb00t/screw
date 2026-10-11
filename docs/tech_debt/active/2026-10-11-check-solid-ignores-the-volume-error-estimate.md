# `check_solid` discards the volume estimator's own error estimate

Severity: nice
Status: active
Date: 2026-10-11
Source: Phase 3 code review (03-REVIEW.md IN-03), deferred by the owner on 2026-10-10
Related files:
- src/screw/solid/__init__.py (`precise_volume`, `check_solid`)
- docs/architecture/decision_log.md (L12, `T_GATE`)

## Context
`BRepGProp.VolumeProperties_s(..., eps, ...)` returns the achieved relative error (8.2e-7 at M6x20, probed); `precise_volume` discards it. If integration did not converge to `PRECISE_EPS`, the reading is less trustworthy than the gate assumes, and `T_GATE` is ten times the largest observed disagreement. Not shown to fail on any measured row. The same limit is recorded for the spike oracle in 02-REVIEW-DISPOSITION.md IN-04.

## Why it matters
The gate's confidence rests on a convergence it does not check.

## Next step
Return the estimate and refuse when it exceeds `T_GATE / 10`, or record in L12 that the estimate is deliberately unused. Revisit when the gate or `T_GATE` next changes.
