# Enji Guard not connected

Severity: nice
Status: active
Date: 2026-10-05
Source: agent-scaffold run, step 7; the owner chose to skip, as in spur
Related files:
- .github/workflows/ci.yml

## Context
The scaffold offers continuous AI auditing (security, dependency hygiene, test coverage,
AI-readiness) through Enji Guard, connected as a GitHub App at https://guard.enji.ai/app
with findings landing as issues and reviewable PRs. Connecting is the owner's OAuth click
in a browser, not scriptable. The owner skipped it on 2026-10-05, matching spur's
standing choice (`spur docs/tech_debt/active/2026-09-21-enji-guard-not-connected.md`).

## Why it matters
`make verify` and CI check what the repo's own tools check. Nothing watches dependency
advisories or audits the tree from outside; a vulnerable pin in `requirements.txt` is
found by whoever reads the advisory, not by the gate.

## Next step
Revisit when the first product code lands on `main`, or when the owner decides they want
continuous audit: open https://guard.enji.ai/app, connect `halfb00t/screw`, run the free
initial audit, then resolve this item.
