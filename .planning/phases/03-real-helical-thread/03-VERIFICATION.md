---
phase: 03-real-helical-thread
verified: 2026-10-11T10:00:00Z
status: passed
score: 11/14 must-haves verified
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
covered_digest: "v3:sha256:f820b2879a8e2fa33ac45965bd0fbd9ae90e978fc2aae3d4f43989c64338d668"
behavior_unverified: 3
overrides_applied: 0
re_verification: false
deferred:
  - truth: "A left-hand pair is proven by the same checks as a right-hand pair (second clause of THRD-02)"
    addressed_in: "Phase 5"
    evidence: "Phase 5 SC3: 'right- and left-hand pairs go through the same checks' (PAIR-03); no nut exists before TYPE-03, so a pair cannot be built in Phase 3"
  - truth: "Every allowed configuration builds inside the timeout, or is capped/refused with a 422 naming the fields (root radii between 0 and about 1e-4 mm that pass validation and then fail in the kernel, WR-04; d=100, length=200 at default pitch exceeding both interim backstops, WR-05)"
    addressed_in: "Phase 7"
    evidence: "Phase 7 SC3: 'a configuration that cannot is capped and warned or refused with a 422 naming the fields, never silently shortened' (OPER-03); recorded in docs/tech_debt/active/2026-10-11-root-radius-floor-is-not-the-kernel-boundary.md and 2026-10-11-default-pitch-d100-length200-exceeds-both-interim-backstops.md. The WR-05 severity ruling is still the owner's (see human_verification item 6)."
behavior_unverified_items:
  - truth: "The form shows a Left-hand thread checkbox after Size; checking it writes left_hand=true to the hash and the query and rebuilds with the preview's thread visibly changing hand; unchecking removes the key; #left_hand=true opens checked; Reset unchecks (plan 03-05)"
    test: "make serve, open http://127.0.0.1:8000/ in light then dark theme; toggle the box; reload with #left_hand=true; Reset; Copy link into a new tab"
    expected: "Checkbox at natural width; the mesh winds the other way after the 350 ms debounce; the hash reads #left_hand=true only while checked"
    why_human: "Only source text of app.js is pinned (tests/test_parity.py); rendering, the checkbox input event and the hand of a mesh need a browser (L01)"
  - truth: "A link with a foreign, repeated or unreadable key (#d=8&m=5, #d=1&d=2, #kind=bolt&kind=bolt, #left_hand=banana, #d=abc, and now #d=) is refused whole, names the key, clears the form, disables downloads and builds nothing (plan 03-05, WR-01 fix e48b8ac)"
    test: "Open each link one at a time, then /#d=8"
    expected: "Each of the six refuses with a sentence naming the key (and the value where unreadable), empty form and panel, downloads disabled, URL not rewritten; /#d=8 opens the M8 part"
    why_human: "#d=abc and #d= depend on HTML number-input value sanitisation returning '' (the debt item's ASSUMPTION, never run in a browser); the WR-01 change is a source-text pin only"
  - truth: "After a failed update (422, gate build_error on the STL after its info rendered, network error) or a refused link, the warnings of the mesh on screen stay visible below the error paragraphs (plan 03-05, D-11)"
    test: "Open the default part; set pitch=6; then d=0.001, pitch=0.0001, length=0.01; then stop the server and edit a field"
    expected: "Last valid mesh stays, status reads 'Showing the last valid part', the error paragraph shows (Diameter and Pitch marked invalid for the 422), and below it the threaded-rod warning"
    why_human: "The interleaving of the info and STL fetches is observable only in a running page. I confirmed server-side that d=0.001, pitch=0.0001, length=0.01 is a 422 build_error (+9.858e-03, refused by the gate), so the precondition of this scenario holds"
human_verification:
  - test: "Left-hand checkbox and thread hand in a browser (03-05 human-check 1)"
    expected: "See behavior_unverified_items[0]"
    why_human: "No browser in the gate (L01)"
  - test: "Link refusals in a browser (03-05 human-check 2), plus /#d= added by the WR-01 fix"
    expected: "See behavior_unverified_items[1]"
    why_human: "HTML number-input sanitisation is browser behaviour"
  - test: "Per-mesh warnings after a failed update (03-05 human-check 3)"
    expected: "See behavior_unverified_items[2]"
    why_human: "Fetch interleaving is observable only in a running page"
  - test: "Status text after a refused link while a mesh is still on screen (03-05 SUMMARY human item 4)"
    expected: "The owner says whether the status line should read 'Showing the last valid part' there. Today it is empty and the mesh's warnings show (form cleared, mesh not editable)"
    why_human: "A UX decision, not a defect a test can judge"
  - test: "First workflow_dispatch of .github/workflows/grid.yml after merge (15 size shards, 7160 rows)"
    expected: "Every shard green; record per-size GitHub-runner wall time in bench/RESULTS.md. Until then timeout-minutes: 120 is an unmeasured guess (03-06) and the full corpus has not run on a CI runner. Locally I ran one cell (M2-left-void) green in 81 s; 03-06 recorded the M3.5 and M4 shards"
    why_human: "Needs GitHub Actions after the PR merges"
  - test: "Owner severity ruling on WR-05 (docs/tech_debt/active/2026-10-11-default-pitch-d100-length200-exceeds-both-interim-backstops.md)"
    expected: "Keep Severity must under D-18, or re-tag blocker. AGENTS.md says a blocker is fixed now or surfaced and waited on. A single GET /api/bolt/model.stl?d=100&length=200 is a valid, in-cap, default-pitch request that the review measured at 53.3 s, 9143 MiB peak RSS, 1.3 GB fine STL against a 30 s timeout and a 4g mem_limit"
    why_human: "A severity ruling is the owner's; the item is open and deferred, not resolved"
  - test: "Owner ruling on THRD-02 bookkeeping (REQUIREMENTS.md line 15 is ticked [x] and traceability says Complete)"
    expected: "Either annotate the requirement so the second clause visibly points at PAIR-03 / Phase 5, or untick and re-tick at Phase 5. See Requirements Coverage for why this report treats Phase 3's THRD-02 scope as met"
    why_human: "Editing the requirement's text or status is the owner's call"
---

# Phase 3: Real Helical Thread Verification Report

**Phase Goal:** A user who sets `d`, `pitch` and `length` in explicit millimetres gets a bolt-kind solid carrying a real ISO 68-1 helical thread, right- or left-hand, on all three front ends, and a build the postcondition rejects never reaches a cache, a preview or a download.
**Verified:** 2026-10-11T10:00:00Z
**Status:** human_needed
**Re-verification:** No, initial verification
**HEAD:** 6fdb403 on `gsd/phase-03-real-helical-thread`; working tree clean apart from untracked `.DS_Store` and `.planning/ui-reviews/`.

## Verdict in one paragraph

The goal is achieved in the code. I rebuilt the default part, both hands, the void and a deliberately wrong rod myself, and exercised the CLI and the HTTP API directly. Nothing in the roadmap contract failed. The remaining work is human: three UI truths are pinned as source text only (no browser in the gate, L01), one UX decision, the first CI run of the slow grid, and two owner rulings. Five code-review findings are deferred by the owner into filed debt items; I list them as recorded gaps, none of which negates a roadmap success criterion. One of them (WR-05) is an availability exposure whose severity ruling is still open.

MVP-mode note: ROADMAP.md marks Phase 3 `Mode: mvp`, but the goal is not written as "As a ..., I want to ..., so that ...", and `user-story.validate` returns `valid: false`. I did not refuse. The orchestrator asked for verification explicitly, Phases 1 and 2 carry the same shape, and a User Flow Coverage table would have been invented. I used standard goal-backward verification. The owner may want to drop the `mvp` tag from Phase 3 or rewrite its goal.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: Preview, STL and STEP on UI, API and CLI carry the modelled L11 helical thread with the pinned ISO 68-1:2023 basic profile; the skeleton's plain solid is gone and there is no cosmetic or unthreaded option | VERIFIED | `solid.build(BoltParams())`: 1 solid, valid, precise volume 459.1440814 vs closed form 459.1440810 (rel +9.71e-10, gate 9e-05), 18.8 % below the old cylinder, default `Volume()` 459.1435 (not used by the gate). `screw export bolt` wrote 1,578,084-byte preview STL and 1,166,017-byte STEP (exit 0). API `model.stl?quality=preview` 200, 31,560 facets, header count matches byte length. STEP re-imported (M10x1.5x30, left-hand): 1 solid, rel -3.05e-07. `grep -i 'cosmetic\|unthreaded\|cylinder' src/` finds only a comment in `params.py` about the old F1 measurement. The UI fetches the same `model.stl?quality=preview` route; how the page renders it is human item 1. |
| 2 | SC2: `left_hand: true` (default false) gives a left-hand thread that passes the same postcondition across the tested grid; parity test green with the new field | VERIFIED | Field on `FastenerParams` base, `type: boolean`, default False, group Thread, schema order `d, pitch, left_hand, length`. `isInside` probe at r = rr + 0.8(ro - rr), z = 2.25P: right reads (True, False) at (+theta, -theta), left reads (False, True); same at the tail (z 18.25). Both hands: 1 solid, valid, rel +9.71e-10 at M6x20. Left STL differs from right STL on CLI and API. `?left_hand=banana` is 422 `bool_parsing` at `["query","left_hand"]`; `--left-hand --left-hand` and `--left-hand --no-left-hand` exit 2. Parity test in `make verify`. Grid has both hands: I ran `pytest -m grid -k M2-left-void` (80 s, 1 passed). Mutation: I made the tail segment drop `left_hand` in-process and `test_the_hand_decides...` failed at z 18.25 (`(True, False) == (False, True)`); unmutated it passes. |
| 3 | SC3: Every build is checked before it is cached or served (valid, exactly one solid, signed precise volume within tolerance, never bare `Volume()`); failure is a `BuildError` naming the check; a positive control feeds the gate a known-bad build | VERIFIED | `check_solid` runs inside `_build`, the function `lru_cache` wraps (`solid/__init__.py:115-140`); order solid count, `isValid()`, `volume_check` (`not abs(rel) <= T_GATE`, NaN-safe, signed). My control: `bolt.rod` replaced with a cylinder, `build()` twice raised `BuildError` "wrong solid ... relative error -1.222e-01", `cache_info()` `currsize=0, misses=2`. Via the API the same substitution gave 422 `build_error` on `model.stl` and `model.step`. Gate refused a real build too: `d=0.001&pitch=0.0001&length=0.01` is 422 at +9.858e-03. Export checks (`exportStl` False, STEP status, STL header) in `_write_export`. |
| 4 | SC4: The one helical builder is proven on a bare rod and a bare void against the closed form; a sample in `make verify`, the full grid in a slower tier | VERIFIED | `helical.thread(6, 1, 20, clearance=0.20)` passes `check_solid` against `closed_volume(6,1,20,0.20)` (rel +9.2e-08). `tests/test_grid.py`: 60 grid-marked cells (15 sizes x 2 hands x rod/void) deselected by default (`addopts ... -m 'not grid'`), 6 governance tests in `make verify`; the corpus-size test pins 7160 rows. `grid.yml`: `workflow_dispatch` + weekly cron, `permissions: contents: read`, no `pull_request` or `push`; `grid` appears in neither `ci.yml` nor `required-jobs.txt`. Import-back holds: `bench...helical.thread is screw.solid.helical.thread`, `maths.closed_volume is calc.thread.closed_volume`, `measure.precise_volume is solid.precise_volume`. The full 7160-row run on a CI runner has not happened (human item 5). |
| 5 | Goal clause: a build the postcondition rejects never reaches a cache, a preview or a download | VERIFIED | `_serve` (`app.py:403-470`): `_EXPORTS.put(raw_key, raw)` runs only after `await backend(...)` returns; `BuildError` goes to a 422 and skips it. `lru_cache` stores only returns. Probe above: two consecutive refusals, `currsize` 0, API 422 on STL and STEP. |
| 6 | 03-02: pitch at or above the root-radius bound is a 422 `pitch_too_coarse` naming d and pitch; more than 250 turns (exact decimals) is a 422 `turn_cap`; neither reaches the kernel; includes CR-01 (tiny pitch) | VERIFIED | API: `pitch=5.6` 422 `pitch_too_coarse`; `pitch=1e300` 422; `length=1500` 422 `turn_cap`; `pitch=5e-324` 422 `turn_cap` "inf turns" (no 500). CLI: the same inputs exit 2 with `error: d and pitch:` / `error: length and pitch:`. `pitch=5.54` (inside the bound) builds. 9 CR-01 tests exist per REVIEW-FIX; the fix is `turns_of` returning `math.inf` on `OverflowError`. WR-03: the printed largest pitch for d=6 is 5.54256 and 5.54 builds; the sweep test over 1999 diameters is in the suite. |
| 7 | 03-02: info document rows d, pitch, length, turns, volume, thread_depth, minor_diameter in fixed order; volume is the closed form; first warning is the threaded-rod warning | VERIFIED | `screw info bolt` and `GET /api/bolt/info` both print rows in that order, volume 459.14408096158724 (closed form), labels "ISO 68-1:2023 basic profile", warning `threaded rod: no head, plain-cut thread ends; not a product build`. `grep Volume() src/` finds only two comments. |
| 8 | 03-03: the fine STL at an L11-measured row above its cap is a 422 `fine_stl_cap` before the cache, slot and pool, on API and CLI; off-row parts and preview/STEP are served; the info document warns first | VERIFIED (right-hand rows; see Recorded gaps for the left-hand caveat) | `download_refusal` is the first statement in `_serve` and in `cmd_export` before the kernel import. Probe d=8, pitch=1.25, length=67.6: fine STL 422 naming `length`, 67.5 mm, 54 turns, run `2026-10-08-a-grid`; preview 200 (4.68 MB); CLI exit 2 with no file, `--quality preview` writes the file and repeats the refusal as a warning; `info` carries the same sentence as its second warning. Seven rows in `FINE_STL_ROWS` match L11's list. |
| 9 | 03-04: `left_hand` on every kind, `BooleanOptionalAction` flag, filenames tell the hands apart, repeated keys and flags refused | VERIFIED | Download name `bolt_d6_pitch1_left_hand0_length20.step`. `?d=0&d=5` 422 `duplicate` at `["query","d"]`. CLI `--d 5 --d 6`, `--left-hand --left-hand`, `--left-hand --no-left-hand` exit 2 naming the flag. `info`/`export --help` list `--left-hand | --no-left-hand` in model order. |
| 10 | 03-05: left-hand checkbox in a Thread fieldset, `read()`/`write()` round trip through the hash, Reset unchecks, built from `/api/schema` alone | PRESENT_BEHAVIOR_UNVERIFIED | `app.js:30-34` `read`/`write`, `:82` `prop.type === 'boolean'` branch, `:194-196` `partQuery` writes only a checked box, schema supplies `type: boolean`. Pinned as source text in `tests/test_parity.py`; the checkbox's rendering, input event and the mesh visibly changing hand are not observable without a browser. Human item 1. |
| 11 | 03-05: a link with a foreign, repeated or unreadable key is refused whole and builds nothing | PRESENT_BEHAVIOR_UNVERIFIED | `app.js:148-152` repeated, `:164-169` foreign, `:176-182` unreadable (WR-01: the `given !== ''` exemption is gone, confirmed in the source); each calls `refuseLink`. `#d=abc` and `#d=` rest on browser value sanitisation, which the project has never run. Human item 2. |
| 12 | 03-05: after a failed update or refused link, the warnings of the mesh on screen stay visible | PRESENT_BEHAVIOR_UNVERIFIED | `pendingWarnings` / `meshWarnings` (`app.js:20-21, 245, 411`); `mesh ? meshWarnings : []` at 3+ call sites (`:130, 290, 437`). Fetch interleaving observable only in a running page. Human item 3. |
| 13 | 03-06: spike imports the shipped code back; protocol still pre-registered; grid tier is isolated from `ci.yml` and the required jobs | VERIFIED | Identity checks in truth 4; `tests/test_bench.py` and `tests/test_grid.py` governance tests pass in `make verify` (860 passed). |
| 14 | 03-07: L12 recorded; docs describe the threaded rod; INTERIM register lists the new knobs and costs; four retired items name fix shas; coverage floor re-measured | VERIFIED (with stale text noted) | `## L12` at `decision_log.md:412`; `fail_under = 96` and `make verify` printed "Required test coverage of 96.0% reached. Total coverage: 96.53%". `git grep` for the old skeleton phrases finds only `AGENTS.md:16` (deliberately left for the owner) and `compose.yaml:18` ("the skeleton is lighter", flagged by 03-07). L12's numbers were not each re-checked by me beyond the run-id citation count (21). |

**Score:** 11/14 truths verified (3 present and wired, behavior-unverified).

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|--------------|----------|
| 1 | A left-hand pair proven by the same checks as a right-hand pair (THRD-02 second clause) | Phase 5 | Phase 5 SC3 "right- and left-hand pairs go through the same checks"; PAIR-03. There is no nut before TYPE-03 |
| 2 | Root radii between 0 and about 1e-4 mm pass validation and then fail in the kernel with a generic message (WR-04); d=100, length=200 at default pitch exceeds both interim backstops (WR-05) | Phase 7 | Phase 7 SC3 (OPER-03): configurations that cannot build inside the timeout are capped and warned or refused with a 422 naming the fields. Filed: `docs/tech_debt/active/2026-10-11-root-radius-floor-is-not-the-kernel-boundary.md`, `...-default-pitch-d100-length200-exceeds-both-interim-backstops.md` |

### Recorded gaps (owner-deferred review findings, not `gaps:`)

I checked all five items exist, carry a severity and an INDEX row (`docs/tech_debt/INDEX.md` lines 19-23). I judged none of them to negate a roadmap success criterion; each is a boundary-honesty or backstop problem against L02/D-18 that the owner chose to defer on 2026-10-10.

| Finding | Severity | State | Why it matters |
|---------|----------|-------|----------------|
| WR-02 | must | active, needs a measurement or rule decision | `fine_stl_refusal` ignores `left_hand`. A left-hand M10 at 60 mm gets a 422 saying "L11 measured it over the export budget", but L11 measured it inside the budget (left-hand first-over is 73 mm). The refusal text also misstates the measured quantity (raw plus gzip, not the STL). This is a refusal of a part nobody measured as over, which D-02 says not to do. Not in a Phase 7 SC verbatim, so I did not mark it deferred to a phase. |
| WR-04 | must | active; Phase 7 SC3 | Root radius is accepted above 0, the kernel fails at about 3e-5 mm with "Geometry kernel failed (Standard_Failure); check d, pitch and length." The gate holds, nothing wrong is served. |
| WR-05 | must | active, owner severity ruling open | `d=100&length=200` default pitch: fine 53.3 s, 1.30 GB, peak RSS 9143 MiB (review's single run, macOS arm64, load 15). I did not re-run it. See human item 6. |
| IN-01 | nice | active | `info` prints turns and volume for `length=1e-9`, which `model.stl` refuses. |
| IN-03 | nice | active | `check_solid` ignores the volume estimator's error estimate (8.2e-7 at M6x20). |

The six fixed findings are confirmed in the tree, not only in REVIEW-FIX: CR-01 (`turns_of` catch, 422 reproduced for `pitch=5e-324` on API and CLI), WR-01 (`app.js:176-182` no `given !== ''`), WR-03 (5.54256, builds at 5.54), WR-06 (mutation above), IN-02 (`request_id` comment above `request_id`, `app.py:406`), IN-04 (commits present). Commits `c28de09 e48b8ac 78cc346 7799d2b cca06d3 aef047d` are ancestors of HEAD.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/screw/calc/thread.py` | kernel-free profile maths, `T_GATE`, `volume_check`, caps, refusals | VERIFIED | 72 stmts, no cadquery import; used by params, calc, solid |
| `src/screw/solid/helical.py` | the one builder with tail fold and `MIN_TAIL_MM` guard | VERIFIED | 100 % covered; used by `bolt.rod`, bench, grid |
| `src/screw/solid/bolt.py` | `rod(p)` over `helical.thread(..., left_hand=p.left_hand)` | VERIFIED | `_build` dispatches `BoltParams` to `bolt.rod` |
| `src/screw/solid/__init__.py` | `precise_volume`, `check_solid`, export checks | VERIFIED | gate inside the `lru_cache`d function |
| `src/screw/params.py` | `left_hand`, root-radius and turn-cap validators | VERIFIED | `PydanticCustomError` with `ctx.fields` |
| `src/screw/static/app.js`, `style.css` | checkbox branch, read/write, link refusals, per-mesh warnings | VERIFIED present and wired; behavior unverified | truths 10-12 |
| `.github/workflows/grid.yml`, `Makefile grid`, `pyproject.toml` marker | slow tier | VERIFIED | not run end to end on CI |
| `docs/architecture/decision_log.md` L12 | what later phases build on | VERIFIED | present |
| `.planning/phases/01-.../01-UI-SPEC.md` | amended (D-19) | not re-read | tested only via the source pins in `test_parity.py` |

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| `solid/__init__._build` | `calc.thread.volume_check` / `closed_volume` | `check_solid(solid, closed)` | WIRED |
| `solid/__init__._build` | `bolt.rod` -> `helical.thread` | isinstance dispatch | WIRED |
| `lru_cache` | `_build_checked` | gate raises inside the wrapped function | WIRED (probe: currsize 0 after two refusals) |
| `params` validators | `calc.thread` | lazy import in each `model_validator` | WIRED |
| `app._serve` / `cli.cmd_export` | `calc.download_refusal` | first check, before cache / kernel import | WIRED |
| `bolt.rod` | `helical.thread(left_hand=)` -> `makeHelix(lefthand=)` | field to builder | WIRED (probe: hand flips) |
| `cli._add_args` | `BooleanOptionalAction` / `_Once` | `annotation is bool` | WIRED |
| `app` | `refuse_repeated_keys` | app-level dependency | WIRED |
| `app.js update()` | `showModel` / `meshWarnings` | `meshWarnings = pendingWarnings` at `:411` | WIRED (source) |
| `grid.yml` | `make grid` | matrix `SIZE` | WIRED (not yet dispatched) |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Real data | Status |
|----------|---------------|--------|-----------|--------|
| info document `volume`, `turns`, `thread_depth` | `closed_volume`, `turns_of`, `thread_depth` | closed-form maths from `p.d`, `p.pitch`, `p.length` | yes (459.144 for M6x20, not kernel `Volume()`) | FLOWING |
| STL / STEP bytes | `export(p, fmt, quality)` | `_build_cached` -> `bolt.rod` -> kernel | yes (31,560 facets; STEP re-imports to 1 solid) | FLOWING |
| page warnings | `info.warnings` | `/api/bolt/info` | yes (threaded-rod warning) | FLOWING (rendering unverified) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Whole gate | `make verify` | ruff, mypy `--strict`, import-linter, unfinished-work scan green; `860 passed in 36.70s`; coverage 96.53 % vs floor 96 | PASS |
| Default rod is the thread | in-process `solid.build(BoltParams())` | rel +9.71e-10, 18.8 % under the cylinder | PASS |
| Hand | `isInside` at +theta/-theta, base and tail | right (True,False), left (False,True) | PASS |
| Void | `helical.thread(6,1,20,clearance=0.2)` + `check_solid` | rel +9.2e-08 | PASS |
| Gate refuses wrong build, never caches | cylinder via `bolt.rod`, two builds, `cache_info()` | two `BuildError`, currsize 0 | PASS |
| API refusals | TestClient (inline backend) over 13 inputs | 422s with the expected `type`/`loc`; no 500 | PASS |
| CLI refusals | `.venv/bin/screw export bolt ...` over 8 inputs | exit 2 with named fields; no traceback | PASS |
| Tail-hand mutant | in-process patch of `helical.twist`, `pytest -k hand_decides` | fails at z 18.25 | PASS |
| One grid cell | `pytest -m grid --no-cov -k M2-left-void` | 1 passed in 81 s | PASS |
| Whole grid on CI | n/a | not run | SKIP (human item 5) |

### Probe Execution

None declared by the plans; no `scripts/*/tests/probe-*.sh` exist. Skipped.

### Requirements Coverage

| Requirement | Source plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| THRD-01 | 03-01, 03-02, 03-03, 03-06, 03-07 | Every threaded part carries a real helical ISO metric thread, no cosmetic option | SATISFIED | truths 1, 6-8; profile P/8 crest, P/4 root, 5H/8 depth in `section()` matches the Phase 2 pin; kernel volume agrees with the independent closed form to 1e-9 |
| THRD-02 | 03-04, 03-05, 03-07 | `left_hand` boolean, default right; a left-hand pair is proven by the same checks as a right-hand pair | SATISFIED for Phase 3's scope, second clause deferred to Phase 5 (see below) | truth 2, 9; Deferred item 1 |
| THRD-04 | 03-01, 03-06, 03-07 | Every thread build gated; failure is a `BuildError`, never cached or served; positive control | SATISFIED | truths 3, 5 |

Cross-reference: the plans declare exactly THRD-01, THRD-02, THRD-04 in their `requirements` fields, ROADMAP's Phase 3 line lists the same three, and REQUIREMENTS.md's traceability table maps those three, and only those three, to Phase 3. No orphaned requirement; nothing is claimed that REQUIREMENTS.md does not map here.

**THRD-02 judgment.** I count it complete for this phase, and the reasons are specific. (a) The second clause needs a nut, and TYPE-03 (the nut) and PAIR-03 (the pair check) are Phase 5; a "left-hand pair" cannot exist in Phase 3. (b) The clause says the pair is proven "by the same checks as a right-hand pair", and those checks do not exist yet for either hand, so the clause is unevaluable rather than failed. (c) Phase 3's own roadmap criterion for the field (SC2) is narrower and is met: same THRD-04 postcondition for both hands, plus an independent hand probe because the volume gate cannot see hand. (d) Phase 5 SC3 explicitly includes "right- and left-hand pairs go through the same checks", so the clause has a named home. What I do not accept is the unqualified `[x]` and "Complete" in REQUIREMENTS.md: on its literal text, THRD-02 is partial until Phase 5. I list the bookkeeping as an owner ruling (human item 7) and did not edit the file.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `AGENTS.md` (symlinked as `CLAUDE.md`) | 16 | "the `bolt` kind is a plain unthreaded cylinder ... Walking skeleton (Phase 1)" | Warning | The standing brief every agent reads is now false. 03-07 deliberately left it for the owner. |
| `compose.yaml` | 18 | "the skeleton is lighter" in the `mem_limit` comment | Info | Stale; the interim register states 7875 MiB for an in-cap fine STL. |
| `src/screw/params.py` | 18-31 | `INTERIM_MAX_MM` comment says the bound keeps one valid request under `mem_limit` | Warning | The comment itself now says the F1 numbers do not carry to a thread; WR-05 shows a valid request that exceeds it. Correction is in the WR-05 item's next step. |

No TBD/FIXME/XXX/TODO/HACK/NotImplementedError in the phase's code files (the project scan inside `make verify` agrees). No stubs: no `return null`, empty handler or hardcoded-empty data in the touched source. No debt marker lacks a reference.

### Prohibitions

| Prohibition | Tier | Verdict |
|-------------|------|---------|
| 03-01: never serve, cache or export a refused build; never loosen `T_GATE`, use bare `Volume()` or drop the sign | test | Not violated: positive controls and my probe; `T_GATE = 9e-05` is L11's value; sign kept (`{rel:+.3e}`) |
| 03-01: no fallback to an unthreaded solid; no end chamfer | judgment | Judged not violated (non-authoritative): `_build_checked` re-raises as `BuildError`; ends are plain planar cuts. Human review recommended |
| 03-02: no trimming or clamping of length/pitch; no number the profile does not give | test / judgment | Not violated: both are 422s. Judgment half non-authoritative |
| 03-03: no shortening, coarser mesh or nearest-row mapping | test | Not violated: off-row (8, 1.0) has no cap; preview and STEP served as asked. Note WR-02 |
| 03-04: no wrong hand on any front end; default hand never moves | test | Not violated (probes above; default literal pinned) |
| 03-05: no hash key dropped or defaulted; no hidden mesh warnings | test | Present in source and pinned; browser behavior unverified (truths 11-12) |
| 03-06: grid not narrowed, not required, no timing assertion in `make verify` | test | Not violated (7160 pin, governance tests) |
| 03-07: no number in L12 or the register that no run measured | judgment | Not exhaustively checked by me; citation count only. Flagged: unverified-prohibition, human review recommended |

### Human Verification Required

See `human_verification` in the frontmatter. In order: (1) left-hand checkbox and hand of the mesh, (2) the six refused links including `#d=`, (3) mesh warnings after failed updates, (4) status text after a refused link, (5) the first `grid.yml` dispatch, (6) the WR-05 severity ruling, (7) THRD-02 bookkeeping. Items 1 to 4 are the four `<human-check>` blocks of plan 03-05 as recorded in its SUMMARY; item 5 is from 03-06/03-07; I did not mark any of them passed.

### Gaps Summary

No roadmap success criterion failed and no must-have truth is FAILED, so there is no `gaps:` block for `/gsd-plan-phase --gaps`. The phase cannot be called `passed` because three truths are present and wired but only source-pinned (the page), and because the owner has open rulings (WR-05 severity, THRD-02 bookkeeping). The two items I would not let slide at the transition are WR-05, because AGENTS.md says a blocker is not merely filed, and the stale `AGENTS.md` line 16, because every agent reads it first.

---

_Verified: 2026-10-11T10:00:00Z_
_Verifier: Claude (gsd-verifier)_
