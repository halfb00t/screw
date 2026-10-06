---
phase: 01-runtime-port-and-walking-skeleton
plan: 05
subsystem: testing
tags: [pytest, parity, registry, argparse, openapi, source-assertions]

requires:
  - phase: 01-runtime-port-and-walking-skeleton
    provides: "KINDS registry and FastenerParams (01-01), derive/SKELETON_WARNING (01-02), the CLI kind parsers (01-03), app.js and /api/kinds (01-04)"
provides:
  - "tests/test_parity.py: one registry-driven proof that the API schema, the API query, the CLI flags and the web form expose exactly KINDS[kind].model_fields, in declaration order"
  - "Same info document from `screw info <kind>` and GET /api/<kind>/info, for the defaults and for each float field moved to 1.5x its default"
  - "_field_literals, a UI genericity check with positive controls, and the app.js statements 01-04 pinned"
  - "Three recorded negative controls: a hand-written CLI flag, an extra info query field and an info.length read in app.js each turn the module red"
affects: [phase-3 threads, phase-4 ISO rows, phase-5 nut and pair, any later kind registered in KINDS]

actuals:
  tokens: 2700
  tasks: 2
  commits: 2
plan_head_before: 288fa8e18194fbeb508ec463bfd4216e4e04315d
plan_head_after: ebbccf064c80bba3423f8214f4777b5a5521088d

tech-stack:
  added: []
  patterns:
    - "parity is parametrised over list(KINDS) and compared against model_fields, never a consumer's own list"
    - "a source check is trusted only after a test feeds it fixtures it must catch and one it must not (F3)"
    - "CLI flags are read from the whole --help output, not from the generated group alone"

key-files:
  created:
    - tests/test_parity.py
  modified: []

key-decisions:
  - "The model route's query names are compared sorted, not in order: BoltModelQuery inherits quality from a mixin listed after the fields, so OpenAPI lists it first, and a query string has no order a user sees. Schema properties and CLI flags, which the user does see, are compared in order."
  - "The pinned hashchange statement is the prefix window.addEventListener('hashchange', not the interface block's full `window.addEventListener('hashchange', navigate);`, because 01-04 shipped `() => navigate().catch(reportLoadError)`. app.js was not reworded."
  - "test_the_cli_flags_are_the_model reads every long flag in the help and expects [--help, *fields] for info and [--help, --output, --format, --quality, *fields] for export."

requirements-completed: [FRNT-05, FRNT-01, FRNT-02, FRNT-04]

coverage:
  - id: D1
    description: "API schema properties, API query names, CLI flags (info and export) and the UI's schema loop all equal the registered model's fields; the registry is asserted non-empty first"
    requirement: FRNT-05
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_the_registry_is_not_empty_and_holds_the_default"
        status: pass
      - kind: unit
        ref: "tests/test_parity.py#test_the_api_schema_is_the_model"
        status: pass
      - kind: unit
        ref: "tests/test_parity.py#test_the_api_query_is_the_model"
        status: pass
      - kind: unit
        ref: "tests/test_parity.py#test_the_cli_flags_are_the_model"
        status: pass
    human_judgment: false
  - id: D2
    description: "A foreign field is a 422 naming it on info and model.stl; a foreign or abbreviated CLI flag exits 2"
    requirement: FRNT-01
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_a_foreign_field_is_refused_on_every_route"
        status: pass
      - kind: unit
        ref: "tests/test_parity.py#test_a_foreign_or_abbreviated_flag_exits_2"
        status: pass
    human_judgment: false
  - id: D3
    description: "The CLI and the API print the same info document, both carrying the skeleton warning"
    requirement: FRNT-04
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_the_cli_and_the_api_print_the_same_document"
        status: pass
    human_judgment: false
  - id: D4
    description: "app.js reads no field name or row key, builds its form, hash and rows from generic statements, and assigns no HTML string; the literal check is shown to catch drift"
    requirement: FRNT-02
    verification:
      - kind: unit
        ref: "tests/test_parity.py#test_the_literal_check_has_teeth"
        status: pass
      - kind: unit
        ref: "tests/test_parity.py#test_the_ui_reads_no_field_by_name"
        status: pass
      - kind: unit
        ref: "tests/test_parity.py#test_every_row_key_is_unread_by_name_in_the_ui"
        status: pass
      - kind: unit
        ref: "tests/test_parity.py#test_the_ui_round_trips_every_field_through_generic_code"
        status: pass
      - kind: unit
        ref: "tests/test_parity.py#test_the_ui_builds_nodes_from_text_only"
        status: pass
    human_judgment: false
  - id: D5
    description: "The live browser hash round trip (field edit, copy link, reopen) is not asserted; no browser runs in the gate (L01)"
    requirement: FRNT-02
    verification: []
    human_judgment: true
    rationale: "Source assertions prove app.js is generic, not that it behaves in a browser; 01-04's end-of-phase human-check list covers the round trip."
---

# Phase 1 Plan 05: One parity test over the registry Summary

**tests/test_parity.py parametrises over KINDS and proves the API schema, API query, CLI flags and web form expose exactly the model's fields in order, that CLI and API print the same document, and that each of three planted drifts turns it red**

## Performance

- **Duration:** about 15 min (start time was not captured at launch; estimated)
- **Completed:** 2026-10-06
- **Tasks:** 2 (Task 2 produces no commit of its own; its evidence is below)
- **Files modified:** 1 (1 created)

## Accomplishments
- One module, 12 tests, 8 of them `@pytest.mark.parametrize("kind", list(KINDS))`. A kind registered later is covered with no edit here. Each comparison is against `KINDS[kind].model_fields`.
- `test_the_registry_is_not_empty_and_holds_the_default` runs first and checks `/api/kinds` returns `default == DEFAULT_KIND` and `kinds == list(KINDS)`, so an empty registry fails instead of passing vacuously.
- Foreign field: `zz_not_a_field=1` is a 422 with loc `["query", "zz_not_a_field"]` on info and model.stl. Foreign CLI flag exits 2 naming it; for every flag, the flag minus its last character exits 2 (`--d` becomes `--`, which argparse also refuses, so that one case proves less than the others).
- `test_the_cli_and_the_api_print_the_same_document` compares the defaults and each float field at 1.5x its default; both documents carry `SKELETON_WARNING`.
- `_field_literals` flags a quoted name or a property read on `info|prop|values|h|q|defaults|properties`; `test_the_literal_check_has_teeth` shows `info.length`, `defaults.pitch`, `q.get('d')` caught and `box.getSize(new Vector3()).length()` not.
- The module passes serially and under `-n 4` (12 passed each); it reads no state another test mutates.

## Task Commits

1. **Task 1: parity test over KINDS** - `984d241` (test)
2. **Task 2: plant three drifts and revert** - no code commit; found a gap in Task 1's CLI check, fixed in `ebbccf0` (test)

**Plan metadata:** committed with this SUMMARY (docs: complete plan).

## Negative controls (Task 2)

Each drift was applied alone to a clean `src/`, the module run with `-n0`, then the file restored with `git checkout -- <that file>`.

**(a) A hand-written `--zz-drift` on the info kind parser (`src/screw/cli.py`).** First run, against Task 1's original test: `12 passed`. The drift went unseen: the test read only the lines after the kind's "parameters" group, and the stray flag sits in the plain `options:` section above it. That is a real hole, fixed in `ebbccf0` (the test now reads every long flag in the help). Re-run with the fix:

```
>       assert _cli_flags(kind, "info", capsys) == ["--help", *fields]
E       AssertionError: assert ['--help', '-...', '--length'] == ['--help', '-...', '--length']
E         At index 1 diff: '--zz-drift' != '--d'
E         Left contains one more item: '--length'
tests/test_parity.py:144: AssertionError
FAILED tests/test_parity.py::test_the_cli_flags_are_the_model[bolt]
1 failed, 11 passed
```

**(b) `zz_drift: float = 0.0` as a second plain query parameter on `bolt_info` (`src/screw/app.py`).** Three tests red, including the intended one:

```
>       assert _query_names(f"/api/{kind}/info") == fields
E       AssertionError: assert ['q', 'zz_drift'] == ['d', 'pitch', 'length']
tests/test_parity.py:125: AssertionError
FAILED tests/test_parity.py::test_the_api_query_is_the_model[bolt]
FAILED tests/test_parity.py::test_a_foreign_field_is_refused_on_every_route[bolt]
FAILED tests/test_parity.py::test_the_cli_and_the_api_print_the_same_document[bolt]
3 failed, 9 passed
```

FastAPI stops expanding the query model once a plain parameter sits beside it, so the other two fail as well.

**(c) `const zzDrift = info.length;` inside `renderInfo` (`src/screw/static/app.js`).**

```
>       assert _field_literals(APP_JS, list(KINDS[kind].model_fields)) == []
E       AssertionError: assert ['length'] == []
E         Left contains one more item: 'length'
tests/test_parity.py:208: AssertionError
FAILED tests/test_parity.py::test_every_row_key_is_unread_by_name_in_the_ui[bolt]
FAILED tests/test_parity.py::test_the_ui_reads_no_field_by_name[bolt]
2 failed, 10 passed
```

After each restore `git diff --quiet -- src` was clean and `git status --short` showed only the orchestrator's three planning files (`.planning/config.json`, `.planning/milestone.lock`, `.planning/state.json`). The final tree passes the module with `-n0` and `-n 4`.

## Files Created/Modified
- `tests/test_parity.py` - the parity module; imports `STATIC`, `app`, `build_backend` from `screw.app`, `cli`, `derive`, `SKELETON_WARNING`, `KINDS`, `DEFAULT_KIND`, and `solid.export` for the inline backend

## Decisions Made
- Model-route query names are compared sorted (see key-decisions): OpenAPI lists the inherited `quality` first. Schema and CLI order, which users see, stay strict.
- `hashchange` is pinned by prefix, not by the interface block's full line, because 01-04's shipped handler differs from what its plan quoted. `app.js` was left as is.
- The CLI check takes the whole help, after Task 2 showed the group-only read missed a stray flag.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] CLI flag check blind to a flag outside the generated group**
- **Found during:** Task 2, drift (a)
- **Issue:** `test_the_cli_flags_are_the_model` read only the lines after the "parameters" group header, so a hand-written flag on the kind parser passed. The plan expected it red.
- **Fix:** `_cli_flags` reads every long flag from the whole help; the test expects `["--help", *fields]` for info and `["--help", "--output", "--format", "--quality", *fields]` for export.
- **Files modified:** tests/test_parity.py
- **Verification:** drift (a) re-run is red; module passes `-n0`, `-n 4`; `make verify` passes (pre-commit ran it)
- **Commit:** ebbccf0

**2. [Rule 1 - Plan inconsistency] Pinned `hashchange` statement does not match app.js**
- **Found during:** Task 1
- **Issue:** the plan's interface block pins `window.addEventListener('hashchange', navigate);`; 01-04 shipped `window.addEventListener('hashchange', () => navigate().catch(reportLoadError));`. UI-SPEC rule 29 does not list it, and the prompt forbids rewording app.js.
- **Fix:** the test pins the prefix `window.addEventListener('hashchange'`.
- **Files modified:** tests/test_parity.py
- **Commit:** 984d241

**3. [Rule 1 - Test expectation] Model-route query names are not in field order**
- **Found during:** Task 1 first run
- **Issue:** `BoltModelQuery(BoltParams, _Quality)` lists `quality` first in OpenAPI, so an in-order comparison failed.
- **Fix:** sorted comparison for that route, with a comment saying why.
- **Commit:** 984d241

**Total deviations:** 3 auto-fixed (all in the test). **Impact:** none on production code; deviation 1 made the test stricter than the plan's own wording.

## Issues Encountered

None open. The `--d` prefix case degenerates to `--`; noted above.

## User Setup Required

None.

## Known Stubs

None.

## Threat Flags

None. No production surface changed; `src/` is byte-identical to its state before this plan.

## Verification

- `.venv/bin/python -m pytest tests/test_parity.py -q -n0 -p no:cacheprovider`: `12 passed in 2.04s`
- `.venv/bin/python -m pytest tests/test_parity.py -q -n 4 -p no:cacheprovider`: `12 passed in 2.82s`
- `make verify` before the Task 1 commit: ruff `All checks passed!`, mypy `Success: no issues found in 21 source files`, `Contracts: 6 kept, 0 broken.`, pytest `175 passed in 24.48s`. The pre-commit hook ran `make verify` again at both commits and passed.
- `grep -c '@pytest.mark.parametrize("kind", list(KINDS))' tests/test_parity.py` prints 8 (needs at least 6).
- `git diff --quiet -- src tests` after Task 2 is clean apart from the committed test fix.

## Next Phase Readiness

Ready for 01-06. Any kind added to `KINDS` is covered at once; a kind whose `derive()` rows or CLI flags drift from its model fails `make verify`. The browser round trip stays a UAT item.

## Self-Check: PASSED

- FOUND: tests/test_parity.py
- FOUND: 984d241, ebbccf0 (both ancestors of HEAD)
