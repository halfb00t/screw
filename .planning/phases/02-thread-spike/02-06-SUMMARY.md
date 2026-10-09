---
phase: 02-thread-spike
plan: 06
subsystem: testing
tags: [thread-spike, pre-registration, protocol-guard, cross-cli-review, pr-landing, d-19]

requires:
  - phase: 02-thread-spike
    provides: the harness, verdict rules, pair check and campaign driver (plans 02-02 to 02-05) and the run guard that refuses until the protocol is on origin/main
provides:
  - 02-SPIKE.md complete above the Results line - Environment, Method, Protocol inputs, Rules, Predictions, Escape clause - merged on main before any run
  - test_the_protocol_pre_registers_every_constant_the_harness_uses and the protocol-headings test, binding every ALL_CAPS constant of quiet, maths, verdict, helical, measure (and the cli and runner constants the review added) to the protocol tables
  - bench/README.md section "Thread spike (Phase 2)"
  - PR 5 (PR 1 of 2) merged as squash fd40abc09947744b3e030446085e26a9e1a0c87f; check-protocol reads "protocol guard: held"
  - branch gsd/phase-02-thread-spike-runs cut from the landed main with no commit of its own
affects: [02-07 campaign, 02-08 verdict and decision entry]

actuals:
  tokens: 35460   # chars/4 over added lines of `git diff 5140840 059aa59 -- bench tests 02-SPIKE.md` (141 840 chars, 5 files, 1870 insertions, 254 deletions)
  tasks: 3
  commits: 26     # git rev-list --count 5140840..059aa59 (see Task Commits for what the range contains)
plan_head_before: 5140840400a5a1ef9bffee1a8bb6f176b540d6db
plan_head_after: 059aa59fa5386b11b18c5ae0beb4c06b3b0a4103

tech-stack:
  added: []
  patterns:
    - "Two-PR pre-registration (D-19): PR 1 lands the harness and the protocol with no data; the guard compares the pre-Results text with origin/main's blob, so any later change is a visible new PR"
    - "A test parses the protocol's input tables and fails when a constant is missing or differs from its code value, so no constant moves without the protocol moving"

key-files:
  created: []
  modified:
    - .planning/phases/02-thread-spike/02-SPIKE.md
    - bench/README.md
    - tests/test_bench.py
    - bench/thread_spike/__main__.py
    - bench/thread_spike/verdict.py

key-decisions:
  - "The PR 1 head and the squash commit on main have the identical git tree (059aa59^{tree} == fd40abc^{tree}), so what was reviewed and verified is exactly what landed"
  - "The Task 2 cross-CLI review checkpoint is recorded as satisfied out of band by the owner merging PR 5; the review evidence is indirect (no GitHub review object) and is flagged for human acceptance rather than asserted"

patterns-established:
  - "A plan whose landing replaces its commits with one squash cannot carry a commit ledger on the follow-on branch: plan_head_before/after name the PR head commits, which stay reachable through refs/pull/5/head"

requirements-completed: [INFR-03]

coverage:
  - id: D1
    description: "02-SPIKE.md on main holds Question, Owner rulings, Environment, Method, Protocol inputs, Rules, Predictions, Escape clause, then Results, in that order, written before any run"
    requirement: INFR-03
    verification:
      - kind: other
        ref: "grep -n '^## ' .planning/phases/02-thread-spike/02-SPIKE.md (lines 5, 15, 66, 76, 114, 222, 245, 262, 275 = Question, Owner rulings, Environment, Method, Protocol inputs, Rules, Predictions, Escape clause, Results)"
        status: pass
      - kind: other
        ref: "git log --format='%h %s' origin/main -- .planning/phases/02-thread-spike/02-SPIKE.md (one line: fd40abc, PR 1 squash)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Every harness constant is tied to the protocol by a test that parses the Protocol inputs, PITCH and NUT_HEIGHT tables; a second test asserts the six required headings exist above Results"
    requirement: INFR-03
    verification:
      - kind: unit
        ref: "make test PYTEST_ARGS=\"tests/test_bench.py -q -n0 --no-cov -k 'protocol'\" (13 passed, 422 deselected in 3.54s)"
        status: pass
      - kind: unit
        ref: "tests/test_bench.py#test_the_protocol_pre_registers_every_constant_the_harness_uses"
        status: pass
    human_judgment: false
  - id: D3
    description: "bench/README.md carries the section 'Thread spike (Phase 2)'"
    requirement: INFR-03
    verification:
      - kind: other
        ref: "grep -n '## Thread spike (Phase 2)' bench/README.md (line 84)"
        status: pass
    human_judgment: false
  - id: D4
    description: "PR 5 is MERGED, the protocol guard holds on gsd/phase-02-thread-spike-runs, no campaign record exists on origin/main, the runs branch has no commit of its own, and src/ is untouched by the diff against origin/main"
    requirement: INFR-03
    verification:
      - kind: other
        ref: ".venv/bin/python -m bench.thread_spike check-protocol (exit 0, 'protocol guard: held')"
        status: pass
      - kind: other
        ref: "gh pr list --state merged --head gsd/phase-02-thread-spike --json number,state --jq '.[0].state' (MERGED)"
        status: pass
      - kind: other
        ref: "test \"$(git rev-parse --abbrev-ref HEAD)\" = gsd/phase-02-thread-spike-runs && test \"$(git rev-list --count origin/main..HEAD)\" -eq 0 && test -z \"$(git log --format=%h origin/main -- bench/results/thread-spike)\" (exit 0)"
        status: pass
    human_judgment: false
  - id: D5
    description: "The other CLI reviewed PR 1 while no data existed and the owner gave the land signal"
    requirement: INFR-03
    verification: []
    human_judgment: true
    rationale: "No GitHub review object or comment exists on PR 5 (reviews and comments both empty, reviewDecision empty). The evidence is indirect: review finding ids F4 and G6 are cited in the protocol (added by adccd4a on 2026-10-08), 23 fix(02-06) commits follow the Task 1 commit by hours, and the owner merged the PR personally. Which CLI performed the review, and the content of the findings and rejections, is unverified from the repo. A human must accept this as satisfying the D-19 review requirement."

duration: 5 min
completed: 2026-10-08
status: complete
---

# Phase 2 Plan 06: Protocol Pre-registration Summary

**The thread spike protocol, a test binding every harness constant to it, and the harness were merged to main as PR 5 (squash `fd40abc`) before any run; the protocol guard now reads "held" on a runs branch cut from that main with no commit of its own.**

## Performance

- **Duration:** 5 min for this session, which only verified the landed state and wrote this record. The work itself (Task 1, the review fixes, the landing) was done in earlier sessions and a second CLI and was not timed.
- **Started:** 2026-10-08T10:40:11Z
- **Completed:** 2026-10-08T10:45Z (approximate; the metadata commit follows)
- **Tasks:** 3 (Task 1 verified on main, Task 2 recorded as satisfied out of band, Task 3 proofs run)
- **Files modified (landed):** 5 (`02-SPIKE.md`, `bench/README.md`, `tests/test_bench.py`, `bench/thread_spike/__main__.py`, `bench/thread_spike/verdict.py`); this session changed none of them.

## Accomplishments

- The protocol is on `main` above the `## Results` line, with Environment, Method, Protocol inputs, Rules, Predictions and Escape clause; `git log origin/main` for the file shows exactly one commit, the PR 5 squash.
- A test ties every pre-registered constant to the protocol tables, so a moved constant fails the gate until the protocol says so.
- PR 5 merged on 2026-10-08T09:28:22Z by the owner (`halfb00t`); required jobs `image`, `test (3.12)` and `vendor-bundle` read pass (`gh pr checks 5`).
- `gsd/phase-02-thread-spike-runs` is at `fd40abc` == `origin/main` with zero commits of its own; `check-protocol` holds.

## Task Commits

The plan's commits were made on the branch `gsd/phase-02-thread-spike` and replaced on `main` by the single squash commit `fd40abc09947744b3e030446085e26a9e1a0c87f` ("Phase 2, PR 1 of 2: thread spike protocol and harness (pre-registration) (#5)"). The PR head was `059aa59fa5386b11b18c5ae0beb4c06b3b0a4103`; its git tree is identical to the squash commit's tree (verified: `059aa59^{tree}` equals `fd40abc^{tree}`). The commits stay reachable through `refs/pull/5/head` and the stale local branch.

1. **Task 1: Write the protocol, tie every constant to it, open PR 1** - `989949a` (docs: `docs(02-06): pre-register the thread spike protocol and tie every constant to it`), folded into `fd40abc`.
2. **Task 2: Cross-CLI review of PR 1** - no commit of its own; satisfied out of band (see Review evidence). Its findings landed as the 23 `fix(02-06)`/`test(02-06)`/`docs(02-06)` commits `5fc4056` to `e77d7af`, authored 2026-10-08 07:20 to 13:34 +06:00, 10 to 16 hours after `989949a` (2026-10-07 21:17). Whether each of those was a review finding is **unverified**; only F4 and G6 are named as review findings (in `02-SPIKE.md`).
3. **Task 3: Apply findings, land, cut PR 2's branch** - landing is `fd40abc`; the branch cut is `git checkout -b gsd/phase-02-thread-spike-runs` from that main (no commit).

**What the commit range contains (`5140840..059aa59`, 26 commits, the figure in `actuals.commits`):** 24 are `fix`/`test`/`docs(02-06)` commits on the harness and protocol including `989949a`; 1 is `3964e3f` `docs(tech-debt)` (the second occurrence of the dying-worker flake, not plan work); 1 is `059aa59` `docs(02-06)` state tracking. One further commit, `5140840` `fix(02-06): a K sweep in which no K qualified fires the escape clause`, is the parent of `989949a` and so the `plan_head_before` base; it is **not** inside the range. It was committed 2026-10-06 20:50, a day **before** the Task 1 commit, so it is a harness commit that predates the protocol write-up and cannot be shown to be a review fix. The orchestrator brief called it a review-fix commit; the git history does not support that.

**Plan metadata:** the `docs(02-06): complete the protocol pre-registration plan` commit that carries this file (hash in the return message).

## Files Created/Modified

Landed through PR 5 (not changed in this session):
- `.planning/phases/02-thread-spike/02-SPIKE.md` - the protocol, 230 added lines over the PR's later commits
- `bench/README.md` - the "Thread spike (Phase 2)" section (32 lines)
- `tests/test_bench.py` - the constant check, the headings check and tests for the review-driven verdict changes
- `bench/thread_spike/__main__.py`, `bench/thread_spike/verdict.py` - review-driven fixes (e.g. `cli.COMPLETE_BLOCKS`, `cli.ESCAPE_SOURCES`, completeness and escape-clause rules)

Created in this session: this file. STATE.md and ROADMAP.md are updated by the metadata commit.

## Evidence recorded this session (2026-10-08)

Task 1 acceptance criteria, re-checked against main's tree:

| Criterion | Command | Result |
|---|---|---|
| Heading order | `grep -n '^## ' .planning/phases/02-thread-spike/02-SPIKE.md` | 5 Question, 15 Owner rulings, 66 Environment, 76 Method, 114 Protocol inputs, 222 Rules, 245 Predictions, 262 Escape clause, 275 Results: PASS |
| README section | `grep -n '## Thread spike (Phase 2)' bench/README.md` | line 84: PASS |
| Constant test exists | `git show fd40abc:tests/test_bench.py \| grep -c 'def test_the_protocol_pre_registers_every_constant_the_harness_uses'` | 1: PASS |
| Protocol tests | `make test PYTEST_ARGS="tests/test_bench.py -q -n0 --no-cov -k 'protocol'"` | `13 passed, 422 deselected in 3.54s`: PASS |
| `check-protocol` exits 2 | superseded: that criterion was pre-landing; it is now "exits 0, held" (see below) | superseded |
| `git diff --quiet origin/main...HEAD -- src/` | same command | exit 0 (trivially: HEAD == origin/main): PASS |
| T_PASS mutation proof | **not re-run** (the `bench/` prohibition forbids the edit in this plan). Cited from the PR 5 body: "Checked locally by changing `T_PASS` to 2e-4: the test failed naming `verdict.T_PASS`; reverted." This is the author's statement, unverified here. | cited, not reproduced |
| PR open with attribution line | `gh pr view 5 --json body --jq .body \| tail -3` | last line `Generated with [Claude Code](https://claude.com/claude-code)` (with the robot emoji): PASS. No skip token in title or body: a grep for `skip ci`, `ci skip`, `[skip`, `no ci`, `skip-checks` counted 0. |

Task 3 step 6, the three order proofs, verbatim:

```
$ .venv/bin/python -m bench.thread_spike check-protocol
protocol guard: held
- origin/main protocol blob: `4e1959ea085dae8b7e9e5e29e488e1c64ef0964e`
- origin/main protocol commit: `fd40abc09947744b3e030446085e26a9e1a0c87f`
- HEAD: `fd40abc09947744b3e030446085e26a9e1a0c87f`
(exit 0)

$ git log --format='%h %s' origin/main -- .planning/phases/02-thread-spike/02-SPIKE.md
fd40abc Phase 2, PR 1 of 2: thread spike protocol and harness (pre-registration) (#5)

$ git log --format=%h origin/main -- bench/results/thread-spike
(empty)
$ git ls-tree -r --name-only origin/main -- bench/results/thread-spike
(empty)
```

Task 3 `<verify>` block:

| Check | Command | Result |
|---|---|---|
| PR merged | `gh pr list --state merged --head gsd/phase-02-thread-spike --json number,state --jq '.[0].state'` | `MERGED` (the query worked; the `gh pr view 5` fallback was not needed). `gh pr view 5` also reads number 5, base main, head `gsd/phase-02-thread-spike`, mergedAt 2026-10-08T09:28:22Z, mergeCommit `fd40abc09947744b3e030446085e26a9e1a0c87f`, mergedBy `halfb00t`. |
| Guard holds | `check-protocol` (above) | exit 0 and "protocol guard: held": PASS |
| Branch state | `test "$(git rev-parse --abbrev-ref HEAD)" = gsd/phase-02-thread-spike-runs && test "$(git rev-list --count origin/main..HEAD)" -eq 0 && test -z "$(git log --format=%h origin/main -- bench/results/thread-spike)"` | exit 0: PASS |

Task 3 acceptance criteria:

1. PR 1 is MERGED and `main`'s newest commit touching `02-SPIKE.md` is its squash commit: PASS (`fd40abc`, the only one).
2. `check-protocol` exits 0 with "protocol guard: held" on the runs branch: PASS.
3. No file under `bench/results/thread-spike/` on `origin/main`: PASS (empty `git ls-tree`).
4. No force push: **PASS as far as the repo shows, with a limit.** `git reflog | grep -E 'forced-update|forced update|reset: moving|update by push'` found nothing (exit 1); the branch's reflog holds only `commit:` entries. The local reflog cannot see the remote's reflog, so a force push by the owner or the other CLI is not excluded by this alone; the remote branch no longer exists (`git ls-remote --heads origin gsd/phase-02-thread-spike` is empty) and `main` history shows only the squash. The orchestrator-visible history is the squash.

## Review evidence (Task 2, satisfied out of band)

The checkpoint's resume condition (PR landed with the owner's signal) is met by the owner merging PR 5. Recorded as it is, not as a reply that did not happen:

- GitHub holds no review objects and no comments on PR 5: `gh pr view 5 --json reviews,comments,reviewDecision` returns `"reviews":[]`, `"comments":[]`, `"reviewDecision":""`.
- Indirect evidence: `02-SPIKE.md` rows `cli.COMPLETE_BLOCKS` ("plan 02-06 review F4") and `cli.ESCAPE_SOURCES` ("plan 02-06 review G6") cite review finding ids; `git log -S` places both in `adccd4a` (2026-10-08 11:15 +06:00, after the Task 1 commit). No commit body names a review, a finding id or Codex.
- All 27 commits in `5140840~1..059aa59` carry the author `Andrew S <halfb00t@gmail.com>`, so authorship does not show which CLI wrote or reviewed what.
- The squash commit's author is the owner; the committer is GitHub. Whether `make pr.land` or the GitHub button did the merge is **unverified**.
- This is flagged `human_judgment: true` (D5 above): a human must accept this as the D-19 review. The AGENTS.md rule "whoever wrote the diff does not review it" cannot be confirmed from the repo.

## Decisions Made

- The landed tree equals the reviewed PR head's tree, so the protocol on main is the protocol that was verified, not a later edit.
- The Task 2 checkpoint is recorded as satisfied out of band, with the evidence limits above, instead of re-opening it.

## Deviations from Plan

None to the code: this session made no code or protocol change.

Process notes (not auto-fixes):

- **Task 2 not executed as written.** The plan calls for the owner's "land" reply in this session; the owner instead performed the merge. The brief for this run directs recording the checkpoint as satisfied out of band, which this file does.
- **T_PASS mutation not re-proved.** Cited from the PR body (see table), because re-proving would edit `bench/`, which this plan's prohibitions forbid.
- **Plan `files_modified` lists 3 files; the landed change touches 5.** The two extra are `bench/thread_spike/__main__.py` and `verdict.py`, allowed by Task 3's `<files>` for accepted review findings.
- **Self-check wrinkle.** `gsd_run check evaluation-scope --plan 02-06 --commits-only` returned `reason: no-matching-commits` before this plan's metadata commit: the runs branch has no commit of its own and the plan's commits sit under the squash. This is the expected result of the two-PR landing, not a missing change.

**Total deviations:** 0 auto-fixed. **Impact on plan:** none; SC1 is met by construction (the protocol's squash commit is on main and `bench/results/thread-spike` is empty there).

## Issues Encountered

- The orchestrator brief describes `5140840` as a review-fix commit; its commit date (2026-10-06 20:50) precedes the Task 1 commit (2026-10-07 21:17) and it is the Task 1 commit's parent. It is therefore recorded as a pre-protocol harness commit.
- `plan_head_before`/`plan_head_after` name PR-head commits, not commits on `main` (the squash replaced them). `/gsd-verify-work`'s same-instrument check needs those objects; they are held by `refs/pull/5/head` on origin (`git ls-remote origin refs/pull/5/head` returns `059aa59fa5386b11b18c5ae0beb4c06b3b0a4103`) and by the stale local branch `gsd/phase-02-thread-spike`, which this plan did not touch. Deleting both would orphan them.
- No tech-debt or idea file was filed: no defect was found. (`3964e3f`, an earlier tech-debt item, came in with the PR.)

## Known Stubs

None. This session created only this summary.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for plan 02-07 (the campaign, which the owner runs detached with agents closed). The guard holds; any change to the protocol text above `## Results` now makes it refuse, so plan 02-07 must change no harness file.
- Open item for the owner: accept or reject the indirect review evidence (D5). If it is rejected, the remedy is a review on the existing record, not a new protocol edit.
- `.planning/STATE.md` carries "Plan: 1 of 8" from earlier sessions; the SDK advance below sets the counter and progress from disk.

## Self-Check: PASSED

- FOUND: `.planning/phases/02-thread-spike/02-SPIKE.md`, `bench/README.md`, `tests/test_bench.py`.
- FOUND: `fd40abc` is an ancestor of HEAD (`git merge-base --is-ancestor fd40abc HEAD`).
- FOUND as objects: `989949a`, `5140840`, `059aa59` (reachable via `refs/pull/5/head`; `989949a` is not an ancestor of `origin/main` because the squash replaced it).
- Task 1 and Task 3 acceptance criteria re-run above; all PASS except the two noted as superseded or cited-not-reproduced.

---
*Phase: 02-thread-spike*
*Completed: 2026-10-08*
