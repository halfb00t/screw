# The tip cut fails in the sliver of thread_length just above the cone's axial length

Severity: nice
Status: active
Date: 2026-10-20
Source: plan 05-12, Task 2 (tip cone), found while testing "one float longer gets the cone"
Related files:
- src/screw/calc/thread.py (`tip_cone_fits`, `tip_cone_length`)
- src/screw/solid/bolt.py (`tip_cut`)

## Context
`tip_cone_fits` says a built thread `t` gets the tip cone when `t > tip_cone_length(pitch, 45)`,
one float above the cone's axial length, as the plan states and as `derive` reports. Measured on
M6 x 10 (pitch 1): the kernel's intersect raises `Standard_Failure` (`BRepAdaptor_Curve::No
geometry`) for `t` from that length up to about 1e-9 mm above it, and cuts correctly at 1e-6 mm
above (volume within 1.3e-5 of the oracle). There the cone grazes the crest at the thread's far
end plane and the boolean is degenerate. The build then answers with a `build_error` 422, never
a wrong part.

## Why it matters
Only a `thread_length` set inside a window of about 1e-6 mm hits it; nobody types one. A refusal
there reads "Geometry kernel failed" instead of a sentence about `thread_length`.

## Next step
Revisit if a real size meets the window (the window moves with the pitch): fold a thread within
`MIN_TAIL_MM` of the cone length into the no-cone side in `tip_cone_fits` (the D-27 move for a
shank sliver), which needs an owner ruling because it changes the plan's "one float longer".
