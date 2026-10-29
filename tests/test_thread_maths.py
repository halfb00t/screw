"""The thread maths: the closed form the kernel is judged against and the gate's comparison,
tested without the kernel."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from bench.thread_spike.maths import PITCH
from screw.calc import cost, download_refusal
from screw.calc.thread import (
    HEAD_CHAMFER_BAND_DEG,
    MAX_TURNS,
    MIN_ROOT_RADIUS_MM,
    MIN_TAIL_MM,
    T_GATE,
    axial_play,
    basic_minor_diameter,
    bolt_closed_volume,
    built_thread_length,
    closed_volume,
    flank_normal_gap,
    fundamental_height,
    head_chamfer_conflict,
    head_chamfer_depths,
    head_chamfer_warnings,
    head_too_small_refusal,
    hex_prism_volume,
    pitch_diameter,
    root_radius_refusal,
    section_area,
    section_radius,
    thread_depth,
    thread_length_conflict,
    turn_cap_refusal,
    turns_of,
    void_root_radius_refusal,
    volume_check,
)
from screw.params import NutParams


def test_the_basic_profile_has_the_coefficients_the_owner_confirmed() -> None:
    # An independently typed value: 5/8 * sqrt(3)/2 for P = 1, not the code's own expression.
    assert fundamental_height(1.0) == pytest.approx(0.866025403784439, abs=1e-12)
    assert thread_depth(1.0) == pytest.approx(0.541265877365274, abs=1e-12)


def test_the_section_is_a_crest_flat_a_root_flat_and_two_linear_flanks() -> None:
    d, pitch = 6.0, 1.0
    ro, rr = d / 2, d / 2 - thread_depth(pitch)
    assert section_radius(d, pitch, 0.0, 0.0) == ro
    assert section_radius(d, pitch, 0.0, math.pi / 8) == pytest.approx(ro)
    assert section_radius(d, pitch, 0.0, math.pi) == rr
    assert section_radius(d, pitch, 0.0, 3 * math.pi / 4) == pytest.approx(rr)
    assert section_radius(d, pitch, 0.0, (math.pi / 8 + 3 * math.pi / 4) / 2) == (
        pytest.approx((ro + rr) / 2))
    assert section_radius(d, pitch, 0.0, 2 * math.pi) == ro  # taken modulo 2 pi
    # The back flank climbs from rr at 5pi/4 to ro at 15pi/8: four fifths of the way at 7pi/4.
    assert section_radius(d, pitch, 0.0, 7 * math.pi / 4) == pytest.approx(rr + 0.8 * (ro - rr))
    assert section_radius(d, pitch, 0.2, 0.0) == pytest.approx(ro + 0.2)


@pytest.mark.parametrize("clearance", [0.0, 0.2])
def test_the_section_area_is_half_the_integral_of_the_radius_squared(clearance: float) -> None:
    """A 400 000-point midpoint rule over one turn: the radius is piecewise linear in angle
    with its breaks on multiples of pi/8, which 400 000 points divide exactly, so the rule's
    only error is the second-order one on each quadratic piece."""
    d, pitch = 6.0, 1.0
    points = 400_000
    step = 2 * math.pi / points
    integral = sum(section_radius(d, pitch, clearance, (i + 0.5) * step) ** 2
                   for i in range(points)) * step / 2
    assert section_area(d, pitch, clearance) == pytest.approx(integral, rel=1e-9)


def test_the_closed_volume_is_the_section_area_times_the_length() -> None:
    assert closed_volume(6.0, 1.0, 5.0) == section_area(6.0, 1.0) * 5.0


# `1.0 + 9e-05` itself reads 9.0000000000000674e-05, which is outside the bound, so the
# boundary pairs sit a relative 1e-9 either side of it instead of on it.
INSIDE = T_GATE * (1 - 1e-9)
OUTSIDE = T_GATE * (1 + 1e-9)


@pytest.mark.parametrize("sign", [1.0, -1.0])
def test_a_volume_just_inside_the_gate_passes_on_both_signs(sign: float) -> None:
    assert volume_check(1.0 + sign * INSIDE, 1.0) is None


@pytest.mark.parametrize("sign", [1.0, -1.0])
def test_a_volume_just_outside_the_gate_is_refused_on_both_signs(sign: float) -> None:
    refusal = volume_check(1.0 + sign * OUTSIDE, 1.0)
    assert refusal is not None
    assert "relative error" in refusal
    assert f"{sign * OUTSIDE:+.3e}" in refusal


@pytest.mark.parametrize("measured", [math.nan, math.inf, -math.inf, -1.0, 0.0])
def test_a_volume_that_cannot_be_the_part_is_refused(measured: float) -> None:
    # -1.0 is the inverted solid (reads -2), 0.0 the collapsed one (reads -1), and a NaN would
    # pass a positively written `abs(rel) > T_GATE` test.
    refusal = volume_check(measured, 1.0)
    assert refusal is not None
    assert "relative error" in refusal


@pytest.mark.parametrize("closed", [0.0, -1.0, math.nan, math.inf, -math.inf])
def test_a_closed_form_that_is_not_a_positive_number_is_refused(closed: float) -> None:
    refusal = volume_check(1.0, closed)
    assert refusal is not None
    assert "closed form" in refusal


def test_the_refusal_names_both_volumes_and_the_bound() -> None:
    refusal = volume_check(0.5, 1.0)
    assert refusal is not None
    assert "0.5 mm3" in refusal
    assert "1 mm3" in refusal
    assert "-5.000e-01" in refusal
    assert "9e-05" in refusal


def test_a_pitch_one_part_in_a_billion_inside_the_root_floor_is_accepted_and_outside_refused(
) -> None:
    # The largest pitch whose root radius is at least the floor, for d = 6: P = 5.52408 mm.
    largest = (6.0 / 2 - MIN_ROOT_RADIUS_MM) / thread_depth(1.0)
    assert root_radius_refusal(6.0, largest * (1 - 1e-9)) is None
    refusal = root_radius_refusal(6.0, largest * (1 + 1e-9))
    assert refusal is not None
    assert refusal.startswith("d and pitch: ")
    assert "ISO 68-1:2023" in refusal
    assert "must be at least 0.01 mm" in refusal
    assert "linux/amd64" in refusal
    assert "40646134133" in refusal   # the walls run the floor was measured in
    assert "5.52" in refusal   # the largest pitch for d = 6 is 5.52408 mm, named in the text
    assert "{" not in refusal
    assert "}" not in refusal


def _largest_pitch_at_the_floor(d: float) -> float:
    """The largest float pitch the rule accepts for d, found by stepping from the closed form."""
    pitch = (d / 2 - MIN_ROOT_RADIUS_MM) / thread_depth(1.0)
    while root_radius_refusal(d, pitch) is not None:
        pitch = math.nextafter(pitch, 0.0)
    while root_radius_refusal(d, math.nextafter(pitch, math.inf)) is None:
        pitch = math.nextafter(pitch, math.inf)
    return pitch


@pytest.mark.parametrize("d", [0.1, 1.1, 6.0, 20.0, 1e3])
def test_a_root_radius_at_the_floor_is_accepted_and_the_next_float_pitch_is_refused(
        d: float) -> None:
    pitch = _largest_pitch_at_the_floor(d)
    assert d / 2 - thread_depth(pitch) >= MIN_ROOT_RADIUS_MM
    assert root_radius_refusal(d, pitch) is None
    past = math.nextafter(pitch, math.inf)
    assert d / 2 - thread_depth(past) < MIN_ROOT_RADIUS_MM
    refusal = root_radius_refusal(d, past)
    assert refusal is not None
    assert refusal.startswith("d and pitch: ")


def test_the_void_rule_holds_the_same_floor_with_the_clearance() -> None:
    d, pitch = 2.0, 1.8
    # the clearance that puts the void's root exactly at the floor, found the same way
    clearance = MIN_ROOT_RADIUS_MM - (d / 2 - thread_depth(pitch))
    while void_root_radius_refusal(d, pitch, clearance) is not None:
        clearance = math.nextafter(clearance, math.inf)
    while void_root_radius_refusal(d, pitch, math.nextafter(clearance, -math.inf)) is None:
        clearance = math.nextafter(clearance, -math.inf)
    assert d / 2 - thread_depth(pitch) + clearance >= MIN_ROOT_RADIUS_MM
    below = math.nextafter(clearance, -math.inf)
    assert d / 2 - thread_depth(pitch) + below < MIN_ROOT_RADIUS_MM
    refusal = void_root_radius_refusal(d, pitch, below)
    assert refusal is not None
    assert refusal.startswith("d, pitch and clearance: ")
    assert "must be at least 0.01 mm" in refusal
    assert "{" not in refusal
    assert "}" not in refusal


def _printed_largest_pitch(refusal: str) -> float:
    marker = ", to 6 significant figures, is "
    assert marker in refusal, refusal
    return float(refusal.rsplit(marker, 1)[1])


def test_the_largest_pitch_the_refusal_prints_is_one_the_same_rule_accepts() -> None:
    # `:g` of the supremum rounded to nearest and was refused again for 993 of these 1999
    # diameters (d 1.1 printed 1.01614 against a limit of 1.016136). Feed each printed number back.
    # d 0.1 .. 0.2 leave a radius under twice the floor for some pitches, and the floor itself
    # takes d 0.02 away: every d here is above it, so every d has a pitch to print.
    for tenths in range(1, 2000):
        d = tenths / 10
        refusal = root_radius_refusal(d, 1e6)
        assert refusal is not None
        printed = _printed_largest_pitch(refusal)
        assert root_radius_refusal(d, printed) is None, (d, printed)
        # still "the largest": within 6-figure truncation of the supremum, not a timid number
        supremum = (d / 2 - MIN_ROOT_RADIUS_MM) / thread_depth(1.0)
        assert printed >= supremum * (1 - 1e-5), (d, printed, supremum)


@pytest.mark.parametrize("d", [0.0201, 1.1, 6.0, 1e5])
def test_the_largest_pitch_is_accepted_across_the_range_of_d(d: float) -> None:
    refusal = root_radius_refusal(d, 1e300)
    assert refusal is not None
    assert root_radius_refusal(d, _printed_largest_pitch(refusal)) is None


@pytest.mark.parametrize("d", [5e-324, 1e-300, 0.0001, 0.0199])
def test_a_d_with_no_accepted_pitch_prints_no_number(d: float) -> None:
    # d under twice the floor: even a pitch of 0+ leaves a root radius of d / 2 or less, under the
    # floor, so every pitch is refused and any pitch printed would be a plausible number the rule
    # refuses (L02). The refusal stands alone. (d = 5e-324: d / 2 underflows to 0.)
    refusal = root_radius_refusal(d, 1.0)
    assert refusal is not None
    assert "largest pitch" not in refusal
    assert refusal.startswith("d and pitch: ")
    assert root_radius_refusal(d, 1e-300) is not None


def test_a_root_radius_of_exactly_zero_is_refused() -> None:
    # Far under the floor, and the case the old rule (`> 0`) was written for: a zero root radius
    # is a section pinched to a point on the axis.
    pitch = 1.0
    assert root_radius_refusal(2 * thread_depth(pitch), pitch) is not None


def test_the_turn_cap_is_90_and_the_cap_row_is_accepted() -> None:
    # Typed, not read back: T = 90 from walls run 40646134133, the walk-down run 40652801529 and
    # the confirm run 40678150220 (tests/test_oper_followup.py recomputes it from the records).
    assert MAX_TURNS == 90
    assert turn_cap_refusal(90.0, 1.0) is None


def test_one_ulp_past_90_turns_is_refused_naming_both_fields_and_the_runs() -> None:
    refusal = turn_cap_refusal(math.nextafter(90.0, math.inf), 1.0)
    assert refusal is not None
    assert refusal.startswith("thread_length, length and pitch: ")
    assert "turns of built thread is past the 90-turn cap" in refusal
    assert "linux/amd64" in refusal
    for run in ("40646134133", "40652801529", "40678150220"):
        assert run in refusal
    assert "2026-10-08-a-frontier" not in refusal
    assert "{" not in refusal
    assert "}" not in refusal


def test_turns_past_the_float_range_read_as_infinite_and_are_refused_in_words() -> None:
    # float(Fraction) raises OverflowError above about 1.8e308; the quotient has no finite
    # reading, and "inf turns of built thread is past the 90-turn cap" is true.
    assert turns_of(1e5, 1e-310) == math.inf
    assert turns_of(20.0, 5e-324) == math.inf
    refusal = turn_cap_refusal(20.0, 5e-324)
    assert refusal is not None
    assert "inf turns of built thread is past the 90-turn cap" in refusal


@pytest.mark.parametrize("size", list(PITCH))
def test_every_size_is_accepted_at_the_cap(size: str) -> None:
    _, pitch = PITCH[size]
    assert turn_cap_refusal(float(MAX_TURNS * pitch), float(pitch)) is None


def test_the_exact_decimal_reading_accepts_what_float_division_would_refuse() -> None:
    # Pitfall 2: 2.7 / 0.03 is a float above 90 although the user typed exactly 90 turns,
    # and the exact binary value of 0.6 would refuse M3.5 at 54 mm.
    assert 2.7 / 0.03 > 90
    assert turns_of(2.7, 0.03) == 90.0
    assert turn_cap_refusal(2.7, 0.03) is None
    assert 5.4 / 0.6 != 9.0
    assert turns_of(5.4, 0.6) == 9.0


@pytest.mark.parametrize(("thread_length", "length", "built"), [
    (20.0, 10.0, 10.0),            # the default 20 below an explicit length: built to the length
    (18.0, 30.0, 18.0),            # a shank of 12 mm
    (30.0, 30.0, 30.0),            # no shank
    (4.99995, 5.0, 5.0),           # a 0.00005 mm shank is folded into the thread (D-27)
    (4.9998, 5.0, 4.9998),         # a 0.0002 mm shank is kept: the fold is strictly below the floor
    (19.999, 20.0, 19.999),        # a 0.001 mm shank was folded before L20 and is kept now
])
def test_the_built_thread_is_the_thread_length_capped_at_the_length_and_a_sliver_is_folded(
        thread_length: float, length: float, built: float) -> None:
    assert built_thread_length(thread_length, length) == built


def test_the_shank_floor_is_a_ten_thousandth_of_a_millimetre() -> None:
    # Typed, not read back: 1e-4 mm, 100 x the largest failing tail (1e-6 mm) of walls run
    # 40646134133 (R9), confirmed in 5 repetitions at 1e-4 and 1e-5 mm by run 40678150220.
    assert MIN_TAIL_MM == 1e-4


def test_a_hex_prism_is_the_hexagon_area_times_the_height() -> None:
    # 200 * sqrt(3) typed independently of the code's (sqrt(3) / 2) * s * s * k: the hexagon of
    # across-flats 10 has area 50 * sqrt(3) mm2, times the head height 4.
    assert hex_prism_volume(10.0, 4.0) == pytest.approx(200 * math.sqrt(3), abs=1e-9)


def test_the_whole_bolt_is_the_thread_plus_the_head() -> None:
    thread = closed_volume(6.0, 1.0, 20.0)
    assert bolt_closed_volume(6.0, 1.0, 20.0, 10.0, 4.0, 20.0) == pytest.approx(
        thread + hex_prism_volume(10.0, 4.0), abs=1e-9)


def test_a_shorter_thread_leaves_a_plain_cylinder_for_the_rest_of_the_length() -> None:
    # Plan 04-04 passes a thread length t below the length: the shank t..length is a cylinder of
    # the major diameter, pi * (d / 2)^2 * (length - t), here typed out for d 6 and 8 mm of it.
    shank = math.pi * 9.0 * 8.0
    assert bolt_closed_volume(6.0, 1.0, 20.0, 10.0, 4.0, 12.0) == pytest.approx(
        section_area(6.0, 1.0) * 12.0 + shank + hex_prism_volume(10.0, 4.0), abs=1e-9)


@pytest.mark.parametrize(("s", "d"), [(6.0, 6.0), (5.0, 6.0), (1e-3, 1e5)])
def test_a_head_no_wider_than_the_shank_is_refused_naming_both_fields(s: float, d: float) -> None:
    text = head_too_small_refusal(s, d)
    assert text is not None
    assert text.startswith("s and d: ")
    assert "must exceed" in text
    assert "{" not in text  # pydantic formats a custom error from its context


def test_a_head_one_ulp_wider_than_the_shank_is_accepted() -> None:
    assert head_too_small_refusal(math.nextafter(6.0, math.inf), 6.0) is None
    assert head_too_small_refusal(10.0, 6.0) is None


def test_a_thread_length_above_the_length_is_a_conflict_with_the_pinned_text() -> None:
    # D-25. 10.00001 is the case `:g` would print as 10: the text must still tell the two apart.
    assert thread_length_conflict(10.0, 10.00001) == (
        "thread_length and length: thread_length 10.00001 mm is longer than length 10 mm; "
        "shorten thread_length or lengthen length")
    text = thread_length_conflict(10.0, 30.0)
    assert text is not None
    assert text.startswith("thread_length and length: ")
    assert "thread_length 30 mm is longer than length 10 mm" in text
    assert "{" not in text
    assert "}" not in text


@pytest.mark.parametrize(("length", "thread_length"), [
    (10.0, 10.0), (10.0, 9.99999), (30.0, 18.0),
    # not finite, or not above 0: left to the model's own 422, which names the bad field
    (math.inf, 5.0), (10.0, math.inf), (math.nan, 5.0), (10.0, math.nan),
    (0.0, 5.0), (-5.0, 10.0), (10.0, 0.0), (10.0, -1.0), (-math.inf, 5.0),
])
def test_equal_shorter_and_unusable_values_are_no_conflict(
        length: float, thread_length: float) -> None:
    assert thread_length_conflict(length, thread_length) is None


# --- the bolt head chamfer's band, cap warning and conflict (06.1 D-02, D-04, D-06) -----------


def _cap_text(angle: str, k: str, cut: str, full: float) -> str:
    return (f"head_chamfer {angle} and k {k}: the head chamfer is cut {cut} mm deep, k / 2, not "
            f"the {repr(full).removesuffix('.0')} mm of the model, so the lower half of the head "
            "keeps its sharp corners (L19)")


def _band_text(angle: str) -> str:
    return (f"head_chamfer {angle}: outside the 15 to 30 degree band of the stated head chamfer "
            "model; built as asked (L19)")


def test_the_head_chamfer_band_is_15_to_30_degrees() -> None:
    assert HEAD_CHAMFER_BAND_DEG == (15.0, 30.0)


@pytest.mark.parametrize("angle", [0.0, -0.0, 15.0, 20.0, 30.0])
def test_a_head_chamfer_inside_the_band_or_sharp_warns_of_nothing(angle: float) -> None:
    """Both band edges are inside it, and 0 (also -0.0, which the model accepts) is the sharp
    head, not an off-band angle."""
    assert head_chamfer_warnings(10.0, 4.0, angle) == []


@pytest.mark.parametrize("angle", [14.999, 30.001, 1e-3, 45.0])
def test_a_head_chamfer_outside_the_band_warns_naming_the_field_and_the_band(
        angle: float) -> None:
    assert head_chamfer_warnings(10.0, 4.0, angle) == [_band_text(repr(angle).removesuffix('.0'))]
    assert head_chamfer_warnings(10.0, 4.0, 14.999)[0] == (
        "head_chamfer 14.999: outside the 15 to 30 degree band of the stated head chamfer model; "
        "built as asked (L19)")


def test_a_head_chamfer_deeper_than_half_k_warns_naming_head_chamfer_and_k() -> None:
    full = head_chamfer_depths(10.0, 4.0, 80.0)[0]
    # Off the band and capped: the band warning first, the cap warning second.
    assert head_chamfer_warnings(10.0, 4.0, 80.0) == [_band_text("80"),
                                                      _cap_text("80", "4", "2", full)]
    # In the band and capped: only the cap.
    full = head_chamfer_depths(100.0, 4.0, 30.0)[0]
    assert head_chamfer_warnings(100.0, 4.0, 30.0) == [_cap_text("30", "4", "2", full)]
    # Equal to k / 2 builds uncapped and says nothing.
    full = head_chamfer_depths(10.0, 1e9, 30.0)[0]
    assert head_chamfer_warnings(10.0, 2 * full, 30.0) == []


def test_a_sharp_head_chamfer_of_zero_warns_of_nothing_even_where_k_is_tiny() -> None:
    assert head_chamfer_warnings(100.0, 0.001, 0.0) == []
    assert head_chamfer_warnings(100.0, 0.001, -0.0) == []


def test_an_explicit_head_chamfer_deeper_than_half_k_is_a_conflict_with_the_pinned_text() -> None:
    assert head_chamfer_conflict(10.0, 4.0, 80.0) == (
        "head_chamfer and k: head_chamfer 80 degrees cuts the head corners deeper than "
        "k / 2 = 2 mm at s 10 mm; lower head_chamfer or raise k")
    text = head_chamfer_conflict(100.0, 4.0, 30.0)
    assert text == (
        "head_chamfer and k: head_chamfer 30 degrees cuts the head corners deeper than "
        "k / 2 = 2 mm at s 100 mm; lower head_chamfer or raise k")
    assert "{" not in text
    assert "}" not in text
    # The same threshold as the cap: equal is no conflict, one ulp under is.
    assert head_chamfer_conflict(10.0, 4.0, 30.0) is None
    full = head_chamfer_depths(10.0, 1e9, 30.0)[0]
    assert head_chamfer_conflict(10.0, 2 * full, 30.0) is None
    assert head_chamfer_conflict(10.0, math.nextafter(2 * full, 0.0), 30.0) is not None


@pytest.mark.parametrize(("s", "k", "angle"), [
    # not finite: left to the model's own 422, which names the bad field
    (math.nan, 4.0, 80.0), (math.inf, 4.0, 80.0), (10.0, math.nan, 80.0),
    (10.0, math.inf, 80.0), (10.0, 4.0, math.nan), (10.0, 4.0, math.inf),
    # not above 0
    (0.0, 4.0, 80.0), (-10.0, 4.0, 80.0), (10.0, 0.0, 80.0), (10.0, -4.0, 80.0),
    # an angle the model refuses: 0 is the sharp head, 90 and above are a 422 on the field
    (10.0, 4.0, 0.0), (10.0, 4.0, -1.0), (10.0, 4.0, 90.0), (10.0, 4.0, 91.0),
])
def test_unusable_values_are_no_head_chamfer_conflict(s: float, k: float, angle: float) -> None:
    assert head_chamfer_conflict(s, k, angle) is None


def test_the_basic_pitch_and_minor_diameters_are_the_iso_68_1_formulas() -> None:
    h = fundamental_height(1.0)
    assert pitch_diameter(6.0, 1.0) == 6.0 - 0.75 * h
    assert basic_minor_diameter(6.0, 1.0) == 6.0 - 1.25 * h


@pytest.mark.parametrize("pitch", [0.4, 1.0, 1.25, 2.5])
def test_the_basic_minor_diameter_is_the_shank_minor_diameter_row_formula(pitch: float) -> None:
    assert basic_minor_diameter(10.0, pitch) == pytest.approx(
        10.0 - 2 * thread_depth(pitch), abs=1e-15
    )


# --- the pair's closed-form gaps, pinned to the section they come from (PAIR-01, RESEARCH F7) ---


def _flank_slope(d: float, pitch: float, clearance: float, theta: float) -> float:
    """dr/dz over a flank by central difference, theta mapped to z = theta * pitch / (2 pi)."""
    h = 1e-3
    dr = (section_radius(d, pitch, clearance, theta + h)
          - section_radius(d, pitch, clearance, theta - h))
    return dr / (2 * h) * (2 * math.pi / pitch)


@pytest.mark.parametrize(("d", "pitch"), [(6.0, 1.0), (10.0, 1.5), (20.0, 2.5), (2.0, 0.4)])
def test_both_flanks_rise_sqrt_3_mm_per_mm_of_z(d: float, pitch: float) -> None:
    # The first flank falls from the crest to the root, the second rises back: 30 degrees from the
    # axis-normal plane on both, whatever the size or the clearance.
    for clearance in (0.0, 0.05, -0.05):
        down = _flank_slope(d, pitch, clearance, math.pi / 2)
        up = _flank_slope(d, pitch, clearance, 3 * math.pi / 2)
        assert down == pytest.approx(-math.sqrt(3), abs=1e-9)
        assert up == pytest.approx(math.sqrt(3), abs=1e-9)


@pytest.mark.parametrize("clearance", [0.0, 0.05, 0.1, 0.25, -0.05])
def test_the_flank_and_axial_gaps_follow_the_numeric_slope_not_a_typed_factor(
        clearance: float) -> None:
    slope = abs(_flank_slope(6.0, 1.0, 0.0, math.pi / 2))
    angle = math.atan(1 / slope)    # flank angle from the axis-normal plane
    assert math.degrees(angle) == pytest.approx(30.0, abs=1e-7)
    # Moving the surface radially by c shifts each flank c / slope along z; the normal gap is the
    # radial shift projected on the flank normal.
    assert flank_normal_gap(clearance) == pytest.approx(clearance * math.sin(angle), abs=1e-12)
    assert axial_play(clearance) == pytest.approx(2 * clearance / slope, abs=1e-12)


def test_the_clearance_moves_the_section_radius_by_exactly_c_at_every_angle() -> None:
    # The premise of both gaps: the nut surface is the rod surface moved radially by c.
    for i in range(64):
        theta = 2 * math.pi * i / 64
        assert section_radius(6.0, 1.0, 0.1, theta) - section_radius(6.0, 1.0, 0.0, theta) == (
            pytest.approx(0.1, abs=1e-12))


def test_the_gaps_are_zero_at_zero_clearance_and_negative_for_an_interference() -> None:
    assert flank_normal_gap(0.0) == 0.0
    assert axial_play(0.0) == 0.0
    assert flank_normal_gap(-0.05) < 0
    assert axial_play(-0.05) < 0


# --- the retired caps (07 D-08, D-17; L21) -------------------------------------------------------

_RETIRED = ("FINE_STL_ROWS", "fine_stl_refusal", "NUT_FINE_STL_RUN", "NUT_FINE_STL_CLEARANCE",
            "NUT_FINE_STL_ROWS", "nut_fine_stl_refusal")


def test_no_retired_cap_name_is_left_in_the_source() -> None:
    # The cost model of L21 is the only download rule (T-07-34): a retired table left in `src/`
    # could be called again by a front end and refuse or admit by a stale rule.
    src = Path(__file__).parents[1] / "src"
    hits = [f"{path.relative_to(src)}: {name}" for path in sorted(src.rglob("*.py"))
            for name in _RETIRED if name in path.read_text()]
    assert hits == []


def test_a_nut_above_the_retired_clearance_ceiling_is_judged_by_the_cost_model_alone() -> None:
    # M6 x 1 right was one of the 30 retired keys, and clearance 6 is above its 5.0 mm ceiling,
    # which refused it (D-17 retires that refusal). s 20 makes the nut valid (s > d + 2 c).
    p = NutParams(clearance=6.0, s=20.0)
    assert download_refusal(p, "stl", "fine") == cost.refusal(p, "stl-fine")
