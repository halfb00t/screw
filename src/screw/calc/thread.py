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
from decimal import ROUND_DOWN, Decimal
from fractions import Fraction

# The THRD-04 gate: the largest |measured / closed - 1| a thread build may show (L11). Ten times
# the winning estimator's largest error over `2026-10-08-a-grid` (8.147e-06, `GATE_FACTOR` 10),
# rounded up to one significant figure (`### 2026-10-08-a-verdict`, Volume estimator).
# Loosening it needs a superseding entry and a re-run of the grid block.
T_GATE = 9e-05

# The most turns a bolt may ask for (D-01): L11's construction cap. The frontier walk
# `2026-10-08-a-frontier` reached 250 turns with no stop at every size, both hands, rod and
# void, and nothing above 250 is measured. A refusal and not a trim, because `length` is an
# explicit choice (L02); the INTERIM 30 s build timeout is the backstop below it. Phase 7
# replaces it with measured per-size caps (OPER-03).
MAX_TURNS = 250


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


def _exact(x: float) -> Fraction:
    """The decimal the user typed: `repr` is the shortest string that round-trips the float.

    Float division is wrong at the cap: 175 / 0.7 is a float above 250 although 175 mm at pitch
    0.7 (M4) is exactly 250 turns and is measured, while the exact binary value of 0.6 would
    refuse M3.5 at 150 mm (03-RESEARCH Pitfall 2). `Fraction(repr(inf))` raises ValueError,
    which `derive` reports as an absent row.
    """
    return Fraction(repr(x))


def turns_of(length: float, pitch: float) -> float:
    """length / pitch as the exact decimal quotient: 5.4 / 0.6 reads 9.0, not 9.000000000000002."""
    try:
        return float(_exact(length) / _exact(pitch))
    except OverflowError:
        # The quotient is past the float range (pitch below about length / 1.8e308, every
        # subnormal pitch): pydantic turns only ValueError into a 422, so an OverflowError here
        # was a 500 on the API and a traceback on the CLI. `derive` already drops a non-finite
        # row with a warning, and the refusal text reads "inf turns", which is true.
        return math.inf


def _largest_accepted_pitch(d: float) -> float | None:
    """The largest pitch of at most 6 significant figures whose root radius is above 0, or None.

    `d / (2 * thread_depth(1.0))` is the supremum, where the root radius is exactly 0 and is
    refused; `:g` rounds to nearest, so printing it sent back a pitch the same rule refused for
    993 of the 1999 diameters 0.1 .. 199.9 (d 1.1 printed 1.01614 against a limit of 1.016136).
    Truncating toward zero and re-checking with the very test the refusal uses makes the printed
    number one the user can type. Fewer digits are tried when 6 still land on the boundary, and
    None (no number) is the answer when none does (a subnormal d), never a plausible one (L02).
    """
    supremum = d / (2 * thread_depth(1.0))
    if not (math.isfinite(supremum) and supremum > 0):
        return None
    exact = Decimal(repr(supremum))
    for figures in range(6, 0, -1):
        candidate = float(exact.quantize(Decimal(1).scaleb(exact.adjusted() - figures + 1),
                                         rounding=ROUND_DOWN))
        if candidate > 0 and d / 2 - thread_depth(candidate) > 0:
            return candidate
    return None


def root_radius_refusal(d: float, pitch: float) -> str | None:
    """None when the root radius d/2 - 5H/8 is above 0; otherwise the refusal text (D-04).

    At 0 or below the root flat crosses the axis and the section is not a simple outline the
    kernel can sweep. No braces in the text: pydantic formats a custom error from its context.
    """
    root = d / 2 - thread_depth(pitch)
    if root > 0:
        return None
    text = (f"d and pitch: the root radius d/2 - 5H/8 of the ISO 68-1:2023 basic profile is "
            f"{root:g} mm at d {d:g} and pitch {pitch:g}, and must be above 0")
    largest = _largest_accepted_pitch(d)
    if largest is None:
        return text
    return f"{text}; the largest pitch for this d, to 6 significant figures, is {largest:g}"


def turn_cap_refusal(length: float, pitch: float) -> str | None:
    """None when length / pitch is at most `MAX_TURNS` as exact decimals; else the text (D-01)."""
    if _exact(length) <= MAX_TURNS * _exact(pitch):
        return None
    return (f"length and pitch: {turns_of(length, pitch):g} turns is past the {MAX_TURNS}-turn "
            f"cap, the most measured (run 2026-10-08-a-frontier); shorten length or raise pitch")


# The fine-STL caps of the thirteen (d, pitch, left_hand) rod runs L11 measured (D-03, D-21):
# (d, pitch, left_hand) -> the largest length in mm whose fine STL plus its gzip level-1 copy
# still fits the INTERIM 64 MiB export budget. L11 measured rows (`2026-10-08-a-grid`), not ISO
# rows: each cap is the longest measured length below the first grid rod row whose fine raw STL
# plus its gzip copy exceeded that budget, at the INTERIM fine preset (0.01 mm, 0.1 rad). The
# criterion is the sum of the two blobs, not the STL alone: at M8 right L=68 the raw fine STL is
# 45,659,684 bytes, under the budget. The caps are keyed by hand because the left-hand rods
# measured smaller files and fit longer (first over-budget length M10 right 57, left 73; the
# right-hand caps applied to a left-hand part refused lengths L11 had measured inside). The keys
# are the campaign's run keys (ISO 262 preview pitches, UNVERIFIED as table truth, exact as run
# keys and exactly representable floats), not ISO rows. This is bench evidence, not a `tables`
# module, so it does not pre-empt contract 6. It was measured against the 64 MiB budget only and
# applies unconditionally, even if a deployer changes SCREW_EXPORT_CACHE_MB (03-RESEARCH Open
# Question 4). A part off these keys gets no cap: a cap from an unmeasured mapping to the
# nearest row is the plausible number L02 forbids. Phase 7 re-measures the budget and the caps
# (OPER-02, OPER-03). Turns are derived from the millimetres by `turns_of`, never stored.
FINE_STL_ROWS: dict[tuple[float, float, bool], float] = {
    (8.0, 1.25, False): 67.5,    # first row over budget: M8 right L=68 rod
    (10.0, 1.5, False): 56.0,    # M10 right L=57 rod
    (12.0, 1.75, False): 60.0,   # M12 right L=61 rod
    (14.0, 2.0, False): 58.0,    # M14 right L=59 rod
    (16.0, 2.0, False): 52.0,    # M16 right L=53 rod
    (18.0, 2.5, False): 65.0,    # M18 right L=66 rod
    (20.0, 2.5, False): 64.0,    # M20 right L=65 rod
    # M8 left-hand: no row over budget up to 80 mm, so no cap (no measured stop).
    (10.0, 1.5, True): 72.0,     # M10 left L=73 rod
    (12.0, 1.75, True): 77.0,    # M12 left L=78 rod
    (14.0, 2.0, True): 78.0,     # M14 left L=79 rod
    (16.0, 2.0, True): 75.0,     # M16 left L=76 rod
    (18.0, 2.5, True): 91.0,     # M18 left L=92 rod
    (20.0, 2.5, True): 91.0,     # M20 left L=92 rod
}


def fine_stl_refusal(d: float, pitch: float, length: float, left_hand: bool) -> str | None:
    """None unless (d, pitch, left_hand) is a measured run and `length` is past its fine-STL cap.

    The text begins `length: ` so the CLI, which prints no `loc` for a model-level error, still
    names the field. No braces in the text: pydantic formats a custom error from its context.
    """
    cap = FINE_STL_ROWS.get((d, pitch, left_hand))
    if cap is None or length <= cap:
        return None
    hand = "left-hand" if left_hand else "right-hand"
    return (f"length: the fine STL of the {hand} rod with d {d:g} and pitch {pitch:g} is refused "
            f"above {cap:g} mm ({turns_of(cap, pitch):g} turns), the longest length L11 measured "
            f"whose fine STL plus its gzip copy fit the 64 MiB export budget (run "
            f"2026-10-08-a-grid); this length is {length:g} mm. Shorten length, or ask for the "
            f"preview STL or the STEP, which are not capped")
