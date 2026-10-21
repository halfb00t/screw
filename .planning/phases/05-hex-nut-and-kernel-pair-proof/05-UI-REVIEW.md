# Phase 05 — UI Review

**Audited:** 2026-10-21
**Baseline:** 01-UI-SPEC.md (amendments by Phase 5 plans 05-10, 05-18, 05-19, 05-21, 05-22)
**Screenshots:** Not captured (no dev server on localhost:3000, 5173, 8080)
**Interaction captures:** off (workflow.ui_interaction_capture is false)

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 4/4 | All Phase 5 strings present and exact; no generic labels; nut warnings follow contract patterns |
| 2. Visuals | 4/4 | Counterpart link placed correctly under #badge; form groups and panel structure follow spec |
| 3. Color | 4/4 | Counterpart link is muted Caption text; accent reserved for primary actions; no hardcoded colors |
| 4. Typography | 4/4 | Counterpart link uses Caption role (.85rem); no new sizes or weights added to scale |
| 5. Spacing | 4/4 | All spacing uses declared tokens; counterpart margins conform to scale |
| 6. Experience Design | 2/4 | lastTyped memory keyed by wrong kind during switch (WR-07); Reset/link do not clear stale values (WR-08) |

**Overall: 21/24**

---

## Top 3 Priority Fixes

1. **WR-07: BLOCKER — Typed clearance stored under old kind during kind switch** — User can trigger `Unknown field "clearance" for kind "bolt"` error if they switch kinds while typing. Use `formKind` (set in `buildForm`) as the memory key instead of `currentKind` (which updates after async `loadPresets`).

2. **WR-08: WARNING — Reset and links don't clear stale memory values** — After Reset, the Matching nut link carries a clearance the field no longer shows. Implement `forgetUntyped(name, written)` to delete memory entries when Reset or a link overwrites a field with a different value.

3. **Update UI-SPEC rule 37** — Add clarification that `lastTyped` should be keyed by the kind whose form is on screen (not `currentKind`), and that entries should be deleted when Reset or a link writes a field empty or to a new value, to match the contract's "stale number" language.

---

## Detailed Findings

### Pillar 1: Copywriting (4/4)

**Evidence:**

All Phase 5 copywriting from the contract is present and exact:

1. **Clearance field** (`src/screw/calc/__init__.py:353`)
   - Label: `"Clearance (radial)"` — matches UI-SPEC Copywriting Contract line
   - Help text server-provided through schema, not in static files

2. **Pair and Limits groups** (`src/screw/calc/__init__.py:66, 70`)
   - `PAIR = "Pair"` — group heading for pair-specific rows
   - `LIMITS = "limits for a bought part; this model is nominal and not toleranced"` — exactly matches UI-SPEC Copywriting line 225

3. **Matching-part link** (`src/screw/static/app.js:401` in 05-22)
   - Text: `'Matching ${counterpart.kind}'` — dynamic, no hardcoded kind name
   - No field names, group names or labels in `app.js` per contract rule 29

4. **M18 note** (`src/screw/calc/__init__.py:88`)
   - `M18_NOTE = "kernel pair proof inconclusive at K = 3 (2026-10-08-a-pair)"` — exact match to UI-SPEC Copywriting line 234

5. **Standing warning** (`src/screw/calc/__init__.py:56-57`)
   - Begins `"ends modelled per L15: bolt tip chamfer, under-head fillet on an ISO 4014 plain shank, nut lead-in countersinks and face chamfers; nominal, not toleranced; not a product build"` — exact match to UI-SPEC line 217

6. **Nut fine-STL refusal** (`src/screw/calc/thread.py`)
   - `clearance: ...` sentence (line 428-431) — names field, runs and options, begins with field name per contract line 232
   - `m: ...` sentence (line 434-437) — names field, cap, runs, offers alternatives, begins with field name per contract line 232
   - No braces in either, pydantic formats custom error

**No issues found.** All strings are server-provided, verbatim-rendered by the page, and match the contract exactly. No generic labels (OK, Submit, Click Here). Every nut-specific warning and field name comes from the API schema or backend constants, not hardcoded in static files.

---

### Pillar 2: Visuals (4/4)

**Evidence:**

Visual structure and hierarchy verified against UI-SPEC Page Anatomy and plan 05-10 amendments:

1. **Counterpart link placement** (`src/screw/static/index.html:22`)
   - Element: `<a id="counterpart" hidden></a>` immediately after `<p id="badge">`
   - Location in aside: Kind, picker, badge, counterpart, form, actions — matches rule 36 and 04-13 as amended
   - Hidden attribute correct: shown only when info.counterpart is not null (plan 05-10)

2. **Form structure**
   - Nut kind adds three new fieldsets via schema: Size, Thread, Nut, Pair (from server via `/api/schema?kind=nut`)
   - Groups built generically from `schema.properties[name].group` — no hardcoded group names in `app.js`
   - Each group becomes an `h3` legend and a `dl` in `#dims` per UI-SPEC rule 24

3. **Info panel groups and hierarchy**
   - Groups rendered in order discovered (`renderInfo` line 370-376): one `h3` per unique group, one `dl` per group
   - Pair group rows (clearance, diameters, engagement) appear after Nut rows, before Part
   - Limits group appears as separate group with its heading

4. **Clearance field in form**
   - Built as any other field: `label.field` with `.name` and `.control`
   - Input type inferred from schema (number input)
   - No default, so `write()` receives `undefined` and sets `input.value = ''` (rule 35)
   - Field is required per schema; 422 `missing` marks it `.invalid`

**No issues found.** Visual hierarchy and page anatomy follow the spec. No decorative elements, icon-only buttons, or unlabeled controls added. Nut-specific components integrate into existing generic structure.

---

### Pillar 3: Color (4/4)

**Evidence:**

Color usage verified against UI-SPEC Color rules and plan 05-10 amendments:

1. **Counterpart link** (`src/screw/static/style.css:125`)
   - CSS rule: `#counterpart { color: var(--muted); font-size: .85rem; }`
   - Applied color: `--muted` (`#677080` light, `#97a0ab` dark)
   - Rationale (plan 05-10, auto-fixed issue 2): link is not a primary action; accent reserved for primary CTAs and invalid fields
   - Matches `#badge` styling (line 123): both muted Caption text under the picker

2. **Badge and link contrast**
   - Both use `--muted on --panel` pair: 4.99:1 (light), 6.33:1 (dark) per UI-SPEC Color section
   - Meets WCAG AA for non-text; exceeds for text

3. **Form field invalid state**
   - `.field.invalid input` uses `border-color: var(--accent)` and `outline: 1px solid var(--accent)` (line 115-118)
   - Applied only when schema validation fails (422, marked by `renderError`)
   - Accent still reserved for primary actions (download buttons) and invalid indicators

4. **No hardcoded colors in Phase 5 code**
   - All colors use CSS custom properties
   - No new colors added to palette
   - No inline `style` attributes

**No issues found.** Color usage follows 60/30/10 rule and accent reservation. No new colors or hardcoded hex values introduced.

---

### Pillar 4: Typography (4/4)

**Evidence:**

Typography verified against UI-SPEC Typography and plan 05-10 amendments:

1. **Counterpart link** (`src/screw/static/style.css:125`)
   - Size: `.85rem` (13.6px) — Caption role per UI-SPEC Typography table
   - Weight: `400` (inherited, not specified) — Body weight
   - Role: caption line, muted, same as `#badge` (line 123)
   - No new size or weight added to scale

2. **Clearance field label**
   - Built by form factory: `.field .name` class applies
   - Size: `14px` (Body) — inherited from `body`
   - Weight: `500` (Label role per UI-SPEC Typography table) — applied by `.field .name { font-weight: 500; }` (line 98)
   - Matches other form field labels exactly

3. **Pair and Limits group headings**
   - Class `h3` in `#dims`, styled by `#dims h3` (line 174-181)
   - Size: `.75rem` (12px) — Group legend role
   - Weight: `600` — Group legend role
   - Text: uppercase via `text-transform: uppercase` — Group legend role
   - Letter-spacing: `.06em` — Group legend role
   - Matches Nut and Part group headings exactly

4. **Typography scale locked**
   - UI-SPEC Typography section lists five sizes: Body (14px), Label (14px), Caption (13.6px), Fine print (12.48px), Group legend (12px)
   - No new sizes or weights introduced in Phase 5
   - Designation (14px, weight 700) and Heading (17.6px, weight 700) unchanged

**No issues found.** All new UI elements reuse existing typography roles. Typography scale remains at 5 sizes, 4 weights (locked per UI-SPEC note OI-8).

---

### Pillar 5: Spacing (4/4)

**Evidence:**

Spacing verified against UI-SPEC Spacing Scale and plan 05-10 amendments:

1. **Counterpart link margins** (`src/screw/static/style.css:125`)
   - Implicit rule: `#badge { margin: .35rem 0 0; }` (line 123)
   - Applied margin for counterpart: `.35rem` top (5.6px, sub-scale exception) — separates from badge line above
   - Sub-scale exception exists in UI-SPEC Exceptions table; no new length added

2. **Badge and link in aside sequence**
   - Badge: `.35rem` top margin (line 123)
   - Counterpart: `.35rem` top margin (line 125, by being a block element after `p#badge`)
   - Gap: `.35rem` top spacing, consistent with `.field` row gap (line 96)

3. **Form group spacing**
   - Fieldset: `.75rem` top margin (md token, line 77)
   - `.field` rows: `.5rem` top and bottom margin (sm token, line 96)
   - Nut fieldsets use same spacing as Size, Thread fields

4. **No arbitrary spacing added**
   - Phase 5 code uses only declared tokens: sm (8px), md (12px), lg (16px), xl (24px), 2xl (32px)
   - No new `rem` or `px` values introduced
   - Exceptions (sub-scale values) already listed in UI-SPEC Exceptions

**No issues found.** All spacing uses declared scale. No new sub-scale lengths added for Phase 5 elements.

---

### Pillar 6: Experience Design (2/4)

**Re-audited after plans 05-21 and 05-22.** Initial findings (lines 198–244 below) remain valid for 05-21's rowOfFields behavior. However, 05-22's `lastTyped` memory implementation diverges from the amended UI-SPEC contract in two ways, both documented in the code review as WR-07 and WR-08 and confirmed by browser probes in the security audit scratch directory.

**WR-07: BLOCKER — Typed clearance keyed by wrong kind during kind switch** (`src/screw/static/app.js:678–686`, `:315`)

- **Contract promise (UI-SPEC rule 37):** `lastTyped` maps a kind to values last typed into fields of that kind
- **Actual behavior:** `rememberTyped(e.target)` uses `currentKind` as the key. In `navigate()`, the new kind's form is built first (`:308`, replacing controls and defaults synchronously) and `currentKind` is assigned only after `await loadPresets(kind)` (`:315`, a network round-trip). An input event during this window runs `rememberTyped` with the new form's control but the old `currentKind`, storing the value under the wrong kind.
- **Impact:** User switches bolt→nut and types clearance at once. Value is stored as `lastTyped.set('bolt', {clearance: '0.1'})`. Later on the nut page, `Matching bolt` reads `lastTyped.get('bolt')` and builds link `#kind=bolt&clearance=0.1&...`. Click triggers `navigate()` refusal at `:318–323`: `Unknown field "clearance" for kind "bolt"`. Nothing clears the stale entry; every bolt field has a default, so `rememberTyped` never writes bolt's key again.
- **Probe evidence:** `probe_wr07_cd.out` (session scratchpad), line 4: "C nut Matching bolt href "#kind=bolt&clearance=0.1&..."; line 5: "Unknown field \"clearance\" for kind \"bolt\"... error".
- **Fix:** Set `formKind` in `buildForm` (where controls are built) and `clearForm` (to null). Use `formKind` as the memory key instead of `currentKind`.

**WR-08: WARNING — Reset and links don't clear stale memory values** (`src/screw/static/app.js:698–701`, `:325`, `:428`)

- **Contract promise (UI-SPEC rule 35, 37):** "an empty typed value deletes the entry, so a link never carries an empty or stale number"; "A value a link, Reset or a kind change wrote is not typed and is not remembered"
- **Actual behavior:** Only the form's `input` event runs `rememberTyped`, which writes the memory. `reset()` calls `write(input, defaults[name])` directly (`:698–701`, no input event). `navigate()` writes each control from the hash (`:325`, no input event). After Reset clears a field or a link writes a new value, the memory keeps the old entry.
- **Impact — Case 1 (Reset):** User types clearance 0.1 on a nut (stored). Presses Reset; field is now empty. Switches to bolt: `Matching nut` link is `#kind=nut&clearance=0.1&...` and opens a nut at 0.1, a value the user cleared. UI-SPEC rule 35 says Reset "still opens the field empty", implying the link should too.
- **Impact — Case 2 (Link):** User types 0.1 on a nut, opens `Matching bolt`. Returns via a shared link or browser Back, opening a nut at clearance 0.3. Field shows 0.3, memory holds 0.1, bolt's link carries 0.1. This is the "typed means an input event" rule (plan 05-22-PLAN.md line 472), but it also violates "stale number" if the user was shown the 0.3 value and expects the link to reflect it.
- **Probe evidence:** `probe_wr07_wr08.out` (session scratchpad), line 50: "A bolt Matching nut href "#kind=nut&clearance=0.1..." (after Reset on line 49: field is now empty); lines 53–54: after link changes clearance to 0.3, bolt's link still carries 0.1 ("B bolt Matching nut href "#kind=nut&clearance=0.1...").
- **Fix:** Implement `forgetUntyped(name, written)` to delete memory entries when `reset()` or `navigate()`'s write loop empties a field or overwrites it with a value different from what's remembered.

**Original findings (05-10, 05-18, 05-19):**

1. **Clearance field: required, empty on load**
   - Schema from `/api/schema?kind=nut` marks `clearance` as required (no `default`)
   - `buildForm` (line 90) reads `defaults[name] = prop.default` → `undefined` for clearance
   - `navigate()` writes field via `write(input, h.get(name) ?? defaults[name])`
   - `write()` (line 46-49): `else input.value = v ?? ''` → empty string for `undefined`
   - Field appears visually empty, not showing "undefined" or "null"
   - Plan 05-10, RESEARCH P9b requirement met

2. **422 missing clearance error**
   - API returns `422 {"type": "missing", "loc": ["clearance"]}` when nut lacks clearance
   - `renderError()` marks the field `.invalid`
   - Input border becomes accent color, field shows error text
   - Nothing builds until value is typed (plan 05-10, rule 35)

3. **Kind change: mesh drops before new form**
   - `navigate()` (line 277-283): `if (kind !== currentKind) { dropMesh(); if (!(await buildForm(kind))) return; ... }`
   - `dropMesh()` (line 588) removes mesh from scene and sets `mesh = null`
   - Clears `meshWarnings` and `meshNotes` (lines 33-35, 581-586)
   - New form builds after mesh is gone, so stale bolt mesh never appears as nut (plan 05-10, rule 34, R10)
   - Test pin: `test_a_kind_change_drops_the_old_mesh_and_what_described_it` (tests/test_parity.py)

4. **Counterpart link: hidden until document available**
   - `showCounterpart(info.counterpart ?? null)` (renderInfo line 386)
   - `showCounterpart()` (line 396-401): `counterpartLink.hidden = counterpart === null; if (counterpart === null) return;`
   - Link hidden on failed update or refused link per plan 05-10
   - Hidden attribute in HTML (index.html line 22) ensures no flash on load

5. **Fine-STL refusal blocks download**
   - `download_refusal()` returns sentence when nut `m > cap` or `clearance > 5mm`
   - `setDownloads()` checks refusal for stl/fine (app.js line 518-519)
   - If refused: button disabled, title shows warning sentence, download link disabled (aria-disabled=true)
   - Link does not open (no href), so refusal text appears as title on hover
   - Preview quality always available (refusal only blocks fine STL)
   - Plan 05-19, rule 17 requirement met

6. **Downloads built from info.downloads**
   - `renderInfo()` does not name format, quality or preference (rule 17)
   - Page reads `downloads` array from API and shows first un-refused entry per format
   - Order and refusal text come from backend (calc/__init__.py `_nut()`)
   - No format names, no quality preference hardcoded (plan 04-16, D-10)

7. **Reset leaves clearance empty** (05-21)
   - `reset()` writes each field from `defaults[name]`
   - Clearance default is `undefined`, so `write()` sets empty string
   - After Reset, nut form is empty again (plan 05-10, rule 35 note)

8. **After failed update, selects show the row the fields hold exactly** (05-21)
   - Plan 05-21 added `rowOfFields()` (line 676) to match the catalogue row client-side on failure
   - Exact `Number(held) === value` with `held !== ''`, no tolerance, no `Math.`
   - `showMatch(null)` in `fail()` takes the row the fields hold (rule 15, 32, D-12)
   - Source pin: `test_after_a_failed_update_the_selects_show_the_row_the_fields_hold_exactly` passes
   - Probe in 05-21-SUMMARY.md confirms: with nut clearance empty, pick ISO 4032 then M6 leaves the selects at ISO 4032 / M6

---

## Re-audit after 05-21 and 05-22

**Plans 05-21 and 05-22** amended 01-UI-SPEC.md and changed only `src/screw/static/app.js` and `tests/test_parity.py`. No HTML or CSS changes.

**Plan 05-21 changes (commits a22734e, 18d896a):** Added `rowOfFields()` function to implement rule 32's "selects follow the fields after a failed update" contract. Verified by source pin and Playwright probe in RED→GREEN format. No contract violations found; Pillar 6 remains 4/4 for this plan's changes.

**Plan 05-22 changes (commits a2e1f07, 98e7864):** Added `lastTyped` Map and `rememberTyped()` to carry the clearance typed on a nut on the bolt's Matching nut link (rule 37, L15 amendment). Amended 01-UI-SPEC.md rule 34, 35, new rule 37. Code review identified two defects (WR-07, WR-08) confirmed by browser probes in the security audit session. Both violations diverge from what rules 35 and 37 promise:

1. **Rule 35** says "a link, Reset and a kind change still open the field empty", implying the Matching nut link should carry no stale value after Reset or a kind change.
2. **Rule 37** says `lastTyped` is "written only by the form's `input` event" and "a value a link, Reset or a kind change wrote is not typed and is not remembered", so values not typed should not persist in the link.

Both promises are violated:
- WR-07: Values are keyed by `currentKind` (wrong kind during switch), not by the kind whose form is shown, causing the link to carry a value for a kind that doesn't have the field, triggering a refusal.
- WR-08: Reset and links write the form but don't update memory, so the link carries stale values the field no longer shows.

**Severity assessment:**
- WR-07 is BLOCKER: user can hit the "Unknown field" error path, breaking the link's contract.
- WR-08 is WARNING: the link carries a stale value, violating rule 35's promise that Reset clears it and rule 37's "no stale number" language, but it does not break a path—just confuses the user about which value the link will use.

**Re-score Pillar 6:** From 4/4 to 2/4 (notable gaps, contract partially met). The 05-21 changes hold the 4/4 baseline for their parts; the 05-22 changes degrade the pillar by introducing two bugs that violate the contract the plans themselves wrote.

---

## Files Audited

- `src/screw/static/index.html` (HTML structure, no Phase 5 changes)
- `src/screw/static/app.js` (form/panel rendering, counterpart link, clearance field, kind change, 05-21 rowOfFields, 05-22 lastTyped and rememberTyped)
- `src/screw/static/style.css` (counterpart link styling, no new scale additions)
- `src/screw/calc/__init__.py` (Clearance field, Pair group, Limits heading, M18 note, standing warning, nut fine-STL refusal routing)
- `src/screw/calc/thread.py` (nut_fine_stl_refusal function with clearance and m sentences)
- `src/screw/params.py` (NutParams class, required clearance field)
- `.planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md` (amended rules 15, 32, 34, 35, 37 and UI Considerations for 05-21 and 05-22)

---

**Blocking issue found: WR-07.** Pillar 6 scores 2/4 after 05-22 due to contract violations in the `lastTyped` memory implementation. Plan 05-21's `rowOfFields` implementation and all other Phase 5 frontend features meet their contract. The overall score is 21/24.
