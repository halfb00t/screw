---
phase: "04"
slug: "iso-hex-bolts-and-screws"
status: approved
shadcn_initialized: false
preset: none
created: "2026-10-12"
contract: "../01-runtime-port-and-walking-skeleton/01-UI-SPEC.md"
---

# Phase 04 — UI Design Contract (pointer)

This phase has no UI contract of its own. The page contract is
`.planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md`, amended in place by the
plan that changed the page, as that file's extension rule 3 and its Phase 3 note (plan 03-05,
D-19) require. One file holds the rules for every phase so a rule number means the same thing in
every plan, summary and `tests/test_parity.py` assertion.

What plan 04-13 amended there (commits `d671ee5`, `b127473`; see `04-13-SUMMARY.md`):

- Page Anatomy, Typography and Color: the preset picker (`#picker`, three selects), the badge
  (`#badge`), the grouped info panel (`#dims`) and the notes (`p.note`).
- Copywriting Contract: the picker legend, axes, blank option and option strings; the three
  badge forms; the designation, group headings, always-shown and exact-only rows and notes; the
  new standing warning; the `thread_length`, short-thread, no-row and fine-STL warnings;
  `head_too_small`, `thread_length_conflict`, the turn-cap text and the catalogue-fetch error.
- Interaction rules 1, 10, 13, 15, 19, 20, 22, 23, 24 and 29 amended; rules 30 to 33 added
  (picker and badge). Rule 33 records the badge basis as shipped: the last row the part matched
  exactly, not the last pick. That is wider than the plan's "after a pick" wording and is flagged
  for the verifier in `04-13-SUMMARY.md`.
- UI Considerations E9 to E14: 68 rows, 52 resolved, 13 dismissed, 3 unresolved (the picker
  shows no loading indicator while `/api/presets` is in flight is the new one).
- Open Issues: OI-1 (browser-side rounding) resolved; the debt item moved to
  `docs/tech_debt/resolved/2026-10-06-ui-rounds-displayed-numbers.md`.
- Verification status: no browser ran in plan 04-13. The picker, badge, panel and notes are
  pinned by `tests/test_parity.py` source assertions and a throwaway node harness. The six-step
  browser check in `04-13-SUMMARY.md` is the Phase 4 UAT item.

This file exists so the execute-phase `ui.safety-gate` finds a `*-UI-SPEC.md` in the phase
directory; it carries no rule of its own. Amend `01-UI-SPEC.md`, not this file.
