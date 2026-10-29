"""The download mesh against the clearance it must not eat (FRNT-06, D-21).

`bench/mesh_deviation.py` states the rule and `bench/RESULTS.md` ("Mesh deviation (Phase 5, D-21)")
records the run that chose `TESSELLATION["fine"]`. These tests keep the choice true: the kernel
flag the measured deviation depends on is pinned, and the shipped export of the M6 thread is
measured again against the bound.
"""

from __future__ import annotations

import pytest
from OCP.BRepMesh import BRepMesh_IncrementalMesh

from bench.mesh_deviation import BOUND_MM, radial_deviations
from screw.params import BoltParams
from screw.solid import TESSELLATION, _write_export, bolt, build


def test_the_fine_mesh_keeps_the_kernels_control_surface_deflection_on_and_absolute() -> None:
    """RESEARCH F1: `exportStl` never sets `ControlSurfaceDeflection`; it holds because the OCP
    struct defaults it on. A cadquery or OCP bump that flips the default would change every
    deviation in the D-21 run without a line of screw changing, so the flag is read here from the
    same five-argument constructor `exportStl` calls. It meshes a copy, as `_write_export` does:
    meshing the cached solid in place left its triangulation on it, and the next test to read the
    default bolt's box (tests/test_solid.py) read the mesh's box, not the solid's."""
    linear, angular = TESSELLATION["fine"]
    parameters = BRepMesh_IncrementalMesh(build(BoltParams()).copy().wrapped, linear, False,
                                          angular, True).Parameters()
    assert parameters.ControlSurfaceDeflection is True
    assert parameters.Relative is False
    assert parameters.Deflection == pytest.approx(linear)
    assert parameters.Angle == pytest.approx(angular)


def test_the_fine_preset_is_the_one_the_fine_stl_caps_were_measured_at() -> None:
    """D-21 kept 0.01 mm / 0.1 rad, so `FINE_STL_ROWS` (measured at it, `2026-10-08-a-grid`) was
    not re-derived. A different fine value would need a recorded run of the caps at it first
    (T-05-39), not only a deviation that fits the bound."""
    assert TESSELLATION["fine"] == (0.01, 0.1)


def test_the_preview_is_coarser_than_the_fine_preset_on_both_deflections() -> None:
    assert TESSELLATION["preview"][0] > TESSELLATION["fine"][0]
    assert TESSELLATION["preview"][1] > TESSELLATION["fine"][1]


@pytest.mark.parametrize("left_hand", [False, True])
def test_the_shipped_fine_stl_of_the_m6_thread_stays_within_the_d21_bound(left_hand: bool) -> None:
    """The M6 x 8 mm thread piece the bolt builder makes, exported by `_write_export` (the
    product's own call), every facet centroid within `BOUND_MM` (0.5 x 0.05 mm) of the modelled
    surface. The preview export of the same piece breaks the bound, so the test can fail: a
    deviation metric that no preset could break would pin nothing."""
    p = BoltParams(length=8.0, thread_length=8.0, left_hand=left_hand)
    piece = bolt.thread(p)
    fine = _write_export(piece, p, "stl", "fine")
    preview = _write_export(piece, p, "stl", "preview")
    fine_worst = max(radial_deviations(fine, p.d, p.pitch, left_hand))
    preview_worst = max(radial_deviations(preview, p.d, p.pitch, left_hand))
    assert fine_worst <= BOUND_MM
    assert preview_worst > BOUND_MM
