# The refused preview's status sentence runs under the Fit button

Severity: nice
Status: active
Date: 2026-10-29
Source: plan 07-14 (phase 7), the scratch Playwright probe of the refused-preview page
Related files:
- src/screw/static/style.css:147-150 (`#status`)
- src/screw/static/app.js `update()` (the refused-preview branch sets the status)
- .planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md UI Considerations E6

## Context
Plan 07-14 made the status show the server's refusal sentence when the info document refuses
the preview STL (L21; ISO 4017 M20 x 60 at pitch 1). Until then the status was a short fixed
string. `#status` is absolutely placed at top .6rem, left .8rem with no right bound, so a long
sentence wraps at the canvas edge and its first line runs under the `Fit` button (top .5rem,
right .5rem).

Measured with headless Chromium on 2026-10-29: at 1440 px wide the status box spans x 362.8 to
1440 and `Fit` x 1391.5 to 1432; at 720 px, x 12.8 to 720 and 671.5 to 712. Both start near
y 53. In the screenshots a few words of the first line are hidden behind `Fit`.

## Why it matters
Nothing is lost: the same sentence is printed whole as a warning under the downloads, and
`#status` has `pointer-events: none`, so `Fit` still works. But the status line on the canvas
reads with a gap.

## Next step
Give `#status` a right bound that clears `Fit`, for example `right: <offset>`. The offset that
clears the button is about 3.5rem, which is not one of the six spacing tokens, so extension
rule 4 of 01-UI-SPEC.md needs the owner's decision: add an exception or move `Fit`. Revisit at
the phase 7 UAT, or at the next change to the viewport overlay.
