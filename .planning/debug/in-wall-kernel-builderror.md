---
status: diagnosed
trigger: "docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md — 20 parts inside the L20 walls pass validation and then fail with BuildError; 11 of them fail the required bounds tier on run 41052312369 (PR #26, head 9b880db). Find the root cause, then propose a kernel fix or a measured guard (a 422 at the parameter boundary). Stop for the owner before applying either."
created: 2026-10-30
updated: 2026-10-30T20:15+06:00
goal: find_root_cause_then_propose
---

# Debug: in-wall parts the kernel refuses

## Symptoms

- **Expected:** every part the parameter model admits (inside the L20 walls, admitted by the
  cost model) either builds at each artifact it is admitted at, or gets a 422 at the parameter
  boundary that names the fields to change (L02). It should never be accepted and then fail.
- **Actual:** the build raises, the reading is `refused` with `BuildError`, and the API returns a
  build failure for an input it called valid.
- **Errors:** `BuildError`. The exact kernel message is in the explore records
  (`bench/results/phase-07/explore-40646117094/`) and in the bounds records of run 41052312369
  (artifact `bounds-records-*`, kept to 2026-11-06). A local copy of the earlier single-job run
  41042483745 is at
  `/private/tmp/claude-501/-Users-half-git-halfb00t-screw/6a65c4eb-e38a-473f-9bb1-ae1319e48ab6/scratchpad/0718/bounds-41042483745/bounds-records/bounds-records.jsonl`.
- **Timeline:** first seen in explore run 40646117094 (plan 07-09), and filed 2026-10-29. Seen
  again on every runner reading since: Runs II bound and gzip (before G31 excluded the two nuts
  there), and the 07-18 bounds tier runs 41042483745 and 41052312369.
- **Reproduction:** build any of the parts below at the given artifact through the solid module,
  or through the API or CLI. Point labels encode the fields: `bolt-d<d>-p<pitch>-n<turns>-<hand>`
  with t = L = turns x pitch, and `nut-d<d>-p<pitch>-m<m/d>d-s<s/d>d-c<clearance>-<hand>`. The
  exact fields of each point are in `tests/data/oper_boundary.json` and
  `bench/points/explore.json`.
  - Tier failures, run 41052312369:
    - stl-preview: `bolt-d3-p0.1-n3-right`, `nut-d30-p0.35-m0.8d-s4d-c0.15-right`,
      `nut-d30-p0.35-m0.8d-s1.6d-c0.15-left`
    - stl-fine: `bolt-d3-p0.1-n3-right`
    - step: `bolt-d100-p0.35-n3-right`, `bolt-d100-p0.1-n3-right`, `bolt-d3-p0.1-n3-right`,
      `bolt-d300-p0.35-n3-left`, `bolt-d300-p1-n3-right`, `bolt-d300-p0.1-n3-right`,
      `bolt-d300-p0.1-n3-left`
  - The full 20 (from explore, all three artifacts): see the debt item.
  - Hand matters. The left twins of `bolt-d300-p1-n3-right`, `bolt-d3-p0.1-n3-right` and
    `bolt-d100-p0.1-n3-right` read ok at all three artifacts. But it is not right-hand only: 5 of
    the 17 refused bolts are left-hand.
  - The platform: the runner is linux/amd64, in the production image. Local is macOS arm64, where
    the result may differ. Check both, and say which you checked.

## Constraints (owner, binding)

- Diagnose and propose only. Do NOT apply a kernel fix or a guard: stop with a checkpoint and
  give options, a recommendation and the evidence.
- A guard must be measured: which parts it refuses, computed by code, plus the catalogue impact
  (294 bolt and 14 nut rows must stay admitted, under B-01).
- Never touch .planning/state.json, .planning/HANDOFF.json, .planning/ui-reviews/,
  .planning/phases/05-*/.continue-here.md or .planning/phases/06.1-*/.gitkeep. No git stash.
  No --no-verify. No uv (the venv is pip-managed at .venv).
- L02: never print a figure that is not computed by committed code or read from a record.
- Read CLAUDE.md and docs/CODING_VALUES.md. The kernel is src/screw/solid; the walls are in
  src/screw/calc/thread.py. Also see the related debt item
  docs/tech_debt/active/2026-10-21-nut-countersink-cutter-crosses-the-axis-at-a-coarse-pitch.md.

## Current Focus

- continuation result (2026-10-30, E23 to E32): the requested guard form does not exist. No
  wall on pitch against d holds the in-wall failure region and keeps B-01 (E30): the bolt's tip
  error grows with the turn count at a fixed d/p inside two size bands of d (0.5 to 0.85 and 1.6
  to 3.3, E27, E30), and nuts fail at isolated d/p (14 and 17, E31, E32). The best d/pitch
  candidate, d / pitch <= 20 on both kinds, refuses the 20 and the 11 tier failures and keeps the
  catalogue, and still admits refused parts on both platforms (counts in Resolution). Linux/amd64
  and macOS arm64 give the same status on every cell read on both, pieces within 9.1e-10 (bolts)
  and 4.1e-08 (nuts) (E29, E32).
- bug_class: Bohrbug per platform (deterministic for fixed inputs, E2, E3), but chaotic in its
  inputs: the outcome flips with hand, platform (E14) and the sweep's accuracy settings (E15).
- hypothesis (confirmed for diagnosis): one root cause behind all five messages. The end-cut
  booleans (the tip cone, BRepAlgoAPI Common in `bolt.tip_cut`; the lead-in countersink,
  Cut in `nut.finish`) act on the pipe-swept thread from `helical.twist`, whose surface error is
  fixed in mm or in radius (the OCCT MakePipeShell default approximation tolerance; the 14-sample
  flank spline, error ~1.42e-05 td per unit d/p), not in thread depths. At a fine pitch for its
  d these errors are 1e-3 to 4e-2 of a thread depth, and the boolean returns a wrong result while
  reporting success (a cut 1-4 % off its oracle, 23x off, invalid, empty, null, or the uncut
  body). The gates refuse every one (L02 holds). AND-gate: yes, two conditions together: (code)
  this builder's accuracy, and (config) the parameter model admits any pitch for a d (pitch has
  only gt=0, the 90-turn cap and the cost model), so no wall stops the part before the kernel.
- reasoning_checkpoint:
  hypothesis: "the 20 refusals are made by the end-cut boolean on a swept thread whose
    representation error is not small against the thread depth, at parameters the model admits
    because no wall bounds pitch against d"
  confirming_evidence:
    - "E5/E9: every bolt fails inside tip_cut, every nut at the countersink cut; bare thread and
      void are valid and within 8.05e-07 of their closed forms"
    - "E12/E14: raising the sweep's accuracy (pipe tol 1e-6, 56 samples) builds 20 of 20 through
      every product gate on macOS arm64 and linux/amd64; tol 1e-6 alone clears 13 (the 7 moderate
      tip-cone bolts, the 3 nuts, 3 of the d300 p0.35)"
    - "E13: the section spline's error grows as d/p in thread depths; the pipe's is ~fixed in mm"
    - "nocut probe: with the end cut left out, all 20 pass every remaining gate"
  falsification_test: "a failing part whose bare thread/void is invalid or off its closed form,
    or one that the accuracy change does not move at all, would refute it (none found in 20)"
  fix_rationale: "not fixing (diagnose only); options in Resolution"
  blind_spots: "the OCCT-internal reason the boolean breaks (SSI walking vs face splitting) is
    not isolated, nor why the error is piecewise constant in d (size bands, E30); the accuracy
    variant regresses 4 parts that build today (E15, E31), so it is not a monotone fix; the
    linux/amd64 grid is a 352-cell subset of the macOS grid (E29, E32); nut failures are
    isolated cells, so a grid cannot bound them"
  candidate_causes:
    - "code: end-cut boolean on the swept thread (confirmed)"
    - "code: sweep accuracy constants (contributing, confirmed by E12)"
    - "config: no parameter wall on pitch against d (contributing)"
    - "environment: platform (eliminated as cause, E3/E14/E29; it only changes which failure)"
    - "data/measurement: piece-gate noise (eliminated for 3-turn parts, E6; re-opened for
      multi-segment threads: the differenced tip piece absorbs a discrepancy that grows with
      the thread length, E24, E25, E28, so bolt-d3-p0.1-n30-left is a correct cut refused)"
  and_gate: "yes: the builder's accuracy AND the missing wall; either one alone would stop the
    accepted-then-refused path"
- next_action: owner decision (options in Resolution): a partial d/pitch wall now with the
  residual region kept as debt, kernel work now (the accuracy variant behind the same wall), or a
  band-fitted guard (not recommended). Nothing applied to src/. Scratch: iw/wgrid.py,
  iw/wall_counts.py, iw/wall_grid_check.py, iw/wg/*.jsonl.

## Evidence

- timestamp: 2026-10-30 (E1)
  checked: explore records bench/results/phase-07/explore-40646117094/*/*.jsonl (linux/amd64,
    cadquery 2.8.0, cadquery_ocp 7.9.3.1.1), every reading of the 20 labels, by the scratch
    script scratchpad/iw_records.py
  found: all 60 readings refused with BuildError; the message is the same at all three artifacts
    of a part (the build fails before export). Five message classes:
    (a) "Geometry kernel produced the wrong tip cone: ... allowed 0.03 of the piece (D-10, R11)."
        on 9 bolts: d3 p0.1 n3 right (+3.793e-02), d3 p0.1 n30 left (+3.992e-02), d3 p0.1 n30
        right (+7.914e-02), d100 p0.1 n3 right (+2.226e+01), d100 p0.1 n30 right (+2.261e+01),
        d100 p0.35 n3 right (-3.069e-02), d100 p0.35 n30 right (-3.300e-02), d300 p1 n3 right
        (+3.364e-02), d300 p1 n30 right (+3.696e-02)
    (b) "Geometry kernel produced 0 solids from the tip cut for these parameters, expected exactly
        1." on d300 p0.1 n3 left and n30 left
    (c) "Geometry kernel failed (ValueError); check d, pitch, left_hand, length, s, k,
        thread_length and head_chamfer." on d300 p0.1 n3 right and n30 right
    (d) "Geometry kernel produced an invalid solid for these parameters." on d300 p0.35, all four
        (n3/n30 x left/right)
    (e) "Geometry kernel produced the wrong lead-in countersink: the lead-in countersink is
        -6.70191e-06 mm3 [right s1.6d], -0.000118483 mm3 [left s1.6d], -6.70203e-06 mm3 [right
        s4d] where its oracle says 276.363 mm3, relative error -1.000e+00, allowed 0.03 of the
        piece (D-10, R11)." on the three nuts
  implication: there is no single BuildError. 17 bolts fail in the tip-cut stage or before (a-d),
    3 nuts in the countersink stage (e). Classes must be diagnosed separately.

- timestamp: 2026-10-30 (E2)
  checked: local copy of bounds run 41042483745 records (header: image screw:ci, x86_64, AMD EPYC
    9V45, cadquery_ocp 7.9.3.1.1), every non-ok reading
  found: exactly 11 refused readings, the same 11 (label, artifact) pairs the symptoms list for
    run 41052312369, each with the explore message to the digit (e.g. bolt-d300-p1-n3-right step
    "+3.364e-02", nut s4d right "-6.70203e-06 mm3")
  implication: on linux/amd64 the refusals are deterministic (same digits across explore and
    bounds runs, separate containers and days); a Bohrbug, not a flake.

- timestamp: 2026-10-30 (E3)
  checked: macOS arm64 local, .venv cadquery-ocp 7.9.3.1.1, scratch iw/repro.py building each of
    the 20 through screw.solid.build (clear_cache first), plus 4 left-twin controls; log
    iw/repro-macos.log
  found: all 20 refused with the linux/amd64 message; the 17 bolt messages agree to every printed
    digit; the 3 nut messages agree except the near-zero piece (-6.70118e-06 / -0.000118482 /
    -6.70116e-06 mm3 here vs -6.70191e-06 / -0.000118483 / -6.70203e-06 on the runner); all 4
    controls (bolt-d300-p1-n3-left, bolt-d3-p0.1-n3-left, bolt-d100-p0.1-n3-left,
    bolt-d300-p1-n30-left) built ok. 0.4 to 2.8 s per build.
  implication: reproduces on macOS arm64; platform is not a factor for these 20. Local
    experiments are valid evidence for the runner's failures.

- timestamp: 2026-10-30 (E4)
  checked: scratch iw/walls.py: every explore label, the parameter model (BoltParams/NutParams
    model_validate) and its statuses
  found: exactly 20 admitted labels have a non-ok reading (the 20 of the debt item). Every other
    refused explore label is outside the walls (18 by d <= 999.999, 16 by the 90-turn cap).
  implication: the 20 are the complete in-wall failure set of the explore run.

- timestamp: 2026-10-30 (E5)
  checked: scratch iw/stage.py: bolt.thread, check, then bolt.tip_cut, for d300 p0.1 and p0.35
  found: the bare thread is 1 solid, valid, volume within +8.05e-07 of closed_volume, at every
    one. The failure is inside tip_cut: d300 p0.1 right -> `bare.intersect(envelope)` returns a
    Null TopoDS_Shape and cadquery's Shape.cast raises `ValueError("Null TopoDS_Shape object")`
    (the "Geometry kernel failed (ValueError)" text); d300 p0.1 left -> the intersect returns 0
    solids; d300 p0.35 n3 both hands and n30 right -> the intersect returns 1 solid with
    isValid() False (8 faces), refused by check_structure(thread) as "invalid solid".
  implication: all 17 bolt refusals are in one operation, the tip-cone boolean (BRepAlgoAPI
    Common of the swept thread and the revolved envelope). The thread itself is fine.

- timestamp: 2026-10-30 (E6)
  checked: scratch iw/tip.py on the 4 tip-cone-volume hand pairs: bare and cut volumes at eps
    1e-6 (PRECISE_EPS) and 1e-9, and the removed piece measured directly as bare.cut(envelope)
  found (macOS arm64, rel = piece / tip_cone_volume - 1):
    d300 p1 n3: right diff +3.364e-02 (eps 1e-9 +3.344e-02), direct +3.437e-02; left diff
      +1.657e-02, direct +1.573e-02
    d3 p0.1 n3: right diff +3.793e-02, direct +3.543e-02; left diff +1.548e-02, direct +1.277e-02
    d100 p0.35 n3: right diff -3.069e-02, direct -3.286e-02; left diff -2.097e-02, direct
      -2.102e-02
    d100 p0.1 n3: right diff +2.226e+01; left diff -1.113e-02; bare.cut(envelope) is 2 solids and
      invalid at both hands (direct +2.301e+01 right, +9.165e+00 left)
  implication: H1's "measurement noise" variant is eliminated: eps 1e-9 moves the piece by at
    most 0.02 percentage points, and a directly measured piece agrees with the differenced one.
    The cut geometry itself is off the oracle by 1.3 % to 3.8 % at both hands of these sizes
    (left twins pass only because they land under T_PIECE 0.03), and grossly wrong at d100 p0.1
    right. Exact geometry is mirror-symmetric (the section is symmetric about theta = 0), so any
    hand difference is numerical.

- timestamp: 2026-10-30 (E7)
  checked: scratch iw/dev.py: radial deviation of the bare thread's 4 lateral faces from the ideal
    helicoid r = section_radius(theta - s 2 pi z / P), 61 x 61 (u, v) samples per face
  found: max |r - r_ideal| = 2.239e-03 mm (4.136e-03 thread depths) at d300 p1, 7.674e-04 mm
    (4.051e-03 td) at d100 p0.35, 8.044e-05 mm (1.486e-03 td) at d3 p0.1, 9.253e-05 mm
    (1.709e-04 td) at d10 p1; identical for the two hands of each size.
  implication: (corrected by E10/E12) the max deviation is the same at both hands, so the sweep's
    deviation from the ideal alone does not explain a hand-dependent piece. It does not show the
    boolean is innocent of the sweep's representation: E12 shows the boolean's accuracy depends
    on how the sweep is approximated.

- timestamp: 2026-10-30 (E8)
  checked: scratch iw/tol.py: BRepAlgoAPI_Common(bare, envelope) built by hand; IsDone, result
    edge/vertex tolerances and the piece, 11 sizes
  found: IsDone True and edge tolerances <= 1.61e-04 mm on every non-null result (no tolerance
    blow-up), yet the piece is off: d300 p1 right +3.364e-02, d3 p0.1 right +3.793e-02, d100
    p0.35 right -3.069e-02; d300 p0.35 right is 1 invalid solid with piece +1.589e+01; d300 p0.1
    right IsDone False and a NULL shape; d300 p0.1 left IsDone True and 0 solids. Controls at
    catalogue-like sizes: d10 p1 -3.809e-06, d20 p2.5 +6.340e-05, d2 p0.4 +1.370e-03.
  implication: the boolean reports success (IsDone True, tight tolerances) on a wrong result at
    several sizes. A post-check is the only thing that catches it, which is what the piece gate
    does.

- timestamp: 2026-10-30 (E9)
  checked: scratch iw/nutcsk.py: each nut countersink cutter cut alone from the assembled body by
    a hand-built BRepAlgoAPI_Cut, at both faces, d30 p0.35 m24 c0.15 (s48 both hands, s120 right)
    and controls d10 p0.35 m8 and m30
  found: at d30 p0.35 m24 both faces' cuts return IsDone True, a valid solid and a piece of
    -6.7e-06 to +8.6e-05 mm3 against an oracle of 276.363 mm3 (the cut removes nothing), at all
    three nuts. The void's sewn seams are not the trigger: the bottom face's cone crosses the void
    in z 2.25..2.4394 with no seam inside and still fails, while d10 p0.35's bottom crossing has a
    seam inside (z 0.7) and builds to -2.076e-06. Controls build to within 5e-06 of the oracle.
    The body itself is 1 valid solid (104 faces). The countersink inner radius is 14.9038 mm,
    positive, so this is not the 2026-10-21 negative-radius item.
  implication: the nut class is the same kind of failure as the bolt class: an OCCT boolean
    between a revolved analytic cutter (a 45 degree cone) and the pipe-swept BSpline thread
    surface that reports success and returns a wrong result (here: the input unchanged).

- timestamp: 2026-10-30 (E10)
  checked: scratch iw/classify.py: 20000 random points in the tip region (z in [0, h], r in
    [minor, crest]) classified by BRepClass3d_SolidClassifier against the bare thread and the
    tip-cut result, against the ideal predicate; points within 1e-3 thread depths of an ideal
    surface skipped
  found: d3 p0.1 n3 right: bare 5 mismatches, cut 22 (all "kernel OUT, ideal IN"), at z/h 0.78
    to 0.83 and (r - minor)/td 0.28 to 0.48, i.e. 0.3 to 0.5 thread depths inside the cone,
    where the material must stay. d300 p1 n3 right: bare 80, cut 80 (79 kernel OUT / ideal IN).
  implication: at d3 p0.1 the cut removes material well inside the cone, a localized wrong trim
    by the boolean, not a uniform surface offset. (A boolean-free cross-check by planar slices,
    iw/slices.py, was stopped after 19 CPU minutes without its first row; not used.)

- timestamp: 2026-10-30 (E11)
  checked: scratch iw/fuzzy.py: the tip-cut Common rebuilt with SetFuzzyValue 1e-6, 1e-5, 1e-4
    and with SetUseOBB, on 7 bolts
  found: no change at d300 p1, d3 p0.1, d100 p0.1, d300 p0.35, d300 p0.1 (same piece / invalid /
    NULL / 0 solids); d100 p0.35 fuzzy 1e-4 made it worse (+2.60e-01).
  implication: boolean options do not fix it. Eliminated as a fix.

- timestamp: 2026-10-30 (E12)
  checked: scratch iw/k4.py and iw/build20.py with the monkeypatch iw/variant.py (nothing in
    src/ changed): MakePipeShell.SetTolerance(tol, tol, 1e-4) in helical.twist and
    helical.SECTION_SAMPLES, then the full product build (screw.solid.build, every gate) of the
    20, macOS arm64, the four variants run concurrently (so times are inflated, not a cost
    figure)
  found: 20 of 20 build with tol 1e-6 and 56 samples; 16 of 20 with tol 1e-5 and 28 samples
    (d300 p0.1 x4 refused: wrong tip cone); 13 of 20 with tol 1e-6 and 14 samples (refused:
    d100 p0.1 x2 invalid, d300 p0.1 x4 0 solids, d300 p0.35 n3 right invalid); 7 of 20 with the
    default tolerance and 56 samples. Tip piece at tol 1e-6 + 56 samples (iw/k4.py): d300 p1
    +9.79e-06, d3 p0.1 -2.13e-06, d100 p0.35 +4.44e-06, d100 p0.1 +1.61e-05, d300 p0.35
    +2.83e-05, d300 p0.1 right +9.97e-05, left +1.03e-04 (T_PIECE 0.03).
  implication: the failures are caused by the accuracy of the swept thread's representation,
    two independent knobs: the pipe's approximation tolerance (OCCT default; tol 1e-6 alone fixes
    the 3 moderate tip-cone sizes and the 3 nuts) and the flank spline's 14 samples (needed at
    d/p >= 1000). Both together fix all 20.

- timestamp: 2026-10-30 (E13)
  checked: scratch iw/dev2.py: max |r - r_ideal| of the section wire alone (201 points per edge)
    and of the swept lateral faces (61 x 61), in thread depths, per variant
  found: section wire at 14 samples: 1.45e-04 td (d10 p1, d/p 10), 4.29e-04 (d3 p0.1, d/p 30),
    4.26e-03 (d300 p1, d/p 300), 4.26e-02 (d300 p0.1, d/p 3000): proportional to d/p, about
    1.42e-05 td per unit of d/p; at 56 samples 256 times smaller (1.61e-04 td at d/p 3000).
    Swept surface at the default tolerance and 56 samples: 1.34e-03 td at d3 p0.1 (8e-05 mm, the
    pipe's own approximation); at tol 1e-6 and 56 samples: <= 2.47e-05 td at all four sizes.
  implication: neither error scales with the thread depth. The section spline's error is a fixed
    fraction of the radius (so grows with d/p in thread depths); the pipe's error is near-fixed in
    mm (so grows as 1/p in thread depths). The booleans that cut the tip cone and the countersink
    on that surface go wrong once these reach about 1e-3 thread depths.

- timestamp: 2026-10-30 (E14)
  checked: linux/amd64, the production image screw:latest (sha256:e48008e3b111..., x86_64,
    cadquery 2.8.0, cadquery-ocp 7.9.3.1.1, built 2026-10-30 15:35 +06:00; since then no src/ or
    requirements change, and the one Dockerfile change, 83976da, is the HEALTHCHECK start-period
    and comments, so `make image` was not re-run), run under emulation on the arm64 host with the repo mounted
    read-only: iw/repro.py (logs iw/repro-linux-amd64.log) and iw/build20.py 1e-6 56
    (iw/v20-linux-amd64-1e-6-56.log)
  found: shipped code: all 20 refused, 4 controls ok; 19 messages match the runner records to the
    digit; bolt-d300-p0.1-n3-right reads "0 solids from the tip cut" here and "failed
    (ValueError)" (Null shape) on the runner. Variant tol 1e-6 + 56 samples: 20 of 20 build (bolts
    2.4 to 6.3 s, nuts 12.3 to 13.8 s, emulated).
  implication: the failure and the variant's fix hold on linux/amd64 too. The one message that
    differs between the runner and emulation is on a case whose outcome is unstable (E16).

- timestamp: 2026-10-30 (E15)
  checked: iw/fine.py and iw/matrix.py on parts outside the explore grid, all admitted by the
    model and cost.fits at HEAD, both platforms (iw/matrix-linux.log)
  found: shipped code refuses more in-wall parts than the 20: d2 p0.07 n3 right (d/p 28.6; wrong
    tip cone, admitted at all three artifacts), d20 p0.05 n3 right (wrong tip cone), d100 p0.05,
    d30 p0.01, d100 p0.01 (0 solids from the tip cut), d300 p0.02 (wrong tip cone). d6 p0.05, d6
    p0.02, d1 p0.034, d0.5 p0.017, d0.3 p0.0101 build. The variant (tol 1e-6, 56 samples) builds
    all of the refused ones except d300 p0.02 (d/p 15000), and REFUSES four parts that build today:
    d100 p0.4 n3 left and right, d250 p1 n3 left and right (0 solids from the tip cut), the same
    on macOS arm64 and linux/amd64. tol 1e-5/56 and 1e-7/56 build those four; the default
    tolerance with 56 samples refuses d100 p0.4 (wrong tip cone). Shipped-code tip pieces near the
    gate on parts that build: d100 p0.4 -2.36e-02, d250 p1 +1.15e-02 (T_PIECE 3e-02).
  implication: the 20 are a sample of a larger in-wall failure region, which has no floor because
    pitch has none (only gt=0, the 90-turn cap and the cost model). The boolean's outcome is not
    monotone in the accuracy knobs either: no single setting is shown to be better everywhere.

- timestamp: 2026-10-30 (E16)
  checked: iw/envelope.py: the shipped thread with three tip envelopes: V0 shipped; V1 the same
    cone continued 1 mm below z = 0 (no face coplanar with the end face); V2 the cone meeting
    z = 0 at minor - 0.3 td (the nut's CROSS_FRACTION), with a matching oracle
  found: V1 gives the shipped result at every size (e.g. d300 p1 +3.36e-02, d300 p0.1 right
    ValueError); V2 still fails d100 p0.1 (+1.48e+01), d300 p0.35 (invalid), d300 p0.1 (0 solids /
    ValueError), d20 p0.05 (invalid), and breaks controls (d2 p0.4 and d2 p0.07 Standard_Failure,
    d20 p2.5 -5.20e+00).
  implication: H5 (the envelope grazes the thread at the root edge / end plane) is not the cause.

- timestamp: 2026-10-30 (E17)
  checked: scratch iw/nocut.py: the 20 through screw.solid.build with the end cut left out (the
    builder's `tip_cone_fits` -> False; `end_depths` countersink depth -> 0 and the nut's closed
    form without the countersinks), every other gate unchanged; macOS arm64
  found: 20 of 20 build (bare thread / void at T_GATE, head chamfer and face chamfer pieces,
    whole part at T_GATE).
  implication: the only operation that fails is the end cut. Leaving it out (cap and warn, the
    R5 / L15 pattern `end_depths` and `tip_cone_fits` already use) builds every one at the shipped
    builder and cost.

- timestamp: 2026-10-30 (E18)
  checked: cost.fits at HEAD for the 20, and tests/data/oper_boundary.json membership
  found: 12 of the 20 are admitted at >= 1 artifact (18 label x artifact points: stl-preview 5,
    stl-fine 3, step 10, the B-01 table's counts); 8 are refused by the cost model at every
    artifact today (d100 p0.1 n30 right, d100 p0.35 n30 right, d300 p0.1 n30 both, d300 p0.35
    n30 both, d300 p1 n30 right, nut s1.6d right) and already get the over_budget 422. 11 of the
    20 are points of the boundary set (the 11 tier failures).
  implication: the user-facing defect today is 12 parts / 18 points; all 20 are inside the walls.

- timestamp: 2026-10-30 (E19)
  checked: scratch iw/sweep.py (records iw/sweep/{base,v656}-*.jsonl, diff iw/sweep_diff.py):
    every distinct explore label the parameter model takes (475: 308 catalogue rows, 167 free
    space) built through screw.solid.build with the shipped helical and with tol 1e-6 + 56
    samples, macOS arm64, 8 processes in parallel
  found: catalogue 308 of 308 ok under both. Free space: shipped 147 ok / 20 refused (exactly
    the 20); variant 167 ok, 0 regressions inside the explore set. Summed build seconds
    (contended): catalogue 559 -> 772, free space 520 -> 847.
  implication: inside the explore set the variant fixes the 20 with no regression; E15 shows
    regressions just outside it (d100 p0.4, d250 p1), so the explore set does not bound it.

- timestamp: 2026-10-30 (E20)
  checked: scratch iw/grid.py + iw/grid_table.py (records iw/grid-bolt.jsonl, iw/grid-nut.jsonl),
    shipped code, macOS arm64: bolts n3 (t = L = 3 pitch, s 1.6 d, k 0.6 d), d in {1, 2, 3, 6, 10,
    20, 30, 60, 100, 200, 300, 600} x d/p in {5 .. 1000} (16 values) x both hands, 384 cells;
    nuts (m 0.8 d, s 1.6 d, c 0.15) on the same grid, stopped at 205 of 384 rows (115 built); and
    iw/lowratio.py, bolts d in {1.5, 2, 2.5, 3, 4, 5} x d/p 12..29
  found: bolts: 82 of 384 refused, all admitted by cost.fits at >= 1 artifact. Smallest refused
    d/p per d: d1 150, d2 30 (right; 27 in lowratio), d3 30 (right; 27), d6 500, d10 500, d20 150
    (right), d30 500, d60 500, d100 300 (right), d200 300 (right), d300 300 (right), d600 1000
    (right); d1.5, d4, d5 nothing below 30. Nothing refused at d/p <= 25 anywhere. Nuts: 7 of 115
    refused, "invalid solid", at d/p 70 (d2, d3, d6 both hands) and d2 100 right; iw/nutstage.py
    puts it at `nut.assemble` (prism.cut(void) invalid; the void itself valid within 1.27e-07);
    the variant builds all three probed (iw/nutmatrix.py).
  implication: the in-wall failure region is far larger than the 20 and its frontier is not a
    clean function of d/p or of pitch (27 at d2-3, 150-500 at d6-60, 300 at d100-300). The
    failing boolean is not only the end cut: on fine-pitch nuts the prism-minus-void cut breaks
    too (same family, same fix by the variant).

- timestamp: 2026-10-30 (E21)
  checked: scratch iw/costv.py, macOS arm64, host otherwise idle (load falling from 17), cold
    build 3 repetitions (median) and export bytes, shipped vs tol 1e-6 + 56 samples
    (iw/cost-macos.log)
  found: iso4017:M6x20 build 0.83 -> 1.10 s, STEP 1303139 -> 4718318 B, fine STL 10480484 ->
    15744884 B; iso4017:M20x200 build 2.22 -> 3.41 s, STEP 5085936 -> 22867610 B, fine STL
    144602684 -> 143001484 B; iso4032:M20 build 1.37 -> 2.05 s, STEP 881196 -> 2816455 B, fine
    STL 10435684 -> 10016184 B; iso4032:M2 build 1.14 -> 1.65 s, STEP 560146 -> 1288635 B, fine
    STL 1726484 -> 1628984 B.
  implication: the variant costs 1.33x to 1.54x build time and 2.3x to 4.5x STEP bytes on
    catalogue rows. M20x200's STEP (22867610 B) would exceed B-01's step bytes budget
    (9748694.773917168 B). The cost model (L21), the budgets (B-01) and the bound tier were fitted
    on the shipped builder; the variant voids them until a full re-sweep.

- timestamp: 2026-10-30 (E22)
  checked: scratch iw/guards.py / iw/guards2.py: candidate guards (exact decimals,
    Fraction(repr)) over the 20, the explore points the model and cost.fits admit at HEAD
    (stl-preview 411, stl-fine 402, step 439 points), tests/data/oper_boundary.json (435 points),
    the catalogue (screw.tables.presets catalogue() 294 + nut_catalogue() 14) and the grid
  found:
    G1 d/pitch >= 30: refuses 20 of 20; also 35 other admitted explore labels that read ok (63
      points: stl-preview 15, stl-fine 16, step 32); 39 boundary points (11 of the 20 + 28
      others); catalogue 0 of 294 / 0 of 14 refused. Misses refusals at d/p 27 to 29.99998
      (lowratio d2/d2.5/d3 right; probe d2 p0.07 right; grid d2 at 29.99998 right).
    G2 pitch < 0.4 or d/pitch >= 300: refuses 20 of 20; 45 other ok labels (113 points: 38, 36,
      39); 59 boundary points (11 + 48); catalogue 0 / 0 refused. Misses grid d200 p0.666667 right
      (d/p 299.99985).
    G3 d/pitch >= 20: refuses 20 of 20; 53 other ok labels (104 points: 32, 25, 47); 53 boundary
      points (11 + 42); catalogue 0 / 0 refused. Misses no refusal found (grid bolts 82 of 82,
      grid nuts 7 of 7, lowratio, every off-grid probe); refuses 206 of 302 ok bolt grid cells
      and 63 of 108 ok nut grid cells.
    Catalogue: max d/p 8.0 for both kinds, min pitch 0.4.
  implication: any (d, pitch) guard keeps B-01 (all 294 + 14 rows). A guard fitted to the 20
    (G1) does not hold the region; one that holds every local refusal (G3) also refuses 53 labels
    that build today. None is a measured wall on linux/amd64 yet.

- timestamp: 2026-10-30 (E23)
  checked: scratch iw/wgrid.py (wraps the `piece_refusal` and `volume_check` that screw.solid
    imports, records every relative error, then calls them; nothing in src/ changes), records
    iw/wg/mac-bolt-{n3,n30,n3s}-*.jsonl, summary iw/wg_table.py; macOS arm64, shipped code. Bolts
    d in {0.3, 0.5, 0.8, 1, 1.2, 1.5, 1.8, 2, 2.2, 2.5, 2.8, 3, 3.5, 4, 4.5, 5, 6, 8, 10, 12, 16,
    20, 24, 30, 42, 60, 100, 150, 200, 300, 450, 600, 999.999} x d/p in {5, 8, 10, 12, 14, 15, ...,
    28 (step 1), 30} x both hands x n3 (t = L = 3 p), n30 (t = L = 30 p), n3s (t = 3 p, length
    t + d: a shank); pitch = d / ratio rounded UP to 6 figures so the exact d/p is at most the
    ratio; s 1.6 d (at most 1000), k 0.6 d; a part cost.fits admits at no artifact is not built
  found: n3 1302 ok / 18 refused, all "wrong tip cone" at d/p 27 to 30, right hand, d 1.8 to 3;
    n3s the same 18 (the shank fuse changes nothing; fillet piece <= 1e-4); n30 1097 ok / 134
    refused / 89 not admitted: refused from d/p 15 (d 1.8, 2, 2.2, 2.5, 2.8, 3 right) and from
    d/p 23 at d 0.5 and 0.8. The differenced tip piece is a function of d/p alone at small d (d2
    and d3 agree to 7 digits: +0.0171095 at d/p 20, +0.0307747 at 27). Largest piece per d/p over
    all d, n3: 5 +0.0014, 8 +0.0031, 10 +0.0046, 15 +0.0099, 20 +0.0171, 25 +0.0264, 27 +0.0308,
    30 +0.0379 (about 4.3e-5 (d/p)^2, right hand; left about 0.4 of it); n30: 5 +0.0072, 8 +0.0140,
    10 +0.0182, 15 +0.0301, 20 +0.0442.
  implication: at 3 turns the bolt frontier is d/p 27 (right hand, d 1.8 to 3) and smooth in d/p;
    at 30 turns it is d/p 15. The number of turns is a third variable a d/pitch wall does not see.

- timestamp: 2026-10-30 (E24)
  checked: scratch iw/tip.py (bare thread, Common with the tip envelope, the removed piece
    measured directly as bare.cut(envelope), eps 1e-6 and 1e-9), macOS arm64: d2 p0.25 (d/p 8)
    right at n3, n30, n90; d2 p0.4 (M2 coarse) n90 right; the n30 members of the 20 (logs
    iw/tip-turns.log, iw/tip-n30-of-20.log); and iw/wgrid.py bolt n90 d2 d/p 5, 8
  found: d2 p0.25 right: the directly measured piece is +2.265e-03 at n3, n30 and n90; the
    differenced piece (what the gate reads) is +3.111e-03, +1.400e-02 and +3.967e-02. The gap
    (after is smaller than bare - piece) is 1.52e-05, 2.117e-04 and 6.748e-04 mm3: about
    2.2e-05 mm3 per sewn seam (9 seams at n30, 29 at n90), eps 1e-9 the same. d2 p0.4 n90
    right: direct +8.262e-04, differenced +2.353e-02 (0.78 of T_PIECE). Product build: d2 p0.25
    n90 right refused ("wrong tip cone", +3.967e-02), admitted today at stl-preview and stl-fine;
    left builds (+2.209e-02). The n30 members of the 20: bolt-d3-p0.1-n30-left direct +1.277e-02
    (inside T_PIECE), differenced +3.992e-02; d3 p0.1 n30 right direct +3.543e-02, differenced
    +7.914e-02; d300 p1 n30 right +3.437e-02 / +3.696e-02; d100 p0.35 n30 right -3.286e-02 /
    -3.300e-02; d100 p0.1 n30 right gross (bare.cut: 2 solids, invalid).
  implication: the tip gate fails by two mechanisms. (i) A wrong cut that grows with d/p (direct
    = differenced at 3 turns: E6). (ii) The Common result's volume drifts by a fixed amount per
    sewn 3-turn segment, which the differenced piece absorbs, so the error grows with the turns
    at a fixed d/p; the whole thread stays inside T_GATE. E6 eliminated H1-noise for 3-turn parts
    only; for multi-segment threads a correct cut is refused (bolt-d3-p0.1-n30-left is one of the
    20). A wall in d and pitch alone cannot hold (ii) and keep B-01: d2 p0.25 n90 is refused at
    d/p 8, the d/p of the catalogue's M16 and M20 rows.

- timestamp: 2026-10-30 (E25)
  checked: scratch iw/seam.py (log iw/seam-macos.log), macOS arm64: the same thread built as the
    shipped sewn 3-turn segments and as one unsewn twist of the whole length, then the shipped
    tip Common, differenced vs direct piece; d2 p0.25 n90 and n30 right, d2 p0.4 n90 right, d3
    p0.1 n30 left
  found: one twist: direct piece -5.642e-05 / +1.917e-05 / -3.348e-05 / +8.634e-04, differenced
    -3.588e-01 / -5.803e-03 / -2.607e-01 / -1.662e-02; sewn: direct +2.265e-03 / +2.265e-03 /
    +8.262e-04 / +1.277e-02, differenced +3.967e-02 / +1.400e-02 / +2.353e-02 / +3.992e-02.
  implication: the drift is not made by the seams: the Common changes the volume of the whole
    long solid, in proportion to its length, in both constructions (worse unsewn). Corrects E24's
    "per sewn seam" to "per 3-turn segment of the sewn thread". The cut itself is accurate.

- timestamp: 2026-10-30 (E26)
  checked: scratch iw/wcat.py (records iw/wg/mac-cat-*.jsonl), macOS arm64: every catalogue row
    (294 bolts, 14 nuts) built with the piece and volume errors recorded
  found: 308 of 308 ok. Largest tip piece: iso4017:M3x30 +0.01964 (60 turns), M3x25 +0.01792
    (50), M2.5x25 +0.01667 (55.6), M2x20 +0.01433 (50); per d the largest is 0.0143 to 0.0196 at
    d 2 to 3 and at most 0.00111 at every d from 3.5 to 20 (iso4017:M20x200, 80 turns, d/p 8:
    +0.00111). Fillet ring at most -0.00243 (iso4014:M3x30), countersink at most +0.00104
    (iso4032:M2.5), face chamfer at most 1.1e-04, whole-part volume at most 2.07e-05.
  implication: the catalogue's M2 to M3 rows already sit at 0.48 to 0.65 of T_PIECE; every other
    row under 0.04 of it.

- timestamp: 2026-10-30 (E27)
  checked: scratch iw/wgrid.py bolt n60 and n90 (records iw/wg/mac-long-*.jsonl), macOS arm64:
    d in {0.3, 0.5, 0.8, 1, 1.2, 1.5, 1.8, 2, 2.2, 2.5, 2.8, 3, 3.5, 4, 5, 6, 8, 10, 12, 16, 20,
    30, 60, 100} x d/p in {3, 4, 5, 6, 7, 8, 10, 12} x both hands; and bolt n80 at d/p 8 for d 2,
    2.5, 3 (iw/wg/mac-pair-n80.jsonl)
  found: refused only at d 1.8 to 3 (right hand from d/p 7 at n90 and from 10 at n60; left from 12
    at n90) and d 0.5 / 0.8 at n90 d/p 12 right. Tip piece in that band, right hand, n90: d/p 3
    +0.0142, 4 +0.0192, 5 +0.0235, 6 +0.0291, 7 +0.0342 (refused), 8 +0.0397 (refused); n60: 5
    +0.0156, 6 +0.0196, 8 +0.0272, 10 +0.0318 (refused). The six d of the band give the same
    digits; so do d 0.5 and 0.8, d 1 to 1.5, d 3.5 to 12, d 16 to 24 (E23 too): the error is
    piecewise constant in d at a fixed d/p and turn count, and the band d 1.8 to 3 is the largest
    at every d/p and turn count measured. d2 p0.25 n80 right (also d2.5 p0.3125 and d3 p0.375)
    refused, +0.03586, admitted today at stl-preview and stl-fine; left ok +0.02031. That is the
    d/p (8) and the turn count (80) of iso4017:M20x200, which builds at +0.00111 (E26).
  implication: no wall in d/p and turns holds the region and keeps B-01: d2 p0.25 n80 and
    M20x200 have the same d/p and turns, one refused, one a catalogue row. A holding wall must
    name d's size band (d 1.8 to 3 here, which holds M2, M2.5 and M3), a kernel artefact whose
    edges are not measured (between d 1.5 and 1.8, and between 3 and 3.5).

- timestamp: 2026-10-30 (E28)
  checked: macOS arm64. (1) scratch iw/o3patch.py (hooked into iw/wgrid.py by O3=1): the tip cone
    cut on the first 3-turn segment before sewing, every product gate unchanged; d2 n90 d/p 5 and
    8, both hands (iw/wg/o3-test.jsonl). (2) iw/refpt.py (log iw/refpt-macos.log): the shipped
    bare and cut volumes with BRepGProp's reference point at z = 0, t/2, t, eps 1e-6 / 1e-9,
    IsUseSpan. (3) iw/matrix.py shipped vs tol 1e-6 + 56 samples on the turn-driven band parts
    (log iw/matrix-band-macos.log)
  found: (1) the differenced piece is unchanged: d2 p0.25 n90 right +0.039674 (refused, as
    shipped), left +0.022085, d/p 5 +0.023528 / +0.012324. (2) the reference point changes no
    digit (+3.9674e-02 at n90, +1.4001e-02 at n30); eps 1e-9 moves it to +3.8964e-02 /
    +1.4020e-02. (3) shipped refuses d2 p0.25 n90 and n80 right, d2 p0.285715 n90 right (d/p 7),
    d2 p0.133334 n30 right (d/p 15), d3 p0.15 n30 right (d/p 20); the variant builds all of them
    and d3 p0.5 n90 right (M3 coarse, 45 mm), d3 p0.15 n30 left.
  implication: the length-proportional discrepancy is not the boolean acting on far segments and
    not the volume integration: a thread sewn from fresh segments with the cut first segment has
    the same volume as the Common's result. It is a property of the shipped sweep's
    representation (the accuracy variant removes it). Cutting the tip before sewing is eliminated
    as a fix on its own; measuring the piece on the first segment before sewing (a gate change)
    is untested.

- timestamp: 2026-10-30 (E29)
  checked: linux/amd64, the production image screw:latest (sha256:e48008e3b111, built
    2026-10-30 15:35 +06:00; since then no src/ or requirements change, the one Dockerfile
    commit 83976da is the HEALTHCHECK, so `make image` was not re-run), emulated on the arm64
    host, repo mounted read-only, scratch iw/wg_linux.sh: iw/wgrid.py bolt n3 d {1, 1.5, 1.8, 2,
    2.5, 3, 3.5, 6, 20, 100, 300} x d/p {16, 17, 18, 19, 20} and d2 x d/p {21 .. 27}; n30 d {0.5,
    2, 3, 6, 20} x d/p {14, 15, 16, 18, 20}; n90 d {2, 3} x d/p {5, 6, 7, 8}; n80 d2 d/p 8; both
    hands; and iw/wcat.py on iso4017 M2x20, M2.5x25, M3x25, M3x30, M16x160, M20x200 and iso4032
    M2, M2.5 (records iw/wg/lin-*.jsonl), compared by iw/wall_grid_check.py
  found: 192 bolt cells, every status equal to macOS, largest |tip piece linux - macOS| 9.1e-10.
    n3: 123 ok, 1 refused (d2 d/p 27 right, +0.030775; d/p 26 +0.028565 ok). Refused and admitted
    by a d/p <= 20 wall: 13 (n30 d2 and d3 right at d/p 15, 16, 18, 20; n80 d2 d/p 8 right; n90
    d2 and d3 right at d/p 7 and 8). Catalogue rows: the same pieces as macOS to 6 digits
    (M3x30 +0.019641, M20x200 +0.001109).
  implication: at these sizes the kernel's result is the same on both platforms to 1e-9; the
    macOS grid stands for linux/amd64 where both were read.

- timestamp: 2026-10-30 (E30)
  checked: macOS arm64: iw/wgrid.py bolt n3 d/p 20 right over d 0.3 .. 3.5 in 0.05 steps near
    the band edges (iw/wg/mac-edges.jsonl); iw/auxr.py, helical.twist with the auxiliary helix
    radius 1 (shipped), 10 and d/2 (log iw/auxr-macos.log); iw/wall_grid_check.py over every
    grid record
  found: band edges at d/p 20: d 0.45 out / 0.5 to 0.85 in (+0.010710) / 0.9 out; d 1.55 out /
    1.6 to 3.3 in (+0.017109) / 3.35 out (-0.000008). The auxiliary radius moves no outcome and
    the piece by at most 0.0005 (d2 p0.25 n90 right +0.039674 / +0.040125 / +0.039674). Bolt
    walls d/p <= W over the grids (refused cells the wall admits, macOS / linux): W 26: 139 / 13;
    W 20: 83 / 13; W 14: 47 / 5; W 8: 15 / 5 (all at 80 to 90 turns); W 6: 0 / 0, but it refuses
    219 of the 294 catalogue bolts. The 3-turn and shank variants have no refusal at W <= 26.
  implication: the bad size bands are d 0.5 to 0.85 and 1.6 to 3.3 (at d/p 20, 3 turns), not
    the auxiliary helix. No d/pitch wall holds the bolt grid and keeps B-01.

- timestamp: 2026-10-30 (E31)
  checked: macOS arm64 unless named. (1) iw/fineiso.py (log iw/fineiso-macos.log): full-thread
    bolts d3 p0.35 L25, d2.5 p0.35 L30, d3 p0.35 L16, both hands. (2) the variant (tol 1e-6 + 56
    samples) on its four regressions, full messages (log iw/regress4-macos.log). (3) iw/nutmatrix.py
    shipped vs variant on the nut cells refused at d/p 17 and 40 (log
    iw/nutislands-variant-macos.log); iw/nutstage.py on them (log iw/nutstage-islands-macos.log)
  found: (1) d3 p0.35 L25 (71.4 turns) right refused, tip +0.032741, admitted at stl-preview and
    stl-fine; left ok +0.017732; d2.5 p0.35 L30 right refused +0.033452, left ok; d3 p0.35 L16 ok
    (+0.022114 / +0.012550). (2) bolt-d100-p0.4-n3-right, -left, bolt-d250-p1-n3-right, -left: ok
    shipped; variant "Geometry kernel produced 0 solids from the tip cut for these parameters,
    expected exactly 1." (3) the variant builds d2 p0.117648 m1.6 s3.2 c0.15 both hands, d1
    p0.0588236 m1 and d1.2 p0.0705883 m1.2 right, d2.8 p0.07 both hands; it still refuses d0.8
    p0.0470589 m0.8 s1.28 c0.15 right ("2 solids"). Stages: d2 d/p 17 right, the first
    countersink cut is invalid; left, the countersink removes nothing; d0.8 and d1 with m = d,
    prism - void is 2 solids (no countersink there: it is left out by the clearance rule).
  implication: the turn-driven bolt failures reach ordinary parts (d3 p0.35 at 25 mm) that any
    d/pitch wall keeping the catalogue admits. The variant's four regressions are at d/p 250, so
    a d/p wall of 20 would sit in front of them.

- timestamp: 2026-10-30 (E32)
  checked: nut grids, shipped code, iw/wgrid.py (summaries iw/nut_summary.py,
    iw/wall_grid_check.py nut). macOS arm64: base (m 0.8 d, s 1.6 d, c 0.15), s4 (s 4 d), c0
    (c 0), m1 (m = d), d in {0.5, 0.8, 1, 1.2, 1.5, 1.8, 2, 2.2, 2.5, 2.8, 3, 3.5, 4, 5, 6, 8,
    10, 12, 16, 20, 24, 30, 42, 60, 100, 200, 300, 600} x d/p {5, 8, 10, 12, 14 .. 20, 22, 25,
    30 .. 70 step 5} x both hands, 4928 cells (iw/wg/mac-nut-*.jsonl); base and m1 at 35 d from
    0.5 to 20 x d/p {8 .. 13} (840 cells, iw/wg/mac-nutdense-*.jsonl). linux/amd64 (screw:latest,
    emulated): base and m1, d {0.8, 1, 1.2, 2, 2.8, 3, 6, 10, 20, 30} x d/p {14 .. 17} (160),
    d {0.8, 1, 1.2, 2, 2.5, 3, 5, 6, 10, 12, 20} x d/p {8 .. 13} (264), m1 d {3.5, 9} d/p 11 (4).
    Variant and stage on the d/p 11 and 14 cells (iw/nutislands2-variant-macos.log,
    iw/nutstage-14-macos.log)
  found: refused cells at d/p <= 20 are isolated: d/p 11 (m1 d3.5 both hands, d9 right), 14
    (m1 d5 both, d12 right), 17 (d2 both hands in base, s4 and m1; m1 d0.8, d1, d1.2 right);
    nothing refused at d/p <= 10 (macOS 1056 built cells, linux 132). Every refused cell read on
    both platforms is refused on both, with the same message; nut pieces differ by at most 4.1e-08.
    Stages: prism - void invalid or 2 solids (d/p 11, 14, 17 m1 right), first countersink cut
    invalid (d2 d/p 17 right) or removing nothing (d2 d/p 17 left). The largest countersink piece
    on a built nut at d/p <= 20 is 0.0085 (0.28 of T_PIECE): the nut fails suddenly, not by an
    error that grows toward the gate. 85 of the 1467 built nut cells whose void has a sewn seam
    within 1e-4 mm of the top face (m/p near 3k - 1) are refused, against 29 of 4397 elsewhere.
    The variant builds the d/p 11 and 14 cells tried.
  implication: the nut needs its own wall if it gets one: its first refusal is at d/p 11, not
    the bolt's 27. A nut wall at 10 holds every nut cell read on both platforms; by the bolt's
    margin rule (largest R10 value at or below F / 1.25) it is 8. Isolated failures tied to a
    seam on a face cannot be bounded by a grid: this is a sample, not a proof.

## Eliminated

- hypothesis: platform difference (linux/amd64 only)
  evidence: E3, all 20 refuse on macOS arm64 with the same messages
  timestamp: 2026-10-30
- hypothesis: H1-noise, the tip piece gate refuses a correct cut because differencing two
    precise volumes of a large solid has a noise floor above T_PIECE of a tiny piece
  evidence: E6, eps 1e-9 vs 1e-6 changes the piece by <= 0.02 percentage points and the piece
    measured directly agrees; the cut geometry is off, not the measurement
  timestamp: 2026-10-30
- hypothesis: the bare thread (pipe sweep) is invalid or off its closed form at these sizes
  evidence: E5, every failing bolt's bare thread is 1 valid solid within 8.05e-07 of closed
  timestamp: 2026-10-30
- hypothesis: H4-seam, the nut countersink fails where the cone crosses a sewn segment seam
  evidence: E9, the bottom face's cone crosses the void with no seam inside and still removes
    nothing; d10 p0.35 has a seam inside its crossing band and builds
  timestamp: 2026-10-30
- hypothesis: the 2026-10-21 negative countersink inner radius causes the nut refusals
  evidence: E9, the inner radius at d30 p0.35 c0.15 is +14.9038 mm
  timestamp: 2026-10-30
- hypothesis: a fuzzy / OBB boolean fixes the tip cut
  evidence: E11
  timestamp: 2026-10-30
- hypothesis: H5, the tip envelope grazes the thread (bottom disc coplanar with the end face,
    cone through the root edge at z = 0), and moving it off fixes the cut
  evidence: E16, V1 changes nothing, V2 fixes none of the gross cases and breaks controls
  timestamp: 2026-10-30
- hypothesis: a wall on pitch against d alone (a max d/pitch) holds the in-wall failure region
    and keeps the catalogue (the owner's requested guard form)
  evidence: E23, E27, E29, E30, E31: the bolt tip error grows with the turn count at a fixed d/p
    (d2 p0.25 n80 refused, M20x200 at the same d/p and turns a catalogue row); every d/p wall
    from 8 to 26 admits refused grid parts on both platforms, and the one that admits none (6)
    refuses 219 of 294 catalogue bolts; nuts fail at isolated d/p 14 and 17
  timestamp: 2026-10-30
- hypothesis: the turn-driven tip error is a drift added at each sewn seam
  evidence: E25, one unsewn twist drifts more, not less
  timestamp: 2026-10-30
- hypothesis: the turn-driven tip error is a volume-integration artefact
  evidence: E28, the integration's reference point changes no digit; eps 1e-9 moves it only
    from +3.9674e-02 to +3.8964e-02
  timestamp: 2026-10-30
- hypothesis: cutting the tip on the first segment before sewing removes the turn-driven error
  evidence: E28, d2 p0.25 n90 right reads +0.039674 either way
  timestamp: 2026-10-30
- hypothesis: the auxiliary helix radius (1 mm) sets the bad size bands
  evidence: E30, radius 10 and d/2 move the piece by at most 0.0005 and no outcome
  timestamp: 2026-10-30

## Specialist Review

- not run (2026-10-30): specialist_hint `python` maps to the skill
  `python-expert-best-practices-code-review`, which is not installed in this environment, and
  the session ran diagnose-only, so no fix direction was applied for review.

## Resolution

root_cause: >
  One cause, two contributing conditions (AND-gate). (1) code: the OCCT booleans that cut the
  pipe-swept thread (the tip cone, BRepAlgoAPI Common in `solid/bolt.py` `tip_cut`; the lead-in
  countersink, Cut in `solid/nut.py` `finish`; and, outside the 20, the nut's prism-minus-void
  in `nut.assemble`) return a wrong result while reporting success once the swept surface's
  representation error is not small against the thread depth. That error is set by two constants
  that do not scale with the depth: MakePipeShell's default approximation tolerance in
  `helical.twist` (fixed in mm, so it grows as 1/pitch in thread depths) and the 14-sample flank
  spline `helical.SECTION_SAMPLES` (about 1.42e-05 thread depths per unit of d/pitch, 4.26e-02 at
  d300 p0.1). The result: a cut 1 % to 8 % off its oracle, 23x off, invalid, empty, null, or the
  uncut body, and which one depends on hand and platform. The bare thread and the void are valid
  and on their closed forms; the gates refuse every bad cut, so no wrong part is served (L02
  holds). (2) config: the parameter model admits any pitch for a d (pitch has only gt=0, the
  90-turn cap and the cost model), so nothing stops these parts before the kernel. Not a platform
  issue (all 20 refuse on macOS arm64 and linux/amd64), not the 2026-10-21 negative countersink
  radius. Refined by E23 to E32: the bolt tip gate fails by two mechanisms of the same sweep.
  (i) A wrong cut that grows with d/p (3 turns: about 4.3e-5 (d/p)^2 of the piece, right hand,
  in the worst size band). (ii) The differenced piece absorbs a discrepancy that grows with the
  thread length (about 5.2e-5 x d/p per turn in the same band), so a correct cut on a long
  thread is refused (bolt-d3-p0.1-n30-left is one). Both are piecewise constant in d, largest in
  the bands d 0.5 to 0.85 and 1.6 to 3.3, and identical on both platforms. The nut fails at
  isolated (d, d/p, m) cells (countersink cut invalid or empty, prism - void invalid or 2 solids).
  The accuracy variant removes all of these that were tried except one nut cell (E31).
guard_measurement (2026-10-30): >
  Candidate: refuse Fraction(repr(d)) / Fraction(repr(pitch)) > 20 on both kinds (inclusive at
  20), a 422 naming d and pitch. Chosen by: the largest R10 preferred number (ISO 3: 8, 10,
  12.5, 16, 20, 25) at or below F / 1.25, one R10 step; F = 27, the smallest refused 3-turn bolt
  d/p on both platforms; the largest 3-turn tip piece at 20 is +0.017109 (0.57 of T_PIECE) on
  both. Chosen after the readings, not pre-registered, and measured on macOS arm64 and emulated
  linux/amd64, which 07-SWEEP-PROTOCOL R1 counts as context, not a bound. (a) refuses 20 of 20. (b) refuses 0 of 294 bolt and 0 of 14 nut rows (max d/p
  8). (c) of the 475 in-wall explore labels it refuses 93: the 20 kernel-refused (12 admitted at
  >= 1 artifact, 8 already over_budget at every artifact) and 73 that build today (53 admitted at
  >= 1 artifact, 20 already over_budget at every artifact); admitted explore points refused that
  build today: stl-preview 32 of 411, stl-fine 25 of 402, step 47 of 439. Bounds tier
  (tests/data/oper_boundary.json, 435 points): refuses 53, the 11 tier failures and 42 others
  (26 bolt, 16 nut). Any nut wall from 10 to 28.5 gives the same (c) counts. (d) it still admits
  refused grid parts: bolts macOS arm64 83 of 2789 built cells (n3 0/782, n3s 0/726, n30 36/687,
  n60 12/307, n80 3/6, n90 32/281), linux/amd64 13 of 178; nuts under 20: macOS 15 of 3192,
  linux 10 of 428 (E32). No d/pitch wall from 6 to 26 holds the bolt grid and keeps B-01 (E30).
  Separate nut wall: 10 holds every nut cell read (0 of 1056 macOS, 0 of 132 linux) at the same
  (c) counts; the margin rule gives 8 (0 of 568 / 0 of 44), which also refuses the explore nuts
  at d/p 8.571 and 10: (c) then refuses 117 labels (97 that build today, 77 of them admitted) and
  80 tier points (11 + 26 bolt + 43 nut).
fix: none applied (diagnose-only mode; the owner chooses). Options in the ROOT CAUSE FOUND return.
verification: n/a
files_changed: []
