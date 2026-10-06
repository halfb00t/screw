"""The solid package against the real kernel: no mocks, geometry asserted, not snapshots."""

from __future__ import annotations

import struct

import pytest

from screw.build_errors import BuildError
from screw.calc import derive
from screw.params import KINDS, BoltParams, FastenerParams
from screw.solid import build, clear_cache, export

TOL = 1e-6  # mm


def _triangles(stl: bytes) -> int:
    """Triangle count from a binary STL, asserting the length is exactly 84 + 50 x count."""
    (count,) = struct.unpack("<I", stl[80:84])
    assert len(stl) == 84 + 50 * count, "not a binary STL"
    return int(count)


def test_the_default_bolt_is_one_valid_solid_six_by_six_by_twenty() -> None:
    solid = build(BoltParams())
    assert len(solid.Solids()) == 1
    assert solid.isValid()
    box = solid.BoundingBox()
    assert box.xlen == pytest.approx(6.0, abs=TOL)
    assert box.ylen == pytest.approx(6.0, abs=TOL)
    assert box.zlen == pytest.approx(20.0, abs=TOL)


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


def test_a_diameter_the_kernel_builds_invalid_is_a_build_error() -> None:
    # d=1e-9 builds with isValid() False (measured at planning): the doorway's positive
    # validity check is what turns it into a refusal instead of a corrupt export.
    with pytest.raises(BuildError):
        export(BoltParams(d=1e-9), "step")


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
