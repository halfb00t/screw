---
phase: 01-runtime-port-and-walking-skeleton
verified: 2026-10-06T08:05:00Z
status: human_needed
score: 15/17 must-haves verified
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
covered_digest: "v3:sha256:c552cee293cc6d0abcfb39792c8eccf32f64cc94e3443fb500976851fc66ed6f"
behavior_unverified: 2
overrides_applied: 1
overrides:
  - must_have: "Plans 01-01..01-09 merged to main as one squash commit with gh pr merge N --squash --delete-branch, before any wall existed (D-12; main was pushed beforehand, so the PR diff was phase work only, D-13)"
    reason: "PR #1 landed as merge commit 4951d47 (51 commits) instead of one squash commit. Process shape only: the phase code is on main either way and the wall applies from PR #2 onward."
    accepted_by: "owner (recorded in .planning/STATE.md line 99)"
    accepted_at: "2026-10-06"
deferred:
  - truth: "`screw pair` subcommand named in FRNT-04's text (`screw serve | info | export | pair`)"
    addressed_in: "Phase 5"
    evidence: "REQUIREMENTS PAIR-04 maps to Phase 5 and names the `screw pair` CLI subcommand; ROADMAP Phase 5 success criterion 3: '`screw pair` and the solid-package function return `proven | violated | inconclusive`'. Phase 1's own success criterion 1 lists `screw serve | info | export` only, and plan 01-03 states 'no pair (Phase 5)'."
  - truth: "import-linter contracts 'params and calc never import tables' and 'tables is a leaf' (INFR-02 text)"
    addressed_in: "Phase 4"
    evidence: "Phase 1 success criterion 4: 'each later contract is written to land with the module it guards (tables in Phase 4, the pair proof in Phase 5)'; no tables module exists yet to guard."
behavior_unverified_items:
  - truth: "Web UI: form generated from /api/schema, live 3D preview, info panel, and a shareable hash that carries only non-default fields and writes kind= only when it differs from the default (ROADMAP SC1, plan 01-04)"
    test: "Run `make serve`, open http://127.0.0.1:8000/ and walk the seven-step human-check in 01-04-PLAN.md Task 1 (selector shows bolt; form order and units; Diameter=8 gives hash #d=8 with no kind=; typing 6.0 drops d; clearing Length drops it; Diameter=100001 shows an error naming Diameter and keeps the last part; #kind=nut shows an error naming nut and builds nothing; copy-link round trip; STL and STEP downloads open)"
    expected: "Each step behaves as written; the preview renders a cylinder; the info panel lists Diameter, Pitch, Length, Volume (closed form) and the standing walking-skeleton warning"
    why_human: "WebGL, clipboard, hash round trip and DOM state transitions run only in a browser. The gate has no browser (L01); app.js is checked by `node --check` and by source assertions in tests/test_parity.py, which prove it is generic and text-only, not that the hash logic or viewer behave."
  - truth: "Switching kind or editing a field while a build is in flight never renders the older response (plan 01-04 edge FRNT-02 concurrency, verification: backstop)"
    test: "In the same browser session type several Diameter values within one second (and, once a second kind exists, switch kind mid-build)"
    expected: "Only the last value's preview and info panel remain; no older response overwrites a newer one"
    why_human: "Non-inferable timing invariant (seq counter, AbortController, formSeq). Presence of the three mechanisms in app.js is not behavioral evidence; abstained per the backstop rule."
human_verification:
  - test: "Walk the 01-04 seven-step UAT in a browser against `make serve` (see behavior_unverified_items[0])"
    expected: "All seven steps pass"
    why_human: "No browser in the gate; rendering and hash behavior are only observable there"
  - test: "Rapid-typing / stale-response check (see behavior_unverified_items[1])"
    expected: "Only the newest response renders"
    why_human: "Timing behavior in a real browser; backstop truth"
  - test: "unverified-prohibition, human review recommended: 01-01 'MUST NOT print a number that cannot be computed honestly' (judgment tier)"
    expected: "Owner reads src/screw/calc/__init__.py (closed-form volume, overflow guard, no kernel Volume(), no thread/turn rows) and confirms. Non-authoritative LLM-judge verdict: HOLDS in calc/API/CLI. The web page's `fmt` (app.js:18) rounds displayed values to three decimals (a valid d=0.0004 shows '0 mm'): owner-signed `must` debt 2026-10-06-ui-rounds-displayed-numbers.md, trigger before the Phase 4 ISO-rows plan."
    why_human: "Judgment-tier prohibition, never a silent pass"
  - test: "unverified-prohibition, human review recommended: 01-01 'MUST NOT silently change a part the user did not ask to change' (judgment tier)"
    expected: "Non-authoritative LLM-judge verdict: HOLDS on API and CLI (defaults frozen at 6.0/1.0/20.0 and DEFAULT_KIND literal 'bolt'; above-bound is a 422 naming the field, never a clamp; foreign field is a 422 / exit 2). The web hash silently drops a foreign or unparseable hash key (owner-signed `must` debt 2026-10-06-ui-drops-foreign-hash-keys.md, trigger before Phase 3's first shareable field). Owner confirms the deviation is acceptable for the skeleton."
    why_human: "Judgment-tier prohibition, never a silent pass"
  - test: "unverified-prohibition, human review recommended: 01-01 'MUST NOT present the walking skeleton as a product build' (judgment tier)"
    expected: "Non-authoritative LLM-judge verdict: HOLDS (SKELETON_WARNING is first in every info document on API, CLI and the UI panel; version is 0.0.0; no release tag). The web page hides the warning while a failed update leaves the last mesh on screen (owner-signed `must` debt 2026-10-06-ui-hides-warnings-on-failed-update.md, trigger before the first non-skeleton warning ships)."
    why_human: "Judgment-tier prohibition, never a silent pass"
  - test: "unverified-prohibition, human review recommended: 01-01 / 01-06 / 01-09 'MUST NOT present a spur-carried runtime figure as measured for screw' (judgment tier)"
    expected: "Non-authoritative LLM-judge verdict: HOLDS (INTERIM labels on 22 lines across src/, Dockerfile, compose.yaml and app.js, each naming its spur source and 'Phase 7 re-sweeps (OPER-02)'; the D-02 audit command prints 'missing: none'). Owner skims the wording for honesty."
    why_human: "Judgment-tier prohibition; wording honesty is not machine-checkable"
---

# Phase 1: Runtime Port and Walking Skeleton Verification Report

**Phase Goal:** A user can generate a walking-skeleton bolt (`d`, `pitch`, `length`, plain unthreaded solid; an internal milestone, never released) from the web UI, the HTTP API and the CLI, all served by spur's ported runtime from one registered model, with front-end parity proven by one test over the registry.
**Verified:** 2026-10-06T08:05:00Z
**Status:** human_needed
**Re-verification:** No, initial verification

Every automated check passed and nothing observable is missing. The one thing no automated check can prove is the web UI's behavior in a browser, so the phase stops at `human_needed`. No gaps (BLOCKERs) were found.

## Goal Achievement

### Method and evidence run by this verifier

SUMMARY claims were not trusted. Fresh evidence gathered in this session:

- `make verify` run today on branch `docs/phase-01-close`: ruff, mypy `--strict`, import-linter `Contracts: 6 kept, 0 broken`, unfinished-work scan, pytest `285 passed in 17.76s`, coverage `95.56%` ("Required test coverage of 94.0% reached"), exit 0.
- `.venv/bin/python docker/smoke.py` through the real lifespan and spawned worker pool: printed `smoke: kernel, exports, ASGI stack and validation all live`.
- CLI run by hand: `screw info bolt --d 8`, `--len 5` (exit 2), `--m 5` (exit 2, "unrecognized arguments: --m 5"), `info nut` (invalid choice), `--d 100001` / `--d inf` (exit 2, "error: d: ..."), `export` to STL (5084 bytes = 84 + 50 x 100 triangles, standing warning on stderr) and STEP (`ISO-10303-21;`).
- Named test `test_two_same_slot_timeouts_in_one_incident_end_as_build_timeout_not_attribute_error` run alone with real workers: passed.
- `python -m bench.build_time`: 12 parts built and exported, load line printed before the first row.
- `cmp` of `three.bundle.min.js` against spur's: identical. `node --check` on an `.mjs` copy of `app.js`: syntax ok.
- `gh api repos/halfb00t/screw/rules/branches/main` and `rulesets/24563199`: read live (see truth 16).
- `gh run view 37428477672`: `success` on head `e69d351` with jobs `vendor-bundle`, `image`, `test (3.12)`.
- `gsd verify.artifacts` / `verify.key-links` on all ten plans (see Artifacts and Key Links).
- `git status` after all commands: only the pre-existing untracked `.planning/ui-reviews/`. No tracked file was modified.

### Observable Truths

ROADMAP success criteria are the contract (SC1 to SC4); plan-level truths are added where they carry distinct claims.

| #  | Truth | Status | Evidence |
| -- | ----- | ------ | -------- |
| 1  | SC1 (API and CLI half): the same skeleton bolt comes from the API (info, STL, STEP, schema, health) and from `screw serve \| info \| export` | ✓ VERIFIED | `app.py`: `/api/bolt/info`, `/api/bolt/model.{stl,step}`, `/api/schema?kind=`, `/api/kinds`, `/api/health`. `cli.py`: `serve`, `info`, `export`. Smoke prints 200s, STL > 1000 B, STEP header. CLI run by hand wrote a valid binary STL and STEP. `test_parity.py::test_the_cli_and_the_api_print_the_same_document` compares the CLI and API info documents for defaults and 1.5x each float field. Wording note: schema is `/api/schema?kind=bolt` and health is global `/api/health` by owner decision D-08 / L09, not literally "under the bolt kind path". |
| 2  | SC1 (web UI half): form generated from `/api/schema`, live 3D preview, info panel, shareable URL carrying the full parameter set with defaults omitted | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Present and wired: `index.html` has every id `app.js` uses (all 11 found); `app.js` fetches `api/kinds`, `api/schema?kind=`, `api/<kind>/info`, `api/<kind>/model.stl`, builds the form from `schema.properties`, writes the hash through `partQuery()` (`Number(input.value) !== Number(defaults[name])`) and `hashQ.set('kind', currentKind)` only when `currentKind !== kinds.default`; `/` and `/static/app.js` served (`test_index_and_static`, smoke); vendored bundle byte-identical. No test runs the browser logic, and the seven-step UAT in 01-04 was never run (01-04-SUMMARY and 01-VALIDATION both list it as outstanding). Routed to human verification. |
| 3  | SC2 (refusal): a field the bolt kind does not define is a 422 naming it on the API and an error naming it on the CLI, never silently ignored | ✓ VERIFIED | `FastenerParams.model_config = ConfigDict(frozen=True, extra="forbid")`; `BoltModelQuery` inherits it. `test_api.py::test_a_foreign_field_is_a_422_naming_it`, `test_parity.py::test_a_foreign_field_is_refused_on_every_route` (loc `["query", "zz_not_a_field"]` on info and model.stl). CLI: `--m 5` and prefix `--len 5` exit 2 naming the argument (`allow_abbrev=False` on every parser), verified by hand. |
| 4  | SC2 (parity): one parity test over the registry proves the UI, API and CLI expose the same fields, and stays in `make verify` | ✓ VERIFIED | `tests/test_parity.py` (245 lines, 12 tests, 8 parametrised over `list(KINDS)`); compares against `KINDS[kind].model_fields`, never a consumer list; first test asserts `len(KINDS) >= 1` and `DEFAULT_KIND in KINDS`; `test_the_literal_check_has_teeth` has positive and negative controls. It ran inside today's `make verify`. Three planted-drift negative controls recorded red in 01-05-SUMMARY (the CLI-flag control exposed a real hole that was fixed in `ebbccf0`). The UI half is source assertion only (no browser): see truth 2. |
| 5  | SC3 (runtime): builds execute in worker processes off the event loop; an overloaded server answers 503 + Retry-After from the web layer only | ✓ VERIFIED | `pool.py` `BuildPool` over spawned `ProcessPoolExecutor`s; `solid` imported via `importlib.import_module("screw.solid")` inside the worker only (2 occurrences); contract 5 (`screw.app` vs cadquery/OCP, indirect imports forbidden) KEPT. Admission control (`BUILD_QUEUE`, `_build_slot`, `HTTPException(503, ..., headers={"Retry-After": "5"})`) lives in `app.py` only. `test_api.py` pins busy/timeout/pool_broken as 503 with type and `Retry-After`. Smoke exercised the real pool. |
| 6  | SC3 (wall): `scripts/pr_land.py`, `skip_tokens.py`, the commit-msg hook and the `main` ruleset are in place | ✓ VERIFIED | Scripts present, `cmp`-identical to spur per 01-07 and 85 tests in the gate. `.git/hooks/commit-msg` and `.git/hooks/pre-commit` exist and are executable. Ruleset `default` id 24563199 read live: `enforcement: active`, `bypass_actors: []`, rules `deletion`, `non_fast_forward`, `pull_request`, `required_status_checks` with contexts `test (3.12)`, `vendor-bundle`, `image` and strict policy true. |
| 7  | SC3 (`make check`): in-image smoke test and vendored-bundle byte check pass | ✓ VERIFIED | CI run 37428477672 on `e69d351`: `image` (builds the image, which runs `docker/smoke.py` at build) and `vendor-bundle` (npm ci, rebuild, `git diff --exit-code`) both `success`, plus `test (3.12)`. Local `make verify` green; bundle `cmp`-identical to spur's. This verifier did not re-run `make check` / Docker (read-only constraint); CI is the evidence. |
| 8  | SC3 (coverage): the coverage floor is enforced | ✓ VERIFIED | `pyproject.toml` `fail_under = 94`, `precision = 2`, `concurrency = ["multiprocessing", "thread"]`; `make test` runs `-n $(PYTEST_WORKERS) --cov --cov-report=term`; today's run printed "Required test coverage of 94.0% reached. Total coverage: 95.56%". Negative control (exit 2 at `--cov-fail-under=100`) recorded in 01-09-SUMMARY. The floor is a measured number (floor(95.03 - 0.25)), not spur's 96. |
| 9  | SC3 (bench): the `bench/` harness runs against the skeleton | ✓ VERIFIED | `bench/{corpus,build_time,export_cost,latency,memory}.py`, README and RESULTS present; `python -m bench.build_time` ran today (12 rows, load before first row); 25 predicate tests in `tests/test_bench.py` in the gate; `bench/RESULTS.md` labels each recorded run "not a bound (L07)". |
| 10 | SC3 (no gear code, no spur figure as a final bound) | ✓ VERIFIED | `params.py`, `calc/__init__.py`, `solid/*` are new designs over `FastenerParams`/`BoltParams`. `git grep` for gear identifiers in src/docker/bench/scripts finds only comments that cite spur's measured corpus as the source of an INTERIM figure. 22 lines mention `INTERIM` (`git grep -c`: Dockerfile 2, compose.yaml 3, app.py 8, cli.py 1, params.py 4, solid 3, app.js 1); each labelled figure carries the spur source and "Phase 7 re-sweeps (OPER-02)". The plan's D-02 audit (vendored bundle excluded, as 01-09 corrected) prints `missing: none`. |
| 11 | SC4: `make verify` is green with import-linter enforcing the inherited contracts plus "only `solid` imports `cadquery`/`OCP`" and "`app` never imports the kernel by any path" | ✓ VERIFIED | Today: `Contracts: 6 kept, 0 broken` (app never imports tests; calc/params/cli kernel-free; CLI vs web layer; calc vs logger; app vs kernel with `allow_indirect_imports = false`; only solid imports the kernel, "2 ignored imports"). INFR-02's tables contracts are deferred to Phase 4 by SC4 itself. |
| 12 | D-16 (behavior-dependent): a second same-slot timeout after the first already replaced the slot ends as `BuildTimeout`, never `AttributeError` | ✓ VERIFIED | Guard is the first statement of `_run_with_timeout`'s `except TimeoutError:` (`self._executors[hash(p) % self.workers] is not executor`, `pool.py`), before `executor._processes` is touched. Invariant exercised, not inferred from presence: the named regression test (ten concurrent same-slot timeouts, real workers) passed when run alone today; RED against the unguarded pool was reproduced 6 of 6 (commit `0de63f8`, GREEN `e1861ab`). |
| 13 | Validation boundary and frozen defaults: d, pitch, length refuse 0, negative, inf, nan; d and length above `INTERIM_MAX_MM = 1e5` are refused naming the field, never clamped; defaults 6.0 / 1.0 / 20.0 and `DEFAULT_KIND = "bolt"` | ✓ VERIFIED | `params.py`: `_f()` sets `gt=0`, `allow_inf_nan=False`, `le=INTERIM_MAX_MM`; `DEFAULT_KIND` is a literal. Tests in `test_params.py` / `test_api.py` (bound inclusive at 100000, `nextafter` refused, 1e200 a 422 naming `d`, d=1e-9 a 422 `build_error`) pass in the gate. Hand check: `--d 100001` -> "error: d: Input should be less than or equal to 100000", `--d inf` -> "error: d: Input should be a finite number", both exit 2. |
| 14 | The info document is honest: closed-form volume (never the kernel's `Volume()`), `SKELETON_WARNING` first in every document, no thread or turn row, overflow gives no row plus a warning | ✓ VERIFIED | `calc/__init__.py` `_bolt()`: rows d, pitch, length, then `volume = math.pi * (p.d / 2) ** 2 * p.length` inside `try/except OverflowError` plus `math.isfinite`; `warnings = [SKELETON_WARNING]`. Hand check: `screw info bolt --d 8` -> volume 1005.3096491487338 mm³, warning present. `test_calc.py` covers the `model_construct(d=1e200)` branch. |
| 15 | UI never renders a stale response while typing or switching kind (plan 01-04 edge FRNT-02 concurrency, `verification: backstop`) | ? UNCERTAIN (insufficient_spec) | `seq`, `AbortController` and `formSeq` are present and checked before every render (`app.js`), but presence is not evidence for a timing invariant. Abstained per the backstop rule; routed to human verification. |
| 16 | Plan 01-10: the ruleset read-back equals `required-jobs.txt`, squash settings are PR_TITLE/PR_BODY, and the ruleset id reached main through `make pr.land` | ✓ VERIFIED | Live `gh api`: contexts `["test (3.12)","vendor-bundle","image"]` equal the three non-comment lines of `required-jobs.txt`; `strict: true`; `bypass_actors: []`; `gh api repos/halfb00t/screw --jq '[.squash_merge_commit_title,.squash_merge_commit_message]'` -> `["PR_TITLE","PR_BODY"]`; PR #2 landed as squash `e69d351`, ancestor of this branch. |
| 17 | Plan 01-10: Phase 1 merged to main as one squash commit (D-12) | ✓ PASSED (override) | PR #1 is `MERGED` as merge commit `4951d47`, not a squash. Override: owner accepted the shape on 2026-10-06 (STATE.md line 99); D-12's squash rule applies from the wall onward. |

**Score:** 15/17 truths verified (1 of them by override); 2 present or uncertain, behavior-unverified (truths 2 and 15).

### Deferred Items

Not met in Phase 1, explicitly addressed by a later phase.

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | `screw pair` subcommand (FRNT-04's text lists `serve \| info \| export \| pair`) | Phase 5 | PAIR-04 (Phase 5) names the `screw pair` subcommand; ROADMAP Phase 5 SC3 repeats it. Phase 1 SC1 lists only `serve \| info \| export`. |
| 2 | import-linter contracts "`params`/`calc` never import `tables`" and "`tables` is a leaf" | Phase 4 | Phase 1 SC4: "each later contract is written to land with the module it guards (tables in Phase 4, the pair proof in Phase 5)". |

### Required Artifacts

`gsd verify.artifacts` over every plan's `must_haves.artifacts`:

| Plan | Result | Notes |
| ---- | ------ | ----- |
| 01-01 | 10/10 pass | params, calc, solid, bolt, pool, app, records, smoke, pyproject, test_pool |
| 01-02 | 4/4 pass | test_api, test_records, L09, interim-bounds debt item |
| 01-03 | 4/4 pass | cli, `__main__`, pyproject entry point, test_cli |
| 01-04 | 5/5 pass | app.js, index.html, vendored bundle, web/package.json, app.py static mount |
| 01-05 | 0/1 by literal pattern | `tests/test_parity.py` lacks the literal text `for kind in KINDS`; the file is substantive and iterates the registry with `@pytest.mark.parametrize("kind", list(KINDS))` (8 uses; plan acceptance asked for at least 6). Pattern mismatch only, intent met. |
| 01-06 | 4/4 pass | refresh script, Dockerfile, compose, requirements.txt |
| 01-07 | 4/4 pass | pr_land, skip_tokens, required-jobs.txt, L08 |
| 01-08 | 4/4 pass | corpus, build_time, RESULTS, test_bench |
| 01-09 | 3/3 pass | coverage config, RESULTS coverage section, overview.md |
| 01-10 | 1/1 pass | HOW_TO_DEVELOP records `rulesets/` |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| 01-01 app.py | pool.py | `BuildPool(` in lifespan | WIRED | verified by tool |
| 01-01 pool.py | solid | `import_module("screw.solid")` in worker | WIRED | verified by tool; 2 occurrences |
| 01-01 app.py | calc | `derive(` in `bolt_info` | WIRED | verified by tool |
| 01-01 solid | bolt.py | `cylinder(` dispatch | WIRED | verified by tool |
| 01-02 tests | app.py | `dependency_overrides[build_backend]` | WIRED | verified by tool |
| 01-03 cli.py | params | `for kind, model in KINDS.items()` | WIRED | verified by tool |
| 01-03 cli.py | solid | lazy `from .solid import` in `cmd_export` | WIRED | verified by tool |
| 01-04 app.js | app.py | `api/kinds`, schema, info, model fetches | WIRED | verified by tool; every fetched path has a route |
| 01-05 test_parity | params / app.js | `model_fields`, `app.js` | WIRED | verified by tool |
| 01-06 Makefile | refresh-requirements.sh | `lock:` target | WIRED | The tool reported "pattern `^lock:` not found" because of the `^` anchor; manual check: `Makefile:112 lock:` and `:113 docker/refresh-requirements.sh`. |
| 01-06 Dockerfile | docker/smoke.py | `python docker/smoke.py` at build | WIRED | verified by tool; CI `image` job green |
| 01-07 pre-commit | skip_tokens | `scripts.skip_tokens` hook | WIRED | verified by tool |
| 01-07 test_pr_land | required-jobs.txt | drift test | WIRED | verified by tool; test in the gate |
| 01-10 required-jobs.txt | GitHub ruleset | `required_status_checks` contexts | WIRED | The tool cannot see GitHub. Live `gh api` read-back equal (truth 16). |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `app.js` form | `schema.properties` | `GET /api/schema?kind=` -> `KINDS[kind].model_json_schema()` | Yes, the registered model | ✓ FLOWING |
| `app.js` info panel | `info.rows`, `info.warnings` | `GET /api/<kind>/info` -> `derive(q)` | Yes, closed-form values | ✓ FLOWING (display rounds, see Anti-Patterns) |
| `app.js` viewer | STL `ArrayBuffer` | `GET /api/<kind>/model.stl?quality=preview` -> pool -> `makeCylinder` | Yes, 84 + 50n byte binary STL | ✓ FLOWING |
| `app.js` downloads | `href` | `setDownloads(q)` -> `api/${currentKind}/model.${fmt}` | Yes | ✓ FLOWING |

`pitch` flows to validation and the info document but not to geometry. This is by design (D-04), stated in the field's help text and in the standing warning.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Skeleton served end to end through lifespan, pool, kernel, validation | `.venv/bin/python docker/smoke.py` | smoke line printed | ✓ PASS |
| CLI info equals API document shape | `.venv/bin/screw info bolt --d 8` | rows d/pitch/length/volume, warning | ✓ PASS |
| Abbreviated flag refused | `.venv/bin/screw info bolt --len 5` | exit 2 | ✓ PASS |
| Foreign flag refused naming it | `.venv/bin/screw info bolt --m 5` | exit 2, names `--m` | ✓ PASS |
| Unknown kind refused | `.venv/bin/screw info nut` | exit 2, invalid choice | ✓ PASS |
| Over-bound and non-finite refused naming the field | `--d 100001`, `--d inf` | exit 2, `error: d: ...` | ✓ PASS |
| STL export is a well-formed binary STL | `screw export bolt --d 8 -o b.stl --quality preview` | 5084 = 84 + 50 x 100 | ✓ PASS |
| STEP export | `screw export bolt -o b.step` | begins `ISO-10303-21;` | ✓ PASS |
| D-16 invariant | `pytest tests/test_pool.py::test_two_same_slot_timeouts_...` | 1 passed | ✓ PASS |
| Bench harness runs on the skeleton | `python -m bench.build_time` | 12 rows | ✓ PASS |
| Gate | `make verify` | 285 passed, 6 contracts kept, 95.56% | ✓ PASS |
| Web UI in a browser | none available | n/a | ? SKIP -> human verification |

### Probe Execution

No `scripts/*/tests/probe-*.sh` exists and no plan declares a probe. Not applicable.

### Requirements Coverage

Requirement IDs from plan frontmatter: 01-01 FRNT-01, FRNT-03, INFR-01, INFR-02; 01-02 FRNT-01, FRNT-03, INFR-01; 01-03 FRNT-04, FRNT-01; 01-04 FRNT-02, INFR-01; 01-05 FRNT-05, FRNT-01, FRNT-02, FRNT-04; 01-06, 01-07, 01-08, 01-10 INFR-01; 01-09 INFR-01, INFR-02. Union equals the seven IDs the phase was given. REQUIREMENTS.md maps FRNT-01 to FRNT-05, INFR-01, INFR-02 to Phase 1: no orphaned requirement.

| Requirement | Source Plans | Description | Status | Evidence |
| ----------- | ------------ | ----------- | ------ | -------- |
| FRNT-01 | 01-01, 01-02, 01-03, 01-05 | One frozen Pydantic model per kind over a shared base, registered by `kind`; foreign field is a 422 naming it | ✓ SATISFIED | `FastenerParams`/`BoltParams`/`KINDS`; `extra="forbid"`; truths 3, 13 |
| FRNT-02 | 01-04, 01-05 | Web UI generated from `/api/schema`: form, live 3D preview, info panel, shareable URL with defaults omitted | ? NEEDS HUMAN | Generation from the schema is wired and source-asserted; rendering, preview and hash behavior need the browser UAT (truth 2). REQUIREMENTS.md already shows it `[x] Complete`; that is ahead of the UAT. |
| FRNT-03 | 01-01, 01-02 | HTTP API serves info, STL, STEP, schema and health; admission control in the web layer only | ✓ SATISFIED | Truths 1, 5. Schema is `?kind=` and health is global by D-08 / L09. |
| FRNT-04 | 01-03, 01-05 | CLI `screw serve \| info \| export \| pair` with flags from the model; never imports the web layer | ✓ SATISFIED (Phase 1 scope) | `serve`, `info`, `export` done, flags from `model_fields`, contract 3 KEPT. `pair` is deferred to Phase 5 (PAIR-04) by roadmap design. |
| FRNT-05 | 01-05 | Each kind ships on UI, API and CLI with parity proven model-driven by one registry test | ✓ SATISFIED | Truth 4 (UI half by source assertion). |
| INFR-01 | 01-01 to 01-10 | spur's runtime ported per L07 (pool, records, app, cli, build_errors, form/viewer/three.js, pr_land, skip_tokens, hook, ruleset, docker/compose, coverage floor, bench) with a skeleton kind | ✓ SATISFIED | Truths 5 to 10, 16. |
| INFR-02 | 01-01, 01-09 | Module graph enforced by import-linter | ✓ SATISFIED (Phase 1 scope) | Truth 11. Tables contracts deferred to Phase 4 per SC4. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `src/screw/static/app.js` | 18, 185 | `fmt = (v) => Number(v).toFixed(3).replace(/\.?0+$/, '')` applied to every `row.value`; a valid `d=0.0004` shows "0 mm" | ⚠️ Warning (L02) | The panel prints a different number than the API sent. Disclosed as UI-SPEC OI-1 and filed as `must` debt with owner sign-off (`docs/tech_debt/active/2026-10-06-ui-rounds-displayed-numbers.md`, trigger: before the Phase 4 plan that puts ISO rows on the panel). Harmless for the four skeleton rows, whose inputs are normal-sized. |
| `src/screw/static/app.js` | 129, 137 | A foreign or unparseable hash key is dropped and the hash is rewritten without it | ⚠️ Warning (L02) | The web path does not refuse what the API and CLI refuse. SC2's wording covers the API and the CLI, so SC2 holds; filed as OI-2 `must` debt (`...ui-drops-foreign-hash-keys.md`, trigger: before Phase 3 adds `left_hand`). |
| `src/screw/static/app.js` | 232-237 | `fail()` replaces warnings with `[]`, hiding the standing warning while the last mesh stays on screen | ⚠️ Warning (D-06) | Filed as OI-3 `must` debt (`...ui-hides-warnings-on-failed-update.md`, trigger: before the first non-skeleton warning ships). |
| `docs/tech_debt/INDEX.md` | n/a | OI-5 (no `aria-invalid`), OI-4, OI-6 to OI-8 are in the UI-SPEC register but not separate debt files | ℹ️ Info | All are `nice` severity and recorded in `01-UI-SPEC.md`; 01-UI-REVIEW scores Experience Design 3/4 on them. |
| unfinished-work markers | n/a | `TBD|FIXME|XXX|TODO|HACK` in src, tests, docker, bench, scripts, Makefile, Dockerfile, compose | ✓ none | Only the Makefile's own scan comment and recipe match; `make verify`'s `no-fake-done` passed. |

No blocker anti-pattern, no unreferenced debt marker, no stub: `pitch` having no geometric effect is an intentional, labelled skeleton limit.

### Human Verification Required

#### 1. Web UI walk-through in a browser

**Test:** `make serve`, open http://127.0.0.1:8000/ and run the seven steps in `01-04-PLAN.md` Task 1 `<human-check>`: selector shows bolt; Diameter, Pitch, Length in order with mm units; preview cylinder; info panel with Diameter, Pitch, Length, Volume (closed form) and the skeleton warning; Diameter 8 gives `#d=8` with no `kind=`; typing 6.0 drops `d`; clearing Length drops it; Diameter 100001 shows an error naming Diameter and keeps the last part; `#kind=nut` shows an error naming nut, lists bolt and builds nothing; Copy link in a new tab reopens the same part; STL and STEP downloads open as files.
**Expected:** every step as written.
**Why human:** WebGL, clipboard and DOM state run only in a browser; the gate has none (L01).

#### 2. Stale-response check

**Test:** type several Diameter values within one second.
**Expected:** only the last value's preview and panel remain.
**Why human:** timing invariant, `verification: backstop`.

#### 3. Flagged judgment-tier prohibitions (autonomous mode: non-authoritative verdicts recorded, none passed silently)

All four verdicts above hold for the calc/API/CLI/infrastructure layers. Three of them have a web-page exception that the owner already signed off as `must` debt (OI-1, OI-2, OI-3). The owner is asked to confirm that those three exceptions remain acceptable for an internal, never-released skeleton, and to skim the INTERIM comment wording for honesty.

### Gaps Summary

There are no gaps. Every ROADMAP success criterion that can be checked without a browser was checked against the code and by running it, and each holds: the three front ends serve the same registered bolt, the foreign-field refusal is real on the API and CLI, the parity test is non-vacuous and in the gate, builds run in spawned workers behind admission control in the web layer only, the wall is live on GitHub, the coverage floor gates the run, the bench harness runs, no gear code was copied, and `make verify` is green with six contracts kept.

Phase status is `human_needed` for one reason: the web UI half of SC1 (and the stale-response invariant) has never been exercised in a browser, because the gate has none. The plan itself scheduled that as the end-of-phase UAT and it has not been run. Two process notes for the orchestrator:

1. ROADMAP marks Phase 1 `Mode: mvp`, but its goal is not in "As a ... I want to ... so that ..." form (`user-story.validate` returns invalid; every plan flagged this). The MVP guard says to refuse and ask for `/gsd-mvp-phase 1`. Verification proceeded on the standard goal-backward method at the orchestrator's explicit request. Restate the goal or drop `Mode: mvp` before Phase 1 is archived.
2. REQUIREMENTS.md already shows FRNT-02 `Complete`, ahead of the browser UAT; the ROADMAP/FRNT-04 text still names `pair` (Phase 5) and "schema and health per kind" (built as `?kind=` and global health by D-08). These are wording drift against locked owner decisions, not defects.

---

_Verified: 2026-10-06T08:05:00Z_
_Verifier: Claude (gsd-verifier)_
