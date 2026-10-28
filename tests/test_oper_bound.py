"""The Runs II readings that run inside the image (07-06): contention (R14), drift and arenas (R23).

The pool is real (`screw.pool.BuildPool`, spawned workers) and the build is a sleeping fake, so
the routing, the one-submission rule, the deadline and the statuses are exercised without a
kernel build. The fakes are module-level functions because `spawn` pickles a function by its
qualified name (the `tests/test_pool.py` `_sleep_past_timeout` pattern).
"""

from __future__ import annotations

import json
import os
import sys
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


# --- drift and arenas (R23) ----------------------------------------------------------------------

DEFAULT_BOLT_PART = {"kind": "bolt", "params": {}}


class _Kernel:
    """Fakes of the kernel's build, export and cache clear, a gzip and a peak reader, writing
    what they do to one log so a test reads the order."""

    def __init__(self, *, refuse_at: int | None = None, peak_error: bool = False) -> None:
        self.log: list[str] = []
        self.builds = 0
        self.refuse_at = refuse_at
        self.peak_error = peak_error
        self.trim_seen: list[object] = []
        self.exported: list[tuple[object, str, str]] = []

    def clear(self) -> None:
        self.log.append("clear")

    def build(self, p: object) -> object:
        self.builds += 1
        self.log.append("build")
        if self.builds == self.refuse_at:
            raise BuildError("no solid at this build")
        return p

    def export(self, p: object, fmt: str, quality: str) -> bytes:
        from screw import solid

        self.log.append("export")
        self.exported.append((p, fmt, quality))
        self.trim_seen.append(vars(solid)["_MALLOC_TRIM"])
        return b"x" * (100 * self.builds)  # build 1's export is 100 bytes, later ones larger

    def gzip1(self, data: bytes) -> bytes:
        self.log.append("gzip")
        return data[:10]

    def peak(self) -> int:
        self.log.append("peak")
        if self.peak_error:
            raise CgroupUnavailable("no memory.peak")
        return PEAK + len(self.log)

    def current(self) -> int:
        self.log.append("current")
        return 7_000_000

    def rss(self) -> int:
        self.log.append("rss")
        return 5_000_000


def _drift(kernel: _Kernel, k: int = 3) -> dict[str, object]:
    point = {"kind": "drift", "artifact": "stl-preview", "part": DEFAULT_BOLT_PART, "k": k,
             "deadline_s": 600}
    return oper_bound.drift(point, build=kernel.build, export=kernel.export,
                            read_peak=kernel.peak, clear=kernel.clear, gzip1=kernel.gzip1,
                            oom_kills=lambda: 0)


def test_a_drift_reading_builds_cold_and_reads_the_peak_after_the_gzip_each_time() -> None:
    kernel = _Kernel()
    record = _drift(kernel)
    assert kernel.log == ["clear", "build", "export", "gzip", "peak"] * 3
    assert [(fmt, quality) for _, fmt, quality in kernel.exported] == [("stl", "preview")] * 3
    assert {type(p).__name__ for p, _, _ in kernel.exported} == {"BoltParams"}
    assert record["status"] == "ok"
    peaks = record["peaks"]
    assert isinstance(peaks, list)
    assert len(peaks) == 3
    assert record["memory_peak_bytes"] == max(peaks)
    assert record["bytes"] == 100  # build 1's, not a later build's
    for key in ("build_s", "export_s"):
        assert isinstance(record[key], float)


def test_a_drift_reading_with_an_unreadable_cgroup_has_no_peaks() -> None:
    record = _drift(_Kernel(peak_error=True))
    assert record["status"] == "no_cgroup"
    assert [key for key in (*FIGURE_KEYS, "peaks") if key in record] == []


def test_a_drift_reading_refused_at_build_2_is_refused_with_no_peaks() -> None:
    kernel = _Kernel(refuse_at=2)
    record = _drift(kernel)
    assert record["status"] == "refused"
    assert record["error"] == "BuildError"
    assert "build 2 of 3" in str(record["message"])
    assert [key for key in (*FIGURE_KEYS, "peaks") if key in record] == []


@pytest.mark.parametrize("k", [1, 2.0, True, None])
def test_a_drift_of_fewer_than_two_whole_builds_is_refused(k: object) -> None:
    point = {"kind": "drift", "artifact": "stl-preview", "part": DEFAULT_BOLT_PART, "k": k}
    kernel = _Kernel()
    with pytest.raises(ValueError, match="k is"):
        oper_bound.drift(point, build=kernel.build, export=kernel.export, clear=kernel.clear)


def test_a_drift_reading_of_a_real_part_takes_build_1s_figures() -> None:
    peaks = iter([10, 20])
    point = {"kind": "drift", "artifact": "stl-preview", "part": DEFAULT_BOLT_PART, "k": 2,
             "deadline_s": 600}
    record = oper_bound.drift(point, read_peak=lambda: next(peaks), oom_kills=lambda: None)
    assert (record["status"], record["peaks"], record["memory_peak_bytes"]) == ("ok", [10, 20], 20)
    assert isinstance(record["bytes"], int)
    assert record["bytes"] > 84


def _arenas(kernel: _Kernel, *, trim: bool) -> dict[str, object]:
    point = {"kind": "arenas", "artifact": "stl-preview", "part": DEFAULT_BOLT_PART, "trim": trim}
    return oper_bound.arenas(point, build=kernel.build, export=kernel.export,
                             read_peak=kernel.peak, read_current=kernel.current,
                             vm_rss=kernel.rss, clear=kernel.clear, gzip1=kernel.gzip1,
                             oom_kills=lambda: 0)


def _trim(size: int) -> int:
    return 0


@pytest.mark.parametrize("trim", [False, True])
def test_an_arena_reading_sets_the_trim_for_the_call_and_restores_it(
        trim: bool, monkeypatch: pytest.MonkeyPatch) -> None:
    from screw import solid

    monkeypatch.setattr(solid, "_MALLOC_TRIM", _trim)
    kernel = _Kernel()
    record = _arenas(kernel, trim=trim)
    assert kernel.trim_seen == [_trim if trim else None]
    assert vars(solid)["_MALLOC_TRIM"] is _trim
    assert kernel.log == ["clear", "build", "export", "current", "rss", "gzip", "peak"]
    assert record["status"] == "ok"
    assert (record["memory_current_bytes"], record["vm_rss_bytes"]) == (7_000_000, 5_000_000)
    assert record["memory_peak_bytes"] == PEAK + 7
    assert record["bytes"] == 100


def test_an_arena_reading_restores_the_trim_when_the_build_is_refused(
        monkeypatch: pytest.MonkeyPatch) -> None:
    from screw import solid

    monkeypatch.setattr(solid, "_MALLOC_TRIM", _trim)
    record = _arenas(_Kernel(refuse_at=1), trim=False)
    assert record["status"] == "refused"
    assert vars(solid)["_MALLOC_TRIM"] is _trim
    assert [key for key in ("memory_current_bytes", "vm_rss_bytes", *FIGURE_KEYS)
            if key in record] == []


def test_a_trim_on_reading_without_malloc_trim_is_not_taken(
        monkeypatch: pytest.MonkeyPatch) -> None:
    from screw import solid

    monkeypatch.setattr(solid, "_MALLOC_TRIM", None)
    with pytest.raises(RuntimeError, match="malloc_trim"):
        _arenas(_Kernel(), trim=True)


def test_an_arena_reading_with_an_unreadable_cgroup_has_no_figure() -> None:
    kernel = _Kernel()

    def no_current() -> int:
        raise CgroupUnavailable("no memory.current")

    point = {"kind": "arenas", "artifact": "stl-preview", "part": DEFAULT_BOLT_PART,
             "trim": False}
    record = oper_bound.arenas(point, build=kernel.build, export=kernel.export,
                               read_peak=kernel.peak, read_current=no_current, vm_rss=kernel.rss,
                               clear=kernel.clear, gzip1=kernel.gzip1, oom_kills=lambda: 0)
    assert record["status"] == "no_cgroup"
    assert [key for key in ("memory_current_bytes", "vm_rss_bytes", *FIGURE_KEYS)
            if key in record] == []


def test_an_arena_reading_of_a_real_part_with_the_trim_off() -> None:
    point = {"kind": "arenas", "artifact": "stl-preview", "part": DEFAULT_BOLT_PART,
             "trim": False}
    linux = sys.platform == "linux"  # /proc/self/status exists nowhere else
    record = oper_bound.arenas(point, read_peak=lambda: 3, read_current=lambda: 2,
                               vm_rss=oper_bound.vm_rss_bytes if linux else lambda: 1,
                               oom_kills=lambda: None)
    assert record["status"] == "ok"
    rss = record["vm_rss_bytes"]
    assert isinstance(rss, int)
    assert rss > (1 if linux else 0)


def _fake_tree(tmp_path: Path, mount: str, files: dict[str, str]) -> Path:
    (tmp_path / "proc" / "self").mkdir(parents=True)
    (tmp_path / "proc" / "mounts").write_text(mount)
    for name, text in files.items():
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    return tmp_path


V2_MOUNT = "cgroup2 /sys/fs/cgroup cgroup2 rw,nosuid,nodev,noexec,relatime 0 0\n"
V1_MOUNT = "cgroup /sys/fs/cgroup/memory cgroup ro,nosuid,nodev,noexec,relatime,memory 0 0\n"


def test_memory_current_is_read_from_cgroup_v2(tmp_path: Path) -> None:
    root = _fake_tree(tmp_path, V2_MOUNT, {"sys/fs/cgroup/memory.current": "4096\n"})
    assert oper_bound.read_current(root) == 4096


def test_a_v1_host_has_no_memory_current_and_no_substitute(tmp_path: Path) -> None:
    root = _fake_tree(tmp_path, V1_MOUNT,
                      {"sys/fs/cgroup/memory/memory.usage_in_bytes": "4096\n"})
    with pytest.raises(CgroupUnavailable):
        oper_bound.read_current(root)


def test_vm_rss_is_read_in_kilobytes_from_proc_self_status(tmp_path: Path) -> None:
    root = _fake_tree(tmp_path, V2_MOUNT, {
        "proc/self/status": "Name:\tpython\nVmHWM:\t  9000 kB\nVmRSS:\t  1234 kB\n"})
    assert oper_bound.vm_rss_bytes(root) == 1234 * 1024


def test_a_status_file_without_vm_rss_is_no_figure(tmp_path: Path) -> None:
    root = _fake_tree(tmp_path, V2_MOUNT, {"proc/self/status": "Name:\tpython\n"})
    with pytest.raises(RuntimeError, match="VmRSS"):
        oper_bound.vm_rss_bytes(root)


@pytest.mark.parametrize("kind", ["drift", "arenas"])
def test_the_child_dispatches_drift_and_arenas_points(
        kind: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    seen: list[Mapping[str, object]] = []

    def fake(point: Mapping[str, object]) -> dict[str, object]:
        seen.append(point)
        return {"status": "ok"}

    monkeypatch.setattr(oper_bound, kind, fake)
    point = {"kind": kind, "artifact": "stl-preview", "part": DEFAULT_BOLT_PART}
    assert oper_bound.main([json.dumps(point)]) == 0
    assert seen == [point]
    assert len(capsys.readouterr().out.splitlines()) == 1
