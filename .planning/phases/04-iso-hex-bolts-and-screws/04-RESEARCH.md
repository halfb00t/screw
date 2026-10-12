# Phase 4: ISO Hex Bolts and Screws - Research

**Researched:** 2026-10-11
**Domain:** typed, cited ISO 4014/4017/262 table data; hex-head bolt solid over the L11 thread; preset plumbing on three front ends; a traceable info document
**Confidence:** MEDIUM-HIGH. HIGH on the codebase, the kernel recipe, the import graph and the FastAPI behaviour (all run or read this session). MEDIUM on table structure (read from the public iTeh previews, not the purchased copies). No table value in this file is entered data: TABL-04 and D-14 govern, and the owner's copy plus the agent's second copy are the only sources of rows.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Geometry this phase**
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

**Fields and defaults**
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

**Presets on the three front ends**
- **D-09:** No preset id in the shareable link, the query or the model (research Anti-Pattern 2;
  UI-SPEC rule 10 unchanged). The badge is computed from the fields: `matches ISO 4017 M6 × 20`
  while every field a row defines equals that row (either standard); after a pick the page keeps
  the picked row in session state and shows `custom, based on ISO 4017 M6 × 20` once a field is
  edited; a reloaded link whose fields match no row reads `custom`. No nearest-row inference
  anywhere (a guessed basis is the plausible number L02 forbids).
- **D-10:** `GET /api/presets?kind=<kind>` returns one kernel-free catalogue document computed
  in the serving process from `tables`: every (standard, size, valid length) row with the mm
  fields it fills as `fields: {name: value}`, its id, its display string, its designation and
  its citation. Unknown kind: `404` like `/api/schema`. The model routes stay mm-only
  (`extra="forbid"` makes a `preset` query key a `422`). The page fetches it once per kind and
  builds the picker from it with no field-name literal. — **Reversibility:** costly — a
  published route shape.
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

**Table rows and the gate**
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

**Info panel content and document shape**
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

**Caps with `thread_length`**
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

**Decision entry**
- **D-24:** A new `L13` in `docs/architecture/decision_log.md` records this phase's choices that
  later phases build on: the geometry (D-01, D-03, ends deferred D-02), the fields and frozen
  defaults (D-05 to D-07), the `thread_length` rule (D-08), the preset plumbing (D-09 to D-12),
  the table rules (D-14 to D-16), the info document shape (D-17, D-20), the cap re-keying and
  input (D-21, D-22) and the `s > d` rule (D-23). It cites L11's run ids for every cap value and
  measures nothing new except the pre-plan fuse probe, which it cites as a probe.

Roadmap and requirement wording resolved by the discussion (planner: build to this, not to the loose text):
- TYPE-01 and ROADMAP SC1 list "chamfered point, under-head fillet" for this phase while THRD-05 owns the tip chamfer in Phase 5 and ISO 4753 is unread. Owner ruling D-02: neither ships here; TYPE-01 and SC1 are amended in this phase to say so, and ISO 4753 joins the purchase list for Phase 5. Both ends stay plain planar cuts (03 D-16).
- SC2 "import-linter forbids `params` and `calc.feasibility` from importing `tables`": screw has no `calc.feasibility`; `params` reaches `screw.calc.thread` by a lazy import. Contract 6 is therefore `screw.params` and `screw.calc.thread` (and anything `params` imports) → `screw.tables` forbidden, indirect disallowed; `derive` and the catalogue code may read `tables`. Contract 7 keeps `screw.tables` a leaf.
- TABL-01 "the preset id is metadata": metadata of the live page session only, never a key in the link, the query or the model (D-09). TABL-06's `custom, based on …` therefore shows in the session after a pick; a reloaded link with edited fields reads `custom`.
- TABL-04 "the gate refuses an UNVERIFIED row in a release build": `make verify` refuses it in every build, so an UNVERIFIED row never reaches `main` (D-15).
- SC5 "the panel adds a one-line note" and the product grade: a `notes` list on the info document (D-20), not a warning and not a row.

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

### Deferred Ideas (OUT OF SCOPE)
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
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| THRD-03 | `thread_length` explicit mm; 4017 preset fills full length, 4014 fills `b` by band; editable | 4014 `b ref.` is 2d+6 (l ≤ 125), 2d+12 (125 < l ≤ 200) in every column read; only M14–M20 at l ≥ 130 use the second band (Planner Alert 1 for the 422/warn mechanism, Alert 6 for undefined cases) |
| TYPE-01 | ISO 4014 bolt (head values, `b` by band, `ls`/`lg`, grade A/B); ends and fillet amended out by D-02 | Table structure of 4014:2022 Tables 1-4 (columns, grade split, `ls,min`/`lg,max` per length cell); hex prism and fuse recipe verified (Code Examples 1-2) |
| TYPE-02 | ISO 4017 screw threaded to the head, lengths to 200 mm | 4017:2022 Tables 1-3 structure; length series rule (shortest = 2d to nearest standard length, ties up; greatest = min(10d, 200)); `length - t = 0` fuse verified |
| TABL-01 | Pick standard + size + length; preset fills mm fields; link carries mm only | Catalogue document and `expand`/`match` split (Architecture Patterns 3, 4); `/api/presets` shape; CLI `--preset` |
| TABL-02 | Typed `Source` per row; a row without one fails mypy | `Source` frozen dataclass with required fields; mypy-in-pytest positive control (Validation Architecture) |
| TABL-03 | One pure-data verification test per row | Parametrised relation tests, ~294 rows (estimate), relation list verified against preview numbers (Code Example 6) |
| TABL-04 | Rows only against purchased copies; UNVERIFIED refused | D-15 scan test + positive control; double-entry workflow; PDF rendering gap (Environment Availability) |
| TABL-05 | M2-M20 per ISO 262:2023, brackets for second choice, coarse only | 15 sizes and coarse pitches read from the 262:2023 preview; brackets confirmed in 4014/4017 headers |
| TABL-06 | Badge `matches` / `custom, based on` / `custom` | `PresetMatch` on `PartInfo`; page session state; exact float equality is safe (Pitfall 9) |
| TABL-07 | Designation without property class | Designation strings pinned in CONTEXT; the Clause 7 text is not in the preview, so left-hand form is the owner's read (Open Question 5) |
| INFO-03 | Every number traces to a field or a cited tested row; no honest value means warning and no number | `derive` finite-or-warned loop is reused; row-presence rule D-18; closed form for the whole bolt verified (Code Example 2) |
| INFO-05 | One-line note where ISO wrench size differs from withdrawn DIN | M10 16/17, M12 18/19, M14 21/22 confirmed from two independent web sources plus the 4017 preview (Sources); `notes` list |
</phase_requirements>

## Summary

The kernel side is the low-risk part. A plain hex prism, a plain cylinder and the L11 thread fuse into one valid solid at every size and both standards probed, the fused volume agrees with the whole-bolt closed form to 1.6e-6 or better (gate 9e-5), the STL is watertight at preview and fine, and `Shape.fuse` without `clean()` is sufficient (`clean()` changed nothing). The data side is mostly an entry-discipline problem: the 4014/4017:2022 tables are laid out with sizes as columns and the valid length range per size as a stepped bold line, so the length series is part of the data and cannot be a formula, although the standards' own footnotes give rules that make a strong cross-check test. About 294 catalogue rows (186 for 4017, 108 for 4014, an estimate from the rules plus the preview images) each need one cheap pure-data test.

Six things in the locked decisions do not work as written or have a consequence the discussion did not see. They are listed as **Planner Alerts** below, each with evidence. The most important: **D-08 cannot use `model_fields_set` on the API**, because FastAPI 0.142.2 copies every field default into the query model before validation, so every field of every API request is "set". The CLI sees the true set, so implementing D-08 as written would make `screw info` and `GET /api/bolt/info` disagree and would turn `#length=10` into a 422 on the model route. A provenance-free design that keeps D-08's observable behaviour is given. The second: **D-21's left-hand numbers are first over-budget lengths, not caps** (73 is itself measured over budget); the caps are 72, 77, 78, 75, 91, 91. The third: contract 6 as worded **passes vacuously** if `calc/__init__.py` imports `tables`, because grimp does not model the package `__init__` edge; wiring that keeps it honest is given and was verified.

**Primary recommendation:** Plan in this order: (1) owner checkpoint (M6 x 20, ISO 262 M6) and the PDF-page rendering route; (2) kernel-free maths in `calc/thread.py` plus the `tables` package with double entry and its gates, in commits that each leave `make verify` green; (3) one atomic change for `BoltParams` fields, validators, solid assembly, `derive` and every test the new default part breaks; (4) preset plumbing (catalogue, `expand`, `match`, API route, CLI); (5) UI; (6) docs, L13, debt resolution. Take Planner Alerts 1, 2, 3 and 6 to the owner before the plan fixes them.

## Planner Alerts (read before planning)

Each alert is a point where CONTEXT.md, REQUIREMENTS or a stated rationale conflicts with something run or read this session. CLAUDE.md "Stop and ask first" applies: evidence conflicts and acceptance criteria that cannot be met as written go to the owner, not into a quiet approximation.

**Alert 1 (blocker for the D-08 plan): `model_fields_set` is all fields on every API route.**
- Evidence [VERIFIED: runtime probe + `.venv/lib/python3.12/site-packages/fastapi/dependencies/utils.py:768-776`]: for `Annotated[BoltParams, Query()]`, `GET /x?length=10` yields `model_fields_set == {'d','left_hand','length','pitch'}`. The source reads `if field.field_info.is_required(): return  else: return deepcopy(field.default)` inside `_get_multidict_value`, so a missing key becomes an explicit default before pydantic sees it. On the CLI, `model(**values)` over non-`None` flags gives the true set (probe: `BoltParams(length=10.0).model_fields_set == {'length'}`).
- Second path [VERIFIED: `src/screw/app.py:249-256`]: `strip()` rebuilds the model route's params as `cls(**q.model_dump(include=set(cls.model_fields)))`, so even with a correct query model the model route would see every field as set. A validator that raises when `thread_length` and `length` are "both set" would 422 `model.stl?length=10` while `/info?length=10` answers 200, and `#length=10` (D-08's own example) would fail on the second request.
- Equality and hash ignore `model_fields_set` [VERIFIED: probe `BoltParams(length=10.0) == BoltParams(length=10.0, d=6.0)` is True, equal hashes], so caches are unaffected whichever design is chosen.
- **Recommended design (keeps D-08's observable behaviour, no framework dependence):**
  1. One pure function in `calc/thread.py`: `thread_length_conflict(length, thread_length) -> str | None` returning the 422 text when `thread_length > length`, naming both fields. "One function, two callers", the shape of `download_refusal`.
  2. API: an app-level dependency next to `refuse_repeated_keys` (`app.py:173-198`, which already reads `request.query_params`): when both keys are present and both parse as floats, call the function and raise `HTTPException(422, detail=[{"loc": ["query"], "type": "thread_length_conflict", "msg": ..., "ctx": {"fields": ["thread_length", "length"]}}])`. Unparseable values are left to the model's own 422. `ctx.fields` is what `problems()` in `app.js` uses to mark both controls invalid.
  3. CLI: the same function in `_params` after `--preset` expansion, on the merged values, exit 2.
  4. The model carries no `model_fields_set` logic. `derive` warns whenever `thread_length > length`: with the pinned text when `thread_length` equals the field default, and with a second text (Alert 6) otherwise.
  5. Consequence to accept or rule on: `BoltParams(length=10, thread_length=30)` constructed directly in Python is accepted (build and info use `t = min(...)`, the warning explains). The page never sends a default-valued field (`partQuery()` omits values equal to defaults), so a typed `thread_length=20` with `length=10` is a warning on the page, not a 422; any other explicit `thread_length` above `length` is a 422.
- Alternatives and why not: dropping the 422 entirely (never refuse, always warn) is simplest and keeps parity, but contradicts L02's "direct conflict between two explicit values is a 422" and D-08 itself. Rebuilding the query model from raw `request.query_params` in every route would restore a true `model_fields_set` but changes the OpenAPI contract that `tests/test_api.py::test_openapi_documents_the_typed_contracts` pins. Ask the owner to confirm the recommended design as the amended D-08 mechanism.

**Alert 2: D-21's left-hand numbers are first over-budget lengths.**
- Evidence [VERIFIED: recomputed from `bench/results/thread-spike/2026-10-08-a-grid.jsonl`, 3580 built rod rows, criterion `fine bytes + gzip1_bytes > 67108864` as in the code comment at `src/screw/calc/thread.py:170-181` ("each cap is the largest length below the first grid row whose fine raw STL plus gzip level 1 exceeded the INTERIM 64 MiB export budget")]: first over-budget grid length per `(d, pitch, left_hand)` and the largest measured fitting length below it:

| d, pitch | right-hand: first over / cap | left-hand: first over / cap |
|---|---|---|
| 8, 1.25 | 68 / 67.5 | none over up to 80 / no cap |
| 10, 1.5 | 57 / 56 | 73 / 72 |
| 12, 1.75 | 61 / 60 | 78 / 77 |
| 14, 2 | 59 / 58 | 79 / 78 |
| 16, 2 | 53 / 52 | 76 / 75 |
| 18, 2.5 | 66 / 65 | 92 / 91 |
| 20, 2.5 | 65 / 64 | 92 / 91 |

- The debt item's "M10 73, M12 78, M14 79, M16 76, M18 92, M20 92" are the *first over* column. Entered as caps they would accept a length the run measured over budget (the code's convention is "largest measured length that fits", e.g. 67.5 for M8 where 68 is the first row over). Use the right-hand column of caps in the table (they reproduce today's `FINE_STL_ROWS`, which is the control) and the left-hand cap column. At the first over-budget row the raw fine STL alone is under 64 MiB for every row (so the refusal text must say "the fine STL plus its gzip copy"). No row above the first over-budget row fits again.
- Both key and grid-row floats are exact (`8.0`, `1.25` ...), so `FINE_STL_ROWS.get((d, pitch, left_hand))` hits for preset-filled parts.

**Alert 3: contract 6 is blind to the package `__init__` edge.**
- Evidence [VERIFIED: grimp 3.17 / import-linter 2.15 experiment on a scratch copy of `src/screw` with `screw.calc.__init__` importing `screw.tables`]: a contract with `source_modules = ["screw.params", "screw.calc.thread"]`, `forbidden_modules = ["screw.tables"]` is **KEPT** although `import screw.calc.thread` executes `screw/calc/__init__.py`, which imports `tables`. With `screw.calc` itself as a source the same contract is BROKEN and names `screw.calc -> screw.tables (l.18)` and `screw.calc.presets -> screw.tables (l.1)`. A function-level import inside `_bolt` is also seen (`screw.calc -> screw.tables (l.49)`), so lazy imports do not hide an edge from grimp. Runtime check on the lazy variant: `BoltParams()` leaves `'screw.tables' in sys.modules` False; after `derive(BoltParams())` it is True.
- Consequence: SC2's "opening the URL rebuilds the same part without consulting a table" is only provable if `calc/__init__.py` does not import `tables` at import time. Recommended wiring:
  - `screw/calc/__init__.py` imports no table module at top level. `_bolt` imports `screw.calc.presets` (or whichever module reads `tables`) inside the function, the reverse of the existing `params` pattern but for the contract's reason.
  - Contract 6: sources `screw.params`, `screw.calc.thread`; forbidden `screw.tables`; default indirect checking (note the repo's existing contracts use `allow_indirect_imports = true` to *allow*; leave the key out).
  - A subprocess test is the positive control for the property import-linter cannot see: `python -I -c "import sys; from screw.params import BoltParams; BoltParams(); assert 'screw.tables' not in sys.modules"`, plus the converse (`derive` loads it) so the test cannot pass vacuously.
  - Contract 7: `screw.tables` forbidden to import `screw.params`, `screw.calc`, `screw.solid`, `screw.app`, `screw.cli`, `cadquery`, `OCP`, `fastapi`, `logging`; KEPT in the experiment.
  - Widen contract 2's `source_modules` with `screw.tables` (kernel-free). Contract 8 already covers `screw` as a whole.

**Alert 4: D-23's stated reason is not what the kernel does, and its cost is visible.**
- Evidence [VERIFIED: probe, scratch `probe_s.py`]: with `s` below `d` the head and shank still fuse into one valid solid inside the gate: `s=5, d=6` (hex corners 5.77 < d), `s=5.3`, `s=3` all `solids=1 valid=True`, relative volume error under 1.4e-7. `s == d` builds too. The head stacks on top of the shank (z in `[length, length+k]`), it does not overlap it, so "a prism fused inside a cylinder would fail the gate with an unhelpful kernel message" does not happen. The rule is a product policy (a head no wider than the shank is not a hex head), not a kernel necessity. L13 should say that.
- Cost: the frozen default `s = 10.0` makes any hand edit of `d` to 10 or more a 422 `head_too_small` until `s` is also set (`d=10` already trips `s <= d`). A picked preset sets `s`; a custom change does not. The error message should therefore be actionable: it names `s` and `d` and says `s` must be above `d`. Ask the owner whether to keep 422 (recommended: it is locked, consistent with L02, and a preset avoids it) or build-and-warn (also L02-clean, and the probe shows it is safe).
- Ripple [VERIFIED: `bench/corpus.py:25`, `tests/test_bench.py:147-151`]: the Phase 1 corpus is `{"d": d, "length": length}` for `d in (2.0, 6.0, 20.0, 100.0)`; `test_every_corpus_entry_is_a_valid_bolt` validates each. With D-23 the d=20 and d=100 entries become 422. With D-07's `thread_length = 20.0` and D-22 the d=100 length=200 entry (WR-05, 200 turns) builds only a 20 mm thread. The corpus must pin `s`, `k` and `thread_length` per entry (a fixed meaning matters: Phase 7 "keeps that one fixed from then on"), and `docs/tech_debt/active/2026-10-11-default-pitch-d100-length200-exceeds-both-interim-backstops.md` needs a note that its repro URL now needs `thread_length=200`.

**Alert 5: whole-bolt volume gating dilutes the thread check.**
- Evidence [VERIFIED: computed with `screw.calc.thread.section_area`]: the thread's share of the whole-bolt closed volume is 0.19 (M12 x 120, ISO 4014), 0.20 (M20 x 200 with b = 52), 0.21 (M6 x 60), 0.38 to 0.53 for short 4017 rows. At 19 percent a thread volume error of 4.7e-4 passes `T_GATE = 9e-05` (`src/screw/calc/thread.py:22`, `T_GATE = 9e-05`) on the whole bolt. L11's largest rod error is 8.1e-6 over 3580 rows (verified from the same JSONL), so real builds have margin, but the gate's detection power on the thread alone drops about five-fold in the worst case. L11's known-bad controls differ by percent, so they are still caught.
- Recommendation (tightening only, so no superseding entry): in `_build`, also run `check_solid(thread_solid, closed_volume(d, pitch, t))` on the bare thread before the fuse, in addition to D-03's whole-bolt check. Cost: one more precise volume of the thread, 0.44 s at M20 x 200 and at most 0.82 s over the grid (`volume_s`, `2026-10-08-a-grid`, a loaded single run). The whole-bolt check then mainly proves the fuse (solid count 2 for a failed fuse is refused by the first line of `check_solid`). Put the decision with the planner; mention it in L13.

**Alert 6: cases D-08 does not define, and a sliver the builder cannot take.**
- `thread_length` explicit and above a *default* `length`: `tests/test_parity.py::test_the_cli_and_the_api_print_the_same_document` moves every float field to `default * 1.5`, which includes `thread_length = 30` against `length = 20`. D-08's 422 needs both explicit; the pinned warning says "(default)" for `thread_length`. No text exists for this case. Recommended (ASSUMED, needs a pin): build to the full length and warn `thread_length 30 exceeds length 20: thread built to the full length`, chosen by value (the field default is the only thing the text can test); L02 allows capping a dimension when no explicit choice is contradicted.
- A shank of positive but tiny length [VERIFIED: probe `probe_edge.py`]: `length - t` of 1e-3 and 1e-6 mm builds and passes the gate; 1e-9 and 1e-12 raise `Standard_Failure: BRepSweep_Translation::Constructor`, which `_build_checked` rewords as `"check d, pitch and length."` (`src/screw/solid/__init__.py:134`). `thread_length = 19.999999999` is a valid-looking request. Mirror the builder's own rule for the thread tail (`MIN_TAIL_MM = 1e-3`, `src/screw/solid/helical.py`): fold a shank shorter than `MIN_TAIL_MM` into the thread (same `t` in the builder, the closed form, the caps and `derive`), or refuse it with a message naming `thread_length` and `length`. The same hole exists below `MIN_TAIL_MM` for `thread_length` itself (`BuildError: length 0.0005 mm is too short`, which says `length` for a `thread_length` request); the open debt item `2026-10-11-info-document-prints-numbers-for-a-length-the-builder-refuses.md` says "revisit when the info document next changes", which is this phase.
- The generic kernel-failure text should name `thread_length`, `s` and `k` too.

**Alert 7: the catalogue makes a third of the 4017 presets download-refused at fine quality.**
- Evidence [computed: series rule plus `FINE_STL_ROWS` right-hand caps]: of about 186 ISO 4017 rows, 62 have `t = length` above the right-hand fine-STL cap: M8 x 70, 80; M10 x 60 to 100; M12 x 65 to 120; M14 x 60 to 140; M16 x 55 to 160; M18 x 70 to 180; M20 x 65 to 200. ISO 4014 rows (`t = b <= 52`) are never over a cap. The page's `Download STL` link asks for the fine default, so for these presets the preview and STEP work and the fine STL is a 422 with the existing warning. This is D-21/D-22 working as decided, but it is what a user will see on the most common long screws. Record the count in L13 and the interim-bounds debt row, and add a test that pins the count so Phase 7's re-sweep shows the change.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Cited table rows, `Source`, series, `expand`/`match` over plain mappings | `screw.tables` (leaf, stdlib only) | none | Contract 7; pure data, importable by `cli` and `app` without the kernel |
| Field validation (bounds, `s > d`, turn cap on `t`) | `screw.params` (model boundary) | `screw.calc.thread` pure rules | Validated once at the boundary; rules live in the kernel-free module `params` already imports lazily |
| Explicit-conflict 422 for `thread_length` > `length` | API dependency and CLI `_params` | `calc.thread` pure function | Provenance exists only at the front door (Alert 1) |
| Closed forms (bolt volume, hex volume, built thread length) | `screw.calc.thread` | none | Oracle shared by the gate, the info rows and the caps; no kernel |
| Head + shank + thread assembly and the gate | `screw.solid` | none | Only doorway to `cadquery`/`OCP` (contract 8); `check_solid` stays inside the cache wrapper |
| Info document (groups, designation, preset match, notes, warnings) | `screw.calc` (`derive`) | `screw.tables` read lazily | Kernel-free per keystroke; reads tables only on a match attempt |
| Catalogue document (`/api/presets`, `screw presets`) | `screw.calc.presets` (builds pydantic doc) | `screw.tables` data | `cli` must not import the app (contract 3), so the builder cannot live in `app` |
| Picker, badge, group headings, notes, `String(row.value)` | Browser (`app.js`) | API documents | Page reads everything from `/api/schema`, `/api/presets`, info; no field or row literal (rule 29) |
| Cap on built thread (250 turns, fine STL) | `screw.calc.thread` | API/CLI refusal call sites | Existing "one function, two callers" shape |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| cadquery | 2.8.0 | hex prism, cylinder, `Shape.fuse` | Locked L01; installed [VERIFIED: `.venv`, `cadquery.__version__`] |
| cadquery-ocp | 7.9.3.1.1 | kernel, `BRepGProp` volume | Locked L01/L11 [VERIFIED: `importlib.metadata`] |
| pydantic | 2.13.5 | `BoltParams` fields, `PartInfo`, catalogue document | Locked L01 [VERIFIED: `.venv`] |
| fastapi | 0.142.2 | `/api/presets`, the conflict dependency | Locked L01 [VERIFIED: `.venv`] |
| import-linter / grimp | 2.15 / 3.17 | contracts 6 and 7 | Locked (L10) [VERIFIED: `.venv`] |
| pytest / pytest-xdist | 9.1.1 / 3.8.0 | per-row parametrised tests | Locked [VERIFIED: `.venv`] |
| mypy | 2.4.0 | `--strict`, `Source` typing | Locked [VERIFIED: `.venv`] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| stdlib `dataclasses`, `typing.Literal`, `fractions`, `math` | 3.12 | typed rows, exact-decimal caps | `tables` is stdlib only so it stays a leaf |
| `mypy.api` (inside pytest) | 2.4.0 | negative test: a row without `Source` fails mypy | One test, SC4's "fails mypy" positive control |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Typed Python rows | JSON/CSV per standard | Loses mypy-checked `Source`; adds file I/O (ARCHITECTURE Q2 already decided) |
| cq_warehouse / bd_warehouse CSVs | none | Verified wrong or inconsistent in STACK § 3; differential oracle only, never a source (D-14) |
| `Workplane.union(clean=...)` | `Shape.fuse` | `Shape.fuse` has no `clean` keyword [VERIFIED: signature `(self, *toFuse, glue=False, tol=None)`]; `.clean()` changed no result in the probe, so skip it |

**Installation:** none. No package is added this phase (`pyproject.toml` and `requirements.txt` stay as they are).

**Version verification:** versions above were read from the project `.venv` this session, not from a registry, because the phase installs nothing.

## Package Legitimacy Audit

No external package is added, removed or upgraded in this phase, so the `package-legitimacy check` seam was not run: there is nothing to check.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| (none) | - | - | - | - | - | - |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
 owner PDF copy ──typed once──► tables/iso4017.py ─┐
 agent copy (from page images)─► tests/data/...  ──┤ cell-by-cell diff test (make verify)
                                  tables/iso4014.py ┤ relation tests per row (parametrised)
                                  tables/iso262.py ─┘ UNVERIFIED scan + positive control
                                        │  (leaf: stdlib only; contract 7)
        ┌───────────────────────────────┴──────────────────────────────┐
        ▼                                                              ▼
 calc/presets.py  (lazy-imported by derive; imported by app, cli)   cli: --preset expand
   catalogue(kind)  ── GET /api/presets?kind=  (404 unknown kind)    (explicit flags win)
   match(fields)    ──► PresetMatch(exact|custom, id, display)             │
        │                                                                  │
 browser (app.js)                                                          │
   picks Standard/Size/Length ──► writes mm fields into the form           │
   form → hash (defaults omitted) → /api/bolt/info?mm fields               │
                                   /api/bolt/model.stl?mm fields           │
                                          │                                │
              dependency: thread_length_conflict (both keys present?)  ◄───┘ same pure rule
                                          │
                       BoltParams (validated once: bounds, s > d, turn cap on t)
                           │                                   │
                  calc.derive ──► PartInfo                solid._build
                  groups, designation,                       t = min(thread_length, length)
                  preset, notes, warnings                    thread (helical.thread, z 0..t)
                  closed form of whole bolt ◄── oracle ──►   shank (cylinder, t..length)
                                                             head (hex prism, length..length+k)
                                                             fuse ×2 ──► check_solid (1 solid,
                                                             valid, volume vs closed form)
                                                             cache ──► STL / STEP bytes
```

### Recommended Project Structure
```
src/screw/
├── tables/                  # data only; a leaf (contract 7); docstring carries the D-16 licence stance
│   ├── __init__.py          # package docstring only: no imports of its modules
│   ├── source.py            # Source(standard, edition, table, column, status); required, no defaults
│   ├── iso262.py            # 15 sizes, coarse pitch, choice 1 or 2
│   ├── iso4014.py           # per size and grade: head values, b by band; per length: ls,min / lg,max
│   ├── iso4017.py           # per size and grade: head values; length series
│   └── presets.py           # expand(id) -> {field: float}; match(fields) -> row | None; catalogue(kind); plain dataclasses
├── calc/
│   ├── __init__.py          # InfoRow(+group), PartInfo(+designation, preset, notes), derive; NO table import at import time
│   ├── thread.py            # + built_thread_length, hex/bolt closed forms, head_too_small rule, thread_length_conflict, re-keyed FINE_STL_ROWS
│   └── presets.py           # builds the pydantic catalogue document and the match for derive; imports tables
└── solid/bolt.py            # head, shank, thread assembly (was `rod`)
tests/
├── test_tables.py           # per-row relations, UNVERIFIED gate, Source typing, series rule, cross-standard checks
├── test_tables_second_entry.py   # the double-entry diff
└── data/                    # the second copy (agent transcription), per-size records, not the printed layout
```

### Pattern 1: Hex head, shank and thread assembly
**What:** three solids stacked along +Z and fused with `Shape.fuse`, thread tip at `z = 0`.
**When to use:** the bolt builder in `solid/bolt.py`; the only place a `cadquery` object exists.
**Example:** see Code Examples 1 and 2. Verified at M2 x 4, M6 x 20, M6 x 30, M10 x 80, M16 x 160, M20 x 200 and left-hand M6 x 30.

### Pattern 2: Built thread length is one function
`built_thread_length(thread_length, length) = min(thread_length, length)` in `calc/thread.py`, called by the builder, the closed form, `derive`, both caps and the turn-cap validator. D-08 says the stored field is never rewritten, so every consumer derives `t`, and a test asserts no consumer recomputes it inline.

### Pattern 3: Tables hand out plain data, `calc.presets` builds documents
`tables.presets` returns frozen dataclasses (`PresetRow`: id, standard, size label, length, fields as a tuple of `(name, float)`, citation string). `calc/presets.py` turns them into the pydantic `PresetCatalogue`/`PresetMatch`. This keeps `tables` free of pydantic and `cli` free of `app`. Field names (`d`, `pitch`, `length`, `s`, `k`, `thread_length`) are string keys in `tables.presets`; a test asserts every key is a `BoltParams` field so a rename cannot drift silently.

### Pattern 4: Match is exact float equality over the fields a row defines
`left_hand` is not a row field and is ignored. Both standards can match; report 4017 first (CONTEXT discretion), pinned by a test. No tolerance: URL values and table values are both literals parsed from decimal text, so `10.0 == 10.0`; a test round-trips every catalogue row through `BoltParams(**fields)` and `derive` and asserts an exact match with that row's id (or the 4017 id where both match).

### Pattern 5: Catalogue document drives the picker without field names
Recommended (discretion): the document publishes its own axes so `app.js` holds no `length` literal that `_field_literals` would flag: `axes: ["Standard", "Size", "Length"]` and, per row, `choice: [standard, size, length]` as display strings, plus `fields` and `id`. The page builds three selects from `axes` and filters by `choice` prefixes; a pick writes `fields` through the existing `write()` helper keyed by whatever names arrive.

### Anti-Patterns to Avoid
- **`model_fields_set` for any rule** on the API path (Alert 1).
- **Importing a table module from `calc/__init__.py` at top level** (Alert 3).
- **A formula for the 4014 length series below M5** (no rule in the standard text read; the series is data): M2 16 and 20, M2.5 16 to 25, M3 20 to 30, (M3.5) 20 to 35, M4 25 to 40 as read from the 4014 preview Table 1 (confirm on the purchased copy).
- **Storing the standard's printed layout** (D-16): both entry copies are per-size records, not symbol-rows by size-columns.
- **A kernel build per row** (C11).
- **Reading `info.preset` fields by field name in `app.js`**: the badge composes from `preset.status` and `preset.display` only.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Preset-id parsing and the catalogue | A second parser in the CLI and the page | One `tables.presets.expand`/`catalogue`, called by `cli` and `calc.presets` | Parity (FRNT-05) and one place for the id grammar (D-11) |
| Turn and fine-STL caps on `t` | New cap code | `turn_cap_refusal`, `fine_stl_refusal` with `t` and `left_hand` added | Exact-decimal handling already solved (`turns_of`, `_exact`) |
| Explicit-conflict rule | Per-front-end copies | `thread_length_conflict` in `calc/thread.py` | Same text and `ctx.fields` on API and CLI |
| Finite-or-warned info rows | A new loop | The `computed` table in `_bolt` (`src/screw/calc/__init__.py:48-86`) extended | Already enforces "no number if not finite, warn instead" |
| Per-row verification | Hand-written test per row | `pytest.mark.parametrize` over the table, `ids=row.id` | A row cannot be added without its test |
| Mesh closedness check | A new walker | `bench/` already has watertight checks; the probe used a 10-line edge-count walk | Only a fixture-level check is needed, not a runtime one |
| PDF to image | A new tool | PDFKit via a throwaway Swift script, or `brew install poppler` | See Environment Availability |

**Key insight:** every new rule here already has a "one pure function, called by every front end" precedent (`download_refusal`, `root_radius_refusal`, `turn_cap_refusal`); follow it and parity comes for free.

## Common Pitfalls

### Pitfall 1: `polygon(6, d)` is across-corners by default
**What goes wrong:** `Workplane.polygon(nSides, diameter, forConstruction=False, circumscribed=False)` inscribes the polygon in a circle of `diameter` (vertices on the circle), so `polygon(6, 10)` has across-corners 10 and volume 259.8, not the across-flats 10 and 346.4 the closed form `(√3/2)s²k` expects.
**Why it happens:** the keyword name is `circumscribed`, and the default reads naturally as "diameter of the hexagon".
**How to avoid:** use `polygon(6, s, circumscribed=True)` [VERIFIED: probe, bbox 10.0 x 11.547, volume 346.4102 for s=10, k=4] or `polygon(6, s / cos(pi/6))`. Add a test that the head's bounding box in the flat direction equals `s`.
**Warning signs:** the gate refuses every bolt with a volume ratio of 0.75.

### Pitfall 2: `Shape.fuse` has no `clean=`
**What goes wrong:** `TypeError: Shape.fuse() got an unexpected keyword argument 'clean'` (hit in the probe). `Workplane.union` has `clean`; `Shape.fuse(*toFuse, glue=False, tol=None)` does not.
**How to avoid:** fuse `Shape`s and call `.clean()` only if a measurement shows a need; here it changed nothing (same volume, same face handling) so leave it out.

### Pitfall 3: The default part changes for every Phase 3 link
**What goes wrong:** a pre-Phase-4 link `#d=8&length=30` meant an 8 mm threaded rod; it now means a screw with a head, thread 20 mm and shank 10 mm. D-01 and D-08 record this as costly and the part is an internal milestone, so it is accepted; say so in L13.
**Ripple list (every test or file the default part, the new fields or the new warning touches):** `tests/test_params.py` (defaults, schema property list `["d","pitch","left_hand","length"]`, group assertion, slug `bolt_d6_pitch1_left_hand0_length20`, turn-cap tests that need `thread_length`), `tests/test_api.py` (OpenAPI field sets, default info keys, logged slug), `tests/test_calc.py` (`WARNING`, `KEYS`, units), `tests/test_parity.py` (`groups == ["Size", "Thread"]`, the flag-list assertions, the `cases` loop, the pinned warning), `tests/test_solid.py` (default bbox 6 x 6 x 20 becomes about 11.547 x 10 x 24, volume), `tests/test_thread_maths.py` (`L11_ROWS == FINE_STL_ROWS`, `fine_stl_refusal` signature), `tests/test_bench.py` and `bench/corpus.py` (Alert 4), `tests/test_cli.py` (warning string, README example test), `README.md` status paragraph, `docs/architecture/overview.md`.
**README example test:** `tests/test_cli.py::test_readme_cli_examples_run` runs every `.venv/bin/screw ...` line in `README.md` and asserts `json.loads(...)["kind"] == "bolt"` for non-export lines; a `screw presets` example line would break it unless the test is adjusted.

### Pitfall 4: Every commit runs `make verify`
**What goes wrong:** the pre-commit hook runs the whole gate (`.pre-commit-config.yaml`, `make verify`), so a commit that adds the double-entry diff before both copies exist, or the UNVERIFIED scan with a row marked UNVERIFIED, cannot be committed. PITFALLS C11 records the collision between a long hook and `gsd_run query commit`'s 30 s timeout.
**How to avoid:** rows and their second copy land together; the scan and its positive control land with the first rows; a plan that changes defaults lands the field, the builder, `derive` and the ripple tests as one change.

### Pitfall 5: `ls,min` and `lg,max` are table cells, not only formulas
**What goes wrong:** the 4014:2022 table prints `ls,min` and `lg,max` per (size, length) cell, and footnote c states `lg,max = lnom − b` and `ls,min = lg,max − 5P`. Storing only `b` and computing both would make the relation test circular; storing the printed cells makes it a real check.
**How to avoid:** store the printed cells for 4014 and test the relations over them. Spot check on preview cells [VERIFIED: script over cells read from the preview]: M6 x 50 (27.0, 32.0), M8 x 50 (21.75, 28.0), M10 x 100 (66.5, 74.0), M12 x 120 (81.25, 90.0) all satisfy both relations. (A hand-typed cell with the wrong column failed the relation on the first try, which is the double-entry argument in one line.)

### Pitfall 6: Product grade changes the head values at l > 150
**What goes wrong:** M16, (M18) and M20 at 160, 180, 200 are grade B with different `s,min`, `e,min`, `dw,min`, `k,max`, `k,min` (M16 grade A `s,min` 23.67, grade B 23.16; `e,min` 26.75 versus 26.17; `dw,min` 22.49 versus 22.00; `k` 10.18/9.82 versus 10.29/9.71, all preview readings). A row key of size alone is wrong; it is (standard, size, grade), and grade is a function of (d, l): A for d ≤ 24 and l ≤ min(10d, 150), else B (title of the standards, FEATURES). The grade-B 4017 rows in scope are M16 x 160, (M18) x 160 and 180, M20 x 160, 180 and 200.
**How to avoid:** test that the grade stored on each row equals the rule, and that the printed table assignment (Table 2 versus Table 3 for 4017; Table 3 versus Table 4 for 4014) is the `Source.table`.

### Pitfall 7: Second-choice sizes in brackets
**What goes wrong:** the headers read `(M3,5)`, `(M7)`, `(M14)`, `(M18)`, `(M22)` in 4014/4017 [CITED: 4017:2022 and 4014:2022 previews]. TABL-05 wants brackets. The badge copy `matches ISO 4017 M6 × 20` is pinned only for a first-choice size; whether it reads `ISO 4017 (M7) × 20` is undefined (Open Question 4). The designation line never brackets (`Hexagon head screw ISO 4017 - M7 x 20`).

### Pitfall 8: The ISO 262:2023 first/second-choice columns do not survive text extraction
**What goes wrong:** the preview's Table 1 text lists 1, 1.2, 1.4 ... 100 with the two choice columns merged, so the choice cannot be read from extracted text. FEATURES.md says it was read in the 2023 text; the brackets in 4014/4017 agree for M2 to M20.
**How to avoid:** the owner types the choice column from the purchased 262; add a cross-table test: a size is `choice == 2` exactly when its header is bracketed in 4014 and 4017, and every size in 4014/4017 has the same pitch in 262 (the printed `P` row in 4014/4017 is a second independent source).

### Pitfall 9: Float equality for the badge and the caps
**What goes wrong:** `FINE_STL_ROWS` keys and the match compare floats. They work because every value is a decimal literal that round-trips (`repr`) and preset-filled values are the table's own floats. Do not compute `pitch` or `d` anywhere on the way (no `d = M * 1.0`).
**How to avoid:** the catalogue round-trip test above; the existing `turns_of` exact-decimal helper for anything that divides.

### Pitfall 10: Standard lengths are mixed integer and half steps only in the tolerance columns
The nominal lengths are integers; the `min`/`max` columns (e.g. `19,58` to `20,42`) are not used. Do not store them. A `length` field of 20.0 equals the nominal. (Not stored, so not entered, so not double-entered: less surface.)

### Pitfall 11: Catalogue size and the preview STL of the long rows
M20 x 200 4017 preview STL is 446,414 triangles, 21.29 MiB, and its fine STL 138.23 MiB [VERIFIED: probe, one run]; the page loads the preview on every pick. This is Phase 3's rod behaviour carried to the screw, not new, but picking a long M20 now costs a 21 MiB download. Phase 7's sweep owns it; note it in the interim-bounds row.

## Code Examples

All examples run against the project `.venv` this session.

### 1. Head and shank
```python
# Source: probe 2026-10-11 against cadquery 2.8.0 (scratch probe_bolt.py), signature
#   Workplane.polygon(nSides, diameter, forConstruction=False, circumscribed=False)
import math
import cadquery as cq

def head(s: float, k: float, z0: float) -> cq.Solid:
    w = cq.Workplane("XY").workplane(offset=z0).polygon(6, s, circumscribed=True).extrude(k)
    solid = w.val()
    assert isinstance(solid, cq.Solid)   # narrows Shape to Solid, as helical.section does for Wire
    return solid                         # volume (sqrt(3)/2) s^2 k; bbox s in x, s / cos(pi/6) in y

def shank(d: float, z0: float, h: float) -> cq.Solid:
    solid = cq.Workplane("XY").workplane(offset=z0).circle(d / 2).extrude(h).val()
    assert isinstance(solid, cq.Solid)
    return solid
```

### 2. Assembly, closed form and the gate
```python
# Source: probe 2026-10-11; helical.thread, closed_volume, section_area, check_solid are the repo's own
from screw.calc.thread import section_area
from screw.solid import helical

def bolt_solid(d, pitch, length, s, k, t, left_hand):
    thread = helical.thread(d, pitch, t, left_hand=left_hand)          # z in [0, t]
    parts = [shank(d, t, length - t)] if length - t > 0 else []        # 4017: no shank
    parts.append(head(s, k, length))                                   # z in [length, length + k]
    result = thread
    for part in parts:
        result = result.fuse(part)                                     # no clean(): same result
    return result

def bolt_closed_volume(d, pitch, length, s, k, t):
    return (section_area(d, pitch) * t + math.pi * (d / 2) ** 2 * (length - t)
            + math.sqrt(3) / 2 * s * s * k)
```
Probe results (macOS arm64, 12 CPUs, load not controlled, one run each, build plus fuse in one process, ru_maxrss of the cumulative process 475 to 496 MiB; **a researcher probe, not the D-03 probe and not a bound**; the planner records the D-03 probe in `bench/RESULTS.md` itself):

| Case | build+fuse | solids / valid | volume vs closed | z extent |
|---|---|---|---|---|
| M6 x 20 (4017, t=20) | 0.17 s | 1 / True | +4.95e-08 | 0 to 24 |
| M6 x 30 (4014, t=18) | 0.28 s | 1 / True | -7.82e-08 | 0 to 34 |
| M10 x 80 (4014, t=26) | 0.26 s | 1 / True | -7.66e-08 | 0 to 86.4 |
| M16 x 160 (4014, t=44) | 0.30 s | 1 / True | -5.56e-08 | 0 to 170 |
| M20 x 200 (4017, t=200) | 0.45 s | 1 / True | -1.83e-07 | 0 to 212.5 |
| M2 x 4 (4017, t=4) | 0.10 s | 1 / True | -1.58e-06 | 0 to 5.4 |
| M6 x 30 left-hand | 0.45 s | 1 / True | -7.82e-08 | 0 to 34 |

Same values with and without `.clean()`. STL closed: edge-count over the triangle soup found 0 non-manifold edges at preview and fine for M6 x 30, M10 x 80 and M20 x 200. Head plus shank alone add 524 triangles (26,284 bytes) at fine and 124 to 164 at preview (probe `probe_hs.py`, M20 x 200 4014 shape and M6 x 60), which supports D-22's "small next to the thread" with a number: 26 KB against a 64 MiB budget.

### 3. Contract 6 and 7 (verified wiring)
```toml
# Source: scratch import-linter experiment 2026-10-11 (grimp 3.17); KEPT / BROKEN results quoted in Alert 3
[[tool.importlinter.contracts]]
name = "The parameters never consult a table"
type = "forbidden"
source_modules = ["screw.params", "screw.calc.thread"]
forbidden_modules = ["screw.tables"]            # indirect imports checked: do not set allow_indirect_imports

[[tool.importlinter.contracts]]
name = "Tables are a leaf"
type = "forbidden"
source_modules = ["screw.tables"]
forbidden_modules = ["screw.params", "screw.calc", "screw.solid", "screw.app", "screw.cli",
                     "cadquery", "OCP", "fastapi", "logging"]
```
Runtime positive control (a pytest, not import-linter, because grimp does not model the package-init edge):
```python
import subprocess, sys
CODE = ("import sys; from screw.params import BoltParams; BoltParams(); "
        "print('screw.tables' in sys.modules)")
assert subprocess.run([sys.executable, "-I", "-c", CODE], capture_output=True, text=True,
                      check=True).stdout.strip() == "False"
```

### 4. Conflict rule, one function two callers
```python
# calc/thread.py (kernel-free). Text starts with the field names because the CLI prints no loc.
def thread_length_conflict(length: float, thread_length: float) -> str | None:
    if thread_length > length:
        return (f"thread_length and length: thread_length {thread_length:g} mm is longer than "
                f"length {length:g} mm; shorten thread_length or lengthen length")
    return None
```
```python
# app.py, next to refuse_repeated_keys (same registration style: dependencies=[Depends(...)])
def refuse_thread_length_conflict(request: Request) -> None:
    qp = request.query_params
    if "thread_length" in qp and "length" in qp:
        try:
            tl, ln = float(qp["thread_length"]), float(qp["length"])
        except ValueError:
            return                       # the model's own 422 names the bad value
        if (msg := thread_length_conflict(ln, tl)) is not None:
            raise HTTPException(422, detail=[{"loc": ["query"], "type": "thread_length_conflict",
                                              "msg": msg, "ctx": {"fields": ["thread_length", "length"]}}])
```
(The repeated-key dependency runs first, so `qp["length"]` is single-valued here.)

### 5. Per-row relations (verified on the preview numbers listed in the table above)
```python
# tests/test_tables.py -- one parametrised test per catalogue row; ids = row.id
@pytest.mark.parametrize("row", ROWS, ids=lambda r: r.id)
def test_row_relations(row):
    assert row.source.status == "verified"                      # the gate, also scanned below
    assert row.s_min < row.s and row.dw_min < row.s_min
    assert row.e_min < row.s / math.cos(math.pi / 6)            # PITFALLS C7
    assert row.k_min <= row.k <= row.k_max
    assert math.isclose(row.k_max - row.k, row.k - row.k_min, abs_tol=1e-9)   # symmetric: held for 9 columns read
    assert row.grade == ("A" if row.d <= 24 and row.length <= min(10 * row.d, 150) else "B")
    if row.standard == "ISO 4014":
        assert row.b in (2 * row.d + 6, 2 * row.d + 12) and row.b == b_for_band(row.d, row.length)
        assert math.isclose(row.lg_max, row.length - row.b, abs_tol=1e-9)
        assert math.isclose(row.ls_min, row.lg_max - 5 * row.pitch, abs_tol=1e-9)
```
Series rules as cross-checks, read from the 4017 preview figure footnotes c and d and the 4014 footnotes d and e [CITED]: 4017 shortest = nearest standard length to 2d with ties rounded up (M3.5 gives 8, M7 gives 16 in the Table 1 stepped line), greatest = largest standard length not above min(10d, 200); 4014 shortest = 5d (M5 to M8), 4.5d (M10), 4d (M12 to M22), rounded to the nearest standard length, greatest not above 10d or 500 mm. The standard-length list that fits every preview row: 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 180, 200 (ASSUMED as a complete list; owner confirms against ISO 888 or the tables).

### 6. `strip()` is unaffected under the recommended design
`app.py:249-256` re-validates all fields; with no `model_fields_set` rule in the model this is harmless. Do not "fix" it with `exclude_unset=True`; that would be needed only under the rejected design.

### 7. FINE_STL_ROWS re-key
```python
# keys (d, pitch, left_hand) -> largest measured fitting t in mm; run 2026-10-08-a-grid (Alert 2 table)
FINE_STL_ROWS: dict[tuple[float, float, bool], float] = {
    (8.0, 1.25, False): 67.5,  (10.0, 1.5, False): 56.0,  (12.0, 1.75, False): 60.0,
    (14.0, 2.0, False): 58.0,  (16.0, 2.0, False): 52.0,  (18.0, 2.5, False): 65.0,
    (20.0, 2.5, False): 64.0,
    (10.0, 1.5, True): 72.0,   (12.0, 1.75, True): 77.0,  (14.0, 2.0, True): 78.0,
    (16.0, 2.0, True): 75.0,   (18.0, 2.5, True): 91.0,   (20.0, 2.5, True): 91.0,
}   # M8 left-hand: no measured stop up to 80 mm, so no cap
```
The right-hand entries and the keys' float values are quoted from `src/screw/calc/thread.py:182-190`; the left-hand entries are recomputed from the records (Alert 2).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 4017:2014 tables, `dw,min` for d ≤ M5 from `s,min - IT16` | 4017:2022 / 4014:2022: `IT15`, M7 added, tables restructured, greatest/shortest length rules stated | 2022-06 [CITED: 4017:2022 foreword, preview] | A table silently carrying pre-2022 values is wrong; the foreword lists M5 `dw,min` 6.88 (2011) vs 7.20 (2022) [CITED: FEATURES] |
| 4014 up to 15d or longer by trade custom | 4014:2022 greatest `lnom <= 10d` or 500 mm; M12 ends at 120 in the grade A table | 2022 [CITED: preview Table 2 image] | The 4014 series for M2 to M20 stops at 10d; M12 x 130 and 150 are not ISO 4014:2022 rows |
| ISO 262:1998 | ISO 262:2023, range 1 to 100 mm | 2023 [CITED: preview foreword] | Coarse pitches M2 to M20 unchanged in the preview |

**Deprecated/outdated:** DIN 931/933 (withdrawn); the wrench note names them (D-20). The public iTeh previews are structure evidence only: they are not purchased copies and TABL-04 forbids entering a row from them as verified.

## Runtime State Inventory

Not a rename or migration phase. The one runtime-state concern is shareable links: Phase 3 links (`#length=30` and so on) keep their field names and change meaning because the default part gains a head (Pitfall 3). Nothing is stored; no secret, service config, OS registration or build artifact carries a renamed string. The only new generated artefacts are local PDF page images, which must stay out of git (see Environment Availability).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 + `.venv` | everything | yes | 3.12.13 | none needed |
| `make`, `ruff`, `mypy`, `lint-imports`, `pytest` | the gate | yes | GNU Make 4.4.1, ruff 0.16.10, mypy 2.4.0, pytest 9.1.1 | none needed |
| `pdftoppm` (poppler) | the Read tool's `pages` option for the agent's second transcription | **no** | `Read` on a PDF with `pages` returned "pdftoppm is not installed" | (a) `brew install poppler` (brew is at `/opt/homebrew/bin/brew`); (b) a throwaway Swift/PDFKit script, `swift` 6.4 is installed: it rendered the iTeh preview pages to legible 1309 x 1852 PNGs and extracted text, including the stepped bold lines; (c) the owner exports page images |
| PDFs of 4014:2022, 4017:2022, 262:2023 | double entry | owner holds them (D-13) | - | none: no entry without them |
| Docker, node | not needed for `make verify` or this phase's gate | not probed | - | the vendored three.js bundle does not change |

**Missing dependencies with no fallback:** none for building; the standards' page images are the gating input, supplied by the owner.
**Missing dependencies with fallback:** `pdftoppm` (use (a), (b) or (c)). The Swift route is verified only on the public previews, which carry an RC4 permission dictionary and unlocked with an empty password; behaviour on the purchased PDFs is unverified (ASSUMED).
**Licence hygiene (D-16):** keep the purchased PDFs and every rendered page outside the repository tree, or add `*.pdf` and a local standards directory to `.gitignore` in the same commit as the first row; `.gitignore` currently lists neither (`.gitignore` read this session). A second-entry data file must not mimic the printed layout.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 with pytest-xdist 3.8.0, pytest-cov 7.1.0 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (`addopts = "--strict-markers --strict-config -m 'not grid'"`, `filterwarnings = ["error"]`, `xfail_strict`) |
| Quick run command | `make test PYTEST_ARGS="tests/test_tables.py -q -n0 --no-cov"` |
| Full suite command | `make verify` (ruff, mypy --strict, lint-imports, unfinished-work scan, pytest under `fail_under = 96`) |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| THRD-03 | preset fills `thread_length` (4017 = length, 4014 = b by band); editable; conflict 422; warning | unit + API + CLI | `make test PYTEST_ARGS="tests/test_params.py tests/test_api.py tests/test_cli.py -q -n0 --no-cov"` | exists; add cases |
| TYPE-01/02 | bolt and screw build as one valid solid, bbox, volume vs whole-bolt closed form, STL closed | kernel | `make test PYTEST_ARGS="tests/test_solid.py -q -n0 --no-cov"` | exists; rewrite default-bolt tests |
| TABL-01 | catalogue round trip: expand, validate, derive matches own id; `/api/presets` and `screw presets` identical | unit + API + CLI parity | `... tests/test_presets.py` | Wave 0 |
| TABL-02 | `Source` required; mypy rejects a row without it | mypy-in-pytest | `... tests/test_tables.py::test_a_row_without_a_source_fails_mypy` | Wave 0 |
| TABL-03 | one relation test per row; series rule; cross-standard head equality; 262 cross-check | parametrised pure data | `... tests/test_tables.py` | Wave 0 |
| TABL-04 | UNVERIFIED scan and its positive control; double-entry diff | pure data | `... tests/test_tables.py tests/test_tables_second_entry.py` | Wave 0 |
| TABL-05 | 15 sizes, coarse pitches, choice flags, brackets in display | pure data | `... tests/test_tables.py` | Wave 0 |
| TABL-06 | badge: `PresetMatch` exact/custom; `app.js` composes copy from `status` and `display` only | unit + source-read | `... tests/test_calc.py tests/test_parity.py` | exists; extend |
| TABL-07 | designation strings, no property class | unit | `... tests/test_calc.py` | exists; extend |
| INFO-03 | rows by group, finite-or-warned, no-row warning, volume is the closed form | unit | `... tests/test_calc.py` | exists; extend |
| INFO-05 | note only on exact match; M10, M12, M14 only | unit | `... tests/test_calc.py` | exists; extend |
| contracts 6, 7 | import boundaries and the runtime `sys.modules` control | lint + subprocess | `make lint-imports`; `... tests/test_import_boundaries.py` | Wave 0 |
| FRNT-05 | parity: new fields, `--preset` positive rule, new document keys, `app.js` literal-free | parity | `... tests/test_parity.py` | exists; extend |

### Sampling Rate
- **Per task commit:** the quick command for the touched file, then `make verify` is run by the pre-commit hook anyway.
- **Per wave merge:** `make verify`.
- **Phase gate:** `make verify` green, then `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `tests/test_tables.py` - per-row relations, UNVERIFIED scan with positive control, `Source` typing via `mypy.api`, series rules, cross-standard checks (REQ-TABL-02..05)
- [ ] `tests/test_tables_second_entry.py` and `tests/data/` - the double-entry diff (REQ-TABL-04); blocked on the owner's copy
- [ ] `tests/test_presets.py` - catalogue round trip, 4017-before-4014 tie, API/CLI catalogue identity, fine-STL-refused count (REQ-TABL-01)
- [ ] `tests/test_import_boundaries.py` - the subprocess `sys.modules` control (Alert 3)
- [ ] Update the ripple list in Pitfall 3; no framework install is needed
- [ ] Coverage: new modules must keep the total at or above `fail_under = 96`; data-only modules are covered by being imported

## Security Domain

`security_enforcement` is on (absent or true), ASVS level 1, `security_block_on: high`.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | none exists (CODING_VALUES: no authentication) |
| V3 Session Management | no | none exists |
| V4 Access Control | no | public read-only tool |
| V5 Input Validation | yes | pydantic field metadata (`gt`, `le`, `allow_inf_nan=False`), `extra="forbid"`, the one cross-field rule, `refuse_repeated_keys`, the new conflict dependency |
| V6 Cryptography | no | none |
| V12 Files and Resources | partly | exports use `tempfile.TemporaryDirectory` with `slug()`-derived names (existing); the new fields enter `slug()` as `%g` numbers only |
| V13 API | yes | typed response models, 404 shape copied from `/api/schema`, no new write route |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Resource exhaustion through `s`, `k`, `thread_length`, `length` | Denial of service | `gt=0`, `le=INTERIM_MAX_MM`, turn cap on `t`, INTERIM caps; note `length` can now be large with a short thread, so a long cheap shank is accepted by design (D-22) |
| Preset id from the command line treated as a path or expression | Tampering | argparse string looked up in an in-memory dict; unknown id exits 2 naming it; never `eval`, never a file path |
| `kind` echoed in the 404 body | Information disclosure / XSS | existing `!r` echo in JSON; the page uses `textContent` only (`test_the_ui_builds_nodes_from_text_only`) |
| Preset catalogue as a cost vector | Denial of service | built from in-memory tables, a few hundred rows, no kernel; optionally cached per kind |
| Licensed ISO text committed | Legal | PDFs and page images outside the repo or gitignored; `Source` holds identifiers only (D-16) |
| Supply chain | Tampering | no new dependency this phase |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The standard-length list 2 ... 200 listed in Code Example 5 is complete for M2 to M20 | Code Examples 5 | Series cross-check test rejects a real row or admits a fake one; the owner's transcription still governs |
| A2 | Series rules (4017 shortest = 2d rounded, ties up; 4014 shortest 5d / 4.5d / 4d) hold for every size, including M2 to M4 for 4014 (not covered by the footnote) | Code Examples 5, Anti-Patterns | The test needs per-size exceptions; M2 to M4 4014 series is data either way |
| A3 | Head values (`s`, `e`, `dw`, `k`) are identical across 4014 and 4017 for each (size, grade) | Pitfall 5, test list | Observed for 9 columns in the previews only; if the standards diverge, drop the cross-standard relation at the checkpoint |
| A4 | Recommended second text for explicit `thread_length` above a default `length`: `thread_length 30 exceeds length 20: thread built to the full length` | Alert 6 | Wording is a pin the owner or planner must set |
| A5 | The PDFKit render and text route works on the purchased PDFs | Environment Availability | The agent's second copy needs `brew install poppler` or owner-supplied images |
| A6 | A left-hand designation form (`-LH` or none) | Open Question 5 | Designation withheld for left-hand parts until the owner reads Clause 7 |
| A7 | Picker `axes` / `choice` catalogue shape | Pattern 5 | A planner-level alternative shape; any shape must keep `app.js` free of field-name literals |
| A8 | Catalogue row count of about 294 (186 + 108) | Summary, Alert 7 | Sizing only; the transcription fixes the real count |
| A9 | Kernel behaviour on linux/amd64 equals macOS arm64 for the fuse | Code Examples 2 | CI could differ (STATE records an earlier linux-only kernel failure in a different construction); the CI `test` job is the check, and Phase 7 re-sweeps |
| A10 | The 4014 `b` for l above 200 (2d + 25) never applies to M2 to M20 | THRD-03 | The 4014 greatest length for M20 is 200, so no row reaches it |

## Open Questions (RESOLVED)

1. **Confirm the D-08 mechanism (Alert 1).**
   - What we know: `model_fields_set` cannot carry the rule; a request-boundary function can.
   - What's unclear: whether the owner accepts "direct Python construction is not refused, the build and info use `t = min(...)` and warn".
   - Recommendation: the design in Alert 1; record it in L13 as the D-08 mechanism, leaving D-08's observable behaviour unchanged.
   - **RESOLVED (D-25, owner 2026-10-11):** the owner accepted the model-level exception: `BoltParams(length=10, thread_length=30)` built in Python is accepted, built to `t = min(...)` and warned; the 422 for two explicit values lives at the request boundary (API dependency, CLI `_params`). Plan 04-05 builds it; plan 04-14 records the acceptance in L13.
2. **Pin the warning text for an explicit `thread_length` above a default `length` (Alert 6).** Recommendation: `thread_length <T> exceeds length <L>: thread built to the full length` for any non-default `thread_length`.
   - **RESOLVED (D-25):** pinned as recommended, `thread_length <T> exceeds length <L>: thread built to the full length` (plan 04-04).
3. **D-23: keep the 422 or build and warn (Alert 4).** Recommendation: keep it (locked), restate the reason, write the message so it tells the user `s` must exceed `d`.
   - **RESOLVED (D-26):** the 422 `head_too_small` stays; the reason is product policy, not a kernel necessity; the message names `s` and `d` and says `s` must exceed `d` (plan 04-03).
4. **Badge and display copy for bracketed sizes.** `ISO 4017 (M7) × 20` or `ISO 4017 M7 × 20`? Recommendation: brackets in the picker and the catalogue `choice`, and in the badge and `display` too, so the copy matches the standards (TABL-05); pin it in UI-SPEC Copywriting.
   - **RESOLVED (D-28):** brackets everywhere: picker, catalogue `choice`, badge and `display` (`ISO 4017 (M7) × 20`); the designation stays unbracketed (plans 04-07, 04-09, 04-13).
5. **Left-hand designation.** Clause 7 is not in either public preview (the 4017 contents list "7 Designation" on page 8 of the standard, the preview ends at Table 4). The owner reads it at the checkpoint; withhold the designation for left-hand parts if no form exists.
   - **RESOLVED (procedure, CONTEXT Claude's Discretion):** the owner reads Clause 7 of ISO 4017:2022 and ISO 4014:2022 at plan 04-01 Task 2 and gives the left-hand form or `none`, recorded in `04-OWNER-READS.md`; if the clause gives no form, the designation is withheld (null) for left-hand parts rather than invented (plan 04-08).
6. **Shank sliver rule (Alert 6): fold or refuse?** Recommendation: fold below `MIN_TAIL_MM` into the thread, applied through `built_thread_length` so every consumer agrees.
   - **RESOLVED (D-27):** fold, not refuse, through one `built_thread_length` (plan 04-04).
7. **Add the thread-only gate (Alert 5)?** Recommendation: yes, one extra precise volume on the bare thread.
   - **RESOLVED (planned):** the bare-thread gate runs before the fuse in `_build`, with a positive control for a thread error the whole-part gate dilutes (plan 04-03 Tasks 1 and 2).
8. **Where the D-03 pre-plan probe is recorded.** The researcher probe above is not durable (scratch scripts) and must not be cited as the D-03 entry; the plan's first task re-runs it and writes `bench/RESULTS.md`. Optional: reuse `bench/thread_spike` helpers for the fuse and `bench/quiet.py` for the load reading (labelled non-decisive).
   - **RESOLVED (planned):** plan 04-01 Task 1 re-runs it as `bench/head_fuse.py` and records `## Head fuse probe (Phase 4, D-03)` in `bench/RESULTS.md`, labelled a probe and not a bound.

## Sources

### Primary (HIGH confidence)
- Project code and docs read this session: `src/screw/params.py`, `calc/__init__.py`, `calc/thread.py`, `solid/__init__.py`, `solid/bolt.py`, `solid/helical.py`, `app.py`, `cli.py`, `static/app.js`, `index.html`, `style.css`, `pyproject.toml`, `Makefile`, `tests/test_parity.py`, `test_calc.py`, `test_params.py`, `test_thread_maths.py`, `test_api.py`, `test_cli.py`, `bench/corpus.py`, `docs/architecture/decision_log.md` (L12), `docs/architecture/overview.md`, `docs/CODING_VALUES.md`, CONTEXT, REQUIREMENTS, STATE, research files ARCHITECTURE, FEATURES, PITFALLS, STACK.
- Runtime probes (scratch scripts in the session scratchpad, not durable): fuse and gate (`probe_bolt.py`, `probe_edge.py`, `probe_s.py`), STL closure (`probe_stl.py`), head and shank bytes (`probe_hs.py`), grimp experiment (`il/`), FastAPI `model_fields_set` probe, `bench/results/thread-spike/2026-10-08-a-grid.jsonl` recomputation.
- FastAPI source: `.venv/lib/python3.12/site-packages/fastapi/dependencies/utils.py:749-776`.

### Secondary (MEDIUM confidence)
- ISO 4017:2022 public preview (iTeh), Tables 1 to 4 and Figure 1 footnotes: `https://cdn.standards.iteh.ai/samples/72585/1179998ddd594550a909d6e13c416f3e/ISO-4017-2022.pdf`. Read through PDFKit text and page renders this session. Structure and illustrative values only.
- ISO 4014:2022 public preview (iTeh), Tables 1 to 4: `https://cdn.standards.iteh.ai/samples/72579/81f2b1e966b440d7a25f6734e508ea48/ISO-4014-2022.pdf`. Same use.
- ISO 262:2023 public preview (iTeh), Table 1: `https://cdn.standards.iteh.ai/samples/85105/41945f5384e447fe8c9492f4e23251a3/ISO-262-2023.pdf`. Sizes and coarse pitches M2 to M20 read; choice columns not recoverable from text.
- DIN 933 versus ISO 4017 wrench sizes (M10 17/16, M12 19/18, M14 22/21): [Eurolink FSS blog](https://blog.eurolinkfss.com/din-933-vs.-iso-4017-and-din-931-vs.-iso-4014) and [Wermac, hex bolt dimensions](https://wermac.org/bolts/metricBDC.html) (DIN 931/933 `s` max 17.00, 19.00, 22.00, ISO smaller at these sizes), plus the ISO side from the 4017:2022 preview (16, 18, 21). Two independent web sources agree with the standard's own preview, which satisfies D-20's "two independent sources" test at MEDIUM confidence; the note should still name DIN 933 for screws and DIN 931 for bolts.

### Tertiary (LOW confidence)
- Web search summary for the DIN comparison (used only to find the two pages above).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, nothing new, versions read from `.venv`
- Architecture: HIGH for kernel, import graph and FastAPI behaviour (run), MEDIUM for the catalogue shape and test layout (recommendations)
- Table structure: MEDIUM, public previews only; values are the owner's and the agent's to enter
- Pitfalls: HIGH where a probe or source read backs them, MEDIUM for the series rules

**Research date:** 2026-10-11
**Valid until:** 2026-11-10 for the code findings (stable); the table structure stays valid until a new ISO edition; re-run the fuse probe if cadquery or cadquery-ocp changes.
