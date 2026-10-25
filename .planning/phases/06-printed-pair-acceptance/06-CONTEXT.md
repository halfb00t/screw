# Phase 6: Printed Pair Acceptance - Context

**Gathered:** 2026-10-22
**Status:** Ready for planning

<domain>
## Phase Boundary

The owner prints a pre-registered test, M6–M12 product bolts and nuts across a clearance ladder,
and records pass or bind for every sample. From that record the phase sets three things:

- the nut's first and only `clearance` default, one absolute-millimetre value cited in a new `Lxx`
  (PAIR-02);
- a printability threshold, two constants (`d` and pitch) from a second pre-registered run on
  M3–M5, with a warning below it on the UI, API and CLI (INFO-04);
- the PAIR-06 verdict: a nominal printed bolt into a bought nut. If it binds, PAIR-07 `undersize` is
  promoted to v1.x in REQUIREMENTS.md; otherwise the record says it is not needed.

The phase closes when the owner prints a fresh pair through the shipped default path and the two
parts thread together by hand (PAIR-05, SC3).

Not in this phase:
- the release itself, and removing the "not a product build" standing warning (both wait for
  Phase 7's measured bounds, D-15);
- the bolt-side `undersize` field (PAIR-07, only promoted here, never built);
- print-hint text (INFO-06, trigger fired, deferred);
- any runtime bound (Phase 7).

Roadmap wording resolved by this discussion (planner: build to this, not to the loose text):
- SC5 "cap-and-warn printability warning": below the threshold nothing can be trimmed without
  changing a `d` or pitch the user set (L02). So the part builds, every number stays, and a warning is
  added. Nothing is capped (D-13).
- SC2 "set once from the recorded result": the record sets the value by the rule pre-registered in
  D-07. The owner's 0.1 mm is a prediction, never an input (D-01).

</domain>

<decisions>
## Implementation Decisions

### The owner's 0.1 mm
- **D-01:** The owner's 0.1 mm enters the phase as the pre-registered **prediction** for the default,
  written into the method before the first print. The ladder is centred on it. The default is whatever
  the D-07 rule reads from the record, so it is 0.1 only if the record says so. PAIR-02 stands as
  written: no default from a guess, forum or vendor figure.

### Test matrix and pass rule (pre-registered before the first print)
- **D-02:** Test parts are **product parts**: per size, ISO 4017 screws at a short standard length,
  built to nominal; ISO 4032 nuts at each clearance step. Every STL comes from the product's own
  `screw export` at the fine mesh, so the test checks exactly what a user downloads. No coupons.
- **D-03:** Clearance ladder **0.05, 0.10, 0.15, 0.20, 0.25 mm** (five steps). The 0.05 floor is the
  smallest clearance the fine mesh was sized against (L15 D-21: worst deviation 0.0161 mm against a
  0.025 mm bound). The ladder must not go below it without re-measuring the mesh.
- **D-04:** Sizes **M6, M8, M10, M12** (coarse pitch), **3 samples** per cell: 60 nuts, 12 bolts.
- **D-05:** Pass rule per sample: the printed nut turns **by fingers** from first engagement to the
  bolt's head and back off, with no tool and no stripped or shaved thread. Anything else is **bind**,
  recorded with where it stopped (turns). A loose fit still passes and is noted `loose`.
- **D-06:** **One fixed print profile** for every part in the phase: one printer, 0.4 mm nozzle, one
  material, one layer height, axis vertical (nut on its face, bolt head-down). The owner types the
  printer, material, layer height and slicer profile into the pre-registration. The default holds for
  those conditions, and the `Lxx` entry says so.

### The default from the record
- **D-07:** Rule: the default is the **smallest step where 3/3 samples pass at all four sizes, and
  every larger step on the ladder also passes at all four sizes**. — **Reversibility:** one-way —
  L02: once a default ships, every shareable link that omits `clearance` means that value forever.
- **D-08:** Escape clause: if no step passes everywhere, or the record is not monotone (a smaller
  step passes where a larger one binds at the same size), **no default ships**. The record is kept as
  written. Claude stops and brings the owner options (extend the ladder above 0.25, a reprint rule
  pre-registered in a second run, a profile change). `clearance` stays required (L15 D-01) until a
  second pre-registered run sets it. No reprint is allowed inside the first run.
- **D-09:** The default is one value for every size (L02, SC2). A nut whose size is outside M6–M12
  gets the same default plus an info-document **warning**: the default clearance was measured on
  M6–M12 only (cite the `Lxx`). The warning is on the UI, API and CLI, and every number stays.

### Printability threshold
- **D-10:** The threshold comes from a **second pre-registered run**, after the default is set. It
  prints M3, M4 and M5 coarse pairs at the default, 3 samples each (9 bolts, 9 nuts), under the D-05
  pass rule and the D-06 profile. The threshold is the smallest size where it and every larger tested
  size pass 3/3. If M5 fails, the threshold is M6 from the main matrix.
- **D-11:** Two constants from that run: `d_min` and `P_min`, the `d` and coarse pitch of the
  threshold size. A part **warns when `pitch < P_min` or `d < d_min`**, and the warning names the edge
  crossed and the run that set it. So M12 × 0.5 warns on pitch, and M3 × 0.5 warns on both.
- **D-12:** Sizes below M3 (M2, M2.5) are never printed. They are below `d_min` by construction and
  warn.
- **D-13:** Below the threshold a part **builds and every number stays**; it is never a `422`. The
  warning goes on **both** the bolt and the nut info documents, on the UI, API and CLI, citing the
  constants' `Lxx` and run.

### PAIR-06: printed bolt into a bought nut
- **D-14:** The matrix's printed nominal bolts (same profile) are run into store-bought steel ISO
  4032 / DIN 934 nuts at **M6, M8, M10 and M12, 3 samples each**, under the D-05 pass rule. PAIR-07
  is promoted to a v1.x requirement if **any size binds in 2 or more of its 3 samples**. Otherwise the
  record says it is not needed. This threshold is pre-registered with the method.
- **Superseded 2026-10-22 by owner ruling R9** ("drop PAIR-06", option Defer + strip): PAIR-06 and PAIR-07
  move to v2, and D-14, the bought nuts and the bought-nut record are dropped from Phase 6 before any print.
  D-14 is kept here as the decision it was.

### Release scope and acceptance
- **D-15:** Phase 6 does not release. The "not a product build" clause in the standing warning
  (`src/screw/calc/__init__.py`) **stays**. The triggers of three debt items say "Phase 6 release"
  and are rewritten to "before the first release (after Phase 7)" in this phase's docs commit. None is
  resolved here:
  - `docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md`
  - `docs/tech_debt/active/2026-10-21-fillet-ring-can-overhang-the-head-flats.md`
  - `docs/tech_debt/active/2026-10-21-screw-pair-exit-codes-collide-with-failure-exits.md`
- **D-16:** SC3's acceptance is a **separate print after the default is in the code**. The owner
  prints one fresh **M8** pair through the shipped default path:
  1. the M8 bolt preset;
  2. the bolt's Matching nut link, with the clearance field left empty so the default applies;
  3. both parts exported.

  The kernel pair verdict for that nut must read `proven` before the print. The parts must thread
  together by hand under D-05. Matrix samples do not count toward SC3.

### Claude's Discretion
- The record format the owner fills in, where the pre-registration and the records live, the run ids,
  and how the result is pinned (follow the 02-SPIKE / `bench/results/` pattern: method committed
  first, record pinned by sha256).
- The short ISO 4017 length per size, and the print order.
- The exact warning texts for D-09 and D-13, following the existing `warnings` style in
  `src/screw/calc/__init__.py`.
- D-09's warning fires on size, whether or not `clearance` was typed: an omitted field and a typed
  value equal to the default can't be told apart in a link (L02).
- How the UI field shows the default. It follows the existing default-field behaviour. The parity
  test's one-required-field rule (L15 D-01) is removed when `clearance` gets its default.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and requirements
- `.planning/ROADMAP.md` § "Phase 6: Printed Pair Acceptance": goal and SC1–SC5.
- `.planning/REQUIREMENTS.md`: PAIR-02, PAIR-05, PAIR-06, INFO-04 (this phase); PAIR-07 (promoted or
  not by D-14); INFO-06 (trigger fired, deferred).
- `.planning/PROJECT.md` § Key Decisions and "Pre-registered measurement": method, predictions and
  escape clause committed before the first run.

### Locked decisions
- `docs/architecture/decision_log.md` L02: no number is better than a wrong number; defaults are
  absolute mm and never move; cap and warn, or refuse.
- `docs/architecture/decision_log.md` L11: the pre-registration and escape-clause pattern; M18 pair
  proof `inconclusive`.
- `docs/architecture/decision_log.md` L15: the required `clearance` (D-01), the nut model refusals
  (`pitch_too_coarse`, `nut_too_thin`), the pair proof, the D-21 fine-mesh rule that sets the 0.05 mm
  ladder floor.
- `docs/architecture/decision_log.md` L16: nut fine-STL caps (clearance ≤ 5.0 mm).

### Prior phase context
- `.planning/phases/05-hex-nut-and-kernel-pair-proof/05-CONTEXT.md`: D-01 (no default until Phase 6),
  D-21 (mesh vs smallest printed clearance), the deferred list naming Phase 6.
- `.planning/phases/02-thread-spike/02-SPIKE.md`: the house pre-registration format to copy.
- `.planning/research/SUMMARY.md` and `.planning/research/PITFALLS.md` C5, C8 and the
  "Pitch too fine for the nozzle" table: priors only (0.10–0.20 mm band, M5/M6 floor), never a value.

### Evidence
- `tests/data/pair_expected.tsv`: the recorded K = 3 verdicts. M8 at 0.05–0.20 mm is `proven` on
  both hands. **0.25 mm is not in the recorded grid**: if D-07 lands on 0.25, D-16's `proven` needs a
  fresh kernel run.
- `bench/RESULTS.md` "Mesh deviation (Phase 5, D-21)": worst 0.0161 mm against the 0.025 mm bound.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/screw/params.py` `NutParams.clearance` (`_req(...)`, line 186): becomes a field with the
  measured default. Its refusals (`void_root_radius_refusal`, `nut_too_thin_refusal`) are unchanged.
- `src/screw/calc/__init__.py` `warnings` list (`STANDING_WARNING` first, then the appended reasons):
  where the D-09 and D-13 warnings go, kernel-free.
- `screw export` / `screw pair nut` (`src/screw/cli.py`): generate the test STLs and the D-16 kernel
  verdict.
- `bench/results/` and `bench/RESULTS.md`: the home and format for a recorded run.

### Established Patterns
- Pre-registered runs: method, predictions and escape clause committed before the first run, the
  record pinned by sha256, every constant citing its run in a decision entry (L11, L15, L16).
- Warnings are strings in the info document on all three front ends. The registry parity test
  (`tests/test_parity.py`) keeps the UI, API and CLI aligned.
- `tests/test_parity.py` special-cases the one required field (`clearance`, lines 385–388), and that
  special case goes when the default lands.

### Integration Points
- `src/screw/params.py` (the default), `src/screw/calc/__init__.py` (both warnings), a new constants
  home for `d_min`, `P_min` and the default's source, `docs/architecture/decision_log.md` (the new
  `Lxx`), `.planning/REQUIREMENTS.md` (PAIR-02/05/06, INFO-04 evidence; PAIR-07 promotion or not).

</code_context>

<specifics>
## Specific Ideas

- The owner predicts a default of 0.1 mm (D-01).
- The acceptance pair is M8, built through the preset and Matching nut link with the clearance empty
  (D-16).

</specifics>

<deferred>
## Deferred Ideas

- **INFO-06 print hints** (orientation, layer height vs pitch): the trigger "the first printed test
  recorded" fires in this phase. Placing it is a roadmap call, not built here.
- **A bought bolt into the printed nuts at each step**: informative, but not in PAIR-06. Raised in
  discussion and not taken.
- **A second print profile or layer height** (research P5's two heights): one fixed profile in v1
  (D-06).
- **Removing "not a product build" and settling the three release debt items**: at the first release,
  after Phase 7 (D-15).

</deferred>

---

*Phase: 06-printed-pair-acceptance*
*Context gathered: 2026-10-22*
