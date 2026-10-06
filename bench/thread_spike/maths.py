"""The thread spike's oracle: the pinned profile's section and its closed-form volume.

Pure maths, free of the CAD kernel: the closed form is what the kernel is judged against, so it
must share no code path with it (an import-linter contract enforces that). Shaped like the
future `screw/calc/thread.py` (D-18).

Profile: ISO 68-1:2023 basic profile, flat crest and flat root, pinned by the owner on
2026-10-06 (02-SPIKE.md, Owner rulings). One-way door: a different profile re-runs the campaign.
Symbols, defined once: `d` major diameter, `P` pitch (`pitch`), `H` fundamental triangle height,
`c` radial clearance, `theta` the angle round the axis.
"""

from __future__ import annotations

import math
from fractions import Fraction

# ISO 262 coarse pitch for the 15 sizes of D-02, as exact fractions so a grid of lengths is
# built without float drift (168 of 3000 float k*P products fail (k*P)/P == k, RESEARCH
# Pitfall 1). name -> (d, P) in mm.
# UNVERIFIED until Phase 4's row tests (D-02). Source: en.wikipedia.org "ISO metric screw
# thread", fetched 2026-10-06 -- a secondary source.
PITCH: dict[str, tuple[Fraction, Fraction]] = {
    "M2": (Fraction(2), Fraction(2, 5)),
    "M2.5": (Fraction(5, 2), Fraction(9, 20)),
    "M3": (Fraction(3), Fraction(1, 2)),
    "M3.5": (Fraction(7, 2), Fraction(3, 5)),
    "M4": (Fraction(4), Fraction(7, 10)),
    "M5": (Fraction(5), Fraction(4, 5)),
    "M6": (Fraction(6), Fraction(1)),
    "M7": (Fraction(7), Fraction(1)),
    "M8": (Fraction(8), Fraction(5, 4)),
    "M10": (Fraction(10), Fraction(3, 2)),
    "M12": (Fraction(12), Fraction(7, 4)),
    "M14": (Fraction(14), Fraction(2)),
    "M16": (Fraction(16), Fraction(2)),
    "M18": (Fraction(18), Fraction(5, 2)),
    "M20": (Fraction(20), Fraction(5, 2)),
}

SIZES: tuple[str, ...] = tuple(PITCH)

# INTERIM (Phase 1 D-01): (linear deflection mm, angular deflection rad), carried from spur
# model.py:53. Equal to `screw.solid.TESSELLATION`; tests/test_bench.py pins the equality so
# this kernel-free module need not import the kernel to read it.
INTERIM_PRESETS: dict[str, tuple[float, float]] = {"preview": (0.08, 0.5), "fine": (0.01, 0.1)}


def fundamental_height(pitch: float) -> float:
    """H = (sqrt(3) / 2) * P, the height of the sharp 60 degree triangle."""
    return math.sqrt(3) / 2 * pitch


def thread_depth(pitch: float) -> float:
    """5H/8: the radial distance from crest flat to root flat of the basic profile."""
    return 5 / 8 * fundamental_height(pitch)


def _radii(d: float, pitch: float, clearance: float) -> tuple[float, float]:
    """(crest radius, root radius) with the radial clearance added to both."""
    return d / 2 + clearance, d / 2 - thread_depth(pitch) + clearance


def section_radius(d: float, pitch: float, clearance: float, theta: float) -> float:
    """Radius of the transverse (z = const) outline at angle `theta`.

    The axial profile wrapped round the axis (theta = 2 pi z / P): crest flat over
    [-pi/8, pi/8] at ro; flank linear in angle to rr over [pi/8, 3pi/4]; root flat over
    [3pi/4, 5pi/4] at rr; flank back over [5pi/4, 15pi/8]. `theta` is taken modulo 2 pi.
    """
    ro, rr = _radii(d, pitch, clearance)
    th = theta % (2 * math.pi)
    if th >= 15 * math.pi / 8:
        th -= 2 * math.pi
    if th <= math.pi / 8:
        return ro
    if th <= 3 * math.pi / 4:
        return ro + (rr - ro) * (th - math.pi / 8) / (5 * math.pi / 8)
    if th <= 5 * math.pi / 4:
        return rr
    return rr + (ro - rr) * (th - 5 * math.pi / 4) / (5 * math.pi / 8)


def section_area(d: float, pitch: float, clearance: float = 0.0) -> float:
    """Area of the transverse section: pi/8 ro^2 + pi/4 rr^2 + 5 pi/24 (ro^2 + ro rr + rr^2).

    Half the integral of r^2 over the angle: the crest spans pi/4, the root pi/2 and each of
    the two flanks 5 pi/8, with r linear in angle across a flank. Re-derived in RESEARCH
    Pattern 2; the kernel agreed to a few 1e-6 on 576 of 576 research rows.
    """
    ro, rr = _radii(d, pitch, clearance)
    return (math.pi / 8 * ro**2 + math.pi / 4 * rr**2
            + 5 * math.pi / 24 * (ro**2 + ro * rr + rr**2))


def closed_volume(d: float, pitch: float, length: float, clearance: float = 0.0) -> float:
    """Volume of a rod of `length`: the section is the same at every z, so area times length."""
    return section_area(d, pitch, clearance) * length
