"""The walking-skeleton bolt: a plain unthreaded cylinder (D-04)."""

from __future__ import annotations

import cadquery as cq

from screw.params import BoltParams


def cylinder(p: BoltParams) -> cq.Solid:
    """Diameter d, length `length`, axis +Z from z=0.

    Typed `Solid` (unlike `Workplane.val()`, which is a bare `Shape`). Measured at
    planning: d=1e-9 builds with `isValid()` False, which the doorway's validity check
    turns into a `BuildError`.
    """
    return cq.Solid.makeCylinder(p.d / 2, p.length)
