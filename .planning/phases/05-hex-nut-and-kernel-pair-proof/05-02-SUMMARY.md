---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 02
subsystem: testing
tags: [end-cut-probe, oracles, owner-reads, rulings, iso-4032, cadquery]

requires:
  - phase: 05-01
    provides: the pre-registration discipline (inputs and rules written before any reading)
  - phase: 03-threaded-rods
    provides: helical.thread, FINE_STL_ROWS and the L13 rod caps the nut rows are compared against
  - phase: 04-iso-hex-bolts-and-screws
    provides: bolt.thread, bolt.assemble and the head-fuse probe shape this copies
provides:
  - bench/end_cuts.py, the D-10 probe of tip cones, fillet rings, nut countersinks and face chamfers on the shipped thread and void, with seven kernel-free oracles
  - bench/RESULTS.md "End-cut probe (Phase 5, D-10)" with 54 honest rows, the grazing-cone defect, six positive controls and the nut fine-STL bytes at the rod caps
  - 05-OWNER-READS.md, the owner's rulings R1-R13, the ISO 4032:2023 M6 s and m with the permanence line, and every unread item marked PENDING with the plan that needs it
affects: [05-04, 05-05, 05-06, 05-07, 05-08, 05-09, 05-10, 05-11, 05-12, 05-13, 05-17]

actuals:
  tokens: 16200
  tasks: 3
  commits: 3
plan_head_before: 54a0ca5a077c23d5c3267762c866719b75f18ad4
plan_head_after: c9f441f11dbc95aee19d521d1318616b8abd8346

tech-stack:
  added: []
  patterns:
    - "an oracle is checked against an identity that does not use it before any kernel row is judged by it (the first arc formula was off by 2.2x)"
    - "a cutter that must cross the root radius is probed beside one that ends on it, because isValid and the volume gate cannot see the open edges of the second"
    - "an owner record marks every unread item PENDING with the plan that needs it, and a later plan's precondition reads the marker"

key-files:
  created:
    - bench/end_cuts.py
    - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-OWNER-READS.md
  modified:
    - bench/RESULTS.md
    - tests/test_bench.py
  removed:
    - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-RULINGS-PENDING-READS.md

key-decisions:
  - "R11: the differential end-cut tolerance is 0.03 (10 x the probe's largest piece error 2.737e-03, rounded up to one significant figure)"
  - "R6: FRNT-06 takes 0.5 of the 0.05 mm proof clearance and keeps the 0.01 mm fine preset"
  - "R1 a, R5 a, R7 yes, R8 yes, R9 yes, R10 a, R13 b; R2, R3, R4 and R13 stay conditional on reads that are PENDING"
  - "Permanence for the M6 s 10.0 and m 5.2 (m max) was given on 2026-10-14 on a secondary source (a web page print), not the standard"

requirements-completed: [TYPE-03, THRD-05, INFO-01, INFO-02, FRNT-06]

coverage:
  - id: D1
    description: "The end-cut probe: tip cone, fillet ring, nut countersink and face chamfer cut from the shipped thread and void, judged against kernel-free oracles, with the grazing-cone defect and the positive controls on record"
    requirement: "THRD-05"
    verification:
      - kind: unit
        ref: "tests/test_bench.py#test_the_end_cut_oracle_hexagon_arc_integrates_to_the_hexagon_area"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_the_end_cut_probe_agrees_with_its_oracles_on_the_smallest_case_of_each_cutter"
        status: pass
      - kind: other
        ref: "grep -c '^## End-cut probe (Phase 5, D-10)' bench/RESULTS.md -> 1; make verify exit 0"
        status: pass
    human_judgment: false
  - id: D2
    description: "05-OWNER-READS.md: the permanence line, the M6 s and m, thirteen rulings, and the unread items marked PENDING with the plan that needs each"
    requirement: "TYPE-03"
    verification:
      - kind: other
        ref: "grep -c '^Permanence acknowledged: 20[0-9-]*, permanent: accepted' 05-OWNER-READS.md -> 1; grep '^- R1'..'^- R13' all present"
        status: pass
    human_judgment: true
    rationale: "s and m come from a one-page print of a web page transcribing ISO 4032:2023, read by an agent, not from the standard and not by the owner; reads 3 to 7 are pending; only the owner can say the frozen defaults match the standard."

duration: about 3h wall across two sessions (mostly waiting on the owner; active time not captured)
completed: 2026-10-14
status: complete
---

# Phase 5 Plan 02: End-cut probe and the owner's reads and rulings Summary

**The end cuts are probed on the shipped thread against seven kernel-free oracles (54 honest rows, one valid solid and no open edges each, largest piece error 2.737e-03), and the owner's thirteen rulings and the ISO 4032 M6 defaults (s 10.0, m 5.2 as m max) are recorded, with the M6 values read from a web-page print rather than the standard and reads 3 to 7 still pending.**

## Performance

- **Duration:** about 3h wall across two sessions, mostly the owner stop; the start time was not captured at launch
- **Completed:** 2026-10-14
- **Tasks:** 3 (Task 2 is the owner checkpoint, resolved by the owner's reply)
- **Files:** 4 changed by the plan (`bench/end_cuts.py`, `bench/RESULTS.md`, `tests/test_bench.py`, `05-OWNER-READS.md`) plus one removed (`05-RULINGS-PENDING-READS.md`)

## Accomplishments

- **Probe (Task 1, `79b32af`).** `bench/end_cuts.py` builds every case through the shipped `helical.thread`, `bolt.thread` and `bolt.assemble` and judges it against `a_out`, `tip_cone_removed`, `mat_in_disc`, `countersink_removed`, `arc_inside`, `face_chamfer_removed` and `ring_volume`. Ten oracle tests in `tests/test_bench.py` check each against an identity that does not use it, so a wrong formula cannot be recorded. One run (96.4 s) is recorded in `bench/RESULTS.md`: all 54 honest rows are one valid solid with 0 open edges at the preview and fine meshes, whole-part error at most 1.97e-05 against `T_GATE` 9e-05.
- **What the probe found.** Largest honest piece error 2.737e-03 (tip 45 degrees, M2 right, a 0.0444 mm3 piece), the input of R11. A countersink that ends exactly on the root radius is valid with the right volume but meshes open (8 and 4 open edges on the right-hand M6 nut, 9 and 752 on the left), which `isValid` and the volume comparison do not see; every countersink in the nut rows therefore crosses the root radius. The piece comparison flags all six positive controls; the whole-part comparison at `T_GATE` flags five and misses the dropped ring on M10 x 200 (0.73 of `T_GATE`), the dilution P8 predicted.
- **Owner record (Task 3, `c9f441f`).** `05-OWNER-READS.md` carries the permanence line, `s` 10.0 and `m` 5.2 (m max), the source caveat at the top, the nine sections, every pending read with the plan that needs it, and R1 to R13 quoted with the plan that applies each. It folds in and removes `05-RULINGS-PENDING-READS.md`.
- **R12 stated, not chosen.** The probe's nut fine-STL table is in the record. Read against the ruling's own condition (the nut fits the 64 MiB budget at each rod cap and does not at cap + 1) it holds on none of the three sizes measured: M10 right and M20 right fit at cap + 1 as well (0.973, 0.936), and M20 left is already over at the cap (1.003). Plan 05-05 must surface this to the owner before it edits `download_refusal`.

## Task Commits

1. **Task 1: end-cut probe, oracles, RESULTS entry** - `79b32af` (test)
2. **Task 2: owner read and rulings** - owner checkpoint, no code; the rulings were first recorded on their own in `5ca0c6a` (docs)
3. **Task 3: owner record** - `c9f441f` (docs)

**Plan metadata:** the commit that adds this SUMMARY, STATE.md and ROADMAP.md. `commits: 3` is measured from the ledger (`git rev-list --count 54a0ca5..c9f441f`).

## Deviations from Plan

### Deviations the owner or the orchestrator directed

**1. [D-14 deviation] ISO 4032 M6 `s` and `m` come from a secondary source, read by an agent**
- **Found during:** Task 2 (owner reply)
- **What happened:** D-14 asks for the owner's read of the purchased standard. The values were read by Claude (Opus 5.5, the orchestrator) from `~/Downloads/ISO standards/ISO 4032 - 2023 Hexagon Regular Nuts, Style 1 - Product Grades A and B.pdf`, which is a one-page print of the GlobalFastener.com web page transcribing ISO 4032:2023, not the standard. The owner approved it explicitly ("use it"). No second independent read exists. `permanent: accepted` was given on this basis on 2026-10-14.
- **Recorded:** at the top of `05-OWNER-READS.md` and in the M6 defaults section; this SUMMARY's coverage entry D2 sets `human_judgment: true`.
- **Consequence:** `s` 10.0 and `m` 5.2 become frozen defaults in plan 05-04 (one-way, D-15) on a source that has not been checked against the standard. If the standard differs, the frozen default is wrong for every link that omits `s` or `m`.

**2. [Plan truth unmet] Reads 3 to 7 are PENDING; "all reads before any geometry or table plan" does not hold**
- **Found during:** Task 2 (owner reply)
- **What happened:** the owner holds the standards only partly. Read 1 and half of read 2 (the Annex A sizes, M3.5 and M7 presence, the printed columns) are answered from the secondary source; the face-chamfer clause (3), ISO 724 (4), ISO 965-2 (5), ISO 4753 (6), the owner copy directory (7), the designation, decimal and left-hand forms (read 2) and the standards' own PDFs (read 8) are not.
- **Plan's own stop rule:** Task 2's verification says to stop with nothing further committed if the owner does not hold one of the four standards. The orchestrator directed this plan to continue and record the gap instead. This SUMMARY records that the rule was not applied.
- **Where each pending read blocks:** designation, decimal and left-hand forms: plan 05-07; owner copy and the real ISO 4032 pages: 05-06; ISO 724 and ISO 965-2: 05-08 and 05-09; chamfer clause: 05-11 and 05-13; ISO 4753: 05-11 and 05-12; `iso4014_fillets.tsv`: 05-12. Plans 05-04 and 05-05 need only `s`, `m`, the permanence line and R12, which are recorded.
- **Rulings that depend on a pending read:** R2 (read 6), R3 and R4 (read 3), R13 (read 4); each is recorded with its literal conditional answer.

### Plan acceptance and process notes

**3. [Process] The Task 3 staged-file check lists two entries**
- `git diff --cached --name-status` at the commit listed `05-OWNER-READS.md` (added) and `05-RULINGS-PENDING-READS.md` (deleted), not only the first. The orchestrator directed the fold-in and removal in one commit. The record holds no table value beyond the two M6 defaults, no clause wording and no PDF or render (D-16).

**4. [Process] Task 3 acceptance wording**
- The plan's `Owner copy directory:` line is present but reads PENDING instead of an absolute path, because no directory exists. The two automated checks pass (permanence line count 1, rulings R1 to R13 all present) and the record has the nine sections.

**5. [Process] Commit trailers**
- Task 1's commit (`79b32af`) carries `Co-Authored-By: Claude Sonnet 5.5`, the orchestrator's brief for that session carried Opus 5.5 for the other commits, and `5ca0c6a` carries Opus 5.5. This executor is Claude Sonnet 5.5, and the harness attribution for the commits it makes says so, so `c9f441f` and the metadata commit carry Sonnet 5.5 (the commit was amended once to correct the trailer from the orchestrator's requested text; both runs of `make verify` passed). No history was rewritten beyond that one unpushed commit.

**Total deviations:** 2 directed (D-14 secondary source, pending reads), 3 process notes, 0 auto-fixed code issues. **Impact:** plan 05-04's precondition (permanence line, M6 `s`, M6 `m`) is met; plans 05-06 and 05-08 cannot pass their preconditions until the owner copy and the standards exist.

## Authentication Gates

None. Task 2 was an owner checkpoint (human-action, blocking-human), not an authentication gate.

## Issues Encountered

- The frozen defaults rest on a web-page transcription (deviation 1). Whether to re-read `s` and `m` against the real ISO 4032 before plan 05-04 freezes them is the owner's decision; the owner accepted permanence with the source named.
- R12's condition is not shown by the probe (stated above, not decided here).
- The ledger file for this plan was written in a previous session and holds `54a0ca5`; the count of 3 is measured from it.

## Known Stubs

None. No file changed by this plan holds a stub, placeholder or `TODO`; the PENDING markers in `05-OWNER-READS.md` are a planning record, not code.

## Threat Flags

None. T-05-04 holds: the record carries answers, paths and the two M6 defaults only, no PDF, render or clause wording is in the repository. T-05-05 holds: every probe input is labelled UNVERIFIED and nothing under `src/` reads `bench/end_cuts.py`. T-05-06 holds: each ruling is quoted with the date and the plan that applies it.

## Next Phase Readiness

Plan 05-03 (the other CLI reviews PR #17) does not depend on this plan. Plan 05-04 can start: its precondition reads the permanence line and the M6 `s` and `m`, all present. Plan 05-05 can start but must put the R12 table to the owner first. Plans 05-06 to 05-09, 05-11 to 05-13 must stop on their preconditions until the pending reads land. The requirement IDs in this plan's frontmatter are shared with later plans; the shared-ID gate keeps them Pending until the last declaring plan finishes.

## Self-Check: PASSED

- Files present: `bench/end_cuts.py`, `tests/test_bench.py`, `bench/RESULTS.md` (entry heading count 1), `05-OWNER-READS.md`; `05-RULINGS-PENDING-READS.md` absent as intended.
- Commits `79b32af`, `5ca0c6a` and `c9f441f` are ancestors of HEAD.
- Task 3 automated checks: permanence line count 1, rulings R1 to R13 all matched, nine sections, `Owner copy directory:` and `Rendering route:` lines present.
