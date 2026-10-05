# Wall `main` the way spur does: a ruleset plus `make pr.land`

Date: 2026-10-05
Source: agent-scaffold run; deliberately left out of the foundation
Related files:
- .github/workflows/ci.yml
- docs/HOW_TO_DEVELOP.md

## Context
spur (L22, L25 there) lands `main` only through `make pr.land`: a GitHub ruleset requires
the listed checks green on a head that is current with `main` and refuses direct pushes;
a commit-msg hook refuses the six GitHub Actions skip tokens; `scripts/pr_land.py` proves
the squash commit got its own CI run. screw ships with the CI mirror only.

## Why it matters
The wall is what makes "every commit on `main` has a green run" a property instead of a
habit. Without it a hand merge or a `[ci skip]` subject can land unverified code.

## Next step
Once the first phase has landed by PR: enable the ruleset (spur's `docs/HOW_TO_DEVELOP.md`
§8 has the exact `gh api` calls), port `scripts/pr_land.py` and `scripts/skip_tokens.py`
with their tests, add `.github/workflows/required-jobs.txt`, log it as a new `Lxx`.
