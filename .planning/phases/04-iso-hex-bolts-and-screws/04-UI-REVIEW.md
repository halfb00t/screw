# Phase 04 — UI Review

**Audited:** 2026-10-12
**Baseline:** `.planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md` (page contract, amended in place by plan 04-13; `04-UI-SPEC.md` is a pointer and carries no rule of its own)
**Screenshots:** not captured (no dev server on localhost:3000, 5173 or 8080; Playwright not installed). Code-only audit. Visual pillars are scored from markup, CSS and script, not from pixels.
**Interaction captures:** off (`interaction_capture: false`). Interaction findings below are code-derived.

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Server and page strings match the amended contract; the blank picker state has no copy and exponent-form numbers reach the panel |
| 2. Visuals | 3/4 | The designation `h2` is body size at weight 700, so the panel's top level is barely distinct from its rows; picker blank state gives no guidance |
| 3. Color | 3/4 | Only tokens used; accent confined to the contract's three roles; badge is muted; OI-4 contrast shortfalls (dark primary button 3.75:1) still open, none added |
| 4. Typography | 3/4 | No new size or weight; the designation and group headings reuse locked roles. The locked five-size, four-weight scale (OI-8) is still a deviation from the template |
| 5. Spacing | 2/4 | Two new off-scale values (`.15rem` on `#dims h2`, `.35rem` on `#badge`) fall outside the enumerated exception list that rule 4 requires |
| 6. Experience Design | 3/4 | Error, refusal and last-valid-mesh states are wired; the picker has no loading indicator (E11 unresolved), 503s offer no retry (OI-6), and no browser run has observed any of it |

**Overall: 17/24**

---

## Top 3 Priority Fixes

1. **Off-scale spacing added by plan 04-13** — the contract says new CSS uses the six tokens or an enumerated exception, and neither `.15rem` (`#dims h2` bottom margin, `style.css:171`) nor `.35rem` (`#badge` top margin, `style.css:123`) is in the OI-8 table — the stylesheet drifts from the locked scale one value at a time — fix: change `#dims h2` to `margin: 0 0 .25rem` and `#badge` to `margin: .25rem 0 0` (both token values), or add both to the OI-8 exception table if the odd value is wanted.

2. **Numbers in exponent form in the info panel** — `String(row.value)` (`app.js:374`) prints a JSON number the way JavaScript does, so a server value of `2.5132741228718346e-06` mm³ shows as `2.5132741228718346e-6 mm³`, and a sub-1e-6 value shows as `1e-7`. Nothing is rounded, so the contract's rule 23 holds, but the panel shows a form the API did not write and an engineer reading it sees a different string than the JSON. User impact: low-probability misreading of a small volume or diameter. Fix: amend rule 23 and the Copywriting row to name this form explicitly and state it is the JavaScript rendering of the API value, or have the server send a display string per row (the deferred idea in CONTEXT). Decide which, then amend the contract in the same change.

3. **Picker has no loading state and no copy for its blank state** — while `/api/presets` is in flight the `#picker` fieldset is hidden with nothing shown (E11 loading is unresolved in the contract), and when the fields match no row all three selects show an empty first option with no text saying why (`app.js:149-156`, `showMatch`). User impact: a user who edits a field sees three blank boxes beside a `custom` badge and cannot tell that the blank means "no row matches". Fix: give the blank option a visible placeholder string declared in the Copywriting Contract (for example `none matches`), and resolve E11 loading in the contract as an explicit assumption or add a `Loading presets` line in `#status`.

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)

Verified against the contract's Copywriting table:

- Badge forms match rule 33: `matches ${preset.display}`, `custom, based on ${presetBasis.display}`, `custom` (`app.js:172-174`). The page composes them from `preset.status` and `preset.display` only.
- Picker legend `ISO preset` (`index.html:20`); axis labels come from `catalogue.axes` (`app.js:201-208`), so no label is held in the page.
- Refusal, unknown-kind, repeated-key, unreadable-value and fetch-failure strings match the contract (`app.js:244`, `265`, `271`, `280`, `289`, `302`, `612`).
- Standing warning, notes and designation are shown as sent through `textContent` (`app.js:362`, `381`).

Findings:

- **WARNING (number form).** `app.js:374` writes `String(row.value)`. For values JavaScript prints in exponent form, the panel shows `2.5132741228718346e-6 mm³` (JSON from Python, parsed and printed by JS). This is the unrounded rendering rule 23 asks for, but the contract's example set does not cover exponent output and no row states it. See Top Fix 2.
- **WARNING (blank picker copy).** The blank option is `new Option('', '')` (`app.js:153`) with no text. The contract accepts an empty option (rule 30), but no sentence anywhere tells the user what an empty select means. The badge `custom` is the only signal.
- **Nice.** The `Copied` label and the `Copy link` label are as the contract says. No empty-state copy exists for the panel, as the contract records (E10 empty is explicit: the panel is empty).

### Pillar 2: Visuals (3/4)

- **WARNING (flat panel hierarchy).** The designation is `#dims h2` at `font-size: 1em; font-weight: 700` (`style.css:171`), the same size as every row label and value. The group headings are 12px uppercase muted. Result: the top of the panel is a bold 14px line above 12px muted caps, which reads as a label, not a title. The contract locked this size deliberately (Typography, "reuses the 14px body size and the 700 weight"), so the fix is a contract decision, not a code slip.
- **WARNING (picker blank state).** Three empty selects with a `custom` badge beneath them (`index.html:20-21`) give no visual cue that the picker is inactive rather than broken. See Top Fix 3.
- **Pass.** The picker reuses `.field` rows and the global `legend` role, so it sits in the same visual system as the form (`style.css:76-122`). The badge is one caption line, never accent.
- **Pass.** The info panel's dashed row dividers and the `repeat(auto-fill, minmax(12.5rem, 1fr))` grid (`style.css:180-187`) are unchanged in shape and handle any row count.

### Pillar 3: Color (3/4)

Color usage is inside the contract:

- New rules use the tokens only. `#messages .note` uses `var(--muted)` on `var(--bg)` (`style.css:167`); `#badge` uses `var(--muted)` (`style.css:123`); `#dims h3` uses `var(--muted)` (`style.css:173`). No hard-coded hex in `style.css` or `app.js`.
- Accent appears only where the contract allows it: `a` text, `.btn.primary`, `.field.invalid` (`style.css:48`, `138`, `115-118`). The new picker and badge introduce no accent.
- The note style is distinct from warning and error (no tint, `style.css:165-167`).

Carried, not new:

- **WARNING (contrast, carried from OI-4).** `.btn.primary` in dark mode is white on `#e0573f`, 3.75:1 against the 4.5:1 text target (contract Color table). Unchanged by this phase; the contract records it. A later colour pass should resolve it.
- **Nice.** The 60/30/10 split is approximate and not measured by area (the contract's own ASSUMPTION). The viewport background is the largest area and is grouped with the neutrals.

Light and dark rendering was not observed. Dark-mode pairings are computed in the contract, not checked on screen.

### Pillar 4: Typography (3/4)

- No new font size is introduced. The designation uses the body size (`style.css:171`); group headings reuse the legend role at `.75rem` / 600 (`style.css:172-179`); the badge reuses the Caption role at `.85rem` (`style.css:123`). This matches the contract's "no new size or weight" rule.
- Weights in use: 400, 500, 600, 700 (unchanged from OI-8).
- Sizes in use: 12, 12.48, 13.6, 14, 17.6px (unchanged from OI-8).

Findings:

- **Carried (OI-8).** The template's three-to-four sizes and two-weights rule is not met: five sizes and four weights, inherited from spur and locked. This phase adds none, so the score is held at 3, not reduced for a change it did not make.
- **Pass.** `#dims h2` at weight 700 reuses the Heading weight that already exists; no new role was invented.

### Pillar 5: Spacing (2/4)

The contract (rule 4 and the Spacing Scale exceptions table) allows new CSS only the six tokens (`.25rem`, `.5rem`, `.75rem`, `1rem`, `1.5rem`, `2rem`) or a value already enumerated in the exceptions table. Checked against `style.css`:

- **WARNING.** `#dims h2 { margin: 0 0 .15rem }` (`style.css:171`). `.15rem` is in the exception list only for the `#dims` row gap and row padding, not for the designation margin. Not a token; not enumerated for this role.
- **WARNING.** `#badge { margin: .35rem 0 0 }` (`style.css:123`). `.35rem` is enumerated for input padding, control gap and the first message top margin, not for the badge. Not a token; not enumerated for this role.
- **Pass.** `#dims h3 { margin: .75rem 0 .25rem }` (`style.css:173`) uses only tokens. The group `dl` gap `.15rem 1.5rem` (`style.css:183`) is the enumerated `#dims` row gap.

The two WARNINGs are why this pillar is 2 and not 3: the contract says new CSS uses the scale, and the plan that added the picker and designation added values the contract does not list. Both are one-line fixes.

### Pillar 6: Experience Design (3/4)

State coverage in code (`app.js`):

- **Loading.** `Building…` while any update is in flight (`app.js:422`); downloads disabled during a build (`app.js:387-396`, `416-418`); the previous panel and badge stay until the new info document renders (rule 16, `renderInfo` at `app.js:359-383`). Good.
- **Error.** Errors are shown above the last valid mesh's warnings and notes (`app.js:426`, `244`, `575`). The panel and badge clear on failure (`app.js:427-428`). The last-valid status string is shown (`app.js:429`). Good.
- **Refusal.** A link the page cannot honour is refused whole, with the form, picker, panel and downloads cleared (`app.js:236-245`). Good.
- **Stale responses.** `seq` and `formSeq` discard overtaken responses (`app.js:83`, `223`, `436`, `444`). `AbortError` is swallowed (`app.js:449`). Good.
- **Picker race.** `pick()` calls `update()`, which aborts the previous request (`app.js:184-197`, `418`). Good.

Findings:

- **WARNING (picker loading).** Between a kind change and the `api/presets` answer the picker is `hidden` with no indicator (`app.js:211-212`; contract E11 loading is unresolved). Low impact for a local response; the contract records it as an assumption. See Top Fix 3.
- **WARNING (no retry on 503).** `fail()` shows the server text and offers no retry control; `Retry-After` is ignored (`app.js:424-430`; OI-6). Unchanged by this phase.
- **WARNING (accessibility, carried from OI-5).** No `aria-invalid` and no `aria-describedby` link from a field to its error (`app.js:343-349` marks `.invalid` only). Controls are about 31px tall against a 44px target. Unchanged by this phase.
- **WARNING (a select change is a build).** A `change` in any picker select calls `update()` at once (`app.js:203`, `184-197`). A keyboard user who arrows through a select on some browsers fires one change per key, each aborting and re-issuing the request. Not a flow break; it wastes builds and can flicker the panel.
- **Not verified.** No browser ran. The six-step human check in `04-13-SUMMARY.md` is the Phase 4 UAT and is still open. Every behavioural claim here is read from source.

Registry safety: `components.json` is absent; no third-party registry is listed in the contract (Registry Safety table). The registry audit does not apply.

---

## Contract Deviations Found

These are places where the built page and the amended contract disagree, or where the contract itself lags the code:

- **Spacing exceptions incomplete** (Pillar 5): `.15rem` on `#dims h2` and `.35rem` on `#badge` are not in the enumerated list.
- **Rule 33 is broader than the plan's wording**, as 04-13-SUMMARY deviation 1 records: `showMatch` sets `presetBasis` on every exact match, so an edit to the default part reads `custom, based on ISO 4017 M6 × 20`. The amended rule 33 and Copywriting row say so, so the page matches the contract. Recorded here because it departs from the plan's "after a pick" wording and the verifier should confirm the owner accepts it.
- **E11 loading and E2 loading** are left unresolved in the contract (assumption only). Not a page defect; a contract gap.

No BLOCKER found. No pillar scores 1, and no defect found breaks a user task in code. Every flow exists and is wired; the open risk is that none of it has been observed in a browser.

---

## Files Audited

- `/Users/halfb00t/git/halfb00t/screw/src/screw/static/index.html` (53 lines)
- `/Users/halfb00t/git/halfb00t/screw/src/screw/static/app.js` (614 lines)
- `/Users/halfb00t/git/halfb00t/screw/src/screw/static/style.css` (203 lines)
- `/Users/halfb00t/git/halfb00t/screw/.planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md` (baseline, read in full)
- `/Users/halfb00t/git/halfb00t/screw/.planning/phases/04-iso-hex-bolts-and-screws/04-UI-SPEC.md` (pointer)
- `/Users/halfb00t/git/halfb00t/screw/.planning/phases/04-iso-hex-bolts-and-screws/04-13-PLAN.md`, `04-13-SUMMARY.md`, `04-CONTEXT.md`
- Plan summaries 04-01 to 04-14: a grep for `static/` in `*-SUMMARY.md` found only `04-13-SUMMARY.md`, so no other plan changed a UI file. Their key-files were not read individually.
- `/Users/halfb00t/git/halfb00t/screw/.planning/ui-reviews/.gitignore` (gitignore gate ran; no capture written)

Not read: `tests/test_parity.py` (source assertions are referenced by the contract but were not re-checked here; this audit is visual and interaction only).
