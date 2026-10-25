"""`screw pair`: the exit code is the verdict (D-06, RESEARCH F5, P1).

The real proof parks its boolean in OpenCascade for the life of the process, and a process that
returns normally after it dies at teardown with status 139 (RESEARCH F5). So nothing here runs
the command's entry point on the real `prove` inside the pytest worker: exit codes of a command
that may reach the kernel are read from a child interpreter, and the 0/1/2 mapping is read
in-process with `prove` and `os._exit` replaced.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

import pytest

from screw import cli
from screw.calc import pair as rule
from screw.params import NutParams
from screw.solid import pair as solid_pair

# The refusals happen before the kernel loads (about 0.1 s here); five seconds is a generous
# bound that still fails if the command starts importing the solid package first.
REFUSAL_SECONDS = 5.0


def _screw(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-m", "screw", "pair", *args],
                          capture_output=True, text=True, timeout=120, check=False)


def test_a_nut_too_thin_for_its_void_exits_2_and_names_it_before_any_kernel_loads() -> None:
    started = time.perf_counter()
    done = _screw("nut", "--clearance", "0.1", "--s", "6")
    assert done.returncode == 2
    assert done.stdout == ""
    assert "across flats s 6 mm must exceed the void's major diameter" in done.stderr
    assert time.perf_counter() - started < REFUSAL_SECONDS


def test_a_refusal_leaves_the_kernel_out_of_the_process() -> None:
    # The same refusals as above, read from inside the process: neither module may be loaded.
    # The arguments come from argv so no `main(["pair", ...` literal sits in the suite.
    code = ("import sys\nfrom screw import cli\n"
            "try:\n    cli.main(sys.argv[1:])\nexcept SystemExit as stop:\n"
            "    print(stop.code, 'cadquery' in sys.modules, 'OCP' in sys.modules)\n")
    for args in (["pair", "nut", "--clearance", "0.1", "--s", "6"],
                 ["pair", "nut", "--s", "6"],
                 ["pair", "nut", "--d", "2", "--pitch", "2", "--clearance", "0.5"]):
        done = subprocess.run([sys.executable, "-I", "-c", code, *args], capture_output=True,
                              text=True, timeout=60, check=False)
        assert done.stdout.split() == ["2", "False", "False"], (args, done.stderr)


def test_a_zero_clearance_is_inconclusive_by_definition_and_exits_2() -> None:
    done = _screw("nut", "--clearance", "0")
    assert done.returncode == 2
    report = solid_pair.PairReport.model_validate_json(done.stdout)
    assert report.verdict == "inconclusive"
    assert report.readings == []
    assert report.clearance == 0.0
    assert done.stderr == ""


def test_a_clearance_that_cannot_hold_the_void_is_inconclusive_by_definition_and_exits_2() -> None:
    done = _screw("nut", "--d", "6", "--pitch", "1", "--s", "20", "--clearance", "3.5")
    assert done.returncode == 2
    assert done.stderr == ""
    report = solid_pair.PairReport.model_validate_json(done.stdout)
    assert report.verdict == "inconclusive"
    assert report.readings == []
    assert report.closed_control is None
    assert report.reasons[0].startswith("d and clearance: ")


def test_no_clearance_proves_the_nut_at_the_default(
        monkeypatch: pytest.MonkeyPatch) -> None:
    # PAIR-02, L17: with no clearance typed the proof runs at the default 0.15, not a refusal. The
    # real proof costs about 40 s and parks the kernel, so `prove` is read here, not run.
    seen: list[float] = []

    def fake_prove(p: NutParams) -> solid_pair.PairReport:
        seen.append(p.clearance)
        return _report("proven")

    monkeypatch.setattr(solid_pair, "prove", fake_prove)
    monkeypatch.setattr(os, "_exit", lambda _status: None)
    cli.cmd_pair(argparse.Namespace(kind="nut", preset=None, d=None, pitch=None, left_hand=None,
                                    s=None, m=None, clearance=None))
    assert seen == [0.15]


def test_the_bolt_has_no_clearance_so_it_has_no_pair() -> None:
    done = _screw("bolt")
    assert done.returncode == 2
    assert "invalid choice: 'bolt' (choose from nut)" in done.stderr


def test_a_nominal_rod_with_no_root_is_refused_with_the_rod_in_the_message() -> None:
    # d 2 pitch 2: the rod's root radius is -0.0825 mm, but a clearance of 0.5 gives the nut's
    # void a root of 0.4175 mm, so the nut itself is valid and only the proof refuses.
    done = _screw("nut", "--d", "2", "--pitch", "2", "--clearance", "0.5")
    assert done.returncode == 2
    assert done.stderr.startswith("error: pair: the nominal rod d and pitch: the root radius")
    assert done.stdout == ""


def _report(verdict: rule.PairVerdict) -> solid_pair.PairReport:
    return solid_pair.PairReport(
        verdict=verdict, reasons=[f"scripted {verdict}"], d=6.0, pitch=1.0, m=5.2, clearance=0.1,
        rod_left_hand=False, nut_left_hand=False, readings=[], closed_control=None,
        band=rule.PAIR_BAND, engagement_turns=5.2, shipped=None, seconds=0.0)


@pytest.mark.parametrize(("verdict", "code"),
                         [("proven", 0), ("violated", 1), ("inconclusive", 2)])
def test_the_exit_code_is_the_verdict_after_the_json_is_out(
        verdict: rule.PairVerdict, code: int, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    exits: list[int] = []
    seen: list[str] = []

    def fake_exit(status: int) -> None:
        # What a real os._exit would not give back: the JSON must already be on stdout.
        seen.append(capsys.readouterr().out)
        exits.append(status)

    monkeypatch.setattr(solid_pair, "prove", lambda _p: _report(verdict))
    monkeypatch.setattr(os, "_exit", fake_exit)
    ns = argparse.Namespace(kind="nut", preset=None, d=None, pitch=None, left_hand=None,
                                s=None, m=None, clearance=0.1)
    cli.cmd_pair(ns)
    assert exits == [code]
    assert json.loads(seen[0])["verdict"] == verdict
    assert solid_pair.PairReport.model_validate_json(seen[0]) == _report(verdict)
