"""The half of a reading that runs inside the production container (07 D-15).

`bench.oper` (the parent, kernel-free) starts one fresh container of the image per reading and runs
`python -m bench.oper_child '<point json>'` in it. This module is that process: one cold build,
one export, then the cgroup's own peak, printed as exactly one JSON line. It runs in the image
because that is the artefact whose `mem_limit` the figure sets: Debian's glibc and the container's
cgroup exist nowhere else (07-RESEARCH A1), and `memory.peak` is the cgroup's exact high-water
mark where `ru_maxrss` and `docker stats` are narrower or coarser (D-02).

A reading it cannot stand behind carries a status and no figure (L02): a kernel refusal is
`refused` with its class, an unreadable cgroup is `no_cgroup`. The statuses the parent adds
(`capped`, `killed`, `crashed`) are the ones a dead child cannot report itself.
"""

from __future__ import annotations

import gzip
import json
import resource
import sys
import time
from importlib import metadata
from pathlib import Path
from typing import Literal

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


def main(argv: list[str]) -> int:
    """Take one reading of the point `argv[0]` (JSON: `kind`, `params`, `artifact`) and print one
    JSON line. Exit 2, with a message on stderr and no line, for a point it cannot read: that is
    a harness bug the parent records as `crashed`, never a number."""
    if len(argv) != 1:
        print("usage: python -m bench.oper_child '<point json>'", file=sys.stderr)
        return 2
    try:
        point = json.loads(argv[0])
        kind = point["kind"]
        artifact = _ARTIFACTS[point["artifact"]]
        params = point["params"]
    except (ValueError, KeyError, TypeError) as exc:
        print(f"bad point {argv[0]!r}: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    # screw is imported here and not at the top so `import bench.oper_child` stays cheap and the
    # tests of the cgroup reader never pay for the kernel.
    from pydantic import ValidationError

    from screw import solid
    from screw.build_errors import BuildError
    from screw.params import KINDS

    if kind not in KINDS:
        print(f"bad point {argv[0]!r}: unknown kind {kind!r}", file=sys.stderr)
        return 2
    try:
        p = KINDS[kind].model_validate(params)
    except ValidationError as exc:
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
    # Read straight after the export and before the gzip below: the peak answers "what does the
    # build and export cost", and the production gzip runs in the serving process, not here.
    maxrss = _maxrss_bytes()
    try:
        peak = read_peak()
    except CgroupUnavailable:
        _emit({"status": "no_cgroup", **versions})
        return 0
    triangles = int.from_bytes(data[80:84], "little") if fmt == "stl" else None
    _emit({"status": "ok", "build_s": build_s, "export_s": export_s, "bytes": len(data),
           "triangles": triangles, "gzip1_bytes": len(gzip.compress(data, 1)),
           "maxrss_bytes": maxrss, "memory_peak_bytes": peak, "oom_kills": oom_kills(),
           **versions})
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
