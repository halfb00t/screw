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
