# The nut's lead-in countersink piece gate refuses a valid nut at huge s and small clearance

Severity: must
Status: active
Date: 2026-10-21
Source: plan 05-19, Task 2, the run `2026-10-20-nut-fine-caps` (46 refused check rows) and ruling R17 in `.planning/phases/05-hex-nut-and-kernel-pair-proof/05-OWNER-READS.md`
Related files:
- src/screw/solid/__init__.py (the piece gate that raises `BuildError: Geometry kernel produced the wrong ...`, line 150)
- src/screw/params.py (`NutParams.s`, bounded only by `INTERIM_MAX_MM`)
- bench/RESULTS.md ("Nut fine-STL caps (Phase 5, R16)": the 46 refused rows)
- bench/results/phase-05/nut-fine-caps.jsonl (the rows, with their errors)

## Context
A nut at the model's largest s (1e5 mm) and a small clearance (-0.05, 0 or 0.1) is accepted by the
parameter model and then refused by the shipped build: `BuildError: Geometry kernel produced the
wrong lead-in countersink: the lead-in countersink is X mm3 where its oracle says Y mm3, relative
error ..., allowed 0.03 of the piece (D-10, R11)`. The run recorded 46 such rows out of 150 check
rows, at m = the key's fine-STL cap, on 16 (clearance -0.05), 15 (0) and 15 (0.1) of the 30 ISO 262
coarse keys. The 1086 ladder rows at clearance 5 mm all built, so the gate is not tripped by m or by
the preset alone.

A scratch reading, not a record and not committed (one session, after the run): M2 right m 12, M8
right m 38 and M14 right m 46 at clearance 0.1, with s = 1e5, 1e4, 1e3, 100 and 30. The gate refused
all three at s = 1e5 and M2 at 1e4 too; every s of 1e3 or below built. The refused piece volumes at
s = 1e5 reproduced the run's digit for digit (0.363281, 9.86292 and 66.6958 mm3), so the refusal is
deterministic and depends on s. A plausible cause is the precision of a volume difference at that s
(the hexagon is about 8.7e9 mm3 per mm of m, the pieces 0.1 to 150 mm3); that is a reading, not a
measurement.

The user-visible effect is a 422 `build_error` on the API (an error exit on the CLI): the tool
refuses and never serves a wrong part, which is the L02 direction. But the refusal names no field the
user set, and the model admits a part it cannot build.

## Why it matters
The nut's s ceiling (1e5, `INTERIM_MAX_MM`) is a figure Phase 1 measured on a plain cylinder, and the
gate shows that a nut well below it already fails for a reason the user cannot act on. Any claim that
the nut builds across its admitted range is false at the top of s.

## Next step
Revisit before the nut's s ceiling is relied on, or at the Phase 7 operability re-sweep (OPER-02):
find the s at which the gate starts to refuse for each key, then either make the piece gate precise at
large s or lower the nut's s ceiling to a measured value, and make the refusal name `s`.
