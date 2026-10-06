# Wall `main` the way spur does: a ruleset plus `make pr.land`

Date: 2026-10-05
Status: done — L08 (Phase 1); the ruleset is applied by the owner after the Phase 1 merge (plan 01-10)
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
Done. The code and the record landed in Phase 1: `scripts/pr_land.py`,
`scripts/skip_tokens.py`, `.github/workflows/required-jobs.txt` and the `no-skip-token`
hook, logged as L08. What remains is the repository ruleset, a setting outside git that the
owner applies after the Phase 1 PR merges: the commands are in `docs/HOW_TO_DEVELOP.md` §9.
