---
phase: 06-printed-pair-acceptance
plan: 05
subsystem: testing
tags: [printed-test, run-1, clearance-default, pre-registration, d-07]

requires:
  - phase: 06-printed-pair-acceptance
    provides: PR A (#19, squash 16f7041) with the protocol, the strict reader, default_from and the blank run-1 record
provides:
  - the manifest of the 24 run-1 STL files (4 bolts, 20 nuts), committed before the first print
  - the owner's run-1 record (60 samples), pinned as RUN_1_SHA256 and refused by a make verify test on any later byte change
  - the derived default, read only by default_from from the pinned record: 0.15 mm (D-08 did not fire)
  - the bench/RESULTS.md entry for run 1 with the pass-count table
affects: [06-06 the owner accepts the reading and the default ships, 06-07 range warning, 06-08 run 2]

actuals:
  tokens: 2900
  tasks: 3
  commits: 2

key-files:
  created:
    - bench/results/phase-06/manifest-run-1.tsv
  modified:
    - bench/results/phase-06/print-run-1.tsv
    - bench/print_rules.py
    - tests/test_print_rules.py
    - bench/RESULTS.md

key-decisions:
  - "The run-1 default reads 0.15 mm: every size passes 3/3 from 0.15 mm up and no size is non-monotone. M6 and M8 pass from 0.1, M10 and M12 bind at 0.1 in 3 of 3, and 0.05 binds at every size. The owner's P1 prediction (0.10 mm) was not borne out. The value is a reading of the record by default_from; shipping it is plan 06-06."
  - "The record's provenance is stated, not smoothed over: the owner printed, fit-tested and reported in prose; the orchestrating Claude transcribed the report into the TSV; the owner confirmed the 60-row table as correct on 2026-10-23. The cells are the owner's observations as transcribed and confirmed, not typed by the owner. The agent that pinned the record changed no cell."

requirements-completed: []

coverage:
  - id: D1
    description: "The pinned run-1 record loads, reads cleanly as 60 samples, and a copy with one changed byte is refused"
    requirement: "PAIR-02"
    verification:
      - kind: unit
        ref: "tests/test_print_rules.py#test_the_run_1_record_is_the_one_pinned"
        status: pass
    human_judgment: false
  - id: D2
    description: "default_from over the pinned record returns 0.15, the value bench/RESULTS.md states"
    requirement: "PAIR-02"
    verification:
      - kind: unit
        ref: "tests/test_print_rules.py#test_run_1_reads_a_default_of_0_15_mm_by_d_07"
        status: pass
    human_judgment: false
  - id: D3
    description: "The 24 run-1 STL files on disk match the committed manifest's names, bytes and sha256 (Task 1, tracer)"
    requirement: "PAIR-02"
    verification:
      - kind: other
        ref: "plan 06-05 Task 1 automated verifies against bench/results/phase-06/manifest-run-1.tsv; commit 646b07d"
        status: pass
    human_judgment: false
  - id: D4
    description: "The printed fit results themselves (42 pass, 18 bind) are a hand judgement under D-05 by the owner, transcribed and confirmed"
    requirement: "PAIR-02"
    verification:
      - kind: manual
        ref: "owner's report and confirmation of the 60-row table, 2026-10-23; bench/RESULTS.md entry"
        status: pass
    human_judgment: true

duration: "about 25min of agent time across Tasks 1 and 3; the owner's printing and fit test are not counted"
completed: 2026-10-23
status: complete
plan_head_before: abc31547c352b7208d4359aa35c79a0a9ab73fad
plan_head_after: 3273e51cc20150ca7f5893b73ac28ccfa7339233
---

# Phase 6 Plan 05: Run 1, the printed clearance ladder Summary

**The owner's 60-sample run-1 record is pinned, and the landed `default_from` reads it as a default of 0.15 mm, so D-08 did not fire.**

## Accomplishments

- Task 1 (tracer): `python -m bench.print_matrix export run-1` from the landed code wrote 24 STL files; the manifest (name, bytes, sha256; 4 bolts, 20 nuts) was committed in `646b07d` before the first print.
- Task 2 (owner checkpoint): the owner printed each (size, sample) group, one bolt and its five nuts, on its own bed (12 beds, M6-1 to M12-3, so sample k sits on a bed `-k`, R4), fit-tested every sample loosest first (R3), and reported in prose. The orchestrating Claude transcribed the report into `print-run-1.tsv`; the owner confirmed the full table ("correct", 2026-10-23). This agent did not edit the record: its sha256 was recomputed as `f76753ded41726daec0a11ec4c5eabc5f4d2afb094cbe258d5e9d915aa6db725` before pinning. Print and test dates: not reported by the owner (reported 2026-10-23); none invented.
- Task 3: the digest is pinned as `RUN_1_SHA256` (three added lines in `bench/print_rules.py`, nothing removed), two tests added, and the RESULTS entry `## Printed pair matrix (Phase 6, 06-print-run-1)` written. The outcome was read only through `default_from(read_matrix(load(RUN_1, RUN_1_SHA256)))`, with the counts from a one-off script over `read_matrix` output.

Passes per cell, n of 3:

| size | 0.05 | 0.1 | 0.15 | 0.2 | 0.25 |
|---|---|---|---|---|---|
| M6 | 0/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| M8 | 0/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| M10 | 0/3 | 0/3 | 3/3 | 3/3 | 3/3 |
| M12 | 0/3 | 0/3 | 3/3 | 3/3 | 3/3 |

42 passes, 18 binds (all at 0 turns: the nut would not start), 12 passes noted `loose` (M6 at 0.2 and 0.25, M8 and M10 at 0.25), no R5 reprint. Default (D-07): **0.15 mm**. The owner's P1 prediction of 0.10 mm was not borne out.

Off-protocol, recorded in the RESULTS entry and not in `print-run-2.tsv`: the owner also printed M3 to M5 informally before any default shipped (M3 "too small to print"; M4 and M5 pass at 0.1, bind below). That is not run 2, and no threshold is read from it. Run 2 (06-08) is undecided pending the owner.

## Task Commits

1. **Task 1: tracer, export and pin the manifest** - `646b07d` docs(06): pin the manifest of the run-1 parts
2. **Task 2: owner prints and records** - checkpoint, no commit (the record is committed in Task 3 as the owner left it)
3. **Task 3: pin, read, write the result** - `3273e51` docs(06): record run 1 as the owner filled it (the record, the pin, the tests and the RESULTS entry; its body states the transcription provenance)

`commits: 2` is the measured count since the ledger base `abc3154`.

## Verification

- `make test PYTEST_ARGS="tests/test_print_rules.py -q -n0 --no-cov"`: `45 passed in 0.07s`.
- `make verify`: `3512 passed in 153.15s (0:02:33)`, exit 0 (also run by the commit hook, passed).
- Acceptance criteria of Task 3: the diff of `bench/print_rules.py` adds exactly the digest line and its comment and removes nothing; `git show --stat 3273e51` lists the four files of the task; the RESULTS entry states 0.15 mm and the outcome test asserts 0.15.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Ruff ERA001 on the digest comment**
- **Found during:** Task 3, first `make verify` (lint step).
- **Issue:** the comment wrapped as "...last edit" / "(protocol, Records)", and ruff read the second line as commented-out code.
- **Fix:** reworded the second line to "as the protocol's Records section says". The comment keeps the plan's meaning; it is still exactly two added comment lines plus the constant.
- **Files modified:** bench/print_rules.py
- **Commit:** `3273e51` (the rejected version was never committed)

### Provenance note (not a deviation of code, a departure from the plan's wording)

The plan's Task 2 expected the owner to fill the TSV by hand ("Claude never edits a result cell"). The owner reported in prose and the orchestrator transcribed the cells. The owner confirmed the table. This is stated in the RESULTS entry and the commit body. This agent changed no cell.

## Issues Encountered

None beyond the lint fix. `make verify` exceeds the foreground tool timeout, so it was awaited in the background.

## Authentication Gates

None.

## Known Stubs

None.

## Threat Flags

None. No new network, auth, file-access or schema surface; one digest constant, two tests, a record and a document entry.

## Ideas and debt

None filed.

## Open for the next plans

- PAIR-02 and INFO-04 stay Pending: the default exists only as a reading of the record until plan 06-06 (the owner accepts the reading as permanent; the default ships on every front end). Nothing was shipped here and `clearance` is still required.
- Run 2 (06-08) needs an owner decision, since M3 to M5 were printed informally at clearances that were not the shipped default.
- The untracked `.planning/HANDOFF.json`, `.planning/phases/05-hex-nut-and-kernel-pair-proof/.continue-here.md` and `.planning/ui-reviews/` were left alone.

## Self-Check: PASSED

Checked after writing: `bench/results/phase-06/manifest-run-1.tsv`, `bench/results/phase-06/print-run-1.tsv` (sha256 equals `RUN_1_SHA256`), `bench/print_rules.py`, `tests/test_print_rules.py` and `bench/RESULTS.md` exist; `646b07d` and `3273e51` are ancestors of HEAD.
