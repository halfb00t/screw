# Phase 5: Hex Nut and Kernel Pair Proof - Context

**Gathered:** 2026-10-14
**Status:** Ready for planning

<domain>
## Phase Boundary

A second registered kind, `nut` (ISO 4032:2023 style 1), joins `bolt` in `KINDS` with the fields
`d`, `pitch`, `left_hand` (base), `s`, `m` and a **required** `clearance` (radial millimetres on
the nut, no default until Phase 6's printed test): the hex prism less the clearance-grown helical
void, with lead-in cones on both faces and the face chamfers as the owner's read of ISO 4032 gives
them, built by `helical.thread` behind the THRD-04 gate and served on the UI, the API and the CLI
from the one model, parity test green with both kinds. The bolt gains its thread ends (THRD-05):
a tip chamfer per ISO 4753 and, on an ISO 4014 bolt with a plain shank, an under-head fillet built
as a solid of revolution; the gate keeps `T_GATE` by growing a kernel-free numeric oracle for the
cone cuts. For any bolt the user gets the matching nut and vice versa through one `counterpart`
key on the info document (TYPE-04). ISO 4032:2023 (M5–M20 normative, M2–M4 from Annex A labelled
"informative / historical"), ISO 724:2023 (`d2`, `D1`, `D2`) and ISO 965-2:2024 (the 6g/6H limits
the panel shows) enter `src/screw/tables/` cited, double-entered and tested like Phase 4's rows.
The info document gains the nut, pair and limits groups (INFO-01, INFO-02). The pair proof ships
as `screw.solid.pair.prove(NutParams) -> PairReport` and `screw pair nut <flags>`, judging the
spike's measured bodies under the unchanged D-14 rule, with one cell in `make verify`, the grid in
`.github/workflows/pair.yml` against expected verdicts pre-registered from `2026-10-08-a-pair`,
and a separately pre-registered, bounded M18 control diagnosis that changes no rule. The download
STL's chord deviation becomes a measured constant cited against the smallest proof clearance
(FRNT-06), and a preview STL names its quality in its file name.

Not in this phase: the clearance default and the printed test (Phase 6, PAIR-02, PAIR-05/06); the
printability threshold (INFO-04, Phase 6); any re-measured runtime bound (Phase 7); the pair proof
as an API endpoint (out of scope); a bolt-side `undersize` field (PAIR-07, v1.x); head chamfer or
washer face; DIN aliases (TABL-08). The part stays an internal milestone: version `0.0.x`, standing
warning on every info document ("not a product build" until Phase 6).

Roadmap and requirement wording resolved by this discussion (planner: build to this, not to the
loose text):
- SC2 "no default for it ships before Phase 6": `clearance` is a required field on the model, so
  the API answers `422 missing` and the CLI exits 2 when it is absent (D-01). L02 freezes a shipped
  default forever; a required field keeps Phase 6's measured value able to become the first one.
- SC3 "the full grid in a CI job against expected verdicts pre-registered from
  `2026-10-08-a-pair`": the verdict bodies are the spike's bodies (rod piece over m + 2P at c = 0,
  plain cylinder blank of radius d and height m less the void), so the recorded expectations
  transfer (D-05). The shipped solids are intersected as an evidence row, never a verdict input.
- SC1 "chamfers on both faces" and THRD-05 "under-head fillet": read with the owner's opening
  read of ISO 4032:2023 and ISO 4753. A single number in the text is used and cited; a band or no
  clause becomes one stated model recorded in the decision entry (D-12). The fillet is a revolved
  ring on a plain shank only; an ISO 4017 screw gets none and says so (D-11).
- SC4 "closed-form flank gaps": the pair rows on the nut's panel are kernel-free derivations of
  the radial clearance (radial, diametral, flank-normal, axial backlash, resulting nut diameters,
  engagement in turns); the kernel verdict never appears on the API or the page (D-19).
- SC6 "labels M18 from the cited record, not from a kernel call": a note on the nut info document
  keyed on `(d, pitch) == (18.0, 2.5)` exactly, any hand, any clearance (D-20).
- PAIR-04 "`screw pair` CLI subcommand": `screw pair nut <nut flags>`, one model, the rod nominal
  by definition (D-06).

</domain>

<decisions>
## Implementation Decisions

### Clearance field and the matching part
- **D-01:** `clearance` is a required field on `NutParams`: no default, so an empty nut link, a
  `GET /api/nut/info` without it and a `screw info nut` without `--clearance` are refused naming
  the field (`422 missing` on the API, exit 2 on the CLI). The form opens with the field empty and
  its hint; the page builds nothing until the user types a value, and the existing 422 path marks
  the field `.invalid` (no JS special case). Phase 6 adds the measured default as the first and
  only one (PAIR-02). The parity test learns one required field (today every field has a default)
  by a positive rule, not by loosening the check. — **Reversibility:** reversible — adding a
  default later changes no existing link's meaning, because every existing nut link carries the
  value; shipping a default now would be the one-way move L02 forbids before the test.
- **D-02:** The matching part (TYPE-04) is one key on the info document: `PartInfo.counterpart:
  {kind: str, fields: {name: value}} | null`, computed kernel-free in `calc`. Bolt → nut carries
  `d`, `pitch`, `left_hand`, and `s`, `m` from the ISO 4032 row when `(d, pitch)` sits on one;
  nut → bolt carries `d`, `pitch`, `left_hand`, and the ISO 4017 row's `s`, `k`. `clearance` is
  never in it (required; the user types it). The page renders a link `#kind=<kind>&<fields>` from
  the key generically (no field name, kind name or label in `app.js`; the parity source assertions
  hold); the API and `screw info` print the same key; the parity test asserts it.
  — **Reversibility:** costly — a published info-document shape every consumer reads.
- **D-03:** Off a row (custom `d` or `pitch`) the counterpart carries the shared fields only
  (`d`, `pitch`, `left_hand`); the target kind opens with its own frozen defaults for the rest and
  reads `custom`; the source document adds one pinned warning naming the fields to set (shape:
  `no ISO 4032:2023 row for d <d> pitch <P>; set s and m on the nut`, and the bolt-side analogue
  naming `s`, `k`, `length`, `thread_length`). Nut → bolt never invents a length: `length` and
  `thread_length` stay at the bolt's frozen 20 mm, a real ISO 4017 row for some sizes and `custom`
  for the rest. No nearest-row inference anywhere (04 D-09, L02).
- **D-04:** `clearance` takes any finite value, `le=INTERIM_MAX_MM`, no lower bound. The
  root-radius rule reads the clearance: `d/2 - 5H/8 + c <= 0` is a `422 pitch_too_coarse` naming
  `d`, `pitch` and `clearance`. c = 0 is the nominal nut (honest geometry, the STEP a CAD user
  wants); c < 0 is an interference nut the user explicitly asked for. The info document warns,
  pinned shape `clearance <c> is not positive: the pair cannot be proven (PAIR-03)`, and
  `screw pair` reads `inconclusive` by definition (D-14 of 02). This keeps the spike's c = 0 and
  c = -0.05 diagnostic rows reproducible through the product model.

### What the pair proof judges
- **D-05:** The verdict bodies are the spike's measured bodies, moved into `src/screw/solid/pair.py`
  from `bench/thread_spike/pair.py` (02 D-18: what was measured is what ships; the spike imports
  them back as Phase 3 did for `helical`): the rod piece `helical.thread(d, pitch, m + 2P,
  clearance=0)` from z = -P, and a plain cylinder blank of radius `d`, height `m`, less the void
  at the nut's clearance over the same span; screw-motion matched poses `(-2π/3, 0, +2π/3)` and
  their half-pitch controls; `BRepAlgoAPI_Common`; precise volume; `_KEEP`. `m` comes from the
  `NutParams` field (its default is the verified ISO 4032 row). The verdict is `cell_verdict` as
  `02-SPIKE.md` Rules write it (owner ruling R1, WR-04 amendment), unchanged: a control that reads
  empty at any pose is `inconclusive` naming the pose and the clearance, never `proven`; c ≤ 0
  inconclusive by definition; a mixed-hand pair `violated`; both hands through the same checks.
  A second, slower row intersects the shipped `solid.build(BoltParams)` and `solid.build(NutParams)`
  (counterparts, D-02) at the matched poses and is printed beside the verdict and recorded in
  `bench/RESULTS.md` as evidence, never a verdict input, until a later campaign pre-registers
  expectations for it. — **Reversibility:** costly — the expected-verdict table, the CI tier and
  the M18 label stand on these bodies; judging the shipped solids instead needs a new
  pre-registered campaign.
- **D-06:** `screw pair nut <nut flags>`: the nut carries everything the proof reads (`d`, `pitch`,
  `left_hand`, `clearance`, `m`); the rod is nominal by definition. Flags are generated from
  `NutParams` like `info` and `export`, so the parity test covers the command with no hand-written
  flag. The function is `screw.solid.pair.prove(p: NutParams) -> PairReport` (a frozen pydantic
  document: `verdict`, the per-pose matched and control readings, the control's closed form and
  band, `clearance`, `engagement_turns`, seconds; no kernel type escapes). The CLI prints the
  report as JSON and exits 0 on `proven`, 1 on `violated`, 2 on `inconclusive`.
  — **Reversibility:** costly — a published CLI and document shape.
- **D-07:** Tiers. `make verify` runs one same-hand proof cell at the frozen default size — M6,
  right hand, c = 0.10 mm, a `proven` cell in `2026-10-08-a-pair` — in a child process (the
  `_KEEP` teardown rule of quick task 261011-fzb), plus the kernel-free verdict-rule tests with
  positive controls (an empty control, a non-empty matched pose, c ≤ 0, a mixed-hand pair). The
  grid — 15 sizes × 2 hands × the 4 proof clearances, 120 same-hand cells, plus the mixed-hand
  cells — is a `pair` pytest marker deselected by `addopts`, run by `make pair [SIZE=]` and
  `.github/workflows/pair.yml` (`workflow_dispatch` plus a schedule, `contents: read`, one job per
  size, outside `ci.yml` and `required-jobs.txt`: the `grid.yml` shape, 03 D-14). Each cell is
  asserted against an expected-verdict table derived by a script from
  `bench/results/thread-spike/2026-10-08-a-pair.jsonl` (M18 `inconclusive` on both hands; each
  size's excluded clearances `inconclusive`, the rest `proven`; mixed-hand `violated`), committed
  before the first run and re-derived by a `make verify` test so it is never typed. The grid
  reproduces the recorded cells exactly: `(d, pitch, m, clearance, hand)` as recorded, the
  UNVERIFIED preview `m` included. **Planner alert:** where the verified ISO 4032 `m` differs from
  the recorded preview `m`, the product's `screw pair nut` at the row's `m` is a different cell;
  those are run and recorded as new evidence with the recorded verdict as the prediction, and a
  mismatch is reported in `bench/RESULTS.md` and the decision entry, never silently reclassified.
- **D-08:** The M18 control diagnosis (SC6) is one pre-registered probe: `05-M18-DIAGNOSIS.md`
  (Question, Environment, Method, Predictions, Escape clause — the `02-SPIKE.md` shape) commits
  before the probe runs, and the order is visible on `main` (02 D-19 precedent: the protocol lands
  as its own PR first, because `make pr.land` squashes). Probes fixed in advance and no others:
  (1) the failing control (theta -2π/3 right hand, +2π/3 left hand) repeated N times at one
  clearance to read determinism; (2) the same control at small theta steps either side of the
  failing pose; (3) the c = -0.05 cell's same pose; (4) `BRepAlgoAPI_Common` with a fuzzy value on,
  and with the operands swapped. The probe states its own deadline (the IN-02 debt item's 600 s is
  not re-used unexamined). Output: a `bench/RESULTS.md` entry and the finding in the L14 entry
  (reproducible or not; pose-local or not). Done is the entry written, whatever it says; no
  verdict rule, pose, constant or body changes (L11 revision direction, D-17 of 02). Until a later
  campaign proves M18, the M18 nut ships and reads `inconclusive`.

### Thread ends and the gate
- **D-09:** Lead-in chamfers (THRD-05): the bolt tip is one cone cut on the bare thread with the
  form, angle and length ISO 4753 gives as the owner reads them (D-14); the nut void gets a
  lead-in cone on both faces. The oracle stays kernel-free: `calc/thread.py` gains a midpoint
  integral of the thread section against the cone over the cut turns (the spike's
  `interference_area` recipe, 400 000 points, matched the kernel to 1e-5 relative), so
  `check_solid` compares the cut thread and the whole part at the same `T_GATE` with a positive
  control (a wrong cone angle or a missed cut the plain gate passes). Cost evidence: the
  `2026-10-08-a-trim` block (decisive; 0.19–0.31 s per trim at the standard max, M2–M12). Both
  ends stop being plain cuts; the standing warning is rewritten (D-18).
- **D-10 (where the cuts sit):** the bare-thread gate (L13) runs on the chamfered bare thread
  against `closed_volume − cone cut`; the whole-part gate runs after the fuses and the fillet
  against the sum of the closed forms. The nut's gate runs on the finished nut: hex prism
  `(√3/2) s² m` minus the void `section_area(d, P, c) · m` minus the face chamfers and the two
  lead-in cones (each a stated model with a kernel-free volume). A pre-plan probe (the 04 D-03
  pattern: a few sizes, both kinds, fine export, RSS) is recorded in `bench/RESULTS.md` as a probe
  before the plan fixes any expectation.
- **D-11:** The under-head fillet is a solid of revolution — a ring of radius `r` (the ISO 4014
  row's `r,min`, or the one value the owner reads at the checkpoint) swept round the shank/head
  junction — fused with the shank and the head, never an OCCT `fillet` operation; its volume is
  exact (a revolved quarter-circle: closed form), so `T_GATE` holds. Only where a plain shank of at
  least `r` exists (an ISO 4014 bolt with `length − t ≥ r`); an ISO 4017 screw, whose thread meets
  the head, gets none and its info document says so in a pinned note. Validity and cost are
  probed before the plan fixes an expectation (D-10). — **Reversibility:** costly — a later change
  alters the part every ISO 4014 link means with no field change; acceptable under the standing
  warning, a superseding entry after release (04 D-01).
- **D-12:** ISO 4032 face chamfers and the nut lead-in: the owner reads ISO 4032:2023 and ISO 4753
  first (D-14). A single number in the text is used and cited on the panel. A band (the 15–30°
  figure) or no clause becomes one stated model, written in the L14 entry as a model and labelled
  as such on any panel row it produces, never as a cited value (PITFALLS M5; L02 "a band is not a
  number" is honoured by naming the choice, not by inventing a row). The model derives from
  fields, not from a row value, so an off-row nut has the same ends (e.g. a cone from the inscribed
  circle of `s`, not from the row's `dw,min`; the planner states it once). The head keeps its
  plain prism (04 D-01; the head chamfer stays a deferred idea). — **Reversibility:** costly —
  as D-11.
- **D-13:** The gate keeps its shape: one solid, `isValid()`, precise volume inside `T_GATE` of the
  oracle, sign kept, inside the function `lru_cache` wraps; the nut adds the product rule
  `s <= d + 2c` → `422 nut_too_thin` naming `s`, `d` and `clearance` (a void wider than the flats is
  not a nut; the D-26 shape: policy, message names the fields).
- **D-14 (owner checkpoint, opens the phase):** one read session before any geometry plan,
  recorded in `05-OWNER-READS.md` like `04-OWNER-READS.md`: ISO 4032:2023 (the M6 row for the
  frozen `s`, `m` defaults; Annex A M2–M4; the chamfer figure or table; `mw`, `dw`, `e`; the
  designation clause and whether a left-hand form exists), ISO 724:2023 (`d2`, `D1`, `D2`: formula
  or table, as printed), ISO 965-2:2024 (which 6g and 6H columns exist for coarse M2–M20),
  ISO 4753 (the tip end form, angle, length; the ISO 4014/4017 reference to it). The full tables
  then follow Phase 4's ruling-B double entry (owner copy from the PDFs' text layer, agent image
  read, cell-by-cell diff in `make verify`, one relation test per row, UNVERIFIED refused).
  Precondition: the owner holds purchased copies of all four (STATE.md, TABL-04).

### Nut fields, defaults, rows and the panel
- **D-15:** `NutParams` fields: `d`, `pitch`, `left_hand` (base) plus `s` (across flats, title
  `Across flats`, group `Nut`), `m` (title `Height`, ISO symbol, group `Nut`) and `clearance`
  (title `Clearance (radial)`, group `Pair`, unit mm, help naming radial and that the diametral
  value is on the panel). `e`, `mw`, `dw` are reported from the ISO 4032 row only (04 D-05: a
  field that changes no geometry is not a field). `s` is declared on each kind, not on the base:
  same name and title, its own row-backed frozen default per kind, its own `s > d` rule with a
  nut-worded message; no link changes either way (L13). Flags: `--s`, `--m`, `--clearance`.
  Frozen defaults: the ISO 4032:2023 M6 row's `s` and `m` as the owner reads them (expected
  `s = 10.0`; `m` from the row, never from the preview), pinned by a row test like 04 D-07.
  — **Reversibility:** one-way — field names and frozen defaults are part of every nut link.
- **D-16:** ISO 965-2:2024 rows: only the limits the panel reports — bolt class 6g: major `d`
  max/min and pitch `d2` max/min; nut class 6H: minor `D1` min/max and pitch `D2` min/max — eight
  numbers per coarse size M2–M20, one typed row per (size, class) with `Source`, double entry under
  ruling B, one relation test per row (max above min; the nominal's position relative to the band
  as the standard prints it, e.g. 6g major max below nominal). Present only on an exact ISO 262
  `(d, pitch)` match, as a group whose heading is INFO-02's text verbatim (`limits for a bought
  part; this model is nominal and not toleranced`), each row labelled with its source like Phase 4
  (`Major diameter, max, 6g (ISO 965-2:2024 Table …)`); off-row they are absent and the no-row
  warning covers them. `d2`, `D1`, `D2` nominal rows come from ISO 724:2023 as read (formula or
  table) and are always present. The bolt's panel shows 6g, the nut's 6H.
- **D-17:** The `nut` kind's catalogue: axes `Standard`, `Size` (no `Length`; the page already
  builds its selects from the document's `axes`), ids `iso4032:M6`, display `ISO 4032 M6`,
  second-choice sizes bracketed (04 D-28), M2–M4 rows cited to Annex A with `informative /
  historical` in the display and as a note on the panel; a pick writes `d`, `pitch`, `s`, `m` and
  leaves `left_hand` and `clearance` alone. Designation as the standard spells it (owner's read;
  `null` for left-hand unless the clause gives a form, as L13).

### STL deflection and the preview file name (FRNT-06)
- **D-18 (the standing warning):** rewritten on every info document when the ends land, text
  pinned by the planner; "not a product build" stays until Phase 6 removes it (04 D-04). The
  ISO 4017 "no under-head fillet" note (D-11) is a note, not a warning.
- **D-19 (pair rows, kernel-free):** on the nut's panel only, group `Pair`: clearance radial and
  diametral (2c), flank-normal gap and axial backlash derived from the section maths (PITFALLS C5
  gives `0.5c` and about `1.155c`; the planner derives and pins them against `section_radius`,
  not from the research text), the resulting nut diameters (`D + 2c`, `D2 + 2c`, `D1 + 2c`),
  engagement `m / P` in turns. Every pair number traces to the `clearance`, `m` and `pitch` fields.
- **D-20 (the M18 label):** a note on the nut info document, pinned
  `kernel pair proof inconclusive at K = 3 (2026-10-08-a-pair)`, keyed on `(d, pitch) ==
  (18.0, 2.5)` exactly (the campaign's keys), any hand, any clearance, from the cited record and
  never from a kernel call (SC6, SC4).
- **D-21:** `TESSELLATION["fine"]` becomes a measured constant: the linear deflection is chosen by
  a stated rule — the mesh may consume at most a stated fraction of the smallest clearance the
  printed test will use, 0.05 mm (the spike's proof floor, 02 D-11) — from the `2026-10-08-a-ladder`
  evidence (h/4…h/32 of thread depth at angular 0.5 rad; bytes and triangles per size), recorded in
  the L14 entry with the run id and the rule. One mesh for bolt and nut, independent of the
  request. **Planner alert:** the L13 fine-STL bytes caps, the 62-preset refused count and the
  M20 × 200 preview figure were measured at the INTERIM 0.01 mm / 0.1 rad; if the rule's value is
  not that pair, those caps are re-derived from a recorded run at the new preset before the value
  ships (never left for Phase 7 as a known-stale number); if 0.01 mm satisfies the rule it is kept
  and its comment cites the rule and the ladder instead of spur. The researcher verifies how
  cadquery 2.8.0's `exportStl` sets `ControlSurfaceDeflection` on the pinned OCP (unverified
  today) and the plan pins it with a test that measures a mesh's deviation. The preview preset may
  stay coarser (0.08 mm > 0.05 mm) and is labelled so; no number on the panel comes from a mesh.
  — **Reversibility:** reversible — a constant with a cited run; Phase 7 re-sweeps (OPER-02).
- **D-22:** A non-default quality names itself: `Content-Disposition` gives `<slug>_preview.stl`
  for `quality=preview`; the fine STL and the STEP keep `<slug>.<ext>`. One rule shared by
  `app._serve` and `screw export`, pinned by a parity test, recorded in L14 with the deflection it
  stands for; `docs/ideas/2026-10-12-preview-stl-download-names-its-quality.md` moves to Done in
  the same commit. — **Reversibility:** costly — a published header.

### Decision entry and records
- **D-23:** A new `L14` in `docs/architecture/decision_log.md` records this phase's choices that
  later phases build on: the nut kind, fields and frozen defaults (D-15), the required clearance
  and its bound (D-01, D-04), the counterpart key (D-02, D-03), the pair proof bodies, function,
  CLI, tiers and the expected-verdict table (D-05 to D-07), the M18 finding (D-08), the end
  models and the numeric oracle (D-09 to D-13), the table rows (D-14, D-16, D-17), the panel
  groups (D-18 to D-20), the deflection rule and the file name (D-21, D-22). Every value cites its
  run id, its `05-OWNER-READS.md` line or its probe; nothing is tuned toward a pass.
  `docs/architecture/overview.md` gains the `nut` kind, `solid/pair.py`, the new tables and the
  new contract; `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md` lines this phase closes are amended.
- **D-24 (contract):** import-linter contract 9 lands with `solid/pair.py`: `screw.app` and
  `screw.pool` must not import `screw.solid.pair` by any path (`allow_indirect_imports = false`),
  with a runtime `sys.modules` probe like contract 6's, so the pair proof can never reach a route
  or a worker (SC4). `screw.cli` reaches it as it reaches `solid.export` today.

### Claude's Discretion
- `PairReport` field names and the JSON layout; the expected-verdict table's file format and
  location (under `tests/data/`), the deriving script, and the `pair.yml` schedule and sharding.
- The `pair` command's place in `tests/test_parity.py` (it serves the kinds that carry a
  `clearance`; the rule is positive and a planted stray flag fails it).
- The numeric oracle's integration recipe, its error bound against `T_GATE`, and its positive
  controls; where the cone cut and the fillet ring sit in `_build` relative to the two gates.
- The 422 and exit-2 wording beyond what D-01, D-03, D-04 and D-13 name; the `Nut` and `Pair`
  group names' exact strings; the `informative / historical` copy; the nut designation element.
- The nut page with `clearance` empty: the form, the `.invalid` mark from the 422, no build, the
  downloads disabled; `Reset` on the nut kind leaves `clearance` empty (it has no default).
- Whether the counterpart link is a button beside the kind selector or a line under the badge;
  its label is static text (`Matching nut`, `Matching bolt`) composed from `counterpart.kind`.
- The pre-plan probe's scope (sizes, both kinds, fine export, RSS) and its `bench/RESULTS.md`
  entry; whether it reuses `bench/quiet.py` (a probe is labelled non-decisive either way).
- How the ISO 4032 Annex A rows, the ISO 724 values and the ISO 965-2 rows are typed in
  `tables/` (the `Source` fields, the relation-test list beyond D-16's examples); the owner-copy
  generator's extension to the new PDFs.
- The order of plans: the owner read first (D-14), then the tables, the nut kind, the ends, the
  pair proof and tiers, the panel and FRNT-06; the M18 diagnosis protocol as its own PR before its
  probe runs, placed where it does not block the nut (D-08).
- The phase branch: `gsd/phase-05-hex-nut-and-kernel-pair-proof`, cut from `main` at `0ef52e8`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` § Phase 5 — goal, precondition, revision note, success criteria 1–6
  (read with the six resolutions in `<domain>`); § Phase 6 and § Phase 7 for what is not here
- `.planning/REQUIREMENTS.md` — THRD-05, PAIR-01, PAIR-03, PAIR-04, TYPE-03, TYPE-04, INFO-01,
  INFO-02, FRNT-06 (this phase); TABL-02…TABL-07 (the table rules the new rows obey); PAIR-02,
  PAIR-05, PAIR-06, INFO-04 (Phase 6 builds on this); FRNT-01…05 (the parity the new kind keeps);
  § Out of Scope (pair check as an endpoint, tolerance classes as geometry, DIN tables)
- `.planning/PROJECT.md` § Core Value, § Key Decisions (`clearance` on the nut; 6g/6H numbers
  only; first release = proven mating pair), § Context (spike before field; pre-registration)
- `.planning/STATE.md` § Blockers/Concerns — the Phase 5 precondition line (purchased copies),
  the ISO 4753 line, the M18 / L11 lines this phase acts on

### The locked inputs this phase builds on
- `docs/architecture/decision_log.md` — **L11** (Pair check paragraph: excluded clearances per
  size, the M18 reading, mixed-hand, sensitivity; Escape clause, revision direction paragraph:
  the rule the proof keeps and what was rejected), **L12** (builder signature with `clearance`,
  the gate, `MIN_TAIL_MM`, hand on the base), **L13** (bare-thread gate, fields and frozen
  defaults, presets, tables and ruling B, info document shape, caps at 0.01/0.1, `downloads`),
  L02, L04, L08, L09
- `.planning/phases/02-thread-spike/02-SPIKE.md` — § Owner rulings (R1: the verdict rule as
  written; pre-registered values: matched poses, `PAIR_BAND`, `EMPTY_MM3`, `T_PASS`), § Protocol
  inputs (`VOID_CLEARANCE`, `DIAGNOSTIC_CLEARANCES`, `CONTROL_OFFSET_PITCHES`, `TIP_CHAMFER_DEG`
  UNVERIFIED, the `NUT_HEIGHT` preview table), § Rules (`cell_verdict`, `size_falsifiable`,
  `excluded_clearances`, `mixed_hand_violated`, Completeness), § Results › Pair-check
  falsifiability, § Verdict
- `.planning/phases/02-thread-spike/02-CONTEXT.md` — D-11 to D-14 (the pair protocol), D-13
  (bodies: rod piece m + 2P, plain blank, no hex), D-18 (shaped to move into `src/`)
- `.planning/phases/03-real-helical-thread/03-CONTEXT.md` — D-08 (gate placement), D-09
  (`left_hand` on the base), D-14 (the slow tier shape), D-16 (plain ends, now replaced), D-17
  (`MIN_TAIL_MM`), Claude's Discretion (`TESSELLATION` deferred to FRNT-06 with the ladder)
- `.planning/phases/04-iso-hex-bolts-and-screws/04-CONTEXT.md` — D-01/D-02 (plain head, ends
  deferred here), D-03 (closed form, two planar fuses, the probe pattern), D-04 (standing
  warning this phase rewrites), D-05 (`s` move is Phase 5's call), D-09…D-12 (presets; the
  picker builds from `axes`), D-13…D-16 (tables, ruling B, UNVERIFIED gate, licence), D-17…D-20
  (info document, groups, notes), D-23/D-26 (the `s > d` policy shape), D-28 (brackets)
- `.planning/phases/04-iso-hex-bolts-and-screws/04-OWNER-READS.md` — the read-record shape
  `05-OWNER-READS.md` copies; ruling B's method
- `bench/RESULTS.md` — `### 2026-10-08-a-pair` (the cells, the M18 tables), `### 2026-10-08-a-verdict`
  (Pair check, Falsifiability, Variant rules, Reference K, Tip trim cost, Ladder), `### 2026-10-08-a-ladder`,
  `### 2026-10-08-a-trim`; `bench/results/thread-spike/2026-10-08-a-pair.jsonl` (the records the
  expected-verdict table is derived from) and `2026-10-08-a-ladder.jsonl`

### Research (the evidence behind the proof, the clearance and the ends)
- `.planning/research/ARCHITECTURE.md` § Q3 (what was measured, the `PairReport` sketch, where
  to expose it — the API/UI show closed-form gaps), § Q4 (one builder for rod and void), § Q5
  (STL cost), § Pair-proof flow, Anti-Patterns 3, 4, 7
- `.planning/research/PITFALLS.md` C4 (the proof that cannot fail), C5 (clearance sign, radial
  vs flank-normal vs axial; never scale), C8 (printed failure modes a kernel cannot see; Phase 6),
  C9 (mesh deviation vs thread depth; `ControlSurfaceDeflection`; mesh on a copy), C10 (ends,
  chamfer cost), M5 (chamfer model unspecified: document it once), § Pitfall-to-Phase Mapping
- `.planning/research/FEATURES.md` § Standards confirmed (ISO 4032:2023 M5–M39 normative, Annex A;
  ISO 724 formulas UNVERIFIED; ISO 965-2 numbers, 965-1 system; 4759 is not thread tolerance),
  § FDM (0.10–0.20 mm radial band is a prior only; units must be explicit), § Info panel (the
  nut, tolerance and pair rows), § Open questions Q1, Q2
- `.planning/research/SUMMARY.md` — P3/P5 rows, the FDM confidence notes

### The code that changes and the patterns it follows
- `src/screw/params.py` — `_f`, `_b`, `FastenerParams`, `BoltParams`, `KINDS`, the `after`
  validators with lazy imports (D-01, D-04, D-13, D-15: `NutParams`, the required field)
- `src/screw/calc/__init__.py` — `InfoRow`, `PartInfo` (`counterpart`, new groups), `_bolt`,
  `derive`, `STANDING_WARNING`, `download_refusal`, `explicit_conflict` (D-02, D-03, D-18…D-20)
- `src/screw/calc/thread.py` — `section_area(d, pitch, clearance)`, `closed_volume`,
  `hex_prism_volume`, `root_radius_refusal`, `volume_check`, `T_GATE` (D-04, D-09, D-10, D-13)
- `src/screw/calc/presets.py`, `src/screw/tables/presets.py` — `AXES`, `PresetCatalogue`,
  `catalogue`, `expand`, `FIELD_NAMES` (D-17: a second kind's catalogue)
- `src/screw/tables/rows.py`, `iso262.py`, `iso4014.py`, `iso4017.py` — `Source`, the row
  dataclasses and tests the ISO 4032, 724 and 965-2 rows copy (D-14, D-16)
- `src/screw/solid/__init__.py` — `_build` (kind dispatch; two gates), `check_solid`,
  `precise_volume`, `TESSELLATION` (D-10, D-13, D-21), `_write_export`
- `src/screw/solid/bolt.py`, `src/screw/solid/helical.py` — `thread`, `assemble`,
  `helical.thread(d, pitch, length, *, clearance, left_hand, k)` (D-09, D-11; the nut builder's
  sibling `solid/nut.py`)
- `bench/thread_spike/pair.py` — `rod_piece`, `nut`, `place`, `check_cover`, `common`, `_KEEP`
  (moves into `solid/pair.py`, D-05); `bench/thread_spike/maths.py` — `MATCHED_POSES`,
  `CONTROL_OFFSET_PITCHES`, `interference_area`, `INTEGRATION_POINTS`, `depth_presets`,
  `VOID_CLEARANCE`; `bench/thread_spike/verdict.py` — `cell_verdict`, `closed_control`,
  `PAIR_BAND`, `EMPTY_MM3`, the nut-body closed form
- `src/screw/app.py` — `/api/kinds`, `/api/schema`, `/api/presets`, the per-kind `info` and
  `model.{fmt}` routes with `refuse_explicit_conflict(kind)`, `_serve` and the
  `Content-Disposition` header (D-22)
- `src/screw/cli.py` — `_add_args`, `_params`, `cmd_info`, `cmd_export`, `cmd_presets`, the
  `sub.add_parser` loop over `KINDS` (D-06)
- `src/screw/static/app.js` — `navigate`, `buildForm`, `loadPresets`, `renderInfo`,
  `showMessages`, `refuseLink`; `index.html` (`#kind`, `#picker`, `#badge`, `.actions`) (D-02)
- `tests/test_parity.py` — `HAND_WRITTEN`, `PINNED_STATEMENTS`, `_field_literals`, the
  per-kind tests (every one now runs for two kinds); `tests/test_grid.py` and
  `.github/workflows/grid.yml` — the slow-tier pattern `pair.yml` copies (D-07);
  `tests/test_import_boundaries.py` — the `sys.modules` probe contract 9 copies (D-24)
- `tests/test_tables.py`, `tests/test_tables_second_entry.py`, `tests/data/owner/` — the
  double-entry and relation-test patterns; `pyproject.toml` `[tool.importlinter]` contracts 2, 6,
  7, 8 (widen for the new modules), contract 9 (new)
- `docs/tech_debt/active/2026-10-10-spike-protocol-amendments-before-next-campaign.md` — WR-03
  and IN-02 wait for the owner before the next campaign; the D-08 probe is not a campaign and
  states its own deadline
- `docs/ideas/2026-10-12-preview-stl-download-names-its-quality.md` — resolved by D-22

### UI contract and records this phase amends
- `.planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md` — Copywriting Contract
  (new strings), Interaction Contract rules 20 (kind selector; the counterpart link replaces
  the flagged ASSUMPTION), 29 (field names and row keys the source assertions list), 30–33
  (picker with two axes), Extension rules 1–3 (the clearance field and pair rows are named there
  for Phase 5)
- `docs/architecture/overview.md` — module map (nut kind, `solid/pair.py`, new tables, contract 9)
- `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` — rows for the deflection rule's
  consequences (D-21) and the pair tier's cost
- `docs/ideas/INDEX.md`, `docs/tech_debt/INDEX.md` — the row moves

### House rules
- `AGENTS.md` / `CLAUDE.md` (the gate, L02 rules, debt capture, cross-CLI review),
  `docs/CODING_VALUES.md`, `docs/HOW_TO_DEVELOP.md` (one PR per phase through `make pr.land`;
  the diagnosis protocol PR is a recorded exception in the 02 D-19 shape)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `helical.thread(d, pitch, length, *, clearance, left_hand, k)`: the one builder already makes
  the clearance-grown void; `section_area(d, pitch, clearance)` and `closed_volume` take the
  clearance, so the nut's closed form is `hex_prism_volume(s, m) − closed_volume(d, pitch, m,
  clearance)` before the end cuts.
- `bench/thread_spike/pair.py`: the measured pair check (rod piece, plain blank, screw-motion
  `place`, `check_cover`, `common` with `_KEEP`); `verdict.cell_verdict`, `closed_control`,
  `PAIR_BAND`, `EMPTY_MM3`: the rule and its band; `maths.interference_area`: the midpoint
  integral the end-cut oracle copies; `maths.depth_presets` and the ladder records: the FRNT-06
  evidence.
- `params._f` / `_b` and the `after` validators with lazy imports: `NutParams` is three `_f`
  calls (one without a default) and two validators (`s > d + 2c`, root radius with `c`).
- `calc.derive` dispatch, `InfoRow(group=…)`, `PartInfo.notes`, `download_refusal`,
  `explicit_conflict(kind, …)`: the nut's document is a sibling `_nut` with the same shapes;
  `counterpart` is one new optional key rendered generically.
- `calc.presets.catalogue_document` with `axes`, `tables/presets.catalogue`/`expand`: the page's
  picker already builds one select per axis from the document, so a two-axis nut catalogue needs
  no JS edit.
- `tables/rows.py` `Source` + `Status`, the UNVERIFIED scan, the ruling-B owner-copy generator
  and `tests/test_tables_second_entry.py`: the three new tables follow them verbatim.
- `solid._build` dispatch on the kind, `check_solid(part=…)`, the bare-thread-then-whole-part
  order, `_write_export` meshing a copy: the nut builder and the end cuts slot in; the deflection
  constant is one tuple.
- `cli._add_args` over `model_fields`, the `sub.add_parser(kind)` loops: `pair` is one more
  subparser family generated the same way.
- `app.js` `navigate`/`buildForm`/`renderInfo`: generic over kinds, groups and keys; the
  counterpart link and the empty required field ride on the existing 422 and hash code.
- `tests/test_grid.py` + `grid.yml`: the marker, `make` target, workflow pins and sharding the
  pair tier copies; the child-process pattern of the bench pair tests.
- `tests/test_import_boundaries.py`: fresh-interpreter `sys.modules` probes for contract 9.

### Established Patterns
- Validated once at the params boundary; a cross-field conflict is a `PydanticCustomError`
  naming the fields (`ctx.fields`); two explicit values in conflict are a request-boundary 422
  (L13 D-25), which the nut has no instance of yet.
- Pure maths kernel-free and logger-free (contracts 2, 4); tables a leaf (7); `params` never
  reaches `tables` (6); `solid` the only kernel doorway (8); `app` never imports the kernel (5).
- Every measured constant cites its run id in the comment; every INTERIM one says so and names
  Phase 7; a probe is recorded as a probe; a pre-registered protocol commits before its run and
  the order is visible on `main`.
- A positive control for every gate and rule; pinned user-facing strings asserted by tests and
  listed in the UI-SPEC Copywriting Contract; `app.js` reads nothing by a field, row, kind or
  group name.
- Debt retired in the fixing commit; ideas moved to Done in the commit that adopts them; a
  deliberate cut is a new item with a severity and a trigger.
- One PR per phase through `make pr.land`; the other CLI reviews; findings triaged in a
  disposition file before close.

### Integration Points
- `params.NutParams` + `KINDS["nut"]` ← fields, validators → `calc/thread.py` rules.
- `solid._build` → `solid/nut.py` (prism − void − end cuts) and `solid/bolt.py` (tip cone,
  fillet ring) → `check_solid` against the grown oracles; `solid/pair.py` (new, from bench) →
  `cli pair`; contract 9 in `pyproject.toml` + `tests/test_import_boundaries.py`.
- `calc.derive` → `_nut`, `counterpart` on both documents, the `Nut`/`Pair`/limits groups, the
  M18 note, the Annex A note, the rewritten standing warning, the ISO 4017 fillet note; the
  match code reads the new tables.
- New `src/screw/tables/{iso4032,iso724,iso965_2}.py` (names the planner's) ← owner copies in
  `tests/data/owner/`, second-entry files, relation tests; `tables/presets.py` serves two kinds.
- `app.py` → the per-kind routes exist by registry; `_serve` file name (D-22); `cli.py` →
  `pair` subcommand, `--clearance` required; `static/app.js` → counterpart link only.
- `.github/workflows/pair.yml`, `make pair`, `tests/test_pair.py` (marker, expected-verdict
  table, the verify cell), `tests/data/<expected verdicts>` + its deriving script.
- `05-M18-DIAGNOSIS.md`, `bench/<probe>.py`, `bench/RESULTS.md` entries (probe, diagnosis,
  pre-plan end-cut probe); `docs/architecture/decision_log.md` L14; `docs/architecture/overview.md`;
  `01-UI-SPEC.md` amendments; `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md` lines.
- gsd: `git.branching_strategy: phase`; branch `gsd/phase-05-hex-nut-and-kernel-pair-proof` from
  `main` at `0ef52e8`; one PR through `make pr.land`, plus the diagnosis-protocol PR (D-08).

</code_context>

<specifics>
## Specific Ideas

- Clearance warning, pinned shape: `clearance <c> is not positive: the pair cannot be proven
  (PAIR-03)`.
- Counterpart off-row warnings, pinned shape: `no ISO 4032:2023 row for d <d> pitch <P>; set s and
  m on the nut` / `no ISO 4017:2022 row for d <d> pitch <P>; set s, k, length and thread_length on
  the bolt`.
- M18 note, verbatim: `kernel pair proof inconclusive at K = 3 (2026-10-08-a-pair)`.
- Limits group heading, verbatim INFO-02: `limits for a bought part; this model is nominal and not
  toleranced`; row labels carry sense, class and source: `Major diameter, max, 6g (ISO 965-2:2024
  Table …)`.
- `screw pair nut --d 6 --pitch 1 --m <row> --clearance 0.1` prints `PairReport` JSON; exit 0
  proven / 1 violated / 2 inconclusive; an inconclusive report names the pose (theta) and the
  clearance whose control read empty.
- The verify cell: M6, right hand, c = 0.10 mm, `proven` in `2026-10-08-a-pair`; the grid: the
  recorded `(d, pitch, m, c, hand)` cells, M18 `inconclusive` both hands, excluded clearances per
  size from L11's list (M2 0.1, 0.2; M2.5 0.1; M3 0.05, 0.15; M4 0.05; M5 0.05; M7 0.05; M10 0.05,
  0.1; M12 0.05; M14 0.1; M3.5, M6, M8, M16, M20 none).
- M18 probes, fixed: repeat the failing control (theta -2π/3 right, +2π/3 left) N times; small
  theta steps either side; the c = -0.05 same pose; fuzzy value on; operands swapped.
- Preset id `iso4032:M6`, display `ISO 4032 M6`, `ISO 4032 (M7)`; M2–M4 display and note carry
  `informative / historical`.
- Preview file name: `<slug>_preview.stl`; fine STL and STEP unchanged.
- Deflection rule shape: fine linear deflection ≤ (stated fraction) × 0.05 mm, evidence
  `2026-10-08-a-ladder`, recorded with the rule and the run id in L14; the caps re-derived if the
  value moves from 0.01 mm / 0.1 rad.
- The opening owner read (D-14) writes `05-OWNER-READS.md`: ISO 4032 M6 `s`, `m` (+ `permanent:
  accepted`), Annex A rows, the chamfer figure, `mw`, `dw`, `e`, the designation clause; ISO 724
  `d2`, `D1`, `D2`; ISO 965-2 columns; ISO 4753 tip form.

</specifics>

<deferred>
## Deferred Ideas

- Judging the shipped solids as the pair verdict — after a campaign pre-registers expectations
  for them (the evidence row of D-05 is the input); not v1.
- Chamfered or washer-faced head (04 deferred) — unchanged; the nut's stated chamfer model
  (D-12) is the precedent if it ever lands.
- Run-out fade at the head side of an ISO 4017 screw (C10, `u ≤ 2P`) — not adopted; a change to
  L11's measured construction, re-measure first.
- A bolt-side `undersize` field (PAIR-06/PAIR-07) — Phase 6 decides after the bought-nut print.
- The clearance default and a "how to test your clearance" hint — Phase 6 (PAIR-02, INFO-06).
- Per-request STL deflection from the nut's clearance — rejected (D-21).
- Formulas from ISO 965-1 for off-row limits — rejected (not purchased, UNVERIFIED, plausible
  number for a non-ISO pitch).
- `mw`, `dw` as nut fields — rejected (D-15; report-only like the bolt's `e`, `dw`).
- Pair proof as an API endpoint — out of scope (REQUIREMENTS § Out of Scope).
- WR-03 and IN-02 protocol amendments — before the next campaign (debt item unchanged); the D-08
  probe is not a campaign.
- DIN 934 alias (TABL-08) — v2.
- Re-measuring the bytes caps on the finished bolt and nut, the pair tier's wall time on a
  GitHub runner, the deflection on linux/amd64 — Phase 7 (OPER-02).

</deferred>

---

*Phase: 05-hex-nut-and-kernel-pair-proof*
*Context gathered: 2026-10-14*
