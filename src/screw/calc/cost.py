"""Per-artifact cost rules: which files a download can produce and how long a build may take.

Kernel-free and logger-free like the rest of `calc` (import-linter contracts 2 and 4): the
pool, the app and the bench harness all key on the same three artifact names, and plan 07-11
adds the admission cost model next to the timeouts it is measured against.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final, Literal, get_args

Artifact = Literal["stl-preview", "stl-fine", "step"]
ARTIFACTS: Final[tuple[Artifact, ...]] = get_args(Artifact)

# INTERIM (Phase 1 D-01, carried from spur; Phase 7 plan 07-16 replaces all three with
# measured values and a cited run). 30 s per build is spur's: its worst observed single build
# was 7.39 s (a 200-tooth fine gear, ten concurrent requests, host under contention), so 30 s is
# about 4x spur's observation -- a margin chosen for slower hardware on spur's corpus. It is
# not a measurement of screw: M6 x 20 builds in 0.09 s (planner probe 2026-10-10), while an
# in-cap off-row part can need minutes (03-RESEARCH Pitfall 5: d=100, pitch=5, length=1250,
# fine STL 152.6 s and 7875 MiB peak RSS, single run, macOS arm64, not a bound). So these are
# the backstop below the turn cap (D-01, D-18; `MAX_TURNS`), not a figure for the threads.
#
# Code constants with no environment override (D-16): a deployer on slower hardware re-sweeps
# and a superseding log entry records the new figure, so the number in force always cites the
# run that set it. Read-only, so a stray assignment cannot move a bound the log cites.
BUILD_TIMEOUT_S: Final[Mapping[Artifact, float]] = MappingProxyType(
    {"stl-preview": 30.0, "stl-fine": 30.0, "step": 30.0})


def artifact_of(fmt: str, quality: str) -> Artifact:
    """The artifact a download of `fmt` at `quality` produces.

    STEP ignores the quality (`solid._write_export` tessellates only for STL), so both of its
    qualities are one artifact with one timeout.
    """
    if quality not in ("preview", "fine"):
        raise ValueError(f"no artifact for quality {quality!r}")
    if fmt == "step":
        return "step"
    if fmt == "stl":
        return "stl-preview" if quality == "preview" else "stl-fine"
    raise ValueError(f"no artifact for format {fmt!r}")
