"""The bolt kind's solid: a threaded rod over its whole length.

No head yet (Phase 4). Both ends are plain planar cuts at z = 0 and z = length: an end treatment
waits for ISO 4753, which is unread (D-16, L02).
"""

from __future__ import annotations

import cadquery as cq

from screw.params import BoltParams
from screw.solid import helical


def rod(p: BoltParams) -> cq.Solid:
    """The ISO 68-1:2023 basic-profile thread of major diameter d, axis +Z from z=0 to length."""
    return helical.thread(p.d, p.pitch, p.length)
