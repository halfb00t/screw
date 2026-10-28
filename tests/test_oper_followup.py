"""The code that applies R5 to R10 of the sweep protocol to runner records (07-05): the margin, R6's
charges and shards, the R7 walk-down, the pre-confirm wall decisions, the walls confirm set and
every "the phase stops and asks the owner" among them.

Everything runs on synthetic records written from the real `walls` and `spread` point sets, so a
label, a parameter and a lift are the ones the runner would record; no Docker, no kernel.
"""

from __future__ import annotations

import functools
import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path

import pytest

from bench import oper, oper_sets
from bench.oper_sets import ProtocolStop
from bench.thread_spike.maths import PITCH

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


def _void_walk(radii: Iterable[float], status: str) -> dict[str, str]:
    """The void-walk labels at `radii`: nuts only, as no rod is walked above 1e-2 mm."""
    return _roots(radii, status, ("nut",))


def _voids(over: Mapping[str, str] | None = None, drop: Iterable[str] = ()) -> list[Raw]:
    """A reading of every void-walk point, ok unless `over` says otherwise, minus `drop`."""
    over, gone = over or {}, set(drop)
    return [_reading(p, over.get(str(p["label"]), "ok")) for p in oper_sets.void_walk_points()
            if p["label"] not in gone]


def _decide(walls: list[Raw], down: Iterable[Raw] = (),
            voids: list[Raw] | None = None) -> oper_sets.Decision:
    """`decide_walls` over a void walk that is all ok unless given."""
    return oper_sets.decide_walls(walls, down, _voids() if voids is None else voids)


def _walls_as_read() -> dict[str, str]:
    """Walls group (d) as the first runner reading found it: every nut void refused at all nine
    radii, the rods refused from 3e-4 mm down (so F = 3e-4 from the rods alone, before G25)."""
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
    assert (decision.tail.read, decision.root.read) == (48, 660)


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


def test_a_failing_group_d_root_is_held_by_the_void_walk_above_it() -> None:
    # Before the void walk, V = 1e-1 lay outside the walk and stopped the phase.
    assert _decide(_walls(_roots([3e-3], "refused"))).root.v == 1e-1


def test_voids_failing_through_1e_1_and_ok_at_3e_1_and_1_give_v_of_1_mm() -> None:
    decision = _decide(_walls(_walls_as_read()), voids=_voids(_void_walk([3e-2, 1e-1], "refused")))
    assert decision.root.v == 1.0
    assert decision.root.read == 660
    assert decision.root.failing[0] == oper_sets._root_label("nut", "M2", False, 0.1)


def test_a_void_that_fails_at_1_mm_stops_the_phase_and_the_walk_is_not_extended() -> None:
    voids = _voids(_void_walk(oper_sets.VOID_RADII, "refused"))
    with _stop("R10", "V is 10"):
        _decide(_walls(_walls_as_read()), voids=voids)


def test_a_void_that_fails_at_3e_1_puts_v_above_the_walk() -> None:
    with _stop("R10", "V is 10"):
        _decide(_walls(_walls_as_read()), voids=_voids(_void_walk([3e-1], "refused")))


def test_an_all_ok_void_walk_leaves_v_to_group_d() -> None:
    nuts = _roots(oper_sets.ROOT_RADII, "refused", ("nut",))
    assert _decide(_walls(nuts)).root.v == 1e-1
    rods = _roots([3e-4], "refused", ("bolt",))
    assert _decide(_walls(rods)).root.v == 1e-2


def test_a_missing_void_reading_stops_the_phase() -> None:
    label = oper_sets._root_label("nut", "M8", True, 3e-1)
    with _stop("R10", label):
        _decide(_walls(), voids=_voids(drop=[label]))


def test_a_killed_void_at_or_above_v_stops_the_phase() -> None:
    label = oper_sets._root_label("nut", "M8", True, 3e-1)
    with _stop("R10", label):
        _decide(_walls(_walls_as_read()), voids=_voids({label: "killed"}))


def test_a_void_walk_label_read_in_the_walls_records_too_is_read_twice() -> None:
    twice = oper_sets.void_walk_points()[0]
    with _stop("R10", "read twice"):
        _decide([*_walls(), _reading(twice)])


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
    ("R10", oper_sets._root_label("nut", "M8", True, 1e-6))])
def test_a_missing_tail_or_root_reading_stops_the_phase(rule: str, label: str) -> None:
    with _stop(rule):
        _decide(_walls(drop=[label]))


# --- R3: the walls confirm set -------------------------------------------------------------------


def _decision(over: Mapping[str, str] | None = None, down: list[Raw] | None = None,
              voids: list[Raw] | None = None) -> oper_sets.Decision:
    return _decide(_walls(over), down or (), voids)


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
    assert len(roots) == 120
    assert {_root_of(lb) for lb in roots} == {"0.001", "0.0003"}


def test_a_v_inside_the_void_walk_is_confirmed_at_v_and_the_next_smaller_void_radius() -> None:
    held = {str(p["label"]): p for p in oper_sets.void_walk_points()}
    top = _decision(_walls_as_read(), voids=_voids(_void_walk([3e-2, 1e-1], "refused")))
    assert top.root.v == 1.0
    points = oper_sets.confirm_points(top)
    roots = [p for p in points if str(p["label"]).startswith("root-")]
    assert len(roots) == 60
    assert {_root_of(str(p["label"])) for p in roots} == {"1", "0.3"}
    assert all(p == held[str(p["label"])] for p in roots)
    assert not any(str(p["label"]).startswith("root-bolt-") for p in points)

    low = oper_sets.confirm_points(_decision(_roots(oper_sets.ROOT_RADII, "refused", ("nut",))))
    roots = [p for p in low if str(p["label"]).startswith("root-")]
    assert len(roots) == 60
    assert {_root_of(str(p["label"])) for p in roots} == {"0.1", "0.03"}
    assert all(p == held[str(p["label"])] for p in roots)


def test_above_zero_is_confirmed_at_the_smallest_walked_value_and_nothing_past_it() -> None:
    labels = _labels(oper_sets.confirm_points(_decision()))
    tails = [lb for lb in labels if lb.startswith("tail-")]
    assert len(tails) == 6
    assert {_tail_of(lb) for lb in tails} == {"1e-9"}
    roots = [lb for lb in labels if lb.startswith("root-")]
    assert len(roots) == 60
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
    _write_records(root / "voids", _voids())
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
                           str(repo / "down"), "--voids", str(repo / "voids")]) == 0
    assert "T = 230 turns" in capsys.readouterr().out
    assert oper_sets.main(["confirm", "--walls", str(repo / "walls2"), "--down",
                           str(repo / "down"), "--voids", str(repo / "voids"),
                           "--explore", str(repo / "explore"), "--out", str(confirm)]) == 0
    doc = json.loads(confirm.read_text())
    assert doc["reps"] == 5
    assert sum(doc["shard_sizes"]) == len(doc["points"])
    assert doc["sources"] == ["walls=walls2", "walls-down=down", "walls-voids=voids",
                              "explore=explore"]
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
    assert oper_sets.main(["decide-walls", "--walls", str(repo / "walls2"), "--voids",
                           str(repo / "voids")]) == 3
    assert "oper_sets: stop (R7):" in capsys.readouterr().err


@pytest.mark.parametrize("command", ["decide-walls", "confirm"])
def test_decide_walls_and_confirm_cannot_run_without_the_void_walk(
        repo: Path, command: str) -> None:
    args = [command, "--walls", str(repo / "walls")]
    if command == "confirm":
        args += ["--explore", str(repo / "explore"), "--out", str(repo / "out.json")]
    with pytest.raises(SystemExit) as stop:
        oper_sets.main(args)
    assert stop.value.code == 2


def test_decide_walls_applies_the_amended_r10_to_group_d_and_the_void_walk(
        repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_records(repo / "as-read", _walls(_walls_as_read()))
    _write_records(repo / "voids-1", _voids(_void_walk([3e-2, 1e-1], "refused")))
    args = ["decide-walls", "--walls", str(repo / "as-read"), "--voids", str(repo / "voids-1")]
    assert oper_sets.main(args) == 0
    assert "root (R10): V = 1 mm;" in capsys.readouterr().out

    _write_records(repo / "voids-2", _voids(_void_walk(oper_sets.VOID_RADII, "refused")))
    args = ["decide-walls", "--walls", str(repo / "as-read"), "--voids", str(repo / "voids-2")]
    assert oper_sets.main(args) == 3
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
