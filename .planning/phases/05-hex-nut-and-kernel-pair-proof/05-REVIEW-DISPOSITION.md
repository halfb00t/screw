---
phase: 05
review: 05-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: open
    title: "A valid nut with across-flats below 1.73 mm fails to build with an unactionable error"
  - id: WR-02
    severity: warning
    disposition: open
    title: "`cell_verdict` returns `proven` when a control reading, or the nut body, is NaN"
  - id: WR-03
    severity: warning
    disposition: open
    title: "`prove` prints a `closed_control` it never compared, against its own contract"
  - id: WR-04
    severity: warning
    disposition: open
    title: "At clearance of about d/2 or more the proof prints a negative \"closed form\" volume as its reason"
  - id: WR-05
    severity: warning
    disposition: open
    title: "`engagement_turns` in the pair report is float division; `screw info` uses the exact quotient"
  - id: WR-06
    severity: warning
    disposition: open
    title: "The shipped-solid evidence row fails for any off-row nut with d >= 10 mm"
  - id: IN-01
    severity: info
    disposition: open
    title: "The countersink-factor comment misstates the smallest `da_max / d`"
  - id: IN-02
    severity: info
    disposition: open
    title: "A fillet ring can overhang the head's flats with no warning"
  - id: IN-03
    severity: info
    disposition: open
    title: "`screw pair` exit codes collide with the exit codes of failures"
  - id: IN-04
    severity: info
    disposition: open
    title: "Brittle or low-value tests in the pair and CLI suites"
open: 10
total: 10
recorded: 2026-10-21T03:33:37.749Z
---

# Phase 05: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| WR-04 | warning | open | - |
| WR-05 | warning | open | - |
| WR-06 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
