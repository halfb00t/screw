---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 19
subsystem: bench, security
tags: [nut, fine-stl, export-budget, t-05-12, r16, pre-registered-run, stop-condition]

requires:
  - phase: 05-hex-nut-and-kernel-pair-proof
    provides: R12 (measure the nut caps in their own run), 05-SECURITY.md T-05-12 open, L11/L13 rod method
provides:
  - R16 in 05-OWNER-READS.md (owner's literal answer option-a, C = 5.0 mm, refuse above C)
  - bench/nut_fine_caps.py, the pre-registered rule and instrument (committed before any row ran)
  - bench/results/phase-05/nut-fine-caps.jsonl, the run's records (1238 lines)
  - the RESULTS.md entry "Nut fine-STL caps (Phase 5, R16)" with the 30 measured caps and the stop
affects: [05-19 Task 3 (not run), T-05-12 / T-05-10 (still open), Phase 5 close, Phase 7 re-sweep]

actuals:
  tokens: 52000
  tasks: 1
  commits: 2
plan_head_before: 1efb765d4ceea6576bca847bf3ef44eeb1159caf
plan_head_after: 837b0bc777c55c98060287d72aa3c68e49048629

key-files:
  created:
    - bench/nut_fine_caps.py
    - bench/results/phase-05/nut-fine-caps.jsonl
  modified:
    - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-OWNER-READS.md
    - tests/test_bench.py
    - bench/RESULTS.md

key-decisions:
  - "R16 (owner, 2026-10-20): option-a. C = 5.0 mm; a fine STL above C on a measured key is refused, naming clearance"
  - "The run met a pre-registered stop condition (46 failed check rows), so no cap ships and Task 3 did not run"

requirements-completed: []

status: stopped
completed: 2026-10-20
---

# Phase 5 Plan 19: The nut's fine-STL cap, stopped at the record Summary

**The pre-registered run measured all 30 nut caps (ISO 262 coarse by both hands, C = 5 mm, s = 1e5 mm) and every ladder row built, but 46 of 150 check rows were refused by the shipped lead-in countersink piece gate, which is a stop condition of the rule, so no cap ships and the plan stops after Task 2.**

## Status

Task 1 (checkpoint:decision) was answered by the owner before this run (`option-a`) and is recorded
as R16. Task 2 is complete: instrument, run and record. **Task 3 did not run** (its precondition,
"the records' end line lists no stop condition", is false). `src/` is untouched: T-05-12 and T-05-10
are still open, and `download_refusal`'s nut branch still returns None. 05-SECURITY.md was not edited.
ROADMAP.md and REQUIREMENTS.md were not advanced: the plan is not complete and TYPE-03 is not newly
satisfied by it.

## Performance

- **Run wall time:** 3011.1 s in the process (`time -p`: real 3012.79 s, user 12894.22 s, sys 1334.18 s), against the 7000 s deadline; exit 0.
- **Host load:** load1 9.89 at 2026-10-20T16:43:05+00:00 before, 9.46 at 2026-10-20T17:33:16+00:00 after (shared host; the run's own meshing included in the second). The rule reads bytes, never time.
- **Commits:** 2 task commits (`0c349a7` Commit A, `837b0bc` Commit B), plus this summary's docs commit.

## Accomplishments

- R16 recorded with the owner's literal answer and the R12 follow-up.
- `bench/nut_fine_caps.py` committed with THE RULE, the ladder, C, s, the checks and the stop conditions before any row ran (HEAD `0c349a7`), with 11 tests whose names contain `nut_fine_caps`.
- One run (`2026-10-20-nut-fine-caps`), 1236 rows: 1086 ladder rows, all built; 150 check rows, 104 built and fit, 46 failed.
- Pre-registration order proven: the records commit descends from the instrument commit and `bench/nut_fine_caps.py` is byte-identical between them (the plan's verify command printed `pre-registered`).

## Task Commits

1. **Task 2, Commit A (pre-registration):** `0c349a7` - feat(05-19): add the nut fine-STL cap run with its rule fixed before any row
2. **Task 2, Commit B (record):** `837b0bc` - docs(05-19): record the nut fine-STL cap run

Records: `bench/results/phase-05/nut-fine-caps.jsonl`, 1238 lines, sha256 `8682c7023253c1320ba6645fd72021e9122bec16c232c9a4064b7219eba92ade`.

## The 30 measured caps (m in mm, the largest whole mm that fits 64 MiB)

| Size | M2 | M2.5 | M3 | M3.5 | M4 | M5 | M6 | M7 | M8 | M10 | M12 | M14 | M16 | M18 | M20 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| right | 12 | 13 | 15 | 18 | 21 | 24 | 30 | 30 | 38 | 36 | 41 | 46 | 45 | 54 | 36 |
| left | 15 | 17 | 19 | 22 | 25 | 30 | 38 | 38 | 47 | 50 | 56 | 61 | 59 | 73 | 47 |

Every cap row fits at 0.954 to 0.995 of 64 MiB; cap + 1 is over by 0.03 to 5.8 %. No cap is below a
GOST ISO 4032-2014 `m_max` (the nearest: M20 right, 36 against 18 mm, 2.0 times). The planner's M20
estimate was 37 to 39 mm; the measured M20 right cap is 36 and M20 left is 47.

## The stop

All 46 failed rows carry one error: `BuildError: Geometry kernel produced the wrong lead-in countersink`
(the D-10 / R11 piece gate, 0.03 of the piece). They are the check rows at m = cap and s = 1e5 at
clearance -0.05 (16 of 30 keys), 0 (15) and 0.1 (15). The C/2 check (clearance 2.5, s = 1e5) and the
slimmest-s check (clearance 5, s = d + 11) built and fit on all 30 keys (largest sum 0.960). The 104
built checks sit at 0.291 to 0.960 of 64 MiB. No check was over budget.

**Diagnostic probe, not a record, not committed** (scratch only, after the record commit, run once,
not part of the rule): `export(NutParams(..., clearance=0.1), "step")` at M2 right m 12, M8 right m 38
and M14 right m 46, s = 1e5, 1e4, 1e3, 100, 30. The gate failed at s = 1e5 for all three and at 1e4 for
M2 only; every s of 1e3 or below built. The failing M2, M8 and M14 piece volumes at s = 1e5 reproduced
the run's numbers digit for digit (0.363281, 9.86292 and 66.6958 mm^3), so the failure is deterministic
and depends on s. That matches a precision limit of a volume-difference gate at the model's largest s
(hexagon volume about 8.7e9 mm^3 per mm of m against pieces of 0.1 to 150 mm^3), but that cause is a
reading, not a measurement. Whatever the cause, a nut at s = 1e5 and a small clearance is refused by the
shipped build with a message that names no field the user set.

## Decisions for the owner (the plan's stop, L02; nothing below is decided)

1. **Re-run under an amended rule, new run id (recommended).** The rule treats a check the shipped
   build refuses as a stop. Amend it, by your ruling and before any row of the new run: a check row the
   build refuses is recorded as "not a file" and is not a stop; the cap is judged on the checks that
   built. The instrument's amendment clause already requires a new run id and a docstring note. Cost:
   about 50 minutes; the bytes are deterministic, so the caps should repeat. This keeps T-05-47 intact
   (rule fixed before rows).
2. **Ratify the existing records.** You rule that the 30 caps stand and the 46 refused checks are not a
   stop, and Task 3 proceeds from this run. Faster, but the rule then changes after the data was seen,
   and the record would say so (T-05-47 weakened, not broken, because you decide).
3. **Fix or bound the gate at huge s first.** A nut with s = 1e5 and c = 0.1 cannot be built today.
   Either lower the nut's s ceiling (an `INTERIM_MAX_MM` decision for `s`) or make the piece gate
   precise at large s, then re-run with the original rule. Slowest; it also repairs a user-reachable
   BuildError. It could be filed as its own debt item whichever option is taken.

Whichever is chosen, Task 3 (the encoded refusal, tests, debt move, L16 and the UI row) is unchanged
and still needs the plan's precondition: a record whose end line lists no stop condition.

## Deviations from Plan

None in the rule, ladder, constants or checks. Notes, not deviations:

- The plan's interface line gives `gzip1(data) -> (bytes, seconds)`; it returns `(compressed size, seconds)`. The instrument uses it as it is.
- The first launch of the run command failed in the shell (zsh `time -p` inside a subshell, `command not found: -p`) before Python started: no row ran, no records file existed. The second launch used `/usr/bin/time -p` and is the run. This is disclosed in the RESULTS.md entry.
- The plan's verify line uses `make test PYTEST_ARGS=...`; the 11 tests were run with `.venv/bin/python -m pytest tests/test_bench.py -q -n0 --no-cov -k nut_fine_caps` (11 passed), and again in `make verify`.
- Two measured facts differ from the plan's predictions and are asserted as measured: M20 right cap 36 (planner estimate 37 to 39) and 46 failed check rows (the plan expected the checks to fit).

## Verification

- `make verify` after commit B: `======================= 3369 passed in 181.87s (0:03:01) =======================` (ruff, mypy `--strict`, import contracts, the unfinished-work scan, pytest; also run by the pre-commit hook on both commits).
- Records check, header and end line, 30 measured keys, 1238 lines: printed `records ok 1238`.
- sha256 present in RESULTS.md (`grep -c` printed 1); pre-registration check printed `pre-registered`.

## Known Stubs

None.

## Threat Flags

None new. T-05-12, T-05-10, T-05-45 to T-05-48 remain as the plan registers them; the missing
mitigation (the refusal in `download_refusal`) is not in code. The one new observation is the gate
failure at s = 1e5 above, which is not a new surface (it refuses, it does not serve a wrong number).

## Tech debt

No item filed or resolved. The gate-at-huge-s observation is awaiting the owner's choice among the three
options (option 3 would file it); the nut-fine-STL-caps item stays active.

## Self-Check: PASSED

- FOUND: bench/nut_fine_caps.py
- FOUND: bench/results/phase-05/nut-fine-caps.jsonl (1238 lines)
- FOUND: 0c349a7 and 837b0bc as ancestors of HEAD
- FOUND: R16 in 05-OWNER-READS.md; the RESULTS.md entry (one heading)
