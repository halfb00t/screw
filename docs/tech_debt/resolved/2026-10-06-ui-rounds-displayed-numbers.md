# The web page rounds every displayed number in the browser

Severity: must
Status: resolved
Date: 2026-10-06
Resolved in: this commit, `fix(ui): show the API's numbers unrounded, with the designation, groups and notes` (plan 04-13; `git log --grep` finds the sha)
Source: Phase 1 UI design contract (01-UI-SPEC.md, OI-1), written after plan 01-04 landed
Related files:
- src/screw/static/app.js:18 (`fmt = (v) => Number(v).toFixed(3).replace(/\.?0+$/, '')`)
- src/screw/static/app.js:185 (`renderInfo` applies `fmt` to every `row.value`)

## Context
The info panel shows `fmt(row.value)` for each `InfoRow` the API sends. `fmt` rounds to
three decimals and trims zeros, so the page shows a different number than the API returned:
`0.0004` (a valid `d`, HTTP 200) displays as `0 mm`; the matching volume
`2.5132741228718346e-06` displays as `0 mm³`; `565.4866776461628` displays as `565.487`;
values past 2^53 print their binary-expansion digits (`785398163397448.2` shows
`785398163397448.25`). Measured with node on 2026-10-06 while writing the UI contract.

## Why it matters
L02: a number the tool prints is a number someone will cut metal to, and the UI must never
compute or round a dimension itself (CLAUDE.md, 01-UI-SPEC hard constraints, D-15). Today
the skeleton's four rows are harmless, but Phase 4 puts cited ISO rows (limits, tolerances)
on the same panel through the same `fmt`, and a rounded limit is exactly the plausible wrong
number L02 forbids.

## Next step
Show `row.value` as the API sent it (`String(row.value)`), or have the server send a display
string per row so the browser formats nothing. Either changes visible formatting, so amend
`01-UI-SPEC.md` § Interaction Contract rule 23 in the same plan. Revisit before the Phase 4
plan that adds ISO rows to the info document (TABL-xx / INFO-01).

## Resolution
Closed by Phase 4 plan 04-13 (D-19). `renderInfo` writes each value as `String(row.value)` plus
its unit, and the one-line rounding helper is deleted, so the page shows the API's number as sent:
`0.0004` reads `0.0004 mm`, the default across-corners row reads `11.547005383792515 mm`. Nothing
else in `app.js` rounds a displayed number; `tests/test_parity.py`
(`test_the_ui_prints_the_numbers_as_sent_under_the_designation_and_the_groups`) refuses
`toFixed`, `toPrecision`, `toLocaleString` and `Intl.NumberFormat` in the source. The UI contract
(`01-UI-SPEC.md` rule 23 and OI-1) is amended by the next commit of the same plan (04-13 Task 2):
rule 23 becomes met, not a target.
JavaScript prints a double as its shortest round-trip digits, which is also what the API sends, so
the two agree digit for digit (checked with node and Python for the default row on 2026-10-12).
