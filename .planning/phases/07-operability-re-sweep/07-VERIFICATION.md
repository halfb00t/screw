---
phase: 07-operability-re-sweep
verified: 2026-10-31T00:00:00Z
status: human_needed
score: 7/8 must-haves verified
covered_files:
  - .planning/phases/07-operability-re-sweep/07-01-PLAN.md
  - .planning/phases/07-operability-re-sweep/07-01-SUMMARY.md
  - .planning/phases/07-operability-re-sweep/07-02-PLAN.md
  - .planning/phases/07-operability-re-sweep/07-02-SUMMARY.md
  - .planning/phases/07-operability-re-sweep/07-03-PLAN.md
  - .planning/phases/07-operability-re-sweep/07-03-SUMMARY.md
  - .planning/phases/07-operability-re-sweep/07-04-PLAN.md
  - .planning/phases/07-operability-re-sweep/07-04-SUMMARY.md
  - .planning/phases/07-operability-re-sweep/07-05-PLAN.md
  - .planning/phases/07-operability-re-sweep/07-05-SUMMARY.md
  - .planning/phases/07-operability-re-sweep/07-06-PLAN.md
  - .planning/phases/07-operability-re-sweep/07-06-SUMMARY.md
  - .planning/phases/07-operability-re-sweep/07-07-PLAN.md
  - .planning/phases/07-operability-re-sweep/07-07-SUMMARY.md
  - .planning/phases/07-operability-re-sweep/07-08-PLAN.md
  - .planning/phases/07-operability-re-sweep/07-08-SUMMARY.md
  - .planning/phases/07-operability-re-sweep/07-09-PLAN.md
  - .planning/phases/07-operability-re-sweep/07-09-SUMMARY.md
  - .planning/phases/07-operability-re-sweep/07-10-PLAN.md
  - .planning/phases/07-operability-re-sweep/07-10-SUMMARY.md
  - .planning/phases/07-operability-re-sweep/07-11-PLAN.md
  - .planning/phases/07-operability-re-sweep/07-11-SUMMARY.md
  - .planning/phases/07-operability-re-sweep/07-12-PLAN.md
  - .planning/phases/07-operability-re-sweep/07-12-SUMMARY.md
  - .planning/phases/07-operability-re-sweep/07-13-PLAN.md
  - .planning/phases/07-operability-re-sweep/07-13-SUMMARY.md
  - .planning/phases/07-operability-re-sweep/07-14-PLAN.md
  - .planning/phases/07-operability-re-sweep/07-14-SUMMARY.md
  - .planning/phases/07-operability-re-sweep/07-15-PLAN.md
  - .planning/phases/07-operability-re-sweep/07-15-SUMMARY.md
  - .planning/phases/07-operability-re-sweep/07-16-PLAN.md
  - .planning/phases/07-operability-re-sweep/07-16-SUMMARY.md
  - .planning/phases/07-operability-re-sweep/07-17-PLAN.md
  - .planning/phases/07-operability-re-sweep/07-17-SUMMARY.md
  - .planning/phases/07-operability-re-sweep/07-18-PLAN.md
  - .planning/phases/07-operability-re-sweep/07-18-SUMMARY.md
  - .planning/phases/07-operability-re-sweep/07-19-PLAN.md
  - .planning/phases/07-operability-re-sweep/07-19-SUMMARY.md
  - .planning/phases/07-operability-re-sweep/07-20-PLAN.md
  - .planning/phases/07-operability-re-sweep/07-20-SUMMARY.md
  - .planning/phases/07-operability-re-sweep/07-21-PLAN.md
  - .planning/phases/07-operability-re-sweep/07-21-SUMMARY.md
  - Dockerfile
  - bench/results/phase-07/fit.json
  - bench/results/phase-07/runtime.json
  - compose.yaml
  - docs/architecture/decision_log.md
  - src/screw/app.py
  - src/screw/calc/cost.py
  - src/screw/cli.py
  - src/screw/params.py
  - src/screw/pool.py
covered_digest: "v3:sha256:4999e71b3fac23ca2ed7deba5e6aea2c574ee8941d47d6e066b7a7c7941714ed"
behavior_unverified: 1
overrides_applied: 1
overrides:
  - must_have: "Every allowed configuration builds inside the timeout; a configuration that cannot is capped and warned or refused with a 422 naming the fields (residual: parts inside the d / pitch walls that the kernel still refuses with a build_error)"
    reason: "Owner-accepted residual must debt docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md. Owner replies: 'File must debt, continue (Recommended)' (2026-10-28), 'Must debt, don't block (Recommended)' (G35, 2026-10-30), 'Rule nut W = 8, island to debt (Recommended)' (G36, 2026-10-30), 'Leave Pending, verify' (OPER-03). OPER-03 stays Pending in REQUIREMENTS.md."
    accepted_by: "owner (halfb00t)"
    accepted_at: "2026-10-30"
behavior_unverified_items:
  - truth: "A full-tier row whose cold wall x (1 + margin) reaches its timeout is re-read at 5 repetitions on 5 runner instances, and the verdict fails closed on an unread follow-up (R5, plan 07-19)"
    test: "Dispatch the operability full tier on a head where at least one point's cold wall x (1 + 0.5382691940004687) reaches its artifact timeout (or with a synthetic near-timeout point), and watch the followup-plan, followup and verdict jobs"
    expected: "followup-plan selects the point, followup reads it on 5 instances, verdict judges the max of the 5 and fails closed if one is unread; the run id is recorded in bench/RESULTS.md"
    why_human: "The follow-up job has never run on the runner. Runs 41161227951, 41162982938 and 41218613704 all skipped it because no point reached its margin (largest cold wall is 0.406 of timeout). The selection and judging code is pinned by synthetic-record tests (tests/test_oper_followup.py), which pass; the workflow wiring on real runners is unexercised. Debt: docs/tech_debt/active/2026-10-31-full-tier-follow-up-job-never-run-on-the-runner.md (nice)."
human_verification:
  - test: "Owner confirms Phase 7 closes with OPER-03 still Pending"
    expected: "Owner accepts that the ROADMAP goal 'every configuration a user is allowed to ask for builds inside the timeout, or is capped/warned/422' is met except for the residual in docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md (an admitted part can still get a 422 build_error that names no field), and that OPER-03 is carried to a later phase or the pre-release debt item"
    why_human: "The requirement as written (REQUIREMENTS.md OPER-03) is not met, by an already-given owner ruling. Closing the phase and what carries OPER-03 forward is the owner's call, not the verifier's."
  - test: "Owner decides whether the bolt fine-STL peak budget needs a guard before release"
    expected: "Either accept docs/tech_debt/active/2026-10-31-bolt-fine-peak-budget-above-the-worker-headroom.md as filed (bolt stl-fine peak budget 2,930,457,561 B vs worker headroom 1,830,617,088 B), or schedule the re-fit"
    why_human: "No admitted bolt has been read above 0.4941 of the headroom (full tier 904,486,912 B max), so no failing part is shown. But a bolt admitted between its measured peak and its budget has no guard other than the OOM kill (L24 note: ASSUMPTION, unmeasured). Presence checks cannot see it; only a runner reading of such a part can."
---

# Phase 7: Operability Re-sweep Verification Report

**Phase Goal:** Every configuration a user is allowed to ask for builds inside a per-build timeout measured on linux/amd64 over the full grid, or is capped and warned or refused with a `422`, and every runtime bound cites the run that set it.
**Verified:** 2026-10-31
**HEAD:** d5a4512 (branch gsd/phase-07-operability-re-sweep)
**Status:** human_needed
**Re-verification:** No, initial verification

## Gate

`make verify` (one run, HEAD d5a4512): `ruff` "All checks passed!", `mypy --strict` "Success: no issues found in 97 source files", import-linter "Contracts: 10 kept, 0 broken.", pytest result line `5155 passed in 249.14s (0:04:09)`, exit 0.

CI on HEAD d5a4512 (read with `gh run view`, not taken from SUMMARY): `ci` run 41218613725 success in all 7 jobs (test (3.12), vendor-bundle, image, bounds (1) to (4)). `operability: full` run 41218613704 success (measure jobs, plan, verdict; `followup` skipped). PR #26 is still a draft and open.

I did not run `make check` (Docker) myself. Its three parts are covered on HEAD by CI: `make verify` (test job), the image build that runs `docker/smoke.py` (image job), and the vendored bundle diff (vendor-bundle job). 07-20-SUMMARY also records `make check` exit 0 at 4a2b536.

## Goal Achievement

### Observable Truths

| # | Truth (source) | Status | Evidence |
| --- | --- | --- | --- |
| 1 | SC1: the per-build timeout is measured over the allowed grid on linux/amd64 and recorded as a constant whose decision entry cites the run | VERIFIED | `src/screw/calc/cost.py:BUILD_TIMEOUT_S` = 26 / 71 / 26 s, a read-only `MappingProxyType` with no env override (`SCREW_BUILD_TIMEOUT` appears nowhere in `src/`, pinned by `tests/test_runtime_bounds.py:371`). The comment and L24 cite bound run 40907549180 and name the bound point and reading per artifact (12.72, 35.26, 12.81 s max cold wall, x2, ceil). `bench/results/phase-07/runtime.json` `timeouts` carries the same figures and equals `derive-runtime` output (tests at `test_runtime_bounds.py:46,50`). Grid coverage: `bench/points/full.json` holds 1056 points (iso4017 558, iso4014 324, iso4032 42, dense-boundary 90, nut factorial 42) = every catalogue row at all three artifacts, so the integer-L/P rows are included; record folder `bench/results/phase-07/full-41161227951/` (1056 readings, all ok, largest cold wall 28.79 s of 71 s, 0.406). Full tier re-run green on HEAD (41218613704). |
| 2 | SC2: memory ceiling, gzip level, worker count and bytes-cache budget are each re-swept for threaded parts on linux/amd64 and each cited; no spur figure and no interim value remains in the code | VERIFIED | L23 table maps each knob to rule and run. Code agrees: `compose.yaml` `mem_limit: 2304m` (= 2415919104 B in runtime.json), `tmpfs /tmp:size=256m`, `SCREW_BUILD_WORKERS: "1"`; `app.py` `DEFAULT_BUILD_WORKERS = 1`, `_GZIP_LEVEL = 1`, `minimum_size=4012`, `EXPORT_CACHE_MB = 240`, queue 2N, `MEDIAN_BUILD_S`; `solid/__init__.py` `SCREW_SOLID_CACHE` 4; `Dockerfile` HEALTHCHECK `--timeout=2s --start-period=10s`. Gzip levels 6 and 9 trialled and rejected at 14 STL points (runs 40909739628, 40999657702); worker N=1/2/3 load table (40909724292); cache and drift runs 41016510597, 41022812680. `grep -rniE "interim"` over `src/`, `Dockerfile`, `compose.yaml` finds nothing; `test_nothing_shipped_is_left_interim_or_waiting_on_a_phase_7_re_sweep` (`test_runtime_bounds.py:360`) and `test_every_run_id_the_code_and_l20_to_l25_cite_has_its_section_in_results` (:338) enforce it. Remaining "spur" strings in `src/` are citations of mechanism, not figures; L23 states spur's 4g, two workers, 1024 B gzip threshold, 64 MiB cache and healthcheck timings are replaced. |
| 3 | SC3a: a CI job builds every allowed configuration inside the timeout; a configuration the model says cannot is capped and warned, or refused with a 422 naming the fields, never silently shortened | VERIFIED | CI: `ci.yml` `bounds` matrix (4 shards, 355 points from `tests/data/oper_boundary.json`) is in `required-jobs.txt`; `operability.yml` full tier runs weekly and on cost-model PRs, and `pr.land` waits for it (`scripts/pr_land.py check_full_tier`). Both green on HEAD. Code paths exist and are used: `cost.fits` / `cost.refusal` (B-02 `over_budget` 422 naming `FIELDS`), `app._serve` calls `download_refusal` first (`app.py:517-526`) and `cli.cmd_export` the same (`cli.py:168`), `cost.cap_defaults` (B-03: caps an unnamed `thread_length`/`length`/`m`, never a named field, never below `MIN_FITTED_TURNS`, one warning that names the field, default and value) wired at `app.py:492,508`; `params._pitch_too_fine` raises `pitch_too_fine` naming `["d","pitch"]`; turn cap, field ceilings and root-radius floor at the model. Tests exist in tests/test_cost.py, test_api.py (10 `over_budget` hits), test_cli.py, test_parity.py and ran in `make verify`. Spot checks (kernel-free, run by me): `BoltParams(d=5)` capped to `thread_length` 16.5 with the cap warning; `BoltParams(d=30,pitch=1)` raises `pitch_too_fine`; `BoltParams(d=100,pitch=5,length=1000,thread_length=1000)` raises `turn_cap`; the three code-review nuts (clearance -30.32 and -21.12) are refused at all three artifacts; the tall nut m 461.4 is refused at `stl-fine` only; default bolt admitted at all three. |
| 3b | SC3 residual: every admitted configuration actually builds (OPER-03 as written) | PASSED (override) | Not met as written: parts inside the L25 walls that the kernel still refuses (long-thread bolts in two d bands, isolated nut cells, e.g. d 3, pitch 0.35, 25 mm thread, right hand) are admitted and then answer `422` `build_error` (`app.py:571-576`) with the builder's message and no `ctx.fields`. No wrong part is served (the gates refuse every bad cut; L02 holds). Override: owner rulings cited in frontmatter. REQUIREMENTS.md keeps OPER-03 Pending. Debt item exists, is `must`, and is indexed. |
| 4 | SC4: CAD builds still run in worker processes off the event loop; `make check` passes | VERIFIED | `pool.py` one single-worker `ProcessPoolExecutor` per slot, spawn context, `loop.run_in_executor` at `pool.py:192`; D-14 queue-aware deadline in `_run_with_timeout`; `tests/test_pool.py` and `test_runtime_bounds.py` (lifespan starts the picked worker count) in `make verify`. In-image smoke and the vendored-bundle check are the `image` and `vendor-bundle` CI jobs, success on HEAD. |
| 5 | Goal clause: every runtime bound cites the run that set it | VERIFIED | `tests/test_runtime_bounds.py` ties every shipped value to L23/L24 text (`:273,:312`), to runtime.json (`:56`), and every run id cited in code and L20 to L25 to a RESULTS.md section (`:338`). I read `src/screw/calc/cost.py`, `app.py`, `compose.yaml` and `Dockerfile` and found each bound with a rule and run id in its comment. `cost.py` model constants are emitted by `bench.oper_fit emit-constants` from `fit.json` (runs 40646117094, 40646125666; envelope widened by 40909768713 and 41206999278) and held equal by tests/test_cost.py. |
| 6 | Quick-task fixes landed: CR-01, WR-01..WR-04 (261031-o7u) and the tall-nut/memory work (261031-qd7) | VERIFIED | All ten commits (f0c890e, 7013c0d, 7c4ac07, 8ed48ee, 3febf4b, e65ff6c, ab72cf8, 912e1ca, b5cc6f9, 4282ef6) are ancestors of HEAD. `cost.BANDS` has `("nut","clearance"): (0.15, 5.0)` emitted, `BANDED_IN_MM`, G39 pairing in `_edges`, `HEADROOM_CAPPED = {("nut","stl-fine")}` with `WORKER_HEADROOM_BYTES = 1830617088`; ci.yml `prediction-drift` step has `continue-on-error: true`. Reproduced: CR-01's three nuts are refused at all artifacts. `outband-tall-41206999278` record folder (135 readings, all ok) exists, with RESULTS section. |
| 7 | Plan 07-19 truth: near-timeout full-tier rows are re-read at 5 repetitions on 5 runner instances and the verdict fails closed on an unread follow-up | PRESENT_BEHAVIOR_UNVERIFIED | Code present and wired (`operability.yml` followup-plan / followup / verdict jobs; `bench/oper_sets.py`), logic pinned by synthetic tests that passed. The job has never run on a runner. See `behavior_unverified_items`. |

**Score:** 7/8 truths verified (1 of them by owner override), 1 present but behavior-unverified.

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/screw/calc/cost.py` | timeouts, fitted model, budgets, refusal, cap | VERIFIED | Substantive, kernel-free, imported by app/cli/calc; constants are emitted blocks |
| `bench/results/phase-07/runtime.json` | derived runtime bounds with readings | VERIFIED | 23 source record folders all present on disk; equals `derive-runtime` (test) |
| `bench/results/phase-07/fit.json` | cost-model fit from runs | VERIFIED | Recomputed from committed records by tests/test_oper_fit.py |
| `compose.yaml`, `Dockerfile` | measured limits and healthcheck | VERIFIED | Match runtime.json (tests/test_runtime_bounds.py:204-235) |
| `src/screw/pool.py`, `app.py` | worker processes, queue-aware deadline, Retry-After | VERIFIED | Wired; tests pass |
| `.github/workflows/ci.yml`, `operability.yml`, `required-jobs.txt` | required bounds tier, full tier | VERIFIED | Present; green on HEAD; list equals ci.yml (tests/test_pr_land.py) |
| `docs/architecture/decision_log.md` L20 to L32 | decision entry per bound | VERIFIED | Headings for L20 to L32 all present |
| `docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md` | OPER-03 named gap | VERIFIED (exists, must, indexed) | All 22 active debt files are indexed in INDEX.md |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `app._serve` | `calc.download_refusal` -> `cost.refusal` | first call before the pool | WIRED | `app.py:517-526`; `cli.py:168-170` |
| `app` model routes | `cost.cap_defaults` | `explicit_fields(request, kind)` | WIRED | `app.py:492, 508` |
| `params` validators | `thread.pitch_too_fine_refusal` | `_pitch_too_fine` | WIRED | `params.py:158-166, 235, 305` |
| `pool._run_with_timeout` | `cost.BUILD_TIMEOUT_S` | per-artifact deadline | WIRED | `app.py:46` imports it |
| `app._serve` BuildTimeout branch | `records.cost_model_miss` | ERROR log, not cached | WIRED | D-10; tests/test_records.py |
| `tests/test_runtime_bounds.py` | runtime.json, L23, L24, RESULTS | consistency | WIRED | ran in `make verify` |
| ci.yml `bounds` | `pr.land` | required-jobs.txt | WIRED | `scripts/pr_land.py check_head`; tests/test_pr_land.py |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Real data | Status |
| --- | --- | --- | --- | --- |
| `cost.COEFFICIENTS/ENVELOPE/BANDS/BUDGET` | fit constants | `bench.oper_fit emit-constants` from fit.json, which tests recompute from committed runner records | yes | FLOWING |
| `app.MEDIAN_BUILD_S` / `retry_after` | medians | runtime.json `retry_after`, load run 40909724292 | yes | FLOWING |
| refusal / cap warning text | prediction | prints fields and defaults only, never a figure (L02) | n/a | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Reviewer nuts refused at all artifacts | `.venv/bin/python` + `cost.fits` on the three CR-01 / G39 nuts | all False at preview, fine, step | PASS |
| Tall nut m 461.4 refused only at fine STL; budget capped | `cost.fits`, `cost.budget("nut","stl-fine")` | `(True, False, True)`, peak 1830617088.0 | PASS |
| Default bolt admitted everywhere | `cost.fits(BoltParams(), a)` | all True | PASS |
| Defaulted thread capped and warned | `cost.cap_defaults(BoltParams(d=5), {"d"})` | thread_length 16.5, one warning naming field, default, value | PASS |
| Fine-pitch wall is a 422 naming d and pitch | `BoltParams(d=30)` | `pitch_too_fine` | PASS |
| 90-turn cap is a 422 | `BoltParams(d=100,pitch=5,length=1000,thread_length=1000)` | `turn_cap` naming thread_length, length, pitch | PASS |
| Whole gate | `make verify` | `5155 passed in 249.14s`, exit 0 | PASS |

### Probe Execution

Step 7c: SKIPPED. No `scripts/*/tests/probe-*.sh` exist and no plan declares a probe script; the phase's runner "probes" are the bench harness, covered by committed run records and tests.

### Requirements Coverage

| Requirement | Source plans | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| OPER-01 | 13 plans | worker processes off the event loop; per-build timeout measured over the whole grid, cited | SATISFIED | Truths 1, 4, 5 |
| OPER-02 | 12 plans | memory ceiling, gzip, workers, cache budget re-swept on linux/amd64, no spur figure | SATISFIED | Truths 2, 5 |
| OPER-03 | 13 plans | every allowed configuration builds inside the timeout, or is capped/warned or 422 | NOT SATISFIED as written; KNOWN, OWNER-ACCEPTED, Pending in REQUIREMENTS.md | Truth 3a verified (CI job, cap, 422 paths); Truth 3b residual under override. Named gap: `docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md` |

Orphans: REQUIREMENTS.md maps only OPER-01, OPER-02, OPER-03 to Phase 7, and all three appear in plan frontmatter. None orphaned.

### Anti-Patterns Found

`make verify` includes the unfinished-work scan and passed (no unreferenced `TBD`/`FIXME`/`XXX`). No blocker anti-patterns.

| File | Pattern | Severity | Impact |
| --- | --- | --- | --- |
| `compose.yaml:27` | `mem_limit` without `memswap_limit` (code review IN-04, unfixed) | Info | The measured cap was a wall (`--memory` = `--memory-swap`); the deployed container may swap past it on a host with swap accounting. Not covered by tests. |
| `src/screw/calc/thread.py:301-306` | stale 250-turn docstring (IN-01) | Info | Comment only |
| `src/screw/pool.py:99-100,170-171,212` | slot computed three times, stale same-slot branch (IN-02) | Info | Dead-ish branch, no behavior change |
| `src/screw/calc/cost.py:21` | imports private `_plain` (IN-03) | Info | Style |
| `src/screw/cli.py:163-189` | cap warning printed only after a successful export (IN-05) | Info | On a `BuildError` the user is not told the part was capped |
| `src/screw/static/app.js:574-575` | `find()` result assumed present (IN-06) | Info | `_DOWNLOADS` guarantees it today |
| `scripts/pr_land.py:464-490` | renamed gate file and 3000-file cap (IN-07) | Info | Gate-bypass edge; WR-02 widened the list but IN-07 is open |
| `docs/tech_debt/INDEX.md` | resolved rows say "this commit" (IN-08) | Info | Traceability only |

The review's CR-01 and WR-01 to WR-04 are fixed (commits above). IN-01 to IN-08 were not part of the fix tasks and remain open; none touches the goal.

Known, owner-signed debt, cited and checked against the goal (none contradicts it, because no admitted part has been shown over a runtime limit):

- `2026-10-29-in-wall-parts-the-kernel-refuses.md` (must): OPER-03's named gap, above.
- `2026-10-31-bolt-fine-peak-budget-above-the-worker-headroom.md` (must): see human item 2.
- `2026-10-31-nut-peak-envelope-refuses-parts-read-under-the-headroom.md` (must): refuses, never admits; one reachable nut (`tall-nut-x0.5-m10.5d`).
- `2026-10-31-head-ratio-edges-never-meet-a-real-out-of-band-ratio.md` (must): one measured case is 1.0024x, inside every envelope; d-only M2/M3 runner readings show no miss (max 0.5992 of envelope).
- `2026-10-31-full-tier-follow-up-job-never-run-on-the-runner.md` (nice): truth 7.
- `2026-10-30-build-time-corpus-is-mostly-refused-by-the-cost-model.md`, `2026-10-29-status-sentence-runs-under-fit.md`, `2026-10-28-shank-fold-warning-rounds-the-numbers-it-compares.md` (nice) and the older Phase 1 to 6 items.

One standing design fact the owner ruled (WR-03, recorded in L24, pinned by `test_the_budgets_are_looser_than_the_limits_exactly_where_l24_records_it`): the B-01 seconds budgets (34.13 s preview, 94.43 s fine) are above the timeouts (26 s, 71 s). A part admitted at the budget edge would meet the timeout, which answers a 503 and logs `cost_model.miss`. Every read part is far below (largest 0.406 of timeout on the full grid; outband-tall max 36.6 s of 71 s). The goal's "builds inside the timeout" is therefore backed by sampled evidence plus an enveloped model plus a logged backstop, not by an exhaustive proof; that is inherent and was ruled.

### Human Verification Required

#### 1. Close Phase 7 with OPER-03 Pending

**Test:** Owner confirms the phase closes with OPER-03 Pending and says what carries it.
**Expected:** The residual in `2026-10-29-in-wall-parts-the-kernel-refuses.md` is accepted until the pre-release item (try the sweep-accuracy kernel fix behind the L25 walls, re-read on linux/amd64, supersede L25 if it holds).
**Why human:** The requirement text is unmet by an existing owner ruling; whether to close, defer or re-open is the owner's decision.

#### 2. Bolt fine-STL peak budget above the worker headroom

**Test:** Owner decides: accept the filed debt, or schedule the bolt stl-fine peak re-fit before release.
**Expected:** Either the item is accepted as filed (revisit before first release, or as soon as an admitted bolt reads a fine-STL peak above 1,830,617,088 B), or a plan is made.
**Why human:** No failing part exists, but the guarantee "an admitted bolt cannot be OOM-killed" has no measurement behind it between 904 MB (max read) and 2.93 GB (budget).

#### 3. Follow-up job on the runner (behavior-unverified truth 7)

**Test:** Dispatch the full tier so the follow-up job actually runs, and record the run id in `bench/RESULTS.md`.
**Expected:** `followup-plan` selects near-timeout rows, `followup` reads them on 5 instances, `verdict` judges the max and fails closed on an unread follow-up.
**Why human:** Needs a runner dispatch with a near-timeout point; never run on the runner. Nice-severity debt.

### Gaps Summary

No blocking gap. The phase goal is met for everything the measurement tiers can reach: the three timeouts, the worker count, `mem_limit`, tmpfs, gzip level, minimum size, export cache, solid cache, queue depth, Retry-After and healthcheck are all code or compose constants that cite a committed GitHub-runner record, with a test tying each to runtime.json, the decision log and RESULTS.md. The full tier (1056 catalogue and boundary points) and the 355-point required tier are green on HEAD; capped-and-warned and `over_budget` / `pitch_too_fine` / `turn_cap` 422 paths exist, are wired at the request boundary on API and CLI, and are tested. `make verify` is green (5155 passed).

The one shortfall is the one you told me about: OPER-03 is Pending because admitted in-wall parts can still reach a kernel `BuildError`, which the API turns into a `422` `build_error` that names no field. I carried it as an override citing the owner's rulings, not as a failure. The status is `human_needed` rather than `passed` because three items need a human: the owner's close-out of OPER-03, the unguarded (unmeasured) bolt fine-STL peak budget, and the follow-up job that has never run on a runner.

---

_Verified: 2026-10-31_
_Verifier: Claude (gsd-verifier)_
