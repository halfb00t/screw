# The infrastructure forked from spur is not a shared package

Severity: nice
Status: active
Date: 2026-10-05
Source: L07, the owner's brief for `/gsd-new-project`
Related files:
- Makefile
- .github/workflows/ci.yml
- pyproject.toml (tooling blocks)
- docs/architecture/decision_log.md (L07, the full copy list)

## Context
screw copies spur's infrastructure (gate, hooks, CI, pool/records/app/cli shells, bench
harness, static viewer) instead of depending on a package both repos import. Two copies of
the same code now exist, and will diverge.

## Why it matters
A fix in one repo's copy is not a fix in the other's. Until the trigger fires this is
cheaper than a third repository with a guessed API; after it fires, every shared fix is
done twice or missed once.

## Next step
Revisit the first time a fix has to land in both repos (the trigger L07 names). Then:
extract the files that are byte-identical or differ only in the parameter-model type into a
shared package, log it as a new `Lxx`, and resolve this item in the same commit.
