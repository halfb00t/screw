---
phase: 03
review: 03-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: blocker
    disposition: fixed
    title: "A tiny pitch makes the model validator raise OverflowError, so the API answers 500 and the CLI prints a traceback instead of a 422"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "#d= (an empty hash value) silently opens the default part, and the records say such a link is refused"
  - id: WR-02
    severity: warning
    disposition: deferred
    title: "The fine-STL refusal applies the right-hand cap to left-hand parts and says L11 measured it over the export budget; the measured quantity is raw plus gzip, not the STL"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "The root-radius message offers the largest pitch for this d with 6 significant figures, and the printed value is itself refused for about half of all diameters"
  - id: WR-04
    severity: warning
    disposition: deferred
    title: "Root radii up to about 1e-4 mm pass validation and the kernel then fails with a generic message, so above 0 is not the real boundary"
  - id: WR-05
    severity: warning
    disposition: deferred
    title: "A valid, in-cap request with default pitch (d=100&length=200) exceeds both interim backstops; the records and the bench corpus do not say so"
  - id: WR-06
    severity: warning
    disposition: fixed
    title: "The hand test cannot see a tail segment of the wrong hand, and the volume gate cannot either"
  - id: IN-01
    severity: info
    disposition: deferred
    title: "derive() prints numbers for a length the builder is known to refuse"
  - id: IN-02
    severity: info
    disposition: fixed
    title: "A comment in _serve is now attached to the wrong code"
  - id: IN-03
    severity: info
    disposition: deferred
    title: "check_solid ignores the volume estimator's own error estimate"
  - id: IN-04
    severity: info
    disposition: fixed
    title: "Redundant assertion in the grid cell test"
open: 0
total: 11
recorded: 2026-10-11T00:20:00Z
---

# Phase 03: Code Review Disposition

Owner ruling 2026-10-10 (execute-phase code-review gate): "Fix mechanical now, defer the rest" — CR-01, WR-01, WR-03, WR-06, IN-02, IN-04 fixed by `gsd-code-fixer` (03-REVIEW-FIX.md); WR-02, WR-04, WR-05, IN-01, IN-03 deferred, each into its own `docs/tech_debt/active/` item for a measurement or a rule decision the owner makes.

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | blocker | fixed | c28de09: turns_of returns inf on OverflowError; tests at pitch=5e-324 and pitch=1e-310/length=1e5 across maths, params (turn_cap), both API routes (422) and the CLI (exit 2); 9 fail with the fix reverted; re-checked by the orchestrator (ValidationError turn_cap; CLI exit 2) |
| WR-01 | warning | fixed | e48b8ac: the given !== '' exemption dropped in app.js, pinned assertion updated in tests/test_parity.py, one sentence added to the resolved record; source-text pin only, browser check goes to the end-of-phase UAT |
| WR-02 | warning | deferred | needs a measurement or a rule decision (key rows by hand, or reword to what L11 measured): docs/tech_debt/active/2026-10-11-fine-stl-cap-applies-right-hand-rows-to-left-hand-parts.md (must) |
| WR-03 | warning | fixed | 78cc346: the printed largest pitch is truncated to 6 significant figures and re-checked by the same rule; sweep test over d 0.1..199.9 feeds every printed value back in; orchestrator re-check: 0 of 1999 printed values refused |
| WR-04 | warning | deferred | needs the smallest buildable root radius measured and set as an INTERIM floor: docs/tech_debt/active/2026-10-11-root-radius-floor-is-not-the-kernel-boundary.md (must) |
| WR-05 | warning | deferred | needs an owner severity ruling (blocker vs D-18 must) and a measurement at the 30 s kill point: docs/tech_debt/active/2026-10-11-default-pitch-d100-length200-exceeds-both-interim-backstops.md (must) |
| WR-06 | warning | fixed | 7799d2b: the hand test probes base, translated copy and tail of M6x20 and the folded d=3.5/pitch=0.6/length=5.4 case; the tail mutant fails at z 18.25 and 3.75, source restored |
| IN-01 | info | deferred | MIN_TAIL_MM move plus an info-document warning: docs/tech_debt/active/2026-10-11-info-document-prints-numbers-for-a-length-the-builder-refuses.md (nice) |
| IN-02 | info | fixed | cca06d3: the request_id comment sits above request_id again |
| IN-03 | info | deferred | return and check the volume error estimate, or record in L12 that it is unused: docs/tech_debt/active/2026-10-11-check-solid-ignores-the-volume-error-estimate.md (nice) |
| IN-04 | info | fixed | aef047d: the redundant built == len(lengths) assertion and its counter deleted |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
