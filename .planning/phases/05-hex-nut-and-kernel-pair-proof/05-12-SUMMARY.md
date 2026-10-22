---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 12
subsystem: solid
tags: [bolt, tip-cone, fillet-ring, tables, double-entry, gates, thrd-05]
requires:
  - phase: 05-11
    provides: "tip_cone_volume, fillet_ring_volume, TIP_ANGLE_DEG, T_PIECE, piece_refusal"
provides:
  - "tables/iso4014.py FILLETS: 14 cited r,min rows (M2 to M20, no M7) read from GOST R ISO 4014-2013, double-entered against tests/data/owner/iso4014_fillets.tsv"
  - "calc/thread.py FILLET_R, fillet_radius, tip_cone_length, tip_cone_fits, bolt_end_closed_volume (kernel-free; FILLET_R pinned equal to FILLETS by a test)"
  - "solid/bolt.py tip_cut, fillet_ring, add_fillet; _build_bolt judges each end piece at T_PIECE and the whole part at T_GATE"
  - "calc derive: volume row with the tip and ring, short-thread tip warning, ISO 4017 no-fillet note"
  - "60-case watertight preview sweep over both standards, both hands"
affects: [05-13, 05-18]
requirements-completed: []  # THRD-05 stays open: the nut's lead-ins are 05-13
estimate_ref: "120000 tokens, 3 tasks"
actuals:
  tokens: 13600
  tasks: 3
  commits: 3
plan_head_before: 8654eebdd5347e318d4d62397cf45714884ae690
plan_head_after: 8b35dfc817c806fa8e96a32cfcddc06708abddd2
key-files:
  created:
    - tests/data/owner/iso4014_fillets.tsv
    - docs/tech_debt/active/2026-10-20-tip-cone-degenerate-boolean-at-the-cone-length.md
  modified:
    - src/screw/tables/rows.py
    - src/screw/tables/iso4014.py
    - src/screw/calc/thread.py
    - src/screw/calc/__init__.py
    - src/screw/solid/bolt.py
    - src/screw/solid/__init__.py
    - tests/test_tables.py
    - tests/test_tables_second_entry.py
    - tests/test_calc.py
    - tests/test_api.py
    - tests/test_solid.py
key-decisions:
  - "Fillet r,min is read from GOST R ISO 4014-2013 (ISO 4014:2011), by the owner's ruling at this plan's precondition (L14 amendment), cited as `GOST R ISO 4014-2013 (ISO 4014:2011)`"
  - "The piece check runs before the cut thread's whole-thread gate, so a skipped or wrong-angle cut is named as the tip cone and not as a thread that is off"
  - "assemble() is unchanged and builds the bolt without the ring; add_fillet fuses it, so the ring's added volume is measured from precise volumes before and after"
status: complete
---

# Phase 5 Plan 12: The bolt's ends Summary

Every bolt now gets a 45 degree tip cone cut on its bare thread, and a bolt on a cited ISO 4014 (d, pitch) row with a plain shank at least r long gets a revolved fillet ring fused under the head; each end is judged by its own volume at `T_PIECE` and the whole part at `T_GATE`.

## Task commits

| Task | Commit | Message |
| ---- | ------ | ------- |
| 1 | 24528c6 | feat(tables): ship the ISO 4014 under-head fillet radii, double-entered |
| 2 | 8454888 | feat(bolt): cut the tip end read from GOST 12414-94 and fuse the under-head fillet, each gated by its piece |
| 3 | 8b35dfc | test(bolt): sweep both standards for a watertight preview mesh |

`commits: 3` is measured from the plan-start ledger (`git rev-list --count 8654eeb..HEAD`).

## Task 1: the fillet radii, double entry

Preconditions (all re-checked): R1 reads option a; the L14 open question is answered (GOST R ISO 4014-2013); the PDF's sha256 equals `e44006af...fb47` and renders; the owner copy's `head -1` was read and no data row until the transcription was written.

I transcribed `r` (minimum row) from rendered page images (PDF pages 8 and 10 for Table 1, page 13 for Table 2, `pdftoppm` to my own scratch directory, no text extraction), together with `P` per size, into `/private/tmp/.../05-12/mine.tsv`, and only then read the owner copy. The two files are byte-identical (`diff` empty): 14 rows, M2 to M20, **no M7 on either side** (neither table prints M7, so an M7 bolt gets no fillet, R1). No disagreement, so no checkpoint. M1,6 and sizes above M20 are outside the product's M2 to M20 and are not rows.

`FilletRadius` and `FILLETS` carry `Source(standard="GOST R ISO 4014", edition="2013", ...)`; `Source.document()` is exactly `GOST R ISO 4014-2013 (ISO 4014:2011)` through a new `ADOPTED_ISO` entry. Phase 4's ISO 4014:2022 rows are untouched and a test pins their citation. `FILLET_R` in `calc/thread.py` is a second typed copy keyed on exact (d, pitch), pinned equal to the cited rows by a test (a planted mismatch names the key). The diff entry `iso4014_fillets.tsv` runs in `make verify`.

## Task 2: tip cone and fillet ring

- `tip_cut(p, bare)` intersects the bare thread with the revolved envelope the probe used; the cone meets the end face at the minor radius and rises at `TIP_ANGLE_DEG` (45, read 6/R2). `fillet_ring` revolves the quarter-circle region; no OCCT fillet is used (`.fillet(` is absent).
- `_build_bolt`: gate the uncut thread, cut, **piece check on the removed volume**, gate the cut thread against `closed_volume - tip_cone_volume`, assemble, fuse the ring, **piece check on the added volume**, gate the whole part against `bolt_end_closed_volume`. `check_solid` gained an optional `volume` argument and returns the volume it judged, so no precise volume is integrated twice; `check_structure` is the structural half, run before any piece volume is read.
- `derive`: the volume row is `bolt_end_closed_volume`; its formula text names the tip cone and the ring; a thread no longer than the cone gets the warning `thread_length: the built thread of ... is not longer than the ... mm tip cone, so no tip cone is cut`; a matched ISO 4017 row carries the note `no under-head fillet: the thread runs to the head (ISO 4017:2022)` as a note.
- Tests: the cut removes the oracle volume and the ring adds the Pappus volume to within `T_PIECE` on the default, M6 x 60, M10 x 80 and M10 x 200; a shank exactly r long gets the ring and one float less does not; left-hand passes; the three positive controls (skipped cut, 30 degree cone where 45 is the model, ring dropped) are each refused naming the piece on M6 x 60 and M10 x 200.

Measured build seconds (`time.perf_counter`, single runs, one host, load not controlled), before this plan's solid change and after:

| Bolt | Before | After |
| ---- | ------ | ----- |
| M6 x 20 (thread to the head: cone, no ring) | 0.42 s | 0.82 s |
| M20 x 200, thread 46 mm (cone and ring) | 0.38 s | 0.98 s |

## Task 3: the watertight sweep

`test_every_size_of_both_standards_meshes_watertight_at_preview` collects 60 ids (15 sizes x 2 standards x 2 hands) and passes: 0 open edges on every part. Wall time of the sweep alone: **62.5 s** with `-n0`, **13.3 s** with the default 8 workers. Full `make verify`: **3144 passed in 101.65 s (1:41)**, coverage 98.02% against 96.0%.

## Deviations from Plan

### Owner-ruled deviations

**1. [Owner ruling] Source substitution: GOST R ISO 4014-2013 for the plan's GOST ISO 4014-2014**
- The plan text (and L14) named GOST ISO 4014-2014, and ISO 4014:2022 first. The owner ruled on 2026-10-20 for ГОСТ Р ИСО 4014-2013 (IDT ISO 4014:2011), recorded in `05-OWNER-READS.md` and the L14 amendment. Source strings, `Source.document()` and the `ADOPTED_ISO` key follow that ruling, in ASCII.

**2. [Owner ruling] Tip angle 45 degrees, not 30**
- The plan's control "cutting at 45 degrees where 30 is the model" is inverted by R2: the model is 45 (stated model, `TIP_ANGLE_DEG`). The control builds a 30 degree cone where 45 is the model.

### Plan claims that did not hold as written (surfaced, not approximated)

**3. The whole-part gate alone does not pass all three controls.** The plan says the three controls "pass the whole-part gate alone (asserted)". Measured on the shipped bolts, the whole-part gate at `T_GATE` flags 4 of the 6 (control, bolt) pairs and misses two, both on M10 x 200: the dropped ring (6.6e-05) and the 30 degree cone (8.1e-05), against `T_GATE` 9e-05. It flags the skipped cut and the dropped ring on M6 x 60 and the skipped cut on M10 x 200. The 05-02 probe measured rods and read five of six flagged; the bolt differs because its thread is 26 of 200 mm. I asserted what is true (`test_the_whole_part_gate_alone_misses_two_of_the_six_controls_on_the_long_bolt`), not the plan's wording. The load-bearing requirement holds: the piece check refuses all six.

**4. "One float longer gets the cone" holds for `derive` and not for the kernel.** `tip_cone_fits` is `t > tip_cone_length(pitch, 45)`, one decision shared by the builder, the closed form and `derive`, as the plan says; `derive` is tested at the float. The kernel's intersect raises `Standard_Failure` for `t` from that length up to about 1e-9 mm above it (it cuts correctly at 1e-6 above): the cone grazes the crest at the thread's far end. The build answers with a 422 `build_error`, never a wrong part. Filed as `docs/tech_debt/active/2026-10-20-tip-cone-degenerate-boolean-at-the-cone-length.md` (nice, owner ruling needed to fold the sliver). The kernel-side test uses `cone + 1e-3`.

**5. The 90 s `make verify` threshold was already crossed.** The plan says to stop if `make verify` grows past 90 s. 05-11's summary recorded 113.05 s before this plan; it now reads 101.65 s with the sweep (host load varies). I did not trim the sweep. If the owner wants verify under 90 s, the plan's own option applies: fewer sizes in verify and the rest under the `grid` marker. Surfaced here for a decision.

### Auto-fixed Issues

**6. [Rule 3 - Blocking] Existing tests read the old volume and notes.** The default and ISO 4014-shaped volumes now include the tip cone and ring, and every ISO 4017 row now has a second note. Updated `tests/test_calc.py`, `tests/test_api.py`, `tests/test_solid.py` to `bolt_end_closed_volume` and to `NO_FILLET_NOTE`; the wrench-note tests ignore the new note. Commit 8454888.

**7. [Rule 3 - Blocking] Lint and type.** RUF002/RUF003 on Cyrillic in comments (written in ASCII), SIM300 and a mypy `object` narrowing in tests. Commits 24528c6, 8454888.

### Process notes

- No separate RED commits: the pre-commit hook runs `make verify`, so a failing test cannot land (as in 05-11).
- `assemble` is unchanged and builds the bolt without the ring; `add_fillet` fuses it (the plan said `assemble` fuses the ring). This lets the ring's added volume be measured from volumes before and after.
- `STANDING_WARNING` still reads "plain-cut thread ends, no tip chamfer or under-head fillet" and is now stale for the bolt; plan 05-13 Task 3 rewrites it and its three literal assertions, so it is not touched here.

## Known Stubs

None.

## Threat Flags

None. T-05-26 (end cuts diluted in the whole-part gate): mitigated by the piece checks and the six controls. T-05-27 (extra precise volumes per build): measured above (+0.4 to +0.6 s), recorded.

## Authentication gates

None. (The prior executor's `~/Downloads` read refusal was resolved by the owner's copy to `/Users/half/gsd-sources/`.)

## Verification

`make verify` (ruff, mypy --strict, import-boundary contracts, unfinished-work scan, pytest): final result line `3144 passed in 101.65s (0:01:41)`, total coverage 98.02% against the 96.0% requirement; the same gate passed in the pre-commit hook of each of the three task commits. `make lint-imports`: 9 kept, 0 broken.

Debt filed: `docs/tech_debt/active/2026-10-20-tip-cone-degenerate-boolean-at-the-cone-length.md` (nice).

## Self-Check: PASSED

- FOUND: tests/data/owner/iso4014_fillets.tsv, src/screw/solid/bolt.py (`def tip_cut(`, `def fillet_ring(`, no `.fillet(`), src/screw/calc/thread.py (`FILLET_R:`), src/screw/tables/iso4014.py (`FILLETS`)
- FOUND: `piece_refusal(` twice in src/screw/solid/__init__.py's bolt branch
- FOUND: commits 24528c6, 8454888, 8b35dfc (ancestors of HEAD)
