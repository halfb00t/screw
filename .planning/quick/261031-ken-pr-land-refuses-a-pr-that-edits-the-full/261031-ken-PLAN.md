---
phase: quick-261031-ken
plan: 01
type: quick
branch: gsd/phase-07-operability-re-sweep
---

# Quick 261031-ken: pr.land refuses a PR that edits the files deciding the full-tier verdict

Written by the orchestrator. No planner agent was spawned. The phase 7 security audit found
that `check_full_tier` picks the full-tier run by its title, `operability: full`, and that title,
the jobs and the judge all come from the PR's own checkout. `FULL_TIER_PATHS` does not cover
`.github/workflows/operability.yml` or the bench code and data that produce and judge the
readings, so a PR can edit them until its own run passes. The owner ruled: "Add as threat,
mitigate (Recommended)".

## What decides the full-tier verdict (read from operability.yml, 2026-10-31)

Every `run:` step in operability.yml is `python -m bench.oper <cmd>`: `matrix`, `run`,
`summarize`, `followup-matrix`, `run --followup-from` and `verdict --set full`. For a bolt or nut
point, `bench.oper run` starts the production image with the checkout's `bench/` mounted
read-only at `/probe/bench` and runs `bench.oper_child` in it (`bench/oper.py` line 386); the
child imports `bench.oper_lift` for those kinds. `bench/__init__.py` holds `host_facts`, which
`bench.oper` imports. `full.json` holds the points, their timeouts and their limits, which the
verdict judges against. So the guarded files are:

- `.github/workflows/operability.yml`
- `bench/__init__.py`
- `bench/oper.py`
- `bench/oper_child.py`
- `bench/oper_lift.py`
- `bench/points/full.json`

Left out, each with its reason. `bench/oper_bound.py`, `bench/oper_load.py` and
`bench/thread_spike/` run only for bound, load and probe points, and `full.json` has none: 972
bolt and 84 nut points. A test pins that, so adding such a point to `full.json` also forces the
module onto the list. `bench/oper_sets.py` and `bench/oper_fit.py` write and fit point files, but
the run never imports them. `tests/data/oper_boundary.json` is read by `bench.oper check` in
ci.yml's required tier, not by the full tier. The image (`Dockerfile`, `src/`) is the system
under test, and L27 already covers it.

## Task 1: the rule, its tests, and the make variable

- `scripts/pr_land.py`: a constant `GATE_PATHS` and a pure `gate_refusals(changed,
  owner_approves)` next to `full_tier_refusals`. `check_full_tier` applies it to the changed
  files it already reads, before the `FULL_TIER_PATHS` early return, so the files are read once.
  The refusal names the touched files and the flag. `land(..., owner_approves_gate_change=False)`
  and `main` get `--owner-approves-gate-change`. The default refuses.
- `Makefile` `pr.land`: pass `$(PR_LAND_FLAGS)` through, so the owner runs
  `make pr.land PR=N PR_LAND_FLAGS=--owner-approves-gate-change`. Without it the tool cannot be
  run as `make pr.land`, which the module docstring says is its only entry point.
- `tests/test_pr_land.py`:
  - refused without the flag, on PR A's recorded files (#22 touched operability.yml and
    bench/oper.py);
  - allowed with the flag;
  - unaffected when the diff touches none of the files;
  - each guarded file on its own is refused;
  - `land()` refuses with no merge call, and merges with the flag;
  - a drift test derives the list from operability.yml: the `python -m` modules it runs, the
    child module `bench.oper` starts, their `bench` import closure through `ast` with the three
    kind-only modules excluded and pinned to `full.json`'s kinds, and the set the verdict reads.
  - `_happy_runner` gets a non-gate files list, because PR A's real list now trips the rule.
- `docs/HOW_TO_DEVELOP.md` section 8: one sentence for the rule and the flag.

## Task 2: L28

The convention: a new entry supersedes or extends, and the old entry gets only a pointer line
under its heading (L08's "Extended by L27"). L28 records the rule, the list and its reasons, and
the override. L27 gets "Superseded in part by L28", for its claim that the list decides, and L08
gets "Extended by L28".

## Verify

`make verify` must pass. Commit through the hook with a 600000 ms timeout, then push. PR #26
stays a draft. PR #26 touches every guarded file, so landing it needs the override.
