# bench

The measuring instrument for screw's runtime figures, ported from spur's `bench/` (L07: "as a
harness, not as numbers"): committed and rerunnable, so a number stays falsifiable by whoever
doubts it later instead of being quoted from a session that has ended.

What it prints is a measurement of one machine on one day, not a bound. `RESULTS.md` records
every run with its machine, load and date; the Phase 1 entries are harness checks on the
walking skeleton. Phase 7 re-sweeps on threaded parts under linux/amd64 (OPER-02) and is what
turns a measurement into a limit.

## What each half measures

- **`bench.build_time`** (`make bench.build`) -- build, fine-STL and STEP time per corpus part,
  in-process through `screw.solid`'s public surface, against `SCREW_BUILD_TIMEOUT`. Also the
  fine STL's byte and triangle counts.
- **`bench.export_cost`** (`make bench.export SET="d=100 length=200"`) -- spur L19's gzip level
  table with its selection rule, and L24's mesh-copy cost, for one part.
- **`bench.latency`** (`make bench.latency`) -- does `/api/health` stay responsive while a
  build is in flight? `single` is one fine build of the heaviest corpus part; `concurrent` is
  ten fine builds of ten distinct parts at once. Reports idle p95, under-load p95, their ratio
  and what the server answered each build with. It sets no bar: screw has no recorded
  baseline to compare against.
- **`bench.memory`** (`make bench.memory`) -- the container memory sweep. `sweep` drives the
  corpus through the service at each of `SCREW_BUILD_WORKERS` = 1, 2, 4 and records the peak
  per N; `confirm` re-runs the corpus at a candidate `mem_limit` and reports the failure
  count. `sweep` runs under a ceiling of its own, so `compose.yaml`'s `mem_limit` can never cap
  the measurement it exists to inform, and a row whose peak reaches that ceiling is reported
  capped, with no peak number.

## Where each half must run, and why

- **Build time and export cost run in-process** on whatever machine you run them on. They need
  no service and no Docker.
- **Latency runs on the host** (`make serve`), because container overhead would make a later
  run incomparable to one taken on the host. Start a **fresh** server for each run: a part the
  server has already built is a cache hit (`SCREW_EXPORT_CACHE_MB`) and puts no load on
  anything, so a second run against the same server measures nothing. `make serve` binds
  `127.0.0.1:8000`; if that is taken, `screw serve --port 8001` and
  `.venv/bin/python -m bench.latency --base-url http://127.0.0.1:8001`.
- **Memory runs in the container** (`docker compose`), because `mem_limit` is a container
  setting and must be measured under the container's own accounting. `malloc_trim(0)`, which
  the per-worker arena release depends on, is glibc-only and does nothing on a macOS
  development machine; the container is Linux, where it runs. The service is published on the
  port of `--base-url` (default 8000): `.venv/bin/python -m bench.memory sweep --base-url
  http://127.0.0.1:8001` when 8000 is taken. On Apple silicon the image is linux/amd64 under
  emulation (`DOCKER_DEFAULT_PLATFORM`, `Makefile` `PLATFORM`), so its timings and memory are
  emulation figures: say so beside any number you quote, and re-measure on linux/amd64 before
  using one as a limit.

Every number either half prints carries the machine that produced it (CPU count, architecture,
RAM) and the load averages read before the first row -- a measurement's meaning changes with
the hardware and the weather behind it.

## How to run them

```
make bench.build                          # in-process, 12 corpus parts
make bench.export SET="d=100 length=200"  # gzip table and mesh-copy cost for one part

make serve                                # in one terminal, a fresh server
make bench.latency                        # in another -- both load scenarios

make bench.memory                         # manages its own containers: the N=1,2,4 sweep
.venv/bin/python -m bench.memory confirm 2g   # confirm a candidate mem_limit
```

`make bench` runs the latency and memory halves in sequence. None of the targets is part of
`make verify` or `make check`: they need a stopwatch, and a timing assertion on shared hardware
would flap until someone stopped believing it. The harness's own predicates (capped rows, STL
sizing, the L19 rule, `ru_maxrss` units, 503 reasons, the refusal of an empty sweep and of a p95
over too few samples) are tested in `tests/test_bench.py`, which is part of the gate.

## The corpus

`bench/corpus.py` is 12 plain cylinders on a d x length grid. The skeleton corpus exercises the
harness and sets no bound: it stays far below the D-14 corner (`d`, `length` up to 1e5 mm), so
nothing measured against it says anything about the interim `mem_limit` or
`SCREW_BUILD_TIMEOUT`. Phase 7 replaces it with the threaded grid and keeps that one fixed from
then on: narrowing, shortening or re-picking a corpus to make a ceiling look better produces a
number that cannot be compared with the one already on record, which defeats the point of
measuring.

## Thread spike (Phase 2)

`bench.thread_spike` (`make bench.thread ARGS="..."`) answers four questions before any field
builds a thread: which helical construction to build (sewn twist against the one-pipe,
ruled-surface and naive `sweep` + `fuse` rows, with each size's failure frontier in turns), what
a fine mesh costs (triangles, seconds, peak RSS, bytes, gzip ratio) against the INTERIM 30 s and
64 MB budgets, whether a kernel pair check can be made falsifiable, and which volume estimator
to trust. The method, every constant, every verdict rule, the predictions and the escape clause
are in `.planning/phases/02-thread-spike/02-SPIKE.md`, written before the first run.

- **Outside `make verify`.** The campaign is hours of kernel time (up to 16 969 rows and 272
  pair cells) and its timings are only meaningful on a quiet host; a timing assertion on shared
  hardware would flap. What the gate does run is the harness's own predicates on synthetic
  records, and the check that every constant in the code equals the protocol's
  (`tests/test_bench.py::test_the_protocol_pre_registers_every_constant_the_harness_uses`).
- **The guard.** No campaign run starts until the protocol is on `origin/main` and its text above
  `## Results` equals main's, byte for byte: `make bench.thread ARGS="check-protocol"` prints
  "protocol guard: held" or the reasons it does not. A change to a pre-registered input after
  landing is a new PR that visibly post-dates the protocol.
- **Smoke against campaign.** `smoke` (`--block <block>`, `--pair`) checks the harness on two
  small sizes: no run id, output in a temporary directory, never recorded, never cited. `campaign
  --run-id <prefix>` is the measurement: nine blocks, each a recorded run `<prefix>-<block>`, and
  `verdict --campaign <prefix>` reads them back and recomputes every row's class from the raw
  record.
- **Where records go.** `bench/results/thread-spike/<id>.jsonl` (a header, then one row per
  line, written as measured) and `<id>.md`; a run id is never reused or overwritten. `bench/RESULTS.md`
  carries each run's header, host state, load readings and every non-ok or over-budget row.
- **Agents closed.** The owner runs the campaign detached with every agent session closed: an
  open session keeps the host's load near 2.0, above the quiet gate's 1.5, and the run reads
  non-decisive.
