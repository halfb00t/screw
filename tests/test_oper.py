"""The operability runner harness (07-01): one reading per fresh container, no number it did not
measure.

Everything here is synthetic: a fake `/proc` and cgroup tree, canned child lines, text pins over
the workflow. No Docker and, except for the one end-to-end child test, no kernel. What these
tests protect is L02 for the harness: a capped, killed, crashed, refused or cgroup-blind reading
must come out as a status and never as a plausible figure.
"""

from __future__ import annotations

import json
import re
import statistics
import subprocess
import sys
from collections.abc import Mapping
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
    row = oper.summarize(readings)[0]
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
    assert oper.main(["summarize", str(path)]) == 0
    assert "crashed" in capsys.readouterr().out
    ok = tmp_path / "ok.jsonl"
    ok.write_text("\n".join(lines[:3]) + "\n")
    assert oper.main(["summarize", str(ok)]) == 0
    assert "build_s" in capsys.readouterr().out
    assert oper.main(["summarize", str(ok), "--markdown"]) == 0
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
