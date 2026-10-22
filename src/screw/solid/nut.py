"""The nut kind's solid: a hex prism less the L11 thread void, both built from the model's fields.

The prism is `s` across flats and `m` high on z = 0..m; the void is the same helical construction
the bolt's thread uses, grown by the radial clearance and overshooting both faces. Each face then
gets a lead-in countersink and a corner chamfer (`finish`), the cutters built from the fields
`d`, `pitch`, `clearance`, `s` and `m` alone, never from a table row (D-12): an off-row nut has the
same ends as one on a row. The models are named in `screw.calc.thread` (R3, R4, R5, L15).
"""

from __future__ import annotations

import math
from collections.abc import Iterator

import cadquery as cq

from screw.calc.thread import (
    CHAMFER_ANGLE_DEG,
    COUNTERSINK_HALF_ANGLE_DEG,
    countersink_face_radius,
    end_depths,
    thread_depth,
)
from screw.params import NutParams
from screw.solid import bolt, helical

# How far below the void's root radius a full-depth countersink cone goes on, as a fraction of the
# thread depth. A cone that ends exactly on the root surface grazes it: the end-cut probe
# (`bench/RESULTS.md`, End-cut probe) left 8 open preview edges on M6 right and 9 on M6 left
# (4 and 752 on the fine mesh) where a cone 0.3 thread depths past the root left 0. Nothing is
# lost by going on: inside the root radius the whole disc is void.
CROSS_FRACTION = 0.3

# How far the cutters reach past the face, mm: a cut that stopped on the face would leave a
# zero-thickness skin there (RESEARCH P11, as the void's own overshoot).
PAST_FACE = 1.0


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


def _revolved(profile: list[tuple[float, float]]) -> cq.Solid:
    """A solid of revolution about Z; the profile is (radius, z) points of a closed polygon."""
    return bolt._solid(cq.Workplane("XZ").polyline(profile).close().revolve(
        360, (0, 0, 0), (0, 1, 0)).val(), "end cutter")


def _inward(p: NutParams, z_face: float) -> float:
    """+1 when the nut lies above `z_face` (the bottom face), -1 when it lies below (the top)."""
    return 1.0 if z_face < p.m / 2 else -1.0


def countersink_inner_radius(p: NutParams, depth: float) -> float:
    """The radius where the countersink cutter ends: the cone's own radius at `depth` when that
    is still outside the void's root radius (a capped depth, R5: the cutter stops there), else
    `CROSS_FRACTION` thread depths below the root radius, so the cone crosses the root surface and
    never grazes it (RESEARCH F8, P7)."""
    root = p.d / 2 - thread_depth(p.pitch) + p.clearance
    at_depth = countersink_face_radius(p.d) - depth * math.tan(
        math.radians(COUNTERSINK_HALF_ANGLE_DEG))
    # 1e-9 mm: the full depth is (face - root) / tan(45 deg) and lands on the root to a rounding
    # error, which must count as reaching it.
    return at_depth if at_depth > root + 1e-9 else root - CROSS_FRACTION * thread_depth(p.pitch)


def countersink(p: NutParams, z_face: float, depth: float) -> cq.Solid:
    """The cutter of the lead-in countersink on the face at `z_face`: the cone opening to
    `countersink_face_radius` on the face, past the face by `PAST_FACE`, ending at
    `countersink_inner_radius`. `depth` is what `end_depths` returns."""
    tan_half = math.tan(math.radians(COUNTERSINK_HALF_ANGLE_DEG))
    face = countersink_face_radius(p.d)
    inner = countersink_inner_radius(p, depth)
    sign = _inward(p, z_face)
    low = z_face + sign * (face - inner) / tan_half
    return _revolved([(0, z_face - sign * PAST_FACE),
                      (face + PAST_FACE * tan_half, z_face - sign * PAST_FACE),
                      (inner, low), (0, low)])


def face_chamfer(p: NutParams, z_face: float, depth: float) -> cq.Solid:
    """The cutter of the corner chamfer on the face at `z_face`: the cone from the inscribed
    radius s / 2 at `CHAMFER_ANGLE_DEG`, cut off flat at `depth` (the capped shape the oracle
    integrates, `face_chamfer_volume`), reaching past the corners and the face."""
    tan_beta = math.tan(math.radians(CHAMFER_ANGLE_DEG))
    r0 = p.s / 2
    outer = r0 / math.cos(math.pi / 6) + PAST_FACE
    sign = _inward(p, z_face)
    # How far the cutter reaches past the face, mm. A fixed 0.5 put the profile's first point at
    # r0 - 0.5 / tan 30 deg = s / 2 - 0.866 mm, which is negative below s = sqrt(3) mm = 1.732: the
    # kernel refused those valid nuts with `Standard_Failure` (plan 05-20 RED run: s 1.5, 1.7 and
    # 1.11 at d 1, pitch 0.25, m 1, c 0.05; the planner's probe saw 1.5, 1.7 and 1.732 fail and
    # 1.7321 build). Capping it at half r0 tan 30 deg keeps that radius at r0 / 2 or more. The
    # overshoot lies outside the nut, so it removes nothing and `face_chamfer_volume` does not see
    # it; from s = 2 sqrt(3) mm up (every catalogue nut) it is the old 0.5 mm exactly.
    overshoot = min(0.5, r0 * tan_beta / 2)
    below = z_face - sign * overshoot
    flat = z_face + sign * depth
    return _revolved([(r0 - overshoot / tan_beta, below), (outer, below),
                      (outer, flat), (r0 + depth / tan_beta, flat)])


def finish(p: NutParams, body: cq.Shape) -> Iterator[tuple[str, cq.Shape]]:
    """Cut the countersinks and then the chamfers from `body`, one face at a time, yielding the
    piece's name and the nut after that cut so the builder can judge each against its oracle.

    The depths are `end_depths`' (R5 caps them; a countersink that cannot cross the void is left
    out and yields nothing). Both ends of the nut are cut whatever the hand: the section is the
    same at every z, so the oracles do not depend on where the helix is on a face.
    """
    csk, chamfer, _ = end_depths(p.d, p.pitch, p.clearance, p.s, p.m)
    faces = (0.0, p.m)
    if csk > 0:
        for z_face in faces:
            body = body.cut(countersink(p, z_face, csk))
            yield "lead-in countersink", body
    for z_face in faces:
        body = body.cut(face_chamfer(p, z_face, chamfer))
        yield "face chamfer", body
