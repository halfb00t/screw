---
phase: 04-iso-hex-bolts-and-screws
plan: 06
subsystem: testing
tags: [bench, corpus, thread-length, oper-02, alert-4]

requires:
  - phase: 04-iso-hex-bolts-and-screws
    provides: "04-04: thread_length (default 20.0) and the folded shank; 04-03: the corpus s and k"
provides:
  - "bench/corpus.py: every one of the 12 entries pins s = 2 d, k = d / 2 and thread_length = length"
  - "sweep labels carry every pinned key (last: d=100 length=200 s=200 k=50 thread_length=200)"
  - "bench/README.md 'The corpus' and the d100 debt item state what the entries pin"
affects: [04-07, Phase 7 (threaded grid and the linux/amd64 re-sweep)]

actuals:
  tokens: 1800
  tasks: 1
  commits: 1
plan_head_before: 699adf116344297c879f4e756e18995bd45a4d64
plan_head_after: 6a949632c01d40175c8940ede6d1415c9dac91a3

tech-stack:
  added: []
  patterns:
    - "A bench workload pins every key whose default changes the part, so a later default change cannot drift recorded figures"

key-files:
  created: []
  modified:
    - bench/corpus.py
    - tests/test_bench.py
    - bench/README.md
    - docs/tech_debt/active/2026-10-11-default-pitch-d100-length200-exceeds-both-interim-backstops.md

key-decisions:
  - "The corpus grid is unchanged; only the keys that keep each entry's Phase 3 meaning were added (no narrowing, OPER-02)"

requirements-completed: [THRD-03]

coverage:
  - id: D1
    description: "Every corpus entry pins s, k and thread_length = length; the grid test spells all 12 out"
    requirement: THRD-03
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_the_skeleton_corpus_is_the_d_by_length_grid"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_every_corpus_entry_is_a_valid_bolt"
        status: pass
    human_judgment: false
  - id: D2
    description: "Sweep labels carry the pinned keys and find_set finds the heaviest entry by its label"
    requirement: THRD-03
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_the_default_sweep_is_the_corpus_labelled_by_every_key_it_pins"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_a_set_is_found_by_the_label_the_sweep_prints"
        status: pass
    human_judgment: false
  - id: D3
    description: "bench/README.md corpus section and the d100 debt item Context say what is pinned and give the Phase 4 repro"
    verification: []
    human_judgment: true
    rationale: "Prose wording; no test reads either file (acceptance criteria checked by grep)"

duration: 8min
completed: 2026-10-11
status: complete
---

# Phase 4 Plan 06: Bench corpus pins thread_length Summary

**All 12 bench corpus entries now pin `thread_length = length` beside `s` and `k`, so the d=100 length=200 part still builds 200 turns instead of the default 20 mm thread.**

## Performance

- **Duration:** about 8 min
- **Completed:** 2026-10-11
- **Tasks:** 1
- **Files modified:** 4

## Accomplishments
- `bench/corpus.py` adds `"thread_length": length` to each entry and the docstring says why (default would quietly make the 200-turn part cheap, OPER-02); the grid is unchanged.
- `tests/test_bench.py` pins the grid with the new key; sweep, `find_set` and unknown-label tests use the new labels.
- `bench/README.md` "The corpus" says each entry carries a head (harness inputs, not ISO rows, not bounds) and pins `thread_length = length`, and still sets no bound.
- The d100 debt item Context gives the Phase 4 repro (`?d=100&length=200&s=200&k=50&thread_length=200`); it stays `Status: active`.

## Task Commits

1. **Task 1: The corpus pins thread_length** - `6a94963` (chore)

**Plan metadata:** committed separately (docs: complete plan)

## Files Created/Modified
- `bench/corpus.py` - the 12 entries with `s`, `k`, `thread_length` pinned
- `tests/test_bench.py` - pinned grid, new labels, heaviest-part assertion
- `bench/README.md` - "The corpus" reworded
- `docs/tech_debt/active/2026-10-11-default-pitch-d100-length200-exceeds-both-interim-backstops.md` - Phase 4 repro line

## Decisions Made
None beyond the plan: grid kept fixed, keys added only.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] A fourth test spelled the heaviest entry**
- **Found during:** Task 1 (`make verify`)
- **Issue:** `test_the_concurrent_scenario_never_builds_the_single_scenarios_part` asserted the last corpus entry as `{d, length, s, k}`; it failed once `thread_length` was added. The plan listed only the grid, label and `find_set` tests.
- **Fix:** Added `"thread_length": 200.0` to that assertion.
- **Files modified:** tests/test_bench.py
- **Verification:** `make verify` -> 1014 passed, coverage 97.21%
- **Committed in:** 6a94963

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Same file, same intent; no scope creep.

## Issues Encountered
None. No filed tech-debt or idea items (the d100 item was edited in place and stays active).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
Ready for 04-07. Phase 7 keeps this corpus fixed from here on; the d100 item's trigger (Phase 7 linux/amd64 re-sweep) is unchanged.

## Self-Check: PASSED

- `bench/corpus.py`, `tests/test_bench.py`, `bench/README.md`, the d100 debt item: present and modified.
- Commit `6a94963` is an ancestor of HEAD; `make verify` exited 0 (1014 passed, 97.21% coverage).
- Plan verification: corpus assertion script printed OK; acceptance greps for `"thread_length": length`, `thread_length=200` (test and debt item), `thread_length` in README corpus section, and `Status: active` pass.

---
*Phase: 04-iso-hex-bolts-and-screws*
*Completed: 2026-10-11*
