"""The solid package against the real kernel: no mocks, geometry asserted, not snapshots."""

from __future__ import annotations

import math
import re
import struct
from collections.abc import Callable
from pathlib import Path

import cadquery as cq
import pytest
from OCP.IFSelect import IFSelect_ReturnStatus

from bench import oper_lift
from bench.thread_spike.helical import naive_sweep_fuse, one_pipe
from bench.thread_spike.maths import VOID_CLEARANCE
from bench.thread_spike.measure import stl_check
from screw.build_errors import BuildError
from screw.calc import derive, download_refusal
from screw.calc.thread import (
    T_GATE,
    TIP_ANGLE_DEG,
    bolt_closed_volume,
    bolt_end_closed_volume,
    built_thread_length,
    closed_volume,
    fillet_radius,
    fillet_ring_volume,
    head_chamfer_depths,
    head_chamfer_kernel_bound,
    piece_refusal,
    section_area,
    thread_depth,
    tip_cone_fits,
    tip_cone_length,
    tip_cone_volume,
    volume_check,
)
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
from screw.tables.iso262 import SIZES
from screw.tables.presets import catalogue

TOL = 1e-6  # mm


def _triangles(stl: bytes) -> int:
    """Triangle count from a binary STL, asserting the length is exactly 84 + 50 x count."""
    (count,) = struct.unpack("<I", stl[80:84])
    assert len(stl) == 84 + 50 * count, "not a binary STL"
    return int(count)


def test_the_default_bolt_is_one_valid_hex_head_screw_threaded_to_the_head() -> None:
    solid = build(BoltParams())
    assert len(solid.Solids()) == 1
    assert solid.isValid()
    box = solid.BoundingBox()
    # The thread on z 0..20 and the head on z 20..20 + k (D-05, D-07). z is exact to the 1e-7 box
    # gap. The chamfer is cut no deeper than k / 2 (06.1 D-03), so the head's lower half keeps its
    # corners and its box is exact too (s across flats in x, s / cos 30 degrees across corners in
    # y); the thread's crest (3.000026 mm at M6 L=20, planner probe 2026-10-10) is inside it, so
    # 1e-4 covers the optimal box.
    assert box.zmin == pytest.approx(0.0, abs=TOL)
    assert box.zmax == pytest.approx(20.0 + 4.0, abs=TOL)
    assert box.xlen == pytest.approx(10.0, abs=1e-4)
    assert box.ylen == pytest.approx(10.0 / math.cos(math.pi / 6), abs=1e-4)
    # The closed form of the whole part is the oracle; the bare thread's is more than 1 % away,
    # so a head that was not fused would be refused (the head is 346 of 805 mm3).
    volume = precise_volume(solid)
    whole = bolt_end_closed_volume(6.0, 1.0, 20.0, 10.0, 4.0, 20.0, True, None, 30.0)
    assert volume == pytest.approx(whole, rel=T_GATE)
    assert abs(volume - closed_volume(6.0, 1.0, 20.0)) > 0.01 * closed_volume(6.0, 1.0, 20.0)


def test_an_iso_4014_shaped_bolt_has_a_thread_a_plain_shank_and_a_head_in_one_valid_solid() -> None:
    # THRD-03, TYPE-01: M6 x 30 with 18 mm of thread from the tip, a plain shank of d from 18 to
    # 30 and the head on top. build() runs both gates against the closed form on t = 18.
    p = BoltParams(length=30.0, thread_length=18.0)
    solid = build(p)
    assert len(solid.Solids()) == 1
    assert solid.isValid()
    box = solid.BoundingBox()
    assert box.zmin == pytest.approx(0.0, abs=TOL)
    assert box.zmax == pytest.approx(34.0, abs=TOL)
    volume = precise_volume(solid)
    assert volume == pytest.approx(
        bolt_end_closed_volume(6.0, 1.0, 30.0, 10.0, 4.0, 18.0, True, 0.25, 30.0), rel=T_GATE)
    # The shank is a plain cylinder of the major diameter: at mid shank a point 2.9 mm from the
    # axis, outside the thread's root radius (2.46) at some angles, is inside at every angle, and
    # one 3.1 mm out is outside.
    for angle in (0.0, math.pi / 3, math.pi):
        x, y = 2.9 * math.cos(angle), 2.9 * math.sin(angle)
        assert solid.isInside(cq.Vector(x, y, 24.0))
        assert not solid.isInside(cq.Vector(3.1 * math.cos(angle), 3.1 * math.sin(angle), 24.0))


def test_a_left_hand_iso_4014_shaped_bolt_builds_through_both_gates() -> None:
    solid = build(BoltParams(length=30.0, thread_length=18.0, left_hand=True))
    assert len(solid.Solids()) == 1
    assert solid.isValid()


def test_a_screw_shorter_than_the_default_thread_builds_to_its_length() -> None:
    # D-08: BoltParams(length=10) keeps thread_length 20 and builds a 10 mm full-thread screw.
    solid = build(BoltParams(length=10.0))
    assert solid.BoundingBox().zmax == pytest.approx(10.0 + 4.0, abs=TOL)
    assert precise_volume(solid) == pytest.approx(
        bolt_end_closed_volume(6.0, 1.0, 10.0, 10.0, 4.0, 10.0, True, None, 30.0), rel=T_GATE)


def test_a_thread_length_above_the_length_builds_to_the_full_length() -> None:
    # D-25: the model accepts it, the builder derives t and the info warns.
    solid = build(BoltParams(length=10.0, thread_length=30.0))
    assert len(solid.Solids()) == 1
    assert solid.BoundingBox().zmax == pytest.approx(10.0 + 4.0, abs=TOL)


def test_a_shank_sliver_below_the_floor_is_folded_and_one_at_the_floor_is_built() -> None:
    # D-27, T-04-08: 0.00005 mm folds into the thread; 0.0002 mm, past the 0.0001 mm floor of L20,
    # keeps a shank. Both are one valid solid inside both gates (the kernel path that crashed on
    # a sliver, Alert 6).
    folded = build(BoltParams(length=5.0, thread_length=4.99995))
    assert len(folded.Solids()) == 1
    assert folded.isValid()
    assert precise_volume(folded) == pytest.approx(
        bolt_end_closed_volume(6.0, 1.0, 5.0, 10.0, 4.0, 5.0, True, None, 30.0), rel=T_GATE)
    kept = build(BoltParams(length=5.0, thread_length=4.9998))
    assert len(kept.Solids()) == 1
    assert kept.isValid()
    assert precise_volume(kept) == pytest.approx(
        bolt_end_closed_volume(6.0, 1.0, 5.0, 10.0, 4.0, 4.9998, True, None, 30.0), rel=T_GATE)


def test_a_thread_below_the_floor_is_refused_naming_both_fields_before_the_kernel(
        monkeypatch: pytest.MonkeyPatch) -> None:
    # Alert 6: helical's own guard names only `length`, so the bolt builder names the pair.
    def unreachable(*_args: float, **_kwargs: float) -> None:
        pytest.fail("the builder reached the kernel")

    monkeypatch.setattr(helical, "twist", unreachable)
    with pytest.raises(BuildError) as raised:
        build(BoltParams(length=0.00005))
    assert str(raised.value).startswith("thread_length and length: ")
    assert "5e-05" in str(raised.value)


def test_the_stl_is_binary_and_the_step_is_iso_10303() -> None:
    assert _triangles(export(BoltParams(), "stl", "preview")) > 0
    assert export(BoltParams(), "step").startswith(b"ISO-10303-21;")


def test_a_left_hand_screw_builds_through_both_gates_with_the_same_head() -> None:
    # The hand is the thread's; the head is a prism that does not know it (D-09).
    solid = build(BoltParams(left_hand=True))
    assert len(solid.Solids()) == 1
    assert solid.isValid()
    assert solid.BoundingBox().xlen == pytest.approx(10.0, abs=1e-4)


@pytest.mark.parametrize(("d", "pitch", "length", "s", "k"), [
    (8.0, 1.25, 12.0, 13.0, 5.3),
    (6.0, 1.0, 20.0, 6.0 * 1.0000001, 0.5),   # a head barely wider than the shank
])
def test_the_head_keeps_sharp_corners_below_the_chamfer_so_its_box_is_s_by_s_over_cos_30(
        d: float, pitch: float, length: float, s: float, k: float) -> None:
    box = build(BoltParams(d=d, pitch=pitch, length=length, s=s, k=k)).BoundingBox()
    # The default 30 degree chamfer is cut no deeper than k / 2 (06.1 D-03), so the lower half of
    # the head keeps the corners and the box is exact. The second case (s just above 6, k 0.5) is a
    # capped default chamfer: the model depth 0.268 is above k / 2 = 0.25.
    assert box.zmax == pytest.approx(length + k, abs=TOL)
    # The head is the widest part only when s is above the crest's 1e-4 box tolerance.
    assert box.xlen == pytest.approx(max(s, d), abs=1e-4)
    assert box.ylen == pytest.approx(max(s / math.cos(math.pi / 6), d), abs=1e-4)


def test_a_head_chamfer_of_zero_builds_todays_sharp_head() -> None:
    # 06.1 D-01: 0 (and -0.0, which `> 0` treats alike) cuts nothing, runs no piece gate and has no
    # chamfer term, so the part is the sharp `bolt.assemble` and its closed form is the old one.
    volume = 0.0
    for zero in (0.0, -0.0):
        clear_cache()      # equal parameters hash alike, and a cached 0.0 would hide the -0.0
        p = BoltParams(head_chamfer=zero)
        solid = build(p)
        assert len(solid.Solids()) == 1
        assert solid.isValid()
        volume = precise_volume(solid)
        assert volume == pytest.approx(
            bolt_end_closed_volume(6.0, 1.0, 20.0, 10.0, 4.0, 20.0, True, None, 0.0), rel=T_GATE)
        sharp = bolt.assemble(p, bolt.tip_cut(p, bolt.thread(p)), bolt.head_prism(p))
        assert volume == pytest.approx(precise_volume(sharp), rel=1e-9)
    # The default part is smaller by the pinned 30 degree term (06.1-01).
    assert volume - precise_volume(build(BoltParams())) == pytest.approx(
        1.0855309493921927, rel=1e-3)


def _no_chamfer(_p: BoltParams, prism: cq.Shape, _depth: float) -> cq.Shape:
    return prism


@pytest.mark.parametrize(("control", "angle", "error"), [
    ("skipped", 30.0, "-1.000e+00"),
    ("45 degrees", 30.0, None),
    ("skipped at 1 degree", 1.0, None),
])
def test_a_skipped_or_wrong_head_chamfer_is_refused_naming_the_piece(
        monkeypatch: pytest.MonkeyPatch, control: str, angle: float, error: str | None) -> None:
    # The positive controls of RESEARCH P8 for the head: the model is a cone at head_chamfer
    # degrees, and each control builds something else. The piece gate names the head chamfer.
    p = BoltParams(head_chamfer=angle)
    original = bolt.chamfer_head
    if control == "45 degrees":
        def at_45(q: BoltParams, prism: cq.Shape, depth: float) -> cq.Shape:
            return original(q.model_copy(update={"head_chamfer": 45.0}), prism, depth)

        monkeypatch.setattr(bolt, "chamfer_head", at_45)
    else:
        monkeypatch.setattr(bolt, "chamfer_head", _no_chamfer)
    if control == "skipped at 1 degree":
        # The whole-part gate alone misses it: the 1 degree piece is 0.0328 mm3, 4.1e-5 of the part
        # and under T_GATE 9e-5, so only the piece gate refuses.
        sharp = bolt.assemble(p, bolt.tip_cut(p, bolt.thread(p)), bolt.head_prism(p))
        closed = bolt_end_closed_volume(6.0, 1.0, 20.0, 10.0, 4.0, 20.0, True, None, 1.0)
        assert volume_check(precise_volume(sharp), closed) is None
    clear_cache()
    try:
        with pytest.raises(BuildError, match="wrong head chamfer: the head chamfer is") as raised:
            build(p)
    finally:
        clear_cache()
    if error is not None:
        assert error in str(raised.value)


def test_a_direct_head_chamfer_deeper_than_half_k_is_capped_and_builds_through_both_gates() -> None:
    # 06.1 D-06: the model accepts 80 degrees (depth 0.577 * tan 80 = 3.3 mm of an M6 head, above
    # k / 2 = 2 mm), so the cut is capped at k / 2 and warned about, never refused; the closed
    # form reads the same capped depth, so both gates agree with the kernel.
    p = BoltParams(head_chamfer=80.0)
    solid = build(p)
    assert len(solid.Solids()) == 1
    assert solid.isValid()
    assert precise_volume(solid) == pytest.approx(
        bolt_end_closed_volume(6.0, 1.0, 20.0, 10.0, 4.0, 20.0, True, None, 80.0), rel=T_GATE)
    box = solid.BoundingBox()
    assert box.zmax == pytest.approx(24.0, abs=TOL)      # the flat top is lower, not the head
    assert box.xlen == pytest.approx(10.0, abs=1e-4)
    assert box.ylen == pytest.approx(10.0 / math.cos(math.pi / 6), abs=1e-4)
    # D-04, defaulted branch: s 20, k 1 at the default 30 degrees asks 0.893 mm and is capped at
    # k / 2 = 0.5 mm.
    wide = BoltParams(s=20.0, k=1.0)
    full, cut = head_chamfer_depths(wide.s, wide.k, wide.head_chamfer)
    assert full == pytest.approx(0.893, abs=1e-3)
    assert cut == 0.5
    assert precise_volume(build(wide)) == pytest.approx(
        bolt_end_closed_volume(6.0, 1.0, 20.0, 20.0, 1.0, 20.0, True, None, 30.0), rel=T_GATE)


@pytest.mark.parametrize("angle", [0.5, 89.9, 1e-4, 1e-6, 5e-324, 89.99999999999999])
def test_a_tiny_or_near_right_head_chamfer_builds_inside_its_gates_or_is_refused_by_name(
        angle: float) -> None:
    # 06.1 D-18, L02. A disjunction per value: the outcomes at 1e-4 and 1e-5 degrees are single
    # macOS arm64 runs and linux/amd64 may differ. A solid that is returned passed both gates; any
    # exception other than BuildError (the API's 422) would be a 500. Geometry only, no call counts.
    clear_cache()
    solid: cq.Solid | None = None
    refusal: BuildError | None = None
    try:
        solid = build(BoltParams(head_chamfer=angle))
    except BuildError as raised:
        refusal = raised
    finally:
        clear_cache()
    if solid is None:
        assert angle not in (0.5, 89.9), f"a positive control was refused: {refusal}"
        if angle == 5e-324:  # WR-01: refused by the oracle, so the kernel never ran
            assert "Geometry kernel failed" not in str(refusal)
            assert "head_chamfer" in str(refusal)
        return
    assert angle != 5e-324, "an angle with no honest oracle was built"
    assert len(solid.Solids()) == 1
    assert solid.isValid()
    assert precise_volume(solid) == pytest.approx(
        bolt_end_closed_volume(6.0, 1.0, 20.0, 10.0, 4.0, 20.0, True, None, angle), rel=T_GATE)


@pytest.mark.parametrize("head", [
    {},  # the default head, s 10 k 4
    {"d": 2.0, "pitch": 0.4, "s": 4.0, "k": 1.4},  # M2, the smallest catalogue head
    {"d": 20.0, "pitch": 2.5, "s": 30.0, "k": 12.5, "length": 40.0, "thread_length": 40.0},  # M20
    {"d": 0.5, "pitch": 0.1, "length": 5.0, "thread_length": 5.0, "s": 1.0, "k": 0.4},  # small
])
def test_the_kernel_bound_angle_builds_through_both_gates(head: dict[str, float]) -> None:
    # The bound is where `derive` stops withholding the chamfer rows and the volume, so a part at
    # the bound has to be a part: one valid solid, piece gate and whole-part gate passed, volume
    # equal to the closed form the document prints. The grid behind the constants is in the
    # comment on them (both platforms, 210 cells at and above the bound, none refused).
    probe = BoltParams.model_validate(head)
    angle = head_chamfer_kernel_bound(probe.s, probe.k)
    p = BoltParams.model_validate({**head, "head_chamfer": angle})
    clear_cache()
    try:
        solid = build(p)
    finally:
        clear_cache()
    assert len(solid.Solids()) == 1
    assert solid.isValid()
    t = built_thread_length(p.thread_length, p.length)
    closed = bolt_end_closed_volume(
        p.d, p.pitch, p.length, p.s, p.k, t, tip_cone_fits(p.pitch, t),
        fillet_radius(p.d, p.pitch, p.length, t), angle)
    assert precise_volume(solid) == pytest.approx(closed, rel=T_GATE)


def _eps_diluted_below_the_gate_for_a_whole_part(d: float, pitch: float) -> float:
    """A relative growth of the diameter that moves the thread's section area by 1.1e-4 to
    1.4e-4 of itself: above T_GATE (9e-5) on the bare thread, and once the thread's share of the
    whole volume (0.57 at M6 x 20) multiplies it, 6.3e-5 to 8.0e-5, below T_GATE on the part."""
    eps = 4e-5
    while True:
        error = section_area(d * (1 + eps), pitch) / section_area(d, pitch) - 1
        if 1.1e-4 <= error <= 1.4e-4:
            return eps
        assert error < 1.4e-4, "the scan stepped over the band"
        eps += 5e-6


def test_a_thread_wrong_by_a_part_in_ten_thousand_is_refused_on_the_thread_not_the_whole(
        monkeypatch: pytest.MonkeyPatch) -> None:
    # RESEARCH Alert 5: the head dilutes a thread error. The thread is 0.57 of the volume at
    # M6 x 20, so a thread wrong by 1.1e-4 to 1.4e-4 reads 6.3e-5 to 8.0e-5 on the whole part,
    # inside T_GATE, and only the bare-thread gate sees it.
    p = BoltParams()
    eps = _eps_diluted_below_the_gate_for_a_whole_part(p.d, p.pitch)
    bad = helical.thread(p.d * (1 + eps), p.pitch, p.length)
    whole = bolt_closed_volume(p.d, p.pitch, p.length, p.s, p.k, p.length)
    share = closed_volume(p.d, p.pitch, p.length) / whole
    assert 0.5 < share < 0.6  # the measured thread share this control relies on
    # The control is real: the whole-part check alone would pass this very thread.
    assert volume_check(precise_volume(bolt.assemble(p, bad, bolt.head_prism(p))), whole) is None
    monkeypatch.setattr(bolt, "thread", lambda _p: bad)
    clear_cache()
    size = _build_cached.cache_info().currsize
    with pytest.raises(BuildError, match="wrong thread") as raised:
        build(p)
    assert 1.1e-4 <= abs(_relative_error(str(raised.value))) <= 1.4e-4
    assert _build_cached.cache_info().currsize == size  # a refusal is never cached


def test_the_good_thread_of_the_same_screw_passes_both_gates() -> None:
    # The negative of the control above: the unpatched build of the same part is served.
    assert len(build(BoltParams()).Solids()) == 1


def test_a_preview_export_leaves_the_cached_solid_unmeshed() -> None:
    # Meshing the cached solid in place made .BoundingBox() read the mesh: spur measured
    # zlen 7.5000 -> 7.5877 mm after a preview export (spur L24, mesh on a copy).
    clear_cache()
    p = BoltParams()
    export(p, "stl", "preview")
    assert build(p).BoundingBox().zlen == pytest.approx(20.0 + 4.0, abs=TOL)


def test_preview_has_fewer_triangles_than_fine() -> None:
    p = BoltParams()
    assert _triangles(export(p, "stl", "preview")) < _triangles(export(p, "stl", "fine"))


def test_a_solid_the_kernel_builds_with_the_wrong_volume_is_a_build_error() -> None:
    # d=0.03, pitch=0.005, length=0.05 (a root radius of 0.0123 mm, just above the 0.01 mm floor)
    # builds one valid solid whose volume is off the closed form: -1.829e-04 in the run that wrote
    # this test, +9.59e-03 at d=0.001 in the research probe, a part the floor now refuses before
    # the kernel. The gate refuses it, naming the volume and the signed relative error.
    with pytest.raises(BuildError, match=r"precise volume .*relative error [+-]\d\.\d+e-0\d"):
        export(BoltParams(d=0.03, pitch=0.005, length=0.05), "step")


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
    assert solid.BoundingBox().zmax == pytest.approx(5.4 + 4.0, abs=TOL)  # + the default head k


def test_a_kind_without_a_builder_is_a_bug_not_a_user_error() -> None:
    class Orphan(FastenerParams):
        kind = "orphan"

    with pytest.raises(TypeError, match="orphan"):
        build(Orphan())


def test_every_registered_kind_builds_and_derives(
        part_of: Callable[[str], FastenerParams]) -> None:
    # The closed list: adding a kind to KINDS without a builder or an info document fails
    # here, not in front of a user.
    assert len(KINDS) >= 1
    for kind, model in KINDS.items():
        p = part_of(kind)
        assert len(build(p).Solids()) == 1
        assert derive(p).kind == model.kind


def _relative_error(text: str) -> float:
    match = re.search(r"relative error ([+-]\d\.\d+e[+-]\d+)", text)
    assert match, text
    return float(match.group(1))


def _assert_refused_and_not_cached(
        monkeypatch: pytest.MonkeyPatch, shape: cq.Shape, p: BoltParams) -> float:
    """Feed `shape` to the gate as if the bolt builder had made the thread: refused twice (a
    refusal is never cached, so the second call rebuilds and is refused again), cache size
    unchanged. The bare-thread gate fires first, before any head is fused."""
    monkeypatch.setattr(bolt, "thread", lambda _p: shape)
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
    (2.0, 0.4, 4.0), (8.0, 1.25, 10.0), (20.0, 2.5, 10.0),
])
def test_the_gate_refuses_the_naive_sweep_the_kernel_calls_valid(
        d: float, pitch: float, length: float, monkeypatch: pytest.MonkeyPatch) -> None:
    # L11 known-bad rows (`2026-10-08-a-controls`): one solid, isValid() True, a volume below
    # half the closed form. Only the volume check catches them.
    # (8.0, 1.25, 10.0), not L11's (6.0, 1.0, 10.0): the naive fuse depends on the platform, and
    # with the same pins that row raises `Null TopoDS_Shape` on linux/amd64 (CI ubuntu-latest;
    # the emulated `screw:latest` image agrees) but is one valid solid at 0.238 of the closed
    # form on macOS arm64. All three rows here are one valid solid on both. L11, platform note.
    naive = naive_sweep_fuse(d, pitch, length)
    assert len(naive.Solids()) == 1
    assert naive.isValid()
    error = _assert_refused_and_not_cached(
        monkeypatch, naive, BoltParams(d=d, pitch=pitch, length=length, s=3 * d, k=d))
    assert error < -0.5


def test_the_gate_refuses_the_inverted_one_pipe_twist_by_its_sign(
        monkeypatch: pytest.MonkeyPatch) -> None:
    # The one-pipe twist reads inverted at 160 turns while isValid() stays True: its precise
    # volume is about -1 times the closed form, a relative error near -2 (L11). The naive
    # sweep above is positive and does not exercise the sign.
    inverted = one_pipe(6.0, 1.0, 160.0)
    assert inverted.isValid()
    # 160 turns is past the model's 90 (L20) and the twist is the kernel's, so the closed form is
    # read from the part under the guards of the registration (250 turns, L11)
    part = oper_lift.registered(
        "bolt", {"d": 6.0, "pitch": 1.0, "length": 160.0, "thread_length": 160.0})
    assert isinstance(part, BoltParams)
    error = _assert_refused_and_not_cached(monkeypatch, inverted, part)
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
    solid = build(BoltParams(d=d, pitch=pitch, length=length, thread_length=length))
    assert len(solid.Solids()) == 1
    assert solid.isValid()
    box = solid.BoundingBox()
    assert box.zmin == pytest.approx(0.0, abs=TOL)
    assert box.zmax == pytest.approx(length + 4.0, abs=TOL)  # the head ends at length + k


def _inside_at(solid: cq.Solid, d: float, pitch: float, sign: int, z: float) -> bool:
    """Is the point 80 % of the way from the root to the crest, on the thread's own helix
    at height `z`, inside the solid?

    The tooth stands on the helix theta = 2 pi z / pitch for a right-hand thread, so the
    probe reads inside at +theta and outside at -theta; a left-hand thread reads the
    reverse. Pass `z` a quarter turn past a whole number of turns: a half turn would read
    inside for both (the symmetric point), 03-RESEARCH Pitfall 9, reproduced 2026-10-10.
    """
    ro = d / 2
    rr = ro - thread_depth(pitch)
    r = rr + 0.8 * (ro - rr)
    theta = sign * 2 * math.pi * z / pitch
    return bool(solid.isInside(cq.Vector(r * math.cos(theta), r * math.sin(theta), z)))


@pytest.mark.parametrize(("d", "pitch", "length", "heights"), [
    # M6x20: the first 3-turn base segment, the second (a translated copy of the first) and the
    # 2 mm tail, which is a separate twist() call (WR-06: a tail built with the wrong hand left
    # the old single probe at z = 2.25 pitch reading correctly).
    pytest.param(6.0, 1.0, 20.0, (2.25, 3 + 2.25, 18 + 0.25), id="M6x20-base-copy-tail"),
    # 5.4 mm at pitch 0.6 leaves a 8.9e-16 mm tail that is folded into the previous segment, so
    # the last twist() is a full 3 turns from z = 3.6 and the tail takes the other branch.
    pytest.param(3.5, 0.6, 5.4, (2.25 * 0.6, 3 * 0.6 + 2.25 * 0.6, 3.6 + 0.25 * 0.6),
                 id="folded-tail"),
])
def test_the_hand_decides_which_way_the_thread_climbs_and_both_pass_the_same_gate(
        d: float, pitch: float, length: float, heights: tuple[float, ...]) -> None:
    # The volume gate cannot see the hand: a mirrored thread has the same volume. Only a
    # probe on the helix does, and both hands are asserted here so it cannot pass vacuously.
    # It is read in every segment: each segment is a separate twist() that gets its own hand.
    # The probe reads the bare thread `_build` fuses the head onto, not the fused screw: OCCT's
    # ray classifier is unreliable on the fused M3.5 x 5.4 screw (isInside says outside at +theta
    # on z = 1.35 for the right-hand part at 80 %, and inside at +theta for the left-hand part at
    # 50 %; the bare thread reads both hands correctly at 80 %, 2026-10-11), although the fused
    # solid is valid and inside T_GATE of its closed form. The head is a prism on top and cannot
    # change the hand.
    right_p = BoltParams(d=d, pitch=pitch, length=length, left_hand=False)
    left_p = BoltParams(d=d, pitch=pitch, length=length, left_hand=True)
    right, left = bolt.thread(right_p), bolt.thread(left_p)
    for z in heights:
        assert (_inside_at(right, d, pitch, +1, z), _inside_at(right, d, pitch, -1, z)) == (
            True, False), z
        assert (_inside_at(left, d, pitch, +1, z), _inside_at(left, d, pitch, -1, z)) == (
            False, True), z
    closed = bolt_end_closed_volume(d, pitch, length, 10.0, 4.0, length, True, None, 30.0)
    for solid in (build(right_p), build(left_p)):
        assert len(solid.Solids()) == 1
        assert solid.isValid()
        assert precise_volume(solid) == pytest.approx(closed, rel=T_GATE)


def test_a_left_hand_rod_exports_as_a_preview_stl_and_a_step() -> None:
    p = BoltParams(left_hand=True)
    assert _triangles(export(p, "stl", "preview")) > 0
    assert export(p, "step", "fine").startswith(b"ISO-10303-21;")
    # The mirror image of the right-hand rod, so not the same mesh.
    mirror = export(BoltParams(), "stl", "preview")
    assert export(p, "stl", "preview") != mirror


def test_the_void_a_nut_will_subtract_passes_the_gate() -> None:
    # The same builder with the clearance-grown section Phase 5 subtracts; 0.20 mm is the
    # clearance every grid void row was built at.
    void = helical.thread(6.0, 1.0, 20.0, clearance=VOID_CLEARANCE)
    check_solid(void, closed_volume(6.0, 1.0, 20.0, VOID_CLEARANCE))
    assert void.BoundingBox().xlen == pytest.approx(6.0 + 2 * VOID_CLEARANCE, abs=1e-4)


def _stl_writing(data: bytes) -> object:
    """A stand-in for `Shape.exportStl` that writes `data` and reports success."""
    def export_stl(_shape: cq.Shape, file_name: str, *_args: object, **_kwargs: object) -> bool:
        Path(file_name).write_bytes(data)
        return True
    return export_stl


def test_an_stl_export_that_wrote_no_file_is_a_build_error_not_a_missing_file(
        monkeypatch: pytest.MonkeyPatch) -> None:
    # exportStl returns False and writes nothing for an empty compound; reading the path then
    # raised FileNotFoundError, the 500 the collapsed-solid blocker recorded.
    monkeypatch.setattr(cq.Shape, "exportStl", lambda *_args, **_kwargs: False)
    with pytest.raises(BuildError, match="STL"):
        export(BoltParams(), "stl", "preview")


def test_a_step_export_the_kernel_did_not_finish_is_a_build_error(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cq.Shape, "exportStep",
                        lambda *_args, **_kwargs: IFSelect_ReturnStatus.IFSelect_RetFail)
    with pytest.raises(BuildError, match="STEP"):
        export(BoltParams(), "step")


@pytest.mark.parametrize("data", [
    pytest.param(bytes(80) + struct.pack("<I", 10), id="header-claims-10-facets-no-body"),
    pytest.param(bytes(80) + struct.pack("<I", 2) + bytes(100), id="well-formed-2-facets"),
    pytest.param(bytes(40), id="shorter-than-a-header"),
])
def test_an_stl_that_is_not_a_closed_solids_mesh_is_a_build_error(
        data: bytes, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cq.Shape, "exportStl", _stl_writing(data))
    with pytest.raises(BuildError, match="STL"):
        export(BoltParams(), "stl", "preview")


# --- the bolt's ends: the tip cone and the fillet ring, each judged by its piece (05-12) --------

M6X60 = BoltParams(d=6.0, pitch=1.0, length=60.0, s=10.0, k=4.0, thread_length=18.0)
M10X80 = BoltParams(d=10.0, pitch=1.5, length=80.0, s=16.0, k=6.4, thread_length=26.0)
M10X200 = BoltParams(d=10.0, pitch=1.5, length=200.0, s=16.0, k=6.4, thread_length=26.0)


def _tip_piece(p: BoltParams) -> tuple[float, float]:
    """(volume the tip cut removed, its oracle) read from precise volumes before and after."""
    bare = bolt.thread(p)
    removed = precise_volume(bare) - precise_volume(bolt.tip_cut(p, bare))
    return removed, tip_cone_volume(p.d, p.pitch, TIP_ANGLE_DEG)


def _ring_piece(p: BoltParams) -> tuple[float, float]:
    """(volume the ring added, its oracle) on the tip-cut, assembled bolt."""
    plain = bolt.assemble(p, bolt.tip_cut(p, bolt.thread(p)), bolt.head_prism(p))
    r = fillet_radius(p.d, p.pitch, p.length, p.length - 1.0)  # any t with the shank >= r
    assert r is not None
    return (precise_volume(bolt.add_fillet(p, plain, r)) - precise_volume(plain),
            fillet_ring_volume(p.d, r))


@pytest.mark.parametrize("p", [BoltParams(), M6X60, M10X80, M10X200],
                         ids=["default", "M6x60", "M10x80", "M10x200"])
def test_the_tip_cut_removes_the_cone_the_oracle_names_to_within_the_piece_tolerance(
        p: BoltParams) -> None:
    removed, oracle = _tip_piece(p)
    assert piece_refusal(removed, oracle, "tip cone") is None
    # The cone is not nothing and not the whole thread: the piece is a real fraction of a mm3.
    assert 0.1 < removed < 10.0


@pytest.mark.parametrize("p", [M6X60, M10X80, M10X200], ids=["M6x60", "M10x80", "M10x200"])
def test_the_fillet_ring_adds_the_volume_pappus_names_to_within_the_piece_tolerance(
        p: BoltParams) -> None:
    added, oracle = _ring_piece(p)
    assert piece_refusal(added, oracle, "fillet ring") is None


def test_an_iso_4014_bolt_gets_the_ring_and_an_iso_4017_screw_does_not() -> None:
    # M10 x 80: the whole part carries the ring (the closed form with it is inside T_GATE and
    # the one without it is not distinguishable at T_GATE alone, which is why the piece exists).
    with_ring = precise_volume(build(M10X80))
    # The same chamfered head the build cuts, so the difference is the ring alone.
    _, cut = head_chamfer_depths(M10X80.s, M10X80.k, M10X80.head_chamfer)
    head = bolt.chamfer_head(M10X80, bolt.head_prism(M10X80), cut)
    plain = precise_volume(bolt.assemble(M10X80, bolt.tip_cut(M10X80, bolt.thread(M10X80)), head))
    assert with_ring - plain == pytest.approx(fillet_ring_volume(10.0, 0.4), rel=0.03)
    # An ISO 4017 M6 x 20 is threaded to the head: no shank, no ring.
    assert fillet_radius(6.0, 1.0, 20.0, 20.0) is None
    assert precise_volume(build(BoltParams())) == pytest.approx(
        bolt_end_closed_volume(6.0, 1.0, 20.0, 10.0, 4.0, 20.0, True, None, 30.0), rel=T_GATE)


def test_a_shank_exactly_as_long_as_the_radius_gets_the_ring_and_one_float_less_does_not() -> None:
    at = build(BoltParams(thread_length=20.0 - 0.25, length=20.0))
    assert precise_volume(at) == pytest.approx(
        bolt_end_closed_volume(6.0, 1.0, 20.0, 10.0, 4.0, 19.75, True, 0.25, 30.0), rel=T_GATE)
    below = build(BoltParams(thread_length=math.nextafter(19.75, 20.0), length=20.0))
    assert precise_volume(below) == pytest.approx(
        bolt_end_closed_volume(
            6.0, 1.0, 20.0, 10.0, 4.0, math.nextafter(19.75, 20.0), True, None, 30.0),
        rel=T_GATE)


def _skip_the_cut(_p: BoltParams, bare: cq.Solid) -> cq.Solid:
    return bare


def _drop_the_ring(_p: BoltParams, part: cq.Shape, _r: float) -> cq.Shape:
    return part


@pytest.mark.parametrize("p", [M6X60, M10X200], ids=["M6x60", "M10x200"])
@pytest.mark.parametrize(("control", "what"), [
    ("skipped", "tip cone"), ("wrong angle", "tip cone"), ("ring dropped", "fillet ring"),
])
def test_a_missing_or_wrong_end_is_refused_naming_the_piece(
        monkeypatch: pytest.MonkeyPatch, p: BoltParams, control: str, what: str) -> None:
    # The positive controls of RESEARCH P8: the model is a 45 degree cone and a ring, and each
    # control builds something else. The piece check names the piece it found wrong.
    if control == "skipped":
        monkeypatch.setattr(bolt, "tip_cut", _skip_the_cut)
    elif control == "wrong angle":
        monkeypatch.setattr(bolt, "TIP_ANGLE_DEG", 30.0)
    else:
        monkeypatch.setattr(bolt, "add_fillet", _drop_the_ring)
    clear_cache()
    try:
        with pytest.raises(BuildError, match=f"wrong {what}: the {what} is"):
            build(p)
    finally:
        clear_cache()


# What the whole-part gate alone says about each control on the shipped bolts. The 05-02 probe
# (`bench/RESULTS.md`, End-cut probe) measured rods and flagged five of six at T_GATE; on the
# whole bolt (thread 26 mm of 200) it flags four: it misses the dropped ring and the 30 degree
# cone on M10 x 200 (8.1e-05 and 6.6e-05 against T_GATE 9e-05). The plan text expected it to pass
# all three controls on both bolts; it does not (05-12 SUMMARY, Deviations). The piece check
# above refuses all six.
@pytest.mark.parametrize(("p", "control", "seen"), [
    (M6X60, "skipped", True), (M6X60, "wrong angle", True), (M6X60, "ring dropped", True),
    (M10X200, "skipped", True), (M10X200, "wrong angle", False), (M10X200, "ring dropped", False),
])
def test_the_whole_part_gate_alone_misses_two_of_the_six_controls_on_the_long_bolt(
        monkeypatch: pytest.MonkeyPatch, p: BoltParams, control: str, seen: bool) -> None:
    r = fillet_radius(p.d, p.pitch, p.length, p.thread_length)
    assert r is not None
    if control == "wrong angle":
        monkeypatch.setattr(bolt, "TIP_ANGLE_DEG", 30.0)
    thread = bolt.thread(p)
    cut = thread if control == "skipped" else bolt.tip_cut(p, thread)
    part = bolt.assemble(p, cut, bolt.head_prism(p))
    if control != "ring dropped":
        part = bolt.add_fillet(p, part, r)
    closed = bolt_end_closed_volume(p.d, p.pitch, p.length, p.s, p.k, p.thread_length, True, r, 0.0)
    assert (volume_check(precise_volume(part), closed) is not None) is seen


@pytest.mark.parametrize("left_hand", [False, True])
def test_a_left_hand_bolt_with_a_ring_and_a_cone_passes_the_same_checks(left_hand: bool) -> None:
    p = M10X80.model_copy(update={"left_hand": left_hand})
    solid = build(p)
    assert len(solid.Solids()) == 1
    assert precise_volume(solid) == pytest.approx(
        bolt_end_closed_volume(10.0, 1.5, 80.0, 16.0, 6.4, 26.0, True, 0.4, 30.0), rel=T_GATE)
    removed, oracle = _tip_piece(p)
    assert piece_refusal(removed, oracle, "tip cone") is None


def test_a_thread_no_longer_than_the_tip_cone_builds_without_the_cone() -> None:
    # One float above the cone length the kernel cannot cut (the cone then grazes the thread's
    # far end and the boolean fails, 05-12 SUMMARY), so the built side of the boundary is read
    # a millimetre-scale step above it; `derive` is tested at the float in `tests/test_calc.py`.
    cone = tip_cone_length(1.0, TIP_ANGLE_DEG)
    for t, cut in ((cone, False), (cone + 1e-3, True)):
        p = BoltParams(d=6.0, pitch=1.0, length=10.0, s=10.0, k=4.0, thread_length=t)
        assert precise_volume(build(p)) == pytest.approx(
            bolt_end_closed_volume(6.0, 1.0, 10.0, 10.0, 4.0, t, cut, 0.25, 30.0), rel=T_GATE)


# --- the watertight sweep over both standards, both hands (RESEARCH P7, 05-12) ------------------


def _sweep_row(size: str, standard: str, left_hand: bool) -> BoltParams:
    """The shortest ISO 4017 row of `size`, or the longest ISO 4014 row of it whose fine STL the
    shipped rule admits for the hand (so the part stays inside what a user can download at fine).
    The row is chosen here, not typed, so a wider envelope only changes which row is read; a size
    with no admitted ISO 4014 row fails, it is never skipped."""
    rows = [BoltParams.model_validate({**dict(r.fields), "left_hand": left_hand})
            for r in catalogue() if r.size == size and r.standard == standard]
    if standard == "ISO 4017":
        return min(rows, key=lambda p: p.length)
    admitted = [p for p in rows if download_refusal(p, "stl", "fine") is None]
    assert admitted, (size, left_hand, "no ISO 4014 row admitted at fine STL")
    return max(admitted, key=lambda p: p.length)


@pytest.mark.parametrize("left_hand", [False, True], ids=["right", "left"])
@pytest.mark.parametrize("standard", ["ISO 4017", "ISO 4014"])
@pytest.mark.parametrize("size", [size.label for size in SIZES])
def test_every_size_of_both_standards_meshes_watertight_at_preview(
        size: str, standard: str, left_hand: bool) -> None:
    p = _sweep_row(size, standard, left_hand)
    mesh = stl_check(export(p, "stl", "preview"))
    assert mesh.open_edges == 0, (size, standard, left_hand, p.length)
    assert mesh.triangles > 0
