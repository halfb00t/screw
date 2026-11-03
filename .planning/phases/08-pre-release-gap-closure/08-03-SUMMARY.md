---
phase: 08-pre-release-gap-closure
plan: 03
subsystem: bench
tags: [bench, oper, fine-sweep, band-walk, f5, f15, l37, decision-log]

requires:
  - phase: 08-pre-release-gap-closure
    provides: "08-01's band walk set (bench/points/fine-bands.json) and run 41635270998 dispatched from b69aae5"
provides:
  - "F5's judge: python -m bench.oper_sets fine-bands --from DIR prints the bands, the in-band and walled check cells and the FINE_BOLT_BANDS block"
  - "the band walk's 151 runner records, committed as downloaded"
  - "one band, d 1.55 to 3.35 mm, as printed code for 08-12"
  - "L37 and F15: the small-d bolt wall of 9, the owner's ruling at S5"
affects: [08-05, 08-06, 08-09, 08-10, 08-12]

actuals:
  tokens: 10150    # chars/4 over the authored diff (40593 chars); the 3.5 MB of downloaded records and the RESULTS readings table are not counted
  tasks: 2
  commits: 5

plan_head_before: 7d1bf926d0d1602d3a735242c2dc5ceddcef5b8b
plan_head_after: d17014f36676ff4d1ffc419df955e52cf7b1d97f

tech-stack:
  added: []
  patterns:
    - "A protocol stop is ruled by the owner, logged as an Lxx, and amended into the frozen protocol in its own commit that says the data exists (as 07 R30 did for R31)"

key-files:
  created:
    - bench/results/phase-08/fine-bands-41635270998/
    - docs/tech_debt/active/2026-11-03-small-d-bolt-wall-refuses-parts-that-built.md
  modified:
    - bench/oper_sets.py
    - tests/test_oper_fine.py
    - bench/RESULTS.md
    - docs/architecture/decision_log.md
    - docs/tech_debt/INDEX.md
    - .planning/phases/08-pre-release-gap-closure/08-SWEEP-PROTOCOL.md
    - .planning/phases/08-pre-release-gap-closure/08-12-PLAN.md

key-decisions:
  - "L37 (owner ruling at S5, reply `c`): a bolt with exact d strictly between 0.45 and 0.9 mm has a d / pitch wall of 9; L25's wall of 20 stands elsewhere. Numbered L37 because plan 08-10 writes L36 and its checks name that id"
  - "F15 amends F3, F5 and F6: a refused check cell at 0.45 < d < 0.9 and d / pitch above 9 outside every band is walled, not an S5 stop; every other out-of-band refusal still stops"
  - "The wall's code is plan 08-12's (calc/thread.py, bench/oper_lift.py, tests/test_fine_pitch.py); this plan changes nothing under src/"

patterns-established: []

requirements-completed: []

coverage:
  - id: D1
    description: "F5's judge, every stop tested, F15's walled rule held to its edges"
    requirement: OPER-03
    verification:
      - kind: unit
        ref: "tests/test_oper_fine.py (50 passed): stops S1 to S5, the walled cells, the cells the wall must not hide, the CLI exit 3 and 0"
        status: pass
    human_judgment: false
  - id: D2
    description: "The committed records give one band, 315 in-band check refusals and 40 walled cells"
    requirement: OPER-03
    verification:
      - kind: unit
        ref: "tests/test_oper_fine.py::test_the_band_walk_records_give_the_bands_08_12_ships"
        status: pass
    human_judgment: false
  - id: D3
    description: "Records and RESULTS sections committed, git status of bench/results/phase-08 empty"
    requirement: OPER-03
    verification:
      - kind: other
        ref: "git status --porcelain bench/results/phase-08 prints nothing; grep -Eq '^### fine-bands, run [0-9]{11}$' bench/RESULTS.md"
        status: pass
    human_judgment: false

duration: two sessions, with the S5 stop between them
completed: 2026-11-03
status: complete
---

# Phase 8 Plan 03: The band walk judged by F5 Summary

**F5 reads one bolt band, d 1.55 to 3.35 mm, from run 41635270998; the 40 refusals at d 0.5 to 0.85 mm hit protocol stop S5 and the owner ruled them the parameter model's (L37, F15).**

## Accomplishments

- F5's judge (`fine_bands`, `check_group`, `fine_bands_text`, `fine_bands_block`, the `fine-bands` subcommand), test-first, every stop with its own test (Task 1, `95bc1dd`).
- Run 41635270998 (success, 152 of 152 jobs, sha b69aae5, linux/amd64): 151 artifacts, 4803 readings, 4273 `ok`, 530 refused, none crashed, killed or capped. Committed as downloaded; RESULTS holds the run and the judge's output.
- The edge group gave one band. The debt's d 0.5 to 0.85 mm band does not exist on the runner: every edge cell there read `ok`.
- The check group: 315 refusals inside the band, 40 outside it (the S5 stop), 1158 `ok` outside every band.

## The S5 stop and the ruling

The judge, run on the records as `95bc1dd` wrote it, stopped:

`oper_sets: stop (F5): S5: check-d0.5-q12.5-n90-right was refused at d 1/2, outside every band, and no bolt outside the bands goes on the fine sweep (D-19)`

The 40 cells: d 0.5 to 0.85 in 0.05 steps, all with 90 turns, q 12.5 right hand only (8), q 16 both hands (16), q 20 both hands (16); the smallest refused exact d / pitch is 12.5. The owner was given the protocol's options (a), (b) and (c); the protocol's rule recommended (b). Owner's reply, verbatim: `c`. That is option (c) as 08-SWEEP-PROTOCOL.md writes it, "lower the bolt wall below the refused ratio for that d range (supersede L25 there)", put to them as a wall of d / pitch 9 for d strictly between 0.45 and 0.9 mm.

- **L37** (`docs/architecture/decision_log.md`, dated 2026-11-03) records it with the evidence and the cost. It is L37, not L36: plan 08-10 writes L36 and greps for it once.
- **F15** (`08-SWEEP-PROTOCOL.md`, commit `0158dd3`) amends F3, F5 and F6 after the first runner reading, as 07 R30 did for R31, and says the data exists. A refused check cell is walled, and no stop, exactly when 0.45 < d < 0.9 and exact d / pitch is above 9, outside every band; any other out-of-band refusal still stops at S5.
- The judge (`b8c026d`) lists the walled cells. Tests pin d 0.45, 0.9, 0.4, 0.95, a q 9 cell, a cell between the bands and an n3s cell as still stopping.

## Where the wall's code lands

Plan 08-12, not this plan. This plan changes nothing under `src/`. The wall lives in `calc/thread.py` (`pitch_too_fine_refusal` is the only reader of the walls; `params.py` calls it). 08-12's frontmatter, truths and tasks now carry it as a new Task 2 (files `calc/thread.py`, `bench/oper_lift.py`, `tests/test_fine_pitch.py`, `tests/test_oper_fine.py`), ahead of the push that 08-06 builds on. `bench/oper_lift.py` must lift the new constant or `python -m bench.oper_sets --check` moves.

## What the wall costs (surfaced for the owner)

The ruling was put as refusing the tiny-d parts that fail. The wall is on d / pitch alone, so it also refuses parts that built: 104 of the 144 check cells in the interval above 9 read `ok` (all 3- and 30-turn cells, and the left-hand q 12.5 cells at 90 turns), and 236 of 244 Phase 7 pitch-walk readings in the same region read `ok`. Every failure seen was a 90-turn thread. The wall refuses before the kernel, so L02 holds, but links that carried such parts now get a 422 naming d and pitch. L37 says this; the narrower tool (a turns ceiling for the interval) is filed as debt, cheapest to choose before 08-12 writes the wall.

## The printed block (for 08-12, verbatim)

`python -m bench.oper_sets fine-bands --from bench/results/phase-08/fine-bands-41635270998` (exit 0):

```
# BEGIN fine-bands: written by `python -m bench.oper_sets fine-bands --from
# bench/results/phase-08/fine-bands-41635270998`; not edited by hand.
FINE_BOLT_BANDS: tuple[tuple[Fraction, Fraction], ...] = (
    (Fraction("1.55"), Fraction("3.35")),
)
# END fine-bands
```

## Task Commits

1. **Task 1: Tracer, F5's judge test-first** - `95bc1dd` (feat)
2. **Task 2: the stop, the ruling and the records**
   - `0158dd3` docs: L37 and F15, plus 08-12 carrying the wall
   - `b8c026d` feat: the judge lists walled cells
   - `a173523` bench: the records, the RESULTS sections and the records test
   - `d17014f` docs: the debt item

Each commit passed the `make verify` pre-commit hook.

## Debt filed

- `docs/tech_debt/active/2026-11-03-small-d-bolt-wall-refuses-parts-that-built.md` (must; trigger: the owner wanting those parts back before the first release, or a user report)

## Deviations from Plan

**1. [Owner ruling at a protocol stop] Task 2 step 3 stopped at S5 and resumed after the ruling.**
- **Found during:** Task 2, the judge run
- **Issue:** 40 check cells refused outside every band.
- **Fix:** the ruling above, F15, the judge change and the records, as the plan's Task 2 otherwise writes it.
- **Commits:** `0158dd3`, `b8c026d`, `a173523`

**2. [Rule 3 - Blocking] L37, not L36.** Eight plans reserve L36 for 08-10's fine-sweep entry and 08-10 asserts it appears once.

**3. 08-12-PLAN.md edited** (a later plan): a third task and four more files, so the wall has an owner. No other plan changed.

**4. The RESULTS F5 section pastes the judge's output after the ruling, and records the first run's exit 3.** The plan expects exit 0 from the first run; the first run is named in the section.

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED

- 95bc1dd, 0158dd3, b8c026d, a173523 and d17014f are ancestors of HEAD.
- `bench/results/phase-08/fine-bands-41635270998` exists; `git status --porcelain bench/results/phase-08` is empty.
- L37 appears once in the decision log; `fine-bands --from` exits 0 on the committed records.
