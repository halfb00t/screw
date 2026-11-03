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
from bench.oper_sets import ProtocolStop
from screw.calc import cost, thread

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


# --- F5: the band edges and the check cells -----------------------------------------------------


def _readings(failing: dict[str, str]) -> list[Raw]:
    """One reading per walk point: `failing[label]` for the labels named, else ok. A label that is
    not a point of the walk is a mistake in the test, not a foreign reading."""
    points = _list("points")
    assert set(failing) <= {str(p["label"]) for p in points}, set(failing)
    return [{**p, "rep": 1, "status": failing.get(str(p["label"]), "ok")} for p in points]


def _band(d: str, q: str = "7", n: int = 50, hand: str = "right") -> str:
    return f"band-d{d}-q{q}-n{n}-{hand}"


def _stop(failing: dict[str, str], match: str) -> None:
    with pytest.raises(ProtocolStop, match=match) as raised:
        oper_sets.fine_bands(_list("points"), _readings(failing))
    assert raised.value.rule == "F5"


TWO_BANDS = {_band("0.5"): "refused", _band("0.85", "7", 90, "left"): "refused",
             _band("1.6", "6.5"): "refused", _band("3.3", "7.5", 70): "crashed"}


def _bands(failing: dict[str, str]) -> tuple[oper_sets.Band, ...]:
    return oper_sets.fine_bands(_list("points"), _readings(failing))


def test_no_refusal_gives_no_band_and_an_empty_block() -> None:
    bands = _bands({})
    assert bands == ()
    block = oper_sets.fine_bands_block(bands, "somewhere")
    assert ("FINE_BOLT_BANDS: tuple[tuple[Fraction, Fraction], ...] = ()\n"
            "# END fine-bands\n") in block
    assert "no band: no bolt of the walk was refused or crashed above d / pitch 6" in (
        oper_sets.fine_bands_text(bands, (), 0))


def test_a_band_is_the_two_walked_sizes_just_outside_its_refusals_and_crashed_counts() -> None:
    bands = _bands(TWO_BANDS)
    assert [(b.low, b.high) for b in bands] == [
        (Fraction("0.45"), Fraction("0.9")), (Fraction("1.55"), Fraction("3.35"))]
    assert bands[0].refused == (_band("0.5"), _band("0.85", "7", 90, "left"))
    assert bands[1].refused == (_band("1.6", "6.5"), _band("3.3", "7.5", 70))


def test_the_text_names_each_band_its_edges_and_the_check_group() -> None:
    bands = _bands(TWO_BANDS)
    text = oper_sets.fine_bands_text(bands, ("check-d3-q9-n3-right",), 1234)
    assert f"band-1: d in (0.45, 0.9), excluded, from 2 refused readings, first {_band('0.5')}" in (
        text)
    assert "band-2: d in (1.55, 3.35), excluded, from 2 refused readings, first " in text
    assert "check: 1 refused inside a band (check-d3-q9-n3-right), 1234 ok outside every band" in (
        text)


def test_the_block_lists_the_bands_in_ascending_d_each_on_its_own_line() -> None:
    block = oper_sets.fine_bands_block(_bands(TWO_BANDS), "bench/results/x")
    assert block == (
        "# BEGIN fine-bands: written by `python -m bench.oper_sets fine-bands --from\n"
        "# bench/results/x`; not edited by hand.\n"
        "FINE_BOLT_BANDS: tuple[tuple[Fraction, Fraction], ...] = (\n"
        '    (Fraction("0.45"), Fraction("0.9")),\n'
        '    (Fraction("1.55"), Fraction("3.35")),\n'
        ")\n"
        "# END fine-bands\n")
    assert all(len(line) <= 100 for line in block.splitlines())


def test_an_edge_refusal_at_exact_d_over_pitch_6_stops() -> None:
    """F5 S2."""
    _stop({_band("2", "6"): "refused"}, r"S2.*d / pitch")


def test_an_edge_refusal_at_d_4_or_more_stops() -> None:
    """F5 S3: outside both bands."""
    _stop({_band("4"): "refused"}, "S3")
    _stop({_band("20", "8"): "crashed"}, "S3")


@pytest.mark.parametrize("d", ["0.3", "1.2", "1.3", "3.8"])
def test_a_refused_size_at_either_end_of_a_walked_range_stops(d: str) -> None:
    """F5 S3: a range end has no out value."""
    _stop({_band(d): "refused"}, rf"S3.*{d}")


@pytest.mark.parametrize("status", ["killed", "capped", "no_cgroup"])
def test_a_reading_that_is_not_ok_refused_or_crashed_stops(status: str) -> None:
    """F5 S1: cost or a gap."""
    _stop({_band("0.5"): "refused", _band("1.6"): status}, rf"S1.*is {status}")


def test_a_missing_a_doubled_or_a_foreign_reading_stops() -> None:
    """F5 S1."""
    every = _readings(TWO_BANDS)
    points = _list("points")
    with pytest.raises(ProtocolStop, match=r"S1.*1 points of the walk have no reading") as raised:
        oper_sets.fine_bands(points, every[1:])
    assert raised.value.rule == "F5"
    with pytest.raises(ProtocolStop, match=r"S1.*was read twice"):
        oper_sets.fine_bands(points, [*every, every[0]])
    with pytest.raises(ProtocolStop, match=r"S1.*is not a point of the walk"):
        oper_sets.fine_bands(points, [*every, {**every[0], "label": "band-elsewhere"}])


def test_a_catalogue_bolt_above_d_over_pitch_6_inside_a_band_stops(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """F5 S4: D-15, no catalogue bolt moves."""
    assert len(_bands(TWO_BANDS)) == 2
    monkeypatch.setattr(oper_sets, "_catalogue_bolts",
                        lambda: [("planted", Fraction(2), Fraction("0.3"))])
    _stop(TWO_BANDS, r"S4.*planted")
    monkeypatch.setattr(oper_sets, "_catalogue_bolts",
                        lambda: [("on the edge", Fraction("1.55"), Fraction("0.2")),
                                 ("at six", Fraction(2), Fraction("0.5"))])
    assert len(_bands(TWO_BANDS)) == 2


def test_the_shipped_catalogue_holds_no_bolt_above_6_inside_a_band() -> None:
    assert all(d / pitch <= 6 or not 1 <= d <= 4 for _, d, pitch in oper_sets._catalogue_bolts())
    assert oper_sets._catalogue_bolts()


CHECK_IN = "check-d3-q9-n3-right"


def test_a_check_cell_refused_inside_a_band_is_listed_and_moves_no_edge() -> None:
    failing = {**TWO_BANDS, CHECK_IN: "refused"}
    bands = _bands(failing)
    assert [(b.low, b.high) for b in bands] == [
        (Fraction("0.45"), Fraction("0.9")), (Fraction("1.55"), Fraction("3.35"))]
    inband, ok_outside, walled = oper_sets.check_group(
        _list("points"), _readings(failing), bands)
    assert walled == ()
    assert inband == (CHECK_IN,)
    outside = [p for p in _list("points") if str(p["label"]).startswith("check-")
               if not any(b.low < Fraction(repr(_params(p)["d"])) < b.high for b in bands)]
    assert ok_outside == len(outside) > 0


@pytest.mark.parametrize("label", ["check-d1.4-q12.5-n3-right",   # between the bands
                                   "check-d3.4-q9-n3-right",       # just past band 2's edge
                                   "check-n3s-d150-q9-right",      # the n3s form
                                   "check-d0.3-q20-n30-left"])     # a walked range's end
def test_a_check_cell_refused_or_crashed_outside_every_band_stops(label: str) -> None:
    """F5 S5 (D-19)."""
    _stop({**TWO_BANDS, label: "refused"}, r"S5.*D-19")
    _stop({**TWO_BANDS, label: "crashed"}, r"S5.*D-19")


def test_a_check_refusal_with_no_band_at_all_stops() -> None:
    """F5 S5 (D-19): no band, no cell inside one."""
    _stop({CHECK_IN: "refused"}, "S5")


# F15 (owner ruling at S5, L37): a refused check cell at 0.45 < d < 0.9 and d / pitch above 9,
# outside every band, is the parameter model's to refuse and is no stop. Nothing else is let
# through.

ONE_BAND = {_band("1.6", "6.5"): "refused", _band("3.3", "7.5", 70): "crashed"}
WALLED = ("check-d0.5-q12.5-n90-right", "check-d0.85-q20-n90-left", "check-d0.6-q16-n90-right")


def test_a_check_cell_above_the_small_d_wall_is_walled_and_no_stop() -> None:
    failing = {**ONE_BAND, WALLED[0]: "refused", WALLED[1]: "crashed", WALLED[2]: "refused"}
    bands = _bands(failing)
    assert [(b.low, b.high) for b in bands] == [(Fraction("1.55"), Fraction("3.35"))]
    inband, _, walled = oper_sets.check_group(_list("points"), _readings(failing), bands)
    assert inband == ()
    assert walled == tuple(sorted(WALLED))


@pytest.mark.parametrize("label", [
    "check-d0.5-q9-n90-right",       # d / pitch at most 9: the wall admits it
    "check-d0.45-q20-n90-right",     # d 0.45 is not strictly inside the interval
    "check-d0.9-q12.5-n90-left",     # nor is d 0.9
    "check-d0.95-q16-n90-right",     # past the interval
    "check-d0.4-q16-n90-right",      # before it
    "check-d1.4-q12.5-n3-right",     # between the bands
    "check-n3s-d150-q9-right"])      # another kind of cell
def test_a_refused_check_cell_the_small_d_wall_does_not_hold_still_stops(label: str) -> None:
    """F15 hides no other refusal: the wall holds only 0.45 < d < 0.9 above d / pitch 9."""
    _stop({**ONE_BAND, label: "refused"}, r"S5.*D-19")
    _stop({**ONE_BAND, label: "crashed"}, r"S5.*D-19")


def test_a_cell_inside_a_band_is_listed_and_not_walled_even_at_small_d() -> None:
    failing = {**TWO_BANDS, WALLED[0]: "refused"}
    bands = _bands(failing)
    inband, _, walled = oper_sets.check_group(_list("points"), _readings(failing), bands)
    assert inband == (WALLED[0],)
    assert walled == ()


def test_the_text_and_the_cli_report_the_walled_cells(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    failing = {**ONE_BAND, WALLED[0]: "refused", WALLED[1]: "refused"}
    text = oper_sets.fine_bands_text(_bands(failing), (), 7, WALLED[:2])
    assert "walled: 2 refused above d / pitch 9 at 0.45 < d < 0.9 (F15, L37)" in text
    _write(tmp_path / "walled", _readings(failing))
    assert oper_sets.main(["fine-bands", "--from", str(tmp_path / "walled")]) == 0
    assert "walled: 2 refused above d / pitch 9" in capsys.readouterr().out


# --- the committed records (run 41635270998) -----------------------------------------------------

RECORDS = REPO_ROOT / "bench" / "results" / "phase-08" / "fine-bands-41635270998"


def test_the_band_walk_records_give_one_band_and_the_walled_cells() -> None:
    """F5 over the committed linux/amd64 records: one band, d 1.55 to 3.35 mm, the 315 in-band
    check refusals, and the 40 cells at d 0.5 to 0.85 mm that F15 hands to the wall."""
    readings = oper_sets.read_readings(RECORDS)
    points = _list("points")
    bands = oper_sets.fine_bands(points, readings)
    assert [(b.low, b.high) for b in bands] == [(Fraction("1.55"), Fraction("3.35"))]
    assert len(bands[0].refused) == 175
    inband, ok_outside, walled = oper_sets.check_group(points, readings, bands)
    assert (len(inband), ok_outside, len(walled)) == (315, 1158, 40)
    assert {_q(label) for label in walled} == {Fraction("12.5"), Fraction(16), Fraction(20)}
    assert {label.split("-")[1] for label in walled} == {
        f"d{d}" for d in ("0.5", "0.55", "0.6", "0.65", "0.7", "0.75", "0.8", "0.85")}
    assert all(label.endswith(("-right", "-left")) and "-n90-" in label for label in walled)
    assert oper_sets.fine_bands_block(bands, "x").count('Fraction("') == 2


def test_the_shipped_bands_are_the_block_the_records_write() -> None:
    """D-15: `calc.thread` holds exactly the block `fine-bands --from` prints for the committed
    run, never a typed edge, and its bands are what `uses_fine_sweep` reads."""
    bands = oper_sets.fine_bands(_list("points"), oper_sets.read_readings(RECORDS))
    block = oper_sets.fine_bands_block(bands, str(RECORDS.relative_to(REPO_ROOT)))
    source = (REPO_ROOT / "src" / "screw" / "calc" / "thread.py").read_text()
    assert source.count("# BEGIN fine-bands") == 1
    assert block in source
    assert tuple((b.low, b.high) for b in bands) == thread.FINE_BOLT_BANDS


def _write(directory: Path, readings: list[Raw]) -> None:
    (directory / "oper-fine-bands-1-1").mkdir(parents=True)
    lines = [json.dumps({"type": "header", "GITHUB_RUN_ID": "1"})]
    lines += [json.dumps({"type": "reading", **r}) for r in readings]
    (directory / "oper-fine-bands-1-1" / "oper-fine-bands-1-1.jsonl").write_text(
        "\n".join(lines) + "\n")


def test_fine_bands_exits_3_on_a_stop_and_prints_the_block_otherwise(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(tmp_path / "good", _readings({**TWO_BANDS, CHECK_IN: "refused"}))
    assert oper_sets.main(["fine-bands", "--from", str(tmp_path / "good")]) == 0
    out = capsys.readouterr().out
    assert "band-1: d in (0.45, 0.9)" in out
    assert "check: 1 refused inside a band (check-d3-q9-n3-right)" in out
    assert out.count("# BEGIN fine-bands") == 1
    assert 'Fraction("3.35")' in out
    assert out.rstrip().endswith("# END fine-bands")
    _write(tmp_path / "bad", _readings({**TWO_BANDS, "check-d3.4-q9-n3-right": "refused"}))
    assert oper_sets.main(["fine-bands", "--from", str(tmp_path / "bad")]) == 3
    assert "oper_sets: stop (F5): " in capsys.readouterr().err


def test_the_judges_walled_edges_and_wall_are_the_small_d_wall_of_calc_thread() -> None:
    """F15 and L37: the judge's two edges and its 9 are the rulings, and `calc.thread` carries the
    same three numbers (plan 08-12), so the cells the judge calls walled are the ones the model
    refuses."""
    assert oper_sets.SMALL_D == thread.SMALL_BOLT_D_MM == (Fraction("0.45"), Fraction("0.9"))
    assert oper_sets.SMALL_WALL == thread.SMALL_BOLT_D_PER_PITCH == 9


def test_the_walled_cells_are_the_ones_the_parameter_model_refuses() -> None:
    """Every cell the judge lists as walled is refused by `pitch_too_fine_refusal` under the
    production walls, and the cells outside the interval are not."""
    readings = oper_sets.read_readings(RECORDS)
    points = _list("points")
    bands = oper_sets.fine_bands(points, readings)
    _, _, walled = oper_sets.check_group(points, readings, bands)
    by_label = {str(p["label"]): _params(p) for p in points}
    assert len(walled) == 40
    for label in walled:
        params = by_label[label]
        assert thread.pitch_too_fine_refusal("bolt", float(params["d"]), float(params["pitch"]))


# --- F6: the proof walk `fine-proof` (08-06) ----------------------------------------------------

PROOF = REPO_ROOT / "bench" / "points" / f"{oper_sets.PROOF_WALK}.json"
EXPLORE_RUN = "bench/results/phase-07/explore-40646117094"
BANDS_RUN = "bench/results/phase-08/fine-bands-41635270998"
NUT_ROW_IDS = ("iso4032:M5", "iso4032:M8", "iso4032:M10", "iso4032:M12", "iso4032:M14",
               "iso4032:M16", "iso4032:M18", "iso4032:M20")
FAILED = ("refused", "crashed")


@functools.cache
def _proof() -> dict[str, object]:
    found: dict[str, object] = json.loads(PROOF.read_text())
    return found


def _plist(key: str) -> list[Raw]:
    found = _proof()[key]
    assert isinstance(found, list)
    return found


def _pcells(prefix: str) -> list[Raw]:
    return [c for c in (*_plist("points"), *_plist("dropped"))
            if str(c["label"]).startswith(prefix)]


def _fine(cell: Raw) -> bool:
    params = _params(cell)
    return thread.uses_fine_sweep(str(cell["kind"]), params["d"], params["pitch"])


def _hands(stem: str) -> list[str]:
    return [f"{stem}-right", f"{stem}-left"]


def test_the_proof_header_names_the_explore_run_the_band_run_and_the_rule() -> None:
    proof = _proof()
    assert proof["set"] == "fine-proof"
    assert proof["reps"] == 1
    assert proof["sources"] == [f"explore={EXPLORE_RUN}", f"bands={BANDS_RUN}"]
    assert str(proof["rule"]).startswith("08-SWEEP-PROTOCOL.md F6")
    assert oper_sets.envelope_of(proof["envelope"]) == oper_sets.shipped_envelope()


def test_the_proof_file_is_what_the_generator_writes_from_its_sources() -> None:
    text = PROOF.read_text()
    assert oper_sets._regenerate_runs2(oper_sets.PROOF_WALK, text) == text
    assert oper.load_set(oper_sets.PROOF_WALK).reps == 1


def test_a_proof_copy_with_one_point_removed_is_not_what_the_generator_writes(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    document = json.loads(PROOF.read_text())
    del document["points"][0]
    (tmp_path / PROOF.name).write_text(json.dumps(document, indent=1) + "\n")
    for name in ("explore", oper_sets.BAND_WALK):  # the files the proof walk is drawn from
        (tmp_path / f"{name}.json").write_text((PROOF.parent / f"{name}.json").read_text())
    monkeypatch.setattr(oper_sets, "POINTS_DIR", tmp_path)
    failure = oper_sets._check_runs2()
    assert failure is not None
    assert PROOF.name in failure


def test_the_proof_walk_is_sharded_by_r6() -> None:
    sizes = _proof()["shard_sizes"]
    assert isinstance(sizes, list)
    assert sum(sizes) == len(_plist("points"))
    assert _proof()["shards"] == len(sizes) > 1


def test_every_proof_cell_is_a_point_or_dropped_once_at_a_known_artifact() -> None:
    cells = [*_plist("points"), *_plist("dropped")]
    labels = [str(c["label"]) for c in cells]
    assert len(labels) == len(set(labels))
    assert {p["artifact"] for p in _plist("points")} <= {"step", "stl-preview", "stl-fine"}
    assert all(label.startswith("proof-") for label in labels)


# F6 grid a: in-band bolts

def test_grid_a_is_every_inband_size_of_the_0_05_grid_by_q_n_and_hand() -> None:
    """Counted in the test: the band's open interval on the 0.05 grid by decimal arithmetic."""
    ((low, high),) = thread.FINE_BOLT_BANDS
    sizes = [d for d in _decimals("0.05", "4", "0.05") if low < Fraction(d) < high]
    assert (sizes[0], sizes[-1], len(sizes)) == ("1.6", "3.3", 35)
    expected = {f"proof-band-d{d}-q{q}-n{n}-{hand}" for d in sizes
                for q in ("6.5", "7", "8", "10", "14", "20") for n in (3, 30, 60, 90)
                for hand in ("right", "left")}
    assert len(expected) == 35 * 6 * 4 * 2 == 1680
    assert {str(c["label"]) for c in _pcells("proof-band-")} == expected


def test_every_grid_a_cell_is_on_the_fine_sweep() -> None:
    """From the committed file and not from the grid spec: a grid drawn over the closed interval
    puts the band's edges in and fails here."""
    cells = _pcells("proof-band-")
    assert cells
    edges = {edge for band in thread.FINE_BOLT_BANDS for edge in band}
    for cell in cells:
        assert _fine(cell), cell["label"]
        assert Fraction(repr(_params(cell)["d"])) not in edges, cell["label"]


def test_a_grid_a_cell_is_a_full_thread_of_n_turns_at_a_pitch_rounded_up() -> None:
    for cell in _pcells("proof-band-"):
        match = re.match(r"^proof-band-d([0-9.]+)-q([0-9.]+)-n(\d+)-(right|left)$",
                         str(cell["label"]))
        assert match, cell["label"]
        params = _params(cell)
        assert params == oper_sets._band_params(match[1], match[2], int(match[3]),
                                                match[4] == "left"), cell["label"]
        assert _ratio(params) <= Fraction(match[2]), cell["label"]
        assert _ratio(params) > 6, cell["label"]


# F6 grid b: the examples and the refusals

def test_grid_b_holds_the_debts_two_examples_in_both_hands() -> None:
    by_label = {str(c["label"]): _params(c) for c in _pcells("proof-debt-")}
    assert sorted(by_label) == sorted([*_hands("proof-debt-d3-p0.35-L25"),
                                       *_hands("proof-debt-d2.5-p0.35-L30")])
    for hand in ("right", "left"):
        assert by_label[f"proof-debt-d3-p0.35-L25-{hand}"] == {
            "d": 3.0, "pitch": 0.35, "length": 25.0, "thread_length": 25.0, "s": 4.8,
            "k": 1.8, "left_hand": hand == "left"}
        assert by_label[f"proof-debt-d2.5-p0.35-L30-{hand}"] == {
            "d": 2.5, "pitch": 0.35, "length": 30.0, "thread_length": 30.0, "s": 4.0,
            "k": 1.5, "left_hand": hand == "left"}


def _failed_labels(directory: str) -> set[str]:
    return {str(r["label"]) for r in oper_sets._read(directory) if r["status"] in FAILED}


def test_grid_b_holds_every_refused_explore_bolt_on_the_fine_sweep_as_drawn() -> None:
    """Counted from the records and the explore file, with the registration's own validation."""
    failed = _failed_labels(EXPLORE_RUN)
    drawn: dict[str, Raw] = {}
    for point in oper_sets._points_of("explore"):
        if point["kind"] == "bolt" and point["label"] in failed:
            part = oper_lift.registered("bolt", _params(dict(point)))
            if thread.uses_fine_sweep("bolt", part.d, part.pitch):
                drawn.setdefault(str(point["label"]), dict(point))
    assert drawn
    found = {str(c["label"]): c for c in _pcells("proof-explore-")}
    assert set(found) == {f"proof-explore-{label}" for label in drawn}
    for label, point in drawn.items():
        assert _params(found[f"proof-explore-{label}"]) == _params(point), label
    # the 84 mm (240 turns) bolts at d 3, d / pitch 8.57, are past the 90-turn cap of the model
    for hand in ("right", "left"):
        cell = found[f"proof-explore-bolt-d3-p0.35-n240-{hand}"]
        assert cell in _plist("dropped")
        assert cell["error"] == "turn_cap"


def test_grid_b_drops_an_explore_bolt_the_runner_would_refuse_with_the_wall_error() -> None:
    """d 3 at pitch 0.1 is d / pitch 30, past the bolt wall of 20: the runner's validator answers
    `bad point` (exit 2) to it, so it is no point (F14), and it is not skipped either."""
    for label in ("bolt-d3-p0.1-n3-right", "bolt-d3-p0.1-n30-left", "bolt-d3-p0.1-n30-right"):
        (cell,) = _pcells(f"proof-explore-{label}")
        assert cell in _plist("dropped"), label
        assert cell["error"] == "pitch_too_fine", label


def test_grid_b_holds_every_inband_refusal_of_the_band_walk_as_drawn() -> None:
    failed = _failed_labels(BANDS_RUN)
    expected = {str(p["label"]): p for p in _list("points") if p["label"] in failed
                and thread.uses_fine_sweep("bolt", _params(p)["d"], _params(p)["pitch"])}
    assert len(expected) == 490
    found = {str(c["label"]): c for c in _pcells("proof-walk-")}
    assert set(found) == {f"proof-walk-{label}" for label in expected}
    for label, point in expected.items():
        assert _params(found[f"proof-walk-{label}"]) == _params(point), label


# F6 grid c: the denser nut grid

def test_grid_c_is_r31s_four_nut_forms_on_the_denser_grid() -> None:
    sizes = sorted({*oper_sets.PITCH_NUT_D, "2.1", "2.3"}, key=Decimal)
    assert len(sizes) == 46
    assert oper_sets.PITCH_NUT_D[:3] == ("0.5", "0.6", "0.7")
    qs = ("5.5", "6", "6.25", "6.5", "6.75", "7", "7.25", "7.5", "7.75", "8")
    expected = {f"proof-nut-{form}-d{d}-q{q}-{hand}" for form in ("base", "s4", "c0", "m1")
                for d in sizes for q in qs for hand in ("right", "left")}
    assert len(expected) == 4 * 46 * 10 * 2 == 3680
    assert {str(c["label"]) for c in _pcells("proof-nut-")} == expected
    for cell in _pcells("proof-nut-"):
        match = re.match(r"^proof-nut-(\w+)-d([0-9.]+)-q([0-9.]+)-(right|left)$",
                         str(cell["label"]))
        assert match, cell["label"]
        params = _params(cell)
        assert params == oper_sets._pitch_params("nut", match[1], match[2], Fraction(match[3]),
                                                 match[4] == "left"), cell["label"]
        assert _ratio(params) <= Fraction(match[3]), cell["label"]


def test_the_six_island_cells_at_d_2_2_and_q_7_are_points() -> None:
    points = {str(p["label"]) for p in _plist("points")}
    island = [f"proof-nut-{form}-d2.2-q7-{hand}" for form in ("base", "s4", "m1")
              for hand in ("right", "left")]
    assert all(label in points for label in island)
    assert sum(1 for label in points if label.startswith("proof-nut-") and "-d2.2-q7-" in label
               and "-c0-" not in label) == 6


# F6 grid d: the moved catalogue rows

def test_grid_d_is_the_eight_nut_rows_the_fine_sweep_moves_in_both_hands() -> None:
    expected = {f"proof-row-{row}-{hand}" for row in NUT_ROW_IDS for hand in ("right", "left")}
    cells = _pcells("proof-row-")
    assert {str(c["label"]) for c in cells} == expected
    assert len(cells) == 16
    for cell in cells:
        assert cell["kind"] == "nut", cell["label"]
        assert _fine(cell), cell["label"]


# the whole file

def test_no_proof_bolt_keeps_the_shipped_sweep_and_none_is_outside_the_bands() -> None:
    bolts = [c for c in (*_plist("points"), *_plist("dropped")) if c["kind"] == "bolt"]
    assert bolts
    assert all(_fine(c) for c in bolts)
    assert not [c for c in bolts if str(c["label"]).startswith(("proof-out-", "proof-large-"))]


def test_every_proof_point_is_one_the_runner_accepts_at_the_first_artifact_that_admits_it() -> None:
    envelope = oper_sets.envelope_of(_proof()["envelope"])
    for point in _plist("points"):
        kind, params = str(point["kind"]), _params(point)
        part = oper_lift.validate(kind, params)  # bench/oper_child.py's own call: walls enforced
        assert point["artifact"] == oper_sets._first_admitted(part, envelope, cost.BUDGET), (
            point["label"])


def test_every_dropped_proof_cell_is_refused_by_the_model_or_admitted_at_no_artifact() -> None:
    envelope = oper_sets.envelope_of(_proof()["envelope"])
    for cell in _plist("dropped"):
        kind, params = str(cell["kind"]), _params(cell)
        error = oper_sets._runner_refusal(kind, params)
        if error is not None:
            assert cell["error"] == error, cell["label"]
            continue
        assert cell["error"] == "over_budget", cell["label"]
        part = oper_lift.drawn(kind, params)
        assert oper_sets._first_admitted(part, envelope, cost.BUDGET) is None, cell["label"]


def test_the_runner_refusal_is_the_models_with_the_pitch_wall_back_in() -> None:
    wall = {"d": 3.0, "pitch": 0.1, "length": 3.0, "thread_length": 3.0, "s": 4.8, "k": 1.8}
    assert oper_sets._model_refusal("bolt", wall) is None
    assert oper_sets._runner_refusal("bolt", wall) == "pitch_too_fine"
    ninety = {**wall, "pitch": 0.35, "length": 31.5, "thread_length": 31.5}
    assert oper_sets._runner_refusal("bolt", ninety) is None
    assert oper_sets._runner_refusal("bolt", {**ninety, "length": 36.75,
                                              "thread_length": 36.75}) == "turn_cap"


def test_refused_on_fine_takes_the_refused_fine_swept_bolts_of_a_set_in_label_order(
        tmp_path: Path) -> None:
    points = _list("points")
    fine = [str(p["label"]) for p in points if thread.uses_fine_sweep(
        "bolt", _params(p)["d"], _params(p)["pitch"])]
    outside = next(str(p["label"]) for p in points if str(p["label"]).startswith("check-")
                   and not thread.uses_fine_sweep("bolt", _params(p)["d"], _params(p)["pitch"]))
    refused = {fine[40]: "refused", fine[7]: "crashed", fine[90]: "refused", outside: "refused"}
    readings = [{**p, "rep": 1, "status": refused.get(str(p["label"]), "ok")} for p in points]
    directory = tmp_path / "records"
    directory.mkdir()
    _write(directory, readings)
    found = oper_sets._refused_on_fine(oper_sets.BAND_WALK, str(directory))
    assert [str(p["label"]) for p in found] == sorted(fine[i] for i in (40, 7, 90))
    assert all(p in points for p in found)


def test_the_proof_walk_subcommand_writes_the_committed_file(tmp_path: Path) -> None:
    out = tmp_path / "fine-proof.json"
    assert oper_sets.main(["proof-walk", "--explore", EXPLORE_RUN, "--bands", BANDS_RUN,
                           "--out", str(out)]) == 0
    assert out.read_text() == PROOF.read_text()


# --- F9: the cost re-sweep and the spread (08-06) -----------------------------------------------

COST = REPO_ROOT / "bench" / "points" / f"{oper_sets.FINE_COST}.json"
SPREAD = REPO_ROOT / "bench" / "points" / f"{oper_sets.FINE_SPREAD}.json"


def _doc(path: Path) -> dict[str, object]:
    found: dict[str, object] = json.loads(path.read_text())
    return found


def _entries(path: Path, key: str) -> list[Raw]:
    found = _doc(path)[key]
    assert isinstance(found, list)
    return found


def _both(path: Path) -> list[Raw]:
    return [*_entries(path, "points"), *_entries(path, "dropped")]


@pytest.mark.parametrize(("path", "name", "reps"),
                         [(COST, "fine-cost", 1), (SPREAD, "fine-spread", 5)])
def test_the_cost_headers_name_the_explore_run_the_shipped_envelope_and_f9(
        path: Path, name: str, reps: int) -> None:
    document = _doc(path)
    assert document["set"] == name
    assert document["reps"] == reps
    assert document["sources"] == [f"explore={EXPLORE_RUN}"]
    assert str(document["rule"]).startswith("08-SWEEP-PROTOCOL.md F9")
    assert oper_sets.envelope_of(document["envelope"]) == oper_sets.shipped_envelope()
    sizes = document["shard_sizes"]
    assert isinstance(sizes, list)
    assert sum(sizes) == len(_entries(path, "points"))
    assert oper.load_set(name).reps == reps


@pytest.mark.parametrize("name", [oper_sets.FINE_COST, oper_sets.FINE_SPREAD])
def test_the_cost_files_are_what_the_generator_writes_from_their_sources(name: str) -> None:
    text = (REPO_ROOT / "bench" / "points" / f"{name}.json").read_text()
    assert oper_sets._regenerate_runs2(name, text) == text


def test_a_cost_copy_with_one_point_removed_is_not_what_the_generator_writes(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    document = json.loads(COST.read_text())
    del document["points"][0]
    (tmp_path / COST.name).write_text(json.dumps(document, indent=1) + "\n")
    (tmp_path / "explore.json").write_text((COST.parent / "explore.json").read_text())
    monkeypatch.setattr(oper_sets, "POINTS_DIR", tmp_path)
    failure = oper_sets._check_runs2()
    assert failure is not None
    assert COST.name in failure


@pytest.mark.parametrize("path", [COST, SPREAD])
def test_no_point_of_a_cost_file_is_off_the_fine_sweep(path: Path) -> None:
    """D-05: only the parts above the thresholds are re-swept."""
    points = _entries(path, "points")
    assert points
    for point in points:
        assert _fine(point), point["label"]


@pytest.mark.parametrize("path", [COST, SPREAD])
def test_every_cost_point_is_one_the_runner_accepts_at_an_artifact_the_model_admits(
        path: Path) -> None:
    envelope = oper_sets.envelope_of(_doc(path)["envelope"])
    for point in _entries(path, "points"):
        part = oper_lift.validate(str(point["kind"]), _params(point))
        artifact = next(a for a in cost.ARTIFACTS if a == point["artifact"])
        assert oper_sets.admits(part, artifact, envelope, cost.BUDGET), point["label"]


@pytest.mark.parametrize("path", [COST, SPREAD])
def test_a_cost_part_is_at_every_artifact_it_is_admitted_at_and_dropped_at_the_rest(
        path: Path) -> None:
    envelope = oper_sets.envelope_of(_doc(path)["envelope"])
    at: dict[str, set[str]] = {}
    for point in _entries(path, "points"):
        at.setdefault(str(point["label"]), set()).add(str(point["artifact"]))
    dropped = {str(c["label"]): c for c in _entries(path, "dropped")}
    for label in {*at, *dropped}:
        cell = next(c for c in _both(path) if c["label"] == label)
        kind, params = str(cell["kind"]), _params(cell)
        if (error := oper_sets._runner_refusal(kind, params)) is not None:
            assert label not in at, label
            assert dropped[label]["error"] == error
            assert dropped[label]["artifacts"] == list(cost.ARTIFACTS)
            continue
        part = oper_lift.drawn(kind, params)
        admitted = {a for a in cost.ARTIFACTS if oper_sets.admits(part, a, envelope, cost.BUDGET)}
        assert at.get(label, set()) == admitted, label
        if admitted == set(cost.ARTIFACTS):
            assert label not in dropped, label
        else:
            assert dropped[label]["error"] == "over_budget", label
            artifacts = dropped[label]["artifacts"]
            assert isinstance(artifacts, list)
            assert set(artifacts) == set(cost.ARTIFACTS) - admitted, label


def test_fine_cost_holds_the_explore_parts_the_rows_the_inband_bolts_and_the_nuts() -> None:
    explore: set[str] = set()
    for point in oper_sets._points_of("explore"):
        part = oper_lift.registered(str(point["kind"]), _params(dict(point)))
        if thread.uses_fine_sweep(str(point["kind"]), part.d, part.pitch):
            explore.add(f"fcost-explore-{point['label']}")
    assert len(explore) == 87
    labels = {str(c["label"]) for c in _both(COST)}
    assert {label for label in labels if label.startswith("fcost-explore-")} == explore
    assert {label for label in labels if label.startswith("fcost-row-")} == {
        f"fcost-row-{row}" for row in NUT_ROW_IDS}
    bands = {f"fcost-band-d{d}-q{q}-n{n}" for d in ("1.6", "2.5", "3", "3.3")
             for q in ("7", "8", "12.5", "20") for n in (3, 30, 90)}
    assert len(bands) == 48  # d 0.5 and 0.8 lie outside the one band and are not drawn
    assert {label for label in labels if label.startswith("fcost-band-")} == bands
    nuts = {f"fcost-nut-{form}-d{d}-q{q}" for form in ("base", "s4")
            for d in ("0.8", "2.2", "5", "10", "20") for q in ("6.25", "7", "8")}
    assert len(nuts) == 30
    assert {label for label in labels if label.startswith("fcost-nut-")} == nuts
    assert len(labels) == 87 + 8 + 48 + 30


def test_fine_cost_parts_are_right_handed_full_thread_bolts_and_the_catalogue_nuts() -> None:
    for cell in _both(COST):
        label, params = str(cell["label"]), _params(cell)
        if label.startswith(("fcost-band-", "fcost-nut-", "fcost-row-")):
            assert params["left_hand"] is False, label
        match = re.match(r"^fcost-band-d([0-9.]+)-q([0-9.]+)-n(\d+)$", label)
        if match:
            assert params == oper_sets._band_params(match[1], match[2], int(match[3]), False)
        match = re.match(r"^fcost-nut-(\w+)-d([0-9.]+)-q([0-9.]+)$", label)
        if match:
            assert params == oper_sets._pitch_params("nut", match[1], match[2],
                                                     Fraction(match[3]), False)


def test_fine_spread_is_the_eight_moved_nut_rows_at_five_repetitions() -> None:
    assert {str(c["label"]) for c in _both(SPREAD)} == {f"fspread-row-{row}" for row in NUT_ROW_IDS}
    assert {p["label"] for p in _entries(SPREAD, "points")} == {
        f"fspread-row-{row}" for row in NUT_ROW_IDS}
    assert _doc(SPREAD)["reps"] == 5
    for cell in _both(SPREAD):
        assert _params(cell)["left_hand"] is False, cell["label"]


def test_a_part_off_the_fine_sweep_cannot_enter_a_cost_set() -> None:
    envelope = oper_sets.shipped_envelope()
    off = ("fcost-off", "nut", oper_sets._pitch_params("nut", "base", "5", Fraction(6), False))
    with pytest.raises(ValueError, match="not on the fine sweep"):
        oper_sets._fine_parts_set(oper_sets._Set("x", reps=1, shards=1, notes=[]), [off],
                                  envelope, cost.BUDGET)


def test_the_fine_cost_sets_subcommand_writes_both_committed_files(tmp_path: Path) -> None:
    assert oper_sets.main(["fine-cost-sets", "--explore", EXPLORE_RUN,
                           "--cost-out", str(tmp_path / "c.json"),
                           "--spread-out", str(tmp_path / "s.json")]) == 0
    assert (tmp_path / "c.json").read_text() == COST.read_text()
    assert (tmp_path / "s.json").read_text() == SPREAD.read_text()


# --- F7 and F8: the proof walk's judgement and the turn ceilings -------------------------------


def _proof_points() -> list[Raw]:
    return [dict(p) for p in oper_sets._points_of(oper_sets.PROOF_WALK)]


def _proof_readings(failing: dict[str, str]) -> list[Raw]:
    """One reading per proof-walk point: `failing[label]` for the labels named, else ok."""
    points = _proof_points()
    assert set(failing) <= {str(p["label"]) for p in points}, set(failing)
    return [{**p, "rep": 1, "status": failing.get(str(p["label"]), "ok")} for p in points]


def _ceilings(failing: dict[str, str]) -> tuple[oper_sets.FineCeiling, ...]:
    return oper_sets.fine_ceilings(_proof_points(), _proof_readings(failing))


def _ceiling_stop(failing: dict[str, str], rule: str, match: str) -> None:
    with pytest.raises(ProtocolStop, match=match) as raised:
        _ceilings(failing)
    assert raised.value.rule == rule


def _turns(n: int, d: str = "2", q: str = "7", hand: str = "right") -> str:
    return f"proof-band-d{d}-q{q}-n{n}-{hand}"


DEBT_3 = "proof-debt-d3-p0.35-L25-right"
SHIPPED_NUT = "proof-nut-base-d5-q6-right"  # d / pitch just under 6: the shipped sweep
FINE_NUT = "proof-nut-base-d5-q7-right"


def test_the_proof_walk_without_a_refusal_gives_no_ceiling_and_an_empty_block() -> None:
    ceilings = _ceilings({})
    assert ceilings == ()
    assert ("FINE_TURN_CEILINGS: tuple[tuple[str, int], ...] = ()\n# END turn-ceilings\n"
            in oper_sets.fine_ceilings_block(ceilings, "somewhere"))


def test_f_is_the_smallest_refused_turns_of_the_band_and_n_one_margin_under_it() -> None:
    (ceiling,) = _ceilings({_turns(90): "refused", _turns(60): "refused"})
    assert (ceiling.region, ceiling.f, ceiling.label, ceiling.n) == (
        "band-1", Fraction(60), "proof-band-d2-q7-n60-right", 48)
    assert [turns for _, turns, _ in ceiling.refused] == [Fraction(60), Fraction(90)]


def test_f_is_exact_not_a_float_quotient() -> None:
    (ceiling,) = _ceilings({DEBT_3: "refused"})
    assert ceiling.f == Fraction("25") / Fraction("0.35") == Fraction(500, 7)
    assert ceiling.n == 57  # 71.43 / 1.25 = 57.14


def test_a_crashed_reading_counts_as_a_refusal() -> None:
    assert _ceilings({_turns(30): "crashed"})[0].n == 24


def test_n_is_the_whole_number_at_or_below_f_over_1_25() -> None:
    """A bolt at exactly N turns is admitted by the guard 08-09 builds, so N never rounds up."""
    assert oper_sets.turn_ceiling(Fraction(125, 2)) == 50
    assert oper_sets.turn_ceiling(Fraction(125, 2) - Fraction(1, 10**9)) == 49


def test_ties_are_set_by_the_first_label() -> None:
    (ceiling,) = _ceilings({_turns(30, "2.05"): "refused", _turns(30, "2"): "refused"})
    assert ceiling.label == "proof-band-d2-q7-n30-right"


@pytest.fixture
def two_bands(monkeypatch: pytest.MonkeyPatch) -> None:
    """The proof walk's one band cut at d 2.5 into two, so the walk has a refusal to put in each."""
    monkeypatch.setattr(thread, "FINE_BOLT_BANDS",
                        ((Fraction("1.55"), Fraction("2.5")), (Fraction("2.5"), Fraction("3.35"))))


@pytest.mark.usefixtures("two_bands")
def test_regions_are_the_bands_in_ascending_order_and_the_block_lists_band_1_first() -> None:
    ceilings = _ceilings({_turns(90, "3"): "refused", _turns(60, "2"): "refused"})
    assert [(c.region, c.n) for c in ceilings] == [("band-1", 48), ("band-2", 72)]
    block = oper_sets.fine_ceilings_block(ceilings, "src")
    assert block.index('("band-1", 48),') < block.index('("band-2", 72),')


@pytest.mark.usefixtures("two_bands")
def test_a_band_with_no_refusal_has_no_ceiling() -> None:
    ceilings = _ceilings({_turns(60, "3"): "refused"})
    assert [c.region for c in ceilings] == ["band-2"]
    assert '"band-1"' not in oper_sets.fine_ceilings_block(ceilings, "src")


def test_the_block_is_the_markers_the_source_and_one_line_per_ceiling() -> None:
    block = oper_sets.fine_ceilings_block(_ceilings({_turns(60): "refused"}), "bench/results/x")
    assert block == (
        "# BEGIN turn-ceilings: written by `python -m bench.oper_sets fine-ceilings --from\n"
        "# bench/results/x`; not edited by hand.\n"
        "FINE_TURN_CEILINGS: tuple[tuple[str, int], ...] = (\n"
        '    ("band-1", 48),\n'
        ")\n"
        "# END turn-ceilings\n")


def test_the_text_names_f_exact_and_float_the_label_n_and_the_spans() -> None:
    text = oper_sets.fine_ceilings_text(_ceilings({DEBT_3: "refused", _turns(90): "crashed"}))
    assert "band-1: F = 500/7 (71.42857142857143) at proof-debt-d3-p0.35-L25-right;" in text
    assert "F / 1.25 = 57.142857142857146; N = 57" in text
    assert "2 refused or crashed" in text
    assert "turns 71.42857142857143 to 90.0" in text


def test_the_text_says_when_no_band_has_a_ceiling() -> None:
    assert "no ceiling" in oper_sets.fine_ceilings_text(())


def test_a_bolt_the_shipped_sweep_keeps_refused_is_a_stop_not_a_ceiling(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(thread, "FINE_BOLT_BANDS", ((Fraction("9"), Fraction("10")),))
    _ceiling_stop({_turns(60): "refused"}, "F7", "S6: proof-band-d2-q7-n60-right")


def test_a_shipped_sweep_nut_refused_is_a_stop() -> None:
    _ceiling_stop({SHIPPED_NUT: "refused"}, "F7", f"S6: {SHIPPED_NUT}")


def test_a_fine_sweep_nut_refused_is_a_stop_and_no_guard_for_nuts() -> None:
    _ceiling_stop({FINE_NUT: "crashed"}, "F7", f"S7: {FINE_NUT}")


def test_a_ceiling_below_3_turns_is_a_stop() -> None:
    _ceiling_stop({_turns(3): "refused"}, "F8", "S8: .* N 2")


def test_the_edge_of_s8_is_a_ceiling_of_exactly_3() -> None:
    assert oper_sets.turn_ceiling(Fraction("3.75")) == 3
    assert oper_sets.turn_ceiling(Fraction("3.7499")) == 2


@pytest.mark.parametrize("status", ["killed", "capped", "no_cgroup", "missing", "timeout"])
def test_a_status_other_than_ok_refused_or_crashed_is_a_stop(status: str) -> None:
    _ceiling_stop({_turns(60): status}, "F7", f"S1: proof-band-d2-q7-n60-right is {status}")


def test_a_missing_a_doubled_or_a_foreign_reading_is_a_stop() -> None:
    points, readings = _proof_points(), _proof_readings({})
    with pytest.raises(ProtocolStop, match="S1: 1 points of the walk have no reading") as raised:
        oper_sets.fine_ceilings(points, readings[1:])
    assert raised.value.rule == "F7"
    with pytest.raises(ProtocolStop, match=r"S1: .* was read twice"):
        oper_sets.fine_ceilings(points, [*readings, readings[0]])
    with pytest.raises(ProtocolStop, match=r"S1: nowhere at .* is not a point"):
        oper_sets.fine_ceilings(points, [*readings, {**readings[0], "label": "nowhere"}])


def test_fine_ceilings_exits_3_on_a_stop_and_prints_the_block_otherwise(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(tmp_path / "good", _proof_readings({_turns(60): "refused"}))
    assert oper_sets.main(["fine-ceilings", "--from", str(tmp_path / "good")]) == 0
    out = capsys.readouterr().out
    assert "band-1: F = 60 (60.0) at proof-band-d2-q7-n60-right; F / 1.25 = 48.0; N = 48" in out
    assert out.count("# BEGIN turn-ceilings") == 1
    assert '    ("band-1", 48),' in out
    assert out.rstrip().endswith("# END turn-ceilings")
    _write(tmp_path / "bad", _proof_readings({FINE_NUT: "refused"}))
    assert oper_sets.main(["fine-ceilings", "--from", str(tmp_path / "bad")]) == 3
    assert "oper_sets: stop (F7): S7: " in capsys.readouterr().err
    _write(tmp_path / "small", _proof_readings({_turns(3): "refused"}))
    assert oper_sets.main(["fine-ceilings", "--from", str(tmp_path / "small")]) == 3
    assert "oper_sets: stop (F8): S8: " in capsys.readouterr().err


def test_the_regions_are_the_shipped_bands_and_a_fine_bolt_always_has_one() -> None:
    assert oper_sets._region(Fraction("2")) == "band-1"
    assert oper_sets._region(Fraction("1.55")) is None  # a band's edge is excluded
    assert oper_sets._region(Fraction("5")) is None


PROOF_RECORDS = REPO_ROOT / "bench" / "results" / "phase-08" / "fine-proof-41684315321"
PRINTED_CEILINGS = ()  # fine-ceilings --from PROOF_RECORDS: the fine sweep refused nothing


def test_the_proof_walk_records_give_the_ceilings_08_09_ships() -> None:
    """Run 41684315321 read all 5790 points ok, so F8 has no ceiling to print (D-06: no refusal,
    no ceiling). 08-09 replaces this with the `calc.thread` block check."""
    readings = oper_sets.read_readings(PROOF_RECORDS)
    assert len(readings) == len(_proof_points()) == 5790
    ceilings = oper_sets.fine_ceilings(_proof_points(), readings)
    assert ceilings == PRINTED_CEILINGS
    block = oper_sets.fine_ceilings_block(ceilings, f"bench/results/phase-08/{PROOF_RECORDS.name}")
    assert "FINE_TURN_CEILINGS: tuple[tuple[str, int], ...] = ()\n" in block
