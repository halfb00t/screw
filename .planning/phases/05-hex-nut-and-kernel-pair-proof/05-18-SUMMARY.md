---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 18
subsystem: export, records
tags: [download-name, content-disposition, decision-log, L15, tech-debt, requirements]

requires:
  - phase: 05-hex-nut-and-kernel-pair-proof
    provides: plans 05-01 to 05-17 (the nut, the pair proof, the ends, the mesh rule) and 05-OWNER-READS.md R1 to R15
provides:
  - calc.download_name(p, fmt, quality), the one file-name rule of the API header and `screw export`
  - decision log L15, the Phase 5 entry
  - the overview, the UI contract and the requirement lines brought up to what shipped
  - two debt items (nut interim bounds, first pair.yml dispatch)
affects: [Phase 6 printed pair acceptance, Phase 7 operability re-sweep, /gsd-verify-work, /gsd-ship]

actuals:
  tokens: 18838
  tasks: 3
  commits: 3
plan_head_before: c844507b62e0988790360cf3a7f967b3c657c531
plan_head_after: 184d2547708ab8cf82d58d8d20f1cebc01643741

key-files:
  created:
    - docs/tech_debt/active/2026-10-14-nut-interim-bounds.md
    - docs/tech_debt/active/2026-10-14-first-pair-yml-dispatch.md
  modified:
    - src/screw/calc/__init__.py
    - src/screw/app.py
    - src/screw/cli.py
    - tests/test_parity.py
    - tests/test_cli.py
    - tests/test_api.py
    - docs/ideas/INDEX.md
    - docs/ideas/2026-10-12-preview-stl-download-names-its-quality.md
    - docs/architecture/decision_log.md
    - docs/architecture/overview.md
    - .planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md
    - .planning/REQUIREMENTS.md
    - docs/tech_debt/INDEX.md

key-decisions:
  - "A preview STL is saved as <slug>_preview.stl; the fine STL and the STEP keep <slug>.<ext> (D-22, R9)"
  - "The entry is L15 because L14 is the owner's GOST source decision; L14 is untouched (218 lines added, 0 removed)"
  - "The nut-interim-bounds item records that the nut has no fine-STL cap (R12 not met), and points at the existing item instead of repeating it"

requirements-completed: [FRNT-06, TYPE-03, TYPE-04, THRD-05, PAIR-01, PAIR-03, PAIR-04, INFO-01, INFO-02]

status: complete
completed: 2026-10-20
---

# Phase 5 Plan 18: The preview download names its quality, L15 and the phase's records Summary

**`calc.download_name` gives a preview STL the name `<slug>_preview.stl` on both the API header and `screw export -o <directory>`, and L15 records every Phase 5 choice with its run, owner-read line or probe, with L14 untouched.**

## Performance

- **Duration:** about 30 min of work; the start time was not captured at launch
- **Completed:** 2026-10-20
- **Tasks:** 3 of 3
- **Files:** 15 changed (421 insertions, 36 deletions) by the three task commits

## Accomplishments

- **Task 1.** `download_name(p, fmt, quality)` in `src/screw/calc/__init__.py`; `app._serve` builds `Content-Disposition` from it; `cmd_export` accepts an existing directory for `-o` (then `--format` is required, with its own error), writes `download_name` inside it, writes a file path as given, and the `wrote` line names the quality of an STL (`wrote x.stl (12 KiB, preview)`). A parity test compares the API header's name with the name the CLI writes for each registered kind, format and quality (8 cells). The preview-name idea moved to Done.
- **Task 2.** L15 appended after L14 (`git show --numstat`: 218 added, 0 removed on `decision_log.md`). It records, each with its citation: the nut kind, fields and frozen defaults; the required clearance and its bound; the nut's refusals; the counterpart; the pair proof's bodies, function, CLI, tiers, the expected table and the ubuntu reading of the verify cell; the M18 finding; the end models, labelled cited or stated model, and the oracles with `T_PIECE`; the table rows read under L14 and the owner's 2026-10-20 rulings; the panel groups; the deflection rule and the file name; owner rulings R1 to R15. The overview, the UI contract's Copywriting and the standing-warning text were brought up to what shipped.
- **Task 3.** The nine Phase 5 requirement lines now name their evidence (they were already ticked and are not re-ticked). Two debt items filed with INDEX rows.

## Task Commits

1. **Task 1: the preview download names its quality** - `9c21beb` (feat)
2. **Task 2: L15, the overview and the UI contract** - `28fc393` (docs). `git show --numstat --format= 28fc393 -- docs/architecture/decision_log.md` prints `218	0`, so L14 is unchanged.
3. **Task 3: requirement evidence and the phase's debt** - `184d254` (docs)

**Plan metadata:** the commit that adds this SUMMARY, STATE.md and ROADMAP.md. `commits: 3` is measured from the plan-start ledger (`git rev-list --count c844507..HEAD` before this summary).

## Verification

`make verify`, run after the last task commit: ruff, mypy `--strict`, import contracts and the unfinished-work scan green; pytest `3358 passed in 185.61s (0:03:05)`, total coverage 97.33 % against the 96.0 % floor. All three task commits also passed the pre-commit `make verify`. Host load was not controlled; the seconds are not comparable with R14's 101.65 s.

TDD (Task 1): the tests were written first and run before `download_name` existed: 11 failed (the 8 parity cells and 3 CLI tests), 4 passed. The implementation then turned them green; two existing tests in `tests/test_api.py` that pinned the old preview header were updated in the same commit.

## Deviations from Plan

### Where the plan text and the shipped fact disagree (the fact is recorded)

**1. The nut-interim-bounds item does not say the nut fine-STL caps reuse the rod caps.** The plan's text says "the nut fine-STL caps reuse the rod caps per R12". R12's record in `05-OWNER-READS.md` says its condition was shown on none of the sizes the probe measured, and plan 05-05 shipped no nut cap (`download_refusal` serves every nut download). The new item `2026-10-14-nut-interim-bounds.md` states that, covers the `s`, `m` and `clearance` ceilings (all `INTERIM_MAX_MM`) and the 250-turn cap, and cross-references the existing `2026-10-14-nut-fine-stl-caps-unmeasured.md` without duplicating or resolving it. The two items do not conflict.

**2. R9 was applied here, not in 05-17.** `05-OWNER-READS.md` says R9 was applied by plan 05-17; 05-17's summary records that it was not and that this plan carries it. It is applied in `9c21beb`; the `05-OWNER-READS.md` line was left as written (not this plan's file to edit).

**3. "Nut fine-STL refusal" in the UI contract.** The plan lists the nut fine-STL refusal among the strings to add. No such string exists (item 1). The Copywriting Contract has a row that says the nut has none and why, instead of a sentence a future cap might use.

**4. The `wrote` line names the quality for an STL only.** The plan says the line names the quality. A STEP has no tessellation and ignores `--quality`, so naming one there would state something false (L02). The STEP's line is unchanged.

**5. R11's "46 honest rows" against the probe's 54.** `05-OWNER-READS.md` R11 says 46 honest rows; `bench/RESULTS.md` ("End-cut probe (Phase 5, D-10)") and 05-02's summary say 54. The recorded maximum (2.737e-03) is the same in both, so `T_PIECE = 0.03` is unaffected. L15 states both counts and cites both files. Not resolved here.

### Process

**6. ROADMAP.md and STATE.md are updated in the final metadata commit, not in Task 3's.** The `roadmap update-plan-progress` and `state` handlers read the SUMMARY on disk, so they run after this file exists. Task 3's commit holds the requirement evidence and the debt; the verify command in the plan (debt files and INDEX rows) passes on it.

**7. The idea's INDEX row names the plan, not a commit hash.** A commit cannot cite its own hash; the row reads "Phase 5, D-22 and R9 (plan 05-18)".

**8. REQUIREMENTS.md.** All nine lines were already `[x]` and `Complete` in the traceability table (earlier plans). They did not name their evidence; each now does, as a trailing note. PAIR-04's note says the first ubuntu run of the full grid is not recorded and points at the debt item. The statuses were not changed.

**9. Commit trailer.** The commits end with `Co-Authored-By: Claude Opus 5.5`, as the orchestrator's brief required, although this executor is Sonnet 5.5 and the harness reminder names that. (Plans 05-02 and 05-04 record the same conflict.)

### Auto-fixed Issues

**10. [Rule 3 - Blocking] The first Task 1 commit attempt failed the hook on lint.** E501 on the `Content-Disposition` line in `app.py` and four ARG005 on an unused-argument lambda in the new parity test. Fixed (a local `name`, a `*_` stub) and recommitted; nothing was committed by the failed attempt.

**11. [Rule 1 - Existing tests superseded by the plan's own behaviour]** Two tests in `tests/test_api.py` (`test_model_download`, `test_a_left_hand_bolt_downloads_under_its_own_filename_and_is_not_the_right_hand_mesh`) pinned `<slug>.stl` for a preview STL; they now pin `<slug>_preview.stl`. Commit `9c21beb`.

**Total deviations:** 2 auto-fixed, 5 where the shipped fact differs from the plan text, 4 process notes. **Impact:** none on scope; the records follow the SUMMARYs and the owner record.

## Authentication Gates

None.

## Known Stubs

None. No file changed by this plan holds a stub, placeholder or unfinished marker.

## Threat Flags

None new. T-05-40 holds: the name is `slug()` (letters, digits and `_.+-`) plus the fixed `_preview`, quoted; `test_the_download_filename_is_safe_for_many_digit_values` still passes. T-05-41 is accepted as the plan says: `-o <directory>` writes one file named by `download_name` inside the directory the user typed. T-05-42 is mitigated: every L15 value names a run, an owner-read line, a probe or a plan summary.

## Filed this plan

- `docs/tech_debt/active/2026-10-14-nut-interim-bounds.md` (must; trigger: Phase 7 OPER-02, OPER-03)
- `docs/tech_debt/active/2026-10-14-first-pair-yml-dispatch.md` (must; trigger: the Phase 5 PR's merge)
- Moved to Done: `docs/ideas/2026-10-12-preview-stl-download-names-its-quality.md`
- Not filed, for the owner: the owner's sign-off on shipping the nut with no fine-STL cap (05-05) is still outstanding; it is written in the existing item and in L15.

## Next Phase Readiness

Plan 05-18 is the last plan of Phase 5. Landing goes through `/gsd-verify-work` and `/gsd-ship`. After the PR merges, dispatch `pair.yml` once and record the ubuntu grid (`2026-10-14-first-pair-yml-dispatch.md`); the CI job time (`2026-10-20-ci-test-job-tripled-by-two-pair-tests.md`) names phase close as its trigger.

## Self-Check: PASSED

- FOUND: `src/screw/calc/__init__.py` (`def download_name(`), `src/screw/app.py` (`download_name(`, no `filename="{params.slug()}.{fmt}"`), `docs/architecture/decision_log.md` (`## L15`), both debt files, their INDEX rows, the idea under `## Done`.
- FOUND commits `9c21beb`, `28fc393`, `184d254` (ancestors of HEAD).
- L14 unchanged: `git show --numstat --format= 28fc393 -- docs/architecture/decision_log.md` prints `218	0`.
- `make verify`: `3358 passed`, coverage 97.33 %.
