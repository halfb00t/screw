"""The load reading (07-08): the server in the image under concurrent cold requests (R15 to R18).

The server is a local `http.server` fake and `docker` is a fake that answers the few commands the
driver sends, so the shared queue, the encoding, the statuses and the deadline are exercised
without an image. The instrument server's pool recorder is tested on a fake pool call.
"""

from __future__ import annotations

import asyncio
import gzip
import json
import re
import statistics
import subprocess
import sys
import threading
import time
import urllib.parse
from collections.abc import Iterator, Sequence
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from bench import oper, oper_load

REPO_ROOT = Path(__file__).resolve().parents[1]
CAP = 12 * 1024**3
PEAK = 123_456_789


# --- p95 -----------------------------------------------------------------------------------------


def test_p95_is_the_19th_of_20_cut_points_from_20_samples() -> None:
    samples = [float(i) for i in range(1, 21)]
    assert oper_load.p95(samples) == statistics.quantiles(samples, n=20)[18]


def test_p95_from_fewer_than_20_samples_is_none() -> None:
    assert oper_load.p95([1.0] * 19) is None
    assert oper_load.p95([]) is None


# --- a fake server and a fake docker -------------------------------------------------------------


HEALTH_BODY = b'{"status": "ok"}'
INFO_BODY = json.dumps({"rows": [{"label": "pitch", "value": 1.0}] * 40}).encode()
PRESETS = {"bolt": {"rows": [{"fields": {"d": 6.0}}, {"fields": {"d": 404.0}}]},
           "nut": {"rows": [{"fields": {"d": 6.0}}]}}


def _catalogue(path: str, query: dict[str, str]) -> tuple[int, bytes]:
    """The fake's kinds, presets and info documents; an info document of `d` 404 is a 404."""
    if path == "/api/kinds":
        return 200, json.dumps({"default": "bolt", "kinds": ["bolt", "nut"]}).encode()
    if path == "/api/presets":
        return 200, json.dumps(PRESETS[query["kind"]]).encode()
    return (404, b"{}") if query.get("d") == "404.0" else (200, INFO_BODY)


class _Server:
    """A local server that answers `/api/health` at once and a model request after a sleep set by
    its `d` param (in hundredths of a second), with the status set by its `status` param. It
    records what each model request asked for and how many were in flight at once."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.seen: list[tuple[str, str | None]] = []
        self.in_flight = 0
        self.most_in_flight = 0
        self.health = 0
        self.order: list[str] = []  # shared with a _Docker: what happened, in order
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_: object) -> None:  # quiet: the test reads `seen`
                return None

            def do_GET(self) -> None:
                url = urllib.parse.urlsplit(self.path)
                query = dict(urllib.parse.parse_qsl(url.query))
                if url.path == "/api/health":
                    with outer.lock:
                        outer.health += 1
                    self._send(200, HEALTH_BODY)
                    return
                if url.path in ("/api/kinds", "/api/presets") or url.path.endswith("/info"):
                    outer.order.append("body")
                    self._send(*_catalogue(url.path, query))
                    return
                with outer.lock:
                    outer.seen.append((self.path, self.headers.get("Accept-Encoding")))
                    outer.in_flight += 1
                    outer.most_in_flight = max(outer.most_in_flight, outer.in_flight)
                try:
                    time.sleep(float(query.get("d", "0")) / 100)
                finally:
                    with outer.lock:
                        outer.in_flight -= 1
                status = int(float(query.get("status", "200")))
                kind = {422: "build_error", 503: "timeout", 500: "boom"}.get(status)
                body = b"x" * 1000 if kind is None else json.dumps(
                    {"detail": [{"type": kind}]}).encode()
                self._send(status, body, {"Retry-After": "5"} if status == 503 else {})

            def _send(self, status: int, body: bytes, extra: dict[str, str] | None = None) -> None:
                self.send_response(status)
                self.send_header("Content-Length", str(len(body)))
                for key, value in (extra or {}).items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(body)

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, args=(0.01,), daemon=True).start()


@pytest.fixture
def server() -> Iterator[_Server]:
    fake = _Server()
    yield fake
    fake.httpd.shutdown()
    fake.httpd.server_close()


class _Docker:
    """Answers `docker run`, `port`, `inspect`, `exec` (the peak reader, the pool log, the
    HEALTHCHECK) and `rm` as the driver sends them, and keeps every argv."""

    def __init__(self, port: int, peak: int = PEAK, pool: str = "",
                 order: list[str] | None = None) -> None:
        self.port, self.peak, self.pool = port, peak, pool
        self.calls: list[list[str]] = []
        self.order: list[str] = [] if order is None else order

    def __call__(self, args: Sequence[str], _timeout: float) -> subprocess.CompletedProcess[str]:
        argv = list(args)
        self.calls.append(argv)
        out = ""
        if argv[0] == "port":
            out = f"127.0.0.1:{self.port}\n"
        elif argv[0] == "inspect":
            out = "true" if "Running" in argv[2] else "false"
        elif argv[0] == "exec" and oper_load._PEAK_CODE in argv:
            self.order.append("peak")
            out = json.dumps({"peak": self.peak, "oom_kills": 0})
        elif argv[0] == "exec" and oper_load._POOL_LOG_CODE in argv:
            out = self.pool
        return subprocess.CompletedProcess(argv, 0, out, "")


@pytest.fixture(autouse=True)
def _fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(oper_load, "IDLE_S", 0.0)
    monkeypatch.setattr(oper_load, "HEALTH_EVERY_S", 0.02)
    monkeypatch.setattr(oper_load, "HEALTHCHECK_EVERY_S", 0.02)


def _entry(i: int, **params: float) -> dict[str, object]:
    return {"label": f"part-{i}", "kind": "bolt", "params": params, "artifact": "stl-preview"}


def _point(mix: list[dict[str, object]], clients: int = 2, **over: object) -> dict[str, object]:
    return {"workers": 1, "queue": 2, "clients": clients, "solid_cache": 4, "bodies": False,
            "mix": mix, **over}


def _run(server: _Server, point: dict[str, object], deadline_s: float = 30.0,
         docker: _Docker | None = None) -> tuple[dict[str, object], _Docker]:
    fake = docker or _Docker(server.port)
    return oper_load.run_load(point, "screw:ci", CAP, deadline_s, name="t", docker=fake), fake


# --- the shared queue ----------------------------------------------------------------------------


def test_six_requests_on_two_clients_each_go_once_from_one_queue_in_mix_order(
        server: _Server) -> None:
    # Request 0 is slow and the rest are quick: from one shared queue the second client takes 1 to
    # 4 while the first holds 0, and the first takes 5 when 0 ends. Dealt in advance, the first
    # client would have held 0, 2 and 4.
    mix = [_entry(0, d=35), *(_entry(i, d=10) for i in range(1, 6))]
    record, _ = _run(server, _point(mix))
    assert record["status"] == "ok"
    requests = record["requests"]
    assert isinstance(requests, list)
    assert [r["index"] for r in requests] == list(range(6))
    assert sorted(path for path, _ in server.seen) == sorted(
        oper_load.model_path(entry) for entry in mix)
    assert len(server.seen) == 6
    starts = [float(r["start_s"]) for r in requests]
    ends = [float(r["end_s"]) for r in requests]
    assert max(starts[:2]) < min(ends)  # the first two start together
    assert starts[1:5] == sorted(starts[1:5])
    assert starts[5] >= ends[0]
    assert server.most_in_flight == 2
    for r in requests:
        assert (r["status_code"], r["bytes"], r["content_encoding"]) == (200, 1000, "identity")
        assert r["label"] == f"part-{r['index']}"


def test_every_load_request_asks_for_identity(server: _Server) -> None:
    _run(server, _point([_entry(i) for i in range(3)]))
    assert [encoding for _, encoding in server.seen] == ["identity"] * 3


def test_an_ok_reading_records_the_health_walls_and_peaks_and_no_p95_below_20(
        server: _Server) -> None:
    pool = json.dumps({"slot": 0, "artifact": "stl-preview", "pending": [], "submit_s": 1.0,
                       "end_s": 2.0, "outcome": "ok"}) + "\n"
    record, _ = _run(server, _point([_entry(i, d=10) for i in range(3)]),
                     docker=_Docker(server.port, pool=pool))
    assert record["status"] == "ok"
    health = record["health"]
    assert isinstance(health, list)
    assert health
    assert all(h["status_code"] == 200 and float(h["wall_s"]) >= 0 for h in health)
    assert (record["idle_peak_bytes"], record["memory_peak_bytes"]) == (PEAK, PEAK)
    assert float(str(record["time_to_healthy_s"])) >= 0
    assert record["pool_calls"] == [json.loads(pool)]
    assert record["latency"] == {"all": {"samples": 3, "p95_s": None},
                                 "stl-preview": {"samples": 3, "p95_s": None}}


def test_the_container_argv_holds_the_four_settings_as_separate_elements(
        server: _Server) -> None:
    _, fake = _run(server, _point([_entry(0)]))
    run = fake.calls[0]
    assert run[:2] == ["run", "-d"]
    for setting in ("SCREW_BUILD_WORKERS=1", "SCREW_MAX_QUEUED_BUILDS=2",
                    "SCREW_EXPORT_CACHE_MB=1", "SCREW_SOLID_CACHE=4"):
        assert run[run.index(setting) - 1] == "-e"
    assert "127.0.0.1::8000" in run
    assert run[-6:] == ["-m", "bench.oper_serve", "--deadline", "30", "--pool-log",
                        oper_load.POOL_LOG]
    assert fake.calls[-1] == ["rm", "-f", "t"]


def test_a_point_with_solid_cache_2_starts_the_server_with_2(server: _Server) -> None:
    _, fake = _run(server, _point([_entry(0)], solid_cache=2))
    assert "SCREW_SOLID_CACHE=2" in fake.calls[0]
    assert "SCREW_SOLID_CACHE=4" not in fake.calls[0]


# --- the statuses --------------------------------------------------------------------------------


@pytest.mark.parametrize(("status_code", "status"), [
    (422, "refused"), (503, "killed"), (500, "crashed")])
def test_a_request_that_is_not_200_gives_its_status_and_no_figures(
        server: _Server, status_code: int, status: str) -> None:
    record, _ = _run(server, _point([_entry(0), _entry(1, status=status_code), _entry(2)]))
    assert record["status"] == status
    assert set(record) == {"status", "requests"}
    requests = record["requests"]
    assert isinstance(requests, list)
    assert [r["status_code"] for r in requests] == [200, status_code, 200]
    for r in requests:
        assert not {"start_s", "end_s", "bytes"} & set(r)


def test_a_reading_past_its_deadline_is_killed(server: _Server) -> None:
    record, fake = _run(server, _point([_entry(0, d=300), _entry(1)], clients=1), deadline_s=1.0)
    assert record["status"] == "killed"
    assert "memory_peak_bytes" not in record
    assert fake.calls[-1] == ["rm", "-f", "t"]


def test_a_peak_at_the_cap_is_capped(server: _Server) -> None:
    record, _ = _run(server, _point([_entry(0)]), docker=_Docker(server.port, peak=CAP))
    assert record["status"] == "capped"
    assert "memory_peak_bytes" not in record


# --- the HEALTHCHECK, the bodies and the gzip levels --------------------------------------------


def _dockerfile_healthcheck() -> list[str]:
    """The HEALTHCHECK's exec form, read here without the driver's code."""
    text = (REPO_ROOT / "Dockerfile").read_text()
    match = re.search(r"^HEALTHCHECK [^\n]*\\\n\s*CMD (\[.*\])$", text, re.MULTILINE)
    assert match is not None
    argv = json.loads(match.group(1))
    assert isinstance(argv, list)
    return [str(arg) for arg in argv]


def test_the_probe_is_the_dockerfiles_healthcheck_command() -> None:
    argv = oper_load.healthcheck_argv()
    assert argv == _dockerfile_healthcheck()
    assert argv[:2] == ["python", "-c"]
    assert "timeout=1" in argv[2]


def test_a_dockerfile_without_a_healthcheck_is_refused(tmp_path: Path) -> None:
    (tmp_path / "Dockerfile").write_text("FROM python:3.12-slim\nCMD [\"screw\"]\n")
    with pytest.raises(ValueError, match="no HEALTHCHECK"):
        oper_load.healthcheck_argv(tmp_path / "Dockerfile")


def test_the_load_runs_the_healthcheck_through_docker_exec_and_records_each_wall(
        server: _Server) -> None:
    record, fake = _run(server, _point([_entry(i, d=10) for i in range(4)], clients=1))
    assert record["status"] == "ok"
    probe = ["exec", "t", *_dockerfile_healthcheck()]
    assert probe in fake.calls
    checks = record["healthcheck"]
    assert isinstance(checks, list)
    assert len(checks) == fake.calls.count(probe)
    assert all(c["exit_code"] == 0 and float(c["wall_s"]) >= 0 for c in checks)


def test_the_bodies_have_their_identity_and_gzip_lengths_and_a_404_has_none(
        server: _Server) -> None:
    base = f"http://127.0.0.1:{server.port}"
    rows = oper_load.catalogue_rows(base, time.monotonic() + 30)
    assert rows == [("bolt", {"d": 6.0}), ("bolt", {"d": 404.0}), ("nut", {"d": 6.0})]
    bodies = oper_load.measure_bodies(base, rows)
    assert [b["path"] for b in bodies] == [
        "/api/health", "/api/presets?kind=bolt", "/api/presets?kind=nut",
        "/api/bolt/info?d=6.0", "/api/bolt/info?d=404.0", "/api/nut/info?d=6.0"]
    expected = {"/api/health": HEALTH_BODY, "/api/bolt/info?d=6.0": INFO_BODY,
                "/api/nut/info?d=6.0": INFO_BODY,
                "/api/presets?kind=bolt": json.dumps(PRESETS["bolt"]).encode(),
                "/api/presets?kind=nut": json.dumps(PRESETS["nut"]).encode()}
    for body in bodies:
        if body["path"] == "/api/bolt/info?d=404.0":
            assert body == {"path": body["path"], "status_code": 404}
            continue
        raw = expected[str(body["path"])]
        assert body["bytes"] == len(raw)
        assert body["gzip"] == {str(level): len(gzip.compress(raw, level))
                                for level in (1, 6, 9)}


def test_the_bodies_are_read_after_the_end_peak(server: _Server) -> None:
    fake = _Docker(server.port, order=server.order)
    record, _ = _run(server, _point([_entry(0)], bodies=True), docker=fake)
    assert record["status"] == "ok"
    assert server.order.count("peak") == 2  # the idle peak and the end peak
    assert server.order.index("body") > len(server.order) - 1 - server.order[::-1].index("peak")
    bodies = record["bodies"]
    assert isinstance(bodies, list)
    assert len(bodies) == 6


def test_no_bodies_are_read_unless_the_point_asks(server: _Server) -> None:
    record, _ = _run(server, _point([_entry(0)]))
    assert "bodies" not in record
    assert "body" not in server.order


def test_a_part_point_with_gzip_levels_reads_its_peak_before_the_first_level(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    from bench import oper_child

    order: list[object] = []
    compress = gzip.compress

    def counting(data: bytes, compresslevel: int = 9, *, mtime: float | None = None) -> bytes:
        order.append(compresslevel)
        return compress(data, compresslevel, mtime=mtime)

    def peak() -> int:
        order.append("peak")
        return PEAK

    monkeypatch.setattr(oper_child, "read_peak", peak)
    monkeypatch.setattr(gzip, "compress", counting)  # the module the child calls through
    point = {"kind": "bolt", "params": {"d": 4.0, "length": 8.0, "thread_length": 8.0},
             "artifact": "stl-preview", "gzip_levels": [1, 6, 9]}
    assert oper_child.main([json.dumps(point)]) == 0
    assert order == [1, "peak", 1, 6, 9]  # R2's level-1 gzip, the peak, then R19's levels
    record = oper.parse_child_line(capsys.readouterr().out.strip())
    levels = record["gzip"]
    assert isinstance(levels, list)
    assert [entry["level"] for entry in levels] == [1, 6, 9]
    assert levels[0]["bytes"] == record["gzip1_bytes"]
    assert all(isinstance(entry["bytes"], int) and entry["seconds"] >= 0 for entry in levels)


def test_the_parent_passes_gzip_levels_to_the_child_and_records_them(tmp_path: Path) -> None:
    _write(tmp_path, [{"label": "b", "kind": "bolt", "params": {}, "artifact": "stl-fine",
                       "gzip_levels": [1, 6, 9]}])
    (point,) = oper.load_set("mini", tmp_path).points
    assert json.loads(point.as_json())["gzip_levels"] == [1, 6, 9]


@pytest.mark.parametrize("levels", [[5], [0], [1, 1], [], ["1"], [True], 6])
def test_the_matrix_refuses_an_unknown_gzip_level_with_exit_2(
        levels: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _write(tmp_path, [{"label": "b", "kind": "bolt", "params": {}, "artifact": "stl-fine",
                       "gzip_levels": levels}])
    monkeypatch.setattr(oper, "POINTS_DIR", tmp_path)
    assert oper.main(["matrix", "--set", "mini"]) == 2
    assert "gzip_levels" in capsys.readouterr().err


@pytest.mark.parametrize("entry", [
    {"level": 1, "bytes": 10}, {"level": 1, "bytes": -1, "seconds": 0.1},
    {"level": 1, "bytes": 10, "seconds": "fast"}, {"level": True, "bytes": 10, "seconds": 0.1}])
def test_a_child_line_with_a_bad_gzip_entry_is_refused(entry: dict[str, object]) -> None:
    line = json.dumps({"status": "ok", "build_s": 1.0, "export_s": 1.0, "bytes": 10,
                       "memory_peak_bytes": PEAK, "gzip": [entry]})
    with pytest.raises(ValueError, match="gzip"):
        oper.parse_child_line(line)


# --- the instrument server -----------------------------------------------------------------------


def test_the_pool_recorder_writes_one_line_per_call_with_what_was_pending(
        tmp_path: Path) -> None:
    from bench import oper_serve
    from screw.params import BoltParams
    from screw.pool import BuildPool

    async def run(pool: BuildPool, p: object, timeout: float, func: object, part: object,
                  fmt: str, quality: str) -> bytes:
        await asyncio.sleep(0.05 if quality == "fine" else 0.0)
        return b"x"

    class _Pool:
        workers = 2

    log = tmp_path / "pool.jsonl"
    recorded = oper_serve.record_calls(run, log)
    p = BoltParams()

    pool = _Pool()

    async def two() -> None:
        first: asyncio.Task[bytes] = asyncio.create_task(
            recorded(pool, p, 30.0, None, p, "stl", "fine"))  # type: ignore[arg-type]
        await asyncio.sleep(0.01)
        await recorded(pool, p, 30.0, None, p, "step", "fine")  # type: ignore[arg-type]
        await first

    asyncio.run(two())
    lines = [json.loads(line) for line in log.read_text().splitlines()]
    assert len(lines) == 2
    by_artifact = {line["artifact"]: line for line in lines}
    assert by_artifact["stl-fine"]["pending"] == []
    assert by_artifact["step"]["pending"] == ["stl-fine"]
    for line in lines:
        assert line["slot"] == hash(p) % 2
        assert line["end_s"] >= line["submit_s"]
        assert line["outcome"] == "ok"


# --- the driver runs on a bare interpreter -------------------------------------------------------


def test_importing_the_load_driver_loads_no_screw_module() -> None:
    code = (f"import sys; sys.path.insert(0, {str(REPO_ROOT)!r}); import bench.oper_load; "
            "print(sorted(m for m in sys.modules if m == 'screw' or m.startswith('screw.')))")
    out = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True,
                         check=True).stdout.strip()
    assert out == "[]"


# --- the parent's load point ---------------------------------------------------------------------

MIX_ENTRY = {"label": "default-bolt", "kind": "bolt", "params": {}, "artifact": "stl-preview"}


def _load_point(**over: object) -> dict[str, object]:
    return {"label": "load-n1", "kind": "load", "workers": 1, "queue": 2, "clients": 2,
            "mix": [MIX_ENTRY], **over}


def _write(directory: Path, points: list[dict[str, object]]) -> None:
    (directory / "mini.json").write_text(json.dumps({
        "set": "mini", "rule": "test", "reps": 1, "shards": 1, "deadline_s": 600,
        "points": points}))


def test_a_load_point_loads_with_solid_cache_4_and_no_bodies_by_default(tmp_path: Path) -> None:
    _write(tmp_path, [_load_point()])
    (point,) = oper.load_set("mini", tmp_path).points
    assert (point.kind, point.artifact) == ("load", "load")
    assert point.body == {"workers": 1, "queue": 2, "clients": 2, "solid_cache": 4,
                          "bodies": False, "mix": [MIX_ENTRY]}


def _without(key: str) -> dict[str, object]:
    return {k: v for k, v in MIX_ENTRY.items() if k != key}


@pytest.mark.parametrize("point", [
    _load_point(workers=0), _load_point(workers=4), _load_point(workers=True),
    _load_point(queue=0), _load_point(workers=2, queue=1), _load_point(clients=0),
    _load_point(solid_cache=0), _load_point(solid_cache=5), _load_point(bodies="yes"),
    _load_point(mix=[]), _load_point(mix="parts"), *(_load_point(mix=[_without(key)]) for key in (
        "label", "kind", "params", "artifact")),
    _load_point(mix=[{**MIX_ENTRY, "artifact": "obj"}]),
    _load_point(mix=[{**MIX_ENTRY, "kind": "load"}]), _load_point(extra=1)],
    ids=["no-workers", "four-workers", "bool-workers", "queue-0", "queue-below-n", "clients-0",
         "cache-0", "cache-5", "text-bodies", "empty-mix", "mix-not-a-list", "entry-no-label",
         "entry-no-kind", "entry-no-params", "entry-no-artifact", "entry-bad-artifact",
         "entry-load-kind", "extra-key"])
def test_the_matrix_refuses_a_bad_load_point_with_exit_2(
        point: dict[str, object], tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    _write(tmp_path, [point])
    monkeypatch.setattr(oper, "POINTS_DIR", tmp_path)
    assert oper.main(["matrix", "--set", "mini"]) == 2
    captured = capsys.readouterr()
    assert "mini" in captured.err
    assert captured.out == ""


def test_the_parent_records_a_load_reading_without_repeating_the_mix(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[dict[str, object]] = []

    def fake(point: dict[str, object], image: str, cap: int, deadline_s: float, *,
             name: str) -> dict[str, object]:
        seen.append(point)
        return {"status": "ok", "memory_peak_bytes": PEAK}

    monkeypatch.setattr(oper_load, "run_load", fake)
    _write(tmp_path, [_load_point()])
    (point,) = oper.load_set("mini", tmp_path).points
    record = oper.run_reading(point, 1, "screw:ci", CAP, 600, {"cadquery": "2"})
    assert seen[0]["mix"] == [MIX_ENTRY]
    assert "mix" not in record
    assert (record["type"], record["kind"], record["status"], record["solid_cache"]) == (
        "reading", "load", "ok", 4)
    rows = oper.summarize([record], [1])
    assert rows[0]["max"] == {"memory_peak_bytes": PEAK}


def test_the_load_smoke_is_one_load_at_n1_with_bodies_and_one_gzip_levels_point() -> None:
    spec = oper.load_set("load-smoke")
    assert (spec.reps, spec.shards, spec.deadline_s) == (1, 1, 600)
    assert spec.rule == "smoke, not a figure: 07-08 path check"
    load, fine = spec.points
    assert load.kind == "load"
    assert load.body is not None
    assert {k: load.body[k] for k in ("workers", "queue", "clients", "solid_cache", "bodies")} == {
        "workers": 1, "queue": 2, "clients": 2, "solid_cache": 4, "bodies": True}
    mix = load.body["mix"]
    assert isinstance(mix, list)
    assert [(e["kind"], e["artifact"]) for e in mix] == [
        (kind, artifact) for kind in ("bolt", "nut") for artifact in ("stl-preview", "stl-fine",
                                                                      "step")]
    assert (fine.kind, fine.artifact, fine.gzip_levels) == ("bolt", "stl-fine", (1, 6, 9))
