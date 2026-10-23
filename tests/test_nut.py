"""The nut kind's solid, its two gates and its defaulted clearance (L17).

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
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

import cadquery as cq
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from bench.thread_spike.measure import stl_check
from screw import app as app_module
from screw import cli
from screw.app import app, build_backend
from screw.build_errors import BuildError
from screw.calc.thread import (
    CHAMFER_ANGLE_DEG,
    COUNTERSINK_HALF_ANGLE_DEG,
    T_GATE,
    closed_volume,
    countersink_face_radius,
    countersink_volume,
    end_depths,
    face_chamfer_volume,
    nut_closed_volume,
    nut_end_closed_volume,
    piece_refusal,
    section_area,
    section_radius,
    thread_depth,
    volume_check,
)
from screw.params import BoltParams, NutParams
from screw.solid import build, clear_cache, export, nut, precise_volume
from screw.tables.presets import nut_catalogue

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
    closed = nut_end_closed_volume(p.d, p.pitch, p.s, p.m, p.clearance)
    assert abs(precise_volume(build(p)) / closed - 1.0) <= T_GATE


@pytest.mark.parametrize("clearance", [0.0, -0.05])
def test_a_nominal_and_an_interference_nut_build(clearance: float) -> None:
    # D-04: any finite clearance up to the interim bound is a part, not a 422.
    p = NutParams(clearance=clearance)
    shape = build(p)
    assert len(shape.Solids()) == 1
    assert shape.isValid()
    closed = nut_end_closed_volume(p.d, p.pitch, p.s, p.m, clearance)
    assert abs(precise_volume(shape) / closed - 1.0) <= T_GATE


def test_a_larger_clearance_removes_the_section_difference_times_m_less_the_ends() -> None:
    nominal, loose = NutParams(clearance=0.0), NutParams(clearance=0.1)
    removed = precise_volume(build(nominal)) - precise_volume(build(loose))
    # The void grows by the section difference times m; the countersinks of the looser nut are
    # shallower, so they take less of what the void already took. The end-aware closed form
    # carries both, and the bare section difference alone is the wrong answer by that much.
    expected = (nut_end_closed_volume(6.0, 1.0, 10.0, 5.2, 0.0)
                - nut_end_closed_volume(6.0, 1.0, 10.0, 5.2, 0.1))
    bare = (section_area(6.0, 1.0, 0.1) - section_area(6.0, 1.0, 0.0)) * nominal.m
    assert bare > 1.0, "the difference must be big enough to mean something"
    assert abs(expected - bare) > 10 * T_GATE * nut_closed_volume(6.0, 1.0, 10.0, 5.2, 0.0)
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
    patch.setattr("screw.solid.nut_end_closed_volume",
                  lambda d, pitch, s, m, c: nut_end_closed_volume(d, pitch, s, m, c) * factor)


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


# ---------------------------------------------------------------- the clearance default


def test_the_clearance_is_a_defaulted_field_not_a_required_one() -> None:
    field = NutParams.model_fields["clearance"]
    assert not field.is_required()
    assert field.default == 0.15
    assert NutParams().clearance == 0.15


def test_the_schema_requires_nothing_and_gives_the_clearance_its_default() -> None:
    schema = client.get("/api/schema", params={"kind": "nut"}).json()
    assert "required" not in schema or schema["required"] == []
    assert schema["properties"]["clearance"]["default"] == 0.15
    assert all("default" in prop for prop in schema["properties"].values())


def test_a_nut_info_without_a_clearance_is_a_200_at_the_default() -> None:
    res = client.get("/api/nut/info")
    assert res.status_code == 200
    body = res.json()
    assert {row["key"]: row["value"] for row in body["rows"]}["clearance"] == 0.15
    assert body == client.get("/api/nut/info", params={"clearance": 0.15}).json()


def test_a_nut_download_without_a_clearance_builds_at_the_default(
        monkeypatch: pytest.MonkeyPatch) -> None:
    # A private byte cache: the shared one would answer a second run before the backend ran, and
    # would keep this test's fake b"x" for every later default download in the session.
    monkeypatch.setattr(app_module, "_EXPORTS", app_module._BlobCache(1 << 20))
    seen: list[float] = []

    async def record(p: NutParams, fmt: str, quality: str) -> bytes:
        seen.append(p.clearance)
        return b"x"

    with _inline(record):
        for path in ("/api/nut/model.stl", "/api/nut/model.step"):
            assert client.get(path).status_code == 200, path
    assert seen == [0.15, 0.15]


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


def test_every_nut_flag_the_help_lists_is_a_field_and_the_clearance_shows_its_default(
        capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as stop:
        cli.main(["info", "nut", "--help"])
    assert stop.value.code == 0
    help_text = " ".join(capsys.readouterr().out.split())
    assert "--clearance V" in help_text
    assert "[0.15]" in help_text
    assert "[required]" not in help_text
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
    # The looser void also takes shallower countersinks, so the end-aware form is the measure.
    expected = (nut_end_closed_volume(tight.d, tight.pitch, tight.s, tight.m, 0.0)
                - nut_end_closed_volume(loose.d, loose.pitch, loose.s, loose.m, 0.1))
    assert abs(removed - expected) <= T_GATE * precise_volume(tight_nut)


# ---------------------------------------------------------------- the ends: countersinks, chamfers


def _pieces(p: NutParams) -> list[tuple[str, float, float]]:
    """(piece, volume its cut removed, its oracle) for each cut `nut.finish` makes, in order, from
    precise volumes before and after: the same measurement the builder judges."""
    body = nut.assemble(p, nut.void(p))
    volume = precise_volume(body)
    csk, chamfer, _ = end_depths(p.d, p.pitch, p.clearance, p.s, p.m)
    oracles = {
        "lead-in countersink": 0.0 if csk <= 0 else countersink_volume(
            p.d, p.pitch, p.clearance, p.s, countersink_face_radius(p.d),
            COUNTERSINK_HALF_ANGLE_DEG, csk),
        "face chamfer": face_chamfer_volume(p.s, p.s / 2, CHAMFER_ANGLE_DEG, chamfer),
    }
    out = []
    for what, cut in nut.finish(p, body):
        after = precise_volume(cut)
        out.append((what, volume - after, oracles[what]))
        volume = after
    return out


ENDED = [
    pytest.param(NutParams(clearance=0.1), id="M6-right"),
    pytest.param(NutParams(clearance=0.1, left_hand=True), id="M6-left"),
    pytest.param(NutParams(clearance=0.0), id="c0"),
    pytest.param(NutParams(clearance=-0.05), id="c-0.05"),
    # D-12: no row has d 6.5, and its ends come from its fields all the same.
    pytest.param(NutParams(d=6.5, pitch=1.0, s=11.0, m=5.2, clearance=0.1), id="off-row"),
    # R5 a: capped at m / 2 (the countersink 0.4 of its 0.92, the chamfer 0.4 of its 0.45).
    pytest.param(NutParams(clearance=0.1, m=0.8), id="thin-capped"),
]


@pytest.mark.parametrize("p", ENDED)
def test_each_cut_removes_the_volume_its_oracle_names_to_within_the_piece_tolerance(
        p: NutParams) -> None:
    pieces = _pieces(p)
    assert [what for what, _, _ in pieces] == (
        ["lead-in countersink"] * 2 + ["face chamfer"] * 2)
    for what, removed, oracle in pieces:
        assert piece_refusal(removed, oracle, what) is None
        assert removed > 0.1, "a real fraction of a mm3, not a cut that removed nothing"


@pytest.mark.parametrize("p", ENDED)
def test_a_nut_with_ends_is_one_valid_solid_inside_the_whole_gate(p: NutParams) -> None:
    solid = build(p)
    assert len(solid.Solids()) == 1
    assert solid.isValid()
    closed = nut_end_closed_volume(p.d, p.pitch, p.s, p.m, p.clearance)
    assert abs(precise_volume(solid) / closed - 1.0) <= T_GATE


def test_both_hands_get_the_same_ends_to_the_gate() -> None:
    right, left = (NutParams(clearance=0.1, left_hand=h) for h in (False, True))
    assert precise_volume(build(right)) == pytest.approx(precise_volume(build(left)), rel=T_GATE)


def test_a_countersink_that_cannot_cross_the_void_is_not_cut_and_the_nut_still_builds() -> None:
    # R3: M2 at clearance 0.2, the cone opens to 1.16 mm inside a 1.2 mm crest radius.
    p = NutParams(d=2.0, pitch=0.4, s=4.0, m=1.6, clearance=0.2)
    assert end_depths(p.d, p.pitch, p.clearance, p.s, p.m)[0] == 0.0
    assert [what for what, _, _ in _pieces(p)] == ["face chamfer"] * 2
    closed = nut_end_closed_volume(p.d, p.pitch, p.s, p.m, p.clearance)
    assert abs(precise_volume(build(p)) / closed - 1.0) <= T_GATE


@pytest.mark.parametrize("left_hand", [False, True], ids=["right", "left"])
@pytest.mark.parametrize("s", [1.5, 1.7, 1.11])
def test_a_narrow_nut_below_root_three_across_flats_builds_inside_the_gate(
        s: float, left_hand: bool) -> None:
    """WR-01: the face-chamfer cutter's fixed 0.5 mm overshoot put its first profile point at a
    negative radius below sqrt(3) mm across flats, and the kernel refused a valid nut with
    `Standard_Failure`. s 1.11 is just above d + 2 c (1.1), the smallest the model accepts here.
    `build` runs every piece gate, so a passing build means each cut met its oracle."""
    p = NutParams(d=1.0, pitch=0.25, s=s, m=1.0, clearance=0.05, left_hand=left_hand)
    solid = build(p)
    assert len(solid.Solids()) == 1
    assert solid.isValid()
    closed = nut_end_closed_volume(p.d, p.pitch, p.s, p.m, p.clearance)
    assert abs(precise_volume(solid) / closed - 1.0) <= T_GATE


@pytest.mark.parametrize("p", [
    pytest.param(NutParams(d=2.0, pitch=0.4, s=3.5, m=1.6, clearance=0.1), id="s3.5"),
    pytest.param(NutParams(d=2.0, pitch=0.4, s=4.0, m=1.6, clearance=0.1), id="s4.0-M2"),
    pytest.param(NutParams(clearance=0.1), id="s10-default"),
])
def test_a_narrow_nut_fix_leaves_the_cutter_every_shipped_nut_was_cut_with(p: NutParams) -> None:
    """From s = 2 sqrt(3) mm up the overshoot is the old 0.5 mm, so a catalogue nut is unchanged
    (L02): the cutter reaches 0.5 mm below the face."""
    _, chamfer, _ = end_depths(p.d, p.pitch, p.clearance, p.s, p.m)
    assert nut.face_chamfer(p, 0.0, chamfer).BoundingBox().zmin == pytest.approx(-0.5, abs=1e-6)


def test_the_ends_read_the_fields_and_no_table() -> None:
    # D-12: a table row gives the nut nothing it does not already take as fields.
    assert "tables" not in Path(nut.__file__).read_text()


def _skip_the_first_countersink(monkeypatch: pytest.MonkeyPatch) -> None:
    real = nut.countersink
    calls: list[float] = []

    def cutter(p: NutParams, z_face: float, depth: float) -> cq.Solid:
        calls.append(z_face)
        if len(calls) == 1:  # a cutter nowhere near the nut leaves it whole
            return cq.Solid.makeBox(0.1, 0.1, 0.1, pnt=cq.Vector(100, 100, 100))
        return real(p, z_face, depth)

    monkeypatch.setattr(nut, "countersink", cutter)


def _skip_the_second_chamfer(monkeypatch: pytest.MonkeyPatch) -> None:
    real = nut.face_chamfer
    calls: list[float] = []

    def cutter(p: NutParams, z_face: float, depth: float) -> cq.Solid:
        calls.append(z_face)
        if len(calls) == 2:
            return cq.Solid.makeBox(0.1, 0.1, 0.1, pnt=cq.Vector(100, 100, 100))
        return real(p, z_face, depth)

    monkeypatch.setattr(nut, "face_chamfer", cutter)


CONTROLS = [
    pytest.param(_skip_the_first_countersink, "lead-in countersink", id="countersink-skipped"),
    pytest.param(_skip_the_second_chamfer, "face chamfer", id="chamfer-skipped"),
    pytest.param(lambda patch: patch.setattr(nut, "CHAMFER_ANGLE_DEG", 45.0), "face chamfer",
                 id="chamfer-45-where-30-is-the-model"),
    pytest.param(lambda patch: patch.setattr(nut, "COUNTERSINK_HALF_ANGLE_DEG", 60.0),
                 "lead-in countersink", id="countersink-60-where-45-is-the-model"),
]


@pytest.mark.parametrize(("plant", "what"), CONTROLS)
def test_a_missing_or_wrong_end_is_refused_naming_the_piece(
        monkeypatch: pytest.MonkeyPatch, plant: Callable[[pytest.MonkeyPatch], object],
        what: str) -> None:
    # The positive controls of RESEARCH P8 for the nut: the model is two countersinks of 90 degrees
    # included and two 30 degree chamfers, and each control builds something else.
    plant(monkeypatch)
    with pytest.raises(BuildError, match=f"wrong {what}: the {what} is"):
        build(NOMINAL)


@pytest.mark.parametrize(("plant", "what"), CONTROLS)
def test_the_whole_nut_gate_alone_sees_each_control_a_nut_is_not_a_long_bolt(
        monkeypatch: pytest.MonkeyPatch, plant: Callable[[pytest.MonkeyPatch], object],
        what: str) -> None:
    # Measured, not predicted (05-13 SUMMARY): a countersink or chamfer is 1 to 2 % of an M6 nut,
    # against the bolt's tip cone in a 200 mm part (05-12, where the gate alone missed two of
    # six), so the whole-part gate flags every control here as well. The piece check is still
    # the one that names which end is wrong.
    plant(monkeypatch)
    last = list(nut.finish(NOMINAL, nut.assemble(NOMINAL, nut.void(NOMINAL))))[-1][1]
    closed = nut_end_closed_volume(NOMINAL.d, NOMINAL.pitch, NOMINAL.s, NOMINAL.m, 0.1)
    assert volume_check(precise_volume(last), closed) is not None, what


# ---------------------------------------------------------------- the catalogue sweep (P7, D-12)


def _catalogue_nut(row_id: str, clearance: float, left_hand: bool = False) -> NutParams:
    [row] = [r for r in nut_catalogue() if r.id == row_id]
    return NutParams.model_validate({**dict(row.fields), "clearance": clearance,
                                     "left_hand": left_hand})


@pytest.mark.parametrize("left_hand", [False, True], ids=["right", "left"])
@pytest.mark.parametrize("row_id", [r.id for r in nut_catalogue()])
def test_every_iso_4032_nut_meshes_watertight_at_preview(row_id: str, left_hand: bool) -> None:
    mesh = stl_check(export(_catalogue_nut(row_id, 0.1, left_hand), "stl", "preview"))
    assert mesh.open_edges == 0, (row_id, left_hand)
    assert mesh.triangles > 0


@pytest.mark.parametrize("clearance", [0.0, 0.1, 0.2])
@pytest.mark.parametrize("row_id", [r.id for r in nut_catalogue()])
def test_every_countersink_crosses_the_void_root(row_id: str, clearance: float) -> None:
    """The cone ends below the root radius, so it crosses the root surface and never grazes it
    (the grazing probe left 8 open preview edges, RESEARCH F8): the geometric half of what the
    mesh sweep above sees. A nut whose cone cannot cross the void gets no countersink at all."""
    p = _catalogue_nut(row_id, clearance)
    depth, _, warnings = end_depths(p.d, p.pitch, clearance, p.s, p.m)
    root = p.d / 2 - thread_depth(p.pitch) + clearance
    if depth == 0.0:
        assert any(w.startswith(f"clearance {clearance:g}:") for w in warnings)
        return
    inner = nut.countersink_inner_radius(p, depth)
    assert inner < root
    # The inner radius is the one the built cutter ends on: its bottom is where the cone reaches it.
    cutter = nut.countersink(p, 0.0, depth)
    reach = (countersink_face_radius(p.d) - inner) / math.tan(math.radians(
        COUNTERSINK_HALF_ANGLE_DEG))
    assert cutter.BoundingBox().zmax == pytest.approx(reach, abs=BOX_TOL)
    # And it opens wider than the crest: the cone crosses the void from the outside as well.
    assert countersink_face_radius(p.d) > p.d / 2 + clearance


def test_a_capped_countersink_ends_flat_in_material_above_the_root() -> None:
    # R5 a: a depth capped at m / 2 stops where the cone is still outside the root radius, so the
    # cutter's bottom is a plane in material that crosses the flanks, never a graze.
    p = NutParams(clearance=0.1, m=0.8)
    depth = end_depths(p.d, p.pitch, p.clearance, p.s, p.m)[0]
    assert depth == pytest.approx(0.4)
    root = p.d / 2 - thread_depth(p.pitch) + p.clearance
    assert nut.countersink_inner_radius(p, depth) > root
    assert nut.countersink(p, 0.0, depth).BoundingBox().zmax == pytest.approx(depth, abs=BOX_TOL)
    mesh = stl_check(export(p, "stl", "preview"))
    assert mesh.open_edges == 0


def test_a_cone_that_ends_on_the_root_passes_every_volume_gate_and_opens_the_mesh(
        monkeypatch: pytest.MonkeyPatch) -> None:
    # The positive control of the sweep (T-05-28): with no overshoot the cone ends exactly on the
    # root surface. The solid is valid and inside the volume gate, so only the mesh sees it; the
    # geometric test above is the other net, and it refuses the same cutter.
    monkeypatch.setattr(nut, "CROSS_FRACTION", 0.0)
    p = NutParams(clearance=0.1)
    depth = end_depths(p.d, p.pitch, p.clearance, p.s, p.m)[0]
    root = p.d / 2 - thread_depth(p.pitch) + p.clearance
    assert not nut.countersink_inner_radius(p, depth) < root
    assert len(build(p).Solids()) == 1  # built: no gate refused it
    assert stl_check(export(p, "stl", "preview")).open_edges > 0
