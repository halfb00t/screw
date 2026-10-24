# The info document prints a whole head chamfer for a tiny angle the kernel refuses

Severity: must
Status: active
Date: 2026-10-24
Source: 06.1 code review WR-01 (the part the oracle-based fix cannot reach)
Related files:
- src/screw/calc/__init__.py (`_bolt`, `chamfer_modelled`)
- src/screw/solid/__init__.py (`_build_bolt`, the head chamfer piece gate)
- tests/test_solid.py (`test_a_tiny_or_near_right_head_chamfer_builds_inside_its_gates_or_is_refused_by_name`)

## Context
`derive()` drops the chamfer rows and the volume, and says "this part is not built", only when
`head_chamfer_volume` raises (the angle's tangent underflows, 5e-324). Angles from about 1e-320
up to 1e-5 degrees pass that oracle but the kernel refuses them (`Standard_Failure` below 1e-5,
the piece gate at 1e-5; 1e-4 and above builds). For those angles the info document prints four
chamfer rows and a finite volume for a part that returns a 422 `build_error`. The boundary is one
macOS arm64 measurement; linux may differ. D-18 forbids a floor in the model, and `derive()`
never runs the kernel, so it cannot know.

## Why it matters
A volume row for a bolt nobody can make is a number someone may act on (L02). Reachable only by
typing an angle under 1e-4 degrees, far outside the 15 to 30 degree band, which already warns.

## Next step
Measure the refusal boundary on linux/amd64 in the Phase 7 sweep, then either add a "may be
refused by the geometry kernel" warning for `0 < head_chamfer` under the measured bound (a
warning, not a floor), or supersede D-18 with a floor.
