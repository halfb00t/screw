---
phase: 01-runtime-port-and-walking-skeleton
plan: 07
subsystem: infra
tags: [pre-commit, commit-msg, github-actions, pr-land, ruleset, skip-token]

requires:
  - phase: 01-runtime-port-and-walking-skeleton
    provides: "the vendor-bundle (01-04) and image (01-06) CI jobs the required-jobs list names, the runtime-closure requirements.txt (01-06) that L08 narrows L06 for"
provides:
  - "scripts/skip_tokens.py and the no-skip-token commit-msg hook: a commit message carrying any GitHub Actions skip token is refused (active on this clone)"
  - "scripts/pr_land.py and make pr.land PR=<n>: squash-merges only a head that is green on every required job and current with main"
  - ".github/workflows/required-jobs.txt (test (3.12), vendor-bundle, image) with a drift test against ci.yml; the test job now has a one-entry python matrix"
  - "L08 in the decision log; the wall idea closed; HOW_TO_DEVELOP §0, §7, §9 describe pr.land, the ship-note workaround and the one-time ruleset commands"
affects: [01-08, 01-10 (owner applies the ruleset and records its id), every later phase (lands through make pr.land)]

actuals:
  tokens: 24500
  tasks: 2
  commits: 1
plan_head_before: 14c913f42fe8a7a1a2d4061f31a5cfe46dc9355f
plan_head_after: cff08fa21b160fd0b388e1cc5fd8a1b21001e235

tech-stack:
  added: []
  patterns:
    - "required-jobs.txt and ci.yml change in one commit; tests/test_pr_land.py derives GitHub's effective job names from ci.yml and fails on drift"
    - "scripts/ is typed and tested like the package (make typecheck covers it) but is not part of the wheel"
    - "the verify hook is pinned to stages [pre-commit] so it runs once per commit alongside the commit-msg hook"

key-files:
  created:
    - scripts/__init__.py
    - scripts/pr_land.py
    - scripts/skip_tokens.py
    - tests/test_pr_land.py
    - tests/test_skip_tokens.py
    - .github/workflows/required-jobs.txt
  modified:
    - .pre-commit-config.yaml
    - .github/workflows/ci.yml
    - Makefile
    - docs/architecture/decision_log.md
    - docs/ideas/2026-10-05-wall-main-like-spur.md
    - docs/ideas/INDEX.md
    - docs/HOW_TO_DEVELOP.md
    - docs/CODING_VALUES.md

key-decisions:
  - "L08: main is walled by required CI jobs on a current head, a commit-msg hook against skip tokens and make pr.land, ported from spur L22 and L25"
  - "The GitHub ruleset is applied by the owner after the Phase 1 merge (its required jobs do not exist on main before then); Phase 1 itself lands pre-wall with gh pr merge --squash --delete-branch"
  - "requirements.txt pins the runtime closure only, which narrows L06: a ruff or mypy release can now turn the gate red on its own; no second pin file"

patterns-established:
  - "Port spur's tooling byte for byte (cmp against ../spur) and change only prose that names spur"

requirements-completed: [INFR-01]

coverage:
  - id: D1
    description: "scripts/pr_land.py and scripts/skip_tokens.py are spur's, with their 85 tests passing in make verify"
    requirement: INFR-01
    verification:
      - kind: unit
        ref: "tests/test_pr_land.py, tests/test_skip_tokens.py (85 passed); cmp against ../spur exits 0 for both scripts"
        status: pass
    human_judgment: false
  - id: D2
    description: "required-jobs.txt lists exactly test (3.12), vendor-bundle, image and equals ci.yml's effective job names"
    requirement: INFR-01
    verification:
      - kind: unit
        ref: "tests/test_pr_land.py#test_required_jobs_file_matches_ci_yml_job_names"
        status: pass
    human_judgment: false
  - id: D3
    description: "the commit-msg hook is installed on this clone and refuses a message with a skip token, both through pre-commit run and through a real commit attempt"
    requirement: INFR-01
    verification:
      - kind: other
        ref: "pre-commit run no-skip-token --hook-stage commit-msg (exit 1 on the token message, exit 0 on the clean one); git commit refused with exit 1, HEAD unchanged"
        status: pass
    human_judgment: false
  - id: D4
    description: "make verify is green with scripts/ type-checked and the new tests collected"
    requirement: INFR-01
    verification:
      - kind: integration
        ref: "make verify: ruff clean, mypy 26 source files clean, Contracts 6 kept 0 broken, 260 passed"
        status: pass
    human_judgment: false
  - id: D5
    description: "L08, the closed idea and HOW_TO_DEVELOP §9 give the owner the exact ruleset commands"
    requirement: INFR-01
    verification: []
    human_judgment: true
    rationale: "The POST body is copied from spur's live ruleset and has not been run against screw (RESEARCH A3); only plan 01-10's read-back can confirm GitHub accepts it"

duration: 13min
completed: 2026-10-06
status: complete
---

# Phase 1 Plan 07: Wall main Summary

**spur's skip-token commit-msg hook and `make pr.land` ported byte for byte, a required-jobs list tied to ci.yml by a drift test, and L08 with the owner's one-time ruleset commands**

## Performance

- **Duration:** about 13 min
- **Started:** 2026-10-06T05:25:00Z
- **Completed:** 2026-10-06T05:38:00Z
- **Tasks:** 2 (task 1 is one commit by design, D-11; task 2 changes no tracked file)
- **Files modified:** 14 in the task commit

## Accomplishments

- `scripts/pr_land.py`, `scripts/skip_tokens.py` and their tests copied from spur; `cmp` against `../spur` exits 0 for both scripts. Only `scripts/__init__.py`'s docstring changed (wheel `screw`, path `src/screw`, no `bench`).
- `.pre-commit-config.yaml` has `default_install_hook_types: [pre-commit, commit-msg]`, the `verify` hook pinned to `stages: [pre-commit]` and the `no-skip-token` hook.
- `ci.yml`'s `test` job has a one-entry `python: ["3.12"]` matrix, so GitHub reports it as `test (3.12)`; `required-jobs.txt` names `test (3.12)`, `vendor-bundle`, `image`, and the drift test finds the matrix.
- `Makefile`: `pr.land` target; `typecheck` covers `scripts`.
- L08 written (inserted before L09), the wall idea marked done and its INDEX row moved to a `## Done` table, `HOW_TO_DEVELOP.md` §0, §7, §9 and `CODING_VALUES.md` "Dependencies" updated.
- The commit-msg hook is active on this clone and was seen to refuse a skip token.

## Task Commits

1. **Task 1: Wall main** - `cff08fa` (feat)
2. **Task 2: Activate the commit-msg hook and prove it refuses** - no commit; `.git/hooks/commit-msg` is untracked by git. HEAD stayed `cff08fa` through the proof.

**Plan metadata:** the docs commit that carries this SUMMARY, STATE.md, ROADMAP.md and REQUIREMENTS.md.

## Skip-token proof (task 2)

`.venv/bin/pre-commit install` printed `pre-commit installed at .git/hooks/pre-commit` and `pre-commit installed at .git/hooks/commit-msg`; `test -x .git/hooks/commit-msg` succeeds.

`pre-commit run no-skip-token --hook-stage commit-msg --commit-msg-filename <file>` on the message `chore: hook proof` plus a bracketed skip-ci token (exit 1):

```
reject GitHub Actions skip tokens in the commit message.......................Failed
- hook id: no-skip-token
- exit code: 1

make: this commit message carries a GitHub Actions skip token:
      line 1: '[skip ci]'
      A skip token here silences CI on this commit, and on a PR head it
      leaves the PR with zero checks.
      Describe it in words instead ("a GitHub Actions skip token") -- do not
      write the literal token.
      If a named line is in the diff `git commit -v` appends below the cut line, commit without -v -- this hook reads the whole message either way.
      See docs/tech_debt/resolved/2026-09-25-ship-note-skip-token-leaks-into-squash-merge.md.
```

The same command on the clean message `chore: hook proof`:

```
reject GitHub Actions skip tokens in the commit message.......................Passed
```

A real commit attempt, as the orchestrator asked, on a throwaway staged file `scratch-hook-proof.txt` with the same token-carrying subject: the pre-commit `verify` hook passed, then `no-skip-token` failed with the same refusal text as above, `git commit` exited 1 and `git log -1 --format=%H` was `cff08fa21b160fd0b388e1cc5fd8a1b21001e235` before and after. The scratch file was then unstaged (`git rm --cached`) and deleted. Afterwards `git status --short` showed only the orchestrator's three planning files:

```
 M .planning/config.json
?? .planning/milestone.lock
?? .planning/state.json
```

Task 2's own verify command (`test -x .git/hooks/commit-msg && ... ! python -m scripts.skip_tokens <token file>`) also passes.

## Files Created/Modified

- `scripts/__init__.py`, `scripts/pr_land.py`, `scripts/skip_tokens.py` - the landing tool and the hook entry point, spur's
- `tests/test_pr_land.py`, `tests/test_skip_tokens.py` - their tests, including the required-jobs drift test
- `.github/workflows/required-jobs.txt` - the three jobs `make pr.land` and the ruleset require
- `.github/workflows/ci.yml` - `test` job matrix, comment tying the jobs to the list
- `.pre-commit-config.yaml` - both hook types, `verify` pinned, `no-skip-token`
- `Makefile` - `pr.land`, `typecheck` over `scripts`
- `docs/architecture/decision_log.md` - L08
- `docs/ideas/2026-10-05-wall-main-like-spur.md`, `docs/ideas/INDEX.md` - the idea closed
- `docs/HOW_TO_DEVELOP.md`, `docs/CODING_VALUES.md` - pr.land, hook, ship-note workaround, one-time ruleset commands, requirements.txt as runtime closure

## Decisions Made

- L08 as above. The ruleset POST body in HOW_TO_DEVELOP §9 is RESEARCH's draft, copied from spur's live ruleset and not run against screw (flagged assumption A3); plan 01-10 reads the wall back and corrects the doc.
- The Open table in `docs/ideas/INDEX.md` is kept with a `none open` placeholder row rather than removed, so the next idea has a table to join.

## Deviations from Plan

None - plan executed exactly as written.

One observation, not a deviation: the refusal text printed by spur's `scripts/skip_tokens.py` ends with a pointer to `docs/tech_debt/resolved/2026-09-25-ship-note-skip-token-leaks-into-squash-merge.md`, a spur file that does not exist in screw. The plan's acceptance criterion requires `cmp` equality with spur's script, so it was left as is. No tech-debt item filed; if the owner wants the pointer retargeted it is a one-line change that breaks the byte-for-byte port.

## Issues Encountered

None. `make verify` ran three times (before the commit, for the acceptance sweep, and inside the pre-commit hook), each green.

## Verification

- `.venv/bin/python -m pytest tests/test_pr_land.py tests/test_skip_tokens.py -q -p no:cacheprovider` - `85 passed`
- `make verify` - `All checks passed!`, `Success: no issues found in 26 source files`, `Contracts: 6 kept, 0 broken.`, `260 passed in 24.85s`
- All eleven task 1 acceptance greps and both `cmp` checks pass.

## User Setup Required

None for this plan. The owner applies the ruleset after the Phase 1 merge (plan 01-10), with the commands in `docs/HOW_TO_DEVELOP.md` §9. Every other clone re-runs `.venv/bin/pre-commit install` once.

## Next Phase Readiness

Ready for 01-08. Not done and not this plan's: the GitHub ruleset and the squash-message setting (plan 01-10, owner), and the `tests/test_pr_land.py` fixtures still name spur's repository by design.

## Self-Check: PASSED

- Files: all six created files exist on disk; `git merge-base --is-ancestor cff08fa HEAD` succeeds.
- Hook: `.git/hooks/commit-msg` is executable.

---
*Phase: 01-runtime-port-and-walking-skeleton*
*Completed: 2026-10-06*
