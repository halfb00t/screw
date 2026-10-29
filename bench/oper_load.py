"""The load reading: concurrent cold requests against the server in the production image (07 D-03,
D-15; R15 to R18, R22, R24, R25).

A load reading is one fresh container of the image under the R2 cap (`--memory` and
`--memory-swap` at the cap), running one uvicorn process (`bench.oper_serve`, the server as
`screw serve` starts it, with the instrument deadline in place of the shipped timeouts) with
`SCREW_BUILD_WORKERS = N`, `SCREW_MAX_QUEUED_BUILDS = Q`, `SCREW_EXPORT_CACHE_MB = 1` and
`SCREW_SOLID_CACHE = K`. C clients then take the point's mix from one shared queue in its order:
the first C start together, and a client takes the next request as soon as its previous response
is complete, so C requests are in flight until the queue empties (R15). Every request asks for
`Accept-Encoding: identity`, so the reading measures builds and serving and not gzip (R19 owns the
level). Meanwhile a host thread GETs `/api/health` every 0.5 s (R24).

Standard library and `bench` only, like `bench.oper`, because the runner's bare setup-python
interpreter runs it; the container is driven through the `docker` CLI. Only an `ok` reading
carries figures (L02): one that ended any other way keeps each request's status and nothing it
measured.
"""

from __future__ import annotations

import http.client
import json
import queue
import statistics
import subprocess
import threading
import time
import urllib.parse
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path

from bench.oper import is_capped

type Docker = Callable[[Sequence[str], float], subprocess.CompletedProcess[str]]

_REPO_ROOT = Path(__file__).resolve().parents[1]

# statistics.quantiles(samples, n=20)'s own bucket count, as bench/latency.py: fewer samples
# than buckets make the 19th cut point a guess about data that was never collected (L02).
MIN_SAMPLES = 20

CONTAINER_PORT = 8000  # bench.oper_serve's, and the Dockerfile's SCREW_PORT
POOL_LOG = "/tmp/oper-pool.jsonl"  # in the container; uid 10001 can write /tmp
# Settle after the first healthy response, then read the idle peak (R16's B): the workers are
# warming the kernel at startup, and B is the server at rest, not its start.
IDLE_S = 2.0
HEALTH_EVERY_S = 0.5  # R24's poller cadence (the plan's)
HEALTHY_EVERY_S = 0.1  # how often the startup wait asks; sets the resolution of R25's figure
_EXEC_TIMEOUT_S = 30.0  # one `docker exec` or `docker inspect` after the deadline has passed
_TAIL = 2000

# `fmt` and the `quality` query value of each artifact. STEP ignores the quality, so its request
# names none and takes the route's default.
_ROUTES: dict[str, tuple[str, str | None]] = {
    "stl-preview": ("stl", "preview"), "stl-fine": ("stl", "fine"), "step": ("step", None)}

# The container's peak, read by the same reader a part reading uses (`bench.oper_child`, on the
# mounted `bench/`): v2 `memory.peak`, else v1, else no figure.
_PEAK_CODE = (
    "import json\n"
    "from bench.oper_child import CgroupUnavailable, oom_kills, read_peak\n"
    "try:\n"
    "    print(json.dumps({'peak': read_peak(), 'oom_kills': oom_kills()}))\n"
    "except CgroupUnavailable as exc:\n"
    "    print(json.dumps({'peak': None, 'oom_kills': oom_kills(), 'problem': str(exc)}))\n")
# The pool log, or nothing when no request reached the pool (a 422 before it, say).
_POOL_LOG_CODE = ("import pathlib, sys\n"
                  "p = pathlib.Path(sys.argv[1])\n"
                  "print(p.read_text() if p.exists() else '', end='')\n")


def p95(samples: Sequence[float]) -> float | None:
    """The 95th percentile, `statistics.quantiles(samples, n=20)[18]`, from at least 20 samples;
    `None` from fewer (the caller says how many there were)."""
    if len(samples) < MIN_SAMPLES:
        return None
    return statistics.quantiles(samples, n=20)[18]


def _spread(samples: Sequence[float]) -> dict[str, object]:
    return {"samples": len(samples), "p95_s": p95(samples)}


def _docker(args: Sequence[str], timeout: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["docker", *args], capture_output=True, text=True, check=False,
                          timeout=timeout)


def container_argv(name: str, image: str, cap: int, deadline_s: float, *, workers: int,
                   queue_depth: int, solid_cache: int,
                   repo_root: Path = _REPO_ROOT) -> list[str]:
    """`docker run -d` of the instrument server, a list and never a shell string. Each server
    setting is its own `-e NAME=VALUE` element built from a validated integer (T-07-61). The port
    is published on 127.0.0.1 only (T-07-21); no `--rm`, so OOMKilled is still readable after."""
    return ["run", "-d", "--name", name, f"--memory={cap}b", f"--memory-swap={cap}b",
            "-p", f"127.0.0.1::{CONTAINER_PORT}",
            "-e", f"SCREW_BUILD_WORKERS={workers}",
            "-e", f"SCREW_MAX_QUEUED_BUILDS={queue_depth}",
            "-e", "SCREW_EXPORT_CACHE_MB=1",
            "-e", f"SCREW_SOLID_CACHE={solid_cache}",
            "-e", "PYTHONPATH=/probe", "-v", f"{repo_root}/bench:/probe/bench:ro",
            "--entrypoint", "python", image, "-m", "bench.oper_serve",
            "--deadline", f"{deadline_s:g}", "--pool-log", POOL_LOG]


def model_path(entry: Mapping[str, object]) -> str:
    """The model URL of a mix entry: `/api/<kind>/model.<fmt>?<params>[&quality=...]`. A value
    is written as JSON writes it (`true`, `6.0`), which the query model reads back exactly."""
    fmt, quality = _ROUTES[str(entry["artifact"])]
    params = entry["params"]
    pairs = [(str(key), json.dumps(value)) for key, value in
             (params.items() if isinstance(params, Mapping) else ())]
    if quality is not None:
        pairs.append(("quality", quality))
    query = urllib.parse.urlencode(pairs)
    return f"/api/{entry['kind']}/model.{fmt}" + (f"?{query}" if query else "")


def _get(host: str, port: int, path: str,
         timeout: float) -> tuple[int, bytes, dict[str, str]]:
    """One GET asking for an uncompressed body: the status, the body and the headers."""
    connection = http.client.HTTPConnection(host, port, timeout=max(timeout, 0.001))
    try:
        connection.request("GET", path, headers={"Accept-Encoding": "identity"})
        response = connection.getresponse()
        body = response.read()
        return response.status, body, {k.lower(): v for k, v in response.getheaders()}
    finally:
        connection.close()


def _detail_type(body: bytes) -> str | None:
    """`detail[0].type` of an error body (`timeout`, `busy`, `build_error`...), if it has one."""
    try:
        detail = json.loads(body)["detail"][0]["type"]
    except (ValueError, KeyError, IndexError, TypeError):
        return None
    return detail if isinstance(detail, str) else None


def _request(host: str, port: int, index: int, entry: Mapping[str, object], t0: float,
             deadline_at: float) -> dict[str, object]:
    record: dict[str, object] = {"index": index, **{key: entry[key] for key in (
        "label", "kind", "params", "artifact")}}
    started = time.monotonic()
    try:
        status, body, headers = _get(host, port, model_path(entry), deadline_at - started)
    except (OSError, http.client.HTTPException) as exc:
        ended = time.monotonic()
        # A socket timeout is the reading's deadline, which every request's timeout is set to.
        error = "deadline" if ended >= deadline_at else f"{type(exc).__name__}: {exc}"
        return {**record, "start_s": started - t0, "end_s": ended - t0, "status_code": None,
                "error": error}
    ended = time.monotonic()
    record.update(start_s=started - t0, end_s=ended - t0, status_code=status, bytes=len(body),
                  content_encoding=headers.get("content-encoding", "identity"))
    if status != 200:
        record["type"] = _detail_type(body)
        if "retry-after" in headers:
            record["retry_after"] = headers["retry-after"]
    return record


def drive(host: str, port: int, mix: Sequence[Mapping[str, object]], clients: int, t0: float,
          deadline_at: float) -> tuple[list[dict[str, object] | None], bool]:
    """The mix through `clients` threads over one shared queue in mix order, and whether every
    request ended before `deadline_at`. Each client takes its first request before a barrier, so
    the first `clients` requests start together; then it takes the next one as soon as its
    previous response is complete. A request that never ended is `None`."""
    work: queue.Queue[tuple[int, Mapping[str, object]]] = queue.Queue()
    for index, entry in enumerate(mix):
        work.put((index, entry))
    results: list[dict[str, object] | None] = [None] * len(mix)
    start = threading.Barrier(clients)

    def take() -> tuple[int, Mapping[str, object]] | None:
        try:
            return work.get_nowait()
        except queue.Empty:
            return None

    def client() -> None:
        item = take()
        try:
            start.wait(timeout=max(deadline_at - time.monotonic(), 0.001))
        except threading.BrokenBarrierError:
            return
        while item is not None and time.monotonic() < deadline_at:
            index, entry = item
            results[index] = _request(host, port, index, entry, t0, deadline_at)
            item = take()

    threads = [threading.Thread(target=client, daemon=True) for _ in range(clients)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(max(deadline_at - time.monotonic(), 0.0))
    finished = not any(thread.is_alive() for thread in threads) and all(
        r is not None and r.get("error") != "deadline" for r in results)
    return results, finished


def _poll(stop: threading.Event, every_s: float, probe: Callable[[], dict[str, object]],
          out: list[dict[str, object]]) -> None:
    """`probe()` now and then every `every_s` on a fixed schedule until `stop` is set."""
    next_at = time.monotonic()
    while True:
        out.append(probe())
        next_at += every_s
        if stop.wait(max(next_at - time.monotonic(), 0.0)):
            return


def _health_probe(host: str, port: int, t0: float,
                  deadline_at: float) -> Callable[[], dict[str, object]]:
    def probe() -> dict[str, object]:
        started = time.monotonic()
        try:
            status, _, _ = _get(host, port, "/api/health", deadline_at - started)
        except (OSError, http.client.HTTPException) as exc:
            return {"offset_s": started - t0, "wall_s": time.monotonic() - started,
                    "status_code": None, "error": f"{type(exc).__name__}: {exc}"}
        return {"offset_s": started - t0, "wall_s": time.monotonic() - started,
                "status_code": status}
    return probe


def _host_port(text: str) -> tuple[str, int] | None:
    """The first `host:port` line `docker port` prints, or `None`."""
    for line in text.splitlines():
        host, sep, port = line.strip().rpartition(":")
        if sep and port.isdigit():
            return host.strip("[]"), int(port)
    return None


class _Ended(Exception):  # noqa: N818 -- an outcome, named for what it is
    """The reading ended before its figures; `status` is the R2 status it ended with."""

    def __init__(self, status: str, message: str) -> None:
        super().__init__(message)
        self.status = status


def _running(docker: Docker, name: str) -> bool:
    done = docker(["inspect", "--format", "{{.State.Running}}", name], _EXEC_TIMEOUT_S)
    return done.returncode == 0 and done.stdout.strip() == "true"


def _wait_healthy(docker: Docker, name: str, host: str, port: int, deadline_at: float) -> float:
    """Seconds from now to the first 200 of `/api/health`: R25's time to healthy."""
    started = time.monotonic()
    while time.monotonic() < deadline_at:
        try:
            status, _, _ = _get(host, port, "/api/health",
                                min(1.0, deadline_at - time.monotonic()))
            if status == 200:
                return time.monotonic() - started
        except (OSError, http.client.HTTPException):
            pass  # not listening yet: uvicorn binds after the lifespan has started the pool
        if not _running(docker, name):
            raise _Ended("crashed", "the server stopped before it answered /api/health")
        time.sleep(HEALTHY_EVERY_S)
    raise _Ended("killed", "the server did not answer /api/health inside the deadline")


def _exec(docker: Docker, name: str, what: str, *args: str) -> str:
    """The stdout of `docker exec name args`, or `_Ended("crashed")` naming `what`."""
    try:
        done = docker(["exec", name, *args], _EXEC_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        raise _Ended("crashed", f"reading {what} timed out") from None
    if done.returncode != 0:
        raise _Ended("crashed", f"reading {what} exited {done.returncode}: "
                                f"{done.stderr[-_TAIL:]}")
    return done.stdout


def _read_peak(docker: Docker, name: str) -> tuple[int, int | None]:
    """The container's cgroup peak and `oom_kill` count, read inside it. An unreadable cgroup is
    `no_cgroup`, never a substituted figure (R2)."""
    text = _exec(docker, name, "the peak", "python", "-c", _PEAK_CODE)
    try:
        found = json.loads(text)
    except ValueError:
        raise _Ended("crashed", f"the peak reader printed {text[:120]!r}") from None
    peak, kills = found.get("peak"), found.get("oom_kills")
    kills = kills if isinstance(kills, int) and not isinstance(kills, bool) else None
    if peak is None:
        raise _Ended("no_cgroup", str(found.get("problem")))
    if isinstance(peak, bool) or not isinstance(peak, int) or peak < 0:
        raise _Ended("crashed", f"the peak reader printed {text[:120]!r}")
    return peak, kills


def _pool_calls(docker: Docker, name: str) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []
    for line in _exec(docker, name, "the pool log", "python", "-c", _POOL_LOG_CODE,
                      POOL_LOG).splitlines():
        try:
            call = json.loads(line)
        except ValueError:
            call = None
        if not isinstance(call, dict):
            raise _Ended("crashed", f"the pool log holds {line[:120]!r}")
        calls.append(call)
    return calls


def _inspect(docker: Docker, name: str, field: str) -> str:
    try:
        done = docker(["inspect", "--format", f"{{{{.State.{field}}}}}", name], _EXEC_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return ""
    return done.stdout.strip() if done.returncode == 0 else ""


def _logs_tail(docker: Docker, name: str) -> str:
    try:
        done = docker(["logs", "--tail", "50", name], _EXEC_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return ""
    return (done.stdout + done.stderr)[-_TAIL:]


def request_status(requests: Iterable[dict[str, object] | None]) -> str:
    """The status the requests give a reading whose container ended cleanly: `refused` if any was
    a 422, `killed` if any was a timeout 503, `crashed` for any other non-200, an unfinished one
    or a compressed body, else `ok` (R2's statuses, L02)."""
    seen = list(requests)
    if any(r is not None and r.get("status_code") == 422 for r in seen):
        return "refused"
    if any(r is not None and r.get("status_code") == 503 and r.get("type") == "timeout"
           for r in seen):
        return "killed"
    if all(r is not None and r.get("status_code") == 200
           and r.get("content_encoding") == "identity" for r in seen):
        return "ok"
    return "crashed"


def _bare(index: int, entry: Mapping[str, object],
          done: dict[str, object] | None) -> dict[str, object]:
    """What a reading that is not `ok` keeps of a request: which it was and how it ended."""
    kept: dict[str, object] = {"index": index, **{key: entry[key] for key in (
        "label", "kind", "params", "artifact")}}
    if done is None:
        return {**kept, "status_code": None, "error": "not finished"}
    return {**kept, **{key: done[key] for key in ("status_code", "type", "error") if key in done}}


def _wall(request: Mapping[str, object]) -> float:
    return float(str(request["end_s"])) - float(str(request["start_s"]))


class _Reading:
    """What one load reading has measured so far; only an `ok` reading reports it."""

    def __init__(self, size: int) -> None:
        self.created = False
        self.healthy_s = 0.0
        self.idle_peak = 0
        self.load_s = 0.0
        self.results: list[dict[str, object] | None] = [None] * size
        self.health: list[dict[str, object]] = []
        self.peak: int | None = None
        self.kills: int | None = None
        self.calls: list[dict[str, object]] = []


def _measure(reading: _Reading, docker: Docker, name: str, argv: list[str],
             mix: Sequence[Mapping[str, object]], clients: int, deadline_at: float) -> None:
    """Start the server, wait for it, read the idle peak, then run the mix with the health
    poller beside it. Raises `_Ended` for a reading that cannot go on."""
    run = docker(argv, _EXEC_TIMEOUT_S)
    if run.returncode != 0:
        raise _Ended("crashed", f"docker run exited {run.returncode}: {run.stderr[-_TAIL:]}")
    reading.created = True
    port_text = docker(["port", name, f"{CONTAINER_PORT}/tcp"], _EXEC_TIMEOUT_S).stdout
    address = _host_port(port_text)
    if address is None:
        raise _Ended("crashed", f"docker port printed {port_text[:120]!r}, no address")
    host, port = address
    reading.healthy_s = _wait_healthy(docker, name, host, port, deadline_at)
    time.sleep(min(IDLE_S, max(deadline_at - time.monotonic(), 0.0)))
    reading.idle_peak, _ = _read_peak(docker, name)
    t0 = time.monotonic()
    stop = threading.Event()
    poller = threading.Thread(target=_poll, daemon=True, args=(
        stop, HEALTH_EVERY_S, _health_probe(host, port, t0, deadline_at), reading.health))
    poller.start()
    try:
        reading.results, finished = drive(host, port, mix, clients, t0, deadline_at)
        reading.load_s = time.monotonic() - t0
    finally:
        stop.set()
        poller.join(_EXEC_TIMEOUT_S)
    if not finished:
        raise _Ended("killed", "requests were still running at the deadline")


def run_load(point: Mapping[str, object], image: str, cap: int, deadline_s: float, *,
             name: str, docker: Docker = _docker) -> dict[str, object]:
    """One load reading of `point` (`workers`, `queue`, `clients`, `mix`, `solid_cache`), the
    whole of it inside `deadline_s` from `docker run` (R6 charges a load reading R2's 600 s).

    The status, in order: the container's first (`capped` for an OOM kill or an end peak at
    99 % of the cap, `killed` past the deadline, `crashed` when the server did not come up or a
    reading of it failed, `no_cgroup` with no readable peak), then the requests' (see
    `request_status`). Only `ok` carries the figures: every request with its start and end
    offsets and bytes, the time to the first healthy response, the idle peak before load (R16's
    B), the peak at the end, the health walls and the pool calls."""
    mix = point["mix"]
    if not isinstance(mix, list):
        raise TypeError("a load point's mix is a list")
    workers, queue_depth, clients, solid_cache = (
        int(str(point[key])) for key in ("workers", "queue", "clients", "solid_cache"))
    argv = container_argv(name, image, cap, deadline_s, workers=workers,
                          queue_depth=queue_depth, solid_cache=solid_cache)
    deadline_at = time.monotonic() + deadline_s
    reading = _Reading(len(mix))
    ended: _Ended | None = None
    oom = False
    tail = ""
    try:
        try:
            _measure(reading, docker, name, argv, mix, clients, deadline_at)
        except _Ended as exc:
            ended = exc
        if reading.created:
            # The peak is a high-water mark, so this one read covers the whole run (R15).
            try:
                reading.peak, reading.kills = _read_peak(docker, name)
                reading.calls = _pool_calls(docker, name)
            except _Ended as exc:
                ended = ended or exc
            oom = _inspect(docker, name, "OOMKilled") == "true"
            if ended is not None and ended.status == "crashed":
                tail = _logs_tail(docker, name)
    finally:
        if reading.created:
            docker(["rm", "-f", name], _EXEC_TIMEOUT_S)
    capped = oom or (reading.kills or 0) > 0 or (
        reading.peak is not None and is_capped(reading.peak, cap))
    status = ("capped" if capped else ended.status if ended is not None
              else request_status(reading.results))
    if status != "ok":
        line: dict[str, object] = {"status": status, "requests": [
            _bare(i, e, r) for i, (e, r) in enumerate(zip(mix, reading.results, strict=True))]}
        if ended is not None:
            line["problem"] = str(ended)
        if tail:
            line["stderr_tail"] = tail
        return line
    done = [r for r in reading.results if r is not None]
    walls: dict[str, list[float]] = {}
    for request in done:
        walls.setdefault(str(request["artifact"]), []).append(_wall(request))
    health_walls = [float(str(h["wall_s"])) for h in reading.health if h.get("status_code") == 200]
    return {"status": "ok", "time_to_healthy_s": reading.healthy_s,
            "idle_peak_bytes": reading.idle_peak, "memory_peak_bytes": reading.peak,
            "oom_kills": reading.kills, "load_s": reading.load_s, "requests": done,
            "latency": {"all": _spread([_wall(r) for r in done]),
                        **{artifact: _spread(w) for artifact, w in walls.items()}},
            "health": reading.health, "health_latency": _spread(health_walls),
            "pool_calls": reading.calls}
