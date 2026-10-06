---
phase: 02-thread-spike
plan: 01
subsystem: testing
tags: [thread-spike, iso-68-1, pre-registration, owner-checkpoint, protocol]

requires:
  - phase: 01-walking-skeleton
    provides: bench harness conventions and the STATE.md blocker line this plan closes
provides:
  - 02-SPIKE.md protocol file with Question, Owner rulings and the stub Results boundary
  - ISO 68-1:2023 profile pin (basic) with the owner-confirmed coefficients and rulings R0-R5
  - STATE.md ISO 68-1 blocker closed; ISO 4753 half kept
affects: [02-02 section maths, 02-03 grid and record layout, 02-05 pair rules and NUT_HEIGHT, 02-06 protocol write-up, 02-07 campaign, 02-08 verdict]

actuals:
  tokens: 1900
  tasks: 2
  commits: 1
plan_head_before: 8ac5256c71406744192d683f1e6b620abb90f7b0
plan_head_after: df710d991d88daf7dcfb36a1efbeb5d884bd011a

tech-stack:
  added: []
  patterns:
    - "Pre-registered protocol file: everything above the ## Results heading is frozen on main before run 1"

key-files:
  created:
    - .planning/phases/02-thread-spike/02-SPIKE.md
  modified:
    - .planning/STATE.md

key-decisions:
  - "Profile pinned to basic (ISO 68-1:2023 basic profile, flat crest and root) by the owner; one-way door, a later change re-runs the whole campaign (D-01)"
  - "Coefficients H = (sqrt(3)/2)*P, crest flat P/8 at d/2, root flat P/4 at d/2 - 5H/8, flanks 60 degrees recorded as owner-confirmed (owner read the standard, gave no correction)"
  - "R0 not applicable; R1-R5 are the planner defaults exactly as written in the plan; the pre-registered values stand with no owner objection"
  - "M7 nut height is 0.8*d = 5.60 as a stated input, UNVERIFIED, because the owner supplied no value"

patterns-established:
  - "Owner checkpoint replies are quoted verbatim in the protocol and in the SUMMARY, with any prior recommendation disclosed (T-02-01)"

requirements-completed: [INFR-03]

coverage:
  - id: D1
    description: "02-SPIKE.md exists with ## Question, ## Owner rulings (D-01 checkpoint, 2026-10-06) and an exact ## Results line, in that order"
    requirement: INFR-03
    verification:
      - kind: other
        ref: "grep -n '^## ' .planning/phases/02-thread-spike/02-SPIKE.md; grep -nx '## Results' .planning/phases/02-thread-spike/02-SPIKE.md"
        status: pass
    human_judgment: false
  - id: D2
    description: "STATE.md ISO 68-1 blocker line replaced with the closure note; the ISO 4753 half kept"
    requirement: INFR-03
    verification:
      - kind: other
        ref: "grep -n 'ISO 68-1:2023 read by the owner' .planning/STATE.md; grep -n 'ISO 4753 (bolt ends, THRD-05)' .planning/STATE.md"
        status: pass
    human_judgment: false
  - id: D3
    description: "Owner pin and R1-R5 rulings recorded faithfully, with no ruling or ISO value added that the owner did not give"
    requirement: INFR-03
    verification: []
    human_judgment: true
    rationale: "Faithfulness of a recorded human ruling and the UNVERIFIED labels is a judgment call; no test asserts it"

duration: 4min
completed: 2026-10-06
status: complete
---

# Phase 2 Plan 01: Owner ISO 68-1 checkpoint Summary

**Basic ISO 68-1:2023 profile pinned by the owner (read 2026-10-06), coefficients owner-confirmed, rulings R0-R5 on file in the pre-registered 02-SPIKE.md protocol before any spike code exists.**

## Performance

- **Duration:** about 4 min for this continuation executor (the owner's decision wait is excluded)
- **Started:** not recorded for the continuation executor; the first executor returned at the Task 1 checkpoint with no edit and no commit
- **Completed:** 2026-10-06T11:49Z
- **Tasks:** 2 (Task 1 resolved by the owner's reply, Task 2 committed)
- **Files modified:** 2 (plus this SUMMARY)

## Accomplishments

- `02-SPIKE.md` created: the four spike questions, the Owner rulings section (pin, read date, coefficients, R0 to R5, pre-registered values), and the `## Results` boundary line with "No run yet."
- STATE.md Blockers/Concerns: ISO 68-1 line closed, ISO 4753 line kept, no other line touched by this plan.
- Every nut-height value carries its source label and the word UNVERIFIED; no clause text from the standard was copied (T-02-02).

## Task Commits

1. **Task 1: Owner reads ISO 68-1:2023, pins the profile and rules on R0-R5 (D-01)** - no commit (`checkpoint:decision`, resolved by the owner's reply below)
2. **Task 2: Write the owner's pin and rulings into the protocol file and close the STATE line** - `df710d9` (docs)

**Plan metadata:** recorded in the commit that follows this file (docs: complete plan)

## Owner's Task 1 reply (verbatim, T-02-01)

Before the owner ruled, the orchestrator recommended `basic, defaults`. Its reasons: the four spike questions do not depend on root shape; basic is the only profile with evidence (closed form 576/576 within 7.6e-6); design adds an unmeasured root radius, a numeric integral and R0 before any row exists; amending D-14 before run 1 would tune the verdict toward a pass; m is a label, not a verdict input. The owner had first asked "what do you suggest?". The owner then replied in two messages.

Message 1 (the ruling):

> basic, defaults

Message 2, answering "the date you read ISO 68-1:2023 (today is 2026-10-06) — reply `today` or a date":

> today

Interpretation recorded: profile pin basic; ISO 68-1:2023 read by the owner on 2026-10-06; coefficients confirmed as presented, no correction given (stated plainly, no stronger claim); R0 not applicable; R1-R5 the planner defaults as written in the plan's Task 1 context; pre-registered values stand, no objection raised.

## Files Created/Modified

- `.planning/phases/02-thread-spike/02-SPIKE.md` - the pre-registered protocol file (Question, Owner rulings, stub Results)
- `.planning/STATE.md` - ISO 68-1 blocker line closed (this commit also carried the orchestrator's pending tracking edits to the same file, as the continuation instructions directed)

## Decisions Made

- Profile pinned basic by the owner; the design profile stays a deferred option (CONTEXT Deferred Ideas).
- R1 to R5 taken as the planner defaults; D-14 is not amended.
- M7 = 0.8 * d = 5.60 as a stated input, UNVERIFIED.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. Verification: `make verify` ran in the pre-commit hook and reported Passed; the plan's three greps matched; `git log -1 --format=%s` for `df710d9` reads the plan's exact commit subject.

## Known Stubs

None. The `## Results` section of `02-SPIKE.md` reads "No run yet." by design (the run-guard boundary); plan 02-06 writes everything between Owner rulings and that heading, and plans 02-07 and 02-08 fill Results.

## Threat Flags

None. No network endpoint, auth path or schema change was introduced.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02-02 can read the Owner rulings section and code `section_radius` and `section_area` for the basic profile.
- Open item for later plans: M7 nut height and all of R5 stay UNVERIFIED until Phase 5 reads ISO 4032:2023.
- No tech-debt or idea item filed by this plan.

## Self-Check: PASSED

- FOUND: `.planning/phases/02-thread-spike/02-SPIKE.md`
- FOUND: commit `df710d9` (one commit between plan_head_before and plan_head_after, measured with `git rev-list --count`)
- FOUND: STATE.md line "ISO 68-1:2023 read by the owner" and "ISO 4753 (bolt ends, THRD-05)"

---
*Phase: 02-thread-spike*
*Completed: 2026-10-06*
