---
status: testing
phase: 05-hex-nut-and-kernel-pair-proof
source: [05-VERIFICATION.md]
started: 2026-10-21T08:05:16Z
updated: 2026-10-21T08:05:16Z
---

## Current Test

number: 1
name: Nut preset with an empty clearance shows no part
expected: |
  Run `make serve` and open http://127.0.0.1:8000. Choose kind nut and pick the preset ISO 4032 M6. Leave clearance empty.
  The empty clearance field blocks the build, and no stale part is shown.
awaiting: user response

## Tests

### 1. Nut preset with an empty clearance shows no part
expected: Choosing kind nut, preset ISO 4032 M6 and an empty clearance blocks the build. No stale part is shown.
result: [pending]

### 2. Clearance 0.1 renders the nut and its panel
expected: Typing 0.1 renders a hex nut with a lead-in countersink and chamfered faces. The Pair group shows radial 0.1 mm, diametral 0.2 mm, the nut major, pitch and minor diameters, and 5.2 turns. The 6g/6H limits group carries the label "limits for a bought part; this model is nominal and not toleranced".
result: [pending]

### 3. Matching-part link round-trips both ways
expected: "Matching bolt" on the nut opens a bolt with the same d, pitch and hand. "Matching nut" on that bolt opens a nut with the same d, pitch and hand.
result: [pending]

### 4. Kind switch drops the previous mesh
expected: Switching kind while a mesh is on screen removes the old mesh before the new form builds.
result: [pending]

### 5. M18 note
expected: Picking the M18 nut preset shows "kernel pair proof inconclusive at K = 3 (2026-10-08-a-pair)" on the panel. No kernel pair proof is run.
result: [pending]

### 6. Download buttons
expected: The nut's preview STL, fine STL and STEP buttons download. The preview STL's filename contains "preview".
result: [pending]

## Summary

total: 6
passed: 0
issues: 0
pending: 6
skipped: 0
blocked: 0

## Gaps
