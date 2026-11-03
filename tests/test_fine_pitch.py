"""The fine-pitch walls (L25, 07 R31): a part whose exact d / pitch is past its kind's wall is a 422
`pitch_too_fine` naming d and pitch, on the API and on the CLI, before any build.

The twenty in-wall parts the kernel refused in explore run 40646117094 are the reason for the wall
(docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md); none of the catalogue rows
is refused by it, and a d / pitch typed as exactly the wall is admitted.
"""

from __future__ import annotations

import functools
import json
import math
import re
from collections.abc import Iterator
from fractions import Fraction
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from screw import cli
from screw.app import app, build_backend
from screw.calc import thread
from screw.calc.thread import (
    MAX_BOLT_D_PER_PITCH,
    MAX_NUT_D_PER_PITCH,
    SMALL_BOLT_D_MM,
    SMALL_BOLT_D_PER_PITCH,
    pitch_too_fine_refusal,
)
from screw.params import KINDS, BoltParams, FastenerParams, NutParams
from screw.tables.presets import catalogue, expand, expand_nut, nut_catalogue

REPO_ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)
type Params = dict[str, float | bool]

# The twenty explore points of run 40646117094 that the L20 walls admitted and the kernel refused
# with BuildError at every artifact, as the in-wall debt item lists them.
IN_WALL = (
    "bolt-d3-p0.1-n3-right", "bolt-d3-p0.1-n30-left", "bolt-d3-p0.1-n30-right",
    "bolt-d100-p0.1-n3-right", "bolt-d100-p0.1-n30-right", "bolt-d100-p0.35-n3-right",
    "bolt-d100-p0.35-n30-right",
    "bolt-d300-p0.1-n3-left", "bolt-d300-p0.1-n3-right", "bolt-d300-p0.1-n30-left",
    "bolt-d300-p0.1-n30-right", "bolt-d300-p0.35-n3-left", "bolt-d300-p0.35-n3-right",
    "bolt-d300-p0.35-n30-left", "bolt-d300-p0.35-n30-right", "bolt-d300-p1-n3-right",
    "bolt-d300-p1-n30-right",
    "nut-d30-p0.35-m0.8d-s1.6d-c0.15-left", "nut-d30-p0.35-m0.8d-s1.6d-c0.15-right",
    "nut-d30-p0.35-m0.8d-s4d-c0.15-right",
)


@functools.cache
def _explore() -> dict[str, tuple[str, Params]]:
    raw = json.loads((REPO_ROOT / "bench" / "points" / "explore.json").read_text())
    return {p["label"]: (p["kind"], p["params"]) for p in raw["points"]}


def _argv(params: Params) -> list[str]:
    out: list[str] = []
    for key, value in params.items():
        flag = "--" + key.replace("_", "-")
        if isinstance(value, bool):
            out.append(flag if value else "--no-" + key.replace("_", "-"))
        else:
            out += [flag, repr(value)]
    return out


@pytest.fixture
def no_build() -> Iterator[list[FastenerParams]]:
    """A backend that records every part it is asked to build: the module's client runs no
    lifespan, so the pool dependency is replaced, and a refused part must never reach it."""
    seen: list[FastenerParams] = []

    async def record(p: FastenerParams, fmt: str, quality: str) -> bytes:
        seen.append(p)
        return b""

    app.dependency_overrides[build_backend] = lambda: record
    try:
        yield seen
    finally:
        app.dependency_overrides.pop(build_backend, None)


def test_the_twenty_are_distinct_explore_points() -> None:
    assert len(set(IN_WALL)) == 20
    assert set(IN_WALL) <= set(_explore())


@pytest.mark.parametrize("label", IN_WALL)
def test_each_in_wall_part_is_a_422_pitch_too_fine_on_the_api(
        label: str, no_build: list[FastenerParams]) -> None:
    kind, params = _explore()[label]
    expected = pitch_too_fine_refusal(kind, float(params["d"]), float(params["pitch"]))
    assert expected is not None
    for route in (f"/api/{kind}/info", f"/api/{kind}/model.step"):
        r = client.get(route, params=params)
        assert r.status_code == 422, (label, route)
        [detail] = r.json()["detail"]
        assert {k: v for k, v in detail.items() if k != "input"} == {
            "loc": ["query"], "type": "pitch_too_fine", "msg": expected,
            "ctx": {"fields": ["d", "pitch"]}}
    assert no_build == []


@pytest.mark.parametrize("label", IN_WALL)
def test_each_in_wall_part_exits_2_on_the_cli_with_the_apis_text(
        label: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    kind, params = _explore()[label]
    expected = pitch_too_fine_refusal(kind, float(params["d"]), float(params["pitch"]))
    out = tmp_path / "x.step"
    for argv in (["info", kind, *_argv(params)],
                 ["export", kind, *_argv(params), "-o", str(out)]):
        with pytest.raises(SystemExit) as raised:
            cli.main(argv)
        assert raised.value.code == 2
        assert capsys.readouterr().err == f"error: {expected}\n"
    assert not out.exists()


def test_no_catalogue_row_is_refused_by_the_wall() -> None:
    # B-01's counts do not move: 294 bolt rows and 14 nut rows, every one admitted.
    bolts = catalogue()
    nuts = nut_catalogue()
    assert (len(bolts), len(nuts)) == (294, 14)
    for row in bolts:
        fields = expand(row.id)
        assert fields is not None
        BoltParams.model_validate(fields)
    ratios = []
    for nut in nuts:
        fields = expand_nut(nut.id)
        assert fields is not None
        NutParams.model_validate(fields)
        ratios.append(Fraction(repr(fields["d"])) / Fraction(repr(fields["pitch"])))
    # The nut catalogue's finest row sits at the nut's wall: the ruling admits it and no finer.
    assert max(ratios) == MAX_NUT_D_PER_PITCH


@pytest.mark.parametrize(("kind", "d", "pitch", "extra"), [
    ("bolt", 20.0, 1.0, {"s": 30.0}), ("bolt", 4.7, 0.235, {"length": 2.0, "thread_length": 2.0}),
    ("bolt", 999.999, 49.99995, {"s": 1000.0}), ("nut", 8.0, 1.0, {"s": 13.0}),
    ("nut", 2.2, 0.275, {"s": 4.0}), ("nut", 0.5, 0.0625, {"s": 1.0})])
def test_a_d_per_pitch_typed_as_exactly_the_wall_is_admitted_and_one_float_finer_is_not(
        kind: str, d: float, pitch: float, extra: Params) -> None:
    # 4.7 / 0.235 is a float above 20, yet the user typed the wall exactly: the ratio is exact.
    wall = MAX_BOLT_D_PER_PITCH if kind == "bolt" else MAX_NUT_D_PER_PITCH
    assert Fraction(repr(d)) / Fraction(repr(pitch)) == wall
    assert MAX_BOLT_D_PER_PITCH < 4.7 / 0.235
    model = KINDS[kind]
    assert model.model_validate({"d": d, "pitch": pitch, **extra}).pitch == pitch
    with pytest.raises(ValidationError) as caught:
        model.model_validate({"d": d, "pitch": math.nextafter(pitch, 0.0), **extra})
    [err] = caught.value.errors()
    assert err["type"] == "pitch_too_fine"
    assert err["loc"] == ()
    assert err["ctx"] == {"fields": ["d", "pitch"]}
    assert err["msg"].startswith("d and pitch: d / pitch is ")


@pytest.mark.parametrize(("kind", "d", "pitch", "hint"), [
    ("bolt", 999.999, 1.0, "50"), ("bolt", 3.0, 0.1, "0.15"), ("bolt", 1.0, 0.03, "0.05"),
    ("bolt", 0.6, 0.04, "0.0666667"),
    ("nut", 30.0, 0.35, "3.75"), ("nut", 7.0, 0.5, "0.875"), ("nut", 999.699, 1.0, "124.963")])
def test_the_smallest_pitch_the_refusal_names_is_admitted_and_a_6_figure_step_finer_is_not(
        kind: str, d: float, pitch: float, hint: str) -> None:
    text = pitch_too_fine_refusal(kind, d, pitch)
    assert text is not None
    found = re.search(r"the smallest pitch for this d, to 6 significant figures, is (\S+)$", text)
    assert found is not None
    assert found.group(1) == hint
    smallest = float(hint)
    assert pitch_too_fine_refusal(kind, d, smallest) is None
    step = 10.0 ** (math.floor(math.log10(smallest)) - 5)
    assert pitch_too_fine_refusal(kind, d, smallest - step) is not None


def test_the_default_parts_are_inside_their_walls() -> None:
    for kind in ("bolt", "nut"):
        assert client.get(f"/api/{kind}/info").status_code == 200


def test_a_field_error_is_reported_before_the_wall() -> None:
    # After-validators run only when every field validated (pydantic), so a bad pitch names the
    # pitch and not a ratio computed from a value that was never accepted.
    r = client.get("/api/bolt/info", params={"pitch": -1})
    assert r.status_code == 422
    assert [e["loc"] for e in r.json()["detail"]] == [["query", "pitch"]]


def test_the_wall_is_the_last_model_rule_of_each_kind() -> None:
    # A part both too thin a head and too fine a pitch reports the head (the older rule) alone.
    with pytest.raises(ValidationError) as caught:
        BoltParams.model_validate({"d": 100.0, "s": 50.0})
    assert [e["type"] for e in caught.value.errors()] == ["head_too_small"]


def test_the_walls_are_the_rulings_values() -> None:
    # The bolt's from the walk's records (tests/test_oper_pitch.py rebuilds it); the nut's ruled.
    assert MAX_BOLT_D_PER_PITCH == 20
    assert MAX_NUT_D_PER_PITCH == 8
    assert isinstance(thread.MAX_BOLT_D_PER_PITCH, Fraction)
    assert isinstance(thread.MAX_NUT_D_PER_PITCH, Fraction)


# --- the small-d bolt wall (L37, owner ruling at 08 S5) ----------------------------------------

# Short threads: the 90-turn cap would refuse a d / pitch of 15 at the default length of 20 mm.
SHORT: Params = {"length": 1.0, "thread_length": 1.0}


def test_a_small_d_bolt_above_the_wall_of_9_is_a_422_naming_d_and_pitch_on_the_api(
        no_build: list[FastenerParams]) -> None:
    params: Params = {"d": 0.6, "pitch": 0.04, **SHORT}  # d / pitch 15, inside (0.45, 0.9)
    expected = pitch_too_fine_refusal("bolt", 0.6, 0.04)
    assert expected is not None
    for route in ("/api/bolt/info", "/api/bolt/model.step"):
        r = client.get(route, params=params)
        assert r.status_code == 422, route
        [detail] = r.json()["detail"]
        assert {k: v for k, v in detail.items() if k != "input"} == {
            "loc": ["query"], "type": "pitch_too_fine", "msg": expected,
            "ctx": {"fields": ["d", "pitch"]}}
    assert no_build == []


def test_a_small_d_bolt_above_the_wall_of_9_exits_2_on_the_cli_with_the_apis_text(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    params: Params = {"d": 0.6, "pitch": 0.04, **SHORT}
    expected = pitch_too_fine_refusal("bolt", 0.6, 0.04)
    out = tmp_path / "x.step"
    for argv in (["info", "bolt", *_argv(params)],
                 ["export", "bolt", *_argv(params), "-o", str(out)]):
        with pytest.raises(SystemExit) as raised:
            cli.main(argv)
        assert raised.value.code == 2
        assert capsys.readouterr().err == f"error: {expected}\n"
    assert not out.exists()


def test_the_small_d_message_names_the_wall_of_9_the_interval_and_l37() -> None:
    text = pitch_too_fine_refusal("bolt", 0.6, 0.04)
    assert text is not None
    assert text.startswith("d and pitch: d / pitch is 15 at d 0.6 and pitch 0.04, above 9, ")
    assert "0.45" in text
    assert "0.9 mm" in text
    assert "L37" in text


def test_a_bolt_at_exactly_d_over_pitch_9_in_the_interval_is_admitted_and_one_float_finer_is_not(
) -> None:
    # 0.54 / 0.06 is a float above 9, yet the user typed the wall exactly: the ratio is exact.
    assert Fraction("0.54") / Fraction("0.06") == SMALL_BOLT_D_PER_PITCH
    assert 0.54 / 0.06 > 9
    assert BoltParams.model_validate({"d": 0.54, "pitch": 0.06, **SHORT}).pitch == 0.06
    with pytest.raises(ValidationError) as caught:
        BoltParams.model_validate({"d": 0.54, "pitch": math.nextafter(0.06, 0.0), **SHORT})
    [err] = caught.value.errors()
    assert err["type"] == "pitch_too_fine"
    assert err["ctx"] == {"fields": ["d", "pitch"]}


@pytest.mark.parametrize(("d", "pitch", "extra"), [
    (0.45, 0.03, {}),              # d / pitch 15 at the interval's open low edge: wall of 20
    (0.9, 0.06, {}),               # and at its open high edge
    (3.0, 0.2, {"length": 10.0, "thread_length": 10.0}),   # d 3 at d / pitch 15
    (0.45, 0.0225, {}),            # d / pitch 20 at the low edge: the wall of 20 still holds
])
def test_a_bolt_at_the_interval_edges_or_outside_it_keeps_the_wall_of_20(
        d: float, pitch: float, extra: Params) -> None:
    params = {**SHORT, **extra}
    assert Fraction(repr(d)) / Fraction(repr(pitch)) > SMALL_BOLT_D_PER_PITCH
    assert pitch_too_fine_refusal("bolt", d, pitch) is None
    assert BoltParams.model_validate({"d": d, "pitch": pitch, **params}).pitch == pitch


def test_the_wall_of_20_still_refuses_a_bolt_at_the_interval_edge_above_20() -> None:
    text = pitch_too_fine_refusal("bolt", 0.45, 0.02)  # d / pitch 22.5
    assert text is not None
    assert "above 20" in text
    assert "L37" not in text


def test_a_nut_in_the_interval_keeps_its_wall_of_8_and_its_own_text() -> None:
    assert pitch_too_fine_refusal("nut", 0.6, 0.075) is None  # d / pitch 8
    text = pitch_too_fine_refusal("nut", 0.6, 0.0625)  # d / pitch 9.6
    assert text is not None
    assert "above 8" in text
    assert "L37" not in text


def test_the_small_d_constants_are_the_rulings_values() -> None:
    assert (Fraction("0.45"), Fraction("0.9")) == SMALL_BOLT_D_MM
    assert SMALL_BOLT_D_PER_PITCH == 9
    assert isinstance(SMALL_BOLT_D_PER_PITCH, Fraction)
