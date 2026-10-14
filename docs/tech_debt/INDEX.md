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
| must | [The nut has no fine-STL cap: its caps need their own measurement run](active/2026-10-14-nut-fine-stl-caps-unmeasured.md) | before the nut fine STL can be offered as bounded |
| must | [Root radii down to about 3e-5 mm pass validation and then fail in the kernel with a generic message](active/2026-10-11-root-radius-floor-is-not-the-kernel-boundary.md) | measure the floor; before L12's boundary claim is relied on |
| must | [A valid in-cap request (d=100, length=200, default pitch) exceeds both interim backstops and is unrecorded](active/2026-10-11-default-pitch-d100-length200-exceeds-both-interim-backstops.md) | owner severity ruling; measure at the 30 s kill point |
| nice | [The M18 probe's --one entry has no deadline when started by hand during a run](active/2026-10-14-m18-probe-one-entry-has-no-deadline-during-a-run.md) | the probe is reused, or the owner wants the entry closed completely |
| nice | [check_solid discards the volume estimator's own error estimate](active/2026-10-11-check-solid-ignores-the-volume-error-estimate.md) | when the gate or T_GATE next changes |
| must | [Two thread spike protocol amendments wait for the owner before the next campaign](active/2026-10-10-spike-protocol-amendments-before-next-campaign.md) | before the next thread-spike campaign runs |
| must | [Interim runtime bounds are spur's figures, not screw's measurements](active/2026-10-05-interim-runtime-bounds.md) | Phase 7 operability re-sweep (OPER-02) |
| must | [bench.memory samples too coarsely to read a peak off a corpus that runs in seconds](active/2026-10-06-bench-memory-sampling-is-too-coarse-for-short-corpora.md) | before the Phase 7 memory sweep (OPER-02, OPER-03) |
| nice | [The infrastructure forked from spur is not a shared package](active/2026-10-05-shared-infra-extraction.md) | fired: the pool.py race guard (L09) — owner decides extract vs fix twice |
| nice | [Enji Guard not connected](active/2026-10-05-enji-guard-not-connected.md) | first product code on `main`, or the owner decides they want continuous AI audit |

## Resolved

| Item | Resolved in |
|---|---|
| [The web page rounds every displayed number in the browser](resolved/2026-10-06-ui-rounds-displayed-numbers.md) | this commit — fix(ui): show the API's numbers unrounded, with the designation, groups and notes (plan 04-13) |
| [derive() prints turns and volume for a length below MIN_TAIL_MM, which the builder refuses](resolved/2026-10-11-info-document-prints-numbers-for-a-length-the-builder-refuses.md) | this commit — fix(calc): report no turns or volume for a thread too short to build (plan 04-05) |
| [The fine-STL refusal applies the right-hand caps to left-hand parts and misstates what L11 measured](resolved/2026-10-11-fine-stl-cap-applies-right-hand-rows-to-left-hand-parts.md) | this commit — fix(calc): key the fine-STL caps by hand from the grid records and say what was measured (plan 04-02) |
| [A failed update hides the standing warnings while the last mesh stays on screen](resolved/2026-10-06-ui-hides-warnings-on-failed-update.md) | 909dec3 — fix(ui): keep the warnings of the mesh on screen when an update fails (plan 03-05) |
| [The web page drops a foreign or unparseable hash key silently](resolved/2026-10-06-ui-drops-foreign-hash-keys.md) | 05fb4ed — fix(ui): refuse a link with a foreign, repeated or unreadable key (plan 03-05) |
| [A repeated query key or CLI flag silently drops one of two explicit values](resolved/2026-10-06-repeated-query-key-silently-wins.md) | eaaac85 (API) and d849557 (CLI) — fix(app): refuse a repeated query key before validation, feat(params): add left_hand to every kind and build left-hand threads from the API and CLI (plan 03-04) |
| [The pool's dying-worker test failed once under host load](resolved/2026-10-06-test-pool-dying-worker-flake.md) | ef37f23 (PR #7) — test(pool): free the wedged test's dead-worker semaphores before it returns |
| [The thread spike harness carries five open review warnings that PR 2 may not fix](resolved/2026-10-09-thread-spike-harness-review-findings.md) | 0e2f437 -- fix(bench): refuse a run while the harness has uncommitted changes and report the HEAD it started at |
| [A collapsed thin solid passes the validity check and is served as a 200](resolved/2026-10-06-collapsed-thin-solid-served-as-200.md) | de9304e — fix(solid): refuse a broken export and close the collapsed-solid blocker (plan 03-01) |
| [The in-process pair tests in tests/test_bench.py end the pytest process with exit 139](resolved/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md) | cfe00a4 — test(bench): read pair.common only in a child so the pytest worker exits clean |
