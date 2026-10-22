---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 03
subsystem: testing
tags: [pr-landing, codex-review, m18-probe, pre-registration, run-guard]

requires:
  - phase: 05-01
    provides: PR A (#17) with the expected pair table, the M18 protocol and the probe
  - phase: 05-02
    provides: the owner's rulings and the phase branch the merge lands on
provides:
  - PR A squash-merged on origin/main (5d90f3e) before any Phase 5 kernel run
  - the phase branch carrying origin/main (merge 3600368), with tests/data/pair_expected.tsv, bench/m18_probe.py and 05-M18-DIAGNOSIS.md
  - bench/m18_probe.py with five Codex findings fixed, each with a kernel-free test that failed before its fix
affects: [05-04, 05-14, 05-17]

actuals:
  tokens: 3500
  tasks: 2
  commits: 3
plan_head_before: 831324d705562e4f45cc31e0ffe5ca2bdd3b7942
plan_head_after: 04376a3

tech-stack:
  added: []
  patterns:
    - "a guard that compares bytes reads both sides as bytes (text mode folds CRLF into LF)"
    - "a run claims its output file with mode x before its first reading; an empty file is an interrupted run"
    - "a probe checks its own harness controls and declares itself void in its header, its table and its exit code"

key-files:
  created:
    - docs/tech_debt/active/2026-10-14-m18-probe-one-entry-has-no-deadline-during-a-run.md
  modified:
    - bench/m18_probe.py
    - tests/test_pair.py
    - docs/tech_debt/INDEX.md

key-decisions:
  - "Finding 1 closed by validation, not a token: the child accepts only a reading in READINGS, re-checks the protocol against the local origin/main ref (no fetch) and requires the parent's empty claimed output file; a hand-started registered reading during a run still has no deadline (tech-debt item, owner sign-off pending)"
  - "Finding 2 closed by opening the output file with mode x before any reading and writing header and rows into that handle at the end, so the file keeps the protocol's shape (header line then 36 rows, no trailing line)"
  - "Commit trailer names the model that wrote the commits (Claude Sonnet 5.5), as in 05-02, not the orchestrator's suggested Opus 5.5"

requirements-completed: [PAIR-03, PAIR-04]

coverage:
  - id: D1
    description: "Codex's five findings on PR #17 are commits on the PR branch, each with a test that failed before its fix, and no protocol file, reading, constant, deadline, verdict or cell_verdict changed"
    requirement: "PAIR-03"
    verification:
      - kind: unit
        ref: "tests/test_pair.py#test_the_run_guard_reads_git_output_as_bytes_so_line_endings_count"
        status: pass
      - kind: unit
        ref: "tests/test_pair.py#test_the_m18_child_runs_only_a_registered_reading_of_a_claimed_run"
        status: pass
      - kind: unit
        ref: "tests/test_pair.py#test_the_m18_one_entry_refuses_before_it_loads_the_kernel"
        status: pass
      - kind: unit
        ref: "tests/test_pair.py#test_the_m18_run_claims_its_output_before_the_first_reading"
        status: pass
      - kind: unit
        ref: "tests/test_pair.py#test_a_void_m18_probe_says_so_in_the_header_the_table_and_the_exit_code"
        status: pass
      - kind: unit
        ref: "tests/test_pair.py#test_the_m18_header_records_the_installed_kernel_pair"
        status: pass
    human_judgment: false
  - id: D2
    description: "PR A is MERGED through make pr.land on green required jobs and the phase branch contains origin/main with make verify green"
    requirement: "PAIR-04"
    verification:
      - kind: other
        ref: "gh pr view 17 --json state -> MERGED (merge 5d90f3e); git merge-base --is-ancestor origin/main HEAD; make verify -> 2698 passed"
        status: pass
    human_judgment: false
---

# Phase 5 Plan 03: Land the pre-registration Summary

**PR A (#17) squash-merged to main as 5d90f3e after five Codex findings on the M18 probe were fixed test-first, and the phase branch merged origin/main with `make verify` green (2698 passed).**

## Performance

- **Duration:** about 50 min (continuation after the Codex checkpoint; CI wait was about 8 min)
- **Started:** 2026-10-14 (continuation of the plan)
- **Tasks:** 2 (Task 1 was the Codex review checkpoint, resolved before this run)
- **Files modified:** `bench/m18_probe.py`, `tests/test_pair.py`, two tech-debt files

## Accomplishments

- Reviewer: Codex (codex-cli 0.162.1, `codex exec -s read-only`), run by the orchestrator. It raised nothing on the derived table, the use of the unmodified `cell_verdict` or the deadline derivation, and five findings on `bench/m18_probe.py`, all applied as their own commits on `gsd/phase-05-preregistration` and pushed.
- Findings, in commit order (one commit each, hooks ran `make verify`):

| # | Codex finding | Commit | Fix | Test (red before) |
|---|---|---|---|---|
| 5 (minor) | `text=True` / `read_text` fold LF and CRLF | 736c3b8 | `_git` returns bytes, `protocol_on_main` compares bytes, `main` reads `read_bytes()` | the git-bytes test (red: `_git` had no `cwd`, so it failed on the signature, not on the CRLF fold) |
| 1 (major) | `--one` bypasses guard, membership, deadline, output protection | d8b1651 | `child_refusal`: reading in `READINGS`, protocol on local origin/main ref byte for byte, empty claimed output file; `_one_line` | `child_refusal` missing; the subprocess test showed the bypass: an off-list clearance 0.5 reading returned `built` |
| 2 (major) | output created only after all readings | 57598e7 | `OUT.open("x")` before any reading, header and rows written into that handle | claim absent during the first reading; interrupted run left no file |
| 3 (major) | harness controls never evaluated | 1910d50 | `harness_void`: four H rows each `built`, volume above `EMPTY_MM3`, within `PAIR_BAND` of `closed_control`; reason in header `void`, `VOID:` line above the table, exit 1 | `harness_void` missing; `main` returned 0 with all four H readings at 0 |
| 4 (major) | header omits the kernel pair | 4be954e | `kernel_versions()` from `importlib.metadata`, header `kernel`; test pins to `requirements.txt` | `KeyError: 'kernel'` |

- Check that nothing forbidden moved: `git diff b7cf17b..4be954e` touches only `bench/m18_probe.py` and `tests/test_pair.py`; no `05-M18-DIAGNOSIS.md`, `pair_expected`, table, verdict code or constant changed (the only changed line mentioning a constant name is an indentation of `ThreadPoolExecutor(max_workers=MAX_CHILDREN)`).
- CI on head 4be954e: `test (3.12)` pass (7m54s), `image` pass, `vendor-bundle` pass.
- `make pr.land PR=17` merged the PR (`gh pr view 17`: MERGED, merge commit 5d90f3e, `git log origin/main -1` is "Pre-register the Phase 5 kernel runs: expected pair verdicts and the M18 diagnosis (#17)") and then ended as predicted with `pr.land: git pull --ff-only origin main failed ... Not possible to fast-forward`, exit 1. Local main is unchanged (73cda42); nothing was reset, rebased or force-pushed (`git reflog` shows only the checkouts).
- Phase branch: `git switch gsd/phase-05-hex-nut-and-kernel-pair-proof`, `git fetch origin`, `git merge --no-edit origin/main` merged without conflict (3600368). `tests/data/pair_expected.tsv`, `bench/m18_probe.py` and `05-M18-DIAGNOSIS.md` are present; `make verify`: 2698 passed, coverage 97.57% (gate 96%).

## Task Commits

1. **Task 1: Codex reviews PR A** - review only, no commit (resolved by the owner's `/gsd-review --codex`)
2. **Task 2: Apply the findings, land PR A, merge origin/main** - five fix commits on the PR branch (736c3b8, d8b1651, 57598e7, 1910d50, 4be954e), the squash commit 5d90f3e on origin/main, the merge 3600368 on the phase branch
3. **Tech-debt item for the one residual** - 04376a3

The `commits: 3` in the frontmatter is measured on the phase branch from the ledger base 831324d (squash commit, merge, tech-debt commit); the five fix commits live on the PR branch and arrive here as the squash, which `git rev-list` on this branch cannot count separately.

## Decisions Made

See `key-decisions`. For finding 1 the simplest closure that did not need a secret was chosen: validate membership, re-run the protocol guard offline in the child and require the parent's claimed file. It leaves one residual (below).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] My first byte-guard test broke the shared git config under the pre-commit hook**
- **Found during:** Task 2, finding 5
- **Issue:** The test ran `git init` and `git config` in a temp dir. The pre-commit hook exports `GIT_DIR` and friends, so inside the hook those commands acted on the real repository: they set `core.bare = true` and `core.autocrlf = false` in `/Users/half/git/halfb00t/screw/.git/config`, and `git init` recreated template files in `.git` (`description`, `*.sample` hooks, `info/`). The first commit attempt then failed with "this operation must be run in a work tree".
- **Fix:** Set `core.bare` back to `false` and removed `core.autocrlf` in `.git/config` (the two keys the test had changed; the original value of `core.bare` is inferred from a working non-bare main checkout, not read from a backup). The test now deletes every `GIT_*` variable before touching git. Both checkouts report clean status and the right branches afterwards.
- **Files modified:** `tests/test_pair.py` (and the shared `.git/config`, repaired by hand)
- **Verification:** commit hooks passed on all later commits; `git config core.bare` reads `false` after each commit.
- **Commit:** 736c3b8
- **Residue for the owner:** untracked template files from the re-init remain in `/Users/half/git/halfb00t/screw/.git` (`description`, `hooks/*.sample`, `info/`); they are inert.

**2. [Rule 2 - Missing critical] Tech-debt item for the residual in finding 1**
- **Found during:** Task 2, finding 1
- **Issue:** A hand-started `--one` of a registered reading during a run is accepted and has no deadline; closing it needs a token the child can verify. CLAUDE.md requires a deliberate cut to be a filed item with the owner's sign-off.
- **Fix:** `docs/tech_debt/active/2026-10-14-m18-probe-one-entry-has-no-deadline-during-a-run.md` (nice) and its INDEX row. The owner's sign-off is outstanding.
- **Commit:** 04376a3

The commit-hook worktree allow-list (`agent-*` branch namespace) did not apply: this is the owner-created worktree on `gsd/phase-05-preregistration`, named by the plan and the orchestrator. The protected-branch check was the one that mattered and held.

**Total deviations:** 2 (1 bug in my own test with a repaired side effect, 1 missing item filed). **Impact:** none on the landed code; the shared git config was repaired and verified.

## Issues Encountered

- `make pr.land` ended with the expected refused pull, exit 1, after the merge.
- Untracked `.DS_Store` files show in the main checkout on `main` (they are ignored on the phase branch by ba10830); not touched.

## Known Stubs

None.

## Owner follow-ups (not done, ask-first operations)

- `git worktree remove .claude/worktrees/phase-05-preregistration`
- `git branch -d gsd/phase-05-preregistration` (it is not merged by ancestry because PR A was squashed, so `-D` may be needed)
- Local `main` is at 73cda42 and diverges from origin/main (unpushed planning commits); the owner decides how to reconcile it.
- Sign off or reject the tech-debt item above.
- Inert template files in the main `.git` from the config incident.

## Threat Flags

None.

## Next Phase Readiness

The pre-registration is on origin/main before any Phase 5 kernel run (SC3, SC6), and the phase branch carries it. The M18 probe now refuses early, repeated, concurrent and off-list runs and declares itself void when a harness control fails; it has not been run (no reading exists).

## Self-Check: PASSED

- FOUND: tests/data/pair_expected.tsv, bench/m18_probe.py, 05-M18-DIAGNOSIS.md, the tech-debt item (all on the phase branch)
- FOUND: 736c3b8, d8b1651, 57598e7, 1910d50, 4be954e (reachable from origin/gsd/phase-05-preregistration), 5d90f3e (origin/main), 3600368, 04376a3 (HEAD ancestry)
- `gh pr view 17 --json state` is MERGED; `git merge-base --is-ancestor origin/main HEAD` true; `make verify` 2698 passed
