"""The thread maths: the closed form the kernel is judged against and the gate's comparison,
tested without the kernel."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from bench.thread_spike.maths import PITCH
from screw.calc.thread import (
    FINE_STL_ROWS,
    MAX_TURNS,
    MIN_TAIL_MM,
    T_GATE,
    axial_play,
    basic_minor_diameter,
    bolt_closed_volume,
    built_thread_length,
    closed_volume,
    fine_stl_refusal,
    flank_normal_gap,
    fundamental_height,
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
    volume_check,
)


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


def test_a_pitch_one_part_in_a_billion_inside_the_root_bound_is_accepted_and_outside_refused(
) -> None:
    # The largest pitch with a root radius above 0 for d = 6: d / 2 = 5H/8 at P = 5.5426.
    largest = 6.0 / (2 * thread_depth(1.0))
    assert root_radius_refusal(6.0, largest * (1 - 1e-9)) is None
    refusal = root_radius_refusal(6.0, largest * (1 + 1e-9))
    assert refusal is not None
    assert refusal.startswith("d and pitch: ")
    assert "ISO 68-1:2023" in refusal
    assert "5.54" in refusal   # the largest pitch for d = 6 is 5.5426 mm, named in the text
    assert "{" not in refusal
    assert "}" not in refusal


def _printed_largest_pitch(refusal: str) -> float:
    marker = ", to 6 significant figures, is "
    assert marker in refusal, refusal
    return float(refusal.rsplit(marker, 1)[1])


def test_the_largest_pitch_the_refusal_prints_is_one_the_same_rule_accepts() -> None:
    # `:g` of the supremum rounded to nearest and was refused again for 993 of these 1999
    # diameters (d 1.1 printed 1.01614 against a limit of 1.016136). Feed each printed number back.
    for tenths in range(1, 2000):
        d = tenths / 10
        refusal = root_radius_refusal(d, 1e6)
        assert refusal is not None
        printed = _printed_largest_pitch(refusal)
        assert root_radius_refusal(d, printed) is None, (d, printed)
        # still "the largest": within 6-figure truncation of the supremum, not a timid number
        supremum = d / (2 * thread_depth(1.0))
        assert printed >= supremum * (1 - 1e-5), (d, printed, supremum)


@pytest.mark.parametrize("d", [1e-300, 0.0001, 1.1, 6.0, 1e5])
def test_the_largest_pitch_is_accepted_across_the_range_of_d(d: float) -> None:
    refusal = root_radius_refusal(d, 1e300)
    assert refusal is not None
    assert root_radius_refusal(d, _printed_largest_pitch(refusal)) is None


def test_a_d_with_no_representable_accepted_pitch_prints_no_number() -> None:
    # d = 5e-324: d / 2 underflows to 0 and every pitch has a root radius of 0 or below, so any
    # pitch printed would be a plausible number the rule refuses (L02). The refusal stands alone.
    refusal = root_radius_refusal(5e-324, 1.0)
    assert refusal is not None
    assert "largest pitch" not in refusal
    assert refusal.startswith("d and pitch: ")


def test_a_root_radius_of_exactly_zero_is_refused() -> None:
    # `> 0`, not `>= 0`: a zero root radius is a section pinched to a point on the axis.
    pitch = 1.0
    assert root_radius_refusal(2 * thread_depth(pitch), pitch) is not None


def test_the_turn_cap_is_250_and_the_cap_row_is_accepted() -> None:
    assert MAX_TURNS == 250
    assert turn_cap_refusal(250.0, 1.0) is None


def test_one_ulp_past_250_turns_is_refused_naming_both_fields_and_the_run() -> None:
    refusal = turn_cap_refusal(math.nextafter(250.0, math.inf), 1.0)
    assert refusal is not None
    assert refusal.startswith("thread_length, length and pitch: ")
    assert "turns of built thread is past the 250-turn cap" in refusal
    assert "250" in refusal
    assert "2026-10-08-a-frontier" in refusal
    assert "{" not in refusal
    assert "}" not in refusal


def test_turns_past_the_float_range_read_as_infinite_and_are_refused_in_words() -> None:
    # float(Fraction) raises OverflowError above about 1.8e308; the quotient has no finite
    # reading, and "inf turns of built thread is past the 250-turn cap" is true.
    assert turns_of(1e5, 1e-310) == math.inf
    assert turns_of(20.0, 5e-324) == math.inf
    refusal = turn_cap_refusal(20.0, 5e-324)
    assert refusal is not None
    assert "inf turns of built thread is past the 250-turn cap" in refusal


@pytest.mark.parametrize("size", list(PITCH))
def test_every_measured_250_turn_row_is_accepted(size: str) -> None:
    _, pitch = PITCH[size]
    assert turn_cap_refusal(float(250 * pitch), float(pitch)) is None


def test_the_exact_decimal_reading_accepts_what_float_division_would_refuse() -> None:
    # Pitfall 2: 175 / 0.7 is a float above 250 although the user typed exactly 250 turns,
    # and the exact binary value of 0.6 would refuse M3.5 at 150 mm.
    assert 175.0 / 0.7 > 250
    assert turns_of(175.0, 0.7) == 250.0
    assert turn_cap_refusal(175.0, 0.7) is None
    assert 5.4 / 0.6 != 9.0
    assert turns_of(5.4, 0.6) == 9.0


# Typed, not read back from the code under test: the seven right-hand rows from L11's "Turn cap
# per size" table and the six left-hand rows from the D-21 clarification (the cap is the longest
# measured length below the first over-budget one), with the printed turns column. M8 left-hand
# has no row: `2026-10-08-a-grid` measured no length over budget up to 80 mm.
L11_ROWS = {
    (8.0, 1.25, False): (67.5, "54"), (10.0, 1.5, False): (56.0, "37.3333"),
    (12.0, 1.75, False): (60.0, "34.2857"), (14.0, 2.0, False): (58.0, "29"),
    (16.0, 2.0, False): (52.0, "26"), (18.0, 2.5, False): (65.0, "26"),
    (20.0, 2.5, False): (64.0, "25.6"),
    (10.0, 1.5, True): (72.0, "48"), (12.0, 1.75, True): (77.0, "44"),
    (14.0, 2.0, True): (78.0, "39"), (16.0, 2.0, True): (75.0, "37.5"),
    (18.0, 2.5, True): (91.0, "36.4"), (20.0, 2.5, True): (91.0, "36.4"),
}

GRID = Path(__file__).parents[1] / "bench" / "results" / "thread-spike" / "2026-10-08-a-grid.jsonl"
EXPORT_BUDGET = 64 * 1024 * 1024


def test_the_fine_stl_table_is_exactly_the_thirteen_rows_l11_measured() -> None:
    assert {key: cap for key, (cap, _) in L11_ROWS.items()} == FINE_STL_ROWS
    assert len(FINE_STL_ROWS) == 13


def test_every_cap_is_the_longest_measured_length_that_fits_in_the_grid_records() -> None:
    """Recompute each cap from the committed records, so a typed cap they do not hold fails.

    A key exists only for a (d, pitch, left_hand) with at least one built rod row whose fine raw
    STL plus its gzip level-1 copy is over 64 MiB; its cap is the longest measured length below
    the first such row. The grid's sizes and hands with none (M2 to M7 on both hands and M8
    left-hand, planner check 2026-10-11) produce no key, so they are uncapped.
    """
    built: dict[tuple[float, float, bool], list[tuple[float, int]]] = {}
    for line in GRID.read_text().splitlines():
        record = json.loads(line)
        if record.get("kind") != "rod" or record["outcome"] != "built":
            continue
        (fine,) = [m for m in record["meshes"] if m["preset"] == "fine"]
        key = (record["d"], record["pitch"], record["left_hand"])
        built.setdefault(key, []).append(
            (record["length"], fine["bytes"] + fine["gzip1_bytes"]))
    recomputed: dict[tuple[float, float, bool], float] = {}
    for key, measured in built.items():
        over = [length for length, size in measured if size > EXPORT_BUDGET]
        if over:
            recomputed[key] = max(length for length, _ in measured if length < min(over))
    assert recomputed == FINE_STL_ROWS


@pytest.mark.parametrize(("key", "row"), list(L11_ROWS.items()))
def test_each_cap_is_accepted_and_the_next_float_above_is_refused(
        key: tuple[float, float, bool], row: tuple[float, str]) -> None:
    (d, pitch, left_hand), (cap, turns) = key, row
    assert fine_stl_refusal(d, pitch, cap, left_hand) is None
    refusal = fine_stl_refusal(d, pitch, math.nextafter(cap, math.inf), left_hand)
    assert refusal is not None
    assert refusal.startswith("thread_length and length: ")
    assert ("left-hand" if left_hand else "right-hand") in refusal
    assert f"{cap:g} mm of thread ({turns} turns)" in refusal
    assert "fine STL plus its gzip copy" in refusal
    assert "64 MiB export budget" in refusal
    assert "2026-10-08-a-grid" in refusal
    assert "preview STL" in refusal
    assert "{" not in refusal
    assert "}" not in refusal


def test_the_refusal_names_the_cap_the_run_and_the_length_asked() -> None:
    refusal = fine_stl_refusal(8.0, 1.25, 67.6, False)
    assert refusal is not None
    assert refusal.startswith("thread_length and length: ")
    assert "the thread built here is 67.6 mm" in refusal
    assert "67.5" in refusal
    assert "54" in refusal
    assert "2026-10-08-a-grid" in refusal
    assert "67.6" in refusal


def test_a_left_hand_part_is_refused_by_the_left_hand_cap_not_the_right_hand_one() -> None:
    # L11 measured the left-hand M10 x 60 inside the budget and the right-hand one over it.
    assert fine_stl_refusal(10.0, 1.5, 60.0, True) is None
    assert fine_stl_refusal(10.0, 1.5, 60.0, False) is not None
    # M8 left-hand fits to 80 mm in the records: no measured stop, so no cap (L02).
    assert fine_stl_refusal(8.0, 1.25, 80.0, True) is None
    assert fine_stl_refusal(8.0, 1.25, 67.6, False) is not None


def test_an_off_row_part_has_no_bytes_cap_not_the_nearest_rows() -> None:
    # An unmeasured mapping to the nearest row is the plausible number L02 forbids (D-03).
    assert fine_stl_refusal(8.0, 1.0, 250.0, False) is None
    assert fine_stl_refusal(8.1, 1.25, 100.0, False) is None
    assert fine_stl_refusal(6.0, 1.0, 250.0, False) is None
    assert fine_stl_refusal(8.0, 1.0, 250.0, True) is None


@pytest.mark.parametrize(("thread_length", "length", "built"), [
    (20.0, 10.0, 10.0),            # the default 20 below an explicit length: built to the length
    (18.0, 30.0, 18.0),            # a shank of 12 mm
    (30.0, 30.0, 30.0),            # no shank
    (19.9995, 20.0, 20.0),         # a 0.0005 mm shank is folded into the thread (D-27)
    (19.999, 20.0, 19.999),        # a 0.001 mm shank is kept: the fold is strictly below the floor
])
def test_the_built_thread_is_the_thread_length_capped_at_the_length_and_a_sliver_is_folded(
        thread_length: float, length: float, built: float) -> None:
    assert built_thread_length(thread_length, length) == built


def test_the_shank_floor_is_a_thousandth_of_a_millimetre() -> None:
    assert MIN_TAIL_MM == 1e-3


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
