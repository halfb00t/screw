"""The HTTP contract of every registered kind: validation, foreign fields, bound adjacency,
admission control, the byte cache, gzip and the per-request log vocabulary.

Every test builds through an inline backend (the autouse fixture below). tests/test_pool.py
is the one place a build crosses the process boundary for real.

The byte cache (`app._EXPORTS`) is shared by the whole pytest session, so a test that
asserts a fresh build, a build count or a failing backend uses a diameter no other test in
the suite downloads (tests/test_pool.py takes the default part, 6.5 and 6.6), or the cache
would answer before the backend under test ever ran.
"""

from __future__ import annotations

import logging
import math
import re
import time
from collections.abc import Iterator
from concurrent.futures.process import BrokenProcessPool
from contextlib import contextmanager
from pathlib import Path
from typing import cast

import cadquery as cq
import pytest
from fastapi.testclient import TestClient

from screw import app as app_module
from screw.app import app, build_backend
from screw.build_errors import BuildError, BuildTimeout
from screw.calc import STANDING_WARNING
from screw.calc.cost import BUILD_TIMEOUT_S, Artifact
from screw.calc.presets import expand
from screw.calc.thread import (
    T_GATE,
    bolt_end_closed_volume,
    head_chamfer_depths,
    head_chamfer_warnings,
)
from screw.params import DEFAULT_KIND, KINDS, BoltParams, FastenerParams
from screw.solid import Format, Quality, export, precise_volume
from screw.tables.presets import catalogue

client = TestClient(app)

# `params=` is typed by starlette 1.7.0 as exactly this union; a bare `dict[str, object]`
# fails mypy at every call site.
Params = dict[str, str | int | float | bool | None]


async def _inline_backend(p: FastenerParams, fmt: str, quality: str) -> bytes:
    # build_backend's BuildBackend type is str/str (app.py has no static import path to
    # solid.Format/solid.Quality to name them with, contract 5); this override does, so the
    # cast just narrows back to what export() actually wants.
    return export(p, cast(Format, fmt), cast(Quality, quality))


@pytest.fixture(autouse=True, scope="module")
def _inline_build_backend() -> Iterator[None]:
    """Override the pool-backed dependency with an in-process build, for every test here.

    The module-level `client = TestClient(app)` never runs the app's lifespan (it is used
    without `with`), so app.state.pool never exists for these tests. Overriding the
    dependency directly means these tests exercise the exact code path the CLI takes and
    never depend on lifespan state. tests/test_pool.py deliberately does not install this
    override, to prove the pool path for real.
    """
    app.dependency_overrides[build_backend] = lambda: _inline_backend
    yield
    app.dependency_overrides.pop(build_backend, None)


@contextmanager
def _backend(replacement: object) -> Iterator[None]:
    """Swap the build backend for one test and put the inline one back afterwards."""
    app.dependency_overrides[build_backend] = lambda: replacement
    try:
        yield
    finally:
        app.dependency_overrides[build_backend] = lambda: _inline_backend


@contextmanager
def _saturated() -> Iterator[None]:
    """Hold every admission slot, as a service with MAX_QUEUED_BUILDS builds in flight."""
    held = [app_module.BUILD_QUEUE.acquire(blocking=False)
            for _ in range(app_module.MAX_QUEUED_BUILDS)]
    try:
        assert all(held)
        yield
    finally:
        for _ in held:
            app_module.BUILD_QUEUE.release()


def _event_records(caplog: pytest.LogCaptureFixture, event: str) -> list[logging.LogRecord]:
    """The records this module's helpers emitted for one literal event name.
    `getattr(..., None)` (not a plain attribute access): `caplog.records` also holds
    records from other loggers (httpx logs its own "HTTP Request" line at INFO once
    anything sets the root level there), and those carry no `event` attribute at all.
    """
    return [rec for rec in caplog.records if getattr(rec, "event", None) == event]


def _field(rec: logging.LogRecord, name: str) -> object:
    """Read a field one of records.py's per-event helpers attached via `extra=`, on a
    record already selected by `_event_records` -- so the field is known present.
    LogRecord's stub declares no such attribute, so `getattr` on it yields an untyped
    value; `object` states that honestly. Each caller compares by equality or narrows
    before doing arithmetic on it.
    """
    return getattr(rec, name)


def test_health() -> None:
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    # pool is present-and-null under the bare client, not absent.
    assert "pool" in body
    assert body["pool"] is None


def test_index_and_static() -> None:
    assert "screw" in client.get("/").text
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/vendor/three.bundle.min.js").status_code == 200


def test_kinds_names_the_frozen_default() -> None:
    assert client.get("/api/kinds").json() == {"default": "bolt", "kinds": ["bolt", "nut"]}
    # The literal, not DEFAULT_KIND: a link that omits `kind` means bolt forever (L02).
    assert DEFAULT_KIND == "bolt"
    assert list(KINDS) == ["bolt", "nut"]


def test_a_nut_with_a_clearance_serves_its_info_and_both_downloads() -> None:
    # TYPE-03: the second kind through every route; the clearance is a test input, not a default.
    info = client.get("/api/nut/info", params={"clearance": 0.1})
    assert info.status_code == 200
    assert info.json()["kind"] == "nut"
    stl = client.get("/api/nut/model.stl", params={"clearance": 0.1, "quality": "preview"})
    assert stl.status_code == 200
    assert len(stl.content) > 1000
    step = client.get("/api/nut/model.step", params={"clearance": 0.1})
    assert step.status_code == 200
    assert step.content.startswith(b"ISO-10303-21;")
    assert 'filename="nut_' in step.headers["content-disposition"]


def test_the_nut_schema_carries_the_clearance_default() -> None:
    schema = client.get("/api/schema", params={"kind": "nut"}).json()
    assert list(schema["properties"]) == ["d", "pitch", "left_hand", "s", "m", "clearance"]
    assert "clearance" not in schema.get("required", [])
    assert schema["properties"]["clearance"]["default"] == 0.15
    assert schema["properties"]["clearance"]["title"] == "Clearance (radial)"
    assert schema["properties"]["clearance"]["group"] == "Pair"
    assert schema["properties"]["s"]["group"] == schema["properties"]["m"]["group"] == "Nut"


def test_schema_requires_a_kind_and_knows_only_registered_kinds() -> None:
    r = client.get("/api/schema", params={"kind": "bolt"})
    assert r.status_code == 200
    props = r.json()["properties"]
    assert list(props) == [
        "d", "pitch", "left_hand", "length", "s", "k", "thread_length", "head_chamfer"]
    assert props["d"]["group"] == "Size"
    assert props["s"]["group"] == props["k"]["group"] == props["head_chamfer"]["group"] == "Head"
    assert props["thread_length"]["group"] == "Thread"
    assert props["thread_length"]["default"] == 20.0
    assert props["d"]["unit"] == "mm"
    assert props["length"]["unit"] == "mm"

    missing = client.get("/api/schema")
    assert missing.status_code == 422
    assert missing.json()["detail"][0]["loc"] == ["query", "kind"]

    unknown = client.get("/api/schema", params={"kind": "washer"})
    assert unknown.status_code == 404
    detail = unknown.json()["detail"][0]
    assert detail["loc"] == ["query", "kind"]
    assert detail["type"] == "unknown_kind"


def test_the_preset_catalogue_is_one_document_in_catalogue_order() -> None:
    res = client.get("/api/presets", params={"kind": "bolt"})
    assert res.status_code == 200
    body = res.json()
    assert set(body) == {"kind", "axes", "rows"}
    assert body["kind"] == "bolt"
    assert body["axes"] == ["Standard", "Size", "Length"]
    rows = body["rows"]
    assert [r["id"] for r in rows] == [row.id for row in catalogue()]
    # 186 ISO 4017 rows then 108 ISO 4014 rows (plans 04-09 and 04-10).
    assert len(rows) == 294
    assert rows[0]["id"] == "iso4017:M2x4"
    assert rows[-1]["id"] == "iso4014:M20x200"
    m6 = next(r for r in rows if r["id"] == "iso4017:M6x20")
    assert set(m6) == {"id", "display", "designation", "picker", "fields", "citation"}
    assert m6["display"] == "ISO 4017 M6 \u00d7 20"
    assert m6["picker"] == ["ISO 4017", "M6", "20"]
    assert m6["fields"] == {"d": 6.0, "pitch": 1.0, "length": 20.0, "s": 10.0, "k": 4.0,
                            "thread_length": 20.0}
    assert "ISO 4017:2022" in m6["citation"]


def test_a_second_choice_size_is_bracketed_in_the_catalogue_and_a_decimal_point_is_kept() -> None:
    rows = {r["id"]: r for r in client.get("/api/presets", params={"kind": "bolt"}).json()["rows"]}
    assert rows["iso4017:M3.5x20"]["picker"][1] == "(M3.5)"
    assert rows["iso4017:M3.5x20"]["display"] == "ISO 4017 (M3.5) \u00d7 20"
    assert "iso4017:m6x20" not in rows, "ids are case-sensitive"


def test_the_preset_catalogue_of_an_unknown_kind_is_a_404_naming_the_known_kinds() -> None:
    res = client.get("/api/presets", params={"kind": "washer"})
    assert res.status_code == 404
    [detail] = res.json()["detail"]
    assert detail["loc"] == ["query", "kind"]
    assert detail["type"] == "unknown_kind"
    assert "Known kinds: bolt, nut" in detail["msg"]


def test_the_preset_catalogue_needs_one_kind() -> None:
    assert client.get("/api/presets").status_code == 422
    twice = client.get("/api/presets", params=[("kind", "bolt"), ("kind", "bolt")])
    assert twice.status_code == 422
    assert twice.json()["detail"][0]["type"] == "duplicate"


@pytest.mark.parametrize("path", ["/api/bolt/info", "/api/bolt/model.stl"])
def test_a_preset_key_is_refused_on_the_model_routes(path: str) -> None:
    # TABL-01, D-09: a link carries millimetres, never a preset id.
    res = client.get(path, params={"preset": "iso4017:M6x20"})
    assert res.status_code == 422
    [detail] = res.json()["detail"]
    assert detail["type"] == "extra_forbidden"
    assert detail["loc"] == ["query", "preset"]


def test_the_empty_query_is_the_iso_4017_m6_x_20_exact_match() -> None:
    preset = client.get("/api/bolt/info").json()["preset"]
    assert preset["status"] == "exact"
    assert preset["id"] == "iso4017:M6x20"


def test_an_unknown_kind_has_no_routes() -> None:
    assert client.get("/api/washer/info").status_code == 404
    assert client.get("/api/washer/model.stl").status_code == 404


def test_the_pair_proof_has_no_endpoint() -> None:
    """PAIR-04: the proof is a function and a CLI command, never a route (a boolean per request
    is not something the server's 30 s budget can promise). Checked on the schema the clients
    read and on the routes the app serves, so a hidden route fails it too."""
    paths = client.get("/openapi.json").json()["paths"]
    assert paths
    assert not [path for path in paths if "pair" in path]
    assert not [route for route in app.routes if "pair" in str(getattr(route, "path", ""))]
    assert client.get("/api/nut/pair").status_code == 404


def test_openapi_documents_the_typed_contracts() -> None:
    """The field names are written out literally here, not derived from PartInfo's own
    `model_fields` -- a renamed field, or a route that lost its typed return annotation,
    must fail this test rather than pass tautologically.
    """
    schema = client.get("/openapi.json").json()

    info_response = schema["paths"]["/api/bolt/info"]["get"]["responses"]["200"]
    assert info_response["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/PartInfo"}

    part_info = schema["components"]["schemas"]["PartInfo"]
    keys = {"kind", "rows", "warnings", "designation", "preset", "notes", "downloads",
            "counterpart"}
    assert set(part_info["properties"]) == keys
    assert set(part_info["required"]) == keys
    preset = schema["components"]["schemas"]["PresetMatch"]
    assert set(preset["properties"]) == {"status", "id", "display"}
    assert set(preset["required"]) == {"status", "id", "display"}
    info_row = schema["components"]["schemas"]["InfoRow"]
    assert set(info_row["properties"]) == {"key", "label", "value", "unit", "group"}
    assert set(info_row["required"]) == {"key", "label", "value", "unit", "group"}

    model_route = schema["paths"]["/api/bolt/model.{fmt}"]["get"]
    query_names = {p["name"] for p in model_route["parameters"] if p["in"] == "query"}
    assert query_names == {"d", "pitch", "left_hand", "length", "s", "k", "thread_length",
                           "head_chamfer", "quality"}
    # The download state is pinned to the model route's own enums, read from this document and
    # not typed here, so a route that grows a format or a quality fails this test instead of
    # drifting from the info document (G-04-3).
    route_params = {p["name"]: p["schema"] for p in model_route["parameters"]}
    formats, qualities = route_params["fmt"]["enum"], route_params["quality"]["enum"]
    download = schema["components"]["schemas"]["Download"]
    assert set(download["properties"]) == {"format", "quality", "refusal"}
    assert set(download["required"]) == {"format", "quality", "refusal"}
    assert set(download["properties"]["format"]["enum"]) == set(formats)
    assert set(download["properties"]["quality"]["enum"]) == set(qualities)
    assert part_info["properties"]["downloads"]["items"] == {
        "$ref": "#/components/schemas/Download"}
    listed = [(e["format"], e["quality"]) for e in client.get("/api/bolt/info").json()["downloads"]]
    assert sorted(listed) == sorted((f, q) for f in formats for q in qualities)
    for fmt in formats:
        assert next(q for f, q in listed if f == fmt) == route_params["quality"]["default"]
    # `quality` belongs to the model route only: it is a foreign field on the info route.
    info_route = schema["paths"]["/api/bolt/info"]["get"]
    info_names = {p["name"] for p in info_route["parameters"] if p["in"] == "query"}
    assert info_names == {"d", "pitch", "left_hand", "length", "s", "k", "thread_length",
                           "head_chamfer"}

    presets_response = schema["paths"]["/api/presets"]["get"]["responses"]["200"]
    assert presets_response["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/PresetCatalogue"}
    catalogue_component = schema["components"]["schemas"]["PresetCatalogue"]
    assert set(catalogue_component["required"]) == {"kind", "axes", "rows"}
    entry_component = schema["components"]["schemas"]["PresetEntry"]
    assert set(entry_component["required"]) == {
        "id", "display", "designation", "picker", "fields", "citation"}

    health_response = schema["paths"]["/api/health"]["get"]["responses"]["200"]
    assert health_response["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/HealthReport"}
    health_component = schema["components"]["schemas"]["HealthReport"]
    assert set(health_component["required"]) == {"status", "version", "pool"}
    pool_component = schema["components"]["schemas"]["PoolState"]
    assert set(pool_component["required"]) == {
        "workers", "queue_available", "workers_replaced"}


def test_an_iso_4014_match_and_a_non_row_part_over_the_wire() -> None:
    # INFO-03: the row values travel only for an exact match; the wire says so in one warning.
    bolt = client.get("/api/bolt/info", params={
        "d": 10, "pitch": 1.5, "length": 80, "s": 16, "k": 6.4, "thread_length": 26}).json()
    by_key = {row["key"]: row for row in bolt["rows"]}
    assert {"b", "lg_max", "ls_min"} <= set(by_key)
    assert by_key["b"]["group"] == by_key["ls_min"]["group"] == "Shank and thread"
    assert by_key["b"]["label"].startswith("Thread length b, ref (ISO 4014:2022 ")
    custom = client.get("/api/bolt/info", params={"pitch": 0.75}).json()
    assert custom["warnings"][1:] == [
        "no ISO 4014:2022 or ISO 4017:2022 row matches these fields; row values not reported",
        "no GOST ISO 4032-2014 (ISO 4032:2012) row for d 6 pitch 0.75; set s and m on the nut"]
    assert {"s_min", "b"}.isdisjoint(row["key"] for row in custom["rows"])
    assert bolt["notes"] == ["product grade A (ISO 4014:2022: l ≤ 150 mm and l ≤ 10 d)",
                             "wrench size 16 mm (ISO 4014:2022); the withdrawn DIN 931 used 17 mm"]
    assert custom["notes"] == []


def test_the_default_info_document() -> None:
    r = client.get("/api/bolt/info")
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "bolt"
    assert [row["key"] for row in body["rows"]] == [
        "d", "pitch", "length", "thread_length", "shank_length", "turns", "thread_depth",
        "minor_diameter", "pitch_diameter", "d_max", "d_min", "d2_max", "d2_min", "s",
        "across_corners", "k", "s_min", "e_min", "k_max", "k_min", "dw_min", "head_chamfer",
        "chamfer_depth", "chamfer_circle_diameter", "corner_edge_left", "volume"]
    # INFO-02: the heading is one ASCII string, compared with `==` and not by substring.
    assert [row["group"] for row in body["rows"]] == (
        ["Shank and thread"] * 9
        + ["limits for a bought part; this model is nominal and not toleranced"] * 4
        + ["Head"] * 12 + ["Part"])
    values = {row["key"]: row["value"] for row in body["rows"]}
    assert values["d"] == 6.0
    assert values["pitch"] == 1.0
    assert values["length"] == 20.0
    assert values["turns"] == 20.0
    assert (values["thread_length"], values["shank_length"]) == (20.0, 0.0)
    assert (values["s"], values["k"]) == (10.0, 4.0)
    assert values["across_corners"] == 10.0 / math.cos(math.pi / 6)
    assert values["volume"] == bolt_end_closed_volume(
        6.0, 1.0, 20.0, 10.0, 4.0, 20.0, True, None, 30.0)
    assert body["warnings"][0] == STANDING_WARNING
    assert body["preset"] == {"status": "exact", "id": "iso4017:M6x20",
                              "display": "ISO 4017 M6 \u00d7 20"}
    assert body["designation"] == "Hexagon head screw ISO 4017 - M6 x 20"


def test_a_sharp_head_info_document_has_the_note_and_no_chamfer_rows() -> None:
    body = client.get("/api/bolt/info", params={"head_chamfer": 0}).json()
    keys = [row["key"] for row in body["rows"]]
    assert {"head_chamfer", "chamfer_depth", "chamfer_circle_diameter",
            "corner_edge_left"}.isdisjoint(keys)
    assert [row["group"] for row in body["rows"]].count("Head") == 8
    assert body["notes"][-1] == (
        "sharp hex head corners: head_chamfer 0 cuts no top chamfer (L19)")
    assert body["notes"][-1] not in body["warnings"]


def test_a_part_matching_no_row_is_custom_on_the_wire() -> None:
    body = client.get("/api/bolt/info", params={"s": 10.5}).json()
    assert body["preset"] == {"status": "custom", "id": None, "display": None}
    assert body["designation"] is None


def test_a_length_below_the_default_thread_is_a_200_with_the_default_warning_never_a_422() -> None:
    # D-08: `?length=10` is a 10 mm full-thread screw and the page says why.
    r = client.get("/api/bolt/info", params={"length": 10})
    assert r.status_code == 200
    body = r.json()
    assert body["warnings"][1] == (
        "thread_length 20 (default) exceeds length 10: thread built to the full length")
    values = {row["key"]: row["value"] for row in body["rows"]}
    assert (values["thread_length"], values["shank_length"]) == (10.0, 0.0)


def test_an_iso_4014_shaped_bolt_reports_its_thread_and_its_shank() -> None:
    r = client.get("/api/bolt/info", params={"length": 30, "thread_length": 18})
    assert r.status_code == 200
    values = {row["key"]: row["value"] for row in r.json()["rows"]}
    assert (values["thread_length"], values["shank_length"]) == (18.0, 12.0)
    assert values["turns"] == 18.0
    assert values["volume"] == bolt_end_closed_volume(
        6.0, 1.0, 30.0, 10.0, 4.0, 18.0, True, 0.25, 30.0)


@pytest.mark.parametrize("route", ["/api/bolt/info", "/api/bolt/model.stl"])
@pytest.mark.parametrize("field", ["d", "pitch", "length", "s", "k", "thread_length"])
@pytest.mark.parametrize("value", ["0", "-1", "inf", "nan", "text"])
def test_each_field_refuses_zero_negative_infinite_nan_and_text(
        route: str, field: str, value: str) -> None:
    query: Params = {field: value}
    if route.endswith(".stl"):
        query["quality"] = "preview"
    r = client.get(route, params=query)
    assert r.status_code == 422
    assert r.json()["detail"][0]["loc"] == ["query", field]


@pytest.mark.parametrize("route", ["/api/bolt/info", "/api/bolt/model.stl"])
def test_a_foreign_field_is_a_422_naming_it(route: str) -> None:
    r = client.get(route, params={"m": 5})
    assert r.status_code == 422
    detail = r.json()["detail"][0]
    assert detail["type"] == "extra_forbidden"
    assert detail["loc"] == ["query", "m"]


def test_quality_is_a_foreign_field_on_the_info_route() -> None:
    """`quality` tessellates a download; the info document has no use for it, so asking
    for it there is a 422 naming it rather than a silently ignored field (L02)."""
    r = client.get("/api/bolt/info", params={"quality": "preview"})
    assert r.status_code == 422
    detail = r.json()["detail"][0]
    assert detail["type"] == "extra_forbidden"
    assert detail["loc"] == ["query", "quality"]


# The walls of L20 (typed from the records: tests/test_oper_followup.py recomputes them): the field,
# the value at the wall, and the other fields that make that corner a valid part.
WALLS: list[tuple[str, str, float, Params]] = [
    ("bolt", "d", 999.999, {"s": 1000.0}),
    ("bolt", "length", 1e4, {}),
    ("bolt", "s", 1000.0, {}),
    ("bolt", "k", 1e5, {}),
    ("bolt", "thread_length", 1e5, {}),
    ("nut", "s", 1000.0, {}),
    ("nut", "m", 1e4, {"d": 200.0, "pitch": 114.0, "s": 300.0}),
    ("nut", "clearance", 496.999, {"s": 1000.0}),
]


@pytest.mark.parametrize(("kind", "field", "bound", "extra"), WALLS)
def test_each_field_wall_is_inclusive_and_the_next_float_is_a_422_naming_the_field(
        kind: str, field: str, bound: float, extra: Params) -> None:
    assert client.get(f"/api/{kind}/info", params={**extra, field: bound}).status_code == 200
    refused = client.get(f"/api/{kind}/info",
                         params={**extra, field: math.nextafter(bound, math.inf)})
    assert refused.status_code == 422
    [detail] = refused.json()["detail"]
    assert detail["loc"] == ["query", field]
    assert detail["type"] == "less_than_equal"


def test_the_nut_d_has_no_wall_of_its_own_and_stays_under_the_shared_one() -> None:
    # G27: nut d is bounded by MAX_FIELD_MM (1e3) and by the cost model, not by a measured wall.
    assert client.get("/api/nut/info", params={"d": 999.699, "s": 1000.0}).status_code == 200
    refused = client.get("/api/nut/info", params={"d": math.nextafter(1000.0, math.inf)})
    assert refused.status_code == 422
    assert refused.json()["detail"][0]["loc"] == ["query", "d"]


def test_a_part_at_the_walls_is_served_by_the_model_route_and_one_past_is_not() -> None:
    seen: list[FastenerParams] = []

    async def stub(p: FastenerParams, fmt: str, quality: str) -> bytes:
        # The model route is exercised with a backend that records what it was asked for and
        # returns the default part's preview: these parts are walls, not meshes to build.
        seen.append(p)
        return export(BoltParams(), "stl", "preview")

    at_wall: Params = {"length": 1e4, "s": 1000.0, "d": 999.999, "k": 1e5}
    with _backend(stub):
        r = client.get("/api/bolt/model.stl", params={**at_wall, "quality": "preview"})
    assert r.status_code == 200
    assert isinstance(seen[-1], BoltParams)
    assert (seen[-1].length, seen[-1].s, seen[-1].d, seen[-1].k) == (1e4, 1000.0, 999.999, 1e5)
    over: Params = {**at_wall, "length": math.nextafter(1e4, math.inf)}
    for route in ("/api/bolt/info", "/api/bolt/model.stl"):
        refused = client.get(route, params={**over, "quality": "preview"}
                             if route.endswith(".stl") else over)
        assert refused.status_code == 422
        assert refused.json()["detail"][0]["loc"] == ["query", "length"]


def test_a_bolt_at_the_d_wall_with_a_default_head_is_head_too_small() -> None:
    # s is bounded by 1e3, which is above the d wall, so the head must be wider than the shank
    # (D-23); the 422 names both fields and does not hide behind the field wall.
    for route in ("/api/bolt/info", "/api/bolt/model.stl"):
        query: Params = {"d": 999.999}
        refused = client.get(route, params={**query, "quality": "preview"}
                             if route.endswith(".stl") else query)
        assert refused.status_code == 422, route
        detail = refused.json()["detail"][0]
        assert detail["type"] == "head_too_small"
        assert detail["ctx"]["fields"] == ["s", "d"]
        assert detail["msg"].startswith("s and d: ")


def test_a_huge_d_is_refused_before_it_overflows_a_volume() -> None:
    # 1e200 overflows a float on the way to a volume (F2); the wall refuses it first.
    huge = client.get("/api/bolt/info", params={"d": 1e200})
    assert huge.status_code == 422
    assert huge.json()["detail"][0]["loc"] == ["query", "d"]


@pytest.mark.parametrize("route", ["/api/bolt/info", "/api/bolt/model.stl"])
@pytest.mark.parametrize(("query", "kind", "fields"), [
    ({"pitch": 6}, "pitch_too_coarse", ["d", "pitch"]),
    ({"pitch": 5.53}, "pitch_too_coarse", ["d", "pitch"]),   # root 0.0069 mm, under the floor
    ({"pitch": 1e300}, "pitch_too_coarse", ["d", "pitch"]),
    ({"length": 300, "thread_length": 300}, "turn_cap", ["thread_length", "length", "pitch"]),
    # length / pitch is past the float range: a 422, not the 500 an OverflowError gave (CR-01)
    ({"pitch": 5e-324}, "turn_cap", ["thread_length", "length", "pitch"]),
    ({"pitch": 1e-310, "length": 1e4}, "turn_cap", ["thread_length", "length", "pitch"]),
])
def test_a_thread_that_cannot_be_made_or_was_never_measured_is_a_422_naming_both_fields(
        route: str, query: Params, kind: str, fields: list[str]) -> None:
    # `ctx.fields` is what app.js problems() highlights; the bolt routes refuse before any build.
    if route.endswith(".stl"):
        query = {**query, "quality": "preview"}
    r = client.get(route, params=query)
    assert r.status_code == 422
    [detail] = r.json()["detail"]
    assert detail["type"] == kind
    assert detail["loc"] == ["query"]
    assert detail["ctx"]["fields"] == fields
    named = ", ".join(fields[:-1]) + " and " + fields[-1]
    assert detail["msg"].startswith(named + ": ")


def test_a_pitch_one_float_past_the_root_floor_is_a_422_naming_d_and_pitch() -> None:
    from screw.calc.thread import MIN_ROOT_RADIUS_MM, root_radius_refusal, thread_depth

    pitch = (6.0 / 2 - MIN_ROOT_RADIUS_MM) / thread_depth(1.0)
    while root_radius_refusal(6.0, pitch) is not None:
        pitch = math.nextafter(pitch, 0.0)
    while root_radius_refusal(6.0, math.nextafter(pitch, math.inf)) is None:
        pitch = math.nextafter(pitch, math.inf)
    # exactly at the floor: served (OPER-03, the adjacency edge); one float above: refused
    assert client.get("/api/bolt/info", params={"pitch": pitch}).status_code == 200
    r = client.get("/api/bolt/info", params={"pitch": math.nextafter(pitch, math.inf)})
    assert r.status_code == 422
    [detail] = r.json()["detail"]
    assert detail["type"] == "pitch_too_coarse"
    assert detail["ctx"]["fields"] == ["d", "pitch"]
    assert detail["msg"].startswith("d and pitch: ")
    assert "must be at least 0.01 mm" in detail["msg"]


@pytest.mark.parametrize("route", ["/api/bolt/info", "/api/bolt/model.stl"])
def test_a_head_no_wider_than_the_shank_is_a_422_naming_s_and_d(route: str) -> None:
    for s in (6.0, 5.0):
        r = client.get(route, params={"s": s, "quality": "preview"} if route.endswith(".stl")
                       else {"s": s})
        assert r.status_code == 422, (route, s)
        [detail] = r.json()["detail"]
        assert detail["type"] == "head_too_small"
        assert detail["loc"] == ["query"]
        assert detail["ctx"]["fields"] == ["s", "d"]
        assert detail["msg"].startswith("s and d: ")


def test_a_head_one_ulp_wider_than_the_shank_is_served() -> None:
    s = math.nextafter(6.0, math.inf)
    assert client.get("/api/bolt/info", params={"s": s}).status_code == 200


def test_a_solid_the_kernel_gets_wrong_is_a_422_build_error() -> None:
    """These parameters pass validation (a root radius of 0.0123 mm, above the 0.01 mm floor) and
    build one valid solid whose volume is off the closed form (-1.829e-04); the gate turns that
    into a BuildError, not a served file."""
    r = client.get("/api/bolt/model.stl", params={
        "d": 0.03, "pitch": 0.005, "length": 0.05, "quality": "preview"})
    assert r.status_code == 422
    detail = r.json()["detail"][0]
    assert detail["type"] == "build_error"
    assert detail["loc"] == ["query"]
    assert "relative error" in detail["msg"]


def test_the_default_part_served_is_the_gated_hex_head_screw(tmp_path: Path) -> None:
    r = client.get("/api/bolt/model.step")
    assert r.status_code == 200
    path = tmp_path / "default.step"
    path.write_bytes(r.content)
    shape = cq.importers.importStep(str(path)).val()
    assert isinstance(shape, cq.Shape)
    assert len(shape.Solids()) == 1
    assert precise_volume(shape) == pytest.approx(
        bolt_end_closed_volume(6.0, 1.0, 20.0, 10.0, 4.0, 20.0, True, None, 30.0), rel=T_GATE)


def test_the_download_filename_is_safe_for_many_digit_values() -> None:
    # pitch=1e300 used to be the extreme case here; a thread of that pitch has a negative root
    # radius, so many digits stand in for it (plan 03-02 makes the extreme a 422).
    r = client.get("/api/bolt/model.stl", params={
        "d": 6.123456789, "pitch": 0.987654321, "length": 9.87654321, "quality": "preview"})
    assert r.status_code == 200
    match = re.fullmatch(r'attachment; filename="([^"]*)"', r.headers["content-disposition"])
    assert match, r.headers["content-disposition"]
    assert re.fullmatch(r"[A-Za-z0-9_.+-]+", match.group(1))


@pytest.mark.parametrize(("fmt", "ctype", "magic"), [
    ("stl", "model/stl", None),
    ("step", "model/step", b"ISO-10303-21;"),
])
def test_model_download(fmt: str, ctype: str, magic: bytes | None) -> None:
    r = client.get(f"/api/bolt/model.{fmt}", params={"quality": "preview", "d": 8})
    assert r.status_code == 200
    assert r.headers["content-type"] == ctype
    # D-22: the preview STL names its quality; the STEP keeps the plain slug.
    name = "_preview.stl" if fmt == "stl" else ".step"
    assert r.headers["content-disposition"] == (
        'attachment; filename="bolt_d8_pitch1_left_hand0_length20_s10_k4_'
        f'thread_length20_head_chamfer30{name}"')
    if magic:
        assert r.content.startswith(magic)


def test_unknown_format_is_rejected() -> None:
    assert client.get("/api/bolt/model.obj").status_code == 422


def test_a_head_chamfer_of_90_is_a_422_naming_the_field() -> None:
    r = client.get("/api/bolt/info", params={"head_chamfer": 90})
    assert r.status_code == 422
    assert r.json()["detail"][0]["loc"] == ["query", "head_chamfer"]


def test_bad_type_is_422_on_the_field() -> None:
    r = client.get("/api/bolt/info", params={"d": "wide"})
    assert r.status_code == 422
    assert r.json()["detail"][0]["loc"] == ["query", "d"]


def test_a_left_hand_bolt_downloads_under_its_own_filename_and_is_not_the_right_hand_mesh() -> None:
    left = client.get("/api/bolt/model.stl", params={"left_hand": "true", "quality": "preview"})
    assert left.status_code == 200
    assert left.headers["content-disposition"] == (
        'attachment; filename="bolt_d6_pitch1_left_hand1_length20_s10_k4_'
        'thread_length20_head_chamfer30_preview.stl"')
    right = client.get("/api/bolt/model.stl", params={"quality": "preview"})
    assert right.headers["content-disposition"].endswith(
        'left_hand0_length20_s10_k4_thread_length20_head_chamfer30_preview.stl"')
    # The bytes of the left-hand solid the handedness probe proves left-handed
    # (tests/test_solid.py), and not of the right-hand one.
    assert left.content == export(BoltParams(left_hand=True), "stl", "preview")
    assert left.content != right.content


def test_left_hand_that_is_not_a_boolean_is_a_422_on_the_field() -> None:
    for route in ("/api/bolt/info", "/api/bolt/model.stl"):
        r = client.get(route, params={"left_hand": "banana"})
        assert r.status_code == 422, route
        assert r.json()["detail"][0]["loc"] == ["query", "left_hand"], route


@pytest.mark.parametrize("query", [
    "d=0&d=5",                  # the first value alone would be a 422, the last alone a 200
    "d=5&d=100000",             # the first alone is fine; the last alone is head_too_small (D-23)
    "d=5&d=0",                  # the last value alone would be a 422
])
def test_a_repeated_key_is_a_422_duplicate_not_a_judgement_of_either_value(query: str) -> None:
    r = client.get(f"/api/bolt/info?{query}")
    assert r.status_code == 422
    assert r.json()["detail"][0] == {
        "loc": ["query", "d"], "type": "duplicate", "msg": "d was given more than once."}


def test_a_repeated_key_on_the_schema_route_is_a_duplicate_not_a_404() -> None:
    r = client.get("/api/schema?kind=bolt&kind=x")
    assert r.status_code == 422
    assert r.json()["detail"][0]["loc"] == ["query", "kind"]
    assert r.json()["detail"][0]["type"] == "duplicate"


def test_a_repeated_left_hand_and_a_repeated_foreign_key_are_duplicates_too() -> None:
    r = client.get("/api/bolt/model.stl?left_hand=true&left_hand=false&quality=preview")
    assert r.status_code == 422
    assert r.json()["detail"][0]["loc"] == ["query", "left_hand"]
    assert r.json()["detail"][0]["type"] == "duplicate"
    r = client.get("/api/bolt/info?zz=1&zz=2")
    assert r.status_code == 422
    assert r.json()["detail"][0]["loc"] == ["query", "zz"]
    assert r.json()["detail"][0]["type"] == "duplicate"


def test_every_repeated_key_is_named_in_first_seen_order() -> None:
    r = client.get("/api/bolt/info?pitch=1&d=5&pitch=2&d=6&length=3")
    assert [e["loc"] for e in r.json()["detail"]] == [["query", "pitch"], ["query", "d"]]


def test_a_saturated_service_refuses_instead_of_queueing() -> None:
    """A queue deeper than the pool can drain is latency with no payoff."""
    with _saturated():
        r = client.get("/api/bolt/model.stl", params={"quality": "preview", "d": 7.2})
    assert r.status_code == 503
    assert r.headers["retry-after"] == "5"
    detail = r.json()["detail"][0]
    assert detail["type"] == "busy"
    assert "parts" in detail["msg"]


def test_a_saturated_service_emits_queue_refused_naming_the_part_and_the_ceiling(
        caplog: pytest.LogCaptureFixture) -> None:
    """A refusal says which part was turned away and how close to the ceiling the service
    was, at WARNING -- capacity, not breakage."""
    caplog.set_level(logging.INFO)
    # The semaphore is exhausted directly, not through _build_slot, so the parent's own
    # `_in_flight_builds` counter is whatever it already reads (0 here, since no real slot
    # holder incremented it) -- captured, not hardcoded, so the assertion checks the record
    # against the module's own counter and not a value this test happens to expect.
    in_flight_before = app_module._in_flight_builds
    with _saturated():
        r = client.get("/api/bolt/model.stl", params={"quality": "preview", "d": 7.3})
    assert r.status_code == 503
    assert caplog.records  # an empty caplog would pass with nothing proven

    refused = _event_records(caplog, "queue.refused")
    assert len(refused) == 1
    assert refused[0].levelno == logging.WARNING
    assert _field(refused[0], "request")
    assert _field(refused[0], "kind") == "bolt"
    assert _field(refused[0], "slug") == (
        "bolt_d7.3_pitch1_left_hand0_length20_s10_k4_thread_length20_head_chamfer30")
    assert _field(refused[0], "in_flight") == in_flight_before
    assert _field(refused[0], "max_queued") == app_module.MAX_QUEUED_BUILDS

    assert not _event_records(caplog, "export.served")
    assert not _event_records(caplog, "build.started")
    # The catch-all `except Exception` in _serve() must not also fire for _build_slot()'s
    # own admission-control HTTPException: that would duplicate this queue.refused record
    # as a spurious build.failed one.
    assert not _event_records(caplog, "build.failed")


def test_max_queued_builds_is_derived_from_build_workers(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """One knob moves both, so a deployer cannot configure a queue deeper than the pool
    can drain -- SCREW_MAX_QUEUED_BUILDS still overrides the derivation when set."""
    monkeypatch.delenv("SCREW_BUILD_WORKERS", raising=False)
    monkeypatch.delenv("SCREW_MAX_QUEUED_BUILDS", raising=False)
    assert app_module._max_queued_builds() == 4  # 2 x the default 2 workers

    monkeypatch.setenv("SCREW_BUILD_WORKERS", "3")
    assert app_module._max_queued_builds() == 6

    monkeypatch.setenv("SCREW_MAX_QUEUED_BUILDS", "1")
    assert app_module._max_queued_builds() == 1  # explicit override still wins


def test_the_export_cache_refuses_a_blob_bigger_than_its_budget() -> None:
    """A _BlobCache never reports a stored size above its budget."""
    cache = app_module._BlobCache(budget=10)
    cache.put("fits", b"12345")
    assert cache.get("fits") == b"12345"

    cache.put("too_big", b"x" * 20)
    assert cache.get("too_big") is None


def test_a_second_identical_download_is_served_from_the_byte_cache() -> None:
    """The parent's byte cache means a repeat download never reaches a worker, and the
    bytes are the same bytes (idempotency)."""
    calls = 0

    async def counting_backend(p: FastenerParams, fmt: str, quality: str) -> bytes:
        nonlocal calls
        calls += 1
        return export(p, cast(Format, fmt), cast(Quality, quality))

    params: Params = {"quality": "preview", "d": 7.4}
    with _backend(counting_backend):
        first = client.get("/api/bolt/model.stl", params=params)
        second = client.get("/api/bolt/model.stl", params=params)

    assert first.status_code == second.status_code == 200
    assert first.content == second.content
    assert calls == 1


def test_a_gzip_client_gets_compressed_bytes_an_identity_client_gets_the_raw_file() -> None:
    """One encoding's bytes must never be served under another's label."""
    params: Params = {"quality": "preview", "d": 7.5}

    gzip_resp = client.get("/api/bolt/model.stl", params=params)
    assert gzip_resp.status_code == 200
    assert gzip_resp.headers["content-encoding"] == "gzip"
    assert "accept-encoding" in gzip_resp.headers["vary"].lower()

    identity_resp = client.get("/api/bolt/model.stl", params=params,
                               headers={"Accept-Encoding": "identity"})
    assert identity_resp.status_code == 200
    assert "content-encoding" not in identity_resp.headers
    assert not identity_resp.content.startswith(b"\x1f\x8b")  # not gzip magic: a raw STL

    # httpx decodes the gzip response transparently: decoded bytes must equal the identity
    # bytes exactly, or a client silently gets the wrong part.
    assert gzip_resp.content == identity_resp.content


def test_a_part_is_compressed_once_per_cache_fill_not_once_per_download(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """A repeat gzip download must hit the cached compressed bytes, not recompress."""
    calls = 0
    original = app_module._gzip

    def counting_gzip(data: bytes) -> bytes:
        nonlocal calls
        calls += 1
        return original(data)

    monkeypatch.setattr(app_module, "_gzip", counting_gzip)

    params: Params = {"quality": "preview", "d": 7.6}
    first = client.get("/api/bolt/model.stl", params=params)
    second = client.get("/api/bolt/model.stl", params=params)

    assert first.status_code == second.status_code == 200
    assert first.content == second.content
    assert calls == 1


def test_a_cache_hit_that_still_needs_compressing_goes_through_admission_control() -> None:
    """The part is already built; only the compression itself can refuse this request --
    exactly the property a naive cache-hit-bypasses-the-slot implementation would fail to
    deliver."""
    params: Params = {"quality": "preview", "d": 7.7}

    # Warm only the raw bytes.
    warm = client.get("/api/bolt/model.stl", params=params,
                      headers={"Accept-Encoding": "identity"})
    assert warm.status_code == 200

    with _saturated():
        r = client.get("/api/bolt/model.stl", params=params)
    assert r.status_code == 503
    assert r.headers["retry-after"] == "5"
    assert r.json()["detail"][0]["type"] == "busy"


def test_an_already_compressed_download_needs_no_slot_at_all() -> None:
    """Once a part's gzip bytes are cached, a repeat download takes zero slots."""
    params: Params = {"quality": "preview", "d": 7.8}

    first = client.get("/api/bolt/model.stl", params=params)
    assert first.status_code == 200
    assert first.headers["content-encoding"] == "gzip"

    with _saturated():
        r = client.get("/api/bolt/model.stl", params=params)
    assert r.status_code == 200


def test_a_fresh_build_emits_build_started_then_export_served_with_source_built(
        caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    r = client.get("/api/bolt/model.stl", params={"quality": "preview", "d": 7.1})
    assert r.status_code == 200
    assert caplog.records  # an empty caplog would pass with nothing proven

    started = _event_records(caplog, "build.started")
    assert started
    served = _event_records(caplog, "export.served")
    assert len(served) == 1
    assert _field(served[0], "source") == "built"
    assert _field(served[0], "request")
    # Every per-request record names the kind, the slug and only the non-default params.
    for record in (started[0], served[0]):
        assert _field(record, "kind") == "bolt"
        assert _field(record, "slug") == (
            "bolt_d7.1_pitch1_left_hand0_length20_s10_k4_thread_length20_head_chamfer30")
        assert _field(record, "params") == {"d": 7.1}


def test_a_repeat_download_is_served_from_cache_with_zero_duration_and_no_build_started(
        caplog: pytest.LogCaptureFixture) -> None:
    params: Params = {"quality": "preview", "d": 7.9}
    client.get("/api/bolt/model.stl", params=params)  # warm the byte cache

    caplog.clear()
    caplog.set_level(logging.INFO)
    r = client.get("/api/bolt/model.stl", params=params)
    assert r.status_code == 200
    assert caplog.records

    assert not _event_records(caplog, "build.started")
    served = _event_records(caplog, "export.served")
    assert len(served) == 1
    assert _field(served[0], "source") == "cache"
    assert _field(served[0], "duration_ms") == 0


def test_a_gzip_request_after_an_identity_download_emits_source_compressed(
        caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    """Raw bytes are already cached; only this encoding is not -- gzip runs inside the
    slot and the record says so, with the time it actually took (a cache hit reports 0).

    gzip of a skeleton cylinder's few-KB STL finishes in well under half a millisecond,
    which `_ms` rounds to 0 -- indistinguishable from a cache hit. spur's gear meshes were
    megabytes, so the real compressor sufficed there; here a fixed 20 ms delay stands in
    for a large part, and the assertion is that the duration is measured, not hardcoded.
    """
    original = app_module._gzip

    def slow_gzip(data: bytes) -> bytes:
        time.sleep(0.02)
        return original(data)

    monkeypatch.setattr(app_module, "_gzip", slow_gzip)
    params: Params = {"quality": "preview", "d": 8.1}
    client.get("/api/bolt/model.stl", params=params, headers={"Accept-Encoding": "identity"})

    caplog.clear()
    caplog.set_level(logging.INFO)
    r = client.get("/api/bolt/model.stl", params=params)
    assert r.status_code == 200
    assert caplog.records

    served = _event_records(caplog, "export.served")
    assert len(served) == 1
    assert _field(served[0], "source") == "compressed"
    duration_ms = _field(served[0], "duration_ms")
    assert isinstance(duration_ms, int)
    assert duration_ms >= 20


def test_an_all_default_part_logs_params_as_an_empty_object_not_omitted(
        caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    r = client.get("/api/bolt/model.stl", params={"quality": "preview"})
    assert r.status_code == 200
    assert caplog.records

    served = _event_records(caplog, "export.served")
    assert len(served) == 1
    assert _field(served[0], "params") == {}
    assert _field(served[0], "kind") == "bolt"
    assert _field(served[0], "slug") == (
        "bolt_d6_pitch1_left_hand0_length20_s10_k4_thread_length20_head_chamfer30")


def test_two_requests_for_one_part_get_two_different_request_ids(
        caplog: pytest.LogCaptureFixture) -> None:
    """Two concurrent requests for the same part are the one case params + time cannot
    disambiguate (same-slot affinity)."""
    caplog.set_level(logging.INFO)
    params: Params = {"quality": "preview", "d": 8.2}
    client.get("/api/bolt/model.stl", params=params)
    client.get("/api/bolt/model.stl", params=params)
    assert caplog.records  # an empty caplog would pass with nothing proven

    served = _event_records(caplog, "export.served")
    assert len(served) == 2
    assert _field(served[0], "request") != _field(served[1], "request")


@pytest.mark.parametrize(("exc", "want_level", "want_exception", "want_status", "want_type"), [
    (BuildError("Geometry kernel failed (Standard_Failure); "
                "check d, pitch, left_hand, length, s, k and thread_length."),
     logging.WARNING, "BuildError", 422, "build_error"),
    (BuildTimeout("Build exceeded the 30s per-build timeout."),
     logging.ERROR, "BuildTimeout", 503, "timeout"),
    (BrokenProcessPool("worker died"),
     logging.ERROR, "BrokenProcessPool", 503, "pool_broken"),
])
def test_a_failed_build_emits_build_failed_naming_the_class_and_the_level(
        caplog: pytest.LogCaptureFixture, exc: Exception, want_level: int,
        want_exception: str, want_status: int, want_type: str) -> None:
    """The level says whose fault it is -- BuildError (the user's part, 422) is a WARNING,
    the two 503 classes are ERROR -- and the status and `type` say what the client may do:
    change the part (422) or come back (503, with Retry-After). Neither is a 500.
    tests/test_pool.py proves the real pool never lets a same-slot timeout reach here as
    anything else.
    """
    caplog.set_level(logging.INFO)

    async def backend(p: FastenerParams, fmt: str, quality: str) -> bytes:
        raise exc

    # d=8.3: a diameter no other test in this suite downloads successfully, so the shared
    # byte cache can never short-circuit this request before the raising backend runs.
    with _backend(backend):
        r = client.get("/api/bolt/model.stl", params={"quality": "preview", "d": 8.3})
    assert r.status_code == want_status
    assert r.json()["detail"][0]["type"] == want_type
    if want_status == 503:
        assert r.headers["retry-after"] == "5"
    assert caplog.records  # an empty caplog would pass with nothing proven

    failed = _event_records(caplog, "build.failed")
    assert len(failed) == 1
    assert failed[0].levelno == want_level
    assert _field(failed[0], "exception") == want_exception
    assert _field(failed[0], "request")
    assert _field(failed[0], "kind") == "bolt"
    assert _field(failed[0], "slug") == (
        "bolt_d8.3_pitch1_left_hand0_length20_s10_k4_thread_length20_head_chamfer30")
    assert _field(failed[0], "params") == {"d": 8.3}
    assert _field(failed[0], "duration_ms") is not None

    assert not _event_records(caplog, "export.served")


def test_an_unclassified_exception_still_emits_build_failed_and_is_not_swallowed(
        caplog: pytest.LogCaptureFixture) -> None:
    """_serve()'s three except clauses cover BuildError, BuildTimeout and BrokenProcessPool;
    anything else (`_gzip()` under memory pressure, or a future violation of the solid
    package's "BuildError is the only exception that escapes" contract) would otherwise
    propagate with no build.failed record at all. The catch-all must log then re-raise, not
    swallow -- the unhandled-error path still has to serve the response, so this drives the
    exception through `pytest.raises`, not a status-code assertion."""
    caplog.set_level(logging.INFO)

    async def backend(p: FastenerParams, fmt: str, quality: str) -> bytes:
        raise MemoryError("out of memory compressing bytes")

    # d=8.4: unused by any other test (see the d=8.3 comment above).
    with _backend(backend), pytest.raises(MemoryError):
        client.get("/api/bolt/model.stl", params={"quality": "preview", "d": 8.4})
    assert caplog.records  # an empty caplog would pass with nothing proven

    failed = _event_records(caplog, "build.failed")
    assert len(failed) == 1
    assert failed[0].levelno == logging.ERROR  # unrecognised class -> the service's fault
    assert _field(failed[0], "exception") == "MemoryError"
    assert _field(failed[0], "request")
    assert _field(failed[0], "slug")
    assert _field(failed[0], "duration_ms") is not None

    assert not _event_records(caplog, "export.served")


@pytest.mark.parametrize(("url", "want_artifact"), [
    ("/api/bolt/model.stl?quality=preview&d=8.6", "stl-preview"),
    ("/api/bolt/model.stl?quality=fine&d=8.6", "stl-fine"),
    ("/api/bolt/model.step?d=8.6", "step"),
])
def test_a_timed_out_admitted_part_is_logged_as_a_cost_model_miss_and_never_cached(
        caplog: pytest.LogCaptureFixture, url: str, want_artifact: str) -> None:
    """The timeout is the backstop behind the cost model (D-10): an admitted part that still
    overruns is the model's miss, so the server records the part and the seconds it was held
    to, at ERROR (the service's fault), next to the unchanged 503 `timeout` the client gets.
    Nothing is cached for it, so the same request builds again.
    """
    caplog.set_level(logging.INFO)
    calls = 0

    async def backend(p: FastenerParams, fmt: str, quality: str) -> bytes:
        nonlocal calls
        calls += 1
        raise BuildTimeout("Build exceeded its 30s per-build timeout.")

    # d=8.6: a diameter no other test in this suite downloads (see the d=8.3 comment above).
    with _backend(backend):
        r = client.get(url)
        assert r.status_code == 503
        assert r.json()["detail"][0]["type"] == "timeout"
        assert r.headers["retry-after"] == "5"
        assert caplog.records  # an empty caplog would pass with nothing proven

        failed = _event_records(caplog, "build.failed")
        misses = _event_records(caplog, "cost_model.miss")
        assert len(failed) == 1
        assert len(misses) == 1
        miss = misses[0]
        assert miss.levelno == logging.ERROR
        assert _field(miss, "request") == _field(failed[0], "request")
        assert _field(miss, "kind") == "bolt"
        assert _field(miss, "params") == {"d": 8.6}
        assert _field(miss, "fmt") == ("step" if want_artifact == "step" else "stl")
        assert _field(miss, "artifact") == want_artifact
        assert _field(miss, "timeout_s") == BUILD_TIMEOUT_S[cast(Artifact, want_artifact)]
        assert not _event_records(caplog, "export.served")

        client.get(url)
    assert calls == 2


@pytest.mark.parametrize("exc", [
    BuildError("flank too small for this bore"),
    BrokenProcessPool("worker died"),
], ids=["build_error", "broken_pool"])
def test_a_failure_other_than_a_timeout_is_not_a_cost_model_miss(
        caplog: pytest.LogCaptureFixture, exc: Exception) -> None:
    caplog.set_level(logging.INFO)

    async def backend(p: FastenerParams, fmt: str, quality: str) -> bytes:
        raise exc

    with _backend(backend):
        client.get("/api/bolt/model.stl", params={"quality": "fine", "d": 8.7})
    assert _event_records(caplog, "build.failed")  # the failure was logged, as a failure
    assert not _event_records(caplog, "cost_model.miss")


@pytest.mark.parametrize(("route", "query"), [
    ("model.stl", {"length": 1e-8, "quality": "preview"}),
    ("model.stl", {"length": 1e-9, "quality": "preview"}),
    ("model.step", {"length": 1e-8}),
])
def test_a_length_too_short_to_model_is_a_422_build_error_not_a_served_file(
        route: str, query: Params) -> None:
    # The collapsed-solid blocker's own reproductions. They used to be a 134-byte STL as a 200,
    # a non-watertight mesh, a one-face STEP and a 500; the builder's doorway now refuses them
    # (D-17) before the kernel runs, so no worker dies on them either.
    r = client.get(f"/api/bolt/{route}", params=query)
    assert r.status_code == 422
    detail = r.json()["detail"][0]
    assert detail["type"] == "build_error"
    assert "length" in detail["msg"]


def test_a_tiny_head_chamfer_is_a_422_build_error_or_a_200_never_a_500() -> None:
    # 06.1 D-18: 5e-324 degrees has no honest oracle, so the build is refused; 1e-6 either builds
    # inside both gates or is refused by name, and neither is a server error.
    refused = client.get("/api/bolt/model.stl", params={
        "head_chamfer": 5e-324, "quality": "preview"})
    assert refused.status_code == 422
    assert refused.json()["detail"][0]["type"] == "build_error"
    # WR-01: the oracle refuses before the kernel runs, and the message does not blame the kernel.
    assert "Geometry kernel failed" not in refused.json()["detail"][0]["msg"]
    info = client.get("/api/bolt/info", params={"head_chamfer": 5e-324}).json()
    assert not {r["key"] for r in info["rows"]} & {
        "head_chamfer", "chamfer_depth", "chamfer_circle_diameter", "corner_edge_left", "volume"}
    assert any("this part is not built" in w for w in info["warnings"])
    near = client.get("/api/bolt/model.stl", params={"head_chamfer": 1e-6, "quality": "preview"})
    assert near.status_code in (200, 422)
    if near.status_code == 422:
        assert near.json()["detail"][0]["type"] == "build_error"
    # The kernel bound: the document cannot know whether 1e-6 builds, so it reports no volume and
    # says the part may be refused, and the API still accepts the angle (D-18, no model floor).
    maybe = client.get("/api/bolt/info", params={"head_chamfer": 1e-6})
    assert maybe.status_code == 200
    assert "volume" not in {r["key"] for r in maybe.json()["rows"]}
    assert any("may be refused as a build error" in w for w in maybe.json()["warnings"])


def test_a_failed_export_is_a_422_and_never_enters_the_bytes_cache(
        monkeypatch: pytest.MonkeyPatch) -> None:
    # 7.77 is a diameter no other test downloads (the byte cache is session-wide). The
    # control request after the refusal proves the key below is the one a success is stored
    # under, so the absence above it is not vacuous.
    key = (BoltParams(d=7.77), "stl", "preview", "identity")
    assert app_module._EXPORTS.get(key) is None
    with monkeypatch.context() as patched:
        patched.setattr(cq.Shape, "exportStl", lambda *_args, **_kwargs: False)
        r = client.get("/api/bolt/model.stl", params={"d": 7.77, "quality": "preview"})
    assert r.status_code == 422
    assert r.json()["detail"][0]["type"] == "build_error"
    assert app_module._EXPORTS.get(key) is None

    assert client.get("/api/bolt/model.stl", params={"d": 7.77, "quality": "preview"}
                      ).status_code == 200
    assert app_module._EXPORTS.get(key) is not None


CAPPED: Params = {"d": 8, "pitch": 1.25, "length": 67.6, "thread_length": 67.6}


def test_a_fine_stl_l11_measured_over_budget_is_a_422_and_never_reaches_the_backend() -> None:
    """D-02: refused before the bytes cache, the admission slot and the pool."""
    calls = 0

    async def counting_backend(p: FastenerParams, fmt: str, quality: str) -> bytes:
        nonlocal calls
        calls += 1
        return b"never served"

    with _backend(counting_backend):
        r = client.get("/api/bolt/model.stl", params=CAPPED)    # quality defaults to fine
    assert r.status_code == 422
    (detail,) = r.json()["detail"]
    assert detail["type"] == "fine_stl_cap"
    assert detail["loc"] == ["query"]
    for fragment in ("thread_length and length", "right-hand", "67.5", "54",
                     "fine STL plus its gzip copy", "64 MiB export budget", "2026-10-08-a-grid"):
        assert fragment in detail["msg"]
    assert calls == 0


NUT_CAPPED: Params = {"d": 10, "pitch": 1.5, "s": 16, "m": 37, "clearance": 0.1}


def test_a_nut_fine_stl_past_its_measured_cap_is_a_422_and_never_reaches_the_backend() -> None:
    """R16, R17: refused before the cache, the admission slot and the pool, like the rod's."""
    calls = 0

    async def counting_backend(p: FastenerParams, fmt: str, quality: str) -> bytes:
        nonlocal calls
        calls += 1
        return b"served"

    with _backend(counting_backend):
        r = client.get("/api/nut/model.stl", params=NUT_CAPPED)    # quality defaults to fine
        assert r.status_code == 422
        (detail,) = r.json()["detail"]
        assert detail["type"] == "fine_stl_cap"
        assert detail["loc"] == ["query"]
        assert detail["msg"].startswith("m: ")
        for fragment in ("right-hand", "above m 36 mm", "fine STL plus its gzip copy",
                         "64 MiB export budget", "2026-10-21-nut-fine-caps-amended"):
            assert fragment in detail["msg"]
        assert calls == 0
        preview = client.get("/api/nut/model.stl", params={**NUT_CAPPED, "quality": "preview"})
        assert preview.status_code == 200
        assert calls == 1


def test_the_same_part_is_served_on_the_preview_stl_the_step_and_the_info_route() -> None:
    preview = client.get("/api/bolt/model.stl", params={**CAPPED, "quality": "preview"})
    assert preview.status_code == 200
    step = client.get("/api/bolt/model.step", params=CAPPED)
    assert step.status_code == 200
    assert step.content.startswith(b"ISO-10303-21;")
    assert client.get("/api/bolt/info", params=CAPPED).status_code == 200


def test_the_cap_itself_and_an_off_row_part_reach_the_backend_as_asked() -> None:
    seen: list[FastenerParams] = []

    async def stub(p: FastenerParams, fmt: str, quality: str) -> bytes:
        seen.append(p)
        return b"stub"

    with _backend(stub):
        at_cap = client.get("/api/bolt/model.stl", params={
            **CAPPED, "length": 67.5, "thread_length": 67.5})
        off_row = client.get("/api/bolt/model.stl", params={"d": 8, "pitch": 1, "length": 100})
        # D-22: the cap reads the thread; 100 mm of bolt with 60 mm of it is inside 67.5.
        short_thread = client.get("/api/bolt/model.stl", params={
            "d": 8, "pitch": 1.25, "length": 100, "thread_length": 60})
    assert at_cap.status_code == off_row.status_code == short_thread.status_code == 200
    bolts = [p for p in seen if isinstance(p, BoltParams)]
    assert [(p.d, p.pitch, p.length, p.thread_length) for p in bolts] == [
        (8.0, 1.25, 67.5, 67.5), (8.0, 1.0, 100.0, 20.0), (8.0, 1.25, 100.0, 60.0)]
    assert len(bolts) == len(seen)


def test_every_download_the_document_lists_is_answered_by_the_route_as_it_says() -> None:
    """G-04-3, T-04-29: the document and the model route read one rule, so they cannot disagree.

    ISO 4017 M8 x 70 and a part off every row, 5.55 mm, a diameter no other test downloads (the
    byte cache is session-wide, and the stub's bytes would answer a later real download).
    """
    row = expand("bolt", "iso4017:M8x70")
    assert row is not None
    capped: Params = {**row}
    plain: Params = {"d": 5.55}
    seen: list[tuple[str, str]] = []

    async def stub(p: FastenerParams, fmt: str, quality: str) -> bytes:
        seen.append((fmt, quality))
        return b"stub"

    for fields, refused in ((capped, 1), (plain, 0)):
        downloads = client.get("/api/bolt/info", params=fields).json()["downloads"]
        assert len(downloads) == 4
        assert sum(e["refusal"] is not None for e in downloads) == refused
        with _backend(stub):
            for entry in downloads:
                before = len(seen)
                r = client.get(f"/api/bolt/model.{entry['format']}",
                               params={**fields, "quality": entry["quality"]})
                if entry["refusal"] is None:
                    assert r.status_code == 200, entry
                    assert seen[before:] == [(entry["format"], entry["quality"])]
                else:
                    assert r.status_code == 422, entry
                    (detail,) = r.json()["detail"]
                    assert detail["type"] == "fine_stl_cap"
                    assert detail["msg"] == entry["refusal"]
                    assert len(seen) == before


def test_the_left_hand_part_l11_measured_inside_the_budget_reaches_the_backend() -> None:
    """D-21: the right-hand M10 x 60 is a 422, the left-hand one the same size is served."""
    seen: list[FastenerParams] = []

    async def stub(p: FastenerParams, fmt: str, quality: str) -> bytes:
        seen.append(p)
        return b"stub"

    mirror: Params = {"d": 10, "pitch": 1.5, "length": 60, "thread_length": 60, "s": 16,
                      "k": 6.4}
    with _backend(stub):
        left = client.get("/api/bolt/model.stl", params={**mirror, "left_hand": "true"})
        right = client.get("/api/bolt/model.stl", params=mirror)
    assert left.status_code == 200
    assert [p.left_hand for p in seen if isinstance(p, BoltParams)] == [True]
    assert right.status_code == 422
    assert right.json()["detail"][0]["type"] == "fine_stl_cap"
    assert "right-hand" in right.json()["detail"][0]["msg"]


CONFLICT_MSG = ("thread_length and length: thread_length 30 mm is longer than length 10 mm; "
                "shorten thread_length or lengthen length")


@pytest.mark.parametrize("route", ["/api/bolt/info", "/api/bolt/model.stl"])
def test_an_explicit_thread_length_above_an_explicit_length_is_a_422_naming_both(
        route: str) -> None:
    # D-25: refused at the request boundary, before any build and on both routes.
    params: Params = {"length": 10, "thread_length": 30}
    if route.endswith(".stl"):
        params = {**params, "quality": "preview"}
    r = client.get(route, params=params)
    assert r.status_code == 422
    assert r.json()["detail"] == [{
        "loc": ["query"], "type": "thread_length_conflict", "msg": CONFLICT_MSG,
        "ctx": {"fields": ["thread_length", "length"]}}]


HEAD_CHAMFER_MSG = (
    "head_chamfer and k: head_chamfer 80 degrees cuts the head corners deeper than "
    "k / 2 = 2 mm at s 10 mm; lower head_chamfer or raise k")


@pytest.mark.parametrize("route", ["/api/bolt/info", "/api/bolt/model.stl"])
def test_an_explicit_head_chamfer_deeper_than_half_k_is_a_422_naming_head_chamfer_and_k(
        route: str) -> None:
    # D-04: refused at the request boundary, before any build and on both routes.
    params: Params = {"head_chamfer": 80}
    if route.endswith(".stl"):
        params = {**params, "quality": "preview"}
    r = client.get(route, params=params)
    assert r.status_code == 422
    assert r.json()["detail"] == [{
        "loc": ["query"], "type": "head_chamfer_conflict", "msg": HEAD_CHAMFER_MSG,
        "ctx": {"fields": ["head_chamfer", "k"]}}]


def test_an_explicit_30_on_a_wide_head_is_a_422_and_a_defaulted_30_is_a_200_with_the_cap_warning(
) -> None:
    r = client.get("/api/bolt/info", params={"head_chamfer": 30, "s": 100})
    assert r.status_code == 422
    assert [d["type"] for d in r.json()["detail"]] == ["head_chamfer_conflict"]
    r = client.get("/api/bolt/info", params={"s": 100})
    assert r.status_code == 200
    assert head_chamfer_warnings(100.0, 4.0, 30.0)[0] in r.json()["warnings"]


def test_the_conflict_compares_parsed_floats() -> None:
    assert client.get("/api/bolt/info", params={"length": 10, "thread_length": "10.0"}
                      ).status_code == 200
    r = client.get("/api/bolt/info", params={"length": 10, "thread_length": "10.00001"})
    assert r.status_code == 422
    [detail] = r.json()["detail"]
    assert detail["type"] == "thread_length_conflict"
    assert detail["msg"] == (
        "thread_length and length: thread_length 10.00001 mm is longer than length 10 mm; "
        "shorten thread_length or lengthen length")


def test_a_default_thread_length_above_an_explicit_length_is_still_a_200_with_the_warning() -> None:
    r = client.get("/api/bolt/info", params={"length": 10})
    assert r.status_code == 200
    assert r.json()["warnings"][1] == (
        "thread_length 20 (default) exceeds length 10: thread built to the full length")


@pytest.mark.parametrize("query", [
    {"length": "-5", "thread_length": "10"},
    {"length": "abc", "thread_length": "10"},
    {"length": "nan", "thread_length": "10"},
    {"length": "10", "thread_length": "abc"},
])
def test_a_bad_value_beside_a_thread_length_stays_a_field_422_naming_the_bad_field(
        query: dict[str, str]) -> None:
    r = client.get("/api/bolt/info", params=query)
    assert r.status_code == 422
    [detail] = r.json()["detail"]
    assert detail["type"] != "thread_length_conflict"
    assert detail["loc"] == ["query", "length" if query["length"] != "10" else "thread_length"]


def test_a_repeated_length_beside_a_thread_length_is_the_duplicate_422_not_the_conflict() -> None:
    r = client.get("/api/bolt/info", params=[("length", "10"), ("length", "11"),
                                              ("thread_length", "30")])
    assert r.status_code == 422
    assert [d["type"] for d in r.json()["detail"]] == ["duplicate"]


def test_the_conflict_rule_does_not_reach_the_schema_route() -> None:
    r = client.get("/api/schema", params={"kind": "bolt", "length": 10, "thread_length": 30})
    assert r.status_code == 200


def test_the_conflict_is_still_a_422_behind_a_root_path() -> None:
    # uvicorn 0.54.0 prepends `--root-path` to `scope["path"]` (h11_impl.py:206), so a request
    # behind a `/screw` prefix matches the bolt route while `request.url.path` reads
    # `/screw/api/bolt/info`; a literal path test skipped the rule there and built a 10 mm
    # thread with a warning (04-REVIEW CR-01).
    behind_prefix = TestClient(app, root_path="/screw")
    r = behind_prefix.get("/screw/api/bolt/info", params={"length": 10, "thread_length": 30})
    assert r.status_code == 422
    [detail] = r.json()["detail"]
    assert detail["type"] == "thread_length_conflict"
    assert detail["ctx"] == {"fields": ["thread_length", "length"]}
    assert behind_prefix.get("/screw/api/bolt/info", params={"length": 10}).status_code == 200


@pytest.mark.parametrize("angle", ["nan", "inf", "abc", "90", "-1"])
def test_a_bad_head_chamfer_beside_a_wide_head_stays_a_field_422_naming_it(angle: str) -> None:
    # T-06.1-11: the rule gives None for anything it cannot judge, so the model's field 422 speaks.
    r = client.get("/api/bolt/info", params={"head_chamfer": angle, "s": 100})
    assert r.status_code == 422
    details = r.json()["detail"]
    assert [d["loc"] for d in details] == [["query", "head_chamfer"]]
    assert details[0]["type"] != "head_chamfer_conflict"


@pytest.mark.parametrize("field", ["s", "k"])
def test_an_unreadable_s_or_k_beside_a_deep_head_chamfer_is_its_field_422_not_the_conflict(
        field: str) -> None:
    # Codex review of PR #21: an unreadable s was dropped and judged at its default, so the 422
    # quoted s 10 mm, a value the user never sent. The model's 422 names the field instead.
    r = client.get("/api/bolt/info", params={"head_chamfer": 80, field: "abc"})
    assert r.status_code == 422
    details = r.json()["detail"]
    assert [d["loc"] for d in details] == [["query", field]]
    assert details[0]["type"] != "head_chamfer_conflict"


def test_a_head_so_small_its_width_squared_underflows_is_a_422_naming_d_and_pitch() -> None:
    # Codex review of PR #21: s = 1e-170 passed the model, and s * s == 0.0 raised
    # ZeroDivisionError in the kernel bound (a 500). The root-radius floor (07 D-18) now refuses
    # every d under 0.02 mm before a head is judged, so the request is a 422 and not a document;
    # `head_chamfer_kernel_bound` keeps its guard, tested in test_calc.py.
    r = client.get("/api/bolt/info",
                   params={"s": "1e-170", "d": "1e-171", "pitch": "1e-172", "length": "1e-171"})
    assert r.status_code == 422
    [detail] = r.json()["detail"]
    assert detail["type"] == "pitch_too_coarse"
    assert detail["ctx"]["fields"] == ["d", "pitch"]


def test_a_repeated_head_chamfer_is_the_duplicate_422_not_the_conflict() -> None:
    r = client.get("/api/bolt/info", params=[("head_chamfer", "80"), ("head_chamfer", "81")])
    assert r.status_code == 422
    assert [d["type"] for d in r.json()["detail"]] == ["duplicate"]


def test_the_head_chamfer_rule_does_not_reach_the_schema_route() -> None:
    r = client.get("/api/schema", params={"kind": "bolt", "head_chamfer": 80})
    assert r.status_code == 200


def test_the_head_chamfer_conflict_is_still_a_422_behind_a_root_path() -> None:
    # T-06.1-13: attached to the bolt routes by name, never sniffed from the path (04-REVIEW CR-01).
    behind_prefix = TestClient(app, root_path="/screw")
    r = behind_prefix.get("/screw/api/bolt/info", params={"head_chamfer": 80})
    assert r.status_code == 422
    [detail] = r.json()["detail"]
    assert detail["type"] == "head_chamfer_conflict"
    assert detail["ctx"] == {"fields": ["head_chamfer", "k"]}


def test_the_thread_length_conflict_is_named_first_when_both_rules_fire() -> None:
    r = client.get("/api/bolt/info",
                   params={"length": 10, "thread_length": 30, "head_chamfer": 80})
    assert r.status_code == 422
    assert [d["type"] for d in r.json()["detail"]] == ["thread_length_conflict"]


def test_an_explicit_head_chamfer_exactly_at_half_k_builds_uncapped_and_one_float_less_k_is_refused(
) -> None:
    # D-04 equality: the 422 and the cap share one threshold, depth > k / 2. At s 10 the 30 degree
    # depth does not depend on k, so k = 2 * depth puts k / 2 exactly on it (a power-of-two scale).
    k_eq = 2 * head_chamfer_depths(10.0, 1.0, 30.0)[0]
    at = client.get("/api/bolt/info", params={"head_chamfer": "30", "k": repr(k_eq)})
    assert at.status_code == 200
    body = at.json()
    assert not any(w.startswith("head_chamfer 30 and k") for w in body["warnings"])
    depth = {row["key"]: row["value"] for row in body["rows"]}["chamfer_depth"]
    assert depth == k_eq / 2
    below = math.nextafter(k_eq, 0.0)
    r = client.get("/api/bolt/info", params={"head_chamfer": "30", "k": repr(below)})
    assert r.status_code == 422
    assert [d["type"] for d in r.json()["detail"]] == ["head_chamfer_conflict"]


def test_a_length_below_the_floor_is_a_warned_info_document_and_a_422_build_error() -> None:
    # IN-01: the info document and the build agree on what is a part. The info document says so
    # with a warning and no turns or volume; the build names thread_length and length.
    info = client.get("/api/bolt/info", params={"length": 0.00005})
    assert info.status_code == 200
    body = info.json()
    assert any(w.startswith("thread_length and length: a thread of 5e-05 mm is shorter")
               for w in body["warnings"])
    assert {"turns", "volume"}.isdisjoint(row["key"] for row in body["rows"])

    r = client.get("/api/bolt/model.stl", params={"length": 0.00005, "quality": "preview"})
    assert r.status_code == 422
    detail = r.json()["detail"][0]
    assert detail["type"] == "build_error"
    assert detail["msg"].startswith("thread_length and length: ")


def test_the_m18_nut_info_carries_the_pair_proof_label_on_the_route() -> None:
    # D-20, SC6: read from the cited record, so the route needs no kernel and no clearance rule.
    label = "kernel pair proof inconclusive at K = 3 (2026-10-08-a-pair)"
    m18 = {"d": 18.0, "pitch": 2.5, "s": 27.0, "m": 14.8, "clearance": 0.1}
    assert label in client.get("/api/nut/info", params=m18).json()["notes"]
    assert label not in client.get("/api/nut/info", params={**m18, "pitch": 2.0}).json()["notes"]


def test_the_counterpart_travels_on_the_wire_for_both_kinds_and_keeps_a_boolean() -> None:
    bolt = client.get("/api/bolt/info", params={"left_hand": "true"}).json()["counterpart"]
    assert bolt == {"kind": "nut", "fields": {
        "d": 6.0, "pitch": 1.0, "left_hand": True, "s": 10.0, "m": 5.2}}
    assert bolt["fields"]["left_hand"] is True
    nut = client.get("/api/nut/info", params={"clearance": 0.1}).json()["counterpart"]
    assert nut == {"kind": "bolt", "fields": {
        "d": 6.0, "pitch": 1.0, "left_hand": False, "s": 10.0, "k": 4.0}}
    off = client.get("/api/bolt/info", params={"d": 6.5}).json()
    assert off["counterpart"]["fields"] == {"d": 6.5, "pitch": 1.0, "left_hand": False}
    assert off["warnings"][-1] == (
        "no GOST ISO 4032-2014 (ISO 4032:2012) row for d 6.5 pitch 1; set s and m on the nut")
