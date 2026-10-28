"""The Runs II readings that run inside the image (07-06): contention (R14), drift and arenas (R23).

The pool is real (`screw.pool.BuildPool`, spawned workers) and the build is a sleeping fake, so
the routing, the one-submission rule, the deadline and the statuses are exercised without a
kernel build. The fakes are module-level functions because `spawn` pickles a function by its
qualified name (the `tests/test_pool.py` `_sleep_past_timeout` pattern).
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Mapping
from pathlib import Path

import pytest

from bench import oper_bound
from bench.oper_child import CgroupUnavailable
from screw.build_errors import BuildError
from screw.params import KINDS

PEAK = 123_456_789
# The task's own figures differ from its sleep, so a record that timed submit-to-result instead
# of taking them from the worker shows it.
P_SLEEP_S, PARTNER_SLEEP_S = 0.6, 0.1
FIGURES = {"bolt": {"build_s": 0.25, "export_s": 0.125, "bytes": 1000, "gzip1_bytes": 400},
           "nut": {"build_s": 0.05, "export_s": 0.025, "bytes": 500, "gzip1_bytes": 200}}
PID_DIR_ENV = "SCREW_TEST_OPER_BOUND_PIDS"


def _sleep_by_kind(kind: str, params: Mapping[str, object], fmt: str,
                   quality: str) -> dict[str, object]:
    """P sleeps longer than its partner; when the test names a directory, every call appends
    its kind and its worker's pid there, so the test counts the builds and the workers."""
    if PID_DIR_ENV in os.environ:
        with (Path(os.environ[PID_DIR_ENV]) / "calls").open("a") as calls:
            calls.write(f"{kind} {os.getpid()}\n")
    time.sleep(P_SLEEP_S if kind == "bolt" else PARTNER_SLEEP_S)
    return {"status": "ok", **FIGURES[kind]}


def _refuse_the_nut(kind: str, params: Mapping[str, object], fmt: str,
                    quality: str) -> dict[str, object]:
    if kind == "nut":
        raise BuildError("no nut today")
    return {"status": "ok", **FIGURES[kind]}


def _break_the_nut(kind: str, params: Mapping[str, object], fmt: str,
                   quality: str) -> dict[str, object]:
    if kind == "nut":
        raise ArithmeticError("a bug, not a kernel refusal")
    return {"status": "ok", **FIGURES[kind]}


def _sleep_past_the_deadline(kind: str, params: Mapping[str, object], fmt: str,
                             quality: str) -> dict[str, object]:
    (Path(os.environ[PID_DIR_ENV]) / kind).write_text(str(os.getpid()))
    time.sleep(60)
    return {"status": "ok", **FIGURES[kind]}


def _slot(kind: str, params: Mapping[str, object], workers: int) -> int:
    return hash(KINDS[kind].model_validate(params)) % workers


BOLT = {"label": "default-bolt", "kind": "bolt", "params": {}, "slot": 0}
NUT = {"label": "default-nut", "kind": "nut", "params": {}, "slot": 1}
FIGURE_KEYS = ("build_s", "export_s", "bytes", "gzip1_bytes", "memory_peak_bytes", "builds")
# A build that ended badly leaves the container's peak on the line for the parent's cap test
# (R2: capped comes first); `bench.oper.classify` drops it with every other number.
BUILD_KEYS = ("build_s", "export_s", "bytes", "gzip1_bytes", "builds")


def _contention(points: list[dict[str, object]], workers: int = 2, deadline_s: float = 60,
                task: oper_bound.Task = _sleep_by_kind,
                read_peak: Callable[[], int] = lambda: PEAK) -> dict[str, object]:
    return oper_bound.contention(points, workers, deadline_s, artifact="stl-preview", task=task,
                                 read_peak=read_peak, oom_kills=lambda: 0)


def test_the_default_bolt_and_nut_sit_on_different_slots_at_two_workers() -> None:
    assert (_slot("bolt", {}, 2), _slot("nut", {}, 2)) == (0, 1)


def test_a_two_worker_reading_builds_each_point_once_on_its_own_worker(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PID_DIR_ENV, str(tmp_path))
    record = _contention([BOLT, NUT])
    calls = [line.split() for line in (tmp_path / "calls").read_text().splitlines()]
    assert sorted(kind for kind, _ in calls) == ["bolt", "nut"]  # each built once
    assert len({pid for _, pid in calls}) == 2  # on two workers
    assert str(os.getpid()) not in {pid for _, pid in calls}  # neither in this process
    assert record["status"] == "ok"
    assert record["memory_peak_bytes"] == PEAK
    # P's figures are the task's own, not the 0.6 s from submit to result.
    assert (record["build_s"], record["export_s"], record["bytes"]) == (0.25, 0.125, 1000)
    assert record["builds"] == [
        {"label": "default-bolt", "slot": 0, "status": "ok", **FIGURES["bolt"]},
        {"label": "default-nut", "slot": 1, "status": "ok", **FIGURES["nut"]}]


def test_one_worker_reads_the_bound_point_alone() -> None:
    record = _contention([BOLT], workers=1)
    assert record["status"] == "ok"
    assert record["builds"] == [
        {"label": "default-bolt", "slot": 0, "status": "ok", **FIGURES["bolt"]}]


def test_a_point_the_pool_routes_to_another_slot_is_crashed_with_both_slots_and_no_figure() -> None:
    swapped = [{**BOLT, "slot": 1}, {**NUT, "slot": 0}]
    record = _contention(swapped)
    assert record["status"] == "crashed"
    message = str(record["message"])
    assert "default-bolt" in message
    assert "slot 1" in message
    assert "slot 0" in message
    assert [key for key in FIGURE_KEYS if key in record] == []


@pytest.mark.parametrize(
    ("points", "workers"),
    [([BOLT], 2), ([BOLT, {**NUT, "slot": 0}], 2), ([BOLT, NUT], 1),
     ([BOLT, {**NUT, "slot": 2}], 2)],
    ids=["one-point-two-workers", "two-on-one-slot", "two-points-one-worker", "slot-past-n"])
def test_a_reading_that_is_not_one_point_per_slot_is_refused_naming_r14(
        points: list[dict[str, object]], workers: int) -> None:
    with pytest.raises(ValueError, match="R14"):
        _contention(points, workers=workers)


def test_a_kernel_refusal_of_a_partner_is_refused_with_its_class_and_text_and_no_figure() -> None:
    record = _contention([BOLT, NUT], task=_refuse_the_nut)
    assert record["status"] == "refused"
    assert record["error"] == "BuildError"
    assert "no nut today" in str(record["message"])
    assert "default-nut" in str(record["message"])
    assert [key for key in BUILD_KEYS if key in record] == []


def test_any_other_exception_in_a_build_is_crashed() -> None:
    record = _contention([BOLT, NUT], task=_break_the_nut)
    assert record["status"] == "crashed"
    assert record["error"] == "ArithmeticError"
    assert [key for key in BUILD_KEYS if key in record] == []


def test_an_unreadable_cgroup_is_no_cgroup_and_no_figure() -> None:
    def no_peak() -> int:
        raise CgroupUnavailable("no memory.peak")

    record = _contention([BOLT, NUT], read_peak=no_peak)
    assert record["status"] == "no_cgroup"
    assert [key for key in FIGURE_KEYS if key in record] == []


def _gone(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    return False


def test_a_build_past_the_deadline_is_killed_and_its_worker_terminated(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PID_DIR_ENV, str(tmp_path))
    started = time.perf_counter()
    record = _contention([BOLT, NUT], deadline_s=2, task=_sleep_past_the_deadline)
    assert time.perf_counter() - started < 30  # the 60 s sleep was not waited out
    assert record["status"] == "killed"
    assert [key for key in FIGURE_KEYS if key in record] == []
    pids = [int((tmp_path / kind).read_text()) for kind in ("bolt", "nut")]
    deadline = time.monotonic() + 10
    while not all(_gone(pid) for pid in pids) and time.monotonic() < deadline:
        time.sleep(0.1)
    assert all(_gone(pid) for pid in pids)


def test_the_build_task_builds_exports_and_gzips_a_real_part() -> None:
    record = oper_bound.build_task("bolt", {}, "stl", "preview")
    assert record["status"] == "ok"
    for key in ("build_s", "export_s"):
        value = record[key]
        assert isinstance(value, float)
        assert value > 0
    raw, packed = record["bytes"], record["gzip1_bytes"]
    assert isinstance(raw, int)
    assert isinstance(packed, int)
    assert 0 < packed < raw


def test_the_child_prints_one_line_for_a_contention_point(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    seen: list[tuple[object, ...]] = []

    def fake(points: list[dict[str, object]], workers: int, deadline_s: float, *,
             artifact: str) -> dict[str, object]:
        seen.append((points, workers, deadline_s, artifact))
        return {"status": "ok", "build_s": 1.0}

    monkeypatch.setattr(oper_bound, "contention", fake)
    point = {"kind": "contention", "artifact": "stl-preview", "workers": 2, "points": [BOLT, NUT]}
    assert oper_bound.main([json.dumps(point)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    assert '"status": "ok"' in lines[0]
    assert '"cadquery"' in lines[0]
    assert seen == [([BOLT, NUT], 2, 600, "stl-preview")]


@pytest.mark.parametrize("text", ["not json", '{"kind": "memory"}', '{"kind": "contention"}',
                                  '{"kind": "contention", "artifact": "stl-preview", '
                                  '"workers": 2, "points": [{"label": "a", "kind": "bolt", '
                                  '"params": {}, "slot": 0}]}'],
                         ids=["garbage", "unknown-kind", "missing-fields", "r14"])
def test_a_point_the_child_cannot_read_is_an_exit_2_with_no_line(
        text: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert oper_bound.main([text]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err != ""
