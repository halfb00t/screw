---
phase: 01
review: 01-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "A collapsed thin solid passes the validity check and is served as a 200 with a wrong or missing mesh"
  - id: WR-01
    severity: warning
    disposition: open
    title: "A repeated query key silently drops one of two explicit values"
  - id: WR-02
    severity: warning
    disposition: open
    title: "`int_env` clamps zero and negative values to 1 instead of falling back, against its own docstring"
  - id: WR-03
    severity: warning
    disposition: open
    title: "The per-build timeout counts queue wait, so a build that never overran is reported as overrunning and kills its worker"
  - id: WR-04
    severity: warning
    disposition: open
    title: "The STL tessellation is absolute millimetres, so a very small part is silently a coarse prism"
  - id: WR-05
    severity: warning
    disposition: open
    title: "The UI's number formatter prints a wrong magnitude for a large `pitch`, and `pitch` has no upper bound"
  - id: WR-06
    severity: warning
    disposition: open
    title: "`bench.memory sweep` returns success and prints a peak for a run where every request failed"
  - id: WR-07
    severity: warning
    disposition: open
    title: "`screw export` leaves a raw traceback for an unwritable output path, and validates parameters only after loading the kernel"
  - id: IN-01
    severity: info
    disposition: open
    title: "`quality` is accepted on STEP, does nothing, and doubles the build"
  - id: IN-02
    severity: info
    disposition: open
    title: "`slug()` uses `%g`, so distinct parts get the same download name"
  - id: IN-03
    severity: info
    disposition: open
    title: "The `Accept-Encoding` test ignores `q=0` and case"
  - id: IN-04
    severity: info
    disposition: open
    title: "A malformed `#d=abc` link and an emptied field build the default silently"
  - id: IN-05
    severity: info
    disposition: open
    title: "CI and delivery nits"
open: 13
total: 13
recorded: 2026-10-06T08:02:17.921Z
---

# Phase 01: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | open | - |
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| WR-04 | warning | open | - |
| WR-05 | warning | open | - |
| WR-06 | warning | open | - |
| WR-07 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
