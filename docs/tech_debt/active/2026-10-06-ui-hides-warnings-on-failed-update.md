# A failed update hides the standing warnings while the last mesh stays on screen

Severity: must
Status: active
Date: 2026-10-06
Source: Phase 1 UI design contract (01-UI-SPEC.md, OI-3), written after plan 01-04 landed
Related files:
- src/screw/static/app.js:232-237 (`fail()` calls `showMessages(errors)` with no warnings)
- src/screw/static/app.js (`showMessages()` replaces the warning paragraphs with `[]`)

## Context
Every failed update (422, 503, network error) replaces the `#messages` area with the error
paragraphs only. The last valid mesh stays on screen with the status `Showing the last valid
part`, but the warnings that belonged to that mesh are gone — including the standing
`walking skeleton: plain unthreaded cylinder, not a product build` that D-06 requires on
every bolt info document.

## Why it matters
D-06 and L02: the warning is the honest label on a part that is not a product build, and it
must be visible whenever the part is. The same path will hide Phase 3 limit warnings and
Phase 6 printability warnings (INFO-04) beside a mesh the user is still looking at — the
warning that says "do not cut this" disappears at the moment an edit fails.

## Next step
Keep the last rendered info document's warnings visible below the error paragraphs while a
mesh is on screen; clear them only when the mesh is cleared (unknown kind) or replaced.
Amend `01-UI-SPEC.md` § Interaction Contract rules 15 and 24 in the same plan. Revisit before
the first warning other than the skeleton's ships (Phase 3 limits, or Phase 6 printability,
whichever lands first).
