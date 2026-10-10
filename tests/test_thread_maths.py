"""The thread maths: the closed form the kernel is judged against and the gate's comparison,
tested without the kernel."""

from __future__ import annotations

import math

import pytest

from bench.thread_spike.maths import PITCH
from screw.calc.thread import (
    MAX_TURNS,
    T_GATE,
    closed_volume,
    fundamental_height,
    root_radius_refusal,
    section_area,
    section_radius,
    thread_depth,
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
    assert refusal.startswith("length and pitch: ")
    assert "250" in refusal
    assert "2026-10-08-a-frontier" in refusal
    assert "{" not in refusal
    assert "}" not in refusal


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
