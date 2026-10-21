# A browser test of the page in the gate

Date: 2026-10-21
Source: 05-UAT.md tests 1 and 3 (gaps G-05-1 and G-05-3), plan 05-21
Related files:
- src/screw/static/app.js
- tests/test_parity.py
- .planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md

## Context
The gate checks `app.js` only as source text and holds no browser (L01, as
`tests/test_parity.py` and 01-UI-SPEC.md read it). G-05-1 reached UAT with every source
assertion green. G-05-1 and G-05-3 were each reproduced before their fix, and shown gone
after, by a scratch Playwright probe that ran on the sibling spur checkout's venv and was not
committed.

spur runs a browser test inside its gate: `tests/test_browser.py`, the dev dependency
`playwright==1.63.0`, and a headless shell that spur's Makefile puts at 198 MB and 16.4 s to
install on macOS arm64.

## Why it matters
Page behaviour (picks, links, what is built) is checked today only by the owner's UAT. A
regression there reaches the owner, not the gate.

## Next step
The owner decides:

- (a) Port spur's harness as a new `Lxx`: a new dev dependency, a browser download in
  `make test`, and gate and CI time on top of the pair tests' debt item
  (`docs/tech_debt/active/2026-10-20-ci-test-job-tripled-by-two-pair-tests.md`).
- (b) Keep the source assertions and the UAT, the status quo.

Revisit when the next page behaviour bug reaches UAT, or at Phase 6 planning, which adds
printability warnings to the page. Plan 05-21 takes neither option.
