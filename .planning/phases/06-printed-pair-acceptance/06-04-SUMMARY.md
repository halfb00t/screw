---
phase: 06-printed-pair-acceptance
plan: 04
subsystem: testing
tags: [pre-registration, codex-review, pull-request, landing]

requires:
  - phase: 06-printed-pair-acceptance
    provides: PR A (#19) from plan 06-03 with the protocol, rule and matrix modules and the two blank records
provides:
  - Codex review of PR A, three findings, all verified and applied as commits on gsd/phase-06-preregistration
  - PR A landed on main as squash commit 16f7041 (state MERGED, main CI green)
  - the phase branch carrying origin/main by a merge commit, holding the landed protocol, rules and blank records byte for byte
affects: [06-05 run 1 export and print, 06-06 L17 and requirement evidence]

actuals:
  tokens: 3000
  tasks: 2
  commits: 2

key-files:
  created: []
  modified:
    - bench/print_rules.py (on the pre-registration branch, now on main)
    - tests/test_print_rules.py (same)
    - .planning/phases/06-printed-pair-acceptance/06-PRINT-PROTOCOL.md (same)

key-decisions:
  - "Finding 1 enforces R3 and changes no ruling: each clearance carries the one order R3 gives it (0.25 is 1, 0.05 is 5). A nut fitted out of turn is refused naming its line, never corrected. This replaces the weaker permutation-of-1-to-5 check, which it implies."
  - "load() folds both CRLF and a lone CR to LF after the digest check, exactly the universal-newline behaviour of read_text(), rather than CRLF only, so no line ending can pass one path and fail the other."
  - "The protocol's three export commands are now pinned by the number test: dropping an -o from any of them fails the test."

requirements-completed: []

coverage:
  - id: D1
    description: "A complete record fitted tightest first is refused naming its first line, so it cannot set a default"
    requirement: "PAIR-02"
    verification:
      - kind: unit
        ref: "tests/test_print_rules.py#test_a_record_fitted_tightest_first_is_refused_whatever_it_passed"
        status: pass
      - kind: unit
        ref: "tests/test_print_rules.py#test_an_incomplete_or_ambiguous_record_is_refused_naming_the_line[order-against-r3]"
        status: pass
    human_judgment: false
  - id: D2
    description: "A record saved with CRLF or CR line endings reads identically through load() and read_text()"
    requirement: "PAIR-02"
    verification:
      - kind: unit
        ref: "tests/test_print_rules.py#test_a_record_saved_with_other_line_endings_reads_the_same_by_both_paths"
        status: pass
    human_judgment: false
  - id: D3
    description: "The protocol's run-1, run-2 and acceptance export commands each carry the mandatory -o"
    requirement: "PAIR-02"
    verification:
      - kind: unit
        ref: "tests/test_print_rules.py#test_the_protocol_states_the_numbers_the_rules_read"
        status: pass
    human_judgment: false
  - id: D4
    description: "PR A is MERGED, origin/main carries its squash commit, and the phase branch holds the landed files byte for byte before any export or print"
    requirement: "INFO-04"
    verification:
      - kind: other
        ref: "gh pr view 19: MERGED 16f7041; git merge-base --is-ancestor origin/main HEAD; git diff --quiet origin/main HEAD -- bench/print_rules.py bench/print_matrix.py 06-PRINT-PROTOCOL.md"
        status: pass
    human_judgment: false

duration: 130min
completed: 2026-10-23
status: complete
plan_head_before: 448bd0e9c7cd5aa0b70337b3cb2cc047e3d01af9
plan_head_after: 1332178799d520d974fc66b7b482e5092ca2ef5e
---

# Phase 6 Plan 04: Codex review and landing of PR A Summary

**Codex reviewed PR A (#19), its three findings were reproduced and fixed with tests, and PR A is on main as `16f7041` with the phase branch merged up to it before any export or print.**

## Accomplishments

- Task 1 (checkpoint) answered by the owner: reviewer `codex`, run `codex exec` headless, read-only, codex-cli 0.163.0, on 2026-10-23. Findings, unedited from `codex-review-pr19.md`:

  > 1. **major** - bench/print_rules.py:176: R3 requires loosest-to-tightest testing, but validation accepts any permutation. A complete record tested in the opposite order is accepted and can set the permanent default; reproduced with an all-pass record returning `0.05`. Validate each clearance's prescribed order before deriving a default, and stop on deviations without rewriting observations.
  >
  > 2. **minor** - bench/print_rules.py:95: CRLF records behave differently through the two reading paths. Universal-newline `read_text()` accepts them, but `load()` preserves carriage returns and subsequent parsing rejects the header. Thus an owner's record can pass inspection and fail after pinning. Normalize CRLF after checking the raw-byte digest, and test both paths.
  >
  > 3. **minor** - 06-PRINT-PROTOCOL.md:60: The acceptance export command omits mandatory `-o`. Following it exits `2` with "the following arguments are required: -o/--output", producing no comparison files. Specify `-o bench/results/phase-06/stl/acceptance`.

- The owner chose "Fix all 3 + land" (AskUserQuestion, 2026-10-23), which authorised the squash-merge to main.
- All three findings were reproduced before fixing: an all-pass record written tightest first returned `0.05` from `default_from`; `python -m bench.print_matrix export acceptance` exited 2; the CRLF test failed on the unfixed `load()`. None was wrong, so none was declined. No fix touched a locked decision or ruling (finding 1 enforces R3).
- PR #19 landed: `make pr.land PR=19` squash-merged it, `gh pr view 19` reads `MERGED`, `origin/main` is `16f7041`, and local main fast-forwarded to it. The CI run on main for that commit finished `success` (test (3.12), vendor-bundle, image).
- The phase branch took `git merge --no-edit origin/main` (merge commit `1332178`, no conflict). `make verify` on it: `3510 passed in 152.53s (0:02:32)`, exit 0.

## Task Commits

1. **Task 1: Codex reviews PR A** - owner checkpoint, no commit.
2. **Task 2: apply the findings, land, merge**, three fix commits on `gsd/phase-06-preregistration` (squashed into `16f7041` on main) then the merge:
   - `dce3862` fix(06): refuse a record whose nuts were fitted out of R3's order (finding 1; test written first, red, then green; protocol states the order mapping)
   - `8c5d2d6` fix(06): fold CRLF in load() so both reading paths agree (finding 2; parametrised CRLF and CR test through both paths, red first)
   - `f418d08` docs(06): give the acceptance export command its mandatory -o (finding 3; number test extended to the three export commands, red first)
   - `16f7041` PR A squash commit on main; `1332178` merge of origin/main into the phase branch.

`commits: 2` in the frontmatter is the measured count on the phase branch since the ledger base (the squash commit and the merge). The three fix commits live on the PR branch and reach the phase branch inside the squash.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Lint line length in the new test**
- **Found during:** finding 3 (ruff E501 on the extended wanted list)
- **Fix:** wrapped the comment and the generator; the commit hook then passed.
- **Commit:** `f418d08`

**2. [Tool behaviour, no fix needed] `make pr.land` failed its last step after the merge**
- **Found during:** Task 2 step 3. The tool squash-merged, waited for CI, switched to main and ran `git pull --ff-only origin main` (reflog: fast-forward `4e912e6 -> 16f7041`), then tried `git branch -D gsd/phase-06-preregistration`. Git refused because the worktree `.claude/worktrees/phase-06-preregistration` has that branch checked out, so the tool exited 2 after everything that matters had happened. `gh pr view 19` reads MERGED, main equals origin/main (`git log origin/main..main` is empty) and the remote head branch is gone. The worktree and local branch were left in place, as the plan requires; Claude did not work around the refusal.

### Plan differences from R9 (known)

- PR A holds seven files, not eight, because `bought-nut.tsv` was removed by R9; `gh pr view 19` listed exactly the seven (protocol, `print_matrix.py`, `print_rules.py`, two records, `pyproject.toml`, `tests/test_print_rules.py`).

### Reflog note on acceptance criterion 2

`git reflog -n 30` still shows `reset: moving to origin/main` and `rebase (abort)` entries. They are dated 2026-10-22 15:41 to 16:23, from the Phase 5 landing, before this plan started. This plan's own reflog entries are `checkout`, `pull --ff-only`, `checkout` and `merge` only. Main was never reset, rebased or force-pushed by this plan.

## Issues Encountered

- `make pr.land` refused the local branch deletion (above). The pre-existing state is unchanged by it.
- `gh pr checks --watch` and `make verify` each exceed the foreground tool timeout; both were awaited in the background.

## Owner follow-ups (not done: deleting a branch or worktree is ask-first)

- `git worktree remove .claude/worktrees/phase-06-preregistration`
- `git branch -d gsd/phase-06-preregistration` after the worktree is removed (git will likely demand `-D` because the branch was squash-merged; its three fix commits are in `16f7041`). The remote branch is already deleted
- `.claude/worktrees/phase-05-preregistration` and `gsd/phase-05-preregistration` are the same kind of leftover; untouched.

## Authentication Gates

None.

## Known Stubs

None.

## Threat Flags

None. No new network, auth, file-access or schema surface; the fixes tighten a reader and correct a command in a document.

## Ideas and debt

None filed.

## Self-Check: PASSED

Checked after writing: `dce3862`, `8c5d2d6` and `f418d08` are ancestors of `gsd/phase-06-preregistration` and are not ancestors of the phase branch (squashed into `16f7041`); `16f7041` and the merge `1332178` are ancestors of the phase branch head. `06-PRINT-PROTOCOL.md`, `bench/print_rules.py` and `bench/results/phase-06/print-run-1.tsv` exist on the phase branch, and no `bench/results/phase-06/manifest-*.tsv` exists (nothing exported).
