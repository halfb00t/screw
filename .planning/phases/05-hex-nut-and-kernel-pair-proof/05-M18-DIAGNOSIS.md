# Phase 5: M18 control diagnosis (D-08), protocol

This file is pre-registered: it lands on `main` in its own PR before the probe runs (02 D-19 precedent: `make pr.land` squashes, so the order is only visible across PRs), and `bench/m18_probe.py` refuses any run while this file differs from `origin/main`'s. Everything below is written before any reading exists.

## Question

Is the M18 control that read 0 solids at theta -2pi/3 (right hand) and +2pi/3 (left hand) in every same-hand cell of `2026-10-08-a-pair`, at every clearance from -0.05 to 0.20 mm, reproducible on this kernel, and is it local to that pose?

This is a diagnosis, not a campaign (D-08). It reads 36 values and writes down what they say. It changes no rule: M18 stays `inconclusive` on both hands until a later pre-registered campaign proves it (L11 revision direction).

## Environment

- **Host:** whatever the run prints from `bench.machine_facts()`, recorded in the header line of `bench/results/phase-05/m18-diagnosis.jsonl` together with the UTC time of the run. The probe is non-decisive whatever the load: two `bench.quiet.read_now()` readings, one before the first child starts (labelled "before") and one after the last child ends (labelled "after, includes the run's own load"), are printed for the record and decide nothing.
- **Python:** 3.12.
- **Kernel pair:** cadquery 2.8.0 with cadquery-ocp 7.9.3.1.1, as pinned in `requirements.txt` (L06). A different pair makes this a different measurement; the header prints the installed versions.
- **HEAD of the run:** printed in the header line (`git rev-parse HEAD`), with the protocol blob taken from `origin/main`.

## Method

The bodies are the recorded ones and nothing else. The cell is the recorded M18 cell of `2026-10-08-a-pair`: d 18.0, pitch 2.5, m 15.8 (the recorded height, UNVERIFIED preview value: the cell is the recorded cell, not the product's), K = 3. Per reading the probe calls `bench.thread_spike.pair.rod_piece(18.0, 2.5, 15.8, hand, 3)` and `pair.nut(18.0, 2.5, 15.8, c, hand, 3)`, places the nut with `pair.place` at the reading's theta and a half-pitch offset (the control pose), runs `pair.check_cover`, intersects with `BRepAlgoAPI_Common` the way `pair.common` does (options per reading, below), parks the boolean and its filler in `pair._KEEP`, and reads the precise volume. Rod and nut have the same hand.

**Readings: 36, fixed now, no others.** The failing control is the half-pitch control at theta -2pi/3 on the right hand and +2pi/3 on the left hand (offset 0.5 pitches).

- **P1, determinism (10).** The failing control at c = 0.10 mm, five times per hand, each reading in a fresh child process.
- **P2, locality (16).** The same control at the failing theta plus delta, c = 0.10 mm, once per hand, delta in radians: -0.1, -0.01, -0.001, -0.0001, +0.0001, +0.001, +0.01, +0.1.
- **P3, sensitivity cell (2).** The failing control pose of the c = -0.05 mm cell, once per hand.
- **P4a, fuzzy value (2).** The failing control at c = 0.10 mm with `SetFuzzyValue(1e-4)`, once per hand. 1e-4 mm is `helical.SEWING_TOLERANCE`, the builder's own tolerance, so no number is invented for the probe.
- **P4b, operands swapped (2).** The failing control at c = 0.10 mm with the operands swapped (`SetArguments` the placed nut, `SetTools` the rod), once per hand.
- **H, harness controls (4).** The other two controls of the c = 0.10 mm cell, once each per hand (right hand: theta 0 and +2pi/3; left hand: theta -2pi/3 and 0). Their closed form is `verdict.closed_control` of that cell: 336.6316 mm3 (at c = 0.10 mm; the recorded readings of these poses were 336.63 mm3).

**Deadline.** Each child may run 130 s. That is 4 x 30.96 s, the slowest M18 k = 3 boolean in `2026-10-08-a-pair.jsonl`, rounded up to a multiple of 10 s. The 600 s of `PAIR_TIMEOUT_S` (debt item IN-02) is a whole-cell figure, six booleans plus two builds, and is not reused: a reading here is one boolean plus its two builds, and the probe asks a bounded question, so a child over 130 s is a result ("timeout"), not a reason to wait. A child over its deadline is killed and recorded `timeout`. At most four children run at once. No reading is retried.

**Output.** One JSON line per reading in `bench/results/phase-05/m18-diagnosis.jsonl`, after a header line (run id, HEAD, protocol blob, host facts, load readings), and an entry in `bench/RESULTS.md` titled `## M18 control diagnosis (Phase 5, D-08)`. The probe refuses to overwrite an existing output file.

## Predictions

Stated before data, each with what it would mean.

- **H1.** Every P1 reading, on each hand, reads 0 solids. Meaning: the recorded empty is reproducible on this kernel. Any non-empty P1 reading means the recorded empty is not reproducible.
- **H2.** The P2 readings at |delta| >= 0.01 rad read non-empty and within `PAIR_BAND` (1e-3, relative) of the closed form. Meaning: the failure is local to the pose. A non-empty reading at 1e-4 or 1e-3 rad is not predicted either way.
- **H3.** Both P3 readings read 0 solids, as recorded.
- **H4.** P4a and P4b read as the recorded empty. Meaning: the empty is not an artefact of the boolean's tolerance or of operand order. A non-empty reading in either means it is.
- **H.** The four harness controls read non-empty within `PAIR_BAND` of 336.6316 mm3. If any does not, the probe is void on this host and says so.

## Escape clause

Done is the entry written, whatever it says. Nothing is re-run toward an outcome. No verdict rule, pose, band, body, K or constant changes (L11 revision direction, 02 D-17). The M18 nut ships and `screw pair` reads `inconclusive` for it until a later pre-registered campaign proves it. A reading that fails or times out is recorded as such.

## Results

Results are written in `bench/RESULTS.md`, never in this file: the run guard compares this file with `origin/main`'s.
