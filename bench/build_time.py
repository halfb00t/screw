"""Per-part build, fine-STL and STEP export time, against `SCREW_BUILD_TIMEOUT`.

Measures, per part, build wall time with the solid cache cleared, fine-STL export time and
STEP export time, in-process, through the same `screw.solid` code a worker runs. Not part of
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
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

from pydantic import ValidationError

from bench import machine_facts
from bench.corpus import corpus
from screw import int_env, solid
from screw.params import BoltParams


@dataclass(frozen=True)
class Timing:
    label: str
    build: float
    stl: float
    step: float
    stl_bytes: int
    stl_triangles: int
    # No defaults on the two fields above: a default 0 would be a plausible-looking fake STL
    # size for a row nobody actually measured (L02).

    @property
    def worst_request(self) -> float:
        """The number `SCREW_BUILD_TIMEOUT` must fit.

        The timeout wraps one worker call, and a cold request builds once and then exports
        once, so build plus the slower of the two exports is what a request pays, not build
        plus both exports.
        """
        return self.build + max(self.stl, self.step)

    def inside(self, timeout: float) -> bool:
        return self.worst_request <= timeout


def label(entry: dict[str, object]) -> str:
    """`d=100 length=200`: the entry's own `key=value` pairs in order, numbers as `%g`.

    One spelling for the corpus and for a sweep file, so a label printed by one is found by
    `bench.export_cost --set` in the other.
    """
    return " ".join(
        f"{k}={v:g}" if isinstance(v, int | float) else f"{k}={v}" for k, v in entry.items())


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


def time_set(p: BoltParams) -> tuple[float, float, float, int, int]:
    """Build wall time (cold solid cache), fine-STL export time, STEP export time, and the
    fine STL's byte and triangle counts.

    The size is read after the STL clock stops, so it does not inflate the timed region.
    """
    solid.clear_cache()
    t0 = time.perf_counter()
    solid.build(p)
    build_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    data = solid.export(p, "stl", "fine")
    stl_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    solid.export(p, "step")
    step_s = time.perf_counter() - t0
    stl_bytes, stl_triangles = stl_size(data)
    return build_s, stl_s, step_s, stl_bytes, stl_triangles


def report(path: Path | None, timings: list[Timing], timeout: int,
           load: tuple[float, float, float]) -> str:
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
        f"- SCREW_BUILD_TIMEOUT: {timeout} s, a cold request is one build plus one export",
        "",
        "| Parameter set | Build (s) | Fine STL (s) | STEP (s) | "
        f"Build + slower export (s) | Inside {timeout} s | Fine STL (bytes) | Triangles |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for t in timings:
        verdict = "yes" if t.inside(timeout) else "**NO**"
        lines.append(f"| {t.label} | {t.build:.2f} | {t.stl:.2f} | {t.step:.2f} | "
                     f"{t.worst_request:.2f} | {verdict} | {t.stl_bytes} | "
                     f"{t.stl_triangles} |")
    heaviest = max(timings, key=lambda t: t.worst_request)
    lines.append("")
    lines.append(f"**Heaviest:** {heaviest.label} -- {heaviest.worst_request:.2f} s "
                 f"of {timeout} s.")
    largest = max(timings, key=lambda t: t.stl_bytes)
    lines.append(f"**Largest fine STL:** {largest.label} -- {largest.stl_bytes} bytes, "
                 f"{largest.stl_triangles} triangles.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bench.build_time",
        description="Time build, fine-STL and STEP export per part, against "
                    "SCREW_BUILD_TIMEOUT.",
    )
    parser.add_argument(
        "sweep", nargs="?", type=Path, default=None,
        help="JSON file of query-parameter sets. Default: the skeleton corpus.")
    parser.add_argument(
        "--timeout", type=int, default=int_env("SCREW_BUILD_TIMEOUT", 30),
        help="Seconds a build plus its slower export must fit -- the same knob and default "
             "the app's lifespan passes to BuildPool.")
    args = parser.parse_args(argv)

    sets = load_sweep(args.sweep)  # fails before any build if a set is not buildable

    # Read before the first row builds, not after the sweep finishes.
    load = os.getloadavg()

    # Time every set before deciding the exit code -- a short-circuiting generator would
    # silently skip the rest.
    timings = [Timing(name, *time_set(p)) for name, p in sets]

    print(report(args.sweep, timings, args.timeout, load))

    over_budget = [t for t in timings if not t.inside(args.timeout)]
    for t in over_budget:
        print(f"warning: {t.label} is over budget: {t.worst_request:.2f} s of "
              f"{args.timeout} s", file=sys.stderr)
    return 1 if over_budget else 0


if __name__ == "__main__":
    sys.exit(main())
