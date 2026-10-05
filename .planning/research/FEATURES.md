# Feature Research

**Domain:** Parametric ISO metric threaded fastener generator (hex bolts/screws, hex nuts, later socket head cap screws) with real helical threads, FDM-printable mating pairs, STL/STEP export, web UI + HTTP API + CLI on one parameter model
**Researched:** 2026-10-05
**Overall confidence:** MEDIUM. Standards metadata and the 4014/4032/262 numbers quoted here were read in the standards' own text (public iTeh previews) or on national-standards-body pages. The FDM numbers are forum, vendor and library-default practice only: no thread-specific measured test was found.

## Confidence legend (used on every claim below)

| Tag | Meaning |
|-----|---------|
| HIGH | Read in the standard's own text (publicly hosted preview/copy) or on a national standards body page (SIS, AFNOR, DIN Media) |
| MEDIUM | Two or more independent web sources agree, or one reputable source plus a cross-check against standard text (this is the `classify-confidence --verified` tier for web results) |
| LOW | A single web source, or a search-engine summary I could not open (the seam's default tier for unverified web results) |
| UNVERIFIED | From the owner's/my memory, or not found. Must not be cited by any table row until confirmed against a purchased copy of the standard |

**Read this first: three findings that touch the owner's brief**

1. **ISO 4032:2023 normatively covers M5 to M39 only.** M1.6 to M4 nuts moved to *informative* Annex A ("historical nuts ... not conforming to ISO 898-2"). The brief's "M2-M20 for every table" therefore cannot cite a *normative* clause for M2, M2.5, M3, M3.5, M4 nuts. Needs an owner decision (see Open Questions, Q1). HIGH.
2. **"Bolt at nominal so it mates a bought nut" conflicts with common FDM practice.** The most common advice is that printed external threads come out oversize and need a negative offset; nut-only clearance (the brief's choice) is what BOSL2 and one online generator do, but it is mainly valid for a printed bolt into a printed nut. A printed bolt at exact nominal into a metal nut is likely to bind. This is the core-value risk and is unmeasured (see Q2). MEDIUM.
3. **4759 is the wrong standard for 6g/6H.** ISO 4759-1 is *product-grade tolerances* (head, shank, hex dimensions, form, position). Thread tolerance classes 6g/6H live in ISO 965 (system in 965-1, numeric limits of size in 965-2). Resolved in Section "Standards confirmed" below. HIGH.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Missing any of these and the tool does not read as a fastener generator.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Pick standard + size + length from a valid-combination list | Every competitor (FreeCAD Fasteners WB, cq_warehouse/bd_warehouse, BOSL2 spec strings, 3dprintgenerator dropdown, McMaster filters) starts from "M6 x 20" | LOW | Length must be a standard nominal length for the chosen row. ISO 4014:2022 only defines a (size, length) pair between "stepped bold lines"; shorter lengths belong to ISO 4017 (fully threaded). HIGH (ISO 4014:2022 Tables 1-4 read). |
| Coarse-pitch metric thread, right-hand, real helix | The product itself; the others default to cosmetic/simple threads for speed (bd_warehouse `simple=True` default, FreeCAD thread property off by default) | HIGH | Cost is the unmeasured risk (spike first, per PROJECT.md). FreeCAD docs: "Generating threads is costly"; bd_warehouse: threaded parts "significantly increase storage requirements". MEDIUM. |
| Hex head with correct across-flats `s`, head height `k`, bearing face `dw`, top chamfer, under-head fillet, chamfered point | Visible geometry of any hex bolt; ISO 4014/4017 Figure 1 shows chamfer beta 15-30 deg point, fillet, incomplete thread `u <= 2P` | MEDIUM | HIGH (ISO 4014:2022 / 4017:2014 text). |
| Hex nut with chamfers on both faces and correct `s`, `m` | Same | MEDIUM | ISO 4032:2023 delivers nuts without washer face unless ordered. HIGH. |
| Lead-in chamfer on nut thread and bolt tip | Without it a printed pair will not start; every printed-thread guide stresses a lead-in/clean thread start | MEDIUM | ISO 4753 governs thread ends on the bolt (referenced by 4014/4017). The nut-side countersink angle is not in the text I read. UNVERIFIED which clause. |
| One clearance field for the printed pair | Every printable-thread generator exposes one (BOSL2 `$slop`, threads-scad `tolerance`, 3dprintgenerator "Nut Clearance" = 0.1 mm, Fusion FDM threads 0.###i/e) | LOW | Units must be explicit (radial vs diametral): see FDM section; sources mix both. |
| STL and STEP download | Stated product promise; McMaster/TraceParts users expect STEP | MEDIUM | STL tessellation fineness changes whether a pair fits (see FDM section, Prusa forum case). Needs an explicit, recorded chord-deviation setting. |
| Live 3D preview | Stated product promise | MEDIUM | Fidelity vs latency decided by the thread-cost spike; the "no number is better than a wrong number" rule means the preview may be simplified but numbers may not. |
| Info panel of derived dimensions | The brief's stated differentiator, but expected in any serious fastener tool (McMaster/fasteners.eu list s, e, k, dw, b) | MEDIUM | Detailed in "Info panel" section. |
| Left-hand thread toggle | Owner decided in v1; every generator that supports threads has `hand` (bd_warehouse `hand`, Kirshner/rcolyer `left_handed`) | LOW | Cheap in kernel; the mating proof must run on LH pairs too. |
| Matching nut for any generated bolt (and vice versa) | Printers print pairs; online generators build "matched nut-and-bolt pairs" (starthere00) | LOW | Pair derived from the same d, P, hand, clearance. |
| API and CLI that take the same fields as the form | The brief's three front ends | MEDIUM | Parity proven model-driven (PROJECT.md). Not offered by any surveyed competitor as an HTTP API. |

### Differentiators (Competitive Advantage)

These align with the Core Value: a pair that actually threads together plus numbers someone can cut metal to.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Kernel-level interference check of the bolt/nut pair at the chosen clearance | No surveyed tool proves a pair mates before printing; BOSL2 and bd_warehouse only state that dimensions are standard-consistent | HIGH | Cost unmeasured; must run inside the per-build timeout. A pass is necessary, not sufficient: a pair passing the kernel and failing on a printer is the named failure mode. |
| ISO tables as presets with clause + edition cited per row and one test per row | bd_warehouse's CSVs carry no clause citations and mix values: its `iso4017:k` for M5 is 3.74 (the ISO 4017 grade B maximum) while `iso4014:k` is 3.5 (nominal), and its `iso4017` M3 `k` is 2.2 vs nominal 2.0 (cross-read against ISO 4014:2022 / 4017:2014 text). Web aggregator tables are worse (see Pitfall note) | MEDIUM (data entry) / HIGH (liability) | Pin the *edition*: ISO 4014:2022 changed `dw,min` for d <= M5 (e.g. M5 6.88 in the 2011 text, 7.20 in the 2022 text) so a table silently carrying pre-2022 values is wrong. HIGH. |
| Honest 6g/6H min/max on the info panel, with an explicit "model is nominal, not toleranced" label | Competitors either ignore tolerance classes (OpenSCAD libs) or bake them into geometry (BOSL2 applies 6g by default). Showing the numbers without implying the model sits inside them is the honest middle | MEDIUM | M10x1.5 6g limits are major dia 9.732-9.968 (distributor catalogue "according to ISO 965", MEDIUM); the model's nominal major of 10.000 is *outside* that band by 0.032. The panel must say so. |
| Round-trippable link: full parameter set in the URL; preset id is metadata only | None of the surveyed web generators (3dprintgenerator, starthere00) documented shareable links (absence, UNVERIFIED) | LOW | Already a house rule (L05 defaults frozen). |
| Preset-match indicator ("matches ISO 4017 M6 x 20" / "custom, based on ...") | Keeps "explicit mm is truth" visible: editing any mm field detaches the badge | LOW | New idea from this research. No competitor found doing it. |
| Printability warnings (cap-and-warn, never guess) for small sizes / pitches | Protolabs Network: avoid threads below M5; Sovol: M6 / pitch >= 1.0 mm conservative. A warning with the source beats a silent bad print | LOW | Threshold must be a constant set by the owner's printed test, not these sources (see FDM section). |
| Scriptable: HTTP API + CLI returning STL/STEP + the same info-panel numbers | cq_warehouse/bd_warehouse are Python libraries; OpenSCAD is CLI-capable but has no panel of derived numbers; web generators are UI-only | MEDIUM | Inherited from spur's shape. |
| Real modelled thread in STEP for CAD users | McMaster's STEP carries modelled threads on some parts but CAD guidance is to avoid putting them in assemblies (CATI blog, LOW); TraceParts not verified. A clean ISO-tabulated modelled thread + nut is the niche | HIGH | Downstream CAD behaviour is another researcher's question. |
| Legacy-name search ("DIN 933 M10") resolving to the ISO preset with a notice about the changed wrench size | Hobbyists search DIN numbers; DIN 933/931/934/912 are withdrawn but still the common names (MEDIUM) | LOW | Alias + notice only; no DIN tables (see Anti-Features). |

### Anti-Features (Commonly Requested, Often Problematic)

Owner-decided OUT of v1 are listed first with the owner's reasoning, not re-argued. Additions from this research follow.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Self-tapping, wood, sheet-metal screws (owner: out) | Common print/hardware need | Owner: different thread form (sharp, tapered, no mating nut), nothing to prove a pair against; not a deferred requirement | None in this product |
| Head markings: strength grade, manufacturer (owner: out) | Looks like a real bolt | Owner: printed plastic has no strength grade; text in the kernel means fonts | None |
| UNC/UNF and any non-ISO thread form (owner: out) | US users; 3dprintgenerator and starthere00 offer them | Owner: one thread form to prove; imperial adds tables without adding proof | ISO metric only (68-1 profile, 261/262 sizes) |
| Countersunk, set screws, washers (owner: out of first two releases) | Part of every "fastener library" (bd_warehouse, FreeCAD, 3dprintgenerator all have them) | Owner: revisit once socket cap has shipped on the proven path | Deferred, not argued |
| Modelling tolerance classes as geometry (owner: out) | BOSL2 does it (6g default) | Owner: conflicts with "explicit mm is truth" and the clearance field | Report 6g/6H numbers only |
| Sizes below M2 or above M20 (owner: out) | Completeness | Owner: M1.6 does not print; M24+ is long thread builds against the timeout; every row is a test | Range grows when someone needs it |
| Shared-infra package extraction (owner: deferred) | Duplication with spur | Owner: third repo to keep green until a fix must land in both | `docs/tech_debt/active/2026-10-05-shared-infra-extraction.md` |
| Property class / strength-grade selector, torque and preload charts | starthere00 sells "seating torque" and torque charts; ISO designations carry "8.8" | A printed part has no property class (owner's marking reasoning applies); any torque number would be a plausible-looking number nobody can stand behind (violates L02/L08) | Omit property class from the designation line; print nothing about strength |
| Separate DIN 933/931/934/912 tables | Hobbyists search these names | DIN 933/931/934/912 are withdrawn; doubling every table doubles row liability. They differ from ISO at M10/M12/M14/M22 across-flats | Alias to the ISO preset with a notice |
| "Loose / standard / tight" fit presets that hide the millimetres | Easier than a number | Contradicts "explicit mm is truth"; presets would be guesses until printed-tested | If ever added, a preset that *fills* the mm field, like the size picker; defer until printed data exists |
| Server-side accounts / saved designs | "Save my bolt" | The URL is the store (architecture overview: nothing is stored) | Shareable link |
| Tap-drill / clearance-hole calculators and hole-pattern generation | bd_warehouse has `clearanceHole`/`tapHole`; starthere00 prints tap drill and clearance hole | Different standards (ISO 273 etc., not researched) and a second table family to cite and test; not needed to prove a bolt/nut pair | Idea file in `docs/ideas/` if wanted |
| Print-in-place / split-print / captive-nut variants | 3dprintgenerator has "split print" | Orthogonal to proving the standard pair; adds geometry modes | `docs/ideas/` |

---

## Standards confirmed (answer to brief item 2)

The brief's numbers were from memory. Status of each after checking:

| Standard | Brief's claim | Verdict | Current edition found | Evidence | Conf. |
|----------|---------------|---------|-----------------------|----------|-------|
| ISO 68-1 | metric thread profile | CORRECT number; **title changed**: "ISO general purpose screw threads - Basic and design profiles - Part 1: Metric screw threads". 2023 edition replaced 68-1:1998 and Amd 1:2020. "Basic and design profile" matters: the design profile is what a real thread (rounded root) looks like | ISO 68-1:2023 (Oct 2023) | AFNOR store page. A search summary says the 2023 edition sets a minimum root radius of 0.125 P: LOW, **UNVERIFIED**, check before the thread profile is specified | HIGH (metadata) |
| ISO 261 | preferred sizes | CORRECT number; it is the **general plan** (the full list of diameter/pitch combinations) | Ed. 2, 1998, listed valid by SIS; a newer edition may exist: UNVERIFIED | SIS page | HIGH / UNVERIFIED (newer ed.) |
| ISO 262 | preferred sizes | CORRECT number; **this is the one that gives 1st/2nd choice sizes** for bolts, screws, studs, nuts, a selection from 261. Range now 1-100 mm | ISO 262:2023, 3rd ed. (Apr 2023), replaces 1998 | Read the 2023 text: M2, M2.5, M3, M4, M5, M6, M8, M10, M12, M16, M20 are 1st choice; M3.5, M7, M14, M18 are 2nd choice (non-preferred, shown in brackets in 4014/4032). Coarse pitches: M2 0.4, M2.5 0.45, M3 0.5, M3.5 0.6, M4 0.7, M5 0.8, M6 1, M7 1, M8 1.25, M10 1.5, M12 1.75, M14 2, M16 2, M18 2.5, M20 2.5 | HIGH |
| ISO 724 | (not in brief) | **Needed**: basic dimensions (pitch dia d2, minor diameters) for the info panel. Aligned with 68-1 design profiles | ISO 724:2023, 3rd ed. (Apr 2023), replaces 724:1993 | SIS page. The formulas d2 = d - 0.6495 P, D1 = d - 1.0825 P are from memory: **UNVERIFIED** against 724:2023 | HIGH (metadata) / UNVERIFIED (formulas) |
| ISO 4014 | hex bolts, partial thread | CORRECT. "Hexagon head bolts - Product grades A and B", M1.6-M64 | ISO 4014:2022, 5th ed. (cancels 4014:2011) | SIS scope text; 2022 sample text read (Tables 1-4). 2022 changes: tables restructured, **M7 added**, `dw,min` raised for d <= M5, lengths rules amended | HIGH |
| ISO 4017 | hex screws, full thread | CORRECT. "Hexagon head screws - Product grades A and B", M1.6-M64. Same product as 4014 except threaded up to the head and lengths up to 200 mm preferred | ISO 4017:2022, 6th ed. (cancels 4017:2014) | SIS scope text; 2014 text read for the "same as 4014" note. **2022 table values not read: UNVERIFIED** | HIGH (scope) / UNVERIFIED (2022 values) |
| ISO 4032 | hex nuts | CORRECT. "Hexagon regular nuts (style 1)", product grades A and B. **Normative range M5-M39**; D < M5 moved to informative Annex A; M7 added | ISO 4032:2023, 5th ed. (Aug 2023), cancels 4032:2012 | Read Foreword, Scope, Tables 1-2, Table 3, plus SIS scope text | HIGH |
| ISO 4762 | socket head cap screws | CORRECT. "Hexagon socket head cap screws", coarse thread M1.6-M64, **product grade A only** | ISO 4762:2004, 4th ed.; no newer edition found (a search summary says confirmed 2023: LOW) | Read scope, normative refs, and Table 1 for M1.6-M12 | HIGH (2004 text) |
| ISO 965 | tolerance classes 6g/6H | CORRECT family. **Parts**: 965-1 = tolerance *system* (positions, grades, designation); **965-2 = numeric limits of size, tolerance classes 6H and 6g for M1.6-M100 (5H/6h for M1-M1.4)**; 965-3 constructional threads; 965-4/-5 hot-dip galvanized; 965-6 fine/medium qualities (2025) | ISO 965-1:2026 (Apr 2026, 5th ed., replaces 2013); ISO 965-2:2024 | iso.org listing titles (via search), DIN Media / en-standard listings. 965-1:2026 content changes (special tolerances, new annex) from a search summary: LOW | MEDIUM |
| ISO 4759-1 | brief also wrote "4759" | **NOT thread tolerance.** ISO 4759-1 = tolerances for bolts, screws, studs and nuts, product grades A, B, C: the size/form/position tolerances behind the min/max columns of 4014/4017/4032/4762 (head, shank, hex). Thread tolerance class comes from ISO 965 | ISO 4759-1:2000 (an older 1978 edition also listed); newer edition: UNVERIFIED | 4014:2011 Table 3 ("Tolerance - product grade - ISO 4759-1" vs "Thread - tolerance class 6g - ISO 724, ISO 965-1"), 4032:2023 Table 3 ("Thread - tolerance class 6H - ISO 965-1"; "Tolerances - product grade D <= M16: A, D > M16: B - ISO 4759-1"), ISO 4762:2004 refs | HIGH |

**Which standard supplies which table row** (so every row can cite "standard + clause"):

| Table | Source standard + clause | Notes |
|-------|--------------------------|-------|
| Size list, pitch | ISO 262:2023 Table 1 (sizes), ISO 261 (pairs) | HIGH |
| d2, D1, d3, thread depth | ISO 724:2023 | UNVERIFIED formulas until read |
| Head/nut dimensions s, e, k, dw, m, c, r, da, ds | ISO 4014:2022 Tables 1-4 + Annex A; ISO 4017:2022; ISO 4032:2023 Tables 1-2; ISO 4762:2004 Table 1 | Pin edition per row |
| Thread length `b`, shank `ls`, grip `lg` | ISO 4014:2022 (b ref. + ls/lg columns); ISO 4017 = full length; ISO 888 (nominal lengths and thread lengths; referenced, not read) | See "b" note below |
| 6g / 6H min and max | ISO 965-2:2024 (numbers); 965-1 (positions, designation) | The standards 4014/4032 cite 965-1 for the class, not 965-2. A row cites the *numeric* source |
| Product grade A vs B boundary | ISO 4014 Table 3 / 4017: A for d <= M24 and l <= 10d or 150 mm (whichever is shorter), else B | HIGH. Affects which min/max values apply |

**Thread length `b` is not one formula across standards.**
- ISO 4014 (2011 and 2022 text): `b ref.` = 2d + 6 for l <= 125 mm, 2d + 12 for 125 < l <= 200, 2d + 25 for l > 200 (checked against the M5-M12, M14-M24 and M22 columns). HIGH.
- ISO 4762:2004: `b ref.` for M3 18, M4 20, M5 22, M6 24, M8 28, M10 32, M12 36 = 2d + 12. HIGH for M1.6-M12 as read; other sizes UNVERIFIED. A single `thread_length` field fed by per-standard presets is right; do not share one formula.
- It is a *reference* dimension, not a toleranced one. Do not print it as a measured min/max.

**Across-corners `e` is two different numbers.** The standard's `e,min` (ISO 4014:2022 M10: 17.77) is a manufacturing minimum; the geometric corner distance of a nominal hexagon is s / cos(30 deg) = 18.475 for s = 16. Web tables mix them (jadealloys lists 18.48). The panel must label which it shows. HIGH.

**DIN to ISO map (names hobbyists search)**

| DIN | Status | ISO successor | Wrench-size differences | Conf. |
|-----|--------|---------------|-------------------------|-------|
| DIN 933 (full-thread hex screw) | withdrawn; DIN ISO 4017:1987 replaced DIN 933:1983-12 | **ISO 4017** | M10 17 vs 16, M12 19 vs 18, M14 22 vs 21, M22 32 vs 34 | MEDIUM (DIN Media listing + trade pages; ISO side HIGH from 4014:2022/4032:2023 text; DIN side from bd_warehouse `din931` CSV column + trade pages) |
| DIN 931 (partial-thread hex bolt) | withdrawn | **ISO 4014** | same four sizes | MEDIUM |
| DIN 934 (hex nut) | withdrawn | **ISO 4032** (coarse), ISO 8673 (fine) | M10 17 vs 16, M12 19 vs 18, M14 22 vs 21 (vendor pages); ISO 4032:2023 M22 s = 34 is HIGH; DIN 934 M22 = 32 is **UNVERIFIED** | MEDIUM |
| DIN 912 (socket head cap) | withdrawn; DIN 912:1983-12 replaced by DIN EN ISO 4762 | **ISO 4762** | Dimensions the same per trade sources. ISO 4762 omits M1.4, M18, M22, M27, M33 that DIN 912 had (vendor source; M18 absence matches bd_warehouse's 4762 table) | MEDIUM |

Consequence for the size list: ISO 4762 has **no M18**, so "M2-M20" for 4762 is M2, M2.5, M3, M4, M5, M6, M8, M10, M12, M14, M16, M20 = 12 rows (UNVERIFIED against the 4762 table; PROJECT.md says "~13"). M3.5 and M7 are not in the 4762 table I can see.

**Rows in the v1 size range, by standard (preferred / non-preferred)**

| Standard | Sizes in M2-M20 | Count | Source |
|----------|-----------------|-------|--------|
| ISO 4014:2022 | M2, M2.5, M3, (M3.5), M4, M5, M6, (M7), M8, M10, M12, (M14), M16, (M18), M20 | 11 preferred + 4 bracketed | HIGH (Tables 1-4) |
| ISO 4017:2022 | presumed same as 4014 | UNVERIFIED | scope text only |
| ISO 4032:2023 normative | M5, M6, (M7), M8, M10, M12, (M14), M16, (M18), M20 | 6 preferred + 4 bracketed | HIGH |
| ISO 4032 M2, M2.5, M3, M3.5, M4 | informative Annex A only | 5 | HIGH that it is Annex A; values UNVERIFIED (2012 edition's M2-M4 values exist, not re-read) |

---

## FDM practice for printed mating threads (answer to brief item 1)

**There is no published, thread-specific measured test in what I found.** Everything below is forum consensus, vendor guides and library defaults. The owner's plan (default from a spike plus a printed test) is the right response; this section only sets the starting range and shows where practice disagrees.

### Typical clearance

| Source | Value | Part | Radial or diametral | Type | Conf. |
|--------|-------|------|---------------------|------|-------|
| Sovol guide (also echoed verbatim by several blogs) | 0.10-0.20 mm per side (0.20-0.40 mm diameter) as a *starting point for testing*; depends on nozzle, line width, layer height, flow, kinematics, shrinkage | external negative, internal positive | radial stated | vendor blog | MEDIUM (many copies agree, none measured) |
| Bambu Lab forum thread "Printing nuts and threaded holes" | 0.1-0.2 mm general; 0.15 (one user); 0.20 (one user); 0.2 both parts with an FDM-specific Fusion thread (one user) | mixed | unclear | forum | MEDIUM |
| Prusa forum "Nut and bolt threads don't fit" (Apr 2021) | 0.2 mm total reduction on a Fusion thread was "too tight" i.e. about 0.1 mm per side insufficient; extrusion multiplier calibration called the most important factor | bolt reduced | total | forum | LOW |
| Prusa forum "Thread tolerances on Prusa mk3s+?" | 0.1-0.125 mm achievable on 0.4 mm nozzle; one user needed 1.3 mm on a 7 mm x 1.1 thread built with only 36 segments per circle ("you want at least 90, preferably 120") | not stated | not stated | forum | LOW |
| Prusa forum "Guide to Printing Threads" (June 2017) | no number: bolt at the *minimum* major diameter, nut at the *maximum* major diameter from the tolerance chart (6g/6H-style), 0.4 mm nozzle, PLA | both | n/a | forum guide | LOW |
| Protolabs Network (Hubs) | holes print small: add 0.1-0.2 mm to the radius for FDM holes | hole | radial | design guide (search-level; not re-opened for this line) | LOW |
| BOSL2 `$slop` (library) | default 0; widens *holes/nuts only* by 4 x `$slop` on the diameter (so radial 2 x `$slop`); "does not affect the size of screws" | nut only | diametral = 4 x slop | library docs | HIGH (docs fetched) |
| threads-scad (rcolyer, CC0) | `tolerance=0.4` default on ScrewThread/ScrewHole/MetricBolt/MetricNut | unspecified | **UNVERIFIED** whether radial or diametral | library README | HIGH (default), UNVERIFIED (semantics) |
| 3dprintgenerator parametric screw generator | "Nut Clearance" default **0.1 mm**; separate "Undersize >= 0 mm" on the screw | nut by default; screw optional | **UNVERIFIED** | online tool | MEDIUM |
| Fusion 360 FDM threads (DurbansPoison) | tolerance classes `0.###e` (external smaller) / `0.###i` (internal larger); example 0.100e + 0.100i = 0.2 mm combined gap | both | "variance from nominal form" | plugin README | HIGH (README) |
| Prusa forum summary (search-level) | tolerance varies by orientation: ~0.1 mm in Z, ~0.25 mm in X | n/a | n/a | forum | LOW, UNVERIFIED |

**Reading of the evidence:** a radial 0.10-0.20 mm is the common starting band on a 0.4 mm nozzle; the units are inconsistent across sources (BOSL2 4x on the diameter, threads-scad 0.4 unspecified), so the clearance field must be defined as radial or diametral in its label and in the API schema, and every number printed alongside it must say which.

### Which part carries it

| Practice | Who | Fit with owner's decision (nut carries it, bolt nominal) |
|----------|-----|-----------------------------------------------------------|
| Nut/hole only | BOSL2; 3dprintgenerator default; Prusa user advice | Matches |
| Both parts (loosen both) | Fusion FDM threads, Prusa forum guide, one Bambu forum user | Conflicts: owner chose one field, on the nut |
| Bolt only (negative offset on male thread) | selfcad/kingroon-style blogs (via a search summary) | Conflicts |
| Mechanism given for bolt-side offset | "external threads expand due to extrusion squish; internal holes shrink" (Sovol) | **Risk to the core value**: a printed bolt at exact nominal into a purchased nut: see Q2 |

**Not established:** whether "bolt nominal mates a bought nut" works on a real printer. The 3dprintgenerator "Undersize" field is the only precedent for letting the bolt carry a (default-zero) offset.

### Smallest size / minimum pitch on a 0.4 mm nozzle

| Source | Statement | Conf. |
|--------|-----------|-------|
| Protolabs Network, "How do you assemble 3D-printed parts?" (page read) | "Threads smaller than M5 printed via FDM should be avoided" in favour of inserts etc. | HIGH (page quote) as to what the source says |
| Sovol | M6 and larger (pitch >= 1.0 mm) is a conservative starting point; M4/M5 possible on a calibrated machine; layer height 0.12-0.16 mm, layer <= 1/6 to 1/8 of pitch; 3-5 perimeters | MEDIUM |
| Bambu Lab forum | one user avoids anything below M6; another says M8 is about the upper practical limit on a 0.4 mm nozzle (**opinion**, not reproduced as a rule) | LOW |
| threads-scad README (author's own testing; nozzle not stated) | internal threads M2 and up worked with metal bolts; printed M3 external under good conditions; M4 and up "quite reliable" | MEDIUM |
| Prusa forum | prefers 2-3 mm pitches "much easier to work with" | LOW |

**Synthesis for requirements:** reliable band is **M5 / M6 upward**; M2-M4 may build but print unreliably. Conservative pitch floor from the two vendor sources is **0.8-1.0 mm**. Because M2-M4 are *inside* the owner's M2-M20 range, they should be a cap-and-warn tier ("below the size FDM prints reliably, source cited"), not a refusal; the actual threshold is a constant to be set from the owner's print test. Consistent with L02.

### Print-orientation and mesh notes that become features

- Vertical thread axis is the usual advice (Sovol "often a good starting point"; Protolabs: vertical threads are more accurate; coarse beats fine). Hint text, not a model parameter.
- STL fineness is a *fit* parameter, not just a looks parameter (Prusa case above: 36 segments; the 1.3 mm outlier). UNVERIFIED that segment count was the cause. Export tessellation tolerance must be explicit and recorded; STEP is exact.
- Extrusion-multiplier calibration is the most-cited prerequisite. A small "how to test your clearance" note beside the field is cheap and honest; a calibration wizard is not v1.

---

## Info panel and presets (answer to brief item 3)

### What the panel should show (derived numbers people actually measure)

Every row needs: the mm value, a one-line source (field or standard + table), and whether it is *nominal*, *min/max* or *reference*.

| Group | Values | Source | Notes |
|-------|--------|--------|-------|
| Head (bolt) | across flats `s` (nom = max, min); across corners: geometric s / cos30 and the standard `e,min`, labelled separately; head height `k` (nom, max, min); bearing-face dia `dw,min`; wrench size | ISO 4014/4017 tables | The wrench size is the number users search by; where DIN differed (M10, M12, M14, M22) show the ISO value and a one-line note |
| Shank/thread (bolt) | nominal length `l`; thread length `b` (ref.), unthreaded shank `ls,min`, grip `lg,max` (4014 only); nominal diameter; pitch `P`; pitch dia `d2`; thread minor/root dia; thread depth | 4014 `b ref.`, `ls`, `lg`; ISO 724 (UNVERIFIED formulas) | For ISO 4017, `b` = `l` (full thread) |
| Tolerance (bolt, class 6g) | major dia max/min, pitch dia max/min | ISO 965-2:2024 (a distributor table shows M10 6g: major 9.732-9.968, pitch 8.862-8.994, MEDIUM) | **Label: "the model is nominal and not toleranced"**. Model major 10.000 > 6g max 9.968 |
| Nut | across flats, across corners (both senses), height `m` (max, min), `mw,min` (wrench height), `dw,min`; internal minor dia `D1`; pitch dia `D2` | ISO 4032:2023 Tables 1-2; ISO 724 | |
| Tolerance (nut, class 6H) | `D1` min/max, `D2` min/max | ISO 965-2:2024 (distributor: M10 6H pitch 9.026-9.206, minor 8.376-8.676, MEDIUM) | Same "nominal model" label |
| Pair | clearance applied (radial and diametral stated), resulting nut `D`/`D2`/`D1` after clearance, engagement length in turns, interference-check result | model + spike | The clearance rows are the product |
| Product grade | A or B, derived from (d, l) | 4014 Table 3 / 4017 | Changes which min/max apply: A for d <= M24 and l <= 10d or 150 mm, else B |
| Warnings | below-print-size, capped values, "no ISO row for this combination" | rule engine | Warning and *no number* when a value cannot be computed honestly (L02) |

Do **not** show: property class, mass, torque, preload, "strength". (Printed plastic: nothing true to say.)

### Preset / shareable-link UX in existing tools

| Tool | How the user picks a part | State sharing | Takeaway |
|------|---------------------------|---------------|----------|
| bd_warehouse / cq_warehouse (Python) | `HexNut(size="M3-0.5", fastener_type="iso4032")`, `HexHeadScrew(..., fastener_type="iso4017", length=...)`; size strings like `M6-1`; class docs list valid `fastener_type`s | n/a (code) | Size + standard as two orthogonal keys; length checked against `nominal_lengths` |
| BOSL2 `screw()` | spec string `"M6x1,10"` (diameter, pitch, length), `head=`, `tolerance="6g"` | n/a (code) | A compact spec string is what power users type |
| FreeCAD Fasteners WB | dialog: standard, diameter, length; a `Thread` boolean (off by default) | document file | Standard-first picker; threads optional because costly |
| 3dprintgenerator | dropdown of 26 specs (M2-M20 and imperial), custom pitch, 8 head styles, nut clearance 0.1, undersize, split print | none documented | Output filename carries the spec; no share link documented |
| starthere00 Nut & Bolt Maker | M3-M20 and UNC/UNF presets, matched pair, spec plates | none documented | Pair builder; paid add-ons for charts |
| ISO designation convention | `Hexagon head bolt ISO 4014 - M12 x 80 - 8.8` (the same convention in 4017/4032/4762) | n/a | Recommended display string; **drop the property class** for printed parts |

**Recommended behaviour:** one picker row "ISO 4017 / M6 / 20" fills the mm fields; the URL carries the mm fields (plus an optional `preset` id as metadata); on any manual edit the badge changes to "custom, based on ISO 4017 M6 x 20" (preset-match indicator, a differentiator above); the designation line is derived (`Hexagon head screw ISO 4017 - M6 x 20`, no property class); the legacy names ("DIN 933") are search aliases. This keeps "explicit millimetres are truth" and L05 (defaults absolute, never rescale).

---

## Competitor / prior-art feature analysis

| Feature | cq_warehouse / bd_warehouse | BOSL2 screws.scad | FreeCAD Fasteners WB | 3dprintgenerator / starthere00 | Our approach |
|---------|-----------------------------|-------------------|----------------------|--------------------------------|--------------|
| Real helical thread | optional (`simple=True` default) | yes | optional, off by default | yes (STL) | **always** on threaded parts |
| ISO 4014/4017/4032/4762 | yes (plus DIN 931, asme, etc.) | partial (nut standards 4032/4033/4035 referenced; heads generic) | yes | generic "standard sizes" | exactly these, edition and clause cited per row |
| Table citations | none visible in CSVs; values mixed (nominal vs grade B max) | references ISO 724/4032/4033/4035; notes DIN conflicts | via ScrewMaker macro | none | clause + edition + one test per row |
| Thread length `b` | not in the `iso4014` CSV I read (columns: `k`, `s`, `short`, `long`) | `thread_len` free argument | not examined | not shown | derived per standard, shown on panel |
| Printing clearance | none (it is a CAD library) | `$slop` on holes | none | one nut-clearance field | one field on the nut (owner), plus unmeasured risk Q2 |
| Pair interference proof | no | no | no | no | kernel check (differentiator) |
| Tolerances | no | geometry (6g/2A default) | no | no | numbers only (owner) |
| Left-hand | yes | yes | not examined | yes (standard in Kirshner-style libs) | boolean (owner) |
| Interfaces | Python API | OpenSCAD code | GUI inside FreeCAD | web UI | UI + HTTP API + CLI |
| Licence note | Apache-2.0; cq_warehouse last push 2024-01, last release v0.8.0 (2022-09); **bd_warehouse (build123d) is the maintained line, pushed 2026-09** | BSD-style (not re-checked) | LGPL-ish (not checked) | n/a | Do not depend on cq_warehouse for tables: no citations, mixed values |

Confidence: MEDIUM (GitHub API for repo metadata is HIGH; feature statements from docs fetches).

---

## Feature Dependencies

```
Thread cost spike (measured build time/size)
    └──gates──> every threaded field and the per-build timeout
                    └──requires──> Real helical bolt thread ──requires──> ISO 262 size/pitch rows
                    └──requires──> Real helical nut thread
                                      └──requires──> clearance field (units: radial/diametral)
                                      └──requires──> chamfered thread starts

Hex bolt (4014/4017) ──requires──> table rows (edition + clause + test each)
Hex nut (4032)       ──requires──> table rows (M5-M20 normative; M2-M4 = Q1)
thread_length field  ──requires──> per-standard presets (4014: 2d+6/12/25; 4017: = l; 4762: 2d+12)

Mating proof (interference check) ──requires──> bolt + nut + clearance + same hand
Mating proof ──enhances──> info panel "Pair" group
Printed test of default clearance ──requires──> mating proof + STL export with recorded tessellation

Info panel ──requires──> pure-maths module (no kernel; runs per keystroke)
Info panel 6g/6H rows ──requires──> ISO 965-2:2024 numbers (purchased copy)
Info panel ──requires──> product grade rule (d, l) ──requires──> table rows

Shareable link ──requires──> frozen absolute-mm defaults (L05)
Preset-match indicator ──requires──> table rows + shareable link
Legacy-name aliases ──enhances──> preset picker

UI + API + CLI parity ──requires──> one parameter model (all fields defined once)
Socket head cap (4762, v2) ──requires──> shared thread + proven pair + 4762 table (12 rows, no M18)

Tolerance-as-geometry ──conflicts──> explicit-mm truth + clearance field (owner out)
Bolt-side offset field ──conflicts?──> "one clearance field on the nut" (Q2, owner decision)
```

### Dependency Notes

- **Spike gates fields:** the owner's "measure before knobs" rule; the thread build cost decides whether the live preview is a real thread or a simplified body, and the max length per size.
- **Table rows gate presets, panel and tests:** one wrong number (e.g. a 2011-edition `dw`) is a liability the tests must catch; pin the edition per row.
- **Mating proof gates the default clearance:** the default must come from the proof plus a printed test; sources above only set the search band.
- **Info panel is independent of the kernel** (house rule: `calc.py` style pure maths), so it can ship before the proof.
- **Product grade rule couples size and length** to the panel's min/max values; it is the one place a length change silently changes a printed tolerance number.

---

## MVP Definition

### Launch With (v1: the mating-pair cut)

- [ ] Real helical right/left-hand ISO metric thread, coarse pitch, M2-M20 with cap-and-warn below the printable band: the product
- [ ] Hex bolt ISO 4014 and 4017, hex nut ISO 4032, each row cited (edition + table) with one test: table stakes plus the liability rule
- [ ] One `thread_length` field with per-standard presets
- [ ] One `clearance` field on the nut with explicit radial/diametral units and a printed-test-derived default
- [ ] Chamfered thread starts on nut and bolt: a printed pair does not start without them
- [ ] Kernel interference check of the pair: core value, the differentiator
- [ ] Info panel (head, thread, pair, 6g/6H, grade, warnings) from the pure-maths module
- [ ] STL and STEP export with recorded tessellation; UI, API, CLI on one model
- [ ] Preset picker + URL with mm fields; preset-match badge; ISO designation line without property class

### Add After Validation (v1.x)

- [ ] Legacy-name aliases ("DIN 933") with the wrench-size notice: trigger: first user searching by DIN number
- [ ] Optional bolt-side offset field: trigger: printed test shows a nominal printed bolt binds in a bought nut (Q2)
- [ ] Print-hint block (orientation, layer height vs pitch) as non-binding text: trigger: first print test done

### Future Consideration (v2+)

- [ ] Socket head cap ISO 4762 (owner's v2): 12 rows in M2-M20 (UNVERIFIED), shares thread
- [ ] Countersunk / set screws / washers: owner, after socket cap ships
- [ ] Fine pitch (ISO 8765 / 8676 / 8673 bolt and nut families): not in the brief; Q3
- [ ] Tap-drill/clearance-hole numbers, split-print, captive-nut variants: `docs/ideas/`

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Real helical thread, bolt + nut | HIGH | HIGH | P1 |
| Table rows with edition/clause/test | HIGH | MEDIUM | P1 |
| Nut clearance field + printed-test default | HIGH | LOW (field) / MEDIUM (test) | P1 |
| Chamfered thread starts | HIGH | MEDIUM | P1 |
| Mating interference check | HIGH | HIGH | P1 |
| Info panel with traceable numbers | HIGH | MEDIUM | P1 |
| STL + STEP export | HIGH | MEDIUM | P1 |
| UI + API + CLI parity | HIGH | MEDIUM | P1 |
| Shareable link + preset-match badge | MEDIUM | LOW | P1 |
| Left-hand toggle | MEDIUM | LOW | P1 (owner) |
| Printability warnings | MEDIUM | LOW | P1 |
| thread_length per-standard presets | HIGH | LOW | P1 |
| Legacy-name aliases | MEDIUM | LOW | P2 |
| Bolt-side offset field | MEDIUM (could be HIGH) | LOW | P2, decide after Q2 |
| Print-hint text | LOW | LOW | P3 |
| Socket head cap 4762 | HIGH | MEDIUM | P2 (v2, owner) |

**Priority key:** P1 must have for launch; P2 should have, add when possible; P3 nice to have.

---

## Open questions that need the owner (stop-and-ask items)

Each is a conflict between evidence and the brief; none is resolved here.

**Q1. ISO 4032:2023 normative range is M5-M39; M2-M4 nuts exist only in informative Annex A.**
Options: (a) ship M2-M4 nut rows citing Annex A, labelled "informative / historical" and buying the 2023 text to read the values; (b) nut range M5-M20, bolt range M2-M20, with a warning when a nut size is unavailable; (c) drop M2-M4 from bolts too (matches the FDM band). Recommendation: (a), because a bolt without a mating nut breaks the product, and M2-M4 are warn-tier for printing anyway. Annex A rows still need one test each.

**Q2. Does a printed bolt at nominal mate a purchased nut?**
FDM sources say external printed threads come out oversize (MEDIUM, unmeasured). Options: (a) keep one nut-carried field and state in the UI/docs that it targets a printed nut; the bought-nut case is tested in the printed-test spike; (b) add a default-zero bolt `undersize` (3dprintgenerator precedent); (c) split the field into nut clearance and bolt undersize now. Recommendation: (a) plus a printed bought-nut test in the spike, with (b) held for v1.x if the test fails.

**Q3. Fine pitch.** ISO 4014/4017/4032/4762 are coarse-pitch only. The brief neither includes nor excludes fine pitch. Recommendation: coarse only in v1, written as an explicit non-goal; a user-set pitch field would have no ISO row and conflicts with the cited-row rule.

**Q4. ISO 68-1:2023 design profile.** The brief says "ISO 68-1 profile". The 2023 edition adds a *design* profile (rounded root). The thread profile spec must pin the edition and choose basic vs design. Needs a read of the standard.

**Q5. Standards cost.** SIS lists ISO 724:2023 at 820 SEK (one data point). Rows cannot be verified from this research's sources: ISO text was read from publicly hosted previews/copies, and the ISO 4014:2011 full text came from a third-party mirror that appears to carry an unlicensed IHS copy. Treat all numbers here as lead-ins; the owner should hold purchased copies of 4014, 4017, 4032, 4762 (when v2 starts), 262, 724, 965-2 before any row ships.

## UNVERIFIED register (must not feed a table row until confirmed)

1. ISO 4017:2022 table values (only the 2014 text and the 2022 scope were read).
2. ISO 4762 rows other than M1.6-M12, its `b ref.` formula outside M1.6-M12, the 12-row M2-M20 count, absence of M3.5/M7.
3. ISO 4032:2023 Annex A (M1.6-M4) values.
4. ISO 724:2023 formulas for d2, D1, d3 (memory).
5. ISO 68-1:2023 minimum root radius 0.125 P (search summary).
6. DIN 934 M22 across-flats 32 and the exact DIN 934 values (vendor pages only).
7. Whether ISO 261 and ISO 4759-1 have editions newer than 1998 and 2000.
8. Radial vs diametral semantics of threads-scad `tolerance=0.4` and 3dprintgenerator "0.1 mm".
9. Orientation-dependent clearance (0.1 Z / 0.25 X) and the cause of the 1.3 mm Prusa outlier.
10. That no competitor documents a URL-round-trippable fastener generator (absence of evidence).
11. McMaster/TraceParts thread representation in STEP (one blog; TraceParts not found).
12. bd_warehouse thread-end-finish options (docs fetched did not list them).
13. The nut-side thread countersink angle clause.
14. CNC Kitchen's thread test content (the Printables page returned 403).

## Pitfall note for PITFALLS.md (feature-level hazard)

Aggregated web tables disagree with the standards and with each other. Examples seen: fasteners.eu lists ISO 4017 M3 `s` = 5 (the standard has 5.5, per the 4014:2022 table and the 4017:2014 text), and jadealloys shows M6 `k` = 3.2 and M16 `s` = 23.16 (the standard has `k` = 4.0 and `s` = 24 nom; 23.16 is `s,min` for grade B). No web table in this research should be used to fill a row; tests must be written from the standard text.

## Sources

**Standards (HIGH unless noted)**
- ISO 4014:2022 public sample (iTeh): https://cdn.standards.iteh.ai/samples/72579/81f2b1e966b440d7a25f6734e508ea48/ISO-4014-2022.pdf; scope/edition: https://www.sis.se/en/produkter/mechanical-systems-and-components-for-general-use/fasteners/bolts-screws-studs/iso-40142022/
- ISO 4014:2011 full text (third-party mirror, see Q5): https://pppars.com/wp-content/uploads/2021/07/ISO-4014-2011.pdf
- ISO 4017:2014 sample: https://cdn.standards.iteh.ai/samples/63206/dd63a69c4be3432aac1914bccda73b2c/ISO-4017-2014.pdf; 2022 scope: https://www.sis.se/en/produkter/mechanical-systems-and-components-for-general-use/fasteners/bolts-screws-studs/iso-40172022/; AFNOR: https://www.boutique.afnor.org/en-gb/standard/iso-40172022/fasteners-hexagon-head-screws-product-grades-a-and-b/xs137372/327514
- ISO 4032:2023 sample: https://cdn.standards.iteh.ai/samples/75016/5b1f83bd2dc44fc199973e9957a75086/ISO-4032-2023.pdf; scope/edition: https://www.sis.se/en/produkter/mechanical-systems-and-components-for-general-use/fasteners/nuts/iso-40322023/
- ISO 4762:2004 sample: https://cdn.standards.iteh.ai/samples/34460/06335046afaf46fb8e84d91a3eda001d/ISO-4762-2004.pdf
- ISO 262:2023 sample: https://cdn.standards.iteh.ai/samples/85105/41945f5384e447fe8c9492f4e23251a3/ISO-262-2023.pdf; ISO 262:1998 sample: https://cdn.standards.iteh.ai/samples/4167/365d2316ebbe496e87cc7e365bdc8331/ISO-262-1998.pdf
- ISO 261 (SIS): https://www.sis.se/en/produkter/mechanical-systems-and-components-for-general-use/screw-threads/metric-screw-threads/iso261/
- ISO 724:2023 (SIS): https://www.sis.se/en/produkter/mechanical-systems-and-components-for-general-use/screw-threads/metric-screw-threads/iso-7242023/
- ISO 68-1:2023 (AFNOR): https://www.boutique.afnor.org/en-gb/standard/iso-6812023/iso-general-purpose-screw-threads-basic-and-design-profiles-part-1-metric-s/xs143155/351967
- ISO 965-1:2026 / 965-2:2024 listings (MEDIUM): https://www.iso.org/standard/87889.html, https://www.iso.org/standard/87890.html, https://www.dinmedia.de/en/standard/din-iso-965-1/402951158
- ISO 4759-1 scope (MEDIUM): https://webstore.ansi.org/standards/iso/ISO47592000
- DIN mapping (MEDIUM): https://www.dinmedia.de/en/standard/din-iso-4017/3071489, https://www.dinmedia.de/en/standard/din-912/1078263, https://blog.eurolinkfss.com/din-933-vs.-iso-4017-and-din-931-vs.-iso-4014, https://fastenerstandards.com/din-934-vs-iso-4032-comparison/
- 6g/6H numeric cross-check, M10 row (MEDIUM): Bossard metric ISO threads catalogue pages, https://assets.eu.ctfassets.net/0vp0u5uh75zd/2tYqENAuufvdsudjM8Qbrc/b3461eaa59c2203d3a8b9509ac24dacf/096_098_Metric_ISOthreads_Fastening_EN_01_2025.pdf

**FDM practice (MEDIUM/LOW as tagged)**
- Sovol: https://www.sovol3d.com/blogs/news/3d-printing-threads-and-screws-how-to-design-reliable-fdm-fasteners
- Protolabs Network (Hubs): https://www.hubs.com/knowledge-base/how-assemble-3d-printed-parts-threaded-fasteners/
- Bambu Lab forum: https://forum.bambulab.com/t/printing-nuts-and-threaded-holes/145508
- Prusa forum: https://forum.prusa3d.com/forum/original-prusa-i3-mk2-s-others-archive/guide-to-printing-threads/ , https://forum.prusa3d.com/forum/original-prusa-i3-mk3s-mk3-how-do-i-print-this-printing-help/thread-tolerances-on-prusa-mk3s/ , https://forum.prusa3d.com/forum/original-prusa-i3-mk3s-mk3-how-do-i-print-this-printing-help/nut-and-bolt-threads-dont-fit/
- BOSL2 screws docs: https://github.com/BelfrySCAD/BOSL2/wiki/screws.scad ; threads-scad: https://github.com/rcolyer/threads-scad ; Fusion FDM threads: https://github.com/DurbansPoison/Fusion-360-FDM-threads
- 3dprintgenerator: https://3dprintgenerator.com/parametric-screw-generator ; starthere00: https://starthere00.com/tools/nut-bolt

**Prior art**
- bd_warehouse (data CSVs, fastener docs, repo metadata via GitHub API): https://github.com/gumyr/bd_warehouse ; cq_warehouse: https://github.com/gumyr/cq_warehouse ; docs: https://cq-warehouse.readthedocs.io/en/latest/fastener.html
- FreeCAD Fasteners Workbench: https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Fasteners_Workbench.md
- Modelled vs cosmetic threads in CAD (LOW): https://www.cati.com/blog/simplified-mcmaster-carr-parts-in-assemblies/

---
*Feature research for: parametric ISO metric threaded fastener generator (screw)*
*Researched: 2026-10-05*
