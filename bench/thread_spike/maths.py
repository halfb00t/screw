"""The thread spike's oracle: the pinned profile's section and its closed-form volume.

Pure maths, free of the CAD kernel: the closed form is what the kernel is judged against, so it
imports no kernel code (an import-linter contract enforces that). It does share the pinned
profile parameters with the builder, which imports `thread_depth` from here;
`test_the_basic_profile_has_the_coefficients_the_owner_confirmed` pins `thread_depth(1.0)` to
the independently written ISO value 0.541265877. Shaped like the future `screw/calc/thread.py`
(D-18).

Profile: ISO 68-1:2023 basic profile, flat crest and flat root, pinned by the owner on
2026-10-06 (02-SPIKE.md, Owner rulings). One-way door: a different profile re-runs the campaign.
Symbols, defined once: `d` major diameter, `P` pitch (`pitch`), `H` fundamental triangle height,
`c` radial clearance, `theta` the angle round the axis.
"""

from __future__ import annotations

import functools
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

# ISO 4017 greatest standard length <= 10d or 200 mm (D-03). The 200 mm cap is a preview value,
# UNVERIFIED until Phase 4's row tests.
LENGTH_CAP_DIAMETERS = 10
LENGTH_CAP_MM = Fraction(200)
# The failure frontier beyond the standard max: 5 turns a step (D-04) up to 250 turns, the
# research's measured ceiling for sewn twist (STACK section A: 0 of 166 failures up to 250 turns).
FRONTIER_STEP_TURNS = 5
FRONTIER_MAX_TURNS = 250
# The sizes the K sweep, the reference rows and the ladder run on (RESEARCH Open Question 7):
# the six trim-probe sizes plus the odd pitches M2.5 and M8.
SAMPLE_SIZES: tuple[str, ...] = ("M2", "M2.5", "M3", "M6", "M8", "M10", "M16", "M20")
# Segment lengths in turns swept before K is locked for the grid (D-07).
K_CANDIDATES: tuple[int, ...] = (3, 5, 10)
# Radial clearance in mm of the void every grid and frontier row builds: the upper end of D-11's
# proof bracket, the outline furthest from the rod section the research verified.
VOID_CLEARANCE = 0.20
# The ruled-surface reference package's module (D-06): imported by the reference worker only,
# from a scratch directory outside the repository (PITFALLS M11). A name here, not an import:
# this module is kernel-free and the parent process reads it to probe the scratch directory.
RULED_MODULE = "cq_warehouse.thread"
# Tip chamfer cone angle in degrees, measured from the end face, meeting it at the minor radius.
# UNVERIFIED: ISO 4753 is unread, so this is a stated protocol input and the trim row it feeds
# is cost evidence for Phase 4, not geometry truth (D-08, 02-SPIKE.md owner rulings).
TIP_CHAMFER_DEG = 30.0
# The mesh ladder is a fraction of the thread depth h = 5H/8 (CONTEXT discretion): h/4 ... h/32
# at angular 0.5. Triangles scale about with 1/deflection (RESEARCH Pattern 7).
DEPTH_FRACTIONS: tuple[int, ...] = (4, 8, 16, 32)
LADDER_ANGULAR = 0.5

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


def standard_max(d: Fraction) -> Fraction:
    """The greatest length the grid covers: min(10 d, 200 mm) (D-03)."""
    return min(LENGTH_CAP_DIAMETERS * d, LENGTH_CAP_MM)


def lengths(d: Fraction, pitch: Fraction, lower: Fraction | None = None) -> list[Fraction]:
    """The D-03 grid in exact fractions, ascending, each length once: every integer-turn length
    k * P and every integer-millimetre length from `lower` up to `standard_max(d)`, both ends
    included.

    `lower` defaults to min(P, 1 mm), the owner's R2 ruling (02-SPIKE.md): it keeps sub-turn
    rows such as M8 L = 1 mm = 0.8 turn, where the short-length floor lives. Exact fractions
    because the grid is also the set of integer-turn lengths: float k * P drifts (168 of 3000
    products fail (k * P) / P == k) and would list a coincident length twice, e.g. 9 mm = 20
    turns of M2.5's 9/20 (RESEARCH Pitfall 1).
    """
    cap = standard_max(d)
    low = min(pitch, Fraction(1)) if lower is None else lower
    by_turns = {k * pitch for k in range(1, int(cap / pitch) + 1)}
    by_mm = {Fraction(mm) for mm in range(1, int(cap) + 1)}
    return sorted(x for x in by_turns | by_mm if low <= x <= cap)


def is_integer_turn(length: Fraction, pitch: Fraction) -> bool:
    """Exact: the quotient's denominator is 1. Never a float comparison (see `lengths`)."""
    return turns_of(length, pitch).denominator == 1


def turns_of(length: Fraction, pitch: Fraction) -> Fraction:
    """Turns in `length`, exactly. The builder gets `float(turns_of(...))`, never a float
    division of two floats, so an integer-turn row is built with its exact integer."""
    return length / pitch


def frontier_turns(d: Fraction, pitch: Fraction) -> list[int]:
    """The D-04 frontier: from the first multiple of 5 turns strictly above the standard max,
    in steps of 5, up to and including 250. A standard max that is itself a multiple of 5 turns
    (M2 50, M6 60) starts at the next one: that length is already in the grid."""
    standard_turns = turns_of(standard_max(d), pitch)
    first = (int(standard_turns // FRONTIER_STEP_TURNS) + 1) * FRONTIER_STEP_TURNS
    return list(range(first, FRONTIER_MAX_TURNS + 1, FRONTIER_STEP_TURNS))


def depth_presets(pitch: float) -> list[tuple[str, float, float]]:
    """The ladder's deflection presets: (name, linear deflection mm, angular rad) at h/4,
    h/8, h/16 and h/32 of the thread depth h = 5H/8, angular `LADDER_ANGULAR`."""
    depth = thread_depth(pitch)
    return [(f"h/{n}", depth / n, LADDER_ANGULAR) for n in DEPTH_FRACTIONS]


# --- Pair check (question 3): the kernel-free expectation a pair reading is judged against ---

# Midpoints over one turn: the integral below matched the kernel to 4-5 significant figures
# whenever the kernel returned a non-empty result (RESEARCH R5, R7: 1e-5 relative at M10 and
# M20), so it is the band's centre.
INTEGRATION_POINTS = 400_000

# Nut height m in mm per size (D-13, owner ruling R5, 02-SPIKE.md). m only scales the engaged
# length and the closed-form expectation together: a label, never a verdict input. Every entry
# carries its source label as recorded at the checkpoint and is UNVERIFIED until Phase 5 reads
# the standard; none was read from it by the owner.
NUT_HEIGHT: dict[str, float] = {
    "M2": 1.60,    # Annex A not read; memory of the withdrawn ISO 4032:2012. UNVERIFIED
    "M2.5": 2.00,  # Annex A not read; memory of the withdrawn ISO 4032:2012. UNVERIFIED
    "M3": 2.40,    # Annex A not read; memory of the withdrawn ISO 4032:2012. UNVERIFIED
    "M3.5": 2.80,  # 0.8 * d, no ISO 4032 row. UNVERIFIED
    "M4": 3.20,    # Annex A not read; memory of the withdrawn ISO 4032:2012. UNVERIFIED
    "M5": 4.70,    # m max as read from the ISO 4032:2023 preview by the research. UNVERIFIED
    "M6": 5.20,    # m max as read from the ISO 4032:2023 preview by the research. UNVERIFIED
    "M7": 5.60,    # ISO 4032:2023 added M7, no value read: 0.8 * d, a stated input. UNVERIFIED
    "M8": 6.80,    # m max as read from the ISO 4032:2023 preview by the research. UNVERIFIED
    "M10": 8.40,   # m max as read from the ISO 4032:2023 preview by the research. UNVERIFIED
    "M12": 10.80,  # m max as read from the ISO 4032:2023 preview by the research. UNVERIFIED
    "M14": 12.80,  # memory of the same table, not re-read. UNVERIFIED
    "M16": 14.80,  # m max as read from the ISO 4032:2023 preview by the research. UNVERIFIED
    "M18": 15.80,  # memory of the same table, not re-read. UNVERIFIED
    "M20": 18.00,  # m max as read from the ISO 4032:2023 preview by the research. UNVERIFIED
}

# Radial clearance of the nut's void in mm, the proof bracket (D-11): the upper end brackets
# Phase 6's printed matrix.
PAIR_CLEARANCES: tuple[float, ...] = (0.05, 0.10, 0.15, 0.20)
# The diagnostic rows (D-11): c = 0 reads inconclusive by definition (the boolean's answer at
# contact is recorded, not trusted: garbage in 3 of 3 research readings), c = -0.05 is the
# sensitivity check, where interference must appear near the closed form.
DIAGNOSTIC_CLEARANCES: tuple[float, ...] = (0.0, -0.05)
# Three screw-motion poses equally spaced over one turn and centred on the seam. The seam pose
# stays in: dropping it would be a pose picked after the probes saw false-empty readings near
# it (RESEARCH Pitfall 3). Every |theta| <= 2 pi / 3 keeps the matched slide at P / 3 and the
# control slide at 5 P / 6, inside the rod's pad of P (Pitfall 2).
MATCHED_POSES: tuple[float, ...] = (-2 * math.pi / 3, 0.0, 2 * math.pi / 3)
# The control: the nut slid half a pitch from the matched pose, so crest meets root (D-12).
CONTROL_OFFSET_PITCHES = 0.5
# The sizes that also run at the two K values other than the locked one, as reference rows
# (Pitfall 8): the research's four probe sizes.
PAIR_REFERENCE_SIZES: tuple[str, ...] = ("M2", "M6", "M10", "M20")


@functools.cache
def interference_area(d: float, pitch: float, clearance: float, phase: float) -> float:
    """Transverse area in mm2 where a rod of the pinned profile overlaps a void of the same
    profile grown by `clearance` and turned by `phase`: 0.5 * max(0, r_b(t)^2 - (r_b(t + phase)
    + c)^2) integrated over one turn. Times the engaged length m it is the volume of the
    interference. Hand-independent: a symmetric profile's transverse section is the same for
    both hands (RESEARCH R4 read left = right).

    `phase` 0 is a matched pose, pi the half-pitch control. M6, m = 5.2: control 12.213 at
    c = 0.10, 14.1335 at 0.05, 16.1427 at 0; matched 4.3627 at c = -0.05 and exactly 0 at
    every c > 0 (RESEARCH Pattern 5). Cached: 400 000 midpoints take about 0.35 s, and the
    verdict asks for the same (size, c, phase) once per hand.
    """
    step = 2 * math.pi / INTEGRATION_POINTS
    total = math.fsum(
        max(0.0, section_radius(d, pitch, 0.0, theta) ** 2
            - section_radius(d, pitch, clearance, theta + phase) ** 2)
        for theta in ((i + 0.5) * step for i in range(INTEGRATION_POINTS)))
    return 0.5 * total * step
