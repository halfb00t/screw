# The web page drops a foreign or unparseable hash key silently

Severity: must
Status: resolved
Resolved in: fix(ui): refuse a link with a foreign, repeated or unreadable key (this commit; plan 03-07 names its sha)
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

## Resolution
Closed by Phase 3 plan 03-05 (D-10, D-12). The page refuses the link like an unknown kind, the
second option this item offered: building with the rest would open a part the link does not name.

- `refuseLink(message)` in `app.js` is the one helper: it clears the form, nulls `currentKind`,
  deselects the selector, empties the panel, disables the downloads and shows the message. The
  unknown-kind branch and the three new cases all use it, and nothing builds after it.
- Checked in this order: a key given more than once (`The link names "d" more than once.`), before
  the kind lookup so `#kind=bolt&kind=x` is refused too; after the form is built, any key other
  than `kind` that the kind does not define (`Unknown field "m" for kind "bolt". Known fields: ...`);
  after the values are written, a key whose control cannot hold its value (a checkbox given
  anything but `true` or `false`, or a non-empty value that a number or select reads back as `''`:
  `Unreadable value for "d": "abc".`). The unparseable-value half of this item is closed with the
  foreign-key half.
- Pinned as source text by `test_the_ui_refuses_a_link_it_cannot_honour` in
  `tests/test_parity.py`; `01-UI-SPEC.md` rule 10 and rule 21 state it and OI-2 is marked resolved.
- Not verified here: the `#d=abc` case still rests on the HTML number-input sanitisation turning
  `abc` into an empty string. No browser is in the gate (L01), so the ASSUMPTION above moved to the
  end-of-phase human check of plan 03-05 Task 2 instead of being resolved by reading the spec.
