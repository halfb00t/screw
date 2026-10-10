"""The controls and evidence around the shipped thread builder (kernel module, worker only).

The builder itself (`section`, `twist`, `thread` and its three registered constants) moved to
`screw/solid/helical.py` in Phase 3 and is imported back below, so the spike measures what
ships (02 D-18, D-13). What stays here is what only the spike needs: the known-bad controls
(`naive_sweep_fuse`, `one_pipe`), the tip trim and the ruled-surface reference.

Vendor types stop here: callers get a `cq.Solid`, and the worker turns it into plain numbers.
"""

from __future__ import annotations

import importlib
import math
from operator import attrgetter

import cadquery as cq

from bench.thread_spike.maths import RULED_MODULE, thread_depth
from screw.solid.helical import MAX_SEGMENTS as MAX_SEGMENTS
from screw.solid.helical import SECTION_SAMPLES as SECTION_SAMPLES
from screw.solid.helical import SEWING_TOLERANCE as SEWING_TOLERANCE
from screw.solid.helical import section as section
from screw.solid.helical import thread as thread
from screw.solid.helical import twist


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
    return twist(d, pitch, turns * pitch, 0.0, left_hand)


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
