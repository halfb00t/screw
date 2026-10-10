"""The thread maths: the closed form the kernel is judged against and the gate's comparison,
tested without the kernel."""

from __future__ import annotations

import math

import pytest

from screw.calc.thread import (
    T_GATE,
    closed_volume,
    fundamental_height,
    section_area,
    section_radius,
    thread_depth,
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
