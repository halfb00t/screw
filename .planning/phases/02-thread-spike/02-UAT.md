---
status: complete
phase: 02-thread-spike
source: [02-01-SUMMARY.md, 02-02-SUMMARY.md, 02-03-SUMMARY.md, 02-04-SUMMARY.md, 02-05-SUMMARY.md, 02-06-SUMMARY.md, 02-07-SUMMARY.md, 02-08-SUMMARY.md]
started: 2026-10-13T08:01:14Z
updated: 2026-10-13T08:44:48.952Z
restarted_from: "02-UAT.md at a0c7923 (4 passed, built from 02-VERIFICATION.md; the owner's 2026-10-09 rulings on the PR 5 review evidence and on the 02-08 prohibitions P1-P3 live there)"
---

## Current Test

[testing complete]

## Tests

### 1. Owner rulings in 02-SPIKE.md recorded faithfully (02-01)
expected: Read `.planning/phases/02-thread-spike/02-SPIKE.md` lines 15-65, "## Owner rulings (D-01 checkpoint, 2026-10-06)". The profile pin (`basic`), the four coefficients (H = (sqrt(3)/2) P; crest flat P/8 at d/2; root flat P/4 at d/2 - 5H/8; flanks at 60 degrees), R0-R5, the pre-registered values and the "defaults" ruling on the four protocol questions are what you ruled and nothing more: no ruling or ISO value appears that you did not give, and every value nobody re-read from the standard (the R5 nut heights, the 30 degree tip cone) carries UNVERIFIED. Your verbatim replies ("basic, defaults", "today", "defaults") are quoted as given. No test asserts the faithfulness of a recorded human ruling.
result: pass

### 2. Closed form and kernel section match the pinned basic profile (02-02)
expected: The closed form codes the pinned coefficients and nothing else: crest flat P/8 at d/2, root flat P/4 at d/2 - 5H/8, H = (sqrt(3)/2) P, flanks at 60 degrees. It lives in `src/screw/calc/thread.py` (pin in the docstring at line 3; `sharp_height` line 41, `section_radius` line 55, `section_area` line 75, `closed_volume` line 87; Phase 3 moved it there from `bench/thread_spike/maths.py`). The tests prove internal consistency only: the section area equals half the integral of the radius squared (`tests/test_bench.py:491`) and the kernel volume of the sewn twist lands within 1.7e-6 of it. Agreement with ISO 68-1:2023 rests on your reading of 2026-10-06; nobody here re-read the standard. Confirm the coefficients as coded are the ones you pinned.
result: pass

### 3. Pre-registered thresholds and rules express your intent for D-07, D-09, D-10 and D-20 (02-03)
expected: `02-SPIKE.md` "## Protocol inputs" (lines 114-221) and "## Rules" (222-244): the 30 s request budget (`BUDGET_S`) and 64 MiB raw-plus-gzip-1 (`BUDGET_BYTES`) as the over-budget cap, never an escape; the K rule's order (fewest fine triangles, then STEP bytes, then smaller K); the 2x estimator tie, broken by median seconds only on a decisive run; T_gate = 10 x the winner's largest error rounded up to one significant figure; a timeout is a cap under the pass bar, never an escape. These are the plan's and the research's values, coded and tested for consistency with the plan text, and were open to the PR 1 review (D-19). No test can say a pre-registered rule is wise: you accept them as the registration you meant.
result: pass

### 4. Ruled-surface reference package: legitimacy checkpoint and scratch install (02-04)
expected: You approved cq_warehouse at a blocking legitimacy checkpoint on 2026-10-06 (reply "approved", `02-04-SUMMARY.md` lines 191-195) on the evidence shown then: pinned commit `daa46507ecc429c0e2dce11d9d5ffd09b12a42af` (authored 2023-09-24), licence Apache-2.0, owner `gumyr`. It was installed only from that commit, `--no-deps`, into `$HOME/.cache/screw-spike/cq_warehouse-daa4650` outside the repository, and the controls block reaches it only through `SCREW_SPIKE_CQW` in a second worker; `git grep -n warehouse -- pyproject.toml requirements.txt` exits 1 (re-run today). Confirm the approval stands as recorded.
result: pass

### 5. PR 5 (harness and protocol) had a cross-CLI review before any data existed (02-06)
expected: GitHub holds no review object or comment on PR 5 (`gh pr view 5` today: reviews 0, comments 0, reviewDecision empty; merged 2026-10-08T09:28:22Z by halfb00t). The evidence is indirect: `02-SPIKE.md` lines 166-167 cite review findings F4 (`cli.COMPLETE_BLOCKS`) and G6 (`cli.ESCAPE_SOURCES`), added by `adccd4a` on 2026-10-08; 22 `fix(02-06)` commits follow the Task 1 commit by 10 to 16 hours; you merged the PR yourself. Which CLI reviewed, and the full findings, are unverified from the repo. You accept this as satisfying D-19 and the AGENTS.md rule that whoever wrote the diff does not review it. (You accepted the same on 2026-10-09 in the previous UAT; this is the re-ask after the restart.)
result: pass

### 6. Campaign 2026-10-08-a: the two departures and four non-decisive blocks are acceptable evidence for L11 (02-07)
expected: The campaign ran on an Apple M5 Max (18 CPUs, 64 GiB, Python 3.12.15), not the registered M2 Max, with the kernel pair identical (cadquery 2.8.0 / cadquery-ocp 7.9.3.1.1) under your option A (no Environment amendment); and you overrode R4 (launched from the agent session with applications open). Result: ksweep, grid and frontier non-decisive ("non-decisive after 900 s (31 readings)"), container non-decisive by construction; ladder, trim, controls, rss and pair decisive. The seconds-based turn caps and the estimator tie-break read "not established"; nothing was re-run toward a pass. Both departures are stated at the head of `bench/RESULTS.md` "## Thread spike (Phase 2)" (line 296) and in L11 "Conditions of the record". You accept this record as the evidence L11 was decided on.
result: pass

### 7. L11 reads as you decided it (02-08)
expected: `docs/architecture/decision_log.md` lines 284-427, "## L11 — The thread is a sewn twist-section at K = 3, volumes are `BRepGProp` at eps 1e-6 gated at 9e-5, and the pair proof is not falsifiable at M18 (blocks Phase 5)". Every required part is present (Profile, Construction, Volume estimator, Turn cap per size, Pair check, Known-bad inputs for THRD-04, Container, Escape clause, Conditions of the record, Inputs still UNVERIFIED); every number cites a `2026-10-08-a-<block>` run; a value no rule produced reads "not established"; the escape-clause consequence you chose (Phase 5 not planned until the roadmap is revised) is recorded as yours. The final wording differs from the Task 2 draft you approved only in the date line, the escape-clause direction and one line rewrap. (P1-P3 of the previous UAT passed on 2026-10-09 on the verifier's non-authoritative LLM-judge reads.)
result: pass

### 8. 02-SPIKE.md has Question, Owner rulings and Results in order (02-01 D1, automated)
expected: 02-SPIKE.md exists with ## Question, ## Owner rulings (D-01 checkpoint, 2026-10-06) and an exact ## Results line, in that order
result: pass
source: automated
coverage_id: 02-01-D1

### 9. STATE.md ISO 68-1 blocker replaced by the closure note (02-01 D2, automated)
expected: STATE.md ISO 68-1 blocker line replaced with the closure note; the ISO 4753 half kept
result: pass
source: automated
coverage_id: 02-01-D2

### 10. smoke builds one M6 rod in a worker and reports honestly (02-02 D1, automated)
expected: smoke builds one M6 right-hand 5-turn sewn rod (K=5) in a worker subprocess, checks it against the closed form, prints a report whose load readings carry their UTC time, says it is not a campaign run, exits 0 only when the row is ok
result: pass
source: automated
coverage_id: 02-02-D1

### 11. Row verdict classes (02-02 D2, automated)
expected: Row verdict: silent_wrong on solids != 1, invalid, |precise rel err| > T_PASS (sign kept, exact boundary), or a checked mesh that is open, inside out or off the closed form; failure/timeout/worker_died keep their class with null measurements
result: pass
source: automated
coverage_id: 02-02-D2

### 12. Worker isolation (02-02 D3, automated)
expected: Worker isolation: a dead child (exit code, signal -11), a timeout and garbage output are each one recorded row and the parent survives
result: pass
source: automated
coverage_id: 02-02-D3

### 13. wait_quiet release rule (02-02 D4, automated)
expected: wait_quiet releases only after three consecutive readings strictly under 1.5; exact 1.5 resets, nextafter(1.5, 0) counts; a host that never quiets is non-decisive with 31 readings; every reading carries its UTC time
result: pass
source: automated
coverage_id: 02-02-D4

### 14. Protocol guard (02-02 D5, automated)
expected: The guard: check-protocol exits 2 printing 'protocol guard: refused' while origin/main has no protocol; protocol_guard holds only when fetched, texts equal before '## Results' and origin/main's protocol commit is an ancestor of HEAD, and names every failed check
result: pass
source: automated
coverage_id: 02-02-D5

### 15. Import-linter contract keeps the harness kernel-free (02-02 D6, automated)
expected: Import-linter contract: bench.thread_spike.maths, .verdict, .runner, .__main__ and bench.quiet reach cadquery/OCP by no path; the six older contracts stay KEPT with root_packages = [screw, bench]
result: pass
source: automated
coverage_id: 02-02-D6

### 16. The D-03 grid is exact (02-03 D1, automated)
expected: The D-03 grid is exact: 1790 lengths per hand with the pinned per-size counts (M2 60 ... M20 240), both ends included, coincident integer-turn and integer-mm lengths listed once, 1781 under the alternative lower bound with rows lost only at M8-M20; integer turns decided on Fractions where the float product drifts
result: pass
source: automated
coverage_id: 02-03-D1

### 17. The D-04 frontier steps (02-03 D2, automated)
expected: The D-04 frontier starts at the first multiple of 5 turns strictly above the standard max (M2 55, M2.5 60, M6 65, M20 85), steps by 5 and ends at 250
result: pass
source: automated
coverage_id: 02-03-D2

### 18. Rod and void row records (02-03 D3, automated)
expected: A rod row records preview and fine meshes, gzip-1 on the named presets, the STL check under a triangle ceiling (a skipped check recorded as not checked) and STEP; a void row records the postcondition only and refuses a mesh or STEP request; each optional field is set exactly when asked for
result: pass
source: automated
coverage_id: 02-03-D3

### 19. Budget and stop rules at their thresholds (02-03 D4, automated)
expected: Budget and stop rules pinned at their thresholds: 64 MiB raw plus gzip-1 inside and one byte more over; exactly 30.0 s inside and the next float over; a non-decisive gate reads 'seconds not established', never over; frontier stops name the first non-ok row and use the clock only when decisive
result: pass
source: automated
coverage_id: 02-03-D4

### 20. K, estimator and gate rules (02-03 D5, automated)
expected: K, estimator and gate rules: select_k takes the fewest fine triangles then STEP bytes then the smaller K and excludes any K with a non-ok row; select_estimator applies the 2x tie rule; gate_tolerance rounds 10x the error up to one significant figure (7.6e-6 to 8e-5, 1e-5 to 1e-4, 2.7e-5 to 3e-4)
result: pass
source: automated
coverage_id: 02-03-D5

### 21. Pass bar, escape clause and turn caps (02-03 D6, automated)
expected: Pass bar, escape clause and turn caps: any silent_wrong, failure or worker_died row of either hand fails the bar naming the row; a timeout is an over-budget cap when decisive and makes the bar not established otherwise; per-size construction, bytes and seconds caps with their reasons, seconds only from a decisive run
result: pass
source: automated
coverage_id: 02-03-D6

### 22. run <block> is guarded and never overwrites (02-03 D7, automated)
expected: run <block> is guarded and never overwrites: a bad or already-recorded run id and a --k-from error exit 2 before the guard, a refused guard writes nothing, the header is the first JSONL line, K comes from the K-sweep record, an empty block raises; the unlanded branch refuses the real command
result: pass
source: automated
coverage_id: 02-03-D7

### 23. Blocks take their rows from maths and run on smoke subsets (02-03 D8, automated)
expected: Blocks take their rows from maths and run on smoke subsets: grid 4 x 1790 rows from lengths(), ksweep 192, frontier walks to 250 or the first stop, ladder 16 with every preset; every block's smoke subset exits 0 end to end against the real kernel
result: pass
source: automated
coverage_id: 02-03-D8

### 24. verdict --campaign recomputes from the raw record (02-03 D9, automated)
expected: verdict --campaign recomputes every class from the raw record (a stored class of ok on a two-solid row still fails), lists missing blocks and never passes on them, and exits 0 only on a clean pass
result: pass
source: automated
coverage_id: 02-03-D9

### 25. Negative control reproduced and never ok (02-04 D1, automated)
expected: The negative control naive_sweep_fuse is reproduced from the research recipe and never classifies ok: M6 L10 gives 1 solid, valid, precise ratio 0.238384 (research 0.238), M2 L6 0.274107 (0.274), M6 L20 and L40 raise Null TopoDS_Shape; the known-bad inputs (naive, 1 solid, valid, ratio below 0.5) are listed with exact parameters for Phase 3's THRD-04 test and the recipe stays importable
result: pass
source: automated
coverage_id: 02-04-D1

### 26. One-pipe and ruled-surface comparison rows in an isolated worker (02-04 D2, automated)
expected: One-pipe twist and the ruled-surface reference run on the sample sizes, right hand, judged by the same classify_row; the ruled rows run only in a second worker whose PYTHONPATH carries SCREW_SPIKE_CQW, the default worker cannot see the package, and the controls block refuses (exit 2, nothing written, before the guard) when the variable is unset or the package is not importable there
result: pass
source: automated
coverage_id: 02-04-D2

### 27. Tip-chamfer-trim row is cost evidence only (02-04 D3, automated)
expected: The tip-chamfer-trim row, one per size and hand at the standard max, records trim seconds and the request cost build + trim + slower export; it is judged on solids, isValid and the preview check only, never against a closed form, never enters the pass bar, and labels the 30 degree cone UNVERIFIED (ISO 4753 unread)
result: pass
source: automated
coverage_id: 02-04-D3

### 28. Peak RSS from a fresh --once child only (02-04 D4, automated)
expected: Peak RSS exists only from a fresh --once child, read after the one mesh and gzip-1 and before any STL check; a persistent worker records none and refuses a gzip-table request; every printed figure is labelled 'fresh child, this row only'; the L19 gzip table and the selected level print only for rows that asked for one
result: pass
source: automated
coverage_id: 02-04-D4

### 29. Container block under linux/amd64 (02-04 D5, automated)
expected: The container block runs the locked construction over the full D-03 grid, rod and void, both hands, through the same JSON-lines worker in screw:latest under linux/amd64 with bench/ mounted read-only (list argv, --rm, docker kill and a new name on timeout), validity, solid count and volume only; a failure or silent_wrong container row counts toward the pass bar and the escape clause; the run is never decisive and refuses (exit 2) when docker or the image is absent
result: pass
source: automated
coverage_id: 02-04-D5

### 30. interference_area is m-free and kernel-free (02-05 D1, automated)
expected: interference_area is m-free and kernel-free: M6 with m = 5.2 reads 12.213, 14.1335 and 16.1427 for the half-pitch control at c = 0.10, 0.05 and 0 and 4.3627 for the matched pose at c = -0.05 (each within 1e-3), and exactly 0 for the matched pose at every proof clearance; the M20 control at c = 0.10 reads 429.631 as in research
result: pass
source: automated
coverage_id: 02-05-D1

### 31. cell_verdict is D-12/D-14 exactly as written (02-05 D2, automated)
expected: cell_verdict is D-12/D-14 exactly as written (owner ruling R1): proven only when all 3 matched poses are empty and all 3 controls fire within PAIR_BAND of the closed form; c <= 0, an unfinished cell, a nut body off its closed form, a control that cannot fire and an off-band or empty control are inconclusive with the reason; a non-empty matched pose is violated; the variant rules are reported and never feed it
result: pass
source: automated
coverage_id: 02-05-D2

### 32. Falsifiability, excluded clearances, mixed hand and sensitivity (02-05 D3, automated)
expected: size_falsifiable, excluded_clearances, mixed_hand_violated and sensitivity_ok implement D-14's rules and D-11's sensitivity check; a size falsifiable on neither or one hand, or whose mixed pair did not read violated, fires the escape clause in the verdict naming the size
result: pass
source: automated
coverage_id: 02-05-D3

### 33. pair.py builds, places and reads a cell in a child (02-05 D4, automated)
expected: pair.py builds the rod piece and the nut once per cell, places the nut by screw motion plus the half-pitch control, raises when the rod does not cover the placed nut, and reads the boolean with its filler kept alive; a real child reads a real M2 control at the closed form, and a child that dies, stalls or babbles is one cell with no reading in it
result: pass
source: automated
coverage_id: 02-05-D4

### 34. The pair block and its report (02-05 D5, automated)
expected: The pair block runs per size both hands at every diagnostic and proof clearance (six readings each), the mixed pair at the proof clearances (matched poses only), and two reference K values on four sizes; its report prints every volume, the control's closed form, solids, diagnostics and verdict, falsifiability, excluded clearances, the mixed-hand and sensitivity lines, the reference K rows and the variant table under 'Variant rules (reported, never the verdict)'
result: pass
source: automated
coverage_id: 02-05-D5

### 35. campaign --run-id runs the nine blocks in order (02-05 D6, automated)
expected: campaign --run-id PREFIX runs the nine blocks in protocol order as PREFIX-<block>, K from PREFIX-ksweep by the rule, logs refused and interrupted blocks in PREFIX-campaign.md and goes on, prints the verdict and 'campaign finished', exits with the verdict's code, and refuses (exit 2, nothing written) a long prefix, a recorded block, or a protocol that has not landed
result: pass
source: automated
coverage_id: 02-05-D6

### 36. 02-SPIKE.md on main holds the protocol in order, written before any run (02-06 D1, automated)
expected: 02-SPIKE.md on main holds Question, Owner rulings, Environment, Method, Protocol inputs, Rules, Predictions, Escape clause, then Results, in that order, written before any run
result: pass
source: automated
coverage_id: 02-06-D1

### 37. Every harness constant is tied to the protocol by a test (02-06 D2, automated)
expected: Every harness constant is tied to the protocol by a test that parses the Protocol inputs, PITCH and NUT_HEIGHT tables; a second test asserts the six required headings exist above Results
result: pass
source: automated
coverage_id: 02-06-D2

### 38. bench/README.md carries the thread spike section (02-06 D3, automated)
expected: bench/README.md carries the section 'Thread spike (Phase 2)'
result: pass
source: automated
coverage_id: 02-06-D3

### 39. PR 5 merged, guard held, runs branch clean, src/ untouched (02-06 D4, automated)
expected: PR 5 is MERGED, the protocol guard holds on gsd/phase-02-thread-spike-runs, no campaign record exists on origin/main, the runs branch has no commit of its own, and src/ is untouched by the diff against origin/main
result: pass
source: automated
note: "'No campaign record exists on origin/main' is the state at PR 5's merge (`fd40abc`, 2026-10-08), the pre-registration point 02-06 D4 checks; PR 6 (`7615de2`) landed the campaign record afterwards. The pass covers that ordering, not main today."
coverage_id: 02-06-D4

### 40. Nine block records and the campaign log committed with sha256 (02-07 D1, automated)
expected: The nine block records and the campaign log are committed under bench/results/thread-spike/ and every JSONL's sha256 appears in bench/RESULTS.md
result: pass
source: automated
coverage_id: 02-07-D1

### 41. Each embedded output in RESULTS.md is byte-equal to its file (02-07 D2, automated)
expected: Each embedded output in bench/RESULTS.md equals its .md file byte for byte (nine block entries plus the campaign entry)
result: pass
source: automated
coverage_id: 02-07-D2

### 42. What was measured is the code that was reviewed (02-07 D3, automated)
expected: bench/thread_spike/ and bench/quiet.py are identical to origin/main's, so what was measured is the code that was reviewed
result: pass
source: automated
coverage_id: 02-07-D3

### 43. make verify green with the records in place (02-07 D4, automated)
expected: make verify is green with the records in place
result: pass
source: automated
coverage_id: 02-07-D4

### 44. Verdict re-run equals the campaign log and exit 1 is recorded (02-08 D1, automated)
expected: The verdict re-run on the committed records equals the campaign log's verdict section and its exit code (1) is recorded in bench/RESULTS.md
result: pass
source: automated
coverage_id: 02-08-D1

### 45. Results and Verdict answer the four questions by citation (02-08 D2, automated)
expected: 02-SPIKE.md Results and Verdict answer the four questions by citation, and nothing above `## Results` changed
result: pass
source: automated
coverage_id: 02-08-D2

### 46. No thread builder in src/ when L11 is committed (02-08 D4, automated)
expected: No thread-building field or builder exists in src/ when L11 is committed (SC4)
result: pass
source: automated
coverage_id: 02-08-D4

### 47. STATE.md and ROADMAP.md carry the escape-clause consequence (02-08 D5, automated)
expected: STATE.md and ROADMAP.md carry the escape-clause consequence (Phase 5 not planned until the roadmap is revised)
result: pass
source: automated
coverage_id: 02-08-D5

### 48. make verify green with the L11 commit (02-08 D6, automated)
expected: make verify is green with the L11 commit
result: pass
source: automated
coverage_id: 02-08-D6

## Summary

total: 48
passed: 48
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
