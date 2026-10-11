# Phase 4: ISO Hex Bolts and Screws - Context

**Gathered:** 2026-10-11
**Status:** Ready for planning

<domain>
## Phase Boundary

The `bolt` kind grows a hex head and an explicit `thread_length`, so one registered model builds
both an ISO 4014 bolt (partial thread, plain shank) and an ISO 4017 screw (threaded to the head):
fields `d`, `pitch`, `left_hand`, `length`, `s`, `k`, `thread_length`, all absolute millimetres,
validated once at the params boundary. ISO 4014:2022, ISO 4017:2022 and ISO 262:2023 rows enter
`src/screw/tables/` as typed, cited, double-entered data with one pure-data test per row; a preset
("M6 × 20, ISO 4017") fills the mm fields on the page (three selects), the API (one catalogue
document) and the CLI (`--preset`, `screw presets`), and the part is always rebuilt from the mm
fields alone (import-linter contracts 6 and 7 land with the module). The info document gains
groups, a designation line, a preset-match status and notes; every number on it traces to a field
or to a cited row, and a value that cannot be computed honestly is a warning and no number. The
page stops rounding, shows the TABL-06 badge and the designation, and renders groups and notes
generically. The three front ends ship together and the parity test stays green.

Not in this phase: tip chamfer and under-head fillet (both to Phase 5, THRD-05, with ISO 4753);
the nut, `clearance`, the pair proof, `d2` and the 6g/6H limits (Phase 5); the printability
threshold (Phase 6); any measured runtime bound (Phase 7). The part stays an internal milestone:
version `0.0.x`, standing warning on every bolt info document (D-04).

Roadmap and requirement wording resolved by this discussion (planner: build to this, not to the
loose text):
- TYPE-01 and ROADMAP SC1 list "chamfered point, under-head fillet" for this phase while THRD-05
  owns the tip chamfer in Phase 5 and ISO 4753 is unread. Owner ruling D-02: neither ships here;
  TYPE-01 and SC1 are amended in this phase to say so, and ISO 4753 joins the purchase list for
  Phase 5. Both ends stay plain planar cuts (03 D-16).
- SC2 "import-linter forbids `params` and `calc.feasibility` from importing `tables`": screw has
  no `calc.feasibility`; `params` reaches `screw.calc.thread` by a lazy import. Contract 6 is
  therefore `screw.params` and `screw.calc.thread` (and anything `params` imports) → `screw.tables`
  forbidden, indirect disallowed; `derive` and the catalogue code may read `tables`. Contract 7
  keeps `screw.tables` a leaf.
- TABL-01 "the preset id is metadata": metadata of the live page session only, never a key in
  the link, the query or the model (D-09). TABL-06's `custom, based on …` therefore shows in the
  session after a pick; a reloaded link with edited fields reads `custom`.
- TABL-04 "the gate refuses an UNVERIFIED row in a release build": `make verify` refuses it in
  every build, so an UNVERIFIED row never reaches `main` (D-15).
- SC5 "the panel adds a one-line note" and the product grade: a `notes` list on the info
  document (D-20), not a warning and not a row.

</domain>

<decisions>
## Implementation Decisions

### Geometry this phase
- **D-01:** The head is a plain hex prism: across-flats `s`, height `k`, sharp corners at
  `s / cos 30°`. No top chamfer, no washer face: the 15–30° chamfer in the standards' figure is a
  band, not a number (L02). The closed form stays exact — `(√3/2)·s²·k` — so the THRD-04 gate
  holds unchanged, and the head meets the shank or thread at one planar fuse. The panel labels
  the geometric across-corners separately from the row's `e,min` (PITFALLS C7).
  — **Reversibility:** costly — a later chamfer changes the geometry every existing link means
  with no field change; acceptable while the standing warning says "not a product build",
  a superseding entry after release.
- **D-02:** No under-head fillet and no tip chamfer in this phase; both move to THRD-05
  (Phase 5) after ISO 4753 is bought and read. REQUIREMENTS.md TYPE-01 and ROADMAP.md Phase 4
  SC1 are amended in this phase to drop "chamfered point, under-head fillet"; THRD-05 gains
  "under-head fillet"; STATE.md's purchase line adds ISO 4753 for Phase 5. Reason: a fillet at
  `r,min` is a cited number but an OCCT fillet on a fused junction is the fragile operation C1/C10
  warn about, its volume would have to enter the closed form or the gate refuses every bolt, and
  nothing measured it; a chamfer without ISO 4753 is an invented end (L02, 03 D-16).
- **D-03:** An ISO 4014 bolt's unthreaded shank is a plain cylinder of diameter `d` (ISO 4014
  `ds` nom = `d`). The L11 thread is built over `min(thread_length, length)` only, from the tip,
  and ends in its plain planar cut, which is fused to the shank's end face (research
  Anti-Pattern 7: fuse at a planar face, never a cylinder over the thread). Closed form of the
  whole bolt: `section_area(d, P) · t + π(d/2)² · (length − t) + (√3/2) s² k` with
  `t = min(thread_length, length)`; a 4017 screw has `length − t = 0` and the thread meets the
  head's underside directly. The two fuses were not measured by Phase 2 (02 D-08 built no head):
  the planner runs a pre-plan probe (a few sizes, both standards, fine export) and records it in
  `bench/RESULTS.md` as a probe, not a bound, before the plan fixes any expectation.
- **D-04:** The standing warning (03 D-06) is rewritten, pinned verbatim:
  `plain-cut thread ends, no tip chamfer or under-head fillet; not a product build`. On every
  bolt info document, asserted on the API, the CLI and the parity test. Phase 5 rewrites it
  when the ends land; Phase 6 removes the "not a product build" clause at release.

### Fields and defaults
- **D-05:** `BoltParams` gains `s`, `k` and `thread_length` (floats, mm). Nothing else becomes a
  field: `e`, `dw`, `b` by band, `ls`, `lg` and the product grade are reported from the matching
  row or derived from the fields. A field that changes no geometry (e.g. `dw` ahead of a chamfer)
  is not added. Whether `s` later moves to `FastenerParams` for the nut is Phase 5's call; a
  move between base and subclass changes no link.
- **D-06:** Field names are the ISO symbols, like `d`: `s`, `k`, `thread_length`. The schema
  `title` carries the words (`Across flats`, `Head height`, `Thread length`) for the form and the
  flags are `--s`, `--k`, `--thread-length`.
- **D-07:** Frozen defaults for the new fields are the ISO 4017 M6 × 20 row's values, expected
  `s = 10.0`, `k = 4.0` (nominal), `thread_length = 20.0`, so the empty link opens a real screw
  and the badge reads `matches ISO 4017 M6 × 20` at startup. The numbers are committed only
  after the owner reads them from the purchased ISO 4017:2022 (and confirms the ISO 262:2023
  coarse pitch 1.0 for M6): an owner checkpoint opens the phase. This closes 01 D-05's
  `ASSUMPTION` with a row test asserting the default `(d, pitch, s, k, length, thread_length)`
  equals the row. — **Reversibility:** one-way — every shareable link that omits these fields
  depends on them forever (L02).
- **D-08:** `thread_length` is measured from the tip. If both `thread_length` and `length` are
  present in the request (`model_fields_set`: link, query or flags) and `thread_length > length`,
  it is a `422` naming both fields (a direct conflict between two explicit values). If
  `thread_length` is at its default and `length` is set below it, the thread is built to the full
  length and the info document warns, pinned:
  `thread_length 20 (default) exceeds length <L>: thread built to the full length`. `derive` and
  the builder use `t = min(thread_length, length)`; the stored field value is not rewritten. A
  link `#length=10` therefore opens a full-thread 10 mm screw with the warning, never a `422`.
  — **Reversibility:** costly — the meaning of every link that sets `length` below 20 without
  `thread_length` is a published contract from this phase on.

### Presets on the three front ends
- **D-09:** No preset id in the shareable link, the query or the model (research Anti-Pattern 2;
  UI-SPEC rule 10 unchanged). The badge is computed from the fields: `matches ISO 4017 M6 × 20`
  while every field a row defines equals that row (either standard); after a pick the page keeps
  the picked row in session state and shows `custom, based on ISO 4017 M6 × 20` once a field is
  edited; a reloaded link whose fields match no row reads `custom`. No nearest-row inference
  anywhere (a guessed basis is the plausible number L02 forbids).
- **D-10:** `GET /api/presets?kind=<kind>` returns one kernel-free catalogue document computed
  in the serving process from `tables`: every (standard, size, valid length) row with the mm
  fields it fills as `fields: {name: value}`, its id, its display string, its designation and its
  citation. Unknown kind: `404` like `/api/schema`. The model routes stay mm-only (`extra="forbid"`
  makes a `preset` query key a `422`). The page fetches it once per kind and builds the picker
  from it with no field-name literal. — **Reversibility:** costly — a published route shape.
- **D-11:** Preset id grammar: `<standard token>:<size>x<length>`, lowercase, no spaces, one id
  per catalogue row — `iso4017:M6x20`, `iso4014:M10x80`. The display string stays
  `ISO 4017 M6 × 20`. CLI: `--preset <id>` on `screw info <kind>` and `screw export <kind>`
  expands the row to field values before the model is built, explicit flags override; an unknown
  id exits 2 naming it; `screw presets <kind>` prints the catalogue (ids, mm fields, citations).
  `cli` may import `tables` (contract 7 forbids only the reverse). `tests/test_parity.py` learns
  that `--preset` is the one flag not generated from a field, by a positive rule, not by loosening
  the check.
- **D-12:** The page's picker is three selects above the form — `Standard` / `Size` / `Length` —
  built from the catalogue; lengths are filtered to the chosen size's standard series;
  second-choice sizes are shown in brackets as the standards print them. A pick writes every
  field the row defines (`d`, `pitch`, `length`, `s`, `k`, `thread_length`) and leaves `left_hand`
  alone; no confirmation dialog (the pick is the explicit action and the badge shows the state).
  `Reset` keeps its meaning: every field to its frozen default, which is ISO 4017 M6 × 20. The
  selects track the fields: they show the matching row, or a blank option while the fields match
  none. `01-UI-SPEC.md` is amended in the same plan (Copywriting, Interaction Contract, UI
  Considerations), per its extension rule 3.

### Table rows and the gate
- **D-13:** Precondition met (owner, 2026-10-11): purchased copies of ISO 4014:2022, ISO 4017:2022
  and ISO 262:2023 are in hand. Rows enter the repo verified from the first commit. The phase's
  opening owner checkpoint is the read of the ISO 4017 M6 × 20 row and the ISO 262 M6 pitch for
  D-07. ISO 4753 is added to the TABL-04 purchase list for Phase 5 (D-02). Tables in this phase:
  ISO 262:2023 (the 15 sizes M2–M20 with coarse pitch and first/second choice), ISO 4014:2022
  (head values by grade, `b` by length band, each size's standard length series) and
  ISO 4017:2022 (head values by grade, each size's standard length series up to 200 mm).
- **D-14:** Double entry. The owner types one copy of every row from the purchased PDFs; the
  agent transcribes a second copy independently from the same pages, supplied locally and read
  with the Read tool (never a web table, never the cq_warehouse CSVs as a source). A test in
  `make verify` diffs the two copies cell by cell; every disagreement is "go read the standard",
  never a majority vote. On top: one pure-data relation test per row (TABL-03; the invariants are
  the planner's, from PITFALLS C7: `e,min < s / cos 30`, `lg,max = l − b`, grade from `(d, l)`,
  `s,min ≤ s`, `k,min ≤ k ≤ k,max`, length series monotone). No kernel build per row (C11).
- **D-15:** UNVERIFIED never reaches `main`: `Source` carries a verification marker; a test in
  `make verify` fails on any UNVERIFIED row under `src/screw/tables/`, so one cannot pass the
  pre-commit hook, the CI job or `make pr.land`. No runtime filtering and no version check: every
  row the catalogue serves is verified by construction. The marker exists for a worktree in
  progress and as the gate's positive control (a test feeds an UNVERIFIED row and sees the
  refusal). The scan is scoped to `src/screw/tables/`; `bench/`'s UNVERIFIED labels on preview
  values are untouched.
- **D-16:** Licence stance, recorded in L13: the `tables` modules store the numeric values the
  product needs for M2–M20 with a required typed `Source(standard, edition, table, column)`
  per row (TABL-02); no clause wording, notes, figures or table layout is reproduced, and the
  catalogue serves the same numbers. The stance is written where the next contributor reads it
  (the `tables` package docstring and `docs/architecture/overview.md`).

### Info panel content and document shape
- **D-17:** `InfoRow` gains `group: str`; `PartInfo` gains `designation: str | None`,
  `preset: PresetMatch | None` (`status: exact | custom`, `id`, `display`) and `notes: list[str]`
  (D-20). `InfoRow.value` stays a float (03 D-07). The page renders one heading per distinct
  `group` in server order, like the form's fieldsets, reading no group name; shows `designation`
  as the panel's heading when present; composes TABL-06's copy from `preset.status` and
  `preset.display`. The same document is served by the API and printed by `screw info`; the
  parity test asserts it and that `app.js` reads no new key by a field or row name.
  — **Reversibility:** costly — the info document is a published shape every consumer reads.
- **D-18:** Rows present always (field-derived, group `Shank and thread` / `Head`): `d`, `pitch`,
  `length`, `thread_length`, shank length `length − t`, `turns` (of the built thread), closed-form
  `volume` of the whole bolt, thread depth and minor diameter (ISO 68-1:2023 basic profile),
  `s` (nominal), geometric across-corners `s / cos 30°`, `k`. Rows present only on an exact match
  of every field the row defines: the row's `s,min`, `e,min`, `dw,min`, `k,max`, `k,min`,
  `b` ref with `lg,max` and `ls,min` (4014), each labelled with its source and sense, e.g.
  `Across flats, min (ISO 4017:2022 Table 1)`. No match: those rows are absent and one warning
  is added, pinned: `no ISO 4014:2022 or ISO 4017:2022 row matches these fields; row values not
  reported`. A non-coarse pitch builds (03 D-04), reads `custom`, gets no row numbers: this
  closes STATE.md's open coarse-pitch question.
- **D-19:** The page shows `String(row.value)`: the API's number as sent, nothing rounds
  anywhere. UI-SPEC rule 23 becomes its stated target contract in the same plan;
  `docs/tech_debt/active/2026-10-06-ui-rounds-displayed-numbers.md` is resolved in the fixing
  commit (status, sha, `git mv`, INDEX row).
- **D-20:** INFO-05 and the product grade are `notes`, present only on an exact row match,
  rendered under the panel after the warnings in their own style and never hidden by an error
  (the rule-15 treatment warnings have). Texts pinned at planning in this shape:
  `wrench size 16 mm (ISO 4017:2022); the withdrawn DIN 933 used 17 mm` (M10, M12, M14 only;
  the DIN side is MEDIUM-confidence research, so the note names the DIN standard and the
  planner confirms the three values against two independent sources or drops the note) and
  `product grade A (ISO 4017:2022: l ≤ 150 mm and l ≤ 10 d)`.

### Caps with `thread_length`
- **D-21 (WR-02 ruling, owner 2026-10-11):** `FINE_STL_ROWS` is keyed by `(d, pitch, left_hand)`.
  Right-hand caps stay as today (M8 67.5, M10 56, M12 60, M14 58, M16 52, M18 65, M20 64 mm);
  left-hand caps are recomputed from `bench/results/thread-spike/2026-10-08-a-grid.jsonl` in the
  same commit — the debt item's reading is M10 73, M12 78, M14 79, M16 76, M18 92, M20 92 mm and
  no cap for M8 left (no measured stop); the planner re-derives them from the records and cites
  the run. The refusal text, the `app.py` comment and L12's "Caps" paragraph are reworded to what
  was measured: the fine STL plus its gzip copy exceeded the 64 MiB export budget.
  `docs/tech_debt/active/2026-10-11-fine-stl-cap-applies-right-hand-rows-to-left-hand-parts.md`
  is resolved in the fixing commit.
- **D-22:** Both caps read the built thread `t = min(thread_length, length)`: the 250-turn cap
  compares `t / pitch` as exact decimals; the fine-STL rows compare `t` against the rod caps. The
  head (an 8-face prism) and the shank (one cylinder) add bytes no run measured, bounded and
  small next to the thread's triangles; the cap comments say so and
  `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` gets a row; Phase 7 re-sweeps on
  the finished bolt (OPER-02, OPER-03). Refusal texts name `thread_length` where they named
  `length`, and the `turn_cap` 422 names `thread_length`, `length` and `pitch`.
- **D-23:** Bounds: `s`, `k`, `thread_length` are `gt=0`, `le=INTERIM_MAX_MM`, finite, like `d`
  and `length`. One new cross-field rule: `s <= d` is a `422` `head_too_small` naming `s` and
  `d` (a head whose flats sit inside the shank is a direct conflict between two explicit values,
  and a prism fused inside a cylinder would fail the gate with an unhelpful kernel message). No
  bound ties `k` or `s` to the tables (contract 6; a tall head is a valid custom part).

### Decision entry
- **D-24:** A new `L13` in `docs/architecture/decision_log.md` records this phase's choices that
  later phases build on: the geometry (D-01, D-03, ends deferred D-02), the fields and frozen
  defaults (D-05 to D-07), the `thread_length` rule (D-08), the preset plumbing (D-09 to D-12),
  the table rules (D-14 to D-16), the info document shape (D-17, D-20), the cap re-keying and
  input (D-21, D-22) and the `s > d` rule (D-23). It cites L11's run ids for every cap value and
  measures nothing new except the pre-plan fuse probe, which it cites as a probe.

### Claude's Discretion
- Where the head sits on the z axis (thread tip at `z = 0` and head above `length`, or head
  below 0): a viewer-only choice; the grid sits at the bounding box's `min.z`.
- The pre-plan fuse probe's scope (sizes, both standards, preview and fine export, RSS) and
  its `bench/RESULTS.md` entry; whether the probe reuses `bench/quiet.py` (a probe is labelled
  non-decisive either way).
- `left_hand` is not a row field, so it does not break the match; the designation of a
  left-hand part follows the designation clause of ISO 4014/4017 as read by the owner at the
  checkpoint (ISO convention is an `-LH` suffix); if the standard gives no left-hand form, the
  designation is withheld for left-hand parts rather than invented.
- Where 4014 rows with `l ≤ b` fill `thread_length = length` and so equal a 4017 row: the match
  reports the standard whose row the fields equal; when both match, 4017 is reported (the
  standard's own "ISO 4017 recommended" note), and the planner pins that in a test.
- How the standard length series (the stepped bold line) and the grade-B rows (`l > 150 mm`:
  M16 and M20 at 160–200) are encoded in the typed rows; the exact `Source` dataclass fields;
  the relation-test list beyond D-14's examples.
- Contract 6 wiring given `params → screw.calc.thread` and `screw.calc.__init__ → tables`: the
  researcher checks how import-linter/grimp treats the package `__init__` edge, and the
  table-reading code lands in a module `params` never reaches (e.g. `calc/presets.py` or
  `tables/presets.py` for `expand`, the match in `calc`), with `calc/__init__.py` kept table-free
  if that is what keeps `allow_indirect_imports = false` honest.
- Module layout: `src/screw/tables/{source,iso262,iso4014,iso4017,presets}.py` per
  ARCHITECTURE.md § Recommended Project Structure, adjusted to what the import graph needs;
  `solid/bolt.py` becomes the bolt assembly (head, shank, thread) over `helical.thread`.
- `screw presets <kind>` output format (one line per row vs JSON); the picker's DOM placement
  inside `aside`; the `notes` CSS class; the designation heading's element.
- The wording of the TYPE-01, THRD-05 and ROADMAP SC1 amendments (D-02) and of the STATE.md
  blocker lines this phase closes.
- The phase branch: `gsd/phase-04-iso-hex-bolts-and-screws`, cut from `main` at `57d05c6`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` § Phase 4 — goal, precondition, success criteria 1–5 (read with the
  five resolutions in `<domain>`); § Phase 5 for what is explicitly not here
- `.planning/REQUIREMENTS.md` — THRD-03, TYPE-01 (amended by D-02), TYPE-02, TABL-01…TABL-07,
  INFO-03, INFO-05 (this phase); THRD-05, TYPE-03, TYPE-04, INFO-01, INFO-02 (Phase 5 builds on
  the tables and the document shape); FRNT-01…05 (the parity the new fields and `--preset` must
  keep); § Out of Scope (fine pitch, property class, DIN tables)
- `.planning/PROJECT.md` § Key Decisions (ISO tables as presets, explicit mm as truth; every row
  cites and tests; `thread_length` serves both standards), § Context (spike before field)
- `.planning/STATE.md` § Blockers/Concerns — the TABL-04 purchase line (met, D-13), the ISO 4753
  line (Phase 5, D-02), the coarse-pitch question (closed by D-18)

### The locked inputs this phase builds on
- `docs/architecture/decision_log.md` — **L12** (the gate in `screw.solid`, the caps as
  refusals, `left_hand` on the base, the standing warning, `FINE_STL_ROWS`), **L11** (run ids:
  `2026-10-08-a-grid`, `-frontier`, `-verdict`), L02 (defaults frozen, cap-or-refuse never guess),
  L04 (no `Any`), L08 (`make pr.land`, required jobs), L09 (registry, routes, hash rule,
  `PartInfo`, INTERIM policy)
- `.planning/phases/03-real-helical-thread/03-CONTEXT.md` — D-04 (no coarse check in
  `params`), D-05/D-06 (info rows and the standing warning this phase rewrites), D-07 (float
  `InfoRow.value`, revisited by D-17), D-09 (`left_hand` on the base), D-16 (plain ends)
- `.planning/phases/01-runtime-port-and-walking-skeleton/01-CONTEXT.md` — D-05 (the frozen
  defaults and the `ASSUMPTION` D-07 closes), D-08 (route shape), D-10 (the parity test), D-15
  (`PartInfo`/`InfoRow`)
- `bench/results/thread-spike/2026-10-08-a-grid.jsonl` and `bench/RESULTS.md` § Thread spike —
  the records the left-hand caps are re-derived from (D-21)

### Research (the evidence behind the tables, presets and panel)
- `.planning/research/ARCHITECTURE.md` § Q2 (where tables live, `Source`, preset expansion,
  per-row verification), § Recommended Project Structure, § Import-linter contracts (6, 7),
  § Preset flow, Anti-Patterns 2, 6, 7
- `.planning/research/PITFALLS.md` C6 (editions, scope), C7 (nom/min/max/ref, grade, DIN
  contamination, the relation-test list), C10 (ends), C11 (no kernel build per row), M3 (preset
  overwrite), M4 (`thread_length` vs `length`), M5 (chamfer model), M6 (DIN names)
- `.planning/research/FEATURES.md` § Standards confirmed (editions, `b` bands, `e` two
  senses, DIN map, rows per standard), § Info panel and presets (panel groups, designation
  convention, preset UX), § Open questions Q3, Q5, § UNVERIFIED register
- `.planning/research/STACK.md` § 3 (no citable table library; the CSVs are a differential
  oracle only, never a source), § Standard editions, the spot values read from the previews

### The code that changes and the patterns it follows
- `src/screw/params.py` — `_f`, `_b`, `FastenerParams`, `BoltParams`, the `after` validators
  with lazy imports from `screw.calc.thread` (D-05 to D-08, D-23 extend)
- `src/screw/calc/__init__.py` — `InfoRow`, `PartInfo`, `_bolt`, `STANDING_WARNING`, `derive`,
  `download_refusal` (D-17 to D-20, D-04)
- `src/screw/calc/thread.py` — `turns_of`, `turn_cap_refusal`, `FINE_STL_ROWS`,
  `fine_stl_refusal`, `closed_volume` (D-21, D-22; the closed form grows by head and shank)
- `src/screw/solid/__init__.py` (`_build`, `check_solid`), `src/screw/solid/bolt.py` (`rod`
  becomes the bolt assembly), `src/screw/solid/helical.py` (`thread`, unchanged)
- `src/screw/app.py` — `schema()` (the 404 shape `/api/presets` copies), `_serve`,
  `download_refusal` call and its budget comment (D-21 rewording)
- `src/screw/cli.py` — `_add_args`, `_params`, `_Once`, `cmd_info`, `cmd_export` (D-11)
- `src/screw/static/app.js` — `buildForm` (fieldsets per group), `renderInfo`, `fmt` (D-19),
  `showMessages`, `navigate`/`refuseLink` (rule 10 unchanged), `partQuery`/`writeHash`
- `src/screw/static/index.html`, `style.css` — the `aside` the picker joins, `#dims`, `#messages`
- `tests/test_parity.py` — `_field_literals`, `_cli_flags`, `_expected_flags`, the pinned
  statements (the `--preset` positive rule, the new document keys)
- `tests/test_calc.py`, `tests/test_thread_maths.py`, `tests/test_params.py`, `tests/test_api.py`,
  `tests/test_cli.py`, `tests/test_solid.py` — the patterns new tests follow
- `pyproject.toml` `[tool.importlinter]` — contracts 2 and 8 to widen with `screw.tables`,
  contracts 6 and 7 to add
- `../spur` — house style only; spur has no presets or tables (checked 2026-10-11)

### UI contract and debt this phase amends or resolves
- `.planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md` — Copywriting Contract
  (badge copy, new strings), Interaction Contract rules 1, 10, 15, 19, 22–24, Extension rules
  2–3 (amended by D-12, D-17, D-19, D-20)
- `docs/tech_debt/active/2026-10-06-ui-rounds-displayed-numbers.md` (resolved by D-19)
- `docs/tech_debt/active/2026-10-11-fine-stl-cap-applies-right-hand-rows-to-left-hand-parts.md`
  (resolved by D-21)
- `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` (a row added by D-22)
- `docs/tech_debt/INDEX.md` — the row moves

### House rules
- `AGENTS.md` / `CLAUDE.md` (the gate, L02 rules, debt capture), `docs/CODING_VALUES.md`,
  `docs/HOW_TO_DEVELOP.md` (one PR per phase through `make pr.land`)
- `docs/architecture/overview.md` — module map to extend with `tables/` and the two contracts;
  the licence stance (D-16)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `params._f` / `_b`: field metadata that drives the form and the flags; `s`, `k`,
  `thread_length` are three `_f` calls. `model_validator(mode="after")` with a lazy import from
  `screw.calc.thread` is the pattern for `s > d` and the `thread_length` rule;
  `self.model_fields_set` is available inside it.
- `calc.derive` / `_bolt`: the row list, the `computed` table with the finite-or-warned rule, the
  `STANDING_WARNING` constant the parity test asserts; `download_refusal` is the one kernel-free
  rule `app._serve` and `cli export` share — the preset expansion follows the same "one function,
  two callers" shape.
- `calc.thread.turns_of` / `_exact`: exact-decimal turns for the cap on `t`; `FINE_STL_ROWS` is a
  plain dict keyed on floats — re-keying by hand is one tuple element.
- `solid.helical.thread(d, pitch, length, *, clearance, left_hand)`: the thread over `t`
  unchanged; `solid.check_solid` takes the closed form as a number, so the bolt's closed form is
  one new function in `calc.thread`.
- `app.schema()`: the handler-raised 404 with `loc: ["query", "kind"]` that `/api/presets` copies;
  `KindsReport`/`HealthReport` show the frozen response-model style.
- `cli._add_args`: generates flags from `model_fields`; `_params` builds the model from
  non-`None` namespace values — `--preset` expansion slots in before that dict is built.
- `app.js buildForm`: one `fieldset` per schema `group` in first-seen order — the same loop
  renders info groups; `renderInfo` is the one place `fmt` is applied; `showMessages(errors,
  warnings)` is where `notes` join; `read`/`write` keep checkbox handling generic.
- `tests/test_parity.py`: `_field_literals` (no field or row name in `app.js`), `_cli_flags`
  (every flag the help lists), `PINNED_STATEMENTS`; `tests/test_calc.py` asserts the info
  document row by row.
- `bench/results/thread-spike/2026-10-08-a-grid.jsonl`: per-row fine STL and gzip bytes by hand,
  the source for D-21.

### Established Patterns
- Validated once at the params boundary, trusted afterwards; a cross-field conflict is a
  `PydanticCustomError` whose message names both fields (`ctx.fields`), which the page marks
  `.invalid` and the CLI prints without a `loc`.
- Pure maths stays kernel-free and logger-free (contracts 2, 4); `tables` becomes a leaf
  (contract 7) and `params` never reaches it (contract 6).
- Every INTERIM constant carries `INTERIM` + source + "Phase 7 re-sweeps"; every measured cap
  cites its run id in the comment; a probe is recorded in `bench/RESULTS.md` as a probe.
- Pinned user-facing strings are asserted by tests and listed in the UI-SPEC Copywriting
  Contract; `app.js` reads nothing by a field or row name.
- Debt is retired in the fixing commit (status, sha, `git mv`, INDEX row); a deliberate cut is a
  new item with a severity and a trigger.
- A positive control for every gate: the UNVERIFIED scan (D-15), the double-entry diff (D-14)
  and the `--preset` parity rule (D-11) each get a test that feeds a bad input and sees the
  refusal.

### Integration Points
- `params.BoltParams` ← `s`, `k`, `thread_length`, the `head_too_small` and `thread_length`
  validators → `calc/thread.py` rules.
- `solid._build` → `solid/bolt.py` (head prism + shank + `helical.thread` over `t`, two planar
  fuses) → `check_solid` against the new whole-bolt closed form.
- `calc.derive._bolt` → groups, designation, preset match, notes, the no-row warning, the
  `thread_length` warning, the new standing warning; the match code reads `tables`.
- New `src/screw/tables/` package (sources, ISO 262, 4014, 4017 rows, presets `expand`) ←
  double-entry copies and relation tests in `tests/`; `pyproject.toml` contracts 6 and 7.
- `app.py` → `GET /api/presets?kind=`; `_serve` unchanged except the reworded refusal comment.
- `cli.py` → `--preset` on `info` and `export`, `screw presets <kind>`.
- `static/app.js`, `index.html`, `style.css` → picker selects, badge, designation heading,
  group headings, notes, `String(row.value)`.
- `tests/test_parity.py` → the `--preset` rule, the new document keys, the new pinned
  statements; `tests/test_calc.py` → the new rows and warnings.
- `docs/architecture/decision_log.md` → L13 (D-24) and the L12 "Caps" rewording (D-21);
  `docs/architecture/overview.md` → `tables` row, contracts 6 and 7, licence stance;
  `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md` amendments (D-02, D-13, D-18).
- gsd: `git.branching_strategy: phase`; branch `gsd/phase-04-iso-hex-bolts-and-screws` from
  `main` at `57d05c6`; one PR through `make pr.land`.

</code_context>

<specifics>
## Specific Ideas

- Standing warning, verbatim: `plain-cut thread ends, no tip chamfer or under-head fillet; not a
  product build`.
- `thread_length` default warning, verbatim shape: `thread_length 20 (default) exceeds length
  <L>: thread built to the full length`.
- No-row warning, verbatim: `no ISO 4014:2022 or ISO 4017:2022 row matches these fields; row
  values not reported`.
- Badge copy (TABL-06, unchanged): `matches ISO 4017 M6 × 20` / `custom, based on ISO 4017
  M6 × 20` / `custom`.
- Designation (TABL-07): `Hexagon head screw ISO 4017 - M6 x 20` and `Hexagon head bolt
  ISO 4014 - M10 x 80`, no property class; the left-hand form only as the standard spells it.
- Preset id: `iso4017:M6x20`; display: `ISO 4017 M6 × 20`; second-choice sizes in brackets in
  the picker and the catalogue display.
- Notes shape: `wrench size 16 mm (ISO 4017:2022); the withdrawn DIN 933 used 17 mm`;
  `product grade A (ISO 4017:2022: l ≤ 150 mm and l ≤ 10 d)`.
- Row labels carry source and sense: `Across flats, min (ISO 4017:2022 Table 1)`; the geometric
  across-corners is labelled `Across corners, geometric (s / cos 30°)` beside `Across corners,
  min (ISO …)`.
- Fine-STL refusal reworded to the measured quantity: the fine STL plus its gzip copy exceeded
  the 64 MiB export budget (run `2026-10-08-a-grid`), keyed by hand; the left-hand caps cite the
  same run.
- Expected defaults after the owner's read: `s = 10.0`, `k = 4.0`, `thread_length = 20.0`
  (ISO 4017:2022 M6; preview values, to be confirmed, never committed from the preview).
- The owner checkpoint that opens the phase: read ISO 4017:2022 M6 × 20 and ISO 262:2023 M6,
  confirm the defaults, then the double-entry transcription (owner's copy first).

</specifics>

<deferred>
## Deferred Ideas

- Chamfered head top (cone to `dw`, 15–30°) or a washer-faced grade-A head — after the plain
  prism ships and the two fuses are measured; needs a stated chamfer model (PITFALLS M5).
- Run-out fade at the thread/shank junction (C10, ISO `u ≤ 2P`) — a change to L11's measured
  construction; re-measure first.
- Tip chamfer and under-head fillet — Phase 5 THRD-05, after ISO 4753 is bought and read.
- `dw` as a field — only with a head chamfer that uses it.
- `preset=` as a metadata key in the hash — rejected (Anti-Pattern 2; a stale basis would ride
  in links).
- Nearest-row inference for the badge — rejected (a guessed basis, L02).
- A server-sent display string per row — rejected for now (`String(row.value)`); revisit only if
  the full-tail display proves unusable to users.
- Re-measuring the fine-STL bytes caps on the finished bolt — Phase 7 (OPER-02).
- ISO 4032 Annex A rows for M2–M4 nuts, `d2`, ISO 724, ISO 965-2 limits — Phase 5.
- DIN 933/931/934/912 aliases (TABL-08) — v2; the DIN wrench note (D-20) is the only DIN text in
  v1.
- Whether `s` moves to `FastenerParams` for the nut — Phase 5.

</deferred>

---

*Phase: 04-iso-hex-bolts-and-screws*
*Context gathered: 2026-10-11*
