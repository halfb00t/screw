---
phase: 07-operability-re-sweep
reviewed: 2026-10-31T00:00:00Z
depth: standard
files_reviewed: 100
files_reviewed_list:
  - .github/workflows/ci.yml
  - .github/workflows/operability.yml
  - .github/workflows/required-jobs.txt
  - bench/__init__.py
  - bench/build_time.py
  - bench/corpus.py
  - bench/end_cuts.py
  - bench/export_cost.py
  - bench/nut_fine_caps.py
  - bench/oper_bound.py
  - bench/oper_child.py
  - bench/oper_fit.py
  - bench/oper_lift.py
  - bench/oper_load.py
  - bench/oper_serve.py
  - bench/oper_sets.py
  - bench/oper.py
  - bench/points/arenas.json
  - bench/points/bound-rerun.json
  - bench/points/bound-smoke.json
  - bench/points/bound.json
  - bench/points/controls.json
  - bench/points/dense-band.json
  - bench/points/drift-60.json
  - bench/points/drift.json
  - bench/points/explore.json
  - bench/points/full.json
  - bench/points/gzip-rerun.json
  - bench/points/gzip.json
  - bench/points/load-smoke.json
  - bench/points/load.json
  - bench/points/outband.json
  - bench/points/solid-cache-4.json
  - bench/points/spread.json
  - bench/points/tracer.json
  - bench/points/walls-confirm.json
  - bench/points/walls-down.json
  - bench/points/walls-pitch.json
  - bench/points/walls.json
  - bench/README.md
  - bench/RESULTS.md
  - bench/results/phase-07/fit.json
  - bench/results/phase-07/runtime.json
  - bench/results/phase-07/tier-order.json
  - bench/thread_spike/verdict.py
  - compose.yaml
  - Dockerfile
  - docs/architecture/decision_log.md
  - docs/architecture/overview.md
  - docs/ideas/2026-10-11-oper-02-resweep-runs-the-controls.md
  - docs/ideas/INDEX.md
  - docs/tech_debt/active/2026-10-05-shared-infra-extraction.md
  - docs/tech_debt/active/2026-10-10-spike-protocol-amendments-before-next-campaign.md
  - docs/tech_debt/active/2026-10-14-m18-probe-one-entry-has-no-deadline-during-a-run.md
  - docs/tech_debt/active/2026-10-21-nut-countersink-cutter-crosses-the-axis-at-a-coarse-pitch.md
  - docs/tech_debt/active/2026-10-28-shank-fold-warning-rounds-the-numbers-it-compares.md
  - docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md
  - docs/tech_debt/active/2026-10-29-status-sentence-runs-under-fit.md
  - docs/tech_debt/active/2026-10-31-full-tier-follow-up-job-never-run-on-the-runner.md
  - docs/tech_debt/INDEX.md
  - docs/tech_debt/resolved/2026-10-05-interim-runtime-bounds.md
  - docs/tech_debt/resolved/2026-10-06-bench-memory-sampling-is-too-coarse-for-short-corpora.md
  - docs/tech_debt/resolved/2026-10-11-default-pitch-d100-length200-exceeds-both-interim-backstops.md
  - docs/tech_debt/resolved/2026-10-14-nut-interim-bounds.md
  - docs/tech_debt/resolved/2026-10-29-cost-model-admits-out-of-fit-head-heights.md
  - Makefile
  - pyproject.toml
  - scripts/pr_land.py
  - src/screw/app.py
  - src/screw/calc/__init__.py
  - src/screw/calc/cost.py
  - src/screw/calc/thread.py
  - src/screw/cli.py
  - src/screw/params.py
  - src/screw/pool.py
  - src/screw/records.py
  - src/screw/solid/__init__.py
  - src/screw/static/app.js
  - tests/data/oper_boundary.json
  - tests/test_api.py
  - tests/test_bench.py
  - tests/test_calc.py
  - tests/test_cli.py
  - tests/test_cost.py
  - tests/test_fine_pitch.py
  - tests/test_mesh.py
  - tests/test_oper_bound.py
  - tests/test_oper_fit.py
  - tests/test_oper_followup.py
  - tests/test_oper_load.py
  - tests/test_oper_pitch.py
  - tests/test_oper.py
  - tests/test_parity.py
  - tests/test_pool.py
  - tests/test_pr_land.py
  - tests/test_presets.py
  - tests/test_records.py
  - tests/test_runtime_bounds.py
  - tests/test_solid.py
  - tests/test_thread_maths.py
findings:
  critical: 1
  warning: 4
  info: 8
  total: 13
status: issues_found
---

# Phase 07: Code Review Report

**Reviewed:** 2026-10-31
**Depth:** standard
**Files Reviewed:** 100
**Status:** issues_found

## Summary

Reviewed `src/screw/*`, `scripts/pr_land.py`, `bench/oper*.py` and the build and corpus bench
diffs, the workflows, `Makefile`, `Dockerfile` and `compose.yaml` in full or by phase diff. The
JSON point and record files, the docs and the tests were checked for consistency with the code,
not line by line. `oper_sets.py` (4100 lines) was read at its command layer, the boundary tier
and the regeneration and drift paths, not exhaustively.

Checks run (read-only): `ruff check .` clean; `lint-imports` 10 kept, 0 broken;
`pytest tests/test_cost.py tests/test_fine_pitch.py tests/test_runtime_bounds.py tests/test_pr_land.py`
272 passed; `python -m bench.oper_sets prediction-drift` shows 0 drift on this host. Two
random-request fuzz passes over `/api/{bolt,nut}/info` (4000 requests, 200 or 422 only, no 500) and
a parity check between the info document and the model route's 422 found nothing.

The pool deadline, the `Retry-After` arithmetic, the compose and Dockerfile figures against
`runtime.json`, the cap algorithm, the fine-pitch wall maths and the runner-side judge are
correct as written. The one defect that changes what the service admits is in the cost model: a
nut's `clearance` is an unguarded linear feature fitted at two values, and the model admits a nut
on a prediction an actual build contradicts (CR-01).

## Critical Issues

### CR-01: The cost model extrapolates a nut's `clearance` linearly outside the two values it was fitted at, and admits a fine STL that is 24x its prediction and 2.5x its budget

**File:** `src/screw/calc/cost.py:163-168` (`BANDS` has no `clearance` entry), `:200-209` (`_features` uses `p.clearance` raw), `:226-259` (`_edges`, `predict`); mirrored in `bench/oper_fit.py:72` (`RATIOS`) and `:198-216` (`edges`)
**Issue:** `explore.json` and `full.json` read nuts at `clearance` 0.15 and 5.0 only (explore: 171 at 0.15, 72 at 5.0, 42 default; spread and outband: default only). The model feeds `clearance` into the fit as a plain linear term, and G28's band guard covers head ratios only. The parameter model allows `clearance` from about `-(d/2 - 5H/8 - 0.01)` up to 496.999. Below 0.15 the three `stl-fine` nut models (bytes +0.112, seconds +0.065, peak +0.055 per mm) predict a *cheaper* part with no reading behind it. This is the same defect class as the resolved head-height item (`docs/tech_debt/resolved/2026-10-29-cost-model-admits-out-of-fit-head-heights.md`), which the owner ruled as G28 and fixed for `k`, `s` and `m`.

Reproduced (mesh bytes are geometry, so macOS arm64 is valid for them):

```
NutParams(d=163.65, pitch=21.743, s=387.26, m=1589.12, clearance=-30.32)
  cost.fits(p, "stl-fine")                  -> True    (stl-preview, step, are refused)
  predicted raw fine-STL bytes              -> 24,513,233  (x(1+e) is about 36.7 MB)
  B-01 stl-fine bytes budget                -> 239,508,059
  solid.export(p, "stl", "fine") measured   -> 591,529,584 bytes, 26.95 s
```

The same nut at `clearance` 0.15 is refused at all three artifacts. A second case,
`d=92.28 pitch=31.418 s=130.54 m=967.04 clearance=-21.12`: predicted 18.8 MB, measured 121.6 MB
(6.5x), admitted. `GET /api/nut/info` for the first nut returns 200 with `stl-fine` unrefused. Of
19,324 randomly drawn valid nuts, 7,349 had an artifact refused at `clearance` 0.15 and admitted at
a negative `clearance`, so the flip is not a corner.

Consequences: the envelope guarantee (`pred x (1+e) >= actual`) does not hold off the fitted
values; a 591 MB response does not fit the 256 MiB `/tmp` tmpfs the export is written to
(`solid._write_export`), the 240 MiB export cache, or the headroom `mem_limit` leaves, so an
admitted request ends as a `build_error` 422 or an OOM-killed worker at N = 1 instead of the clean
`over_budget` refusal L21 promises. This is L02: a prediction nothing supports is used as a number.

**Fix:** treat `clearance` like G28's ratios. Add a fitted range per kind (`("nut", "clearance"):
(0.15, 5.0)`, emitted by `bench.oper_fit.emit-constants` from the fitted points, never typed) and in
`_edges` / `oper_fit.edges` evaluate a `clearance` below the low edge also at the low edge, and one
above the high edge also at the high edge, taking the max of raw and edge predictions as for the
ratios. The minimal alternative is to refuse (or cap-and-warn) a nut `clearance` outside the
fitted range until a Runs II out-of-band set reads it. Either needs an owner ruling (a new G
entry) and a regression test that the example above is refused at `stl-fine`. Add negative and
zero `clearance` points to the outband set so R12 can widen `e`.

## Warnings

### WR-01: The documented `make bench.export` example cannot run

**File:** `Makefile:178`, `bench/export_cost.py:13-14`, `bench/README.md:20,62`
**Issue:** This phase rewrote the example from `d=100 length=200` to `SET="d=100 length=90"` in all
four places. `find_set` matches the label exactly, and the corpus label of that part is
`d=100 length=90 s=200 k=50 thread_length=90`. Running `python -m bench.export_cost --set "d=100 length=90"`
exits 2 with `error: no set labeled 'd=100 length=90'`. CODING_VALUES: "The README's own commands are
tests."
**Fix:** write the full label in all four places (`SET="d=100 length=90 s=200 k=50 thread_length=90"`),
or make `find_set` accept a unique prefix. Add a test that runs the documented `--set` argument
through `find_set`.

### WR-02: `GATE_PATHS` leaves `scripts/pr_land.py` and the `pr.land` recipe unguarded, the hole L28 closes for `required-jobs.txt`

**File:** `scripts/pr_land.py:104-114` (`GATE_PATHS`), `:79-84` (`FULL_TIER_PATHS`)
**Issue:** L28's reason for listing `required-jobs.txt` is that "merging a PR makes the PR's copy
main's list for every later landing". `scripts/pr_land.py` (which holds `GATE_PATHS`,
`FULL_TIER_PATHS`, `check_head`, the whole merge gate) and the `pr.land` recipe in `Makefile` have
the same property and are on neither list, so a PR that deletes a gate lands without
`--owner-approves-gate-change`. L28's "The limit" paragraph excuses only files the PR's own CI runs
(`make verify`), which does not cover this. Separately, `requirements.txt`, `Dockerfile` and the
kernel pair they pin can move every measured bound, but are in neither `FULL_TIER_PATHS` nor the
`paths:` filter of `operability.yml`; only the weekly schedule and the 355-point required tier
would see a kernel bump.
**Fix:** add `scripts/pr_land.py`, `tests/test_pr_land.py` and `Makefile` to `GATE_PATHS`, and
`requirements.txt` and `Dockerfile` to `FULL_TIER_PATHS` and the workflow `paths:` (the existing
parity tests will force both lists to agree), or record in L28 why each is out.

### WR-03: The admission budgets are looser than the limits that enforce them, and nothing ties them

**File:** `src/screw/calc/cost.py:45-46,175-179`, `compose.yaml:27`
**Issue:** `BUDGET` is the largest enveloped catalogue prediction; `BUILD_TIMEOUT_S` and `mem_limit`
come from the worst measured reading. They disagree where a part can sit between them:
stl-preview seconds budget 34.13 s against a 26 s timeout; stl-fine 94.43 s against 71 s;
stl-fine peak budget 2,930,457,561 B against the worker headroom of `mem_limit` 2,415,919,104 B less
the idle server (65,208,320), the export cache (251,658,240) and the tmpfs (268,435,456), which is
1,830,617,088 B. A part admitted at the budget edge would be killed by its timeout (a 503 and a
replaced worker, with `cost_model.miss` logged as the model's fault) or by the container. The
measured maxima (12.7 s, 35.3 s, W 1.76 GB) are below the limits, so no failing part is shown;
the point is that no test or rule asserts `budget <= limit`, so a widened envelope (R12 widens `e`
and with it the next regenerated budget) can silently cross them. `tests/test_runtime_bounds.py`
checks `mem_limit` and the timeouts against `runtime.json` but never against `BUDGET`.
**Fix:** add a test (and a line in L21/L22) stating the invariant that holds, for example
`BUDGET[a].seconds <= BUILD_TIMEOUT_S[a]` and `BUDGET[a].peak + B + cache + tmpfs <= mem_limit`, or
record that the budget is deliberately looser and that the timeout and `cost_model.miss` are the
backstop for the gap, with the numbers above.

### WR-04: A step the workflow calls "a record, not a gate" can fail the required `test (3.12)` job

**File:** `.github/workflows/ci.yml:42-45`
**Issue:** `predicted-float drift on this runner` runs `python -m bench.oper_sets prediction-drift`
with `if: always()` and no `continue-on-error`. The command regenerates every committed point file;
any `ProtocolStop` (exit 3), `ValueError` (exit 2) or traceback inside it turns the `test (3.12)`
check, which `required-jobs.txt` makes mandatory, red for a reason unrelated to the gate. The
operability workflow's own display-only summary step does use `continue-on-error: true`.
**Fix:** add `continue-on-error: true` to the step, or drop `if: always()` and let it run only
after a green `make verify`.

## Info

### IN-01: Stale 250-turn text after the cap became 90

**File:** `src/screw/calc/thread.py:301-306`
**Issue:** the `_exact` docstring still explains itself with "175 / 0.7 ... is exactly 250 turns and
is measured" while `MAX_TURNS` is now 90.
**Fix:** reword the example around the current cap (for example 63 mm at pitch 0.7 is exactly 90).

### IN-02: `pool.py` computes the slot three times, and the replaced-executor timeout branch is now effectively dead

**File:** `src/screw/pool.py:99-100,170-171,212`
**Issue:** `hash(p) % self.workers` is written in `executor_for`, `_run_with_timeout` (twice, once for
the slot and once at line 212) and `recreate_for`, and `_run_with_timeout` no longer calls
`executor_for`. Because the D-14 deadlines on one slot are strictly increasing in submit order (at
least one timeout apart), the "several requests time out in one pass" case that the same-slot guard at
line 212 and its comment describe cannot occur any more; a queued request sees `BrokenProcessPool`
first. `app._serve` also logs `cost_model.miss` for every `BuildTimeout`, including that branch.
**Fix:** use `slot` throughout, and either drop the stale branch and its comment or keep it with a
note that it is defensive.

### IN-03: `cost.py` imports a private name from `calc.thread`

**File:** `src/screw/calc/cost.py:21`
**Issue:** `from screw.calc.thread import _plain, built_thread_length` reaches into an underscore
helper across modules.
**Fix:** rename `_plain` to a public name in `thread.py`, or format the numbers in `cost.py`.

### IN-04: `compose.yaml` sets `mem_limit` but not `memswap_limit`

**File:** `compose.yaml:27`
**Issue:** every reading ran with `--memory` and `--memory-swap` both at the cap, "so the cap is a
wall" (`bench/oper.py:353`, `bench/oper_load.py:103`). The deployed container only has `mem_limit`, so
on a host with swap accounting it may use up to twice that in swap instead of meeting the wall that
was measured.
**Fix:** add `memswap_limit: 2304m`.

### IN-05: The CLI prints the cap warning only after a successful export

**File:** `src/screw/cli.py:163-189`
**Issue:** `cmd_export` takes the capped part, but the warnings (including the cap's) are printed
last. If `export` raises `BuildError`, the user sees `error: ...` about a part whose `length` or
`thread_length` the tool changed, with no mention of the cap.
**Fix:** print `info.warnings[0]` when it is a cap warning before the export, or print the warnings in a
`finally`. Add a CLI test for the failure path.

### IN-06: `update()` assumes the info document always lists the preview download

**File:** `src/screw/static/app.js:574-575`
**Issue:** `info.downloads.find(...)` returns `undefined` if the entry is missing, and
`preview.refusal` then throws a `TypeError` that the `catch` reports as a request failure.
**Fix:** `if (preview === undefined || preview.refusal !== null)` with the missing case sent to
`fail([...])`, or a comment that `_DOWNLOADS` guarantees the entry (it does today).

### IN-07: `gate_refusals` reads only the new name of a renamed file and trusts a paginated list

**File:** `scripts/pr_land.py:464-490`
**Issue:** `--jq '.[].filename'` omits `previous_filename`, so renaming a `GATE_PATHS` file out of its
path shows only the new name. The pulls-files API also caps at 3000 files, past which the list is
silently short.
**Fix:** `--jq '.[] | .filename, (.previous_filename // empty)'`, and refuse when the count reaches 3000.

### IN-08: Resolved debt rows name no commit, and a style slip

**File:** `docs/tech_debt/INDEX.md:43-45,47,49`, `bench/oper_sets.py:4045`
**Issue:** AGENTS.md asks that a resolved item carry the commit sha; five rows from this phase read
"this commit" and the item files say "`git log --grep` finds the sha". `bench/oper_sets.py:4045` has
`drift_set =sub.add_parser(` (no space before `sub`).
**Fix:** fill the shas in with the next docs commit; fix the spacing.

---

_Reviewed: 2026-10-31_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
