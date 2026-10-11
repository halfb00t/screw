# Phase 03 — UI Review

**Audited:** 2026-10-10
**Baseline:** 01-UI-SPEC.md (amended in place by plan 03-05, per D-19; no separate 03-UI-SPEC.md)
**Screenshots:** Not captured (code-only audit; no browser available)
**Interaction captures:** off (workflow.ui_interaction_capture is false)

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 4/4 | All strings exact to spec; textContent used throughout; no field-name literals |
| 2. Visuals | 4/4 | Checkbox rule present; label structure correct; theme inheritance sound |
| 3. Color | 4/4 | No new colors; checkbox inherits --fg; accent still only on three elements |
| 4. Typography | 4/4 | No new sizes or weights; checkbox uses existing .field role and .field small |
| 5. Spacing | 4/4 | Checkbox width: auto only; no arbitrary spacing added |
| 6. Experience Design | 4/4 | All state paths present; per-mesh warnings correct; repeat/foreign/unreadable checks all in place |

**Overall: 24/24**

---

## Audit Scope

Phase 3 plan 03-05 added three features to the UI:
1. **Task 1:** Left-hand thread checkbox built from schema (`prop.type === 'boolean'`)
2. **Task 2:** Link refusals for foreign, repeated, and unreadable hash keys
3. **Task 3:** Per-mesh warnings survive failed updates

Audited files:
- `src/screw/static/app.js` (lines 30-34: read/write helpers; 82-84: checkbox branch; 123-181: navigate with refusals; 233-246: renderInfo/pendingWarnings; 289: fail/meshWarnings; 410: showModel copy; 436: reportLoadError)
- `src/screw/static/style.css` (line 112: `.field input[type=checkbox] { width: auto; }`)

No browser is available to verify rendering, interaction, or theme toggle. All findings are from source code analysis. Four human checks in the plan (03-05-SUMMARY §8) remain outstanding: checkbox rendering in both themes, hash round-trip persistence, link refusal UI, and per-mesh warnings visibility in all error paths.

---

## Detailed Findings

### Pillar 1: Copywriting (4/4)

**Copywriting contract compliance:**

1. **Refusal messages — exact to spec:**
   - Repeated key: `The link names "${k}" more than once.` (app.js:150) ✓ matches rule 10
   - Foreign keys: `Unknown field(s) "${key}"(s) for kind "${kind}". Known fields: …` (app.js:167–168) ✓ singular/plural per plan 03-05
   - Unreadable value: `Unreadable value for "${key}": "${value}".` (app.js:180) ✓ names key and value

2. **Security (textContent only):**
   - showMessages() uses `textContent` exclusively (app.js:210–213) ✓ no `innerHTML`, `outerHTML`, or `insertAdjacentHTML`
   - All error strings pass through showMessages before DOM render
   - User input (hash keys/values) quoted in messages, not interpolated as code

3. **Field-name literals:**
   - Grep for hardcoded field names (`d`, `pitch`, `left_hand`, `length`, `turns`, `volume`, etc.): **0 matches** ✓
   - Form reads from schema.properties only; hash reads from URLSearchParams keys only
   - Refusal message lists known fields from `[...fields.keys()]` at runtime ✓

4. **Checkbox label & help:**
   - Field structure generates label from `prop.title` and help from `prop.description` (app.js:101–108) ✓
   - Help text shown in `.field small` on focus-within only (style.css:183–184) ✓
   - Spec expects: `Left-hand thread` (title) and help via schema; implemented via generic path ✓

5. **Warnings preserved:**
   - renderInfo() stores new info warnings in pendingWarnings (app.js:244) ✓
   - showModel() copies to meshWarnings only when mesh replaces (app.js:410) ✓
   - fail(), refuseLink(), reportLoadError() all show `mesh ? meshWarnings : []` (app.js:289, 130, 436) ✓

**Finding:** All three refusal message templates are text-only, formatted through showMessages, and name the offending keys and values exactly as the spec requires. No field-name literals embedded. Warnings rendered verbatim from server.

---

### Pillar 2: Visuals (4/4)

**Structure and hierarchy (code-only):**

1. **Checkbox element:**
   - Branch condition: `prop.type === 'boolean'` → `input.type = 'checkbox'` (app.js:82–84) ✓
   - No `min`, `max`, `step`, or `inputMode` attributes set on checkbox (lines 82–95 bypass number attributes) ✓
   - Wrapped in `label.field` with `.name`, `.control`, `.unit`, and optional `.description` (app.js:98–110) ✓

2. **Layout and width:**
   - `.field` grid: `grid-template-columns: 1fr 8.5rem` (style.css:93) places label left, unit right ✓
   - Checkbox width rule: `.field input[type=checkbox] { width: auto; }` (style.css:112) ✓ overrides shared `width: 100%` rule (line 101)
   - Specificity: `0,2,1` (class + element) beats `0,1,1` (class + element) for the shared rule ✓

3. **Focus and interaction indicators:**
   - Help text shown on `.field:focus-within small` (style.css:184) ✓ works for all input types including checkbox
   - Invalid state: `.field.invalid input` border + outline in accent color (style.css:115–118) ✓ applies to checkbox too

4. **Theme and inheritance:**
   - Checkbox inherits `color: var(--fg)` from `.field input` (style.css:100) ✓
   - No special checkbox color rules; inherits from light/dark palette ✓
   - Background inherits `var(--bg)` from `.field input` ✓

**Finding:** Checkbox element structure matches spec rule 2. Width rule prevents stretching. All inheritance and theme rules in place. Human verification needed: rendering at natural width in both light and dark, input event firing, and thread preview changing hand on toggle.

---

### Pillar 3: Color (4/4)

**Color usage (no new colors added):**

1. **Accent reserved list:**
   - Spec reserves accent for: link text, `.btn.primary` fill, `.field.invalid` border/outline ✓
   - New checkbox adds no accent usage ✓
   - No hardcoded hex colors in app.js or new CSS lines ✓

2. **Inherited colors:**
   - Checkbox input: inherits `color: var(--fg)` and `background: var(--bg)` from `.field input` rule (line 100–101) ✓
   - Invalid checkbox: inherits `.field.invalid` border accent (line 115–118) ✓
   - No new color tokens added to `:root` (style.css:1–37) ✓

3. **60/30/10 distribution:**
   - No new accent uses; 10% budget unchanged ✓
   - Checkbox does not use accent in any state ✓

**Finding:** No color defects. Checkbox inherits correctly and uses no new colors. The implementation adds zero color tokens or hardcoded values.

---

### Pillar 4: Typography (4/4)

**Font size and weight (no new sizes/weights added):**

1. **Checkbox label:**
   - Label text (.field .name): inherits 14px / 500 weight from style.css:98 ✓
   - Spec locks five sizes (12, 12.48, 13.6, 14, 17.6px) and four weights (400, 500, 600, 700); checkbox uses existing label role ✓

2. **Help text:**
   - `.field small { font-size: .78rem; font-weight: 400; }` (style.css:114) ✓ existing fine-print role
   - Checkbox help reuses same rule ✓

3. **No new sizes or weights:**
   - Grep for `font-size` or `font-weight` in new/changed lines: 0 new values ✓
   - OI-8 locked the five-size, four-weight scale as inherited from spur; Phase 3 Extension rule 4 forbids new sizes/weights ✓

**Finding:** All text for checkbox uses existing typography roles. No new sizes or weights introduced.

---

### Pillar 5: Spacing (4/4)

**Spacing tokens and arbitrary values:**

1. **Six-token palette:**
   - xs (4px / .25rem), sm (8px / .5rem), md (12px / .75rem), lg (16px / 1rem), xl (24px / 1.5rem), 2xl (32px / 2rem)
   - Checkbox inherits `.field` margins (.5rem = sm, style.css:96) ✓

2. **Checkbox width rule:**
   - `width: auto;` (style.css:112) ✓ no arbitrary px values
   - Maintains natural width without measuring or restricting ✓

3. **No arbitrary spacing in Phase 3:**
   - OI-8 enumerates off-scale exceptions (locked); Phase 3 Extension rule 4 forbids new arbitrary values ✓
   - Grep for new `[0-9].*px` or `[0-9].*rem` in app.js: 0 ✓
   - New style.css lines use only existing tokens ✓

**Finding:** Spacing uses six tokens only. Checkbox width rule is token-clean (`auto`, not a measurement).

---

### Pillar 6: Experience Design (4/4)

**State coverage and error paths:**

1. **Checkbox states:**
   - Unchecked (default): checked=false, read()='false', not written to hash ✓ (app.js:32, 196)
   - Checked: checked=true, read()='true', written as `left_hand=true` to hash ✓ (app.js:30, 196)
   - Hash `#left_hand=true` opens checked (app.js:171: write sets `input.checked = String(v) === 'true'`) ✓
   - Omitted key opens unchecked (app.js:171: defaults['left_hand']=false) ✓
   - Reset unchecks (app.js:451: `write(input, defaults[name])` ✓)

2. **Link refusal checks (order and placement):**
   - Repeat check (line 148–152): runs BEFORE kind lookup ✓ catches `#kind=bolt&kind=bolt`, `#kind=bolt&kind=x`, `#d=1&d=2`
   - Foreign check (line 164–169): runs AFTER form built ✓ catches `#d=8&m=5` using fields keys
   - Unreadable check (line 175–181): runs AFTER values written ✓ catches `#left_hand=banana` (not 'true'/'false'), `#d=abc` (number input reads as '')
   - All three routes through refuseLink() (line 123–131): clears form, nulls currentKind, deselects, empties panel, disables downloads, shows message ✓

3. **Unreadable value validation:**
   - Checkbox: `given !== null && given !== 'true' && given !== 'false'` (app.js:177–178) ✓
   - Number/select: `given !== null && given !== '' && read(input) === ''` (app.js:179) ✓
   - Read the HTML-sanitised value back from the control; if it's empty but hash gave a non-empty value, refuse ✓

4. **Per-mesh warnings:**
   - renderInfo() stores fetched warnings in pendingWarnings (app.js:244) ✓
   - showModel() copies pendingWarnings to meshWarnings only when mesh is replaced (app.js:410) ✓
   - Three error paths show `mesh ? meshWarnings : []` below error messages:
     - fail() (app.js:289): `showMessages(errors, mesh ? meshWarnings : [])` ✓
     - refuseLink() (app.js:130): `showMessages([message], mesh ? meshWarnings : [])` ✓
     - reportLoadError() (app.js:436): `showMessages([...], mesh ? meshWarnings : [])` ✓
   - Startup failure (app.js:473): `showMessages([...])` with no warnings (mesh is null) ✓

5. **Status message:**
   - `Showing the last valid part` shown only when mesh exists and update fails (app.js:291) ✓
   - Refused link clears status to '' (app.js:129) ✓ as per plan decision (03-05-SUMMARY Decisions §2)

6. **Loading and disabled states:**
   - Downloads disabled until first successful mesh (app.js:248–260) ✓
   - Status shows "Building…" while update in flight (app.js:285) ✓
   - Debounce 350 ms on keystroke (app.js:321) ✓
   - No debounce on kind change, Reset, or navigate() (app.js:140–142) ✓

**Findings:**
- All three link-refusal cases present, checked in correct order (repeat before kind lookup, foreign after form built, unreadable after write).
- Repeated-key check catches duplicate `kind=` entries before the kind is looked up (parity with API 422 `duplicate`).
- Per-mesh warning logic is sound: warnings belong to the mesh on screen, not the last info fetch; they change only when the mesh is replaced.
- All error paths (4xx/5xx/network/refusal) show the mesh's warnings below the error messages, and startup failure shows none.
- The form is cleared before checking keys, so no partially-filled state is visible after a refusal.
- Checkbox round-trip (write hash, read hash, toggle input event) is implemented; human check needed for actual toggle.

**Needs human verification:**
- Checkbox input event fires on toggle (plan HC #1)
- Hash round-trip persists and reloads correctly (plan HC #1)
- Thread hand visibly changes in preview (plan HC #1)
- Copy link preserves #left_hand=true state (plan HC #1)
- Hash refused links are not rewritten (plan HC #2)
- Multiple error messages show together (plan HC #2)
- Warnings visible below error paragraphs in all paths (plan HC #3)
- Last valid mesh, status message, and warnings all on screen together after failed edit (plan HC #3)
- Checkbox theme works in both light and dark (plan HC #1, backstop E3)

---

## Top 3 Priority Fixes

All three tasks from the plan are present and correctly implemented. **No blocking defects found.**

### 1. Run end-of-phase human checks for checkbox interaction
**Finding:** Checkbox toggle, hash round-trip, and thread preview hand change cannot be verified without a browser.
**Impact:** Four human checks in the plan (03-05-SUMMARY §8) must be run before shipping to verify rendering, interaction, and state persistence.
**Fix:** Execute plan HC #1–#4 in the end-of-phase UAT: render light/dark, toggle checkbox, verify hash, copy link, test all three refusal cases, verify error messages and warnings together.

### 2. Verify per-mesh warning visibility across error paths
**Finding:** Code shows `mesh ? meshWarnings : []` in three places (fail, refuseLink, reportLoadError), but actual rendering and text wrapping in the UI are unverified.
**Impact:** If warnings overflow or clip, the "honest label on the part" (D-06) is not visible and the user loses critical build information.
**Fix:** Run plan HC #3 (set pitch=6, set d/pitch to trigger build_error STL failure, stop server); verify last valid mesh, status `Showing the last valid part`, error message, and warning starting with `threaded rod:` all visible together.

### 3. Verify form structure after refusal
**Finding:** Code clears form, nulls currentKind, deselects kind selector. No field values or labels are visible after a refusal. This is correct but must be visually confirmed.
**Impact:** User should see an empty form and empty panel, with the refusal message naming the key(s) that caused the refusal.
**Fix:** Run plan HC #2 (open `#d=8&m=5`, `#kind=bolt&kind=bolt`, `#left_hand=banana`, `#d=abc` in sequence); verify each shows error message naming the key, empty form, empty panel, disabled downloads, and correct number of error paragraphs before any links are typed.

---

## Files Audited

- `/Users/half/git/halfb00t/screw/src/screw/static/app.js` — 476 lines; reviewed: 30–34 (read/write), 82–84 (checkbox branch), 123–181 (navigate/refusals), 233–246 (renderInfo), 287–292 (fail), 401–411 (showModel), 436 (reportLoadError)
- `/Users/half/git/halfb00t/screw/src/screw/static/style.css` — 185 lines; reviewed: 91–118 (.field rules, 112 checkbox width), 183–184 (help text visibility)

Commits audited:
- 9570adb (feat): checkbox branch, read/write, field structure
- 05fb4ed (fix): refuseLink helper, three link-refusal checks
- 909dec3 (fix): pendingWarnings, meshWarnings, per-mesh warning logic

---

## Recommendation

This is a high-quality implementation. All three plan tasks are present and correct; the code closely follows the spec; and no security or logic defects were found. The implementation is **ready for the end-of-phase human verification gate** (plan HC #1–#4). No code fixes are needed before shipping.

**Blockers:** None.
**Warnings:** Four human checks remain; schedule them before release.

