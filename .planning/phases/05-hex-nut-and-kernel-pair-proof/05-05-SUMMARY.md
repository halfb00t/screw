---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 05
subsystem: nut-kind
tags: [nut, pydantic, validators, refusals, clearance, warning, kernel-evidence]
requires:
  - phase: 05-04
    provides: "NutParams with required clearance, solid/nut.py, per-kind dispatch in derive and download_refusal"
provides:
  - "NutParams._root_radius (same-name override, reads clearance), _nut_too_thin, _turn_cap on m + 2 pitch"
  - "void_root_radius_refusal, nut_too_thin_refusal, nut_turn_cap_refusal in calc/thread.py"
  - "the non-positive clearance warning on the nut's info document"
  - "kernel evidence that a positive clearance moves the nut's thread away from the axis on both hands"
  - "docs/tech_debt/active/2026-10-14-nut-fine-stl-caps-unmeasured.md"
affects: [05-06, 05-07, 05-10, 05-13, 05-14]
actuals:
  tokens: 14000
  tasks: 3
  commits: 3
plan_head_before: b0ee9e974a7d8aa5e3f6f2adcdf538639a340483
plan_head_after: 5ee04b20d0a7e7efb6b452bc6d7fab5d7c71f9bc
tech-stack:
  added: []
  patterns:
    - "a same-name model_validator on the subclass replaces the inherited rule (RESEARCH F6)"
    - "boundary tests built from the exact float: c = 5H/8 - d/2 makes the root radius exactly 0.0"
    - "a kernel direction test whose positive control is the c = 0 half, proven to bite by flipping the hand sign"
key-files:
  created:
    - docs/tech_debt/active/2026-10-14-nut-fine-stl-caps-unmeasured.md
  modified:
    - src/screw/params.py
    - src/screw/calc/thread.py
    - src/screw/calc/__init__.py
    - tests/test_nut.py
    - tests/test_calc.py
    - docs/tech_debt/INDEX.md
key-decisions:
  - "R12 decided by its own recorded condition: the probe's table does not meet it, so the else-branch applies and the nut fine-STL rule is NOT shipped; no cap, no reuse of FINE_STL_ROWS (see STOP below)"
  - "The nut's turn cap compares exact decimals of m + 2 pitch against 250 pitch, so m = 173.6 at pitch 0.7 is exactly 250 turns and accepted"
requirements-completed: []
requirements-partial:
  - id: PAIR-01
    note: "the clearance direction and its refusals ship; the diametral value on the info panel is a later plan's, so the requirement is not marked complete"
  - id: TYPE-03
    note: "the nut's model rules ship; ISO 4032 rows, e, mw, dw and chamfers are plans 05-06 to 05-13, so the requirement is not marked complete"
  - id: PAIR-03
    note: "the non-positive clearance warning ships; the pair verdict itself is later plans' (05-14)"
coverage:
  - id: D1
    description: "The nut's root-radius rule reads the clearance, with the inherited c-free rule replaced"
    requirement: PAIR-01
    verification:
      - kind: unit
        ref: "tests/test_nut.py#test_the_root_radius_rule_reads_the_clearance"
        status: pass
      - kind: unit
        ref: "tests/test_nut.py#test_the_void_root_radius_is_refused_at_exactly_zero_and_accepted_one_float_above"
        status: pass
    human_judgment: false
  - id: D2
    description: "A nut whose flats are no wider than its void is a 422 nut_too_thin on the API and exit 2 on the CLI, naming s, d and clearance"
    requirement: PAIR-01
    verification:
      - kind: unit
        ref: "tests/test_nut.py#test_a_nut_whose_flats_are_no_wider_than_its_void_is_refused_naming_three_fields"
        status: pass
      - kind: unit
        ref: "tests/test_nut.py#test_an_over_thin_nut_is_a_422_on_the_api_and_exit_2_on_the_cli"
        status: pass
    human_judgment: false
  - id: D3
    description: "The nut's turn cap judges m + 2 pitch at exactly 250 turns"
    requirement: TYPE-03
    verification:
      - kind: unit
        ref: "tests/test_nut.py#test_the_turn_cap_judges_the_void_the_builder_makes"
        status: pass
    human_judgment: false
  - id: D4
    description: "A clearance of 0 or below is warned once; 5e-324 and 0.1 carry no such warning"
    requirement: PAIR-01
    verification:
      - kind: unit
        ref: "tests/test_calc.py#test_a_nut_with_a_non_positive_clearance_warns_once_after_the_standing_warning"
        status: pass
      - kind: unit
        ref: "tests/test_calc.py#test_a_nut_with_a_positive_clearance_has_no_clearance_warning"
        status: pass
    human_judgment: false
  - id: D5
    description: "A positive clearance moves the nut's thread surfaces away from the axis on both hands, and the volume drops by the section-area difference times m"
    requirement: PAIR-01
    verification:
      - kind: unit
        ref: "tests/test_nut.py#test_a_positive_clearance_moves_the_nut_thread_away_from_the_axis_on_both_hands"
        status: pass
    human_judgment: false
  - id: D6
    description: "The nut's fine STL is capped per R12"
    requirement: TYPE-03
    verification: []
    human_judgment: true
    rationale: "STOPPED by R12's own condition: the probe's nut bytes do not support reusing the rod caps, so no nut fine-STL rule was written. The nut caps need their own measurement run; owner sign-off on shipping meanwhile is outstanding. See the STOP section and the debt item."
duration: 30min
completed: 2026-10-14
status: complete
---

# Phase 5 Plan 05: Nut refusals and clearance warning Summary

**The nut is refused at the model when its void crosses the axis, is wider than its flats, or runs past 250 turns, a clearance of 0 or below is warned out loud, and a kernel test pins that a positive clearance enlarges the thread on both hands. The nut's fine-STL cap is NOT shipped: R12's own condition sends it to a separate measurement run.**

## STOP: the nut fine-STL rule (R12) is not implemented

This is the part of the plan that did not ship, and it is a stop, not a quiet approximation.

R12 reads: reuse `FINE_STL_ROWS` on `m` if the probe's nut bytes at each cap fit the 64 MiB budget **and** cap + 1 mm does not; otherwise measure nut caps in their own run. The probe's table in `05-OWNER-READS.md` fails both halves of that condition:

| Size | At the cap | Cap + 1 mm | What it shows |
| --- | --- | --- | --- |
| M10 right | 0.956 | 0.973 | still fits one mm past the cap |
| M20 right | 0.921 | 0.936 | still fits one mm past the cap |
| M20 left | 1.003 | 1.019 | over budget at the cap itself |

The probe measured 3 of the 13 capped rows. So the else-branch applies. I did not reuse `FINE_STL_ROWS`, did not invent nut caps and did not route the nut through the bolt rule. Concretely:

- `nut_fine_stl_refusal` was not written; the plan's artifact line for it and the key link `nut_fine_stl_refusal\(` from `calc/__init__.py` are therefore unmet, on purpose.
- `download_refusal` serves every nut download. Its nut branch carries a comment stating the R12 outcome and naming the debt item. A test (`test_a_nut_download_is_never_refused_until_the_nut_fine_stl_caps_are_measured`) pins the absence and uses the rod rule on the same numbers as its control.
- The plan's own stop branch asks for a `checkpoint:human-verify` and the owner's written word before the nut keeps no cap. The orchestrator instructed me to complete everything else and return a prominent stop instead of a checkpoint, so I did. **The owner's sign-off on shipping without a nut cap is outstanding**, and the debt item says so.
- Filed `docs/tech_debt/active/2026-10-14-nut-fine-stl-caps-unmeasured.md` (Severity: must, trigger: before the nut fine STL can be offered as bounded) with its INDEX row, in the same commit as the warning (`ecc13c5`).

Threat T-05-12 (huge `m`) is therefore mitigated by the 250-turn cap on `m + 2 pitch` only; the fine-STL half of its mitigation is open. The acceptance criterion `calc/thread.py contains def nut_fine_stl_refusal(` is not met for the same reason.

## Accomplishments

- `NutParams._root_radius` replaces the inherited rule by name: `d/2 - 5H/8 + c <= 0` is `422 pitch_too_coarse` with `ctx.fields == [d, pitch, clearance]`. M2 x 2 is refused as a bolt and accepted and built as a nut at c = 0.5. With `c = 5H/8 - d/2` the sum is exactly `0.0` (refused) and one float above is accepted.
- `NutParams._nut_too_thin`: `s <= d + 2c` is `422 nut_too_thin`, fields `[s, d, clearance]`, text begins `s, d and clearance: ` and says the void is wider than the flats. `screw info nut --clearance 0.1 --s 6` exits 2 with that text.
- `NutParams._turn_cap`: judged on `m + 2 pitch`, exact decimals. m = 248, 124 and 173.6 (at pitches 1.0, 0.5, 0.7) are accepted at exactly 250 turns; one float past is `turn_cap` with fields `[m, pitch]`.
- The info document appends `clearance {c:g} is not positive: the pair cannot be proven (PAIR-03)` for c <= 0, after the standing warning; c = 0, c = -0.05 get it, c = 5e-324 and c = 0.1 do not. c = 0 and c = -0.05 still build (D-04, no lower bound added).
- Kernel evidence on both hands: a point 0.05 mm outside the nominal void surface (crest, mid flank and root) is inside the c = 0 nut and outside the c = 0.1 nut, and the volume drops by the section-area difference times m inside `T_GATE`. Flipping the hand sign fails both parametrised cases, so the c = 0 half is a working positive control.
- `make verify`: ruff, mypy --strict, import contracts, unfinished-work scan and pytest all pass. Result line: `2769 passed in 81.97s`, `Required test coverage of 96.0% reached. Total coverage: 97.45%`.

## Task Commits

1. **Task 1: the nut's three model rules** - `0aa9ff5` (feat)
2. **Task 2: non-positive clearance warning; nut fine-STL rule stopped per R12, debt filed** - `ecc13c5` (feat)
3. **Task 3: kernel evidence that a positive clearance enlarges the nut thread on both hands** - `5ee04b2` (test)

Every commit ran the pre-commit `make verify`. The trailer names the writer, `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`, not the orchestrator's suggested Opus 5.5, because Sonnet 5.5 wrote this diff.

## Files Created/Modified

- `src/screw/calc/thread.py` - `void_root_radius_refusal`, `nut_too_thin_refusal`, `nut_turn_cap_refusal`
- `src/screw/params.py` - `NutParams._root_radius`, `_nut_too_thin`, `_turn_cap`
- `src/screw/calc/__init__.py` - the non-positive clearance warning in `_nut`; the R12 comment on the nut branch of `download_refusal` (no behaviour change there)
- `tests/test_nut.py` - the model-rule tests, the API/CLI check, the both-hands kernel test; one 05-04 test case moved (below)
- `tests/test_calc.py` - the warning tests and the uncapped-download test
- `docs/tech_debt/INDEX.md`, `docs/tech_debt/active/2026-10-14-nut-fine-stl-caps-unmeasured.md`

## Decisions Made

- The plan's literal commit subjects were `feat(nut): ...` and `test(nut): ...`; the commits use `(05-05)` as the scope, as 05-04 did and the executor protocol requires.
- The refusal texts print `s` and `d + 2c` with `repr` (via the existing `_plain`), not `:g`, so a boundary refusal never reads "10 must exceed 10". The root-radius text uses `:g` like the rod's.
- No largest-accepted-pitch hint on the nut's root-radius text: the rod's hint solves for pitch at c = 0, and a version with `c` is more machinery than the rule needs.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] A 05-04 test assumed a clearance of 100000 is a 200 on a default nut**
- **Found during:** Task 1
- **Issue:** `test_a_clearance_the_model_takes_is_a_200[100000]` built a default nut (s = 10) at c = 1e5. The new thin-nut rule correctly refuses it (the void would be 200006 mm wide).
- **Fix:** the 200 cases are now 0, -0.05, 0.1 and 1.9 (the largest c under the default s is just below 2); a new assertion in the thin-nut test pins that the interim ceiling passes the field and is refused as `nut_too_thin`, not `less_than_equal`.
- **Files modified:** `tests/test_nut.py`
- **Commit:** `0aa9ff5`

**2. [Rule 3 - Blocking] E501 in two new lines**
- **Found during:** Tasks 1 and 2 commits (hook)
- **Fix:** rewrapped the comment in `params.py` and a tuple loop in `tests/test_calc.py`; each commit was retried with the same message.
- **Commit:** `0aa9ff5`, `ecc13c5`

### Plan stop, not a deviation to be tidied

**3. [R12 stop] The nut fine-STL rule was not implemented.** See the STOP section above.

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking), 1 plan-prescribed stop reached. **Impact:** one plan artifact and one key link are unmet by design; everything else is as planned.

## Issues Encountered

None beyond the lint retries. The tests that run `git` in a temp dir did not arise (none here).

## Known Stubs

None. The nut has no fine-STL cap, which is a recorded debt item with a named trigger, not a stub that reaches the UI. Nothing was added to `.planning/WINDOWS.md`.

## Threat Flags

None new. T-05-13 (clearance crossing the axis) is mitigated: refused before the kernel, tested at the exact bound. T-05-12 is half mitigated (turn cap only), as stated above.

## Things the next plans need to know

- The default nut now refuses a clearance of 2 or more through `nut_too_thin` (s = 10, d = 6). Any later test or preset that types a large clearance must also raise `s`.
- Plans that read `05-OWNER-READS.md` R12 should treat it as "separate nut run", with the debt item as the live record.
- The nut's info document warns in this order: standing warning, non-positive clearance (if any), per-row non-finite notes, the no-row warning, then download refusals. Plan 05-07 replaces the no-row warning.
- **Debt filed:** `docs/tech_debt/active/2026-10-14-nut-fine-stl-caps-unmeasured.md` (must).

## Self-Check: PASSED

- `0aa9ff5`, `ecc13c5` and `5ee04b2` are ancestors of HEAD; `git rev-list --count b0ee9e9..5ee04b2` is 3, matching `actuals.commits`.
- `src/screw/params.py` contains `def _nut_too_thin(` and, inside `class NutParams`, `def _root_radius(` and `def _turn_cap(`; `screw info nut --clearance 0.1 --s 6` exits 2 with `s, d and clearance: ` on stderr.
- `src/screw/calc/__init__.py` contains `is not positive: the pair cannot be proven (PAIR-03)`.
- `src/screw/calc/thread.py` does not contain `def nut_fine_stl_refusal(`, deliberately (R12 stop).
- `make verify` after the last commit: `2769 passed`, coverage 97.45 against the 96.00 floor.
