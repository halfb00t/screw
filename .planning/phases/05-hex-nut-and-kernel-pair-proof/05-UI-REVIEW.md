# Phase 05 — UI Review (Re-audit after gap closure 05-24 and 05-25)

**Audited:** 2026-10-22
**Baseline:** 01-UI-SPEC.md (amendments by Phase 5 plans 05-10, 05-18, 05-19, 05-21, 05-22, 05-23, 05-24, 05-25)
**Screenshots:** Not captured (no dev server on localhost:3000, 5173, 8080)
**Interaction captures:** off (workflow.ui_interaction_capture is false)

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 4/4 | All Phase 5 strings server-provided; error messages contract-correct; no generic labels |
| 2. Visuals | 4/4 | Page anatomy follows spec; counterpart link placement correct; visual hierarchy intact |
| 3. Color | 4/4 | Counterpart link muted Caption; accent reserved for downloads and invalid; no hardcoded colors |
| 4. Typography | 4/4 | All Phase 5 text reuses declared roles; no new sizes or weights |
| 5. Spacing | 4/4 | All spacing uses declared tokens and exceptions; no new sub-scale values |
| 6. Experience Design | 4/4 | **WR-09 and WR-10 resolved:** seven clears before first await on kind switch; failed schema/catalogue refused whole unless overtaken |

**Overall: 24/24** (maintained from 05-23 review)

---

## Resolution of Prior Findings and New Gap Fixes

### WR-09: RESOLVED ✓ (Plan 05-24)

**Prior issue (05-23 truth C4, first sentence):** With the nut's catalogue request held after a kind switch from bolt, once the nut's controls are on screen the bolt's picker remains live and a Size pick of M2.5 throws `Cannot read properties of undefined (reading 'input')` and writes `d` 2.5 and `pitch` 0.45 into the nut's controls.

**Evidence of fix:**

1. **Form and picker cleared before new schema fetch** (`src/screw/static/app.js:335-344`):
   - `dropMesh();` (line 335)
   - `clearForm();` (line 336) — sets `formKind = null`, clears fields and defaults
   - `clearPicker();` (line 337) — sets `catalogue = null`, hides picker, clears selects
   - `$('#dims').replaceChildren();` (line 338)
   - `showCounterpart(null);` (line 339)
   - `setDownloads(null);` (line 340)
   - `setStatus('');` (line 341)
   - `try { if (!(await buildForm(kind))) return; ...` (lines 342-344) — first await comes after all clears

2. **Update guard still blocks writes** (`line 504`): `if (currentKind === null || formKind !== currentKind) return;`

3. **Source test pin** (`tests/test_parity.py:1004-1015`): `test_a_kind_change_clears_the_old_form_and_picker_before_it_fetches_the_new_ones` asserts all seven clears in head before first await

4. **Probe verification** (`05-24-SUMMARY.md`): `probe_05_24.py` at BASE failed 5 steps; after fix, exit 0, 11 PASS. The window step reads `{"hidden": true, "selects": 0, "badge": ""}`, the pick throws nothing, and the nut's `d` and `pitch` stay empty.

**Result:** A Size pick in the old bolt's picker (held during nut schema load) cannot run because the picker and its catalogue are cleared before the schema is fetched. No page error, no stale values written.

---

### WR-10: RESOLVED ✓ (Plan 05-25)

**Prior issue (05-25 must_haves truth 1):** With `api/schema?kind=nut` answering 500 on a kind switch from bolt, the blank form opened under a selector that reads `nut` (which a select does not report as a change when picked again), and the bolt's info panel, `Matching nut` link, and two live download links stayed on screen.

**Evidence of fix:**

1. **Panel, link, downloads and status cleared at start of switch** (`app.js:338-341`):
   - `$('#dims').replaceChildren();` — info panel emptied
   - `showCounterpart(null);` — matching-part link hidden
   - `setDownloads(null);` — downloads disabled (no href)
   - `setStatus('');` — status cleared (no "Showing the last valid part" over empty canvas)

2. **Both fetches in one try block** (`app.js:342-354`):
   ```javascript
   try {
     if (!(await buildForm(kind))) return;
     if (!(await loadPresets(kind))) return;
   } catch (err) {
     if (mine !== formSeq) return;
     return refuseLink(`Could not load the part: ${err.message}`);
   }
   ```

3. **Overtaken navigation guard** (`app.js:299, 352`):
   - `const mine = ++formSeq;` — each navigation keeps its sequence number
   - `if (mine !== formSeq) return;` — drops failure of overtaken navigation (a newer one owns the page)

4. **Refusal path clears everything** (`app.js:277-286`):
   - `refuseLink()` calls `currentKind = null; kindSelect.selectedIndex = -1;`
   - Shows error message and empty form/picker/panel/downloads
   - Deselected selector makes any pick a real change, so picking the same kind retries

5. **Source test pins** (`tests/test_parity.py:1017-1034`):
   - `test_a_kind_change_clears_the_old_form_and_picker_before_it_fetches_the_new_ones` (line 1004): re-bodied, asserts all seven clears in head before first await
   - `test_a_kind_change_whose_fetch_fails_is_refused_whole_unless_overtaken` (line 1017): asserts both awaits in single try, overtaken guard before refusal

6. **Probe verification** (`05-25-SUMMARY.md`): `probe_05_25.py` at BASE failed 11 steps; after fix, exit 0, 16 PASS. The `fail:` step reads `{"inputs": 0, "dims": 0, "link": null, "downloads": [null, null], "picker": {"hidden": true, "selects": [], "badge": ""}}`, selector is deselected (`kindIndex: -1`), hash stays `#kind=nut`, one error shown, no page error.

**Consequence: Startup failure.** A failed first schema fetch is now refused the same way, showing `Could not load the part: ...` with selector deselected. The startup string `Could not load the part kinds and schema: ...` now covers only a failed `/api/kinds` fetch.

**Result:** A failed schema or catalogue fetch on any kind switch (startup included) deselects the selector and refuses the whole page, clearing all old content. Picking any kind retries. A newer navigation's failure is dropped. No half-page or stale content is shown.

---

### IN-08: RESOLVED ✓ (Plan 05-25)

**Prior issue (05-24 open, review finding IN-08):** The WR-09 source pin counted `clearForm` and `clearPicker` statements from their function definitions, which shadowed local calls elsewhere; a fragile pin.

**Evidence of fix:**

1. **New helper function** (`tests/test_parity.py:998-1003`): `_rebuild_block()` drops comment lines and squashes whitespace, so a comment between the clears or a line break does not break the pin.

2. **Re-bodied 05-24 pin** (`line 1004`): Now asserts only one ordering: all seven clears (`dropMesh();`, `clearForm();`, `clearPicker();`, the panel/link/downloads/status clears) come in head before the first `await`. Counts nothing file-wide.

3. **New 05-25 pin** (`line 1017`): Asserts both awaits in the same try, overtaken guard before refusal. Also counts nothing file-wide.

4. **Mutant check** (`05-25-SUMMARY.md`, mutants_05_25.py):
   - New pins pass benign changes: another `clearForm` caller elsewhere, a split `const built = await buildForm(kind)`, a comment between the clears
   - New pins fail the defects: no overtaken guard, panel cleared after schema fetch, BASE app.js
   - Old pin failed all three benign mutants (fragility gone)

**Result:** The pins describe the order and the try structure without being fragile to formatting or other callers of the cleared functions.

---

## Detailed Findings

### Pillar 1: Copywriting (4/4)

**Verification:** All Phase 5 strings are server-provided and match the contract exactly.

1. **Clearance field** (`src/screw/calc/__init__.py:353`)
   - Label: `"Clearance (radial)"` (PAIR group)
   - Help text: server-provided from schema

2. **Kind-switch error** (`src/screw/static/app.js:353`)
   - Message: `Could not load the part: ${err.message}`
   - Example: `Could not load the part: 500 Internal Server Error`
   - Contract row (01-UI-SPEC.md Copywriting, plan 05-25): `Could not load the part: ${err.message}`

3. **Startup error** (`src/screw/static/app.js:775`)
   - Message: `Could not load the part kinds and schema: ${err.message}`
   - Reached only if `/api/kinds` fails (per 05-25 Copywriting amendment)

4. **Validation errors** (`app.js:418`)
   - Trimmed from API response: `String(d.msg).replace(/^Value error, /)`

5. **No field or kind names in app.js** (rule 29)
   - Every link, label, group heading comes from the API
   - Error messages are generic template strings

**No issues found.** All strings are server-provided or generic templates.

---

### Pillar 2: Visuals (4/4)

**Verification:** Visual structure and hierarchy follow UI-SPEC Page Anatomy after the clears.

1. **Counterpart link placement** (`src/screw/static/index.html`)
   - Element: Not visible in the static HTML (added dynamically by app.js)
   - Rendered by `showCounterpart()` (line 441)
   - Hidden attribute managed: `counterpartLink.hidden = counterpart === null`

2. **Clears maintain page structure**:
   - `dropMesh()` (line 638): removes mesh; canvas stays in DOM
   - `clearForm()` (line 77): clears `#params`; fieldsets remain in DOM
   - `clearPicker()` (line 84): hides picker; legend stays in DOM for next build
   - `$('#dims').replaceChildren()`: empties info panel; structure stays for next render
   - `showCounterpart(null)`: hides link
   - `setDownloads(null)`: disables download buttons
   - `setStatus('')`: clears status text

3. **No visual regression on kind switch**:
   - All clears maintain the expected layout (rule 36, E3, E10)
   - New kind's info document writes the panel and link again
   - Failed update keeps panel empty (rule 15)

**No issues found.** Visual structure and hierarchy are maintained.

---

### Pillar 3: Color (4/4)

**Verification:** Color usage respects the accent reservation and 60/30/10 split.

1. **Counterpart link** (`src/screw/static/style.css:125`)
   - CSS: `#counterpart { color: var(--muted); font-size: .85rem; }`
   - Applied color: `--muted` (secondary text, reserved for non-primary elements)
   - Rationale: link is not a primary action; accent reserved for downloads and invalid fields (rule 34)

2. **Accent usage** (style.css):
   - Line 48: `a { color: var(--accent); }` — header "API" link only
   - Line 116-117: `.field.invalid input` — border and outline
   - Line 140: `.btn.primary` — download buttons
   - No other uses in the codebase

3. **No hardcoded colors**:
   - All colors use CSS custom properties
   - Light/dark mode switch via `@media (prefers-color-scheme: dark)`

**No issues found.** Color usage follows the contract.

---

### Pillar 4: Typography (4/4)

**Verification:** All Phase 5 text reuses existing roles; no new sizes or weights added.

1. **Counterpart link** (`style.css:125`)
   - Size: `.85rem` (Caption role per UI-SPEC Typography table)
   - Weight: `400` (Body weight, inherited)
   - Matches `#badge` exactly

2. **Error messages** (`style.css:164`)
   - Size: `.85rem` (Caption role)
   - Weight: `400`
   - Padding/margin: exception values (locked)

3. **Typography scale locked**:
   - Body: 14px 400
   - Label: 14px 500
   - Caption: 13.6px (.85rem) 400
   - Fine print: 12.48px (.78rem) 400
   - Group legend: 12px (.75rem) 600
   - No new sizes or weights introduced in Phase 5 gap closure plans

**No issues found.** All typography reuses existing roles.

---

### Pillar 5: Spacing (4/4)

**Verification:** All spacing uses declared tokens and UI-SPEC exceptions.

1. **New clears preserve spacing**:
   - `$('#dims').replaceChildren()`: empties the grid; gap and padding structure stays
   - `showCounterpart(null)`: hides the link; no margin left behind
   - `setDownloads(null)`: disables buttons; `.downloads` flex gap stays `.5rem`
   - `setStatus('')`: clears text; position and padding stay

2. **Spacing tokens in use**:
   - `.5rem` (sm) — button gaps, field row margins
   - `.75rem` (md) — fieldset top margin, group gaps, info row gaps
   - `1rem` (lg) — padding
   - `1.5rem` (xl) — column gap in info grid
   - `2rem` (2xl) — bottom column gap

3. **Exceptions (locked, sub-scale)**:
   - `.15rem, .3rem, .35rem, .4rem, .45rem, .6rem, .7rem, .8rem, .85rem` — fine-print, badge, input padding, message margins
   - No new arbitrary values added

**No issues found.** Spacing follows the declared scale and exceptions.

---

### Pillar 6: Experience Design (4/4)

**Re-audited after plans 05-24 and 05-25.** WR-09 and WR-10 are resolved. All interaction states are correctly implemented.

#### 1. Kind switch clears all old content before fetching new schema ✓

The rebuild block (lines 316-355) now executes all seven clears before the first `await`:

```javascript
dropMesh();                               // line 335
clearForm();                              // line 336 - sets formKind = null
clearPicker();                            // line 337 - sets catalogue = null
$('#dims').replaceChildren();            // line 338
showCounterpart(null);                   // line 339
setDownloads(null);                       // line 340
setStatus('');                            // line 341
try {
  if (!(await buildForm(kind))) return;   // line 343
  if (!(await loadPresets(kind))) return; // line 344
} catch (err) { ... }
```

**Evidence:**
- Test pin (`test_a_kind_change_clears_the_old_form_and_picker_before_it_fetches_the_new_ones`, line 1012): asserts all seven clears in the head of the rebuild block, before first await
- Probe (05-24-SUMMARY): WR-09 window step shows `picker.hidden=true, selects=0, badge=''` after switch and before new picker loads
- Consequence: no old picker can write to new form, no old mesh shown as "last valid part"

#### 2. Failed schema or catalogue fetch is refused whole ✓

The try block wraps both fetches (lines 342-354):

```javascript
try {
  if (!(await buildForm(kind))) return;
  if (!(await loadPresets(kind))) return;
} catch (err) {
  if (mine !== formSeq) return;           // overtaken guard
  return refuseLink(`Could not load the part: ${err.message}`);
}
```

**Evidence:**
- Test pin (`test_a_kind_change_whose_fetch_fails_is_refused_whole_unless_overtaken`, line 1017): asserts both awaits in one try, overtaken guard before refusal
- Probe (05-25-SUMMARY): `fail:` step shows all of old part cleared (dims=0, link=null, downloads=[null, null]), one error, selector deselected (`kindIndex=-1`), hash kept
- Consequence: no half-page (blank form under selector reading the new kind), no stale content, any pick retries

#### 3. Overtaken navigation refuses nothing ✓

The catch block guards against a newer navigation's failure (line 352):

```javascript
const mine = ++formSeq;  // line 299 - each navigation records its sequence
...
if (mine !== formSeq) return;  // line 352 - drop this failure if formSeq advanced
```

**Evidence:**
- Probe (05-25-SUMMARY): `overtaken-schema:` and `overtaken-catalogue:` steps show the bolt stays whole when the nut's schema or catalogue fails late (after user Back)
- Consequence: wiping the bolt with the nut's failure is measured as fixed (BASE wipes it on catalogue failure, review patch wipes it on schema failure; now neither does)

#### 4. Clearance field: required, empty on load ✓

- Schema marks `clearance` as required (no `default`)
- `buildForm` reads `defaults[name] = prop.default` → `undefined` for clearance
- `navigate()` writes field via `write(input, h.get(name) ?? defaults[name])`
- `write()` (line 59): `else input.value = v ?? ''` → empty string for `undefined`
- Field appears visually empty, not showing "undefined"

#### 5. 422 missing clearance error ✓

- API returns `422 {"type": "missing", "loc": ["clearance"]}`
- `renderError()` marks the field `.invalid` (red border, accent color outline)
- Input border becomes accent color, field shows error text
- Nothing builds until value is typed (rule 35)

#### 6. Status on failed update ✓

- Measured (plan 05-25): a failed bolt's `Showing the last valid part` stayed over empty canvas during a kind switch
- Fixed: `setStatus('')` clears it at the start of the switch (line 341)
- UI-SPEC E17: "the status is empty until a valid nut builds" (now matched by code)

#### 7. Update guard holds during kind switch ✓

- `update()` (line 504): `if (currentKind === null || formKind !== currentKind) return;`
- `formKind` is null for the whole switch (set by `clearForm`, line 81)
- `currentKind` only set after both fetches succeed (line 355)
- Result: no writes, no requests, no downloads while a switch loads

#### 8. Typed-value memory keyed by formKind ✓

- `rememberTyped` (line 707): `lastTyped.set(formKind, typed);`
- `forgetUntyped` (line 709): deletes entries when field value changes via Reset or link
- Called in navigate's write loop (line 366) and Reset handler (line 729)
- Result: clearance typed on nut carries to bolt's Matching nut link (and vice versa) without stale entries

#### 9. rowOfFields treats missing controls as not held ✓

- `rowOfFields` (line 206): `const control = fields.get(name); if (control === undefined) return false;`
- Combined with update guard, prevents errors during kind switches

#### 10. All request and state guards in place ✓

- Loading: `setStatus('Building…')` (line 544), cleared on success (line 552) or failure (line 570)
- Error: `422` marks fields `.invalid`; error messages shown via `showMessages`
- Empty: clearance field empty on load; nut builds nothing until value typed
- Download states: disabled when info fetch fails; enabled when part builds (rule 17)
- Refusal states: all content cleared, selector deselected

**No issues found.** All interaction states and user flows are correctly implemented. Plans 05-24 and 05-25 resolved WR-09 and WR-10 gap findings.

---

## Top 3 Priority Fixes

None identified. All findings from 05-24 and 05-25 re-verification are resolved. The page meets the UI-SPEC contract for all 6 pillars and all interaction requirements.

If future work extends the page, watch for:
1. New fields with defaults on the nut or bolt — ensure they don't override counterpart values or violate L02 (no silent changes to shipped fields)
2. New error paths on kind switch — ensure they follow the one-try pattern and overtaken guard
3. New panel or link clears — ensure they sit before the first await like the current seven

---

## Files Audited

- `src/screw/static/index.html` (page structure, counterpart hidden attribute via app.js)
- `src/screw/static/app.js` (formSeq and overtaken guard, clearForm, clearPicker, the seven clears, the single try block, showCounterpart, setDownloads, setStatus, refuseLink, update guard, rememberTyped, forgetUntyped, rowOfFields, all error paths)
- `src/screw/static/style.css` (counterpart link color, typography, spacing, accent usage)
- `src/screw/calc/__init__.py` (clearance field, Pair group, Nut group, standing warning, M18 note)
- `src/screw/params.py` (NutParams clearance required field)
- `tests/test_parity.py` (WR-09 and WR-10 source pins, probe evidence)
- `.planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md` (contract amendments for plans 05-24 and 05-25)
- `.planning/phases/05-hex-nut-and-kernel-pair-proof/05-24-SUMMARY.md` and `05-25-SUMMARY.md` (probe results confirming all steps pass)

---

**Audit complete. Re-audit after gap closure plans 05-24 (WR-09) and 05-25 (WR-10) confirms all findings resolved. Overall score: 24/24.**
