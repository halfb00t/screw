---
phase: 06-printed-pair-acceptance
plan: 09
subsystem: calc
tags: [printability, threshold, warning, info-04, l18, d-13, r10]

requires:
  - phase: 06-printed-pair-acceptance
    provides: the pinned run-2 record and threshold_from reading M4 (06-08, accepted under R10); the measured-range warning builder and its two insertion points (06-07)
provides:
  - D_MIN_MM 4.0 and P_MIN_MM 0.7, with THRESHOLD_SIZE, THRESHOLD_RUN and THRESHOLD_ENTRY, in src/screw/calc/printability.py
  - printability_warning(d, pitch), appended by _bolt and _nut, so the page, the API and the CLI print one sentence from derive()
  - a make verify test that re-derives both constants from the pinned run-2 record
  - decision L18, citing R10 and stating the evidence is weaker than the pre-registered run
  - INFO-04 ticked with its evidence
affects: [06-10 acceptance print]

requirements-completed: [INFO-04]

actuals:
  tokens: 12000
  tasks: 2
  commits: 2

key-files:
  created: []
  modified:
    - src/screw/calc/printability.py
    - src/screw/calc/__init__.py
    - tests/test_calc.py
    - tests/test_parity.py
    - tests/test_print_rules.py
    - docs/architecture/decision_log.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "L18 (R7 r7-a): the printability threshold is M4, d_min 4.0 mm and P_min 0.7 mm, read by threshold_from from the pinned run-2 record. The entry cites R10 and says the record is the owner's earlier prints, no manifest, only the 0.15 mm result in the record, so weaker evidence than the pre-registered run."
  - "SC5's cap-and-warn is a warning with no cap and no 422: nothing can be trimmed without changing a d or pitch the user set, and the two numbers are not a conflict between two explicit fields (D-13, L02)."

coverage:
  - id: D1
    description: "D_MIN_MM and P_MIN_MM equal COARSE of threshold_from over the pinned run-2 record; THRESHOLD_RUN equals RUN_2_ID"
    requirement: "INFO-04"
    verification:
      - kind: unit
        ref: "tests/test_print_rules.py#test_the_printability_threshold_is_the_one_run_2_reads"
        status: pass
    human_judgment: false
  - id: D2
    description: "Strict edges: exactly at the threshold nothing warns, one float below either edge does, naming only that edge"
    requirement: "INFO-04"
    verification:
      - kind: unit
        ref: "tests/test_calc.py#test_the_printability_edges_are_strict"
        status: pass
    human_judgment: false
  - id: D3
    description: "Each crossed edge is named, d first, in one sentence; M2 and M2.5 warn on both; none crossed gives no entry"
    requirement: "INFO-04"
    verification:
      - kind: unit
        ref: "tests/test_calc.py#test_a_part_below_the_printability_threshold_warns_naming_each_edge_crossed"
        status: pass
      - kind: unit
        ref: "tests/test_calc.py#test_m2_and_m2_5_warn_on_both_printability_edges"
        status: pass
    human_judgment: false
  - id: D4
    description: "A part below the threshold is never refused or capped: the API answers 200 on info and on the preview model.stl, both kinds"
    requirement: "INFO-04"
    verification:
      - kind: integration
        ref: "tests/test_calc.py#test_a_part_below_the_printability_threshold_still_builds"
        status: pass
    human_judgment: false
  - id: D5
    description: "Warning order: standing warning first, the D-09 sentence then the printability sentence on a nut, the off-row sentence last; two separate sentences; rows unchanged with the sentence off"
    requirement: "INFO-04"
    verification:
      - kind: unit
        ref: "tests/test_calc.py#test_the_printability_warning_keeps_the_warning_order"
        status: pass
    human_judgment: false
  - id: D6
    description: "The CLI and the API print the same document and the same sentence, by fields and by preset"
    requirement: "INFO-04"
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_the_printability_warning_is_the_same_on_the_cli_and_the_api"
        status: pass
    human_judgment: false
  - id: D7
    description: "The page shows the printability sentence under the info panel for a bolt or nut below the threshold, and neither warning for M8 x 16"
    requirement: "INFO-04"
    verification:
      - kind: manual
        ref: "06-09-PLAN.md Task 2 human-check, collected for end-of-phase UAT"
        status: pending
    human_judgment: true

duration: "about 25min of agent time, most of it waiting on make verify"
completed: 2026-10-23
status: complete
plan_head_before: 9f02248a6a868ba2c3ddd83134412e1ae8848fd5
plan_head_after: b608a3adcace2c225050f7c3de9314a18ccf8187
---

# Phase 6 Plan 09: The printability threshold Summary

**A bolt or nut with d below 4.0 mm or pitch below 0.7 mm (M4, as `threshold_from` reads the pinned run-2 record) carries one warning naming each edge crossed, the run and L18, on the page, the API and the CLI, and is still built as asked.**

## Accomplishments

- `printability.py`: `THRESHOLD_ENTRY` "L18", `THRESHOLD_RUN` "06-print-run-2", `THRESHOLD_SIZE` "M4", `D_MIN_MM` 4.0, `P_MIN_MM` 0.7 with a why-comment citing D-10, D-11, R10 and the digest constant, and `printability_warning(d, pitch)`: strict `<` on the stored floats, `:g` in the text, d first then pitch joined by "and". Standard library only.
- `_bolt` appends it after the download refusals and before the counterpart block; `_nut` appends it right after the D-09 sentence and before the M18 note. `grep -c 'printability_warning(p.d, p.pitch)'` is 2.
- `tests/test_print_rules.py::test_the_printability_threshold_is_the_one_run_2_reads` re-derives both constants from the pinned record, so editing a constant or the record alone fails `make verify` (T-06-18).
- No existing test needed its exact warning list changed: the commit adds test lines only (no line of an existing test is removed or edited). `make verify` ran 3550 passed, coverage 97.55 percent.
- L18 appended to the decision log. It cites R10 and lists the four departures (no `export run-2`, no manifest, ladder prose outside the record, M3 thread not printed and recorded as bind at 0 turns, no dates) and says in as many words that the evidence is weaker than the pre-registered run and that nothing ties the printed nuts to the default's export. INFO-04 is `[x]` with its evidence and the traceability row is Complete.

## Task Commits

1. **Task 1 (tracer): the constants, the warning, both kinds, all front ends** - `57b8f36` feat(calc): warn below the printed threshold on bolts and nuts (INFO-04)
2. **Task 2: L18 and INFO-04** - `b608a3a` docs(06): log the printability threshold and record INFO-04 evidence

`commits: 2` is measured from the ledger base `9f02248`.

Tracer gate: `HUMAN_VERIFY_MODE` end-of-phase with automated-only `<verify>`: re-ran the task's verify end to end (the `-k printab` tests, the CLI check of `iso4017:M2x6`, `make verify`); all passed, so expansion to Task 2 proceeded with no checkpoint.

## Deviations from Plan

### Auto-fixed Issues

None. Two things the owner or a reviewer may want to see:

- **R10 adaptation (not a fabrication):** the plan's Task 2 text assumes the run followed the pre-registered export and manifest ("the manifest and record digests, parts built at the L17 default through the default path"). L18 instead cites R10, gives only the record digest, and states there is no manifest. No manifest was written or implied.
- **Wording kept as the plan fixes it:** the warning prints numbers with `:g`, so a d one float below 4.0 reads "d 4 mm is below d_min 4 mm". That is the specified formatting; the comparison is on the stored float, and the boundary test covers it. Cosmetic only and reachable only by typing a value one ulp below the edge.
- The task's `<precondition>` held (the pinned run-2 reading returns `M4`).
- The human-check of Task 2 (the page via `make serve`) was not run by this agent; it is collected for end-of-phase UAT as the plan says.

## Issues Encountered

None. One test of my own initially failed (an off-row ordering case used a nut with no off-row sentence, and the API model test needed the in-process build backend that `tests/test_parity.py` also uses); both were test mistakes fixed before the commit.

## Authentication Gates

None.

## Known Stubs

None.

## Threat Flags

None. A warning sentence built from two floats and constants; no new endpoint, auth path or file access. T-06-18 and T-06-19 are mitigated by the re-derivation test and by the 200-on-info-and-preview-model test.

## Ideas and debt

None filed.

## Open for the next plans

- The page check (`make serve`, ISO 4017 M3 x 6 or smaller, a nut outside M6 to M12, ISO 4017 M8 x 16) is for end-of-phase UAT.
- `PAIR_CLEARANCES` still does not bracket run 1's ladder top (noted in L17); untouched here.

## Self-Check: PASSED

Checked after writing: `src/screw/calc/printability.py`, `tests/test_print_rules.py`, `docs/architecture/decision_log.md` (one `## L18 ` heading, three mentions of `06-print-run-2`) exist; `57b8f36` and `b608a3a` are ancestors of HEAD; INFO-04 is `[x]` once in `.planning/REQUIREMENTS.md`.
