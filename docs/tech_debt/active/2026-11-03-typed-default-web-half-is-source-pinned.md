# The page's typed-default parity is pinned as source text and one browser check, not executed

Severity: must
Status: active
Date: 2026-11-03
Source: Phase 8 plan check and 08-04 (D-13)
Owner sign-off: accepted 2026-11-02 (08-CONTEXT.md D-23)
Related files:
- src/screw/static/app.js (`partQuery`, `touch`, `touched`)
- tests/test_parity.py (`test_the_page_writes_a_touched_field_even_at_its_default`, `test_a_typed_default_is_explicit_on_the_api_and_the_cli`)

## Context
D-13 asks for one test across the three front ends. The API and the CLI are executed per kind and per
defaulted field in `make verify`. No harness runs the page (L01), so the page's half is the source
assertions in `test_the_page_writes_a_touched_field_even_at_its_default` plus the owner's browser
check, recorded in `08-04-SUMMARY.md` under `## Browser check`.

## Why it matters
A later edit to the page's writers can break the parity with every test still green, as long as the
pinned statements stay in the source. A typed default would then be capped again on the web while the
API and the CLI refuse it (audit INT-03, L02).

## Next step
An executed check of the page's query (a front-end harness, if a later decision admits one). Revisit
when:
- `partQuery`, `touch`, `touched` or a listener that writes it changes;
- a front-end test harness enters the repo;
- a report says the page and the API answer a typed default differently.
