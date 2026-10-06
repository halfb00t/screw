# Tech debt index

Known-bad code, missing tests, brittle paths, risky shortcuts, deliberate skips. One file
per item in `active/`; move to `resolved/` (never delete) when fixed, in the same commit
as the fix.

Severity (grep-able `Severity:` field):

- **blocker** — data corruption, silent partial success, source-of-truth violation,
  paid-API drain risk. Fix before shipping.
- **must** — correctness or maintainability hygiene, or deferred work with a named
  trigger.
- **nice** — cosmetic, speculative, honour-system.

## Active

| Severity | Item | Trigger to revisit |
|---|---|---|
| must | [Interim runtime bounds are spur's figures, not screw's measurements](active/2026-10-05-interim-runtime-bounds.md) | Phase 7 operability re-sweep (OPER-02) |
| must | [The web page rounds every displayed number in the browser](active/2026-10-06-ui-rounds-displayed-numbers.md) | before the Phase 4 plan that puts cited ISO rows on the info panel |
| must | [The web page drops a foreign or unparseable hash key silently](active/2026-10-06-ui-drops-foreign-hash-keys.md) | before the Phase 3 plan that adds the first shareable field (`left_hand`) |
| must | [A failed update hides the standing warnings while the last mesh stays on screen](active/2026-10-06-ui-hides-warnings-on-failed-update.md) | before the first warning other than the skeleton's ships (Phase 3 limits or Phase 6 printability) |
| nice | [The infrastructure forked from spur is not a shared package](active/2026-10-05-shared-infra-extraction.md) | fired: the pool.py race guard (L09) — owner decides extract vs fix twice |
| nice | [Enji Guard not connected](active/2026-10-05-enji-guard-not-connected.md) | first product code on `main`, or the owner decides they want continuous AI audit |

## Resolved

| Item | Resolved in |
|---|---|
