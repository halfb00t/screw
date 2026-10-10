# Two thread spike protocol amendments wait for the owner before the next campaign

Severity: must
Status: active
Date: 2026-10-10
Source: quick task 261010-lgv (the Phase 2 harness review fixes) plus the owner ruling 2026-10-10 (Task 1), "amend-defer": WR-03 and IN-02 are deferred, trigger "before the next campaign". The owner's sign-off is that ruling.
Related files:
- bench/quiet.py:52 and bench/thread_spike/__main__.py (`wait_quiet()` in `run_block`, WR-03: `decisive` is fixed at block start)
- bench/thread_spike/verdict.py:1346 (`PAIR_TIMEOUT_S`, IN-02: 600 s against the worst case its own comment cites)
- .planning/phases/02-thread-spike/02-REVIEW.md (WR-03, IN-02)
- .planning/phases/02-thread-spike/02-SPIKE.md (D-17, the Protocol inputs table)

## Context
The Phase 2 harness review (`02-REVIEW.md`) found twelve items. Quick task 261010-lgv fixed
WR-01, WR-02, WR-04, WR-05, IN-01, IN-05 and IN-06, and skipped IN-03, IN-04 and IN-07 with
reasons (`02-REVIEW-DISPOSITION.md`). Two items touch pre-registered protocol text, so
fixing them is an amendment the owner rules on, not a bug fix. The owner deferred both.

- **WR-03.** `Campaign.decisive` is fixed from the release at the start of a block (D-17). A
  grid or frontier block runs long enough for the host to get busy part-way through, and
  nothing re-reads the load, so such a block still carries `decisive: true` and every timing
  claim that depends on it (the seconds cap, the 30 s frontier stop, the estimator tie-break,
  over-budget) is treated as established. The review's fix is a load reading between rows,
  recorded in the JSONL, with a pre-registered rule that downgrades `decisive` when a reading
  is at or above `QUIET_BAR` before a timing-bearing row. Both the readings and the rule are
  new protocol text.
- **IN-02.** `PAIR_TIMEOUT_S` is 600 s, pre-registered in the Protocol inputs (owner: "they
  stand"). Its comment cites 16-121 s per M20 boolean and six booleans per cell: 726 s of
  booleans alone, plus the rod and nut builds. A slow M20 cell would be killed and recorded
  as an inconclusive timeout. Campaign 2026-10-08-a-pair recorded no timeout cell, so this
  is latent. The fix is to derive the deadline from the cited worst case or to cite the
  measurement that justifies 600; either changes a pre-registered input.

## Why it matters
Neither changes the recorded campaign 2026-10-08-a. A later campaign (a re-run after the
Phase 5 roadmap revision, or Phase 7's re-measure) could carry `decisive: true` through a
block that went noisy half-way (WR-03), or lose a slow M20 pair cell to a deadline its own
comment says is too short (IN-02). Either way the verdict rules would be applied to evidence
that looks well-formed.

## Next step
Before the next thread-spike campaign runs, put each amendment to the owner: WR-03 (the load
readings and the downgrade rule) and IN-02 (the deadline and its derivation). Each accepted
one is a PR that post-dates the protocol (D-19), with its tests and a dated note in
`02-SPIKE.md`, as the WR-01 and WR-04 notes were. A rejected one is closed here with the
owner's reason. Move this item to `resolved/` when both are decided.

<!-- On resolve: set Status: resolved, add `Resolved in: <commit sha>`,
     git mv into resolved/, move the INDEX row to Resolved — same commit as the fix. -->
