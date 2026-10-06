"""The kernel child: one JSON request line in, one JSON record line out (kernel module).

Run as `python -m bench.thread_spike.worker` by `runner.Worker`. JSON only, and stdout carries
nothing else: the parent reads one line per request and a stray print would desynchronise it.
With `--once` it serves exactly one request and exits: the only way a row gets a peak RSS, since
`ru_maxrss` is a process-lifetime high-water mark and a persistent worker's belongs to whichever
earlier row was biggest (RESEARCH Pitfall 5).
This process holds the OpenCascade memory and is the one that may segfault, hang or leak, which
is why the parent is a separate, kernel-free process (RESEARCH Pattern 3).

It measures; it does not judge. Whether a row is ok is decided by `verdict.classify_row` in the
parent, against the closed form this process never sees.
"""

from __future__ import annotations

import json
import os
import platform
import resource
import sys
import time
from collections.abc import Callable

import cadquery as cq

from bench.build_time import stl_size
from bench.export_cost import gzip_rows, maxrss_bytes, select_gzip_level
from bench.thread_spike import helical, measure
from bench.thread_spike.maths import TIP_CHAMFER_DEG
from bench.thread_spike.verdict import (
    GzipEntry,
    MeshRecord,
    RowRecord,
    RowRequest,
    failed_record,
    parse_request,
)


class _OnceProbe:
    """What only a fresh child may take: the peak RSS right after the row's one mesh and its
    gzip-1, before any STL check (the check alone adds about 0.7 GB in-process, RESEARCH
    Pitfall 5), then, after that reading, L19's gzip table on the same STL when asked."""

    def __init__(self, want_table: bool) -> None:
        self._want_table = want_table
        self.peak_rss_bytes: int | None = None
        self.table: list[GzipEntry] | None = None
        self.selected: int | None = None

    def __call__(self, data: bytes) -> None:
        self.peak_rss_bytes = maxrss_bytes(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, platform.system())
        if self._want_table:
            rows = gzip_rows(data)
            self.table = [(r.level, r.out_bytes, r.single_ms, r.concurrent_ms) for r in rows]
            self.selected = select_gzip_level(rows)


def _mesh_record(shape: cq.Shape, name: str, tolerance: float, angular: float,
                 request: RowRequest,
                 after_mesh: Callable[[bytes], None] | None = None) -> MeshRecord:
    """Mesh one preset of a rod, gzip it when the request names the preset, and check it unless
    it is over the request's triangle ceiling. The check runs after the timed region, and a
    skipped one is recorded as not checked, never as watertight. `after_mesh` sees the STL
    between its gzip and its check."""
    data, mesh_s = measure.mesh_stl(shape, tolerance, angular)
    triangles = stl_size(data)[1]
    gzip1_bytes: int | None = None
    gzip1_s: float | None = None
    if name in request["gzip_on"]:
        gzip1_bytes, gzip1_s = measure.gzip1(data)
    if after_mesh is not None:
        after_mesh(data)
    if triangles > request["check_ceiling"]:
        return {
            "preset": name, "tolerance": tolerance, "angular": angular, "triangles": triangles,
            "bytes": len(data), "mesh_s": mesh_s, "gzip1_bytes": gzip1_bytes,
            "gzip1_s": gzip1_s, "checked": False, "check_s": None, "watertight": None,
            "open_edges": None, "stl_volume": None, "surface_area": None,
        }
    t0 = time.perf_counter()
    check = measure.stl_check(data)
    check_s = time.perf_counter() - t0
    return {
        "preset": name, "tolerance": tolerance, "angular": angular,
        "triangles": check.triangles, "bytes": len(data), "mesh_s": mesh_s,
        "gzip1_bytes": gzip1_bytes, "gzip1_s": gzip1_s, "checked": True, "check_s": check_s,
        "watertight": check.watertight, "open_edges": check.open_edges,
        "stl_volume": check.signed_volume, "surface_area": check.surface_area,
    }


KINDS = ("rod", "void", "naive", "one_pipe", "ruled", "trim")


def _build(request: RowRequest) -> tuple[cq.Shape, float, float | None]:
    """The row's solid, the seconds its construction took and, on a `trim` row, the seconds the
    tip trim took on top (a rod is built first at the request's K, then trimmed, D-08)."""
    kind, d, pitch = request["kind"], request["d"], request["pitch"]
    t0 = time.perf_counter()
    if kind == "naive":
        shape: cq.Shape = helical.naive_sweep_fuse(d, pitch, request["length"])
    elif kind == "one_pipe":
        shape = helical.one_pipe(d, pitch, request["turns"], request["left_hand"])
    elif kind == "ruled":
        shape = helical.ruled_reference(d, pitch, request["length"])
    else:
        shape = helical.thread(d, pitch, request["turns"], clearance=request["clearance"],
                               left_hand=request["left_hand"], k=request["k"])
    build_s = time.perf_counter() - t0
    if kind != "trim":
        return shape, build_s, None
    assert isinstance(shape, cq.Solid)
    t0 = time.perf_counter()
    trimmed = helical.trim_tip(shape, d, pitch, request["length"], TIP_CHAMFER_DEG)
    return trimmed, build_s, time.perf_counter() - t0


def _refusal(request: RowRequest, once: bool) -> str | None:
    """Why this request cannot be answered honestly here, or `None`."""
    kind = request["kind"]
    if kind not in KINDS:
        return f"unknown row kind {kind!r}"
    if kind == "void" and (request["presets"] or request["step"]):
        return "a void row takes no presets and no STEP"
    if kind in ("naive", "ruled") and request["left_hand"]:
        return f"a {kind} row is right hand only"
    if request["want_gzip_table"] and not once:
        return "a gzip table is measured only in a --once child"
    if once and kind == "rod" and len(request["presets"]) != 1:
        return ("a --once rod row takes exactly one preset: its peak RSS is read after that "
                "mesh and before any check")
    if request["want_gzip_table"] and kind != "rod":
        return "a gzip table needs a rod row's STL"
    return None


def run_row(request: RowRequest, *, once: bool = False) -> RowRecord:
    """Build one row and measure it; any exception becomes a `failure` record.

    A `rod` is built, volumed, meshed at every requested preset and exported to STEP when
    asked. A `void` (the cutter a nut subtracts, built at the request's clearance) records the
    postcondition only: no mesh and no STEP, and a request that asks for one is refused. The
    comparison kinds (`naive`, `one_pipe`, `ruled`) are built by their own construction and
    measured the same way, and `trim` is a rod with its tip trimmed (D-06, D-08). The negative
    control and the ruled-surface reference are right-hand only.

    `once` is the `--once` child: a rod row then carries its peak RSS and, when the request asks
    for it, L19's gzip table. A persistent worker records neither, and refuses a request for
    the table.
    """
    refusal = _refusal(request, once)
    if refusal is not None:
        return failed_record(request, "failure", refusal)
    probe = _OnceProbe(request["want_gzip_table"]) if once and request["kind"] == "rod" else None
    try:
        shape, build_s, trim_s = _build(request)
        solids = len(shape.Solids())
        is_valid = bool(shape.isValid())
        t0 = time.perf_counter()
        precise = measure.precise_volume(shape)
        volume_s = time.perf_counter() - t0
        default = measure.default_volume(shape)
        meshes = [_mesh_record(shape, name, tolerance, angular, request, probe)
                  for name, tolerance, angular in request["presets"]]
        step_bytes: int | None = None
        step_s: float | None = None
        if request["step"]:
            step_bytes, step_s = measure.step_export(shape)
    except Exception as exc:  # any kernel exception is one recorded row, not a dead worker
        return failed_record(request, "failure", f"{type(exc).__name__}: {exc}")
    return {
        **request,
        "outcome": "built",
        "error": None,
        "solids": solids,
        "is_valid": is_valid,
        "precise_volume": precise,
        "default_volume": default,
        "build_s": build_s,
        "volume_s": volume_s,
        "meshes": meshes,
        "step_bytes": step_bytes,
        "step_s": step_s,
        "trim_s": trim_s,
        "peak_rss_bytes": None if probe is None else probe.peak_rss_bytes,
        "gzip_table": None if probe is None else probe.table,
        "gzip_selected": None if probe is None else probe.selected,
    }


def main() -> None:
    once = "--once" in sys.argv[1:]
    for line in sys.stdin:
        record = run_row(parse_request(line), once=once)
        sys.stdout.write(json.dumps(record) + "\n")
        sys.stdout.flush()
        if once:
            break
    sys.stdout.flush()
    # OCP objects freed at interpreter teardown can segfault after the record is written
    # (RESEARCH Pitfall 4, provoked once: exit 139 at teardown). The parent has its line; skip
    # the teardown.
    os._exit(0)


if __name__ == "__main__":
    main()
