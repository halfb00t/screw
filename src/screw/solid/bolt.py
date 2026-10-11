"""The bolt kind's solid: the L11 thread from the tip at z = 0, a plain shank from 04-04, and a
plain hex prism head with sharp corners on top.

Both thread ends are plain planar cuts and there is no fillet or chamfer (D-01, D-02, 03 D-16):
an end treatment waits for ISO 4753, which is unread (L02).
"""

from __future__ import annotations

import cadquery as cq

from screw.build_errors import BuildError
from screw.calc.thread import MIN_TAIL_MM, built_thread_length
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


def assemble(p: BoltParams, thread: cq.Solid) -> cq.Shape:
    """The plain shank of diameter d from the thread's end t to the length, then the hex head, a
    prism of across-flats s and height k on z length..length + k, fused onto the thread."""
    # circumscribed=True makes the polygon's diameter the across-flats width: without it the
    # diameter is across corners and the prism is 0.75 of its closed form (RESEARCH Pitfall 1).
    head = cq.Workplane("XY").workplane(offset=p.length).polygon(
        6, p.s, circumscribed=True).extrude(p.k).val()
    assert isinstance(head, cq.Solid)  # a Workplane.val() is a Shape; extrude of a face is a Solid
    t = built_thread_length(p.thread_length, p.length)
    if p.length > t:
        # A planar fuse at the thread's plain end (D-03), never a cylinder over the thread: the
        # shank starts on the face the thread already ends in.
        shank = cq.Workplane("XY").workplane(offset=t).circle(p.d / 2).extrude(p.length - t).val()
        assert isinstance(shank, cq.Solid)
        body: cq.Shape = thread.fuse(shank)
    else:
        body = thread
    # No clean(): Shape.fuse takes none, and the D-03 probe (bench/RESULTS.md "Head fuse probe")
    # saw the same single valid solid either way.
    return body.fuse(head)
