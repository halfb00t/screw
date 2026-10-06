"""The one real end-to-end worker test, plus the routing-affinity and pool-failure tests.

Every other API test (tests/test_api.py) runs the export inline, in the test process,
via that file's autouse fixture. This file is deliberately different: it is the one
place in the suite that proves a build actually crosses the process boundary, so it
earns its own TestClient idiom -- see the comment on
test_a_real_worker_builds_and_downloads below for why, and don't "fix" it back.
"""

from __future__ import annotations

import asyncio
import logging
import multiprocessing as mp
import os
import signal
import threading
import time
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from typing import cast

import pytest
from fastapi.testclient import TestClient

from screw.app import BoltModelQuery, app, build_backend, strip
from screw.build_errors import BuildError, BuildTimeout
from screw.params import BoltParams


def _sleep_past_timeout(seconds: float) -> bytes:
    """Module-level, not a lambda -- `spawn` can only pickle a function it can import
    by qualified name (confirmed empirically in spur with a throwaway pytest run).
    Returns bytes only to match `BuildPool._run_with_timeout`'s `Callable[..., bytes]`
    contract -- the value is never used, only the fact that the call takes `seconds` to
    return.
    """
    time.sleep(seconds)
    return b""


def _die() -> bytes:
    """Module-level: ends its own worker process immediately, with no Python exception
    and no interpreter teardown -- `os._exit` bypasses both, which is what makes
    `concurrent.futures` detect this as a broken pool rather than a normal task
    failure [verified in spur: a throwaway pytest run confirmed `os._exit(1)`
    inside a worker surfaces as `BrokenProcessPool` from `future.result()`, whereas a
    raised Python exception would surface as that exception instead].
    """
    os._exit(1)


def _event_records(caplog: pytest.LogCaptureFixture, event: str) -> list[logging.LogRecord]:
    """Same helper as tests/test_api.py's own `_event_records` -- the records
    this module's helpers emitted for one literal event name. `getattr(..., None)`
    because `caplog.records` also holds records from other loggers that carry no
    `event` attribute at all.
    """
    return [rec for rec in caplog.records if getattr(rec, "event", None) == event]


def _field(rec: logging.LogRecord, name: str) -> object:
    """Same helper as tests/test_api.py's own `_field` -- `name` is a parameter, not a
    literal, at this call site, so ruff's B009 ("no getattr with a constant") does not
    fire here the way it would on a direct `getattr(rec, "slot")`.
    """
    return getattr(rec, name)


def test_a_real_worker_builds_and_downloads() -> None:
    # `with TestClient(app) as client:` is required here, unlike tests/test_api.py's
    # module-level `client = TestClient(app)` -- only the `with` form sends the ASGI
    # lifespan.startup message that actually creates app.state.pool (verified in
    # spur: a bare TestClient(app) never starts lifespan).
    with TestClient(app) as client:
        r = client.get("/api/bolt/model.stl", params={"quality": "preview"})
        assert r.status_code == 200
        assert len(r.content) > 1000

        # Tripwire: prove the build actually crossed the process
        # boundary, not merely that the inline path would also have returned 200.
        params = BoltParams()
        executor = app.state.pool.executor_for(params)
        worker_pid = executor.submit(os.getpid).result()
        assert worker_pid != os.getpid()


def test_the_same_part_always_reaches_the_same_worker() -> None:
    """Routing-stability property the byte caches depend on: same params, same executor, always."""
    with TestClient(app):
        pool = app.state.pool
        a = BoltParams()
        b = BoltParams()
        assert a is not b
        assert a == b
        assert pool.executor_for(a) is pool.executor_for(a)
        assert pool.executor_for(b) is pool.executor_for(b)
        assert pool.executor_for(a) is pool.executor_for(b)


def test_preview_fine_and_step_share_one_worker() -> None:
    """Preview STL, fine STL and STEP reduce to one BoltParams, so one executor."""
    with TestClient(app):
        pool = app.state.pool
        preview = strip(BoltModelQuery(quality="preview"), BoltParams)
        fine = strip(BoltModelQuery(quality="fine"), BoltParams)
        step = strip(BoltModelQuery(), BoltParams)  # STEP has no quality dimension
        assert pool.executor_for(preview) is pool.executor_for(fine)
        assert pool.executor_for(fine) is pool.executor_for(step)


def test_executor_processes_attribute_still_exists() -> None:
    """Regression guard for the forced-termination path.

    `ProcessPoolExecutor` has no public API to kill a running task -- the
    timeout->terminate->recreate path reaches the OS process through the private,
    undocumented `_processes` dict (pid -> SpawnProcess). Confirmed present on
    CPython 3.12.13 (spur's research); checked on CPython
    3.12.13, the only supported interpreter (L01). If a future interpreter removes
    or renames this attribute, this test fails `make verify` loudly instead of
    the termination path silently becoming a no-op.
    """
    executor = ProcessPoolExecutor(max_workers=1, mp_context=mp.get_context("spawn"))
    try:
        executor.submit(os.getpid).result()  # a trivial task, so a worker actually starts
        assert hasattr(executor, "_processes")
        assert executor._processes  # non-empty: at least the one worker just used
        # Same guard for the second private the wedged-build test reaches through: the
        # executor's manager thread, captured there so that it -- not the test -- is the
        # one reaper of the terminated worker (typeshed types it as `_ThreadWakeup`; at
        # runtime it is the `_ExecutorManagerThread`, a `threading.Thread`).
        assert isinstance(executor._executor_manager_thread, threading.Thread)
    finally:
        # Explicit shutdown: filterwarnings = ["error"] in pyproject.toml turns a
        # leaked subprocess's ResourceWarning into a test failure.
        executor.shutdown(wait=True)


def test_a_wedged_build_is_terminated_and_its_worker_replaced(
        caplog: pytest.LogCaptureFixture) -> None:
    """A build that overruns its per-build timeout is killed, not merely
    abandoned -- the wait ends and the work ends with it -- and the wedged hash slot's
    worker is replaced rather than left dead, so the next request for that slot
    succeeds against a fresh worker."""
    caplog.set_level(logging.INFO)  # caplog defaults to WARNING, and
    # worker.replaced is ERROR, but this pins the assertion to the level under test
    # rather than to caplog's own default happening to be low enough.
    with TestClient(app):
        pool = app.state.pool
        params = BoltParams()
        expected_slot = hash(params) % pool.workers  # pool.executor_for's own arithmetic
        executor = pool.executor_for(params)
        worker_pid_before = executor.submit(os.getpid).result()  # starts the worker
        [proc] = list(executor._processes.values())
        # The executor's own manager thread will be the one reaper of `proc` (see the
        # join below). Captured now: `recreate_for`'s `shutdown(wait=False)` drops the
        # executor's reference to it (`_executor_manager_thread = None`, process.py,
        # 3.12.13) before this test gets control back.
        manager = executor._executor_manager_thread
        assert isinstance(manager, threading.Thread)
        replaced_before = pool.replaced

        original_timeout = pool.timeout
        pool.timeout = 0.2  # short, injected timeout -- a test that waited out the
        # real production default would not be exercising this path (it would just be
        # slow), and 0.2s is well past _sleep_past_timeout's own scheduling overhead.
        try:
            with pytest.raises(BuildTimeout):
                asyncio.run(pool._run_with_timeout(params, _sleep_past_timeout, 5.0))
        finally:
            pool.timeout = original_timeout

        # Wait for the manager thread, never for `proc` directly. Once the worker dies,
        # the manager thread and this one wake on the same process sentinel and race to
        # `os.waitpid` for the same child; the loser gets ECHILD, which
        # `multiprocessing.popen_fork.Popen.poll` swallows into "still alive"
        # (ASSUMPTION, not directly observed -- see the resolved debt record for what
        # was and wasn't checked). The old `proc.join(timeout=5); assert not
        # proc.is_alive()` is consistent with failing that way on the GitHub runner on
        # 4 of 5 attempts (runs 36116930241, 36117030280, 36118554588, 2026-09-25) with
        # the worker in fact dead, and never once on a workstation (0/18 locally,
        # contended and idle). With the manager thread as the only
        # reaper, `exitcode` is the status its join recorded, and asserting the signal
        # number proves the death was ours, not a crash. The liveness assertion between
        # the two is load-bearing: a timed `join` can return with the thread still
        # running, and reading `exitcode` before it has stored the status is the same
        # `waitpid` race again -- reproduced by pausing the manager just before its
        # assignment (Codex re-review of ae052f8: `exitcode=None`, errno ECHILD).
        manager.join(timeout=5)
        assert not manager.is_alive(), "executor manager thread did not finish shutdown"
        assert proc.exitcode == -signal.SIGTERM
        assert pool.replaced == replaced_before + 1

        replaced = _event_records(caplog, "worker.replaced")
        assert len(replaced) == 1
        assert replaced[0].levelno == logging.ERROR
        assert _field(replaced[0], "cause") == "timeout"
        assert _field(replaced[0], "slot") == expected_slot

        # the next request routed to the same hash slot succeeds against the fresh worker
        new_pid = pool.executor_for(params).submit(os.getpid).result()
        assert new_pid != worker_pid_before


def test_a_dying_worker_surfaces_as_broken_pool_and_is_replaced(
        caplog: pytest.LogCaptureFixture) -> None:
    """A worker that dies unexpectedly (a hard process death, not a Python
    exception) surfaces as BrokenProcessPool from the awaited call, and its slot is
    replaced rather than left dead."""
    caplog.set_level(logging.INFO)  # caplog defaults to WARNING
    with TestClient(app):
        pool = app.state.pool
        params = BoltParams()
        expected_slot = hash(params) % pool.workers
        replaced_before = pool.replaced

        with pytest.raises(BrokenProcessPool):
            asyncio.run(pool._run_with_timeout(params, _die))

        assert pool.replaced == replaced_before + 1

        replaced = _event_records(caplog, "worker.replaced")
        assert len(replaced) == 1
        assert replaced[0].levelno == logging.ERROR
        assert _field(replaced[0], "cause") == "broken_pool"
        assert _field(replaced[0], "slot") == expected_slot

        # the slot is usable again, against a fresh worker
        assert pool.executor_for(params).submit(os.getpid).result() > 0


@pytest.mark.parametrize(("exc", "want_status", "want_type"), [
    (BuildError("flank too small for this bore"), 422, "build_error"),
    (BuildTimeout("Build exceeded the 30s per-build timeout."), 503, "timeout"),
    (BrokenProcessPool("worker died"), 503, "pool_broken"),
])
def test_each_build_failure_mode_maps_to_its_own_status_and_type(
        exc: Exception, want_status: int, want_type: str) -> None:
    """BuildError -> 422, BuildTimeout -> 503, BrokenProcessPool ->
    503 -- three distinct exception mappings, reusing _build_slot's `503` +
    `Retry-After` + `detail[].type` shape for the two new ones rather than inventing a
    new response contract. Drives each failure via the injectable build_backend,
    exactly as it's meant to be used: no real worker or build needed for a contract
    test about status codes and body shapes.
    """
    from screw import app as app_module

    async def backend(p: BoltParams, fmt: str, quality: str) -> bytes:
        raise exc

    # A plain (non-`with`) TestClient never runs the lifespan -- fine here,
    # since overriding build_backend means the real pool is never consulted.
    client = TestClient(app)
    app.dependency_overrides[build_backend] = lambda: backend
    try:
        capacity_before = app_module.BUILD_QUEUE._value
        # d=6.5: a diameter no other test in this suite ever successfully downloads,
        # so the parent's byte cache (_EXPORTS) can never short-circuit this
        # request before the raising backend gets a chance to run (the same reasoning
        # tests/test_api.py's cache test, when it lands, uses for picking a non-default d).
        r = client.get("/api/bolt/model.stl", params={"quality": "preview", "d": 6.5})
        assert r.status_code == want_status
        detail = r.json()["detail"][0]
        assert detail["type"] == want_type
        if want_status == 503:
            assert r.headers["retry-after"] == "5"
        # the admission slot is released on every failure path: a repeated
        # failure must never leak capacity and turn into a service that refuses
        # everything -- the failure mode hardest to diagnose from the outside.
        assert app_module.BUILD_QUEUE._value == capacity_before
    finally:
        app.dependency_overrides.pop(build_backend, None)


def test_the_four_failure_types_are_pairwise_distinct() -> None:
    """`busy` (existing, from a saturated queue), `build_error`, `timeout` and
    `pool_broken` must all differ, so a client can tell "your part is
    impossible" from "come back in a moment" from "something died" from "the queue is
    full" -- checked against the values the app actually returns, not restated
    constants that would trivially agree with themselves.
    """
    from screw import app as app_module

    client = TestClient(app)
    types: set[str] = set()

    # d=6.6: a diameter no other test in this suite ever successfully downloads (see
    # the comment in test_each_build_failure_mode_maps_to_its_own_status_and_type),
    # so _EXPORTS can never short-circuit any of the four requests below.
    query: dict[str, str | int | float | bool | None] = {"quality": "preview", "d": 6.6}

    async def _never_called(p: BoltParams, fmt: str, quality: str) -> bytes:
        # build_backend is a FastAPI dependency, resolved before the endpoint body
        # runs, on every request regardless of which branch inside it ends up
        # executing -- so even the "busy" sub-case below needs an override in place
        # (a plain TestClient(app), unlike `with TestClient(app):`, never starts the
        # lifespan that would otherwise supply a real one). This tripwire is that
        # override: it must never actually run, because _build_slot's admission check
        # is supposed to refuse the request before backend(...) is ever awaited.
        raise AssertionError("_build_slot should have refused before calling backend")

    app.dependency_overrides[build_backend] = lambda: _never_called
    try:
        held = [app_module.BUILD_QUEUE.acquire(blocking=False)
                for _ in range(app_module.MAX_QUEUED_BUILDS)]
        try:
            r = client.get("/api/bolt/model.stl", params=query)
            assert r.status_code == 503
            types.add(r.json()["detail"][0]["type"])
        finally:
            for _ in held:
                app_module.BUILD_QUEUE.release()

        for exc in (BuildError("flank too small"),
                    BuildTimeout("Build exceeded the 30s per-build timeout."),
                    BrokenProcessPool("worker died")):
            async def backend(p: BoltParams, fmt: str, quality: str,
                               _exc: Exception = exc) -> bytes:
                raise _exc

            app.dependency_overrides[build_backend] = lambda b=backend: b
            r = client.get("/api/bolt/model.stl", params=query)
            types.add(r.json()["detail"][0]["type"])
    finally:
        app.dependency_overrides.pop(build_backend, None)

    assert len(types) == 4


def test_health_reports_pool_state() -> None:
    """/api/health additionally reports pool state -- worker count, remaining
    admission capacity and workers replaced since start -- nested under one `pool` key
    without disturbing the existing top-level
    `status`/`version` shape the UI and the container healthcheck already read.
    """
    from screw import app as app_module

    with TestClient(app) as client:
        pool = app.state.pool
        body = client.get("/api/health").json()
        assert body["status"] == "ok"
        assert "version" in body
        assert body["pool"] == {
            "workers": pool.workers,
            "queue_available": app_module.MAX_QUEUED_BUILDS,
            "workers_replaced": pool.replaced,
        }


def test_health_queue_available_falls_while_a_slot_is_held() -> None:
    """Remaining admission capacity in /api/health drops while a build holds a slot and
    returns to full once it's released -- backed by the plain in-flight counter
    `_build_slot` maintains, not `BUILD_QUEUE._value` (reading it from app.py
    was rejected in spur).
    """
    from screw import app as app_module

    with TestClient(app) as client:
        full = client.get("/api/health").json()["pool"]["queue_available"]
        with app_module._build_slot("test-req", BoltParams(), "stl", "preview"):
            held = client.get("/api/health").json()["pool"]["queue_available"]
            assert held == full - 1
        released = client.get("/api/health").json()["pool"]["queue_available"]
        assert released == full


def test_health_workers_replaced_increases_after_a_forced_termination() -> None:
    """`workers_replaced` on /api/health reflects `BuildPool.replaced`, and increases
    after the timeout-terminate-replace path fires -- proving the reported field
    tracks live pool state rather than being frozen at startup.
    """
    with TestClient(app) as client:
        pool = app.state.pool
        params = BoltParams()
        before = client.get("/api/health").json()["pool"]["workers_replaced"]

        original_timeout = pool.timeout
        pool.timeout = 0.2
        try:
            with pytest.raises(BuildTimeout):
                asyncio.run(pool._run_with_timeout(params, _sleep_past_timeout, 5.0))
        finally:
            pool.timeout = original_timeout

        after = client.get("/api/health").json()["pool"]["workers_replaced"]
        assert after == before + 1


def test_health_handler_never_awaits_or_touches_pool_internals() -> None:
    """The health handler is a plain sync function -- FastAPI never awaits a sync
    route, so a sync `def health()` is itself the structural proof that this endpoint
    performs no `await` on a worker. Guards against a future edit accidentally making it
    `async def` and reaching into the pool's executors.
    """
    from screw.app import health

    assert not asyncio.iscoroutinefunction(health)


def test_four_same_slot_requests_all_refuse_without_cancellation() -> None:
    """Every request queued on the same hash slot behind one that times out
    must surface as BrokenProcessPool -- never asyncio.CancelledError (a BaseException
    every handler between here and the client misses), and never its own BuildTimeout
    (its own deadline firing first would mean this test never actually exercised the
    queued path, so that outcome must fail the assertions below, not silently pass
    them).

    Also: the same incident must replace the worker exactly once, and the hash
    slot must be usable again afterwards against a fresh worker.

    FOUR same-slot siblings are driven, not three: a single-worker executor's call
    queue is `max_workers + EXTRA_QUEUED_CALLS == 2` deep (concurrent/futures/
    process.py, 3.12.13, line 118 -- `EXTRA_QUEUED_CALLS = 1`). `add_call_item_to_queue`
    (lines 391-404) drains `work_ids_queue` into that 2-deep call queue by calling
    `work_item.future.set_running_or_notify_cancel()` on each item it pulls (line
    404) -- marking it RUNNING before any worker has actually touched it, purely
    because it fit in the queue. `flag_executor_shutting_down` (line 540) only cancels
    a future whose own `.cancel()` succeeds, which a RUNNING future's never does. With
    request 1 already dequeued into the (single, busy) worker, the 2-deep call queue
    is exactly big enough to also swallow requests 2 and 3, both becoming RUNNING; a
    *fourth* is the first request that can still be sitting in `work_ids_queue`,
    genuinely PENDING, when the incident is handled -- reachable in production, not
    just in this test: `MAX_QUEUED_BUILDS` admits 4 builds and affinity can route
    all four to one hash slot. [verified empirically in spur, both pre- and
    post-fix, 5 runs each, with `cancel_futures=True` temporarily restored on
    `recreate_for`'s `shutdown()` call and then reverted (`git diff` confirmed clean
    before committing): the second and third siblings always raised
    `BrokenProcessPool` in every run, pre-fix and post-fix alike (already RUNNING,
    uncancellable) -- but the FOURTH raised `asyncio.CancelledError` pre-fix, in every
    one of 5 runs, and `BrokenProcessPool` post-fix. `asyncio.gather(...,
    return_exceptions=True)` returns a `CancelledError` *instance* for a cancelled
    awaitable rather than raising it out of `gather` itself, so the assertions below
    observe it directly. ] Requests 2,
    3 and 4 are created back-to-back in the same asyncio tick (no `await` between
    them) after the one gap below -- that's what leaves 2 and 3 RUNNING and 4 PENDING;
    an intervening `await asyncio.sleep(0)` before request 4 was not needed to
    reproduce this and was not added.
    """
    with TestClient(app):
        pool = app.state.pool
        params = BoltParams()
        worker_pid_before = pool.executor_for(params).submit(os.getpid).result()
        replaced_before = pool.replaced

        original_timeout = pool.timeout
        pool.timeout = 1.0  # injected, short -- restored in `finally` exactly as the
        # existing timeout tests do.
        try:
            async def _drive() -> list[object]:
                first = asyncio.create_task(
                    pool._run_with_timeout(params, _sleep_past_timeout, 10.0))
                # The gap is the point of this test, not incidental: a sibling that
                # arrives later always has a later deadline under the per-build
                # timeout, so the gap must be comfortably above event-loop scheduling
                # jitter and comfortably below the 1.0s injected timeout -- 0.5s clears
                # both, and keeps the whole test near the timeout's own 1.0s rather
                # than the 10.0s sleep (the sleep only needs to outlast the timeout;
                # the terminate that follows the timeout is what actually ends it).
                # Second, third and fourth all start after that one gap, before the
                # first's deadline -- not three separate gaps (see the docstring above
                # for why four requests, and why no extra `sleep(0)` between them, is
                # what actually reaches a genuinely-PENDING fourth request).
                await asyncio.sleep(0.5)
                second = asyncio.create_task(
                    pool._run_with_timeout(params, _sleep_past_timeout, 10.0))
                third = asyncio.create_task(
                    pool._run_with_timeout(params, _sleep_past_timeout, 10.0))
                fourth = asyncio.create_task(
                    pool._run_with_timeout(params, _sleep_past_timeout, 10.0))
                # mypy --strict: asyncio.gather's overloads collapse to Any once
                # return_exceptions=True mixes results with exception instances in one
                # list -- cast to what the awaited call actually returns, the same
                # pattern pool.py's own build_export uses for a dynamic-import return.
                return cast(list[object], await asyncio.gather(
                    first, second, third, fourth, return_exceptions=True))

            first_result, second_result, third_result, fourth_result = asyncio.run(_drive())
        finally:
            pool.timeout = original_timeout

        assert isinstance(first_result, BuildTimeout)
        for sibling_result in (second_result, third_result, fourth_result):
            assert isinstance(sibling_result, BrokenProcessPool)
            assert not isinstance(sibling_result, asyncio.CancelledError)
            assert not isinstance(sibling_result, BuildTimeout)
        assert pool.replaced == replaced_before + 1

        new_pid = pool.executor_for(params).submit(os.getpid).result()
        assert new_pid != worker_pid_before


def test_two_same_slot_deaths_from_one_incident_replace_the_worker_once(
        caplog: pytest.LogCaptureFixture) -> None:
    """Two same-slot requests that both lose their worker to a hard process
    death both surface as BrokenProcessPool (unchanged by the fix), and
    `pool.replaced` rises by exactly 1 -- not 2 -- because both requests are observing
    the same incident, not two independent ones. The record-count assertion is there
    because the counter-only assertions would still pass against a record emitted at the
    two `_run_with_timeout` call sites instead of inside `recreate_for`'s identity guard;
    this is the assertion that would catch that regression.
    """
    caplog.set_level(logging.INFO)  # caplog defaults to WARNING
    with TestClient(app):
        pool = app.state.pool
        params = BoltParams()
        replaced_before = pool.replaced

        async def _drive() -> list[object]:
            first = asyncio.create_task(pool._run_with_timeout(params, _die))
            second = asyncio.create_task(pool._run_with_timeout(params, _die))
            return cast(list[object],
                        await asyncio.gather(first, second, return_exceptions=True))

        first_result, second_result = asyncio.run(_drive())

        assert isinstance(first_result, BrokenProcessPool)
        assert isinstance(second_result, BrokenProcessPool)
        assert pool.replaced == replaced_before + 1
        assert len(_event_records(caplog, "worker.replaced")) == 1
