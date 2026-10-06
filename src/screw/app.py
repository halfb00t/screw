"""HTTP API.

    GET /api/health                  liveness, plus build pool state
    GET /api/kinds                   the registered kinds and the default one
    GET /api/schema?kind=            JSON schema of one kind's parameters (drives the form)
    GET /api/bolt/info?...           the info document: rows and warnings
    GET /api/bolt/model.stl?...      binary STL   (quality=preview|fine)
    GET /api/bolt/model.step?...     STEP AP214 solid

Every parameter is a query string field, so a model URL is shareable and curl-able. Unset
fields take their defaults; a field the kind does not define is a 422 naming it.
"""

from __future__ import annotations

import gzip
import threading
import time
import uuid
from collections import OrderedDict
from collections.abc import AsyncIterator, Awaitable, Callable, Hashable, Iterator
from concurrent.futures.process import BrokenProcessPool
from contextlib import asynccontextmanager, contextmanager
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import JsonSchemaValue
from starlette.concurrency import run_in_threadpool

from . import __version__, int_env
from .build_errors import BuildError, BuildTimeout
from .calc import PartInfo, derive
from .params import DEFAULT_KIND, KINDS, BoltParams, FastenerParams
from .pool import BuildPool
from .records import build_failed, build_started, configure, export_served, queue_refused

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
# INTERIM (D-01): 64 MB, carried from spur's export-cache default (same knob, renamed),
# where it sized the cache against 160-199 tooth gears (~9 MB raw STL each). Not measured
# for screw; the skeleton cylinder's STL is under 1.5 MB at the largest admitted size.
# Phase 7 re-sweeps (OPER-02).
_EXPORTS = _BlobCache(int_env("SCREW_EXPORT_CACHE_MB", 64) * 1024 * 1024)


def _max_queued_builds() -> int:
    """A queue deeper than the pool can drain is latency with no payoff.

    INTERIM (D-01): 2x the build workers, carried from spur (L04's admission control),
    where a measured load run showed deeper queues only adding latency. Not measured for
    screw. Phase 7 re-sweeps (OPER-02).

    A function, not a bare module constant, so SCREW_BUILD_WORKERS and
    SCREW_MAX_QUEUED_BUILDS are read together, on every call -- tests exercise all three
    derivation cases via monkeypatch + a direct call, without reloading this module.
    """
    return int_env("SCREW_MAX_QUEUED_BUILDS", 2 * int_env("SCREW_BUILD_WORKERS", 2))


MAX_QUEUED_BUILDS = _max_queued_builds()
BUILD_QUEUE = threading.BoundedSemaphore(MAX_QUEUED_BUILDS)

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
    instead of a ramp. SCREW_BUILD_WORKERS defaults to a fixed 2, not os.cpu_count() -- a
    machine-dependent default would make the measured mem_limit untrue somewhere.
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
        # INTERIM (D-01): 2 workers, carried from spur's default; a fixed number, not
        # os.cpu_count(). Not measured for screw. Phase 7 re-sweeps (OPER-02).
        int_env("SCREW_BUILD_WORKERS", 2),
        # INTERIM (D-01): 30 s per build, carried from spur. spur's worst observed single
        # build was 7.39 s (a 200-tooth fine gear, ten concurrent requests, host under
        # contention), so 30 s is ~4x spur's observation -- a margin chosen for slower
        # hardware on spur's corpus. It is not a measurement of screw: the skeleton cylinder
        # builds in well under a second (INTERIM_MAX_MM's comment). Phase 7 re-sweeps
        # (OPER-02).
        int_env("SCREW_BUILD_TIMEOUT", 30),
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


app = FastAPI(
    title="screw",
    version=__version__,
    summary="Parametric thread and fastener generator with STL/STEP export.",
    lifespan=lifespan,
)

# spur L19 measured the real 9,062,784-byte STL of a 199-tooth fine gear at gzip levels 1/6/9
# (host loadavg 2.68/3.07/2.78 just before measuring):
#
#   level | single-threaded median | output bytes (% of input) | 10-concurrent wall (median of 3)
#   ----- | ----------------------- | -------------------------- | ---------------------------------
#     1   |  51.5 ms                | 2,632,467 (29.0%)          |  74.4 ms
#     6   | 147.9 ms                | 2,403,312 (26.5%)          | 198.9 ms
#     9   | 788.0 ms                | 2,404,371 (26.5%)          | 925.5 ms
#
# spur's selection rule, set up front: adopt a higher level only if it shrinks output by
# >=10% AND costs <=1.5x the 10-concurrent wall time of the level below it. Level 6 was only
# 8.7% smaller, level 9 also missed it, so level 1 won.
# INTERIM (D-01): level 1 carried from spur L19. That is a gear mesh, not a screw mesh:
# nothing here is measured for screw. Phase 7 re-sweeps (OPER-02).
_GZIP_LEVEL = 1

# INTERIM (D-01): `minimum_size=1024` carried from spur; not measured for screw. Phase 7
# re-sweeps (OPER-02).
app.add_middleware(GZipMiddleware, minimum_size=1024, compresslevel=_GZIP_LEVEL)


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
            # INTERIM (D-01): 5 s, carried from spur; a client hint, not a measurement.
            # Phase 7 re-sweeps (OPER-02).
            headers={"Retry-After": "5"},
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


@app.get("/api/schema")
def schema(kind: str) -> JsonSchemaValue:
    """One kind's parameter schema. `kind` is required: there is no API-side default."""
    model = KINDS.get(kind)
    if model is None:
        # A handler-raised 404, not a Literal path parameter: a Literal built from the
        # registry at runtime cannot satisfy mypy --strict, and the body shape matches the
        # 422s the UI already parses.
        raise HTTPException(404, detail=[{
            "loc": ["query", "kind"], "type": "unknown_kind",
            "msg": f"Unknown kind {kind!r}. Known kinds: {', '.join(KINDS)}."}])
    return model.model_json_schema()


@app.get("/api/bolt/info")
def bolt_info(q: Annotated[BoltParams, Query()]) -> PartInfo:
    """The bolt's info document. `quality` is not a bolt field, so it is a 422 here."""
    return derive(q)


@app.get("/api/bolt/model.{fmt}", response_class=Response,
         responses={200: {"content": {t: {} for t in MEDIA_TYPES.values()}}})
async def bolt_model(fmt: Literal["stl", "step"], q: Annotated[BoltModelQuery, Query()],
                     request: Request,
                     backend: Annotated[BuildBackend, Depends(build_backend)]) -> Response:
    return await _serve(strip(q, BoltParams), fmt, q.quality, request, backend)


async def _serve(params: FastenerParams, fmt: Literal["stl", "step"], quality: str,
                 request: Request, backend: BuildBackend) -> Response:
    """The one model-serving path every kind's route delegates to: cache, admission
    control, build, compress, log, respond.
    """
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
            raise HTTPException(503, detail=[{"loc": ["query"], "msg": str(exc),
                                              "type": "timeout"}],
                                headers={"Retry-After": "5"}) from exc
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
                headers={"Retry-After": "5"},
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
    headers = {"Content-Disposition": f'attachment; filename="{params.slug()}.{fmt}"',
               "Vary": "Accept-Encoding"}
    if wants_gzip:
        # Setting Content-Encoding here is what makes GZipMiddleware's pass-through branch
        # leave this body alone instead of compressing it a second time (starlette's
        # middleware/gzip.py: "if it is [already set], the body passes through unchanged").
        headers["Content-Encoding"] = "gzip"
    return Response(data, media_type=MEDIA_TYPES[fmt], headers=headers)
