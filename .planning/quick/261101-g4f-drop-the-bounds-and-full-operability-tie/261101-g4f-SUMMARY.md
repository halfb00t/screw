---
phase: quick-261101-g4f
plan: 01
status: complete
subsystem: CI / merge gate
tags: [ci, operability, pr-land, L26, L27, L28, L33]
branch: gsd/phase-07-operability-re-sweep
plan_head_before: 2a0562f2376e95a170c87e61d4b7d219b9247ffd
plan_head_after: 3e88de86209a363cae5ae33a87d177a3d14ef233
commits: 3
actuals:
  tokens: 20245
  tasks: 3
  commits: 3
---

# Quick 261101-g4f: drop the bounds and full operability tiers (L33)

CI no longer measures anything on the runner. The required `bounds` job is gone, along with the
full tier's schedule, PR trigger and follow-up and verdict jobs. `make pr.land` no longer has the
full-tier rule or the gate-file rule. L33 records the owner's ruling and what it costs. The hand
dispatch of a point set stays.

## Commits

| sha | Subject |
| --- | --- |
| ac463a5 | refactor(pr-land): drop the full-tier and gate-file rules (L33) |
| 727c2c4 | ci: drop the required bounds job and the full operability tier (L33) |
| 3e88de8 | docs: log L33, CI measures nothing on the runner, and retire the tier docs |

## Owner ruling (recorded verbatim in L33)

On the runner measurement on CI: "this shit doesn't matter". To "What should be cut from the CI
measurement?": "Drop all runner measurement", whose option text was "Delete both full and bounds,
and remove bounds from the required jobs. The timeouts and budgets stay frozen at the values already
measured. Nothing re-checks them."

## What changed

- **pr.land.** Removed `check_full_tier`, `full_tier_refusals`, `full_tier_path`, `gate_refusals`,
  `parse_changed_files`, `FULL_TIER_*`, `GATE_PATHS`, `GATE_FLAG` and `--owner-approves-gate-change`.
  The Makefile's `PR_LAND_FLAGS` had no other use and is gone; the recipe is back to its form before
  L28. The new test `test_land_requires_exactly_the_jobs_required_jobs_txt_lists` reads the real
  file and checks two things. A run with every listed job green lands, and the runner gets no other
  call. A run missing any one listed job is refused by name.
- **CI.** ci.yml lost `bounds` and the `image` job's `docker save` and upload steps, which only fed
  it. `required-jobs.txt` now lists `test (3.12)`, `vendor-bundle` and `image`. operability.yml
  lost `schedule`, `pull_request` and the `followup-plan`, `followup` and `verdict` jobs. `set` is now
  a required input and `run-name` is `operability: ${{ inputs.set }}`.
- **Docs.** L33 is new. L08, L26, L27, L28 and L31 got superseded notes. HOW_TO_DEVELOP.md's pr.land
  paragraph changed, and the two tier headings in RESULTS.md got a note each. In PR #26's body,
  the Landing section changed and nothing else did.

## Deviations from Plan

- **[Rule 1, wording] L33 says `503`, not `504`.** The brief said a slow-down would show as `504` /
  `cost_model.miss`. `app.py:577-594` answers a `BuildTimeout` with a `503` of type `timeout` and
  logs `cost_model.miss`, so L33 says `503`. L33 also covers a memory overrun: `worker.replaced`, a
  `503 pool_broken`. Its ASSUMPTION is that the OOM killer picks the worker and not the server.
- **Commit order.** I put pr_land first and CI second. Removing the ci.yml `bounds` job first would
  break the `GATE_PATHS` derivation test, which is a pr_land test, in the CI commit.

## Kept, and why

- `bench/oper.py` is the bench harness, which the owner said to keep. That includes `check`,
  `followup-matrix`, `verdict`, `run --followup-from`, `FOLLOWUP_TIMEOUT_MIN` and their offline
  tests. No workflow runs these any more. Some of its comments still describe the jobs.
  Kept because I was unsure.
- `bench/points/full.json` and `tests/data/oper_boundary.json` stay because `oper_sets --check` and
  `prediction-drift` regenerate both. `full.json` can also still be dispatched. The boundary file's
  shard and estimate tests stay; `_shard_list` now reads the file, not the ci.yml matrix.
- The ci.yml `prediction-drift` step in `test (3.12)` is a record of the float tolerance that
  `--check` uses, not a tier. Kept.
- ci.yml-wide trust checks (no secret, no `github-token`, no base-context trigger) were moved out
  of the old bounds test into `test_ci_holds_no_secret_and_never_runs_in_the_base_context`.
- `test_the_half_is_the_measure_jobs_timeout_in_the_workflow` stays because the `measure` job
  stays.

## Debt

- Resolved (moot): `docs/tech_debt/resolved/2026-10-31-full-tier-follow-up-job-never-run-on-the-runner.md`,
  in 727c2c4.
- Not filed: the removed guard. The owner accepted that risk in L33.
- Active items that name a tier. Their substance is unchanged:
  - `2026-10-30-build-time-corpus-is-mostly-refused-by-the-cost-model.md` says "the runner tiers
    ... judge admitted boundary points, so this is not a gap in the gate". That premise no longer
    holds.
  - `2026-10-05-shared-infra-extraction.md`: its second trigger was pr_land's L27 rule, which is
    now removed. Its INDEX row still names it.
  - `2026-10-31-bolt-fine-peak-budget-above-the-worker-headroom.md`: its evidence is full-tier
    readings, and one trigger is "an admitted bolt read above the headroom". Nothing reads one on
    CI now.
  - `2026-10-29-in-wall-parts-the-kernel-refuses.md` cites "the bound tier" as measured on the
    shipped sweep. That is history.

## Verification

- `make verify`: `5094 passed in 199.38s`; ruff clean, mypy 97 files, contracts 10 kept.
- CI run 41278874522 on 3e88de8: `success`. Its jobs are `vendor-bundle`, `image` and
  `test (3.12)`, all success. No `bounds` job ran, and no `operability` run started on the head.

## Self-Check: PASSED

- The three commits are ancestors of HEAD.
- The resolved debt file exists, and the active one is gone.
- `required-jobs.txt` holds the three jobs.
