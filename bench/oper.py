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
# What a line that is not ok may keep: its reason and the versions, never a figure.
_KEPT_WITHOUT_FIGURES = ("status", "error", "message", "cadquery", "cadquery_ocp")
# The figures a summary takes a median and a max of.
_METRICS = ("build_s", "export_s", "bytes", "memory_peak_bytes")
_STDERR_TAIL = 2000

_container_numbers = itertools.count(1)


@dataclass(frozen=True)
class Point:
    """What one reading builds: a part (`kind`, `params`) and one artifact of it."""

    label: str
    kind: str
    params: Mapping[str, float | bool]
    artifact: str

    def as_json(self) -> str:
        return json.dumps({"kind": self.kind, "params": dict(self.params),
                           "artifact": self.artifact}, sort_keys=True, allow_nan=False)


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
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"child line: {key} is {value!r}, not a finite non-negative number")


def parse_child_line(line: str) -> dict[str, object]:
    """One child line as a record, or `ValueError`.

    Refuses NaN, infinity and negatives anywhere, a missing key on an ok line, an unknown status
    and anything that is not one JSON object. A line that is not ok is cut down to its reason: a
    refused child has no business reporting a build time (L02, T-07-01).
    """
    try:
        record = json.loads(line, parse_constant=_refuse_constant)
    except json.JSONDecodeError as exc:
        raise ValueError(f"child line is not JSON: {line[:120]!r}") from exc
    if not isinstance(record, dict):
        _refuse(f"child line is not a JSON object: {line[:120]!r}")
    status = record.get("status")
    if status not in _CHILD_STATUSES:
        raise ValueError(f"child line has status {status!r}, not one of {sorted(_CHILD_STATUSES)}")
    for key, value in record.items():
        _check_number(str(key), value)
    if status != "ok":
        return {key: record[key] for key in _KEPT_WITHOUT_FIGURES if key in record}
    for key in (*_OK_SECONDS, *_OK_COUNTS):
        if key not in record:
            raise ValueError(f"ok child line is missing {key}")
    for key in _OK_COUNTS:
        value = record[key]
        if isinstance(value, bool) or not isinstance(value, int):
            _refuse(f"ok child line: {key} is {value!r}, not a whole number")
    for key in _OK_SECONDS:
        value = record[key]
        if isinstance(value, bool) or not isinstance(value, int | float):
            _refuse(f"ok child line: {key} is {value!r}, not a number")
    return dict(record)


def classify(*, timed_out: bool, oom_killed: bool, exit_code: int, stdout: str, stderr: str,
             cap: int) -> dict[str, object]:
    """How a reading ended, as `status` plus only what that status may carry.

    In order: past the deadline is `killed`; Docker's `OOMKilled` is `capped`; any non-zero exit
    (a signal included) or a last line that is not a valid child line is `crashed`, with the exit
    code and the stderr tail as evidence; the child's own `refused` and `no_cgroup` stand; an ok
    line whose peak is at the cap, or whose cgroup counted an OOM kill, is `capped`. Only a clean
    ok line keeps its figures.
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
        child = parse_child_line(lines[-1])
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
                      stdout=stdout, stderr=stderr, cap=cap)
    record: dict[str, object] = {
        "type": "reading", "label": point.label, "kind": point.kind, "params": dict(point.params),
        "artifact": point.artifact, "rep": rep, "load1": load1, "container": name, **result,
        "wall_s": wall_s}
    for key in ("cadquery", "cadquery_ocp"):
        if key not in record and versions is not None:
            record[key] = versions.get(key)
    return record


def summarize(readings: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    """Per (label, artifact), in first-seen order: how many repetitions, a count per status, the
    status of the point, and the median (`statistics.median`) and max of each metric over the
    repetitions. A point with any repetition that is not ok has no median and no max: four good
    repetitions and one capped one are not a measurement of the part (D-04, L02). The status is
    `ok`, the one failing status when they agree, or `mixed`."""
    grouped: dict[tuple[object, object], list[Mapping[str, object]]] = {}
    for reading in readings:
        grouped.setdefault((reading["label"], reading["artifact"]), []).append(reading)
    rows: list[dict[str, object]] = []
    for (label, artifact), group in grouped.items():
        counts: dict[str, int] = {}
        for reading in group:
            counts[str(reading["status"])] = counts.get(str(reading["status"]), 0) + 1
        failing = [status for status in counts if status != "ok"]
        status = "ok" if not failing else failing[0] if len(failing) == 1 else "mixed"
        median: dict[str, float] | None = None
        maximum: dict[str, float] | None = None
        if status == "ok":
            columns = {m: [_number(r, m) for r in group] for m in _METRICS}
            median = {m: statistics.median(values) for m, values in columns.items()}
            maximum = {m: max(values) for m, values in columns.items()}
        rows.append({"label": label, "artifact": artifact, "n": len(group), "status": status,
                     "counts": counts, "median": median, "max": maximum})
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
        median, maximum = row["median"], row["max"]
        if isinstance(median, dict) and isinstance(maximum, dict):
            head += "".join(f"  {m}: median {median[m]:.3f} max {maximum[m]:.3f}" for m in _METRICS)
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


def _cmd_point(args: argparse.Namespace) -> int:
    try:
        params = parse_params(args.params)
    except ValueError as exc:
        print(f"oper: {exc}", file=sys.stderr)
        return 2
    point = Point(label=args.label, kind=args.kind, params=params, artifact=args.artifact)
    try:
        versions = _image_versions(args.image)
        head = header(args.image, versions)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"oper: cannot read image {args.image}: {exc}", file=sys.stderr)
        return 2
    sink = _open_sink(args.out)
    try:
        _emit(sink, head)
        for rep in range(1, args.reps + 1):
            _emit(sink, run_reading(point, rep, args.image, CAP_BYTES, DEADLINE_S, versions))
    finally:
        if sink is not sys.stdout:
            sink.close()
    return 0


def _read_readings(paths: list[str]) -> list[dict[str, object]]:
    readings: list[dict[str, object]] = []
    for path in paths:
        for line in Path(path).read_text().splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if isinstance(record, dict) and record.get("type") == "reading":
                readings.append(record)
    return readings


def _cmd_summarize(args: argparse.Namespace) -> int:
    rows = summarize(_read_readings(args.files))
    if not rows:
        print("no readings", file=sys.stderr)
        return 1
    print(format_rows(rows))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m bench.oper", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    point = commands.add_parser("point", help="take --reps readings of one point")
    point.add_argument("--kind", required=True)
    point.add_argument("--params", default="", help='"name=value ..." (numbers, true, false)')
    point.add_argument("--artifact", required=True, choices=["stl-preview", "stl-fine", "step"])
    point.add_argument("--label", default="point")
    point.add_argument("--image", required=True)
    point.add_argument("--reps", type=int, default=5)
    point.add_argument("--out", default="-", help="a JSONL path, or - for stdout")
    point.set_defaults(handler=_cmd_point)

    summary = commands.add_parser("summarize", help="median and max per point from JSONL files")
    summary.add_argument("files", nargs="+")
    summary.set_defaults(handler=_cmd_summarize)

    args = parser.parse_args(argv)
    code: int = args.handler(args)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
