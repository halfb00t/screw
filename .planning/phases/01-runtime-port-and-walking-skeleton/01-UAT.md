---
status: testing
phase: 01-runtime-port-and-walking-skeleton
source: [01-VERIFICATION.md]
started: 2026-10-06T08:10:28Z
updated: 2026-10-06T08:10:28Z
---

## Current Test

number: 1
name: Seven-step browser check of the walking-skeleton page (01-04-PLAN.md Task 1)
expected: |
  Run `make serve`, open http://127.0.0.1:8000/ and walk the seven steps: the selector shows
  bolt; the form shows Diameter / Pitch / Length in that order with mm units; Diameter=8 gives
  the hash `#d=8` with no `kind=`; typing 6.0 drops `d` from the hash; clearing Length drops
  it; Diameter=100001 shows an error naming Diameter and keeps the last part on screen;
  `#kind=nut` shows an error naming nut and builds nothing; the copied link round-trips to the
  same part; the STL and STEP downloads open. The preview renders a cylinder; the info panel
  lists Diameter, Pitch, Length, Volume (closed form) and the standing walking-skeleton warning.
awaiting: user response

## Tests

### 1. Seven-step browser check of the walking-skeleton page (01-04-PLAN.md Task 1)
expected: Each of the seven steps behaves as written above; the preview renders a cylinder; the info panel lists Diameter, Pitch, Length, Volume (closed form) and the standing walking-skeleton warning.
result: [pending]

### 2. Stale responses never render while typing or switching kind (01-04 edge FRNT-02 concurrency, backstop)
expected: Type quickly through several Diameter values and switch the kind selector mid-flight; the preview, the info panel and the hash always show the last value entered, never an earlier response arriving late.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
