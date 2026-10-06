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
from typing import cast

import pytest
from fastapi.testclient import TestClient

from screw import app as app_module
from screw.app import app, build_backend
from screw.build_errors import BuildError, BuildTimeout
from screw.calc import SKELETON_WARNING
from screw.params import DEFAULT_KIND, INTERIM_MAX_MM, KINDS, FastenerParams
from screw.solid import Format, Quality, export

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


def test_kinds_names_the_frozen_default() -> None:
    assert client.get("/api/kinds").json() == {"default": "bolt", "kinds": ["bolt"]}
    # The literal, not DEFAULT_KIND: a link that omits `kind` means bolt forever (L02).
    assert DEFAULT_KIND == "bolt"
    assert list(KINDS) == ["bolt"]


def test_schema_requires_a_kind_and_knows_only_registered_kinds() -> None:
    r = client.get("/api/schema", params={"kind": "bolt"})
    assert r.status_code == 200
    props = r.json()["properties"]
    assert list(props) == ["d", "pitch", "length"]
    assert props["d"]["group"] == "Size"
    assert props["d"]["unit"] == "mm"
    assert props["length"]["unit"] == "mm"

    missing = client.get("/api/schema")
    assert missing.status_code == 422
    assert missing.json()["detail"][0]["loc"] == ["query", "kind"]

    unknown = client.get("/api/schema", params={"kind": "nut"})
    assert unknown.status_code == 404
    detail = unknown.json()["detail"][0]
    assert detail["loc"] == ["query", "kind"]
    assert detail["type"] == "unknown_kind"


def test_an_unknown_kind_has_no_routes() -> None:
    assert client.get("/api/nut/info").status_code == 404
    assert client.get("/api/nut/model.stl").status_code == 404


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
    assert set(part_info["properties"]) == {"kind", "rows", "warnings"}
    assert set(part_info["required"]) == {"kind", "rows", "warnings"}
    info_row = schema["components"]["schemas"]["InfoRow"]
    assert set(info_row["properties"]) == {"key", "label", "value", "unit"}
    assert set(info_row["required"]) == {"key", "label", "value", "unit"}

    model_route = schema["paths"]["/api/bolt/model.{fmt}"]["get"]
    query_names = {p["name"] for p in model_route["parameters"] if p["in"] == "query"}
    assert query_names == {"d", "pitch", "length", "quality"}
    # `quality` belongs to the model route only: it is a foreign field on the info route.
    info_route = schema["paths"]["/api/bolt/info"]["get"]
    info_names = {p["name"] for p in info_route["parameters"] if p["in"] == "query"}
    assert info_names == {"d", "pitch", "length"}

    health_response = schema["paths"]["/api/health"]["get"]["responses"]["200"]
    assert health_response["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/HealthReport"}
    health_component = schema["components"]["schemas"]["HealthReport"]
    assert set(health_component["required"]) == {"status", "version", "pool"}
    pool_component = schema["components"]["schemas"]["PoolState"]
    assert set(pool_component["required"]) == {
        "workers", "queue_available", "workers_replaced"}


def test_the_default_info_document() -> None:
    r = client.get("/api/bolt/info")
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "bolt"
    assert [row["key"] for row in body["rows"]] == ["d", "pitch", "length", "volume"]
    values = {row["key"]: row["value"] for row in body["rows"]}
    assert values["d"] == 6.0
    assert values["pitch"] == 1.0
    assert values["length"] == 20.0
    assert values["volume"] == pytest.approx(math.pi * 3.0**2 * 20.0)
    assert body["warnings"][0] == SKELETON_WARNING
    # The skeleton builds no thread, so no row may claim a turn count (D-06).
    assert not any("turn" in row["key"] or "turn" in row["label"].lower()
                   for row in body["rows"])


@pytest.mark.parametrize("route", ["/api/bolt/info", "/api/bolt/model.stl"])
@pytest.mark.parametrize("field", ["d", "pitch", "length"])
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


def test_the_interim_bound_is_inclusive_and_the_next_value_is_refused() -> None:
    # The number D-14 pinned. Phase 7 replaces it from the sweep and edits this line on
    # purpose: the bound is a contract, not an accident of whichever constant is imported.
    assert INTERIM_MAX_MM == 100000.0
    bound = INTERIM_MAX_MM
    just_over = math.nextafter(bound, math.inf)
    assert just_over > bound

    for field in ("d", "length"):
        at_bound: Params = {field: bound}
        assert client.get("/api/bolt/info", params=at_bound).status_code == 200
        r = client.get("/api/bolt/model.stl", params={**at_bound, "quality": "preview"})
        assert r.status_code == 200
        assert len(r.content) > 84

        over: Params = {field: just_over}
        for route in ("/api/bolt/info", "/api/bolt/model.stl"):
            refused = client.get(route, params=over)
            assert refused.status_code == 422
            assert refused.json()["detail"][0]["loc"] == ["query", field]

    # 1e200 overflows a float on the way to a volume (F2); the bound refuses it first.
    huge = client.get("/api/bolt/info", params={"d": 1e200})
    assert huge.status_code == 422
    assert huge.json()["detail"][0]["loc"] == ["query", "d"]


def test_a_diameter_the_kernel_cannot_build_is_a_422_build_error() -> None:
    """d=1e-9 passes validation (it is positive and finite) but the kernel returns a solid
    that is not valid; the doorway turns that into a BuildError, not a served file."""
    r = client.get("/api/bolt/model.stl", params={"d": 1e-9, "quality": "preview"})
    assert r.status_code == 422
    detail = r.json()["detail"][0]
    assert detail["type"] == "build_error"
    assert detail["loc"] == ["query"]
    assert "invalid solid" in detail["msg"]


def test_the_download_filename_is_safe_for_extreme_values() -> None:
    r = client.get("/api/bolt/model.stl", params={"pitch": 1e300, "quality": "preview"})
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
    assert r.headers["content-disposition"] == (
        f'attachment; filename="bolt_d8_pitch1_length20.{fmt}"')
    if magic:
        assert r.content.startswith(magic)


def test_unknown_format_is_rejected() -> None:
    assert client.get("/api/bolt/model.obj").status_code == 422


def test_bad_type_is_422_on_the_field() -> None:
    r = client.get("/api/bolt/info", params={"d": "wide"})
    assert r.status_code == 422
    assert r.json()["detail"][0]["loc"] == ["query", "d"]


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
    assert _field(refused[0], "slug") == "bolt_d7.3_pitch1_length20"
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
        assert _field(record, "slug") == "bolt_d7.1_pitch1_length20"
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
    assert _field(served[0], "slug") == "bolt_d6_pitch1_length20"


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
    (BuildError("Geometry kernel failed (Standard_Failure); check d and length."),
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
    assert _field(failed[0], "slug") == "bolt_d8.3_pitch1_length20"
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
