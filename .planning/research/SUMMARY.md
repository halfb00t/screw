# Research Summary: Parametric ISO Metric Threaded Fastener Generator

**Project:** screw — a parametric generator for hex bolts (ISO 4014/4017), hex nuts (ISO 4032), and socket cap screws (ISO 4762 in v2), with real helical threads, FDM-printable mating pairs, STL/STEP export, and three front ends (web UI, HTTP API, CLI) on one parameter model.

**Research Date:** 2026-10-05  
**Researchers:** Four parallel agents (Stack, Features, Architecture, Pitfalls)  
**Overall Confidence:** MEDIUM-HIGH (kernel and standards findings are HIGH; FDM and multi-machine behavior are UNVERIFIED)

---

## Executive Summary

This project forks spur's infrastructure and manufacturing approach (Python 3.12, CadQuery/OpenCascade, FastAPI, one parameter model with three front ends) to generate threaded fasteners instead of gears. The core value — a bolt and nut that thread together when printed — depends on three technical decisions that research has now sized:

1. **Thread construction:** a twisted transverse cross-section, extruded helically in 5-turn segments and sewn together, avoids the silent partial failures (valid solids with the core missing) that plague the naive sweep-and-union approach. This construction passed 166 configurations without failure and matched closed-form volume to 0.001%. [STACK, HIGH confidence on pinned pair; MEDIUM overall due to single machine.]

2. **ISO table data:** research found no library of fastener dimensions with cited sources. Hand-entry with full clause citations and one test per row is the only path that meets the owner's rule. [FEATURES, HIGH on source status; UNVERIFIED on which editions to buy.]

3. **Mating proof:** a kernel interference check at clearance > 0 with a positive control (half-pitch offset must collide) can prove a pair in 1.2–13.6 s per size. However, at clearance ≤ 0 and one-pose tests, the boolean fails silently. The proof must use multiple poses, non-zero clearance for the boolean, and an analytic statement for zero clearance. Full-grid reliability is unmeasured; this must be part of the thread spike in phase 2. [ARCHITECTURE, PITFALLS; UNVERIFIED]

Four owner decisions are needed before phase 3:

- **Q1 (M2–M4 nuts):** ISO 4032:2023 normatively covers M5–M39 only. Options: cite informative Annex A, restrict nut range to M5–M20, or drop M2–M4 from bolts. **Recommendation:** cite Annex A (brief needs purchased ISO 4032:2023 text).
- **Q2 (printed bolt into bought nut):** Unmeasured risk that FDM external threads come out oversize. **Recommendation:** validate in spike; add bolt undersize field in v1.x if needed.
- **Q3 (6g/6H source):** Brief wrote "4759" but ISO 4759-1 is product-grade, not thread. **Resolved:** cite ISO 965-2.
- **Q4 (thread profile):** ISO 68-1:2023 has basic (flat) and design (rounded) profiles. **Recommendation:** basic in v1 (measured here); design is v2.

---

## Key Findings

### From STACK.md

**Thread Construction (HIGH on pinned pair; MEDIUM overall)**

- **Twist-section, 5-turn sewn approach:** 166 configurations zero failures, volume to 0.001%, 0.10–0.32 s build, 15x fewer triangles than one pipe. [MEASURED macOS arm64, CadQuery 2.8.0 / cadquery-ocp 7.9.3.1.1]
- **Naive `Workplane.sweep + union(core)`:** 35% hard failures, and critically **35 of 139 valid-looking results had core silently dropped** (volume 75–80% short), with `isValid() == True`. [MEASURED]
- **`cq_warehouse` ruled-surface:** valid reference but not dependency (git-only, no PyPI, unmaintained since 2024-01, 7% hard-fail rate). **Keep as baseline; do not depend.**
- **`cq_warehouse` and `bd_warehouse` CSVs:** not sources of truth (0 of 15 ISO 4017 `k` matching standard, no clause citations). **Hand-enter from standards.**

**ISO Table Data (HIGH on editions; UNVERIFIED on purchase)**

- ISO 4014/4017 replaced 2022; ISO 4032 in 2023 (scope now M5–M39, M2–M4 to Annex A). [ISO-PREVIEW, SIS]
- Brief's "4759" is wrong; correct source is ISO 965-1 and 965-2 for 6g/6H. [HIGH confidence source identification]
- Thread length `b` is not one formula: ISO 4014 `b ref. = 2d + 6/12/25` per length band; ISO 4017 is full length; ISO 4762 is `2d + 12` for M1.6–M12 (rest UNVERIFIED). **Per-standard presets required.**
- **No new dependencies needed.** cadquery 2.8.0 and cadquery-ocp 7.9.3.1.1 sufficient.

### From FEATURES.md

**Core Requirements for v1 (MEDIUM confidence; standards HIGH, FDM LOW)**

- **Real helical threads on every threaded part.** Cosmetic threads cannot be proven to mate.
- **One clearance field on nut**, default from printed test (not blogs).
- **ISO 4014 and 4017 bolts, ISO 4032 nuts, presets with full citations.** M2–M20 (11 preferred); M3.5, M7, M14, M18, M22 are non-preferred and may be v1.x. **M2–M4 nuts depend on owner decision (Q1).**
- **Three front ends (UI, API, CLI) from one model, parity proven model-driven.**
- **Info panel from pure maths (`calc` layer), never unchecked solids.** ISO 965-2 limits with label: "limits for bought part; geometry is nominal."

**Printability Evidence (MEDIUM sources, LOW values)**

- **Consensus clearance band:** 0.10–0.20 mm radial on 0.4 mm nozzle. Sources: blogs, vendor guides, forums (not controlled). **This is a prior only; default comes from printed test.**
- **Conservative minimum:** M5/M6 and pitch ≥ 0.8–1.0 mm. **No controlled FDM study exists** on clearance × orientation × layer height.

### From ARCHITECTURE.md

**System Design (MEDIUM-HIGH; numbers single-machine)**

- **One model per type, registry-driven parity.** FastAPI rejects discriminated union as Query model; wide model silently ignores strays (L03). Per-kind models keep "one model, three front ends" true. [VERIFIED on pinned stack]
- **Import-linter contracts enforce isolation.** `calc`/`params` never import `tables` (contract 6); `tables` is leaf (contract 7); `app` never imports kernel (contract 5).

**Build Order (confirmed and amended)**

1. Port + walking skeleton (gives P2 a host; parity test early)
2. **Thread spike (parallel with 1)** — construction, mesh budget, pair reliability, volume estimator. Pre-register method.
3. Thread component (calc/thread.py + solid/helical.py + postcondition gate)
4. Bolt + tables (ISO 261/68-1/965, iso4017/4014 rows)
5. Nut + pair proof (iso4032, solid/pair.py, controls)
6. Operability re-sweep (timeout, memory, gzip, cache, workers on full grid)
7. v2: Socket cap (iso4762, thread shared; adding kind is a checklist)

**Thread Geometry (HIGH on isolation; UNVERIFIED on every construction)**

- Maths (ISO 68-1, closed-form area, flank gaps) in kernel-free `calc/thread.py`.
- One builder `solid/helical.py` turns section into helical solid; **postcondition: 1 solid, `isValid()`, volume within 1.2e-5 of closed form.** Gate failure = `BuildError`, never cached.

**Mating Proof Design (UNVERIFIED on grid reliability)**

- Algorithm: maths pre-check → kernel `common` at integer-pitch pose → control: half-pitch slide must be non-empty.
- Verdict: `proven` only if proof empty AND control fired; empty control is `inconclusive`, never pass.
- Clearance ≤ 0 returns `inconclusive` by definition (coincident surfaces fragile).
- Exposed in: pytest fixture (primary), `screw pair` CLI (owner needs this), **not API** (1.2–33 s vs 30 s timeout; nut `derive()` shows closed-form gaps instead).

### From PITFALLS.md

**Critical Pitfalls (HIGH on existence; prevention in roadmap)**

1. **C1: Helical boolean returns "valid" solid with wrong content.** Swept-tooth + union silently dropped core in 8 of 15 cases (75–80% short); `isValid() == True` on all. [MEASURED on pinned pair]
   - **Prevention:** P2 measures grid; P3 enforces gate: solid count, `isValid()`, **volume against closed form** (not just `isValid()`). Feed gate the known-bad result.

2. **C2: `Shape.Volume()` not oracle on helical surfaces.** Default off by 15–21%; `eps=1e-6` matched to 0.1%. [MEASURED]
   - **Prevention:** P2 chooses estimator; P4 numbers use chosen estimator, never bare `Volume()`.

3. **C3: Build time tracks turns, not diameter; worst is smallest pitch at longest length.** 0.6 s (10 turns) to ~80 s (160 turns). Failure frontier not monotone. [MEASURED; bounds UNVERIFIED]
   - **Prevention:** P2 sweeps every allowed config, not samples. P6 caps by turns (L/P), per size. Set timeout from worst-case measured point.

4. **C4: Mating proof cannot fail.** `bolt.intersect(nut).Volume() == 0` passes when boolean silently failed, `Volume()` inaccurate, flanks coincident. [MEASURED 12 poses, 3 sizes; UNVERIFIED sufficient]
   - **Prevention:** P2 measures pair reliability with controls (half-pitch must collide). P3 implements `PairReport(verdict, interference, control, clearance, engaged_length)` with left/mixed-hand tests. Never prove c ≤ 0 with boolean.

5. **C6 & C7: Table liability larger than transcription.** Editions changed (2022/2023); scope changed (M5–M39 normative); semantics vary (s = nom = max, e/dw = min, b = ref). [P] standards; secondary tables disagree.
   - **Prevention:** P4 cites standard, edition, table, row per row; one test per row asserting standard invariants. Use official previews or purchased copies.

**Moderate Pitfalls**

- **M1:** Self-intersecting at small pitch; assert profile width < P − margin.
- **M3:** Preset overwrites edits; warn before; show "matches ISO row: yes/no".
- **M4:** 4014 thread length > bolt; cap and warn (L03).
- **M5:** Head chamfer model unspecified; document 15–30 degree cone once.
- **C11:** One test per row × grid → gate timeouts; sample in gate, full in `bench/`.

---

## Implications for Roadmap

### Phase Structure (7 phases, ~2–3 mo. each P1–P6, 1 mo. P7)

| Phase | Content | Why | Gate Output | Research Flags |
|---|---|---|---|---|
| **P1** | Port spur runtime (pool, app, cli, records, viewer, gate, bench); walking skeleton (bolt, 3 front ends) | Port is reviewable before threading | `make verify` green; parity green | httpx2 dev dependency for starlette 1.7.0 TestClient |
| **P2** | Thread spike: construction grid sweep, mesh budget, pair reliability, estimator choice. Pre-register method. | Top risk; gives P1 place to land | Decision entry with run ids; constants proposed, no code | **Pair-proof cost UNVERIFIED.** If > 30 s/size, answer is offline-only. **Estimator must handle 150-turn helical** (15–21% error in default call). |
| **P3** | Thread component (based on P2), bolt geometry, nut blank, pair proof (controls, verdicts) | Thread is shared risk | Pair verdict across sample (1 size gate, full grid CI) | **Q2 validation:** printed nominal bolt → bought nut. **Q4 choice:** design profile wanted? |
| **P4** | Tables (261, 68-1, 965-2, 4017, 4014, 4032) and presets. Info panel. Row tests. | Tables ship with type that uses them | Every row cited, tested; panel traceable | **Q1 decision:** M2–M4 nut source (Annex A?). **Purchase standards** (4014, 4017, 4032, 965-2). |
| **P5** | Printed test (M6, M8, M10, M12, steps 0.05 mm, vertical, 0.4 nozzle, 2 heights, 3 samples). Floor from result. | Default clearance from measured, not blogs | Clearance default + floor with run ref. | **No FDM study exists.** Scope: M6–M12 v1; wider v1.x. |
| **P6** | Operability bounds (timeout, memory, gzip, cache, workers). Full grid CI sweep. Parity re-check. | Tie down scale; every bound cites run | Every bound has run id; CI runs grid parallel | **Linux/amd64 re-sweep** (P1–P5 on arm64/macOS). **Mesh time is tight bound,** not build. |
| **P7** | Socket cap (iso4762 ~13 rows, solid/cap_screw.py, 2 routes). Thread shared. | Socket cap is second shape on proven infra | Checklist complete; parity covers it | **Edition, key sizes UNVERIFIED** for 4762. |

### Key Gates

- **P1:** testclient needs httpx2; port quiet-host gate.
- **P2:** Pre-register before first run; quiet host or load cap; escape clause if worst > budget.
- **P3:** Postcondition gate (valid, 1 solid, closed-form oracle) before cache write; pair: multi-pose + control; left/mixed-hand.
- **P4:** Row tests pure data/maths, not kernel; sample kernel in P3 only.
- **P6:** Re-measure gzip/cache on threaded corpus; timeout from P3 worst case; memory re-sweep.

---

## Confidence Assessment

| Area | Confidence | Basis | Gaps / UNVERIFIED |
|---|---|---|---|
| **Stack: Thread construction** | HIGH (pinned); MEDIUM (overall) | 166 measured configs; twist sewn = 0 failures, 0.001% volume. | linux/amd64; design profile; CAD importer STEP |
| **Stack: ISO data** | HIGH (sources) | Verified cq_warehouse CSVs not citable; editions 2022/2023 confirmed. | Which edition to buy; Annex A values for M2–M4 |
| **Features: Core requirements** | MEDIUM-HIGH | Standards read from previews/SIS (HIGH); FDM from forums (LOW–MEDIUM). | Printed nominal bolt → bought nut validation needed |
| **Features: Printability** | MEDIUM (sources); LOW (values) | Vendor guides, forums say M5/M6+, 0.10–0.20 mm radial. **No controlled FDM study.** | Owner's printed test is the only default source |
| **Architecture: Design** | MEDIUM-HIGH | Registry verified on stack; import-linter contracts proven. | Left-hand full grid; mixed-hand pairs; building from URL without table |
| **Architecture: Build order** | MEDIUM-HIGH | Structural order from spur lesson. | P2 pair-check cost UNVERIFIED (could exceed timeout) |
| **Pitfalls: C1–C4 (kernel)** | HIGH (existence); MEDIUM (prevention) | C1, C2, C4 reproduced; C3 measured; all existence proofs. | Twist avoids C1 on linux/amd64?; full-grid pair reliability |
| **Pitfalls: C6–C7 (table)** | HIGH (liability) | Edition changes from official standards. | Which edition for M2–M4; DIN 934 M22 UNVERIFIED |
| **Pitfalls: C8 (printed)** | LOW (forums/blogs only) | 10x clearance spread (0.125–1.3 mm) in one forum = no default yet | Owner's printed test only source |

---

## Open Questions for Owner

1. **Q1 — M2–M4 nuts:** Options (a) cite Annex A, buy text; (b) nut range M5–M20; (c) drop M2–M4 from bolts. **Rec:** (a).
2. **Q2 — Printed bolt → bought nut:** Validate in P3; add bolt field v1.x if needed. **Rec:** validate first.
3. **Q4 — Profile:** Basic (flat, measured) or design (rounded, UNVERIFIED)? **Rec:** basic v1.
4. **Budget/schedule:** P2 cannot rush. If pair-check > 30 s/size, answer is "offline only" (tests + CLI, no API).

---

## Roadmap Dependency Graph

```
P1. Infra port + walking skeleton
    └─ Gives P2 a host; early parity test

P2. Thread spike (⊥ with P1, starts week 1)
    ├─ 4 questions: construction, mesh, pair cost, estimator
    └─ Output: decision entry, constants, no code

P3. Thread component (after P2)
    ├─ calc/thread.py, solid/helical.py, gate
    ├─ Bolt + Nut blank
    ├─ Pair proof (controls, verdicts)
    └─ Gate: solid count, isValid, oracle, watertight

P4. Tables + Info panel (after P3)
    ├─ ISO 261, 68-1, 965, 4017, 4014, 4032
    ├─ One test per row
    └─ derive() outputs panel

P5. Printed test (after P3, ⊥ P4)
    ├─ M6–M12, clearance steps, 3 samples
    └─ Output: default, floor, run log

P6. Operability (after P5)
    ├─ Full M2–M20 grid on CI
    ├─ Bounds + parity
    └─ Output: every bound cites run

P7. Socket cap v2 (after P6)
    └─ iso4762, 4 days if P1–P6 solid
```

---

## Gaps and Assumptions

### UNVERIFIED (must confirm)

1. linux/amd64 behavior (all numbers are macOS arm64; OCCT #1543 on both 7.9.3 and 8.0.1 but reproducibility unconfirmed).
2. Pair-proof cost on full M2–M20 grid (12 poses tested; ~60 proofs total, ~30 min sequentially).
3. Mesh volume accuracy (choice: precision call or mesh-based; not yet made).
4. Socket cap edition, dk smooth vs knurled, b formula for M12+.
5. Clearance sign convention (PROJECT.md is ambiguous on "inward").
6. STEP importer behavior in FreeCAD, Fusion, SolidWorks.

### Assumptions flagged for review

1. Twist construction robust on full grid (all sizes must be tested, failure frontier not monotone).
2. Five-turn segments are right size (measured: fewer triangles, no inversion; optimality unproven).
3. Lead-in chamfers sufficient for printing (P5 will validate).
4. 6g/6H reported with label has no legal risk (depends on label wording).
5. One printability floor M6–M12 applies to whole M2–M20 (pitch-to-nozzle ratio changes per size).

---

## Sources

- **Stack.md:** MEASURED (pinned pair construction grid, cq_warehouse interop); SOURCE (PyPI, GitHub API); ISO-PREVIEW (2022/2023 standards)
- **Features.md:** HIGH read (ISO standards text); MEDIUM (vendor guides, forums agree on 0.10–0.20 mm, M5/M6 floor); LOW (individual posts, one SLS paper)
- **Architecture.md:** VERIFIED on pinned stack; MEASURED build times, mesh, volume, pair costs; gaps linux/amd64, STEP round-trip
- **Pitfalls.md:** HIGH C1–C4 reproduced; MEASURED on loaded host; gaps linux/amd64, full-grid pair reliability, printed test results
- **PROJECT.md:** HIGH owner constraints (L01–L06); UNVERIFIED standard numbers (from memory)

---

*Synthesis of 4 parallel agents: STACK, FEATURES, ARCHITECTURE, PITFALLS*  
*Completed: 2026-10-05*  
*Confidence: MEDIUM-HIGH overall; HIGH kernel/standards; MEDIUM-LOW printed behavior*
