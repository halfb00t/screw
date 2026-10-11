"""The one helical builder: the rod, and the void a nut subtracts (kernel module, worker only).

Both are the same solid with a different radial clearance, so both go through `thread`. The
construction is L11's: a transverse section carrying root, flanks and crest is twisted along the
axis by one pipe (`MakePipeShell` with an auxiliary helix), in `k`-turn segments sewn together,
with no tooth-to-core boolean. Moved from `bench/thread_spike/helical.py`, which measured it, so
what ships is what was measured. The ISO 68-1:2023 basic profile is pinned (02-SPIKE.md).

Vendor types stop at `screw.solid`: callers inside it get a `cq.Solid`.
"""

from __future__ import annotations

import math

import cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakePipeShell
from OCP.TopoDS import TopoDS

from screw.build_errors import BuildError
from screw.calc.thread import thread_depth

# Spline samples per flank: 14 sits 0.1 um off the ideal Archimedean spiral, 4 gives 7 um
# (STACK, measured). MEASURED-PRIOR protocol input of L11, not a campaign result.
SECTION_SAMPLES = 14
# The default pipe fails with Standard_Failure from about 80 turns; 500 builds a 250-turn pipe
# (STACK, measured). MEASURED-PRIOR protocol input of L11.
MAX_SEGMENTS = 500
# Sewing tolerance in mm (STACK, measured): closes the seams between identical segment ends
# without a boolean. A protocol input, not a tuning knob. MEASURED-PRIOR protocol input of L11.
SEWING_TOLERANCE = 1e-4
# Segment length in turns: K = 3, selected by the K rule over `2026-10-08-a-ksweep` (L11; all
# three K qualified and K = 3 had the fewest fine triangles at the standard max).
DEFAULT_K = 3
# INTERIM (D-17): the shortest length, or sewn tail, the builder accepts, in mm. Research probe
# 2026-10-10 at d=6, pitch=1: a twist of length <= 1e-8 mm SIGSEGVs the process before any check
# can run, 3e-8 to 1e-6 mm raises, 1e-5 mm builds; as a sewn tail, 1e-5 to 1e-2 mm built one
# valid solid at (6, 1), (2, 0.4) and (20, 2.5). 1e-3 sits 100x above the last failing tail.
# Phase 7 re-measures (OPER-03).
MIN_TAIL_MM = 1e-3


def section(d: float, pitch: float, clearance: float = 0.0) -> cq.Wire:
    """Transverse outline of the basic-profile thread, one start.

    Crest flat P/8 at d/2, root flat P/4 at d/2 - 5H/8, both grown by `clearance`; the flanks
    are Archimedean spirals (radius linear in angle) sampled at `SECTION_SAMPLES` points.
    """
    ro = d / 2 + clearance
    rr = d / 2 - thread_depth(pitch) + clearance
    nf = SECTION_SAMPLES

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


def twist(d: float, pitch: float, length: float, clearance: float = 0.0,
          left_hand: bool = False) -> cq.Solid:
    """One pipe over a spine of `length` mm, z in [0, length]."""
    spine = cq.Wire.assembleEdges([cq.Edge.makeLine(cq.Vector(0, 0, 0), cq.Vector(0, 0, length))])
    # Radius 1 is arbitrary: the auxiliary helix only sets the twist rate.
    aux = cq.Wire.makeHelix(pitch, length, 1, lefthand=left_hand)
    pipe = BRepOffsetAPI_MakePipeShell(spine.wrapped)
    pipe.SetMaxSegments(MAX_SEGMENTS)
    pipe.SetMode(aux.wrapped, False)
    pipe.Add(section(d, pitch, clearance).wrapped)
    pipe.Build()
    pipe.MakeSolid()
    return cq.Solid(pipe.Shape())


def thread(d: float, pitch: float, length: float, *, clearance: float = 0.0,
           left_hand: bool = False, k: int = DEFAULT_K) -> cq.Solid:
    """Solid with z in [0, length], both ends plain planar cuts, and no boolean.

    Integer `k`-turn copies of one base twist, translated by i * k * pitch, plus a last
    segment that always ends at `length` itself. It takes the length in mm, not a turn count:
    130 of 3750 integer-turn rows (15 sizes, 1 to 250 turns) leave a positive float tail below
    `MIN_TAIL_MM`, and (3.5, 0.6, 5.4) leaves 8.9e-16 mm, which SIGSEGVs the kernel (RESEARCH
    Pitfall 1). A tail that short is folded into the previous segment, so the end face still
    sits at `length`. Segments are sewn with `SEWING_TOLERANCE`, interior seam caps left out.
    """
    if not length >= MIN_TAIL_MM:  # NaN-safe: a NaN fails the comparison
        raise BuildError(f"length {length:g} mm is too short to model a thread "
                         f"(smallest length built: {MIN_TAIL_MM:g} mm).")
    segment = k * pitch
    full = int(length // segment)
    folded = full > 0 and length - full * segment < MIN_TAIL_MM
    bases = full - 1 if folded else full  # full segments that are plain copies of one twist
    parts: list[tuple[cq.Solid, float, float]] = []
    if bases:
        base = twist(d, pitch, segment, clearance, left_hand)
        parts += [(base.translate(cq.Vector(0, 0, i * k * pitch)),
                   i * k * pitch, (i + 1) * k * pitch) for i in range(bases)]
    z0 = bases * k * pitch
    parts.append((twist(d, pitch, length - z0, clearance, left_hand).translate(
        cq.Vector(0, 0, z0)), z0, length))
    if len(parts) == 1:
        return parts[0][0]
    sew = BRepBuilderAPI_Sewing(SEWING_TOLERANCE)
    for i, (solid, lo, hi) in enumerate(parts):
        for face in solid.Faces():
            if face.geomType() == "PLANE":
                z = face.Center().z
                if (i > 0 and abs(z - lo) < 1e-7) or (i < len(parts) - 1 and abs(z - hi) < 1e-7):
                    continue  # interior seam cap
            sew.Add(face.wrapped)
    sew.Perform()
    return cq.Solid.makeSolid(cq.Shell(TopoDS.Shell_s(sew.SewedShape())))
