---
schema_version: 1
open_count: 1
waived_count: 0
fixed_count: 0
total_count: 1
last_updated: 2026-10-31T02:15:49.140Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 07 | unrun-verify | .github/workflows/operability.yml |  | the full tier's followup job (R5 re-reads on 5 runner instances) has not run on the runner: no point of runs 41155746591 or 41158301476 reached its timeout after the margin, so it was skipped; it is tested offline only (tests/test_oper_followup.py) | open |  | 2026-10-31T02:15:49.140Z |  |

````json
[
  {
    "id": 1,
    "kind": "unrun-verify",
    "phase": "07",
    "file": ".github/workflows/operability.yml",
    "line": null,
    "description": "the full tier's followup job (R5 re-reads on 5 runner instances) has not run on the runner: no point of runs 41155746591 or 41158301476 reached its timeout after the margin, so it was skipped; it is tested offline only (tests/test_oper_followup.py)",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-31T02:15:49.140Z",
    "resolved_at": null,
    "milestone": null
  }
]
````
