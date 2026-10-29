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
| must | [The cost model admits a part it refuses once its head height leaves the fitted band](active/2026-10-29-cost-model-admits-out-of-fit-head-heights.md) | 07-15's out-of-band readings (G28 guard since bc7b2ab) |
| must | [Twenty parts inside the L20 walls pass validation and then fail in the kernel](active/2026-10-29-in-wall-parts-the-kernel-refuses.md) | before phase 7 closes, or the first release |
| nice | [The refused preview's status sentence runs under the Fit button](active/2026-10-29-status-sentence-runs-under-fit.md) | the phase 7 UAT, or the next change to the viewport overlay |
| nice | [The shank-fold warning prints its numbers with :g, so a value near the 0.0001 mm line can read as the wrong side of it](active/2026-10-28-shank-fold-warning-rounds-the-numbers-it-compares.md) | the next change to the warning texts |
| must | [No test holds that a nut outside the measured range is still a 200 from the API](active/2026-10-24-measured-range-nut-api-200-untested.md) | the next edit to the nut warnings, or before the first release (after Phase 7) |
| must | [The nut's countersink cutter ends at a negative radius at a coarse pitch and the kernel refuses a valid nut](active/2026-10-21-nut-countersink-cutter-crosses-the-axis-at-a-coarse-pitch.md) | before the nut's pitch or clearance range is relied on, with the root-radius floor item, on a request for a nut whose void root ratio r/d is near or below 0.12, or before a void guard is relied on |
| nice | [Three pair and CLI tests couple to prose, internal names and a wall-clock bound](active/2026-10-21-brittle-pair-and-cli-tests.md) | the first time the 5 s assertion fails, or the next edit to the pair orchestration tests |
| must | [screw pair's verdict exit codes 1 and 2 are also what a crash and a refused parameter return](active/2026-10-21-screw-pair-exit-codes-collide-with-failure-exits.md) | before any script, workflow or doc branches on the exit code, or the first release (after Phase 7) |
| must | [A bolt's under-head fillet ring can overhang the head's flats with no warning](active/2026-10-21-fillet-ring-can-overhang-the-head-flats.md) | before the first release (after Phase 7), or when the fillet or the head next changes |
| must | [The required CI test job tripled: two pair tests run 20x slower on the runner than locally](active/2026-10-20-ci-test-job-tripled-by-two-pair-tests.md) | phase 5 close, or the `test (3.12)` job passing 20 min |
| must | [The ISO standards Phase 5 reads are not purchased: rows come from free GOST texts of older editions](active/2026-10-20-iso-standards-not-purchased.md) | before the first release (after Phase 7), or any public release that claims ISO conformance |
| nice | [The tip cut fails in the sliver of thread_length just above the cone's axial length](active/2026-10-20-tip-cone-degenerate-boolean-at-the-cone-length.md) | revisit if a real size meets the window, or when the tip length is next changed |
| must | [The pair tier has not run on ubuntu: pair.yml can be dispatched only once it is on main](active/2026-10-14-first-pair-yml-dispatch.md) | the Phase 5 PR's merge to `main` |
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
| [The nut's size ceilings are interim; its fine-STL caps are measured on macOS arm64 only](resolved/2026-10-14-nut-interim-bounds.md) | this commit — refactor(calc): retire the per-row fine-STL caps the cost model replaced (07 D-08, D-17) |
| [The default cap can pick a thread shorter than any turn count the cost model was fitted on](resolved/2026-10-29-default-cap-lands-below-the-fitted-turns.md) | this commit — feat(calc): the default cap stops at the fewest turns the cost model was fitted on (07 B-03) |
| [The queued-request timeout test flakes under full-suite load](resolved/2026-10-28-queued-request-timeout-test-flakes-under-full-suite-load.md) | this commit — test(pool): give the queued-request timeout test twice the slack under load |
| [The nut's lead-in countersink piece gate refuses a valid nut at huge s and small clearance](resolved/2026-10-21-nut-lead-in-gate-refuses-a-valid-nut-at-huge-s.md) | a804806 — feat(calc): re-measured MAX_TURNS, MIN_TAIL_MM and field ceilings as cited kernel walls (07 D-08) |
| [Root radii down to about 3e-5 mm pass validation and then fail in the kernel with a generic message](resolved/2026-10-11-root-radius-floor-is-not-the-kernel-boundary.md) | 683a434 — feat(calc): refuse a root radius below the measured kernel floor (07 D-18) |
| [The info document prints a whole head chamfer for a tiny angle the kernel refuses](resolved/2026-10-24-info-document-cannot-see-a-kernel-refused-head-chamfer.md) | this commit — fix(06.1): warn below the measured limit of the head chamfer instead of printing its rows |
| [The nut has no fine-STL cap: its caps need their own measurement run](resolved/2026-10-14-nut-fine-stl-caps-unmeasured.md) | this commit — fix(05-19): refuse a nut's fine STL past its measured cap (plan 05-19) |
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
