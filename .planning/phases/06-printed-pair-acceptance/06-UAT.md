---
status: testing
phase: 06-printed-pair-acceptance
source: [06-VERIFICATION.md]
started: 2026-10-23T16:58:06Z
updated: 2026-10-23T16:58:06Z
---

## Current Test

Test 1: the page shows the phase-6 warnings.

## Tests

### 1. Page renders the printability and measured-range warnings (06-09 Task 2)
expected: On http://127.0.0.1:8000 (make serve):
- bolt ISO 4017 M3 (or d=3, pitch=0.5): the warning panel shows "d 3 mm is below d_min 4 mm and pitch 0.5 mm is below P_min 0.7 mm: ... parameters left as set"
- a nut with d=5 (e.g. M5): the panel shows "d 5 mm is outside M6 to M12, the sizes the clearance default was measured on (L17, run 06-print-run-1)"
- bolt ISO 4017 M8 x 16 and its matching nut: neither sentence appears
result: [pending]

## Summary

total: 1
passed: 0
issues: 0
pending: 1
skipped: 0

## Gaps
