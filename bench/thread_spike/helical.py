"""The sewn-twist thread builder: the construction under test (kernel module, worker only).

Ported from `.planning/research/STACK.md` § Reference implementation, parameterised by the
segment length K (D-07). The solid is the thread itself, with no tooth-to-core boolean: a
transverse section carrying root, flanks and crest is twisted along the axis by one pipe
(`MakePipeShell` with an auxiliary helix), in K-turn segments sewn together. Shaped like the
future `screw/solid/helical.py` (D-18). The ISO 68-1:2023 basic profile is pinned (02-SPIKE.md).

Vendor types stop here: callers get a `cq.Solid`, and the worker turns it into plain numbers.
"""

from __future__ import annotations

import importlib
import math
from operator import attrgetter

import cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakePipeShell
from OCP.TopoDS import TopoDS

from bench.thread_spike.maths import RULED_MODULE, thread_depth

# Spline samples per flank: 14 sits 0.1 um off the ideal Archimedean spiral, 4 gives 7 um
# (STACK, measured).
SECTION_SAMPLES = 14
# The default pipe fails with Standard_Failure from about 80 turns; 500 builds a 250-turn pipe
# (STACK, measured).
MAX_SEGMENTS = 500
# Sewing tolerance in mm (STACK, measured): closes the seams between identical segment ends
# without a boolean. A protocol input, not a tuning knob.
SEWING_TOLERANCE = 1e-4


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


def twist(d: float, pitch: float, turns: float, clearance: float = 0.0,
          left_hand: bool = False) -> cq.Solid:
    """One pipe of `turns` turns, z in [0, turns * pitch]."""
    length = turns * pitch
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


def thread(d: float, pitch: float, turns: float, *, clearance: float = 0.0,
           left_hand: bool = False, k: int = 5) -> cq.Solid:
    """Solid with z in [0, turns * pitch] and no boolean.

    Integer `k`-turn copies of one base twist, translated by i * k * pitch, plus one remainder
    segment when turns - full * k > 0, sewn with `SEWING_TOLERANCE` with the interior seam
    caps left out. `turns` is used exactly as given: it is never re-derived from a float
    length / pitch and carries no epsilon (RESEARCH Pitfall 1: 168 of 3000 float k*P products
    drift), so the caller passes the exact turn count of its grid.
    """
    if turns <= 0:
        raise ValueError(f"turns must be positive, got {turns!r}")
    full = int(turns // k)
    rest = turns - full * k
    end = turns * pitch
    parts: list[tuple[cq.Solid, float, float]] = []
    if full:
        base = twist(d, pitch, k, clearance, left_hand)
        parts += [(base.translate(cq.Vector(0, 0, i * k * pitch)),
                   i * k * pitch, (i + 1) * k * pitch) for i in range(full)]
    if rest > 0:
        z0 = full * k * pitch
        parts.append((twist(d, pitch, rest, clearance, left_hand).translate(cq.Vector(0, 0, z0)),
                      z0, end))
    if len(parts) == 1:
        return parts[0][0]
    sew = BRepBuilderAPI_Sewing(SEWING_TOLERANCE)
    for i, (solid, z0, z1) in enumerate(parts):
        for face in solid.Faces():
            if face.geomType() == "PLANE":
                z = face.Center().z
                if (i > 0 and abs(z - z0) < 1e-7) or (i < len(parts) - 1 and abs(z - z1) < 1e-7):
                    continue  # interior seam cap
            sew.Add(face.wrapped)
    sew.Perform()
    return cq.Solid.makeSolid(cq.Shell(TopoDS.Shell_s(sew.SewedShape())))


def naive_sweep_fuse(d: float, pitch: float, length: float) -> cq.Shape:
    """The negative control: a trapezoid tooth swept along a helix and fused to a core cylinder.

    Kept here as the known-bad input for Phase 3's THRD-04 positive-control test; it is never
    a candidate. Reproduced from RESEARCH Pitfall 9, which measured it: M6 L10 gave one valid
    solid at 0.238 of the closed-form volume, M2 L6 0.274, and M6 L20 and L40 raised
    `Null TopoDS_Shape`. Re-run here, the same recipe gave 0.238, 0.274 and the two exceptions.

    The tooth: crest half-width P/16 at d/2, flanks 30 degrees from the radial, root embedded
    0.05 P inside the core so the fuse has an overlap to bite on. The helix has radius d/2 and
    the tool is L + 2P long, shifted down by P so both ends overrun the core. No trim.
    """
    ro = d / 2
    core_radius = ro - thread_depth(pitch)
    base = core_radius - 0.05 * pitch  # the embedded root: inside the core's surface
    half_base = pitch / 16 + (ro - base) * math.tan(math.radians(30))
    profile = [(base, -half_base), (ro, -pitch / 16), (ro, pitch / 16), (base, half_base)]
    helix = cq.Wire.makeHelix(pitch, length + 2 * pitch, ro)
    tool = (cq.Workplane("XZ").polyline(profile).close()
            .sweep(cq.Workplane(obj=helix), isFrenet=True)
            .translate(cq.Vector(0, 0, -pitch)).val())
    assert isinstance(tool, cq.Shape)
    return cq.Solid.makeCylinder(core_radius, length).fuse(tool)


def one_pipe(d: float, pitch: float, turns: float, left_hand: bool = False) -> cq.Solid:
    """The twisted section in one pipe over all `turns`, no segments: the comparison row for
    the sewn construction (STACK measured 0 failures in 139 builds to 100 turns, and inverted
    solids of volume about -1x at 160-171 turns that still report `isValid()` True)."""
    return twist(d, pitch, turns, 0.0, left_hand)


def trim_tip(rod: cq.Solid, d: float, pitch: float, length: float,
             angle_deg: float) -> cq.Shape:
    """`rod` intersected with a tip envelope: a cylinder of radius d/2 + 1 mm up to where a cone
    frustum starts, the frustum meeting the end face at z = `length` at the minor radius
    d/2 - 5H/8 and widening downward at `angle_deg` measured from the end face.

    Cost evidence for Phase 4 (D-08), not geometry truth: the cone angle is a stated protocol
    input (`maths.TIP_CHAMFER_DEG`, ISO 4753 unread). RESEARCH A2: the probe trimmed valid in
    0.5-0.8 s at six sizes.
    """
    minor = d / 2 - thread_depth(pitch)
    outer = d / 2 + 1.0
    run = (outer - minor) * math.tan(math.radians(angle_deg))  # axial depth of the frustum
    # Local (x, y) of the XZ workplane is (radius, z); revolved about the z axis.
    profile = [(0, -1.0), (outer, -1.0), (outer, length - run), (minor, length), (0, length)]
    envelope = (cq.Workplane("XZ").polyline(profile).close()
                .revolve(360, (0, 0, 0), (0, 1, 0)).val())
    assert isinstance(envelope, cq.Shape)
    return rod.intersect(envelope)


def ruled_reference(d: float, pitch: float, length: float) -> cq.Shape:
    """The ruled-surface reference: `cq_warehouse`'s `IsoThread` fused to a core cylinder of
    its own root radius. End finishes are pre-registered as "fade" (RESEARCH Code Example 8:
    "chamfer" cost about 6x and broke at 80 turns, PITFALLS C1). Its profile is not the pinned
    one, so its ratio to the closed form is not an accuracy claim.

    Everything from the package is held as `object` and narrowed against cadquery types: a
    package that returns something else is a refusal, not a guess (L04).
    """
    module = importlib.import_module(RULED_MODULE)
    factory: object = vars(module)["IsoThread"]
    if not callable(factory):
        raise TypeError(f"{RULED_MODULE}.IsoThread is not callable")
    thread: object = factory(major_diameter=d, pitch=pitch, length=length, external=True,
                             end_finishes=("fade", "fade"))
    root: object = attrgetter("min_radius")(thread)
    if not isinstance(thread, cq.Solid) or not isinstance(root, float):
        raise TypeError("IsoThread did not return a cadquery Solid with a float min_radius")
    return cq.Solid.makeCylinder(root, length).fuse(thread)
