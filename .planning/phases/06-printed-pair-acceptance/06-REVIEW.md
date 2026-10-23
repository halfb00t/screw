---
phase: 06-printed-pair-acceptance
reviewer: codex-cli 0.163.0 (cross-CLI: the diff was written by Claude Code)
depth: standard
scope: git diff 1332178..HEAD -- src tests bench/print_rules.py (PR #19 was reviewed separately)
reviewed: 2026-10-23
critical: 0
warning: 3
info: 1
status: issues_found
---

# Phase 06 code review

Reviewer: Codex, read-only (`codex exec -s read-only`). Claude Code wrote the diff, so per AGENTS.md
it does not review it. The orchestrator reproduced WR-01 independently.

## Warnings

### WR-01: `:g` formatting makes boundary warnings numerically false (L02)
- File: `src/screw/calc/printability.py:59` (also line 32, the D-09 sentence)
- `printability_warning(3.999999, 0.7)` prints "d 4 mm is below d_min 4 mm";
  `pitch=0.6999999` prints "pitch 0.7 mm is below P_min 0.7 mm"; `measured_range_warning(5.999999, ...)`
  prints "d 6 mm is outside M6 to M12". A printed number is a number someone cuts metal to.
- Fix: format with round-trip precision (`repr`/`!r`, or `:.17g` trimmed) and test the full text
  just below each edge.
- Reproduced by Codex (API, CLI) and by the orchestrator (direct call).

### WR-02: "built as asked" promises a build that other rules may refuse
- File: `src/screw/calc/printability.py:65`
- Bolt `d=3, pitch=0.5, length=1e-9` carries both "this part is not built" and "built as asked";
  `build()` raises `BuildError`.
- Fix: say the warning leaves parameters unchanged, without promising a build; align L18's wording.
- Reproduced by Codex.

### WR-03: test leaves a fake `b"x"` in the shared API export cache
- File: `tests/test_nut.py:244`
- Running the test twice in one process fails the second run (`seen == []`), and later default
  STL/STEP requests in the same process return the cached `b"x"`. Order-dependent test pollution.
- Fix: isolate/restore the export cache around the test.
- Reproduced by Codex (`--keep-duplicates`).

## Info

### IN-01: stale comments still describe clearance as required/typed-only
- Files: `src/screw/static/app.js:319`, `src/screw/static/app.js:463`, `tests/test_nut.py:1`
- Fix: describe the L17 default and `rememberTyped()` behaviour.

## Checked and clean (per Codex)
Exact thresholds at 4.0 / 0.7 / 6.0 / 12.0 behave correctly; both record digests match; NaN/inf are
rejected by model, API and CLI; `measured_range_warning` ignoring `pitch` follows R6 (diameter-only),
not a defect. UI rendering inspected in source, not in a browser.
