"""The half of a reading that runs inside the production container (07 D-15).

`bench.oper` (the parent, kernel-free) starts one fresh container of the image per reading and runs
`python -m bench.oper_child '<point json>'` in it. This module is that process: one cold build,
one export and a level-1 gzip of it, then the cgroup's own peak, printed as exactly one JSON line.
It runs in the image because that is the artefact whose `mem_limit` the figure sets: Debian's
glibc and the container's cgroup exist nowhere else (07-RESEARCH A1), and `memory.peak` is the
cgroup's exact high-water mark where `ru_maxrss` and `docker stats` are narrower or coarser (D-02).

A reading it cannot stand behind carries a status and no figure (L02): a kernel refusal is
`refused` with its class, an unreadable cgroup is `no_cgroup`. The statuses the parent adds
(`capped`, `killed`, `crashed`) are the ones a dead child cannot report itself.
"""

from __future__ import annotations

import gzip
import json
import math
import resource
import sys
import time
from collections.abc import Callable, Mapping
from functools import partial
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    import cadquery as cq

# `fmt, quality` as `screw.solid.export` takes them. STEP ignores the quality, so "fine" is only
# the signature's default.
_ARTIFACTS: dict[str, tuple[Literal["stl", "step"], Literal["preview", "fine"]]] = {
    "stl-preview": ("stl", "preview"),
    "stl-fine": ("stl", "fine"),
    "step": ("step", "fine"),
}


class CgroupUnavailable(RuntimeError):  # noqa: N818 -- a condition, named for what is missing
    """The container's memory peak could not be read, so the reading has no peak."""


def _is_cgroup2(root: Path) -> bool:
    try:
        mounts = (root / "proc/mounts").read_text()
    except OSError as exc:
        raise CgroupUnavailable(f"cannot read /proc/mounts: {exc}") from exc
    for line in mounts.splitlines():
        fields = line.split()
        if len(fields) >= 3 and fields[1] == "/sys/fs/cgroup" and fields[2] == "cgroup2":
            return True
    return False


def _read_count(path: Path) -> int:
    """A file holding one non-negative whole number of bytes. `max`, a float or a negative are
    not a count, and a made-up zero would read as a peak (L02)."""
    try:
        text = path.read_text().strip()
    except OSError as exc:
        raise CgroupUnavailable(f"cannot read {path}: {exc}") from exc
    if not (text.isascii() and text.isdigit()):
        raise CgroupUnavailable(f"{path} holds {text!r}, not a count of bytes")
    return int(text)


def read_peak(root: Path = Path("/")) -> int:
    """The container's peak memory in bytes: cgroup v2 `memory.peak` when `/sys/fs/cgroup` is a
    `cgroup2` mount, else v1 `memory.max_usage_in_bytes`.

    A v2 mount without `memory.peak` (a kernel before 5.19) does not fall back to a v1 file: the
    two are different accounting, and a stale file would be a plausible wrong number. Nothing
    readable raises `CgroupUnavailable`. `root` is `/` in the image and a fake tree in tests.
    """
    cgroup = root / "sys/fs/cgroup"
    if _is_cgroup2(root):
        return _read_count(cgroup / "memory.peak")
    return _read_count(cgroup / "memory" / "memory.max_usage_in_bytes")


def oom_kills(root: Path = Path("/")) -> int | None:
    """`oom_kill` of the cgroup's `memory.events`, or `None` where the file is absent. Unknown is
    not zero: the parent also reads Docker's own `OOMKilled`, and this is the corroboration."""
    try:
        events = (root / "sys/fs/cgroup/memory.events").read_text()
    except OSError:
        return None
    for line in events.splitlines():
        key, _, value = line.partition(" ")
        if key == "oom_kill" and value.strip().isdigit():
            return int(value)
    return None


def _versions() -> dict[str, str]:
    return {"cadquery": metadata.version("cadquery"),
            "cadquery_ocp": metadata.version("cadquery-ocp")}


def _maxrss_bytes() -> int:
    """`ru_maxrss` in bytes: kilobytes on Linux, bytes on macOS (where a laptop run is only a
    path check)."""
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return rss if sys.platform == "darwin" else rss * 1024


def _emit(record: dict[str, object]) -> None:
    print(json.dumps(record, allow_nan=False))


def _finding(shape: cq.Shape, build_s: float, measured: float, closed: float) -> dict[str, object]:
    """What a probe found in `shape`: the solid count, `isValid()` and the precise volume as a
    ratio to the closed form. Signed and ungated: a control is expected to be wrong, and a
    ratio of about -1 is an inverted solid that still reports valid."""
    ratio = measured / closed
    if not math.isfinite(ratio):
        raise ArithmeticError(f"the volume ratio {measured!r} / {closed!r} is not finite")
    return {"status": "ok", "build_s": build_s, "solids": len(shape.Solids()),
            "valid": bool(shape.isValid()), "volume_ratio": ratio}


def _probe_tail(d: float, pitch: float, turns: float, tail: float,
                left_hand: bool) -> dict[str, object]:
    """A bare thread of `turns` whole turns plus a sewn tail of `tail` mm, built through the
    production gate (`check_solid`: one solid, valid, inside THRD-04) with the builder's own
    guard lowered, so the tail walk reaches the kernel's wall instead of the guard (D-08)."""
    from screw.calc.thread import closed_volume
    from screw.solid import check_solid, helical

    length = turns * pitch + tail
    # `helical` imports MIN_TAIL_MM and does not export it, so the module's globals are where the
    # guard lives; its `thread` reads the global at call time.
    guard = vars(helical)
    saved = guard["MIN_TAIL_MM"]
    # The guard exists because a tail at or below about 1e-8 mm SIGSEGVs the process, the very
    # wall this probe walks (calc/thread.py MIN_TAIL_MM, probe 2026-10-10). Setting it to 0
    # lets the kernel see the tail; the container absorbs the crash and the parent records it.
    # Restored in the finally: the next probe in a long-lived process must meet the real guard.
    guard["MIN_TAIL_MM"] = 0.0
    try:
        started = time.perf_counter()
        shape = helical.thread(d, pitch, length, left_hand=left_hand)
        build_s = time.perf_counter() - started
    finally:
        guard["MIN_TAIL_MM"] = saved
    closed = closed_volume(d, pitch, length)
    measured = check_solid(shape, closed, part="thread")
    return _finding(shape, build_s, measured, closed)


def _probe_naive(d: float, pitch: float, length: float) -> dict[str, object]:
    """The negative control: a tooth swept along a helix and fused to a core cylinder."""
    from bench.thread_spike.helical import naive_sweep_fuse
    from screw.calc.thread import closed_volume
    from screw.solid import precise_volume

    started = time.perf_counter()
    shape = naive_sweep_fuse(d, pitch, length)
    build_s = time.perf_counter() - started
    return _finding(shape, build_s, precise_volume(shape), closed_volume(d, pitch, length))


def _probe_one_pipe(d: float, pitch: float, turns: float, left_hand: bool) -> dict[str, object]:
    """The comparison row for the sewn construction: one pipe over all `turns`."""
    from bench.thread_spike.helical import one_pipe
    from screw.calc.thread import closed_volume
    from screw.solid import precise_volume

    started = time.perf_counter()
    shape = one_pipe(d, pitch, turns, left_hand)
    build_s = time.perf_counter() - started
    return _finding(shape, build_s, precise_volume(shape),
                    closed_volume(d, pitch, turns * pitch))


def _number(args: Mapping[str, object], key: str) -> float:
    value = args[key]
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"probe argument {key} is {value!r}, not a number")
    return float(value)


def _flag(args: Mapping[str, object], key: str) -> bool:
    value = args[key]
    if not isinstance(value, bool):
        raise TypeError(f"probe argument {key} is {value!r}, not true or false")
    return value


def run_probe(point: Mapping[str, object]) -> dict[str, object]:
    """Run the probe `point["probe"]` with `point["args"]` and return what it found.

    A kernel exception, any class, is the record `refused` with the class and the text: the
    controls are known to raise on some platforms (L11), and a walk to a wall must not end in a
    traceback. An unknown probe or a missing argument is a `KeyError` and a wrong type a
    `TypeError`, both raised before the kernel is touched: those are harness bugs, never a
    reading (the parent, `bench.oper.PROBE_ARGS`, has already checked both).
    """
    name = str(point["probe"])
    args = point["args"]
    if not isinstance(args, Mapping):
        raise TypeError(f"probe args must be an object, not {type(args).__name__}")
    job: Callable[[], dict[str, object]]
    if name == "tail":
        job = partial(_probe_tail, _number(args, "d"), _number(args, "pitch"),
                      _number(args, "turns"), _number(args, "tail"), _flag(args, "left_hand"))
    elif name == "naive":
        job = partial(_probe_naive, _number(args, "d"), _number(args, "pitch"),
                      _number(args, "length"))
    elif name == "one_pipe":
        job = partial(_probe_one_pipe, _number(args, "d"), _number(args, "pitch"),
                      _number(args, "turns"), _flag(args, "left_hand"))
    else:
        raise KeyError(name)
    try:
        return job()
    except Exception as exc:  # OCCT raises assorted Standard_Failure subclasses
        return {"status": "refused", "error": type(exc).__name__, "message": str(exc)}


def _main_probe(point: Mapping[str, object], text: str) -> int:
    """One reading of a probe: what it found plus the same peak, RSS and version fields a part
    reading carries. A refused probe carries its reason only."""
    versions = _versions()
    try:
        found = run_probe(point)
    except (KeyError, TypeError) as exc:
        print(f"bad point {text!r}: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    if found["status"] != "ok":
        _emit({**found, **versions})
        return 0
    maxrss = _maxrss_bytes()
    try:
        peak = read_peak()
    except CgroupUnavailable:
        _emit({"status": "no_cgroup", **versions})
        return 0
    _emit({**found, "maxrss_bytes": maxrss, "memory_peak_bytes": peak, "oom_kills": oom_kills(),
           **versions})
    return 0


def main(argv: list[str]) -> int:
    """Take one reading of the point `argv[0]` (JSON: `kind`, `params`, `artifact`; or for a
    probe `kind` "probe", `probe`, `args`) and print one JSON line. Exit 2, with a message on
    stderr and no line, for a point it cannot read: that is a harness bug the parent records as
    `crashed`, never a number."""
    if len(argv) != 1:
        print("usage: python -m bench.oper_child '<point json>'", file=sys.stderr)
        return 2
    try:
        point = json.loads(argv[0])
        kind = point["kind"]
    except (ValueError, KeyError, TypeError) as exc:
        print(f"bad point {argv[0]!r}: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    if kind == "probe":
        return _main_probe(point, argv[0])
    try:
        artifact = _ARTIFACTS[point["artifact"]]
        params = point["params"]
    except (KeyError, TypeError) as exc:
        print(f"bad point {argv[0]!r}: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    # screw is imported here and not at the top so `import bench.oper_child` stays cheap and the
    # tests of the cgroup reader never pay for the kernel.
    from bench import oper_lift
    from screw import solid
    from screw.build_errors import BuildError
    from screw.params import KINDS

    if kind not in KINDS:
        print(f"bad point {argv[0]!r}: unknown kind {kind!r}", file=sys.stderr)
        return 2
    try:
        # `lift` is a past-the-cap point's one lifted guard; every other validator still runs.
        p = oper_lift.validate(kind, params, point.get("lift"))
    except ValueError as exc:  # a pydantic ValidationError is one
        print(f"bad point {argv[0]!r}: {exc}", file=sys.stderr)
        return 2

    fmt, quality = artifact
    versions = _versions()
    solid.clear_cache()
    try:
        started = time.perf_counter()
        solid.build(p)
        build_s = time.perf_counter() - started
        started = time.perf_counter()
        data = solid.export(p, fmt, quality)
        export_s = time.perf_counter() - started
    except BuildError as exc:
        _emit({"status": "refused", "error": type(exc).__name__, "message": str(exc), **versions})
        return 0
    triangles = int.from_bytes(data[80:84], "little") if fmt == "stl" else None
    gzip1_bytes = len(gzip.compress(data, 1))
    # The only peak read comes after the gzip: the cgroup's `memory.peak` is a high-water mark, so
    # this one covers the build, the export and the compression the serving process runs on every
    # response, and the parent's cap check (`bench.oper.classify`) sees memory the gzip used. Read
    # before it, a gzip that took the container past 99 % of the cap without an OOM kill would
    # have stayed `ok` with numbers.
    maxrss = _maxrss_bytes()
    try:
        peak = read_peak()
    except CgroupUnavailable:
        _emit({"status": "no_cgroup", **versions})
        return 0
    _emit({"status": "ok", "build_s": build_s, "export_s": export_s, "bytes": len(data),
           "triangles": triangles, "gzip1_bytes": gzip1_bytes,
           "maxrss_bytes": maxrss, "memory_peak_bytes": peak, "oom_kills": oom_kills(),
           **versions})
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
