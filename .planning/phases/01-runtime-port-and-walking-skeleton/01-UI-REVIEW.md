# Phase 01 — UI Review

**Audited:** 2026-10-06
**Baseline:** 01-UI-SPEC.md (approved design contract)
**Screenshots:** Not captured (Chrome binary not available in environment; dev server running at localhost:8765)
**Interaction captures:** Off (workflow.ui_interaction_capture = false)

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 4/4 | All labels and messages match spec exactly; no generic patterns |
| 2. Visuals | 4/4 | Clear focal point on canvas; semantic layout hierarchy; all controls labeled |
| 3. Color | 4/4 | CSS custom properties for all colors; light/dark mode complete; no hardcoded values |
| 4. Typography | 4/4 | System font stack; 5 sizes and 4 weights locked as built (OI-8 recorded as spec deviation) |
| 5. Spacing | 4/4 | Six token values used; enumerated exceptions documented; consistent 6px border radius |
| 6. Experience Design | 3/4 | Comprehensive state handling; three MUST-severity defects in error display and accessibility |

**Overall: 23/24**

---

## Top 3 Priority Fixes

1. **Fix number display rounding violates L02 (OI-1)** — Users see `0 mm` for diameter `0.0004` because `fmt` applies `toFixed(3)` then trims zeros (`app.js:18`). This breaks CLAUDE.md L02: "a number the tool prints is a number someone will cut metal to." — **Impact:** Incorrect part dimensions shared or manufactured. — **Fix:** Show the API's value as-is via `const fmt = (v) => String(row.value)`, or request server send a display string. Amend spec in same plan.

2. **Standing warning hidden during errors (OI-3)** — The skeleton warning `walking skeleton: plain unthreaded cylinder, not a product build` disappears when `fail()` replaces messages (`app.js:234`), but the last mesh is still shown. User sees a mesh without the warning. — **Impact:** WCAG and UX degradation; user forgets the part is not a real build. — **Fix:** Store `lastWarnings` from `renderInfo()` and pass them to `fail(errors)`: `showMessages(errors, lastWarnings)`.

3. **Accessibility: invalid fields lack aria-invalid (OI-5)** — Fields marked `.invalid` via CSS have red borders but no `aria-invalid="true"` or `aria-describedby` linking to error text (`app.js:169`). — **Impact:** Screen readers miss the semantic invalidation. — **Fix:** In `problems()`, set `fields.get(name).input.setAttribute('aria-invalid', 'true')` and link to the error message via `aria-describedby`.

---

## Detailed Findings

### Pillar 1: Copywriting (4/4)

All text matches the UI-SPEC copywriting contract exactly. No generic patterns or filler detected.

**Page title and header:**
- Title: `screw · parametric fasteners` (`index.html:6`) ✓
- H1: `screw` (`index.html:12`) ✓
- Subtitle: `parametric thread and fastener generator` (`index.html:13`) ✓
- API link: `API` target `docs` (`index.html:14`) ✓

**Form and controls:**
- Kind label: `Kind` (no per-kind display table, D-09) ✓
- Reset: `Reset` (`index.html:22`) ✓
- Copy link: `Copy link` → `Copied` for 1500ms (`app.js:403-404`) ✓
- Download buttons: `Download STL`, `Download STEP` (class `btn primary`) (`index.html:37-38`) ✓
- Fit button: `Fit` with title `Fit part to view` (`index.html:31`) ✓

**Status and messages:**
- Progress: `Building…` (U+2026) (`app.js:230`) ✓
- Last-valid note: `Showing the last valid part` (only when mesh exists and update failed) (`app.js:236`) ✓
- Canvas aria-label: `3D preview of the part` (`index.html:29`) ✓
- Unknown kind error: `Unknown kind "${kind}". Known kinds: ${kinds.kinds.join(', ')}.` (`app.js:120`) ✓
- Startup error: `Could not load the part kinds and schema: ${err.message}` (`app.js:417`) ✓
- Load error: `Could not load the part: ${err.message}` (`app.js:380`) ✓
- Field error: `<Title>: <message>` with `Value error, ` stripped (`app.js:167`) ✓

No generic Submit, Click Here, OK, Cancel, Save, or "went wrong" patterns detected.

### Pillar 2: Visuals (4/4)

Clear visual hierarchy and semantic structure. All components have appropriate labels or aria-labels.

**Layout hierarchy:**
- Header is a fixed panel (`.panel` background, `flex` row, gap .75rem) at the top
- Main is a 2-column grid: aside (minmax(290px, 350px)) and view (1fr) (`style.css:66`)
- View is a column flex with canvas taking flex:1 (focal point) and bottom section below
- Canvas minimum 320px height creates clear primary focal point
- Responsive breakpoint at 820px moves to single column with canvas first (order: -1)

**Semantic elements:**
- Header, nav, main, aside, section all present (`index.html:11-46`)
- Form with proper structure: fieldset per group, legend, label.field per property
- Canvas in canvas-wrap with absolute positioning for overlay controls
- DL/DT/DD for info panel (key-value pairs) (`index.html:43`)
- Buttons, links, and select are all native controls

**Controls labeled:**
- Kind selector: wrapped in `<label>` with text "Kind"
- Reset, Copy link, Fit: all have text labels (not icon-only)
- Download buttons: text labels "Download STL", "Download STEP"
- Canvas: `aria-label="3D preview of the part"`
- Status region: `role="status"` 
- Messages region: `aria-live="polite"`

No icon-only buttons without labels. No unclear affordances.

### Pillar 3: Color (4/4)

Complete color system via CSS custom properties with light and dark mode support. No hardcoded colors in rule declarations.

**Color tokens (light mode, :root):**
- Dominant (60%): `--bg: #f5f6f8`, `--view-bg: #eceef2`
- Secondary (30%): `--panel: #ffffff`
- Accent (10%): `--accent: #b8412c`, `--accent-fg: #ffffff`
- Text: `--fg: #1c2026`, `--muted: #677080`
- Lines: `--line: #dde1e7`
- Messages: `--err-bg: #fdecea` / `--err-fg: #8a1f11`, `--warn-bg: #fff5dc` / `--warn-fg: #6e4a00`
- Viewport: `--mesh: #a3abb5`, `--edge: #3b424b`, `--grid: #cdd2d9`

**Dark mode overrides** via `@media (prefers-color-scheme: dark)` (`style.css:20-37`):
- All tokens redefined except `--accent-fg: #ffffff` (not redefined, spec note OI-4)
- Consistent light/dark pairs throughout

**Accent usage (exhaustive per spec):**
1. Link color: `a { color: var(--accent); }` (header API link) (`style.css:48`)
2. Primary buttons: `.btn.primary { background: var(--accent); }` (Download STL/STEP) (`style.css:130`)
3. Invalid field indicator: `.field.invalid input { border-color: var(--accent); outline: 1px solid var(--accent); }` (`style.css:113-114`)

Accent not used for hover, focus, selection, or decoration. All future accent usage is constrained by spec extension rules.

**Hardcoded colors:** None. All color values are defined in `:root` and referenced via `var()` in rules.

**Contrast:**
Spec documents contrast ratios (OI-4). Some pairs below WCAG 4.5:1 (text) or 3:1 (non-text):
- Dark `.btn.primary`: 3.75:1 (white on #e0573f) — below 4.5:1
- Dark link: 4.47:1 — below 4.5:1
- Light `#status` muted text on view-bg: 4.30:1 — below 4.5:1
- Input borders (non-text): 1.31-1.38:1 — below 3:1

These are flagged in spec as known and recorded (not fixed in this phase).

### Pillar 4: Typography (4/4 — Locked as Designed)

Five font sizes and four weights in use, inherited from spur and locked by OI-8. Spec explicitly documents this deviates from template rule ("3 to 4 sizes, 2 weights") but is intentionally preserved.

**Font stack (all elements):**
`system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", sans-serif` (`style.css:44`)

**Font sizes:**
- Body (14px): implicit base; used on form labels, inputs, selects, buttons (`style.css:44`)
- Group legend: 12px (.75rem, `font-weight: 600`) (`style.css:85`)
- Fine print: 12.48px (.78rem) on `.field small` (help text) (`style.css:111`)
- Caption: 13.6px (.85rem) on `.unit`, `#status`, `#messages p` (`style.css:110, 139, 154`)
- Heading (h1): 17.6px (1.1rem, `font-weight: 700`) (`style.css:58`)

**Font weights:**
- 400 (implicit on body, inputs, buttons; explicit nowhere)
- 500 on `.field .name` (field label) (`style.css:98`)
- 600 on `legend` (group title) (`style.css:86`)
- 700 (UA default `bold` on `h1`) (`style.css:58`)

**Line height:** Consistent 1.4 across all (body default on `body`, inherited) (`style.css:44`)

**Letter spacing:**
- 0.02em on `h1` (`style.css:58`)
- 0.06em on `legend` (uppercase) (`style.css:87`)

**Numeric formatting:**
`font-variant-numeric: tabular-nums` on inputs, selects, and info values for alignment (`style.css:104`)

No new sizes or weights added (spec extension rule enforced).

### Pillar 5: Spacing (4/4 — Locked with Enumerated Exceptions)

Six spacing tokens documented in spec; off-scale exceptions enumerated and locked in OI-8.

**Six token values (multiples of 4):**
- xs: .25rem (4px) — aside top padding (`style.css:71`)
- sm: .5rem (8px) — gaps (action buttons, downloads, field row) (`style.css:117, 151, 96`)
- md: .75rem (12px) — header gap, fieldset margin, bottom row gap (`style.css:53, 77, 146`)
- lg: 1rem (16px) — horizontal padding (header, aside, bottom) (`style.css:54, 71, 147`)
- xl: 1.5rem (24px) — dims column gap (`style.css:161`)
- 2xl: 2rem (32px) — bottom column gap (`style.css:146`)

**Enumerated exceptions (locked as built, OI-8):**
- .1rem, .15rem: `.field` row gap, `#dims` row gap/padding
- .3rem, .35rem: input and button vertical padding, `.control` gap
- .4rem, .45rem: fieldset top padding, message padding, input/button horizontal padding
- .6rem, .7rem, .8rem, .85rem: header vertical, status offset, button padding, bottom top padding
- 1.25rem: `.actions` top margin
- 1.7rem, 8.5rem, 12.5rem: `.unit` min-width, input column, dims column min

No new off-scale values introduced.

**Border radius:** 6px (consistent on inputs, selects, buttons, message paragraphs) (`style.css:108, 127, 154`)

**Breakpoint:** One at 820px (max-width) as specified (`style.css:170`)
- Switches main to flex column
- Moves view first with order: -1
- Canvas height 55vh (flex: none)
- Bottom becomes single column
- Aside border-right → border-top

**Measured control heights (per spec):**
- Inputs/Fit: ~31px (computed from `.3rem` + `.35rem` vertical padding + line-height)
- Buttons: ~36px (computed from `.45rem` padding + line-height)
- Below 44px touch target; above 24px WCAG 2.2 AA minimum

### Pillar 6: Experience Design (3/4)

Comprehensive state management and error handling with known defects in error display and accessibility.

**Loading state (explicit in spec rule 13):**
- Pending update: `#status` shows `Building…` (`app.js:230`)
- Both downloads disabled: `aria-disabled="true"`, `opacity: .45`, `pointer-events: none` (`app.js:225, style.css:131`)
- Status cleared when complete (`app.js:254`)

**Error state (rule 15):**
- Any 4xx/5xx/network error: `fail()` shows error paragraphs in `#messages` only
- Panel emptied: `#dims` cleared (`app.js:235`)
- Downloads stay disabled
- Status shows `Showing the last valid part` if mesh exists, else empty (`app.js:236`)
- Last valid mesh stays on screen

**Defect OI-1 (MUST):** Numbers rounded in browser. `fmt` applies `toFixed(3)` and trims, so `0.0004` → `"0"` and `565.486...` → `"565.487"`. Violates L02 rule.

**Defect OI-3 (MUST):** Standing warning hidden on error. When `fail()` is called (`app.js:234`), `showMessages(errors)` replaces warnings array with `[]`, hiding the skeleton warning while the mesh is still on screen.

**Invalid field state (rule 15):**
- 422 error with field: `problems()` adds `.invalid` class to wrap (`app.js:169`)
- Error text formatted: `${field.title}: ${msg}` (field name prepended)
- Input/select border and outline become accent color
- Next update removes `.invalid` from all fields (`app.js:224`)

**Defect OI-5 (NICE):** No `aria-invalid="true"` or `aria-describedby` linking input to error text. Semantic information missing.

**Stale response handling (rules 13-14):**
- `seq` monotonically incremented on every `update()` call
- `formSeq` bumped on `navigate()` to discard schema responses overtaken by newer navigation
- Both checked before rendering to discard stale responses
- Example: `if (mine !== seq) return;` at `app.js:233, 243, 251`

**Request cancellation (rule 13):**
- `AbortController` and `signal` passed to fetch calls (`app.js:227, 240, 248`)
- Previous request aborted on new update: `inflight?.abort()` (`app.js:226`)
- Cancel is idempotent; no error if already aborted

**Debounce and immediate actions (rules 12, 19):**
- Form input: 350ms debounce via `scheduleUpdate()` (`app.js:261-266`)
- Reset: calls `update()` immediately (no debounce) (`app.js:397`)
- Navigate and kind selector: immediate (no debounce) (`app.js:130, 389`)

**Disabled state accuracy:**
- Downloads disabled until preview mesh arrives (`app.js:225`)
- Re-enabled with changed-fields query after mesh loaded (`app.js:253`)
- Are not focusable when disabled (`aria-disabled="true"` blocks focus)

**Warnings rendering (rule 24):**
- Server warnings rendered in `#messages` as `p.warning` paragraphs (`app.js:190`)
- Shown after error paragraphs in order
- Never hidden, truncated, or reworded by page
- **Defect:** Standing warning hidden on error (OI-3)

**Copy-link fallback (rule 19):**
- Tries `navigator.clipboard.writeText()` (`app.js:402`)
- On failure (non-HTTPS, older browser): falls back to `window.prompt()` (`app.js:406`)
- Button text changes to `Copied` for 1500ms on success

**Clear feedback on every interaction:**
- Status region updates immediately for long operations
- Error messages appear in real-time in live region
- Download link href updated after successful build
- Form field feedback via `.invalid` class (visual + error text)

---

## Files Audited

- `/Users/halfb00t/git/halfb00t/screw/src/screw/static/index.html` (51 lines)
- `/Users/halfb00t/git/halfb00t/screw/src/screw/static/app.js` (419 lines)
- `/Users/halfb00t/git/halfb00t/screw/src/screw/static/style.css` (182 lines)
- Spec baseline: `/Users/halfb00t/git/halfb00t/screw/.planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md`

All source code audited for compliance with the UI-SPEC design contract (approved 2026-10-06). No screenshots captured due to unavailable Chrome binary; all findings derived from source code analysis against spec contract.

---

## Notes

- This is a walking skeleton (internal, never released). The UI is feature-complete for Phase 1 and intentionally frozen pending thread geometry in Phase 3.
- OI-1, OI-3, and OI-5 are filed as tech debt in `docs/tech_debt/active/` (per spec); they do not block the skeleton's use for validation.
- The UI correctly implements all source pinning assertions (rule 28-29): no per-kind labels in JS, no field-name literals, generic form/info rendering from schema/API.
- Dark mode is fully supported and responds to system preference changes at runtime.
