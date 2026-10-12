---
status: diagnosed
phase: 04-iso-hex-bolts-and-screws
source: [04-VERIFICATION.md]
started: 2026-10-12T07:37:18Z
updated: 2026-10-12T13:40:47Z
---

## Current Test

[testing complete]

## Tests

### 1. The six browser steps of plan 04-13 (picker cascade, badge transitions, panel groups and notes, light and dark)
expected: As above (from 04-VERIFICATION.md behavior_unverified_items 1 and 2 and human item 1).
result: pass
note: Orchestrator pre-run 2026-10-12 (Chrome via MCP, dark theme only, `screw serve --port 8001` at commit afb9d04): every step above was observed as expected, with Length 82 for the off-row edit; light theme, contrast and the 820px wrap were not looked at. This is evidence for the owner, not a substitute for the owner's run.

### 2. Download STL on a long ISO 4017 preset (e.g. ISO 4017 M20 x 200, or M8 x 70)
expected: Decide whether the current behaviour is acceptable: the info panel warns that the fine STL is refused, the Download STL link then returns a 422 JSON body; the preview STL and the STEP of the same part are served. 62 of the 186 ISO 4017 presets (21% of the 294-row catalogue) are in this state under the INTERIM 64 MiB export budget (D-21, L13; 04-REVIEW IN-02).
result: pass

### 3. Rule on the open code-review findings WR-01, WR-02, IN-01, IN-02, IN-03, IN-04 (04-REVIEW-DISPOSITION.md)
expected: Each is fixed, filed as a docs/tech_debt item with the owner's sign-off, or skipped by the owner. CR-01 (the one blocker) is already fixed in 41c21ae.
result: issue
reported: "fix all; IN-02 a, IN-03 a"
severity: minor
note: Ruled 2026-10-12. Fixed in the session: WR-01 `27723c1`, WR-02 `505934a`, IN-01 and IN-04 `d38efef` (CR-01 `41c21ae` earlier). IN-03 skipped by the owner (as designed, D-25/D-09). IN-02 option a is the one open item: a page/API contract change, planned as gap G-04-3 below rather than patched inline. G-04-3 closed by plans 04-15 and 04-16 (`90ad513`, `afeffd8`, `31a4596`, `ac91249`); re-verified 2026-10-12 in 04-VERIFICATION.md (re_verification, 9/10).

### 4. The browser steps of plan 04-16 Task 1 (Download STL (preview), tooltip, saved file, Download STEP, disabled state)
expected: As in Current Test above (04-VERIFICATION.md behavior_unverified_items 1 and human item 1). The verifier ran the real setDownloads from app.js under node on a stub DOM and the four cases held; that is evidence, not the browser run.
result: pass

### 5. The page in the light theme and in a window narrower than 820px (plans 04-13 and 04-16)
expected: Picker, badge, grouped panel, notes and the downloads row (longest label `Download STL (preview)`, 22 characters) wrap cleanly and keep contrast in both themes (04-VERIFICATION.md human item 2; UAT test 1 was pre-run in the dark theme only).
result: issue
reported: "this part doesn't look clean"
severity: minor
note: Screenshot (light theme, 2026-10-12 19:23 local) of the info panel for ISO 4017 M8 x 70: the full-precision values (`0.6765823467065926 mm`, `6.646835306586815 mm`, `15.011106998930268 mm`, `3670.874961137891 mm³`) do not wrap or shrink, so `15.011106998930268 mm` runs into the `Head height` label of the next cell and the labels beside them wrap one word per line (`Thread / depth / (ISO / 68- / 1:2023 / basic / profile)`). Short values (`13 mm`, `12.73 mm`) lay out fine. Full precision is by design (L02; the 2026-10-06 rounding debt item was resolved in 04-13), so the fix is the row layout, not the number.

### 6. Rule on the open findings of the incremental code review of the gap closure: WR-03, IN-05, IN-06, IN-07, IN-08 (04-REVIEW-DISPOSITION.md, open: 5)
expected: Each is fixed, filed under docs/tech_debt/ with the owner's sign-off, or skipped by the owner. None is a must-have failure; WR-03 is the one warning (the rule 17 test checks a Python copy of the algorithm, not app.js).
result: pass
note: Owner typed pass (2026-10-12) without naming a disposition per finding; the five rows stay `open` in 04-REVIEW-DISPOSITION.md until a ruling is written there.

## Summary

total: 6
passed: 4
issues: 2
pending: 0
skipped: 0
blocked: 0

## Gaps

- gap_id: G-04-3
  truth: "The page's Download STL link never points at a download the server will refuse: when the fine STL of the part is refused by the INTERIM export cap, the page offers the preview STL instead (labelled so) and the STEP, and the info document carries the download state as a structured field that the API and the CLI print alike"
  status: resolved
  resolved_by: 04-16-PLAN.md
  resolved_at: 2026-10-12
  reason: "User reported: fix all; IN-02 a, IN-03 a"
  severity: minor
  test: 3
  root_cause: "The info document has no structured download state: `download_refusal` (src/screw/calc/__init__.py) is applied only at the model routes and in `screw export`, and `derive` adds the refusal only as warning text. The page builds both download links with a fixed `quality=fine` for the STL (src/screw/static/app.js, the Download STL anchor) and may not match warning text (D-10), so it cannot know the fine STL will be a 422 for 62 of the 294 catalogue rows (ISO 4017 presets under the INTERIM 64 MiB cap, D-21, L13)."
  artifacts:
    - path: "src/screw/calc/__init__.py"
      issue: "PartInfo carries the refusal as a warning sentence only; no per-format/quality download state"
    - path: "src/screw/static/app.js"
      issue: "the Download STL link is always `model.stl?...&quality=fine`; nothing switches it to the preview STL when fine is refused"
    - path: "src/screw/cli.py"
      issue: "`screw info` prints the document as served, so the new field must appear there too (FRNT-05 parity)"
    - path: ".planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md"
      issue: "the Copywriting and Interaction contract for the download buttons has no refused-fine state"
  missing:
    - "A structured `downloads` member on PartInfo (per format and quality: served, or refused with the reason), computed by `download_refusal` so the two paths cannot disagree"
    - "The page builds the two download links from that member and offers `Download STL (preview)` when the fine STL is refused; no string matching in app.js (D-10)"
    - "CLI `screw info` parity for the field; tests on calc (the 62 refused presets), API, CLI and the parity assertions; 01-UI-SPEC.md amended in the same plan"
  debug_session: ""
- gap_id: G-04-5
  truth: "Picker, badge, grouped panel, notes and the downloads row wrap cleanly and keep contrast in both themes; a full-precision value in the info panel stays inside its cell and its label stays readable"
  status: failed
  reason: "User reported: this part doesn't look clean"
  severity: minor
  test: 5
  root_cause: "src/screw/static/style.css lays out each info row as a single-line flex box whose value cannot shrink: `#dims div { display: flex; justify-content: space-between; gap: .75rem }` (line 186, default `flex-wrap: nowrap`), `#dims dd { white-space: nowrap }` (line 189, flex-item default `min-width: auto` so the value's minimum width is its whole string, 179.2 px for `15.011106998930268 mm`), and `#dims dt` (line 188) has no sizing so it is the only item that shrinks, down to its longest word. In a `repeat(auto-fill, minmax(12.5rem, 1fr))` track (line 182; 200-256 px at most widths) the label collapses to one word per line and, once value + 12 px gap + longest label word exceeds the track, the row overflows into the next cell. Reproduced in headless Chrome at HEAD 1c612e0, light theme, 720 px viewport: 3 tracks of 213.3 px, `15.011106998930268 mm` ends 43.2 px past its cell and 19.2 px into `Head height` (179.2 + 12 + 65.3 - 213.3 = 43.2). Not narrow-only: overflow also at 821, 1280, 1536, 1600, 1680, 1920 and 2560 px; none at 375, 1024, 1366, 1440 (labels still squeezed to 4 lines at 1440). The rules date from plan 01-04 (8fd0ab0) when values were rounded; plan 04-13 (d671ee5) made them full precision by design (L02) and added the long cited labels, which exposed the defect. The dark theme block sets colours only, so both themes share the geometry. No test reads style.css or pins a `#dims` rule."
  artifacts:
    - path: "src/screw/static/style.css"
      issue: "lines 182, 186, 188, 189: single-line flex row (`nowrap`), unshrinkable `dd` (`white-space: nowrap`, `min-width: auto`), unsized `dt` that absorbs the whole shortfall"
    - path: ".planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md"
      issue: "lines 78, 362, 364: Page Anatomy says `label left and value right in each row`; E10 overflow and long-text rows note that `dd` is `nowrap` and may overrun, as a later visual check, not a layout rule"
  missing:
    - "Change the row layout, not the number (L02: full precision stays): let label and value stop sharing a line when they do not fit — `flex-wrap: wrap` on `#dims dl div` with the value pushed right (differential V7: no overflow at any width, values whole); optionally `dt { flex: 1 1 7rem }` so short values stay beside their labels, plus `dd { white-space: normal; overflow-wrap: anywhere }` only as the last-resort guard for a value wider than a whole track (V8: no overflow at 680-1920 px, long values drop whole under the label, the 25-character longest valid value `0.00010825317547305484 mm` breaks only at the space before `mm`)"
    - "Do not use `min-width: 0` alone (V1, V5: identical or worse), `overflow-wrap: anywhere` inside the single-line row (V4: splits digits, e.g. `14.3 / 8 mm`, a misreading risk under L02) or a wider column alone (V6: only moves the threshold)"
    - "Amend 01-UI-SPEC.md Page Anatomy and E10 (overflow, long-text) in the same plan; add a guard the gate can run, since no test covers the CSS today (e.g. a style.css source pin in tests/test_parity.py for the `#dims` row rules)"
  debug_session: ".planning/debug/info-panel-full-precision-value-overflows-cell.md"
