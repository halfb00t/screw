"""The D-03 probe of Phase 4: a hex head and a plain shank fused to the shipped thread.

Phase 2 built no head (02 D-08), so nothing had measured what the two planar fuses do to the
solid count, validity, volume, mesh closedness or export size. This records it before any plan
fixes an expectation about the fused bolt. It bounds nothing: single runs, one host, load not
controlled. Kernel side (it imports `cadquery`), run by hand: `python -m bench.head_fuse`.

The head values below (`s`, `k`, and the thread lengths `t`) are preview readings, UNVERIFIED:
probe inputs chosen to span the corpus, not table rows. D-15's UNVERIFIED scan covers
`src/screw/tables/` only, and nothing here is read by `src/`.

The thread is the shipped builder's (`helical.thread`), never a copy of it, so what is measured
is what ships.
"""

from __future__ import annotations

import math
import resource
import subprocess
import time
from dataclasses import dataclass

import cadquery as cq

from bench import machine_facts
from bench.build_time import stl_size
from bench.quiet import Reading, read_now
from bench.thread_spike.measure import mesh_stl, stl_check
from screw.calc.thread import section_area
from screw.solid import TESSELLATION, helical, precise_volume


@dataclass(frozen=True)
class Case:
    label: str
    d: float
    pitch: float
    length: float
    s: float
    k: float
    t: float
    left_hand: bool = False


# s, k and t of every case are UNVERIFIED preview readings (probe inputs, not table rows).
CASES: tuple[Case, ...] = (
    Case("M2 x 4", 2.0, 0.4, 4.0, 4.0, 1.4, 4.0),  # full thread, preview reading
    Case("M6 x 20", 6.0, 1.0, 20.0, 10.0, 4.0, 20.0),  # full thread, preview reading
    Case("M6 x 30", 6.0, 1.0, 30.0, 10.0, 4.0, 18.0),  # partial thread, preview reading
    Case("M10 x 80", 10.0, 1.5, 80.0, 16.0, 6.4, 26.0),  # partial thread, preview reading
    Case("M16 x 160", 16.0, 2.0, 160.0, 24.0, 10.0, 44.0),  # partial thread, preview reading
    Case("M20 x 200", 20.0, 2.5, 200.0, 30.0, 12.5, 200.0),  # full thread, preview reading
    Case("M6 x 30 left-hand", 6.0, 1.0, 30.0, 10.0, 4.0, 18.0, True),  # left-hand, preview reading
)


def _shape(w: cq.Workplane) -> cq.Shape:
    """The one solid on a workplane, narrowed from `val()`'s union."""
    v = w.val()
    assert isinstance(v, cq.Shape)
    return v


def _head_and_shank(case: Case) -> cq.Shape:
    """Head plus shank without the thread: the head alone when the thread runs to the head."""
    # circumscribed=True makes `s` the across-flats size; the default inscribes the polygon in a
    # circle of that diameter and reads 0.75 of the closed form (RESEARCH Pitfall 1).
    head = _shape(cq.Workplane("XY").workplane(offset=case.length).polygon(
        6, case.s, circumscribed=True).extrude(case.k))
    if case.length > case.t:
        shank = _shape(cq.Workplane("XY").workplane(offset=case.t).circle(case.d / 2).extrude(
            case.length - case.t))
        return shank.fuse(head)
    return head


def assemble(case: Case) -> tuple[cq.Shape, cq.Solid]:
    """(the fused part, the bare thread): thread z 0..t, shank t..length, head length..length+k.

    `Shape.fuse` has no `clean=` keyword (RESEARCH Pitfall 2) and the research probe saw no
    change from `.clean()`, so none is called.
    """
    thread = helical.thread(case.d, case.pitch, case.t, left_hand=case.left_hand)
    return thread.fuse(_head_and_shank(case)), thread


def closed(case: Case) -> float:
    """Whole-bolt closed form: thread section over t, plain cylinder over the rest, hex prism."""
    return (section_area(case.d, case.pitch) * case.t
            + math.pi * (case.d / 2) ** 2 * (case.length - case.t)
            + math.sqrt(3) / 2 * case.s * case.s * case.k)


def probe(case: Case) -> dict[str, object]:
    t0 = time.perf_counter()
    part, thread = assemble(case)
    seconds = time.perf_counter() - t0
    expected = closed(case)
    bare_expected = section_area(case.d, case.pitch) * case.t
    box = part.BoundingBox()
    out: dict[str, object] = {
        "label": case.label,
        "build_seconds": seconds,
        "solids": len(part.Solids()),
        "valid": bool(part.isValid()),
        "volume_error": precise_volume(part) / expected - 1,
        "thread_error": precise_volume(thread) / bare_expected - 1,
        "zmin": box.zmin,
        "zmax": box.zmax,
    }
    for quality in ("preview", "fine"):
        tolerance, angular = TESSELLATION[quality]
        data, _ = mesh_stl(part, tolerance, angular)
        size, triangles = stl_size(data)
        out[f"{quality}_triangles"] = triangles
        out[f"{quality}_bytes"] = size
        out[f"{quality}_open_edges"] = stl_check(data).open_edges
    tolerance, angular = TESSELLATION["fine"]
    out["head_shank_fine_bytes"] = stl_size(
        mesh_stl(_head_and_shank(case), tolerance, angular)[0])[0]
    # ru_maxrss is the peak over the whole process so far (bytes on macOS, KiB on Linux), so a
    # row reads the largest case run before it, not its own.
    out["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return out


def _row(r: dict[str, object]) -> str:
    return (f"| {r['label']} | {float(str(r['build_seconds'])):.2f} | {r['solids']} | {r['valid']} "
            f"| {float(str(r['volume_error'])):+.2e} | {float(str(r['thread_error'])):+.2e} "
            f"| {float(str(r['zmin'])):.4f} to {float(str(r['zmax'])):.4f} "
            f"| {r['preview_triangles']} / {r['fine_triangles']} "
            f"| {r['preview_bytes']} / {r['fine_bytes']} "
            f"| {r['preview_open_edges']} / {r['fine_open_edges']} "
            f"| {r['head_shank_fine_bytes']} | {r['peak_rss_bytes']} |")


def _load(reading: Reading) -> str:
    return f"load1 {reading.load1:.2f} at {reading.utc}"


def main() -> None:
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip()
    print(f"host: {machine_facts()}")
    print(f"HEAD: {head}")
    print(f"before: {_load(read_now())}")
    print("| Case | build+fuse s | solids | isValid | whole-part rel. volume error "
          "| bare-thread rel. volume error | z extent | triangles preview / fine "
          "| bytes preview / fine | open edges preview / fine | head+shank fine bytes "
          "| peak RSS so far (bytes, macOS) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for case in CASES:
        print(_row(probe(case)), flush=True)
    print(f"after: {_load(read_now())} (includes the run's own meshing load)")


if __name__ == "__main__":
    main()
