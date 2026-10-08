"""The quiet-host gate: wait until the machine is idle enough for a timing to mean something.

Not part of `make verify` and not a bound: it decides whether a measurement run may start, it
measures nothing itself. Kernel-free on purpose (an import-linter contract keeps it so): it
runs in the parent process of a campaign, which must never hold OpenCascade memory.

A run that starts on a host that never quiets is recorded as non-decisive, never retried toward
a pass (D-17). Validity, solid-count and volume outcomes do not depend on load; timings do.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

# spur D-05's convention on the same 12-core host class (spur
# `13-latency-bar/investigation/session.py:40-45`: bar 1.5, three consecutive readings, 30 s
# apart, give up after 900 s). A host with an open agent session idles near 2.0, so a run only
# releases decisively with agent sessions closed; otherwise it reads non-decisive.
QUIET_BAR = 1.5
QUIET_SAMPLES = 3
QUIET_INTERVAL_S = 30.0
QUIET_CAP_S = 900.0


@dataclass(frozen=True)
class Reading:
    """One 1-minute load average and the UTC time it was read, so a figure printed later is
    never mistaken for the figure at the start of a run (spur WR-07)."""

    utc: str
    load1: float


@dataclass(frozen=True)
class QuietResult:
    decisive: bool
    readings: tuple[Reading, ...]


def _read_load1() -> float:
    return os.getloadavg()[0]


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def wait_quiet(
    bar: float = QUIET_BAR,
    samples: int = QUIET_SAMPLES,
    interval: float = QUIET_INTERVAL_S,
    cap: float = QUIET_CAP_S,
    *,
    read: Callable[[], float] = _read_load1,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], str] = _utc_now,
    clock: Callable[[], float] = time.monotonic,
) -> QuietResult:
    """Release decisively once the last `samples` readings are all strictly under `bar`.

    Strictly: a reading of exactly `bar` resets the run. Returns non-decisive, with every
    reading taken, once `clock()` reaches the deadline: at cap 900 and interval 30 that is 31
    readings, the last at t = 900. The effects are parameters so a test can inject a made-up
    host and no test needs a stopwatch.
    """
    taken: list[Reading] = []
    deadline = clock() + cap
    while True:
        taken.append(Reading(now(), read()))
        recent = taken[-samples:]
        if len(recent) >= samples and all(r.load1 < bar for r in recent):
            return QuietResult(True, tuple(taken))
        if clock() >= deadline:
            return QuietResult(False, tuple(taken))
        sleep(interval)


def read_now() -> Reading:
    """One reading, for the end of a run.

    Its 1-minute load includes the run's own load: `exportStl` meshes on every core, so a run
    that ends in a mesh reads busy because of itself. It is printed for the record, labelled as
    such, and never decides whether a run was quiet; the release at the start does.
    """
    return Reading(_utc_now(), _read_load1())
