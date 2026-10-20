"""The pair proof's tests: the expected verdicts, pinned before any Phase 5 pair run.

The unmarked tests run in `make verify` and read no kernel: they pin what makes the pair tier
honest, the table of expected verdicts (D-07) and the M18 probe's reading list (D-08). Plan 05-14
adds the slow `pair` tier that runs the kernel against the table.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import asdict, replace
from importlib.metadata import version
from pathlib import Path

import pytest

from bench import m18_probe, pair_expected
from bench.thread_spike import maths
from bench.thread_spike import verdict as spike_verdict
from bench.thread_spike.verdict import PAIR_BAND, closed_control
from screw.calc import pair as rule
from screw.solid.helical import DEFAULT_K, SEWING_TOLERANCE

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


def test_the_pair_rule_module_loads_no_kernel() -> None:
    code = "import sys, screw.calc.pair; print('cadquery' in sys.modules, 'OCP' in sys.modules)"
    out = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True,
                         check=True).stdout.strip()
    assert out == "False False"
