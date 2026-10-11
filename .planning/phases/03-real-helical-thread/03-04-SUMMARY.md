---
phase: 03-real-helical-thread
plan: 04
subsystem: params
tags: [left-hand-thread, boolean-field, argparse-booleanoptionalaction, duplicate-key-422, isinside-probe, fastapi-dependency]

requires:
  - phase: 03-real-helical-thread
    provides: helical.thread(..., left_hand=) and the precise-volume gate (plan 03-01), the params boundary rules (03-02), the shared download refusal (03-03)
provides:
  - "FastenerParams.left_hand: bool, default False and frozen, group Thread, between pitch and length in the schema, the query model and the CLI flags"
  - "bolt.rod passes the hand to helical.thread; a left-hand rod passes the same THRD-04 gate and is left-handed by an isInside probe on the helix"
  - "CLI --left-hand / --no-left-hand (BooleanOptionalAction, no value) and _Once / _OnceBool: any repeated flag, export's -o, --format and --quality included, exits 2 naming it"
  - "API refuse_repeated_keys: an app-level dependency; a key given twice on any route is a 422 type duplicate naming it, before any value is judged"
  - "download filenames tell the hands apart: bolt_d6_pitch1_left_hand0_length20 / ..._left_hand1_..."
affects: [03-05, 03-06, 03-07, phase-04, phase-05]

actuals:
  tokens: 5400
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "a boolean field is a sibling helper (_b) of the numeric one (_f): no bound, no step, empty unit, still title/group/unit for the parity test"
    - "a CLI parameter is None until given, so argparse Actions refuse a repeat with `is not None`; the API refuses the same thing with one app-level dependency"
    - "handedness is proved by a probe on the helix at z = 2.25 P asserted for both hands in one test; the volume gate cannot see the hand"

key-files:
  created: []
  modified:
    - src/screw/params.py
    - src/screw/solid/bolt.py
    - src/screw/cli.py
    - src/screw/app.py
    - tests/test_params.py
    - tests/test_solid.py
    - tests/test_parity.py
    - tests/test_api.py
    - tests/test_cli.py
    - docs/tech_debt/INDEX.md
    - docs/tech_debt/resolved/2026-10-06-repeated-query-key-silently-wins.md

key-decisions:
  - "The repeat message names the whole option (`--left-hand/--no-left-hand`, `-o/--output`) and the spelling that came second, so `--left-hand --no-left-hand` names both and `-o` is named as typed"
  - "The numeric-vs-bool narrowing in _add_args moved the `annotation is not None` assert before the `is bool` test: mypy otherwise narrows the else branch to None and calls the numeric branch unreachable"
  - "The debt item's Resolved-in line names the CLI half by sha (d849557) and the API half by subject, as plan 03-01 did; plan 03-07 names the final sha"

patterns-established:
  - "Repeat refusal lives in one shared helper (_refuse_repeat) for both argparse actions"
  - "The registry-parametrised parity test builds its expected CLI flags from the model (`--x` then `--no-x` for a bool), never from a list the test keeps"

requirements-completed: [THRD-02]

coverage:
  - id: D1
    description: "left_hand is a boolean on every kind's model: default False, in the Thread group, ordered d, pitch, left_hand, length in the schema, the OpenAPI query and the CLI flags; an omitted key or flag means right-hand"
    requirement: THRD-02
    verification:
      - kind: unit
        ref: "tests/test_params.py#test_the_hand_is_a_boolean_in_the_thread_group_with_no_numeric_bounds"
        status: pass
      - kind: unit
        ref: "tests/test_params.py#test_the_default_hand_is_right_and_frozen"
        status: pass
      - kind: integration
        ref: "tests/test_parity.py#test_the_cli_flags_are_the_model"
        status: pass
      - kind: integration
        ref: "tests/test_parity.py#test_the_cli_and_the_api_print_the_same_document"
        status: pass
    human_judgment: false
  - id: D2
    description: "A left-hand rod is left-handed by an independent isInside probe (inside at -theta, outside at +theta; right-hand the reverse) and passes the same THRD-04 gate as the right-hand rod; the probe fails when the builder ignores the hand"
    requirement: THRD-02
    verification:
      - kind: unit
        ref: "tests/test_solid.py#test_the_hand_decides_which_way_the_thread_climbs_and_both_pass_the_same_gate"
        status: pass
      - kind: unit
        ref: "tests/test_solid.py#test_a_left_hand_rod_exports_as_a_preview_stl_and_a_step"
        status: pass
    human_judgment: false
  - id: D3
    description: "?left_hand=true on the API and --left-hand on the CLI deliver the left-hand solid's bytes; --no-left-hand and the omitted flag deliver the right-hand ones; ?left_hand=banana is a 422 on the field; a value after the flag exits 2"
    requirement: THRD-02
    verification:
      - kind: integration
        ref: "tests/test_api.py#test_a_left_hand_bolt_downloads_under_its_own_filename_and_is_not_the_right_hand_mesh"
        status: pass
      - kind: integration
        ref: "tests/test_cli.py#test_the_hand_flags_build_the_hand_they_name"
        status: pass
      - kind: integration
        ref: "tests/test_api.py#test_left_hand_that_is_not_a_boolean_is_a_422_on_the_field"
        status: pass
      - kind: integration
        ref: "tests/test_cli.py#test_a_value_after_the_hand_flag_is_refused_not_read_as_true"
        status: pass
    human_judgment: false
  - id: D4
    description: "A repeated query key on any route is a 422 duplicate naming it before validation, and a repeated CLI flag exits 2 naming it; one registry-parametrised test covers both front ends"
    verification:
      - kind: integration
        ref: "tests/test_parity.py#test_a_repeated_parameter_is_refused_naming_it"
        status: pass
      - kind: integration
        ref: "tests/test_api.py#test_a_repeated_key_is_a_422_duplicate_not_a_judgement_of_either_value"
        status: pass
      - kind: integration
        ref: "tests/test_api.py#test_a_repeated_key_on_the_schema_route_is_a_duplicate_not_a_404"
        status: pass
      - kind: command
        ref: ".venv/bin/screw info bolt --left-hand --no-left-hand (exit 2, stderr names --left-hand/--no-left-hand)"
        status: pass
    human_judgment: false
  - id: D5
    description: "The page still loads with the new schema property before plan 03-05 gives it a checkbox"
    verification: []
    human_judgment: true
    rationale: "Read from app.js, not run in a browser: a number input given the string false sanitises to empty and partQuery skips empty inputs, so the page builds the right-hand part. Plan 03-05 replaces it with a checkbox; a human looks at the page then."

duration: 7min
completed: 2026-10-10
status: complete
commits: 2
plan_head_before: e451574db47cf6a5d5d28fee94873247c4958c7e
plan_head_after: eaaac855a459b4cb803fd43044555f2956de017e
---

# Phase 3 Plan 04: Left-hand thread and the repeated-parameter refusal Summary

**`left_hand` is a frozen-default boolean on every kind; the API (`?left_hand=true`) and the CLI (`--left-hand` / `--no-left-hand`) build a left-hand thread proved left-handed by an `isInside` probe on the helix, and a repeated query key or CLI flag is refused naming it instead of silently keeping one.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-10-10T14:23:33Z
- **Completed:** 2026-10-10T14:30:13Z (SUMMARY write follows)
- **Tasks:** 2
- **Files modified:** 11 (8 code and test files, 3 docs; `tests/test_cli.py` was not in the plan's list, see Deviations)

## Accomplishments

- `left_hand: bool = False` on `FastenerParams`, from a new `_b` helper: schema `type: boolean`, group `Thread`, empty unit, no bounds; property order d, pitch, left_hand, length; `"banana"` is a 422 `loc ["query", "left_hand"]`.
- The handedness proof, measured on M6 x 1 x 20 with the probe at r = rr + 0.8 (ro - rr), z = 2.25 P, theta = 2 pi z / P: right-hand reads `(inside at +theta, inside at -theta) == (True, False)`, left-hand `(False, True)`. Both hands pass `check_solid` against the same closed form. With `bolt.rod` temporarily ignoring the hand, the probe failed on `assert (True, False) == (False, True)` and the byte-equality tests failed too; the source was restored.
- CLI: `--left-hand` / `--no-left-hand` listed on one invocation line of both `info` and `export`; `--left-hand false` is `unrecognized arguments` (exit 2), never read as true.
- Repeats refused on both front ends: `?d=0&d=5`, `?d=5&d=100000`, `?d=5&d=0`, `/api/schema?kind=bolt&kind=x`, `?left_hand=true&left_hand=false`, `?zz=1&zz=2` are 422 `duplicate`; `--d 5 --d 6`, `--left-hand --left-hand`, `--left-hand --no-left-hand`, `--quality fine --quality preview` exit 2 naming the flag.
- Debt item `2026-10-06-repeated-query-key-silently-wins.md` retired in the fixing commit.

## Task Commits

1. **Task 1: left_hand builds a left-hand thread from the API and the CLI, and a repeated flag exits 2** - `d849557` (feat)
2. **Task 2: a repeated query key is a 422 on every route, and the repeated-key debt item is retired** - `eaaac85` (fix)

**Plan metadata:** the SUMMARY commit and the STATE/ROADMAP commit follow (docs).

## Files Created/Modified

- `src/screw/params.py` - `_b` boolean-field helper; `left_hand` on `FastenerParams` with its D-09 frozen-default comment
- `src/screw/solid/bolt.py` - `rod` passes `left_hand=p.left_hand`
- `src/screw/cli.py` - `_refuse_repeat`, `_Once`, `_OnceBool`; bool branch of `_add_args`; `-o`, `--format`, `--quality` use `_Once`; `--quality` defaults to `None`, `cmd_export` reads `ns.quality or "fine"`
- `src/screw/app.py` - `refuse_repeated_keys` as `FastAPI(dependencies=[Depends(...)])`; module docstring names the duplicate case
- `tests/test_params.py`, `tests/test_solid.py`, `tests/test_parity.py`, `tests/test_api.py`, `tests/test_cli.py` - the new tests and the updated slug, schema and flag pins
- `docs/tech_debt/resolved/2026-10-06-repeated-query-key-silently-wins.md` (moved from active/), `docs/tech_debt/INDEX.md` - item resolved, row moved

## Decisions Made

- The repeat message names the whole option and the second spelling (`--left-hand/--no-left-hand was given more than once (again as --no-left-hand)`), so the contradiction names both flags and `-o` is named as typed. ruff `ARG002` also required `option_string` to be used.
- The `is not None` assert in `_add_args` sits before the `is bool` test: mypy `--strict` narrowed the else branch to `None` and flagged the numeric branch unreachable otherwise.
- The debt item's `Resolved in:` names the CLI half by sha and the API half by subject (as plan 03-01 did); plan 03-07 names the final sha.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] mypy `unreachable` and `arg-type` in `cli.py` (first `make verify`)**
- **Found during:** Task 1
- **Issue:** after `field.annotation is bool`, mypy narrowed the else branch to `None`; and `ns.quality or "fine"` is `Any | str`, not `Quality`.
- **Fix:** moved the `assert annotation is not None` before the `is bool` test; `cast("Quality", quality)` beside the existing `Format` cast.
- **Files modified:** src/screw/cli.py
- **Committed in:** d849557

**2. [Rule 3 - Blocking] ruff `ARG002` (unused `option_string`) and `E501` in `cli.py`**
- **Found during:** Task 1
- **Fix:** one `_refuse_repeat` helper used by both actions, whose message uses `option_string`; two comments reflowed.
- **Committed in:** d849557

**3. [Rule 3 - Blocking] mypy `arg-type` on `params=` with a `list[tuple[str, str]]`**
- **Found during:** Task 2
- **Fix:** a `Pairs` alias with the element type starlette declares (the list type is invariant).
- **Files modified:** tests/test_parity.py
- **Committed in:** eaaac85

**4. [Rule 2 - Missing Critical] Two CLI tests in `tests/test_cli.py`, a file the plan did not list**
- **Found during:** Task 1
- **Issue:** the plan proves the hand at the solid and the document equality in parity, but nothing showed the CLI flag reaches the builder (the info document carries no hand), and L02 forbids building the wrong hand on any front end.
- **Fix:** `test_the_hand_flags_build_the_hand_they_name` (the `--left-hand` STL equals the left-hand solid's export, `--no-left-hand` and no flag equal the right-hand one) and `test_a_value_after_the_hand_flag_is_refused_not_read_as_true`; the API equivalent compares `?left_hand=true` bytes to the left-hand export in `tests/test_api.py`.
- **Committed in:** d849557

---

**Total deviations:** 4 auto-fixed (3 blocking lint/type, 1 missing test coverage). **Impact on plan:** none on behaviour or the contracts. Each failing `make verify` was a first attempt before the commit.

## TDD Gate Compliance

Both tasks are `tdd="true"`. The pre-commit hook runs `make verify`, so a RED-only commit cannot land; RED was shown by running the new tests against the pre-change source and test plus implementation are one commit per task.

- **Task 1 RED:** `make test PYTEST_ARGS="tests/test_params.py tests/test_solid.py tests/test_parity.py tests/test_api.py tests/test_cli.py -q -n0 --no-cov"` before any `src/` edit gave `21 failed, 176 passed`: the schema and slug tests (`AttributeError`/`ValidationError` on a field that did not exist, slug `bolt_d8.3_pitch1_length20` against the expected `..._left_hand0_...`), the two solid tests, `test_the_no_flag_is_a_value...` and `test_a_repeated_parameter_is_refused_naming_it` (no exit 2 for a repeat), the download-filename and log-slug pins in `tests/test_api.py`. `test_left_hand_that_is_not_a_boolean_is_a_422_on_the_field` passed before the change (the foreign-field 422 already names `left_hand`), so it is a regression pin, not RED evidence. Semantic assessment: the target tests ran and failed on the planned assertions for the intended reason.
- **Task 2 RED:** `tests/test_parity.py tests/test_api.py` gave `7 failed, 95 passed`: `?d=0&d=5` and `?d=5&d=100000` answered 200 (`assert 200 == 422`), `?d=5&d=0` judged only the 0 (`input: '0'` greater-than error, not `duplicate`), `/api/schema?kind=bolt&kind=x` answered 404, `?left_hand=true&left_hand=false` 200, and the multi-key case had no `detail`; the debt item's reproductions, as tests. Semantic assessment: intended failures.
- The two tests added after the RED run (`tests/test_cli.py` hand tests and the `left.content == export(...)` line) were checked by mutation instead: with `rod` ignoring the hand they failed (`assert left != right`). `gsd_run check tdd-red-evidence` was not run (no persisted record, as in plans 03-01 to 03-03).

## Issues Encountered

- My first manual repeat-flag loop passed the whole argument string as one word under zsh and so reported `unrecognized arguments`; redone with `eval`, it showed the intended messages. No effect on the tree.
- The dispatch asked for a `Co-Authored-By: Claude Fable 5.1` trailer; the harness attribution for this session names Sonnet 5.5, so both commits carry `Claude Sonnet 5.5`. Plans 03-01 to 03-03 used the other name.
- Until plan 03-05 the page shows `left_hand` as an empty number input (read from `app.js`, not run in a browser); it sends no key, so it builds the right-hand part. The `ui-drops-foreign-hash-keys` item's trigger ("the Phase 3 plan that adds the first shareable field, `left_hand`") belongs to 03-05, which names it.

## Verification

- `make verify` (last run, before the second code commit; the hook re-ran it and passed): ruff `All checks passed!`; mypy clean over 46 source files; import-linter passed; pytest `============================= 833 passed in 28.02s =============================`, coverage `97.02%` against the 94 floor. After Task 1 alone: `827 passed in 29.58s`, `96.98%`.
- `make test PYTEST_ARGS="tests/test_params.py tests/test_solid.py tests/test_parity.py tests/test_api.py tests/test_cli.py -q -n0 --no-cov"`: `197 passed` (Task 1 state); `tests/test_parity.py tests/test_api.py`: `102 passed` (Task 2 state).
- `.venv/bin/screw info bolt --left-hand --no-left-hand`: exit 2, `screw info bolt: error: --left-hand/--no-left-hand was given more than once (again as --no-left-hand)`.
- `.venv/bin/screw info bolt --help | grep -E '^ +--left-hand, --no-left-hand'` prints `  --left-hand, --no-left-hand`.
- Acceptance greps: `left_hand: bool` in `FastenerParams` (params.py line 75, before `BoltParams`); `left_hand=p.left_hand` in bolt.py; `class _OnceBool(argparse.BooleanOptionalAction)` and `class _Once(argparse.Action)` in cli.py; `grep -c 'type=bool' src/screw/cli.py` is 0; `isInside` with both `left_hand=True` and `left_hand=False` in tests/test_solid.py; `def refuse_repeated_keys(` and `dependencies=[Depends(refuse_repeated_keys)]` in app.py; the debt item is under `## Resolved` only, `Status: resolved`, active copy gone.

## Debt

- Resolved: `docs/tech_debt/resolved/2026-10-06-repeated-query-key-silently-wins.md` (must), INDEX row moved in `eaaac85`; its `Resolved in:` names the CLI half (`d849557`) and the API half by subject; plan 03-07 names the sha.
- Filed: none.
- Not claimed: the second clause of THRD-02, a left-hand pair proven by the same checks as a right-hand pair, is the Phase 5 pair proof (PAIR-03), as the plan's assumption said; this plan proves a left-hand rod passes the same THRD-04 gate and is left-handed by an independent probe.

## Threat Flags

None. No new endpoint or file access; T-3-09 and T-3-10 are mitigated as planned, and the CLI and API share no new parsing path beyond the one dependency and the two actions.

## Next Phase Readiness

Ready for 03-05 (the page's checkbox and the shareable-hash handling for `left_hand`). The `left_hand` field, its schema type `boolean` and the duplicate-key refusal are in place for it to build on.

## Self-Check: PASSED

Created/modified files exist; commits `d849557` and `eaaac85` are ancestors of HEAD; the active copy of the debt item is gone.

---
*Phase: 03-real-helical-thread*
*Completed: 2026-10-10*
