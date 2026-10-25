---
phase: 06-printed-pair-acceptance
plan: 08
subsystem: testing
tags: [printed-test, run-2, printability-threshold, d-10, r10, info-04]

requires:
  - phase: 06-printed-pair-acceptance
    provides: PR A (#19, squash 16f7041) with the protocol, read_small, threshold_from and the blank run-2 record; the shipped default 0.15 mm (L17, 06-06)
provides:
  - the owner's run-2 record (9 samples), pinned as RUN_2_SHA256 and refused by a make verify test on any later byte change
  - the threshold size, read only by threshold_from from the pinned record: M4 (d 4.0 mm, coarse pitch 0.7 mm)
  - owner ruling R10 (accept the owner's earlier prints as run 2) with its four deviations
  - the bench/RESULTS.md entry for run 2, stating every departure from the protocol
affects: [06-09 the threshold constants, the warning and L18, 06-10 acceptance print]

actuals:
  tokens: 2200
  tasks: 1
  commits: 2

key-files:
  created: []
  modified:
    - .planning/phases/06-printed-pair-acceptance/06-OWNER-RULINGS.md
    - bench/results/phase-06/print-run-2.tsv
    - bench/print_rules.py
    - tests/test_print_rules.py
    - bench/RESULTS.md

key-decisions:
  - "R10 (owner, 2026-10-23, chose b over Claude's recommended a): the M2 to M5 prints the owner made informally before the default shipped are the run-2 record. Task 1 (export run-2, manifest-run-2.tsv) was not executed and Task 2 was resolved by the owner's reported results; Task 3 ran as written."
  - "The run-2 threshold reads M4: M3 0/3 (thread did not print, recorded bind at 0 turns), M4 3/3, M5 3/3. d_min 4.0 mm and P_min 0.7 mm are plan 06-09's to write; this plan only pins the reading."

requirements-completed: []

coverage:
  - id: D1
    description: "The pinned run-2 record loads, reads cleanly as 9 samples, and a copy with one changed byte is refused"
    requirement: "INFO-04"
    verification:
      - kind: unit
        ref: "tests/test_print_rules.py#test_the_run_2_record_is_the_one_pinned"
        status: pass
    human_judgment: false
  - id: D2
    description: "threshold_from over the pinned record returns M4, and COARSE gives its d 4.0 and pitch 0.7, the size bench/RESULTS.md states"
    requirement: "INFO-04"
    verification:
      - kind: unit
        ref: "tests/test_print_rules.py#test_run_2_reads_a_threshold_of_m4_by_d_10"
        status: pass
    human_judgment: false
  - id: D3
    description: "The printed fit results (M3 thread did not print, M4 and M5 pass 3/3 at 0.15 mm) are the owner's hand judgement, transcribed and confirmed"
    requirement: "INFO-04"
    verification:
      - kind: manual
        ref: "owner's report and confirmation of the 9-row table, 2026-10-23; bench/RESULTS.md entry"
        status: pass
    human_judgment: true

duration: "about 20min of agent time; the owner's printing and fit test are not counted"
completed: 2026-10-23
status: complete
plan_head_before: d79b200093ec930fcb2031522252a783766e9675
plan_head_after: d51438a8f7e969d314966106dc2d7ac1d8076756
---

# Phase 6 Plan 08: Run 2, the printability threshold Summary

**The owner's 9-sample run-2 record is pinned, and the landed `threshold_from` reads it as M4 (d 4.0 mm, coarse pitch 0.7 mm); the record is the owner's earlier informal prints accepted under R10, not the pre-registered run.**

## Accomplishments

- Owner ruling R10 appended to `06-OWNER-RULINGS.md` (`471991a`): the owner chose to accept the M2 to M5 parts printed before the default shipped over re-running run 2 as pre-registered, against Claude's recommendation. It names the four deviations below. The landed protocol text was not edited.
- The record: the transcription (owner's report, written down by Claude, confirmed "correct" by the owner, 2026-10-23) was copied byte for byte over `bench/results/phase-06/print-run-2.tsv`; `cmp` equal, sha256 `6c2d924006db1ccca860b665fdc2cbcd3c84137b0edefb417e6c31aab9dd923e`. No cell was edited by this agent.
- Task 3 (`d51438a`): `RUN_2_SHA256` pinned (the diff of `bench/print_rules.py` adds the digest line and a two-line comment, nothing else), two tests added, the RESULTS entry `## Printability run (Phase 6, 06-print-run-2)` written. The size was read only through `threshold_from(read_small(...))`; it was also checked once before pinning (read_small clean, `M4`, `COARSE["M4"] = (4.0, 0.7)`).

Passes per size, n of 3:

| size | d | coarse pitch | passes at 0.15 mm |
|---|---|---|---|
| M3 | 3 | 0.50 | 0/3 |
| M4 | 4 | 0.70 | 3/3 |
| M5 | 5 | 0.80 | 3/3 |

Threshold (D-10): **M4**, so `d_min` is 4.0 mm and `P_min` is 0.7 mm. The owner made no P3 prediction.

## Task Commits

1. **Ruling R10** - `471991a` docs(06): record owner ruling R10, accept the existing M3 to M5 prints as run 2
2. **Task 1: tracer, export and manifest** - NOT EXECUTED under R10 (no commit; no `manifest-run-2.tsv` exists)
3. **Task 2: owner prints and fills** - resolved by the owner's reported results; no commit of its own
4. **Task 3: pin, read, write the result** - `d51438a` docs(06): record run 2 as the owner filled it

`commits: 2` is measured from the ledger base `d79b200`.

## Deviations from Plan

### Owner ruling R10 (departures from the protocol, accepted by the owner)

1. Printed before the default shipped; the parts did not come from `export run-2`; no manifest was committed before printing; the owner did not report where the parts came from.
2. The owner tested a clearance ladder on M4 and M5 ("passed at 0.1 and 0.15, loose at 0.20 and higher"; below 0.1 they bound after half a turn). Only the 0.15 mm result, the shipped L17 default, is in the record; the rest is RESULTS prose.
3. M3: "m2 and m3 were too small for the printer to print thread". The record has only pass and bind, so each M3 sample is `bind`, turns `0`, note `thread did not print`. M2 is outside the record and prose only.
4. Three samples per size, each (size, sample) group on its own bed (M3-1 to M5-3), like run 1; dates not reported.

### Plan criteria not met because of R10

- Task 1 acceptance (`git log -1 --format=%s -- bench/results/phase-06/manifest-run-2.tsv` is `docs(06): pin the manifest of the run-2 parts`; the run-2 manifest committed before the first print; 6 files with every digest and every nut name carrying the default): **not met**. No export was run and no manifest exists, by R10.
- Must-have truths 1 and 2 (parts exported through the shipped default path; manifest committed before the first print): **not met**. T-06-16's mitigation (every nut name carries the shipped default, every digest) has nothing to check; the link from the printed nuts to the default is the owner's word.
- Task 2 acceptance ("the owner replied `recorded` with the dates"): the owner reported results in prose and confirmed the transcription; no dates were reported.
- `files_modified` lists `manifest-run-2.tsv`; it was not created.

### Auto-fixed Issues

None.

## Issues Encountered

None. The pre-commit hook stashes unstaged files and restored the copied record intact (sha256 re-checked after the first commit).

## Authentication Gates

None.

## Known Stubs

None.

## Threat Flags

None. A digest constant, two tests, a record and a document entry; no new network, auth or file-access surface.

## Ideas and debt

None filed.

## Open for the next plans

- INFO-04 stays Pending: 06-09 writes the constants `d_min` 4.0 and `P_min` 0.7, the warning on the UI, API and CLI, and L18; 06-09 completes it. This plan does not.
- The evidence for the threshold is weaker than the pre-registered run would have given (deviations 1 and 2). 06-09's L18 text should say so and cite the RESULTS entry.
- The untracked `.planning/HANDOFF.json`, `.planning/phases/05-hex-nut-and-kernel-pair-proof/.continue-here.md` and `.planning/ui-reviews/` were never staged.

## Self-Check: PASSED

Checked after writing: `bench/results/phase-06/print-run-2.tsv` (sha256 equals `RUN_2_SHA256`), `bench/print_rules.py`, `tests/test_print_rules.py`, `bench/RESULTS.md` and `06-OWNER-RULINGS.md` exist; `471991a` and `d51438a` are ancestors of HEAD; `manifest-run-2.tsv` does not exist, as R10 requires.
