# Phase 5: Hex Nut and Kernel Pair Proof - Research

**Researched:** 2026-10-14
**Domain:** parametric ISO 4032 hex nut kind, thread-end cuts with a kernel-free numeric oracle, a kernel pair-proof (BRepAlgoAPI_Common) judged by a pre-registered rule, CadQuery 2.8.0 / OCP 7.9.3.1.1, FastAPI + pydantic v2 required-field flow, import-linter, GitHub Actions slow tier
**Confidence:** HIGH on everything read from this repo or run against the installed `.venv` kernel this session; MEDIUM on CI-platform behaviour (nothing here ran on linux/amd64); the ISO 4032 / 724 / 965-2 / 4753 contents are NOT researched (paywalled, owner-read per D-14) and every such number is `[ASSUMED]` or absent.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01:** `clearance` is a required field on `NutParams`: no default, so an empty nut link, a
`GET /api/nut/info` without it and a `screw info nut` without `--clearance` are refused naming
the field (`422 missing` on the API, exit 2 on the CLI). The form opens with the field empty and
its hint; the page builds nothing until the user types a value, and the existing 422 path marks
the field `.invalid` (no JS special case). Phase 6 adds the measured default as the first and
only one (PAIR-02). The parity test learns one required field (today every field has a default)
by a positive rule, not by loosening the check. — **Reversibility:** reversible — adding a
default later changes no existing link's meaning, because every existing nut link carries the
value; shipping a default now would be the one-way move L02 forbids before the test.

**D-02:** The matching part (TYPE-04) is one key on the info document: `PartInfo.counterpart:
{kind: str, fields: {name: value}} | null`, computed kernel-free in `calc`. Bolt → nut carries
`d`, `pitch`, `left_hand`, and `s`, `m` from the ISO 4032 row when `(d, pitch)` sits on one;
nut → bolt carries `d`, `pitch`, `left_hand`, and the ISO 4017 row's `s`, `k`. `clearance` is
never in it (required; the user types it). The page renders a link `#kind=<kind>&<fields>` from
the key generically (no field name, kind name or label in `app.js`; the parity source assertions
hold); the API and `screw info` print the same key; the parity test asserts it.
— **Reversibility:** costly — a published info-document shape every consumer reads.

**D-03:** Off a row (custom `d` or `pitch`) the counterpart carries the shared fields only
(`d`, `pitch`, `left_hand`); the target kind opens with its own frozen defaults for the rest and
reads `custom`; the source document adds one pinned warning naming the fields to set (shape:
`no ISO 4032:2023 row for d <d> pitch <P>; set s and m on the nut`, and the bolt-side analogue
naming `s`, `k`, `length`, `thread_length`). Nut → bolt never invents a length: `length` and
`thread_length` stay at the bolt's frozen 20 mm, a real ISO 4017 row for some sizes and `custom`
for the rest. No nearest-row inference anywhere (04 D-09, L02).

**D-04:** `clearance` takes any finite value, `le=INTERIM_MAX_MM`, no lower bound. The
root-radius rule reads the clearance: `d/2 - 5H/8 + c <= 0` is a `422 pitch_too_coarse` naming
`d`, `pitch` and `clearance`. c = 0 is the nominal nut (honest geometry, the STEP a CAD user
wants); c < 0 is an interference nut the user explicitly asked for. The info document warns,
pinned shape `clearance <c> is not positive: the pair cannot be proven (PAIR-03)`, and
`screw pair` reads `inconclusive` by definition (D-14 of 02). This keeps the spike's c = 0 and
c = -0.05 diagnostic rows reproducible through the product model.

**D-05:** The verdict bodies are the spike's measured bodies, moved into `src/screw/solid/pair.py`
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

**D-06:** `screw pair nut <nut flags>`: the nut carries everything the proof reads (`d`, `pitch`,
`left_hand`, `clearance`, `m`); the rod is nominal by definition. Flags are generated from
`NutParams` like `info` and `export`, so the parity test covers the command with no hand-written
flag. The function is `screw.solid.pair.prove(p: NutParams) -> PairReport` (a frozen pydantic
document: `verdict`, the per-pose matched and control readings, the control's closed form and
band, `clearance`, `engagement_turns`, seconds; no kernel type escapes). The CLI prints the
report as JSON and exits 0 on `proven`, 1 on `violated`, 2 on `inconclusive`.
— **Reversibility:** costly — a published CLI and document shape.

**D-07:** Tiers. `make verify` runs one same-hand proof cell at the frozen default size — M6,
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

**D-08:** The M18 control diagnosis (SC6) is one pre-registered probe: `05-M18-DIAGNOSIS.md`
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

**D-09:** Lead-in chamfers (THRD-05): the bolt tip is one cone cut on the bare thread with the
form, angle and length ISO 4753 gives as the owner reads them (D-14); the nut void gets a
lead-in cone on both faces. The oracle stays kernel-free: `calc/thread.py` gains a midpoint
integral of the thread section against the cone over the cut turns (the spike's
`interference_area` recipe, 400 000 points, matched the kernel to 1e-5 relative), so
`check_solid` compares the cut thread and the whole part at the same `T_GATE` with a positive
control (a wrong cone angle or a missed cut the plain gate passes). Cost evidence: the
`2026-10-08-a-trim` block (decisive; 0.19–0.31 s per trim at the standard max, M2–M12). Both
ends stop being plain cuts; the standing warning is rewritten (D-18).

**D-10 (where the cuts sit):** the bare-thread gate (L13) runs on the chamfered bare thread
against `closed_volume − cone cut`; the whole-part gate runs after the fuses and the fillet
against the sum of the closed forms. The nut's gate runs on the finished nut: hex prism
`(√3/2) s² m` minus the void `section_area(d, P, c) · m` minus the face chamfers and the two
lead-in cones (each a stated model with a kernel-free volume). A pre-plan probe (the 04 D-03
pattern: a few sizes, both kinds, fine export, RSS) is recorded in `bench/RESULTS.md` as a probe
before the plan fixes any expectation.

**D-11:** The under-head fillet is a solid of revolution — a ring of radius `r` (the ISO 4014
row's `r,min`, or the one value the owner reads at the checkpoint) swept round the shank/head
junction — fused with the shank and the head, never an OCCT `fillet` operation; its volume is
exact (a revolved quarter-circle: closed form), so `T_GATE` holds. Only where a plain shank of at
least `r` exists (an ISO 4014 bolt with `length − t ≥ r`); an ISO 4017 screw, whose thread meets
the head, gets none and its info document says so in a pinned note. Validity and cost are
probed before the plan fixes an expectation (D-10). — **Reversibility:** costly — a later change
alters the part every ISO 4014 link means with no field change; acceptable under the standing
warning, a superseding entry after release (04 D-01).

**D-12:** ISO 4032 face chamfers and the nut lead-in: the owner reads ISO 4032:2023 and ISO 4753
first (D-14). A single number in the text is used and cited on the panel. A band (the 15–30°
figure) or no clause becomes one stated model, written in the L14 entry as a model and labelled
as such on any panel row it produces, never as a cited value (PITFALLS M5; L02 "a band is not a
number" is honoured by naming the choice, not by inventing a row). The model derives from
fields, not from a row value, so an off-row nut has the same ends (e.g. a cone from the inscribed
circle of `s`, not from the row's `dw,min`; the planner states it once). The head keeps its
plain prism (04 D-01; the head chamfer stays a deferred idea). — **Reversibility:** costly —
as D-11.

**D-13:** The gate keeps its shape: one solid, `isValid()`, precise volume inside `T_GATE` of the
oracle, sign kept, inside the function `lru_cache` wraps; the nut adds the product rule
`s <= d + 2c` → `422 nut_too_thin` naming `s`, `d` and `clearance` (a void wider than the flats is
not a nut; the D-26 shape: policy, message names the fields).

**D-14 (owner checkpoint, opens the phase):** one read session before any geometry plan,
recorded in `05-OWNER-READS.md` like `04-OWNER-READS.md`: ISO 4032:2023 (the M6 row for the
frozen `s`, `m` defaults; Annex A M2–M4; the chamfer figure or table; `mw`, `dw`, `e`; the
designation clause and whether a left-hand form exists), ISO 724:2023 (`d2`, `D1`, `D2`: formula
or table, as printed), ISO 965-2:2024 (which 6g and 6H columns exist for coarse M2–M20),
ISO 4753 (the tip end form, angle, length; the ISO 4014/4017 reference to it). The full tables
then follow Phase 4's ruling-B double entry (owner copy from the PDFs' text layer, agent image
read, cell-by-cell diff in `make verify`, one relation test per row, UNVERIFIED refused).
Precondition: the owner holds purchased copies of all four (STATE.md, TABL-04).

**D-15:** `NutParams` fields: `d`, `pitch`, `left_hand` (base) plus `s` (across flats, title
`Across flats`, group `Nut`), `m` (title `Height`, ISO symbol, group `Nut`) and `clearance`
(title `Clearance (radial)`, group `Pair`, unit mm, help naming radial and that the diametral
value is on the panel). `e`, `mw`, `dw` are reported from the ISO 4032 row only (04 D-05: a
field that changes no geometry is not a field). `s` is declared on each kind, not on the base:
same name and title, its own row-backed frozen default per kind, its own `s > d` rule with a
nut-worded message; no link changes either way (L13). Flags: `--s`, `--m`, `--clearance`.
Frozen defaults: the ISO 4032:2023 M6 row's `s` and `m` as the owner reads them (expected
`s = 10.0`; `m` from the row, never from the preview), pinned by a row test like 04 D-07.
— **Reversibility:** one-way — field names and frozen defaults are part of every nut link.

**D-16:** ISO 965-2:2024 rows: only the limits the panel reports — bolt class 6g: major `d`
max/min and pitch `d2` max/min; nut class 6H: minor `D1` min/max and pitch `D2` min/max — eight
numbers per coarse size M2–M20, one typed row per (size, class) with `Source`, double entry under
ruling B, one relation test per row (max above min; the nominal's position relative to the band
as the standard prints it, e.g. 6g major max below nominal). Present only on an exact ISO 262
`(d, pitch)` match, as a group whose heading is INFO-02's text verbatim (`limits for a bought
part; this model is nominal and not toleranced`), each row labelled with its source like Phase 4
(`Major diameter, max, 6g (ISO 965-2:2024 Table …)`); off-row they are absent and the no-row
warning covers them. `d2`, `D1`, `D2` nominal rows come from ISO 724:2023 as read (formula or
table) and are always present. The bolt's panel shows 6g, the nut's 6H.

**D-17:** The `nut` kind's catalogue: axes `Standard`, `Size` (no `Length`; the page already
builds its selects from the document's `axes`), ids `iso4032:M6`, display `ISO 4032 M6`,
second-choice sizes bracketed (04 D-28), M2–M4 rows cited to Annex A with `informative /
historical` in the display and as a note on the panel; a pick writes `d`, `pitch`, `s`, `m` and
leaves `left_hand` and `clearance` alone. Designation as the standard spells it (owner's read;
`null` for left-hand unless the clause gives a form, as L13).

**D-18 (the standing warning):** rewritten on every info document when the ends land, text
pinned by the planner; "not a product build" stays until Phase 6 removes it (04 D-04). The
ISO 4017 "no under-head fillet" note (D-11) is a note, not a warning.

**D-19 (pair rows, kernel-free):** on the nut's panel only, group `Pair`: clearance radial and
diametral (2c), flank-normal gap and axial backlash derived from the section maths (PITFALLS C5
gives `0.5c` and about `1.155c`; the planner derives and pins them against `section_radius`,
not from the research text), the resulting nut diameters (`D + 2c`, `D2 + 2c`, `D1 + 2c`),
engagement `m / P` in turns. Every pair number traces to the `clearance`, `m` and `pitch` fields.

**D-20 (the M18 label):** a note on the nut info document, pinned
`kernel pair proof inconclusive at K = 3 (2026-10-08-a-pair)`, keyed on `(d, pitch) ==
(18.0, 2.5)` exactly (the campaign's keys), any hand, any clearance, from the cited record and
never from a kernel call (SC6, SC4).

**D-21:** `TESSELLATION["fine"]` becomes a measured constant: the linear deflection is chosen by
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

**D-22:** A non-default quality names itself: `Content-Disposition` gives `<slug>_preview.stl`
for `quality=preview`; the fine STL and the STEP keep `<slug>.<ext>`. One rule shared by
`app._serve` and `screw export`, pinned by a parity test, recorded in L14 with the deflection it
stands for; `docs/ideas/2026-10-12-preview-stl-download-names-its-quality.md` moves to Done in
the same commit. — **Reversibility:** costly — a published header.

**D-23:** A new `L14` in `docs/architecture/decision_log.md` records this phase's choices that
later phases build on: the nut kind, fields and frozen defaults (D-15), the required clearance
and its bound (D-01, D-04), the counterpart key (D-02, D-03), the pair proof bodies, function,
CLI, tiers and the expected-verdict table (D-05 to D-07), the M18 finding (D-08), the end
models and the numeric oracle (D-09 to D-13), the table rows (D-14, D-16, D-17), the panel
groups (D-18 to D-20), the deflection rule and the file name (D-21, D-22). Every value cites its
run id, its `05-OWNER-READS.md` line or its probe; nothing is tuned toward a pass.
`docs/architecture/overview.md` gains the `nut` kind, `solid/pair.py`, the new tables and the
new contract; `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md` lines this phase closes are amended.

**D-24 (contract):** import-linter contract 9 lands with `solid/pair.py`: `screw.app` and
`screw.pool` must not import `screw.solid.pair` by any path (`allow_indirect_imports = false`),
with a runtime `sys.modules` probe like contract 6's, so the pair proof can never reach a route
or a worker (SC4). `screw.cli` reaches it as it reaches `solid.export` today.

Roadmap and requirement wording resolved by the discussion (CONTEXT `<domain>`; build to this, not to the loose ROADMAP text):
- SC2 "no default for it ships before Phase 6": `clearance` is a required field on the model, so the API answers `422 missing` and the CLI exits 2 when it is absent (D-01). L02 freezes a shipped default forever; a required field keeps Phase 6's measured value able to become the first one.
- SC3 "the full grid in a CI job against expected verdicts pre-registered from `2026-10-08-a-pair`": the verdict bodies are the spike's bodies (rod piece over m + 2P at c = 0, plain cylinder blank of radius d and height m less the void), so the recorded expectations transfer (D-05). The shipped solids are intersected as an evidence row, never a verdict input.
- SC1 "chamfers on both faces" and THRD-05 "under-head fillet": read with the owner's opening read of ISO 4032:2023 and ISO 4753. A single number in the text is used and cited; a band or no clause becomes one stated model recorded in the decision entry (D-12). The fillet is a revolved ring on a plain shank only; an ISO 4017 screw gets none and says so (D-11).
- SC4 "closed-form flank gaps": the pair rows on the nut's panel are kernel-free derivations of the radial clearance (radial, diametral, flank-normal, axial backlash, resulting nut diameters, engagement in turns); the kernel verdict never appears on the API or the page (D-19).
- SC6 "labels M18 from the cited record, not from a kernel call": a note on the nut info document keyed on `(d, pitch) == (18.0, 2.5)` exactly, any hand, any clearance (D-20).
- PAIR-04 "`screw pair` CLI subcommand": `screw pair nut <nut flags>`, one model, the rod nominal by definition (D-06).

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

### Deferred Ideas (OUT OF SCOPE)

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
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TYPE-03 | ISO 4032:2023 style 1 hex nut: `s`, `e`, `m`, `mw`, `dw`, chamfers both faces; M5-M20 normative, M2-M4 Annex A labelled "informative / historical" | Codebase Map (NutParams, tables, presets, `solid/nut.py`); verified kernel recipe: hex prism minus overshoot void builds one valid solid inside `T_GATE` for 8 sizes x 2 hands (<= 1.7e-6, 0.13-0.22 s); cone and chamfer cutters + exact oracles verified; the cone-must-pass-the-root pitfall (open mesh edges) |
| TYPE-04 | matching nut for any bolt and vice versa from the same `d`, pitch, hand and clearance | `PartInfo.counterpart` (D-02/D-03); `dict[str, float \| bool]` keeps JSON booleans (verified); generic link rule in `app.js`; `PINNED` source tests that must change |
| THRD-05 | nut thread and bolt tip lead-in chamfers, bolt under-head fillet (ISO 4753 clause owner-read) | Exact kernel-free oracles verified against the kernel (tip cone <= 7.9e-6 rel; countersink 1e-5 of removed; hex-corner chamfer 1e-7); revolved-ring fillet fuse verified (1 solid, valid, 1e-7); dilution warning: removed/added volumes fall below `T_GATE` of a long bolt |
| PAIR-01 | one `clearance` on the nut, radial mm; positive moves thread surfaces away from the axis; bolt nominal; panel shows radial and diametral | `helical.section(d, pitch, clearance)` already grows both radii; closed form `section_area(d, pitch, clearance)`; required-field flow verified end to end (422 `missing`, schema without `default`); same-name `_root_radius` override verified |
| PAIR-03 | kernel interference check -> `proven / violated / inconclusive` with control; c <= 0 inconclusive | Spike record walkthrough, pre-registered expected-verdict table derived (88 proven, 32 inconclusive same-hand cells; M18 all inconclusive), rule moved kernel-free into `calc`, `os._exit` requirement (exit 139 verified), mixed-hand signature gap, M6 verify cell reproduced `proven` in 35.0 s |
| PAIR-04 | function in the solid package, `screw pair`, slow tier (one size in verify, grid in CI), not an endpoint | `pair` marker/`make pair`/`pair.yml` modelled on `grid`; contract 9 TOML; `sys.modules` probe; `addopts` test pin that breaks; coverage-floor headroom (97.57% vs 96.00; ~20 elements) |
| INFO-01 | panel rows: nut (`s`,`e`,`m`,`mw`,`dw`,`D1`,`D2`), pair (clearance radial/diametral, resulting nut diameters, engagement) | D-19 derivations checked against `section_radius` (normal gap 0.5c, axial play 2c/sqrt(3)); `_nut` mirrors `_bolt`; groups and `InfoRow` generic page |
| INFO-02 | 6g/6H limits with the verbatim label | table-row pattern (`Source`, ruling B, relation tests), heading is a group name on `InfoRow.group` |
| FRNT-06 | STL and STEP from the same solid; chord deviation explicit, recorded, chosen against clearance; `ControlSurfaceDeflection` on for downloads | VERIFIED: cadquery 2.8.0 `exportStl` calls the 5-arg `BRepMesh_IncrementalMesh`; effective `ControlSurfaceDeflection` is True. MEASURED: realised radial centroid deviation is 0.9-1.8x the linear-deflection argument at fine (table below) - the rule must be on measured deviation, not the argument |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

Read `./CLAUDE.md` (symlink to `AGENTS.md`). Actionable directives the plans must honour:

- **Gate:** `make verify` (ruff, `mypy --strict` over `src tests docker bench scripts`, `lint-imports`, the unfinished-work scan, pytest under the 96.00 coverage floor). State the command and the result line in every reply. No Docker needed.
- **L02 standing rules:** a printed number is a number someone cuts metal to; no honest value = warning and no number. A parameter the user did not set never changes the part; defaults are absolute mm and frozen; a direct conflict between two explicit values is a `422` naming the fields; a trimmable dimension is capped and warned.
- **L04:** `Any` is never written (`disallow_any_explicit = true`); an untyped value is `object`, narrowed at use.
- **No `type: ignore` in `src/screw/`** (the scan in the Makefile refuses it); no `TODO|FIXME|XXX|HACK|NotImplementedError` in `*.py|*.js|*.sh`.
- Thread-maths (`screw.calc`, `params`, `cli`, `tables`) never imports `cadquery`/`OCP`; `cadquery` objects do not escape `screw.solid`; a parameter is validated once at the params boundary.
- Comments carry the measurement or constraint that forced the choice; every measured constant cites its run id; INTERIM constants say so and name Phase 7.
- New behaviour ships with its tests in the same change; a deliberate corner cut is a `docs/tech_debt/` item with the owner's sign-off; before the final reply state whether an item was filed and its path.
- Stop and ask on: an architectural claim not in the decision log, a locked decision that looks wrong, an acceptance criterion that cannot be met as written, an unverified library behaviour after a real check, conflicting evidence, a destructive operation.
- One concern per commit; Conventional Commits; the commit trailer comes from the session reminder. Work starts through a gsd entry point.
- **Project skills:** `.ai_skills/` holds only `README.md` ("starts empty on purpose"); `.claude/skills` is a symlink to it. There are no project skills to load; none were invented.
- Cross-CLI review: whoever wrote the diff does not review it.

## Summary

Phase 5 is large but almost every moving part has a measured precedent in this repo. The nut is a hex prism minus the L11 void (`helical.thread` with a clearance, overshooting the faces by one pitch each side), which I built for 8 sizes x both hands: always one valid solid, volume inside `T_GATE` by two to three orders of magnitude (<= 1.7e-6 against 9e-05), 0.13-0.22 s. The three end cuts (bolt tip cone, nut lead-in countersink, nut hex-corner face chamfer) each have an *exact* kernel-free oracle that needs no 400 000-point double integral: because a helical thread's transverse section is rotation-invariant, the removed volume is a one-dimensional integral over the cut depth of a closed-form per-radius area. I verified all three against the kernel on 4-8 sizes and both hands (tip cone within 8e-6 relative to the part, countersink 1e-5 of the removed volume, hex chamfer 1e-7). Under-head fillet as a revolved ring fuses cleanly onto the real bolt builder (1 solid, valid, 1e-7).

The pair proof moves almost verbatim, but five facts in this session change how it must be built. (1) Any process that runs `BRepAlgoAPI_Common` through the `_KEEP` pattern and exits normally dies with exit 139 at interpreter teardown (3 of 3 runs, in a spawned `multiprocessing` child 6 of 6, exit -11), so `screw pair` must end with a flush and `os._exit(code)` or its documented 0/1/2 contract is false, and every test of it is a subprocess. (2) The verdict rule (`cell_verdict`) and the closed-form control live in `bench/`, which `src/` cannot import; the kernel-free rule belongs in `screw/calc/` with `bench` importing it back, which also keeps contracts 2 and 4 and the spike's no-kernel contract intact. (3) The public signature `prove(p: NutParams)` cannot express the mixed-hand cells D-07 requires; an internal rod-hand parameter is needed. (4) The recorded expectations were measured on macOS arm64; this kernel pair is known to behave differently on linux/amd64 (L11 platform note), and the verify cell runs in the required `test (3.12)` CI job. (5) `make verify` coverage headroom is about 20 uncovered elements, so the kernel-bound part of `solid/pair.py` must be thin (orchestration injectable and covered in-process; only `common` runs in a child).

The FRNT-06 evidence changes the shape of D-21: realised chord deviation at the INTERIM fine preset (0.01 mm, 0.1 rad) measured 0.0094 to 0.0184 mm radial across M2-M20 - up to 1.8x the linear-deflection argument and 37% of the 0.05 mm proof clearance - while the preview preset (0.08, 0.5) measured 0.088 mm, more than the whole clearance. The "stated fraction" is therefore an owner decision with a concrete trade (0.01 mm survives only a fraction of at least about 0.37; a stricter fraction means roughly 0.005 mm and about 2.5x the triangles, which re-opens every L13 bytes cap).

**Primary recommendation:** Build in this order: owner read (D-14, nothing in this machine can read the PDFs) -> tables -> `NutParams` + the required-field flow across API/CLI/UI/parity -> kernel-free oracles in `calc` -> `solid/nut.py` and bolt ends behind the two gates -> `calc/pair.py` (rule) + `solid/pair.py` (bodies) with `os._exit` CLI and contract 9 -> panel/counterpart -> FRNT-06 measured test; put the M18 diagnosis protocol in its own earlier PR; pre-register the expected-verdict table in `tests/data/` (derived below) before the first pair-grid run.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Parameter validation (required `clearance`, `s <= d + 2c`, root radius with `c`, 250-turn cap on the void) | `params` (pydantic) | `calc.thread` rules | Validated once at the model boundary (CLAUDE.md); rules are kernel-free text/number functions the model imports lazily |
| Closed forms, end-cut oracles, pair rows, counterpart, limits rows | `calc` (pure maths) | `tables` (cited rows) | Runs per keystroke; no kernel, no logger (contracts 2, 4); tables only through `calc/presets.py` inside the function (contract 6) |
| Nut, tip cone, fillet ring, gates | `solid` (kernel) | - | The only OCP doorway (contract 8); gates run inside the `lru_cache` function |
| Pair verdict rule, expected-verdict table | `calc/pair.py` (kernel-free) | `tests/data/` | Pre-registered rule must not need the kernel; `bench` imports it back |
| Pair bodies and `prove()` | `solid/pair.py` | `cli` (lazy import) | Kernel work; reachable only from the CLI and tests (contract 9) |
| STL deflection, file name | `solid` (`TESSELLATION`) / `calc` (name rule) | `app._serve`, `cli.cmd_export` | One constant; one pure naming function both front ends call |
| Required-field UX, counterpart link | Browser (`app.js`, generic) | API 422 path | The page reads no field/kind name; the 422 marks the field |
| Slow tiers | CI (`pair.yml`) | `make pair` | Outside `ci.yml` / `required-jobs.txt` |

## Standard Stack

No new runtime or dev dependency is needed. Everything below is already pinned and was read from the installed `.venv` this session.

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| cadquery | 2.8.0 | solids, booleans, `exportStl`/`exportStep` | the kernel front end the repo is built on (L01) `[VERIFIED: .venv pip list]` |
| cadquery-ocp | 7.9.3.1.1 | `BRepAlgoAPI_Common`, `BRepMesh_IncrementalMesh`, `BRepGProp` | the pair proof and the gates use it directly inside `screw.solid` `[VERIFIED: .venv pip list]` |
| pydantic | 2.13.5 | `NutParams`, `PairReport`, `PartInfo.counterpart` | the one parameter model (L09) `[VERIFIED: .venv pip list]` |
| fastapi | 0.142.2 | nut routes, 422 shape | `[VERIFIED: .venv pip list]` |
| import-linter / grimp | 2.15 / 3.17 | contract 9 | `[VERIFIED: .venv pip list]` |
| pytest / pytest-xdist / pytest-cov | 9.1.1 / 3.8.0 / 7.1.0 | verify tier, `pair` marker | `[VERIFIED: .venv pip list]` |
| Python | 3.12.15 | only supported interpreter (L01) | `[VERIFIED: python3.12 --version]` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| mypy 2.4.0, ruff 0.16.10 | - | the gate | every change `[VERIFIED: .venv pip list]` |
| numpy 2.5.3 | transitive (casadi/vtk), NOT a project dependency | used only in my scratch probes | do not import it in `src/` or `tests/`; the deviation test below needs only `struct` and `math` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| 400 000-point double midpoint integral (D-09 text) | exact one-dimensional integral over the cut depth with closed-form per-radius area (`a_out` below) | The section is rotation-invariant, so the angle integral is exact and cheap; verified to the same or better agreement (<= 8e-6 relative) with no cache needed. Both are "Claude's Discretion"; the exact form is recommended, the spike recipe remains acceptable |
| `BRepFilletAPI` fillet under the head | revolved ring fused (D-11) | locked; verified feasible |
| centroid-radial mesh deviation metric | `BRepExtrema_DistShapeShape` per sample | radial deviation is a conservative UPPER bound of the true distance (the radial segment is one path to the surface), needs no kernel call in the test, and is what I measured |

**Installation:** none. **Version verification:** `.venv/bin/python -m pip list` run this session (versions above). `pyproject.toml` dependency list unchanged by this phase.

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| (none) | - | - | - | - | - | This phase installs no external package; `pyproject.toml` and `requirements.txt` are untouched |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Codebase Map: what exists, what changes (real paths and symbols)

All rows were read with `Read` this session.

### Source (`src/screw/`)
| File | Today | Phase 5 change |
|------|-------|----------------|
| `params.py` | `_f(default, *, gt, le, title, group, unit, step, help)` (requires `gt`), `_b`, `FastenerParams` (d, pitch, left_hand + `_root_radius` after-validator + `slug()`), `BoltParams`, `KINDS = {BoltParams.kind: BoltParams}`, `DEFAULT_KIND = "bolt"`, `INTERIM_MAX_MM = 1e5` | add `NutParams(FastenerParams)` with `kind = "nut"`; a required-field helper (no `gt`, `le=INTERIM_MAX_MM`, `allow_inf_nan=False`, no default); override `_root_radius` by **the same method name** (verified: replaces the inherited one) to read the clearance; `_nut_too_thin` (D-13), `_turn_cap` on the void length `m + 2*pitch`; register in `KINDS` |
| `calc/thread.py` | `T_GATE = 9e-05` (l.22), `MAX_TURNS = 250` (l.29), `MIN_TAIL_MM = 1e-3` (l.37), `section_radius`, `section_area(d, pitch, clearance=0.0)`, `closed_volume(d, pitch, length, clearance=0.0)`, `hex_prism_volume(s, k)`, `volume_check`, `root_radius_refusal(d, pitch)`, `turn_cap_refusal(t, pitch)`, `head_too_small_refusal`, `FINE_STL_ROWS` | clearance-aware root-radius text; `nut_too_thin_refusal`; `nut_closed_volume`; the three oracles (tip cone, countersink, hex-corner chamfer); keep it kernel- and logger-free |
| `calc/__init__.py` | `InfoRow`, `PresetMatch`, `Download`, `PartInfo` (kind, rows, warnings, designation, preset, notes, downloads), `STANDING_WARNING`, `NO_ROW_WARNING` (names ISO 4014/4017), `_bolt`, `derive` (isinstance dispatch, `TypeError` otherwise), `download_refusal` (isinstance dispatch), `_DOWNLOADS`, `_downloads`, `explicit_conflict` + `_EXPLICIT_CONFLICTS` (a registered kind without an entry raises) | `PartInfo.counterpart`; `_nut`; `derive`/`download_refusal` branches; `_EXPLICIT_CONFLICTS["nut"] = None`; nut `NO_ROW` warning; rewritten `STANDING_WARNING`; new group constants (`Nut`, `Pair`, the limits heading) |
| `calc/presets.py` | hard-wired to bolt: `match(p: BoltParams)`, `designation_for`, `row_values`, `notes`, `AXES = ["Standard","Size","Length"]`, `catalogue_document(kind)` and `expand(kind, id)` both raise `TypeError` unless `KINDS.get(kind) is BoltParams` | dispatch per kind; nut axes `["Standard","Size"]`; nut `match` compares `d, pitch, s, m` only (never `clearance`, never `left_hand`) |
| `tables/rows.py` | `Source(standard, edition, table, column, status)`, `Size`, `HexHead`, `SeriesLength`, `ThreadBand`, `ShankCell` (all `frozen, slots, kw_only`, no defaults) | add `HexNut`, an ISO 724 row, an ISO 965-2 (size, class) row; an explicit `informative` flag for Annex A rows |
| `tables/presets.py` | `PresetRow` (has `length`, `grade`, `head`, `band`, `cell`), `catalogue()` bolt-only `@cache`, `expand(id)` closed-set dict lookup, `FIELD_NAMES = ("d","pitch","length","s","k","thread_length")` | a nut row type and `catalogue`/`expand` per kind; ids `iso4032:M6` |
| `tables/iso262.py` | `SIZES` (15 sizes, `choice` 1/2, verified rows) | reused unchanged (nut M3.5/M7/M14/M18 are second choice: brackets) |
| `solid/__init__.py` | `_build(p)` raises `TypeError` unless `BoltParams` (bare-thread gate, then `bolt.assemble`, whole-part gate), `_build_checked` (wraps unknown exceptions in a bolt-worded `BuildError`: "check d, pitch, length, thread_length, s and k."), `_build_cached = lru_cache(...)`, `TESSELLATION = {"preview": (0.08, 0.5), "fine": (0.01, 0.1)}` (l.53), `check_solid`, `precise_volume`, `_write_export` (`shape.copy().exportStl(..., relative=False)`), `export` | kind dispatch in `_build`; kind-neutral `BuildError` wording; `TESSELLATION["fine"]` per D-21; file-name rule |
| `solid/bolt.py` | `thread(p)`, `assemble(p, bare_thread)` (shank planar fuse, then head fuse) | tip cone on the bare thread; fillet ring in `assemble` only when `length - t >= r` |
| `solid/helical.py` | `section`, `twist`, `thread(d, pitch, length, *, clearance=0.0, left_hand=False, k=DEFAULT_K)`, `DEFAULT_K = 3` (l.35), `SEWING_TOLERANCE = 1e-4`, `MAX_SEGMENTS = 500` | unchanged; the nut void and the pair bodies call it |
| `solid/nut.py`, `solid/pair.py` | new | nut builder; pair bodies + `prove` |
| `calc/pair.py` | new (recommended) | the kernel-free verdict rule (see "Where the rule lives") |
| `app.py` | per-kind routes are hand-written for bolt: `BoltModelQuery(BoltParams, _Quality)`, `bolt_info`, `bolt_model`, `strip(q, cls)`, `_serve` with `Content-Disposition: attachment; filename="{params.slug()}.{fmt}"`, `refuse_explicit_conflict(kind)` | `NutModelQuery`, `nut_info`, `nut_model` routes; D-22 name rule in `_serve`; update the module docstring route list. `/api/kinds`, `/api/schema`, `/api/presets` already registry-driven |
| `cli.py` | `_add_args` builds flags from `model_fields` with help `f"{field.description} [{field.default}]"`; `_params`; `cmd_info`, `cmd_export`, `cmd_presets`; one `sub.add_parser(kind)` loop | required-field help (`field.default` is `PydanticUndefined`); `pair` subcommand family; `cmd_pair` ends in `os._exit` |
| `static/app.js` | generic: `buildForm` sets `defaults[name] = prop.default`, `partQuery` compares `Number(value) !== Number(defaults[name])`, `renderInfo`, `problems()` marks `fields.get(d.loc?.[1])` `.invalid` | counterpart link only; see Pitfall P9 for the two traps |
| `static/index.html` | `#kind`, `#picker`, `#badge`, `.actions`, `#messages`, `#dims` | a counterpart anchor |
| `pool.py` | reaches the kernel only by `importlib.import_module("screw.solid")` at runtime | unchanged; generic over kinds already |
| `records.py` | `params: p.model_dump(exclude_defaults=True)` | works unchanged (a required field is always "non-default") |

### Tests, tooling, CI that must change (found by grep, not guessed)
| Place | Why it breaks |
|-------|---------------|
| `tests/test_parity.py` | `KINDS[kind]()` is called with no arguments in `test_every_row_key_is_unread_by_name_in_the_ui` (l.354) and defaults loops in `..._print_the_same_document` (l.283-311: `field.default * 1.5` on a required field has no default); `cli.main(["info", kind])` in `test_the_no_flag_is_a_value...` (l.346) exits 2 for nut; `..._form_has_a_size_fieldset_then_a_thread_one_then_a_head_one` asserts `groups == ["Size","Thread","Head"]` for every kind (l.431); `assert api_doc["warnings"][0] == (…"plain-cut thread ends…")` (l.310) is the old literal; `set(re.findall(r"\binfo\.(\w+)", APP_JS)) == {"designation","rows","warnings","notes","preset","downloads"}` (l.615) needs `counterpart`; `_cli_flags` expects `"{kind} parameters (defaults in brackets):"` |
| `tests/test_api.py` | l.128/133 `list(KINDS) == ["bolt"]` and `{"default":"bolt","kinds":["bolt"]}`; l.147, 184, 216-217 use `"nut"` as the unknown kind; l.232 pins `PartInfo` keys `{"kind","rows","warnings","designation","preset","notes","downloads"}` |
| `tests/test_calc.py` | l.191/216/301 `model()` with no arguments for every `KINDS` entry; l.623 `explicit_conflict("nut", …)` expects `TypeError: no explicit-conflict rule registered for kind 'nut'` |
| `tests/test_presets.py` | l.59-66 loops `KINDS` expecting `expand(kind, ROWS[0].id) == ROWS[0].fields`; l.63-66 expects `TypeError` matching `nut` from `expand("nut", …)` and `catalogue_document("nut")` |
| `tests/test_cli.py` | l.183-189 `["info","nut"]`/`["export","nut",…]` expected to exit 2 as an unknown kind; l.284 `presets nut` exit 2; l.246-254 flag order over `KINDS` |
| `tests/test_solid.py` | l.283-290 `p = model()` for every `KINDS` entry |
| `tests/test_params.py` | l.29-30 registry loop (fine) plus a nut default-row test to add |
| `tests/test_grid.py` | l.90 `assert "-m 'not grid'" in options["addopts"]` - changing `addopts` to `-m 'not grid and not pair'` breaks this literal substring; update the test; l.115 `assert "grid" not in ci` - keep `ci.yml` free of the word |
| `tests/test_bench.py` | l.519 `assert maths.INTERIM_PRESETS == TESSELLATION` - moving the fine preset breaks it; decouple (bench keeps the recorded campaign's literal) or update `maths.py` knowingly |
| `docker/smoke.py` | l.71-72 `get("/api/schema", b"kind=nut")` expects 404 - nut becomes registered; use another sentinel |
| `pyproject.toml` | l.115-116 `addopts`/`markers`; contract list; coverage `fail_under = 96` |
| `Makefile` | `.PHONY` list and a `pair` target modelled on `grid` (`$(PY) -m pytest -m pair -n $(PYTEST_WORKERS) --no-cov $(if $(SIZE),-k '$(SIZE)-',) $(PYTEST_ARGS)`) |
| `.github/workflows/grid.yml` | the template for `pair.yml`; `tests/test_grid.py` pins its shape (no `pull_request`/`push`, `permissions: contents: read`, no `secrets.`, matrix = `maths.SIZES`) |
| `bench/thread_spike/pair.py`, `verdict.py`, `maths.py` | import the moved bodies/rule back (pattern: `from screw.solid.helical import thread as thread`, `from screw.calc.thread import closed_volume as closed_volume`); `tests/test_bench.py` (4904 lines, 60 `nut` hits) pins them by name (`_KEEP`, `_span`, `rod_piece`, `nut`, `place`, `check_cover`, `common`, `cell_verdict`, `closed_control`) |
| `docs/architecture/decision_log.md` (L14), `overview.md` (module table, contract list, "No nut yet", `Nine are in force`), `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, `docs/ideas/INDEX.md` + the preview-name idea, `01-UI-SPEC.md` | D-23 |

### Contract numbering (for D-24)
`pyproject.toml` already holds 9 `[[tool.importlinter.contracts]]` blocks `[VERIFIED: lint-imports run: "Contracts: 9 kept, 0 broken."]`; `docs/architecture/overview.md` numbers eight of them and leaves "the spike's oracle, verdict and parent process stay free of the CAD kernel" unnumbered. D-24's "contract 9" is the next number in that scheme; the toml will then hold 10 blocks. Refer to it by its **name**, not by position.

## The spike record `2026-10-08-a-pair`

**Where:** `bench/results/thread-spike/2026-10-08-a-pair.jsonl` (273 lines = 1 header + 272 cells; sha256 `1644650ed5b418fc2b43bfa8fd875d371f0fc4940018f67b5b3241df6c84d9f3`, matches `bench/RESULTS.md` `### 2026-10-08-a-pair` at l.3313), `…-pair.md`, the verdict view at `bench/RESULTS.md` `### Pair check (D-11 to D-14)` (l.5599) and `#### Falsifiability (D-14)` (l.4962), protocol `.planning/phases/02-thread-spike/02-SPIKE.md`. Host: Apple M5 Max (18 CPUs), arm64, macOS, cadquery 2.8.0 / cadquery-ocp 7.9.3.1.1, HEAD `32cdeac`, decisive, K = 3 `[VERIFIED: bench/RESULTS.md l.3313-3330, jsonl header]`.

**Row keys:** `size, d, pitch, m, clearance, rod_left_hand, nut_left_hand, k, outcome, error, nut_volume, readings[{theta, offset_pitches, outcome, solids, volume, diag_errors, diag_warnings, seconds}], verdict, reasons, closed_control`. Parse with `verdict.parse_pair_result_row` (the run's own `verdict` key is dropped and recomputed).

**Cells:** per size, both same-hand pairs at c in `(0.0, -0.05, 0.05, 0.10, 0.15, 0.20)` and the mixed pair (right rod, left nut) at the four proof clearances = 16 cells x 15 sizes = 240, plus K = 5 and K = 10 reference rows at M2, M6, M10, M20 (4 sizes x 2 K x 4 clearances = 32) = 272 `[VERIFIED: cell count run]`. The product grid is K = 3 only (`helical.DEFAULT_K = 3`).

### Pre-registered expected verdicts (derived this session by running the unmodified `bench.thread_spike.verdict.cell_verdict` over the record at `0ef52e8`)
Same-hand cells, identical on right and left hand at every size. P = proven, i = inconclusive. Recorded `(d, pitch, m)` are the grid's cell keys (the `m` values are the spike's UNVERIFIED preview heights).

| Size | d | pitch | recorded m | c=0.05 | c=0.10 | c=0.15 | c=0.20 | excluded (i) |
|---|---|---|---|---|---|---|---|---|
| M2 | 2.0 | 0.4 | 1.6 | P | i | P | i | 0.1, 0.2 |
| M2.5 | 2.5 | 0.45 | 2.0 | P | i | P | P | 0.1 |
| M3 | 3.0 | 0.5 | 2.4 | i | P | i | P | 0.05, 0.15 |
| M3.5 | 3.5 | 0.6 | 2.8 | P | P | P | P | none |
| M4 | 4.0 | 0.7 | 3.2 | i | P | P | P | 0.05 |
| M5 | 5.0 | 0.8 | 4.7 | i | P | P | P | 0.05 |
| M6 | 6.0 | 1.0 | 5.2 | P | P | P | P | none |
| M7 | 7.0 | 1.0 | 5.6 | i | P | P | P | 0.05 |
| M8 | 8.0 | 1.25 | 6.8 | P | P | P | P | none |
| M10 | 10.0 | 1.5 | 8.4 | i | i | P | P | 0.05, 0.1 |
| M12 | 12.0 | 1.75 | 10.8 | i | P | P | P | 0.05 |
| M14 | 14.0 | 2.0 | 12.8 | P | i | P | P | 0.1 |
| M16 | 16.0 | 2.0 | 14.8 | P | P | P | P | none |
| M18 | 18.0 | 2.5 | 15.8 | i | i | i | i | 0.05, 0.1, 0.15, 0.2 (all) |
| M20 | 20.0 | 2.5 | 18.0 | P | P | P | P | none |

- Diagnostic clearances c = 0 and c = -0.05: `inconclusive` at every size and hand (by definition, `cell_verdict` returns "inconclusive by definition (D-11)" for `clearance <= 0`).
- Mixed hand (right rod, left nut) at c = 0.05, 0.10, 0.15, 0.20: `violated` at every size (60 cells).
- Totals: 120 same-hand proof cells = 88 proven + 32 inconclusive (44 + 16 per hand). The excluded sets match the L11 text and CONTEXT's list exactly `[VERIFIED: derive run; docs/architecture/decision_log.md l.349-351]`.
- **M18 poses** (`2026-10-08-a-pair`, all six same-hand cells per hand): right hand, the half-pitch control at theta -2.0944 (-2pi/3) reads 0 solids / volume 0.0 at *every* clearance including c = 0 and c = -0.05; the other two controls read ~300-394 mm3 near the closed form (e.g. c = 0.10: 336.6303 / 336.6301 vs closed form 336.632). Left hand: the failing pose is theta +2.0944. All matched poses read empty (correct); `diag_errors`/`diag_warnings` false on the failing reading. This is a one-observation-per-cell pattern: determinism is exactly what the D-08 probe measures `[VERIFIED: jsonl read this session]`.
- **Verdict reasons text** the report must reproduce: `control at theta -2.0944 reads empty (closed form 355.423 mm3)` (M18 right c=0.05) and the `+2.0944` form on the left hand.
- Recorded boolean seconds per cell (M5 Max, serial inside one worker): M6 right c=0.10 was 31.7 s; M6 cell range 16.7-137.3 s; M20 36.4-124.1 s; per-size sum of all k=3 cells: M2 395 s ... M16 1130 s, M20 1031 s; all k=3 cells 9962 s `[VERIFIED: jsonl sums]`.
- **I reproduced the verify cell**: `rod_piece(6,1,5.2,False,3)` + `nut(6,1,5.2,0.10,False,3)` + the six poses via `pair.common` -> `cell_verdict` = `('proven', ())`, controls 12.213 vs closed form 12.213, total 35.03 s on this host (M5 Max, serial) `[VERIFIED: scratch probe cell.py]`.

### Phase 4 pattern the `nut` kind should copy
Taken from `04-OWNER-READS.md`, `tables/*.py`, `tests/test_tables_second_entry.py`, `calc/presets.py`:
1. Owner opening read -> `05-OWNER-READS.md` with `permanent: accepted` for the frozen M6 `s`/`m` defaults (04 did this for ISO 4017 M6: `s` 10.0, `k` 4.0, `length` 20).
2. Rows as frozen keyword-only dataclasses with a required `Source(standard, edition, table, column, status)`; the column is the printed header incl. decimal comma and brackets (`"M2,5"`, `"(M3,5)"`); `status="verified"` only (the `unverified` scan refuses the rest).
3. Owner copy as TSV under `tests/data/owner/` (`size<TAB>…`), generated mechanically from the PDF text layer (ruling B) - the generator lives outside the repo (`/Users/halfb00t/Documents/standards/screw-owner-copy/make_owner_copy.py`, not present on this machine); the agent's independent transcription goes in `tables/*.py`; `tests/test_tables_second_entry.py` has `_SHAPE: dict[file, (key_columns, number_columns)]`, `read_owner`, `shipped()`, `diff()` - add three entries to `_SHAPE` and `shipped()`, and extend `test_the_owner_copy_is_not_vacuous` row counts.
4. One relation test per row in `tests/test_tables.py`; a frozen-default row test (`test_the_frozen_defaults_are_the_iso_4017_m6_row_the_owner_confirmed` pattern) for `NutParams()` `s`/`m`.
5. `PresetRow`-like catalogue: second-choice sizes bracketed in `display`/`picker` (`(M7)`), designation ASCII with the decimal comma (`"Hexagon head bolt ISO 4014 - M10 x 80"` precedent; left-hand = no designation).
6. `_row_value(key, sense, value, source, group)` labels each cited value `"{sense} ({standard}:{edition} {table})"` - reuse verbatim for `Major diameter, max, 6g (ISO 965-2:2024 Table …)`.

## Verified findings (run against the installed `.venv` this session)

Scratch probes lived in the session scratchpad and are not committed (D-10 asks the planner for a recorded, labelled-non-decisive probe in `bench/RESULTS.md` before any plan fixes an expectation; these numbers are research inputs to that probe's design, not a substitute). Host: Apple M5 Max, 18 CPUs, macOS arm64, Python 3.12.15, cadquery 2.8.0, cadquery-ocp 7.9.3.1.1. Single runs, not bounds, not linux/amd64.

### F1. cadquery 2.8.0 `exportStl` and `ControlSurfaceDeflection` (answers the D-21 "unverified today")
`[VERIFIED: .venv/lib/python3.12/site-packages/cadquery/occ_impl/shapes.py:484-515, read]` `exportStl(fileName, tolerance=1e-3, angularTolerance=0.1, ascii=False, relative=True, parallel=True)` calls `BRepMesh_IncrementalMesh(self.wrapped, tolerance, relative, angularTolerance, parallel)` and then `StlAPI_Writer().Write(...)`. It never sets `ControlSurfaceDeflection` itself. The 5-argument constructor leaves it at the `IMeshTools_Parameters` default. `[VERIFIED: probe mesh_ctor.py]` reading `BRepMesh_IncrementalMesh(shape, 0.01, False, 0.1, True).Parameters()` gave:
`ControlSurfaceDeflection True, Deflection 0.01, DeflectionInterior 0.01, Angle 0.1, AngleInterior 0.2, Relative False, InParallel True, AllowQualityDecrease False, MinSize 0.001, CleanModel True, InternalVerticesMode True, EnableControlSurfaceDeflectionAllSurfaces False, ForceFaceDeflection False`.
So "on for downloads" holds today **by default of the OCP struct, not by anything screw sets**; a cadquery or OCP bump could change it. Pin it two ways: (a) a test that builds `BRepMesh_IncrementalMesh(solid, lin, False, ang, True)` and asserts `.Parameters().ControlSurfaceDeflection is True` and `Relative is False`; (b) the behavioural deviation test (F2). `exportStl` is called with `relative=False` in `_write_export` (l.190-191), so `tolerance` is absolute mm.

### F2. What the "linear deflection" actually buys on a thread (the data D-21 needs)
`[VERIFIED: probes dev.py / dev2.py]` Method: a right-hand rod `helical.thread(d, pitch, 8*pitch)`, binary STL via `shape.copy().exportStl(...)`, parsed with `struct`; for sampled triangle centroids (every 5th-7th triangle, ends excluded by two pitches) compute `section_radius(d, pitch, 0, atan2(y, x) - 2*pi*z/pitch)` minus `hypot(x, y)`. The sign `+2*pi*z/pitch` is right-hand (mesh **vertices** matched the oracle surface to 1.2e-05 mm; the opposite sign gave 0.54 mm); a left-hand rod uses `-2*pi*z/pitch` (vertex error 1.2e-05 mm). The radial segment is one path from the centroid to the surface, so each sampled radial value is an **upper bound of that point's true distance to the surface**; the sampled maximum is not a proven bound of the mesh's global maximum (a sample, centroids only).

| Part | Preset (lin mm, ang rad) | Triangles | Max radial dev mm | p99 mm |
|---|---|---|---|---|
| M6 L8 | preview (0.08, 0.5) | 12 348 | 0.0880 | 0.0713 |
| M6 L8 | (0.05, 0.5) | 14 728 | 0.0755 | 0.0582 |
| M6 L8 | (0.0125, 0.1) | 77 548 | 0.0158 | 0.0089 |
| M6 L8 | fine (0.01, 0.1) | 88 846 | 0.0159 | 0.0070 |
| M6 L8 | (0.01, 0.5) | 79 784 | 0.0167 | 0.0071 |
| M6 L8 | (0.005, 0.1) | 212 452 | 0.0056 | 0.0045 |
| M2 L3.2 | fine / (0.005, 0.1) | 49 130 / 72 492 | 0.0094 / 0.0090 | 0.0067 / 0.0035 |
| M3 L4 | fine / (0.005, 0.1) | 58 020 / 89 176 | 0.0141 / 0.0079 | 0.0097 / 0.0036 |
| M10 L12 | fine / (0.005, 0.1) | 191 924 / 303 458 | 0.0184 / 0.0081 | 0.0081 / 0.0046 |
| M20 L20 | fine / (0.005, 0.1) | 316 938 / 783 488 | 0.0161 / 0.0059 | 0.0069 / 0.0042 |

Consequences for the plan: (1) the realised deviation at the INTERIM fine preset is **0.9x to 1.8x the linear-deflection argument** (max 0.0184 mm = 37% of the 0.05 mm proof clearance); the preview preset's 0.088 mm exceeds the whole 0.05 mm clearance, which is exactly why FRNT-06 lets only the preview be coarse and bars any panel number from a mesh. (2) D-21's "if 0.01 mm satisfies the rule it is kept" is true only for a fraction of 0.05 mm of about 0.37 or more; for a fraction like 1/4 (0.0125 mm) the measured 0.0184 (M10) fails and the next measured step (0.005 mm, max 0.0090) costs 1.5x (M2) to 2.5x (M20) the triangles, which re-opens every L13 bytes cap. **The fraction is an owner decision (it is not in the decision log): put it in the plan as a checkpoint with this table, do not choose it.** (3) State the rule on a *measured* deviation (the metric above), not on the `tolerance` argument, and say which sizes were sampled. (4) The metric is a pure function of `struct`, `math` and `section_radius`; no numpy, no kernel call in the assertion.

### F3. The nut body: hex prism minus an overshooting void
`[VERIFIED: probe nut_probe.py]` `cq.Workplane("XY").polygon(6, s, circumscribed=True).extrude(m).val().cut(helical.thread(d, pitch, m + 2*pitch, clearance=c, left_hand=lh).translate(cq.Vector(0, 0, -pitch)))` at c = 0.1 (s, m = the spike's UNVERIFIED preview heights, probe inputs only):

| Size | hands | solids | valid | rel. volume error vs `hex_prism_volume(s, m) - section_area(d, pitch, c) * m` | build s |
|---|---|---|---|---|---|
| M2 | R, L | 1 | True | +1.70e-06 | 0.13 |
| M3 | R, L | 1 | True | +1.23e-06 | 0.14 |
| M5, M6, M10 | R, L | 1 | True | -1.1e-07 to -2.1e-07 | 0.16-0.17 |
| M16, M18, M20 | R, L | 1 | True | -4.2e-07 to +2.0e-08 | 0.18-0.22 |

Both hands give the same error to the digit (the section is hand-independent). `polygon(6, s, circumscribed=True)` is the existing across-flats convention (`solid/bolt.py`). `hex_prism_volume(s, m)` is `sqrt(3)/2 * s * s * m`.

### F4. Exact kernel-free oracles for the three end cuts (the D-09/D-10 "numeric oracle")
`[VERIFIED: probes oracle.py, oracle2.py, ch.py, boltfull.py]` The transverse section is rotation-invariant, so for any radius `rho` the area the section pokes outside (or leaves inside) a disc has a closed form, and a cone cut is a one-dimensional integral over its depth; the helix phase and the hand drop out.
- `a_out(rho) = 0.5 * integral over one turn of max(0, r_s(theta)^2 - rho^2)`: crest flat `0.5 (ro^2 - rho^2) pi/4` if `rho < ro`; root flat `0.5 (rr^2 - rho^2) pi/2` if `rho < rr`; two flanks of angular width `5 pi/8`, with `k = ro - rr`: `(ro^3 - rr^3)/(3k) - rho^2` for `rho <= rr`, `(ro^3 - rho^3)/(3k) - rho^2 (ro - rho)/k` for `rr < rho < ro`, else 0; total `crest + root + 0.5 * 2 * (5 pi/8) * flank`.
- Bolt tip cone (cone meets the end face at the minor radius, angle `alpha` from the face, `rho(z) = minor + z / tan(alpha)`) removes `integral a_out(rho(z)) dz` over `z in [0, (d/2 - minor) tan(alpha)]` (`n = 20 000` midpoints). Kernel vs oracle on the **bare thread** (cut by `rod.intersect(revolved envelope)`, the `2026-10-08-a-trim` recipe): M6 R +2.16e-07, M6 L +2.86e-07, M2 R -4.68e-06, M2 L -7.91e-06, M20 R +3.91e-07, M20 L +4.74e-07, M18 R +3.93e-07, M18 L +4.89e-07 relative to the cut thread; 0.14-0.22 s per cut; always 1 solid, valid. The plain closed form misses the cut by -2.13e-03 (M6 L10) to -9.7e-04 (M20 L40), so the old gate would *refuse* a correct chamfered tip and the oracle is what restores it. `T_GATE` = 9e-05.
- Nut countersink (cone `rho(z) = r_f - z tan(half)` from the face), material removed `= integral mat_in_disc(rho(z)) dz` with `mat_in_disc(rho) = pi rho^2 - section_area(d, pitch, c) + a_out(rho)` (valid while `rho <= s/2`, the inscribed radius): kernel removed 6.49270949 mm3 vs oracle 6.49264475 mm3 (M6, one face, c = 0.1, `r_f = ro + P/2`, 45 degrees, probe inputs): 1.0e-05 relative to the removed volume.
- Hex-corner face chamfer (cone from radius `r0`, angle `beta` from the face), removed `= integral arc_inside(rho) * (rho - r0) tan(beta) drho` over `rho in [r0, R]`, with `a = s/2`, `R = a / cos(pi/6)`, `arc_inside(rho) = 2 pi rho` for `rho <= a`, `rho (2 pi - 12 acos(a / rho))` for `a < rho < R`, 0 above. Kernel on the bare prism 5.440107 mm3 vs oracle 5.440108 (`n = 40 000`; `n = 400 000` gives 5.4401076008: quadrature error 6e-09). **Trap:** the arc-inside formula is `rho (2 pi - 12 acos(a/rho))`; the first version I wrote (`12 rho acos(a/rho)`) was wrong by a factor of 2.2 - test the oracle against the kernel before trusting it.
- Whole finished nuts (countersink both faces + chamfer both faces) pass the same comparison once each term is checked separately; `removed = 2 * countersink + 2 * chamfer` is additive **only if the cutters do not overlap** (Pitfall P10).
- Fillet ring (a revolved region, area `r^2 (1 - pi/4)`, centroid offset `u_bar = (r^3/2 - (pi r^2/4)(r - 4r/(3 pi))) / A`; volume by Pappus `2 pi (d/2 + u_bar) A`): fused with `bolt.assemble(...)` result, 4 of 4 bolts one solid, valid, relative error -7.9e-08 (M10x80 b26, r = 0.4), -7.4e-08 (M6x30 b18, r = 0.25), -1.6e-08 (M20x100 b46, r = 0.8), -7.4e-08 (M6x30 left); fuse 0.03-0.05 s. The `r` values are probe inputs, not ISO values.
- Whole bolts (bare thread tip-cut -> `assemble` -> ring): 1 solid, valid, bare-thread oracle error 1.5e-09 to 4.5e-07, STL open edges 0 at preview and fine, build 0.37-0.55 s (ISO 4014 M10x80 b26, ISO 4017 M6x20, ISO 4014 M16x100 left).

### F5. The pair proof bodies and exit codes
- `[VERIFIED: probe exit_code.py]` A normal-exit process that called `bench.thread_spike.pair.common` (which parks the operation in `_KEEP`) exits **139** (3 of 3); the identical script ending `sys.stdout.flush(); sys.stderr.flush(); os._exit(2)` exits 2. A `multiprocessing` **spawn** child that calls `common`, returns its result through a queue and ends normally has `exitcode == -11` (6 of 6) although the parent already has the result. Consequences: `cmd_pair` must `os._exit(code)` after flushing; no test may call `cli.main(["pair", ...])` in the pytest process (it would kill the worker); CLI exit codes are tested with `subprocess.run([sys.executable, "-m", "screw", "pair", ...])`; a spawn-child test must not assert `exitcode == 0`.
- `[VERIFIED: probe mp_child2.py, inconclusive]` I could not get coverage data out of a spawned child with an ad-hoc rcfile (not even from a child that exited 0), so whether `coverage` records a spawned/segfaulting child under the project's `concurrency = ["multiprocessing", "thread"]` config is **not established**; do not plan on it (Pitfall P5).
- `[VERIFIED: dir(BRepAlgoAPI_Common)]` the option methods D-08 probe (4) needs exist in this OCP: `SetFuzzyValue`, `FuzzyValue`, `SetArguments`/`SetTools` (operand swap), `SetRunParallel`, `SetNonDestructive`, `SetGlue`, `SetUseOBB`, `SetCheckInverted`, `DSFiller`, `Check`. I did **not** run any of them against the M18 failing control - the protocol must commit first.
- `[VERIFIED: probe cell.py]` the M6 right-hand c = 0.10 cell with the spike functions: `('proven', ())`, matched 0/0/0, controls 12.213/12.213/12.213 (closed form 12.213), 35.03 s serial.

### F6. FastAPI/pydantic: a required field with no default
`[VERIFIED: probes req.py, override.py]` with `clearance: float = Field(..., le=INTERIM_MAX_MM, allow_inf_nan=False, title=..., description=..., json_schema_extra={"group": "Pair", "unit": "mm"})` on a `FastenerParams` subclass used as `Annotated[NutP, Query()]`:
- no `clearance` -> `422`, `{"type": "missing", "loc": ["query", "clearance"], "msg": "Field required", "input": {…the other fields' defaults…}}`; `clearance=-0.05` and `0.1` accepted; `clearance=` (empty) -> `float_parsing`; `clearance=inf` -> `finite_number`.
- `model_json_schema()` has `"required": ["clearance"]` and the property has **no `default` key** (`maximum` present, `group`/`unit` present, `title`/`description` as given); OpenAPI marks the query parameter `required: True`. `model_fields["clearance"].default` is `PydanticUndefined`, `.is_required()` is True; `NutP()` raises `ValidationError` of type `missing`.
- A subclass `@model_validator(mode="after") def _root_radius(self)` with the **same name** as the base's replaces the inherited rule: `d=2.0, pitch=2.0, clearance=0.5` was accepted (the base rule would have refused, rod root radius -0.083) and `clearance=0.0` raised `pitch_too_coarse` with `ctx.fields == ["d", "pitch", "clearance"]`.
- `class C(BaseModel): fields: dict[str, float | bool]` round-trips `{"left_hand": true, "d": 6.0}` as JSON `true`/`6.0` (smart union keeps `bool`), so `counterpart.fields` can carry `left_hand`; `PresetEntry.fields: dict[str, float]` (existing) cannot.

### F7. Flank gaps for D-19 (derived from the code, not from PITFALLS)
`section_radius` falls from `ro` to `rr` over `5 pi/8` of angle and `theta = 2 pi z / P`, so `|dr/dz| = (ro - rr) * 16/(5P) = 2H/P = sqrt(3)` (`ro - rr = 5H/8`), i.e. the flank is `dz/dr = 1/sqrt(3) = tan 30 degrees`. The nut surface is the rod surface shifted radially by `c`: flank-normal gap `c sin(30 degrees) = 0.5 c`; axial gap per flank `c tan(30 degrees) = 0.57735 c`; total axial play `2 c / sqrt(3) = 1.1547 c`; diametral `2c`; engagement `m / P` turns. These agree with PITFALLS C5's "0.5c and about 1.155c". Pin them in a test by evaluating `section_radius` (kernel-free), not by retyping the constants.

### F8. Mesh closedness of the finished nut
`[VERIFIED: probes nutmesh.py, nutmesh2.py]` With a countersink cone that ends **exactly at the root radius** `rr`, the M6 nut (valid, one solid, volume fine) meshed with **8 open edges (preview) and 4 (fine)** and the fine mesh took 6.77 s; M20 was watertight. With the same cone continued past the root (`ri = rr - 0.3`, `zi = z1 + 0.3`) every variant (both, countersink only, chamfer only, none) for M2/M6/M10 meshed with 0 open edges and fine meshing took 0.04-0.23 s. Neither `isValid()` nor the volume gate sees the defect; `_check_stl` checks only the header count and byte length. `bench/thread_spike/measure.py` `stl_check` (welds at 1e-5 mm, counts open edges) is the available check.

### F9. Coverage headroom
`[VERIFIED: full-suite run, 2637 passed in 40.19 s, TOTAL 1072 statements 202 branches, 97.57 %]` against `fail_under = 96` with `precision = 2`: about 31 statements/branches uncovered today, about 51 allowed at the current size, about 4 % of whatever new code is added. A new `solid/pair.py` that is exercised only through a subprocess would be uncovered.

## Architecture Patterns

### System Architecture Diagram

```
 browser (app.js, generic) --hash--> GET /api/schema?kind=nut  -> NutParams.model_json_schema()   (clearance: required, no default)
        |                            GET /api/presets?kind=nut -> calc.presets.catalogue_document   (axes Standard,Size)
        |  partQuery() omits an empty clearance
        v
 GET /api/nut/info?...  --Query model (NutParams: field + after validators: root radius with c, s<=d+2c, 250 turns on m+2P)--> 422 missing/pitch_too_coarse/nut_too_thin
        |  ok
        v
   calc.derive(NutParams) -> PartInfo{rows: Nut / Pair / limits groups, warnings: STANDING_WARNING + c<=0 + off-row,
        |                              notes: Annex A, M18 label, counterpart, downloads}      (no kernel, no table in params)
        v
 GET /api/nut/model.{stl,step}?quality= -> download_refusal -> _serve -> BuildPool -> solid.export
        |                                                                    |
        |                                                         _build_checked (lru_cache)
        |                                                          void = helical.thread(d,pitch,m+2P,clearance=c)   [bare gate vs closed_volume]
        |                                                          nut  = prism.cut(void).cut(2 countersinks).cut(2 chamfers)
        |                                                          check_solid(nut, hex - void - cuts)   [oracles from calc]
        |                                                          Content-Disposition: <slug>[_preview].<ext>
        v
 CLI:  screw info|export|presets nut ...                       screw pair nut ... --clearance c
                                                                  |  (lazy import; never from app/pool: contract 9)
                                                                  v
                                       solid.pair.prove(NutParams) -> rod_piece (m+2P, c=0) / blank (r=d, h=m) - void(c)
                                                                  |  place(theta, offset) x 6, common() -> (vol, solids,...)
                                                                  v
                                       calc.pair.rule(...) -> PairReport{verdict, readings, closed form, band, c, turns, s}
                                                                  |  stdout JSON; flush; os._exit(0|1|2)
 CI:  make verify: kernel-free rule tests + ONE child-process cell (M6 R c=0.10)       pair.yml: 15 sizes x cells vs tests/data expected table
```

### Recommended project structure (additions)
```
src/screw/
├── calc/pair.py            # kernel-free: PAIR_BAND, EMPTY_MM3, T_PASS, MATCHED_POSES, CONTROL_OFFSET_PITCHES, interference_area, closed_control, cell rule
├── calc/thread.py          # + nut_closed_volume, nut_too_thin_refusal, clearance-aware root radius, end-cut oracles
├── solid/nut.py            # void, prism, countersinks, chamfers (cutters as revolved profiles)
├── solid/pair.py           # _KEEP, rod_piece, blank, place, check_cover, common, prove (+ rod-hand parameter)
├── tables/iso4032.py  iso724.py  iso965_2.py
tests/
├── test_pair.py            # verify-tier (rule + one child cell) and the `pair`-marked grid
├── data/pair_expected.tsv  # derived by a script from the jsonl, committed before the first run
├── data/owner/iso4032.tsv  iso724.tsv  iso965_2.tsv
.github/workflows/pair.yml
```

### Where the verdict rule lives (recommendation, within Claude's Discretion)
`cell_verdict`, `closed_control`, `_nut_body`, `PAIR_BAND` (verdict.py l.1340), `EMPTY_MM3` (l.1343), `T_PASS` (l.47), `interference_area` + `INTEGRATION_POINTS` + `MATCHED_POSES` + `CONTROL_OFFSET_PITCHES` + `PAIR_CLEARANCES` + `DIAGNOSTIC_CLEARANCES` (maths.py) are kernel-free. `src/` cannot import `bench` (`bench` is not in the wheel: `packages = ["src/screw"]`), and the spike's contract forbids `bench.thread_spike.verdict/maths` from reaching the kernel by *any* path, so the rule must not move into `solid/pair.py` and be re-imported there. Put it in `screw/calc/pair.py` (contracts 2 and 4 keep it honest), have `bench.thread_spike.verdict`/`maths` re-export it (`from screw.calc.pair import cell_verdict as cell_verdict` - the pattern already used for `closed_volume`), and move the `PairReading`/`PairCell`/`PairRecord` `TypedDict`s and `Outcome`/`PairVerdict` literals with it so `tests/test_bench.py` keeps pinning the same names. Constants stay byte-identical: `PAIR_BAND = 1e-3`, `EMPTY_MM3 = 1e-6`, `T_PASS = 1e-4`, `MATCHED_POSES = (-2*pi/3, 0.0, 2*pi/3)`, `CONTROL_OFFSET_PITCHES = 0.5` (maths.py:181), `PAIR_CLEARANCES = (0.05, 0.10, 0.15, 0.20)`, `DIAGNOSTIC_CLEARANCES = (0.0, -0.05)` (maths.py:170, 174).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| the thread void and rod | a new helix/sweep | `helical.thread(d, pitch, length, clearance=c, left_hand=…)` | measured, gated, one construction (L11, L12) |
| the pair boolean | another intersection routine | the spike's `common` with `_KEEP` | what was measured is what ships (02 D-18); freeing the op segfaults |
| volume | `Shape.Volume()` | `precise_volume` (`BRepGProp` at eps 1e-6) | the default is 15-21 % off on some constructions (L11) |
| end-cut volumes | the kernel's own volume of the cutter | the exact oracles in F4 | the oracle must share no code with the kernel (calc/thread.py docstring) |
| under-head fillet | `fillet()` | revolved ring fused (D-11) | locked; verified; closed form |
| mesh closedness | trusting `isValid()` | `stl_check`-style edge pairing in a test sweep | F8: valid + exact volume + open mesh |
| required-field UI | a JS special case | the existing 422 `missing` path (`problems()` marks `.invalid`) | locked (D-01) |
| file name | string surgery in two places | one pure function in `calc` that `_serve` and `cmd_export` both call | D-22 "one rule shared" |
| expected-verdict table | typing it | a script that derives it from the jsonl with the rule, plus a `make verify` test that re-derives it | D-07 |
| workflow shape | a new CI style | copy `grid.yml` and its pin tests | T-3-14 posture |

**Key insight:** every number in this phase has a kernel-free twin (closed form or exact integral) that is cheaper than the kernel and independent of it; the work is wiring them, not inventing them.

## Common Pitfalls

### P1. The CLI exit code is a lie unless the process ends with `os._exit`
**What goes wrong:** `screw pair` would exit 139 (SIGSEGV at teardown) instead of 0/1/2. **Why:** F5. **Avoid:** `sys.stdout.flush(); sys.stderr.flush(); os._exit(code)` as the last statement of `cmd_pair`; tests via `subprocess`. **Warning sign:** exit status 139/-11 with a complete JSON on stdout.

### P2. Putting the rule where `bench` cannot reach it, or the kernel where `calc` can
Moving `cell_verdict` into `solid/pair.py` (as D-05's wording invites) breaks the spike's no-kernel contract the moment `bench.thread_spike.verdict` imports it back, and makes the verify-tier "kernel-free rule tests" import cadquery. See "Where the verdict rule lives".

### P3. `prove(p: NutParams)` cannot express a mixed-hand cell
D-07 asserts the mixed-hand cells (`rod_left_hand != nut_left_hand`) are `violated`, but `NutParams` has one `left_hand`. The rule needs the rod's hand independent of the nut's. Add an internal keyword-only `rod_left_hand: bool | None = None` (or a lower-level `prove_cell(d, pitch, m, clearance, rod_left_hand, nut_left_hand)`) that `prove` calls; do **not** expose it on the CLI or the model (a mixed pair is a rule test, not a product feature). This is a gap in CONTEXT; raise it, do not paper over it.

### P4. The recorded verdicts are macOS arm64; CI is linux/amd64
L11's platform note: the same cadquery/OCP pins gave different kernel results on ubuntu-latest than on macOS arm64. The verify cell (M6 R c = 0.10) runs inside the **required** `test (3.12)` job, so a platform difference turns every PR red, and the cell costs about 35 s on an 18-core M5 Max (the grid tier measured 3.1-7.1 s a row on GitHub runners against 1.6 s locally, so plan for 100+ s there - `[ASSUMED]`, extrapolated). **Avoid:** before the verify cell is merged, run it once on `ubuntu-latest` (a throwaway `workflow_dispatch` on the phase branch, or the first `pair.yml` dispatch) and record the result; if it disagrees with `proven`, that is a finding to surface to the owner (no rule or constant changes), not a flake to retry. `pair.yml` must record and not gate `main` (like `grid.yml`); mismatches against the macOS-derived table are written up, never reclassified (D-07).

### P5. Coverage floor 96.00 with about 20 elements of headroom
New kernel code run only in a child process is uncovered (F5). **Avoid:** keep `solid/pair.py` thin and inject `common` (a keyword argument or module-level seam) so `prove`'s whole orchestration - build, place, cover check, report assembly, c <= 0 short-circuit, error paths - is covered in-process by a fake that returns scripted `(volume, solids, errors, warnings, seconds)` tuples; only `common` itself (about 10 statements) is exercised in the child. `rod_piece`, `blank`, `place` and `check_cover` are safe in-process (`Shape.cut` leaves nothing in `_KEEP`; `tests/test_bench.py` already runs them in the pytest process). Re-measure with `make test` after each plan.

### P6. A required field breaks every `KINDS[kind]()` and "default document" assumption
See the table in the Codebase Map. Add one test helper (e.g. `tests.conftest` `sample(kind)` returning a valid instance with a stated `clearance`) and a positive rule in the parity tests: required fields are exactly those with `is_required()`, and every other field must still carry a default. `cli._add_args` prints `[{field.default}]` -> `[PydanticUndefined]` for `clearance`; print `[required]`. `test_a_foreign_field…`, `test_a_repeated_parameter…` already work per kind. The CLI "defaults in brackets" header the parity test greps for must stay.

### P7. A cone that ends exactly on the root surface (F8)
Valid solid, exact volume, **open mesh edges**, 60x slower fine mesh. Continue every countersink cutter past `rr` (into the void) so its surface crosses, never grazes, the root cylinder; extend every cutter past the faces it cuts. Add a mesh-closedness sweep over the nut catalogue (30 builds, preview mesh, about 0.2-0.3 s each) to the verify tier, and the same for the bolt ends (tip cone, ring).

### P8. The whole-part gate cannot see the tip cone or the fillet on a long bolt
`[VERIFIED: dilution.py]` Tip cone volume as a fraction of the bare thread: M6 L10 2.13e-03 (23.7 x `T_GATE`), L60 3.55e-04 (3.95 x), L250 **8.53e-05 (0.95 x)**; M2 L250 4.20e-05 (0.47 x). The fillet ring is 1.49e-04 of an M10x80 b26 (1.66 x), **6.54e-05 of an M10x200 (0.73 x)**, 2.34e-04 of an M6x30. So a missing cone or ring, or a wrong cone angle (30 to 45 degrees shifts M6 L250 by 6.2e-05), passes a gate at `T_GATE` on long parts. **Avoid:** keep `T_GATE` for the whole part as D-13 says, and add a *differential* check that is relative to the piece: the volume the cut removed (bare thread before vs after) or the fuse added, compared with the oracle's piece inside a stated fraction of that piece. The observed volume noise is about 1e-7 of the part (ring: 0.07 % of the ring), so a tolerance of a few percent of the piece discriminates. Positive controls: skip the cut; use 45 degrees for 30; drop the ring. This is a design point to put in the plan, not a locked-decision change.

### P9. `app.js` traps with a field that has no default
(a) `defaults[name] = prop.default` is `undefined` for `clearance`; `partQuery`'s `Number(value) !== Number(defaults[name])` is then `x !== NaN`, always true, so a typed `0` **is** written to the hash. Do not "fix" the default to `''`: `Number('')` is 0 and a typed `0` would vanish from the link (clearance = 0 is a legal nominal nut, D-04). (b) `write(input, undefined)` sets the string "undefined" on a number input (the browser sanitises it to empty; nothing in the gate runs a browser, L01) - make `write` use `v ?? ''` so Reset and navigation do not rely on that; the pinned statements in `PINNED_STATEMENTS` do not include the `else input.value = v;` line. (c) An empty clearance gives `422 missing` -> `fail()` -> the old **bolt mesh stays on screen with "Showing the last valid part"** after switching to the nut kind, and keeps the bolt's warnings and notes. D-01 says "the page builds nothing"; decide whether a kind switch should drop `mesh` (UI-SPEC amendment) or accept the stale-mesh label. (d) `test_the_ui_builds_both_download_links…` pins `set(re.findall(r"\binfo\.(\w+)", APP_JS)) == {…six keys…}`: add `counterpart` and keep `\bcounterpart\.(\w+)` to `{kind, fields}`. (e) The counterpart `fields` include `left_hand` as a JSON boolean; `q.set(name, value)` stringifies to `true`/`false`, which `navigate()` accepts. (f) Omit `kind=` when the target is `kinds.default` only if you want a short link; `update()` rewrites the hash anyway.

### P10. The additive end-cut oracle is only valid under stated conditions
`removed = 2*countersink + 2*chamfer` and each integral assume: countersink radius at the face `r_f <= s/2` (inside the inscribed circle, else `mat_in_disc` overcounts), `r_f <= r0` (the chamfer start; else the cutters overlap and are double-counted), `2*z1 <= m` (the two countersinks do not meet; `z1` is the countersink depth), and `(R - r0) tan(beta) <= m/2` (the chamfers do not meet). A nut with a small `m` (M2: m = 1.6 vs countersink depth about 0.5 per face at the probe's angle) is near these limits. The planner must state the model once (D-12) with these as validity conditions and decide what happens outside them (cap and warn per L02, or `422`); the oracle must integrate the *capped* depth if it caps.

### P11. The nut's void is `m + 2P` long
The 250-turn construction cap (`MAX_TURNS = 250`, `turn_cap_refusal(t, pitch)`) was measured on rod and void, so the nut's `_turn_cap` validator must judge `m + 2*pitch` (what `helical.thread` actually builds), naming `m` and `pitch`; judging `m` alone lets 250 < m/P <= 250 + 2 through. `MIN_TAIL_MM` is not a concern (`m + 2P` is far above it) but `helical.thread`'s doorway guard still applies.

### P12. Moving `TESSELLATION["fine"]` cascades
`tests/test_bench.py:519` pins `maths.INTERIM_PRESETS == TESSELLATION`; `FINE_STL_ROWS` (`calc/thread.py` l.277-292) and its message cite the 0.01 mm / 0.1 rad bytes; `bench/export_cost.py` and `bench/head_fuse.py` read `TESSELLATION["fine"]`; `calc/__init__.py` l.259 comment cites the pair. If the owner's fraction moves the value, the caps are re-derived from a *recorded run at the new preset* before it ships (D-21), which is a bench task with real cost (the grid fine-STL bytes at M8-M20 are 45-145 MB at the current preset). If it stays, the comment must cite the rule, the F2 table and `2026-10-08-a-ladder` (the ladder's fine rows: M6 L60 604 344 triangles, M20 L200 2 898 882).

### P13. `addopts` literal and `-k` ids
`addopts = "--strict-markers --strict-config -m 'not grid'"` becomes `-m 'not grid and not pair'` (a command-line `-m` still wins, so `make pair` works); `tests/test_grid.py` l.90 asserts the old substring and must be updated in the same commit; register the `pair:` marker next to `grid:` (`--strict-markers`). Cell ids should follow `M6-right-c0.1`, `M6-left-c0.1`, `M6-mixed-c0.1`: `-k 'M6-'` is a case-insensitive substring match and `M2-` must not pull `M12-`/`M2.5-` (the grid test pins exactly this; copy it).

### P14. `prove()` at c <= 0
`cell_verdict` returns "inconclusive by definition (D-11)" for `clearance <= 0` before it reads anything; the spike still took six booleans there (M6 c = 0: 137 s). Reading poses at c <= 0 buys no verdict. Recommend `prove` short-circuits (verdict + reason, no booleans, readings `[]`) - cheaper, no segfault-prone kernel call on a degenerate geometry - and the product keeps building the c = 0 / c = -0.05 nut solids for reproducibility (D-04). If the owner wants the readings recorded, make that an explicit option. (Open Question Q3.)

### P15. Derive the expected table from the *unmodified* rule, then freeze it
The table in this document came from `bench.thread_spike.verdict.cell_verdict` at `0ef52e8`. Commit `tests/data/pair_expected.*` (and its deriving script) in a commit **before** the rule moves and before any pair-grid run, and have the `make verify` re-derive test fail if the moved rule disagrees - that is what makes "no rule changed" checkable.

### P16. Environment surprises
`.venv/bin/coverage` has a stale shebang (`/Users/halfb00t/git/halfb00t/screw/.venv/bin/python`, no such path on this account): use `.venv/bin/python -m coverage`. `pdftoppm`/`pdftotext` (poppler) are not installed and no standards PDFs exist at `/Users/halfb00t/Documents/standards` or `/Users/half/Documents/standards`: the D-14 read and the ruling-B owner copy cannot be done by an agent on this machine.

## Code Examples

All run in the scratch probes named above; adapt names to the repo.

### E1. Required field helper and the nut's validators (F6)
```python
# params.py  (no `Any`; mypy --strict; `_f` cannot be reused: it requires `gt` and a default)
def _req(*, le: float, title: str, group: str, unit: str = "", step: float | None = None,
         help: str = "") -> float:
    extra: JsonDict = {"group": group, "unit": unit}
    if step is not None:
        extra["step"] = step
    return Field(..., le=le, allow_inf_nan=False, title=title, description=help,
                 json_schema_extra=extra)

class NutParams(FastenerParams):
    kind: ClassVar[str] = "nut"
    s: float = _f(10.0, gt=0, le=INTERIM_MAX_MM, title="Across flats", group="Nut", unit="mm",
                  step=0.1, help="Width across flats of the hexagon nut (ISO symbol s).")
    m: float = _f(<owner-read M6 m>, gt=0, le=INTERIM_MAX_MM, title="Height", group="Nut", unit="mm",
                  step=0.1, help="Nut height (ISO symbol m).")
    clearance: float = _req(le=INTERIM_MAX_MM, title="Clearance (radial)", group="Pair", unit="mm",
                            step=0.01, help="...radial mm; the diametral value is on the panel")

    @model_validator(mode="after")
    def _root_radius(self) -> Self:   # same name: replaces FastenerParams._root_radius (verified)
        from screw.calc.thread import root_radius_refusal
        if (msg := root_radius_refusal(self.d, self.pitch, self.clearance)) is not None:
            raise PydanticCustomError("pitch_too_coarse", msg, {"fields": ["d", "pitch", "clearance"]})
        return self
```

### E2. The exact oracles (F4) - kernel-free, in `calc/thread.py`
```python
def _outside_disc_area(d, pitch, clearance, rho):        # a_out
    ro, rr = _radii(d, pitch, clearance); k = ro - rr
    total = 0.0
    if rho < ro: total += 0.5 * (ro**2 - rho**2) * math.pi / 4
    if rho < rr: total += 0.5 * (rr**2 - rho**2) * math.pi / 2
    if rho <= rr:   flank = (ro**3 - rr**3) / (3 * k) - rho**2
    elif rho < ro:  flank = (ro**3 - rho**3) / (3 * k) - rho**2 * (ro - rho) / k
    else:           flank = 0.0
    return total + 0.5 * 2 * (5 * math.pi / 8) * flank

def nut_material_in_disc(d, pitch, c, rho):              # rho <= s/2
    return math.pi * rho**2 - section_area(d, pitch, c) + _outside_disc_area(d, pitch, c, rho)

def arc_inside_hex(a, rho):                              # a = s/2
    R = a / math.cos(math.pi / 6)
    if rho <= a: return 2 * math.pi * rho
    if rho >= R: return 0.0
    return rho * (2 * math.pi - 12 * math.acos(a / rho))
# tip: sum(_outside_disc_area(d, pitch, 0, minor + (i+.5)*h/ tan(alpha)) for i in range(n)) * h, h = depth / n
```

### E3. Cutters that cross, never graze (F8)
```python
def _revolved(profile: list[tuple[float, float]]) -> cq.Shape:
    # XZ workplane: local (x, y) is (radius, z); revolve about local y = global Z
    return cq.Workplane("XZ").polyline(profile).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()

# countersink on the face z = 0: reaches r_f at the face, continues to `ri < rr` at depth `zi > z1`
csk_bottom = _revolved([(0, -1.0), (r_f + 1.0, -1.0), (ri, zi), (0, zi)])
csk_top    = _revolved([(0, m + 1.0), (r_f + 1.0, m + 1.0), (ri, m - zi), (0, m - zi)])
# face chamfer: triangle outside radius r0, extended past the corners
ch_bottom  = _revolved([(r0, 0), (R_big, 0), (R_big, (R_big - r0) * tan_beta)])
ch_top     = _revolved([(r0, m), (R_big, m), (R_big, m - (R_big - r0) * tan_beta)])
nut = prism.cut(void).cut(csk_bottom).cut(csk_top).cut(ch_bottom).cut(ch_top)
```
Bolt tip (the `trim_tip` recipe, cone at z = 0): `rod.intersect(_revolved([(0, t + 1.0), (outer, t + 1.0), (outer, run), (minor, 0.0), (0, 0.0)]))` with `outer = d/2 + 1`, `run = (outer - minor) * tan(alpha)`.

### E4. `cmd_pair` ending (P1)
```python
def cmd_pair(ns: argparse.Namespace) -> None:
    from .solid.pair import prove          # lazy: loads the kernel only here
    report = prove(_params(ns.kind, ns))    # NutParams
    print(report.model_dump_json(indent=2))
    sys.stdout.flush(); sys.stderr.flush()
    os._exit({"proven": 0, "violated": 1, "inconclusive": 2}[report.verdict])
```

### E5. Contract 9 and its runtime probe (D-24)
```toml
[[tool.importlinter.contracts]]
name = "The serving process and its workers never import the pair proof"
type = "forbidden"
source_modules = ["screw.app", "screw.pool"]
forbidden_modules = ["screw.solid.pair"]
allow_indirect_imports = false
```
`[VERIFIED: probe il.toml]` import-linter 2.15 reports a `forbidden` contract whose `forbidden_modules` entry does not exist as **KEPT** (no error, no warning), so a misspelt module name passes vacuously: the contract must land in the same commit as `solid/pair.py` (CONTEXT D-24) and the runtime `sys.modules` probe below is the control that the name is right. `screw.solid/__init__.py` must **not** import `pair` (every `screw.solid` importer would inherit the edge). The runtime half copies `tests/test_import_boundaries.py::_loads_tables`: fresh `python -I -c "import sys; import screw.app; print('screw.solid.pair' in sys.modules)"` is False, with a control that `import screw.solid.pair` prints True. `pool` reaches the kernel only by `importlib.import_module("screw.solid")` (pool.py l.51, 63), so it has no static edge today. `screw.cli` is not in `source_modules`; its lazy import is fine.

### E6. `pair.yml` skeleton (copy of `grid.yml`, `tests/test_grid.py` pins the shape)
```yaml
name: pair
on:
  workflow_dispatch:
  schedule:
    - cron: "23 4 * * 1"
permissions:
  contents: read
jobs:
  pair:
    runs-on: ubuntu-latest
    timeout-minutes: 240      # sizing UNVERIFIED on runners; see P4 / Open Question Q6
    strategy:
      fail-fast: false
      matrix:
        size: [M2, M2.5, M3, M3.5, M4, M5, M6, M7, M8, M10, M12, M14, M16, M18, M20]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12", cache: pip}
      - run: make pair PYTHON=python SIZE=${{ matrix.size }}
      - name: kernel pair this run resolved
        if: always()
        run: .venv/bin/python -c "from importlib.metadata import version; print('cadquery', version('cadquery'), 'cadquery-ocp', version('cadquery-ocp'))"
```

### E7. The deviation test (F2), no numpy
```python
def _radial_deviations(stl: bytes, d: float, pitch: float, hand: int) -> list[float]:
    n = struct.unpack("<I", stl[80:84])[0]
    zs = []
    ...  # per facet: 9 floats at offset 84 + 50*i + 12; centroid -> (x, y, z)
    # sign = +1 right hand, -1 left; skip facets within 2*pitch of either end
    # dev = section_radius(d, pitch, 0.0, atan2(y, x) - hand * 2*pi*z/pitch) - hypot(x, y)
```
Assert `max(dev) <= <fraction> * 0.05` at the rule's preset for a stated list of sizes and both hands, and that a deliberately coarse preset **fails** it (the positive control).

### E8. Counterpart model
```python
class Counterpart(BaseModel):
    model_config = ConfigDict(frozen=True)
    kind: str
    fields: dict[str, float | bool]      # bool survives JSON (F6)
# PartInfo.counterpart: Counterpart | None = Field(description=...)
```

## State of the Art

| Old approach | Current approach | When changed | Impact |
|--------------|------------------|--------------|--------|
| Plain planar thread ends (03 D-16, 04 D-01) | cone-cut tip and countersunk nut faces behind an exact oracle | this phase | `STANDING_WARNING` rewritten; plain closed form no longer matches (-2e-3) |
| Interim `TESSELLATION` carried from spur | rule on measured deviation vs the proof clearance | this phase (D-21) | F2 table |
| Pair check in `bench/` | `calc/pair.py` rule + `solid/pair.py` bodies | this phase | contract 9; `os._exit` CLI |

**Deprecated/outdated:** `bench.thread_spike.maths.NUT_HEIGHT` preview heights and `TIP_CHAMFER_DEG = 30.0` are UNVERIFIED protocol inputs (ISO 4032 / 4753 unread); they remain the *recorded campaign's* inputs and must not be silently replaced by owner-read values inside the expected-verdict table (D-07).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | A GitHub `ubuntu-latest` runner runs the M6 verify cell in roughly 100 s or more (3-4x the 35 s measured here), extrapolated from the grid tier's 3.1-7.1 s a row against 1.6 s locally | P4, Validation | `make verify` on CI gets slower than the plan budgets; not wrong in kind, only in size |
| A2 | The exit-139-at-teardown behaviour of `_KEEP` also occurs on linux/amd64 (verified on macOS arm64 only; L11's own record says exit 139 was "provoked once" in research) | F5, P1 | If linux does not segfault, `os._exit` is merely redundant there; no harm. If it differs in the other direction, nothing breaks |
| A3 | ISO 724 gives `d2 = d - 0.6495 P` and `D1 = d - 1.0825 P` as the basic-profile values (from training knowledge; the code's `minor_diameter` row already uses `d - 2*(5H/8)` which equals the second) | INFO-01 | Rows would be wrong if the owner's read differs; D-14 makes the owner's read the source, so nothing ships from this claim |
| A4 | The ISO 4032 chamfer is expressed as a band/angle (CONTEXT D-12 mentions "the 15-30 degree figure") rather than one number | D-12 | Changes whether the chamfer is a cited value or a stated model; resolved at the owner read |
| A5 | ISO 4753 is a 2011 edition (a store listing shows "ISO 4753:2011") and the owner's purchased copy is that edition | Sources | The edition in the `Source` rows must be what the owner holds; check at the read |
| A6 | ISO 4032 has no M3.5 row (the spike wrote "M3.5 2.80: 0.8 * d, no ISO 4032 row" and "ISO 4032:2023 added M7") | Open Q5 | If M3.5 has no row the nut catalogue has 14 sizes and `iso262` M3.5 has no nut counterpart (D-03 off-row warning applies); if it has one, a row to enter |
| A7 | A browser sanitises `input.value = "undefined"` on a number input to the empty string (no browser runs in the gate, L01) | P9 | Reset on the nut would show the word instead of an empty field; the `v ?? ''` guard removes the dependency |
| A8 | `coverage`'s `multiprocessing` concurrency would or would not record a spawned child that segfaults at teardown | F5, P5 | Not established either way (my attempt collected no child data at all); the plan must not depend on it |
| A9 | The `pair.yml` cron minute/hour (`23 4 * * 1`) and `timeout-minutes: 240` are placeholders | E6 | Cosmetic; sizing needs a first run (the grid precedent was "UNVERIFIED" until run 38240380994) |

## Open Questions

1. **What fraction of the 0.05 mm proof clearance may the download mesh consume? (owner decision)**
   - What we know: F2 - fine (0.01, 0.1) realises up to 0.0184 mm (37 %); (0.005, 0.1) realises up to 0.0090 mm (18 %) at 1.5-2.5x the triangles; preview realises 0.088 mm.
   - What's unclear: the fraction. It is not in the decision log and D-21 leaves it as "a stated fraction".
   - Recommendation: a `checkpoint:decision` in the FRNT-06 plan presenting the F2 table; the plan then states the rule on measured deviation, runs the L13 caps re-derivation only if the value moves, and records the rule and run id in L14. Do not pick 0.37 to keep 0.01 mm (that is a rule chosen after seeing which value passes).

2. **How does `prove` express a mixed-hand pair? (gap in CONTEXT D-06/D-07)**
   - What we know: `prove(p: NutParams)` has one `left_hand`; D-07 requires the mixed-hand cells.
   - Recommendation: internal keyword-only `rod_left_hand: bool | None = None` (default: same hand as the nut); the CLI and the model stay single-hand.

3. **Does `prove` read poses at c <= 0?**
   - What we know: the verdict is "inconclusive by definition" before any reading; the spike spent six booleans per such cell (M6 c = 0: 137 s) and c = 0 produced garbage reads in research.
   - Recommendation: short-circuit with the pinned reason and no readings; keep the c = 0 / -0.05 nuts buildable (D-04).

4. **D-22 "one rule shared by `app._serve` and `screw export`" - but `export` takes `-o <path>` from the user.**
   - Recommendation: one pure function `download_name(params, fmt, quality)` in `calc`; `_serve` uses it for `Content-Disposition`; `cmd_export` uses it as the file name when `-o` is an existing directory and names the quality in its `wrote …` line otherwise. Surface to the owner if "shared" was meant more strongly.

5. **Which sizes have ISO 4032 rows?** (A6) M3.5 and M7 need the owner's read; the Annex A M2-M4 rows carry `informative`.

6. **Verify-cell placement vs the required CI job (P4).** If the first `ubuntu-latest` run of the M6 cell disagrees with `proven`, the phase has a decision the owner must make; no rule or constant may change (L11 revision direction).

7. **Stale bolt mesh on a kind switch with an empty clearance (P9c).** Needs a UI-SPEC call (drop the mesh on a kind change, or accept the label).

8. **Cutter-overlap policy for small `m` (P10).** Cap and warn, or `422`; whichever is chosen the oracle must integrate what the kernel cuts.

9. **Differential-gate tolerance for the tip cone and the fillet (P8).** Choose with a recorded probe (noise about 0.07 % of the ring was observed); put the rule in the plan before the code.

10. **Where the shipped-solid evidence row (D-05, second row) places the nut on the bolt.** Keep the nut inside the full-thread span (clear of the tip cone and the head/shank) or the intersection mixes in features the rod-piece row never saw.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | everything (L01) | yes | 3.12.15 | - |
| `.venv` with dev extras | `make verify` | yes | cadquery 2.8.0, cadquery-ocp 7.9.3.1.1, pytest 9.1.1, import-linter 2.15 | `make venv` |
| Docker | `make smoke`, the `image` CI job | yes | 29.8.2 | - (verify needs none) |
| `gh` | `make pr.land`, `pair.yml` dispatch | yes | 2.102.0 | - |
| Node | `make vendor-check` | yes | v26.11.0 (CI uses 22) | - |
| poppler (`pdftoppm`, `pdftotext`) | D-14 owner read and ruling-B copy | **no** | - | owner's own machine (Phase 4 used `brew install poppler`) |
| Purchased standards PDFs (ISO 4032:2023, 724:2023, 965-2:2024, 4753) | D-14, TABL-04 | **no** (not at `/Users/halfb00t/Documents/standards`, not at `/Users/half/Documents/standards`) | - | none - the owner reads and replies; no row ships from a preview or from this document |
| Owner-copy generator `make_owner_copy.py` | ruling B | **no** (lives outside the repo on the owner's account) | - | the owner extends and runs it |
| linux/amd64 kernel run | P4, F5 | not on this host | - | first `pair.yml` / throwaway dispatch |

**Missing dependencies with no fallback:** the standards and the owner's read - they block every table row and the frozen nut defaults (`s`, `m`), hence every plan that depends on them. Schedule the D-14 checkpoint first, as CONTEXT says.
**Missing dependencies with fallback:** poppler and the generator (owner machine).

## Validation Architecture

Framework: pytest 9.1.1 with xdist (`-n 8` clamped to online CPUs), pytest-cov under `fail_under = 96`, `filterwarnings = ["error"]`, `xfail_strict`. Config `pyproject.toml` `[tool.pytest.ini_options]`; `testpaths = ["tests"]`.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 + pytest-xdist 3.8.0 + pytest-cov 7.1.0 |
| Config file | `pyproject.toml` (`addopts`, `markers`, coverage) |
| Quick run command | `make test PYTEST_ARGS="tests/test_calc.py -q -n0 --no-cov"` (one file; `-n0` serial; `--no-cov` because a partial run reads a low total) |
| Full suite command | `make verify` (lint, mypy --strict, lint-imports, no-fake-done, pytest + coverage); currently 2637 passed in 40.19 s, 97.57 % |
| Slow tiers | `make grid` (existing), `make pair [SIZE=M6]` (new), both deselected by `addopts` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test type | Automated command | File exists? |
|--------|----------|-----------|-------------------|-------------|
| TYPE-03 | `NutParams` fields, frozen M6 `s`/`m` equal the owner-read row; nut builds through both gates for every catalogue row, both hands | unit + kernel (about 0.2 s a build) | `pytest tests/test_params.py tests/test_solid.py -k nut` | params/solid files exist; nut tests Wave 0 |
| TYPE-03 | ISO 4032 / Annex A rows: relation test per row, second entry diff, UNVERIFIED refused | data | `pytest tests/test_tables.py tests/test_tables_second_entry.py -k "4032 or 724 or 965"` | files exist; rows and `tests/data/owner/*.tsv` Wave 0 (blocked by D-14) |
| TYPE-03 | `informative / historical` on M2-M4 preset display and panel note | unit | `pytest tests/test_presets.py tests/test_calc.py -k informative` | Wave 0 |
| TYPE-04 | counterpart both ways, off-row shared fields + pinned warning, `clearance` never in it, API = CLI document | unit + parity | `pytest tests/test_calc.py tests/test_parity.py -k counterpart` | Wave 0 |
| THRD-05 | tip-cone / countersink / chamfer oracles vs the kernel at several sizes and both hands; positive controls (no cut, wrong angle, dropped ring); differential check; fillet only where `length - t >= r`; ISO 4017 note | unit (oracle, kernel-free) + kernel | `pytest tests/test_thread_maths.py tests/test_solid.py -k "tip or csk or chamfer or fillet"` | `tests/test_thread_maths.py` exists; rest Wave 0 |
| THRD-05 | nut and bolt STL watertight (0 open edges) over the nut catalogue and the bolt ends | kernel sweep | `pytest tests/test_solid.py -k watertight` | Wave 0 (reuse `bench.thread_spike.measure.stl_check` or copy its edge pairing) |
| PAIR-01 | positive `clearance` enlarges the nut thread, bolt untouched; radial and diametral rows; required: 422 `missing`, CLI exit 2, UI marks `.invalid` (source assertion) | unit + API + CLI | `pytest tests/test_params.py tests/test_api.py tests/test_cli.py tests/test_parity.py -k clearance` | Wave 0 |
| PAIR-03 | the rule: empty control -> `inconclusive` naming pose and clearance; matched pose non-empty -> `violated`; c <= 0 inconclusive; mixed-hand -> `violated`; nut body off closed form -> `inconclusive`; both hands | unit (kernel-free, `calc/pair.py`) | `pytest tests/test_calc_pair.py` (name free) | Wave 0 |
| PAIR-03 | one real cell: M6 right c = 0.10 -> `proven`, controls within `PAIR_BAND` of 12.213 | kernel, **child process** (`subprocess` + `os._exit`), about 35 s | `pytest tests/test_pair.py -k verify_cell` | Wave 0 |
| PAIR-03 | `prove` orchestration with an injected `common` (covered in-process) | unit | `pytest tests/test_pair.py -k prove` | Wave 0 |
| PAIR-03 | expected table re-derived from the jsonl by the (moved) rule equals the committed `tests/data/pair_expected.*`; bench still re-exports the rule | data | `pytest tests/test_pair.py -k expected tests/test_bench.py -k "cell_verdict or pair"` | Wave 0 |
| PAIR-04 | `screw pair nut` JSON and exit 0/1/2 via `subprocess`; parity flags generated from `NutParams` (positive rule, planted stray flag fails); no pair route in OpenAPI; info document has no verdict | CLI + API | `pytest tests/test_cli.py tests/test_parity.py tests/test_api.py -k pair` | Wave 0 |
| PAIR-04 | contract 9 kept; `import screw.app` leaves `screw.solid.pair` out of `sys.modules` (with a control that importing it puts it in) | contract + runtime probe | `make lint-imports`; `pytest tests/test_import_boundaries.py -k pair` | Wave 0 |
| PAIR-04 / SC3 | the full grid vs `tests/data/pair_expected.*`: 120 same-hand + 60 mixed cells at the recorded `(d, pitch, m, c, hand)`; diagnostics by definition | kernel, **slow tier** | `make pair SIZE=M6`; `pair.yml` | Wave 0 |
| PAIR-04 | `pair.yml` shape pins (no `pull_request`/`push`, `contents: read`, no `secrets.`, matrix = `maths.SIZES`, not in `ci.yml`/`required-jobs.txt`), marker registered and deselected, `-k 'M6-'` selects only M6 cells | unit | `pytest tests/test_pair.py -k "workflow or marker or selects"` | Wave 0 (copy `tests/test_grid.py`) |
| INFO-01 | nut rows (`s`, `e`, `m`, `mw`, `dw` from the row; `D1`, `D2`), pair rows (c radial/diametral, 0.5c normal, 2c/sqrt(3) axial, resulting diameters, `m/P`); every row traces to a field or a cited row; none from a mesh | unit | `pytest tests/test_calc.py -k "nut or pair_rows"` | Wave 0 |
| INFO-02 | limits group heading equals `limits for a bought part; this model is nominal and not toleranced`; rows only on an exact ISO 262 match; row labels carry sense, class, source | unit + data | `pytest tests/test_calc.py tests/test_tables.py -k limits` | Wave 0 |
| INFO-01/SC6 | M18 note `kernel pair proof inconclusive at K = 3 (2026-10-08-a-pair)` keyed on exactly `(18.0, 2.5)`, any hand/clearance, present with no kernel import | unit + `sys.modules` | `pytest tests/test_calc.py -k m18` | Wave 0 |
| FRNT-06 | `ControlSurfaceDeflection` True on the 5-arg constructor; measured deviation at the rule's preset <= rule x 0.05 mm over a stated size list and both hands; a coarse preset fails (control); STL and STEP from one cached solid | kernel | `pytest tests/test_solid.py -k "deflection or deviation"` | Wave 0 |
| FRNT-06 | `<slug>_preview.stl` vs `<slug>.stl` / `<slug>.step`; same function in `export` | API + CLI + parity | `pytest tests/test_api.py tests/test_cli.py -k filename` | Wave 0 |
| (cross-kind) | parity for the new kind: schema = model, query = model, flags = model (+ required `[required]` help), groups per kind, standing warning literal, `counterpart` key set | parity | `pytest tests/test_parity.py` | exists; must be updated first (Codebase Map) |

### Sampling Rate
- **Per task commit:** the one test file the task touches with `-n0 --no-cov`, plus `make lint-imports` when a module or import changes.
- **Per wave merge:** `make verify` (the pre-commit hook runs it anyway; budget about 45-60 s locally with the verify cell in the xdist pool).
- **Phase gate:** `make verify` green, then one `make pair SIZE=M6` and `make pair SIZE=M18` locally (the two sizes that bracket the claim), then the first `pair.yml` dispatch recorded in `bench/RESULTS.md` before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `tests/test_pair.py` (rule via `calc/pair.py`, `prove` with injected `common`, the child-process verify cell, expected-table re-derivation, workflow/marker pins) and `tests/test_calc_pair.py` or a section of `test_calc.py`
- [ ] `tests/data/pair_expected.*` + the deriving script (commit **before** the rule moves and before any pair-grid run; table in this document)
- [ ] `tests/data/owner/iso4032.tsv`, `iso724.tsv`, `iso965_2.tsv` and their `_SHAPE`/`shipped()` entries (blocked by the D-14 read)
- [ ] a `sample(kind)` test helper and updates to the nine existing test locations in the Codebase Map, in the same commit that registers `nut` (the registry commit breaks them all at once, like 04-04)
- [ ] `conftest`/helper for subprocess CLI runs with a timeout
- [ ] Framework install: none

### What cannot be proven without the kernel (and where it runs)
- `proven` itself, and everything about M18's control: only a real `BRepAlgoAPI_Common` can say; verify tier runs one cell, the grid tier runs 180; both are platform-dependent (A1, P4).
- That a cut part is watertight and meshes quickly (F8): `isValid()` and the volume gate pass a defective mesh.
- The deviation numbers (F2): a mesh property.
- That the oracle equals the kernel (F4): the oracle is kernel-free, its test is not; keep those tests in `tests/test_solid.py`, not in `test_thread_maths.py` (which must stay importable without the kernel, contract 2 does not bind tests but the file's purpose does).
- Left-hand correctness of the nut: the volume cannot see the hand (L12 used an `isInside` probe on the helix at z = 2.25 P for the rod); the nut needs its own probe (a point on the helix is inside the *void*, i.e. outside the nut material, for the hand asked and inside for the other).

## Security Domain

`security_enforcement` is enabled (absent = enabled; `.planning/config.json` has `security_enforcement: true`, `security_asvs_level: 1`).

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication / V3 Session | no | no accounts, no sessions |
| V4 Access Control | no (one control: no pair endpoint) | contract 9 keeps the expensive kernel proof off every route |
| V5 Input Validation | yes | pydantic v2 field bounds (`le=INTERIM_MAX_MM`, `allow_inf_nan=False`), after-validators naming fields, closed-set preset ids (`expand` is a dict lookup), `extra="forbid"`, repeated-key 422 dependency |
| V6 Cryptography | no | - |
| V12 Files / V14 Config | yes | `Content-Disposition` filename built from validated floats plus a constant `_preview` suffix; `pair.yml` with `permissions: contents: read`, no `pull_request`/`push`/`secrets.` (T-3-14) |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Resource exhaustion by an expensive build (huge `d`/`m`, many turns) | Denial of service | 250-turn cap on the void length `m + 2P` (P11), `INTERIM_MAX_MM`, admission queue and 30 s worker timeout (unchanged) |
| The pair proof reachable from a route (6 booleans, 16-137 s each cell) | Denial of service | not an endpoint; contract 9 plus the `sys.modules` probe (D-24) |
| Header injection via the download name | Tampering | slug contains only letters, digits, `_.+-` (`FastenerParams.slug` docstring, T-01-06); the new suffix is a constant |
| A forged `counterpart` or M18 note from user input | Spoofing | both computed server-side from validated fields and cited tables; the page renders text with `textContent` only (a parity test forbids `innerHTML`) |
| CI token abuse on the slow tier | Elevation of privilege | `grid.yml` posture copied and pinned by a test |
| A number from a coarse mesh presented as dimension | Information integrity (L02) | no panel number comes from a mesh (F2, D-21) |

## Sources

### Primary (HIGH confidence) - read or run this session
- `/Users/half/git/halfb00t/screw/.planning/phases/05-hex-nut-and-kernel-pair-proof/05-CONTEXT.md` (all decisions D-01 to D-24)
- Repo files read in full or in the cited ranges: `src/screw/params.py`, `calc/thread.py`, `calc/__init__.py`, `calc/presets.py`, `tables/rows.py`, `tables/presets.py`, `tables/iso262.py`, `tables/iso4017.py` (head), `solid/__init__.py`, `solid/bolt.py`, `solid/helical.py`, `app.py`, `cli.py`, `static/app.js`, `static/index.html`, `pool.py` (import lines), `bench/thread_spike/{pair,maths,verdict,worker,helical,measure}.py`, `tests/{test_grid,test_import_boundaries,test_parity,test_tables_second_entry}.py` and the registry tests named in the Codebase Map, `pyproject.toml`, `Makefile`, `.github/workflows/{ci,grid}.yml`, `required-jobs.txt`, `docs/architecture/{decision_log (L11-L13), overview}.md`, `bench/RESULTS.md` (grid tier, head fuse probe, ladder, trim, pair headings), `bench/results/thread-spike/2026-10-08-a-{pair,ladder}.jsonl`, `04-OWNER-READS.md`, `02-SPIKE.md`, the spike-protocol-amendments debt item, the preview-name idea, `.planning/{STATE,REQUIREMENTS,ROADMAP}.md`
- Installed packages: `.venv/lib/python3.12/site-packages/cadquery/occ_impl/shapes.py:484-515` (`exportStl`), OCP `IMeshTools_Parameters` / `BRepMesh_IncrementalMesh.Parameters()` / `dir(BRepAlgoAPI_Common)` queried in-process
- Probes (scratchpad, not committed): `mesh_params.py`, `mesh_ctor.py`, `dev.py`, `dev2.py`, `nut_probe.py`, `oracle.py`, `oracle2.py`, `ch.py`, `nutmesh.py`, `nutmesh2.py`, `fillet.py`, `boltfull.py`, `dilution.py`, `exit_code.py`, `exit_code2.py`, `mp_child.py`, `mp_child2.py`, `cell.py`, `derive.py`, `m18.py`, `m6.py`, `req.py`, `override.py`, `union.py`, `il.toml`; a full `pytest -n 8 --cov` run (2637 passed, 97.57 %)

### Secondary (MEDIUM confidence)
- Store listings for ISO 4753 (edition 2011): `https://connect.snv.ch/en/iso-4753-2011`, `https://webstore.ansi.org/standards/iso/iso47531999` - edition only; no dimension was read from them

### Tertiary (LOW confidence / not researched)
- Contents of ISO 4032:2023, ISO 724:2023, ISO 965-2:2024, ISO 4753: not read, not searched for values; every number from them is the owner's (D-14)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - nothing new; versions read from the venv
- Architecture / codebase map: HIGH - every file and symbol read; test breakages found by grep and line-checked
- Kernel behaviour (nut, oracles, ring, mesh, exit codes): HIGH on this host; MEDIUM across platforms (A1, A2, P4)
- Pitfalls: HIGH for P1, P2, P5-P9, P13 (measured or read); MEDIUM for P4, P10, P12 (consequences not run)
- Standards content: none researched (owner)

**Research date:** 2026-10-14
**Valid until:** 30 days for the codebase map (the tree changes with each plan); the kernel numbers are tied to cadquery 2.8.0 / cadquery-ocp 7.9.3.1.1 and are void after a kernel bump (L11: a bump is a re-measure event).

