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


# The fine-STL caps of the thirteen (d, pitch, left_hand) rod runs L11 measured (D-03, D-21): (d,
# pitch, left_hand) -> the largest length in mm whose fine STL plus its gzip level-1 copy still fits
# the INTERIM 64 MiB export budget. L11 measured rows (`2026-10-08-a-grid`), not ISO rows: each cap
# is the longest measured length below the first grid rod row whose fine raw STL plus its gzip copy
# exceeded that budget, at the fine preset (0.01 mm, 0.1 rad), which the D-21 rule kept
# (bench/RESULTS.md "Mesh deviation (Phase 5, D-21)": worst deviation 0.0161 mm against the 0.025 mm
# bound), so no cap was re-derived; tests/test_mesh.py pins the preset the caps were measured at.
# The criterion is the sum of the two blobs, not the STL alone: at M8 right L=68 the raw fine STL is
# 45,659,684 bytes, under the budget. The caps are keyed by hand because the left-hand rods measured
# smaller files and fit longer (first over-budget length M10 right 57, left 73; the right-hand caps
# applied to a left-hand part refused lengths L11 had measured inside). The keys are the campaign's
# run keys (ISO 262 preview pitches, UNVERIFIED as table truth, exact as run keys and exactly
# representable floats), not ISO rows. This is bench evidence, not a `tables` module, so it does not
# pre-empt contract 6. It was measured against the 64 MiB budget only and applies unconditionally,
# even if a deployer changes SCREW_EXPORT_CACHE_MB (03-RESEARCH Open Question 4). A part off these
# keys gets no cap: a cap from an unmeasured mapping to the nearest row is the plausible number L02
# forbids. Phase 7 re-measures the budget and the caps (OPER-02, OPER-03). Turns are derived from
# the millimetres by `turns_of`, never stored.
# D-22: the cap reads the built thread `t`, the part these rods measured. The head and the plain
# shank add bytes no run measured, bounded and small next to the thread (the head-plus-shank fine
# bytes are in `bench/RESULTS.md`, Head fuse probe); Phase 7 re-sweeps on the finished bolt.
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


# The fine-STL caps of the thirty nut keys (the 15 ISO 262 coarse (d, pitch) by both hands), R16
# and R17: (d, pitch, left_hand) -> the largest whole-mm nut height m whose fine STL plus its gzip
# level-1 copy still fits the INTERIM 64 MiB export budget. Measured by bench/nut_fine_caps.py,
# run `2026-10-21-nut-fine-caps-amended` (bench/RESULTS.md "Nut fine-STL caps, amended re-run
# (Phase 5, R17)"), which repeated run `2026-10-20-nut-fine-caps` row for row with identical
# bytes. The rule, fixed before any row ran: the shipped `screw.solid.export(p, "stl", "fine")` of
# a nut at m = 1, 2, 3, ... mm, the cap the largest m that fits below the first that does not. The
# fine preset is (0.01 mm, 0.1 rad), the one tests/test_mesh.py pins and the cap records header
# carries (a test compares them, so a preset change fails until the caps are re-measured). The run
# measured at clearance NUT_FINE_STL_CLEARANCE (5.0 mm, the owner's R16 answer: the largest
# clearance any GOST ISO 4032-2014 row's own s admits) and at s 1e5 mm (INTERIM_MAX_MM, the
# largest s the model admits). Because s adds a near-constant number of bytes that does not grow
# with m (the planner's 05-19 probe), a cap measured at the largest s holds for every s; the run's
# checks at clearances -0.05, 0, 0.1 and 2.5 and at the slimmest s at 5.0 all fit the budget where
# the shipped build made the part (it refuses the others, which are no file:
# docs/tech_debt/active/2026-10-21-nut-lead-in- gate-refuses-a-valid-nut-at-huge-s.md). A nut off
# these 30 keys gets no cap: the rods' FINE_STL_ROWS is never applied to a nut (R12) and a cap
# from an unmeasured mapping to the nearest row is the plausible number L02 forbids (D-03). The
# numbers are macOS arm64 and the INTERIM budget; Phase 7 re-measures on linux/amd64 (OPER-02).
NUT_FINE_STL_RUN = "2026-10-21-nut-fine-caps-amended"
NUT_FINE_STL_CLEARANCE = 5.0
NUT_FINE_STL_ROWS: dict[tuple[float, float, bool], float] = {
    (2.0, 0.4, False): 12.0, (2.5, 0.45, False): 13.0, (3.0, 0.5, False): 15.0,
    (3.5, 0.6, False): 18.0, (4.0, 0.7, False): 21.0, (5.0, 0.8, False): 24.0,
    (6.0, 1.0, False): 30.0, (7.0, 1.0, False): 30.0, (8.0, 1.25, False): 38.0,
    (10.0, 1.5, False): 36.0, (12.0, 1.75, False): 41.0, (14.0, 2.0, False): 46.0,
    (16.0, 2.0, False): 45.0, (18.0, 2.5, False): 54.0, (20.0, 2.5, False): 36.0,
    (2.0, 0.4, True): 15.0, (2.5, 0.45, True): 17.0, (3.0, 0.5, True): 19.0,
    (3.5, 0.6, True): 22.0, (4.0, 0.7, True): 25.0, (5.0, 0.8, True): 30.0,
    (6.0, 1.0, True): 38.0, (7.0, 1.0, True): 38.0, (8.0, 1.25, True): 47.0,
    (10.0, 1.5, True): 50.0, (12.0, 1.75, True): 56.0, (14.0, 2.0, True): 61.0,
    (16.0, 2.0, True): 59.0, (18.0, 2.5, True): 73.0, (20.0, 2.5, True): 47.0,
}


def nut_fine_stl_refusal(d: float, pitch: float, m: float, clearance: float,
                         left_hand: bool) -> str | None:
    """None unless (d, pitch, left_hand) is one of the 30 measured nut keys and either the clearance
    is above the ceiling the run measured at or `m` is past the key's fine-STL cap.

    The clearance is judged first: the cap holds only at or below `NUT_FINE_STL_CLEARANCE`, so a
    larger clearance has no measured cap to be judged against (R16). The text begins `clearance: `
    or `m: ` so the CLI, which prints no `loc` for a model-level error, still names the field. No
    braces in the text: pydantic formats a custom error from its context.
    """
    cap = NUT_FINE_STL_ROWS.get((d, pitch, left_hand))
    if cap is None:
        return None
    if clearance > NUT_FINE_STL_CLEARANCE:
        return (f"clearance: the fine STL of a nut with d {d:g} and pitch {pitch:g} was measured "
                f"only at a clearance of {NUT_FINE_STL_CLEARANCE:g} mm or less (run "
                f"{NUT_FINE_STL_RUN}), and a larger clearance makes a larger file; the clearance "
                f"asked for is {clearance:g} mm. Use a clearance of {NUT_FINE_STL_CLEARANCE:g} mm "
                f"or less, or ask for the preview STL or the STEP, which are not capped")
    if m <= cap:
        return None
    hand = "left-hand" if left_hand else "right-hand"
    return (f"m: the fine STL of a {hand} nut with d {d:g} and pitch {pitch:g} is refused above m "
            f"{cap:g} mm, the tallest run {NUT_FINE_STL_RUN} measured whose fine STL plus its gzip "
            f"copy fit the 64 MiB export budget (at a clearance of {NUT_FINE_STL_CLEARANCE:g} mm "
            f"and s 1e5 mm); the m asked for is {m:g} mm. Lower m, or ask for the preview STL or "
            f"the STEP, which are not capped")


# --- the end-cut oracles (05-RESEARCH F4, P10; probed in `bench/RESULTS.md`, End-cut probe) -----
#
# The transverse section of a thread is the same at every z and rotation-invariant, so for a
# radius `rho` the area it pokes outside a disc has a closed form, and a cone cut is a
# one-dimensional integral over its depth. These are the numbers the THRD-04 differential gate
# compares a chamfered or filleted part against. They are plain `math`, share no code path with
# the kernel, and refuse with a `ValueError` naming the condition outside their validity: no
# number there (L02). The formulas moved here unchanged from `bench/end_cuts.py`, where the
# kernel agreed with them to the piece errors recorded in the probe entry (the first hexagon-arc
# formula written for F4 was off by a factor of 2.2, so `tests/test_end_oracles.py` pins each
# one to an identity that does not use it).


def _check_angle(name: str, degrees: float) -> None:
    if not 0 < degrees < 90:
        raise ValueError(f"{name} {degrees:g} degrees must be above 0 and below 90")


def outside_disc_area(d: float, pitch: float, clearance: float, rho: float) -> float:
    """Area of the thread section that lies outside the disc of radius `rho`.

    Half the integral over one turn of max(0, r(theta)^2 - rho^2): the crest flat spans pi/4 at
    ro, the root flat pi/2 at rr and each flank 5 pi/8 with r linear in angle. Valid for any
    `rho >= 0` and any clearance; the helix phase and the hand drop out because the section is
    rotation-invariant. At `rho = 0` it is `section_area`; at or past the crest radius it is 0.
    """
    if not rho >= 0:
        raise ValueError(f"rho {rho:g} mm must be 0 or more")
    ro, rr = _radii(d, pitch, clearance)
    k = ro - rr
    total = 0.0
    if rho < ro:
        total += 0.5 * (ro**2 - rho**2) * math.pi / 4
    if rho < rr:
        total += 0.5 * (rr**2 - rho**2) * math.pi / 2
    if rho <= rr:
        flank = (ro**3 - rr**3) / (3 * k) - rho**2
    elif rho < ro:
        flank = (ro**3 - rho**3) / (3 * k) - rho**2 * (ro - rho) / k
    else:
        flank = 0.0
    return total + 0.5 * 2 * (5 * math.pi / 8) * flank


def tip_cone_volume(d: float, pitch: float, angle_deg: float, n: int = 20_000) -> float:
    """Volume a tip cone removes from the bare thread (clearance 0).

    The cone meets the end face at the minor radius and rises at `angle_deg` from the face, so
    its radius at height z is minor + z / tan(angle); at each z it removes the section outside
    that disc. `n` midpoints over z in [0, (d/2 - minor) tan(angle)], above which the cone is
    outside the section. Valid for 0 < angle < 90, a minor radius above 0 and any rod longer
    than that height; at n = 20 000 the quadrature error is below T_GATE / 100 of the piece
    (`tests/test_end_oracles.py`).
    """
    _check_angle("angle", angle_deg)
    minor = d / 2 - thread_depth(pitch)
    if not minor > 0:
        raise ValueError(f"the minor radius {minor:g} mm must be above 0 for a tip cone")
    tan_alpha = math.tan(math.radians(angle_deg))
    h = (d / 2 - minor) * tan_alpha / n
    return h * sum(outside_disc_area(d, pitch, 0.0, minor + (i + 0.5) * h / tan_alpha)
                   for i in range(n))


def nut_material_in_disc(d: float, pitch: float, clearance: float, rho: float) -> float:
    """Nut material inside the disc of radius `rho`: the disc less the void it holds,
    pi rho^2 - section_area + outside_disc_area(rho). It is 0 inside the root circle.

    Valid while `rho <= s / 2`, the inscribed radius of the hexagon: past it the disc leaves the
    nut and the formula overcounts (P10). The caller holds `s`; `countersink_volume` checks it.
    """
    return math.pi * rho**2 - section_area(d, pitch, clearance) + outside_disc_area(
        d, pitch, clearance, rho)


def countersink_volume(d: float, pitch: float, clearance: float, s: float, face_radius: float,
                       half_angle_deg: float, depth: float, n: int = 20_000) -> float:
    """Material one countersink removes from a nut face.

    The cone has radius `face_radius` - z tan(half) at depth z from the face, `half_angle_deg`
    from the axis; it removes `nut_material_in_disc` at each z over [0, depth] (`n` midpoints).
    Below the root radius the disc holds no material and the integrand is 0, so a cone that ends
    in the void and one that ends at `depth` agree. Valid when the face radius is at most s / 2
    (inside the inscribed circle), 0 < half angle < 90 and the cone has not reached its apex by
    `depth`. Two more conditions are the caller's, because this function holds neither the nut
    height nor the chamfer: face radius at most the chamfer's start radius (else the cutters
    overlap and are counted twice) and 2 * depth <= m (the countersinks of the two faces do
    not meet); `end_depths` holds both (P10).
    """
    _check_angle("half angle", half_angle_deg)
    if not 0 < face_radius <= s / 2:
        raise ValueError(f"face radius {face_radius:g} mm must be above 0 and at most s / 2 = "
                         f"{s / 2:g} mm, the inscribed radius of the hexagon")
    tan_half = math.tan(math.radians(half_angle_deg))
    if not (math.isfinite(depth) and depth >= 0 and face_radius - depth * tan_half >= 0):
        raise ValueError(f"depth {depth:g} mm must be 0 or more and at most face radius / "
                         f"tan(half angle) = {face_radius / tan_half:g} mm, where the cone ends")
    h = depth / n
    return h * sum(nut_material_in_disc(d, pitch, clearance, face_radius - (i + 0.5) * h * tan_half)
                   for i in range(n))


def hex_arc_inside(s: float, rho: float) -> float:
    """Length of the circle of radius `rho` that lies inside the regular hexagon of across-flats
    `s`: the whole circle up to the inscribed radius a = s / 2, rho (2 pi - 12 acos(a / rho))
    between a and the corner radius R = a / cos(pi / 6), nothing above.
    """
    a = s / 2
    corner = a / math.cos(math.pi / 6)
    if rho <= a:
        return 2 * math.pi * rho
    if rho >= corner:
        return 0.0
    return rho * (2 * math.pi - 12 * math.acos(a / rho))


def face_chamfer_volume(s: float, r0: float, angle_deg: float, depth: float,
                        n: int = 40_000) -> float:
    """Material one hexagon-corner face chamfer removes from a prism of across-flats `s`.

    A cone starting at radius `r0` on the face and rising at `angle_deg` from it removes a depth
    (rho - r0) tan(angle), no deeper than `depth`, over the arc `hex_arc_inside(s, rho)`,
    integrated over rho in [r0, R] (`n` midpoints). At `depth` 0 it is 0, and at the cone's own
    depth at the corner, (R - r0) tan(angle), the cap no longer binds. Valid when 0 < r0 < R, 0
    < angle < 90 and depth >= 0. Two conditions are the caller's: r0 outside the void's crest
    radius, and a depth of at most m / 2 (the chamfers of the two faces do not meet);
    `end_depths` holds both (P10).
    """
    _check_angle("angle", angle_deg)
    corner = s / 2 / math.cos(math.pi / 6)
    if not 0 < r0 < corner:
        raise ValueError(f"chamfer start {r0:g} mm must be above 0 and below the corner radius "
                         f"{corner:g} mm")
    if not (math.isfinite(depth) and depth >= 0):
        raise ValueError(f"depth {depth:g} mm must be 0 or more")
    tan_beta = math.tan(math.radians(angle_deg))
    h = (corner - r0) / n
    return h * sum(hex_arc_inside(s, r0 + (i + 0.5) * h) * min((i + 0.5) * h * tan_beta, depth)
                   for i in range(n))


# The hexagon less its inscribed disc, over a^2: 2 sqrt(3) - pi. The closed form below uses it as
# the area a flat cut at `depth` takes from outside the inscribed circle.
_HEX_RIM = 2 * math.sqrt(3) - math.pi

# The uncapped head chamfer over tan(angle) a^3: 4/3 + pi/3 + ln 3 - 2 sqrt(3) = 0.01504155806...
_UNCAPPED_J = 4 / 3 + math.pi / 3 + math.log(3) - 2 * math.sqrt(3)


def head_chamfer_volume(s: float, angle_deg: float, depth: float) -> float:
    """Material the top-face cone chamfer removes from a hexagonal head of across-flats `s`.

    The cone starts at the inscribed circle a = s / 2 and rises at `angle_deg` from the face; it
    removes (rho - a) tan(angle), no deeper than `depth`, over the arc `hex_arc_inside(s, rho)`
    of each circle rho from a to the corner radius R = a / cos(pi / 6). This is that integral in
    closed form, so the head's volume stays exact (06.1 D-07). Writing w = sqrt(rho^2 - a^2) and
    A = acos(a / rho), integration by parts gives

    - the integral of rho^2 (2 pi - 12 A) is
      2 pi rho^3 / 3 - 4 rho^3 A + 2 a rho w + 2 a^3 asinh(w / a)
    - the integral of rho (2 pi - 12 A) is pi rho^2 - 6 rho^2 A + 6 a w

    Both vanish at rho = a, and the second at R is the hexagon less its inscribed disc,
    a^2 (2 sqrt 3 - pi): a built-in check. When the cut is no deeper than the cone reaches at the
    corner the result is one constant, tan(angle) a^3 (4/3 + pi/3 + ln 3 - 2 sqrt 3). Otherwise
    the cone meets the flat at x = depth / tan(angle) past the inscribed circle and the cut is
    the cone below that and `depth` times the hexagon area beyond it.

    Three details keep it honest (L02): x is formed from `depth / tan` and never as a difference of
    two radii (that form returned -49.5 mm3 at 89.99999999999999 degrees), the angle comes from
    `atan2` and `asinh`, and below theta = asinh(w / a) 0.05 the acos part, three orders of
    magnitude of cancellation, is replaced by its series (the next term is under 1e-14 relative at
    0.05). Measured: worst 3.4e-14 against an independent Gauss-Legendre reference over 600 rows,
    4.3e-10 against `face_chamfer_volume` and the polar integral in `tests/test_end_oracles.py`
    over 108 rows, which is their own quadrature error. Valid for s above 0, 0 < angle < 90 and
    a finite depth of 0 or more; anything else, and an angle whose tangent underflows to 0,
    raises `ValueError` (never `ZeroDivisionError`, which `derive` would not catch).
    """
    _check_angle("head_chamfer", angle_deg)
    if not (math.isfinite(s) and s > 0):
        raise ValueError(f"s {s:g} mm must be finite and above 0")
    tau = math.tan(math.radians(angle_deg))
    if not tau > 0:
        raise ValueError(f"head_chamfer {angle_deg:g} degrees is too small to have a tangent")
    if not (math.isfinite(depth) and depth >= 0):
        raise ValueError(f"depth {depth:g} mm must be finite and 0 or more")
    a = s / 2
    x = depth / tau
    if x >= a * (2 / math.sqrt(3) - 1):
        return tau * a**3 * _UNCAPPED_J
    xi = x / a
    w = math.sqrt(xi * (xi + 2))
    theta = math.asinh(w)
    g = math.atan2(w, 1.0)
    ch = 1 + xi
    pi_part = math.pi / 3 * xi * xi * (2 * xi + 3)
    if theta < 0.05:
        t2 = theta * theta
        acos_part = -(theta**5) * (6 / 5 + t2 * (1 / 2 + t2 * (13 / 180 + t2 * 71 / 10080)))
    else:
        acos_part = -2 * (ch * ch * (2 * ch - 3) * g + w * (3 - ch) - theta)
    i2 = math.pi * w * w - 6 * ch * ch * g + 6 * w
    return tau * a**3 * (pi_part + acos_part) + depth * a**2 * (_HEX_RIM - i2)


def fillet_ring_volume(d: float, r: float) -> float:
    """Volume of a quarter-circle fillet ring of radius `r` at a shank of diameter `d`.

    The revolved region is the square r x r less a quarter disc centred on its far corner: area
    A = r^2 (1 - pi/4) and first moment about the shank r^3 (5/6 - pi/4), so Pappus gives
    2 pi (d/2 A + r^3 (5/6 - pi/4)) = 2 pi (d/2 + u_bar) A with u_bar the centroid's offset.
    Valid for r above 0. That the shank is at least r long under the head is the caller's.
    """
    if not r > 0:
        raise ValueError(f"r {r:g} mm must be above 0")
    return 2 * math.pi * (d / 2 * r**2 * (1 - math.pi / 4) + r**3 * (5 / 6 - math.pi / 4))


# --- the end models (D-12, R2 to R4; recorded as models, never as cited table values) -----------
#
# Each constant says where it comes from in `05-OWNER-READS.md` and whether it is `cited` (one
# printed number, with its document) or a `stated model` (a band or no clause: the choice is
# named, not invented, and any panel row it feeds says "model"). Tuning one toward a gate that
# passes is forbidden (D-23): a value changes only by a new owner ruling and a new L15 entry.

# Bolt tip, stated model (R2, read 6: GOST 12414-94 (ISO 4753:1983), the chamfered end). The text
# prints the end face diameter and the length u and marks the angle on its figures as about 45
# degrees; it prints no angle number and no chamfer length. Note 3's "48 degrees" is recorded as
# an unresolved misprint and not used (owner ruling 2026-10-20, option a). The cone meets the end
# face at the minor diameter and rises at this angle from the face, which is what
# `tip_cone_volume` integrates.
TIP_ANGLE_DEG = 45.0

# Nut lead-in countersink, stated model (R3 b, read 3: GOST ISO 4032-2014 (ISO 4032:2012),
# Figure 1 footnote c). The figure prints the included angle as a band, 90 to 120 degrees; the
# model takes the 90 degree end, so the half angle from the axis is 45 degrees.
COUNTERSINK_HALF_ANGLE_DEG = 45.0

# Nut lead-in countersink face radius, stated model (R3 b, owner ruling 2026-10-20, option A):
# the countersink opens to `COUNTERSINK_FACE_FACTOR * d / 2` on the face. GOST ISO 4032-2014
# (ISO 4032:2012) Figure 1 footnote c names the diameter `da` the countersink runs to, and
# Tables 1 and 2 print `da max` per size but the figure gives no rule that ties the face to it.
# The factor is the largest `da_max / d` of the 14 table rows, 1.16 at M2,5
# (the smallest is 1.079, at M14: 15.1 / 14), so the cone opens at least as wide as any printed
# `da`. A model, not a printed number: any panel row it feeds says "model".
COUNTERSINK_FACE_FACTOR = 1.16

# Nut face chamfer, stated model (R4 a, read 3: GOST ISO 4032-2014 (ISO 4032:2012), Figure 1
# footnote b). The figure prints the angle of the hexagon corners' chamfer as a band, 15 to 30
# degrees from the end face, and no depth; the model takes the 30 degree end, as a cone from the
# inscribed circle of `s` (start radius s / 2, from fields and not from the row's `dw`, D-12).
CHAMFER_ANGLE_DEG = 30.0

# Bolt head chamfer band, stated model (L19, owner ruling 2026-10-24). The band is the one the R4 a
# read prints for the nut's hexagon-corner chamfer (GOST ISO 4032-2014 (ISO 4032:2012), Figure 1
# footnote b, read 3 in `05-OWNER-READS.md`): 15 to 30 degrees from the end face, applied to the
# bolt head by the owner's ruling. No repo note records a read of the ISO 4014 or ISO 4017 head
# figure and those texts are not purchased (L14), so no edition of either is cited here. Both edges
# are inside the band; an angle outside it builds as asked and is warned about.
HEAD_CHAMFER_BAND_DEG = (15.0, 30.0)

# Under-head fillet radius `r` (minimum), cited (R1 option a, read from GOST R ISO 4014-2013 (ISO
# 4014:2011) Tables 1 and 2, the `r` minimum row, owner ruling 2026-10-20, L14 amendment; the
# Source document is `GOST R ISO 4014-2013 (ISO 4014:2011)`). Keyed on exact (d, pitch) in
# millimetres: a bolt off a row gets no fillet, never a guessed radius (L02). Neither table prints
# M7, so there is none. The solid reads no table (contract 6), so this is a second typed copy of
# `screw.tables.iso4014.FILLETS`, pinned equal to it by `tests/test_tables.py`.
FILLET_R: dict[tuple[float, float], float] = {
    (2.0, 0.4): 0.1,
    (2.5, 0.45): 0.1,
    (3.0, 0.5): 0.1,
    (3.5, 0.6): 0.1,
    (4.0, 0.7): 0.2,
    (5.0, 0.8): 0.2,
    (6.0, 1.0): 0.25,
    (8.0, 1.25): 0.4,
    (10.0, 1.5): 0.4,
    (12.0, 1.75): 0.6,
    (14.0, 2.0): 0.6,
    (16.0, 2.0): 0.6,
    (18.0, 2.5): 0.6,
    (20.0, 2.5): 0.8,
}


def fillet_radius(d: float, pitch: float, length: float, t: float) -> float | None:
    """The cited fillet radius, or None when the bolt gets no fillet (R1, L02).

    None off a `FILLET_R` row, and None when the plain shank `length - t` is shorter than `r`,
    where the ring would run into the thread. `t` is `built_thread_length`.
    """
    r = FILLET_R.get((d, pitch))
    if r is None or length - t < r:
        return None
    return r


def tip_cone_length(pitch: float, angle_deg: float) -> float:
    """Axial length of the tip cone: from the minor radius at the end face to the crest radius,
    the radial depth `thread_depth(pitch)` times tan(angle). A built thread this short or shorter
    is not cut: the cone would be all of it (L02: capped and warned, never a thinner tip)."""
    _check_angle("angle", angle_deg)
    return thread_depth(pitch) * math.tan(math.radians(angle_deg))


def tip_cone_fits(pitch: float, t: float) -> bool:
    """True when the built thread `t` is longer than the tip cone, so the cone is cut. The one
    place that decides it: the builder, the closed form and `derive` all call it."""
    return t > tip_cone_length(pitch, TIP_ANGLE_DEG)


def bolt_end_closed_volume(d: float, pitch: float, length: float, s: float, k: float, t: float,
                           tip: bool, r: float | None) -> float:
    """`bolt_closed_volume` less the tip cone when `tip`, plus the fillet ring when `r` is a
    radius: the volume of a bolt with its ends (D-09, D-11). Each oracle raises `ValueError`
    outside its validity, so there is no number for a bolt the oracles cannot judge (L02)."""
    volume = bolt_closed_volume(d, pitch, length, s, k, t)
    if tip:
        volume -= tip_cone_volume(d, pitch, TIP_ANGLE_DEG)
    if r is not None:
        volume += fillet_ring_volume(d, r)
    return volume


# The differential tolerance, as a fraction of the piece an end cut removes or adds (R11, P8):
# 10 times the largest piece error `bench/RESULTS.md` records under `End-cut probe (Phase 5,
# D-10)` -- 2.737e-03, tip 45 degrees on the M2 right-hand rod, one single-run maximum over 46
# honest rows -- rounded up to one significant figure: 10 x 2.737e-03 = 2.737e-02 -> 0.03. The
# whole-part gate cannot see a tip cone or a ring on a long bolt (P8); this one can, and the
# probe's controls (a skipped cut -1.00, a 45 degree cone where 30 is expected +0.73) sit far
# above it. `tests/test_end_oracles.py` re-derives it from the entry.
T_PIECE = 0.03


def piece_refusal(measured: float, oracle: float, what: str) -> str | None:
    """None when the volume an end cut removed or added is inside `T_PIECE` of its oracle's
    piece; otherwise the text naming `what` and the signed relative error (P8).

    `measured` is the precise volume before the cut less after it (or the reverse for a fuse),
    `oracle` the kernel-free volume of that piece. The error is signed: a skipped cut reads -1.
    """
    if not (math.isfinite(oracle) and oracle > 0):
        return f"the {what} oracle {oracle:.6g} mm3 is not a finite positive number"
    rel = measured / oracle - 1.0
    # A negated <=, as in `volume_check`: a NaN volume must not pass.
    if not abs(rel) <= T_PIECE:
        return (f"the {what} is {measured:.6g} mm3 where its oracle says {oracle:.6g} mm3, "
                f"relative error {rel:+.3e}, allowed {T_PIECE:g} of the piece (D-10, R11)")
    return None


def countersink_face_radius(d: float) -> float:
    """Radius at which the nut lead-in countersink opens on the face: `COUNTERSINK_FACE_FACTOR`
    times d / 2, from the field `d` alone (D-12), the one place the builder, the oracle and
    `end_depths` read it."""
    return COUNTERSINK_FACE_FACTOR * d / 2


def end_depths(d: float, pitch: float, clearance: float, s: float,
               m: float) -> tuple[float, float, list[str]]:
    """The countersink depth and the face chamfer depth the builder cuts, and what was capped.

    The countersink is the cone from the face radius `COUNTERSINK_FACE_FACTOR * d / 2` at
    `COUNTERSINK_HALF_ANGLE_DEG` to the root radius, past which it removes no material: depth
    (face radius - root radius) / tan(half angle). The chamfer is the cone from the inscribed
    radius s / 2 at `CHAMFER_ANGLE_DEG`, to the depth it reaches at the hexagon corner. Each
    is capped, with a warning and never a refusal (L02, R5: the user set neither), where the
    oracles' validity (P10) would otherwise fail:

    - face radius at most the void's crest radius d/2 + clearance: the cone cannot cross the
      void, so the countersink is left out (depth 0), naming `clearance`;
    - face radius past s / 2: it would leave the flats and overlap the chamfer, so the
      countersink is left out, naming `s`;
    - 2 * depth above m: the cutters of the two faces would meet, so each depth is capped at
      m / 2, naming `m`. The oracle caps the chamfer by a flat cut at that depth
      (`face_chamfer_volume`), so the builder must cut the same shape.
    """
    if not m > 0:
        raise ValueError(f"m {m:g} mm must be above 0")
    warnings: list[str] = []
    ro, rr = _radii(d, pitch, clearance)
    face_radius = countersink_face_radius(d)
    if face_radius <= ro:
        csk = 0.0
        warnings.append(
            f"clearance {clearance:g}: the nut lead-in countersink opens to {face_radius:.4g} mm "
            f"radius, which does not pass the void's crest radius d/2 + clearance = {ro:.4g} mm, "
            f"so it cannot cross the void and is left out (L15)")
    elif face_radius > s / 2:
        csk = 0.0
        warnings.append(
            f"s {s:g}: the nut lead-in countersink opens to {face_radius:.4g} mm radius, past "
            f"the flats at s / 2 = {s / 2:.4g} mm, so it is left out (L15)")
    else:
        full = (face_radius - rr) / math.tan(math.radians(COUNTERSINK_HALF_ANGLE_DEG))
        csk = min(full, m / 2)
        if csk < full:
            warnings.append(
                f"m {m:g}: the nut lead-in countersinks are cut {csk:.4g} mm deep, not the "
                f"{full:.4g} mm of the model, so they do not meet (L15)")
    corner = s / 2 / math.cos(math.pi / 6)
    chamfer_full = (corner - s / 2) * math.tan(math.radians(CHAMFER_ANGLE_DEG))
    chamfer = min(chamfer_full, m / 2)
    if chamfer < chamfer_full:
        warnings.append(
            f"m {m:g}: the nut face chamfers are cut {chamfer:.4g} mm deep, not the "
            f"{chamfer_full:.4g} mm of the model, so they do not meet (L15)")
    return csk, chamfer, warnings


def nut_end_closed_volume(d: float, pitch: float, s: float, m: float, clearance: float) -> float:
    """`nut_closed_volume` less the two lead-in countersinks and the two face chamfers: the volume
    of a nut with its ends (D-12, R3, R4), at the depths `end_depths` returns (R5 caps them).

    A countersink `end_depths` leaves out (depth 0) removes nothing. Each oracle raises
    `ValueError` outside its validity, so there is no number for a nut they cannot judge (L02).
    """
    csk, chamfer, _ = end_depths(d, pitch, clearance, s, m)
    volume = nut_closed_volume(d, pitch, s, m, clearance)
    if csk > 0:
        volume -= 2 * countersink_volume(d, pitch, clearance, s, countersink_face_radius(d),
                                         COUNTERSINK_HALF_ANGLE_DEG, csk)
    return volume - 2 * face_chamfer_volume(s, s / 2, CHAMFER_ANGLE_DEG, chamfer)


# --- the bolt head chamfer (L19, 06.1 D-03, D-04) ----------------------------------------------


def head_chamfer_depths(s: float, k: float, angle_deg: float) -> tuple[float, float]:
    """The depth the head chamfer model asks for and the depth the builder cuts: (full, cut).

    full is the cone's depth at the hexagon corner, (corner - s / 2) tan(angle), written as
    `end_depths` writes the nut's; cut is the smaller of that and k / 2, which mirrors the nut's
    m / 2 (L15) and leaves the lower half of the head and the bearing face untouched (D-03). The
    one predicate the builder, the closed form, `derive`, the warning and the 422 rule all call,
    so they cannot disagree at the boundary. The cut is capped only when full is above k / 2,
    never at it: an equal depth builds uncapped (D-04). It does not validate its inputs (a
    negative angle never reaches it from the model).
    """
    corner = s / 2 / math.cos(math.pi / 6)
    full = (corner - s / 2) * math.tan(math.radians(angle_deg))
    return full, min(full, k / 2)


def head_chamfer_warnings(s: float, k: float, angle_deg: float) -> list[str]:
    """What `derive` appends for a head chamfer the model accepted: the band warning, then the
    cap warning (D-02, D-04, D-06).

    Nothing for an angle that is not above 0: the sharp head has no chamfer to be off the band
    (tested as `> 0`, never `!= 0`, because the model accepts -0.0). The band warning names
    `head_chamfer` and the band; the cap warning, when the model depth is above k / 2 and the cut
    is capped there, names `head_chamfer` and `k`. A direct construction (D-06) or a defaulted
    angle is capped and warned, never refused; the 422 for an explicit value is
    `head_chamfer_conflict`'s, at the request boundary. Every number is printed with `_plain`, so
    a value is never rounded into a misleading one (L02).
    """
    if not angle_deg > 0:
        return []
    warnings: list[str] = []
    low, high = HEAD_CHAMFER_BAND_DEG
    if not low <= angle_deg <= high:
        warnings.append(
            f"head_chamfer {_plain(angle_deg)}: outside the {_plain(low)} to {_plain(high)} degree "
            f"band of the stated head chamfer model; built as asked (L19)")
    full, cut = head_chamfer_depths(s, k, angle_deg)
    if full > k / 2:
        warnings.append(
            f"head_chamfer {_plain(angle_deg)} and k {_plain(k)}: the head chamfer is cut "
            f"{_plain(cut)} mm deep, k / 2, not the {_plain(full)} mm of the model, so the lower "
            f"half of the head keeps its sharp corners (L19)")
    return warnings


def head_chamfer_conflict(s: float, k: float, angle_deg: float) -> str | None:
    """None unless an explicit `head_chamfer` cuts deeper than k / 2; else the text (D-04, D-05).

    The same threshold as the cap in `head_chamfer_warnings`, both read from `head_chamfer_depths`,
    so no explicit angle builds a part that differs from its model (D-04). The caller supplies s
    and k from the request, or from the model's defaults when only `head_chamfer` was sent (D-05).
    A value that is not finite, an s or k not above 0, or an angle outside 0 < angle < 90 gives
    None, so the model's own 422 keeps naming the bad field. The text begins with the field names
    (the CLI prints no `loc` for this error), has no braces (pydantic formats a custom error from
    its context) and prints only the user's numbers and k / 2, so no rounded figure can read as
    equal to the bound.
    """
    if not (math.isfinite(s) and math.isfinite(k) and math.isfinite(angle_deg)
            and s > 0 and k > 0 and 0 < angle_deg < 90):
        return None
    if not head_chamfer_depths(s, k, angle_deg)[0] > k / 2:
        return None
    return (f"head_chamfer and k: head_chamfer {_plain(angle_deg)} degrees cuts the head corners "
            f"deeper than k / 2 = {_plain(k / 2)} mm at s {_plain(s)} mm; lower head_chamfer or "
            f"raise k")
