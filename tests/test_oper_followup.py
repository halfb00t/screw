"""The code that applies R5 to R10 of the sweep protocol to runner records (07-05): the margin, R6's
charges and shards, the R7 walk-down, the pre-confirm wall decisions, the walls confirm set and
every "the phase stops and asks the owner" among them.

Everything runs on synthetic records written from the real `walls` and `spread` point sets, so a
label, a parameter and a lift are the ones the runner would record; no Docker, no kernel.
"""

from __future__ import annotations

import functools
import json
import math
import random
import re
from collections.abc import Iterable, Mapping
from decimal import Decimal
from pathlib import Path

import pytest

from bench import oper, oper_sets
from bench.oper_sets import ProtocolStop
from bench.thread_spike.maths import PITCH
from screw.calc import cost
from screw.calc.thread import built_thread_length
from screw.params import KINDS, BoltParams, FastenerParams
from screw.tables.presets import expand, expand_nut

REPO_ROOT = Path(__file__).resolve().parents[1]
type Raw = dict[str, object]


@functools.cache
def _walls_points() -> tuple[Raw, ...]:
    return tuple(oper_sets.walls().points)


def _reading(point: Mapping[str, object], status: str = "ok", rep: int = 1, wall: float = 3.0,
             build: float = 1.0, export: float = 0.5) -> Raw:
    probe = point["kind"] == "probe"
    reading: Raw = {
        "type": "reading", "label": point["label"], "kind": point["kind"],
        "params": point["args"] if probe else point["params"],
        "artifact": point["probe"] if probe else point["artifact"], "rep": rep, "status": status,
        "build_s": build, "export_s": export, "bytes": 10, "memory_peak_bytes": 10,
        "wall_s": wall}
    if "lift" in point:
        reading["lift"] = point["lift"]
    return reading


def _walls(over: Mapping[str, str] | None = None, drop: Iterable[str] = ()) -> list[Raw]:
    """A reading of every walls point, ok unless `over` says otherwise, minus the `drop` labels."""
    over, gone = over or {}, set(drop)
    return [_reading(p, over.get(str(p["label"]), "ok")) for p in _walls_points()
            if p["label"] not in gone]


def _down(stem: str, statuses: Mapping[int, str]) -> list[Raw]:
    """Walk-down readings of one cell: `statuses` by step."""
    return [{"type": "reading", "label": f"turns{n}-{stem}", "kind": stem.split("-")[0],
             "params": {}, "artifact": "stl-preview", "rep": 1, "status": status, "wall_s": 1.0}
            for n, status in statuses.items()]


def _tails(decades: Iterable[int], status: str) -> dict[str, str]:
    return {oper_sets._tail_label(d, pitch, left, k): status
            for k in decades for d, pitch in oper_sets.TAIL_SIZES for left in (False, True)}


def _roots(radii: Iterable[float], status: str,
           kinds: tuple[str, ...] = ("bolt", "nut")) -> dict[str, str]:
    return {oper_sets._root_label(kind, size, left, r): status for r in radii
            for size in PITCH for left in (False, True) for kind in kinds}


def _decide(walls: list[Raw], down: Iterable[Raw] = ()) -> oper_sets.Decision:
    return oper_sets.decide_walls(walls, down)


def _walls_as_read() -> dict[str, str]:
    """Walls group (d) as the first runner reading found it: every nut void refused at all nine
    radii, the rods refused from 3e-4 mm down (so F = 3e-4, the root floor R10 takes, G26)."""
    return (_roots(oper_sets.ROOT_RADII, "refused", ("nut",))
            | _roots(oper_sets.ROOT_RADII[3:], "refused", ("bolt",)))


def _stop(rule: str, naming: str = "") -> pytest.RaisesExc[ProtocolStop]:
    """The stop of `rule`, and, when given, naming `naming` in its text."""
    return pytest.raises(ProtocolStop, match=rf"\({rule}\).*{naming}")


def _tail_of(label: str) -> str:
    match = re.search(r"-(1e-\d)$", label)
    assert match
    return match.group(1)


def _root_of(label: str) -> str:
    match = re.search(r"-r([\d.e-]+)$", label)
    assert match
    return match.group(1)


# --- R5: the margin ------------------------------------------------------------------------------


def _spread(walls_by_rep: Mapping[str, list[float]]) -> list[Raw]:
    out: list[Raw] = []
    for label, walls in walls_by_rep.items():
        for rep, wall in enumerate(walls, start=1):
            point = {"label": label, "kind": "bolt", "params": {}, "artifact": "step"}
            out.append(_reading(point, rep=rep, build=wall - 0.5, export=0.5))
    return out


def test_the_margin_is_the_largest_max_over_median_of_the_cold_wall() -> None:
    result = oper_sets.margin(_spread({"a": [10, 10, 10, 10, 11], "b": [10, 11, 12, 13, 15]}))
    assert result.label == "b"
    assert result.m == pytest.approx(15 / 12 - 1)
    assert {p.label: p.maximum for p in result.points} == {"a": 11, "b": 15}


def test_a_spread_point_that_never_varies_has_a_margin_of_zero() -> None:
    assert oper_sets.margin(_spread({"a": [4, 4, 4, 4, 4]})).m == 0


@pytest.mark.parametrize("walls", [[10, 10, 10, 10], [10, 10, 10, 10, 10, 10]],
                         ids=["four-reps", "six-reps"])
def test_a_spread_point_without_five_repetitions_has_no_median(walls: list[float]) -> None:
    with _stop("R5", "point c"):
        oper_sets.margin(_spread({"a": [10, 10, 10, 10, 10], "b": [1] * 5}) + _spread({"c": walls}))


def test_a_spread_point_with_a_repetition_that_is_not_ok_has_no_median() -> None:
    readings = _spread({"a": [10, 10, 10, 10, 10]})
    readings[2]["status"] = "capped"
    with _stop("R5"):
        oper_sets.margin(readings)


def test_a_spread_point_with_one_repetition_read_twice_is_incomplete() -> None:
    readings = _spread({"a": [10, 10, 10, 10, 10]})
    readings[4]["rep"] = 3
    with _stop("R5"):
        oper_sets.margin(readings)


def test_a_spread_point_with_no_readings_at_all_has_no_median() -> None:
    with _stop("R5"):
        oper_sets.margin(_spread({"a": [10] * 5}), expected=[("a", "step"), ("b", "step")])


# --- R6: charges and shards ----------------------------------------------------------------------


def test_a_group_is_charged_its_largest_wall_whatever_the_status_of_that_reading() -> None:
    bolt = {"label": "x", "kind": "bolt", "params": {}, "artifact": "stl-preview"}
    readings = [_reading(bolt, wall=12.0), _reading({**bolt, "label": "y"}, "killed", wall=600.4),
                _reading({**bolt, "label": "z"}, wall=30.0),
                _reading({**bolt, "label": "n", "kind": "nut"}, wall=5.0)]
    table = oper_sets.charge_table(readings)
    assert table == {("bolt", "stl-preview"): 600.4, ("nut", "stl-preview"): 5.0}


def test_a_group_with_no_explore_reading_is_charged_its_deadline() -> None:
    table = {("bolt", "stl-preview"): 40.0}
    points: list[Raw] = [
        {"label": "a", "kind": "bolt", "params": {}, "artifact": "stl-preview"},
        {"label": "b", "kind": "bolt", "params": {}, "artifact": "step"},
        {"label": "t", "kind": "probe", "probe": "tail", "args": {}}]
    assert oper_sets.charges(points, table, 600.0) == [40.0, 600.0, 600.0]


def test_shards_are_the_longest_prefixes_strictly_under_half() -> None:
    assert oper_sets.shard_sizes([3000, 3000, 3000, 3000], 10500) == [3, 1]
    assert oper_sets.shard_sizes([5250, 5250, 5250], 10500) == [1, 1, 1]  # equal starts a new one
    assert oper_sets.shard_sizes([1, 1, 1], 10500) == [3]
    assert oper_sets.shard_sizes([], 10500) == []


def test_a_charge_not_under_half_the_job_timeout_stops_the_phase() -> None:
    with _stop("R6"):
        oper_sets.shard_sizes([10, 10500, 10], 10500)


def test_the_half_is_the_measure_jobs_timeout_in_the_workflow() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "operability.yml").read_text()
    measure = workflow[workflow.index("\n  measure:"):]
    match = re.search(r"timeout-minutes: (\d+)", measure)
    assert match
    assert int(match.group(1)) == oper_sets.MEASURE_TIMEOUT_MIN
    assert oper_sets.HALF_JOB_S == oper_sets.MEASURE_TIMEOUT_MIN * 30


# --- R7: the walk-down ---------------------------------------------------------------------------


def test_the_cell_constructor_builds_the_250_turn_points_the_walls_set_holds() -> None:
    held = {str(p["label"]): p["params"] for p in _walls_points() if p["kind"] != "probe"}
    for kind, size, left in oper_sets._cells():
        stem = oper_sets._stem(kind, size, left)
        assert oper_sets._turn_cell(kind, size, left, 250) == held[f"turns-{stem}"]
        assert oper_sets._turn_cell(kind, size, left, 260) == held[f"beyond-turns-{stem}"]


def test_no_walk_down_when_every_250_turn_reading_is_ok() -> None:
    assert oper_sets.walk_down_points(_walls()) == []


def test_a_refused_cell_is_walked_at_every_step_from_240_down_to_10() -> None:
    points = oper_sets.walk_down_points(_walls({"turns-nut-M8-left": "refused",
                                                "turns-bolt-M3-right": "crashed"}))
    assert len(points) == 48
    labels = [str(p["label"]) for p in points]
    assert labels[0] == "turns240-bolt-M3-right"
    assert labels[23] == "turns10-bolt-M3-right"
    assert {lb.split("-", 1)[1] for lb in labels} == {"bolt-M3-right", "nut-M8-left"}
    assert all(p["artifact"] == "stl-preview" and "lift" not in p for p in points)
    walked = next(p for p in points if p["label"] == "turns100-nut-M8-left")
    assert walked["params"] == oper_sets._turn_cell("nut", "M8", True, 100)


@pytest.mark.parametrize("status", ["killed", "capped", "no_cgroup"])
def test_a_250_turn_reading_that_is_cost_or_a_gap_stops_the_phase(status: str) -> None:
    with _stop("R7", "turns-bolt-M6-right"):
        oper_sets.walk_down_points(_walls({"turns-bolt-M6-right": status,
                                           "turns-nut-M8-left": "refused"}))


def test_a_missing_250_turn_reading_stops_the_phase() -> None:
    with _stop("R7", "turns-nut-M10-left"):
        oper_sets.walk_down_points(_walls(drop=["turns-nut-M10-left"]))


def test_the_walk_down_set_is_written_with_its_shards_and_sources(tmp_path: Path) -> None:
    out = oper_sets._walk_down_set(_walls({"turns-nut-M8-left": "refused"}))
    out.sharded({("nut", "stl-preview"): 600.0}, ["walls=w", "explore=e"])
    doc = json.loads(out.text())
    assert doc["set"] == "walls-down"
    assert (doc["reps"], doc["shards"], doc["shard_sizes"]) == (1, 2, [17, 7])
    assert doc["sources"] == ["walls=w", "explore=e"]
    (tmp_path / "walls-down.json").write_text(out.text())
    spec = oper.load_set("walls-down", tmp_path)
    assert [len(oper.shard_points(spec, n)) for n in (1, 2)] == [17, 7]  # 600 s each, 10500 s


# --- R7 to R10: the candidate walls --------------------------------------------------------------


def test_all_250_turn_readings_ok_give_t_250_and_the_tested_values_at_1e5() -> None:
    decision = _decide(_walls())
    assert decision.t == 250
    assert decision.max_field_mm == 1e5
    values = {key: c.value for key, c in decision.ceilings.items()}
    assert values[("bolt", "d")] == 99999.9
    assert values[("nut", "clearance")] == 49996.9
    assert values[("nut", "d")] == 99999.6
    others = [v for key, v in values.items()
              if key not in {("bolt", "d"), ("nut", "clearance"), ("nut", "d")}]
    assert others == [1e5] * 6
    assert (decision.tail.v, decision.root.v) == (None, None)
    assert (decision.tail.read, decision.root.read) == (48, 270)


def test_a_walked_cell_ends_at_its_first_ok_step_and_t_is_the_smallest() -> None:
    down = _down("nut-M8-left", {240: "refused", 230: "ok", 220: "ok"})
    decision = _decide(_walls({"turns-nut-M8-left": "refused"}), down)
    assert decision.first_ok["nut-M8-left"] == 230
    assert decision.t == 230
    assert "turns230-nut-M8-left" in decision.turn_labels
    assert "turns220-nut-M8-left" not in decision.turn_labels


def test_a_reading_below_the_first_ok_step_is_evidence_of_nothing() -> None:
    steps = dict.fromkeys(range(240, 200, -10), "refused") | {200: "ok", 190: "refused"}
    decision = _decide(_walls({"turns-bolt-M3-right": "crashed"}), _down("bolt-M3-right", steps))
    assert decision.first_ok["bolt-M3-right"] == 200
    assert decision.t == 200


@pytest.mark.parametrize("status", ["killed", "capped", "no_cgroup"])
def test_a_walk_down_reading_that_is_cost_stops_the_phase(status: str) -> None:
    with _stop("R7"):
        _decide(_walls({"turns-nut-M8-left": "refused"}),
                _down("nut-M8-left", {240: "refused", 230: status}))


def test_a_walk_down_reading_that_is_missing_stops_the_phase() -> None:
    with _stop("R7", "turns230-nut-M8-left"):
        _decide(_walls({"turns-nut-M8-left": "refused"}), _down("nut-M8-left", {240: "refused"}))


def test_a_cell_with_no_ok_step_stops_the_phase() -> None:
    every = dict.fromkeys(oper_sets.TURN_STEPS, "refused")
    with _stop("R7", "no ok step"):
        _decide(_walls({"turns-nut-M8-left": "refused"}), _down("nut-M8-left", every))


def test_a_refused_nutlead_reading_drops_the_nut_s_ceiling_a_decade() -> None:
    decision = _decide(_walls({"nutlead-M8-s100000": "refused"}))
    assert decision.ceilings[("nut", "s")].decade == 1e4
    assert decision.ceilings[("nut", "m")].decade == 1e5
    assert decision.max_field_mm == 1e5  # eight fields still share 1e5


def test_a_killed_reading_does_not_move_a_wall_but_cannot_raise_one() -> None:
    decision = _decide(_walls({"ceiling-bolt-k-100000": "killed",
                               "ceiling-bolt-k-10000": "capped"}))
    assert decision.ceilings[("bolt", "k")].decade == 1e3


def test_lifted_readings_past_a_cap_change_nothing() -> None:
    assert any(p.get("lift") for p in _walls_points())
    lifted = {str(p["label"]): "refused" for p in _walls_points() if p.get("lift")}
    assert _decide(_walls(lifted)) == _decide(_walls())
    assert _decide(_walls(drop=lifted)) == _decide(_walls())


def test_a_field_with_no_ok_decade_stops_the_phase() -> None:
    every = {f"ceiling-bolt-k-{x}": "refused" for x in (1000, 10000, 100000)}
    with _stop("R8"):
        _decide(_walls(every))


def test_a_missing_field_reading_stops_the_phase() -> None:
    with _stop("R8", "ceiling-nut-m-100000"):
        _decide(_walls(drop=["ceiling-nut-m-100000"]))


def test_the_ceiling_shared_by_most_fields_is_max_field_mm_and_a_tie_goes_low() -> None:
    low = {f"ceiling-{stem}-100000": "refused"
           for stem in ("bolt-length", "bolt-s", "bolt-k", "nut-m", "nut-clearance")}
    assert _decide(_walls(low)).max_field_mm == 1e4  # 5 fields at 1e4, 4 at 1e5
    assert _decide(_walls({"ceiling-bolt-k-100000": "refused",
                           "ceiling-nut-m-100000": "refused"})).max_field_mm == 1e5
    three = {f"ceiling-{stem}-{x}": "refused" for stem in ("bolt-k", "nut-m", "nut-clearance")
             for x in (10000, 100000)}
    three |= {f"ceiling-{stem}-100000": "refused" for stem in ("bolt-length", "bolt-s", "nut-d")}
    assert _decide(_walls(three)).max_field_mm == 1e3  # 3, 3 and 3: the lowest


def test_the_largest_failing_tail_sets_v_a_hundred_times_above_it() -> None:
    decision = _decide(_walls(_tails([8, 9], "crashed") | _tails([5], "ok")))
    assert decision.tail.v == 1e-6
    assert decision.tail.failing[0].endswith("1e-8")
    assert len(decision.tail.failing) == 12


def test_the_largest_failing_root_sets_v_ten_times_above_it() -> None:
    decision = _decide(_walls(_roots([3e-5, 1e-5, 3e-6, 1e-6], "refused")))
    assert decision.root.v == 1e-3


def test_one_failing_cell_is_enough_for_f() -> None:
    label = oper_sets._tail_label(2.0, 0.4, True, 6)
    assert _decide(_walls({label: "refused"})).tail.v == 1e-4


def test_a_failing_tail_whose_v_lies_outside_the_walk_stops_the_phase() -> None:
    with _stop("R9"):
        _decide(_walls(_tails([3, 4, 5, 6, 7, 8, 9], "crashed")))


def test_voids_refused_everywhere_do_not_stop_r10() -> None:
    decision = _decide(_walls(_walls_as_read()))
    assert decision.root.v == 1e-2
    assert decision.root.read == 270
    assert all(label.startswith("root-bolt-") for label in decision.root.failing)
    assert decision.root.failing[0] == oper_sets._root_label("bolt", "M2", False, 3e-4)
    nuts = _roots(oper_sets.ROOT_RADII, "refused", ("nut",))
    assert _decide(_walls(nuts)).root.v is None  # every rod ok: "above 0"
    assert _decide(_walls(drop=nuts)).root.v is None


def test_a_rod_refused_at_1e_3_gives_v_of_1e_2() -> None:
    decision = _decide(_walls(_roots([1e-3], "refused", ("bolt",))))
    assert decision.root.v == 1e-2  # 10 F lands exactly on a power of ten


def test_a_rod_refused_at_3e_3_puts_v_above_the_rod_walk_and_stops_the_phase() -> None:
    # The rods are walked from 1e-2 down, and no rod reading stands at 0.1.
    with _stop("R10", "V is 0.1, which lies outside the walk"):
        _decide(_walls(_roots([3e-3], "refused", ("bolt",))))


def test_rods_refused_at_1e_2_stop_the_phase() -> None:
    with _stop("R10", "the largest failing value is 0.01"):
        _decide(_walls(_roots([1e-2], "refused", ("bolt",))))


def test_a_killed_rod_at_or_above_v_stops_the_phase_and_a_killed_nut_does_not() -> None:
    rods = _roots(oper_sets.ROOT_RADII[3:], "refused", ("bolt",))
    label = oper_sets._root_label("bolt", "M8", True, 1e-2)
    with _stop("R10", label):
        _decide(_walls(rods | {label: "killed"}))
    nut = oper_sets._root_label("nut", "M8", True, 1e-2)
    assert _decide(_walls(rods | {nut: "killed"})).root.v == 1e-2


def test_a_killed_reading_at_or_above_v_stops_the_phase() -> None:
    over = _tails([8, 9], "crashed") | _tails([5], "killed")
    with _stop("R9"):
        _decide(_walls(over))
    with _stop("R10"):
        _decide(_walls(_roots([1e-5], "refused") | _roots([1e-3], "capped")))


def test_a_killed_reading_below_v_stops_nothing_and_sets_no_f() -> None:
    decision = _decide(_walls(_tails([8, 9], "crashed") | _tails([7], "killed")))
    assert decision.tail.v == 1e-6


def test_a_capped_reading_in_a_clean_walk_denies_above_zero() -> None:
    with _stop("R9"):
        _decide(_walls({oper_sets._tail_label(6.0, 1.0, False, 9): "capped"}))
    with _stop("R10"):
        _decide(_walls(_roots([1e-6], "no_cgroup")))


@pytest.mark.parametrize(("rule", "label"), [
    ("R9", oper_sets._tail_label(6.0, 1.0, False, 9)),
    ("R10", oper_sets._root_label("bolt", "M8", True, 1e-6))])
def test_a_missing_tail_or_root_reading_stops_the_phase(rule: str, label: str) -> None:
    with _stop(rule):
        _decide(_walls(drop=[label]))


# --- R3: the walls confirm set -------------------------------------------------------------------


def _decision(over: Mapping[str, str] | None = None,
              down: list[Raw] | None = None) -> oper_sets.Decision:
    return _decide(_walls(over), down or ())


def _labels(points: Iterable[Mapping[str, object]]) -> list[str]:
    return [str(p["label"]) for p in points]


def test_the_confirm_set_at_t_250_holds_the_walls_points_and_the_lifted_260s() -> None:
    points = oper_sets.confirm_points(_decision())
    turns = [p for p in points if str(p["label"]).startswith(("turns-", "beyond-turns-"))]
    assert len(turns) == 120
    assert sum(str(p["label"]).startswith("turns-") for p in turns) == 60
    beyond = [p for p in turns if str(p["label"]).startswith("beyond-turns-")]
    assert len(beyond) == 60
    assert all(p["lift"] == {"max_turns": 260} for p in beyond)


def test_the_confirm_set_below_250_builds_the_cells_at_t_and_t_plus_10() -> None:
    down = _down("nut-M8-left", {240: "refused", 230: "ok"})
    decision = _decision({"turns-nut-M8-left": "refused"}, down)
    points = oper_sets.confirm_points(decision)
    labels = _labels(points)
    assert sum(lb.startswith("turns230-") for lb in labels) == 60
    assert sum(lb.startswith("turns240-") for lb in labels) == 60
    assert not any(lb.startswith(("turns-", "beyond-turns-")) for lb in labels)
    held = {str(p["label"]): p for p in points}
    assert held["turns230-bolt-M20-right"]["params"] == \
        oper_sets._turn_cell("bolt", "M20", False, 230)


def test_the_confirm_set_at_t_240_reads_the_250s_the_walls_set_holds() -> None:
    steps = {240: "ok"}
    down = _down("nut-M8-left", steps)
    points = oper_sets.confirm_points(_decision({"turns-nut-M8-left": "refused"}, down))
    labels = _labels(points)
    assert sum(lb.startswith("turns240-") for lb in labels) == 60
    assert sum(lb.startswith("turns-") for lb in labels) == 60


def test_the_confirm_set_copies_the_walls_points_verbatim_lift_included() -> None:
    held = {str(p["label"]): p for p in _walls_points()}
    for point in oper_sets.confirm_points(_decision()):
        assert point == held[str(point["label"])]


def test_every_field_is_confirmed_at_its_decade_and_the_next_each_label_once() -> None:
    labels = _labels(oper_sets.confirm_points(_decision()))
    assert len(labels) == len(set(labels))
    for stem in ("bolt-d", "bolt-length", "bolt-s", "bolt-k", "bolt-thread", "nut-s", "nut-d",
                 "nut-m", "nut-clearance"):
        assert f"ceiling-{stem}-100000" in labels
        assert f"beyond-{stem}-1000000" in labels
    assert not any(lb.startswith("nutlead") and "1000000" in lb for lb in labels)
    assert sum(lb.startswith("nutlead") for lb in labels) == 3
    assert "ceiling-bolt-d-10000" not in labels


def test_a_field_decided_at_1e4_is_confirmed_at_1e4_and_1e5() -> None:
    labels = _labels(oper_sets.confirm_points(_decision({"ceiling-bolt-k-100000": "refused"})))
    assert {"ceiling-bolt-k-10000", "ceiling-bolt-k-100000"} <= set(labels)
    assert "beyond-bolt-k-1000000" not in labels


def test_the_lifted_confirm_points_past_1e5_carry_their_lift() -> None:
    points = oper_sets.confirm_points(_decision())
    beyond = [p for p in points if str(p["label"]).startswith("beyond-") and "turns" not in
              str(p["label"])]
    assert len(beyond) == 9
    assert all(p["lift"] == {"max_mm": 1e6} for p in beyond)


def test_tail_and_root_are_confirmed_at_v_and_the_next_smaller_walked_value() -> None:
    over = _tails([8, 9], "crashed") | _roots([3e-5, 1e-5], "refused")
    labels = _labels(oper_sets.confirm_points(_decision(over)))
    tails = [lb for lb in labels if lb.startswith("tail-")]
    assert len(tails) == 12
    assert {_tail_of(lb) for lb in tails} == {"1e-6", "1e-7"}
    roots = [lb for lb in labels if lb.startswith("root-")]
    assert len(roots) == 60
    assert all(lb.startswith("root-bolt-") for lb in roots)
    assert {_root_of(lb) for lb in roots} == {"0.001", "0.0003"}


def test_r10_is_confirmed_on_the_rods_at_v_and_the_next_smaller_radius() -> None:
    held = {str(p["label"]): p for p in _walls_points()}
    decision = _decision(_walls_as_read())
    assert decision.root.v == 1e-2
    roots = [p for p in oper_sets.confirm_points(decision) if str(p["label"]).startswith("root-")]
    assert len(roots) == 60
    assert all(str(p["label"]).startswith("root-bolt-") for p in roots)
    assert {_root_of(str(p["label"])) for p in roots} == {"0.01", "0.003"}
    assert all(p == held[str(p["label"])] for p in roots)


def test_above_zero_is_confirmed_at_the_smallest_walked_value_and_nothing_past_it() -> None:
    labels = _labels(oper_sets.confirm_points(_decision()))
    tails = [lb for lb in labels if lb.startswith("tail-")]
    assert len(tails) == 6
    assert {_tail_of(lb) for lb in tails} == {"1e-9"}
    roots = [lb for lb in labels if lb.startswith("root-")]
    assert len(roots) == 30
    assert all(lb.startswith("root-bolt-") for lb in roots)
    assert {_root_of(lb) for lb in roots} == {"1e-06"}


# --- the files and the command -------------------------------------------------------------------


def _write_records(directory: Path, readings: Iterable[Raw], shard: int = 1) -> None:
    folder = directory / f"oper-x-{shard}-1"
    folder.mkdir(parents=True)
    lines = [json.dumps({"type": "header", "GITHUB_RUN_ID": "1"}),
             *(json.dumps(r) for r in readings)]
    (folder / f"oper-x-{shard}-1.jsonl").write_text("\n".join(lines) + "\n")


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path.resolve()
    (root / "points").mkdir()
    monkeypatch.setattr(oper_sets, "REPO_ROOT", root)
    monkeypatch.setattr(oper_sets, "POINTS_DIR", root / "points")
    explore = [_reading({"label": f"e{kind}", "kind": kind, "params": {},
                         "artifact": "stl-preview"}, wall=wall)
               for kind, wall in (("bolt", 3000.0), ("nut", 2000.0))]
    _write_records(root / "explore", explore)
    _write_records(root / "walls", _walls())
    return root


def test_a_missing_directory_of_records_is_an_error_and_not_a_stop(
        repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert oper_sets.main(["charges", "--explore", str(repo / "nowhere")]) == 2
    assert "oper_sets:" in capsys.readouterr().err


def test_the_charges_command_prints_the_largest_wall_per_group(
        repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert oper_sets.main(["charges", "--explore", str(repo / "explore")]) == 0
    out = capsys.readouterr().out
    assert "bolt | stl-preview | 3000.0" in out
    assert "nut | stl-preview | 2000.0" in out


def test_the_margin_command_stops_with_exit_3_on_a_point_without_a_median(
        repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    points = oper_sets.spread().points
    readings = [_reading(p, rep=rep) for p in points for rep in range(1, 6)]
    _write_records(repo / "spread", readings[:-1])
    assert oper_sets.main(["margin", "--spread", str(repo / "spread")]) == 3
    assert "oper_sets: stop (R5):" in capsys.readouterr().err
    _write_records(repo / "spread2", readings)
    assert oper_sets.main(["margin", "--spread", str(repo / "spread2")]) == 0
    assert "m = 0.0, set by" in capsys.readouterr().out


def test_walk_down_command_writes_nothing_when_every_250_turn_reading_is_ok(
        repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = repo / "points" / "walls-down.json"
    args = ["walk-down", "--walls", str(repo / "walls"), "--explore", str(repo / "explore"),
            "--out", str(out)]
    assert oper_sets.main(args) == 0
    assert "no walk-down: every 250-turn reading is ok" in capsys.readouterr().out
    assert not out.exists()


def test_the_walk_down_and_confirm_files_are_written_and_checked_from_their_sources(
        repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    refused = _walls({"turns-nut-M8-left": "refused"})
    (repo / "walls2").mkdir()
    _write_records(repo / "walls2", refused)
    down = repo / "points" / "walls-down.json"
    assert oper_sets.main(["walk-down", "--walls", str(repo / "walls2"), "--explore",
                           str(repo / "explore"), "--out", str(down)]) == 0
    doc = json.loads(down.read_text())
    assert doc["sources"] == ["walls=walls2", "explore=explore"]
    assert sum(doc["shard_sizes"]) == 24 == len(doc["points"])
    assert doc["shard_sizes"] == [5, 5, 5, 5, 4]  # nuts are charged 2000 s, half is 10500

    _write_records(repo / "down", _down("nut-M8-left", {240: "refused", 230: "ok"}))
    confirm = repo / "points" / "walls-confirm.json"
    assert oper_sets.main(["decide-walls", "--walls", str(repo / "walls2"), "--down",
                           str(repo / "down")]) == 0
    assert "T = 230 turns" in capsys.readouterr().out
    assert oper_sets.main(["confirm", "--walls", str(repo / "walls2"), "--down",
                           str(repo / "down"), "--explore", str(repo / "explore"),
                           "--out", str(confirm)]) == 0
    doc = json.loads(confirm.read_text())
    assert doc["reps"] == 5
    assert sum(doc["shard_sizes"]) == len(doc["points"])
    assert doc["sources"] == ["walls=walls2", "walls-down=down", "explore=explore"]
    spec = oper.load_set("walls-confirm", repo / "points")
    assert sum(len(oper.shard_points(spec, n)) for n in range(1, spec.shards + 1)) == \
        len(spec.points)
    # bolt, nut, bolt, nut is 10000 s; a fifth point (a bolt, 3000 s) does not fit under 10500
    assert doc["shard_sizes"][0] == 4

    capsys.readouterr()
    for name, text in oper_sets.generate().items():
        (repo / "points" / f"{name}.json").write_text(text)
    assert oper_sets.main(["--check"]) == 0
    confirm.write_text(confirm.read_text().replace('"reps": 5', '"reps": 4'))
    assert oper_sets.main(["--check"]) == 1
    assert "walls-confirm.json" in capsys.readouterr().err


def test_check_fails_when_a_source_can_no_longer_give_the_set(
        repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (repo / "walls2").mkdir()
    _write_records(repo / "walls2", _walls({"turns-nut-M8-left": "refused"}))
    down = repo / "points" / "walls-down.json"
    assert oper_sets.main(["walk-down", "--walls", str(repo / "walls2"), "--explore",
                           str(repo / "explore"), "--out", str(down)]) == 0
    for name, text in oper_sets.generate().items():
        (repo / "points" / f"{name}.json").write_text(text)
    assert oper_sets.main(["--check"]) == 0
    (repo / "walls2" / "oper-x-1-1" / "oper-x-1-1.jsonl").write_text("")
    capsys.readouterr()
    assert oper_sets.main(["--check"]) == 1
    assert "walls-down.json" in capsys.readouterr().err


def test_a_stop_in_decide_walls_exits_3_and_names_the_rule(
        repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (repo / "walls2").mkdir()
    _write_records(repo / "walls2", _walls({"turns-nut-M8-left": "refused"}))
    assert oper_sets.main(["decide-walls", "--walls", str(repo / "walls2")]) == 3
    assert "oper_sets: stop (R7):" in capsys.readouterr().err


@pytest.mark.parametrize("command", ["decide-walls", "confirm"])
def test_decide_walls_and_confirm_take_no_void_walk(repo: Path, command: str) -> None:
    args = [command, "--walls", str(repo / "walls"), "--voids", str(repo / "voids")]
    if command == "confirm":
        args += ["--explore", str(repo / "explore"), "--out", str(repo / "out.json")]
    with pytest.raises(SystemExit) as stop:
        oper_sets.main(args)
    assert stop.value.code == 2


def test_decide_walls_prints_the_rods_only_root_floor(
        repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_records(repo / "as-read", _walls(_walls_as_read()))
    assert oper_sets.main(["decide-walls", "--walls", str(repo / "as-read")]) == 0
    assert "root (R10): V = 0.01 mm; 270 readings read" in capsys.readouterr().out

    _write_records(repo / "rods-1e-2", _walls(_roots([1e-2], "refused", ("bolt",))))
    assert oper_sets.main(["decide-walls", "--walls", str(repo / "rods-1e-2")]) == 3
    assert "oper_sets: stop (R10):" in capsys.readouterr().err


def test_the_void_walk_is_written_with_its_shards_and_checked_from_its_source(
        repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    voids = repo / "points" / "walls-voids.json"
    assert oper_sets.main(["void-walk", "--explore", str(repo / "explore"),
                           "--out", str(voids)]) == 0
    assert "120 points in shards of [5, 5," in capsys.readouterr().out
    doc = json.loads(voids.read_text())
    assert doc["sources"] == ["explore=explore"]
    assert doc["shard_sizes"] == [5] * 24  # nuts are charged 2000 s, half is 10500
    assert (doc["set"], doc["reps"], doc["shards"]) == ("walls-voids", 1, 24)

    for name, text in oper_sets.generate().items():
        (repo / "points" / f"{name}.json").write_text(text)
    assert oper_sets.main(["--check"]) == 0
    voids.write_text(voids.read_text().replace('"reps": 1', '"reps": 2'))
    capsys.readouterr()
    assert oper_sets.main(["--check"]) == 1
    assert "walls-voids.json" in capsys.readouterr().err


# --- R3, R7 to R10: the walls, decided with their confirm (07-07) ---------------------------------

REPS = (1, 2, 3, 4, 5)
WALLS_DIRS = ("walls-40646134133", "walls-down-40652801529", "walls-confirm-40678150220")


def _confirm_of(decision: oper_sets.Decision, over: Mapping[str, str] | None = None,
                rep_over: Mapping[tuple[str, int], str] | None = None,
                drop: Iterable[tuple[str, int]] = ()) -> list[Raw]:
    """The 5 repetitions of every point of the confirm set the candidate asks for, ok unless
    `over` (a label, all repetitions) or `rep_over` (one repetition) says otherwise."""
    over, rep_over, gone = over or {}, rep_over or {}, set(drop)
    return [_reading(p, rep_over.get((str(p["label"]), rep), over.get(str(p["label"]), "ok")), rep)
            for p in oper_sets.confirm_points(decision) for rep in REPS
            if (str(p["label"]), rep) not in gone]


def _derive(walls_over: Mapping[str, str] | None = None, down: list[Raw] | None = None,
            over: Mapping[str, str] | None = None,
            rep_over: Mapping[tuple[str, int], str] | None = None,
            drop: Iterable[tuple[str, int]] = ()) -> oper_sets.Derived:
    walls = _walls(walls_over)
    confirm = _confirm_of(_decide(walls, down or ()), over, rep_over, drop)
    return oper_sets.derive_walls(walls, down or (), confirm)


def _confirm_dup(confirm: list[Raw], label: str) -> list[Raw]:
    """`confirm` with repetition 4 of `label` replaced by a second copy of repetition 3."""
    return [r | {"rep": 3} if (r["label"], r["rep"]) == (label, 4) else r for r in confirm]


def test_every_cell_ok_five_times_at_250_confirms_250_and_the_tested_values() -> None:
    result = _derive()
    assert result.max_turns == 250
    assert len(result.turn_labels) == 60
    assert result.max_field_mm == 1e5
    assert result.constants == {"MAX_BOLT_D_MM": 99999.9, "MAX_NUT_D_MM": 99999.6,
                                "MAX_NUT_CLEARANCE_MM": 49996.9}
    assert (result.tail.v, result.root.v) == (None, None)
    assert result.notes == ()


def test_a_refused_250_cell_walked_down_and_confirmed_at_240_gives_240() -> None:
    down = _down("nut-M8-left", {240: "ok"})
    result = _derive({"turns-nut-M8-left": "refused"}, down)
    assert result.max_turns == 240
    assert "turns240-nut-M8-left" in result.turn_labels
    assert result.past["MAX_TURNS"].startswith("250 turns")


def test_a_killed_250_reading_awards_no_turn_bound_250_included() -> None:
    walls = _walls({"turns-bolt-M2-right": "killed"})
    with _stop("R7", "turns-bolt-M2-right"):
        oper_sets.derive_walls(walls, (), [])


def test_a_confirm_repetition_at_t_that_is_not_ok_awards_no_turn_bound() -> None:
    with _stop("R7", "turns-bolt-M8-left"):
        _derive(rep_over={("turns-bolt-M8-left", 4): "capped"})


def test_a_confirm_at_t_missing_a_repetition_for_one_cell_awards_no_turn_bound() -> None:
    with _stop("R7", "turns-nut-M14-right"):
        _derive(drop=[("turns-nut-M14-right", 2)])


def test_a_confirm_at_t_missing_for_a_cell_awards_no_turn_bound() -> None:
    with _stop("R7", "turns-nut-M14-right"):
        _derive(drop=[("turns-nut-M14-right", rep) for rep in REPS])


def test_a_cell_with_no_ok_walk_down_step_or_a_gap_above_it_awards_no_turn_bound() -> None:
    every = dict.fromkeys(oper_sets.TURN_STEPS, "refused")
    with _stop("R7", "no ok step"):
        _derive({"turns-nut-M8-left": "refused"}, _down("nut-M8-left", every))
    with _stop("R7", "turns230-nut-M8-left"):
        _derive({"turns-nut-M8-left": "refused"}, _down("nut-M8-left", {240: "refused"}))


def test_a_confirm_point_without_repetitions_one_to_five_each_once_stops_at_r3() -> None:
    walls = _walls()
    confirm = _confirm_dup(_confirm_of(_decide(walls)), "turns-bolt-M2-right")
    with _stop("R3", "turns-bolt-M2-right"):
        oper_sets.derive_walls(walls, (), confirm)


def test_a_lifted_ok_reading_past_a_cap_awards_nothing() -> None:
    result = _derive(over={"beyond-bolt-k-1000000": "ok", "beyond-bolt-thread-1000000": "ok"})
    assert result.max_turns == 250
    assert all(c.decade <= 1e5 and c.value <= 1e5 for c in result.ceilings.values())
    lifted = [str(p["label"]) for p in _walls_points() if p.get("lift")]
    refused = _derive(over=dict.fromkeys(lifted, "refused"))
    assert refused.max_turns == 250
    assert refused.constants == result.constants


def test_a_confirm_repetition_at_the_decided_decade_that_fails_makes_the_ceiling_stricter() -> None:
    result = _derive(rep_over={("ceiling-bolt-k-100000", 3): "refused"})
    assert result.ceilings[("bolt", "k")].decade == 1e4
    assert result.constants["MAX_BOLT_K_MM"] == 1e4
    assert result.max_field_mm == 1e5
    assert any(note.startswith("bolt k:") and "stricter" in note for note in result.notes)


def test_a_cost_repetition_at_the_decided_decade_cannot_hold_it() -> None:
    result = _derive(rep_over={("ceiling-nut-m-100000", 2): "capped"})
    assert result.ceilings[("nut", "m")].decade == 1e4


def test_a_candidate_decade_the_confirm_does_not_hold_stops_the_phase() -> None:
    with _stop("R8", "ceiling-bolt-k-100000"):
        _derive(drop=[("ceiling-bolt-k-100000", rep) for rep in REPS])


def test_a_field_with_no_ok_decade_stops_the_phase_after_the_confirm_too() -> None:
    every = {f"ceiling-bolt-k-{x}": "refused" for x in (1000, 10000, 100000)}
    with _stop("R8", "bolt k"):
        oper_sets.derive_walls(_walls(every), (), [])


@pytest.mark.parametrize(("decades", "tail"), [((8, 9), 1e-6), ((4, 5, 6, 7, 8, 9), 1e-2)])
def test_the_largest_failing_tail_sets_the_floor_a_hundred_times_above_it(
        decades: tuple[int, ...], tail: float) -> None:
    result = _derive(_tails(decades, "refused"))
    assert result.tail.v == tail
    assert result.root.v is None


def test_a_tail_floor_outside_the_walk_or_over_a_killed_reading_stops_the_phase() -> None:
    with _stop("R9", "outside the walk"):
        _derive(_tails(range(3, 10), "refused"))
    with _stop("R9", "killed"):
        _derive(_tails((8, 9), "refused") | {oper_sets._tail_label(6.0, 1.0, False, 3): "killed"})


def test_above_zero_stands_only_on_the_smallest_tail_read_ok_five_times() -> None:
    result = _derive()
    assert result.tail.v is None
    assert result.tail.read == 48
    label = oper_sets._tail_label(6.0, 1.0, False, 9)
    with _stop("R9", "G1"):
        _derive(rep_over={(label, 2): "crashed"})
    with _stop("R9", "G1"):
        _derive(rep_over={(label, 5): "capped"})
    with _stop("R9", "G1"):
        _derive(drop=[(label, rep) for rep in REPS])
    with _stop("R9", "above 0"):
        _decide(_walls(_tails((5,), "capped")))


def test_a_confirm_repetition_below_the_floor_makes_it_stricter_only_if_it_was_confirmed() -> None:
    label = oper_sets._tail_label(6.0, 1.0, False, 5)  # the step past V = 1e-4, read in the confirm
    with _stop("R9", "no confirm reading tested"):
        _derive(_tails((6, 7, 8, 9), "refused"), rep_over={(label, 3): "refused"})


def test_the_largest_failing_rod_root_sets_the_floor_ten_times_above_it() -> None:
    result = _derive(_roots([3e-5, 1e-5, 3e-6, 1e-6], "refused", ("bolt",)))
    assert result.root.v == 1e-3
    assert result.tail.v is None


def test_voids_refused_everywhere_are_no_part_of_the_root_floor() -> None:
    result = _derive(_walls_as_read())
    assert result.root.v == 1e-2
    assert result.root.read == 270


def test_above_zero_for_the_root_stands_only_on_the_smallest_rod_read_ok_five_times() -> None:
    result = _derive()
    assert result.root.v is None
    smallest = [str(p["label"]) for p in oper_sets.confirm_points(_decide(_walls()))
                if str(p["label"]).startswith("root-") and str(p["label"]).endswith("-r1e-06")]
    assert len(smallest) == 30  # the rods, every size and hand; no nut void
    assert all("-bolt-" in label for label in smallest)
    with _stop("R10", "G1"):
        _derive(rep_over={(smallest[0], 3): "refused"})


def test_a_nut_d_with_no_confirmed_decade_needs_a_shared_ceiling_below_its_refused_decade() -> None:
    cost = {"ceiling-nut-d-1000": "capped"}
    refused = {f"ceiling-nut-d-{x}": "refused" for x in (10000, 100000)}
    with _stop("R8", "G27"):
        _derive(refused, over=cost)  # the shared ceiling is 1e5, not below the refused decade 1e4
    with _stop("R8", "nut d has no ok decade"):
        _derive(refused, over={"ceiling-nut-d-1000": "refused"})  # a wall, not cost
    with _stop("R8", "nut d has no ok decade"):
        _derive({"ceiling-nut-d-1000": "refused"} | refused)


def _read_all() -> tuple[list[oper_sets.Reading], list[oper_sets.Reading],
                         list[oper_sets.Reading]]:
    base = REPO_ROOT / "bench" / "results" / "phase-07"
    walls, down, confirm = (oper_sets.read_readings(base / name) for name in WALLS_DIRS)
    return walls, down, confirm


@functools.cache
def _committed() -> oper_sets.Derived:
    walls, down, confirm = _read_all()
    return oper_sets.derive_walls(walls, down, confirm)


def test_the_committed_records_give_the_walls_07_07_writes() -> None:
    result = _committed()
    assert result.max_turns == 90
    assert result.max_field_mm == 1000.0
    assert result.constants == {
        "MAX_BOLT_D_MM": 999.999, "MAX_BOLT_LENGTH_MM": 10000.0, "MAX_BOLT_K_MM": 100000.0,
        "MAX_BOLT_THREAD_LENGTH_MM": 100000.0, "MAX_NUT_M_MM": 10000.0,
        "MAX_NUT_CLEARANCE_MM": 496.999}
    assert ("nut", "d") in result.cost_limited
    assert ("nut", "d") not in result.ceilings
    assert result.cost_limited[("nut", "d")] == 1e4
    assert (result.tail.v, result.root.v) == (1e-4, 1e-2)
    assert len(result.notes) == 1
    assert result.notes[0].startswith("nut d:")


def test_the_committed_records_leave_the_walls_the_candidate_decided_but_nut_d() -> None:
    walls, down, _ = _read_all()
    result = _committed()
    candidate = oper_sets.decide_walls(walls, down)
    assert candidate.t == result.max_turns
    for key, ceiling in result.ceilings.items():
        assert ceiling == candidate.ceilings[key]
    assert (candidate.tail.v, candidate.root.v) == (result.tail.v, result.root.v)


def test_derive_walls_prints_each_wall_with_its_readings_and_the_nut_d_exception(
        capsys: pytest.CaptureFixture[str]) -> None:
    base = REPO_ROOT / "bench" / "results" / "phase-07"
    walls, down, confirm = (str(base / name) for name in WALLS_DIRS)
    args = ["derive-walls", "--walls", walls, "--down", down, "--confirm", confirm]
    assert oper_sets.main(args) == 0
    out = capsys.readouterr().out
    assert "MAX_TURNS = 90 " in out
    assert "MAX_FIELD_MM = 1000.0 " in out
    assert "MAX_BOLT_D_MM = 999.999" in out
    assert "MIN_TAIL_MM = 0.0001 " in out
    assert "MIN_ROOT_RADIUS_MM = 0.01 " in out
    assert "MAX_NUT_D_MM" not in out
    assert "nut d: no constant of its own (G27" in out


def test_derive_walls_exits_3_on_a_stop_and_on_an_above_zero_tail(
        repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    walls = _walls()
    _write_records(repo / "w", walls)
    _write_records(repo / "c-ok", _confirm_of(_decide(walls)))
    args = ["derive-walls", "--walls", str(repo / "w"), "--confirm", str(repo / "c-ok")]
    assert oper_sets.main(args) == 3
    captured = capsys.readouterr()
    assert "MIN_ROOT_RADIUS_MM = above 0" in captured.out
    assert "oper_sets: stop (R9):" in captured.err
    assert "builder's guard" in captured.err

    _write_records(repo / "c-bad", _confirm_of(
        _decide(walls), rep_over={("turns-bolt-M2-right", 4): "capped"}))
    assert oper_sets.main(["derive-walls", "--walls", str(repo / "w"),
                           "--confirm", str(repo / "c-bad")]) == 3
    assert "oper_sets: stop (R7):" in capsys.readouterr().err


def test_the_source_constants_equal_what_derive_walls_gives_for_the_records() -> None:
    """No wall in the code can drift from its evidence (07 D-08, D-18, T-07-19)."""
    from screw import params
    from screw.calc import thread

    result = _committed()
    assert result.max_turns == thread.MAX_TURNS
    assert result.tail.v == thread.MIN_TAIL_MM
    assert result.root.v == thread.MIN_ROOT_RADIUS_MM
    assert result.max_field_mm == params.MAX_FIELD_MM
    for name, value in result.constants.items():
        assert getattr(params, name) == value, name
    # every per-field constant in the source is one derive_walls printed, and the nut d has none
    declared = {name for name in vars(params) if re.fullmatch(r"[A-Z_]*MAX_[A-Z_]*MM", name)}
    assert declared == {"MAX_FIELD_MM", *result.constants}
    assert "MAX_NUT_D_MM" not in declared
    # a field with a wall of its own carries it, one without carries the shared one
    for (kind, field), ceiling in result.ceilings.items():
        model = params.KINDS[kind]
        [le] = [m.le for m in model.model_fields[field].metadata if hasattr(m, "le")]
        assert le == ceiling.value
    [nut_d] = [m.le for m in params.NutParams.model_fields["d"].metadata if hasattr(m, "le")]
    assert nut_d == params.MAX_FIELD_MM


# --- Runs II (07-15): D(A), the bound set, the load mix and the gzip set -------------------------

ARTIFACTS3: tuple[cost.Artifact, ...] = cost.ARTIFACTS
UNBOUNDED: oper_sets.Budget = dict.fromkeys(ARTIFACTS3, (None, None, None))


def _flat(e: float = 0.5, **over: float) -> dict[tuple[str, str, str], float]:
    """An envelope of `e` everywhere, with `over` keyed `kind_target` (every artifact)."""
    envelope = dict.fromkeys(oper_sets.shipped_envelope(), e)
    for name, value in over.items():
        kind, target = name.split("_")
        for artifact in ARTIFACTS3:
            envelope[kind, artifact, target] = value
    return envelope


def _pt(label: str, kind: str, params: Mapping[str, object], artifact: str) -> Raw:
    return {"label": label, "kind": kind, "params": dict(params), "artifact": artifact}


def _bolts(lengths: Iterable[float], prefix: str = "b") -> list[Raw]:
    """A bolt per length at every artifact, labelled `<prefix><i>`, in file order."""
    return [_pt(f"{prefix}{i}", "bolt", {"length": length}, artifact)
            for i, length in enumerate(lengths) for artifact in ARTIFACTS3]


def _ok_readings(points: Iterable[Mapping[str, object]], **over: Mapping[str, object]) -> list[Raw]:
    """An ok explore reading of every point; `over[label]` replaces fields of its readings."""
    out: list[Raw] = []
    for p in points:
        reading = _reading(p, build=1.0, export=0.5)
        reading.update(over.get(str(p["label"]), {}))
        out.append(reading)
    return out


def _part(point: Mapping[str, object]) -> FastenerParams:
    params = point["params"]
    assert isinstance(params, dict)
    return KINDS[str(point["kind"])].model_validate(params)


def _env_seconds(point: Mapping[str, object], artifact: cost.Artifact,
                 envelope: Mapping[tuple[str, str, str], float]) -> float:
    part = _part(point)
    return cost.predict(part, artifact).seconds * (1.0 + envelope[part.kind, artifact, "seconds"])


def test_d_of_a_keeps_the_first_of_two_points_that_are_one_part() -> None:
    points = [_pt("z-first", "bolt", {"length": 30.0}, "step"),
              _pt("a-second", "bolt", {"length": 30.0}, "step"),
              _pt("c", "nut", {}, "step")]
    found = oper_sets.candidates(points, "step", _flat(), UNBOUNDED)
    assert [c.label for c in found] == ["z-first", "c"]


def test_the_edge_ratio_under_a_finite_budget_is_the_largest_enveloped_prediction() -> None:
    envelope = _flat(0.25, bolt_peak=2.0)
    budget: oper_sets.Budget = dict.fromkeys(ARTIFACTS3, (50000000.0, 30.0, 1000000000.0))
    points = _bolts([10.0, 20.0, 40.0])
    order = oper_sets.tier_order(points, envelope, budget)
    for artifact in ARTIFACTS3:
        ranking = order[artifact]["edge_ranking"]
        assert isinstance(ranking, list)
        for item in ranking:
            point = next(p for p in points
                         if p["label"] == item["label"] and p["artifact"] == artifact)
            pred = cost.predict(_part(point), artifact)
            want = max(pred.bytes * 1.25 / 5e7, pred.seconds * 1.25 / 30.0, pred.peak * 3.0 / 1e9)
            assert item["edge_ratio"] == want
        ratios = [item["edge_ratio"] for item in ranking]
        assert ratios == sorted(ratios, reverse=True)


def test_an_artifact_the_budget_leaves_unbounded_ranks_by_enveloped_build_seconds() -> None:
    envelope = _flat(0.5)
    budget: oper_sets.Budget = {"stl-preview": (None, None, None),
                                "stl-fine": (2.4e8, None, None), "step": (None, None, None)}
    points = [*_bolts([10.0, 40.0, 20.0]), *(_pt("n", "nut", {}, a) for a in ARTIFACTS3)]
    order = oper_sets.tier_order(points, envelope, budget)
    for artifact in ("stl-preview", "step"):
        ranking = order[artifact]["edge_ranking"]
        assert isinstance(ranking, list)
        by_label = {str(p["label"]): p for p in points if p["artifact"] == artifact}
        assert [item["edge_ratio"] for item in ranking] == [
            _env_seconds(by_label[str(item["label"])], artifact, envelope) for item in ranking]
        assert [item["label"] for item in ranking] == sorted(
            by_label, key=lambda label: -_env_seconds(by_label[label], artifact, envelope))


def test_a_tie_in_edge_ratio_goes_to_the_label_that_sorts_first() -> None:
    # head_chamfer is no feature of the model, so the two bolts predict alike
    points = [_pt("zz", "bolt", {"head_chamfer": 15.0}, a) for a in ARTIFACTS3] + [
        _pt("aa", "bolt", {"head_chamfer": 20.0}, a) for a in ARTIFACTS3]
    order = oper_sets.tier_order(points, _flat())
    for artifact in ARTIFACTS3:
        ranking = order[artifact]["edge_ranking"]
        assert isinstance(ranking, list)
        assert [item["label"] for item in ranking] == ["aa", "zz"]
        assert ranking[0]["edge_ratio"] == ranking[1]["edge_ratio"]


def test_the_draw_is_the_other_candidates_shuffled_by_a_new_generator_per_artifact() -> None:
    points = _bolts([4.0 + i for i in range(12)])
    order = oper_sets.tier_order(points, _flat())
    for artifact in ARTIFACTS3:
        entry = order[artifact]
        ranking = entry["edge_ranking"]
        assert isinstance(ranking, list)
        edge = {item["label"] for item in ranking[:3]}
        want = [f"b{i}" for i in range(12) if f"b{i}" not in edge]
        random.Random(20261026).shuffle(want)
        assert entry["draw"] == want
        assert entry["candidates"] == [f"b{i}" for i in range(12)]
    assert oper_sets.tier_order(points, _flat()) == order


def _bound_space() -> tuple[list[Raw], list[Raw], dict[tuple[str, str, str], float]]:
    """Six bolts, two nuts and twelve shorter filler bolts (so every slot holds a partner) at every
    artifact, no budget. The bolt seconds and the nut peak are enveloped 100 times, so the 5
    slowest are bolts and the largest peak prediction a nut."""
    points = [*_bolts([10.0, 20.0, 30.0, 40.0, 50.0, 60.0]),
              *(_pt(f"n{i}", "nut", {"m": m}, a) for i, m in enumerate((5.2, 8.0))
                for a in ARTIFACTS3),
              *_bolts([4.0 + i / 2 for i in range(12)], prefix="f")]
    envelope = _flat(0.0, bolt_seconds=100.0, nut_peak=100.0)
    return points, envelope_points_ok(points), envelope


def envelope_points_ok(points: list[Raw]) -> list[Raw]:
    """Readings: the slowest bolt has the largest cold wall, the shortest bolt the largest ok
    peak, and the second nut a larger peak that is not ok."""
    return _ok_readings(points, b5={"build_s": 50.0}, b0={"memory_peak_bytes": 10**9},
                        n1={"status": "capped", "memory_peak_bytes": 10**10})


def test_the_bound_set_is_the_top_five_the_measured_extrema_and_the_peak_prediction() -> None:
    points, readings, envelope = _bound_space()
    bound = oper_sets.bound_sets(points, readings, envelope, UNBOUNDED)
    for artifact in ARTIFACTS3:
        # n1 is capped at every artifact, so it is no candidate (G31), not even for the peak
        # prediction, which reads no reading
        here = [p for p in points if p["artifact"] == artifact and p["label"] != "n1"]
        slowest = sorted(here, key=lambda p: (-_env_seconds(p, artifact, envelope),
                                              str(p["label"])))[:5]
        peaks = {str(p["label"]): cost.predict(_part(p), artifact).peak * (
            1.0 + envelope[str(p["kind"]), artifact, "peak"]) for p in here}
        top_peak = min(peaks, key=lambda label: (-peaks[label], label))
        assert [str(p["label"]) for p in slowest] == ["b5", "b4", "b3", "b2", "b1"]
        assert top_peak == "n0"
        # b5 (worst measured wall) is in the top 5 already; b0 is the largest ok peak
        assert [c.label for c in bound[artifact]] == ["b5", "b4", "b3", "b2", "b1", "n0", "b0"]


def test_every_contention_partner_is_the_slowest_admitted_point_on_its_slot() -> None:
    points, readings, envelope = _bound_space()
    contention = oper_sets.bound_points(points, readings, envelope, UNBOUNDED)
    bound = oper_sets.bound_sets(points, readings, envelope, UNBOUNDED)
    assert len(contention) == 3 * sum(len(v) for v in bound.values())
    for reading in contention:
        artifact, workers = reading["artifact"], reading["workers"]
        assert artifact in ARTIFACTS3
        assert isinstance(workers, int)
        members = reading["points"]
        assert isinstance(members, list)
        here = {str(p["label"]): p for p in points if p["artifact"] == artifact}
        where = next(a for a in ARTIFACTS3 if a == artifact)
        assert sorted(m["slot"] for m in members) == list(range(workers))
        p_label = members[0]["label"]
        assert reading["label"] == f"{p_label}-n{workers}"
        for member in members:
            assert member["slot"] == hash(_part(here[member["label"]])) % workers
            assert set(member) == {"label", "kind", "params", "slot"}
        for member in members[1:]:
            rivals = [label for label, p in here.items() if label != p_label
                      and hash(_part(p)) % workers == member["slot"]]
            assert member["label"] == min(rivals, key=lambda label: (
                -_env_seconds(here[label], where, envelope), label))


def _members(contention: Iterable[Mapping[str, object]], artifact: str) -> set[str]:
    out: set[str] = set()
    for reading in contention:
        members = reading["points"]
        assert isinstance(members, list)
        if reading["artifact"] == artifact:
            out |= {str(m["label"]) for m in members}
    return out


def test_a_point_not_ok_at_another_artifact_is_neither_a_bound_point_nor_a_partner() -> None:
    """G31: two nuts the kernel refuses were admitted, entered the stl-preview set as P and as
    partners, and every reading that built them was refused. A candidate needs an ok explore
    reading at every artifact, not only the two measured picks at their own artifact."""
    points, readings, envelope = _bound_space()
    before = oper_sets.bound_points(points, readings, envelope, UNBOUNDED)
    assert "b4" in _members(before, "stl-preview")
    readings = [{**r, "status": "refused"} if (r["label"], r["artifact"]) == ("b4", "step")
                else r for r in readings]
    bound = oper_sets.bound_sets(points, readings, envelope, UNBOUNDED)
    contention = oper_sets.bound_points(points, readings, envelope, UNBOUNDED)
    for artifact in ARTIFACTS3:
        assert "b4" not in [c.label for c in bound[artifact]]
        assert [c.label for c in bound[artifact]][:5] == ["b5", "b3", "b2", "b1", "b0"]
    assert not any("b4" in _members(contention, artifact) for artifact in ARTIFACTS3)


def test_a_point_is_unread_when_no_reading_carries_its_identity_fields() -> None:
    """A contention point keeps its label when its partner changes, so the members decide; a gzip
    point's `preset` is not copied into its readings, so it does not."""
    member = {"label": "a", "kind": "bolt", "params": {}, "slot": 0}
    other = {"label": "b", "kind": "bolt", "params": {"length": 30.0}, "slot": 1}
    contention = {"label": "a-n2", "kind": "contention", "artifact": "stl-preview",
                  "workers": 2, "points": [member, other]}
    swapped = {**contention, "points": [member, {**other, "label": "c"}]}
    gzip = {"label": "g", "kind": "bolt", "params": {"d": 8.0}, "artifact": "stl-fine",
            "preset": "iso4017:M8x20", "gzip_levels": [1, 6, 9]}
    recorded = [{**contention, "params": {}, "rep": 1, "status": "ok"},
                {**{k: v for k, v in gzip.items() if k != "preset"}, "rep": 1, "status": "ok"}]
    assert oper_sets.unread([contention, swapped, gzip], recorded) == [swapped]
    assert oper_sets.unread([{**gzip, "gzip_levels": [1]}], recorded) == [
        {**gzip, "gzip_levels": [1]}]


def test_the_committed_reruns_are_the_stl_preview_points_the_two_refused_nuts_touched() -> None:
    """G31 on the record: the two kernel-refused nuts leave every bound and gzip point, and only
    stl-preview points are read again, 10 contention and 2 gzip."""
    nuts = {"nut-d30-p0.35-m0.8d-s4d-c0.15-right", "nut-d30-p0.35-m0.8d-s1.6d-c0.15-left"}
    sets = {name: json.loads((REPO_ROOT / "bench/points" / f"{name}.json").read_text())
            for name in ("bound", "gzip", "bound-rerun", "gzip-rerun")}
    for name in ("bound", "gzip"):
        labels = {str(p["label"]) for p in sets[name]["points"]} | {
            str(m["label"]) for p in sets[name]["points"] for m in p.get("points", [])}
        assert not labels & nuts, name
    rerun = sets["bound-rerun"]["points"]
    assert len(rerun) == 10
    assert {p["artifact"] for p in rerun} == {"stl-preview"}
    assert sets["bound-rerun"]["sources"] == [
        "explore=bench/results/phase-07/explore-40646117094",
        "run=bench/results/phase-07/bound-40907549180"]
    assert [(p["label"], p["artifact"]) for p in sets["gzip-rerun"]["points"]] == [
        ("iso4017:M16x150", "stl-preview"), ("iso4017:M20x160", "stl-preview")]
    assert all(p in sets["bound"]["points"] for p in rerun)
    assert all(p in sets["gzip"]["points"] for p in sets["gzip-rerun"]["points"])
    for name in ("bound-rerun", "gzip-rerun"):
        assert sets[name]["envelope"] == sets[name.removesuffix("-rerun")]["envelope"]
        assert sets[name]["shard_sizes"] == [len(sets[name]["points"])]


def _recorded(point: Mapping[str, object]) -> Raw:
    """An ok reading of a contention point as the harness records it: the point's fields, `params`
    empty."""
    return {**point, "type": "reading", "params": {}, "rep": 1, "status": "ok"}


def test_the_rerun_command_writes_the_unread_points_and_refuses_an_empty_rerun(
        runs2_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert _runs2(runs2_repo, "tier-order", "bound") == 0
    bound = json.loads((runs2_repo / "points" / "bound.json").read_text())
    read, unread_points = bound["points"][:-2], bound["points"][-2:]
    _write_records(runs2_repo / "b1", [_recorded(p) for p in read])
    out = runs2_repo / "points" / "bound-rerun.json"
    assert oper_sets.main(["rerun", "--set", "bound", "--explore", str(runs2_repo / "ex2"),
                           "--run", str(runs2_repo / "b1"), "--out", str(out)]) == 0
    doc = json.loads(out.read_text())
    assert doc["points"] == unread_points
    assert doc["sources"] == ["explore=ex2", "run=b1"]
    assert doc["rule"] == "07-SWEEP-PROTOCOL.md R14 (G4, G24, G31)"
    assert oper_sets.main(["--check"]) == 0, capsys.readouterr().err
    _write_records(runs2_repo / "b2", [_recorded(p) for p in bound["points"]])
    with pytest.raises(ValueError, match="read every point of the bound set"):
        oper_sets.build_rerun("bound-rerun", "ex2", "b2", oper_sets.shipped_envelope())


def test_a_slot_no_admitted_point_holds_stops_the_phase() -> None:
    lengths = [x / 2 for x in range(8, 200)]
    even = [length for length in lengths if hash(BoltParams(length=length)) % 2 == 0][:6]
    points = _bolts(even)
    with _stop("R14", "slot 1"):
        oper_sets.bound_points(points, _ok_readings(points), _flat(), UNBOUNDED)


def test_the_gzip_set_is_every_stl_bound_point_at_levels_1_6_and_9() -> None:
    points, readings, envelope = _bound_space()
    bound = oper_sets.bound_sets(points, readings, envelope, UNBOUNDED)
    gzip = oper_sets.gzip_points(bound)
    assert [(p["label"], p["artifact"]) for p in gzip] == [
        (c.label, artifact) for artifact in ("stl-preview", "stl-fine") for c in bound[artifact]]
    assert all(p["gzip_levels"] == [1, 6, 9] for p in gzip)


def test_the_arena_readings_are_z_of_a_with_the_trim_on_and_off() -> None:
    points, readings, envelope = _bound_space()
    bound = oper_sets.bound_sets(points, readings, envelope, UNBOUNDED)
    arenas = oper_sets.arena_points(bound, readings)
    # b0 has the largest ok explore peak of every bound set; n1's larger one is capped
    assert [(p["label"], p["artifact"], p["trim"]) for p in arenas] == [
        (f"arenas-b0-trim-{trim}", artifact, trim == "on")
        for artifact in ARTIFACTS3 for trim in ("on", "off")]
    assert all(p["part"] == {"kind": "bolt", "params": {"length": 10.0}} for p in arenas)
    tie = _ok_readings(points, b5={"memory_peak_bytes": 10**9}, b0={"memory_peak_bytes": 10**9})
    assert oper_sets.arena_points(bound, tie)[0]["label"] == "arenas-b0-trim-on"


def _tier(rankings: Mapping[str, tuple[list[str], list[str]]]) -> dict[str, object]:
    return {"artifacts": {a: {"edge_ranking": [{"label": label, "edge_ratio": 1.0}
                                               for label in ranking], "draw": draw}
                          for a, (ranking, draw) in rankings.items()}}


def test_the_load_mix_takes_edge_then_draw_parts_per_artifact_never_one_part_twice() -> None:
    points = _bolts([4.0 + i / 2 for i in range(80)], prefix="q")
    readings = _ok_readings(points)
    readings = [r if (r["label"], r["artifact"]) != ("q5", "stl-fine")
                else {**r, "status": "killed"} for r in readings]
    q = [f"q{i}" for i in range(80)]
    tier = _tier({"stl-fine": (q[0:4], q[3:30]),
                  "step": ([q[0], q[40], q[41], q[42], q[43]], q[0:70]),
                  "stl-preview": (q[50:55], q[0:80])})
    mix = oper_sets.load_mix(tier, points, readings)
    fine = [*q[0:3], *[label for label in q[3:30] if label != "q5"][:17]]  # q5 not ok there
    step = [*q[40:43], *[label for label in q[0:70] if label not in fine
                         and label not in q[40:43]][:17]]
    preview = [*q[50:53], *[label for label in q if label not in fine + step
                            and label not in q[50:53]][:17]]
    want = [{"label": label, "kind": "bolt", "params": {"length": 4.0 + int(label[1:]) / 2},
             "artifact": artifact}
            for artifact, labels in (("stl-fine", fine), ("step", step),
                                     ("stl-preview", preview)) for label in labels]
    random.Random(20261026).shuffle(want)
    assert mix == want
    assert len({json.dumps([m["kind"], m["params"]], sort_keys=True) for m in mix}) == 60

    load = oper_sets.load_points(tier, points, readings)
    assert [(p["label"], p["workers"], p["queue"], p["clients"], p["solid_cache"], p["bodies"])
            for p in load] == [("load-n1", 1, 2, 2, 4, True), ("load-n2", 2, 4, 4, 4, False),
                               ("load-n3", 3, 6, 6, 4, False)]
    assert all(p["mix"] == mix for p in load)


def test_a_list_that_cannot_supply_its_parts_stops_the_phase() -> None:
    points = _bolts([4.0 + i / 2 for i in range(30)], prefix="q")
    q = [f"q{i}" for i in range(30)]
    tier = _tier({"stl-fine": (q[0:3], q[3:19]), "step": (q[19:22], q[0:30]),
                  "stl-preview": (q[22:25], q)})
    with _stop("R15", "draw of stl-fine supplies 16"):
        oper_sets.load_mix(tier, points, _ok_readings(points))


@pytest.fixture
def runs2_repo(repo: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The repo fixture with a synthetic explore file of 80 bolts at every artifact and their ok
    records, and the code-written point files in place, so `--check` has something to pass."""
    points = _bolts([4.0 + i / 2 for i in range(80)], prefix="q")
    monkeypatch.setattr(oper_sets, "_explore_points", lambda: [dict(p) for p in points])
    readings = [{**r, "memory_peak_bytes": 10**8 + i, "build_s": 1.0 + i / 100}
                for i, r in enumerate(_ok_readings(points))]
    _write_records(repo / "ex2", readings)
    for name, text in oper_sets.generate().items():
        (repo / "points" / f"{name}.json").write_text(text)
    return repo


def _runs2(repo: Path, *sets: str) -> int:
    return oper_sets.main(["runs2", "--explore", str(repo / "ex2"), "--out-dir",
                           str(repo / "points"), "--tier-order",
                           str(repo / oper_sets.TIER_ORDER), "--sets", *sets])


def test_runs2_writes_d_of_a_and_the_sets_with_their_envelope_sources_and_shards(
        runs2_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert _runs2(runs2_repo, "tier-order") == 0
    assert oper_sets.main(["--check"]) == 0
    assert _runs2(runs2_repo, "bound", "load", "gzip", "arenas") == 0
    assert oper_sets.main(["--check"]) == 0, capsys.readouterr().err
    tier = json.loads((runs2_repo / oper_sets.TIER_ORDER).read_text())
    assert tier["sources"] == ["explore-points=bench/points/explore.json"]
    assert oper_sets.envelope_of(tier["envelope"]) == oper_sets.shipped_envelope()
    for name, sources in (("bound", ["explore=ex2"]),
                          ("load", [f"tier-order={oper_sets.TIER_ORDER}", "explore=ex2"]),
                          ("gzip", ["explore=ex2"]), ("arenas", ["explore=ex2"])):
        doc = json.loads((runs2_repo / "points" / f"{name}.json").read_text())
        assert (doc["reps"], doc["sources"]) == (5, sources)
        assert oper_sets.envelope_of(doc["envelope"]) == oper_sets.shipped_envelope()
        # every reading is charged R2's 600 s: 17 fit under half the 350-minute job
        assert doc["shard_sizes"] == oper_sets.shard_sizes([600.0] * len(doc["points"]), 10500.0)
        assert max(doc["shard_sizes"]) <= 17
        spec = oper.load_set(name, runs2_repo / "points")
        assert spec.reps == 5
    text = (runs2_repo / "points" / "bound.json").read_text()
    assert oper_sets._regenerate_runs2("bound", text) == text


def test_check_fails_when_a_recorded_e_exceeds_the_shipped_one(
        runs2_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert _runs2(runs2_repo, "tier-order", "bound") == 0
    path = runs2_repo / "points" / "bound.json"
    doc = json.loads(path.read_text())
    doc["envelope"]["bolt"]["step"]["seconds"] += 1.0
    path.write_text(json.dumps(doc, indent=1) + "\n")
    capsys.readouterr()
    assert oper_sets.main(["--check"]) == 1
    assert "bound.json cannot be written again" in capsys.readouterr().err
    failure = oper_sets._check_runs2()
    assert failure is not None
    assert "exceeds the shipped one" in failure


def test_a_widening_after_the_draw_redraws_nothing(
        runs2_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert _runs2(runs2_repo, "tier-order", *oper_sets.RUNS2_SETS) == 0
    files = {path: path.read_text() for path in
             [runs2_repo / oper_sets.TIER_ORDER,
              *(runs2_repo / "points" / f"{n}.json" for n in oper_sets.RUNS2_SETS)]}
    widened = {key: e + 1.0 for key, e in cost.ENVELOPE.items()}
    monkeypatch.setattr(cost, "ENVELOPE", widened)
    assert oper_sets.main(["--check"]) == 0
    for path, text in files.items():
        name = "tier-order" if path.name == "tier-order.json" else path.stem
        assert oper_sets._regenerate_runs2(name, text) == text


# --- the out-of-band points (07-15, R11's G28 and G29) -------------------------------------------

# The nearest-the-budget rows as generated at the committed constants, by (kind, field, side,
# artifact); the first-in-file rows are the M2 rows everywhere.
NEAREST = {
    ("bolt", "k", "below"): ("iso4017:M20x160", "iso4017:M20x100", "iso4017:M20x150"),
    ("bolt", "k", "above"): ("iso4017:M18x180", "iso4017:M18x150", "iso4017:M16x130"),
    ("bolt", "s", "below"): ("iso4017:M20x200", "iso4017:M20x200", "iso4017:M16x160"),
    ("bolt", "s", "above"): ("iso4017:M4x25", "iso4017:M10x50", "iso4017:M18x120"),
    ("nut", "s", "below"): ("iso4032:M20", "iso4032:M20", "iso4032:M16"),
    ("nut", "s", "above"): ("iso4032:M20", "iso4032:M20", "iso4032:M16"),
    ("nut", "m", "below"): ("iso4032:M20", "iso4032:M20", "iso4032:M16"),
    ("nut", "m", "above"): ("iso4032:M20", "iso4032:M20", "iso4032:M16"),
}
TURNS_NEAREST = ("iso4017:M20x40", "iso4014:M20x200", "iso4017:M20x40")


def _committed_outband() -> tuple[dict[str, object], dict[tuple[str, str, str], float]]:
    doc = json.loads((REPO_ROOT / "bench/points/outband.json").read_text())
    return doc, oper_sets.envelope_of(doc["envelope"])


def test_a_value_below_or_above_a_band_is_the_first_on_its_step_past_the_edge() -> None:
    step = oper_sets._form_step("bolt", "k")
    assert step == Decimal("0.1")
    assert oper_sets._form_step("bolt", "thread_length") == Decimal("0.5")
    assert oper_sets._largest_below(0.6, 2.0, step) == 1.1  # 1.2 / 2 is the edge itself
    assert oper_sets._largest_below(0.6, 2.1, step) == 1.2  # 1.26: 1.2 / 2.1 is below 0.6
    assert oper_sets._largest_below(0.6, 0.1, step) is None  # no positive value is below 0.06
    assert oper_sets._smallest_above(0.7, 2.0, step) == 1.5  # 1.4 / 2 is the edge itself
    assert oper_sets._smallest_above(2.0, 4.0, step) == 8.1


def test_g28_reads_each_ratio_below_and_above_its_band_with_admitted_catalogue_rows() -> None:
    _, envelope = _committed_outband()
    points, absent = oper_sets.head_ratio_points(envelope)
    seen: dict[tuple[str, str, str, str], list[str]] = {}
    for point in points:
        label, artifact = str(point["label"]), point["artifact"]
        assert artifact in ARTIFACTS3
        where = next(a for a in ARTIFACTS3 if a == artifact)
        _, kind, field, side, row = label.split("-", 4)
        part = _part(point)
        low, high = cost.BANDS[kind, field]
        ratio = float(getattr(part, field)) / part.d
        assert oper_sets.admits(part, where, envelope, cost.BUDGET)
        step = 0.1
        if side == "below":
            assert ratio < low
            assert (float(getattr(part, field)) + step) / part.d >= low - 1e-12
        elif side == "above":
            assert ratio > high
            assert (float(getattr(part, field)) - step) / part.d <= high + 1e-12
        else:
            assert ratio >= 10 * high
        # only the one field leaves the catalogue row
        fields = (expand(row) if kind == "bolt" else expand_nut(row)) or {}
        params = point["params"]
        assert isinstance(params, dict)
        assert {k: v for k, v in params.items() if fields.get(k) != v} == {
            field: getattr(part, field)}
        seen.setdefault((kind, field, side, where), []).append(row)
    for (kind, field), _band in cost.BANDS.items():
        first = "iso4017:M2x4" if kind == "bolt" else "iso4032:M2"
        for side in ("below", "above"):
            for artifact, nearest in zip(ARTIFACTS3, NEAREST[kind, field, side], strict=True):
                assert seen[kind, field, side, artifact] == [nearest, first]
    assert {(kind, field) for kind, field, side, _ in seen if side == "far"} == {
        ("bolt", "k"), ("nut", "s")}
    assert all(rows == ["iso4017:M2x4"] or rows == ["iso4032:M2"]
               for (_, _, side, _), rows in seen.items() if side == "far")
    assert sorted(absent) == sorted(f"{kind} {field}/d far above its band at {a}"
                                    for kind, field in (("bolt", "s"), ("nut", "m"))
                                    for a in ARTIFACTS3)


def test_g29_reads_bolts_whose_built_thread_is_below_the_fewest_fitted_turns() -> None:
    _, envelope = _committed_outband()
    points = oper_sets.turns_points(envelope)
    assert [(p["artifact"], p["label"]) for p in points] == [
        (artifact, f"turns-below-{row}") for artifact, nearest in zip(
            ARTIFACTS3, TURNS_NEAREST, strict=True) for row in (nearest, "iso4017:M2x4")]
    for point in points:
        part = _part(point)
        assert isinstance(part, BoltParams)
        turns = built_thread_length(part.thread_length, part.length) / part.pitch
        assert turns < cost.MIN_FITTED_TURNS
        more = built_thread_length(part.thread_length + 0.5, part.length) / part.pitch
        assert more >= cost.MIN_FITTED_TURNS
        where = next(a for a in ARTIFACTS3 if a == point["artifact"])
        assert oper_sets.admits(part, where, envelope, cost.BUDGET)


def test_a_side_or_an_artifact_no_catalogue_row_supplies_stops_at_r11() -> None:
    nothing = _flat(1e6)
    with _stop("R11", "G28"):
        oper_sets.head_ratio_points(nothing)
    with _stop("R11", "G29"):
        oper_sets.turns_points(nothing)


def test_the_committed_outband_set_is_charged_as_explore_like_parts() -> None:
    doc, _ = _committed_outband()
    points = doc["points"]
    assert isinstance(points, list)
    assert doc["reps"] == 5
    assert doc["sources"] == ["explore=bench/results/phase-07/explore-40646117094"]
    table = oper_sets.charge_table(oper_sets.read_readings(
        REPO_ROOT / "bench/results/phase-07/explore-40646117094"))
    assert doc["shard_sizes"] == oper_sets.shard_sizes(
        oper_sets.charges(points, table, 600.0), oper_sets.HALF_JOB_S)


# --- the load table (07-15 Task 2) ----------------------------------------------------------------


def _load_reading(rep: int, status: str = "ok", workers: int = 1, few: bool = False) -> Raw:
    reading: Raw = {"type": "reading", "label": f"load-n{workers}", "kind": "load", "params": {},
                    "artifact": "load", "rep": rep, "workers": workers, "status": status}
    if status != "ok":
        return {**reading, "requests": []}
    per = {"samples": 20, "p95_s": 2.0 + rep}
    return {**reading, "time_to_healthy_s": 1.25, "idle_peak_bytes": 6 * 10**7,
            "memory_peak_bytes": 9 * 10**8 + rep,
            "latency": {"all": {"samples": 60, "p95_s": 10.0 + rep}, "stl-fine": per,
                        "step": {"samples": 19, "p95_s": None} if few else per,
                        "stl-preview": per},
            "health_latency": {"samples": 300, "p95_s": 0.0125}}


def test_the_load_table_prints_each_repetitions_figures_and_none_for_a_failed_one() -> None:
    readings = [*(_load_reading(rep) for rep in (1, 2, 3, 4)), _load_reading(5, "killed"),
                *(_load_reading(rep, workers=2, few=rep == 3) for rep in (1, 2, 3, 4, 5))]
    rows = oper_sets.load_table(readings).splitlines()
    assert rows[0].startswith("| point | N | rep | status | p95 all s | p95 stl-fine s | "
                              "p95 step s | p95 stl-preview s | idle peak bytes |")
    assert rows[2] == ("| load-n1 | 1 | 1 | ok | 11.000 | 3.000 | 3.000 | 3.000 | 60000000 | "
                       "900000001 | 1.250 | 0.013 |")
    assert rows[6] == "| load-n1 | 1 | 5 | killed |" + "  |" * 8
    assert "fewer than 20 samples (19)" in rows[9]
    assert len(rows) == 12


def test_a_load_point_without_repetitions_one_to_five_is_incomplete_and_has_no_figure() -> None:
    readings = [_load_reading(rep) for rep in (1, 2, 2, 4, 5)]
    rows = oper_sets.load_table(readings).splitlines()[2:]
    assert len(rows) == 5
    assert all("incomplete (reps ['1', '2', '2', '4', '5'])" in row for row in rows)
    assert not any("11.000" in row or "900000001" in row for row in rows)


def test_the_load_table_command_reads_a_downloaded_run(
        repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_records(repo / "load", [_load_reading(rep) for rep in (1, 2, 3, 4, 5)])
    assert oper_sets.main(["load-table", "--from", str(repo / "load")]) == 0
    assert "| load-n1 | 1 | 5 | ok | 15.000 |" in capsys.readouterr().out


# --- the envelope check (07-15 Task 3; R12, G5, G21, G28) -----------------------------------------

FIT = REPO_ROOT / "bench/results/phase-07/fit.json"
M20 = {"d": 20.0, "pitch": 2.5, "length": 60.0, "thread_length": 60.0, "s": 30.0, "k": 12.5}


def _actuals(kind: str, params: Mapping[str, object], artifact: cost.Artifact,
             times: float = 1.0) -> dict[str, float]:
    pred = cost.predict(KINDS[kind].model_validate(dict(params)), artifact)
    return {"bytes": pred.bytes, "build_s": pred.seconds * times, "export_s": 0.0,
            "memory_peak_bytes": pred.peak}


def _contention(workers: int, times: float) -> Raw:
    members = [{"label": "m20", "kind": "bolt", "params": dict(M20), "slot": 0}] + [
        {"label": f"p{i}", "kind": "nut", "params": {}, "slot": i} for i in range(1, workers)]
    return {"type": "reading", "label": f"m20-n{workers}", "kind": "contention",
            "artifact": "stl-fine", "rep": 1, "status": "ok", "workers": workers,
            "points": members, **_actuals("bolt", M20, "stl-fine", times)}


def _e(rows: list[oper_sets.Widening], kind: str, artifact: str, target: str
       ) -> oper_sets.Widening:
    return next(r for r in rows if (r.kind, r.artifact, r.target) == (kind, artifact, target))


def test_a_contended_or_load_wall_widens_nothing_and_the_same_part_alone_does() -> None:
    fit = json.loads(FIT.read_text())
    e = cost.ENVELOPE["bolt", "stl-fine", "seconds"]
    times = 3.0 * (1.0 + e)  # three times the enveloped prediction
    load: Raw = {"type": "reading", "label": "load-n1", "kind": "load", "artifact": "load",
                 "rep": 1, "status": "ok", "workers": 1}
    rows = oper_sets.envelope_check(fit, [("9", _contention(2, times)), ("9", load)])
    assert all(r.widened is None for r in rows)
    rows = oper_sets.envelope_check(fit, [("9", _contention(1, times))])
    row = _e(rows, "bolt", "stl-fine", "seconds")
    assert row.ratio == pytest.approx(3.0)
    assert row.widened is not None
    assert row.widened >= 3.0 * (1.0 + e) - 1.0
    assert row.worst == "9:m20-n1 rep 1"
    # the factor covers the reading in the arithmetic admission uses
    pred = cost.predict(BoltParams.model_validate(M20), "stl-fine").seconds
    assert pred * (1.0 + row.widened) >= pred * times
    others = [r for r in rows if (r.kind, r.artifact, r.target) != ("bolt", "stl-fine", "seconds")]
    assert all(r.widened is None for r in others)


def test_a_widening_never_lowers_an_e_and_a_model_without_readings_keeps_its_e() -> None:
    fit = json.loads(FIT.read_text())
    part: Raw = {"type": "reading", "label": "m20", "kind": "bolt", "params": dict(M20),
                 "artifact": "step", "rep": 1, "status": "ok",
                 **_actuals("bolt", M20, "step", 0.5)}
    arena: Raw = {"type": "reading", "label": "a", "kind": "arenas", "artifact": "step",
                  "rep": 1, "status": "ok", "part": {"kind": "bolt", "params": dict(M20)},
                  **_actuals("bolt", M20, "step", 0.5)}
    rows = oper_sets.envelope_check(fit, [("9", part), ("9", arena)])
    assert all(r.widened is None for r in rows)
    assert _e(rows, "bolt", "step", "seconds").ratio < 1.0
    assert _e(rows, "nut", "step", "seconds").worst == ""
    assert [r.e for r in rows] == [m["envelope"] for m in fit["models"]]


def _fit_repo(tmp_path: Path, sets: Mapping[str, list[Raw]]) -> Path:
    fit = tmp_path / "fit.json"
    fit.write_text(FIT.read_text())
    for name, readings in sets.items():
        folder = tmp_path / name / f"oper-{name}-1-1"
        folder.mkdir(parents=True)
        lines = [json.dumps({"type": "header", "GITHUB_RUN_ID": f"77{len(name)}"}),
                 *(json.dumps(r) for r in readings)]
        (folder / f"oper-{name}-1-1.jsonl").write_text("\n".join(lines) + "\n")
    return fit


def test_the_command_writes_only_the_widened_envelopes_and_the_widening_runs(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # the default nut binds no C1 component (the bolt rows set every one), so widening its
    # stl-fine seconds by half refuses nothing B-01 keeps
    e = cost.ENVELOPE["nut", "stl-fine", "seconds"]
    alone = {**_contention(1, 1.0), "label": "nut-n1",
             "points": [{"label": "nut", "kind": "nut", "params": {}, "slot": 0}],
             **_actuals("nut", {}, "stl-fine", 1.5 * (1.0 + e))}
    eb = cost.ENVELOPE["bolt", "stl-fine", "seconds"]
    outband: Raw = {"type": "reading", "label": "outband-x", "kind": "bolt", "params": dict(M20),
                    "artifact": "stl-fine", "rep": 1, "status": "ok",
                    **_actuals("bolt", M20, "stl-fine", 9.0 * (1.0 + eb))}
    fit = _fit_repo(tmp_path, {"bound": [alone], "outband": [outband]})
    old = json.loads(fit.read_text())
    assert oper_sets.main(["envelope-check", "--fit", str(fit), "--from",
                           str(tmp_path / "bound"), str(tmp_path / "outband")]) == 0
    assert "widened 1 envelopes by runs 775" in capsys.readouterr().out
    after = json.loads(fit.read_text())
    # the runs that widened the committed fit.json stay named, and the new one joins them
    assert after["widened_by"] == sorted({*old.get("widened_by", []), "775"})
    assert old.keys() <= after.keys()
    assert after.keys() - old.keys() <= {"widened_by"}
    key = ("nut", "stl-fine", "seconds")
    changed = [(a["kind"], a["artifact"], a["target"]) for a, b in
               zip(after["models"], old["models"], strict=True) if a != b]
    assert changed == [key]
    model = next(m for m in after["models"] if (m["kind"], m["artifact"], m["target"]) == key)
    was = next(m for m in old["models"] if (m["kind"], m["artifact"], m["target"]) == key)
    # the bolt's out-of-band 9x widens nothing (G30): the nut's N = 1 reading's 1.5x set it
    assert model["envelope"] == pytest.approx(1.5 * (1.0 + e) - 1.0)
    assert {k: v for k, v in model.items() if k != "envelope"} == {
        k: v for k, v in was.items() if k != "envelope"}
    assert all(a == b for a, b in zip(after["excluded"], old["excluded"], strict=True))


def test_an_out_of_band_nut_reading_widens_e_and_a_bolt_or_load_reading_does_not() -> None:
    """G30: after the out-of-band stop, a nut reading of R11's out-of-band points widens e as a
    cold isolated reading does; a bolt's never does, nor any load reading."""
    nut: Raw = {"type": "reading", "label": "outband-nut", "kind": "nut", "params": {},
                "artifact": "stl-fine", "rep": 1, "status": "ok"}
    bolt: Raw = {**nut, "label": "outband-bolt", "kind": "bolt"}
    assert oper_sets.widens("outband", nut)
    assert not oper_sets.widens("outband", bolt)
    assert not oper_sets.widens("load", {**nut, "kind": "load"})
    assert all(oper_sets.widens(name, bolt) for name in ("bound", "gzip", "arenas", "bound-rerun",
                                                         "gzip-rerun"))


def test_the_shipped_envelope_covers_every_runs_ii_reading_that_may_widen_it() -> None:
    """07-15 Task 3 on the record: over every Runs II directory, the readings that may widen e
    (G5, G21, G30) are all within the shipped envelope, and G30's two nut models are the ones
    outband run 40909768713 widened, its worst readings now at their enveloped prediction."""
    fit = json.loads(FIT.read_text())
    assert fit["widened_by"] == ["40909768713"]
    directories = sorted(path for path in (REPO_ROOT / "bench/results/phase-07").iterdir()
                         if path.name.split("-")[0] in {"bound", "load", "gzip", "arenas",
                                                        "outband"})
    assert len(directories) == 7
    kept = [(run, reading) for name, run, reading in oper_sets.runs_readings(directories)
            if oper_sets.widens(name, reading)]
    rows = oper_sets.envelope_check(fit, kept)
    assert [r for r in rows if r.widened is not None] == []
    for target in ("seconds", "peak"):
        row = _e(rows, "nut", "stl-fine", target)
        assert row.worst.startswith("40909768713:outband-nut-s-below-iso4032:M2 rep 3")
        assert 1.0 - 1e-12 < row.ratio <= 1.0
    assert [m["envelope"] for m in fit["models"]] == [
        cost.ENVELOPE[m["kind"], m["artifact"], m["target"]] for m in fit["models"]]
    assert oper_sets._admits_all(oper_sets.shipped_envelope()) == []


def test_a_widening_that_would_refuse_a_part_b01_keeps_stops_and_writes_nothing(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    default: Raw = {"type": "reading", "label": "default-bolt", "kind": "bolt", "params": {},
                    "artifact": "stl-preview", "rep": 1, "status": "ok",
                    **_actuals("bolt", {}, "stl-preview", 10**4)}
    fit = _fit_repo(tmp_path, {"gzip": [default]})
    before = fit.read_text()
    assert oper_sets.main(["envelope-check", "--fit", str(fit), "--from",
                           str(tmp_path / "gzip")]) == 3
    assert "oper_sets: stop (R12): the widened envelope refuses" in capsys.readouterr().err
    assert fit.read_text() == before


# --- the runtime values (07-16; R14 to R26) -----------------------------------------------------

GIB = 2**30
QUARTER = 256 * 2**20  # R16's rounding step


def _bolt_part(length: float) -> Raw:
    return {"label": f"bolt-{length:g}", "kind": "bolt", "params": {"length": length}}


def _contended(p: str, artifact: str, workers: int, walls: Iterable[float] = (1.0,) * 5,
                peaks: Iterable[int] = (100,) * 5, statuses: Iterable[str] = ("ok",) * 5,
                reps: Iterable[int] = REPS) -> tuple[Raw, list[Raw]]:
    """A contention point P at N and its readings: rep i reads `walls[i]` s and `peaks[i]` B."""
    members = [{**_bolt_part(float(len(p))), "label": p, "slot": 0}]
    point: Raw = {"label": f"{p}-n{workers}", "kind": "contention", "artifact": artifact,
                  "workers": workers, "points": members}
    readings: list[Raw] = [{**point, "type": "reading", "params": {}, "rep": rep, "status": s,
                            "build_s": wall - 0.25, "export_s": 0.25, "memory_peak_bytes": peak}
                           for rep, wall, peak, s in zip(reps, walls, peaks, statuses,
                                                         strict=False)]
    return point, readings


def _read(point: Mapping[str, object], readings: Iterable[Mapping[str, object]],
          run: str = "7") -> oper_sets.Read:
    return oper_sets.Read(point, run, tuple(readings))


def _load_point(workers: int) -> Raw:
    return {"label": f"load-n{workers}", "kind": "load", "workers": workers,
            "queue": 2 * workers, "clients": 2 * workers, "solid_cache": 4,
            "bodies": workers == 1, "mix": []}


def _request(index: int, artifact: str, wall: float) -> Raw:
    return {"index": index, "artifact": artifact, "start_s": 10.0, "end_s": 10.0 + wall,
            "status_code": 200}


def _served(workers: int, rep: int, status: str = "ok", p95: float = 10.0,
                  peak: int = GIB, idle: int = 50 * 2**20, health: tuple[float, int] = (0.01, 25),
                  **over: object) -> Raw:
    reading: Raw = {**_load_point(workers), "type": "reading", "rep": rep, "status": status,
                    "idle_peak_bytes": idle, "memory_peak_bytes": peak,
                    "latency": {"all": {"samples": 60, "p95_s": p95}},
                    "requests": [_request(i, a, 1.0) for i, a in enumerate(ARTIFACTS3)],
                    "pool_calls": [{"slot": 0, "artifact": "stl-fine", "pending": [],
                                    "submit_s": 0.0, "end_s": 1.0, "outcome": "ok"}],
                    "health_latency": {"samples": health[1], "p95_s": health[0]},
                    "healthcheck": [{"offset_s": 0.0, "wall_s": 0.2, "exit_code": 0}],
                    "time_to_healthy_s": 0.5}
    reading.update(over)
    return reading


def _load(workers: int, status: str = "ok", p95: float = 10.0, peak: int = GIB,
          health: tuple[float, int] = (0.01, 25), **over: object) -> oper_sets.Read:
    return _read(_load_point(workers), [{**_served(workers, rep, status, p95, peak,
                                                   health=health), **over} for rep in REPS])


def _workers(read: oper_sets.Read, w: int = GIB, nproc: int = 4,
             mem_total: int = 16 * GIB) -> oper_sets.Workers:
    return oper_sets.per_workers(read, w, 0, 0, QUARTER, nproc, mem_total)


def _gzip_point(label: str, artifact: str = "stl-preview") -> Raw:
    return {**_bolt_part(4.0), "label": label, "artifact": artifact, "gzip_levels": [1, 6, 9]}


def _gzip_reading(point: Raw, rep: int, levels: Mapping[int, tuple[int, float]]) -> Raw:
    return {**point, "type": "reading", "rep": rep, "status": "ok",
            "gzip": [{"level": level, "bytes": b, "seconds": s}
                     for level, (b, s) in levels.items()]}


def _gzip(label: str, by_rep: Mapping[int, Mapping[int, tuple[int, float]]]) -> oper_sets.Read:
    point = _gzip_point(label)
    return _read(point, [_gzip_reading(point, rep, levels) for rep, levels in by_rep.items()])


def _same(levels: Mapping[int, tuple[int, float]]) -> dict[int, Mapping[int, tuple[int, float]]]:
    return dict.fromkeys(REPS, levels)


def test_a_value_rounds_up_to_the_256_mib_step_and_one_byte_over_a_gib_is_1_25_gib() -> None:
    assert oper_sets._round_up(GIB, QUARTER) == GIB
    assert oper_sets._round_up(GIB + 1, QUARTER) == 5 * QUARTER
    assert oper_sets._round_up(239508059.14804876, QUARTER) == QUARTER


def test_mem_limit_is_the_larger_of_the_sum_and_the_load_peak_rounded_up() -> None:
    read = _load(1, peak=GIB)
    row = oper_sets.per_workers(read, GIB + 1, 0, 0, 0, 4, 16 * GIB)  # the sum, 1 B over a GiB
    assert row.mem_limit_bytes == 5 * QUARTER
    assert row.qualifies
    row = oper_sets.per_workers(_load(2, peak=3 * GIB + 1), 10, 10, 10, QUARTER, 4, 16 * GIB)
    assert row.mem_limit_bytes == 13 * QUARTER  # the load peak, above W x N + B + cache + tmpfs
    row = oper_sets.per_workers(_load(3, peak=1), 100, 7, 11, QUARTER, 4, 16 * GIB)
    assert row.mem_limit_bytes == 2 * QUARTER  # 300 + 7 + 11 B over 256 MiB rounds up a step


@pytest.mark.parametrize("status", ["killed", "capped", "crashed"])
def test_an_n_with_one_load_repetition_not_ok_does_not_qualify(status: str) -> None:
    read = _load(1)
    readings = list(read.readings)
    readings[2] = {**readings[2], "status": status}
    row = _workers(_read(read.point, readings))
    assert not row.qualifies
    assert row.mem_limit_bytes is None
    assert "not 5 ok" in row.why_not[0]


def test_an_n_with_four_load_repetitions_does_not_qualify() -> None:
    read = _load(1)
    assert not _workers(_read(read.point, read.readings[:4])).qualifies


def test_n_must_be_at_most_nproc_minus_one() -> None:
    assert _workers(_load(3), nproc=4).qualifies
    row = _workers(_load(3), nproc=3)
    assert not row.qualifies
    assert row.why_not == ("N = 3 is above nproc - 1 = 2",)


def test_mem_limit_must_be_under_the_smallest_mem_total_and_under_16e9() -> None:
    row = _workers(_load(1, peak=4 * GIB), w=0)
    assert row.mem_limit_bytes == 4 * GIB
    assert row.qualifies
    assert not _workers(_load(1, peak=4 * GIB), w=0, mem_total=4 * GIB).qualifies
    assert _workers(_load(1, peak=4 * GIB), w=0, mem_total=4 * GIB + 1).qualifies
    row = _workers(_load(1, peak=16 * 10**9 - 1), w=0, mem_total=20 * 10**9)
    assert row.mem_limit_bytes is not None
    assert row.mem_limit_bytes >= 16 * 10**9
    assert not row.qualifies


def test_the_p95_of_an_n_is_the_max_over_its_five_repetitions() -> None:
    read = _load(2)
    readings = [{**r, "latency": {"all": {"samples": 60, "p95_s": 5.0 + int(str(r["rep"]))}}}
                for r in read.readings]
    row = _workers(_read(read.point, readings))
    assert row.p95_s == 10.0
    assert row.p95_reading == "7:load-n2 rep 5"


def test_the_bound_point_is_the_p_with_the_largest_max_cold_wall_at_the_picked_n() -> None:
    a = _contended("pa", "stl-fine", 2, walls=(10.0, 30.2, 11.0, 12.0, 9.0))
    b = _contended("pb", "stl-fine", 2, walls=(29.0,) * 5)
    c = _contended("pc", "stl-fine", 1, walls=(90.0,) * 5)  # another N decides nothing
    others = [_contended(f"p{x}", art, 2) for x, art in (("d", "stl-preview"), ("e", "step"))]
    reads = [_read(*x) for x in (a, b, c, *others)]
    found = oper_sets.timeouts(reads, 2)
    assert found["stl-fine"] == {"seconds": 61, "max_cold_wall_s": 30.2, "bound_point": "pa-n2",
                                 "reading": "7:pa-n2 rep 2"}
    assert found["stl-preview"]["seconds"] == 2
    assert found["step"]["seconds"] == 2


def test_a_tie_between_bound_points_goes_to_the_label_that_sorts_first() -> None:
    reads = [_read(*_contended(p, a, 1, walls=(4.0,) * 5)) for p in ("zz", "aa")
             for a in ARTIFACTS3]
    assert {row["bound_point"] for row in oper_sets.timeouts(reads, 1).values()} == {"aa-n1"}


def test_a_bound_point_at_the_picked_n_with_four_repetitions_stops_at_r14() -> None:
    point, readings = _contended("pa", "stl-fine", 1)
    reads = [_read(point, readings[:4]), *(_read(*_contended("p", a, 1)) for a in
                                           ("stl-preview", "step"))]
    with _stop("R14", "pa-n1 at stl-fine has no max"):
        oper_sets.timeouts(reads, 1)


def test_w_is_the_max_n1_container_peak_over_every_bound_point_and_ignores_other_ns() -> None:
    reads = [_read(*_contended("slow", "stl-fine", 1, peaks=(5, 6, 7, 8, 9))),
             _read(*_contended("heavy", "step", 1, peaks=(1, 2, 300, 4, 5))),
             _read(*_contended("heavy", "step", 3, peaks=(10**9,) * 5))]
    assert oper_sets._w(reads) == (300, "7:heavy-n1 rep 3")


@pytest.mark.parametrize("status", ["capped", "killed", "no_cgroup"])
def test_an_n1_contention_reading_that_is_not_ok_leaves_w_no_number(status: str) -> None:
    statuses = ("ok", status, "ok", "ok", "ok")
    reads = [_read(*_contended("heavy", "step", 1, statuses=statuses))]
    with _stop("R16", "heavy-n1 at step has no max"):
        oper_sets._w(reads)


def test_a_point_read_in_two_runs_or_in_none_is_a_stop() -> None:
    point, readings = _contended("pa", "step", 1)
    tagged = [("bound", "1", r) for r in readings[:3]] + [("bound-rerun", "2", r)
                                                         for r in readings[3:]]
    with _stop("R14", r"pa-n1 at step is read in 2 runs \(1, 2\), not in exactly one"):
        oper_sets.matched([point], tagged, oper_sets.BOUND_SETS, oper_sets._IDENTITY, "R14")
    with _stop("R14", "read in 0 runs"):
        oper_sets.matched([point], [], oper_sets.BOUND_SETS, oper_sets._IDENTITY, "R14")


def test_a_contention_point_is_matched_by_its_members_and_not_by_its_label() -> None:
    point, readings = _contended("pa", "step", 2)
    members = point["points"]
    assert isinstance(members, list)
    old_members = [*members, {"label": "nut", "kind": "nut", "params": {}, "slot": 1}]
    stale = [{**r, "points": old_members, "status": "refused"} for r in readings]
    tagged = [("bound", "1", r) for r in stale] + [("bound-rerun", "2", r) for r in readings]
    found = oper_sets.matched([point], tagged, oper_sets.BOUND_SETS, oper_sets._IDENTITY, "R14")
    assert found[0].run == "2"
    assert found[0].ok


def test_disagreeing_nproc_across_the_runner_headers_is_a_stop() -> None:
    with _stop("R16", "nproc"):
        oper_sets._runner([{"nproc": 4, "mem_total_bytes": 1}, {"nproc": 2, "mem_total_bytes": 1}])
    assert oper_sets._runner([{"nproc": 4, "mem_total_bytes": 9},
                              {"nproc": 4, "mem_total_bytes": 7}]) == (4, 7)


def test_the_tmpfs_must_fit_inside_mem_limit() -> None:
    oper_sets.tmpfs_inside(QUARTER, QUARTER, 1)
    with _stop("R26", "larger than mem_limit"):
        oper_sets.tmpfs_inside(2 * QUARTER, QUARTER, 2)


def test_the_tmpfs_per_worker_is_the_stl_fine_bytes_budget() -> None:
    assert oper_sets.tmpfs_base([]) == (cost.BUDGET["stl-fine"][0],
                                        "the stl-fine bytes budget (B-01)")


def test_r17_keeps_a_queue_of_2n_when_every_call_fits_its_queue_aware_deadline() -> None:
    limits = {"stl-preview": 10, "stl-fine": 30, "step": 10}
    # queued behind a fine STL and a preview: its deadline is 10 + 30 + 10 = 50 s
    call = {"slot": 0, "artifact": "step", "pending": ["stl-fine", "stl-preview"],
            "submit_s": 0.0, "end_s": 50.0, "outcome": "ok"}
    reads = [_load(2, pool_calls=[call])]
    found = oper_sets.queue_depth(reads, limits, 2 * GIB, 2)
    assert found["depth"] == 4
    assert found["largest_wall_over_deadline"] == 1.0


def test_r17_takes_a_queue_of_n_when_one_call_overruns_its_deadline() -> None:
    limits = {"stl-preview": 10, "stl-fine": 30, "step": 10}
    call = {"slot": 0, "artifact": "step", "pending": ["stl-fine"], "submit_s": 0.0,
            "end_s": 40.5, "outcome": "ok"}
    found = oper_sets.queue_depth([_load(2, pool_calls=[call])], limits, 2 * GIB, 2)
    assert found["depth"] == 2
    assert found["reading"] == "7:load-n2 rep 1 pool call 0"


def test_r17_takes_a_queue_of_n_when_an_end_peak_is_above_mem_limit() -> None:
    limits = {str(a): 100 for a in ARTIFACTS3}
    assert oper_sets.queue_depth([_load(3, peak=GIB + 1)], limits, GIB, 3)["depth"] == 3
    assert oper_sets.queue_depth([_load(3, peak=GIB)], limits, GIB, 3)["depth"] == 6


def test_retry_after_is_the_median_of_the_pooled_request_walls_per_artifact() -> None:
    readings = [_served(1, rep, requests=[_request(i, a, float(rep * 10 + i))
                                                for i in range(20) for a in ARTIFACTS3])
                for rep in REPS]
    found = oper_sets.retry_after([_read(_load_point(1), readings)])
    walls = sorted(float(rep * 10 + i) for rep in REPS for i in range(20))
    assert found["step"] == {"median_s": (walls[49] + walls[50]) / 2, "samples": 100}


def test_minimum_size_is_the_smallest_length_above_the_largest_body_that_does_not_shrink() -> None:
    def body(size: int, level1: int) -> Raw:
        return {"path": f"/b{size}", "status_code": 200, "bytes": size,
                "gzip": {"1": level1, "6": level1, "9": level1}}

    bodies = [body(95, 98), body(300, 280), body(500, 500), body(4012, 686), body(9000, 900)]
    found = oper_sets.minimum_size([_load(1, bodies=bodies)], 1)
    assert found["bytes"] == 4012
    assert found["largest_not_shrinking"] == {"bytes": 500, "gzip_bytes": 500,
                                              "body": "7:load-n1 rep 5 /b500"}
    assert oper_sets.minimum_size([_load(1, bodies=bodies[3:])], 1)["bytes"] == 4012
    with _stop("R20", "does not shrink"):
        oper_sets.minimum_size([_load(1, bodies=[body(95, 98)])], 1)


def test_screw_workers_stays_1_at_a_health_p95_of_the_probes_1_s() -> None:
    assert oper_sets.screw_workers([_load(1, health=(1.0, 20))])["workers"] == 1
    with _stop("R24", "above the probe's 1 s"):
        oper_sets.screw_workers([_load(1, health=(1.01, 400))])
    with _stop("R24", "19 health samples"):
        oper_sets.screw_workers([_load(1, health=(0.01, 19))])


def test_the_healthcheck_timeout_and_start_period_come_from_the_picked_n() -> None:
    checks = [{"offset_s": 0.0, "wall_s": w, "exit_code": 0} for w in (0.2, 0.74, 0.3)]
    found = oper_sets.healthcheck([_load(1, healthcheck=checks, time_to_healthy_s=5.01)])
    assert (found["timeout_s"], found["max_wall_s"]) == (2, 0.74)
    assert found["start_period_s"] == 20  # 2 x 5.01 s rounded up to 10 s
    assert (found["interval_s"], found["retries"]) == (30, 3)
    with _stop("R25", "no HEALTHCHECK"):
        oper_sets.healthcheck([_load(1, healthcheck=[])])


def test_r19_compares_each_levels_max_over_five_repetitions() -> None:
    by_rep: dict[int, Mapping[int, tuple[int, float]]] = {
        rep: {1: (1000, 0.1), 6: (850 if rep < 5 else 950, 0.12), 9: (800, 0.2)} for rep in REPS}
    found = oper_sets.gzip_level([_gzip("a", by_rep)])
    assert found["maxima"] == {"a at stl-preview": {"1": {"bytes": 1000, "seconds": 0.1},
                                                    "6": {"bytes": 950, "seconds": 0.12},
                                                    "9": {"bytes": 800, "seconds": 0.2}}}
    # level 6's max, 950, saves only 5 %; level 9 against level 1 saves 20 % but takes 2x
    assert found["level"] == 1


def test_r19_adopts_level_6_only_if_every_point_passes_on_its_own() -> None:
    good = _same({1: (1000, 0.1), 6: (900, 0.15), 9: (800, 0.3)})
    poor = _same({1: (1000, 0.1), 6: (901, 0.1), 9: (900, 0.1)})
    assert oper_sets.gzip_level([_gzip("a", good)])["level"] == 6
    found = oper_sets.gzip_level([_gzip("a", good), _gzip("b", poor)])
    trials = found["trials"]
    assert isinstance(trials, list)
    assert trials[0]["failing"] == ["b at stl-preview"]
    # level 9 is compared with level 1, the adopted one: 'a' takes 3x level 1's seconds
    assert trials[1]["against"] == 1
    assert trials[1]["failing"] == ["a at stl-preview"]
    assert found["level"] == 1


def test_r19_compares_level_9_with_the_adopted_level_6() -> None:
    levels = _same({1: (1000, 0.1), 6: (900, 0.15), 9: (810, 0.2)})
    found = oper_sets.gzip_level([_gzip("a", levels)])
    assert found["level"] == 9  # 810 <= 0.9 x 900 and 0.2 <= 1.5 x 0.15


def test_a_gzip_point_with_four_repetitions_stops_at_r19() -> None:
    levels = {1: (1000, 0.1), 6: (900, 0.1), 9: (800, 0.1)}
    with _stop("R19", "a at stl-preview has no max"):
        oper_sets.gzip_level([_gzip("a", dict.fromkeys(REPS[:4], levels))])


def _explore_part(label: str, params: Mapping[str, object], size: int,
                  status: str = "ok") -> list[oper_sets.Tagged]:
    return [("explore", "40646117094",
             {"type": "reading", "label": label, "kind": "bolt", "params": dict(params),
              "artifact": a, "rep": 1, "status": status, "bytes": size, "gzip1_bytes": size // 2})
            for a in ARTIFACTS3]


def test_the_export_cache_holds_the_largest_candidates_raw_and_gzip_bytes_in_whole_mib() -> None:
    explore = [*_explore_part("small", {}, 10**6), *_explore_part("big", {"length": 30.0}, 10**7),
               *_explore_part("failed", {"length": 25.0}, 10**8, status="killed")]
    found = oper_sets.export_cache(explore, [])
    assert found["part"] == "big"
    assert found["raw_and_gzip1_bytes"] == 3 * (10**7 + 5 * 10**6)
    assert found["mib"] == 43
    assert found["bytes"] == 43 * 2**20
    assert found["candidates"] == 2


def test_a_part_the_cost_model_refuses_at_any_artifact_is_no_export_cache_candidate() -> None:
    refused = {"length": 2.0, "thread_length": 1.0}  # below the fitted turns (G30)
    assert oper_sets._validated("bolt", refused) is not None
    explore = [*_explore_part("small", {}, 10**6), *_explore_part("refused", refused, 10**8)]
    assert oper_sets.export_cache(explore, [])["part"] == "small"


def test_a_gzip_reading_with_more_bytes_at_level_6_than_level_1_stops_at_r21() -> None:
    levels = _same({1: (1000, 0.1), 6: (1001, 0.1), 9: (900, 0.1)})
    with _stop("R21", "more bytes at gzip level 6 than at level 1"):
        oper_sets.export_cache(_explore_part("small", {}, 10**6), [_gzip("a", levels)])


def _scenario(nproc: Iterable[int] = (4,)) -> tuple[list[Raw], list[oper_sets.Tagged],
                                                     dict[str, list[Mapping[str, object]]]]:
    """Every set R14 to R26 read, all ok: one bound point per artifact at N 1 to 3, one gzip point,
    loads at N 1 to 3 whose p95 grows with N, and two explore parts."""
    headers: list[Raw] = [{"type": "header", "nproc": n, "mem_total_bytes": 16 * GIB}
                          for n in nproc]
    tagged: list[oper_sets.Tagged] = []
    bound: list[Mapping[str, object]] = []
    for artifact in ARTIFACTS3:
        for workers in (1, 2, 3):
            point, readings = _contended("p", artifact, workers, walls=(2.0 * workers,) * 5,
                                          peaks=(GIB // 2,) * 5)
            bound.append(point)
            tagged += [("bound", "1", r) for r in readings]
    gzip_read = _gzip("g", _same({1: (1000, 0.1), 6: (950, 0.1), 9: (940, 0.1)}))
    tagged += [("gzip", "2", r) for r in gzip_read.readings]
    bodies = [{"path": "/api/health", "status_code": 200, "bytes": 95,
               "gzip": {"1": 98, "6": 98, "9": 98}},
              {"path": "/api/presets?kind=nut", "status_code": 200, "bytes": 4012,
               "gzip": {"1": 686, "6": 619, "9": 618}}]
    loads = [_load(1, p95=10.0, peak=GIB, bodies=bodies),
             *(_load(n, p95=10.0 * n, peak=n * GIB) for n in (2, 3))]
    tagged += [("load", "3", r) for read in loads for r in read.readings]
    tagged += [*_explore_part("small", {}, 10**6), *_explore_part("big", {"length": 30.0}, 10**7)]
    sets = {"bound": bound, "gzip": [gzip_read.point], "load": [read.point for read in loads]}
    return headers, tagged, sets


def test_runtime_derives_every_value_in_order_from_a_complete_record() -> None:
    headers, tagged, sets = _scenario()
    found = oper_sets.runtime(headers, tagged, sets, ["somewhere"])
    assert found["picked_workers"] == 1  # the lowest max-over-reps p95
    assert found["w"] == {"bytes": GIB // 2, "reading": "1:p-n1 rep 1"}
    assert found["timeouts"] == {a: {"seconds": 4, "max_cold_wall_s": 2.0, "bound_point": "p-n1",
                                     "reading": "1:p-n1 rep 1"} for a in ARTIFACTS3}
    assert found["tmpfs_bytes"] == QUARTER
    assert found["mem_limit_bytes"] == 4 * QUARTER
    assert found["export_cache"]["mib"] == 43  # type: ignore[index]
    assert found["gzip"]["level"] == 1  # type: ignore[index]
    assert found["queue_depth"]["depth"] == 2  # type: ignore[index]
    assert found["minimum_size"]["bytes"] == 4012  # type: ignore[index]


def test_the_pick_goes_to_the_smaller_n_on_a_tie_in_p95() -> None:
    headers, tagged, sets = _scenario()
    tagged = [(name, run, {**r, "latency": {"all": {"samples": 60, "p95_s": 7.0}}})
              if r.get("kind") == "load" and r.get("workers") in (2, 3) else (name, run, r)
              for name, run, r in tagged]
    tagged = [(name, run, {**r, "latency": {"all": {"samples": 60, "p95_s": 9.0}}})
              if r.get("kind") == "load" and r.get("workers") == 1 else (name, run, r)
              for name, run, r in tagged]
    assert oper_sets.runtime(headers, tagged, sets, [])["picked_workers"] == 2


def test_no_qualifying_n_stops_at_r16_naming_each_reason() -> None:
    headers, tagged, sets = _scenario(nproc=(1,))
    with _stop("R16", r"no N qualifies \(G7\): N = 1: N = 1 is above nproc - 1 = 0; N = 2"):
        oper_sets.runtime(headers, tagged, sets, [])
    headers, _, _ = _scenario(nproc=(4, 2))
    with _stop("R16", "nproc"):
        oper_sets.runtime(headers, tagged, sets, [])


def test_derive_runtime_exits_3_on_a_stop_and_writes_nothing(
        repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    point, _ = _contended("pa", "step", 1)
    for name, points in (("bound", [point]), ("gzip", []), ("load", []), ("arenas", []),
                         ("drift", []), ("drift-60", [])):
        (repo / "points" / f"{name}.json").write_text(json.dumps({"points": points}))
    out = repo / "runtime.json"
    assert oper_sets.main(["derive-runtime", "--from", str(repo / "explore"), "--out",
                           str(out)]) == 3
    assert "oper_sets: stop (R14): pa-n1 at step is read in 0 runs" in capsys.readouterr().err
    assert not out.exists()


def _bound_points(labels_by_artifact: Mapping[str, Iterable[str]]) -> list[Raw]:
    out: list[Raw] = []
    for artifact, labels in labels_by_artifact.items():
        for label in labels:
            for workers in (1, 2):
                point, _ = _contended(label, artifact, workers)
                out.append(point)
    return out


def _explore_peak(label: str, artifact: str, peak: int, status: str = "ok") -> Raw:
    return {"type": "reading", "label": label, "kind": "bolt", "params": {}, "artifact": artifact,
            "rep": 1, "status": status, "memory_peak_bytes": peak}


def test_drift_takes_per_artifact_the_bound_point_with_the_largest_ok_explore_peak() -> None:
    bound = _bound_points(dict.fromkeys(ARTIFACTS3, ("aa", "bb", "cc")))
    explore = [_explore_peak("aa", a, 100) for a in ARTIFACTS3] + [
        _explore_peak("bb", a, 300) for a in ARTIFACTS3] + [
        _explore_peak("cc", a, 900, status="ok" if a == "step" else "killed")
        for a in ARTIFACTS3]
    timeouts = {"stl-preview": 26, "stl-fine": 71, "step": 26}
    found = oper_sets.drift_points(bound, explore, timeouts)
    assert [(p["label"], p["artifact"], p["k"], p["deadline_s"]) for p in found] == [
        ("drift-bb", "stl-preview", 20, 520), ("drift-bb", "stl-fine", 20, 1420),
        ("drift-cc", "step", 20, 520)]
    assert found[0]["part"] == {"kind": "bolt", "params": {"length": 2.0}}


def test_a_tie_in_the_drift_peak_goes_to_the_label_that_sorts_first() -> None:
    bound = _bound_points(dict.fromkeys(ARTIFACTS3, ("zz", "aa")))
    explore = [_explore_peak(label, a, 5) for label in ("zz", "aa") for a in ARTIFACTS3]
    found = oper_sets.drift_points(bound, explore, dict.fromkeys(ARTIFACTS3, 10))
    assert {p["label"] for p in found} == {"drift-aa"}


def test_a_drift_deadline_not_under_half_the_job_timeout_stops_at_r6() -> None:
    bound = _bound_points(dict.fromkeys(ARTIFACTS3, ("aa",)))
    explore = [_explore_peak("aa", a, 5) for a in ARTIFACTS3]
    found = oper_sets.drift_points(bound, explore, dict.fromkeys(ARTIFACTS3, 524))
    assert {p["deadline_s"] for p in found} == {10480}
    with _stop("R6", "deadline of 10500 s, not under half the job timeout"):
        oper_sets.drift_points(bound, explore, dict.fromkeys(ARTIFACTS3, 525))


def test_the_w_k_set_is_the_committed_mix_at_n1_with_k_solids_cached() -> None:
    load = json.loads((REPO_ROOT / "bench/points/load.json").read_text())["points"]
    found = oper_sets.solid_cache_points(load, 3)
    assert found == [{"label": "solid-cache-3", "kind": "load", "workers": 1, "queue": 2,
                      "clients": 2, "solid_cache": 3, "bodies": False,
                      "mix": next(p["mix"] for p in load if p["workers"] == 1)}]
    made = oper_sets.build_solid_cache(oper_sets.LOAD_POINTS, 3)
    assert (made.reps, made.shard_sizes, made.sources) == (5, [1], ["load=bench/points/load.json"])


def test_the_committed_drift_set_is_drawn_from_the_shipped_timeouts() -> None:
    drift = json.loads((REPO_ROOT / "bench/points/drift.json").read_text())
    assert drift["reps"] == 5
    for point in drift["points"]:
        assert point["deadline_s"] == 20 * cost.BUILD_TIMEOUT_S[point["artifact"]]
        assert point["deadline_s"] < oper_sets.HALF_JOB_S
    arenas = json.loads((REPO_ROOT / "bench/points/arenas.json").read_text())["points"]
    assert [p["part"] for p in drift["points"]] == [p["part"] for p in arenas[::2]]


def test_check_fails_on_a_drift_or_w_k_file_its_generator_does_not_write(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(oper_sets, "POINTS_DIR", tmp_path)
    assert oper_sets._check_runtime_sets() is None  # no such file: nothing to check
    for name in ("drift", "solid-cache-4"):
        text = (REPO_ROOT / f"bench/points/{name}.json").read_text()
        (tmp_path / f"{name}.json").write_text(text)
    assert oper_sets._check_runtime_sets() is None
    drift = tmp_path / "drift.json"
    drift.write_text(drift.read_text().replace('"deadline_s": 1420', '"deadline_s": 1400'))
    assert oper_sets._check_runtime_sets() == (f"{drift} is not what the generator writes from "
                                               "its sources")


def _w_k(k: int, peaks: Iterable[int] = (GIB,) * 5,
         statuses: Iterable[str] = ("ok",) * 5) -> oper_sets.Read:
    point: Raw = {"label": f"solid-cache-{k}", "kind": "load", "workers": 1, "queue": 2,
                  "clients": 2, "solid_cache": k, "bodies": False, "mix": []}
    return _read(point, [{**point, "type": "reading", "rep": rep, "status": status,
                          "memory_peak_bytes": peak}
                         for rep, peak, status in zip(REPS, peaks, statuses, strict=True)])


def _qualify(w_k: int) -> oper_sets.Workers:
    return _workers(_load(1, peak=1), w=w_k)


def test_r22_keeps_4_solids_when_w4_qualifies_and_names_its_run() -> None:
    found = oper_sets.solid_cache({4: _w_k(4, peaks=(1, 2, GIB, 3, 4))}, _qualify)
    assert found["k"] == 4
    assert found["runs"] == ["7"]
    assert found["w_k"] == {"4": {"w_bytes": GIB, "reading": "7:solid-cache-4 rep 3",
                                  "mem_limit_bytes": 5 * QUARTER, "qualifies": True,
                                  "why_not": []}}


def test_r22_takes_3_when_w4_does_not_qualify_and_w3_does() -> None:
    found = oper_sets.solid_cache({4: _w_k(4, peaks=(16 * GIB,) * 5), 3: _w_k(3)}, _qualify)
    assert found["k"] == 3
    assert found["runs"] == ["7", "7"]
    w_k = found["w_k"]
    assert isinstance(w_k, dict)
    assert not w_k["4"]["qualifies"]


def test_r22_stops_on_a_w_k_repetition_that_is_not_ok_on_a_k_not_measured_and_on_no_k() -> None:
    with _stop("R22", "solid-cache-4 at load has no max"):
        oper_sets.solid_cache({4: _w_k(4, statuses=("ok", "capped", "ok", "ok", "ok"))},
                              _qualify)
    with _stop("R22", r"W\(4\) does not qualify and W\(3\) is not measured"):
        oper_sets.solid_cache({4: _w_k(4, peaks=(16 * GIB,) * 5)}, _qualify)
    too_big = {k: _w_k(k, peaks=(16 * GIB,) * 5) for k in (4, 3, 2, 1)}
    with _stop("R22", "no K in 4, 3, 2, 1 qualifies"):
        oper_sets.solid_cache(too_big, _qualify)


def _drift(artifact: str, first: int = 100 * 10**6, last: int = 105 * 10**6, builds: int = 20,
           statuses: Iterable[str] = ("ok",) * 5) -> oper_sets.Read:
    point: Raw = {"label": f"drift-{artifact}", "kind": "drift", "artifact": artifact,
                  "part": {"kind": "bolt", "params": {}}, "k": 20, "deadline_s": 520}
    peaks = [first, *([last] * (builds - 1))]
    return _read(point, [{**point, "type": "reading", "rep": rep, "status": status,
                          "peaks": peaks} for rep, status in zip(REPS, statuses, strict=True)])


def _long(artifact: str, first: int = 100 * 10**6, middle: int = 120 * 10**6,
          end: int = 125 * 10**6, builds: int = 60,
          statuses: Iterable[str] = ("ok",) * 5) -> oper_sets.Read:
    """A 60-build drift reading: `first` after build 1, `middle` after builds 2 to 40, `end` after
    builds 41 to 60."""
    point: Raw = {"label": f"drift-{artifact}", "kind": "drift", "artifact": artifact,
                  "part": {"kind": "bolt", "params": {}}, "k": 60, "deadline_s": 1560}
    peaks = [first, *([middle] * 39), *([end] * 20)][:builds]
    return _read(point, [{**point, "type": "reading", "rep": rep, "status": status,
                          "peaks": peaks} for rep, status in zip(REPS, statuses, strict=True)])


def test_the_drift_is_the_max_over_repetitions_of_build_20_minus_build_1() -> None:
    found = oper_sets.drift([_drift(a) for a in ARTIFACTS3])
    row = found["step"]
    assert (row["drift_bytes"], row["allowance_bytes"]) == (5 * 10**6, 10**7)
    assert not row["above_allowance"]
    assert oper_sets.drift([_drift("step", last=112 * 10**6)])["step"]["above_allowance"]


def test_a_drift_repetition_not_ok_or_missing_build_20_stops_at_r23() -> None:
    with _stop("R23", "drift-step at step has no max"):
        oper_sets.drift([_drift("step", statuses=("ok", "killed", "ok", "ok", "ok"))])
    with _stop("R23", "has no peak after build 1 and build 20"):
        oper_sets.drift([_drift("step", builds=19)])


def test_the_plateau_holds_when_builds_41_to_60_rise_at_most_the_allowance() -> None:
    drifts = [_drift(a) for a in ARTIFACTS3]
    found = oper_sets.plateau([_long(a) for a in ARTIFACTS3], drifts)
    assert found["step"]["difference_bytes"] == 5 * 10**6
    assert found["step"]["allowance_bytes"] == 10**7
    assert found["step"]["holds"] is True
    at_it = oper_sets.plateau([_long("step", end=130 * 10**6)], drifts)  # 10 MB: at it
    assert at_it["step"]["holds"] is True


def test_a_plateau_miss_stops_at_r23_and_names_recycling_as_next() -> None:
    drifts = [_drift(a) for a in ARTIFACTS3]
    with _stop("R23", "the plateau does not hold: step: builds 41 to 60 peak 10000001 bytes .*"
                      "the next step is recycling"):
        oper_sets.plateau([_long("stl-fine"), _long("step", end=130 * 10**6 + 1)], drifts)


def test_the_plateau_allowance_is_a_tenth_of_the_smallest_build_1_peak_of_both_readings() -> None:
    drifts = [_drift("step", first=80 * 10**6)]
    with _stop("R23", "over its allowance of 8000000.0 bytes"):
        oper_sets.plateau([_long("step", end=129 * 10**6)], drifts)


def test_a_plateau_repetition_not_ok_or_short_of_60_builds_stops_at_r23() -> None:
    drifts = [_drift("step")]
    with _stop("R23", "drift-step at step has no max"):
        oper_sets.plateau([_long("step", statuses=("ok", "ok", "capped", "ok", "ok"))], drifts)
    with _stop("R23", "has no peak after each of its 60 builds"):
        oper_sets.plateau([_long("step", builds=59)], drifts)


def test_the_drift_peak_is_the_largest_peak_after_any_build_of_both_readings() -> None:
    found = oper_sets.drift_peak([_drift("step"), _long("stl-fine", end=7 * 10**8)])
    assert found == (7 * 10**8, "7:drift-stl-fine rep 1 build 41")


def test_a_60_build_drift_set_takes_60_x_the_timeout_and_stops_at_r6_past_half_the_job() -> None:
    bound = _bound_points(dict.fromkeys(ARTIFACTS3, ("aa",)))
    explore = [_explore_peak("aa", a, 5) for a in ARTIFACTS3]
    found = oper_sets.drift_points(bound, explore, dict.fromkeys(ARTIFACTS3, 26), builds=60)
    assert {(p["k"], p["deadline_s"]) for p in found} == {(60, 1560)}
    with _stop("R6", "deadline of 10500 s"):
        oper_sets.drift_points(bound, explore, dict.fromkeys(ARTIFACTS3, 175), builds=60)


def test_the_committed_60_build_set_is_the_20_build_set_read_60_times() -> None:
    short = json.loads((REPO_ROOT / "bench/points/drift.json").read_text())["points"]
    long = json.loads((REPO_ROOT / "bench/points/drift-60.json").read_text())["points"]
    assert [(p["label"], p["artifact"], p["part"]) for p in long] == [
        (p["label"], p["artifact"], p["part"]) for p in short]
    for point in long:
        assert point["k"] == 60
        assert point["deadline_s"] == 60 * cost.BUILD_TIMEOUT_S[point["artifact"]]


def _arenas(current: Mapping[tuple[str, bool], int]) -> list[oper_sets.Read]:
    reads = []
    for (artifact, trim), value in current.items():
        point: Raw = {"label": f"arenas-{artifact}-{trim}", "kind": "arenas",
                      "artifact": artifact, "part": {"kind": "bolt", "params": {}}, "trim": trim}
        reads.append(_read(point, [{**point, "type": "reading", "rep": rep, "status": "ok",
                                    "memory_current_bytes": value - rep} for rep in REPS]))
    return reads


def test_the_trim_is_kept_only_if_its_max_current_is_lower_at_every_artifact() -> None:
    lower = {(str(a), trim): 100 if trim else 200 for a in ARTIFACTS3 for trim in (True, False)}
    found = oper_sets.arenas(_arenas(lower))
    assert found["kept"] is True
    maxima = found["maxima"]
    assert isinstance(maxima, dict)
    assert maxima["step"] == {"trim_on": {"memory_current_bytes": 99,
                                          "reading": "7:arenas-step-True rep 1"},
                              "trim_off": {"memory_current_bytes": 199,
                                           "reading": "7:arenas-step-False rep 1"}}
    assert oper_sets.arenas(_arenas({**lower, ("stl-fine", True): 200}))["kept"] is False
    reads = _arenas(lower)
    reads[0] = _read(reads[0].point, reads[0].readings[:4])
    with _stop("R23", "has no max"):
        oper_sets.arenas(reads)


def _stage_two(drift_end: int = 105 * 10**6, plateau_middle: int = 120 * 10**6,
               plateau_end: int = 125 * 10**6) -> tuple[
        list[Raw], list[oper_sets.Tagged], dict[str, list[Mapping[str, object]]]]:
    headers, tagged, sets = _scenario()
    w_k = _w_k(4, peaks=(3 * GIB,) * 5)
    drifts = [_drift(a, last=drift_end) for a in ARTIFACTS3]
    longs = [_long(a, middle=plateau_middle, end=plateau_end) for a in ARTIFACTS3]
    release = _arenas({(str(a), trim): 100 if trim else 200 for a in ARTIFACTS3
                       for trim in (True, False)})
    tagged = [*tagged, *(("solid-cache-4", "4", r) for r in w_k.readings),
              *(("drift", "5", r) for read in drifts for r in read.readings),
              *(("drift-60", "8", r) for read in longs for r in read.readings),
              *(("arenas", "6", r) for read in release for r in read.readings)]
    sets = {**sets, "solid-cache-4": [w_k.point], "drift": [read.point for read in drifts],
            "drift-60": [read.point for read in longs],
            "arenas": [read.point for read in release]}
    return headers, tagged, sets


def test_stage_two_ships_the_larger_mem_limit_and_keeps_the_tessellation() -> None:
    headers, tagged, sets = _stage_two()
    found = dict(oper_sets.derivation(headers, tagged, sets, [], stage_two=True))
    assert found["solid_cache_k"] == 4
    # W(4) 3 GiB + B 50 MiB + the 43 MiB cache + the 256 MiB tmpfs is 3421 MiB: 3.5 GiB
    assert found["shipped_mem_limit"] == {"bytes": 14 * QUARTER, "from_w_bytes": 4 * QUARTER,
                                          "from_w_k_bytes": 14 * QUARTER}
    assert found["arenas_kept"] is True
    assert found["recycling"] == {"max_tasks_per_child": None,
                                  "rule": "R23: the plateau holds at every artifact, and the "
                                          "drift is counted in W (R16)"}
    assert found["tessellation_kept"] == {"kept": True,
                                          "rule": "R23: the tessellation presets are kept"}
    assert set(oper_sets.runtime(headers, tagged, sets, [])) < set(found)


def test_w_takes_the_drift_peak_and_a_20_build_drift_above_its_allowance_stops_nothing() -> None:
    headers, tagged, sets = _stage_two(drift_end=GIB, plateau_middle=GIB, plateau_end=GIB)
    found = dict(oper_sets.derivation(headers, tagged, sets, [], stage_two=True))
    drifts = found["drift"]
    assert isinstance(drifts, dict)
    assert drifts["step"]["above_allowance"]  # a tenfold drift, absorbed into W (G32)
    assert found["w"] == {"bytes": GIB, "contention": {"bytes": GIB // 2,
                                                       "reading": "1:p-n1 rep 1"},
                          "drift": {"bytes": GIB, "reading": "5:drift-stl-preview rep 1 build 2"}}
    assert found["mem_limit_bytes"] == 6 * QUARTER  # 1 GiB + 349 MiB rounds up to 1.5 GiB
    assert dict(oper_sets.derivation(headers, tagged, sets, []))["w"] == {
        "bytes": GIB // 2, "reading": "1:p-n1 rep 1"}


def test_stage_two_stops_at_a_plateau_miss_before_any_value() -> None:
    headers, tagged, sets = _stage_two(plateau_end=131 * 10**6)
    with _stop("R23", "the plateau does not hold"):
        dict(oper_sets.derivation(headers, tagged, sets, [], stage_two=True))


def test_the_committed_records_keep_4_solids_and_the_trim_and_count_the_drift_in_w(
        capsys: pytest.CaptureFixture[str]) -> None:
    """07-16 on the record: W(4) qualifies (run 41016510597), the trim lowers memory.current at
    every artifact (run 40909754190), and the 20-build drift (run 41016507364) is above its
    allowance at all three artifacts, but the 60-build run 41022812680 levels off (G32)."""
    directories = sorted(str(p) for p in (REPO_ROOT / "bench/results/phase-07").iterdir()
                         if p.is_dir())
    assert oper_sets.main(["check-r22-r23", "--from", *directories]) == 0
    out, err = capsys.readouterr()
    assert err == ""
    assert '"solid_cache_k": 4' in out
    assert '"arenas_kept": true' in out
    assert '"bytes": 2415919104' in out  # G20: the shipped mem_limit
    assert '"above_allowance": true' in out
    assert '"holds": false' not in out


# --- R27 step 5: the required tier (07-18) -------------------------------------------------------

PREVIEW_ONLY: dict[str, tuple[list[str], list[str]]] = {"stl-fine": ([], []), "step": ([], [])}


def _step5(edge: list[float], draw: list[float | str], timeout: float = 250.0,
           envelope: Mapping[tuple[str, str, str], float] | None = None) -> list[Raw]:
    """R27 step 5 over a synthetic stl-preview D(A): the edge points' charges, then the draw's; a
    text in the draw is a reading with that status (its wall is far above any charge)."""
    labels = [f"q{i}" for i in range(len(edge) + len(draw))]
    points = [_pt(label, "bolt", {"length": 4.0 + i / 2}, "stl-preview")
              for i, label in enumerate(labels)]
    readings = [_reading(p, charge, wall=9e9) if isinstance(charge, str)
                else _reading(p, wall=9e9, build=charge, export=0.0)
                for p, charge in zip(points, [*edge, *draw], strict=True)]
    tier = _tier({"stl-preview": (labels[:len(edge)], labels[len(edge):]), **PREVIEW_ONLY})
    return oper_sets.boundary_points(tier, points, readings, envelope or _flat(),
                                     dict.fromkeys(ARTIFACTS3, timeout))


def test_the_edge_points_are_taken_even_when_their_charges_alone_reach_the_tier() -> None:
    assert [(p["label"], p["charge_s"]) for p in _step5([300.0, 300.0, 300.0], [1.0])] == [
        ("q0", 300.0), ("q1", 300.0), ("q2", 300.0)]


def test_draw_points_are_taken_in_order_until_the_first_that_does_not_fit_and_none_after() -> None:
    taken = _step5([50.0, 50.0, 100.0], [100.0, 150.0, 400.0, 50.0])
    assert [p["label"] for p in taken] == ["q0", "q1", "q2", "q3", "q4"]  # 450 s; 850 s does not


def test_a_sum_of_exactly_the_tier_does_not_fit() -> None:
    assert [p["label"] for p in _step5([100.0, 50.0, 50.0], [100.0, 300.0])] == [
        "q0", "q1", "q2", "q3"]


def test_a_point_not_ok_at_explore_is_charged_its_full_timeout_and_an_ok_one_its_cold_wall(
) -> None:
    taken = _step5([100.0, 50.0, 50.0], ["killed", 100.0, "refused"])
    assert [(p["label"], p["charge_s"]) for p in taken] == [
        ("q0", 100.0), ("q1", 50.0), ("q2", 50.0), ("q3", 250.0), ("q4", 100.0)]


def test_every_tier_point_carries_its_timeout_and_its_enveloped_limit_per_target() -> None:
    envelope = _flat(0.25)
    for point in _step5([1.0, 1.0, 1.0], [1.0, 1.0], timeout=26.0, envelope=envelope):
        part = _part(point)
        assert point["timeout_s"] == 26.0
        assert point["limit"] == dict(zip(cost.TARGETS, oper_sets.enveloped(
            part, "stl-preview", envelope), strict=True))
        assert set(point) == {"label", "kind", "params", "artifact", "charge_s", "estimate_s",
                              "timeout_s", "limit"}


def test_a_shard_estimate_is_the_container_wall_or_the_timeout_where_explore_was_not_ok(
) -> None:
    points = _bolts([4.0, 5.0, 6.0, 7.0], prefix="q")
    readings = _ok_readings(points, q1={"wall_s": 40.0}, q2={"status": "killed", "wall_s": 600.4},
                            q3={"status": "refused", "wall_s": 3.0})
    tier = _tier({"stl-preview": (["q0", "q1", "q2"], ["q3"]), **PREVIEW_ONLY})
    taken = oper_sets.boundary_points(tier, points, readings, _flat(),
                                      dict.fromkeys(ARTIFACTS3, 26.0))
    assert [(p["label"], p["estimate_s"]) for p in taken] == [
        ("q0", 3.0), ("q1", 40.0), ("q2", 600.4), ("q3", 26.0)]


def test_a_widened_envelope_moves_each_points_limit_and_nothing_else() -> None:
    narrow = _step5([100.0, 50.0, 50.0], [100.0, 150.0, 400.0], envelope=_flat(0.25))
    wide = _step5([100.0, 50.0, 50.0], [100.0, 150.0, 400.0], envelope=_flat(0.75))
    assert [{k: v for k, v in p.items() if k != "limit"} for p in narrow] == [
        {k: v for k, v in p.items() if k != "limit"} for p in wide]
    for a, b in zip(narrow, wide, strict=True):
        assert isinstance(a["limit"], dict)
        assert isinstance(b["limit"], dict)
        assert all(b["limit"][target] > a["limit"][target] for target in cost.TARGETS)


def test_the_tier_takes_its_order_and_members_from_tier_order_alone() -> None:
    points = _bolts([4.0 + i / 2 for i in range(6)], prefix="q")
    readings = _ok_readings(points)
    tier = _tier({"stl-preview": (["q5", "q0", "q3"], ["q1"]), "stl-fine": (["q2"], []),
                  "step": ([], ["q4"])})
    taken = oper_sets.boundary_points(tier, points, readings, _flat(),
                                      dict.fromkeys(ARTIFACTS3, 26.0))
    assert [(p["label"], p["artifact"]) for p in taken] == [
        ("q5", "stl-preview"), ("q0", "stl-preview"), ("q3", "stl-preview"),
        ("q1", "stl-preview"), ("q2", "stl-fine"), ("q4", "step")]


def test_a_tier_point_with_no_explore_reading_stops_the_phase() -> None:
    points = _bolts([4.0, 5.0], prefix="q")
    tier = _tier({"stl-preview": (["q0"], ["q1"]), **PREVIEW_ONLY})
    with _stop("R27", "q1 at stl-preview has no explore reading"):
        oper_sets.boundary_points(tier, points, _ok_readings(points[:1]), _flat(),
                                  dict.fromkeys(ARTIFACTS3, 26.0))


def test_the_committed_boundary_file_is_what_the_shipped_constants_write() -> None:
    """T-07-46: a change to the model, the envelope, a budget or a timeout cannot ship with a stale
    required tier; T-07-69: it is cut from the committed D(A) and the explore run Runs II drew
    from, never from a list drawn again."""
    text = (REPO_ROOT / oper_sets.BOUNDARY).read_text()
    sources = dict(str(entry).split("=", 1) for entry in json.loads(text)["sources"])
    bound = json.loads((REPO_ROOT / "bench" / "points" / "bound.json").read_text())
    assert sources["tier-order"] == oper_sets.TIER_ORDER
    assert f"explore={sources['explore']}" in bound["sources"]
    assert text == oper_sets.boundary_text(sources["explore"])


def test_the_boundary_command_writes_the_file_from_the_committed_d_of_a(
        runs2_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert _runs2(runs2_repo, "tier-order") == 0
    out = runs2_repo / "boundary.json"
    assert oper_sets.main(["boundary", "--explore", str(runs2_repo / "ex2"),
                           "--out", str(out)]) == 0
    document = json.loads(out.read_text())
    assert out.read_text() == oper_sets.boundary_text("ex2")
    assert document["sources"] == [f"tier-order={oper_sets.TIER_ORDER}", "explore=ex2"]
    assert document["timeouts"] == dict(cost.BUILD_TIMEOUT_S)
    assert {p["artifact"] for p in document["points"]} == set(ARTIFACTS3)
    assert f"wrote {out}" in capsys.readouterr().out


def test_the_records_check_writes_are_read_by_the_envelope_check(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """R12 widens from recorded readings: the `bounds-records` artifact, downloaded into a folder
    of its own as `gh run download -p` lays it out, is a source `envelope-check --from` reads."""
    point = _pt("q0", "bolt", {"length": 20.0}, "stl-preview")
    part = _part(point)
    limit = dict(zip(cost.TARGETS, oper_sets.enveloped(part, "stl-preview", _flat()), strict=True))
    boundary = tmp_path / "boundary.json"
    boundary.write_text(json.dumps({"points": [{**point, "timeout_s": 26.0, "limit": limit}]}))
    reading = {**_reading(point, build=1.0, export=0.5), "bytes": 10**12}
    monkeypatch.setattr(oper, "run_reading", lambda *args, **kwargs: dict(reading))
    monkeypatch.setattr(oper, "_image_versions", lambda image: {})
    monkeypatch.setattr(oper, "header", lambda image, versions: {
        "type": "header", "GITHUB_RUN_ID": "41"})
    out = tmp_path / "bounds-41" / "bounds-records" / "bounds-records.jsonl"
    out.parent.mkdir(parents=True)
    assert oper.main(["check", str(boundary), "--image", "i", "--out", str(out)]) == 1
    tagged = oper_sets.runs_readings([tmp_path / "bounds-41"])
    assert tagged == [("bounds", "41", reading)]
    assert all(oper_sets.widens(name, found) for name, _, found in tagged)


# --- the drift of a regeneration on another host (07-18) ------------------------------------------


def test_a_last_bit_change_of_a_limit_or_an_edge_ratio_is_a_predicted_drift() -> None:
    limit = 6801399.663168809
    committed = {"points": [{"label": "a", "charge_s": 1.5, "limit": {"bytes": limit}}],
                 "edge_ranking": [{"label": "a", "edge_ratio": 0.5}]}
    fresh = {"points": [{"label": "a", "charge_s": 1.5,
                         "limit": {"bytes": math.nextafter(limit, math.inf)}}],
             "edge_ranking": [{"label": "a", "edge_ratio": math.nextafter(0.5, 0.0)}]}
    found = oper_sets.drifts(committed, fresh)
    assert [(d.path, d.predicted) for d in found] == [
        ("$.points[0].limit.bytes", True), ("$.edge_ranking[0].edge_ratio", True)]
    assert found[0].relative == math.ulp(limit) / limit


@pytest.mark.parametrize("fresh", [
    {"points": [{"label": "b", "charge_s": 1.5, "limit": {"bytes": 1.0}}]},
    {"points": [{"label": "a", "charge_s": 1.6, "limit": {"bytes": 1.0}}]},
    {"points": [{"charge_s": 1.5, "label": "a", "limit": {"bytes": 1.0}}]},
    {"points": []},
    {"points": [{"label": "a", "charge_s": 1.5, "limit": {"bytes": 1}}]},
])
def test_any_other_change_is_a_drift_that_is_not_predicted(fresh: Raw) -> None:
    committed = {"points": [{"label": "a", "charge_s": 1.5, "limit": {"bytes": 1.0}}]}
    found = oper_sets.drifts(committed, fresh)
    assert found
    assert not any(d.predicted for d in found)
    assert all(d.relative == float("inf") for d in found)


def test_the_drift_command_lists_every_regenerable_file(
        capsys: pytest.CaptureFixture[str]) -> None:
    assert oper_sets.main(["prediction-drift"]) == 0
    rows = capsys.readouterr().out.splitlines()
    files = [row.split(" | ")[0] for row in rows[1:]]
    for name in (oper_sets.TIER_ORDER, oper_sets.BOUNDARY, "bench/points/bound.json",
                 "bench/points/explore.json", "bench/points/drift-60.json"):
        assert name in files
