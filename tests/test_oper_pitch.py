"""R31, the fine-pitch walk (G35): the committed walk set is the grid the rule states, and F and W
come from the walk's readings by the rule's definition, with every gap a stop.

The judge runs on synthetic readings written from the committed walk set, so a label and its
params are the ones the runner records; no Docker, no kernel.
"""

from __future__ import annotations

import functools
import json
from collections.abc import Mapping
from decimal import ROUND_CEILING, Context, Decimal
from fractions import Fraction
from pathlib import Path

import pytest

from bench import oper, oper_lift, oper_sets
from bench.oper_sets import ProtocolStop
from screw.calc import cost, thread

REPO_ROOT = Path(__file__).resolve().parents[1]
WALK = REPO_ROOT / "bench" / "points" / f"{oper_sets.PITCH_WALK}.json"
type Raw = dict[str, object]


@functools.cache
def _walk() -> dict[str, object]:
    found: dict[str, object] = json.loads(WALK.read_text())
    return found


def _points() -> list[Raw]:
    points = _walk()["points"]
    assert isinstance(points, list)
    return points


def _ratio(params: object) -> Fraction:
    assert isinstance(params, dict)
    return Fraction(repr(params["d"])) / Fraction(repr(params["pitch"]))


def _q(label: str) -> int:
    return int(label.rsplit("-q", 1)[1].split("-")[0])


# --- the walk set ---------------------------------------------------------------------------------


def test_the_walk_file_is_what_the_generator_writes_under_its_recorded_envelope() -> None:
    text = WALK.read_text()
    assert oper_sets._regenerate_runs2(oper_sets.PITCH_WALK, text) == text
    assert oper.load_set(oper_sets.PITCH_WALK).reps == 1


def test_every_cell_of_the_grid_is_a_point_or_dropped_once() -> None:
    points, dropped = _points(), _walk()["dropped"]
    assert isinstance(dropped, list)
    bolts = len(oper_sets.PITCH_BOLT_FORMS) * len(oper_sets.PITCH_BOLT_D) * len(
        oper_sets.PITCH_BOLT_Q) * 2
    nuts = len(oper_sets.PITCH_NUT_FORMS) * len(oper_sets.PITCH_NUT_D) * len(
        oper_sets.PITCH_NUT_Q) * 2
    labels = [str(p["label"]) for p in points] + [str(x["label"]) for x in dropped]
    assert len(labels) == len(set(labels)) == bolts + nuts == 2904 + 2816
    assert len(points) == 5656
    assert {p["artifact"] for p in points} == {"step"}
    assert (5, 8, 10, 12, 14, *range(15, 32)) == oper_sets.PITCH_BOLT_Q
    assert tuple(range(5, 13)) == oper_sets.PITCH_NUT_Q


def test_a_cell_pitch_is_d_over_q_rounded_up_to_6_figures() -> None:
    """Checked against decimal arithmetic, a second way to round up: the exact d / pitch is then
    at most q, so a cell at a wall's own q is admitted by it."""
    context = Context(prec=50)
    for point in _points():
        params, q = point["params"], _q(str(point["label"]))
        assert isinstance(params, dict)
        quotient = context.divide(Decimal(repr(params["d"])), Decimal(q))
        expected = quotient.quantize(Decimal(1).scaleb(quotient.adjusted() - 5),
                                     rounding=ROUND_CEILING)
        assert params["pitch"] == float(expected), point["label"]
        assert _ratio(params) <= q


def test_the_bolt_forms_have_3_turns_and_the_nut_forms_their_fields() -> None:
    for point in _points():
        params, label = point["params"], str(point["label"])
        assert isinstance(params, dict)
        d, pitch = Fraction(repr(params["d"])), Fraction(repr(params["pitch"]))
        if point["kind"] == "bolt":
            thread = Fraction(repr(params["thread_length"]))
            assert thread == 3 * pitch
            length = Fraction(repr(params["length"]))
            assert length == (thread if "-n3-" in label else thread + d)
            assert params["s"] == min(oper_sets._scaled(params["d"], "1.6"), 1000.0)
            assert params["k"] == oper_sets._scaled(params["d"], "0.6")
        else:
            form = label.split("-")[2]
            assert params["m"] == (params["d"] if form == "m1"
                                   else oper_sets._scaled(params["d"], "0.8"))
            assert params["s"] == oper_sets._scaled(params["d"], "4" if form == "s4" else "1.6")
            assert params["clearance"] == (0.0 if form == "c0" else 0.15)
        assert params["left_hand"] is label.endswith("-left")


def test_every_point_is_one_the_model_and_the_cost_model_admit() -> None:
    """The model less the fine-pitch wall (R31 reads past the wall it decides, G36)."""
    envelope = oper_sets.envelope_of(_walk()["envelope"])
    for point in _points():
        params = point["params"]
        assert isinstance(params, dict)
        part = oper_lift.drawn(str(point["kind"]), params)
        assert any(oper_sets.admits(part, a, envelope, cost.BUDGET) for a in cost.ARTIFACTS)


def test_the_walk_is_sharded_by_r6_from_the_explore_charges() -> None:
    sizes = _walk()["shard_sizes"]
    assert isinstance(sizes, list)
    assert sum(sizes) == len(_points())
    assert _walk()["shards"] == len(sizes)
    assert _walk()["sources"] == ["explore=bench/results/phase-07/explore-40646117094"]


# --- F and W --------------------------------------------------------------------------------------


@pytest.mark.parametrize(("x", "w"), [
    (Fraction(27) / Fraction(5, 4), Fraction(20)), (Fraction(25) / Fraction(5, 4), Fraction(20)),
    (Fraction(11) / Fraction(5, 4), Fraction(8)), (Fraction(10) / Fraction(5, 4), Fraction(8)),
    (Fraction("31.24") / Fraction(5, 4), Fraction(20)), (Fraction("12.5"), Fraction("12.5")),
    (Fraction("0.0099"), Fraction("0.008")), (Fraction(1000), Fraction(1000)),
    (Fraction("3.14"), Fraction("2.5"))])
def test_w_is_the_largest_r10_number_at_or_below(x: Fraction, w: Fraction) -> None:
    assert oper_sets.r10_at_or_below(x) == w


def _readings(failing: Mapping[str, str]) -> list[Raw]:
    """One reading per walk point: `failing[label]` for the labels named, else ok."""
    return [{**p, "rep": 1, "status": failing.get(str(p["label"]), "ok")} for p in _points()]


BOLT_27 = "pitch-bolt-n3-d3-q27-right"
NUT_11 = "pitch-nut-m1-d3.5-q11-right"


def test_f_is_the_smallest_exact_ratio_of_a_refused_or_crashed_reading_per_kind() -> None:
    walls = oper_sets.pitch_walls(_points(), _readings(
        {BOLT_27: "refused", "pitch-bolt-n3-d2-q30-left": "crashed", NUT_11: "refused",
         "pitch-nut-base-d2-q12-left": "refused"}))
    assert walls["bolt"].label == BOLT_27
    assert walls["bolt"].f == Fraction(3) / Fraction("0.111112")
    assert walls["bolt"].w == 20
    assert walls["nut"].label == NUT_11
    assert walls["nut"].w == 8
    text = oper_sets.pitch_walls_text(walls)
    assert f"at {BOLT_27}" in text
    assert "W = 20\n" in text
    assert "W = 8\n" in text


@pytest.mark.parametrize("status", ["killed", "capped", "no_cgroup"])
def test_a_reading_that_is_cost_or_a_gap_leaves_w_with_no_number(status: str) -> None:
    with pytest.raises(ProtocolStop, match=f"is {status}, which is cost or a gap"):
        oper_sets.pitch_walls(_points(), _readings(
            {BOLT_27: "refused", NUT_11: "refused", "pitch-bolt-n3-d1-q5-left": status}))


def test_a_missing_a_doubled_or_a_foreign_reading_leaves_w_with_no_number() -> None:
    every = _readings({BOLT_27: "refused", NUT_11: "refused"})
    with pytest.raises(ProtocolStop, match="1 points of the walk have no reading"):
        oper_sets.pitch_walls(_points(), every[1:])
    with pytest.raises(ProtocolStop, match="was read twice"):
        oper_sets.pitch_walls(_points(), [*every, every[0]])
    with pytest.raises(ProtocolStop, match="is not a point of the walk"):
        oper_sets.pitch_walls(_points(), [*every, {**every[0], "label": "pitch-bolt-elsewhere"}])


def test_a_kind_with_no_refusal_has_no_f() -> None:
    with pytest.raises(ProtocolStop, match="no nut of the walk was refused or crashed"):
        oper_sets.pitch_walls(_points(), _readings({BOLT_27: "refused"}))


def _write(directory: Path, readings: list[Raw]) -> None:
    (directory / "oper-walls-pitch-1-1").mkdir(parents=True)
    lines = [json.dumps({"type": "header", "GITHUB_RUN_ID": "1"})]
    lines += [json.dumps({"type": "reading", **r}) for r in readings]
    (directory / "oper-walls-pitch-1-1" / "oper-walls-pitch-1-1.jsonl").write_text(
        "\n".join(lines) + "\n")


def test_pitch_walls_exits_0_on_the_ruled_walls_and_3_on_any_other(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(tmp_path / "ruled", _readings({BOLT_27: "refused", NUT_11: "refused"}))
    assert oper_sets.main(["pitch-walls", "--from", str(tmp_path / "ruled")]) == 0
    assert "bolt: F = " in capsys.readouterr().out
    _write(tmp_path / "other", _readings({"pitch-bolt-n3-d2-q24-right": "refused",
                                          NUT_11: "refused"}))
    assert oper_sets.main(["pitch-walls", "--from", str(tmp_path / "other")]) == 3
    captured = capsys.readouterr()
    assert "W = 16\n" in captured.out
    assert "the bolt W is 16, not 20" in captured.err


def test_a_nut_w_off_the_margin_rule_does_not_stop_the_walk_since_the_nut_is_ruled(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # G36: the nut's W is 8 by ruling; a nut refused at d / pitch 7 is reported, not a stop.
    _write(tmp_path / "island", _readings({BOLT_27: "refused", NUT_7: "refused"}))
    assert oper_sets.main(["pitch-walls", "--from", str(tmp_path / "island")]) == 0
    out = capsys.readouterr().out
    assert "W = 5\n" in out
    assert "nut: shipped W = 8, the owner's ruling (G36)\n" in out
    assert f"inside the wall, refused: nut {NUT_7} at d / pitch " in out


NUT_7 = "pitch-nut-base-d2.2-q7-left"


def test_the_residual_is_every_refusal_at_or_below_the_shipped_wall() -> None:
    readings = _readings({BOLT_27: "refused", NUT_11: "refused", NUT_7: "crashed"})
    walls = oper_sets.pitch_walls(_points(), readings)
    shipped = oper_sets.shipped_pitch_walls(walls)
    assert shipped == {"bolt": 20, "nut": 8}
    assert [(kind, label) for kind, _, label in oper_sets.pitch_residual(readings, shipped)] == [
        ("nut", NUT_7)]


# --- the committed walk's records --------------------------------------------------------------

RECORDS = REPO_ROOT / "bench" / "results" / "phase-07" / "walls-pitch-41074314305"


@functools.cache
def _recorded() -> tuple[dict[str, oper_sets.PitchWall], list[oper_sets.Reading]]:
    readings = oper_sets.read_readings(RECORDS)
    return oper_sets.pitch_walls(_points(), readings), readings


def test_the_shipped_bolt_wall_is_the_block_the_records_write() -> None:
    """R31: the bolt's W is written by code from the records, never typed: `calc.thread` holds
    exactly the block `pitch-walls --from` prints for the committed run."""
    walls, _ = _recorded()
    assert walls["bolt"].w == oper_sets.EXPECTED_BOLT_PITCH_W == thread.MAX_BOLT_D_PER_PITCH
    block = oper_sets.pitch_walls_block(walls, str(RECORDS.relative_to(REPO_ROOT)))
    assert block in (REPO_ROOT / "src" / "screw" / "calc" / "thread.py").read_text()


def test_the_nut_wall_is_the_ruled_8_and_not_the_margin_rules_5() -> None:
    walls, _ = _recorded()
    assert walls["nut"].w == 5
    assert thread.MAX_NUT_D_PER_PITCH == 8
    source = (REPO_ROOT / "src" / "screw" / "calc" / "thread.py").read_text()
    comment = source[source.index("# END pitch-walls"):source.index("MAX_NUT_D_PER_PITCH =")]
    assert "G36" in comment
    assert "d 2.2 mm, d / pitch 7" in comment


def test_the_residual_of_the_committed_walk_is_the_nut_island_of_six() -> None:
    walls, readings = _recorded()
    residual = oper_sets.pitch_residual(readings, oper_sets.shipped_pitch_walls(walls))
    assert {kind for kind, _, _ in residual} == {"nut"}
    assert {ratio for _, ratio, _ in residual} == {Fraction(1100000, 157143)}
    assert sorted(label for _, _, label in residual) == [
        f"pitch-nut-{form}-d2.2-q7-{hand}" for form in ("base", "m1", "s4")
        for hand in ("left", "right")]
