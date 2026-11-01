# The queued-request timeout test flakes under full-suite load

Severity: must
Status: resolved
Date: 2026-10-28
Resolved in: this commit — `test(pool): give the queued-request timeout test twice the slack under load`
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

## Failure record
2026-10-28, plan 07-06, the pre-commit `make verify` of the docs commit after 2a0916b, under
`-n` load (1 failed, 4310 passed in 193.26s). The failing assertion, `tests/test_pool.py:615`:

```
>           assert results == [b"", b""]
E           AssertionError: assert [BuildTimeout...or pending.')] == [b'', b'']
E             At index 0 diff: BuildTimeout('Build exceeded its 1s per-build timeout. Try a coarser quality.') != b''
```

Captured log: one `worker.replaced` record, `"slot": 0, "cause": "timeout"`. Index 0 is the
first request, the one with no build ahead of it: its own 0.6 s sleep ran past its 1.0 s timeout.
So this failure is not the queue-aware deadline (D-14) cutting the queued request. It is the
first build's 0.4 s of headroom being used up on a loaded host, which is what the ASSUMPTION above
says.

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

## Resolution
The owner chose to fix it now (2026-10-28), after the fourth failure that day: on the 07-17 plan
amendment commit, which passed on the retry. The test now builds for 1.2 s twice under a 2.0 s
timeout and asserts a wall time above 2.0 s. It still holds `timeout / 2 < build < timeout`
(1.0 < 1.2 < 2.0). The first build has 0.8 s of slack against its own clock, up from 0.4 s, for
about 1.2 s more test time.

Checked before the commit:
- The test passed 3 of 3 runs alone.
- With the queue-aware sum removed from `_run_with_timeout` in `src/screw/pool.py`
  (`deadline = timeout`), the test fails on `assert results == [b"", b""]`: the second request
  ends as `BuildTimeout`. So the test still proves D-14.

Not proven: that 0.8 s of slack holds under every load. If the test fails again, reopen this
item with the captured assertion.
