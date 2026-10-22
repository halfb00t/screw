---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 14
subsystem: solid
tags: [pair-proof, verdict-rule, import-boundary, shipped-evidence, pair-03, pair-04]
requires:
  - phase: 05-01
    provides: "the expected-verdict table and the re-derivation test over the unmodified rule (P15)"
  - phase: 05-12
    provides: "the shipped bolt with its tip cone (tip_cone_length, TIP_ANGLE_DEG)"
  - phase: 05-13
    provides: "the shipped nut with its ends, and counterpart_for from 05-10"
provides:
  - "src/screw/calc/pair.py: the pair verdict rule, constants, record shapes and closed-form interference integral, kernel-free, moved verbatim from the spike"
  - "src/screw/solid/pair.py: _KEEP, _span, rod_piece, blank, place, check_cover, common (moved verbatim), PairReading, ShippedReading, PairReport, prove(p, *, rod_left_hand, shipped, common)"
  - "pyproject.toml contract 'The serving process and its workers never import the pair proof' with a fresh-interpreter probe and control"
  - "the shipped-solid evidence row in PairReport.shipped, never a verdict input"
affects: [05-15, 05-16, 05-17]
requirements-completed: [PAIR-03]
requirements-held-back: "PAIR-04 needs the screw pair CLI (05-15) and the slow tier (05-16); only its function clause and its not-an-endpoint clause are met here"
estimate_ref: "130000 tokens, 3 tasks"
actuals:
  tokens: 19000
  tasks: 3
  commits: 3
plan_head_before: 269feb64829415da48003683ae351e23ffe3b17d
plan_head_after: 14e0f0ec254c7bffc578788a7053534780b16d10
tech-stack:
  added: []
  patterns:
    - "import-back with `from screw.calc.pair import X as X` in bench.thread_spike.verdict and maths, the closed_volume pattern: one object, two import paths, asserted by identity tests"
    - "prove takes the boolean as a keyword seam (`common`), so the whole orchestration is covered in-process by a scripted fake and only `common` itself runs in a child process (F5, P5)"
key-files:
  created:
    - src/screw/calc/pair.py
    - src/screw/solid/pair.py
  modified:
    - bench/thread_spike/verdict.py
    - bench/thread_spike/maths.py
    - bench/thread_spike/pair.py
    - pyproject.toml
    - tests/test_pair.py
    - tests/test_import_boundaries.py
key-decisions:
  - "The shipped nut starts a whole number of pitches up (2 P), not at the tip cone length + P the plan names: measured, the plan's start is half a thread out of phase (Deviations 1)"
  - "c <= 0 short-circuits before building anything; its reason text is the rule's own, pinned equal by a test"
  - "PairReport.closed_control and .shipped are None where nothing was read, never a number nobody compared against (L02)"
status: complete
---

# Phase 5 Plan 14: The kernel pair proof Summary

`screw.solid.pair.prove(NutParams)` now returns a frozen `PairReport` (`proven | violated | inconclusive`, every reason, the six readings, the control's closed form and band, and the shipped bolt-and-nut evidence row), judged by the spike's rule moved byte-for-byte into kernel-free `screw.calc.pair`, and no import path from `screw.app` or `screw.pool` reaches it.

## Task commits

| Task | Commit | Message |
| ---- | ------ | ------- |
| 1 | 06c1547 | refactor(pair): move the pair verdict rule into calc unchanged |
| 2 | e4c5509 | feat(pair): add the kernel pair proof to the solid package, unreachable from the server |
| 3 | 14e0f0e | feat(pair): print the shipped bolt and nut intersection beside the verdict |

`commits: 3` is measured from the plan-start ledger (`git rev-list --count 269feb6..HEAD` before this summary).

## What was built

- **The rule moved unchanged** (`src/screw/calc/pair.py`). The names the plan lists plus the private helpers `cell_verdict` reads (`_is_empty`, `_off_by`, `_matched`, `_controls`, `_is_mixed`, `_poses_ok`), the `Outcome`/`ReadingOutcome`/`PairVerdict` literals and the four record TypedDicts. The module was assembled by script from text cut out of `verdict.py` and `maths.py`, not retyped. **Identity check, recorded:** every one of the 11 moved text blocks is an exact substring both of the originals at `269feb6` and of the new module (`T_PASS`, the band and empty constants with their comments, the integration points, the clearance and pose constants, the literals, the TypedDicts, `closed_control`, `_nut_body` with its four helpers, `_poses_ok` and `cell_verdict`, `interference_area`). `bench.thread_spike.verdict` and `maths` import each name back; `test_the_spike_verdict_module_re_exports_the_moved_object` and its `maths` twin assert `is` over the literal name lists (24 parametrised cases). The 05-01 re-derivation test and the whole of `tests/test_bench.py` pass unchanged over the moved rule, with no edit to `test_bench.py`.
- **Rule tests with positive controls, kernel-free** (`tests/test_pair.py`): an empty control at each of the three poses is `inconclusive` naming that pose (`theta -2.0944` for the first), a non-empty matched pose is `violated`, c = 0 and c = -0.05 are inconclusive by definition, a mixed-hand cell is `violated` for both rod hands, a failed, timed-out or dead cell is never `proven`, a nut body off its closed form believes no reading, and right and left hand go through the same checks. A fresh `-I` interpreter importing `screw.calc.pair` has neither `cadquery` nor `OCP` in `sys.modules`.
- **The bodies** (`src/screw/solid/pair.py`). `_span`, `rod_piece`, `blank` (the spike's `nut`), `place` and `check_cover` have AST-identical bodies and signatures to the originals. `common` is identical except `measure.precise_volume` became `precise_volume` imported from `screw.solid`, the very function `measure` re-exports. `bench/thread_spike/pair.py` imports all seven names back, keeps `nut = blank`, and `_KEEP` is the same list object, so `bench/m18_probe.py`'s `pair._KEEP.append` is unchanged.
- **`prove`** reads the three matched poses and then their half-pitch controls, builds the `PairRecord` the rule takes, and judges it with `cell_verdict`. `rod_left_hand` is the internal keyword (R7); a mixed pair is read at the matched poses only, as the rule requires (a mixed cell with controls is `inconclusive` in `cell_verdict`). At c <= 0 it reads nothing (R8): `inconclusive` by definition, `readings == []`, `common` called zero times.
- **The contract** `The serving process and its workers never import the pair proof` (`screw.app`, `screw.pool` -> `screw.solid.pair`, `allow_indirect_imports = false`), in the same commit as the module. Positive control: with `import screw.solid.pair` appended to `pool.py` the contract reads BROKEN with the path `screw.app -> screw.pool -> screw.solid.pair`; `pool.py` was restored byte for byte. The runtime half is three fresh `-I` probes in `tests/test_import_boundaries.py`: `import screw.app` and `import screw.pool, screw.solid` leave `screw.solid.pair` out of `sys.modules`, and `import screw.solid.pair` puts it in.
- **The evidence row** (`ShippedReading`, `PairReport.shipped`): `build(BoltParams)` from `counterpart_for(p)` with the rod's hand and `length = thread_length = tip_cone_length(pitch, TIP_ANGLE_DEG) + m + 2 pitch`, against `build(p)`, at the matched poses only, printed beside the verdict. A planted non-empty reading leaves the verdict, reasons and readings equal to the run without it.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug in the plan's placement] The shipped nut starts at 2 P, not at tip cone length + P**
- **Found during:** Task 3, before writing the code (the plan's start is in the must_haves).
- **Issue:** both threads have phase 2 pi z / P, so a nut is at a matched pose only when it starts a whole number of pitches up. `tip_cone_length(P, 45 degrees)` is `5H/8 = 0.5413 P`, so "from z = tip cone length + P" is 1.5413 P, half a thread out of step: that is close to the control pose, not a matched one.
- **Measured** (child process, shipped M6 right-hand bolt and nut, c = 0.10, 2026-10-20), volumes in mm3 at theta -2.0944 / 0 / +2.0944:

  | start of the nut | volume | solids |
  | ---------------- | ------ | ------ |
  | tip cone length + P = 1.5413 mm (the plan) | 8.74720 / 8.74718 / 8.74718 | 1 / 1 / 1 |
  | 2 P = 2.0 mm | 0 / 0 / 0 | 0 / 0 / 0 |

  Constant 8.747 across the poses is the signature of a fixed misphase, not of the pose. On M3 and M4 (c = 0.10 and 0.15) the 2 P start reads 0 at all three poses and the half-pitch control from it reads 0.72 and 1.69 mm3.
- **Fix:** `start = ceil((tip + pitch) / pitch)` pitches, the least whole-pitch start that clears the cone by at least a pitch (2 P for every size, since the cone is always `0.5413 P`). The nut stays clear of the head: its top at the largest slide is 0.21 P below the thread's end.
- **Not changed:** the counterpart's length, the matched poses, the shipped parts, and every verdict input. The row is evidence, and its format is as the plan lists; only the numbers it prints differ from what a literal start would print.
- **Tests:** a kernel-free test pins that the start is a whole number of pitches and at least `tip + P`; `test_the_real_shipped_pair_is_empty_at_whole_pitch_starts_and_not_off_phase` runs M3 in a child process with its two positive controls (the half-pitch control and the plan's own start both read 1 solid).
- **Files modified:** `src/screw/solid/pair.py`, `tests/test_pair.py`. **Commit:** 14e0f0e.
- **For the owner:** if the plan's start was wanted for a reason this measurement does not see, it is one constant in `_shipped`.

**2. [Rule 2 - Missing critical functionality] A shipped build or boolean that raises is a recorded failure**
- `ShippedReading` carries `outcome` and `error` beside the plan's `theta`, `volume`, `solids`, `seconds`. An off-row bolt can fail validation (`_head_too_small` on the counterpart's default `s`) or the kernel can raise; either becomes three `failure` readings with the error text beside the same verdict, never a crash that discards the verdict and never a zero (L02).

**3. [Interpretation] `closed_control` and `shipped` are `None` where nothing was read**
- `closed_control` is `None` for a mixed-hand pair (no control is read) and at c <= 0. `shipped` is `None` when not asked for, at c <= 0, and when the cell did not finish (a kernel exception already ended it; a second boolean on the evidence row is not run behind it). The plan's field list names both fields without a type; `float | None` and `list[ShippedReading] | None` are what L02 asks for.

**4. [Plan prediction not met, rule left as written] An empty control's reason names the pose and the closed form, not the clearance**
- The plan and D-05 say the reason names "the pose and the clearance". `cell_verdict` prints `control at theta -2.0944 reads empty (closed form 12.213 mm3)`, and the rule moves unchanged (prohibition). The report carries `clearance` as a field. Tests assert the measured text and `report.clearance`; 05-15's printer should show the field beside the reasons if the CLI line must name the clearance.

**5. [Plan acceptance not met as written] `grep -c 'pair' src/screw/solid/__init__.py` prints 1, not 0**
- The one line is an existing comment on `TESSELLATION` ("Phase 5 re-chooses it against the pair clearance (FRNT-06)", l.65); nothing imports the pair module. The intent is pinned by an AST test that no import in that file names `pair`, and by the fresh-interpreter probe. The comment is 05-17's to rewrite (R6) and was not touched here.

**6. [Interpretation of R8] At c <= 0 `prove` builds nothing**
- R8 says "the nut solid still builds"; this was read as the product nut (`solid.build(NutParams)`, unchanged and still building at c = 0 and c = -0.05). `prove` itself returns before building the rod or the blank. The by-definition reason is the rule's text for a same-hand cell; `test_at_zero_or_negative_clearance_nothing_is_read` asserts it equal to `cell_verdict`'s so the two cannot drift apart. A mixed-hand pair at c <= 0 gets the same reason rather than the rule's "poses are not the pre-registered ones", which would be misleading.

**7. [Held back] PAIR-04 is not marked complete**
- The plan's frontmatter lists PAIR-03 and PAIR-04. PAIR-04 also requires the `screw pair` subcommand and the slow-tier test, which are 05-15 and 05-16; only PAIR-03 was marked complete.

**8. [Housekeeping] `_loads_tables` in `tests/test_import_boundaries.py` now delegates to a general `_loads(module, code)`**; the table tests are unchanged.

## Measured facts

- **`make verify`:** result line `3313 passed in 132.94s (0:02:12)` (wall 2:13.57), total coverage **97.42 %** against the 96.0 % requirement (`src/screw/solid/pair.py` 89.57 %: the body of `common`, l.116-129, which only runs in a child process (F5), and the one-line guard in `blank` for a nut in pieces, l.83; `src/screw/calc/pair.py` 96.95 %: the two moved `ValueError` guards for a built record missing its volume, l.147 and 188). The three task commits each passed the pre-commit `make verify`.
- **Suite cost.** The host was busy and unevenly so (load averages 12.6 and 8.3 at the two runs), so wall time is not comparable. `pytest -n 8 --no-cov`: base `269feb6` in a throwaway worktree 106.90 s (3243 passed, 550.2 s user + 93.3 s system), HEAD 87.97 s (3313 passed, 608.8 s user + 100.7 s system). CPU time, the part load does not move much, rose 643 s to 709 s: **+66 s of CPU, about +10 %, for 70 tests.** The new tests that cost most: the real shipped child (18.6 s, M3, three matched poses and two controls), the `bodies` fixture (about 3 s once per worker that runs a prove test) and each prove test that places six poses (about 0.5 s per pose, placing and the cover check on a spline solid). Nothing was trimmed; the owner decides whether the child test moves under a marker.
- **`prove` on M6 with a scripted boolean** takes about 3 s: rod 1.5 s, blank 1.5 s. The real six booleans are 35 s serial (RESEARCH F5).
- **Positive control for the contract:** see What was built.

## Known Stubs

None. `readings == []`, `closed_control is None` and `shipped is None` are the defined results where nothing was read, not placeholders.

## Threat Flags

None. No endpoint, auth path or file access was added. `screw.solid.pair` imports `screw.calc.presets` (the tables) for `counterpart_for`; the module is unreachable from `screw.app` and `screw.pool`, and `import screw.solid` still leaves `screw.tables` out of `sys.modules` (its existing test passes).

Threat register: T-05-30 mitigated (contract with `allow_indirect_imports = false`, the runtime probe and its control, the contract shown to break), T-05-31 mitigated (verbatim move, identity tests, the 05-01 re-derivation test over the moved rule), T-05-32 mitigated (the planted non-empty evidence reading leaves the verdict unchanged).

## Notes for 05-15 and later

- `prove` must be called in a process that ends with `os._exit` after flushing (the real `common` parks its boolean).
- `PairReport` field order: verdict, reasons, d, pitch, m, clearance, rod_left_hand, nut_left_hand, readings, closed_control, band, engagement_turns, shipped, seconds.
- No tech-debt or idea item was filed.

## Self-Check: PASSED

- FOUND: src/screw/calc/pair.py, src/screw/solid/pair.py, tests/test_pair.py, tests/test_import_boundaries.py
- FOUND commits: 06c1547, e4c5509, 14e0f0e (each an ancestor of HEAD)
- `pyproject.toml` contains `The serving process and its workers never import the pair proof`; `lint-imports` prints it KEPT (10 contracts kept, 0 broken)
