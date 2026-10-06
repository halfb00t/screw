# Phase 2: Thread Spike - Context

**Gathered:** 2026-10-06
**Status:** Ready for planning

<domain>
## Phase Boundary

A pre-registered measurement campaign, not product code. It answers four questions with run
ids over the whole allowed grid: which helical construction to build (failure frontier
included), what the mesh budget is (triangles, seconds, RSS, STL bytes, gzip ratio), whether a
kernel pair check can be made falsifiable (half-pitch control), and which volume estimator
agrees with the closed form. Output: spike code in `bench/thread_spike/`, every run recorded in
`bench/RESULTS.md`, the protocol and verdict in `02-SPIKE.md`, and one new decision-log entry
(construction, estimator, turn cap per size, the ISO 68-1:2023 profile pinned after the owner
has read the standard). If the escape clause fires, the spike says so and the roadmap is
revised before Phase 3 (construction) or Phase 5 (pair proof) is planned.

No field that builds a thread exists in `src/` when the decision entry is committed (SC4). No
table row ships; every ISO value the spike needs (coarse pitches, ISO 4017 length cap, ISO 4032
nut heights) is a preview value labelled UNVERIFIED in the protocol and the results.

Roadmap wording resolved by this discussion (planner: build to this, not to the loose text):
- SC1 "git history shows that order" is met by landing the protocol as its own PR before
  run 1 (D-19); `make pr.land` squashes, so a single PR could not show the order on `main`.
- SC3 "every standard length" is met by a superset (every integer mm and every integer-turn
  length up to min(10d, 200 mm), D-03), because the ISO 4017 length series is unverified
  until Phase 4 and a user can type any mm length.
- SC4 "pinned after the standard was read": the read happens *before* run 1, not after the
  campaign (D-01), because the section the spike builds depends on the profile.

</domain>

<decisions>
## Implementation Decisions

### Owner checkpoint: ISO 68-1:2023 before run 1
- **D-01:** The owner buys and reads ISO 68-1:2023 before the first run, pins the profile
  (basic or design) and the pin is written into the `02-SPIKE.md` protocol and later into the
  decision entry. Order: read → pin → pre-register → run. The planner writes this as a manual
  checkpoint task that opens the phase; no run before it. The read also confirms the profile
  coefficients the research took from memory (H = (√3/2)·P, crest and root flats) before the
  section maths is coded. STATE.md's "ISO 68-1 must be read" line is closed by this
  checkpoint. — **Reversibility:** one-way — every measured row is the pinned profile's
  section; a later profile change re-runs the whole campaign.

### Grid
- **D-02:** 15 sizes: M2, M2.5, M3, M4, M5, M6, M8, M10, M12, M16, M20 plus the second-choice
  M3.5, M7, M14, M18 (TABL-05 ships them in brackets; C3 says the frontier is not monotone, so
  an unswept size cannot ship under this spike's cap). Coarse pitch per ISO 262 (preview
  values, UNVERIFIED until Phase 4's row tests).
- **D-03:** Lengths per size: every integer-turn length (L = k·P, k ≥ 1) and every
  integer-millimetre length, from the smallest of those up to min(10d, 200 mm). A superset of
  any table the owner later verifies and of what a user can type (THRD-03); catches the
  integer-turn failures C1 saw first and finds the short-length floor.
- **D-04:** Failure frontier beyond min(10d, 200 mm): step 5 turns up to 250 turns (the
  research's measured ceiling for sewn twist); stop per size at the first failure or when
  build + fine mesh exceeds the 30 s INTERIM; record where and why each size stopped. The
  per-size turn cap in the decision entry is derived from this record.
- **D-05:** Both hands over the full grid on the host. Then one container validity-only pass
  of the winning construction in the linux/amd64 image (emulation on arm64): validity, solid
  count and volume outcomes only; timings are labelled emulation and feed no bound. STACK
  names the kernel pair and the sewing tolerance as the likeliest to differ on linux/amd64;
  Phase 7 does the timed re-sweep.

### Construction comparison and escape clause
- **D-06:** Candidates: the sewn twist-section (research favourite, 0/166 failures, volume to
  1.2e-5) on the full grid × hands × frontier; one-pipe twist and `cq_warehouse` ruled-surface
  as reference rows on a size sample; the naive `sweep` + `fuse` as the negative control. The
  negative control's silent-wrong rows (`isValid()` True, one solid, core missing) are kept as
  the known-bad input THRD-04's positive-control gate test needs in Phase 3. `cq_warehouse`
  runs from a scratch venv for the reference rows only and is never added to `pyproject.toml`
  (PITFALLS M11).
- **D-07:** Segment length: sweep K ∈ {3, 5, 10} on a size sample at the standard max turns
  and at the frontier; a pre-registered rule picks K (planner writes it in the protocol, e.g.
  fewest triangles among the K with zero failures and volume inside tolerance); K is then
  locked for the full grid.
- **D-08:** Each row builds a bare rod and a bare void (the cutter Phase 5's nut subtracts),
  plus one tip-chamfer-trim row per size at the standard max length to price Phase 4's one
  remaining fragile boolean (C10: 70 s on one failing sweep row). ISO 4753 is unread, so the
  chamfer cone angle is a stated protocol input labelled UNVERIFIED; the row is cost
  evidence, not geometry truth. No head is built: ISO 4014/4017 head rows do not exist yet
  and a plain hex prism would be an invented dimension (L02).
- **D-09:** Pass bar, pre-registered: 0 hard failures AND 0 silent-wrong rows over the whole
  allowed grid, both hands. Silent-wrong = precise volume (D-20's estimator) outside the
  pre-registered tolerance of the closed form, sign included; or solids ≠ 1; or `isValid()`
  False; or a non-watertight STL.
- **D-10:** Escape clause: any failure or silent-wrong row inside the standard range (either
  hand) → the spike reports it, Phase 3 is not planned until the roadmap is revised. An
  over-budget row (build + slower fine export > 30 s INTERIM, or fine STL raw + gzip > 64 MB
  INTERIM cache budget) → a per-size cap below the standard max, reported in the decision
  entry as Phase 3's cap-and-warn input; not an escape. Both budgets are INTERIM (Phase 1
  D-01); Phase 7 re-measures them. Nothing is tuned toward a pass.

### Pair-check protocol
- **D-11:** Clearances: c ∈ {0.05, 0.10, 0.15, 0.20} mm radial on the nut for the proof
  (brackets Phase 6's printed matrix); c = 0 and c = −0.05 as diagnostic rows: c = 0 must read
  `inconclusive` by definition (what the boolean did is recorded, not trusted); c = −0.05 must
  show interference near the closed-form estimate (the sensitivity check).
- **D-12:** Poses: 3 screw-motion matched poses (rotate the nut by θ and slide by θ·P/2π —
  physically identical, seam-shifted) plus 3 half-pitch-offset controls. `proven` only if all
  3 matched poses are empty AND all 3 controls are non-empty. Research saw one collision read
  empty at 2 of 3 slides; pose-dependence of a broken boolean is what is being measured.
- **D-13:** Bodies: a rod piece of length m + 2P versus a plain cylinder blank minus the void;
  nut height m per ISO 4032:2023 preview per size, UNVERIFIED until Phase 5. The hex adds
  nothing to a thread proof. Pair grid = size × hand × clearance × poses; bolt length does not
  enter (engagement is the nut height). M2–M4 heights are in Annex A, not the preview:
  Claude's discretion on a labelled source.
- **D-14:** Falsifiability rule (SC5): per (size, hand, c > 0), all matched poses empty AND
  every control non-empty within a pre-registered band of the closed-form estimate (band set
  in the protocol from the chosen estimator's measured error). A flaky (size, c) cell is
  recorded and excluded from Phase 5's allowed clearances for that size. A size with no
  c ≥ 0.05 at which the rule holds at every pose is "not falsifiable for size X" and fires the
  escape clause. A mixed-hand pair must read `violated` at every size; left-hand pairs are
  judged by the same rule as right-hand ones.

### Spike home, records, promotion
- **D-15:** Code lives in `bench/thread_spike/` (a package: kernel-free section maths and
  closed-form volume, helical rod and void builders, pair check, grid, report). It prints
  Markdown and exits 1 on a failed verdict (spur `bench/tip_chamfer_spike.py` shape). `bench/`
  is already under `make lint` and `make typecheck` (mypy `--strict`, L04), so the code meets
  the gate from day 1; its predicates (grid generation, verdict rules, the quiet-gate
  decision) are tested in `tests/test_bench.py`; no timing assertion enters the gate.
- **D-16:** Records: `.planning/phases/02-thread-spike/02-SPIKE.md` holds Question,
  Environment, Method, Predictions and Escape clause (spur
  `13-LATENCY-INVESTIGATION.md` shape) and is landed before run 1; `bench/RESULTS.md` gets a
  `## Thread spike (Phase 2)` section with every run's verbatim output, host state and run id
  (spur "Tooth-tip chamfer spike" shape); `02-SPIKE.md`'s Results and Verdict cite run ids and
  re-type no numbers. The new decision entry cites `bench/RESULTS.md` run ids.
- **D-17:** `bench/quiet.py`: `wait_quiet(bar=1.5, samples=3, interval=30, cap=900)` returns
  decisive / non-decisive plus timestamped readings; every spike run calls it and prints the
  load at start AND at end, each labelled by the time it was read (spur WR-07). A non-decisive
  release is recorded as such and never retried toward a pass. The 1.5 bar is spur D-05's
  convention on the same 12-core host class; a host with an open agent session idles near
  2.0, so runs happen with agents closed or read non-decisive.
- **D-18:** The builder is written to be moved: the maths is shaped like the future
  `calc/thread.py` (kernel-free, the oracle) and the builder like `solid/helical.py`; Phase 3
  moves them into `src/` unchanged where possible and the spike imports them back (spur 11-05:
  what was measured is what ships).

### Landing
- **D-19:** Two PRs, a deliberate exception to HOW_TO_DEVELOP's one-PR-per-phase, recorded
  here. PR 1: `bench/quiet.py`, the runnable `bench/thread_spike/` scaffold, `02-SPIKE.md`
  protocol, tests — reviewed by the other CLI (predictions and escape clause before any data
  exists) and landed via `make pr.land` before run 1. PR 2: the runs, `bench/RESULTS.md`,
  `02-SPIKE.md` Results/Verdict, the decision entry, roadmap/state updates. PR 1 is on
  `gsd/phase-02-thread-spike`; PR 2's branch is re-cut from `origin/main` after PR 1 lands
  (planner names it). — **Reversibility:** costly — once PR 1 is on `main`, a change to the
  protocol is a new PR that visibly post-dates it, which is the point.

### Claude's Discretion
- **D-20:** The volume-estimator selection rule and tolerance band. Candidates:
  `BRepGProp.VolumeProperties_s(shape, props, 1e-6, False, False)` and the STL's signed
  tetrahedron volume (both within 0.1 % in research; default `Volume()` is 15–21 % off on some
  constructions). The protocol states the rule before run 1 (error vs the closed form across
  the grid, then cost).
- The mesh-budget sweep design: deviation presets expressed as a fraction of thread depth
  (5H/8) with spur's absolute INTERIM presets as reference rows; triangle count, mesh seconds,
  peak RSS, STL bytes, STEP bytes and seconds, and the L19 gzip table via `bench.export_cost`'s
  rule; sized from the research numbers (sewn twist fine mesh ≤ 1 s per row, so the full grid
  is affordable; the planner decides whether gzip runs per row or per size max).
- Container-pass mechanics (D-05): mount `bench/` into the runtime image or add a dev stage;
  the image is the runtime closure only (L08).
- The labelled source for M2–M4 nut heights (D-13) and the sewing tolerance (research 1e-4)
  and tip-chamfer angle (D-08) as protocol inputs.
- Whether `BRepAlgoAPI_Common.HasErrors()/HasWarnings()` through OCP is read as a diagnostic
  column in the pair check (untested in research; informative, not a verdict input).
- Reuse of `bench.machine_facts()`, `bench.build_time.Timing`'s worst-request rule and
  `bench.export_cost`'s gzip table where they fit; a `make bench.thread` target in the
  Makefile's bench family.
- Run ids, the exact Markdown layout of the report, and the sample sizes for D-06/D-07.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` § Phase 2 — goal, success criteria 1–5 (read with the three
  resolutions in `<domain>`)
- `.planning/REQUIREMENTS.md` — INFR-03 (this phase); THRD-01, THRD-02, THRD-04 (what Phase 3
  builds on the answer); PAIR-03, PAIR-04 (the verdict shape the pair check must serve);
  OPER-01 (integer L/P lengths); TABL-05 (the 15 sizes)
- `.planning/PROJECT.md` § Context — the spur lessons (spike before field, pre-registration,
  quiet host); § Constraints — measurement before knobs
- `.planning/STATE.md` § Blockers/Concerns — the ISO 68-1 line D-01 closes; the pair-proof
  reliability line SC5 answers

### Research (the evidence the protocol predicts from)
- `.planning/research/STACK.md` § Reference implementation (the sewn twist-section code the
  builder starts from), § Measured evidence A–D (construction table, STL/STEP sizes, pair cost,
  volume accuracy), § 2 Thread generation in OCCT, § Gaps
- `.planning/research/ARCHITECTURE.md` § Q3 (pair proof: poses, controls, `PairReport`),
  § Q4 (component split, one builder for rod and void, postcondition, constructions compared),
  § Q5 STL: the cost centre, § Q6 (what the spike must answer), § UNVERIFIED register
- `.planning/research/PITFALLS.md` C1 (silent wrong solids), C2 (volume estimator), C3 (turns,
  frontier not monotone), C4 (the proof that cannot fail), C9 (mesh vs thread depth), C10
  (ends), C12 (noise floor, labelled readings), § Probe record (the precise-volume and
  watertightness snippets)
- `.planning/research/SUMMARY.md` — P2 row and the open owner questions (Q4 profile)

### Harness and records
- `bench/README.md` — where each half runs and why; the corpus rule (a corpus is never
  re-picked to flatter a ceiling)
- `bench/RESULTS.md` — the entry shape (host state, load, verbatim output, "not a bound")
- `bench/__init__.py`, `bench/build_time.py`, `bench/export_cost.py`, `bench/corpus.py`,
  `tests/test_bench.py` — reusable pieces and the tested-predicate pattern
- `docs/architecture/decision_log.md` — L02 (no plausible number), L04 (no `Any`, bench
  included), L07 (harness, not numbers), L08 (squash landing — why D-19), L09 (INTERIM policy)
- `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` — the 30 s / 64 MB budgets
  D-10 compares against are INTERIM
- `docs/CODING_VALUES.md`, `docs/HOW_TO_DEVELOP.md` §3–§9 — the loop; D-19 is the exception

### spur precedents (`../spur`)
- `../spur/bench/tip_chamfer_spike.py`, `../spur/bench/honeycomb_spike.py` — spike script
  shape (Markdown report, exit 1 on a failed verdict, `machine_facts`, load readings)
- `../spur/bench/RESULTS.md` § "Tooth-tip chamfer spike (Phase 10, D-05)", § "Honeycomb
  cell-count spike (Phase 11, D-24)", § "Phase 13 investigation sessions" — record shape and
  the quiet-gate release table
- `../spur/.planning/milestones/v0.3-phases/13-latency-bar/13-LATENCY-INVESTIGATION.md` —
  the pre-registered protocol shape (Question, Environment, Method, Predictions, Results,
  Verdict; escape clause written before the split pair)
- `../spur/.planning/RETROSPECTIVE.md` — pre-registration and quiet-gate lessons

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `bench/__init__.py` `machine_facts()`; `bench/build_time.py` (`Timing`, the
  build-plus-slower-export rule, load printed before the first row); `bench/export_cost.py`
  (the L19 gzip table and selection rule, mesh-on-copy cost); `bench/corpus.py` (a written-out
  deterministic grid and its `label()`); `tests/test_bench.py` (predicates tested, timings
  not).
- `src/screw/solid/__init__.py`: `TESSELLATION` INTERIM presets (reference rows for the mesh
  budget); `build()`/`clear_cache()` exist but have no thread builder, so the spike builds its
  own solids through `cadquery` directly from `bench/` (outside contract 8's source set, as
  `bench/build_time.py` already is).
- `.venv` carries the pinned kernel pair `cadquery 2.8.0` / `cadquery-ocp 7.9.3.1.1`; every
  research number was taken on it.

### Established Patterns
- A measurement is not a bound: every number carries machine, load and date; INTERIM labels
  on anything carried from spur; nothing in `make verify` asserts a timing.
- Comments carry the measurement or the constraint; `Any` is never written (bench included).
- Pre-registered protocol, quiet-host gate with a cap, non-decisive recorded not retried.
- The current `_build` gate (`len(Solids()) == 1 and isValid()`) is exactly the C1 hole; an
  open `blocker` debt item (collapsed thin solid served as 200) sits on it, scheduled for a
  `/gsd-quick` PR outside this phase. The spike's postcondition (D-09) is what Phase 3 replaces
  that gate with.

### Integration Points
- Nothing enters `src/` this phase. New: `bench/quiet.py`, `bench/thread_spike/`, a
  `make bench.thread` target, `tests/test_bench.py` cases, `bench/RESULTS.md` section,
  `02-SPIKE.md`, a new `Lxx` in `docs/architecture/decision_log.md`, the STATE.md blocker line.
- gsd: `git.branching_strategy: phase`; branch `gsd/phase-02-thread-spike` cut from
  `origin/main` at `3e992cd` for the discussion and PR 1; PR 2 on a branch re-cut after PR 1
  lands (D-19).

</code_context>

<specifics>
## Specific Ideas

- The builder starts from STACK.md § Reference implementation (sewn 5-turn twist section,
  `SetMaxSegments(500)`, `BRepBuilderAPI_Sewing(1e-4)`), parameterised by K (D-07).
- Precise volume: `BRepGProp.VolumeProperties_s(shape.wrapped, props, 1e-6, False, False)`;
  mesh check: binary STL parsed, vertices welded at 1e-5 mm, every directed edge paired,
  signed tetrahedra volume (PITFALLS § Probe record).
- Every UNVERIFIED preview value (pitches, length cap, nut heights, chamfer angle) is labelled
  as such wherever it appears: protocol, report, RESULTS.md, decision entry.
- Load readings are printed with the time they were read, at both ends of every run.
- The decision entry records: construction + K, estimator + tolerance, per-size turn cap and
  its source row, pair-check verdict per size with excluded clearances, ISO 68-1:2023 profile.

</specifics>

<deferred>
## Deferred Ideas

- Design (rounded-root) profile as a later option if the owner pins basic in D-01.
- STEP importer behaviour in FreeCAD, Fusion, SolidWorks, Onshape — unmeasured, not this
  phase.
- The open `blocker` debt item (collapsed thin solid served as 200) — its trigger is the
  `/gsd-quick` PR after the Phase 1 close, outside Phase 2.
- Phase 7 reuses `bench/quiet.py` and the Phase 2 grid as the fixed threaded corpus
  (`bench/README.md`'s corpus rule).

</deferred>

---

*Phase: 02-thread-spike*
*Context gathered: 2026-10-06*
