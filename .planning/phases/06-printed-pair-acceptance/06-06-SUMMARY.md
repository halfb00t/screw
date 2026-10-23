---
phase: 06-printed-pair-acceptance
plan: 06
subsystem: parameter-model
tags: [clearance-default, frozen-default, one-way, l17, pair-02, free-helper]

requires:
  - phase: 06-printed-pair-acceptance
    provides: the pinned run-1 record and default_from reading 0.15 mm (06-05)
provides:
  - NutParams.clearance defaults to 0.15 mm, frozen (L02, L17), on every front end
  - _free, the default-carrying float helper with no lower bound (R8, replaces _req)
  - L17 in the decision log, citing run 06-print-run-1, its digests, the owner's profile and the owner's `permanent: accepted`
  - PAIR-02 ticked with evidence; INFO-06's trigger noted as fired
  - the three release debt items' triggers moved to "the first release (after Phase 7)"
affects: [06-07 range warning (R6), 06-08 run 2, 06-09 threshold and L18, 06-10 acceptance print]

actuals:
  tokens: 5300
  tasks: 3
  commits: 2

key-files:
  created: []
  modified:
    - src/screw/params.py
    - tests/conftest.py
    - tests/test_params.py
    - tests/test_nut.py
    - tests/test_api.py
    - tests/test_cli.py
    - tests/test_cli_pair.py
    - tests/test_parity.py
    - tests/test_print_rules.py
    - docs/architecture/decision_log.md
    - .planning/REQUIREMENTS.md
    - docs/tech_debt/INDEX.md
    - docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md
    - docs/tech_debt/active/2026-10-21-fillet-ring-can-overhang-the-head-flats.md
    - docs/tech_debt/active/2026-10-21-screw-pair-exit-codes-collide-with-failure-exits.md

key-decisions:
  - "L17: the nut's clearance default is 0.15 mm, the value default_from reads from the pinned run-1 record. Owner reply, verbatim, 2026-10-23: `permanent: accepted`. One-way: every link that omits clearance means 0.15 forever; a later reading is a superseding decision."
  - "R8 applied as r8-b: `_req` became `_free(default, *, le, ...)`; the generic required-field rule stays in the CLI, the page and the parity tests, and a planted `Field(...)` field still fails it."
  - "R7 applied: L17 now, L18 for the run-2 threshold in 06-09; L17 is not amended in place."

requirements-completed: [PAIR-02]

coverage:
  - id: D1
    description: "NutParams.clearance default is the literal 0.15 and the field is not required"
    requirement: "PAIR-02"
    verification:
      - kind: unit
        ref: "tests/test_params.py#test_the_clearance_default_is_the_frozen_value_l17_records"
        status: pass
    human_judgment: false
  - id: D2
    description: "The shipped default equals default_from over the pinned run-1 record"
    requirement: "PAIR-02"
    verification:
      - kind: unit
        ref: "tests/test_print_rules.py#test_the_shipped_clearance_default_is_the_one_run_1_reads"
        status: pass
    human_judgment: false
  - id: D3
    description: "An omitted clearance and the typed default build the same nut and the same info document"
    requirement: "PAIR-02"
    verification:
      - kind: unit
        ref: "tests/test_print_rules.py#test_an_omitted_clearance_and_the_typed_default_build_the_same_nut"
        status: pass
    human_judgment: false
  - id: D4
    description: "A nut without a clearance builds at the default on the CLI, the API, the schema and a bolt's counterpart link"
    requirement: "PAIR-02"
    verification:
      - kind: unit
        ref: "tests/test_cli.py#test_a_nut_without_a_clearance_takes_the_default"
        status: pass
      - kind: unit
        ref: "tests/test_nut.py#test_a_nut_info_without_a_clearance_is_a_200_at_the_default"
        status: pass
      - kind: unit
        ref: "tests/test_api.py#test_the_nut_schema_carries_the_clearance_default"
        status: pass
      - kind: unit
        ref: "tests/test_parity.py#test_a_bolts_matching_nut_link_opens_a_nut_that_builds_with_or_without_a_clearance"
        status: pass
    human_judgment: false
  - id: D5
    description: "The generic required-field rule still has teeth: a planted required field fails it and the CLI marks it [required]"
    requirement: "PAIR-02"
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_a_planted_required_field_fails_the_required_field_rule"
        status: pass
      - kind: unit
        ref: "tests/test_cli.py#test_a_required_flag_is_marked_required_in_the_help"
        status: pass
    human_judgment: false
  - id: D6
    description: "The owner accepted 0.15 mm as the permanent default (one-way door)"
    requirement: "PAIR-02"
    verification:
      - kind: manual
        ref: "owner reply `permanent: accepted`, 2026-10-23, to the question of shipping 0.15 mm frozen forever (plan 06-06 Task 1); recorded in L17"
        status: pass
    human_judgment: true

duration: "about 40min of agent time, three full make verify runs included"
completed: 2026-10-23
status: complete
plan_head_before: 2140861f4ada8d2389ab8ac1c726f306e03fd92d
plan_head_after: c8d2a7288949111863b0a62aa5f83e36c3b3384c
---

# Phase 6 Plan 06: The clearance default ships Summary

**The nut's clearance defaults to 0.15 mm, the value `default_from` reads from the pinned run-1 record, accepted by the owner as permanent on 2026-10-23, and every front end builds a nut without a clearance at it.**

## Accomplishments

- Task 1 (owner decision, resolved before this agent started): the owner replied `permanent: accepted` on 2026-10-23 to shipping X = 0.15 mm as the default, frozen forever. The context shown to the owner: pass counts M6 and M8 3/3 from 0.10 up, M10 and M12 3/3 from 0.15 up, 0 of 3 below; recorded kernel verdicts at 0.15 for M6, M8, M10 and M12 `proven` for both same-hand pairs and `violated` for mixed hands; the R6 range warning (`d < 6.0` or `d > 12.0`) arrives in 06-07. X is 0.15, which is in the recorded grid, so no fresh `screw pair nut` reading was needed (Pitfall 1 applies only at 0.25).
- Task 2 (tracer, `bace6c2`): `_req` became `_free` (R8, r8-b: same body with `default` in place of `...`, comment rewritten); `NutParams.clearance = _free(0.15, ...)` under a frozen-default comment that names L17, run `06-print-run-1`, the record's full sha256, the profile file and the acceptance date. `REQUIRED_VALUES` is `{}`. The tests that pinned a required clearance now pin the default, and two new tests in `tests/test_print_rules.py` hold the value to the record (literal, and re-derived) and to the omitted-equals-typed adjacency. The plan's automated verify (`screw info nut` clearance row equals the record's reading) exits 0.
- Task 3 (`c8d2a72`): L17 appended in L16's shape; PAIR-02 `[x]` with evidence and its traceability row `Complete`; INFO-06 notes its trigger fired; the three debt items' triggers read "before the first release (after Phase 7)"; none moved to `resolved/`; the standing warning's `not a product build` clause is untouched (D-15).

## Task Commits

1. **Task 1: owner decision** - checkpoint, no commit (reply recorded in L17 and here)
2. **Task 2: tracer, default ships** - `bace6c2` feat(nut): ship the clearance default run 1 reads (L17)
3. **Task 3: docs** - `c8d2a72` docs(06): log L17, record PAIR-02 evidence, move the release triggers

`commits: 2` is measured from the ledger base `2140861`.

## Verification

- `make test PYTEST_ARGS="tests/test_params.py tests/test_nut.py tests/test_api.py tests/test_cli.py tests/test_parity.py tests/test_print_rules.py -q -n0 --no-cov"`: `1 failed, 558 passed` on the first run (a test of mine that expected `SystemExit` from a successful `cli.main`), then `tests/test_cli.py` alone `75 passed`.
- `make verify`: `3514 passed in 192.21s (0:03:12)`, exit 0, before the Task 2 commit; `3514 passed in 151.04s (0:02:31)`, exit 0, before the Task 3 commit; both commit hooks passed.
- Task 3 greps: `^## L17 ` count 1; `^- \[x\] \*\*PAIR-02\*\*` count 1; `Phase 6 release` in the three items 0 and `first release (after Phase 7)` in 3; `not a product build` in `src/screw/calc/__init__.py` count 1; `docs/tech_debt/resolved/` gained nothing.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] A ninth file in the Task 2 commit: `tests/test_cli_pair.py`**
- **Found during:** Task 2, first `make verify` (2 failed, 3512 passed).
- **Issue:** `tests/test_cli_pair.py::test_no_clearance_exits_2_naming_it` pinned `screw pair nut` with no clearance as exit 2, and `test_a_refusal_leaves_the_kernel_out_of_the_process` used `["pair", "nut"]` as a refusal that never loads the kernel. Both pinned the required clearance and are not in the plan's file list or in RESEARCH's blast-radius table.
- **Fix:** Step 3 of the action says any other failing test that pins a required clearance is rewritten to the default the same way, so it was. The first became `test_no_clearance_proves_the_nut_at_the_default`: in-process, `prove` stubbed, asserts it receives a nut with clearance 0.15 (the real proof takes about 40 s and parks the kernel, as that file's docstring says). The second keeps its three refusals, the second now `["pair", "nut", "--s", "6"]`, which is refused by the thin-nut rule at the default clearance before any kernel loads (measured: exit 2 in 0.08 s).
- **Consequence:** the acceptance criterion "`git show --stat HEAD` lists only this task's eight files" is not met as written: the commit lists nine. The plan's own step 3 and that criterion conflict when a ninth test pins the required clearance, and the pre-commit hook runs `make verify`, so the file could not land in a separate green commit. Surfaced here and in the commit body.
- **Files modified:** tests/test_cli_pair.py
- **Commit:** `bace6c2`

**2. [Rule 2 - Consistency] `docs/tech_debt/INDEX.md` rows moved with their items**
- **Found during:** Task 3.
- **Issue:** the INDEX's trigger column for the three items still said "the Phase 6 release", contradicting the items. CLAUDE.md keeps item files and INDEX rows in step.
- **Fix:** the same wording change in the three INDEX rows, nothing else. The plan's file list names only the three item files.
- **Files modified:** docs/tech_debt/INDEX.md
- **Commit:** `c8d2a72`

### Not done, by design

- `requirements mark-complete` was not run: PAIR-02's checkbox, evidence and traceability row were edited in Task 3 as the plan specifies, and INFO-04 is untouched (it needs the run-2 threshold).
- The comment in `src/screw/calc/__init__.py` ("Phase 6 removes the last clause at release", RESEARCH Pitfall 9) and the `PAIR_CLEARANCES` comment in `src/screw/calc/pair.py` were not edited: neither file is in this plan's list. L17 states the second contradiction. The first is open for a later plan or the release.

## Issues Encountered

`make verify` exceeds a short foreground timeout, so each run was waited for in the foreground with the 600 s limit (3.2 min at most).

## Authentication Gates

None.

## Known Stubs

None.

## Threat Flags

None. The default changes the value of an existing field; no new network, auth or file-access surface. T-06-12 and T-06-13 are mitigated: the literal test, the re-derivation test, the omitted-equals-typed test and the frozen-default comment are in `make verify`, and the owner's acceptance is recorded.

## Ideas and debt

None filed. Items touched: `docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md`, `2026-10-21-fillet-ring-can-overhang-the-head-flats.md` and `2026-10-21-screw-pair-exit-codes-collide-with-failure-exits.md` had their triggers moved to "the first release (after Phase 7)", plus their `docs/tech_debt/INDEX.md` rows; none resolved.

## Open for the next plans

- 06-07 wires the R6 range warning (`d < 6.0` or `d > 12.0`); L17 already says so.
- INFO-04 stays Pending (the threshold comes from run 2), PAIR-05 stays Pending (the acceptance print, 06-10).
- L15 still reads "required clearance" in its own text; L17 says it supersedes that part and L15 was not edited.
- The untracked `.planning/HANDOFF.json`, `.planning/phases/05-hex-nut-and-kernel-pair-proof/.continue-here.md` and `.planning/ui-reviews/` were left alone and never staged.

## Self-Check: PASSED

Checked after writing: `src/screw/params.py`, `tests/test_cli_pair.py`, `docs/architecture/decision_log.md` (contains `## L17`) and `.planning/REQUIREMENTS.md` exist and carry the edits; `bace6c2` and `c8d2a72` are ancestors of HEAD.
