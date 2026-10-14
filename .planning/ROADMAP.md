# Roadmap: screw

## Overview

screw goes from a scaffold with no product code to its first release, the mating-pair cut: an
ISO 4014/4017 hex bolt and an ISO 4032 hex nut with real helical threads, proven to mate in the
kernel and then on the owner's printer. The order follows the research's build-order evidence
(`.planning/research/SUMMARY.md`, `ARCHITECTURE.md` § Q6). spur's runtime is ported onto a
walking-skeleton kind while a pre-registered thread spike measures the top risk. The thread
lands as one gated component before any table exists. Tables ship with the kind that uses them.
The nut phase brings the kernel pair proof. The owner's printed test sets the clearance default
and the printability threshold, and the operability bounds are re-swept on the finished grid on
linux/amd64. Every kind ships on UI, API and CLI in the same change: the registry-driven parity
test goes green in Phase 1 and stays in the gate for every phase after it. Phases are ordered
by dependency, not scheduled. The socket head cap screw (ISO 4762, TYP2-01) is the second
release and is not in this roadmap.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Runtime Port and Walking Skeleton** - spur's runtime ported per L07, serving a plain skeleton bolt on UI, API and CLI with parity proven (completed 2026-10-06)
- [x] **Phase 2: Thread Spike** - a pre-registered measurement picks the thread construction, volume estimator and turn cap before any thread field exists (completed 2026-10-09)
- [x] **Phase 3: Real Helical Thread** - the bolt kind carries a real ISO 68-1 helical thread, right- or left-hand, behind a postcondition gate (completed 2026-10-11)
- [x] **Phase 4: ISO Hex Bolts and Screws** - ISO 4014 and 4017 presets from cited, tested table rows fill explicit mm fields; a traceable info panel for the bolt (completed 2026-10-12)
- [ ] **Phase 5: Hex Nut and Kernel Pair Proof** - ISO 4032 nut with a clearance field, matching-part derivation and a kernel pair proof that can fail
- [ ] **Phase 6: Printed Pair Acceptance** - the owner's printed test sets the clearance default and the printability threshold; a printed pair threads together by hand
- [ ] **Phase 7: Operability Re-sweep** - every runtime bound measured on the full grid on linux/amd64 and cited; every allowed configuration builds inside the timeout

## Phase Details

### Phase 1: Runtime Port and Walking Skeleton

**Goal**: A user can generate a walking-skeleton bolt (`d`, `pitch`, `length`, plain unthreaded solid; an internal milestone, never released) from the web UI, the HTTP API and the CLI, all served by spur's ported runtime from one registered model, with front-end parity proven by one test over the registry.
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: INFR-01, INFR-02, FRNT-01, FRNT-02, FRNT-03, FRNT-04, FRNT-05
**Success Criteria** (what must be TRUE):
  1. A user can open the web UI, get a form generated from `/api/schema`, see the skeleton bolt in the live 3D preview with its info panel, and copy a shareable URL that carries the full parameter set with defaults omitted; the same bolt comes from the API (info, STL, STEP, schema and health under the `bolt` kind path) and from `screw serve | info | export`.
  2. A field the `bolt` kind does not define is a `422` naming it on the API and an error naming it on the CLI, never silently ignored; one parity test over the registry proves the UI, API and CLI expose the same fields, and it stays in `make verify` for every later phase.
  3. The L07 runtime is ported and running: builds execute in worker processes off the event loop, an overloaded server answers `503` + `Retry-After` from the web layer only, `scripts/pr_land.py` + `skip_tokens.py`, the commit-msg hook and the `main` ruleset are in place, `make check` passes (in-image smoke test and vendored-bundle byte check), the coverage floor is enforced, and the `bench/` harness runs against the skeleton. No spur gear module (`calc.py`, `model.py`, `params.py`, their tests, the regression fixture) is copied and no spur runtime figure is carried as a final bound.
  4. `make verify` is green with import-linter enforcing the inherited contracts plus "only `solid` imports `cadquery`/`OCP`" and "`app` never imports the kernel by any path"; each later contract is written to land with the module it guards (tables in Phase 4, the pair proof in Phase 5).

**Plans**: 10/10 plans complete

Plans:
**Wave 1**
- [x] 01-01-PLAN.md — Tracer: skeleton bolt over the API through the worker pool; owner vets dev packages; D-16 pool guard

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 01-02-PLAN.md — API contract tests per kind; records tests; L09 and the interim-bounds debt item

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 01-03-PLAN.md — CLI slice: `screw serve | info | export`, flags from the model; README commands as tests

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 01-04-PLAN.md — Web UI slice: kind selector, schema form, preview, generic info panel, hash; vendored bundle check

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 01-05-PLAN.md — One registry-driven parity test across UI, API and CLI, shown to fail on planted drift

**Wave 6** *(blocked on Wave 5 completion)*
- [x] 01-06-PLAN.md — Container delivery: linux/amd64 runtime closure, image with smoke, compose, `make check`

**Wave 7** *(blocked on Wave 6 completion)*
- [x] 01-07-PLAN.md — Wall `main`: skip-token hook, `make pr.land`, required jobs, L08 and docs

**Wave 8** *(blocked on Wave 7 completion)*
- [x] 01-08-PLAN.md — Bench harness ported and run once against the skeleton

**Wave 9** *(blocked on Wave 8 completion)*
- [x] 01-09-PLAN.md — Coverage floor measured and enforced; interim-bounds inventory complete; docs describe the skeleton

**Wave 10** *(blocked on Wave 9 completion)*
- [x] 01-10-PLAN.md — Owner checkpoint after the merge: apply and read back the `main` ruleset

**UI hint**: yes

### Phase 2: Thread Spike

**Goal**: The owner knows, from a pre-registered and recorded measurement rather than a guess, which helical construction to build, which volume estimator to trust, what turn cap each size needs, and whether a kernel pair proof can be made falsifiable, all before any field that builds a thread exists.
**Mode:** mvp
**Depends on**: Nothing (needs only `cadquery`; may run in parallel with Phase 1)
**Requirements**: INFR-03
**Success Criteria** (what must be TRUE):
  1. The method, predictions and escape clause are committed before the first run, and git history shows that order.
  2. Every run sits behind a quiet-host gate, and every load reading is labelled with when it was taken.
  3. The results answer four questions with run ids, over the whole allowed grid (M2–M20 coarse pitch, every standard length) rather than a sample: construction, failure frontier included; mesh budget (triangles, seconds, RSS, gzip ratio); pair-check reliability with its half-pitch control; and the volume estimator against the closed form.
  4. A new decision entry records the construction chosen, the volume estimator chosen, the turn cap per size, and the ISO 68-1:2023 profile (basic or design) pinned after the standard was read, and no field that builds a thread exists in `src/` when it is committed.
  5. If the pair check cannot be made falsifiable, or the worst case trips the escape clause, the spike says so and the roadmap is revised before Phase 5 is planned; no constant is tuned toward a pass.

**Plans**: 8/8 plans complete (two PRs, D-19: plans 01-06 are PR 1 on `gsd/phase-02-thread-spike`; plans 07-08 are PR 2 on `gsd/phase-02-thread-spike-runs`, cut from `origin/main` after PR 1 lands)

Plans:
**Wave 1**
- [x] 02-01-PLAN.md — Owner checkpoint: read ISO 68-1:2023, pin the profile, rule on R0-R5; record them in 02-SPIKE.md

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 02-02-PLAN.md — Tracer: one sewn rod row end to end (quiet gate, worker, closed form, verdict, report); the pre-registration guard

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 02-03-PLAN.md — Exact D-03 grid and D-04 frontier, K sweep, mesh ladder, guarded blocks, verdict rules

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 02-04-PLAN.md — Negative control, one-pipe and ruled-surface reference (legitimacy checkpoint), tip trim, fresh-child RSS, container pass

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 02-05-PLAN.md — Pair check with half-pitch controls and closed-form oracle; one guarded campaign command

**Wave 6** *(blocked on Wave 5 completion)*
- [x] 02-06-PLAN.md — Pre-register the protocol, other-CLI review, land PR 1 with make pr.land

**Wave 7** *(blocked on Wave 6 completion)*
- [x] 02-07-PLAN.md — Owner runs the campaign on a quiet host; every block recorded verbatim in bench/RESULTS.md

**Wave 8** *(blocked on Wave 7 completion)*
- [x] 02-08-PLAN.md — Reproducible verdict, Results/Verdict by citation, owner decision, L11

### Phase 3: Real Helical Thread

**Goal**: A user who sets `d`, `pitch` and `length` in explicit millimetres gets a bolt-kind solid carrying a real ISO 68-1 helical thread, right- or left-hand, on all three front ends, and a build the postcondition rejects never reaches a cache, a preview or a download.
**Mode:** mvp
**Depends on**: Phase 1, Phase 2
**Requirements**: THRD-01, THRD-02, THRD-04
**Success Criteria** (what must be TRUE):
  1. Preview, STL and STEP from the UI, API and CLI carry a modelled helical thread built by the construction Phase 2 chose, with the profile Phase 2 pinned; the skeleton's plain solid is gone and there is no cosmetic or unthreaded option.
  2. A user can set `left_hand: true` (default false) and get a left-hand thread that passes the same postcondition as a right-hand one across the tested grid; the parity test is green with the new field.
  3. Every thread build is checked before it is cached or served: valid shape, exactly one solid, volume within the stated tolerance of the closed form using the estimator Phase 2 chose (sign included, never bare `Volume()`); a failure is a `BuildError` naming what failed, and a positive-control test feeds the gate a known-bad build and sees it refused.
  4. The one helical builder is proven on a bare rod and on a bare void (the void the nut subtracts in Phase 5) against the closed form: a sample in `make verify`, the full grid in a slower tier.

**Precondition (owner, 2026-10-10, D-13)**: the harness-review `/gsd-quick` PR (`docs/tech_debt/active/2026-10-09-thread-spike-harness-review-findings.md`) is merged on `main` and `gsd/phase-03-real-helical-thread` is rebased on it before plan 03-01 starts; it is a separate PR, not folded into this phase.

**Plans**: 7/7 plans complete (one PR, through `make pr.land`)

Plans:
**Wave 1**
- [x] 03-01-PLAN.md — Tracer: the default bolt is the gated L11 thread on API, CLI and pool; positive controls and the make-verify sample; broken exports refused, collapsed-solid blocker retired

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 03-02-PLAN.md — Root-radius and 250-turn 422s at the params boundary; the info document describes the thread with the threaded-rod warning

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 03-03-PLAN.md — The fine STL L11 measured over budget is refused on the API and the CLI and warned about on the info document

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 03-04-PLAN.md — `left_hand` on every kind, built and probed left-handed from the API and the CLI; repeated keys and flags refused

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 03-05-PLAN.md — The page: the checkbox and its link round trip, foreign/repeated/unreadable hash keys refused, warnings kept per mesh; 01-UI-SPEC amended

**Wave 6** *(blocked on Wave 5 completion)*
- [x] 03-06-PLAN.md — The spike imports the shipped maths, builder and estimator back; the full measured grid in `grid.yml` outside the required jobs

**Wave 7** *(blocked on Wave 6 completion)*
- [x] 03-07-PLAN.md — L12, the docs, the INTERIM register and the fix shas; coverage floor re-measured

**UI hint**: yes

### Phase 4: ISO Hex Bolts and Screws

**Goal**: A user picks "M6 × 20, ISO 4017" (or an ISO 4014 size and length) and gets a hex head bolt or screw whose explicit millimetre fields were filled from a cited, tested table row, with an info panel whose every number traces to a field or a row.
**Mode:** mvp
**Depends on**: Phase 3
**Precondition (owner checkpoint)**: owner holds purchased copies of ISO 4014:2022, 4017:2022, 4032:2023, 262:2023, 724:2023, 965-2:2024. No table row is entered as verified before the owner confirms this (TABL-04).
**Requirements**: THRD-03, TYPE-01, TYPE-02, TABL-01, TABL-02, TABL-03, TABL-04, TABL-05, TABL-06, TABL-07, INFO-03, INFO-05
**Success Criteria** (what must be TRUE):
  1. A user can pick standard + size + length from the valid combinations across M2–M20 per ISO 262:2023 (first-choice sizes, second-choice sizes in brackets, coarse pitch only) on the UI, API and CLI, and get an ISO 4014 bolt (`s`, `e`, `k`, `dw`, `b` by length band, `ls`/`lg`, product grade A/B; plain planar thread ends, the chamfer and the fillet are Phase 5's, D-02) or an ISO 4017 screw threaded to the head up to the standard's 200 mm cap; the parity test is green.
  2. The preset fills explicit mm fields only: the shareable URL carries mm fields, the preset id is metadata, and opening the URL rebuilds the same part without consulting a table (import-linter forbids `screw.params` and `screw.calc.thread` from importing `tables` and keeps `tables` a leaf); `thread_length` is filled by the preset (full length for 4017, `b` for 4014) and stays editable.
  3. The UI badge reads "matches ISO 4017 M6 × 20" while the fields equal the row and "custom, based on ISO 4017 M6 × 20" once any field is edited; the designation line shows the ISO designation without a property class.
  4. Every table row carries a typed `Source` (standard, edition, table, column), so a row without one fails mypy, and exactly one pure-data verification test generated from the table; a row marked UNVERIFIED (entered from a preview) is refused by the gate in a release build.
  5. The bolt's info panel numbers (head, shank and thread) come from the kernel-free maths, each traceable to a mm field or a cited, tested row; a value that cannot be computed honestly is a warning and no number; any volume shown is the closed form; where the ISO wrench size differs from the withdrawn DIN equivalent the panel adds a one-line note.

**Plans**: 17/17 plans complete (one PR, through `make pr.land`)

Plans:
**Wave 1**
- [x] 04-01-PLAN.md — Owner opening read (ISO 4017 M6 × 20, ISO 262 M6, Clause 7, rendering route, permanence of the defaults acknowledged); the D-03 head-fuse probe; purchased material kept out of git
- [x] 04-02-PLAN.md — Fine-STL caps keyed by hand from the grid records, reworded to what was measured, WR-02 retired in the fixing commit (D-21)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 04-03-PLAN.md — Tracer (defaults from the 04-01 acknowledgement): the empty link builds a gated hex head screw (s, k) on every front end; head_too_small; the bare-thread gate

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 04-04-PLAN.md — thread_length and the plain shank (ISO 4014 shape); built_thread_length and the sliver fold; caps on the built thread

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 04-05-PLAN.md — The explicit-conflict 422 at the request boundary on API and CLI (D-25); the short-thread warning, IN-01 retired
- [x] 04-06-PLAN.md — The bench corpus pins thread_length and keeps its Phase 3 meaning; its README and the d100 repro
- [x] 04-07-PLAN.md — First cited rows (ISO 262 and ISO 4017 M6) double-entered behind the gates and contracts 6 and 7

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 04-08-PLAN.md — The info document reports the exact match and the designation; the frozen defaults equal the ISO 4017 M6 × 20 row

**Wave 6** *(blocked on Wave 5 completion)*
- [x] 04-09-PLAN.md — Owner's full copy; every ISO 262 size and every ISO 4017 head and length

**Wave 7** *(blocked on Wave 6 completion)*
- [x] 04-10-PLAN.md — ISO 4014 heads, b bands and shank cells; ISO 4014 presets filling b; the 4017-first tie rule

**Wave 8** *(blocked on Wave 7 completion)*
- [x] 04-11-PLAN.md — Info document: groups, the matched row's cited values, the no-row warning, grade and DIN wrench notes

**Wave 9** *(blocked on Wave 8 completion)*
- [x] 04-12-PLAN.md — Preset catalogue on API and CLI (`/api/presets`, `screw presets`, `--preset`); parity rule; refused fine-STL count

**Wave 10** *(blocked on Wave 9 completion)*
- [x] 04-13-PLAN.md — Page: picker, badge, designation, groups, notes, unrounded numbers; 01-UI-SPEC amended
- [x] 04-14-PLAN.md — L13 (supersedes L12's cap list; D-25 acceptance) and L12's pointer, overview, README status; TYPE-01/THRD-05/SC1 amendments; STATE blockers; interim-bounds rows

**Wave 11** *(blocked on Wave 10 completion; gap closure G-04-3)*
- [x] 04-15-PLAN.md — Download state on the info document (per format and quality, from `download_refusal`); `/api/<kind>/info` and `screw info` print it alike; the model route and `screw export` refuse exactly what it refuses; every catalogue row checked

**Wave 12** *(blocked on Wave 11 completion; gap closure G-04-3)*
- [x] 04-16-PLAN.md — The page builds both download links from `info.downloads` and offers `Download STL (preview)` where the fine STL is refused; 01-UI-SPEC and L13 amended; IN-02 closed

**Wave 13** *(blocked on Wave 12 completion; gap closure G-04-5)*
- [x] 04-17-PLAN.md — An info row wraps: the label keeps half the row and a full-precision value drops whole under it instead of into the next cell (CSS only, never rounded); style.css source pin; 01-UI-SPEC amended

**UI hint**: yes

### Phase 5: Hex Nut and Kernel Pair Proof

**Goal**: For any bolt a user can get the matching ISO 4032 nut at a chosen radial clearance, see the pair's numbers on the info panel, and get a kernel verdict on whether the pair mates, one that cannot report `proven` when its own control did not fire.
**Mode:** mvp
**Depends on**: Phase 4
**Precondition (owner checkpoint)**: owner holds purchased copies of ISO 4014:2022, 4017:2022, 4032:2023, 262:2023, 724:2023, 965-2:2024, and ISO 4753 (bolt ends, D-02). The ISO 4032 and ISO 965-2 rows ship here (TABL-04); ISO 4753 is read here for THRD-05.
**Revision (L11 escape clause, 2026-10-13)**: M18 is not falsifiable on either hand in `2026-10-08-a-pair` (one control pose reads empty at every clearance). Owner's direction: scope the proof, M18 reads `inconclusive`. The D-14 rule stands as PAIR-03 writes it; no rule or constant is changed toward a `proven`. Phase 5 is plannable on this revision (decision log L11, revision direction).
**Requirements**: TYPE-03, TYPE-04, THRD-05, PAIR-01, PAIR-03, PAIR-04, INFO-01, INFO-02, FRNT-06
**Success Criteria** (what must be TRUE):
  1. A user can generate an ISO 4032 hex nut M2–M20 from a preset or mm fields on the UI, API and CLI (`s`, `e`, `m`, `mw`, `dw`, chamfers on both faces), with M2–M4 labelled "informative / historical" in the preset and on the panel; for any bolt the user gets the matching nut, and vice versa, from the same `d`, pitch, hand and clearance; the nut thread and the bolt tip carry lead-in chamfers; the parity test is green with both kinds.
  2. The nut's `clearance` field is radial millimetres, a positive value enlarges the nut's thread while the bolt stays nominal, and no default for it ships before Phase 6 records the printed test; the info panel shows the full INFO-01 set (clearance radial and diametral, resulting nut diameters, engagement in turns) and the 6g/6H limits from ISO 965-2:2024 under the label "limits for a bought part; this model is nominal and not toleranced".
  3. `screw pair` and the solid-package function return `proven | violated | inconclusive` with the control result: a half-pitch axial offset of the same pair must collide at every matched pose, or the verdict is `inconclusive` naming the pose and clearance whose control read empty, never `proven`; clearance ≤ 0 is `inconclusive` by definition; right- and left-hand pairs go through the same checks; one size runs in `make verify`, the full grid in a CI job against expected verdicts pre-registered from `2026-10-08-a-pair` before the first run (M18 `inconclusive` on both hands at K = 3; each size's excluded clearances outside its proven set), and no rule or constant is changed to turn an `inconclusive` into a `proven`.
  4. The pair proof is not an API endpoint: the API and UI show closed-form flank gaps instead, and import-linter forbids `app` and `pool` from importing the pair module.
  5. STL and STEP downloads come from the same modelled-thread solid; the STL chord deviation is explicit, measured against the clearances the printed test will use, and recorded and cited in a decision entry, with `ControlSurfaceDeflection` on for downloads; the preview may mesh coarser, the numbers may not.
  6. The M18 control that reads empty at theta -2π/3 (right hand) and +2π/3 (left hand) at every clearance in `2026-10-08-a-pair` (0 solids, no boolean error or warning) is diagnosed in one bounded task whose method is committed before it runs; the finding is recorded in a decision entry and changes no verdict rule. Until a later campaign proves M18, the M18 nut ships (criterion 1), `screw pair` reads `inconclusive` for it, and the info panel's pair section labels M18 "kernel pair proof inconclusive at K = 3 (`2026-10-08-a-pair`)" from the cited record, not from a kernel call (criterion 4).

**Plans**: 4/18 plans executed (sequential waves 1-18; the pre-registration lands as its own PR first)

Plans:
**Wave 1**
- [x] 05-01-PLAN.md — Pre-registration PR: expected pair verdicts derived from `2026-10-08-a-pair` by the unmodified rule, and the M18 diagnosis protocol with its probe (D-07, D-08)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 05-02-PLAN.md — D-10 end-cut probe, then the owner read of ISO 4032, 724, 965-2, 4753 and the phase rulings, recorded in 05-OWNER-READS.md (D-14)

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 05-03-PLAN.md — Codex reviews the pre-registration PR; it lands on main; the phase branch merges origin/main

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 05-04-PLAN.md — Tracer: the nut kind with a required clearance on every front end, hex prism less the L11 void, two gates (D-01, D-15)

**Wave 5** *(blocked on Wave 4 completion)*
- [ ] 05-05-PLAN.md — Nut rules: root radius with clearance, nut_too_thin, turn cap on m + 2P, the non-positive clearance warning, the nut fine-STL rule (D-04, D-13)

**Wave 6** *(blocked on Wave 5 completion)*
- [ ] 05-06-PLAN.md — ISO 4032:2023 rows double-entered, relation tests, the frozen nut defaults pinned to the M6 row

**Wave 7** *(blocked on Wave 6 completion)*
- [ ] 05-07-PLAN.md — The ISO 4032 catalogue and the nut's exact match, cited values, designation and Annex A note (D-17)

**Wave 8** *(blocked on Wave 7 completion)*
- [ ] 05-08-PLAN.md — ISO 724 nominal diameters and the ISO 965-2:2024 6g/6H limits, double-entered (D-16)

**Wave 9** *(blocked on Wave 8 completion)*
- [ ] 05-09-PLAN.md — The panel: pitch and minor diameters, the INFO-02 limits group, the pair rows, the M18 note (D-16, D-19, D-20)

**Wave 10** *(blocked on Wave 9 completion)*
- [ ] 05-10-PLAN.md — The matching part (counterpart) on every info document and the page link; UI contract amendments (D-02, D-03)

**Wave 11** *(blocked on Wave 10 completion)*
- [ ] 05-11-PLAN.md — TDD: kernel-free end-cut oracles, end models, capped depths and the piece tolerance (D-09, D-10)

**Wave 12** *(blocked on Wave 11 completion)*
- [ ] 05-12-PLAN.md — Bolt ends: ISO 4753 tip cone and ISO 4014 under-head fillet ring, gated whole and by piece, watertight sweep (D-09, D-11)

**Wave 13** *(blocked on Wave 12 completion)*
- [ ] 05-13-PLAN.md — Nut ends: lead-in countersinks and face chamfers on both faces, watertight sweep; the standing warning rewritten (D-12, D-18)

**Wave 14** *(blocked on Wave 13 completion)*
- [ ] 05-14-PLAN.md — The pair proof: the rule moved into calc/pair.py, the bodies and prove() in solid/pair.py, the shipped-solid evidence row, the server-side contract (D-05, D-06, D-24)

**Wave 15** *(blocked on Wave 14 completion)*
- [ ] 05-15-PLAN.md — `screw pair` with exit codes, the verify cell, the pair-marked grid, `make pair`, pair.yml; the ubuntu reading of the verify cell (D-06, D-07)

**Wave 16** *(blocked on Wave 15 completion)*
- [ ] 05-16-PLAN.md — Kernel runs: the M18 diagnosis, the full pair grid, the product cells at the verified nut height (D-07, D-08)

**Wave 17** *(blocked on Wave 16 completion)*
- [ ] 05-17-PLAN.md — FRNT-06: the fine STL deflection by the owner's rule, ControlSurfaceDeflection and deviation pinned, caps re-derived if the preset moved (D-21)

**Wave 18** *(blocked on Wave 17 completion)*
- [ ] 05-18-PLAN.md — The preview download names its quality (D-22); L14, the overview, the UI contract, requirement and state lines, the phase's debt (D-23)

**UI hint**: yes

### Phase 6: Printed Pair Acceptance

**Goal**: The owner holds a bolt and a nut printed from this tool at the default clearance that thread together by hand, and that default and the printability threshold come from a recorded printed test, not from a forum or vendor figure.
**Mode:** mvp
**Depends on**: Phase 5
**Requirements**: PAIR-02, PAIR-05, PAIR-06, INFO-04
**Success Criteria** (what must be TRUE):
  1. The printed test (M6–M12 matrix of clearance steps) has its method, predictions and escape clause committed before the first print, and its results, every sample with pass or bind, are recorded in the repo by the owner (manual checkpoint).
  2. The default `clearance` is set once from the recorded result, as a single absolute-millimetre value (L02), and cited in a new decision entry.
  3. The owner prints a bolt and its matching nut at the default clearance and they thread together by hand: the release's manual acceptance. The kernel verdict for that pair is `proven`, which is necessary, not sufficient.
  4. The test also drives a nominal printed bolt into a bought nut and records the result; if it binds, PAIR-07 (bolt-side `undersize`) is promoted to a v1.x requirement in REQUIREMENTS.md, otherwise the record says it is not needed.
  5. The printability threshold is a constant set from the same test and cited; sizes and pitches below it get a cap-and-warn printability warning naming its source on the UI, API and CLI.

**Plans**: TBD
**UI hint**: yes

### Phase 7: Operability Re-sweep

**Goal**: Every configuration a user is allowed to ask for builds inside a per-build timeout measured on linux/amd64 over the full grid, or is capped and warned or refused with a `422`, and every runtime bound cites the run that set it.
**Mode:** mvp
**Depends on**: Phase 6 (the sweep runs on the final grid, clearance default included)
**Requirements**: OPER-01, OPER-02, OPER-03
**Success Criteria** (what must be TRUE):
  1. The per-build timeout is measured over the whole allowed grid on linux/amd64 (every size, every standard length, including lengths where `L/P` is an integer) and recorded as a constant whose decision entry cites the run.
  2. The memory ceiling, gzip level, worker count and bytes-cache budget are each re-swept for threaded parts on linux/amd64 and each cited in a decision entry; no spur figure and no interim value remains in the code.
  3. A CI job builds every allowed configuration inside the timeout; a configuration that cannot is capped and warned or refused with a `422` naming the fields, never silently shortened.
  4. With the measured bounds in place, CAD builds still run in worker processes off the event loop, and `make check` (in-image smoke test, vendored-bundle byte check) passes.

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7. Phase 2 needs nothing from Phase 1 and may run alongside it; Phase 3 needs both.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Runtime Port and Walking Skeleton | 10/10 | Complete    | 2026-10-06 |
| 2. Thread Spike | 8/8 | Complete    | 2026-10-09 |
| 3. Real Helical Thread | 7/7 | Complete    | 2026-10-11 |
| 4. ISO Hex Bolts and Screws | 17/17 | Complete    | 2026-10-12 |
| 5. Hex Nut and Kernel Pair Proof | 4/18 | In Progress | - |
| 6. Printed Pair Acceptance | 0/TBD | Not started | - |
| 7. Operability Re-sweep | 0/TBD | Not started | - |
