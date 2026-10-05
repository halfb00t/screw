# Pitfalls Research

**Domain:** Parametric ISO metric threaded-fastener generator (hex bolt/screw ISO 4014/4017, hex nut ISO 4032, socket cap ISO 4762 later), real helical threads, FDM-printable mating pairs, STL/STEP export, web UI + HTTP API + CLI on one parameter model; CadQuery 2.8.0 / cadquery-ocp 7.9.3.1.1 (the pinned pair), FastAPI, Python 3.12.
**Researched:** 2026-10-05
**Confidence:** MEDIUM-HIGH overall. The kernel and table findings are HIGH (reproduced on the pinned pair; read from standard text). The printing findings are LOW (no controlled FDM study exists in what I could reach). Every number is tagged; anything unmeasured is marked UNVERIFIED.

## How to read this file

**Evidence tags** (this project treats an unmeasured number as unknown):

| Tag | Meaning | Confidence |
|-----|---------|------------|
| `[M]` | Measured by me on the pinned kernel pair on this machine (Apple M2 Max, 12 cores) during this research. Reproduced failures are HIGH as *existence proofs*. Timings are NOT bounds: the host was shared (1-min load 4 to 86 during the probes, see "Probe record"). | HIGH (existence) / UNVERIFIED (as bound) |
| `[P]` | Read from standard text: ISO 4017:2022 and ISO 4032:2023 official previews (iTeh), ISO 4014:2011 full-text copy (withdrawn edition). | HIGH (MEDIUM for the 4014 copy) |
| `[C]` | Read from source code (`cq_warehouse` 0.8.0 `thread.py`, `fastener.py`). | HIGH |
| `[D]` | Derived arithmetic from `[P]` values or from ISO 68-1 geometry. | HIGH if inputs are |
| `[W]` | Web search or fetch, not cross-checked (`classify-confidence` gives LOW for websearch/webfetch unless verified, MEDIUM if verified). | LOW unless stated |
| `[S]` | Sibling project spur documents (`RETROSPECTIVE.md`, decision log, bench README). | HIGH |

**Working phase labels** (the roadmapper may renumber; PROJECT.md says first release = infra port + thread spike + hex bolt + hex nut as a proven pair, socket cap second):

| Label | Content |
|-------|---------|
| P1 | Infra port from spur (pool, app, cli, records, viewer, gate, harness, ruleset, docker) |
| P2 | Thread spike: construction choice, correctness oracle, build-time and mesh/STEP measurement, before any field exists |
| P3 | Thread + bolt + nut geometry and the kernel mating proof |
| P4 | ISO tables, presets, info panel numbers |
| P5 | Print validation: clearance default, printable-size floor (human checkpoint) |
| P6 | Operability bounds on the full allowed grid (timeout, memory, gzip, workers, caps) and three-interface parity |
| P7 | Socket head cap screw (ISO 4762), second release |

## Headline findings (read first)

1. **A "valid" solid with the wrong content is the dominant failure mode, not an exception.** On the pinned pair, a swept-tooth + `union` with a core cylinder returned a solid with `isValid() == True` and the core silently dropped in 8 of 15 configurations, an invalid solid in 1, a `Null TopoDS_Shape` exception in 5, and the right answer in 1 (`[M]`, C1). `cq_warehouse`'s own `chamfer` end finish at 80 turns returned 3 solids, 17.4 mm3 instead of about 1,680, `isValid() == True`, and a 184-byte STL (`[M]`).
2. **`Shape.Volume()` is not an honest number on helical surfaces.** CadQuery's default volume read 15 % low to 21 % high on valid thread solids; the `eps=1e-6` form of the same OCCT call matched an independent analytic reference to 0.1 % at about 0.1 to 0.2 s (`[M]`, C2). Printing `Volume()` for a threaded part breaks the project's first standing rule.
3. **Build cost tracks turns, and the worst case is the smallest pitch at the longest standard length.** ISO 4017's greatest standard length (10d or 200 mm) is 50 to 80 turns for every size M2 to M20 (`[D]`). Fuse cost grew from 0.6 s (10 turns) to about 80 s (160 turns) on a loaded host; `chamfer` ends cost about 6x `fade` at equal turns (`[M]`, C3). Nothing here is a bound yet; the spike must produce them.
4. **Table liability is bigger than "transcription".** ISO 4032:2023 covers M5 to M39 only; M2 to M4 nuts moved to an informative annex, so PROJECT.md's "M2 to M20 for every table" has no normative nut row below M5 (`[P]`, C6). ISO 4014/4017 were re-issued in 2022 and 4032 in 2023; `e` and `dw` are minimums, `s` is nominal = max, `b` is a reference value that depends on the length band, and product grade A/B changes `s`, `e`, `dw` with length (`[P]`, C7).
5. **The owner's "4759" is the wrong standard for 6g/6H.** ISO 4759-1 is "Tolerances for fasteners: product grades A, B and C". The 6g/6H numbers come from ISO 965-1 (principles, fundamental deviations) and ISO 965-2 (limits of sizes) (`[W]`, MEDIUM; confirm).
6. **The printed-pair evidence base is anecdotal.** Reported clearances for similar sizes span 0.125 mm to 1.3 mm in one forum thread alone; blog rules say 0.1 to 0.2 mm per side and "M5/M6 and up". No controlled study of clearance x orientation x layer height was found (`[W]`, LOW). The default must come from the project's own printed test, as PROJECT.md already says.

---

## Critical Pitfalls

### Pitfall C1: Helical boolean returns a "valid" solid with the wrong content

**What goes wrong:** `core.union(swept_tooth)`, `blank.cut(swept_groove)` or `a.intersect(b)` on helical solids returns without error and `isValid()` is `True`, but the result is the tool alone, the core minus almost nothing, or a compound of fragments. Observed on the pinned pair (`cadquery 2.8.0`, `cadquery-ocp 7.9.3.1.1`, `[M]`):

| Construction | Result |
|--------------|--------|
| Swept trapezoid tooth (`isFrenet=True`, root embedded 0.05 P) fused to a core cylinder, 15 size/length cases (M2..M12, 6 to 35 mm) | 1 correct, 8 silently dropped the core (union volume = tool volume, `isValid` True), 1 invalid, 5 raised `Null TopoDS_Shape` |
| Same tool, same M6 x 10, only the axial offset changed | core dropped at offset -1.0 P; at -0.5 P and -1.37 P the union volume read core + tool by the default estimator (not re-checked with the precise estimator of C2, so "right" is UNVERIFIED). Hypothesis (mine): in the failing case the flank crosses the end plane exactly at the cylinder seam (angle 0) |
| Swept groove cut from an M6 x 10 blank, then trimmed | removed about 6 mm3; the groove volume should be about 52 mm3 (`[D]`); silent partial failure (single probe, UNVERIFIED as a general statement) |
| `cq_warehouse` `IsoThread` with `chamfer` end, M6 x 80 (80 turns), fused to a core | 3 solids, 17.4 mm3 (expected about 1,680), `isValid` True, STL 184 bytes; reproduced twice |
| `cq_warehouse` `fade`/`raw` ends, same fuse | 10 cases built with no exception and `isValid` True; 7 of them re-measured with the precise estimator (C2) and all matched the reference (1.000 to 1.001). The other 3, including a `raw`/`raw` M6 x 10 that returned 2 solids, were not re-measured |

The same bug family is open upstream: OCCT issue #1543 (boolean cut with a helical swept tool "silently removes nothing" when the tool exits through a planar face, depends on where the helix crosses the cylinder seam, reported on OCCT 7.9.3 and 8.0.1; the pinned pair is the 7.9.3 line, mapping of `cadquery-ocp 7.9.3.1.1` to OCCT 7.9.3 is UNVERIFIED). A CadQuery-list thread reports non-manifold output when the cut tool extends beyond the cylinder and a French "Courbes non jointives" crash when the profile starts below it (`[W]`, LOW; old OCCT).

**Why it happens:** the helical sweep gives periodic B-spline faces; intersecting them with a cylinder's seam and planar end faces loses boundary vertices (#1543's stated root cause). Round numbers looked like the worst inputs in the probe (integer `L/P` failed, `L/P` = 10.25 passed); my inference is that integer turns put the end-plane crossing exactly on the seam, consistent with #1543 but not isolated. A nut thread is the same trap by construction: the groove or ridge always exits through the top and bottom planar faces.

**How cq_warehouse avoids it (`[C]`):** it does not sweep. It builds four ruled surfaces between helical wires on the apex and root radii and closes them into a solid (`make_thread_faces`). `raw` and `fade` ends use no boolean at all (documented 0.018 s and 0.087 s); `square` is a `cut` (0.370 s) and `chamfer` an `intersect` with a chamfered cylinder (1.641 s), the slow and fragile ones. It then fuses a separate core cylinder (`shank.fuse(thread)`), and the thread's root radius is deliberately 0.001 mm inside the core with this comment in the code: "inaccuracies in parametric curve calculations can result in a gap which causes the OCCT core to fail when combining with other object (like the core of the thread)". BOSL2 (OpenSCAD) builds a polyhedron directly and handles ends with `blunt_start` + `lead_in`; build123d's `bd_warehouse` keeps the same four end finishes (`[W]`).

**How to avoid:**
1. P2 chooses the construction by a measured, pre-registered comparison on the whole allowed grid, not on one nice size. Candidates seen working in these probes: ruled-surface thread + core fuse (cq_warehouse lineage), and a sibling's twist-extruded cross-section (no boolean, volume within 1e-3 of analytic, builds in 0.04 to 0.11 s, but `BRepOffsetAPI_MakePipeShell::MakeSolid` failed at 80 and 160 turns for M6 and succeeded for M3 at 80 turns, `[M]`; see C3).
2. Make the end treatment part of the construction (fade-out / run-out), not a trailing boolean. ISO already allows it: ISO 4014/4017 give "incomplete thread u <= 2P" under the head and a chamfered end with beta = 15 to 30 degrees per ISO 4753 (`[P]`), so a faded run-out near the head is on-spec; the chamfered tip is the one place a boolean may be unavoidable, so it needs its own measured envelope.
3. Put a **build gate inside `model.py`** that runs after every build and cannot be bypassed: exactly 1 solid; `isValid()`; precise volume within a stated fraction of a pure-math volume (computed in `calc.py`, sharing no code with the production path, spur's oracle pattern `[S]`); mesh watertight (C11). A gate failure is a failed build: not cached, not served, not exported.
4. A regression test for the gate needs a **positive control**: feed it the dropped-core result (tool-only solid) and assert it trips. A gate that was only ever shown passing is the WR-06 lesson (`[S]`: "a regression test is only a test if the bug it names makes it fail").
5. Include integer-turn and integer-millimetre lengths in every sweep (L/P integral, L integral). They failed first.
6. Pin the kernel pair (L06 already does); a pair bump re-runs the thread fixture before merge.

**Warning signs:** union volume within 1e-3 of the tool volume; `len(Solids()) > 1` after a fuse; STL under a few KB; exceptions `Null TopoDS_Shape`, `BRepOffsetAPI_MakePipeShell::MakeSolid`, `Courbes non jointives`; a build that is fast for 40 turns and fails at 41; a result that changes when the thread is rotated by an arbitrary angle.

**Phase to address:** P2 (construction + oracle chosen), P3 (gate enforced in the production path), P6 (full-grid sweep).

---

### Pitfall C2: The kernel's own `Volume()` is not an oracle on helical surfaces

**What goes wrong:** `cadquery`'s `Shape.Volume()` uses OCCT GProp with default (non-precision) integration. On valid thread solids it was off by large margins (`[M]`, `cq_warehouse` fade/raw thread fused to a core, reference = core + Pappus tooth volume, `[D]`):

| Case | `Volume()` | `eps=1e-6` | triangle-based | Reference |
|------|-----------|------------|----------------|-----------|
| M6 x 10 | 194.5 | 229.8 | 229.7 | 229.6 |
| M6 x 20 | 395.4 | 459.3 | 457.1 | 459.1 |
| M6 x 40 | 1028.4 | 919.2 | 961.8 | 918.3 |
| M8 x 20 | 999.5 | 827.7 | 827.4 | 827.2 |
| M12 x 35 | 2839.3 | 3302.0 | 3299.6 | 3300.6 |

`Volume()/reference` ranged 0.847 to 1.208; the `eps` form ranged 1.000 to 1.001. An STL's own signed volume matched the reference to 0.1 % (458.8 to 459.2 vs 459.3) while `Volume()` read 395.4 for the same shape.

**Why it happens:** Gauss integration over bi-cubic helical B-spline faces converges slowly; the precision-controlled call (`BRepGProp.VolumeProperties_s(shape, props, eps, False, False)`) iterates to a tolerance. A twist-extruded section (single smooth face) agreed with the default call (vol/ref 1.0000), so the error depends on the construction, which makes it worse: it passes in one construction and silently fails in another.

**Consequences:** (a) a printed volume or mass on the info panel is wrong by up to about 20 %: a direct hit on L08 ("a number the tool prints is a number someone will cut metal to"); (b) any build gate or interference proof built on `Volume()` has a noise floor of tens of percent, so it can pass a broken part and fail a good one (C1, C4); (c) spur's oracle-vs-kernel tests (`abs=1e-9` closed forms) will not port as-is.

**How to avoid:** never print or assert on bare `Volume()` for threaded shapes. Use the `eps` call, or integrate the mesh, and agree the choice in P2. Treat any number that is not cross-checked by an independent analytic or mesh reference as unknown and warn instead (L08). If no reference is available for a quantity (for example mass of a nut with a faded run-out), omit it.

**Warning signs:** two construction variants of the same part disagree on volume by more than the geometric difference; `Volume()` and mesh volume differ by more than 1 %.

**Phase to address:** P2 (estimator chosen, snippet in the Probe record), P4 (info panel numbers each carry their oracle).

---

### Pitfall C3: Build time scales with turns, not diameter; the failure frontier is not monotone; bounds cannot be extrapolated

**What goes wrong:** a bound set from the nicest sizes (M6 x 20) is violated by the worst allowed configuration, and the worst configuration is not the biggest bolt.

**Measured (`[M]`, single runs, `cq_warehouse` ruled-surface thread + core fuse, host load average 13 to 86 on 12 cores during these runs, so wall times are inflated and noisy; NOT bounds):**

| Config | Turns | Build (s) | STL tris at tol 0.05 / ang 0.2 | STL size | STEP size |
|--------|-------|-----------|-------------------------------|----------|-----------|
| M6 x 10, fade/raw | 10 | 0.59 | 6.8k | 0.34 MB | 0.52 MB |
| M6 x 20 | 20 | 1.47 | 11.4k | 0.57 MB | 0.86 MB |
| M6 x 40 | 40 | 5.73 | 17.2k | 0.86 MB | 3.67 MB |
| M6 x 80 | 80 | 13.4 | 34.0k | 1.7 MB | 13.0 MB |
| M6 x 160 | 160 | 79.6 | 66.1k | 3.3 MB | 48.2 MB |
| M3 x 40 (P 0.5) | 80 | 15.3 | 34.0k | 1.7 MB | 7.3 MB |
| M3 x 80 | 160 | 17.1 | 87.3k | 4.4 MB | 5.0 MB |
| M20 x 100 (P 2.5) | 40 | 5.09 | 22.3k | 1.1 MB | 3.8 MB |
| M6 x 20, chamfer/raw | 20 | 8.64 | 14.7k | 0.73 MB | 2.4 MB |
| M6 x 80, chamfer/raw | 80 | 52 to 67, **broken result (C1)** | n/a | 184 B | n/a |

Reading: M6 x 40 (5.7 s) and M20 x 100 (5.1 s) have equal turns and about 3x different diameter, so turns dominate (single runs: UNVERIFIED). Growth from 40 to 160 turns is steeper than linear. `chamfer` costs about 5.9x `fade` at 20 turns (documented ratio 19x on the thread alone). M3 x 80 (160 turns) building faster than 80 turns is load noise, which is itself the point. STL size grows roughly linearly with turns (about 410 to 680 triangles per turn on this construction); STEP grows faster than linearly in the M6 series.

**Turns at the greatest standard length, ISO 4017:2022 ("greatest standard length <= 10d or 200 mm", `[P]`; `[D]` arithmetic):**

| Size | P | l max (mm) | Turns |
|------|---|-----------|-------|
| M2 | 0.4 | 20 | 50 |
| M2.5 | 0.45 | 25 | 56 |
| M3 | 0.5 | 30 | 60 |
| M4 | 0.7 | 40 | 57 |
| M5 | 0.8 | 50 | 63 |
| M6 | 1.0 | 60 | 60 |
| M8 | 1.25 | 80 | 64 |
| M10 | 1.5 | 100 | 67 |
| M12 | 1.75 | 120 | 69 |
| M16 | 2.0 | 160 | 80 |
| M20 | 2.5 | 200 | 80 |

ISO 4014's threaded portion is short (b = 2d + 6 / 2d + 12 / 2d + 25 mm by length band, so at most about 26 turns for M20 and about 70 for M2, `[P]`/`[D]`), so partial-thread bolts are cheap; **full-thread ISO 4017 at long lengths is the whole risk**, and a user can also type `thread_length` freely on a 4014 bolt. Nut threads were not measured here (UNVERIFIED): at most about 10 turns for common thicknesses, but the planar-exit boolean (C1) applies.

**Why it happens:** each turn adds a periodic face pair that every boolean must intersect with the core, and the intersection graph grows with turns. The sibling twist-extrude construction removes the boolean cost but moves the limit to the sweep itself (exceptions at 80 turns for M6, success at 80 turns for M3).

**How to avoid:**
1. The spike (P2) is pre-registered like spur 13-02 (`[S]`): method, predictions and escape clause committed before the first run; quiet-host gate with a cap; load read at both ends of each run and labelled by when it was taken (spur WR-07).
2. Sweep **every allowed (size, length, hand, thread_length, end finish) combination**, not samples. The failure frontier is not monotone (C1: fails at 20 turns, works at 10.25), so an extrapolated cap is a guess. Estimate: 11 preferred sizes x tens of lengths x 2 types x 2 hands is hundreds of builds; at seconds each the sweep is an hours-scale campaign in `bench/`, not in `make verify`.
3. Cap by **turns** (`L/P`), expressed as a `le` in the schema derived from the measurement and cited (L03 cap-and-warn or 422 naming the fields), and per size, since a fixed mm cap lets M2 through at 3x the turns of M20.
4. Re-measure the Docker image separately (linux/amd64 and arm64); spur's L17 showed the container is a different instrument (`[S]`).
5. Run the sweep with the per-build timeout killing the worker (spur `BuildPool`), because OCCT booleans have no cooperative cancel.

**Warning signs:** a bound quoted to two significant figures with no run id; time roughly constant between two lengths that should differ 2x (noise floor); a timeout set equal to the slowest measured build (no headroom).

**Phase to address:** P2 (measure), P6 (write the bounds, `le`, timeout; sweep the full grid).

---

### Pitfall C4: The mating proof that cannot fail

**What goes wrong:** "a kernel-level interference check proves the pair" is built as `common(bolt, nut).Volume() == 0` at one relative position. It passes when the boolean silently failed (C1 returns empty or tool-only), when `Volume()` is inaccurate (C2), at the one phase tested, and, at clearance 0, it is a boolean on coincident helical flank surfaces, the most fragile case there is.

**Why it happens:** a zero is the answer a broken boolean gives. Nothing in the check says the boolean worked.

**How to avoid:**
1. **Positive control in the same call**: compute interference at a deliberately negative clearance (for example -0.1 mm) and require it to be non-zero and close to an analytic estimate; only then trust the zero at the real clearance.
2. Check at several axial phases (at least 3, including a half-pitch offset) and across the full engagement length; a helical pair is invariant under axial slide only if both helices have the same pitch and hand, which is exactly what the check should prove.
3. Never prove at clearance 0 with a boolean; use clearance > 0 for the boolean proof and an analytic statement for 0.
4. Include left-hand pairs and a mixed-hand pair that must fail.
5. Precise volume or mesh volume only (C2).
6. Cost: unmeasured here (UNVERIFIED). Measure `common` of two 20-turn threaded solids in P2 before promising it in a gate.
7. Reword the success criterion into two: SC-kernel (automated, above) and SC-printed (manual-only, human checkpoint listed once in VALIDATION.md's manual-only table, the spur v0.2 pattern `[S]`). "Threads together when printed" cannot be a kernel-verifiable statement.

**Warning signs:** the only test is `assert interference == 0`; no test where the pair is meant to collide; the proof passes for a bolt with the wrong pitch.

**Phase to address:** P3.

---

### Pitfall C5: Clearance sign, convention and the flank geometry

**What goes wrong:** (a) PROJECT.md says the nut "carries" the clearance and "its thread grows inward". A hole that grows *inward* would add interference; clearance means nut material retreats from the bolt axis (hole diameters grow). The sign convention is ambiguous in the brief (UNVERIFIED reading; resolve with the owner before P3). (b) A radial offset is not a flank gap. For a 60-degree thread each flank is 30 degrees from the radial direction, so the flank-normal gap is `c * sin(30 deg) = 0.5 c` and axial backlash is about `1.155 c` (`[D]`). "0.2 mm clearance" therefore leaves 0.1 mm between flanks, which is the same order as FDM over-extrusion and elephant-foot error. (c) Implementing clearance as a uniform scale of the nut (123DScrew uses `1 + static_tol/major_d`, `[W]`) rescales pitch, flats and thickness too and gives a different effective clearance per size. (d) Normal-offset and radial-translation conventions give different crest-flat widths; the info panel must say which it is.

**How to avoid:** define `clearance` once in `docs/` as a signed radial translation of every nut thread surface in millimetres, positive = hole grows, with the flank-normal and axial values *derived and displayed*, and test that interference volume is monotone non-increasing in `clearance` (needs the C4 positive control). Never scale. Prior art consistent with nut-side clearance: BOSL2 applies `$slop` to internal threads only, and 123DScrew puts it on the insert (`[W]`, MEDIUM-LOW; cited for design agreement, not for values).

**Warning signs:** a clearance default expressed as a percentage or a ratio; bolt and nut both change when `clearance` changes; interference rising with clearance.

**Phase to address:** P3 (definition and tests), P5 (value).

---

### Pitfall C6: Table liability, part 1: editions, scope and the owner's standard numbers

**What goes wrong:** rows are copied from a source that is a different edition, a different standard, or out of scope for the claimed sizes. Verified now (`[P]` unless marked):

| Owner's number (from memory) | Status |
|-----------------------------|--------|
| ISO 68-1 (basic profile) | Exists; a 2023 edition exists (`[W]`). Profile: H = 0.866025 P; crest truncated H/8, root H/4; basic minor d1 = D1 = d - 2(5/8)H (`[W]`, consistent with `[D]`). Confirm edition. |
| ISO 261 / 262 | Exist; 262 has a 2023 edition (`[W]`). M14, M18, M22 are second choice (`[W]`); ISO 4017:2022 and 4032:2023 bracket M3.5, M7, M14, M18, M22 as non-preferred (`[P]`). |
| ISO 4014 | 2011 edition (4th) read in full; withdrawn and replaced by a 2022 edition (`[W]`, LOW-MEDIUM). I have not read the 2022 tables: UNVERIFIED. |
| ISO 4017 | **6th edition, 2022-06**, "cancels and replaces the fifth edition (ISO 4017:2014), technically revised": tables restructured, M7 added, dw,min for d <= M5 changed from smin-IT16 to smin-IT15, greatest standard lengths restored, shortest = 2d rounded. |
| ISO 4032 | **5th edition, 2023**, replaces 2012. **Scope M5 to M39.** "nuts with D < M5 and D > M39 ... have been shifted to informative Annex A"; M7 added; da,max, dw,min, mw,min now two decimals. Annex A was not in the preview: values for M2, M2.5, M3, M4 nuts are UNVERIFIED. |
| ISO 4762 | 2004 edition (4th) shown as current in searches; a newer edition is UNVERIFIED (`[W]`). |
| ISO 965 | 965-1 = principles and basic data; 965-2 = limits of sizes (1998, +A1:2021, and a 2024 edition covering 6H/6g M1.6 to M100); correct sources for 6g/6H numbers (`[W]`, MEDIUM). |
| "965/4759" | **4759-1 is "Tolerances for fasteners, Part 1: Bolts, screws, studs and nuts, product grades A, B and C"** (`[P]`: cited as a normative reference inside 4014/4017/4032). It is not a thread-tolerance standard. |

**Consequences:** a row that says "ISO 4032 M3 nut" with no normative source; a table from the 2014/2012 editions presented as current; 6g numbers cited to the wrong standard. PROJECT.md's own rule ("a row without a cited source does not ship") then removes M2 to M4 nuts unless Annex A (informative) is accepted as a source, which is an owner decision (stop-and-ask).

**How to avoid:**
1. Cite **standard, edition year, table and column** in each row; one verification test per row (pure data test, no kernel).
2. Use the standards' own text, not secondary tables. Official previews (iTeh) contain the dimension tables for 4017:2022 and 4032:2023; buying or reading 4014:2022 and ISO 4762 is a P4 task.
3. Record edition drift as a decision (L-number): which edition each row follows and why.
4. Decide up front whether the licence of embedding ISO table values is acceptable (dimensions are facts; reproducing tables wholesale is a different matter; legal position UNVERIFIED, owner call).
5. Count rows honestly: the preferred set in M2 to M20 is M2, M2.5, M3, M4, M5, M6, M8, M10, M12, M16, M20 = 11 sizes (M14 and M18 are non-preferred, M7 and M3.5 likewise `[P]`).

**Warning signs:** a table with a source URL but no edition year; the same size showing different `s` in two tables of one source; a size that appears in the code but not in the cited standard's scope.

**Phase to address:** P4 (and P7 for 4762: confirm edition; head diameter `dk` has separate max values for smooth and knurled heads, from memory, UNVERIFIED).

---

### Pitfall C7: Table liability, part 2: what a number means (nominal, max, min, reference, grade)

**What goes wrong:** the value in a cell is used as if it were the geometric dimension. From the standards (`[P]`):

- **`s` across flats is "nom. = max."** with a separate min. `e` across corners and `dw` are **min only**. `k` has nom, max and min. Nut `m` has **max and min, no nominal**. A hex built as `s` has prism corners at `s / cos 30 = 1.1547 s` (M10: 18.475), above the table `e,min` (M10: 17.77) because the head is chamfered (beta 15 to 30 degrees in ISO 4014's figure). A plain prism passes the minimum but then any "across corners" printed must be the prism's, not the table's, and it must be labelled (`[D]`).
- **`b` (thread length) is a reference ("b ref.") that depends on the length band:** 2d + 6 for l <= 125, 2d + 12 for 125 < l <= 200, 2d + 25 for l > 200 (checked against M2..M20 in 4014:2011 Table 1, e.g. M10: 26 / 32 / 45; M12: 30 / 36 / 49). Plain `b` per size is wrong for long bolts. The grip length range follows from it: `lg,max = l,nom - b`, `lg,min = lg,max - 5P`. So `thread_length` for the ISO 4014 preset is a function of (size, length) and is a reference, not a toleranced edge. For `l <= b` the partial thread degenerates to full thread, and the standard's length table marks short lengths "ISO 4017 is recommended".
- **Product grade A vs B changes values and depends on length.** In ISO 4014: grade A for M1.6 to M24 and l <= 10d or 150 mm (the shorter), grade B otherwise. M12: `s,min` 17.73 (A) vs 17.57 (B); `e,min` 20.03 vs 19.85; `dw,min` 16.63 vs 16.47. In ISO 4032:2023 grade A is M5 to M16 (Table 1) and grade B M18 to M39 (Table 2). A row key of (size) is insufficient; it is (standard, edition, size, length).
- **DIN contamination.** ISO 4017/4032 vs DIN 933/934 across flats: M10 16 vs 17, M12 18 vs 19, M14 21 vs 22, M22 34 vs 32 (ISO from `[P]`; DIN from several secondary sources `[W]`, MEDIUM). DIN 934 nut thicknesses also differ from ISO 4032 (ISO M8 `m,max` 6.80, M10 8.40, M12 10.80, M16 14.80, `[P]`; DIN 934 values smaller, from memory, UNVERIFIED). A widely linked secondary site printed M10 `s` = 17.00 and M12 = 19.00 inside a table headed ISO 4014/4017 and, as retrieved by the fetch tool, put 29.16 and 35.00 (these are `s,min`) in the `e,min` column for M20 and M24 (actual `e,min` 32.95 and 39.55 in ISO 4032:2023). That may be an extraction artefact, which is the point: secondary tables are not a source.
- **Tolerance numbers vs nominal geometry.** The info panel will report 6g/6H min/max while geometry is nominal (PROJECT.md). For a bolt, 6g `d,max` is below nominal (the fundamental deviation for P = 1 is about -26 um, M6 6g `d,max` about 5.974 mm, from memory and from the formula `es = -(15 + 11P)` um, UNVERIFIED), so the generated nominal 6.000 mm shank sits above the very limit the panel prints. Someone who machines the generated geometry produces a part outside the printed tolerance.

**How to avoid:** model each cell with its semantics (`nom`, `max`, `min`, `ref`, `grade`), name the field after the semantics, and let geometry choose which cell it builds from, in a documented table in `docs/`. Info panel labels must say "from ISO 4017:2022 row (min)" versus "measured on this geometry". Print 6g/6H as "limits for a bought part, not this model's geometry", or do not print them (L08); this is an owner decision. A row test asserts the invariants the standard implies (`e,min` below `s / cos 30`, `lg,max = l - b`, grade rule from length).

**Warning signs:** a table column named `s` with no suffix; a single `b` per size; an `e` column used to build geometry; a test that merely re-types the row.

**Phase to address:** P4.

---

### Pitfall C8: Printed-pair failure modes that a kernel check cannot see

**What goes wrong:** the pair interferes by zero in the kernel and still binds on the printer. Candidate causes and the state of evidence:

| Cause | Mechanism | Evidence |
|-------|-----------|----------|
| Elephant foot at the bed face | first layers flare, jam the thread entry | blog-level `[W]` (LOW): a 45-degree chamfer of about 0.8 to 1.5 mm on the starting face of both threads, as lead-in |
| Over-extrusion / perimeter squish | inflates flanks; flank gap is only `c/2` for radial `c` (C5) | `[D]` for the geometry, `[W]` LOW for the printer part |
| Pitch too fine for the nozzle | crest flat P/8 and tooth depth 5H/8 are below line width at small sizes | `[D]`: M2 crest flat 0.05 mm, depth 0.217 mm; M3 0.063 / 0.271; M4 0.088 / 0.379; M6 0.125 / 0.541; M10 0.188 / 0.812 (P = 0.4 .. 1.5; depth = 0.5413 P). Against a 0.4 mm nozzle and a reported 0.1 to 0.2 mm radial clearance, M2/M3 tooth depth is of the order of the clearance itself |
| Overhang | lower flank is 60 degrees from vertical when the axis is vertical | `[D]`; "threads have overhangs > 45 degrees", support-free needs fine layers `[W]` LOW |
| Orientation | vertical axis (threads in XY layers) is the common advice; horizontal gives stair-stepped flanks and weaker bolts | `[W]` LOW; 123DScrew: "print screws vertical; inserts vertical", layer <= 0.2 mm for M6-ish, 3 to 4 perimeters (`[W]`) |
| Hole undersize | FDM holes read 0.1 to 0.3 mm undersized | `[W]` LOW |
| Seam | slicer-side; z-seam on a thread flank is a bump | no source; slicer setting, not geometry (UNVERIFIED) |

**What evidence actually exists:** none controlled. One peer-reviewed paper (`[W]`, MEDIUM, **SLS PA12**, M8 holes, orientation not stated) says printing threads "is feasible only for sufficiently large thread dimensions, typically those greater than M6". Blogs say "M5 or larger", "0.2 to 0.4 mm total diametral offset", "0.2 to 0.4 offset for M8 and up". A Prusa forum thread shows one user at 1.3 mm tolerance on a 7 mm screw (0.15 mm layers, 0.4 mm nozzle, PLA) and another quoting 0.125 mm, with the conclusion "trial and error is the only way" (`[W]`, LOW, two reports, not corroborating). That is a 10x spread on the same quantity.

**How to avoid:**
1. Treat every clearance number above as a prior, not a default. The default value comes from the owner's printed test (PROJECT.md) and is recorded as a measured result with printer, nozzle, layer height, material and orientation.
2. Make the test a designed matrix: sizes {M6, M8, M10, M12} (M12 is the safest first print), clearance steps of 0.05 mm, vertical axis, 0.4 mm nozzle, two layer heights, one lead-in chamfer variant, three samples each. Pre-register the acceptance rule ("turns by hand without tools over the full engagement").
3. Derive and show the **printability floor** from the printed test: a warning (not a refusal, L02 cap-and-warn) when tooth depth is below the demonstrated value. The floor is a measured constant with its test cited, not a number from a blog.
4. Provide a lead-in chamfer on both ends of the nut bore and a chamfered bolt tip as geometry (ISO 4753 beta 15 to 30 degrees on the bolt, `[P]`); export with the thread axis along Z in the STL so the user's default slicer orientation is the vertical one (UNVERIFIED that users do not re-orient).
5. The L05 trap: once a default for `clearance` ships, every shared link that omitted it depends on it. Settle the number **before** the first release, or keep the default conservative and ship the printed-test value as a preset (presets fill mm fields; defaults do not move). This is a design suggestion for the owner, flagged ASSUMPTION.

**Warning signs:** a default that came from a blog; a pair printed once; a test print at a single size.

**Phase to address:** P5 (human checkpoint), P3 (lead-in geometry).

---

### Pitfall C9: STL and STEP size, mesh tolerance versus thread depth, and mesh state on a cached solid

**What goes wrong:** (a) triangle counts are far above spur's gear: 7k to 87k at 10 to 160 turns (`[M]`, ruled-surface construction, tol 0.05 mm, 0.2 rad), and **construction-dependent by 6x to 16x** (about 410 to 680 triangles per turn vs 2,600 to 6,700): the sibling twist-extruded section with a spline flank gave 26k triangles at 10 turns, 114k at 20, 269k for M20 x 100, 422k for M3 x 40 at the same tolerances (`[M]`). (b) The mesh deviation tolerance must be small against the tooth depth (0.22 to 1.35 mm across M2 to M20), or the flanks become polygons; a tolerance chosen for gears will not carry. (c) **Mesh history leaks**: exporting the same shape at three tolerances in sequence gave 11,376 triangles at 0.05/0.2, 23,016 at 0.01/0.1, and 23,016 again at 0.1/0.5: the coarse request reused the finer mesh already attached to the shape (`[M]`). This is exactly spur L24 ("a cached solid never carries a mesh: STL export meshes a copy") and it matters more here because a threaded mesh is large. (d) STEP of a modelled thread grows faster than linearly: 0.52 MB at 10 turns, 3.7 MB at 40, 13 MB at 80, 48 MB at 160 (`[M]`, default exporter; the superlinearity is UNVERIFIED as to cause). What downstream CAD does with that is UNVERIFIED (not tested).

**Watertightness:** the STL of the fade/raw M6 x 20 shank had 0 unpaired directed edges and 0 degenerate triangles at all three tolerances, so non-manifold output was not seen with the ruled-surface construction (`[M]`, one shape, vertex weld at 1e-5 mm). The CadQuery-list report of non-manifold output (`[W]`, LOW) relates to cut-beyond-boundary constructions; do not assume it never occurs.

**How to avoid:**
1. Port spur L24 as-is and extend its content-equivalence check (spur: triangle count + decoded volume, `[S]`; bytes match in only 8 of 20 reruns) with a watertight edge-pairing check and mesh-volume vs analytic volume (C2).
2. Tolerance for the viewer and the STL is derived from tooth depth (for example a fraction of 5H/8), with the fraction picked by a measured deviation-versus-triangle-count curve in P2. Separate preview and export tolerances only if the preview is clearly labelled and the numbers shown are not computed from the preview mesh.
3. Re-run spur's gzip and export-cost harnesses on threaded parts; do not carry spur's gzip level or cache size (L19). The triangle count cap (a `le` on turns, C3) is what bounds payload size.
4. STEP: decide in P2 whether the default export is the modelled thread (large, slow in importers, UNVERIFIED) and whether a size warning is shown; measure STEP size and time with the same sweep.

**Warning signs:** the same request returning different triangle counts depending on what was exported before; a gzip level chosen on a gear; a preview that looks round because the tolerance is larger than the tooth.

**Phase to address:** P2 (measure), P6 (gzip, cache, payload bounds).

---

### Pitfall C10: Thread ends, run-out and the first/last partial turn

**What goes wrong:** the thread is built as a long helical solid and trimmed to the shank with a planar cut or a chamfer cone. That trailing boolean is the slow (chamfer about 19x slower than fade on the thread alone per cq_warehouse docs; about 6x here with a core) and fragile one (C1, broken result at 80 turns), and the partial first/last turn creates the slivers and thin crescents that downstream tools reject.

**Why it happens:** a turn that starts and ends mid-pitch meets the end plane at an arbitrary phase; the sliver at the plane has zero thickness at one end.

**How to avoid:** use a fade-out (thread height drops to zero over 90 degrees of arc in `cq_warehouse`/`bd_warehouse`) at the head side, matching ISO's incomplete thread u <= 2P (`[P]`), and a controlled chamfer-end model at the tip, measured separately because it is a boolean. Nut bores: lead-in cone on both faces (C8) so the thread start is not at the planar face. Do not rely on the first/last turn being a whole number of pitches: also test lengths with fractional turns (L = 10.25 P succeeded where integers failed in the naive probe, `[M]`, not a fix).

**Warning signs:** the tip chamfer test passes only at chosen lengths; a sliver face with area below 1e-4 mm2; an end finish that is "slow only sometimes".

**Phase to address:** P2 (end finish cost and failure measured), P3.

---

### Pitfall C11: Tests and gate cost: "one test per row" becomes "one thread build per row"

**What goes wrong:** the rule "every table row carries one verification test" is implemented by building each row. At 1 to 15 s per threaded build (`[M]`, loaded host), a few hundred rows turn `make verify` from spur's measured 64 s (L34 `[S]`) into many minutes, and the pre-commit hook then collides with `gsd_run query commit`'s 30 s timeout (three milestones running in spur `[S]`; the hook is already over 30 s at 64 s).

**How to avoid:** row tests are pure data/maths tests (cited cell exists, invariants hold, preset fills the right mm fields); kernel builds in the gate are a small fixed sample chosen once and the full grid lives in `bench/` (spur's composed sweep lived there, `[S]`). Keep the plain `git commit` rule in AGENTS.md and make the 30 s timeout a documented non-use, not a surprise. Parallelise with the xdist setup ported in P1 and measure the gate before and after P3.

**Warning signs:** the hook time after the first kernel test is more than 2x before; commits through the GSD commit tool killed mid-hook.

**Phase to address:** P1 (port with the known timeout rule), P3/P4 (test design).

---

### Pitfall C12: Noise floor, shared hosts and mislabelled readings (spur's most expensive lesson, again)

**What goes wrong:** a bar is set at what the instrument cannot resolve; a reading labelled "at start" was taken at the end. This research itself ran on a host whose 1-min load went 4 to 86 on 12 cores while other agents worked: build times for configurations with the same turns differed by more than 2x, and a longer build finished faster than a shorter one (`[M]`). spur lost about 2 h on a 0.1 ms floor (02-04) and four runs on a mislabelled load reading (12-02/12-03) (`[S]`).

**How to avoid:** measure the harness first (idle repeat of one config, record the spread); port spur's quiet-host gate with a cap (D-05: load under 1.5 for three samples, capped at 900 s) and note that a machine with an active Claude Code session idles near 2.0 (`[S]`); read load at both ends and label by time; record "non-decisive" instead of retrying; set bars from a profile the human has read (15-03 pattern). Every bound cites the run id.

**Phase to address:** P1 (port harness and the gate), P2 and P6 (use it).

---

## Moderate Pitfalls

### Pitfall M1: Self-intersecting profile at small pitch
**What goes wrong:** a profile whose width at some radius approaches the pitch makes adjacent turns touch. Root embedding is the usual cause: with `eps = 0.2 P` the tooth width at the embedded radius reaches 0.98 P (gap about 0.019 P, 0.008 mm at M2) and the fuse returned `isValid() == False`; 0.05 P was valid (`[M]`, single probe). cq_warehouse's embed is 0.001 mm (`[C]`). I did **not** isolate a failure specific to small diameter; the generic fuse failure (C1) dominated. **Prevention:** keep embed to a few micrometres, assert in `calc.py` that every profile width stays below `P - margin`, include M2/M2.5/M3 in the P2 grid. **Phase:** P2.

### Pitfall M2: Left-hand thread
**What goes wrong:** mirroring a right-hand solid can invert orientation or change the seam behaviour; the LH pair needs its own proof. **Prevention:** use the construction's native hand parameter (cq_warehouse has `hand`), include LH in the P2 grid and in C4's mating proof (mixed-hand pair must fail). **Phase:** P2, P3.

### Pitfall M3: A preset that rewrites the user's edits
**What goes wrong:** picking "M6 x 20, ISO 4017" fills mm fields and overwrites a hand-edited `thread_length`; or a later table correction changes what an old preset name means while old links hold mm values. **Prevention:** presets fill only at selection time, warn before overwriting edited fields, and the info panel states whether the current mm values equal the cited row ("matches ISO 4017:2022 M6 x 20: yes/no"), never "this is ISO" by name alone. **Phase:** P4, P6.

### Pitfall M4: 4014 thread length longer than the bolt, or a short bolt
**What goes wrong:** `thread_length >= length` on a 4014 bolt makes the shank zero or negative. **Prevention:** cap and warn (L03) when the cap does not contradict an explicit choice; 422 only for a direct conflict between two explicit fields. **Phase:** P3.

### Pitfall M5: Hex head chamfer model unspecified
**What goes wrong:** head and nut chamfer angle and `dw` bearing circle are not specified by one number in the table; two implementations disagree. **Prevention:** document the chamfer model once (angle in the 15 to 30 degree band from the standard's figure, intersect with cone at `dw`), test `e` against it. **Phase:** P3/P4.

### Pitfall M6: Mixing DIN names with ISO rows
**What goes wrong:** hobbyists search DIN 933/931/934/912; the mapping is "same except M10, M12, M14, M22" for 933/931 vs 4017/4014 (`[W]`, MEDIUM; ISO side `[P]`). **Prevention:** a search alias table that points DIN names to ISO rows and states the exceptions. **Phase:** P4.

### Pitfall M7: Fixture bytes
**What goes wrong:** byte-comparing OCCT output (spur: 8 of 20 byte-identical `[S]`). **Prevention:** content equivalence (triangle count, mesh volume, watertight, bbox) for the fixture; defaults never rescale (L05) proven by a replayed link set. **Phase:** P3.

### Pitfall M8: Reusing spur's gear-specific fixture, bounds or build helpers
**What goes wrong:** copying a number "that already works". **Prevention:** L07 already says no figure carries; enforce in review: no constant without a run id. **Phase:** P1, P6.

### Pitfall M9: Untrusted parameters as a CPU bomb
**What goes wrong:** `pitch` or `thread_length` combinations (for example pitch 0.2, length 200 = 1,000 turns) reach the kernel and tie a worker until timeout. **Prevention:** a turns cap validated once at the `Params` boundary (spur rule), before the pool; admission control stays in the web layer; a killed worker is a 504-class, never cached. **Phase:** P3, P6.

### Pitfall M10: A broken build served or cached under a shareable link
**What goes wrong:** the C1 failure is cached and every future request for that link returns it. **Prevention:** the gate runs before the cache write; failed builds are never cached; a tripwire test builds the known-bad configuration and expects a refusal with a body naming the fields. **Phase:** P3, P6.

### Pitfall M11: `cq_warehouse` as a dependency
**What goes wrong:** licence and packaging. A copy in the shared scratchpad had a zero-byte `LICENSE` file, while `setup.cfg` and the GitHub page say Apache-2.0 (`[W]`/`[C]`; verify at the source before depending). `pip download cq_warehouse` found no matching distribution on the default index from this machine (`[M]`, LOW; environment may differ), which conflicts with the pinned-closure rule (L06). The docs list no minimum sizes or known limits (`[W]`). **Prevention:** treat it as a reference implementation and a baseline to beat; if used, vendor a pinned commit under the licence with the NOTICE and re-run the C1/C2 gates against it; confirm in the STACK research. **Phase:** P2.

## Minor Pitfalls

- **Wording `thread_length` on the panel.** Print "b (reference)" for 4014 rows, not "thread length". P4.
- **ISO 261 preferred set vs sizes users want.** M14 and M18 hobbyists exist; the picker shows only preferred sizes by decision; surface the exclusion in the UI text. P4.
- **ISO 4762 key sizes and `dk` smooth vs knurled** are from memory (UNVERIFIED). P7.
- **Mesh watertightness is checked on one shape** only; extend to the fixture set. P3.
- **`pip` accidentally resolving a newer kernel** if `PIP_CONSTRAINT` is unset (my own `pip download` ran without it): CI installs with it, local scratch venvs do not. P1.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Trust `isValid()` as the build check | Zero code | C1 failures served and cached | Never |
| Print `Volume()` for threaded parts | Free number | Wrong by up to about 20 %, violates L08 | Never |
| Copy ISO values from a secondary table | Fast | DIN/ISO mix, nominal/min confusion, wrong edition (C6, C7) | Never |
| One build per table-row test | Easy to write | `make verify` blows up, hook vs 30 s tool (C11) | Never; sample in gate, full in bench |
| Hard-code an mm length cap | Simple | Wrong per size (turns differ 3x) | Never; cap turns |
| Sweep-and-fuse because it is the CadQuery tutorial | Familiar | 1/15 correct on the pinned pair | Only as the spike's "naive baseline" |
| Round-number spike grid (M6 x 20, M10 x 30) | Fast run | Misses the seam-aligned failures | Never; include L/P integral lengths and fractions |
| Fixed STL tolerance from the gear | Ported | Flank polygons or huge meshes | Never; derive from tooth depth |
| Default clearance from a blog | Ship early | Cannot change later without rescaling every omitted-field link (L05) | Never |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| CadQuery `Shape.Volume()` | Treat as exact | `BRepGProp.VolumeProperties_s(shape, props, eps, False, False)` or mesh volume; cross-check analytically (C2) |
| CadQuery `union/cut/intersect` on helical solids | Check no exception and `isValid()` | Solid count, precise volume vs analytic, positive control (C1, C4) |
| OCCT `BRepMesh_IncrementalMesh` / `exportStl` on a cached shape | Export the cached object at several tolerances | Mesh a copy (spur L24); history leaks otherwise (C9) |
| `cq_warehouse` | Assume it is an installable pinned dependency | Verify licence file and install path; treat as reference (M11) |
| `cq_warehouse` end finishes | Use `chamfer` everywhere | Prefer `fade`; measure `chamfer` separately, it is about 6x slower and broke at 80 turns (C3, C10) |
| ISO standards sites | Read a withdrawn edition | Cite edition year and check status; iteh previews for 2022/2023 editions (C6) |
| `gsd_run query commit` | Use it with a long hook | Plain `git commit` (spur 3 milestones, 30 s timeout `[S]`) |
| OCCT version | Assume bug fixed | #1543 reported on 7.9.3 and 8.0.1; pin and re-check on every pair bump |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Turns-driven boolean cost | Fuse 0.6 s at 10 turns, 5.7 s at 40, 13 s at 80, about 80 s at 160 (loaded host, `[M]`) | Cap by turns from a measured sweep (C3) | 40 to 80 turns, which is every full-thread screw at its greatest standard length (`[D]`) |
| `chamfer`/`square` end finishes | 6x slower than `fade` at 20 turns (`[M]`); 19x on the thread alone (docs) | `fade` at the head; measure the tip chamfer alone | Any length; broken result at 80 turns |
| Mesh size | 410 to 6,700 triangles per turn depending on construction (`[M]`) | Choose the construction on mesh cost too; tolerance from tooth depth | 80+ turns: 34k to 420k triangles, 1.7 to 21 MB STL |
| STEP size | 13 MB at 80 turns, 48 MB at 160 (`[M]`) | Cap turns; warn on export size | 80+ turns |
| Memory of cached meshed solids | Unmeasured here (UNVERIFIED) | Spur L24 mesh-on-copy; re-run the memory sweep with threaded corpus (L17) | Container `mem_limit` from gears does not carry |
| Gate cost | `make verify` minutes | Sample builds in gate (C11) | After the first kernel test of the grid |
| Noisy timing | Equal-turn configs 2x apart | Quiet-host gate (C12) | Always on a developer machine |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Unbounded `thread_length` / tiny `pitch` reaching the kernel | CPU exhaustion, worker pinned until timeout, queue fill | Turns `le` at the `Params` boundary, per-build kill, admission control in the web layer (M9) |
| Serving or caching a failed build | Wrong part under a permalink | Gate before cache write (M10) |
| Info panel claiming ISO conformance | Someone orders or machines to the claim | "Matches cited row: yes/no", edition year, L08 warnings (M3, C7) |
| Reporting 6g limits next to nominal geometry | Out-of-tolerance machined part | Label as bought-part limits or omit (C7) |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Silent preset overwrite | User loses an edited field | Warn before overwriting (M3) |
| Clearance shown only as radial mm | User expects a flank gap equal to it | Show radial, flank-normal and axial values (C5) |
| No printability warning | M2/M3 prints fail with no hint | Warning from the measured floor, never a refusal (C8) |
| Preview mesh that hides the thread | User cannot judge pitch | Tolerance from tooth depth (C9) |
| "Thread length" for a reference value | Wrong expectations of the real part | Label "b (reference)" (Minor) |
| Orientation unmentioned | User prints a bolt horizontal | Export axis along Z and say so (C8) |

## "Looks Done But Isn't" Checklist

- [ ] **Thread build:** often missing the solid-count + analytic-volume + watertight gate. Verify: feed the tool-only (dropped-core) solid and see the gate refuse.
- [ ] **Volume on the panel:** often bare `Volume()`. Verify: compare against the `eps` call and mesh volume on a 20-turn part; the numbers must agree within 1 %.
- [ ] **Mating proof:** often one phase, clearance 0, no positive control. Verify: negative clearance gives non-zero interference matching the analytic estimate.
- [ ] **Table row:** often missing edition year or the grade rule. Verify: the row cites standard + edition + table + column and its test checks an invariant, not a retyped value.
- [ ] **M2 to M4 nuts:** ISO 4032:2023 does not cover them. Verify: the cited source for each such row exists and the owner accepted it.
- [ ] **Build bound:** often a round figure. Verify: the decision cites a run id from the full grid and the host load at both ends.
- [ ] **Sweep grid:** often only convenient lengths. Verify: includes L/P integral lengths, integral millimetres, and fractions; both hands; every end finish used.
- [ ] **Export:** often meshes the cached solid. Verify: two exports at different tolerances give counts that depend only on tolerance.
- [ ] **Printed pair:** often one print. Verify: the matrix in C8 with printer settings recorded.
- [ ] **Default clearance:** often provisional. Verify: set from a recorded print before first release, or kept out of the default.
- [ ] **`make verify`:** often grows silently. Verify: time recorded before and after each kernel-test phase.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| C1 construction fails late | HIGH (re-do geometry module) | Switch construction behind the same `model.py` interface; the gate and oracle are construction-independent, so only the builder changes |
| C2 wrong number already printed | MEDIUM | Remove the number, warn (L08), ship the corrected estimator, note in the decision log |
| C3 bound too loose, a config times out in prod | MEDIUM | Tighten the turns `le` (a 422 for previously accepted links) and log the supersession with the new run; links with the old value now fail loudly, not silently |
| C5 clearance sign wrong | HIGH | Defaults never rescale (L05): add a new field name rather than flip the sign of the old one |
| C6/C7 wrong table row shipped | LOW-MEDIUM | Correct the row, bump the edition note; links hold mm so they still build; add the invariant test that would have caught it |
| C8 default clearance wrong after release | HIGH | New field or a preset; never move the default (L05) |
| C9 mesh leak found late | LOW | Port L24's copy discipline |
| C12 unusable measurement session | LOW | Record non-decisive, rerun later behind the gate |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| C1 silent boolean failure | P2 choose, P3 enforce | Gate refuses tool-only solid; full-grid sweep shows 0 gate failures or documented caps |
| C2 volume estimator | P2 | `eps` volume vs mesh vs analytic within 1 % on grid sample |
| C3 build time | P2 measure, P6 bound | Decision cites run ids, turns `le`, quiet-host readings |
| C4 mating proof | P3 | Positive control, phases, both hands, mixed-hand failure |
| C5 clearance convention | P3 definition, P5 value | Monotone-in-clearance test; doc defines sign and derived gaps |
| C6 editions and scope | P4 | Every row cites standard + edition + table; M2-M4 nut decision logged |
| C7 cell semantics | P4 | Row tests assert invariants; labels carry nom/max/min/ref |
| C8 printed pair | P5 | Recorded matrix; floor constant cites the print |
| C9 mesh/STEP | P2 measure, P6 bound | Mesh-on-copy test; watertight check; payload bound cites run |
| C10 ends and run-out | P2 measure, P3 | End-finish cost table; no sliver faces |
| C11 gate cost | P1 port, P3/P4 design | Hook time recorded each phase |
| C12 noise floor | P1, P2, P6 | Harness spread recorded; load labelled by time |
| M1 small-pitch profile | P2 | `calc.py` width assertion; M2/M3 in grid |
| M2 left-hand | P2, P3 | LH in grid and proof |
| M3 preset overwrite | P4, P6 | UI test; panel "matches row" |
| M9 CPU bomb | P3, P6 | Turns `le` + 422; timeout kill test |
| M10 cached failure | P3, P6 | Tripwire config refused |
| M11 cq_warehouse licence | P2 | Licence and install path confirmed in STACK |

---

## spur retrospective lessons mapped to this project

Source: `/Users/halfb00t/git/halfb00t/spur/.planning/RETROSPECTIVE.md` (v0.1, v0.2, v0.3). "Recurs" is my judgement from the evidence above.

| spur lesson | Recurs here? | Where it bites | Phase to address |
|-------------|--------------|----------------|------------------|
| Measurement floor: "a bar at the instrument's noise floor is not a bar" (02-04, 0.1 ms) | **Yes, already observed**: the research host ran at load 4 to 86; equal-turn builds differed by more than 2x | Thread build-time bounds, latency, gate time | P1 (port quiet-host gate), P2, P6 |
| Label a reading by when it was taken (WR-07: load read at the end labelled "at start") | Yes: sweeps are minutes long | `bench/build_time.py` port | P1 (fix in the port, do not copy the bug), P2 |
| Pre-registered measurement (method, predictions, escape clause before the first run) | Yes: the spike is the place | Thread spike, clearance print matrix | P2, P5 |
| Spike before field (HEX_CELL_CAP, ROOT_CONTACT) | Yes: PROJECT.md already says so | `thread_length` cap, turns `le`, printability floor | P2 then P3/P6 |
| Verify a phase's premise with a live read (Phase 5 "CI never ran" was false) | **Yes, several brief premises are shaky now**: M2 to M20 for every table vs ISO 4032:2023 scope M5 to M39; "4759" for 6g/6H; "`b` from the table" ignores the length band; "clearance grows inward"; "kernel check proves the pair"; "cq_warehouse unverified" (now: exists, 0.8.0, Apache-2.0 per `setup.cfg`/GitHub; licence file and install path to confirm) | Roadmap phase premises | Before roadmap approval; P4 re-reads standards |
| Hook timeouts vs commit tools (30 s `gsd_run query commit` vs 3.5 min then 64 s hook) | Yes: gate already above 30 s once spur's runtime is ported, and kernel tests make it longer | Every close-out commit | P1 (AGENTS rule: plain `git commit`), P3 (test cost) |
| Metric wording: write the success metric about the state at kickoff (v0.3 metric 1 failed on a row the milestone wrote) | Yes: "every allowed configuration builds inside the timeout" and "a pair threads together when printed" are ill-posed until the allowed set and the proof are defined | Roadmap success criteria | Roadmap: list the allowed set at kickoff; split SC-kernel and SC-printed (C4) |
| A regression test must be able to fail (WR-06) | **Yes, strongest instance**: a gate that only sees passing builds cannot detect C1; the interference check is a zero-returning check (C4) | Build gate, mating proof | P3 |
| Content equivalence not byte equality for OCCT outputs | Yes, more so (large meshes, history-dependent counts) | STL/STEP fixtures | P3, P6 |
| L24 mesh-free cached solid | **Yes, reproduced** (C9c) | Export path | P1 (port) and P3 |
| Spur oracles beside the kernel (`_filleted_spoke_volume`, abs 1e-9) | Yes: needed for thread volume, mating interference and C2 | `calc.py` | P2/P3 |
| Pure-math core behind a thin shell; `calc.py` never imports `cadquery` | Yes: the thread oracle lives in `calc.py` and shares no code with `model.py` | Architecture | P2 |
| Cap-and-warn or 422, never guess; defaults never rescale (L03, L05) | Yes: turns cap, `thread_length` vs `length`, clearance default | Schema | P3, P5 |
| Triage review findings before close (17 open in v0.3) | Process | Every phase close | Every phase |
| Verifier digests stale by construction (3 closes, 3 overrides) | Process | GSD verifier fingerprint | P1: record cause once, do not re-stamp |
| Land-then-verify needs one owner | Process | PR landing | P1 |

---

## Open questions and UNVERIFIED register

1. ISO 4014:2022 tables and the exact `b` rule in the 2022 edition (2011 read; 2022 not read).
2. ISO 4032:2023 Annex A (M2 to M4 nuts): contents, and whether an informative annex satisfies "cited source".
3. ISO 4762 current edition and its table (P7).
4. Mapping of `cadquery-ocp 7.9.3.1.1` to OCCT 7.9.3 (relevant to #1543).
5. Cost of the mating check (`common` of two threaded solids) and the nut-thread (internal) build failure rate; not measured.
6. Whether turns, not diameter, dominate (two single runs).
7. Cause of superlinear STEP growth; downstream CAD import cost and behaviour.
8. Any controlled FDM study of ISO metric thread clearance, orientation, layer height; none found.
9. Printer-side effects of the lead-in chamfer dimensions (0.8 to 1.5 mm is blog-level).
10. Licence status of `cq_warehouse` as shipped and of embedding ISO table values.
11. 6g fundamental deviation formula and M6 6g `d,max` 5.974 mm (from memory).
12. DIN 934 nut thickness values (from memory).

## Probe record (method, versions, caveats)

All probes: `cadquery 2.8.0`, `cadquery-ocp 7.9.3.1.1` (the pinned pair; `/Users/halfb00t/git/halfb00t/screw/.venv`) and a sibling scratch venv with `cq_warehouse 0.8.0` on the same pair. Python 3.12, macOS arm64, Apple M2 Max. Scripts lived in the session scratchpad and are not kept; the method is reproduced here so the P2 spike can supersede it.

- **Naive sweep + fuse:** ISO basic-profile trapezoid tooth (3P/4 at the minor radius, P/8 at the major radius, height 5H/8, root embedded 0.05 P), `Workplane("XZ").polyline(...).sweep(helix, isFrenet=True)`, tool length L + 2P translated -P, `core.union(tool)`. Success = valid, exactly 1 solid, `core + 0.3 tool < union < core + tool` with the precise volume estimator.
- **cq_warehouse thread:** `IsoThread(d, P, L, external=True, end_finishes=(a, b))` fused to `circle(r_minor).extrude(L)`; reference volume = core + tooth area x 2 pi r_centroid x L/P (Pappus).
- **Precise volume:** `from OCP.BRepGProp import BRepGProp; from OCP.GProp import GProp_GProps; p = GProp_GProps(); BRepGProp.VolumeProperties_s(shape.wrapped, p, 1e-6, False, False); p.Mass()`.
- **Mesh check:** binary STL parsed with stdlib, vertices welded by rounding to 1e-5 mm, every directed edge must have exactly one reverse partner, volume by signed tetrahedra.
- **Load at the time:** `uptime` showed 4.1 (15:53), 32 to 86 (15:57 to 16:03), 28 to 46 (16:03 to 16:04). The shared scratchpad shows other agents benchmarking concurrently. All wall times are therefore upper-bound-ish and noisy, and are not usable as bounds.
- **What the probes do not show:** that sweeps cannot work (only this construction failed), that cq_warehouse is correct in general (its chamfer end broke at 80 turns; its fade/raw ends matched the reference in 7 of 7 precise-volume checks; one raw/raw case returned 2 solids and was not resolved), anything about internal (nut) threads, or anything about a different kernel pair.

## Sources

- ISO 4017:2022 official preview (iTeh): `https://cdn.standards.iteh.ai/samples/72585/1179998ddd594550a909d6e13c416f3e/ISO-4017-2022.pdf` (`[P]`, HIGH): foreword changes, scope, Tables 1 and 2, figure notes (u <= 2P, ISO 4753 chamfered end, greatest/shortest standard length).
- ISO 4032:2023 official preview (iTeh): `https://cdn.standards.iteh.ai/samples/75016/5b1f83bd2dc44fc199973e9957a75086/ISO-4032-2023.pdf` (`[P]`, HIGH): scope M5 to M39, Annex A, Tables 1 and 2.
- ISO 4014:2011 full-text copy: `https://pppars.com/wp-content/uploads/2021/07/ISO-4014-2011.pdf` (`[P]`, MEDIUM: third-party copy of a withdrawn edition): scope and grade rule, Table 1/2, `b` bands, notes on `lg`.
- ISO 4014 status and 2022 editions (search snippets, LOW-MEDIUM): `https://www.iso.org/standard/56447.html`, `https://standards.globalspec.com/std/1307397/iso-4014`
- ISO 4032 edition: `https://www.iso.org/standard/75016.html` (search snippet).
- ISO 965-2 editions: `https://www.fasteners.eu/tech-info/ISO/965-2/`, `https://indfast.org/product/iso-965-21998-iso-general-purpose-metric-screw-threads-tolerances-part-2-limits-of-sizes-for-general-purpose-external-and-internal-screw-threads-medium-quality/` (LOW-MEDIUM).
- ISO 4759-1 scope: `https://standards.iteh.ai/catalog/standards/iso/d631c3ca-3424-488a-b176-b07244c96bae/iso-4759-1-2000`, `https://standards.globalspec.com/std/798389/iso-4759-1` (MEDIUM).
- ISO 261/262: `https://www.iso.org/standard/4167.html`, `https://www.boutique.afnor.org/en-gb/standard/iso-2622023/iso-general-purpose-metric-screw-threads-selected-sizes-for-bolts-screws-st/xs142125/344836` (LOW-MEDIUM).
- ISO 68-1 profile: `https://en.wikipedia.org/wiki/ISO_metric_screw_thread`, `https://cdn.standards.iteh.ai/samples/85107/2562fb7b223244f5a95c287e78f257a6/ISO-68-1-2023.pdf` (LOW-MEDIUM).
- ISO 4762 editions: `https://www.iso.org/obp/ui#!iso:std:iso:4762:ed-4:v1:en` (search snippet; LOW).
- DIN vs ISO across flats: `https://www.wermac.org/bolts/metricBDC.html`, `https://www.wermac.org/bolts/dimensions_hex-nuts_across-flats-and-heights_din-iso.html`, `https://eurolinkfss.com/comparing-din-934-to-iso-4032-iso-8673/`, `https://fullerfasteners.com/2024/07/comparing-iso-4014-4017-to-din-931-933/` (MEDIUM when two agree and the ISO side matches `[P]`; the wermac table anomalies are LOW).
- OCCT issue #1543, helical boolean cut silently removes nothing: `https://github.com/Open-Cascade-SAS/OCCT/issues/1543` (HIGH for its own claims; fetched via summariser).
- CadQuery list, non-manifold threads: `https://groups.google.com/g/cadquery/c/5kVRpECcxAU/m/7no7_ja6AAAJ` (LOW, old).
- cq_warehouse thread docs (end finish timings): `https://cq-warehouse.readthedocs.io/en/latest/thread.html`; code read: `thread.py`, `fastener.py` in a 0.8.0 copy (`[C]`, HIGH). Repository: `https://github.com/gumyr/cq_warehouse` (Apache-2.0 per GitHub page; licence file in the inspected copy empty).
- bd_warehouse / build123d IsoThread end finishes: `https://github.com/gumyr/bd_warehouse` (LOW-MEDIUM).
- BOSL2 threading (`blunt_start`, `lead_in`, `$slop` on internal threads): `https://github.com/revarbat/BOSL2/wiki/threading.scad` (MEDIUM-LOW, via search summary).
- 123DScrew (build123d printable screws, insert-side clearance, vertical printing): `https://github.com/kevmasajedi/123DScrew` (LOW, one project).
- FDM thread guidance (blog/vendor level, all LOW): `https://www.selfcad.com/blog/3d-printing-threads-and-screws-key-settings-and-tips`, `https://www.sovol3d.com/blogs/news/3d-printing-threads-and-screws-how-to-design-reliable-fdm-fasteners`, `https://kingroon.com/blogs/3d-printing-guides/how-to-3d-printing-threads-perfectly`, `https://forum.prusa3d.com/forum/original-prusa-i3-mk3s-mk3-how-do-i-print-this-printing-help/thread-tolerances-on-prusa-mk3s/`
- SLS PA12 M8 thread load study (MEDIUM, wrong process for FDM): `https://pmc.ncbi.nlm.nih.gov/articles/PMC12787388/`
- spur: `/Users/halfb00t/git/halfb00t/spur/.planning/RETROSPECTIVE.md`, `/Users/halfb00t/git/halfb00t/spur/docs/architecture/decision_log.md` (L03, L05, L08, L17, L19, L24, L26, L34 by title), `/Users/halfb00t/git/halfb00t/spur/bench/README.md`.
- screw: `/Users/halfb00t/git/halfb00t/screw/.planning/PROJECT.md`, `/Users/halfb00t/git/halfb00t/screw/docs/architecture/decision_log.md` (L01 to L07).
- Own probes `[M]`: see Probe record.

---
*Pitfalls research for: parametric ISO metric threaded fasteners (CadQuery/OCCT)*
*Researched: 2026-10-05*
