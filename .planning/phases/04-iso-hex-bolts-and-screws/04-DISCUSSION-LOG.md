# Phase 4: ISO Hex Bolts and Screws - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-11
**Phase:** 4-iso-hex-bolts-and-screws
**Areas discussed:** Bolt geometry this phase, Fields and defaults, Presets on 3 front ends, Table rows and the gate, Info panel content and shape, Caps with thread_length

---

## Bolt geometry this phase

### Head form

| Option | Description | Selected |
|--------|-------------|----------|
| Plain hex prism s × k | Sharp corners at s/cos 30; closed form exact; one planar fuse; geometric across-corners labelled apart from the row's e,min | ✓ |
| Prism chamfered to dw at a stated angle | Needs an unspecified angle and dw; cone∩prism volume in the gate; one more unmeasured boolean | |
| Washer-faced head (grade A figure) | Washer face dw × c; two extra booleans; closest to a real bolt, furthest from what Phase 2 measured | |

**User's choice:** Plain hex prism s × k

### Under-head fillet and tip chamfer (TYPE-01 vs THRD-05)

| Option | Description | Selected |
|--------|-------------|----------|
| Neither; amend TYPE-01 | Plain planar ends (03 D-16); fillet and tip chamfer to Phase 5 THRD-05 after ISO 4753 is read; TYPE-01 amended | ✓ |
| Fillet now at r,min; tip later | A cited minimum, but a fragile fillet on a fused junction whose volume must enter the closed form | |
| Both now; buy ISO 4753 first | Adds a standard and a checkpoint before planning can finish | |

**User's choice:** Neither; amend TYPE-01
**Notes:** ISO 4753 is added to the purchase list for Phase 5.

### ISO 4014 shank and junction

| Option | Description | Selected |
|--------|-------------|----------|
| Cylinder at d, planar step | Shank at d (ds nom); thread over thread_length only, planar cut fused to the shank end face (Anti-Pattern 7); fuse cost probed before planning | ✓ |
| Cylinder at d with a run-out fade | Varying section changes L11's measured construction; re-measure first | |
| Shank at the pitch diameter | The ISO 4015 shape, not 4014; a value no 4014 row carries | |

**User's choice:** Cylinder at d, planar step

### Standing warning text

| Option | Description | Selected |
|--------|-------------|----------|
| Name what is still missing | `plain-cut thread ends, no tip chamfer or under-head fillet; not a product build` | ✓ |
| Keep only 'not a product build' | Shorter; the flat tip goes unexplained on the page | |
| You decide the wording | Claude writes it under a stated rule | |

**User's choice:** Name what is still missing

---

## Fields and defaults

### Which dimensions become fields

| Option | Description | Selected |
|--------|-------------|----------|
| s, k, thread_length only | The three values that shape the solid; e, dw, b, ls, lg, grade are panel values | ✓ |
| s, k, thread_length plus dw now | A geometry-inert field for a whole phase | |

**User's choice:** s, k, thread_length only

### Field names

| Option | Description | Selected |
|--------|-------------|----------|
| ISO symbols: s, k, thread_length | `d` precedent; titles carry the words | ✓ |
| Words: across_flats, head_height, thread_length | Mixed styles with d and pitch; longer links | |

**User's choice:** ISO symbols

### Frozen defaults

| Option | Description | Selected |
|--------|-------------|----------|
| ISO 4017 M6×20 row, after your read | s=10, k=4, thread_length=20 expected; committed only after the owner reads the purchased standard; badge matches at startup | ✓ |
| Preview values now, verify later | One-way default on an unverified number | |
| Round numbers, no row | Badge reads custom at startup | |

**User's choice:** ISO 4017 M6×20 row, after your read

### thread_length > length

| Option | Description | Selected |
|--------|-------------|----------|
| 422 if both set; cap+warn if default | model_fields_set decides; min(thread_length, length) is built; pinned warning text | ✓ |
| Always a 422 naming both | Shortening length on the form is a 422 until thread_length is edited too | |
| Default None = full thread | Not an absolute-mm default; L02 wording would need a note | |

**User's choice:** 422 if both set; cap+warn if default

---

## Presets on 3 front ends

### Preset id in the link?

| Option | Description | Selected |
|--------|-------------|----------|
| No id in the link | Badge from the fields; 'custom, based on' only in the live session; reloaded edited links read `custom` | ✓ |
| `preset=` key in the hash as metadata | Stale basis rides in links; rule 10 needs a whitelist | |
| Server infers the basis | A guessed basis printed (L02) | |

**User's choice:** No id in the link

### Catalogue API shape

| Option | Description | Selected |
|--------|-------------|----------|
| One catalogue document | `GET /api/presets?kind=` with every row's fields, id, display, designation, citation; 404 on unknown kind | ✓ |
| List plus expand (research shape) | Two endpoints, a round trip per pick | |
| Inside /api/schema | Schema grows to tens of KB; two concerns mixed | |

**User's choice:** One catalogue document

### Id grammar and CLI

| Option | Description | Selected |
|--------|-------------|----------|
| `iso4017:M6x20`; --preset on info/export + `screw presets` | Explicit flags override; unknown id exits 2; parity test whitelists `--preset` | ✓ |
| Three flags: --standard, --size, --length-nom | Three non-field flags; `--length-nom` beside `--length` | |
| `--preset` only, no listing command | Ids discoverable only via the API or source | |

**User's choice:** `iso4017:M6x20`; --preset + `screw presets`

### Picker

| Option | Description | Selected |
|--------|-------------|----------|
| 3 selects, pick fills all, Reset = defaults | Standard / Size / Length; lengths filtered per size; bracketed second-choice sizes; no confirm dialog; selects track the fields | ✓ |
| 3 selects with a confirm on overwrite | A modal on a common action (PITFALLS M3) | |
| One combined list | Hundreds of entries, no filtering | |

**User's choice:** 3 selects, pick fills all, Reset = defaults

---

## Table rows and the gate

### TABL-04 precondition

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, all three | ISO 4014:2022, 4017:2022, 262:2023 in hand | ✓ |
| Not yet | Buy-and-read checkpoint first | |
| Some of them | Sequence the missing ones | |

**User's choice:** Yes, all three

### Transcription and proof

| Option | Description | Selected |
|--------|-------------|----------|
| Double entry, diffed by a test | Owner types one copy, agent transcribes a second from the same PDF pages; a test diffs them; relation tests on top | ✓ |
| Agent transcribes, you spot-check | A transcription slip in an unchecked row ships | |
| You type everything; agent writes plumbing | One human's typos, caught only where the preview overlaps | |

**User's choice:** Double entry, diffed by a test

### UNVERIFIED gate meaning

| Option | Description | Selected |
|--------|-------------|----------|
| Never on main: make verify refuses it | A test fails on any UNVERIFIED row under src/screw/tables/; no runtime filtering, no version check | ✓ |
| Staged: present, never served, release gate | Runtime filtering plus a version-keyed test | |
| Version-keyed gate only | A dev deployment prints preview numbers | |

**User's choice:** Never on main

### Licence stance

| Option | Description | Selected |
|--------|-------------|----------|
| Values + citation only, no standard text | Numeric values with Source(standard, edition, table, column); no wording, notes, figures, layout | ✓ |
| Values only, cite standard + edition | Weaker than TABL-02 | |
| Ask a lawyer before any row lands | Blocks the phase | |

**User's choice:** Values + citation only, no standard text

---

## Info panel content and shape

### Document shape for badge, designation, groups

| Option | Description | Selected |
|--------|-------------|----------|
| Typed fields on PartInfo + group on InfoRow | `group` per row; `designation`, `preset` (status, id, display) on PartInfo; value stays float | ✓ |
| Text-valued rows | A badge as a row with empty unit | |
| Page computes them from the catalogue | Parity gap on the CLI | |

**User's choice:** Typed fields on PartInfo + group on InfoRow

### Row match rule

| Option | Description | Selected |
|--------|-------------|----------|
| Field-derived always; row values only on an exact match | Row minima, b ref, grade only when every field the row defines matches; otherwise absent plus one pinned warning | ✓ |
| Row values keyed on (d, pitch) alone | Prints a number about a different part | |
| Field-derived only, never row values | Drops e,min, dw,min, b, grade from the panel | |

**User's choice:** Field-derived always; row values only on an exact match

### Browser rounding fix

| Option | Description | Selected |
|--------|-------------|----------|
| Page shows String(row.value) | The API's number as sent; UI-SPEC rule 23 becomes its target; debt resolved | ✓ |
| Server sends a display string per row | A rounding rule to defend | |
| Round derived values server-side | Still a rounding | |

**User's choice:** Page shows String(row.value)

### DIN note and product grade

| Option | Description | Selected |
|--------|-------------|----------|
| A `notes` list on PartInfo | Rendered after warnings in their own style; only on an exact row match | ✓ |
| Fold them into `warnings` | Trains users to skip warnings | |
| Into the row labels | A sentence in a label; grade is not a number | |

**User's choice:** A `notes` list on PartInfo

---

## Caps with thread_length

### WR-02 ruling

| Option | Description | Selected |
|--------|-------------|----------|
| Key by hand, left-hand caps from the records | (d, pitch, left_hand); left-hand caps re-derived from 2026-10-08-a-grid.jsonl; message, comment and L12 reworded to the measured quantity | ✓ |
| One conservative cap for both hands, reworded | Refuses left-hand parts measured as fitting | |

**User's choice:** Key by hand, left-hand caps from the records

### Cap input on a bolt

| Option | Description | Selected |
|--------|-------------|----------|
| The built thread; head and shank noted as unmeasured | Both caps read min(thread_length, length); head/shank bytes recorded as unmeasured in the interim-bounds item | ✓ |
| Re-measure the seven bytes rows on the finished bolt first | A single-host probe for a difference of kilobytes | |
| Keep `length` as the cap input | Refuses turns a 4014 bolt does not build | |

**User's choice:** The built thread; head and shank noted as unmeasured

### Bounds on s, k, thread_length

| Option | Description | Selected |
|--------|-------------|----------|
| s > d as a 422 naming both; k > 0; usual ceilings | gt 0, le INTERIM_MAX_MM; `head_too_small` names s and d | ✓ |
| No cross-field rule; let the gate refuse | An unhelpful kernel message instead of the two fields | |
| Also bound k and s to the ISO envelope | An unmeasured envelope; contract 6 | |

**User's choice:** s > d as a 422 naming both; k > 0; usual ceilings

---

## Claude's Discretion

Listed in 04-CONTEXT.md § Claude's Discretion: head position on z; the pre-plan fuse probe's scope; left_hand in the match and the `-LH` designation as the standard spells it; 4014 rows with l ≤ b matching 4017; length-series and grade-B encoding; the relation-test list; contract 6 wiring given `params → calc.thread`; module layout; `screw presets` output; picker and notes DOM; amendment wording; the phase branch.

## Deferred Ideas

Chamfered or washer-faced head; run-out fade; tip chamfer and under-head fillet (Phase 5 with ISO 4753); dw as a field; `preset=` hash metadata (rejected); nearest-row inference (rejected); server display string (rejected for now); re-measuring bytes caps on the finished bolt (Phase 7); Annex A nuts, d2, ISO 724, 965-2 (Phase 5); DIN aliases (v2); `s` on the base (Phase 5).
