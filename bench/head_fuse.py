"""The D-03 probe of Phase 4: a hex head and a plain shank fused to the shipped thread.

Phase 2 built no head (02 D-08), so nothing had measured what the two planar fuses do to the
solid count, validity, volume, mesh closedness or export size. This records it before any plan
fixes an expectation about the fused bolt. It bounds nothing: single runs, one host, load not
controlled. Kernel side (it imports `cadquery`), run by hand: `python -m bench.head_fuse`.

The head values below (`s`, `k`, and the thread lengths `t`) are preview readings, UNVERIFIED:
probe inputs chosen to span the corpus, not table rows. D-15's UNVERIFIED scan covers
`src/screw/tables/` only, and nothing here is read by `src/`.

Thread, shank and head are built by the shipped `screw.solid.bolt.thread` and `assemble` from a
`BoltParams` per case, never a copy, so what is measured is what ships. Since 06.1 the head is the
chamfered one (`product_head`), at each case's default `head_chamfer`, and `closed` carries the
chamfer term; the rows in `bench/RESULTS.md` predate it and are the sharp-head probe, to be
re-run before Phase 7 reads them. The first run of this
probe (2026-10-11) fused shank and head together before the thread, the reverse of the product's
order, so its table was evidence for a different boolean sequence (04-REVIEW WR-01); the table in
`bench/RESULTS.md` is the re-run through the shipped builder.
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
from screw.calc.thread import head_chamfer_depths, head_chamfer_volume, section_area
from screw.params import BoltParams
from screw.solid import TESSELLATION, bolt, precise_volume


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

    def params(self) -> BoltParams:
        """The case as the shipped parameter model: the probe builds what a request builds."""
        return BoltParams(d=self.d, pitch=self.pitch, length=self.length, s=self.s, k=self.k,
                          thread_length=self.t, left_hand=self.left_hand)


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


def product_head(p: BoltParams) -> cq.Shape:
    """The head `_build_bolt` fuses: the prism, with its top corners chamfered at `head_chamfer`
    degrees when that is above 0. The product's piece gate is not repeated here; this probe
    judges the fuse. `bench.end_cuts` imports it, so both sweeps assemble the same head."""
    head: cq.Shape = bolt.head_prism(p)
    if p.head_chamfer > 0:
        head = bolt.chamfer_head(p, head, head_chamfer_depths(p.s, p.k, p.head_chamfer)[1])
    return head


def head_chamfer_term(p: BoltParams) -> float:
    """The volume `product_head` has less than the sharp prism, from the closed form."""
    if not p.head_chamfer > 0:
        return 0.0
    cut = head_chamfer_depths(p.s, p.k, p.head_chamfer)[1]
    return head_chamfer_volume(p.s, p.head_chamfer, cut)


def _head_and_shank(case: Case) -> cq.Shape:
    """Head plus shank without the thread, for the `head+shank fine bytes` column only; the part
    under test comes from the shipped builder, not from here. The head alone when the thread
    runs to the head."""
    head = product_head(case.params())
    if case.length > case.t:
        shank = _shape(cq.Workplane("XY").workplane(offset=case.t).circle(case.d / 2).extrude(
            case.length - case.t))
        return shank.fuse(head)
    return head


def assemble(case: Case) -> tuple[cq.Shape, cq.Solid]:
    """(the fused part, the bare thread), built by the shipped `screw.solid.bolt` from the case's
    `BoltParams`: thread z 0..t, then the shank t..length fused on, then the chamfered head
    length..length+k (`product_head`), in the product's order (`_build_bolt` calls `bolt.assemble`
    with the same head, less its tip cone and fillet ring, which this probe does not cut).
    `Shape.fuse` has no `clean=` keyword (RESEARCH Pitfall 2) and none is called, as in the
    product.
    """
    p = case.params()
    thread = bolt.thread(p)
    return bolt.assemble(p, thread, product_head(p)), thread


def closed(case: Case) -> float:
    """Whole-bolt closed form: thread section over t, plain cylinder over the rest, hex prism,
    less the head chamfer."""
    return (section_area(case.d, case.pitch) * case.t
            + math.pi * (case.d / 2) ** 2 * (case.length - case.t)
            + math.sqrt(3) / 2 * case.s * case.s * case.k - head_chamfer_term(case.params()))


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
