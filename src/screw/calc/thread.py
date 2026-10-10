"""The thread maths: the ISO 68-1:2023 basic profile and the closed form the kernel is judged by.

The profile was pinned at the Phase 2 D-01 checkpoint (flat crest P/8 at d/2, flat root P/4 at
d/2 - 5H/8, flanks at 60 degrees; `02-SPIKE.md`, Owner rulings). The closed form below is the
oracle for the THRD-04 postcondition in `screw.solid`: it shares no code path with the kernel,
so a kernel that builds the wrong solid cannot agree with it by accident.

This module runs on every keystroke through `params` and `calc`, so it is pure arithmetic: it
imports no kernel, no logger and no `screw.records` (import-linter contracts 2 and 4).
"""

from __future__ import annotations

import math

# The THRD-04 gate: the largest |measured / closed - 1| a thread build may show (L11). Ten times
# the winning estimator's largest error over `2026-10-08-a-grid` (8.147e-06, `GATE_FACTOR` 10),
# rounded up to one significant figure (`### 2026-10-08-a-verdict`, Volume estimator).
# Loosening it needs a superseding entry and a re-run of the grid block.
T_GATE = 9e-05


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


def volume_check(measured: float, closed: float) -> str | None:
    """None when `measured` is inside `T_GATE` of `closed`; otherwise the refusal text.

    The error is signed: an inverted solid reads about -2 and keeps its sign in the text.
    """
    if not (math.isfinite(closed) and closed > 0):
        return f"the closed form {closed:.6g} mm3 is not a finite positive number"
    rel = measured / closed - 1.0
    # Written as a negated <=, not `abs(rel) > T_GATE`: every comparison with NaN is False, so
    # the positive form would pass a NaN volume.
    if not abs(rel) <= T_GATE:
        return (f"the precise volume {measured:.6g} mm3 differs from the closed form "
                f"{closed:.6g} mm3 by relative error {rel:+.3e}, allowed {T_GATE:.0e} (L11)")
    return None
