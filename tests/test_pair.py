"""The pair proof's tests: the expected verdicts, pinned before any Phase 5 pair run.

The unmarked tests run in `make verify` and read no kernel: they pin what makes the pair tier
honest, the table of expected verdicts (D-07) and the M18 probe's reading list (D-08). Plan 05-14
adds the slow `pair` tier that runs the kernel against the table.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from bench import m18_probe, pair_expected
from bench.thread_spike import maths
from bench.thread_spike.verdict import closed_control
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
