---
phase: 08-pre-release-gap-closure
plan: 07
subsystem: bench
tags: [fine-sweep, proof-walk, turn-ceilings, f7, f8, d-06, d-07, d-18, oper-03]

requires:
  - phase: 08-pre-release-gap-closure
    provides: "08-06's freeze sha 09af247 and the three runs dispatched from it; 08-12's bands; 08-03's judge template"
provides:
  - "bench/oper_sets.py fine-ceilings: the F7 and F8 judge (fine_ceilings, fine_ceilings_text, fine_ceilings_block, turn_ceiling, _region, FineCeiling)"
  - "bench/results/phase-08/fine-proof-41684315321, fine-cost-41684331518, fine-spread-41684347573: the runs' records as downloaded"
  - "The printed turn-ceilings block: the empty tuple, because the fine sweep refused nothing in the proof walk"
affects: [08-08, 08-09, 08-10]

actuals:
  tokens: 3981    # chars/4 over the +/- lines of bench/oper_sets.py and tests/test_oper_fine.py (15922 chars); RESULTS.md (about 6200 pasted lines) and the downloaded records are excluded, they are runner output
  tasks: 2
  commits: 2      # MEASURED: git rev-list --count 51b471e..HEAD, before this SUMMARY's own commit

plan_head_before: 51b471eb6efe632e899cc76f12858ea8e0c04ed4
plan_head_after: 3f81fcd7c1087e08947cd444d291f07c5bdd1e4b

tech-stack:
  added: []
  patterns:
    - "A ceiling is judge output over committed records and nothing else: the block is printed, never typed, and a test holds it to the records"
    - "Stops are exceptions with the protocol's rule name (F7, F8) and an S-code in the message; the CLI turns them into exit 3"

key-files:
  created:
    - bench/results/phase-08/fine-proof-41684315321/
    - bench/results/phase-08/fine-cost-41684331518/
    - bench/results/phase-08/fine-spread-41684347573/
  modified:
    - bench/oper_sets.py
    - tests/test_oper_fine.py
    - bench/RESULTS.md

key-decisions:
  - "The dataclass is FineCeiling, not the plan's Ceiling: Ceiling is already the R7 to R10 walls judge's dataclass in the same module"

requirements-completed: []  # OPER-03 closes with 08-09 (the guard) and 08-10

coverage:
  - id: D1
    description: "F7 and F8 are code: every stop (S1 reading faults, S6 shipped-sweep part, S7 fine-sweep nut, S8 N below 3) is a test, ceilings are exact and in ascending band order, a band with no refusal has no ceiling"
    requirement: "OPER-03"
    verification:
      - kind: unit
        ref: "tests/test_oper_fine.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "The three runs' records are committed as downloaded, each with a RESULTS section, and the judge exits 0 on the proof records"
    requirement: "OPER-03"
    verification:
      - kind: other
        ref: ".venv/bin/python -m bench.oper_sets fine-ceilings --from bench/results/phase-08/fine-proof-41684315321"
        status: pass
      - kind: unit
        ref: "tests/test_oper_fine.py::test_the_proof_walk_records_give_the_ceilings_08_09_ships"
        status: pass
    human_judgment: false
  - id: D3
    description: "D-15's two long-thread debt examples are admitted by the guard 08-09 builds"
    requirement: "OPER-03"
    verification:
      - kind: other
        ref: "the plan's step 5 check: refused D-15 examples: []"
        status: pass
    human_judgment: false

duration: n/a
completed: 2026-11-04
status: complete
---

# Phase 8 Plan 07: F7 and F8 judge and the proof runs Summary

**The fine sweep built all 5790 proof-walk points, so F8 prints no ceiling: the guard 08-09 builds ships with `FINE_TURN_CEILINGS = ()`**

## Performance

- **Duration:** not tracked (a long wait on the three runs between Task 1 and Task 2)
- **Tasks:** 2 (two commits)
- **Files modified:** 3 sources and docs, plus three downloaded record directories (106 files)

## Accomplishments

- `python -m bench.oper_sets fine-ceilings --from DIR` applies F7 and F8 to the proof walk's records and prints, per band, F (exact and float), the label that sets it and N, the refusal count and the turns and d / pitch it spans, then the `turn-ceilings` block. Exit 3 on a stop.
- Run results, all dispatched from the freeze sha `09af247322141e81c8584092ab7f92cea66b7cfa` (head sha checked on each):

| Run | Set | Conclusion | Jobs | Readings | Status counts |
|---|---|---|---|---|---|
| 41684315321 | fine-proof (reps 1) | success | 92 of 92 | 5790 of 5790 points | ok 5790 |
| 41684331518 | fine-cost (reps 1) | success | 11 of 11 | 278 of 278 points | ok 278 |
| 41684347573 | fine-spread (reps 5) | success | 6 of 6 | 120 (24 points x 5) | ok 120 |

- F7: every proof point has exactly one reading, every one `ok`; no S1, S6 or S7. F8: band-1 (d 1.55 to 3.35 mm) has no refused or crashed reading across 2174 bolt points (3 to 90 turns, d / pitch 6.499978333405555 to 20.0), among them the 490 cells the shipped sweep refused in the band walk and the debt's four examples; no ceiling, no S8.
- D-15's check (step 5): with no ceiling in band-1 the guard admits both long-thread debt examples (500/7 and 600/7 turns), and all four `proof-debt-` readings are `ok`. The plan's automated check printed `refused D-15 examples: []`.
- F11 held: `git diff 09af247 HEAD -- src/` was empty before the judge ran and again before the commit.

## The printed ceilings block (for 08-09, verbatim from the judge)

`python -m bench.oper_sets fine-ceilings --from bench/results/phase-08/fine-proof-41684315321` (exit 0):

```
band-1: no refusal, no ceiling
# BEGIN turn-ceilings: written by `python -m bench.oper_sets fine-ceilings --from
# bench/results/phase-08/fine-proof-41684315321`; not edited by hand.
FINE_TURN_CEILINGS: tuple[tuple[str, int], ...] = ()
# END turn-ceilings
```

## Task Commits

1. **Task 1: F7 and F8 from synthetic readings to the printed block (tracer)** - `dca2665` (feat)
2. **Task 2: the three runs' records, RESULTS sections and F8's output** - `3f81fcd` (bench)

## Files Created/Modified

- `bench/oper_sets.py` - `MIN_CEILING_TURNS`, `_region`, `turn_ceiling`, `FineCeiling`, `_proof_status`, `fine_ceilings`, `fine_ceilings_text`, `fine_ceilings_block`; subcommand `fine-ceilings`
- `tests/test_oper_fine.py` - 20 tests for the judge (all stops, exactness, ordering, empty and adjacency edges, CLI exit codes) and `test_the_proof_walk_records_give_the_ceilings_08_09_ships`
- `bench/RESULTS.md` - `### fine-proof, run 41684315321`, `### fine-cost, run 41684331518`, `### fine-spread, run 41684347573` and `### F7 and F8 from run 41684315321 (08 D-06, D-07, D-18)` under `## Phase 8 fine sweep`
- `bench/results/phase-08/fine-proof-41684315321/`, `fine-cost-41684331518/`, `fine-spread-41684347573/` - records as downloaded

## Decisions Made

None new. The empty tuple is the plan's flagged OPER-03 empty edge (D-06: no refusal, no ceiling; D-01: both the sweep and the guard land).

## Deviations from Plan

**1. [Rule 3 - Blocking name clash] `FineCeiling`, not `Ceiling`.** The plan names the dataclass `Ceiling`; `bench/oper_sets.py` already defines `Ceiling` for the R7 to R10 field-ceiling judge (line 762). Redefining it would break that judge. Named `FineCeiling`; it also carries the refusals it was set from (label, exact turns, exact d / pitch) so the printed text can state the count and spans, and `turn_ceiling(f)` holds N's rule in one place for the adjacency test. Files: `bench/oper_sets.py`. Commit: `dca2665`.

**Total deviations:** 1 (Rule 3). No frozen file touched; no stop fired.

## Issues Encountered

- The runs were still queued or running when Task 1 finished; Task 2 waited on them with `gh run watch` (never re-dispatched). fine-cost and fine-spread finished first, fine-proof last.
- fine-proof's `gh run download` gave 91 artifact directories for 92 jobs (the 92nd job is the `plan` job, which uploads no records, as in the band walk's 151 of 152).
- Commits used plain `git commit` and passed the `make verify` hook; no orphaned process left. The per-plan ledger file `gsd-plan-head-before-08-07` was written after Task 1 with the start head (51b471e); the dispatch reported that head and nothing committed in between.

## Known Stubs

None.

## Threat Flags

None. Only a bench judge, its tests, runner records and RESULTS text changed; no `src/` file.

## Next Phase Readiness

- 08-08 fits `FINE_ENVELOPE` on the fine-proof, fine-cost and fine-spread records; with no ceiling every fine-sweep part is guard-admitted, so none is excluded from the fit.
- 08-09 builds the turns guard from the block above: an empty `FINE_TURN_CEILINGS` means the guard is wired but refuses nothing today. It replaces `test_the_proof_walk_records_give_the_ceilings_08_09_ships` with the `calc.thread` block check. The residual of F13 (cells off the proof grids) is its debt to file.
- Worth the owner's eye at 08-09: the guard D-06 asked for has no data-backed ceiling to enforce; the runner shows no refusal on the fine sweep in the shipped bands on the F6 grids.

## Self-Check: PASSED

- `dca2665` and `3f81fcd` are ancestors of HEAD; `git rev-list --count 51b471e..HEAD` was 2 at the check.
- The three record directories exist and `git status --porcelain bench/results/phase-08` is empty.
- `grep -c "^def fine_ceilings(\|^def fine_ceilings_text(\|^def fine_ceilings_block(" bench/oper_sets.py` prints 3; `fine-ceilings --help` exits 0.
