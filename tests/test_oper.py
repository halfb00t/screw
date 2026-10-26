"""The operability runner harness (07-01): one reading per fresh container, no number it did not
measure.

Everything here is synthetic: a fake `/proc` and cgroup tree, canned child lines, text pins over
the workflow. No Docker and, except for the one end-to-end child test, no kernel. What these
tests protect is L02 for the harness: a capped, killed, crashed, refused or cgroup-blind reading
must come out as a status and never as a plausible figure.
"""

from __future__ import annotations

import json
import statistics
import subprocess
import sys
from pathlib import Path

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
             artifact: str = "stl-preview") -> dict[str, object]:
    record: dict[str, object] = {"type": "reading", "label": label, "artifact": artifact,
                                 "rep": rep, "status": status}
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
