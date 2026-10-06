# The web page drops a foreign or unparseable hash key silently

Severity: must
Status: active
Date: 2026-10-06
Source: Phase 1 UI design contract (01-UI-SPEC.md, OI-2), written after plan 01-04 landed
Related files:
- src/screw/static/app.js:129 (`navigate()` reads only the names the schema defines)
- src/screw/static/app.js:137 (`partQuery()` skips an empty value)
- src/screw/static/app.js (`writeHash()` rewrites the URL without the dropped key)

## Context
A shareable link whose hash names a key the kind does not define, or a value the number input
cannot hold, is accepted: `#d=8&m=5` opens `d=8` and the hash is rewritten to `#d=8`;
`#d=abc` opens the default diameter and rewrites to no `d` at all. Nothing tells the user
that part of the link was ignored. The API answers the same input with a 422 naming the
field and the CLI exits 2 naming the flag (FRNT-01, plans 01-02 and 01-03), and the page
already refuses an unknown `kind` the same way (`Unknown kind "…"`). ASSUMPTION: the
`#d=abc` case rests on the HTML number-input sanitisation turning `abc` into an empty
string; it was read from the spec, not run in a browser.

## Why it matters
L02: a parameter the user did not set must never silently change the part, and a direct
conflict is named, never guessed. A link that said `m=5` and silently opens the default
builds a different part than the link names, and the parity success criterion (roadmap
SC2: a foreign field is refused on every front end, never silently ignored) is only two
thirds true.

## Next step
Name the dropped keys in `#messages` and build with the rest, or refuse the link like the
unknown-kind case. Record the choice in `01-UI-SPEC.md` § Interaction Contract rule 10 and
extend `tests/test_parity.py` (plan 01-05) or a UI test to pin it. Revisit before the Phase 3
plan that adds the first field users will share (`left_hand`, THRD-xx).
