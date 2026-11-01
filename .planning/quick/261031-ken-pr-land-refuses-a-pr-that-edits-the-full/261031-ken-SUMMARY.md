---
phase: quick-261031-ken
plan: 01
status: complete
subsystem: merge gate / pr.land
tags: [security, pr-land, operability, L28]
branch: gsd/phase-07-operability-re-sweep
plan_head_before: f3b907d1ad51b0fe260d3a49475e62125ba3a8f4
plan_head_after: 6d05169
commits: 4
---

# Quick 261031-ken: pr.land refuses a PR that edits the files judging its own full tier

`make pr.land` now refuses a PR whose diff touches a `GATE_PATHS` file, unless the owner passes
`--owner-approves-gate-change`. The list is the six files that produce and judge a full-tier
verdict, and a test derives it from operability.yml.

## Commits

| sha | Subject | Files |
| --- | --- | --- |
| da39988 | feat(pr-land): refuse a PR that edits what judges its own full tier | scripts/pr_land.py, tests/test_pr_land.py, Makefile, docs/HOW_TO_DEVELOP.md |
| a0b71fe | docs(decisions): log L28, pr.land refuses a PR that edits its own full-tier judge | docs/architecture/decision_log.md |

## The guarded list (`GATE_PATHS`)

- `.github/workflows/operability.yml`
- `bench/__init__.py`: `host_facts`, which `bench.oper` imports
- `bench/oper.py`: every `python -m` step (`matrix`, `run`, `summarize`, `followup-matrix`, `verdict`)
- `bench/oper_child.py`: the child that `bench.oper run` starts in each container from the mounted `bench/`
- `bench/oper_lift.py`: imported by the child for a bolt or a nut
- `bench/points/full.json`: the points, plus the timeouts and limits the verdict judges against

Left out: `oper_bound.py`, `oper_load.py` and `thread_spike/`. They run only for bound, load and
probe points, and `full.json` has none of those (972 bolt points and 84 nut points; a test pins
this). `oper_sets.py` and `oper_fit.py` are never imported by a run. `tests/data/oper_boundary.json`
is read only by ci.yml's `bench.oper check`, not by the full tier.

## The rule

- `gate_refusals(pr_number, changed, owner_approves)` sits next to `full_tier_refusals`.
  `check_full_tier` applies it to the files it already reads, so there is no new `gh` call.
- The refusal names the touched files and gives the command
  `make pr.land PR=<n> PR_LAND_FLAGS=--owner-approves-gate-change`.
- The flag lifts only this rule. A PR that also touches `FULL_TIER_PATHS` still needs its green
  full run, and a test checks this.
- The Makefile passes `$(PR_LAND_FLAGS)` through. When it is empty, nothing is approved.

## Tests (tests/test_pr_land.py, 106 pass)

- Refused without the flag: PR A's (#22) recorded files, plus each guarded file on its own.
- Allowed with the flag.
- Unaffected by a diff that touches no guarded file, including `oper_sets.py`, `oper_bound.py`
  and `tracer.json`.
- `land()` refuses with no merge call, and merges with the flag.
- Drift: `full_tier_judge_files(workflow)` equals `GATE_PATHS`. It covers the `python -m`
  modules, `bench.oper_child`, the `ast` import closure, the package `__init__.py` files and the
  `--set` point file. A second test checks that `full.json` has no bound, load or probe kind.
- PR A's real file list now trips the rule, so the existing tests that are about other rules use
  `PR_A_FILES_NO_GATE`.

## Verify

`make verify`: `======================= 4804 passed in 235.00s (0:03:54) =======================`
(the run before the L28 commit; the one before da39988 gave the same 4804 passed in 236.59s).

## PR #26

PR #26 touches five of the six guarded files: operability.yml, oper.py, oper_child.py,
oper_lift.py and full.json. `bench/__init__.py` is already on main. Landing it needs
`make pr.land PR=26 PR_LAND_FLAGS=--owner-approves-gate-change`. It stays a draft.

## Deviations

- [Rule 3] Added a `PR_LAND_FLAGS` pass-through to the `pr.land` make target. The module runs only
  as `make pr.land`, so without it the flag could not be passed.
- One sentence was added to docs/HOW_TO_DEVELOP.md section 8.

## Not filed

No debt or idea item was filed. The same shape against `ci.yml`, a PR editing its own required jobs,
is outside this ruling and was not investigated here.

## Self-Check: PASSED

da39988 and a0b71fe are ancestors of HEAD. All the files listed above exist.

## Addendum: T-07-72, the required jobs' judge (owner: "Extend L28 guard (Recommended)")

The ci.yml gap noted under "Not filed" above was ruled on. It is threat T-07-72.

| sha | Subject | Files |
| --- | --- | --- |
| 6d05169 | feat(pr-land): extend the gate-change rule to the required jobs' judge | scripts/pr_land.py, tests/test_pr_land.py, docs/HOW_TO_DEVELOP.md, docs/architecture/decision_log.md |

- There is still one list and one flag. `GATE_PATHS` (scripts/pr_land.py:104) gains
  `.github/workflows/ci.yml`, `.github/workflows/required-jobs.txt` and
  `tests/data/oper_boundary.json`.
- Nothing more was needed from bench: ci.yml's `bounds` job runs
  `python3 -m bench.oper check tests/data/oper_boundary.json`, and that reaches only `bench.oper`
  and the container child `bench.oper_child` with `bench.oper_lift`, all three already listed.
  The boundary file holds 329 bolt points and 26 nut points, with no bound, load or probe kind.
- The drift test `test_gate_paths_are_what_the_full_tier_and_the_bounds_job_run_and_read` derives
  the list from all of operability.yml and ci.yml's `bounds` job, plus `required-jobs.txt`. The
  kinds test now runs on both point files.
- The limit is stated in L28 and is not guarded: `test (3.12)` runs the PR's own `make verify`
  and `prediction-drift`, and `vendor-bundle` builds the PR's own `web/`.
- L28 was rewritten in place, because it exists on this branch only.
- PR #26 touches 8 of the 9 files, all but `bench/__init__.py`, so it still needs the flag.
- `make verify`: `======================= 4808 passed in 171.54s (0:02:51) =======================`

Final `GATE_PATHS`: `.github/workflows/ci.yml`, `.github/workflows/operability.yml`,
`.github/workflows/required-jobs.txt`, `bench/__init__.py`, `bench/oper.py`, `bench/oper_child.py`,
`bench/oper_lift.py`, `bench/points/full.json`, `tests/data/oper_boundary.json`.

Self-check: 6d05169 is an ancestor of HEAD.
