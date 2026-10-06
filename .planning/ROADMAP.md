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
- [ ] **Phase 2: Thread Spike** - a pre-registered measurement picks the thread construction, volume estimator and turn cap before any thread field exists
- [ ] **Phase 3: Real Helical Thread** - the bolt kind carries a real ISO 68-1 helical thread, right- or left-hand, behind a postcondition gate
- [ ] **Phase 4: ISO Hex Bolts and Screws** - ISO 4014 and 4017 presets from cited, tested table rows fill explicit mm fields; a traceable info panel for the bolt
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

**Plans**: TBD

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

**Plans**: TBD
**UI hint**: yes

### Phase 4: ISO Hex Bolts and Screws

**Goal**: A user picks "M6 × 20, ISO 4017" (or an ISO 4014 size and length) and gets a hex head bolt or screw whose explicit millimetre fields were filled from a cited, tested table row, with an info panel whose every number traces to a field or a row.
**Mode:** mvp
**Depends on**: Phase 3
**Precondition (owner checkpoint)**: owner holds purchased copies of ISO 4014:2022, 4017:2022, 4032:2023, 262:2023, 724:2023, 965-2:2024. No table row is entered as verified before the owner confirms this (TABL-04).
**Requirements**: THRD-03, TYPE-01, TYPE-02, TABL-01, TABL-02, TABL-03, TABL-04, TABL-05, TABL-06, TABL-07, INFO-03, INFO-05
**Success Criteria** (what must be TRUE):
  1. A user can pick standard + size + length from the valid combinations across M2–M20 per ISO 262:2023 (first-choice sizes, second-choice sizes in brackets, coarse pitch only) on the UI, API and CLI, and get an ISO 4014 bolt (`s`, `e`, `k`, `dw`, `b` by length band, `ls`/`lg`, chamfered point, under-head fillet, product grade A/B) or an ISO 4017 screw threaded to the head up to the standard's 200 mm cap; the parity test is green.
  2. The preset fills explicit mm fields only: the shareable URL carries mm fields, the preset id is metadata, and opening the URL rebuilds the same part without consulting a table (import-linter forbids `params` and `calc.feasibility` from importing `tables` and keeps `tables` a leaf); `thread_length` is filled by the preset (full length for 4017, `b` for 4014) and stays editable.
  3. The UI badge reads "matches ISO 4017 M6 × 20" while the fields equal the row and "custom, based on ISO 4017 M6 × 20" once any field is edited; the designation line shows the ISO designation without a property class.
  4. Every table row carries a typed `Source` (standard, edition, table, column), so a row without one fails mypy, and exactly one pure-data verification test generated from the table; a row marked UNVERIFIED (entered from a preview) is refused by the gate in a release build.
  5. The bolt's info panel numbers (head, shank and thread) come from the kernel-free maths, each traceable to a mm field or a cited, tested row; a value that cannot be computed honestly is a warning and no number; any volume shown is the closed form; where the ISO wrench size differs from the withdrawn DIN equivalent the panel adds a one-line note.

**Plans**: TBD
**UI hint**: yes

### Phase 5: Hex Nut and Kernel Pair Proof

**Goal**: For any bolt a user can get the matching ISO 4032 nut at a chosen radial clearance, see the pair's numbers on the info panel, and get a kernel verdict on whether the pair mates, one that cannot report `proven` when its own control did not fire.
**Mode:** mvp
**Depends on**: Phase 4
**Precondition (owner checkpoint)**: owner holds purchased copies of ISO 4014:2022, 4017:2022, 4032:2023, 262:2023, 724:2023, 965-2:2024. The ISO 4032 and ISO 965-2 rows ship here (TABL-04).
**Requirements**: TYPE-03, TYPE-04, THRD-05, PAIR-01, PAIR-03, PAIR-04, INFO-01, INFO-02, FRNT-06
**Success Criteria** (what must be TRUE):
  1. A user can generate an ISO 4032 hex nut M2–M20 from a preset or mm fields on the UI, API and CLI (`s`, `e`, `m`, `mw`, `dw`, chamfers on both faces), with M2–M4 labelled "informative / historical" in the preset and on the panel; for any bolt the user gets the matching nut, and vice versa, from the same `d`, pitch, hand and clearance; the nut thread and the bolt tip carry lead-in chamfers; the parity test is green with both kinds.
  2. The nut's `clearance` field is radial millimetres, a positive value enlarges the nut's thread while the bolt stays nominal, and no default for it ships before Phase 6 records the printed test; the info panel shows the full INFO-01 set (clearance radial and diametral, resulting nut diameters, engagement in turns) and the 6g/6H limits from ISO 965-2:2024 under the label "limits for a bought part; this model is nominal and not toleranced".
  3. `screw pair` and the solid-package function return `proven | violated | inconclusive` with the control result: a half-pitch axial offset of the same pair must collide or the verdict is `inconclusive`; clearance ≤ 0 is `inconclusive` by definition; right- and left-hand pairs go through the same checks; one size runs in `make verify`, the full grid in a CI job.
  4. The pair proof is not an API endpoint: the API and UI show closed-form flank gaps instead, and import-linter forbids `app` and `pool` from importing the pair module.
  5. STL and STEP downloads come from the same modelled-thread solid; the STL chord deviation is explicit, measured against the clearances the printed test will use, and recorded and cited in a decision entry, with `ControlSurfaceDeflection` on for downloads; the preview may mesh coarser, the numbers may not.

**Plans**: TBD
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
| 2. Thread Spike | 0/TBD | Not started | - |
| 3. Real Helical Thread | 0/TBD | Not started | - |
| 4. ISO Hex Bolts and Screws | 0/TBD | Not started | - |
| 5. Hex Nut and Kernel Pair Proof | 0/TBD | Not started | - |
| 6. Printed Pair Acceptance | 0/TBD | Not started | - |
| 7. Operability Re-sweep | 0/TBD | Not started | - |
