---
phase: 04-iso-hex-bolts-and-screws
plan: 04
subsystem: solid
tags: [thread-length, plain-shank, iso-4014, built-thread-length, turn-cap, fine-stl-cap, d-08, d-22, d-27]

requires:
  - phase: 04-iso-hex-bolts-and-screws
    provides: "04-03: bolt_closed_volume(d, pitch, length, s, k, t), the two gates, bolt.thread(p) and bolt.assemble(p, thread), head_too_small, the new standing warning"
  - phase: 04-iso-hex-bolts-and-screws
    provides: "04-02: FINE_STL_ROWS keyed by (d, pitch, left_hand) and fine_stl_refusal"
provides:
  - "BoltParams.thread_length (default 20.0, flag --thread-length, schema group Thread, gt=0, le=INTERIM_MAX_MM, finite)"
  - "calc/thread.py: MIN_TAIL_MM (moved from helical) and built_thread_length(thread_length, length), the one place t is computed"
  - "turn_cap_refusal(t, pitch) and fine_stl_refusal(d, pitch, t, left_hand): both caps read the built thread, with the pinned texts naming thread_length"
  - "bolt.assemble fuses a planar plain shank of diameter d from t to length, then the head; bolt.thread raises a BuildError naming thread_length and length below MIN_TAIL_MM"
  - "info rows thread_length (Thread length (built)) and shank_length (Plain shank length); warnings for a default or explicit thread_length above length and for a folded shank"
affects: [04-05 (request-boundary 422 for two explicit values, short-thread info warning), 04-06 (bench corpus pins thread_length), 04-07, 04-08 (ISO 4017 row fills thread_length = length), 04-14 (L13 records the D-25 model-level acceptance)]

actuals:
  tokens: 16100
  tasks: 1
  commits: 1
plan_head_before: 1032284731de5a397854e07dea027b3b12b1f450
plan_head_after: 6784362ad3ba8d6944cc063c060bb4d5be527fa7

tech-stack:
  added: []
  patterns:
    - "One derived value, one function: built_thread_length is called by the validator, the builder, both closed forms, both caps and derive; none recomputes t"
    - "A model-level exception to a 422 is documented where it lives: the model builds and warns, the request boundary refuses (D-25)"

key-files:
  created: []
  modified:
    - src/screw/params.py
    - src/screw/calc/thread.py
    - src/screw/calc/__init__.py
    - src/screw/solid/helical.py
    - src/screw/solid/bolt.py
    - src/screw/solid/__init__.py
    - tests/test_params.py
    - tests/test_calc.py
    - tests/test_solid.py
    - tests/test_api.py
    - tests/test_cli.py
    - tests/test_thread_maths.py

key-decisions:
  - "The stored thread_length is never rewritten (D-08, L02): a length below the frozen default 20 builds a full-thread screw and derive says so, so old links keep their meaning"
  - "The model refuses no thread_length against length (D-25): BoltParams(length=10, thread_length=30) builds to 10 mm and warns; the 422 for two explicit values is plan 04-05's request-boundary rule"
  - "The `(default)` mark in the exceeds warning is value-keyed (thread_length == the field default), the only thing a model can test; plan 04-05's 422 pre-empts the explicit-equals-default case on the API and CLI"
  - "A shank sliver under MIN_TAIL_MM is folded into the thread by built_thread_length, matching helical's own tail fold; a gap of exactly 0.001 mm keeps its shank"
  - "The fine-STL cap keeps its measured-rod meaning: it reads t, and the head and shank bytes no run measured are recorded as bounded in the cap comment for Phase 7"

patterns-established:
  - "Test fixtures that pin a thread longer than 20 mm now set thread_length equal to length, so they keep testing the full thread they were written for"

requirements-completed: [THRD-03, TYPE-01, INFO-03]

coverage:
  - id: D1
    description: "A bolt with thread_length below length builds as one valid solid inside both gates: the L11 thread over t, a plain d-diameter cylinder from t to length, the head on top, for both hands"
    requirement: TYPE-01
    verification:
      - kind: unit
        ref: "tests/test_solid.py#test_an_iso_4014_shaped_bolt_has_a_thread_a_plain_shank_and_a_head_in_one_valid_solid"
        status: pass
      - kind: unit
        ref: "tests/test_solid.py#test_a_left_hand_iso_4014_shaped_bolt_builds_through_both_gates"
        status: pass
    human_judgment: false
  - id: D2
    description: "A default thread_length below an explicit length is built to the length and warned, never a 422, on the model, the API and the CLI"
    requirement: THRD-03
    verification:
      - kind: unit
        ref: "tests/test_calc.py#test_a_default_thread_below_an_explicit_length_is_built_to_the_length_and_warned"
        status: pass
      - kind: integration
        ref: "tests/test_api.py#test_a_length_below_the_default_thread_is_a_200_with_the_default_warning_never_a_422"
        status: pass
      - kind: integration
        ref: "tests/test_cli.py#test_a_length_below_the_default_thread_is_built_to_the_length_and_warned_not_refused"
        status: pass
      - kind: integration
        ref: ".venv/bin/screw info bolt --length 10"
        status: pass
    human_judgment: false
  - id: D3
    description: "A shank sliver below MIN_TAIL_MM is folded and warned, a gap of exactly 0.001 mm keeps its shank, a thread below the floor is a BuildError naming thread_length and length before the kernel"
    requirement: THRD-03
    verification:
      - kind: unit
        ref: "tests/test_solid.py#test_a_shank_sliver_below_the_floor_is_folded_and_one_at_the_floor_is_built"
        status: pass
      - kind: unit
        ref: "tests/test_solid.py#test_a_thread_below_the_floor_is_refused_naming_both_fields_before_the_kernel"
        status: pass
      - kind: unit
        ref: "tests/test_calc.py#test_a_shank_too_short_to_model_is_folded_into_the_thread_and_warned"
        status: pass
    human_judgment: false
  - id: D4
    description: "The info rows read thread_length (built) and shank_length from t; the turn cap and fine-STL cap read t and name thread_length; a 1e5 mm length with a 20 mm thread is accepted"
    requirement: INFO-03
    verification:
      - kind: unit
        ref: "tests/test_calc.py#test_the_thread_rows_are_the_built_thread_and_the_plain_shank_left_over"
        status: pass
      - kind: unit
        ref: "tests/test_params.py#test_a_thread_past_250_turns_is_refused_naming_thread_length_length_and_pitch"
        status: pass
      - kind: unit
        ref: "tests/test_params.py#test_a_long_length_with_a_short_thread_is_accepted_the_cap_reads_the_built_thread"
        status: pass
      - kind: unit
        ref: "tests/test_calc.py#test_the_fine_stl_cap_reads_the_built_thread_not_the_length"
        status: pass
    human_judgment: false
  - id: D5
    description: "thread_length is refused at 0, below 0, inf, nan and text naming itself on the model, the API and the CLI, accepted at INTERIM_MAX_MM and refused one float above"
    requirement: THRD-03
    verification:
      - kind: unit
        ref: "tests/test_params.py#test_length_s_k_and_thread_length_are_accepted_at_the_interim_bound_and_refused_above_it"
        status: pass
      - kind: integration
        ref: "tests/test_api.py#test_each_field_refuses_zero_negative_infinite_nan_and_text"
        status: pass
      - kind: integration
        ref: "tests/test_cli.py#test_a_bad_value_exits_2_naming_the_field"
        status: pass
    human_judgment: false

duration: 9min
completed: 2026-10-11
status: complete
---

# Phase 4 Plan 04: thread_length and the plain shank Summary

**One `thread_length` field and one `built_thread_length` function turn the bolt into an ISO 4014-shaped part (L11 thread over t, plain d-diameter shank, hex head) with both caps, the rows and the warnings reading the same built thread, in one green commit.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-10-11T16:23:18Z
- **Completed:** 2026-10-11T16:32:24Z
- **Tasks:** 1
- **Files modified:** 12

## Accomplishments

- `BoltParams.thread_length` (20.0, frozen, `--thread-length`, group Thread) with the same bounds as `length`; the stored value is never rewritten.
- `built_thread_length(thread_length, length)` is the only place t is computed: the turn-cap validator, `bolt.thread`, `bolt.assemble`, `_build`, both closed forms, both caps and `derive` all call it. `MIN_TAIL_MM` moved to the kernel-free `calc/thread.py` with its INTERIM comment.
- `bolt.assemble` fuses a planar plain shank at the thread's end (never a cylinder over the thread), then the head; the M6 x 30 / 18 mm case is one valid solid inside both gates, both hands, and a probe at mid-shank reads a full-diameter cylinder.
- Info rows `thread_length` ("Thread length (built)") and `shank_length` ("Plain shank length"); warnings pinned verbatim for default-exceeds, explicit-exceeds and a folded shank. `--length 10` prints the default warning and a 10 mm full-thread screw, never a 422.
- The 250-turn cap reads t and names `thread_length, length and pitch`; the fine-STL cap reads t and starts `thread_length and length: `. A 1e5 mm length with a 20 mm thread is accepted.
- A thread below MIN_TAIL_MM is a `BuildError` naming `thread_length and length` before any kernel call (Alert 6, T-04-08).

## Task Commits

1. **Task 1: thread_length and the plain shank build an ISO 4014-shaped bolt on every front end** - `6784362` (feat)

**Plan metadata:** the docs commit that follows this file (docs: complete plan)

## Files Created/Modified

- `src/screw/calc/thread.py` - `MIN_TAIL_MM`, `built_thread_length`, `turn_cap_refusal(t, pitch)`, `fine_stl_refusal(d, pitch, t, left_hand)` with the pinned texts and the D-22 cap comment
- `src/screw/params.py` - the `thread_length` field and the turn-cap validator on t with `ctx.fields` `["thread_length", "length", "pitch"]`
- `src/screw/calc/__init__.py` - the two new rows, the thread-length warnings, caps on t
- `src/screw/solid/bolt.py` - `thread` over t with the below-floor `BuildError`, `assemble` with the shank
- `src/screw/solid/__init__.py` - `_build` takes t from `built_thread_length`; the kernel-failure text names `thread_length`
- `src/screw/solid/helical.py` - imports `MIN_TAIL_MM`, one definition
- `tests/test_params.py`, `tests/test_calc.py`, `tests/test_solid.py`, `tests/test_api.py`, `tests/test_cli.py`, `tests/test_thread_maths.py` - the new behavior and the ripple of the new field

## Decisions Made

See `key-decisions`. All follow the plan and the cited owner decisions (D-08, D-22, D-25, D-27); nothing needed the decision log.

## TDD Gate Compliance

The task carries `tdd="true"`, and the pre-commit hook runs `make verify`, so a separate failing RED commit is impossible (as in plans 04-02 and 04-03). What each phase showed:

- **RED:** the tests were written and updated first, with `src/` untouched. `tests/test_thread_maths.py` failed at collection (`ImportError: cannot import name 'MIN_TAIL_MM' from 'screw.calc.thread'`); that module is a load failure, not RED evidence on its own, so its behavior tests (`built_thread_length`, the pinned cap texts) are covered by the other RED files and by GREEN. `pytest tests/test_params.py tests/test_calc.py tests/test_solid.py tests/test_api.py tests/test_cli.py tests/test_parity.py` reported **66 failed, 267 passed** (test_params 12, test_calc 13, test_solid 11, test_api 16, test_cli 14; test_parity 0, as the plan expects). Semantic assessment: every failure is on the planned assertion for the new field or text: `thread_length` rejected as `extra_forbidden`, the schema and slug without it, the info keys `thread_length` and `shank_length` absent, the old turn-cap and fine-STL texts, `--thread-length` unrecognised (`SystemExit: 2`), and the shank/fold/floor builds missing. None is a syntax, import or fixture error in the 66.
- **GREEN:** `make verify` exits 0 (ruff, mypy --strict, import contracts, unfinished-work scan, pytest): **982 passed, coverage 97.09 %** (floor 96.0 %). The hook ran it again on commit and passed. The only intermediate defects were a mypy `Shape`/`Solid` assignment in `bolt.assemble` and a `tuple[float, float]` against `approx` comparison in a new test, both fixed before the commit.
- **REFACTOR:** none.

## Deviations from Plan

None - plan executed exactly as written.

Notes on ripple the plan listed only in general terms ("every test the new field breaks"), not deviations: the filename and log-slug assertions in `tests/test_api.py` gained `_thread_length20`; fixtures that build a thread longer than 20 mm (the 160 mm inverted-twist control, the off-whole-turn lengths up to 30.6 mm) set `thread_length` equal to `length` so they still test the full thread they were written for; the three fine-STL expectations that asserted `{cap:g} mm ({turns} turns)` read `{cap:g} mm of thread ({turns} turns)` because the plan pins that text. A stray `tests/test_api.py-E` created by a mistyped `sed -i` was removed before staging.

## Issues Encountered

None that remain. `tests/test_parity.py` and `tests/test_bench.py` needed no edit and pass unchanged, as the plan states.

## Known Stubs

None.

## Threat Flags

None. T-04-08 (shank sliver crashing the kernel) is mitigated as planned: `built_thread_length` folds a sliver, the 0.0005 mm and exactly-0.001 mm cases build, and a thread below 1e-3 mm is a `BuildError` before the kernel. T-04-06 (long cheap shank) is accepted by design; a 1e5 mm length with a short thread is accepted at the model and bounded by INTERIM_MAX_MM and the 30 s timeout, and plan 04-14 records it for Phase 7. No new network, auth or file surface.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for plan 04-05: the names it builds on (`built_thread_length`, `turn_cap_refusal(t, pitch)`, `fine_stl_refusal(d, pitch, t, left_hand)`, the `(default)` warning text) are in the tree. Plan 04-05 owns the 422 for two explicit values at the request boundary (D-25) and the short-thread info warning (IN-01); plan 04-06 pins `thread_length` in the bench corpus and writes `bench/README.md`.

No debt or idea item filed by this plan.

---
*Phase: 04-iso-hex-bolts-and-screws*
*Completed: 2026-10-11*

## Self-Check: PASSED

- `src/screw/calc/thread.py`, `src/screw/solid/bolt.py`, `src/screw/params.py`, `src/screw/calc/__init__.py`, `src/screw/solid/__init__.py`, `src/screw/solid/helical.py` exist and contain the planned definitions (`def built_thread_length(`, `MIN_TAIL_MM = 1e-3` once, none in helical; `built_thread_length(` in all four consumer files; `title="Thread length"`; no `model_fields_set`).
- Commit `6784362` is an ancestor of HEAD.
- `.venv/bin/screw info bolt --length 10` prints the default warning at `warnings[1]` and rows `thread_length` 10.0, `shank_length` 0.0.
- `make verify` exits 0 (982 passed, 97.09 %).
