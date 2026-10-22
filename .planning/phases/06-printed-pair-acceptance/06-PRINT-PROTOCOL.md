# Phase 6: Printed pair acceptance - protocol

This file is pre-registered: everything above the `## Results` heading lands on `main` in PR A before the first print of run 1 (SC1); nothing above it changes once a record row exists, and a change after landing is a new PR that visibly post-dates this text.

## Question

Three questions and one acceptance, all on one fixed print profile (see `## Print profile`).

1. **The default (PAIR-02).** What is the smallest ladder step from which a product nut threads onto a product bolt by hand, at every size M6, M8, M10 and M12? That step is the first and only `clearance` default of the product.
2. **A bought nut (PAIR-06).** Does a nominal printed bolt bind in a bought steel nut? The answer decides whether the bolt-side `undersize` follow-up (PAIR-07) is promoted.
3. **The printability threshold (INFO-04).** What is the smallest coarse size of M3, M4 and M5 that prints and threads at that default? Its `d` and coarse pitch are the two constants below which a part warns.

**Acceptance (PAIR-05, D-16).** After the default ships, one fresh M8 pair made through the page threads together by hand. It is not a sample of either run and does not count toward any cell.

## Owner rulings

Taken by the owner on 2026-10-22, before any Phase 6 record row existed, and recorded in `06-OWNER-RULINGS.md` (`Ruled: 2026-10-22`). R1 to R5 shape the method and are quoted here; R6 to R8 are code rulings and stay in that file.

- R1 run-2 pre-registration: R1 a - run 2 is pre-registered in PR A with run 1 (its clearance defined as the value the run-1 rule returns; the owner's run-2 predictions written now).
- R2 bolts for the bought nuts: R2 a - 12 more bolts printed from the same matrix STLs, same batch and profile, used only in the bought nuts.
- R3 order of one bolt's five nuts: R3 a - loosest to tightest (0.25, 0.2, 0.15, 0.1, 0.05 mm), order recorded per sample.
- R4 plate rule: R4 a - sample k of every cell is printed on plate set k (three plate sets); plate recorded per part.
- R5 part that fails to print: R5 b - the failed part alone is reprinted from the same STL and profile before any part of its cell is fit-tested, and its note says `reprinted: print failure` (narrows the no-reprint wording of D-08: owner ruling).

## Print profile

Every part of this test uses this one profile, and the default it sets holds for this profile, which the decision entry will say (D-06). The owner types the lines marked below.

- Printer: OWNER-SLOT make and model
- Nozzle: 0.4 mm (D-06)
- Material: OWNER-SLOT type, brand, colour, lot if known
- Layer height: OWNER-SLOT mm
- Slicer and profile: OWNER-SLOT slicer and version, profile name, every setting changed from it
- Orientation: nut on its face, bolt head-down (D-06)
- Bought nuts: OWNER-SLOT ISO 4032 or DIN 934, steel, brand or source, plating, property class if marked; 3 each of M6, M8, M10, M12

## Method

### Run 1: the clearance ladder (PAIR-02) and the bought nuts (PAIR-06)

The parts are the product's own fine exports, so the test checks exactly what a user downloads (D-02). `python -m bench.print_matrix export run-1 -o bench/results/phase-06/stl/run-1` writes 24 STL files: the bolts iso4017:M6x12, iso4017:M8x16, iso4017:M10x20 and iso4017:M12x25, and the nuts iso4032:M6, iso4032:M8, iso4032:M10 and iso4032:M12, each at the clearances 0.05, 0.10, 0.15, 0.20 and 0.25 mm. Its manifest (`name`, `bytes`, `sha256`) is committed before the first print. STLs are never committed; the manifests are.

- Each nut STL is printed 3 times (60 nuts) and each bolt STL 3 times (12 bolts).
- R2: 12 more bolts are printed from the same four bolt STLs, same batch and profile, and are used only in the bought nuts. PAIR-06 takes 3 samples per size in the bought nuts of `## Print profile`.
- R4: sample k of every cell (size, clearance) is printed on plate set k, so there are three plate sets. The owner's plate id is recorded in `plate`.
- R3: the five nuts of one bolt are fitted loosest to tightest, in this order: 0.25, 0.20, 0.15, 0.10, 0.05 mm. The position a nut actually took is recorded in `order` (1 to 5).
- R5: a part that fails to print is reprinted alone from the same STL and the same profile, before any part of its cell is fit-tested. Its note says `reprinted: print failure`. A nut that prints and then binds is never reprinted; that is a result.

The fit test (D-05), for every sample, in this order:

1. Hold the bolt by its head and offer the nut to the thread tip by fingers.
2. Turn the nut by fingers only, from first engagement, towards the bolt's head.
3. The sample passes when the nut turns all the way to the bolt's head and back off again, with no tool, and with no stripped or shaved thread.
4. Anything else is a bind: a nut that will not start, stops part-way, needs a tool, or shaves or strips the thread. A bind is recorded with the turns, counted from first engagement, at which it stopped.
5. A pass that is slack enough to wobble on the thread is still a pass and is noted `loose`.

### Run 2: the printability threshold (INFO-04)

Run 2 happens after the default ships and only then. `python -m bench.print_matrix export run-2 -o bench/results/phase-06/stl/run-2` writes the bolts iso4017:M3x6, iso4017:M4x8 and iso4017:M5x10 and the nuts iso4032:M3, iso4032:M4 and iso4032:M5, with no clearance argument, so the nuts can only be built at the shipped default (R1 a: that clearance is defined as the value the run-1 rule returns). Each size is printed 3 samples: 9 bolts and 9 nuts, on the same profile, with the plate recorded in `plate`, fitted under the same pass rule. Its manifest is committed before the first print.

### Acceptance (D-16)

After the default ships, one fresh M8 pair is made through the page: the ISO 4017 M8 x 16 preset, its Matching nut link, `clearance` left at its default, both parts downloaded. Both downloads are compared byte for byte with the files of `python -m bench.print_matrix export acceptance`. Before the pair is printed, the kernel verdict of `screw pair nut --d 8 --pitch 1.25 --s 13 --m 6.8` must read proven. The two printed parts must pass the fit test above.

## Records

The owner fills three tab-separated files under `bench/results/phase-06/`, committed blank with every key cell written: `bench/results/phase-06/print-run-1.tsv` (60 rows), `bench/results/phase-06/bought-nut.tsv` (12 rows) and `bench/results/phase-06/print-run-2.tsv` (9 rows). The key columns are written; the owner fills the rest.

Run 1, `print-run-1.tsv`, columns in this order:

- `size`: the size label, M6, M8, M10 or M12 (written).
- `clearance`: the nut's clearance in mm, exactly as written (0.05 is written `0.05`, 0.10 is written `0.1`, and so on).
- `sample`: 1, 2 or 3 (written).
- `plate`: the owner's plate id; sample k is on plate set k (R4).
- `order`: 1 to 5, the position this nut took on its bolt (R3). The five orders of one bolt are 1 to 5 once each.
- `result`: exactly `pass` or `bind`.
- `turns`: `-` on a pass; on a bind, the turns from first engagement at which the nut stopped, as a decimal such as `2.5`.
- `note`: `-`, or `loose` on a loose pass, or short text without tabs (a failed print is `reprinted: print failure`, R5).

Bought nuts, `bought-nut.tsv`: `size`, `sample`, `result`, `turns`, `note`, filled as above.

Run 2, `print-run-2.tsv`: `size`, `sample`, `plate`, `result`, `turns`, `note`, filled as above.

The reader (`bench/print_rules.py`) refuses any other spelling: a blank or padded cell, a `pass` with turns, a bind without turns, `loose` on a bind, a repeated, missing or unregistered row, an `order` that is not a permutation of 1 to 5 for a bolt. It names the line. The owner fixes a refused line; Claude never edits a result cell. Each record's sha256 is pinned after the owner's last edit of it, as `RUN_1_SHA256`, `BOUGHT_SHA256` and `RUN_2_SHA256` in `bench/print_rules.py` (the only lines of that module allowed to change after this protocol lands) and in `bench/RESULTS.md`; a record is never edited after its pin.

## Rules

Each rule is stated in words and applied by the named function of `bench/print_rules.py` as it is at the commit PR A lands; its controls are in `tests/test_print_rules.py`.

The coarse pitches the rules read (ISO 262, mm):

| Size | d | P |
|------|---|---|
| M3 | 3 | 0.50 |
| M4 | 4 | 0.70 |
| M5 | 5 | 0.80 |
| M6 | 6 | 1.00 |
| M8 | 8 | 1.25 |
| M10 | 10 | 1.50 |
| M12 | 12 | 1.75 |

- **Pass (D-05).** A sample passes or binds as the fit test says. A cell, a (size, clearance) pair, passes when its 3 samples all pass; two of three is not a pass.
- **Default (D-07), `default_from`.** The default is the smallest ladder step from which every cell of every size passes: that step and every larger step pass at all four sizes. The ladder is 0.05, 0.10, 0.15, 0.20, 0.25 mm. The default is whatever this function returns for the pinned record; the owner's 0.10 mm is a prediction and is never an input.
- **No default (D-08).** If no step qualifies, or if any size has a passing cell below a non-passing one (the record is not monotone), `default_from` returns nothing and no default ships.
- **Undersize (D-14), `promotes_undersize`.** If some size binds in 2 or 3 of its 3 bought-nut samples, PAIR-07 is promoted to a v1.x requirement. Otherwise the record says it is not needed.
- **Threshold (D-10), `threshold_from`.** The smallest of M3, M4 and M5 that passes 3/3 together with every larger one of the three. If there is none the threshold is M6, whose cell at the default passed 3/3 by the default rule.
- **Constants (D-11).** `d_min` and `P_min` are the `d` and the coarse pitch of that size. A part warns when `pitch < P_min` or `d < d_min`, strictly. The part builds and every number is kept (D-13); nothing is capped and nothing is refused.
- **Outside the measured range (D-09, R6).** The default clearance warns, on the bolt-and-nut info documents of the UI, the API and the CLI, when `d < 6.0` or `d > 12.0`, the range of `d` the matrix spans (R6, `06-OWNER-RULINGS.md`). The warning does not change a number.

## Predictions

A prediction is not a target: no step, size, rule or sample was chosen to make one come true, and a prediction that fails is a result.

- P1 (owner, D-01): the default reads 0.10 mm.
- P2: OWNER-SLOT which steps pass 3/3 at each size, or which bind
- P3: OWNER-SLOT PAIR-07 promoted or not needed
- P4: OWNER-SLOT the run-2 threshold size (M3, M4, M5 or M6)

Prior evidence (never an input): the research priors of `.planning/research/PITFALLS.md` C5 and C8. Forum and blog figures, rated LOW in that research, put a printed radial clearance at 0.10 to 0.20 mm with a 10x spread between two reports and "trial and error is the only way"; the vendor and blog floor is "M5 or larger" and one SLS paper says "greater than M6". Each is a prior only and none was used to choose a step, a size or a rule.

## Escape clause

- **No default (D-08).** If `default_from` returns nothing, no default ships and `clearance` stays required (L15 D-01). The record is committed as written. Claude stops and brings the owner options: extend the ladder above 0.25 mm, a reprint rule, a profile change, each a new pre-registered run. No part is reprinted inside run 1 beyond R5.
- **Undersize (D-14).** Both outcomes are written before the data: some size binds in 2 or 3 of its 3 bought-nut samples, and PAIR-07 is promoted to a v1.x requirement; or no size does, and the record says it is not needed.
- **Run 2.** Run 2 always yields a threshold. If M5 does not pass 3/3, the threshold is M6.
- **Acceptance (D-16).** A kernel verdict other than proven for the shipped default, or a byte mismatch between the page download and the CLI export, or an acceptance pair that binds, stops the phase for the owner. No rule, constant or table changes to turn any of them.

Nothing is tuned toward a pass: no ladder step, size, sample count, pass rule, rule or record changes after any record row exists, and a change after landing is a new PR that visibly post-dates this protocol.

## Results

Results are written in `bench/RESULTS.md` (the entries that plans 06-05, 06-08 and 06-10 add), never in this file.
