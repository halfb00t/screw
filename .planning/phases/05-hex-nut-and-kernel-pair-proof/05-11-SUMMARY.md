---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 11
subsystem: calc
tags: [calc, thread-maths, oracles, end-cuts, tdd, thrd-05]
requires:
  - phase: 05-02
    provides: "bench/end_cuts.py, the probed end-cut formulas and the End-cut probe entry in bench/RESULTS.md"
  - phase: 05-10
    provides: "the matching-part and UI contract"
provides:
  - "calc/thread.py outside_disc_area, tip_cone_volume, countersink_volume, face_chamfer_volume, fillet_ring_volume (kernel-free oracles; ValueError outside validity)"
  - "TIP_ANGLE_DEG 45, COUNTERSINK_FACE_FACTOR 1.16, COUNTERSINK_HALF_ANGLE_DEG 45, CHAMFER_ANGLE_DEG 30, each with its OWNER-READS line and cited-or-model label"
  - "end_depths(d, pitch, clearance, s, m) -> (countersink depth, chamfer depth, warnings), capped per R5"
  - "T_PIECE 0.03 (R11) and piece_refusal(measured, oracle, what)"
  - "bench/end_cuts.py imports the oracles back from screw.calc.thread"
affects: [05-12, 05-13, 05-18]
requirements-completed: []  # THRD-05 stays open: the end cuts are built by 05-12 and 05-13
estimate_ref: "90000 tokens, 2 tasks"
actuals:
  tokens: 18500
  tasks: 2
  commits: 5
plan_head_before: 5574dc694e5f9407fa068e196fe50b5893d589a1
plan_head_after: 343636150d204cae4e09983fa1987b79dfdbc8ba
tech-stack:
  added: []
  patterns:
    - "an end model is a named constant whose comment says cited (document string) or stated model, and the OWNER-READS ruling it stands on"
    - "an oracle raises ValueError outside its validity; end_depths is the one place that caps and warns so the oracle never sees an invalid input"
key-files:
  created:
    - tests/test_end_oracles.py
  modified:
    - src/screw/calc/thread.py
    - bench/end_cuts.py
    - tests/test_bench.py
key-decisions:
  - "COUNTERSINK_FACE_FACTOR = 1.16 (owner ruling R3 option A, 2026-10-20): the largest da_max / d of the 14 GOST ISO 4032-2014 rows, at M2,5; a stated model"
  - "end_depths drops the countersink (depth 0) with a warning naming clearance when the face radius does not pass the void's crest radius, never a 422 (R3, L02)"
  - "end_depths also drops the countersink, naming s, when the face radius exceeds s / 2 (see Deviations, Rule 2)"
  - "T_PIECE = 0.03 from R11: 10 x 2.737e-03 = 2.737e-02 rounded up to one significant figure"
status: complete
---

# Phase 5 Plan 11: The end-cut oracles, end models and capped depths Summary

The kernel-free numbers the THRD-04 gate will compare chamfered and filleted parts against now live in `calc/thread.py`: five oracles pinned to independent identities, the owner-ruled end models, `end_depths` with R5's cap-and-warn, and the 0.03 piece tolerance.

## Task commits

| Task | Commit | Message |
| ---- | ------ | ------- |
| 1 | 3130876 | feat(thread): add kernel-free oracles for the tip cone, countersink, face chamfer and fillet ring |
| 2 (part 1) | c94ebba | feat(thread): add the end models, the piece tolerance and the bench import-back |
| 2 (part 2) | 3436361 | feat(thread): add the countersink face factor and the capped end depths |

`commits: 5` in the frontmatter is the measured `git rev-list --count` from the plan-start ledger. Two of the five are the orchestrator's `docs(05)` commits (849d3ab, 912de9c) recording owner rulings; the plan's own are the three above.

## What was built

- **Oracles** (`src/screw/calc/thread.py`): `outside_disc_area`, `tip_cone_volume`, `countersink_volume`, `face_chamfer_volume`, `fillet_ring_volume`, plus the helpers `nut_material_in_disc` and `hex_arc_inside`. The formulas moved unchanged from the bench probe. Each raises `ValueError` naming the condition outside its validity. No `cadquery` import.
- **Identities** (`tests/test_end_oracles.py`): `outside_disc_area(rho = 0)` is `section_area`; the hex arc integrates to `hex_prism_volume(s, 1)`; the tip cone equals a 2-D midpoint integral over (z, theta) and the swapped integral; the countersink equals a grid over depth and section angle; the ring equals a direct region integral and Pappus; quadrature error at the shipped point counts is under `T_GATE / 100`; the probe's M6 values are reproduced to 1e-12.
- **Planted-error check:** with the hexagon arc's `12 acos` changed to `6 acos`, 12 tests fail; with the flank integral's `3 k` changed to `2 k`, 32 fail. Both mutations were reverted and the file restored (diff shows insertions only).
- **End models:** `TIP_ANGLE_DEG` 45 (R2, read 6, stated model), `COUNTERSINK_HALF_ANGLE_DEG` 45 (R3 b, the 90 degree end of the printed band, stated model), `COUNTERSINK_FACE_FACTOR` 1.16 (R3, owner option A, stated model, derivation in its comment), `CHAMFER_ANGLE_DEG` 30 (R4 a, the 30 degree end of the band, stated model). Documents are named exactly `GOST 12414-94 (ISO 4753:1983)` and `GOST ISO 4032-2014 (ISO 4032:2012)`; a test checks no other edition appears.
- **`end_depths`:** full countersink depth is where the cone reaches the root radius, `(1.16 d/2 - rr) / tan 45`; full chamfer depth is the cone's own depth at the hexagon corner. Both are capped at `m / 2`, with the plan's warning text, so the two faces' cutters never meet. When `1.16 d/2 <= d/2 + c` the cone cannot cross the void: countersink depth 0 and a warning naming `clearance`.
- **`T_PIECE` 0.03** and `piece_refusal`, signed relative error, NaN refused; a test re-derives the tolerance from the probe entry's recorded number and checks every honest probe row passes and every control is refused.
- **Bench import-back:** `bench/end_cuts.py` imports the oracles from `screw.calc.thread`; `tests/test_bench.py` asserts they are the same objects.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Countersink dropped when the face radius exceeds s / 2**
- **Found during:** Task 2 (end_depths)
- **Issue:** The model accepts `s` between `d + 2c` and `1.16 d`; there the countersink face radius leaves the flats and overlaps the chamfer's start, and `countersink_volume` raises (P10). `end_depths` would hand the builder a depth the oracle rejects.
- **Fix:** Same treatment as the crest case (R3's cap-and-warn, L02): countersink depth 0 and a warning naming `s`; never a refusal, since the countersink is not a field the user set.
- **Files modified:** src/screw/calc/thread.py, tests/test_end_oracles.py
- **Commit:** 3436361

**2. [Rule 3 - Blocking] Lint: compound asserts**
- **Found during:** Task 2
- **Issue:** ruff PT018 on five new `assert a and b` lines.
- **Fix:** split into two asserts.
- **Commit:** 3436361

### Process deviations

- **No separate RED commit** for either task. The pre-commit hook runs `make verify` including pytest, so a failing-test commit cannot land. The RED run was real for the Task 1 oracles (87 tests failed before they existed); for the `end_depths` remainder the code was written before its tests and no RED run was made. Test and code commits are combined. The plan's `git log` ordering criterion for Task 1 is therefore not met as written.
- **Oracle tests live in `tests/test_end_oracles.py`**, not `tests/test_calc.py`, as the plan's file list says.
- **The bench uses the calc names without aliases** (`outside_disc_area` and so on) rather than `... as a_out`, so the import-back test compares the calc names directly.
- **The plan's M2 example does not cap.** The plan says `end_depths` caps for "M2 at its row m"; at M2 (`m` 1.6, `s` 4) the full countersink depth (about 0.4 mm) and the chamfer depth (about 0.18 mm) are both under `m / 2` = 0.8, so nothing caps. The cap test uses a thin nut (`m` 0.8 on M6, `s` 10) instead. Whether any real table row caps is for plan 05-13 to see once rows exist.

### Note for plan 05-13

`face_chamfer_volume` treats `depth` as a flat cap: the chamfer removes `min((rho - r0) tan beta, depth)` at each radius. The builder must cut the same shape when `end_depths` caps the chamfer (a conical cut intersected with a slab of that depth), or the gate will disagree with the part.

## Known Stubs

None.

## Threat Flags

None. No new endpoint, auth path, file access or schema at a trust boundary.

## Authentication gates

None.

## Verification

`make verify` (ruff, mypy `--strict`, import-boundary contracts, unfinished-work scan, pytest): final result line `3049 passed in 113.05s (0:01:53)`, total coverage 98.03% against the 96.0% requirement. The same gate passed again in the pre-commit hook of 3436361.

Debt filed: none.

## Self-Check: PASSED

- FOUND: src/screw/calc/thread.py (`def end_depths(`, `T_PIECE = `, `COUNTERSINK_FACE_FACTOR = 1.16`)
- FOUND: tests/test_end_oracles.py
- FOUND: commits 3130876, c94ebba, 3436361 (ancestors of HEAD)
