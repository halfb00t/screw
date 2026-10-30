"""The operability runner harness (07-01): one reading per fresh container, no number it did not
measure.

Everything here is synthetic: a fake `/proc` and cgroup tree, canned child lines, text pins over
the workflow. No Docker and, except for the one end-to-end child test, no kernel. What these
tests protect is L02 for the harness: a capped, killed, crashed, refused or cgroup-blind reading
must come out as a status and never as a plausible figure.
"""

from __future__ import annotations

import functools
import json
import math
import os
import re
import statistics
import subprocess
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import NotRequired, TypedDict

import pytest

import bench
from bench import oper, oper_child

REPO_ROOT = Path(__file__).resolve().parents[1]


# --- the cgroup reader -------------------------------------------------------------------------


def _fake_root(tmp_path: Path, *, mount: str, files: dict[str, str]) -> Path:
    (tmp_path / "proc").mkdir()
    (tmp_path / "proc" / "mounts").write_text(mount)
    for name, text in files.items():
        target = tmp_path / "sys" / "fs" / "cgroup" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    return tmp_path


V2_MOUNT = "cgroup2 /sys/fs/cgroup cgroup2 rw,nosuid,nodev,noexec,relatime 0 0\n"
V1_MOUNT = "cgroup /sys/fs/cgroup/memory cgroup ro,nosuid,nodev,noexec,relatime,memory 0 0\n"


def test_the_peak_is_read_from_cgroup_v2_memory_peak(tmp_path: Path) -> None:
    root = _fake_root(tmp_path, mount=V2_MOUNT, files={"memory.peak": "5640192\n"})
    assert oper_child.read_peak(root) == 5640192


def test_the_peak_is_read_from_cgroup_v1_when_there_is_no_v2_mount(tmp_path: Path) -> None:
    root = _fake_root(tmp_path, mount=V1_MOUNT,
                      files={"memory/memory.max_usage_in_bytes": "7340032\n"})
    assert oper_child.read_peak(root) == 7340032


def test_no_cgroup_file_is_no_peak_not_a_zero(tmp_path: Path) -> None:
    root = _fake_root(tmp_path, mount=V2_MOUNT, files={})
    with pytest.raises(oper_child.CgroupUnavailable):
        oper_child.read_peak(root)


def test_a_v2_mount_without_memory_peak_does_not_fall_back_to_a_v1_file(tmp_path: Path) -> None:
    # A kernel before 5.19 has no memory.peak; a stale v1-looking file must not stand in for it.
    root = _fake_root(tmp_path, mount=V2_MOUNT,
                      files={"memory/memory.max_usage_in_bytes": "7340032\n"})
    with pytest.raises(oper_child.CgroupUnavailable):
        oper_child.read_peak(root)


def test_a_missing_mount_table_is_no_peak(tmp_path: Path) -> None:
    with pytest.raises(oper_child.CgroupUnavailable):
        oper_child.read_peak(tmp_path)


@pytest.mark.parametrize("text", ["max\n", "abc\n", "-5\n", "", "1.5\n"])
def test_a_peak_file_that_is_not_a_count_of_bytes_is_no_peak(tmp_path: Path, text: str) -> None:
    root = _fake_root(tmp_path, mount=V2_MOUNT, files={"memory.peak": text})
    with pytest.raises(oper_child.CgroupUnavailable):
        oper_child.read_peak(root)


def test_oom_kills_come_from_memory_events(tmp_path: Path) -> None:
    root = _fake_root(tmp_path, mount=V2_MOUNT,
                      files={"memory.events": "low 0\nhigh 0\nmax 3\noom 1\noom_kill 1\n"})
    assert oper_child.oom_kills(root) == 1


def test_oom_kills_are_unknown_not_zero_when_the_file_is_absent(tmp_path: Path) -> None:
    assert oper_child.oom_kills(_fake_root(tmp_path, mount=V2_MOUNT, files={})) is None


# --- the cap rule ------------------------------------------------------------------------------


def test_a_peak_at_99_percent_of_the_cap_is_capped() -> None:
    assert oper.is_capped(int(oper.CAP_BYTES * 0.99), oper.CAP_BYTES) is True


def test_a_peak_one_byte_below_99_percent_of_the_cap_is_not_capped() -> None:
    assert oper.is_capped(int(oper.CAP_BYTES * 0.99) - 1, oper.CAP_BYTES) is False


# --- the child's line --------------------------------------------------------------------------


def _ok_line(**over: object) -> str:
    line: dict[str, object] = {
        "status": "ok", "build_s": 1.5, "export_s": 0.25, "bytes": 1000, "triangles": 18,
        "gzip1_bytes": 400, "maxrss_bytes": 90_000_000, "memory_peak_bytes": 120_000_000,
        "oom_kills": 0, "cadquery": "2.8.0", "cadquery_ocp": "7.9.3.1.1"}
    line.update(over)
    return json.dumps(line)


def test_a_well_formed_ok_line_parses() -> None:
    record = oper.parse_child_line(_ok_line())
    assert record["status"] == "ok"
    assert record["memory_peak_bytes"] == 120_000_000


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "-Infinity", "-1", "-0.5"])
def test_a_child_number_that_is_not_finite_and_non_negative_is_refused(bad: str) -> None:
    line = _ok_line().replace("1.5", bad, 1)
    with pytest.raises(ValueError, match=r"build_s|finite|negative|constant"):
        oper.parse_child_line(line)


def test_an_ok_line_missing_a_key_is_refused() -> None:
    record = json.loads(_ok_line())
    del record["memory_peak_bytes"]
    with pytest.raises(ValueError, match="memory_peak_bytes"):
        oper.parse_child_line(json.dumps(record))


def test_a_line_that_is_not_json_is_refused() -> None:
    with pytest.raises(ValueError, match="JSON"):
        oper.parse_child_line("Traceback (most recent call last):")


def test_a_json_line_that_is_not_an_object_is_refused() -> None:
    with pytest.raises(ValueError, match="object"):
        oper.parse_child_line("[1, 2]")


def test_an_unknown_child_status_is_refused() -> None:
    with pytest.raises(ValueError, match="status"):
        oper.parse_child_line(json.dumps({"status": "great"}))


@pytest.mark.parametrize("status", [[], {}, [1], {"a": 1}, 3, None],
                         ids=["list", "object", "list-of-one", "object-of-one", "number", "null"])
def test_a_status_that_is_not_text_is_refused_like_an_unknown_one(status: object) -> None:
    with pytest.raises(ValueError, match="status"):
        oper.parse_child_line(json.dumps({"status": status}))


@pytest.mark.parametrize("stdout", ['{"status": []}', '{"status": {}}'], ids=["list", "object"])
def test_a_status_that_is_not_text_is_a_crashed_reading_and_not_a_traceback(stdout: str) -> None:
    record = _classify(stdout=stdout)
    assert record["status"] == "crashed"
    assert "status" in str(record["problem"])


def test_a_refused_line_keeps_its_reason_and_drops_every_number() -> None:
    line = json.dumps({"status": "refused", "error": "BuildError", "message": "no solid",
                       "build_s": 3.0, "memory_peak_bytes": 5})
    record = oper.parse_child_line(line)
    assert record == {"status": "refused", "error": "BuildError", "message": "no solid"}


# --- classification: a status, never a number the run did not earn -----------------------------

NUMBER_KEYS = ("build_s", "export_s", "bytes", "memory_peak_bytes", "triangles", "gzip1_bytes",
               "maxrss_bytes")


def _classify(*, timed_out: bool = False, oom_killed: bool = False, exit_code: int = 0,
              stdout: str | None = None, stderr: str = "") -> dict[str, object]:
    return oper.classify(timed_out=timed_out, oom_killed=oom_killed, exit_code=exit_code,
                         stdout=_ok_line() if stdout is None else stdout, stderr=stderr,
                         cap=oper.CAP_BYTES)


def test_a_clean_reading_is_ok_and_carries_its_numbers() -> None:
    record = _classify()
    assert record["status"] == "ok"
    assert record["memory_peak_bytes"] == 120_000_000
    assert record["build_s"] == 1.5


REFUSED_LINE = json.dumps({"status": "refused", "error": "BuildError", "message": "no solid"})


@pytest.mark.parametrize(
    ("timed_out", "oom_killed", "exit_code", "stdout", "status"),
    [
        (False, True, 137, "", "capped"),
        (False, False, 0, _ok_line(memory_peak_bytes=oper.CAP_BYTES), "capped"),
        (False, False, 0, _ok_line(memory_peak_bytes=int(oper.CAP_BYTES * 0.99)), "capped"),
        (True, False, 0, "", "killed"),
        (False, False, 139, "", "crashed"),
        (False, False, -11, "", "crashed"),
        (False, False, 1, "", "crashed"),
        (False, False, 0, "not json at all", "crashed"),
        (False, False, 0, REFUSED_LINE, "refused"),
        (False, False, 0, json.dumps({"status": "no_cgroup"}), "no_cgroup"),
    ],
    ids=["oom", "peak-at-cap", "peak-at-99-percent", "deadline", "sigsegv-exit", "signal-code",
         "plain-failure", "garbage", "refused", "no-cgroup"],
)
def test_a_reading_that_is_not_ok_carries_no_number(
        timed_out: bool, oom_killed: bool, exit_code: int, stdout: str, status: str) -> None:
    record = _classify(timed_out=timed_out, oom_killed=oom_killed, exit_code=exit_code,
                       stdout=stdout)
    assert record["status"] == status
    assert [key for key in NUMBER_KEYS if key in record] == []


def test_a_capped_reading_that_still_printed_a_line_keeps_none_of_its_figures() -> None:
    record = _classify(stdout=_ok_line(memory_peak_bytes=oper.CAP_BYTES))
    assert "build_s" not in record
    assert "memory_peak_bytes" not in record


def test_a_refused_reading_names_its_class() -> None:
    assert _classify(stdout=REFUSED_LINE)["error"] == "BuildError"


def test_the_signal_and_the_stderr_tail_of_a_crash_are_kept_as_evidence() -> None:
    record = _classify(exit_code=139, stdout="", stderr="x" * 5000)
    assert record["exit_code"] == 139
    tail = record["stderr_tail"]
    assert isinstance(tail, str)
    assert len(tail) <= 2000


# --- the summary ---------------------------------------------------------------------------------


def _reading(rep: int, status: str = "ok", *, build_s: float = 1.0, label: str = "p",
             artifact: str = "stl-preview",
             lift: dict[str, float] | None = None) -> dict[str, object]:
    record: dict[str, object] = {"type": "reading", "label": label, "artifact": artifact,
                                 "rep": rep, "status": status}
    if lift is not None:
        record["lift"] = lift
    if status == "ok":
        record.update(build_s=build_s, export_s=build_s / 10, bytes=100 * rep,
                      memory_peak_bytes=1000 * rep)
    return record


def test_five_ok_repetitions_report_their_median_and_max() -> None:
    builds = [3.0, 1.0, 2.0, 5.0, 4.0]
    rows = oper.summarize([_reading(r, build_s=b) for r, b in enumerate(builds, 1)])
    assert len(rows) == 1
    row = rows[0]
    assert row["status"] == "ok"
    median = row["median"]
    maximum = row["max"]
    assert isinstance(median, dict)
    assert isinstance(maximum, dict)
    assert median["build_s"] == statistics.median(builds)
    assert maximum["build_s"] == max(builds)
    assert maximum["memory_peak_bytes"] == 5000


def test_a_point_with_one_capped_repetition_has_a_status_and_no_median_or_max() -> None:
    readings = [_reading(r) for r in range(1, 5)] + [_reading(5, "capped")]
    row = oper.summarize(readings)[0]
    assert row["status"] == "capped"
    assert row["median"] is None
    assert row["max"] is None
    assert row["counts"] == {"ok": 4, "capped": 1}


def test_a_point_with_two_different_failures_is_mixed() -> None:
    readings = [_reading(1, "capped"), _reading(2, "killed"), _reading(3)]
    assert oper.summarize(readings)[0]["status"] == "mixed"


def test_no_readings_summarize_to_no_rows() -> None:
    assert oper.summarize([]) == []


def test_points_are_summarized_separately_and_in_first_seen_order() -> None:
    readings = [_reading(1, label="b"), _reading(1, label="a"), _reading(2, label="b")]
    assert [(r["label"], r["n"]) for r in oper.summarize(readings)] == [("b", 2), ("a", 1)]


def test_a_lifted_reading_keeps_its_own_row_and_cannot_supply_a_bound() -> None:
    """Lifted and ordinary readings that share a label and artifact are two points: merging them
    printed one numeric `ok` row for a part nobody can request."""
    plain = [_reading(r, build_s=1.0) for r in range(1, 6)]
    lifted = [_reading(r, build_s=9.0, lift={"max_mm": 1e6}) for r in range(1, 6)]
    rows = oper.summarize(plain + lifted)
    assert [(r["lift"], r["n"], r["status"]) for r in rows] == [
        (None, 5, "ok"), ({"max_mm": 1e6}, 5, "ok")]
    assert rows[0]["max"] is not None
    assert rows[1]["median"] is None
    assert rows[1]["max"] is None


def test_two_lifts_of_one_label_are_two_rows() -> None:
    readings = [_reading(1, lift={"max_turns": 260}), _reading(1, lift={"max_turns": 270})]
    assert [r["lift"] for r in oper.summarize(readings)] == [
        {"max_turns": 260}, {"max_turns": 270}]


def test_a_lifted_row_names_its_lift_in_both_formats() -> None:
    readings = [_reading(1, lift={"max_mm": 1e6})]
    rows = oper.summarize(readings)
    assert '"max_mm": 1000000.0' in oper.format_rows(rows)
    assert '"max_mm": 1000000.0' in oper.markdown_report([], readings, rows)


# --- the CLI -----------------------------------------------------------------------------------


def test_summarizing_a_file_with_no_readings_says_so_and_exits_1(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "empty.jsonl"
    path.write_text(json.dumps({"type": "header", "nproc": 4}) + "\n")
    assert oper.main(["summarize", str(path)]) == 1
    captured = capsys.readouterr()
    assert "no readings" in captured.err
    assert captured.out == ""


def test_summarizing_readings_prints_a_row_per_point(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "one.jsonl"
    lines = [json.dumps({"type": "header", "nproc": 4})]
    lines += [json.dumps(_reading(r)) for r in range(1, 6)]
    path.write_text("\n".join(lines) + "\n")
    assert oper.main(["summarize", str(path)]) == 0
    assert "stl-preview" in capsys.readouterr().out


def test_params_parse_as_numbers_and_booleans() -> None:
    assert oper.parse_params("d=6 pitch=1.25 left_hand=true") == {
        "d": 6.0, "pitch": 1.25, "left_hand": True}
    assert oper.parse_params("") == {}


@pytest.mark.parametrize("text", ["d=abc", "d", "d=nan", "d=inf", "=3"])
def test_an_unparseable_param_pair_is_refused_naming_it(text: str) -> None:
    with pytest.raises(ValueError, match=text.split()[0]):
        oper.parse_params(text)


def test_the_point_command_refuses_a_bad_param_before_touching_docker(
        capsys: pytest.CaptureFixture[str]) -> None:
    code = oper.main(["point", "--kind", "bolt", "--params", "d=abc", "--artifact", "stl-preview",
                      "--image", "screw:none", "--reps", "1", "--out", "-"])
    assert code == 2
    assert "d=abc" in capsys.readouterr().err


# --- the host facts ------------------------------------------------------------------------------

CPUINFO = ("processor\t: 0\nvendor_id\t: GenuineIntel\n"
           "model name\t: AMD EPYC 7763 64-Core Processor\ncpu MHz\t\t: 2445.4\n"
           "processor\t: 1\nmodel name\t: AMD EPYC 7763 64-Core Processor\n")


def test_the_cpu_model_is_the_first_model_name_line() -> None:
    assert bench.cpu_model(CPUINFO) == "AMD EPYC 7763 64-Core Processor"


def test_the_cpu_model_is_none_when_the_line_is_absent() -> None:
    assert bench.cpu_model("processor\t: 0\nBogoMIPS\t: 48.00\n") is None
    assert bench.cpu_model("") is None


def test_host_facts_carry_the_d01_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_RUN_ID", "123")
    monkeypatch.setenv("GITHUB_JOB", "measure")
    monkeypatch.setenv("GITHUB_SHA", "abc")
    facts = bench.host_facts()
    for key in ("nproc", "mem_total_bytes", "cpu_model", "kernel", "machine"):
        assert key in facts
    assert facts["GITHUB_RUN_ID"] == "123"
    assert facts["GITHUB_JOB"] == "measure"
    assert facts["GITHUB_SHA"] == "abc"


def test_host_facts_leave_out_github_ids_that_are_not_set(
        monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("GITHUB_RUN_ID", "GITHUB_JOB", "GITHUB_SHA"):
        monkeypatch.delenv(name, raising=False)
    assert not [key for key in bench.host_facts() if key.startswith("GITHUB_")]


def test_every_report_names_the_cpu_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bench, "cpu_model", lambda text=None: "Test CPU 9000")
    assert "Test CPU 9000" in bench.machine_facts()


# --- the container argv --------------------------------------------------------------------------


def test_a_reading_runs_in_a_capped_container_that_is_not_auto_removed() -> None:
    argv = oper.reading_argv("screw-oper-1-1", "screw:ci", REPO_ROOT, '{"kind": "bolt"}', 1000)
    assert "--rm" not in argv  # the parent inspects OOMKilled, then removes it itself
    assert "--memory=1000b" in argv
    assert "--memory-swap=1000b" in argv
    assert not [a for a in argv if a.startswith("--platform")]
    assert argv[-3:-1] == ["-m", "bench.oper_child"]
    assert argv[-1] == '{"kind": "bolt"}'
    assert f"{REPO_ROOT}/bench:/probe/bench:ro" in argv


# --- the child, end to end (one real kernel build) -----------------------------------------------


def test_the_child_prints_exactly_one_line_with_a_status_and_no_number_it_could_not_read(
        capsys: pytest.CaptureFixture[str]) -> None:
    point = json.dumps({"kind": "bolt", "params": {"d": 4.0, "length": 8.0, "thread_length": 8.0},
                        "artifact": "stl-preview"})
    assert oper_child.main([point]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    record = oper.parse_child_line(lines[0])
    # Outside a container with a cgroup (a laptop) the peak is unreadable: a status, no figure.
    assert record["status"] in {"ok", "no_cgroup"}
    if record["status"] == "ok":
        assert isinstance(record["memory_peak_bytes"], int)
        assert isinstance(record["bytes"], int)
        assert isinstance(record["triangles"], int)
    else:
        assert "memory_peak_bytes" not in record
        assert "build_s" not in record


def test_the_peak_is_read_after_the_gzip_so_a_gzip_past_the_cap_is_capped(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """The gzip's memory counts: a peak read before it kept `ok` and numbers for a container the
    compression pushed past 99 % of its cap without an OOM kill."""
    import gzip

    from screw import solid

    peak = {"bytes": 1_000_000}
    real_compress = gzip.compress

    def compress(data: bytes, level: int) -> bytes:
        peak["bytes"] = oper.CAP_BYTES  # the gzip is what takes the container to its cap
        return real_compress(data, level)

    monkeypatch.setattr(solid, "build", lambda p: None)
    monkeypatch.setattr(solid, "export", lambda *_: bytes(84))
    monkeypatch.setattr(gzip, "compress", compress)
    monkeypatch.setattr(oper_child, "read_peak", lambda: peak["bytes"])
    monkeypatch.setattr(oper_child, "oom_kills", lambda: 0)
    point = {"kind": "bolt", "params": {}, "artifact": "stl-preview"}
    assert oper_child.main([json.dumps(point)]) == 0
    line = capsys.readouterr().out.strip()
    assert oper.parse_child_line(line)["memory_peak_bytes"] == oper.CAP_BYTES
    record = oper.classify(timed_out=False, oom_killed=False, exit_code=0, stdout=line, stderr="",
                           cap=oper.CAP_BYTES)
    assert record["status"] == "capped"
    assert [key for key in NUMBER_KEYS if key in record] == []


def test_a_kernel_refusal_is_a_refused_line_with_its_class(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    from screw import solid
    from screw.build_errors import BuildError

    def refuse(*_: object, **__: object) -> bytes:
        raise BuildError("no solid for these parameters")

    monkeypatch.setattr(solid, "export", refuse)
    point = json.dumps({"kind": "bolt", "params": {}, "artifact": "step"})
    assert oper_child.main([point]) == 0
    record = oper.parse_child_line(capsys.readouterr().out.strip())
    assert (record["status"], record["error"], record["message"]) == (
        "refused", "BuildError", "no solid for these parameters")
    assert "build_s" not in record


@pytest.mark.parametrize("argv", [[], ["{not json"], ['{"kind": "washer", "params": {}, '
                                                      '"artifact": "step"}'],
                                  ['{"kind": "bolt", "params": {}, "artifact": "obj"}'],
                                  ['{"kind": "bolt", "params": {"d": -1}, "artifact": "step"}']],
                         ids=["no-arg", "bad-json", "unknown-kind", "unknown-artifact",
                              "invalid-params"])
def test_a_point_the_child_cannot_read_is_an_exit_2_with_no_line(
        argv: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    assert oper_child.main(argv) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err != ""


# --- the parent runs on a bare interpreter --------------------------------------------------------


def test_importing_the_parent_loads_no_screw_module() -> None:
    code = (f"import sys; sys.path.insert(0, {str(REPO_ROOT)!r}); import bench.oper; "
            "print(sorted(m for m in sys.modules if m == 'screw' or m.startswith('screw.')))")
    out = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True,
                         check=True).stdout.strip()
    assert out == "[]"


# --- the point files -----------------------------------------------------------------------------

POINTS_DIR = REPO_ROOT / "bench" / "points"


def _write_set(directory: Path, /, **over: object) -> Path:
    spec: dict[str, object] = {
        "set": "mini", "rule": "07-SWEEP-PROTOCOL.md R2", "reps": 2, "shards": 2,
        "deadline_s": 60,
        "points": [{"label": f"p{i}", "kind": "bolt", "params": {}, "artifact": "step"}
                   for i in range(5)]}
    spec.update(over)
    path = directory / "mini.json"
    path.write_text(json.dumps(spec))
    return path


def test_the_tracer_set_is_one_default_bolt_preview_with_five_repetitions() -> None:
    spec = oper.load_set("tracer")
    assert (spec.reps, spec.shards, spec.deadline_s) == (5, 1, 600)
    assert [(p.label, p.kind, dict(p.params), p.artifact) for p in spec.points] == [
        ("default-bolt", "bolt", {}, "stl-preview")]


def test_the_tracer_file_names_the_protocol_rule_it_runs_under() -> None:
    raw = json.loads((POINTS_DIR / "tracer.json").read_text())
    assert raw["set"] == "tracer"
    assert raw["rule"] == "07-SWEEP-PROTOCOL.md R2"


@pytest.mark.parametrize("name", ["../x", "Tracer", "a/b", "", "tracer.json", "t racer", "a_b"])
def test_a_set_name_outside_the_rule_is_refused_naming_it(name: str, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=re.escape(repr(name))):
        oper.load_set(name, tmp_path)


def test_a_set_with_no_file_is_refused_naming_it(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="'absent'"):
        oper.load_set("absent", tmp_path)


@pytest.mark.parametrize(
    "over",
    [{"reps": 0}, {"reps": 2.5}, {"reps": True}, {"shards": 0}, {"deadline_s": 0},
     {"deadline_s": "60"}, {"points": []}, {"rule": 3}, {"set": "other"}, {"extra": 1},
     {"points": [{"label": "a", "kind": "bolt", "params": {}, "artifact": "obj"}]},
     {"points": [{"label": "a", "kind": "bolt", "params": {"d": "6"}, "artifact": "step"}]},
     {"points": [{"label": "a", "kind": "bolt", "artifact": "step"}]},
     {"points": [{"label": "a", "kind": "bolt", "params": {}, "artifact": "step", "x": 1}]},
     {"points": [{"label": "a", "kind": "bolt", "params": {}, "artifact": "step"},
                 {"label": "a", "kind": "bolt", "params": {}, "artifact": "step"}]}],
    ids=["reps-zero", "reps-float", "reps-bool", "shards-zero", "deadline-zero", "deadline-text",
         "no-points", "rule-not-text", "set-name-differs", "extra-key", "bad-artifact",
         "text-param", "missing-params", "extra-point-key", "duplicate-label"],
)
def test_a_point_file_that_breaks_the_schema_is_refused(over: dict[str, object],
                                                        tmp_path: Path) -> None:
    _write_set(tmp_path, **over)
    with pytest.raises(ValueError, match="mini"):
        oper.load_set("mini", tmp_path)


def test_a_point_file_missing_a_key_is_refused(tmp_path: Path) -> None:
    path = _write_set(tmp_path)
    raw = json.loads(path.read_text())
    del raw["rule"]
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="mini"):
        oper.load_set("mini", tmp_path)


def test_points_go_to_shards_round_robin_in_file_order(tmp_path: Path) -> None:
    _write_set(tmp_path)
    spec = oper.load_set("mini", tmp_path)
    assert [p.label for p in oper.shard_points(spec, 1)] == ["p0", "p2", "p4"]
    assert [p.label for p in oper.shard_points(spec, 2)] == ["p1", "p3"]


def test_a_shard_past_the_points_is_empty(tmp_path: Path) -> None:
    _write_set(tmp_path, shards=7)
    assert oper.shard_points(oper.load_set("mini", tmp_path), 7) == []


def test_shard_sizes_cut_consecutive_slices_in_file_order(tmp_path: Path) -> None:
    _write_set(tmp_path, shards=3, shard_sizes=[1, 3, 1])
    spec = oper.load_set("mini", tmp_path)
    assert spec.shard_sizes == (1, 3, 1)
    assert [[p.label for p in oper.shard_points(spec, n)] for n in (1, 2, 3, 4)] == [
        ["p0"], ["p1", "p2", "p3"], ["p4"], []]


def test_a_set_without_shard_sizes_keeps_the_round_robin_split(tmp_path: Path) -> None:
    _write_set(tmp_path)
    assert oper.load_set("mini", tmp_path).shard_sizes is None


@pytest.mark.parametrize(
    "sizes",
    [[2, 2], [3, 3, 3], [5, 0, 0], [2.5, 2.5, 0], [True, 2, 2], ["2", 2, 1], "2,2,1", 5],
    ids=["too-few", "wrong-sum", "zero-size", "float", "bool", "text-entry", "text", "number"],
)
def test_shard_sizes_that_are_not_whole_numbers_summing_to_the_points_are_refused(
        sizes: object, tmp_path: Path) -> None:
    _write_set(tmp_path, shards=3, shard_sizes=sizes)
    with pytest.raises(ValueError, match=r"mini.*shard_sizes"):
        oper.load_set("mini", tmp_path)


def test_sources_are_a_list_of_text(tmp_path: Path) -> None:
    _write_set(tmp_path, sources=["walls=bench/results/phase-07/walls-1"])
    assert oper.load_set("mini", tmp_path).sources == ("walls=bench/results/phase-07/walls-1",)
    _write_set(tmp_path, sources=[3])
    with pytest.raises(ValueError, match=r"mini.*sources"):
        oper.load_set("mini", tmp_path)


_ENVELOPE = {"bolt": {"stl-preview": {"bytes": 2.0, "seconds": 0.0, "peak": 1.5}}}


def test_an_envelope_header_is_kind_artifact_target_to_an_e(tmp_path: Path) -> None:
    _write_set(tmp_path, envelope=_ENVELOPE)
    assert len(oper.load_set("mini", tmp_path).points) == 5


@pytest.mark.parametrize(
    "envelope",
    [{}, [], {"bolt": {}}, {"bolt": {"stl-coarse": {"bytes": 1, "seconds": 1, "peak": 1}}},
     {"bolt": {"step": {"bytes": 1, "seconds": 1}}},
     {"bolt": {"step": {"bytes": 1, "seconds": 1, "peak": 1, "wall": 1}}},
     {"bolt": {"step": {"bytes": -0.5, "seconds": 1, "peak": 1}}},
     {"bolt": {"step": {"bytes": True, "seconds": 1, "peak": 1}}},
     {"bolt": {"step": {"bytes": "1", "seconds": 1, "peak": 1}}},
     {"": {"step": {"bytes": 1, "seconds": 1, "peak": 1}}}, 2.0],
    ids=["empty", "list", "no-artifact", "bad-artifact", "missing-target", "extra-target",
         "negative", "bool", "text", "empty-kind", "number"],
)
def test_an_envelope_header_of_any_other_shape_is_refused(envelope: object,
                                                          tmp_path: Path) -> None:
    _write_set(tmp_path, envelope=envelope)
    with pytest.raises(ValueError, match=r"mini.*envelope"):
        oper.load_set("mini", tmp_path)


# --- the matrix ----------------------------------------------------------------------------------


def test_the_tracer_matrix_is_five_repetitions_of_one_shard(
        capsys: pytest.CaptureFixture[str]) -> None:
    assert oper.main(["matrix", "--set", "tracer"]) == 0
    out = capsys.readouterr().out
    assert out.count("\n") == 1
    assert out.startswith("matrix=")
    assert json.loads(out.removeprefix("matrix=")) == {
        "include": [{"shard": 1, "rep": rep} for rep in range(1, 6)]}


@pytest.mark.parametrize("name", ["../x", "Tracer", "no-such-set"])
def test_the_matrix_refuses_a_bad_set_name_with_exit_2_naming_it(
        name: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert oper.main(["matrix", "--set", name]) == 2
    captured = capsys.readouterr()
    assert repr(name) in captured.err
    assert captured.out == ""


# --- the run -------------------------------------------------------------------------------------


def _stub_docker(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, int]]:
    taken: list[tuple[str, int]] = []

    def fake_reading(point: oper.Point, rep: int, image: str, cap: int, deadline_s: float,
                     versions: Mapping[str, str] | None = None) -> dict[str, object]:
        taken.append((point.label, rep))
        return {"type": "reading", "label": point.label, "artifact": point.artifact, "rep": rep,
                "status": "ok", "image": image, "cap": cap, "deadline_s": deadline_s}

    monkeypatch.setattr(oper, "run_reading", fake_reading)
    monkeypatch.setattr(oper, "_image_versions", lambda image: {"cadquery": "2.8.0"})
    monkeypatch.setattr(oper, "header", lambda image, versions: {"type": "header", "image": image})
    return taken


def test_a_shard_measures_its_points_once_each_with_the_given_rep(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sets = tmp_path / "sets"
    sets.mkdir()
    _write_set(sets, reps=5)
    monkeypatch.setattr(oper, "POINTS_DIR", sets)
    taken = _stub_docker(monkeypatch)
    out = tmp_path / "out.jsonl"
    assert oper.main(["run", "--set", "mini", "--shard", "1", "--rep", "3", "--image", "screw:x",
                      "--out", str(out)]) == 0
    assert taken == [("p0", 3), ("p2", 3), ("p4", 3)]
    records = [json.loads(line) for line in out.read_text().splitlines()]
    assert [r["type"] for r in records] == ["header", "reading", "reading", "reading"]
    assert records[1]["cap"] == oper.CAP_BYTES
    assert records[1]["deadline_s"] == 60


def test_two_runs_of_one_file_write_the_same_order(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sets = tmp_path / "sets"
    sets.mkdir()
    _write_set(sets)
    monkeypatch.setattr(oper, "POINTS_DIR", sets)
    _stub_docker(monkeypatch)
    texts = []
    for run in ("a", "b"):
        out = tmp_path / f"{run}.jsonl"
        assert oper.main(["run", "--set", "mini", "--shard", "2", "--rep", "1", "--image", "i",
                          "--out", str(out)]) == 0
        texts.append(out.read_text())
    assert texts[0] == texts[1]


def test_a_shard_with_no_points_writes_the_header_and_succeeds(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sets = tmp_path / "sets"
    sets.mkdir()
    _write_set(sets, shards=7)
    monkeypatch.setattr(oper, "POINTS_DIR", sets)
    taken = _stub_docker(monkeypatch)
    out = tmp_path / "out.jsonl"
    assert oper.main(["run", "--set", "mini", "--shard", "7", "--rep", "1", "--image", "i",
                      "--out", str(out)]) == 0
    assert taken == []
    assert [json.loads(line)["type"] for line in out.read_text().splitlines()] == ["header"]


@pytest.mark.parametrize(("shard", "rep"), [("0", "1"), ("3", "1"), ("1", "0"), ("1", "3")])
def test_a_shard_or_rep_outside_the_set_is_refused_with_exit_2(
        shard: str, rep: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    sets = tmp_path / "sets"
    sets.mkdir()
    _write_set(sets)  # 2 shards, 2 reps
    monkeypatch.setattr(oper, "POINTS_DIR", sets)
    taken = _stub_docker(monkeypatch)
    assert oper.main(["run", "--set", "mini", "--shard", shard, "--rep", rep, "--image", "i",
                      "--out", str(tmp_path / "o.jsonl")]) == 2
    assert taken == []
    assert "mini" in capsys.readouterr().err


# --- the per-run markdown ------------------------------------------------------------------------


def test_the_markdown_summary_lists_host_facts_status_counts_and_one_row_per_point(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    first = tmp_path / "a.jsonl"
    second = tmp_path / "b.jsonl"
    header = {"type": "header", "nproc": 4, "cpu_model": "AMD EPYC 7763", "kernel": "6.8.0"}
    first.write_text("\n".join([json.dumps(header)]
                               + [json.dumps(_reading(r)) for r in (1, 2)]) + "\n")
    other = {**header, "cpu_model": "Intel Xeon 8370C"}
    second.write_text("\n".join(
        [json.dumps(other), json.dumps(_reading(3)), json.dumps(_reading(4, "capped"))]) + "\n")
    assert oper.main(["summarize", str(first), str(second), "--markdown"]) == 0
    out = capsys.readouterr().out
    assert "| nproc | 4 |" in out
    assert "AMD EPYC 7763" in out
    assert "Intel Xeon 8370C" in out  # GitHub mixes CPU generations: both are shown
    assert "ok: 3" in out
    assert "capped: 1" in out
    assert out.count("| p |") == 1
    assert "capped" in out


def test_the_markdown_summary_of_no_readings_is_the_same_refusal(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "h.jsonl"
    path.write_text(json.dumps({"type": "header", "nproc": 4}) + "\n")
    assert oper.main(["summarize", str(path), "--markdown"]) == 1
    captured = capsys.readouterr()
    assert "no readings" in captured.err
    assert captured.out == ""


# --- the Runs II points (07-06): contention, read by bench.oper_bound -----------------------------

MEMBER_P = {"label": "default-bolt", "kind": "bolt", "params": {}, "slot": 0}
MEMBER_NUT = {"label": "default-nut", "kind": "nut", "params": {}, "slot": 1}


def _contention_point(**over: object) -> dict[str, object]:
    point: dict[str, object] = {"label": "c2", "kind": "contention", "artifact": "stl-preview",
                                "workers": 2, "points": [MEMBER_P, MEMBER_NUT]}
    point.update(over)
    return point


def test_a_contention_point_reaches_the_bound_child_as_it_stands_in_the_file(
        tmp_path: Path) -> None:
    _write_set(tmp_path, points=[_contention_point()])
    (point,) = oper.load_set("mini", tmp_path).points
    assert (point.label, point.kind, point.artifact) == ("c2", "contention", "stl-preview")
    assert json.loads(point.as_json()) == {"kind": "contention", "artifact": "stl-preview",
                                           "workers": 2, "points": [MEMBER_P, MEMBER_NUT]}


def test_one_worker_takes_the_bound_point_alone(tmp_path: Path) -> None:
    _write_set(tmp_path, points=[_contention_point(workers=1, points=[MEMBER_P])])
    (point,) = oper.load_set("mini", tmp_path).points
    assert point.body == {"workers": 1, "points": [MEMBER_P]}


@pytest.mark.parametrize(
    "point",
    [_contention_point(workers=0, points=[]), _contention_point(workers=4),
     _contention_point(workers=2.0), _contention_point(workers=True),
     _contention_point(points=[MEMBER_P]),
     _contention_point(points=[MEMBER_P, {**MEMBER_NUT, "slot": 0}]),
     _contention_point(points=[MEMBER_P, {**MEMBER_NUT, "slot": 2}]),
     _contention_point(points=[MEMBER_P, {**MEMBER_NUT, "slot": True}]),
     _contention_point(points=[MEMBER_P, {**MEMBER_NUT, "label": "default-bolt"}]),
     _contention_point(points=[MEMBER_P, {**MEMBER_NUT, "params": {"d": "6"}}]),
     _contention_point(points=[MEMBER_P, {**MEMBER_NUT, "kind": "contention"}]),
     _contention_point(points=[MEMBER_P, {k: v for k, v in MEMBER_NUT.items() if k != "slot"}]),
     _contention_point(points=[MEMBER_P, {**MEMBER_NUT, "artifact": "step"}]),
     _contention_point(artifact="obj"), _contention_point(label=""),
     _contention_point(params={}), _contention_point(points="P"),
     {k: v for k, v in _contention_point().items() if k != "workers"},
     {"label": "m", "kind": "memory", "artifact": "stl-preview", "part": {"kind": "bolt",
                                                                          "params": {}},
      "cache": 4}],
    ids=["no-workers", "four-workers", "float-workers", "bool-workers", "fewer-points",
         "two-on-one-slot", "slot-past-n", "bool-slot", "duplicate-label", "text-param",
         "harness-kind", "missing-slot", "member-artifact", "bad-artifact", "empty-label",
         "extra-key", "points-not-a-list", "missing-workers", "removed-memory-kind"])
def test_the_matrix_refuses_a_bad_runs_ii_point_with_exit_2(
        point: dict[str, object], tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _write_set(tmp_path, points=[point])
    monkeypatch.setattr(oper, "POINTS_DIR", tmp_path)
    assert oper.main(["matrix", "--set", "mini"]) == 2
    captured = capsys.readouterr()
    assert "mini" in captured.err
    assert captured.out == ""


def _bound_line(**over: object) -> str:
    line: dict[str, object] = {
        "status": "ok", "build_s": 1.5, "export_s": 0.25, "bytes": 1000, "gzip1_bytes": 400,
        "memory_peak_bytes": 120_000_000, "oom_kills": 0,
        "builds": [{"label": "default-bolt", "slot": 0, "status": "ok", "build_s": 1.5,
                    "export_s": 0.25, "bytes": 1000, "gzip1_bytes": 400}],
        "cadquery": "2.8.0", "cadquery_ocp": "7.9.3.1.1"}
    line.update(over)
    return json.dumps(line)


def _classify_bound(stdout: str) -> dict[str, object]:
    return oper.classify(timed_out=False, oom_killed=False, exit_code=0, stdout=stdout,
                         stderr="", cap=oper.CAP_BYTES, bound=True)


def test_a_clean_contention_line_is_ok_with_every_build() -> None:
    record = _classify_bound(_bound_line())
    assert record["status"] == "ok"
    assert record["build_s"] == 1.5
    assert isinstance(record["builds"], list)


@pytest.mark.parametrize(
    ("line", "status"),
    [(_bound_line(status="refused", error="BuildError", message="default-nut: no",
                  memory_peak_bytes=oper.CAP_BYTES), "capped"),
     (_bound_line(status="crashed", error="ArithmeticError", message="x", oom_kills=1),
      "capped"),
     (_bound_line(status="refused", error="BuildError", message="default-nut: no"), "refused"),
     (json.dumps({"status": "crashed", "error": "SlotMismatch", "message": "slot 1, slot 0"}),
      "crashed"),
     (json.dumps({"status": "killed", "message": "1 of 2 builds"}), "killed"),
     (json.dumps({"status": "no_cgroup"}), "no_cgroup"),
     (_bound_line(builds=[{"label": "p", "build_s": -1.0}]), "crashed"),
     (_bound_line(builds="none"), "crashed")],
    ids=["refused-at-cap", "crashed-with-oom-kill", "refused", "slot-mismatch", "killed",
         "no-cgroup", "negative-build-figure", "builds-not-a-list"])
def test_a_contention_reading_that_is_not_ok_carries_no_number(line: str, status: str) -> None:
    record = _classify_bound(line)
    assert record["status"] == status
    assert [key for key in (*NUMBER_KEYS, "builds") if key in record] == []


def test_a_part_child_may_not_report_killed_or_crashed_itself() -> None:
    for status in ("killed", "crashed"):
        record = _classify(stdout=json.dumps({"status": status}))
        assert (record["status"], "status" in str(record["problem"])) == ("crashed", True)


def test_a_contention_reading_runs_the_bound_child(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_set(tmp_path, points=[_contention_point()])
    (point,) = oper.load_set("mini", tmp_path).points
    ran: list[tuple[list[str], float | None]] = []

    def fake_run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        timeout = kwargs.get("timeout")
        ran.append((argv, timeout if isinstance(timeout, float | int) else None))
        return subprocess.CompletedProcess(argv, 0, _bound_line(), "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(oper, "_docker", lambda *args, timeout=None: None)
    monkeypatch.setattr(oper, "_inspect_exit", lambda name: (False, 0))
    record = oper.run_reading(point, 1, "screw:ci", oper.CAP_BYTES, 600)
    ((argv, timeout),) = ran
    assert argv[-3:-1] == ["-m", "bench.oper_bound"]
    assert json.loads(argv[-1])["points"] == [MEMBER_P, MEMBER_NUT]
    assert timeout == 600
    assert (record["status"], record["workers"], record["points"]) == (
        "ok", 2, [MEMBER_P, MEMBER_NUT])


PART = {"kind": "bolt", "params": {}}


def _drift_point(**over: object) -> dict[str, object]:
    point: dict[str, object] = {"label": "d3", "kind": "drift", "artifact": "stl-preview",
                                "part": PART, "k": 20, "deadline_s": 1200}
    point.update(over)
    return point


def _arenas_point(**over: object) -> dict[str, object]:
    point: dict[str, object] = {"label": "a-on", "kind": "arenas", "artifact": "step",
                                "part": PART, "trim": True}
    point.update(over)
    return point


def test_drift_and_arenas_points_reach_the_bound_child_as_they_stand(tmp_path: Path) -> None:
    _write_set(tmp_path, points=[_drift_point(), _arenas_point(), _arenas_point(
        label="a-off", trim=False)])
    drift, on, off = oper.load_set("mini", tmp_path).points
    assert drift.deadline_s == 1200
    assert json.loads(drift.as_json()) == {"kind": "drift", "artifact": "stl-preview",
                                           "part": PART, "k": 20, "deadline_s": 1200}
    assert (on.deadline_s, json.loads(on.as_json())) == (
        None, {"kind": "arenas", "artifact": "step", "part": PART, "trim": True})
    assert off.body == {"part": PART, "trim": False}


@pytest.mark.parametrize(
    "point",
    [_drift_point(k=1), _drift_point(k=2.0), _drift_point(k=True), _drift_point(deadline_s=0),
     _drift_point(deadline_s="600"), _drift_point(deadline_s=True),
     {k: v for k, v in _drift_point().items() if k != "deadline_s"},
     _drift_point(part={"kind": "bolt", "params": {}, "lift": {"max_mm": 1e6}}),
     _drift_point(part={"kind": "probe", "params": {}}),
     _drift_point(part={"kind": "bolt", "params": {"d": "6"}}), _drift_point(part="bolt"),
     _drift_point(trim=True), _arenas_point(trim="yes"), _arenas_point(trim=1),
     {k: v for k, v in _arenas_point().items() if k != "trim"}, _arenas_point(k=2),
     _arenas_point(artifact="obj"), _arenas_point(label=3)],
    ids=["one-build", "float-k", "bool-k", "zero-deadline", "text-deadline", "bool-deadline",
         "missing-deadline", "part-extra-key", "part-probe", "part-text-param", "part-not-object",
         "drift-extra-key", "trim-text", "trim-number", "missing-trim", "arenas-extra-key",
         "bad-artifact", "label-not-text"])
def test_the_matrix_refuses_a_bad_drift_or_arenas_point_with_exit_2(
        point: dict[str, object], tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _write_set(tmp_path, points=[point])
    monkeypatch.setattr(oper, "POINTS_DIR", tmp_path)
    assert oper.main(["matrix", "--set", "mini"]) == 2
    assert "mini" in capsys.readouterr().err


def test_a_drift_reading_runs_under_its_own_deadline(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_set(tmp_path, points=[_drift_point()])
    (point,) = oper.load_set("mini", tmp_path).points
    timeouts: list[object] = []

    def fake_run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        timeouts.append(kwargs.get("timeout"))
        return subprocess.CompletedProcess(argv, 0, _bound_line(peaks=[5, 6], builds=[]), "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(oper, "_docker", lambda *args, timeout=None: None)
    monkeypatch.setattr(oper, "_inspect_exit", lambda name: (False, 0))
    record = oper.run_reading(point, 1, "screw:ci", oper.CAP_BYTES, 600)
    assert timeouts == [1200.0]
    assert (record["status"], record["k"], record["peaks"]) == ("ok", 20, [5, 6])


@pytest.mark.parametrize(
    "line",
    [_bound_line(peaks=[1, -2]), _bound_line(peaks=[1.5]), _bound_line(peaks=[True]),
     _bound_line(peaks="many"), _bound_line(memory_current_bytes=1.5),
     _bound_line(vm_rss_bytes=True)],
    ids=["negative-peak", "float-peak", "bool-peak", "peaks-not-a-list", "float-current",
         "bool-rss"])
def test_a_drift_or_arena_line_with_a_figure_that_cannot_be_true_is_crashed(line: str) -> None:
    record = _classify_bound(line)
    assert record["status"] == "crashed"
    assert [key for key in (*NUMBER_KEYS, "peaks", "builds") if key in record] == []


def test_an_arena_line_keeps_both_measures_of_retained_memory() -> None:
    record = _classify_bound(_bound_line(memory_current_bytes=7, vm_rss_bytes=5, builds=[]))
    assert (record["status"], record["memory_current_bytes"], record["vm_rss_bytes"]) == (
        "ok", 7, 5)


# --- the workflow's trust surface (T-3-14, T-07-02) ----------------------------------------------

WORKFLOW_YML = REPO_ROOT / ".github" / "workflows" / "operability.yml"


def _run_values(text: str) -> list[str]:
    """Every `run:` value of a workflow, inline or block scalar, as one string each."""
    lines = text.splitlines()
    values: list[str] = []
    for i, line in enumerate(lines):
        match = re.match(r"^(\s*)(?:-\s+)?run:\s*(.*)$", line)
        if not match:
            continue
        indent = len(match.group(1))
        value = [match.group(2)]
        for follow in lines[i + 1:]:
            if follow.strip() and len(follow) - len(follow.lstrip()) <= indent:
                break
            value.append(follow)
        values.append("\n".join(value))
    return values


def test_the_workflow_starts_only_on_a_dispatch() -> None:
    text = WORKFLOW_YML.read_text()
    assert re.search(r"^on:\n  workflow_dispatch:", text, re.MULTILINE)
    assert not re.search(r"^\s*(pull_request|pull_request_target|push|schedule)\s*:", text,
                         re.MULTILINE)


def test_the_workflow_reads_the_repository_and_names_no_secret() -> None:
    text = WORKFLOW_YML.read_text()
    assert re.search(r"^permissions:\n  contents: read$", text, re.MULTILINE)
    assert "secrets." not in text


def test_the_set_input_reaches_a_script_only_through_an_env_variable() -> None:
    text = WORKFLOW_YML.read_text()
    runs = _run_values(text)
    assert runs, "no run: steps found"
    assert not [run for run in runs if "${{ inputs." in run]
    assert re.search(r"^\s+SET: \$\{\{ inputs\.set \}\}$", text, re.MULTILINE)
    assert 'python -m bench.oper matrix --set "$SET"' in text
    assert 'python -m bench.oper run --set "$SET"' in text


def test_the_workflow_builds_the_image_from_the_commit_under_test() -> None:
    text = WORKFLOW_YML.read_text()
    assert "docker/build-push-action@v6" in text
    assert re.search(r"^\s+load: true$", text, re.MULTILINE)
    assert re.search(r"^\s+tags: screw:ci$", text, re.MULTILINE)
    assert "--image screw:ci" in text


def test_the_measure_job_has_a_timeout_and_keeps_the_artifact_of_a_red_run() -> None:
    text = WORKFLOW_YML.read_text()
    assert re.search(r"^\s+timeout-minutes: \d+$", text, re.MULTILINE)
    assert "fail-fast: false" in text
    upload = text.index("actions/upload-artifact@v4")
    assert "if: always()" in text[upload - 200:upload + 200]


def test_the_matrix_job_feeds_the_measure_job() -> None:
    text = WORKFLOW_YML.read_text()
    assert "needs: plan" in text
    assert "fromJSON(needs.plan.outputs.matrix)" in text


# --- the make target -----------------------------------------------------------------------------


def test_make_lists_the_runner_harness() -> None:
    out = subprocess.run(["make", "-s", "help"], cwd=REPO_ROOT, capture_output=True, text=True,
                         check=True).stdout
    assert [line for line in out.splitlines() if line.split()[:1] == ["bench.oper"]]


# --- the probes (07-03): the walls and the controls are read through the same parent ------------

TAIL_ARGS: dict[str, float | bool] = {
    "d": 6.0, "pitch": 1.0, "turns": 3, "tail": 0.01, "left_hand": False}
NAIVE_ARGS: dict[str, float | bool] = {"d": 8.0, "pitch": 1.25, "length": 10.0}
PIPE_ARGS: dict[str, float | bool] = {"d": 6.0, "pitch": 1.0, "turns": 3, "left_hand": False}


def _probe(probe: str = "tail", args: Mapping[str, object] | None = None,
           label: str = "t") -> dict[str, object]:
    return {"label": label, "kind": "probe", "probe": probe,
            "args": dict(TAIL_ARGS if args is None else args)}


def test_a_probe_point_loads_with_its_name_and_arguments(tmp_path: Path) -> None:
    _write_set(tmp_path, points=[_probe(), _probe("naive", NAIVE_ARGS, "n"),
                                 _probe("one_pipe", PIPE_ARGS, "o")])
    points = oper.load_set("mini", tmp_path).points
    assert [(p.label, p.kind, p.artifact) for p in points] == [
        ("t", "probe", "tail"), ("n", "probe", "naive"), ("o", "probe", "one_pipe")]
    assert dict(points[0].params) == TAIL_ARGS


def test_a_probe_point_reaches_the_child_as_its_name_and_arguments(tmp_path: Path) -> None:
    _write_set(tmp_path, points=[_probe()])
    (point,) = oper.load_set("mini", tmp_path).points
    assert json.loads(point.as_json()) == {"kind": "probe", "probe": "tail", "args": TAIL_ARGS}


def _without(args: Mapping[str, object], key: str) -> dict[str, object]:
    return {k: v for k, v in args.items() if k != key}


@pytest.mark.parametrize(
    ("point", "named"),
    [(_probe("twist"), "'twist'"),
     (_probe("tail", _without(TAIL_ARGS, "turns")), "turns"),
     (_probe("naive", {**NAIVE_ARGS, "left_hand": False}), "left_hand"),
     (_probe("one_pipe", _without(PIPE_ARGS, "left_hand")), "left_hand"),
     (_probe("tail", {**TAIL_ARGS, "tail": "0.01"}), "argument 'tail'"),
     (_probe("tail", {**TAIL_ARGS, "tail": True}), "argument 'tail'"),
     (_probe("tail", {**TAIL_ARGS, "tail": 0}), "argument 'tail'"),
     (_probe("tail", {**TAIL_ARGS, "left_hand": 1}), "argument 'left_hand'"),
     ({**_probe(), "artifact": "stl-preview"}, "'t'"),
     ({"label": "t", "kind": "probe", "args": TAIL_ARGS}, "'t'")],
    ids=["unknown-probe", "missing-arg", "extra-arg", "missing-hand", "text-arg", "bool-arg",
         "zero-arg", "number-hand", "artifact-on-a-probe", "no-probe-name"])
def test_a_probe_point_that_breaks_its_schema_is_refused_naming_it(
        point: dict[str, object], named: str, tmp_path: Path) -> None:
    _write_set(tmp_path, points=[point])
    with pytest.raises(ValueError, match=re.escape(named)):
        oper.load_set("mini", tmp_path)


def test_the_matrix_refuses_a_bad_probe_with_exit_2_naming_it(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _write_set(tmp_path, points=[_probe("twist")])
    monkeypatch.setattr(oper, "POINTS_DIR", tmp_path)
    assert oper.main(["matrix", "--set", "mini"]) == 2
    assert "'twist'" in capsys.readouterr().err


def _probe_line(**over: object) -> str:
    line: dict[str, object] = {
        "status": "ok", "build_s": 0.4, "solids": 1, "valid": True, "volume_ratio": 1.00001,
        "maxrss_bytes": 90_000_000, "memory_peak_bytes": 120_000_000, "oom_kills": 0,
        "cadquery": "2.8.0", "cadquery_ocp": "7.9.3.1.1"}
    line.update(over)
    return json.dumps(line)


def test_a_probe_line_parses_when_a_probe_is_expected() -> None:
    record = oper.parse_child_line(_probe_line(), probe=True)
    assert (record["solids"], record["valid"], record["volume_ratio"]) == (1, True, 1.00001)


def test_an_inverted_solid_keeps_its_negative_volume_ratio() -> None:
    # one_pipe at 160 to 171 turns reads about -1 times the closed form with isValid() True
    # (bench/thread_spike/helical.py); the sign is the finding, so it is not a refusable number.
    record = oper.parse_child_line(_probe_line(volume_ratio=-1.0), probe=True)
    assert record["volume_ratio"] == -1.0


@pytest.mark.parametrize("over", [{"build_s": -1.0}, {"solids": -1}, {"volume_ratio": "NaN"}],
                         ids=["negative-seconds", "negative-count", "nan-ratio"])
def test_a_probe_line_with_a_number_that_cannot_be_true_is_refused(over: dict[str, object]) -> None:
    line = _probe_line(**over).replace('"NaN"', "NaN")
    with pytest.raises(ValueError, match="child line"):
        oper.parse_child_line(line, probe=True)


@pytest.mark.parametrize("key", ["build_s", "solids", "valid", "volume_ratio",
                                 "memory_peak_bytes"])
def test_a_probe_line_missing_a_field_is_refused(key: str) -> None:
    record = json.loads(_probe_line())
    del record[key]
    with pytest.raises(ValueError, match=key):
        oper.parse_child_line(json.dumps(record), probe=True)


def test_a_part_line_is_not_a_probe_line_and_a_probe_line_is_not_a_part_line() -> None:
    with pytest.raises(ValueError, match="solids"):
        oper.parse_child_line(_ok_line(), probe=True)
    with pytest.raises(ValueError, match="export_s"):
        oper.parse_child_line(_probe_line())


def test_a_clean_probe_is_ok_and_keeps_what_it_found() -> None:
    record = oper.classify(timed_out=False, oom_killed=False, exit_code=0, stdout=_probe_line(),
                           stderr="", cap=oper.CAP_BYTES, probe=True)
    assert record["status"] == "ok"
    assert (record["solids"], record["volume_ratio"]) == (1, 1.00001)


@pytest.mark.parametrize("exit_code", [139, -11], ids=["container-exit", "signal"])
def test_a_probe_that_crashes_the_container_is_crashed_with_no_number(exit_code: int) -> None:
    # The tail walk crosses the kernel's SIGSEGV wall on purpose (D-08, T-07-07): the container
    # absorbs it, the reading says so, and the parent goes on to the next point.
    record = oper.classify(timed_out=False, oom_killed=False, exit_code=exit_code, stdout="",
                           stderr="", cap=oper.CAP_BYTES, probe=True)
    assert record["status"] == "crashed"
    assert record["exit_code"] == exit_code
    assert [k for k in (*NUMBER_KEYS, "solids", "volume_ratio", "valid") if k in record] == []


def test_a_capped_probe_that_still_printed_a_line_keeps_none_of_its_findings() -> None:
    record = oper.classify(timed_out=False, oom_killed=True, exit_code=137, stdout=_probe_line(),
                           stderr="", cap=oper.CAP_BYTES, probe=True)
    assert record == {"status": "capped"}


def _probe_reading(rep: int, status: str = "ok", *, build_s: float = 1.0) -> dict[str, object]:
    record: dict[str, object] = {"type": "reading", "label": "t", "kind": "probe",
                                 "artifact": "tail", "rep": rep, "status": status}
    if status == "ok":
        record.update(build_s=build_s, solids=1, valid=True, volume_ratio=1.0,
                      memory_peak_bytes=1000 * rep)
    return record


def test_probe_readings_report_the_median_and_max_of_what_a_probe_measures() -> None:
    readings = [_probe_reading(r, build_s=b) for r, b in enumerate([3.0, 1.0, 2.0], 1)]
    row = oper.summarize(readings, expected_reps=[1, 2, 3])[0]
    assert row["status"] == "ok"
    assert row["median"] == {"build_s": 2.0, "memory_peak_bytes": 2000}
    assert row["max"] == {"build_s": 3.0, "memory_peak_bytes": 3000}


def test_a_probe_summary_prints_in_both_formats_without_inventing_an_export(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "p.jsonl"
    lines = [json.dumps({"type": "header", "nproc": 4})]
    lines += [json.dumps(_probe_reading(r)) for r in (1, 2)] + [json.dumps(
        {**_probe_reading(3, "crashed"), "exit_code": 139})]
    path.write_text("\n".join(lines) + "\n")
    assert oper.main(["summarize", str(path), "--reps", "1,2,3"]) == 0
    assert "crashed" in capsys.readouterr().out
    ok = tmp_path / "ok.jsonl"
    ok.write_text("\n".join(lines[:3]) + "\n")
    assert oper.main(["summarize", str(ok), "--reps", "1,2"]) == 0
    assert "build_s" in capsys.readouterr().out
    assert oper.main(["summarize", str(ok), "--reps", "1,2", "--markdown"]) == 0
    row = [line for line in capsys.readouterr().out.splitlines() if line.startswith("| t |")]
    assert len(row) == 1
    assert "| - | - | - | - |" in row[0]  # no export seconds and no bytes: a dash, not a zero


@pytest.mark.parametrize(
    "argv",
    [["--kind", "probe", "--artifact", "step"], ["--kind", "probe"],
     ["--kind", "probe", "--probe", "twist"], ["--kind", "bolt"],
     ["--kind", "bolt", "--artifact", "step", "--probe", "tail"]],
    ids=["artifact-on-a-probe", "no-probe-name", "unknown-probe", "no-artifact",
         "probe-on-a-part"])
def test_the_point_command_refuses_a_misplaced_probe_or_artifact_before_touching_docker(
        argv: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    code = oper.main(["point", *argv, "--params", "d=6", "--image", "screw:none", "--reps", "1",
                      "--out", "-"])
    assert code == 2
    assert capsys.readouterr().err.startswith("oper: ")


# --- the probes, in the child (real kernel, each builds in under a second) -----------------------


def test_the_tail_probe_builds_one_valid_solid_inside_the_gate() -> None:
    from screw.calc.thread import T_GATE

    result = oper_child.run_probe({"probe": "tail", "args": TAIL_ARGS})
    assert result["status"] == "ok"
    assert (result["solids"], result["valid"]) == (1, True)
    ratio = result["volume_ratio"]
    assert isinstance(ratio, float)
    assert abs(ratio - 1) <= T_GATE
    assert isinstance(result["build_s"], float)


def _guard() -> object:
    from screw.solid import helical

    return vars(helical)["MIN_TAIL_MM"]


def test_the_tail_probe_lowers_the_builder_guard_for_the_call_and_restores_it(
        monkeypatch: pytest.MonkeyPatch) -> None:
    from screw.solid import helical

    saved = _guard()
    assert isinstance(saved, float)
    assert saved > 0
    seen: list[object] = []
    real = helical.thread

    def spy(*args: float, **kwargs: bool) -> object:
        seen.append(_guard())
        return real(*args, **kwargs)

    monkeypatch.setattr(helical, "thread", spy)
    oper_child.run_probe({"probe": "tail", "args": TAIL_ARGS})
    assert seen == [0.0]
    assert _guard() == saved


def test_the_tail_probe_restores_the_guard_when_the_build_fails(
        monkeypatch: pytest.MonkeyPatch) -> None:
    from screw.solid import helical

    saved = _guard()

    def fail(*_: object, **__: object) -> object:
        raise RuntimeError("Standard_Failure")

    monkeypatch.setattr(helical, "twist", fail)
    result = oper_child.run_probe({"probe": "tail", "args": TAIL_ARGS})
    assert _guard() == saved
    assert (result["status"], result["error"]) == ("refused", "RuntimeError")
    assert "Standard_Failure" in str(result["message"])
    assert [k for k in ("build_s", "solids", "valid", "volume_ratio") if k in result] == []


def test_the_one_pipe_control_builds_the_twist_without_a_gate() -> None:
    result = oper_child.run_probe({"probe": "one_pipe", "args": PIPE_ARGS})
    assert result["status"] == "ok"
    assert (result["solids"], result["valid"]) == (1, True)
    ratio = result["volume_ratio"]
    assert isinstance(ratio, float)
    assert abs(ratio - 1) < 1e-3


def test_the_naive_control_reports_what_it_built_or_the_kernel_error() -> None:
    # macOS arm64 gives one valid solid at about a quarter of the closed form; linux/amd64 may
    # raise `Null TopoDS_Shape` (L11 platform note). Either is a record, never an exception.
    result = oper_child.run_probe({"probe": "naive", "args": NAIVE_ARGS})
    if result["status"] == "ok":
        assert isinstance(result["solids"], int)
        assert isinstance(result["valid"], bool)
        assert isinstance(result["volume_ratio"], float)
    else:
        assert result["status"] == "refused"
        assert isinstance(result["error"], str)


def test_a_kernel_exception_in_a_control_is_a_refused_record_with_its_class_and_text(
        monkeypatch: pytest.MonkeyPatch) -> None:
    from bench.thread_spike import helical as spike

    def fail(*_: object, **__: object) -> object:
        raise ValueError("Null TopoDS_Shape")

    monkeypatch.setattr(spike, "naive_sweep_fuse", fail)
    result = oper_child.run_probe({"probe": "naive", "args": NAIVE_ARGS})
    assert result == {"status": "refused", "error": "ValueError", "message": "Null TopoDS_Shape"}


def test_a_probe_the_child_does_not_know_is_a_key_error_not_a_reading() -> None:
    with pytest.raises(KeyError, match="twist"):
        oper_child.run_probe({"probe": "twist", "args": {}})


def test_the_child_prints_one_line_for_a_probe(capsys: pytest.CaptureFixture[str]) -> None:
    point = json.dumps({"kind": "probe", "probe": "tail", "args": TAIL_ARGS})
    assert oper_child.main([point]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    record = oper.parse_child_line(lines[0], probe=True) if '"ok"' in lines[0] \
        else oper.parse_child_line(lines[0])
    # Outside a container with a cgroup (a laptop) the peak is unreadable: a status, no finding.
    assert record["status"] in {"ok", "no_cgroup"}
    if record["status"] == "no_cgroup":
        assert "volume_ratio" not in record


@pytest.mark.parametrize("argv", [['{"kind": "probe", "probe": "twist", "args": {}}'],
                                  ['{"kind": "probe", "probe": "tail"}'],
                                  ['{"kind": "probe", "args": {}}']],
                         ids=["unknown-probe", "no-args", "no-probe-name"])
def test_a_probe_the_child_cannot_read_is_an_exit_2_with_no_line(
        argv: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    assert oper_child.main(argv) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err != ""


# --- the pre-registered point sets (07-03): the generator is their only definition --------------

EXPECTED_SHAPE = {"explore": (1, 40, 600), "spread": (5, 12, 600), "walls": (1, 20, 600),
                  "controls": (1, 4, 600)}  # reps, shards, deadline_s: protocol R3 and R4
SET_NAMES = tuple(EXPECTED_SHAPE)


class _Point(TypedDict, total=False):
    """A point as the generator writes it: a part has `params` and `artifact`, a probe has
    `probe` and `args`; `preset` marks a catalogue row and `lift` a point past a cap."""

    label: str
    kind: str
    params: dict[str, float | bool]
    artifact: str
    preset: str
    lift: dict[str, float]
    probe: str
    args: dict[str, float | bool]


class _Dropped(TypedDict):
    label: str
    kind: str
    params: dict[str, float | bool]
    artifacts: list[str]
    error: str
    lift: NotRequired[dict[str, float]]


class _Doc(TypedDict):
    set: str
    rule: str
    reps: int
    shards: int
    deadline_s: int
    points: list[_Point]
    dropped: list[_Dropped]
    notes: list[str]


@functools.cache
def _generated() -> dict[str, _Doc]:
    from bench import oper_sets

    return {name: json.loads(text) for name, text in oper_sets.generate().items()}


def _parts(name: str) -> list[_Point]:
    return [p for p in _generated()[name]["points"] if p["kind"] != "probe"]


def _by_label(name: str) -> dict[str, list[_Point]]:
    labelled: dict[str, list[_Point]] = {}
    for point in _generated()[name]["points"]:
        labelled.setdefault(point["label"], []).append(point)
    return labelled


def test_the_generator_lists_the_four_sets_and_the_smoke_and_gives_the_same_text_twice() -> None:
    from bench import oper_sets

    first = oper_sets.generate()
    assert tuple(first) == (*SET_NAMES, "bound-smoke", "load-smoke")
    assert oper_sets.generate() == first


@pytest.mark.parametrize("name", SET_NAMES)
def test_each_set_carries_the_reps_shards_and_deadline_the_protocol_fixes(name: str) -> None:
    doc = _generated()[name]
    assert doc["set"] == name
    assert doc["rule"] == "07-SWEEP-PROTOCOL.md R4"
    assert (doc["reps"], doc["shards"], doc["deadline_s"]) == EXPECTED_SHAPE[name]
    assert doc["deadline_s"] == oper.DEADLINE_S


@pytest.mark.parametrize("name", SET_NAMES)
def test_the_runner_loads_every_set_the_generator_writes(name: str, tmp_path: Path) -> None:
    from bench import oper_sets

    (tmp_path / f"{name}.json").write_text(oper_sets.generate()[name])
    spec = oper.load_set(name, tmp_path)
    assert len(spec.points) == len(_generated()[name]["points"])


def test_the_committed_point_files_are_what_the_generator_writes(
        capsys: pytest.CaptureFixture[str]) -> None:
    from bench import oper_sets

    assert oper_sets.main(["--check"]) == 0
    assert "integer L/P: 201 of 294" in capsys.readouterr().out


def test_check_names_the_first_file_that_differs_and_exits_1(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    from bench import oper_sets

    for name, text in oper_sets.generate().items():
        (tmp_path / f"{name}.json").write_text(text)
    (tmp_path / "walls.json").write_text("{}\n")
    (tmp_path / "spread.json").write_text(
        (tmp_path / "spread.json").read_text().replace('"reps": 5', '"reps": 4'))
    monkeypatch.setattr(oper_sets, "POINTS_DIR", tmp_path)
    assert oper_sets.main(["--check"]) == 1
    err = capsys.readouterr().err
    assert "spread.json" in err
    assert "walls.json" not in err  # the first one only


def test_check_of_a_missing_file_is_a_difference(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    from bench import oper_sets

    monkeypatch.setattr(oper_sets, "POINTS_DIR", tmp_path)
    assert oper_sets.main(["--check"]) == 1
    assert "explore.json" in capsys.readouterr().err


def test_writing_twice_gives_byte_identical_files(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from bench import oper_sets

    monkeypatch.setattr(oper_sets, "POINTS_DIR", tmp_path)
    assert oper_sets.main([]) == 0
    first = {p.name: p.read_bytes() for p in tmp_path.glob("*.json")}
    assert sorted(first) == sorted(
        f"{name}.json" for name in (*SET_NAMES, "bound-smoke", "load-smoke"))
    assert oper_sets.main([]) == 0
    assert {p.name: p.read_bytes() for p in tmp_path.glob("*.json")} == first
    assert all(data.endswith(b"\n") and not data.endswith(b"\n\n") for data in first.values())


@pytest.mark.parametrize("name", SET_NAMES)
def test_a_point_file_stays_small_enough_to_review(name: str) -> None:
    from bench import oper_sets

    assert len(oper_sets.generate()[name]) < 5_000_000


def test_201_of_the_294_catalogue_rows_have_an_integer_turn_count_by_exact_decimals() -> None:
    from bench import oper_sets

    assert oper_sets.integer_turn_rows() == (201, 294)


def test_explore_holds_every_catalogue_row_at_each_of_the_three_artifacts() -> None:
    from screw.tables.presets import catalogue, expand, expand_nut, nut_catalogue

    labelled = _by_label("explore")
    artifacts = ["stl-preview", "stl-fine", "step"]
    for row in catalogue():
        points = labelled[row.id]
        assert [p["artifact"] for p in points] == artifacts
        assert all(p["preset"] == row.id and p["kind"] == "bolt" for p in points)
        assert all(p["params"] == expand(row.id) for p in points)
    for nut_row in nut_catalogue():
        points = labelled[nut_row.id]
        assert [p["artifact"] for p in points] == artifacts
        assert all(p["preset"] == nut_row.id and p["kind"] == "nut" for p in points)
        assert all(p["params"] == expand_nut(nut_row.id) for p in points)
    assert sum(1 for p in _generated()["explore"]["points"] if "preset" in p) == 924


def test_the_bolt_factorial_has_an_integer_turn_count_by_construction() -> None:
    from screw.calc.thread import _exact

    factorial = [p for p in _parts("explore") if p["label"].startswith("bolt-d")]
    assert len({p["label"] for p in factorial}) > 100
    for point in factorial:
        params = point["params"]
        assert params["thread_length"] == params["length"]
        turns = _exact(params["length"]) / _exact(params["pitch"])
        assert turns.denominator == 1
        assert turns in (3, 30, 240)
    assert {p["params"]["left_hand"] for p in factorial} == {False, True}


def test_the_nut_factorial_covers_both_clearances_and_the_left_hand_subset() -> None:
    nuts = [p for p in _parts("explore") if p["label"].startswith("nut-d")]
    assert {p["params"]["clearance"] for p in nuts} == {0.15, 5.0}
    left = [p for p in nuts if p["params"]["left_hand"]]
    assert left
    assert {p["params"]["clearance"] for p in left} == {0.15}
    assert all(p["params"]["s"] == round(1.6 * p["params"]["d"], 4) for p in left)


def test_the_four_recorded_corners_are_in_explore_at_the_artifact_they_were_recorded_with() -> None:
    labelled = _by_label("explore")
    fine = ["corner-d100-L200", "corner-d100-p5-L1250", "corner-d6-p0.1-L25"]
    for label in fine:
        assert [p["artifact"] for p in labelled[label]] == ["stl-fine"]
    assert labelled["corner-d100-L200"][0]["params"] == {
        "d": 100.0, "length": 200.0, "s": 200.0, "k": 50.0, "thread_length": 200.0}


def test_a_corner_the_model_refuses_is_dropped_with_its_error_and_never_measured() -> None:
    # d = 1e5 needs s above d, and s is bounded by the same 1e5 (head_too_small, params.py): the
    # recorded corner is not a request anyone can make, which the file says instead of hiding.
    dropped = {d["label"]: d for d in _generated()["explore"]["dropped"]}
    assert dropped["corner-d1e5-p1-L1"]["error"] == "less_than_equal"
    assert "corner-d1e5-p1-L1" not in _by_label("explore")


@pytest.mark.parametrize("name", SET_NAMES)
def test_every_part_point_validates_in_the_parameter_model(name: str) -> None:
    from bench import oper_lift

    # Under the guards of the registration: the point files do not move with the walls L20 sets.
    for point in _parts(name):
        oper_lift.registered(point["kind"], point["params"], point.get("lift"))


@pytest.mark.parametrize("name", SET_NAMES)
def test_every_dropped_combination_is_refused_by_the_model_with_the_error_it_names(
        name: str) -> None:
    from pydantic import ValidationError

    from bench import oper_lift

    for entry in _generated()[name]["dropped"]:
        assert set(entry) - {"lift"} == {"label", "kind", "params", "artifacts", "error"}
        with pytest.raises(ValidationError) as caught:
            oper_lift.registered(entry["kind"], entry["params"], entry.get("lift"))
        assert caught.value.errors()[0]["type"] == entry["error"]


def test_the_factorial_refusals_are_listed_and_not_silent() -> None:
    errors = {d["error"] for d in _generated()["explore"]["dropped"]}
    assert {"pitch_too_coarse", "turn_cap", "nut_too_thin"} <= errors


def test_no_label_is_used_twice_for_the_same_artifact() -> None:
    for name in SET_NAMES:
        pairs = [(p["label"], p.get("artifact", p.get("probe")))
                 for p in _generated()[name]["points"]]
        assert len(pairs) == len(set(pairs))


def test_spread_is_the_defaults_and_the_last_rows_at_three_artifacts_each() -> None:
    from screw.tables.presets import catalogue, nut_catalogue

    labelled = _by_label("spread")
    assert list(labelled) == ["default-bolt", "default-nut", catalogue()[-1].id,
                              nut_catalogue()[-1].id]
    assert all(len(points) == 3 for points in labelled.values())
    assert labelled["default-bolt"][0]["params"] == {}
    assert len(_generated()["spread"]["points"]) == 12


# --- walls ---------------------------------------------------------------------------------------


def _walls(prefix: str) -> list[_Point]:
    return [p for p in _generated()["walls"]["points"] if p["label"].startswith(prefix)]


def test_the_turn_walls_are_250_turns_at_the_15_sizes_both_hands_rod_and_void() -> None:
    from bench.thread_spike.maths import PITCH
    from screw.calc.thread import _exact

    bolts, nuts = _walls("turns-bolt-"), _walls("turns-nut-")
    assert len(bolts) == len(nuts) == 15 * 2
    for point in bolts:
        params = point["params"]
        pitch = _exact(params["pitch"])
        assert _exact(params["thread_length"]) == _exact(params["length"]) == 250 * pitch
        assert point["artifact"] == "stl-preview"
    for point in nuts:
        params = point["params"]
        pitch = _exact(params["pitch"])
        assert _exact(params["m"]) + 2 * pitch == 250 * pitch
    sizes = {p["label"].split("-")[2] for p in bolts}
    assert sizes == set(PITCH)
    assert {p["params"]["left_hand"] for p in bolts} == {False, True}


def test_the_field_ceiling_corners_sit_at_1e3_1e4_and_1e5() -> None:
    ceilings = _walls("ceiling-")
    assert len(ceilings) == 3 * 9
    by_label = {p["label"]: p["params"] for p in ceilings}
    for x in (1e3, 1e4, 1e5):
        tag = f"{x:g}"
        assert by_label[f"ceiling-bolt-s-{tag}"] == {"s": x}
        assert by_label[f"ceiling-bolt-k-{tag}"] == {"k": x}
        assert by_label[f"ceiling-bolt-length-{tag}"] == {"length": x}
        assert by_label[f"ceiling-nut-s-{tag}"] == {"s": x}
        bolt_d = by_label[f"ceiling-bolt-d-{tag}"]
        assert bolt_d["s"] == x
        assert bolt_d["d"] < x
        both = by_label[f"ceiling-bolt-thread-{tag}"]
        assert both["thread_length"] == both["length"] == x
        assert both["pitch"] == x / 250
        nut_m = by_label[f"ceiling-nut-m-{tag}"]
        assert nut_m["m"] == x
        assert nut_m["pitch"] * 248 >= x  # rounded up, so the void stays at or under 250 turns


def test_the_diameter_probe_holds_the_largest_d_the_head_rule_admits_at_its_s() -> None:
    from decimal import Context, Decimal

    from bench import oper_lift

    by_label = {p["label"]: p["params"] for p in _walls("ceiling-bolt-d-")}
    assert {label: params["d"] for label, params in by_label.items()} == {
        "ceiling-bolt-d-1000": 999.999, "ceiling-bolt-d-10000": 9999.99,
        "ceiling-bolt-d-100000": 99999.9}
    for params in by_label.values():
        # under the guards of the registration, whose field bound is the 1e5 the corners were
        # chosen under (L20 moved the model's own to the measured walls)
        oper_lift.registered("bolt", params)
        # the next number of 6 significant figures up is no longer under s: the model refuses it
        above = float(Context(prec=6).next_plus(Decimal(repr(params["d"]))))
        with pytest.raises(ValueError, match="across-flats"):
            oper_lift.registered("bolt", {**params, "d": above})


def test_the_clearance_probe_holds_the_largest_clearance_nut_too_thin_admits_at_its_s() -> None:
    from decimal import Context, Decimal

    from bench import oper_lift

    by_label = {p["label"]: p["params"] for p in _walls("ceiling-nut-clearance-")}
    assert {label: params["clearance"] for label, params in by_label.items()} == {
        "ceiling-nut-clearance-1000": 496.999, "ceiling-nut-clearance-10000": 4996.99,
        "ceiling-nut-clearance-100000": 49996.9}
    for x, params in zip((1e3, 1e4, 1e5), by_label.values(), strict=True):
        assert (params["d"], params["s"]) == (6.0, x)
        oper_lift.registered("nut", params)
        above = float(Context(prec=6).next_plus(Decimal(repr(params["clearance"]))))
        with pytest.raises(ValueError, match="across flats"):
            oper_lift.registered("nut", {**params, "clearance": above})


def test_the_nut_diameter_probe_holds_the_largest_d_nut_too_thin_admits_at_its_s() -> None:
    from decimal import Context, Decimal

    from bench import oper_lift

    by_label = {p["label"]: p["params"] for p in _walls("ceiling-nut-d-")}
    assert {label: params["d"] for label, params in by_label.items()} == {
        "ceiling-nut-d-1000": 999.699, "ceiling-nut-d-10000": 9999.69,
        "ceiling-nut-d-100000": 99999.6}
    for x, params in zip((1e3, 1e4, 1e5), by_label.values(), strict=True):
        assert params["s"] == x
        assert "clearance" not in params  # the default 0.15, which the protocol states
        oper_lift.registered("nut", params)
        above = float(Context(prec=6).next_plus(Decimal(repr(params["d"]))))
        with pytest.raises(ValueError, match="across flats"):
            oper_lift.registered("nut", {**params, "d": above})


def test_the_protocol_ties_the_nut_diameter_ceiling_to_its_probe_and_tested_value() -> None:
    rule = " ".join(_rule(8).split())
    assert "nut `d` the `ceiling-nut-d` reading" in rule
    assert "nut `d`, whose tested value is the largest under X - 2 x 0.15 (99999.6 at 1e5)" in rule
    assert "nut `d`: a nut with `s` = X" in " ".join(_protocol().split())


def test_the_tail_walk_runs_eight_decades_at_three_sizes_and_both_hands() -> None:
    tails = _walls("tail-")
    assert len(tails) == 3 * 2 * 8
    assert all(p["kind"] == "probe" and p["probe"] == "tail" for p in tails)
    assert {p["args"]["tail"] for p in tails} == {float(f"1e-{i}") for i in range(2, 10)}
    assert {(p["args"]["d"], p["args"]["pitch"]) for p in tails} == {
        (6.0, 1.0), (2.0, 0.4), (20.0, 2.5)}
    assert all(p["args"]["turns"] == 3 for p in tails)
    assert {p["args"]["left_hand"] for p in tails} == {False, True}


def test_the_root_radius_walk_reaches_the_radius_it_names_at_every_size_and_hand() -> None:
    from screw.calc.thread import thread_depth

    points = _walls("root-")
    assert len(points) == 15 * 2 * 9 * 2
    radii = set()
    for point in points:
        params = point["params"]
        target = float(point["label"].rsplit("-r", 1)[1])
        radii.add(target)
        realised = params["d"] / 2 - thread_depth(params["pitch"])
        if point["kind"] == "nut":
            realised += 0.15
        assert realised > 0
        assert realised == pytest.approx(target, rel=1e-3)
    assert radii == {1e-2, 3e-3, 1e-3, 3e-4, 1e-4, 3e-5, 1e-5, 3e-6, 1e-6}


def test_the_void_walk_is_the_group_d_nut_at_four_higher_radii() -> None:
    from bench import oper_sets
    from bench.thread_spike.maths import PITCH
    from screw.calc.thread import thread_depth

    walk = oper_sets._void_walk_set()
    assert walk.dropped == []  # the parameter model refuses none of the 120
    points: list[_Point] = json.loads(walk.text())["points"]
    assert len(points) == 15 * 2 * 4
    assert [p["label"] for p in points[:4]] == [
        f"root-nut-{next(iter(PITCH))}-right-r{r:g}" for r in (0.03, 0.1, 0.3, 1.0)]
    assert {p["label"].rsplit("-r", 1)[1] for p in points} == {"0.03", "0.1", "0.3", "1"}
    for point in points:
        params = point["params"]
        assert point["kind"] == "nut"
        assert point["artifact"] == "stl-preview"
        assert set(point) == {"label", "kind", "params", "artifact"}  # no lift, no preset
        assert set(params) == {"d", "pitch", "m", "s", "left_hand"}
        assert params["pitch"] > 0
        assert params["m"] == 3 * params["pitch"]
        assert params["s"] == oper_sets._scaled(params["d"], "1.6")
        target = float(point["label"].rsplit("-r", 1)[1])
        realised = params["d"] / 2 - thread_depth(params["pitch"]) + 0.15
        assert realised == pytest.approx(target, abs=1e-9)
    assert min(p["params"]["pitch"] for p in points) == pytest.approx(0.277128, abs=1e-6)


def test_the_void_walk_builds_its_nuts_as_group_d_builds_them() -> None:
    from bench import oper_sets

    nuts = _walls("root-nut-")
    assert len(nuts) == 15 * 2 * 9
    for point in nuts:
        _, _, size, hand, radius = point["label"].split("-", 4)
        built = oper_sets._void_cell(size, hand == "left", float(radius[1:]))
        assert built == point["params"]


def test_the_void_walk_labels_are_not_walls_labels() -> None:
    from bench import oper_sets

    walls = {p["label"] for p in _generated()["walls"]["points"]}
    assert walls.isdisjoint(p["label"] for p in oper_sets.void_walk_points())


def test_the_committed_void_walk_is_the_generators_from_the_explore_run() -> None:
    from bench import oper_sets

    spec = oper.load_set("walls-voids")
    assert (spec.reps, spec.deadline_s) == (1, 600)
    assert spec.rule == "07-SWEEP-PROTOCOL.md R10 (G25)"
    assert spec.sources == ("explore=bench/results/phase-07/explore-40646117094",)
    assert spec.shard_sizes is not None
    assert sum(spec.shard_sizes) == 120 == len(spec.points)
    expected = oper_sets.void_walk_points()
    assert [(p.label, p.kind, dict(p.params), p.artifact) for p in spec.points] == [
        (e["label"], e["kind"], e["params"], e["artifact"]) for e in expected]


def test_walls_include_the_nuts_the_two_open_nut_debt_items_name() -> None:
    lead = _walls("nutlead-")
    assert len(lead) == 3 * 3
    assert {(p["params"]["d"], p["params"]["m"], p["params"]["clearance"]) for p in lead} == {
        (2.0, 12.0, 0.1), (8.0, 38.0, 0.1), (14.0, 46.0, 0.1)}
    assert {p["params"]["s"] for p in lead} == {1e3, 1e4, 1e5}
    countersink = _walls("nutcsk-")
    assert {(p["params"]["pitch"], p["params"]["clearance"]) for p in countersink} == {
        (1.5, 0.05), (1.8, 0.05), (1.5, 0.01)}
    assert all(p["params"]["d"] == 2.0 and p["params"]["s"] == 4.0 and p["params"]["m"] == 3.0
               for p in countersink)


# --- controls ------------------------------------------------------------------------------------


def test_the_controls_run_the_thread_spikes_positions_on_the_sample_sizes_right_hand() -> None:
    from bench.thread_spike.maths import PITCH, SAMPLE_SIZES, standard_max

    points = _generated()["controls"]["points"]
    assert all(p["kind"] == "probe" for p in points)
    naive = [p for p in points if p["probe"] == "naive"]
    pipe = [p for p in points if p["probe"] == "one_pipe"]
    assert len(naive) + len(pipe) == len(points)
    assert all(p["args"]["left_hand"] is False for p in pipe)
    for size in SAMPLE_SIZES:
        d, pitch = PITCH[size]
        lengths = {p["args"]["length"] for p in naive if p["label"].startswith(f"naive-{size}-")}
        assert lengths == {float(x) for x in {10 * pitch, 10, 20, standard_max(d)}}
        turns = {p["args"]["turns"] for p in pipe if p["label"].startswith(f"one_pipe-{size}-")}
        wanted = {float(standard_max(d) / pitch), 100.0, 160.0, 200.0, 250.0}
        assert turns == wanted


# --- the loader accepts what the generator adds --------------------------------------------------


def test_a_point_file_may_carry_dropped_notes_and_a_preset_per_point(tmp_path: Path) -> None:
    point = {"label": "a", "kind": "bolt", "params": {}, "artifact": "step", "preset": "iso:x"}
    _write_set(tmp_path, points=[point], dropped=[{"label": "b"}], notes=["why"])
    assert oper.load_set("mini", tmp_path).points[0].label == "a"


@pytest.mark.parametrize(
    "over",
    [{"dropped": "no"}, {"notes": "no"}, {"notes": [1]},
     {"points": [{"label": "a", "kind": "bolt", "params": {}, "artifact": "step", "preset": 3}]}],
    ids=["dropped-not-a-list", "notes-not-a-list", "note-not-text", "preset-not-text"])
def test_the_added_keys_are_held_to_their_types(over: dict[str, object], tmp_path: Path) -> None:
    _write_set(tmp_path, **over)
    with pytest.raises(ValueError, match="mini"):
        oper.load_set("mini", tmp_path)


def test_one_part_may_be_listed_once_per_artifact_but_not_twice_for_one(tmp_path: Path) -> None:
    def part(artifact: str) -> dict[str, object]:
        return {"label": "a", "kind": "bolt", "params": {}, "artifact": artifact}

    _write_set(tmp_path, points=[part("step"), part("stl-fine")])
    assert len(oper.load_set("mini", tmp_path).points) == 2
    _write_set(tmp_path, points=[part("step"), part("step")])
    with pytest.raises(ValueError, match="mini"):
        oper.load_set("mini", tmp_path)


# --- a point past a validator cap lifts that one guard (07 R3) -----------------------------------

SHORT_ROD = {"d": 2.0, "pitch": 0.4, "length": 104.0, "thread_length": 104.0}  # 260 turns


def _lift_error(kind: str, params: Mapping[str, float | bool],
                lift: Mapping[str, float] | None = None, *,
                registered: bool = False) -> str | None:
    """The error type the model gives `params` with `lift` lifted: the production model, or, with
    `registered`, the guards the point files were registered under (250 turns, 1e5 mm)."""
    from pydantic import ValidationError

    from bench import oper_lift

    check = oper_lift.registered if registered else oper_lift.validate
    try:
        check(kind, params, lift)
    except ValidationError as exc:
        return str(exc.errors()[0]["type"])
    return None


def test_the_parent_and_the_lift_module_name_the_same_guards() -> None:
    from bench import oper_lift

    assert oper.LIFT_ARGS == oper_lift.LIFTS


def test_a_turn_lift_admits_the_turns_it_names_and_not_one_more() -> None:
    assert _lift_error("bolt", SHORT_ROD) == "turn_cap"
    assert _lift_error("bolt", SHORT_ROD, {"max_turns": 260}) is None
    longer = {**SHORT_ROD, "length": 104.4, "thread_length": 104.4}
    assert _lift_error("bolt", longer, {"max_turns": 260}) == "turn_cap"
    void = {"d": 2.0, "pitch": 0.4, "m": 103.2, "s": 4.0}  # m + 2 pitch is 260 turns
    assert _lift_error("nut", void) == "turn_cap"
    assert _lift_error("nut", void, {"max_turns": 260}) is None


def test_a_turn_lift_leaves_every_other_guard_in_place_and_restores_the_cap() -> None:
    from screw.calc import thread

    cap = thread.MAX_TURNS
    assert _lift_error("bolt", {**SHORT_ROD, "s": 1.0}, {"max_turns": 260}) == "head_too_small"
    assert cap == thread.MAX_TURNS
    assert _lift_error("bolt", {**SHORT_ROD, "d": -1.0}, {"max_turns": 260}) == "greater_than"
    assert cap == thread.MAX_TURNS


def test_a_field_lift_admits_the_bound_it_names_and_not_a_decade_more() -> None:
    assert _lift_error("bolt", {"s": 1e6}) == "less_than_equal"
    assert _lift_error("bolt", {"s": 1e6}, {"max_mm": 1e6}) is None
    assert _lift_error("bolt", {"s": 1e7}, {"max_mm": 1e6}) == "less_than_equal"
    assert _lift_error("nut", {"s": 1e6, "clearance": 4e5}, {"max_mm": 1e6}) is None


def test_a_field_lift_leaves_every_other_guard_in_place_and_the_classes_untouched() -> None:
    from annotated_types import Le

    from screw.params import MAX_FIELD_MM, BoltParams, NutParams

    assert _lift_error("bolt", {"d": 5e5, "s": 4e5}, {"max_mm": 1e6}) == "head_too_small"
    assert _lift_error("nut", {"s": 1e5, "clearance": 5e5}, {"max_mm": 1e6}) == "nut_too_thin"
    assert _lift_error("bolt", {"length": 1e6, "pitch": 1e-3, "thread_length": 1e6},
                       {"max_mm": 1e6}) == "turn_cap"
    for model in (BoltParams, NutParams):
        assert [m.le for m in model.model_fields["s"].metadata
                if isinstance(m, Le)] == [MAX_FIELD_MM]


def test_the_registered_guards_are_the_ones_the_point_files_were_made_under() -> None:
    from screw.calc import thread

    cap, floor = thread.MAX_TURNS, thread.MIN_ROOT_RADIUS_MM
    rod = {"d": 2.0, "pitch": 0.4, "length": 100.0, "thread_length": 100.0}  # 250 turns
    assert _lift_error("bolt", rod) == "turn_cap"    # the production cap is lower since L20
    assert _lift_error("bolt", rod, registered=True) is None
    past = {**rod, "length": 100.4, "thread_length": 100.4}
    assert _lift_error("bolt", past, registered=True) == "turn_cap"
    assert _lift_error("bolt", {"length": 1e5}) == "less_than_equal"
    assert _lift_error("bolt", {"length": 1e5}, registered=True) is None
    assert _lift_error("bolt", {"length": 1.0000001e5}, registered=True) == "less_than_equal"
    # a root radius above 0, as L12 had it: the floor of L20 is not a registered guard
    thin = {"d": 2.0, "pitch": 1.84, "length": 1.84, "thread_length": 1.84}
    assert _lift_error("bolt", thin) == "pitch_too_coarse"
    assert _lift_error("bolt", thin, registered=True) is None
    gone = {"d": 2.0, "pitch": 1.85, "length": 1.85, "thread_length": 1.85}
    assert _lift_error("bolt", gone, registered=True) == "pitch_too_coarse"    # root under 0
    # and the production constants are back after every call, errors included
    assert (cap, floor) == (thread.MAX_TURNS, thread.MIN_ROOT_RADIUS_MM)


def test_a_registered_lift_names_exactly_one_known_guard_and_replaces_only_that_one() -> None:
    from bench import oper_lift

    assert _lift_error("bolt", SHORT_ROD, {"max_turns": 260}, registered=True) is None
    longer = {**SHORT_ROD, "length": 104.4, "thread_length": 104.4}
    assert _lift_error("bolt", longer, {"max_turns": 260}, registered=True) == "turn_cap"
    assert _lift_error("bolt", {"s": 1e6}, registered=True) == "less_than_equal"
    assert _lift_error("bolt", {"s": 1e6}, {"max_mm": 1e6}, registered=True) is None
    # lifting the field bound leaves the turn cap at the registered 250, not the production 90
    rod = {"d": 2.0, "pitch": 0.4, "length": 100.0, "thread_length": 100.0}
    assert _lift_error("bolt", rod, {"max_mm": 1e6}, registered=True) is None
    for lift in ({"max_turns": 260, "max_mm": 1e6}, {"max_pitch": 3}):
        with pytest.raises(ValueError, match="exactly one"):
            oper_lift.registered("bolt", {}, lift)


@pytest.mark.parametrize("lift", [{}, {"max_turns": 260, "max_mm": 1e6}, {"max_pitch": 3}],
                         ids=["empty-is-no-lift", "two-guards", "unknown-guard"])
def test_a_lift_must_name_exactly_one_known_guard(lift: dict[str, float]) -> None:
    from bench import oper_lift

    if lift == {}:
        assert oper_lift.validate("bolt", {}, lift).kind == "bolt"
    else:
        with pytest.raises(ValueError, match="exactly one"):
            oper_lift.validate("bolt", {}, lift)


def test_a_lift_reaches_the_child_and_only_when_a_point_has_one(tmp_path: Path) -> None:
    plain = {"label": "a", "kind": "bolt", "params": {}, "artifact": "step"}
    lifted = {**plain, "label": "b", "lift": {"max_mm": 1e6}}
    _write_set(tmp_path, points=[plain, lifted])
    first, second = oper.load_set("mini", tmp_path).points
    assert first.lift is None
    assert "lift" not in json.loads(first.as_json())
    assert second.lift == {"max_mm": 1e6}
    assert json.loads(second.as_json())["lift"] == {"max_mm": 1e6}


@pytest.mark.parametrize(
    "lift",
    [{}, {"max_turns": 260, "max_mm": 1e6}, {"max_pitch": 3}, "max_mm", ["max_mm"],
     {"max_turns": 260.5}, {"max_turns": 0}, {"max_turns": True}, {"max_mm": 0},
     {"max_mm": "1e6"}, {"max_mm": False}],
    ids=["empty", "two-guards", "unknown-guard", "text", "list", "fractional-turns", "zero-turns",
         "bool-turns", "zero-mm", "text-mm", "bool-mm"])
def test_a_lift_that_breaks_its_schema_is_refused_naming_the_point(
        lift: object, tmp_path: Path) -> None:
    point = {"label": "lifted", "kind": "bolt", "params": {}, "artifact": "step", "lift": lift}
    _write_set(tmp_path, points=[point])
    with pytest.raises(ValueError, match="lifted"):
        oper.load_set("mini", tmp_path)


def test_a_probe_cannot_carry_a_lift(tmp_path: Path) -> None:
    _write_set(tmp_path, points=[{**_probe(), "lift": {"max_mm": 1e6}}])
    with pytest.raises(ValueError, match="'t'"):
        oper.load_set("mini", tmp_path)


def test_a_reading_past_a_guard_records_which_guard_it_lifted(
        monkeypatch: pytest.MonkeyPatch) -> None:
    def run(argv: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 0, stdout=_ok_line(), stderr="")

    def docker(*args: str, **_: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 0, stdout="false 0", stderr="")

    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(oper, "_docker", docker)
    plain = oper.Point("a", "bolt", {}, "step")
    lifted = oper.Point("b", "bolt", {"s": 2e5}, "step", {"max_mm": 1e6})
    assert "lift" not in oper.run_reading(plain, 1, "screw:x", oper.CAP_BYTES, 60)
    assert oper.run_reading(lifted, 1, "screw:x", oper.CAP_BYTES, 60)["lift"] == {"max_mm": 1e6}


def test_the_child_validates_a_lifted_point_with_the_guard_lifted(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    from screw import solid
    from screw.params import FastenerParams

    built: list[FastenerParams] = []
    monkeypatch.setattr(solid, "build", lambda p: built.append(p))
    monkeypatch.setattr(solid, "export", lambda *_: bytes(84))
    point = {"kind": "bolt", "params": {"s": 2e5}, "artifact": "stl-preview"}
    assert oper_child.main([json.dumps(point)]) == 2  # refused unlifted: less_than_equal
    assert built == []
    capsys.readouterr()
    assert oper_child.main([json.dumps({**point, "lift": {"max_mm": 1e6}})]) == 0
    assert len(built) == 1
    assert getattr(built[0], "s") == 2e5  # noqa: B009 -- FastenerParams has no `s`, a bolt does
    assert oper_child.main([json.dumps({**point, "lift": {"max_pitch": 1}})]) == 2


def test_walls_past_the_caps_hold_260_turns_and_the_next_decade_each_with_its_one_lift() -> None:
    beyond = _walls("beyond-")
    assert len(beyond) == 15 * 2 * 2 + 9
    assert all(p["artifact"] == "stl-preview" and p["kind"] != "probe" for p in beyond)
    turns = [p for p in beyond if p["label"].startswith("beyond-turns-")]
    assert len(turns) == 60
    assert {tuple(p["lift"].items()) for p in turns} == {(("max_turns", 260),)}
    fields = [p for p in beyond if not p["label"].startswith("beyond-turns-")]
    assert {tuple(p["lift"].items()) for p in fields} == {(("max_mm", 1e6),)}
    assert {p["label"] for p in fields} == {
        f"beyond-{field}-1000000" for field in (
            "bolt-d", "bolt-length", "bolt-s", "bolt-k", "bolt-thread", "nut-s", "nut-clearance",
            "nut-d", "nut-m")}


def test_every_past_the_cap_point_is_refused_by_the_plain_model_and_by_it_alone() -> None:
    from screw.params import KINDS

    for point in _walls("beyond-"):
        # past the guards of the registration, whose caps are the ones the points step past
        plain = _lift_error(point["kind"], point["params"], registered=True)
        assert plain in {"turn_cap", "less_than_equal"}
        assert _lift_error(point["kind"], point["params"], point["lift"], registered=True) is None
        assert point["kind"] in KINDS


# --- the protocol the point files are registered in (07-03) ---------------------------------------

PROTOCOL = REPO_ROOT / ".planning" / "phases" / "07-operability-re-sweep" / "07-SWEEP-PROTOCOL.md"


def _protocol() -> str:
    return PROTOCOL.read_text()


def test_the_protocol_states_thirty_rules_once_each_in_order() -> None:
    headings = re.findall(r"^## R(\d+) ", _protocol(), re.MULTILINE)
    assert headings == [str(n) for n in range(1, 31)]


def test_every_point_file_names_a_rule_the_protocol_states() -> None:
    for name in ("tracer", *SET_NAMES):
        rule = json.loads((POINTS_DIR / f"{name}.json").read_text())["rule"]
        match = re.fullmatch(r"07-SWEEP-PROTOCOL\.md R(\d+)", rule)
        assert match, rule
        assert f"\n## R{match.group(1)} " in _protocol()


def test_the_protocol_table_gives_each_set_the_shape_and_counts_its_file_has() -> None:
    rows = {m.group(1): [int(x) for x in m.groups()[1:]] for m in re.finditer(
        r"^\| (explore|spread|walls|controls) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \|",
        _protocol(), re.MULTILINE)}
    assert sorted(rows) == sorted(SET_NAMES)
    for name in SET_NAMES:
        doc = _generated()[name]
        assert rows[name] == [doc["reps"], doc["shards"], doc["deadline_s"], len(doc["points"]),
                              len(doc["dropped"])], name


def _rule(number: int) -> str:
    text = _protocol()
    start = text.index(f"\n## R{number} ")
    return text[start:text.index("\n## R", start + 1)]


@pytest.mark.parametrize("number", [9, 10])
def test_a_floor_stands_only_on_ok_readings_and_otherwise_stops_the_phase(number: int) -> None:
    rule = " ".join(_rule(number).split())
    assert "stands only on `ok` readings" in rule
    assert "`capped` reading sets no F" in rule
    assert "the phase stops and asks the owner" in rule


def test_the_protocol_names_the_git_blob_sha_of_every_committed_point_file() -> None:
    import hashlib

    quoted = dict(re.findall(r"`(\w+)\.json`\s+`([0-9a-f]{40})`", _protocol()))
    assert sorted(quoted) == sorted(("tracer", *SET_NAMES))
    for name, sha in quoted.items():
        data = (POINTS_DIR / f"{name}.json").read_bytes()
        assert hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest() == sha, name


def test_the_protocol_fixes_every_number_a_rule_needs_before_any_reading() -> None:
    text = _protocol()
    for needle in ("random.Random(20261026)", "at least 10 %", "1.5x", "256 MiB",
                   "4 x 10^9 bytes", "ceil(2 x", "statistics.quantiles(n=20)"):
        assert needle in text, needle


def test_no_rule_carries_the_macos_tail_floor_or_spurs_export_budget_as_a_value() -> None:
    text = _protocol()
    assert "64 MiB" not in text
    assert "stays 1e-3" not in text
    assert "1e-3 sits" not in text
    assert "above 0" in _rule(9)


def test_the_protocol_records_the_disposition_of_the_two_debt_items_it_leaves_open() -> None:
    text = _protocol()
    for item in ("2026-10-10-spike-protocol-amendments-before-next-campaign.md",
                 "2026-10-14-m18-probe-one-entry-has-no-deadline-during-a-run.md"):
        assert item in text
        assert (REPO_ROOT / "docs" / "tech_debt" / "active" / item).is_file()


def test_contention_partners_take_one_affinity_slot_each_so_the_workers_are_distinct() -> None:
    rule = " ".join(_rule(14).split())
    assert "on each of the other N - 1 slots, one candidate of the same artifact" in rule
    assert "`hash(p) % N`" in rule
    assert "N distinct workers" in rule
    assert "a tie going to the label that sorts first" in rule
    assert "the phase stops and asks the owner" in rule


def test_the_slot_the_protocol_computes_is_the_pools_and_is_the_same_in_every_process() -> None:
    import inspect

    from screw.pool import BuildPool

    assert "hash(p) % self.workers" in inspect.getsource(BuildPool.executor_for)
    code = ("from screw.params import KINDS; "
            "ps = [KINDS['bolt'].model_validate({'length': n, 'thread_length': n}) "
            "for n in (20, 30, 40)] + [KINDS['nut'].model_validate({'m': 6})]; "
            "print([hash(p) % n for p in ps for n in (1, 2, 3)])")
    seen = {subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                           check=True, env={**os.environ, "PYTHONHASHSEED": seed}).stdout
            for seed in ("1", "2", "random")}
    assert len(seen) == 1


@pytest.mark.parametrize("number", [11, 13])
def test_a_point_supplies_a_fit_or_calibration_figure_only_if_every_repetition_is_ok(
        number: int) -> None:
    rule = " ".join(_rule(number).split())
    assert "whose every repetition is `ok`" in rule
    assert "per-point max, R11" in rule or "has no max (R3) and is not fitted" in rule
    assert "no ok reading" not in rule


def test_the_bound_set_holds_the_memory_extrema_that_w_is_read_from() -> None:
    rule = " ".join(_rule(14).split())
    assert "the admitted point with the largest enveloped peak-bytes prediction" in rule
    assert "the admitted point with the largest measured peak" in rule
    assert "the set holds 5 to 8 points" in rule
    assert "the memory extrema of each included" in " ".join(_rule(16).split())


def test_a_turn_bound_stands_only_on_ok_boundary_readings_and_otherwise_stops_the_phase() -> None:
    rule = " ".join(_rule(7).split())
    assert "The bound stands only on `ok` readings" in rule
    assert "A `killed`, `capped` or `no_cgroup` reading in that evidence" in rule
    assert "or a reading it asks for that is missing" in rule
    assert "No turn bound is then awarded, 250 included," in rule
    assert "the phase stops and asks the owner" in rule


def test_the_load_run_is_the_cold_worst_case_with_no_part_repeated() -> None:
    rule = " ".join(_rule(15).split())
    assert "no request repeats a part anywhere in a run" in rule
    assert "The artifacts take their parts in the order `stl-fine`, `step`, `stl-preview`" in rule
    assert "Each artifact takes its parts on its own" in rule
    assert "the first 3 parts of its own edge ranking" in rule
    assert "takes its next-ranked ones by its own edge ranking, so every artifact keeps" in rule
    assert "the three artifacts of one part included" in rule
    assert "A run has 20 parts for each artifact" in rule
    assert "pass" not in rule
    assert "no part is repeated to fill a gap" in rule
    assert "a new `random.Random(20261026).shuffle`" in rule
    assert "`SCREW_EXPORT_CACHE_MB` is 1" in rule
    assert "Every request carries `Accept-Encoding: identity`" in rule


def test_the_required_tier_fixes_its_candidates_edge_draw_ties_and_duplicates() -> None:
    rule = " ".join(_rule(27).split())
    assert "deduplicated by part" in rule
    assert "the first in file order is kept" in rule
    assert "a tie going to the label that sorts first" in rule
    assert "shuffled by `random.Random(20261026).shuffle`" in rule
    assert "The *edge ranking* is every candidate ordered by edge ratio, largest first" in rule
    assert "Where no component is finite for A" in rule
    assert "which under C3 is `stl-preview` and `step`" in rule
    assert "the edge ratio is the point's enveloped build-seconds prediction, by this rule" in rule
    assert "ranked by seconds and not by bytes" in rule
    assert "it stops at the first draw point that does not fit and skips none" in rule
    assert "otherwise the artifact's full timeout (R14)" in rule
    assert "Steps 1 to 4 need no timeout, so D(A) is fixed before the load run (R15)" in rule
    assert "the tier is built only then and never before" in rule


def test_the_seeded_shuffle_the_protocol_names_is_the_one_python_3_12_gives() -> None:
    import random

    order = list(range(12))
    random.Random(20261026).shuffle(order)
    assert order == [8, 11, 9, 10, 5, 0, 4, 6, 7, 2, 3, 1]


def test_the_export_cache_setting_floors_at_one_so_the_load_run_cannot_turn_it_off(
        monkeypatch: pytest.MonkeyPatch) -> None:
    from screw import int_env

    monkeypatch.setenv("SCREW_EXPORT_CACHE_MB", "0")
    assert int_env("SCREW_EXPORT_CACHE_MB", 64) == 1


def test_explore_holds_enough_distinct_parts_for_a_load_run_that_repeats_none() -> None:
    parts: dict[str, set[str]] = {}
    for point in _generated()["explore"]["points"]:
        key = json.dumps([point["kind"], point["params"]], sort_keys=True)
        parts.setdefault(point["artifact"], set()).add(key)
    assert all(len(keys) >= 20 for keys in parts.values())  # 20 per artifact
    assert len(set().union(*parts.values())) >= 60  # 3 x 20 parts, none shared


def test_the_load_peak_is_read_once_at_the_end_of_one_run_and_drift_is_the_drift_runs() -> None:
    load = " ".join(_rule(15).split())
    assert "The container's cgroup peak is read once, at the end of the run" in load
    assert "growth across repeated builds is the drift run of R23" in load
    assert "read at the end of the load run, R15" in " ".join(_rule(16).split())


def test_the_drift_run_builds_one_fixed_part_cold_k_times_and_compares_the_first_and_last_peak(
) -> None:
    rule = " ".join(_rule(23).split())
    assert "It is separate from the load run" in rule
    assert "K = 20 times in a row" in rule
    assert "the point of A's bound set (R14) with the largest `memory_peak_bytes`" in rule
    assert "among those whose reading is `ok`" in rule
    assert "a tie going to the label that sorts first" in rule
    assert "`screw.solid.clear_cache`" in rule
    assert "compares the cgroup peak after build 1 with the peak after build K" in rule
    assert "the drift of the artifact is the max over its 5 repetitions" in rule
    assert "exceeds 0.10 x the smallest peak after build 1 among its 5 repetitions" in rule
    assert "Drift adds to R16's `mem_limit(N)` only through W" in rule
    assert "Drift adds nothing to R16's `mem_limit(N)`" not in rule
    assert "the owner fixes" not in rule
    assert "pass 2" not in rule


def test_a_repeated_part_would_hit_the_solid_cache_so_the_drift_run_empties_it(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The reason the drift run cannot just repeat a request: the cache keeps at least one solid,
    and a repeat of the same validated params is a hit, not a build."""
    from screw import int_env
    from screw.solid import _build_cached, clear_cache

    monkeypatch.setenv("SCREW_SOLID_CACHE", "0")
    assert int_env("SCREW_SOLID_CACHE", 4) == 1
    assert _build_cached.cache_parameters()["maxsize"] >= 1
    clear_cache()  # exists, and is what the rule names


def test_the_turn_bound_is_a_common_candidate_that_every_cell_is_confirmed_at() -> None:
    rule = " ".join(_rule(7).split())
    assert "A *cell* is a size, a hand and a kind" in rule
    assert "The *candidate* T is the smallest first ok step over the cells" in rule
    assert "`MAX_TURNS` is T only if the confirmation readings" in rule
    assert "are `ok`, in all 5 repetitions, for every cell" in rule
    assert "The confirmation set reads every cell at T, at 5 repetitions taken fresh" in rule
    assert "has not been read at T yet" not in rule
    assert "a cell is read at T only if" not in rule
    assert "A confirmation reading at T that is not `ok`, or is missing, awards no turn" in rule
    assert "the confirmation readings at T" in rule
    assert "For R7 the value is the candidate T" in " ".join(_rule(3).split())


# --- the repetitions a summary expects (R3) -------------------------------------------------------


def test_four_distinct_repetitions_are_incomplete_and_carry_no_median_or_max() -> None:
    row = oper.summarize([_reading(r) for r in (1, 2, 3, 4)])[0]
    assert row["status"] == "incomplete"
    assert row["n"] == 4
    assert row["median"] is None
    assert row["max"] is None


def test_five_copies_of_one_repetition_are_incomplete_and_carry_no_median_or_max() -> None:
    row = oper.summarize([_reading(1)] * 5)[0]
    assert row["status"] == "incomplete"
    assert row["n"] == 5
    assert row["reps"] == [1, 1, 1, 1, 1]
    assert row["median"] is None
    assert row["max"] is None


def test_a_sixth_repetition_or_a_foreign_one_is_incomplete() -> None:
    assert oper.summarize([_reading(r) for r in range(1, 7)])[0]["status"] == "incomplete"
    assert oper.summarize([_reading(r) for r in (1, 2, 3, 4, 6)])[0]["status"] == "incomplete"


def test_the_expected_repetitions_are_the_callers_and_in_any_order() -> None:
    explore = oper.summarize([_reading(1)], expected_reps=[1])[0]
    assert explore["status"] == "ok"
    assert explore["max"] is not None
    shuffled = oper.summarize([_reading(r) for r in (3, 1, 5, 2, 4)])[0]
    assert shuffled["status"] == "ok"
    assert oper.summarize([_reading(2)], expected_reps=[1])[0]["status"] == "incomplete"


def test_a_failing_repetition_keeps_its_own_status_before_the_incomplete_one() -> None:
    row = oper.summarize([_reading(1), _reading(2, "capped")])[0]
    assert row["status"] == "capped"
    assert row["median"] is None


def test_a_lifted_row_with_missing_repetitions_is_incomplete_too() -> None:
    row = oper.summarize([_reading(r, lift={"max_mm": 1e6}) for r in (1, 2)])[0]
    assert row["status"] == "incomplete"


def test_an_incomplete_point_prints_its_repetitions_and_no_figures(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "dup.jsonl"
    path.write_text("\n".join(json.dumps(_reading(1)) for _ in range(5)) + "\n")
    assert oper.main(["summarize", str(path)]) == 0
    text = capsys.readouterr().out
    assert "incomplete" in text
    assert "reps seen [1, 1, 1, 1, 1]" in text
    assert "median" not in text
    assert oper.main(["summarize", str(path), "--markdown"]) == 0
    markdown = capsys.readouterr().out
    assert "reps seen [1, 1, 1, 1, 1]" in markdown
    assert "| p | stl-preview | 5 | incomplete |" in markdown
    assert oper.main(["summarize", str(path), "--reps", "1"]) == 0  # one rep expected: five copies
    assert "incomplete" in capsys.readouterr().out


@pytest.mark.parametrize("text", ["", "0", "1,1", "a", "1,,2", "-1"])
def test_a_bad_expected_repetitions_list_is_refused_with_exit_2(
        text: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "one.jsonl"
    path.write_text(json.dumps(_reading(1)) + "\n")
    assert oper.main(["summarize", str(path), "--reps", text]) == 2
    assert "--reps" in capsys.readouterr().err


def test_the_job_summary_expects_the_one_repetition_of_its_job() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "operability.yml").read_text()
    assert 'summarize --markdown --reps "$REP"' in workflow


def test_the_protocol_asks_for_the_distinct_repetitions_and_the_harness_enforces_it() -> None:
    rule = " ".join(_rule(3).split())
    assert "`rep` 1 to the set's reps, each exactly once" in rule
    assert "is `incomplete` and has no median and no max" in rule
    assert oper.BOUND_REPS == (1, 2, 3, 4, 5)
    assert "(`bench.oper.summarize`)" in rule


# --- the gap rulings (PR A2): each new rule is pinned by its key phrase ---------------------------


def test_an_above_zero_floor_is_confirmed_at_its_smallest_walked_value() -> None:
    rule = " ".join(_rule(3).split())
    assert "Where R9 or R10 decides \"above 0\"" in rule
    assert "the smallest walked value (tail 1e-9 mm, root radius 1e-6 mm) for every cell" in rule
    assert "Any reading there that is not `ok` awards no floor" in rule
    assert "the confirm set of R3 at 1e-9 mm, for every size and hand" in " ".join(_rule(9).split())
    assert "the confirm set of R3 at 1e-6 mm, for every size and hand, rods only" in " ".join(
        _rule(10).split())


def test_the_walk_down_reads_every_step_once_and_the_confirm_decides() -> None:
    rule = " ".join(_rule(7).split())
    assert "every step of 10 turns from 240 down to 10, at 1 repetition, in one dispatch" in rule
    assert "The cell's first ok step is the highest of those steps whose reading is `ok`" in rule
    assert "A cell's readings below its first ok step are recorded and used for nothing" in rule
    assert "the 5-repetition confirm at T decides" in rule
    assert "whether or not that cell already has a 1-repetition reading at T" in rule
    assert "such a reading is not one of the 5 and stands in for none of them" in rule
    assert "from 240 down to 10" in rule
    assert "A cell with no `ok` step has no first ok step" in rule
    assert "the R7 walk-down set" in " ".join(_rule(3).split())


def test_a_spread_point_without_a_median_leaves_the_margin_with_no_number() -> None:
    rule = " ".join(_rule(5).split())
    assert "If any `spread` point has no median" in rule
    assert "`m` has no number and the phase stops and asks the owner" in rule


def test_only_cold_isolated_readings_widen_the_envelope() -> None:
    rule = " ".join(_rule(12).split())
    assert "only a cold isolated reading widens it" in rule
    assert "a contention reading at N = 1 and build 1 of a drift repetition" in rule
    assert "A contended wall (a contention reading at N = 2 or 3)" in rule
    assert "a load request wall and a drift build 2 to K never widen `e`" in rule


def test_a_widening_redraws_no_bound_set_load_mix_or_tier_list() -> None:
    rule = " ".join(_rule(12).split())
    assert "D(A) (R27 steps 1 to 4), the bound set (R14) and the load mix (R15)" in rule
    assert "are each fixed once" in rule
    assert "are never redrawn when `e` widens" in rule
    assert "A widening changes admission and the final numbers only" in rule
    for number, phrase in ((14, "is not redrawn when `e` widens (R12)"),
                           (15, "is not redrawn when `e` widens (R12)"),
                           (27, "it is not redrawn when `e` widens (R12)")):
        assert phrase in " ".join(_rule(number).split()), number


def test_a_shard_is_the_longest_file_order_prefix_that_fits_under_half_the_timeout() -> None:
    rule = " ".join(_rule(6).split())
    assert "A shard is the longest such prefix of the points not yet placed" in rule
    assert "summed charge stays under half the measure job's `timeout-minutes`" in rule
    assert "each point is charged the largest `wall_s` of any `explore` reading in" in rule
    assert "whatever the status of that reading" in rule
    assert "A (kind, artifact) group with no `explore` reading is charged its `deadline_s`" in rule
    assert "For the contention, load and drift sets" in rule
    assert "each reading is charged the deadline its own rule sets: 600 s where R2's deadline" \
        in rule
    assert "and K x the artifact's timeout for a drift reading, that is 20 x that timeout (R23)" \
        in rule
    assert "(600 s, R2)" not in rule
    assert ("A reading whose deadline is not under half the job's `timeout-minutes` "
            "stops the phase") in rule
    assert "the job timeout also counts the runner setup, the image build and the upload" in rule
    assert "one job per repetition" not in rule
    assert "cannot fit in a job at all" not in rule
    assert "stops the phase and asks the owner" in rule


def test_a_worker_count_qualifies_only_with_five_ok_load_repetitions() -> None:
    rule = " ".join(_rule(16).split())
    assert "and only if all 5 of its load repetitions are `ok`" in rule
    assert "If no N qualifies, the phase stops and asks the owner" in rule


def test_the_queue_depth_is_checked_on_the_load_records_against_the_derived_timeouts() -> None:
    rule = " ".join(_rule(17).split())
    assert "checked on the existing load records of the picked N, after R14 has derived the" \
        in rule
    assert "no request's wall, its queue wait plus its build, may exceed the timeout of its" in rule
    assert "under the queue-aware deadline (plan 07-02)" in rule
    assert "needs no further runner time" in rule


def test_every_solid_cache_peak_is_measured_after_the_pick_with_one_worker() -> None:
    rule = " ".join(_rule(22).split())
    assert "`W(K)` for every K from 1 to 4 is measured after R16's pick" in rule
    assert "the load mix of R15 at N = 1 with `SCREW_SOLID_CACHE` = K, 5 repetitions" in rule
    assert "every `W(K)` this rule compares comes from the same instrument" in rule
    assert "`W(4)` is not taken from R16's W" in rule
    assert "W(4) is R16's W" not in rule
    assert "With one worker, the container peak is that worker's peak" in rule


def test_the_budget_ruling_is_one_of_the_three_candidates() -> None:
    rule = " ".join(_rule(13).split())
    assert "the ruling is one of C1, C2 and C3: no other triple is offered or taken" in rule


def test_the_gzip_levels_are_compared_on_the_max_over_five_repetitions() -> None:
    rule = " ".join(_rule(19).split())
    assert "A level's seconds and bytes are each the max over 5 repetitions (R3)" in rule
    assert "the comparison below uses those maxima" in rule


def test_a_refused_pair_is_read_in_the_full_tier_and_must_return_its_refusal() -> None:
    rule = " ".join(_rule(28).split())
    assert "A pair the cost model refuses is still read in the full tier" in rule
    assert "must return its expected refusal (422 or info status)" in rule
    assert "it is not judged against the cost model" in rule
    assert "fails the tier only if it does not return its expected refusal" in " ".join(
        _rule(29).split())


def test_the_protocol_header_names_every_plan_that_applies_its_rules() -> None:
    header = " ".join(_protocol().split("\n## R1 ")[0].split())
    assert "Plans 07-03 to 07-21 apply these rules" in header
    assert "07-20 apply" not in header


def test_each_drift_build_is_gzipped_before_its_peak_is_read() -> None:
    rule = " ".join(_rule(23).split())
    assert "after the build, its export and a level-1 gzip of the output, after every build" in rule


# --- the gap rulings (PR A3): each new rule is pinned by its key phrase ---------------------------


def test_a_gzip_level_passes_at_every_stl_bound_point_against_the_adopted_level() -> None:
    rule = " ".join(_rule(19).split())
    assert "Level 1 is the start; level 6 is tried first, then level 9" in rule
    assert "costs at most 1.5x the seconds of the adopted level" in rule
    assert "it must pass at every point of the STL bound set on its own" in rule
    assert ("the points of the `stl-preview` and `stl-fine` bound sets (R14) together, "
            "10 to 16 points") in rule
    assert "Level 9 is compared with the adopted level, not with level 6" in rule
    assert "the level below it" not in rule


def test_the_export_cache_holds_the_largest_part_ok_at_all_three_artifacts() -> None:
    rule = " ".join(_rule(21).split())
    assert "of all three artifacts of the candidate part with the largest such sum" in rule
    assert ("The candidates are the `explore` parts that are admitted at all 3 artifacts "
            "and whose `explore` readings are `ok` at all 3") in rule
    assert "the gzip level-1 bytes are the upper bound" in rule
    assert "If any R19 reading shows the bytes at level 6 or 9 above the bytes at level 1" in rule
    assert "the phase stops and asks the owner" in rule
    assert "of the admitted part with the largest such sum" not in rule


def test_the_trim_is_kept_only_if_its_max_memory_current_is_lower_at_every_artifact() -> None:
    rule = " ".join(_rule(23).split())
    assert ("`_release_arenas` (the trim) is kept only if the retained memory after an export "
            "is lower with it than without, at every artifact") in rule
    assert "the *arena readings* are readings (R2) of Z(A)" in rule
    assert "5 repetitions (R3) with the trim on and 5 with it off" in rule
    assert "The measure is the cgroup's `memory.current`, read after the export" in rule
    assert ("the trim is kept only if the max with the trim on is lower than the max with it "
            "off at every artifact") in rule
    assert "`_release_arenas` is kept if" not in rule


def test_the_health_wall_is_the_healthcheck_commands_over_the_picked_ns_load_readings() -> None:
    rule = " ".join(_rule(25).split())
    assert "`--timeout` is `ceil(2 x` the max health wall under load `)` seconds" in rule
    assert "The health wall is the wall of the `HEALTHCHECK` command" in rule
    assert "the max is taken over the 5 load readings of the picked N" in rule


def test_the_dense_boundary_is_bolts_at_coarse_pitch_with_the_largest_admitted_turns() -> None:
    rule = " ".join(_rule(28).split())
    assert "The dense boundary is bolt only" in rule
    assert "for each of the 15 L11 sizes and both hands" in rule
    assert ("at the size's coarse pitch P with `s = 1.6 d`, `k = 0.6 d` and "
            "`thread_length = length = n x P`") in rule
    assert ("where n is the largest whole number of turns at which that bolt is admitted "
            "at that artifact") in rule
    assert "the largest admitted integer-turn length" not in rule


def test_the_shipped_mem_limit_is_the_larger_of_the_ones_from_w_and_from_w_k() -> None:
    r16 = " ".join(_rule(16).split())
    assert ("The `mem_limit` that ships is the larger of `mem_limit(N)` at the picked N built "
            "from this W and the one built from `W(K)` at the K R22 keeps") in r16
    r22 = " ".join(_rule(22).split())
    assert ("The `mem_limit` that ships is the larger of the one built from R16's W and the one "
            "built from `W(K)` at the K this rule keeps") in r22
    assert "both computed as R16 computes `mem_limit(N)` at the picked N" in r22
    assert "`W(4)` is not taken from R16's W" in r22


def test_gzip_and_arena_readings_are_cold_isolated_and_widen_the_envelope() -> None:
    rule = " ".join(_rule(12).split())
    assert "only a cold isolated reading widens it" in rule
    assert ("a part reading of either tier, a gzip reading of R19, an arena reading of R23, "
            "a contention reading at N = 1") in rule
    assert "a load request wall and a drift build 2 to K never widen `e`" in rule


def test_a_missing_gzip_or_arena_max_stops_the_phase() -> None:
    stop = ("(R3: a point with any repetition that is not `ok` has no max), "
            "the phase stops and asks the owner")
    assert f"If a max the gzip comparison needs is missing {stop}" in " ".join(_rule(19).split())
    assert f"If a max the arena comparison needs is missing {stop}" in " ".join(_rule(23).split())


# --- the gap ruling (PR A4): pinned by its key phrase ---------------------------------------------


def test_a_gzip_or_arena_reading_is_charged_its_deadline_and_not_an_explore_wall() -> None:
    rule = " ".join(_rule(6).split())
    assert "a reading of the contention, load, drift, gzip and arena sets is ruled below" in rule
    assert ("The R19 gzip set and the R23 arena set are charged the same way: each of their "
            "readings is charged R2's 600 s") in rule
    assert "a reading that does not fit stops the phase, by the rule above" in rule
    assert "a gzip reading also compresses its output at levels 6 and 9" in rule
    assert "the charge of neither set rests on a measured wall" in rule
    assert "a reading of the contention, load and drift sets is ruled below" not in rule


# --- the owner's ruling after the first runner reading (G25): pinned by its key phrase ------------


def test_the_nut_voids_are_walked_above_1e_2_in_a_set_of_their_own() -> None:
    r4 = " ".join(_rule(4).split())
    assert ("Above 1e-2 mm the nut voids are walked in a set of their own, the void walk "
            "(`walls-voids`)") in r4
    assert "at `r` in {3e-2, 1e-1, 3e-1, 1} mm" in r4
    assert "added after the first runner reading by the owner's ruling that R30 asks for" in r4
    assert "the void walk is not extended past 1 mm" in r4
    for number in (3, 6):
        assert "the R7 walk-down set and the void walk of R4 (d)" in " ".join(
            _rule(number).split())


def test_the_void_walk_ruling_is_an_owner_ruling_after_the_freeze_and_not_a_harness_fix() -> None:
    rulings = (PROTOCOL.parent / "07-GAP-RULINGS.md").read_text()
    assert ("\n## Gap G25 (owner ruling after the first runner reading, 2026-10-28)\n") in rulings
    assert "40646134133" in rulings
    assert re.search(r"^\| G25 \|", rulings, re.MULTILINE)
    assert "not a harness fix" in rulings
    protocol = _protocol()
    assert protocol[protocol.index("## Harness fixes"):].startswith("## Harness fixes\n\nNone yet.")
    assert not re.search(r"\bG\d+\b", protocol)


# --- the owner's ruling after the void walk (G26): pinned by its key phrase ----------------------


def test_r10_decides_on_the_rods_of_group_d_only() -> None:
    rule = " ".join(_rule(10).split())
    assert "Let F be the largest root radius `r` of a rod in `walls` group (d)" in rule
    assert ("V must be a radius the rods of group (d) hold, a power of ten from 1e-2 mm down to "
            "1e-6 mm") in rule
    assert "every rod reading of group (d) at a radius of V or more" in rule
    assert "The nut voids bear on no bound" in rule
    assert "set no F, need not be `ok` for V and are not in the R3 confirm" in rule
    assert ("The owner ruled this after the first runner reading, once the void walk had been "
            "read, as R30 asks") in rule
    assert "in `walls` group (d) and in the void walk of R4 (d)" not in rule
    assert "V must be a radius the two walks hold" not in rule
    assert "A void reading that fails at 1 mm puts V above the walk" not in rule
    assert "for every size, hand, rod and void" not in rule


def test_the_r10_confirm_reads_the_rods_only() -> None:
    rule = " ".join(_rule(3).split())
    assert ("which `walls` groups (c) and (d) already hold; for R10 the confirm reads the rods "
            "of group (d) only") in rule
    assert "where V lies in the void walk" not in rule


def test_the_rods_only_ruling_is_an_owner_ruling_after_the_void_walk_and_not_a_harness_fix(
) -> None:
    rulings = (PROTOCOL.parent / "07-GAP-RULINGS.md").read_text()
    assert "\n## Gap G26 (owner ruling after the void walk, 2026-10-28)\n" in rulings
    for figure in ("40665307964", "0.1250", "0.1200", "0.7852", "0.7667", "not a harness fix"):
        assert figure in rulings
    assert re.search(r"^\| G26 \| R3, R10 \|", rulings, re.MULTILINE)
    protocol = _protocol()
    assert protocol[protocol.index("## Harness fixes"):].startswith("## Harness fixes\n\nNone yet.")
    assert not re.search(r"\bG\d+\b", protocol)
    assert not re.search(r"\b\d{11}\b", protocol)


def test_the_nut_diameter_gets_no_wall_and_stays_under_the_shared_ceiling_below_its_refusal(
) -> None:
    rule = " ".join(_rule(8).split())
    assert "The nut `d` gets no constant of its own" in rule
    assert "`capped` in all 5 confirm repetitions, and its reading at 1e4 is `refused`" in rule
    assert "the cost model's admission (R12) and the timeouts bound a large nut, not a wall" in rule
    assert ("stays under the shared `MAX_FIELD_MM` only while that value lies below the nut `d`'s "
            "first refused decade (1e4)") in rule
    assert "A shared value at or above that decade stops the phase and asks the owner" in rule
    assert "added after the first runner reading by the owner's ruling that R30 asks for" in rule
    rulings = (PROTOCOL.parent / "07-GAP-RULINGS.md").read_text()
    assert "\n## Gap G27 (owner ruling after the walls confirm, 2026-10-28)\n" in rulings
    assert re.search(r"^\| G27 \| R8 \| R8 writes no `MAX_NUT_D_MM`", rulings, re.MULTILINE)


# --- the owner's ruling on the head ratios the fit never saw (G28): pinned by its key phrases ----


def test_a_head_ratio_outside_its_band_is_predicted_no_lower_than_anywhere_in_the_band() -> None:
    rule = " ".join(_rule(11).split())
    assert ("A part whose head ratio lies above the band the fit saw is predicted no lower than "
            "anywhere in that band, and one whose ratio lies below it no lower than at the band's "
            "low edge") in rule
    assert "the bolt's k / d and s / d and the nut's s / d and m / d" in rule
    assert "its smallest and largest value over the fitted points of its kind" in rule
    assert ("computed from the records by code and shipped with the coefficients, never "
            "typed") in rule
    assert ("a ratio above its band taking both edges (the smallest and the largest) and a ratio "
            "below it the smallest only") in rule
    assert "a smaller head never costs more than one at the low edge" in rule
    assert "the prediction is the largest of these, target by target" in rule
    assert "Inside every band the prediction is the fit's own, unchanged" in rule
    assert ("a reading above its enveloped prediction stops the phase for the owner and does not "
            "widen `e`") in rule
    assert "added after the first runner reading by the owner's ruling that R30 asks for" in rule
    assert "nearest" not in rule
    rulings = (PROTOCOL.parent / "07-GAP-RULINGS.md").read_text()
    assert ("\n## Gap G28 (owner ruling on the head ratios the cost model was not fitted on, "
            "2026-10-29)\n") in rulings
    for reply in ('"Clamp k/d, verify on runner (Recommended)"',
                  '"All head ratios, max-of (Recommended)"',
                  '"B: max over the band (Recommended)"', '"2: one-sided B (Recommended)"',
                  "22 failed, 4409 passed", "d869b87", "40646117094",
                  "40646125666", "not a harness fix"):
        assert reply in rulings, reply
    assert re.search(r"^\| G28 \| R11 \|", rulings, re.MULTILINE)
    protocol = _protocol()
    assert protocol[protocol.index("## Harness fixes"):].startswith("## Harness fixes\n\nNone yet.")
    assert not re.search(r"\bG\d+\b", protocol)
    assert not re.search(r"\b\d{11}\b", protocol)


def test_a_bolt_below_the_fitted_turns_was_read_on_the_runner_and_is_now_refused() -> None:
    """G29 had the runner read such bolts; G30, after one of them read over its envelope, refuses
    them at every artifact instead of predicting them."""
    rule = " ".join(_rule(11).split())
    assert ("A bolt whose built thread has fewer turns than the fewest among the fitted bolt "
            "points (computed from the records by code, never typed) is refused before any build "
            "at every artifact, with the budget's refusal (B-02) naming the fields that set its "
            "turns: the pitch, the length and the thread length") in rule
    assert "predicted by the fit as it stands" not in rule
    assert ("per artifact, two bolts below that count that the walls and the fit's admission "
            "admitted: the one closest to the budget and the first in catalogue order") in rule
    assert "Those readings widen no `e`" in rule
    assert rule.count("stops the phase for the owner and does not widen `e`") == 1
    assert rule.count("added after the first runner reading by the owner's ruling that R30 asks "
                      "for") == 3
    rulings = (PROTOCOL.parent / "07-GAP-RULINGS.md").read_text()
    assert ("\n## Gap G29 (owner ruling on named threads below the fitted turns, 2026-10-29)\n"
            in rulings)
    for evidence in ('"Add to 07-15 (Recommended)"', "52dcf95", "40646117094", "40646125666"):
        assert evidence in rulings, evidence
    assert re.search(r"^\| G29 \| R11 \|", rulings, re.MULTILINE)


# --- the owner's rulings after the out-of-band check (G30) and on the bound set (G31) -----------


def test_the_out_of_band_nut_readings_widen_e_and_the_bolt_readings_do_not() -> None:
    rule = " ".join(_rule(11).split())
    assert ("After that stop, the owner ruled that a nut reading of these parts above its "
            "enveloped prediction widens `e` as a cold isolated reading does (R12), and that a "
            "bolt reading of them widens no `e`") in rule
    rulings = (PROTOCOL.parent / "07-GAP-RULINGS.md").read_text()
    assert "\n## Gap G30 (owner ruling after the out-of-band check, 2026-10-30)\n" in rulings
    for evidence in ('"1: widen nuts, guard G29 (Recommended)"', "40909768713", "196ef2e",
                     "not a harness fix", "0 of the 294 bolt catalogue rows"):
        assert evidence in rulings, evidence
    assert re.search(r"^\| G30 \| R11 \|", rulings, re.MULTILINE)
    owner = (PROTOCOL.parent / "07-OWNER-RULINGS.md").read_text()
    assert ("\n## B-02 and B-03: a bolt below the fitted turns is refused at every artifact "
            "(2026-10-30, G30)\n") in owner
    assert '"1: widen nuts, guard G29 (Recommended)"' in owner


def test_every_bound_candidate_has_an_ok_explore_reading_at_every_artifact() -> None:
    rule = " ".join(_rule(14).split())
    assert ("The candidates are the admitted `explore` points at that artifact whose `explore` "
            "reading is `ok` at every artifact") in rule
    assert "for the two measured choices" not in rule
    assert "one candidate of the same artifact" in rule
    assert "The partner of each other slot is the candidate other than P" in rule
    assert "A slot that holds no candidate leaves that (P, N) unrunnable" in rule
    assert ("only the points it changed are read again, at 5 repetitions, and the earlier "
            "readings of the points they replace are kept as records and decide nothing") in rule
    assert "R19's gzip set takes the bound set's points, so the same holds there" in rule
    assert rule.count("added after the first runner reading by the owner's ruling that R30 asks "
                      "for") == 1
    rulings = (PROTOCOL.parent / "07-GAP-RULINGS.md").read_text()
    assert ("\n## Gap G31 (owner ruling on the kernel-refused nuts in the bound set, "
            "2026-10-30)\n") in rulings
    for evidence in ('"Exclude, rerun preview (Recommended)"', "40907549180", "40909739628",
                     "not a harness fix"):
        assert evidence in rulings, evidence
    assert re.search(r"^\| G31 \| R14, R19 \|", rulings, re.MULTILINE)
    protocol = _protocol()
    assert protocol[protocol.index("## Harness fixes"):].startswith("## Harness fixes\n\nNone yet.")
    assert not re.search(r"\bG\d+\b", protocol)
    assert not re.search(r"\b\d{11}\b", protocol)


# --- the owner's ruling on the drift stop (G32): pinned by its key phrases ----------------------


def test_the_drift_is_counted_in_w_under_a_plateau_read_over_60_builds() -> None:
    r16 = " ".join(_rule(16).split())
    assert ("W is also at least the largest peak after any build of R23's drift readings, the "
            "20-build and the 60-build one, once R23's plateau holds") in r16
    assert r16.count("added after the first runner reading by the owner's ruling that R30 asks "
                     "for") == 1
    r23 = " ".join(_rule(23).split())
    assert ("`max_tasks_per_child` stays unset unless the plateau (below) fails for any "
            "artifact") in r23
    assert "shows growth above its allowance for any artifact" not in r23
    assert "A drift above its allowance does not stop the phase by itself" in r23
    assert ("A second drift reading builds the same Z(A), at the same three artifacts in the "
            "same order, K = 60 times, 5 repetitions, each with a deadline of 60 x the "
            "artifact's timeout, which R6 charges it") in r23
    assert ("the plateau difference is the max peak over builds 41 to 60 minus the max peak "
            "over builds 21 to 40") in r23
    assert ("0.10 x the smallest peak after build 1 among the repetitions of both drift "
            "readings of that artifact") in r23
    assert ("If any artifact misses it, the phase stops and asks the owner again, and the next "
            "step is recycling") in r23
    assert "This criterion was fixed before the 60-build reading was taken" in r23
    assert r23.count("added after the first runner reading by the owner's ruling that R30 asks "
                     "for") == 1
    rulings = (PROTOCOL.parent / "07-GAP-RULINGS.md").read_text()
    assert "\n## Gap G32 (owner ruling on the drift stop, 2026-10-30)\n" in rulings
    for evidence in ('"1 + longer drift run (Recommended)"', "41016507364", "1716760576",
                     "378d58c", "not a harness fix"):
        assert evidence in rulings, evidence
    assert re.search(r"^\| G32 \| R16, R23 \|", rulings, re.MULTILINE)
    owner = (PROTOCOL.parent / "07-OWNER-RULINGS.md").read_text()
    assert ("\n## R16 and R23: the drift is counted in W, under a plateau read over 60 builds "
            "(2026-10-30, G32)\n") in owner
    assert '"1 + longer drift run (Recommended)"' in owner
    protocol = _protocol()
    assert protocol[protocol.index("## Harness fixes"):].startswith("## Harness fixes\n\nNone yet.")
    assert not re.search(r"\bG\d+\b", protocol)
    assert not re.search(r"\b\d{11}\b", protocol)


# --- the required tier (07-18): judge and check ---------------------------------------------------

LIMIT = {"bytes": 1000.0, "seconds": 10.0, "peak": 5000.0}


def _boundary_point(label: str = "b0", artifact: str = "stl-preview", timeout: float = 20.0,
                    limit: Mapping[str, float] = LIMIT) -> dict[str, object]:
    return {"label": label, "kind": "bolt", "params": {"d": 6.0}, "artifact": artifact,
            "charge_s": 1.0, "timeout_s": timeout, "limit": dict(limit)}


def _tier_reading(label: str = "b0", status: str = "ok", build: float = 4.0,
                  export: float = 1.0, size: float = 900, peak: float = 4000) -> dict[str, object]:
    reading: dict[str, object] = {"type": "reading", "label": label, "kind": "bolt",
                                  "params": {"d": 6.0}, "artifact": "stl-preview", "rep": 1,
                                  "status": status, "wall_s": 99.0}
    if status == "ok":
        reading.update(build_s=build, export_s=export, bytes=size, memory_peak_bytes=peak)
    return reading


def _loaded(tmp_path: Path, **over: object) -> oper.BoundaryPoint:
    path = tmp_path / "boundary.json"
    path.write_text(json.dumps({"points": [{**_boundary_point(), **over}]}))
    return oper.load_boundary(path)[0]


def test_an_ok_reading_under_every_limit_and_its_timeout_passes(tmp_path: Path) -> None:
    assert oper.judge(_loaded(tmp_path), _tier_reading()) == []


@pytest.mark.parametrize(("reading", "naming"), [
    (_tier_reading(status="refused"), "refused, not ok"),
    (_tier_reading(status="killed"), "killed, not ok"),
    (_tier_reading(status="capped"), "capped, not ok"),
    (_tier_reading(build=9.0, export=2.0), "seconds 11.0 over its limit 10.0"),
    (_tier_reading(size=1001), "bytes 1001 over its limit 1000.0"),
    (_tier_reading(peak=5001), "peak 5001 over its limit 5000.0"),
])
def test_each_failure_r29_names_fails_the_point_and_names_it(
        reading: dict[str, object], naming: str, tmp_path: Path) -> None:
    failures = oper.judge(_loaded(tmp_path), reading)
    assert len(failures) == 1
    assert failures[0].startswith("b0 at stl-preview: ")
    assert naming in failures[0]


def test_a_cold_wall_over_its_timeout_fails_even_under_its_seconds_limit(tmp_path: Path) -> None:
    point = _loaded(tmp_path, timeout_s=4.5)
    assert oper.judge(point, _tier_reading(build=4.0, export=1.0)) == [
        "b0 at stl-preview: cold wall 5.0 s over its timeout 4.5 s"]


def test_the_cold_wall_is_build_plus_export_and_never_the_container_wall(tmp_path: Path) -> None:
    assert oper.judge(_loaded(tmp_path, timeout_s=5.0), {**_tier_reading(), "wall_s": 1e6}) == []


def test_a_figure_at_its_limit_passes_and_the_next_float_above_fails(tmp_path: Path) -> None:
    point = _loaded(tmp_path, timeout_s=10.0)
    at = _tier_reading(build=9.0, export=1.0, size=1000.0, peak=5000.0)
    assert oper.judge(point, at) == []
    above = {"bytes": _tier_reading(size=math.nextafter(1000.0, math.inf)),
             "peak": _tier_reading(peak=math.nextafter(5000.0, math.inf)),
             "seconds": _tier_reading(build=math.nextafter(9.0, math.inf), export=1.0)}
    for target, reading in above.items():
        assert [f for f in oper.judge(point, reading) if f"{target} " in f], target


@pytest.mark.parametrize("over", [
    {"timeout_s": 0}, {"timeout_s": "26"}, {"limit": {"bytes": 1.0, "seconds": 1.0}},
    {"limit": {"bytes": 1.0, "seconds": 1.0, "peak": float("nan")}}, {"artifact": "png"},
])
def test_a_boundary_point_that_breaks_the_schema_is_refused(over: dict[str, object],
                                                            tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"boundary|artifact"):
        _loaded(tmp_path, **over)


def _stub_tier(monkeypatch: pytest.MonkeyPatch,
               readings: Mapping[str, dict[str, object]]) -> list[tuple[str, int, float]]:
    """`run_reading` answers each label from `readings` and records the label, the rep and the
    deadline it was asked for; no Docker."""
    taken: list[tuple[str, int, float]] = []

    def fake_reading(point: oper.Point, rep: int, image: str, cap: int, deadline_s: float,
                     versions: Mapping[str, str] | None = None) -> dict[str, object]:
        taken.append((point.label, rep, deadline_s))
        assert cap == oper.CAP_BYTES
        return dict(readings[point.label])

    monkeypatch.setattr(oper, "run_reading", fake_reading)
    monkeypatch.setattr(oper, "_image_versions", lambda image: {"cadquery": "2.8.0"})
    monkeypatch.setattr(oper, "header", lambda image, versions: {
        "type": "header", "image": image, "GITHUB_RUN_ID": "7"})
    return taken


def _tier_file(tmp_path: Path, labels: Iterable[str]) -> Path:
    path = tmp_path / "boundary.json"
    path.write_text(json.dumps({"points": [_boundary_point(label) for label in labels]}))
    return path


def test_check_reads_every_point_once_cold_and_exits_0_with_a_table(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    taken = _stub_tier(monkeypatch, {"b0": _tier_reading("b0"), "b1": _tier_reading("b1")})
    assert oper.main(["check", str(_tier_file(tmp_path, ["b0", "b1"])), "--image", "i"]) == 0
    assert taken == [("b0", 1, oper.DEADLINE_S), ("b1", 1, oper.DEADLINE_S)]
    out = capsys.readouterr().out
    assert "2 points, 0 failures." in out
    assert "| b0 | stl-preview | ok | 5.000 | 20 | 10.000 | 900 | 1000 | 4000 | 5000 |" in out
    assert "### Failures" not in out
    assert not list(tmp_path.glob("*.jsonl"))


def test_check_exits_1_naming_every_failing_point(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _stub_tier(monkeypatch, {"b0": _tier_reading("b0", size=2000),
                             "b1": _tier_reading("b1"), "b2": _tier_reading("b2", "crashed")})
    assert oper.main(["check", str(_tier_file(tmp_path, ["b0", "b1", "b2"])),
                      "--image", "i"]) == 1
    out = capsys.readouterr().out
    assert "3 points, 2 failures." in out
    assert "- b0 at stl-preview: bytes 2000 over its limit 1000.0" in out
    assert "- b2 at stl-preview: crashed, not ok" in out
    assert "| b2 | stl-preview | crashed | - | 20 | 10.000 | - | 1000 | - | 5000 |" in out


@pytest.mark.parametrize("text", ["", "\n", '{"points": []}'])
def test_check_of_a_file_with_no_point_is_not_a_pass(
        text: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    taken = _stub_tier(monkeypatch, {})
    path = tmp_path / "boundary.json"
    path.write_text(text)
    assert oper.main(["check", str(path), "--image", "i"]) == 1
    assert taken == []
    assert "no reading is not a pass" in capsys.readouterr().err


def test_check_out_writes_the_header_and_every_reading_in_the_run_format(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    readings = {"b0": _tier_reading("b0"), "b1": _tier_reading("b1", "refused")}
    _stub_tier(monkeypatch, readings)
    out = tmp_path / "bounds-records.jsonl"
    assert oper.main(["check", str(_tier_file(tmp_path, ["b0", "b1"])), "--image", "i",
                      "--out", str(out)]) == 1
    headers, found = oper._read_records([str(out)])
    assert headers == [{"type": "header", "image": "i", "GITHUB_RUN_ID": "7"}]
    assert found == [readings["b0"], readings["b1"]]
    rows = oper.summarize(found, [1])
    assert [(row["label"], row["status"]) for row in rows] == [("b0", "ok"), ("b1", "refused")]


# --- the bounds job in ci.yml (07-18; D-12, D-15, L08, T-07-44, T-07-45) ------------------------

CI_YML = REPO_ROOT / ".github" / "workflows" / "ci.yml"
REQUIRED_JOBS = REPO_ROOT / ".github" / "workflows" / "required-jobs.txt"


def _ci_job(job_id: str) -> str:
    """The text of one ci.yml job: from its two-space id line to the next one."""
    text = CI_YML.read_text()
    match = re.search(rf"^  {job_id}:\n((?:(?!  \S).*\n?)*)", text, re.MULTILINE)
    assert match is not None, f"no {job_id} job in ci.yml"
    return match.group(1)


def _steps(job: str) -> list[str]:
    """A job's steps, each the text from its `- ` line to the next."""
    return re.split(r"^      - ", job, flags=re.MULTILINE)[1:]


def _step_with(job: str, *needles: str) -> str:
    found = [step for step in _steps(job) if all(needle in step for needle in needles)]
    assert len(found) == 1, f"{len(found)} steps hold {needles}"
    return found[0]


def test_the_bounds_job_checks_the_boundary_set_in_the_image_the_image_job_built() -> None:
    job = _ci_job("bounds")
    assert re.search(r"^    needs: image$", job, re.MULTILINE)
    assert re.search(r"^    runs-on: ubuntu-latest$", job, re.MULTILINE)
    download = _step_with(job, "actions/download-artifact@v4")
    assert re.search(r"^\s+name: screw-ci-image$", download, re.MULTILINE)
    assert "gunzip -c screw-ci.tar.gz | docker load" in _step_with(job, "docker load")
    python = _step_with(job, "actions/setup-python@v5")
    assert 'python-version: "3.12"' in python
    assert "cache" not in python
    check = _step_with(job, "bench.oper check")
    assert ("python3 -m bench.oper check tests/data/oper_boundary.json --image screw:ci "
            "--out bounds-records.jsonl") in check
    assert '"$GITHUB_STEP_SUMMARY"' in check
    # The table is piped into the summary, so the step must fail with the check, not with tee.
    assert re.search(r"^\s+shell: bash$", check, re.MULTILINE)
    assert ".venv" not in job
    assert "make " not in job


def test_the_bounds_job_reads_the_repository_and_holds_no_secret() -> None:
    job = _ci_job("bounds")
    permissions = re.search(r"^    permissions:\n((?:      .*\n)+)", job, re.MULTILINE)
    assert permissions is not None
    assert permissions.group(1).splitlines() == ["      contents: read"]
    text = CI_YML.read_text()
    assert "secrets." not in text
    assert not re.search(r"^\s+github-token:", text, re.MULTILINE)
    assert not re.search(r"^\s*pull_request_target\s*:", text, re.MULTILINE)
    assert "\non:\n  push:\n    branches: [main]\n  pull_request:\n\n" in text


def test_the_bounds_job_keeps_the_readings_of_a_red_run_for_seven_days() -> None:
    upload = _step_with(_ci_job("bounds"), "actions/upload-artifact@v4")
    assert re.search(r"^\s+if: always\(\)$", upload, re.MULTILINE)
    assert re.search(r"^\s+name: bounds-records$", upload, re.MULTILINE)
    assert re.search(r"^\s+path: bounds-records\.jsonl$", upload, re.MULTILINE)
    assert re.search(r"^\s+retention-days: 7$", upload, re.MULTILINE)


def test_the_image_job_hands_its_image_on_for_one_day() -> None:
    job = _ci_job("image")
    save = _step_with(job, "docker save")
    assert "docker save screw:ci | gzip -1 > screw-ci.tar.gz" in save
    assert re.search(r"^\s+shell: bash$", save, re.MULTILINE)
    upload = _step_with(job, "actions/upload-artifact@v4")
    assert re.search(r"^\s+name: screw-ci-image$", upload, re.MULTILINE)
    assert re.search(r"^\s+path: screw-ci\.tar\.gz$", upload, re.MULTILINE)
    assert re.search(r"^\s+retention-days: 1$", upload, re.MULTILINE)


def test_bounds_is_a_job_make_pr_land_requires() -> None:
    lines = REQUIRED_JOBS.read_text().splitlines()
    assert lines.count("bounds") == 1


def test_the_bounds_job_timeout_leaves_half_for_a_slower_runner() -> None:
    """R6's precedent: the readings take at most half the job's `timeout-minutes`, the other half
    left for a slower runner instance, the image load and the upload. A reading is estimated by
    its explore container wall, or by its timeout where explore did not read it ok (R27's
    charge)."""
    match = re.search(r"^    timeout-minutes: (\d+)$", _ci_job("bounds"), re.MULTILINE)
    assert match is not None
    document = json.loads((REPO_ROOT / "tests" / "data" / "oper_boundary.json").read_text())
    explore = dict(str(entry).split("=", 1) for entry in document["sources"])["explore"]
    files = sorted(str(path) for path in (REPO_ROOT / explore).glob("*/*.jsonl"))
    walls = {(r["label"], r["artifact"]): r for r in oper._read_records(files)[1]}
    estimate = 0.0
    for point in document["points"]:
        reading = walls[point["label"], point["artifact"]]
        wall = reading["wall_s"]
        assert isinstance(wall, int | float)
        estimate += wall if reading["status"] == "ok" else max(wall, point["timeout_s"])
    assert estimate < int(match.group(1)) * 60 / 2


def test_the_required_tier_is_read_in_shards_each_point_once() -> None:
    rule = " ".join(_rule(27).split())
    assert "The tier is read in parallel shards, one job each, all on the one image" in rule
    assert ("a shard is the longest run of consecutive points not yet placed whose summed "
            "estimate stays under 600 s, D-12's 10 minutes, so every point is in exactly one "
            "shard and is read once") in rule
    assert ("A point's estimate is the container wall (`wall_s`) of its `explore` reading when "
            "that reading is `ok`, and otherwise the larger of that wall and its artifact's "
            "timeout") in rule
    assert ("Each shard job's `timeout-minutes` is at least twice its shard's summed "
            "estimate") in rule
    assert "The 600 s of step 5 per artifact is unchanged" in rule
    rulings = (PROTOCOL.parent / "07-GAP-RULINGS.md").read_text()
    assert "\n## Gap G34 (owner ruling on the required tier's wall time, 2026-10-30)\n" in rulings
    for evidence in ('"Shard into parallel jobs (Recommended)"', "41042483745", "35.5 min",
                     "not a harness fix"):
        assert evidence in rulings, evidence
    assert re.search(r"^\| G34 \| R27, D-12 \|", rulings, re.MULTILINE)


def test_a_predicted_float_may_move_by_the_measured_libm_difference_and_nothing_else() -> None:
    rule = " ".join(_rule(27).split())
    assert ("every value must be the same except a float computed from the cost model's "
            "prediction (an edge ratio of step 2, a limit of R29), which may differ from the "
            "committed one by a relative difference of at most 2^-51, that is 2 x 2^-52") in rule
    assert ("2 of the 2559 such floats in the two files moved by one ulp from the files written "
            "on macOS, the larger by a relative 1.459 x 2^-52, and no other value moved") in rule
    assert rule.count("added after the first runner reading by the owner's ruling that R30 asks "
                      "for") == 2
    rulings = (PROTOCOL.parent / "07-GAP-RULINGS.md").read_text()
    assert ("\n## Gap G33 (owner ruling on the regeneration checks across platforms, "
            "2026-10-30)\n") in rulings
    for evidence in ('"A: tolerance on limits (Recommended)"', "41048346068",
                     "3.239877599502309e-16", "6801399.663168809", "not a harness fix"):
        assert evidence in rulings, evidence
    assert re.search(r"^\| G33 \| R27 \|", rulings, re.MULTILINE)
    owner = (PROTOCOL.parent / "07-OWNER-RULINGS.md").read_text()
    assert ("\n## R27: the required tier, after its first runner reading (2026-10-30, G33, "
            "G34)\n") in owner
    for reply in ('"B: fix\n   in-wall debt first (Recommended)"',
                  '"A: tolerance on limits (Recommended)"',
                  '"Shard into parallel jobs (Recommended)"'):
        assert reply in owner, reply
