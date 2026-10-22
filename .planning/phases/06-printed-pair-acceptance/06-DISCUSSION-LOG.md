# Phase 6: Printed Pair Acceptance - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-22
**Phase:** 06-printed-pair-acceptance
**Areas discussed:** Test matrix and pass rule, Default from the results, Printability threshold,
Bought nut + release scope

---

## The owner's 0.1 mm

The owner added "default clearance value 0.1" to the area selection. Claude pointed out the conflict:
PAIR-02 says the default comes from a recorded printed test, never a guess. 0.1 mm is the bottom of
the research's forum band. L02 freezes a shipped default forever.

| Option | Description | Selected |
|--------|-------------|----------|
| Prediction | Pre-register 0.1 as the predicted default; the ladder is centred on it; the record sets the value | ✓ |
| Your print history | 0.1 from earlier prints on this printer; the test confirms it is the smallest passing step | |
| Ship 0.1 now | Default now; supersede PAIR-02 and SC2 with a new Lxx | |

**User's choice:** Prediction.

---

## Test matrix and pass rule

| Question | Options | Selected |
|----------|---------|----------|
| Test parts | Product parts / Short coupons / Mixed | Product parts |
| Ladder | 0.05–0.25 step 0.05 / 0.05–0.20 step 0.05 / 0.00–0.30 step 0.05 | 0.05–0.25 step 0.05 |
| Sizes and samples | M6–M12 × 3 / × 2 / × 1 | M6–M12 × 3 |
| Pass rule | Full run by fingers / Full engagement only / Pass, bind, loose graded | Full run by fingers |
| Print settings | One fixed profile / Two layer heights / Tell you the setup | One fixed profile |

---

## Default from the results

| Question | Options | Selected |
|----------|---------|----------|
| Rule | Smallest all-pass step / All-pass + one step / 2 of 3 samples | Smallest all-pass step |
| Escape | Stop, no default / Pre-registered reprint / Per-size fallback | Stop, no default |
| Off-matrix sizes | Warn, keep value / Silent / Required off-matrix | Warn, keep value |

---

## Printability threshold

| Question | Options | Selected |
|----------|---------|----------|
| Below M6 | Second run M3–M5 / M6 by construction / Ladder includes M4/M5 | Second run M3–M5 |
| Axis | Pitch and d / Pitch only / d only | Pitch and d |
| Below it | Build + warn, both kinds / Warn on the nut only / Refuse with 422 | Build + warn, both kinds |

---

## Bought nut + release scope

| Question | Options | Selected |
|----------|---------|----------|
| Bought nut | M6–M12 × 3 / One size only / Plus bought bolt | M6–M12 × 3 |
| Release | Retarget to Phase 7 / Drop warning in 6 / Triage debt in 6 | Retarget to Phase 7 |
| Acceptance | Separate print after the default is in the code (M8) / Matrix counts / Separate, all 4 sizes | Separate print after the default is in the code (M8) |

---

## Claude's Discretion

- Record format and location, run ids, sha256 pinning
- Bolt length per size and print order
- Warning texts
- The off-matrix warning fires on size alone
- How the UI field shows the default

## Deferred Ideas

- INFO-06 print hints (trigger fired)
- A bought bolt into the printed nuts
- A second print profile
- The release and the "not a product build" removal (after Phase 7)
