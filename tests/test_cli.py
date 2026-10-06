"""The command line: flags generated from the registry, refusals that name the argument,
and the exit codes a script depends on."""

from __future__ import annotations

import json
import re
import struct
import subprocess
import sys
from pathlib import Path

import pytest

from screw import __version__, cli
from screw.calc import derive
from screw.params import KINDS, BoltParams

pytestmark = pytest.mark.xfail(
    strict=True, reason="RED (01-03): screw.cli is a placeholder until the GREEN commit")

SKELETON = "warning: walking skeleton: plain unthreaded cylinder, not a product build"


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
    assert SKELETON in capsys.readouterr().err

    step = tmp_path / "b.step"
    cli.main(["export", "bolt", "-o", str(step)])
    assert step.read_bytes().startswith(b"ISO-10303-21;")
    assert SKELETON in capsys.readouterr().err


def test_the_format_flag_overrides_the_extension(tmp_path: Path) -> None:
    out = tmp_path / "part.dat"
    cli.main(["export", "bolt", "-o", str(out), "--format", "step"])
    assert out.read_bytes().startswith(b"ISO-10303-21;")


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
])
def test_a_bad_value_exits_2_naming_the_field(
        field: str, value: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert _exit_code(["info", "bolt", f"--{field}", value]) == 2
    assert f"error: {field}:" in capsys.readouterr().err


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
    # d=1e-9 passes the model (d > 0) and the kernel cannot make a valid solid of it.
    out = tmp_path / "b.stl"
    code = _exit_code(["export", "bolt", "-o", str(out), "--d", "1e-9"])
    assert isinstance(code, str)
    assert code.startswith("error: ")
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
