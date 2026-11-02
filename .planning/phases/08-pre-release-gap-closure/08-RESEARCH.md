# Phase 8: Pre-release Gap Closure - Research

**Researched:** 2026-11-02
**Domain:** an OpenCascade pipe-sweep accuracy switch behind a per-kind d/pitch threshold, a kernel-free turns guard, a fitted cost model widened for the fine sweep, hand runner dispatch, and three small contract fixes (CLI deadline, badge wording, typed-default parity)
**Confidence:** MEDIUM-HIGH (the code seams, records and contracts are read this session; the kernel behaviour is reproduced locally on macOS arm64, which D-04 says is development evidence only; every threshold and ceiling still needs the linux/amd64 runner reading)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Use both the kernel fix (the debt's "option 2") and a kernel-free guard. Option 2 raises the sweep's accuracy: MakePipeShell approximation tolerance to 1e-6 and `helical.SECTION_SAMPLES` from 14 to 56. The guard refuses whatever option 2 leaves. Both land in this phase. Reversibility: costly. The sweep change moves build time, STEP bytes and the cost points of every part above the threshold. Undoing it means reverting the re-swept envelope too.
- **D-02:** The higher accuracy applies only above a d / pitch threshold, not everywhere. Parts at or below the threshold keep today's sweep. Their timeouts (L24), budgets (L21 B-01, L32) and cost points stay as measured and frozen (L33).
- **D-03:** The threshold is per kind, read from data. The nut threshold is at or below 7, so the d 2.2 mm, d / pitch 7 island is covered. This puts the M20 nut rows (d / pitch 8) on the fine sweep. The researcher checks that their STEP and every other artifact stay under B-01. The bolt threshold is read from the bolt refusals. It goes above 8 if the data allows, so no bolt catalogue row changes. iso4017:M20x200 would be 22.9 MB of STEP on the fine sweep, over B-01's 9.7 MB. If the data forces the bolt threshold to or below a catalogue row's d / pitch, stop and ask the owner.
- **D-04:** Prove everything on linux/amd64 on the runner, through operability.yml's `workflow_dispatch`, by hand. L33 removed the CI measurement, so these runs are started by hand, as Runs I and II were. Local macOS runs are for development only. They are not the evidence.
- **D-05:** Re-sweep only the parts above the thresholds, also by hand on the runner. Widen the fitted envelope, or add a feature, so the cost model predicts those parts honestly. There is no full re-sweep. The values for parts below the thresholds do not move.
- **D-06:** The guard limits built turns per d band. It is a kernel-free `422` in `calc/thread.py`, beside `pitch_too_fine_refusal`, that names `d`, `pitch` and `thread_length` in `ctx.fields`. Per-band ceilings are read from what option 2 leaves after the runner re-read. The error type name is the planner's choice, following `pitch_too_fine`. If no refusal is left in a band, that band gets no ceiling.
- **D-07:** Proof bar: a named grid, with the residual logged. These become tests, and every one either builds or is refused before the kernel: the debt's 20 parts; the d 2.2, d / pitch 7 nut island (forms base, s4 and m1, both hands); the long-thread bolt bands (d 0.5 to 0.85 and 1.6 to 3.3 mm, including d 3, pitch 0.35, 25 mm thread, right hand); a stated denser nut grid that includes d / pitch 7. A new `Lxx` records that cells off the grid are unproven: isolated failures at a seam cannot be bounded by a grid (debug E32). There is no catch-all that turns a post-build `BuildError` into a field `422`.
- **D-08:** Log the outcome as a new `Lxx` that supersedes L25 where it moves the walls or adds the guard. Resolve the debt in the same commit as the fix, and correct its "names no field" wording (INT-06). Mark OPER-03 complete in `.planning/REQUIREMENTS.md` only when SC1 holds.
- **D-09:** `screw export` stays unbounded by design. Log a new `Lxx` with this reason: `BUILD_TIMEOUT_S` (L24) protects a shared server's workers, and it was measured on the runner with every worker busy; a CLI user's machine has a different speed, so a runner deadline would refuse parts that would finish; the cost gate still refuses over-budget parts on the CLI (exit 2), and Ctrl-C is the user's deadline. Add one line to the README or the CLI docs, and to the `export` help text if it fits. There is no child process and no `--timeout` flag.
- **D-10:** Amend TABL-06 to agree with L19. The badge flips to "custom" when a dimension the row prints is edited. `head_chamfer` is not one, because no ISO row prints an angle. There is no code change and L19 stays. Update `.planning/REQUIREMENTS.md` TABL-06's text, citing L19 and this owner ruling (2026-11-01).
- **D-11:** The web moves to the API and CLI rule: the form tracks which fields the user typed into; `partQuery()` writes a touched field to the query and to the shareable link even when its value equals the default; a typed value is then explicit on all three front ends: a `422 over_budget` where the API and CLI give one, never a silent cap (L02); untouched fields stay out of the link, so links stay default-free.
- **D-12:** Fields set by picking a preset count as explicit on the web, matching the CLI, where "a preset's fields" are in the explicit set and a preset is never capped (`cli._params`, `cost.cap_defaults`). The planner checks the web's current preset path against this.
- **D-13:** A test shows the same typed-default part gets the same answer on the three front ends. Use the parity test, or the web tests' equivalent if the parity test cannot drive the form.
- **D-14:** Add INFO-05 to the `requirements-completed` of the Phase 4 SUMMARY of plan 04-11 or 04-13. Run `/gsd-validate-phase 6` and `/gsd-validate-phase 7`. Re-run `/gsd-audit-milestone`.

### Claude's Discretion

- The error type name and message wording for the turns guard (follow `pitch_too_fine`).
- How the per-kind threshold is expressed in code (constants beside `MAX_*_D_PER_PITCH`, read by `solid/helical.py` through its params). The import boundaries hold: `calc` never imports `cadquery`.
- The exact denser nut grid, as long as it includes d / pitch 7 and is stated in the `Lxx`.
- How the web resets "touched": for example, a field cleared back to empty, or a new preset picked.

### Deferred Ideas (OUT OF SCOPE)

- A CLI `--timeout` flag: rejected for now (D-09). Revisit if CLI users ask for a deadline.
- INT-04 (`solid.build` returns `cq.Solid` to bench and tests) and INT-05 (the cost model ignores `head_chamfer`): info findings, outside this phase.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| OPER-03 | Every allowed configuration builds inside the timeout; a configuration that cannot is capped and warned or refused with a `422`, never silently shortened (`.planning/REQUIREMENTS.md:66`, Pending). | Sections "Fine sweep", "Turns guard", "Cost model", "Runner workflow", "Validation Architecture". Local reproduction shows the fine sweep builds every cell the shipped sweep refuses in the probed region. |
| TABL-06 | Preset-match badge (`REQUIREMENTS.md:42`, "once any field is edited"). Touched by INT-02. | "INT-02": one text amendment, L19 text and `tables/presets.py` row fields quoted. |
| FRNT-05 | Each kind ships on UI, API and CLI with parity proven model-driven (`REQUIREMENTS.md:59`). Touched by INT-03. | "INT-03": the web omits a value equal to its default; reproduced kernel-free with `d=30 pitch=2 s=48 k=18`. |
| INFO-05 | Wrench-size note for M10, M12, M14 (`REQUIREMENTS.md:51`). Bookkeeping only. | "Bookkeeping": 04-11 and 04-13 SUMMARY frontmatter, both `requirements-completed: []`. |
</phase_requirements>

## Summary

The kernel fix works where the data says it should, and the hard part is the boundary, not the sweep. On macOS arm64 (development evidence only, D-04) the sweep with `MakePipeShell.SetTolerance(1e-6, 1e-6, 1e-4)` and 56 section samples builds all 6 cells of the d 2.2, d / pitch 7 nut island that the shipped sweep refuses, 288 of 288 nut cells at d / pitch 6.25 to 8, and 48 of 48 long-thread bolt cells at d / pitch 7 to 20 (n70 to n90, bands d 0.5 to 3) of which the shipped sweep refuses 30. The M5 to M20 nut catalogue rows build on it with STEP bytes 2.7x to 3.2x, preview-STL bytes 1.2x to 2.4x, fine-STL bytes 0.96x to 1.24x and build time 1.3x to 1.5x the shipped sweep, all far under B-01.

Three findings change the plan and are not in CONTEXT. (1) The island's exact d / pitch is 6.999993636369421 (pitch rounded up to 6 figures), so a nut threshold written "d / pitch >= 7" does not cover it; the threshold must be a strict `>` below 6.99999, and the walk read every nut cell at q 5, 6, 8, 9, 10 and 12 as ok, so `> 6` is the data-derived value. (2) Below any bolt threshold above 8 the shipped sweep still refuses ordinary parts at d 1.6 to 3.3 mm: d 2.5, pitch 0.35, 30 mm thread (d / pitch 7.14, 85.7 turns) and d 2 / 3 at d / pitch 7 with 80 turns or more and at d / pitch 8 with 70 turns or more. Those are not "what option 2 leaves"; they are what the shipped sweep keeps below the threshold, and D-06's guard must cover them, with a ceiling squeezed between the catalogue (M3x30 is 60 turns) and the first refusal (70 turns at d / pitch 8). (3) Making the web treat a typed default as explicit also changes `thread_length_conflict` and `head_chamfer_conflict` behaviour on the web, and it contradicts sentences in L19, L21 and `01-UI-SPEC.md` rules 6, 9, 19 and 35, which the new `Lxx` must supersede in part.

**Primary recommendation:** Land the fine sweep and the strict thresholds (bolt `> 8`, nut `> 6`) in one commit with a `fine` argument on `helical.thread`; register and push a pre-registered walk set and a fine cost re-sweep set; dispatch both by hand from the pushed phase branch; derive the guard ceilings and the fine envelope with committed judge code; then land the guard, the cost constants and L34 together, and resolve the debt in that commit.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Which sweep a part gets (fine or shipped) | `screw.calc.thread` (pure predicate on exact d / pitch) | `screw.solid` (reads it, passes `fine=` to `helical`) | `calc` never imports `cadquery`; `solid` already imports `calc.thread`. One predicate, read by the builder and by the cost model. |
| The sweep itself (tolerance, samples) | `screw.solid.helical` (kernel, worker only) | none | Vendor types stop at `screw.solid`. |
| Turns guard (422 naming fields) | `screw.params` model validator calling a pure `calc.thread` function | none | A parameter is validated once, at the model boundary (CLAUDE.md); one validator reaches API, CLI, info route and web `ctx.fields` highlight. |
| Fine-sweep cost prediction | `screw.calc.cost` (emitted constants) | `bench.oper_fit` (writes them), runner records (evidence) | `make verify` holds the shipped block to the committed records. |
| Runner evidence | GitHub Actions `operability.yml` dispatch, production image | `bench.oper`, `bench.oper_sets` (set generators and judges) | D-04: only the linux/amd64 runner bounds anything. |
| Typed-field tracking and link writing | Browser (`static/app.js`) | API (`app.explicit_fields` reads raw query keys) | The server already treats a present key as explicit; only the page drops keys. |
| CLI no-deadline decision | Decision log (new Lxx) + README/help text | `cli.cmd_export` (no code change) | D-09. |
| Badge wording | `REQUIREMENTS.md` text | L19 (unchanged) | D-10. |

## Standard Stack

No new package is needed. Everything is the shipped stack.

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| cadquery / cadquery-ocp | 2.8.0 / 7.9.3.1.1 | The sweep: `BRepOffsetAPI_MakePipeShell.SetTolerance(Tol3d=0.0001, BoundTol=0.0001, TolAngular=0.01)` | [VERIFIED: local `OCP` docstring read this session; cadquery 2.8.0 from `.venv`; the runner records name the same pair, `bench/RESULTS.md` host table] |
| pydantic | pinned in `requirements.txt` | `PydanticCustomError(type, msg, {"fields": [...]})` for the guard | [VERIFIED: `src/screw/params.py:166`] |
| pytest 9.1.1 + xdist + cov | `.venv` | `make test PYTEST_ARGS=...` | [VERIFIED: `.venv/bin/python -c "import pytest"` this session] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| A separate `FINE_ENVELOPE` for fine-sweep parts | Refit coefficients with a `fine` feature | The explore set holds only 20 bolt and 8 nut labels above the thresholds (counted this session), too few for a stable log-linear refit with 7 to 8 coefficients. A per-model envelope e over the re-sweep is R12's own definition and leaves every part below the thresholds bit-identical (D-02, D-05). Recommended. |
| A turn-aware fine predicate (fine only when d / pitch > 8 and turns are large) | the locked per-kind d / pitch threshold | Would spare ordinary short fine-pitch bolts the 3x to 4.5x STEP growth, but D-03 locks "a d / pitch threshold". Do not plan it; state the consequence in the Lxx instead. |
| Bolt threshold at or below 7 so no guard is needed below it | Guard below the threshold | Moves catalogue bolts (d / pitch 7 and 8 rows, including iso4017:M20x200 at 22.9 MB STEP) onto the fine sweep and breaks B-01. D-03 says stop and ask; not recommended. |

**Installation:** none. **Version verification:** no package is added.

## Package Legitimacy Audit

No external package is installed by this phase; the audit table is empty by construction. **Packages removed due to SLOP: none. Packages flagged SUS: none.**

## Architecture Patterns

### System Architecture Diagram

```
request (web hash/query, API query, CLI flags)
   |
   v
params.BoltParams / NutParams  (model validators, in order, last = _fine_pitch)
   |  pitch_too_fine (L25 walls)  -> 422 ctx.fields [d, pitch]
   |  NEW turns guard             -> 422 ctx.fields [d, pitch, thread_length(, length)]
   v
calc.cap_defaults / download_refusal  (cost.fits per artifact)
   |   fits() = predict() x (1 + e), e = ENVELOPE, or FINE_ENVELOPE when uses_fine_sweep(kind, d, pitch)
   |   over budget -> 422 over_budget (API) / exit 2 (CLI) / cap + warn for a defaulted field only
   v
solid.export (worker)  --> bolt.thread(p) / nut.void(p)
   |      fine = calc.thread.uses_fine_sweep(kind, d, pitch)   (exact Fraction compare)
   v
helical.thread(..., fine) -> twist(..., fine) -> section(..., samples=56 if fine else 14)
   |      pipe.SetTolerance(1e-6, 1e-6, 1e-4) only when fine
   v
check_solid / piece_refusal gates (unchanged)  -> bytes | BuildError -> 422 build_error
```

### Recommended Project Structure (touch list)
```
src/screw/calc/thread.py      # + thresholds, uses_fine_sweep(), turns_guard_refusal()
src/screw/params.py           # + one model validator per kind calling the guard
src/screw/solid/helical.py    # section(samples), twist(fine), thread(fine) ; default stays shipped
src/screw/solid/bolt.py       # thread(): pass fine=
src/screw/solid/nut.py        # void(): pass fine=
src/screw/calc/cost.py        # + FINE_ENVELOPE (emitted), fits()/predict() pick it
bench/oper_sets.py            # + proof-grid walk set, + fine re-sweep set, + judge subcommand
bench/oper_fit.py             # + fine envelope computation and emit-constants lines
bench/oper_lift.py            # _no_pitch_wall also lifts the new guard (see Pitfall 1)
bench/points/<new>.json       # pre-registered sets
bench/results/phase-08/       # runner records, downloaded by hand
tests/                        # test_fine_pitch.py (extend), test_turn_guard.py (new), records-driven proof test, test_cost.py, test_parity.py
src/screw/static/app.js       # touched-field tracking
```

### Pattern 1: the kernel-free per-kind wall, now twice
**What:** exact-decimal compare of `Fraction(repr(d)) / Fraction(repr(pitch))`, a message that begins with the field names (the CLI prints no `loc` for a model-level error), and a `PydanticCustomError` carrying `{"fields": [...]}` from the model's last validator.
**When to use:** the fine-sweep predicate, the turns guard.
**Example (existing, quoted):**
```python
# src/screw/params.py:158-166  [VERIFIED: read this session]
def _pitch_too_fine(p: FastenerParams) -> None:
    from screw.calc.thread import pitch_too_fine_refusal

    if (msg := pitch_too_fine_refusal(p.kind, p.d, p.pitch)) is not None:
        raise PydanticCustomError("pitch_too_fine", msg, {"fields": ["d", "pitch"]})
```
```python
# src/screw/calc/thread.py:76 and :83  [VERIFIED: read this session]
MAX_BOLT_D_PER_PITCH = Fraction("20")
MAX_NUT_D_PER_PITCH = Fraction(8)
```

### Pattern 2: the fine switch (skeleton, values from the cited evidence)
```python
# calc/thread.py (kernel-free). Strict `>`: the island's exact d / pitch is 6.999993636369421.
FINE_BOLT_ABOVE = Fraction(8)   # catalogue max d / pitch is 8.0 (tests/test_fine_pitch.py asserts nut max == 8)
FINE_NUT_ABOVE = Fraction(6)    # largest q the walk read ok for every cell below the island's q 7

def uses_fine_sweep(kind: str, d: float, pitch: float) -> bool:
    above = FINE_BOLT_ABOVE if kind == "bolt" else FINE_NUT_ABOVE
    return _exact(d) / _exact(pitch) > above

# solid/helical.py: `fine` selects the two knobs of the debug session's E12/E14 variant.
#   section(...): nf = 56 if fine else 14      (today: SECTION_SAMPLES = 14, helical.py:26)
#   twist(...):   if fine: pipe.SetTolerance(1e-6, 1e-6, 1e-4)   # before pipe.Add(...), as the variant did
```
The variant that produced E12/E14 and all local probes this session called `pipe.SetTolerance(tol, tol, 1e-4)` after `SetMode` and before `Add` [VERIFIED: scratch `iw/variant.py` read this session, outside the repo; reproduced in `/tmp/p8/variant.py`]. Use exactly those arguments: the evidence was taken with TolAngular 1e-4, not the 0.01 default.

### Pattern 3: hand dispatch from a pushed branch
The image is built from the dispatched commit (`operability.yml`, `docker/build-push-action`, tag `screw:ci`), so the code under test must be committed and pushed first. The branch `gsd/phase-08-pre-release-gap-closure` has no upstream today (`git branch -vv`).
```bash
# command shapes Phase 7 used  [VERIFIED: 07-05-PLAN.md:29,200,203; 07-05-SUMMARY.md:101-104]
git push -u origin gsd/phase-08-pre-release-gap-closure
gh workflow run operability.yml --ref gsd/phase-08-pre-release-gap-closure -f set=<name>
gh run list --workflow operability.yml --limit 3
gh run download <run-id> -p 'oper-*' -D bench/results/phase-08/<name>-<run-id>   # NOT `gh run download <id>`: dockerbuild artifacts are invalid zips
```
`set` is the only input and it is required (`operability.yml`, `workflow_dispatch.inputs.set.required: true`). Records land as artifacts `oper-<set>-<shard>-<rep>` (30 days retention). Phase 7 wrote one `### <set>, run <id>` section per run in `bench/RESULTS.md` with dispatched sha, CPU models, status counts and the judge's printed output (see `### walls-pitch, run 41074314305`).

### Pattern 4: judge code writes the constant, a test holds the file to it
`python -m bench.oper_sets pitch-walls --from <dir>` prints the `# BEGIN pitch-walls` block that `calc/thread.py` carries; `tests/test_oper_pitch.py` and `tests/test_cost.py::test_the_shipped_constants_are_the_block_emit_constants_writes_from_the_evidence` fail if a shipped number is not what the committed records produce. Phase 8 constants that are read from data (the guard ceilings, the fine envelope) follow this pattern; constants that are rulings (the bolt threshold 8, equal to the catalogue maximum) carry the ruling in a comment like `MAX_NUT_D_PER_PITCH`.

### Anti-Patterns to Avoid
- **A threshold written `>= 7` for the nut.** Misses the island (Pitfall 2).
- **A module global toggled for the fine sweep.** `SECTION_SAMPLES` is read inside `section()` today; make it an argument, not a flipped global (the cached solid is built under one lock, but tests and bench import `helical.thread` directly).
- **A catch-all that turns a post-build `BuildError` into a field 422.** Forbidden by D-07.
- **Adding the guard to `params` without lifting it in `bench/oper_lift`.** Breaks every pre-registered set's regeneration (Pitfall 1).
- **Editing `helical` after the cost re-sweep was read.** It voids the fine envelope.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Exact d / pitch compare | float division | `_exact()` (`Fraction(repr(x))`) as `pitch_too_fine_refusal` does | 175 / 0.7 is a float above 250 though exactly 250 (docstring at `calc/thread.py:301`). |
| 422 with `ctx.fields` on all front ends | per-front-end checks | one `PydanticCustomError` from a model validator | API body, CLI `error:` line (exit 2) and the web's `ctx.fields` highlight all come from it (`tests/test_fine_pitch.py` asserts the exact shape). |
| Pre-registered point set and its regeneration check | an ad-hoc JSON | `_Set` + `build_*` + `_regenerate_runs2` entry + a CLI subcommand in `bench/oper_sets.py` | `python -m bench.oper_sets --check` regenerates every committed set from its sources. |
| Envelope arithmetic | hand-typed e | `bench.oper_fit.envelope` (raises the factor by single ulps until `pred x (1+e)` >= every actual) | R12's guarantee holds in float arithmetic. |
| Constants block in `cost.py` | typing numbers | extend `bench.oper_fit.emit_constants`; the existing test asserts the block verbatim | Typed numbers fail `make verify`. |
| Margin rule for ceilings | an eyeballed number | R31's rule form (`r10_at_or_below(F / 1.25)`), adapted and pre-registered, but see Pitfall 4 | A bound is credible because its rule was fixed before its data (07-SWEEP-PROTOCOL). |

**Key insight:** every number the tool prints or enforces here has a committed judge and a test that re-derives it. A threshold or ceiling with no record behind it is exactly what `make verify` is built to reject.

## Common Pitfalls

### Pitfall 1: the new guard silently rewrites every pre-registered set
**What goes wrong:** `oper_lift.drawn()` validates under the production model less `MAX_BOLT_D_PER_PITCH` and `MAX_NUT_D_PER_PITCH` only (`bench/oper_lift.py:93-110`). A new validator in `params.py` is then active inside `drawn()`, drops points from `walls-pitch.json`, `explore.json` and others when they are regenerated, and `python -m bench.oper_sets --check` and `tests/test_oper_pitch.py::test_the_walk_file_is_what_the_generator_writes_under_its_recorded_envelope` go red.
**How to avoid:** extend `_no_pitch_wall` (or add a sibling context manager used by `drawn` and `registered`) to lift the guard's constants. Also the runner child validates with plain `oper_lift.validate(kind, params, lift)` (`bench/oper_child.py:322`), which has no `drawn` lift: a point the guard refuses is a "bad point", exit 2, never read. Phase 7 avoided this by reading the walk before the wall landed; do the same: dispatch the guard-placing walk from a commit that has the fine sweep and no guard, then add the guard.
**Warning signs:** `oper_sets --check` names a point file; child exit 2 "bad point".

### Pitfall 2: the island is at d / pitch 6.9999936, not 7
**What goes wrong:** the walk sets `pitch = ceil6(d / q)`, so the exact ratio is at most q. The six island cells are at `1100000/157143 = 6.999993636369421` [VERIFIED: `python -m bench.oper_sets pitch-walls --from bench/results/phase-07/walls-pitch-41074314305` run this session]. `ratio >= 7` leaves them on the shipped sweep.
**How to avoid:** strict `>` against a clean number below 6.99999. The walk read all 344 nut cells at q 5 and q 6, q 8, 9, 10 and 12 as ok, q 7 had 338 ok and the 6 island cells refused, q 11 had 11 refused (counted from the committed records this session). The largest q read ok below the island is 6.
**Consequence to state in the Lxx:** with `> 6` the nut catalogue rows M5 (6.25), M8 (6.4), M10 (6.667), M12 (6.857), M14 (7.0), M18 (7.2), M16 and M20 (8.0) move to the fine sweep: 8 of 14. The default nut (d 6, pitch 1, ratio 6) and M2, M2.5, M3, M3.5, M4, M6 stay. The margin rule (`r10_at_or_below(F / 1.25)` = 5) would also move M3, M6 and the default nut; do not use it, D-02 wants parts at or below the threshold unchanged and D-03 says "at or below 7".

### Pitfall 3: the shipped sweep keeps refusing ordinary bolts below the bolt threshold
**What goes wrong:** with the bolt threshold at 8 (the catalogue maximum, the only value that moves no catalogue bolt), the shipped sweep still refuses long threads at d 1.6 to 3.3 mm at d / pitch 7 to 8.
**Evidence (local macOS arm64, dev only, shipped sweep, this session):** d 2.5, pitch 0.35, 30 mm (d / pitch 7.143, 85.7 turns) right hand refused "wrong tip cone"; d 2, d / pitch 7: refused at n80 and n90, ok to n75; d 2 and d 3, d / pitch 8: ok to n66, refused from n70; d / pitch 6: ok through n90. The left twins build. Runner side: dense-band run 41153581470 read M2, M2.5, M3 at n90 right ok with tip pieces 0.78 to 0.97 of T_PIECE (`bench/RESULTS.md`, `### dense-band, run 41153581470`); debug E27/E29 had d2 d / pitch 8 n80 and d / pitch 7 n90 refused on linux/amd64 [CITED: `.planning/debug/resolved/in-wall-kernel-builderror.md` E27, E29].
**Why it matters:** SC1 says every admitted in-wall part builds or is refused. These parts are admitted today and are below the threshold, so option 2 never touches them. D-06's guard must cover them.
**How to avoid:** the guard needs a runner walk of the shipped sweep in this region (d bands 0.5 to 0.85 and 1.6 to 3.3, d / pitch 6 to 8, turns 50 to 90), and a ceiling that sits above the catalogue's worst row in the band, iso4017:M3x30 at 60.0 turns (d / pitch 6.0) [VERIFIED: computed from the catalogue this session], and below the first refusal (70 turns at d / pitch 8 locally). A flat 1.25 margin under 70 is 56, which refuses M3x30 and M2.5x25 (55.6 turns) and so is not usable; the guard is 2-D (d band, d / pitch above 6, turns above N) or the margin rule is adapted. Pre-register which before the walk. The band edges at d / pitch 7 to 8 are unmeasured (E30 measured them only at d / pitch 20: d 0.45 out, 0.5 in, 0.85 in, 0.9 out, 1.55 out, 1.6 in, 3.3 in, 3.35 out), so the walk needs d steps near 0.45 to 0.9 and 1.5 to 3.4.
**Alternative to put to the owner if the 2-D guard looks fragile:** a band-specific fine predicate (fine when d is in a band and d / pitch > 6). It moves no catalogue bolt (no catalogue bolt in the bands has d / pitch above 6) and refuses nothing, but it is a second kind of threshold and D-03 locked a d / pitch one. Surface it; do not decide it.

### Pitfall 4: the fine sweep makes ordinary parts bigger
**What goes wrong:** every bolt with d / pitch in (8, 20] and every nut in (6, 8] changes: macOS dev numbers for the catalogue nuts: M20 build 1.65 -> 2.46 s, STEP 881196 -> 2816455 B (the debug session's E21 recorded the same bytes, 2816455), preview STL 1565584 -> 1829684 B, fine STL 10435684 -> 10016184 B; M5 is the extreme for the preview (378184 -> 731784 B) and the fine STL (2509184 -> 3107184 B, 1.24x). Across M5, M8, M10, M12, M14, M16, M18, M20 the fine STEP is 2.0 MB to 2.8 MB against B-01's 9748694.77 B, the preview at most 1.8 MB against 55.7 MB, and the fine STL at most 10.1 MB against 239.5 MB [VERIFIED: local probe this session (`/tmp/p8/cat-shipped.log`, `/tmp/p8/cat-fine.log`); B-01 at `src/screw/calc/cost.py:184` `BUDGET`]. The cgroup peak (L32's cap) cannot be read locally; the runner reading decides it, but these builds are small. Fine-pitch bolts such as M20 x 1.5 (d / pitch 13.3), not in the catalogue, take the same hit (E21: 3.6x to 4.5x STEP for bolts at d / pitch 6 to 8).
**How to avoid:** say it in the Lxx "What moves" section (L32's model). The B-01 budget stays; the fine envelope is what refuses a fine-sweep part whose real STEP would pass the budget.

### Pitfall 5: widening the shared envelope changes parts below the thresholds
**What goes wrong:** `ENVELOPE[kind, artifact, target]` applies to every part. Raising it to cover 4.5x STEP growth would refuse parts that are untouched and break "values for parts below the thresholds do not move" (D-05) and B-01's catalogue-admitted counts.
**How to avoid:** a separate `FINE_ENVELOPE`, selected by `uses_fine_sweep`, computed by R12's definition over the fine re-sweep readings only.
**Follow-on checks:** `tests/test_runtime_bounds.py::test_runtime_json_is_what_derive_runtime_writes_from_every_committed_record` and R21's export-cache count use `cost.fits` over explore candidates (L32 recorded 394 -> 390 when a cap changed `fits`); a fine envelope can drop more explore nuts and bolts, so re-run it and read the count before committing. `python -m bench.oper_sets --check` and `prediction-drift` must stay unchanged: they take the envelope from the file's recorded one, not from `cost.ENVELOPE`, but verify by running them.

### Pitfall 6: run ids in shipped code need a RESULTS section
**What goes wrong:** `tests/test_runtime_bounds.py::test_every_run_id_the_code_and_l20_to_l25_cite_has_its_section_in_results` scans `src/**/*.py|js`, `Dockerfile`, `compose.yaml` and the text of L20 to L25 for 11-digit run ids and requires `^#+ .*\brun <id>\b` in `bench/RESULTS.md`. Every comment that cites a Phase 8 run needs its `### <set>, run <id>` heading. L26 and later are not scanned, but cite there too.

### Pitfall 7: typed-default parity reaches past the cap
**What goes wrong:** D-11 also changes the explicit-conflict rules on the web. `explicit_conflict` fires on two explicit values (`thread_length_conflict`, `head_chamfer_conflict`, D-25). Today a typed `thread_length=20` is dropped by `partQuery` and a short `length` only warns (`01-UI-SPEC.md:233`); after D-11 it is a 422, as on the API. A preset pick (D-12) makes all six row fields explicit (`entry.fields` = d, pitch, length, s, k, thread_length [VERIFIED: `src/screw/tables/presets.py` row fields]), so editing `length` below the row's `thread_length` afterwards is a 422 `thread_length_conflict`, exactly as `screw export --preset iso4014:M10x80 --length 20` already is (`cli._params` comment).
**How to avoid:** state it in the Lxx; amend the sentences it contradicts: L19 ("a typed 30 is never explicit there", `decision_log.md:~1456`), L21 ("a typed default counts as not set there", `~1770`), and `01-UI-SPEC.md` rule 6 (grammar, "Only fields that differ from their default are written"), rule 9 (reading), rule 19 (Reset), rule 35, and table rows at lines 224 and 233. The UI-SPEC grows by appending rule numbers (04-13 SUMMARY pattern), so add a rule and edit the quoted ones in place.

### Pitfall 8: `PINNED_STATEMENTS` pins the line being changed
`tests/test_parity.py` pins `Number(value) !== Number(defaults[name])` and `for (const [name, { input }] of fields) write(input, h.get(name) ?? defaults[name]);` (lines 601 and 606). Changing `partQuery`/`navigate` means editing the pins in the same commit, with the teeth test (`test_the_literal_check_has_teeth`) kept. `_field_literals` also asserts the page reads no field by name.

### Pitfall 9: the pair proof does not follow the sweep switch unless told to
`solid/pair.py:68,78` call `helical.thread(...)` directly for the rod and the void. With `fine` defaulting to False they keep the shipped sweep, so `screw pair` for an M5 to M20 nut proves a pair built on a different representation than the served nut. The 240 pre-registered pair cells (`tests/data/pair_expected.tsv`, `make pair`) were measured on the shipped sweep. Decide and log it (see Open Question 3).

### Pitfall 10: the cost re-sweep is invalidated by any later kernel change
The fine envelope is a statement about the committed `helical` bytes. Freeze `helical.py`, the thresholds and `bolt.py`/`nut.py` before the cost dispatch. L33 removed CI measurement, so nothing re-checks it afterwards.

## Code Examples

### Turns guard shape (follow `turn_cap`)
```python
# params.py, BoltParams: [VERIFIED shape: src/screw/params.py turn_cap validator, read this session]
@model_validator(mode="after")
def _turn_guard(self) -> Self:
    from screw.calc.thread import built_thread_length, turn_guard_refusal   # turn_guard_refusal is new

    t = built_thread_length(self.thread_length, self.length)
    if (msg := turn_guard_refusal(self.d, self.pitch, t)) is not None:
        raise PydanticCustomError("turn_guard", msg, {"fields": ["d", "pitch", "thread_length", "length"]})
    return self
```
The message must begin with the field names (`"d, pitch, thread_length and length: "`) because the CLI prints no `loc`. CONTEXT D-06 lists `d`, `pitch`, `thread_length`; the built thread is `min(thread_length, length)` (`built_thread_length`, `calc/thread.py:203`) and the existing `turn_cap` names `thread_length, length, pitch`, so name `length` too (Open Question 4). The type name `turn_guard` is a placeholder (discretion). Call it from the last validator so a part another rule refuses keeps its older error, as `_fine_pitch` does (L25).

### API and CLI assertions to reuse (`tests/test_fine_pitch.py`)
```python
# API: 422, detail == {"loc": ["query"], "type": <type>, "msg": expected, "ctx": {"fields": [...]}}
# CLI: SystemExit code 2 and capsys.readouterr().err == f"error: {expected}\n"; no file written
```
[VERIFIED: the two parametrised tests in `tests/test_fine_pitch.py`, read this session.]

### INT-03 reproduction part (kernel-free, run this session)
`BoltParams d=30 pitch=2 s=48 k=18` (head ratios inside their bands). Omitting `thread_length`: info warns "thread_length: the default 20 mm puts the preview STL ... over its measured budget" and all four downloads are served (capped part). Passing `thread_length=20`: no cap, stl-fine and stl-preview downloads refused, `screw export bolt --d 30 --pitch 2 --s 48 --k 18 --thread-length 20 -o x.stl` exits 2 and writes nothing. That is the API/CLI answer; the web, which drops `thread_length=20`, gives the first. Use this part for D-13.

### Touched-field tracking (shape only)
`partQuery()` today: `const changed = input.type === 'number' ? Number(value) !== Number(defaults[name]) : value !== String(defaults[name]); if (changed) q.set(name, value);` [VERIFIED: `static/app.js:384-397`]. New rule: write when `changed || touched.has(name)`. `touched` is page state keyed like `lastTyped`: add on the `input` event with a non-empty value, delete when the field is cleared, replace with the picked row's field names in `pick()` (`app.js:226`), reset to the hash's keys in `navigate()` (a present key is explicit; otherwise a reload would drop it), clear on Reset (`app.js` `#reset` handler) and on a kind switch (new form). Never read it in `writeHash`'s callers other than via `partQuery` (parity tests assert `partQuery`/`writeHash` do not name `presetBasis`, `rowOfFields`, `quality`, `download`, `lastTyped`).

## Runtime State Inventory

Not a rename or migration phase. Omitted.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Walls only (L25: bolt d / pitch 20, nut 8) | Walls plus a fine sweep above a lower threshold plus a turns guard | this phase | Parts between the thresholds and the walls build on a more accurate, larger representation. |
| CI measures the runner (L26 to L28) | Hand dispatch only (L33) | 2026-11-01 | Every Phase 8 reading is started by hand, and nothing re-checks the frozen timeouts afterwards. |

**Deprecated/outdated:** `README.md` line 15 still says "there is no nut yet" (not this phase; mention only if a README edit for D-09 touches the paragraph).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Local macOS arm64 builds predict linux/amd64 outcomes for the probed cells. The debug session found identical status on every cell read on both platforms, pieces within 9.1e-10 (bolts) and 4.1e-08 (nuts) (E29, E32), but the island, the 288-cell nut grid and the 48-cell bolt grid were not read on the runner. | Summary, Pitfalls 3, 4 | A threshold or ceiling placed from local data fails on the runner. This is why D-04 requires the runner walk. |
| A2 | Nut threshold `> 6` (rather than e.g. `> 6.9`) is the better choice. | Pitfall 2 | Choosing `> 6.9` moves 4 catalogue rows instead of 8 but leaves (6, 6.9] on the shipped sweep, where only q = 6 and M10/M12 were ever read. The planner/owner may prefer it. |
| A3 | A `FINE_ENVELOPE` per (kind, artifact, target) is enough, i.e. the log-linear shape holds in the fine region at the existing coefficients. | Alternatives | If fine readings do not scale with the shipped model (4.5x STEP at d / pitch 8, unknown at 20 for large d), e becomes huge and refuses most fine parts; then a `fine` feature or a separate refit is needed. |
| A4 | Timeouts stay valid: the fine seconds envelope keeps admitted fine builds under the same budget-vs-timeout relation WR-03 accepted (budget 15.0 / 34.1 / 94.4 s against timeouts 26 / 71 / 26 s). | Cost model | A fine-sweep part admitted near the seconds budget can overrun the timeout (503 `timeout`, `cost_model.miss` logged). Include a verdict check like the dense-band set's `cold wall x (1 + m)` against the timeout. |
| A5 | `solid/pair.py` stays on the shipped sweep. | Pitfall 9 | `screw pair` proves a pair on a different representation than the served nut for M5 to M20. |
| A6 | A Phase 8 sweep protocol (rules written before data, set files pinned by blob sha) is expected by the owner as in Phase 7. | Patterns | If not, the extra document is overhead; if expected and skipped, the thresholds read as post-hoc. |
| A7 | The number of runner readings needed (a walk of a few thousand `step` points plus a re-sweep of the above-threshold labels at 3 artifacts) fits one or two dispatches like Phase 7's 19-shard walk (5656 points). | Runner | Larger sets need more shards; shard counts come from R6 charges. |

## Open Questions (RESOLVED)

Each question's resolution, recorded 2026-11-02 after the owner's rulings D-15 to D-19 (08-CONTEXT.md) and the plan check.

1. **Bolt below-threshold residual (the main one).**
   - Known: the shipped sweep refuses ordinary long-thread parts at d 1.6 to 3.3 mm, d / pitch 7 to 8, turns 70 to 90; a threshold above 8 does not reach them; the catalogue squeezes the ceiling to the interval [60, ~66].
   - Unclear: where the runner puts the first refusal and the band edges at d / pitch 6 to 8.
   - Recommendation: a pre-registered shipped-sweep walk of that region, a 2-D guard (d band, d / pitch above 6, turns above N), and the band-specific fine predicate offered to the owner as the alternative. If neither fits without moving a catalogue bolt, stop and ask (D-03).
   - **RESOLVED by D-15 and D-19:** the band-specific fine predicate (d in a measured band, d / pitch > 6), and no d / pitch-only bolt clause (D-19). The band edges are read on the runner by 08-SWEEP-PROTOCOL.md F4 and F5 (plans 08-01, 08-03).
2. **Nut threshold: 6 or something in (6, 7).** Recommend `> 6`; the planner states the 8 catalogue rows it moves.
   - **RESOLVED by D-16:** strict `d / pitch > 6`; it moves M5, M8, M10, M12, M14, M16, M18 and M20.
3. **Pair proof and the sweep.** Recommend leaving `solid/pair.py` on the shipped sweep, log it, and let the owner rule if they want the pair proof on the served geometry (it would need `pair_expected.tsv` re-measured, outside this phase).
   - **RESOLVED by D-17:** `solid/pair.py` stays on the shipped sweep; L36 records it and plan 08-09 files the residual as debt.
4. **Guard `ctx.fields`.** D-06 says `d`, `pitch`, `thread_length`; the built thread also depends on `length`. Recommend all four, text starting `d, pitch, thread_length and length: `.
   - **RESOLVED by D-18:** all four fields.
5. **Does the fine sweep leave any bolt refusal at all above the threshold?** Locally no (48 of 48). If the runner agrees, D-06's "if no refusal is left in a band, that band gets no ceiling" applies to d / pitch above 8, and the guard exists only for the below-threshold residual of Question 1.
   - **RESOLVED by the protocol and D-19:** D-19 removes the d / pitch-only bolt clause, so no bolt outside the measured bands is on the fine sweep. Inside a band, F7 and F8 turn each fine-sweep refusal into that band's ceiling, and a band with no refusal gets none (D-06). Outside the bands, F5's check cells (8 < d / pitch <= 20) re-read the shipped sweep, and a refusal there is a stop for the owner (D-19). A refused nut on the fine sweep is an F7 stop. Each stop has its owner path in the protocol's `## Stops and owner paths`.
6. **Web UX after a preset pick (D-12).** Editing `length` below the picked row's `thread_length` becomes a 422. This is the owner's rule; mention it in the Lxx and the UI-SPEC so it is not found as a regression.
   - **RESOLVED by L35** (plan 08-04): L35 and UI-SPEC rule 38 name the consequence: `thread_length_conflict` can now fire on the web once a picked row's thread_length is explicit.
7. **Does the fine envelope change the admitted set enough to move runtime.json's R21 count or any frozen B-01 count?** Compute before committing the constants.
   - **RESOLVED by F10 and F12** (plan 08-08): F12 re-derives `runtime.json`, and a move of any value other than R21's export-cache candidate count is a stop. F10 stops if `FINE_ENVELOPE` refuses a catalogue row or a default part at any artifact (B-01). Both stops have owner paths in the protocol.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 + `.venv` with cadquery | local development builds, `make verify` | yes | 3.12.15 / cadquery 2.8.0 | none needed |
| `make`, pytest, xdist | gates | yes | pytest 9.1.1 | none |
| `gh` authenticated | dispatch and download | yes | logged in as halfb00t | none |
| `git` remote `origin` | push before dispatch | yes (`git@github.com:halfb00t/screw.git`) | branch not pushed yet | push with `-u` |
| Docker | `make check`, `make image`, local `bench.oper` | yes | 29.8.2 | runner dispatch is the evidence anyway |
| Node | none required (`vendor` only); an optional JS unit test would need it | yes | v22.23.4 | source-text assertions (house style, L01) |
| GitHub-hosted linux/amd64 runner | all D-04 evidence | not probed from here | ubuntu-latest | none; D-04 forbids substituting macOS |

**Missing dependencies with no fallback:** none found. **Blocking human action:** the dispatches are `gh` commands an agent can run, but the scheduling of a full walk may deserve a `checkpoint:human-verify`.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 + pytest-xdist 3.8.0 + pytest-cov 7.1.0, coverage floor 96 |
| Config file | `pyproject.toml` (`addopts = "--strict-markers --strict-config -m 'not grid and not pair'"`) |
| Quick run command | `make test PYTEST_ARGS="tests/test_fine_pitch.py tests/test_cost.py -q -n0 --no-cov"` |
| Full suite command | `make verify` (ruff, mypy `--strict`, import-linter, unfinished-work scan, pytest; no Docker) |

### Phase Requirements to Test Map
| Req / SC | Behavior | Test Type | Automated Command | File Exists? |
|----------|----------|-----------|-------------------|-------------|
| SC1 sweep | `uses_fine_sweep` is exact and strict at the thresholds; `helical.thread(fine=True)` uses 56 samples and the tolerance; default call unchanged | unit (kernel-free for the predicate, kernel for a 2-3 cell build) | `make test PYTEST_ARGS="tests/test_thread_maths.py tests/test_solid.py -q -n0 --no-cov"` | extend existing |
| SC1 island | the 6 island nuts (d 2.2, pitch 0.314286, forms base/s4/m1, both hands) build through `solid.build` | kernel, ~2 s each locally | `make test PYTEST_ARGS="tests/test_nut.py -k island -q -n0 --no-cov"` | no, Wave 0 |
| SC1 debt example | d 3, pitch 0.35, thread 25 mm right builds (4.4 s locally) | kernel | `make test PYTEST_ARGS="tests/test_solid.py -k long_thread -q -n0 --no-cov"` | no, Wave 0 |
| SC1 guard | the guard is a 422 with `ctx.fields` on API and exit 2 on CLI, same text; no catalogue row refused | kernel-free | `make test PYTEST_ARGS="tests/test_fine_pitch.py tests/test_turn_guard.py -q -n0 --no-cov"` | new file |
| SC1 proof grid | every point of the committed grid is `ok` in the committed runner records or refused by the model | records-driven, kernel-free (the `tests/test_oper_pitch.py` pattern) | `make test PYTEST_ARGS="tests/test_oper_fine.py -q -n0 --no-cov"` | new file |
| SC1 constants | shipped thresholds, ceilings and `FINE_ENVELOPE` equal what the judge/emit code writes from `bench/results/phase-08/` | records-driven | `make test PYTEST_ARGS="tests/test_cost.py tests/test_oper_fit.py tests/test_oper_pitch.py -q -n0 --no-cov"` | extend |
| SC1 debt | the 20 in-wall parts stay 422 `pitch_too_fine` (already pinned), debt file moved to `resolved/`, INDEX row moved | existing + grep | `make test PYTEST_ARGS="tests/test_fine_pitch.py -q -n0 --no-cov"` | exists |
| SC2 | `export` help or README carries the no-deadline line; L-entry exists | text assertion | `make test PYTEST_ARGS="tests/test_cli.py -q -n0 --no-cov"` | extend |
| SC3 | `REQUIREMENTS.md` TABL-06 text names the printed fields; no code change | grep | `grep -n "TABL-06" .planning/REQUIREMENTS.md` | n/a |
| SC4 | the d=30 pitch=2 s=48 k=18 part with a typed `thread_length=20` is a 422 `over_budget` / exit 2 on API and CLI, and the page's source writes a touched field | API+CLI executed, web by source assertions | `make test PYTEST_ARGS="tests/test_parity.py tests/test_cost.py -q -n0 --no-cov"` | extend |
| SC5 | `04-11-SUMMARY.md` or `04-13-SUMMARY.md` has `requirements-completed: [INFO-05]`; both VALIDATION.md read `status: validated`; audit reads `passed`/`tech_debt` | grep + the workflow | `grep -n "requirements-completed" .planning/phases/04-iso-hex-bolts-and-screws/04-13-SUMMARY.md` | n/a |

Kernel tests are not marked: they run inside `make verify` under xdist (`-n 8` clamped to the host). The only slow markers are `grid` and `pair`, deselected by default; do not put the proof grid there. Keep kernel-built tests to about 10 builds of 2 to 5 s; the wide grid is proven by committed runner records.

**No browser harness exists** (`tests/test_parity.py` docstring: "It holds no browser (L01): the UI is checked by reading `app.js` and `style.css` as text"). The parity test cannot drive the form. D-13's honest form: execute API and CLI on the INT-03 part (kernel-free, shown above), and pin the web side with source assertions that `partQuery` writes a touched field and that `touched` is set by the `input` event, `pick()` and `navigate()`. Do not add a node-based test unless the owner wants a new harness (it needs `node` on every `make verify` host).

### Sampling Rate
- **Per task commit:** the targeted quick command for touched files, plus `make lint typecheck lint-imports` for `calc`, `params`, `bench` edits.
- **Per wave merge:** `make verify`.
- **Phase gate:** `make verify` green, `python -m bench.oper_sets --check` clean, runner records committed, then `/gsd-validate-phase 6`, `/gsd-validate-phase 7`, `/gsd-audit-milestone`.

### Wave 0 Gaps
- [ ] `tests/test_turn_guard.py` (API 422 shape, CLI exit 2, catalogue untouched)
- [ ] `tests/test_oper_fine.py` (proof grid against committed records; constants against the judge)
- [ ] kernel cells for the island and the 25 mm debt example in `tests/test_nut.py` / `tests/test_solid.py`
- [ ] `bench/oper_lift.py` lift for the guard before any set is regenerated
- [ ] a Phase 8 sweep protocol (rules before data), and the walk and re-sweep point files

## Security Domain

`security_enforcement` is enabled (ASVS level 1).

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | no accounts |
| V3 Session Management | no | none |
| V4 Access Control | no | none |
| V5 Input Validation | yes | the pydantic model boundary: the guard is one more validator; the repeated-key and explicit-conflict rules stay at the request boundary; the web builds nodes from text only (`test_the_ui_builds_nodes_from_text_only`) |
| V6 Cryptography | no | none |

### Known Threat Patterns
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Resource exhaustion by a part the model admits but the kernel cannot build | Denial of service | the guard (kernel-free 422) plus the cost model and `BUILD_TIMEOUT_S` backstop; the fine envelope keeps fine-sweep parts inside the budget |
| Workflow input injection through `set` | Tampering | `operability.yml` passes `set` only through an environment variable; `bench.oper matrix` checks `[a-z0-9-]+` and an existing file (unchanged; pinned by `tests/test_oper.py`) |
| Token scope on hand-dispatched runs | Elevation | `permissions: contents: read`, no secrets (unchanged) |
| An unbounded CLI build | Denial of service (local) | accepted by D-09: the CLI runs on the user's own machine; the cost gate still refuses over-budget parts |

## Sources

### Primary (HIGH confidence)
- Repo files read this session: `src/screw/solid/helical.py`, `solid/__init__.py`, `solid/bolt.py`, `solid/nut.py`, `solid/pair.py`, `params.py`, `calc/thread.py`, `calc/cost.py`, `cli.py`, `app.py`, `static/app.js`, `tables/presets.py`; `bench/oper_sets.py`, `oper_fit.py`, `oper_lift.py`, `oper_child.py`, `.github/workflows/operability.yml`; `tests/test_fine_pitch.py`, `test_oper_pitch.py`, `test_cost.py`, `test_runtime_bounds.py`, `test_parity.py`, `test_grid.py`.
- `docs/architecture/decision_log.md` L19, L21, L25, L32, L33 (verbatim sections), `docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md`, `.planning/debug/resolved/in-wall-kernel-builderror.md` (E1 to E32, Resolution), `.planning/v1.0-MILESTONE-AUDIT.md`, `.planning/REQUIREMENTS.md`.
- Committed runner records: `bench/results/phase-07/walls-pitch-41074314305/` (counts by q read this session), `bench/RESULTS.md` (`### dense-band, run 41153581470`, `### R31's walls ...`).
- OCP docstring for `BRepOffsetAPI_MakePipeShell.SetTolerance` (local `.venv`).

### Secondary (MEDIUM confidence)
- Local probes on macOS arm64, development evidence only (D-04), scripts in `/tmp/p8` (not committed): island 6/6 shipped refused and 6/6 fine ok; bolt cells 30/48 shipped refused and 48/48 fine ok; nut grid d/p 6.25 to 8 fine 288/288 ok and shipped 108/108 ok at 6.25 to 6.75; catalogue nuts M5 to M20 sizes; shipped-sweep turn ceilings at d 2 and 3, d / pitch 6, 7, 8.

### Tertiary (LOW confidence)
- The scratch `iw/` scripts of the debug session (outside the repo, transient) for the exact variant call.

## Bookkeeping, contract fixes and decision-log facts (items 6 to 10 of the brief)

**INT-01 (D-09).** `cli.cmd_export` (`src/screw/cli.py:151`) imports `solid.export` after the kernel-free `download_refusal` check and runs it in-process; no code change. Add: a README "Use" line next to `.venv/bin/screw export bolt --d 8 -o bolt.stl` (README lines 25 to 30), and the subparser help at `cli.py:245` (`help="write an STL or STEP file"`; no test pins that string, grep found none). The new Lxx (next free id **L34**, `## L34 — ...`, parsed by `^## (L\d\d) ` in `tests/test_runtime_bounds.py`) records the three reasons of D-09 and cites L24 and the WR-03 note.

**INT-02 (D-10).** TABL-06 text, `.planning/REQUIREMENTS.md:42`: `"custom, based on ISO 4017 M6 × 20" once any field is edited.` The row fields the badge compares are d, pitch, length, s, k, thread_length (`tables/presets.py`); handedness and `head_chamfer` are not in a row. L19 (`decision_log.md` around 1496): "A preset never sets the angle and `match` ignores it: no row prints an angle". Amend the REQUIREMENTS text only; also note the nut row (d, pitch, s, m) if the sentence names fields.

**INT-06.** The debt file says the 422 "names no field"; fix that sentence when moving it to `docs/tech_debt/resolved/` with `Status: resolved`, the commit sha, and the INDEX row moved in the same commit (CLAUDE.md flow). INDEX row to move: `docs/tech_debt/INDEX.md` line 19.

**Decision-log entry format** (L25, L32 read): `## L34 — <title>`, `Date:`, who decided and the rulings cited, bold-lead paragraphs (**The rule.**, **What it refuses.**, **What moves.**, **What it leaves open.**), `Reason:` and `Reversibility:` lines. State "Supersedes in part L25 (walls/guard), L19 and L21 (the sentences about what the page writes)" and "supersedes nothing else". One entry may carry the sweep, guard and typed-default decisions, or split into L34 (sweep and guard), L35 (CLI deadline), L36 (typed default); the owner's D-08/D-09/D-11 name "a new Lxx" each, so splitting is cleaner.

**Bookkeeping (D-14).** `04-11-SUMMARY.md:46` and `04-13-SUMMARY.md:53` both read `requirements-completed: []` (04-13 with a comment that phase.complete reconciles traceability). 04-11's plan lists INFO-05 (`04-11-PLAN.md:14`) and built the wrench note; set `requirements-completed: [INFO-05]` there (and optionally 04-13). `06-VALIDATION.md` frontmatter is `status: draft`, `nyquist_compliant: false`, `wave_0_complete: false`; `07-VALIDATION.md` is `status: validated`, `nyquist_compliant: false` with the comment "OPER-03 is Pending by owner ruling" at line 7 and the unchecked line 144. After OPER-03 holds, `/gsd-validate-phase 7` can set it true; `/gsd-validate-phase 6` needs its Wave 0 boxes read against the code. Both commands are gsd workflows, not scripts.

**Cost model constants, what `make verify` pins.** The `# BEGIN emit-constants` block in `calc/cost.py` is asserted verbatim against `bench.oper_fit.emit_constants(fit.json, 07-OWNER-RULINGS.md, bands, min_turns, headroom)` (`tests/test_cost.py::test_the_shipped_constants_are_the_block_emit_constants_writes_from_the_evidence`). A `FINE_ENVELOPE` must be added to `emit_constants`, with its own committed JSON under `bench/results/phase-08/`, and its test. Existing widening is recorded in `fit.json["widened_by"]` (runs 40909768713, 41206999278) and checked by `tests/test_oper_fit.py`; do not touch `fit.json` for the fine region.

**Re-sweep population (counted this session from `bench/points/*.json`, labels the production model admits):** explore has 20 bolt labels with d / pitch above 8 (d 1, 3, 10, 30, 100 at d / pitch 8.57 to 10, n3 and n30, both hands) and 8 nut labels above 6 (iso4032 M5, M8, M10, M12, M14, M16, M18, M20); `full` has the same 8 nut rows; spread has 1 nut label above 6 and no bolt. Three of these bolts (d 30 n30, d 100 all) are step-only today. A useful fine set is these labels at three artifacts plus corners the explore set lacks: bolts at d / pitch 12 and 20 with d 1 to 100, nuts at 6.25, 7, 8 across d 0.8 to 20, and 5 repetitions on a handful to feed R12's cold-isolated rule.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, no new packages.
- Architecture (seams, files, contracts): HIGH, every seam read in this session.
- Kernel behaviour and thresholds: MEDIUM, local reproduction matches the debug session exactly where they overlap (M20 nut STEP 2816455 B in both), but the runner decides.
- Cost envelope shape: MEDIUM-LOW until the fine readings exist (A3).
- Pitfalls: HIGH for the repo-structure ones (1, 2, 5 to 9), MEDIUM for 3 and 4.

**Research date:** 2026-11-02
**Valid until:** 2026-11-30, or until `helical.py`, `params.py` validators or `operability.yml` change.
