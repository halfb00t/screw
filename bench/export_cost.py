"""Re-measures spur L19's gzip-level table and L24's mesh-copy cost, on demand, for one part.

Both decisions came from one-off probes nobody could re-run, and screw carries them over
unmeasured (`src/screw/app.py` `_GZIP_LEVEL`, `src/screw/solid/__init__.py` `_write_export`).
This is the committed instrument that reproduces them, so a threaded part's cost is measured
rather than assumed to match a gear's. What it prints is a measurement of one part on one
machine, not a bound (L07).

Not part of `make verify`: it builds a fine STL (seconds, for a threaded part) and forks six
child processes for the mesh-copy comparison, and a timing assertion on shared hardware would
flap.

Run it as `make bench.export SET="d=100 length=200"`, or directly as
`.venv/bin/python -m bench.export_cost --set "d=100 length=200"` from the repo root: the `-m`
form puts the root on `sys.path` so `import bench` resolves (`tests/test_bench.py` says why).
`--child {copy,in-place}` is internal: the mesh-copy section re-invokes this module as a
subprocess with it, one fresh process per run, so the parent's own `ru_maxrss` is always that
one run's peak and never a maximum carried over from an earlier run.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import platform
import resource
import statistics
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import TypedDict

from bench import machine_facts
from bench.build_time import load_sweep, stl_size
from screw import solid
from screw.params import BoltParams

# spur L19's own table shape: five single-threaded runs (median), ten concurrent calls,
# three walls of ten (median).
GZIP_LEVELS: tuple[int, ...] = (1, 6, 9)
SINGLE_RUNS = 5
CONCURRENT = 10
CONCURRENT_RUNS = 3
# spur L24's own reading: mean of 3, one process per run, export only (build excluded).
COPY_RUNS = 3


class _ChildPayload(TypedDict):
    """The one JSON line `--child` prints: the wire shape between the parent's subprocess
    call and `_run_child`, typed so the parent reads it without an `Any` (L04)."""

    export_ms: float
    peak_rss_bytes: int
    bytes: int
    triangles: int


@dataclass(frozen=True)
class GzipRow:
    """One level's row of L19's table: single-threaded median (ms), output bytes, and the
    10-concurrent wall median (ms)."""

    level: int
    single_ms: float
    out_bytes: int
    concurrent_ms: float


def maxrss_bytes(raw: int, system: str) -> int:
    """`ru_maxrss` is bytes on Darwin and kibibytes everywhere else (Linux, where the image
    runs), so the same reading means 1024x more on one than on the other."""
    return raw if system == "Darwin" else raw * 1024


def gzip_rows(data: bytes) -> list[GzipRow]:
    """L19's table, re-measured on `data`: per level, the median of `SINGLE_RUNS` timed
    `gzip.compress` calls, the output size, and the median of `CONCURRENT_RUNS` walls of
    `CONCURRENT` calls submitted together to a `ThreadPoolExecutor` -- zlib releases the GIL,
    the same in-process concurrency L19's own measurement relied on."""
    rows: list[GzipRow] = []
    for level in GZIP_LEVELS:
        single_samples: list[float] = []
        out_bytes = 0
        for _ in range(SINGLE_RUNS):
            t0 = time.perf_counter()
            compressed = gzip.compress(data, compresslevel=level)
            single_samples.append((time.perf_counter() - t0) * 1000)
            out_bytes = len(compressed)  # identical every run: compression is deterministic
        single_ms = statistics.median(single_samples)

        concurrent_samples: list[float] = []
        for _ in range(CONCURRENT_RUNS):
            with ThreadPoolExecutor(max_workers=CONCURRENT) as pool:
                t0 = time.perf_counter()
                futures = [pool.submit(gzip.compress, data, compresslevel=level)
                           for _ in range(CONCURRENT)]
                for f in futures:
                    f.result()
                concurrent_samples.append((time.perf_counter() - t0) * 1000)
        concurrent_ms = statistics.median(concurrent_samples)

        rows.append(GzipRow(level, single_ms, out_bytes, concurrent_ms))
    return rows


def _by_level(rows: list[GzipRow]) -> dict[int, GzipRow]:
    return {row.level: row for row in rows}


def _decisions(rows: list[GzipRow]) -> list[tuple[int, bool, float, float]]:
    """Walk 6 then 9 against the level currently adopted, not always level 1: one
    `(level, adopted, shrink_pct, wall_ratio)` tuple per candidate. Integer arithmetic
    decides the shrink clause (a `1 - a / b` form reads 0.0999... at exactly 10%); the wall
    clause compares the measured floats directly, `candidate <= 1.5 * current`.
    `shrink_pct` and `wall_ratio` are recomputed as floats for the printed verdict only,
    never for either decision clause."""
    by_level = _by_level(rows)
    current = by_level[1]
    decisions: list[tuple[int, bool, float, float]] = []
    for level in (6, 9):
        candidate = by_level[level]
        shrunk = 10 * (current.out_bytes - candidate.out_bytes) >= current.out_bytes
        wall_ok = candidate.concurrent_ms <= 1.5 * current.concurrent_ms
        adopted = shrunk and wall_ok
        shrink_pct = 100 * (current.out_bytes - candidate.out_bytes) / current.out_bytes
        wall_ratio = candidate.concurrent_ms / current.concurrent_ms
        decisions.append((level, adopted, shrink_pct, wall_ratio))
        if adopted:
            current = candidate
    return decisions


def select_gzip_level(rows: list[GzipRow]) -> int:
    """spur L19's rule: start at level 1; adopt 6 then 9 in turn when the candidate shrinks
    output by at least 10% of the level currently adopted **and** its 10-concurrent wall is at
    most 1.5x that level's wall."""
    level = 1
    for candidate_level, adopted, _, _ in _decisions(rows):
        if adopted:
            level = candidate_level
    return level


def find_set(sweep: Path | None, label: str) -> BoltParams:
    """The part whose label the sweep prints, or exit 2 listing the labels there are."""
    sets = load_sweep(sweep)
    for set_label, params in sets:
        if set_label == label:
            return params
    available = ", ".join(set_label for set_label, _ in sets)
    print(f"error: no set labeled {label!r} -- available: {available}", file=sys.stderr)
    raise SystemExit(2)


def _run_child(params: BoltParams, mode: str) -> int:
    """`--child {copy,in-place}`: build `params` (untimed) and time one fine-STL export either
    on `shape.copy()` (what `solid.export` does, L24) or on the cached shape itself. Prints one
    JSON line with the export time, this process's own peak RSS, and the exported STL's byte and
    triangle counts; nothing else goes to stdout."""
    shape = solid.build(params)
    tol, ang = solid.TESSELLATION["fine"]
    with tempfile.TemporaryDirectory(prefix="screw-export-cost-") as d:
        path = Path(d) / f"{params.slug()}.stl"
        t0 = time.perf_counter()
        if mode == "copy":
            shape.copy().exportStl(str(path), tolerance=tol, angularTolerance=ang,
                                   ascii=False, relative=False)
        else:
            shape.exportStl(str(path), tolerance=tol, angularTolerance=ang,
                            ascii=False, relative=False)
        export_ms = (time.perf_counter() - t0) * 1000
        data = path.read_bytes()
    n_bytes, n_triangles = stl_size(data)
    peak = maxrss_bytes(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, platform.system())
    payload: _ChildPayload = {
        "export_ms": export_ms,
        "peak_rss_bytes": peak,
        "bytes": n_bytes,
        "triangles": n_triangles,
    }
    print(json.dumps(payload))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bench.export_cost",
        description="Re-measure spur L19's gzip-level table and L24's mesh-copy cost for one "
                    "part.",
    )
    parser.add_argument("sweep", nargs="?", type=Path, default=None,
                        help="JSON file of query-parameter sets. Default: the skeleton corpus.")
    parser.add_argument("--set", dest="label", required=True,
                        help="The part's label, exactly as bench.build_time prints it.")
    parser.add_argument("--child", choices=("copy", "in-place"), default=None,
                        help=argparse.SUPPRESS)  # internal: see module docstring
    args = parser.parse_args(argv)

    params = find_set(args.sweep, args.label)

    if args.child is not None:
        return _run_child(params, args.child)

    # Read before any building starts, the same discipline as bench.build_time.
    load1, load5, load15 = os.getloadavg()
    versions = ", ".join(f"{dist} {metadata.version(dist)}"
                         for dist in ("cadquery", "cadquery-ocp"))
    head = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    print(f"- Machine: {machine_facts()}")
    print(f"- Python: {platform.python_version()}")
    print(f"- Kernel: {versions}")
    print(f"- HEAD: `{head}`")
    print(f"- Set: {args.label}")
    print(f"- Load averages at start: {load1:.2f}, {load5:.2f}, {load15:.2f}")
    print()

    data = solid.export(params, "stl", "fine")
    n_bytes, n_triangles = stl_size(data)
    print(f"- Fine STL: {n_bytes} bytes, {n_triangles} triangles")
    print()

    print("### gzip level (L19)")
    rows = gzip_rows(data)
    print("| Level | Single-threaded median (ms) | Output bytes (% of input) | "
          "10-concurrent wall, median of 3 (ms) |")
    print("|---|---|---|---|")
    for row in rows:
        pct = 100 * row.out_bytes / len(data)
        print(f"| {row.level} | {row.single_ms:.1f} | {row.out_bytes} ({pct:.1f}%) | "
              f"{row.concurrent_ms:.1f} |")
    print()
    decisions = _decisions(rows)
    level = select_gzip_level(rows)
    detail = "; ".join(
        f"level {candidate_level}: {shrink:.2f}% smaller (bar 10%), {wall:.2f}x wall "
        f"(bar 1.5x) -- {'adopted' if adopted else 'not adopted'}"
        for candidate_level, adopted, shrink, wall in decisions
    )
    print(f"**L19 selects:** level {level} -- {detail}")
    print()

    print("### Mesh copy (L24)")
    print(f"{COPY_RUNS} child processes per mode, alternating copy and in-place, one fresh "
          "process per run so peak RSS is that run's own reading, never a cumulative maximum "
          "carried over from an earlier one.")
    mesh_rows: list[tuple[int, str, float, float, int]] = []
    copy_runs: list[_ChildPayload] = []
    inplace_runs: list[_ChildPayload] = []
    sweep_args = [] if args.sweep is None else [str(args.sweep)]
    for run in range(1, COPY_RUNS + 1):
        for mode, bucket in (("copy", copy_runs), ("in-place", inplace_runs)):
            child = subprocess.run(
                [sys.executable, "-m", "bench.export_cost", *sweep_args,
                 "--set", args.label, "--child", mode],
                capture_output=True, text=True, check=False,
            )
            if child.returncode != 0 or not child.stdout.strip():
                sys.stderr.write(child.stderr)
                raise SystemExit(
                    f"error: --child {mode} run {run} exited {child.returncode} "
                    "without a payload (its stderr is above)")
            child_payload: _ChildPayload = json.loads(child.stdout.strip().splitlines()[-1])
            bucket.append(child_payload)
            peak_mib = child_payload["peak_rss_bytes"] / (1024 * 1024)
            mesh_rows.append((run, mode, child_payload["export_ms"], peak_mib,
                              child_payload["triangles"]))

    print("| Run | Mode | Export (ms) | Peak RSS (MiB) | Triangles |")
    print("|---|---|---|---|---|")
    for run, mode, export_ms, peak_mib, triangles in mesh_rows:
        print(f"| {run} | {mode} | {export_ms:.1f} | {peak_mib:.1f} | {triangles} |")
    print()

    copy_export_mean = statistics.mean(r["export_ms"] for r in copy_runs)
    inplace_export_mean = statistics.mean(r["export_ms"] for r in inplace_runs)
    copy_rss_mean = statistics.mean(r["peak_rss_bytes"] for r in copy_runs) / (1024 * 1024)
    inplace_rss_mean = statistics.mean(r["peak_rss_bytes"] for r in inplace_runs) / (1024 * 1024)
    delta_ms = copy_export_mean - inplace_export_mean
    delta_mib = copy_rss_mean - inplace_rss_mean
    # Signed format (`:+`), not a hardcoded "+": a run where copy reads cheaper than in place
    # by chance must print its honest sign, never a plausible-looking "+" (L02).
    print(f"**Copy cost:** {delta_ms:+.1f} ms mean export, {delta_mib:+.1f} MiB mean "
          "peak RSS over in place (mean of 3 each).")

    all_triangles = {r["triangles"] for r in copy_runs} | {r["triangles"] for r in inplace_runs}
    if len(all_triangles) != 1:
        print(f"error: copy and in-place exports disagree on triangle count "
              f"({sorted(all_triangles)}) -- L24's invariant (a copy meshes identically) "
              "did not hold on this part", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
