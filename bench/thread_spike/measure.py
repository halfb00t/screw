"""Volumes and the STL check (kernel module, worker only).

The default `Shape.Volume()` is a reference column, never a verdict input: it read +6.3 % on a
`cq_warehouse` thread and -1.0024 of the closed form on an inverted one-pipe solid, while
`isValid()` stayed True (RESEARCH Pattern 2). The verdict estimator is the precise one below.
"""

from __future__ import annotations

import gzip
import math
import struct
import tempfile
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps

from bench.build_time import stl_size

# Relative error bound of `BRepGProp.VolumeProperties_s`, per face. Read from the OCP
# docstring: above 0.001 the integration is non-adaptive. 1e-7 cost 2x (0.4-2.0 s against
# 0.2-1.0 s per row) for no gain: 1.53e-6 against 1.62e-6 at M6 L20 (RESEARCH Code Example 4).
PRECISE_EPS = 1e-6
# Vertices of the STL are welded by rounding each coordinate to this many mm before edges are
# paired, so the two sides of a seam compare equal.
WELD_MM = 1e-5
# The app's INTERIM gzip level (`src/screw/app.py` `_GZIP_LEVEL`, spur L19): the byte budget is
# raw + gzip at the level that ships. Levels 6 and 9 gave 4.9 % smaller on an M6 L60 STL, under
# L19's 10 % bar, so 1 stays (RESEARCH Pattern 7); Phase 7 re-measures.
GZIP_LEVEL = 1


def precise_volume(shape: cq.Shape) -> float:
    """Volume to `PRECISE_EPS`, signed: an inverted solid reads about -1 times its closed form."""
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape.wrapped, props, PRECISE_EPS, False, False)
    return float(props.Mass())


def default_volume(shape: cq.Shape) -> float:
    return float(shape.Volume())


def mesh_stl(shape: cq.Shape, tolerance: float, angular: float) -> tuple[bytes, float]:
    """Binary STL of a copy of `shape` (the shipped way, L24) and the seconds the export took.

    Only the export is timed: reading the file back is not part of the mesh cost. The
    temporary directory is removed on return or on an exception.
    """
    with tempfile.TemporaryDirectory(prefix="screw-spike-") as directory:
        path = Path(directory) / "part.stl"
        t0 = time.perf_counter()
        shape.copy().exportStl(str(path), tolerance=tolerance, angularTolerance=angular,
                               ascii=False, relative=False)
        seconds = time.perf_counter() - t0
        return path.read_bytes(), seconds


def gzip1(data: bytes) -> tuple[int, float]:
    """gzip at the app's level: the compressed size in bytes and the seconds it took."""
    t0 = time.perf_counter()
    compressed = gzip.compress(data, compresslevel=GZIP_LEVEL)
    return len(compressed), time.perf_counter() - t0


def step_export(shape: cq.Shape) -> tuple[int, float]:
    """STEP of `shape`, written the shipped way (`screw.solid`'s `_write_export`): the file's
    size in bytes and the seconds the export took. The temporary directory is removed on return
    or on an exception."""
    with tempfile.TemporaryDirectory(prefix="screw-spike-") as directory:
        path = Path(directory) / "part.step"
        t0 = time.perf_counter()
        shape.exportStep(str(path))
        seconds = time.perf_counter() - t0
        return path.stat().st_size, seconds


@dataclass(frozen=True)
class StlCheck:
    triangles: int
    watertight: bool
    open_edges: int
    signed_volume: float
    surface_area: float


def stl_check(data: bytes) -> StlCheck:
    """Watertightness, signed volume and surface area of a binary STL, with the standard
    library only.

    Watertight means every directed edge occurs exactly once and its reverse exactly once;
    `open_edges` counts the directed edges that break that. Signed volume is the sum of
    v0 . (v1 x v2) / 6 over the facets (negative for an inside-out mesh); surface area the sum
    of |(v1 - v0) x (v2 - v0)| / 2. Measured in research: about 3 us per triangle (1.3 s for
    605 450, 9.4 s for 3 203 406), so a campaign runs this outside the timed and the RSS region.
    """
    _, triangles = stl_size(data)
    edges: Counter[tuple[tuple[int, ...], tuple[int, ...]]] = Counter()
    volume = 0.0
    area = 0.0
    for facet in struct.iter_unpack("<12fH", data[84:]):
        v0 = (facet[3], facet[4], facet[5])
        v1 = (facet[6], facet[7], facet[8])
        v2 = (facet[9], facet[10], facet[11])
        volume += (v0[0] * (v1[1] * v2[2] - v1[2] * v2[1])
                   - v0[1] * (v1[0] * v2[2] - v1[2] * v2[0])
                   + v0[2] * (v1[0] * v2[1] - v1[1] * v2[0])) / 6
        ax, ay, az = v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]
        bx, by, bz = v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]
        area += math.sqrt((ay * bz - az * by) ** 2 + (az * bx - ax * bz) ** 2
                          + (ax * by - ay * bx) ** 2) / 2
        a, b, c = (tuple(round(x / WELD_MM) for x in v) for v in (v0, v1, v2))
        for edge in ((a, b), (b, c), (c, a)):
            if edge[0] != edge[1]:  # a facet collapsed by the weld has no such edge
                edges[edge] += 1
    open_edges = sum(1 for (u, v), n in edges.items() if n != 1 or edges.get((v, u), 0) != 1)
    # An empty mesh proves nothing, so zero triangles is not watertight.
    return StlCheck(triangles, triangles > 0 and open_edges == 0, open_edges, volume, area)
