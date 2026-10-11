# Phase 3: Real Helical Thread - Context

**Gathered:** 2026-10-10
**Status:** Ready for planning

<domain>
## Phase Boundary

The `bolt` kind stops being a plain cylinder and becomes a real helical thread over its whole
`length`: the ISO 68-1:2023 basic profile, built by the construction Phase 2 chose (sewn
twist-section, K = 3, L11), right- or left-hand through a new `left_hand` boolean field, on the
web UI, the HTTP API and the CLI from the one registered model. Every thread build passes a
postcondition — valid shape, exactly one solid, `precise` volume inside `T_gate` of the closed
form, sign included — before it can reach the solid cache, the bytes cache, a preview or a
download; a failure is a `BuildError` naming what failed. The one helical builder is proven on a
bare rod and on a bare void (the clearance-grown section Phase 5's nut subtracts) against the
closed form: a sample in `make verify`, the full Phase 2 grid in a slower tier.

The spike's kernel-free maths and its builder move from `bench/thread_spike/` into
`src/screw/calc/thread.py` and `src/screw/solid/helical.py` unchanged where possible, and the
spike imports them back (02 D-18: what was measured is what ships).

Not in this phase: head, shank, `thread_length` and the ISO 4014/4017 rows (Phase 4); tip and
nut chamfers, the nut kind, the `clearance` field and the pair proof (Phase 5); every table;
any re-measured runtime bound (Phase 7). The part stays an internal milestone: version `0.0.x`,
no release tag, a standing warning on the info document (D-06 below).

Roadmap wording resolved by this discussion (planner: build to this, not to the loose text):
- SC3 "volume within the stated tolerance … using the estimator Phase 2 chose" is L11 exactly:
  `BRepGProp.VolumeProperties_s` at eps 1e-6, `|relative error| <= T_gate = 9e-05`, sign kept
  in the message. No other estimator and no other number.
- SC4 "a sample in `make verify`, the full grid in a slower tier": the slower tier is a separate
  GitHub workflow file, manual plus scheduled, outside L08's required jobs (D-14).
- Goal "a build the postcondition rejects never reaches a cache": the gate runs inside the
  solid package before the `lru_cache` wrapper (an exception is never cached) and the bytes
  cache only ever stores a successful export, so both caches are covered by one gate placement
  (D-08). No second gate in `app.py`.
- L11 "Phase 3's cap-and-warn input is the smallest of the three columns": applied as D-01 to
  D-03 below — a refusal, not a trim, because `length` is an explicit choice (L02). This reads
  L11's number as its input and narrows "cap-and-warn" to "refuse" for one artefact; it is
  recorded in the new decision entry (D-15), not as a superseding entry.

</domain>

<decisions>
## Implementation Decisions

### Caps: L11's turn caps applied to arbitrary (d, pitch, length)
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

### Pitch validity at the params boundary
- **D-04:** The only new `(d, pitch)` refusal is geometric: `d/2 - 5H/8 <= 0` with
  `H = (sqrt(3)/2) * P` (the basic-profile root radius, from the coefficients the owner
  confirmed at the 02 D-01 checkpoint; zero at `pitch ≈ 0.9238 d`) is a `422` naming `d` and
  `pitch`. Everything else builds: no measured-band restriction, no ISO 262 coarse check (Phase
  4; contract 6 forbids `params` reaching `tables`). The THRD-04 gate catches a wrong solid and
  the INTERIM timeout bounds cost. This closes 01 D-07's open `pitch >= d` question. No lower
  bound on `length` or `d` is added: the gate refuses a collapsed solid by its volume (D-08),
  which is honest where an INTERIM minimum would be a number nobody measured; sub-turn lengths
  (`length < pitch`) build (02 R2 built 0.8-turn rows ok).

### Info panel after the skeleton
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

### The gate (THRD-04) and the blocker it closes
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

### `left_hand` on the three front ends
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

### Module moves and the harness precondition
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

### Slow tier and the `make verify` sample
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

### Decision entry
- **D-15:** A new `L12` in `docs/architecture/decision_log.md` records this phase's choices that
  later phases build on: the cap mechanism (D-01 to D-03, the reading of L11's "cap-and-warn"
  as refuse-for-one-artefact), the geometric pitch bound (D-04), the gate placement and export
  checks (D-08), the standing warning (D-06) and the slow tier (D-14). It cites L11's run ids
  and measures nothing new. The planner lands it in the same PR.

### Thread ends
- **D-16:** Both ends are plain planar cuts at `z = 0` and `z = length`, as every measured spike
  row was (`2026-10-08-a-grid`). No fade, no chamfer: ISO 4753 is unread (THRD-05, Phase 5) and
  an invented end is the plausible number L02 forbids. The bounding box is `d × d × length`.

### Owner rulings on research open questions (planning session, 2026-10-10)
- **D-17:** A `length` the kernel cannot model is refused at the builder doorway, not at the
  params boundary: `helical.thread` raises `BuildError` when `not length >= MIN_TAIL_MM`
  (1e-3 mm, INTERIM — research probe 2026-10-10 at `d=6, pitch=1`: `length <= 1e-8` mm SIGSEGVs
  the worker before the THRD-04 gate can run, 3e-8…1e-6 mm raises, 1e-5 mm builds; Phase 7
  re-measures). The same constant folds a sub-1e-3 mm remainder segment into the previous one so
  the end face still sits at `z = length`. The existing `BuildError` path answers (`422
  build_error` on the API naming `length`, exit 1 on the CLI); no `503 pool_broken` and no
  silent exit 139 for a deterministic input. D-04's "no lower bound at the params boundary"
  stands as written. Resolves 03-RESEARCH Open Question 1.
  — **Reversibility:** reversible — one constant in the kernel module and its tests.
- **D-18:** In-cap off-row cost (03-RESEARCH Pitfall 5: `d=100, pitch=5, length=1250` → fine STL
  36.9M triangles, 7.9 GiB peak RSS, 153 s; preview 308 MiB; container limit 4 GiB, timeout 30 s)
  is built as decided under D-01/D-03. No unmeasured guard is added (L02). The plan records the
  figures in `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` (Severity must,
  Phase 7 trigger OPER-03). Resolves Open Question 2.
- **D-19:** No `03-UI-SPEC.md`. The plan amends
  `.planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md` in place (rules 2, 10,
  15, 24, 29 per 03-RESEARCH) for the checkbox branch, the boolean hash round-trip, the
  foreign-key refusal (D-10) and warnings kept on failure (D-11), each pinned by a test in the
  same change. Resolves Open Question 7.

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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` § Phase 3 — goal, success criteria 1–4 (read with the four
  resolutions in `<domain>`); § Phase 4 and § Phase 5 for what is explicitly not here
- `.planning/REQUIREMENTS.md` — THRD-01, THRD-02, THRD-04 (this phase); THRD-03, THRD-05,
  PAIR-01, INFO-01, INFO-03, FRNT-06, OPER-01…03 (what later phases add on this builder);
  FRNT-01…05 (the parity the new field must keep); § Out of Scope (fine pitch, unthreaded flag)
- `.planning/PROJECT.md` § Context (spur lessons: spike before field, what was measured is
  what ships), § Constraints
- `.planning/STATE.md` § Blockers/Concerns — the coarse-pitch question D-04 answers; the
  harness debt line; "Phase 3 is plannable"

### The locked inputs this phase builds on
- `docs/architecture/decision_log.md` — **L11** (construction, K = 3, sewing tolerance,
  `MAX_SEGMENTS`, section samples, estimator and `T_gate`, the turn-cap table, the known-bad
  inputs, the UNVERIFIED/INTERIM register); L02 (refuse or cap, never guess; frozen defaults);
  L04 (no `Any`); L08 (required jobs = every job in `ci.yml`; `make pr.land`); L09 (registry,
  per-kind routes, hash rule, `PartInfo`, INTERIM policy)
- `.planning/phases/02-thread-spike/02-SPIKE.md` — § Owner rulings (profile pin `basic`,
  coefficients, R2 sub-turn rows), § Protocol inputs (PITCH keys, UNVERIFIED labels), § Rules
  (turn caps, known-bad rows), § Verdict
- `.planning/phases/02-thread-spike/02-CONTEXT.md` — D-03 (the corpus D-14 reuses), D-06
  (the negative control as THRD-04's known-bad input), D-08 (rod and void, no head), D-18 (the
  move into `src/` and the import-back)
- `bench/RESULTS.md` § Thread spike (Phase 2) — `### 2026-10-08-a-verdict`, `-grid`,
  `-frontier`, `-controls`, `-ladder` (the run ids every cap and gate constant must cite)

### The code that moves and the code it lands in
- `bench/thread_spike/helical.py` — `section`, `twist`, `thread` (to `solid/helical.py`);
  `naive_sweep_fuse` (stays; the positive control)
- `bench/thread_spike/maths.py` — profile maths and `closed_volume` (to `calc/thread.py`);
  `VOID_CLEARANCE = 0.20`, `lengths()` / `standard_max()` (the D-03 corpus, stays)
- `bench/thread_spike/measure.py` — the precise-volume call and the STL watertight check the
  gate and the grid test reuse
- `src/screw/solid/__init__.py` — `_build`, `_build_checked`, `lru_cache`, `_write_export`
  (the gate's home, D-08); `TESSELLATION` INTERIM comment
- `src/screw/params.py` — `_f`, `FastenerParams`, `INTERIM_MAX_MM` (the boundary D-01/D-04
  extend); `src/screw/calc/__init__.py` — `InfoRow`, `PartInfo`, `_bolt`, `SKELETON_WARNING`
- `src/screw/app.py:47-90` — `_BlobCache.put` (the over-budget branch D-02 reasons from),
  `_serve`; `src/screw/cli.py:22-35` — the flag generator D-09/D-12 extend
- `src/screw/static/app.js` — the form builder (number input only today), `navigate()`,
  `partQuery()`, `writeHash()`, `fail()`, `showMessages()` (D-09 to D-11)
- `tests/test_parity.py`, `tests/test_solid.py`, `tests/test_api.py`, `tests/test_cli.py`,
  `tests/test_bench.py` — the patterns the new tests follow

### Research (the evidence behind the gate and the ends)
- `.planning/research/ARCHITECTURE.md` § Q4 (split `calc/thread.py` / `solid/helical.py`, one
  builder for rod and void, the postcondition), Pattern 4 (cap vs refuse on threads),
  Anti-Patterns 4, 6, 7; § Import-linter contracts
- `.planning/research/PITFALLS.md` C1 (valid-but-wrong solids), C2 (`Volume()` is no oracle),
  C3 (turns, non-monotone frontier), C9 (mesh vs thread depth, mesh on a copy), C10 (ends,
  partial turns), M1, M2 (native hand), M9 (CPU bomb at the boundary), M10 (never cache a
  broken build)

### Debt this phase resolves or depends on
- `docs/tech_debt/active/2026-10-06-collapsed-thin-solid-served-as-200.md` (blocker, D-08)
- `docs/tech_debt/active/2026-10-06-ui-drops-foreign-hash-keys.md` (D-10)
- `docs/tech_debt/active/2026-10-06-ui-hides-warnings-on-failed-update.md` (D-11)
- `docs/tech_debt/active/2026-10-06-repeated-query-key-silently-wins.md` (D-12)
- `docs/tech_debt/active/2026-10-09-thread-spike-harness-review-findings.md` (the
  precondition PR; not folded)
- `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` — the 30 s / 64 MiB budgets
  D-01/D-02 lean on are INTERIM; `docs/tech_debt/INDEX.md` for the row moves
- `.planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md` § Interaction
  Contract rules 10, 15, 24 (amended by D-10/D-11)

### House rules
- `AGENTS.md` / `CLAUDE.md`, `docs/CODING_VALUES.md`, `docs/HOW_TO_DEVELOP.md` (one PR per
  phase through `make pr.land`; the harness quick PR is separate by owner decision)
- `docs/architecture/overview.md` — module map to extend with `calc/thread.py` and
  `solid/helical.py`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `bench/thread_spike/helical.py` `section` / `twist` / `thread(k=…)`: the measured builder;
  moves, does not get rewritten. `naive_sweep_fuse`: the known-bad builder for the gate's
  positive control (stays in bench, imported by the test).
- `bench/thread_spike/maths.py`: `section_area`, `closed_volume`, `thread_depth` — the oracle
  the gate compares against and the source of D-05's rows; `lengths()`/`standard_max()` — the
  D-03 corpus for the slow tier.
- `bench/thread_spike/measure.py`: the `BRepGProp.VolumeProperties_s(…, 1e-6, False, False)`
  call and the binary-STL watertight check (vertex weld 1e-5 mm, paired directed edges).
- `src/screw/solid/__init__.py`: `_build_checked` already funnels every kernel exception into
  `BuildError`; `lru_cache` means a raise is never cached (the gate placement D-08 needs
  nothing new there). `_write_export` meshes a copy (spur L24) — keep.
- `src/screw/params.py` `_f()`: field metadata that drives the form and the CLI; a boolean
  field needs a sibling helper (no `gt`/`le`) and the form's checkbox branch.
- `src/screw/calc/__init__.py` `InfoRow`/`PartInfo`: the generic document; D-05 adds rows, no
  renderer change.
- `tests/test_parity.py`: registry-driven; the boolean branch is covered by adding the field,
  the `app.js` source assertion must still find no field-name literal.

### Established Patterns
- Validated once at the model boundary, trusted afterwards; cross-field rules (turns, root
  radius) belong in an `after` model validator with a `422` naming both fields.
- `params` reaches `calc` by a lazy import inside the validator (01 code_context); `calc` never
  imports the kernel or the logger (contracts 2, 4).
- Every INTERIM constant carries `INTERIM` + source + "Phase 7 re-sweeps"; every measured
  constant cites its run id in the comment (L11 style).
- Debt is retired in the fixing commit: `Status: resolved`, sha, `git mv` to `resolved/`,
  INDEX row moved.
- A positive control for every gate (THRD-04; 02 D-06): the test that feeds a known-bad build
  and sees the refusal ships with the gate.

### Integration Points
- `params.FastenerParams` ← `left_hand` (D-09), turn cap and root-radius validators (D-01,
  D-04) → `calc/thread.py` rules.
- `solid._build` dispatch → `solid/bolt.py` → `solid/helical.thread(d, pitch, …, left_hand)`;
  gate in `_build_checked` (D-08); export status checks in `_write_export`.
- `calc.derive._bolt` → D-05 rows and the D-06 warning; `SKELETON_WARNING` removed.
- `app._serve` and `cli export` → the fine-STL cap rule (D-02/D-03) before any build is
  requested; duplicate-key refusal (D-12) in the app's query parsing and the CLI's flag action.
- `static/app.js` → checkbox branch, boolean hash round-trip (D-09), refuse foreign keys
  (D-10), keep warnings on failure (D-11).
- `.github/workflows/grid.yml` (new, D-14); `pyproject.toml` pytest markers; a `make` target
  for the grid if one is wanted (the `bench.*` family is the precedent).
- `bench/thread_spike/{helical,maths}.py` → thin re-exports of the `src/` modules (D-13),
  after the harness quick PR has landed.
- `docs/architecture/decision_log.md` → L12 (D-15); `docs/architecture/overview.md` module
  table; `docs/tech_debt/` four items resolved.
- gsd: `git.branching_strategy: phase`; branch `gsd/phase-03-real-helical-thread` from `main`
  at `a0c7923`.

</code_context>

<specifics>
## Specific Ideas

- Standing warning, verbatim: `threaded rod: no head, plain-cut thread ends; not a product build`.
- Fine-STL refusal names three things: the field (`length`), the cap (mm and turns) and the
  run id (`2026-10-08-a-grid`); the turn-cap refusal names `length`, `pitch` and 250 turns with
  `2026-10-08-a-frontier`.
- The L11 row table in code is labelled as measured run keys, not ISO rows, one run id per row.
- Panel labels for depth and minor diameter say "ISO 68-1:2023 basic profile".
- The void sample in `make verify` uses the spike's 0.20 mm (`maths.VOID_CLEARANCE`), the
  clearance every grid void row was built at.
- Nothing in `make verify` asserts a timing (02 D-15); the grid workflow records, it does not
  gate `main`.

</specifics>

<deferred>
## Deferred Ideas

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

</deferred>

---

*Phase: 03-real-helical-thread*
*Context gathered: 2026-10-10*
