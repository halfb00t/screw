# The thread spike harness carries five open review warnings that PR 2 may not fix

Severity: must
Status: active
Date: 2026-10-09
Source: execute-phase code-review hook on Phase 2 (`.planning/phases/02-thread-spike/02-REVIEW.md`, ledger `02-REVIEW-DISPOSITION.md`); all twelve findings open
Related files:
- bench/thread_spike/__main__.py:1375 (WR-01: `verdict --campaign PREFIX` globs `PREFIX-*.jsonl`, so a prefix that extends another is read too, and the header's `block` is trusted over the file name)
- bench/thread_spike/__main__.py:1142 and :1118 (WR-02: `run <block> --k-from` and `--frontier-from` accept incomplete records; the campaign path is guarded, the standalone path is not)
- bench/quiet.py:52 and bench/thread_spike/__main__.py:1218 (WR-03: `decisive` is fixed at block start; nothing re-reads the load during a multi-hour block)
- bench/thread_spike/verdict.py:1589 (WR-04: the mixed-hand branch of `cell_verdict` returns before the nut-body check that guards same-hand cells)
- bench/thread_spike/__main__.py:183 (WR-05: the guard does not check that the working tree matches the HEAD it records)
- bench/thread_spike/worker.py:246, helical.py:74, measure.py:40, maths.py:3, verdict.py:196, verdict.py:1329, __main__.py:226 and :1056 (IN-01 to IN-07)

## Context
The Phase 2 harness landed on main as PR 5 (`fd40abc`) after a second CLI reviewed it, and
decision D-19 freezes it for PR 2: the runs branch records data and the decision entry and
changes no harness file. The end-of-phase code review (standard depth, 13 source files) then
found 0 critical, 5 warning and 7 info items. None changed the recorded campaign
`2026-10-08-a`: the reviewer checked that the classification, the closed form and the STL
check hold, that the pair report has no timeout, failure or worker_died cell, and that every
record name matches `{prefix}-{block}`. The warnings are places where the harness could read a
record other than the one the protocol means, or could accept a dirty working tree, on a
future run.

WR-03 touches a pre-registered rule (D-17: the gate is read once per block and the end reading
is labelled "includes this run's own load" and never used), so changing it is a protocol
amendment in a PR that post-dates the protocol, not a bug fix.

## Why it matters
A later campaign (a re-run after a Phase 5 revision, or Phase 7's re-measure) could record a
block under a clean-looking HEAD from an edited tree (WR-05), adopt a neighbouring campaign's
run under a nested prefix (WR-01), or carry `decisive: true` through a block that went noisy
half-way (WR-03). The verdict rules would then be applied to the wrong evidence while every
record looked well-formed.

## Next step
Revisit when the next harness PR is opened (the first PR after PR 2 lands that touches
`bench/thread_spike/` or `bench/quiet.py`), and in any case before the next campaign is run:
fix WR-01, WR-02, WR-04 and WR-05 with their tests in that PR; put WR-03 to the owner as a
protocol amendment; triage IN-01 to IN-07 there. Update the ledger rows in
`02-REVIEW-DISPOSITION.md` as each one closes.
