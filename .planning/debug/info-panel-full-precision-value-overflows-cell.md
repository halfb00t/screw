---
status: diagnosed
trigger: "UAT gap G-04-5, Phase 04 (ISO Hex Bolts and Screws), test 5 \"The page in the light theme and in a window narrower than 820px (plans 04-13 and 04-16)\". Discovered during /gsd-verify-work 04 on 2026-10-12. Severity minor. Goal: find the root cause only; a gap-closure plan will fix it."
created: 2026-10-12T00:00:00Z
updated: 2026-10-12T00:00:00Z
goal: find_root_cause_only
---

## Current Focus

hypothesis: CONFIRMED. Each info row `#dims dl > div` is a single-line flex container (`display:flex; justify-content:space-between; gap:.75rem`, flex-wrap defaults to nowrap) holding the label `dt` and the value `dd` side by side in a grid track that can be as narrow as 200px (`#dims dl {grid-template-columns: repeat(auto-fill, minmax(12.5rem, 1fr))}`). `#dims dd {white-space: nowrap}` plus the flex-item default `min-width: auto` make the value's minimum its full string width (179.2px for `15.011106998930268 mm`), so the flex shrink takes the whole shortfall out of `dt` (flex: 0 1 auto) down to its min-content, its longest word (one word per line); when value width + 12px gap + longest label word > track width the row's content overflows the cell (overflow visible) into the 24px column gap and the next cell.
test: done (measured reproduction on the real page + differential CSS)
expecting: n/a
next_action: return ROOT CAUSE FOUND to the orchestrator (goal find_root_cause_only); the gap-closure plan picks the fix
bug_class: Bohrbug (deterministic layout: same data + same viewport width -> same overflow, reproduced pixel-exact)
reasoning_checkpoint:
  hypothesis: "The value dd cannot shrink (white-space: nowrap + flex min-width:auto) in a single-line flex row, so dt is crushed to its longest word and, when dd max-content + 12px + dt longest word exceeds the 200-256px grid track, the row overflows into the next cell"
  confirming_evidence:
    - "Real page, 720px: computed dd {white-space:nowrap; min-width:auto}, dd box = full string width (179.2px), dt 65.3px; measured overflow 43.2px = 179.2+12+65.3-213.3 exactly; screenshot matches the user's word for word"
    - "Differential: V1 (div min-width:0) no change; V2 (dd white-space normal) partial; V7/V8 (row flex-wrap) zero overflow at every width"
  falsification_test: "If letting the row wrap (V7) left the overflow in place, or V1 removed it, the hypothesis would be wrong; neither happened"
  fix_rationale: "Not applied (find_root_cause_only). The fix must give label and value separate lines when they do not fit side by side, so neither is forced below its natural width; rounding the number is excluded by L02"
  blind_spots: "Exact viewport of the user's screenshot unknown (consistent with ~720 CSS px at 2x); Chrome only (Safari/Firefox flex min-content rules are the same per spec, not measured); system-ui font metrics on the dev Mac only"
  candidate_causes:
    - "code (CSS): #dims dd white-space:nowrap + single-line flex row #dims dl div (primary)"
    - "data: full-precision values (20-25 chars, plan 04-13, by design L02) and the long cited labels added in Phase 4 (trigger, not a defect)"
    - "environment: viewport -> auto-fill track width 200-256px (both layouts, many common widths) (enabling condition)"
    - "process/spec: 01-UI-SPEC E10 overflow row recorded `may overrun` as a resolved backstop instead of a layout rule"
  and_gate: "yes: overflow needs (a) the unshrinkable dd in a single-line flex row AND (b) a value as long as full precision makes it AND (c) a track under ~256px. (b) is by design (L02) and (c) is the grid's normal behaviour, so (a) is the only cause to fix"

## Symptoms

expected: Every info-panel row (label left, value right, three rows per line in the wide layout) lays out cleanly whatever the value's length; labels wrap as phrases, values never run into the neighbouring cell.
actual: (user) "this part doesn't look clean". Screenshot (light theme, ISO 4017 M8 x 70, ~1440 px wide): full-precision values `0.6765823467065926 mm`, `6.646835306586815 mm`, `15.011106998930268 mm`, `3670.874961137891 mm³` do not wrap or shrink; `15.011106998930268 mm` runs across the gap into the next cell's label `Head height`; labels beside those values wrap one word per line (`Thread / depth / (ISO / 68- / 1:2023 / basic / profile)`, `Across / corners, / geometric / (s / cos / 30°)`, `Volume / (closed / form)`). Short values (`13 mm`, `12.73 mm`, `5.3 mm`, `56`) lay out fine.
errors: none (no console errors recorded)
reproduction: UAT test 5 (.planning/phases/04-iso-hex-bolts-and-screws/04-UAT.md); `screw serve --port 8001`, empty hash, pick ISO 4017 / M8 / 70, look at the info panel (light theme; dark likely same geometry).
started: grouped-rows layout from plan 04-13; noticed 2026-10-12 UAT after G-04-3 closure (04-15, 04-16). Full precision is by design (L02; rounding debt resolved in 04-13 by `String(row.value)`).

## Eliminated

- hypothesis: the grid item (`#dims dl div`) keeps its automatic minimum width (`min-width: auto`) and so overflows its grid track (the classic `min-width: 0` fix)
  evidence: V1 `min-width: 0` on the div gives numbers identical to as-is; measured cell width equals the track width in every run. The track's min sizing function is the fixed 12.5rem, so the grid item's automatic minimum is already 0; the overflow is the flex row's content overflowing its own box
  timestamp: 2026-10-12T00:00:00Z

- hypothesis: the #bottom column (`minmax(0, 1.4fr)`) or #dims itself is too narrow / overflows the page
  evidence: #dims width equals the computed column (598.5px at 1440, 688px at 720) and n tracks + gaps sum to it exactly (2x287.25+24, 3x213.33+48); the overflow is inside the dl cells
  timestamp: 2026-10-12T00:00:00Z

- hypothesis: a regression from plan 04-16 (G-04-3 closure)
  evidence: git blame: the flex row and `dd {white-space: nowrap}` are from 8fd0ab0 (plan 01-04); `#dims dl` from d671ee5 (plan 04-13); 04-16 touched only the download anchors
  timestamp: 2026-10-12T00:00:00Z

- hypothesis: light-theme-specific
  evidence: the prefers-color-scheme:dark block contains only custom properties; no layout differs between themes
  timestamp: 2026-10-12T00:00:00Z

- hypothesis: removing `white-space: nowrap` from dd alone is the whole fix
  evidence: V2 still overflows at 720 (15.4px), 1600 and 1920 (4 rows): the full-precision digit run (~155px) has no break opportunity, so dd's min-content stays ~155px. nowrap is a contributor, not the whole cause
  timestamp: 2026-10-12T00:00:00Z

## Evidence

- timestamp: 2026-10-12T00:00:00Z
  checked: .planning/debug/knowledge-base.md (Phase 0)
  found: one entry (pool-flake-reentrant-tracker), a test-pool GC flake; no keyword overlap with layout/overflow/wrap/CSS
  implication: no known-pattern candidate; investigate fresh

- timestamp: 2026-10-12T00:00:00Z
  checked: src/screw/static/style.css lines 180-189
  found: `#dims dl { display: grid; grid-template-columns: repeat(auto-fill, minmax(12.5rem, 1fr)); gap: .15rem 1.5rem; }`; `#dims div { display: flex; justify-content: space-between; gap: .75rem; ... }`; `#dims dt { color: var(--muted); }` (no flex/min-width rules); `#dims dd { margin: 0; font-variant-numeric: tabular-nums; white-space: nowrap; }`
  implication: the value can never wrap and, as a flex item with default min-width:auto, can never shrink below its full string width; the label is the only shrinkable item

- timestamp: 2026-10-12T00:00:00Z
  checked: src/screw/static/app.js renderInfo (lines 356-383), index.html (#bottom > .col > #dims), UI-SPEC Page Anatomy lines 70-80
  found: each info row is `<div><dt>label</dt><dd>String(value) unit</dd></div>` inside a per-group `<dl>`; `#dims` sits in the right column of `#bottom` (`grid-template-columns: minmax(0,1fr) minmax(0,1.4fr)`), single column under 820px
  implication: the DOM is a grid (dl) of flex rows (div) of two flex items (dt, dd); nothing in app.js sizes anything, so the defect is CSS-only

- timestamp: 2026-10-12T00:00:00Z
  checked: 01-UI-SPEC.md UI Considerations E10 rows (lines 362, 364)
  found: E10 overflow row, marked `resolved / backstop`: "`dd` is `nowrap` in a `minmax(12.5rem, 1fr)` column; a 15-digit volume at the INTERIM bound may overrun; visual test at d=1e5, length=1e5". E10 long-text: "A long server label in dt must wrap, not clip"
  implication: the contract recorded the overrun risk as a held-out visual check rather than as a layout rule; it was never closed by a CSS change

- timestamp: 2026-10-12T00:00:00Z
  checked: git blame style.css 180-189; git show d671ee5 (plan 04-13)
  found: `#dims div` flex row and `#dims dd { white-space: nowrap }` date from 8fd0ab0 (plan 01-04, 2026-10-06); d671ee5 only renamed `#dims` -> `#dims dl` and removed the browser rounding (`toFixed(3)` trimmed), so values grew from at most ~9 chars (`15.011 mm`) to 20-21 chars (`15.011106998930268 mm`), and Phase 4 added the long cited labels
  implication: a latent Phase 1 layout defect, triggered by 04-13's full-precision values; not a regression from 04-16

- timestamp: 2026-10-12T00:00:00Z
  checked: GET /api/bolt/info?d=8&pitch=1.25&length=70&s=13&k=5.3&thread_length=70 on :8001
  found: 17 rows in 3 groups; long values 0.6765823467065926 mm, 6.646835306586815 mm, 15.011106998930268 mm, 3670.874961137891 mm³; preset exact iso4017:M8x70
  implication: same data as the screenshot

- timestamp: 2026-10-12T00:00:00Z
  checked: measured reproduction, headless Chrome (CDP probe /tmp/gsd-g045-O3ci/measure.mjs) loading the REAL page http://127.0.0.1:8001/#d=8&pitch=1.25&length=70&s=13&k=5.3&thread_length=70 (real index.html, style.css, app.js at HEAD 1c612e0), light theme, deviceScaleFactor 1
  found: viewport 720 (narrow layout): #dims 688px, dl tracks 3 x 213.33px; computed dd {white-space: nowrap; min-width: auto; flex-shrink: 1}, dt {flex: 0 1 auto; min-width: auto}, row div {display:flex; justify-content: space-between; gap 12px}. dd box widths = full string width (179.2 / 170.5 / 179.2 / 175.4 px for the four long values). Value text right edge minus cell right edge: Thread depth +24.0px (touches next cell, 0px), Minor diameter +26.3px, Across corners geometric +43.2px (19.2px INTO the next cell `Head height`), Volume +22.0px. dt squeezed to 46.2 / 57.1 / 65.3 / 48.0px. Screenshot /tmp/gsd-g045-O3ci/out/asis-720.png matches the user's screenshot word for word (`Thread / depth / (ISO / 68- / 1:2023 / basic / profile)`, `15.011106998930268 mm` over `Head height`, `Volume / (closed / form)`). Short-value rows: no overflow (text right - cell right = 0).
  implication: REPRODUCED. User's ~1440px screenshot is consistent with a ~720 CSS px window at 2x (three tracks needs #dims >= 648px; in the narrow layout that is a 680-820px viewport)

- timestamp: 2026-10-12T00:00:00Z
  checked: overflow arithmetic against the measured numbers
  found: overflow = dd max-content (nowrap) + 12px gap + dt min-content (longest word) - track width. Across corners: 179.2 + 12 + 65.3 - 213.3 = 43.2 (measured 43.2). Thread depth: 179.2 + 12 + 46.2 - 213.3 = 24.1 (measured 24.0). At 1440 wide: 2 tracks of 287.25px, 179.2 + 12 + 96 = 287.2, so no overflow but dt is left 96px and wraps to ~4 lines
  implication: mechanism confirmed quantitatively: the dd cannot shrink (nowrap makes its min-content its full width; flex items default to min-width:auto), so dt, the only shrinkable item, is crushed to its longest word and, once even that does not fit, the row overflows the grid cell

- timestamp: 2026-10-12T00:00:00Z
  checked: viewport sweep on the real page as-is (/tmp/gsd-g045-O3ci/sweep.mjs, dt/dd line counts by Range client rects), 15 widths 375-2560
  found: overflow (value text right edge past cell right edge) at 500, 680, 720, 800 (narrow) AND 821, 1280, 1536, 1600, 1680, 1920, 2560 (wide); none at 375 (1 track 343px), 1024 (1 track 356px), 1366 (2x265.7), 1440 (2x287.2). Worst row everywhere: `Across corners, geometric (s / cos 30°)` / `15.011106998930268 mm` (needs 179.2 + 12 + 65.3 = 256.5px). At 1920: 4 tracks of 201.6px, 54.9px past the cell, 30.9px into the next cell. Labels squeezed to 7 lines wherever a long value sits beside them
  implication: not a narrow-layout-only bug; any track under ~256.5px overflows, and auto-fill with `minmax(12.5rem, 1fr)` produces 200-256px tracks at most widths in both layouts

- timestamp: 2026-10-12T00:00:00Z
  checked: differential CSS, injected only into the headless page (repo untouched), widths 720/821/1280/1600/1920
  found: V1 `#dims dl div {min-width:0}` -> numbers identical to as-is. V2 `dd {white-space:normal}` -> still overflows at 720 (15.4px), 1600, 1920 (all 4 rows): the digit run itself (~155px) has no break opportunity. V3 V2 + `overflow-wrap: break-word` -> identical to V2 (break-word does not lower min-content). V4 `dd {white-space:normal; overflow-wrap:anywhere}` -> 0 overflow, BUT splits numbers mid-digit, short ones included: `14.3 / 8 mm`, `11.6 / 3 / mm`, `0.6765823 / 467065926 / mm` (screenshot out/V4shot-720.png). V5 `dd {min-width:0}` with nowrap -> worse: 9 rows overflow, up to 105px (text spills out of its shrunken box). V6 `minmax(17rem,1fr)` -> 0 text overflow at these values but only moves the threshold, and at 821 the 272px track is wider than the 237.4px #dims column (grid overflows its column). V7 `div {flex-wrap:wrap}` + `dd {margin-left:auto}` -> 0 overflow at all widths, labels <= 2 lines, values whole, but every long-label row (even `12.73 mm`) moves its value under the label. V8 V7 + `dt {flex: 1 1 7rem}` + `dd {white-space:normal; overflow-wrap:anywhere}` -> 0 overflow at 680/720/821/1280/1440/1600/1920, no value split, short values stay beside their labels, long full-precision values drop whole under their label, labels wrap as phrases (<= 4 lines at 200px tracks) (screenshot out/V8-720.png)
  implication: the cause is the single-line flex row with an unshrinkable value, not the grid item's min-width and not the grid track alone; a fix must let label and value stop sharing a line when they do not fit

- timestamp: 2026-10-12T00:00:00Z
  checked: longest value strings the API can emit for a valid part (node String(value) + unit): d=90000 extreme gives `1502197910971446.5 mm³` (22 chars, 184px); a d=0.001 part gives `0.00010825317547305484 mm` (25 chars, 213.9px) but that part fails its build on the page (L11 volume gate), so the panel is empty for it. Injected both strings into the M8 x 70 panel
  found: as-is: 25-char value 91.2px past its cell at a 200px track. V7 alone: 25-char value 13.9px past a 200px track (nowrap keeps it on one line). V7 + `white-space:normal; overflow-wrap:anywhere` on dd: 0 overflow; the 25-char value breaks at the space before `mm` (number stays whole), the 22-char one stays on one line
  implication: wrapping the row covers every realistic value; the dd break rule is needed only as the last-resort guard for a value wider than a whole 200px track, and then breaks at the unit first

- timestamp: 2026-10-12T00:00:00Z
  checked: style.css lines 20-37 (dark theme block); grep tests/ for nowrap, style.css, #dims, white-space, overflow-wrap
  found: the dark block sets only custom properties (colours), so the geometry is identical in both themes; no test reads style.css or pins any #dims rule (only `$('#dims').replaceChildren();` in tests/test_parity.py:407, an app.js statement)
  implication: theme is not a factor; the CSS change trips no existing test, so the gap-closure plan needs its own guard (source assertion on the row rules and/or a browser-measured UAT step)

## Resolution

root_cause: "In src/screw/static/style.css the info row `#dims div` (line 186) is a single-line flex container (`display: flex; justify-content: space-between; gap: .75rem`, no flex-wrap) placing `dt` and `dd` side by side in a `#dims dl` grid track that auto-fill sizes to 200-256px at most viewport widths (`repeat(auto-fill, minmax(12.5rem, 1fr))`, line 182). `#dims dd { white-space: nowrap }` (line 189), together with the flex-item default `min-width: auto`, fixes the value's minimum at its full string width (about 8.5px a character: 179.2px for `15.011106998930268 mm`), so flex shrinking takes the whole shortfall out of `dt` (`flex: 0 1 auto`, line 188 sets no sizing) down to its longest word, giving one word per line. Once value width + 12px gap + the label's longest word exceeds the track (256.5px for the Across corners row), the row's content overflows the cell (overflow visible) across the 24px column gap into the next cell's label. The rules date from plan 01-04 (8fd0ab0), when values were rounded to at most about 9 characters. Plan 04-13 (d671ee5) made them full precision (20-25 characters, by design under L02) and added the long cited labels, which exposed the defect. 01-UI-SPEC E10 `overflow` had recorded `dd is nowrap ... may overrun` as a backstop visual check, not as a layout rule."
fix: ""
verification: ""
files_changed: []
