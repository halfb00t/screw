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
import itertools
import json
import math
import os
import statistics
import subprocess
import sys
import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn, TextIO

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
}
_PROBE_FLAGS = frozenset({"left_hand"})
_PROBE_POINT_KEYS = frozenset({"label", "kind", "probe", "args"})
# What a line that is not ok may keep: its reason and the versions, never a figure.
_KEPT_WITHOUT_FIGURES = ("status", "error", "message", "cadquery", "cadquery_ocp")
# The figures a summary takes a median and a max of; a probe has no export, so it has two.
_METRICS = ("build_s", "export_s", "bytes", "memory_peak_bytes")
_PROBE_METRICS = ("build_s", "memory_peak_bytes")
_STDERR_TAIL = 2000

_container_numbers = itertools.count(1)

# The point files a workflow may name, and the artifacts a point may ask for.
POINTS_DIR = _REPO_ROOT / "bench" / "points"
_ARTIFACTS = ("stl-preview", "stl-fine", "step")
_SET_NAME_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-")
_SET_KEYS = frozenset({"set", "rule", "reps", "shards", "deadline_s", "points"})
# What the generator (`bench.oper_sets`) adds: the combinations the parameter model refused and
# why the set holds what it holds. The runner never reads either; it only checks their shape.
_SET_OPTIONAL_KEYS = frozenset({"dropped", "notes"})
_POINT_KEYS = frozenset({"label", "kind", "params", "artifact"})
# `preset` is the catalogue row id a point was expanded from; `lift` names the one validator guard
# a past-the-cap point lifts (`bench.oper_lift`), as `{"max_turns": 260}` or `{"max_mm": 1e6}`.
_POINT_OPTIONAL_KEYS = frozenset({"preset", "lift"})
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

    def as_json(self) -> str:
        if self.kind == PROBE_KIND:
            return json.dumps({"kind": PROBE_KIND, "probe": self.artifact,
                               "args": dict(self.params)}, sort_keys=True, allow_nan=False)
        part: dict[str, object] = {"kind": self.kind, "params": dict(self.params),
                                   "artifact": self.artifact}
        if self.lift:
            part["lift"] = dict(self.lift)
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


def parse_child_line(line: str, *, probe: bool = False) -> dict[str, object]:
    """One child line as a record, or `ValueError`.

    Refuses NaN, infinity and negatives anywhere (but a probe's volume ratio, which is signed), a
    missing key on an ok line, an unknown status and anything that is not one JSON object. A
    line that is not ok is cut down to its reason: a refused child has no business reporting a
    build time (L02, T-07-01). `probe` says what the parent asked for, so a part's ok line is not
    taken for a probe's and the other way round.
    """
    try:
        record = json.loads(line, parse_constant=_refuse_constant)
    except json.JSONDecodeError as exc:
        raise ValueError(f"child line is not JSON: {line[:120]!r}") from exc
    if not isinstance(record, dict):
        _refuse(f"child line is not a JSON object: {line[:120]!r}")
    status = record.get("status")
    # A list or an object is unhashable and cannot be tested for membership: type first.
    if not isinstance(status, str) or status not in _CHILD_STATUSES:
        raise ValueError(f"child line has status {status!r}, not one of {sorted(_CHILD_STATUSES)}")
    for key, value in record.items():
        _check_number(str(key), value)
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
             cap: int, probe: bool = False) -> dict[str, object]:
    """How a reading ended, as `status` plus only what that status may carry.

    In order: past the deadline is `killed`; Docker's `OOMKilled` is `capped`; any non-zero exit
    (a signal included) or a last line that is not a valid child line is `crashed`, with the exit
    code and the stderr tail as evidence; the child's own `refused` and `no_cgroup` stand; an ok
    line whose peak is at the cap, or whose cgroup counted an OOM kill, is `capped`. Only a clean
    ok line keeps its figures. `probe` is whether the point was a probe (see `parse_child_line`).
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
        child = parse_child_line(lines[-1], probe=probe)
    except ValueError as exc:
        return {**crashed, "problem": str(exc)}
    if child["status"] != "ok":
        return child
    peak = child["memory_peak_bytes"]
    kills = child.get("oom_kills")
    if (isinstance(peak, int) and is_capped(peak, cap)) or (isinstance(kills, int) and kills > 0):
        return {"status": "capped",
                **{key: child[key] for key in ("cadquery", "cadquery_ocp") if key in child}}
    return child


def reading_argv(name: str, image: str, repo_root: Path, point_json: str, cap: int) -> list[str]:
    """The argv for one reading. A list, never a shell string. House shape of
    `bench.thread_spike.runner.container_argv` with three differences: no `--rm`, because the
    parent must `docker inspect` the stopped container for `OOMKilled` before removing it; the
    memory and swap caps both at `cap`, so the cap is a wall and not a suggestion; and no
    `--platform`, so the host's `DOCKER_DEFAULT_PLATFORM` decides (native on the runner). The
    image runs as uid 10001 and has no `bench/`, so the repository's is mounted read-only."""
    return ["docker", "run", "--name", name, f"--memory={cap}b", f"--memory-swap={cap}b",
            "--entrypoint", "python", "-v", f"{repo_root}/bench:/probe/bench:ro",
            "-e", "PYTHONPATH=/probe", image, "-m", "bench.oper_child", point_json]


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
    argv = reading_argv(name, image, _REPO_ROOT, point.as_json(), cap)
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
                      stdout=stdout, stderr=stderr, cap=cap, probe=point.kind == PROBE_KIND)
    record: dict[str, object] = {
        "type": "reading", "label": point.label, "kind": point.kind, "params": dict(point.params),
        "artifact": point.artifact, "rep": rep, "load1": load1, "container": name, **result,
        "wall_s": wall_s}
    if point.lift:
        record["lift"] = dict(point.lift)  # a reading past a guard says which guard it lifted
    for key in ("cadquery", "cadquery_ocp"):
        if key not in record and versions is not None:
            record[key] = versions.get(key)
    return record


def summarize(readings: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    """Per (label, artifact, lift), in first-seen order: how many repetitions, a count per status,
    the status of the point, and the median (`statistics.median`) and max of each metric over the
    repetitions. A point with any repetition that is not ok has no median and no max: four good
    repetitions and one capped one are not a measurement of the part (D-04, L02). The status is
    `ok`, the one failing status when they agree, or `mixed`.

    A reading past a validator guard (`lift`) is a confirmation probe of a wall, not a part anyone
    can request: it keeps its own row, names its lift, and has a status and no median or max, so it
    cannot supply a bound or a fit figure (R3, R7, R8)."""
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
        lift = json.loads(lift_text)
        median: dict[str, float] | None = None
        maximum: dict[str, float] | None = None
        if status == "ok" and lift is None:
            metrics = _PROBE_METRICS if group[0].get("kind") == PROBE_KIND else _METRICS
            columns = {m: [_number(r, m) for r in group] for m in metrics}
            median = {m: statistics.median(values) for m, values in columns.items()}
            maximum = {m: max(values) for m, values in columns.items()}
        rows.append({"label": label, "artifact": artifact, "lift": lift, "n": len(group),
                     "status": status, "counts": counts, "median": median, "max": maximum})
    return rows


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


def _load_point(name: str, raw: object) -> Point:
    if isinstance(raw, dict) and raw.get("kind") == PROBE_KIND:
        return _load_probe(f"set {name!r}", raw)
    allowed = _POINT_KEYS | _POINT_OPTIONAL_KEYS
    if not isinstance(raw, dict) or not _POINT_KEYS <= set(raw) <= allowed:
        _refuse(f"set {name!r}: a point needs the keys {sorted(_POINT_KEYS)} "
                f"and may add {sorted(_POINT_OPTIONAL_KEYS)}")
    if "preset" in raw and not isinstance(raw["preset"], str):
        _refuse(f"set {name!r}: a point's preset is the text of a catalogue row id")
    lift = _load_lift(name, raw)
    label, kind, params, artifact = raw["label"], raw["kind"], raw["params"], raw["artifact"]
    if not (isinstance(label, str) and label and isinstance(kind, str) and kind):
        _refuse(f"set {name!r}: a point's label and kind are non-empty text")
    if artifact not in _ARTIFACTS:
        _refuse(f"set {name!r}: artifact {artifact!r} is not one of {list(_ARTIFACTS)}")
    if not isinstance(params, dict) or not all(
            isinstance(key, str) and (isinstance(value, bool) or _is_number(value))
            for key, value in params.items()):
        _refuse(f"set {name!r}: point {label!r} params are names with a number or true/false")
    return Point(label=label, kind=kind, params=dict(params), artifact=str(artifact), lift=lift)


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
    return PointSet(name=name, rule=raw["rule"], reps=raw["reps"], shards=raw["shards"],
                    deadline_s=float(raw["deadline_s"]), points=points)


def shard_points(spec: PointSet, shard: int) -> list[Point]:
    """The points of 1-based `shard`: point `i` of the file (0-based) goes to shard
    `i % shards + 1`, so two runs of one file split it the same way."""
    return [p for i, p in enumerate(spec.points) if i % spec.shards + 1 == shard]


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


def _write_run(image: str, out: str, plan: list[tuple[Point, int]], deadline_s: float) -> int:
    """The header, then one reading per `(point, rep)` of `plan`, in plan order."""
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
            _emit(sink, run_reading(point, rep, image, CAP_BYTES, deadline_s, versions))
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
        if not 1 <= args.shard <= spec.shards:
            _refuse(f"set {spec.name!r}: shard {args.shard} is outside 1..{spec.shards}")
        if not 1 <= args.rep <= spec.reps:
            _refuse(f"set {spec.name!r}: rep {args.rep} is outside 1..{spec.reps}")
    except ValueError as exc:
        print(f"oper: {exc}", file=sys.stderr)
        return 2
    plan = [(point, args.rep) for point in shard_points(spec, args.shard)]
    return _write_run(args.image, args.out, plan, spec.deadline_s)


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
        label = f"{row['label']} (lift {json.dumps(row['lift'], sort_keys=True)})" if row[
            "lift"] else row["label"]
        lines.append(f"| {label} | {row['artifact']} | {row['n']} | {row['status']} "
                     f"| {counts} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _cmd_summarize(args: argparse.Namespace) -> int:
    try:
        headers, readings = _read_records(args.files)
    except OSError as exc:
        print(f"oper: cannot read {exc.filename}: {exc.strerror}", file=sys.stderr)
        return 1
    rows = summarize(readings)
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
    run.set_defaults(handler=_cmd_run)

    summary = commands.add_parser("summarize", help="median and max per point from JSONL files")
    summary.add_argument("files", nargs="+")
    summary.add_argument("--markdown", action="store_true",
                         help="a per-run table for $GITHUB_STEP_SUMMARY")
    summary.set_defaults(handler=_cmd_summarize)

    args = parser.parse_args(argv)
    code: int = args.handler(args)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
