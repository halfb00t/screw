# screw pair's verdict exit codes 1 and 2 are also what a crash and a refused parameter return

Severity: must
Status: active
Date: 2026-10-21
Source: 05-REVIEW.md IN-03, filed by plan 05-20 (owner's choice 2026-10-21)
Related files:
- src/screw/cli.py:186 (`PAIR_EXIT`) and :209 (`os._exit(PAIR_EXIT[report.verdict])`) at ad09d46
- tests/test_cli_pair.py (`test_the_exit_code_is_the_verdict_after_the_json_is_out`)
- docs/architecture/decision_log.md (D-06's exit codes, published)

## Context
`PAIR_EXIT` maps `violated` to 1 and `inconclusive` to 2. Exit 2 is also what every refused
parameter returns, with empty stdout. Exit 1 is also what Python returns after an uncaught
exception, and `cmd_pair` has no handler around `prove`. A script that branches on `$?` reads a
crashed proof as "violated" and a refused parameter as "inconclusive".

Today the discriminator is the report JSON on stdout: it appears only with a verdict. The tests pin
the 0/1/2 mapping for verdicts but not the collision. Plan 05-20 added one more inconclusive-by-
definition case (a clearance of d / 2 or more) that still prints its JSON and exits 2, so the
discriminator holds there too.

## Why it matters
The D-06 codes are published, so a caller that trusts the code alone can take a crash for a
violation, or a typo for an inconclusive proof. Nothing in this repo branches on the code yet.

## Next step
Revisit before any script, workflow or doc branches on the exit code, or before the Phase 6 release.
Either document stdout as the discriminator (a non-empty report means a verdict), or exit outside
{0, 1, 2} on an unexpected exception and keep D-06's verdict codes. This is an owner decision,
because D-06 is costly to reverse.
