# The M18 probe's --one entry has no deadline when started by hand during a run

Severity: nice
Status: active
Date: 2026-10-14
Source: Codex review of PR #17 (finding 1), plan 05-03; the fix closes the entry before, after and off the list, not during a run
Related files:
- bench/m18_probe.py (`child_refusal`, `_one_line`)

## Context
`python -m bench.m18_probe --one JSON` now refuses a reading that is not one of the 36, a
protocol that is not on origin/main byte for byte, and any state where the parent has not
claimed an empty output file. While a run is in progress all three hold, so a hand-started
`--one` of a registered reading is accepted and has no 130 s deadline. Closing that needs a
secret the child can check (a token the parent writes and the child verifies), which is more
machinery than a 36-reading diagnosis warrants. Needs the owner's sign-off as a deliberate cut.

2026-10-26 (plan 07-03): stays active. The phase 7 campaign does not reuse `bench/m18_probe.py`;
every `bench.oper` reading is killed at the parent's `DEADLINE_S` (600 s), whoever started it, so
the trigger (the probe is reused) has not fired (`07-SWEEP-PROTOCOL.md`, "Debt this campaign
leaves open").

## Why it matters
A hand-started duplicate of a registered reading during the one run could hang without being
killed. It cannot measure an unregistered pose, run early or run after the run. The output is
unaffected: only the parent writes it.

## Next step
Revisit if the probe is reused for another campaign, or if the owner wants the entry closed
completely.
