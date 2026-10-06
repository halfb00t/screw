"""Measurement harness, ported from spur's `bench/` (L07: "as a harness, not as numbers").

Rerunnable and committed so every figure it prints stays falsifiable by whoever doubts it
later, not a number quoted from a session that has ended. The harness is the deliverable:
nothing it prints in Phase 1 is a bound. Phase 7 re-sweeps on threaded parts under
linux/amd64 (OPER-02) and is what turns a measurement into a limit.

`bench.build_time` and `bench.export_cost` time `screw.solid` in-process. `bench.latency`
measures `/api/health` under load against a running `make serve`; `bench.memory` sweeps
container memory with `docker compose`. None of them is part of `make verify`: they need
minutes (and a service or a daemon), and a timing assertion on shared hardware would flap
until someone stopped believing it.
"""

from __future__ import annotations

import os
import platform


def machine_facts() -> str:
    """CPU count, architecture and total RAM.

    Every number this harness reports must carry the machine that produced it -- a
    measurement's meaning changes with the hardware behind it, so this is printed alongside
    every scenario and every sweep row, shared by every half rather than computed twice.
    """
    cpu = os.cpu_count()
    ram = _total_ram_gib()
    ram_text = f"{ram:.1f} GiB RAM" if ram is not None else "RAM unknown"
    return f"{cpu if cpu is not None else '?'} CPUs, {platform.machine()}, {ram_text}"


def _total_ram_gib() -> float | None:
    """Total RAM in GiB via `os.sysconf`, or `None` where the platform exposes neither.

    spur verified `os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')` against
    `sysctl hw.memsize` on an arm64 macOS host (34359738368 bytes = 32 GiB); both names are
    also defined on glibc Linux, where the memory half of this harness runs.
    """
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / (1024**3)
    except (ValueError, OSError, AttributeError):
        return None
