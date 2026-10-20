"""The bolt kind's solid: the L11 thread from the tip at z = 0, a plain shank from 04-04, and a
plain hex prism head with sharp corners on top.

The tip is one cone cut on the bare thread (`tip_cut`, the ISO tip end read from GOST 12414-94,
stated model, L14, read 6), and a bolt on a cited ISO 4014 row with a long enough plain shank
gets a fillet ring revolved at the shank/head junction (`add_fillet`, R1, D-11). The ring is
built by revolving a profile and fused, never an OCCT fillet: its volume is then an exact
closed form the gate can judge. The head keeps its sharp corners (the nut's chamfers are 05-13).
"""

from __future__ import annotations

import math

import cadquery as cq

from screw.build_errors import BuildError
from screw.calc.thread import MIN_TAIL_MM, TIP_ANGLE_DEG, built_thread_length, thread_depth
from screw.params import BoltParams
from screw.solid import helical


def thread(p: BoltParams) -> cq.Solid:
    """The ISO 68-1:2023 basic-profile thread of major diameter d, axis +Z from the tip at z=0
    to the built thread length t, right- or left-hand as asked."""
    t = built_thread_length(p.thread_length, p.length)
    if not t >= MIN_TAIL_MM:  # NaN-safe, like helical's own guard
        # helical.thread refuses the same value but names only `length`, which would send the
        # user to the wrong field when the short value is the thread (RESEARCH Alert 6).
        raise BuildError(f"thread_length and length: the thread built here is {t:g} mm, shorter "
                         f"than the {MIN_TAIL_MM:g} mm the builder can model.")
    return helical.thread(p.d, p.pitch, t, left_hand=p.left_hand)


def _solid(made: object, what: str) -> cq.Solid:
    """The Solid an extrude leaves on a workplane (`val()` is typed as the union of everything a
    workplane can hold). Anything else is a kernel failure, refused like the gate refuses one and
    never asserted: `python -O` strips an assert and would let the fuse run on it (04-REVIEW IN-01).
    """
    if not isinstance(made, cq.Solid):
        raise BuildError(f"Geometry kernel produced {type(made).__name__} for the {what}, "
                         "expected a solid.")
    return made


def tip_cut(p: BoltParams, bare: cq.Solid) -> cq.Solid:
    """The bare thread cut by the tip cone at z = 0: the thread intersected with a revolved
    envelope that leaves the cone (the `2026-10-08-a-trim` recipe the end-cut probe used).

    The cone meets the end face at the minor radius and rises at `TIP_ANGLE_DEG` from the face;
    the envelope reaches a millimetre past the crest and past the thread's far end, so it shares
    no face with the thread except the end plane the probe measured.
    """
    t = built_thread_length(p.thread_length, p.length)
    minor = p.d / 2 - thread_depth(p.pitch)
    outer = p.d / 2 + 1.0
    run = (outer - minor) * math.tan(math.radians(TIP_ANGLE_DEG))
    top = t + 1.0
    envelope = _solid(cq.Workplane("XZ").polyline(
        [(0, top), (outer, top), (outer, run), (minor, 0.0), (0, 0.0)]
    ).close().revolve(360, (0, 0, 0), (0, 1, 0)).val(), "tip envelope")
    solids = bare.intersect(envelope).Solids()
    if len(solids) != 1:
        raise BuildError(f"Geometry kernel produced {len(solids)} solids from the tip cut for "
                         "these parameters, expected exactly 1.")
    return solids[0]


def fillet_ring(p: BoltParams, r: float) -> cq.Solid:
    """The quarter-circle ring of radius `r` under the head: the region of area r^2 (1 - pi/4)
    between the shank (radius d/2), the head's underside z = length and the arc centred at
    (d/2 + r, length - r), revolved about the axis. It shares the shank cylinder and the underside
    plane, so it fuses onto both."""
    root = p.d / 2
    mid = r / math.sqrt(2)
    return _solid(cq.Workplane("XZ").moveTo(root, p.length).lineTo(root + r, p.length)
                  .threePointArc((root + r - mid, p.length - r + mid), (root, p.length - r))
                  .close().revolve(360, (0, 0, 0), (0, 1, 0)).val(), "fillet ring")


def add_fillet(p: BoltParams, part: cq.Shape, r: float) -> cq.Shape:
    """`part` (the assembled bolt) with the fillet ring of radius `r` fused under the head."""
    return part.fuse(fillet_ring(p, r))


def assemble(p: BoltParams, bare_thread: cq.Solid) -> cq.Shape:
    """The plain shank of diameter d from the thread's end t to the length, then the hex head, a
    prism of across-flats s and height k on z length..length + k, fused onto `bare_thread`
    (what `thread()` built; named so it does not shadow that function, 04-REVIEW IN-04)."""
    # circumscribed=True makes the polygon's diameter the across-flats width: without it the
    # diameter is across corners and the prism is 0.75 of its closed form (RESEARCH Pitfall 1).
    head = _solid(cq.Workplane("XY").workplane(offset=p.length).polygon(
        6, p.s, circumscribed=True).extrude(p.k).val(), "head")
    t = built_thread_length(p.thread_length, p.length)
    if p.length > t:
        # A planar fuse at the thread's plain end (D-03), never a cylinder over the thread: the
        # shank starts on the face the thread already ends in.
        shank = _solid(cq.Workplane("XY").workplane(offset=t).circle(p.d / 2).extrude(
            p.length - t).val(), "shank")
        body: cq.Shape = bare_thread.fuse(shank)
    else:
        body = bare_thread
    # No clean(): Shape.fuse takes none, and the D-03 probe (bench/RESULTS.md "Head fuse probe")
    # saw the same single valid solid either way.
    return body.fuse(head)
