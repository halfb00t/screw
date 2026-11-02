"""The Phase 8 sets and judges (08-SWEEP-PROTOCOL.md): the committed band walk is the grid F4
states, drawn by code from the R6 charges of explore run 40646117094, and the shipped sweep is
what it reads.

Kernel-free: the checks run on the committed point file and on the generator, with no Docker and no
kernel, like tests/test_oper_pitch.py.
"""

from __future__ import annotations

import functools
import json
import re
from decimal import ROUND_CEILING, Context, Decimal
from fractions import Fraction
from pathlib import Path

import pytest

from bench import oper, oper_lift, oper_sets
from screw.calc import cost

REPO_ROOT = Path(__file__).resolve().parents[1]
WALK = REPO_ROOT / "bench" / "points" / f"{oper_sets.BAND_WALK}.json"
type Raw = dict[str, object]

FULL_THREAD = re.compile(r"^(?P<group>band|check)-d(?P<d>[0-9.]+)-q(?P<q>[0-9.]+)-n(?P<n>\d+)-"
                         r"(?P<hand>right|left)$")
LARGE = re.compile(r"^check-(?P<form>n3s?)-d(?P<d>[0-9.]+)-q(?P<q>[0-9.]+)-(?P<hand>right|left)$")


@functools.cache
def _walk() -> dict[str, object]:
    found: dict[str, object] = json.loads(WALK.read_text())
    return found


def _list(key: str) -> list[Raw]:
    found = _walk()[key]
    assert isinstance(found, list)
    return found


def _cells() -> list[Raw]:
    """Every cell of the walk, read or dropped, in file order within each list."""
    return [*_list("points"), *_list("dropped")]


def _params(cell: Raw) -> dict[str, float]:
    params = cell["params"]
    assert isinstance(params, dict)
    return params


def _ratio(params: dict[str, float]) -> Fraction:
    return Fraction(repr(params["d"])) / Fraction(repr(params["pitch"]))


def _q(label: str) -> Fraction:
    match = FULL_THREAD.match(label) or LARGE.match(label)
    assert match, label
    return Fraction(match["q"])


def _decimals(low: str, high: str, step: str) -> list[str]:
    """`low` to `high` in `step`, second method: decimal arithmetic, no float."""
    out, x = [], Decimal(low)
    while x <= Decimal(high):
        out.append(format(x.normalize(), "f"))
        x += Decimal(step)
    return out


# --- the grid ---------------------------------------------------------------------------------


def test_the_sizes_are_the_f4_lists() -> None:
    expected = [*_decimals("0.3", "1.2", "0.05"), *_decimals("1.3", "3.8", "0.05"),
                "4", "4.5", "5", "6", "8", "10", "12", "16", "20"]
    assert expected[:3] == ["0.3", "0.35", "0.4"]
    assert tuple(expected) == oper_sets.BAND_D
    assert len(oper_sets.BAND_D) == 79
    assert (*expected, "24", "30", "42", "60", "100") == oper_sets.CHECK_D
    assert oper_sets.CHECK_LARGE_D == ("150", "200", "300", "450", "600", "999.999")
    assert oper_sets.BAND_Q == ("5", "6", "6.5", "7", "7.5", "8")
    assert oper_sets.CHECK_Q == ("9", "12.5", "16", "20")
    assert oper_sets.BAND_TURNS == (50, 70, 90)
    assert oper_sets.CHECK_TURNS == (3, 30, 90)
    assert oper_sets.CHECK_FORMS == ("n3", "n3s")


def test_every_cell_of_the_grid_is_a_point_or_dropped_once() -> None:
    labels = [str(c["label"]) for c in _cells()]
    edge = len(oper_sets.BAND_D) * len(oper_sets.BAND_Q) * len(oper_sets.BAND_TURNS) * 2
    check = len(oper_sets.CHECK_D) * len(oper_sets.CHECK_Q) * len(oper_sets.CHECK_TURNS) * 2
    large = len(oper_sets.CHECK_LARGE_D) * len(oper_sets.CHECK_Q) * len(oper_sets.CHECK_FORMS) * 2
    assert (edge, check, large) == (2844, 2016, 96)
    assert len(labels) == len(set(labels)) == edge + check + large == 4956
    assert sum(label.startswith("band-") for label in labels) == edge
    assert sum(label.startswith("check-") for label in labels) == check + large == 2112
    assert all(c["kind"] == "bolt" for c in _cells())


def test_the_walk_file_is_what_the_generator_writes_under_its_recorded_envelope() -> None:
    text = WALK.read_text()
    assert oper_sets._regenerate_runs2(oper_sets.BAND_WALK, text) == text
    assert oper.load_set(oper_sets.BAND_WALK).reps == 1


def test_a_copy_with_one_point_removed_is_not_what_the_generator_writes(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    document = json.loads(WALK.read_text())
    del document["points"][0]
    (tmp_path / WALK.name).write_text(json.dumps(document, indent=1) + "\n")
    monkeypatch.setattr(oper_sets, "POINTS_DIR", tmp_path)
    failure = oper_sets._check_runs2()
    assert failure is not None
    assert WALK.name in failure


def test_the_header_names_the_explore_run_the_shipped_envelope_and_the_rule() -> None:
    walk = _walk()
    assert walk["set"] == "fine-bands"
    assert walk["reps"] == 1
    assert walk["sources"] == ["explore=bench/results/phase-07/explore-40646117094"]
    assert str(walk["rule"]).startswith("08-SWEEP-PROTOCOL.md F4")
    assert oper_sets.envelope_of(walk["envelope"]) == oper_sets.shipped_envelope()


def test_the_walk_is_sharded_by_r6_from_the_explore_charges() -> None:
    sizes = _walk()["shard_sizes"]
    assert isinstance(sizes, list)
    assert sum(sizes) == len(_list("points"))
    assert _walk()["shards"] == len(sizes) > 1


# --- the cells --------------------------------------------------------------------------------


def test_a_cell_pitch_is_d_over_q_rounded_up_to_6_figures() -> None:
    """Decimal arithmetic, a second way to round up: the exact d / pitch is then at most q."""
    context = Context(prec=50)
    for cell in _cells():
        params, q = _params(cell), _q(str(cell["label"]))
        quotient = context.divide(Decimal(repr(params["d"])), Decimal(q.numerator)
                                  / Decimal(q.denominator))
        expected = quotient.quantize(Decimal(1).scaleb(quotient.adjusted() - 5),
                                     rounding=ROUND_CEILING)
        assert params["pitch"] == float(expected), cell["label"]
        assert _ratio(params) <= q, cell["label"]


def test_the_edge_group_lies_at_or_below_8_and_the_check_group_in_8_to_20() -> None:
    for cell in _cells():
        label, ratio = str(cell["label"]), _ratio(_params(cell))
        if label.startswith("band-"):
            assert 4 < ratio <= 8, label
        else:
            assert 8 < ratio <= 20, label


def test_the_adjacency_edge_is_read_exactly_at_a_threshold() -> None:
    """OPER-03: a cell at q 6 or q 8 reads the part whose exact d / pitch is 6 or 8."""
    exact = {Fraction(6), Fraction(8)}
    reached = {_ratio(_params(c)) for c in _cells() if str(c["label"]).startswith("band-")}
    assert exact <= reached


def test_a_full_thread_cell_builds_exactly_n_turns() -> None:
    seen = 0
    for cell in _cells():
        label, params = str(cell["label"]), _params(cell)
        match = FULL_THREAD.match(label)
        if match is None:
            continue
        seen += 1
        pitch = Fraction(repr(params["pitch"]))
        assert Fraction(repr(params["thread_length"])) / pitch == int(match["n"]), label
        assert params["length"] == params["thread_length"], label
        assert params["d"] == float(match["d"]), label
        assert params["s"] == min(oper_sets._scaled(params["d"], "1.6"), 1000.0), label
        assert params["k"] == oper_sets._scaled(params["d"], "0.6"), label
        assert params["left_hand"] is (match["hand"] == "left"), label
    assert seen == 2844 + 2016


def test_the_large_check_cells_are_r31s_n3_and_n3s_bolts() -> None:
    seen = 0
    for cell in _cells():
        label, params = str(cell["label"]), _params(cell)
        match = LARGE.match(label)
        if match is None:
            continue
        seen += 1
        pitch, d = Fraction(repr(params["pitch"])), Fraction(repr(params["d"]))
        assert Fraction(repr(params["thread_length"])) == 3 * pitch, label
        length = Fraction(repr(params["length"]))
        assert length == (3 * pitch if match["form"] == "n3" else 3 * pitch + d), label
        assert params["s"] == min(oper_sets._scaled(params["d"], "1.6"), 1000.0), label
    assert seen == 96


def test_pitch_params_takes_a_fraction_q_as_an_int_q() -> None:
    assert (oper_sets._pitch_params("bolt", "n3", "3", Fraction(7), True)
            == oper_sets._pitch_params("bolt", "n3", "3", 7, True))
    assert oper_sets._pitch_params("nut", "base", "6", Fraction(25, 4), False)["pitch"] == 0.96


# --- reading and dropping ---------------------------------------------------------------------


def test_every_dropped_cell_is_refused_by_the_model_or_admitted_at_no_artifact() -> None:
    envelope = oper_sets.envelope_of(_walk()["envelope"])
    for cell in _list("dropped"):
        params = _params(cell)
        error = oper_sets._model_refusal("bolt", params)
        if error is not None:
            assert cell["error"] == error, cell["label"]
            continue
        assert cell["error"] == "over_budget", cell["label"]
        part = oper_lift.drawn("bolt", params)
        assert oper_sets._first_admitted(part, envelope, cost.BUDGET) is None, cell["label"]


def test_every_point_is_one_the_model_admits_at_the_first_artifact_that_admits_it() -> None:
    envelope = oper_sets.envelope_of(_walk()["envelope"])
    for point in _list("points"):
        part = oper_lift.drawn("bolt", _params(point))
        assert point["artifact"] == oper_sets._first_admitted(part, envelope, cost.BUDGET), (
            point["label"])


def test_the_first_admitted_artifact_is_step_then_stl_preview_then_stl_fine(
        monkeypatch: pytest.MonkeyPatch) -> None:
    part = oper_lift.drawn("bolt", oper_sets._pitch_params("bolt", "n3", "3", 8, False))
    envelope = oper_sets.shipped_envelope()

    def admitting(*artifacts: str) -> None:
        monkeypatch.setattr(oper_sets, "admits", lambda _p, artifact, _e, _b: artifact in artifacts)

    for artifacts, first in ((("step", "stl-preview", "stl-fine"), "step"),
                             (("stl-preview", "stl-fine"), "stl-preview"),
                             (("stl-fine",), "stl-fine"), ((), None)):
        admitting(*artifacts)
        assert oper_sets._first_admitted(part, envelope, cost.BUDGET) == first


def test_a_cell_admitted_at_stl_preview_only_is_read_there(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(oper_sets, "admits",
                        lambda _p, artifact, _e, _b: artifact == "stl-preview")
    monkeypatch.setattr(oper_sets, "BAND_D", ("3",))
    monkeypatch.setattr(oper_sets, "CHECK_D", ("3",))
    monkeypatch.setattr(oper_sets, "CHECK_LARGE_D", ("150",))
    made = oper_sets.band_walk_set(oper_sets.shipped_envelope())
    assert made.points
    assert {p["artifact"] for p in made.points} == {"stl-preview"}
    assert len(made.points) + len(made.dropped) == (
        6 * 3 * 2 + 4 * 3 * 2 + 4 * 2 * 2)
