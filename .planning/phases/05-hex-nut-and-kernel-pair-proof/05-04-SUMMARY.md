---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 04
subsystem: nut-kind
tags: [nut, pydantic, required-field, cadquery, fastapi, argparse, registry]
requires:
  - phase: 05-02
    provides: "05-OWNER-READS.md: ISO 4032:2023 M6 s 10.0 and m 5.2 (secondary source) with permanent: accepted"
provides:
  - "NutParams (s, m, required clearance) and the nut registered in KINDS beside the bolt"
  - "nut_closed_volume, the nut's closed form, in calc/thread.py"
  - "solid/nut.py: void(p) and assemble(p, void), both gated inside the cached build"
  - "GET /api/nut/info and /api/nut/model.{stl,step}; screw info|export|presets nut; [required] CLI help"
  - "per-kind dispatch in catalogue_document, expand, derive, download_refusal, _EXPLICIT_CONFLICTS and the BuildError text"
  - "tests/conftest.py REQUIRED_VALUES and the part_of fixture; tests/test_nut.py"
affects: [05-05, 05-06, 05-07, 05-10, 05-13, 05-14]
actuals:
  tokens: 10100
  tasks: 2
  commits: 2
plan_head_before: 7b50a42c4d55b491892a10254bbf39b966782d07
plan_head_after: 4d26392132697d1fc9e6cc783db85151342f6e79
tech-stack:
  added: []
  patterns:
    - "_req(): a required field helper beside _f, built the way _f builds its extras"
    - "registry-wide tests build part_of(kind), and a positive parity rule pins required fields to REQUIRED_VALUES"
    - "a planted-wrong closed form is monkeypatched through the dotted name screw.solid reads it by"
key-files:
  created:
    - src/screw/solid/nut.py
    - tests/test_nut.py
  modified:
    - src/screw/params.py
    - src/screw/calc/__init__.py
    - src/screw/calc/thread.py
    - src/screw/calc/presets.py
    - src/screw/solid/__init__.py
    - src/screw/app.py
    - src/screw/cli.py
    - tests/conftest.py
    - tests/test_parity.py
    - tests/test_api.py
    - tests/test_calc.py
    - tests/test_presets.py
    - tests/test_cli.py
    - tests/test_solid.py
    - tests/test_params.py
    - docker/smoke.py
key-decisions:
  - "NutParams.s = 10.0 and .m = 5.2 are the values 05-OWNER-READS.md records under permanent: accepted; the comment on them states the source is secondary (a GlobalFastener.com print of ISO 4032:2023, read by Claude, approved by the owner)"
  - "clearance is required (Field(...)), has no gt and no default: the schema carries required: [clearance] and no default key"
  - "the nut kind's rows and downloads are generic, so the nut has its own groups Thread, Nut and Pair and `custom` with the no-row warning until 05-07"
  - "BuildError names the model's own fields from type(p).model_fields, so a nut failure no longer names a bolt's length and k"
requirements-completed: [TYPE-03, PAIR-01]
coverage:
  - id: D1
    description: "A nut with a typed clearance builds through the API info and download routes, the pool, the CLI and the kinds list"
    requirement: TYPE-03
    verification:
      - kind: unit
        ref: "tests/test_nut.py#test_a_real_worker_builds_a_nut_for_the_stl_and_the_step"
        status: pass
      - kind: unit
        ref: "tests/test_api.py#test_a_nut_with_a_clearance_serves_its_info_and_both_downloads"
        status: pass
      - kind: unit
        ref: "tests/test_nut.py#test_the_cli_prints_the_nut_document_and_writes_a_binary_stl"
        status: pass
    human_judgment: false
  - id: D2
    description: "A missing clearance is refused naming the field on every front end, with no default anywhere"
    requirement: PAIR-01
    verification:
      - kind: unit
        ref: "tests/test_nut.py#test_a_nut_info_without_a_clearance_is_a_422_missing_naming_it"
        status: pass
      - kind: unit
        ref: "tests/test_cli.py#test_a_nut_without_a_clearance_exits_2_naming_it"
        status: pass
      - kind: unit
        ref: "tests/test_parity.py#test_the_required_fields_are_exactly_the_ones_the_samples_name"
        status: pass
    human_judgment: false
  - id: D3
    description: "The nut is the hex prism less the L11 void with both gates, each shown to bite on a planted wrong closed form"
    requirement: TYPE-03
    verification:
      - kind: unit
        ref: "tests/test_nut.py#test_a_void_wrong_by_more_than_the_gate_is_refused_naming_the_void"
        status: pass
      - kind: unit
        ref: "tests/test_nut.py#test_a_nut_wrong_by_more_than_the_gate_is_refused_naming_the_solid"
        status: pass
    human_judgment: false
  - id: D4
    description: "The M6 s and m defaults are the owner-accepted permanent values"
    requirement: TYPE-03
    verification:
      - kind: unit
        ref: "tests/test_params.py#test_the_nut_defaults_are_the_iso_4032_m6_values_the_owner_accepted"
        status: pass
    human_judgment: false
  - id: D5
    description: "The page lists nut in its kind selector from /api/kinds; selecting it opens a form with a clearance field and no default"
    verification: []
    human_judgment: true
    rationale: "No browser is in the gate (L01). The page is generic and the kinds list is tested, but the empty-clearance flow (stale mesh, 'undefined' written to a number input, RESEARCH P9) is plan 05-10's and has not been looked at in a browser."
duration: 12min
completed: 2026-10-14
status: complete
---

# Phase 5 Plan 04: Nut tracer Summary

**The nut is a registered kind: a hex prism less the L11 thread void behind two volume gates, with a required radial `clearance` that every front end refuses by name when it is missing.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-10-14T15:55:46Z
- **Completed:** 2026-10-14T16:08:03Z (code), SUMMARY committed after
- **Tasks:** 2 of 2
- **Files modified:** 18 (2 created, 16 modified), 751 insertions and 65 deletions

## Accomplishments

- `NutParams` with `s` 10.0 and `m` 5.2 (the owner-accepted ISO 4032:2023 M6 values) and a required `clearance` through a new `_req` helper; `KINDS` is `{bolt, nut}`, `DEFAULT_KIND` stays `bolt`.
- The nut builds on all three front ends: `/api/nut/info`, `/api/nut/model.{stl,step}` (also through a real pool worker), and `screw info|export|presets nut`. `screw info nut` with no clearance prints `error: clearance: Field required` and exits 2; `--help` prints `[required]`.
- `solid/nut.py` is the prism `polygon(6, s, circumscribed=True)` extruded `m`, less `helical.thread(d, pitch, m + 2 pitch, clearance=c)` shifted down one pitch. The void is gated against `closed_volume(...)` first and the nut against `nut_closed_volume` second, inside the cached function at `T_GATE`.
- Every bolt-only assumption was promoted to a per-kind dispatch: preset catalogue and expand, `derive`, `download_refusal`, explicit conflicts, and the `BuildError` text, which now names `type(p).model_fields`.
- Measured on the default M6 nut at c 0.1, both hands: one valid solid, box 10.0000 x 11.5470 x 5.2000, and the precise volume inside `T_GATE` of the closed form (both gated at build, and re-asserted in `tests/test_nut.py`).
- `make verify`: ruff, mypy --strict (65 files), import contracts, unfinished-work scan and pytest all pass. Result line: `2757 passed in 81.85s`, `Required test coverage of 96.0% reached. Total coverage: 97.36%`. `solid/nut.py` is 100 %.

## Task Commits

1. **Task 1: End-to-end nut with a typed clearance (tracer)** - `6ed753f` (feat)
2. **Task 2: Pin the nut's solid, gates and refusals of a missing clearance** - `4d26392` (test)

**Plan metadata:** the commit carrying this file (docs).

Both commits ran the pre-commit `make verify` and passed. The commit trailer names the writer, `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`, not the orchestrator's suggested Opus 5.5, because Sonnet 5.5 wrote this diff.

## Tracer feedback gate

Tracer verified end-to-end before the expansion task (Task 2): `screw info nut --clearance 0.1` printed `kind: nut`, `screw export nut --clearance 0.1 -o x.stl` wrote a 2962 KiB binary STL, `screw info nut` exited 2, and `make verify` was green. The plan's `<verify>` carries only `<automated>` steps and `HUMAN_VERIFY_MODE` is the default `end-of-phase`, so no human checkpoint was synthesised.

## TDD note (Task 2, `tdd="true"`)

The plan states that Task 1 implements every behaviour, so Task 2's tests pass on first run and the planted-error tests are the teeth. There is no RED commit. That is the plan's own instruction and not a skipped gate; the `TDD_MODE` runtime gate was not enabled for this phase.

The plan's second acceptance criterion (planted-error tests fail without their monkeypatch) was checked once by hand: with `_scale_void_form`, `_scale_nut_form` and the `nut.assemble` plant turned into no-ops in a throwaway copy, 4 tests failed (`..._refused_naming_the_void`, `..._refused_naming_the_solid`, `..._is_not_cached`, `..._names_the_nuts_own_fields`) and 28 passed. The copy was deleted.

## Files Created/Modified

- `src/screw/params.py` - `_req`, `NutParams`, `KINDS` with the nut
- `src/screw/calc/thread.py` - `nut_closed_volume`
- `src/screw/calc/__init__.py` - `THREAD`, `NUT`, `PAIR`, `NUT_NO_ROW_WARNING`, `_nut`, nut branches in `derive` and `download_refusal`, `_EXPLICIT_CONFLICTS["nut"] = None`
- `src/screw/calc/presets.py` - nut dispatch in `catalogue_document` (axes Standard, Size; no rows) and `expand` (None for every id)
- `src/screw/solid/nut.py` (new) - `void`, `assemble`
- `src/screw/solid/__init__.py` - `_build` dispatch, `_build_nut`, `_build_bolt`, kind-neutral `BuildError` text
- `src/screw/app.py` - `NutModelQuery`, `nut_info`, `nut_model`, route list in the docstring
- `src/screw/cli.py` - `[required]` in the flag help
- `tests/conftest.py` - `REQUIRED_VALUES`, `part_of`
- `tests/test_nut.py` (new, 22 tests) - solid, gates, kernel failure, refusals, pool, CLI
- `tests/test_parity.py`, `test_api.py`, `test_calc.py`, `test_presets.py`, `test_cli.py`, `test_solid.py`, `test_params.py`, `docker/smoke.py` - every registry-wide break fixed in the same commit, plus nut tests in the files they belong to

## Decisions Made

- `NutParams` s and m default to 10.0 and 5.2 and are pinned by a literal test. The comment on them cites 05-OWNER-READS.md, the permanence line, and that the source is secondary (a print of a web page transcribing ISO 4032:2023, read by Claude and approved by the owner as a deviation from D-14). Nothing here has been checked against the standard itself.
- `_nut` also appends the download-refusal warnings through `_downloads`, as `_bolt` does, so the document and the rule cannot disagree once plan 05-05 adds the nut's fine-STL rule. Today it adds none.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `_req` returned `Any` under `mypy --strict`**
- **Found during:** Task 1
- **Issue:** `Field(...)` returns `Any`, and `_req` is declared `-> float`; `no-any-return` failed.
- **Fix:** assign to a `float`-typed local and return that. No `type: ignore` (the Makefile refuses one in `src/screw/`).
- **Files modified:** `src/screw/params.py`
- **Commit:** `6ed753f`

**2. [Rule 3 - Blocking] Registry-wide tests that `monkeypatch.setattr(solid, "closed_volume", ...)` fail `mypy --strict`**
- **Found during:** Task 2
- **Issue:** `screw.solid` does not re-export `closed_volume` or `nut_closed_volume`, so attribute access on the module is an `attr-defined` error.
- **Fix:** the planted-form helpers patch by dotted string (`"screw.solid.closed_volume"`) and compute the right form from `screw.calc.thread`.
- **Files modified:** `tests/test_nut.py`
- **Commit:** `4d26392`

### Plan wording followed differently

**3. [Note] Commit scope is `(05-04)`, not `(nut)`**
- The plan's literal subjects were `feat(nut): ...` and `test(nut): ...`. The executor protocol and the repo's own history (`docs(05-03): ...`) use `{type}({phase}-{plan})`, so the commits are `feat(05-04): ...` and `test(05-04): ...`. The type and the description are as planned.

**4. [Note] The test the plan says pins the old BuildError text pins no real text**
- `tests/test_api.py` ~884 builds its own `BuildError("... check d, pitch, length, s and k.")`, which was already stale (it omits `thread_length`) and is never compared with the builder's output. It is updated to the new bolt wording, and `tests/test_nut.py` now pins both real texts: the nut's `check d, pitch, left_hand, s, m and clearance.` and the bolt's `check d, pitch, left_hand, length, s, k and thread_length.`.

**5. [Rule 2 - Missing critical] Tests the plan did not list**
- New behaviour ships with its tests in the same change, so the Task 1 commit also carries: `tests/test_params.py` (nut default literals, clearance required, nominal and interference clearances accepted), `tests/test_calc.py` (the nut's rows, groups, volume and warnings; the closed form against a midpoint sum over `section_radius`), `tests/test_api.py` (nut routes 200, schema required and no default), `tests/test_cli.py` (nut without clearance exits 2 for `info` and `export`; `[required]` in the help). `test_parity.py` also gained `test_a_planted_required_field_fails_the_required_field_rule`, the teeth of the positive rule the plan asked for.

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking), 3 notes. **Impact:** none on scope or behaviour.

## Issues Encountered

None that blocked. The pre-commit hook's `GIT_*` export (the wave-3 warning) did not matter: nothing here runs `git` in a temp directory.

## Known Stubs

None. The nut's `rows` list in `/api/presets?kind=nut` is empty and `expand("nut", id)` is None for every id by design: no ISO 4032 row has shipped, and plan 05-07 fills it. `tests/test_presets.py` and `tests/test_parity.py` pin the empty document and name 05-07 as the plan that replaces the assertion with the non-empty rule for every kind. Nothing was added to `.planning/WINDOWS.md` (this is a planned gap with a named plan, not a stub that reaches the UI).

## Threat Flags

None beyond the plan's register. T-05-09 is mitigated as planned (required, `allow_inf_nan=False`, `le=INTERIM_MAX_MM`, tested for empty, inf, nan, text and 100001). T-05-10's second half stays with 05-05: the nut has no turn cap on `m + 2 pitch` and no fine-STL rule yet, so a long nut is bounded only by the interim ceilings and the build timeout until 05-05 lands.

## Things the next plans need to know

- **Interim UI state.** `/api/kinds` now lists `nut`, so the page's selector offers it. Selecting it opens a form whose clearance has no default and 422s `missing` until typed; RESEARCH P9 (the stale bolt mesh left on screen, the `undefined` string written to a number input, `counterpart`) is plan 05-10's and is untouched here. `tests/test_parity.py` reads `app.js` as text only, so it cannot see this.
- **Plan 05-05** adds the nut's refusals: `_root_radius` still judges the nut with clearance 0 (inherited), there is no `s <= d + 2c` rule and no turn cap on `m + 2 pitch` yet. `download_refusal` returns None for the nut here, and the R12 table in 05-OWNER-READS.md must go to the owner before it edits that function.
- **`bolt._solid`** is a private helper of `solid/bolt.py`, now also called from `solid/nut.py` (`bolt._solid(...)`). It works and is typed, but a leading-underscore name crossing a module boundary is a small smell; renaming it was out of this plan's scope. Not filed as a tech-debt item (nice-tier at most); raised here for the owner.
- **Debt filed:** none.

## Self-Check: PASSED

- `src/screw/solid/nut.py` and `tests/test_nut.py` exist; `6ed753f` and `4d26392` are ancestors of HEAD.
- `git rev-list --count 7b50a42..4d26392` is 2, matching `actuals.commits`.
- `make verify` run after the last commit: 2757 passed, coverage 97.36 against the 96.00 floor.
- Acceptance criteria re-run: `NutParams.model_fields['clearance'].is_required()` prints `True`; `screw info nut --help` contains `[required]`; `docker/smoke.py` line 71 requests `kind=washer`; `nut.py` contains `circumscribed=True` and `m + 2 * p.pitch` and imports `helical`; `tests/test_nut.py` has 22 test functions and names `PydanticUndefined`, `is_required()`, `float_parsing` and `finite_number`.
