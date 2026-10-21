---
phase: 05
review: 05-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "A valid nut with across-flats below 1.73 mm fails to build with an unactionable error"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "`cell_verdict` returns `proven` when a control reading, or the nut body, is NaN"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "`prove` prints a `closed_control` it never compared, against its own contract"
  - id: WR-04
    severity: warning
    disposition: fixed
    title: "At clearance of about d/2 or more the proof prints a negative \"closed form\" volume as its reason"
  - id: WR-05
    severity: warning
    disposition: fixed
    title: "`engagement_turns` in the pair report is float division; `screw info` uses the exact quotient"
  - id: WR-06
    severity: warning
    disposition: fixed
    title: "The shipped-solid evidence row fails for any off-row nut with d >= 10 mm"
  - id: IN-01
    severity: info
    disposition: fixed
    title: "The countersink-factor comment misstates the smallest `da_max / d`"
  - id: IN-02
    severity: info
    disposition: deferred
    title: "A fillet ring can overhang the head's flats with no warning"
  - id: IN-03
    severity: info
    disposition: deferred
    title: "`screw pair` exit codes collide with the exit codes of failures"
  - id: IN-04
    severity: info
    disposition: deferred
    title: "Brittle or low-value tests in the pair and CLI suites"
open: 0
total: 10
recorded: 2026-10-21T07:32:33.000Z
---

# Phase 05: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | fixed | 4edaf3e fix(05-20): build a nut narrower than sqrt(3) mm across flats |
| WR-02 | warning | fixed | fcdc0ab fix(05-20): never believe a pair reading or nut body that is not finite |
| WR-03 | warning | fixed | 4aa0126 fix(05-20): print the control's closed form only where the rule compared it |
| WR-04 | warning | fixed | 0db1b73 fix(05-20): read nothing when the proof body cannot hold the void |
| WR-05 | warning | fixed | 946e730 fix(05-20): report the pair's engagement as the exact quotient |
| WR-06 | warning | fixed | 83e5b77 fix(05-20): give an off-row nut's evidence bolt the nut's own s |
| IN-01 | info | fixed | 4218e54 docs(05-20): correct the smallest da_max / d the countersink factor cites |
| IN-02 | info | deferred | docs/tech_debt/active/2026-10-21-fillet-ring-can-overhang-the-head-flats.md (must) |
| IN-03 | info | deferred | docs/tech_debt/active/2026-10-21-screw-pair-exit-codes-collide-with-failure-exits.md (must) |
| IN-04 | info | deferred | docs/tech_debt/active/2026-10-21-brittle-pair-and-cli-tests.md (nice) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
