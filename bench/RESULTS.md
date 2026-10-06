# screw bench results

Every number below names its machine, its load and its date, and none of it is a bound. The
harness in `bench/` is what L07 ported from spur ("as a harness, not as numbers"); the Phase 1
entries run it once against the walking skeleton (a plain unthreaded cylinder) to show it
works. Phase 7 re-sweeps on threaded parts on linux/amd64 (OPER-02) and is what turns a
measurement into a limit. Until then the interim figures in
`docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` stand as labelled spur carry-overs,
and nothing here confirms or replaces them.

How to read an entry: the load averages are `os.getloadavg()` read before the first row builds
(or, for the container sweep, `uptime` just before launch); the machine line is
`bench.machine_facts()`. A figure measured in the container is an emulation figure (the image
is linux/amd64 on an arm64 host) and is labelled so.

## Harness check on the walking skeleton (Phase 1)

Harness check on the walking skeleton -- not a bound (L07); Phase 7 re-sweeps.

Host for every entry in this section: Apple M2 Max, 12 CPUs, 32 GiB RAM, macOS (Darwin 27.0.0),
2026-10-06. The corpus is `bench/corpus.py`: 12 plain cylinders, d in {2, 6, 20, 100} mm by
length in {5, 20, 200} mm. It stays far below the D-14 corner (d and length up to 1e5 mm) on
purpose, so nothing here says anything about the interim `mem_limit` or `SCREW_BUILD_TIMEOUT`.

### Build, fine STL and STEP time (`make bench.build`)

Run 2026-10-06T05:46:55Z, native arm64 (no container), in-process through `screw.solid`, load
averages 2.79, 2.59, 2.60 at start (other projects were running on this host; this is not an
idle machine). Output verbatim:

```
- Machine: 12 CPUs, arm64, 32.0 GiB RAM
- Python: 3.12.13
- Kernel: cadquery 2.8.0, cadquery-ocp 7.9.3.1.1
- HEAD: `8bb2398`
- Sweep: `bench/corpus.py` (the skeleton corpus)
- Load averages at start: 2.79, 2.59, 2.60
- SCREW_BUILD_TIMEOUT: 30 s, a cold request is one build plus one export

| Parameter set | Build (s) | Fine STL (s) | STEP (s) | Build + slower export (s) | Inside 30 s | Fine STL (bytes) | Triangles |
|---|---|---|---|---|---|---|---|
| d=2 length=5 | 0.01 | 0.00 | 0.00 | 0.01 | yes | 25084 | 500 |
| d=2 length=20 | 0.00 | 0.00 | 0.00 | 0.01 | yes | 25084 | 500 |
| d=2 length=200 | 0.00 | 0.00 | 0.00 | 0.01 | yes | 25084 | 500 |
| d=6 length=5 | 0.00 | 0.00 | 0.00 | 0.01 | yes | 25084 | 500 |
| d=6 length=20 | 0.00 | 0.00 | 0.00 | 0.01 | yes | 25084 | 500 |
| d=6 length=200 | 0.00 | 0.00 | 0.00 | 0.01 | yes | 25084 | 500 |
| d=20 length=5 | 0.00 | 0.00 | 0.00 | 0.01 | yes | 25084 | 500 |
| d=20 length=20 | 0.00 | 0.00 | 0.00 | 0.01 | yes | 25084 | 500 |
| d=20 length=200 | 0.00 | 0.00 | 0.00 | 0.01 | yes | 25084 | 500 |
| d=100 length=5 | 0.00 | 0.00 | 0.00 | 0.01 | yes | 44484 | 888 |
| d=100 length=20 | 0.00 | 0.00 | 0.00 | 0.01 | yes | 44484 | 888 |
| d=100 length=200 | 0.00 | 0.00 | 0.00 | 0.01 | yes | 44484 | 888 |

**Heaviest:** d=2 length=5 -- 0.01 s of 30 s.
**Largest fine STL:** d=100 length=5 -- 44484 bytes, 888 triangles.
```

What this shows: the harness runs end to end and prints the load before the first row. It shows
nothing about a threaded part: every row sits at the 10 ms floor of a two-decimal print, so which
row the "Heaviest" line names is not a finding (the first row's 0.01 s build is the only build
figure that rose off 0.00; its cause was not investigated). Triangle count follows the tessellation's angular deflection, not the length, which is
why the length rows repeat.

### gzip level table and mesh-copy cost (`make bench.export SET="d=100 length=200"`)

Run 2026-10-06T05:46:57Z, native arm64, in-process plus six child processes, load averages
2.79, 2.59, 2.60 at start. Output verbatim:

```
- Machine: 12 CPUs, arm64, 32.0 GiB RAM
- Python: 3.12.13
- Kernel: cadquery 2.8.0, cadquery-ocp 7.9.3.1.1
- HEAD: `8bb2398`
- Set: d=100 length=200
- Load averages at start: 2.79, 2.59, 2.60

- Fine STL: 44484 bytes, 888 triangles

### gzip level (L19)
| Level | Single-threaded median (ms) | Output bytes (% of input) | 10-concurrent wall, median of 3 (ms) |
|---|---|---|---|
| 1 | 0.2 | 10507 (23.6%) | 0.9 |
| 6 | 0.7 | 8820 (19.8%) | 1.7 |
| 9 | 7.7 | 8784 (19.7%) | 11.7 |

**L19 selects:** level 1 -- level 6: 16.06% smaller (bar 10%), 1.81x wall (bar 1.5x) -- not adopted; level 9: 16.40% smaller (bar 10%), 12.84x wall (bar 1.5x) -- not adopted

### Mesh copy (L24)
3 child processes per mode, alternating copy and in-place, one fresh process per run so peak RSS is that run's own reading, never a cumulative maximum carried over from an earlier one.
| Run | Mode | Export (ms) | Peak RSS (MiB) | Triangles |
|---|---|---|---|---|
| 1 | copy | 2.4 | 459.2 | 888 |
| 1 | in-place | 2.2 | 456.1 | 888 |
| 2 | copy | 2.2 | 457.0 | 888 |
| 2 | in-place | 2.2 | 457.6 | 888 |
| 3 | copy | 2.2 | 456.4 | 888 |
| 3 | in-place | 2.2 | 456.2 | 888 |

**Copy cost:** +0.1 ms mean export, +0.9 MiB mean peak RSS over in place (mean of 3 each).
```

What this shows: the instrument runs and applies L19's rule. The "level 6 not adopted" verdict is
decided on the wall bar at sub-2 ms walls over a 44 KB mesh, so it is a statement about this
mesh, not about a threaded part's, which is the reason the harness exists. The ~456 MiB peak RSS
in the mesh-copy rows is dominated by the interpreter plus the cadquery import (the params.py
comment measured the same floor, ~450 MiB), not by the export; the copy-versus-in-place
difference (0.1 ms, 0.9 MiB) is inside that run-to-run noise.

### `/api/health` under load (`bench.latency`)

Run 2026-10-06T05:52:50Z against `screw serve --port 8001` (8000 was held by another project's
container, which was left running), started fresh for this run: native arm64 on the host, not in
the container; 2 build workers and a 4-deep queue (the app's own defaults); harness at HEAD
`26bf992`. Launched as `.venv/bin/python -m bench.latency --base-url http://127.0.0.1:8001`,
which is what `make bench.latency` runs plus the port. Load averages are the harness's own
reading at the start of each scenario. Output verbatim:

```
## Latency: concurrent

- Machine: 12 CPUs, arm64, 32.0 GiB RAM
- Load averages at start: 2.38, 2.48, 2.54
- Idle p95: 0.6 ms (n=3585)
- Under-load p95: 0.8 ms (n=2989)
- Ratio (under-load / idle): 1.26x -- no bar is set for screw yet
- Slowest successful build: 2.14 s
- Build requests: 10 attempted -- 200: 4, 503 busy: 6 (`503 busy` is admission control, expected once concurrency exceeds the queue)

## Latency: single

- Machine: 12 CPUs, arm64, 32.0 GiB RAM
- Load averages at start: 2.35, 2.47, 2.53
- Idle p95: 0.6 ms (n=3594)
- Under-load p95: 0.6 ms (n=3765)
- Ratio (under-load / idle): 0.99x -- no bar is set for screw yet
- Slowest successful build: 2.11 s
- Build requests: 1 attempted -- 200: 1 (`503 busy` is admission control, expected once concurrency exceeds the queue)
```

What this shows: the harness runs both scenarios, records the 503 reasons and prints the load.
Admission control took 4 of the 10 concurrent requests and refused 6, as the queue depth says it
should. It does not show a bound. An earlier run of the same two scenarios in this session, before
the harness printed the load, read 1.27x and 1.08x with 2.14 s and 2.15 s slowest builds. A
skeleton cylinder builds in about 10 ms in-process (`bench.build` above), so the 2.1 s slowest
build is not the cost of building a part; its cause (the first build in a fresh worker, possibly
the kernel import) was not isolated. The threaded-part answer is Phase 7's.

### Container memory sweep (`bench.memory sweep`)

Run 2026-10-06T05:53:17Z to 05:54:19Z, harness at HEAD `26bf992`, image `screw:latest`
(`sha256:b2dccee07712`, rebuilt from cached layers with `make image` immediately before).
Docker 29.4.0 via OrbStack on this host; the daemon is linux/aarch64 and the image is
**linux/amd64 under emulation** (`DOCKER_DEFAULT_PLATFORM=linux/amd64`), so every figure below
is an emulation figure, not a native linux/amd64 one, and not a macOS one either. The sweep ran
under its own 8 GiB ceiling (not `compose.yaml`'s interim `mem_limit: 4g`), published on
`127.0.0.1:8001` because 8000 was held by another project's container (left running). Launched as
`.venv/bin/python -m bench.memory sweep --base-url http://127.0.0.1:8001`, which is what
`make bench.memory` runs plus the port. Output verbatim (`uptime` at launch read load averages
2.34 2.46 2.53, the same as the harness's own line):

```
## Memory sweep

- Machine: 12 CPUs, arm64, 32.0 GiB RAM
- Load averages at start: 2.34, 2.46, 2.53
- Peak read from: `docker stats --no-stream` MEM USAGE, polled every 0.5s (a sampled peak, not the cgroup's exact accounting)
- Early/late peak: max of the first half vs second half of the corpus run's samples

| N (SCREW_BUILD_WORKERS) | Peak | Early peak | Late peak | Samples | Requests | Failures | Elapsed |
|---|---|---|---|---|---|---|---|
| 1 | 1323.0 MiB | 732.1 MiB | 1323.0 MiB | 4 | 12 | 0 | 5.8s |
| 2 | 980.8 MiB | 488.5 MiB | 980.8 MiB | 6 | 12 | 0 | 10.9s |
| 4 | 1881.1 MiB | 992.8 MiB | 1881.1 MiB | 12 | 12 | 0 | 22.0s |
```

No row was capped and no request failed. The containers were torn down by the harness, and no
screw container or network was left on the host afterwards.

What this shows: the sweep starts a container at each N, drives the corpus, samples and tears
down. It does not show a footprint. Each peak is the maximum of 4 to 12 `docker stats` readings
over a 5.8 to 22 s run (one reading takes longer than the 0.5 s poll interval), and the corpus is
12 cylinders. In every row the peak falls in the second half of the readings, so the figure is where
sampling happened to stop, not a plateau. N=1 reads higher than N=2 (1323 against 981 MiB), which a
footprint that grows with workers would not produce; the cause was not isolated, and emulation
and worker start-up are candidates, not findings. Do not read "late peak above early peak" as
drift. Phase 7 drives the threaded grid under linux/amd64 for long enough to sample properly,
and is what sets `mem_limit` (OPER-02, OPER-03).
