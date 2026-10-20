---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 09
subsystem: calc
tags: [calc, info-panel, thread-maths, limits, pair, m18]
requires:
  - phase: 05-08
    provides: "pitch_diameter, basic_minor_diameter, BOLT_LIMITS and NUT_LIMITS (derived 6g and 6H limits)"
  - phase: 05-07
    provides: "the nut info document (Thread, Nut, Pair, Part groups) and NutParams"
provides:
  - "calc/__init__.py LIMITS heading, M18_KEY, M18_NOTE; bolt pitch_diameter row; nut thread_depth, pitch_diameter, minor_diameter rows; the nut's eight Pair rows in fixed order"
  - "calc/presets.py LIMITS_SOURCE, bolt_limits_for, nut_limits_for (exact ISO 262 lookup)"
  - "calc/thread.py FLANK_ANGLE, flank_normal_gap, axial_play"
affects: [05-10, 05-11]
actuals:
  tokens: 30000
  tasks: 3
  commits: 3
plan_head_before: 9b8160f376a1e3f64b230589f6b4fe9ae5ae32c8
plan_head_after: 89d720fb5ca53b49cf1933202ac50eb374d5fcf1
tech-stack:
  added: []
  patterns:
    - "the limits group is spliced after the last Thread/Shank row (the `after` map), so it is one contiguous heading, and depends on (d, pitch) alone: an ISO 262 size that is no catalogue row still carries it"
    - "a gap factor is derived from the flank angle and pinned by a numeric derivative of section_radius, never a retyped 0.5 or 1.1547"
key-files:
  created: []
  modified:
    - src/screw/calc/__init__.py
    - src/screw/calc/presets.py
    - src/screw/calc/thread.py
    - tests/test_calc.py
    - tests/test_thread_maths.py
    - tests/test_api.py
    - tests/test_parity.py
key-decisions:
  - "The limits and the nominal d2/D2/D1 are separate sources: the nominal rows cite the ISO 68-1:2023 basic profile (the formula), the limits rows cite the two GOST texts they are derived from; no label names ISO 724:2023 or ISO 965-2:2024"
  - "The M18 note keys on (d, pitch) alone, so it is also on a nut that matches no catalogue row; PartInfo.notes description updated to say so"
  - "Bolt shank cited rows (b, lg,max, ls,min) now follow pitch_diameter, so pitch_diameter sits right after minor_diameter on every bolt"
requirements-completed: [INFO-01, INFO-02, PAIR-01]
requirements-partial:
  - id: PAIR-03
    note: "the c <= 0 warning and the pair numbers exist; the kernel verdict and its control are later plans"
status: complete
---

# Phase 5 Plan 09: The info panel's pitch and minor diameters, the bought-part limits, the pair rows and the M18 label Summary

The bolt and nut panels now print the nominal d2, D2 and D1 from the ISO 68-1:2023 basic profile, the 6g and 6H limits under INFO-02's heading on an exact ISO 262 size, the nut's eight Pair rows in fixed order, and the M18 pair-proof label from the cited record. Every number is kernel-free.

## Task commits

| Task | Commit | Message |
| ---- | ------ | ------- |
| 1 | cd6fa2b | feat(info): show the pitch diameter and the bought-part limits on an exact size |
| 2 | 167a6b1 | feat(nut): report the pair's closed-form gaps, nut diameters and engagement |
| 3 | 89d720f | feat(nut): label M18's pair proof inconclusive from the recorded campaign |

## What was built

**Task 1.** Bolt: `pitch_diameter` row after `minor_diameter` (`Pitch diameter d2 (ISO 68-1:2023 basic profile)`). Nut Thread group: `d, pitch, thread_depth, pitch_diameter (D2), minor_diameter (D1)`. `bolt_limits_for` and `nut_limits_for` look up the exact ISO 262 (d, pitch) and the 05-08 limits row, else `[]`; four rows each (6g: major max/min, pitch max/min; 6H: minor min/max, pitch min/max), label `<sense> (derived: GOST 24705-2004 (ISO 724:1993, MOD) + GOST 16093-2004 (based on ISO 965-1:1998 and ISO 965-3:1998))`, value the stored decimal-sum float. Tested for all 15 ISO 262 sizes on both kinds, for hand, clearance and catalogue independence, one float either side of M6 (`nextafter(6.0)`, `nextafter(1.0)`, 6.0001, pitch 0.9: no group, no empty heading, no-row warning present), and for the ASCII heading on the API and the CLI.

**Task 2.** `FLANK_ANGLE = pi/6`; `flank_normal_gap(c) = c sin(30 deg)`; `axial_play(c) = 2 c tan(30 deg)`. The nut's Pair group is `clearance, clearance_diametral, flank_gap, axial_play, nut_major_diameter, nut_pitch_diameter, nut_minor_diameter, engagement_turns` (unit `turns`, `turns_of` exact quotient). Tests differentiate `section_radius` by central difference on both flanks (|dr/dz| = sqrt(3) to 1e-9), derive the angle from the slope and compare the gaps to that, check the radial shift by c at 64 angles, and cover c = 0 (zero gaps and the warning) and c = -0.05 (negative gaps, reported).

**Task 3.** `M18_KEY = (18.0, 2.5)`, `M18_NOTE = "kernel pair proof inconclusive at K = 3 (2026-10-08-a-pair)"`, appended to the nut's notes (after the grade note on the M18 row) exactly once for every hand and clearance in the plan, absent at `nextafter(18.0)`, pitch 2.0 and pitch `nextafter(2.5)`, absent on the bolt, and present with no `cadquery` in `sys.modules` (fresh `-I` subprocess).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Existing tests superseded by the plan's own behaviour]** Phase 4 and 05-07 tests pinned the old row lists and one asserted `pitch diameter` was NOT a row (`test_the_derived_rows_name_the_profile_and_the_hand_is_not_a_row`); the nut-row-reads-back and grade-note tests pinned `notes` without the M18 note. All updated to the new documented behaviour in the task commits (`tests/test_calc.py`, `tests/test_api.py`).

**2. [Rule 2 - Doc accuracy]** The `PartInfo.notes` field description said notes are "present only on an exact match", which the M18 note (keyed on the size alone, per D-20) makes untrue for a nut; the description now says so.

No other deviation; no architectural change.

## Known Stubs

None.

## Threat Flags

None. Static lookups and pure functions; no endpoint, auth path or file access. T-05-20 (limits off a row) is mitigated by the exact-equality lookup with boundary tests one float either side; T-05-21 (retyped factors) by the numeric-derivative pin.

## Issues Encountered

M7 shares pitch 1.0 with M6 but is a distinct ISO 262 size (d 7.0), so the lookup keys on d and pitch together. Nothing deferred. No tech-debt or idea item filed.

## Verification

`make verify`: ruff, mypy `--strict`, import-boundary contracts, unfinished-work scan, pytest; final result line `2938 passed in 93.49s`, coverage 97.94% (floor 96%). Each task commit also passed the pre-commit `make verify` hook. `.venv/bin/screw info bolt` prints the INFO-02 heading and `Pitch diameter d2 (ISO 68-1:2023 basic profile)`; `.venv/bin/screw info nut --clearance 0.1` lists the eight Pair keys in order.

## Self-Check: PASSED

Files found: `src/screw/calc/__init__.py`, `src/screw/calc/presets.py`, `src/screw/calc/thread.py`, `tests/test_calc.py`, `tests/test_thread_maths.py`. Commits found on HEAD: cd6fa2b, 167a6b1, 89d720f.
