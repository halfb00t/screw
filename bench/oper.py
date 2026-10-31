"""The parent of an operability reading: one fresh container per reading, no number it did not
measure (07 D-01, D-02, D-04, D-15).

A reading is one cold build and one export of one artifact of one part, taken in a new container
of the production image under its own memory cap, with the peak read from the container's cgroup
(`bench.oper_child`, the half that runs inside). This module starts the container, classifies how
it ended, and writes one JSON record per repetition. It is kernel-free and standard-library only,
so the runner executes it with a bare setup-python interpreter: every figure it writes was printed
by a child, and a reading that did not finish cleanly carries a status and no figure (L02).

Not part of `make verify`: it needs Docker and minutes. Run it with `make bench.oper`. Nothing a
laptop prints with it is a bound; D-01 allows only the GitHub runner to set one.
"""

from __future__ import annotations

import argparse
import contextlib
import itertools
import json
import math
import os
import statistics
import subprocess
import sys
import time
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn, TextIO, cast

from bench import host_facts

_REPO_ROOT = Path(__file__).resolve().parents[1]

# A reading's own container cap on the 16 GB runner (07 D-02): 12 GiB leaves 4 GiB for the OS,
# dockerd and this parent. Undersized is visible and not silent: a reading that reaches it is
# `capped` and has no figure. The precedent is bench/memory.py's 8 GiB sweep ceiling, whose first
# sweep read exactly the cap and printed it as a peak.
CAP_BYTES = 12 * 1024**3

# A capped reading does not creep up on its cap, it reads it: 1 % absorbs the cgroup's page
# granularity without being wide enough to call an honest peak capped (bench/memory.py).
CAP_TOLERANCE_FRACTION = 0.01

# The wall for one reading, in seconds. A reading that reaches it is `killed` and recorded; the
# recorded corners that "did not finish in 120 s" on macOS (2026-10-05-interim-runtime-bounds)
# show why an unbounded reading would take the job's time budget with it.
DEADLINE_S = 600

# What a child may report; the parent adds capped, killed and crashed.
_CHILD_STATUSES = frozenset({"ok", "refused", "no_cgroup"})
# What an ok line must carry, with the type of each.
_OK_COUNTS = ("bytes", "memory_peak_bytes")
_OK_SECONDS = ("build_s", "export_s")
# A probe builds something that is not a part (a tail on the kernel's crash wall, a known-bad
# control), so it has no export: its ok line carries what the build found instead (07-03).
PROBE_KIND = "probe"
_PROBE_OK_COUNTS = ("solids", "memory_peak_bytes")
_PROBE_OK_SECONDS = ("build_s",)
# A probe's volume ratio is signed on purpose: one_pipe at 160 to 171 turns builds an inverted
# solid that reads about -1 times the closed form with isValid() True, and that sign is the
# finding (bench/thread_spike/helical.py). Every other number stays finite and non-negative.
_SIGNED = frozenset({"volume_ratio"})
# The probes a point file may name and the arguments each takes; the child's table
# (`bench.oper_child`) is keyed by the same names. `left_hand` is the only yes/no argument.
PROBE_ARGS: dict[str, tuple[str, ...]] = {
    "tail": ("d", "pitch", "turns", "tail", "left_hand"),
    "naive": ("d", "pitch", "length"),
    "one_pipe": ("d", "pitch", "turns", "left_hand"),
    # G37: a bolt's tip cone cut and measured as the build does, its piece reported and not gated.
    "tip_piece": ("d", "pitch", "length", "thread_length", "s", "k", "left_hand"),
}
_PROBE_FLAGS = frozenset({"left_hand"})
_PROBE_POINT_KEYS = frozenset({"label", "kind", "probe", "args"})
# What a line that is not ok may keep: its reason and the versions, never a figure.
_KEPT_WITHOUT_FIGURES = ("status", "error", "message", "cadquery", "cadquery_ocp")
# The figures a summary takes a median and a max of; a probe has no export, so it has two.
_METRICS = ("build_s", "export_s", "bytes", "memory_peak_bytes")
_PROBE_METRICS = ("build_s", "memory_peak_bytes")
_STDERR_TAIL = 2000
# The repetitions R3 asks of a point that sets a bound: 5 distinct ones, `rep` 1 to 5.
BOUND_REPS = (1, 2, 3, 4, 5)

_container_numbers = itertools.count(1)

# The point files a workflow may name, and the artifacts a point may ask for.
POINTS_DIR = _REPO_ROOT / "bench" / "points"
_ARTIFACTS = ("stl-preview", "stl-fine", "step")
_SET_NAME_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-")
_SET_KEYS = frozenset({"set", "rule", "reps", "shards", "deadline_s", "points"})
# What the generator (`bench.oper_sets`) adds: the combinations the parameter model refused and
# why the set holds what it holds. The runner never reads either; it only checks their shape.
# `shard_sizes` and `sources` are written only by the sets generated from runner records (R6, R7,
# R3): the size of each consecutive shard, and the record directories the set was derived from.
# `envelope` is the R12 envelope a Runs II set was drawn under, kind -> artifact -> target -> e,
# as fit.json keys its models: R12 never redraws a set after a widening, so `bench.oper_sets
# --check` regenerates the file under the envelope it names (G6).
# `margin` is R5's m, which the full tier (R28) re-reads a near-timeout point by (07-19).
_SET_OPTIONAL_KEYS = frozenset({"dropped", "notes", "shard_sizes", "sources", "envelope",
                                "margin"})
_ENVELOPE_TARGETS = frozenset({"bytes", "seconds", "peak"})
_POINT_KEYS = frozenset({"label", "kind", "params", "artifact"})
# The Runs II kinds (07-06), read by `bench.oper_bound` in the container: a contention reading of
# N points on N workers (R14), a drift reading of one part built K times and an arena reading of
# one part with the trim on or off (R23). Each kind's own fields are checked by `_load_bound`.
CONTENTION_KIND, DRIFT_KIND, ARENAS_KIND = "contention", "drift", "arenas"
BOUND_KINDS = frozenset({CONTENTION_KIND, DRIFT_KIND, ARENAS_KIND})
_BOUND_KEYS = {CONTENTION_KIND: frozenset({"label", "kind", "artifact", "workers", "points"}),
               DRIFT_KIND: frozenset({"label", "kind", "artifact", "part", "k", "deadline_s"}),
               ARENAS_KIND: frozenset({"label", "kind", "artifact", "part", "trim"})}
_MEMBER_KEYS = frozenset({"label", "kind", "params", "slot"})
_PART_KEYS = frozenset({"kind", "params"})
# R23: a drift compares the peak after build 1 with the peak after build K, so K is at least 2.
MIN_DRIFT_BUILDS = 2
# Whole numbers of bytes a Runs II ok line may add to a part's (arenas, R23).
_BOUND_COUNTS = ("memory_current_bytes", "vm_rss_bytes")
# R14's worker counts: N in {1, 2, 3}.
CONTENTION_WORKERS = (1, 2, 3)
# A bound child also reports a reading it cut itself (a build past the deadline, a build on the
# wrong worker), which a part child never does.
_BOUND_CHILD_STATUSES = _CHILD_STATUSES | {"killed", "crashed"}
# A load reading (07-08, R15): the server in the image under C concurrent clients, run by
# `bench.oper_load` from this parent. It builds no part of its own, so it has no artifact; its
# `artifact` is the kind's name, as a probe's is the probe's. `solid_cache` is R22's K, 4 unless
# a point measures another; `bodies` asks for R20's JSON body lengths after the run.
LOAD_KIND = "load"
_LOAD_KEYS = frozenset({"label", "kind", "workers", "queue", "clients", "mix"})
_LOAD_OPTIONAL_KEYS = frozenset({"solid_cache", "bodies"})
_MIX_KEYS = frozenset({"label", "kind", "params", "artifact"})
LOAD_SOLID_CACHE = (1, 2, 3, 4)
DEFAULT_SOLID_CACHE = 4
# The figure a load reading's summary takes: the container's peak at the end of the run (R16).
_LOAD_METRICS = ("memory_peak_bytes",)
# `preset` is the catalogue row id a point was expanded from; `lift` names the one validator guard
# a past-the-cap point lifts (`bench.oper_lift`), as `{"max_turns": 260}` or `{"max_mm": 1e6}`.
# `gzip_levels` asks the child for R19's per-level bytes and seconds of the export, after its peak.
# A judged point (the full tier, R28 and R29; 07-19) carries what `judge` holds its reading to,
# `timeout_s` and `limit`, as a required-tier point does, and its R6 `charge_s`.
# `expect: refused` marks a pair the shipped cost model refuses, read so that it must still return
# that refusal and never judged against the model (R28, G12).
_POINT_OPTIONAL_KEYS = frozenset({"preset", "lift", "gzip_levels", "charge_s", "timeout_s",
                                  "limit", "expect"})
EXPECTED_REFUSAL = "refused"
# The type of B-02's 422, which the child records as the error of an expected refusal (07-11).
REFUSAL_TYPE = "over_budget"
GZIP_LEVELS = (1, 6, 9)  # R19's; `bench.oper_child.GZIP_LEVELS` is the same three
LIFT_ARGS = ("max_turns", "max_mm")


@dataclass(frozen=True)
class Point:
    """What one reading builds: a part (`kind`, `params`) and one artifact of it.

    A probe (`kind == "probe"`) is not a part: its `artifact` is the probe's name and its
    `params` are the probe's arguments, so a reading, a summary and a shard treat both alike."""

    label: str
    kind: str
    params: Mapping[str, float | bool]
    artifact: str
    lift: Mapping[str, float] | None = None
    # A Runs II point's own fields (`workers` and `points` for contention, `part`, `k` and
    # `deadline_s` for drift, `part` and `trim` for arenas), passed to the child as they stand.
    body: Mapping[str, object] | None = None
    # A drift reading's own deadline (K x the artifact's timeout, R23), in place of the set's.
    deadline_s: float | None = None
    # R19's levels for a part point, computed by the child after its peak read.
    gzip_levels: tuple[int, ...] | None = None
    # A judged point's timeout and its limit per target (R29): `run` fails the job on a miss.
    timeout_s: float | None = None
    limit: Mapping[str, float] | None = None
    # A judged point's R6 charge, which cuts R5's follow-up shards, and `expect: refused` (G12).
    charge_s: float | None = None
    expect: str | None = None

    def as_json(self) -> str:
        if self.body is not None:
            return json.dumps({"kind": self.kind, "artifact": self.artifact, **self.body},
                              sort_keys=True, allow_nan=False)
        if self.kind == PROBE_KIND:
            return json.dumps({"kind": PROBE_KIND, "probe": self.artifact,
                               "args": dict(self.params)}, sort_keys=True, allow_nan=False)
        part: dict[str, object] = {"kind": self.kind, "params": dict(self.params),
                                   "artifact": self.artifact}
        if self.lift:
            part["lift"] = dict(self.lift)
        if self.gzip_levels:
            part["gzip_levels"] = list(self.gzip_levels)
        if self.expect:
            part["expect"] = self.expect
        return json.dumps(part, sort_keys=True, allow_nan=False)


@dataclass(frozen=True)
class PointSet:
    """A point file: the points, how often each is repeated, and how they are split over shards.
    `rule` names the pre-registered protocol rule the set runs under (07-SWEEP-PROTOCOL.md)."""

    name: str
    rule: str
    reps: int
    shards: int
    deadline_s: float
    points: tuple[Point, ...]
    shard_sizes: tuple[int, ...] | None = None
    sources: tuple[str, ...] = ()
    margin: float | None = None  # R5's m, the full tier's (R28)


def is_capped(peak_bytes: int, cap_bytes: int) -> bool:
    """Whether a peak is the container's own cap showing up as if it were a measurement. Pure and
    Docker-free so a test pins both sides of the boundary."""
    return peak_bytes >= int(cap_bytes * (1 - CAP_TOLERANCE_FRACTION))


def _refuse(message: str) -> NoReturn:
    """Every refusal of a child line is a `ValueError`, whatever kind of wrong it was."""
    raise ValueError(message)


def _refuse_constant(name: str) -> float:
    _refuse(f"child line holds the non-finite JSON constant {name}")


def _check_number(key: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return
    if not math.isfinite(value) or (value < 0 and key not in _SIGNED):
        raise ValueError(f"child line: {key} is {value!r}, not a finite non-negative number")


def parse_child_line(line: str, *, probe: bool = False, bound: bool = False) -> dict[str, object]:
    """One child line as a record, or `ValueError`.

    Refuses NaN, infinity and negatives anywhere (but a probe's volume ratio, which is signed), a
    missing key on an ok line, an unknown status and anything that is not one JSON object. A
    line that is not ok is cut down to its reason: a refused child has no business reporting a
    build time (L02, T-07-01). `probe` says what the parent asked for, so a part's ok line is not
    taken for a probe's and the other way round. `bound` is a Runs II child (`bench.oper_bound`),
    which may also report `killed` and `crashed`; the numbers inside its `builds` are held to the
    same rule as the top-level ones.
    """
    try:
        record = json.loads(line, parse_constant=_refuse_constant)
    except json.JSONDecodeError as exc:
        raise ValueError(f"child line is not JSON: {line[:120]!r}") from exc
    if not isinstance(record, dict):
        _refuse(f"child line is not a JSON object: {line[:120]!r}")
    status = record.get("status")
    statuses = _BOUND_CHILD_STATUSES if bound else _CHILD_STATUSES
    # A list or an object is unhashable and cannot be tested for membership: type first.
    if not isinstance(status, str) or status not in statuses:
        raise ValueError(f"child line has status {status!r}, not one of {sorted(statuses)}")
    for key, value in record.items():
        _check_number(str(key), value)
    builds = record.get("builds", [])
    if not (isinstance(builds, list) and all(isinstance(build, dict) for build in builds)):
        _refuse("child line: builds is a list of objects")
    for build in builds:
        for key, value in build.items():
            _check_number(str(key), value)
    levels = record.get("gzip", [])
    if not (isinstance(levels, list) and all(
            isinstance(entry, dict) and set(entry) == {"level", "bytes", "seconds"}
            and all(isinstance(entry[key], int) and not isinstance(entry[key], bool)
                    for key in ("level", "bytes"))
            and _is_number(entry["seconds"]) for entry in levels)):
        _refuse("child line: gzip is a list of {level, bytes, seconds}")
    for entry in levels:
        for key, value in entry.items():
            _check_number(f"gzip {key}", value)
    peaks = record.get("peaks", [])
    if not (isinstance(peaks, list) and all(
            isinstance(peak, int) and not isinstance(peak, bool) and peak >= 0
            for peak in peaks)):
        _refuse("child line: peaks is a list of whole numbers of bytes")
    for key in _BOUND_COUNTS:
        value = record.get(key, 0)
        if isinstance(value, bool) or not isinstance(value, int):
            _refuse(f"child line: {key} is {value!r}, not a whole number")
    if status != "ok":
        return {key: record[key] for key in _KEPT_WITHOUT_FIGURES if key in record}
    counts, seconds = (_PROBE_OK_COUNTS, _PROBE_OK_SECONDS) if probe else (_OK_COUNTS, _OK_SECONDS)
    for key in (*seconds, *counts, *(("valid", "volume_ratio") if probe else ())):
        if key not in record:
            raise ValueError(f"ok child line is missing {key}")
    for key in counts:
        value = record[key]
        if isinstance(value, bool) or not isinstance(value, int):
            _refuse(f"ok child line: {key} is {value!r}, not a whole number")
    for key in (*seconds, *(("volume_ratio",) if probe else ())):
        value = record[key]
        if isinstance(value, bool) or not isinstance(value, int | float):
            _refuse(f"ok child line: {key} is {value!r}, not a number")
    if probe and not isinstance(record["valid"], bool):
        _refuse(f"ok child line: valid is {record['valid']!r}, not true or false")
    return dict(record)


def classify(*, timed_out: bool, oom_killed: bool, exit_code: int, stdout: str, stderr: str,
             cap: int, probe: bool = False, bound: bool = False) -> dict[str, object]:
    """How a reading ended, as `status` plus only what that status may carry.

    In order: past the deadline is `killed`; Docker's `OOMKilled` is `capped`; any non-zero exit
    (a signal included) or a last line that is not a valid child line is `crashed`, with the exit
    code and the stderr tail as evidence; the child's own `refused` and `no_cgroup` stand; an ok
    line whose peak is at the cap, or whose cgroup counted an OOM kill, is `capped`. Only a clean
    ok line keeps its figures. `probe` is whether the point was a probe (see `parse_child_line`).

    A Runs II reading (`bound`) can end badly with the container's peak read (a build refused or
    crashed after the others ran), so its cap test comes before the child's own status: a refused
    build in a container at its cap is `capped` (R2's order), and only then is the child's
    status taken.
    """
    if timed_out:
        return {"status": "killed"}
    if oom_killed:
        return {"status": "capped"}
    crashed: dict[str, object] = {"status": "crashed", "exit_code": exit_code,
                                  "stderr_tail": stderr[-_STDERR_TAIL:]}
    if exit_code != 0:
        return crashed
    lines = [line for line in stdout.splitlines() if line.strip()]
    if not lines:
        return {**crashed, "problem": "the child printed no line"}
    try:
        child = parse_child_line(lines[-1], probe=probe, bound=bound)
    except ValueError as exc:
        return {**crashed, "problem": str(exc)}
    # parse_child_line accepted the line, so it is one JSON object; the full line, because a
    # line that is not ok has had its peak cut from `child`.
    full = json.loads(lines[-1]) if bound else child
    if child["status"] != "ok" and not bound:
        return child
    peak = full.get("memory_peak_bytes")
    kills = full.get("oom_kills")
    if (isinstance(peak, int) and is_capped(peak, cap)) or (isinstance(kills, int) and kills > 0):
        return {"status": "capped",
                **{key: child[key] for key in ("cadquery", "cadquery_ocp") if key in child}}
    return child


def reading_argv(name: str, image: str, repo_root: Path, point_json: str, cap: int,
                 module: str = "bench.oper_child") -> list[str]:
    """The argv for one reading. A list, never a shell string. House shape of
    `bench.thread_spike.runner.container_argv` with three differences: no `--rm`, because the
    parent must `docker inspect` the stopped container for `OOMKilled` before removing it; the
    memory and swap caps both at `cap`, so the cap is a wall and not a suggestion; and no
    `--platform`, so the host's `DOCKER_DEFAULT_PLATFORM` decides (native on the runner). The
    image runs as uid 10001 and has no `bench/`, so the repository's is mounted read-only.
    `module` is the child: `bench.oper_bound` for a Runs II point."""
    return ["docker", "run", "--name", name, f"--memory={cap}b", f"--memory-swap={cap}b",
            "--entrypoint", "python", "-v", f"{repo_root}/bench:/probe/bench:ro",
            "-e", "PYTHONPATH=/probe", image, "-m", module, point_json]


def _docker(*args: str, timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["docker", *args], capture_output=True, text=True, check=False,
                          timeout=timeout)


def _inspect_exit(name: str) -> tuple[bool, int | None]:
    """Docker's `OOMKilled` and `ExitCode` of the stopped container, `(False, None)` when it
    cannot be read (a run that never created the container)."""
    result = _docker("inspect", "--format", "{{.State.OOMKilled}} {{.State.ExitCode}}", name)
    fields = result.stdout.split()
    if result.returncode != 0 or len(fields) != 2 or not fields[1].lstrip("-").isdigit():
        return False, None
    return fields[0] == "true", int(fields[1])


def run_reading(point: Point, rep: int, image: str, cap: int, deadline_s: float,
                versions: Mapping[str, str] | None = None) -> dict[str, object]:
    """One repetition of `point`: a fresh container, classified, with `load1` read just before it
    and `wall_s` from just before `docker run` to just after `docker rm` (kept for every status,
    because it sizes shards). `versions` is the header's, used when the child could not report
    its own."""
    name = f"screw-oper-{os.getpid()}-{next(_container_numbers)}"
    if point.kind == LOAD_KIND and point.body is not None:
        return _run_load_reading(point, point.body, name, rep, image, cap, deadline_s, versions)
    if point.deadline_s is not None:
        deadline_s = point.deadline_s  # a drift reading's own (R23)
    bound = point.kind in BOUND_KINDS
    argv = reading_argv(name, image, _REPO_ROOT, point.as_json(), cap,
                        "bench.oper_bound" if bound else "bench.oper_child")
    load1 = os.getloadavg()[0]
    started = time.perf_counter()
    timed_out = False
    stdout = stderr = ""
    returncode = 1
    try:
        try:
            done = subprocess.run(argv, capture_output=True, text=True, check=False,
                                  timeout=deadline_s)
            stdout, stderr, returncode = done.stdout, done.stderr, done.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            _docker("kill", name)
        oom_killed, container_exit = _inspect_exit(name)
    finally:
        _docker("rm", "-f", name)
    wall_s = time.perf_counter() - started
    result = classify(timed_out=timed_out, oom_killed=oom_killed,
                      exit_code=returncode if container_exit is None else container_exit,
                      stdout=stdout, stderr=stderr, cap=cap, probe=point.kind == PROBE_KIND,
                      bound=bound)
    record: dict[str, object] = {
        "type": "reading", "label": point.label, "kind": point.kind, "params": dict(point.params),
        "artifact": point.artifact, "rep": rep, "load1": load1, "container": name,
        **(point.body or {}), **result, "wall_s": wall_s}
    if point.lift:
        record["lift"] = dict(point.lift)  # a reading past a guard says which guard it lifted
    if point.gzip_levels:
        record["gzip_levels"] = list(point.gzip_levels)
    for key in ("cadquery", "cadquery_ocp"):
        if key not in record and versions is not None:
            record[key] = versions.get(key)
    return record


def _run_load_reading(point: Point, body: Mapping[str, object], name: str, rep: int, image: str,
                      cap: int, deadline_s: float,
                      versions: Mapping[str, str] | None) -> dict[str, object]:
    """One load reading (`bench.oper_load`), recorded as every reading is. The mix is not
    repeated in the record: each request carries its own label, kind, params and artifact."""
    from bench.oper_load import run_load  # it imports this module, so not at the top

    load1 = os.getloadavg()[0]
    started = time.perf_counter()
    result = run_load(body, image, cap, deadline_s, name=name)
    return {"type": "reading", "label": point.label, "kind": point.kind, "params": {},
            "artifact": point.artifact, "rep": rep, "load1": load1, "container": name,
            **{key: value for key, value in body.items() if key != "mix"}, **result,
            "wall_s": time.perf_counter() - started, **dict(versions or {})}


def summarize(readings: Iterable[Mapping[str, object]],
              expected_reps: Iterable[int] = BOUND_REPS) -> list[dict[str, object]]:
    """Per (label, artifact, lift), in first-seen order: how many repetitions, which ones, a count
    per status, the status of the point, and the median (`statistics.median`) and max of each
    metric over the repetitions. A point with any repetition that is not ok has no median and no
    max: four good repetitions and one capped one are not a measurement of the part (D-04, L02).
    The status is `ok`, the one failing status when they agree, or `mixed`.

    The repetitions must also be the ones asked for: each of `expected_reps` (R3's 1 to 5 by
    default) exactly once. Four distinct ones, or five copies of one (a missing job artifact, a
    file downloaded twice), are not five repetitions; the point is `incomplete` and has no median
    and no max, however many of its readings are ok.

    A reading past a validator guard (`lift`) is a confirmation probe of a wall, not a part anyone
    can request: it keeps its own row, names its lift, and has a status and no median or max, so it
    cannot supply a bound or a fit figure (R3, R7, R8)."""
    wanted = sorted(expected_reps)
    grouped: dict[tuple[object, object, str], list[Mapping[str, object]]] = {}
    for reading in readings:
        lift = json.dumps(reading.get("lift"), sort_keys=True)
        grouped.setdefault((reading["label"], reading["artifact"], lift), []).append(reading)
    rows: list[dict[str, object]] = []
    for (label, artifact, lift_text), group in grouped.items():
        counts: dict[str, int] = {}
        for reading in group:
            counts[str(reading["status"])] = counts.get(str(reading["status"]), 0) + 1
        failing = [status for status in counts if status != "ok"]
        status = "ok" if not failing else failing[0] if len(failing) == 1 else "mixed"
        reps = [reading.get("rep") for reading in group]
        if status == "ok" and not _are_reps(reps, wanted):
            status = "incomplete"
        lift = json.loads(lift_text)
        median: dict[str, float] | None = None
        maximum: dict[str, float] | None = None
        if status == "ok" and lift is None:
            metrics = {PROBE_KIND: _PROBE_METRICS, LOAD_KIND: _LOAD_METRICS}.get(
                str(group[0].get("kind")), _METRICS)
            columns = {m: [_number(r, m) for r in group] for m in metrics}
            median = {m: statistics.median(values) for m, values in columns.items()}
            maximum = {m: max(values) for m, values in columns.items()}
        rows.append({"label": label, "artifact": artifact, "lift": lift, "n": len(group),
                     "reps": reps, "status": status, "counts": counts, "median": median,
                     "max": maximum})
    return rows


def _are_reps(seen: list[object], wanted: list[int]) -> bool:
    """Whether `seen` is exactly `wanted`, each once, in any order."""
    return (all(isinstance(rep, int) and not isinstance(rep, bool) for rep in seen)
            and sorted(cast(list[int], seen)) == wanted)


def _number(reading: Mapping[str, object], key: str) -> float:
    value = reading[key]
    if isinstance(value, bool) or not isinstance(value, int | float):
        _refuse(f"an ok reading of {reading.get('label')} has {key} = {value!r}")
    return value


def format_rows(rows: list[dict[str, object]]) -> str:
    """The summary as plain text, one line per point."""
    lines = []
    for row in rows:
        head = f"{row['label']}  {row['artifact']}  n={row['n']}  {row['status']}"
        if row["lift"]:
            head += f"  lift {json.dumps(row['lift'], sort_keys=True)}"
        if row["status"] == "incomplete":
            head += f"  reps seen {row['reps']}"
        median, maximum = row["median"], row["max"]
        if isinstance(median, dict) and isinstance(maximum, dict):
            head += "".join(f"  {m}: median {median[m]:.3f} max {maximum[m]:.3f}" for m in median)
        else:
            head += f"  {row['counts']}"
        lines.append(head)
    return "\n".join(lines)


def parse_params(text: str) -> dict[str, float | bool]:
    """`"d=6 pitch=1.25 left_hand=true"` as a dict: a number, or a bool for `true`/`false`. A
    pair that is neither names itself in the error."""
    params: dict[str, float | bool] = {}
    for token in text.split():
        key, sep, value = token.partition("=")
        if not sep or not key:
            raise ValueError(f"bad --params pair {token!r}: expected name=value")
        if value in ("true", "false"):
            params[key] = value == "true"
            continue
        try:
            number = float(value)
        except ValueError:
            raise ValueError(f"bad --params pair {token!r}: {value!r} is not a number "
                             "or true/false") from None
        if not math.isfinite(number):
            raise ValueError(f"bad --params pair {token!r}: {value!r} is not finite")
        params[key] = number
    return params


def _is_number(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, int | float) and math.isfinite(value)


def _is_count(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value >= 1


def _is_envelope(value: object) -> bool:
    """R12's envelope as a Runs II set records it: kind -> artifact -> {bytes, seconds, peak} ->
    e, every e a finite number at or above 0 (R12's `max(0, ...)`)."""
    return isinstance(value, dict) and bool(value) and all(
        isinstance(kind, str) and kind and isinstance(artifacts, dict) and bool(artifacts)
        and all(artifact in _ARTIFACTS and isinstance(targets, dict)
                and set(targets) == _ENVELOPE_TARGETS
                and all(_is_number(e) and e >= 0 for e in targets.values())
                for artifact, targets in artifacts.items())
        for kind, artifacts in value.items())


def _load_probe(where: str, raw: dict[str, object]) -> Point:
    """A probe point: its name and exactly the arguments that probe takes, each a number above 0
    (`left_hand` a yes/no). `where` names the set, or the command line, in every refusal."""
    label, probe, args = raw.get("label"), raw.get("probe"), raw.get("args")
    if set(raw) != _PROBE_POINT_KEYS:
        _refuse(f"{where}: probe point {label!r} needs exactly the keys "
                f"{sorted(_PROBE_POINT_KEYS)}")
    if not (isinstance(label, str) and label):
        _refuse(f"{where}: a probe point's label is non-empty text")
    if not isinstance(probe, str) or probe not in PROBE_ARGS:
        _refuse(f"{where}: probe point {label!r} names probe {probe!r}, "
                f"not one of {sorted(PROBE_ARGS)}")
    if not isinstance(args, dict):
        _refuse(f"{where}: probe point {label!r} args must be an object")
    wanted = PROBE_ARGS[probe]
    missing = [key for key in wanted if key not in args]
    extra = [key for key in args if key not in wanted]
    if missing or extra:
        _refuse(f"{where}: probe point {label!r} ({probe}) takes {list(wanted)}; "
                f"missing {missing}, unexpected {extra}")
    for key, value in args.items():
        if key in _PROBE_FLAGS:
            if not isinstance(value, bool):
                _refuse(f"{where}: probe point {label!r} argument {key!r} is {value!r}, "
                        "not true or false")
        elif not (_is_number(value) and value > 0):
            _refuse(f"{where}: probe point {label!r} argument {key!r} is {value!r}, "
                    "not a number above 0")
    return Point(label=label, kind=PROBE_KIND, params=dict(args), artifact=probe)


def _load_lift(name: str, raw: dict[str, object]) -> dict[str, float] | None:
    """A part point's `lift`, or `None`: exactly one guard of `LIFT_ARGS` and its new limit, a
    whole number of turns for `max_turns` and a number above 0 for `max_mm`."""
    if "lift" not in raw:
        return None
    lift, label = raw["lift"], raw.get("label")
    if not (isinstance(lift, dict) and len(lift) == 1 and next(iter(lift)) in LIFT_ARGS):
        _refuse(f"set {name!r}: point {label!r} lift names exactly one of {list(LIFT_ARGS)}")
    ((guard, limit),) = lift.items()
    if not (_is_count(limit) if guard == "max_turns" else _is_number(limit) and limit > 0):
        _refuse(f"set {name!r}: point {label!r} lift {guard!r} is {limit!r}, "
                f"not {'a whole number of turns' if guard == 'max_turns' else 'a number above 0'}")
    return {guard: limit}


def _load_member(name: str, label: object, raw: object, workers: int) -> dict[str, object]:
    """One point of a contention reading: a part and the slot 0 to N - 1 the set computed."""
    if not (isinstance(raw, dict) and set(raw) == _MEMBER_KEYS):
        _refuse(f"set {name!r}: contention {label!r} lists points with exactly the keys "
                f"{sorted(_MEMBER_KEYS)}")
    member_label, kind, params, slot = raw["label"], raw["kind"], raw["params"], raw["slot"]
    if not (isinstance(member_label, str) and member_label and isinstance(kind, str) and kind
            and kind != PROBE_KIND and kind not in BOUND_KINDS):
        _refuse(f"set {name!r}: contention {label!r} lists a point whose label and part kind are "
                "non-empty text")
    if not isinstance(params, dict) or not all(
            isinstance(key, str) and (isinstance(value, bool) or _is_number(value))
            for key, value in params.items()):
        _refuse(f"set {name!r}: contention {label!r} point {member_label!r} params are names "
                "with a number or true/false")
    if isinstance(slot, bool) or not isinstance(slot, int) or not 0 <= slot < workers:
        _refuse(f"set {name!r}: contention {label!r} point {member_label!r} slot is {slot!r}, "
                f"not a worker 0 to {workers - 1}")
    return {"label": member_label, "kind": kind, "params": dict(params), "slot": slot}


def _load_part(name: str, label: str, raw: object) -> dict[str, object]:
    """The one part of a drift or arenas point: a part kind and its params."""
    if not (isinstance(raw, dict) and set(raw) == _PART_KEYS):
        _refuse(f"set {name!r}: {label!r} part has exactly the keys {sorted(_PART_KEYS)}")
    kind, params = raw["kind"], raw["params"]
    if not (isinstance(kind, str) and kind and kind != PROBE_KIND and kind not in BOUND_KINDS):
        _refuse(f"set {name!r}: {label!r} part kind is the non-empty text of a part kind")
    if not isinstance(params, dict) or not all(
            isinstance(key, str) and (isinstance(value, bool) or _is_number(value))
            for key, value in params.items()):
        _refuse(f"set {name!r}: {label!r} part params are names with a number or true/false")
    return {"kind": kind, "params": dict(params)}


def _load_bound(name: str, raw: dict[str, object]) -> Point:
    """A Runs II point, held to its kind's keys and types.

    A contention point (R14) lists P first and then one partner per other worker: N in 1 to 3, N
    points on the N distinct slots 0 to N - 1, all built at the point's artifact. A drift point
    (R23) names one part, K builds (at least 2) and its own deadline in seconds; an arenas point
    one part and whether the trim is on."""
    kind, label, artifact = raw["kind"], raw.get("label"), raw.get("artifact")
    if set(raw) != _BOUND_KEYS[str(kind)]:
        _refuse(f"set {name!r}: a {kind} point needs exactly the keys "
                f"{sorted(_BOUND_KEYS[str(kind)])}")
    if not (isinstance(label, str) and label):
        _refuse(f"set {name!r}: a {kind} point's label is non-empty text")
    if artifact not in _ARTIFACTS:
        _refuse(f"set {name!r}: {kind} {label!r} artifact {artifact!r} is not one of "
                f"{list(_ARTIFACTS)}")
    if kind == DRIFT_KIND:
        k, deadline = raw["k"], raw["deadline_s"]
        if not (_is_count(k) and isinstance(k, int) and k >= MIN_DRIFT_BUILDS):
            _refuse(f"set {name!r}: drift {label!r} k is {k!r}, not a whole number of builds of "
                    f"at least {MIN_DRIFT_BUILDS}")
        if not (_is_number(deadline) and isinstance(deadline, int | float) and deadline > 0):
            _refuse(f"set {name!r}: drift {label!r} deadline_s is {deadline!r}, not seconds "
                    "above 0")
        return Point(label=label, kind=DRIFT_KIND, params={}, artifact=str(artifact),
                     body={"part": _load_part(name, label, raw["part"]), "k": k,
                           "deadline_s": deadline}, deadline_s=float(deadline))
    if kind == ARENAS_KIND:
        trim = raw["trim"]
        if not isinstance(trim, bool):
            _refuse(f"set {name!r}: arenas {label!r} trim is {trim!r}, not true or false")
        return Point(label=label, kind=ARENAS_KIND, params={}, artifact=str(artifact),
                     body={"part": _load_part(name, label, raw["part"]), "trim": trim})
    workers, points = raw["workers"], raw["points"]
    if not isinstance(workers, int) or isinstance(workers, bool) or (
            workers not in CONTENTION_WORKERS):
        _refuse(f"set {name!r}: contention {label!r} workers is {workers!r}, not one of "
                f"{list(CONTENTION_WORKERS)} (R14)")
    if not (isinstance(points, list) and len(points) == workers):
        _refuse(f"set {name!r}: contention {label!r} lists {workers} points, P and one partner "
                "per other worker (R14)")
    members = [_load_member(name, label, member, int(workers)) for member in points]
    if len({member["slot"] for member in members}) != len(members):
        _refuse(f"set {name!r}: contention {label!r} puts two points on one slot (R14)")
    if len({member["label"] for member in members}) != len(members):
        _refuse(f"set {name!r}: contention {label!r} lists one label twice")
    return Point(label=label, kind=str(kind), params={}, artifact=str(artifact),
                 body={"workers": workers, "points": members})


def _whole(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _load_load(name: str, raw: dict[str, object]) -> Point:
    """A load point (R15): N workers in 1 to 3, a queue of at least N, at least one client,
    `solid_cache` K in 1 to 4 (4 if absent, R22), `bodies` yes or no (no if absent), and a
    non-empty mix of parts, each a label, a part kind, its params and an artifact. Every number
    becomes one `-e` element of the container's argv, so each is checked here (T-07-61)."""
    label = raw.get("label")
    if not _LOAD_KEYS <= set(raw) <= _LOAD_KEYS | _LOAD_OPTIONAL_KEYS:
        _refuse(f"set {name!r}: a load point needs the keys {sorted(_LOAD_KEYS)} and may add "
                f"{sorted(_LOAD_OPTIONAL_KEYS)}")
    if not (isinstance(label, str) and label):
        _refuse(f"set {name!r}: a load point's label is non-empty text")
    workers, depth, clients = (_whole(raw[key]) for key in ("workers", "queue", "clients"))
    cache = _whole(raw.get("solid_cache", DEFAULT_SOLID_CACHE))
    bodies = raw.get("bodies", False)
    if workers not in CONTENTION_WORKERS:
        _refuse(f"set {name!r}: load {label!r} workers is {raw['workers']!r}, not one of "
                f"{list(CONTENTION_WORKERS)}")
    if depth is None or depth < workers:
        _refuse(f"set {name!r}: load {label!r} queue is {raw['queue']!r}, not a whole number of "
                "at least its workers")
    if clients is None or clients < 1:
        _refuse(f"set {name!r}: load {label!r} clients is {raw['clients']!r}, not a whole number "
                "of at least 1")
    if cache not in LOAD_SOLID_CACHE:
        _refuse(f"set {name!r}: load {label!r} solid_cache is {raw.get('solid_cache')!r}, not "
                f"one of {list(LOAD_SOLID_CACHE)} (R22)")
    if not isinstance(bodies, bool):
        _refuse(f"set {name!r}: load {label!r} bodies is {bodies!r}, not true or false")
    mix = raw["mix"]
    if not (isinstance(mix, list) and mix):
        _refuse(f"set {name!r}: load {label!r} mix is a non-empty list")
    entries: list[dict[str, object]] = []
    for entry in mix:
        if not (isinstance(entry, dict) and set(entry) == _MIX_KEYS):
            _refuse(f"set {name!r}: load {label!r} mix entries have exactly the keys "
                    f"{sorted(_MIX_KEYS)}")
        part = _load_part(name, str(label), {"kind": entry["kind"], "params": entry["params"]})
        if not (isinstance(entry["label"], str) and entry["label"]):
            _refuse(f"set {name!r}: load {label!r} mix entry labels are non-empty text")
        if part["kind"] == LOAD_KIND:
            _refuse(f"set {name!r}: load {label!r} mix entry kind is a part kind")
        if entry["artifact"] not in _ARTIFACTS:
            _refuse(f"set {name!r}: load {label!r} mix entry artifact {entry['artifact']!r} is "
                    f"not one of {list(_ARTIFACTS)}")
        entries.append({"label": entry["label"], **part, "artifact": entry["artifact"]})
    return Point(label=label, kind=LOAD_KIND, params={}, artifact=LOAD_KIND, body={
        "workers": workers, "queue": depth, "clients": clients, "solid_cache": cache,
        "bodies": bodies, "mix": entries})


def _load_point(name: str, raw: object) -> Point:
    if isinstance(raw, dict) and raw.get("kind") == PROBE_KIND:
        return _load_probe(f"set {name!r}", raw)
    if isinstance(raw, dict) and raw.get("kind") == LOAD_KIND:
        return _load_load(name, raw)
    if isinstance(raw, dict) and raw.get("kind") in BOUND_KINDS:
        return _load_bound(name, raw)
    allowed = _POINT_KEYS | _POINT_OPTIONAL_KEYS
    if not isinstance(raw, dict) or not _POINT_KEYS <= set(raw) <= allowed:
        _refuse(f"set {name!r}: a point needs the keys {sorted(_POINT_KEYS)} "
                f"and may add {sorted(_POINT_OPTIONAL_KEYS)}")
    if "preset" in raw and not isinstance(raw["preset"], str):
        _refuse(f"set {name!r}: a point's preset is the text of a catalogue row id")
    lift = _load_lift(name, raw)
    levels = raw.get("gzip_levels")
    if levels is not None and not (
            isinstance(levels, list) and levels and len(set(levels)) == len(levels)
            and all(_whole(level) in GZIP_LEVELS for level in levels)):
        _refuse(f"set {name!r}: point {raw.get('label')!r} gzip_levels is {levels!r}, not "
                f"distinct levels of {list(GZIP_LEVELS)} (R19)")
    label, kind, params, artifact = raw["label"], raw["kind"], raw["params"], raw["artifact"]
    if not (isinstance(label, str) and label and isinstance(kind, str) and kind):
        _refuse(f"set {name!r}: a point's label and kind are non-empty text")
    timeout, limit, charge = _load_judged(name, raw)
    expect = raw.get("expect")
    if expect is not None and (expect != EXPECTED_REFUSAL or limit is not None):
        _refuse(f"set {name!r}: point {label!r} expect is {expect!r}; only `refused` is expected, "
                "and an expected refusal carries no limit (G12)")
    if artifact not in _ARTIFACTS:
        _refuse(f"set {name!r}: artifact {artifact!r} is not one of {list(_ARTIFACTS)}")
    if not isinstance(params, dict) or not all(
            isinstance(key, str) and (isinstance(value, bool) or _is_number(value))
            for key, value in params.items()):
        _refuse(f"set {name!r}: point {label!r} params are names with a number or true/false")
    return Point(label=label, kind=kind, params=dict(params), artifact=str(artifact), lift=lift,
                 gzip_levels=None if levels is None else tuple(levels), timeout_s=timeout,
                 limit=limit, charge_s=charge, expect=None if expect is None else str(expect))


def _load_judged(name: str, raw: Mapping[str, object]) -> tuple[
        float | None, dict[str, float] | None, float | None]:
    """A judged point's `timeout_s` and `limit`, both or neither (a limit with no timeout would be
    half a judgement), with the required tier's types, and its `charge_s` seconds if any."""
    label = raw.get("label")
    charge = raw.get("charge_s", 0.0)
    if not (_is_number(charge) and isinstance(charge, int | float) and charge >= 0):
        _refuse(f"set {name!r}: point {label!r} charge_s is {charge!r}, not seconds")
    charge_s = float(charge) if "charge_s" in raw else None
    if ("timeout_s" in raw) != ("limit" in raw):
        _refuse(f"set {name!r}: point {label!r} carries timeout_s and limit together or neither")
    if "timeout_s" not in raw:
        return None, None, charge_s
    timeout, limit = raw["timeout_s"], raw["limit"]
    if not (_is_number(timeout) and isinstance(timeout, int | float) and timeout > 0):
        _refuse(f"set {name!r}: point {label!r} timeout_s is {timeout!r}, not seconds above 0")
    if not (isinstance(limit, dict) and set(limit) == set(_TIER_TARGETS)
            and all(_is_number(value) and value > 0 for value in limit.values())):
        _refuse(f"set {name!r}: point {label!r} limit is {limit!r}, not a number above 0 for "
                f"each of {list(_TIER_TARGETS)}")
    return float(timeout), {str(key): float(value) for key, value in limit.items()}, charge_s


def load_set(name: str, directory: Path | None = None) -> PointSet:
    """The point file `bench/points/<name>.json`, or `ValueError` naming the set.

    The name is the workflow's `set` input, so it is held to `[a-z0-9-]+` and to a file that
    exists before it touches a path (T-07-02). The file must carry exactly the schema's keys with
    the schema's types: a point file with a typo should stop the run, not measure something
    else."""
    if not name or not set(name) <= _SET_NAME_CHARS:
        _refuse(f"set {name!r}: a set name is lower-case letters, digits and hyphens")
    path = (directory if directory is not None else POINTS_DIR) / f"{name}.json"
    try:
        raw = json.loads(path.read_text())
    except OSError:
        _refuse(f"set {name!r}: no point file at {path}")
    except json.JSONDecodeError as exc:
        _refuse(f"set {name!r}: {path} is not JSON ({exc})")
    if not isinstance(raw, dict) or not _SET_KEYS <= set(raw) <= _SET_KEYS | _SET_OPTIONAL_KEYS:
        _refuse(f"set {name!r}: a point file needs the keys {sorted(_SET_KEYS)} "
                f"and may add {sorted(_SET_OPTIONAL_KEYS)}")
    if not isinstance(raw.get("dropped", []), list) or not (
            isinstance(raw.get("notes", []), list)
            and all(isinstance(note, str) for note in raw.get("notes", []))):
        _refuse(f"set {name!r}: dropped is a list and notes is a list of text")
    if raw["set"] != name or not isinstance(raw["rule"], str):
        _refuse(f"set {name!r}: `set` must repeat the file's name and `rule` must be text")
    if not (_is_count(raw["reps"]) and _is_count(raw["shards"])):
        _refuse(f"set {name!r}: reps and shards are whole numbers of at least 1")
    if not (_is_number(raw["deadline_s"]) and raw["deadline_s"] > 0):
        _refuse(f"set {name!r}: deadline_s is a number of seconds above 0")
    if not isinstance(raw["points"], list) or not raw["points"]:
        _refuse(f"set {name!r}: points is a non-empty list")
    points = tuple(_load_point(name, entry) for entry in raw["points"])
    if len({(p.label, p.artifact) for p in points}) != len(points):
        _refuse(f"set {name!r}: a label may be listed once per artifact, not twice for one")
    sizes = raw.get("shard_sizes")
    if sizes is not None and not (
            isinstance(sizes, list) and len(sizes) == raw["shards"]
            and all(_is_count(size) for size in sizes) and sum(sizes) == len(points)):
        _refuse(f"set {name!r}: shard_sizes is {raw['shards']} whole numbers of at least 1 "
                f"that sum to the {len(points)} points")
    sources = raw.get("sources", [])
    if not (isinstance(sources, list) and all(isinstance(source, str) for source in sources)):
        _refuse(f"set {name!r}: sources is a list of text")
    if "margin" in raw and not (_is_number(raw["margin"]) and raw["margin"] >= 0):
        _refuse(f"set {name!r}: margin is R5's m, a number of at least 0")
    if "envelope" in raw and not _is_envelope(raw["envelope"]):
        _refuse(f"set {name!r}: envelope is kind -> artifact -> bytes, seconds and peak -> an e "
                "of at least 0 (R12)")
    return PointSet(name=name, rule=raw["rule"], reps=raw["reps"], shards=raw["shards"],
                    deadline_s=float(raw["deadline_s"]), points=points,
                    shard_sizes=None if sizes is None else tuple(sizes), sources=tuple(sources),
                    margin=None if "margin" not in raw else float(raw["margin"]))


def shard_points(spec: PointSet, shard: int) -> list[Point]:
    """The points of 1-based `shard`. With `shard_sizes` (R6, the sets generated from runner
    records) the shard is the consecutive slice of that size; without it point `i` of the file
    (0-based) goes to shard `i % shards + 1`, the split R4 fixed for the four first sets, so
    two runs of one file split it the same way and those files did not change."""
    if spec.shard_sizes is None:
        return [p for i, p in enumerate(spec.points) if i % spec.shards + 1 == shard]
    if not 1 <= shard <= len(spec.shard_sizes):
        return []
    start = sum(spec.shard_sizes[:shard - 1])
    return list(spec.points[start:start + spec.shard_sizes[shard - 1]])


def _image_versions(image: str) -> dict[str, str]:
    """The kernel pair installed in `image`, read by a container of it."""
    code = ("import json, importlib.metadata as m; "
            "print(json.dumps({'cadquery': m.version('cadquery'), "
            "'cadquery_ocp': m.version('cadquery-ocp')}))")
    done = subprocess.run(["docker", "run", "--rm", "--entrypoint", "python", image, "-c", code],
                          capture_output=True, text=True, check=True)
    versions = json.loads(done.stdout)
    return {str(key): str(value) for key, value in versions.items()}


def _image_id(image: str) -> str:
    done = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}", image],
                          capture_output=True, text=True, check=True)
    return done.stdout.strip()


def header(image: str, versions: Mapping[str, str]) -> dict[str, object]:
    """The first line of every JSONL file: the D-01 host facts, the image and its kernel pair."""
    return {"type": "header", "image": image, "image_id": _image_id(image),
            "versions": dict(versions), **host_facts()}


def _emit(sink: TextIO, record: Mapping[str, object]) -> None:
    sink.write(json.dumps(record, allow_nan=False) + "\n")
    sink.flush()  # a killed run keeps every reading it finished


def _open_sink(out: str) -> TextIO:
    return sys.stdout if out == "-" else Path(out).open("w")


def _write_run(image: str, out: str, plan: list[tuple[Point, int]], deadline_s: float,
               readings: list[dict[str, object]] | None = None,
               tag: Mapping[str, object] | None = None) -> int:
    """The header, then one reading per `(point, rep)` of `plan`, in plan order, each with the
    keys of `tag` added and each also appended to `readings` when it is given."""
    try:
        versions = _image_versions(image)
        head = header(image, versions)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"oper: cannot read image {image}: {exc}", file=sys.stderr)
        return 2
    sink = _open_sink(out)
    try:
        _emit(sink, head)
        for point, rep in plan:
            reading = {**run_reading(point, rep, image, CAP_BYTES, deadline_s, versions),
                       **(tag or {})}
            _emit(sink, reading)
            if readings is not None:
                readings.append(reading)
    finally:
        if sink is not sys.stdout:
            sink.close()
    return 0


def _point_of(args: argparse.Namespace) -> Point:
    """The point the `point` command names, or `ValueError`: a part takes `--artifact`, a probe
    (`--kind probe`) takes `--probe` with `--params` as its arguments, and neither takes the
    other's flag."""
    params = parse_params(args.params)
    if args.kind != PROBE_KIND:
        if args.artifact is None or args.probe is not None:
            _refuse(f"a {args.kind} point takes --artifact and no --probe")
        return Point(label=args.label, kind=args.kind, params=params, artifact=args.artifact)
    if args.artifact is not None or args.probe is None:
        _refuse("a probe point takes --probe and no --artifact")
    return _load_probe("point", {"label": args.label, "kind": PROBE_KIND, "probe": args.probe,
                                 "args": params})


def _cmd_point(args: argparse.Namespace) -> int:
    try:
        point = _point_of(args)
    except ValueError as exc:
        print(f"oper: {exc}", file=sys.stderr)
        return 2
    return _write_run(args.image, args.out, [(point, rep) for rep in range(1, args.reps + 1)],
                      DEADLINE_S)


def _cmd_matrix(args: argparse.Namespace) -> int:
    try:
        spec = load_set(args.set)
    except ValueError as exc:
        print(f"oper: {exc}", file=sys.stderr)
        return 2
    include = [{"shard": shard, "rep": rep}
               for shard in range(1, spec.shards + 1) for rep in range(1, spec.reps + 1)]
    print("matrix=" + json.dumps({"include": include}, separators=(",", ":")))
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    try:
        spec = load_set(args.set)
        if args.followup_from is None:
            shards, reps = spec.shards, spec.reps
            points = shard_points(spec, args.shard) if 1 <= args.shard <= shards else []
        else:  # R5: this shard of the follow-up selection, at one of 5 repetitions
            cut = followup_shards(followup_points(spec, read_records_under(args.followup_from)))
            shards, reps = len(cut), len(BOUND_REPS)
            points = cut[args.shard - 1] if 1 <= args.shard <= shards else []
        if not 1 <= args.shard <= shards:
            _refuse(f"set {spec.name!r}: shard {args.shard} is outside 1..{shards}")
        if not 1 <= args.rep <= reps:
            _refuse(f"set {spec.name!r}: rep {args.rep} is outside 1..{reps}")
    except (OSError, ValueError) as exc:
        print(f"oper: {exc}", file=sys.stderr)
        return 2
    plan = [(point, args.rep) for point in points]
    readings: list[dict[str, object]] = []
    code = _write_run(args.image, args.out, plan, spec.deadline_s, readings,
                      None if args.followup_from is None else {"followup": True})
    if code != 0:
        return code
    # R29: a judged point's miss fails the job, after every record is written, so a red run
    # keeps all its readings (07-19). A point with no limit is a recording and judged by nothing.
    failures = [failure for (point, _), reading in zip(plan, readings, strict=True)
                for failure in judged_failures(point, reading)]
    for failure in failures:
        print(f"oper: {failure}", file=sys.stderr)
    return 1 if failures else 0


def judged_failures(point: Point, reading: Mapping[str, object]) -> list[str]:
    """R29's failures of one reading of a judged point; none for a point that carries no limit.
    An expected refusal (G12) passes only on the refusal it expects and is judged by nothing
    else: it has no cost to judge."""
    if point.expect == EXPECTED_REFUSAL:
        if reading.get("status") == "refused" and reading.get("error") == REFUSAL_TYPE:
            return []
        return [f"{point.label} at {point.artifact}: expected its {REFUSAL_TYPE} refusal, got "
                f"{reading.get('status')} {reading.get('error', '')}".rstrip()]
    if point.timeout_s is None or point.limit is None:
        return []
    return judge(BoundaryPoint(point, point.timeout_s, point.limit), reading)


# --- R5's follow-up of the full tier (R3, R5, R28; 07-19) ---------------------------------------
#
# A full-tier point is read once. One whose cold wall x (1 + m) reaches its timeout is read again
# at repetitions 1 to 5 as 5 matrix jobs of the same workflow run, so on 5 runner instances (R3),
# and the `verdict` job judges every reading of the run. The selection is a filter over the
# committed set and the run's own records, so no point file is written outside bench.oper_sets
# (R30).

# `timeout-minutes` of the `followup` job, as `measure`'s; a test pins both to the workflow.
FOLLOWUP_TIMEOUT_MIN = 350
FOLLOWUP_HALF_S = FOLLOWUP_TIMEOUT_MIN * 60 / 2  # R6: the other half is setup, build and upload


def read_records_under(directory: str) -> list[dict[str, object]]:
    """Every reading of the JSONL files under `directory`, as `gh run download` or
    `actions/download-artifact` lay them out (one folder per artifact), in sorted path order."""
    paths = sorted(str(path) for path in Path(directory).rglob("*.jsonl"))
    return _read_records(paths)[1]


def _cold_wall(reading: Mapping[str, object]) -> float:
    return _number(reading, "build_s") + _number(reading, "export_s")


def followup_points(spec: PointSet, readings: Iterable[Mapping[str, object]]) -> list[Point]:
    """R5: in file order, the judged points whose single measure reading is ok with a cold wall x
    (1 + m) at or above the point's timeout. A point that was not ok has failed already."""
    if spec.margin is None:
        _refuse(f"set {spec.name!r} records no margin, so R5 selects nothing it could stand by")
    ok = {(reading.get("label"), reading.get("artifact")): reading for reading in readings
          if reading.get("status") == "ok" and not reading.get("followup")}
    out: list[Point] = []
    for point in spec.points:
        reading = ok.get((point.label, point.artifact))
        if point.timeout_s is None or reading is None:
            continue
        if _cold_wall(reading) * (1 + spec.margin) >= point.timeout_s:
            out.append(point)
    return out


def followup_shards(points: list[Point]) -> list[list[Point]]:
    """R6 over the follow-up selection: consecutive shards, each the longest run of points whose
    summed charge stays under half the follow-up job's timeout; a point not under it alone is a
    stop, as R6 rules for every set."""
    shards: list[list[Point]] = []
    running = 0.0
    for point in points:
        charge = DEADLINE_S if point.charge_s is None else point.charge_s
        if charge >= FOLLOWUP_HALF_S:
            _refuse(f"{point.label} is charged {charge:g} s, not under half the follow-up job's "
                    f"timeout ({FOLLOWUP_HALF_S:g} s)")
        if shards and running + charge < FOLLOWUP_HALF_S:
            shards[-1].append(point)
            running += charge
        else:
            shards.append([point])
            running = charge
    return shards


def verdict(spec: PointSet, readings: Sequence[Mapping[str, object]]) -> list[str]:
    """R29 over every reading of a full-tier run: each point has exactly one measure reading and
    it passes, and each follow-up point (R5) has repetitions 1 to 5, each once, all ok and each
    within its timeout and limits. Every failure names its point."""
    measure = [reading for reading in readings if not reading.get("followup")]
    follow = [reading for reading in readings if reading.get("followup")]
    failures: list[str] = []
    for point in spec.points:
        found = [r for r in measure
                 if (r.get("label"), r.get("artifact")) == (point.label, point.artifact)]
        if len(found) != 1:
            failures.append(f"{point.label} at {point.artifact}: {len(found)} measure readings, "
                            "not 1")
            continue
        failures += judged_failures(point, found[0])
    for point in followup_points(spec, measure):
        mine = [r for r in follow
                if (r.get("label"), r.get("artifact")) == (point.label, point.artifact)]
        for reading in mine:
            failures += judged_failures(point, reading)
        status = summarize(mine, BOUND_REPS)[0]["status"] if mine else "unread"
        if status != "ok":
            failures.append(f"{point.label} at {point.artifact}: follow-up {status}, not ok at "
                            "repetitions 1 to 5 (R3, R5)")
    return failures


def _cmd_followup_matrix(args: argparse.Namespace) -> int:
    try:
        spec = load_set(args.set)
        cut = followup_shards(followup_points(spec, read_records_under(args.source)))
    except (OSError, ValueError) as exc:
        print(f"oper: {exc}", file=sys.stderr)
        return 2
    include = [{"shard": shard, "rep": rep}
               for shard in range(1, len(cut) + 1) for rep in BOUND_REPS]
    print("matrix=" + json.dumps({"include": include}, separators=(",", ":")))
    print(f"count={len(include)}")
    return 0


def _cmd_verdict(args: argparse.Namespace) -> int:
    try:
        spec = load_set(args.set)
        failures = verdict(spec, read_records_under(args.source))
    except (OSError, ValueError) as exc:
        print(f"oper: {exc}", file=sys.stderr)
        return 2
    for failure in failures:
        print(f"oper: {failure}", file=sys.stderr)
    print(f"{spec.name}: {len(spec.points)} points, {len(failures)} failures")
    return 1 if failures else 0


def _read_records(paths: list[str]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """The header and reading records of JSONL files, in file order."""
    headers: list[dict[str, object]] = []
    readings: list[dict[str, object]] = []
    for path in paths:
        for line in Path(path).read_text().splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if isinstance(record, dict) and record.get("type") == "header":
                headers.append(record)
            elif isinstance(record, dict) and record.get("type") == "reading":
                readings.append(record)
    return headers, readings


def _fact_text(value: object) -> str:
    if value is None:
        return "unknown"
    return json.dumps(value, sort_keys=True) if isinstance(value, dict | list) else str(value)


def markdown_report(headers: list[dict[str, object]], readings: list[dict[str, object]],
                    rows: list[dict[str, object]]) -> str:
    """A per-run summary for `$GITHUB_STEP_SUMMARY`: the distinct host facts of the headers
    (GitHub mixes CPU generations, so two shards may differ), the status counts, then a row per
    point. A figure is printed only for a point whose every repetition is ok."""
    facts: dict[str, list[str]] = {}
    for head in headers:
        for key, value in head.items():
            if key != "type" and _fact_text(value) not in facts.setdefault(key, []):
                facts[key].append(_fact_text(value))
    totals: dict[str, int] = {}
    for reading in readings:
        totals[str(reading["status"])] = totals.get(str(reading["status"]), 0) + 1
    lines = ["### Host", "", "| fact | value |", "| --- | --- |"]
    lines += [f"| {key} | {', '.join(values)} |" for key, values in facts.items()]
    lines += ["", "### Readings", "",
              "Status counts: " + ", ".join(f"{status}: {n}" for status, n in totals.items()), "",
              "| point | artifact | n | status | counts | median build s | max build s "
              "| median export s | max export s | median bytes | max bytes "
              "| median peak bytes | max peak bytes |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in rows:
        median, maximum = row["median"], row["max"]
        cells = ["-"] * 8
        if isinstance(median, dict) and isinstance(maximum, dict):
            # A probe has no export seconds and no bytes: a dash, never a zero (L02).
            cells = [f"{table[m]:{spec}}" if m in table else "-" for m, spec in (
                ("build_s", ".3f"), ("export_s", ".3f"), ("bytes", ".0f"),
                ("memory_peak_bytes", ".0f")) for table in (median, maximum)]
        tally = row["counts"]
        counts = ", ".join(f"{status}: {n}" for status, n in tally.items()) if isinstance(
            tally, dict) else ""
        if row["status"] == "incomplete":
            counts += f"; reps seen {row['reps']}"
        label = f"{row['label']} (lift {json.dumps(row['lift'], sort_keys=True)})" if row[
            "lift"] else row["label"]
        lines.append(f"| {label} | {row['artifact']} | {row['n']} | {row['status']} "
                     f"| {counts} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


# --- the required tier (R27, R29; 07-18) ---------------------------------------------------------
#
# `check` reads the boundary set `bench.oper_sets boundary` writes (tests/data/oper_boundary.json)
# once each, cold, through `run_reading`, and fails on what R29 fails a tier on: a reading that is
# not ok, a cold wall past its artifact's timeout, or an actual past prediction x (1 + e) for any
# target. The limits come with the file, so this module stays standard-library only (the `bounds`
# job runs it on the runner's bare Python).

_BOUNDARY_KEYS = frozenset({"label", "kind", "params", "artifact", "timeout_s", "limit"})
_BOUNDARY_OPTIONAL_KEYS = frozenset({"charge_s", "estimate_s"})
_TIER_TARGETS = ("bytes", "seconds", "peak")


@dataclass(frozen=True)
class BoundaryPoint:
    """A point of the required tier and what R29 holds its reading to: the artifact's timeout and
    the enveloped prediction of each target (bytes, seconds, peak)."""

    point: Point
    timeout_s: float
    limit: Mapping[str, float]


def load_boundary(path: Path, shard: int | None = None) -> list[BoundaryPoint]:
    """The points of a boundary file, or of its 1-based `shard` (G34: the consecutive slice its
    `shard_sizes` gives, so every point is in exactly one shard), or `ValueError` naming what is
    wrong. A blank file holds no point; the caller decides that no reading is not a pass."""
    text = path.read_text()
    if not text.strip():
        if shard is not None:
            _refuse(f"{path}: a blank file has no shard {shard}")
        return []
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        _refuse(f"{path} is not JSON ({exc})")
    entries = raw.get("points") if isinstance(raw, dict) else None
    if not isinstance(entries, list):
        _refuse(f"{path}: a boundary file is an object with a list of points")
    out: list[BoundaryPoint] = []
    for entry in entries:
        if not (isinstance(entry, dict)
                and _BOUNDARY_KEYS <= set(entry) <= _BOUNDARY_KEYS | _BOUNDARY_OPTIONAL_KEYS):
            _refuse(f"{path}: a boundary point needs the keys {sorted(_BOUNDARY_KEYS)}")
        point = _load_point(str(path), {key: entry[key] for key in _POINT_KEYS})
        if point.kind == PROBE_KIND:
            _refuse(f"{path}: boundary point {point.label!r} is a probe, not a part")
        timeout, limit = entry["timeout_s"], entry["limit"]
        if not (_is_number(timeout) and timeout > 0):
            _refuse(f"{path}: boundary point {point.label!r} timeout_s is {timeout!r}, not "
                    "seconds above 0")
        if not (isinstance(limit, dict) and set(limit) == set(_TIER_TARGETS)
                and all(_is_number(value) and value > 0 for value in limit.values())):
            _refuse(f"{path}: boundary point {point.label!r} limit is {limit!r}, not a number "
                    f"above 0 for each of {list(_TIER_TARGETS)}")
        out.append(BoundaryPoint(point, float(timeout),
                                 {key: float(value) for key, value in limit.items()}))
    if shard is None:
        return out
    sizes = raw.get("shard_sizes")
    if not (isinstance(sizes, list) and all(_is_count(size) for size in sizes)
            and sum(sizes) == len(out)):
        _refuse(f"{path}: shard_sizes are whole numbers of at least 1 that sum to the "
                f"{len(out)} points")
    if not 1 <= shard <= len(sizes):
        _refuse(f"{path}: shard {shard} is outside 1..{len(sizes)}")
    start = sum(sizes[:shard - 1])
    return out[start:start + sizes[shard - 1]]


def judge(point: BoundaryPoint, reading: Mapping[str, object]) -> list[str]:
    """What R29 fails the tier on in one reading of `point`, each naming the point; empty when the
    reading is ok and within its timeout and every limit. A figure exactly at its limit passes:
    the limit is the enveloped prediction R12 admits at, and R29 fails only above it."""
    where = f"{point.point.label} at {point.point.artifact}"
    status = reading.get("status")
    if status != "ok":
        return [f"{where}: {status}, not ok"]
    wall = _number(reading, "build_s") + _number(reading, "export_s")
    failures = []
    if wall > point.timeout_s:
        failures.append(f"{where}: cold wall {wall!r} s over its timeout {point.timeout_s!r} s")
    for target, actual in (("bytes", _number(reading, "bytes")), ("seconds", wall),
                           ("peak", _number(reading, "memory_peak_bytes"))):
        if actual > point.limit[target]:
            failures.append(f"{where}: {target} {actual!r} over its limit "
                            f"{point.limit[target]!r}")
    return failures


def check_report(points: list[BoundaryPoint], readings: list[Mapping[str, object]],
                 failures: list[str]) -> str:
    """The tier as markdown for `$GITHUB_STEP_SUMMARY`: one row per point with its reading and its
    limits, then every failure. A reading that is not ok shows a dash for each figure (L02)."""
    lines = ["### Required tier (R27, R29)", "",
             f"{len(points)} points, {len(failures)} failures.", "",
             "| point | artifact | status | cold wall s | timeout s | seconds limit | bytes "
             "| bytes limit | peak bytes | peak limit |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for point, reading in zip(points, readings, strict=True):
        wall = bytes_ = peak = "-"
        if reading.get("status") == "ok":
            wall = f"{_number(reading, 'build_s') + _number(reading, 'export_s'):.3f}"
            bytes_ = f"{_number(reading, 'bytes'):.0f}"
            peak = f"{_number(reading, 'memory_peak_bytes'):.0f}"
        lines.append(f"| {point.point.label} | {point.point.artifact} | {reading.get('status')} "
                     f"| {wall} | {point.timeout_s:g} | {point.limit['seconds']:.3f} | {bytes_} "
                     f"| {point.limit['bytes']:.0f} | {peak} | {point.limit['peak']:.0f} |")
    if failures:
        lines += ["", "### Failures", "", *(f"- {failure}" for failure in failures)]
    return "\n".join(lines)


def _cmd_check(args: argparse.Namespace) -> int:
    try:
        points = load_boundary(Path(args.file), args.shard)
    except (OSError, ValueError) as exc:
        print(f"oper: {exc}", file=sys.stderr)
        return 2
    if not points:
        print(f"oper: {args.file} holds no point, and no reading is not a pass", file=sys.stderr)
        return 1
    try:
        versions = _image_versions(args.image)
        head = header(args.image, versions)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"oper: cannot read image {args.image}: {exc}", file=sys.stderr)
        return 2
    readings: list[Mapping[str, object]] = []
    with contextlib.ExitStack() as stack:
        sink = None if args.out is None else stack.enter_context(Path(args.out).open("w"))
        if sink is not None:
            _emit(sink, head)
        for n, boundary in enumerate(points, 1):
            reading = run_reading(boundary.point, 1, args.image, CAP_BYTES, DEADLINE_S, versions)
            if sink is not None:
                _emit(sink, reading)
            readings.append(reading)
            print(f"[{n}/{len(points)}] {boundary.point.label} at {boundary.point.artifact}: "
                  f"{reading.get('status')}", file=sys.stderr, flush=True)
    failures = [failure for boundary, reading in zip(points, readings, strict=True)
                for failure in judge(boundary, reading)]
    print(check_report(points, readings, failures))
    return 1 if failures else 0


def _rep_ids(text: str) -> list[int]:
    """`"1,2,3"` as `[1, 2, 3]`: the repetitions a summary expects, each a whole number from 1."""
    try:
        ids = [int(token) for token in text.split(",")]
    except ValueError:
        _refuse(f"--reps {text!r}: expected whole numbers separated by commas")
    if not ids or any(rep < 1 for rep in ids) or len(set(ids)) != len(ids):
        _refuse(f"--reps {text!r}: expected distinct repetitions from 1")
    return ids


def _cmd_summarize(args: argparse.Namespace) -> int:
    try:
        headers, readings = _read_records(args.files)
    except OSError as exc:
        print(f"oper: cannot read {exc.filename}: {exc.strerror}", file=sys.stderr)
        return 1
    try:
        rows = summarize(readings, _rep_ids(args.reps))
    except ValueError as exc:
        print(f"oper: {exc}", file=sys.stderr)
        return 2
    if not rows:
        print("no readings", file=sys.stderr)
        return 1
    print(markdown_report(headers, readings, rows) if args.markdown else format_rows(rows))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m bench.oper", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    point = commands.add_parser("point", help="take --reps readings of one point")
    point.add_argument("--kind", required=True)
    point.add_argument("--params", default="", help='"name=value ..." (numbers, true, false)')
    point.add_argument("--artifact", choices=list(_ARTIFACTS), help="for a part")
    point.add_argument("--probe", help=f"for --kind {PROBE_KIND}: one of {sorted(PROBE_ARGS)}")
    point.add_argument("--label", default="point")
    point.add_argument("--image", required=True)
    point.add_argument("--reps", type=int, default=5)
    point.add_argument("--out", default="-", help="a JSONL path, or - for stdout")
    point.set_defaults(handler=_cmd_point)

    matrix = commands.add_parser("matrix", help="print the workflow matrix of a point file")
    matrix.add_argument("--set", required=True)
    matrix.set_defaults(handler=_cmd_matrix)

    run = commands.add_parser("run", help="one repetition of one shard of a point file")
    run.add_argument("--set", required=True)
    run.add_argument("--shard", type=int, required=True)
    run.add_argument("--rep", type=int, required=True)
    run.add_argument("--image", required=True)
    run.add_argument("--out", required=True, help="a JSONL path, or - for stdout")
    run.add_argument("--followup-from", help="the run's measure records: read this shard of R5's "
                                             "follow-up selection instead (07-19)")
    run.set_defaults(handler=_cmd_run)

    followup = commands.add_parser("followup-matrix", help="the matrix of R5's follow-up jobs "
                                                           "from a run's measure records")
    followup.add_argument("--set", required=True)
    followup.add_argument("--from", dest="source", required=True)
    followup.set_defaults(handler=_cmd_followup_matrix)

    verdict_command = commands.add_parser("verdict", help="R29 over every reading of a full-tier "
                                                          "run, its follow-ups included")
    verdict_command.add_argument("--set", required=True)
    verdict_command.add_argument("--from", dest="source", required=True)
    verdict_command.set_defaults(handler=_cmd_verdict)

    summary = commands.add_parser("summarize", help="median and max per point from JSONL files")
    summary.add_argument("files", nargs="+")
    summary.add_argument("--reps", default=",".join(map(str, BOUND_REPS)),
                         help="the repetitions each point must have, once each: 1,2,3,4,5 for a "
                              "set that sets a bound (R3), 1 for explore, $REP for one job's file")
    summary.add_argument("--markdown", action="store_true",
                         help="a per-run table for $GITHUB_STEP_SUMMARY")
    summary.set_defaults(handler=_cmd_summarize)

    check = commands.add_parser("check", help="read the required tier once each and fail on "
                                              "R29's failures (07-18)")
    check.add_argument("file", help="a boundary file, tests/data/oper_boundary.json")
    check.add_argument("--image", required=True)
    check.add_argument("--shard", type=int, help="only this 1-based shard of the file's "
                                                 "shard_sizes (G34)")
    check.add_argument("--out", help="a JSONL path for the header and every reading, in `run`'s "
                                     "format")
    check.set_defaults(handler=_cmd_check)

    args = parser.parse_args(argv)
    code: int = args.handler(args)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
