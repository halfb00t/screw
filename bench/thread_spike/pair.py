"""The pair check Phase 5 will own: a nut against a rod piece, read at placed poses (kernel module).

Shaped like the future `screw/solid` pair check (D-18), so what was measured is what ships.
Vendor types stop here: callers hand in and get back `cq.Solid` and plain numbers, and the
worker turns those into a record. It measures; whether a reading proves anything is decided in
the parent by `verdict.cell_verdict`, against a closed form this process never sees.

A pair is a rod piece, the thread at clearance 0 over m + 2P from z = -P, and a nut, a plain
cylinder of radius d and height m (the hex adds nothing to a thread proof and its dimensions
would be invented, D-13) less the void thread over the same span. Poses are screw motions, so
every matched pose is the same physical configuration with the seam moved (RESEARCH Pattern 5).
"""

from __future__ import annotations

import math
import time
from fractions import Fraction

import cadquery as cq
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.TopTools import TopTools_ListOfShape

from bench.thread_spike import helical, measure

# The boolean and its filler are kept for the life of the process: freeing them segfaulted at
# teardown (exit 139, RESEARCH Pitfall 4, provoked once), which is also why the worker ends with
# `os._exit(0)` after flushing.
_KEEP: list[object] = []


def _turns(pitch: float, m: float) -> float:
    """Turns in the m + 2P span, exactly: a float division of floats drifts (168 of 3000 products
    fail (k * P) / P == k, RESEARCH Pitfall 1), and `str` of a float is its shortest round trip."""
    p = Fraction(str(pitch))
    return float((Fraction(str(m)) + 2 * p) / p)


def rod_piece(d: float, pitch: float, m: float, left_hand: bool, k: int) -> cq.Solid:
    """The rod over z in [-P, m + P]: a pad of one pitch each side covers every placed nut as
    long as a pose slides it by no more than P (RESEARCH Pitfall 2)."""
    rod = helical.thread(d, pitch, _turns(pitch, m), clearance=0.0, left_hand=left_hand, k=k)
    return rod.translate(cq.Vector(0, 0, -pitch))


def nut(d: float, pitch: float, m: float, clearance: float, left_hand: bool,
        k: int) -> cq.Solid:
    """A plain blank of radius d and height m over z in [0, m], less the void thread of this
    clearance through all of it. One solid or a raised error: a nut body in pieces is a defect of
    the build, and its volume would not be the closed form's."""
    void = helical.thread(d, pitch, _turns(pitch, m), clearance=clearance, left_hand=left_hand,
                          k=k).translate(cq.Vector(0, 0, -pitch))
    solids = cq.Solid.makeCylinder(d, m).cut(void).Solids()
    if len(solids) != 1:
        raise ValueError(f"the nut body has {len(solids)} solids, not 1")
    return solids[0]


def place(blank: cq.Solid, theta: float, offset_pitches: float, pitch: float,
          left_hand: bool) -> cq.Solid:
    """The nut turned by `theta` about z and slid by sign * theta * P / 2 pi (sign -1 for left
    hand: a left-hand thread advances the other way) plus `offset_pitches` pitches. The screw
    motion keeps a matched pose physically identical; half a pitch more is the control."""
    sign = -1.0 if left_hand else 1.0
    slide = sign * theta * pitch / (2 * math.pi) + offset_pitches * pitch
    turned = blank.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), math.degrees(theta))
    return turned.translate(cq.Vector(0, 0, slide))


def check_cover(rod: cq.Shape, placed: cq.Shape) -> None:
    """Raise unless the rod's z range covers the placed nut's. A nut hanging off the rod shrinks
    the engaged length and the control reads below its closed form, silently, so a violated
    cover is a defect of this harness, never a measurement."""
    rod_box, nut_box = rod.BoundingBox(), placed.BoundingBox()
    if rod_box.zmin > nut_box.zmin or rod_box.zmax < nut_box.zmax:
        raise ValueError(
            f"the rod covers z in [{rod_box.zmin:.4f}, {rod_box.zmax:.4f}] but the placed nut "
            f"spans [{nut_box.zmin:.4f}, {nut_box.zmax:.4f}]: the pose slides past the pad")


def common(a: cq.Shape, b: cq.Shape) -> tuple[float, int, bool, bool, float]:
    """The boolean intersection of `a` and `b`: (precise volume, solid count, filler had errors,
    filler had warnings, seconds). An empty result has volume 0.0 and 0 solids.

    The two flags are columns for the reader and never a verdict input: in research they were
    False on every false-empty control (RESEARCH Pitfall 4).
    """
    t0 = time.perf_counter()
    op = BRepAlgoAPI_Common()
    first, second = TopTools_ListOfShape(), TopTools_ListOfShape()
    first.Append(a.wrapped)
    second.Append(b.wrapped)
    op.SetArguments(first)
    op.SetTools(second)
    op.Build()
    filler = op.DSFiller()
    _KEEP.append((op, filler))
    shape = op.Shape()
    solids = [] if shape.IsNull() else cq.Shape.cast(shape).Solids()
    volume = measure.precise_volume(cq.Shape.cast(shape)) if solids else 0.0
    return (volume, len(solids), bool(filler.HasErrors()), bool(filler.HasWarnings()),
            time.perf_counter() - t0)
