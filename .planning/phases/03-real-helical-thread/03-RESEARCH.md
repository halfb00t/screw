# Phase 3: Real Helical Thread - Research

**Researched:** 2026-10-10
**Domain:** moving a measured CadQuery/OCCT helical-thread builder and its kernel-free maths from `bench/` into `src/`, gating every build, and wiring one new boolean field through the registry, API, CLI and web form
**Confidence:** HIGH on the move, the gate, the cap functions, the front-end wiring and every kernel behaviour quoted below (each was run against the installed pair this session); MEDIUM on slow-tier runner timing and on how far the tiny-input findings generalise (probed on 3 to 13 rows, not a grid)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Caps: L11's turn caps applied to arbitrary (d, pitch, length)**
- **D-01:** `length / pitch > 250` is a `422` naming `length` and `pitch`, validated once at the
  params boundary and never reaching the pool. 250 is L11's construction cap: the frontier walk
  (`2026-10-08-a-frontier`) reached 250 turns with no stop at every size, both hands, rod and
  void; above it nothing is measured. Not cap-and-warn: trimming `length` builds a part the
  user did not ask for. The INTERIM 30 s timeout stays the backstop below the cap.
  — **Reversibility:** reversible — one constant and one validator; Phase 7 replaces it with
  measured per-size caps (OPER-03) and the comment cites the run that set it.
- **D-02:** L11's per-size bytes cap gates the fine STL only. `GET /api/bolt/model.stl?quality=fine`
  and `screw export --quality fine` for a row above its cap are refused (`422` on the API, an
  error exit on the CLI) naming `length`, the cap in mm and in turns, and the run id
  `2026-10-08-a-grid`. Info, preview STL and STEP build at the asked length — none of them was
  over budget. Verified 2026-10-10: `app.py:72` serves an over-budget blob but never caches it,
  so without this rule every repeat request rebuilds it until the timeout. One kernel-free rule
  used by both front ends (parity).
- **D-03:** The bytes cap fires only when `(d, pitch)` equals one of the seven measured L11 rows
  (M8 67.5 mm / 54 turns, M10 56 / 37.33, M12 60 / 34.29, M14 58 / 29, M16 52 / 26,
  M18 65 / 26, M20 64 / 25.6). An off-row `(d, pitch)` gets the 250-turn cap alone and its fine
  STL is served uncached as today: a cap from a mapping nobody measured is the plausible number
  L02 forbids. The row table lives in kernel-free code, labelled "L11 measured rows
  (`2026-10-08-a-grid`), not ISO rows", one run id per row; it is bench evidence, not a `tables`
  module, and does not pre-empt contract 6. The pitches are the campaign's keys (ISO 262
  preview values, UNVERIFIED as table truth, exact as run keys).

**Pitch validity at the params boundary**
- **D-04:** The only new `(d, pitch)` refusal is geometric: `d/2 - 5H/8 <= 0` with
  `H = (sqrt(3)/2) * P` (the basic-profile root radius, from the coefficients the owner
  confirmed at the 02 D-01 checkpoint; zero at `pitch ≈ 0.9238 d`) is a `422` naming `d` and
  `pitch`. Everything else builds: no measured-band restriction, no ISO 262 coarse check (Phase
  4; contract 6 forbids `params` reaching `tables`). The THRD-04 gate catches a wrong solid and
  the INTERIM timeout bounds cost. This closes 01 D-07's open `pitch >= d` question. No lower
  bound on `length` or `d` is added: the gate refuses a collapsed solid by its volume (D-08),
  which is honest where an INTERIM minimum would be a number nobody measured; sub-turn lengths
  (`length < pitch`) build (02 R2 built 0.8-turn rows ok).

**Info panel after the skeleton**
- **D-05:** Rows: `d`, `pitch`, `length`, `turns` (= `length / pitch`), `volume` (the thread
  closed form `section_area(d, P) * length`, the spike oracle, never the kernel's `Volume()`),
  `thread depth` (`5H/8`) and `minor diameter` (`d - 5H/4`), the last two labelled
  "ISO 68-1:2023 basic profile" — they are the two radii the builder literally uses. The pitch
  diameter `d2` waits for Phase 5 (INFO-01) and the ISO 724 read. The skeleton withheld `turns`
  because it had no thread; it is honest now.
- **D-06:** `SKELETON_WARNING` is removed (SC1). A new standing warning takes its place on every
  bolt info document, text pinned: `threaded rod: no head, plain-cut thread ends; not a product
  build`. Asserted on the API and the CLI by the parity/records tests, as D-06 of Phase 1 was.
  Phase 4 rewrites it when the head lands; Phase 6 removes it at release.
- **D-07:** The hand is not an info row. `InfoRow.value` stays a float (01 D-15); `left_hand`
  is visible where the user set it — the form, the URL hash, the CLI flag — and in the preview.

**The gate (THRD-04) and the blocker it closes**
- **D-08:** The postcondition lives in `screw.solid`, inside the function `lru_cache` wraps
  (today `_build_checked`), so a rejected build is never cached and never exported:
  `isValid()`, exactly one solid, and `precise` volume versus `calc.thread`'s closed form inside
  `T_gate = 9e-05` with the signed relative error in the message. The positive-control test
  feeds the gate L11's known-bad rows through `bench.thread_spike.helical.naive_sweep_fuse`
  (one solid, `isValid()` true, volume below half the closed form) and sees `BuildError`; the
  planner picks a cheap subset of the fifteen. The same change treats `exportStl()` returning
  `False` and a non-`IFSelect_RetDone` STEP status as `BuildError` and checks the STL header
  triangle count against the byte length before serving. This resolves
  `docs/tech_debt/active/2026-10-06-collapsed-thin-solid-served-as-200.md` (blocker): the
  item moves to `resolved/` with its INDEX row in the fixing commit. — **Reversibility:**
  costly — every later kind's builder runs through this gate; loosening `T_gate` needs a
  superseding entry and a re-run of the grid block (L11).

**`left_hand` on the three front ends**
- **D-09:** `left_hand: bool = False` on the shared `FastenerParams` base, not on `BoltParams`:
  THRD-01 threads every part and TYPE-04 derives the nut from the same `d`, pitch and hand. The
  default is frozen (L02): the hash writes `left_hand=true` only when set, an omitted key means
  right-hand forever. UI: the checkbox branch of the schema form (01 Claude's Discretion). CLI:
  `argparse.BooleanOptionalAction` (`--left-hand` / `--no-left-hand`). API: pydantic's bool
  parsing on the query model. The parity test covers the boolean branch through the registry,
  and the `app.js` source assertion (no field-name literal) still holds.
  — **Reversibility:** one-way — a field on the base and in the hash is part of every shareable
  link from this phase on.
- **D-10:** A shareable link naming a key the kind does not define is refused by the page,
  naming the keys, exactly like the unknown-kind case: parity with the API's `422` and the
  CLI's exit 2 (SC2 of Phase 1, now true on all three front ends). Resolves
  `docs/tech_debt/active/2026-10-06-ui-drops-foreign-hash-keys.md`; amend `01-UI-SPEC.md`
  § Interaction Contract rule 10 and pin it in a test in the same change.
- **D-11:** A failed update (422, 503, network) keeps the last rendered info document's
  warnings visible below the error paragraphs while its mesh stays on screen; they clear only
  when the mesh is cleared or replaced. Resolves
  `docs/tech_debt/active/2026-10-06-ui-hides-warnings-on-failed-update.md`; amend
  `01-UI-SPEC.md` rules 15 and 24 in the same plan.
- **D-12:** A repeated query key is a `422` `{"loc": ["query", name], "type": "duplicate"}`
  refused before validation; a repeated CLI flag exits 2 naming it (an `argparse.Action` in the
  same flag generator change that adds `BooleanOptionalAction`); one parametrised test over the
  registry on both front ends. Resolves
  `docs/tech_debt/active/2026-10-06-repeated-query-key-silently-wins.md`.

**Module moves and the harness precondition**
- **D-13:** `src/screw/calc/thread.py` takes the profile maths from
  `bench/thread_spike/maths.py` (`fundamental_height`, `thread_depth`, `section_radius`,
  `section_area`, `closed_volume`; the grid, frontier and preset helpers stay in `bench`).
  `src/screw/solid/helical.py` takes `section`, `twist` and `thread` from
  `bench/thread_spike/helical.py` with K = 3 as the default (L11); `naive_sweep_fuse`,
  `one_pipe`, `trim_tip` and `ruled_reference` stay in `bench` (controls and evidence, not
  product). The spike then imports both back (02 D-18). Import-linter already covers the new
  modules: contract 2 (`screw.calc` never imports the kernel) and contract 8 (`screw.solid.**`
  is the doorway); the bench contract keeps `bench.thread_spike.maths` kernel-free through
  `screw.calc.thread`.
- **Precondition (owner, 2026-10-10):** the harness review debt
  (`docs/tech_debt/active/2026-10-09-thread-spike-harness-review-findings.md`, must) fires on
  the first PR touching `bench/thread_spike/` or `bench/quiet.py`. It is settled in a separate
  `/gsd-quick` PR that lands on `main` **before** the Phase 3 PR: WR-01, WR-02, WR-04, WR-05
  with tests; WR-03 put to the owner as a protocol amendment; IN-01 to IN-07 triaged; the
  `02-REVIEW-DISPOSITION.md` ledger updated. Phase 3's import-back is then a pure move. The
  planner lists that PR as the phase's precondition and does not fold the fixes in.

**Slow tier and the `make verify` sample**
- **D-14:** The slower tier is a separate workflow file, `.github/workflows/grid.yml`, on
  `workflow_dispatch` plus a weekly schedule, running a pytest marker (name is the planner's)
  over the spike's D-03 corpus — 15 sizes, every integer-mm and integer-turn length up to
  min(10 d, 200 mm), both hands, rod and void — through the same gate against the closed form.
  It is **not** in `.github/workflows/required-jobs.txt`: L08's "every job in `ci.yml` is
  required" stays true because the grid is not in `ci.yml`; the planner verifies
  `tests/test_pr_land.py`'s job-name check reads `ci.yml` only. The corpus is the measured one
  and is never re-picked to flatter a result (`bench/README.md` corpus rule). `make verify`
  carries a sample the planner picks: at least the default `M6 × 20` right-hand rod, one
  left-hand rod, one void at the spike's 0.20 mm clearance, one sub-turn and one non-integer-turn
  length, and the positive control of D-08. — **Reversibility:** reversible — a workflow file.

**Decision entry**
- **D-15:** A new `L12` in `docs/architecture/decision_log.md` records this phase's choices that
  later phases build on: the cap mechanism (D-01 to D-03, the reading of L11's "cap-and-warn"
  as refuse-for-one-artefact), the geometric pitch bound (D-04), the gate placement and export
  checks (D-08), the standing warning (D-06) and the slow tier (D-14). It cites L11's run ids
  and measures nothing new. The planner lands it in the same PR.

**Thread ends**
- **D-16:** Both ends are plain planar cuts at `z = 0` and `z = length`, as every measured spike
  row was (`2026-10-08-a-grid`). No fade, no chamfer: ISO 4753 is unread (THRD-05, Phase 5) and
  an invented end is the plausible number L02 forbids. The bounding box is `d × d × length`.

### Claude's Discretion
- Exact turns from float fields: the spike's `thread()` takes an exact `turns` and never
  re-derives it from `length / pitch` (RESEARCH Pitfall 1: 168 of 3000 float `k·P` products
  drift). The product has `length` and `pitch` as floats; the builder's end face must sit at
  `z = length` exactly, not at `turns * pitch`. The researcher states how (e.g. the builder
  takes `length` and places the remainder segment to end at `length`); the planner tests a
  non-integer-turn length and an integer-turn length whose float product drifts.
- Where the kernel-free rules live (`calc/thread.py`: the root-radius bound, the 250-turn
  cap, the L11 row table and the fine-STL cap rule), and how `params` reaches them (the lazy
  import inside the validator, the spur pattern 01 used) and how `app._serve` and `cli export`
  share the one cap function.
- `422` and error message wording beyond what D-01 to D-04 and D-12 name; the `unit` string
  for the `turns` row.
- `TESSELLATION` stays at the INTERIM presets; Phase 5 (FRNT-06) re-chooses against the
  clearance, with the decisive `2026-10-08-a-ladder` block as its evidence.
- The `make verify` sample beyond D-14's minimum, the pytest marker name, grid sharding across
  a job matrix (GitHub's per-job limit is below a serial full-grid run), and whether the
  coverage floor is re-measured after the suite grows (L34 rule: never a round number).
- `solid/bolt.py` keeps its name and becomes the bolt-kind assembly over `helical.thread`
  (nothing but the rod in this phase).
- The phase branch: `gsd/phase-03-real-helical-thread`, cut from `main` at `a0c7923`.

### Deferred Ideas (OUT OF SCOPE)
- Pitch diameter `d2 = d - 3H/4` as a panel row — Phase 5 (INFO-01), after ISO 724:2023 is read.
- A `warnings` line when `pitch / d` falls outside the measured 0.125–0.2 band — not adopted;
  Phase 7's full-grid sweep (OPER-03) replaces the question with measured caps.
- Mapping an off-row `d` to the nearest ISO size's bytes cap — rejected (unmeasured mapping).
- Tip chamfer and head-side fade (PITFALLS C10, THRD-05) — Phase 5; ISO 4753 unread.
- Preview and fine mesh presets chosen against thread depth and clearance (FRNT-06) — Phase 5,
  using the decisive `2026-10-08-a-ladder` block.
- Measured per-size caps replacing the 250-turn and bytes caps — Phase 7 (OPER-03).
- WR-03 (quiet-gate re-read during a block) as a protocol amendment — the owner's call in the
  harness `/gsd-quick` PR, not here.
- A text-valued `InfoRow` variant — not adopted; revisit only if a later kind needs a
  non-numeric fact on the panel.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| THRD-01 | Every threaded part carries a real helical ISO metric coarse-pitch thread (ISO 68-1:2023 basic profile); no cosmetic or unthreaded option | The builder move (`solid/helical.py`), the length-space segmentation with tail fold (Pattern 1), `solid/bolt.py` becoming `helical.thread(d, pitch, length, left_hand)`; tests: Validation map rows T1 to T4 |
| THRD-02 | Boolean `left_hand` (default right-hand) on all three front ends; a left-hand part passes the same checks | `left_hand` on the base class, the three front-end mechanisms verified by running them (Patterns 5 to 7), and the independent handedness probe (Pitfall 9: the volume gate cannot see the hand) |
| THRD-04 | Every thread build gated: valid shape, one solid, volume within a stated tolerance of the closed form (sign included); `BuildError` naming what failed; positive-control test | Gate placement inside `_build` (Pattern 2), the NaN-safe comparison, two verified positive controls (naive sweep and the inverted one-pipe solid), the export-status and STL-header checks (Pattern 3) |
</phase_requirements>

## Summary

This is a move-and-wire phase and the evidence says it is safe to do as CONTEXT decided, with one builder-level
addition the CONTEXT did not know about. The spike's `section`, `twist` and `thread` and the profile maths move
verbatim into `src/screw/solid/helical.py` and `src/screw/calc/thread.py`. Re-built from the installed pair
(cadquery 2.8.0, cadquery-ocp 7.9.3.1.1, the pair L11 names), 527 grid rows across six (size, hand, kind) cells
(M2.5 void, M3.5 rod and void, M4 left rod, M6 rod, M10 rod) all came back one valid solid inside 7.1e-06 of the
closed form, a factor 12.7 inside `T_gate`, with both end faces within the 1e-7 mm kernel box gap of `z = 0` and
`z = length`.

The one discovery that changes the plan: **the spike's `thread()` is only safe because its caller passes an exact
integer-turn count.** Handed a float `length`, a tail of a few ulps (0.9e-15 mm at `length = 5.4`, `pitch = 0.6`)
makes the remainder segment a degenerate pipe and the kernel dies with SIGSEGV (return code -11, no exception, no
`BuildError`). In the 3750 integer-turn rows of the 15 sizes up to 250 turns, 130 land on such a positive tail when
the segmentation is done in length space and 56 when turns are re-derived by float division. The builder must
therefore fold any tail shorter than a small absolute length into the previous segment so the pieces still end at
exactly `z = length` (Pattern 1). The same SIGSEGV happens for a whole part shorter than about 1e-8 mm, which
conflicts with D-04's "no lower bound, the gate refuses a collapsed solid": the gate never runs on a crashed
process. This needs an owner ruling (Open Question 1); the recommended default is a doorway guard that raises
`BuildError`, not a params bound.

Everything else is mechanical and was verified by running it: the import-linter change (contract 8 needs
`screw.solid.** -> OCP`, and `screw.solid -> OCP` only if `solid/__init__.py` itself imports OCP), the
`PydanticCustomError` shape that the existing `app.js` already highlights (`ctx.fields`), the app-level
duplicate-key dependency that preempts validation, the `BooleanOptionalAction` plus once-only `Action` (mypy
`--strict` clean), `-m 'not grid'` in `addopts` with `-m grid` on the command line, and the `exportStl`/`exportStep`
failure returns. Baseline before any change: `make verify` green on this branch, 695 passed in 37.96 s, coverage
95.56 % against the 94 floor.

**Primary recommendation:** Move the spike code as two modules; make `thread()` take `length` in millimetres,
segment in length space with a 1e-3 mm tail fold and a doorway guard, run the gate (valid, one solid, NaN-safe
signed `precise` volume inside 9e-05) inside `_build` before the `lru_cache`, put every rule (root bound, 250-turn
cap by exact decimal arithmetic, L11 row table, fine-STL cap, volume check) in kernel-free `calc/thread.py`, and
get an owner ruling on the tiny-length crash before planning the params validators.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Profile maths, closed volume, volume check, caps, L11 row table | `screw.calc.thread` (kernel-free) | `screw.params` (lazy import in validators), `screw.app`/`screw.cli` (fine-STL rule) | Runs per keystroke and is the oracle the kernel is judged by; contracts 2 and 4 forbid kernel and logger |
| `422` on turns, root radius, repeated key | `screw.params` validators; app-level dependency for repeated keys | CLI `argparse` Action for repeated flags | Validated once at the model boundary (AGENTS.md code style); a repeated key is a parsing fact the model never sees |
| Helical solid construction | `screw.solid.helical` (kernel) | `screw.solid.bolt` (kind assembly) | `screw.solid` is the only doorway to `cadquery`/`OCP` (contract 8) |
| Build postcondition (THRD-04) and export-status checks | `screw.solid` (`_build`, `_write_export`) | `screw.calc.thread.volume_check` (pure comparison) | Inside the `lru_cache`d function so a raise is never cached; bytes cache stores only successes (`app.py` `_serve`) |
| Fine-STL refusal | `screw.calc` (dispatch like `derive`) called by `app._serve` and `cli.cmd_export` before any build | Info document warning (recommended) | Same rule on both front ends, no kernel needed, never reaches the pool |
| `left_hand` checkbox, hash round trip, foreign-key refusal, warnings on failure | `static/app.js` (browser) | `/api/schema` supplies `type: boolean` | The page reads everything off the schema (test_parity pins no field literal) |
| Slow grid tier | `.github/workflows/grid.yml` + pytest marker | `Makefile` target (optional) | Outside `ci.yml` so L08's required-jobs equality is untouched |

## Standard Stack

### Core
No new runtime or dev dependency. Everything is already installed and pinned by `requirements.txt` (L06).

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| cadquery | 2.8.0 | `cq.Solid`, `cq.Wire.makeHelix`, `exportStl`/`exportStep` | L01; the pair L11 measured [VERIFIED: `.venv/bin/python -c "from importlib.metadata import version"` this session] |
| cadquery-ocp | 7.9.3.1.1 | `BRepOffsetAPI_MakePipeShell`, `BRepBuilderAPI_Sewing`, `BRepGProp`, `IFSelect_ReturnStatus` | The binding the spike used; same pair as L11 "Conditions of the record" [VERIFIED: same command; decision_log.md L11] |
| pydantic | 2.13.5 | `model_validator(mode="after")`, `PydanticCustomError`, bool lax parsing | The params boundary (L01) [VERIFIED: importlib.metadata] |
| fastapi | 0.142.2 | app-level `dependencies=[Depends(...)]` that preempts query validation | Existing app [VERIFIED: importlib.metadata; behaviour verified by running, scratchpad `e10.py`] |
| argparse (stdlib, Python 3.12.15) | 3.12 | `BooleanOptionalAction`, once-only `Action` | Locked by D-09, D-12 |
| pytest + pytest-xdist 3.8.0 + pytest-cov 7.1.0 | as `pyproject.toml` | marker `grid`, `-m` override | Existing gate |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `fractions.Fraction` (stdlib) | 3.12 | Exact decimal reading of float fields: `Fraction(repr(x))` | The 250-turn cap and the `turns` row (Pitfall 2) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `Fraction(repr(length)) > 250 * Fraction(repr(pitch))` | `length / pitch > 250` | Float division wrongly refuses the measured M4 250-turn row (175 mm, 0.7 mm): `175.0/0.7 > 250` is True [VERIFIED: probe `e-table` this session] |
| One `thread(d, pitch, length)` | Keep spike `thread(turns)` plus a wrapper | Two entry points; the spike would then not measure the shipped path. Rejected (simplicity, D-13 "what was measured is what ships") |
| Doorway guard (`BuildError`) for tiny length | A `gt=` bound in `params` | D-04 says no lower bound at the params boundary; the guard keeps the letter of D-04 and stops the SIGSEGV (Open Question 1) |

**Installation:** none. `make venv` already provides the environment; `.venv` exists and `make verify` ran green.

**Version verification:** the installed pair equals the pair named in L11 ("cadquery 2.8.0, cadquery-ocp 7.9.3.1.1").
No package is added, so no registry lookup applies. [VERIFIED: importlib.metadata this session]

## Package Legitimacy Audit

No external packages are installed or added by this phase (the builder, gate, rules and tests use the installed
cadquery/OCP, pydantic, FastAPI, argparse and pytest). The `gsd_run query package-legitimacy check` gate has
nothing to check.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| (none) | — | — | — | — | — | — |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## L11 Values the Code Must Carry (read from the source of truth this session)

Quoted verbatim from `docs/architecture/decision_log.md`; each constant in code cites the run id beside it.

- Construction, lines 297-300: "The sewn twist-section, segment length K = 3 turns, selected by the K rule over `2026-10-08-a-ksweep` (`### 2026-10-08-a-verdict`, K section; all three K qualified and K = 3 had the fewest fine triangles at the standard max). Sewing tolerance 1e-4 mm, `MAX_SEGMENTS` 500 and 14 section samples per flank are protocol inputs labelled MEASURED-PRIOR (research probes), not campaign results".
- Cap, lines 300-302: "The frontier walk (`2026-10-08-a-frontier`) reached 250 turns with no stop for all 15 sizes and both hands".
- Estimator and gate, lines 311-315: "`BRepGProp.VolumeProperties_s` at eps 1e-6 (`precise`), never the default `Volume()`" ... "the shipped gate is `T_gate` = 9e-05 (`GATE_FACTOR` 10 times the winner's largest error, rounded up to one significant figure)".
- Bytes-cap rows, lines 334-340 (column order: size, construction cap, bytes cap mm, bytes cap turns, first row over budget, seconds cap):
  - `| M8 | 250, no stop up to 250 turns | 67.5 | 54 | M8 right L=68 rod | not established |`
  - `| M10 | 250, no stop up to 250 turns | 56 | 37.3333 | M10 right L=57 rod | not established |`
  - `| M12 | 250, no stop up to 250 turns | 60 | 34.2857 | M12 right L=61 rod | not established |`
  - `| M14 | 250, no stop up to 250 turns | 58 | 29 | M14 right L=59 rod | not established |`
  - `| M16 | 250, no stop up to 250 turns | 52 | 26 | M16 right L=53 rod | not established |`
  - `| M18 | 250, no stop up to 250 turns | 65 | 26 | M18 right L=66 rod | not established |`
  - `| M20 | 250, no stop up to 250 turns | 64 | 25.6 | M20 right L=65 rod | not established |`
  - Store `(d, pitch) -> cap_mm` only; derive turns as `cap_mm / pitch` (67.5/1.25 = 54, 56/1.5 = 37.333, 60/1.75 = 34.2857, 58/2 = 29, 52/2 = 26, 65/2.5 = 26, 64/2.5 = 25.6, all equal to the printed column). The keys `(8.0, 1.25)`, `(10.0, 1.5)`, `(12.0, 1.75)`, `(14.0, 2.0)`, `(16.0, 2.0)`, `(18.0, 2.5)`, `(20.0, 2.5)` come from `bench/thread_spike/maths.py` `PITCH` (secondary-source ISO 262 values, "UNVERIFIED until Phase 4's row tests"; exact as run keys) and are exactly representable floats. The budget they were measured against is "the INTERIM fine preset (0.01 mm, 0.1 rad) with gzip level 1" over "the INTERIM 64 MiB budget".
- Known-bad inputs, lines 358-364: "(d=2.0, pitch=0.4, length=4.0), (2.0, 0.4, 10.0), (2.0, 0.4, 20.0), (2.5, 0.45, 4.5), (2.5, 0.45, 10.0), (3.0, 0.5, 10.0), (6.0, 1.0, 10.0), (8.0, 1.25, 10.0), (8.0, 1.25, 80.0), (10.0, 1.5, 10.0), (10.0, 1.5, 100.0), (16.0, 2.0, 10.0), (20.0, 2.5, 10.0), (20.0, 2.5, 20.0), (20.0, 2.5, 200.0)", recipe "`naive_sweep_fuse(d, pitch, length)` in `bench/thread_spike/helical.py`".
- Void clearance for the sample: `bench/thread_spike/maths.py:59` `VOID_CLEARANCE = 0.20`. Presets: `maths.py:76` `INTERIM_PRESETS: dict[str, tuple[float, float]] = {"preview": (0.08, 0.5), "fine": (0.01, 0.1)}` (equal to `screw.solid.TESSELLATION`, pinned by `tests/test_bench.py`).
- Builder constants to move with their comments, `bench/thread_spike/helical.py:27,30,33`: `SECTION_SAMPLES = 14`, `MAX_SEGMENTS = 500`, `SEWING_TOLERANCE = 1e-4`.
- `bench/thread_spike/measure.py:28` `PRECISE_EPS = 1e-6`; relative error is `verdict.relative_error`: "Signed: measured / closed - 1. An inverted solid reads about -2, which sign keeps."

## Architecture Patterns

### System Architecture Diagram

```
 request (UI hash | API query | CLI flags)
        |
        v
 [duplicate key / repeated flag refusal]            app-level Depends | argparse Action   -> 422 / exit 2
        |
        v
 [FastenerParams / BoltParams validation]           screw.params
    field checks (gt, le, finite, bool)  --> lazy import --> screw.calc.thread rules:
    root radius d/2 - 5H/8 <= 0   -> 422 (d, pitch)
    exact-decimal turns > 250     -> 422 (length, pitch)
        |
        +---------------- info -----------------> calc.derive -> rows (d, pitch, length, turns, volume,
        |                                                         thread depth, minor diameter) + standing warning
        |                                                         (+ fine-STL warning when the cap rule fires)
        v
 [fine STL cap rule]  calc.fine_stl_refusal(p)  only for fmt=stl, quality=fine, (d, pitch) on an L11 row
        |  refuse -> 422 (API) / exit 2 (CLI)    -- before any build, before the pool
        v
 [app: bytes cache lookup, admission slot]  -> BuildPool worker (spawned process)     (CLI: in process)
        |
        v
 screw.solid._build_cached = lru_cache(_build_checked)
        _build:  bolt.rod(p) -> helical.thread(d, pitch, length, left_hand)
                      |  length-space segments, tail fold, sewn, no boolean
                      v
                 GATE: isValid, one solid, precise volume vs calc.thread.closed_volume, |rel| <= T_GATE (NaN-safe)
                      | raise BuildError  (never cached, never exported)
                      v
        _write_export (mesh a copy): exportStl False / STEP status != RetDone / STL header != 84+50n  -> BuildError
        |
        v
 bytes -> app puts only a success into _EXPORTS  -> gzip -> response
```

### Recommended Project Structure
```
src/screw/
├── calc/
│   ├── __init__.py      # derive(): new rows, new standing warning, fine_stl_refusal() dispatch
│   └── thread.py        # NEW kernel-free: profile maths, closed_volume, T_GATE, volume_check, MAX_TURNS, rules, L11 rows
├── params.py            # left_hand on the base; two after-validators (lazy import of calc.thread)
├── solid/
│   ├── __init__.py      # gate in _build, precise_volume, export-status checks, PRECISE_EPS
│   ├── bolt.py          # rod(p) -> helical.thread(...)
│   └── helical.py       # NEW kernel: section, twist, thread (+ the constants with their L11 comments)
├── app.py               # duplicate-key dependency, fine-STL refusal in _serve
├── cli.py               # BooleanOptionalAction + once-only Actions, fine-STL refusal in cmd_export
└── static/app.js        # checkbox branch, foreign-key refusal, warnings kept on failure
bench/thread_spike/
├── maths.py             # keeps grid/frontier/pair helpers; re-exports the five profile functions (with __all__)
├── helical.py           # keeps naive_sweep_fuse, one_pipe, trim_tip, ruled_reference; re-exports section/twist/thread
└── measure.py           # precise_volume delegates to screw.solid
.github/workflows/grid.yml   # NEW: workflow_dispatch + schedule, matrix over size
tests/                       # see Validation Architecture
```

### Pattern 1: the builder takes `length`, segments in length space, folds a degenerate tail
**What:** `thread(d, pitch, length, *, clearance=0.0, left_hand=False, k=DEFAULT_K)` with `DEFAULT_K = 3`. All
positions are millimetres. Full `k`-turn segments are copies of one base twist translated by `i * k * pitch` (same
arithmetic as the spike, so integer-turn rows reproduce). The last segment always ends at the argument `length`
itself, so the end face is at `z = length` by construction, not at `turns * pitch`. If the remainder
`length - full * k * pitch` is shorter than `MIN_TAIL_MM`, the last full segment is stretched to `length` (its own
twist of `length - z0`) instead of adding a sliver. A whole part shorter than `MIN_TAIL_MM` is refused with
`BuildError` before the kernel is touched.
**When to use:** the only entry point for rod and void. The pair/void in Phase 5 passes `m + 2 * pitch` as `length`.
**Why this and not the spike's turns:** [VERIFIED: probes this session, scratchpad `e3`, `e7`, `e8`, `e13`, `e16`]
- Tails measured with `d=6, pitch=1` single twist: 1e-12 and 1e-9 mm SIGSEGV (rc -11, no output); 1e-8 mm SIGSEGV;
  3e-8, 1e-7 mm `Standard_Failure: NCollection_Array1::Value` / `BRep_API: command not done`; 1e-6 mm
  `MakePipeShell::MakeSolid`; 1e-5 mm builds, relative error 7.9e-07.
- As a sewn tail (3 turns + tail, K = 3) at `(6, 1)`, `(2, 0.4)`, `(20, 2.5)`: 1e-5, 3e-5, 1e-4, 3e-4, 1e-3, 1e-2 mm
  all built one valid solid.
- 130 of 3750 integer-turn rows (15 sizes, 1 to 250 turns, `float(n*P)` and `float(P)`) have a positive tail below
  1e-3 mm in length space; 56 do when turns are re-derived by float division. Without the fold, `pitch=0.6,
  length=5.4` (M3.5, 9 turns, rest 8.88e-16 mm) crashes with SIGSEGV; the same input with the fold builds
  (relative error +1.86e-07). 14 of 82 M3.5 and 17 of 92 M4 grid rows exercised the fold in the six-cell run.
- With the fold, `thread(...)` agrees with the spike's exact-turns `thread(...)` to 7e-13 relative volume on the drift
  rows and 0 on the others.

**Example:** (tested form, scratchpad `cand2.py`; kernel module, `from __future__ import annotations`)
```python
# Source: research probe 2026-10-10, derived from bench/thread_spike/helical.py:63-114
DEFAULT_K = 3        # L11: K = 3 turns, selected by the K rule over 2026-10-08-a-ksweep
MIN_TAIL_MM = 1e-3   # INTERIM research probe, 100x above the last failing tail (see Pattern 1 evidence)

def thread(d: float, pitch: float, length: float, *, clearance: float = 0.0,
           left_hand: bool = False, k: int = DEFAULT_K) -> cq.Solid:
    if not length >= MIN_TAIL_MM:                 # NaN-safe: a NaN fails the comparison
        raise BuildError(f"length {length:g} mm is too short to model a thread "
                         f"(smallest length built: {MIN_TAIL_MM:g} mm).")
    segment = k * pitch
    full = int(length // segment)
    folded = full > 0 and length - full * segment < MIN_TAIL_MM
    bases = full - 1 if folded else full           # full segments that are plain copies
    parts: list[tuple[cq.Solid, float, float]] = []
    if bases:
        base = twist(d, pitch, segment, clearance, left_hand)
        parts += [(base.translate(cq.Vector(0, 0, i * k * pitch)),
                   i * k * pitch, (i + 1) * k * pitch) for i in range(bases)]
    z0 = bases * k * pitch
    parts.append((twist(d, pitch, length - z0, clearance, left_hand).translate(cq.Vector(0, 0, z0)),
                  z0, length))                     # the last span ends at `length` itself
    if len(parts) == 1:
        return parts[0][0]
    # ... sew exactly as the spike does (BRepBuilderAPI_Sewing(SEWING_TOLERANCE), interior cap faces skipped)
```
`twist(d, pitch, length, clearance, left_hand)` is the spike's `twist` with the spine length passed directly
(`turns * pitch` removed); `one_pipe` in `bench` calls `twist(d, pitch, turns * pitch, ...)`.

### Pattern 2: the gate sits in `_build`, with a pure kernel-free comparison
**What:** `_build` already holds the "one valid solid" invariant (`solid/__init__.py:73-81`). Extend it to
`_check_thread(solid, p)`: solid count, `isValid()`, then the signed `precise` volume against
`calc.thread.closed_volume(p.d, p.pitch, p.length)`. Put the comparison in a pure function
`calc.thread.volume_check(measured, closed) -> str | None` so NaN, infinity, a negative volume and a zero closed
form are unit-testable without the kernel. `lru_cache` never stores an exception, so a rejected build is neither
cached nor exported; the bytes cache in `app.py` only `put`s after `backend()` returned (`app.py` `_serve`).
**Rule:** the relative error is `measured / closed - 1.0` (`verdict.relative_error`, signed; an inverted solid
reads about -2). Refuse when `not abs(error) <= T_GATE`, written exactly that way: `abs(nan) > T` is False and
would pass a NaN volume (the spike refuses non-finite numbers at its wire boundary for this reason, STATE
02 decision).
**Positive controls verified this session (both refused by this rule):**
- `naive_sweep_fuse(6.0, 1.0, 10.0)`: 1 solid, `isValid()` True, volume 0.238 of the closed form (relative error
  -0.762), 0.50 s. I ran 13 of the 15 L11 known-bad rows; every one was one valid solid at 0.183 to 0.290 of the
  closed form. The cheap subset: `(2.0, 0.4, 4.0)` 0.44 s,
  `(6.0, 1.0, 10.0)` 0.50 s, `(20.0, 2.5, 10.0)` 0.26 s (build time of the control only).
- `one_pipe(6.0, 1.0, 160.0)`: 1 solid, `isValid()` True, precise volume -1.0 times the closed form (relative error
  -2.0000, default `Volume()` ratio -1.001), 0.73 s. This is the sign case THRD-04 names; the naive sweep is
  positive and does not exercise it.
**Cost of the gate per cold build** (`isValid` + `precise_volume`, this host): M6 x 20 0.13 s; 250 turns of pitch
1 1.36 s; M20 x 200 0.49 s. [VERIFIED: probe `e-cost`, macOS arm64, loaded host, single run]

### Pattern 3: export checks
[VERIFIED: run this session] `Shape.exportStl` returns `bool` (`True`; `False` on a bad path or an empty compound,
and in the empty case writes no file). `Shape.exportStep` returns `IFSelect_ReturnStatus`: `IFSelect_RetDone` on
success, `IFSelect_RetStop` on a bad path; cadquery discards the status of `writer.Transfer`, so only `Write`'s
status is observable. Compare with `from OCP.IFSelect import IFSelect_ReturnStatus` and
`status == IFSelect_ReturnStatus.IFSelect_RetDone`. Order matters: check the return value before
`path.read_bytes()`, which otherwise raises `FileNotFoundError` (the 500 the blocker item records). STL header:
`count = struct.unpack("<I", data[80:84])[0]`; require `len(data) == 84 + 50 * count` and `count >= 4` (the debt
item's floor). Every export of the default M6 x 20 satisfied it (preview 31560 triangles 1,578,084 bytes; fine
209668 triangles 10,483,484 bytes; both watertight).

### Pattern 4: where the rules live and how `params` reaches them
`calc/thread.py` (no `cadquery`, no `logging`, no `screw.records`; contracts 2 and 4 hold for sub-modules):
`fundamental_height`, `thread_depth`, `section_radius`, `section_area`, `closed_volume` (moved verbatim);
`T_GATE = 9e-05`; `volume_check`; `MAX_TURNS = 250`; `turns_of(length, pitch)`; `root_radius_refusal(d, pitch)`;
`turn_cap_refusal(length, pitch)`; `FINE_STL_ROWS`; `fine_stl_refusal(d, pitch, length)`. `params.py` cannot import
`screw.calc.thread` at module top: importing it executes `screw/calc/__init__.py`, which imports `screw.params`
(circular). Import inside the validator body (the pattern 01 used). `calc/__init__.py` may import `calc.thread` at
top level (thread.py imports nothing from the package).
- **Validators:** root-radius rule as an `after` validator on `FastenerParams`; turn cap as an `after` validator on
  `BoltParams` (it needs `length`). Raise `PydanticCustomError(type, message, {"fields": [...]})`:
  verified through the real stack, the API answers `{"type": "turn_cap", "loc": ["query"], "msg": "...", "ctx":
  {"fields": ["length", "pitch"], ...}}` and `app.js problems()` already highlights `ctx.fields`. A plain
  `ValueError` gives `ctx: {"error": {}}` and nothing for the page to highlight. The CLI prints `error: <msg>` (no
  `loc`), so the message text must name both fields. After-validators only run when every field validated, so a
  `d <= 0` request reports only the field error.
- **Fine-STL rule shared by both front ends:** `calc.fine_stl_refusal(p: FastenerParams) -> str | None`, dispatching
  with `isinstance` exactly like `derive`. `app._serve` calls it first when `fmt == "stl" and quality == "fine"`
  and raises the `422`; `cli.cmd_export` calls it before importing `solid` when `ns.quality == "fine"` and the
  format is STL. Because `_serve` is the generic path every kind uses, do not read `length` there.
- **Recommended addition (discretion):** the same function feeds an info-document warning, because the page's
  "Download STL" anchor links to `model.stl?...` without `quality` (server default `fine`, `app.py` `_Quality`),
  so a click on a capped row would navigate the browser to raw JSON.

### Pattern 5: duplicate query keys (FastAPI)
[VERIFIED: ran against fastapi 0.142.2, scratchpad `e10.py`] An app-level `FastAPI(dependencies=[Depends(f)])`
whose `f(request)` raises `HTTPException(422, detail=[{"loc": ["query", name], "type": "duplicate", "msg": ...}])`
runs before the endpoint's own query model is validated: `?d=abc&d=5`, `?d=0&d=5`, `?left_hand=true&left_hand=false`
and `?zz=1&zz=2` all answer the duplicate `422`. Detect with `request.query_params.multi_items()`. The body shape
matches the other `422`s the page parses. An app-level dependency applies to every `@app.get` route, so it should
cover `/api/schema?kind=a&kind=b` too, which the debt item lists (that route was not run; the test over the
registry will prove it).

### Pattern 6: CLI flags
[VERIFIED: ran on Python 3.12.15 and `mypy --config-file pyproject.toml`, scratchpad `e14.py`, `m1.py`] A numeric
flag uses an `argparse.Action` subclass whose `__call__` calls `parser.error(...)` (exit 2, names the flag) when
`getattr(namespace, self.dest) is not None`, else `setattr`. A boolean flag uses a `BooleanOptionalAction` subclass
doing the same check then `super().__call__`. `default=None` stays (the `_params` builder drops `None`). Annotate
`values: str | Sequence[object] | None` (passes `mypy --strict` with `disallow_any_explicit`). Help renders as
`--left-hand, --no-left-hand` on one line, so `tests/test_parity.py::_cli_flags` returns both spellings: its
expected list must add `--no-left-hand` for each bool field. `--left-hand --no-left-hand`, `--left-hand
--left-hand` and `--d 5 --d 6` all exit 2; `--left-han` exits 2 (`allow_abbrev=False`).

### Pattern 7: the page
`buildForm` gets a boolean branch (`prop.type === 'boolean'` -> `input.type = 'checkbox'`; none of the number
attributes). Because `input.value` is the constant `"on"` for a checkbox, three call sites that read or write
`.value` need a branch: `navigate()` (`input.value = h.get(name) ?? defaults[name]`), `partQuery()` (the "changed"
comparison and `q.set(name, input.value)`) and the Reset handler. Add two helpers `read(input)` / `write(input,
v)` keyed on `input.type`, a checkbox reading `String(input.checked)` and writing `input.checked = v === true ||
v === 'true'`; the hash then carries `left_hand=true` only when set and compares as a string against
`String(defaults[name])` (`'false'`). `tests/test_parity.py::PINNED_STATEMENTS` pins the old `.value` spellings
verbatim, three of them (`for (const [name, { input }] of fields) input.value = h.get(name) ?? defaults[name];`,
`q.set(name, input.value)`, `Number(input.value) !== Number(defaults[name])`); amend the pinned list to the helper
forms in the same change and say so in `01-UI-SPEC.md` rule 29, which names them. CSS: `.field input` is
`width: 100%` with padding and border (`style.css:100-109`); a checkbox needs `input[type=checkbox] { width:
auto }`. `left_hand` is a `Thread` group in the schema, so the form shows a second fieldset after `Size`.
- **D-10:** after the form is built for a valid kind, any hash key other than `kind` that is not in `fields` is a
  refusal like the unknown-kind branch (`clearForm()`, `currentKind = null`, empty panel, downloads off, message
  naming the keys). `kind` is the only non-field key the page writes.
- **D-11:** keep warnings per mesh, not per last info fetch. `update()` fetches info first (rule 16), so on a failed
  `model.stl` the most recent info document belongs to the failing part while the mesh on screen is the previous
  one. Hold `pendingWarnings` after the info fetch, copy to `meshWarnings` when `showModel` runs, and make
  `fail()` call `showMessages(errors, mesh ? meshWarnings : [])`. This is the debt item's own wording ("the warnings
  that belonged to that mesh"). This matters now: a gate `BuildError` surfaces at the STL request, after info
  already rendered.

### Anti-Patterns to Avoid
- **Re-deriving turns by float division** for the builder or the cap: drifts (Pitfall 1, Pitfall 2).
- **Translating all segments from `i * seg` differences and comparing floats to reuse the base:** write the loop by
  index (as Pattern 1) so the base is reused for the first `bases` segments only.
- **A second gate in `app.py`:** CONTEXT resolved the roadmap wording; one gate in `solid`.
- **A `tables`-style import from `params`:** contract 6 (Phase 4); the L11 row table is bench evidence in
  `calc/thread.py`, labelled as measured run keys.
- **Reading `Volume()` anywhere:** L11, INFO-03.
- **Writing the gate as `if abs(rel) > T_GATE`:** a NaN passes it.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Exact turns from decimal fields | A float epsilon (`1e-9`) snap | `Fraction(repr(x))` arithmetic | The spike already does this (`pair.py::_turns` uses `Fraction(str(...))`); no tolerance constant to invent (L02) |
| Duplicate query keys | A per-route check | One app-level `Depends` | One place, runs before validation (Pattern 5) |
| Bool CLI flags | A manual `--no-` pair | `argparse.BooleanOptionalAction` | D-09; help and parsing for free |
| Cross-field `422` that the page can highlight | A `ValueError` with field names in prose only | `PydanticCustomError` with `ctx.fields` | `app.js problems()` already reads `ctx.fields` |
| Volume oracle | `Shape.Volume()` | `BRepGProp.VolumeProperties_s(..., 1e-6, False, False)` | L11; default reads -1.001 on an inverted solid |
| Proof that a left-hand part is left-handed | Volume equality (both hands have the same volume) | An `isInside` probe on the crest helix | Pitfall 9 |
| Tail sliver handling | Epsilon in turns | Absolute millimetre fold (`MIN_TAIL_MM`) | The kernel failure is absolute (Pattern 1 data), not relative to the pitch |
| STL validity | A parser | The 84 + 50n header identity (and the watertight helper in the slow tier only) | `bench.thread_spike.measure.stl_check` costs about 3 us per triangle; keep it out of the serving path |

**Key insight:** the dangerous inputs are not exotic. Ordinary decimal lengths (5.4 at pitch 0.6) sit within an ulp
of a segment boundary, and the kernel answers a degenerate sliver with a process crash, not an exception. A
postcondition that runs after the build cannot help; the builder has to avoid the sliver.

## Common Pitfalls

### Pitfall 1: a float tail crashes the kernel
**What goes wrong:** `helical.thread` with `length` in place of exact turns SIGSEGVs (worker death, `503
pool_broken` "can be retried" on the API, a silent exit 139 on the CLI).
**Why it happens:** `full = int(length // seg)` leaves `rest = 8.9e-16` mm; `MakePipeShell` on a sliver below about 1e-8 mm
dies, below about 1e-6 mm raises.
**How to avoid:** Pattern 1 fold. **Warning signs:** rc -11, `BrokenProcessPool`. **Test:** length 5.4 at pitch 0.6
builds; a parametrised drift case from the 130-row set (e.g. `M3.5` 9, 18, 36, 51 turns).

### Pitfall 2: float division mis-states the 250-turn cap
**What goes wrong:** `length / pitch > 250` refuses the measured M4 row (175 mm at pitch 0.7: float quotient
exceeds 250). Comparing exact binary values also refuses M3.5 (150 mm at 0.6).
**How to avoid:** `Fraction(repr(length)) > MAX_TURNS * Fraction(repr(pitch))` accepts all 15 measured 250-turn
rows [VERIFIED: probe over `maths.PITCH`]. The same helper gives the `turns` row exactly:
`float(Fraction(repr(length)) / Fraction(repr(pitch)))` is `9.0` where `5.4 / 0.6` is `9.000000000000002`.

### Pitfall 3: the gate never runs on the tiny-input crash
**What goes wrong:** D-04 relies on the volume gate to refuse a collapsed solid; for `length` at or below about 1e-8
mm (d = 6, pitch 1) or an all-features-below-1e-8 part the process dies first. The debt item's own reproductions
(`length=1e-8`, `1e-9`) are in this zone. See Open Question 1.
**Intermediate sizes behave:** `d=1e-6, pitch=1e-7, length=1e-5` raises `Standard_Failure` (becomes `BuildError`);
`d=0.001, pitch=1e-4, length=0.01` builds and the gate refuses it (+9.59e-03); `d=0.01, pitch=0.0015, length=0.3` is
refused (-3.58e-04); `d=0.1, pitch=0.0125, length=2` passes (-8.18e-05, inside 9e-05 by 8.2 %).

### Pitfall 4: tests that rely on the skeleton's failure inputs
`d=1e-9` was the kernel-failure input (`tests/test_solid.py`, `test_api.py:264-266`, `test_cli.py:127-129`); with the
default pitch 1.0 it is now a root-radius `422`. `{"pitch": 1e300}` is likewise a `422` now (`test_params.py`
`test_pitch_has_no_upper_bound`, `test_the_slug_is_filename_safe...`). Replace the kernel-failure fixtures with a
gate refusal through the real stack: `d=0.001, pitch=0.0001, length=0.01` (0.75 s, relative error +9.59e-03,
kernel pair pinned by L06). `test_d_and_length_are_accepted_at_the_interim_bound` needs `pitch` large enough that
`length = 1e5` is within 250 turns (e.g. `pitch=400`, `d=1e5`: built in 1.74 s, relative error +7.52e-07).

### Pitfall 5: an in-cap off-row part can exceed the INTERIM backstops
Single runs, this host (macOS arm64, load 4 to 26, not decisive, not linux/amd64):
`d=100, pitch=5, length=1250` (250 turns, inside D-01): build 0.6 s; preview STL 6,452,418 triangles, 308 MiB, 6.7 s
mesh, peak RSS 1534 MiB; **fine STL 36,906,760 triangles, 1760 MiB, 152.6 s mesh, peak RSS 7875 MiB** (the INTERIM
timeout is 30 s, `compose.yaml` `mem_limit: 4g`). `d=6, pitch=0.1, length=25` fine: 2,126,222 triangles, 101 MiB,
RSS 1327 MiB (over the 64 MiB export budget, served uncached by `_BlobCache.put`). D-01 and D-03 accept this
("the INTERIM timeout stays the backstop") and L11 lists the budgets as INTERIM; the plan should record these
figures in `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` and surface Open Question 2.

### Pitfall 6: `INTERIM_MAX_MM`'s comment becomes untrue
`params.py:12-33` justifies 1e5 mm with cylinder measurements ("the corner this bound admits ... a cylinder with d=1e5
and length=1e5"). For a thread the cost is set by turns and size, not by that corner. Rewrite the comment to say
the measurements were for the skeleton cylinder and are unmeasured for threads; do not delete the bound.

### Pitfall 7: `mypy --strict` re-export errors in the bench modules
`bench/thread_spike/maths.py` and `helical.py` re-export moved names that `tests/test_bench.py` and `worker.py`
reference as `maths.closed_volume`, `helical.thread`. Under `--strict` (`no_implicit_reexport`) use `__all__` or
`from screw.calc.thread import closed_volume as closed_volume`.

### Pitfall 8: import-linter contract 8 needs an edit, and its two ignore lines must both match
[VERIFIED: ran `lint-imports` on a copy with `PYTHONPATH` pointing at it] A new `screw/solid/helical.py` importing
`OCP` makes contract 8 fail (`screw.solid.helical -> OCP`) because `ignore_imports` lists only `cadquery`. Add
`"screw.solid.** -> OCP"` (always matches once `helical.py` imports OCP) and `"screw.solid -> OCP"`, but the latter
only if `screw/solid/__init__.py` itself imports OCP (the gate's `BRepGProp` and `IFSelect_ReturnStatus`); otherwise
import-linter fails with "No matches for ignored import screw.solid -> OCP". Recommended: gate and export checks live
in `__init__.py` (D-08), so both lines are needed. Contract 2 does flag a kernel import in `screw.calc.thread`
(verified), so no contract-2 edit. A bare run without `PYTHONPATH` analyses the real tree, not a copy: the editable
install wins.

### Pitfall 9: the volume gate is blind to handedness
Left and right rods have equal volume, so a request for `left_hand=true` that built a right-hand thread passes the
gate. Add an independent test with `solid.isInside`: probe radius `r = rr + 0.8 * (ro - rr)`, `z = 2.25 * pitch`,
`theta = 2 * pi * z / pitch`. [VERIFIED: ran, scratchpad inline] right-hand (`left_hand=False`): inside at
`+theta`, outside at `-theta`; left-hand: the reverse. Do not use `z = 2.5 * pitch` (both inside). Also assert the
probes in the same test for both hands so the assertion cannot pass vacuously.

### Pitfall 10: coverage and xdist on the grid tier
The grid tier should run with `--no-cov` (the `fail_under` floor reads a low total on a partial run, `Makefile`
comment above `test:`) and `-n 4` on a 4 vCPU runner (A3).

## Code Examples

### The `422` validators (verified form)
```python
# Source: verified with the real stack, scratchpad e11.py (pydantic 2.13.5, fastapi 0.142.2)
from pydantic import model_validator
from pydantic_core import PydanticCustomError

@model_validator(mode="after")
def _root_radius(self) -> Self:
    from screw.calc.thread import root_radius_refusal      # lazy: calc/__init__ imports params
    if (msg := root_radius_refusal(self.d, self.pitch)) is not None:
        raise PydanticCustomError("pitch_too_coarse", msg, {"fields": ["d", "pitch"]})
    return self
```
`msg` must be a plain string with no `{}` braces (pydantic formats the template from the context mapping): format
numbers into the string before passing it.

### Duplicate keys, app level
```python
# Source: verified, scratchpad e10.py
def refuse_repeated_keys(request: Request) -> None:
    seen: set[str] = set(); repeated: list[str] = []
    for key, _ in request.query_params.multi_items():
        if key in seen and key not in repeated:
            repeated.append(key)
        seen.add(key)
    if repeated:
        raise HTTPException(422, detail=[{"loc": ["query", k], "type": "duplicate",
                                          "msg": f"{k} was given more than once."} for k in repeated])

app = FastAPI(..., dependencies=[Depends(refuse_repeated_keys)])
```

### pytest tiers
```toml
# pyproject.toml [tool.pytest.ini_options]  (--strict-markers is on, so the marker must be registered)
addopts = "--strict-markers --strict-config -m 'not grid'"
markers = ["grid: slow thread grid (CI grid.yml, not make verify)"]
```
[VERIFIED: scratchpad `pm/`] default run deselects `grid`; `pytest -m grid` runs it (the later `-m` wins);
`make test PYTEST_ARGS="-m grid --no-cov"` works because `PYTEST_ARGS` comes last. An explicit node id of a grid test
is still deselected unless `-m grid` is passed.

### Import-linter edit
```toml
# pyproject.toml, contract "Only the solid package imports the CAD kernel"
ignore_imports = ["screw.solid -> cadquery", "screw.solid.** -> cadquery",
                  "screw.solid -> OCP", "screw.solid.** -> OCP"]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Skeleton cylinder, `isValid()`-only check | Sewn twist-section, K = 3, `precise` volume gate at 9e-05 | L11, 2026-10-09 | Phase 3 ships this |
| `Volume()` as an oracle | `VolumeProperties_s` at eps 1e-6 | L11 | default reads -1.001 on an inverted solid |
| Spike `thread(turns)` | `thread(length)` with tail fold | this phase | needed once the caller has a float length |

**Deprecated/outdated:** `SKELETON_WARNING`, the `INTERIM_MAX_MM` cylinder comment, `BoltParams`'s "plain unthreaded
cylinder" docstring, the `pitch` help text ("The walking skeleton builds no thread"), `bench/corpus.py`'s "pitch does
not change the solid" docstring, `src/screw/__init__.py`'s skeleton docstring, and `docs/architecture/overview.md`'s
"No thread, head, table or nut yet".

## Suggested Plan Decomposition (planner's call)

Dependency order, each step ending in `make verify`:
1. **Precondition, not a plan:** the harness `/gsd-quick` PR is on `main`; rebase the phase branch on it.
2. **Kernel-free rules and params:** `calc/thread.py` (moved maths, `T_GATE`, `volume_check`, caps, row table), `left_hand` and the two validators in `params.py`, `tests/test_thread_maths.py`, the params tests, the `422` shape tests. Needs the Open Question 1 ruling for the length guard.
3. **Builder and gate:** `solid/helical.py`, `solid/bolt.py`, the gate and export checks in `solid/__init__.py`, contract 8 edit, `precise_volume` made public and `bench.thread_spike.measure` delegating, the bench import-back with call-site changes (`worker.py`, `pair.py`, `one_pipe`, `test_bench.py`), the sample tests and both positive controls, the blocker debt item resolved.
4. **Info and front ends:** `derive` rows and warning, `fine_stl_refusal` in `app._serve` and `cli.cmd_export`, duplicate-key dependency and CLI Actions, parity and API/CLI tests, the repeated-key debt item resolved.
5. **Page:** checkbox branch, helpers, foreign-key refusal, per-mesh warnings, CSS, `01-UI-SPEC.md` amendments, `PINNED_STATEMENTS` and new source assertions, the two UI debt items resolved.
6. **Slow tier and records:** `grid.yml`, marker and `addopts`, `tests/test_grid.py`, optional `make grid`, the `scripts/pr_land.py:53-54` comment ("The one workflow this repository has") made true again, `bench/README.md`/`bench/RESULTS.md` entry for the first grid run, coverage floor re-measured.
7. **Records:** `L12` in `decision_log.md` (D-15), `docs/architecture/overview.md` module table and contract list, stale docstrings (`src/screw/__init__.py`, `params.py` help texts and `BoltParams`, `solid/bolt.py`, `bench/corpus.py`), `docs/tech_debt/` INDEX moves, the interim-bounds item updated with Pitfall 5, STATE and ROADMAP.

New debt to consider filing (state it in the final reply): the Pitfall 5 figures (into the existing interim-bounds item, Severity must,
Phase 7 trigger); a hash value that is not a boolean if Open Question 3 is not folded in.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `MIN_TAIL_MM = 1e-3` is safe for every in-range `(d, pitch)`; it was probed at `(6,1)`, `(2,0.4)`, `(20,2.5)` for tails 1e-5 to 1e-2 and at one tiny-scale row | Pattern 1 | A size with a larger failing tail would still crash or raise; the 527-row run exercised the fold only on M3.5 and M4 |
| A2 | Slow-tier runner time is about 2 s per row (6 parallel processes on a loaded 18-core host gave 132 s for 60 rows at M6, 285 s for 133 rows at M10, about 180 s for 82 rows at M3.5) so 15 jobs of at most 960 rows each with `-n 4` finish well inside 90 min | Validation Architecture | The workflow may need more shards; first run is the measurement |
| A3 | GitHub public repos get 4 vCPU `ubuntu-latest` runners and 20 concurrent jobs on the free plan | Validation Architecture | Different shard sizing; no correctness impact [ASSUMED: training knowledge] |
| A4 | GitHub disables scheduled workflows in a public repo after 60 days without repository activity | Validation Architecture | The weekly run silently stops; `workflow_dispatch` still works [ASSUMED: training knowledge] |
| A5 | All timings and RSS numbers are single runs on this macOS arm64 host under variable load (4.4 to 26.7) | Pitfall 5, Pattern 2 | They bound nothing (L11 rule: single-machine); Phase 7 re-measures |
| A6 | `Fraction(repr(x))` reads a float as the decimal the user typed, for any value a form, query string or CLI flag can deliver | Pitfall 2 | A user value with more than 17 significant digits reads as its shortest round-trip, not as typed; irrelevant for the caps |
| A7 | The checkbox `.checked` / `input.value` behaviour in a browser matches the DOM spec; no browser exists in the gate (L01) | Pattern 7 | A UI regression the source assertions cannot catch; covered only by the end-of-phase human check (`human_verify_mode: end-of-phase`) |

## Open Questions

1. **Tiny `length` kills the process; D-04 says no lower bound. (Needs an owner ruling before planning the validators.)**
   - What we know: with `d=6, pitch=1`, `length` of 1e-8 mm or less SIGSEGVs (rc -11), 3e-8 to 1e-6 raises, 1e-5 builds and
     passes the gate. The pool turns a crash into `503 pool_broken`, "The request can be retried" (`app.py` `_serve`),
     misleading for a deterministic input; the CLI process exits 139 with no message. D-04 and
     `2026-10-06-collapsed-thin-solid-served-as-200.md` (which suggests a `params` lower bound) disagree.
   - What's unclear: whether the owner accepts a refusal at the builder doorway (a `BuildError`, `422 build_error`
     naming `length`) as consistent with "no lower bound at the params boundary".
   - Recommendation: doorway guard in `helical.thread` using the same `MIN_TAIL_MM = 1e-3` as the fold (labelled
     INTERIM, research probe, Phase 7 re-measures). Surface per AGENTS.md "evidence conflicts".

2. **Cost of in-cap off-row parts (Pitfall 5).**
   - What we know: one in-cap request (d=100, pitch=5, length=1250) needs 7.9 GiB and 153 s for the fine STL here, and
     308 MiB for the preview the page requests on every edit.
   - What's unclear: whether D-01/D-03's "the INTERIM timeout is the backstop" is acceptable when the container limit is
     4 GiB and the preview itself is 308 MiB.
   - Recommendation: build as decided; record the figures in the interim-bounds debt item; do not add an unmeasured cap.

3. **A hash value that is not a boolean.** `#left_hand=banana` would set the checkbox silently to false (the same
   class of silent drop D-10 closes for keys). D-10 names keys only. Recommend refusing any `left_hand` hash value
   other than `true`/`false` the same way; planner or owner to confirm. Also `#d=1&d=2` (repeated hash key).

4. **`SCREW_EXPORT_CACHE_MB`.** The L11 bytes caps are measured against the 64 MiB budget. A deployer who changes the
   env var moves the budget the table was measured for. Recommended: apply the rule unconditionally as D-02 says and
   state in the table comment that it holds for the 64 MiB budget only.

5. **CLI exit status for the fine-STL refusal.** Recommended exit 2, like the `_params` validation path (a refusal of the
   asked parameters, the CLI analogue of the `422`); a `BuildError` exits 1.

6. **Slug for a bool field.** `format(True, 'g')` is `'1'`; the slug becomes `bolt_d6_pitch1_left_hand0_length20`
   (field order: base fields first). Six pinned slugs in `tests/test_api.py` (lines 291, 337, 483, 550, 606) and
   `tests/test_params.py` change. Recommended: keep the generic `:g` slug and update the pins; right-hand and
   left-hand downloads then have distinct file names.

7. **UI contract.** The roadmap says `UI hint: yes` and `workflow.ui_safety_gate` is true; the Phase 1 gate halted for a
   missing UI-SPEC. `01-UI-SPEC.md` says each phase "extends this contract ... in the plan that adds it". Decide
   whether `/gsd-ui-phase 3` runs first or the plan amends `01-UI-SPEC.md` (rules 2, 10, 15, 24, 29) in place.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 + `.venv` | everything | yes | 3.12.15 | none needed |
| cadquery / cadquery-ocp | builder, gate, tests | yes | 2.8.0 / 7.9.3.1.1 | none (L01) |
| `make`, `ruff`, `mypy`, `lint-imports`, `pytest` | `make verify` | yes | `make verify` ran green | — |
| `gh` | checking workflow results, `make pr.land` | yes (`gh repo view` answered; repo is PUBLIC) | — | — |
| Docker | `make image`/`make smoke` only | not probed; not needed by `make verify` | — | CI `image` job covers it |
| Node | vendor bundle only | present (v26.11.0), not needed this phase | — | — |

**Missing dependencies with no fallback:** none. **Precondition (not an environment item):** the harness review PR
must be on `main` before the Phase 3 PR (D-13); the branch was cut at `a0c7923`, and the harness PR is a rebase
target.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (>=8) + pytest-xdist 3.8.0 + pytest-cov 7.1.0, `filterwarnings = ["error"]`, `xfail_strict`, `--strict-markers` |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]`; coverage floor `fail_under = 94` |
| Quick run command | `make test PYTEST_ARGS="tests/test_solid.py tests/test_calc.py tests/test_params.py -q -n0 --no-cov"` |
| Full suite command | `make verify` (baseline before changes: 695 passed in 37.96 s, 95.56 % total) |
| Slow tier | `make test PYTEST_ARGS="-m grid -q --no-cov"` (add a `make grid` target if wanted; the `bench.*` family is the precedent) |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| THRD-01 | Default bolt is one valid solid with a helical thread: bounding box 6 x 6 x 20 (±1e-6, the kernel box gap is 1e-7), precise volume within `T_GATE` of `closed_volume`; preview and fine STL watertight | integration (real kernel) | `pytest tests/test_solid.py -k thread` | extend `tests/test_solid.py` |
| THRD-01 | End face at `z = length` for a non-integer-turn length (20.5), a sub-turn length (0.8), and drift rows (`pitch=0.6, length=5.4`; `0.45` pitch 9 mm; M3.5 9, 18, 51 turns) | integration | same | extend `tests/test_solid.py` |
| THRD-01 | Builder refuses `length < MIN_TAIL_MM` with `BuildError` and never reaches the kernel (subject to Open Question 1) | unit | same | extend |
| THRD-01 | Rod and void against the closed form: `thread(..., clearance=0.0)` and `thread(..., clearance=maths.VOID_CLEARANCE)` | integration | same, sample in `make verify` | extend |
| THRD-01 | Rules: root radius refusal at `pitch >= 0.9238 d` (boundary via `thread_depth`), turn cap accepts all 15 measured 250-turn rows and refuses 250.0001 turns, `turns_of(5.4, 0.6) == 9.0` | unit (kernel-free) | `pytest tests/test_calc.py -k thread` or new `tests/test_thread_maths.py` | new file recommended |
| THRD-01 | `422` through the model: `{"loc": ["query"], "type": "turn_cap", "ctx": {"fields": ["length", "pitch"]}}`, root radius names `d`,`pitch` | unit + API | `pytest tests/test_params.py tests/test_api.py -k "turn or root"` | extend both |
| THRD-01 | Info rows `d, pitch, length, turns, volume, thread_depth, minor_diameter`; warning text verbatim; no row key appears as a literal in `app.js` | unit + parity | `pytest tests/test_calc.py tests/test_parity.py` | rewrite `test_calc.py`, extend parity |
| THRD-02 | `left_hand` default False, frozen, in schema as `boolean`, in hash only when true; API `?left_hand=true`, CLI `--left-hand`/`--no-left-hand`, API/CLI documents equal | unit + parity | `pytest tests/test_params.py tests/test_parity.py` | extend (parity's document test builds cases from float fields only: add a bool case) |
| THRD-02 | Handedness probe (`isInside`, Pitfall 9) for both hands; left-hand passes the same gate; STL/STEP exports for both | integration | `pytest tests/test_solid.py -k hand` | extend |
| THRD-04 | Positive control 1: `naive_sweep_fuse` rows `(6.0,1.0,10.0)`, `(2.0,0.4,4.0)`, `(20.0,2.5,10.0)` raise `BuildError` naming the volume and the signed error | integration | `pytest tests/test_solid.py -k gate` | extend |
| THRD-04 | Positive control 2 (sign): `one_pipe(6.0,1.0,160.0)` is refused with a negative signed error | integration | same | extend |
| THRD-04 | `volume_check` pure: NaN, +inf, -inf, negative, zero closed form, exact boundary, just outside 9e-05 | unit (kernel-free) | `pytest tests/test_thread_maths.py` | new |
| THRD-04 | A refused build is not cached: second `build(p)` raises again, `_build_cached.cache_info().currsize` unchanged; a refused export never enters the app's `_EXPORTS` | integration | `pytest tests/test_solid.py tests/test_api.py -k refused` | extend |
| THRD-04 | Gate through the three front ends: API `422 build_error` and CLI `error:` exit 1 on `d=0.001, pitch=0.0001, length=0.01`; `exportStl` False / STEP status / bad header monkeypatched to `BuildError` | integration | `pytest tests/test_api.py tests/test_cli.py tests/test_solid.py` | extend |
| D-02/D-03 | `fine_stl_refusal`: refuses `(8.0, 1.25, 67.6)`, accepts `(8.0, 1.25, 67.5)`, accepts an off-row `(8.1, 1.25, 500)`, names `length`, mm, turns, run id; API `422` and CLI exit; preview and STEP unaffected | unit + API + CLI | `pytest tests/test_calc.py tests/test_api.py tests/test_cli.py -k fine` | extend |
| D-10, D-11 | `app.js` source assertions: foreign-key refusal text path, `meshWarnings` used in `fail()`; pinned statements amended | source-text | `pytest tests/test_parity.py` | extend |
| D-12 | Repeated key / flag, parametrised over `KINDS` and over every field including the bool, API `422 duplicate` and CLI exit 2 | parity | `pytest tests/test_parity.py -k repeated` | extend |
| SC4 | Grid: 15 sizes x both hands x rod/void x the D-03 lengths (7160 rows) through `helical.thread` and the gate | slow (`@pytest.mark.grid`) | `pytest -m grid` | new `tests/test_grid.py` |
| SC4 | Sample in `make verify`: M6 x 20 right rod, M6 x 20 left rod, M6 void at 0.20, `0.8`-turn, `20.5`-turn, drift rows, positive controls | integration | `make verify` | `tests/test_solid.py` |
| governance | `grid.yml` is not in `ci.yml`, `required-jobs.txt` unchanged, `test_pr_land.py` untouched and green | existing | `pytest tests/test_pr_land.py -q -n0 --no-cov` | exists |
| governance | import contracts after the contract-8 edit | contracts | `make lint-imports` | exists |
| bench | spike smoke after the import-back; every `tests/test_bench.py` test that calls `helical.thread` (for example `test_a_real_m6_right_hand_five_turn_rod_passes_the_row_verdict`, line 931) | existing | `make test PYTEST_ARGS="tests/test_bench.py -q -n0 --no-cov"`, `.venv/bin/python -m bench.thread_spike smoke ...` | exists, call sites change |

Tests that break on purpose and must be rewritten, located by grep (read each before editing): `tests/test_params.py`
(defaults, schema order and loop, slug, extreme-value slug, `pitch` no upper bound, the INTERIM bound test),
`tests/test_calc.py` (rows, warning, "no turns row", overflow cases), `tests/test_api.py` (schema props at line 130, query
names 171-175, rows 192, warnings 198, `d=1e-9`/`pitch=1e300` at 264-275, slugs), `tests/test_cli.py` (line 20
`SKELETON`, lines 127-129), `tests/test_solid.py` (`d=1e-9`), `tests/test_parity.py` (imports `SKELETON_WARNING`,
`_cli_flags`, pinned statements), `tests/test_bench.py` (line 933 `helical.thread(d, pitch, turns, k=5)` and the
worker/pair call sites). `bench/thread_spike/worker.py:116` passes `request["turns"]`; pass `request["length"]`
(the request already carries both) and `pair.py` passes `m + 2 * pitch`.

### Sampling Rate
- **Per task commit:** the quick command for the touched module, then `make lint-imports` when `pyproject.toml` or a module edge moves.
- **Per wave merge:** `make verify`.
- **Phase gate:** `make verify` green and one `grid.yml` `workflow_dispatch` run (or a documented single-size shard) before `/gsd-verify-work`; it records, it does not gate `main` (CONTEXT specifics).

### Wave 0 Gaps
- [ ] `tests/test_thread_maths.py` — kernel-free rules (root bound, cap, exact turns, `volume_check`, fine-STL rule, L11 row table)
- [ ] `tests/test_grid.py` — `@pytest.mark.grid`, parametrised ids like `M3.5-right-rod-5.4`; selecting a size in CI by `-k` needs ids that do not alias (`M2-` does not match `M12-`; `M3-` does not match `M3.5-`) — verify with `--collect-only` before relying on it
- [ ] `pyproject.toml` marker registration and `addopts`
- [ ] Contract 8 edit (Pitfall 8)
- [ ] Coverage floor: re-measure by the spur L34 rule after the suite grows (`floor(L - max(0.25, S))`, never a round number); baseline total is 95.56 %

Grid shard sizing (UNVERIFIED on GitHub runners; this host, 6 processes in parallel, loaded): 60 to 133 rows per cell
took 132 to 285 s, about 2.1 s per row. 7160 rows at that rate is about 4 hours of compute; with one job per size and
`-n 4` the largest job (M20: 240 lengths x 4 cells) is roughly 960 rows. Set `timeout-minutes` generously, `fail-fast: false`,
`permissions: contents: read`, and record the first run's wall time in `bench/RESULTS.md` rather than asserting it.

## Security Domain

### Applicable ASVS Categories (level 1, `security_enforcement` true)

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | no accounts (REQUIREMENTS: out of scope) |
| V3 Session Management | no | stateless |
| V4 Access Control | no | no principals |
| V5 Input Validation | yes | pydantic at the model boundary; `extra="forbid"`; `allow_inf_nan=False`; duplicate-key refusal; turn and root-radius refusals; builder doorway guard |
| V6 Cryptography | no | none used |
| V12/V13 API and DoS | yes | the 250-turn cap, the fine-STL refusal, `BuildTimeout` and the bounded queue (INTERIM) |
| V14 Configuration | yes | `grid.yml`: `permissions: contents: read`, no secrets, triggers `workflow_dispatch` and `schedule` only (no `pull_request`, so no untrusted-code exposure) |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| CPU or memory exhaustion by an in-cap request (Pitfall 5) | Denial of service | turn cap, per-build timeout, bounded queue, the new fine-STL refusal; residual risk recorded as debt (INTERIM) |
| Crash loop: a deterministic input that kills the worker and invites retries ("can be retried") | Denial of service | builder doorway guard and tail fold (Pitfall 1, 3); without them a client retry kills worker after worker |
| Poisoned cache: a wrong solid served repeatedly | Tampering | gate before `lru_cache`; the bytes cache only stores a successful export |
| XSS through warning text | Tampering | `textContent` only; `tests/test_parity.py::test_the_ui_builds_nodes_from_text_only` stays; new messages that include keys from the URL hash must go through `textContent` too (D-10) |
| Unfriendly or injecting filename from a bool field | Tampering | `slug()` is built from validated values only; `left_hand0`/`left_hand1` contain nothing outside `[A-Za-z0-9_.+-]` |
| Log injection through `left_hand` | Repudiation | `records._part_fields` logs `model_dump(exclude_defaults=True)`, structured JSON |

## Project Constraints (from CLAUDE.md)

- `make verify` is the only "done" (ruff, mypy `--strict`, import contracts, unfinished-work scan, pytest); state the command and the result line.
- No `Any` (L04): untyped values are `object`; `disallow_any_explicit` is on. No `type: ignore` in `src/screw/` (`make no-fake-done`).
- No `TODO`, `FIXME`, `XXX`, `HACK`, `NotImplementedError` in `*.py`, `*.js`, `*.sh`.
- L02: a number is printed only if it can be computed honestly; defaults are absolute mm and frozen (the `left_hand` default is part of every link); a direct conflict is a `422` naming the fields; a capped dimension is warned about.
- `calc` never imports `cadquery`, `OCP`, `logging` or `screw.records`; vendor types stop at `screw.solid`; `params` validated once.
- Comments carry the measurement or constraint that forced the choice; every INTERIM constant says `INTERIM`, its source and "Phase 7 re-sweeps"; every measured constant cites its run id.
- New behaviour ships with its tests in the same change; debt is retired in the fixing commit (Status resolved, sha, `git mv` to `resolved/`, INDEX row); a new idea or debt item is a file from `docs/<dir>/TEMPLATE.md` with an INDEX row; state in the final reply whether any item was filed.
- Conventional Commits, one concern per commit, English; commit messages end with the attribution line given by the session.
- Work goes through a gsd entry point; a cross-CLI review is done by someone other than the author; one PR per phase through `make pr.land`, the harness PR separately and first.
- "Stop and ask first": an unverified library behaviour, a locked decision that looks wrong, or conflicting evidence: Open Questions 1 and 2 are exactly that.

## Sources

### Primary (HIGH confidence)
- Repo files read this session: `03-CONTEXT.md`; `.planning/REQUIREMENTS.md`; `.planning/STATE.md`; `docs/architecture/decision_log.md` (L11, L08 sections); `bench/thread_spike/helical.py`, `maths.py`, `measure.py`, `pair.py` (call sites); `src/screw/solid/__init__.py`, `solid/bolt.py`, `params.py`, `calc/__init__.py`, `app.py`, `cli.py`, `build_errors.py`, `static/app.js`, `static/style.css`, `static/index.html`; `pyproject.toml`; `Makefile`; `.github/workflows/ci.yml`, `required-jobs.txt`; `scripts/pr_land.py:48-70`; `tests/test_solid.py`, `test_parity.py`, `test_params.py`, `test_calc.py`, `test_pr_land.py` (job-name derivation); the four tech-debt items; `01-UI-SPEC.md` rules 2, 6, 10, 15, 24, 29; `.planning/research/ARCHITECTURE.md` Q4.
- Installed packages exercised directly: cadquery 2.8.0 / cadquery-ocp 7.9.3.1.1 (`exportStl`, `exportStep`, `makeHelix`, `MakePipeShell`, `isInside`), pydantic 2.13.5, fastapi 0.142.2, import-linter (run on a copy), argparse and mypy on Python 3.12.15, pytest `-m` behaviour. Probe scripts `e1`-`e16`, `cand.py`, `cand2.py` in the session scratchpad (not committed).

### Secondary (MEDIUM confidence)
- `bench/RESULTS.md` § Thread spike (grid summary table lines 340-348, ladder and verdict blocks cited by L11): used only for row counts and per-size maxima, not re-derived.

### Tertiary (LOW confidence)
- GitHub Actions runner and scheduling facts (A3, A4): training knowledge, not fetched.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, nothing new; versions read from the environment.
- Architecture: HIGH, every integration point read and the three front-end mechanisms ran.
- Pitfalls: HIGH for the SIGSEGV, float-cap, contract-8 and handedness findings (reproduced); MEDIUM for how far the tiny-input threshold generalises (A1) and for runner timing (A2).

**Research date:** 2026-10-10
**Valid until:** 2026-11-09 (stable; re-check if the kernel pair in `requirements.txt` moves, which L06 and L11 tie to every number here)
