"""The D-21 run of Phase 5: how far the shipped download mesh strays from the thread it models.

THE RULE (stated here, in the commit that adds this module, before any ladder row is run; FRNT-06):

    The fine preset is the LARGEST linear deflection on `LADDER_MM` (angular `ANGULAR_RAD`,
    absolute millimetres) whose measured maximum radial deviation, over every size in `SIZES` and
    both hands, is at most `FRACTION * PROOF_CLEARANCE_MM`.

`FRACTION` is 0.5, the owner's answer to R6 (`.planning/phases/05-hex-nut-and-kernel-pair-proof/
05-OWNER-READS.md`, "Rulings": "R6 (FRNT-06 fraction): `a`. 0.5 of the 0.05 mm proof clearance,
keep the 0.01 mm fine preset, cite the rule"). The agent did not choose it. The bound is therefore
0.025 mm. The ladder is fixed here too, so the step is not picked after reading the table: no step
may be added to `LADDER_MM` once a table has been seen.

THE METRIC. Each rod is the shipped `screw.solid.helical.thread(d, pitch, 8 * pitch)`, exported by
the shipped call (`bench.thread_spike.measure.mesh_stl`: `shape.copy().exportStl(..., ascii=False,
relative=False)`, as `screw.solid._write_export` does). Every facet of the binary STL is sampled,
none in five. The facet centroid (x, y, z) is compared with the surface it models:

    deviation = | section_radius(d, pitch, 0, atan2(y, x) - hand * 2 pi z / pitch) - hypot(x, y) |

with `hand` +1 right and -1 left (05-RESEARCH F2: the opposite sign misses by 0.54 mm). A facet is
skipped when its centroid lies within two pitches of either end of the rod's z extent, where the
end planes and the last turn are not the thread. The radial segment from a centroid to the surface
is one path to it, so each value is an UPPER bound of that point's distance to the surface (on a
flank the normal distance is about half of it, on a crest or root equal; checked against the
kernel on M3). The maximum over the sampled centroids is NOT a proven bound of the mesh's global
maximum: it is a sample of centroids (vertices lie on the surface and read as zero). That limit is
carried into the entry.

THE HARNESS CHECK. Before a row counts, every mesh vertex in the same z window must lie on the
`section_radius` surface to `VERTEX_TOL_MM` (1e-4 mm; 05-RESEARCH F2 read 1.2e-05). If one does
not, the sign or the model is wrong and the run aborts as a harness defect, never as a result.

Kernel side (it imports `cadquery`), run by hand: `python -m bench.mesh_deviation`. The metric
itself (`radial_deviations`, `vertex_error`, `rule`) is pure `struct` and `math`, so a test can
feed it a hand-built STL. It measures a mesh property of one rod family on one host; nothing under
`src/` reads it.
"""

from __future__ import annotations

import math
import struct
import subprocess
from dataclasses import dataclass

import cadquery as cq

from bench import machine_facts
from bench.quiet import Reading, read_now
from bench.thread_spike.maths import PITCH
from bench.thread_spike.measure import mesh_stl
from screw.calc.thread import section_radius
from screw.solid import helical

# The ladder of linear deflections, mm, largest first. Fixed before the run (see the rule above).
LADDER_MM = (0.01, 0.0075, 0.005, 0.0025)
ANGULAR_RAD = 0.1
# The coarse preview preset, measured alongside as the positive control: it must not pass.
PREVIEW = (0.08, 0.5)
# Sizes sampled (05-17 plan, RESEARCH F2): the smallest, M3, M6, M10 and the largest of the 15.
SIZES = ("M2", "M3", "M6", "M10", "M20")
HANDS = (False, True)
PROOF_CLEARANCE_MM = 0.05
FRACTION = 0.5
BOUND_MM = FRACTION * PROOF_CLEARANCE_MM
VERTEX_TOL_MM = 1e-4
ROD_PITCHES = 8     # the rod is this many pitches long
SKIP_PITCHES = 2    # facets this close to either end are not the thread

_FACET = struct.Struct("<12fH")  # normal, three vertices, attribute byte count


@dataclass(frozen=True)
class Row:
    size: str
    left_hand: bool
    linear: float
    angular: float
    triangles: int
    nbytes: int
    max_deviation: float
    p99_deviation: float


def _facets(stl: bytes) -> list[tuple[float, ...]]:
    count = struct.unpack("<I", stl[80:84])[0]
    if len(stl) != 84 + _FACET.size * count:
        raise ValueError(f"STL claims {count} facets but is {len(stl)} bytes long")
    return list(_FACET.iter_unpack(stl[84:]))


def _z_window(facets: list[tuple[float, ...]], pitch: float) -> tuple[float, float]:
    zs = [f[i] for f in facets for i in (5, 8, 11)]
    return min(zs) + SKIP_PITCHES * pitch, max(zs) - SKIP_PITCHES * pitch


def _gap(d: float, pitch: float, left_hand: bool, x: float, y: float, z: float) -> float:
    """Signed radial gap: the modelled surface's radius at this point less the point's radius."""
    hand = -1.0 if left_hand else 1.0
    theta = math.atan2(y, x) - hand * 2 * math.pi * z / pitch
    return section_radius(d, pitch, 0.0, theta) - math.hypot(x, y)


def radial_deviations(stl: bytes, d: float, pitch: float, left_hand: bool) -> list[float]:
    """|radial gap| of every facet centroid outside the two-pitch end margins, in facet order."""
    facets = _facets(stl)
    low, high = _z_window(facets, pitch)
    out: list[float] = []
    for f in facets:
        x, y, z = ((f[3] + f[6] + f[9]) / 3, (f[4] + f[7] + f[10]) / 3,
                   (f[5] + f[8] + f[11]) / 3)
        if low <= z <= high:
            out.append(abs(_gap(d, pitch, left_hand, x, y, z)))
    return out


def vertex_error(stl: bytes, d: float, pitch: float, left_hand: bool) -> float:
    """The largest |radial gap| of any mesh vertex in the same z window: the harness check."""
    facets = _facets(stl)
    low, high = _z_window(facets, pitch)
    worst = 0.0
    for f in facets:
        for i in (3, 6, 9):
            if low <= f[i + 2] <= high:
                worst = max(worst, abs(_gap(d, pitch, left_hand, f[i], f[i + 1], f[i + 2])))
    return worst


def measure(size: str, left_hand: bool, rod: cq.Solid, linear: float, angular: float) -> Row:
    """Mesh `rod` at one preset the shipped way and sample every facet; abort on a harness fault."""
    d, pitch = (float(v) for v in PITCH[size])
    stl, _ = mesh_stl(rod, linear, angular)
    on_surface = vertex_error(stl, d, pitch, left_hand)
    if on_surface > VERTEX_TOL_MM:
        raise RuntimeError(f"harness defect: {size} {'left' if left_hand else 'right'} "
                           f"({linear}, {angular}) has a vertex {on_surface:.3e} mm off the "
                           f"surface, over {VERTEX_TOL_MM:g}: the sign or the model is wrong")
    devs = sorted(radial_deviations(stl, d, pitch, left_hand))
    p99 = devs[math.ceil(0.99 * len(devs)) - 1]   # nearest rank
    return Row(size, left_hand, linear, angular, struct.unpack("<I", stl[80:84])[0], len(stl),
               devs[-1], p99)


def rule(rows: list[Row]) -> float:
    """The largest ladder step whose maximum deviation over every size and hand is within bound.

    Raises `ValueError` if a step's grid is incomplete or no step meets the bound: an incomplete
    run does not select a preset, and a ladder that fails is the owner's to extend, not ours.
    """
    wanted = {(size, hand) for size in SIZES for hand in HANDS}
    for step in sorted(LADDER_MM, reverse=True):
        mine = [r for r in rows if r.linear == step and r.angular == ANGULAR_RAD]
        if {(r.size, r.left_hand) for r in mine} != wanted:
            raise ValueError(f"ladder step {step} mm does not cover every size and hand")
        if max(r.max_deviation for r in mine) <= BOUND_MM:
            return step
    raise ValueError(f"no ladder step meets the bound of {BOUND_MM:g} mm")


def _load(reading: Reading) -> str:
    return f"load1 {reading.load1:.2f} at {reading.utc}"


def _row(r: Row) -> str:
    return (f"| {r.size} | {'left' if r.left_hand else 'right'} | {r.linear:g} / {r.angular:g} "
            f"| {r.triangles} | {r.nbytes} | {r.max_deviation:.4f} | {r.p99_deviation:.4f} |")


def main() -> None:
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip()
    print(f"host: {machine_facts()}")
    print(f"HEAD: {head}")
    print(f"before: {_load(read_now())}")
    print(f"bound: {FRACTION:g} x {PROOF_CLEARANCE_MM:g} mm = {BOUND_MM:g} mm")
    print("| Size | Hand | Preset (lin mm / ang rad) | Triangles | Bytes | Max deviation mm "
          "| p99 deviation mm |")
    print("|---|---|---|---|---|---|---|")
    rows: list[Row] = []
    for size in SIZES:
        d, pitch = (float(v) for v in PITCH[size])
        for left_hand in HANDS:
            rod = helical.thread(d, pitch, ROD_PITCHES * pitch, left_hand=left_hand)
            for lin, ang in [(step, ANGULAR_RAD) for step in LADDER_MM] + [PREVIEW]:
                row = measure(size, left_hand, rod, lin, ang)
                print(_row(row), flush=True)
                rows.append(row)
    ladder = [r for r in rows if r.angular == ANGULAR_RAD]
    print(f"after: {_load(read_now())} (includes the run's own meshing load)")
    print(f"selected: {rule(ladder):g} mm at {ANGULAR_RAD:g} rad")


if __name__ == "__main__":
    main()
