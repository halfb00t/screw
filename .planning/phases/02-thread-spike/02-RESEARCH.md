# Phase 2: Thread Spike - Research

**Researched:** 2026-10-06
**Domain:** pre-registered measurement campaign on helical thread solids (CadQuery 2.8.0 / OCCT via cadquery-ocp 7.9.3.1.1), kernel pair-check falsifiability, mesh budget, quiet-host gating, pre-registration in git
**Confidence:** HIGH on construction, volume and mesh mechanics (re-run this session on the pinned pair); MEDIUM on pair-check behaviour (probe-level: 4 sizes, one hand, c = 0.1); LOW on every ISO value (previews, memory, secondary sites; all labelled UNVERIFIED by D-02/D-08/D-13).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Owner checkpoint: ISO 68-1:2023 before run 1**
- **D-01:** The owner buys and reads ISO 68-1:2023 before the first run, pins the profile (basic or design) and the pin is written into the `02-SPIKE.md` protocol and later into the decision entry. Order: read → pin → pre-register → run. The planner writes this as a manual checkpoint task that opens the phase; no run before it. The read also confirms the profile coefficients the research took from memory (H = (√3/2)·P, crest and root flats) before the section maths is coded. STATE.md's "ISO 68-1 must be read" line is closed by this checkpoint. — **Reversibility:** one-way — every measured row is the pinned profile's section; a later profile change re-runs the whole campaign.

**Grid**
- **D-02:** 15 sizes: M2, M2.5, M3, M4, M5, M6, M8, M10, M12, M16, M20 plus the second-choice M3.5, M7, M14, M18 (TABL-05 ships them in brackets; C3 says the frontier is not monotone, so an unswept size cannot ship under this spike's cap). Coarse pitch per ISO 262 (preview values, UNVERIFIED until Phase 4's row tests).
- **D-03:** Lengths per size: every integer-turn length (L = k·P, k ≥ 1) and every integer-millimetre length, from the smallest of those up to min(10d, 200 mm). A superset of any table the owner later verifies and of what a user can type (THRD-03); catches the integer-turn failures C1 saw first and finds the short-length floor.
- **D-04:** Failure frontier beyond min(10d, 200 mm): step 5 turns up to 250 turns (the research's measured ceiling for sewn twist); stop per size at the first failure or when build + fine mesh exceeds the 30 s INTERIM; record where and why each size stopped. The per-size turn cap in the decision entry is derived from this record.
- **D-05:** Both hands over the full grid on the host. Then one container validity-only pass of the winning construction in the linux/amd64 image (emulation on arm64): validity, solid count and volume outcomes only; timings are labelled emulation and feed no bound. STACK names the kernel pair and the sewing tolerance as the likeliest to differ on linux/amd64; Phase 7 does the timed re-sweep.

**Construction comparison and escape clause**
- **D-06:** Candidates: the sewn twist-section (research favourite, 0/166 failures, volume to 1.2e-5) on the full grid × hands × frontier; one-pipe twist and `cq_warehouse` ruled-surface as reference rows on a size sample; the naive `sweep` + `fuse` as the negative control. The negative control's silent-wrong rows (`isValid()` True, one solid, core missing) are kept as the known-bad input THRD-04's positive-control gate test needs in Phase 3. `cq_warehouse` runs from a scratch venv for the reference rows only and is never added to `pyproject.toml` (PITFALLS M11).
- **D-07:** Segment length: sweep K ∈ {3, 5, 10} on a size sample at the standard max turns and at the frontier; a pre-registered rule picks K (planner writes it in the protocol, e.g. fewest triangles among the K with zero failures and volume inside tolerance); K is then locked for the full grid.
- **D-08:** Each row builds a bare rod and a bare void (the cutter Phase 5's nut subtracts), plus one tip-chamfer-trim row per size at the standard max length to price Phase 4's one remaining fragile boolean (C10: 70 s on one failing sweep row). ISO 4753 is unread, so the chamfer cone angle is a stated protocol input labelled UNVERIFIED; the row is cost evidence, not geometry truth. No head is built: ISO 4014/4017 head rows do not exist yet and a plain hex prism would be an invented dimension (L02).
- **D-09:** Pass bar, pre-registered: 0 hard failures AND 0 silent-wrong rows over the whole allowed grid, both hands. Silent-wrong = precise volume (D-20's estimator) outside the pre-registered tolerance of the closed form, sign included; or solids ≠ 1; or `isValid()` False; or a non-watertight STL.
- **D-10:** Escape clause: any failure or silent-wrong row inside the standard range (either hand) → the spike reports it, Phase 3 is not planned until the roadmap is revised. An over-budget row (build + slower fine export > 30 s INTERIM, or fine STL raw + gzip > 64 MB INTERIM cache budget) → a per-size cap below the standard max, reported in the decision entry as Phase 3's cap-and-warn input; not an escape. Both budgets are INTERIM (Phase 1 D-01); Phase 7 re-measures them. Nothing is tuned toward a pass.

**Pair-check protocol**
- **D-11:** Clearances: c ∈ {0.05, 0.10, 0.15, 0.20} mm radial on the nut for the proof (brackets Phase 6's printed matrix); c = 0 and c = −0.05 as diagnostic rows: c = 0 must read `inconclusive` by definition (what the boolean did is recorded, not trusted); c = −0.05 must show interference near the closed-form estimate (the sensitivity check).
- **D-12:** Poses: 3 screw-motion matched poses (rotate the nut by θ and slide by θ·P/2π — physically identical, seam-shifted) plus 3 half-pitch-offset controls. `proven` only if all 3 matched poses are empty AND all 3 controls are non-empty. Research saw one collision read empty at 2 of 3 slides; pose-dependence of a broken boolean is what is being measured.
- **D-13:** Bodies: a rod piece of length m + 2P versus a plain cylinder blank minus the void; nut height m per ISO 4032:2023 preview per size, UNVERIFIED until Phase 5. The hex adds nothing to a thread proof. Pair grid = size × hand × clearance × poses; bolt length does not enter (engagement is the nut height). M2–M4 heights are in Annex A, not the preview: Claude's discretion on a labelled source.
- **D-14:** Falsifiability rule (SC5): per (size, hand, c > 0), all matched poses empty AND every control non-empty within a pre-registered band of the closed-form estimate (band set in the protocol from the chosen estimator's measured error). A flaky (size, c) cell is recorded and excluded from Phase 5's allowed clearances for that size. A size with no c ≥ 0.05 at which the rule holds at every pose is "not falsifiable for size X" and fires the escape clause. A mixed-hand pair must read `violated` at every size; left-hand pairs are judged by the same rule as right-hand ones.

**Spike home, records, promotion**
- **D-15:** Code lives in `bench/thread_spike/` (a package: kernel-free section maths and closed-form volume, helical rod and void builders, pair check, grid, report). It prints Markdown and exits 1 on a failed verdict (spur `bench/tip_chamfer_spike.py` shape). `bench/` is already under `make lint` and `make typecheck` (mypy `--strict`, L04), so the code meets the gate from day 1; its predicates (grid generation, verdict rules, the quiet-gate decision) are tested in `tests/test_bench.py`; no timing assertion enters the gate.
- **D-16:** Records: `.planning/phases/02-thread-spike/02-SPIKE.md` holds Question, Environment, Method, Predictions and Escape clause (spur `13-LATENCY-INVESTIGATION.md` shape) and is landed before run 1; `bench/RESULTS.md` gets a `## Thread spike (Phase 2)` section with every run's verbatim output, host state and run id (spur "Tooth-tip chamfer spike" shape); `02-SPIKE.md`'s Results and Verdict cite run ids and re-type no numbers. The new decision entry cites `bench/RESULTS.md` run ids.
- **D-17:** `bench/quiet.py`: `wait_quiet(bar=1.5, samples=3, interval=30, cap=900)` returns decisive / non-decisive plus timestamped readings; every spike run calls it and prints the load at start AND at end, each labelled by the time it was read (spur WR-07). A non-decisive release is recorded as such and never retried toward a pass. The 1.5 bar is spur D-05's convention on the same 12-core host class; a host with an open agent session idles near 2.0, so runs happen with agents closed or read non-decisive.
- **D-18:** The builder is written to be moved: the maths is shaped like the future `calc/thread.py` (kernel-free, the oracle) and the builder like `solid/helical.py`; Phase 3 moves them into `src/` unchanged where possible and the spike imports them back (spur 11-05: what was measured is what ships).

**Landing**
- **D-19:** Two PRs, a deliberate exception to HOW_TO_DEVELOP's one-PR-per-phase, recorded here. PR 1: `bench/quiet.py`, the runnable `bench/thread_spike/` scaffold, `02-SPIKE.md` protocol, tests — reviewed by the other CLI (predictions and escape clause before any data exists) and landed via `make pr.land` before run 1. PR 2: the runs, `bench/RESULTS.md`, `02-SPIKE.md` Results/Verdict, the decision entry, roadmap/state updates. PR 1 is on `gsd/phase-02-thread-spike`; PR 2's branch is re-cut from `origin/main` after PR 1 lands (planner names it). — **Reversibility:** costly — once PR 1 is on `main`, a change to the protocol is a new PR that visibly post-dates it, which is the point.

Roadmap wording resolved by the discussion (planner: build to this, not to the loose text):
- SC1 "git history shows that order" is met by landing the protocol as its own PR before run 1 (D-19); `make pr.land` squashes, so a single PR could not show the order on `main`.
- SC3 "every standard length" is met by a superset (every integer mm and every integer-turn length up to min(10d, 200 mm), D-03), because the ISO 4017 length series is unverified until Phase 4 and a user can type any mm length.
- SC4 "pinned after the standard was read": the read happens *before* run 1, not after the campaign (D-01), because the section the spike builds depends on the profile.

### Claude's Discretion
- **D-20:** The volume-estimator selection rule and tolerance band. Candidates: `BRepGProp.VolumeProperties_s(shape, props, 1e-6, False, False)` and the STL's signed tetrahedron volume (both within 0.1 % in research; default `Volume()` is 15–21 % off on some constructions). The protocol states the rule before run 1 (error vs the closed form across the grid, then cost).
- The mesh-budget sweep design: deviation presets expressed as a fraction of thread depth (5H/8) with spur's absolute INTERIM presets as reference rows; triangle count, mesh seconds, peak RSS, STL bytes, STEP bytes and seconds, and the L19 gzip table via `bench.export_cost`'s rule; sized from the research numbers (sewn twist fine mesh ≤ 1 s per row, so the full grid is affordable; the planner decides whether gzip runs per row or per size max).
- Container-pass mechanics (D-05): mount `bench/` into the runtime image or add a dev stage; the image is the runtime closure only (L08).
- The labelled source for M2–M4 nut heights (D-13) and the sewing tolerance (research 1e-4) and tip-chamfer angle (D-08) as protocol inputs.
- Whether `BRepAlgoAPI_Common.HasErrors()/HasWarnings()` through OCP is read as a diagnostic column in the pair check (untested in research; informative, not a verdict input).
- Reuse of `bench.machine_facts()`, `bench.build_time.Timing`'s worst-request rule and `bench.export_cost`'s gzip table where they fit; a `make bench.thread` target in the Makefile's bench family.
- Run ids, the exact Markdown layout of the report, and the sample sizes for D-06/D-07.

### Deferred Ideas (OUT OF SCOPE)
- Design (rounded-root) profile as a later option if the owner pins basic in D-01.
- STEP importer behaviour in FreeCAD, Fusion, SolidWorks, Onshape — unmeasured, not this phase.
- The open `blocker` debt item (collapsed thin solid served as 200) — its trigger is the `/gsd-quick` PR after the Phase 1 close, outside Phase 2.
- Phase 7 reuses `bench/quiet.py` and the Phase 2 grid as the fixed threaded corpus (`bench/README.md`'s corpus rule).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INFR-03 | The thread spike is pre-registered (method, predictions, escape clause committed before the first run), run behind a quiet-host gate with load readings labelled by when they were taken, and its result is a decision entry — construction chosen, volume estimator chosen, turn cap per size — before any thread field exists. | Protocol Inputs table (what to pre-register and recommended values); Pattern 6 (machine-checkable pre-registration guard); Pattern 4 and Code Example 2 (quiet gate as a pure, testable function); Standard Stack + Pattern 1-3, 7 (how each of the four questions is measured); Validation Architecture (what the gate tests and what it must not); Open Questions 1-3 (outcomes the protocol must be ready for). |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

`./CLAUDE.md` is a symlink to `AGENTS.md`; read this session. Directives that bind this phase:

- `make verify` is the gate (ruff, mypy `--strict`, import-linter, unfinished-work scan, pytest); state the command and the result line; no Docker needed.
- `Any` is not written (L04); a genuinely untyped value is `object`, narrowed where used. `bench/` is inside the mypy run: `$(PY) -m mypy src tests docker bench scripts` [VERIFIED: Makefile:59-60].
- Comments carry the measurement or the constraint (spur standard); the `no-fake-done` scan fails on the markers `(TODO|FIXME|XXX|HACK|NotImplementedError)` in `*.py`, `*.js`, `*.sh` (`git grep -nwE`) [VERIFIED: Makefile:76-83]. Keep those words out of spike code and comments.
- The thread-maths module must never import `cadquery`; its import-boundary contract lands in the same commit as the module.
- Vendor types stop at their boundary; `cadquery` objects do not escape the solid module (for the spike: the kernel module of `bench/thread_spike/`, and D-18 moves it to `solid/` later).
- A number the tool prints is a number someone will cut metal to; no plausible number (L02). Every UNVERIFIED ISO preview value stays labelled wherever it appears.
- New dependency = decision, ask first (`docs/CODING_VALUES.md` § Dependencies). Prefer stdlib (`struct` for STL, not a mesh library).
- Measure before you claim; measurements ship with the number, the workload and the load.
- Non-blocking ideas/debt go to `docs/ideas/` / `docs/tech_debt/active/` (state in the final reply whether any was filed).
- Commit messages: Conventional Commits; never carry a GitHub Actions skip token (commit-msg hook refuses; `make pr.land` refuses a PR title/body with one) [CITED: docs/architecture/decision_log.md L08].
- Start file-changing work through a gsd entry point; no direct repo edits outside a gsd workflow.
- Two PRs in this phase is a recorded exception (D-19), not a precedent.

## Summary

The phase is a measurement campaign, not product code, and the sewn twist-section is the construction to test. Re-running STACK's reference implementation on the pinned pair this session reproduced its headline: valid, one solid, volume within 7.6e-6 of the closed form (precise estimator) on 576 of 576 rows (M2.5, M3.5, M8; both hands; every D-03 length; K=3 and K=5), and the naive sweep + fuse reproduced the silent-wrong class (`isValid()` True, one solid, volume 24-27 % of the closed form on M6 L10 and M2 L6; an exception `Null TopoDS_Shape` on M6 L20 and L40). One-pipe twist reproduced sign inversion at 160-171 turns (precise and default volume both read −1.0000 of the closed form, `isValid()` True) and sewn K=5 fixed all three. The closed-form area matches the kernel to a few 1e-6 and is also the right oracle for the pair check: the half-pitch control interference and the c = −0.05 sensitivity value have closed forms (a one-pitch numeric integral) that matched the kernel to 4-5 significant figures every time the kernel returned a non-empty result.

The most important finding for planning is about the pair check. The control (half-pitch offset, c = 0.1) returned an empty result, a false negative, in 21 of 72 probe readings (29 %): 12 combinations of size (M2, M6, M10, M20) and K (3, 5, 10) × 6 poses; 10 of the 12 combinations had at least one false-empty pose, no K was clean across sizes, and the failing poses differ by size and K. Every non-empty reading agreed with the closed form; no matched pose ever read non-empty at c = 0.1 (42 readings). Neither fuzzy values (1e-5, 1e-4) nor serial execution changed a false-empty. So D-14's rule ("all controls non-empty") is outcome-determined by which three poses are pre-registered, and the likely honest verdict of the spike is "not falsifiable as specified" for many cells. The protocol must state its pose list as a deterministic rule before run 1, state this prior evidence among its Predictions, and be ready for the escape clause (Open Question 1).

Budget findings: at spur's INTERIM `fine` preset the mesh of a threaded part is large and driven by linear deflection (triangles scale about 1/δ): M20 L200 (80 turns) is 3.29 M triangles, 164 MB raw, 76 MB gzip-1, 2.26 GB peak RSS in a fresh child; raw + gzip already exceeds the 64 MB INTERIM cache budget near L=53 mm for M20. Over-budget rows (a per-size cap) are therefore expected from budget, not from construction failure. Sewn K trades STL triangles against STEP size (K=3: fewest triangles, 82 vs 50 faces and 3.57 vs 2.93 MB STEP at M6 L60), so D-07's rule needs a pre-registered secondary criterion.

**Primary recommendation:** Build `bench/thread_spike/` as a kernel-free maths + verdict core (exact rational grid, closed-form area and interference integral, pure predicates, quiet gate) tested in `tests/test_bench.py`, plus a kernel module (STACK's sewn twist parameterised by K, `BRepGProp` eps estimator, stdlib STL check) driven by a persistent JSON-lines worker subprocess per block with a hard timeout; pre-register pose list, tolerances and the variant-rule list in `02-SPIKE.md`, land that PR first, and make every run print and refuse on a machine-checked protocol-landed header.

## Architectural Responsibility Map

This is bench tooling, not a web app; "tier" here means the process/module layer that owns a capability.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Grid generation, ISO profile numbers, closed-form area and interference integral, verdict predicates, quiet-gate decision | Kernel-free module (`bench/thread_spike` maths + verdict, `bench/quiet.py`) | Tests (`tests/test_bench.py`) | Runs in the gate with no kernel; it is the oracle the kernel is judged against (D-18, Architecture Q4) |
| Thread solids (rod, void, nut, naive negative control, tip trim), volume estimators, STL check, pair boolean | Kernel module (`bench/thread_spike` helical + pair + measure) | Worker subprocess | Only place that imports `cadquery`/`OCP`; vendor objects stop at the row record (plain floats/ints) |
| Per-row isolation, hard timeout, crash classification, RSS | Runner/worker process tier | Fresh child for RSS rows | OCCT can segfault (exit 139 observed) and has no cooperative cancel; one crash must be one recorded row, not a lost campaign |
| Quiet gate + load labelling | Host tier (`bench/quiet.py`) | Run header in each report | Load is a host property; every reading carries the time it was read |
| Pre-registration, order proof | Git/Markdown tier (`02-SPIKE.md`, PR 1 then PR 2) | Run header guard | SC1 is a property of `main`'s history, not of a file |
| linux/amd64 validity pass | Container tier (`docker run --platform linux/amd64`, `bench/` bind-mounted) | — | Image is the runtime closure only (L08); timings there are emulation |
| Decision entry (L11) | Docs tier (`docs/architecture/decision_log.md`) | RESULTS.md run ids | Single source of locked decisions; next free id is L11 [VERIFIED: decision_log.md:264 `## L10 — The owner-vetted dev tools are pinned ...` is the last entry] |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `cadquery` | 2.8.0 | Solids, booleans, STL/STEP export | Locked pair (L01, L06); imported OK in `.venv` this session [VERIFIED: `.venv/bin/python` printed `2.8.0`] |
| `cadquery-ocp` | 7.9.3.1.1 | `BRepOffsetAPI_MakePipeShell`, `BRepBuilderAPI_Sewing`, `BRepGProp`, `BRepAlgoAPI_Common` | Locked pair; `importlib.metadata.version` printed `7.9.3.1.1` [VERIFIED: this session]. Latest on PyPI is 8.0.1.0.0 (published 2026-10-05) and cadquery 2.8.0 excludes it [CITED: STACK.md § Version Compatibility]; do not bump |
| Python | 3.12.13 | Runtime | `.venv/bin/python --version` [VERIFIED]; 3.12 only (L01) |
| stdlib | — | `struct` (STL), `gzip`, `resource` (RSS), `fractions` (grid), `subprocess` + `json` (worker), `statistics`, `os.getloadavg`, `datetime` | CODING_VALUES § Dependencies: prefer stdlib. `numpy` is in the runtime closure but is not a declared dependency; do not rely on it (`requirements.txt` carries `numpy==2.5.3` only as a transitive of `cadquery`) |

### Supporting (reuse, do not re-write)
| Existing piece | Location | Use |
|----------------|----------|-----|
| `machine_facts()` | `bench/__init__.py` | CPU/arch/RAM line in every run header |
| `stl_size(data)` | `bench/build_time.py:78` | byte + triangle count with the length-vs-header refusal (L02) |
| `Timing.worst_request` rule | `bench/build_time.py:45` | request = build + the slower export (spike adds the trim step, as spur's `CostRow.request_s` does) |
| `GZIP_LEVELS`, `gzip_rows`, `select_gzip_level`, `maxrss_bytes` | `bench/export_cost.py:47,82,140,76` | L19 table and rule; `GZIP_LEVELS: tuple[int, ...] = (1, 6, 9)` [VERIFIED: export_cost.py:47]; `ru_maxrss` is bytes on Darwin, KiB elsewhere |
| `label()` | `bench/corpus.py` | keeps kernel-free label text; do not import `bench.build_time` from a kernel-free module (it imports `screw.solid`) |
| `TESSELLATION` | `src/screw/solid/__init__.py:41` | reference presets: `TESSELLATION: dict[str, tuple[float, float]] = {"preview": (0.08, 0.5), "fine": (0.01, 0.1)}` [VERIFIED]; mesh the shipped way: `shape.copy().exportStl(str(path), tolerance=tol, angularTolerance=ang, ascii=False, relative=False)` [VERIFIED: solid/__init__.py:128-129] |

### Reference-only (scratch, never in `pyproject.toml`)
| Package | Version | Purpose | Notes |
|---------|---------|---------|-------|
| `cq_warehouse` | 0.8.0, commit `daa46507ecc429c0e2dce11d9d5ffd09b12a42af` | ruled-surface reference rows (D-06) | Installed with `pip install --no-deps --target <scratch> git+https://github.com/gumyr/cq_warehouse.git` in 6 s and imported by the project's `.venv/bin/python` with `PYTHONPATH=<scratch>`; no change to `.venv` [VERIFIED: this session]. `IsoThread(major_diameter=6, pitch=1.0, length=20, external=True, end_finishes=("fade","fade"))` builds in 0.18 s; fused to a core it is valid, 1 solid, default `Volume()` 487.9 mm3 against closed form 459.2 (+6.3 %) [VERIFIED: probe R9] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Persistent worker subprocess per block | `concurrent.futures.ProcessPoolExecutor` (as `screw.pool`) | Pool needs the same hard-kill-on-timeout logic and breaks a whole pool on a segfault; a hand-rolled JSON-lines child is ~60 lines, stdlib, and one dead child is one row |
| Fresh child per row | Persistent worker | `import cadquery` costs 2.9-3.7 s per process under load [VERIFIED: probe R1]; at 7000+ builds that is hours of pure import. Use fresh children only where per-row RSS matters (Pitfall 5) |
| `import-linter` contract for the kernel-free module | AST test in `tests/test_bench.py` | Both work. Contract is the project's own mechanism (CODING_VALUES § Coupling); it needs `root_packages = ["screw", "bench"]` (see Pattern 8, verified) |
| `psutil` RSS sampling | `resource.getrusage` in a fresh child | `psutil` is a new dependency (ask first) and sampling undercounts spikes (the existing `bench-memory-sampling-is-too-coarse` debt item) |

**Installation:** nothing new. The scratch reference install (planner: gate behind `checkpoint:human-verify`, see audit):
```bash
PIP_CONSTRAINT=requirements.txt .venv/bin/python -m pip install --no-deps \
  --target "$SCRATCH/cqw" "git+https://github.com/gumyr/cq_warehouse.git@daa46507ecc429c0e2dce11d9d5ffd09b12a42af"
# run reference rows: PYTHONPATH="$SCRATCH/cqw" .venv/bin/python -m bench.thread_spike ...
```
**Version verification:** versions above were read from the live `.venv` and `git ls-remote`/`direct_url.json` this session, not from training data.

## Package Legitimacy Audit

`gsd_run query package-legitimacy check --ecosystem pypi cq_warehouse cadquery cadquery-ocp` was run this session.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| `cq_warehouse` | PyPI: not present (`does-not-exist`); GitHub only | repo since 2021 (`thread.py` header "date: November 11th 2021") | n/a | github.com/gumyr/cq_warehouse (Apache-2.0, `LICENSE` 11358 bytes in the installed dist-info) | [SLOP] by the seam (no PyPI distribution) | **Locked by D-06 as scratch-only reference rows, so not removed.** The verdict is the expected consequence of a git-only package (STACK: PyPI JSON 404), not a hallucinated name. Planner MUST add a `checkpoint:human-verify` before the install and pin the commit `daa46507ecc429c0e2dce11d9d5ffd09b12a42af`. Never added to `pyproject.toml`/`requirements.txt`; no code copied (licence file read; copying would need its NOTICE) |
| `cadquery` | PyPI | published 2026-06-21 (2.8.0) | unknown to seam | github.com/CadQuery/cadquery | [SUS] (`unknown-downloads`) | Already pinned and installed (L06); no new install |
| `cadquery-ocp` | PyPI | newest release 2026-10-05 (8.0.1.0.0) | unknown to seam | none listed | [SUS] (`too-new`, `no-repository`) | The seam looked at the newest release; the pinned 7.9.3.1.1 is what is installed (L06). No bump |

**Packages removed due to [SLOP] verdict:** none (cq_warehouse kept by locked decision, see above).
**Packages flagged as suspicious [SUS]:** `cadquery`, `cadquery-ocp` (already-installed pins; no new install, no checkpoint beyond the existing L06/L10 policy).

## Architecture Patterns

### System Architecture Diagram

```
 owner reads ISO 68-1:2023 ──► pin profile (basic|design) ──► 02-SPIKE.md protocol
                                                    │            (inputs, predictions, escape clause,
                                                    ▼             pose list, tolerances, variant rules)
                                      PR 1: scaffold + quiet.py + tests ──► other-CLI review ──► make pr.land
                                                    │                         (squash on main = the order)
                                      branch re-cut from origin/main (PR 2)
                                                    ▼
 run (one block = size × hand [× preset subset]) ─────────────────────────────────────────────────────┐
   guard: protocol text before "## Results" == origin/main's ──► refuse (exit 2) otherwise           │
   wait_quiet(1.5,3,30,900) ──► readings[time,load] ──► header: HEAD, protocol blob hash, kernel,     │
                                                         host, load@start(time)                      │
   exact-rational grid ──► worker subprocess (JSON lines, hard timeout, respawn on death)             │
        row: build rod/void(K) ─► postcondition { solids, isValid, precise vol, default vol, closed } │
             ─► STL ladder: mesh a COPY ─► bytes/tris ─► gzip-1 ─► watertight + signed vol (outside   │
                the timed region and outside the RSS reading) ─► STEP bytes/s ─► [tip-trim row]       │
        pair cell: nut = blank.cut(void(c)); rod m+2P; place(θ, slide) ─► common ─► precise vol       │
                   ─► matched/control table vs closed-form interference                               │
   load@end(time, "includes this run's own load") ─► JSONL (raw) + Markdown (verbatim) ──────────────┘
                                                    ▼
 kernel-free verdict predicates ──► RESULTS.md (run ids) ──► 02-SPIKE.md Results/Verdict ──► L11
 container pass: docker run --platform linux/amd64 --entrypoint python -v bench:ro … validity rows only
```

### Recommended Project Structure
```
bench/
├── quiet.py                 # wait_quiet + Reading/QuietResult; kernel-free; D-17
├── thread_spike/
│   ├── __init__.py
│   ├── maths.py             # kernel-free: pitch table (UNVERIFIED), profile, section_area,
│   │                        #   interference_area, exact grid, turns; the future calc/thread.py
│   ├── verdict.py           # kernel-free: silent-wrong, pass bar, escape clause, K rule,
│   │                        #   estimator rule, pair rule, budget/frontier rules, protocol guard
│   ├── helical.py           # kernel: section, twist, thread(K), rod, void, naive, trim; the
│   │                        #   future solid/helical.py (only module that imports cadquery/OCP
│   │                        #   with measure.py and pair.py)
│   ├── measure.py           # kernel: GProp eps volume, default volume, STL write/check, STEP
│   ├── pair.py              # kernel: nut, placement, common, diagnostics
│   ├── worker.py            # JSON-lines child: one request line in, one record line out
│   └── __main__.py          # blocks, run header, Markdown report, exit 1 on failed verdict
└── RESULTS.md               # gains "## Thread spike (Phase 2)"
tests/test_bench.py          # predicates only (D-15); one cheap real-kernel smoke row
Makefile                     # bench.thread target next to bench.build/bench.export
```

### Pattern 1: Exact-rational grid
**What:** Generate lengths with `fractions.Fraction` (pitches `Fraction(9, 20)` etc.), de-duplicate exactly, convert to float only at the builder boundary; integer-turn status is `(L / P).denominator == 1`, never a float comparison.
**When to use:** the D-03 grid, the D-04 frontier lengths, and Phase 7's reuse of the same corpus.
**Why:** float `k*P` drifts: 168 of 3000 `(k*P)/P != k` for the 12 coarse pitches in range [VERIFIED: probe R12, e.g. `0.4*3 = 1.2000000000000002`, `/0.4 = 3.0000000000000004`]. Also dedupes coincident lengths exactly (M2.5: integer mm that are integer turns are 9 and 18).
**Counts (planner: pin them in a test, Phase 7 reuses the grid):** 1790 lengths per hand, 3580 rod rows; per size M2 60, M2.5 78, M3 60, M3.5 82, M4 92, M5 100, M6 60, M7 70, M8 128, M10 133, M12 171, M14 140, M16 160, M18 216, M20 240 [VERIFIED: scratch `grid.py`, using pitches below and reading D-03's "from the smallest of those" as `min(P, 1 mm)`; see Open Question 3].
**Turns at the standard max (min(10d, 200 mm)):** M2 50, M2.5 55.6, M3 60, M3.5 58.3, M4 57.1, M5 62.5, M6 60, M7 70, M8 64, M10 66.7, M12 68.6, M14 70, M16 80, M18 72, M20 80 [VERIFIED: same script].
**Coarse pitches (preview, UNVERIFIED until Phase 4):** M2 0.4, M2.5 0.45, M3 0.5, M3.5 0.6, M4 0.7, M5 0.8, M6 1.0, M7 1.0, M8 1.25, M10 1.5, M12 1.75, M14 2.0, M16 2.0, M18 2.5, M20 2.5 [CITED: en.wikipedia.org/wiki/ISO_metric_screw_thread, fetched this session; secondary source, MEDIUM; the protocol labels them UNVERIFIED as D-02 says].

### Pattern 2: One row = the postcondition Phase 3 will ship
**What:** per row record `solids`, `isValid()`, precise volume (`BRepGProp.VolumeProperties_s(shape.wrapped, props, 1e-6, False, False)`), default `Volume()` (known-bad reference column), closed form `A(c)·L`, and the **signed** relative error `v/A − 1`. Classify: `ok`, `silent_wrong` (solids ≠ 1 or invalid or |rel err| > T_pass or sign wrong or non-watertight STL), `failure` (exception), `timeout`, `worker_died`.
**Evidence:** the overload and its semantics were read from the OCP docstring: `VolumeProperties_s(S, VProps, Eps: float, OnlyClosed: bool = False, SkipShared: bool = False) -> float`, "Parameter Eps sets maximal relative error of computed mass (volume) for each face ... WARNING: if Eps > 0.001 algorithm performs non-adaptive integration" [VERIFIED: `VolumeProperties_s.__doc__`]. CONTEXT's `(shape, props, 1e-6, False, False)` is this overload.
**Closed form (matches STACK, re-derived this session):** `A = pi/8 ro^2 + pi/4 rr^2 + 5pi/24 (ro^2 + ro rr + rr^2)`, `ro = d/2 + c`, `rr = d/2 - 5H/8 + c`, `H = (sqrt(3)/2) P`. Angular spans check: crest π/4, two flanks 5π/8 each, root π/2, total 2π. The transverse section is the axial profile wrapped (θ = 2πz/P), so for any single-start profile `A = (π/P) ∫ r(z)² dz`; a design-profile root arc changes only the integrand (Open Question 2).
**Measured over every D-03 length, both hands (probe R10):** M2.5, M3.5, M8, K=3 and K=5, 576 rows per K: 0 invalid, 0 multi-solid, max |rel err| precise (eps 1e-6) 7.6e-6 (M2.5 K=3), default `Volume()` 2.7e-5. So on the sewn twist the default estimator is also fine; the estimator question is decided by the other constructions (cq_warehouse default +6.3 %, probe R9).

### Pattern 3: Persistent worker, one JSON line per row, classified outcomes
**What:** parent spawns `python -m bench.thread_spike.worker`, writes a request line, reads one record line with a hard timeout; on timeout it `kill()`s and respawns and records `timeout`; a non-zero/negative return code (segfault shows as exit 139 / signal 11) is `worker_died`; only a Python exception inside the row is `failure`. JSON only (never pickle/eval).
**Why:** an OCP segfault was provoked this session (Pitfall 4) and OCCT has no cooperative cancel. A timeout under a non-decisive gate is not a construction failure (Open Question 6).
**Hard timeouts (protocol inputs, [ASSUMED]):** row 120 s (4 × the 30 s INTERIM budget, so over-budget rows are measured rather than killed); pair cell 600 s (STACK saw 16-121 s on full M20 bodies).

### Pattern 4: Quiet gate as a pure function with injected effects
**What:** `wait_quiet(bar, samples, interval, cap, *, read, sleep, now, clock)` returns `QuietResult(decisive, readings)`; every `Reading` carries `utc` taken at read time. Semantics are spur's own: release when the last `samples` readings are all strictly under `bar`, then check the cap [CITED: spur `13-latency-bar/investigation/session.py:40-45,296-319`: `QUIET_BAR = 1.5`, `SAMPLE_INTERVAL_S = 30`, `QUIET_RUN = 3`, `QUIET_CAP_S = 900.0`; release test `all(s["load1"] < QUIET_BAR for s in recent)`]. spur read `sysctl -n vm.loadavg`; `os.getloadavg()[0]` is the same 1-minute figure and also exists in the Linux container.
**Verified behaviour (Code Example 2):** three readings 1.4 release decisively; an exact 1.5 resets the run; never-quiet at cap 900 / interval 30 returns non-decisive with **31** readings (t = 0, 30, ..., 900).
**Run-end reading caveat:** the 1-minute load at the end of a multi-minute OCCT run includes the run itself (and `exportStl` defaults to `parallel=True` [VERIFIED: cadquery `Shape.exportStl` signature], so meshing loads every core). Label the end reading "includes this run's own load"; decisiveness is decided by the release, as in spur.

### Pattern 5: Pair cell = nut body, rod piece, screw-motion placement, closed-form oracle
**What (all of it exercised this session, probe R4-R8):**
```
rod   = thread(d, P, m + 2P, c=0, hand).translate(0, 0, -P)          # covers [-P, m + P]
void  = thread(d, P, m + 2P, c,   hand).translate(0, 0, -P)
nut   = cylinder(radius=d, height=m).cut(void)                        # plain blank, D-13
place(nut, θ, extra) = nut.rotate(z, degrees(θ)).translate(0, 0, sign(hand)·θ·P/2π + extra)
                                                                      # sign = -1 for left hand
matched: extra = 0    control: extra = P/2    interference = vol(common(rod, placed nut))
```
**Hard constraint:** the rod must cover the nut at every pose or the engaged length shrinks and the control volume falls below the closed form (silently). With pad P the total slide must stay ≤ P: keep θ ∈ [−π, π] (matched slide ≤ P/2, control ≤ P). I broke this myself with θ = 4, 5, 6 (volumes 11.89, 11.52, 11.14 instead of 12.2131) [VERIFIED: probe R6].
**Closed forms (kernel-free, numeric integral over one pitch, 4e5 midpoints):** `interference = m · ∫ ½ max(0, r_b(θ)² − r_v(θ+φ)²) dθ`, with `r_v = r_b + c` and `φ = π` for the half-pitch control, `φ = 0` for matched. M6, m = 5.2: half-pitch c = 0.1 → 12.213 (kernel 12.2131); c = 0.05 → 14.1335; c = 0 → 16.1427 (kernel 16.1428); matched c = −0.05 → 4.3627 (kernel 4.3627, 4.3626, 4.3629 at three poses); half-pitch c = −0.05 → 18.2374 (kernel 18.2374) [VERIFIED: probes R4, R5]. At other sizes the non-empty control agreed with the closed form to ≤ 1e-5 relative (M10 54.968-54.969 vs 54.969; M20 429.629-429.632 vs 429.631) [VERIFIED: probe R7].
**Left hand and mixed hand:** LH rod + LH nut with the opposite slide sign read matched-empty / control 12.2131 exactly like RH [VERIFIED: probe R4]. RH rod + LH nut read non-empty at all 6 poses (6.5-6.9 mm3, 10-12 solids, varying with θ), i.e. `violated` is easy to see; do not compare those volumes to a closed form.

### Pattern 6: Pre-registration that a machine can check
**What:** the run header prints `git hash-object` of `02-SPIKE.md` and the commit that last touched it, and `__main__` refuses (exit 2) unless (a) the file is clean in the working tree, (b) `git merge-base --is-ancestor <that commit> origin/main` succeeds (after `git fetch origin main`), and (c) the text before the first `## Results` heading equals `git show origin/main:<path>` up to the same heading. PR 1 must therefore land the protocol with a stub `## Results` heading as the boundary. All three git commands work on this repo: on this unlanded branch the ancestor test exits 1, as it must [VERIFIED: this session, `git merge-base --is-ancestor` on `02-CONTEXT.md`'s last commit]. Squash merges keep this valid because the check uses `origin/main`'s own commit after the squash, not the branch commits.
**Predicate lives in `verdict.py`** with the git output injected so `tests/test_bench.py` covers it without a repo.

### Pattern 7: Mesh ladder measured the shipped way
**What:** per row and per preset, mesh a **copy** through `exportStl(..., ascii=False, relative=False)` into a temp file; record triangles, bytes, mesh seconds, gzip-1 bytes; run the watertight + signed-volume check **after** the timed region and **after** the RSS reading; STEP via `shape.exportStep(path)`, record bytes and seconds. Presets: spur's two absolute (INTERIM) as reference columns, plus a ladder as fractions of the thread depth `h = 5H/8 = 0.5413 P` (0.217 mm at M2 to 1.353 mm at M20).
**Measured (probe R2, R3, R11, loaded host, indicative):** triangles scale about with 1/δ and barely with the angular tolerance at small δ (M20 L200: (0.05, 0.5) 605 450; (0.05, 0.1) 709 452; (0.01, 0.5) 3 203 406; (0.01, 0.1) 3 286 664). gzip-1 ratio 0.45-0.48 on M2, M6, M20 STLs; level 6/9 gave 0.444 on M6 L60 (4.9 % smaller than level 1, so L19's ≥ 10 % clause would keep level 1). STEP is about linear in turns for K=5: M6 L60 2.93 MB, L250 12.38 MB; M20 L200 5.57 MB, L625 17.59 MB; 0.05-0.31 s.
**Mesh volume is a deflection-limited number, not a 1e-4 estimator:** signed STL volume read −1.31e-2 at (0.05, 0.5) and −2.8e-3 at (0.01, 0.1) on M6 L20; −5.55e-3 at (0.01, 0.1) on M2 L20; −7.2e-4 on M20 L200 [VERIFIED: probes R1, R2]. It is inscribed (always low), roughly mean sag × S/V. Use it as a sign/watertightness/gross check with a deflection-derived band; the gate-grade estimator is `BRepGProp`.

### Pattern 8: Kernel-free guarantee for `bench/thread_spike/maths.py`
**What:** add `"bench"` to import-linter's `root_packages` and a forbidden contract (`source_modules = ["bench.thread_spike.maths", "bench.thread_spike.verdict", "bench.quiet"]`, `forbidden_modules = ["cadquery", "OCP"]`). Proven this session with a scratch config: `bench.corpus` KEPT, and `bench.build_time` BROKEN with the chain `bench.build_time -> screw.solid (l.29)`, `screw.solid -> cadquery (l.24)` [VERIFIED: `lint-imports --config <scratch>`]. Current config is `root_package = "screw"` [VERIFIED: pyproject.toml:142], so the edit is needed and must be re-run through `make lint-imports` in the same commit as the module (CODING_VALUES § Coupling). Whether adding `bench` perturbs the four existing contracts was not run against the real `pyproject.toml`: [ASSUMED] no effect (they all name `source_modules = ["screw"]` or `screw.*`).

### Anti-Patterns to Avoid
- **Floats for grid and integer-turn tests:** drift (Pattern 1).
- **`isValid()` or default `Volume()` as a verdict:** `isValid()` is True on the naive core-missing rows and on inverted solids; default `Volume()` was +6.3 % on cq_warehouse and −1.0024 of the closed form on an inverted one-pipe.
- **A pose list chosen after seeing data:** the control verdict is pose-determined (Pitfall 3); fix the list in the protocol, record every pose.
- **Reading RSS from a persistent worker as if per row:** `ru_maxrss` is a process high-water mark.
- **A mesh check inside the timed or RSS region:** the pure-Python check costs ~3 µs/triangle and gigabytes at the finest preset.
- **Importing `bench.build_time` from the kernel-free modules:** it pulls `screw.solid` and cadquery.
- **Tuning K, tolerance, poses or timeouts after a result:** each is a protocol input.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| STL triangle/byte count | a second parser | `bench.build_time.stl_size` | already refuses length/header mismatch (L02) |
| gzip level table + rule | a new rule | `bench.export_cost.gzip_rows` / `select_gzip_level` | L19's bars are the project's rule; run the full table per size-max rows only (level 9 on a 164 MB STL is minutes) |
| Machine line, `ru_maxrss` units | new helpers | `bench.machine_facts`, `maxrss_bytes` | Darwin bytes vs Linux KiB already handled |
| Exact lengths | float arithmetic with tolerances | `fractions.Fraction` | 168/3000 float mismatches |
| Volume of the kernel solid | default `Shape.Volume()` | `BRepGProp.VolumeProperties_s` eps overload | adaptive, documented per-face relative error |
| STL watertight/volume | a mesh library | stdlib `struct` + weld at 1e-5 mm + directed-edge pairing (PITFALLS probe record) | CODING_VALUES: `struct` to parse an STL. Measured 9.4 s for 3.2 M triangles, 1.3 s for 605 k |
| Thread solid | `Workplane.sweep` + `fuse`, `twistExtrude` as shipped | STACK reference implementation (sewn twist) | the naive path is the negative control, not a candidate |
| Pair-check expected values | hand-typed numbers | `interference_area` integral | matched the kernel to 4-5 significant figures; also the band centre for D-14 |
| Process isolation | threads or in-process loops | worker subprocess | segfault = lost campaign otherwise |

**Key insight:** in this domain the dangerous results look valid. Every defence in the spike (exact grid, closed-form oracle, sign, solid count, controls with closed-form expectations, protocol-before-data) exists because a plausible-looking row can be wrong.

## Runtime State Inventory

Omitted: not a rename/refactor/migration phase (greenfield bench code and records).

## Common Pitfalls

### Pitfall 1: Float grid drift
**What goes wrong:** `k*P` is not exactly an integer number of pitches in floating point; integer-turn rows get mislabelled or dropped and the C1-sensitive rows go unswept.
**Why:** 0.4·3 = 1.2000000000000002 and /0.4 = 3.0000000000000004 [VERIFIED: probe R12]. The reference code's `int(n // SEG_TURNS + 1e-9)` hides the same drift inside the builder.
**How to avoid:** Pattern 1; test the counts above; pass the builder `(float(L), turns as Fraction → float)` and let it use `turns` rather than re-deriving from `L/P`.
**Warning signs:** grid size differs between two runs; an "integer-turn" row whose label is not `denominator == 1`.

### Pitfall 2: Pose slide larger than the rod pad
**What goes wrong:** control volume falls below the closed form (engaged length shrinks) and looks like estimator error or a "flaky cell".
**Why:** rod length `m + 2P` covers slides up to P only.
**How to avoid:** θ ∈ [−π, π] (Pattern 5), or pad the rod by 1.5 P and say so in the protocol; assert in code that `rod.zmin ≤ nut.zmin` and `rod.zmax ≥ nut.zmax` for every placed pose.
**Warning signs:** a control non-empty but not within the band while θ is large.

### Pitfall 3: The control is pose-, size- and K-dependent, so D-14's rule is outcome-set by the pose list
**What goes wrong:** with c = 0.1 and the half-pitch control, the boolean returns an empty result with no error for the same physical configuration (all poses are physically identical by screw symmetry; non-empty readings agree to 5 figures, so the empty ones are wrong).
**Evidence (probes R4-R8, host load 2-18, M-nut heights from preview/protocol inputs, RH rod+nut, plain blank radius d, rod pad P):**

| Size (m) | K=3 false-empty / 6 | K=5 | K=10 |
|----------|---------------------|-----|------|
| M2 (1.6) | 2 (θ 0.5, 2.0) | 0 | 2 (θ 1.0, 2.0) |
| M6 (5.2) | 0 | 4 (θ 0, 0.1, 0.3, 0.5) | 3 (θ 0, 0.1, 0.5) |
| M10 (8.4) | 2 (θ 0.1, 1.0) | 1 (θ 0.1) | 1 (θ 1.0) |
| M20 (18) | 1 (θ 0.1) | 3 (θ 0.1, 0.3, 0.5) | 2 (θ 0, 0.3) |

Poses θ ∈ {0, 0.1, 0.3, 0.5, 1.0, 2.0} rad. 21 of 72 control readings were false-empty (29 %); 10 of 12 (size, K) combinations had at least one. A finer M6 K=5 scan: false-empty at θ ∈ {0, 0.05, 0.1, 0.2, 0.3, 0.5}, correct at {−0.6, −0.3, −0.1, 0.4, 0.6, 1.0, 1.5, 2.0, 2.5, 3.0, π}; perturbing the slide by 1e-3 or 1e-2 did not change a false-empty; fuzzy value 1e-5 / 1e-4 and `SetRunParallel(False)` did not either (K = 5 and 10, θ = 0 and 0.1). No matched pose at c = 0.1 ever read non-empty (42 readings: 24 in the size/K table, 6 for RH and LH M6, 12 in the M6 scan). At c = 0 the matched poses returned garbage (θ = 1.0: vol −0.0000 in 1 solid, 30.0 s; θ = 2.5: 3 solids, 31.8 s; θ = 0: empty) [VERIFIED: probes R4-R8].
**Consequence:** a fixed 3-pose control rule is passed or failed by pose choice. If P(false-empty) ≈ 0.3 independently, P(all 3 controls fire) ≈ 0.36 per cell; failures also correlate across c for a given pose (same geometry), so many (size, hand) cells will fail every c and fire D-14's escape clause for those sizes. That is a legitimate spike result, but only if the protocol said so first.
**How to avoid / what to pre-register:** (a) the pose list as a deterministic rule (for example six equally spaced angles inside [−π, π] shifted off zero; the planner picks the rule, the research only requires that it is fixed before run 1, stays inside [−π, π] and is never edited after data); (b) a seam-aligned pose θ = 0 recorded as a separate diagnostic row, not a verdict input, because the scan shows false-empty clusters near it; (c) the primary rule exactly as D-12/D-14; (d) a list of variant rules computed from the same recorded readings (e.g. "at least 2 of 3 controls fire and all fired controls agree with the closed form", "matched and control at the same pose", the c = −0.05 same-pose sensitivity as a control) reported beside the verdict but never changing it, so Phase 5's revision has data without anyone tuning toward a pass.
**Warning signs:** a control volume of exactly 0.0000 with `solids = 0` and `HasWarnings` False.

### Pitfall 4: The `HasWarnings` diagnostic is silent exactly where it is needed, and reading it can segfault
**What goes wrong:** `BRepAlgoAPI_Common` has no `HasErrors`/`HasWarnings` in OCP 7.9.3.1.1; they live on `BOPAlgo_BOP` and `BOPAlgo_PaveFiller` (`dir()` lists them there) [VERIFIED: this session]. The route `op.DSFiller().HasErrors()/.HasWarnings()` returns values, but (a) the process died with exit 139 at teardown (after printing) unless the `op` and filler references were kept alive and the process ended with `os._exit(0)`; (b) the readings: all False on every false-empty control and every correct result, `HasWarnings` True on exactly the c = 0 matched garbage rows (solids = 1 and 3, volume ~0) [VERIFIED: probes R4, R5].
**How to avoid:** if the column is kept, read it only inside the throw-away worker, keep references for the process lifetime, end the worker with `os._exit` after flushing, record it as `diag_warnings` and never as a verdict input (CONTEXT already says so). It cannot substitute for the controls: it did not flag one false-empty.

### Pitfall 5: RSS, import cost and the check's own memory
**What goes wrong:** `ru_maxrss` is the process peak; in a persistent worker a big earlier row hides every later row, and a pure-Python STL check on the same process adds gigabytes (in-process peak 2.98 GB after a 3.2 M triangle mesh + check vs 2.26 GB for the mesh alone in a fresh child) [VERIFIED: probes R3, R11].
**How to avoid:** per-row RSS only from a fresh child (the `bench.export_cost --child` pattern), for a bounded subset: per (size, hand) the largest row at each reported preset, plus every frontier terminal row. Everything else records "worker high-water, not per-row". Take `ru_maxrss` immediately after mesh + gzip, before the STL check. Import of cadquery costs 2.9-3.7 s per process under load, 6.7 s in the emulated container: do not spawn per row.
**Measured peaks (fresh child, fine (0.01, 0.1), loaded host, bytes read into Python):** M2 L20 926 MB; M6 L60 1158 MB; M20 L200 2261 MB; baseline after import 467-469 MB; M20 L200 at (0.05, 0.5) 850 MB [VERIFIED: probe R11].

### Pitfall 6: Mesh budget will trip on budget, not on construction
**What goes wrong:** the campaign is planned around construction failures and finds the cap is set by bytes.
**Evidence:** fine (0.01, 0.1): M2 L20 340 k triangles / 17.0 MB; M6 L60 679 k / 33.9 MB; M20 L200 3.29 M / 164.3 MB, gzip-1 76.2 MB. Raw + gzip = 49.7 MB at M6 L60 (inside 64 MB) and 240 MB at M20 L200. About 0.82 MB per mm at M20 gives raw + 0.46·raw > 64 MB near L = 53 mm [VERIFIED: probe R11; extrapolation arithmetic is mine]. A 250-turn M20 (625 mm) fine STL would be roughly 500 MB, 10 M triangles [ASSUMED: linear extrapolation, not run].
**How to avoid:** predict it in the protocol; keep over-budget rows (cap, D-10) distinct from failures in every table; the per-size cap in L11 is the smaller of the construction frontier and the budget.
**Campaign volume to plan for:** ~3 G triangles (both hands) at the finest preset ≈ 145 GB of temporary STL written and read; mesh ~1.3-2.5 s/M triangles on a quiet to moderately loaded host; the STL check ~3 µs/triangle (~2.4 h if run on every row at the finest preset, ~30 min at a (0.05, 0.5)-class preset). [ASSUMED: arithmetic from the grid counts and measured per-turn triangle counts; order of magnitude only.] Run the check on every row at a coarse shipped-class preset and at the fine preset only under a pre-registered triangle ceiling, with skipped checks counted visibly (a skipped check is not a pass).

### Pitfall 7: Timing is load-dependent by 2x or more
**What goes wrong:** a bound or a frontier stop read off a loaded run.
**Evidence:** the same M6 L60 fine mesh took 2.53 s at load 29 and 1.30 s at load 2.8; M20 L200 fine mesh 12.6 s at load 25 vs 5.4 s at load 11-18 (earlier run); host load during research ranged 1.98-29.4 with only this session's work on the owner's host [VERIFIED: probes R2, R3, R11, R13]. The host idles near 2-5 with an agent session open.
**How to avoid:** the quiet gate (D-17) for any timing-derived claim (30 s frontier stop, budget cap); validity, solid count, volume and pair outcomes are load-independent and may be reported from a non-decisive run provided the protocol says so in advance (Open Question 6). Hard-timeout kills under a non-decisive gate are recorded `timeout`, not `failure`.

### Pitfall 8: K trades triangles against STEP size and seams
**Evidence (M6 L60, host load 2.5-8):** K=3: 82 faces, 104 776 / 604 344 triangles at (0.05, 0.5)/(0.01, 0.1), STEP 3.57 MB; K=5: 50 faces, 116 352 / 678 624, STEP 2.93 MB; K=10: 26 faces, 130 434 / 792 016 [VERIFIED: probes R1, R14]. So "fewest triangles" selects K=3 while STEP size and face count rise. D-07's rule must name a secondary criterion (STEP bytes, then K) and the preset the triangle count is read at, before run 1. K also changes which poses fail in the pair check (Pitfall 3), but D-07 locks K before the pair campaign: pre-register that the pair campaign uses the locked K and reports the other two K values as reference rows on a sample.

### Pitfall 9: Negative-control recipe produces exceptions as well as silent-wrong rows
**Evidence:** trapezoid tooth (axial half-width P/16 + (ro − r)·tan30°, root embedded 0.05 P), `Workplane("XZ").polyline(...).sweep(helix, isFrenet=True)`, tool length L + 2P translated −P, `core.fuse(tool)`: M6 L10 → 1 solid, valid, precise volume 54.7 vs closed 229.6 (0.238); M2 L6 → 4.0 vs 14.7 (0.274); M10 L50 → 3292.0 vs 3257.1 (1.011, plausibly right); M6 L20 and L40 → `ValueError: Null TopoDS_Shape object` [VERIFIED: probe R15]. The recorded known-bad inputs for THRD-04 are the two silent-wrong rows; the exception rows are `failure`, not silent-wrong. Keep the builder recipe in `bench/thread_spike/` (Phase 3's test imports it).

### Pitfall 10: Squash landing and the two-PR order
**What goes wrong:** PR 2 is cut from the PR 1 branch (pre-squash) so the guard compares against commits that do not exist on `main`; or the protocol file is edited in PR 2 beyond Results/Verdict.
**How to avoid:** cut PR 2 from `origin/main` after `make pr.land` (D-19); the guard of Pattern 6; keep skip tokens out of PR titles/bodies (`make pr.land` refuses them) [CITED: L08].

### Pitfall 11: `RESULTS.md` size
`RESULTS.md` currently has 241 lines. A verbatim per-row table for 3580 rod rows plus void rows, frontier rows, ~1100 pair cells would be megabytes of Markdown. See Open Question 5 (raw JSONL committed beside it with a sha256 in the header is the recommendation).

## Code Examples

Verified patterns (all run this session; scratch scripts are not kept, these are the method).

### 1. Exact grid
```python
# Source: scratch grid.py (probe R12); pitches are preview values, UNVERIFIED (D-02)
from fractions import Fraction

PITCH: dict[str, tuple[Fraction, Fraction]] = {   # name -> (d, P)
    "M2": (Fraction(2), Fraction(2, 5)), "M2.5": (Fraction(5, 2), Fraction(9, 20)),
    # ... 15 entries ...
}

def lengths(d: Fraction, pitch: Fraction) -> list[Fraction]:
    cap = min(10 * d, Fraction(200))
    turns = {k * pitch for k in range(1, int(cap / pitch) + 1)}
    mm = {Fraction(m) for m in range(1, int(cap) + 1)}
    lo = min(pitch, Fraction(1))                  # Open Question 3: reading of D-03
    return sorted(x for x in turns | mm if lo <= x <= cap)

def is_integer_turn(length: Fraction, pitch: Fraction) -> bool:
    return (length / pitch).denominator == 1
```

### 2. Quiet gate core
```python
# Source: scratch quiet_demo.py; semantics = spur session.py:296-319
@dataclass(frozen=True)
class Reading:
    utc: str        # time the value was read
    load1: float

@dataclass(frozen=True)
class QuietResult:
    decisive: bool
    readings: tuple[Reading, ...]

def wait_quiet(bar: float = 1.5, samples: int = 3, interval: float = 30.0, cap: float = 900.0, *,
               read: Callable[[], float], sleep: Callable[[float], None],
               now: Callable[[], str], clock: Callable[[], float]) -> QuietResult:
    taken: list[Reading] = []
    deadline = clock() + cap
    while True:
        taken.append(Reading(now(), read()))
        recent = taken[-samples:]
        if len(recent) >= samples and all(r.load1 < bar for r in recent):
            return QuietResult(True, tuple(taken))
        if clock() >= deadline:
            return QuietResult(False, tuple(taken))
        sleep(interval)
# production wiring: read=lambda: os.getloadavg()[0], sleep=time.sleep,
#   now=lambda: datetime.now(UTC).isoformat(), clock=time.monotonic
# verified: [1.4,1.4,1.4] decisive in 3; [1.4,1.5,1.4,1.4,1.4] decisive in 5 (1.5 resets);
#           never quiet, cap 900, interval 30 -> non-decisive, 31 readings, last at t=900
```

### 3. Closed-form area and interference oracle (kernel-free)
```python
# Source: scratch cf.py / lib.area (probes R4-R7); matches STACK's formula
def area(d: float, p: float, c: float = 0.0) -> float:
    ro = d / 2 + c
    rr = d / 2 - 5 / 8 * p * math.sqrt(3) / 2 + c
    return (math.pi / 8 * ro**2 + math.pi / 4 * rr**2
            + 5 * math.pi / 24 * (ro**2 + ro * rr + rr**2))

# r(theta): crest flat [-pi/8, pi/8] at ro; flank to rr over [pi/8, 3pi/4]; root flat
# [3pi/4, 5pi/4] at rr; flank back over [5pi/4, 15pi/8]. interference = m * integral of
# 0.5 * max(0, r_b(th)**2 - r_v(th + phi)**2) dth, r_v = r_b + c, phi = pi (control) or 0.
# M6 m=5.2: control c=0.1 -> 12.213; c=0 -> 16.1427; matched c=-0.05 -> 4.3627.
```

### 4. Precise volume, signed postcondition
```python
# Source: probes R1, R10; overload read from OCP docstring
def precise_volume(shape: cq.Shape, eps: float = 1e-6) -> float:
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape.wrapped, props, eps, False, False)
    return float(props.Mass())          # float(): OCP returns Any under mypy
# signed rel err = precise_volume(s) / (area(d, p, c) * L) - 1  ->  -2.0 for an inverted solid
# eps=1e-6 cost 0.2-1.0 s per row, eps=1e-7 0.4-2.0 s with no accuracy gain (1.53e-6 vs 1.62e-6 at M6 L20)
```

### 5. Pair boolean with the diagnostic kept alive
```python
# Source: scratch pair.py (probes R4-R8)
_KEEP: list[object] = []   # references live for the process lifetime: freeing the filler segfaults

def common(a: cq.Shape, b: cq.Shape) -> tuple[float, int, bool, bool]:
    op = BRepAlgoAPI_Common()
    la, lb = TopTools_ListOfShape(), TopTools_ListOfShape()
    la.Append(a.wrapped); lb.Append(b.wrapped)
    op.SetArguments(la); op.SetTools(lb); op.Build()
    res = cq.Shape.cast(op.Shape())
    filler = op.DSFiller(); _KEEP.append((op, filler))
    vol = 0.0 if res.isNull() or not res.Solids() else precise_volume(res)
    return vol, len(res.Solids()), filler.HasErrors(), filler.HasWarnings()
# worker ends with: sys.stdout.flush(); os._exit(0)
```

### 6. Stdlib STL check (watertight + signed volume)
```python
# Source: scratch lib.stl_check (probes R1-R3); PITFALLS probe record method
# weld vertices by round(x / 1e-5); every directed edge (u, v) must occur once and (v, u) once;
# volume = sum of signed tetrahedra. 1.3 s for 605 450 triangles, 9.4 s for 3 203 406.
```

### 7. Container validity pass (feasibility proven)
```bash
docker run --rm --platform linux/amd64 --entrypoint python \
  -v "$PWD/bench:/probe/bench:ro" -e PYTHONPATH=/probe screw:latest -m bench.thread_spike --container-pass
# The probe used this same mount pattern (`-v <scratch>:/probe:ro`, `--entrypoint python`) with a
# scratch entry script; the `-m bench.thread_spike --container-pass` entry point is the proposed
# shape, not yet written. Probe: image arch amd64 on an aarch64 OrbStack host; import 6.7 s;
# same volume errors as native (M6 L20 eps1e-6 +1.53e-06, M6 L60 +1.64e-06, M20 L200 +1.14e-06)
# [VERIFIED: probe R16]
```
The image runs as uid 10001 and has no `bench/`; a read-only bind mount plus `PYTHONPATH` is enough. No STL is written in the validity-only pass, so the compose `tmpfs` size does not matter.

### 8. Reference rows from the scratch directory
```python
# Source: probe R9 (PYTHONPATH=<scratch>/cqw .venv/bin/python)
from cq_warehouse.thread import IsoThread
th = IsoThread(major_diameter=6, pitch=1.0, length=20, external=True,
               end_finishes=("fade", "fade"))        # th.min_radius for the core
solid = cq.Workplane("XY").circle(th.min_radius).extrude(20).val().fuse(th)
# pre-register the end finishes: "chamfer" cost ~6x "fade" and broke at 80 turns (PITFALLS C1)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `Workplane.sweep(helix)` + `fuse` | twisted transverse section via `MakePipeShell` aux helix, sewn 5-turn segments | STACK 2026-10-05; reproduced here | 0 bad rows in 576 vs silent-wrong/exception on the naive path |
| `Shape.Volume()` | `BRepGProp.VolumeProperties_s(... eps ...)` | C2 | default is fine on sewn twist (≤ 2.7e-5) but +6.3 % on cq_warehouse; choose per rule, record both |
| ISO 68-1:1998 (one profile) | ISO 68-1:2023: basic and design profiles | 2023-10 | external design profile has a rounded root: fully rounded R = 0.144 P, partially rounded minimum R1 = 0.125 P; internal thread design profile = basic profile, flat roots [CITED: boltscience.com/pages/ISO68-1-basic-and-design-thread-profiles.htm; secondary, MEDIUM; the owner reads the standard under D-01]. The ISO preview PDF is not machine-readable here (no PDF text tool; the fetch tool returned encoded streams) |
| One kernel pair forever | cadquery master moves to OCP 8 | cadquery-ocp 8.0.1.0.0 published 2026-10-05 | kernel bump = re-measure event; not this phase |

**Deprecated/outdated:** `ControlSurfaceDeflection=False` for downloads (Phase 5 concern, STACK B); `Workplane.twistExtrude` as shipped (fails from 60-100 turns).

## Protocol Inputs the Planner Must Pre-register

Everything below is a choice that must be in `02-SPIKE.md` before run 1. "Recommended" values are mine, tagged; the evidence is above. The R-series probes in Sources are research, not campaign runs: they carry no run id and may be cited in the protocol's Predictions only as prior evidence ("research probe R7 saw ...").

| Input | Recommended | Basis |
|-------|-------------|-------|
| Profile | owner's D-01 pin; research default basic (SUMMARY Q4) | D-01; closed form and builder assume basic until pinned |
| Pitch table, `min(10d, 200)`, nut heights, tip angle | the lists above, each labelled UNVERIFIED | D-02, D-08, D-13 |
| Row-level silent-wrong tolerance `T_pass` | relative 1e-4 on the precise volume, plus sign and solid count [ASSUMED] | measured max 7.6e-6 on 576 sewn rows; naive defect is ~0.76; chosen so it neither flaps nor hides a 1e-3 defect; both estimators are tested against it |
| Gate tolerance for Phase 3 (`T_gate`) | derived after the campaign by a pre-registered formula, e.g. 10 × max observed |err| of the chosen estimator on passing rows, rounded up to one significant figure [ASSUMED] | separates the verdict tolerance (fixed before data) from the shipped gate (derived from data) and avoids the circularity in D-09/D-20 |
| Estimator rule (D-20) | candidates `GProp(eps 1e-6)`, STL signed tetra (deflection-limited), plus default `Volume()` as a known-bad reference column; pick the smaller max |err| over passing rows, tie (within 2×) → cheaper | Pattern 2/7 |
| STL volume band | `k × mean deflection × S/V` or simply "negative and ≤ 2 % at a shipped-class preset" [ASSUMED] | inscribed mesh is always low (−7e-4 to −2.9e-2 measured) |
| K rule (D-07) | primary: fewest triangles at a named preset among K with 0 failures and |err| ≤ T_pass; secondary: smaller STEP bytes; tertiary: smaller K | Pitfall 8 |
| Frontier | next multiple of 5 turns above the standard max, then +5 up to 250; stop at first `failure`/`silent_wrong`, or when a decisive-gate build + fine mesh (spur INTERIM `fine` (0.01, 0.1)) exceeds 30 s | D-04; per-turn triangle counts above |
| Mesh presets | spur `preview` (0.08, 0.5) and `fine` (0.01, 0.1) + depth fractions, e.g. h/4, h/8, h/16, h/32 with angular 0.5 | triangles ∝ 1/δ; angular matters ~17 % at δ = 0.05 |
| Pair poses | fixed deterministic list inside [−π, π], plus a θ = 0 diagnostic; matched and control share θ | Pitfalls 2-3 |
| Pair band | measured vs closed form within 1e-3 relative [ASSUMED] | non-empty readings agreed to ≤ 1e-5 |
| Pair diagnostics | c = 0 and c = −0.05 at the matched poses; mixed-hand at each size; variant rules reported, not verdict | D-11, D-14, Pitfall 3 |
| Hard timeouts | row 120 s, pair cell 600 s [ASSUMED] | Pattern 3 |
| Container pass | winning construction only, validity/solids/volume, no mesh | D-05 |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Nut heights for M2-M4 follow m = 0.8·d (1.6, 2.0, 2.4, 3.2), matching the withdrawn ISO 4032:2012 values as remembered; M3.5, M7, M14, M18 values are protocol inputs without a source. Probes used m = 1.6 (M2), 5.2 (M6), 8.4 (M10), 18.0 (M20) (the last three from STACK's ISO-4032 preview reading) | Pair, Protocol Inputs | Wrong m scales interference linearly and changes the number of engaged turns; a label, not a verdict input, but the owner should replace from Annex A |
| A2 | Tip chamfer envelope: cone from the minor radius at the tip face, 30° from the end face; the probe trimmed valid in 0.5-0.8 s at all six sizes tried | Pitfall/Patterns, trim row | ISO 4753 is unread; cost evidence only (D-08) |
| A3 | `T_pass = 1e-4`, `T_gate` formula, pair band 1e-3, STL band, hard timeouts 120/600 s | Protocol Inputs | Wrong tolerances either flap or hide defects; planner/owner confirm in the protocol |
| A4 | Adding `bench` to import-linter `root_packages` leaves the four existing contracts unchanged | Pattern 8 | A surprise broken contract in `make verify`; the planner runs `make lint-imports` in the same commit |
| A5 | A 250-turn M20 fine STL ≈ 500 MB / 10 M triangles; ~3 G triangles and ~145 GB temporary STL for the campaign | Pitfall 6 | Disk/time planning off by a factor; order-of-magnitude only |
| A6 | Pair-check probability model (independent false-empty ≈ 0.3) | Pitfall 3 | Illustrative only; the campaign measures the real rate |
| A7 | `float()`/`object` wraps are enough for mypy strict on new OCP-touching functions (STACK says the reference code passes) | Standard Stack | A few typing fixes during PR 1 |
| A8 | The three ISO design-profile numbers (R = 0.144 P, R1 ≥ 0.125 P, flat internal roots) come from a secondary site | State of the Art | Owner's read of ISO 68-1:2023 supersedes (D-01) |
| A9 | `*.stl` outputs are not committed (`.gitignore` ignores `*.stl`, `*.step`) but JSONL is | Pitfall 11 | none |

## Open Questions

1. **Pair-check falsifiability is likely to fail as specified. What does the protocol say before run 1?**
   - What we know: 29 % of half-pitch controls false-empty at c = 0.1 (Pitfall 3), no K or fuzzy/serial setting cleans it, matched poses never false-positive at c > 0, non-empty readings equal the closed form, and the c = −0.05 matched-pose readings were correct at 3 of 3 poses (including θ = 0, where the control fails).
   - What's unclear: whether the false-empty correlates with a false-empty at the matched pose (a matched "empty" could itself be a false-empty; the control only helps if the failure is shared). The same-pose negative-clearance reading is the stronger positive control; D-12/D-14 do not use it as a verdict input.
   - Recommendation: pre-register D-12/D-14 as written plus the variant-rule list and the θ = 0 diagnostic (Pitfall 3 item (d)), report variants beside the verdict, and let the escape clause fire if D-14 says so. Adding the same-pose c = −0.05 control to the verdict is a change to locked decisions: surface it to the owner at the checkpoint, do not fold it in silently.

2. **If the owner pins the design profile (D-01), rod and void no longer share one section.**
   - What we know: the external design profile rounds the root; the internal thread keeps flat roots (secondary source). The closed form is `(π/P) ∫ r(z)² dz`, so only the integrand and the spline sampling change; a root arc needs more than 14 samples.
   - What's unclear: whether the nut void is the bolt's design section + c (one builder, the Phase 3 architecture assumption) or the basic internal section (two sections, so "one builder for rod and void" becomes "one builder, two sections").
   - Recommendation: write `section(profile, kind)` and implement only the pinned profile; if design is pinned, surface the void-section question before pre-registering, since it changes the pair campaign.

3. **D-03 "from the smallest of those".**
   - Reading used for the counts: lower bound `min(P, 1 mm)` (so P > 1 sizes include sub-turn lengths such as M8 L = 1 mm = 0.8 turn, the short-length floor D-03 wants to find). The alternative (start at L = P) removes about 1-2 rows per size for M8-M20.
   - Recommendation: state the reading in the protocol; keep the sub-turn rows (they are where the integer-turn/short-length floor lives).

4. **Nut-height source for M2-M4 and the second-choice sizes.** Recommendation: a labelled protocol input (A1), replaced when the owner reads Annex A in Phase 5.

5. **Verbatim output size.** D-16 says every run's verbatim output goes in `RESULTS.md`; per-row tables are megabytes.
   - Recommendation: the runner writes JSONL (one record per row) next to the Markdown it prints; `RESULTS.md` carries each run's header, host state, load readings, per-size aggregates and every non-ok or over-budget row verbatim, with the JSONL's path and sha256; the verdict predicates run on the JSONL in tests. Needs the owner's nod because it narrows "verbatim".

6. **Does decisiveness apply to validity outcomes?**
   - What we know: only timings depend on load; failures, solid counts, volumes and pair outcomes do not (kill-by-timeout under load is the exception).
   - Recommendation: pre-register that a non-decisive run's validity/pair outcomes count and its timing-derived claims (30 s frontier stop, budget caps from seconds) do not; non-decisive runs are never re-run toward a pass (D-17). The host is rarely quiet while agent sessions are open (load 2-29 observed), so the owner closes agents or runs detached.

7. **Sample sizes for reference rows and the K sweep (D-06/D-07).** Free choice; suggest the six sizes of the trim probe (M2, M3, M6, M10, M16, M20) plus M2.5/M8 for odd pitches, at the standard max turns and the frontier.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 + `.venv` with the pinned kernel pair | everything | ✓ | 3.12.13; cadquery 2.8.0; cadquery-ocp 7.9.3.1.1 | none needed |
| git | guard, run header | ✓ | 2.54.0 | — |
| gh (authenticated) | PR 1 / PR 2, `make pr.land` | ✓ | 2.102.0, logged in as halfb00t | — |
| Docker (OrbStack) | D-05 container pass | ✓ | Client 29.4.0; host aarch64; `screw:latest` is an amd64 image (`docker image inspect`) | none; pass is the deliverable |
| Network to github.com | cq_warehouse scratch install | ✓ | `pip install --no-deps --target` took 6 s | skip reference rows (D-06 reduces to one-pipe + naive) |
| Quiet host (load < 1.5, 3 × 30 s) | decisive timing | ✗ at research time | load 1.98-29.4 observed over ~25 min with the owner's other projects running | run with agents closed / detached; else non-decisive (Open Question 6) |
| `psutil`, `pdftotext`, `numpy`-for-bench | — | not used | psutil absent; no PDF text tool | stdlib; owner reads ISO 68-1 |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** a quiet host; the ISO 68-1 PDF cannot be machine-read here (owner checkpoint D-01).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (floating `>=8`, `xdist==3.8.0`, `cov==7.1.0`, `filterwarnings = ["error"]`) |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`); coverage source is `src/screw` only [VERIFIED: pyproject.toml:118 `source = ["src/screw"]`, :136 `fail_under = 94`], so bench code does not move the floor |
| Quick run command | `make test PYTEST_ARGS="tests/test_bench.py -q -n0 --no-cov"` (the Makefile comment prescribes `--no-cov` for partial runs) |
| Full suite command | `make verify` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFR-03 | quiet gate: 3 consecutive strict-under readings release; exact bar resets; cap → non-decisive; every reading timestamped | unit | `make test PYTEST_ARGS="tests/test_bench.py -k quiet -q -n0 --no-cov"` | ❌ Wave 0 |
| INFR-03 | grid: exact counts per size (1790 total), integer-turn exactness, dedupe, deterministic order | unit | `... -k grid ...` | ❌ Wave 0 |
| INFR-03 | verdict predicates with positive controls: naive known-bad (ratio 0.238, 1 solid, valid) flagged silent-wrong; inverted (−1.0) flagged; non-watertight (one triangle removed) flagged; flipped orientation → negative volume | unit | `... -k verdict ...` | ❌ Wave 0 |
| INFR-03 | escape clause, pass bar, over-budget vs failure separation, frontier stop rule, K rule, estimator rule, pair rule (all 3 matched empty + all 3 controls fire within band; mixed hand must be violated) on synthetic records | unit | `... -k rule ...` | ❌ Wave 0 |
| INFR-03 | closed forms: `area` vs numeric quadrature; `interference_area` pins M6 m = 5.2: control c = 0.1 → 12.213, c = −0.05 matched → 4.3627 (±1e-3) | unit | `... -k closed_form ...` | ❌ Wave 0 |
| INFR-03 | pre-registration guard predicate with injected git output (ancestor yes/no, dirty, text-before-`## Results` equal/different) | unit | `... -k protocol ...` | ❌ Wave 0 |
| INFR-03 | kernel-free module stays kernel-free | contract | `make lint-imports` (new contract, Pattern 8) | ❌ Wave 0 |
| INFR-03 | real-kernel smoke: M6, 5 turns, sewn: 1 solid, valid, |precise vol / closed form − 1| < 1e-4 (~0.3 s) | integration | `... -k smoke ...` | ❌ Wave 0 |
| INFR-03 | pre-registration order, host-state labelling, decision entry | manual-only | git log on `main` shows PR 1 squash before PR 2 squash; `02-SPIKE.md` text before `## Results` unchanged | — |

No timing assertion enters the gate (D-15).

### Sampling Rate
- **Per task commit:** the quick command above.
- **Per wave merge:** `make verify`.
- **Phase gate:** `make verify` green on both PRs; PR 1 additionally reviewed by the other CLI before `make pr.land`.

### Wave 0 Gaps
- [ ] `bench/quiet.py`, `bench/thread_spike/{__init__,maths,verdict,helical,measure,pair,worker,__main__}.py`
- [ ] `tests/test_bench.py` cases above (file exists; cases are new)
- [ ] `pyproject.toml`: `root_packages = ["screw", "bench"]` and the kernel-free contract
- [ ] `Makefile`: `bench.thread` target and `.PHONY` entry next to `bench.build`/`bench.export`
- [ ] `.planning/phases/02-thread-spike/02-SPIKE.md` with a stub `## Results` heading
- [ ] Framework install: none (pytest already in `.venv`)

## Security Domain

`security_enforcement` is enabled (absent = enabled; config reads `true`, ASVS level 1). This is offline bench tooling with no network service, but it shells out, installs a git package and parses child output.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | CLI args validated at the boundary (run ids/labels `[A-Za-z0-9-]+` as spur's `_label`, sizes from a closed list, output paths resolved under `bench/`); worker records parsed with `json` only (never `pickle`/`eval`); every subprocess call a list argv, no shell |
| V6 Cryptography | no | `sha256`/`git hash-object` for integrity labels only; stdlib `hashlib` |
| V10/V14 Dependencies and supply chain | yes | no new `pyproject` dependency; `cq_warehouse` from a pinned commit into a scratch `--target` dir, `--no-deps`, behind a human-verify checkpoint; kernel pair stays pinned (L06) |
| V12 Files | yes | temp STLs in `tempfile.TemporaryDirectory`, removed per row; hundreds of MB, so cleaned even on a killed worker (parent removes the directory) |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Unpinned/unregistered package executes at import (`cq_warehouse`) | Tampering | pin commit sha, scratch dir outside the repo, never on `sys.path` of `make verify`, human-verify checkpoint |
| Run id / label used in a path or git command | Tampering | regex-validated ids, `Path.resolve()` under `bench/`, argv lists |
| Worker child output trusted blindly | Tampering | JSON only, schema check (`TypedDict`), unknown keys refused |
| Container mount writable by the image | Tampering | `-v bench:ro`, non-root image user (10001 in the Dockerfile) |
| Disk exhaustion by 500 MB temp files | Denial of service | per-row temp dir cleanup, size ceiling on frontier rows, hard timeout |

## Sources

### Primary (HIGH confidence)
- Repository files read this session: `.planning/phases/02-thread-spike/02-CONTEXT.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/ROADMAP.md` (Phase 2/3/5), `.planning/config.json`, `AGENTS.md` (via CLAUDE.md), `docs/CODING_VALUES.md`, `docs/HOW_TO_DEVELOP.md`, `docs/architecture/decision_log.md` (L01-L10), `Makefile`, `pyproject.toml`, `Dockerfile`, `requirements.txt`, `src/screw/solid/__init__.py`, `bench/{__init__,corpus,build_time,export_cost}.py`, `bench/README.md`, `bench/RESULTS.md`, `tests/test_bench.py`, `tests/conftest.py`, `.planning/research/{STACK,ARCHITECTURE,PITFALLS,SUMMARY}.md`, `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md`.
- spur: `.planning/milestones/v0.3-phases/13-latency-bar/13-LATENCY-INVESTIGATION.md`, `.../investigation/session.py`, `bench/tip_chamfer_spike.py`, `bench/RESULTS.md` § "Tooth-tip chamfer spike".
- Live tool output on the pinned pair: OCP docstrings (`BRepGProp.VolumeProperties_s`, `Shape.exportStl`), `dir()` of `BRepAlgoAPI_Common`/`BOPAlgo_BOP`, `gsd_run query package-legitimacy check`, `git ls-remote`, `lint-imports --config <scratch>`, `docker image inspect`/`docker run`.
- Research probes R1-R16 (below).

### Secondary (MEDIUM confidence)
- [ISO metric screw thread, Wikipedia](https://en.wikipedia.org/wiki/ISO_metric_screw_thread): ISO 262 coarse pitch table for the 15 sizes, H = (√3/2)P, d1 = D − 1.082532 P.
- [ISO 68-1 basic and design thread profiles, boltscience.com](https://www.boltscience.com/pages/ISO68-1-basic-and-design-thread-profiles.htm): design profile root radii.
- STACK/PITFALLS/ARCHITECTURE measured evidence (own earlier research; reproduced in part here).

### Tertiary (LOW confidence)
- Search results for ISO 68-1:2023 (fastenerandfixing.com, plastiform.info): consistent with the above; not relied on.
- iTeh ISO 68-1:2023 preview PDF: fetched, not machine-readable here; Clause 6 not read by anyone in this project (D-01).

### Research probe record (not campaign runs; no run ids; scratch scripts not kept)

| Id | What | Host load at time | Result used above |
|----|------|-------------------|-------------------|
| R1 | sewn thread M6 L20/L60 (K=3,5,10), M2 L20, M20 L200: build, volume estimators, STL two presets, check | 8.9-20.5 | volume errors, triangles, mesh volume error |
| R2 | M20 L200 mesh ladder + check timing and RSS (in-process) | 11-18 | δ scaling; check cost 9.4 s / 3.2 M tri |
| R3 | fresh-child RSS and gzip, 4 rows | 25-29 | peaks, gzip ratios |
| R4 | M6 pair: RH, LH, mixed, c = 0.1, 0, −0.05, 3 matched + 3 control poses | 5.6-18 | pair table, c = 0 garbage, diagnostics |
| R5 | closed-form interference vs kernel | n/a | agreement |
| R6 | M6 pose scan 12 poses; θ > π artefact | 6-18 | pad constraint |
| R7 | 4 sizes × K ∈ {3,5,10} × 6 control + 2 matched poses | 2-10 | false-empty table |
| R8 | fuzzy / serial / K variants at θ = 0, 0.1; fine θ scan; slide perturbation | 2-10 | no remedy |
| R9 | cq_warehouse scratch install and M6 L20 fuse | ~10 | +6.3 % default volume |
| R10 | M2.5/M3.5/M8, both hands, every D-03 length, K=3 and 5 (576 rows each K) | 5.7-12.4 | 0 bad rows, max errors, ~0.65 s/row |
| R11 | fresh-child M2/M6/M20 meshes, gzip, STEP | 25-29 | budgets, peaks |
| R12 | float drift count; exact grid counts | n/a | 168/3000; 1790 |
| R13 | host load samples | 1.98-29.4 | quiet-host availability |
| R14 | STEP size vs K and turns | 2.5 | STEP table |
| R15 | naive sweep + fuse, one-pipe inversion, tip trim, DSFiller crash | 2-8 | negative controls, trim cost |
| R16 | container run of the reference builder (amd64 image on aarch64) | n/a | same volume errors |

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, no new dependency; versions read live.
- Architecture: HIGH for construction/estimator/mesh patterns (reproduced); MEDIUM for the worker/guard design (recommended, partly exercised).
- Pitfalls: HIGH for 1, 2, 4, 5, 9 (reproduced); MEDIUM for 3 (4 sizes, RH only, c = 0.1, indicative poses, loaded host); MEDIUM for 6 (extrapolated beyond 80 turns).
- ISO values: LOW (previews/secondary; labelled UNVERIFIED by decision).

**Research date:** 2026-10-06
**Valid until:** 2026-11-05 (stable stack; invalidated by any kernel-pair bump or cadquery release that moves to OCP 8)
