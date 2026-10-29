"""The command line: flags generated from the registry, refusals that name the argument,
and the exit codes a script depends on."""

from __future__ import annotations

import argparse
import json
import math
import re
import shlex
import struct
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import Field

from screw import __version__, cli
from screw.calc import cost, derive, download_name, download_refusal
from screw.params import KINDS, BoltParams, FastenerParams, NutParams

WARNING = ("warning: ends modelled per L15 and L19: bolt tip chamfer, hex head chamfer, "
           "under-head fillet on an ISO 4014 plain shank, nut lead-in countersinks and face "
           "chamfers; nominal, not toleranced; not a product build")


def _exit_code(argv: list[str]) -> str | int | None:
    with pytest.raises(SystemExit) as exc:
        cli.main(argv)
    return exc.value.code


def test_info_prints_the_part_info_document(capsys: pytest.CaptureFixture[str]) -> None:
    cli.main(["info", "bolt"])
    assert capsys.readouterr().out == derive(BoltParams()).model_dump_json(indent=2) + "\n"


def test_info_reads_every_field_flag(capsys: pytest.CaptureFixture[str]) -> None:
    cli.main(["info", "bolt", "--d", "8", "--pitch", "1.25", "--length", "30",
              "--thread-length", "18"])
    rows = {r["key"]: r["value"] for r in json.loads(capsys.readouterr().out)["rows"]}
    assert (rows["d"], rows["pitch"], rows["length"]) == (8.0, 1.25, 30.0)
    assert (rows["thread_length"], rows["shank_length"]) == (18.0, 12.0)


def test_a_length_below_the_default_thread_is_built_to_the_length_and_warned_not_refused(
        capsys: pytest.CaptureFixture[str]) -> None:
    # D-08: the default 20 is frozen; `--length 10` is a 10 mm full-thread screw, never a 422.
    cli.main(["info", "bolt", "--length", "10"])
    doc = json.loads(capsys.readouterr().out)
    assert doc["warnings"][1] == (
        "thread_length 20 (default) exceeds length 10: thread built to the full length")
    rows = {r["key"]: r["value"] for r in doc["rows"]}
    assert (rows["thread_length"], rows["shank_length"]) == (10.0, 0.0)


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
    ("thread-length", "0"), ("thread-length", "-1"), ("thread-length", "inf"),
    ("thread-length", "nan"), ("thread-length", "100001"),
    ("s", "0"), ("s", "-1"), ("s", "inf"), ("s", "nan"), ("s", "100001"),
    ("k", "0"), ("k", "-1"), ("k", "inf"), ("k", "nan"), ("k", "100001"),
])
def test_a_bad_value_exits_2_naming_the_field(
        field: str, value: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert _exit_code(["info", "bolt", f"--{field}", value]) == 2
    assert f"error: {field.replace('-', '_')}:" in capsys.readouterr().err


def test_a_head_one_ulp_wider_than_the_shank_is_accepted(
        capsys: pytest.CaptureFixture[str]) -> None:
    cli.main(["info", "bolt", "--s", repr(math.nextafter(6.0, math.inf))])
    rows = {r["key"]: r["value"] for r in json.loads(capsys.readouterr().out)["rows"]}
    assert rows["s"] == math.nextafter(6.0, math.inf)


@pytest.mark.parametrize("field", ["s", "k"])
def test_a_head_value_that_is_text_exits_2_naming_the_flag(
        field: str, capsys: pytest.CaptureFixture[str]) -> None:
    # argparse refuses text before the model sees it, and names the flag.
    assert _exit_code(["info", "bolt", f"--{field}", "text"]) == 2
    assert f"argument --{field}: invalid float value: 'text'" in capsys.readouterr().err


@pytest.mark.parametrize(("argv", "prefix"), [
    (["info", "bolt", "--pitch", "6"], "error: d and pitch:"),
    # 5.53 mm leaves a root radius of 0.0069 mm: above 0 (the old rule built it) and under the
    # 0.01 mm floor the kernel was measured to build down to (07 D-18, L20).
    (["info", "bolt", "--pitch", "5.53"], "error: d and pitch:"),
    (["info", "bolt", "--length", "300", "--thread-length", "300"],
     "error: thread_length, length and pitch:"),
    # head_too_small (D-23): the CLI prints no type, so the text names both fields.
    (["info", "bolt", "--s", "6"], "error: s and d: "),
    (["export", "bolt", "-o", "unused.stl", "--s", "5"], "error: s and d: "),
    # length / pitch is past the float range: exit 2, not the OverflowError traceback (CR-01)
    (["info", "bolt", "--pitch", "5e-324"], "error: thread_length, length and pitch: inf turns"),
    (["info", "bolt", "--pitch", "1e-310", "--length", "1e4"],
     "error: thread_length, length and pitch: inf turns"),
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
    ["info", "washer"],
    ["export", "washer", "-o", "unused.stl"],
])
def test_an_unknown_kind_exits_2(argv: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    assert _exit_code(argv) == 2
    err = capsys.readouterr().err
    assert "washer" in err
    assert "bolt" in err      # the valid choices are named
    assert "nut" in err


def test_a_nut_without_a_clearance_takes_the_default(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # PAIR-02, L17: the clearance has a default, so it is built, never refused by name.
    cli.main(["info", "nut"])     # returns instead of exiting: exit 0
    rows = {row["key"]: row["value"] for row in json.loads(capsys.readouterr().out)["rows"]}
    assert rows["clearance"] == 0.15
    out = tmp_path / "n.stl"
    cli.main(["export", "nut", "-o", str(out), "--quality", "preview"])
    assert out.stat().st_size > 84


def test_a_required_flag_is_marked_required_in_the_help(
        capsys: pytest.CaptureFixture[str]) -> None:
    # No registered kind has a required field since L17, so the generic rule is tested on a planted
    # model through the same `_add_args` the subcommands use.
    class Planted(FastenerParams):
        kind = "planted"
        needed: float = Field(...)

    parser = argparse.ArgumentParser()
    cli._add_args(parser, "planted", Planted)
    with pytest.raises(SystemExit):
        parser.parse_args(["--help"])
    out = re.sub(r"\s+", " ", capsys.readouterr().out)
    assert "[required]" in out
    assert "PydanticUndefined" not in out


def test_a_defaulted_flag_shows_its_default_in_the_help(
        capsys: pytest.CaptureFixture[str]) -> None:
    assert _exit_code(["info", "nut", "--help"]) == 0
    out = re.sub(r"\s+", " ", capsys.readouterr().out)
    assert "[required]" not in out
    assert "(ISO 4032 symbol m). [5.2]" in out


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
    # These pass the model (a root radius of 0.0123 mm, above the 0.01 mm floor) and the kernel
    # builds one valid solid of them whose volume is off the closed form (-1.829e-04): the gate
    # refuses it.
    out = tmp_path / "b.stl"
    code = _exit_code(["export", "bolt", "-o", str(out), "--d", "0.03", "--pitch", "0.005",
                       "--length", "0.05"])
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


def test_presets_prints_the_catalogue_and_refuses_an_unknown_kind(
        capsys: pytest.CaptureFixture[str]) -> None:
    cli.main(["presets", "bolt"])
    doc = json.loads(capsys.readouterr().out)
    ids = [row["id"] for row in doc["rows"]]
    assert doc["kind"] == "bolt"
    assert doc["axes"] == ["Standard", "Size", "Length"]
    assert "iso4017:M6x20" in ids
    assert "iso4014:M10x80" in ids
    assert len(ids) == len(set(ids))
    assert _exit_code(["presets", "washer"]) == 2
    assert _exit_code(["presets"]) == 2


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


# The explore point `bolt-d30-p1-n30-right`, which 07-BUDGET-TABLE.md lists as refused at stl-fine
# under C1 (B-01; run 40646117094). An R12 widening only refuses more, so it stays refused.
OVER = ["--d", "30", "--pitch", "1", "--length", "30", "--thread-length", "30", "--s", "48",
        "--k", "18"]
OVER_PART = BoltParams(d=30.0, pitch=1.0, length=30.0, thread_length=30.0, s=48.0, k=18.0)


def test_a_fine_stl_over_its_budget_exits_2_and_writes_nothing(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "x.stl"
    refusal = cost.refusal(OVER_PART, "stl-fine")
    assert refusal is not None
    assert _exit_code(["export", "bolt", *OVER, "-o", str(out)]) == 2
    err = capsys.readouterr().err
    assert err == f"error: {refusal}\n"
    assert err.startswith("error: d, pitch, length, s, k and thread_length: ")
    assert "L21" in err
    assert not out.exists()


def test_a_nut_fine_stl_over_its_budget_exits_2_and_writes_nothing(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # The explore point `nut-d100-p1-m0.8d-s1.6d-c5-right`, which 07-BUDGET-TABLE.md lists as
    # refused at stl-fine under C1 (B-01; run 40646117094); a widening only refuses more.
    out = tmp_path / "x.stl"
    argv = ["export", "nut", "--d", "100", "--pitch", "1", "--s", "160", "--m", "80",
            "--clearance", "5", "-o", str(out)]
    refusal = cost.refusal(NutParams(d=100.0, pitch=1.0, s=160.0, m=80.0, clearance=5.0),
                           "stl-fine")
    assert refusal is not None
    assert _exit_code(argv) == 2
    err = capsys.readouterr().err
    assert err == f"error: {refusal}\n"
    assert err.startswith("error: d, pitch, s, m and clearance: ")
    assert "L21" in err
    assert not out.exists()


@pytest.mark.parametrize(("suffix", "quality"), [
    ("stl", "fine"), ("stl", "preview"), ("step", "fine"), ("step", "preview")])
def test_each_download_of_a_refused_part_is_judged_on_its_own(
        tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch,
        suffix: str, quality: str) -> None:
    """A refusal is per artifact (D-06): the export exits 2 exactly where the shared rule refuses.

    The kernel is stubbed, so only the rule is under test, not a d 30 build.
    """
    monkeypatch.setattr("screw.solid.export", lambda p, fmt, q: b"solid")
    out = tmp_path / f"x.{suffix}"
    refusal = download_refusal(OVER_PART, suffix, quality)
    argv = ["export", "bolt", *OVER, "-o", str(out), "--quality", quality]
    capsys.readouterr()
    if refusal is None:
        cli.main(argv)
        assert out.read_bytes() == b"solid"
    else:
        assert _exit_code(argv) == 2
        assert capsys.readouterr().err == f"error: {refusal}\n"
        assert not out.exists()


# B-03 (07-OWNER-RULINGS.md, 2026-10-29): OVER with its length and thread_length left at their
# defaults is over its budget at stl-preview and stl-fine; its defaulted thread_length is capped.
CAPPED = ["--d", "30", "--s", "48", "--k", "18"]
CAPPED_PART = BoltParams(d=30.0, s=48.0, k=18.0)


def test_info_prints_the_capped_part_with_its_warning_first(
        capsys: pytest.CaptureFixture[str]) -> None:
    capped, (warning,) = cost.cap_defaults(CAPPED_PART, frozenset({"d", "s", "k"}))
    assert isinstance(capped, BoltParams)
    cli.main(["info", "bolt", *CAPPED])
    doc = json.loads(capsys.readouterr().out)
    assert doc["warnings"][0] == warning
    assert warning.startswith("thread_length: the default 20 mm ")
    rows = {r["key"]: r["value"] for r in doc["rows"]}
    assert rows["thread_length"] == capped.thread_length < 20.0


def test_export_writes_the_capped_part_under_its_name_and_warns(
        tmp_path: Path, capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    built: list[FastenerParams] = []

    def fake_export(p: FastenerParams, fmt: str, quality: str) -> bytes:
        built.append(p)
        return b"solid"

    monkeypatch.setattr("screw.solid.export", fake_export)
    capped, (warning,) = cost.cap_defaults(CAPPED_PART, frozenset({"d", "s", "k"}))
    assert isinstance(capped, BoltParams)
    cli.main(["export", "bolt", *CAPPED, "-o", str(tmp_path), "--format", "stl"])
    assert [f.name for f in tmp_path.iterdir()] == [download_name(capped, "stl", "fine")]
    assert built == [capped]
    assert f"warning: {warning}\n" in capsys.readouterr().err


def test_a_presets_fields_count_as_given_so_a_preset_is_never_capped(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # iso4017:M6x20 carries length and thread_length 20, the defaults. With --s 13 its preview is
    # over the budget; the same values left unnamed would be capped (thread_length 4.5, above B-03's
    # turns floor, where --s 15 no longer caps), the preset's are refused.
    p = BoltParams(s=13.0)
    assert cost.cap_defaults(p, frozenset({"s"}))[1] != ()
    named = frozenset({"d", "pitch", "length", "s", "k", "thread_length"})
    assert cost.cap_defaults(p, named) == (p, ())
    cli.main(["info", "bolt", "--preset", "iso4017:M6x20", "--s", "13"])
    doc = json.loads(capsys.readouterr().out)
    assert doc == json.loads(derive(p).model_dump_json())
    out = tmp_path / "x.stl"
    assert _exit_code(["export", "bolt", "--preset", "iso4017:M6x20", "--s", "13", "-o", str(out),
                       "--quality", "preview"]) == 2
    assert capsys.readouterr().err == f"error: {cost.refusal(p, 'stl-preview')}\n"
    assert not out.exists()


def test_a_nut_with_a_defaulted_m_over_the_budget_is_capped_on_m(
        capsys: pytest.CaptureFixture[str]) -> None:
    nut = NutParams(d=2.0, pitch=0.1)
    capped, (warning,) = cost.cap_defaults(nut, frozenset({"d", "pitch"}))
    assert isinstance(capped, NutParams)
    cli.main(["info", "nut", "--d", "2", "--pitch", "0.1"])
    doc = json.loads(capsys.readouterr().out)
    assert doc["warnings"][0] == warning
    assert warning.startswith("m: ")
    assert {r["key"]: r["value"] for r in doc["rows"]}["m"] == capped.m < 5.2


def test_a_bolt_only_a_coarser_pitch_would_admit_keeps_its_refusal(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # B-03 is part-wide, not part-wide-pitch: the pitch never moves, so the 422 analogue stands.
    p = BoltParams(d=100.0, s=160.0, k=60.0)
    argv = ["--d", "100", "--s", "160", "--k", "60"]
    cli.main(["info", "bolt", *argv])
    assert json.loads(capsys.readouterr().out) == json.loads(derive(p).model_dump_json())
    out = tmp_path / "x.stl"
    assert _exit_code(["export", "bolt", *argv, "-o", str(out), "--quality", "preview"]) == 2
    assert capsys.readouterr().err == f"error: {cost.refusal(p, 'stl-preview')}\n"
    assert not out.exists()


def test_the_over_budget_fine_stl_exits_2_from_the_real_process(tmp_path: Path) -> None:
    """Like a bad parameter, not a build failure (exit 1): the shell sees the same code."""
    out = tmp_path / "x.stl"
    result = subprocess.run(
        [sys.executable, "-m", "screw.cli", "export", "bolt", *OVER, "-o", str(out)],
        capture_output=True, text=True, check=False)
    assert result.returncode == 2
    assert result.stderr == f"error: {cost.refusal(OVER_PART, 'stl-fine')}\n"
    assert not out.exists()


def test_either_hand_of_m10_x_60_is_judged_by_the_shared_rule(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """D-21: the hand is a feature of the cost model, so each hand reads its own outcome.

    A real fine export would write a large STL, so the outcome is asked of the rule `screw export`
    shares with the API, and the command is held to it.
    """
    mirror = ["--d", "10", "--pitch", "1.5", "--length", "60", "--thread-length", "60", "--s", "16",
              "--k", "6.4"]
    for hand in ([], ["--left-hand"]):
        p = BoltParams(d=10.0, pitch=1.5, length=60.0, thread_length=60.0, left_hand=bool(hand),
                       s=16.0, k=6.4)
        assert download_refusal(p, "stl", "fine") == cost.refusal(p, "stl-fine")
        cli.main(["info", "bolt", *mirror, *hand])
        assert json.loads(capsys.readouterr().out)["warnings"] == derive(p).warnings


def test_an_explicit_thread_length_above_an_explicit_length_exits_2_naming_both(
        capsys: pytest.CaptureFixture[str]) -> None:
    assert _exit_code(["info", "bolt", "--length", "10", "--thread-length", "30"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "error: thread_length and length: thread_length 30 mm is longer than length 10 mm; "
        "shorten thread_length or lengthen length\n")


def test_the_same_conflict_stops_an_export_before_it_writes_a_file(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "x.stl"
    given = ["export", "bolt", "--length", "10", "--thread-length", "30", "-o", str(out)]
    assert _exit_code(given) == 2
    assert "error: thread_length and length: " in capsys.readouterr().err
    assert not out.exists()


def test_an_explicit_head_chamfer_deeper_than_half_k_exits_2_and_writes_nothing(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    msg = ("error: head_chamfer and k: head_chamfer 80 degrees cuts the head corners deeper "
           "than k / 2 = 2 mm at s 10 mm; lower head_chamfer or raise k\n")
    assert _exit_code(["info", "bolt", "--head-chamfer", "80"]) == 2
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("", msg)
    out = tmp_path / "x.stl"
    assert _exit_code(["export", "bolt", "-o", str(out), "--head-chamfer", "80"]) == 2
    assert capsys.readouterr().err == msg
    assert not out.exists()


def test_a_thread_length_equal_to_the_length_or_a_default_beside_a_short_length_is_built(
        capsys: pytest.CaptureFixture[str]) -> None:
    cli.main(["info", "bolt", "--length", "10", "--thread-length", "10.0"])
    assert json.loads(capsys.readouterr().out)["kind"] == "bolt"
    cli.main(["info", "bolt", "--length", "10"])
    assert json.loads(capsys.readouterr().out)["warnings"][1].startswith(
        "thread_length 20 (default) exceeds length 10")


def test_a_bad_length_beside_a_thread_length_is_the_field_error_not_the_conflict(
        capsys: pytest.CaptureFixture[str]) -> None:
    assert _exit_code(["info", "bolt", "--length", "-5", "--thread-length", "10"]) == 2
    assert "error: length: " in capsys.readouterr().err


def test_export_into_a_directory_names_the_file_by_its_quality(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # D-22, R9: a directory is named by `download_name`; a preview STL says so.
    cli.main(["export", "bolt", "-o", str(tmp_path), "--format", "stl", "--quality", "preview"])
    assert (tmp_path / f"{BoltParams().slug()}_preview.stl").is_file()
    assert "preview" in capsys.readouterr().err


def test_export_into_a_directory_needs_a_format() -> None:
    out = _exit_code(["export", "bolt", "-o", str(Path.cwd())])
    assert out == "error: output is a directory: pass --format stl or --format step"


def test_export_to_a_file_path_writes_it_as_given_and_the_wrote_line_names_the_quality(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "x.stl"
    cli.main(["export", "bolt", "-o", str(out), "--quality", "preview"])
    assert out.is_file()
    assert re.search(r"^wrote .*x\.stl \(\d+ KiB, preview\)$", capsys.readouterr().err, re.M)
    cli.main(["export", "bolt", "-o", str(out)])
    assert ", fine)" in capsys.readouterr().err
