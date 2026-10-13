---
phase: 01-runtime-port-and-walking-skeleton
verified: 2026-10-13T08:00:00Z
status: passed
score: 17/17 must-haves verified
human_verified: 2026-10-06T08:28:30Z
human_verified_items: 2
covered_files:
  - ".github/workflows/ci.yml"
  - ".github/workflows/required-jobs.txt"
  - ".planning/phases/01-runtime-port-and-walking-skeleton/01-01-PLAN.md"
  - ".planning/phases/01-runtime-port-and-walking-skeleton/01-01-SUMMARY.md"
  - ".planning/phases/01-runtime-port-and-walking-skeleton/01-02-PLAN.md"
  - ".planning/phases/01-runtime-port-and-walking-skeleton/01-02-SUMMARY.md"
  - ".planning/phases/01-runtime-port-and-walking-skeleton/01-03-PLAN.md"
  - ".planning/phases/01-runtime-port-and-walking-skeleton/01-03-SUMMARY.md"
  - ".planning/phases/01-runtime-port-and-walking-skeleton/01-04-PLAN.md"
  - ".planning/phases/01-runtime-port-and-walking-skeleton/01-04-SUMMARY.md"
  - ".planning/phases/01-runtime-port-and-walking-skeleton/01-05-PLAN.md"
  - ".planning/phases/01-runtime-port-and-walking-skeleton/01-05-SUMMARY.md"
  - ".planning/phases/01-runtime-port-and-walking-skeleton/01-06-PLAN.md"
  - ".planning/phases/01-runtime-port-and-walking-skeleton/01-06-SUMMARY.md"
  - ".planning/phases/01-runtime-port-and-walking-skeleton/01-07-PLAN.md"
  - ".planning/phases/01-runtime-port-and-walking-skeleton/01-07-SUMMARY.md"
  - ".planning/phases/01-runtime-port-and-walking-skeleton/01-08-PLAN.md"
  - ".planning/phases/01-runtime-port-and-walking-skeleton/01-08-SUMMARY.md"
  - ".planning/phases/01-runtime-port-and-walking-skeleton/01-09-PLAN.md"
  - ".planning/phases/01-runtime-port-and-walking-skeleton/01-09-SUMMARY.md"
  - ".planning/phases/01-runtime-port-and-walking-skeleton/01-10-PLAN.md"
  - ".planning/phases/01-runtime-port-and-walking-skeleton/01-10-SUMMARY.md"
  - "Dockerfile"
  - "Makefile"
  - "bench/corpus.py"
  - "compose.yaml"
  - "docker/refresh-requirements.sh"
  - "docker/smoke.py"
  - "pyproject.toml"
  - "requirements.txt"
  - "scripts/pr_land.py"
  - "scripts/skip_tokens.py"
  - "src/screw/__init__.py"
  - "src/screw/__main__.py"
  - "src/screw/app.py"
  - "src/screw/build_errors.py"
  - "src/screw/calc/__init__.py"
  - "src/screw/cli.py"
  - "src/screw/params.py"
  - "src/screw/pool.py"
  - "src/screw/records.py"
  - "src/screw/solid/__init__.py"
  - "src/screw/solid/bolt.py"
  - "src/screw/static/app.js"
  - "src/screw/static/index.html"
  - "src/screw/static/style.css"
  - "tests/test_api.py"
  - "tests/test_cli.py"
  - "tests/test_parity.py"
  - "tests/test_pool.py"
covered_digest: "v3:sha256:8e7f95f3a39e8a0b840850b2f5f9720435c3b6ff4e527a831f60af83338daab1"
behavior_unverified: 0
overrides_applied: 1
overrides:
  - must_have: "Plans 01-01..01-09 merged to main as one squash commit with gh pr merge N --squash --delete-branch, before any wall existed (D-12; main was pushed beforehand, so the PR diff was phase work only, D-13)"
    reason: "PR #1 landed as merge commit 4951d47 (51 commits) instead of one squash commit. Process shape only: the phase code is on main either way and the wall applies from PR #2 onward."
    accepted_by: "owner (recorded in .planning/STATE.md line 99)"
    accepted_at: "2026-10-06"
re_verification:
  previous_status: passed
  previous_score: 17/17
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 1: Runtime Port and Walking Skeleton Verification Report

**Phase Goal:** A user can generate a walking-skeleton bolt (`d`, `pitch`, `length`, plain unthreaded solid; an internal milestone, never released) from the web UI, the HTTP API and the CLI, all served by spur's ported runtime from one registered model, with front-end parity proven by one test over the registry.
**Verified:** 2026-10-13T08:00:00Z against `main` at HEAD `752d20c`
**Status:** passed
**Re-verification:** Yes, regeneration run (#5118). The 2026-10-06 report (passed, 17/17) went `stale` because Phases 2, 3 and 4 changed its covered source files. This run re-reads every truth against the code on `main` today. There was no `gaps:` section to close; the previous report's two `behavior_unverified_items` were closed by the owner's browser UAT (`01-UAT.md`, both `pass`) and stay closed.

## How the phase goal reads on today's code

Two clauses of the goal are superseded by decisions made after Phase 1, and are not reported as gaps:

- "plain unthreaded solid": retired by L11 and L12 (Phase 3: a real ISO 68-1 helical thread behind a postcondition gate). L13 (Phase 4) then made the default an ISO 4017 hex head screw (M6 x 20, `s` 10, `k` 4). "Walking skeleton" no longer describes the part, only the runtime that serves it.
- The walking-skeleton truths that named the cylinder (volume of a cylinder, the `SKELETON_WARNING`, "no thread or turn row") are re-read below, per truth, against the threaded hex part. Each says how it was re-read.

What Phase 1 delivered is the runtime: one registered parameter model serving UI, API and CLI, a parity test over the registry, a schema-generated form, a hash that omits defaults and the default kind, a `422` naming the field on a conflict, cap-and-warn, the worker pool, INTERIM-labelled carried bounds, CI, Docker and the L02 standing rules. All of that is present and works on `main`.

## Goal Achievement

### Method and evidence run by this verifier

SUMMARY claims were not trusted. Evidence gathered in this session:

- `make verify` run in full today at HEAD `752d20c`: ruff `All checks passed!`; mypy `--strict` `Success: no issues found in 59 source files`; import-linter `Contracts: 9 kept, 0 broken`; unfinished-work scan green; pytest `2637 passed in 68.54s`, coverage `97.33%` (`Required test coverage of 96.0% reached`); exit 0.
- Named tests run alone: the D-16 same-slot-timeout test (`tests/test_pool.py::test_two_same_slot_timeouts_in_one_incident_end_as_build_timeout_not_attribute_error`) passed; seven registry-parity tests and three frozen-default tests passed.
- The real app through its lifespan and spawned worker pool (`TestClient(app)` in a script file): `/api/health` 200 with `pool.workers 2`; `/api/kinds` `{default: bolt, kinds: [bolt]}`; `/api/bolt/model.stl?quality=preview` 200, 1,579,284 bytes, `filename="bolt_d6_pitch1_left_hand0_length20_s10_k4_thread_length20.stl"`; `/api/bolt/model.step` 200 beginning `ISO-10303-21`; info rows d 6.0, pitch 1.0, length 20.0, turns 20, volume 805.5542424753626.
- API refusals: `?zz=1` 422 loc `["query","zz"]`; `?d=5&d=6` 422 type `duplicate`; `?d=100001` 422 loc `["query","d"]`; `?length=10&thread_length=30` 422 with `ctx.fields = [thread_length, length]`; `/api/schema?kind=nut` 404.
- CLI by hand: `screw info bolt --m 5` -> `unrecognized arguments: --m 5`; `--d 5 --d 6` -> exit 2, `--d was given more than once`; `--d 0` -> `error: d: Input should be greater than 0` (before the kernel loads); `--pitch 1e100` -> `error: d and pitch: the root radius ... must be above 0` naming both fields.
- `gh`: ruleset `24563199` read live, `enforcement: active`, `bypass_actors: []`, rules `deletion`, `non_fast_forward`, `pull_request`, `required_status_checks` with contexts `test (3.12)`, `vendor-bundle`, `image`, strict true. CI run `38278036579` on main `e8df305` (Phase 4 merge): jobs `test (3.12)`, `vendor-bundle`, `image` all `success`.
- `git diff --stat e8df305 HEAD -- src tests Dockerfile compose.yaml Makefile pyproject.toml .github scripts bench docker` shows only `bench/RESULTS.md` (+59). So the CI-verified image and gate are the same source as HEAD.
- `git status` at the end: only the pre-existing untracked `.planning/ui-reviews/` and `web/.DS_Store`. No tracked file was modified.
- Cited, not redone: `03-VERIFICATION.md` (regenerated today, passed 14/14) covers the thread, the caps and the refusals; the owner's 2026-10-13 Phase 3 UAT re-ran browser checks on this same page.

### Observable Truths

ROADMAP success criteria SC1 to SC4 are the contract; plan-level truths are added where they carry distinct claims. Numbering is kept from the previous report.

| #  | Truth | Status | Evidence |
| -- | ----- | ------ | -------- |
| 1  | SC1 (API and CLI half): the same bolt comes from the API (info, STL, STEP, schema, health) and from `screw serve \| info \| export` | ✓ VERIFIED | `src/screw/app.py:361-455`: `/api/health`, `/api/kinds`, `/api/schema?kind=`, `/api/presets?kind=`, `/api/bolt/info`, `/api/bolt/model.{fmt}`. `src/screw/cli.py:175-231`: `serve`, `info`, `export` (plus `presets`, added in Phase 4). Live run above: STL 200 / 1.58 MB, STEP 200 `ISO-10303-21`. `tests/test_parity.py::test_the_cli_and_the_api_print_the_same_document` passed in the gate. Read as before: schema is `?kind=` and health is global by D-08 / L09. |
| 2  | SC1 (web UI half): form generated from `/api/schema`, live 3D preview, info panel, shareable URL carrying the full parameter set with defaults omitted | ✓ VERIFIED (owner UAT) | Formerly PRESENT_BEHAVIOR_UNVERIFIED. Closed by `01-UAT.md` test 1 (`pass`, owner's browser, 2026-10-06) and re-confirmed on the same page by Phase 3's 2026-10-13 UAT (left-hand checkbox, hash round trip, link refusals, per-mesh warnings). Code on `main` agrees: `app.js:435-442` writes `kind=` only when `currentKind !== kinds.default` and writes only fields that differ from the schema defaults (`partQuery`, `app.js:308-319`, numeric compare so `6.0` and `6` agree); the form is built from `schema.properties` (`buildForm`, fetches `api/schema?kind=`). Re-read: the preview is now the threaded hex part, not a cylinder. |
| 3  | SC2 (refusal): a field the kind does not define is a 422 naming it on the API and an error naming it on the CLI, never silently ignored | ✓ VERIFIED | `params.py:60` `ConfigDict(frozen=True, extra="forbid")`. Live: `?zz=1` 422 loc `["query","zz"]`; CLI `--m 5` exit 2 naming the argument; `allow_abbrev=False` on every parser (`cli.py:177-215`). `test_parity.py::test_a_foreign_field_is_refused_on_every_route` and `test_a_foreign_or_abbreviated_flag_exits_2` passed. The web page now also refuses a foreign hash key whole (`app.js:285-289` `refuseLink`), which closes the former OI-2 warning. |
| 4  | SC2 (parity): one parity test over the registry proves the UI, API and CLI expose the same fields, and stays in `make verify` | ✓ VERIFIED | `tests/test_parity.py` (738 lines, 27 tests, 14 parametrised over `list(KINDS)`). Compares against `KINDS[kind].model_fields`, never a hand-kept list; `test_the_registry_is_not_empty_and_holds_the_default` guards vacuity; `test_the_literal_check_has_teeth` and `test_a_stray_flag_makes_the_flag_comparison_fail` are negative controls. It ran inside today's `make verify`; seven of its tests were also run alone and passed. It grew with each phase (presets, downloads, left-hand `--no-` flag, repeated parameter), so the guard now covers fields that did not exist in Phase 1. |
| 5  | SC3 (runtime): builds execute in worker processes off the event loop; an overloaded server answers 503 + Retry-After from the web layer only | ✓ VERIFIED | `pool.py` `BuildPool`: one spawned single-worker `ProcessPoolExecutor` per slot, hash affinity, kernel imported only inside the worker through `importlib.import_module("screw.solid")` (`pool.py:51`, `:63`). Admission control is `BUILD_QUEUE` / `_build_slot` in `app.py:302`, 503 with `Retry-After: 5`; the busy, timeout and pool_broken paths are 503s with a `type` (`app.py:319`, `:514-545`). Contract "The serving process never imports the CAD kernel" KEPT. Live run above served a real build through the pool. |
| 6  | SC3 (wall): `scripts/pr_land.py`, `skip_tokens.py`, the commit-msg hook and the `main` ruleset are in place | ✓ VERIFIED | Scripts present; `tests/test_pr_land.py` (982 lines) and `tests/test_skip_tokens.py` in the gate. `.git/hooks/commit-msg` and `.git/hooks/pre-commit` exist, executable. Ruleset read live (see Method). Squash settings unchanged (PR #8 to #12 all landed through the wall). |
| 7  | SC3 (`make check`): in-image smoke test and vendored-bundle byte check pass | ✓ VERIFIED | `ci.yml` unchanged since Phase 1 (`git log -- .github/workflows/ci.yml` lists only 01-04/01-06/01-07 commits). Run `38278036579` on `e8df305`: `image` (builds the image, which runs `docker/smoke.py`, and curls health, preview STL and STEP), `vendor-bundle` and `test (3.12)` all `success`. `required-jobs.txt` equals the ruleset contexts. This verifier did not rerun Docker locally; CI on the same source is the evidence. |
| 8  | SC3 (coverage): the coverage floor is enforced | ✓ VERIFIED | `pyproject.toml:140` `fail_under = 96`, measured and raised since Phase 1's 94. Today: `Required test coverage of 96.0% reached. Total coverage: 97.33%`. |
| 9  | SC3 (bench): the `bench/` harness runs against the parts | ✓ VERIFIED | `bench/{build_time,export_cost,latency,memory,corpus}.py`, `README.md`, `RESULTS.md` present; `python -m bench.build_time --help` runs; `tests/test_bench.py` in the gate. `RESULTS.md` labels recorded runs as not a bound (L07). Re-read: the corpus is now threaded hex parts, not cylinders. |
| 10 | SC3 (no gear code, no spur figure as a final bound) | ✓ VERIFIED | `params.py`, `calc/`, `solid/` are screw designs over `FastenerParams`/`BoltParams`. `git grep` for gear identifiers in `src/` finds only `app.py:90`, `app.py:154`, `pool.py:81`, comments that cite spur's measured corpus as the source of an INTERIM figure. `INTERIM` appears on `Dockerfile` 2, `compose.yaml` 3, `app.py` 7, `calc/` 5, `cli.py` 1, `params.py` 8, `solid/__init__.py` 3, `app.js` 1; each carried figure names its spur source and "Phase 7 re-sweeps (OPER-02)". `params.py:15-31` also records the new thread-cost measurement against the carried bound. |
| 11 | SC4: `make verify` is green with import-linter enforcing the inherited contracts plus "only `solid` imports `cadquery`/`OCP`" and "`app` never imports the kernel by any path" | ✓ VERIFIED | Today `Contracts: 9 kept, 0 broken`: app vs tests; thread maths vs kernel; CLI vs web layer; thread maths vs logger; serving process vs kernel ("The serving process never imports the CAD kernel"); only `solid` imports the kernel (5 ignored imports); the spike's oracle; **"The parameters never consult a table"** and **"Tables are a leaf"**. The two contracts the previous report deferred to Phase 4 now exist and are KEPT. INFR-02 is met in the narrower form L13 fixed: the sources of "The parameters never consult a table" are `screw.params` and `screw.calc.thread` (`pyproject.toml`), while `screw.calc.presets` imports `screw.tables.presets` by design; the requirement's text "`params` and `calc` never import `tables`" overstates the shipped boundary. |
| 12 | D-16 (behavior-dependent): a second same-slot timeout after the first already replaced the slot ends as `BuildTimeout`, never `AttributeError` | ✓ VERIFIED | Guard `self._executors[hash(p) % self.workers] is not executor` is the first statement of `_run_with_timeout`'s `except TimeoutError:` (`pool.py:173`, guard at `:189`), before `executor._processes` is touched. The invariant is exercised: the named regression test was run alone today and passed. |
| 13 | Validation boundary and frozen defaults: numeric fields refuse 0, negative, inf, nan; `d`, `length`, `s`, `k`, `thread_length` above `INTERIM_MAX_MM = 1e5` are refused naming the field, never clamped; defaults and `DEFAULT_KIND = "bolt"` are frozen | ✓ VERIFIED (re-read) | `params.py:34` `_f()` sets `gt`, `le`, `allow_inf_nan=False`; `DEFAULT_KIND = "bolt"` is a literal (`params.py:155`). Re-read: the frozen defaults were d 6.0, pitch 1.0, length 20.0; they are now d 6.0, pitch 1.0, length 20.0, `s` 10.0, `k` 4.0, `thread_length` 20.0, `left_hand` False, asserted against the ISO 4017 M6 x 20 row by `test_params.py::test_the_frozen_defaults_are_the_iso_4017_m6_x_20_row`. The three Phase 1 values did not move, so an old link still means the same part (L02). `pitch` is not bounded by `le`, but an absurd pitch is refused by the root-radius rule (`--pitch 1e100` -> `error: d and pitch: ... must be above 0`), so the former WR-05 magnitude case cannot reach a built part. Live: `?d=100001` 422 loc `["query","d"]`. |
| 14 | The info document is honest: closed-form volume (never the kernel's `Volume()`), a standing warning first, a value that cannot be computed honestly is a warning and no number | ✓ VERIFIED (re-read) | Re-read for the threaded part. `git grep "\.Volume()" src` finds nothing; the volume row is closed-form (`calc/thread.py`, `bolt_closed_volume`), and the kernel-side gate uses the L11 `precise_volume` estimator on the solid side only (`solid/__init__.py:91-99`). The Phase 1 `SKELETON_WARNING` is replaced by `STANDING_WARNING = "plain-cut thread ends, no tip chamfer or under-head fillet; not a product build"` (`calc/__init__.py:38`), still first in the warnings list (live: `warnings[0]` is that text). The "no thread or turn row" clause is superseded: `turns` and `volume` rows now exist (turns 20, volume 805.554...). L02's rule holds where it matters: `--length 1e-8 --thread-length 1e-8` prints no `turns` or `volume` row and warns "a thread of 1e-08 mm is shorter than the 0.001 mm the builder can model, so this part is not built; turns and volume not reported", and `export` of that part is refused (`error: thread_length and length: ...`, exit 1). |
| 15 | UI never renders a stale response while typing or switching kind (plan 01-04 edge FRNT-02 concurrency, `verification: backstop`) | ✓ VERIFIED (owner UAT) | Formerly UNCERTAIN (insufficient_spec), routed to human. Closed by `01-UAT.md` test 2 (`pass`, rapid typing in the owner's browser). `seq`, `AbortController` and `formSeq` are still present and checked before every render (`app.js:61`, `:83`, `:223`, `:256-257`, `:431-472`). The kind-switch half still cannot be exercised: `KINDS` registers only `bolt` (`params.py:151`), so it waits for a second kind (Phase 5). That is a recorded deferral, not a new gap. |
| 16 | Plan 01-10: the ruleset read-back equals `required-jobs.txt`, squash settings are PR_TITLE/PR_BODY, and the ruleset id reached main through `make pr.land` | ✓ VERIFIED | Live `gh api` ruleset read: contexts `["test (3.12)","vendor-bundle","image"]` equal the three non-comment lines of `.github/workflows/required-jobs.txt`; `strict: true`; `bypass_actors: []`. Every PR since (#2, #3, #4 to #12) landed through the wall. |
| 17 | Plan 01-10: Phase 1 merged to main as one squash commit (D-12) | ✓ PASSED (override) | PR #1 is merge commit `4951d47`, not a squash. Override accepted by the owner on 2026-10-06 (STATE.md line 99); D-12's squash rule applies from the wall onward. Unchanged. |

**Score:** 17/17 truths verified (1 by override, 2 by owner UAT); 0 behavior-unverified.

### Deferred Items

Both items the previous report deferred have since landed or remain correctly scheduled.

| # | Item | Status now | Evidence |
|---|------|------------|----------|
| 1 | `screw pair` subcommand (FRNT-04's text lists `serve \| info \| export \| pair`) | Still deferred to Phase 5 | `cli.py` registers `serve`, `info`, `export`, `presets` and no `pair`. REQUIREMENTS PAIR-04 (Phase 5, Pending) names the `screw pair` subcommand and ROADMAP Phase 5 SC3 repeats it. Phase 1 SC1 lists `serve \| info \| export` only. |
| 2 | import-linter contracts "params and calc never import tables" and "tables is a leaf" | Landed in Phase 4, narrower than the Phase 1 wording | Contracts "The parameters never consult a table" (sources `screw.params`, `screw.calc.thread` only) and "Tables are a leaf" are KEPT in today's `make verify` (Truth 11); `screw.calc.presets` reads `screw.tables` on purpose (L13). |

### Required Artifacts

Re-read against `main`. The Phase 1 plan artifacts all still exist and are substantive; several were extended by later phases.

| Plan | Artifacts | Status | Notes |
| ---- | --------- | ------ | ----- |
| 01-01 | `params.py`, `calc/`, `solid/`, `pool.py`, `app.py`, `records.py`, `docker/smoke.py`, `pyproject.toml`, `tests/test_pool.py` | ✓ present, substantive, wired | `solid/bolt.py` is now a 60-line assembler (thread + hex head) rather than `cylinder()`; the 01-01 key link "`cylinder(` dispatch" is re-read as `bolt.thread(p)` / `bolt.assemble(p, thread)` (`solid/__init__.py:126`, `:132`). |
| 01-02 | `tests/test_api.py`, `tests/test_records.py`, L09, interim-bounds debt item | ✓ | `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` still active, as designed. |
| 01-03 | `cli.py`, `__main__.py`, entry point, `tests/test_cli.py` | ✓ | Flags generated from `model_fields` (`cli.py:52`, `_add_args`); `cli` imports no web layer (contract KEPT). |
| 01-04 | `app.js`, `index.html`, vendored `three.bundle.min.js`, `web/package.json`, static mount | ✓ | `vendor-bundle` CI job green. |
| 01-05 | `tests/test_parity.py` | ✓ | Iterates the registry through `@pytest.mark.parametrize("kind", list(KINDS))`. |
| 01-06 | `docker/refresh-requirements.sh`, `Dockerfile`, `compose.yaml`, `requirements.txt` | ✓ | Smoke runs at build (`Dockerfile:30`); `image` CI job green. |
| 01-07 | `scripts/pr_land.py`, `scripts/skip_tokens.py`, `required-jobs.txt`, L08 | ✓ | |
| 01-08 | `bench/` | ✓ | |
| 01-09 | coverage config, `RESULTS.md` coverage section, `overview.md` | ✓ | Floor now 96. |
| 01-10 | `HOW_TO_DEVELOP.md` records `rulesets/` | ✓ | |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `app.py` | `pool.py` | `BuildPool(` in lifespan | WIRED | `app.py:149`; live run built through it |
| `pool.py` | `solid` | `import_module("screw.solid")` in worker | WIRED | `pool.py:51`, `:63` |
| `app.py` | `calc` | `derive(` in `bolt_info` | WIRED | `app.py:438-441` |
| `solid/__init__.py` | `solid/bolt.py` | `bolt.thread` / `bolt.assemble` | WIRED | Re-read from the 01-01 `cylinder(` link (L12/L13) |
| `tests/test_api.py` | `app.py` | `dependency_overrides[build_backend]` | WIRED | tests pass |
| `cli.py` | `params` | `for kind, model in KINDS.items()` | WIRED | `cli.py:208` |
| `cli.py` | `solid` | lazy `from .solid import` in `cmd_export` | WIRED | `cli.py:163`, after the refusals |
| `app.js` | `app.py` | `api/kinds`, `api/schema`, `api/presets`, `api/<kind>/info`, `api/<kind>/model.*` | WIRED | every fetched path has a route |
| `test_parity.py` | `params` / `app.js` | `model_fields`, `app.js` source | WIRED | |
| `Makefile` | `refresh-requirements.sh` | `lock:` target | WIRED | `Makefile:120 lock:` |
| `Dockerfile` | `docker/smoke.py` | `python docker/smoke.py` at build | WIRED | `Dockerfile:30` |
| `pre-commit` | `skip_tokens` | hook | WIRED | |
| `test_pr_land.py` | `required-jobs.txt` | drift test | WIRED | in the gate |
| `required-jobs.txt` | GitHub ruleset | `required_status_checks` contexts | WIRED | live read-back equal |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `app.js` form | `schema.properties` | `GET /api/schema?kind=` -> `KINDS[kind].model_json_schema()` | Yes, the registered model | ✓ FLOWING |
| `app.js` info panel | `info.rows`, `info.warnings` | `GET /api/<kind>/info` -> `derive(q)` | Yes, closed-form values, printed as sent (`test_the_ui_prints_the_numbers_as_sent...`) | ✓ FLOWING |
| `app.js` viewer | STL `ArrayBuffer` | `GET /api/<kind>/model.stl?quality=preview` -> pool -> `solid.export` | Yes, 1.58 MB STL of the threaded hex part | ✓ FLOWING |
| `app.js` downloads | `href` | built from `info.downloads` | Yes | ✓ FLOWING |

`pitch` now reaches the geometry (it is the thread pitch). The Phase 1 note "pitch flows to validation and the info document but not to geometry" no longer applies.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Gate | `make verify` | 2637 passed, 9 contracts kept, 97.33% | ✓ PASS |
| D-16 invariant | `pytest tests/test_pool.py::test_two_same_slot_timeouts_...` | 1 passed | ✓ PASS |
| Registry parity (subset) | `pytest tests/test_parity.py -k "registry_is_not_empty or ... literal_check_has_teeth or repeated_parameter"` | 7 passed | ✓ PASS |
| Frozen defaults | `pytest tests/test_params.py -k "frozen_defaults or default_kind"` | 3 passed | ✓ PASS |
| Whole stack through lifespan and pool | `TestClient(app)` script | health 200, STL 200 1.58 MB, STEP 200 `ISO-10303-21` | ✓ PASS |
| Foreign field / duplicate key / over-bound / conflict -> 422 naming the field | API script | all four 422 with the named loc or `ctx.fields` | ✓ PASS |
| Foreign flag / repeated flag / bad value | `screw info bolt --m 5`, `--d 5 --d 6`, `--d 0` | exit 2 each, naming the argument | ✓ PASS |
| Unbuildable length gives no number | `screw info bolt --length 1e-8 --thread-length 1e-8` | no turns or volume row, warning; export refused | ✓ PASS |
| Web UI in a browser | none available to this verifier | owner UAT 2026-10-06 and 2026-10-13 | ✓ owner-verified |

### Probe Execution

No `scripts/*/tests/probe-*.sh` exists and no plan declares a probe. Not applicable.

### Requirements Coverage

Requirement IDs from plan frontmatter: 01-01 FRNT-01, FRNT-03, INFR-01, INFR-02; 01-02 FRNT-01, FRNT-03, INFR-01; 01-03 FRNT-04, FRNT-01; 01-04 FRNT-02, INFR-01; 01-05 FRNT-05, FRNT-01, FRNT-02, FRNT-04; 01-06, 01-07, 01-08, 01-10 INFR-01; 01-09 INFR-01, INFR-02. The union is exactly the seven IDs given for this phase. REQUIREMENTS.md maps FRNT-01 to FRNT-05, INFR-01 and INFR-02 to Phase 1, all `Complete`. No orphaned requirement.

| Requirement | Source Plans | Description | Status | Evidence |
| ----------- | ------------ | ----------- | ------ | -------- |
| FRNT-01 | 01-01, 01-02, 01-03, 01-05 | One frozen Pydantic model per kind over a shared base, registered by `kind`; foreign field is a 422 naming it | ✓ SATISFIED | `FastenerParams` / `BoltParams` / `KINDS`; `extra="forbid"`; Truths 3, 13 |
| FRNT-02 | 01-04, 01-05 | Web UI generated from `/api/schema`: form, live 3D preview, info panel, shareable URL with defaults omitted | ✓ SATISFIED | Truth 2 (owner UAT, twice) and the source assertions in `test_parity.py` |
| FRNT-03 | 01-01, 01-02 | HTTP API serves info, STL, STEP, schema and health; admission control in the web layer only | ✓ SATISFIED | Truths 1, 5 |
| FRNT-04 | 01-03, 01-05 | CLI `screw serve \| info \| export \| pair` with flags from the model; never imports the web layer | ✓ SATISFIED (Phase 1 scope) | `serve`, `info`, `export` done, flags from `model_fields`, contract KEPT. `pair` is Phase 5 (PAIR-04) by roadmap design. REQUIREMENTS.md marks FRNT-04 `[x]` while its text still names `pair`; that wording drift predates this run and is recorded, not a gap. |
| FRNT-05 | 01-05 | Each kind ships on UI, API and CLI with parity proven model-driven by one registry test | ✓ SATISFIED | Truth 4 |
| INFR-01 | 01-01 to 01-10 | spur's runtime ported per L07 with a walking-skeleton kind | ✓ SATISFIED | Truths 5 to 10, 16 |
| INFR-02 | 01-01, 01-09 | Module graph enforced by import-linter | ✓ SATISFIED (narrower than written) | Truth 11; the tables contract covers `screw.params` and `screw.calc.thread`, not all of `calc` (L13) |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| unfinished-work markers | n/a | `TBD`, `FIXME`, `XXX`, `TODO`, `HACK` in `src`, `tests`, `docker`, `bench`, `scripts`, `Makefile`, `Dockerfile`, `compose.yaml` | ✓ none | `git grep` finds none outside the Makefile's own scan recipe; `make verify`'s `no-fake-done` passed. |
| `AGENTS.md` (`CLAUDE.md` symlink) | 16 | still calls the bolt a plain unthreaded cylinder | ℹ️ Info | Known docs-record issue, not a gap. |
| `compose.yaml` | 18 | comment "the skeleton is lighter" | ℹ️ Info | Known docs-record issue, not a gap. |
| `docs/tech_debt/resolved/*` | n/a | `Resolved in:` shas cite pre-squash branch commits | ℹ️ Info | Owner accepted 2026-10-13. |
| `src/screw/__init__.py` | 20 | `int_env` clamps `0` and negatives to `1` (see the review observation) | ⚠️ Warning | Deployer-env typo only; not user input, no wrong number printed. Not a blocker. |

The three former app.js warnings of the 2026-10-06 report are gone: the numbers are printed as sent (`test_the_ui_prints_the_numbers_as_sent_under_the_designation_and_the_groups`), a foreign or unreadable hash key refuses the link whole (`app.js:285-289`, `:299-304`), and the mesh's warnings stay on screen over a failed update (`test_the_ui_keeps_the_warnings_of_the_mesh_on_screen`). Their debt files (`ui-rounds-displayed-numbers`, `ui-drops-foreign-hash-keys`, `ui-hides-warnings-on-failed-update`) are in `docs/tech_debt/resolved/`.

### Review disposition observation (not a gap)

`01-REVIEW-DISPOSITION.md` lists 13 findings with `disposition: open` (`open: 13`), recorded 2026-10-06 and never updated. That file is stale as a record; the code on `main` tells a different story. Checked finding by finding against `main` at HEAD:

| Finding | State on `main` | How verified |
| ------- | --------------- | ------------ |
| CR-01 collapsed thin solid served as 200 | **Fixed.** `_write_export` refuses a failed STL write and a non-`RetDone` STEP status; `_check_stl` checks header count against byte length and a minimum of 4 facets; `check_solid` gates the volume with the L11 estimator (`solid/__init__.py:102`, `:167`, `:176`). A length below `MIN_TAIL_MM` is refused in `calc` and the builder. Debt file resolved (`de9304e`, inside PR #10). | code read; `--length 1e-8` run by hand: no volume printed, export refused with a named error |
| WR-01 repeated query key | **Fixed.** `refuse_repeated_keys` (`app.py:177`) and `_Once` / `_OnceBool` (`cli.py:36`, `:43`). | live 422 `duplicate`; CLI exit 2 |
| WR-05 UI number formatter / unbounded pitch | **Fixed in effect.** The UI prints server numbers as sent; huge pitch is refused by the root-radius rule. | `--pitch 1e100` refused naming `d` and `pitch`; parity test |
| WR-07 (second half) kernel loaded before parameter validation | **Fixed.** `_params()` runs before the kernel imports (`cli.py:151`, `_params` before `from .solid import` at `:163`). | `--d 0` refuses without kernel load |
| WR-07 (first half) `screw export` raw traceback for an unwritable path | **Still open.** `cli.py:169` `out.write_bytes(data)` is unguarded; `screw export bolt -o /nonexistent/x.stl --quality preview` prints a `FileNotFoundError` traceback, exit 1. | run by hand |
| WR-02 `int_env` clamps `0` / negative to 1 | **Still open.** `src/screw/__init__.py:20`: `max(1, int(...))`; `SCREW_BUILD_TIMEOUT=0` and `=-5` both give `1`. | run by hand |
| WR-03 per-build timeout counts queue wait | **Still open.** `pool.py:172` `asyncio.wait_for(future, timeout=self.timeout)` starts at submit. Latent for in-grid parts (a default M6 x 20 builds in about 0.1 s); it can fire for a slow build queued behind another on one slot. It fails safe: a 503 `timeout` with `Retry-After`, no wrong number served. Phase 3 made slow builds possible, which is the trigger the review named. | code read |
| WR-04 absolute-mm tessellation makes a tiny part a coarse prism | **Still open**, INTERIM-labelled (`solid/__init__.py` says Phase 5 re-chooses it against the clearance, FRNT-06). The closed-form volume is still what the panel prints. | code read |
| WR-06 `bench.memory sweep` succeeds when requests failed | **Still open.** `bench/memory.py:269` `all(row.peak_bytes is not None ...)` ignores `failures`. Harness only; `confirm()` does check failures. | code read |
| IN-01 `quality` accepted on STEP | **Still open** (STEP route takes `quality`; it is part of the cache key). | code read |
| IN-02 `slug()` uses `%g` | **Still open** (`params.py` `slug`). | code read |
| IN-03 `Accept-Encoding` ignores `q=0` | **Still open** (`app.py` `"gzip" in ...`). | code read |
| IN-04 emptied field / `#d=abc` builds the default silently | **Largely fixed for links** (`app.js:299-304` refuses an unreadable present key); the live-typing blank-field case was not re-tested. | code read |
| IN-05 CI and delivery nits | Not re-checked; `ci.yml` and `Dockerfile` are unchanged since Phase 1 (the floating base tag and the missing `docker logs` step remain). | git log |

None of the still-open items is a correctness defect on `main` in the L02 sense (none prints a plausible wrong number, silently changes a user-set part, or serves a mesh that is not the part). The two that touch the product at runtime, WR-03 and WR-02, fail loudly and safe. They are an observation, not a gap, per the instruction for this run. Housekeeping for the owner: only CR-01 and WR-01 and the three UI items have debt files; the remaining open items (WR-02, WR-03, WR-04, WR-06, WR-07 first half, IN-01 to IN-03, IN-05) have no `docs/tech_debt/` file, and `01-REVIEW-DISPOSITION.md` still says `open: 13`. Filing them or closing the disposition file is a decision for the orchestrator and the owner; this verifier changed neither.

### Human Verification Required

None new. The two items of the previous report (the seven-step browser check and the stale-response check) were walked by the owner and recorded `pass` in `01-UAT.md` (session completed 2026-10-06T08:28:30Z); Phase 3's 2026-10-13 UAT re-ran browser checks on the same page and passed. Nothing in the code on `main` contradicts those verdicts: the hash logic, the sequence guards and the schema-driven form are present and covered by source assertions in `test_parity.py`. The judgment-tier prohibitions flagged in the 2026-10-06 report were re-read today and hold, now without the three web-page exceptions that report listed:

- MUST NOT print a number that cannot be computed honestly: holds (Truth 14); the UI prints server numbers as sent.
- MUST NOT silently change a part the user did not ask to change: holds on API, CLI and web (Truths 3, 13); the web page now refuses a foreign or unreadable hash key instead of dropping it.
- MUST NOT present the walking skeleton as a product build: holds in the form it takes today; `STANDING_WARNING` says "not a product build" and is first in every info document, and `__version__` is `0.0.0`.
- MUST NOT present a spur-carried runtime figure as measured for screw: holds (Truth 10); INTERIM labels carry their spur source and the Phase 7 re-sweep.

`01-SECURITY.md` is `verified` with `threats_open: 0`; not re-run.

### Gaps Summary

There are no gaps. Every Phase 1 runtime deliverable still holds on `main` at `752d20c`, through three phases of change on top of it: one registered model serves the UI, the API and the CLI; the parity test runs over the registry in `make verify` and has grown with the model; the form is generated from `/api/schema`; the hash omits defaults and the default kind; a conflict or foreign field is a `422` naming the field (an exit 2 on the CLI); caps warn and refusals name their fields; builds run in spawned workers behind admission control that lives only in the web layer; the carried bounds are INTERIM-labelled; the wall, CI (`test (3.12)`, `vendor-bundle`, `image`), the Docker build and the coverage floor are in place and green; and the L02 standing rules hold. The two superseded goal clauses ("plain unthreaded solid", the cylinder-named truths) are re-read per truth above, not reported as defects.

Notes for the orchestrator, none of them gaps:

1. ROADMAP marks Phase 1 `Mode: mvp`, but its goal is not in "As a ... I want to ... so that ..." form. Verification proceeded on the standard goal-backward method at the orchestrator's request, as in the previous report.
2. `01-REVIEW-DISPOSITION.md` is stale (`open: 13`) against `main`; see the observation table.
3. The FRNT-04 text in REQUIREMENTS.md still names `pair`, which is Phase 5 (PAIR-04).

---

_Verified: 2026-10-13T08:00:00Z_
_Verifier: Claude (gsd-verifier)_
