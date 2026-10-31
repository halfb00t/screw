---
phase: 07-operability-re-sweep
plan: 20
subsystem: infra
tags: [operability, full-tier, ci, merge-gate, make-check, R5, R12, R28, R29, L26, L27, D-12, D-13]
status: complete

requires:
  - phase: 07-operability-re-sweep
    provides: "07-19 the judged full set (1056 points), its pull_request trigger and the L27 gate; 07-18 the required bounds tier; 07-16 and 07-21 the timeouts and the serving knobs"
provides:
  - "bench/results/phase-07/full-41161227951/: the full tier read green on the phase head 95a99da, 1056 of 1056 ok"
  - "bench/RESULTS.md `### full, run 41161227951`"
  - "the run ids for the verifier: every required ci.yml job and the full tier green on 4a2b536, and pr.land's two read-only checks returning no refusal there"
affects: [phase-07-verification, phase-07-ship]

estimate:
  tokens: 60000
  tasks: 2
actuals:
  tokens: 515        # chars/4 over the added lines of the plan's diff outside the run records (2060 chars); 149417 with the 40 JSONL files (595607 chars)
  tasks: 2
  commits: 1         # MEASURED: git rev-list --count 95a99da..4a2b536 (this SUMMARY's commit not counted)
plan_head_before: 95a99daf6b0d757bc6d9d2c25ee7ecedf876c222
plan_head_after: 4a2b536550ac573e790021da95e8c87fb83a2911

tech-stack:
  added: []
  patterns:
    - "a pull_request run's records carry the PR's merge sha as GITHUB_SHA; the RESULTS subsection names both the head and the merge sha"

key-files:
  created:
    - bench/results/phase-07/full-41161227951/
    - .planning/phases/07-operability-re-sweep/07-20-SUMMARY.md
  modified:
    - bench/RESULTS.md
    - bench/results/phase-07/runtime.json

key-decisions:
  - "The green path of Task 1 was taken: run 41161227951 at 95a99da passed, so no envelope widened and no under-prediction commit was made"
  - "OPER-01 and OPER-02 are ticked. OPER-03 is left Pending for the owner: the in-wall residual (must debt, before the first release) is a set of admitted parts that get a build error, so 'every allowed configuration builds' does not hold as written"

requirements-completed: [OPER-01, OPER-02]  # OPER-03 held for the owner's ruling (see below)

duration: about 50 min (02:43 to 03:31 UTC, 2026-10-31)
completed: 2026-10-31
---

# Phase 7 Plan 20: Proof on the head Summary

**The full tier read all 1056 points `ok` on the phase head 95a99da (run 41161227951), and its records are committed. On the head after that commit, 4a2b536, the full tier (41162982938) and all 7 required ci.yml jobs (41162982868) are green. `make pr.land`'s two read-only checks return no refusal there, and `make check` passes locally.**

## Performance

- **Duration:** about 50 minutes, 02:43 to 03:31 UTC on 2026-10-31. Most of it was waiting on runners.
- **Tasks:** 2 of 2
- **Commits:** 1, measured from the ledger. This SUMMARY's commit is not counted.

## Task 1: the full tier green on the head, recorded

- The push of 95a99da (07-19's last commit) had already started the `pull_request` full run 41161227951, so nothing was dispatched.
  - It completed `success` in about 15 minutes: 40 `measure` jobs, `followup-plan`, `verdict`, and `followup` skipped. The longest `measure` job took 453 s.
- The records were downloaded into `bench/results/phase-07/full-41161227951/`: 40 artifacts, 1056 readings, all `ok`.
  - The records' `GITHUB_SHA` is `769ebac`. That is the PR's merge commit of 95a99da onto `main` at `67a9d02`, which is what a `pull_request` run checks out. The RESULTS subsection names both shas.
- Judged again by committed code:
  - `python3 -m bench.oper verdict --set full --from bench/results/phase-07/full-41161227951` gives `full: 1056 points, 0 failures`.
  - `python -m bench.oper_sets envelope-check` against a scratch copy of fit.json gives `no reading exceeds its envelope`. The scratch copy is byte-identical afterwards. The largest ratio is 1.0, nut step bytes, at the point that set that envelope.
  - The largest cold wall is `iso4017:M16x160` at stl-fine: 28.79 s of 71 s, 0.406 of its timeout. Times (1 + m) it is 44.29 s, still under the timeout. That is why R5 selected no follow-up point and no 5-repetition max exists.
- `derive-runtime` over every record folder moves only `runtime.json`'s `sources` and its header count (315 to 355). No derived value moves, so L22's container sizing is untouched.
- Commit `4a2b536`; `make verify` passed in the hook.

## Task 2: every gate green on the final head, and `make check`

Final head for the plan's Task 2: `4a2b536550ac573e790021da95e8c87fb83a2911`. Branch current with `main`: 0 behind, 177 ahead.

| run | workflow | head | job | conclusion |
| --- | --- | --- | --- | --- |
| 41162982868 | ci.yml (`pull_request`) | 4a2b536 | test (3.12) | success, 1328 s |
| | | | vendor-bundle | success, 8 s |
| | | | image | success, 144 s |
| | | | bounds (1) | success, 700 s |
| | | | bounds (2) | success, 701 s |
| | | | bounds (3) | success, 545 s |
| | | | bounds (4) | success, 268 s |
| 41162982938 | operability: full (`pull_request`) | 4a2b536 | 40 measure, plan, followup-plan, verdict | success (followup skipped) |

- `gh pr checks 26`, the plan's verify filter: `0`, so every check on the head is green or skipped.
- `make pr.land` has no dry-run mode, so it was not run. Its two read-only functions were called directly for 4a2b536:
  - `check_head(sha, _real_runner, required_jobs())` returned `[]`;
  - `check_full_tier(26, sha, _real_runner)` returned `[]`.
  
  Neither merges anything. `land` was not called.
- `make check` (Docker 29.4.0) exited 0:
  - `4790 passed in 204.59s`;
  - `smoke: kernel, exports, ASGI stack and validation all live`;
  - the vendored bundle rebuilt byte-identical (`git diff --exit-code -- src/screw/static/vendor` clean).
- **Draft PR for the ship step: #26.** It is still a draft, unmerged, and branch protection was not touched.

## Runs

| run | what | head | result |
| --- | --- | --- | --- |
| 41161227084 | CI | 95a99da | success |
| 41161227951 | operability `full`, `pull_request` (recorded) | 95a99da | success, 1056 of 1056 ok, verdict passed, follow-up skipped |
| 41162982868 | CI | 4a2b536 | success, 7 of 7 jobs |
| 41162982938 | operability `full`, `pull_request` | 4a2b536 | success, verdict passed, follow-up skipped |

The commit that adds this SUMMARY moves the head again, and the PR's diff still touches `FULL_TIER_PATHS`. The push therefore starts one more CI run and one more full run. Recording them here would move the head yet again, so this file stops at 4a2b536. The executor reports that head's run ids and conclusions in its return message.

## Requirements

- **OPER-01, ticked.** L24 cites the timeouts' runs, and `runtime.json` is derived from the committed records. The full tier reads every catalogue row, the integer-L/P rows included, inside its timeout on the head: the largest cold wall is 0.406 of its timeout. Builds run in worker processes, and `make check`'s smoke passes in the image.
- **OPER-02, ticked.** L23 measures the memory ceiling, the gzip level, the worker count and the cache budgets on the runner. No derived value moved in this plan.
- **OPER-03, not ticked: held for the owner.** Every configuration the tiers read builds inside its timeout, both tiers are green and the CI job exists. But `docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md` (must, before the first release) records parts the model admits that the kernel refuses with a build error. One is the ordinary bolt d 3, pitch 0.35, 25 mm of thread, right hand. Such a part is never served wrong (L02 holds), but it is not "capped and warned or refused with a 422" either. The requirement does not hold as written, so it was not ticked. The question goes to the owner in the executor's return message.

## Deviations from Plan

**1. [Wording] Commit subject.** The plan's subject was "record the first full operability tier run". 07-19 had already recorded the first one (41155746591, a tracer dispatch), so the commit says "record the full operability tier run on the phase head, 41161227951".

**2. [Scope] runtime.json in the record commit.** The same rule as 07-19's deviation 4: `tests/test_runtime_bounds.py` derives runtime.json from every record folder, so the record commit regenerates it. Only `sources` and the header count moved.

**3. [Check] pr.land's read-only half was run instead of `make pr.land`.** Orchestrator note 2 forbids a merging mode, and `scripts/pr_land.py` has no dry-run flag. `check_head` and `check_full_tier` are the read-only checks `land` runs before it merges.

None of the under-prediction path's files changed: fit.json, `calc/cost.py`, the boundary file, full.json and L21.

## Not met on the runner

- **R5's follow-up on 5 instances:** still never exercised on the runner. No point of runs 41161227951 or 41162982938 reaches its timeout after the margin, so `followup` was skipped both times. The plan's truth on within-margin rows holds vacuously.
  - The debt item `docs/tech_debt/active/2026-10-31-full-tier-follow-up-job-never-run-on-the-runner.md` and WINDOWS #1 stay open, unchanged.
- **No expected refusal:** the full set still holds no `expect: refused` point (07-19).

## Debt Changes

None filed, resolved or edited. The in-wall residual (must) and the follow-up item (nice) stay active.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: bench/results/phase-07/full-41161227951/ (40 folders), `### full, run 41161227951` in bench/RESULTS.md
- FOUND: 4a2b536 is an ancestor of HEAD
- `gh run view 41161227951 --json conclusion` reports `success`
