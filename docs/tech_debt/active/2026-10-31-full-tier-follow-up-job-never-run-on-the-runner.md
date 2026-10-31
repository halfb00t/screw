# The full tier's follow-up job has never run on the runner

Severity: nice
Status: active
Date: 2026-10-31
Source: plan 07-19 (L26); its tracer asked for R5's follow-up jobs to judge a within-margin point
on 5 runner instances
Related files:
- .github/workflows/operability.yml (`followup-plan`, `followup`, `verdict`)
- bench/oper.py (`followup_points`, `followup_shards`, `verdict`, `run --followup-from`)
- tests/test_oper_followup.py (the offline tests of all of them)

## Context
R5 re-reads a full-tier point at repetitions 1 to 5 when its single cold wall x (1 + m) reaches
its timeout. In the first full run, 41155746591 (dispatch, records committed), no point came
close: the largest cold wall was 0.397 of its timeout (iso4017:M20x200, stl-fine), or 0.611 of it
after the margin. `followup-plan` selected nothing and the `followup` job was skipped, in that
run and in 41158301476, the first `pull_request` run. That job's YAML, its image build, its artifact download and
`run --followup-from` have been tested offline only. A synthetic point that would make it run
would be a point file written outside `bench.oper_sets` (R30), so none was made.

## Why it matters
The first run that needs a follow-up is the first run of that job. If it breaks there, `verdict`
still fails the tier, because a selected point with no follow-up reading is `unread`. So the
failure is loud and not silent, but it would come on a PR the full tier is guarding.

## Next step
Revisit when a full-tier run first selects a follow-up point: read that run's `followup` jobs and
`verdict`, and resolve this item with the run id.
