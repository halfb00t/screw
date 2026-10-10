---
phase: 02
review: 02-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: open
    title: "`verdict --campaign PREFIX` also reads campaigns whose prefix merely extends PREFIX"
  - id: WR-02
    severity: warning
    disposition: open
    title: "`--k-from` and `--frontier-from` accept incomplete records"
  - id: WR-03
    severity: warning
    disposition: open
    title: "The quiet gate decides `decisive` once, at the start of each block"
  - id: WR-04
    severity: warning
    disposition: open
    title: "A mixed-hand cell reads \"violated\" without the nut body being checked"
  - id: WR-05
    severity: warning
    disposition: open
    title: "A run is recorded under the HEAD sha without checking the harness is committed"
  - id: IN-01
    severity: info
    disposition: open
    title: "`_head()` has no `cwd` and is read after the run"
  - id: IN-02
    severity: info
    disposition: open
    title: "`PAIR_TIMEOUT_S` does not follow from the numbers in its own comment"
  - id: IN-03
    severity: info
    disposition: open
    title: "A bad request line kills the worker instead of returning a failure record"
  - id: IN-04
    severity: info
    disposition: open
    title: "The status returns of `Build`, `MakeSolid` and `VolumeProperties_s` are ignored"
  - id: IN-05
    severity: info
    disposition: open
    title: "The oracle docstring overclaims independence from the builder"
  - id: IN-06
    severity: info
    disposition: open
    title: "An oversized integer in an edited JSONL escapes the refusal path"
  - id: IN-07
    severity: info
    disposition: open
    title: "The reference worker's kernel is not recorded"
open: 12
total: 12
recorded: 2026-10-09T02:43:53.790Z
---

# Phase 02: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| WR-04 | warning | open | - |
| WR-05 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |
| IN-06 | info | open | - |
| IN-07 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
