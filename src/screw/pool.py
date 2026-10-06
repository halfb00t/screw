"""Process pool that runs CAD builds outside the serving process.

Ported from spur (L07); the mechanics were found there by incident, so structure and
comments travel together. `app.py` holds a `BuildPool` instance and calls its async
`export()`; it has no static import path to `cadquery`/`OCP` through this module
(import-linter contract 5) -- the kernel import happens only at runtime, inside a worker,
via `importlib.import_module`. Each of the N single-worker `ProcessPoolExecutor`s is warmed
with the kernel once at startup and then reused for every build routed to it by
parameter-hash affinity: the UI's preview STL, fine STL and STEP requests for one part are
three byte-cache keys but one solid, so keeping them on the same worker avoids the same
solid becoming resident in all N of them. Accepted cost: no work stealing -- a hot part
serialises, which is what it does under the single kernel lock.

A per-build timeout means a wedged worker, fatal to 1/N of the parameter space under
affinity until something kills it, is terminated: `export()` terminates the OS process
running an overrunning build rather than merely abandoning the `Future` waiting on it, then
replaces that hash slot's executor (`recreate_for`). The same replacement handles a worker
that dies on its own (`BrokenProcessPool`).
"""

from __future__ import annotations

import asyncio
import functools
import importlib
import multiprocessing as mp
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from typing import ParamSpec, cast

from .build_errors import BuildTimeout
from .params import FastenerParams
from .records import worker_replaced

_SPAWN = mp.get_context("spawn")  # portable, and the parent has no OCP to fork

P = ParamSpec("P")  # the real call shapes: build_export(p, fmt, quality),
# _sleep_past_timeout(seconds), _die() -- see _run_with_timeout below


def _warm() -> None:
    """`ProcessPoolExecutor`'s initializer: runs once per worker, before its first task.

    Loads the kernel into the worker before it accepts work, so the first real request
    doesn't pay the cadquery/OCP import cost. This import is the reason contract 5 must be
    `allow_indirect_imports = false` scoped to `screw.app` only -- `screw.pool` importing
    `screw.solid` at runtime, inside a worker, is exactly the boundary being drawn, not a
    violation of it.
    """
    importlib.import_module("screw.solid")


def build_export(p: FastenerParams, fmt: str, quality: str) -> bytes:
    """The function submitted across the process boundary.

    Deliberately a dynamic import, not `from .solid import export` (even nested inside this
    function): a static import would put a `screw.app -> screw.pool -> screw.solid ->
    cadquery` edge in the import graph, which contract 5 forbids for `screw.app`. The
    parent process only ever holds this function's *name*, for `spawn` to pickle by
    reference; only a worker process executes its body, where importing the kernel is fine.
    """
    solid = importlib.import_module("screw.solid")
    # `solid` is loaded dynamically, so mypy sees its attributes as untyped; `export()`'s
    # real return type is bytes, so warn_return_any needs this cast rather than a genuine
    # type gap.
    return cast(bytes, solid.export(p, fmt, quality))


class BuildPool:
    """N independent single-worker executors, routed to by parameter-hash affinity."""

    def __init__(self, workers: int, timeout: int) -> None:
        self.workers = workers
        self.timeout = timeout  # per-build ceiling in seconds; see app.py's lifespan for
        # where the number itself comes from -- this class only enforces it.
        self.replaced = 0  # workers replaced since start, reported at /api/health
        # `max_tasks_per_child` is deliberately absent (stays None -- no recycling). spur's
        # memory sweep split each N's samples into an early/late half to check for drift
        # that malloc_trim doesn't flatten: N=2 and N=4 grew late vs early, but spur's
        # corpus was strictly ascending tooth count, so the "late" half was inherently the
        # biggest gears -- a bounded per-worker solid cache holding increasingly large
        # solids grows resident memory for that reason alone, with no leak required. No run
        # showed unbounded growth. Recycling anyway would cost a respawn plus a cadquery
        # import and wipe the warm solid cache that affinity exists to keep. Not measured
        # for screw; Phase 7 re-sweeps (OPER-02).
        self._executors = [
            ProcessPoolExecutor(max_workers=1, mp_context=_SPAWN, initializer=_warm)
            for _ in range(workers)
        ]

    def executor_for(self, p: FastenerParams) -> ProcessPoolExecutor:
        return self._executors[hash(p) % self.workers]  # affinity, not load-balance

    def recreate_for(self, p: FastenerParams, executor: ProcessPoolExecutor,
                     cause: str) -> None:
        """Discard a broken/wedged single-worker executor and replace it.

        `executor` is the one the *caller's own* failing request actually used --
        `_run_with_timeout` passes in the `executor` local it already holds. Affinity means
        several requests share one hash slot, so more than one of them can observe the
        same dead/wedged worker and each call this method for the same incident. Without
        this identity check the second (and third, ...) caller would discard and recreate
        a *replacement* that the first caller's call just built and is still warming
        (`_warm` importing `screw.solid`/`cadquery`), and `/api/health`'s
        `workers_replaced` would count one incident as two -- observed directly by spur's
        `test_two_same_slot_deaths_from_one_incident_replace_the_worker_once` against this
        method before the guard existed (`replaced` read 2, not 1).

        `cause` (`"timeout"` or `"broken_pool"`) is threaded in from the caller because
        `recreate_for` itself cannot tell which of `_run_with_timeout`'s two branches is
        calling it. The `worker.replaced` log record below and the `self.replaced` counter
        above it are two views of the same event and must stay on the same side of this
        identity guard: emitting from either call site in `_run_with_timeout` instead
        would log once per *caller* rather than once per *incident*, re-creating the
        double-count this guard exists to prevent -- this time in the log, where nothing
        else would catch it.
        """
        i = hash(p) % self.workers
        if self._executors[i] is not executor:
            return  # someone else already replaced this slot for this incident
        # No `cancel_futures=True`. A single-worker executor's call queue holds
        # `max_workers + EXTRA_QUEUED_CALLS == 2` items (CPython 3.12.13 process.py, line
        # 118); `add_call_item_to_queue` (lines 391-404) marks each item it pulls into that
        # queue RUNNING via `future.set_running_or_notify_cancel()` (line 404) -- before
        # any worker has touched it, purely because it fit. A future already RUNNING can't
        # be cancelled, so `flag_executor_shutting_down`'s own cancel loop (line 540, only
        # reached with `cancel_futures=True`) silently skips it and it falls through to
        # `_ExecutorManagerThread._terminate_broken` the same way a worker dying on its own
        # does -- `BrokenProcessPool`, which the `except BrokenProcessPool` branch below
        # already handles and app.py already maps to a 503 `pool_broken`. With request 1
        # already dequeued into the (single, busy) worker, that 2-deep call queue is
        # exactly big enough to also make requests 2 and 3 RUNNING; a *fourth* same-slot
        # request is the first one that can still be sitting in `work_ids_queue`, genuinely
        # PENDING -- and reachable in production, since `MAX_QUEUED_BUILDS` admits 4 builds
        # and affinity can route all four to one hash slot. [spur verified, with and
        # without `cancel_futures=True`, 5 runs each: the 2nd and 3rd same-slot requests
        # always reached `BrokenProcessPool`, but the *4th* raised
        # `asyncio.CancelledError` with `cancel_futures=True` restored, in every run --
        # which is what keeps this method's unconditional omission of it from ever letting
        # a 4th-or-later same-slot request reach that path.]
        self._executors[i].shutdown(wait=False)
        self._executors[i] = ProcessPoolExecutor(
            max_workers=1, mp_context=_SPAWN, initializer=_warm)
        self.replaced += 1
        worker_replaced(slot=i, cause=cause)

    async def _run_with_timeout(
        self, p: FastenerParams, func: Callable[P, bytes], *args: P.args, **kwargs: P.kwargs,
    ) -> bytes:
        """Route `func(*args, **kwargs)` to `p`'s worker, enforcing the per-build timeout
        and replacing the worker if it wedges or dies.

        A private seam behind `export()` rather than inlined there, so tests/test_pool.py
        can drive the timeout/replacement path with a trivial sleeping function instead of
        a real (and therefore slow) CAD build -- the mechanics under test (timeout ->
        terminate -> recreate, and broken-pool -> recreate) don't depend on what `func`
        actually builds.
        """
        executor = self.executor_for(p)
        loop = asyncio.get_running_loop()
        # run_in_executor(executor, func, *args) takes positional arguments only, so
        # func/args/kwargs are bound into a functools.partial first -- the partial carries
        # the keyword arguments across the boundary that run_in_executor's own signature
        # has no slot for (PEP 612 requires *args: P.args and **kwargs: P.kwargs together,
        # so a signature that forwarded only *args would type-check while accepting -- and
        # then silently dropping -- a keyword argument). A partial of a module-level
        # function pickles by reference under `spawn`, so a callable still has to be
        # importable by its qualified name.
        future = loop.run_in_executor(executor, functools.partial(func, *args, **kwargs))
        try:
            return await asyncio.wait_for(future, timeout=self.timeout)
        except TimeoutError:
            # The builtin TimeoutError, not the qualified asyncio.TimeoutError: since
            # Python 3.11 the asyncio name is an alias of the builtin, and 3.12 is this
            # project's only interpreter (L01) -- asyncio.wait_for always raises this one.
            #
            # Same-slot guard (divergence from spur, recorded in L09). Several requests on
            # one hash slot can time out in one incident. The first terminates the worker,
            # shuts this executor down and installs a replacement in the slot; a second
            # one's timeout, firing in the same loop pass, still holds the shut-down
            # executor, and CPython 3.12 sets `_processes` to None on shutdown, so the
            # loop below raised `AttributeError: 'NoneType' object has no attribute
            # 'values'` -- no status in app.py, a raw 500 from uvicorn. spur measured it
            # under ten concurrent builds and left it as its open `must` debt file
            # 2026-10-02-same-slot-timeout-cleanup-race-produces-undocumented-500.md.
            # The first request already killed the worker, so the slot being replaced
            # means there is nothing left to terminate or recreate: report the timeout.
            if self._executors[hash(p) % self.workers] is not executor:
                raise BuildTimeout(
                    f"Build exceeded the {self.timeout}s per-build timeout. "
                    "Try a coarser quality."
                ) from None
            # Executor.shutdown(cancel_futures=True) is not a substitute for this: it only
            # cancels futures that have not started running yet
            # (`inspect.signature(ProcessPoolExecutor.shutdown)` is `(self, wait=True, *,
            # cancel_futures=False)`). A future already executing OCCT code is untouched
            # by it: the wait would end while the work continued, and under affinity every
            # later request for this hash slot would queue up behind a build nobody is
            # waiting for. Terminating the OS process is the only way found to actually
            # stop it.
            #
            # `_processes` is private, undocumented CPython -- present on 3.12.13. If a
            # future interpreter removes or renames it,
            # tests/test_pool.py::test_executor_processes_attribute_still_exists fails
            # `make verify` loudly, rather than this path silently degrading into an
            # abandoned future that never gets killed.
            for proc in executor._processes.values():
                proc.terminate()
            self.recreate_for(p, executor, "timeout")
            raise BuildTimeout(
                f"Build exceeded the {self.timeout}s per-build timeout. "
                "Try a coarser quality."
            ) from None
        except BrokenProcessPool:
            # The worker died on its own (crash, OOM-kill, ...) rather than being
            # terminated by us -- concurrent.futures raises this from the awaited call
            # automatically. Same remedy as the timeout case: the dead slot is replaced
            # rather than staying dead. Re-raised so app.py maps it to its own status code
            # instead of this module deciding HTTP semantics.
            self.recreate_for(p, executor, "broken_pool")
            raise

    async def export(self, p: FastenerParams, fmt: str, quality: str) -> bytes:
        return await self._run_with_timeout(p, build_export, p, fmt, quality)

    def shutdown(self) -> None:
        for executor in self._executors:
            executor.shutdown(wait=False)
