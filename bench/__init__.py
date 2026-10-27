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
from pathlib import Path


def machine_facts() -> str:
    """CPU count, CPU model, architecture and total RAM.

    Every number this harness reports must carry the machine that produced it -- a
    measurement's meaning changes with the hardware behind it, so this is printed alongside
    every scenario and every sweep row, shared by every half rather than computed twice.
    """
    cpu = os.cpu_count()
    ram = _total_ram_gib()
    ram_text = f"{ram:.1f} GiB RAM" if ram is not None else "RAM unknown"
    model = cpu_model()
    # GitHub mixes CPU generations behind one `ubuntu-latest` label, so a figure without the
    # model that produced it cannot be compared with another run's (07 D-01).
    model_text = f", {model}" if model is not None else ""
    return f"{cpu if cpu is not None else '?'} CPUs{model_text}, {platform.machine()}, {ram_text}"


def cpu_model(text: str | None = None) -> str | None:
    """The first `model name` of `/proc/cpuinfo` (or of `text`), or `None` where there is none.

    `None` and not a guess: macOS has no `/proc`, and an arm64 Linux kernel names no model
    there, so an absent line is an unknown model, never a plausible one (L02).
    """
    if text is None:
        try:
            text = Path("/proc/cpuinfo").read_text()
        except OSError:
            return None
    for line in text.splitlines():
        key, _, value = line.partition(":")
        if key.strip() == "model name" and value.strip():
            return value.strip()
    return None


def host_facts() -> dict[str, object]:
    """The host facts a runner figure must carry (07 D-01), as one JSON-ready record.

    `GITHUB_RUN_ID`, `GITHUB_JOB` and `GITHUB_SHA` are present only when the environment sets
    them: a laptop run carries no run id, and an invented one would point at the wrong run.
    """
    facts: dict[str, object] = {
        "nproc": os.cpu_count(),
        "mem_total_bytes": _mem_total_bytes(),
        "cpu_model": cpu_model(),
        "kernel": platform.release(),
        "machine": platform.machine(),
    }
    for name in ("GITHUB_RUN_ID", "GITHUB_JOB", "GITHUB_SHA"):
        value = os.environ.get(name)
        if value:
            facts[name] = value
    return facts


def _mem_total_bytes() -> int | None:
    """`MemTotal` of `/proc/meminfo` (kB, times 1024), or `None` without a `/proc`."""
    try:
        text = Path("/proc/meminfo").read_text()
    except OSError:
        return None
    for line in text.splitlines():
        if line.startswith("MemTotal:"):
            fields = line.split()
            if len(fields) >= 2 and fields[1].isdigit():
                return int(fields[1]) * 1024
    return None


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
