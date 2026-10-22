---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 13
subsystem: solid
tags: [nut, countersink, face-chamfer, gates, watertight-sweep, standing-warning, thrd-05, type-03]
requires:
  - phase: 05-11
    provides: "countersink_volume, face_chamfer_volume, end_depths, COUNTERSINK_FACE_FACTOR, CHAMFER_ANGLE_DEG, T_PIECE, piece_refusal"
  - phase: 05-12
    provides: "the piece-gate pattern (check_structure, precise_volume before and after, piece_refusal) and the bolt's ends"
provides:
  - "solid/nut.py countersink, face_chamfer, finish, countersink_inner_radius: the R3 lead-in countersink and R4 30 degree corner chamfer on both nut faces, cut from the fields d, pitch, clearance, s, m only"
  - "calc/thread.py nut_end_closed_volume and countersink_face_radius"
  - "solid/__init__.py nut branch: void gate, then four piece checks at T_PIECE, then the whole nut at T_GATE"
  - "derive: nut volume row from nut_end_closed_volume with the formula text naming the ends; end_depths warnings (R5 naming m, R3 naming clearance or s) on the nut document"
  - "STANDING_WARNING rewritten to name the modelled ends, asserted exactly on the calc, CLI and parity tests"
  - "28-id ISO 4032 watertight preview sweep and 42-id countersink-crosses-the-root test, each with a positive control"
affects: [05-14, 05-17, 05-18]
requirements-completed: [THRD-05, TYPE-03]
estimate_ref: "110000 tokens, 3 tasks"
actuals:
  tokens: 8963
  tasks: 3
  commits: 3
plan_head_before: c7962a2ffa4fd52772937a6675047df0c5522df2
plan_head_after: a641c403090b48b7e2198e8e72f8715239278996
tech-stack:
  added: []
  patterns:
    - "nut.finish is a generator yielding (piece name, nut after that cut): the builder judges each cut against its own oracle without the cutter module importing the kernel's volume integrator"
    - "a full-depth countersink cone goes on CROSS_FRACTION (0.3) thread depths below the root radius so it crosses the root surface; a depth capped by R5 stops flat in material"
key-files:
  created: []
  modified:
    - src/screw/solid/nut.py
    - src/screw/solid/__init__.py
    - src/screw/calc/thread.py
    - src/screw/calc/__init__.py
    - tests/test_nut.py
    - tests/test_calc.py
    - tests/test_parity.py
    - tests/test_cli.py
key-decisions:
  - "R5 a applied: end_depths caps both depths at m / 2 and the nut's document warns naming m; params.py is untouched (no 422 for a thin nut, R5 b not taken)"
  - "finish returns a generator of (piece, shape) rather than a single shape, so each of the four cuts is gated by its own precise-volume difference"
  - "the chamfer cutter is the cone cut off flat at the depth end_depths returns, the shape face_chamfer_volume integrates (05-11 note)"
status: complete
---

# Phase 5 Plan 13: The nut's ends and the rewritten standing warning Summary

Both faces of every nut now carry a 90 degree lead-in countersink (opening to 1.16 d/2, crossing the void's root) and a 30 degree corner chamfer from the inscribed circle, each judged by its own volume at `T_PIECE` and the whole nut at `T_GATE`; every info document's first warning now names the modelled ends.

## Task commits

| Task | Commit | Message |
| ---- | ------ | ------- |
| 1 | 7557806 | feat(nut): cut lead-in countersinks and face chamfers on both faces, each gated by its piece |
| 2 | 8dc388c | test(nut): sweep the ISO 4032 catalogue for a watertight preview mesh |
| 3 | a641c40 | feat(info): name the modelled ends in the standing warning |

`commits: 3` is measured from the plan-start ledger (`git rev-list --count c7962a2..HEAD`).

## What was built

- **Cutters** (`solid/nut.py`): `countersink(p, z_face, depth)` is the 45 degree half-angle cone opening to `countersink_face_radius(d)` on the face, reaching `PAST_FACE` (1 mm) outside it, and ending at `countersink_inner_radius`. At full depth that radius is `CROSS_FRACTION` (0.3) thread depths below the root radius `d/2 - 5H/8 + clearance`, so the cone crosses the root surface; at a depth R5 capped it is the cone's own radius there, above the root, and the cutter ends flat in material. `face_chamfer(p, z_face, depth)` is the 30 degree cone from `s/2`, cut off flat at `depth`, the capped shape `face_chamfer_volume` integrates (05-11's note). `finish(p, body)` yields, in order, the countersink on each face (none when `end_depths` returns depth 0) and then the chamfer on each face.
- **Builder** (`solid/__init__.py`): void gate; `assemble`; structure check and precise volume; for each yielded cut a structure check, a precise volume, and `piece_refusal(volume before - after, oracle)` naming the piece (`wrong lead-in countersink: the lead-in countersink is ...`); then `check_solid` of the finished nut against `nut_end_closed_volume`, reusing the last volume so it is integrated once per cut.
- **Oracle** (`calc/thread.py`): `nut_end_closed_volume` is `nut_closed_volume - 2 countersink_volume - 2 face_chamfer_volume` at `end_depths`' depths; a dropped countersink contributes nothing. `countersink_face_radius(d)` is the one reading of the 1.16 factor for the cutter, the oracle and `end_depths`.
- **Info** (`calc/__init__.py`): the nut's volume row uses `nut_end_closed_volume` with a formula text naming the countersinks and chamfers; `end_depths`' warnings are appended to the nut document (R5 names `m`, R3 names `clearance` or `s`).
- **Standing warning**: `ends modelled per L15: bolt tip chamfer, under-head fillet on an ISO 4014 plain shank, nut lead-in countersinks and face chamfers; nominal, not toleranced; not a product build`, asserted with `==` in `tests/test_calc.py`, `tests/test_parity.py` and `tests/test_cli.py` (the CLI prefixes `warning: `). `grep -rn 'plain-cut thread ends' src tests` prints nothing.

## Measured facts

- **Builds.** Every ISO 4032 row at clearance 0, 0.1 and 0.2 builds as one valid solid, whole-gate error at most 3.3e-06 against `T_GATE` 9e-05. Build time rose from about 0.15 s to 1.0 to 1.5 s per nut (four more precise volumes and four booleans): M2 0.7 to 1.1 s, M20 1.4 s.
- **No catalogue row caps.** At the rows' own `m`, `end_depths` returns the full depths for every size (the smallest margin is M2: countersink 0.38 mm and chamfer 0.18 mm against `m / 2` 0.8 mm), so R5 never fires on a shipped row; it fires on a thin custom nut (M6, `m` 0.8: both depths 0.4 mm, two warnings naming `m`).
- **R3 clearance case is real on two rows.** M2 and M2.5 at clearance 0.2 have no countersink (the cone opens to 1.16 and 1.45 mm inside a 1.2 and 1.45 mm crest radius); the document warns naming `clearance`, and the nut builds with chamfers only.
- **Whole gate against the controls.** Measured on the M6 and M20 nuts (clearance 0.1): the whole-nut gate alone flags every control (one countersink skipped +1.5e-02 and +1.9e-02; one chamfer skipped +3.5e-03 and +3.4e-03; chamfer cutter at 45 degrees -4.3e-03 and -4.1e-03), all far above `T_GATE`. See Deviations 1.
- **Sweep wall time.** `test_every_iso_4032_nut_meshes_watertight_at_preview` (28 ids: 14 rows x 2 hands) is 33.96 s with `-n0` (about 1.2 s per id) and about 6 s on 8 workers. All 28 pass, 0 open edges. The 42-id crossing test is cheap (one cutter per id).
- **Positive control for the sweep.** With `CROSS_FRACTION` 0 (the cone ends on the root) M6 right at clearance 0.1 builds through every volume gate and its preview mesh reads 8 open edges; M6 left at clearance 0 reads 3. The same cutter fails the geometric test. Both nets are shown to see what the volume gates cannot.
- **`make verify`.** Final result line `3243 passed in 137.72s (0:02:17)`, total coverage 98.09% against the 96.0% requirement (the run before Task 3 read `3171 passed in 145.81s`). The host was loaded throughout (load averages 6 to 9 with other sessions running), so the absolute number is inflated and above both the 101.65 s of R14 and the ~110 s line. A back-to-back like-for-like measurement, `pytest -n 8 --no-cov`, base commit c7962a2 in a throwaway worktree against HEAD: **101.36 s (3144 passed) against 109.69 s (3243 passed)**, so this plan adds about 8 s (8 %) to the suite on the same host at the same load. Nothing was trimmed. The owner decides whether to move any of the sweep under the `grid` marker.

## Deviations from Plan

### Plan claims that did not hold as written

**1. The plan's interface for `finish` is changed.** The plan lists `finish(p, nut) -> cq.Shape`. The builder must judge each of the four cuts by its own volume, which needs the nut after each cut, and `solid/nut.py` cannot call the kernel's volume integrator (it lives in `screw.solid`, which imports `nut`). `finish` is therefore a generator of `(piece name, nut after that cut)`; the acceptance criterion `def finish(` holds and the builder consumes it. No requirement is weakened: the whole gate and all four piece checks run.

**2. The whole-nut gate alone sees all four controls on a nut.** Unlike the bolt (05-12, where it missed two of six), a countersink or chamfer is 1 to 2 % of an M6 nut, so `T_GATE` flags every planted control. The plan only claims the piece check refuses them; it does. The test `test_the_whole_nut_gate_alone_sees_each_control_a_nut_is_not_a_long_bolt` asserts the measured fact, not a prediction, and the piece check is still what names the wrong piece.

**3. The crossing test reads the root radius directly.** The plan says the inner radius is below `rr + clearance`; `_radii` already includes the clearance, so the test compares with `d/2 - 5H/8 + clearance`, written out independently of `nut.py`. A catalogue nut whose cone cannot cross at that clearance is asserted to carry the `clearance` warning instead, and the capped case has its own test (flat bottom above the root).

### Auto-fixed Issues

**4. [Rule 1 - Bug] Tests that compared a nut to the end-less closed form.** Four tests in `tests/test_nut.py` and one in `tests/test_calc.py` read `nut_closed_volume`, and two clearance-difference tests assumed the void's section difference alone; with countersinks the looser nut's shallower cones change the answer. They now read `nut_end_closed_volume`, the clearance-difference tests use the difference of the end-aware forms, and one asserts the bare section difference would have been the wrong answer by more than ten gates.

**5. [Rule 3 - Blocking] Lint.** SIM105 and E501 on a try/pass in `derive` (now `contextlib.suppress`) and one long line in `nut.py`.

### Process notes

- No separate RED commits: the pre-commit hook runs `make verify`, so a failing test cannot land (as in 05-11 and 05-12). The nut tests were written after a first manual build and measurement of every row, and each control was observed to be refused.
- Task 3's `L15` is this phase's decision entry, which plan 05-18 writes; until then the warning cites an entry the log does not yet hold (as the plan states).

## Known Stubs

None.

## Threat Flags

None. T-05-28 (grazing countersink): mitigated by the overshoot, `test_every_countersink_crosses_the_void_root`, the catalogue sweep and the positive control above. T-05-29 (overlapping cutters at small m): mitigated by `end_depths`' R5 cap, which the oracle and the cutter both use, and a capped-nut test.

## Authentication gates

None.

## Verification

`make verify` (ruff, mypy `--strict`, import-boundary contracts, unfinished-work scan, pytest): `3243 passed in 137.72s (0:02:17)`, coverage 98.09%; the same gate passed in the pre-commit hook of each of the three task commits. `.venv/bin/screw info bolt` prints the new warning first.

Debt filed: none. (The nut build is now about 1 s, against 0.15 s before; not filed as debt because it sits well inside the interim build bounds, but it is the number to watch if a deadline is ever tightened.)

## Self-Check: PASSED

- FOUND: src/screw/solid/nut.py (`def countersink(`, `def face_chamfer(`, `def finish(`; no `tables` in its text), src/screw/calc/thread.py (`def nut_end_closed_volume(`), src/screw/calc/__init__.py (`ends modelled per L15`)
- FOUND: `nut_end_closed_volume(` in src/screw/solid/__init__.py's nut branch; `grep -rn 'plain-cut thread ends' src tests` prints nothing
- FOUND: commits 7557806, 8dc388c, a641c40 (ancestors of HEAD)
