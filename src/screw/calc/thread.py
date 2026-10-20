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

# INTERIM (D-17): the shortest length, or sewn tail, the builder accepts, in mm. Research probe
# 2026-10-10 at d=6, pitch=1: a twist of length <= 1e-8 mm SIGSEGVs the process before any check
# can run, 3e-8 to 1e-6 mm raises, 1e-5 mm builds; as a sewn tail, 1e-5 to 1e-2 mm built one
# valid solid at (6, 1), (2, 0.4) and (20, 2.5). 1e-3 sits 100x above the last failing tail.
# Phase 7 re-measures (OPER-03). One definition for the builder, the closed form, the caps and
# the info document (D-27).
MIN_TAIL_MM = 1e-3


def fundamental_height(pitch: float) -> float:
    """H = (sqrt(3) / 2) * P, the height of the sharp 60 degree triangle."""
    return math.sqrt(3) / 2 * pitch


def thread_depth(pitch: float) -> float:
    """5H/8: the radial distance from crest flat to root flat of the basic profile."""
    return 5 / 8 * fundamental_height(pitch)


def pitch_diameter(d: float, pitch: float) -> float:
    """d2 = D2 = d - 3H/4: the basic pitch diameter of the ISO 68-1:2023 basic profile (R13).

    This is the number the info panel prints. The GOST 24705-2004 (ISO 724:1993, MOD) Table 1
    value is not a source of it: the table is only what the shipped values are tested to agree
    with, rounded to the table's printed decimals.
    """
    return d - 3 / 4 * fundamental_height(pitch)


def basic_minor_diameter(d: float, pitch: float) -> float:
    """d1 = D1 = d - 5H/4: the basic minor diameter of the ISO 68-1:2023 basic profile (R13).

    The same value as the shank's `minor_diameter` row (d - 2 * 5H/8), under the name the nut's
    D1 uses. Tested against GOST 24705-2004 Table 1 only; no panel number comes from the table.
    """
    return d - 5 / 4 * fundamental_height(pitch)


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


# The flank's angle from the axis-normal plane, 30 degrees: the flank rises sqrt(3) mm per mm of
# radius change in z (RESEARCH F7; tests/test_thread_maths.py differentiates `section_radius` to
# confirm it), and tan 30 degrees = 1 / sqrt(3). The two gaps below derive from it, not from 0.5.
FLANK_ANGLE = math.pi / 6


def flank_normal_gap(clearance: float) -> float:
    """The gap measured normal to a flank when the nut surface is the rod surface moved
    radially by `clearance`: clearance * sin(flank angle), half the clearance at 30 degrees.

    For reporting, never a geometry input (PAIR-04): the nut surface is the rod surface moved
    radially by c, and the flank rises sqrt(3) mm per mm of z (RESEARCH F7).
    """
    return clearance * math.sin(FLANK_ANGLE)


def axial_play(clearance: float) -> float:
    """The axial slack across both flanks for a radial `clearance`: 2 * clearance * tan(flank
    angle), 2c / sqrt(3) at 30 degrees. Each flank is shifted c * tan(30 degrees) along z.

    For reporting, never a geometry input (PAIR-04).
    """
    return 2 * clearance * math.tan(FLANK_ANGLE)


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


def hex_prism_volume(s: float, k: float) -> float:
    """Volume of a regular hexagonal prism of across-flats `s` and height `k`.

    The hexagon area is (sqrt(3) / 2) s^2, a sharp-cornered plain prism with no chamfer or
    washer face (D-01, D-02).
    """
    return math.sqrt(3) / 2 * s * s * k


def nut_closed_volume(d: float, pitch: float, s: float, m: float, clearance: float) -> float:
    """Volume of the whole nut: the hex prism of across-flats `s` and height `m` less the thread
    void, which fills the section of the radial `clearance` over the whole height.

    Both hands agree to the digit (RESEARCH F3): the transverse section of a helical thread is
    the same outline for either hand, so the void is `section_area * m` whatever the hand is.
    The void overshoots both faces in the builder, but only the part inside the prism is
    removed, so the overshoot does not enter the closed form.
    """
    return hex_prism_volume(s, m) - section_area(d, pitch, clearance) * m


def built_thread_length(thread_length: float, length: float) -> float:
    """The thread the builder makes, in mm from the tip: `thread_length` capped at `length`.

    D-08: the thread runs from the tip, so a `thread_length` above `length` is built to the full
    length, and the stored field is never rewritten. D-27: a shank left shorter than
    `MIN_TAIL_MM` is a sliver the builder cannot take (the kernel crashed on one, RESEARCH
    Alert 6), so it is folded into the thread, as `helical.thread` folds its own sewn tail. The
    builder, the closed forms, both caps, the turn-cap validator and `derive` all call this and
    none recomputes it.
    """
    t = min(thread_length, length)
    return length if length - t < MIN_TAIL_MM else t


def bolt_closed_volume(d: float, pitch: float, length: float, s: float, k: float,
                       t: float) -> float:
    """Volume of the whole bolt (D-03): thread on z 0..t, plain shank t..length, head on
    length..length + k.

    The thread is the section area times t, the shank a cylinder of the major diameter, the head
    a hexagonal prism. `t` is `built_thread_length`, at most `length`.
    """
    return (section_area(d, pitch) * t + math.pi * (d / 2) ** 2 * (length - t)
            + hex_prism_volume(s, k))


def head_too_small_refusal(s: float, d: float) -> str | None:
    """None when the across-flats width `s` exceeds the diameter `d`; otherwise the text (D-23).

    The text begins `s and d: ` so the CLI, which prints no `loc` for a model-level error, still
    names both fields. No braces in the text: pydantic formats a custom error from its context.
    """
    if s > d:
        return None
    return (f"s and d: the across-flats width s {s:g} mm must exceed the diameter d {d:g} mm; "
            f"a head no wider than the shank is not a hex head")


def nut_too_thin_refusal(s: float, d: float, clearance: float) -> str | None:
    """None when the across-flats width `s` exceeds the void's major diameter `d + 2 * clearance`;
    otherwise the text (D-13).

    At or below it the void's crest reaches the flats and the nut is cut in two or left with an
    edge of no thickness. The text begins `s, d and clearance: ` so the CLI, which prints no `loc`
    for a model-level error, still names the fields. No braces: pydantic formats a custom error
    from its context.
    """
    major = d + 2 * clearance
    if s > major:
        return None
    return (f"s, d and clearance: across flats s {_plain(s)} mm must exceed the void's major "
            f"diameter d + 2 * clearance = {_plain(major)} mm, or the void is wider than the "
            f"flats and breaks through them")


def _plain(x: float) -> str:
    """`repr` without a trailing `.0`: 30.0 reads 30, 10.00001 reads 10.00001.

    `:g` keeps 6 significant figures and prints 10.00001 as 10, which would make the conflict
    text below say "10 mm is longer than 10 mm" (L02: a number the tool prints is one someone acts
    on).
    """
    return repr(x).removesuffix(".0")


def thread_length_conflict(length: float, thread_length: float) -> str | None:
    """None unless an explicit `thread_length` is longer than an explicit `length`; else the text.

    D-25: the one rule the API dependency and the CLI share, the shape of `download_refusal`.
    The model carries no such rule because it cannot tell an explicit value from a default
    (D-08: a default `thread_length` above a short `length` builds to the full length and warns).
    A value that is not finite or not above 0 gives None, so the model's own 422 keeps naming
    the bad field. Equal values are no conflict. No braces in the text: pydantic formats a custom
    error from its context.
    """
    if not (math.isfinite(length) and math.isfinite(thread_length)
            and length > 0 and thread_length > 0 and thread_length > length):
        return None
    return (f"thread_length and length: thread_length {_plain(thread_length)} mm is longer than "
            f"length {_plain(length)} mm; shorten thread_length or lengthen length")


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


def turn_cap_refusal(t: float, pitch: float) -> str | None:
    """None when t / pitch is at most `MAX_TURNS` as exact decimals; else the text (D-01, D-22).

    `t` is the built thread (`built_thread_length`), not the length: the shank adds no turns.
    The text begins `thread_length, length and pitch: ` so the CLI, which prints no `loc` for a
    model-level error, still names the fields.
    """
    if _exact(t) <= MAX_TURNS * _exact(pitch):
        return None
    return (f"thread_length, length and pitch: {turns_of(t, pitch):g} turns of built thread is "
            f"past the {MAX_TURNS}-turn cap, the most measured (run 2026-10-08-a-frontier); "
            f"shorten thread_length or length, or raise pitch")


def void_root_radius_refusal(d: float, pitch: float, clearance: float) -> str | None:
    """None when the nut void's root radius d/2 - 5H/8 + clearance is above 0; else the text (D-04).

    The nut's void grows by the clearance on both radii (L11 `section_radius`), so the rule the
    rod uses (`root_radius_refusal`, no clearance) is wrong for it: it refuses a nut a positive
    clearance would make and accepts one a negative clearance would push through the axis. The
    text begins `d, pitch and clearance: `. No braces: pydantic formats a custom error from its
    context.
    """
    root = d / 2 - thread_depth(pitch) + clearance
    if root > 0:
        return None
    return (f"d, pitch and clearance: the void's root radius d/2 - 5H/8 + clearance of the "
            f"ISO 68-1:2023 basic profile is {root:g} mm at d {d:g}, pitch {pitch:g} and "
            f"clearance {clearance:g}, and must be above 0")


def nut_turn_cap_refusal(m: float, pitch: float) -> str | None:
    """None when the void the builder makes, `m + 2 pitch`, is at most `MAX_TURNS` turns as exact
    decimals; else the text (P11).

    `solid/nut.py` sweeps the void a pitch past each face, so the kernel sees `m + 2 pitch`, not
    `m`. The text begins `m and pitch: `.
    """
    void = _exact(m) + 2 * _exact(pitch)
    if void <= MAX_TURNS * _exact(pitch):
        return None
    return (f"m and pitch: {float(void / _exact(pitch)):g} turns of void (m + 2 pitch, what the "
            f"builder makes) is past the {MAX_TURNS}-turn cap, the most measured (run "
            f"2026-10-08-a-frontier); lower m or raise pitch")


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
# D-22: the cap reads the built thread `t`, the part these rods measured. The head and the plain
# shank add bytes no run measured, bounded and small next to the thread (the head-plus-shank
# fine bytes are in `bench/RESULTS.md`, Head fuse probe); Phase 7 re-sweeps on the finished bolt.
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


def fine_stl_refusal(d: float, pitch: float, t: float, left_hand: bool) -> str | None:
    """None unless (d, pitch, left_hand) is a measured run and the built thread `t` is past its
    fine-STL cap.

    The text begins `thread_length and length: ` so the CLI, which prints no `loc` for a
    model-level error, still names the fields. No braces in the text: pydantic formats a custom
    error from its context.
    """
    cap = FINE_STL_ROWS.get((d, pitch, left_hand))
    if cap is None or t <= cap:
        return None
    hand = "left-hand" if left_hand else "right-hand"
    return (f"thread_length and length: the fine STL of a {hand} thread with d {d:g} and pitch "
            f"{pitch:g} is refused above {cap:g} mm of thread ({turns_of(cap, pitch):g} turns), "
            f"the longest L11 measured whose fine STL plus its gzip copy fit the 64 MiB export "
            f"budget (run 2026-10-08-a-grid); the thread built here is {t:g} mm. Shorten "
            f"thread_length or length, or ask for the preview STL or the STEP, which are not "
            f"capped")
