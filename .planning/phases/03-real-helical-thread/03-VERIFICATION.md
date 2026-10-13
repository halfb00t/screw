---
phase: 03-real-helical-thread
verified: 2026-10-13T13:45:00Z
status: passed
score: 14/14 must-haves verified
covered_files:
  - .github/workflows/grid.yml
  - .planning/phases/03-real-helical-thread/03-01-PLAN.md
  - .planning/phases/03-real-helical-thread/03-01-SUMMARY.md
  - .planning/phases/03-real-helical-thread/03-02-PLAN.md
  - .planning/phases/03-real-helical-thread/03-02-SUMMARY.md
  - .planning/phases/03-real-helical-thread/03-03-PLAN.md
  - .planning/phases/03-real-helical-thread/03-03-SUMMARY.md
  - .planning/phases/03-real-helical-thread/03-04-PLAN.md
  - .planning/phases/03-real-helical-thread/03-04-SUMMARY.md
  - .planning/phases/03-real-helical-thread/03-05-PLAN.md
  - .planning/phases/03-real-helical-thread/03-05-SUMMARY.md
  - .planning/phases/03-real-helical-thread/03-06-PLAN.md
  - .planning/phases/03-real-helical-thread/03-06-SUMMARY.md
  - .planning/phases/03-real-helical-thread/03-07-PLAN.md
  - .planning/phases/03-real-helical-thread/03-07-SUMMARY.md
  - Makefile
  - docs/architecture/decision_log.md
  - pyproject.toml
  - src/screw/app.py
  - src/screw/calc/__init__.py
  - src/screw/calc/thread.py
  - src/screw/cli.py
  - src/screw/params.py
  - src/screw/solid/__init__.py
  - src/screw/solid/bolt.py
  - src/screw/solid/helical.py
  - src/screw/static/app.js
  - src/screw/static/style.css
  - tests/test_api.py
  - tests/test_calc.py
  - tests/test_cli.py
  - tests/test_grid.py
  - tests/test_params.py
  - tests/test_parity.py
  - tests/test_solid.py
  - tests/test_thread_maths.py
covered_digest: "v3:sha256:bd9cc73bf196bba9e357deb759e34a412480b5450a364f4441a95e674560081c"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 11/14
  gaps_closed: []
  gaps_remaining: []
  regressions: []
deferred:
  - truth: "A left-hand pair is proven by the same checks as a right-hand pair (second clause of THRD-02)"
    addressed_in: "Phase 5"
    evidence: "Phase 5 SC3: 'right- and left-hand pairs go through the same checks' (PAIR-03); no nut exists before TYPE-03. REQUIREMENTS.md line 15 now carries the annotation 'second clause: Phase 5 PAIR-03' (owner ruling 2026-10-11, UAT test 7)."
  - truth: "Every allowed configuration builds inside the timeout, or is capped/refused with a 422 naming the fields (root radii between 0 and about 3e-5 mm pass validation and then fail in the kernel, WR-04; d=100, length=200 at default pitch exceeds both interim backstops, WR-05)"
    addressed_in: "Phase 7"
    evidence: "Phase 7 SC3 (OPER-03): a configuration that cannot build inside the timeout is capped and warned or refused with a 422 naming the fields. Both items are still active in docs/tech_debt/INDEX.md, Severity must; owner ruling 2026-10-11 (UAT test 6): WR-05 stays must under D-18, trigger is the Phase 7 linux/amd64 re-sweep."
---

# Phase 3: Real Helical Thread Verification Report

**Phase Goal:** A user who sets `d`, `pitch` and `length` in explicit millimetres gets a bolt-kind solid carrying a real ISO 68-1 helical thread, right- or left-hand, on all three front ends, and a build the postcondition rejects never reaches a cache, a preview or a download.
**Verified:** 2026-10-13T13:45:00Z
**Status:** passed
**Re-verification:** Yes, regeneration (#5118) against `main` at HEAD `04b5c50`, after Phase 4 landed on top. The previous report (2026-10-11, `passed` in its frontmatter, 11/14) read `stale` because covered files changed. This run re-derived every truth from the code as it is now; the 03-UAT.md human checkpoints are the only inputs taken from outside the code.
**HEAD:** 04b5c50 on `main`; the working tree is clean apart from untracked `.planning/ui-reviews/` and `web/.DS_Store`.

## Verdict in one paragraph

The goal holds on `main` today, under the Phase 4 default (an ISO 4017 hex screw). The bare thread is still the L11 helical thread; it is gated on its own (`part="thread"`) and again fused with the head and shank, inside the function `lru_cache` wraps, so a refused build is never cached, exported or served. `left_hand` is a boolean on the base model, default false, and reaches the builder, the API, the CLI and the page. Nothing in the roadmap contract failed. The three truths the earlier report left `PRESENT_BEHAVIOR_UNVERIFIED` (checkbox and hand in a browser, link refusals, per-mesh warnings) were run by the owner in a browser on 2026-10-13 (03-UAT.md tests 4 to 7, 33 passed, 0 issues), and the code that those checks exercised is still in the tree; I count them VERIFIED on that evidence and do not re-issue them as human items. Two of the five review findings the old report listed as open are fixed since (WR-02, IN-01, both in Phase 4); three stay active and deferred (WR-04, WR-05 to Phase 7, IN-03 nice).

MVP-mode note: ROADMAP.md marks Phase 3 `Mode: mvp`, but the goal is not written as "As a ..., I want to ..., so that ...", and `user-story.validate` returns `valid: false` for it. I did not refuse: Phases 1 and 2 have the same shape and a User Flow Coverage table would have been invented. Standard goal-backward verification applied. The owner may want to drop the `mvp` tag or rewrite the goal.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: Preview, STL and STEP from UI, API and CLI carry the modelled L11 helical thread with the pinned ISO 68-1:2023 basic profile; the plain solid is gone and there is no cosmetic or unthreaded option | VERIFIED | `solid/__init__.py:_build` builds `bolt.thread(p)` (`bolt.py:thread` -> `helical.thread`, `makeHelix`/`MakePipeShell`) then fuses shank and head. In-process `solid.build(BoltParams())`: 1 solid, valid, precise volume rel +4.95e-08 against `bolt_closed_volume` (gate 9e-05). API (TestClient, inline backend): default `model.stl?quality=preview` 200, 1,579,284 bytes; `model.step` 200, 1,190,192 bytes. CLI: `screw export bolt -o a.stl --quality preview` wrote 1542 KiB, `-o a.step` 1162 KiB, exit 0. `?cosmetic=true` is 422 `extra_forbidden`; the schema has no thread-on/off field (`d, pitch, left_hand, length, s, k, thread_length`). The UI fetches the same `model.stl?quality=preview` route (UAT test 3 pass, 12). |
| 2 | SC2: `left_hand: true` (default false) gives a left-hand thread that passes the same postcondition as the right-hand one across the tested grid; the parity test is green with the field | VERIFIED | `params.py:63` `left_hand = _b(False, ...)` on `FastenerParams`; schema `type: boolean`, `default: False`, third in order. `solid.build(BoltParams(left_hand=True))`: 1 solid, valid, rel +4.95e-08, same as right. `tests/test_solid.py::test_the_hand_decides_which_way_the_thread_climbs_and_both_pass_the_same_gate` (heights in every segment, including the folded tail) and `test_a_left_hand_rod_exports_as_a_preview_stl_and_a_step` ran green now; the hand probe is an independent `isInside` check on the bare thread because the volume gate cannot see hand (and OCCT's classifier is unreliable on the fused M3.5 x 5.4 part, noted in the test). Left STL differs from right on API (1,579,284 vs 1,240,484 bytes) and CLI (1542 vs 1211 KiB). `?left_hand=banana` is 422 `bool_parsing` at `["query","left_hand"]`; `--left-hand --left-hand` and `--left-hand --no-left-hand` exit 2. Grid has both hands: 60 `-m grid` cells (15 sizes x 2 hands x rod/void). `tests/test_parity.py` is in the 455 passed below. My own `isInside` sketch at an arbitrary angle returned (True, True)/(False, False); that was my probe's angle convention, not the code, and I relied on the repo's probe instead. |
| 3 | SC3: Every build is checked before it is cached or served (valid shape, exactly one solid, signed precise volume within tolerance, never bare `Volume()`); a failure is a `BuildError` naming what failed; a positive control feeds the gate a known-bad build | VERIFIED | `solid/__init__.py:check_solid` (count, then `isValid()`, then `volume_check(precise_volume(...))`, NaN-safe, signed); `_build` calls it on the bare thread (`part="thread"`) and on the fused part, inside `_build_checked`, which `lru_cache` wraps (`:166-168`). `Volume()` appears in `src/` only in a docstring (`solid/__init__.py:94`). My control: `bolt.thread` replaced by a plain cylinder, `solid.build` twice raised `BuildError` "Geometry kernel produced the wrong thread: ... relative error +2.316e...", `_build_cached.cache_info().currsize` stayed 0; the real export afterwards succeeded and cached 1 entry. Test controls ran green now: `test_the_gate_refuses_the_naive_sweep_the_kernel_calls_valid`, `..._inverted_one_pipe_twist_by_its_sign`, `test_a_shape_of_two_solids_is_refused_naming_the_count`, `test_an_invalid_solid_is_refused_before_its_volume_is_read`, `test_a_thread_wrong_by_a_part_in_ten_thousand_is_refused_on_the_thread_not_the_whole` (11 passed, 32 deselected). |
| 4 | SC4: The one helical builder is proven on a bare rod and a bare void against the closed form; a sample in `make verify`, the full grid in a slower tier | VERIFIED | `test_the_void_a_nut_will_subtract_passes_the_gate` green now. `tests/test_grid.py`: 60 cells collected by `-m grid`, 6 governance tests selected by default (`addopts ... -m 'not grid'`, `pyproject.toml:115`); `tests/test_grid.py` + `tests/test_bench.py`: 455 passed, 60 deselected. `grid.yml`: `workflow_dispatch` plus weekly `schedule`, `permissions: contents: read`, no `pull_request`/`push`; `ci.yml` and `required-jobs.txt` do not name it (`scripts/pr_land.py:53-55` pins the gating workflow). The full 7160-row run on a GitHub runner happened: run 38240380994 (ref main at 57d05c6, 15 of 15 shards green), recorded in `bench/RESULTS.md`, accepted by the owner in UAT test 10 (slowest shard M20 29:03 of job wall against `timeout-minutes: 120`). |
| 5 | Goal clause: a build the postcondition rejects never reaches a cache, a preview or a download | VERIFIED | `app.py:_serve`: `_EXPORTS.put(raw_key, raw)` runs only after `await backend(...)` returns; `BuildError` goes to a 422 `build_error` and skips it. `lru_cache` stores only returns (probe: `currsize` 0 after two refusals). `_write_export` refuses a bad STL header, `exportStl` False and a non-`RetDone` STEP status as `BuildError`. |
| 6 | 03-02: pitch at or above the root-radius bound is a 422 `pitch_too_coarse` naming d and pitch; more than 250 turns (exact decimals) is a 422 `turn_cap`; neither reaches the kernel | VERIFIED | API: `pitch=5.6` 422 `pitch_too_coarse`, `ctx.fields ["d","pitch"]`, "largest pitch ... 5.54256"; `length=1500&thread_length=1500` 422 `turn_cap`, `ctx.fields ["thread_length","length","pitch"]` (the Phase 4 form of the cap: it reads the built thread, `calc/thread.py:turn_cap_refusal`). CLI: the same inputs exit 2 with `error: d and pitch:` / `error: thread_length, length and pitch:`. Validators are `params.py:_root_radius`, `_turn_cap`. |
| 7 | 03-02: the info document describes the thread (rows, closed-form volume, standing warning first) | VERIFIED | `GET /api/bolt/info` 200 (2306 bytes), `left_hand=true` variant 200; first warning "plain-cut thread ends, no tip chamfer or under-head fillet; not a product build" (the Phase 4 wording of the standing warning; Phase 3 wrote "threaded rod ... no head"; same slot, same intent, UAT test 1 records the deviation). `screw info bolt --left-hand` prints the document. `calc/thread.py` carries the closed form; no kernel `Volume()` feeds a printed number. |
| 8 | 03-03: the fine STL at an L11-measured row above its cap is a 422 `fine_stl_cap` before the cache, slot and pool, on API and CLI; off-row parts and preview/STEP are served; the info document warns | VERIFIED | `_serve` calls `download_refusal` first (`app.py:462`), `cli.py:156` likewise. d=8, pitch=1.25, length=thread_length=67.6: fine STL 422 naming the cap 67.5 mm, 54 turns, run `2026-10-08-a-grid`; preview 200 (4,680,584 bytes); CLI exit 2, no file written. Thirteen `FINE_STL_ROWS` keyed by `(d, pitch, left_hand)` (`calc/thread.py`). The old WR-02 caveat is gone: `fine_stl_refusal` takes `left_hand`, and left-hand M10 x 60 mm now serves a fine STL (200, 37,578,284 bytes) where the right-hand cap is 56 mm. |
| 9 | 03-04: `left_hand` on every kind, `BooleanOptionalAction` flag, filenames tell the hands apart, repeated keys and flags refused | VERIFIED | `cli.py:36-71` `_Once`/`_OnceBool`; `?d=8&d=9` 422 `duplicate` at `["query","d"]`; CLI repeated flags exit 2 naming the flag (`--left-hand/--no-left-hand was given more than once`); `slug()` iterates every model field so the hand is in the filename. |
| 10 | 03-05: left-hand checkbox in a Thread fieldset, `read()`/`write()` round trip through the hash, Reset unchecks, built from `/api/schema` alone | VERIFIED (owner-run in a browser) | `app.js:103` `prop.type === 'boolean'` branch builds `input.type = 'checkbox'`; `:41` comment pins that the link carries `left_hand=true` and nothing else when checked. UAT tests 3, 4 and 5 (2026-10-13): page loads, checkbox at natural width in both themes, mesh reverses hand, hash and reload and Reset and Copy link behave. |
| 11 | 03-05: a link with a foreign, repeated or unreadable key is refused whole and builds nothing | VERIFIED (owner-run in a browser) | `app.js:236 refuseLink`; callers at `:265` (repeated), `:271/:289` (unknown kind/field), `:302` (unreadable value). UAT test 6: all six links (`#d=8&m=5`, `#d=1&d=2`, `#kind=bolt&kind=bolt`, `#left_hand=banana`, `#d=abc`, `#d=`) refused naming the key, `/#d=8` opens. The `#d=abc`/`#d=` browser-sanitisation assumption is now run, not assumed. |
| 12 | 03-05: after a failed update or refused link, the warnings of the mesh on screen stay visible | VERIFIED (owner-run in a browser) | `pendingWarnings`/`meshWarnings` (`app.js:31-32`, set at `:379`, promoted to the mesh at `:576`); `mesh ? meshWarnings : []` at `:244`, `:454`, `:603`. UAT test 7 pass. UAT test 4's old twin (status line after a refused link) was ruled by the owner on 2026-10-11: keep the empty status line. |
| 13 | 03-06: spike imports the shipped code back; protocol still pre-registered; the grid tier is isolated from `ci.yml` and the required jobs | VERIFIED | `tests/test_bench.py` and `tests/test_grid.py` governance tests green now (455 passed, 60 deselected); UAT tests 27 to 29. |
| 14 | 03-07: L12 recorded; docs describe the threaded part; INTERIM register lists the new knobs; retired items name fix shas; coverage floor re-measured | VERIFIED (with an observation) | `## L12` at `decision_log.md:428`; owner read it on 2026-10-13 (UAT test 11, lines 428-538). `fail_under = 96` (`pyproject.toml:140`); orchestrator's `make test` on HEAD: 2637 passed in 68.85 s, coverage 97.33 % against the 96.0 floor. The four items 03-07 retired name fix shas that are not reachable from `main` (see Observations). |

**Score:** 14/14 truths verified (0 present, behavior-unverified).

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|--------------|----------|
| 1 | A left-hand pair proven by the same checks as a right-hand pair (THRD-02 second clause) | Phase 5 | Phase 5 SC3 and PAIR-03; REQUIREMENTS.md line 15 now says so in the requirement text |
| 2 | Root radii between 0 and about 3e-5 mm pass validation and then fail in the kernel with a generic message (WR-04); d=100, length=200 at default pitch exceeds both interim backstops (WR-05) | Phase 7 | Phase 7 SC3 (OPER-03); both active in `docs/tech_debt/INDEX.md`, Severity must; WR-05 ruled "stays must under D-18" by the owner |

### Review findings, state now

| Finding | Severity | State on `main` |
|---------|----------|-----------------|
| WR-02 fine-STL cap ignored `left_hand` | must | Resolved in Phase 4 (plan 04-02). `FINE_STL_ROWS` is keyed by hand; verified above by a left-hand M10 x 60 mm fine STL serving 200 |
| IN-01 `info` printed turns and volume for a length below `MIN_TAIL_MM` | nice | Resolved in Phase 4 (plan 04-05) |
| WR-04 root radius floor is not the kernel boundary | must | Active; Phase 7 SC3. The gate holds: nothing wrong is served |
| WR-05 d=100, length=200 exceeds both interim backstops | must | Active; owner ruling 2026-10-11 keeps it `must`, trigger Phase 7 re-sweep. I did not re-run the 53 s / 9 GiB measurement |
| IN-03 `check_solid` ignores the estimator's error estimate | nice | Active |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/screw/calc/thread.py` | kernel-free profile maths, `T_GATE`, `volume_check`, caps, refusals | VERIFIED | No `cadquery`/`OCP` import; `lint-imports`: 9 contracts kept, 0 broken |
| `src/screw/solid/helical.py` | the one builder, tail fold, `MIN_TAIL_MM` guard, `left_hand` to `makeHelix(lefthand=)` | VERIFIED | Used by `bolt.thread`, bench and grid |
| `src/screw/solid/bolt.py` | `thread(p)` over `helical.thread(..., left_hand=p.left_hand)`; `assemble` fuses shank and head | VERIFIED | `_build` calls both |
| `src/screw/solid/__init__.py` | `precise_volume`, `check_solid`, export checks, gate inside the cache | VERIFIED | `:166-168` |
| `src/screw/params.py` | `left_hand`, root-radius, turn-cap validators | VERIFIED | `PydanticCustomError` with `ctx.fields` |
| `src/screw/static/app.js`, `style.css` | checkbox branch, link refusals, per-mesh warnings | VERIFIED | source above plus owner's browser run |
| `.github/workflows/grid.yml`, `Makefile grid`, `pyproject.toml` marker | slow tier | VERIFIED | run 38240380994 recorded |
| `docs/architecture/decision_log.md` L12 | what later phases build on | VERIFIED | present, owner-read |

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| `solid/__init__._build` | `calc.thread.volume_check` / `closed_volume` / `bolt_closed_volume` | `check_solid(..., closed)` twice | WIRED |
| `solid/__init__._build` | `bolt.thread` -> `helical.thread` | direct call | WIRED |
| `lru_cache` | `_build_checked` | gate raises inside the wrapped function | WIRED (probe: `currsize` 0 after two refusals) |
| `params` validators | `calc.thread` | lazy import in each `model_validator` | WIRED |
| `app._serve` / `cli.cmd_export` | `calc.download_refusal` | first statement, before cache / kernel | WIRED |
| `bolt.thread` | `helical.thread(left_hand=)` -> `makeHelix(lefthand=)` | field to builder | WIRED (hands differ in STL on API and CLI) |
| `cli._add_args` | `_OnceBool` / `_Once` | `annotation is bool` | WIRED |
| `app` | `refuse_explicit_conflict` and repeated-key dependency | route dependencies | WIRED |
| `app.js update()` | `showModel` / `meshWarnings` | `meshWarnings = pendingWarnings` at `:576` | WIRED |
| `grid.yml` | `make grid` | matrix `SIZE` | WIRED (run recorded) |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Real data | Status |
|----------|---------------|--------|-----------|--------|
| info document `volume`, `turns` | `closed_volume`, `turns_of` | closed-form maths from `p.d`, `p.pitch`, `p.length`, `p.thread_length` | yes | FLOWING |
| STL / STEP bytes | `export(p, fmt, quality)` | `_build_cached` -> `bolt.thread` + `assemble` -> kernel | yes (1.58 MB preview STL, STEP re-export 1.19 MB) | FLOWING |
| page warnings | `info.warnings` | `/api/bolt/info` | yes | FLOWING (rendering run by owner) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Gate, hand and void tests | `pytest tests/test_solid.py -k "hand_decides or naive_sweep or inverted_one_pipe or two_solids or invalid_solid or thread_wrong_by or left_hand_rod_exports or void_a_nut" --no-cov` | 11 passed, 32 deselected | PASS |
| Grid and bench governance | `pytest tests/test_grid.py tests/test_bench.py --no-cov` | 455 passed, 60 deselected | PASS |
| Grid cells exist | `pytest tests/test_grid.py -m grid --collect-only` | 60 of 66 collected | PASS |
| Import contracts | `lint-imports` | 9 kept, 0 broken | PASS |
| Gate refuses a wrong thread, never caches | cylinder via `bolt.thread`, two builds, `cache_info()` | two `BuildError`, `currsize` 0 | PASS |
| API probes | TestClient, inline backend, 14 requests | 200s and 422s as listed in truths 1 to 9, no 500 | PASS |
| CLI probes | `.venv/bin/screw export / info bolt` over 9 invocations | exit 0 for builds, exit 2 with the field named for refusals, no file for the capped fine STL | PASS |
| Whole suite | `make test` (orchestrator, HEAD 04b5c50) | 2637 passed in 68.85 s, coverage 97.33 % (floor 96.0) | PASS (cited, not re-run) |

### Probe Execution

None declared by the plans; no `scripts/*/tests/probe-*.sh` exist. Skipped.

### Requirements Coverage

| Requirement | Source plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| THRD-01 | 03-01, 03-02, 03-03, 03-06, 03-07 | Every threaded part carries a real helical ISO metric thread, no cosmetic option | SATISFIED | truths 1, 6 to 8; `section()` matches the pinned P/8 crest, P/4 root, 5H/8 depth; kernel volume agrees with the independent closed form to 5e-08 |
| THRD-02 | 03-04, 03-05, 03-07 | `left_hand` boolean, default right; a left-hand pair proven like a right-hand pair | SATISFIED for Phase 3's scope; second clause is Phase 5 PAIR-03 | truths 2, 9, 10; REQUIREMENTS.md line 15 now carries the annotation (owner ruling 2026-10-11) |
| THRD-04 | 03-01, 03-06, 03-07 | Every thread build gated; failure is a `BuildError`, never cached or served; positive control | SATISFIED | truths 3, 5 |

Cross-reference: the seven PLAN `requirements` fields declare exactly THRD-01, THRD-02, THRD-04 (03-01: 01+04; 03-02, 03-03: 01; 03-04, 03-05: 02; 03-06: 01+04; 03-07: all three). The SUMMARY `requirements-completed` fields match. ROADMAP's Phase 3 line lists the same three, and REQUIREMENTS.md's traceability table maps those three, and only those three, to Phase 3 (THRD-03 is Phase 4, THRD-05 is Phase 5). Every ID accounted for; no orphans; nothing claimed that REQUIREMENTS.md does not map here.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `AGENTS.md` (symlinked as `CLAUDE.md`) | 16 | "**Walking skeleton** (Phase 1): the `bolt` kind is a plain unthreaded cylinder ..." | Warning | The standing brief every agent reads is false since Phase 3 (and since Phase 4 the default is a hex screw). 03-07 left it for the owner; two phases later it is still there. Documentation, not a goal failure |
| `compose.yaml` | 18 | "the skeleton is lighter" in the `mem_limit` comment | Info | Stale; WR-05's item records the real exposure |
| `src/screw/params.py` | 18-31 | `INTERIM_MAX_MM` comment says the bound keeps one valid request under `mem_limit`, then says the figures do not carry to a thread | Warning | Premise known false; correction sits in WR-05's next step (Phase 7) |

No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`NotImplemented` in the phase's code files (grep over solid, calc/thread, params, cli, app, app.js came back empty). No stubs, empty handlers or hardcoded empty data in the touched source.

### Prohibitions

| Prohibition | Tier | Verdict |
|-------------|------|---------|
| 03-01: never serve, cache or export a refused build; never loosen `T_GATE`, use bare `Volume()` or drop the sign | test | Not violated: positive controls pass now, my probe, `T_GATE = 9e-05` (L11), `Volume()` only in a docstring, sign kept (`{rel:+.3e}`) |
| 03-01: no fallback to an unthreaded solid; no end chamfer | judgment | Judged not violated (non-authoritative LLM verdict): `_build_checked` re-raises as `BuildError`; ends are plain planar cuts (`bolt.py` docstring, D-01/D-02). Human review recommended |
| 03-02: no trimming or clamping of length/pitch; no number the profile does not give | test / judgment | Not violated: both are 422s. Judgment half non-authoritative |
| 03-03: no shortening, coarser mesh or nearest-row mapping | test | Not violated: off-row parts have no cap; preview and STEP served as asked |
| 03-04: no wrong hand on any front end; default hand never moves | test | Not violated (hand test, STL difference on API and CLI, literal pinned) |
| 03-05: no hash key dropped or defaulted; no hidden mesh warnings | test | Present in source and pinned; owner ran the browser checks 2026-10-13 |
| 03-06: grid not narrowed, not required, no timing assertion in `make verify` | test | Not violated (60 cells, governance tests green) |
| 03-07: no number in L12 or the register that no run measured | judgment | Not exhaustively checked by me; the owner read L12 on 2026-10-13 and passed it. Flagged unverified-prohibition for the record, no open human item |

### Human Verification Required

None open. The earlier report's seven human items are closed in 03-UAT.md (tests 1 to 7 of the first UAT on 2026-10-11, restarted 2026-10-13 with 33 passed, 0 issues): checkbox and hand (tests 4, 5), link refusals (6), per-mesh warnings (7), 01-UI-SPEC read (8), the refused-link status line (owner keeps it empty), the first grid run (10, run 38240380994), the WR-05 severity ruling (stays `must`) and the THRD-02 bookkeeping ruling (tick kept, requirement annotated). I found no contradiction between those verdicts and the code.

### Observations (not Phase 3 gaps)

- `Resolved in:` shas in `docs/tech_debt/resolved/` (05fb4ed, 909dec3, de9304e, eaaac85, cfe00a4 on local branches; ef37f23, 0e2f437 on none) cite pre-squash commits that `main` cannot reach, because PR #10 squash-merged as 66d9393. The owner accepted this on 2026-10-13 (UAT test 9). It also means UAT test 32's "reachable from HEAD" wording was true when written and is not true on `main` now. A docs-record issue; no code is affected.
- UAT test 1 records that the cold-start expected text (threaded-rod warning first) is Phase 3's and the app now says the Phase 4 wording. Same slot, same intent.
- Two Phase 3 behaviours changed shape under Phase 4 and still hold: the turn cap reads the built thread (`thread_length`, `length`, `pitch`) and the bare thread is gated separately before the fuse. Both are stronger than what Phase 3 shipped, not weaker.

### Gaps Summary

No roadmap success criterion failed and no must-have truth is FAILED, so there is no `gaps:` block. The only items left are deferred by design (THRD-02 second clause to Phase 5; WR-04 and WR-05 to Phase 7) and two documentation warnings (the stale `AGENTS.md` line 16 brief, the `params.py` interim comment). I would still fix `AGENTS.md:16` soon, because every agent reads it first and it now describes a product that no longer exists.

### Digest refresh (2026-10-13, PR #13 review)

One covered file changed after the verifier ran: `docs/architecture/decision_log.md` gained L11's additive "Escape clause, revision direction" paragraph (`b4f9a96`, the Phase 5 roadmap revision). L12 and every L11 value this report cites are unchanged; `covered_digest` is recomputed with `verification.fingerprint` over the same 36 files.

---

_Verified: 2026-10-13T13:45:00Z_
_Verifier: Claude (gsd-verifier)_
