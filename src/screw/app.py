"""HTTP API.

    GET /                            the web UI (static/index.html); assets under /static
    GET /api/health                  liveness, plus build pool state
    GET /api/kinds                   the registered kinds and the default one
    GET /api/schema?kind=            JSON schema of one kind's parameters (drives the form)
    GET /api/presets?kind=           the ISO preset catalogue of one kind (drives the picker)
    GET /api/bolt/info?...           the info document: rows and warnings
    GET /api/bolt/model.stl?...      binary STL   (quality=preview|fine)
    GET /api/bolt/model.step?...     STEP AP214 solid
    GET /api/nut/info?...            the nut's info document, its `clearance` defaulted (L17)
    GET /api/nut/model.stl?...       binary STL   (quality=preview|fine)
    GET /api/nut/model.step?...      STEP AP214 solid

Every parameter is a query string field, so a model URL is shareable and curl-able. Every unset
field takes its default; a field the kind does not define, or a key given twice, is a 422
naming it, and so is an explicit `thread_length` longer than an explicit `length`.
"""

from __future__ import annotations

import gzip
import math
import threading
import time
import uuid
from collections import OrderedDict
from collections.abc import AsyncIterator, Awaitable, Callable, Hashable, Iterator, Mapping
from concurrent.futures.process import BrokenProcessPool
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from types import MappingProxyType
from typing import Annotated, Final, Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import JsonSchemaValue
from starlette.concurrency import run_in_threadpool

from . import __version__, int_env
from .build_errors import BuildError, BuildTimeout
from .calc import PartInfo, derive_capped, download_name, download_refusal, explicit_conflict
from .calc.cost import BUILD_TIMEOUT_S, Artifact, artifact_of, cap_defaults, refused_fields
from .calc.presets import PresetCatalogue, catalogue_document
from .params import DEFAULT_KIND, KINDS, BoltParams, FastenerParams, NutParams
from .pool import BuildPool
from .records import (
    build_failed,
    build_started,
    configure,
    cost_model_miss,
    export_served,
    queue_refused,
)

STATIC = Path(__file__).parent / "static"
MEDIA_TYPES = {"stl": "model/stl", "step": "model/step"}


class _BlobCache:
    """LRU of exported bytes bounded by total size rather than by entry count.

    The only exported-bytes cache in the whole topology. It needs no lock of its own: it
    is the only thing touching its dict, single-threaded, on one event loop, in the one
    uvicorn worker this app runs as.

    Any hashable key works; the one real key shape is described above `_EXPORTS`.
    """

    def __init__(self, budget: int) -> None:
        self._budget = budget
        self._items: OrderedDict[Hashable, bytes] = OrderedDict()
        self._bytes = 0

    def get(self, key: Hashable) -> bytes | None:
        data = self._items.get(key)
        if data is not None:
            self._items.move_to_end(key)
        return data

    def put(self, key: Hashable, data: bytes) -> None:
        old = self._items.pop(key, None)
        if old is not None:
            self._bytes -= len(old)
        if len(data) > self._budget:
            return
        self._items[key] = data
        self._bytes += len(data)
        while self._bytes > self._budget:
            self._bytes -= len(self._items.popitem(last=False)[1])


# Keyed on (params, fmt, quality, encoding) -- "identity" or "gzip" -- so both encodings of
# a part are first-class variants of the one cache, sharing the one byte budget, rather
# than a gzip-only sidecar bolted alongside a still-primary raw cache. Accepted cost:
# caching both encodings of a hot part means this cache holds fewer distinct parts within
# the same budget.
#
# 240 MiB by 07-SWEEP-PROTOCOL R21: both encodings, raw and gzip level 1, of all three artifacts
# of the admitted part whose sum is the largest, so the heaviest part a user can ask for is served
# from here on a repeat. Over the 394 candidates of explore run 40646117094 that part is
# iso4017:M20x200, 250654910 B, rounded up to a whole MiB. The gzip level-1 bytes bound any level
# R19 could adopt, and none was. The env override stays (CODING_VALUES: limits in code with an env
# var): the budget is part of the measured mem_limit, so a deployer who moves it re-sweeps, as
# D-16 says for the timeouts.
EXPORT_CACHE_MB: Final = int_env("SCREW_EXPORT_CACHE_MB", 240)
_EXPORTS = _BlobCache(EXPORT_CACHE_MB * 1024 * 1024)

# One build worker by 07-SWEEP-PROTOCOL R16: of the worker counts whose mem_limit fits the
# runner, the one with the lowest load p95 over all requests (the max over 5 repetitions), 35.09 s
# at N = 1 against 51.88 s at N = 2 and 69.78 s at N = 3 (load run 40909724292); all three
# qualified, and R16 ranks latency only. A fixed number, not os.cpu_count(): a machine-dependent
# default would make the measured mem_limit untrue somewhere. The env override stays for a
# deployer on other hardware, who re-sweeps (D-16).
DEFAULT_BUILD_WORKERS: Final = 1


def _build_workers() -> int:
    return int_env("SCREW_BUILD_WORKERS", DEFAULT_BUILD_WORKERS)


def _max_queued_builds() -> int:
    """A queue deeper than the pool can drain is latency with no payoff.

    2x the build workers by 07-SWEEP-PROTOCOL R17, which keeps 2N when the load run at the
    picked N shows no timeout and a peak within mem_limit. At N = 1 (load run 40909724292) the
    largest request wall, queue wait plus build, was 0.362 of its queue-aware deadline (rep 2,
    pool call 26) and the end peak 1657307136 B, under the 2415919104 B mem_limit. The env
    override stays for a deployer who re-sweeps (D-16).

    A function, not a bare module constant, so SCREW_BUILD_WORKERS and
    SCREW_MAX_QUEUED_BUILDS are read together, on every call -- tests exercise all three
    derivation cases via monkeypatch + a direct call, without reloading this module.
    """
    return int_env("SCREW_MAX_QUEUED_BUILDS", 2 * _build_workers())


MAX_QUEUED_BUILDS = _max_queued_builds()
BUILD_QUEUE = threading.BoundedSemaphore(MAX_QUEUED_BUILDS)

# The median built-request wall per artifact, queue wait plus build, over the 100 built requests
# of each in the 5 load repetitions at N = 1 (07-SWEEP-PROTOCOL R18, load run 40909724292).
# runtime.json carries each with its sample count; tests/test_runtime_bounds.py holds them equal.
MEDIAN_BUILD_S: Final[Mapping[Artifact, float]] = MappingProxyType({
    "stl-preview": 5.214082512000019, "stl-fine": 9.527734555999999, "step": 6.330915500499998})


def retry_after(artifact: Artifact) -> str:
    """The `Retry-After` of a 503 for `artifact`: its median build times the queue depth, rounded
    up to whole seconds and at least 1 (R18, D-11). The product is taken here, at run time, so a
    deployer's SCREW_MAX_QUEUED_BUILDS moves it.
    """
    return str(max(1, math.ceil(MEDIAN_BUILD_S[artifact] * MAX_QUEUED_BUILDS)))

# A plain in-flight counter, not BUILD_QUEUE._value: threading.BoundedSemaphore's internal
# counter is itself a private attribute, so this module keeps its own instead of reading
# another module's undocumented internals to report the same number. Incremented and
# decremented only inside _build_slot's own acquire/release pair below. With one uvicorn
# worker and this counter only ever touched from the event-loop thread, it needs no lock
# of its own -- that stops being true the moment SCREW_WORKERS raises the serving-process
# count again.
_in_flight_builds = 0

# The type an injected build backend must satisfy -- plain str for fmt/quality (not
# solid.Format/solid.Quality) because this module has no static import path to the solid
# package to name them with (contract 5); the endpoint's own Literal types are still
# checked at the call site.
BuildBackend = Callable[[FastenerParams, str, str], Awaitable[bytes]]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Build the pool eagerly at startup, tear it down at shutdown.

    Eager, import-only warm-up: the memory sweep then measures steady state from t=0
    instead of a ramp. SCREW_BUILD_WORKERS defaults to `DEFAULT_BUILD_WORKERS`, R16's pick.
    """
    # The only code that runs inside *every* spawned uvicorn worker, regardless of
    # SCREW_WORKERS: uvicorn's extra workers are `multiprocessing.spawn` children whose
    # target is uvicorn's own subprocess_started, never cli.cmd_serve, so a spawned worker
    # inherits none of the parent's logging configuration (spur verified by reading
    # uvicorn's installed source and by a live reproduction). configure() is idempotent,
    # so the default SCREW_WORKERS=1 case, where this and cli.cmd_serve's own call both run
    # in one process, still installs exactly one handler, not two.
    configure()
    app.state.pool = BuildPool(
        _build_workers(),
        # The per-artifact timeouts are code constants (D-09, D-16); the module-level name,
        # not a copy, so an instrument can replace it before startup.
        BUILD_TIMEOUT_S,
    )
    try:
        yield
    finally:
        app.state.pool.shutdown()
        # Clear the attribute, not just the object it points at: `app` is one
        # module-level FastAPI singleton shared by every test file in one pytest session,
        # and `getattr(app.state, "pool", None)`'s absent-vs-set distinction (health()'s
        # contract) is meaningless if a shut-down pool from an earlier test's
        # `with TestClient(app)` block lingers here for a later test's bare, lifespan-free
        # client to see.
        del app.state.pool


def refuse_repeated_keys(request: Request) -> None:
    """Refuse a query string that names a key twice, before anything judges its values.

    D-12, L02: the query model keeps the last of two values, so `?d=0&d=5` was a 200 for d=5
    and `?d=5&d=100000` a 200 for the larger part; a shared link with a duplicated key built a
    part its author did not see. An app-level dependency runs before each route's query model
    is validated (verified on fastapi 0.142.2, 03-RESEARCH Pattern 5), so the repeat is refused
    as a duplicate instead of one of its values being judged, and it covers every route,
    `/api/schema` included. Keys are listed in first-seen order.
    """
    seen: dict[str, int] = {}
    for key, _ in request.query_params.multi_items():
        seen[key] = seen.get(key, 0) + 1
    repeated = [key for key, n in seen.items() if n > 1]
    if repeated:
        raise HTTPException(422, detail=[
            {"loc": ["query", key], "type": "duplicate", "msg": f"{key} was given more than once."}
            for key in repeated])


def refuse_explicit_conflict(kind: str) -> Callable[[Request], None]:
    """A route dependency: the kind's explicit-value rules are a 422 naming their fields.

    One explicit head_chamfer is enough for the bolt's rule (06.1 D-05); the thread_length rule
    needs two explicit values.

    D-25: D-08's 422 for two explicit values lives at the request boundary because FastAPI
    0.142.2 copies every field default into the query model before validation
    (`fastapi/dependencies/utils.py:768-776`) and `strip()` rebuilds the model route's params
    with every field, so pydantic's `model_fields_set` cannot tell an explicit value from a
    default (04-RESEARCH Alert 1). The raw query can: only the keys it names reach the rule.
    Attached to each of the kind's model routes by name, so the rule is the kind's own
    (`explicit_conflict`, 04-REVIEW WR-02) and nothing sniffs the URL path: uvicorn 0.54.0
    prepends `--root-path` to `scope["path"]` (h11_impl.py:206), which is how a literal
    `/api/bolt/` test once skipped the 422 behind a prefix (04-REVIEW CR-01). The owner
    accepted that direct Python construction is not refused (D-25). A value `float()` cannot
    read reaches the rule as a string, which no rule judges, so the query model's 422 names it.
    """
    def refuse(request: Request) -> None:
        values: dict[str, object] = {}
        for key, raw in request.query_params.items():
            try:
                values[key] = float(raw)
            except ValueError:
                # Kept as the raw string, not dropped: a dropped s or k would be judged at its
                # frozen default, so `?head_chamfer=80&s=abc` was a conflict quoting s 10 mm.
                values[key] = raw
        if (conflict := explicit_conflict(kind, values)) is not None:
            raise HTTPException(422, detail=[{
                "loc": ["query"], "type": conflict.type, "msg": conflict.msg,
                "ctx": {"fields": list(conflict.fields)}}])
    return refuse


app = FastAPI(
    title="screw",
    version=__version__,
    summary="Parametric thread and fastener generator with STL/STEP export.",
    lifespan=lifespan,
    dependencies=[Depends(refuse_repeated_keys)],
)

# Level 1 by 07-SWEEP-PROTOCOL R19 (spur L19's rule shape, screw's thresholds): a higher level is
# adopted only if it shrinks the bytes by at least 10 % at no more than 1.5x the seconds, at every
# STL bound point, each the max over 5 repetitions. Over the 14 points (gzip runs 40909739628 and
# 40999657702) levels 6 and 9 failed both tests everywhere: at best 4.9 % smaller, at 1.74x the
# seconds or more. The largest, iso4017:M20x200 fine STL: 66239886 B in 2.01 s at level 1,
# 63595608 B in 3.56 s at level 6.
_GZIP_LEVEL = 1

# 4012 B by R20: the smallest measured JSON body length from which every body measured shrinks at
# level 1. Of the 1555 bodies of load run 40909724292, the largest that does not shrink is
# /api/health, 95 B to 98 B; 4012 B is the smallest body above it.
app.add_middleware(GZipMiddleware, minimum_size=4012, compresslevel=_GZIP_LEVEL)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


def build_backend() -> BuildBackend:
    """The injectable seam that exposes the pool's export to the endpoint.

    Hard-fails rather than falling back to an inline build when no pool has started: a
    production request that skipped the pool would silently reinstate the event-loop
    stall the pool removes, and would also skip affinity's cache locality. Tests override
    this dependency with an inline backend instead; the production code path never goes
    inline.
    """
    pool: BuildPool | None = getattr(app.state, "pool", None)
    if pool is None:
        raise RuntimeError("Build pool not started -- did the app's lifespan run?")
    return pool.export


class _Quality(BaseModel):
    quality: Literal["preview", "fine"] = Field(
        "fine", description="STL tessellation: preview (coarse, small) or fine.")


class BoltModelQuery(BoltParams, _Quality):
    """The bolt's parameters plus the model route's `quality`. Not used on the info route,
    where `quality` is a foreign field and therefore a 422 naming it.
    """


class NutModelQuery(NutParams, _Quality):
    """The nut's parameters plus the model route's `quality`, as `BoltModelQuery` is the bolt's."""


def strip[T: FastenerParams](q: FastenerParams, cls: type[T]) -> T:
    """Strip the per-endpoint extras back to the plain parameter class.

    The build caches are keyed on the parameter object, and pydantic equality includes the
    class, so a query model and the plain model describing the same part would otherwise
    never hit each other's cache entries.
    """
    return cls(**q.model_dump(include=set(cls.model_fields)))


def _gzip(data: bytes) -> bytes:
    """gzip-encode at `_GZIP_LEVEL`. A named module-level function, not an inline call, so
    a test can substitute a counting wrapper the same way it substitutes `build_backend`.
    No `mtime=`: nothing compares gzip bytes themselves, only the bodies they decode to,
    so a fixed header timestamp would buy nothing.
    """
    return gzip.compress(data, compresslevel=_GZIP_LEVEL)


@contextmanager
def _build_slot(request_id: str, p: FastenerParams, fmt: str, quality: str) -> Iterator[None]:
    """Admission control: refuse work we cannot start soon rather than queue it.

    A slot covers a build *and* the first gzip encode of its result: `GZipMiddleware`
    compresses only after the endpoint has returned and this slot is gone, so putting
    compression there bounded nothing -- spur measured the mechanism as 4.33x/5.52x
    under-load ratios with the build pool never running. `_serve()` compresses inside this
    slot instead, so a request for an already-built-but-not-yet-compressed part can be
    refused here too.

    Takes the request identity so a refusal can name the part that was turned away.
    """
    global _in_flight_builds
    if not BUILD_QUEUE.acquire(blocking=False):
        queue_refused(request_id, p, fmt, quality,
                      in_flight=_in_flight_builds, max_queued=MAX_QUEUED_BUILDS)
        raise HTTPException(
            503,
            detail=[{"loc": ["query"], "type": "busy",
                     "msg": f"Busy: {MAX_QUEUED_BUILDS} parts are already being built or "
                            "compressed. Try again in a moment."}],
            headers={"Retry-After": retry_after(artifact_of(fmt, quality))},
        )
    _in_flight_builds += 1
    try:
        yield
    finally:
        _in_flight_builds -= 1
        BUILD_QUEUE.release()


class PoolState(BaseModel):
    """Build pool state nested under `/api/health`'s `pool` key."""

    model_config = ConfigDict(frozen=True)

    workers: int = Field(description="Build worker processes in the pool.")
    queue_available: int = Field(
        description="Admission slots free now, each covering a build and its first "
                    "gzip encode.")
    workers_replaced: int = Field(
        description="Workers replaced since start, after a timeout or a crash.")


class HealthReport(BaseModel):
    """The document `/api/health` returns. `pool` is `null`, not absent, when the app runs
    without its lifespan -- the same null-over-absent rule as every other optional value.
    """

    model_config = ConfigDict(frozen=True)

    status: Literal["ok"] = Field(description="Always ok: the process answered.")
    version: str = Field(description="screw version.")
    pool: PoolState | None = Field(
        description="Build pool state; null when the app runs without its lifespan.")


@app.get("/api/health")
def health() -> HealthReport:
    """Liveness, plus pool state -- parent-local counters only.

    `status` and `version` stay at the top level, so the container healthcheck and the UI
    (neither of which reads pool fields) are unaffected. Pool state nests under one `pool`
    key: every later pool field lands inside `pool` without touching the published top
    level, which keeps this a reversible decision instead of a fresh one-way door each
    time a field is added.

    This endpoint's latency under load is the proof the event loop stays free, so it has
    to measure the event loop and not the pool: a plain `def`, not `async def`, means
    there is nothing here for FastAPI to await, and every value below is an O(1) attribute
    or counter read -- no lock, no IPC, no call into a worker. Asking the workers
    themselves would make the measurement measure the exact thing it is supposed to be
    independent of.

    `pool` is `null`, not absent, when `app.state.pool` hasn't been set -- the one path
    that can happen on is a bare `TestClient(app)` used without `with`, which never runs
    this app's lifespan.
    """
    pool: BuildPool | None = getattr(app.state, "pool", None)
    return HealthReport(
        status="ok",
        version=__version__,
        pool=None if pool is None else PoolState(
            workers=pool.workers,
            queue_available=MAX_QUEUED_BUILDS - _in_flight_builds,
            workers_replaced=pool.replaced,
        ),
    )


class KindsReport(BaseModel):
    """The registered kinds and the default one, so the UI needs no literal for either."""

    model_config = ConfigDict(frozen=True)

    default: str = Field(description="The kind a link that omits `kind` means (L02).")
    kinds: list[str] = Field(description="Every registered kind.")


@app.get("/api/kinds")
def kinds() -> KindsReport:
    return KindsReport(default=DEFAULT_KIND, kinds=list(KINDS))


def _known_kind(kind: str) -> type[FastenerParams]:
    """The kind's model, or the 404 the UI parses for an unknown one."""
    model = KINDS.get(kind)
    if model is None:
        # A handler-raised 404, not a Literal path parameter: a Literal built from the
        # registry at runtime cannot satisfy mypy --strict, and the body shape matches the
        # 422s the UI already parses.
        raise HTTPException(404, detail=[{
            "loc": ["query", "kind"], "type": "unknown_kind",
            "msg": f"Unknown kind {kind!r}. Known kinds: {', '.join(KINDS)}."}])
    return model


@app.get("/api/schema")
def schema(kind: str) -> JsonSchemaValue:
    """One kind's parameter schema. `kind` is required: there is no API-side default."""
    return _known_kind(kind).model_json_schema()


@app.get("/api/presets")
def presets(kind: str) -> PresetCatalogue:
    """One kind's ISO preset catalogue, the picker's only source (D-10).

    The model routes take millimetres only: a preset id is not a query key there, so a link
    never carries one and the part is always rebuilt from its fields (D-09, TABL-01).
    """
    _known_kind(kind)
    return catalogue_document(kind)


def explicit_fields(request: Request, kind: str) -> frozenset[str]:
    """The kind's fields the request named: its raw query keys, the set `refuse_explicit_conflict`
    reads, because the query model holds every default and cannot tell one from a typed value
    (D-25). B-03's cap moves only a field outside this set.
    """
    return frozenset(key for key in request.query_params if key in KINDS[kind].model_fields)


@app.get("/api/bolt/info", dependencies=[Depends(refuse_explicit_conflict(BoltParams.kind))])
def bolt_info(q: Annotated[BoltParams, Query()], request: Request) -> PartInfo:
    """The bolt's info document, of the part as capped (B-03). `quality` is not a bolt field, so
    it is a 422 here."""
    return derive_capped(q, explicit_fields(request, BoltParams.kind))[1]


@app.get("/api/bolt/model.{fmt}", response_class=Response,
         responses={200: {"content": {t: {} for t in MEDIA_TYPES.values()}}},
         dependencies=[Depends(refuse_explicit_conflict(BoltParams.kind))])
async def bolt_model(fmt: Literal["stl", "step"], q: Annotated[BoltModelQuery, Query()],
                     request: Request,
                     backend: Annotated[BuildBackend, Depends(build_backend)]) -> Response:
    # B-03: the same capped part as the info document, so the preview, the download and its file
    # name are the part the warning describes (L02).
    p, _ = cap_defaults(strip(q, BoltParams), explicit_fields(request, BoltParams.kind))
    return await _serve(p, fmt, q.quality, request, backend)


@app.get("/api/nut/info", dependencies=[Depends(refuse_explicit_conflict(NutParams.kind))])
def nut_info(q: Annotated[NutParams, Query()], request: Request) -> PartInfo:
    """The nut's info document, of the part as capped (B-03). `quality` is a 422 here."""
    return derive_capped(q, explicit_fields(request, NutParams.kind))[1]


@app.get("/api/nut/model.{fmt}", response_class=Response,
         responses={200: {"content": {t: {} for t in MEDIA_TYPES.values()}}},
         dependencies=[Depends(refuse_explicit_conflict(NutParams.kind))])
async def nut_model(fmt: Literal["stl", "step"], q: Annotated[NutModelQuery, Query()],
                    request: Request,
                    backend: Annotated[BuildBackend, Depends(build_backend)]) -> Response:
    p, _ = cap_defaults(strip(q, NutParams), explicit_fields(request, NutParams.kind))
    return await _serve(p, fmt, q.quality, request, backend)


async def _serve(params: FastenerParams, fmt: Literal["stl", "step"], quality: str,
                 request: Request, backend: BuildBackend) -> Response:
    """The one model-serving path every kind's route delegates to: cache, admission
    control, build, compress, log, respond.
    """
    # First, before the cache, the admission slot and the pool: an artifact the cost model
    # predicts over its measured budget is refused on the parameters alone, so it never occupies
    # a worker (D-05, D-06, L21). Reads no field by name, so every kind gets its own rule
    # through the one call. B-02 (07-OWNER-RULINGS.md, 2026-10-29): one type, `over_budget`, for
    # every artifact, naming the fields the cost reads in model order (for a bolt below the fitted
    # turns, the fields that set them, G30) and the artifact; it retires `fine_stl_cap`.
    refusal = download_refusal(params, fmt, quality)
    if refusal is not None:
        raise HTTPException(422, detail=[{
            "loc": ["query"], "type": "over_budget", "msg": refusal,
            "ctx": {"fields": list(refused_fields(params)),
                    "artifact": artifact_of(fmt, quality)}}])
    # A plain local, not middleware or contextvars -- minted once here and passed to every
    # record this request emits, so two concurrent requests for the same part (the one
    # case params + time cannot disambiguate: same-slot affinity) are still
    # distinguishable in the log.
    request_id = uuid.uuid4().hex[:8]
    # Same test GZipMiddleware itself makes (starlette's middleware/gzip.py,
    # `"gzip" in headers.get("Accept-Encoding", "")`) -- endpoint and middleware must
    # agree on who gets encoded bytes, or a client that asked for identity could be served
    # gzip bytes cached for a previous gzip-accepting client.
    wants_gzip = "gzip" in request.headers.get("Accept-Encoding", "")
    encoding = "gzip" if wants_gzip else "identity"
    key = (params, fmt, quality, encoding)
    # A plain cache hit never enters the slot below, so its duration is zero by
    # construction and its source is "cache" -- both set here, not as a branch, so the
    # cache-hit path that skips the block below still has a defined value for each when
    # export_served() is called.
    duration_s = 0.0
    source = "cache"
    data = _EXPORTS.get(key)
    if data is None:
        start = time.monotonic()
        try:
            # Compression moves inside this slot: outside it, a bound on cache-hit
            # compression would be a no-op, because GZipMiddleware compresses only after
            # the endpoint has already returned and the slot is gone (see _build_slot).
            with _build_slot(request_id, params, fmt, quality):
                raw_key = (params, fmt, quality, "identity")
                raw = _EXPORTS.get(raw_key)
                if raw is None:
                    source = "built"
                    build_started(request_id, params, fmt, quality)
                    raw = await backend(params, fmt, quality)
                    _EXPORTS.put(raw_key, raw)
                else:
                    source = "compressed"
                if wants_gzip:
                    # Off the event loop, same as Starlette's own middleware did for
                    # bodies this size -- what's new is that it's now bounded by the same
                    # admission control as a fresh build.
                    data = await run_in_threadpool(_gzip, raw)
                    _EXPORTS.put(key, data)
                else:
                    data = raw
        except BuildError as exc:
            build_failed(request_id, params, fmt, quality, exc=exc,
                         duration_s=time.monotonic() - start)
            raise HTTPException(422, detail=[{"loc": ["query"], "msg": str(exc),
                                              "type": "build_error"}]) from exc
        except BuildTimeout as exc:
            # 503, not 422: the same part succeeds on faster hardware, so overrunning is a
            # property of this machine and this moment, not of the parameters -- calling
            # it a parameter error would tell the user to change a part that is fine.
            # Same busy-refusal shape as _build_slot above (reused, not reinvented), with
            # its own `type` so a client can tell "come back in a moment" from "your part
            # is impossible".
            build_failed(request_id, params, fmt, quality, exc=exc,
                         duration_s=time.monotonic() - start)
            # The timeout is the backstop behind the cost model (D-10): reaching it means
            # the model admitted a part the machine could not build in time. Nothing was
            # cached -- the put sits after the awaited build.
            artifact = artifact_of(fmt, quality)
            cost_model_miss(request_id, params, fmt, quality, artifact=artifact,
                            timeout_s=BUILD_TIMEOUT_S[artifact])
            raise HTTPException(503, detail=[{"loc": ["query"], "msg": str(exc),
                                              "type": "timeout"}],
                                headers={"Retry-After": retry_after(artifact)}) from exc
        except BrokenProcessPool as exc:
            # 503, not 422: the worker is gone, the parameters didn't do anything wrong.
            # BuildPool.export already replaced the dead slot before this propagated here
            # (pool.py's _run_with_timeout); the client just needs to know it can retry.
            # This also covers a request queued behind a *different*, same-slot request
            # that overran its own timeout (affinity) -- that queued request's worker was
            # terminated by this service, not by a crash, so "died unexpectedly" alone is
            # not true of every caller reaching this branch.
            build_failed(request_id, params, fmt, quality, exc=exc,
                         duration_s=time.monotonic() - start)
            raise HTTPException(
                503,
                detail=[{"loc": ["query"],
                         "msg": "A build worker was lost (died unexpectedly, or was "
                                "terminated after another request on the same slot "
                                "overran its timeout). The request can be retried.",
                         "type": "pool_broken"}],
                headers={"Retry-After": retry_after(artifact_of(fmt, quality))},
            ) from exc
        except HTTPException:
            # _build_slot()'s own admission-control refusal (busy, 503) raises this from
            # inside the `with` above and already calls queue_refused() itself -- an
            # already-classified, already-logged outcome, not an unclassified crash. Must
            # come before the catch-all below, or a busy refusal would also produce a
            # spurious build.failed record naming "HTTPException" alongside the correct
            # queue.refused one.
            raise
        except Exception as exc:
            # The three classes above are the solid package's *documented* contract
            # ("BuildError is the only exception the module lets out") -- but `_gzip()`
            # runs inside this same slot under `run_in_threadpool` and can raise under
            # memory pressure, and a future violation of that contract is exactly the kind
            # of bug this catch exists for. Log then re-raise, not swallow: uvicorn's own
            # ASGI-level 500 is still what serves the response (and its record carries a
            # traceback); this only adds screw's own build.failed record to what would
            # otherwise be the *only* remaining evidence of a request that actually failed.
            build_failed(request_id, params, fmt, quality, exc=exc,
                         duration_s=time.monotonic() - start)
            raise
        duration_s = time.monotonic() - start
    export_served(request_id, params, fmt, quality, source=source, encoding=encoding,
                  duration_s=duration_s)
    name = download_name(params, fmt, quality)
    headers = {"Content-Disposition": f'attachment; filename="{name}"',
               "Vary": "Accept-Encoding"}
    if wants_gzip:
        # Setting Content-Encoding here is what makes GZipMiddleware's pass-through branch
        # leave this body alone instead of compressing it a second time (starlette's
        # middleware/gzip.py: "if it is [already set], the body passes through unchanged").
        headers["Content-Encoding"] = "gzip"
    return Response(data, media_type=MEDIA_TYPES[fmt], headers=headers)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")
