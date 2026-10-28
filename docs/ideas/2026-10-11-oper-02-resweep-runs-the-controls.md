# Phase 7's linux/amd64 re-sweep runs the known-bad controls, not only the builder

Date: 2026-10-11
Source: the PR #10 CI failure (quick 261011-fbb)
Related files:
- docs/architecture/decision_log.md (L11)
- tests/test_solid.py
- bench/thread_spike/helical.py
- bench/RESULTS.md

## Context
L11's known-bad list was measured on macOS arm64 only, and the container block covered the
builder alone. On linux/amd64, five of the 15 rows behave differently: (2.5, 0.45, 4.5),
(2.5, 0.45, 10.0), (6.0, 1.0, 10.0) and (8.0, 1.25, 80.0) raise `Null TopoDS_Shape`, and
(20.0, 2.5, 200.0) is two solids (see L11, platform note). The THRD-04 test row
(6.0, 1.0, 10.0) failed CI and was swapped for (8.0, 1.25, 10.0).

## Why it matters
THRD-04's positive-control test needs rows that are silent-wrong on the platform it runs on,
and CI and the image are linux/amd64. A control that raises fails the test instead of
exercising the volume gate. The 2026-10-11 evidence is one emulated, ad-hoc run.

## Next step (done)
Revisit when Phase 7 (OPER-02) is planned. The linux/amd64 re-sweep runs the `controls` block
(`naive_sweep_fuse`, `one_pipe`) natively, next to the builder, and records it as a
`bench/RESULTS.md` entry. Then check the THRD-04 test rows and the L11 known-bad list against it.

## Outcome
Done in Phase 7. Run 40646142406 ran the 69 control rows on linux/amd64 (`### controls, run
40646142406` and `#### controls against L11 and the THRD-04 test rows` in `bench/RESULTS.md`). The
one-pipe twist agrees with L11 on all 40 rows; the naive fuse differs in outcome on 8 of 29. The four
THRD-04 test rows still fail silently on the runner, so no test row changes. L20 records it.
