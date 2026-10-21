---
status: diagnosed
phase: 05-hex-nut-and-kernel-pair-proof
source: [05-VERIFICATION.md]
started: 2026-10-21T08:05:16Z
updated: 2026-10-21T09:05:17.878Z
---

## Current Test

[testing complete]

## Tests

### 1. Nut preset with an empty clearance shows no part
expected: Choosing kind nut, preset ISO 4032 M6 and an empty clearance blocks the build. No stale part is shown.
result: issue
reported: "after selecting nut, I can't choose standard, size with empty Clearance"
severity: major
note: "Screenshot: Standard and Size selects are empty after switching kind to nut. GET /api/presets?kind=nut returns rows (ISO 4032 M2...), so the picker is not populated client-side."

### 2. Clearance 0.1 renders the nut and its panel
expected: Typing 0.1 renders a hex nut with a lead-in countersink and chamfered faces. The Pair group shows radial 0.1 mm, diametral 0.2 mm, the nut major, pitch and minor diameters, and 5.2 turns. The 6g/6H limits group carries the label "limits for a bought part; this model is nominal and not toleranced".
result: pass
note: \"M6 values typed by hand (d 6, pitch 1, s 10, m 5.2); preset picker broken, see test 1.\"

### 3. Matching-part link round-trips both ways
expected: "Matching bolt" on the nut opens a bolt with the same d, pitch and hand. "Matching nut" on that bolt opens a nut with the same d, pitch and hand.
result: issue
severity: major
owner_request: "Yes, I do want." (the bolt-to-nut link should carry a clearance)
reported: "1. yes 2. opened the nut, but clearence was empty so nut wasn't rendered; left-hande check worked"
note: "d, pitch and hand round-trip both ways (pass). The issue is the owner's request that the bolt-to-nut link carry a clearance. That conflicts with locked D-01 / L15 (clearance has no default before Phase 6, PAIR-02), so it needs an owner ruling or an L15 amendment before any fix plan."

### 4. Kind switch drops the previous mesh
expected: Switching kind while a mesh is on screen removes the old mesh before the new form builds.
result: pass

### 5. M18 note
expected: Picking the M18 nut preset shows "kernel pair proof inconclusive at K = 3 (2026-10-08-a-pair)" on the panel. No kernel pair proof is run.
result: pass
note: "M18 values typed by hand (d 18, pitch 2.5, s 27, m 15.8); preset picker broken, see test 1."

### 6. Download buttons
expected: The nut's "Download STL" and "Download STEP" links download the fine builds; neither filename contains "preview". A link falls back to preview, labelled "(preview)", only when the server refuses fine (D-10, G-04-3).
result: pass
note: "The original expected text named three buttons (preview STL, fine STL, STEP). The user reported: I don't see any preview stl and fine stl, just download stl and download step. That is the intended two-link UI (D-10), so the expected text was corrected and the test re-run."

## Summary

total: 6
passed: 4
issues: 2
pending: 0
skipped: 0
blocked: 0

## Gaps

- gap_id: G-05-1
  truth: "Choosing kind nut, preset ISO 4032 M6 and an empty clearance blocks the build. No stale part is shown."
  status: failed
  reason: "User reported: after selecting nut, I can't choose standard, size with empty Clearance"
  severity: major
  test: 1
  root_cause: "A pick writes the row's fields and calls update(). With clearance empty, /api/nut/info answers 422, and fail() calls showMatch(null). showPicks then blanks every select, and Size has no options while Standard is blank. Every pick snaps back to blank. The fields keep the first row (d 2, pitch 0.4, s 4, m 1.6, as the screenshot shows: Standard ISO 4032 auto-picked Size M2). The catalogue fetch is fine: GET /api/presets?kind=nut returns the rows."
  artifacts:
    - path: "src/screw/static/app.js"
      issue: "fail() (update loop) calls showMatch(null), so the selects drop the user's pick on any 422, including the expected missing-clearance 422"
    - path: "src/screw/static/app.js"
      issue: "pick() resolves a row and writes its fields, but the selects' state depends only on the next info document"
  missing:
    - "Keep the picked row in the selects when the build is refused only for a field the row does not define (the nut's clearance), or match the fields against the catalogue client-side on failure"
    - "A browser-level test: kind nut, empty clearance, pick ISO 4032 then M6; the selects keep ISO 4032 / M6, the fields hold M6, nothing builds"
  debug_session: ""

- gap_id: G-05-3
  truth: "The bolt-to-nut matching link opens a nut that renders, which means the link carries a clearance."
  status: failed
  reason: "User reported: opened the nut, but clearence was empty so nut wasn't rendered. Owner then asked for the link to carry a clearance: Yes, I do want."
  severity: major
  test: 3
  decision_conflict: "D-01 / L15: clearance is required with no default before Phase 6 (PAIR-02). A fix needs an owner ruling on which value the link carries, then an L15 amendment."
  owner_ruling: "2026-10-21: option 'last typed clearance'. The page remembers the clearance last typed on a nut in this tab and carries it on the bolt's Matching nut link; with none typed the link stays empty. No invented number. Needs an L15 amendment logged before or with the fix."
  root_cause: "By design today: showCounterpart builds the link from info.counterpart, and the bolt's counterpart carries d, pitch and left_hand only (D-01, D-02). The bolt has no clearance field to carry."
  artifacts:
    - path: "src/screw/static/app.js"
      issue: "showCounterpart: the link carries only the fields the server names, so the nut opens with clearance empty"
    - path: "docs/architecture/decision_log.md"
      issue: "L15 / D-01 states the empty clearance on the link; needs the 2026-10-21 amendment"
  missing:
    - "L15 amendment for the owner's ruling"
    - "Page-local memory of the last typed nut clearance (not in the bolt's hash, never sent to the API for the bolt) added to the Matching nut href"
    - "A test: type 0.1 on a nut, follow Matching bolt, then Matching nut; the nut opens with clearance 0.1 and renders. A fresh tab with no typed clearance opens the nut empty."
