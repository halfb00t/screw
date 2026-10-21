"""The pair proof's tests: the expected verdicts, pinned before any Phase 5 pair run.

The unmarked tests run in `make verify` and read no kernel: they pin what makes the pair tier
honest, the table of expected verdicts (D-07) and the M18 probe's reading list (D-08). Plan 05-14
adds the slow `pair` tier that runs the kernel against the table.
"""

from __future__ import annotations

import ast
import json
import math
import os
import re
import subprocess
import sys
import time
import tomllib
from collections.abc import Sequence
from dataclasses import asdict, replace
from importlib.metadata import version
from pathlib import Path

import cadquery as cq
import pytest
from pydantic import ValidationError

from bench import m18_probe, pair_expected
from bench.thread_spike import maths
from bench.thread_spike import verdict as spike_verdict
from bench.thread_spike.verdict import PAIR_BAND, closed_control
from screw.calc import derive
from screw.calc import pair as rule
from screw.calc.thread import TIP_ANGLE_DEG, tip_cone_length
from screw.params import BoltParams, FastenerParams, NutParams
from screw.solid import pair as solid_pair
from screw.solid import precise_volume
from screw.solid.helical import DEFAULT_K, SEWING_TOLERANCE
from screw.tables import iso262

PROOF_CLEARANCES = (0.05, 0.10, 0.15, 0.20)

# L11's "Pair check" paragraph, retyped from the decision log on purpose: the table is derived
# from the record, so this literal is the independent second source for the excluded clearances
# (decision_log.md L11, `2026-10-08-a-pair`). Identical on both hands at every size.
L11_EXCLUDED: dict[str, tuple[float, ...]] = {
    "M2": (0.1, 0.2),
    "M2.5": (0.1,),
    "M3": (0.05, 0.15),
    "M3.5": (),
    "M4": (0.05,),
    "M5": (0.05,),
    "M6": (),
    "M7": (0.05,),
    "M8": (),
    "M10": (0.05, 0.1),
    "M12": (0.05,),
    "M14": (0.1,),
    "M16": (),
    "M18": (0.05, 0.1, 0.15, 0.2),
    "M20": (),
}


def _table() -> list[dict[str, str]]:
    """The committed table as rows keyed by column name."""
    lines = pair_expected.TABLE.read_text(encoding="utf-8").splitlines()
    assert tuple(lines[0].split("\t")) == pair_expected.COLUMNS
    return [dict(zip(pair_expected.COLUMNS, line.split("\t"), strict=True)) for line in lines[1:]]


def _is_mixed(row: dict[str, str]) -> bool:
    return row["rod_left_hand"] != row["nut_left_hand"]


def _same_hand_proof(row: dict[str, str]) -> bool:
    return not _is_mixed(row) and float(row["clearance"]) in PROOF_CLEARANCES


def _count(rows: list[dict[str, str]], verdict: str) -> int:
    return sum(1 for r in rows if r["verdict"] == verdict)


def test_the_expected_verdicts_are_re_derived_from_the_recorded_pair_campaign() -> None:
    derived = pair_expected.render(pair_expected.derive())
    assert derived == pair_expected.TABLE.read_text(encoding="utf-8")


def test_the_expected_table_counts_the_recorded_k_3_cells() -> None:
    rows = _table()
    proof = [r for r in rows if _same_hand_proof(r)]
    diagnostic = [r for r in rows if not _is_mixed(r) and float(r["clearance"]) <= 0.0]
    mixed = [r for r in rows if _is_mixed(r)]
    assert len(rows) == 240
    assert (len(proof), _count(proof, "proven"), _count(proof, "inconclusive")) == (120, 88, 32)
    assert (len(diagnostic), _count(diagnostic, "inconclusive")) == (60, 60)
    assert (len(mixed), _count(mixed, "violated")) == (60, 60)


def test_the_excluded_clearances_are_the_ones_l11_records() -> None:
    rows = [r for r in _table() if _same_hand_proof(r)]
    for size, excluded in L11_EXCLUDED.items():
        for hand in ("true", "false"):
            not_proven = tuple(sorted(float(r["clearance"]) for r in rows
                                      if r["size"] == size and r["rod_left_hand"] == hand
                                      and r["verdict"] != "proven"))
            assert not_proven == excluded, f"{size}, left hand {hand}"


def test_m18_is_inconclusive_on_both_hands_at_every_proof_clearance() -> None:
    m18 = [r for r in _table() if r["size"] == "M18" and _same_hand_proof(r)]
    assert len(m18) == 8
    assert {r["verdict"] for r in m18} == {"inconclusive"}


def test_a_record_that_is_not_the_one_l11_cites_is_refused(tmp_path: Path) -> None:
    changed = tmp_path / "pair.jsonl"
    data = bytearray(pair_expected.RECORD.read_bytes())
    data[-2] ^= 0x01
    changed.write_bytes(bytes(data))
    with pytest.raises(ValueError, match=pair_expected.RECORD_SHA256):
        pair_expected.derive(changed)


def test_the_table_is_the_product_k() -> None:
    assert pair_expected.PRODUCT_K == DEFAULT_K


def _probe(name: str, left_hand: bool) -> list[m18_probe.Reading]:
    return [r for r in m18_probe.READINGS if r.probe == name and r.left_hand is left_hand]


def test_the_m18_probe_reads_exactly_the_36_pre_registered_readings() -> None:
    assert len(m18_probe.READINGS) == 36
    assert len(set(m18_probe.READINGS[:5])) == 1  # P1 repeats one reading
    assert m18_probe.REPEATS == 5
    expected = {"P1": 5, "P2": len(m18_probe.DELTAS), "P3": 1, "P4a": 1, "P4b": 1, "H": 2}
    for left_hand in (False, True):
        assert {name: len(_probe(name, left_hand)) for name in expected} == expected
        failing = maths.MATCHED_POSES[2] if left_hand else maths.MATCHED_POSES[0]
        others = tuple(t for t in maths.MATCHED_POSES if t != failing)
        assert {r.theta for r in _probe("P1", left_hand)} == {failing}
        assert [r.theta - failing for r in _probe("P2", left_hand)] == pytest.approx(
            list(m18_probe.DELTAS))
        assert [r.theta for r in _probe("P3", left_hand)] == [failing]
        assert [r.theta for r in _probe("H", left_hand)] == list(others)
    assert m18_probe.DELTAS == (-0.1, -0.01, -0.001, -0.0001, 0.0001, 0.001, 0.01, 0.1)
    assert all(r.offset_pitches == maths.CONTROL_OFFSET_PITCHES for r in m18_probe.READINGS)
    assert m18_probe.FUZZY_MM == SEWING_TOLERANCE
    for r in m18_probe.READINGS:
        assert (r.fuzzy is not None) is (r.probe == "P4a")
        assert r.swapped is (r.probe == "P4b")
        assert r.clearance == (-0.05 if r.probe == "P3" else 0.10)


def test_the_m18_deadline_is_four_times_the_slowest_recorded_m18_boolean() -> None:
    assert m18_probe.deadline_from_record(pair_expected.RECORD) == m18_probe.DEADLINE_S == 130.0


def test_the_m18_probe_refuses_to_run_until_its_protocol_is_on_main() -> None:
    text = m18_probe.PROTOCOL.read_bytes()
    assert not m18_probe.protocol_on_main(text, None)
    assert not m18_probe.protocol_on_main(text, text + b" ")
    assert not m18_probe.protocol_on_main(text, text.replace(b"\n", b"\r\n"))
    assert m18_probe.protocol_on_main(text, text)


def test_the_run_guard_reads_git_output_as_bytes_so_line_endings_count(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The pre-commit hook runs this with GIT_INDEX_FILE and friends pointing at the real repo.
    for name in [n for n in os.environ if n.startswith("GIT_")]:
        monkeypatch.delenv(name)
    git = ("git", "-C", str(tmp_path))
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "config", "core.autocrlf", "false"], check=True)
    (tmp_path / "protocol.md").write_bytes(b"one\r\ntwo\r\n")
    subprocess.run([*git, "add", "protocol.md"], check=True)
    assert m18_probe._git("show", ":protocol.md", cwd=tmp_path) == b"one\r\ntwo\r\n"
    assert m18_probe._git("show", ":missing.md", cwd=tmp_path) is None


def test_the_protocol_states_the_numbers_the_probe_reads() -> None:
    text = m18_probe.PROTOCOL.read_text(encoding="utf-8")
    deltas = ", ".join(f"{delta:+g}" for delta in m18_probe.DELTAS)
    closed = closed_control({
        "size": "M18", "d": m18_probe.D, "pitch": m18_probe.PITCH, "m": m18_probe.M,
        "clearance": m18_probe.CLEARANCE, "rod_left_hand": False, "nut_left_hand": False,
        "k": m18_probe.K})
    assert m18_probe.FUZZY_MM == 1e-4
    for stated in (f"{m18_probe.DEADLINE_S:g} s", "1e-4", "five times", deltas, f"{closed:.4f}"):
        assert stated in text, stated


def test_the_m18_child_runs_only_a_registered_reading_of_a_claimed_run(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    local = m18_probe.PROTOCOL.read_bytes()
    out = tmp_path / "m18-diagnosis.jsonl"
    monkeypatch.setattr(m18_probe, "OUT", out)
    monkeypatch.setattr(m18_probe, "_git", lambda *_a, **_k: local)
    registered = m18_probe.READINGS[0]
    off_list = replace(registered, clearance=0.5)
    out.touch()
    assert m18_probe.child_refusal(registered) is None
    assert "registered" in str(m18_probe.child_refusal(off_list))
    out.write_text("{}\n")
    assert "claimed" in str(m18_probe.child_refusal(registered))
    out.unlink()
    assert "claimed" in str(m18_probe.child_refusal(registered))
    out.touch()
    monkeypatch.setattr(m18_probe, "_git", lambda *_a, **_k: local + b" ")
    assert "origin/main" in str(m18_probe.child_refusal(registered))


def test_the_m18_one_entry_refuses_before_it_loads_the_kernel() -> None:
    off_list = replace(m18_probe.READINGS[0], clearance=0.5)
    done = subprocess.run(
        [sys.executable, "-m", "bench.m18_probe", "--one", json.dumps(asdict(off_list))],
        capture_output=True, text=True, timeout=60, cwd=m18_probe.ROOT, check=False)
    result = json.loads(done.stdout.strip().splitlines()[-1])
    assert result["outcome"] == "failure"
    assert "registered" in result["error"]


def _probe_row(r: m18_probe.Reading, volume: float | None = None) -> dict[str, object]:
    """What a child prints for `r`, kernel-free: the harness controls read their closed form."""
    closed = m18_probe._closed_form(r)
    harness = r.probe == "H"
    return {**asdict(r), "closed_control": closed, "outcome": "built",
            "solids": 1 if harness else 0,
            "volume": (closed if volume is None else volume) if harness else 0.0}


def _fake_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    out = tmp_path / "phase-05" / "m18-diagnosis.jsonl"
    monkeypatch.setattr(m18_probe, "OUT", out)
    monkeypatch.setattr(m18_probe, "_git", lambda *_a, **_k: m18_probe.PROTOCOL.read_bytes())
    return out


def test_the_m18_run_claims_its_output_before_the_first_reading(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out = _fake_run(tmp_path, monkeypatch)
    started: list[m18_probe.Reading] = []

    def child(r: m18_probe.Reading) -> dict[str, object]:
        started.append(r)
        assert out.exists()  # claimed already, so a second launch cannot also run
        assert m18_probe.main() == 2  # the second launch is refused
        return _probe_row(r)

    monkeypatch.setattr(m18_probe, "_child", child)
    assert m18_probe.main() == 0
    assert len(started) == 36  # the refused launches started nothing
    assert len(out.read_text(encoding="utf-8").splitlines()) == 37
    assert m18_probe.main() == 2


def test_an_interrupted_m18_run_leaves_a_claim_that_blocks_a_repeat(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out = _fake_run(tmp_path, monkeypatch)

    def child(_r: m18_probe.Reading) -> dict[str, object]:
        raise KeyboardInterrupt

    monkeypatch.setattr(m18_probe, "_child", child)
    with pytest.raises(KeyboardInterrupt):
        m18_probe.main()
    assert out.exists()
    assert m18_probe.main() == 2


def test_the_m18_probe_is_void_when_a_harness_control_does_not_fire() -> None:
    harness = [r for r in m18_probe.READINGS if r.probe == "H"]
    healthy = [_probe_row(r) for r in m18_probe.READINGS]
    assert m18_probe.harness_void(healthy) is None
    closed = m18_probe._closed_form(harness[0])
    inside = [_probe_row(r, closed * (1 + 0.9 * PAIR_BAND)) for r in harness]
    assert m18_probe.harness_void(inside) is None
    for bad in (0.0, closed * (1 + 1.1 * PAIR_BAND), closed * 2):
        rows = [_probe_row(r, bad) if r == harness[1] else _probe_row(r)
                for r in m18_probe.READINGS]
        assert "left hand" not in str(m18_probe.harness_void(rows))  # harness[1] is right hand
        assert "right hand" in str(m18_probe.harness_void(rows))
    timed_out = [{**_probe_row(r), "outcome": "timeout"} if r == harness[0] else _probe_row(r)
                 for r in m18_probe.READINGS]
    assert m18_probe.harness_void(timed_out) is not None
    assert "not 4" in str(m18_probe.harness_void(healthy[:30]))


def test_a_void_m18_probe_says_so_in_the_header_the_table_and_the_exit_code(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    out = _fake_run(tmp_path, monkeypatch)
    monkeypatch.setattr(
        m18_probe, "_child",
        lambda r: _probe_row(r, 0.0) if r.probe == "H" else _probe_row(r))
    assert m18_probe.main() == 1
    header = json.loads(out.read_text(encoding="utf-8").splitlines()[0])
    assert "harness controls" in header["void"]
    assert "VOID" in capsys.readouterr().out
    out.unlink()
    monkeypatch.setattr(m18_probe, "_child", _probe_row)
    assert m18_probe.main() == 0
    assert json.loads(out.read_text(encoding="utf-8").splitlines()[0])["void"] is None
    assert "VOID" not in capsys.readouterr().out


def test_the_m18_header_records_the_installed_kernel_pair(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out = _fake_run(tmp_path, monkeypatch)
    monkeypatch.setattr(m18_probe, "_child", _probe_row)
    assert m18_probe.main() == 0
    header = json.loads(out.read_text(encoding="utf-8").splitlines()[0])
    assert header["kernel"] == {"cadquery": version("cadquery"),
                                "cadquery-ocp": version("cadquery-ocp")}
    pins = Path(m18_probe.ROOT / "requirements.txt").read_text(encoding="utf-8")
    for name, installed in header["kernel"].items():
        assert f"{name}=={installed}" in pins  # the protocol's pair is requirements.txt's (L06)


# --- The rule moved into screw.calc.pair (05-14): identical objects, and its positive controls ---

# Every name the move named (05-14-PLAN.md), spelled out so a name that quietly stays behind in the
# spike, as a copy, fails here and not in a campaign.
MOVED_TO_VERDICT = (
    "T_PASS", "PAIR_BAND", "EMPTY_MM3", "Outcome", "ReadingOutcome", "PairVerdict", "PairReading",
    "PairCell", "PairRequest", "PairRecord", "closed_control", "_nut_body", "cell_verdict",
    "MATCHED_POSES", "CONTROL_OFFSET_PITCHES", "PAIR_CLEARANCES", "DIAGNOSTIC_CLEARANCES",
    "interference_area")
MOVED_TO_MATHS = ("INTEGRATION_POINTS", "MATCHED_POSES", "CONTROL_OFFSET_PITCHES",
                  "PAIR_CLEARANCES", "DIAGNOSTIC_CLEARANCES", "interference_area")


@pytest.mark.parametrize("name", MOVED_TO_VERDICT)
def test_the_spike_verdict_module_re_exports_the_moved_object(name: str) -> None:
    assert getattr(spike_verdict, name) is getattr(rule, name)


@pytest.mark.parametrize("name", MOVED_TO_MATHS)
def test_the_spike_maths_module_re_exports_the_moved_object(name: str) -> None:
    assert getattr(maths, name) is getattr(rule, name)


def test_the_moved_constants_have_the_values_the_spike_registered() -> None:
    assert (rule.PAIR_BAND, rule.EMPTY_MM3, rule.T_PASS) == (1e-3, 1e-6, 1e-4)
    assert rule.CONTROL_OFFSET_PITCHES == 0.5
    assert rule.PAIR_CLEARANCES == (0.05, 0.10, 0.15, 0.20)
    assert rule.DIAGNOSTIC_CLEARANCES == (0.0, -0.05)
    assert rule.INTEGRATION_POINTS == 400_000


def _cell(clearance: float = 0.10, *, rod_left: bool = False,
          nut_left: bool = False) -> rule.PairCell:
    return {"size": "M6", "d": 6.0, "pitch": 1.0, "m": 5.2, "clearance": clearance,
            "rod_left_hand": rod_left, "nut_left_hand": nut_left, "k": DEFAULT_K}


def _reading(theta: float, offset: float, volume: float) -> rule.PairReading:
    return {"theta": theta, "offset_pitches": offset, "outcome": "built",
            "solids": 0 if volume == 0.0 else 1, "volume": volume, "diag_errors": False,
            "diag_warnings": False, "seconds": 0.1}


def _record(clearance: float = 0.10, *, rod_left: bool = False, nut_left: bool = False,
            matched: Sequence[float] = (0.0, 0.0, 0.0),
            controls: Sequence[float] | None = None) -> rule.PairRecord:
    """A built cell as a kernel process would report it: the nut body at its closed form, each
    matched pose as given and each control at the closed form unless given. The readings are
    made by hand, so no kernel runs."""
    cell = _cell(clearance, rod_left=rod_left, nut_left=nut_left)
    mixed = rod_left != nut_left
    closed = rule.closed_control(cell)
    controls = controls if controls is not None else (closed, closed, closed)
    readings = [_reading(t, 0.0, v) for t, v in zip(rule.MATCHED_POSES, matched, strict=True)]
    if not mixed:
        readings += [_reading(t, rule.CONTROL_OFFSET_PITCHES, v)
                     for t, v in zip(rule.MATCHED_POSES, controls, strict=True)]
    return {**cell, "outcome": "built", "error": None, "nut_volume": rule._nut_body(cell),
            "readings": readings}


def _not_built(outcome: rule.Outcome, *, left: bool = False) -> rule.PairRecord:
    return {**_cell(rod_left=left, nut_left=left), "outcome": outcome, "error": "no answer",
            "nut_volume": None, "readings": []}


@pytest.mark.parametrize("left", [False, True], ids=["right", "left"])
def test_a_cell_whose_controls_fire_and_matched_poses_are_empty_is_proven(left: bool) -> None:
    assert rule.cell_verdict(_record(rod_left=left, nut_left=left)) == ("proven", ())


@pytest.mark.parametrize("left", [False, True], ids=["right", "left"])
@pytest.mark.parametrize("pose", range(3))
def test_an_empty_control_at_any_pose_is_inconclusive_and_names_that_pose(
        left: bool, pose: int) -> None:
    closed = rule.closed_control(_cell())
    controls = tuple(0.0 if i == pose else closed for i in range(3))
    verdict, reasons = rule.cell_verdict(_record(
        rod_left=left, nut_left=left, controls=controls))
    assert verdict == "inconclusive"
    (reason,) = reasons
    assert f"control at theta {rule.MATCHED_POSES[pose]:+.4f} reads empty" in reason
    assert f"{closed:.6g}" in reason  # the closed form is the clearance's: c is not in the text


def test_the_empty_control_of_the_first_pose_reads_minus_2_0944() -> None:
    closed = rule.closed_control(_cell())
    _, reasons = rule.cell_verdict(_record(controls=(0.0, closed, closed)))
    assert "control at theta -2.0944 reads empty" in reasons[0]


@pytest.mark.parametrize("left", [False, True], ids=["right", "left"])
def test_a_non_empty_matched_pose_is_violated(left: bool) -> None:
    verdict, reasons = rule.cell_verdict(_record(
        rod_left=left, nut_left=left, matched=(0.0, 0.5, 0.0)))
    assert verdict == "violated"
    assert "matched pose theta +0.0000 reads 0.5 mm3" in reasons[0]


@pytest.mark.parametrize("clearance", [0.0, -0.05])
def test_a_clearance_at_or_below_zero_is_inconclusive_by_definition(clearance: float) -> None:
    verdict, reasons = rule.cell_verdict(_record(clearance))
    assert verdict == "inconclusive"
    assert "inconclusive by definition" in reasons[0]


@pytest.mark.parametrize("rod_left", [False, True], ids=["right rod", "left rod"])
def test_a_mixed_hand_cell_is_violated(rod_left: bool) -> None:
    record = _record(rod_left=rod_left, nut_left=not rod_left, matched=(1.0, 1.0, 1.0))
    assert rule.cell_verdict(record)[0] == "violated"


@pytest.mark.parametrize("outcome", ["failure", "timeout", "worker_died"])
@pytest.mark.parametrize("left", [False, True], ids=["right", "left"])
def test_a_cell_that_did_not_finish_is_never_proven(outcome: rule.Outcome, left: bool) -> None:
    verdict, reasons = rule.cell_verdict(_not_built(outcome, left=left))
    assert verdict == "inconclusive"
    assert outcome in reasons[0]


def test_a_nut_body_that_is_not_the_closed_form_believes_no_reading() -> None:
    record = _record(matched=(1.0, 1.0, 1.0))
    record["nut_volume"] = (record["nut_volume"] or 0.0) * 1.01
    verdict, reasons = rule.cell_verdict(record)
    assert verdict == "inconclusive"
    assert "no reading is believed" in reasons[0]


NOT_FINITE = pytest.param(math.nan, id="nan"), pytest.param(math.inf, id="inf"), \
    pytest.param(-math.inf, id="-inf")


@pytest.mark.parametrize("value", NOT_FINITE)
def test_a_nut_body_that_is_not_finite_believes_no_reading(value: float) -> None:
    # WR-02: `abs(nan / body - 1) > T_PASS` is False, so the positive form read a NaN body as on
    # its closed form and went on to prove the cell.
    record = _record()
    record["nut_volume"] = value
    verdict, reasons = rule.cell_verdict(record)
    assert verdict == "inconclusive"
    assert "no reading is believed" in reasons[0]


@pytest.mark.parametrize("pose", range(3))
@pytest.mark.parametrize("value", NOT_FINITE)
def test_a_control_that_is_not_finite_is_inconclusive_and_names_its_pose(
        value: float, pose: int) -> None:
    closed = rule.closed_control(_cell())
    controls = tuple(value if i == pose else closed for i in range(3))
    verdict, reasons = rule.cell_verdict(_record(controls=controls))
    assert verdict == "inconclusive"
    assert any(f"control at theta {rule.MATCHED_POSES[pose]:+.4f}" in r for r in reasons)


def test_a_matched_pose_that_is_not_finite_is_never_proven() -> None:
    # 02-SPIKE Rules call a reading empty only at 0 solids or |volume| <= 1e-6, so a NaN is
    # non-empty and the pose is `violated`, the written rule's answer. Reading it as anything
    # else would amend the pre-registered rule. The product never hands the rule one: `prove`
    # refuses a non-finite kernel volume where it reads it (`not_finite` tests below).
    verdict, _ = rule.cell_verdict(_record(matched=(0.0, math.nan, 0.0)))
    assert verdict == "violated"


def _judged_cases() -> list[tuple[str, rule.PairRecord, float | None]]:
    cell = _cell()
    closed = rule.closed_control(cell)
    removed = _record()
    removed["readings"] = removed["readings"][:-1]
    scaled = _record()
    scaled["nut_volume"] = (scaled["nut_volume"] or 0.0) * 1.01
    return [
        ("proven", _record(), closed),
        ("an empty control", _record(controls=(0.0, closed, closed)), closed),
        ("a control that cannot fire", _record(0.6), 0.0),
        ("a cell that did not finish", _not_built("failure"), None),
        ("a nut body off its closed form", scaled, None),
        ("a mixed-hand pair", _record(rod_left=True, matched=(1.0, 1.0, 1.0)), None),
        ("no reading at c = 0", _record(0.0), None),
        ("a non-empty matched pose", _record(matched=(0.0, 0.5, 0.0)), None),
        ("a missing control", removed, None),
    ]


@pytest.mark.parametrize(
    ("record", "compared"), [pytest.param(r, c, id=name) for name, r, c in _judged_cases()])
def test_the_rule_returns_the_compared_closed_form_or_none_where_it_ended_first(
        record: rule.PairRecord, compared: float | None) -> None:
    # WR-03: `prove` printed `closed_control` whenever it was computed, on a failure and on a
    # violation too, a number no reading was ever judged against.
    verdict, reasons, closed = rule.cell_judgement(record)
    assert (verdict, reasons) == rule.cell_verdict(record)
    assert closed == compared


def test_the_pair_rule_module_loads_no_kernel() -> None:
    code = "import sys, screw.calc.pair; print('cadquery' in sys.modules, 'OCP' in sys.modules)"
    out = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True,
                         check=True).stdout.strip()
    assert out == "False False"


# --- screw.solid.pair.prove (05-14) --------------------------------------------------------------
# `common` is the one call that cannot run in pytest's own process (it parks its boolean in
# `_KEEP`, and a process that ran it dies at teardown with 139, RESEARCH F5), so these tests hand
# `prove` a scripted fake and run the real bodies, which are safe in-process.

EMPTY = (0.0, 0, False, False, 0.1)


class _Script:
    """A fake `common`: answers the calls in order, and raises where the script holds an error."""

    def __init__(self, *answers: tuple[float, int, bool, bool, float] | Exception) -> None:
        self._answers = answers
        self.calls: list[tuple[cq.Shape, cq.Shape]] = []

    def __call__(self, a: cq.Shape, b: cq.Shape) -> tuple[float, int, bool, bool, float]:
        self.calls.append((a, b))
        answer = self._answers[len(self.calls) - 1]
        if isinstance(answer, Exception):
            raise answer
        return answer


def _fires(closed: float) -> tuple[float, int, bool, bool, float]:
    return (closed, 1, False, False, 0.1)


M6_CLOSED = rule.closed_control(_cell(0.10))


@pytest.fixture(scope="module")
def bodies() -> tuple[cq.Solid, cq.Solid]:
    """The M6 right-hand rod and the c = 0.10 blank, built once: each takes about 1.5 s and the
    orchestration tests below only need them to exist."""
    return (solid_pair.rod_piece(6.0, 1.0, 5.2, False, DEFAULT_K),
            solid_pair.blank(6.0, 1.0, 5.2, 0.10, False, DEFAULT_K))


@pytest.fixture
def built(bodies: tuple[cq.Solid, cq.Solid], monkeypatch: pytest.MonkeyPatch) -> None:
    rod, body = bodies
    monkeypatch.setattr(solid_pair, "rod_piece", lambda *_a: rod)
    monkeypatch.setattr(solid_pair, "blank", lambda *_a: body)


def _nut(clearance: float = 0.10, *, left_hand: bool = False) -> NutParams:
    return NutParams(clearance=clearance, left_hand=left_hand)


@pytest.fixture(scope="module")
def proven(bodies: tuple[cq.Solid, cq.Solid]) -> tuple[solid_pair.PairReport, _Script]:
    """One proven M6 report, taken once: each pose costs about 0.5 s of placing and covering."""
    rod, body = bodies
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(solid_pair, "rod_piece", lambda *_a: rod)
        patch.setattr(solid_pair, "blank", lambda *_a: body)
        fake = _Script(*[EMPTY] * 3, *[_fires(M6_CLOSED)] * 3)
        return solid_pair.prove(_nut(), shipped=False, common=fake), fake


def test_a_pair_whose_matched_poses_are_empty_and_controls_fire_is_proven(
        proven: tuple[solid_pair.PairReport, _Script]) -> None:
    report, fake = proven
    assert (report.verdict, report.reasons) == ("proven", [])
    assert len(fake.calls) == 6
    assert [(r.theta, r.offset_pitches) for r in report.readings] == [
        *[(t, 0.0) for t in rule.MATCHED_POSES], *[(t, 0.5) for t in rule.MATCHED_POSES]]
    assert report.closed_control == pytest.approx(M6_CLOSED)
    assert report.band == PAIR_BAND
    assert report.engagement_turns == pytest.approx(5.2)
    assert (report.d, report.pitch, report.m, report.clearance) == (6.0, 1.0, 5.2, 0.10)
    assert (report.rod_left_hand, report.nut_left_hand) == (False, False)
    assert report.seconds > 0


def test_the_real_blank_is_the_closed_form_the_rule_checks_it_against(
        bodies: tuple[cq.Solid, cq.Solid]) -> None:
    # `cell_verdict` believes no reading from a blank off its closed form by more than T_PASS, so
    # the "proven" above holds only if the blank the kernel builds is on it.
    _, body = bodies
    assert precise_volume(body) == pytest.approx(rule._nut_body(_cell(0.10)), rel=rule.T_PASS)


@pytest.mark.usefixtures("built")
def test_an_empty_control_is_inconclusive_and_names_the_pose_and_carries_the_clearance() -> None:
    fake = _Script(*[EMPTY] * 3, EMPTY, _fires(M6_CLOSED), _fires(M6_CLOSED))
    report = solid_pair.prove(_nut(), shipped=False, common=fake)
    assert report.verdict == "inconclusive"
    (reason,) = report.reasons
    assert "control at theta -2.0944 reads empty" in reason
    assert report.clearance == 0.10  # the reason carries the closed form, the report the c


@pytest.mark.usefixtures("built")
def test_a_failing_boolean_ends_the_cell_inconclusive_and_keeps_the_readings_taken() -> None:
    fake = _Script(*[EMPTY] * 3, RuntimeError("boolean exploded"))
    report = solid_pair.prove(_nut(), shipped=False, common=fake)
    assert report.verdict == "inconclusive"
    assert report.reasons == ["cell failure: RuntimeError: boolean exploded"]
    assert [r.outcome for r in report.readings] == ["built"] * 3 + ["failure"]
    last = report.readings[-1]
    assert (last.theta, last.offset_pitches) == (rule.MATCHED_POSES[0], 0.5)
    assert (last.solids, last.volume, last.seconds) == (None, None, None)
    assert len(fake.calls) == 4


@pytest.mark.usefixtures("built")
@pytest.mark.parametrize("value", [math.nan, math.inf], ids=["nan", "inf"])
def test_a_control_volume_that_is_not_finite_ends_the_cell_as_a_failure(value: float) -> None:
    fake = _Script(*[EMPTY] * 3, (value, 1, False, False, 0.1))
    report = solid_pair.prove(_nut(), shipped=False, common=fake)
    assert report.verdict == "inconclusive"
    (reason,) = report.reasons
    assert reason.startswith("cell failure: ValueError: ")
    assert "not a finite number" in reason
    assert [r.outcome for r in report.readings] == ["built"] * 3 + ["failure"]
    assert len(fake.calls) == 4


@pytest.mark.usefixtures("built")
@pytest.mark.parametrize("value", [math.nan, math.inf], ids=["nan", "inf"])
def test_a_matched_volume_that_is_not_finite_is_a_failure_never_a_violation(
        value: float) -> None:
    fake = _Script((value, 1, False, False, 0.1))
    report = solid_pair.prove(_nut(), shipped=False, common=fake)
    assert report.verdict == "inconclusive"
    assert "not a finite number" in report.reasons[0]
    assert [r.outcome for r in report.readings] == ["failure"]
    assert len(fake.calls) == 1


@pytest.mark.usefixtures("built")
def test_a_nut_body_volume_that_is_not_finite_reads_nothing(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(solid_pair, "precise_volume", lambda _shape: math.nan)
    fake = _Script()
    report = solid_pair.prove(_nut(), shipped=False, common=fake)
    assert report.verdict == "inconclusive"
    (reason,) = report.reasons
    assert reason.startswith("cell failure: ValueError: ")
    assert "nut body" in reason
    assert "not a finite number" in reason
    assert report.readings == []
    assert fake.calls == []


@pytest.mark.usefixtures("built")
def test_a_report_prints_the_compared_closed_form_only_where_the_controls_were_judged() -> None:
    failed = solid_pair.prove(
        _nut(), shipped=False, common=_Script(*[EMPTY] * 3, RuntimeError("boolean exploded")))
    assert (failed.verdict, failed.closed_control) == ("inconclusive", None)
    violated = solid_pair.prove(
        _nut(), shipped=False, common=_Script(*[(0.5, 1, False, False, 0.1)] * 3, *[EMPTY] * 3))
    assert (violated.verdict, violated.closed_control) == ("violated", None)
    empty = solid_pair.prove(_nut(), shipped=False, common=_Script(
        *[EMPTY] * 3, EMPTY, _fires(M6_CLOSED), _fires(M6_CLOSED)))
    assert empty.verdict == "inconclusive"
    assert empty.closed_control == pytest.approx(M6_CLOSED)
    assert f"{M6_CLOSED:.6g}" in empty.reasons[0]


@pytest.mark.parametrize("clearance", [0.0, -0.05])
def test_at_zero_or_negative_clearance_nothing_is_read(clearance: float) -> None:
    fake = _Script()
    report = solid_pair.prove(_nut(clearance), shipped=False, common=fake)
    assert report.verdict == "inconclusive"
    assert report.readings == []
    assert report.closed_control is None
    assert fake.calls == []
    # the reason is the rule's own for a same-hand cell, so the two cannot drift apart
    assert tuple(report.reasons) == rule.cell_verdict(_record(clearance))[1]


@pytest.mark.parametrize("rod_left", [None, True], ids=["same hand", "mixed"])
@pytest.mark.parametrize("clearance", [3.0, 3.5])
def test_a_clearance_of_half_the_diameter_or_more_cannot_hold_the_void_and_reads_nothing(
        clearance: float, rod_left: bool | None) -> None:
    # WR-04: the proof body is a cylinder of radius d, so at c >= d / 2 the void's crest reaches
    # its surface and the closed-form nut body is not a volume (-39.6362 mm3 at d 6, c 3.5).
    p = NutParams(d=6.0, pitch=1.0, s=20.0, m=5.2, clearance=clearance)
    fake = _Script()
    report = solid_pair.prove(p, rod_left_hand=rod_left, common=fake)
    assert report.verdict == "inconclusive"
    assert report.readings == []
    assert report.closed_control is None
    assert report.shipped is None
    assert fake.calls == []
    (reason,) = report.reasons
    assert reason.startswith("d and clearance: ")
    assert "inconclusive by definition" in reason
    assert "closed form" not in reason
    assert re.search(r"(?<![\w.])-\d", reason) is None


def test_the_nut_body_is_a_volume_just_below_the_clearance_that_cannot_hold_the_void() -> None:
    # The branch above starts at d / 2 because the closed form is positive just below it, at
    # every ISO 262 coarse size; kernel-free.
    for size in iso262.SIZES:
        cell = _cell(math.nextafter(size.d / 2, 0.0))
        cell["d"], cell["pitch"], cell["m"] = size.d, size.pitch, 1.0
        assert rule._nut_body(cell) > 0.0, size.label


def test_the_reported_engagement_is_the_info_documents_exact_quotient() -> None:
    # WR-05: `m / pitch` is 9.000000000000002 for m 5.4, pitch 0.6; `screw info` prints 9.0.
    # Clearance 0 reads nothing, so no kernel boolean runs.
    p = NutParams(d=3.5, pitch=0.6, s=6.0, m=5.4, clearance=0.0)
    report = solid_pair.prove(p, shipped=False, common=_Script())
    [row] = [r for r in derive(p).rows if r.key == "engagement_turns"]
    assert report.engagement_turns == 9.0
    assert report.engagement_turns == row.value


@pytest.mark.usefixtures("built")
def test_a_rod_of_the_other_hand_is_violated_through_the_rule() -> None:
    fake = _Script(*[(0.5, 1, False, False, 0.1)] * 3)
    report = solid_pair.prove(_nut(), rod_left_hand=True, shipped=False, common=fake)
    assert report.verdict == "violated"
    assert (report.rod_left_hand, report.nut_left_hand) == (True, False)
    assert len(fake.calls) == 3  # a mixed pair is read at the matched poses and nothing else
    assert all(r.offset_pitches == 0.0 for r in report.readings)
    assert report.closed_control is None


@pytest.mark.usefixtures("built")
def test_a_left_hand_nut_goes_through_the_same_checks() -> None:
    fake = _Script(*[EMPTY] * 3, *[_fires(M6_CLOSED)] * 3)
    report = solid_pair.prove(_nut(left_hand=True), shipped=False, common=fake)
    assert (report.verdict, report.rod_left_hand, report.nut_left_hand) == ("proven", True, True)


def test_the_report_is_frozen_plain_and_serialisable(
        proven: tuple[solid_pair.PairReport, _Script]) -> None:
    report, _ = proven

    def plain(value: object) -> bool:
        if isinstance(value, dict):
            return all(isinstance(k, str) and plain(v) for k, v in value.items())
        if isinstance(value, list):
            return all(plain(v) for v in value)
        return value is None or isinstance(value, bool | int | float | str)

    assert plain(report.model_dump())
    assert solid_pair.PairReport.model_validate_json(report.model_dump_json()) == report
    with pytest.raises(ValidationError, match="frozen"):
        report.verdict = "violated"  # type: ignore[misc]


def test_the_bodies_run_in_process_and_park_nothing(bodies: tuple[cq.Solid, cq.Solid]) -> None:
    rod, body = bodies
    parked = len(solid_pair._KEEP)
    placed = solid_pair.place(body, 2 * 3.141592653589793 / 3, 0.5, 1.0, False)
    solid_pair.check_cover(rod, placed)
    assert len(solid_pair._KEEP) == parked


def test_the_pair_proof_is_not_imported_by_the_solid_package() -> None:
    init = Path(solid_pair.__file__).with_name("__init__.py")
    names = {n for node in ast.walk(ast.parse(init.read_text(encoding="utf-8")))
             if isinstance(node, ast.Import | ast.ImportFrom)
             for n in (*(a.name for a in node.names), getattr(node, "module", None) or "")}
    assert not {n for n in names if n.split(".")[-1] == "pair"}


# --- The shipped-solid evidence row (05-14 task 3) ------------------------------------------------


class _Builds:
    """A fake `solid.build`: records what it was asked for and hands back a stub, a box z 0..7 for
    a bolt and one z 0..5.2 for a nut, so the placement is read off the shapes `common` gets."""

    def __init__(self) -> None:
        self.asked: list[FastenerParams] = []
        self.bolt = cq.Solid.makeBox(1, 1, 7.0)
        self.nut = cq.Solid.makeBox(1, 1, 5.2)

    def __call__(self, p: FastenerParams) -> cq.Solid:
        self.asked.append(p)
        return self.bolt if isinstance(p, BoltParams) else self.nut


@pytest.fixture
def builds(built: None, monkeypatch: pytest.MonkeyPatch) -> _Builds:
    fake = _Builds()
    monkeypatch.setattr(solid_pair, "build", fake)
    return fake


SHIPPED = (8.7, 1, False, False, 0.2)


def _verdict_script(*after: tuple[float, int, bool, bool, float] | Exception) -> _Script:
    return _Script(*[EMPTY] * 3, *[_fires(M6_CLOSED)] * 3, *after)


def test_the_shipped_row_intersects_the_counterpart_bolt_and_the_nut_at_the_matched_poses(
        builds: _Builds) -> None:
    fake = _verdict_script(SHIPPED, SHIPPED, SHIPPED)
    report = solid_pair.prove(_nut(), common=fake)
    tip = tip_cone_length(1.0, TIP_ANGLE_DEG)
    bolt, nut = builds.asked
    assert isinstance(bolt, BoltParams)
    assert bolt.length == bolt.thread_length == pytest.approx(tip + 5.2 + 2 * 1.0)
    assert (bolt.d, bolt.pitch, bolt.left_hand) == (6.0, 1.0, False)
    assert (bolt.s, bolt.k) == (10.0, 4.0)  # the counterpart's: the M6 ISO 4017 row
    assert nut == _nut()
    assert len(fake.calls) == 9  # six for the verdict, then the three matched poses only
    assert report.shipped is not None
    assert [(r.theta, r.outcome, r.solids, r.volume, r.seconds, r.error)
            for r in report.shipped] == [(t, "built", 1, 8.7, 0.2, None)
                                         for t in rule.MATCHED_POSES]
    for (rod, placed), theta in zip(fake.calls[6:], rule.MATCHED_POSES, strict=True):
        assert rod is builds.bolt
        # a whole number of pitches up, clear of the tip cone by at least a pitch, then the
        # screw-motion slide of the pose
        start = placed.BoundingBox().zmin - theta / (2 * math.pi)
        assert start == pytest.approx(round(start))
        assert start >= tip + 1.0


def test_a_planted_non_empty_shipped_reading_leaves_the_verdict_unchanged(
        builds: _Builds, proven: tuple[solid_pair.PairReport, _Script]) -> None:
    baseline, _ = proven
    report = solid_pair.prove(_nut(), common=_verdict_script(SHIPPED, SHIPPED, SHIPPED))
    assert (report.verdict, report.reasons) == ("proven", [])
    assert report.readings == baseline.readings
    assert report.shipped is not None


def test_without_the_shipped_row_no_bolt_is_built(builds: _Builds) -> None:
    report = solid_pair.prove(_nut(), shipped=False, common=_verdict_script())
    assert report.shipped is None
    assert builds.asked == []


def test_a_cell_that_did_not_finish_or_read_nothing_takes_no_shipped_row(
        builds: _Builds) -> None:
    failed = solid_pair.prove(_nut(), common=_Script(RuntimeError("boom")))
    assert (failed.verdict, failed.shipped) == ("inconclusive", None)
    nominal = solid_pair.prove(_nut(0.0), common=_Script())
    assert (nominal.readings, nominal.shipped) == ([], None)
    assert builds.asked == []


def test_a_shipped_part_that_cannot_be_built_is_three_failures_beside_the_same_verdict(
        built: None, monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(_p: FastenerParams) -> cq.Solid:
        raise RuntimeError("no kernel today")

    monkeypatch.setattr(solid_pair, "build", refuse)
    fake = _verdict_script()
    report = solid_pair.prove(_nut(), common=fake)
    assert report.verdict == "proven"
    assert len(fake.calls) == 6
    assert report.shipped is not None
    assert [(r.outcome, r.volume, r.error) for r in report.shipped] == [
        ("failure", None, "RuntimeError: no kernel today")] * 3


def test_a_shipped_boolean_that_raises_fails_that_pose_only(builds: _Builds) -> None:
    report = solid_pair.prove(_nut(), common=_verdict_script(SHIPPED, ValueError("bad"), SHIPPED))
    assert report.verdict == "proven"
    assert report.shipped is not None
    assert [r.outcome for r in report.shipped] == ["built", "failure", "built"]
    assert report.shipped[1].error == "ValueError: bad"


def test_a_shipped_volume_that_is_not_finite_fails_that_pose_only(builds: _Builds) -> None:
    report = solid_pair.prove(
        _nut(), common=_verdict_script(SHIPPED, (math.nan, 1, False, False, 0.2), SHIPPED))
    assert report.verdict == "proven"
    assert report.shipped is not None
    assert [r.outcome for r in report.shipped] == ["built", "failure", "built"]
    assert report.shipped[1].volume is None
    assert "not a finite number" in (report.shipped[1].error or "")


def test_the_shipped_row_is_called_evidence_in_the_docstring() -> None:
    assert "evidence" in (solid_pair.prove.__doc__ or "")


# The placement is measured, not argued: the thread has phase 2 pi z / P on the bolt and on the
# nut, so only a start that is a whole number of pitches is a matched pose. M3, c = 0.10, the
# kernel in a child (RESEARCH F5: a process that ran `common` dies at teardown with 139).
_SHIPPED_CHILD = """
import json, os, sys
from screw.calc.thread import TIP_ANGLE_DEG, tip_cone_length
from screw.params import BoltParams, NutParams
from screw.solid import build, pair

p = NutParams(d=3.0, pitch=0.5, m=2.4, s=5.5, clearance=0.1)
tip = tip_cone_length(p.pitch, TIP_ANGLE_DEG)
length = tip + p.m + 2 * p.pitch
bolt = build(BoltParams(d=3.0, pitch=0.5, s=5.5, k=2.0, length=length, thread_length=length))
nut = build(p)
matched = pair._shipped(p, False, pair.common)
control = pair.common(bolt, pair.place(nut, 0.0, 2.5, p.pitch, False))
literal = pair.common(bolt, pair.place(nut, 0.0, (tip + p.pitch) / p.pitch, p.pitch, False))
print(json.dumps({"matched": [r.model_dump() for r in matched], "control": control[:2],
                  "literal": literal[:2]}))
sys.stdout.flush(); sys.stderr.flush(); os._exit(0)
"""


def test_the_real_shipped_pair_is_empty_at_whole_pitch_starts_and_not_off_phase() -> None:
    done = subprocess.run([sys.executable, "-I", "-c", _SHIPPED_CHILD], capture_output=True,
                          text=True, timeout=300, check=True)
    result = json.loads(done.stdout.strip().splitlines()[-1])
    assert [(r["outcome"], r["solids"]) for r in result["matched"]] == [("built", 0)] * 3
    # the positive controls: the same pair half a pitch off, and at the start "cone length + P"
    # the plan named, both interfere, so an empty reading above is the pose and not a blind boolean
    assert result["control"][1] == 1
    assert result["literal"][1] == 1


# --- the verify cell and the pair tier (PAIR-04, D-07) --------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
PAIR_YML = REPO_ROOT / ".github" / "workflows" / "pair.yml"
CI_YML = REPO_ROOT / ".github" / "workflows" / "ci.yml"
REQUIRED_JOBS = REPO_ROOT / ".github" / "workflows" / "required-jobs.txt"
RESULTS = REPO_ROOT / "bench" / "results" / "phase-05"

# The spike's own per-cell deadline for a whole pair cell, six booleans (recorded worst cell
# 137.3 s, RESEARCH D-07): reused, never re-picked. A cell that outlives it is killed and fails.
CELL_DEADLINE_S = spike_verdict.PAIR_TIMEOUT_S

# A child process, because the real boolean parks its operation in OpenCascade for the life of
# the process and a normal exit then dies at teardown with status 139 (RESEARCH F5): the child
# flushes and ends with os._exit(0), so a non-zero status here means the proof itself failed.
# `s` is the across-flats width the model needs to accept the row and nothing the proof reads
# (`shipped=False` builds no bolt and `prove` never touches `s`): the product default of 10 mm
# is refused for 94 of the 240 rows (d + 2 c above 10), so it is raised to clear the void by 1 mm
# and is the product default wherever that already suffices.
_CELL_CHILD = """
import json, os, sys

from screw.params import NutParams
from screw.solid.pair import prove

row = json.loads(sys.argv[1])
d, c = row["d"], row["clearance"]
p = NutParams(d=d, pitch=row["pitch"], m=row["m"], clearance=c, left_hand=row["nut_left_hand"],
              s=max(10.0, d + 2 * c + 1.0))
report = prove(p, rod_left_hand=row["rod_left_hand"], shipped=False)
print(report.model_dump_json())
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
"""


def _hands(row: dict[str, str]) -> str:
    rod, nut = row["rod_left_hand"] == "true", row["nut_left_hand"] == "true"
    if rod != nut:
        assert not rod, "the table holds the right-hand rod with a left-hand nut as its mixed pair"
        return "mixed"
    return "left" if nut else "right"


def _cell_id(row: dict[str, str]) -> str:
    return f"{row['size']}-{_hands(row)}-c{float(row['clearance']):g}"


def _run_cell(row: dict[str, str], *, deadline: float) -> solid_pair.PairReport:
    """The proof of one table row in a child process, with `shipped=False` (the verdict's own
    six booleans). A timeout, a non-zero exit or output that is not a PairReport fails the cell:
    nothing here can turn a dead child into a pass."""
    spec = {"d": float(row["d"]), "pitch": float(row["pitch"]), "m": float(row["m"]),
            "clearance": float(row["clearance"]),
            "rod_left_hand": row["rod_left_hand"] == "true",
            "nut_left_hand": row["nut_left_hand"] == "true"}
    where = _cell_id(row)
    try:
        done = subprocess.run([sys.executable, "-I", "-c", _CELL_CHILD, json.dumps(spec)],
                              capture_output=True, text=True, timeout=deadline, check=False)
    except subprocess.TimeoutExpired:
        pytest.fail(f"{where}: no answer within {deadline:g} s; a killed cell is never a pass")
    if done.returncode != 0:
        pytest.fail(f"{where}: the child exited {done.returncode}: {done.stderr[-500:]}")
    lines = done.stdout.strip().splitlines()
    try:
        return solid_pair.PairReport.model_validate_json(lines[-1])
    except (IndexError, ValidationError) as exc:
        pytest.fail(f"{where}: the child's output is not a PairReport ({exc!r}): "
                    f"{done.stdout[-500:]}")


def _verify_row() -> dict[str, str]:
    (row,) = (r for r in _table() if _cell_id(r) == "M6-right-c0.1")
    return row


def test_the_verify_cell_is_the_recorded_m6_right_hand_c_0_1_row() -> None:
    row = _verify_row()
    assert (row["d"], row["pitch"], row["m"], row["verdict"]) == ("6.0", "1.0", "5.2", "proven")


def test_the_verify_cell_is_proven_as_pre_registered() -> None:
    row = _verify_row()
    report = _run_cell(row, deadline=CELL_DEADLINE_S)
    assert report.verdict == row["verdict"], report.reasons
    # the proof did read: six matched and control poses, and the control fired at its closed form
    assert len(report.readings) == 6
    assert report.closed_control is not None


GRID_ROWS = _table()
GRID_IDS = [_cell_id(r) for r in GRID_ROWS]


def _write_down(row: dict[str, str], record: dict[str, object]) -> None:
    # One line per cell, appended: an xdist worker writes whole lines, never a partial one.
    RESULTS.mkdir(parents=True, exist_ok=True)
    with (RESULTS / f"pair-{row['size']}.jsonl").open("a", encoding="utf-8") as out:
        out.write(json.dumps(record) + "\n")


@pytest.mark.pair
@pytest.mark.parametrize("row", GRID_ROWS, ids=GRID_IDS)
def test_pair_cell(row: dict[str, str]) -> None:
    started = time.perf_counter()
    record: dict[str, object] = {"id": _cell_id(row), "expected": row["verdict"]}
    try:
        report = _run_cell(row, deadline=CELL_DEADLINE_S)
    except BaseException as failure:    # a failed cell is written down before it fails the run
        _write_down(row, record | {"error": f"{type(failure).__name__}: {failure}"[:500],
                                   "wall_seconds": time.perf_counter() - started})
        raise
    _write_down(row, record | {"report": report.model_dump(),
                               "wall_seconds": time.perf_counter() - started})
    assert report.verdict == row["verdict"], (report.verdict, row["verdict"], report.reasons)


def test_the_pair_grid_is_the_240_pre_registered_cells_with_unique_ids() -> None:
    assert len(GRID_ROWS) == len(set(GRID_IDS)) == 240
    for wanted in ("M6-right-c0.1", "M6-left-c0.1", "M6-mixed-c0.1", "M6-right-c0",
                   "M6-right-c-0.05"):
        assert wanted in GRID_IDS


def test_a_size_selects_exactly_its_sixteen_pair_cells_by_id() -> None:
    """`make pair SIZE=M2` runs `-k 'M2-'`, a case-insensitive substring match: M2 must not pull
    in M12 or M2.5, nor M3 in M3.5 (the same rule the thread grid pins)."""
    for size in maths.SIZES:
        selected = [i for i in GRID_IDS if f"{size}-".lower() in i.lower()]
        assert selected == [i for i in GRID_IDS if i.startswith(f"{size}-")]
        assert len(selected) == 16


def test_the_pair_marker_is_registered_and_deselected_by_default() -> None:
    options = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())["tool"]["pytest"][
        "ini_options"]
    assert "-m 'not grid and not pair'" in options["addopts"]
    assert any(m.startswith("pair:") for m in options["markers"])


def test_the_pair_workflow_has_no_pull_request_or_push_trigger_and_reads_only() -> None:
    """T-05-34: no fork code runs with this token, and the token cannot write."""
    text = PAIR_YML.read_text()
    assert "workflow_dispatch:" in text
    assert re.search(r"^\s*schedule:", text, re.MULTILINE)
    assert not re.search(r"^\s*(pull_request|pull_request_target|push)\s*:", text, re.MULTILINE)
    assert re.search(r"^permissions:\n  contents: read$", text, re.MULTILINE)
    assert "secrets." not in text
    assert "make pair PYTHON=python SIZE=" in text


def test_the_pair_workflow_matrix_is_exactly_the_measured_sizes_in_order() -> None:
    match = re.search(r"^\s*size:\s*\[([^\]]*)\]", PAIR_YML.read_text(), re.MULTILINE)
    assert match is not None, "no `size: [...]` matrix found in pair.yml"
    assert tuple(s.strip().strip('"') for s in match.group(1).split(",")) == maths.SIZES


def test_the_pair_tier_is_not_a_required_job() -> None:
    """D-07, L08: every job in ci.yml is required, so the slow tier lives in its own workflow."""
    ci = CI_YML.read_text()
    assert "make pair" not in ci
    assert "-m pair" not in ci
    required = [line for line in REQUIRED_JOBS.read_text().splitlines()
                if line.strip() and not line.startswith("#")]
    assert not [name for name in required if name.startswith("pair")]
