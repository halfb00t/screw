# The nut's size ceilings are interim; its fine-STL caps are measured on macOS arm64 only

Severity: must
Status: resolved
Date: 2026-10-14
Resolved in: this commit — `refactor(calc): retire the per-row fine-STL caps the cost model replaced (07 D-08, D-17)` (`git log --grep` finds the sha)
Source: plans 05-04 and 05-05 (Phase 5); filed by plan 05-18 as the phase closed
Related files:
- src/screw/params.py (`NutParams`: `s`, `m`, `clearance` share `INTERIM_MAX_MM`)
- src/screw/calc/thread.py (`nut_turn_cap_refusal`, `MAX_TURNS`)
- src/screw/calc/__init__.py (`download_refusal`, the nut branch)
- docs/tech_debt/resolved/2026-10-14-nut-fine-stl-caps-unmeasured.md
- docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md (the bolt's and the runtime's rows)

## Context
The nut's three size fields `s`, `m` and `clearance` are each bounded only by `INTERIM_MAX_MM`
(1e5 mm), the figure Phase 1 measured on a plain cylinder and not on a nut (D-14, F1). The nut's
other bounds are rules, not measurements: the root radius with the clearance, `s > d + 2c`
(`nut_too_thin`) and the 250-turn cap on `m + 2 pitch` (`MAX_TURNS`, measured on rods and voids in
L11's `2026-10-08-a-frontier`, nothing above it). None of them is a bound on build time or memory
for a nut. What was measured is small: every ISO 4032 row builds in 1.0 to 1.5 s at clearances 0, 0.1
and 0.2 on macOS arm64 under a shared host (plan 05-13), not on linux/amd64 and not at the corners.

The nut's fine-STL caps shipped in plan 05-19 (run `2026-10-21-nut-fine-caps-amended`, L16), and the
item that tracked them, `2026-10-14-nut-fine-stl-caps-unmeasured.md`, is resolved. They were measured
on macOS arm64 against the INTERIM 64 MiB budget.

## Why it matters
A user can ask for a nut up to 1e5 mm across, or one tall enough to take 250 turns of void, and
nothing measured says the build finishes inside `SCREW_BUILD_TIMEOUT` or the container's memory. The
bolt has the same open question (`2026-10-05-interim-runtime-bounds.md`); the nut adds three more
fields to it.

## Next step
Revisit with Phase 7's operability re-sweep (OPER-02, OPER-03): measure the nut on the full grid on
linux/amd64, replace the `s`, `m` and `clearance` ceilings and the turn cap with measured values,
and re-measure the nut's fine-STL caps on linux/amd64 alongside the rods'. Add the nut's rows to
the table in `2026-10-05-interim-runtime-bounds.md` in that change.

## Resolution
The ceilings and the turn cap were re-measured on linux/amd64 in L20 (07 D-08): the nut's `s` is
bounded by `MAX_FIELD_MM` (1000), its `m` by `MAX_NUT_M_MM` (10000) and its `clearance` by
`MAX_NUT_CLEARANCE_MM` (496.999), its `d` stays under `MAX_FIELD_MM` (G27), and `MAX_TURNS` is 90,
each cited to its walls run. The fine-STL caps were replaced in L21 (07 D-17) by the nut's fitted,
enveloped cost model, which judges the preview STL, the fine STL and the STEP against the owner's
budget on raw bytes, cold build seconds and cgroup peak (runs explore 40646117094 and spread
40646125666). This commit removes `NUT_FINE_STL_ROWS`, `NUT_FINE_STL_RUN`,
`NUT_FINE_STL_CLEARANCE` and `nut_fine_stl_refusal`, with the rods' `FINE_STL_ROWS` and
`fine_stl_refusal`; `download_refusal` already read the cost model alone, so no download outcome
changes. A clearance above 5.0 mm is no longer refused for that reason alone:
`tests/test_thread_maths.py::test_a_nut_above_the_retired_clearance_ceiling_is_judged_by_the_cost_model_alone`.
The rows the Next step asked to add to `2026-10-05-interim-runtime-bounds.md` are not added: what is
left there (the build timeout, the workers, the container's memory limit) applies to every kind and
stays open in that item until plans 07-15 and 07-16.
