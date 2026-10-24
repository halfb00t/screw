# No test holds that a nut outside the measured range is still a 200 from the API

Severity: must
Status: active
Date: 2026-10-24
Source: /gsd-secure-phase 06 (T-06-15), run inside /gsd-verify-work 06
Related files:
- tests/test_calc.py:1346
- src/screw/calc/printability.py:41
- .planning/phases/06-printed-pair-acceptance/06-07-PLAN.md (threat T-06-15)
- .planning/phases/06-printed-pair-acceptance/06-SECURITY.md

## Context
T-06-15's mitigation plan names two controls for a nut with d outside M6 to M12: the warning
adds a sentence only (rows and other warnings unchanged), and the API answers 200. The first is
held by `test_the_measured_range_warning_changes_no_row_and_keeps_the_warning_order`, which calls
`derive()` directly. No test calls `/api/nut/info` or `/api/nut/model.stl` for an out-of-range
nut. 06-07-SUMMARY's Threat Flags cite "the 200 on the API" as if it were tested.

A probe on 2026-10-24 at cc955e6 shows the behaviour is right today:
`GET /api/nut/info?d=5&pitch=0.8&s=8&m=4.7` returns 200 with the sentence
"d 5 mm is outside M6 to M12, the sizes the clearance default was measured on (L17, run
06-print-run-1)".

## Why it matters
L02: a parameter the user did not set must never silently change the part, and a warning must
not become a refusal. A later change that turns the range sentence into a 422 (for example, moving
it into a validator) would pass `make verify`.

## Next step
Add one API test beside `test_a_part_below_the_printability_threshold_still_builds`
(tests/test_calc.py:1464): GET `/api/nut/info` and preview `/api/nut/model.stl` for d=5, assert
200 and exactly one range sentence. Revisit at the next edit to the nut warnings, or before the
first release (after Phase 7).
