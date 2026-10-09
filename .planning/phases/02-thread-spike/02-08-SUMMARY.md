---
phase: 02-thread-spike
plan: 08
subsystem: testing
tags: [thread-spike, verdict, decision-log, l11, escape-clause, d-10, d-16, sc4, sc5]

requires:
  - phase: 02-thread-spike
    provides: the committed campaign records of prefix 2026-10-08-a and the pre-registered protocol (plans 02-06 and 02-07)
provides:
  - "bench/RESULTS.md `### 2026-10-08-a-verdict`: the verdict re-run on the committed records, exit 1, byte-identical to the campaign log's verdict section"
  - "02-SPIKE.md `## Results` (one subsection per question) and `## Verdict`, written by citation of run ids and RESULTS.md entries, no figure re-typed (D-16)"
  - "docs/architecture/decision_log.md L11: sewn twist-section at K = 3, BRepGProp volumes at eps 1e-6 gated at T_gate 9e-05, turn cap per size, pair check per size, THRD-04 known-bad inputs, container outcome, escape clause FIRED, conditions of the record, UNVERIFIED/INTERIM inputs"
  - "STATE.md and ROADMAP.md carry the escape-clause consequence: Phase 5 is not planned until the roadmap is revised (SC5); Phase 3 stays plannable"
affects: [03-real-helical-thread, 05-hex-nut-and-kernel-pair-proof]

actuals:
  tokens: 25563   # chars/4 over the added lines of `git diff cb3c39b..bfd5a45` (102253 chars, 5 files); dominated by the verbatim verdict block in bench/RESULTS.md, measured before this file was written
  tasks: 3
  commits: 2        # MEASURED: git rev-list --count cb3c39bc3cbfbb0d92dfede7c56a679d0cd65d0a..bfd5a45 (this file's metadata commit follows)
plan_head_before: cb3c39bc3cbfbb0d92dfede7c56a679d0cd65d0a
plan_head_after: bfd5a45bc171c1a15ad48f3ec98a23bd3f3745f4

tech-stack:
  added: []
  patterns:
    - "A decision entry takes its numbers from a pre-registered rule's output with the run id beside each; a value the campaign could not establish is written 'not established', never filled"

key-files:
  created:
    - .planning/phases/02-thread-spike/02-08-SUMMARY.md
  modified:
    - .planning/phases/02-thread-spike/02-SPIKE.md
    - bench/RESULTS.md
    - docs/architecture/decision_log.md
    - .planning/STATE.md
    - .planning/ROADMAP.md

key-decisions:
  - "L11: the construction is the sewn twist-section at K = 3; the volume estimator is BRepGProp.VolumeProperties_s at eps 1e-6 (never the default Volume()), gated at T_gate 9e-05; turn caps per size are construction 250 turns for every size, a bytes cap from M8 up, and a seconds cap 'not established' for every size"
  - "L11 escape clause FIRED: size M18 is not falsifiable (right, left hand) in 2026-10-08-a-pair (decisive); the owner chose 'revise: Phase 5', so Phase 5 is not planned until the roadmap is revised and no direction is named yet; Phase 3 stays plannable"

patterns-established:
  - "The verdict is a deterministic function of the committed records: re-run it and diff against the campaign log before writing any claim"

requirements-completed: [INFR-03]

coverage:
  - id: D1
    description: "The verdict re-run on the committed records equals the campaign log's verdict section and its exit code (1) is recorded in bench/RESULTS.md"
    requirement: INFR-03
    verification:
      - kind: other
        ref: "`python -m bench.thread_spike verdict --campaign 2026-10-08-a` exit 1; diff against lines 13-1086 of bench/results/thread-spike/2026-10-08-a-campaign.md empty; fenced block in RESULTS.md byte-equal"
        status: pass
    human_judgment: false
  - id: D2
    description: "02-SPIKE.md Results and Verdict answer the four questions by citation, and nothing above `## Results` changed"
    requirement: INFR-03
    verification:
      - kind: other
        ref: ".venv/bin/python -m bench.thread_spike check-protocol (prints 'protocol guard: held'); `grep -nx '## Verdict'` finds 337"
        status: pass
    human_judgment: false
  - id: D3
    description: "L11 is in the decision log with every required part, every number citing a run id, and the owner's escape-clause choice recorded"
    requirement: INFR-03
    verification:
      - kind: other
        ref: "grep -n '^## L11' docs/architecture/decision_log.md (line 284); commit bfd5a45"
        status: pass
    human_judgment: true
    rationale: "The wording of a locked decision is accepted by the owner; the numbers come from rules, but whether L11 says what the owner means is a judgment the owner made at the Task 2 checkpoint on the drafted text, and the final wording differs from the draft only in the date line, the escape-clause direction and one line rewrap"
  - id: D4
    description: "No thread-building field or builder exists in src/ when L11 is committed (SC4)"
    requirement: INFR-03
    verification:
      - kind: other
        ref: "git diff --quiet origin/main -- src/ (exit 0) and git grep for helix/Helix/PipeShell/left_hand/thread_length/Sewing under src/screw (exit 1)"
        status: pass
    human_judgment: false
  - id: D5
    description: "STATE.md and ROADMAP.md carry the escape-clause consequence (Phase 5 not planned until the roadmap is revised)"
    requirement: INFR-03
    verification:
      - kind: other
        ref: "STATE.md Blockers line 'Phase 5 not planned until the roadmap is revised (L11, SC5)'; ROADMAP.md Phase 5 '**Precondition (L11 escape clause)**' line"
        status: pass
    human_judgment: false
  - id: D6
    description: "make verify is green with the L11 commit"
    verification:
      - kind: other
        ref: "make verify: 695 passed, total coverage 95.56% (required 94.0%); the pre-commit hook ran it and passed"
        status: pass
    human_judgment: false

duration: 61min
completed: 2026-10-09
status: complete
---

# Phase 2 Plan 08: Verdict and Decision Entry Summary

**The thread spike's verdict is reproduced and written by citation, and L11 locks a sewn twist-section at K = 3 with precise volumes gated at 9e-05 and no seconds caps, with the escape clause FIRED for the M18 pair proof, so Phase 5 is blocked until the roadmap is revised.**

## Performance

- **Duration:** 61 min wall clock, from the 02-07 close (`cb3c39b`, 07:22 +06) to the L11 commit (`bfd5a45`, 08:22 +06). It includes the wait for the owner's Task 2 reply; the active work was shorter.
- **Started:** 2026-10-09T01:22Z
- **Completed:** 2026-10-09T02:23Z
- **Tasks:** 3 (two auto, one decision checkpoint)
- **Files modified:** 5 (plus this summary)

## Accomplishments

- The verdict was re-run on the committed records: exit 1, the designed exit for "not a pass"; the output is identical to lines 13 to 1086 of the campaign log, and a byte-equal fenced block is recorded as `### 2026-10-08-a-verdict` in `bench/RESULTS.md`.
- `02-SPIKE.md` below `## Results` answers the four questions (construction and frontier, mesh budget, pair-check falsifiability, volume estimator) plus the container, each naming run ids and RESULTS.md entries and which predictions held or failed; `## Verdict` is at line 337. Nothing above `## Results` changed, and `check-protocol` prints "protocol guard: held".
- L11 is in the decision log (line 284) with Profile, Construction, Volume estimator, Turn cap per size (table), Pair check, Known-bad inputs for THRD-04, Container, Escape clause, Conditions of the record, Inputs still UNVERIFIED / INTERIM, Reason and Reversibility (costly). Every number names its `2026-10-08-a-*` run; the seconds caps read "not established" because the grid run is non-decisive (L02).
- The escape clause is recorded as it fired: "Phase 5 is not planned until the roadmap is revised (SC5)", rule output "pair: not falsifiable for size M18 (right, left hand)", from the decisive `2026-10-08-a-pair`. It is not softened, and the M18 non-falsifiability is stated in L11, STATE.md and ROADMAP.md.
- STATE.md: the "pair-proof reliability is unmeasured" blocker is replaced by the measured result with its L11 citation; a Decisions bullet for L11 and a "Phase 5 not planned until the roadmap is revised (L11, SC5)" blocker were added. ROADMAP.md: one precondition line under Phase 5.
- SC4 holds: `src/` is unchanged against `origin/main` and `src/screw` carries no thread-building identifier.

## Owner's Task 2 answer (2026-10-09), quoted

The owner selected the option labelled "revise: Phase 5 (Recommended)" — record L11 with the escape outcome and block Phase 5 planning until the roadmap is revised; Phase 3 stays plannable. The owner named no direction for the Phase 5 revision, so L11 says the direction is to be named when Phase 5 is revised. The owner separately chose "Leave as is" for the three earlier commits with the wrong author email (`32cdeac`, `af790ea`, `cb3c39b`): they are not rewritten.

## Task Commits

1. **Task 1: Reproduce the verdict and write Results and Verdict into the protocol by citation** - `a3d72f6` (docs)
2. **Task 2: Owner accepts L11 and chooses the roadmap consequence** - decision checkpoint, no commit; answer quoted above
3. **Task 3: Commit L11 and the state and roadmap consequences** - `bfd5a45` (docs)

**Plan metadata:** the commit that adds this file, `docs(02-08): complete the verdict and decision plan`.

## Task 1 evidence

- Verdict command: exit 1 (the designed non-pass exit, not a crash).
- Diff of the re-run output against lines 13 to 1086 of `bench/results/thread-spike/2026-10-08-a-campaign.md`: empty.
- The fenced block in `bench/RESULTS.md` is byte-equal to the saved output.
- `grep -nx '## Verdict'` finds `337:## Verdict` in `02-SPIKE.md`.
- `check-protocol`: guard held.

## Task 3 evidence

- SC4 verify command, run exactly: `grep -n '^## L11' docs/architecture/decision_log.md && git diff --quiet origin/main -- src/ && { git grep -n -e helix -e Helix -e PipeShell -e left_hand -e thread_length -e Sewing -- src/screw; test $? -eq 1; }` printed `284:## L11 — ...` and exited 0.
- Commit `bfd5a45` staged exactly `docs/architecture/decision_log.md`, `.planning/STATE.md`, `.planning/ROADMAP.md`. The pre-commit hook ran `make verify` and passed.
- `make verify` after the commit: `695 passed in 33.81s`, "Required test coverage of 94.0% reached. Total coverage: 95.56%".
- `.venv/bin/python -m bench.thread_spike check-protocol` printed `protocol guard: held`, exit 0.
- Post-commit deletion check: no deleted files.

## Acceptance criteria

| Criterion | Result |
|---|---|
| Task 1: re-run verdict equals campaign log's verdict (diff empty), exit code stated in RESULTS.md | PASS (exit 1, diff empty, stated) |
| Task 1: Results subsections for the four questions and `## Verdict`, each citing run ids | PASS (`## Verdict` at 337) |
| Task 1: check-protocol still holds | PASS ("protocol guard: held") |
| Task 2: the owner's reply names one option; revise names the blocked phases | PASS (revise, Phase 5; no direction named) |
| Task 3: L11 has Profile, Construction, Volume estimator, Turn cap per size, Pair check, Known-bad inputs, Container, Escape clause, Reason, Reversibility; every number names a run id | PASS |
| Task 3: STATE.md pair-reliability blocker replaced by the measured result; revise adds the blocking line and the ROADMAP precondition line | PASS |
| Task 3: src/ unchanged in PR 2; no thread-building identifier in src/screw (SC4) | PASS |
| Task 3: `make verify` exits 0 | PASS (695 passed; the hook passed the commit) |

## Files Created/Modified

- `docs/architecture/decision_log.md` - L11, 128 lines appended
- `.planning/phases/02-thread-spike/02-SPIKE.md` - `## Results` and `## Verdict` below the boundary (Task 1)
- `bench/RESULTS.md` - `### 2026-10-08-a-verdict` (Task 1)
- `.planning/STATE.md` - L11 Decisions bullet, pair-proof blocker replaced, Phase 5 blocker added
- `.planning/ROADMAP.md` - one precondition line under Phase 5

## Decisions Made

L11 is the decision. It is the owner's, taken at the verdict checkpoint on the pre-registered rules; the values come from the rules' output and none was edited. No other decision was taken in this plan.

## Deviations from Plan

None - plan executed exactly as written.

Wording differences from the Task 1 draft of L11 (the plan allows wording, forbids numbers): the date line reads "Date: 2026-10-09." without the draft's drafting note; the Escape clause placeholder is filled with the owner's choice; one Reason line was rewrapped. In STATE.md the Decisions header's range "L01–L10" was updated to "L01–L11" so it matches the log (a one-token edit beside the L11 bullet).

## Issues Encountered

- The Task 1 executor's `gsd query commit` timed out earlier, so both commits of this plan were made with plain `git commit`; the pre-commit hook ran `make verify` each time.
- Three earlier commits carry a wrong author email (`32cdeac`, `af790ea`, `cb3c39b`, author `half@Andrews-MacBook-Pro.local`). The owner chose "Leave as is"; nothing was rewritten.
- Known-bad inputs list: the 15 (d, pitch, length) rows in L11 match the 15 naive-control rows in `### 2026-10-08-a-verdict` that read one solid, valid, with a precise ratio below 0.5 (checked against the verdict text before committing). Rows of two solids or a ratio above 1 are not in the list by the stated criterion.

## Known Stubs

None. No technical-debt or idea item was filed: no defect was found.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 3 is plannable on L11: construction, K, estimator, `T_gate`, turn caps (construction and bytes; seconds not established), and the THRD-04 known-bad inputs are locked.
- Phase 5 is not plannable: the roadmap must be revised first (via `/gsd-phase`), with a direction the owner has yet to name. The variant rules and reference-K rows in `### 2026-10-08-a-verdict` are the material for that revision.
- PR 2 closes the phase the normal way from `gsd/phase-02-thread-spike-runs`: `/gsd-verify-work 2`, `/gsd-secure-phase 2`, `/gsd-validate-phase 2`, `/gsd-ship 2`, then `make pr.land`. The phase is not marked complete here.

---
*Phase: 02-thread-spike*
*Completed: 2026-10-09*

## Self-Check: PASSED

Created files and both task commits (`a3d72f6`, `bfd5a45`) verified present on the branch; L11 heading at line 284 and `## Verdict` at line 337 found; check-protocol held.
