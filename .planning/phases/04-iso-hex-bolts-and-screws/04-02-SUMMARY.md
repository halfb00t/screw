---
phase: 04-iso-hex-bolts-and-screws
plan: 02
subsystem: calc
tags: [fine-stl-cap, left-hand, grid-records, tech-debt, d-21]

requires:
  - phase: 03-real-helical-thread
    provides: "FINE_STL_ROWS (right-hand caps), fine_stl_refusal, the 2026-10-08-a-grid run records"
provides:
  - "FINE_STL_ROWS keyed by (d, pitch, left_hand): 13 entries, M8 left-hand uncapped"
  - "fine_stl_refusal(d, pitch, length, left_hand) naming the hand and the measured quantity"
  - "a test that recomputes every cap from the committed grid records"
  - "WR-02 debt item resolved"
affects: [04-04 (caps move from length to built thread t, D-22), 04-14 (L12 correction and L13 hand-keyed cap rule)]

actuals:
  tokens: 6700
  tasks: 1
  commits: 1

tech-stack:
  added: []
  patterns:
    - "A typed measured constant is paired with a test that recomputes it from the committed bench records"

key-files:
  created:
    - docs/tech_debt/resolved/2026-10-11-fine-stl-cap-applies-right-hand-rows-to-left-hand-parts.md
  modified:
    - src/screw/calc/thread.py
    - src/screw/calc/__init__.py
    - src/screw/app.py
    - tests/test_thread_maths.py
    - tests/test_calc.py
    - tests/test_api.py
    - tests/test_cli.py
    - docs/tech_debt/INDEX.md

key-decisions:
  - "Left-hand caps are the longest measured length below the first over-budget row (72, 77, 78, 75, 91, 91 mm), not the first over-budget length the debt item listed (D-21 clarification)"
  - "M8 left-hand has no cap: the grid measured no length over budget up to 80 mm (65,776,259 bytes at L=80, under 67,108,864)"
  - "The decision log is untouched; L12's factual correction and L13's hand-keyed rule land together in plan 04-14 (D-24)"

requirements-completed: [INFO-03]

coverage:
  - id: D1
    description: "FINE_STL_ROWS keyed by (d, pitch, left_hand) with the 13 measured caps; M8 left-hand uncapped"
    requirement: INFO-03
    verification:
      - kind: unit
        ref: "tests/test_thread_maths.py#test_the_fine_stl_table_is_exactly_the_thirteen_rows_l11_measured"
        status: pass
    human_judgment: false
  - id: D2
    description: "Every cap equals the longest measured length that fits, recomputed from the 2026-10-08-a-grid records"
    requirement: INFO-03
    verification:
      - kind: unit
        ref: "tests/test_thread_maths.py#test_every_cap_is_the_longest_measured_length_that_fits_in_the_grid_records"
        status: pass
    human_judgment: false
  - id: D3
    description: "Each cap is accepted and the next float above it is refused, on both hands, with the pinned refusal text"
    requirement: INFO-03
    verification:
      - kind: unit
        ref: "tests/test_thread_maths.py#test_each_cap_is_accepted_and_the_next_float_above_is_refused"
        status: pass
    human_judgment: false
  - id: D4
    description: "Left-hand M10 x 60 is served while right-hand M10 x 60 is a 422 fine_stl_cap on the API, exit 2 on the CLI and a warning on the info document"
    requirement: INFO-03
    verification:
      - kind: integration
        ref: "tests/test_api.py#test_the_left_hand_part_l11_measured_inside_the_budget_reaches_the_backend"
        status: pass
      - kind: integration
        ref: "tests/test_cli.py#test_the_left_hand_part_l11_measured_inside_the_budget_is_not_refused"
        status: pass
      - kind: unit
        ref: "tests/test_calc.py#test_a_left_hand_part_is_judged_by_its_own_measured_cap"
        status: pass
    human_judgment: false
  - id: D5
    description: "app.py comments and the WR-02 debt item say what was measured; the item is resolved in the fixing commit"
    verification: []
    human_judgment: true
    rationale: "Comment and debt-item wording is prose; a reader judges whether it states the measured quantity correctly"

duration: 15min
completed: 2026-10-11
status: complete
---

# Phase 4 Plan 02: Hand-keyed fine-STL caps Summary

**Fine-STL caps keyed by (d, pitch, left_hand) with 13 rows proven against the committed grid records, a refusal that names the hand and the fine-STL-plus-gzip-over-64-MiB quantity, and the WR-02 debt item resolved in the same commit.**

## Performance

- **Duration:** about 15 min (start time was not recorded; estimated)
- **Completed:** 2026-10-11T14:41Z
- **Tasks:** 1
- **Files modified:** 9 (one of them renamed active -> resolved)

## Accomplishments

- `FINE_STL_ROWS` is `dict[tuple[float, float, bool], float]` with 13 entries. Right-hand M8 67.5, M10 56, M12 60, M14 58, M16 52, M18 65, M20 64 mm are unchanged. Left-hand M10 72, M12 77, M14 78, M16 75, M18 91, M20 91 mm are new. M8 left-hand has no entry.
- `test_every_cap_is_the_longest_measured_length_that_fits_in_the_grid_records` reads `bench/results/thread-spike/2026-10-08-a-grid.jsonl`, keeps built rod rows, sums the fine raw STL bytes and the gzip-1 bytes, takes the first length over 67,108,864 per key and the longest measured length below it, and requires equality with `FINE_STL_ROWS`. The executor's own pre-implementation run of the same criterion gave first-over / cap pairs M10 73/72, M12 78/77, M14 79/78, M16 76/75, M18 92/91, M20 92/91 left-hand and reproduced all seven right-hand caps. The M8 left-hand maximum is 65,776,259 bytes at L=80, under the budget. No cap is typed to match: the test fails if the records do not hold one.
- The refusal now reads `length: the fine STL of the <hand> rod with d .. and pitch .. is refused above <cap> mm (<turns> turns), the longest length L11 measured whose fine STL plus its gzip copy fit the 64 MiB export budget (run 2026-10-08-a-grid); this length is .. mm. Shorten length, or ask for the preview STL or the STEP, which are not capped`. No brace.
- Left-hand M10 x 60 is served (API reaches the backend, `download_refusal` is None, no info warning); right-hand M10 x 60 is 422 `fine_stl_cap` on the API, exit 2 on the CLI naming `length`, and an info warning ending in the refusal.
- `app.py` comments over `_EXPORTS` and in `_serve` now say the fine STL plus its gzip-1 copy exceeded the budget, give the raw 45,659,684 bytes at M8 right L=68 (so the two blobs, not the STL, were over), and say the caps are keyed by hand. No behaviour change in `app.py`.
- WR-02 debt item moved to `docs/tech_debt/resolved/` with `Status: resolved`, a `## Resolution`, and its INDEX row moved to Resolved, all in the fixing commit.

## Task Commits

1. **Task 1: Key the fine-STL caps by hand, prove them from the records, say what was measured, and retire WR-02** - `1a43cd2` (fix)

**Plan metadata:** see the docs commit that follows this file.

## TDD Gate Compliance

Plan type is `execute` with `tdd="true"` on the task and an explicit one-commit requirement (the debt item, the keying, the message and the comments are one fix; acceptance criterion: HEAD of that commit lists thread.py, app.py, the resolved item and INDEX). The cycle was run in order but landed as one commit; a separate RED commit could not pass the pre-commit `make verify` gate.

- **RED:** tests were written and run against the unchanged source with `make test PYTEST_ARGS="tests/test_thread_maths.py tests/test_calc.py tests/test_api.py tests/test_cli.py -q -n0 --no-cov"`: 24 failed, 191 passed, exit 1. The failures were the planned behaviour: `test_every_cap_is_the_longest_measured_length_that_fits_in_the_grid_records` failed on `recomputed != FINE_STL_ROWS` (13 recomputed keys against 7 stored); the left-hand tests failed on the assertion `download_refusal(left, "stl", "fine") is None` getting the right-hand M10 cap-56 refusal; the four-argument calls failed on the old three-argument signature. Semantic assessment: the target tests executed and failed for the intended reason (right-hand caps applied to left-hand parts, three-argument API), not a collection, import or fixture fault. The `gsd_run check tdd-red-evidence` classifier was not run: pytest's console output is not one of its supported report formats.
- **GREEN:** the same command passed after the change, and `make verify` passed (871 passed, coverage 96.88 percent against the 96 percent floor).
- **REFACTOR:** none.

## Files Created/Modified

- `src/screw/calc/thread.py` - 13-row hand-keyed `FINE_STL_ROWS`, rewritten block comment, `fine_stl_refusal(d, pitch, length, left_hand)` with the new text
- `src/screw/calc/__init__.py` - `_bolt` and `download_refusal` pass `p.left_hand`
- `src/screw/app.py` - comments only
- `tests/test_thread_maths.py` - 13-row typed table, the grid-records recomputation, both-hand boundary tests, left-hand/M8 cases
- `tests/test_calc.py`, `tests/test_api.py`, `tests/test_cli.py` - four-argument calls and the left-hand M10 x 60 case on each front end
- `docs/tech_debt/resolved/2026-10-11-fine-stl-cap-applies-right-hand-rows-to-left-hand-parts.md` - the WR-02 item, resolved (git mv from active/)
- `docs/tech_debt/INDEX.md` - row moved from Active to Resolved

## Decisions Made

- Left-hand caps follow the code's own convention (longest measured length below the first over-budget row), per the D-21 clarification; the debt item's 73, 78, 79, 76, 92, 92 are first-over lengths and are not caps.
- M8 left-hand is uncapped because no run measured it over budget (L02: no number the records do not hold).
- `docs/architecture/decision_log.md` is not edited; L12's measurement correction and L13's rule land together in plan 04-14 (D-24).

## Deviations from Plan

### Auto-fixed Issues

None - plan executed exactly as written, with two noted adaptations that are not rule deviations:

- The debt item's `Resolved in:` and the INDEX Resolved cell say "this commit" plus the commit subject instead of a sha, because a commit cannot contain its own sha. The sha is `1a43cd2`, recorded here.
- The CLI left-hand test asks `download_refusal` for the left-hand side (a real fine export would write a large STL), as the plan directed, and runs the real command for the right-hand side.

**Total deviations:** 0 auto-fixed.

## Issues Encountered

None. No stubs, no skipped tests, no unrun verifies, so nothing was appended to `.planning/WINDOWS.md`.

## Threat Flags

None. T-04-03 (left-hand caps) is mitigated by the recomputation test; no new endpoint, auth path or trust-boundary file access.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 04-04 can move the caps' input from `length` to the built thread `t` (D-22); the table keys and the recomputation test are the stable base.
- Plan 04-14 must land L13 (hand-keyed cap rule with these values and run ids) and the L12 factual correction with its pointer, and nothing else points at the decision log yet.
- Verification: `make verify` run before the commit, result line `871 passed`, exit 0; the pre-commit hook ran it again and passed.

## Self-Check: PASSED

- FOUND: docs/tech_debt/resolved/2026-10-11-fine-stl-cap-applies-right-hand-rows-to-left-hand-parts.md; active/ copy absent
- FOUND: commit 1a43cd2 (ancestor of HEAD); it lists thread.py, app.py, the resolved item and INDEX.md and not decision_log.md
- Acceptance greps: `(10.0, 1.5, True): 72.0`, `(20.0, 2.5, True): 91.0`, no `(8.0, 1.25, True)` key, `fine STL plus` and `64 MiB export budget` in thread.py, `fine_stl_refusal(p.d, p.pitch, p.length, p.left_hand)` count 2 in calc/__init__.py, `45,659,684` and `gzip` in the app.py comment, INDEX row only under Resolved

---
*Phase: 04-iso-hex-bolts-and-screws*
*Completed: 2026-10-11*
