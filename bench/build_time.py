"""Per-part build and export time, each artifact against its own timeout (L24).

Measures, per part, build wall time with the solid cache cleared, then the preview-STL, fine-STL
and STEP export times, in-process, through the same `screw.solid` code a worker runs, and judges
each artifact's cold wall against `calc.cost.BUILD_TIMEOUT_S` for that artifact. Not part of
`make verify`: a timing assertion on shared hardware would flap, and a threaded sweep will take
minutes. Run it with `make bench.build`, or `make bench.build SWEEP=<json>` for a file of
parameter sets; with no file it runs `bench.corpus`.

The output is a measurement of the machine named in its own header, not a bound (L07).
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

from pydantic import ValidationError

from bench import machine_facts
from bench.corpus import corpus, label
from screw import solid
from screw.calc.cost import ARTIFACTS, BUILD_TIMEOUT_S, Artifact, fits
from screw.params import BoltParams


@dataclass(frozen=True)
class Timing:
    label: str
    build: float
    exports: Mapping[Artifact, float]
    stl_bytes: int
    stl_triangles: int
    # No defaults on the two fields above: a default 0 would be a plausible-looking fake STL
    # size for a row nobody actually measured (L02).
    refused: frozenset[Artifact]
    # The artifacts the cost model refuses for this part as given. The service answers each
    # with a 422 before any build (L21), so none is ever held to a timeout.

    def cold_wall(self, artifact: Artifact) -> float:
        """What a cold request for `artifact` pays: one build and that artifact's one export,
        the wall `BUILD_TIMEOUT_S[artifact]` bounds (07 R2, L24)."""
        return self.build + self.exports[artifact]

    def over_timeout(self) -> list[Artifact]:
        """The admitted artifacts whose cold wall is past their timeout; at it is inside."""
        return [artifact for artifact in ARTIFACTS if artifact not in self.refused
                and self.cold_wall(artifact) > BUILD_TIMEOUT_S[artifact]]


def load_sweep(path: Path | None = None) -> list[tuple[str, BoltParams]]:
    """The parameter sets to time, each validated into a `BoltParams`.

    With no `path` that is `bench.corpus`; with one, a JSON list of the same query
    dictionaries. A set that fails validation cannot be timed and must not be silently
    skipped: raise, naming the file, the position and the set.
    """
    source = "the skeleton corpus" if path is None else str(path)
    raw: list[dict[str, object]] = corpus() if path is None else json.loads(path.read_text())
    sets: list[tuple[str, BoltParams]] = []
    for i, entry in enumerate(raw):
        try:
            p = BoltParams.model_validate(entry)
        except ValidationError as exc:
            raise ValueError(
                f"{source} set {i} ({label(entry)}) is not a buildable bolt: {exc}") from exc
        sets.append((label(entry), p))
    return sets


def stl_size(data: bytes) -> tuple[int, int]:
    """(byte count, triangle count) of a binary STL, the count read from the header's own
    little-endian uint32 at bytes 80-84 -- O(1), where walking every facet is for content
    proofs, not counting.

    Raises when the length disagrees with `84 + 50 * n`: a truncated file, or an ASCII STL
    that happens to carry 80 header-like bytes, would otherwise hand back a plausible but
    wrong count (L02).
    """
    n = int.from_bytes(data[80:84], "little")
    expected = 84 + 50 * n
    if len(data) != expected:
        raise ValueError(
            f"STL is {len(data)} bytes but its header's triangle count ({n}) implies "
            f"{expected} bytes -- truncated file or not a binary STL, refusing to "
            "report a triangle count that would be a plausible wrong number")
    return len(data), n


def time_set(p: BoltParams) -> tuple[float, dict[Artifact, float], int, int]:
    """Build wall time (cold solid cache), each artifact's export time after it, and the fine
    STL's byte and triangle counts.

    The size is read after the STL clock stops, so it does not inflate the timed region.
    """
    solid.clear_cache()
    t0 = time.perf_counter()
    solid.build(p)
    build_s = time.perf_counter() - t0
    exports: dict[Artifact, float] = {}
    t0 = time.perf_counter()
    solid.export(p, "stl", "preview")
    exports["stl-preview"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    data = solid.export(p, "stl", "fine")
    exports["stl-fine"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    solid.export(p, "step")
    exports["step"] = time.perf_counter() - t0
    stl_bytes, stl_triangles = stl_size(data)
    return build_s, exports, stl_bytes, stl_triangles


def _verdict(t: Timing, artifact: Artifact) -> str:
    if artifact in t.refused:
        return f"{t.cold_wall(artifact):.2f} refused (L21)"
    inside = t.cold_wall(artifact) <= BUILD_TIMEOUT_S[artifact]
    return f"{t.cold_wall(artifact):.2f} {'yes' if inside else '**NO**'}"


def report(path: Path | None, timings: list[Timing], load: tuple[float, float, float]) -> str:
    if not timings:
        raise ValueError(
            "the sweep produced no timings -- an empty sweep must be refused loudly, "
            "never printed as an empty table that reads as a pass")
    versions = ", ".join(f"{dist} {metadata.version(dist)}"
                         for dist in ("cadquery", "cadquery-ocp"))
    head = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    # `load` is read by the caller before the first row builds: a long sweep read its load
    # after the last row in spur, which made the "at start" label false.
    load1, load5, load15 = load
    sweep = "`bench/corpus.py` (the skeleton corpus)" if path is None else f"`{path}`"
    lines = [
        f"- Machine: {machine_facts()}",
        f"- Python: {platform.python_version()}",
        f"- Kernel: {versions}",
        f"- HEAD: `{head}`",
        f"- Sweep: {sweep}",
        f"- Load averages at start: {load1:.2f}, {load5:.2f}, {load15:.2f}",
        "- Timeouts (`calc.cost.BUILD_TIMEOUT_S`, L24): "
        + ", ".join(f"{a} {BUILD_TIMEOUT_S[a]:g} s" for a in ARTIFACTS)
        + "; a cold request is one build plus one export",
        "",
        "| Parameter set | Build (s) | Preview STL (s) | Fine STL (s) | STEP (s) | "
        + " | ".join(f"Build + {a} (s), inside" for a in ARTIFACTS)
        + " | Fine STL (bytes) | Triangles |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for t in timings:
        exports = " | ".join(f"{t.exports[a]:.2f}" for a in ARTIFACTS)
        verdicts = " | ".join(_verdict(t, a) for a in ARTIFACTS)
        lines.append(f"| {t.label} | {t.build:.2f} | {exports} | {verdicts} | {t.stl_bytes} | "
                     f"{t.stl_triangles} |")
    lines.append("")
    for a in ARTIFACTS:
        heaviest = max(timings, key=lambda t: t.cold_wall(a))
        lines.append(f"**Heaviest {a}:** {heaviest.label} -- {heaviest.cold_wall(a):.2f} s "
                     f"of {BUILD_TIMEOUT_S[a]:g} s.")
    largest = max(timings, key=lambda t: t.stl_bytes)
    lines.append(f"**Largest fine STL:** {largest.label} -- {largest.stl_bytes} bytes, "
                 f"{largest.stl_triangles} triangles.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bench.build_time",
        description="Time build and each artifact's export per part, against "
                    "calc.cost.BUILD_TIMEOUT_S for that artifact (L24).",
    )
    parser.add_argument(
        "sweep", nargs="?", type=Path, default=None,
        help="JSON file of query-parameter sets. Default: the skeleton corpus.")
    args = parser.parse_args(argv)

    sets = load_sweep(args.sweep)  # fails before any build if a set is not buildable

    # Read before the first row builds, not after the sweep finishes.
    load = os.getloadavg()

    # Time every set before deciding the exit code -- a short-circuiting generator would
    # silently skip the rest.
    timings = [Timing(name, *time_set(p), frozenset(a for a in ARTIFACTS if not fits(p, a)))
               for name, p in sets]

    print(report(args.sweep, timings, load))

    over = [(t, a) for t in timings for a in t.over_timeout()]
    for t, a in over:
        print(f"warning: {t.label} is over its {a} timeout: {t.cold_wall(a):.2f} s of "
              f"{BUILD_TIMEOUT_S[a]:g} s", file=sys.stderr)
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
