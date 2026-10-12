---
status: diagnosed
phase: 04-iso-hex-bolts-and-screws
source: [04-VERIFICATION.md]
started: 2026-10-12T07:37:18Z
updated: 2026-10-12T08:58:15.491Z
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
note: Ruled 2026-10-12. Fixed in the session: WR-01 `27723c1`, WR-02 `505934a`, IN-01 and IN-04 `d38efef` (CR-01 `41c21ae` earlier). IN-03 skipped by the owner (as designed, D-25/D-09). IN-02 option a is the one open item: a page/API contract change, planned as gap G-04-3 below rather than patched inline.

## Summary

total: 3
passed: 2
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

- gap_id: G-04-3
  truth: "The page's Download STL link never points at a download the server will refuse: when the fine STL of the part is refused by the INTERIM export cap, the page offers the preview STL instead (labelled so) and the STEP, and the info document carries the download state as a structured field that the API and the CLI print alike"
  status: failed
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
