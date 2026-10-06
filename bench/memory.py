"""The container memory sweep: peak memory at N = 1, 2, 4 build workers over the corpus.

Drives `docker compose` itself, because `mem_limit` is a container setting and must be
measured under the container's own accounting -- on Linux/glibc, where `malloc_trim(0)`
actually does something (`_release_arenas`, `src/screw/solid/__init__.py`).

`sweep` brings the service up at each N, drives the corpus (`bench/corpus.py`) through
`/api/bolt/model.stl?quality=fine`, and records the peak. `confirm` re-runs the same corpus at a
candidate `mem_limit` and reports the failure count. Neither is a bound: the Phase 1 corpus is
12 plain cylinders far below the D-14 corner, and the interim `mem_limit: 4g` in
`compose.yaml` is spur's figure that Phase 7 re-sweeps (OPER-02).

Not part of `make verify`: it needs a running Docker daemon and minutes. Run it with
`make bench.memory`. The service is published on the host port of `--base-url` (default 8000,
the one `compose.yaml` publishes) with `docker compose run -p`, so a host whose 8000 is taken
by another project can point the sweep at a free one without editing `compose.yaml`.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx2 as httpx

from bench import machine_facts
from bench.corpus import corpus

DEFAULT_BASE_URL = "http://127.0.0.1:8000"

# A fixed default, not os.cpu_count(): a machine-dependent worker count would make a measured
# mem_limit untrue somewhere, the same reasoning that keeps parameter defaults absolute (L02).
# This is what compose.yaml ships.
SHIPPING_DEFAULT_WORKERS = 2

# The port the image listens on (Dockerfile `SCREW_PORT`); the host side comes from --base-url.
CONTAINER_PORT = 8000

# docker stats' MEM USAGE column, longest suffix first -- "MiB" itself ends in "B", so
# checking "B" before "KiB"/"MiB"/"GiB" would misparse every non-byte value.
_MEM_UNITS: list[tuple[str, int]] = [
    ("GiB", 1024**3), ("MiB", 1024**2), ("KiB", 1024), ("B", 1),
]

POLL_INTERVAL = 0.5  # seconds between docker stats samples

# The sweep's own ceiling, applied through the same override mechanism `confirm` uses, so a
# re-run can never be silently capped by whatever compose.yaml currently ships. spur's first
# sweep, still under its shipped `mem_limit: 2g`, read exactly 2048.0 MiB for both N=2 and N=4:
# the cap itself, printed as if it were a peak. Fixed, not derived from the host's RAM, for the
# reason SHIPPING_DEFAULT_WORKERS gives. Safe to pick by hand because an undersized value is
# not silent: a row that reaches it is refused (capped, no peak number), see `_is_capped`.
_SWEEP_MEM_LIMIT_BYTES = 8 * 1024**3  # 8589934592

# A capped row does not creep up on the ceiling, it reads it. 1% is a small stated fraction
# chosen to absorb `docker stats`' own one-decimal-MiB rounding (~0.05 MiB against an 8 GiB
# ceiling) without being wide enough to call a real, honest peak capped.
_CAP_TOLERANCE_FRACTION = 0.01


def _is_capped(peak_bytes: int, ceiling_bytes: int) -> bool:
    """Whether a sampled peak is the sweep's own container ceiling showing up as if it were a
    measurement, not a real footprint. Pure and Docker-free so tests pin every case."""
    return peak_bytes >= ceiling_bytes * (1 - _CAP_TOLERANCE_FRACTION)


def _parse_mem(text: str) -> int:
    """Parse a `docker stats` size like "612.3MiB" into bytes."""
    for suffix, factor in _MEM_UNITS:
        if text.endswith(suffix):
            return int(float(text[: -len(suffix)]) * factor)
    raise ValueError(f"unrecognised docker stats memory size: {text!r}")


def _publish(base_url: str) -> str:
    """The `-p` value that puts the container's port on the host port `base_url` names."""
    port = urlparse(base_url).port
    if port is None:
        raise ValueError(f"--base-url {base_url!r} names no port")
    return f"127.0.0.1:{port}:{CONTAINER_PORT}"


def _wait_healthy(container: str, timeout: float = 120.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Health.Status}}", container],
            capture_output=True, text=True, check=False,
        )
        if result.stdout.strip() == "healthy":
            return
        time.sleep(2)
    raise RuntimeError(f"{container} never reported healthy within {timeout:.0f}s")


def _poll_peak_mem(container: str, stop: threading.Event, samples: list[int]) -> None:
    """Sampled container memory, in bytes, appended to `samples` in place.

    Read from `docker stats --no-stream`'s MEM USAGE field, polled for the whole run: a
    *sampled* peak, not the cgroup accounting's exact one. A spike narrower than the polling
    interval (and `docker stats --no-stream` itself takes longer than `POLL_INTERVAL`) is
    missed, and `bench/README.md` says so. `docker stats` over `docker exec ... cat
    /sys/fs/cgroup/memory.peak` because it needs no shell inside the image (non-root,
    `nologin`) and its output is stable across the cgroup v1/v2 split.
    """
    while not stop.is_set():
        result = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "{{.MemUsage}}", container],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            used = result.stdout.split("/")[0].strip()
            samples.append(_parse_mem(used))
        stop.wait(POLL_INTERVAL)


def _teardown(container: str) -> None:
    subprocess.run(["docker", "rm", "-f", container], capture_output=True, check=False)


def _drive_corpus(base_url: str) -> tuple[int, int]:
    """Run the whole corpus through `/api/bolt/model.stl?quality=fine`, one part at a time.

    Returns (request count, failure count).
    """
    requests = 0
    failures = 0
    with httpx.Client(timeout=120.0) as client:
        for part in corpus():
            requests += 1
            # corpus() is typed `dict[str, object]`; stringify every value rather than trust
            # its runtime type, since a query string is text either way.
            params = {k: str(v) for k, v in part.items()} | {"quality": "fine"}
            try:
                response = client.get(f"{base_url}/api/bolt/model.stl", params=params)
                response.raise_for_status()
            except httpx.HTTPError:
                failures += 1
    return requests, failures


@dataclass(frozen=True)
class SweepRow:
    n: int
    peak_bytes: int | None
    requests: int
    failures: int
    elapsed_s: float
    samples: int = 0  # how many docker stats readings the peak is the maximum of
    # Max of the first half of the samples against the second: did resident memory keep
    # climbing across the corpus, or plateau? One overall peak cannot tell "climbed once early
    # and stayed" from "kept climbing".
    early_peak_bytes: int | None = None
    late_peak_bytes: int | None = None
    note: str = ""


def _run_container(container: str, workers: int, mem_limit: str, base_url: str) -> None:
    """Start the compose service detached as `container` at `workers` build workers under
    `mem_limit`, and wait until it reports healthy. Raises what `subprocess`/`_wait_healthy`
    raise; the caller tears the container down."""
    override_path = _write_mem_limit_override(mem_limit)
    try:
        subprocess.run(
            ["docker", "compose", "-f", "compose.yaml", "-f", override_path, "run",
             "--rm", "-d", "--name", container, "-p", _publish(base_url),
             "-e", f"SCREW_BUILD_WORKERS={workers}", "screw"],
            check=True, capture_output=True,
        )
    finally:
        Path(override_path).unlink(missing_ok=True)
    _wait_healthy(container)


def _sweep_one(n: int, base_url: str) -> SweepRow:
    """Cold-start the service at SCREW_BUILD_WORKERS=n under the sweep's own ceiling, drive the
    corpus, tear down. The ceiling goes through the override file in Docker's byte form (an
    integer with a `b` suffix) so the number Compose applies and the number `_is_capped`
    compares against are literally the same constant."""
    container = f"screw-bench-n{n}"
    _teardown(container)  # a stray container from an earlier, aborted run
    try:
        _run_container(container, n, f"{_SWEEP_MEM_LIMIT_BYTES}b", base_url)
    except (subprocess.CalledProcessError, RuntimeError) as exc:
        print(f"warning: N={n} never came up: {exc}", file=sys.stderr)
        _teardown(container)
        return SweepRow(n, None, 0, 0, 0.0, note=str(exc))

    stop = threading.Event()
    samples: list[int] = []
    poller = threading.Thread(target=_poll_peak_mem, args=(container, stop, samples))
    poller.start()
    try:
        t0 = time.monotonic()
        requests, failures = _drive_corpus(base_url)
        elapsed = time.monotonic() - t0
    finally:
        # The teardown in a finally block: a refused connection or a Ctrl-C mid-corpus must
        # not leave a container holding the port and the memory.
        stop.set()
        poller.join()
        _teardown(container)

    if not samples:
        print(f"warning: N={n} produced no memory samples", file=sys.stderr)
        return SweepRow(n, None, requests, failures, elapsed, note="no memory samples")
    peak = max(samples)
    if _is_capped(peak, _SWEEP_MEM_LIMIT_BYTES):
        # A capped row is the sweep's own ceiling, not a measurement (L02): reported with no
        # peak number at all.
        print(f"warning: N={n} peak ({peak / (1024**2):.1f} MiB) reached the sweep's own "
              f"{_SWEEP_MEM_LIMIT_BYTES / (1024**3):.0f}g ceiling -- reporting no peak",
              file=sys.stderr)
        return SweepRow(n, None, requests, failures, elapsed, samples=len(samples),
                        note=f"capped at the sweep's own "
                             f"{_SWEEP_MEM_LIMIT_BYTES / (1024**3):.0f}g ceiling")
    mid = len(samples) // 2 or 1  # `or 1` guards a 1-sample run: both halves non-empty
    early_peak = max(samples[:mid])
    late_peak = max(samples[mid:]) if samples[mid:] else early_peak
    return SweepRow(n, peak, requests, failures, elapsed, samples=len(samples),
                    early_peak_bytes=early_peak, late_peak_bytes=late_peak)


def _sweep_table_markdown(rows: list[SweepRow], load: tuple[float, float, float]) -> str:
    load1, load5, load15 = load
    lines = [
        "## Memory sweep\n",
        f"- Machine: {machine_facts()}",
        f"- Load averages at start: {load1:.2f}, {load5:.2f}, {load15:.2f}",
        "- Peak read from: `docker stats --no-stream` MEM USAGE, polled every "
        f"{POLL_INTERVAL}s (a sampled peak, not the cgroup's exact accounting)",
        "- Early/late peak: max of the first half vs second half of the corpus run's samples",
        "",
        "| N (SCREW_BUILD_WORKERS) | Peak | Early peak | Late peak | Samples | Requests "
        "| Failures | Elapsed |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        peak = f"{row.peak_bytes / (1024**2):.1f} MiB" if row.peak_bytes is not None \
            else f"(none -- {row.note})"
        early = f"{row.early_peak_bytes / (1024**2):.1f} MiB" \
            if row.early_peak_bytes is not None else "--"
        late = f"{row.late_peak_bytes / (1024**2):.1f} MiB" \
            if row.late_peak_bytes is not None else "--"
        lines.append(f"| {row.n} | {peak} | {early} | {late} | {row.samples} | {row.requests} "
                     f"| {row.failures} | {row.elapsed_s:.1f}s |")
    return "\n".join(lines) + "\n"


def sweep(base_url: str = DEFAULT_BASE_URL) -> bool:
    """N = 1, 2, 4: peak container memory over the corpus, one row per N.

    Each N runs under the sweep's own ceiling -- whatever `mem_limit` compose.yaml currently
    ships cannot cap this measurement. Returns False if any row is incomplete (no samples,
    docker never came up, or the peak reached the ceiling and was refused rather than
    reported): a partial or self-capped sweep must never be mistaken for a finished one.
    """
    load = os.getloadavg()  # before the first container starts, not after the last row
    rows = [_sweep_one(n, base_url) for n in (1, 2, 4)]
    print(_sweep_table_markdown(rows, load))
    return all(row.peak_bytes is not None for row in rows)


def _write_mem_limit_override(mem_limit: str) -> str:
    """A one-line compose override file: the only way to set `mem_limit` per invocation, since
    `docker compose run` has no `--memory` flag (unlike plain `docker run`)."""
    with tempfile.NamedTemporaryFile(
        "w", suffix=".yaml", delete=False, prefix="screw-bench-mem-limit-",
    ) as handle:
        handle.write(f"services:\n  screw:\n    mem_limit: {mem_limit}\n")
        return handle.name


def confirm(mem_limit: str, base_url: str = DEFAULT_BASE_URL,
            workers: int = SHIPPING_DEFAULT_WORKERS) -> bool:
    """Re-run the corpus at a candidate `mem_limit`; report the failure count. Zero failures is
    what a candidate must show before anyone adopts it."""
    container = "screw-bench-confirm"
    _teardown(container)
    try:
        _run_container(container, workers, mem_limit, base_url)
    except (subprocess.CalledProcessError, RuntimeError) as exc:
        print(f"warning: confirm at mem_limit={mem_limit} never came up: {exc}",
              file=sys.stderr)
        _teardown(container)
        return False

    try:
        requests, failures = _drive_corpus(base_url)
    finally:
        _teardown(container)
    print(f"## Memory confirm: mem_limit={mem_limit}, SCREW_BUILD_WORKERS={workers}\n\n"
          f"- Machine: {machine_facts()}\n"
          f"- Requests: {requests}, failures: {failures}\n")
    if failures:
        print(f"warning: {failures} of {requests} requests failed at "
              f"mem_limit={mem_limit}", file=sys.stderr)
    return failures == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bench.memory",
        description="Container memory sweep over the corpus: drives docker compose itself, "
                    "because mem_limit is a container setting and must be measured under the "
                    "container's own accounting.",
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    sweep_parser = subparsers.add_parser(
        "sweep", help="N = 1, 2, 4: peak container memory over the corpus")
    sweep_parser.add_argument("--base-url", default=DEFAULT_BASE_URL,
                              help=f"Default: {DEFAULT_BASE_URL}")

    confirm_parser = subparsers.add_parser(
        "confirm", help="Re-run the corpus at a candidate mem_limit; report failures")
    confirm_parser.add_argument("mem_limit", help="Candidate mem_limit, e.g. 2g")
    confirm_parser.add_argument("--workers", type=int, default=SHIPPING_DEFAULT_WORKERS,
                                help=f"SCREW_BUILD_WORKERS. Default: {SHIPPING_DEFAULT_WORKERS}")
    confirm_parser.add_argument("--base-url", default=DEFAULT_BASE_URL,
                                help=f"Default: {DEFAULT_BASE_URL}")

    args = parser.parse_args(argv)
    if args.mode == "sweep":
        return 0 if sweep(args.base_url) else 1
    return 0 if confirm(args.mem_limit, args.base_url, args.workers) else 1


if __name__ == "__main__":
    sys.exit(main())
