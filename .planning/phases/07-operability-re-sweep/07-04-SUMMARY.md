---
phase: 07-operability-re-sweep
plan: 04
subsystem: testing
tags: [pre-registration, codex-review, pr-land, github-actions, merge]

requires:
  - phase: 07-operability-re-sweep
    provides: "07-03: PR A (#22), the sweep protocol R1 to R30, the point sets and probes"
provides:
  - "PR A squash-merged into main as 9dea01e66f857ef6c37524f2907891ddd0bd7196 before any runner reading"
  - "gsd/phase-07-operability-re-sweep carries origin/main (merge commit 80d70d7) and is on origin"
  - "the operability workflow is active, so workflow_dispatch can start it (not dispatched here)"
affects: [07-05, 07-06, operability, ci]

actuals:
  tokens: 21253   # chars/4 over the added lines of 40f667d..bfb4064 (the review-finding commits on PR A)
  tasks: 2
  commits: 25     # 23 review-finding commits on gsd/phase-07-preregistration (40f667d..bfb4064, squashed into 9dea01e) + cd02386 state + 80d70d7 merge on the phase branch; the summary and tracking commits come after this count
plan_head_before: 40f667d843d9c83a0111890f95b0bfbdf4d0f2b3   # PR A head when the plan began; no per-plan ledger was written for 07-04
plan_head_after: bfb40641780b11a480ebc57bba3f3f29f4504f65    # PR A head that landed; the phase branch then merged 9dea01e at 80d70d7ec4f3e971f0a081dc437001bd05c4f55b

tech-stack:
  added: []
  patterns:
    - "an author never reviews: Codex reviewed, Claude applied, the owner ruled on every rule-changing finding"

key-files:
  created: []
  modified:
    - bench/oper.py
    - bench/oper_child.py
    - bench/oper_sets.py
    - bench/oper_lift.py
    - .planning/phases/07-operability-re-sweep/07-SWEEP-PROTOCOL.md

key-decisions:
  - "Rules R1 to R30 froze at the squash merge 9dea01e; every later reading is newer than the protocol (R30)"
  - "Owner rulings on Codex round 3: R23 drift measured in a separate run with allowance 0.10 x the smallest build-1 peak and no drift term in mem_limit; preview and STEP edge points ranked by build seconds; each artifact takes its next-best edge point when another took its own; a non-ok tier point is charged its full timeout"

requirements-completed: [OPER-01, OPER-02]

duration: multi-session (Codex review loop with the owner between rounds)
completed: 2026-10-27
status: complete
---

# Phase 7 Plan 04: Land the pre-registration Summary

**PR A (#22) went through four Codex review rounds, landed on main as squash 9dea01e with green required jobs, and the phase branch now carries it, passes `make verify` and is on origin with the operability workflow active.**

## Performance

- **Tasks:** 2 (Task 1 was the owner's Codex review; Task 2 applied the findings and landed the PR)
- **Completed:** 2026-10-27
- **Files modified by findings:** 8 files, +2225 / -149 lines (`git diff --shortstat 40f667d bfb4064`)

## Accomplishments

- Task 1: reviewer was Codex, not the CLI that wrote the diff, over four rounds. Counts are the finding bullets in each review file.
  - Round 1: 8 findings (R9/R10 floors on non-ok readings, circular contention selection, unspecified load mix, confirmation probes unreachable past the validators, diameter ceiling awarded beyond the tested d, no nut clearance reading, carried macOS and spur figures, a non-text `status` raising `TypeError`).
  - Round 2: 8 earlier findings re-checked (7 resolved, #3 partly) plus 7 new ones (lifted readings losing identity in summaries, gzip memory missed by the cap test, contention slot selection, fitting on non-ok repetitions, nut diameter probes, worker memory drift, R7 on unsuccessful readings).
  - Round 3: 4 choices needing owner rulings (R23 drift measurement, preview and STEP edge ranking, shared edge allocation, unsuccessful-reading accounting) plus 2 new findings (tested turn value on walk-down, incomplete or duplicated repetitions receiving numeric summaries); the rest were confirmations. One nice-level provenance check found no mismatch.
  - Round 4: `no findings`.
- Task 2 step 1: the findings became 23 commits on `gsd/phase-07-preregistration` (40f667d..bfb4064). The owner ruled A (the other items were applied as proposed) and, on round 3: a separate drift run for R23 with an allowance of 0.10 x the smallest build-1 peak and no drift term in `mem_limit`; preview and STEP edges ranked by build seconds; each artifact takes its next-best edge point when another took its own; a non-ok tier point is charged its full timeout. Rule-changing findings were put to the owner and not applied silently.
- Task 2 step 2: CI on PR head bfb40641780b11a480ebc57bba3f3f29f4504f65 was green: `test (3.12)` pass in 14m25s, `vendor-bundle` pass, `image` pass.
- Task 2 step 3: `make pr.land PR=22` refused the first time (see Issues). After the state.json commit it merged. `gh pr view 22 --json state --jq .state` reads `MERGED`; the squash commit is `9dea01e66f857ef6c37524f2907891ddd0bd7196` and `git log --oneline origin/main -1` is `9dea01e feat(bench): operability harness and pre-registered sweep protocol (phase 7, PR A) (#22)`.
- Step 4: after `git switch gsd/phase-07-operability-re-sweep` and `git fetch origin`, `git merge --no-edit origin/main` made merge commit `80d70d7ec4f3e971f0a081dc437001bd05c4f55b` with no conflict. The phase branch was pushed with a plain `git push -u` (new branch on origin, head 80d70d7).
- Step 5: `gh workflow list --all | grep -i operability` prints `operability	active	398167702`. Nothing was dispatched.

## Task Commits

1. **Task 1: Codex reviews PR A** - no commit (owner action; reviews kept outside the repo)
2. **Task 2: apply findings, land PR A, merge and push the phase branch** - review-finding commits 40f667d..bfb4064 on the PR branch (squashed into `9dea01e`), `cd02386` (state.json), `80d70d7` (merge of origin/main)

**Plan metadata:** the SUMMARY commit and the STATE and ROADMAP commit follow this file.

## Files Created/Modified

- `bench/oper.py`, `bench/oper_child.py`, `bench/oper_sets.py`, `bench/oper_lift.py` - harness fixes from the findings (status type check, lift identity in summaries, peak read after the gzip, repetition identity check, nut clearance and diameter probes)
- `.planning/phases/07-operability-re-sweep/07-SWEEP-PROTOCOL.md` - rules revised under the owner's rulings, then frozen by the merge
- `.planning/state.json` - gsd progress fields only, committed as `cd02386`

## Decisions Made

See key-decisions. The rulings changed rules R23 and R27 and the load and boundary point sets before the freeze; none is open.

## Deviations from Plan

None in code. One procedural event, recorded under Issues, was handled by the owner's ruling.

## Issues Encountered

- **`make pr.land PR=22` refused before merging** with `pr.land: the working tree has uncommitted changes.` and `nothing was merged.` Cause: the tracked `.planning/state.json` had been modified by gsd tooling (progress 82% to 83%, `updated_at`). The owner chose option A: commit only that file. Done as `cd02386 docs(07-04): record gsd state progress` (`git add .planning/state.json` and nothing else), then `make pr.land PR=22` merged.
- **Follow-up outcome:** `pr.land` switched the checkout to `main` and pulled it (fast-forward to 9dea01e), then exited 1 on `git branch -D gsd/phase-07-preregistration failed: error: cannot delete branch 'gsd/phase-07-preregistration' used by worktree at '/Users/half/git/halfb00t/screw/.claude/worktrees/phase-07-preregistration'`. This was the expected refusal from the plan. It was reported and not repaired; the merge itself had completed.
- **Reflog check:** `git reflog -n 30` in the main checkout lists `rebase` entries, all of them old (`HEAD@{24}` and earlier) and from the earlier phase 06.1 branch rebase, not from this plan. This plan ran no reset, rebase, force push or deletion, and none touched `main`.
- **No per-plan commit ledger** (`gsd-plan-head-before-07-04`) exists, because the plan's code commits live in the PR worktree and the plan began mid-flight. `actuals.commits` is counted with `git rev-list --count 40f667d..bfb4064` (23) plus the two phase-branch commits.

## Verification

- `make verify` on the phase branch after the merge: `======================= 4036 passed in 177.37s (0:02:57) =======================`, coverage `Required test coverage of 96.0% reached. Total coverage: 97.69%`.
- Plan verify 1: `gh pr view 22 --json state --jq .state` prints `MERGED` (PR 22 is the one `gh pr list --state merged --head gsd/phase-07-preregistration` returns).
- Plan verify 2: `git merge-base --is-ancestor origin/main HEAD`, branch name, `.github/workflows/operability.yml`, `07-SWEEP-PROTOCOL.md` and `git ls-remote --exit-code --heads origin gsd/phase-07-operability-re-sweep` all passed; the last printed `80d70d7ec4f3e971f0a081dc437001bd05c4f55b	refs/heads/gsd/phase-07-operability-re-sweep`.
- Plan verify 3: `make verify` exit 0 (above).
- Acceptance: origin/main tip is the PR A squash commit; the reflog shows no reset or rebase of main; `operability` is listed active; this SUMMARY records the merged sha, the follow-up outcome and the owner follow-ups.

## Owner follow-ups

Not done by this plan, by instruction:

- `git worktree remove .claude/worktrees/phase-07-preregistration`
- `git branch -d gsd/phase-07-preregistration` (use `-D` only if git says it is not merged, since the squash changes the tip; this is the owner's call)

## Known Stubs

None. This plan wrote no source files.

## Threat Flags

None. No new network endpoint, auth path or trust boundary appeared; the workflow keeps dispatch-only, `contents: read` and no secret, as Codex confirmed.

## Next Phase Readiness

The workflow is active on main and the phase branch is on origin, so plan 07-05 can dispatch `operability` with `--ref gsd/phase-07-operability-re-sweep`. The rules are frozen by the merge and older than every figure.

## Self-Check: PASSED

9dea01e, 80d70d7 and cd02386 are ancestors of the phase branch. bfb4064 is the PR A head and is an ancestor of gsd/phase-07-preregistration, not of the phase branch: the squash merge replaced it with 9dea01e.
