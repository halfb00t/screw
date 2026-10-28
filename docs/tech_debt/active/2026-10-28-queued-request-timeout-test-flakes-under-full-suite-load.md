# The queued-request timeout test flakes under full-suite load

Severity: must
Status: active
Date: 2026-10-28
Source: phase 7 execution (plan 07-05 and quick task 261028-mt2). The pre-commit `make verify` failed on this test twice and passed on the retry each time.
Related files:
- tests/test_pool.py:591

## Context
`test_a_request_queued_behind_a_build_keeps_its_own_full_timeout` runs two same-slot builds of
0.6 s each under a 1.0 s timeout and asserts that both return. Each build has 0.4 s of headroom
against its own clock. Under the full suite's load the test failed twice in one day (once in
07-05, once in 261028-mt2). It passes when run alone and on a retry. No failure output was kept,
so which assertion failed is not recorded. ASSUMPTION: the 0.6 s build ran past its 1.0 s
timeout because the host was loaded.

## Why it matters
`make verify` is the single gate (pre-commit, CI, `make worktree.land`). A gate test that fails
on load teaches retrying until it is green. That hides a real regression of the queue-aware
deadline (D-14) behind "flaky".

## Next step
Capture the failing assertion on the next failure (`-p no:randomly -x` run under `-n` load).
Then widen the headroom without losing what the test proves. The test needs
`timeout / 2 < build < timeout`, so that two queued builds pass the timeout together while each
fits alone. Slack only grows if both numbers are scaled up: for example, builds of 1.2 s under a
2.0 s timeout give 0.8 s of slack and cost about 1.2 s more test time. Revisit at the next failure, or before phase 7 closes.
