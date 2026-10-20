---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 10
subsystem: calc-and-ui
tags: [calc, info-document, counterpart, ui, ui-spec, r10]
requires:
  - phase: 05-09
    provides: "the nut info document (Thread, Nut, Pair groups), the limits group, iso4032 and iso4017 rows keyed on exact ISO 262 (d, pitch)"
provides:
  - "calc/__init__.py Counterpart(kind, fields: dict[str, float | bool]) and PartInfo.counterpart on every bolt and nut info document"
  - "calc/presets.py counterpart_for(p) -> (Counterpart, off-row warning | None)"
  - "static/index.html #counterpart anchor; app.js showCounterpart, dropMesh, write with v ?? ''"
  - "01-UI-SPEC.md rules 34 to 36, rule 20 closed, E15 to E18, the Phase 5 Copywriting rows"
affects: [05-11, 05-17, 05-18]
requirements-completed: [TYPE-04, PAIR-01]
estimate_ref: "110000 tokens, 3 tasks"
actuals:
  tokens: 20500
  tasks: 3
  commits: 3
plan_head_before: 4d31ebbd886a7e9c069c216760d8692820f3b98e
plan_head_after: 65f74f45487470d8e6dc327c76e66e5f7079f6fe
tech-stack:
  added: []
  patterns:
    - "the page builds the matching-part link from info.counterpart.kind and .fields alone (URLSearchParams on an object), so a new kind needs no JS edit"
    - "a kind change drops the mesh in navigate(), so the selector and the link share one path (R10)"
key-files:
  created: []
  modified:
    - src/screw/calc/__init__.py
    - src/screw/calc/presets.py
    - src/screw/static/app.js
    - src/screw/static/index.html
    - src/screw/static/style.css
    - tests/test_calc.py
    - tests/test_api.py
    - tests/test_parity.py
    - .planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md
key-decisions:
  - "The off-row counterpart warning is appended last on the document, after the download refusals, so the existing no-row warning keeps its place"
  - "R10 is applied in navigate()'s kind-change branch (dropMesh before buildForm), not only in the selector's handler, so the Matching link, which goes through hashchange, drops the stale mesh too"
  - "The #counterpart link is muted Caption text, not the accent: UI-SPEC Color reserves the accent for primary actions and invalid fields"
status: complete
---

# Phase 5 Plan 10: The matching part, the empty-clearance traps and the UI contract Summary

Every bolt and nut info document now names the part that mates with it, printed alike by the API and the CLI, and the page offers it as one generic `Matching <kind>` link; a field with no default opens empty, a kind change drops the old mesh, and 01-UI-SPEC.md records all of it.

## Task commits

| Task | Commit | Message |
| ---- | ------ | ------- |
| 1 | 9757396 | feat(info): add the matching part to every info document |
| 2 | ad687c7 | feat(ui): link the matching part and start a defaultless field empty |
| 3 | 65f74f4 | docs(ui-spec): record the nut, the pair rows and the matching-part link |

## What was built

**Task 1.** `Counterpart(kind, fields)` with `fields: dict[str, float | bool]` (the smart union keeps the hand a JSON boolean) and `PartInfo.counterpart`. `counterpart_for(p)` in `calc/presets.py` looks the exact ISO 262 size up and takes, for a bolt, the GOST ISO 4032-2014 row's `s` and `m_max`, for a nut the ISO 4017 head's `s` and `k` (the same in both grades); d, pitch and left_hand always carry; `clearance`, `length` and `thread_length` never do. Off a row the document's last warning reads `no GOST ISO 4032-2014 (ISO 4032:2012) row for d 6.5 pitch 1; set s and m on the nut` or `no ISO 4017:2022 row for d 6.5 pitch 1; set s, k, length and thread_length on the bolt`. An ISO 4017 M7 bolt is off the nut rows (the GOST text prints no M7). Tests: default bolt and nut, both hands, off-row and M7, one float off a row, the excluded fields, a round trip for all 14 nut rows (`NutParams(**fields, clearance=0.1)` reads preset `iso4032:<size>`), the nut-to-bolt follow, the wire document, and the API = CLI counterpart.

**Task 2.** `<a id="counterpart" hidden>` under the badge; `showCounterpart(info.counterpart ?? null)` sets `href` to `#` plus `new URLSearchParams({ kind: counterpart.kind, ...counterpart.fields })` and the text to `Matching ` plus the kind, and hides the link on a failed update or a refused link. `write` uses `v ?? ''`. `dropMesh()` runs where `navigate()` sees a kind change. Parity tests: the `info.*` set gains `counterpart`, `counterpart.*` is exactly `{kind, fields}`, no kind name is quoted, `v ?? ''` is pinned, the R10 drop is pinned in order (before `buildForm`), and the nut and pair row keys plus `m` and `clearance` are checked unread by name.

**Task 3.** 01-UI-SPEC.md: a Phase 5 amendment note; Page Anatomy, Typography and Color for `#counterpart`; Copywriting rows for the nut fields and groups, the limits heading, the clearance and off-row warnings, the M18 note and the missing-clearance error; rule 20's ASSUMPTION closed; rules 9, 15, 19, 22, 29 amended; new rules 34 to 36; UI Considerations E15 to E18 (count now 81: resolved 64, dismissed 14, unresolved 3); Verification status; extension rule 3.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Existing tests superseded by the plan's own behaviour]** Four warning-list assertions pinned the document's last warning as the bolt no-row warning (`tests/test_calc.py` three, `tests/test_api.py` one). A bolt off an ISO 262 size now carries the counterpart's off-row warning after it, so they assert the new full list or membership. Commit 9757396.

**2. [Rule 2 - UI contract]** `style.css` gained `#counterpart { color: var(--muted); font-size: .85rem; }` (not in the plan's file list). Without it the link would be the accent colour, which 01-UI-SPEC Color reserves for primary actions and invalid fields. Recorded in the spec (Color, Typography). Commit ad687c7.

**3. [Rule 1 - Placement of R10]** The plan's wording puts the mesh drop in the kind change handler. The Matching link changes the kind through `hashchange`, not the selector, so the drop is in `navigate()`'s `kind !== currentKind` branch, which both paths reach (T-05-23 is then closed for the link too). The source assertion pins it there. Commit ad687c7.

## Known Stubs

None.

## Threat Flags

None. T-05-22 (link tampering) is mitigated: the `href` is a `URLSearchParams` of server numbers and booleans set as a property, and `innerHTML` stays absent (`test_the_ui_builds_nodes_from_text_only`). T-05-23 (stale bolt mesh shown as the nut) is mitigated by `dropMesh()` and `test_a_kind_change_drops_the_old_mesh_and_what_described_it`.

## Issues Encountered

None blocking. No browser is in the gate (L01), so the click on the link, the empty canvas after a kind change and the muted link in both themes are end-of-phase UAT items; the spec's Verification status says so. Edge ASSUMPTION carried from the plan: off a row the target kind opens with its own frozen defaults and may refuse them with a 422 naming fields, after the source document warned which fields to set. No tech-debt or idea item filed.

## Verification

`make verify`: ruff, mypy `--strict`, import-boundary contracts, unfinished-work scan, pytest; final result line `2975 passed in 93.15s`, coverage 97.87% (floor 96%). Each task commit also passed the pre-commit `make verify` hook. `.venv/bin/screw info bolt` prints `"kind": "nut"`; `grep -c "Matching <kind>"` on the UI spec prints 3; the spec has no `ASSUMPTION, plan 01-04 flagged`.

## Self-Check: PASSED

Files found: `src/screw/calc/__init__.py`, `src/screw/calc/presets.py`, `src/screw/static/app.js`, `src/screw/static/index.html`, `src/screw/static/style.css`, `tests/test_calc.py`, `tests/test_api.py`, `tests/test_parity.py`, `.planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md`. Commits found on HEAD: 9757396, ad687c7, 65f74f4.
