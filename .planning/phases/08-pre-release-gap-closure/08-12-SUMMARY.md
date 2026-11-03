---
phase: 08-pre-release-gap-closure
plan: 12
subsystem: calc
tags: [fine-sweep, bands, d-15, d-19, l37, small-d-wall, oper-03]

requires:
  - phase: 08-pre-release-gap-closure
    provides: "08-03's printed fine-bands block and L37/F15; 08-05's uses_fine_sweep with the nut clause and the bolt call site"
provides:
  - "FINE_BOLT_BANDS (one band, d 1.55 to 3.35 mm) as the block fine-bands --from prints, held to the committed records by a test"
  - "uses_fine_sweep for bolts: strictly inside a band and exact d / pitch above FINE_BAND_ABOVE = 6, bands read at call time, no d / pitch-only clause"
  - "The small-d bolt wall of 9 for 0.45 < d < 0.9 mm (L37): SMALL_BOLT_D_MM, SMALL_BOLT_D_PER_PITCH, a 422 pitch_too_fine before the kernel"
  - "The pushed head 08-06 dispatches the proof walk from"
affects: [08-06, 08-09, 08-10]

actuals:
  tokens: 4750    # chars/4 over the diff of the 3 task commits (18983 chars of +/- lines, tests included)
  tasks: 3
  commits: 3

plan_head_before: 5f00d3f1ed12b047768a5cdcbda5f6393cd5efc6
plan_head_after: 9a5a8d676f0f10ba14beba5c19ec34c0ffb231f2

tech-stack:
  added: []
  patterns:
    - "A constant written by a judge is pasted verbatim from the generator's output and held by a test that re-derives the block from the committed records"
    - "A wall that is the owner's ruling (not a margin rule) lives beside the judge-written block, never inside it"

key-files:
  created: []
  modified:
    - src/screw/calc/thread.py
    - bench/oper_lift.py
    - tests/test_oper_fine.py
    - tests/test_solid.py
    - tests/test_thread_maths.py
    - tests/test_fine_pitch.py
    - tests/test_params.py

key-decisions:
  - "The band block is the generator's output, byte for byte; FINE_BAND_ABOVE is a separate constant (D-15), and there is no FINE_BOLT_ABOVE (D-19)"
  - "The small-d wall's refusal text prints the interval edges with float(...):g and not the Fraction, which printed 9/20 and 9/10 in the first draft (caught by the message test; L02)"
  - "The small-d constants sit below MAX_NUT_D_PER_PITCH, outside the pitch-walls block that its judge writes"

patterns-established: []

requirements-completed: [OPER-03]

coverage:
  - id: D1
    description: "The shipped bands are the block the committed records write; the block equals RESULTS' F5 section"
    requirement: OPER-03
    verification:
      - kind: unit
        ref: "tests/test_oper_fine.py::test_the_shipped_bands_are_the_block_the_records_write"
        status: pass
      - kind: other
        ref: "diff of the BEGIN/END fine-bands extracts of calc/thread.py and bench/RESULTS.md is empty; grep -c '# BEGIN fine-bands' prints 1"
        status: pass
    human_judgment: false
  - id: D2
    description: "Both debt long-thread bolts are on the fine sweep and build through every gate (local macOS arm64, development evidence)"
    requirement: OPER-03
    verification:
      - kind: unit
        ref: "tests/test_solid.py::test_the_long_thread_debt_examples_build_on_the_fine_sweep (d 3 x 25 mm, d 2.5 x 30 mm)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Band edges, d / pitch 6, the D-19 route and the call-time read are pinned; the catalogue still moves exactly the eight nut rows"
    requirement: OPER-03
    verification:
      - kind: unit
        ref: "tests/test_thread_maths.py (12 new cases) and test_the_fine_sweep_moves_exactly_the_eight_nut_rows"
        status: pass
    human_judgment: false
  - id: D4
    description: "A bolt with 0.45 < d < 0.9 mm above d / pitch 9 is a 422 pitch_too_fine naming d and pitch on the API and exit 2 on the CLI; at 9 or at the edges it is admitted"
    requirement: OPER-03
    verification:
      - kind: unit
        ref: "tests/test_fine_pitch.py (small-d section) and tests/test_oper_fine.py::test_the_judges_walled_edges_and_wall_are_the_small_d_wall_of_calc_thread"
        status: pass
    human_judgment: false

duration: one session
completed: 2026-11-03
status: complete
---

# Phase 8 Plan 12: The bolt bands and the small-d wall Summary

**Long-thread bolts in the measured band (d 1.55 to 3.35 mm, above d / pitch 6) now build on the fine sweep; bolts at d 0.45 to 0.9 mm above d / pitch 9 are refused by the parameter model before the kernel (L37).**

## Accomplishments

- Task 1 (tracer): `FINE_BOLT_BANDS` pasted from `python -m bench.oper_sets fine-bands --from bench/results/phase-08/fine-bands-41635270998` (exit 0), `FINE_BAND_ABOVE = Fraction(6)`, and the bolt clause of `uses_fine_sweep`. The block test regenerates the text from the committed records. Both debt examples (d 3, pitch 0.35, 25 mm, s 4.8, k 1.8; d 2.5, pitch 0.35, 30 mm, s 4, k 1.5; right hand) are on the fine sweep and build through `build(BoltParams(...))`. The tracer gate re-ran end to end through the `make verify` hook and passed, so expansion went ahead.
- Task 2: `SMALL_BOLT_D_MM = (0.45, 0.9)` and `SMALL_BOLT_D_PER_PITCH = 9`, read at call time by `pitch_too_fine_refusal`; the same `pitch_too_fine` 422 naming d and pitch, before the kernel. d 0.54 at pitch 0.06 (exactly 9) is admitted and one float finer is refused; d 0.45 and 0.9 at d / pitch 15, and d 3 at 15, are admitted; a nut is untouched. `bench.oper_lift._no_pitch_wall` lifts the third constant, and `python -m bench.oper_sets --check` stays clean. `tests/test_oper_fine.py` holds the judge's two edges and the 9 equal to `calc.thread`'s, and that every cell the judge calls walled is refused by the model.
- Task 3: band-edge, d / pitch 6, D-19 and call-time tests, every edge read from `FINE_BOLT_BANDS`. `test_the_fine_sweep_moves_exactly_the_eight_nut_rows` is green with the bands in place: no bolt row and neither default part is fine.

## Re-pinned test values

- `tests/test_thread_maths.py::test_no_bolt_is_fine_until_a_band_exists` (08-05, described the pre-band state) became `test_a_bolt_outside_every_band_keeps_the_shipped_sweep`: the `(3, 0.35)` case left (it is in the band now), the rest kept.
- `tests/test_oper_fine.py::test_the_band_walk_records_give_the_bands_08_12_ships` became `test_the_band_walk_records_give_one_band_and_the_walled_cells` (same assertions, new name), beside the new block test the plan names.
- `tests/test_params.py::test_the_exact_90_turn_row_is_accepted_though_float_division_reads_above_90`: d 0.6 to d 0.45 at pitch 0.03 (length 2.7). Its d 0.6 at d / pitch 20 is inside the L37 interval and over the wall of 9. The test is about the exact decimal turn count, which d 0.45 (d / pitch 15, an edge outside the interval) still tests. No cost-model value, runner pin or threshold moved.

## Task Commits

1. **Task 1: the bands and the bolt clause** - `9c4904a` (feat)
2. **Task 2: the small-d wall of 9** - `496c3d8` (fix)
3. **Task 3: the edge and D-19 pins** - `9a5a8d6` (test)

Each passed the `make verify` pre-commit hook. The first attempt of Task 1 and of Task 2 failed the hook's ruff step (a Yoda comparison, line lengths) and the first Task 2 attempt failed one pytest case (the params test above); nothing was committed until the hook passed.

## Deviations from Plan

**1. [Rule 1 - Bug] The L37 refusal text printed the interval as `9/20` and `9/10`.** Found by the new message test: the first draft interpolated the `Fraction` constants. Fixed with `float(...):g` (L02: a number the tool prints is one someone acts on).

**2. [Rule 3 - Blocking] Task 1 also edited `tests/test_thread_maths.py`** (the stale 08-05 test above): the pre-commit hook runs the whole suite, and the old test asserted `(3, 0.35)` was not fine. Task 3 then added the edge tests to the same file as planned.

**3. [Rule 1 - Bug in a test] `test_the_exact_90_turn_row...`** moved to d 0.45, as above.

Otherwise the plan ran as written. Acceptance checks: `grep -c "# BEGIN fine-bands"` is 1 and the block `diff`s empty against RESULTS' F5 section; `git diff --quiet origin/main -- src/screw/calc/cost.py src/screw/solid/pair.py` exits 0; `grep -v '^#' src/screw/calc/thread.py | grep -c FINE_BOLT_ABOVE` prints 0.

## Known Stubs

None.

## Threat Flags

None. The only new refusal reads the existing `d` and `pitch` fields at the existing validation boundary.

## Debt

Nothing new filed. `docs/tech_debt/active/2026-11-03-small-d-bolt-wall-refuses-parts-that-built.md` (the owner shipped L37 as is, d4764de) was not touched, and the wall written here is the one it describes.

## Flagged assumption

The macOS arm64 kernel builds both long-thread examples on the fine sweep, as E12 and E14 measured. These are development evidence; the runner proof is 08-06 and 08-07 (D-04).

## Self-Check: PASSED

- 9c4904a, 496c3d8 and 9a5a8d6 are ancestors of HEAD.
- `src/screw/calc/thread.py` holds one `# BEGIN fine-bands`; `.venv/bin/python -m bench.oper_sets --check` exits 0.
