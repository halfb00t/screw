# Phase 3: Real Helical Thread - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-10
**Phase:** 3-real-helical-thread
**Areas discussed:** Caps on arbitrary (d, pitch, length), Pitch validity bound, Info panel after the skeleton, Debt items this phase absorbs + slow tier

---

## Caps on arbitrary (d, pitch, length)

### Turns above L11's 250-turn construction cap

| Option | Description | Selected |
|--------|-------------|----------|
| 422 naming length and pitch | Refused at the params boundary; `length` is an explicit choice; above 250 turns is unmeasured | ✓ |
| Cap length to 250·pitch and warn | L11's literal "cap-and-warn"; serves a different part than the link names | |
| No turn cap; INTERIM 30 s timeout only | Every CPU-bomb request ties a worker for 30 s | |

**User's choice:** 422 naming `length` and `pitch`.

### What the per-size bytes cap gates

| Option | Description | Selected |
|--------|-------------|----------|
| Fine STL only: 422 on `model.stl?quality=fine` above the cap | Info, preview, STEP build at the asked length; narrows L11's "cap-and-warn" to "refuse" for one artefact | ✓ |
| Geometry cap-and-warn on every output | Caps preview and STEP that were never over budget | |
| Serve everything, cache nothing over budget | Today's behaviour (`app.py:72`); would re-litigate L11 | |

**User's choice:** Fine STL only.
**Notes:** Verified during the discussion that `_BlobCache.put` drops any blob larger than the budget, so an over-budget fine STL is rebuilt on every request.

### Which cap applies to an off-row (d, pitch)

| Option | Description | Selected |
|--------|-------------|----------|
| Exact-row match only; off-row gets the turn cap alone | No cap from a mapping nobody measured (L02) | ✓ |
| Nearest ISO size at or above d, in turns | Conservative in d but ignores pitch; unmeasured | |
| Refuse any off-row (d, pitch) | Needs the ISO 262 table in `params` (contract 6; Phase 4) | |

**User's choice:** Exact-row match only.

---

## Pitch validity bound

| Option | Description | Selected |
|--------|-------------|----------|
| Geometric bound only: root radius > 0 | 422 when `d/2 - 5H/8 <= 0`; the gate and the timeout cover the rest | ✓ |
| Geometric bound + a warning outside the measured band | Adds the first non-skeleton warning | |
| Refuse pitch/d outside the measured band | Refuses every fine pitch and odd combination | |

**User's choice:** Geometric bound only.
**Notes:** Closes Phase 1 D-07's open `pitch >= d` question.

---

## Info panel after the skeleton

### Panel rows

| Option | Description | Selected |
|--------|-------------|----------|
| d, pitch, length, turns, volume + thread depth and basic minor diameter | Labelled "ISO 68-1:2023 basic profile"; d2 waits for Phase 5 | ✓ |
| Minimal: d, pitch, length, turns, volume | Everything else in Phase 5 | |
| Also pitch diameter d2 = d − 3H/4 | ISO 724 formula, unread | |

**User's choice:** Depth and minor diameter included; d2 deferred.

### Standing warning

| Option | Description | Selected |
|--------|-------------|----------|
| A new standing warning naming what is missing | `threaded rod: no head, plain-cut thread ends; not a product build` | ✓ |
| No standing warning | Headless rod with no label | |

**User's choice:** New standing warning.

### Hand on the panel

| Option | Description | Selected |
|--------|-------------|----------|
| Not a row | `InfoRow` stays numeric (D-15 of Phase 1) | ✓ |
| A text-valued row variant | Touches the contract and the renderer for one fact | |

**User's choice:** Not a row.

---

## Debt items this phase absorbs + slow tier

### Debt items folded (multi-select)

| Option | Description | Selected |
|--------|-------------|----------|
| Collapsed thin solid served as 200 (blocker) | The THRD-04 gate replaces the hole; export status checks added; no INTERIM lower bound | ✓ |
| UI drops foreign hash keys (must) | Trigger: the first shareable field (`left_hand`) | ✓ |
| UI hides warnings on a failed update (must) | Trigger: the first non-skeleton warning | ✓ |

**User's choice:** All three folded.

### Foreign hash key behaviour

| Option | Description | Selected |
|--------|-------------|----------|
| Refuse the link, naming the keys, like the unknown-kind case | Parity with the API 422 and CLI exit 2 | ✓ |
| Name the dropped keys in #messages and build with the rest | Builds a part the link did not describe | |

**User's choice:** Refuse the link.

### Harness review debt fired by the D-18 import-back

| Option | Description | Selected |
|--------|-------------|----------|
| Separate /gsd-quick harness PR before the Phase 3 PR | Phase 3's diff stays about the thread; the import-back is a pure move | ✓ |
| Fold into Phase 3 as its own plan | One large PR; WR-03 owner question mid-phase | |
| Do not touch bench/: duplicate the builder | Breaks 02 D-18 and spur 11-05 | |

**User's choice:** Separate `/gsd-quick` harness PR first (precondition).

### The SC4 slower tier

| Option | Description | Selected |
|--------|-------------|----------|
| Separate workflow file, manual + scheduled, not in required-jobs | `.github/workflows/grid.yml`; L08's wall unchanged | ✓ |
| A required job in ci.yml | Every PR waits hours | |
| The spike harness grid block on the owner's host | A record, not a gate; nothing unattended | |

**User's choice:** Separate workflow file.

### Repeated query key debt (follow-up)

| Option | Description | Selected |
|--------|-------------|----------|
| Fold into Phase 3 | `?left_hand=true&left_hand=false` is exactly its case; CLI side lands with `BooleanOptionalAction` | ✓ |
| Leave it active; separate /gsd-quick later | Ships the first boolean with duplicate-wins intact | |

**User's choice:** Fold into Phase 3.

---

## Claude's Discretion

- Exact turns from float `length / pitch` (builder end face at `z = length`).
- Where the kernel-free rules live (`calc/thread.py`) and how `params`, `app` and `cli` reach them.
- 422/error wording beyond the named fields; the `turns` row unit.
- INTERIM `TESSELLATION` kept until Phase 5.
- The `make verify` sample beyond the stated minimum; pytest marker name; grid sharding; coverage floor re-measure.
- `solid/bolt.py` keeps its name over `helical.thread`.
- Branch `gsd/phase-03-real-helical-thread` from `main` at `a0c7923`.

## Deferred Ideas

- `d2` panel row — Phase 5 (INFO-01, ISO 724).
- Pitch/d measured-band warning — not adopted; Phase 7 measures caps.
- Nearest-size bytes-cap mapping — rejected.
- Tip chamfer / head-side fade — Phase 5 (THRD-05).
- Mesh presets vs thread depth and clearance — Phase 5 (FRNT-06), `2026-10-08-a-ladder`.
- Measured per-size caps — Phase 7 (OPER-03).
- WR-03 protocol amendment — the harness `/gsd-quick` PR.
- Text-valued `InfoRow` — not adopted.
