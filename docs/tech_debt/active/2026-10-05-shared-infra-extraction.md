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

2026-10-06: the trigger fired. `src/screw/pool.py` carries a same-slot timeout guard in
`_run_with_timeout` (Phase 1 D-16, L09) that spur still lacks: spur carries the race as its
open `must` debt, `2026-10-02-same-slot-timeout-cleanup-race-produces-undocumented-500.md`.
The fix must now land in both repos, and the two copies of `pool.py` have diverged for the
first time.

## Why it matters
A fix in one repo's copy is not a fix in the other's. Until the trigger fires this is
cheaper than a third repository with a guessed API; after it fires, every shared fix is
done twice or missed once.

## Next step
Owner decides: extract the shared package now, or fix spur by hand with the same guard and
keep the fork. Either way, when the files are extracted (those byte-identical or differing
only in the parameter-model type), log it as a new `Lxx` and resolve this item in the same
commit. Severity is unchanged: which of the two to do is the owner's call, surfaced in the
01-02 SUMMARY.
