"""The bolt kind's solid: the L11 thread from the tip at z = 0, a plain shank from 04-04, and a
plain hex prism head with sharp corners on top.

Both thread ends are plain planar cuts and there is no fillet or chamfer (D-01, D-02, 03 D-16):
an end treatment waits for ISO 4753, which is unread (L02).
"""

from __future__ import annotations

import cadquery as cq

from screw.params import BoltParams
from screw.solid import helical


def thread(p: BoltParams) -> cq.Solid:
    """The ISO 68-1:2023 basic-profile thread of major diameter d, axis +Z from z=0 to the
    threaded length (the whole length here), right- or left-hand as asked."""
    return helical.thread(p.d, p.pitch, p.length, left_hand=p.left_hand)


def assemble(p: BoltParams, thread: cq.Solid) -> cq.Shape:
    """The hex head, a prism of across-flats s and height k on z length..length + k, fused onto
    the thread."""
    # circumscribed=True makes the polygon's diameter the across-flats width: without it the
    # diameter is across corners and the prism is 0.75 of its closed form (RESEARCH Pitfall 1).
    head = cq.Workplane("XY").workplane(offset=p.length).polygon(
        6, p.s, circumscribed=True).extrude(p.k).val()
    assert isinstance(head, cq.Solid)  # a Workplane.val() is a Shape; extrude of a face is a Solid
    # No clean(): Shape.fuse takes none, and the D-03 probe (bench/RESULTS.md "Head fuse probe")
    # saw the same single valid solid either way.
    return thread.fuse(head)
