---
phase: 03-real-helical-thread
plan: 07
subsystem: docs
tags: [decision-log, tech-debt, coverage-floor, l12, interim-register, spur-l34]

requires:
  - phase: 03-real-helical-thread
    provides: the builder, gate, caps, refusals, left_hand, page changes and slow tier of plans 03-01 to 03-06, and the fix commits of four retired debt items
provides:
  - "L12 in the decision log: what later phases build on from Phase 3, citing L11's run ids"
  - "the module map, README, package docstring and bench docs describe the threaded rod"
  - "the INTERIM register carries MIN_TAIL_MM, MAX_TURNS, FINE_STL_ROWS and the in-cap costs D-18 accepted"
  - "the four items Phase 3 retired name their fix shas, in their files and in the INDEX"
  - "the coverage floor re-measured on the Phase 3 suite: fail_under 96"
affects: [phase-04, phase-05, phase-07]

actuals:
  tokens: 5712
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "a decision entry restates a value only with its run id or a labelled probe; it measures nothing new"
    - "a retired debt item names the fix commit sha it was resolved in, in the file and in the INDEX row"
    - "the coverage floor is re-measured by spur L34's rule (one serial, three -n 8) and cited from pyproject.toml"

key-files:
  created: []
  modified:
    - docs/architecture/decision_log.md
    - docs/architecture/overview.md
    - README.md
    - src/screw/__init__.py
    - bench/corpus.py
    - bench/README.md
    - bench/memory.py
    - bench/RESULTS.md
    - docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md
    - docs/tech_debt/resolved/2026-10-06-collapsed-thin-solid-served-as-200.md
    - docs/tech_debt/resolved/2026-10-06-repeated-query-key-silently-wins.md
    - docs/tech_debt/resolved/2026-10-06-ui-drops-foreign-hash-keys.md
    - docs/tech_debt/resolved/2026-10-06-ui-hides-warnings-on-failed-update.md
    - docs/tech_debt/INDEX.md
    - pyproject.toml
    - Makefile

key-decisions:
  - "L12 reads L11's 'cap-and-warn input' as a refusal for the 250-turn and fine-STL artefacts and says so in the entry, not as a superseding entry (D-15)"
  - "The coverage floor moves from 94 to 96: L = 96.66, S = 0.36, floor(96.30) = 96"
  - "Resolved in: lines name the fix shas without a PR number, because no PR exists yet (b537528 added the number afterwards)"

patterns-established:
  - "Probe figures are labelled research probe or planner probe 2026-10-10, single runs on macOS arm64, bounding nothing"

requirements-completed: [THRD-01, THRD-02, THRD-04]

coverage:
  - id: D1
    description: "L12 is in the decision log with the builder, gate, caps, pitch bound, hand, link refusals, standing warning and slow tier; every L11 value cites its run id and every probe figure is labelled"
    requirement: THRD-04
    verification:
      - kind: other
        ref: "grep -n '^## L12' docs/architecture/decision_log.md; grep -c '2026-10-08-a-' docs/architecture/decision_log.md (21); MIN_TAIL_MM, check_solid, 2026-10-08-a-frontier, 2026-10-08-a-grid and Reversibility: present below the L12 heading"
        status: pass
    human_judgment: true
    rationale: "A grep proves the terms are present, not that each sentence says what the code does; the owner reads the entry that later phases will cite"
  - id: D2
    description: "overview.md, README.md, the package docstring and the bench docs describe the bolt as a threaded rod and name calc/thread.py, solid/helical.py, the gate and the grid tier; no tracked description outside the exempt records calls the bolt a cylinder"
    requirement: THRD-01
    verification:
      - kind: other
        ref: "! git grep -n -i -e 'plain unthreaded' -e '12 plain cylinders' -e 'walking.skeleton bolt' -e 'builds no thread' -- src README.md docs/architecture bench/corpus.py bench/README.md bench/memory.py (printed nothing)"
        status: pass
      - kind: integration
        ref: "tests/test_cli.py#test_readme_cli_examples_run"
        status: pass
    human_judgment: false
  - id: D3
    description: "The INTERIM register lists MIN_TAIL_MM, MAX_TURNS and FINE_STL_ROWS with their sources and records the D-18 figures; still Severity must with the Phase 7 trigger"
    requirement: THRD-04
    verification:
      - kind: other
        ref: "grep -q for MIN_TAIL_MM, MAX_TURNS, FINE_STL_ROWS, '7875 MiB' and 'Severity: must' in docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md"
        status: pass
    human_judgment: false
  - id: D4
    description: "Each of the four items Phase 3 retired names its fix commit in Resolved in: and in its INDEX row, and every sha is reachable from HEAD"
    requirement: THRD-04
    verification:
      - kind: other
        ref: "grep -E '^Resolved in: [0-9a-f]{7}' on the four files; git cat-file -e and git merge-base --is-ancestor for de9304e, eaaac85, d849557, 05fb4ed, 909dec3"
        status: pass
    human_judgment: false
  - id: D5
    description: "The coverage floor is re-measured on the 843-test suite by spur L34's rule and fail_under equals its result (96)"
    verification:
      - kind: other
        ref: "bench/RESULTS.md '## Coverage floor (Phase 3)': serial 96.66, -n 8 97.02, 96.66, 97.02; pyproject.toml fail_under = 96; make verify 'Required test coverage of 96.0% reached. Total coverage: 97.02%'"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-10-10
status: complete
commits: 3
plan_head_before: 50394ad633e906d9d89b9b9ffc0332777601415e
plan_head_after: bbee02732939d30cb2c5a0ad9a86f080194dc904
---

# Phase 3 Plan 07: L12, the threaded-rod docs, the INTERIM costs and the coverage floor Summary

**L12 records what Phase 3 built on L11 (length-taking builder, THRD-04 gate, 250-turn and fine-STL refusals, root-radius bound, `left_hand` on the base, slow tier); the docs describe the threaded rod; the four retired debt items name their fix shas; the INTERIM register carries the thread's accepted costs; and the coverage floor is re-measured at 96.**

## Performance

- **Duration:** 12 min (SUMMARY write and state updates follow)
- **Started:** 2026-10-10T16:39:56Z
- **Completed:** 2026-10-10T16:52Z
- **Tasks:** 3
- **Files modified:** 16 (0 created, 16 modified)

## Accomplishments

- `## L12` in `docs/architecture/decision_log.md`: Builder, Gate, Caps, Pitch, Hand, Links and keys, Standing warning and info document, Slow tier, and an Open paragraph pointing at the debt register, then Reason and Reversibility (costly overall; one-way for the `left_hand` field, default and hash spelling; reversible for the caps and `MIN_TAIL_MM`). It cites `2026-10-08-a-ksweep`, `-frontier`, `-grid`, `-controls` and the verdict; every other figure is labelled research probe or planner probe 2026-10-10, single runs on macOS arm64. It adds no measurement of its own. The two local grid shards of plan 03-06 are cited as a harness check, not a bound, and the first GitHub-runner run is stated as not made.
- `overview.md` describes the threaded rod, names `calc/thread.py` (oracle and kernel-free rules), `solid/helical.py` (the one builder for rod and void) and the gate in `solid/__init__.py`, the `bench/` row mentions `make grid` and `grid.yml`, and the contract list gains the unnumbered spike contract, noting that it now also covers `screw.calc.thread` through the import-back. The count of contracts in force reads seven (it said six; the hook's `Contracts: 7 kept, 0 broken` was already seven).
- `README.md`, `src/screw/__init__.py`, `bench/corpus.py`, `bench/README.md` and `bench/memory.py` say the bolt builds the L11 thread and that the corpus is threaded at the default 1 mm pitch and still no bound. The README commands are unchanged and `test_readme_cli_examples_run` stays green.
- `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md`: the shifted line numbers, three new Related files (`helical.py`, `calc/thread.py` twice), three new knob rows (`MIN_TAIL_MM` 1e-3 mm, `MAX_TURNS` 250, `FINE_STL_ROWS`) with their sources, a "What the thread costs inside the caps" paragraph with the D-18 figures as single runs that bound nothing (d=100, pitch=5, length=1250: fine STL 36,906,760 triangles, 1760 MiB, 152.6 s, peak RSS 7875 MiB; preview 6,452,418 triangles, 308 MiB, 6.7 s, RSS 1534 MiB; d=6, pitch=0.1, length=25 fine: 2,126,222 triangles, 101 MiB, RSS 1327 MiB; planner probe d=1e5, pitch=1, length=1 builds in 0.01 s and its preview STL did not finish in 120 s). Severity stays must, trigger Phase 7 (OPER-01 to OPER-03).
- The four retired items name their commits in `Resolved in:` and in the INDEX: `de9304e` (collapsed solid, blocker), `eaaac85` (API) and `d849557` (CLI) for the repeated key, `05fb4ed` (foreign hash keys), `909dec3` (warnings on a failed update). Each was confirmed against its plan SUMMARY and with `git cat-file -e` and `git merge-base --is-ancestor` on this branch before it was written.
- Coverage floor by spur L34's rule: serial 96.66 %, `-n 8` 97.02, 96.66, 97.02 %; L = 96.66, S = 0.36, floor(96.30) = **96**, up from 94. `fail_under = 96` with its comment citing the entry; `bench/RESULTS.md` has `## Coverage floor (Phase 3)` with the four rows, load averages, host, the per-module column (`calc/thread.py` and `solid/helical.py` both 100.00 %) and the statement that it is a floor on what the suite covers.

## Task Commits

1. **Task 1: L12 and the documents describe the threaded rod that ships** - `8fd6a4e` (docs)
2. **Task 2: the INTERIM register records the thread's costs; the retired items name their fix commits** - `1144bca` (docs)
3. **Task 3: re-measure the coverage floor on the Phase 3 suite** - `bbee027` (test)

**Plan metadata:** the SUMMARY commit and the STATE/ROADMAP commit follow (docs).

## Files Created/Modified

- `docs/architecture/decision_log.md` - `## L12`
- `docs/architecture/overview.md` - Phase 3 state, module rows, contract list
- `README.md`, `src/screw/__init__.py`, `bench/corpus.py`, `bench/README.md`, `bench/memory.py` - the bolt is a threaded rod
- `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` - the three knobs, the costs, the shifted lines, two stale rows restated
- `docs/tech_debt/resolved/...` (four files) and `docs/tech_debt/INDEX.md` - the fix shas
- `bench/RESULTS.md` - `## Coverage floor (Phase 3)`
- `pyproject.toml` - `fail_under = 96` and its comment; `Makefile` - the comment that cites the entry

## Decisions Made

- L12 gives the reading of L11's "cap-and-warn input" in the entry itself (a refusal for two artefacts, because `length` is an explicit choice) and calls it a reading, not a superseding entry, as D-15 specified.
- No PR number in the `Resolved in:` lines, because the Phase 3 PR does not exist yet (`gh pr list --head gsd/phase-03-real-helical-thread` printed nothing). Plan 03-05's `b537528` precedent added the number in a later commit; the ship step can do the same.
- `L12` labels the unreadable-hash-value refusal (`#d=abc`) as resting on browser number-input sanitisation that no test has run, as plan 03-05 recorded.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Two stale rows in the INTERIM register said the skeleton cylinder was cheap**
- **Found during:** Task 2
- **Issue:** the `SCREW_BUILD_TIMEOUT` row said "the skeleton cylinder builds in well under a second" and the `mem_limit` row said "the skeleton is lighter". Both are false for a thread: an in-cap fine STL peaked at 7875 MiB against the 4g limit.
- **Fix:** the first now reads M6 x 20 builds in 0.09 s (planner probe) while an in-cap off-row part can need minutes; the second points at the 7875 MiB figure. The `INTERIM_MAX_MM` row got the F1-was-for-the-cylinder sentence the plan asked for, and the "Why it matters" and "Next step" paragraphs name the new knobs.
- **Files modified:** docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md
- **Committed in:** 1144bca

**2. [Rule 1 - Bug] The contract count in overview.md and the Makefile's floor citation were stale**
- **Found during:** Tasks 1 and 3
- **Issue:** the overview said six contracts are in force (seven are, once the spike contract is listed), and `Makefile` line 89 cites `"Coverage floor (Phase 1)"`, which is no longer the entry `fail_under` comes from. `Makefile` is not in the plan's file list.
- **Fix:** "Seven are in force" with the unnumbered spike contract added; the Makefile comment now cites Phase 3.
- **Files modified:** docs/architecture/overview.md, Makefile
- **Committed in:** 8fd6a4e, bbee027

---

**Total deviations:** 2 auto-fixed (both Rule 1, stale text). **Impact on plan:** none on behaviour; all four changes are comments or prose.

## Issues Encountered

- The serial coverage run printed `843 passed, 60 deselected in 108.15s` and its coverage table; its exit status was not recorded (the command was wrapped in `time`). The earlier segfault-at-exit item (`2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md`) concerns `tests/test_bench.py` run alone, and this run was the whole suite.
- In the floor measurement the `pool.py` line loss (3 of 56 lines) appeared in the serial run and in `-n 8` run 2. Phase 1 saw it in the serial run only. The cause was not isolated; the rule already takes the lowest total. It is the reason S is 0.36 and not 0.00.

## User Setup Required

None - no external service configuration required.

## Verification

- `make verify` (last run, before the Task 3 commit; the hook re-ran it and passed): `All checks passed!`; `Success: no issues found in 47 source files`; `Contracts: 7 kept, 0 broken.`; `Required test coverage of 96.0% reached. Total coverage: 97.02%`; `============================= 843 passed in 35.21s =============================`.
- Task 1 automated checks: `^## L12` found at line 412; `grep -c '2026-10-08-a-' docs/architecture/decision_log.md` printed 21; `helical` found in overview.md; the `git grep` for the four present-tense phrases printed nothing.
- Task 2 automated checks: the five `grep -q` terms in the register passed; the four `Resolved in: [0-9a-f]{7}` lines matched; the five shas pass `git cat-file -e` and `git merge-base --is-ancestor`; the INDEX `## Resolved` table lists the four with the same shas and `## Active` lists none of them.
- Task 3 automated checks: the `## Coverage floor (Phase 3)` heading and the `pyproject.toml` citation are present; `fail_under = 96`.

## Debt

- Filed: none. Resolved: none by this plan (the four items were retired in 03-01, 03-04 and 03-05; this plan names their shas).
- Open items as of this plan: `2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md` (must, plan 03-06), `2026-10-10-spike-protocol-amendments-before-next-campaign.md` (must, PR #9), and the interim-bounds register, now with the thread's costs.

## For the owner

- **AGENTS.md line 16** (`CLAUDE.md` is its symlink) still says the bolt is "a plain unthreaded cylinder" and "Walking skeleton (Phase 1)". It is the agents' instruction file, so this plan did not edit it. Suggested wording is the owner's: the bolt is a threaded rod, no head, table or nut yet (Phase 3).
- `compose.yaml` line 18 still carries "the skeleton is lighter" in the `mem_limit` comment. It is outside this plan's files; the interim register's `mem_limit` row now states the 7875 MiB figure. The comment can change when compose.yaml is next touched.
- The Phase 3 PR number can be added to the four `Resolved in:` lines and INDEX rows once the PR exists, as `b537528` did for PR #7.

## Known Stubs

None.

## Threat Flags

None. The plan adds no endpoint, file access or schema; T-3-16 is mitigated as planned (every L12 and register value cites a run id or a labelled probe, and the retired items name real commits). No package installed.

## Next Phase Readiness

Phase 3's records are complete: the next step is the end-of-phase verifier (the human checks listed in the 03-05 SUMMARY are still to be run in a browser), then the phase PR. The first `workflow_dispatch` of `grid.yml` after merge measures the GitHub-runner wall time per size and its result goes into `bench/RESULTS.md`; until then the 120-minute timeout is a guess (03-06). Phase 4 starts from L12 and rewrites the standing warning when the head lands.

## Flag for the verifier

`requirements mark-complete` ticked THRD-01, THRD-02 and THRD-04 from this plan's `requirements` field, once every plan declaring them had a SUMMARY. THRD-02's text also says "a left-hand pair is proven by the same checks as a right-hand pair"; plan 03-04 did not claim that clause (it is Phase 5's PAIR-03 pair proof; 03-04 proves a left-hand rod passes the same THRD-04 gate and is left-handed by an `isInside` probe). Whether the box stays ticked is the verifier's call.

## Self-Check: PASSED

All 16 modified files exist on disk; commits `8fd6a4e`, `1144bca` and `bbee027` are ancestors of HEAD; the plan commit ledger measures 3 commits from `50394ad`; the working tree holds only untracked `.DS_Store` and `.planning/ui-reviews/` files that predate this plan.

---
*Phase: 03-real-helical-thread*
*Completed: 2026-10-10*
