---
status: complete
phase: 01-runtime-port-and-walking-skeleton
source: [01-VERIFICATION.md]
started: 2026-10-06T08:10:28Z
updated: 2026-10-06T08:28:30.978Z
---

## Current Test

[testing complete]

## Tests

### 1. Seven-step browser check of the walking-skeleton page (01-04-PLAN.md Task 1)
expected: With `make serve` running, at http://127.0.0.1:8000/ — (1) the selector shows bolt, the form shows Diameter / Pitch / Length in that order with mm units, the preview renders a cylinder, the info panel lists Diameter, Pitch, Length, Volume (closed form) and the standing walking-skeleton warning; (2) Diameter=8 gives the hash `#d=8` with no `kind=`; (3) typing 6.0 drops `d` from the hash and clearing Length drops `length`; (4) Diameter=100001 shows an error naming Diameter and keeps the last part on screen; (5) `#kind=nut` shows an error naming nut and builds nothing; (6) the copied link round-trips to the same part and the STL and STEP downloads open; (7) typing several Diameter values within a second leaves only the last value's preview and panel. Source: 01-04-PLAN.md Task 1 human-check.
result: pass

### 2. Stale responses never render while typing or switching kind (01-04 edge FRNT-02 concurrency, backstop)
expected: Type quickly through several Diameter values; the preview, the info panel and the hash always show the last value entered, never an earlier response arriving late.
result: pass
note: Scoped to rapid typing — `KINDS` registers only `bolt` (`src/screw/params.py:88`), so the kind-switch half of 01-VERIFICATION.md behavior_unverified_items[1] could not be exercised and stays deferred until a second kind exists (Phase 5).

## Summary

total: 2
passed: 2
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
