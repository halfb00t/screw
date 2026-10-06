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
| nice | [The infrastructure forked from spur is not a shared package](active/2026-10-05-shared-infra-extraction.md) | fired: the pool.py race guard (L09) — owner decides extract vs fix twice |
| nice | [Enji Guard not connected](active/2026-10-05-enji-guard-not-connected.md) | first product code on `main`, or the owner decides they want continuous AI audit |

## Resolved

| Item | Resolved in |
|---|---|
