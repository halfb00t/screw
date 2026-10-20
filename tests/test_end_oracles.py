"""The end-cut oracles of `screw.calc.thread`, each pinned to an identity that does not use it.

Kernel-free: nothing here imports `cadquery`, so these run on every `make verify` without the
bench. The first hexagon-arc formula written for 05-RESEARCH F4 was off by a factor of 2.2, so a
wrong formula must fail at least one test below (planted-error check recorded in the plan 05-11
SUMMARY). The oracles' agreement with the kernel is the probe entry in `bench/RESULTS.md`.
"""

from __future__ import annotations

import math
from collections.abc import Iterable

import pytest

from screw.calc import thread as t

SECTIONS = ((2.0, 0.4), (6.0, 1.0), (10.0, 1.5), (20.0, 2.5))
# The quadrature must be invisible next to the gate that reads the piece (05-11 truth).
QUADRATURE = t.T_GATE / 100


def _angle_midpoints(n: int) -> Iterable[float]:
    return ((i + 0.5) * 2 * math.pi / n for i in range(n))


def _radii_squared(d: float, pitch: float, clearance: float, n: int) -> list[float]:
    """r(theta)^2 of the section at `n` midpoint angles, read from `section_radius`."""
    return [t.section_radius(d, pitch, clearance, th) ** 2 for th in _angle_midpoints(n)]


# --- outside_disc_area -----------------------------------------------------------------------


@pytest.mark.parametrize(("d", "pitch"), SECTIONS)
@pytest.mark.parametrize("clearance", [-0.05, 0.0, 0.1])
def test_the_area_outside_a_disc_of_radius_zero_is_the_whole_section(
        d: float, pitch: float, clearance: float) -> None:
    assert t.outside_disc_area(d, pitch, clearance, 0.0) == pytest.approx(
        t.section_area(d, pitch, clearance), rel=1e-12)


@pytest.mark.parametrize(("d", "pitch"), SECTIONS)
@pytest.mark.parametrize("clearance", [-0.05, 0.0, 0.1])
def test_the_area_outside_the_crest_radius_is_zero(d: float, pitch: float,
                                                   clearance: float) -> None:
    crest = d / 2 + clearance
    assert t.outside_disc_area(d, pitch, clearance, crest) == 0.0
    assert t.outside_disc_area(d, pitch, clearance, crest + 1.0) == 0.0


@pytest.mark.parametrize(("d", "pitch"), SECTIONS)
def test_the_area_outside_a_disc_is_continuous_at_the_root_and_crest_radii(
        d: float, pitch: float) -> None:
    clearance = 0.1
    crest, root = t._radii(d, pitch, clearance)
    for edge in (root, crest):
        left = t.outside_disc_area(d, pitch, clearance, math.nextafter(edge, 0.0))
        right = t.outside_disc_area(d, pitch, clearance, math.nextafter(edge, math.inf))
        assert left == pytest.approx(right, abs=1e-12)


@pytest.mark.parametrize(("d", "pitch"), SECTIONS)
def test_the_area_outside_a_disc_matches_an_integral_over_the_section_angle(
        d: float, pitch: float) -> None:
    """Half the integral of max(0, r^2 - rho^2) over the angle, r from `section_radius`: a route
    that shares no arithmetic with the closed form."""
    clearance = 0.1
    crest, root = t._radii(d, pitch, clearance)
    n = 100_000
    squares = _radii_squared(d, pitch, clearance, n)
    for rho in (0.5 * root, root, (root + crest) / 2, 0.99 * crest):
        integral = 0.5 * sum(max(0.0, r2 - rho * rho) for r2 in squares) * 2 * math.pi / n
        assert t.outside_disc_area(d, pitch, clearance, rho) == pytest.approx(integral, rel=1e-6)


@pytest.mark.parametrize("rho", [-1.0, -1e-9, math.nan])
def test_the_area_outside_a_negative_or_missing_radius_is_refused_naming_rho(rho: float) -> None:
    with pytest.raises(ValueError, match="rho"):
        t.outside_disc_area(6.0, 1.0, 0.1, rho)


@pytest.mark.parametrize(("d", "pitch"), SECTIONS)
def test_nut_material_in_a_disc_matches_an_integral_over_the_section_angle(
        d: float, pitch: float) -> None:
    """The disc less what the void takes of it, half the integral of min(r, rho)^2 over the
    angle; nothing inside the root circle."""
    clearance = 0.1
    crest, root = t._radii(d, pitch, clearance)
    n = 100_000
    squares = _radii_squared(d, pitch, clearance, n)
    assert t.nut_material_in_disc(d, pitch, clearance, 0.9 * root) == pytest.approx(0.0, abs=1e-9)
    for rho in (1.1 * crest, 1.5 * crest):
        void = 0.5 * sum(min(r2, rho * rho) for r2 in squares) * 2 * math.pi / n
        assert t.nut_material_in_disc(d, pitch, clearance, rho) == pytest.approx(
            math.pi * rho * rho - void, rel=1e-6)


# --- the hexagon arc and the face chamfer ----------------------------------------------------


def test_the_hexagon_arc_is_a_full_circle_inside_the_inscribed_circle_and_nothing_past_a_corner(
        ) -> None:
    s = 10.0
    for rho in (0.1, 2.5, 5.0):
        assert t.hex_arc_inside(s, rho) == pytest.approx(2 * math.pi * rho, rel=1e-12)
    assert t.hex_arc_inside(s, s / 2 / math.cos(math.pi / 6) + 0.01) == 0.0


@pytest.mark.parametrize("s", [4.0, 10.0, 30.0])
def test_the_hexagon_arc_integrates_to_the_hexagon_area(s: float) -> None:
    """The arcs over [0, R] sweep the hexagon: the area is `hex_prism_volume(s, 1)`."""
    corner = s / 2 / math.cos(math.pi / 6)
    n = 200_000
    h = corner / n
    area = h * sum(t.hex_arc_inside(s, (i + 0.5) * h) for i in range(n))
    assert area == pytest.approx(t.hex_prism_volume(s, 1.0), rel=1e-6)


def _polar_chamfer(s: float, r0: float, beta_deg: float, depth: float) -> float:
    """The chamfer volume as a polar integral over the hexagon, with no `hex_arc_inside` in it:
    the radial extent per 60 degree sector is a / cos(phi - 30 degrees), and the depth removed
    at rho is min((rho - r0) tan(beta), depth), integrated over rho exactly per sector."""
    a = s / 2
    tan_beta = math.tan(math.radians(beta_deg))
    n = 100_000
    total = 0.0
    for i in range(n):
        phi = (i + 0.5) * (math.pi / 3) / n
        extent = a / math.cos(phi - math.pi / 6)
        cap = min(extent, r0 + depth / tan_beta)
        total += (tan_beta * ((cap**3 - r0**3) / 3 - r0 * (cap**2 - r0**2) / 2)
                  + depth * (extent**2 - cap**2) / 2) * (math.pi / 3) / n
    return 6 * total


@pytest.mark.parametrize("s", [4.0, 10.0, 30.0])
@pytest.mark.parametrize("start", [1.0, 0.9])
def test_the_face_chamfer_matches_a_polar_integral_over_the_hexagon(s: float,
                                                                    start: float) -> None:
    r0 = start * s / 2
    assert t.face_chamfer_volume(s, r0, 30.0, 1e9) == pytest.approx(
        _polar_chamfer(s, r0, 30.0, 1e9), rel=1e-6)


@pytest.mark.parametrize("s", [4.0, 30.0])
def test_a_capped_face_chamfer_matches_the_polar_integral_and_binds_only_below_the_corner_depth(
        s: float) -> None:
    r0 = s / 2
    corner = s / 2 / math.cos(math.pi / 6)
    full = (corner - r0) * math.tan(math.radians(30.0))
    assert t.face_chamfer_volume(s, r0, 30.0, 0.0) == 0.0
    assert t.face_chamfer_volume(s, r0, 30.0, full) == pytest.approx(
        t.face_chamfer_volume(s, r0, 30.0, 1e9), rel=1e-12)
    half = t.face_chamfer_volume(s, r0, 30.0, full / 2)
    assert 0 < half < t.face_chamfer_volume(s, r0, 30.0, full)
    assert half == pytest.approx(_polar_chamfer(s, r0, 30.0, full / 2), rel=1e-6)


def test_the_face_chamfer_refuses_a_start_an_angle_or_a_depth_outside_its_validity() -> None:
    corner = 10.0 / 2 / math.cos(math.pi / 6)
    with pytest.raises(ValueError, match="chamfer start"):
        t.face_chamfer_volume(10.0, corner, 30.0, 1.0)
    with pytest.raises(ValueError, match="chamfer start"):
        t.face_chamfer_volume(10.0, 0.0, 30.0, 1.0)
    with pytest.raises(ValueError, match="angle"):
        t.face_chamfer_volume(10.0, 5.0, 90.0, 1.0)
    with pytest.raises(ValueError, match="depth"):
        t.face_chamfer_volume(10.0, 5.0, 30.0, -0.1)


# --- the tip cone ----------------------------------------------------------------------------


@pytest.mark.parametrize(("d", "pitch"), [SECTIONS[0], SECTIONS[1], SECTIONS[3]])
@pytest.mark.parametrize("angle", [30.0, 45.0])
def test_the_tip_cone_matches_a_double_integral_over_height_and_angle(
        d: float, pitch: float, angle: float) -> None:
    """M2, M6 and M20: the cone removes, at each height z, half the integral over the angle of
    max(0, r^2 - rho(z)^2) -- a midpoint grid over (z, theta) with no `outside_disc_area` in it."""
    minor = d / 2 - t.thread_depth(pitch)
    tan_alpha = math.tan(math.radians(angle))
    nz, nt = 1000, 4000
    squares = _radii_squared(d, pitch, 0.0, nt)
    h = t.thread_depth(pitch) * tan_alpha / nz
    total = 0.0
    for i in range(nz):
        rho = minor + (i + 0.5) * h / tan_alpha
        total += sum(r2 - rho * rho for r2 in squares if r2 > rho * rho)
    grid = 0.5 * total * (2 * math.pi / nt) * h
    assert t.tip_cone_volume(d, pitch, angle) == pytest.approx(grid, rel=1e-6)


@pytest.mark.parametrize(("d", "pitch"), SECTIONS)
def test_the_tip_cone_matches_the_swapped_integral_and_scales_with_tan_alpha(
        d: float, pitch: float) -> None:
    """Swapping the order of integration, the cone removes tan(alpha) times half the integral
    over the angle of r^2 (r - rr) - (r^3 - rr^3) / 3."""
    root = d / 2 - t.thread_depth(pitch)
    n = 100_000
    radii = [t.section_radius(d, pitch, 0.0, th) for th in _angle_midpoints(n)]
    swapped = 0.5 * sum(r * r * (r - root) - (r**3 - root**3) / 3 for r in radii) * 2 * math.pi / n
    for angle in (30.0, 45.0):
        assert t.tip_cone_volume(d, pitch, angle) == pytest.approx(
            swapped * math.tan(math.radians(angle)), rel=1e-6)


@pytest.mark.parametrize(("d", "pitch"), SECTIONS)
@pytest.mark.parametrize("angle", [30.0, 45.0])
def test_the_tip_cone_quadrature_error_at_the_shipped_point_count_is_invisible_to_the_gate(
        d: float, pitch: float, angle: float) -> None:
    fine = t.tip_cone_volume(d, pitch, angle, n=200_000)
    assert abs(t.tip_cone_volume(d, pitch, angle) / fine - 1) < QUADRATURE


@pytest.mark.parametrize("angle", [0.0, 90.0, -5.0, math.nan])
def test_the_tip_cone_refuses_an_angle_outside_its_validity_naming_it(angle: float) -> None:
    with pytest.raises(ValueError, match="angle"):
        t.tip_cone_volume(6.0, 1.0, angle)


def test_the_tip_cone_refuses_a_minor_radius_at_or_below_zero() -> None:
    with pytest.raises(ValueError, match="minor radius"):
        t.tip_cone_volume(0.5, 1.0, 45.0)


# --- the countersink -------------------------------------------------------------------------

# M6, c 0.1, s 10, face radius d/2 + c + P/2 = 3.6, 45 degrees, to the depth the probe's crossing
# cone ends at (`bench.end_cuts.NutCase.csk_depth`).
M6_CSK = (6.0, 1.0, 0.1, 10.0, 3.6, 45.0, 1.2036456405748563)


def test_the_countersink_matches_a_grid_over_depth_and_section_angle() -> None:
    """The material removed is, at each depth z, the disc less half the integral of min(r, rho)^2
    over the angle: a midpoint grid over (z, theta) with neither `outside_disc_area` nor
    `nut_material_in_disc` in it."""
    d, pitch, c, _, face, half, depth = M6_CSK
    nz, nt = 600, 4000
    squares = _radii_squared(d, pitch, c, nt)
    tan_half = math.tan(math.radians(half))
    h = depth / nz
    total = 0.0
    for i in range(nz):
        rho2 = (face - (i + 0.5) * h * tan_half) ** 2
        total += math.pi * rho2 - 0.5 * sum(min(r2, rho2) for r2 in squares) * 2 * math.pi / nt
    assert t.countersink_volume(*M6_CSK) == pytest.approx(total * h, rel=1e-5)


def test_the_countersink_quadrature_error_at_the_shipped_point_count_is_invisible_to_the_gate(
        ) -> None:
    fine = t.countersink_volume(*M6_CSK, n=200_000)
    assert abs(t.countersink_volume(*M6_CSK) / fine - 1) < QUADRATURE


def test_the_countersink_ends_where_the_cone_leaves_the_material_and_a_longer_depth_adds_nothing(
        ) -> None:
    d, pitch, c, s, face, half, _ = M6_CSK
    root = t._radii(d, pitch, c)[1]
    to_root = (face - root) / math.tan(math.radians(half))
    assert t.countersink_volume(d, pitch, c, s, face, half, 1.2) == pytest.approx(
        t.countersink_volume(d, pitch, c, s, face, half, to_root), rel=1e-4)
    assert t.countersink_volume(d, pitch, c, s, face, half, 0.0) == 0.0


def test_the_countersink_refuses_a_face_radius_past_the_inscribed_circle_naming_it() -> None:
    with pytest.raises(ValueError, match="face radius"):
        t.countersink_volume(6.0, 1.0, 0.1, 10.0, 5.01, 45.0, 0.5)
    with pytest.raises(ValueError, match="face radius"):
        t.countersink_volume(6.0, 1.0, 0.1, 10.0, 0.0, 45.0, 0.5)


def test_the_countersink_refuses_a_depth_past_the_cone_s_apex_or_below_zero_naming_it() -> None:
    with pytest.raises(ValueError, match="depth"):
        t.countersink_volume(6.0, 1.0, 0.1, 10.0, 3.6, 45.0, 3.61)
    with pytest.raises(ValueError, match="depth"):
        t.countersink_volume(6.0, 1.0, 0.1, 10.0, 3.6, 45.0, -0.1)
    with pytest.raises(ValueError, match="half angle"):
        t.countersink_volume(6.0, 1.0, 0.1, 10.0, 3.6, 90.0, 0.5)


# --- the fillet ring -------------------------------------------------------------------------


@pytest.mark.parametrize(("d", "r"), [(6.0, 0.25), (10.0, 0.4), (20.0, 0.8)])
def test_the_fillet_ring_equals_the_revolved_region_integral_and_pappus_with_the_centroid(
        d: float, r: float) -> None:
    """The region is the square r x r less a quarter disc on its far corner. With the offset
    u = r (1 - cos phi) from the shank, its height is r (1 - sin phi) and du = r sin phi dphi:
    revolve by integrating 2 pi (d/2 + u) over the region. And Pappus with the centroid offset
    written the long way (the centroid of the square less that of the quarter disc)."""
    n = 100_000
    h = (math.pi / 2) / n
    total = 0.0
    for i in range(n):
        phi = (i + 0.5) * h
        total += (2 * math.pi * (d / 2 + r * (1 - math.cos(phi))) * r * (1 - math.sin(phi))
                  * r * math.sin(phi) * h)
    assert t.fillet_ring_volume(d, r) == pytest.approx(total, rel=1e-9)
    area = r**2 * (1 - math.pi / 4)
    u_bar = (r**3 / 2 - (math.pi * r**2 / 4) * (r - 4 * r / (3 * math.pi))) / area
    assert t.fillet_ring_volume(d, r) == pytest.approx(
        2 * math.pi * (d / 2 + u_bar) * area, rel=1e-9)


@pytest.mark.parametrize("r", [0.0, -0.25, math.nan])
def test_the_fillet_ring_refuses_a_radius_that_is_not_above_zero_naming_it(r: float) -> None:
    with pytest.raises(ValueError, match="r "):
        t.fillet_ring_volume(6.0, r)


# --- the formulas moved, not rewritten ---------------------------------------------------------


def test_the_oracles_reproduce_the_values_the_probe_computed_before_they_moved() -> None:
    """Pinned from `bench.end_cuts` at 5574dc6, before the move; the M6 countersink also equals
    the 6.49264475 mm3 05-RESEARCH F4 printed for the same case."""
    for rho, expected in ((0.0, 24.682276415072565), (2.0, 12.115905800713389),
                          (2.6, 3.6282815033653693), (3.0, 0.3495836012664334),
                          (3.05, 0.1485665578739514)):
        assert t.outside_disc_area(6.0, 1.0, 0.1, rho) == pytest.approx(expected, rel=1e-12)
    assert t.tip_cone_volume(6.0, 1.0, 30.0) == pytest.approx(0.4894417451591129, rel=1e-12)
    assert t.tip_cone_volume(6.0, 1.0, 45.0) == pytest.approx(0.8477379699607621, rel=1e-12)
    assert t.tip_cone_volume(2.0, 0.4, 45.0) == pytest.approx(0.04443775303885566, rel=1e-12)
    assert t.countersink_volume(*M6_CSK) == pytest.approx(6.49264475069634, rel=1e-12)
    assert t.countersink_volume(*M6_CSK) == pytest.approx(6.49264475, rel=1e-8)
    assert t.face_chamfer_volume(10.0, 5.0, 30.0, 1e9) == pytest.approx(
        1.0855309498188361, rel=1e-12)
    assert t.fillet_ring_volume(6.0, 0.25) == pytest.approx(0.25752785679776874, rel=1e-12)
    assert t.hex_arc_inside(10.0, 5.5) == pytest.approx(6.1973412234937015, rel=1e-12)
    assert t.nut_material_in_disc(6.0, 1.0, 0.1, 3.6) == pytest.approx(16.03276437545116,
                                                                       rel=1e-12)
