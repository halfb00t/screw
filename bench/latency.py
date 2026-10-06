"""Does `/api/health` stay fast while a build is in flight?

Two load scenarios against a running **host** service (`make serve`): `single`, one fine
build of the heaviest corpus part, and `concurrent`, ten fine builds of ten distinct corpus
parts at once. Each samples `/api/health` idle for a settle window, then for as long as a
build is in flight, and reports both p95s.

The host, not the container, because container overhead would make a later run incomparable
to one taken on the host. spur measured `/api/health` this way; screw has no recorded
baseline of its own, so this reports the ratio and sets no bar (L07). Not part of
`make verify`: it needs a running service and a stopwatch, and a latency assertion on shared
hardware would flap until someone stopped believing it. Run it with `make bench.latency`
after `make serve` is up -- on a fresh server: a part the server has already built is a
cache hit (`SCREW_EXPORT_CACHE_MB`) and puts no load on anything.

This module never imports `screw.solid`, and so never the CAD kernel: it is a measuring
client, and the server validates every request on its own.
"""

from __future__ import annotations

import argparse
import os
import statistics
import sys
import time
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass

import httpx2 as httpx

from bench import machine_facts
from bench.corpus import corpus, label

DEFAULT_BASE_URL = "http://127.0.0.1:8000"

# statistics.quantiles(samples, n=20)'s own bucket count. Fewer samples than buckets makes the
# 95th-percentile cut point a guess about data that was never collected, not a measurement --
# refuse instead of printing one (L02).
MIN_SAMPLES = 20

SETTLE_SECONDS = 2.0  # idle sampling window before load starts

# The heaviest corpus part is the last (`bench/corpus.py`). The concurrent scenario takes the
# first ten, so it never builds the single scenario's part: the default run is concurrent then
# single, and a part built first would make the second scenario a cache hit.
CONCURRENT_PARTS = 10


def _p95(samples: list[float]) -> float:
    """The one named stdlib method used for every p95 in this harness.

    `statistics.quantiles(samples, n=20)[-1]` is the last of 20 cut points: the 95th
    percentile. Hand-rolling one (`sorted(samples)[int(0.95 * len)]`) is exactly the
    plausible but off-by-one number L02 forbids.
    """
    return statistics.quantiles(samples, n=20)[-1]


def _sample_for(base_url: str, client: httpx.Client, duration: float) -> list[float]:
    """Sample `/api/health` as fast as the server answers, for `duration` seconds."""
    samples: list[float] = []
    deadline = time.monotonic() + duration
    while time.monotonic() < deadline:
        t0 = time.perf_counter()
        client.get(f"{base_url}/api/health", timeout=30.0)
        samples.append(time.perf_counter() - t0)
    return samples


@dataclass(frozen=True)
class RequestOutcome:
    params: str  # the `key=value` label, from the part's own query dictionary
    status: str  # "200", or "503 " + the server's own `detail[0]["type"]`
    wall_s: float


def fetch(base_url: str, client: httpx.Client, part: dict[str, object]) -> RequestOutcome:
    """One `/api/bolt/model.stl` request at `quality=fine`.

    `"200"` on success; `"503 " + detail[0]["type"]` (`busy`, `timeout` or `pool_broken` -- the
    three `type` values `src/screw/app.py` gives a 503) on refusal, read from the documented
    body. A refusal is not a harness failure: the queue holds `2 x SCREW_BUILD_WORKERS` builds
    (L09), and the concurrent scenario deliberately fires ten. Any other status raises, and a
    503 without that documented field raises naming the body, never a guessed reason (L02).
    """
    query = {k: str(v) for k, v in part.items()} | {"quality": "fine"}
    t0 = time.perf_counter()
    response = client.get(f"{base_url}/api/bolt/model.stl", params=query, timeout=120.0)
    if response.status_code == 503:
        try:
            reason = response.json()["detail"][0]["type"]
        except (ValueError, KeyError, IndexError) as exc:
            raise ValueError(
                f"503 response body missing detail[0].type: {response.text!r}") from exc
        status = f"503 {reason}"
    else:
        response.raise_for_status()
        status = "200"
    return RequestOutcome(label(part), status, time.perf_counter() - t0)


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    idle: list[float]
    under_load: list[float]
    outcomes: tuple[RequestOutcome, ...]

    @property
    def slowest_build(self) -> float:
        return max((o.wall_s for o in self.outcomes if o.status == "200"), default=0.0)


def _sample_while_building(base_url: str, client: httpx.Client,
                           futures: list[Future[RequestOutcome]]) -> list[float]:
    """Keep sampling `/api/health` for as long as at least one build is in flight.

    A do-while shape (sample first, check after) guarantees at least one sample even for a
    build that finishes before the first check would otherwise run.
    """
    samples: list[float] = []
    while True:
        t0 = time.perf_counter()
        client.get(f"{base_url}/api/health", timeout=30.0)
        samples.append(time.perf_counter() - t0)
        if all(future.done() for future in futures):
            return samples


def _scenario(name: str, base_url: str, parts: list[dict[str, object]]) -> ScenarioResult:
    with httpx.Client() as client:
        idle = _sample_for(base_url, client, SETTLE_SECONDS)
        with ThreadPoolExecutor(max_workers=len(parts)) as pool:
            futures = [pool.submit(fetch, base_url, client, part) for part in parts]
            under_load = _sample_while_building(base_url, client, futures)
        outcomes = tuple(future.result() for future in futures)
    return ScenarioResult(name, idle, under_load, outcomes)


def scenario_single(base_url: str) -> ScenarioResult:
    """Idle p95, then one fine build of the heaviest corpus part in flight."""
    return _scenario("single", base_url, [corpus()[-1]])


def scenario_concurrent(base_url: str) -> ScenarioResult:
    """Idle p95, then ten fine builds of ten distinct corpus parts at once. Admission control
    refuses whatever the queue cannot hold; see `fetch`."""
    return _scenario("concurrent", base_url, corpus()[:CONCURRENT_PARTS])


SCENARIOS: dict[str, Callable[[str], ScenarioResult]] = {
    "single": scenario_single,
    "concurrent": scenario_concurrent,
}

# The order a no-argument run has: pinned here, so adding a scenario to `SCENARIOS` cannot
# silently put it into `make bench.latency`.
DEFAULT_SCENARIOS: tuple[str, ...] = ("concurrent", "single")


def _p95_or_warn(samples: list[float], what: str) -> tuple[float, int] | None:
    """The one place a p95 is computed, or refused (L02): over fewer samples than
    `statistics.quantiles`' own bucket count it is a plausible number, not a measured one."""
    if len(samples) < MIN_SAMPLES:
        print(f"warning: {what} has only {len(samples)} /api/health samples "
              f"(need >= {MIN_SAMPLES}); refusing to report a p95", file=sys.stderr)
        return None
    return _p95(samples), len(samples)


def report_markdown(result: ScenarioResult, idle: tuple[float, int],
                    under_load: tuple[float, int], load: tuple[float, float, float]) -> str:
    """The scenario's report: machine, the load read before the scenario started, both p95s,
    their ratio (no bar -- L07), the slowest build, and what the server answered each build
    request with."""
    idle_p95, idle_n = idle
    load1, load5, load15 = load
    load_p95, load_n = under_load
    ratio = load_p95 / idle_p95 if idle_p95 > 0 else float("inf")
    counts: dict[str, int] = {}
    for outcome in result.outcomes:
        counts[outcome.status] = counts.get(outcome.status, 0) + 1
    answered = ", ".join(f"{status}: {count}" for status, count in counts.items())
    return (
        f"## Latency: {result.name}\n\n"
        f"- Machine: {machine_facts()}\n"
        f"- Load averages at start: {load1:.2f}, {load5:.2f}, {load15:.2f}\n"
        f"- Idle p95: {idle_p95 * 1000:.1f} ms (n={idle_n})\n"
        f"- Under-load p95: {load_p95 * 1000:.1f} ms (n={load_n})\n"
        f"- Ratio (under-load / idle): {ratio:.2f}x -- no bar is set for screw yet\n"
        f"- Slowest successful build: {result.slowest_build:.2f} s\n"
        f"- Build requests: {len(result.outcomes)} attempted -- {answered} "
        f"(`503 busy` is admission control, expected once concurrency exceeds the queue)\n"
    )


def _run_scenario(name: str, base_url: str) -> bool:
    # Read before the scenario starts, never after: an end-of-run reading under an "at start"
    # label is the mistake bench.build_time's report was fixed for in spur.
    load = os.getloadavg()
    result = SCENARIOS[name](base_url)
    idle = _p95_or_warn(result.idle, f"{name}/idle")
    under_load = _p95_or_warn(result.under_load, f"{name}/under-load")
    if idle is None or under_load is None:
        return False
    print(report_markdown(result, idle, under_load, load))
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bench.latency",
        description="Does /api/health stay fast while a build runs? Against a running host "
                    "service (`make serve`).",
    )
    parser.add_argument(
        "scenario", nargs="?", choices=sorted(SCENARIOS), default=None,
        help="Which load scenario to run. Omit to run concurrent then single.")
    parser.add_argument(
        "--base-url", default=DEFAULT_BASE_URL,
        help=f"The running host service. Default: {DEFAULT_BASE_URL}.")
    args = parser.parse_args(argv)

    names = [args.scenario] if args.scenario else list(DEFAULT_SCENARIOS)
    # Run every scenario before deciding the exit code -- a generator inside all() would
    # short-circuit on the first failure and silently skip the rest.
    results = [_run_scenario(name, args.base_url) for name in names]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
