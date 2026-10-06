"""The parent's handle on the kernel child (kernel-free).

One request line in, one record line out, under a hard deadline. OpenCascade has no cooperative
cancel and an OCP segfault was provoked in research (exit 139), so a timeout kills the child and
the next request respawns it, and a dead child is one recorded `worker_died` row: never a lost
campaign, never a made-up number (L02, T-02-04).
"""

from __future__ import annotations

import contextlib
import json
import queue
import subprocess
import sys
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path
from typing import IO

from bench.thread_spike.verdict import (
    RowRecord,
    RowRequest,
    failed_record,
    parse_record,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STDERR_TAIL = 2000

# The production image (D-05): the container pass runs the locked construction in it, because
# production runs in it.
CONTAINER_IMAGE = "screw:latest"


def container_argv(name: str, repo_root: Path) -> list[str]:
    """The argv that runs this package's worker inside `CONTAINER_IMAGE` as linux/amd64.

    A list, never a shell string (T-02-12). The image runs as uid 10001 and has no `bench/`, so
    the repository's `bench/` is mounted read-only and put on PYTHONPATH (RESEARCH Code Example
    7). `--rm` removes the container when it exits and `--name` is what `docker_kill` needs to
    stop one a timeout abandoned.
    """
    return ["docker", "run", "-i", "--rm", "--platform", "linux/amd64", "--name", name,
            "--entrypoint", "python", "-v", f"{repo_root}/bench:/probe/bench:ro",
            "-e", "PYTHONPATH=/probe", CONTAINER_IMAGE, "-m", "bench.thread_spike.worker"]


def docker_kill(argv: list[str]) -> None:
    """Stop the container `argv` (a `container_argv`) started. Killing the `docker run` client
    does not stop its container, so a timed-out row would otherwise keep building in the
    background; a container that is already gone is not an error."""
    if "--name" in argv:
        name = argv[argv.index("--name") + 1]
        subprocess.run(["docker", "kill", name], capture_output=True, check=False)


class Worker:
    """A persistent kernel child. `argv` and `env` are injectable for the container pass and
    the reference rows; the default is this package's own worker. `argv` may be a callable,
    asked at every spawn, so a respawn can take a new container name; `on_timeout` gets the argv
    of the child a timeout just dropped, so the container worker can `docker_kill` it."""

    def __init__(self, argv: list[str] | Callable[[], list[str]] | None = None,
                 env: dict[str, str] | None = None,
                 on_timeout: Callable[[list[str]], None] | None = None) -> None:
        self._argv = argv if argv is not None else [
            sys.executable, "-m", "bench.thread_spike.worker"]
        self._env = env
        self._on_timeout = on_timeout
        self._spawned: list[str] = []
        self._proc: subprocess.Popen[str] | None = None
        self._stderr: IO[str] | None = None

    def _spawn(self) -> subprocess.Popen[str]:
        # stderr goes to a file, not a pipe: nothing reads a pipe while a row is building, so a
        # chatty child would fill it and deadlock the campaign.
        self._stderr = tempfile.TemporaryFile(  # noqa: SIM115 -- closed in _drop, per child
            mode="w+", encoding="utf-8")
        self._spawned = self._argv() if callable(self._argv) else list(self._argv)
        self._proc = subprocess.Popen(
            self._spawned, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self._stderr,
            text=True, cwd=_REPO_ROOT, env=self._env)
        return self._proc

    def _stderr_tail(self) -> str:
        if self._stderr is None:
            return ""
        self._stderr.flush()
        self._stderr.seek(0)
        return self._stderr.read()[-_STDERR_TAIL:].strip()

    def _drop(self) -> None:
        """Forget the child (killed first if still running); the next request respawns."""
        if self._proc is not None:
            if self._proc.poll() is None:
                self._proc.kill()
            self._proc.wait()
            for stream in (self._proc.stdin, self._proc.stdout):
                if stream is not None:
                    with contextlib.suppress(OSError):  # a broken pipe on the unflushed write
                        stream.close()
        if self._stderr is not None:
            self._stderr.close()
        self._proc = None
        self._stderr = None

    def _died(self, request: RowRequest) -> RowRecord:
        proc = self._proc
        assert proc is not None
        try:
            code = proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            code = proc.wait()
        tail = self._stderr_tail()
        self._drop()
        # A negative return code is the signal that killed it (-11: segmentation fault).
        error = f"worker exited with return code {code}"
        return failed_record(request, "worker_died", f"{error}: {tail}" if tail else error)

    def run(self, request: RowRequest, timeout_s: float) -> RowRecord:
        """One row. Timed out: the child is killed and the request echoed with outcome
        "timeout". Child gone: outcome "worker_died" with its return code and stderr tail."""
        proc = self._proc
        if proc is None or proc.poll() is not None:
            self._drop()
            proc = self._spawn()
        stdin, stdout = proc.stdin, proc.stdout
        assert stdin is not None
        assert stdout is not None
        try:
            stdin.write(json.dumps(request) + "\n")
            stdin.flush()
        except BrokenPipeError:
            return self._died(request)
        lines: queue.Queue[str] = queue.Queue()
        threading.Thread(target=lambda: lines.put(stdout.readline()), daemon=True).start()
        try:
            line = lines.get(timeout=timeout_s)
        except queue.Empty:
            spawned = self._spawned
            self._drop()
            if self._on_timeout is not None:
                self._on_timeout(spawned)
            return failed_record(request, "timeout", f"no record within {timeout_s:g} s")
        if not line.endswith("\n"):  # EOF, or a line cut short by the child dying
            return self._died(request)
        try:
            return parse_record(line)
        except ValueError as exc:
            # The child spoke, but not our protocol: its state is unknown, so do not reuse it.
            self._drop()
            return failed_record(request, "failure", f"unreadable worker output: {exc}")

    def close(self) -> None:
        """End the child: EOF on stdin lets it exit, and a child that will not is killed."""
        proc = self._proc
        if proc is not None and proc.stdin is not None and proc.poll() is None:
            proc.stdin.close()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                if self._on_timeout is not None:
                    self._on_timeout(self._spawned)
        self._drop()


def run_once(request: RowRequest, timeout_s: float, argv: list[str] | None = None,
             env: dict[str, str] | None = None) -> RowRecord:
    """One row in a fresh `--once` child, killed at `timeout_s`: the only way a row gets a peak
    RSS, because the child's `ru_maxrss` is then that row's alone (RESEARCH Pitfall 5). Children
    run one at a time, so a slow row costs time and never memory (T-02-13)."""
    worker = Worker(argv=argv if argv is not None else [
        sys.executable, "-m", "bench.thread_spike.worker", "--once"], env=env)
    try:
        return worker.run(request, timeout_s)
    finally:
        worker.close()
