"""The nut kind's solid, its two gates and its required clearance.

Covers TYPE-03, PAIR-01, D-01, D-04 and D-13.

The geometry is read from the real kernel, no mocks. A gate test plants a wrong closed form by
monkeypatching the name `screw.solid` reads it through, and carries its positive control: the
right closed form builds, one just inside `T_GATE` builds, one just outside is refused naming what
it judged. A refusal test names the field the request or the flag got wrong.
"""

from __future__ import annotations

import json
import math
import re
import struct
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import cadquery as cq
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from pydantic_core import PydanticUndefined

from screw import cli
from screw.app import app, build_backend
from screw.build_errors import BuildError
from screw.calc.thread import (
    T_GATE,
    closed_volume,
    nut_closed_volume,
    section_area,
    section_radius,
    thread_depth,
)
from screw.params import BoltParams, NutParams
from screw.solid import build, clear_cache, nut, precise_volume

client = TestClient(app)

# The M6 nut at a test clearance: s and m are the model's frozen defaults, 0.1 is a test input.
NOMINAL = NutParams(clearance=0.1)
BOX_TOL = 1e-4  # mm; the kernel's own box gap is 1e-7, the thread's crest is inside the prism


@pytest.fixture(autouse=True)
def _cold_solid_cache() -> Iterator[None]:
    # A planted gate only fires on a build, and `build` answers from its cache: a part an earlier
    # test built would pass the planted gate unjudged.
    clear_cache()
    yield
    clear_cache()


@contextmanager
def _inline(backend: object) -> Iterator[None]:
    app.dependency_overrides[build_backend] = lambda: backend
    try:
        yield
    finally:
        app.dependency_overrides.pop(build_backend, None)


# ---------------------------------------------------------------- the solid


@pytest.mark.parametrize("left_hand", [False, True], ids=["right", "left"])
def test_the_nut_is_one_valid_hex_prism_of_s_across_flats_and_m_high(left_hand: bool) -> None:
    p = NutParams(clearance=0.1, left_hand=left_hand)
    shape = build(p)
    assert len(shape.Solids()) == 1
    assert shape.isValid()
    box = shape.BoundingBox()
    # s across flats in x and s / cos 30 degrees across corners in y (the prism is sharp-cornered),
    # z from 0 to m: the void overshoots both faces by a pitch, so neither face moves.
    assert box.xlen == pytest.approx(p.s, abs=BOX_TOL)
    assert box.ylen == pytest.approx(p.s / math.cos(math.pi / 6), abs=BOX_TOL)
    assert box.zmin == pytest.approx(0.0, abs=BOX_TOL)
    assert box.zmax == pytest.approx(p.m, abs=BOX_TOL)


@pytest.mark.parametrize("left_hand", [False, True], ids=["right", "left"])
def test_the_nuts_precise_volume_is_inside_the_gate_of_its_closed_form(left_hand: bool) -> None:
    p = NutParams(clearance=0.1, left_hand=left_hand)
    closed = nut_closed_volume(p.d, p.pitch, p.s, p.m, p.clearance)
    assert abs(precise_volume(build(p)) / closed - 1.0) <= T_GATE


@pytest.mark.parametrize("clearance", [0.0, -0.05])
def test_a_nominal_and_an_interference_nut_build(clearance: float) -> None:
    # D-04: any finite clearance up to the interim bound is a part, not a 422.
    p = NutParams(clearance=clearance)
    shape = build(p)
    assert len(shape.Solids()) == 1
    assert shape.isValid()
    closed = nut_closed_volume(p.d, p.pitch, p.s, p.m, clearance)
    assert abs(precise_volume(shape) / closed - 1.0) <= T_GATE


def test_a_larger_clearance_removes_the_section_difference_times_m() -> None:
    nominal, loose = NutParams(clearance=0.0), NutParams(clearance=0.1)
    removed = precise_volume(build(nominal)) - precise_volume(build(loose))
    expected = (section_area(6.0, 1.0, 0.1) - section_area(6.0, 1.0, 0.0)) * nominal.m
    assert expected > 1.0, "the difference must be big enough to mean something"
    # Judged against the nut, as the gate is: T_GATE of the nut's volume is 0.03 mm3 here, and the
    # difference being measured is about 10 mm3.
    assert abs(removed - expected) <= T_GATE * nut_closed_volume(6.0, 1.0, 10.0, 5.2, 0.0)


# ---------------------------------------------------------------- the two gates


def test_the_nut_builds_when_the_closed_forms_are_right() -> None:
    # The positive control of the two tests below: nothing planted, nothing refused.
    assert len(build(NOMINAL).Solids()) == 1


def _scale_void_form(patch: pytest.MonkeyPatch, factor: float) -> None:
    """Make `screw.solid` judge the void against `factor` times the right closed form."""
    patch.setattr("screw.solid.closed_volume",
                  lambda d, pitch, length, c: closed_volume(d, pitch, length, c) * factor)


def _scale_nut_form(patch: pytest.MonkeyPatch, factor: float) -> None:
    """Make `screw.solid` judge the nut against `factor` times the right closed form."""
    patch.setattr("screw.solid.nut_closed_volume",
                  lambda d, pitch, s, m, c: nut_closed_volume(d, pitch, s, m, c) * factor)


def test_a_closed_form_just_inside_the_gate_does_not_refuse_the_void_or_the_nut(
        monkeypatch: pytest.MonkeyPatch) -> None:
    _scale_void_form(monkeypatch, 1 + T_GATE / 3)
    _scale_nut_form(monkeypatch, 1 + T_GATE / 3)
    assert len(build(NOMINAL).Solids()) == 1


def test_a_void_wrong_by_more_than_the_gate_is_refused_naming_the_void(
        monkeypatch: pytest.MonkeyPatch) -> None:
    _scale_void_form(monkeypatch, 1.001)
    with pytest.raises(BuildError, match="wrong void"):
        build(NOMINAL)


def test_a_nut_wrong_by_more_than_the_gate_is_refused_naming_the_solid(
        monkeypatch: pytest.MonkeyPatch) -> None:
    _scale_nut_form(monkeypatch, 1.001)
    with pytest.raises(BuildError, match="wrong solid") as raised:
        build(NOMINAL)
    # The sign is kept in the text (L11): a closed form 0.1 % too big reads the solid 0.1 % under.
    found = re.search(r"relative error ([+-]\d\.\d+e[+-]\d+)", str(raised.value))
    assert found, str(raised.value)
    assert float(found.group(1)) == pytest.approx(-1e-3, rel=0.01)


def test_a_refused_nut_is_not_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    with monkeypatch.context() as patch:
        _scale_nut_form(patch, 1.001)
        with pytest.raises(BuildError):
            build(NOMINAL)
    # The planted form is gone and the same parameters now build: the refusal left no entry.
    assert len(build(NOMINAL).Solids()) == 1


# ---------------------------------------------------------------- a kernel failure


def test_a_nut_kernel_failure_names_the_nuts_own_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(p: NutParams, v: object) -> object:
        raise RuntimeError("planted")

    monkeypatch.setattr(nut, "assemble", boom)
    with pytest.raises(BuildError) as raised:
        build(NOMINAL)
    text = str(raised.value)
    assert text == ("Geometry kernel failed (RuntimeError); "
                    "check d, pitch, left_hand, s, m and clearance.")
    for bolt_only in ("length", "thread_length", " k"):
        assert bolt_only not in text.removeprefix("Geometry kernel failed (RuntimeError); ")


def test_a_bolt_kernel_failure_still_names_the_bolts_fields(
        monkeypatch: pytest.MonkeyPatch) -> None:
    from screw.params import BoltParams
    from screw.solid import bolt

    def boom(p: BoltParams, thread: object) -> object:
        raise RuntimeError("planted")

    monkeypatch.setattr(bolt, "assemble", boom)
    with pytest.raises(BuildError) as raised:
        build(BoltParams())
    assert str(raised.value) == ("Geometry kernel failed (RuntimeError); "
                                 "check d, pitch, left_hand, length, s, k and thread_length.")


# ---------------------------------------------------------------- the required clearance


def test_the_clearance_is_a_required_field_with_no_default() -> None:
    field = NutParams.model_fields["clearance"]
    assert field.is_required()
    assert field.default is PydanticUndefined
    with pytest.raises(ValidationError):
        NutParams()


def test_the_schema_requires_exactly_the_clearance_and_gives_it_no_default() -> None:
    schema = client.get("/api/schema", params={"kind": "nut"}).json()
    assert schema["required"] == ["clearance"]
    assert "default" not in schema["properties"]["clearance"]
    assert all("default" in prop for name, prop in schema["properties"].items()
               if name != "clearance")


def test_a_nut_info_without_a_clearance_is_a_422_missing_naming_it() -> None:
    res = client.get("/api/nut/info")
    assert res.status_code == 422
    [detail] = res.json()["detail"]
    assert detail["type"] == "missing"
    assert detail["loc"] == ["query", "clearance"]


def test_a_nut_download_without_a_clearance_is_a_422_before_any_build() -> None:
    async def never(p: object, fmt: str, quality: str) -> bytes:
        raise AssertionError("a request without a clearance reached the build backend")

    with _inline(never):
        for path in ("/api/nut/model.stl", "/api/nut/model.step"):
            res = client.get(path)
            assert res.status_code == 422, path
            [detail] = res.json()["detail"]
            assert (detail["type"], detail["loc"]) == ("missing", ["query", "clearance"]), path


@pytest.mark.parametrize(("raw", "kind"), [
    ("", "float_parsing"),
    ("inf", "finite_number"),
    ("nan", "finite_number"),
    ("100001", "less_than_equal"),
    ("text", "float_parsing"),
])
def test_a_clearance_the_model_cannot_take_is_refused_naming_clearance(raw: str, kind: str) -> None:
    res = client.get("/api/nut/info", params={"clearance": raw})
    assert res.status_code == 422, raw
    [detail] = res.json()["detail"]
    assert detail["loc"] == ["query", "clearance"], raw
    assert detail["type"] == kind, raw


@pytest.mark.parametrize("raw", ["0", "-0.05", "0.1", "1.9"])
def test_a_clearance_the_model_takes_is_a_200(raw: str) -> None:
    # The positive control of the refusals above: 0 and an interference are legal (D-04). The
    # interim ceiling 100000 passes the field and is refused by the thin-nut rule (D-13, below):
    # with the default s of 10 the void is wider than the flats from c = 2 up.
    res = client.get("/api/nut/info", params={"clearance": raw})
    assert res.status_code == 200, (raw, res.text)
    assert res.json()["kind"] == "nut"


# ---------------------------------------------------------------- through every front end


def test_the_kinds_route_lists_the_nut_beside_the_bolt() -> None:
    body = client.get("/api/kinds").json()
    assert body == {"default": "bolt", "kinds": ["bolt", "nut"]}


def test_a_real_worker_builds_a_nut_for_the_stl_and_the_step() -> None:
    # Through the pool, so the NutParams crosses the process boundary and builds in a worker.
    # 0.13 and 0.17 are clearances no other test downloads: the byte cache is shared by the
    # session and would answer before the pool ran.
    with TestClient(app) as pooled:
        stl = pooled.get("/api/nut/model.stl", params={"clearance": 0.13, "quality": "preview"})
        assert stl.status_code == 200
        assert len(stl.content) > 1000
        (count,) = struct.unpack("<I", stl.content[80:84])
        assert len(stl.content) == 84 + 50 * count
        step = pooled.get("/api/nut/model.step", params={"clearance": 0.17})
        assert step.status_code == 200
        assert step.content.startswith(b"ISO-10303-21;")


def test_the_cli_prints_the_nut_document_and_writes_a_binary_stl(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cli.main(["info", "nut", "--clearance", "0.1"])
    assert json.loads(capsys.readouterr().out)["kind"] == "nut"
    out = tmp_path / "nut.stl"
    cli.main(["export", "nut", "--clearance", "0.1", "--quality", "preview", "-o", str(out)])
    data = out.read_bytes()
    (count,) = struct.unpack("<I", data[80:84])
    assert len(data) == 84 + 50 * count
    assert count > 100


def test_the_cli_and_the_api_print_one_nut_document(capsys: pytest.CaptureFixture[str]) -> None:
    cli.main(["info", "nut", "--clearance", "0.1", "--left-hand", "--s", "11"])
    printed = json.loads(capsys.readouterr().out)
    served = client.get("/api/nut/info",
                        params={"clearance": 0.1, "left_hand": "true", "s": 11}).json()
    assert printed == served


def test_every_nut_flag_the_help_lists_is_a_field_and_the_required_one_says_so(
        capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as stop:
        cli.main(["info", "nut", "--help"])
    assert stop.value.code == 0
    help_text = " ".join(capsys.readouterr().out.split())
    assert "--clearance V" in help_text
    assert "[required]" in help_text
    assert "PydanticUndefined" not in help_text


# ---------------------------------------------------------------- the nut's three model rules


def _refusal(**fields: float | bool) -> dict[str, object]:
    """The one error a NutParams(**fields) raises, as pydantic reports it."""
    with pytest.raises(ValidationError) as caught:
        NutParams(**fields)  # type: ignore[arg-type]
    [err] = caught.value.errors()
    return dict(err)


def test_the_root_radius_rule_reads_the_clearance() -> None:
    # M2 x 2 is a bolt the c-free rule refuses (root radius 1 - 5H/8 < 0), and a nut a clearance
    # of 0.5 makes: the nut's rule replaces the inherited one (RESEARCH F6), not runs beside it.
    with pytest.raises(ValidationError):
        BoltParams(d=2.0, pitch=2.0)
    p = NutParams(d=2.0, pitch=2.0, clearance=0.5)
    shape = build(p)
    assert len(shape.Solids()) == 1
    assert shape.isValid()
    err = _refusal(d=2.0, pitch=2.0, clearance=0.0)
    assert err["type"] == "pitch_too_coarse"
    assert err["loc"] == ()
    assert err["ctx"] == {"fields": ["d", "pitch", "clearance"]}
    assert str(err["msg"]).startswith("d, pitch and clearance: ")


def test_the_void_root_radius_is_refused_at_exactly_zero_and_accepted_one_float_above() -> None:
    # c = 5H/8 - d/2: d/2 - 5H/8 is the exact negation of it, so the sum the rule takes is 0.0.
    exact = thread_depth(2.0) - 1.0
    assert 2.0 / 2 - thread_depth(2.0) + exact == 0.0
    assert _refusal(d=2.0, pitch=2.0, clearance=exact)["type"] == "pitch_too_coarse"
    assert NutParams(d=2.0, pitch=2.0, clearance=math.nextafter(exact, math.inf)).d == 2.0


def test_a_nut_whose_flats_are_no_wider_than_its_void_is_refused_naming_three_fields() -> None:
    d, c = 6.0, 0.1
    err = _refusal(s=d + 2 * c, clearance=c)
    assert err["type"] == "nut_too_thin"
    assert err["loc"] == ()
    assert err["ctx"] == {"fields": ["s", "d", "clearance"]}
    msg = str(err["msg"])
    assert msg.startswith("s, d and clearance: ")
    assert "wider than the flats" in msg
    assert NutParams(s=math.nextafter(d + 2 * c, math.inf), clearance=c).clearance == c
    # The interim ceiling passes the clearance field and is refused here, not as less_than_equal.
    assert _refusal(clearance=1e5)["type"] == "nut_too_thin"
    # A negative clearance shrinks the void: the same s that is thin at c = 0.1 is fine at -0.1.
    assert NutParams(s=6.1, clearance=-0.1).s == 6.1


def test_the_turn_cap_judges_the_void_the_builder_makes() -> None:
    # m + 2 pitch is what `solid/nut.py` sweeps: 248 pitches of m make exactly 250 turns.
    for pitch, m in ((1.0, 248.0), (0.5, 124.0), (0.7, 173.6)):
        assert NutParams(pitch=pitch, m=m, clearance=0.1).m == m, (pitch, m)
        err = _refusal(pitch=pitch, m=math.nextafter(m, math.inf), clearance=0.1)
        assert err["type"] == "turn_cap"
        assert err["loc"] == ()
        assert err["ctx"] == {"fields": ["m", "pitch"]}
        assert str(err["msg"]).startswith("m and pitch: ")


def test_an_over_thin_nut_is_a_422_on_the_api_and_exit_2_on_the_cli(
        capsys: pytest.CaptureFixture[str]) -> None:
    res = client.get("/api/nut/info", params={"clearance": 0.1, "s": 6})
    assert res.status_code == 422
    [detail] = res.json()["detail"]
    assert detail["type"] == "nut_too_thin"
    assert detail["loc"] == ["query"]
    assert detail["ctx"]["fields"] == ["s", "d", "clearance"]
    assert detail["msg"].startswith("s, d and clearance: ")
    with pytest.raises(SystemExit) as stop:
        cli.main(["info", "nut", "--clearance", "0.1", "--s", "6"])
    assert stop.value.code == 2
    assert "error: s, d and clearance: " in capsys.readouterr().err


@pytest.mark.parametrize("left_hand", [False, True], ids=["right", "left"])
def test_a_positive_clearance_moves_the_nut_thread_away_from_the_axis_on_both_hands(
        left_hand: bool) -> None:
    """PAIR-01's direction as a kernel fact: 0.05 mm outside the nominal void surface is inside
    the c = 0 nut and outside the c = 0.1 nut, and the volume drops by the section difference.

    The c = 0 half is the positive control. The point is placed with the hand's sign (RESEARCH
    F2: the section angle is atan2(y, x) - 2 pi z / P right-hand and + for left-hand), so a wrong
    sign puts the point on another part of the surface and the c = 0 check, which needs the point
    in material, fails.
    """
    tight = NutParams(clearance=0.0, left_hand=left_hand)
    loose = NutParams(clearance=0.1, left_hand=left_hand)
    tight_nut, loose_nut = build(tight).Solids()[0], build(loose).Solids()[0]
    z = tight.m / 2
    turn = 2 * math.pi * z / tight.pitch
    sign = 1 if left_hand else -1
    # crest, mid flank and root of the section: the three kinds of surface the thread has
    for section_angle in (0.0, math.pi / 2, math.pi):
        radius = section_radius(tight.d, tight.pitch, 0.0, section_angle) + 0.05
        angle = section_angle - sign * turn
        point = cq.Vector(radius * math.cos(angle), radius * math.sin(angle), z)
        assert tight_nut.isInside(point, 1e-6), (left_hand, section_angle)
        assert not loose_nut.isInside(point, 1e-6), (left_hand, section_angle)
    removed = precise_volume(tight_nut) - precise_volume(loose_nut)
    expected = (section_area(tight.d, tight.pitch, 0.1)
                - section_area(tight.d, tight.pitch, 0.0)) * tight.m
    assert abs(removed - expected) <= T_GATE * precise_volume(tight_nut)
