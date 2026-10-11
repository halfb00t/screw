"""The command line: flags generated from the registry, refusals that name the argument,
and the exit codes a script depends on."""

from __future__ import annotations

import json
import re
import shlex
import struct
import subprocess
import sys
from pathlib import Path

import pytest

from screw import __version__, cli
from screw.calc import derive, download_refusal
from screw.params import KINDS, BoltParams

WARNING = ("warning: plain-cut thread ends, no tip chamfer or under-head fillet; "
           "not a product build")


def _exit_code(argv: list[str]) -> str | int | None:
    with pytest.raises(SystemExit) as exc:
        cli.main(argv)
    return exc.value.code


def test_info_prints_the_part_info_document(capsys: pytest.CaptureFixture[str]) -> None:
    cli.main(["info", "bolt"])
    assert capsys.readouterr().out == derive(BoltParams()).model_dump_json(indent=2) + "\n"


def test_info_reads_every_field_flag(capsys: pytest.CaptureFixture[str]) -> None:
    cli.main(["info", "bolt", "--d", "8", "--pitch", "1.25", "--length", "30"])
    rows = {r["key"]: r["value"] for r in json.loads(capsys.readouterr().out)["rows"]}
    assert (rows["d"], rows["pitch"], rows["length"]) == (8.0, 1.25, 30.0)


def test_export_writes_stl_and_step_and_warns_on_stderr(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    stl = tmp_path / "b.stl"
    cli.main(["export", "bolt", "-o", str(stl), "--quality", "preview"])
    data = stl.read_bytes()
    (triangles,) = struct.unpack("<I", data[80:84])
    assert triangles > 0
    assert len(data) == 84 + 50 * triangles
    assert WARNING in capsys.readouterr().err

    step = tmp_path / "b.step"
    cli.main(["export", "bolt", "-o", str(step)])
    assert step.read_bytes().startswith(b"ISO-10303-21;")
    assert WARNING in capsys.readouterr().err


def test_the_format_flag_overrides_the_extension(tmp_path: Path) -> None:
    out = tmp_path / "part.dat"
    cli.main(["export", "bolt", "-o", str(out), "--format", "step"])
    assert out.read_bytes().startswith(b"ISO-10303-21;")


def test_the_hand_flags_build_the_hand_they_name(tmp_path: Path) -> None:
    # The solid under `left_hand=True` is proven left-handed by the probe in tests/test_solid.py;
    # here the flag must reach it, and `--no-left-hand` must reach the default.
    from screw.solid import export

    def stl(*flags: str) -> bytes:
        out = tmp_path / "x.stl"
        cli.main(["export", "bolt", "-o", str(out), "--quality", "preview", *flags])
        return out.read_bytes()

    left = export(BoltParams(left_hand=True), "stl", "preview")
    right = export(BoltParams(), "stl", "preview")
    assert left != right
    assert stl("--left-hand") == left
    assert stl("--no-left-hand") == right
    assert stl() == right


def test_a_value_after_the_hand_flag_is_refused_not_read_as_true(
        capsys: pytest.CaptureFixture[str]) -> None:
    assert _exit_code(["info", "bolt", "--left-hand", "false"]) == 2
    assert "false" in capsys.readouterr().err


@pytest.mark.parametrize("argv", [
    ["info", "bolt", "--m", "5"],
    ["info", "bolt", "--lenght", "5"],
    ["serve", "--m", "5"],
])
def test_a_foreign_flag_exits_2_naming_it(
        argv: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    assert _exit_code(argv) == 2
    assert argv[-2] in capsys.readouterr().err


@pytest.mark.parametrize("argv", [
    ["info", "bolt", "--len", "5"],
    ["info", "bolt", "--pit", "1"],
    ["export", "bolt", "-o", "unused.stl", "--len", "5"],
    ["serve", "--hos", "0.0.0.0"],
])
def test_a_prefix_of_a_real_flag_is_refused(
        argv: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    # argparse binds `--len` to `--length` unless allow_abbrev=False is on every parser;
    # a prefix quietly choosing a field is a parameter the user did not set (L02).
    assert _exit_code(argv) == 2
    assert "unrecognized arguments" in capsys.readouterr().err


@pytest.mark.parametrize(("field", "value"), [
    ("d", "0"), ("d", "inf"), ("d", "nan"), ("d", "100001"), ("length", "-1"),
    ("s", "0"), ("s", "-1"), ("s", "inf"), ("s", "nan"), ("s", "100001"),
    ("k", "0"), ("k", "-1"), ("k", "inf"), ("k", "nan"), ("k", "100001"),
])
def test_a_bad_value_exits_2_naming_the_field(
        field: str, value: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert _exit_code(["info", "bolt", f"--{field}", value]) == 2
    assert f"error: {field}:" in capsys.readouterr().err


@pytest.mark.parametrize("field", ["s", "k"])
def test_a_head_value_that_is_text_exits_2_naming_the_flag(
        field: str, capsys: pytest.CaptureFixture[str]) -> None:
    # argparse refuses text before the model sees it, and names the flag.
    assert _exit_code(["info", "bolt", f"--{field}", "text"]) == 2
    assert f"argument --{field}: invalid float value: 'text'" in capsys.readouterr().err


@pytest.mark.parametrize(("argv", "prefix"), [
    (["info", "bolt", "--pitch", "6"], "error: d and pitch:"),
    (["info", "bolt", "--length", "300"], "error: length and pitch:"),
    (["info", "bolt", "--s", "6"], "error: s and d: "),
    (["export", "bolt", "-o", "unused.stl", "--s", "5"], "error: s and d: "),
    # length / pitch is past the float range: exit 2, not the OverflowError traceback (CR-01)
    (["info", "bolt", "--pitch", "5e-324"], "error: length and pitch: inf turns"),
    (["info", "bolt", "--pitch", "1e-310", "--length", "1e5"],
     "error: length and pitch: inf turns"),
    (["export", "bolt", "-o", "unused.stl", "--pitch", "1e300"], "error: d and pitch:"),
])
def test_a_thread_that_cannot_be_made_exits_2_naming_both_fields(
        argv: list[str], prefix: str, capsys: pytest.CaptureFixture[str]) -> None:
    # The CLI prints no loc for a model-level error, so the message text names the fields.
    assert _exit_code(argv) == 2
    err = capsys.readouterr().err
    assert prefix in err
    assert "Traceback" not in err


def test_the_measured_m4_250_turn_row_is_accepted_on_the_command_line(
        capsys: pytest.CaptureFixture[str]) -> None:
    cli.main(["info", "bolt", "--d", "4", "--pitch", "0.7", "--length", "175"])
    assert json.loads(capsys.readouterr().out)["kind"] == "bolt"


@pytest.mark.parametrize("argv", [
    ["info", "nut"],
    ["export", "nut", "-o", "unused.stl"],
])
def test_an_unknown_kind_exits_2(argv: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    assert _exit_code(argv) == 2
    err = capsys.readouterr().err
    assert "nut" in err
    assert "bolt" in err      # the valid choices are named


def test_unknown_output_extension_is_refused(tmp_path: Path) -> None:
    out = tmp_path / "b.obj"
    # A string SystemExit prints it and exits 1, not argparse's 2.
    assert _exit_code(["export", "bolt", "-o", str(out)]) == (
        "error: output must end in .stl or .step (or pass --format)")
    assert not out.exists()


def test_an_unknown_output_extension_exits_1_from_the_real_process(tmp_path: Path) -> None:
    """The exit code a shell script sees, not just SystemExit's `code` attribute."""
    out = tmp_path / "b.obj"
    result = subprocess.run(
        [sys.executable, "-m", "screw.cli", "export", "bolt", "-o", str(out)],
        capture_output=True, text=True, check=False)
    assert result.returncode == 1
    assert "error: output must end in .stl or .step (or pass --format)" in result.stderr
    assert not out.exists()


def test_a_kernel_failure_stops_the_export_and_writes_nothing(tmp_path: Path) -> None:
    # These pass the model (all positive) and the kernel builds one valid solid of them whose
    # volume is off the closed form (+9.59e-03 in the research probe): the gate refuses it.
    out = tmp_path / "b.stl"
    code = _exit_code(["export", "bolt", "-o", str(out), "--d", "0.001", "--pitch", "0.0001",
                       "--length", "0.01"])
    assert isinstance(code, str)
    assert code.startswith("error: ")
    assert not out.exists()


def test_a_length_too_short_to_model_ends_with_an_error_naming_it_and_writes_nothing(
        tmp_path: Path) -> None:
    out = tmp_path / "b.stl"
    code = _exit_code(["export", "bolt", "-o", str(out), "--length", "1e-9"])
    assert isinstance(code, str)
    assert code.startswith("error: ")
    assert "length" in code
    assert not out.exists()


def test_a_length_too_short_to_model_exits_1_from_the_real_process(tmp_path: Path) -> None:
    """Not a worker death: the process says why and returns 1 instead of dying on a signal."""
    out = tmp_path / "b.stl"
    result = subprocess.run(
        [sys.executable, "-m", "screw.cli", "export", "bolt", "-o", str(out), "--length", "1e-9"],
        capture_output=True, text=True, check=False)
    assert result.returncode == 1
    assert "error: " in result.stderr
    assert "length" in result.stderr
    assert not out.exists()


@pytest.mark.parametrize("command", ["info", "export"])
@pytest.mark.parametrize("kind", list(KINDS))
def test_the_flags_follow_the_model_fields_in_order(
        command: str, kind: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert _exit_code([command, kind, "--help"]) == 0
    out = capsys.readouterr().out
    _, _, after = out.partition(f"{kind} parameters (defaults in brackets):\n")
    assert after      # the group header must have been found
    flags = re.findall(r"^\s+(--[a-z][a-z-]*)", after, re.MULTILINE)
    assert flags == ["--" + name.replace("_", "-") for name in KINDS[kind].model_fields]


def test_version_prints_the_package_version(capsys: pytest.CaptureFixture[str]) -> None:
    assert _exit_code(["--version"]) == 0
    assert capsys.readouterr().out == f"screw {__version__}\n"


def test_serve_runs_uvicorn_on_the_app_without_its_own_log_config(
        monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("SCREW_HOST", "SCREW_PORT", "SCREW_WORKERS", "SCREW_ROOT_PATH"):
        monkeypatch.delenv(name, raising=False)
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
    monkeypatch.setattr("uvicorn.run", lambda *a, **kw: calls.append((a, kw)))
    cli.main(["serve"])
    assert calls == [(("screw.app:app",), {
        "host": "127.0.0.1", "port": 8000, "workers": 1, "root_path": "",
        "proxy_headers": True, "log_config": None})]


def test_readme_cli_examples_run(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Every `.venv/bin/screw` command the README shows runs as written (-o aside)."""
    readme = (Path(__file__).parents[1] / "README.md").read_text()
    lines = re.findall(r"^[ \t]+\.venv/bin/screw (.+)$", readme, re.MULTILINE)
    # A regex that stops matching must fail the test, not pass it vacuously.
    assert len(lines) >= 2
    for n, line in enumerate(lines):
        args = shlex.split(line.split("#", 1)[0])
        capsys.readouterr()
        if args[0] == "export":
            at = args.index("-o") + 1
            out = tmp_path / f"{n}{Path(args[at]).suffix}"
            args[at] = str(out)
            cli.main(args)
            assert out.stat().st_size > 0
        else:
            cli.main(args)
            assert json.loads(capsys.readouterr().out)["kind"] == "bolt"


CAPPED = ["--d", "8", "--pitch", "1.25", "--length", "67.6"]


def test_a_fine_stl_l11_measured_over_budget_exits_2_and_writes_nothing(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "x.stl"
    assert _exit_code(["export", "bolt", *CAPPED, "-o", str(out)]) == 2
    err = capsys.readouterr().err
    assert "error: length:" in err
    assert "2026-10-08-a-grid" in err
    assert not out.exists()


def test_the_same_part_is_exported_as_a_step_and_as_a_preview_stl(tmp_path: Path) -> None:
    step = tmp_path / "x.step"
    cli.main(["export", "bolt", *CAPPED, "-o", str(step)])
    assert step.read_bytes().startswith(b"ISO-10303-21;")
    stl = tmp_path / "x.stl"
    cli.main(["export", "bolt", *CAPPED, "-o", str(stl), "--quality", "preview"])
    assert len(stl.read_bytes()) > 84


def test_the_over_budget_fine_stl_exits_2_from_the_real_process(tmp_path: Path) -> None:
    """Like a bad parameter, not a build failure (exit 1): the shell sees the same code."""
    out = tmp_path / "x.stl"
    result = subprocess.run(
        [sys.executable, "-m", "screw.cli", "export", "bolt", *CAPPED, "-o", str(out)],
        capture_output=True, text=True, check=False)
    assert result.returncode == 2
    assert "error: length:" in result.stderr
    assert not out.exists()


def test_the_left_hand_part_l11_measured_inside_the_budget_is_not_refused(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """D-21: M10 x 60 is over the budget right-hand and inside it left-hand.

    A real fine export of the left-hand part would write a large STL, so its side is asked of the
    rule `screw export` shares with the API; the right-hand side is the real command.
    """
    mirror = ["--d", "10", "--pitch", "1.5", "--length", "60", "--s", "16", "--k", "6.4"]
    left = BoltParams(d=10.0, pitch=1.5, length=60.0, left_hand=True, s=16.0, k=6.4)
    assert download_refusal(left, "stl", "fine") is None
    cli.main(["info", "bolt", *mirror, "--left-hand"])
    assert json.loads(capsys.readouterr().out)["warnings"] == [derive(left).warnings[0]]

    cli.main(["info", "bolt", *mirror])
    warnings = json.loads(capsys.readouterr().out)["warnings"]
    assert len(warnings) == 2
    assert warnings[1].startswith("length: ")
    assert "right-hand" in warnings[1]

    out = tmp_path / "x.stl"
    assert _exit_code(["export", "bolt", *mirror, "-o", str(out)]) == 2
    assert "error: length:" in capsys.readouterr().err
    assert not out.exists()
