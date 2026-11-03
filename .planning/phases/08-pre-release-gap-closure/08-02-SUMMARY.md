---
phase: 08-pre-release-gap-closure
plan: 02
subsystem: cli
tags: [cli, decision-log, requirements, tech-debt, l34]

requires:
  - phase: 08-pre-release-gap-closure
    provides: "08-01's pushed protocol commit b69aae5 and the band walk dispatched from it (ordering only)"
provides:
  - "L34: screw export and screw pair have no build deadline (D-09, D-21)"
  - "export and pair help lines, a README sentence and a test that pins them"
  - "ROADMAP Phase 8 SC2 naming both commands"
  - "TABL-06 text that agrees with L19"
  - "INFO-05 in 04-11's requirements-completed"
  - "INT-04 and INT-05 filed as tech debt"
affects: [08-10]

actuals:
  tokens: 3700
  tasks: 3
  commits: 3

plan_head_before: bd0093f7f0b9b7c416a60a0a1e34c1ea6f4c62e1
plan_head_after: 6b085cc8fd6d745f87f18611c4bc87a380f9e751

tech-stack:
  added: []
  patterns:
    - "A build path with no deadline is logged as an Lxx and said in the help line a user reads, with a test pinning the help"

key-files:
  created:
    - docs/tech_debt/active/2026-11-03-solid-build-hands-a-cadquery-solid-to-bench-and-tests.md
    - docs/tech_debt/active/2026-11-03-cost-model-does-not-read-the-head-chamfer.md
  modified:
    - docs/architecture/decision_log.md
    - src/screw/cli.py
    - tests/test_cli.py
    - README.md
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md
    - .planning/phases/04-iso-hex-bolts-and-screws/04-11-SUMMARY.md
    - docs/tech_debt/INDEX.md

key-decisions:
  - "L34 (written from 08 D-09 and D-21, no new ruling): screw export and screw pair have no build deadline, no child process and no --timeout flag"
  - "TABL-06 follows L19: the badge flips on a dimension the row prints; head chamfer angle, hand and nut clearance keep the match (D-10)"

patterns-established: []

requirements-completed: [TABL-06, INFO-05]

coverage:
  - id: D1
    description: "export and pair help lines say 'no build deadline, Ctrl-C stops it (L34)'; README names both commands"
    requirement: OPER-03
    verification:
      - kind: unit
        ref: "tests/test_cli.py::test_export_and_pair_say_they_have_no_build_deadline (RED before the edit, green after)"
        status: pass
    human_judgment: false
  - id: D2
    description: "L34 in decision_log.md and ROADMAP SC2 naming both commands, in one commit that changes one ROADMAP line"
    requirement: OPER-03
    verification:
      - kind: other
        ref: "awk on the L34 section for 'screw export', 'screw pair', D-09, D-21, 'Never capped'; git diff --numstat of ROADMAP.md is 1/1; tests/test_runtime_bounds.py passes"
        status: pass
    human_judgment: false
  - id: D3
    description: "TABL-06 text amended to agree with L19; no code or L19 change"
    requirement: TABL-06
    verification:
      - kind: other
        ref: "grep for the new text, the old text absent, commit a1d0796 touches only .planning/REQUIREMENTS.md"
        status: pass
    human_judgment: false
  - id: D4
    description: "INFO-05 traced to plan 04-11; INT-04 and INT-05 filed with INDEX rows"
    requirement: INFO-05
    verification:
      - kind: other
        ref: "SUMMARY diff is 1/1; both debt files carry a Severity line and an INDEX row; commit 6b085cc touches no src, bench or tests"
        status: pass
    human_judgment: false

duration: one session
completed: 2026-11-03
status: complete
---

# Phase 8 Plan 02: CLI build deadline log, TABL-06, INFO-05 and filed debt Summary

**L34 logs that `screw export` and `screw pair` have no build deadline, both help lines and the README say so, and TABL-06, INFO-05 and the audit's INT-04 and INT-05 are closed or filed.**

## Accomplishments

- L34 records D-09's three reasons and D-21 for `screw pair` ("Never capped"), with no child process and no `--timeout` flag. ROADMAP SC2 names both commands, in the same commit.
- `screw --help` shows `no build deadline, Ctrl-C stops it (L34)` for `export` and `pair`. The README Use block has one sentence. `test_export_and_pair_say_they_have_no_build_deadline` pins the help and the README.
- TABL-06 now says the badge flips on a dimension the row prints, and that head chamfer angle, hand and nut clearance keep "matches" (L19, owner ruling 2026-11-01). No code or L19 change.
- `04-11-SUMMARY.md` lists `requirements-completed: [INFO-05]` (one-line change).
- INT-04 (nice) and INT-05 (must) are filed, not fixed.

## Task Commits

1. **Task 1: Tracer, L34 to the help a user reads** - `287e5ea` (docs)
2. **Task 2: Amend TABL-06 to say what L19 ships** - `a1d0796` (docs)
3. **Task 3: Trace INFO-05 and file INT-04 and INT-05** - `6b085cc` (docs)

Each commit passed the `make verify` pre-commit hook.

## Debt filed

- `docs/tech_debt/active/2026-11-03-solid-build-hands-a-cadquery-solid-to-bench-and-tests.md` (INT-04, nice)
- `docs/tech_debt/active/2026-11-03-cost-model-does-not-read-the-head-chamfer.md` (INT-05, must)

## Deviations from Plan

**1. [Rule 3 - Blocking] `cli.py` diff is 4 added and 2 removed lines, not the plan's 3 and 2.**
- **Found during:** Task 1
- **Issue:** the export parser's one-line call with the longer help string would pass ruff's 100 columns.
- **Fix:** the call is wrapped over two lines (`help=` on the second). Only the two help strings changed in behaviour; no deadline code, `grep -c timeout src/screw/cli.py` stays 1.
- **Commit:** 287e5ea

**2. Debt file dates are 2026-11-03** (the commit date, as the plan says), while L34 is dated 2026-11-02 (the day of the rulings, as the plan says).

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED

- 287e5ea, a1d0796 and 6b085cc are ancestors of HEAD; both debt files exist; L34 appears once in the decision log.
- `make verify` passed in the pre-commit hook of each of the three commits.
