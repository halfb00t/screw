"""The server a load reading measures: `screw serve` as an instrument (07 D-03; R15, R17, G8).

`bench.oper_load` starts one container of the production image per load reading and runs
`python -m bench.oper_serve --deadline <s> --pool-log <path>` in it. This starts `screw.app:app`
exactly as `screw serve` does (`configure()`, then `uvicorn.run(..., workers=1,
proxy_headers=True, log_config=None)`), with two differences, both made in this process only:

- `screw.app.BUILD_TIMEOUT_S` is replaced by the instrument deadline for every artifact before
  the app's lifespan builds its pool, so a slow build is measured and not cut at the shipped
  timeout. The shipped timeouts are what plan 07-16 sets from these readings; reading under
  them would measure the interim values instead of the builds.
- `BuildPool._run_with_timeout` is wrapped so every pool call appends one JSON line to the pool
  log: the slot, the artifact, the artifacts already pending on that slot at submit, the submit
  and end times and the outcome. R17 is checked offline on these records once R14 has derived
  the timeouts (G8): a request's queue wait plus its build must fit its artifact's timeout under
  the queue-aware deadline, and this log is the only place the queue behind a slot is visible.

Nothing in `src/` changes for it.
"""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from types import MappingProxyType

import uvicorn

import screw.app
from screw.calc.cost import ARTIFACTS, artifact_of
from screw.params import FastenerParams
from screw.pool import BuildPool
from screw.records import configure

# The one call the app makes through the pool: `build_export(p, fmt, quality)`.
type Export = Callable[[FastenerParams, str, str], bytes]
type RunWithTimeout = Callable[[BuildPool, FastenerParams, float, Export, FastenerParams, str, str],
                               Awaitable[bytes]]


def record_calls(run: RunWithTimeout, log_path: Path) -> RunWithTimeout:
    """`run` (the shape of `BuildPool._run_with_timeout`) with one log line per call.

    The pending list is this wrapper's own, per pool and slot, kept beside the pool's
    `_pending` (which holds timeouts, not artifacts): the line says which artifacts the call
    queued behind. The event loop is single-threaded and nothing awaits between the read and
    the append, so no lock is needed, as in the pool itself. The line is written when the call
    ends, whatever the outcome, so a timed-out or broken build is in the log too.
    """
    pending: dict[tuple[int, int], list[str]] = {}

    async def recorded(self: BuildPool, p: FastenerParams, timeout: float, func: Export,
                       part: FastenerParams, fmt: str, quality: str) -> bytes:
        slot = hash(p) % self.workers
        artifact = artifact_of(fmt, quality)
        queue = pending.setdefault((id(self), slot), [])
        line: dict[str, object] = {"slot": slot, "artifact": artifact, "pending": list(queue),
                                   "submit_s": time.monotonic()}
        queue.append(artifact)
        outcome = "ok"
        try:
            return await run(self, p, timeout, func, part, fmt, quality)
        except BaseException as exc:
            outcome = type(exc).__name__
            raise
        finally:
            queue.remove(artifact)
            line.update(end_s=time.monotonic(), outcome=outcome)
            with log_path.open("a") as log:
                log.write(json.dumps(line, allow_nan=False) + "\n")

    return recorded


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m bench.oper_serve", description=__doc__)
    parser.add_argument("--deadline", type=float, required=True,
                        help="seconds every artifact's build may take (the reading's deadline)")
    parser.add_argument("--pool-log", type=Path, required=True,
                        help="the JSONL file one line per pool call is appended to")
    args = parser.parse_args(argv)
    configure()
    # The module's globals, as bench.oper_child lowers a guard: the name is Final to mypy, and
    # the lifespan reads it at startup, after this line.
    vars(screw.app)["BUILD_TIMEOUT_S"] = MappingProxyType(dict.fromkeys(ARTIFACTS, args.deadline))
    # setattr: mypy refuses assignment to a method, and the class is the one the app builds.
    setattr(BuildPool, "_run_with_timeout",  # noqa: B010
            record_calls(BuildPool._run_with_timeout, args.pool_log))
    # 0.0.0.0 inside the container; the load driver publishes the port on 127.0.0.1 only.
    uvicorn.run("screw.app:app", host="0.0.0.0", port=8000, workers=1, proxy_headers=True,
                log_config=None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
