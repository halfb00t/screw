"""Structured logging: the traced proof, the formatter's edges, and the level knob.
tests/test_api.py covers the per-request vocabulary's branches with `caplog`; this file
covers everything specific to `records.py` itself.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path
from typing import cast

import pytest
from fastapi.testclient import TestClient

from screw import calc as calc_package
from screw import records
from screw.app import app, build_backend
from screw.params import BoltParams, FastenerParams
from screw.solid import Format, Quality, export

client = TestClient(app)


async def _inline_backend(p: FastenerParams, fmt: str, quality: str) -> bytes:
    # Same seam tests/test_api.py uses: app.state.pool never exists for this module-level
    # TestClient (no `with`, so lifespan never runs), so the dependency is overridden with
    # an in-process build instead.
    return export(p, cast(Format, fmt), cast(Quality, quality))


def test_a_model_request_emits_one_export_served_line_that_json_loads_round_trips(
        capsys: pytest.CaptureFixture[str]) -> None:
    """The one end-to-end check of the one path: configure, the call site, the formatter,
    the handler, the stream -- proven by reading the real stderr output of a real request
    back through `json.loads`, not by inspecting any layer in isolation."""
    records.configure()
    app.dependency_overrides[build_backend] = lambda: _inline_backend
    try:
        resp = client.get("/api/bolt/model.stl", params={"quality": "preview", "d": 9.1})
    finally:
        app.dependency_overrides.pop(build_backend, None)
    assert resp.status_code == 200

    # Every line on stderr, not just the last: httpx2 (the TestClient's own transport)
    # also logs at INFO once the root handler is installed, and its own "HTTP Request"
    # line can land after ours -- a real `screw serve` process has no httpx client
    # logging its own requests, so this is a test-harness artifact, not a production
    # ordering guarantee to assert on.
    lines = capsys.readouterr().err.strip().splitlines()
    assert lines, "configure() should have installed a handler that wrote to stderr"
    served = [record for line in lines
              if (record := json.loads(line)).get("event") == "export.served"]
    assert served, "no export.served record found on stderr"
    record = served[-1]

    assert record["event"] == "export.served"
    for field in ("ts", "level", "logger", "version", "request", "kind", "slug", "params",
                  "fmt", "quality", "encoding", "source", "duration_ms"):
        assert field in record, f"missing field: {field}"
    assert record["kind"] == "bolt"
    assert record["params"] == {"d": 9.1}
    assert record["source"] in ("cache", "compressed", "built")


def test_configure_called_twice_installs_exactly_one_handler() -> None:
    """The default SCREW_WORKERS=1 deployment runs both call sites (cli.cmd_serve and
    app.py's lifespan()) in one process -- a configure() that always added a handler
    would print every production line twice."""
    records.configure()
    records.configure()
    handlers = [h for h in logging.getLogger().handlers
                if isinstance(h, records._JsonHandler)]
    assert len(handlers) == 1


def _make_record(**extra: object) -> logging.LogRecord:
    """A LogRecord built with `Logger.makeRecord` and `extra=`, the same mechanism `_emit`
    uses, so these tests exercise `_JsonFormatter` directly, independent of the logging
    call site."""
    logger = logging.getLogger("screw.records")
    return logger.makeRecord("screw.records", logging.INFO, __file__, 1,
                             extra.get("event", "test.probe"), (), None, extra=extra)


def test_the_formatter_round_trips_every_application_field_through_json_loads() -> None:
    """A formatter that dropped `extra` could not pass this, unlike a branch test that
    only checks the fields it happens to look at."""
    record = _make_record(event="export.served", request="abc12345", kind="bolt",
                          slug="bolt_d8", params={"d": 8}, duration_ms=42)
    payload = json.loads(records._JsonFormatter().format(record))

    assert payload["event"] == "export.served"
    assert payload["request"] == "abc12345"
    assert payload["kind"] == "bolt"
    assert payload["slug"] == "bolt_d8"
    assert payload["params"] == {"d": 8}
    assert payload["duration_ms"] == 42
    for envelope_field in ("ts", "level", "logger", "version"):
        assert envelope_field in payload


def _raise(message: str) -> None:
    """Raises from a named function, not inline in a test's `try` block (ruff TRY301), so
    the two traceback tests below get a real, multi-frame `exc_info`/`__traceback__` -- the
    same shape a genuine unclassified crash produces -- rather than a synthetic one built
    by hand."""
    raise ValueError(message)


def _record_with_a_real_traceback(message: str) -> logging.LogRecord:
    """The same record shape uvicorn's own `"Exception in ASGI application"` log call
    builds (`h11_impl.py`'s `run_asgi`): a real `exc_info` tuple, not a hand-built one --
    building `record` inside the `except` and returning it there (rather than assigning
    to an outer variable) is what keeps mypy's `possibly-undefined` check satisfied
    without a `# type: ignore`."""
    try:
        _raise(message)
    except ValueError:
        return logging.getLogger("uvicorn.error").makeRecord(
            "uvicorn.error", logging.ERROR, __file__, 1,
            "Exception in ASGI application", (), sys.exc_info())
    raise AssertionError("unreachable: _raise always raises")


def test_the_formatter_renders_a_real_traceback_into_a_dedicated_field() -> None:
    """A record that itself carries `exc_info` -- uvicorn's own `"Exception in ASGI
    application"` line is exactly this shape, since `cli.cmd_serve` passes
    `log_config=None` -- must not have its traceback silently discarded: a genuinely
    unclassified crash in `_serve()` has nothing else to read anywhere. screw's own helpers
    (`build_failed()`) never pass `exc_info=` to `_emit`, so their records are unchanged by
    this."""
    record = _record_with_a_real_traceback("boom, unexpected solid bug")
    line = records._JsonFormatter().format(record)

    # One physical line is the whole point (jq-readable): a real traceback's embedded
    # newlines must stay escaped inside the JSON string value, not break the line.
    assert "\n" not in line
    payload = json.loads(line)
    assert "ValueError" in payload["traceback"]
    assert "boom, unexpected solid bug" in payload["traceback"]


def test_build_failed_helper_never_carries_a_traceback_field(
        capsys: pytest.CaptureFixture[str]) -> None:
    """The design boundary the traceback rendering must not cross: `build_failed()` never
    passes `exc_info=` to `_emit`, so its own records stay traceback-free (worker-side file
    paths and interpreter internals would otherwise reach whoever reads `docker logs`) even
    after `_JsonFormatter` learns to render one for records that do carry it."""
    records.configure()
    try:
        _raise("boom")
    except ValueError as exc:
        records.build_failed("req00001", BoltParams(), "stl", "fine", exc=exc,
                             duration_s=0.01)
    lines = [line for line in capsys.readouterr().err.strip().splitlines()
             if json.loads(line).get("event") == "build.failed"]
    assert lines, "no build.failed record found on stderr"
    record = json.loads(lines[-1])
    assert "traceback" not in record
    assert record["kind"] == "bolt"
    assert record["exception"] == "ValueError"


def test_a_field_with_a_newline_and_non_ascii_stays_one_physical_line() -> None:
    """The one-record-one-line contract `jq` depends on, whatever the stream's real
    encoding is -- the formatter must escape, not emit raw bytes."""
    tricky = "line one\nline two: thread angle ° façade"
    record = _make_record(event="export.served", note=tricky)
    line = records._JsonFormatter().format(record)

    assert "\n" not in line
    assert json.loads(line)["note"] == tricky


def test_two_records_of_the_same_event_serialize_identical_key_order() -> None:
    """Two records that compare equal on event must not disagree on shape -- envelope
    first, then the event's own fields in the order `_emit` built them, regardless of what
    the *values* happen to be."""
    def keys_for(request_value: str) -> list[str]:
        record = _make_record(event="export.served", request=request_value, source="cache")
        return list(json.loads(records._JsonFormatter().format(record)))

    assert keys_for("aaaaaaaa") == keys_for("bbbbbbbb")


def test_ms_is_an_integer_with_half_to_even_rounding() -> None:
    """Never a float; a sub-millisecond duration reads 0; the exact half-millisecond
    tie-break is Python's own round() (half-to-even), pinned as a recorded contract rather
    than left as an accident of the implementation."""
    assert type(records._ms(0.0179)) is int
    assert records._ms(0.00001) == 0            # sub-millisecond
    assert records._ms(0.0025) == 2              # exact 2.5ms tie -> even (2)
    assert records._ms(0.0035) == 4              # exact 3.5ms tie -> even (4)


def test_parse_level_falls_back_to_info_on_nonsense_and_empty() -> None:
    """The same "read once, fall back on nonsense" shape as `int_env`."""
    assert records._parse_level("INFO") == logging.INFO
    assert records._parse_level("warning") == logging.WARNING  # case-insensitive
    assert records._parse_level("NONSENSE") == logging.INFO
    assert records._parse_level("") == logging.INFO


def test_screw_log_level_moves_the_threshold(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """Driven through the real `configure()` and the env var, not just `_parse_level` in
    isolation: with SCREW_LOG_LEVEL=WARNING an INFO record is suppressed and a WARNING
    record still gets through -- one step either side of the threshold."""
    monkeypatch.setenv("SCREW_LOG_LEVEL", "WARNING")
    records.configure()

    records._emit(logging.INFO, "test.info.suppressed", {})
    records._emit(logging.WARNING, "test.warning.visible", {})

    events = [json.loads(line)["event"]
              for line in capsys.readouterr().err.strip().splitlines()]
    assert "test.info.suppressed" not in events
    assert "test.warning.visible" in events


def test_screw_log_level_unset_defaults_to_info(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SCREW_LOG_LEVEL", raising=False)
    records.configure()
    assert logging.getLogger().level == logging.INFO


def test_configure_twice_still_emits_exactly_one_line_per_record(
        capsys: pytest.CaptureFixture[str]) -> None:
    """The default SCREW_WORKERS=1 deployment runs both call sites in one process -- a
    naive configure() would double every printed line, not just double-install the
    handler."""
    records.configure()
    records.configure()
    handlers = [h for h in logging.getLogger().handlers
                if isinstance(h, records._JsonHandler)]
    assert len(handlers) == 1

    records._emit(logging.INFO, "test.idempotency.probe", {})
    lines = [line for line in capsys.readouterr().err.strip().splitlines()
             if json.loads(line)["event"] == "test.idempotency.probe"]
    assert len(lines) == 1


def test_calc_module_stays_log_free() -> None:
    """calc runs on every keystroke in the UI and must never import logging, nor the module
    that owns it (`screw.records`): cheap insurance against drift into the module that
    matters most to keep pure. The pyproject.toml import-linter contract "The thread maths
    stays free of the logger" is the suspenders for this same claim; this regex is the
    belt, so it must catch a `from .records import ...`, `from screw.records import ...`,
    `import screw.records` and `from screw import records` edit too, not only a direct
    `import logging`. calc is a package, so every module under it is scanned."""
    assert calc_package.__file__ is not None
    sources = sorted(Path(calc_package.__file__).parent.rglob("*.py"))
    assert sources, "a glob that silently matched nothing must fail, not pass"
    for source in sources:
        assert not re.search(
            r"^\s*(import|from)\s+(logging|\.+records|screw\.records)\b"
            r"|^\s*from\s+(screw|\.+)\s+import\s+.*\brecords\b",
            source.read_text(), re.MULTILINE), source
