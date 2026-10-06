"""The kernel child: one JSON request line in, one JSON record line out (kernel module).

Run as `python -m bench.thread_spike.worker` by `runner.Worker`. JSON only, and stdout carries
nothing else: the parent reads one line per request and a stray print would desynchronise it.
This process holds the OpenCascade memory and is the one that may segfault, hang or leak, which
is why the parent is a separate, kernel-free process (RESEARCH Pattern 3).

It measures; it does not judge. Whether a row is ok is decided by `verdict.classify_row` in the
parent, against the closed form this process never sees.
"""

from __future__ import annotations

import json
import os
import sys
import time

from bench.thread_spike import helical, measure
from bench.thread_spike.verdict import (
    MeshRecord,
    RowRecord,
    RowRequest,
    failed_record,
    parse_request,
)


def run_row(request: RowRequest) -> RowRecord:
    """Build one row and measure it; any exception becomes a `failure` record."""
    if request["kind"] != "rod":
        return failed_record(request, "failure", f"unknown row kind {request['kind']!r}")
    try:
        t0 = time.perf_counter()
        shape = helical.thread(request["d"], request["pitch"], request["turns"],
                               clearance=request["clearance"], left_hand=request["left_hand"],
                               k=request["k"])
        build_s = time.perf_counter() - t0
        solids = len(shape.Solids())
        is_valid = bool(shape.isValid())
        t0 = time.perf_counter()
        precise = measure.precise_volume(shape)
        volume_s = time.perf_counter() - t0
        default = measure.default_volume(shape)
        meshes: list[MeshRecord] = []
        for name, tolerance, angular in request["presets"]:
            data, mesh_s = measure.mesh_stl(shape, tolerance, angular)
            check = measure.stl_check(data)
            meshes.append({
                "preset": name, "tolerance": tolerance, "angular": angular,
                "triangles": check.triangles, "bytes": len(data), "mesh_s": mesh_s,
                "checked": True, "watertight": check.watertight, "open_edges": check.open_edges,
                "stl_volume": check.signed_volume, "surface_area": check.surface_area,
            })
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
    }


def main() -> None:
    for line in sys.stdin:
        record = run_row(parse_request(line))
        sys.stdout.write(json.dumps(record) + "\n")
        sys.stdout.flush()
    sys.stdout.flush()
    # OCP objects freed at interpreter teardown can segfault after the record is written
    # (RESEARCH Pitfall 4, provoked once: exit 139 at teardown). The parent has its line; skip
    # the teardown.
    os._exit(0)


if __name__ == "__main__":
    main()
