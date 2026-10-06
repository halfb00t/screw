"""Structured JSON logging, configured once at the composition boundary.

Both `cli.py` and `app.py` need to log: `cli.cmd_serve`'s `configure()` call before
`uvicorn.run` is the composition root for the default single-worker deployment
(`CMD ["screw", "serve"]`, `make serve`), and `app.py`'s `lifespan()` startup is the only
code that runs inside every spawned uvicorn worker once `SCREW_WORKERS>1`. spur verified
that a spawned worker does not inherit the parent's `logging` state at all: uvicorn starts
extra workers via `multiprocessing`'s "spawn" context, whose target is uvicorn's own
`subprocess_started`, never `cli.cmd_serve` (spur L20). Splitting this out of both call
sites is what lets both call `configure()` without either importing the other.

Not named `logging.py`: that would shadow the stdlib module by name in every reader's head,
in a file that itself imports stdlib `logging`. `records.py` names what it is -- the module
owning this project's log record vocabulary: one formatter, one level knob, and one small
function per event, so `app.py` and `pool.py` never assemble an `extra=` dict by hand and a
rename can only be a deliberate change to a literal string a test asserts.

Kernel-free like `build_errors.py`, and for the same reason: `screw.cli` imports this
module too, and the CLI must never reach `cadquery`/`OCP`/`fastapi`/`starlette` through any
path (the import-linter contracts in pyproject.toml enforce it).
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import sys
from typing import TextIO

from . import __version__
from .build_errors import BuildError
from .params import FastenerParams

_LOG = logging.getLogger(__name__)

# Every attribute a stock LogRecord carries whether or not `extra=` was passed (spur
# verified it against CPython 3.12 with a direct `Logger.makeRecord` call), plus
# `message`/`asctime`, which the base `Formatter.format()` may add but this one never
# calls. Defined once, so the formatter's exclusion set and its round-trip test can never
# quietly disagree about what "an application field" means.
_STANDARD_LOGRECORD_ATTRS = frozenset({
    "args", "asctime", "created", "exc_info", "exc_text", "filename", "funcName",
    "levelname", "levelno", "lineno", "message", "module", "msecs", "msg", "name",
    "pathname", "process", "processName", "relativeCreated", "stack_info", "taskName",
    "thread", "threadName",
})


class _JsonFormatter(logging.Formatter):
    """One JSON object per physical line: reading is `make serve 2>&1 | jq`, with no second
    renderer, so a value this formatter fails to escape correctly would fork one log line
    into two and break every downstream `jq`.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.datetime.fromtimestamp(
                record.created, tz=datetime.UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            # `event` rides in `record.__dict__` for screw's own records (`_emit` passes it
            # via `extra=`); uvicorn's own records carry no such key, so this falls back to
            # the formatted message rather than raising.
            "event": record.__dict__.get("event", record.getMessage()),
            "version": __version__,
        }
        # Only a record that itself carries `exc_info`/`stack_info` gets a `traceback`
        # field. screw's own helpers (`build_failed()` et al.) never pass `exc_info=`, so
        # no worker-side traceback text leaves this process through screw's own
        # vocabulary and their records are unchanged by this branch. What it serves is the
        # record screw does not control: uvicorn's "Exception in ASGI application" line
        # (`log_config=None`) sets real `exc_info`, and a genuinely unclassified crash in a
        # route is the one case that needs the traceback. `json.dumps` below escapes its
        # embedded newlines, so it still lands as one physical line.
        if record.exc_info:
            payload["traceback"] = self.formatException(record.exc_info)
        elif record.exc_text:
            # A second handler formatting the same record: stdlib's own Formatter caches
            # the rendered text on `exc_text` after the first `formatException()` call.
            payload["traceback"] = record.exc_text
        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)
        for key, value in record.__dict__.items():
            if key in _STANDARD_LOGRECORD_ATTRS or key == "event":
                continue
            payload[key] = value
        # default=str: an unexpected non-serializable value must never raise inside a log
        # call and turn a clean 422 into a 500. ensure_ascii keeps its stdlib default
        # (True) so one record stays one physical line regardless of the stream's real
        # encoding. No sort_keys: insertion order is the stable order (envelope first,
        # then the event's own fields in the order its helper built them).
        return json.dumps(payload, default=str)


class _JsonHandler(logging.StreamHandler[TextIO]):
    """A `StreamHandler` subclass with no added behaviour: a pure identity marker.

    `configure()`'s idempotency guard checks `isinstance(h, _JsonHandler)` against the
    root logger's own handler list, not a module-level flag: the "is this process already
    configured" state lives on the object it describes, so a test can tear the handler
    down (tests/conftest.py's autouse fixture) without reaching into this module's
    privates, and a freshly spawned worker that re-imports this module cannot resurrect a
    stale flag that never existed in its own interpreter.
    """


def _parse_level(raw: str) -> int:
    """`SCREW_LOG_LEVEL`, falling back to INFO on anything `logging` doesn't recognise --
    the same "read once, fall back on nonsense" shape as `int_env`.

    `logging.getLevelName(name)` is the stdlib's own validity check: it returns an int for
    a real level name and a `"Level <name>"` string for anything else.
    """
    level = logging.getLevelName(raw.upper())
    return level if isinstance(level, int) else logging.INFO


def configure() -> None:
    """Install one stderr JSON handler on the root logger -- idempotently.

    Called from both `cli.cmd_serve` (before `uvicorn.run`) and `app.py`'s `lifespan()`
    startup. Under the default `SCREW_WORKERS=1` both call sites run in the same process,
    so the second call must be a no-op: spur verified live that a naive `configure()`
    double-adds a handler and doubles every printed line. The `lifespan()` call site is
    not a defensive fallback -- it is the only call that reaches every uvicorn worker once
    `SCREW_WORKERS>1` (see this module's docstring).

    Reads the level from the environment itself rather than taking a level argument, so
    the two call sites cannot disagree about it within one process.

    Stderr, matching the convention `cli.py` sets: stdout is product output (`screw info`
    prints JSON there), stderr is diagnostics. uvicorn's own default access-to-stdout /
    rest-to-stderr split collapses into this one stream; `docker logs` captures both.
    """
    root = logging.getLogger()
    if any(isinstance(handler, _JsonHandler) for handler in root.handlers):
        return
    handler = _JsonHandler(sys.stderr)
    handler.setFormatter(_JsonFormatter())
    root.addHandler(handler)
    root.setLevel(_parse_level(os.environ.get("SCREW_LOG_LEVEL", "INFO")))


def _part_fields(p: FastenerParams) -> dict[str, object]:
    """The part identity every per-request record carries: `kind` and `slug` for the human
    eye and grep, plus `params` -- only the fields that differ from default -- so a failed
    build is reproducible by pasting `params` back into `/api/<kind>/model.stl?...`,
    exactly the shareable-link form L02 keeps stable. Built here, once, so the fields can
    never drift out of sync with each other. An all-default part yields an empty `params`
    object, emitted as such, not omitted: "no non-default params" is itself a fact.
    """
    return {"kind": p.kind, "slug": p.slug(), "params": p.model_dump(exclude_defaults=True)}


def _ms(seconds: float) -> int:
    """Whole milliseconds via Python's `round()` (half-to-even on an exact .5 tie) --
    never a float. Sub-millisecond precision would be false precision given
    `time.monotonic()`'s real granularity and the IPC this duration deliberately includes.
    """
    return round(seconds * 1000)


def _emit(level: int, event: str, fields: dict[str, object]) -> None:
    """The one call site that ever touches the stdlib logger directly -- every per-event
    helper below routes through here, which is what makes ruff's `G004`/`LOG015` rules
    enforce "no f-string in a log call" / "no bare root-logger call" by construction,
    since `app.py` and `pool.py` never call `logging` directly.

    `event` rides as a field (a reader's primary key into the record) *and* as the
    message: the degraded paths -- a bare `uvicorn screw.app:app`, `docker/smoke.py`, a
    `TestClient` used without running the app's lifespan -- fall through to stdlib's
    unconfigured-root `lastResort` handler (stderr, WARNING+), which prints only the
    message, not `extra`. Passing `event` as the message means those paths still print
    something legible instead of an empty line.
    """
    _LOG.log(level, event, extra={"event": event, **fields})


def build_started(request: str, p: FastenerParams, fmt: str, quality: str) -> None:
    """`build.started` at INFO, emitted immediately before the backend call -- the one
    place a build actually begins. No `duration_ms`: a start record has nothing to time yet.
    """
    _emit(logging.INFO, "build.started",
          {"request": request, **_part_fields(p), "fmt": fmt, "quality": quality})


def export_served(request: str, p: FastenerParams, fmt: str, quality: str, *,
                   source: str, encoding: str, duration_s: float) -> None:
    """`export.served` at INFO -- the one record every model request emits, whichever of
    the three paths served it. `source` is one of exactly three values, each naming a code
    path that exists in `app._serve()`: `"cache"` (a byte-cache hit, no build slot at all),
    `"compressed"` (the raw bytes were already cached but this encoding was not -- gzip
    runs inside the slot), `"built"` (a fresh pool build under the slot).
    """
    _emit(logging.INFO, "export.served",
          {"request": request, **_part_fields(p), "fmt": fmt, "quality": quality,
           "encoding": encoding, "source": source, "duration_ms": _ms(duration_s)})


def build_failed(request: str, p: FastenerParams, fmt: str, quality: str, *,
                  exc: Exception, duration_s: float) -> None:
    """`build.failed` -- one record per failing request, at the level "whose fault is it"
    picks: WARNING for `BuildError` (a 422, the user's parameters, deterministic), ERROR
    for everything else (`BuildTimeout`, `BrokenProcessPool` -- both 503s, the service's
    fault). An unrecognised future failure class also lands at ERROR: a failure mode this
    module has not classified is the service's problem until someone says otherwise.

    `exception` is `type(exc).__name__`. No traceback text rides on the record:
    `BuildError`'s own message already carries the kernel text, and the other two classes
    have no kernel traceback at all -- publishing `exc_info` here would leak worker-side
    file paths and interpreter internals into a stream anyone reading `docker logs` can
    see, for no incident value the class name doesn't already give (T-01-05).
    """
    level = logging.WARNING if isinstance(exc, BuildError) else logging.ERROR
    _emit(level, "build.failed",
          {"request": request, **_part_fields(p), "fmt": fmt, "quality": quality,
           "exception": type(exc).__name__, "duration_ms": _ms(duration_s)})


def queue_refused(request: str, p: FastenerParams, fmt: str, quality: str, *,
                   in_flight: int, max_queued: int) -> None:
    """`queue.refused` at WARNING (capacity, not breakage): one record per refused
    request, carrying the identity of the part that was turned away alongside how close
    to the ceiling the service was.
    """
    _emit(logging.WARNING, "queue.refused",
          {"request": request, **_part_fields(p), "fmt": fmt, "quality": quality,
           "in_flight": in_flight, "max_queued": max_queued})


def worker_replaced(*, slot: int, cause: str) -> None:
    """`worker.replaced` at ERROR (the service's fault; these are the 503s), with the hash
    slot and the `cause` -- `"timeout"` or `"broken_pool"` -- distinguishing a wedged build
    from a worker that died on its own.

    `/api/health` exposes only a `workers_replaced` count, so this log record is the only
    place the *when* and the *why* of a replacement can live. It carries no `request` id:
    the pool has no request context to give it, and the `build.failed` record that
    precedes it (emitted from `app.py`, which does have one) already does.
    """
    _emit(logging.ERROR, "worker.replaced", {"slot": slot, "cause": cause})
