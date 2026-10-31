---
phase: quick-261031-ken
plan: 01
status: complete
subsystem: merge gate / pr.land
tags: [security, pr-land, operability, L28]
branch: gsd/phase-07-operability-re-sweep
plan_head_before: f3b907d1ad51b0fe260d3a49475e62125ba3a8f4
plan_head_after: a0b71fe841227facc1a02e4f12f897640a19b4e0
commits: 2
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
