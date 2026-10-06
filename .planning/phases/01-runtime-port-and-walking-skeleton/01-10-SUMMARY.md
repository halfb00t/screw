---
phase: 01-runtime-port-and-walking-skeleton
plan: 10
subsystem: infra
tags: [github-ruleset, branch-protection, pr-land, ci-required-jobs]

requires:
  - phase: 01-runtime-port-and-walking-skeleton
    provides: required-jobs.txt, make pr.land, ci.yml jobs test (3.12), vendor-bundle, image (plans 01-06, 01-07), and the merged Phase 1 PR
provides:
  - main is walled by ruleset default (id 24563199), read back equal to required-jobs.txt with strict policy and no bypass actors
  - squash merge commits carry PR_TITLE and PR_BODY
  - HOW_TO_DEVELOP section 9 records the ruleset id with its PUT-by-id, read-back and delete commands
  - the wall's first use, PR #2, landed through make pr.land as squash e69d351
affects: [every later phase PR, required-jobs.txt changes, ci.yml job renames]

actuals:
  tokens: 1247    # chars/4 over the realized diff (4988 chars of docs/HOW_TO_DEVELOP.md)
  tasks: 2
  commits: 1      # MEASURED: git rev-list --count f1ec232..e69d351 on main; the branch commit 2be2fe7 was squashed into e69d351
plan_head_before: f1ec232e7c72c0bea48f752262183f05a26da6e7
plan_head_after: e69d35199fd53375f834f94d92a9717d01b11bbf

tech-stack:
  added: []
  patterns:
    - "Repository settings are recorded in HOW_TO_DEVELOP with the command that reproduces and changes them, since they do not live in git"
    - "The required-checks rule is replaced whole by a PUT by id; every other rule is carried over from the live ruleset"

key-files:
  created: []
  modified:
    - docs/HOW_TO_DEVELOP.md

key-decisions:
  - "Ruleset POST body copied from spur was accepted by GitHub unchanged, so no corrected body is recorded"
  - "allowed_merge_methods stays merge, squash, rebase as section 9 specified; narrowing it to squash is an owner choice and was not made (PR #1 landed as a merge commit)"

requirements-completed: [INFR-01]

coverage:
  - id: D1
    description: "Ruleset default on main read back equal to required-jobs.txt: contexts equal, strict policy true, deletion + non_fast_forward + pull_request rules present, bypass_actors empty, every integration_id 15368"
    requirement: INFR-01
    verification:
      - kind: other
        ref: "gh api repos/halfb00t/screw/rules/branches/main and rulesets/24563199, python comparison against .github/workflows/required-jobs.txt (output in Read-back evidence below)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Squash merge setting is PR_TITLE and PR_BODY"
    requirement: INFR-01
    verification:
      - kind: other
        ref: "gh api repos/halfb00t/screw --jq '[.squash_merge_commit_title, .squash_merge_commit_message]' prints [\"PR_TITLE\",\"PR_BODY\"]"
        status: pass
    human_judgment: false
  - id: D3
    description: "The ruleset id and PUT-by-id command reached main through make pr.land"
    requirement: INFR-01
    verification:
      - kind: other
        ref: "git show origin/main:docs/HOW_TO_DEVELOP.md | grep 'rulesets/24563199' (2 matches); PR #2 state MERGED, mergeCommit e69d351"
        status: pass
    human_judgment: false

duration: "~20 min active (excludes the wait at the owner checkpoint; the start time was not captured across it)"
completed: 2026-10-06
status: complete
---

# Phase 1 Plan 10: Wall main Summary

**main is walled by ruleset `default` (id 24563199): the three CI jobs of required-jobs.txt green on a current head, a PR for every change, no deletion, no force push, no bypass actors. The record of it reached main through `make pr.land` as PR #2, the wall's first use.**

## Performance

- **Duration:** ~20 min active (the owner checkpoint wait excluded)
- **Completed:** 2026-10-06
- **Tasks:** 2 (Task 1 a blocking-human checkpoint resolved by the orchestrator on the owner's delegation, Task 2 auto)
- **Files modified:** 1 (`docs/HOW_TO_DEVELOP.md`)

## Accomplishments

- Task 1: before presenting the checkpoint, confirmed the precondition (merged PR query printed `1`), pulled main (`f1ec232`), and confirmed main's latest `ci.yml` run 37426271212 concluded success with jobs `image`, `vendor-bundle`, `test (3.12)`. At that point the repo had 0 rulesets and squash settings `COMMIT_OR_PR_TITLE` / `COMMIT_MESSAGES`. The PATCH and POST were not run by the executor (D-11); the orchestrator ran them on the owner's delegation on 2026-10-06.
- Task 2: read the wall back independently (the orchestrator's paste was not trusted), recorded id 24563199 and the PUT-by-id, read-back and delete commands in section 9, and landed that record as PR #2 through `make pr.land`.

## Read-back evidence

Python comparison of `gh api repos/halfb00t/screw/rules/branches/main` and `gh api repos/halfb00t/screw/rulesets/24563199` against `.github/workflows/required-jobs.txt`, run by the executor before the PR was opened (exit 0):

```
contexts==required-jobs: True ['image', 'test (3.12)', 'vendor-bundle']
strict: True
types: ['deletion', 'non_fast_forward', 'pull_request', 'required_status_checks'] needed present: True
bypass_actors: [] empty: True
ruleset name/id/enforcement/target: default 24563199 active branch
integration_ids: {15368}
```

```
$ gh api repos/halfb00t/screw --jq '[.squash_merge_commit_title, .squash_merge_commit_message]'
["PR_TITLE","PR_BODY"]
$ gh api repos/halfb00t/screw --jq .squash_merge_commit_title
PR_TITLE
```

Plan `<verify>` (automated 1) re-run after the landing, from main:

```
ruleset=image,test (3.12),vendor-bundle jobs=image,test (3.12),vendor-bundle
EQUAL
```

Plan `<verify>` (automated 2): `git fetch origin main && git show origin/main:docs/HOW_TO_DEVELOP.md | grep 'rulesets/[0-9]'` succeeded; `rulesets/24563199` appears twice and `gh api -X PUT repos/halfb00t/screw/rulesets/24563199` is present.

## make pr.land output (verbatim)

First attempt, with the orchestrator's two modified planning files in the tree. Nothing was merged; no stash or other route was used:

```
.venv/bin/python -m scripts.pr_land 2
pr.land: the working tree has uncommitted changes.
pr.land: nothing was merged.
make: *** [Makefile:213: pr.land] Error 1
```

Second attempt, after the orchestrator cleaned the tree (exit 0):

```
.venv/bin/python -m scripts.pr_land 2
https://github.com/halfb00t/screw/actions/runs/37428477672
```

PR #2: checks `test (3.12)` 1m37s, `vendor-bundle` 8s, `image` 1m54s, all pass on head `2be2fe7`. State MERGED at 2026-10-06T07:14:52Z, squash commit `e69d35199fd53375f834f94d92a9717d01b11bbf` on main (`docs(01-10): record the main ruleset id and its update commands (#2)`). After landing, `pr.land` removed the local branch `docs/record-main-ruleset`; `origin/docs/record-main-ruleset` still exists on the remote.

## Task Commits

1. **Task 1: Owner puts up the main ruleset** - no commit (a repository setting outside git; applied by the orchestrator on the owner's delegation)
2. **Task 2: Read the wall back, record its id, land through make pr.land** - `2be2fe7` on the PR branch, landed as squash `e69d351` on main (docs)

**Plan metadata:** the commit on `docs/phase-01-close` that carries this SUMMARY, STATE.md, ROADMAP.md, REQUIREMENTS.md and `.planning/state.json`. It lands with the verification artifacts as one PR.

## Files Created/Modified

- `docs/HOW_TO_DEVELOP.md` - section 9 heading "The wall (applied once, after the Phase 1 merge)": ruleset `default` id 24563199 applied 2026-10-06, the squash-message PATCH kept, the one-time POST replaced by the apply-by-id PUT, the read-back and the delete command, and the note that required-jobs.txt and the ruleset change together.

## Decisions Made

- The POST body was accepted unchanged, so section 9 keeps no corrected body. It names the four rules and `bypass_actors: []` that GitHub accepted.
- The two moved text blocks leave `allowed_merge_methods` as `merge, squash, rebase`, exactly as section 9 specified. PR #1 landed as a merge commit and the owner accepted that. The owner may narrow the list to squash; the executor did not.

## Deviations from Plan

### Plan truth that did not hold as written

**1. Phase 1 merged as a merge commit, not one squash commit**
- **Found during:** Task 1 precondition review
- **Issue:** the first must_have says plans 01-01..01-09 merged "as one squash commit with `gh pr merge N --squash --delete-branch`". PR #1 landed as merge commit `4951d47` carrying 51 commits.
- **Impact:** the precondition (a merged PR exists for the phase branch) still holds. The owner accepted the shape on 2026-10-06 and it is recorded in STATE.md; not re-litigated here. The squash message setting applies from PR #2 onward.
- **Files modified:** none.

### Executed differently from the plan

**2. [Rule 3 - Blocker] make pr.land refused on a dirty tree**
- **Found during:** Task 2, landing step
- **Issue:** the orchestrator's uncommitted `.planning/STATE.md` and `.planning/state.json` made `pr.land` refuse (output above). The plan has no step for this.
- **Fix:** stopped and reported the exact message. The orchestrator stashed its own edits (its stash, never touched by the executor) and the retry landed the PR. No other merge route was used.
- **Files modified:** none by the executor.
- **Verification:** second `make pr.land PR=2` exit 0; `git status --short` empty before it.

**3. Task 1 was applied by the orchestrator, not by the owner at a terminal**
- **Found during:** Task 1
- **Issue:** the plan has the owner run the PATCH and POST (D-11).
- **Fix:** the owner delegated the three section 9 commands to the orchestrator, which ran them in order and passed the results back. The executor re-ran the read-back itself for the evidence above.

---

**Total deviations:** 3 (1 plan truth that did not hold, 1 Rule 3 blocker, 1 delegation of the owner action)
**Impact on plan:** none on the outcome. The wall matches required-jobs.txt and the record reached main through `make pr.land`.

## Issues Encountered

- The dirty-tree refusal above. Cause: orchestrator state edits made before the plan's landing step, not a defect in `pr.land`; its refusal is the designed behavior.
- The commit trailer on `2be2fe7` is `Co-Authored-By: Claude Sonnet 5.5` where the orchestrator's brief named `Claude Fable 5.1`. The harness attribution names the executing model; the orchestrator said to keep it and not amend.

## Threat Flags

None. The wall adds no new endpoint, auth path or schema; the read-back confirms the mitigations the plan's threat model required:

- T-01-33: ruleset requires the three CI jobs on a current head (strict policy true), a pull request for every change, and carries deletion and non_fast_forward rules.
- T-01-34: `bypass_actors` is `[]`.
- T-01-35: sorted contexts equal sorted required-jobs.txt lines; the drift test in `tests/test_pr_land.py` keeps required-jobs.txt equal to ci.yml.

## Known Stubs

None. This plan changes one documentation file and no code.

## User Setup Required

None - no external service configuration required. The repository setting was applied during Task 1.

## Next Phase Readiness

Plan 01-10 is the last plan of Phase 1. The orchestrator adds the verification artifacts to `docs/phase-01-close` and lands them as one PR through `make pr.land`, the second use of the wall. Phase 2 then plans from the walled `main`. Two things carry forward from this plan:

- Any change to `.github/workflows/required-jobs.txt` needs the PUT-by-id command in HOW_TO_DEVELOP section 9 run in the same change; until it is, the wall and `make pr.land` require different lists.
- `origin/docs/record-main-ruleset` is a leftover remote branch from PR #2.

## Self-Check: PASSED

- FOUND: `docs/HOW_TO_DEVELOP.md` containing `rulesets/24563199` on `origin/main`.
- FOUND: `e69d351` is an ancestor of `docs/phase-01-close` HEAD (`git merge-base --is-ancestor`, verified at commit time).
- FOUND: PR #2 state MERGED; ruleset read-back equal to required-jobs.txt, re-run after the landing.
