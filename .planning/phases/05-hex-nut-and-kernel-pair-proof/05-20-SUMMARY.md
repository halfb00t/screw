---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 20
subsystem: nut solid, pair rule, pair proof, tech debt
tags: [code-review, gap-closure, wr-01, wr-02, wr-03, wr-04, wr-05, wr-06, in-01, t-05-52, t-05-53, t-05-54, t-05-55, t-05-56, t-05-57, t-05-58]

requires:
  - phase: 05-hex-nut-and-kernel-pair-proof
    provides: 05-REVIEW.md and its disposition (open 10 of 10), the pair rule and proof (05-14), the nut ends (05-11 to 05-13), the expected table (05-01)
provides:
  - a face-chamfer cutter whose overshoot is min(0.5, (s / 2) tan 30 deg / 2) mm, so a nut narrower than sqrt(3) mm across flats builds
  - negated tolerance comparisons in the pair rule and a finite-volume refusal at the proof's reading boundary
  - calc.pair.cell_judgement (the rule plus the closed form it compared) and an honest PairReport.closed_control
  - a d / 2 short-circuit in prove (inconclusive by definition, nothing read, no closed form printed)
  - engagement_turns as turns_of(m, pitch) and an evidence bolt that takes the nut's own s off an ISO 4017 row
  - the L15 "Review fixes" paragraph, an IN-01 erratum in L15 and R3, four tech-debt items and 05-REVIEW-DISPOSITION.md at open 0
affects: [05-SECURITY.md re-audit (T-05-52 to T-05-58), Phase 5 re-review and close, Phase 6 release (IN-02, IN-03), Phase 7 re-sweep]

actuals:
  tokens: 14800
  tasks: 4
  commits: 10
plan_head_before: 9180beed8532a0331684d4ff01f19e927738c351
plan_head_after: 88cb31dc8b5da5b89ed773fc4e03266760315178

tech-stack:
  added: []
  patterns:
    - "a non-finite number is refused where it is read (_finite in solid/pair.py), mirroring the spike's _num"
    - "the rule returns what it compared (cell_judgement); the report copies it and never recomputes"
    - "a tolerance comparison is a negated <= so NaN falls outside"

key-files:
  created:
    - docs/tech_debt/active/2026-10-21-fillet-ring-can-overhang-the-head-flats.md
    - docs/tech_debt/active/2026-10-21-screw-pair-exit-codes-collide-with-failure-exits.md
    - docs/tech_debt/active/2026-10-21-brittle-pair-and-cli-tests.md
    - docs/tech_debt/active/2026-10-21-nut-countersink-cutter-crosses-the-axis-at-a-coarse-pitch.md
  modified:
    - src/screw/solid/nut.py
    - src/screw/calc/pair.py
    - src/screw/solid/pair.py
    - src/screw/calc/thread.py
    - tests/test_nut.py
    - tests/test_pair.py
    - tests/test_cli_pair.py
    - tests/test_end_oracles.py
    - docs/architecture/decision_log.md
    - docs/tech_debt/INDEX.md
    - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-OWNER-READS.md
    - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-REVIEW-DISPOSITION.md

key-decisions:
  - "WR-01: build every accepted s by capping the cutter's overshoot; the model gained no floor on s"
  - "WR-02: guard at two boundaries (negated comparisons in the rule, finite refusal in prove) and leave the rule's clauses alone; a planted matched NaN stays violated as 02-SPIKE Rules is written"
  - "WR-03: the rule returns the closed form it used; prove prints that and nothing else"
  - "WR-04: at c >= d / 2 prove reads nothing and is inconclusive by definition; the D-05 blank does not grow"
  - "WR-06: off a row the evidence bolt takes the nut's own s and the bolt's frozen k"

requirements-completed: [TYPE-03, THRD-05, PAIR-03, PAIR-04]

duration: 48min
completed: 2026-10-21
status: complete
---

# Phase 05 Plan 20: Fix the Phase 5 code review warnings Summary

**Six review warnings and one info fixed at the boundary where each starts, each with a test that failed before its fix: a nut under sqrt(3) mm across flats builds, no NaN can make the pair rule say `proven`, the report prints only a closed form the rule compared, and the 240 recorded verdicts re-derive byte for byte.**

## Performance

- **Duration:** about 48 min (measured from the plan commit 9180bee at 12:48 to this SUMMARY, +0600)
- **Started:** 2026-10-21T06:50Z
- **Completed:** 2026-10-21T07:38Z
- **Tasks:** 4
- **Files modified:** 16 (4 created, 12 modified)

## Accomplishments

- **WR-01.** `face_chamfer` named its overshoot `min(0.5, r0 * tan 30 deg / 2)`. The fixed 0.5 mm put the first profile point at `s/2 - 0.866` mm, negative below sqrt(3) mm. RED run: `NutParams(d=1, pitch=0.25, m=1, clearance=0.05)` at s 1.5, 1.7 and 1.11, both hands, all raised `Standard_Failure`. After the fix all six build inside T_GATE. From s = 2 sqrt(3) mm up the cutter reaches exactly 0.5 mm below the face (tested at s 3.5, 4 and 10).
- **WR-02.** Both tolerance comparisons in `cell_judgement` are negated `<=` (the `volume_check` pattern). RED run: the nan nut body and the nan control at each of three poses read `proven`. `prove` now refuses a non-finite kernel volume where it reads one (the blank, each boolean, each evidence pose) via `_finite`, so a NaN at a matched pose read through `prove` is `inconclusive` (a `cell failure`), never `violated` or `proven`. A NaN planted straight into the rule at a matched pose is `violated`, as the written rule says (a NaN is not empty, 02-SPIKE Rules); the rule's clauses and their order did not change.
- **WR-03.** `cell_judgement(record)` returns the verdict, the reasons and the closed form it judged the controls against, or `None` where it ended first. `cell_verdict` returns the first two. `PairReport.closed_control` is that value and its docstring states the rule.
- **WR-04.** At a clearance of d / 2 or more `prove` reads nothing and returns `inconclusive` by definition. `screw pair nut --d 6 --pitch 1 --s 20 --clearance 3.5` exits 2 with a report whose first reason begins `d and clearance: ` and whose `closed_control`, `readings` and `shipped` are empty or null. The blank stays radius d (D-05).
- **WR-05.** `engagement_turns` is `turns_of(m, pitch)`: m 5.4 at pitch 0.6 reads 9.0 (it read 9.000000000000002).
- **WR-06.** Off an ISO 4017 row the evidence bolt takes the nut's own s and the bolt's frozen k. The off-row M12 x 1.5 nut (s 19, m 10, c 0.1) now builds a real bolt through the kernel and gets three `built` readings with no error (before: three failures, "s 10 mm must exceed the diameter d 12 mm"). On a row nothing changes (M10 keeps 16.0 / 6.4).
- **IN-01.** The countersink comment says the smallest `da_max / d` is 1.079 at M14; a test pins it and the largest (1.16 at M2.5) against `iso4032.NUTS`; L15 and R3 carry the erratum.
- **Debt and disposition.** IN-02, IN-03, IN-04 and the planner's countersink-cutter defect are filed; `05-REVIEW-DISPOSITION.md` reads 7 fixed with shas, 3 deferred with debt paths, `open: 0`.

## Task Commits

1. **Task 1 (WR-01):** `4edaf3e` fix(05-20): build a nut narrower than sqrt(3) mm across flats
2. **Task 2, commit 2 (WR-02):** `fcdc0ab` fix(05-20): never believe a pair reading or nut body that is not finite
3. **Task 2, commit 3 (WR-03):** `4aa0126` fix(05-20): print the control's closed form only where the rule compared it
4. **Task 2, commit 4 (WR-04):** `0db1b73` fix(05-20): read nothing when the proof body cannot hold the void
5. **Task 3, commit 5 (WR-05):** `946e730` fix(05-20): report the pair's engagement as the exact quotient
6. **Task 3, commit 6 (WR-06):** `83e5b77` fix(05-20): give an off-row nut's evidence bolt the nut's own s
7. **Task 3, commit 7 (IN-01):** `4218e54` docs(05-20): correct the smallest da_max / d the countersink factor cites
8. **Task 4, commit 8 (L15):** `e06c90f` docs(05-20): record the phase 5 review fixes in L15
9. **Task 4, commit 9 (debt):** `42b6811` docs(05-20): file review findings IN-02 to IN-04 and the countersink cutter defect as debt
10. **Task 4, commit 10 (disposition):** `88cb31d` docs(05-20): record the phase 5 review dispositions

Every commit ran the pre-commit `make verify` and carries the `Co-Authored-By: Claude Sonnet 5.5` trailer (checked over the ten with `git rev-list -10 HEAD`: `trailers ok`).

## Evidence

- **Final `make verify`** (exit 0, run on the tree at `88cb31d`): `3460 passed in 151.76s (0:02:31)`, after ruff, mypy, the import contracts and the unfinished-work scan passed.
- **Task 1 preview-STL sha256** (`solid.export(p, "stl", "preview")`), identical before and after the cutter change:

  | Nut | sha256 | bytes |
  |---|---|---|
  | `NutParams(clearance=0.1)` | `755e9cc75ae2e07dcb28657d6a793dd7f8decb52700df9d26965099be40c0048` | 335484 |
  | `NutParams(d=2.0, pitch=0.4, s=4.0, m=1.6, clearance=0.1)` (GOST ISO 4032-2014 M2) | `866188a973eb19d52517cdd875e4b841fa0f660cc7254e6768660bf25c2d38d8` | 153284 |

- **The 240-cell re-derivation** (`bench.pair_expected.render(derive()) == tests/data/pair_expected.tsv`):
  - before commit 2: identical (`table identical`);
  - before commit 3: identical;
  - before commit 4: identical;
  - on the final tree: `test_the_expected_verdicts_are_re_derived_from_the_recorded_pair_campaign` passed inside `make verify`.

  `git diff ad09d46 -- tests/data/pair_expected.tsv` is empty. The table was never edited and no cell was reclassified.
- **NaN-token grep** `grep -lE 'NaN|Infinity' bench/results/thread-spike/2026-10-08-a-pair.jsonl bench/results/phase-05/pair-*.jsonl`: printed nothing (exit 1) before commits 2, 3 and 4.
- **RED runs** (each in its fix's own commit): WR-01 6 failed (`Standard_Failure`); WR-02 10 failed (nan rows read `proven`, the boundary tests saw no refusal); WR-03 `AttributeError: no attribute 'cell_judgement'` and the report test; WR-04 5 failed (the CLI and `prove` tried the real bodies); WR-05 `9.000000000000002 == 9.0`; WR-06 `s 10 mm must exceed the diameter d 12 mm` and `bolt.s == 10.0`; IN-01 `'1.079' in comment`.
- **Filed debt** (all dated 2026-10-21, INDEX rows in commit `42b6811`):
  - `docs/tech_debt/active/2026-10-21-fillet-ring-can-overhang-the-head-flats.md` (must, IN-02)
  - `docs/tech_debt/active/2026-10-21-screw-pair-exit-codes-collide-with-failure-exits.md` (must, IN-03)
  - `docs/tech_debt/active/2026-10-21-brittle-pair-and-cli-tests.md` (nice, IN-04)
  - `docs/tech_debt/active/2026-10-21-nut-countersink-cutter-crosses-the-axis-at-a-coarse-pitch.md` (must, the planner's finding)
- **Final disposition counts:** 7 `fixed` with shas, 3 `deferred` with debt paths, `open: 0`, `total: 10`.

## Files Created/Modified

- `src/screw/solid/nut.py` - `face_chamfer` overshoot capped at half `r0 tan 30 deg`, comment cites the failing s values
- `src/screw/calc/pair.py` - negated comparisons, `cell_judgement`, `cell_verdict` as its first two elements
- `src/screw/solid/pair.py` - `_finite`, `cell_judgement` in `prove`, the d / 2 branch, `turns_of`, the evidence bolt's `s`
- `src/screw/calc/thread.py` - the countersink-factor comment (1.079 at M14)
- `tests/test_nut.py`, `tests/test_pair.py`, `tests/test_cli_pair.py`, `tests/test_end_oracles.py` - the behaviour tests of each fix
- `docs/architecture/decision_log.md` - the L15 "Review fixes" paragraph and the IN-01 erratum
- `.planning/phases/05-hex-nut-and-kernel-pair-proof/05-OWNER-READS.md` - the R3 erratum
- `docs/tech_debt/INDEX.md` and the four new items under `docs/tech_debt/active/`
- `.planning/phases/05-hex-nut-and-kernel-pair-proof/05-REVIEW-DISPOSITION.md` - every finding's outcome

## Decisions Made

The plan's decisions were followed as written; the record of each is the L15 "Review fixes (plan 05-20, 05-REVIEW.md)" paragraph. In short: WR-01 builds every accepted s and adds no refusal; WR-02 guards the rule and the reading boundary and leaves a planted matched NaN as `violated`; WR-03 makes the behaviour match the docstring; WR-04 reads nothing at c >= d / 2 and does not grow the blank; WR-06 gives the evidence bolt the nut's own s off a row. No `make pair` re-run was needed: no grid cell has a non-finite reading or a clearance of d / 2 or more, and `closed_control` is not a verdict input.

## Deviations from Plan

None - plan executed exactly as written. Two cosmetic adjustments inside the plan's own steps:

- the `COUNTERSINK_FACE_FACTOR` comment was re-wrapped so `the smallest is 1.079, at M14` sits on one line, because the plan's own verify `grep` reads it as one line;
- two ruff `E501` / `I001` findings in code the plan edited (a 103-column line in `prove`'s return and the test import order) were fixed before the commit, and the first attempt at commit 5 was refused by the hook for the first of them and re-committed after the fix. No commit was made with `--no-verify`.

## Issues Encountered

- The planted matched NaN is `violated` at the rule, not `inconclusive`, and that is deliberate: 02-SPIKE Rules defines empty as 0 solids or |volume| <= 1e-6, so a NaN reading is non-empty, and reclassifying it would amend the pre-registered rule, which needs an owner ruling. The product never hands the rule one: `prove` turns a non-finite kernel volume into a `cell failure`, which is `inconclusive`. Both are tested.
- `.venv/bin/mypy` and `.venv/bin/ruff` have shebangs that point at a moved checkout path; `.venv/bin/python -m mypy` and `-m ruff` (what `make` runs) work. Nothing in the repo was changed for this.

## Known Stubs

None.

## Threat Flags

None. No new endpoint, auth path, file access or schema surface; the plan's register (T-05-52 to T-05-59) covers every change.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The orchestrator can re-run the code review and the security re-audit (`05-SECURITY.md` was not edited here): T-05-52 to T-05-58 each have a test that failed before its fix.
- Open items that block nothing in Phase 5: IN-03 (pair exit codes) and IN-02 (fillet ring) are `must` debt with a Phase 6 release trigger; the countersink-cutter defect is `must` debt tied to the root-radius floor item.

## Self-Check: PASSED

- All 17 files named above (four created, twelve modified, this SUMMARY) exist: 17 of 17 `FOUND`.
- All ten commits are ancestors of HEAD (`git merge-base --is-ancestor`): 10 of 10 `FOUND`.

---
*Phase: 05-hex-nut-and-kernel-pair-proof*
*Completed: 2026-10-21*
