# Phase 8: Pre-release Gap Closure - Context

**Gathered:** 2026-11-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Close the gaps the v1.0 milestone audit found (`.planning/v1.0-MILESTONE-AUDIT.md`) so the first
release ships with OPER-03 met:

1. No part admitted inside the L25 walls ends in a kernel `422 build_error`: it builds, is refused
   before the kernel with a `422` naming its fields (`ctx.fields`), or is capped and warned. The
   in-wall debt (`docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md`) is
   resolved, and its cases are tests.
2. INT-01: the CLI build's lack of a deadline becomes a logged owner decision.
3. INT-02: TABL-06's wording is amended to agree with L19.
4. INT-03: a value typed equal to its default gets the same answer on the web, the API and the CLI.
5. Bookkeeping: INFO-05 is added to a Phase 4 SUMMARY `requirements-completed`;
   `/gsd-validate-phase 6` and `/gsd-validate-phase 7` leave both VALIDATION.md files
   `validated`; the re-run milestone audit reads `passed` or `tech_debt`.

New capabilities are out of scope. The audit's info findings INT-04 and INT-05 are not gaps to close
here. INT-06 is a wording fix, made when the in-wall debt is resolved.

</domain>

<decisions>
## Implementation Decisions

### In-wall fix route (OPER-03, SC1)
- **D-01:** Use both the kernel fix (the debt's "option 2") and a kernel-free guard. Option 2 raises
  the sweep's accuracy: MakePipeShell approximation tolerance to 1e-6 and
  `helical.SECTION_SAMPLES` from 14 to 56. The guard refuses whatever option 2 leaves. Both land in
  this phase. — **Reversibility:** costly — the sweep change moves build time, STEP bytes and the
  cost points of every part above the threshold. Undoing it means reverting the re-swept envelope
  too.
- **D-02:** The higher accuracy applies only above a d / pitch threshold, not everywhere. Parts at or
  below the threshold keep today's sweep. Their timeouts (L24), budgets (L21 B-01, L32) and cost
  points stay as measured and frozen (L33).
- **D-03:** The threshold is per kind, read from data:
  - The nut threshold is at or below 7, so the d 2.2 mm, d / pitch 7 island is covered. This puts
    the M20 nut rows (d / pitch 8) on the fine sweep. The researcher checks that their STEP and
    every other artifact stay under B-01.
  - The bolt threshold is read from the bolt refusals. It goes above 8 if the data allows, so no
    bolt catalogue row changes. iso4017:M20x200 would be 22.9 MB of STEP on the fine sweep, over
    B-01's 9.7 MB.
  - If the data forces the bolt threshold to or below a catalogue row's d / pitch, stop and ask the
    owner.
- **D-04:** Prove everything on linux/amd64 on the runner, through operability.yml's
  `workflow_dispatch`, by hand. L33 removed the CI measurement, so these runs are started by hand,
  as Runs I and II were. Local macOS runs are for development only. They are not the evidence.
- **D-05:** Re-sweep only the parts above the thresholds, also by hand on the runner. Widen the
  fitted envelope, or add a feature, so the cost model predicts those parts honestly. There is no
  full re-sweep. The values for parts below the thresholds do not move.
- **D-06:** The guard limits built turns per d band. It is a kernel-free `422` in
  `calc/thread.py`, beside `pitch_too_fine_refusal`, that names `d`, `pitch` and `thread_length` in
  `ctx.fields`. Per-band ceilings are read from what option 2 leaves after the runner re-read. The
  error type name is the planner's choice, following `pitch_too_fine`. If no refusal is left in a
  band, that band gets no ceiling.
- **D-07:** Proof bar: a named grid, with the residual logged. These become tests, and every one
  either builds or is refused before the kernel:
  - the debt's 20 parts;
  - the d 2.2, d / pitch 7 nut island (forms base, s4 and m1, both hands);
  - the long-thread bolt bands (d 0.5 to 0.85 and 1.6 to 3.3 mm, including d 3, pitch 0.35, 25 mm
    thread, right hand);
  - a stated denser nut grid that includes d / pitch 7.

  A new `Lxx` records that cells off the grid are unproven: isolated failures at a seam cannot be
  bounded by a grid (debug E32). There is no catch-all that turns a post-build `BuildError` into a
  field `422`.
- **D-08:** Log the outcome as a new `Lxx` that supersedes L25 where it moves the walls or adds the
  guard. Resolve the debt in the same commit as the fix, and correct its "names no field" wording
  (INT-06). Mark OPER-03 complete in `.planning/REQUIREMENTS.md` only when SC1 holds.

### CLI build deadline (INT-01, SC2)
- **D-09:** `screw export` stays unbounded by design. Log a new `Lxx` with this reason:
  - `BUILD_TIMEOUT_S` (L24) protects a shared server's workers, and it was measured on the runner
    with every worker busy.
  - A CLI user's machine has a different speed, so a runner deadline would refuse parts that would
    finish.
  - The cost gate still refuses over-budget parts on the CLI (exit 2), and Ctrl-C is the user's
    deadline.

  Add one line to the README or the CLI docs, and to the `export` help text if it fits. There is no
  child process and no `--timeout` flag.

### head_chamfer badge (INT-02, SC3)
- **D-10:** Amend TABL-06 to agree with L19. The badge flips to "custom" when a dimension the row
  prints is edited. `head_chamfer` is not one, because no ISO row prints an angle. There is no code
  change and L19 stays. Update `.planning/REQUIREMENTS.md` TABL-06's text, citing L19 and this
  owner ruling (2026-11-01).

### Typed-default parity (INT-03, SC4)
- **D-11:** The web moves to the API and CLI rule:
  - The form tracks which fields the user typed into.
  - `partQuery()` writes a touched field to the query and to the shareable link even when its value
    equals the default.
  - A typed value is then explicit on all three front ends: a `422 over_budget` where the API and
    CLI give one, never a silent cap (L02).
  - Untouched fields stay out of the link, so links stay default-free.
- **D-12:** Fields set by picking a preset count as explicit on the web, matching the CLI, where "a
  preset's fields" are in the explicit set and a preset is never capped (`cli._params`,
  `cost.cap_defaults`). The planner checks the web's current preset path against this.
- **D-13:** A test shows the same typed-default part gets the same answer on the three front ends.
  Use the parity test, or the web tests' equivalent if the parity test cannot drive the form.

### Bookkeeping (SC5, not discussed, mechanical)
- **D-14:**
  - Add INFO-05 to the `requirements-completed` of the Phase 4 SUMMARY of plan 04-11 or 04-13.
  - Run `/gsd-validate-phase 6` and `/gsd-validate-phase 7`.
  - Re-run `/gsd-audit-milestone`.

### Owner rulings after research (2026-11-02, from 08-RESEARCH.md open questions)
- **D-15:** Bolt residual below the bolt threshold (research Pitfall 3, Open Question 1): a
  band-specific fine predicate. The fine sweep applies when the bolt's d is in a measured band
  (about 0.5 to 0.85 mm and 1.6 to 3.3 mm, edges read on the runner) and d / pitch > 6. Those
  long-thread parts build instead of being refused, and no catalogue bolt moves (none in the bands
  has d / pitch above 6). This adds a second kind of fine trigger beside D-03's d / pitch
  threshold, and the new `Lxx` records it. The D-06 turns guard stays as the backstop for anything
  the runner shows the fine sweep still refuses. A 2-D turns guard squeezed into [60, ~66] turns by
  iso4017:M3x30 was rejected.
- **D-16:** Nut threshold is strict `d / pitch > 6` (research Pitfall 2). It moves 8 of 14 nut
  catalogue rows (M5, M8, M10, M12, M14, M16, M18, M20) to the fine sweep. The default nut (d 6,
  pitch 1) and M2, M2.5, M3, M3.5, M4 and M6 stay on the shipped sweep. The `Lxx` lists the moved
  rows.
- **D-17:** `solid/pair.py` stays on the shipped sweep (research Pitfall 9). The `Lxx` records that
  `screw pair` for M5 to M20 proves a pair on the shipped representation, not the served fine one.
  `tests/data/pair_expected.tsv` is not re-measured.
- **D-18:** The turns guard's `ctx.fields` names `d`, `pitch`, `thread_length` and `length`
  (amends D-06), because the built thread is `min(thread_length, length)`.
- **D-19 (2026-11-02, after plan check):** The bolt fine trigger is the D-15 band clause only;
  there is no d / pitch-only bolt clause. D-03 reads the bolt threshold from the refusals, and the
  committed Phase 6 and 7 runner records hold 973 `ok` bolt readings and no refusal outside the
  bands at 8 < d / pitch <= 20; the 6 refusals there are inside the bands (d 3, d / pitch 8.57,
  84 mm thread). So bolts outside the bands stay on the shipped sweep up to the wall of 20. The
  runner walk adds out-of-band check cells at d / pitch in (8, 20]; if any is refused, the protocol
  stops and asks the owner. This refines D-03 and D-15.

### Claude's Discretion
- The error type name and message wording for the turns guard (follow `pitch_too_fine`).
- How the per-kind threshold is expressed in code (constants beside `MAX_*_D_PER_PITCH`, read by
  `solid/helical.py` through its params). The import boundaries hold: `calc` never imports
  `cadquery`.
- The exact denser nut grid, as long as it includes d / pitch 7 and is stated in the `Lxx`.
- How the web resets "touched": for example, a field cleared back to empty, or a new preset picked.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Gaps and their sources
- `.planning/v1.0-MILESTONE-AUDIT.md`: the gaps. OPER-03, INFO-05 and INT-01 to INT-06, with
  file:line evidence.
- `.planning/ROADMAP.md` § Phase 8: the goal and success criteria SC1 to SC5.
- `.planning/REQUIREMENTS.md`: the OPER-03, TABL-06, FRNT-05 and INFO-05 text.

### In-wall fix
- `docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md`: the residual (island,
  long-thread bands, isolated cells), option 2's measurements and the fallback.
- `.planning/debug/resolved/in-wall-kernel-builderror.md`: the diagnosis, evidence E1 to E32. E12,
  E14, E15, E19, E21, E27, E30, E31 and E32 matter most.
- `bench/results/phase-07/walls-pitch-41074314305/`: the walk readings behind L25 and the island.
- `docs/architecture/decision_log.md`:
  - L11: the construction and the volume estimator.
  - L20: the outer walls.
  - L21: the cost model and B-01.
  - L23: runtime sizing on the runner.
  - L24: timeouts.
  - L25: the d / pitch walls.
  - L32: the nut fine-STL peak budget.
  - L33: CI measures nothing, so re-sweeps are dispatched by hand.

### CLI deadline
- `docs/architecture/decision_log.md` L24, and the WR-03 note at lines 2028 to 2047 (the budget is
  above the timeout, owner-ruled).
- `src/screw/cli.py` `cmd_export`.

### Badge
- `docs/architecture/decision_log.md` L19 (the presets paragraph: `match` ignores the angle).

### Typed default
- `docs/architecture/decision_log.md` L02 standing rules (also in `CLAUDE.md`), and D-25 (explicit
  fields are the raw query keys).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `calc/thread.py` `pitch_too_fine_refusal` and `MAX_BOLT_D_PER_PITCH` / `MAX_NUT_D_PER_PITCH`
  (lines 76 to 83 and 390): the pattern for a kernel-free per-kind wall and its 422. The turns guard
  follows it.
- `solid/helical.py` `SECTION_SAMPLES = 14` (line 26) and the pipe-shell build: where the accuracy
  becomes conditional on the threshold.
- `calc/cost.py` `cap_defaults`, `fits_every_artifact` and `BUILD_TIMEOUT_S`: the envelope to widen
  for the parts above the threshold.
- `bench/` with `bench.oper`, `oper_sets`, the point sets and operability.yml `workflow_dispatch`
  (`plan`/`measure`, `set` required): the hand re-sweep path under L33.

### Established Patterns
- A conflict between explicit fields is a `422` with `ctx.fields` at the request boundary
  (`refuse_explicit_conflict`, `cli._params` and `explicit_conflict`). A post-build failure is a
  `422 build_error` (`app.py` around 571), which is what SC1 removes for in-wall parts.
- The explicit set is the raw query keys on the API (`app.explicit_fields`), and the given flags
  plus a preset's fields on the CLI (`cli._params`). `cap_defaults` moves only fields outside this
  set.
- `make verify` holds every shipped constant to committed records. New cost constants need records
  from the runner.

### Integration Points
- `static/app.js` `partQuery()` (around line 384) and the hash/link writer, for touched-field
  tracking.
- `tables/presets.py` `match()` and `app.js` badge (around lines 187 to 200): read only. INT-02 is a
  doc change.
- `tests/test_parity.py`: the registry-driven parity test (FRNT-05).

</code_context>

<specifics>
## Specific Ideas

- Known catalogue d / pitch range: from about 5 (M2×0.4) to 8 (M20×2.5). The nut wall of 8 is the
  catalogue's largest.
- Option 2 breaks 4 parts at d / pitch 250 ("0 solids from the tip cut"). They sit behind the bolt
  wall of 20, so they stay refused by `pitch_too_fine`. Confirm this still holds.
- Option 2 on one nut cell, d 0.8, pitch 0.0470589, m 0.8, right hand, gave "2 solids" (E31). Its
  d / pitch is 17, above the nut wall of 8, so it is already refused.

</specifics>

<deferred>
## Deferred Ideas

- A CLI `--timeout` flag: rejected for now (D-09). Revisit if CLI users ask for a deadline.
- INT-04 (`solid.build` returns `cq.Solid` to bench and tests) and INT-05 (the cost model ignores
  `head_chamfer`): info findings, outside this phase.

</deferred>

---

*Phase: 08-pre-release-gap-closure*
*Context gathered: 2026-11-01*
