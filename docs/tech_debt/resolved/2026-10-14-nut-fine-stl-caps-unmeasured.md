# The nut has no fine-STL cap: its caps need their own measurement run

Severity: must
Status: resolved
Date: 2026-10-14
Resolved in: this commit, `fix(05-19): refuse a nut's fine STL past its measured cap` (plan 05-19; `git log --grep` finds the sha)
Source: plan 05-05, Task 2, ruling R12 in `.planning/phases/05-hex-nut-and-kernel-pair-proof/05-OWNER-READS.md`
Related files:
- src/screw/calc/__init__.py (`download_refusal`, the nut branch now calls `nut_fine_stl_refusal`)
- src/screw/calc/thread.py (`NUT_FINE_STL_ROWS`, `nut_fine_stl_refusal`; `FINE_STL_ROWS` stays the rods')
- bench/RESULTS.md ("End-cut probe (Phase 5, D-10)", the nut-bytes table)
- tests/test_calc.py (the absence pin `test_a_nut_download_is_never_refused_until_the_nut_fine_stl_caps_are_measured`, replaced by `test_a_tall_nut_fine_stl_is_refused_by_the_nuts_cap_and_nothing_else_is`)

## Context
R12 says: reuse `FINE_STL_ROWS` on `m` if the probe's nut bytes at each cap fit the 64 MiB budget
and cap + 1 mm does not; otherwise measure nut caps in their own run. The probe's table does not
meet the condition. M10 right (0.973 of 64 MiB at cap + 1) and M20 right (0.936) still fit one mm
past the cap, so the rod caps are conservative there, and M20 left is already over at the cap
itself (1.003). The probe measured three of the thirteen capped (d, pitch, hand) rows. So the
else-branch applies and no nut cap exists: `download_refusal` serves every nut download, and the
rod's rule is deliberately not routed through the nut (a rod cap on a nut is a number nobody
measured, L02).

The plan's own stop branch asks for a checkpoint and the owner's written word before the nut keeps
no cap meanwhile. The orchestrator ran the plan to completion instead and asked for this item;
the owner's sign-off on shipping without the cap is still outstanding.

## Why it matters
Threat T-05-12 (huge `m`) is mitigated only by the 250-turn cap on `m + 2 pitch` and the interim
ceilings. A nut tall enough to build can have a fine STL plus its gzip copy past the 64 MiB export
budget, with nothing refusing it before the build. Every front end behaves the same way, so the
API, the CLI and the info document agree; they are all unbounded for the nut's fine STL.

## Next step
Before the nut fine STL can be offered as bounded: run a measurement of the nut's fine STL plus
gzip-1 copy on every (d, pitch, hand) row the rods measured, at the heights where each crosses
64 MiB, record it in `bench/RESULTS.md`, add `nut_fine_stl_refusal(d, pitch, m, left_hand)` with
its own cap table naming `m`, wire it into the nut branch of `download_refusal`, and replace the
test named above. Ask the owner for the bench run (it is a bench task, not an inline edit) and
for a decision on the interim state.

## Resolution
Plan 05-19 measured the nut's own caps in a pre-registered run per ISO 262 coarse size and hand
(`bench/nut_fine_caps.py`; run `2026-10-21-nut-fine-caps-amended`, which repeated the stopped run
`2026-10-20-nut-fine-caps` row for row; `bench/RESULTS.md`, "Nut fine-STL caps, amended re-run
(Phase 5, R17)"). The owner's R16 (ceiling C = 5.0 mm, a fine STL above it refused) and R17 (a check
the build refuses is not a stop) shaped it. `nut_fine_stl_refusal` now refuses a nut's fine STL past
its cap with a sentence naming `m` (or `clearance` above C) on the API (422 `fine_stl_cap`), the CLI
(exit 2) and the info document; the preview STL and the STEP are never refused. Recorded as L16.
