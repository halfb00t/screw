"""The Runs II readings that run inside the production container (07 D-02, D-09; R14, R23).

`bench.oper` (the parent) starts one fresh container per reading and runs
`python -m bench.oper_bound '<point json>'` in it for the point kinds this module owns. Like
`bench.oper_child` it prints exactly one JSON line, and a reading it cannot stand behind carries a
status and no figure (L02).

*Contention* is R14's experiment: the bound point P and one cold partner per other worker, built
together in one `BuildPool` of N workers, so the timeout D-09 derives from P's wall is the wall P
takes while every other worker is busy too, not P alone (Pitfall 2: the old memory driver never had
more than one build in flight). Every point goes through `BuildPool.executor_for`, the server's own
routing (`hash(p) % N`), and never to a worker chosen by index: the set file computed each slot with
that hash (R14), and the reading checks the pool agrees before it builds anything, so a reading
with two builds on one worker, which would leave another idle and measure less than N-way
contention, never yields a number. Every point is submitted once: a resubmitted partner would be a
warm second build beside a cold P, and R14 asks for all N cold.
"""

from __future__ import annotations

import concurrent.futures
import gzip
import json
import os
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import Future, ProcessPoolExecutor
from dataclasses import dataclass
from typing import Literal

from bench.oper import DEADLINE_S
from bench.oper_child import _ARTIFACTS, CgroupUnavailable, _versions, oom_kills, read_peak
from screw.build_errors import BuildError
from screw.calc.cost import ARTIFACTS
from screw.params import KINDS
from screw.pool import BuildPool

type Fmt = Literal["stl", "step"]
type Quality = Literal["preview", "fine"]
type Task = Callable[[str, Mapping[str, object], Fmt, Quality], dict[str, object]]

# The figures one build reports and a contention record carries per build.
_BUILD_FIGURES = ("build_s", "export_s", "bytes", "gzip1_bytes")


def build_task(kind: str, params: Mapping[str, object], fmt: Fmt,
               quality: Quality) -> dict[str, object]:
    """R2's sequence inside a pool worker: a cold build, its export and a level-1 gzip, each
    timed here so a build's figures do not include the wait for its result. The worker is warm
    (`screw.pool._warm` imported the kernel) and new, and the cache is cleared all the same."""
    from screw import solid

    p = KINDS[kind].model_validate(dict(params))
    solid.clear_cache()
    try:
        started = time.perf_counter()
        solid.build(p)
        build_s = time.perf_counter() - started
        started = time.perf_counter()
        data = solid.export(p, fmt, quality)
        export_s = time.perf_counter() - started
    except BuildError as exc:
        return {"status": "refused", "error": type(exc).__name__, "message": str(exc)}
    return {"status": "ok", "build_s": build_s, "export_s": export_s, "bytes": len(data),
            "gzip1_bytes": len(gzip.compress(data, 1))}


def run_member(task: Task, kind: str, params: Mapping[str, object], fmt: Fmt,
               quality: Quality) -> tuple[int, dict[str, object]]:
    """What a contention worker runs: `task` and the worker's pid, so the reading can show each
    build ran in the process its slot was warmed in."""
    return os.getpid(), task(kind, params, fmt, quality)


@dataclass(frozen=True)
class Member:
    """One point of a contention reading: a part and the slot the set file computed for it."""

    label: str
    kind: str
    params: Mapping[str, object]
    slot: int


def _member(raw: object) -> Member:
    fields = raw if isinstance(raw, dict) else {}
    label, kind, params, slot = (fields.get(key) for key in ("label", "kind", "params", "slot"))
    if not (isinstance(label, str) and isinstance(kind, str) and kind in KINDS
            and isinstance(params, dict) and isinstance(slot, int)
            and not isinstance(slot, bool)):
        raise ValueError(f"a contention point is a label, a kind of {sorted(KINDS)}, params and "
                         f"a whole-number slot, not {raw!r}")
    return Member(label=label, kind=kind, params=params, slot=slot)


def _line(status: str, **fields: object) -> dict[str, object]:
    return {"status": status, **fields}


def _terminate(pool: BuildPool, executors: Sequence[ProcessPoolExecutor]) -> None:
    """Stop the builds still running, as the pool's own timeout branch does: shutting an executor
    down does not stop a build already in OCCT, terminating its process does."""
    for executor in executors:
        for process in executor._processes.values():
            process.terminate()
    pool.shutdown()


def contention(points: Sequence[object], workers: int, deadline_s: float, *, artifact: str,
               task: Task = build_task, read_peak: Callable[[], int] = read_peak,
               oom_kills: Callable[[], int | None] = oom_kills) -> dict[str, object]:
    """One contention reading (R14): `points` (P first) built together on a pool of `workers`,
    one per worker, each submitted once and routed by `executor_for`.

    The status, in order: `crashed` if the pool routes a point to another slot than the set
    names (both slots in the message; nothing is built); `killed` if a build is still running at
    `deadline_s` (its process terminated); `no_cgroup` if the peak cannot be read; `crashed` if a
    build raised anything but a kernel refusal; `refused` if a build was refused (class and text
    kept); else `ok`. The peak is the container's, read once after all N builds end. Only `ok`
    carries figures: P's at the top and every build's in `builds`. A set that is not one point per
    slot 0 to N - 1 is a `ValueError` naming R14: no reading is taken of it.
    """
    members = [_member(raw) for raw in points]
    slots = sorted(member.slot for member in members)
    if slots != list(range(workers)):
        raise ValueError(f"R14: a contention reading at N = {workers} holds one point on each "
                         f"slot 0 to {workers - 1}, not points on slots {slots}")
    fmt, quality = _ARTIFACTS[artifact]
    parts = [KINDS[member.kind].model_validate(dict(member.params)) for member in members]
    routed = [hash(p) % workers for p in parts]
    wrong = [f"{member.label}: the set names slot {member.slot}, the pool routes it to slot {slot}"
             for member, slot in zip(members, routed, strict=True) if member.slot != slot]
    if wrong:
        return _line("crashed", error="SlotMismatch", message="; ".join(wrong))
    pool = BuildPool(workers, dict.fromkeys(ARTIFACTS, deadline_s))
    executors = [pool.executor_for(p) for p in parts]
    try:
        # Every worker imports the kernel before any build starts, so the N builds start together
        # and none of them pays the import inside its own wall.
        warm_pids = [executor.submit(os.getpid).result() for executor in executors]
        futures: list[Future[tuple[int, dict[str, object]]]] = [
            executor.submit(run_member, task, member.kind, dict(member.params), fmt, quality)
            for executor, member in zip(executors, members, strict=True)]
        _, pending = concurrent.futures.wait(futures, timeout=deadline_s)
        if pending:
            _terminate(pool, executors)
            return _line("killed", message=f"{len(pending)} of {workers} builds were still "
                                           f"running at {deadline_s:g} s")
    finally:
        pool.shutdown()
    kills = oom_kills()
    try:
        peak = read_peak()
    except CgroupUnavailable as exc:
        return _line("no_cgroup", message=str(exc), oom_kills=kills)
    builds: list[dict[str, object]] = []
    refusal: dict[str, object] | None = None
    for member, slot, warm_pid, future in zip(members, routed, warm_pids, futures, strict=True):
        raised = future.exception()
        if isinstance(raised, BuildError):
            refusal = refusal or _line("refused", error=type(raised).__name__,
                                       message=f"{member.label}: {raised}")
            continue
        if raised is not None:
            return _line("crashed", error=type(raised).__name__,
                         message=f"{member.label}: {raised}", memory_peak_bytes=peak,
                         oom_kills=kills)
        pid, result = future.result()
        if pid != warm_pid:
            return _line("crashed", error="SlotMismatch",
                         message=f"{member.label} ran in pid {pid}, not in the worker of slot "
                                 f"{slot} (pid {warm_pid})", memory_peak_bytes=peak,
                         oom_kills=kills)
        if result.get("status") != "ok":
            refusal = refusal or _line("refused", error=result.get("error"),
                                       message=f"{member.label}: {result.get('message')}")
            continue
        builds.append({"label": member.label, "slot": slot, "status": "ok",
                       **{key: result[key] for key in _BUILD_FIGURES}})
    if refusal is not None:
        return {**refusal, "memory_peak_bytes": peak, "oom_kills": kills}
    bound = builds[0]
    return _line("ok", **{key: bound[key] for key in _BUILD_FIGURES}, memory_peak_bytes=peak,
                 oom_kills=kills, builds=builds)


def _run(point: object) -> dict[str, object]:
    kind = point.get("kind") if isinstance(point, dict) else None
    if isinstance(point, dict) and kind == "contention":
        workers, points, artifact = point["workers"], point["points"], point["artifact"]
        if not (isinstance(workers, int) and isinstance(points, list)
                and isinstance(artifact, str) and artifact in _ARTIFACTS):
            raise ValueError("a contention point has whole-number workers, a list of points and "
                             f"an artifact of {sorted(_ARTIFACTS)}")
        return contention(points, workers, DEADLINE_S, artifact=artifact)
    raise ValueError(f"unknown kind {kind!r}")


def main(argv: list[str]) -> int:
    """Take one reading of the point `argv[0]` and print one JSON line. Exit 2, with a message on
    stderr and no line, for a point it cannot read: a harness bug the parent records as
    `crashed`, never a number."""
    if len(argv) != 1:
        print("usage: python -m bench.oper_bound '<point json>'", file=sys.stderr)
        return 2
    try:
        record = _run(json.loads(argv[0]))
    except (ValueError, KeyError) as exc:  # a pydantic ValidationError is a ValueError
        print(f"bad point {argv[0]!r}: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({**record, **_versions()}, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
