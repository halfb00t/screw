---
status: testing
phase: 04-iso-hex-bolts-and-screws
source: [04-VERIFICATION.md]
started: 2026-10-12T07:37:18Z
updated: 2026-10-12T07:37:18Z
---

## Current Test

number: 1
name: The six browser steps of plan 04-13 (picker cascade, badge transitions, panel groups and notes, light and dark)
expected: |
  Empty hash: selects read ISO 4017 / M6 / 20, badge `matches ISO 4017 M6 × 20`, heading is the
  designation `Hexagon head screw ISO 4017 - M6 x 20`, groups Shank and thread / Head / Part in that
  order, `Across corners, geometric (s / cos 30°)` reads `11.547005383792515 mm`, the standing
  warning first and the note `product grade A (ISO 4017:2022: l ≤ 150 mm and l ≤ 10 d)` after it
  in its own style, in light and dark. Pitch 0.75: row values vanish, the no-row warning appears,
  the note goes, badge `custom, based on ISO 4017 M6 × 20` (rule 33: the basis is the last exact
  match, so NOT plain `custom`; 04-13-SUMMARY step 4 is stale on this). Pick ISO 4014 / M10 / 80:
  d 10, pitch 1.5, length 80, s 16, k 6.4, thread_length 26 filled, Left-hand thread untouched,
  rebuild at once, badge `matches ISO 4014 M10 × 80`, hash carries mm fields only. Edit Length
  to 75: `custom, based on ISO 4014 M10 × 80`, selects blank; Length 90: `matches ISO 4014 M10 × 90`
  (a real row with the same b). Reset: `matches ISO 4017 M6 × 20`. Reload a link with an edited
  field: plain `custom`, selects blank. A second-choice size shows bracketed, e.g. `(M7)`, in the
  Size select and in the badge. Long labels wrap at 820px.
awaiting: user response

## Tests

### 1. The six browser steps of plan 04-13 (picker cascade, badge transitions, panel groups and notes, light and dark)
expected: As above (from 04-VERIFICATION.md behavior_unverified_items 1 and 2 and human item 1).
result: [pending]
note: Orchestrator pre-run 2026-10-12 (Chrome via MCP, dark theme only, `screw serve --port 8001` at commit afb9d04): every step above was observed as expected, with Length 82 for the off-row edit; light theme, contrast and the 820px wrap were not looked at. This is evidence for the owner, not a substitute for the owner's run.

### 2. Download STL on a long ISO 4017 preset (e.g. ISO 4017 M20 x 200, or M8 x 70)
expected: Decide whether the current behaviour is acceptable: the info panel warns that the fine STL is refused, the Download STL link then returns a 422 JSON body; the preview STL and the STEP of the same part are served. 62 of the 186 ISO 4017 presets (21% of the 294-row catalogue) are in this state under the INTERIM 64 MiB export budget (D-21, L13; 04-REVIEW IN-02).
result: [pending]

### 3. Rule on the open code-review findings WR-01, WR-02, IN-01, IN-02, IN-03, IN-04 (04-REVIEW-DISPOSITION.md)
expected: Each is fixed, filed as a docs/tech_debt item with the owner's sign-off, or skipped by the owner. CR-01 (the one blocker) is already fixed in 41c21ae.
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
