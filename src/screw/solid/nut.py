"""The nut kind's solid: a hex prism less the L11 thread void, both built from the model's fields.

The prism is `s` across flats and `m` high on z = 0..m; the void is the same helical construction
the bolt's thread uses, grown by the radial clearance and overshooting both faces. The ends are
plain planar cuts: the lead-in countersink and the face chamfer wait for plan 05-13 (L02).
"""

from __future__ import annotations

import cadquery as cq

from screw.params import NutParams
from screw.solid import bolt, helical


def void(p: NutParams) -> cq.Solid:
    """The thread void: the helical solid of radial clearance `p.clearance`, z = -pitch..m + pitch.

    It is `m + 2 * pitch` long and shifted down by one pitch so it overshoots both faces by a
    pitch (RESEARCH P11): a cut that stopped on a face would leave a zero-thickness skin there.
    """
    return helical.thread(p.d, p.pitch, p.m + 2 * p.pitch, clearance=p.clearance,
                          left_hand=p.left_hand).translate(cq.Vector(0, 0, -p.pitch))


def assemble(p: NutParams, void: cq.Solid) -> cq.Shape:
    """The hex prism of across-flats `p.s` and height `p.m` with `void` cut out of it."""
    # circumscribed=True makes the polygon's diameter the across-flats width: without it the
    # diameter is across corners and the prism is 0.75 of its closed form (RESEARCH Pitfall 1).
    prism = bolt._solid(cq.Workplane("XY").polygon(6, p.s, circumscribed=True).extrude(p.m).val(),
                        "nut")
    return prism.cut(void)
