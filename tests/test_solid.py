"""The solid package against the real kernel: no mocks, geometry asserted, not snapshots."""

from __future__ import annotations

import math
import re
import struct

import cadquery as cq
import pytest

from bench.thread_spike.helical import naive_sweep_fuse, one_pipe
from bench.thread_spike.maths import VOID_CLEARANCE
from screw.build_errors import BuildError
from screw.calc import derive
from screw.calc.thread import T_GATE, closed_volume
from screw.params import KINDS, BoltParams, FastenerParams
from screw.solid import (
    _build_cached,
    bolt,
    build,
    check_solid,
    clear_cache,
    export,
    helical,
    precise_volume,
)

TOL = 1e-6  # mm


def _triangles(stl: bytes) -> int:
    """Triangle count from a binary STL, asserting the length is exactly 84 + 50 x count."""
    (count,) = struct.unpack("<I", stl[80:84])
    assert len(stl) == 84 + 50 * count, "not a binary STL"
    return int(count)


def test_the_default_bolt_is_one_valid_thread_six_by_six_by_twenty() -> None:
    solid = build(BoltParams())
    assert len(solid.Solids()) == 1
    assert solid.isValid()
    box = solid.BoundingBox()
    # z is exact to the 1e-7 box gap. x and y are not: the optimal box reads the crest up to
    # 3.000069 mm at M6 L=20.5 (3.000026 at L=20, planner probe 2026-10-10), so 1e-4.
    assert box.zmin == pytest.approx(0.0, abs=TOL)
    assert box.zmax == pytest.approx(20.0, abs=TOL)
    assert box.xlen == pytest.approx(6.0, abs=1e-4)
    assert box.ylen == pytest.approx(6.0, abs=1e-4)
    # A modelled thread, not the old cylinder: the closed form is the oracle, and the cylinder
    # of the same major diameter is 1 % or more away from it.
    volume = precise_volume(solid)
    assert volume == pytest.approx(closed_volume(6.0, 1.0, 20.0), rel=T_GATE)
    assert abs(volume - math.pi * 9 * 20) > 0.01 * math.pi * 9 * 20


def test_the_stl_is_binary_and_the_step_is_iso_10303() -> None:
    assert _triangles(export(BoltParams(), "stl", "preview")) > 0
    assert export(BoltParams(), "step").startswith(b"ISO-10303-21;")


def test_a_preview_export_leaves_the_cached_solid_unmeshed() -> None:
    # Meshing the cached solid in place made .BoundingBox() read the mesh: spur measured
    # zlen 7.5000 -> 7.5877 mm after a preview export (spur L24, mesh on a copy).
    clear_cache()
    p = BoltParams()
    export(p, "stl", "preview")
    assert build(p).BoundingBox().zlen == pytest.approx(20.0, abs=TOL)


def test_preview_has_fewer_triangles_than_fine() -> None:
    p = BoltParams()
    assert _triangles(export(p, "stl", "preview")) < _triangles(export(p, "stl", "fine"))


def test_a_solid_the_kernel_builds_with_the_wrong_volume_is_a_build_error() -> None:
    # d=0.001, pitch=0.0001, length=0.01 builds one valid solid whose volume is off the closed
    # form: +9.59e-03 in the research probe, +9.858e-03 in the run that wrote this test. The
    # gate refuses it, naming the volume and the signed relative error.
    with pytest.raises(BuildError, match=r"precise volume .*relative error \+\d\.\d+e-03"):
        export(BoltParams(d=0.001, pitch=0.0001, length=0.01), "step")


def _two_boxes() -> cq.Shape:
    box = cq.Solid.makeBox(1, 1, 1)
    return cq.Compound.makeCompound([box, box.translate(cq.Vector(5, 0, 0))])


def test_a_shape_of_two_solids_is_refused_naming_the_count() -> None:
    with pytest.raises(BuildError, match="2 solids"):
        check_solid(_two_boxes(), 2.0)


def test_an_invalid_solid_is_refused_before_its_volume_is_read() -> None:
    # d=1e-9 builds a cylinder with isValid() False (measured at planning); its volume is also
    # wrong against this closed form, and validity is the check named.
    collapsed = cq.Solid.makeCylinder(5e-10, 20)
    assert not collapsed.isValid()
    with pytest.raises(BuildError, match="invalid solid"):
        check_solid(collapsed, 1.0)


def test_a_build_failing_several_checks_is_refused_naming_the_first() -> None:
    # Two solids, one of them invalid, and both far from the closed form: the count is named.
    both = cq.Compound.makeCompound([cq.Solid.makeCylinder(5e-10, 20), cq.Solid.makeBox(1, 1, 1)])
    with pytest.raises(BuildError, match="2 solids"):
        check_solid(both, 1.0)


@pytest.mark.parametrize("length", [1e-8, 1e-9, math.nan])
def test_a_length_the_kernel_cannot_model_is_refused_before_the_kernel_runs(
        length: float, monkeypatch: pytest.MonkeyPatch) -> None:
    # A twist of 1e-8 mm or less SIGSEGVs the process before any check can run (D-17), so the
    # refusal has to come first; twist is patched to fail the test if it is ever reached.
    def unreachable(*_args: float, **_kwargs: float) -> None:
        pytest.fail("the builder reached the kernel")

    monkeypatch.setattr(helical, "twist", unreachable)
    with pytest.raises(BuildError, match="length"):
        helical.thread(6.0, 1.0, length)


def test_an_integer_turn_length_whose_float_tail_drifts_builds_and_ends_at_its_length() -> None:
    # 9 turns of 0.6 leave a float tail of 8.9e-16 mm, which SIGSEGVs without the tail fold.
    solid = build(BoltParams(d=3.5, pitch=0.6, length=5.4))
    assert len(solid.Solids()) == 1
    assert solid.isValid()
    assert solid.BoundingBox().zmax == pytest.approx(5.4, abs=TOL)


def test_a_kind_without_a_builder_is_a_bug_not_a_user_error() -> None:
    class Orphan(FastenerParams):
        kind = "orphan"

    with pytest.raises(TypeError, match="orphan"):
        build(Orphan())


def test_every_registered_kind_builds_and_derives() -> None:
    # The closed list: adding a kind to KINDS without a builder or an info document fails
    # here, not in front of a user.
    assert len(KINDS) >= 1
    for model in KINDS.values():
        p = model()
        assert len(build(p).Solids()) == 1
        assert derive(p).kind == model.kind


def _relative_error(text: str) -> float:
    match = re.search(r"relative error ([+-]\d\.\d+e[+-]\d+)", text)
    assert match, text
    return float(match.group(1))


def _assert_refused_and_not_cached(
        monkeypatch: pytest.MonkeyPatch, shape: cq.Shape, p: BoltParams) -> float:
    """Feed `shape` to the gate as if the bolt builder had made it: refused twice (a refusal
    is never cached, so the second call rebuilds and is refused again), cache size unchanged."""
    monkeypatch.setattr(bolt, "rod", lambda _p: shape)
    clear_cache()
    size = _build_cached.cache_info().currsize
    errors = []
    for _ in range(2):
        with pytest.raises(BuildError) as raised:
            build(p)
        errors.append(_relative_error(str(raised.value)))
    assert _build_cached.cache_info().currsize == size
    return errors[0]


@pytest.mark.parametrize(("d", "pitch", "length"), [
    (2.0, 0.4, 4.0), (6.0, 1.0, 10.0), (20.0, 2.5, 10.0),
])
def test_the_gate_refuses_the_naive_sweep_the_kernel_calls_valid(
        d: float, pitch: float, length: float, monkeypatch: pytest.MonkeyPatch) -> None:
    # L11 known-bad rows (`2026-10-08-a-controls`): one solid, isValid() True, a volume below
    # half the closed form. Only the volume check catches them.
    naive = naive_sweep_fuse(d, pitch, length)
    assert len(naive.Solids()) == 1
    assert naive.isValid()
    error = _assert_refused_and_not_cached(
        monkeypatch, naive, BoltParams(d=d, pitch=pitch, length=length))
    assert error < -0.5


def test_the_gate_refuses_the_inverted_one_pipe_twist_by_its_sign(
        monkeypatch: pytest.MonkeyPatch) -> None:
    # The one-pipe twist reads inverted at 160 turns while isValid() stays True: its precise
    # volume is about -1 times the closed form, a relative error near -2 (L11). The naive
    # sweep above is positive and does not exercise the sign.
    inverted = one_pipe(6.0, 1.0, 160.0)
    assert inverted.isValid()
    error = _assert_refused_and_not_cached(
        monkeypatch, inverted, BoltParams(d=6.0, pitch=1.0, length=160.0))
    assert error < -1.5


@pytest.mark.parametrize(("d", "pitch", "length"), [
    pytest.param(6.0, 1.0, 0.8, id="sub-turn-0.8"),
    pytest.param(6.0, 1.0, 20.5, id="non-integer-20.5"),
    pytest.param(3.5, 0.6, 10.8, id="float-drift-18-turns"),
    pytest.param(3.5, 0.6, 30.6, id="float-drift-51-turns"),
    pytest.param(2.5, 0.45, 9.0, id="float-drift-20-turns"),
])
def test_a_length_off_the_whole_turns_builds_through_the_gate_and_ends_at_its_length(
        d: float, pitch: float, length: float) -> None:
    solid = build(BoltParams(d=d, pitch=pitch, length=length))
    assert len(solid.Solids()) == 1
    assert solid.isValid()
    box = solid.BoundingBox()
    assert box.zmin == pytest.approx(0.0, abs=TOL)
    assert box.zmax == pytest.approx(length, abs=TOL)


def test_the_void_a_nut_will_subtract_passes_the_gate() -> None:
    # The same builder with the clearance-grown section Phase 5 subtracts; 0.20 mm is the
    # clearance every grid void row was built at.
    void = helical.thread(6.0, 1.0, 20.0, clearance=VOID_CLEARANCE)
    check_solid(void, closed_volume(6.0, 1.0, 20.0, VOID_CLEARANCE))
    assert void.BoundingBox().xlen == pytest.approx(6.0 + 2 * VOID_CLEARANCE, abs=1e-4)
