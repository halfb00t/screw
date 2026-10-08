# Phase 2: Thread Spike - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-06
**Phase:** 02-thread-spike
**Areas discussed:** ISO 68-1 flag, Grid: sizes, lengths, frontier; Construction bar and escape clause; Pair-check protocol; Spike home and promotion path; Landing

---

## ISO 68-1 flag (raised before the areas)

| Option | Description | Selected |
|--------|-------------|----------|
| Buy and read it before run 1 | Owner checkpoint opens the phase: hold ISO 68-1:2023, pin basic or design, then pre-register and run. SC4 met as written. | ✓ |
| I already hold it | Same order, no purchase step. | |
| Pin basic from the preview, mark UNVERIFIED | Spike runs on the basic profile; decision entry says UNVERIFIED; re-read in Phase 4. SC4 not met as written. | |

**User's choice:** Buy and read it before run 1
**Notes:** The section the spike builds depends on the profile, so the read precedes the run.

---

## Grid: sizes, lengths, frontier

| Option | Description | Selected |
|--------|-------------|----------|
| 15 sizes: first + second choice | M2…M20 plus M3.5 M7 M14 M18 (TABL-05 ships the bracketed sizes; frontier not monotone). | ✓ |
| 11 first-choice sizes | The research grid; second-choice swept in Phase 4 or never. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Every integer mm + every integer-turn length, from L=P to min(10d, 200) | Superset of any later table and of what a user can type; finds the short-length floor. | ✓ |
| ISO 4017 preview series + integer-turn lengths | Smaller; literal SC3 wording; off-series lengths unswept until Phase 7. | |
| ISO 4017 preview series only | Misses the integer-turn lengths OPER-01 names. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Step 5 turns up to 250 turns; stop per size at first failure or over 30 s INTERIM | Research's measured ceiling; per-size cap with a known margin. | ✓ |
| Fixed 2x the standard max | Bounded cost; may stop short of the frontier for small sizes. | |
| Stop at the standard max, no frontier | Does not meet SC3. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Both hands on host + one container validity-only pass of the winner | LH verified at one size only; kernel pair and sewing tolerance likeliest to differ on linux/amd64. | ✓ |
| Both hands, host only | linux/amd64 construction behaviour stays UNVERIFIED until Phase 7. | |
| Right-hand full grid, left-hand sample, host only | Cheapest. | |

**User's choice:** all four recommended options; "Next area" with no extra questions.

---

## Construction bar and escape clause

| Option | Description | Selected |
|--------|-------------|----------|
| Sewn twist on the full grid; one-pipe + cq_warehouse as reference sample; naive sweep as negative control | Research already ranked them; the negative control's silent-wrong rows feed THRD-04's gate test. | ✓ |
| All four constructions on the whole grid | Days of wall time. | |
| Sewn twist only | No measured fallback. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Sweep K in {3, 5, 10} on a size sample, then lock one K | Resolves "unproven" without 3x the grid; pre-registered pick rule. | ✓ |
| Lock K=5 from the research | Carries an unproven choice into Phase 3. | |
| Sweep K over the whole grid | 3x the campaign. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Bare rod and bare void, plus one tip-chamfer-trim row per size at the standard max | Prices Phase 4's fragile boolean without inventing head dimensions. | ✓ |
| Bare rod and bare void only | Phase 4's chamfer boolean unmeasured until Phase 7. | |
| Full bolt: head fuse + chamfer per row | Needs head rows that do not exist; invented dimension (L02). | |

| Option | Description | Selected |
|--------|-------------|----------|
| Any failure or silent-wrong row inside the standard range escapes; over-budget rows become a per-size cap, reported | A failure is a construction verdict; a slow row is a cap (SC4). Budgets are INTERIM. | ✓ |
| Any failure OR any over-budget row escapes | Escapes on spur's INTERIM 30 s. | |
| Failure only; no time or size bar | Phase 3 would ship with no turn cap. | |

**User's choice:** all four recommended options; "Next area".

---

## Pair-check protocol

| Option | Description | Selected |
|--------|-------------|----------|
| c in {0.05, 0.10, 0.15, 0.20}; c = 0 and c = -0.05 as diagnostic rows | Brackets the printed matrix; negative row is the sensitivity check. | ✓ |
| c in {0.05, 0.10, 0.15, 0.20} only | Loses the sensitivity row. | |
| c from 0.02 to 0.30 in 0.02 steps | Many hours for resolution Phase 6 will not use. | |

| Option | Description | Selected |
|--------|-------------|----------|
| 3 screw-motion matched poses + 3 half-pitch controls; all must agree | Seam-shifted identical poses; pose-dependence of a broken boolean is what is measured. | ✓ |
| 1 matched + 1 control | Research density; a seam-dependent false zero is invisible. | |
| 5 matched + 5 controls | ~1.7x the pair campaign. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Rod piece m + 2P vs cylinder blank minus the void, m per ISO 4032 preview (UNVERIFIED) | Engagement = the shipped nut's height; fastest usable variant in research. | ✓ |
| Fixed 10-turn rod piece vs the same nut blank | Engagement is not the shipped nut's. | |
| Full bolt body vs full nut | Slowest, degenerate at c=0. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Per (size, hand, c>0): all matched empty AND every control fires within a band; a size with no clean c ≥ 0.05 column escapes; mixed-hand must read violated | One flaky cell is recorded and excluded; a size with no clean column is the roadmap revision SC5 names. | ✓ |
| Majority of poses per cell | Tolerating a control that did not fire is the C4 hole. | |
| Any failing pose at any clearance anywhere escapes | Would revise the roadmap over a clearance Phase 6 may never pick. | |

**User's choice:** all four recommended options; "Next area".

---

## Spike home and promotion path

| Option | Description | Selected |
|--------|-------------|----------|
| bench/thread_spike/ package; Markdown report; exit 1 on failed verdict | Under the gate from day 1; committed and rerunnable (research scripts were lost). | ✓ |
| .planning/phases/02-thread-spike/spike/ scripts | Outside the gate; archived with the milestone. | |
| src/screw/solid/helical.py with no field | Against SC4's intent. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Protocol in 02-SPIKE.md landed before run 1; runs in bench/RESULTS.md with run ids; Results/Verdict cite run ids | bench/RESULTS.md is durable and is what the decision entry cites. | ✓ |
| Everything in bench/RESULTS.md | One long entry. | |
| Everything in 02-SPIKE.md | Archived at milestone close; the decision entry would cite a moving path. | |

| Option | Description | Selected |
|--------|-------------|----------|
| bench/quiet.py wait_quiet(bar=1.5, samples=3, interval=30 s, cap=900 s); load printed at start and end labelled by time; tested predicate | spur never ported its gate as code; Phase 7 needs it again. | ✓ |
| Manual uptime readings | Relies on discipline (spur 12-02's mislabelled reading). | |
| Gate inside each spike script | Phase 7 copies it. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Written to be moved: maths and builder split like calc/thread.py and solid/helical.py; Phase 3 moves them unchanged, spike imports them back | spur 11-05: what was measured is what ships. | ✓ |
| Throwaway; Phase 3 rewrites from the research reference | Two implementations that can differ in the proven seams. | |

**User's choice:** all four recommended options; "Done with it".

---

## Landing (raised after the areas: SC1 vs L08 squash)

| Option | Description | Selected |
|--------|-------------|----------|
| Two PRs: PR 1 = quiet gate + spike scaffold + 02-SPIKE.md protocol, landed before run 1; PR 2 = runs, RESULTS.md, verdict, decision entry | Order is in main's history; predictions reviewed before data exists. Exception to one-PR-per-phase, recorded. | ✓ |
| One PR; tag the protocol commit | Provable by tag, not visible in main's log. | |
| One PR; record the protocol commit sha in 02-SPIKE.md | Sha becomes unreachable after the squash; does not meet SC1. | |

**User's choice:** Two PRs.

---

## Claude's Discretion

Volume-estimator selection rule and tolerance band; mesh-budget sweep design; container-pass mechanics; M2–M4 nut-height source; sewing tolerance and chamfer angle as protocol inputs; `HasErrors/HasWarnings` diagnostic column; reuse of existing bench helpers and the `make bench.thread` target; run ids and report layout; sample sizes for the reference rows and the K sweep.

## Deferred Ideas

Design profile as a later option; STEP importer behaviour in other CAD; the open `blocker` debt item (collapsed thin solid) — its `/gsd-quick` PR is outside Phase 2; Phase 7 reuses `bench/quiet.py` and the Phase 2 grid as the fixed corpus.
