# Stack Research

**Domain:** parametric ISO metric threaded fasteners (hex bolt/screw ISO 4014/4017, hex nut ISO 4032, socket cap ISO 4762 in release two), real helical threads, FDM-printable mating pairs, STL/STEP export, web UI + HTTP API + CLI on one Pydantic model
**Researched:** 2026-10-05
**Scope:** only what L01 left open: the thread-generation approach, any library for it, and where ISO table data comes from. The locked base (Python 3.12, CadQuery 2.8.0 + cadquery-ocp 7.9.3.1.1, FastAPI/Pydantic v2/uvicorn, argparse, vanilla JS + vendored three.js, pytest, Docker, GitHub Actions) is not re-opened.
**Overall confidence:** HIGH on "do not adopt cq_warehouse or build123d/bd_warehouse" and on "enter the tables by hand"; HIGH on the thread construction inside the measured space (below); MEDIUM on everything the measurements did not reach (linux/amd64, mesh targets vs clearance, other CAD importers, a printed pair).

## How to read the evidence tags

| Tag | Meaning |
|-----|---------|
| MEASURED | I ran it in this session. Machine: Apple M2 Max (12 cores), macOS arm64, Python 3.12.13, `cadquery 2.8.0`, `cadquery-ocp 7.9.3.1.1` (the repo's pinned pair), single process unless a row says "5 parallel". Numbers are not bounds (L07: re-sweep in the linux/amd64 image before any constant is written). |
| SOURCE | Read from the project's own source, PyPI JSON or GitHub API today. |
| ISO-PREVIEW | Read from the free iTeh preview PDF of the standard (first 10 pages, which include the dimension tables for 4014/4017/4032; the stepped "bold line" length ranges do not survive text extraction). |
| SNIPPET | Search-result snippet from a standards store or a secondary page. MEDIUM at best. |
| UNVERIFIED | Not checked live. Do not build on it. |

The `research-plan` seam routed both questions to `websearch`/`context7`; `classify-confidence` rates `websearch` and `webfetch` LOW and `context7` MEDIUM. `context7` is not available as a tool in this run, so no claim here rests on it. Every claim I rely on is either MEASURED or SOURCE/ISO-PREVIEW first-hand; provider-tier LOW material (search snippets) is labelled SNIPPET and never carries a decision.

## Answer in one screen

1. **`cq_warehouse` is a reference and the thing to beat, never a dependency.** It exists, is Apache-2.0, and its fastener + thread code runs on the pinned pair (I built ISO 4017 M6x20 and ISO 4032 M6 on Python 3.12 / cadquery 2.8.0 / OCP 7.9.3.1.1: valid, one solid). But it is not on PyPI (HTTP 404 for `cq_warehouse` and `cq-warehouse`), install is git-only, the last commit is 2024-01-20 and the last code change 2023-09-24, its thread fuse costs about quadratic time in turns with about 7 % hard failures on the M2-M20 grid, and its tables carry no standard/edition/clause and disagree with the current ISO editions.
2. **Build threads in-house, as a twisted transverse section.** One analytic outline r(theta) of the ISO 68-1 basic profile, extruded along a straight spine with an auxiliary helix (`BRepOffsetAPI_MakePipeShell`, `SetMaxSegments(500)`), in segments of 5 turns sewn into one solid (`BRepBuilderAPI_Sewing`, 1e-4). No boolean with a core. 166 of 166 configurations (11 sizes M2-M20, lengths up to 250 turns) came out valid, one solid, volume within 1.2e-5 of the closed form; thread alone 0.10 s median, a whole bolt (head, tip chamfer, fuse) 0.4-0.8 s single-process.
3. **The naive CadQuery path (helix sweep + union with a core cylinder) is not usable.** 35 % hard failures on the same grid, and a quarter of all configurations (35 of 139) come back `isValid() == True`, one solid, with the core silently missing (volume 75-80 % short).
4. **`build123d` / `bd_warehouse` cannot join this environment.** build123d 0.13.0 needs `cadquery-ocp-novtk 8.0.x`; cadquery 2.8.0 needs `cadquery-ocp <8.0`; both ship a top-level `OCP` package. Its fasteners are a Compound of overlapping solids (22 solids for M6x20), not a solid. It is, however, actively maintained and has two ideas worth copying (an FDM `manufacturing_compensation` and an `interference` overlap).
5. **ISO table data: no library cites rows, so enter them by hand, edition-pinned and clause-cited, one test per row.** Cross-checking the two popular CSVs against ISO 4017:2022 / 4014:2022 / 4032:2023 found 0 of 15 ISO 4017 k values matching, 4 of 15 ISO 4014 values wrong, and ISO 4032 M5-M20 matching 9 of 9. Use them only as a differential oracle.
6. **Three premises in the brief are stale (details below):** ISO 4014 and 4017 were replaced in 2022, ISO 4032 in 2023 (it now covers M5-M39; M2-M4 nuts live only in an informative "historical" annex), and ISO 68-1 was replaced in 2023. "4759" is product-grade tolerances, not the source of 6g/6H.

## Recommended Stack

### Core Technologies (additions to the locked base: none)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `cadquery` | 2.8.0 (pinned, L06) | Solids, booleans, STL/STEP export | Already locked. 2.8.0 (2026-06-21) requires `cadquery-ocp >=7.9.3.1,<8.0` (SOURCE, PyPI). Python `>=3.11`. |
| `cadquery-ocp` | 7.9.3.1.1 (pinned) | Direct OCCT access for `BRepOffsetAPI_MakePipeShell`, `BRepBuilderAPI_Sewing`, `BRepGProp` | Already locked. The thread engine needs OCP calls CadQuery does not expose (`SetMaxSegments`, sewing, precise volume). `model.py` is already the only doorway to `cadquery`/`OCP` (import-linter), so this adds no boundary. Both spur's and screw's `pyproject.toml` already carry the mypy override `OCP.* -> ignore_missing_imports` (cadquery-ocp ships no stubs); the reference code below passes `mypy --strict` with the repo's own config (MEASURED). |
| Twist-section thread engine (own code, about 70 lines) | n/a | External thread (bolt) and internal-thread cutter (nut) for every fastener type | Robust (0 failures in 166 configs), fast (0.1 s), no new dependency, exact helical geometry (0.1 um from ideal at 14 flank points), one analytic section so volume, clearance and the mating proof have closed forms. See "Measured evidence". |
| Closed-form section area | n/a | Volume of a threaded length without asking the kernel | `A = pi/8 ro^2 + pi/4 rr^2 + 5pi/24 (ro^2 + ro rr + rr^2)`, `ro = d/2 + c`, `rr = d/2 - 5H/8 + c`, volume of a thread of length L = A*L. Matches numeric integration to 1e-11 and the kernel to a few 1e-6 (MEASURED). Lives in `calc.py` (pure maths, no kernel import). |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| none new | n/a | The thread, table and mating-proof work needs no extra runtime dependency | Hold this line; every added dependency is another pin in `requirements.txt` (L06) and another wheel to have on linux/amd64 + arm64 |
| `pytest` (already locked) | existing | Row tests, closed-form-vs-kernel tests, build matrix | Table rows are pure-data tests; kernel tests use the closed form as the oracle (see Patterns) |
| `bd_warehouse` / `cq_warehouse` CSVs | n/a | Differential oracle in a test helper only | Never as a source of truth and never imported at runtime; see "Table data" |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `BRepGProp.VolumeProperties_s(shape, props, eps, False, False)` | Precise kernel volume for tests and for any number printed from the kernel | `Shape.Volume()` uses the default integration and is off by +1.1e-3 at 150 turns (MEASURED). `eps=1e-5` gave 2.7e-5 in 0.4 s, `eps=1e-7` 8e-6 in 0.8 s. Prefer the closed form for the info panel (L08). |
| Differential build matrix (11 sizes x lengths up to 250 turns, one subprocess per cell, hard timeout) | Prove the thread construction before any field exists | The harness I used is about 60 lines; port it into `bench/` (L07). Checks per cell: `isValid()`, exactly one solid, volume vs closed form (sign included, see inverted-solid note), and a wall-clock timeout. |
| 2D section check | Exact "bolt fits inside nut" proof in about 8 ms | Two planar faces from `section(d, p, 0)` and `section(d, p, c)`; `bolt_face.cut(void_face).Area() == 0` means no interference for every screw-motion placement (MEASURED: 0.0 mm2 for c >= 0, 0.839 mm2 at c = -0.05 on M6). |

## Reference implementation (verified)

This is the construction the numbers below were measured on. It passes `mypy --strict` with the repo's `pyproject.toml` and, on M6, builds right- and left-hand threads of 20, 37.3 and 200 mm with volume error 1.5e-6 to 4.1e-6, z exactly `[0, L]`, crest at +90 degrees for right hand and -90 degrees for left hand at z = P/4 mod P (MEASURED). It is an ISO 68-1 basic profile (flat crest P/8, flat root P/4, depth 5H/8); the design profile with rounded root (ISO 68-1:2023 Clause 6) is not modelled (see Gaps).

```python
import math
import cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakePipeShell
from OCP.TopoDS import TopoDS

SEG_TURNS = 5  # measured: 2..10 mesh well; >=20 turns per face bloats the STL about 6x


def section(d: float, p: float, c: float = 0.0, nf: int = 14) -> cq.Wire:
    """Transverse (z = const) outline of an ISO basic-profile thread, one start.
    crest flat P/8 at d/2, root flat P/4 at d/2 - 5H/8; flanks are Archimedean spirals
    (radius linear in angle), sampled at nf points (nf=14: 0.1 um off ideal, nf=4: 7 um)."""
    ro = d / 2 + c
    rr = d / 2 - 5 / 8 * p * math.sqrt(3) / 2 + c

    def pt(r: float, th: float) -> tuple[float, float]:
        return (r * math.cos(th), r * math.sin(th))

    w = cq.Workplane("XY").moveTo(*pt(ro, -math.pi / 8))
    w = w.threePointArc(pt(ro, 0), pt(ro, math.pi / 8))
    a0, a1 = math.pi / 8, 3 * math.pi / 4
    w = w.spline([pt(ro - (ro - rr) * i / nf, a0 + (a1 - a0) * i / nf) for i in range(1, nf + 1)],
                 includeCurrent=True)
    w = w.threePointArc(pt(rr, math.pi), pt(rr, 5 * math.pi / 4))
    b0, b1 = 5 * math.pi / 4, 15 * math.pi / 8
    w = w.spline([pt(rr + (ro - rr) * i / nf, b0 + (b1 - b0) * i / nf) for i in range(1, nf + 1)],
                 includeCurrent=True)
    wire = w.close().val()
    assert isinstance(wire, cq.Wire)
    return wire


def twist(d: float, p: float, turns: float, c: float = 0.0, left: bool = False) -> cq.Solid:
    length = turns * p
    spine = cq.Wire.assembleEdges([cq.Edge.makeLine(cq.Vector(0, 0, 0), cq.Vector(0, 0, length))])
    aux = cq.Wire.makeHelix(p, length, 1, lefthand=left)  # radius 1 is arbitrary: only the twist rate matters
    pipe = BRepOffsetAPI_MakePipeShell(spine.wrapped)
    pipe.SetMaxSegments(500)   # default fails (Standard_Failure) from ~80 turns
    pipe.SetMode(aux.wrapped, False)
    pipe.Add(section(d, p, c).wrapped)
    pipe.Build()
    pipe.MakeSolid()
    return cq.Solid(pipe.Shape())


def thread(d: float, p: float, length: float, c: float = 0.0, left: bool = False) -> cq.Solid:
    """Solid with z in [0, length]; no boolean. Segments are integer-turn copies, so seams match exactly."""
    n = length / p
    full = int(n // SEG_TURNS + 1e-9)
    rest = n - full * SEG_TURNS
    parts: list[tuple[cq.Solid, float, float]] = []
    if full:
        base = twist(d, p, SEG_TURNS, c, left)
        parts += [(base.translate(cq.Vector(0, 0, i * SEG_TURNS * p)),
                   i * SEG_TURNS * p, (i + 1) * SEG_TURNS * p) for i in range(full)]
    if rest > 1e-9:
        z0 = full * SEG_TURNS * p
        parts.append((twist(d, p, rest, c, left).translate(cq.Vector(0, 0, z0)), z0, length))
    if len(parts) == 1:
        return parts[0][0]
    sew = BRepBuilderAPI_Sewing(1e-4)
    for i, (solid, z0, z1) in enumerate(parts):
        for f in solid.Faces():
            if f.geomType() == "PLANE":
                z = f.Center().z
                if (i > 0 and abs(z - z0) < 1e-7) or (i < len(parts) - 1 and abs(z - z1) < 1e-7):
                    continue  # interior seam cap
            sew.Add(f.wrapped)
    sew.Perform()
    return cq.Solid.makeSolid(cq.Shell(TopoDS.Shell_s(sew.SewedShape())))
```

Use: the bolt shank is `thread(d, p, L + 1.0).translate((0, 0, -1.0))` fused to the head (one planar-contact boolean, 0.16-0.29 s), the nut hole is `body.cut(thread(d, p, m + 2.0, c=clearance).translate((0, 0, -1.0)))` (one boolean, 0.25-0.35 s, volume equal to `body - A(c)*m` within 1.1e-6 for every size M2-M20). The nut cutter is the same outline grown by the radial clearance `c`; that is a design choice for the Architecture/Features documents, shown here because the construction makes it a one-argument change.

## Measured evidence

All rows MEASURED on the machine above unless tagged otherwise. "Grid" = 11 sizes (M2, M2.5, M3, M4, M5, M6, M8, M10, M12, M16, M20 at ISO coarse pitch) x lengths 6..200 mm with L/P <= 100 turns = 139 configurations, one subprocess each, 5 in parallel (so wall times are inflated against single-process runs).

### A. Thread construction: which one

| Construction | Hard failures on the grid | Silent wrong result | Time |
|--------------|---------------------------|---------------------|------|
| **Twist section, one pipe, `SetMaxSegments(500)`** | 0 / 139 (N <= 100). Above 100 turns 3 / 27 came out inside-out | Inverted solids report `isValid() == True`, one solid, volume = -1.0x expected (M3 L80, M4 L120, M8 L200); in a full bolt M8x200 gave 5205.66 mm3 against about 9000 expected | thread 0.04-0.17 s |
| **Twist section in 5-turn segments, sewn** (recommended) | 0 / 166, N up to 250 | none: volume within 1.2e-5 of the closed form; K=5 vs K=3 bolt volumes agree to 3.4e-5 | thread median 0.10 s, p90 0.32 s, max 0.53 s; full bolt median 0.69 s, p90 1.6 s, max 2.4 s (5 parallel); single-process M3x10 0.42 s, M6x20 0.43 s, M6x60 0.72 s, M10x40 0.52 s, M20x80 0.57 s |
| `cq_warehouse` `IsoThread` (fade/raw) fused to a core cylinder | 10 / 139 (7 invalid, 2 multi-solid, 1 volume off by 22 %) | most others within 1-3 % of an independent reference (reference is itself approximate; not a pass/fail claim) | median 0.65 s under 10 turns, 1.4 s at 20-29, 3.0 s at 30-39, 8.5 s at 60-69, 15 s at 80-89, about 42 s at 90+ (few samples); max 49.6 s. About quadratic in turns |
| Naive `Workplane.sweep(helix, isFrenet=True)` of a trapezoid + `fuse` with a core | 48 / 139 (7 kernel errors `MakePipeShell::MakeSolid`, 3 invalid, 3 multi-solid, 35 one-solid-valid with the core missing: volume 75-80 % short). Rotating the core seam 37 degrees did not help (46 / 139) | the 35 are the dangerous ones: `isValid()` True | about 1 s median, 10-15 s at 80-100 turns |
| `Workplane.twistExtrude` as shipped (default `MaxSegments`) | `Standard_Failure` from 80 turns on M6/M10/M20 (ok at 60) and from 100 on M2/M3 (ok at 80) | volume off up to 1e-3 (integration, not geometry) | 0.04-0.15 s while it works |
| `bd_warehouse` 0.3.0 `IsoThread` / `HexHeadScrew` (build123d 0.13.0, OCP 8.0.1) | not run on the grid | the part is a Compound of overlapping solids (M6x20: 22 solids, 870.8 mm3 summed; fused to one solid 824.2 mm3, which agrees with `cq_warehouse`'s 824.0) | build 0.05 s, fuse to one solid 1.5 s (M6x20, 22 solids), 3.0 s (M6x40), 1.9 s (M10x40), 2.5 s (M3x20, 40 turns), 2.3 s (M20x80) |

Why the fuse is the weak point: a tooth solid wound N turns around a core is intersected with the core's cylinder face along an N-turn helix, and OCCT's boolean cost grows with N while its robustness does not. The twist construction has no tooth/core intersection at all: the outline carries the root, the flanks and the crest, so the solid is the thread.

Why segments: the one-pipe version builds in 0.26 s at 200 turns but (a) inverts silently at some turns above 100 and (b) meshes into about 10 000 triangles per turn. Sewing 5-turn segments removes both. Segments are integer-turn translated copies of one base solid, so the seams are identical curves; `BRepBuilderAPI_Sewing(1e-4)` closes them without a boolean (0.05-0.14 s).

Cross-kernel check (pipe step only): on OCP 8.0.1 via a build123d venv the same pipe construction reproduces the default failure from 80 turns, works with `SetMaxSegments(500)`, volume within 1e-5 at 10, 60, 80, 150 and 200 turns. Sewing, booleans and meshing were not re-run there.

### B. STL and STEP size for helical surfaces

Tessellation presets are spur's (`preview` = linear 0.08 mm / angular 0.5 rad, `fine` = 0.01 / 0.1). Binary STL, no gzip unless stated.

| Part (M6 pitch 1.0 unless stated) | Construction | Preset | Triangles | STL | Export time |
|-----------------------------------|--------------|--------|-----------|-----|-------------|
| bolt 20 mm | one pipe | preview | 166 866 | 8.1 MB (4.3 MB gz) | 1.0 s |
| bolt 20 mm | one pipe | fine | 1 148 170 | 56 MB | 33.9 s |
| bolt 60 mm | one pipe | fine | 4 469 754 | 218 MB | 153 s |
| shank only, 20 turns | one pipe | (0.08, 0.5) | 193 384 | 9.4 MB | 1.2 s |
| shank only, 20 turns | `cq_warehouse` ruled tooth + core | (0.08, 0.5) | 4 686 | 0.23 MB | 0.02 s |
| bolt 20 mm | **sewn 5-turn** | (0.05, 0.5) | 38 644 | 1.9 MB | 0.06 s |
| bolt 60 mm | sewn 5-turn | (0.05, 0.5) / (0.02, 0.3) | 116 222 / 356 510 | 5.5 / 17.0 MB | 0.15 / 0.44 s |
| M20 bolt 80 mm | sewn 5-turn | (0.05, 0.5) / (0.02, 0.3) | 237 388 / 652 068 | 11.3 / 31.1 MB | 0.28 / 1.0 s |
| M6 nut m=5.2 | sewn cutter | (0.05, 0.5) | 11 678 | 0.57 MB | not timed |
| M20 nut m=18 | sewn cutter | (0.05, 0.5) | 52 058 | 2.5 MB | not timed |

STEP, modelled thread, one solid: M6x20 bolt 1.16 MB, M6x60 2.9 MB, M6 nut 0.47 MB (export 0.01-0.05 s). Round trip: re-imported in cadquery 2.8 / OCP 7.9 and in build123d 0.13 / OCP 8.0.1, valid, one solid, volume identical to 0.01 mm3. How FreeCAD, Fusion, SolidWorks or Onshape handle these B-spline helical faces is UNVERIFIED.

Mesh accuracy matters here because the nut's clearance is the product. Mesh volume against kernel volume, default `BRepMesh` settings, M6x20 bolt / M6 nut, one-pipe construction:

| (linear, angular) | bolt | nut (hole shrinks, so volume grows) |
|-------------------|------|--------------------------------------|
| (0.1, 0.5) | -1.66 % | +0.80 % |
| (0.05, 0.5) | -0.83 % | +0.57 % |
| (0.02, 0.3) | -0.28 % | +0.17 % |
| (0.01, 0.2) | -0.17 % | +0.07 % |

`ControlSurfaceDeflection=False` (via `IMeshTools_Parameters`) cuts the triangle count 10x (193 384 to 19 124) but the nut volume then reads +5.1 to +6.2 % at every tolerance and the bolt -1.1 to -4.6 %: the mesh eats the clearance. Do not use it for a download. It is acceptable for a coarse viewer-only mesh (M6x20 bolt at (0.1, 0.5): 13 198 triangles, 0.65 MB) because no one measures a part off the viewer. The STL tolerance must sit well under the clearance; the clearance default is a spike-and-print result (PROJECT.md) and is UNVERIFIED here.

All STL meshes checked were watertight (zero non-2-manifold edges, one-pipe and sewn) in the preview and fine presets tested.

### C. The mating proof: what it costs

| Check | Cost (M6 unless stated) | Verdict |
|-------|-------------------------|---------|
| 2D section cut, planar faces | 6-8 ms | exact for every screw-motion placement; interference 0.0 mm2 at c >= 0, 0.839 mm2 at c = -0.05. Use at serve time and in unit tests |
| 3D `bolt.intersect(nut)`, full bodies, one-pipe | 3.6 s (c = 0.2), 6.8 s (0.1), 11.6 s (0.02), 26.9 s (c = 0); M20: 16 s to 121 s, and at c = 0 it returned 2 garbage solids of zero volume | too slow and degenerate as c approaches 0 |
| 3D intersect, 10-turn engaged piece vs full nut, sewn | 1.6 s (0.1), 3.0 s (0.05), 4.8 s (0.02), 8.2 s (c = 0, clean zero); c = -0.05 reported 4.36 mm3 (sensitivity check) | usable in CI / a background check, not per keystroke |

### D. Kernel volume accuracy

Default `Shape.Volume()` on a 150-turn M6 thread is +1.1e-3 off (and the same on M3): a GProp integration artefact, not a geometry error (vertices of the tessellated surface sit within 0.2 um of the ideal outline at 10, 60 and 150 turns for M6 and M20). Any kernel-derived number on the info panel must use a precise estimator or, better, the closed form (L08: a number someone cuts metal to).

## Answers to the three research items

### 1. `cq_warehouse.fastener`: dependency, reference, or the thing to beat?

**Reference, and the thing to beat. Not a dependency.** Verdict HIGH.

| Fact | Value | Tag |
|------|-------|-----|
| Exists, current version | 0.8.0 (`setup.cfg`); tags v0.5.3 to v0.8.0; GitHub `gumyr/cq_warehouse`, 152 stars, 21 open issues and PRs by the API count, not archived | SOURCE |
| On PyPI | No. `https://pypi.org/pypi/cq_warehouse/json` and `cq-warehouse` both return 404. README installs from git (`pip install git+https://github.com/gumyr/cq_warehouse.git`) | SOURCE |
| Maintenance | Last commit 2024-01-20 ("Updating for security vulnerability"); last code change 2023-09-24 (merge of PR #84). Issues opened after that and still open: #87 "Screws with threads don't seem to work" (2024-03), #86 "external thread with end_finishes=("chamfer","square")" (2024-02). The author now maintains `bd_warehouse` for build123d | SOURCE |
| Licence | Apache-2.0: header in `thread.py`, `setup.cfg` classifier, GitHub licence API. (The LICENSE file itself was not read: that API call timed out in this session. Confirm the file at the source before copying any code.) | SOURCE / UNVERIFIED for the LICENSE file |
| Python / cadquery / OCP | `python_requires >=3.9`, `install_requires` empty (it imports `cadquery` and `OCP.TopoDS`). Installed from git on Python 3.12.13 next to cadquery 2.8.0 + cadquery-ocp 7.9.3.1.1: `import cq_warehouse.fastener` OK; `HexHeadScrew(size="M6-1", length=20, fastener_type="iso4017", simple=False)` 0.98 s, valid, 1 solid, 824.0 mm3; `HexNut("M6-1","iso4032",simple=False)` 0.56 s, valid, 1 solid | MEASURED |
| Defaults | `simple=True`: no thread unless asked | SOURCE |
| How it builds a thread | Not a sweep. `Thread.make_thread_faces` makes `Wire.makeHelix` edges at the apex and root radii, four ruled surfaces between them, a shell, a solid (a tooth only, "raw" ends extend past `[0, L]`). The caller fuses it to a core cylinder. A `0.001` mm radial fudge is added so the tooth overlaps the core. Its own comment says it found this faster and more reliable than sweep or extrude-with-rotation (2021) | SOURCE |
| Published thread times | tooth only: raw 0.018 s, fade 0.087 s, square 0.370 s, chamfer 1.641 s (hardware unspecified; no fuse) | SOURCE (docs) |
| Times once fused to a core (what you actually need) | 0.65 s under 10 turns to about 15 s at 80-89 turns, quadratic-ish; 7 % hard failures (invalid / multi-solid) on the grid | MEASURED |
| Tables | One CSV per head type, columns like `iso4017:k`, `iso4017:s`. No standard edition, no clause, no table number, no source column. Every row is a claim with no citation (PROJECT.md: "a row without a cited source does not ship") | SOURCE |
| Table accuracy vs current ISO | See "3. Table data": ISO 4017 k 0/15 matching, ISO 4014 4 of 15 wrong, ISO 4032 9/9 matching | MEASURED against ISO-PREVIEW |

Why not a dependency: git-only install fits badly with a pinned, constraint-resolved closure (L06) and a hashless VCS pin is the weakest link in it; the code is unmaintained against a kernel pair that is about to move (see Version Compatibility); the part that matters, the fuse, is the part that is slow and flaky; the tables cannot be cited.

Why it is still the reference: (a) its ruled-surface faces mesh 10-40x lighter than a B-spline pipe (4 686 vs 193 384 triangles for 20 turns at the same tolerance), which is a real advantage the twist construction only recovers through segmentation; (b) it shows the right API shape (hand, end finishes `raw`/`fade`/`square`/`chamfer`); (c) `fade` ends avoid the trailing boolean, a cheaper tip than a chamfer cone (a tip chamfer boolean is the dominant cost of my bolt build, 0.17-0.43 s). Worth a spike if the tip boolean ever bites.

### 2. Thread generation in OCCT

**Use the twisted transverse section built in sewn 5-turn segments** (see "Reference implementation"). Verdict: HIGH inside the measured space, MEDIUM overall (one machine, one architecture, ISO basic profile only, no printed pair).

Options weighed:

| Approach | Verdict | Reason |
|----------|---------|--------|
| Twisted transverse section, 5-turn sewn segments (own code) | **Adopt** | 166 / 166 valid single solids to 250 turns; closed-form volume; no tooth/core boolean; 0.1 s thread; 8-10x fewer triangles than one pipe; same behaviour on OCP 7.9.3 and 8.0.1 for the pipe step |
| `Workplane.sweep(helix)` + fuse to core | Reject | 35 % hard failures, a quarter of all configurations with a silently wrong volume (MEASURED); the classic tutorial path |
| `cq_warehouse` ruled tooth + core fuse | Reference only | works about 93 % of the grid but cost grows about quadratically with turns and 7 % hard-fail; no dependency |
| `bd_warehouse` per-loop loft | Reference only | outputs a Compound of overlapping solids; fusing costs 1.5-3 s; open issues on fuse/chamfer (#23, #63); needs OCP 8 |
| `Workplane.twistExtrude` as shipped | Reject as shipped | hard cap at 60-80 turns, fixed by `SetMaxSegments(500)` which means going through OCP anyway |
| OpenSCAD-style mesh threads | Reject | no STEP; the product is a precise solid |
| Own analytic mesher for STL (bypass `BRepMesh`) | Not now | only if the spike shows STL size cannot be met after segmentation; bigger code, loses the single-source solid |

Build time vs length and diameter: thread alone is a function of turns, not of diameter (0.04-0.17 s up to 100 turns across all 11 sizes; 0.4 s at 200 turns). Whole bolt: 0.4-0.8 s up to M20x80 / M6x60, dominated by the tip-chamfer intersect (0.17-0.43 s) and the head fuse (0.16-0.29 s). ISO 4017:2022 limits the greatest nominal length to min(10 d, 200 mm) (footnote d, ISO-PREVIEW), so the allowed range tops out at about 80 turns (M16 160 mm / P 2 = 80, M20 200 / 2.5 = 80; M2 20/0.4 = 50, M3 30/0.5 = 60, M6 60/1 = 60, M8 80/1.25 = 64, M10 100/1.5 = 67, M12 120/1.75 = 69); ISO 4014:2022 allows min(10 d, 500 mm). Anything beyond 10 d is a product decision, and was measured valid to 250 turns.

STL triangle count and export size: see table B. The honest summary: one pipe is unusable (8 MB at the `preview` preset for a 20 mm M6), sewn segments are workable (1.9 MB / 38 644 triangles for the same part at 0.05 mm), and a download at 0.02 mm deflection is tens of MB for a long M20. The live viewer and the download must not share a mesh; that decision is a spike, not a guess.

Boolean robustness: the construction has two booleans left, both between the thread and planar or conical faces (head fuse, tip chamfer) and one cut for the nut. The matrix ran them 166 times without a failure, and the volume check caught every wrong answer in the other constructions. Make that check part of the build path (L08), including the sign of the volume; an inverted solid passes `isValid()`.

### 3. A library for ISO table data with cited sources?

**No such library exists; hand-enter, edition-pinned, clause-cited.** Verdict HIGH.

What I looked at:

| Source | Finding | Tag |
|--------|---------|-----|
| `cq_warehouse` CSVs | no edition, clause or source column; `iso4017:k` column differs from ISO 4017:2022 for all 15 sizes compared (M6: CSV 4.24, standard nominal 4, max 4.15, min 3.85); ISO 4014 column wrong for M1.6, M2, M2.5, M3.5 (CSV 1.3/1.6/1.9/2.6 against 1.1/1.4/1.7/2.4); ISO 4032 `m`, `s` correct for M5, M6, M8, M10, M12, M14, M16, M18, M20 (9/9); M7 absent everywhere (new in the 2022/2023 editions) | MEASURED vs ISO-PREVIEW |
| `bd_warehouse` 0.3.0 CSVs | identical to `cq_warehouse` in every compared cell | MEASURED |
| BOLTS (`boltsparts/BOLTS`) | open parts library with a `standards:` block per class (body, status, standard, e.g. DIN 933 "withdrawn"); data LGPL-2.1+, repo GPL-3.0; last commit 2022-11-02. Table-level metadata, not clause-level, and DIN-oriented | SOURCE |
| FreeCAD Fasteners workbench | has ISO 4017 / 4032 tables; data licence UNVERIFIED | SNIPPET |
| PyPI search for ISO 724 / 965 tolerance packages | nothing found | SNIPPET (negative) |

So there is nothing to import. The free iTeh previews expose the full dimension tables of ISO 4014:2022 (Tables 1-3), 4017:2022 (Tables 1-4) and 4032:2023 (Tables 1-2) for checking a hand-entered row against the standard, but the previews lose the "stepped bold line" that marks each size's standard length range, so that part of the tables must be read from the PDF page image or the paid standard (UNVERIFIED which lengths are in range per size). Whether storing dimension values (facts) with a citation is acceptable for this project's licence stance is the owner's call (UNVERIFIED).

Recommended shape (for the Architecture document to place): a plain Python module or CSV per standard with columns `standard, edition, table, row_key, symbol, value, clause_or_figure`; one test per row asserting the cell against an independent source of the same edition; `calc.py` reads it, `model.py` never does. Cross-check with the two CSVs in a helper only to find disagreement, and treat every disagreement as "go read the standard".

Spot values read from the previews (for the first row tests): ISO 4017:2022 M6 P 1, k nom 4 (max 4.15, min 3.85), s 10 (min 9.78), e min 11.05, dw min 8.88; ISO 4014:2022 M6 b ref 18 (M8 22, M10 26, M12 30, for l nom <= 125 mm); ISO 4032:2023 M6 m max 5.20 (min 4.90), mw min 3.92, s 10 (min 9.78), e min 11.05, dw min 8.88, da 6.00 to 6.75.

### Standard editions (what the brief should now say)

| Standard | Edition in force | What changed / notes | Tag |
|----------|------------------|----------------------|-----|
| ISO 4014 hexagon head bolts, grades A and B | **ISO 4014:2022** (ed. 5, June 2022); 2011 edition withdrawn 2022-06-28 | M1.6 to M64; M7 appears (bracketed, non-preferred) in the tables; thread length `b` is a "ref." value (M6 18) | ISO-PREVIEW |
| ISO 4017 hexagon head screws, grades A and B | **ISO 4017:2022** (ed. 6, June 2022); 2014 edition withdrawn 2022-06-28 | M1.6 to M64; greatest length min(10 d, 200 mm) | ISO-PREVIEW |
| ISO 4032 hexagon regular nuts (style 1) | **ISO 4032:2023** (ed. 5, 2023-08-21); 2012 edition withdrawn 2023 | **Normative scope M5 to M39.** Nuts D < M5 and D > M39 moved to **informative Annex A, "Historical nuts ... not conforming to ISO 898-2 nor ISO 3506-2"**; M7 added; thread tolerance class 6H via ISO 965-1 | ISO-PREVIEW |
| ISO 4762 hexagon socket head cap screws | ISO 4762:2004 (ed. 4); shown as confirmed in a 2023 review, no newer edition found | Not read; release two | SNIPPET |
| ISO 68-1 basic and design profiles | **ISO 68-1:2023** (ed. 2, 2023-10), replaces 1998 incl. Amd 1:2020 | Adds "design profiles": external thread minor `d3`, height `h3`, full root radius `R`, root-corner radius `R1`. Basic profile unchanged: H = 0.866 025 404 P, H1 = 5H/8 = 0.541 265 877 P | ISO-PREVIEW (clause 5); Clause 6 not visible |
| ISO 261 general plan | ISO 261:1998 (ed. 2), no newer edition found | | SNIPPET |
| ISO 262 selected sizes | ISO 262:2023 (ed. 3, April 2023), range 1 to 100 mm | | SNIPPET |
| ISO 724 basic dimensions | A 2023 edition is reported | | SNIPPET, UNVERIFIED |
| ISO 965-1 tolerances | ISO 965-1:2013 | Source of 6g / 6H numbers. Values not read | SNIPPET, values UNVERIFIED |
| ISO 4759-1 | ISO 4759-1:2000 | Product-grade tolerances (A, B, C) for heads, shanks, lengths. **Not** the source of 6g/6H; the brief's "965/4759" resolves to 965-1 for thread tolerance numbers | SNIPPET / ISO-PREVIEW (cited as a normative reference of 4014/4017/4032) |

Two consequences for the roadmap: **M2-M4 nuts have no normative ISO 4032 text** (M2 to M4 is the range an FDM user prints most), so "M2-M20 for every table" needs an owner decision (cite informative Annex A, cite the withdrawn 2012 edition, or start nuts at M5); and **the 2022/2023 editions carry M7**, bracketed "non-preferred" in the tables, so v1 can skip it without citing an omission.

## Installation

```bash
# Core: nothing new. The kernel pair stays exactly as pinned (L06).
#   cadquery==2.8.0
#   cadquery-ocp==7.9.3.1.1      (OCP imports used: BRepOffsetAPI, BRepBuilderAPI, TopoDS, GProp, BRepGProp, BRepMesh, IMeshTools)

# Supporting: none
# Dev: none new
```

Do not add `cq_warehouse`, `bd_warehouse` or `build123d` to `pyproject.toml` or `requirements.txt`.

## Alternatives Considered

| Recommended | Alternative | When to use the alternative |
|-------------|-------------|-----------------------------|
| Twist section + sewn 5-turn segments | `cq_warehouse` ruled tooth + core fuse | Only if a spike shows STL size (not build time) is the binding constraint and its fuse can be made robust on the full grid. Its 10-40x lighter meshes are real. Copy the idea (ruled surfaces between helix edges), not the package |
| Twist section + sewn 5-turn segments | `bd_warehouse` loft loops | Only on an OCP 8 / build123d stack, which is a different L01. Its `manufacturing_compensation` (radial shift for vertically printed FDM threads) and `interference` (overlap into the core) are worth copying as concepts |
| Closed-form volume for the info panel | `BRepGProp` with `eps=1e-7` | When the shape is not a plain thread (a head with a socket), where no closed form exists. 0.8 s |
| 2D section check for the pair | 3D `intersect` | In CI on a few sizes and a few clearances; not per request |
| One pipe (single B-spline face) | Sewn segments | Never for output; fine only inside a probe |
| Hand-entered clause-cited tables | A package of tables | None exists |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `cq_warehouse` as a dependency | Not on PyPI; git-only; unmaintained since 2024-01; 21 open issues; fuse cost about quadratic in turns, about 7 % hard failures on M2-M20; uncited tables, wrong against current ISO | Own thread engine; keep `cq_warehouse` as reference reading and a differential oracle |
| `build123d`, `bd_warehouse` in this environment | build123d 0.13.0 requires `cadquery-ocp-novtk >=8.0,<8.1`; cadquery 2.8.0 requires `cadquery-ocp <8.0`. A dry-run `pip install build123d` into the pinned venv resolves `cadquery-ocp-novtk 8.0.1.0.0` and `cadquery-ocp-proxy 8.0.1.0.0` next to the pinned `cadquery-ocp 7.9.3.1.1`; both distributions ship a top-level `OCP/` package (742 files in the novtk RECORD), so they overwrite one another. Its fasteners are Compounds of overlapping solids | Nothing; a build123d move is a superseding decision to L01 |
| `Workplane.sweep(helix)` then `fuse` with a core | 35 % hard failures; 35 of 139 configurations silently wrong with `isValid() == True` | The twist construction |
| `Workplane.twistExtrude` / `Solid.extrudeLinearWithRotation` as shipped | `Standard_Failure` from 60-100 turns depending on size | `BRepOffsetAPI_MakePipeShell` with `SetMaxSegments(500)` |
| One twist solid longer than about 20 turns for output | Inverts silently above 100 turns (3 / 27); meshes about 10 000 triangles per turn | 5-turn sewn segments |
| `isValid()` as the acceptance test | Passes inverted solids, solids missing their core, and 2-solid results | Volume vs closed form (with sign), solid count, a timeout |
| `Shape.Volume()` for a printed number | +1.1e-3 on a 150-turn thread | Closed form, or `BRepGProp` with `eps <= 1e-6` |
| `ControlSurfaceDeflection=False` for STL download | Nut volume +5 to +6 %: the mesh closes the clearance | Default meshing at a deflection well under the clearance |
| `bolt.intersect(nut)` on full bodies as the per-request mating proof | 3.6-121 s and degenerate as clearance tends to 0 | 2D section cut at serve time; 3D intersect on a short engaged piece in CI |
| `cq_warehouse`/`bd_warehouse` CSVs as table data | No clause, edition or source; 0/15 ISO 4017 k values match the current standard | Hand-entered, cited rows |
| `4759` as the source of 6g/6H | ISO 4759-1 is product-grade tolerances | ISO 965-1 (values to be read from the standard) |

## Stack Patterns by Variant

**If the info panel prints a volume or mass:** compute it from the closed form (thread) plus a precise `BRepGProp` estimate (head), and assert both agree with the kernel in a test. A figure that is only "what the kernel said" is exactly the number L08 forbids.

**If the owner wants the ISO 68-1:2023 design profile (rounded external root, `d3`, `R`):** same engine. The section outline gets a root arc of radius R tangent to the flanks instead of the flat root; flank and root samples are the only change. The formulas for `R`, `h3`, `d3` are in Clause 6, which the preview does not show (UNVERIFIED). A rounded root also lowers the minor diameter below the basic-profile `d1` the reference code uses.

**If a thread length goes beyond 10 d (user-edited `thread_length`):** supported by the construction (valid to 250 turns, MEASURED); the cap is a product and timeout decision, written from a recorded bench run (PROJECT.md constraint).

**If left-hand:** pass `lefthand=True` to the auxiliary helix; do not mirror a right-hand solid (a mirror flips orientation). MEASURED: crest at -90 degrees at z = P/4.

**If the tip needs the ISO 4753 chamfered end:** one planar/conical intersect on the finished shank (0.17-0.43 s). If it ever dominates, build the last two turns as their own segment and chamfer only that. UNVERIFIED as measured.

**If STL size is unacceptable after the spike:** (1) serve a coarse viewer-only mesh (`ControlSurfaceDeflection=False`), keep the download fine; (2) shrink K; (3) an analytic mesher generated from the same outline. All three are a spike decision, not a default.

**Where the code goes (import-linter fit):** `calc.py` owns the profile numbers (H, 5H/8, the closed-form area, table lookups) with no kernel import; `model.py` owns `section`, `twist`, `thread`, and the only `cadquery`/`OCP` imports; tests compare `model` volume against `calc` area times length.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `cadquery 2.8.0` (2026-06-21) | `cadquery-ocp >=7.9.3.1, <8.0`, Python `>=3.11` | SOURCE (PyPI). L01's 3.12-only ceiling is about wheels for `cadquery-ocp` |
| `cadquery-ocp 7.9.3.1.1` | `cadquery 2.8.0` | The measured pair. Latest `cadquery-ocp` on PyPI is `8.0.1.0.0` (2026-09-05), which cadquery 2.8.0 excludes |
| CadQuery master | `ocp=8.0.1.0` in `environment.yml` | SOURCE. A cadquery release that moves to OCP 8 is likely; timing UNVERIFIED. Treat the kernel bump as a re-measure event: every number here is on OCP 7.9.3.1.1 (the pipe step was reproduced on 8.0.1, nothing else) |
| `build123d 0.13.0` (2026-09-21) | `cadquery-ocp-novtk >=8.0,<8.1`, Python `>=3.11,<3.15` | Incompatible with the pinned pair (see What NOT to Use) |
| `bd_warehouse 0.3.0` (2026-07-12) | `build123d >=0.11.1`; repo pushed 2026-09-21 ("Updated to support build123d v0.13.0 - OCP 8.0.1") | Apache-2.0, active |
| `cq_warehouse 0.8.0` | any cadquery that still has `Solid`, `Wire.makeHelix`; ran on 2.8.0 | Not on PyPI |
| mypy strict, `disallow_any_explicit` | OCP calls | `OCP.*` needs `ignore_missing_imports` (no stubs; already in screw's `pyproject.toml`); with it, the reference code is clean. A `lambda` and `.val()` needed a `def` and an `isinstance` narrow. MEASURED |

## Gaps and things this document did not measure

- **linux/amd64 and the Docker image:** every number is macOS arm64. Re-sweep in the image (L07). The kernel pair and the sewing tolerance are the likeliest things to behave differently.
- **Mesh targets vs the clearance default:** the STL deflection must be a fraction of the clearance, and the clearance comes from a printed test. Not set here.
- **A printed pair:** nothing here proves two parts thread by hand. The kernel proof (2D section, 3D intersect) is necessary, not sufficient (PROJECT.md's own warning).
- **Other CAD importers:** only OCCT readers (OCP 7.9 and 8.0.1) were tried on the STEP.
- **Design profile (rounded root) and ISO 965-1 6g/6H values:** not read; Clause 6 of ISO 68-1:2023 and the 965-1 tables are behind the paywall beyond the previews.
- **ISO 4762:2004, ISO 261, ISO 262, ISO 724, ISO 965-1:** edition status from search snippets only.
- **ISO length-range "stepped lines" per size** in 4014/4017 tables are lost in text extraction: read them from the page image before entering length ranges.
- **Heads and ISO chamfers:** the bolts timed here use a plain hex prism with a cone chamfer, not ISO-exact head geometry (across-corners, washer face `dw`, `kw`). Head cost is expected to be small next to the thread, but it is not measured.
- **Not researched here (other documents):** FDM practice (clearance, minimum pitch), STEP cosmetic-vs-modelled convention, DIN 933/931/934/912 mapping.
- **Contradiction to flag, not resolve:** `cq_warehouse`'s own docstring says sweep and extrude-with-rotation were slower and less reliable (2021); here the extrude-with-rotation family, with `SetMaxSegments` raised and segmented, was the most robust. Different kernel versions and a different end goal (tooth vs whole thread) are the likely reason; nothing was done to test that.

## Sources

- PyPI JSON (SOURCE): `cadquery 2.8.0`, `cadquery-ocp 8.0.1.0.0`, `build123d 0.13.0`, `bd-warehouse 0.3.0`; 404 for `cq_warehouse`.
- GitHub API and raw files (SOURCE): `gumyr/cq_warehouse` (`thread.py`, `fastener.py`, `setup.cfg`, CSVs, issues #86 #87, commits); `gumyr/bd_warehouse` (`thread.py`, `fastener.py`, CSVs, commits, issues #23 #63); `CadQuery/cadquery` (`environment.yml`, releases); `boltsparts/BOLTS` (`data/hex.blt`, licence, last commit).
- Run in this session (MEASURED): scratch venvs with `cadquery 2.8.0 + cadquery-ocp 7.9.3.1.1 + cq_warehouse@dev` and with `bd_warehouse 0.3.0 + build123d 0.13.0 + OCP 8.0.1`; harnesses for the grid (one subprocess per cell), mesh/STEP size, volume accuracy, interference, and the reference code above.
- ISO previews (ISO-PREVIEW), iTeh standards: ISO 4017:2022 (`cdn.standards.iteh.ai/samples/72585/.../ISO-4017-2022.pdf`), ISO 4014:2022 (`.../samples/72579/.../ISO-4014-2022.pdf`), ISO 4032:2023 (`.../samples/75016/.../ISO-4032-2023.pdf`), ISO 68-1:2023 (`.../samples/85107/.../ISO-68-1-2023.pdf`). `iso.org` pages returned HTTP 403 to the fetch tool.
- Search snippets (SNIPPET, LOW tier): ISO store / standards-store pages for edition status of ISO 4014, 4017, 4032, 4762, 261, 262, 68-1, 965-1, 4759-1.
- cq_warehouse docs, thread end-finish timings: `docs/thread.rst` in the repository (SOURCE).

---
*Stack research for: parametric ISO metric threaded fasteners (CadQuery/OpenCascade)*
*Researched: 2026-10-05*
