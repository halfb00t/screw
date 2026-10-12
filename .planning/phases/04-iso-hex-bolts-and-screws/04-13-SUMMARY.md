---
phase: 04-iso-hex-bolts-and-screws
plan: 13
subsystem: ui
tags: [web, picker, badge, info-panel, notes, ui-spec, tabl-01, tabl-05, tabl-06, tabl-07, info-03, info-05]

requires:
  - phase: 04-iso-hex-bolts-and-screws
    provides: "04-11/04-12: the info document with designation, preset, notes and a group on every row; GET /api/presets?kind= (axes, rows with picker strings and mm fields)"
provides:
  - "info panel: designation h2, one h3 + dl per row group in server order, every value as String(row.value) plus unit"
  - "notes as p.note after the warnings, held with the mesh like warnings (pendingNotes / meshNotes)"
  - "preset picker: three selects (Standard, Size, Length) built from /api/presets, a pick writes the row's mm fields and builds at once"
  - "preset-match badge: matches <display> / custom, based on <display> / custom, composed from info.preset.status and display"
  - "01-UI-SPEC.md amended: anatomy, copywriting, rules 1, 10, 13, 15, 19, 20, 22-24, 29, new rules 30-33, UI considerations E9-E14, OI-1 resolved"
  - "tech debt 2026-10-06-ui-rounds-displayed-numbers resolved"
affects: [04-14, end-of-phase UAT, verify-work]

actuals:
  tokens: 15487
  tasks: 2
  commits: 2
plan_head_before: c497ea65bb408b9d4949f934b3f24cd06439da31
plan_head_after: b127473e1a4ccd294290a9ebbfb60e2c6da1cce8

tech-stack:
  added: []
  patterns:
    - "the catalogue is fetched once per kind change inside navigate(), under the formSeq guard, and a failed fetch refuses the link whole"
    - "page-session state (presetBasis) that never reaches the hash, query or a request, pinned by source assertions on partQuery, writeHash and the list of fetch URLs"
    - "UI-SPEC rule numbers grow by appending (30-33) rather than renumbering, so the earlier cross-references stay valid"

key-files:
  created: []
  modified:
    - src/screw/static/app.js
    - src/screw/static/index.html
    - src/screw/static/style.css
    - tests/test_parity.py
    - .planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md
    - docs/tech_debt/INDEX.md
    - docs/tech_debt/resolved/2026-10-06-ui-rounds-displayed-numbers.md

key-decisions:
  - "The badge basis is the last row the part matched exactly, not only the last pick (see Deviations)"
  - "A failed /api/presets fetch refuses the link whole through refuseLink instead of leaving a form without its picker"
  - "A change to the blank option is not a pick: the selects return to what the fields match"
  - "Resolved-in for the tech debt item is 'this commit' plus the subject, the convention of 04-02 and 04-05; a commit cannot contain its own sha"

patterns-established:
  - "Source assertions read function bodies by name (_function_body) to prove a symbol is absent from partQuery and writeHash"

requirements-completed: []  # the browser-only half of TABL-01/05/06 and INFO-03/05 is the end-of-phase UAT; phase.complete reconciles traceability

duration: about 1 h
completed: 2026-10-12
status: complete
---

# Phase 4 Plan 13: The page shows the catalogue, the badge and the unrounded document Summary

**The web page prints the API's numbers as sent under the designation and the row groups, shows the notes beside the warnings, and picks an ISO 4014/4017 size and length from three selects with a preset-match badge; the UI contract is amended to say so.**

## Accomplishments

- **Task 1 (`d671ee5`).** `renderInfo` writes `${String(row.value)} ${row.unit}`.trim() and the rounding helper is gone, so a valid 0.0004 reads `0.0004 mm` (the debt item's own example) and the default across-corners row reads `11.547005383792515 mm`. The panel opens with the `h2` designation when `info.designation` is a string, then one `h3` and `dl` per distinct `row.group` in first-seen order (a `Map`, the `buildForm` pattern); `#dims` is a `div`. `info.notes` render as `p.note` after the warnings and, like warnings, belong to the mesh: `pendingNotes` becomes `meshNotes` only in `showModel`, and every error call passes `mesh ? meshNotes : []`. CSS adds `#dims h2`, `#dims h3` (the legend's role, no new size or weight) and `#messages .note` (muted on `--bg`; contrast computed 4.62 light, 6.86 dark). Tech debt `2026-10-06-ui-rounds-displayed-numbers` moved to `resolved/` with its INDEX row, in the same commit.
- **Task 2 (`b127473`).** `#picker` (legend `ISO preset`) and `#badge` in the aside. `loadPresets` fetches `api/presets?kind=` once per kind change after `buildForm`, under the `formSeq` guard, and builds one select per `catalogue.axes` entry with a blank first option; the Size and Length lists are the distinct `picker[1]` / `picker[2]` of the rows matching the earlier choices, in catalogue order. A change resolves to one complete row (later blank or no-longer-offered selects take their first offered value), writes every entry of `row.fields` through `write(fields.get(name).input, value)` (left-hand is not in `fields`), and calls `update()` at once. After each info document the selects show the exact-match row or blank, and the badge reads `matches <display>`, `custom, based on <display>` or `custom`. `navigate()` clears the basis; `partQuery`, `writeHash` and every fetch URL never read it or a row id.
- **UI contract (`01-UI-SPEC.md`).** Dated note at the top; Page Anatomy rows for `#picker`, `#badge`, `#dims`, `p.note`; Typography and Color rows; Copywriting rows for the legend, axes, blank option, option strings, the three badge forms, the designation, groups, always/exact-only rows, notes, the new standing warning, thread_length / short-thread / no-row / fine-STL warnings, `head_too_small`, `thread_length_conflict`, the turn-cap text and the catalogue-fetch error; Interaction rules 1, 10, 13, 15, 19, 20, 22, 23, 24, 29 amended and new rules 30 to 33 for the picker and badge; UI Considerations E9 to E14 (43 to 68 rows: resolved 52 = 36 explicit + 16 backstop, dismissed 13, unresolved 3); OI-1 marked resolved; extension rules 2 and 3 updated. Strings were taken from the live API documents and the schema, not from memory.

## Verification (what was and was not run)

- `make verify` exits 0 on HEAD `b127473`: ruff, mypy `--strict`, import-linter, unfinished-work scan, **2619 passed**, coverage 97.57% (floor 96.0%). The pre-commit hook ran the same gate on each commit and passed. Baseline before this plan: 2615 passed; the 4 new tests are in `tests/test_parity.py`.
- Task-level checks from the plan all pass: `grep -c toFixed app.js` is 0, `String(row.value)` present, `<div id="dims">`, `#messages .note`, the INDEX row under `## Resolved`, `api/presets?kind=`, `custom, based on `, `id="picker"`, `id="badge"`, the UI-SPEC strings.
- A mutation check: putting `presetBasis` into `partQuery` made `test_the_badge_composes_...` fail; reverted.
- A throwaway node harness (kept in the scratchpad, not the repo) extracted the picker functions from `app.js`, stubbed the DOM, and drove them against the live 294-row catalogue. It showed: build with 3 axes; exact match fills `ISO 4017 / M6 / 20` and the badge; picking ISO 4014 keeps M6 and takes the first offered length 30; M10 then takes 45, then 80 writes `{d 10, pitch 1.5, length 80, s 16, k 6.4, thread_length 26}`; custom blanks the selects and reads `custom, based on ISO 4014 M10 × 80`; picking from the blank state fills the first size and length; a bracketed row shows `ISO 4017 / (M3.5) / 8` and `matches ISO 4017 (M3.5) × 8`; a blank pick resyncs and does not build; M12 keeps length 80, M5 falls to 25.
- **No browser was available.** Nothing below was observed on screen: layout, light and dark contrast, the hash after a pick, the interleaving of the info and STL fetches, real `select` behaviour. JS has no unit runner; the parity source assertions and the harness above are the proof. The two plan human checks run in the end-of-phase UAT.

## Task Commits

1. **Task 1: The panel shows the designation, the groups, the notes and the API's numbers unrounded** - `d671ee5` (fix)
2. **Task 2: Pick a standard, size and length on the page, see the badge, and amend the UI contract** - `b127473` (feat)

## Deviations from Plan

### Auto-fixed / judgement calls

**1. [Rule 1 - Bug avoided] The badge basis follows the last exact match, not only the last pick**
- **Found during:** Task 2 design.
- **Issue:** with the basis set only in the pick handler, pick M10 x 80, edit Length to 90 (itself a catalogue row, badge `matches ISO 4014 M10 × 90`), then edit again would read `custom, based on ISO 4014 M10 × 80`, a stale row; the same after Reset (`matches ISO 4017 M6 × 20`, next edit "based on" the earlier pick). That is a misleading badge, the kind of plausible wrong output L02 forbids.
- **Fix:** `showMatch` also sets `presetBasis = info.preset` whenever the document is exact; a pick still sets it from the picked row; `navigate()` still clears it. Consequence: editing the default part (empty hash) reads `custom, based on ISO 4017 M6 × 20`, not `custom`. A reloaded link whose fields match no row still reads `custom`, as pinned. No nearest-row inference is added.
- **Where written down:** UI-SPEC rule 33 and the Copywriting badge row. **Flag for the verifier:** this is broader than the plan's "after a pick" wording; revert is one line if the owner wants the literal rule.

**2. [Rule 2 - Missing critical functionality] A failed catalogue fetch refuses the link**
- **Issue:** the plan says a failed fetch "shows no picker and the startup/navigation error path". Left to throw after `buildForm`, the form of the new kind would sit under the old `currentKind`.
- **Fix:** `navigate()` catches it and calls `refuseLink('Could not load the part: <status>')`; `refuseLink` now also calls `clearPicker()`, so no select is left to pick into a cleared form (a pick there would dereference a missing field). The plan's "refuseLink empties the badge and blanks the selects" became "removes the picker and empties the badge"; the `fail` path blanks the selects as planned. Pinned: `clearPicker();` added to the refuseLink statements in the parity test.

**3. [Judgement] A change to the blank option is not a pick**
- The plan does not say. The selects return to what the fields match and nothing is built.

**4. [Plan wording] Plan text vs. facts**
- The plan's expected across-corners string is `11.547005383792516`; the API sends and JavaScript prints `11.547005383792515` (checked with node and Python). The human-check text in the plan is off by one digit; the UI-SPEC and the debt resolution use the real value.
- The plan's key-link pattern `preset\.status` would not match `info.preset?.status`, so the code is `preset !== null && preset.status === 'exact'`.
- The parity test allows exactly `status`, `display` and `id` as keys read off a preset member: the plan says "status and display and no other key", but step 2 also needs `id` to select the matching row; the badge text itself uses the first two only.
- `#picker` has no CSS rule of its own: the global `fieldset`, `legend` and `.field` rules already lay it out like the form's fieldsets, and an empty rule would be noise. `#badge` has one.

## Issues Encountered

None. Neither commit was rejected by the hook.

## Known Stubs

None.

## Threat Flags

None beyond the plan's register. T-04-21: all new nodes use `createElement`, `Object.assign` with `textContent`, or `new Option`; `test_the_ui_builds_nodes_from_text_only` still passes. T-04-22: `presetBasis` is cleared in `navigate()` and absent from `partQuery` / `writeHash` by assertion; the test also lists the only four fetch URLs the page builds.

## What a human should check in a browser (end-of-phase UAT)

1. `make serve`, empty hash: selects read `ISO 4017 / M6 / 20`; badge `matches ISO 4017 M6 × 20`; panel heading `Hexagon head screw ISO 4017 - M6 x 20`, groups `Shank and thread`, `Head`, `Part`; `Across corners, geometric (s / cos 30°)` reads `11.547005383792515 mm`; the grade note shows after the standing warning in its own style, in light and dark.
2. Pick `ISO 4014` / `M10` / `80`: the hash carries only mm fields (no preset), `Left-hand thread` is untouched, the part rebuilds at once, badge `matches ISO 4014 M10 × 80`, `Hexagon head bolt ISO 4014 - M10 x 80` as heading plus the wrench note.
3. Edit Length to 75: badge `custom, based on ISO 4014 M10 × 80`, selects blank. Edit it to 90: `matches ISO 4014 M10 × 90` (deviation 1). Reset: `matches ISO 4017 M6 × 20`. Reload an edited link: `custom`.
4. Pitch 0.75: row values, designation and notes go; the no-row warning shows; badge `custom`. Pick a bracketed size (`(M3.5)`): it shows bracketed in the select and the badge.
5. Make a request fail (length 10 with Thread length 30): the error shows with the last mesh's warnings and notes below it.
6. Long labels (`Bearing face diameter, min (ISO 4014:2022 Table 2)`) wrap in the panel; the 820px layout holds.

## Filing

No tech-debt or idea item was filed. One item was resolved and moved (`docs/tech_debt/resolved/2026-10-06-ui-rounds-displayed-numbers.md`).

## Self-Check: PASSED

- FOUND: commits `d671ee5` and `b127473` (ancestors of HEAD).
- FOUND: `docs/tech_debt/resolved/2026-10-06-ui-rounds-displayed-numbers.md`, absent from `active/`; INDEX row under `## Resolved`.
- FOUND: `src/screw/static/app.js`, `index.html`, `style.css`, `tests/test_parity.py`, `01-UI-SPEC.md` modified as listed.
- `make verify`: exit 0, 2619 passed, coverage 97.57%.
